from database.database import get_db_connection
from datetime import datetime, timezone
import uuid


def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_offer_id():
    return f"OFR-{uuid.uuid4().hex[:16].upper()}"


def _parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None


def _is_offer_valid(offer):
    current_time = datetime.now(timezone.utc)

    start_at = _parse_datetime(offer["start_at"])
    end_at = _parse_datetime(offer["end_at"])

    if not start_at or not end_at:
        return False

    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=timezone.utc)

    if end_at.tzinfo is None:
        end_at = end_at.replace(tzinfo=timezone.utc)

    if current_time < start_at:
        return False

    if current_time > end_at:
        return False

    if not offer["is_active"]:
        return False

    if offer["status"] != "active":
        return False

    if (
        offer["usage_limit"] is not None
        and offer["used_count"] >= offer["usage_limit"]
    ):
        return False

    return True


def create_offer(
    offer_name,
    start_at,
    end_at,
    offer_type="percentage",
    discount_value=0,
    description=None,
    offer_code=None,
    maximum_discount=None,
    minimum_order_amount=0,
    maximum_order_amount=None,
    minimum_quantity=1,
    maximum_quantity=None,
    applicable_to="all",
    target_id=None,
    user_id=None,
    usage_limit=None,
    usage_per_user=1,
    priority=0,
    is_stackable=False,
    is_featured=False,
    created_by=None,
    status="scheduled"
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        allowed_offer_types = {
            "percentage",
            "flat",
            "buy_one_get_one",
            "buy_x_get_y",
            "free_shipping",
            "cashback"
        }

        allowed_applicable_to = {
            "all",
            "product",
            "category",
            "variant",
            "user",
            "new_user"
        }

        allowed_statuses = {
            "draft",
            "scheduled",
            "active",
            "paused",
            "expired",
            "exhausted",
            "blocked",
            "deleted"
        }

        if offer_type not in allowed_offer_types:
            raise ValueError("Invalid offer type.")

        if applicable_to not in allowed_applicable_to:
            raise ValueError("Invalid applicable_to value.")

        if status not in allowed_statuses:
            raise ValueError("Invalid offer status.")

        if not offer_name or not offer_name.strip():
            raise ValueError("Offer name is required.")

        if not start_at or not end_at:
            raise ValueError(
                "start_at and end_at are required."
            )

        start_datetime = _parse_datetime(start_at)
        end_datetime = _parse_datetime(end_at)

        if not start_datetime or not end_datetime:
            raise ValueError(
                "Invalid start_at or end_at format."
            )

        if end_datetime <= start_datetime:
            raise ValueError(
                "end_at must be after start_at."
            )

        discount_value = float(discount_value)

        if discount_value < 0:
            raise ValueError(
                "Discount value cannot be negative."
            )

        if offer_type == "percentage":
            if discount_value > 100:
                raise ValueError(
                    "Percentage discount cannot exceed 100."
                )

        if maximum_discount is not None:
            maximum_discount = float(maximum_discount)

            if maximum_discount < 0:
                raise ValueError(
                    "Maximum discount cannot be negative."
                )

        minimum_order_amount = float(
            minimum_order_amount or 0
        )

        if minimum_order_amount < 0:
            raise ValueError(
                "Minimum order amount cannot be negative."
            )

        if maximum_order_amount is not None:
            maximum_order_amount = float(
                maximum_order_amount
            )

            if maximum_order_amount < minimum_order_amount:
                raise ValueError(
                    "Maximum order amount cannot be less "
                    "than minimum order amount."
                )

        if minimum_quantity < 1:
            raise ValueError(
                "Minimum quantity must be at least 1."
            )

        if maximum_quantity is not None:
            if maximum_quantity < minimum_quantity:
                raise ValueError(
                    "Maximum quantity cannot be less "
                    "than minimum quantity."
                )

        if usage_limit is not None and usage_limit < 1:
            raise ValueError(
                "Usage limit must be greater than zero."
            )

        if usage_per_user < 1:
            raise ValueError(
                "Usage per user must be greater than zero."
            )

        if applicable_to != "all" and not target_id and applicable_to != "new_user":
            if applicable_to != "user" or not user_id:
                raise ValueError(
                    "target_id/user_id is required for this offer."
                )

        if offer_code:
            offer_code = offer_code.strip().upper()

            cursor.execute("""
                SELECT offer_id
                FROM offers
                WHERE offer_code = ?
            """, (offer_code,))

            if cursor.fetchone():
                raise ValueError(
                    "Offer code already exists."
                )

        offer_id = _generate_offer_id()
        current_time = _current_time()

        cursor.execute("""
            INSERT INTO offers (
                offer_id,
                offer_name,
                offer_code,
                description,
                offer_type,
                discount_value,
                maximum_discount,
                minimum_order_amount,
                maximum_order_amount,
                minimum_quantity,
                maximum_quantity,
                applicable_to,
                target_id,
                user_id,
                usage_limit,
                usage_per_user,
                used_count,
                start_at,
                end_at,
                priority,
                is_stackable,
                is_featured,
                is_active,
                status,
                created_by,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                0, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?
            )
        """, (
            offer_id,
            offer_name.strip(),
            offer_code,
            description,
            offer_type,
            discount_value,
            maximum_discount,
            minimum_order_amount,
            maximum_order_amount,
            minimum_quantity,
            maximum_quantity,
            applicable_to,
            target_id,
            user_id,
            usage_limit,
            usage_per_user,
            start_at,
            end_at,
            priority,
            int(is_stackable),
            int(is_featured),
            status,
            created_by,
            current_time,
            current_time
        ))

        connection.commit()

        return get_offer_by_id(offer_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_offer_by_id(offer_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM offers
            WHERE offer_id = ?
            AND status != 'deleted'
        """, (offer_id,))

        offer = cursor.fetchone()

        return dict(offer) if offer else None

    finally:
        connection.close()


def get_offer_by_code(offer_code):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM offers
            WHERE offer_code = ?
            AND status != 'deleted'
        """, (
            offer_code.strip().upper(),
        ))

        offer = cursor.fetchone()

        return dict(offer) if offer else None

    finally:
        connection.close()


def get_offers(
    status=None,
    offer_type=None,
    applicable_to=None,
    is_active=None,
    is_featured=None,
    limit=50,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT *
            FROM offers
            WHERE status != 'deleted'
        """

        params = []

        if status:
            query += """
                AND status = ?
            """
            params.append(status)

        if offer_type:
            query += """
                AND offer_type = ?
            """
            params.append(offer_type)

        if applicable_to:
            query += """
                AND applicable_to = ?
            """
            params.append(applicable_to)

        if is_active is not None:
            query += """
                AND is_active = ?
            """
            params.append(int(is_active))

        if is_featured is not None:
            query += """
                AND is_featured = ?
            """
            params.append(int(is_featured))

        query += """
            ORDER BY
                priority DESC,
                created_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([
            limit,
            offset
        ])

        cursor.execute(
            query,
            tuple(params)
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


def get_active_offers(
    user_id=None,
    product_id=None,
    category_id=None,
    variant_id=None,
    order_amount=0,
    quantity=1,
    limit=20
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        current_time = _current_time()

        query = """
            SELECT *
            FROM offers
            WHERE status = 'active'
            AND is_active = 1
            AND start_at <= ?
            AND end_at >= ?
            AND (
                usage_limit IS NULL
                OR used_count < usage_limit
            )
            AND minimum_order_amount <= ?
            AND minimum_quantity <= ?
        """

        params = [
            current_time,
            current_time,
            order_amount,
            quantity
        ]

        query += """
            AND (
                maximum_order_amount IS NULL
                OR maximum_order_amount >= ?
            )
        """

        params.append(order_amount)

        query += """
            AND (
                maximum_quantity IS NULL
                OR maximum_quantity >= ?
            )
        """

        params.append(quantity)

        query += """
            AND (
                applicable_to = 'all'
                OR (
                    applicable_to = 'product'
                    AND target_id = ?
                )
                OR (
                    applicable_to = 'category'
                    AND target_id = ?
                )
                OR (
                    applicable_to = 'variant'
                    AND target_id = ?
                )
                OR (
                    applicable_to = 'user'
                    AND user_id = ?
                )
                OR (
                    applicable_to = 'new_user'
                    AND ? IS NOT NULL
                )
            )
            ORDER BY priority DESC, discount_value DESC
            LIMIT ?
        """

        params.extend([
            product_id,
            category_id,
            variant_id,
            user_id,
            user_id,
            limit
        ])

        cursor.execute(
            query,
            tuple(params)
        )

        offers = []

        for row in cursor.fetchall():
            offer = dict(row)

            if _is_offer_valid(offer):
                offers.append(offer)

        return offers

    finally:
        connection.close()


def update_offer(
    offer_id,
    **fields
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        allowed_fields = {
            "offer_name",
            "offer_code",
            "description",
            "offer_type",
            "discount_value",
            "maximum_discount",
            "minimum_order_amount",
            "maximum_order_amount",
            "minimum_quantity",
            "maximum_quantity",
            "applicable_to",
            "target_id",
            "user_id",
            "usage_limit",
            "usage_per_user",
            "start_at",
            "end_at",
            "priority",
            "is_stackable",
            "is_featured",
            "is_active",
            "status"
        }

        update_fields = {
            key: value
            for key, value in fields.items()
            if key in allowed_fields
        }

        if not update_fields:
            raise ValueError(
                "No valid fields provided."
            )

        cursor.execute("""
            SELECT *
            FROM offers
            WHERE offer_id = ?
            AND status != 'deleted'
        """, (offer_id,))

        existing = cursor.fetchone()

        if not existing:
            raise ValueError(
                "Offer not found."
            )

        if "offer_code" in update_fields:
            code = update_fields["offer_code"]

            if code:
                code = code.strip().upper()

                cursor.execute("""
                    SELECT offer_id
                    FROM offers
                    WHERE offer_code = ?
                    AND offer_id != ?
                """, (
                    code,
                    offer_id
                ))

                if cursor.fetchone():
                    raise ValueError(
                        "Offer code already exists."
                    )

                update_fields["offer_code"] = code

        if "offer_type" in update_fields:
            allowed_types = {
                "percentage",
                "flat",
                "buy_one_get_one",
                "buy_x_get_y",
                "free_shipping",
                "cashback"
            }

            if update_fields["offer_type"] not in allowed_types:
                raise ValueError(
                    "Invalid offer type."
                )

        if "applicable_to" in update_fields:
            allowed_targets = {
                "all",
                "product",
                "category",
                "variant",
                "user",
                "new_user"
            }

            if update_fields["applicable_to"] not in allowed_targets:
                raise ValueError(
                    "Invalid applicable_to value."
                )

        if "discount_value" in update_fields:
            discount_value = float(
                update_fields["discount_value"]
            )

            if discount_value < 0:
                raise ValueError(
                    "Discount value cannot be negative."
                )

            offer_type = update_fields.get(
                "offer_type",
                existing["offer_type"]
            )

            if (
                offer_type == "percentage"
                and discount_value > 100
            ):
                raise ValueError(
                    "Percentage discount cannot exceed 100."
                )

            update_fields["discount_value"] = discount_value

        if (
            "start_at" in update_fields
            or "end_at" in update_fields
        ):
            start_at = update_fields.get(
                "start_at",
                existing["start_at"]
            )

            end_at = update_fields.get(
                "end_at",
                existing["end_at"]
            )

            start_datetime = _parse_datetime(start_at)
            end_datetime = _parse_datetime(end_at)

            if not start_datetime or not end_datetime:
                raise ValueError(
                    "Invalid start_at or end_at."
                )

            if end_datetime <= start_datetime:
                raise ValueError(
                    "end_at must be after start_at."
                )

        if "usage_limit" in update_fields:
            usage_limit = update_fields["usage_limit"]

            if (
                usage_limit is not None
                and usage_limit < 1
            ):
                raise ValueError(
                    "Usage limit must be greater than zero."
                )

            if (
                usage_limit is not None
                and usage_limit < existing["used_count"]
            ):
                raise ValueError(
                    "Usage limit cannot be less than used count."
                )

        update_fields["updated_at"] = _current_time()

        set_clause = ", ".join(
            f"{key} = ?"
            for key in update_fields
        )

        values = list(update_fields.values())
        values.append(offer_id)

        cursor.execute(
            f"""
            UPDATE offers
            SET {set_clause}
            WHERE offer_id = ?
            AND status != 'deleted'
            """,
            tuple(values)
        )

        connection.commit()

        return get_offer_by_id(offer_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def activate_offer(offer_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM offers
            WHERE offer_id = ?
            AND status != 'deleted'
        """, (offer_id,))

        offer = cursor.fetchone()

        if not offer:
            raise ValueError(
                "Offer not found."
            )

        if (
            offer["usage_limit"] is not None
            and offer["used_count"] >= offer["usage_limit"]
        ):
            raise ValueError(
                "Offer usage limit has been exhausted."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE offers
            SET
                status = 'active',
                is_active = 1,
                updated_at = ?
            WHERE offer_id = ?
        """, (
            current_time,
            offer_id
        ))

        connection.commit()

        return get_offer_by_id(offer_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def pause_offer(offer_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT offer_id
            FROM offers
            WHERE offer_id = ?
            AND status != 'deleted'
        """, (offer_id,))

        if not cursor.fetchone():
            raise ValueError(
                "Offer not found."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE offers
            SET
                status = 'paused',
                is_active = 0,
                updated_at = ?
            WHERE offer_id = ?
        """, (
            current_time,
            offer_id
        ))

        connection.commit()

        return get_offer_by_id(offer_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def calculate_offer_discount(
    offer_id,
    order_amount,
    quantity=1
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM offers
            WHERE offer_id = ?
            AND status != 'deleted'
        """, (offer_id,))

        offer = cursor.fetchone()

        if not offer:
            raise ValueError(
                "Offer not found."
            )

        offer = dict(offer)

        if not _is_offer_valid(offer):
            raise ValueError(
                "Offer is not currently valid."
            )

        order_amount = float(order_amount)

        if order_amount < offer["minimum_order_amount"]:
            raise ValueError(
                "Minimum order amount not reached."
            )

        if (
            offer["maximum_order_amount"] is not None
            and order_amount > offer["maximum_order_amount"]
        ):
            raise ValueError(
                "Maximum order amount exceeded."
            )

        if quantity < offer["minimum_quantity"]:
            raise ValueError(
                "Minimum quantity not reached."
            )

        if (
            offer["maximum_quantity"] is not None
            and quantity > offer["maximum_quantity"]
        ):
            raise ValueError(
                "Maximum quantity exceeded."
            )

        offer_type = offer["offer_type"]
        discount_value = float(
            offer["discount_value"] or 0
        )

        discount_amount = 0

        if offer_type == "percentage":
            discount_amount = (
                order_amount * discount_value / 100
            )

        elif offer_type == "flat":
            discount_amount = discount_value

        elif offer_type == "cashback":
            discount_amount = (
                order_amount * discount_value / 100
            )

        elif offer_type == "free_shipping":
            discount_amount = 0

        elif offer_type == "buy_one_get_one":
            discount_amount = 0

        elif offer_type == "buy_x_get_y":
            discount_amount = 0

        if offer["maximum_discount"] is not None:
            discount_amount = min(
                discount_amount,
                float(offer["maximum_discount"])
            )

        discount_amount = min(
            discount_amount,
            order_amount
        )

        return {
            "offer_id": offer["offer_id"],
            "offer_code": offer["offer_code"],
            "offer_type": offer_type,
            "order_amount": order_amount,
            "quantity": quantity,
            "discount_amount": round(
                discount_amount,
                2
            ),
            "final_amount": round(
                order_amount - discount_amount,
                2
            ),
            "currency": "INR"
        }

    finally:
        connection.close()


def increment_offer_usage(
    offer_id,
    quantity=1
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if quantity < 1:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        cursor.execute("""
            SELECT
                offer_id,
                usage_limit,
                used_count,
                status,
                is_active
            FROM offers
            WHERE offer_id = ?
            AND status != 'deleted'
        """, (offer_id,))

        offer = cursor.fetchone()

        if not offer:
            raise ValueError(
                "Offer not found."
            )

        if not offer["is_active"]:
            raise ValueError(
                "Offer is inactive."
            )

        if offer["status"] != "active":
            raise ValueError(
                "Offer is not active."
            )

        new_used_count = (
            offer["used_count"] + quantity
        )

        if (
            offer["usage_limit"] is not None
            and new_used_count > offer["usage_limit"]
        ):
            raise ValueError(
                "Offer usage limit exceeded."
            )

        current_time = _current_time()

        new_status = "active"

        if (
            offer["usage_limit"] is not None
            and new_used_count >= offer["usage_limit"]
        ):
            new_status = "exhausted"

        cursor.execute("""
            UPDATE offers
            SET
                used_count = ?,
                status = ?,
                is_active = CASE
                    WHEN ? = 'exhausted'
                    THEN 0
                    ELSE is_active
                END,
                updated_at = ?
            WHERE offer_id = ?
        """, (
            new_used_count,
            new_status,
            new_status,
            current_time,
            offer_id
        ))

        connection.commit()

        return get_offer_by_id(offer_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_offer_status(
    offer_id,
    status
):
    allowed_statuses = {
        "draft",
        "scheduled",
        "active",
        "paused",
        "expired",
        "exhausted",
        "blocked",
        "deleted"
    }

    if status not in allowed_statuses:
        raise ValueError(
            "Invalid offer status."
        )

    is_active = 1 if status == "active" else 0

    return update_offer(
        offer_id,
        status=status,
        is_active=is_active
    )


def delete_offer(offer_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT offer_id
            FROM offers
            WHERE offer_id = ?
            AND status != 'deleted'
        """, (offer_id,))

        if not cursor.fetchone():
            raise ValueError(
                "Offer not found."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE offers
            SET
                status = 'deleted',
                is_active = 0,
                deleted_at = ?,
                updated_at = ?
            WHERE offer_id = ?
        """, (
            current_time,
            current_time,
            offer_id
        ))

        connection.commit()

        return {
            "success": True,
            "message": "Offer deleted successfully."
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def refresh_offer_status():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        current_time = _current_time()

        # Scheduled → Active
        cursor.execute("""
            UPDATE offers
            SET
                status = 'active',
                is_active = 1,
                updated_at = ?
            WHERE status = 'scheduled'
            AND start_at <= ?
            AND end_at >= ?
            AND (
                usage_limit IS NULL
                OR used_count < usage_limit
            )
        """, (
            current_time,
            current_time,
            current_time
        ))

        activated_count = cursor.rowcount

        # Active → Expired
        cursor.execute("""
            UPDATE offers
            SET
                status = 'expired',
                is_active = 0,
                updated_at = ?
            WHERE status = 'active'
            AND end_at < ?
        """, (
            current_time,
            current_time
        ))

        expired_count = cursor.rowcount

        # Active → Exhausted
        cursor.execute("""
            UPDATE offers
            SET
                status = 'exhausted',
                is_active = 0,
                updated_at = ?
            WHERE status = 'active'
            AND usage_limit IS NOT NULL
            AND used_count >= usage_limit
        """, (
            current_time,
        ))

        exhausted_count = cursor.rowcount

        connection.commit()

        return {
            "success": True,
            "activated_count": activated_count,
            "expired_count": expired_count,
            "exhausted_count": exhausted_count
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
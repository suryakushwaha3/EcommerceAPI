from database.database import get_db_connection
from datetime import datetime, timezone
import uuid


def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_coupon_id():
    return f"CPN-{uuid.uuid4().hex[:16].upper()}"


def _parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None


def _is_coupon_valid(coupon):
    current_time = datetime.now(timezone.utc)

    start_at = _parse_datetime(coupon["start_at"])
    end_at = _parse_datetime(coupon["end_at"])

    if not start_at or not end_at:
        return False

    if start_at.tzinfo is None:
        start_at = start_at.replace(
            tzinfo=timezone.utc
        )

    if end_at.tzinfo is None:
        end_at = end_at.replace(
            tzinfo=timezone.utc
        )

    if current_time < start_at:
        return False

    if current_time > end_at:
        return False

    if not coupon["is_active"]:
        return False

    if coupon["status"] != "active":
        return False

    if (
        coupon["usage_limit"] is not None
        and coupon["used_count"] >= coupon["usage_limit"]
    ):
        return False

    return True


def _validate_coupon_user_usage(
    cursor,
    coupon_id,
    user_id
):
    """
    Checks whether the user has already used the coupon.

    This requires order-level coupon usage data.
    Current schema stores coupon_id inside orders,
    so usage is calculated from completed/valid orders.
    """

    if not user_id:
        return 0

    cursor.execute("""
        SELECT COUNT(*) AS usage_count
        FROM orders
        WHERE coupon_id = ?
        AND user_id = ?
        AND order_status NOT IN (
            'cancelled',
            'failed'
        )
        AND deleted_at IS NULL
    """, (
        coupon_id,
        user_id
    ))

    result = cursor.fetchone()

    return result["usage_count"] or 0


def create_coupon(
    coupon_code,
    coupon_name,
    start_at,
    end_at,
    discount_type="percentage",
    discount_value=0,
    description=None,
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
    is_first_order_only=False,
    is_stackable=False,
    priority=0,
    created_by=None,
    status="scheduled"
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        allowed_discount_types = {
            "percentage",
            "flat",
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

        if not coupon_code:
            raise ValueError(
                "Coupon code is required."
            )

        if not coupon_name:
            raise ValueError(
                "Coupon name is required."
            )

        coupon_code = coupon_code.strip().upper()

        if discount_type not in allowed_discount_types:
            raise ValueError(
                "Invalid discount type."
            )

        if applicable_to not in allowed_applicable_to:
            raise ValueError(
                "Invalid applicable_to value."
            )

        if status not in allowed_statuses:
            raise ValueError(
                "Invalid coupon status."
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

        cursor.execute("""
            SELECT coupon_id
            FROM coupons
            WHERE coupon_code = ?
        """, (
            coupon_code,
        ))

        if cursor.fetchone():
            raise ValueError(
                "Coupon code already exists."
            )

        discount_value = float(
            discount_value or 0
        )

        if discount_value < 0:
            raise ValueError(
                "Discount value cannot be negative."
            )

        if (
            discount_type == "percentage"
            and discount_value > 100
        ):
            raise ValueError(
                "Percentage discount cannot exceed 100."
            )

        if maximum_discount is not None:
            maximum_discount = float(
                maximum_discount
            )

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

        if usage_limit is not None:
            if usage_limit < 1:
                raise ValueError(
                    "Usage limit must be greater than zero."
                )

        if usage_per_user < 1:
            raise ValueError(
                "Usage per user must be greater than zero."
            )

        if (
            applicable_to not in {
                "all",
                "new_user"
            }
            and not target_id
            and not user_id
        ):
            raise ValueError(
                "Target information is required."
            )

        coupon_id = _generate_coupon_id()
        current_time = _current_time()

        cursor.execute("""
            INSERT INTO coupons (
                coupon_id,
                coupon_code,
                coupon_name,
                description,
                discount_type,
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
                is_first_order_only,
                is_stackable,
                is_active,
                priority,
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
            coupon_id,
            coupon_code,
            coupon_name.strip(),
            description,
            discount_type,
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
            int(is_first_order_only),
            int(is_stackable),
            priority,
            status,
            created_by,
            current_time,
            current_time
        ))

        connection.commit()

        return get_coupon_by_id(coupon_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_coupon_by_id(coupon_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM coupons
            WHERE coupon_id = ?
            AND status != 'deleted'
        """, (
            coupon_id,
        ))

        coupon = cursor.fetchone()

        return dict(coupon) if coupon else None

    finally:
        connection.close()


def get_coupon_by_code(coupon_code):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM coupons
            WHERE coupon_code = ?
            AND status != 'deleted'
        """, (
            coupon_code.strip().upper(),
        ))

        coupon = cursor.fetchone()

        return dict(coupon) if coupon else None

    finally:
        connection.close()


def get_coupons(
    status=None,
    discount_type=None,
    applicable_to=None,
    is_active=None,
    limit=50,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT *
            FROM coupons
            WHERE status != 'deleted'
        """

        params = []

        if status:
            query += """
                AND status = ?
            """
            params.append(status)

        if discount_type:
            query += """
                AND discount_type = ?
            """
            params.append(discount_type)

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


def validate_coupon(
    coupon_code,
    user_id=None,
    product_id=None,
    category_id=None,
    variant_id=None,
    order_amount=0,
    quantity=1,
    is_first_order=False
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        coupon_code = coupon_code.strip().upper()

        cursor.execute("""
            SELECT *
            FROM coupons
            WHERE coupon_code = ?
            AND status != 'deleted'
        """, (
            coupon_code,
        ))

        coupon = cursor.fetchone()

        if not coupon:
            return {
                "valid": False,
                "message": "Invalid coupon code."
            }

        coupon = dict(coupon)

        if not _is_coupon_valid(coupon):
            return {
                "valid": False,
                "message": "Coupon is expired or inactive."
            }

        order_amount = float(order_amount)

        if (
            order_amount
            < coupon["minimum_order_amount"]
        ):
            return {
                "valid": False,
                "message": (
                    f"Minimum order amount is "
                    f"{coupon['minimum_order_amount']}."
                )
            }

        if (
            coupon["maximum_order_amount"] is not None
            and order_amount
            > coupon["maximum_order_amount"]
        ):
            return {
                "valid": False,
                "message": "Maximum order amount exceeded."
            }

        if quantity < coupon["minimum_quantity"]:
            return {
                "valid": False,
                "message": "Minimum quantity requirement not met."
            }

        if (
            coupon["maximum_quantity"] is not None
            and quantity > coupon["maximum_quantity"]
        ):
            return {
                "valid": False,
                "message": "Maximum quantity exceeded."
            }

        applicable_to = coupon["applicable_to"]

        if applicable_to == "product":
            if coupon["target_id"] != product_id:
                return {
                    "valid": False,
                    "message": (
                        "Coupon is not applicable "
                        "to this product."
                    )
                }

        elif applicable_to == "category":
            if coupon["target_id"] != category_id:
                return {
                    "valid": False,
                    "message": (
                        "Coupon is not applicable "
                        "to this category."
                    )
                }

        elif applicable_to == "variant":
            if coupon["target_id"] != variant_id:
                return {
                    "valid": False,
                    "message": (
                        "Coupon is not applicable "
                        "to this variant."
                    )
                }

        elif applicable_to == "user":
            if coupon["user_id"] != user_id:
                return {
                    "valid": False,
                    "message": (
                        "Coupon is not assigned "
                        "to this user."
                    )
                }

        elif applicable_to == "new_user":
            if not user_id:
                return {
                    "valid": False,
                    "message": "Login is required."
                }

            if not is_first_order:
                return {
                    "valid": False,
                    "message": (
                        "Coupon is only for new users."
                    )
                }

        if coupon["is_first_order_only"]:
            if not is_first_order:
                return {
                    "valid": False,
                    "message": (
                        "Coupon is valid only "
                        "for the first order."
                    )
                }

        if user_id:
            user_usage = _validate_coupon_user_usage(
                cursor,
                coupon["coupon_id"],
                user_id
            )

            if (
                user_usage
                >= coupon["usage_per_user"]
            ):
                return {
                    "valid": False,
                    "message": (
                        "You have already used "
                        "this coupon."
                    )
                }

        return {
            "valid": True,
            "message": "Coupon is valid.",
            "coupon": coupon
        }

    finally:
        connection.close()


def calculate_coupon_discount(
    coupon_code,
    order_amount,
    quantity=1,
    user_id=None,
    product_id=None,
    category_id=None,
    variant_id=None,
    is_first_order=False
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        validation = validate_coupon(
            coupon_code=coupon_code,
            user_id=user_id,
            product_id=product_id,
            category_id=category_id,
            variant_id=variant_id,
            order_amount=order_amount,
            quantity=quantity,
            is_first_order=is_first_order
        )

        if not validation["valid"]:
            raise ValueError(
                validation["message"]
            )

        coupon = validation["coupon"]

        order_amount = float(order_amount)
        discount_value = float(
            coupon["discount_value"] or 0
        )

        discount_amount = 0

        if coupon["discount_type"] == "percentage":
            discount_amount = (
                order_amount
                * discount_value
                / 100
            )

        elif coupon["discount_type"] == "flat":
            discount_amount = discount_value

        elif coupon["discount_type"] == "cashback":
            discount_amount = (
                order_amount
                * discount_value
                / 100
            )

        elif coupon["discount_type"] == "free_shipping":
            discount_amount = 0

        if coupon["maximum_discount"] is not None:
            discount_amount = min(
                discount_amount,
                float(coupon["maximum_discount"])
            )

        discount_amount = min(
            discount_amount,
            order_amount
        )

        return {
            "coupon_id": coupon["coupon_id"],
            "coupon_code": coupon["coupon_code"],
            "discount_type": coupon["discount_type"],
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


def increment_coupon_usage(
    coupon_id,
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
                coupon_id,
                usage_limit,
                used_count,
                status,
                is_active
            FROM coupons
            WHERE coupon_id = ?
            AND status != 'deleted'
        """, (
            coupon_id,
        ))

        coupon = cursor.fetchone()

        if not coupon:
            raise ValueError(
                "Coupon not found."
            )

        if not coupon["is_active"]:
            raise ValueError(
                "Coupon is inactive."
            )

        if coupon["status"] != "active":
            raise ValueError(
                "Coupon is not active."
            )

        new_used_count = (
            coupon["used_count"]
            + quantity
        )

        if (
            coupon["usage_limit"] is not None
            and new_used_count
            > coupon["usage_limit"]
        ):
            raise ValueError(
                "Coupon usage limit exceeded."
            )

        current_time = _current_time()

        new_status = "active"

        if (
            coupon["usage_limit"] is not None
            and new_used_count
            >= coupon["usage_limit"]
        ):
            new_status = "exhausted"

        cursor.execute("""
            UPDATE coupons
            SET
                used_count = ?,
                status = ?,
                is_active = CASE
                    WHEN ? = 'exhausted'
                    THEN 0
                    ELSE is_active
                END,
                updated_at = ?
            WHERE coupon_id = ?
        """, (
            new_used_count,
            new_status,
            new_status,
            current_time,
            coupon_id
        ))

        connection.commit()

        return get_coupon_by_id(coupon_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def activate_coupon(coupon_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                coupon_id,
                usage_limit,
                used_count,
                status
            FROM coupons
            WHERE coupon_id = ?
            AND status != 'deleted'
        """, (
            coupon_id,
        ))

        coupon = cursor.fetchone()

        if not coupon:
            raise ValueError(
                "Coupon not found."
            )

        if (
            coupon["usage_limit"] is not None
            and coupon["used_count"]
            >= coupon["usage_limit"]
        ):
            raise ValueError(
                "Coupon usage limit exhausted."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE coupons
            SET
                status = 'active',
                is_active = 1,
                updated_at = ?
            WHERE coupon_id = ?
        """, (
            current_time,
            coupon_id
        ))

        connection.commit()

        return get_coupon_by_id(coupon_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def pause_coupon(coupon_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT coupon_id
            FROM coupons
            WHERE coupon_id = ?
            AND status != 'deleted'
        """, (
            coupon_id,
        ))

        if not cursor.fetchone():
            raise ValueError(
                "Coupon not found."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE coupons
            SET
                status = 'paused',
                is_active = 0,
                updated_at = ?
            WHERE coupon_id = ?
        """, (
            current_time,
            coupon_id
        ))

        connection.commit()

        return get_coupon_by_id(coupon_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_coupon(
    coupon_id,
    **fields
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        allowed_fields = {
            "coupon_code",
            "coupon_name",
            "description",
            "discount_type",
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
            "is_first_order_only",
            "is_stackable",
            "is_active",
            "priority",
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
            FROM coupons
            WHERE coupon_id = ?
            AND status != 'deleted'
        """, (
            coupon_id,
        ))

        existing = cursor.fetchone()

        if not existing:
            raise ValueError(
                "Coupon not found."
            )

        if "coupon_code" in update_fields:
            code = update_fields["coupon_code"]

            if code:
                code = code.strip().upper()

                cursor.execute("""
                    SELECT coupon_id
                    FROM coupons
                    WHERE coupon_code = ?
                    AND coupon_id != ?
                """, (
                    code,
                    coupon_id
                ))

                if cursor.fetchone():
                    raise ValueError(
                        "Coupon code already exists."
                    )

                update_fields["coupon_code"] = code

        if "discount_type" in update_fields:
            allowed_types = {
                "percentage",
                "flat",
                "free_shipping",
                "cashback"
            }

            if (
                update_fields["discount_type"]
                not in allowed_types
            ):
                raise ValueError(
                    "Invalid discount type."
                )

        if "discount_value" in update_fields:
            discount_value = float(
                update_fields["discount_value"]
            )

            if discount_value < 0:
                raise ValueError(
                    "Discount value cannot be negative."
                )

            discount_type = update_fields.get(
                "discount_type",
                existing["discount_type"]
            )

            if (
                discount_type == "percentage"
                and discount_value > 100
            ):
                raise ValueError(
                    "Percentage discount cannot exceed 100."
                )

            update_fields["discount_value"] = (
                discount_value
            )

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

            if (
                not start_datetime
                or not end_datetime
            ):
                raise ValueError(
                    "Invalid start_at or end_at."
                )

            if end_datetime <= start_datetime:
                raise ValueError(
                    "end_at must be after start_at."
                )

        if "usage_limit" in update_fields:
            usage_limit = update_fields[
                "usage_limit"
            ]

            if (
                usage_limit is not None
                and usage_limit < 1
            ):
                raise ValueError(
                    "Usage limit must be greater than zero."
                )

            if (
                usage_limit is not None
                and usage_limit
                < existing["used_count"]
            ):
                raise ValueError(
                    "Usage limit cannot be less "
                    "than used count."
                )

        update_fields["updated_at"] = _current_time()

        set_clause = ", ".join(
            f"{key} = ?"
            for key in update_fields
        )

        values = list(
            update_fields.values()
        )

        values.append(coupon_id)

        cursor.execute(
            f"""
            UPDATE coupons
            SET {set_clause}
            WHERE coupon_id = ?
            AND status != 'deleted'
            """,
            tuple(values)
        )

        connection.commit()

        return get_coupon_by_id(coupon_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_coupon_status(
    coupon_id,
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
            "Invalid coupon status."
        )

    is_active = 1 if status == "active" else 0

    return update_coupon(
        coupon_id,
        status=status,
        is_active=is_active
    )


def delete_coupon(coupon_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT coupon_id
            FROM coupons
            WHERE coupon_id = ?
            AND status != 'deleted'
        """, (
            coupon_id,
        ))

        if not cursor.fetchone():
            raise ValueError(
                "Coupon not found."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE coupons
            SET
                status = 'deleted',
                is_active = 0,
                deleted_at = ?,
                updated_at = ?
            WHERE coupon_id = ?
        """, (
            current_time,
            current_time,
            coupon_id
        ))

        connection.commit()

        return {
            "success": True,
            "message": "Coupon deleted successfully."
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def refresh_coupon_status():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        current_time = _current_time()

        # Scheduled → Active
        cursor.execute("""
            UPDATE coupons
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
            UPDATE coupons
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
            UPDATE coupons
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
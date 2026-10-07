from database.database import get_db_connection
from datetime import datetime, timezone
import uuid


# =========================================================
# HELPERS
# =========================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_review_id():
    return f"REV-{uuid.uuid4().hex[:16].upper()}"


def _validate_user(cursor, user_id):
    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE user_id = ?
        AND account_status = 'active'
        AND deleted_at IS NULL
    """, (user_id,))

    return cursor.fetchone()


def _validate_product(cursor, product_id):
    cursor.execute("""
        SELECT
            product_id,
            product_name,
            status
        FROM products
        WHERE product_id = ?
        AND status = 'active'
        AND deleted_at IS NULL
    """, (product_id,))

    return cursor.fetchone()


def _validate_variant(
    cursor,
    product_id,
    variant_id
):
    if not variant_id:
        return True

    cursor.execute("""
        SELECT variant_id
        FROM product_variants
        WHERE variant_id = ?
        AND product_id = ?
        AND is_active = 1
        AND status = 'active'
        AND deleted_at IS NULL
    """, (
        variant_id,
        product_id
    ))

    return cursor.fetchone() is not None


def _validate_order_item(
    cursor,
    user_id,
    product_id,
    order_id=None,
    order_item_id=None
):
    if not order_item_id:
        return False

    query = """
        SELECT
            oi.order_item_id,
            oi.order_id,
            oi.product_id,
            oi.item_status,
            o.user_id
        FROM order_items oi
        INNER JOIN orders o
            ON oi.order_id = o.order_id
        WHERE oi.order_item_id = ?
        AND oi.product_id = ?
        AND o.user_id = ?
    """

    params = [
        order_item_id,
        product_id,
        user_id
    ]

    if order_id:
        query += """
            AND oi.order_id = ?
        """

        params.append(order_id)

    cursor.execute(
        query,
        tuple(params)
    )

    return cursor.fetchone()


def _get_review_by_id_cursor(
    cursor,
    review_id
):
    cursor.execute("""
        SELECT
            r.*,
            p.product_name
        FROM reviews r
        LEFT JOIN products p
            ON r.product_id = p.product_id
        WHERE r.review_id = ?
        AND r.status != 'deleted'
        AND r.deleted_at IS NULL
    """, (review_id,))

    review = cursor.fetchone()

    return dict(review) if review else None


def _update_product_rating(
    cursor,
    product_id
):
    cursor.execute("""
        SELECT
            COUNT(*) AS total_reviews,

            COALESCE(
                AVG(rating),
                0
            ) AS average_rating,

            SUM(
                CASE
                    WHEN rating = 5 THEN 1
                    ELSE 0
                END
            ) AS five_star_count,

            SUM(
                CASE
                    WHEN rating = 4 THEN 1
                    ELSE 0
                END
            ) AS four_star_count,

            SUM(
                CASE
                    WHEN rating = 3 THEN 1
                    ELSE 0
                END
            ) AS three_star_count,

            SUM(
                CASE
                    WHEN rating = 2 THEN 1
                    ELSE 0
                END
            ) AS two_star_count,

            SUM(
                CASE
                    WHEN rating = 1 THEN 1
                    ELSE 0
                END
            ) AS one_star_count

        FROM reviews
        WHERE product_id = ?
        AND moderation_status = 'approved'
        AND status = 'active'
        AND deleted_at IS NULL
    """, (product_id,))

    rating_data = cursor.fetchone()

    total_reviews = (
        rating_data["total_reviews"] or 0
    )

    average_rating = float(
        rating_data["average_rating"] or 0
    )

    cursor.execute("""
        UPDATE products
        SET
            rating = ?,
            rating_count = ?,
            review_count = ?,
            updated_at = ?
        WHERE product_id = ?
    """, (
        round(average_rating, 2),
        total_reviews,
        total_reviews,
        _current_time(),
        product_id
    ))


# =========================================================
# CREATE REVIEW
# =========================================================

def create_review(
    user_id,
    product_id,
    rating,
    review_title=None,
    review_text=None,
    variant_id=None,
    order_id=None,
    order_item_id=None,
    review_type="text",
    is_anonymous=False,
    is_recommended=True,
    ip_address=None,
    user_agent=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # Validate user
        # -------------------------------------------------

        user = _validate_user(
            cursor,
            user_id
        )

        if not user:
            raise ValueError(
                "User not found or inactive."
            )

        # -------------------------------------------------
        # Validate product
        # -------------------------------------------------

        product = _validate_product(
            cursor,
            product_id
        )

        if not product:
            raise ValueError(
                "Product not found."
            )

        # -------------------------------------------------
        # Validate rating
        # -------------------------------------------------

        try:
            rating = float(rating)

        except (TypeError, ValueError):
            raise ValueError(
                "Invalid rating."
            )

        if rating < 1 or rating > 5:
            raise ValueError(
                "Rating must be between 1 and 5."
            )

        # -------------------------------------------------
        # Validate review type
        # -------------------------------------------------

        allowed_review_types = {
            "text",
            "image",
            "video",
            "text_image",
            "text_video",
            "text_image_video"
        }

        if review_type not in allowed_review_types:
            raise ValueError(
                "Invalid review type."
            )

        # -------------------------------------------------
        # Validate title
        # -------------------------------------------------

        if review_title:

            if len(review_title) > 255:
                raise ValueError(
                    "Review title is too long."
                )

        # -------------------------------------------------
        # Validate review text
        # -------------------------------------------------

        if review_text:

            if len(review_text) > 5000:
                raise ValueError(
                    "Review text is too long."
                )

        # -------------------------------------------------
        # Validate variant
        # -------------------------------------------------

        if variant_id:

            if not _validate_variant(
                cursor,
                product_id,
                variant_id
            ):
                raise ValueError(
                    "Invalid product variant."
                )

        # -------------------------------------------------
        # Prevent duplicate order item review
        # -------------------------------------------------

        if order_item_id:

            cursor.execute("""
                SELECT review_id
                FROM reviews
                WHERE user_id = ?
                AND order_item_id = ?
                AND status != 'deleted'
            """, (
                user_id,
                order_item_id
            ))

            existing_review = cursor.fetchone()

            if existing_review:
                raise ValueError(
                    "You have already reviewed this order item."
                )

        # -------------------------------------------------
        # Verified purchase
        # -------------------------------------------------

        verified_purchase = 0

        if order_item_id:

            order_item = _validate_order_item(
                cursor,
                user_id,
                product_id,
                order_id,
                order_item_id
            )

            if not order_item:
                raise ValueError(
                    "Invalid order item."
                )

            verified_purchase = 1

        # -------------------------------------------------
        # Create review
        # -------------------------------------------------

        review_id = _generate_review_id()
        current_time = _current_time()

        cursor.execute("""
            INSERT INTO reviews (
                review_id,
                product_id,
                variant_id,
                user_id,
                order_id,
                order_item_id,
                rating,
                review_title,
                review_text,
                review_type,
                is_verified_purchase,
                is_anonymous,
                is_featured,
                is_recommended,
                helpful_count,
                not_helpful_count,
                report_count,
                moderation_status,
                edit_count,
                status,
                ip_address,
                user_agent,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, 0, 0, 0,
                'pending', 0, 'active',
                ?, ?, ?, ?
            )
        """, (
            review_id,
            product_id,
            variant_id,
            user_id,
            order_id,
            order_item_id,
            rating,
            review_title,
            review_text,
            review_type,
            verified_purchase,
            int(is_anonymous),
            0,
            int(is_recommended),
            ip_address,
            user_agent,
            current_time,
            current_time
        ))

        connection.commit()

        return _get_review_by_id_cursor(
            cursor,
            review_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# GET REVIEW BY ID
# =========================================================

def get_review_by_id(review_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        return _get_review_by_id_cursor(
            cursor,
            review_id
        )

    finally:
        connection.close()


# =========================================================
# GET PRODUCT REVIEWS
# =========================================================

def get_product_reviews(
    product_id,
    rating=None,
    verified_only=False,
    moderation_status="approved",
    limit=20,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            SELECT
                r.*,
                p.product_name
            FROM reviews r
            LEFT JOIN products p
                ON r.product_id = p.product_id
            WHERE r.product_id = ?
            AND r.status = 'active'
            AND r.deleted_at IS NULL
        """

        params = [
            product_id
        ]

        # -------------------------------------------------
        # Moderation filter
        # -------------------------------------------------

        if moderation_status:

            query += """
                AND r.moderation_status = ?
            """

            params.append(
                moderation_status
            )

        # -------------------------------------------------
        # Rating filter
        # -------------------------------------------------

        if rating is not None:

            query += """
                AND r.rating = ?
            """

            params.append(
                rating
            )

        # -------------------------------------------------
        # Verified purchase filter
        # -------------------------------------------------

        if verified_only:

            query += """
                AND r.is_verified_purchase = 1
            """

        # -------------------------------------------------
        # Pagination
        # -------------------------------------------------

        query += """
            ORDER BY
                r.is_featured DESC,
                r.created_at DESC
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


# =========================================================
# GET USER REVIEWS
# =========================================================

def get_user_reviews(
    user_id,
    limit=20,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                r.*,
                p.product_name
            FROM reviews r
            LEFT JOIN products p
                ON r.product_id = p.product_id
            WHERE r.user_id = ?
            AND r.status != 'deleted'
            AND r.deleted_at IS NULL
            ORDER BY r.created_at DESC
            LIMIT ? OFFSET ?
        """, (
            user_id,
            limit,
            offset
        ))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# =========================================================
# UPDATE REVIEW
# =========================================================

def update_review(
    review_id,
    user_id,
    rating=None,
    review_title=None,
    review_text=None,
    is_recommended=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # Get review
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                review_id,
                product_id,
                rating,
                review_title,
                review_text,
                is_recommended,
                edit_count
            FROM reviews
            WHERE review_id = ?
            AND user_id = ?
            AND status = 'active'
            AND deleted_at IS NULL
        """, (
            review_id,
            user_id
        ))

        review = cursor.fetchone()

        if not review:
            raise ValueError(
                "Review not found or unauthorized."
            )

        # -------------------------------------------------
        # Rating
        # -------------------------------------------------

        if rating is not None:

            try:
                rating = float(rating)

            except (TypeError, ValueError):
                raise ValueError(
                    "Invalid rating."
                )

            if rating < 1 or rating > 5:
                raise ValueError(
                    "Rating must be between 1 and 5."
                )

        else:

            rating = review["rating"]

        # -------------------------------------------------
        # Existing values
        # -------------------------------------------------

        if review_title is None:
            review_title = review["review_title"]

        if review_text is None:
            review_text = review["review_text"]

        if is_recommended is None:
            is_recommended = review["is_recommended"]

        # -------------------------------------------------
        # Validate title
        # -------------------------------------------------

        if review_title:

            if len(review_title) > 255:
                raise ValueError(
                    "Review title is too long."
                )

        # -------------------------------------------------
        # Validate text
        # -------------------------------------------------

        if review_text:

            if len(review_text) > 5000:
                raise ValueError(
                    "Review text is too long."
                )

        current_time = _current_time()

        # -------------------------------------------------
        # Update review
        # -------------------------------------------------

        cursor.execute("""
            UPDATE reviews
            SET
                rating = ?,
                review_title = ?,
                review_text = ?,
                is_recommended = ?,
                edit_count = edit_count + 1,
                last_edited_at = ?,
                moderation_status = 'pending',
                updated_at = ?
            WHERE review_id = ?
            AND user_id = ?
            AND status = 'active'
        """, (
            rating,
            review_title,
            review_text,
            int(is_recommended),
            current_time,
            current_time,
            review_id,
            user_id
        ))

        # -------------------------------------------------
        # Recalculate product rating
        #
        # Review becomes pending after edit, so the
        # product rating must be recalculated.
        # -------------------------------------------------

        _update_product_rating(
            cursor,
            review["product_id"]
        )

        connection.commit()

        return _get_review_by_id_cursor(
            cursor,
            review_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# DELETE REVIEW
# =========================================================

def delete_review(
    review_id,
    user_id
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                product_id
            FROM reviews
            WHERE review_id = ?
            AND user_id = ?
            AND status = 'active'
            AND deleted_at IS NULL
        """, (
            review_id,
            user_id
        ))

        review = cursor.fetchone()

        if not review:

            raise ValueError(
                "Review not found or unauthorized."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE reviews
            SET
                status = 'deleted',
                deleted_at = ?,
                updated_at = ?
            WHERE review_id = ?
            AND user_id = ?
        """, (
            current_time,
            current_time,
            review_id,
            user_id
        ))

        # -------------------------------------------------
        # Update product rating
        # -------------------------------------------------

        _update_product_rating(
            cursor,
            review["product_id"]
        )

        connection.commit()

        return {
            "success": True,
            "message": "Review deleted successfully."
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# MODERATE REVIEW
# =========================================================

def moderate_review(
    review_id,
    moderation_status,
    moderated_by,
    moderation_reason=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        allowed_statuses = {
            "pending",
            "approved",
            "rejected",
            "flagged",
            "hidden"
        }

        if moderation_status not in allowed_statuses:

            raise ValueError(
                "Invalid moderation status."
            )

        if not moderated_by:

            raise ValueError(
                "Moderated by is required."
            )

        # -------------------------------------------------
        # Get review
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                review_id,
                product_id
            FROM reviews
            WHERE review_id = ?
            AND status = 'active'
            AND deleted_at IS NULL
        """, (review_id,))

        review = cursor.fetchone()

        if not review:

            raise ValueError(
                "Review not found."
            )

        current_time = _current_time()

        # -------------------------------------------------
        # Update moderation
        # -------------------------------------------------

        cursor.execute("""
            UPDATE reviews
            SET
                moderation_status = ?,
                moderation_reason = ?,
                moderated_by = ?,
                moderated_at = ?,
                updated_at = ?
            WHERE review_id = ?
        """, (
            moderation_status,
            moderation_reason,
            moderated_by,
            current_time,
            current_time,
            review_id
        ))

        # -------------------------------------------------
        # Update product rating
        # -------------------------------------------------

        _update_product_rating(
            cursor,
            review["product_id"]
        )

        connection.commit()

        return _get_review_by_id_cursor(
            cursor,
            review_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# MARK HELPFUL / NOT HELPFUL
# =========================================================

def mark_helpful(
    review_id,
    helpful=True
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT review_id
            FROM reviews
            WHERE review_id = ?
            AND status = 'active'
            AND deleted_at IS NULL
        """, (review_id,))

        if not cursor.fetchone():

            raise ValueError(
                "Review not found."
            )

        current_time = _current_time()

        if helpful:

            cursor.execute("""
                UPDATE reviews
                SET
                    helpful_count =
                        helpful_count + 1,
                    updated_at = ?
                WHERE review_id = ?
            """, (
                current_time,
                review_id
            ))

        else:

            cursor.execute("""
                UPDATE reviews
                SET
                    not_helpful_count =
                        not_helpful_count + 1,
                    updated_at = ?
                WHERE review_id = ?
            """, (
                current_time,
                review_id
            ))

        connection.commit()

        return _get_review_by_id_cursor(
            cursor,
            review_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# REPORT REVIEW
# =========================================================

def report_review(
    review_id,
    reason=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                review_id,
                report_count
            FROM reviews
            WHERE review_id = ?
            AND status = 'active'
            AND deleted_at IS NULL
        """, (review_id,))

        review = cursor.fetchone()

        if not review:

            raise ValueError(
                "Review not found."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE reviews
            SET
                report_count =
                    report_count + 1,

                moderation_status =
                    CASE
                        WHEN report_count + 1 >= 5
                        THEN 'flagged'
                        ELSE moderation_status
                    END,

                moderation_reason =
                    CASE
                        WHEN ? IS NOT NULL
                        THEN ?
                        ELSE moderation_reason
                    END,

                updated_at = ?

            WHERE review_id = ?
        """, (
            reason,
            reason,
            current_time,
            review_id
        ))

        connection.commit()

        return _get_review_by_id_cursor(
            cursor,
            review_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# SELLER RESPONSE
# =========================================================

def add_seller_response(
    review_id,
    seller_response,
    seller_response_by
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        if not seller_response:

            raise ValueError(
                "Seller response cannot be empty."
            )

        if len(seller_response) > 2000:

            raise ValueError(
                "Seller response is too long."
            )

        if not seller_response_by:

            raise ValueError(
                "Seller response by is required."
            )

        cursor.execute("""
            SELECT review_id
            FROM reviews
            WHERE review_id = ?
            AND status = 'active'
            AND deleted_at IS NULL
        """, (review_id,))

        if not cursor.fetchone():

            raise ValueError(
                "Review not found."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE reviews
            SET
                seller_response = ?,
                seller_response_at = ?,
                seller_response_by = ?,
                updated_at = ?
            WHERE review_id = ?
        """, (
            seller_response,
            current_time,
            seller_response_by,
            current_time,
            review_id
        ))

        connection.commit()

        return _get_review_by_id_cursor(
            cursor,
            review_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# FEATURE / UNFEATURE REVIEW
# =========================================================

def feature_review(
    review_id,
    is_featured=True
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT review_id
            FROM reviews
            WHERE review_id = ?
            AND status = 'active'
            AND deleted_at IS NULL
        """, (review_id,))

        if not cursor.fetchone():

            raise ValueError(
                "Review not found."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE reviews
            SET
                is_featured = ?,
                updated_at = ?
            WHERE review_id = ?
        """, (
            int(is_featured),
            current_time,
            review_id
        ))

        connection.commit()

        return _get_review_by_id_cursor(
            cursor,
            review_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# REVIEW SUMMARY
# =========================================================

def get_review_summary(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                COUNT(*) AS total_reviews,

                COALESCE(
                    ROUND(AVG(rating), 2),
                    0
                ) AS average_rating,

                SUM(
                    CASE
                        WHEN rating = 5
                        THEN 1
                        ELSE 0
                    END
                ) AS five_star_count,

                SUM(
                    CASE
                        WHEN rating = 4
                        THEN 1
                        ELSE 0
                    END
                ) AS four_star_count,

                SUM(
                    CASE
                        WHEN rating = 3
                        THEN 1
                        ELSE 0
                    END
                ) AS three_star_count,

                SUM(
                    CASE
                        WHEN rating = 2
                        THEN 1
                        ELSE 0
                    END
                ) AS two_star_count,

                SUM(
                    CASE
                        WHEN rating = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS one_star_count,

                SUM(
                    CASE
                        WHEN is_verified_purchase = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS verified_review_count

            FROM reviews

            WHERE product_id = ?
            AND moderation_status = 'approved'
            AND status = 'active'
            AND deleted_at IS NULL
        """, (product_id,))

        result = cursor.fetchone()

        if not result:
            return None

        data = dict(result)

        total = data["total_reviews"] or 0

        # -------------------------------------------------
        # Handle SQLite NULL values
        # -------------------------------------------------

        data["five_star_count"] = (
            data["five_star_count"] or 0
        )

        data["four_star_count"] = (
            data["four_star_count"] or 0
        )

        data["three_star_count"] = (
            data["three_star_count"] or 0
        )

        data["two_star_count"] = (
            data["two_star_count"] or 0
        )

        data["one_star_count"] = (
            data["one_star_count"] or 0
        )

        data["verified_review_count"] = (
            data["verified_review_count"] or 0
        )

        # -------------------------------------------------
        # Percentages
        # -------------------------------------------------

        if total > 0:

            data["five_star_percentage"] = round(
                (
                    data["five_star_count"]
                    / total
                ) * 100,
                2
            )

            data["four_star_percentage"] = round(
                (
                    data["four_star_count"]
                    / total
                ) * 100,
                2
            )

            data["three_star_percentage"] = round(
                (
                    data["three_star_count"]
                    / total
                ) * 100,
                2
            )

            data["two_star_percentage"] = round(
                (
                    data["two_star_count"]
                    / total
                ) * 100,
                2
            )

            data["one_star_percentage"] = round(
                (
                    data["one_star_count"]
                    / total
                ) * 100,
                2
            )

        else:

            data["five_star_percentage"] = 0
            data["four_star_percentage"] = 0
            data["three_star_percentage"] = 0
            data["two_star_percentage"] = 0
            data["one_star_percentage"] = 0

        return data

    finally:
        connection.close()
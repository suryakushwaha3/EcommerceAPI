from datetime import datetime, timezone
import secrets

from database.database import get_db_connection


# ============================================================
# Helpers
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_rating_id():
    return f"RAT_{secrets.token_hex(8).upper()}"


def _product_exists(cursor, product_id):
    cursor.execute(
        """
        SELECT product_id
        FROM products
        WHERE product_id = ?
        AND deleted_at IS NULL
        """,
        (product_id,)
    )

    return cursor.fetchone() is not None


def _variant_exists(cursor, variant_id, product_id):
    cursor.execute(
        """
        SELECT variant_id
        FROM product_variants
        WHERE variant_id = ?
        AND product_id = ?
        AND deleted_at IS NULL
        """,
        (
            variant_id,
            product_id
        )
    )

    return cursor.fetchone() is not None


def _calculate_percentages(
    total_ratings,
    five_star_count,
    four_star_count,
    three_star_count,
    two_star_count,
    one_star_count
):
    if total_ratings <= 0:
        return {
            "rating_5_percentage": 0,
            "rating_4_percentage": 0,
            "rating_3_percentage": 0,
            "rating_2_percentage": 0,
            "rating_1_percentage": 0
        }

    return {
        "rating_5_percentage": round(
            (five_star_count / total_ratings) * 100,
            2
        ),
        "rating_4_percentage": round(
            (four_star_count / total_ratings) * 100,
            2
        ),
        "rating_3_percentage": round(
            (three_star_count / total_ratings) * 100,
            2
        ),
        "rating_2_percentage": round(
            (two_star_count / total_ratings) * 100,
            2
        ),
        "rating_1_percentage": round(
            (one_star_count / total_ratings) * 100,
            2
        )
    }


def _calculate_average(
    five_star_count,
    four_star_count,
    three_star_count,
    two_star_count,
    one_star_count
):
    total_ratings = (
        five_star_count
        + four_star_count
        + three_star_count
        + two_star_count
        + one_star_count
    )

    if total_ratings == 0:
        return 0

    total_score = (
        (five_star_count * 5)
        + (four_star_count * 4)
        + (three_star_count * 3)
        + (two_star_count * 2)
        + (one_star_count * 1)
    )

    return round(
        total_score / total_ratings,
        2
    )


# ============================================================
# Create Rating Summary
# ============================================================

def create_rating(
    product_id,
    variant_id=None,
    five_star_count=0,
    four_star_count=0,
    three_star_count=0,
    two_star_count=0,
    one_star_count=0,
    verified_rating_count=0,
    unverified_rating_count=0,
    last_rating_at=None
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # Product validation
        # ----------------------------------------------------

        if not product_id:
            return {
                "success": False,
                "message": "Product ID is required"
            }

        if not _product_exists(cursor, product_id):
            return {
                "success": False,
                "message": "Product not found"
            }

        # ----------------------------------------------------
        # Variant validation
        # ----------------------------------------------------

        if variant_id:

            if not _variant_exists(
                cursor,
                variant_id,
                product_id
            ):
                return {
                    "success": False,
                    "message": "Variant not found for this product"
                }

        # ----------------------------------------------------
        # Validate counts
        # ----------------------------------------------------

        counts = [
            five_star_count,
            four_star_count,
            three_star_count,
            two_star_count,
            one_star_count,
            verified_rating_count,
            unverified_rating_count
        ]

        if any(count < 0 for count in counts):
            return {
                "success": False,
                "message": "Rating counts cannot be negative"
            }

        total_ratings = (
            five_star_count
            + four_star_count
            + three_star_count
            + two_star_count
            + one_star_count
        )

        if (
            verified_rating_count
            + unverified_rating_count
            != total_ratings
        ):
            return {
                "success": False,
                "message": (
                    "Verified and unverified rating count "
                    "must equal total ratings"
                )
            }

        # ----------------------------------------------------
        # Check existing summary
        # ----------------------------------------------------

        if variant_id:

            cursor.execute(
                """
                SELECT rating_id
                FROM ratings
                WHERE product_id = ?
                AND variant_id = ?
                """,
                (
                    product_id,
                    variant_id
                )
            )

        else:

            cursor.execute(
                """
                SELECT rating_id
                FROM ratings
                WHERE product_id = ?
                AND variant_id IS NULL
                """,
                (product_id,)
            )

        if cursor.fetchone():

            return {
                "success": False,
                "message": "Rating summary already exists"
            }

        # ----------------------------------------------------
        # Calculate average
        # ----------------------------------------------------

        average_rating = _calculate_average(
            five_star_count,
            four_star_count,
            three_star_count,
            two_star_count,
            one_star_count
        )

        percentages = _calculate_percentages(
            total_ratings,
            five_star_count,
            four_star_count,
            three_star_count,
            two_star_count,
            one_star_count
        )

        # ----------------------------------------------------
        # Generate ID
        # ----------------------------------------------------

        rating_id = _generate_rating_id()
        current_time = _current_time()

        if last_rating_at is None and total_ratings > 0:
            last_rating_at = current_time

        # ----------------------------------------------------
        # Insert
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO ratings (
                rating_id,
                product_id,
                variant_id,
                total_ratings,
                average_rating,
                five_star_count,
                four_star_count,
                three_star_count,
                two_star_count,
                one_star_count,
                verified_rating_count,
                unverified_rating_count,
                rating_5_percentage,
                rating_4_percentage,
                rating_3_percentage,
                rating_2_percentage,
                rating_1_percentage,
                last_rating_at,
                status,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                rating_id,
                product_id,
                variant_id,
                total_ratings,
                average_rating,
                five_star_count,
                four_star_count,
                three_star_count,
                two_star_count,
                one_star_count,
                verified_rating_count,
                unverified_rating_count,
                percentages["rating_5_percentage"],
                percentages["rating_4_percentage"],
                percentages["rating_3_percentage"],
                percentages["rating_2_percentage"],
                percentages["rating_1_percentage"],
                last_rating_at,
                "active",
                current_time,
                current_time
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Rating created successfully",
            "rating_id": rating_id
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to create rating",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Rating By ID
# ============================================================

def get_rating_by_id(rating_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM ratings
            WHERE rating_id = ?
            """,
            (rating_id,)
        )

        rating = cursor.fetchone()

        if not rating:
            return {
                "success": False,
                "message": "Rating not found"
            }

        return {
            "success": True,
            "rating": dict(rating)
        }

    except Exception as error:

        return {
            "success": False,
            "message": "Failed to get rating",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Product Rating
# ============================================================

def get_product_rating(
    product_id,
    variant_id=None
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        if not _product_exists(cursor, product_id):
            return {
                "success": False,
                "message": "Product not found"
            }

        if variant_id:

            cursor.execute(
                """
                SELECT *
                FROM ratings
                WHERE product_id = ?
                AND variant_id = ?
                AND status = 'active'
                """,
                (
                    product_id,
                    variant_id
                )
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM ratings
                WHERE product_id = ?
                AND variant_id IS NULL
                AND status = 'active'
                """,
                (product_id,)
            )

        rating = cursor.fetchone()

        if not rating:

            return {
                "success": True,
                "product_id": product_id,
                "variant_id": variant_id,
                "rating": None
            }

        return {
            "success": True,
            "product_id": product_id,
            "variant_id": variant_id,
            "rating": dict(rating)
        }

    except Exception as error:

        return {
            "success": False,
            "message": "Failed to get product rating",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get All Ratings For Product
# ============================================================

def get_product_ratings(product_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        if not _product_exists(cursor, product_id):
            return {
                "success": False,
                "message": "Product not found"
            }

        cursor.execute(
            """
            SELECT *
            FROM ratings
            WHERE product_id = ?
            AND status = 'active'
            ORDER BY variant_id IS NOT NULL ASC, id ASC
            """,
            (product_id,)
        )

        ratings = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "product_id": product_id,
            "count": len(ratings),
            "ratings": ratings
        }

    except Exception as error:

        return {
            "success": False,
            "message": "Failed to get product ratings",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Rating Summary
# ============================================================

def update_rating(
    rating_id,
    five_star_count=None,
    four_star_count=None,
    three_star_count=None,
    two_star_count=None,
    one_star_count=None,
    verified_rating_count=None,
    unverified_rating_count=None,
    last_rating_at=None
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM ratings
            WHERE rating_id = ?
            """,
            (rating_id,)
        )

        rating = cursor.fetchone()

        if not rating:

            return {
                "success": False,
                "message": "Rating not found"
            }

        # ----------------------------------------------------
        # Existing values
        # ----------------------------------------------------

        five = (
            five_star_count
            if five_star_count is not None
            else rating["five_star_count"]
        )

        four = (
            four_star_count
            if four_star_count is not None
            else rating["four_star_count"]
        )

        three = (
            three_star_count
            if three_star_count is not None
            else rating["three_star_count"]
        )

        two = (
            two_star_count
            if two_star_count is not None
            else rating["two_star_count"]
        )

        one = (
            one_star_count
            if one_star_count is not None
            else rating["one_star_count"]
        )

        verified = (
            verified_rating_count
            if verified_rating_count is not None
            else rating["verified_rating_count"]
        )

        unverified = (
            unverified_rating_count
            if unverified_rating_count is not None
            else rating["unverified_rating_count"]
        )

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        counts = [
            five,
            four,
            three,
            two,
            one,
            verified,
            unverified
        ]

        if any(count < 0 for count in counts):

            return {
                "success": False,
                "message": "Rating counts cannot be negative"
            }

        total = five + four + three + two + one

        if verified + unverified != total:

            return {
                "success": False,
                "message": (
                    "Verified and unverified rating count "
                    "must equal total ratings"
                )
            }

        # ----------------------------------------------------
        # Calculate
        # ----------------------------------------------------

        average = _calculate_average(
            five,
            four,
            three,
            two,
            one
        )

        percentages = _calculate_percentages(
            total,
            five,
            four,
            three,
            two,
            one
        )

        current_time = _current_time()

        if last_rating_at is None:

            if total > 0:
                last_rating_at = current_time
            else:
                last_rating_at = rating["last_rating_at"]

        # ----------------------------------------------------
        # Update
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE ratings
            SET
                total_ratings = ?,
                average_rating = ?,
                five_star_count = ?,
                four_star_count = ?,
                three_star_count = ?,
                two_star_count = ?,
                one_star_count = ?,
                verified_rating_count = ?,
                unverified_rating_count = ?,
                rating_5_percentage = ?,
                rating_4_percentage = ?,
                rating_3_percentage = ?,
                rating_2_percentage = ?,
                rating_1_percentage = ?,
                last_rating_at = ?,
                updated_at = ?
            WHERE rating_id = ?
            """,
            (
                total,
                average,
                five,
                four,
                three,
                two,
                one,
                verified,
                unverified,
                percentages["rating_5_percentage"],
                percentages["rating_4_percentage"],
                percentages["rating_3_percentage"],
                percentages["rating_2_percentage"],
                percentages["rating_1_percentage"],
                last_rating_at,
                current_time,
                rating_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Rating updated successfully",
            "rating_id": rating_id,
            "average_rating": average,
            "total_ratings": total
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update rating",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Delete Rating
# ============================================================

def delete_rating(rating_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT rating_id
            FROM ratings
            WHERE rating_id = ?
            """,
            (rating_id,)
        )

        rating = cursor.fetchone()

        if not rating:

            return {
                "success": False,
                "message": "Rating not found"
            }

        cursor.execute(
            """
            DELETE FROM ratings
            WHERE rating_id = ?
            """,
            (rating_id,)
        )

        connection.commit()

        return {
            "success": True,
            "message": "Rating deleted successfully",
            "rating_id": rating_id
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to delete rating",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Rating Status
# ============================================================

def update_rating_status(
    rating_id,
    status
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        allowed_status = [
            "active",
            "inactive"
        ]

        if status not in allowed_status:

            return {
                "success": False,
                "message": "Invalid rating status"
            }

        cursor.execute(
            """
            SELECT rating_id
            FROM ratings
            WHERE rating_id = ?
            """,
            (rating_id,)
        )

        if not cursor.fetchone():

            return {
                "success": False,
                "message": "Rating not found"
            }

        current_time = _current_time()

        cursor.execute(
            """
            UPDATE ratings
            SET
                status = ?,
                updated_at = ?
            WHERE rating_id = ?
            """,
            (
                status,
                current_time,
                rating_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Rating status updated successfully",
            "rating_id": rating_id,
            "status": status
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update rating status",
            "error": str(error)
        }

    finally:
        connection.close()
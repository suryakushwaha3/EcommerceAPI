import secrets
from datetime import datetime, timezone

from database.database import get_db_connection


# ============================================================
# Helper Functions
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_highlight_id():
    return "HL_" + secrets.token_hex(8).upper()


# ============================================================
# Create Product Highlight
# ============================================================

def create_product_highlight(
    product_id,
    highlight_text,
    variant_id=None,
    highlight_type="general",
    display_order=0,
    is_featured=0,
    is_active=1
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        highlight_text = highlight_text.strip()

        if not highlight_text:
            return {
                "success": False,
                "message": "Highlight text is required"
            }

        # ----------------------------------------------------
        # Check Product
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM products
            WHERE product_id = ?
            AND deleted_at IS NULL
            """,
            (product_id,)
        )

        if not cursor.fetchone():
            return {
                "success": False,
                "message": "Product not found"
            }

        # ----------------------------------------------------
        # Check Variant
        # ----------------------------------------------------

        if variant_id:

            cursor.execute(
                """
                SELECT id
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

            if not cursor.fetchone():
                return {
                    "success": False,
                    "message": "Variant not found for this product"
                }

        highlight_id = _generate_highlight_id()
        now = _current_time()

        cursor.execute(
            """
            INSERT INTO product_highlights (
                highlight_id,
                product_id,
                variant_id,
                highlight_text,
                highlight_type,
                display_order,
                is_featured,
                is_active,
                status,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                highlight_id,
                product_id,
                variant_id,
                highlight_text,
                highlight_type,
                display_order,
                is_featured,
                is_active,
                "active",
                now,
                now
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product highlight created successfully",
            "highlight_id": highlight_id
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to create product highlight",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Highlight By ID
# ============================================================

def get_product_highlight_by_id(highlight_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM product_highlights
            WHERE highlight_id = ?
            AND deleted_at IS NULL
            """,
            (highlight_id,)
        )

        highlight = cursor.fetchone()

        if not highlight:
            return {
                "success": False,
                "message": "Product highlight not found"
            }

        return {
            "success": True,
            "highlight": dict(highlight)
        }

    finally:
        connection.close()


# ============================================================
# Get Product Highlights
# ============================================================

def get_product_highlights(
    product_id,
    variant_id=None,
    include_inactive=False
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # Check Product
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM products
            WHERE product_id = ?
            AND deleted_at IS NULL
            """,
            (product_id,)
        )

        if not cursor.fetchone():
            return {
                "success": False,
                "message": "Product not found"
            }

        # ----------------------------------------------------
        # Build Query
        # ----------------------------------------------------

        query = """
            SELECT *
            FROM product_highlights
            WHERE product_id = ?
            AND deleted_at IS NULL
        """

        params = [product_id]

        if variant_id:
            query += """
                AND variant_id = ?
            """
            params.append(variant_id)

        if not include_inactive:
            query += """
                AND is_active = 1
                AND status = 'active'
            """

        query += """
            ORDER BY is_featured DESC,
                     display_order ASC,
                     id ASC
        """

        cursor.execute(query, params)

        highlights = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(highlights),
            "highlights": highlights
        }

    finally:
        connection.close()


# ============================================================
# Update Product Highlight
# ============================================================

def update_product_highlight(
    highlight_id,
    **fields
):
    allowed_fields = {
        "highlight_text",
        "variant_id",
        "highlight_type",
        "display_order",
        "is_featured",
        "is_active",
        "status"
    }

    update_fields = []
    values = []

    for field, value in fields.items():

        if field not in allowed_fields:
            continue

        if value is None:
            continue

        if field == "highlight_text":

            value = value.strip()

            if not value:
                return {
                    "success": False,
                    "message": "Highlight text cannot be empty"
                }

        update_fields.append(
            f"{field} = ?"
        )

        values.append(value)

    if not update_fields:
        return {
            "success": False,
            "message": "No valid fields to update"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # Get Existing Highlight
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT product_id
            FROM product_highlights
            WHERE highlight_id = ?
            AND deleted_at IS NULL
            """,
            (highlight_id,)
        )

        highlight = cursor.fetchone()

        if not highlight:
            return {
                "success": False,
                "message": "Product highlight not found"
            }

        product_id = highlight["product_id"]

        # ----------------------------------------------------
        # Validate Variant
        # ----------------------------------------------------

        if "variant_id" in fields and fields["variant_id"]:

            cursor.execute(
                """
                SELECT id
                FROM product_variants
                WHERE variant_id = ?
                AND product_id = ?
                AND deleted_at IS NULL
                """,
                (
                    fields["variant_id"],
                    product_id
                )
            )

            if not cursor.fetchone():
                return {
                    "success": False,
                    "message": "Variant not found for this product"
                }

        # ----------------------------------------------------
        # Update
        # ----------------------------------------------------

        update_fields.append(
            "updated_at = ?"
        )

        values.append(
            _current_time()
        )

        values.append(
            highlight_id
        )

        query = f"""
            UPDATE product_highlights
            SET {", ".join(update_fields)}
            WHERE highlight_id = ?
            AND deleted_at IS NULL
        """

        cursor.execute(
            query,
            values
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product highlight updated successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update product highlight",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Delete Product Highlight - Soft Delete
# ============================================================

def delete_product_highlight(highlight_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        now = _current_time()

        cursor.execute(
            """
            UPDATE product_highlights
            SET status = 'deleted',
                is_active = 0,
                deleted_at = ?,
                updated_at = ?
            WHERE highlight_id = ?
            AND deleted_at IS NULL
            """,
            (
                now,
                now,
                highlight_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Product highlight not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Product highlight deleted successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to delete product highlight",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Highlight Status
# ============================================================

def update_product_highlight_status(
    highlight_id,
    status
):
    allowed_statuses = (
        "active",
        "inactive",
        "draft",
        "blocked",
        "deleted"
    )

    if status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid highlight status"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        now = _current_time()

        deleted_at = (
            now
            if status == "deleted"
            else None
        )

        is_active = (
            1
            if status == "active"
            else 0
        )

        cursor.execute(
            """
            UPDATE product_highlights
            SET status = ?,
                is_active = ?,
                deleted_at = ?,
                updated_at = ?
            WHERE highlight_id = ?
            AND deleted_at IS NULL
            """,
            (
                status,
                is_active,
                deleted_at,
                now,
                highlight_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Product highlight not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": (
                f"Product highlight status changed to {status}"
            )
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update highlight status",
            "error": str(error)
        }

    finally:
        connection.close()
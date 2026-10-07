from datetime import datetime, timezone
import secrets

from database.database import get_db_connection


def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_specification_id():
    return f"SPEC_{secrets.token_hex(8).upper()}"


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


def _variant_exists(cursor, product_id, variant_id):
    cursor.execute(
        """
        SELECT variant_id
        FROM product_variants
        WHERE variant_id = ?
        AND product_id = ?
        AND deleted_at IS NULL
        """,
        (variant_id, product_id)
    )
    return cursor.fetchone() is not None


def create_product_specification(
    product_id,
    specification_name,
    specification_value,
    specification_group=None,
    specification_unit=None,
    variant_id=None,
    display_order=0,
    is_highlighted=0,
    is_searchable=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if not product_id:
            return {
                "success": False,
                "message": "Product ID is required"
            }

        if not specification_name:
            return {
                "success": False,
                "message": "Specification name is required"
            }

        if not specification_value:
            return {
                "success": False,
                "message": "Specification value is required"
            }

        if not _product_exists(cursor, product_id):
            return {
                "success": False,
                "message": "Product not found"
            }

        if variant_id:
            if not _variant_exists(cursor, product_id, variant_id):
                return {
                    "success": False,
                    "message": "Variant not found for this product"
                }

        specification_id = _generate_specification_id()
        current_time = _current_time()

        cursor.execute(
            """
            INSERT INTO product_specifications (
                specification_id,
                product_id,
                variant_id,
                specification_group,
                specification_name,
                specification_value,
                specification_unit,
                display_order,
                is_highlighted,
                is_searchable,
                status,
                created_at,
                updated_at,
                deleted_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                specification_id,
                product_id,
                variant_id,
                specification_group,
                specification_name,
                specification_value,
                specification_unit,
                display_order,
                is_highlighted,
                is_searchable,
                "active",
                current_time,
                current_time,
                None
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product specification created successfully",
            "specification_id": specification_id
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to create product specification",
            "error": str(error)
        }

    finally:
        connection.close()


def get_product_specification_by_id(specification_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM product_specifications
            WHERE specification_id = ?
            AND deleted_at IS NULL
            """,
            (specification_id,)
        )

        row = cursor.fetchone()

        if not row:
            return {
                "success": False,
                "message": "Product specification not found"
            }

        return {
            "success": True,
            "specification": dict(row)
        }

    except Exception as error:
        return {
            "success": False,
            "message": "Failed to get product specification",
            "error": str(error)
        }

    finally:
        connection.close()


def get_product_specifications(
    product_id,
    variant_id=None,
    include_inactive=False
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if not _product_exists(cursor, product_id):
            return {
                "success": False,
                "message": "Product not found"
            }

        query = """
            SELECT *
            FROM product_specifications
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
                AND status = 'active'
            """

        query += """
            ORDER BY
                specification_group ASC,
                display_order ASC,
                id ASC
        """

        cursor.execute(query, tuple(params))

        specifications = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(specifications),
            "specifications": specifications
        }

    except Exception as error:
        return {
            "success": False,
            "message": "Failed to get product specifications",
            "error": str(error)
        }

    finally:
        connection.close()


def update_product_specification(
    specification_id,
    specification_name=None,
    specification_value=None,
    specification_group=None,
    specification_unit=None,
    variant_id=None,
    display_order=None,
    is_highlighted=None,
    is_searchable=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM product_specifications
            WHERE specification_id = ?
            AND deleted_at IS NULL
            """,
            (specification_id,)
        )

        existing = cursor.fetchone()

        if not existing:
            return {
                "success": False,
                "message": "Product specification not found"
            }

        existing = dict(existing)

        if variant_id is not None:
            if variant_id == "":
                variant_id = None
            elif not _variant_exists(
                cursor,
                existing["product_id"],
                variant_id
            ):
                return {
                    "success": False,
                    "message": "Variant not found for this product"
                }

        fields = []
        values = []

        if specification_name is not None:
            fields.append("specification_name = ?")
            values.append(specification_name)

        if specification_value is not None:
            fields.append("specification_value = ?")
            values.append(specification_value)

        if specification_group is not None:
            fields.append("specification_group = ?")
            values.append(specification_group)

        if specification_unit is not None:
            fields.append("specification_unit = ?")
            values.append(specification_unit)

        if variant_id is not None or variant_id == "":
            fields.append("variant_id = ?")
            values.append(variant_id)

        if display_order is not None:
            fields.append("display_order = ?")
            values.append(display_order)

        if is_highlighted is not None:
            fields.append("is_highlighted = ?")
            values.append(is_highlighted)

        if is_searchable is not None:
            fields.append("is_searchable = ?")
            values.append(is_searchable)

        if not fields:
            return {
                "success": False,
                "message": "No fields provided for update"
            }

        current_time = _current_time()

        fields.append("updated_at = ?")
        values.append(current_time)

        values.append(specification_id)

        cursor.execute(
            f"""
            UPDATE product_specifications
            SET {", ".join(fields)}
            WHERE specification_id = ?
            AND deleted_at IS NULL
            """,
            tuple(values)
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product specification updated successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update product specification",
            "error": str(error)
        }

    finally:
        connection.close()


def delete_product_specification(specification_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT specification_id
            FROM product_specifications
            WHERE specification_id = ?
            AND deleted_at IS NULL
            """,
            (specification_id,)
        )

        if not cursor.fetchone():
            return {
                "success": False,
                "message": "Product specification not found"
            }

        current_time = _current_time()

        cursor.execute(
            """
            UPDATE product_specifications
            SET
                status = 'deleted',
                deleted_at = ?,
                updated_at = ?
            WHERE specification_id = ?
            AND deleted_at IS NULL
            """,
            (
                current_time,
                current_time,
                specification_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product specification deleted successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to delete product specification",
            "error": str(error)
        }

    finally:
        connection.close()


def update_product_specification_status(
    specification_id,
    status
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        allowed_statuses = {
            "active",
            "inactive"
        }

        if status not in allowed_statuses:
            return {
                "success": False,
                "message": "Invalid status. Use active or inactive"
            }

        cursor.execute(
            """
            SELECT specification_id
            FROM product_specifications
            WHERE specification_id = ?
            AND deleted_at IS NULL
            """,
            (specification_id,)
        )

        if not cursor.fetchone():
            return {
                "success": False,
                "message": "Product specification not found"
            }

        current_time = _current_time()

        cursor.execute(
            """
            UPDATE product_specifications
            SET
                status = ?,
                updated_at = ?
            WHERE specification_id = ?
            AND deleted_at IS NULL
            """,
            (
                status,
                current_time,
                specification_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product specification status updated successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update specification status",
            "error": str(error)
        }

    finally:
        connection.close()
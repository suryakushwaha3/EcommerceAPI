from datetime import datetime, timezone
import secrets

from database.database import get_db_connection


# ============================================================
# Helpers
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_variant_id():
    return f"VAR_{secrets.token_hex(8).upper()}"


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


def _variant_exists(cursor, variant_id):
    cursor.execute(
        """
        SELECT *
        FROM product_variants
        WHERE variant_id = ?
        AND deleted_at IS NULL
        """,
        (variant_id,)
    )

    return cursor.fetchone()


def _calculate_stock_status(stock_quantity, low_stock_threshold):
    if stock_quantity <= 0:
        return "out_of_stock"

    if stock_quantity <= low_stock_threshold:
        return "low_stock"

    return "in_stock"


# ============================================================
# Create Product Variant
# ============================================================

def create_product_variant(
    product_id,
    variant_name,
    variant_code=None,
    sku=None,
    barcode=None,
    attributes=None,
    mrp=0,
    selling_price=0,
    discount_type="percentage",
    discount_value=0,
    tax_percentage=0,
    currency="INR",
    stock_quantity=0,
    low_stock_threshold=5,
    stock_status=None,
    reserved_quantity=0,
    sold_quantity=0,
    weight=None,
    weight_unit="kg",
    length=None,
    width=None,
    height=None,
    dimension_unit="cm",
    is_default=False,
    is_active=True,
    sort_order=0
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # Required validation
        # ----------------------------------------------------

        if not product_id:
            return {
                "success": False,
                "message": "Product ID is required"
            }

        if not variant_name:
            return {
                "success": False,
                "message": "Variant name is required"
            }

        if not sku:
            return {
                "success": False,
                "message": "SKU is required"
            }

        # ----------------------------------------------------
        # Product validation
        # ----------------------------------------------------

        if not _product_exists(cursor, product_id):
            return {
                "success": False,
                "message": "Product not found"
            }

        # ----------------------------------------------------
        # Numeric validation
        # ----------------------------------------------------

        if mrp < 0:
            return {
                "success": False,
                "message": "MRP cannot be negative"
            }

        if selling_price < 0:
            return {
                "success": False,
                "message": "Selling price cannot be negative"
            }

        if discount_value < 0:
            return {
                "success": False,
                "message": "Discount value cannot be negative"
            }

        if tax_percentage < 0:
            return {
                "success": False,
                "message": "Tax percentage cannot be negative"
            }

        if stock_quantity < 0:
            return {
                "success": False,
                "message": "Stock quantity cannot be negative"
            }

        if low_stock_threshold < 0:
            return {
                "success": False,
                "message": "Low stock threshold cannot be negative"
            }

        if reserved_quantity < 0:
            return {
                "success": False,
                "message": "Reserved quantity cannot be negative"
            }

        if sold_quantity < 0:
            return {
                "success": False,
                "message": "Sold quantity cannot be negative"
            }

        # ----------------------------------------------------
        # Discount validation
        # ----------------------------------------------------

        allowed_discount_types = [
            "percentage",
            "flat",
            "none"
        ]

        if discount_type not in allowed_discount_types:
            return {
                "success": False,
                "message": "Invalid discount type"
            }

        if discount_type == "none":
            discount_value = 0

        if discount_type == "percentage" and discount_value > 100:
            return {
                "success": False,
                "message": "Percentage discount cannot be greater than 100"
            }

        # ----------------------------------------------------
        # Stock status
        # ----------------------------------------------------

        allowed_stock_status = [
            "in_stock",
            "out_of_stock",
            "low_stock",
            "pre_order",
            "discontinued"
        ]

        if stock_status is None:
            stock_status = _calculate_stock_status(
                stock_quantity,
                low_stock_threshold
            )

        if stock_status not in allowed_stock_status:
            return {
                "success": False,
                "message": "Invalid stock status"
            }

        # ----------------------------------------------------
        # Duplicate SKU
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT variant_id
            FROM product_variants
            WHERE sku = ?
            AND deleted_at IS NULL
            """,
            (sku,)
        )

        if cursor.fetchone():
            return {
                "success": False,
                "message": "SKU already exists"
            }

        # ----------------------------------------------------
        # Duplicate variant code
        # ----------------------------------------------------

        if variant_code:

            cursor.execute(
                """
                SELECT variant_id
                FROM product_variants
                WHERE variant_code = ?
                AND deleted_at IS NULL
                """,
                (variant_code,)
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Variant code already exists"
                }

        # ----------------------------------------------------
        # Duplicate barcode
        # ----------------------------------------------------

        if barcode:

            cursor.execute(
                """
                SELECT variant_id
                FROM product_variants
                WHERE barcode = ?
                AND deleted_at IS NULL
                """,
                (barcode,)
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Barcode already exists"
                }

        # ----------------------------------------------------
        # Generate ID and time
        # ----------------------------------------------------

        variant_id = _generate_variant_id()
        current_time = _current_time()

        # ----------------------------------------------------
        # Default variant
        # ----------------------------------------------------

        if is_default:

            cursor.execute(
                """
                UPDATE product_variants
                SET
                    is_default = 0,
                    updated_at = ?
                WHERE product_id = ?
                AND deleted_at IS NULL
                """,
                (
                    current_time,
                    product_id
                )
            )

        # ----------------------------------------------------
        # INSERT
        #
        # Total columns = 31
        # Total values  = 31
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO product_variants (
                variant_id,
                product_id,
                variant_name,
                variant_code,
                sku,
                barcode,
                attributes,
                mrp,
                selling_price,
                discount_type,
                discount_value,
                tax_percentage,
                currency,
                stock_quantity,
                low_stock_threshold,
                stock_status,
                reserved_quantity,
                sold_quantity,
                weight,
                weight_unit,
                length,
                width,
                height,
                dimension_unit,
                is_default,
                is_active,
                sort_order,
                status,
                created_at,
                updated_at,
                deleted_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                variant_id,
                product_id,
                variant_name,
                variant_code,
                sku,
                barcode,
                attributes,
                mrp,
                selling_price,
                discount_type,
                discount_value,
                tax_percentage,
                currency,
                stock_quantity,
                low_stock_threshold,
                stock_status,
                reserved_quantity,
                sold_quantity,
                weight,
                weight_unit,
                length,
                width,
                height,
                dimension_unit,
                1 if is_default else 0,
                1 if is_active else 0,
                sort_order,
                "active",
                current_time,
                current_time,
                None
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product variant created successfully",
            "variant_id": variant_id
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to create product variant",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Variant By ID
# ============================================================

def get_product_variant_by_id(variant_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM product_variants
            WHERE variant_id = ?
            AND deleted_at IS NULL
            """,
            (variant_id,)
        )

        variant = cursor.fetchone()

        if not variant:
            return {
                "success": False,
                "message": "Product variant not found"
            }

        return {
            "success": True,
            "variant": dict(variant)
        }

    except Exception as error:

        return {
            "success": False,
            "message": "Failed to get product variant",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Product Variants
# ============================================================

def get_product_variants(
    product_id,
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

        if include_inactive:

            cursor.execute(
                """
                SELECT *
                FROM product_variants
                WHERE product_id = ?
                AND deleted_at IS NULL
                ORDER BY is_default DESC, sort_order ASC, id ASC
                """,
                (product_id,)
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM product_variants
                WHERE product_id = ?
                AND is_active = 1
                AND status = 'active'
                AND deleted_at IS NULL
                ORDER BY is_default DESC, sort_order ASC, id ASC
                """,
                (product_id,)
            )

        variants = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "product_id": product_id,
            "count": len(variants),
            "variants": variants
        }

    except Exception as error:

        return {
            "success": False,
            "message": "Failed to get product variants",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Product Variant
# ============================================================

def update_product_variant(
    variant_id,
    variant_name=None,
    variant_code=None,
    sku=None,
    barcode=None,
    attributes=None,
    mrp=None,
    selling_price=None,
    discount_type=None,
    discount_value=None,
    tax_percentage=None,
    currency=None,
    stock_quantity=None,
    low_stock_threshold=None,
    stock_status=None,
    reserved_quantity=None,
    sold_quantity=None,
    weight=None,
    weight_unit=None,
    length=None,
    width=None,
    height=None,
    dimension_unit=None,
    is_default=None,
    is_active=None,
    sort_order=None
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        variant = _variant_exists(
            cursor,
            variant_id
        )

        if not variant:
            return {
                "success": False,
                "message": "Product variant not found"
            }

        product_id = variant["product_id"]

        # ----------------------------------------------------
        # Duplicate SKU
        # ----------------------------------------------------

        if sku is not None:

            cursor.execute(
                """
                SELECT variant_id
                FROM product_variants
                WHERE sku = ?
                AND variant_id != ?
                AND deleted_at IS NULL
                """,
                (
                    sku,
                    variant_id
                )
            )

            if cursor.fetchone():

                return {
                    "success": False,
                    "message": "SKU already exists"
                }

        # ----------------------------------------------------
        # Duplicate variant code
        # ----------------------------------------------------

        if variant_code is not None:

            cursor.execute(
                """
                SELECT variant_id
                FROM product_variants
                WHERE variant_code = ?
                AND variant_id != ?
                AND deleted_at IS NULL
                """,
                (
                    variant_code,
                    variant_id
                )
            )

            if cursor.fetchone():

                return {
                    "success": False,
                    "message": "Variant code already exists"
                }

        # ----------------------------------------------------
        # Duplicate barcode
        # ----------------------------------------------------

        if barcode is not None:

            cursor.execute(
                """
                SELECT variant_id
                FROM product_variants
                WHERE barcode = ?
                AND variant_id != ?
                AND deleted_at IS NULL
                """,
                (
                    barcode,
                    variant_id
                )
            )

            if cursor.fetchone():

                return {
                    "success": False,
                    "message": "Barcode already exists"
                }

        # ----------------------------------------------------
        # Existing values
        # ----------------------------------------------------

        final_mrp = (
            mrp
            if mrp is not None
            else variant["mrp"]
        )

        final_selling_price = (
            selling_price
            if selling_price is not None
            else variant["selling_price"]
        )

        final_discount_type = (
            discount_type
            if discount_type is not None
            else variant["discount_type"]
        )

        final_discount_value = (
            discount_value
            if discount_value is not None
            else variant["discount_value"]
        )

        final_stock_quantity = (
            stock_quantity
            if stock_quantity is not None
            else variant["stock_quantity"]
        )

        final_low_stock_threshold = (
            low_stock_threshold
            if low_stock_threshold is not None
            else variant["low_stock_threshold"]
        )

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if final_mrp < 0:
            return {
                "success": False,
                "message": "MRP cannot be negative"
            }

        if final_selling_price < 0:
            return {
                "success": False,
                "message": "Selling price cannot be negative"
            }

        if final_discount_value < 0:
            return {
                "success": False,
                "message": "Discount value cannot be negative"
            }

        if final_stock_quantity < 0:
            return {
                "success": False,
                "message": "Stock quantity cannot be negative"
            }

        if final_low_stock_threshold < 0:
            return {
                "success": False,
                "message": "Low stock threshold cannot be negative"
            }

        allowed_discount_types = [
            "percentage",
            "flat",
            "none"
        ]

        if final_discount_type not in allowed_discount_types:

            return {
                "success": False,
                "message": "Invalid discount type"
            }

        if (
            final_discount_type == "percentage"
            and final_discount_value > 100
        ):

            return {
                "success": False,
                "message": "Percentage discount cannot be greater than 100"
            }

        # ----------------------------------------------------
        # Stock status
        # ----------------------------------------------------

        final_stock_status = (
            stock_status
            if stock_status is not None
            else _calculate_stock_status(
                final_stock_quantity,
                final_low_stock_threshold
            )
        )

        allowed_stock_status = [
            "in_stock",
            "out_of_stock",
            "low_stock",
            "pre_order",
            "discontinued"
        ]

        if final_stock_status not in allowed_stock_status:

            return {
                "success": False,
                "message": "Invalid stock status"
            }

        # ----------------------------------------------------
        # Update time
        # ----------------------------------------------------

        current_time = _current_time()

        # ----------------------------------------------------
        # Default variant
        # ----------------------------------------------------

        if is_default is True:

            cursor.execute(
                """
                UPDATE product_variants
                SET
                    is_default = 0,
                    updated_at = ?
                WHERE product_id = ?
                AND variant_id != ?
                AND deleted_at IS NULL
                """,
                (
                    current_time,
                    product_id,
                    variant_id
                )
            )

        # ----------------------------------------------------
        # Update only supplied fields
        # ----------------------------------------------------

        update_fields = []
        update_values = []

        fields = {
            "variant_name": variant_name,
            "variant_code": variant_code,
            "sku": sku,
            "barcode": barcode,
            "attributes": attributes,
            "mrp": mrp,
            "selling_price": selling_price,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "tax_percentage": tax_percentage,
            "currency": currency,
            "stock_quantity": stock_quantity,
            "low_stock_threshold": low_stock_threshold,
            "stock_status": final_stock_status,
            "reserved_quantity": reserved_quantity,
            "sold_quantity": sold_quantity,
            "weight": weight,
            "weight_unit": weight_unit,
            "length": length,
            "width": width,
            "height": height,
            "dimension_unit": dimension_unit,
            "sort_order": sort_order
        }

        for field, value in fields.items():

            if value is not None:

                update_fields.append(
                    f"{field} = ?"
                )

                update_values.append(value)

        if is_default is not None:

            update_fields.append(
                "is_default = ?"
            )

            update_values.append(
                1 if is_default else 0
            )

        if is_active is not None:

            update_fields.append(
                "is_active = ?"
            )

            update_values.append(
                1 if is_active else 0
            )

        update_fields.append(
            "updated_at = ?"
        )

        update_values.append(
            current_time
        )

        update_values.append(
            variant_id
        )

        cursor.execute(
            f"""
            UPDATE product_variants
            SET {", ".join(update_fields)}
            WHERE variant_id = ?
            AND deleted_at IS NULL
            """,
            tuple(update_values)
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product variant updated successfully",
            "variant_id": variant_id
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update product variant",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Delete Product Variant
# ============================================================

def delete_product_variant(variant_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        variant = _variant_exists(
            cursor,
            variant_id
        )

        if not variant:

            return {
                "success": False,
                "message": "Product variant not found"
            }

        current_time = _current_time()

        cursor.execute(
            """
            UPDATE product_variants
            SET
                status = 'deleted',
                is_active = 0,
                is_default = 0,
                deleted_at = ?,
                updated_at = ?
            WHERE variant_id = ?
            """,
            (
                current_time,
                current_time,
                variant_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product variant deleted successfully",
            "variant_id": variant_id
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to delete product variant",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Variant Status
# ============================================================

def update_product_variant_status(
    variant_id,
    status
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        variant = _variant_exists(
            cursor,
            variant_id
        )

        if not variant:

            return {
                "success": False,
                "message": "Product variant not found"
            }

        allowed_status = [
            "active",
            "inactive",
            "blocked",
            "deleted"
        ]

        if status not in allowed_status:

            return {
                "success": False,
                "message": "Invalid variant status"
            }

        current_time = _current_time()

        is_active = (
            1
            if status == "active"
            else 0
        )

        deleted_at = (
            current_time
            if status == "deleted"
            else None
        )

        cursor.execute(
            """
            UPDATE product_variants
            SET
                status = ?,
                is_active = ?,
                deleted_at = ?,
                updated_at = ?
            WHERE variant_id = ?
            """,
            (
                status,
                is_active,
                deleted_at,
                current_time,
                variant_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product variant status updated successfully",
            "variant_id": variant_id,
            "status": status
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update product variant status",
            "error": str(error)
        }

    finally:
        connection.close()
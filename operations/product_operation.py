import secrets
from datetime import datetime, timezone

from database.database import get_db_connection


# ============================================================
# Helper Functions
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_product_id():
    return "PRD_" + secrets.token_hex(8).upper()


# ============================================================
# Create Product
# ============================================================

def create_product(
    product_name,
    sku,
    selling_price,
    mrp=0,
    slug=None,
    brand_id=None,
    category_id=None,
    subcategory_id=None,
    short_description=None,
    description=None,
    barcode=None,
    product_type="physical",
    discount_type="percentage",
    discount_value=0,
    tax_percentage=0,
    currency="INR",
    stock_status="in_stock",
    seller_id=None,
    is_featured=0,
    is_bestseller=0,
    is_trending=0,
    is_new_arrival=0,
    is_returnable=1,
    is_exchangeable=1,
    return_days=7
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        product_name = product_name.strip()
        sku = sku.strip()

        if slug:
            slug = slug.strip().lower()
        else:
            slug = product_name.lower().replace(" ", "-")

        cursor.execute(
            """
            SELECT id
            FROM products
            WHERE sku = ?
            """,
            (sku,)
        )

        if cursor.fetchone():
            return {
                "success": False,
                "message": "SKU already exists"
            }

        cursor.execute(
            """
            SELECT id
            FROM products
            WHERE slug = ?
            """,
            (slug,)
        )

        if cursor.fetchone():
            return {
                "success": False,
                "message": "Product slug already exists"
            }

        if barcode:
            cursor.execute(
                """
                SELECT id
                FROM products
                WHERE barcode = ?
                """,
                (barcode,)
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Barcode already exists"
                }

        product_id = _generate_product_id()
        now = _current_time()

        cursor.execute(
            """
            INSERT INTO products (
                product_id,
                product_name,
                slug,
                brand_id,
                category_id,
                subcategory_id,
                short_description,
                description,
                sku,
                barcode,
                product_type,
                mrp,
                selling_price,
                discount_type,
                discount_value,
                tax_percentage,
                currency,
                stock_status,
                status,
                is_featured,
                is_bestseller,
                is_trending,
                is_new_arrival,
                is_returnable,
                is_exchangeable,
                return_days,
                seller_id,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                product_id,
                product_name,
                slug,
                brand_id,
                category_id,
                subcategory_id,
                short_description,
                description,
                sku,
                barcode,
                product_type,
                mrp,
                selling_price,
                discount_type,
                discount_value,
                tax_percentage,
                currency,
                stock_status,
                "active",
                is_featured,
                is_bestseller,
                is_trending,
                is_new_arrival,
                is_returnable,
                is_exchangeable,
                return_days,
                seller_id,
                now,
                now
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product created successfully",
            "product_id": product_id
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to create product",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Product By ID
# ============================================================

def get_product_by_id(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE product_id = ?
            AND deleted_at IS NULL
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if not product:
            return {
                "success": False,
                "message": "Product not found"
            }

        return {
            "success": True,
            "product": dict(product)
        }

    finally:
        connection.close()


# ============================================================
# Get Product By SKU
# ============================================================

def get_product_by_sku(sku):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE sku = ?
            AND deleted_at IS NULL
            """,
            (sku.strip(),)
        )

        product = cursor.fetchone()

        if not product:
            return {
                "success": False,
                "message": "Product not found"
            }

        return {
            "success": True,
            "product": dict(product)
        }

    finally:
        connection.close()


# ============================================================
# Get Product By Slug
# ============================================================

def get_product_by_slug(slug):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE slug = ?
            AND deleted_at IS NULL
            """,
            (slug.strip().lower(),)
        )

        product = cursor.fetchone()

        if not product:
            return {
                "success": False,
                "message": "Product not found"
            }

        return {
            "success": True,
            "product": dict(product)
        }

    finally:
        connection.close()


# ============================================================
# Update Product
# ============================================================

def update_product(product_id, **fields):
    allowed_fields = {
        "product_name",
        "slug",
        "brand_id",
        "category_id",
        "subcategory_id",
        "short_description",
        "description",
        "sku",
        "barcode",
        "product_type",
        "mrp",
        "selling_price",
        "discount_type",
        "discount_value",
        "tax_percentage",
        "currency",
        "stock_status",
        "is_featured",
        "is_bestseller",
        "is_trending",
        "is_new_arrival",
        "is_returnable",
        "is_exchangeable",
        "return_days",
        "seller_id",
        "meta_title",
        "meta_description",
        "meta_keywords"
    }

    update_fields = []
    values = []

    for field, value in fields.items():

        if field not in allowed_fields:
            continue

        if value is None:
            continue

        if field == "product_name":
            value = value.strip()

        if field in ("slug", "sku"):
            value = value.strip().lower()

        update_fields.append(f"{field} = ?")
        values.append(value)

    if not update_fields:
        return {
            "success": False,
            "message": "No valid fields to update"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
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

        if "sku" in fields:
            cursor.execute(
                """
                SELECT id
                FROM products
                WHERE sku = ?
                AND product_id != ?
                """,
                (
                    fields["sku"],
                    product_id
                )
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "SKU already exists"
                }

        if "slug" in fields:
            cursor.execute(
                """
                SELECT id
                FROM products
                WHERE slug = ?
                AND product_id != ?
                """,
                (
                    fields["slug"],
                    product_id
                )
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Slug already exists"
                }

        if "barcode" in fields and fields["barcode"]:
            cursor.execute(
                """
                SELECT id
                FROM products
                WHERE barcode = ?
                AND product_id != ?
                """,
                (
                    fields["barcode"],
                    product_id
                )
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Barcode already exists"
                }

        update_fields.append("updated_at = ?")
        values.append(_current_time())

        values.append(product_id)

        query = f"""
            UPDATE products
            SET {", ".join(update_fields)}
            WHERE product_id = ?
            AND deleted_at IS NULL
        """

        cursor.execute(query, values)

        connection.commit()

        return {
            "success": True,
            "message": "Product updated successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update product",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Delete Product - Soft Delete
# ============================================================

def delete_product(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = _current_time()

        cursor.execute(
            """
            UPDATE products
            SET status = 'deleted',
                deleted_at = ?,
                updated_at = ?
            WHERE product_id = ?
            AND deleted_at IS NULL
            """,
            (
                now,
                now,
                product_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Product not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Product deleted successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to delete product",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Product Status
# ============================================================

def update_product_status(product_id, status):
    allowed_statuses = (
        "active",
        "inactive",
        "draft",
        "pending",
        "blocked",
        "deleted"
    )

    if status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid product status"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = _current_time()

        deleted_at = now if status == "deleted" else None

        cursor.execute(
            """
            UPDATE products
            SET status = ?,
                deleted_at = ?,
                updated_at = ?
            WHERE product_id = ?
            AND deleted_at IS NULL
            """,
            (
                status,
                deleted_at,
                now,
                product_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Product not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": f"Product status changed to {status}"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update product status",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Stock Status
# ============================================================

def update_stock_status(product_id, stock_status):
    allowed_statuses = (
        "in_stock",
        "out_of_stock",
        "low_stock",
        "pre_order",
        "coming_soon",
        "discontinued"
    )

    if stock_status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid stock status"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE products
            SET stock_status = ?,
                updated_at = ?
            WHERE product_id = ?
            AND deleted_at IS NULL
            """,
            (
                stock_status,
                _current_time(),
                product_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Product not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Stock status updated successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update stock status",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Search Products
# ============================================================

def search_products(
    search=None,
    category_id=None,
    subcategory_id=None,
    seller_id=None,
    status="active",
    min_price=None,
    max_price=None,
    min_rating=None,
    stock_status=None,
    limit=20,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT *
            FROM products
            WHERE deleted_at IS NULL
        """

        params = []

        if search:
            query += """
                AND (
                    product_name LIKE ?
                    OR sku LIKE ?
                    OR barcode LIKE ?
                    OR short_description LIKE ?
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value,
                search_value
            ])

        if category_id:
            query += " AND category_id = ?"
            params.append(category_id)

        if subcategory_id:
            query += " AND subcategory_id = ?"
            params.append(subcategory_id)

        if seller_id:
            query += " AND seller_id = ?"
            params.append(seller_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        if min_price is not None:
            query += " AND selling_price >= ?"
            params.append(min_price)

        if max_price is not None:
            query += " AND selling_price <= ?"
            params.append(max_price)

        if min_rating is not None:
            query += " AND rating >= ?"
            params.append(min_rating)

        if stock_status:
            query += " AND stock_status = ?"
            params.append(stock_status)

        query += """
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([
            limit,
            offset
        ])

        cursor.execute(query, params)

        products = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(products),
            "products": products
        }

    finally:
        connection.close()


# ============================================================
# Product View Count
# ============================================================

def increment_product_view(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE products
            SET view_count = view_count + 1,
                updated_at = ?
            WHERE product_id = ?
            AND deleted_at IS NULL
            """,
            (
                _current_time(),
                product_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product view updated"
        }

    finally:
        connection.close()


# ============================================================
# Wishlist Count
# ============================================================

def update_wishlist_count(product_id, increment=True):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if increment:
            query = """
                UPDATE products
                SET wishlist_count = wishlist_count + 1,
                    updated_at = ?
                WHERE product_id = ?
            """
        else:
            query = """
                UPDATE products
                SET wishlist_count =
                    CASE
                        WHEN wishlist_count > 0
                        THEN wishlist_count - 1
                        ELSE 0
                    END,
                    updated_at = ?
                WHERE product_id = ?
            """

        cursor.execute(
            query,
            (
                _current_time(),
                product_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Wishlist count updated"
        }

    finally:
        connection.close()


# ============================================================
# Cart Count
# ============================================================

def update_cart_count(product_id, increment=True):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if increment:
            query = """
                UPDATE products
                SET cart_count = cart_count + 1,
                    updated_at = ?
                WHERE product_id = ?
            """
        else:
            query = """
                UPDATE products
                SET cart_count =
                    CASE
                        WHEN cart_count > 0
                        THEN cart_count - 1
                        ELSE 0
                    END,
                    updated_at = ?
                WHERE product_id = ?
            """

        cursor.execute(
            query,
            (
                _current_time(),
                product_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Cart count updated"
        }

    finally:
        connection.close()


# ============================================================
# Purchase Count
# ============================================================

def increment_purchase_count(product_id, quantity=1):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE products
            SET purchase_count = purchase_count + ?,
                updated_at = ?
            WHERE product_id = ?
            AND deleted_at IS NULL
            """,
            (
                quantity,
                _current_time(),
                product_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Purchase count updated"
        }

    finally:
        connection.close()


# ============================================================
# Featured Products
# ============================================================

def get_featured_products(limit=20):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE is_featured = 1
            AND status = 'active'
            AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        products = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "products": products
        }

    finally:
        connection.close()


# ============================================================
# Bestseller Products
# ============================================================

def get_bestseller_products(limit=20):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE is_bestseller = 1
            AND status = 'active'
            AND deleted_at IS NULL
            ORDER BY purchase_count DESC
            LIMIT ?
            """,
            (limit,)
        )

        products = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "products": products
        }

    finally:
        connection.close()


# ============================================================
# Trending Products
# ============================================================

def get_trending_products(limit=20):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE is_trending = 1
            AND status = 'active'
            AND deleted_at IS NULL
            ORDER BY view_count DESC
            LIMIT ?
            """,
            (limit,)
        )

        products = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "products": products
        }

    finally:
        connection.close()


# ============================================================
# New Arrivals
# ============================================================

def get_new_arrivals(limit=20):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE is_new_arrival = 1
            AND status = 'active'
            AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        products = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "products": products
        }

    finally:
        connection.close()

        # ============================================================
# Get Complete Product Details
# ============================================================

def get_product_details(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------
        # Product
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE product_id = ?
            AND deleted_at IS NULL
            """,
            (product_id,)
        )

        product_row = cursor.fetchone()

        if not product_row:
            return {
                "success": False,
                "message": "Product not found"
            }

        product = dict(product_row)

        # ----------------------------------------------------
        # Product Images
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM product_images
            WHERE product_id = ?
            AND deleted_at IS NULL
            AND status = 'active'
            ORDER BY is_primary DESC,
                     is_thumbnail DESC,
                     sort_order ASC,
                     id ASC
            """,
            (product_id,)
        )

        images = [
            dict(row)
            for row in cursor.fetchall()
        ]

        # ----------------------------------------------------
        # Product Highlights
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM product_highlights
            WHERE product_id = ?
            AND deleted_at IS NULL
            AND status = 'active'
            ORDER BY is_featured DESC,
                     display_order ASC,
                     id ASC
            """,
            (product_id,)
        )

        highlights = [
            dict(row)
            for row in cursor.fetchall()
        ]

        # ----------------------------------------------------
        # Product Specifications
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM product_specifications
            WHERE product_id = ?
            AND deleted_at IS NULL
            AND status = 'active'
            ORDER BY display_order ASC,
                     id ASC
            """,
            (product_id,)
        )

        specifications = [
            dict(row)
            for row in cursor.fetchall()
        ]

        # ----------------------------------------------------
        # Product Variants
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM product_variants
            WHERE product_id = ?
            AND deleted_at IS NULL
            AND status = 'active'
            ORDER BY id ASC
            """,
            (product_id,)
        )

        variants = [
            dict(row)
            for row in cursor.fetchall()
        ]

        # ----------------------------------------------------
        # Rating
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM ratings
            WHERE product_id = ?
            AND status = 'active'
            LIMIT 1
            """,
            (product_id,)
        )

        rating_row = cursor.fetchone()

        rating = dict(rating_row) if rating_row else None

        # ----------------------------------------------------
        # Final Response
        # ----------------------------------------------------

        product["images"] = images
        product["highlights"] = highlights
        product["specifications"] = specifications
        product["variants"] = variants
        product["rating"] = rating

        return {
            "success": True,
            "product": product
        }

    except Exception as error:
        return {
            "success": False,
            "message": "Failed to get product details",
            "error": str(error)
        }

    finally:
        connection.close()






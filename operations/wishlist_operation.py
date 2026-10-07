import secrets
from datetime import datetime, timezone

from database.database import get_db_connection


# ============================================================
# Helper Functions
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_wishlist_id():
    return "WIS_" + secrets.token_hex(8).upper()


# ============================================================
# Get Product / Variant Details
# ============================================================

def _get_product_details(
    cursor,
    product_id,
    variant_id=None
):
    if variant_id:

        cursor.execute(
            """
            SELECT
                v.variant_id,
                v.product_id,
                v.variant_name,
                v.sku,
                v.mrp,
                v.selling_price,
                v.stock_quantity,
                v.stock_status,
                v.is_active,
                v.status
            FROM product_variants v
            WHERE v.variant_id = ?
            AND v.product_id = ?
            AND v.deleted_at IS NULL
            """,
            (
                variant_id,
                product_id
            )
        )

        variant = cursor.fetchone()

        if not variant:
            return None

        return {
            "product_id": variant["product_id"],
            "variant_id": variant["variant_id"],
            "variant_name": variant["variant_name"],
            "sku": variant["sku"],
            "mrp": variant["mrp"],
            "selling_price": variant["selling_price"],
            "stock_quantity": variant["stock_quantity"],
            "stock_status": variant["stock_status"],
            "is_active": variant["is_active"],
            "status": variant["status"]
        }

    cursor.execute(
        """
        SELECT
            product_id,
            product_name,
            sku,
            mrp,
            selling_price,
            stock_status,
            status
        FROM products
        WHERE product_id = ?
        AND deleted_at IS NULL
        """,
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        return None

    return {
        "product_id": product["product_id"],
        "variant_id": None,
        "variant_name": None,
        "sku": product["sku"],
        "mrp": product["mrp"],
        "selling_price": product["selling_price"],
        "stock_quantity": None,
        "stock_status": product["stock_status"],
        "is_active": 1 if product["status"] == "active" else 0,
        "status": product["status"]
    }


# ============================================================
# Add To Wishlist
# ============================================================

def add_to_wishlist(
    user_id,
    product_id,
    variant_id=None,
    source="product_page",
    priority=0,
    notify_on_price_drop=False,
    notify_on_stock_available=True,
    notes=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # Validate User
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE user_id = ?
            AND account_status = 'active'
            AND deleted_at IS NULL
            """,
            (user_id,)
        )

        if not cursor.fetchone():
            return {
                "success": False,
                "message": "User not found or inactive"
            }

        # ----------------------------------------------------
        # Validate Source
        # ----------------------------------------------------

        allowed_sources = (
            "product_page",
            "search",
            "category",
            "recommendation",
            "cart",
            "other"
        )

        if source not in allowed_sources:
            return {
                "success": False,
                "message": "Invalid wishlist source"
            }

        # ----------------------------------------------------
        # Validate Product
        # ----------------------------------------------------

        product = _get_product_details(
            cursor,
            product_id,
            variant_id
        )

        if not product:
            return {
                "success": False,
                "message": "Product or variant not found"
            }

        if product["status"] != "active":
            return {
                "success": False,
                "message": "Product is not available"
            }

        if variant_id and not product["is_active"]:
            return {
                "success": False,
                "message": "Product variant is inactive"
            }

        # ----------------------------------------------------
        # Check Existing Wishlist
        # ----------------------------------------------------

        if variant_id:

            cursor.execute(
                """
                SELECT *
                FROM wishlists
                WHERE user_id = ?
                AND product_id = ?
                AND variant_id = ?
                AND status = 'active'
                """,
                (
                    user_id,
                    product_id,
                    variant_id
                )
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM wishlists
                WHERE user_id = ?
                AND product_id = ?
                AND variant_id IS NULL
                AND status = 'active'
                """,
                (
                    user_id,
                    product_id
                )
            )

        existing = cursor.fetchone()

        if existing:

            now = _current_time()

            cursor.execute(
                """
                UPDATE wishlists
                SET current_price = ?,
                    price_changed = ?,
                    notify_on_price_drop = ?,
                    notify_on_stock_available = ?,
                    priority = ?,
                    notes = ?,
                    source = ?,
                    updated_at = ?
                WHERE wishlist_id = ?
                """,
                (
                    product["selling_price"],
                    1
                    if existing["current_price"]
                    != product["selling_price"]
                    else 0,
                    1 if notify_on_price_drop else 0,
                    1 if notify_on_stock_available else 0,
                    priority,
                    notes,
                    source,
                    now,
                    existing["wishlist_id"]
                )
            )

            connection.commit()

            return {
                "success": True,
                "message": "Product already in wishlist; wishlist updated",
                "wishlist_id": existing["wishlist_id"]
            }

        # ----------------------------------------------------
        # Create Wishlist
        # ----------------------------------------------------

        wishlist_id = _generate_wishlist_id()
        now = _current_time()

        cursor.execute(
            """
            INSERT INTO wishlists (
                wishlist_id,
                user_id,
                product_id,
                variant_id,
                added_price,
                current_price,
                price_changed,
                notify_on_price_drop,
                notify_on_stock_available,
                priority,
                notes,
                source,
                status,
                added_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?,
                'active', ?, ?
            )
            """,
            (
                wishlist_id,
                user_id,
                product_id,
                variant_id,
                product["selling_price"],
                product["selling_price"],
                1 if notify_on_price_drop else 0,
                1 if notify_on_stock_available else 0,
                priority,
                notes,
                source,
                now,
                now
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product added to wishlist",
            "wishlist_id": wishlist_id
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to add product to wishlist",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Wishlist Item
# ============================================================

def get_wishlist_item(
    wishlist_id,
    user_id
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                w.*,
                p.product_name,
                p.slug,
                p.product_image
            FROM wishlists w
            LEFT JOIN products p
                ON w.product_id = p.product_id
            WHERE w.wishlist_id = ?
            AND w.user_id = ?
            """,
            (
                wishlist_id,
                user_id
            )
        )

        item = cursor.fetchone()

        if not item:
            return {
                "success": False,
                "message": "Wishlist item not found"
            }

        return {
            "success": True,
            "wishlist": dict(item)
        }

    finally:
        connection.close()


# ============================================================
# Get User Wishlist
# ============================================================

def get_user_wishlist(
    user_id,
    active_only=True,
    priority=None,
    limit=50,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            SELECT
                w.*,
                p.product_name,
                p.slug,
                p.selling_price AS product_current_price,
                p.mrp AS product_mrp,
                p.stock_status AS product_stock_status,
                p.status AS product_status
            FROM wishlists w
            LEFT JOIN products p
                ON w.product_id = p.product_id
            WHERE w.user_id = ?
        """

        params = [user_id]

        if active_only:
            query += """
                AND w.status = 'active'
            """

        if priority is not None:
            query += """
                AND w.priority = ?
            """
            params.append(priority)

        query += """
            ORDER BY
                w.priority DESC,
                w.added_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([
            limit,
            offset
        ])

        cursor.execute(
            query,
            params
        )

        items = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(items),
            "items": items
        }

    finally:
        connection.close()


# ============================================================
# Check Wishlist Item
# ============================================================

def is_in_wishlist(
    user_id,
    product_id,
    variant_id=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        if variant_id:

            cursor.execute(
                """
                SELECT wishlist_id
                FROM wishlists
                WHERE user_id = ?
                AND product_id = ?
                AND variant_id = ?
                AND status = 'active'
                """,
                (
                    user_id,
                    product_id,
                    variant_id
                )
            )

        else:

            cursor.execute(
                """
                SELECT wishlist_id
                FROM wishlists
                WHERE user_id = ?
                AND product_id = ?
                AND variant_id IS NULL
                AND status = 'active'
                """,
                (
                    user_id,
                    product_id
                )
            )

        item = cursor.fetchone()

        return {
            "success": True,
            "is_in_wishlist": item is not None,
            "wishlist_id": (
                item["wishlist_id"]
                if item
                else None
            )
        }

    finally:
        connection.close()


# ============================================================
# Remove From Wishlist
# ============================================================

def remove_from_wishlist(
    wishlist_id,
    user_id
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        now = _current_time()

        cursor.execute(
            """
            UPDATE wishlists
            SET status = 'removed',
                removed_at = ?,
                updated_at = ?
            WHERE wishlist_id = ?
            AND user_id = ?
            AND status = 'active'
            """,
            (
                now,
                now,
                wishlist_id,
                user_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Wishlist item not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Product removed from wishlist"
        }

    finally:
        connection.close()


# ============================================================
# Remove Product From Wishlist
# ============================================================

def remove_product_from_wishlist(
    user_id,
    product_id,
    variant_id=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        now = _current_time()

        if variant_id:

            cursor.execute(
                """
                UPDATE wishlists
                SET status = 'removed',
                    removed_at = ?,
                    updated_at = ?
                WHERE user_id = ?
                AND product_id = ?
                AND variant_id = ?
                AND status = 'active'
                """,
                (
                    now,
                    now,
                    user_id,
                    product_id,
                    variant_id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE wishlists
                SET status = 'removed',
                    removed_at = ?,
                    updated_at = ?
                WHERE user_id = ?
                AND product_id = ?
                AND variant_id IS NULL
                AND status = 'active'
                """,
                (
                    now,
                    now,
                    user_id,
                    product_id
                )
            )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Product not found in wishlist"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Product removed from wishlist"
        }

    finally:
        connection.close()


# ============================================================
# Restore Wishlist Item
# ============================================================

def restore_wishlist_item(
    wishlist_id,
    user_id
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM wishlists
            WHERE wishlist_id = ?
            AND user_id = ?
            AND status = 'removed'
            """,
            (
                wishlist_id,
                user_id
            )
        )

        wishlist = cursor.fetchone()

        if not wishlist:
            return {
                "success": False,
                "message": "Removed wishlist item not found"
            }

        product = _get_product_details(
            cursor,
            wishlist["product_id"],
            wishlist["variant_id"]
        )

        if not product:
            return {
                "success": False,
                "message": "Product is no longer available"
            }

        now = _current_time()

        cursor.execute(
            """
            UPDATE wishlists
            SET status = 'active',
                removed_at = NULL,
                current_price = ?,
                price_changed = ?,
                updated_at = ?
            WHERE wishlist_id = ?
            AND user_id = ?
            AND status = 'removed'
            """,
            (
                product["selling_price"],
                1
                if wishlist["added_price"]
                != product["selling_price"]
                else 0,
                now,
                wishlist_id,
                user_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Wishlist item restored successfully"
        }

    finally:
        connection.close()


# ============================================================
# Update Wishlist Settings
# ============================================================

def update_wishlist_item(
    wishlist_id,
    user_id,
    priority=None,
    notify_on_price_drop=None,
    notify_on_stock_available=None,
    notes=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        update_fields = []
        values = []

        if priority is not None:
            update_fields.append(
                "priority = ?"
            )
            values.append(priority)

        if notify_on_price_drop is not None:
            update_fields.append(
                "notify_on_price_drop = ?"
            )
            values.append(
                1 if notify_on_price_drop else 0
            )

        if notify_on_stock_available is not None:
            update_fields.append(
                "notify_on_stock_available = ?"
            )
            values.append(
                1
                if notify_on_stock_available
                else 0
            )

        if notes is not None:
            update_fields.append(
                "notes = ?"
            )
            values.append(notes)

        if not update_fields:
            return {
                "success": False,
                "message": "No fields to update"
            }

        update_fields.append(
            "updated_at = ?"
        )

        values.append(
            _current_time()
        )

        values.extend([
            wishlist_id,
            user_id
        ])

        query = f"""
            UPDATE wishlists
            SET {", ".join(update_fields)}
            WHERE wishlist_id = ?
            AND user_id = ?
            AND status = 'active'
        """

        cursor.execute(
            query,
            values
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Wishlist item not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Wishlist updated successfully"
        }

    finally:
        connection.close()


# ============================================================
# Update Current Prices
# ============================================================

def refresh_wishlist_prices(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM wishlists
            WHERE user_id = ?
            AND status = 'active'
            """,
            (user_id,)
        )

        wishlist_items = cursor.fetchall()

        updated_count = 0
        price_drop_count = 0
        price_increase_count = 0

        for item in wishlist_items:

            product = _get_product_details(
                cursor,
                item["product_id"],
                item["variant_id"]
            )

            if not product:
                continue

            old_price = item["current_price"]
            new_price = product["selling_price"]

            if old_price != new_price:

                if new_price < old_price:
                    price_drop_count += 1

                else:
                    price_increase_count += 1

                cursor.execute(
                    """
                    UPDATE wishlists
                    SET current_price = ?,
                        price_changed = 1,
                        updated_at = ?
                    WHERE wishlist_id = ?
                    """,
                    (
                        new_price,
                        _current_time(),
                        item["wishlist_id"]
                    )
                )

                updated_count += 1

        connection.commit()

        return {
            "success": True,
            "updated_count": updated_count,
            "price_drop_count": price_drop_count,
            "price_increase_count": price_increase_count
        }

    finally:
        connection.close()


# ============================================================
# Get Price Drop Items
# ============================================================

def get_price_drop_items(
    user_id,
    limit=20,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                w.*,
                p.product_name,
                p.slug,
                p.selling_price AS latest_product_price,
                p.mrp AS product_mrp
            FROM wishlists w
            LEFT JOIN products p
                ON w.product_id = p.product_id
            WHERE w.user_id = ?
            AND w.status = 'active'
            AND w.price_changed = 1
            AND w.current_price < w.added_price
            ORDER BY
                (w.added_price - w.current_price) DESC
            LIMIT ? OFFSET ?
            """,
            (
                user_id,
                limit,
                offset
            )
        )

        items = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(items),
            "items": items
        }

    finally:
        connection.close()


# ============================================================
# Get Out Of Stock Wishlist Items
# ============================================================

def get_out_of_stock_items(
    user_id,
    limit=20,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                w.*,
                p.product_name,
                p.slug,
                p.stock_status,
                p.status AS product_status
            FROM wishlists w
            LEFT JOIN products p
                ON w.product_id = p.product_id
            WHERE w.user_id = ?
            AND w.status = 'active'
            AND (
                p.stock_status = 'out_of_stock'
                OR p.status != 'active'
            )
            ORDER BY w.added_at DESC
            LIMIT ? OFFSET ?
            """,
            (
                user_id,
                limit,
                offset
            )
        )

        items = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(items),
            "items": items
        }

    finally:
        connection.close()


# ============================================================
# Clear Wishlist
# ============================================================

def clear_wishlist(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        now = _current_time()

        cursor.execute(
            """
            UPDATE wishlists
            SET status = 'removed',
                removed_at = ?,
                updated_at = ?
            WHERE user_id = ?
            AND status = 'active'
            """,
            (
                now,
                now,
                user_id
            )
        )

        removed_count = cursor.rowcount

        connection.commit()

        return {
            "success": True,
            "message": "Wishlist cleared successfully",
            "removed_count": removed_count
        }

    finally:
        connection.close()
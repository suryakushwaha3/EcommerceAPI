import secrets
from datetime import datetime, timezone

from database.database import get_db_connection


# ============================================================
# Helper Functions
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_cart_id():
    return "CRT_" + secrets.token_hex(8).upper()


def _to_bool(value, default=True):
    """
    Convert common boolean values safely.

    Supported:
        True / False
        1 / 0
        "true" / "false"
        "1" / "0"
        "yes" / "no"
        "on" / "off"
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        if value == 1:
            return True

        if value == 0:
            return False

    if isinstance(value, str):

        value = value.strip().lower()

        if value in ("true", "1", "yes", "on"):
            return True

        if value in ("false", "0", "no", "off"):
            return False

    return default


# ============================================================
# Get Product / Variant Details
# ============================================================

def _get_product_details(cursor, product_id, variant_id=None):

    # --------------------------------------------------------
    # Variant Product
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Normal Product
    # --------------------------------------------------------

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
# Calculate Cart Item
# ============================================================

def _calculate_item(
    quantity,
    mrp,
    selling_price
):

    quantity = int(quantity)

    mrp = float(mrp or 0)
    selling_price = float(selling_price or 0)

    discount_amount = max(
        0,
        (mrp - selling_price) * quantity
    )

    tax_amount = 0

    total_amount = (
        selling_price * quantity
    ) + tax_amount

    return {
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount
    }


# ============================================================
# Add To Cart
# ============================================================

def add_to_cart(
    user_id,
    product_id,
    quantity=1,
    variant_id=None
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        if quantity <= 0:

            return {
                "success": False,
                "message": "Quantity must be greater than zero"
            }

        # ----------------------------------------------------
        # Verify User
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
        # Get Product / Variant
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

        if variant_id:

            if not product["is_active"]:

                return {
                    "success": False,
                    "message": "Product variant is inactive"
                }

            if product["status"] != "active":

                return {
                    "success": False,
                    "message": "Product variant is not available"
                }

        # ----------------------------------------------------
        # Stock Validation
        # ----------------------------------------------------

        stock_status = product["stock_status"]

        if stock_status in (
            "out_of_stock",
            "unavailable"
        ):

            return {
                "success": False,
                "message": "Product is currently unavailable"
            }

        # ----------------------------------------------------
        # Check Existing Cart Item
        # ----------------------------------------------------

        if variant_id:

            cursor.execute(
                """
                SELECT *
                FROM carts
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
                FROM carts
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

        # ----------------------------------------------------
        # Existing Cart Item
        # ----------------------------------------------------

        if existing:

            new_quantity = (
                existing["quantity"] + quantity
            )

            if (
                variant_id
                and product["stock_quantity"] is not None
                and new_quantity > product["stock_quantity"]
            ):

                return {
                    "success": False,
                    "message": "Requested quantity exceeds available stock"
                }

            calculation = _calculate_item(
                new_quantity,
                product["mrp"],
                product["selling_price"]
            )

            now = _current_time()

            cursor.execute(
                """
                UPDATE carts
                SET quantity = ?,
                    unit_price = ?,
                    mrp = ?,
                    discount_amount = ?,
                    tax_amount = ?,
                    total_amount = ?,
                    stock_status = ?,
                    stock_checked_at = ?,
                    price_changed = ?,
                    updated_at = ?
                WHERE cart_id = ?
                """,
                (
                    new_quantity,
                    product["selling_price"],
                    product["mrp"],
                    calculation["discount_amount"],
                    calculation["tax_amount"],
                    calculation["total_amount"],
                    (
                        "low_stock"
                        if stock_status == "low_stock"
                        else "available"
                    ),
                    now,
                    (
                        1
                        if existing["unit_price"]
                        != product["selling_price"]
                        else 0
                    ),
                    now,
                    existing["cart_id"]
                )
            )

            connection.commit()

            return {
                "success": True,
                "message": "Cart quantity updated",
                "cart_id": existing["cart_id"]
            }

        # ----------------------------------------------------
        # New Cart Item Stock Validation
        # ----------------------------------------------------

        if (
            variant_id
            and product["stock_quantity"] is not None
            and quantity > product["stock_quantity"]
        ):

            return {
                "success": False,
                "message": "Requested quantity exceeds available stock"
            }

        # ----------------------------------------------------
        # Create Cart
        # ----------------------------------------------------

        cart_id = _generate_cart_id()
        now = _current_time()

        calculation = _calculate_item(
            quantity,
            product["mrp"],
            product["selling_price"]
        )

        cart_stock_status = (
            "low_stock"
            if stock_status == "low_stock"
            else "available"
        )

        cursor.execute(
            """
            INSERT INTO carts (
                cart_id,
                user_id,
                product_id,
                variant_id,
                quantity,
                unit_price,
                mrp,
                discount_amount,
                tax_amount,
                total_amount,
                currency,
                is_selected,
                stock_status,
                price_changed,
                stock_checked_at,
                expires_at,
                status,
                added_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                'INR',
                1,
                ?,
                0,
                ?,
                NULL,
                'active',
                ?,
                ?
            )
            """,
            (
                cart_id,
                user_id,
                product_id,
                variant_id,
                quantity,
                product["selling_price"],
                product["mrp"],
                calculation["discount_amount"],
                calculation["tax_amount"],
                calculation["total_amount"],
                cart_stock_status,
                now,
                now,
                now
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product added to cart",
            "cart_id": cart_id
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to add product to cart",
            "error": str(error)
        }

    finally:

        connection.close()


# ============================================================
# Get Cart Item
# ============================================================

def get_cart_item(
    cart_id,
    user_id
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM carts
            WHERE cart_id = ?
            AND user_id = ?
            """,
            (
                cart_id,
                user_id
            )
        )

        cart = cursor.fetchone()

        if not cart:

            return {
                "success": False,
                "message": "Cart item not found"
            }

        return {
            "success": True,
            "cart": dict(cart)
        }

    finally:

        connection.close()


# ============================================================
# Get User Cart
# ============================================================

def get_user_cart(
    user_id,
    selected_only=False,
    include_removed=False
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            SELECT
                c.*,
                p.product_name,
                p.slug,
                p.status AS product_status
            FROM carts c
            LEFT JOIN products p
                ON c.product_id = p.product_id
            WHERE c.user_id = ?
        """

        params = [user_id]

        if not include_removed:

            query += """
                AND c.status IN (
                    'active',
                    'saved_for_later'
                )
            """

        if selected_only:

            query += """
                AND c.is_selected = 1
                AND c.status = 'active'
            """

        query += """
            ORDER BY c.added_at DESC
        """

        cursor.execute(
            query,
            params
        )

        items = [
            dict(row)
            for row in cursor.fetchall()
        ]

        subtotal = 0
        total_mrp = 0
        total_discount = 0
        total_tax = 0

        for item in items:

            if (
                item["status"] == "active"
                and item["is_selected"] == 1
            ):

                subtotal += float(
                    item["total_amount"] or 0
                )

                total_mrp += (
                    float(item["mrp"] or 0)
                    * item["quantity"]
                )

                total_discount += float(
                    item["discount_amount"] or 0
                )

                total_tax += float(
                    item["tax_amount"] or 0
                )

        grand_total = subtotal + total_tax

        return {
            "success": True,
            "count": len(items),
            "items": items,
            "summary": {
                "total_mrp": total_mrp,
                "total_discount": total_discount,
                "subtotal": subtotal,
                "tax_amount": total_tax,
                "shipping_charge": 0,
                "grand_total": grand_total,
                "currency": "INR"
            }
        }

    finally:

        connection.close()


# ============================================================
# Update Cart Quantity
# ============================================================

def update_cart_quantity(
    cart_id,
    user_id,
    quantity
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        if quantity <= 0:

            return remove_from_cart(
                cart_id,
                user_id
            )

        cursor.execute(
            """
            SELECT *
            FROM carts
            WHERE cart_id = ?
            AND user_id = ?
            AND status = 'active'
            """,
            (
                cart_id,
                user_id
            )
        )

        cart = cursor.fetchone()

        if not cart:

            return {
                "success": False,
                "message": "Cart item not found"
            }

        product = _get_product_details(
            cursor,
            cart["product_id"],
            cart["variant_id"]
        )

        if not product:

            return {
                "success": False,
                "message": "Product is no longer available"
            }

        if product["status"] != "active":

            return {
                "success": False,
                "message": "Product is no longer available"
            }

        if cart["variant_id"]:

            if not product["is_active"]:

                return {
                    "success": False,
                    "message": "Product variant is inactive"
                }

            if (
                product["stock_quantity"] is not None
                and quantity > product["stock_quantity"]
            ):

                return {
                    "success": False,
                    "message": "Requested quantity exceeds available stock"
                }

        if product["stock_status"] in (
            "out_of_stock",
            "unavailable"
        ):

            return {
                "success": False,
                "message": "Product is currently unavailable"
            }

        calculation = _calculate_item(
            quantity,
            product["mrp"],
            product["selling_price"]
        )

        now = _current_time()

        price_changed = (
            1
            if cart["unit_price"]
            != product["selling_price"]
            else 0
        )

        cursor.execute(
            """
            UPDATE carts
            SET quantity = ?,
                unit_price = ?,
                mrp = ?,
                discount_amount = ?,
                tax_amount = ?,
                total_amount = ?,
                price_changed = ?,
                stock_status = ?,
                stock_checked_at = ?,
                updated_at = ?
            WHERE cart_id = ?
            AND user_id = ?
            """,
            (
                quantity,
                product["selling_price"],
                product["mrp"],
                calculation["discount_amount"],
                calculation["tax_amount"],
                calculation["total_amount"],
                price_changed,
                (
                    "low_stock"
                    if product["stock_status"] == "low_stock"
                    else "available"
                ),
                now,
                now,
                cart_id,
                user_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Cart quantity updated successfully"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update cart quantity",
            "error": str(error)
        }

    finally:

        connection.close()


# ============================================================
# Remove From Cart
# ============================================================

def remove_from_cart(
    cart_id,
    user_id
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        now = _current_time()

        cursor.execute(
            """
            UPDATE carts
            SET status = 'removed',
                is_selected = 0,
                removed_at = ?,
                updated_at = ?
            WHERE cart_id = ?
            AND user_id = ?
            AND status != 'removed'
            """,
            (
                now,
                now,
                cart_id,
                user_id
            )
        )

        if cursor.rowcount == 0:

            return {
                "success": False,
                "message": "Cart item not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Item removed from cart"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to remove cart item",
            "error": str(error)
        }

    finally:

        connection.close()


# ============================================================
# Save For Later
# ============================================================

def save_for_later(
    cart_id,
    user_id
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        now = _current_time()

        cursor.execute(
            """
            UPDATE carts
            SET status = 'saved_for_later',
                is_selected = 0,
                updated_at = ?
            WHERE cart_id = ?
            AND user_id = ?
            AND status = 'active'
            """,
            (
                now,
                cart_id,
                user_id
            )
        )

        if cursor.rowcount == 0:

            return {
                "success": False,
                "message": "Active cart item not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Item saved for later"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to save item for later",
            "error": str(error)
        }

    finally:

        connection.close()


# ============================================================
# Move Back To Cart
# ============================================================

def move_to_cart(
    cart_id,
    user_id
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM carts
            WHERE cart_id = ?
            AND user_id = ?
            AND status = 'saved_for_later'
            """,
            (
                cart_id,
                user_id
            )
        )

        cart = cursor.fetchone()

        if not cart:

            return {
                "success": False,
                "message": "Saved item not found"
            }

        product = _get_product_details(
            cursor,
            cart["product_id"],
            cart["variant_id"]
        )

        if not product:

            return {
                "success": False,
                "message": "Product is no longer available"
            }

        if product["status"] != "active":

            return {
                "success": False,
                "message": "Product is no longer available"
            }

        if cart["variant_id"]:

            if not product["is_active"]:

                return {
                    "success": False,
                    "message": "Product variant is inactive"
                }

            if (
                product["stock_quantity"] is not None
                and cart["quantity"] > product["stock_quantity"]
            ):

                return {
                    "success": False,
                    "message": "Saved quantity exceeds available stock"
                }

        if product["stock_status"] in (
            "out_of_stock",
            "unavailable"
        ):

            return {
                "success": False,
                "message": "Product is currently unavailable"
            }

        now = _current_time()

        calculation = _calculate_item(
            cart["quantity"],
            product["mrp"],
            product["selling_price"]
        )

        price_changed = (
            1
            if cart["unit_price"]
            != product["selling_price"]
            else 0
        )

        cursor.execute(
            """
            UPDATE carts
            SET status = 'active',
                is_selected = 1,
                unit_price = ?,
                mrp = ?,
                discount_amount = ?,
                tax_amount = ?,
                total_amount = ?,
                price_changed = ?,
                stock_status = ?,
                stock_checked_at = ?,
                updated_at = ?
            WHERE cart_id = ?
            AND user_id = ?
            AND status = 'saved_for_later'
            """,
            (
                product["selling_price"],
                product["mrp"],
                calculation["discount_amount"],
                calculation["tax_amount"],
                calculation["total_amount"],
                price_changed,
                (
                    "low_stock"
                    if product["stock_status"] == "low_stock"
                    else "available"
                ),
                now,
                now,
                cart_id,
                user_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Item moved back to cart"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to move item back to cart",
            "error": str(error)
        }

    finally:

        connection.close()


# ============================================================
# Select Cart Item
# ============================================================

def select_cart_item(
    cart_id,
    user_id,
    selected=True
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        selected = _to_bool(
            selected,
            default=True
        )

        cursor.execute(
            """
            UPDATE carts
            SET is_selected = ?,
                updated_at = ?
            WHERE cart_id = ?
            AND user_id = ?
            AND status = 'active'
            """,
            (
                1 if selected else 0,
                _current_time(),
                cart_id,
                user_id
            )
        )

        if cursor.rowcount == 0:

            return {
                "success": False,
                "message": "Cart item not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": (
                "Cart item selected"
                if selected
                else "Cart item unselected"
            )
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update cart selection",
            "error": str(error)
        }

    finally:

        connection.close()


# ============================================================
# Select / Unselect All
# ============================================================

def select_all_cart_items(
    user_id,
    selected=True
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        selected = _to_bool(
            selected,
            default=True
        )

        selected_value = 1 if selected else 0
        now = _current_time()

        cursor.execute(
            """
            UPDATE carts
            SET is_selected = ?,
                updated_at = ?
            WHERE user_id = ?
            AND status = 'active'
            """,
            (
                selected_value,
                now,
                user_id
            )
        )

        updated_count = cursor.rowcount

        connection.commit()

        return {
            "success": True,
            "message": (
                "All cart items selected"
                if selected
                else "All cart items unselected"
            ),
            "updated_count": updated_count
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update cart selection",
            "error": str(error)
        }

    finally:

        connection.close()


# ============================================================
# Validate Cart
# ============================================================

def validate_cart(
    user_id,
    selected_only=True
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            SELECT *
            FROM carts
            WHERE user_id = ?
            AND status = 'active'
        """

        params = [user_id]

        if selected_only:

            query += """
                AND is_selected = 1
            """

        cursor.execute(
            query,
            params
        )

        cart_items = cursor.fetchall()

        validation_errors = []
        price_updates = []

        for cart in cart_items:

            product = _get_product_details(
                cursor,
                cart["product_id"],
                cart["variant_id"]
            )

            if not product:

                validation_errors.append({
                    "cart_id": cart["cart_id"],
                    "reason": "Product unavailable"
                })

                continue

            if product["status"] != "active":

                validation_errors.append({
                    "cart_id": cart["cart_id"],
                    "reason": "Product inactive"
                })

                continue

            if cart["variant_id"]:

                if not product["is_active"]:

                    validation_errors.append({
                        "cart_id": cart["cart_id"],
                        "reason": "Product variant inactive"
                    })

                    continue

                if (
                    product["stock_quantity"] is not None
                    and cart["quantity"] > product["stock_quantity"]
                ):

                    validation_errors.append({
                        "cart_id": cart["cart_id"],
                        "reason": "Requested quantity exceeds stock",
                        "available_quantity":
                            product["stock_quantity"]
                    })

                    continue

            if product["stock_status"] in (
                "out_of_stock",
                "unavailable"
            ):

                validation_errors.append({
                    "cart_id": cart["cart_id"],
                    "reason": "Out of stock"
                })

                continue

            # ------------------------------------------------
            # Price Change
            # ------------------------------------------------

            if (
                cart["unit_price"]
                != product["selling_price"]
                or cart["mrp"]
                != product["mrp"]
            ):

                price_updates.append({
                    "cart_id": cart["cart_id"],
                    "old_price": cart["unit_price"],
                    "new_price": product["selling_price"],
                    "old_mrp": cart["mrp"],
                    "new_mrp": product["mrp"]
                })

                calculation = _calculate_item(
                    cart["quantity"],
                    product["mrp"],
                    product["selling_price"]
                )

                now = _current_time()

                cursor.execute(
                    """
                    UPDATE carts
                    SET unit_price = ?,
                        mrp = ?,
                        discount_amount = ?,
                        tax_amount = ?,
                        total_amount = ?,
                        price_changed = 1,
                        stock_status = ?,
                        stock_checked_at = ?,
                        updated_at = ?
                    WHERE cart_id = ?
                    """,
                    (
                        product["selling_price"],
                        product["mrp"],
                        calculation["discount_amount"],
                        calculation["tax_amount"],
                        calculation["total_amount"],
                        (
                            "low_stock"
                            if product["stock_status"] == "low_stock"
                            else "available"
                        ),
                        now,
                        now,
                        cart["cart_id"]
                    )
                )

            else:

                # ------------------------------------------------
                # Refresh Stock
                # ------------------------------------------------

                now = _current_time()

                cursor.execute(
                    """
                    UPDATE carts
                    SET stock_status = ?,
                        stock_checked_at = ?,
                        updated_at = ?
                    WHERE cart_id = ?
                    """,
                    (
                        (
                            "low_stock"
                            if product["stock_status"] == "low_stock"
                            else "available"
                        ),
                        now,
                        now,
                        cart["cart_id"]
                    )
                )

        connection.commit()

        return {
            "success": len(validation_errors) == 0,
            "valid": len(validation_errors) == 0,
            "validation_errors": validation_errors,
            "price_updates": price_updates
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "valid": False,
            "message": "Failed to validate cart",
            "error": str(error)
        }

    finally:

        connection.close()


# ============================================================
# Clear Cart
# ============================================================

def clear_cart(
    user_id,
    selected_only=False
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        now = _current_time()

        if selected_only:

            cursor.execute(
                """
                UPDATE carts
                SET status = 'removed',
                    is_selected = 0,
                    removed_at = ?,
                    updated_at = ?
                WHERE user_id = ?
                AND status = 'active'
                AND is_selected = 1
                """,
                (
                    now,
                    now,
                    user_id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE carts
                SET status = 'removed',
                    is_selected = 0,
                    removed_at = ?,
                    updated_at = ?
                WHERE user_id = ?
                AND status IN (
                    'active',
                    'saved_for_later'
                )
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
            "message": "Cart cleared successfully",
            "removed_count": removed_count
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to clear cart",
            "error": str(error)
        }

    finally:

        connection.close()


# ============================================================
# Restore Cart Item
# ============================================================

def restore_cart_item(
    cart_id,
    user_id
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # IMPORTANT:
        # Restore supports both:
        #
        # 1. saved_for_later -> active
        # 2. removed         -> active
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM carts
            WHERE cart_id = ?
            AND user_id = ?
            AND status IN (
                'saved_for_later',
                'removed'
            )
            """,
            (
                cart_id,
                user_id
            )
        )

        cart = cursor.fetchone()

        if not cart:

            return {
                "success": False,
                "message": "Cart item not found or cannot be restored"
            }

        # ----------------------------------------------------
        # Get Latest Product / Variant Details
        # ----------------------------------------------------

        product = _get_product_details(
            cursor,
            cart["product_id"],
            cart["variant_id"]
        )

        if not product:

            return {
                "success": False,
                "message": "Product is no longer available"
            }

        # ----------------------------------------------------
        # Product Status
        # ----------------------------------------------------

        if product["status"] != "active":

            return {
                "success": False,
                "message": "Product is inactive"
            }

        # ----------------------------------------------------
        # Variant Validation
        # ----------------------------------------------------

        if cart["variant_id"]:

            if not product["is_active"]:

                return {
                    "success": False,
                    "message": "Product variant is inactive"
                }

            if (
                product["stock_quantity"] is not None
                and cart["quantity"] > product["stock_quantity"]
            ):

                return {
                    "success": False,
                    "message": "Saved quantity exceeds available stock"
                }

        # ----------------------------------------------------
        # Stock Validation
        # ----------------------------------------------------

        if product["stock_status"] in (
            "out_of_stock",
            "unavailable"
        ):

            return {
                "success": False,
                "message": "Product is currently unavailable"
            }

        # ----------------------------------------------------
        # Recalculate Latest Price
        # ----------------------------------------------------

        now = _current_time()

        calculation = _calculate_item(
            cart["quantity"],
            product["mrp"],
            product["selling_price"]
        )

        price_changed = (
            1
            if (
                float(cart["unit_price"] or 0)
                != float(product["selling_price"] or 0)
                or
                float(cart["mrp"] or 0)
                != float(product["mrp"] or 0)
            )
            else 0
        )

        current_stock_status = (
            "low_stock"
            if product["stock_status"] == "low_stock"
            else "available"
        )

        # ----------------------------------------------------
        # Restore
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE carts
            SET status = 'active',
                is_selected = 1,
                removed_at = NULL,
                unit_price = ?,
                mrp = ?,
                discount_amount = ?,
                tax_amount = ?,
                total_amount = ?,
                price_changed = ?,
                stock_status = ?,
                stock_checked_at = ?,
                updated_at = ?
            WHERE cart_id = ?
            AND user_id = ?
            AND status IN (
                'saved_for_later',
                'removed'
            )
            """,
            (
                product["selling_price"],
                product["mrp"],
                calculation["discount_amount"],
                calculation["tax_amount"],
                calculation["total_amount"],
                price_changed,
                current_stock_status,
                now,
                now,
                cart_id,
                user_id
            )
        )

        if cursor.rowcount == 0:

            connection.rollback()

            return {
                "success": False,
                "message": "Cart item could not be restored"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Cart item restored successfully"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to restore cart item",
            "error": str(error)
        }

    finally:

        connection.close()

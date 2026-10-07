import secrets
from datetime import datetime, timezone

from database.database import get_db_connection


# ============================================================
# Helper Functions
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_order_id():
    return "ORD_" + secrets.token_hex(8).upper()


def _generate_order_number():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(3).upper()

    return f"ORD-{timestamp}-{random_part}"


def _generate_order_item_id():
    return "OIT_" + secrets.token_hex(8).upper()


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
                v.barcode,
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
            "barcode": variant["barcode"],
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
            barcode,
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
        "product_name": product["product_name"],
        "variant_id": None,
        "variant_name": None,
        "sku": product["sku"],
        "barcode": product["barcode"],
        "mrp": product["mrp"],
        "selling_price": product["selling_price"],
        "stock_quantity": None,
        "stock_status": product["stock_status"],
        "is_active": 1 if product["status"] == "active" else 0,
        "status": product["status"]
    }


# ============================================================
# Get Product Image
# ============================================================

def _get_product_image(
    cursor,
    product_id
):
    cursor.execute(
        """
        SELECT image_url
        FROM product_images
        WHERE product_id = ?
        AND status = 'active'
        ORDER BY is_primary DESC, sort_order ASC
        LIMIT 1
        """,
        (product_id,)
    )

    image = cursor.fetchone()

    if image:
        return image["image_url"]

    return None


# ============================================================
# Validate User
# ============================================================

def _validate_user(
    cursor,
    user_id
):
    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        AND account_status = 'active'
        AND deleted_at IS NULL
        """,
        (user_id,)
    )

    return cursor.fetchone()


# ============================================================
# Calculate Item Amount
# ============================================================

def _calculate_item_amount(
    quantity,
    mrp,
    selling_price
):
    gross_mrp = mrp * quantity
    subtotal = selling_price * quantity

    discount_amount = max(
        0,
        gross_mrp - subtotal
    )

    tax_amount = 0
    shipping_charge = 0

    total_amount = (
        subtotal
        + tax_amount
        + shipping_charge
    )

    return {
        "gross_mrp": gross_mrp,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "shipping_charge": shipping_charge,
        "total_amount": total_amount
    }


# ============================================================
# Create Order
# ============================================================

def create_order(
    user_id,
    items,
    shipping_name,
    shipping_phone,
    shipping_address_line1,
    shipping_city,
    shipping_state,
    shipping_pincode,
    payment_method="cod",
    shipping_email=None,
    shipping_address_line2=None,
    shipping_country="India",
    billing_name=None,
    billing_phone=None,
    billing_address_line1=None,
    billing_address_line2=None,
    billing_city=None,
    billing_state=None,
    billing_country=None,
    billing_pincode=None,
    same_as_shipping=True,
    coupon_id=None,
    offer_id=None,
    customer_note=None,
    internal_note=None,
    ip_address=None,
    user_agent=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # Validate User
        # ----------------------------------------------------

        user = _validate_user(
            cursor,
            user_id
        )

        if not user:
            return {
                "success": False,
                "message": "User not found or inactive"
            }

        # ----------------------------------------------------
        # Validate Items
        # ----------------------------------------------------

        if not items or not isinstance(items, list):
            return {
                "success": False,
                "message": "Order items are required"
            }

        # ----------------------------------------------------
        # Validate Payment Method
        # ----------------------------------------------------

        allowed_payment_methods = (
            "cod",
            "upi",
            "card",
            "net_banking",
            "wallet",
            "emi",
            "other"
        )

        if payment_method not in allowed_payment_methods:
            return {
                "success": False,
                "message": "Invalid payment method"
            }

        # ----------------------------------------------------
        # Billing = Shipping
        # ----------------------------------------------------

        if same_as_shipping:

            billing_name = shipping_name
            billing_phone = shipping_phone
            billing_address_line1 = shipping_address_line1
            billing_address_line2 = shipping_address_line2
            billing_city = shipping_city
            billing_state = shipping_state
            billing_country = shipping_country
            billing_pincode = shipping_pincode

        # ----------------------------------------------------
        # Process Items
        # ----------------------------------------------------

        processed_items = []

        subtotal = 0
        total_discount = 0
        total_tax = 0
        total_shipping = 0

        for item in items:

            product_id = item.get("product_id")
            variant_id = item.get("variant_id")
            quantity = item.get("quantity", 1)

            if not product_id:
                connection.rollback()

                return {
                    "success": False,
                    "message": "Product ID is required"
                }

            if quantity <= 0:
                connection.rollback()

                return {
                    "success": False,
                    "message": "Quantity must be greater than zero"
                }

            product = _get_product_details(
                cursor,
                product_id,
                variant_id
            )

            if not product:
                connection.rollback()

                return {
                    "success": False,
                    "message": (
                        f"Product not found: {product_id}"
                    )
                }

            if product["status"] != "active":

                return {
                    "success": False,
                    "message": (
                        f"Product is not available: "
                        f"{product_id}"
                    )
                }

            if variant_id and not product["is_active"]:

                return {
                    "success": False,
                    "message": (
                        f"Product variant is inactive: "
                        f"{variant_id}"
                    )
                }

            # ------------------------------------------------
            # Stock Validation
            # ------------------------------------------------

            if variant_id:

                if (
                    product["stock_quantity"] is None
                    or product["stock_quantity"] < quantity
                ):
                    connection.rollback()

                    return {
                        "success": False,
                        "message": (
                            f"Insufficient stock for "
                            f"{product_id}"
                        )
                    }

            else:

                if product["stock_status"] == "out_of_stock":

                    connection.rollback()

                    return {
                        "success": False,
                        "message": (
                            f"Product is out of stock: "
                            f"{product_id}"
                        )
                    }

            # ------------------------------------------------
            # Calculate Amount
            # ------------------------------------------------

            amount = _calculate_item_amount(
                quantity,
                product["mrp"],
                product["selling_price"]
            )

            product_name = item.get(
                "product_name",
                product.get(
                    "product_name",
                    ""
                )
            )

            product_image = _get_product_image(
                cursor,
                product_id
            )

            processed_item = {
                "product_id": product_id,
                "variant_id": variant_id,
                "product_name": product_name,
                "variant_name": product.get(
                    "variant_name"
                ),
                "sku": product.get("sku"),
                "barcode": product.get("barcode"),
                "product_image": product_image,
                "quantity": quantity,
                "mrp": product["mrp"],
                "selling_price": product["selling_price"],
                "discount_amount": amount[
                    "discount_amount"
                ],
                "tax_amount": amount[
                    "tax_amount"
                ],
                "shipping_charge": amount[
                    "shipping_charge"
                ],
                "total_amount": amount[
                    "total_amount"
                ]
            }

            processed_items.append(
                processed_item
            )

            subtotal += amount["subtotal"]

            total_discount += amount[
                "discount_amount"
            ]

            total_tax += amount[
                "tax_amount"
            ]

            total_shipping += amount[
                "shipping_charge"
            ]

        # ----------------------------------------------------
        # Order Discount
        # ----------------------------------------------------

        coupon_discount = 0

        # Coupon/offer calculation will be handled
        # by coupon_operation.py / offer_operation.py.
        # Here we only preserve the applied IDs.

        discount_amount = total_discount

        total_amount = (
            subtotal
            - coupon_discount
            + total_tax
            + total_shipping
        )

        if total_amount < 0:
            total_amount = 0

        # ----------------------------------------------------
        # Generate Order IDs
        # ----------------------------------------------------

        order_id = _generate_order_id()
        order_number = _generate_order_number()
        now = _current_time()

        # ----------------------------------------------------
        # Payment Status
        # ----------------------------------------------------

        if payment_method == "cod":
            payment_status = "pending"
        else:
            payment_status = "pending"

        # ----------------------------------------------------
        # Create Order
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO orders (
                order_id,
                order_number,
                user_id,
                subtotal,
                discount_amount,
                coupon_discount,
                tax_amount,
                shipping_charge,
                platform_fee,
                total_amount,
                currency,
                coupon_id,
                offer_id,
                payment_method,
                payment_status,
                order_status,
                fulfillment_status,

                shipping_name,
                shipping_phone,
                shipping_email,
                shipping_address_line1,
                shipping_address_line2,
                shipping_city,
                shipping_state,
                shipping_country,
                shipping_pincode,

                billing_name,
                billing_phone,
                billing_address_line1,
                billing_address_line2,
                billing_city,
                billing_state,
                billing_country,
                billing_pincode,

                same_as_shipping,

                customer_note,
                internal_note,

                ip_address,
                user_agent,

                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,

                ?, ?, ?, ?, ?, ?, ?, ?, ?,

                ?, ?, ?, ?, ?, ?, ?, ?,

                ?,

                ?, ?,

                ?, ?,

                ?, ?
            )
            """,
            (
                order_id,
                order_number,
                user_id,
                subtotal,
                discount_amount,
                coupon_discount,
                total_tax,
                total_shipping,
                0,
                total_amount,

                "INR",
                coupon_id,
                offer_id,
                payment_method,
                payment_status,
                "pending",
                "unfulfilled",

                shipping_name,
                shipping_phone,
                shipping_email,
                shipping_address_line1,
                shipping_address_line2,
                shipping_city,
                shipping_state,
                shipping_country,
                shipping_pincode,

                billing_name,
                billing_phone,
                billing_address_line1,
                billing_address_line2,
                billing_city,
                billing_state,
                billing_country,
                billing_pincode,

                1 if same_as_shipping else 0,

                customer_note,
                internal_note,

                ip_address,
                user_agent,

                now,
                now
            )
        )

        # ----------------------------------------------------
        # Create Order Items
        # ----------------------------------------------------

        for item in processed_items:

            order_item_id = _generate_order_item_id()

            cursor.execute(
                """
                INSERT INTO order_items (
                    order_item_id,
                    order_id,
                    product_id,
                    variant_id,
                    seller_id,
                    product_name,
                    variant_name,
                    sku,
                    barcode,
                    product_image,
                    quantity,
                    unit_mrp,
                    unit_price,
                    discount_amount,
                    tax_percentage,
                    tax_amount,
                    shipping_charge,
                    total_amount,
                    currency,
                    item_status,
                    return_allowed,
                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, 0, ?, ?, ?, 'INR',
                    'pending', 1, ?, ?
                )
                """,
                (
                    order_item_id,
                    order_id,
                    item["product_id"],
                    item["variant_id"],
                    None,
                    item["product_name"],
                    item["variant_name"],
                    item["sku"],
                    item["barcode"],
                    item["product_image"],
                    item["quantity"],
                    item["mrp"],
                    item["selling_price"],
                    item["discount_amount"],
                    item["tax_amount"],
                    item["shipping_charge"],
                    item["total_amount"],
                    now,
                    now
                )
            )

            # ------------------------------------------------
            # Update Variant Stock
            # ------------------------------------------------

            if item["variant_id"]:

                cursor.execute(
                    """
                    UPDATE product_variants
                    SET stock_quantity =
                            stock_quantity - ?,
                        sold_quantity =
                            sold_quantity + ?,
                        updated_at = ?
                    WHERE variant_id = ?
                    AND product_id = ?
                    AND stock_quantity >= ?
                    """,
                    (
                        item["quantity"],
                        item["quantity"],
                        now,
                        item["variant_id"],
                        item["product_id"],
                        item["quantity"]
                    )
                )

                if cursor.rowcount == 0:
                    connection.rollback()

                    return {
                        "success": False,
                        "message": (
                            "Stock changed while creating order"
                        )
                    }

        # ----------------------------------------------------
        # Commit Entire Order
        # ----------------------------------------------------

        connection.commit()

        return {
            "success": True,
            "message": "Order created successfully",
            "order_id": order_id,
            "order_number": order_number,
            "total_amount": total_amount,
            "currency": "INR"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to create order",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Order By ID
# ============================================================

def get_order_by_id(
    order_id,
    user_id=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            SELECT *
            FROM orders
            WHERE order_id = ?
            AND deleted_at IS NULL
        """

        params = [order_id]

        if user_id:
            query += """
                AND user_id = ?
            """

            params.append(user_id)

        cursor.execute(
            query,
            params
        )

        order = cursor.fetchone()

        if not order:
            return {
                "success": False,
                "message": "Order not found"
            }

        cursor.execute(
            """
            SELECT *
            FROM order_items
            WHERE order_id = ?
            AND deleted_at IS NULL
            ORDER BY created_at ASC
            """,
            (order_id,)
        )

        items = [
            dict(row)
            for row in cursor.fetchall()
        ]

        order_data = dict(order)
        order_data["items"] = items

        return {
            "success": True,
            "order": order_data
        }

    finally:
        connection.close()


# ============================================================
# Get Order By Order Number
# ============================================================

def get_order_by_number(
    order_number,
    user_id=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            SELECT *
            FROM orders
            WHERE order_number = ?
            AND deleted_at IS NULL
        """

        params = [order_number]

        if user_id:
            query += """
                AND user_id = ?
            """

            params.append(user_id)

        cursor.execute(
            query,
            params
        )

        order = cursor.fetchone()

        if not order:
            return {
                "success": False,
                "message": "Order not found"
            }

        cursor.execute(
            """
            SELECT *
            FROM order_items
            WHERE order_id = ?
            AND deleted_at IS NULL
            ORDER BY created_at ASC
            """,
            (order["order_id"],)
        )

        items = [
            dict(row)
            for row in cursor.fetchall()
        ]

        order_data = dict(order)
        order_data["items"] = items

        return {
            "success": True,
            "order": order_data
        }

    finally:
        connection.close()


# ============================================================
# Get User Orders
# ============================================================

def get_user_orders(
    user_id,
    order_status=None,
    payment_status=None,
    limit=20,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            SELECT *
            FROM orders
            WHERE user_id = ?
            AND deleted_at IS NULL
        """

        params = [user_id]

        if order_status:

            query += """
                AND order_status = ?
            """

            params.append(order_status)

        if payment_status:

            query += """
                AND payment_status = ?
            """

            params.append(payment_status)

        query += """
            ORDER BY created_at DESC
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

        orders = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(orders),
            "orders": orders
        }

    finally:
        connection.close()


# ============================================================
# Get All Orders
# ============================================================

def get_orders(
    order_status=None,
    payment_status=None,
    user_id=None,
    limit=50,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            SELECT *
            FROM orders
            WHERE deleted_at IS NULL
        """

        params = []

        if order_status:

            query += """
                AND order_status = ?
            """

            params.append(order_status)

        if payment_status:

            query += """
                AND payment_status = ?
            """

            params.append(payment_status)

        if user_id:

            query += """
                AND user_id = ?
            """

            params.append(user_id)

        query += """
            ORDER BY created_at DESC
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

        orders = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(orders),
            "orders": orders
        }

    finally:
        connection.close()


# ============================================================
# Update Order Status
# ============================================================

def update_order_status(
    order_id,
    order_status
):
    allowed_statuses = (
        "pending",
        "confirmed",
        "processing",
        "packed",
        "shipped",
        "out_for_delivery",
        "delivered",
        "cancelled",
        "returned",
        "partially_returned",
        "refunded",
        "failed"
    )

    if order_status not in allowed_statuses:

        return {
            "success": False,
            "message": "Invalid order status"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT order_status
            FROM orders
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (order_id,)
        )

        order = cursor.fetchone()

        if not order:

            return {
                "success": False,
                "message": "Order not found"
            }

        now = _current_time()

        shipped_at = None
        delivered_at = None
        cancelled_at = None

        if order_status == "shipped":
            shipped_at = now

        elif order_status == "delivered":
            delivered_at = now

        elif order_status == "cancelled":
            cancelled_at = now

        cursor.execute(
            """
            UPDATE orders
            SET order_status = ?,
                shipped_at = COALESCE(?, shipped_at),
                delivered_at = COALESCE(?, delivered_at),
                cancelled_at = COALESCE(?, cancelled_at),
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (
                order_status,
                shipped_at,
                delivered_at,
                cancelled_at,
                now,
                order_id
            )
        )

        cursor.execute(
            """
            UPDATE order_items
            SET item_status = ?,
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (
                order_status,
                now,
                order_id
            )
        )

        if order_status == "delivered":

            cursor.execute(
                """
                UPDATE orders
                SET fulfillment_status = 'fulfilled',
                    updated_at = ?
                WHERE order_id = ?
                """,
                (
                    now,
                    order_id
                )
            )

        elif order_status == "cancelled":

            cursor.execute(
                """
                UPDATE orders
                SET fulfillment_status = 'cancelled',
                    updated_at = ?
                WHERE order_id = ?
                """,
                (
                    now,
                    order_id
                )
            )

        elif order_status in (
            "confirmed",
            "processing",
            "packed",
            "shipped",
            "out_for_delivery"
        ):

            cursor.execute(
                """
                UPDATE orders
                SET fulfillment_status = 'fulfilled',
                    updated_at = ?
                WHERE order_id = ?
                """,
                (
                    now,
                    order_id
                )
            )

        connection.commit()

        return {
            "success": True,
            "message": (
                f"Order status changed to "
                f"{order_status}"
            )
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update order status",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Confirm Order
# ============================================================

def confirm_order(order_id):
    return update_order_status(
        order_id,
        "confirmed"
    )


# ============================================================
# Mark Order Processing
# ============================================================

def process_order(order_id):
    return update_order_status(
        order_id,
        "processing"
    )


# ============================================================
# Mark Order Packed
# ============================================================

def pack_order(order_id):
    return update_order_status(
        order_id,
        "packed"
    )


# ============================================================
# Ship Order
# ============================================================

def ship_order(
    order_id,
    courier_name=None,
    tracking_number=None,
    tracking_url=None,
    estimated_delivery_date=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT order_id
            FROM orders
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (order_id,)
        )

        if not cursor.fetchone():

            return {
                "success": False,
                "message": "Order not found"
            }

        now = _current_time()

        cursor.execute(
            """
            UPDATE orders
            SET order_status = 'shipped',
                fulfillment_status = 'fulfilled',
                courier_name = ?,
                tracking_number = ?,
                tracking_url = ?,
                estimated_delivery_date = ?,
                shipped_at = ?,
                updated_at = ?
            WHERE order_id = ?
            """,
            (
                courier_name,
                tracking_number,
                tracking_url,
                estimated_delivery_date,
                now,
                now,
                order_id
            )
        )

        cursor.execute(
            """
            UPDATE order_items
            SET item_status = 'shipped',
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (
                now,
                order_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Order shipped successfully"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to ship order",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Mark Order Delivered
# ============================================================

def deliver_order(order_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT order_id
            FROM orders
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (order_id,)
        )

        if not cursor.fetchone():

            return {
                "success": False,
                "message": "Order not found"
            }

        now = _current_time()

        cursor.execute(
            """
            UPDATE orders
            SET order_status = 'delivered',
                fulfillment_status = 'fulfilled',
                delivered_at = ?,
                updated_at = ?
            WHERE order_id = ?
            """,
            (
                now,
                now,
                order_id
            )
        )

        cursor.execute(
            """
            UPDATE order_items
            SET item_status = 'delivered',
                delivered_at = ?,
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (
                now,
                now,
                order_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Order delivered successfully"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to deliver order",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Cancel Order
# ============================================================

def cancel_order(
    order_id,
    user_id=None,
    reason=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            SELECT *
            FROM orders
            WHERE order_id = ?
            AND deleted_at IS NULL
        """

        params = [order_id]

        if user_id:

            query += """
                AND user_id = ?
            """

            params.append(user_id)

        cursor.execute(
            query,
            params
        )

        order = cursor.fetchone()

        if not order:

            return {
                "success": False,
                "message": "Order not found"
            }

        non_cancelable_statuses = (
            "shipped",
            "out_for_delivery",
            "delivered",
            "cancelled",
            "returned",
            "refunded"
        )

        if order["order_status"] in non_cancelable_statuses:

            return {
                "success": False,
                "message": (
                    "Order cannot be cancelled "
                    f"after {order['order_status']}"
                )
            }

        now = _current_time()

        # ----------------------------------------------------
        # Restore Variant Stock
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                variant_id,
                product_id,
                quantity
            FROM order_items
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (order_id,)
        )

        items = cursor.fetchall()

        for item in items:

            if item["variant_id"]:

                cursor.execute(
                    """
                    UPDATE product_variants
                    SET stock_quantity =
                            stock_quantity + ?,
                        sold_quantity =
                            CASE
                                WHEN sold_quantity >= ?
                                THEN sold_quantity - ?
                                ELSE 0
                            END,
                        updated_at = ?
                    WHERE variant_id = ?
                    AND product_id = ?
                    """,
                    (
                        item["quantity"],
                        item["quantity"],
                        item["quantity"],
                        now,
                        item["variant_id"],
                        item["product_id"]
                    )
                )

        # ----------------------------------------------------
        # Cancel Order
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE orders
            SET order_status = 'cancelled',
                fulfillment_status = 'cancelled',
                cancelled_at = ?,
                cancellation_reason = ?,
                updated_at = ?
            WHERE order_id = ?
            """,
            (
                now,
                reason,
                now,
                order_id
            )
        )

        cursor.execute(
            """
            UPDATE order_items
            SET item_status = 'cancelled',
                cancelled_at = ?,
                cancellation_reason = ?,
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (
                now,
                reason,
                now,
                order_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Order cancelled successfully"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to cancel order",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Request Order Return
# ============================================================

def request_return(
    order_id,
    user_id,
    reason=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM orders
            WHERE order_id = ?
            AND user_id = ?
            AND deleted_at IS NULL
            """,
            (
                order_id,
                user_id
            )
        )

        order = cursor.fetchone()

        if not order:

            return {
                "success": False,
                "message": "Order not found"
            }

        if order["order_status"] != "delivered":

            return {
                "success": False,
                "message": (
                    "Return can only be requested "
                    "for delivered orders"
                )
            }

        now = _current_time()

        cursor.execute(
            """
            UPDATE orders
            SET return_requested_at = ?,
                return_reason = ?,
                updated_at = ?
            WHERE order_id = ?
            """,
            (
                now,
                reason,
                now,
                order_id
            )
        )

        cursor.execute(
            """
            UPDATE order_items
            SET item_status = 'return_requested',
                return_requested_at = ?,
                return_reason = ?,
                updated_at = ?
            WHERE order_id = ?
            AND item_status = 'delivered'
            AND deleted_at IS NULL
            """,
            (
                now,
                reason,
                now,
                order_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Return request submitted successfully"
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": "Failed to request return",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Refund Amount
# ============================================================

def update_refund_amount(
    order_id,
    refund_amount
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        if refund_amount < 0:

            return {
                "success": False,
                "message": "Refund amount cannot be negative"
            }

        cursor.execute(
            """
            SELECT total_amount
            FROM orders
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (order_id,)
        )

        order = cursor.fetchone()

        if not order:

            return {
                "success": False,
                "message": "Order not found"
            }

        if refund_amount > order["total_amount"]:

            return {
                "success": False,
                "message": (
                    "Refund amount cannot exceed "
                    "order total"
                )
            }

        now = _current_time()

        cursor.execute(
            """
            UPDATE orders
            SET refund_amount = ?,
                refunded_at = ?,
                updated_at = ?
            WHERE order_id = ?
            """,
            (
                refund_amount,
                now,
                now,
                order_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Refund amount updated successfully"
        }

    finally:
        connection.close()


# ============================================================
# Add Tracking Information
# ============================================================

def update_tracking(
    order_id,
    courier_name=None,
    tracking_number=None,
    tracking_url=None,
    estimated_delivery_date=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE orders
            SET courier_name = ?,
                tracking_number = ?,
                tracking_url = ?,
                estimated_delivery_date = ?,
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (
                courier_name,
                tracking_number,
                tracking_url,
                estimated_delivery_date,
                _current_time(),
                order_id
            )
        )

        if cursor.rowcount == 0:

            return {
                "success": False,
                "message": "Order not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Tracking information updated"
        }

    finally:
        connection.close()


# ============================================================
# Soft Delete Order
# ============================================================

def delete_order(order_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        now = _current_time()

        cursor.execute(
            """
            UPDATE orders
            SET deleted_at = ?,
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
            """,
            (
                now,
                now,
                order_id
            )
        )

        if cursor.rowcount == 0:

            return {
                "success": False,
                "message": "Order not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Order deleted successfully"
        }

    finally:
        connection.close()
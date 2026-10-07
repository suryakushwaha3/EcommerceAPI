def create_order_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id TEXT NOT NULL UNIQUE,

            order_number TEXT NOT NULL UNIQUE,

            user_id TEXT NOT NULL,

            subtotal REAL NOT NULL DEFAULT 0,

            discount_amount REAL NOT NULL DEFAULT 0,

            coupon_discount REAL NOT NULL DEFAULT 0,

            tax_amount REAL NOT NULL DEFAULT 0,

            shipping_charge REAL NOT NULL DEFAULT 0,

            platform_fee REAL NOT NULL DEFAULT 0,

            total_amount REAL NOT NULL DEFAULT 0,

            currency TEXT NOT NULL DEFAULT 'INR',

            coupon_id TEXT,

            offer_id TEXT,

            payment_method TEXT NOT NULL DEFAULT 'cod'
                CHECK (
                    payment_method IN (
                        'cod',
                        'upi',
                        'card',
                        'net_banking',
                        'wallet',
                        'emi',
                        'other'
                    )
                ),

            payment_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (
                    payment_status IN (
                        'pending',
                        'processing',
                        'paid',
                        'failed',
                        'cancelled',
                        'refunded',
                        'partially_refunded'
                    )
                ),

            order_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (
                    order_status IN (
                        'pending',
                        'confirmed',
                        'processing',
                        'packed',
                        'shipped',
                        'out_for_delivery',
                        'delivered',
                        'cancelled',
                        'returned',
                        'partially_returned',
                        'refunded',
                        'failed'
                    )
                ),

            fulfillment_status TEXT NOT NULL DEFAULT 'unfulfilled'
                CHECK (
                    fulfillment_status IN (
                        'unfulfilled',
                        'partially_fulfilled',
                        'fulfilled',
                        'cancelled'
                    )
                ),

            shipping_name TEXT NOT NULL,

            shipping_phone TEXT NOT NULL,

            shipping_email TEXT,

            shipping_address_line1 TEXT NOT NULL,

            shipping_address_line2 TEXT,

            shipping_city TEXT NOT NULL,

            shipping_state TEXT NOT NULL,

            shipping_country TEXT NOT NULL DEFAULT 'India',

            shipping_pincode TEXT NOT NULL,

            billing_name TEXT,

            billing_phone TEXT,

            billing_address_line1 TEXT,

            billing_address_line2 TEXT,

            billing_city TEXT,

            billing_state TEXT,

            billing_country TEXT,

            billing_pincode TEXT,

            same_as_shipping INTEGER NOT NULL DEFAULT 1,

            courier_name TEXT,

            tracking_number TEXT,

            tracking_url TEXT,

            estimated_delivery_date TEXT,

            shipped_at TEXT,

            delivered_at TEXT,

            cancelled_at TEXT,

            cancellation_reason TEXT,

            return_requested_at TEXT,

            return_reason TEXT,

            refund_amount REAL NOT NULL DEFAULT 0,

            refunded_at TEXT,

            customer_note TEXT,

            internal_note TEXT,

            ip_address TEXT,

            user_agent TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            deleted_at TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_order_id
        ON orders(order_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_order_number
        ON orders(order_number)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_user_id
        ON orders(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_coupon_id
        ON orders(coupon_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_offer_id
        ON orders(offer_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_payment_status
        ON orders(payment_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_order_status
        ON orders(order_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_fulfillment_status
        ON orders(fulfillment_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_payment_method
        ON orders(payment_method)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_tracking_number
        ON orders(tracking_number)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_delivery_date
        ON orders(estimated_delivery_date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_created_at
        ON orders(created_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_updated_at
        ON orders(updated_at)
    """)

    connection.commit()


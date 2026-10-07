def create_order_item_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_item_id TEXT NOT NULL UNIQUE,

            order_id TEXT NOT NULL,

            product_id TEXT NOT NULL,

            variant_id TEXT,

            seller_id TEXT,

            product_name TEXT NOT NULL,

            variant_name TEXT,

            sku TEXT,

            barcode TEXT,

            product_image TEXT,

            quantity INTEGER NOT NULL DEFAULT 1
                CHECK (quantity > 0),

            unit_mrp REAL NOT NULL DEFAULT 0,

            unit_price REAL NOT NULL DEFAULT 0,

            discount_amount REAL NOT NULL DEFAULT 0,

            tax_percentage REAL NOT NULL DEFAULT 0,

            tax_amount REAL NOT NULL DEFAULT 0,

            shipping_charge REAL NOT NULL DEFAULT 0,

            total_amount REAL NOT NULL DEFAULT 0,

            currency TEXT NOT NULL DEFAULT 'INR',

            item_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (
                    item_status IN (
                        'pending',
                        'confirmed',
                        'processing',
                        'packed',
                        'shipped',
                        'out_for_delivery',
                        'delivered',
                        'cancelled',
                        'return_requested',
                        'returned',
                        'refunded',
                        'partially_refunded'
                    )
                ),

            return_allowed INTEGER NOT NULL DEFAULT 1,

            return_deadline TEXT,

            return_requested_at TEXT,

            return_reason TEXT,

            cancellation_reason TEXT,

            cancelled_at TEXT,

            refund_amount REAL NOT NULL DEFAULT 0,

            refunded_at TEXT,

            delivered_at TEXT,

            customer_note TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            deleted_at TEXT,

            FOREIGN KEY (order_id)
                REFERENCES orders(order_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_order_item_id
        ON order_items(order_item_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_order_id
        ON order_items(order_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_product_id
        ON order_items(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_variant_id
        ON order_items(variant_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_seller_id
        ON order_items(seller_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_sku
        ON order_items(sku)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_status
        ON order_items(item_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_return_deadline
        ON order_items(return_deadline)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_created_at
        ON order_items(created_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_updated_at
        ON order_items(updated_at)
    """)

    connection.commit()


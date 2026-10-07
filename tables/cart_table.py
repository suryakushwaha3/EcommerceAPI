def create_cart_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            cart_id TEXT NOT NULL UNIQUE,

            user_id TEXT NOT NULL,

            product_id TEXT NOT NULL,

            variant_id TEXT,

            quantity INTEGER NOT NULL DEFAULT 1
                CHECK (quantity > 0),

            unit_price REAL NOT NULL DEFAULT 0,

            mrp REAL NOT NULL DEFAULT 0,

            discount_amount REAL NOT NULL DEFAULT 0,

            tax_amount REAL NOT NULL DEFAULT 0,

            total_amount REAL NOT NULL DEFAULT 0,

            currency TEXT NOT NULL DEFAULT 'INR',

            is_selected INTEGER NOT NULL DEFAULT 1,

            stock_status TEXT NOT NULL DEFAULT 'available'
                CHECK (
                    stock_status IN (
                        'available',
                        'low_stock',
                        'out_of_stock',
                        'unavailable'
                    )
                ),

            price_changed INTEGER NOT NULL DEFAULT 0,

            stock_checked_at TEXT,

            expires_at TEXT,

            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    status IN (
                        'active',
                        'saved_for_later',
                        'expired',
                        'removed'
                    )
                ),

            added_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            removed_at TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_carts_cart_id
        ON carts(cart_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_carts_user_id
        ON carts(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_carts_product_id
        ON carts(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_carts_variant_id
        ON carts(variant_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_carts_status
        ON carts(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_carts_is_selected
        ON carts(is_selected)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_carts_stock_status
        ON carts(stock_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_carts_added_at
        ON carts(added_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_carts_updated_at
        ON carts(updated_at)
    """)

    connection.commit()


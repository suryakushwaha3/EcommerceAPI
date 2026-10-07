def create_wishlist_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            wishlist_id TEXT NOT NULL UNIQUE,

            user_id TEXT NOT NULL,

            product_id TEXT NOT NULL,

            variant_id TEXT,

            added_price REAL NOT NULL DEFAULT 0,

            current_price REAL NOT NULL DEFAULT 0,

            price_changed INTEGER NOT NULL DEFAULT 0,

            notify_on_price_drop INTEGER NOT NULL DEFAULT 0,

            notify_on_stock_available INTEGER NOT NULL DEFAULT 1,

            priority INTEGER NOT NULL DEFAULT 0,

            notes TEXT,

            source TEXT DEFAULT 'product_page'
                CHECK (
                    source IN (
                        'product_page',
                        'search',
                        'category',
                        'recommendation',
                        'cart',
                        'other'
                    )
                ),

            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    status IN (
                        'active',
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
        CREATE INDEX IF NOT EXISTS idx_wishlists_wishlist_id
        ON wishlists(wishlist_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_user_id
        ON wishlists(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_product_id
        ON wishlists(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_variant_id
        ON wishlists(variant_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_status
        ON wishlists(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_priority
        ON wishlists(priority)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_price_changed
        ON wishlists(price_changed)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_price_notification
        ON wishlists(notify_on_price_drop)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_stock_notification
        ON wishlists(notify_on_stock_available)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_added_at
        ON wishlists(added_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wishlists_updated_at
        ON wishlists(updated_at)
    """)

    connection.commit()


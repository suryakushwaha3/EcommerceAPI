def create_offer_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            offer_id TEXT NOT NULL UNIQUE,

            offer_name TEXT NOT NULL,

            offer_code TEXT UNIQUE,

            description TEXT,

            offer_type TEXT NOT NULL DEFAULT 'percentage'
                CHECK (
                    offer_type IN (
                        'percentage',
                        'flat',
                        'buy_one_get_one',
                        'buy_x_get_y',
                        'free_shipping',
                        'cashback'
                    )
                ),

            discount_value REAL NOT NULL DEFAULT 0,

            maximum_discount REAL,

            minimum_order_amount REAL NOT NULL DEFAULT 0,

            maximum_order_amount REAL,

            minimum_quantity INTEGER NOT NULL DEFAULT 1,

            maximum_quantity INTEGER,

            applicable_to TEXT NOT NULL DEFAULT 'all'
                CHECK (
                    applicable_to IN (
                        'all',
                        'product',
                        'category',
                        'variant',
                        'user',
                        'new_user'
                    )
                ),

            target_id TEXT,

            user_id TEXT,

            usage_limit INTEGER,

            usage_per_user INTEGER NOT NULL DEFAULT 1,

            used_count INTEGER NOT NULL DEFAULT 0,

            start_at TEXT NOT NULL,

            end_at TEXT NOT NULL,

            priority INTEGER NOT NULL DEFAULT 0,

            is_stackable INTEGER NOT NULL DEFAULT 0,

            is_featured INTEGER NOT NULL DEFAULT 0,

            is_active INTEGER NOT NULL DEFAULT 1,

            status TEXT NOT NULL DEFAULT 'scheduled'
                CHECK (
                    status IN (
                        'draft',
                        'scheduled',
                        'active',
                        'paused',
                        'expired',
                        'exhausted',
                        'blocked',
                        'deleted'
                    )
                ),

            created_by TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            deleted_at TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_offer_id
        ON offers(offer_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_offer_code
        ON offers(offer_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_type
        ON offers(offer_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_applicable_to
        ON offers(applicable_to)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_target_id
        ON offers(target_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_user_id
        ON offers(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_start_at
        ON offers(start_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_end_at
        ON offers(end_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_priority
        ON offers(priority)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_featured
        ON offers(is_featured)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_active
        ON offers(is_active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_status
        ON offers(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offers_created_at
        ON offers(created_at)
    """)

    connection.commit()


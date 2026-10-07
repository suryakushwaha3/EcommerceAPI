def create_coupon_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            coupon_id TEXT NOT NULL UNIQUE,

            coupon_code TEXT NOT NULL UNIQUE,

            coupon_name TEXT NOT NULL,

            description TEXT,

            discount_type TEXT NOT NULL DEFAULT 'percentage'
                CHECK (
                    discount_type IN (
                        'percentage',
                        'flat',
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

            is_first_order_only INTEGER NOT NULL DEFAULT 0,

            is_stackable INTEGER NOT NULL DEFAULT 0,

            is_active INTEGER NOT NULL DEFAULT 1,

            priority INTEGER NOT NULL DEFAULT 0,

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
        CREATE INDEX IF NOT EXISTS idx_coupons_coupon_id
        ON coupons(coupon_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_code
        ON coupons(coupon_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_discount_type
        ON coupons(discount_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_applicable_to
        ON coupons(applicable_to)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_target_id
        ON coupons(target_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_user_id
        ON coupons(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_start_at
        ON coupons(start_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_end_at
        ON coupons(end_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_priority
        ON coupons(priority)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_first_order
        ON coupons(is_first_order_only)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_active
        ON coupons(is_active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_status
        ON coupons(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_created_at
        ON coupons(created_at)
    """)

    connection.commit()


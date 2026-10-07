def create_banner_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            banner_id TEXT NOT NULL UNIQUE,

            banner_name TEXT NOT NULL,

            title TEXT,

            subtitle TEXT,

            description TEXT,

            image_url TEXT NOT NULL,

            mobile_image_url TEXT,

            desktop_image_url TEXT,

            banner_type TEXT NOT NULL DEFAULT 'promotional'
                CHECK (
                    banner_type IN (
                        'promotional',
                        'category',
                        'product',
                        'offer',
                        'seasonal',
                        'festival',
                        'announcement'
                    )
                ),

            placement TEXT NOT NULL DEFAULT 'home'
                CHECK (
                    placement IN (
                        'home',
                        'category',
                        'product',
                        'search',
                        'cart',
                        'checkout'
                    )
                ),

            target_type TEXT DEFAULT 'none'
                CHECK (
                    target_type IN (
                        'none',
                        'product',
                        'category',
                        'offer',
                        'external_url'
                    )
                ),

            target_id TEXT,

            redirect_url TEXT,

            button_text TEXT,

            display_order INTEGER NOT NULL DEFAULT 0,

            is_featured INTEGER NOT NULL DEFAULT 0,

            is_active INTEGER NOT NULL DEFAULT 1,

            start_at TEXT,

            end_at TEXT,

            click_count INTEGER NOT NULL DEFAULT 0,

            view_count INTEGER NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    status IN (
                        'active',
                        'inactive',
                        'scheduled',
                        'expired',
                        'draft',
                        'blocked',
                        'deleted'
                    )
                ),

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            deleted_at TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_banner_id
        ON banners(banner_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_name
        ON banners(banner_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_type
        ON banners(banner_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_placement
        ON banners(placement)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_target_type
        ON banners(target_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_target_id
        ON banners(target_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_display_order
        ON banners(display_order)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_featured
        ON banners(is_featured)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_active
        ON banners(is_active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_status
        ON banners(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_start_at
        ON banners(start_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_end_at
        ON banners(end_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_banners_created_at
        ON banners(created_at)
    """)

    connection.commit()


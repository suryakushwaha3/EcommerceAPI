def create_category_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            category_id TEXT NOT NULL UNIQUE,

            parent_category_id TEXT,

            category_name TEXT NOT NULL,

            slug TEXT NOT NULL UNIQUE,

            description TEXT,

            category_image TEXT,

            banner_image TEXT,

            icon TEXT,

            meta_title TEXT,

            meta_description TEXT,

            meta_keywords TEXT,

            display_order INTEGER NOT NULL DEFAULT 0,

            level INTEGER NOT NULL DEFAULT 0,

            is_featured INTEGER NOT NULL DEFAULT 0,

            is_active INTEGER NOT NULL DEFAULT 1,

            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    status IN (
                        'active',
                        'inactive',
                        'draft',
                        'blocked',
                        'deleted'
                    )
                ),

            product_count INTEGER NOT NULL DEFAULT 0,

            view_count INTEGER NOT NULL DEFAULT 0,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            deleted_at TEXT,

            FOREIGN KEY (parent_category_id)
                REFERENCES categories(category_id)
                ON DELETE SET NULL
                ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_category_id
        ON categories(category_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_parent_id
        ON categories(parent_category_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_name
        ON categories(category_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_slug
        ON categories(slug)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_level
        ON categories(level)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_display_order
        ON categories(display_order)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_featured
        ON categories(is_featured)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_active
        ON categories(is_active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_status
        ON categories(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_categories_created_at
        ON categories(created_at)
    """)

    connection.commit()


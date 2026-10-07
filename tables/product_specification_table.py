def create_product_specification_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_specifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            specification_id TEXT NOT NULL UNIQUE,

            product_id TEXT NOT NULL,

            variant_id TEXT,

            specification_group TEXT,

            specification_name TEXT NOT NULL,

            specification_value TEXT NOT NULL,

            specification_unit TEXT,

            display_order INTEGER NOT NULL DEFAULT 0,

            is_highlighted INTEGER NOT NULL DEFAULT 0,

            is_searchable INTEGER NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    status IN (
                        'active',
                        'inactive',
                        'deleted'
                    )
                ),

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            deleted_at TEXT,

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_specifications_id
        ON product_specifications(specification_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_specifications_product_id
        ON product_specifications(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_specifications_variant_id
        ON product_specifications(variant_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_specifications_group
        ON product_specifications(specification_group)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_specifications_name
        ON product_specifications(specification_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_specifications_searchable
        ON product_specifications(is_searchable)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_specifications_highlighted
        ON product_specifications(is_highlighted)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_specifications_status
        ON product_specifications(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_specifications_display_order
        ON product_specifications(display_order)
    """)

    connection.commit()


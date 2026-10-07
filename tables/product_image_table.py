def create_product_image_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            image_id TEXT NOT NULL UNIQUE,

            product_id TEXT NOT NULL,

            image_url TEXT NOT NULL,

            image_type TEXT NOT NULL DEFAULT 'product'
                CHECK (
                    image_type IN (
                        'product',
                        'thumbnail',
                        'front',
                        'back',
                        'side',
                        'top',
                        'bottom',
                        'detail',
                        'packaging',
                        'lifestyle',
                        'banner'
                    )
                ),

            alt_text TEXT,

            title TEXT,

            is_primary INTEGER NOT NULL DEFAULT 0,

            is_thumbnail INTEGER NOT NULL DEFAULT 0,

            sort_order INTEGER NOT NULL DEFAULT 0,

            width INTEGER,

            height INTEGER,

            file_size INTEGER,

            mime_type TEXT,

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

    # ---------------------------------------------------------
    # Indexes
    # ---------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_images_image_id
        ON product_images(image_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_images_product_id
        ON product_images(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_images_type
        ON product_images(image_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_images_primary
        ON product_images(is_primary)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_images_thumbnail
        ON product_images(is_thumbnail)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_images_sort_order
        ON product_images(sort_order)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_images_status
        ON product_images(status)
    """)

    connection.commit()


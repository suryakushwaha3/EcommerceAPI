def create_review_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            review_id TEXT NOT NULL UNIQUE,

            product_id TEXT NOT NULL,

            variant_id TEXT,

            user_id TEXT NOT NULL,

            order_id TEXT,

            order_item_id TEXT,

            rating REAL NOT NULL
                CHECK (
                    rating >= 1
                    AND rating <= 5
                ),

            review_title TEXT,

            review_text TEXT,

            review_type TEXT NOT NULL DEFAULT 'text'
                CHECK (
                    review_type IN (
                        'text',
                        'image',
                        'video',
                        'text_image',
                        'text_video',
                        'text_image_video'
                    )
                ),

            is_verified_purchase INTEGER NOT NULL DEFAULT 0,

            is_anonymous INTEGER NOT NULL DEFAULT 0,

            is_featured INTEGER NOT NULL DEFAULT 0,

            is_recommended INTEGER NOT NULL DEFAULT 1,

            helpful_count INTEGER NOT NULL DEFAULT 0,

            not_helpful_count INTEGER NOT NULL DEFAULT 0,

            report_count INTEGER NOT NULL DEFAULT 0,

            seller_response TEXT,

            seller_response_at TEXT,

            seller_response_by TEXT,

            moderation_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (
                    moderation_status IN (
                        'pending',
                        'approved',
                        'rejected',
                        'flagged',
                        'hidden'
                    )
                ),

            moderation_reason TEXT,

            moderated_by TEXT,

            moderated_at TEXT,

            edit_count INTEGER NOT NULL DEFAULT 0,

            last_edited_at TEXT,

            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    status IN (
                        'active',
                        'inactive',
                        'deleted'
                    )
                ),

            ip_address TEXT,

            user_agent TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            deleted_at TEXT,

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,

            FOREIGN KEY (order_id)
                REFERENCES orders(order_id)
                ON DELETE SET NULL
                ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_review_id
        ON reviews(review_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_product_id
        ON reviews(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_variant_id
        ON reviews(variant_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_user_id
        ON reviews(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_order_id
        ON reviews(order_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_order_item_id
        ON reviews(order_item_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_rating
        ON reviews(rating)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_verified_purchase
        ON reviews(is_verified_purchase)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_featured
        ON reviews(is_featured)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_moderation_status
        ON reviews(moderation_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_status
        ON reviews(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_created_at
        ON reviews(created_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_updated_at
        ON reviews(updated_at)
    """)

    connection.commit()


def create_rating_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            rating_id TEXT NOT NULL UNIQUE,

            product_id TEXT NOT NULL,

            variant_id TEXT,

            total_ratings INTEGER NOT NULL DEFAULT 0,

            average_rating REAL NOT NULL DEFAULT 0,

            five_star_count INTEGER NOT NULL DEFAULT 0,

            four_star_count INTEGER NOT NULL DEFAULT 0,

            three_star_count INTEGER NOT NULL DEFAULT 0,

            two_star_count INTEGER NOT NULL DEFAULT 0,

            one_star_count INTEGER NOT NULL DEFAULT 0,

            verified_rating_count INTEGER NOT NULL DEFAULT 0,

            unverified_rating_count INTEGER NOT NULL DEFAULT 0,

            rating_5_percentage REAL NOT NULL DEFAULT 0,

            rating_4_percentage REAL NOT NULL DEFAULT 0,

            rating_3_percentage REAL NOT NULL DEFAULT 0,

            rating_2_percentage REAL NOT NULL DEFAULT 0,

            rating_1_percentage REAL NOT NULL DEFAULT 0,

            last_rating_at TEXT,

            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    status IN (
                        'active',
                        'inactive'
                    )
                ),

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ratings_rating_id
        ON ratings(rating_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ratings_product_id
        ON ratings(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ratings_variant_id
        ON ratings(variant_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ratings_average_rating
        ON ratings(average_rating)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ratings_total_ratings
        ON ratings(total_ratings)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ratings_verified_count
        ON ratings(verified_rating_count)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ratings_status
        ON ratings(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ratings_updated_at
        ON ratings(updated_at)
    """)

    connection.commit()


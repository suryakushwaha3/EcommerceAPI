def create_product_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id TEXT NOT NULL UNIQUE,

            product_name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,

            brand_id TEXT,
            category_id TEXT,
            subcategory_id TEXT,

            short_description TEXT,
            description TEXT,

            sku TEXT NOT NULL UNIQUE,
            barcode TEXT UNIQUE,

            product_type TEXT NOT NULL DEFAULT 'physical',

            mrp REAL NOT NULL DEFAULT 0,
            selling_price REAL NOT NULL DEFAULT 0,

            discount_type TEXT DEFAULT 'percentage'
                CHECK (
                    discount_type IN (
                        'percentage',
                        'flat',
                        'none'
                    )
                ),

            discount_value REAL NOT NULL DEFAULT 0,

            tax_percentage REAL NOT NULL DEFAULT 0,

            currency TEXT NOT NULL DEFAULT 'INR',

            stock_status TEXT NOT NULL DEFAULT 'in_stock'
                CHECK (
                    stock_status IN (
                        'in_stock',
                        'out_of_stock',
                        'low_stock',
                        'pre_order',
                        'coming_soon',
                        'discontinued'
                    )
                ),

            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    status IN (
                        'active',
                        'inactive',
                        'draft',
                        'pending',
                        'blocked',
                        'deleted'
                    )
                ),

            is_featured INTEGER NOT NULL DEFAULT 0,
            is_bestseller INTEGER NOT NULL DEFAULT 0,
            is_trending INTEGER NOT NULL DEFAULT 0,
            is_new_arrival INTEGER NOT NULL DEFAULT 0,

            is_returnable INTEGER NOT NULL DEFAULT 1,
            is_exchangeable INTEGER NOT NULL DEFAULT 1,

            return_days INTEGER NOT NULL DEFAULT 7,

            rating REAL NOT NULL DEFAULT 0,
            rating_count INTEGER NOT NULL DEFAULT 0,
            review_count INTEGER NOT NULL DEFAULT 0,

            view_count INTEGER NOT NULL DEFAULT 0,
            wishlist_count INTEGER NOT NULL DEFAULT 0,
            cart_count INTEGER NOT NULL DEFAULT 0,
            purchase_count INTEGER NOT NULL DEFAULT 0,

            seller_id TEXT,

            meta_title TEXT,
            meta_description TEXT,
            meta_keywords TEXT,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            deleted_at TEXT
        )
    """)

    # ---------------------------------------------------------
    # Indexes
    # ---------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_product_id
        ON products(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_product_name
        ON products(product_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_sku
        ON products(sku)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_barcode
        ON products(barcode)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_brand
        ON products(brand_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_category
        ON products(category_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_subcategory
        ON products(subcategory_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_seller
        ON products(seller_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_status
        ON products(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_stock_status
        ON products(stock_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_price
        ON products(selling_price)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_rating
        ON products(rating)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_featured
        ON products(is_featured)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_bestseller
        ON products(is_bestseller)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_trending
        ON products(is_trending)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_new_arrival
        ON products(is_new_arrival)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_created_at
        ON products(created_at)
    """)

    connection.commit()


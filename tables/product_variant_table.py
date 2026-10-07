def create_product_variant_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            variant_id TEXT NOT NULL UNIQUE,

            product_id TEXT NOT NULL,

            variant_name TEXT NOT NULL,

            variant_code TEXT UNIQUE,

            sku TEXT NOT NULL UNIQUE,

            barcode TEXT UNIQUE,

            attributes TEXT,

            mrp REAL NOT NULL DEFAULT 0,

            selling_price REAL NOT NULL DEFAULT 0,

            discount_type TEXT NOT NULL DEFAULT 'percentage'
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

            stock_quantity INTEGER NOT NULL DEFAULT 0,

            low_stock_threshold INTEGER NOT NULL DEFAULT 5,

            stock_status TEXT NOT NULL DEFAULT 'in_stock'
                CHECK (
                    stock_status IN (
                        'in_stock',
                        'out_of_stock',
                        'low_stock',
                        'pre_order',
                        'discontinued'
                    )
                ),

            reserved_quantity INTEGER NOT NULL DEFAULT 0,

            sold_quantity INTEGER NOT NULL DEFAULT 0,

            weight REAL,

            weight_unit TEXT DEFAULT 'kg',

            length REAL,

            width REAL,

            height REAL,

            dimension_unit TEXT DEFAULT 'cm',

            is_default INTEGER NOT NULL DEFAULT 0,

            is_active INTEGER NOT NULL DEFAULT 1,

            sort_order INTEGER NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    status IN (
                        'active',
                        'inactive',
                        'blocked',
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
        CREATE INDEX IF NOT EXISTS idx_product_variants_variant_id
        ON product_variants(variant_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_product_id
        ON product_variants(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_variant_code
        ON product_variants(variant_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_sku
        ON product_variants(sku)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_barcode
        ON product_variants(barcode)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_stock_status
        ON product_variants(stock_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_status
        ON product_variants(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_is_default
        ON product_variants(is_default)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_is_active
        ON product_variants(is_active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_price
        ON product_variants(selling_price)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_variants_sort_order
        ON product_variants(sort_order)
    """)

    connection.commit()


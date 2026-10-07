# tables/product_highlight_table.py

import sqlite3


def create_product_highlight_table(connection):
    """
    Create product_highlights table.
    """

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_highlights (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            highlight_id TEXT NOT NULL UNIQUE,

            product_id TEXT NOT NULL,

            variant_id TEXT,

            highlight_text TEXT NOT NULL,

            highlight_type TEXT DEFAULT 'general',

            display_order INTEGER DEFAULT 0,

            is_featured INTEGER DEFAULT 0,

            is_active INTEGER DEFAULT 1,

            status TEXT DEFAULT 'active',

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            deleted_at TEXT,

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
                ON DELETE CASCADE,

            FOREIGN KEY (variant_id)
                REFERENCES product_variants(variant_id)
                ON DELETE SET NULL
        )
    """)

    # -----------------------------------------------------
    # Indexes
    # -----------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_product_highlights_product_id
        ON product_highlights(product_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_product_highlights_variant_id
        ON product_highlights(variant_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_product_highlights_status
        ON product_highlights(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_product_highlights_active
        ON product_highlights(is_active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_product_highlights_order
        ON product_highlights(display_order)
    """)

    connection.commit()

 # database/database.py

import sqlite3
from pathlib import Path


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "shopping.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    """
    Create and return a SQLite database connection.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
        check_same_thread=False
    )

    # Dictionary-like row access
    connection.row_factory = sqlite3.Row

    # Enable foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON")

    # Better concurrent read/write support
    connection.execute("PRAGMA journal_mode = WAL")

    # Wait for locked database
    connection.execute("PRAGMA busy_timeout = 30000")

    return connection


# Alias for compatibility
def get_connection():
    """
    Alias of get_db_connection().
    """

    return get_db_connection()


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def initialize_database():
    """
    Create all database tables.
    """

    from tables.user_table import create_user_table
    from tables.product_table import create_product_table
    from tables.product_image_table import create_product_image_table
    from tables.product_variant_table import create_product_variant_table
    from tables.product_specification_table import create_product_specification_table
    from tables.product_highlight_table import create_product_highlight_table
    from tables.category_table import create_category_table
    from tables.banner_table import create_banner_table
    from tables.cart_table import create_cart_table
    from tables.wishlist_table import create_wishlist_table
    from tables.order_table import create_order_table
    from tables.order_item_table import create_order_item_table
    from tables.payment_table import create_payment_table
    from tables.review_table import create_review_table
    from tables.rating_table import create_rating_table
    from tables.offer_table import create_offer_table
    from tables.coupon_table import create_coupon_table

    connection = get_db_connection()

    try:
        # -------------------------------------------------
        # Parent Tables
        # -------------------------------------------------

        create_user_table(connection)
        create_category_table(connection)
        create_product_table(connection)

        # -------------------------------------------------
        # Product Related Tables
        # -------------------------------------------------

        create_product_image_table(connection)
        create_product_variant_table(connection)
        create_product_specification_table(connection)
        create_product_highlight_table(connection)

        # -------------------------------------------------
        # Store Related Tables
        # -------------------------------------------------

        create_banner_table(connection)
        create_cart_table(connection)
        create_wishlist_table(connection)

        # -------------------------------------------------
        # Order Related Tables
        # -------------------------------------------------

        create_order_table(connection)
        create_order_item_table(connection)

        # -------------------------------------------------
        # Payment / Review
        # -------------------------------------------------

        create_payment_table(connection)
        create_review_table(connection)
        create_rating_table(connection)

        # -------------------------------------------------
        # Offers / Coupons
        # -------------------------------------------------

        create_offer_table(connection)
        create_coupon_table(connection)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# DATABASE HEALTH CHECK
# =========================================================

def check_database_connection():
    """
    Check database connection.
    """

    connection = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT 1")

        result = cursor.fetchone()

        return result is not None

    except sqlite3.Error:
        return False

    finally:
        if connection:
            connection.close()


# =========================================================
# EXECUTE QUERY
# =========================================================

def execute_query(
    query,
    params=(),
    fetchone=False,
    fetchall=False
):
    """
    Execute a SQL query.

    Example:

        execute_query(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
            fetchone=True
        )
    """

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(query, params)

        if fetchone:
            return cursor.fetchone()

        if fetchall:
            return cursor.fetchall()

        connection.commit()

        return cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# EXECUTE MANY
# =========================================================

def execute_many(query, data):
    """
    Execute one query for multiple records.
    """

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.executemany(query, data)

        connection.commit()

        return cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# EXECUTE TRANSACTION
# =========================================================

def execute_transaction(queries):
    """
    Execute multiple queries in one transaction.

    Format:

        [
            (
                "INSERT INTO users (...) VALUES (?)",
                (value,)
            ),
            (
                "UPDATE users SET name = ? WHERE id = ?",
                (name, user_id)
            )
        ]
    """

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        for query, params in queries:
            cursor.execute(query, params)

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# EXECUTE INSERT
# =========================================================

def execute_insert(query, params=()):
    """
    Execute INSERT query and return last inserted ID.
    """

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(query, params)

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# CLOSE CONNECTION
# =========================================================

def close_connection(connection):
    """
    Safely close database connection.
    """

    if connection:
        connection.close()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    initialize_database()

    if check_database_connection():

        print("======================================")
        print("Database initialized successfully.")
        print(f"Database: {DATABASE_PATH}")
        print("======================================")

    else:

        print("Database connection failed.")
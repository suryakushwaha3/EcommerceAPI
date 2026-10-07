import secrets
from datetime import datetime, timezone

from database.database import get_db_connection


# ============================================================
# Helper Functions
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_category_id():
    return "CAT_" + secrets.token_hex(8).upper()


# ============================================================
# Create Category
# ============================================================

def create_category(
    category_name,
    slug=None,
    parent_category_id=None,
    description=None,
    category_image=None,
    banner_image=None,
    icon=None,
    meta_title=None,
    meta_description=None,
    meta_keywords=None,
    display_order=0,
    level=None,
    is_featured=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        category_name = category_name.strip()

        if slug:
            slug = slug.strip().lower()
        else:
            slug = category_name.lower().replace(" ", "-")

        # Check duplicate slug
        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE slug = ?
            """,
            (slug,)
        )

        if cursor.fetchone():
            return {
                "success": False,
                "message": "Category slug already exists"
            }

        # Calculate category level
        if parent_category_id:
            cursor.execute(
                """
                SELECT level
                FROM categories
                WHERE category_id = ?
                AND deleted_at IS NULL
                """,
                (parent_category_id,)
            )

            parent = cursor.fetchone()

            if not parent:
                return {
                    "success": False,
                    "message": "Parent category not found"
                }

            if level is None:
                level = parent["level"] + 1

        else:
            level = 0

        category_id = _generate_category_id()
        now = _current_time()

        cursor.execute(
            """
            INSERT INTO categories (
                category_id,
                parent_category_id,
                category_name,
                slug,
                description,
                category_image,
                banner_image,
                icon,
                meta_title,
                meta_description,
                meta_keywords,
                display_order,
                level,
                is_featured,
                is_active,
                status,
                product_count,
                view_count,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, 1, 'active', 0, 0, ?, ?
            )
            """,
            (
                category_id,
                parent_category_id,
                category_name,
                slug,
                description,
                category_image,
                banner_image,
                icon,
                meta_title,
                meta_description,
                meta_keywords,
                display_order,
                level,
                is_featured,
                now,
                now
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Category created successfully",
            "category_id": category_id
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to create category",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Category By ID
# ============================================================

def get_category_by_id(category_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM categories
            WHERE category_id = ?
            AND deleted_at IS NULL
            """,
            (category_id,)
        )

        category = cursor.fetchone()

        if not category:
            return {
                "success": False,
                "message": "Category not found"
            }

        return {
            "success": True,
            "category": dict(category)
        }

    finally:
        connection.close()


# ============================================================
# Get Category By Slug
# ============================================================

def get_category_by_slug(slug):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM categories
            WHERE slug = ?
            AND deleted_at IS NULL
            """,
            (slug.strip().lower(),)
        )

        category = cursor.fetchone()

        if not category:
            return {
                "success": False,
                "message": "Category not found"
            }

        return {
            "success": True,
            "category": dict(category)
        }

    finally:
        connection.close()


# ============================================================
# Get Categories
# ============================================================

def get_categories(
    parent_category_id=None,
    level=None,
    featured_only=False,
    active_only=True,
    limit=50,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT *
            FROM categories
            WHERE deleted_at IS NULL
        """

        params = []

        if active_only:
            query += """
                AND status = 'active'
                AND is_active = 1
            """

        if parent_category_id is None:
            query += """
                AND parent_category_id IS NULL
            """
        else:
            query += """
                AND parent_category_id = ?
            """
            params.append(parent_category_id)

        if level is not None:
            query += """
                AND level = ?
            """
            params.append(level)

        if featured_only:
            query += """
                AND is_featured = 1
            """

        query += """
            ORDER BY display_order ASC, category_name ASC
            LIMIT ? OFFSET ?
        """

        params.extend([
            limit,
            offset
        ])

        cursor.execute(query, params)

        categories = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(categories),
            "categories": categories
        }

    finally:
        connection.close()


# ============================================================
# Get Subcategories
# ============================================================

def get_subcategories(parent_category_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM categories
            WHERE parent_category_id = ?
            AND status = 'active'
            AND is_active = 1
            AND deleted_at IS NULL
            ORDER BY display_order ASC, category_name ASC
            """,
            (parent_category_id,)
        )

        categories = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(categories),
            "categories": categories
        }

    finally:
        connection.close()


# ============================================================
# Update Category
# ============================================================

def update_category(category_id, **fields):
    allowed_fields = {
        "category_name",
        "slug",
        "description",
        "category_image",
        "banner_image",
        "icon",
        "meta_title",
        "meta_description",
        "meta_keywords",
        "display_order",
        "is_featured",
        "is_active",
        "status"
    }

    update_fields = []
    values = []

    for field, value in fields.items():

        if field not in allowed_fields:
            continue

        if value is None:
            continue

        if field == "category_name":
            value = value.strip()

        if field == "slug":
            value = value.strip().lower()

        update_fields.append(f"{field} = ?")
        values.append(value)

    if not update_fields:
        return {
            "success": False,
            "message": "No valid fields to update"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE category_id = ?
            AND deleted_at IS NULL
            """,
            (category_id,)
        )

        if not cursor.fetchone():
            return {
                "success": False,
                "message": "Category not found"
            }

        if "slug" in fields:
            cursor.execute(
                """
                SELECT id
                FROM categories
                WHERE slug = ?
                AND category_id != ?
                """,
                (
                    fields["slug"],
                    category_id
                )
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Category slug already exists"
                }

        update_fields.append("updated_at = ?")
        values.append(_current_time())

        values.append(category_id)

        query = f"""
            UPDATE categories
            SET {", ".join(update_fields)}
            WHERE category_id = ?
            AND deleted_at IS NULL
        """

        cursor.execute(query, values)

        connection.commit()

        return {
            "success": True,
            "message": "Category updated successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update category",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Move Category
# ============================================================

def move_category(category_id, new_parent_category_id=None):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if category_id == new_parent_category_id:
            return {
                "success": False,
                "message": "Category cannot be its own parent"
            }

        new_level = 0

        if new_parent_category_id:

            cursor.execute(
                """
                SELECT level
                FROM categories
                WHERE category_id = ?
                AND deleted_at IS NULL
                """,
                (new_parent_category_id,)
            )

            parent = cursor.fetchone()

            if not parent:
                return {
                    "success": False,
                    "message": "New parent category not found"
                }

            new_level = parent["level"] + 1

        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE category_id = ?
            AND deleted_at IS NULL
            """,
            (category_id,)
        )

        if not cursor.fetchone():
            return {
                "success": False,
                "message": "Category not found"
            }

        cursor.execute(
            """
            UPDATE categories
            SET parent_category_id = ?,
                level = ?,
                updated_at = ?
            WHERE category_id = ?
            """,
            (
                new_parent_category_id,
                new_level,
                _current_time(),
                category_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Category moved successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to move category",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Search Categories
# ============================================================

def search_categories(
    search,
    limit=20,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        search_value = f"%{search}%"

        cursor.execute(
            """
            SELECT *
            FROM categories
            WHERE (
                category_name LIKE ?
                OR slug LIKE ?
                OR description LIKE ?
            )
            AND status = 'active'
            AND is_active = 1
            AND deleted_at IS NULL
            ORDER BY category_name ASC
            LIMIT ? OFFSET ?
            """,
            (
                search_value,
                search_value,
                search_value,
                limit,
                offset
            )
        )

        categories = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(categories),
            "categories": categories
        }

    finally:
        connection.close()


# ============================================================
# Update Category Status
# ============================================================

def update_category_status(category_id, status):
    allowed_statuses = (
        "active",
        "inactive",
        "draft",
        "blocked",
        "deleted"
    )

    if status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid category status"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = _current_time()

        deleted_at = now if status == "deleted" else None

        cursor.execute(
            """
            UPDATE categories
            SET status = ?,
                is_active = ?,
                deleted_at = ?,
                updated_at = ?
            WHERE category_id = ?
            AND deleted_at IS NULL
            """,
            (
                status,
                1 if status == "active" else 0,
                deleted_at,
                now,
                category_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Category not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": f"Category status changed to {status}"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update category status",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Delete Category
# ============================================================

def delete_category(category_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Prevent deleting category which still has children
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM categories
            WHERE parent_category_id = ?
            AND deleted_at IS NULL
            """,
            (category_id,)
        )

        child_count = cursor.fetchone()["count"]

        if child_count > 0:
            return {
                "success": False,
                "message": "Cannot delete category with subcategories"
            }

        now = _current_time()

        cursor.execute(
            """
            UPDATE categories
            SET status = 'deleted',
                is_active = 0,
                deleted_at = ?,
                updated_at = ?
            WHERE category_id = ?
            AND deleted_at IS NULL
            """,
            (
                now,
                now,
                category_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Category not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Category deleted successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to delete category",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Product Count
# ============================================================

def update_product_count(
    category_id,
    count
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE categories
            SET product_count = ?,
                updated_at = ?
            WHERE category_id = ?
            AND deleted_at IS NULL
            """,
            (
                max(0, count),
                _current_time(),
                category_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Category not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Product count updated successfully"
        }

    finally:
        connection.close()


# ============================================================
# Increment Category View
# ============================================================

def increment_category_view(category_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE categories
            SET view_count = view_count + 1,
                updated_at = ?
            WHERE category_id = ?
            AND status = 'active'
            AND deleted_at IS NULL
            """,
            (
                _current_time(),
                category_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Category view updated"
        }

    finally:
        connection.close()


# ============================================================
# Get Featured Categories
# ============================================================

def get_featured_categories(limit=20):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM categories
            WHERE is_featured = 1
            AND is_active = 1
            AND status = 'active'
            AND deleted_at IS NULL
            ORDER BY display_order ASC
            LIMIT ?
            """,
            (limit,)
        )

        categories = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(categories),
            "categories": categories
        }

    finally:
        connection.close()
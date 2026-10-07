import secrets
from datetime import datetime, timezone

from database.database import get_db_connection


# ============================================================
# Helper Functions
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_banner_id():
    return "BAN_" + secrets.token_hex(8).upper()


# ============================================================
# Create Banner
# ============================================================

def create_banner(
    banner_name,
    image_url,
    title=None,
    subtitle=None,
    description=None,
    mobile_image_url=None,
    desktop_image_url=None,
    banner_type="promotional",
    placement="home",
    target_type="none",
    target_id=None,
    redirect_url=None,
    button_text=None,
    display_order=0,
    is_featured=0,
    start_at=None,
    end_at=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if not banner_name or not banner_name.strip():
            return {
                "success": False,
                "message": "Banner name is required"
            }

        if not image_url or not image_url.strip():
            return {
                "success": False,
                "message": "Banner image URL is required"
            }

        allowed_types = (
            "promotional",
            "category",
            "product",
            "offer",
            "seasonal",
            "festival",
            "announcement"
        )

        allowed_placements = (
            "home",
            "category",
            "product",
            "search",
            "cart",
            "checkout"
        )

        allowed_target_types = (
            "none",
            "product",
            "category",
            "offer",
            "external_url"
        )

        if banner_type not in allowed_types:
            return {
                "success": False,
                "message": "Invalid banner type"
            }

        if placement not in allowed_placements:
            return {
                "success": False,
                "message": "Invalid banner placement"
            }

        if target_type not in allowed_target_types:
            return {
                "success": False,
                "message": "Invalid target type"
            }

        if start_at and end_at and start_at >= end_at:
            return {
                "success": False,
                "message": "End time must be greater than start time"
            }

        banner_id = _generate_banner_id()
        now = _current_time()

        status = "active"

        if start_at and start_at > now:
            status = "scheduled"

        if end_at and end_at <= now:
            status = "expired"

        cursor.execute(
            """
            INSERT INTO banners (
                banner_id,
                banner_name,
                title,
                subtitle,
                description,
                image_url,
                mobile_image_url,
                desktop_image_url,
                banner_type,
                placement,
                target_type,
                target_id,
                redirect_url,
                button_text,
                display_order,
                is_featured,
                is_active,
                start_at,
                end_at,
                click_count,
                view_count,
                status,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, 0,
                0, ?, ?, ?
            )
            """,
            (
                banner_id,
                banner_name.strip(),
                title,
                subtitle,
                description,
                image_url.strip(),
                mobile_image_url,
                desktop_image_url,
                banner_type,
                placement,
                target_type,
                target_id,
                redirect_url,
                button_text,
                display_order,
                is_featured,
                1 if status in ("active", "scheduled") else 0,
                start_at,
                end_at,
                status,
                now,
                now
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Banner created successfully",
            "banner_id": banner_id,
            "status": status
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to create banner",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get Banner By ID
# ============================================================

def get_banner_by_id(banner_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM banners
            WHERE banner_id = ?
            AND deleted_at IS NULL
            """,
            (banner_id,)
        )

        banner = cursor.fetchone()

        if not banner:
            return {
                "success": False,
                "message": "Banner not found"
            }

        return {
            "success": True,
            "banner": dict(banner)
        }

    finally:
        connection.close()


# ============================================================
# Get Banners
# ============================================================

def get_banners(
    placement=None,
    banner_type=None,
    status=None,
    active_only=False,
    featured_only=False,
    limit=20,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT *
            FROM banners
            WHERE deleted_at IS NULL
        """

        params = []

        if placement:
            query += """
                AND placement = ?
            """
            params.append(placement)

        if banner_type:
            query += """
                AND banner_type = ?
            """
            params.append(banner_type)

        if status:
            query += """
                AND status = ?
            """
            params.append(status)

        if active_only:
            query += """
                AND is_active = 1
                AND status = 'active'
            """

        if featured_only:
            query += """
                AND is_featured = 1
            """

        query += """
            ORDER BY display_order ASC, created_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([
            limit,
            offset
        ])

        cursor.execute(query, params)

        banners = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(banners),
            "banners": banners
        }

    finally:
        connection.close()


# ============================================================
# Get Active Banners For Placement
# ============================================================

def get_active_banners(
    placement="home",
    limit=20
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = _current_time()

        cursor.execute(
            """
            SELECT *
            FROM banners
            WHERE placement = ?
            AND is_active = 1
            AND status = 'active'
            AND deleted_at IS NULL
            AND (
                start_at IS NULL
                OR start_at <= ?
            )
            AND (
                end_at IS NULL
                OR end_at > ?
            )
            ORDER BY display_order ASC, created_at DESC
            LIMIT ?
            """,
            (
                placement,
                now,
                now,
                limit
            )
        )

        banners = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(banners),
            "banners": banners
        }

    finally:
        connection.close()


# ============================================================
# Search Banners
# ============================================================

def search_banners(
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
            FROM banners
            WHERE (
                banner_name LIKE ?
                OR title LIKE ?
                OR subtitle LIKE ?
                OR description LIKE ?
            )
            AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (
                search_value,
                search_value,
                search_value,
                search_value,
                limit,
                offset
            )
        )

        banners = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(banners),
            "banners": banners
        }

    finally:
        connection.close()


# ============================================================
# Update Banner
# ============================================================

def update_banner(banner_id, **fields):
    allowed_fields = {
        "banner_name",
        "title",
        "subtitle",
        "description",
        "image_url",
        "mobile_image_url",
        "desktop_image_url",
        "banner_type",
        "placement",
        "target_type",
        "target_id",
        "redirect_url",
        "button_text",
        "display_order",
        "is_featured",
        "is_active",
        "start_at",
        "end_at"
    }

    update_fields = []
    values = []

    for field, value in fields.items():

        if field not in allowed_fields:
            continue

        if field == "banner_name" and value:
            value = value.strip()

        if field == "image_url" and value:
            value = value.strip()

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
            SELECT *
            FROM banners
            WHERE banner_id = ?
            AND deleted_at IS NULL
            """,
            (banner_id,)
        )

        banner = cursor.fetchone()

        if not banner:
            return {
                "success": False,
                "message": "Banner not found"
            }

        final_start_at = fields.get(
            "start_at",
            banner["start_at"]
        )

        final_end_at = fields.get(
            "end_at",
            banner["end_at"]
        )

        if (
            final_start_at
            and final_end_at
            and final_start_at >= final_end_at
        ):
            return {
                "success": False,
                "message": "End time must be greater than start time"
            }

        update_fields.append("updated_at = ?")
        values.append(_current_time())

        values.append(banner_id)

        query = f"""
            UPDATE banners
            SET {", ".join(update_fields)}
            WHERE banner_id = ?
            AND deleted_at IS NULL
        """

        cursor.execute(query, values)

        connection.commit()

        return {
            "success": True,
            "message": "Banner updated successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update banner",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Update Banner Status
# ============================================================

def update_banner_status(banner_id, status):
    allowed_statuses = (
        "active",
        "inactive",
        "scheduled",
        "expired",
        "draft",
        "blocked",
        "deleted"
    )

    if status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid banner status"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = _current_time()

        is_active = (
            1
            if status in ("active", "scheduled")
            else 0
        )

        deleted_at = (
            now
            if status == "deleted"
            else None
        )

        cursor.execute(
            """
            UPDATE banners
            SET status = ?,
                is_active = ?,
                deleted_at = ?,
                updated_at = ?
            WHERE banner_id = ?
            AND deleted_at IS NULL
            """,
            (
                status,
                is_active,
                deleted_at,
                now,
                banner_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Banner not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": f"Banner status changed to {status}"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update banner status",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Delete Banner
# ============================================================

def delete_banner(banner_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = _current_time()

        cursor.execute(
            """
            UPDATE banners
            SET status = 'deleted',
                is_active = 0,
                deleted_at = ?,
                updated_at = ?
            WHERE banner_id = ?
            AND deleted_at IS NULL
            """,
            (
                now,
                now,
                banner_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Banner not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Banner deleted successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to delete banner",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Increment Banner View
# ============================================================

def increment_banner_view(banner_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE banners
            SET view_count = view_count + 1,
                updated_at = ?
            WHERE banner_id = ?
            AND deleted_at IS NULL
            """,
            (
                _current_time(),
                banner_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Banner not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Banner view updated"
        }

    finally:
        connection.close()


# ============================================================
# Increment Banner Click
# ============================================================

def increment_banner_click(banner_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE banners
            SET click_count = click_count + 1,
                updated_at = ?
            WHERE banner_id = ?
            AND deleted_at IS NULL
            """,
            (
                _current_time(),
                banner_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Banner not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Banner click updated"
        }

    finally:
        connection.close()


# ============================================================
# Get Featured Banners
# ============================================================

def get_featured_banners(
    placement="home",
    limit=10
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = _current_time()

        cursor.execute(
            """
            SELECT *
            FROM banners
            WHERE placement = ?
            AND is_featured = 1
            AND is_active = 1
            AND status = 'active'
            AND deleted_at IS NULL
            AND (
                start_at IS NULL
                OR start_at <= ?
            )
            AND (
                end_at IS NULL
                OR end_at > ?
            )
            ORDER BY display_order ASC
            LIMIT ?
            """,
            (
                placement,
                now,
                now,
                limit
            )
        )

        banners = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(banners),
            "banners": banners
        }

    finally:
        connection.close()


# ============================================================
# Update Display Order
# ============================================================

def update_banner_order(
    banner_id,
    display_order
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE banners
            SET display_order = ?,
                updated_at = ?
            WHERE banner_id = ?
            AND deleted_at IS NULL
            """,
            (
                display_order,
                _current_time(),
                banner_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Banner not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Banner display order updated"
        }

    finally:
        connection.close()


# ============================================================
# Refresh Scheduled / Expired Banner Status
# ============================================================

def refresh_banner_status():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = _current_time()

        # Scheduled -> Active
        cursor.execute(
            """
            UPDATE banners
            SET status = 'active',
                is_active = 1,
                updated_at = ?
            WHERE status = 'scheduled'
            AND start_at IS NOT NULL
            AND start_at <= ?
            AND (
                end_at IS NULL
                OR end_at > ?
            )
            AND deleted_at IS NULL
            """,
            (
                now,
                now,
                now
            )
        )

        activated_count = cursor.rowcount

        # Active / Scheduled -> Expired
        cursor.execute(
            """
            UPDATE banners
            SET status = 'expired',
                is_active = 0,
                updated_at = ?
            WHERE status IN ('active', 'scheduled')
            AND end_at IS NOT NULL
            AND end_at <= ?
            AND deleted_at IS NULL
            """,
            (
                now,
                now
            )
        )

        expired_count = cursor.rowcount

        connection.commit()

        return {
            "success": True,
            "activated_count": activated_count,
            "expired_count": expired_count
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to refresh banner status",
            "error": str(error)
        }

    finally:
        connection.close()
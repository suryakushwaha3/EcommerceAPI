import os
import uuid
from datetime import datetime

from database.database import get_db_connection


# =========================================================
# Configuration
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

PRODUCT_UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "uploads",
    "products"
)

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


# =========================================================
# Helpers
# =========================================================

def _current_time():
    return datetime.utcnow().isoformat()


def _generate_image_id():
    return f"IMG_{uuid.uuid4().hex[:16].upper()}"


def _ensure_product_upload_directory():
    os.makedirs(
        PRODUCT_UPLOAD_DIR,
        exist_ok=True
    )


def _get_file_extension(filename):
    if not filename:
        return None

    extension = os.path.splitext(filename)[1]

    if not extension:
        return None

    return extension.lower().replace(".", "")


def _is_allowed_image(filename, mime_type=None):
    extension = _get_file_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        return False

    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        return False

    return True


def _generate_image_filename(extension):
    return f"{uuid.uuid4().hex.upper()}.{extension}"


def _get_image_url(filename):
    return f"/uploads/products/{filename}"


# =========================================================
# Create Product Image Using URL
# =========================================================

def create_product_image(
    product_id,
    image_url,
    image_type="product",
    alt_text=None,
    title=None,
    is_primary=0,
    is_thumbnail=0,
    sort_order=0,
    width=None,
    height=None,
    file_size=None,
    mime_type=None
):
    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # -------------------------------------------------
        # Check Product
        # -------------------------------------------------

        cursor.execute("""
            SELECT product_id
            FROM products
            WHERE product_id = ?
              AND status != 'deleted'
        """, (product_id,))

        product = cursor.fetchone()

        if not product:
            return {
                "success": False,
                "message": "Product not found."
            }

        # -------------------------------------------------
        # Validate Image Type
        # -------------------------------------------------

        allowed_types = {
            "product",
            "thumbnail",
            "front",
            "back",
            "side",
            "top",
            "bottom",
            "detail",
            "packaging",
            "lifestyle",
            "banner"
        }

        if image_type not in allowed_types:
            return {
                "success": False,
                "message": "Invalid image type."
            }

        # -------------------------------------------------
        # Primary Image
        # -------------------------------------------------

        if is_primary:
            cursor.execute("""
                UPDATE product_images
                SET is_primary = 0,
                    updated_at = ?
                WHERE product_id = ?
                  AND status = 'active'
            """, (
                _current_time(),
                product_id
            ))

        # -------------------------------------------------
        # Thumbnail
        # -------------------------------------------------

        if is_thumbnail:
            cursor.execute("""
                UPDATE product_images
                SET is_thumbnail = 0,
                    updated_at = ?
                WHERE product_id = ?
                  AND status = 'active'
            """, (
                _current_time(),
                product_id
            ))

        # -------------------------------------------------
        # Generate ID
        # -------------------------------------------------

        image_id = _generate_image_id()
        current_time = _current_time()

        # -------------------------------------------------
        # Insert
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO product_images (
                image_id,
                product_id,
                image_url,
                image_type,
                alt_text,
                title,
                is_primary,
                is_thumbnail,
                sort_order,
                width,
                height,
                file_size,
                mime_type,
                status,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
        """, (
            image_id,
            product_id,
            image_url,
            image_type,
            alt_text,
            title,
            int(bool(is_primary)),
            int(bool(is_thumbnail)),
            sort_order,
            width,
            height,
            file_size,
            mime_type,
            "active",
            current_time,
            current_time
        ))

        connection.commit()

        return {
            "success": True,
            "message": "Product image created successfully.",
            "image_id": image_id
        }

    except Exception as e:
        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        connection.close()


# =========================================================
# Upload Product Image
# =========================================================

def upload_product_image(
    product_id,
    image_file,
    image_type="product",
    alt_text=None,
    title=None,
    is_primary=0,
    is_thumbnail=0,
    sort_order=0
):
    connection = get_db_connection()

    saved_file_path = None

    try:
        cursor = connection.cursor()

        # -------------------------------------------------
        # Validate File
        # -------------------------------------------------

        if image_file is None:
            return {
                "success": False,
                "message": "Image file is required."
            }

        if not image_file.filename:
            return {
                "success": False,
                "message": "Image filename is required."
            }

        # -------------------------------------------------
        # Check Product
        # -------------------------------------------------

        cursor.execute("""
            SELECT product_id
            FROM products
            WHERE product_id = ?
              AND status != 'deleted'
        """, (product_id,))

        product = cursor.fetchone()

        if not product:
            return {
                "success": False,
                "message": "Product not found."
            }

        # -------------------------------------------------
        # Validate Image Type
        # -------------------------------------------------

        allowed_types = {
            "product",
            "thumbnail",
            "front",
            "back",
            "side",
            "top",
            "bottom",
            "detail",
            "packaging",
            "lifestyle",
            "banner"
        }

        if image_type not in allowed_types:
            return {
                "success": False,
                "message": "Invalid image type."
            }

        # -------------------------------------------------
        # Validate File
        # -------------------------------------------------

        filename = image_file.filename
        mime_type = image_file.mimetype

        if not _is_allowed_image(
            filename,
            mime_type
        ):
            return {
                "success": False,
                "message": (
                    "Invalid image format. "
                    "Only JPG, JPEG, PNG and WEBP are allowed."
                )
            }

        # -------------------------------------------------
        # Check File Size
        # -------------------------------------------------

        image_file.seek(0, os.SEEK_END)

        file_size = image_file.tell()

        image_file.seek(0)

        if file_size <= 0:
            return {
                "success": False,
                "message": "Image file is empty."
            }

        if file_size > MAX_IMAGE_SIZE:
            return {
                "success": False,
                "message": "Image size must not exceed 10 MB."
            }

        # -------------------------------------------------
        # Generate Image ID
        # -------------------------------------------------

        image_id = _generate_image_id()

        extension = _get_file_extension(filename)

        saved_filename = _generate_image_filename(
            extension
        )

        # -------------------------------------------------
        # Create Directory
        # -------------------------------------------------

        _ensure_product_upload_directory()

        saved_file_path = os.path.join(
            PRODUCT_UPLOAD_DIR,
            saved_filename
        )

        # -------------------------------------------------
        # Save Physical Image
        # -------------------------------------------------

        image_file.save(saved_file_path)

        # -------------------------------------------------
        # Primary Image
        # -------------------------------------------------

        if is_primary:
            cursor.execute("""
                UPDATE product_images
                SET is_primary = 0,
                    updated_at = ?
                WHERE product_id = ?
                  AND status = 'active'
            """, (
                _current_time(),
                product_id
            ))

        # -------------------------------------------------
        # Thumbnail
        # -------------------------------------------------

        if is_thumbnail:
            cursor.execute("""
                UPDATE product_images
                SET is_thumbnail = 0,
                    updated_at = ?
                WHERE product_id = ?
                  AND status = 'active'
            """, (
                _current_time(),
                product_id
            ))

        # -------------------------------------------------
        # Image URL
        # -------------------------------------------------

        image_url = _get_image_url(
            saved_filename
        )

        current_time = _current_time()

        # -------------------------------------------------
        # Insert Database Record
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO product_images (
                image_id,
                product_id,
                image_url,
                image_type,
                alt_text,
                title,
                is_primary,
                is_thumbnail,
                sort_order,
                width,
                height,
                file_size,
                mime_type,
                status,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
        """, (
            image_id,
            product_id,
            image_url,
            image_type,
            alt_text,
            title,
            int(bool(is_primary)),
            int(bool(is_thumbnail)),
            sort_order,
            None,
            None,
            file_size,
            mime_type,
            "active",
            current_time,
            current_time
        ))

        connection.commit()

        return {
            "success": True,
            "message": "Product image uploaded successfully.",
            "image": {
                "image_id": image_id,
                "product_id": product_id,
                "image_url": image_url,
                "image_type": image_type,
                "is_primary": int(bool(is_primary)),
                "is_thumbnail": int(bool(is_thumbnail)),
                "sort_order": sort_order,
                "file_size": file_size,
                "mime_type": mime_type
            }
        }

    except Exception as e:
        connection.rollback()

        # -------------------------------------------------
        # Remove File If DB Insert Failed
        # -------------------------------------------------

        if saved_file_path and os.path.exists(
            saved_file_path
        ):
            try:
                os.remove(saved_file_path)
            except Exception:
                pass

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        connection.close()


# =========================================================
# Get Image By ID
# =========================================================

def get_product_image_by_id(image_id):
    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM product_images
            WHERE image_id = ?
              AND status != 'deleted'
        """, (image_id,))

        image = cursor.fetchone()

        if not image:
            return {
                "success": False,
                "message": "Product image not found."
            }

        return {
            "success": True,
            "image": dict(image)
        }

    finally:
        connection.close()


# =========================================================
# Get All Images Of Product
# =========================================================

def get_product_images(product_id):
    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM product_images
            WHERE product_id = ?
              AND status = 'active'
            ORDER BY
                is_primary DESC,
                is_thumbnail DESC,
                sort_order ASC,
                id ASC
        """, (product_id,))

        images = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "count": len(images),
            "images": images
        }

    finally:
        connection.close()


# =========================================================
# Update Product Image
# =========================================================

def update_product_image(image_id, **fields):

    allowed_fields = {
        "image_url",
        "image_type",
        "alt_text",
        "title",
        "is_primary",
        "is_thumbnail",
        "sort_order",
        "width",
        "height",
        "file_size",
        "mime_type"
    }

    update_fields = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not update_fields:
        return {
            "success": False,
            "message": "No valid fields provided for update."
        }

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # -------------------------------------------------
        # Get Existing Image
        # -------------------------------------------------

        cursor.execute("""
            SELECT *
            FROM product_images
            WHERE image_id = ?
              AND status != 'deleted'
        """, (image_id,))

        image = cursor.fetchone()

        if not image:
            return {
                "success": False,
                "message": "Product image not found."
            }

        product_id = image["product_id"]

        # -------------------------------------------------
        # Validate Image Type
        # -------------------------------------------------

        if "image_type" in update_fields:

            allowed_types = {
                "product",
                "thumbnail",
                "front",
                "back",
                "side",
                "top",
                "bottom",
                "detail",
                "packaging",
                "lifestyle",
                "banner"
            }

            if update_fields["image_type"] not in allowed_types:
                return {
                    "success": False,
                    "message": "Invalid image type."
                }

        # -------------------------------------------------
        # Primary Image
        # -------------------------------------------------

        if update_fields.get("is_primary"):

            cursor.execute("""
                UPDATE product_images
                SET is_primary = 0,
                    updated_at = ?
                WHERE product_id = ?
                  AND status = 'active'
                  AND image_id != ?
            """, (
                _current_time(),
                product_id,
                image_id
            ))

        # -------------------------------------------------
        # Thumbnail
        # -------------------------------------------------

        if update_fields.get("is_thumbnail"):

            cursor.execute("""
                UPDATE product_images
                SET is_thumbnail = 0,
                    updated_at = ?
                WHERE product_id = ?
                  AND status = 'active'
                  AND image_id != ?
            """, (
                _current_time(),
                product_id,
                image_id
            ))

        # -------------------------------------------------
        # Build Query
        # -------------------------------------------------

        update_fields["updated_at"] = _current_time()

        set_clause = ", ".join(
            f"{field} = ?"
            for field in update_fields
        )

        values = list(
            update_fields.values()
        )

        values.append(image_id)

        cursor.execute(
            f"""
            UPDATE product_images
            SET {set_clause}
            WHERE image_id = ?
              AND status != 'deleted'
            """,
            values
        )

        connection.commit()

        return {
            "success": True,
            "message": "Product image updated successfully.",
            "image_id": image_id
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        connection.close()


# =========================================================
# Delete Product Image
# =========================================================

def delete_product_image(image_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT image_url
            FROM product_images
            WHERE image_id = ?
              AND status != 'deleted'
        """, (image_id,))

        image = cursor.fetchone()

        if not image:
            return {
                "success": False,
                "message": "Product image not found."
            }

        image_url = image["image_url"]

        current_time = _current_time()

        # -------------------------------------------------
        # Soft Delete Database Record
        # -------------------------------------------------

        cursor.execute("""
            UPDATE product_images
            SET status = 'deleted',
                deleted_at = ?,
                updated_at = ?
            WHERE image_id = ?
        """, (
            current_time,
            current_time,
            image_id
        ))

        connection.commit()

        # -------------------------------------------------
        # Delete Local Uploaded File
        # -------------------------------------------------

        if image_url and image_url.startswith(
            "/uploads/products/"
        ):

            filename = os.path.basename(
                image_url
            )

            file_path = os.path.join(
                PRODUCT_UPLOAD_DIR,
                filename
            )

            if os.path.exists(file_path):

                try:
                    os.remove(file_path)
                except Exception:
                    pass

        return {
            "success": True,
            "message": "Product image deleted successfully.",
            "image_id": image_id
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        connection.close()


# =========================================================
# Set Primary Image
# =========================================================

def set_primary_product_image(image_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT product_id
            FROM product_images
            WHERE image_id = ?
              AND status = 'active'
        """, (image_id,))

        image = cursor.fetchone()

        if not image:
            return {
                "success": False,
                "message": "Product image not found."
            }

        product_id = image["product_id"]
        current_time = _current_time()

        # -------------------------------------------------
        # Remove Primary
        # -------------------------------------------------

        cursor.execute("""
            UPDATE product_images
            SET is_primary = 0,
                updated_at = ?
            WHERE product_id = ?
              AND status = 'active'
        """, (
            current_time,
            product_id
        ))

        # -------------------------------------------------
        # Set Primary
        # -------------------------------------------------

        cursor.execute("""
            UPDATE product_images
            SET is_primary = 1,
                updated_at = ?
            WHERE image_id = ?
              AND status = 'active'
        """, (
            current_time,
            image_id
        ))

        connection.commit()

        return {
            "success": True,
            "message": "Primary image updated successfully.",
            "image_id": image_id
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        connection.close()


# =========================================================
# Set Thumbnail Image
# =========================================================

def set_thumbnail_product_image(image_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT product_id
            FROM product_images
            WHERE image_id = ?
              AND status = 'active'
        """, (image_id,))

        image = cursor.fetchone()

        if not image:
            return {
                "success": False,
                "message": "Product image not found."
            }

        product_id = image["product_id"]
        current_time = _current_time()

        # -------------------------------------------------
        # Remove Thumbnail
        # -------------------------------------------------

        cursor.execute("""
            UPDATE product_images
            SET is_thumbnail = 0,
                updated_at = ?
            WHERE product_id = ?
              AND status = 'active'
        """, (
            current_time,
            product_id
        ))

        # -------------------------------------------------
        # Set Thumbnail
        # -------------------------------------------------

        cursor.execute("""
            UPDATE product_images
            SET is_thumbnail = 1,
                updated_at = ?
            WHERE image_id = ?
              AND status = 'active'
        """, (
            current_time,
            image_id
        ))

        connection.commit()

        return {
            "success": True,
            "message": "Thumbnail image updated successfully.",
            "image_id": image_id
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        connection.close()


# =========================================================
# Update Image Status
# =========================================================

def update_product_image_status(image_id, status):

    allowed_status = {
        "active",
        "inactive",
        "deleted"
    }

    if status not in allowed_status:
        return {
            "success": False,
            "message": "Invalid image status."
        }

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT image_id
            FROM product_images
            WHERE image_id = ?
        """, (image_id,))

        image = cursor.fetchone()

        if not image:
            return {
                "success": False,
                "message": "Product image not found."
            }

        current_time = _current_time()

        deleted_at = (
            current_time
            if status == "deleted"
            else None
        )

        cursor.execute("""
            UPDATE product_images
            SET status = ?,
                deleted_at = ?,
                updated_at = ?
            WHERE image_id = ?
        """, (
            status,
            deleted_at,
            current_time,
            image_id
        ))

        connection.commit()

        return {
            "success": True,
            "message": "Product image status updated successfully.",
            "image_id": image_id,
            "status": status
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        connection.close()
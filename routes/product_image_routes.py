from flask import jsonify, request
import os
import secrets
import math
from datetime import datetime, timezone

from database.database import get_db_connection

from operations.product_image_operation import (
    create_product_image,
    upload_product_image,
    get_product_image_by_id,
    get_product_images,
    update_product_image,
    delete_product_image,
    set_primary_product_image,
    set_thumbnail_product_image,
    update_product_image_status,
    save_product_image_with_cursor,
)


def product_image_routes(app):

    # =========================================================
    # CREATE PRODUCT WITH 1-4 IMAGES
    # POST /api/products/with-image
    # =========================================================

    @app.route("/api/products/with-image", methods=["POST"])
    def create_product_with_image_route():
        connection = None
        saved_file_paths = []

        try:
            data = request.form

            def get_text(name, default=None):
                value = data.get(name)

                if value is None:
                    return default

                value = value.strip()
                return value if value else default

            def get_float(name, default=0.0):
                value = get_text(name)

                if value is None:
                    return float(default)

                try:
                    result = float(value)
                except (TypeError, ValueError):
                    raise ValueError(f"{name} must be a valid number.")

                if not math.isfinite(result):
                    raise ValueError(f"{name} must be a finite number.")

                return result

            def get_int(name, default=0):
                value = get_text(name)

                if value is None:
                    return default

                try:
                    return int(value)
                except (TypeError, ValueError):
                    raise ValueError(f"{name} must be an integer.")

            def get_bool(name, default=0):
                value = get_text(name)

                if value is None:
                    return int(bool(default))

                value = value.lower()

                if value in ("1", "true", "yes", "on"):
                    return 1

                if value in ("0", "false", "no", "off"):
                    return 0

                raise ValueError(f"{name} must be true or false.")

            # Read uploaded images.
            image_files = [
                image
                for image in request.files.getlist("images")
                if image and image.filename
            ]

            # Support older clients sending a single "image" field.
            if not image_files:
                image = request.files.get("image")

                if image and image.filename:
                    image_files = [image]

            if not image_files:
                return jsonify({
                    "success": False,
                    "message": "At least one product image is required.",
                }), 400

            if len(image_files) > 4:
                return jsonify({
                    "success": False,
                    "message": "A maximum of 4 images is allowed.",
                }), 400

            # Select the primary image using a zero-based index.
            primary_image_index = get_int("primary_image_index", 0)

            if not 0 <= primary_image_index < len(image_files):
                return jsonify({
                    "success": False,
                    "message": "Invalid primary_image_index.",
                }), 400

            # Product validation.
            product_name = get_text("product_name")
            sku = get_text("sku")
            selling_price_text = get_text("selling_price")

            if not product_name:
                return jsonify({
                    "success": False,
                    "message": "Product name is required.",
                }), 400

            if not sku:
                return jsonify({
                    "success": False,
                    "message": "SKU is required.",
                }), 400

            if selling_price_text is None:
                return jsonify({
                    "success": False,
                    "message": "Selling price is required.",
                }), 400

            slug = get_text("slug")

            if not slug:
                slug = "-".join(product_name.lower().split())

            barcode = get_text("barcode")
            selling_price = get_float("selling_price")
            mrp = get_float("mrp")
            discount_value = get_float("discount_value")
            tax_percentage = get_float("tax_percentage")

            if selling_price < 0 or mrp < 0:
                raise ValueError("Prices cannot be negative.")

            if discount_value < 0:
                raise ValueError("Discount value cannot be negative.")

            if not 0 <= tax_percentage <= 100:
                raise ValueError("Tax percentage must be between 0 and 100.")

            discount_type = get_text("discount_type", "percentage")

            if discount_type not in ("percentage", "flat", "none"):
                raise ValueError("Invalid discount type.")

            if discount_type == "percentage" and discount_value > 100:
                raise ValueError("Percentage discount cannot exceed 100.")

            if discount_type == "none":
                discount_value = 0

            stock_status = get_text("stock_status", "in_stock")
            allowed_stock_statuses = {
                "in_stock",
                "out_of_stock",
                "low_stock",
                "pre_order",
                "coming_soon",
                "discontinued",
            }

            if stock_status not in allowed_stock_statuses:
                raise ValueError("Invalid stock status.")

            status = get_text("status", "active")
            allowed_statuses = {
                "active",
                "inactive",
                "draft",
                "pending",
                "blocked",
                "deleted",
            }

            if status not in allowed_statuses:
                raise ValueError("Invalid product status.")

            return_days = get_int("return_days", 7)

            if return_days < 0:
                raise ValueError("Return days cannot be negative.")

            # Generate product ID and timestamps.
            product_id = "PRD_" + secrets.token_hex(8).upper()
            current_time = datetime.now(timezone.utc).isoformat()

            # Open database connection.
            connection = get_db_connection()
            cursor = connection.cursor()

            # Check duplicate SKU, slug and barcode.
            cursor.execute(
                """
                SELECT product_id
                FROM products
                WHERE sku = ?
                   OR slug = ?
                   OR (? IS NOT NULL AND barcode = ?)
                """,
                (sku, slug, barcode, barcode),
            )

            if cursor.fetchone():
                connection.rollback()

                return jsonify({
                    "success": False,
                    "message": "Product with this SKU, slug or barcode already exists.",
                }), 409

            # Insert product.
            cursor.execute(
                """
                INSERT INTO products (
                    product_id,
                    product_name,
                    slug,
                    brand_id,
                    category_id,
                    subcategory_id,
                    short_description,
                    description,
                    sku,
                    barcode,
                    product_type,
                    mrp,
                    selling_price,
                    discount_type,
                    discount_value,
                    tax_percentage,
                    currency,
                    stock_status,
                    status,
                    is_featured,
                    is_bestseller,
                    is_trending,
                    is_new_arrival,
                    is_returnable,
                    is_exchangeable,
                    return_days,
                    seller_id,
                    meta_title,
                    meta_description,
                    meta_keywords,
                    rating,
                    rating_count,
                    review_count,
                    view_count,
                    wishlist_count,
                    cart_count,
                    purchase_count,
                    created_at,
                    updated_at,
                    deleted_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    0, 0, 0, 0, 0, 0, 0, ?, ?, NULL
                )
                """,
                (
                    product_id,
                    product_name,
                    slug,
                    get_text("brand_id"),
                    get_text("category_id"),
                    get_text("subcategory_id"),
                    get_text("short_description"),
                    get_text("description"),
                    sku,
                    barcode,
                    get_text("product_type", "physical"),
                    mrp,
                    selling_price,
                    discount_type,
                    discount_value,
                    tax_percentage,
                    get_text("currency", "INR"),
                    stock_status,
                    status,
                    get_bool("is_featured"),
                    get_bool("is_bestseller"),
                    get_bool("is_trending"),
                    get_bool("is_new_arrival"),
                    get_bool("is_returnable", 1),
                    get_bool("is_exchangeable", 1),
                    return_days,
                    get_text("seller_id"),
                    get_text("meta_title", product_name),
                    get_text("meta_description"),
                    get_text("meta_keywords"),
                    current_time,
                    current_time,
                ),
            )

            # Save every image using the same database cursor.
            saved_images = []
            is_multi_image_request = bool(
                request.files.getlist("images")
            )

            for index, image_file in enumerate(image_files):
                if is_multi_image_request:
                    is_primary = int(index == primary_image_index)
                    is_thumbnail = is_primary
                    sort_order = index
                else:
                    is_primary = get_bool("is_primary", 1)
                    is_thumbnail = get_bool("is_thumbnail", 1)
                    sort_order = get_int("sort_order", 0)

                    if sort_order < 0:
                        raise ValueError("Sort order cannot be negative.")

                image_result, saved_path = save_product_image_with_cursor(
                    cursor=cursor,
                    product_id=product_id,
                    image_file=image_file,
                    image_type=get_text("image_type", "product"),
                    alt_text=get_text("alt_text", product_name),
                    title=get_text("image_title", product_name),
                    is_primary=is_primary,
                    is_thumbnail=is_thumbnail,
                    sort_order=sort_order,
                )

                if saved_path:
                    saved_file_paths.append(saved_path)

                saved_images.append(image_result)

            # Save product and images together.
            connection.commit()

            return jsonify({
                "success": True,
                "message": "Product added successfully!",
                "product_id": product_id,
                "product": {
                    "product_id": product_id,
                    "product_name": product_name,
                    "slug": slug,
                    "sku": sku,
                    "barcode": barcode,
                    "mrp": mrp,
                    "selling_price": selling_price,
                    "discount_type": discount_type,
                    "discount_value": discount_value,
                    "tax_percentage": tax_percentage,
                    "currency": get_text("currency", "INR"),
                    "stock_status": stock_status,
                    "status": status,
                    "created_at": current_time,
                    "updated_at": current_time,
                },
                "images": saved_images,
                "primary_image_index": primary_image_index,
            }), 201

        except ValueError as error:
            if connection:
                connection.rollback()

            for file_path in saved_file_paths:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        app.logger.exception(
                            "Failed to remove image after rollback."
                        )

            return jsonify({
                "success": False,
                "message": str(error),
            }), 400

        except Exception:
            if connection:
                connection.rollback()

            for file_path in saved_file_paths:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        app.logger.exception(
                            "Failed to remove image after rollback."
                        )

            app.logger.exception("Failed to create product with images.")

            return jsonify({
                "success": False,
                "message": "Failed to create product and upload images.",
            }), 500

        finally:
            if connection:
                connection.close()

    # =========================================================
    # CREATE IMAGE USING URL
    # POST /api/products/<product_id>/images
    # =========================================================

    @app.route("/api/products/<string:product_id>/images", methods=["POST"])
    def create_product_image_route(product_id):
        data = request.get_json(silent=True) or {}

        image_url = data.get("image_url")

        if not image_url:
            return jsonify({
                "success": False,
                "message": "Image URL is required.",
            }), 400

        result = create_product_image(
            product_id=product_id,
            image_url=image_url,
            image_type=data.get("image_type", "product"),
            alt_text=data.get("alt_text"),
            title=data.get("title"),
            is_primary=data.get("is_primary", 0),
            is_thumbnail=data.get("is_thumbnail", 0),
            sort_order=data.get("sort_order", 0),
            width=data.get("width"),
            height=data.get("height"),
            file_size=data.get("file_size"),
            mime_type=data.get("mime_type"),
        )

        return jsonify(result), 201 if result.get("success") else 400

    # =========================================================
    # UPLOAD ONE ADDITIONAL IMAGE
    # POST /api/products/<product_id>/images/upload
    # =========================================================

    @app.route(
        "/api/products/<string:product_id>/images/upload",
        methods=["POST"],
    )
    def upload_product_image_route(product_id):
        image_file = request.files.get("image")

        if not image_file or not image_file.filename:
            return jsonify({
                "success": False,
                "message": "Image file is required.",
            }), 400

        try:
            sort_order = int(request.form.get("sort_order", 0))
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "Sort order must be a number.",
            }), 400

        if sort_order < 0:
            return jsonify({
                "success": False,
                "message": "Sort order cannot be negative.",
            }), 400

        def as_bool(value):
            return str(value).strip().lower() in {
                "1", "true", "yes", "on",
            }

        result = upload_product_image(
            product_id=product_id,
            image_file=image_file,
            image_type=request.form.get("image_type", "product"),
            alt_text=request.form.get("alt_text"),
            title=request.form.get("title"),
            is_primary=as_bool(request.form.get("is_primary", "0")),
            is_thumbnail=as_bool(request.form.get("is_thumbnail", "0")),
            sort_order=sort_order,
        )

        return jsonify(result), 201 if result.get("success") else 400

    # =========================================================
    # GET ALL PRODUCT IMAGES
    # GET /api/products/<product_id>/images
    # =========================================================

    @app.route("/api/products/<string:product_id>/images", methods=["GET"])
    def get_product_images_route(product_id):
        result = get_product_images(product_id)
        return jsonify(result), 200 if result.get("success") else 404

    # =========================================================
    # GET IMAGE BY ID
    # GET /api/products/images/<image_id>
    # =========================================================

    @app.route("/api/products/images/<string:image_id>", methods=["GET"])
    def get_product_image_route(image_id):
        result = get_product_image_by_id(image_id)
        return jsonify(result), 200 if result.get("success") else 404

    # =========================================================
    # UPDATE IMAGE
    # PUT /api/products/images/<image_id>
    # =========================================================

    @app.route("/api/products/images/<string:image_id>", methods=["PUT"])
    def update_product_image_route(image_id):
        data = request.get_json(silent=True) or {}
        result = update_product_image(image_id=image_id, **data)
        return jsonify(result), 200 if result.get("success") else 400

    # =========================================================
    # DELETE IMAGE
    # DELETE /api/products/images/<image_id>
    # =========================================================

    @app.route("/api/products/images/<string:image_id>", methods=["DELETE"])
    def delete_product_image_route(image_id):
        result = delete_product_image(image_id)
        return jsonify(result), 200 if result.get("success") else 404

    # =========================================================
    # SET PRIMARY IMAGE
    # PUT /api/products/images/<image_id>/primary
    # =========================================================

    @app.route(
        "/api/products/images/<string:image_id>/primary",
        methods=["PUT"],
    )
    def set_primary_product_image_route(image_id):
        result = set_primary_product_image(image_id)
        return jsonify(result), 200 if result.get("success") else 404

    # =========================================================
    # SET THUMBNAIL IMAGE
    # PUT /api/products/images/<image_id>/thumbnail
    # =========================================================

    @app.route(
        "/api/products/images/<string:image_id>/thumbnail",
        methods=["PUT"],
    )
    def set_thumbnail_product_image_route(image_id):
        result = set_thumbnail_product_image(image_id)
        return jsonify(result), 200 if result.get("success") else 404

    # =========================================================
    # UPDATE IMAGE STATUS
    # PUT /api/products/images/<image_id>/status
    # =========================================================

    @app.route(
        "/api/products/images/<string:image_id>/status",
        methods=["PUT"],
    )
    def update_product_image_status_route(image_id):
        data = request.get_json(silent=True) or {}
        status = data.get("status")

        if not status:
            return jsonify({
                "success": False,
                "message": "Status is required.",
            }), 400

        result = update_product_image_status(
            image_id=image_id,
            status=status,
        )

        return jsonify(result), 200 if result.get("success") else 400
 
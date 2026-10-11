import os

from flask import request, jsonify

from database.database import get_db_connection

from operations.product_image_operation import (
    save_product_image_with_cursor
)

from operations.product_operation import (
    create_product,
    get_product_by_id,
    get_product_by_sku,
    get_product_by_slug,
    update_product,
    delete_product,
    update_product_status,
    update_stock_status,
    search_products,
    increment_product_view,
    update_wishlist_count,
    update_cart_count,
    increment_purchase_count,
    get_featured_products,
    get_bestseller_products,
    get_trending_products,
    get_new_arrivals,
    get_product_details
)


def product_routes(app):

    # ============================================================
    # HELPERS
    # ============================================================

    def get_request_data():
        """Accept JSON and multipart/form-data."""
        if request.is_json:
            return request.get_json(silent=True) or {}

        return request.form.to_dict()

    def parse_int(value, default=0):
        if value is None or str(value).strip() == "":
            return default
        return int(value)

    def parse_float(value, default=0.0):
        if value is None or str(value).strip() == "":
            return default
        return float(value)

    def parse_bool_int(value, default=0):
        """Accept common boolean values and return 0 or 1."""
        if value is None or str(value).strip() == "":
            return default

        if isinstance(value, bool):
            return int(value)

        normalized = str(value).strip().lower()

        if normalized in ("1", "true", "yes", "on"):
            return 1

        if normalized in ("0", "false", "no", "off"):
            return 0

        raise ValueError(
            f"Invalid boolean value: {value}. Use 1/0 or true/false."
        )

    def error_response(message, status_code=400, error=None):
        response = {
            "success": False,
            "message": message
        }

        if error is not None:
            response["error"] = str(error)

        return jsonify(response), status_code

    def cleanup_saved_files(saved_file_paths):
        """Remove files saved during a failed image upload."""
        for file_path in saved_file_paths:
            try:
                if file_path and os.path.isfile(file_path):
                    os.remove(file_path)
            except OSError:
                app.logger.exception(
                    "Failed to clean up uploaded product image"
                )

    # ============================================================
    # CREATE PRODUCT WITH UP TO 4 IMAGES
    # POST /api/products
    # ============================================================

    @app.route("/api/products", methods=["POST"])
    def create_product_route():

        product_created = False
        product_id = None

        try:
            data = get_request_data()

            product_name = data.get("product_name")
            sku = data.get("sku")
            selling_price = data.get("selling_price")

            # ----------------------------------------------------
            # REQUIRED FIELD VALIDATION
            # ----------------------------------------------------

            if not product_name or not str(product_name).strip():
                return error_response("Product name is required")

            if not sku or not str(sku).strip():
                return error_response("SKU is required")

            if selling_price is None or str(selling_price).strip() == "":
                return error_response("Selling price is required")

            # ----------------------------------------------------
            # GET UPLOADED IMAGES
            # Use the same "images" key for each file.
            # ----------------------------------------------------

            uploaded_images = request.files.getlist("images")

            uploaded_images = [
                image for image in uploaded_images
                if image and image.filename
            ]

            if len(uploaded_images) > 4:
                return error_response(
                    "Maximum 4 product images are allowed"
                )

            # ----------------------------------------------------
            # PARSE PRODUCT FIELDS
            # ----------------------------------------------------

            try:
                selling_price = parse_float(selling_price)
                mrp = parse_float(data.get("mrp"), 0)

                discount_value = parse_float(
                    data.get("discount_value"), 0
                )

                tax_percentage = parse_float(
                    data.get("tax_percentage"), 0
                )

                return_days = parse_int(
                    data.get("return_days"), 7
                )

                is_featured = parse_bool_int(
                    data.get("is_featured"), 0
                )

                is_bestseller = parse_bool_int(
                    data.get("is_bestseller"), 0
                )

                is_trending = parse_bool_int(
                    data.get("is_trending"), 0
                )

                is_new_arrival = parse_bool_int(
                    data.get("is_new_arrival"), 0
                )

                is_returnable = parse_bool_int(
                    data.get("is_returnable"), 1
                )

                is_exchangeable = parse_bool_int(
                    data.get("is_exchangeable"), 1
                )

                primary_image_index = parse_int(
                    data.get("primary_image_index"), 0
                )

            except (TypeError, ValueError) as error:
                return error_response(
                    "Invalid numeric or boolean value in product fields",
                    error=error
                )

            # ----------------------------------------------------
            # BASIC VALIDATION
            # ----------------------------------------------------

            if selling_price < 0 or mrp < 0:
                return error_response(
                    "Selling price and MRP cannot be negative"
                )

            if discount_value < 0 or tax_percentage < 0:
                return error_response(
                    "Discount and tax values cannot be negative"
                )

            if return_days < 0:
                return error_response(
                    "Return days cannot be negative"
                )

            if uploaded_images:
                if not 0 <= primary_image_index < len(uploaded_images):
                    return error_response(
                        "primary_image_index must identify one of "
                        "the uploaded images, starting from 0"
                    )
            else:
                primary_image_index = 0

            # ----------------------------------------------------
            # CREATE PRODUCT
            # NOTE: create_product() commits the product separately.
            # ----------------------------------------------------

            result = create_product(
                product_name=str(product_name).strip(),
                sku=str(sku).strip(),
                selling_price=selling_price,
                mrp=mrp,
                slug=data.get("slug") or None,
                brand_id=data.get("brand_id") or None,
                category_id=data.get("category_id") or None,
                subcategory_id=data.get("subcategory_id") or None,
                short_description=data.get("short_description"),
                description=data.get("description"),
                barcode=data.get("barcode") or None,
                product_type=data.get("product_type") or "physical",
                discount_type=data.get("discount_type") or "percentage",
                discount_value=discount_value,
                tax_percentage=tax_percentage,
                currency=data.get("currency") or "INR",
                stock_status=data.get("stock_status") or "in_stock",
                seller_id=data.get("seller_id") or None,
                is_featured=is_featured,
                is_bestseller=is_bestseller,
                is_trending=is_trending,
                is_new_arrival=is_new_arrival,
                is_returnable=is_returnable,
                is_exchangeable=is_exchangeable,
                return_days=return_days
            )

            if not result.get("success"):
                return jsonify(result), 400

            product_created = True
            product_id = result.get("product_id")

            # ----------------------------------------------------
            # SAVE PRODUCT IMAGES
            # ----------------------------------------------------

            saved_file_paths = []
            saved_images = []

            if uploaded_images:

                connection = None
                cursor = None

                try:
                    connection = get_db_connection()
                    cursor = connection.cursor()

                    # Ensure that the product exists before saving
                    # image records.
                    cursor.execute(
                        """
                        SELECT product_id
                        FROM products
                        WHERE product_id = ?
                        """,
                        (product_id,)
                    )

                    product_row = cursor.fetchone()

                    if not product_row:
                        raise ValueError(
                            "Created product could not be found in the database"
                        )

                    for index, image_file in enumerate(uploaded_images):

                        is_primary = int(
                            index == primary_image_index
                        )

                        image_info, saved_file_path = (
                            save_product_image_with_cursor(
                                cursor=cursor,
                                product_id=product_id,
                                image_file=image_file,
                                image_type="product",
                                alt_text=str(product_name).strip(),
                                title=str(product_name).strip(),
                                is_primary=is_primary,
                                is_thumbnail=is_primary,
                                sort_order=index
                            )
                        )

                        saved_file_paths.append(saved_file_path)
                        saved_images.append(image_info)

                    # Commit all image records together.
                    connection.commit()

                except Exception:
                    if connection:
                        try:
                            connection.rollback()
                        except Exception:
                            app.logger.exception(
                                "Failed to roll back product image transaction"
                            )

                    cleanup_saved_files(saved_file_paths)

                    app.logger.exception(
                        "Product created, but image saving failed"
                    )

                    return jsonify({
                        "success": False,
                        "product_created": True,
                        "product_id": product_id,
                        "message": (
                            "Product was created, but saving its images "
                            "failed. Do not create the product again. "
                            "Check the error and upload images to this "
                            "existing product."
                        )
                    }), 500

                finally:
                    if cursor:
                        try:
                            cursor.close()
                        except Exception:
                            pass

                    if connection:
                        try:
                            connection.close()
                        except Exception:
                            pass

            # ----------------------------------------------------
            # SUCCESS RESPONSE
            # ----------------------------------------------------

            response = dict(result)
            response["uploaded_image_count"] = len(saved_images)
            response["images"] = saved_images

            if saved_images:
                response["message"] = (
                    "Product and all images created successfully"
                )
            else:
                response["message"] = "Product created successfully"

            return jsonify(response), 201

        except Exception as error:
            app.logger.exception("Failed to create product")

            response = {
                "success": False,
                "message": "Failed to create product",
                "error": str(error)
            }

            if product_created:
                response["product_created"] = True
                response["product_id"] = product_id
                response["note"] = (
                    "The product was already created. "
                    "Do not submit the create request again with the same SKU."
                )

            return jsonify(response), 500

    # ============================================================
    # GET PRODUCT BY ID
    # GET /api/products/<product_id>
    # ============================================================

    @app.route("/api/products/<string:product_id>", methods=["GET"])
    def get_product_by_id_route(product_id):
        try:
            result = get_product_by_id(product_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to fetch product")
            return error_response(
                "Failed to fetch product", 500, error
            )

    # ============================================================
    # GET PRODUCT BY SKU
    # GET /api/products/sku/<sku>
    # ============================================================

    @app.route("/api/products/sku/<string:sku>", methods=["GET"])
    def get_product_by_sku_route(sku):
        try:
            result = get_product_by_sku(sku)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to fetch product by SKU")
            return error_response(
                "Failed to fetch product by SKU", 500, error
            )

    # ============================================================
    # GET PRODUCT BY SLUG
    # GET /api/products/slug/<slug>
    # ============================================================

    @app.route("/api/products/slug/<path:slug>", methods=["GET"])
    def get_product_by_slug_route(slug):
        try:
            result = get_product_by_slug(slug)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to fetch product by slug")
            return error_response(
                "Failed to fetch product by slug", 500, error
            )

    # ============================================================
    # UPDATE PRODUCT
    # PUT /api/products/<product_id>
    # ============================================================

    @app.route("/api/products/<string:product_id>", methods=["PUT"])
    def update_product_route(product_id):
        try:
            data = get_request_data()

            if not data:
                return error_response("No update data provided")

            result = update_product(product_id, **data)

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to update product")
            return error_response(
                "Failed to update product", 500, error
            )

    # ============================================================
    # DELETE PRODUCT - SOFT DELETE
    # DELETE /api/products/<product_id>
    # ============================================================

    @app.route(
        "/api/products/<string:product_id>",
        methods=["DELETE"]
    )
    def delete_product_route(product_id):
        try:
            result = delete_product(product_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to delete product")
            return error_response(
                "Failed to delete product", 500, error
            )

    # ============================================================
    # UPDATE PRODUCT STATUS
    # PUT /api/products/<product_id>/status
    # ============================================================

    @app.route(
        "/api/products/<string:product_id>/status",
        methods=["PUT"]
    )
    def update_product_status_route(product_id):
        try:
            data = get_request_data()
            status = data.get("status")

            if not status:
                return error_response("Product status is required")

            result = update_product_status(
                product_id=product_id,
                status=status
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to update product status")
            return error_response(
                "Failed to update product status", 500, error
            )

    # ============================================================
    # UPDATE STOCK STATUS
    # PUT /api/products/<product_id>/stock-status
    # ============================================================

    @app.route(
        "/api/products/<string:product_id>/stock-status",
        methods=["PUT"]
    )
    def update_stock_status_route(product_id):
        try:
            data = get_request_data()
            stock_status = data.get("stock_status")

            if not stock_status:
                return error_response("Stock status is required")

            result = update_stock_status(
                product_id=product_id,
                stock_status=stock_status
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to update stock status")
            return error_response(
                "Failed to update stock status", 500, error
            )

    # ============================================================
    # SEARCH / FILTER PRODUCTS
    # GET /api/products
    # ============================================================

    @app.route("/api/products", methods=["GET"])
    def search_products_route():
        try:
            search = request.args.get("search")
            category_id = request.args.get("category_id")
            subcategory_id = request.args.get("subcategory_id")
            seller_id = request.args.get("seller_id")

            status = request.args.get("status", "active")
            stock_status = request.args.get("stock_status")

            min_price = request.args.get("min_price", type=float)
            max_price = request.args.get("max_price", type=float)
            min_rating = request.args.get("min_rating", type=float)

            limit = request.args.get("limit", default=20, type=int)
            offset = request.args.get("offset", default=0, type=int)

            limit = max(1, min(limit, 100))
            offset = max(0, offset)

            result = search_products(
                search=search,
                category_id=category_id,
                subcategory_id=subcategory_id,
                seller_id=seller_id,
                status=status,
                min_price=min_price,
                max_price=max_price,
                min_rating=min_rating,
                stock_status=stock_status,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to fetch products")
            return error_response(
                "Failed to fetch products", 500, error
            )

    # ============================================================
    # INCREMENT PRODUCT VIEW
    # POST /api/products/<product_id>/view
    # ============================================================

    @app.route(
        "/api/products/<string:product_id>/view",
        methods=["POST"]
    )
    def increment_product_view_route(product_id):
        try:
            result = increment_product_view(product_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to update product view")
            return error_response(
                "Failed to update product view", 500, error
            )

    # ============================================================
    # UPDATE WISHLIST COUNT
    # POST /api/products/<product_id>/wishlist-count
    # ============================================================

    @app.route(
        "/api/products/<string:product_id>/wishlist-count",
        methods=["POST"]
    )
    def update_wishlist_count_route(product_id):
        try:
            data = get_request_data()
            increment = parse_bool_int(
                data.get("increment"), 1
            )

            result = update_wishlist_count(
                product_id=product_id,
                increment=bool(increment)
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to update wishlist count")
            return error_response(
                "Failed to update wishlist count", 500, error
            )

    # ============================================================
    # UPDATE CART COUNT
    # POST /api/products/<product_id>/cart-count
    # ============================================================

    @app.route(
        "/api/products/<string:product_id>/cart-count",
        methods=["POST"]
    )
    def update_cart_count_route(product_id):
        try:
            data = get_request_data()
            increment = parse_bool_int(
                data.get("increment"), 1
            )

            result = update_cart_count(
                product_id=product_id,
                increment=bool(increment)
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to update cart count")
            return error_response(
                "Failed to update cart count", 500, error
            )

    # ============================================================
    # INCREMENT PURCHASE COUNT
    # POST /api/products/<product_id>/purchase-count
    # ============================================================

    @app.route(
        "/api/products/<string:product_id>/purchase-count",
        methods=["POST"]
    )
    def increment_purchase_count_route(product_id):
        try:
            data = get_request_data()
            quantity = data.get("quantity", 1)

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                return error_response(
                    "Quantity must be a valid integer"
                )

            if quantity <= 0:
                return error_response(
                    "Quantity must be greater than 0"
                )

            result = increment_purchase_count(
                product_id=product_id,
                quantity=quantity
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to update purchase count")
            return error_response(
                "Failed to update purchase count", 500, error
            )

    # ============================================================
    # FEATURED PRODUCTS
    # GET /api/products/featured
    # ============================================================

    @app.route("/api/products/featured", methods=["GET"])
    def get_featured_products_route():
        try:
            limit = request.args.get("limit", default=20, type=int)
            limit = max(1, min(limit, 100))

            result = get_featured_products(limit=limit)
            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to fetch featured products")
            return error_response(
                "Failed to fetch featured products", 500, error
            )

    # ============================================================
    # BESTSELLER PRODUCTS
    # GET /api/products/bestsellers
    # ============================================================

    @app.route("/api/products/bestsellers", methods=["GET"])
    def get_bestseller_products_route():
        try:
            limit = request.args.get("limit", default=20, type=int)
            limit = max(1, min(limit, 100))

            result = get_bestseller_products(limit=limit)
            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to fetch bestsellers")
            return error_response(
                "Failed to fetch bestsellers", 500, error
            )

    # ============================================================
    # TRENDING PRODUCTS
    # GET /api/products/trending
    # ============================================================

    @app.route("/api/products/trending", methods=["GET"])
    def get_trending_products_route():
        try:
            limit = request.args.get("limit", default=20, type=int)
            limit = max(1, min(limit, 100))

            result = get_trending_products(limit=limit)
            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to fetch trending products")
            return error_response(
                "Failed to fetch trending products", 500, error
            )

    # ============================================================
    # NEW ARRIVALS
    # GET /api/products/new-arrivals
    # ============================================================

    @app.route("/api/products/new-arrivals", methods=["GET"])
    def get_new_arrivals_route():
        try:
            limit = request.args.get("limit", default=20, type=int)
            limit = max(1, min(limit, 100))

            result = get_new_arrivals(limit=limit)
            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to fetch new arrivals")
            return error_response(
                "Failed to fetch new arrivals", 500, error
            )

    # ============================================================
    # GET COMPLETE PRODUCT DETAILS
    # GET /api/products/<product_id>/details
    # ============================================================

    @app.route(
        "/api/products/<string:product_id>/details",
        methods=["GET"]
    )
    def product_details(product_id):
        try:
            result = get_product_details(product_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            app.logger.exception("Failed to fetch product details")
            return error_response(
                "Failed to fetch product details", 500, error
            )
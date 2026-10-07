from unittest import result

from flask import app, request, jsonify

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
    # CREATE PRODUCT
    # POST /api/products
    # ============================================================

    @app.route("/api/products", methods=["POST"])
    def create_product_route():
        try:
            data = request.get_json(silent=True) or {}

            product_name = data.get("product_name")
            sku = data.get("sku")
            selling_price = data.get("selling_price")

            if not product_name or not sku or selling_price is None:
                return jsonify({
                    "success": False,
                    "message": "Product name, SKU and selling price are required"
                }), 400

            result = create_product(
                product_name=product_name,
                sku=sku,
                selling_price=selling_price,
                mrp=data.get("mrp", 0),
                slug=data.get("slug"),
                brand_id=data.get("brand_id"),
                category_id=data.get("category_id"),
                subcategory_id=data.get("subcategory_id"),
                short_description=data.get("short_description"),
                description=data.get("description"),
                barcode=data.get("barcode"),
                product_type=data.get("product_type", "physical"),
                discount_type=data.get("discount_type", "percentage"),
                discount_value=data.get("discount_value", 0),
                tax_percentage=data.get("tax_percentage", 0),
                currency=data.get("currency", "INR"),
                stock_status=data.get("stock_status", "in_stock"),
                seller_id=data.get("seller_id"),
                is_featured=data.get("is_featured", 0),
                is_bestseller=data.get("is_bestseller", 0),
                is_trending=data.get("is_trending", 0),
                is_new_arrival=data.get("is_new_arrival", 0),
                is_returnable=data.get("is_returnable", 1),
                is_exchangeable=data.get("is_exchangeable", 1),
                return_days=data.get("return_days", 7)
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 201

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to create product",
                "error": str(error)
            }), 500


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
            return jsonify({
                "success": False,
                "message": "Failed to fetch product",
                "error": str(error)
            }), 500


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
            return jsonify({
                "success": False,
                "message": "Failed to fetch product",
                "error": str(error)
            }), 500


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
            return jsonify({
                "success": False,
                "message": "Failed to fetch product",
                "error": str(error)
            }), 500


    # ============================================================
    # UPDATE PRODUCT
    # PUT /api/products/<product_id>
    # ============================================================

    @app.route("/api/products/<string:product_id>", methods=["PUT"])
    def update_product_route(product_id):
        try:
            data = request.get_json(silent=True) or {}

            if not data:
                return jsonify({
                    "success": False,
                    "message": "No update data provided"
                }), 400

            result = update_product(
                product_id,
                **data
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update product",
                "error": str(error)
            }), 500


    # ============================================================
    # DELETE PRODUCT - SOFT DELETE
    # DELETE /api/products/<product_id>
    # ============================================================

    @app.route("/api/products/<string:product_id>", methods=["DELETE"])
    def delete_product_route(product_id):
        try:
            result = delete_product(product_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to delete product",
                "error": str(error)
            }), 500


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
            data = request.get_json(silent=True) or {}

            status = data.get("status")

            if not status:
                return jsonify({
                    "success": False,
                    "message": "Product status is required"
                }), 400

            result = update_product_status(
                product_id=product_id,
                status=status
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update product status",
                "error": str(error)
            }), 500


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
            data = request.get_json(silent=True) or {}

            stock_status = data.get("stock_status")

            if not stock_status:
                return jsonify({
                    "success": False,
                    "message": "Stock status is required"
                }), 400

            result = update_stock_status(
                product_id=product_id,
                stock_status=stock_status
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update stock status",
                "error": str(error)
            }), 500


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

            status = request.args.get(
                "status",
                "active"
            )

            stock_status = request.args.get("stock_status")

            min_price = request.args.get(
                "min_price",
                type=float
            )

            max_price = request.args.get(
                "max_price",
                type=float
            )

            min_rating = request.args.get(
                "min_rating",
                type=float
            )

            limit = request.args.get(
                "limit",
                default=20,
                type=int
            )

            offset = request.args.get(
                "offset",
                default=0,
                type=int
            )

            # Safety limits
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
            return jsonify({
                "success": False,
                "message": "Failed to fetch products",
                "error": str(error)
            }), 500


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
            return jsonify({
                "success": False,
                "message": "Failed to update product view",
                "error": str(error)
            }), 500


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
            data = request.get_json(silent=True) or {}

            increment = data.get(
                "increment",
                True
            )

            result = update_wishlist_count(
                product_id=product_id,
                increment=bool(increment)
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update wishlist count",
                "error": str(error)
            }), 500


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
            data = request.get_json(silent=True) or {}

            increment = data.get(
                "increment",
                True
            )

            result = update_cart_count(
                product_id=product_id,
                increment=bool(increment)
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update cart count",
                "error": str(error)
            }), 500


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
            data = request.get_json(silent=True) or {}

            quantity = data.get(
                "quantity",
                1
            )

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": "Quantity must be a valid integer"
                }), 400

            if quantity <= 0:
                return jsonify({
                    "success": False,
                    "message": "Quantity must be greater than 0"
                }), 400

            result = increment_purchase_count(
                product_id=product_id,
                quantity=quantity
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update purchase count",
                "error": str(error)
            }), 500


    # ============================================================
    # FEATURED PRODUCTS
    # GET /api/products/featured
    # ============================================================

    @app.route("/api/products/featured", methods=["GET"])
    def get_featured_products_route():
        try:
            limit = request.args.get(
                "limit",
                default=20,
                type=int
            )

            limit = max(1, min(limit, 100))

            result = get_featured_products(
                limit=limit
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to fetch featured products",
                "error": str(error)
            }), 500


    # ============================================================
    # BESTSELLER PRODUCTS
    # GET /api/products/bestsellers
    # ============================================================

    @app.route(
        "/api/products/bestsellers",
        methods=["GET"]
    )
    def get_bestseller_products_route():
        try:
            limit = request.args.get(
                "limit",
                default=20,
                type=int
            )

            limit = max(1, min(limit, 100))

            result = get_bestseller_products(
                limit=limit
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to fetch bestseller products",
                "error": str(error)
            }), 500


    # ============================================================
    # TRENDING PRODUCTS
    # GET /api/products/trending
    # ============================================================

    @app.route(
        "/api/products/trending",
        methods=["GET"]
    )
    def get_trending_products_route():
        try:
            limit = request.args.get(
                "limit",
                default=20,
                type=int
            )

            limit = max(1, min(limit, 100))

            result = get_trending_products(
                limit=limit
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to fetch trending products",
                "error": str(error)
            }), 500


    # ============================================================
    # NEW ARRIVALS
    # GET /api/products/new-arrivals
    # ============================================================

    @app.route(
        "/api/products/new-arrivals",
        methods=["GET"]
    )
    def get_new_arrivals_route():
        try:
            limit = request.args.get(
                "limit",
                default=20,
                type=int
            )

            limit = max(1, min(limit, 100))

            result = get_new_arrivals(
                limit=limit
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to fetch new arrival products",
                "error": str(error)
            }), 



# ============================================================
# Get Complete Product Details
# ============================================================

    @app.route(
    "/api/products/<product_id>/details",
    methods=["GET"]
    )
    def product_details(product_id):

        result = get_product_details(product_id)

        if not result["success"]:
             jsonify(result), 404

        return jsonify(result), 200
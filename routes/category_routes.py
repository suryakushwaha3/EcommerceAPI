from flask import request, jsonify

from operations.category_operation import (
    create_category,
    get_category_by_id,
    get_category_by_slug,
    get_categories,
    get_subcategories,
    update_category,
    move_category,
    search_categories,
    update_category_status,
    delete_category,
    update_product_count,
    increment_category_view,
    get_featured_categories
)


def category_routes(app):

    # ========================================================
    # Create Category
    # ========================================================

    @app.route("/api/categories", methods=["POST"])
    def create_category_route():

        try:
            data = request.get_json(silent=True) or {}

            category_name = data.get("category_name")

            if not category_name:
                return jsonify({
                    "success": False,
                    "message": "category_name is required"
                }), 400

            result = create_category(
                category_name=category_name,
                slug=data.get("slug"),
                parent_category_id=data.get("parent_category_id"),
                description=data.get("description"),
                category_image=data.get("category_image"),
                banner_image=data.get("banner_image"),
                icon=data.get("icon"),
                meta_title=data.get("meta_title"),
                meta_description=data.get("meta_description"),
                meta_keywords=data.get("meta_keywords"),
                display_order=data.get("display_order", 0),
                level=data.get("level"),
                is_featured=data.get("is_featured", 0)
            )

            return jsonify(result), 201 if result.get("success") else 400

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to create category",
                "error": str(error)
            }), 500


    # ========================================================
    # Get All Categories
    # ========================================================

    @app.route("/api/categories", methods=["GET"])
    def get_categories_route():

        try:
            parent_category_id = request.args.get("parent_category_id")

            level = request.args.get("level", type=int)

            featured_only = (
                request.args.get(
                    "featured_only",
                    "false"
                ).lower() == "true"
            )

            active_only = (
                request.args.get(
                    "active_only",
                    "true"
                ).lower() == "true"
            )

            limit = request.args.get(
                "limit",
                default=50,
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

            result = get_categories(
                parent_category_id=parent_category_id,
                level=level,
                featured_only=featured_only,
                active_only=active_only,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get categories",
                "error": str(error)
            }), 500


    # ========================================================
    # Search Categories
    # ========================================================

    @app.route("/api/categories/search", methods=["GET"])
    def search_categories_route():

        try:
            search = request.args.get("search", "").strip()

            if not search:
                return jsonify({
                    "success": False,
                    "message": "search parameter is required"
                }), 400

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

            limit = max(1, min(limit, 100))
            offset = max(0, offset)

            result = search_categories(
                search=search,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to search categories",
                "error": str(error)
            }), 500


    # ========================================================
    # Get Featured Categories
    # ========================================================

    @app.route("/api/categories/featured", methods=["GET"])
    def get_featured_categories_route():

        try:
            limit = request.args.get(
                "limit",
                default=20,
                type=int
            )

            limit = max(1, min(limit, 100))

            result = get_featured_categories(
                limit=limit
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get featured categories",
                "error": str(error)
            }), 500


    # ========================================================
    # Get Category By Slug
    # ========================================================

    @app.route("/api/categories/slug/<slug>", methods=["GET"])
    def get_category_by_slug_route(slug):

        try:
            result = get_category_by_slug(slug)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get category",
                "error": str(error)
            }), 500


    # ========================================================
    # Get Subcategories
    # ========================================================

    @app.route(
        "/api/categories/<category_id>/subcategories",
        methods=["GET"]
    )
    def get_subcategories_route(category_id):

        try:
            result = get_subcategories(
                parent_category_id=category_id
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get subcategories",
                "error": str(error)
            }), 500


    # ========================================================
    # Get Category By ID
    # ========================================================

    @app.route("/api/categories/<category_id>", methods=["GET"])
    def get_category_by_id_route(category_id):

        try:
            result = get_category_by_id(category_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get category",
                "error": str(error)
            }), 500


    # ========================================================
    # Update Category
    # ========================================================

    @app.route("/api/categories/<category_id>", methods=["PUT"])
    def update_category_route(category_id):

        try:
            data = request.get_json(silent=True) or {}

            result = update_category(
                category_id,
                **data
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update category",
                "error": str(error)
            }), 500


    # ========================================================
    # Move Category
    # ========================================================

    @app.route(
        "/api/categories/<category_id>/move",
        methods=["PUT"]
    )
    def move_category_route(category_id):

        try:
            data = request.get_json(silent=True) or {}

            new_parent_category_id = data.get(
                "new_parent_category_id"
            )

            result = move_category(
                category_id=category_id,
                new_parent_category_id=new_parent_category_id
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to move category",
                "error": str(error)
            }), 500


    # ========================================================
    # Update Category Status
    # ========================================================

    @app.route(
        "/api/categories/<category_id>/status",
        methods=["PUT"]
    )
    def update_category_status_route(category_id):

        try:
            data = request.get_json(silent=True) or {}

            status = data.get("status")

            if not status:
                return jsonify({
                    "success": False,
                    "message": "status is required"
                }), 400

            result = update_category_status(
                category_id=category_id,
                status=status
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update category status",
                "error": str(error)
            }), 500


    # ========================================================
    # Delete Category
    # ========================================================

    @app.route(
        "/api/categories/<category_id>",
        methods=["DELETE"]
    )
    def delete_category_route(category_id):

        try:
            result = delete_category(
                category_id=category_id
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to delete category",
                "error": str(error)
            }), 500


    # ========================================================
    # Update Product Count
    # ========================================================

    @app.route(
        "/api/categories/<category_id>/product-count",
        methods=["PUT"]
    )
    def update_product_count_route(category_id):

        try:
            data = request.get_json(silent=True) or {}

            count = data.get("count")

            if count is None:
                return jsonify({
                    "success": False,
                    "message": "count is required"
                }), 400

            try:
                count = int(count)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": "count must be an integer"
                }), 400

            result = update_product_count(
                category_id=category_id,
                count=count
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update product count",
                "error": str(error)
            }), 500


    # ========================================================
    # Increment Category View
    # ========================================================

    @app.route(
        "/api/categories/<category_id>/view",
        methods=["POST"]
    )
    def increment_category_view_route(category_id):

        try:
            result = increment_category_view(
                category_id=category_id
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update category view",
                "error": str(error)
            }), 500
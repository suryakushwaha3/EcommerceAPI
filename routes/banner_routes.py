from flask import request, jsonify

from operations.banner_operation import (
    create_banner,
    get_banner_by_id,
    get_banners,
    get_active_banners,
    search_banners,
    update_banner,
    update_banner_status,
    delete_banner,
    increment_banner_view,
    increment_banner_click,
    get_featured_banners,
    update_banner_order,
    refresh_banner_status
)


def banner_routes(app):

    # ========================================================
    # Create Banner
    # ========================================================

    @app.route("/api/banners", methods=["POST"])
    def create_banner_route():

        try:
            data = request.get_json(silent=True) or {}

            banner_name = data.get("banner_name")
            image_url = data.get("image_url")

            if not banner_name:
                return jsonify({
                    "success": False,
                    "message": "banner_name is required"
                }), 400

            if not image_url:
                return jsonify({
                    "success": False,
                    "message": "image_url is required"
                }), 400

            result = create_banner(
                banner_name=banner_name,
                image_url=image_url,
                title=data.get("title"),
                subtitle=data.get("subtitle"),
                description=data.get("description"),
                mobile_image_url=data.get("mobile_image_url"),
                desktop_image_url=data.get("desktop_image_url"),
                banner_type=data.get(
                    "banner_type",
                    "promotional"
                ),
                placement=data.get(
                    "placement",
                    "home"
                ),
                target_type=data.get(
                    "target_type",
                    "none"
                ),
                target_id=data.get("target_id"),
                redirect_url=data.get("redirect_url"),
                button_text=data.get("button_text"),
                display_order=data.get(
                    "display_order",
                    0
                ),
                is_featured=data.get(
                    "is_featured",
                    0
                ),
                start_at=data.get("start_at"),
                end_at=data.get("end_at")
            )

            return jsonify(result), (
                201 if result.get("success")
                else 400
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to create banner",
                "error": str(error)
            }), 500


    # ========================================================
    # Get Banners
    # ========================================================

    @app.route("/api/banners", methods=["GET"])
    def get_banners_route():

        try:
            placement = request.args.get("placement")
            banner_type = request.args.get("banner_type")
            status = request.args.get("status")

            active_only = (
                request.args.get(
                    "active_only",
                    "false"
                ).lower() == "true"
            )

            featured_only = (
                request.args.get(
                    "featured_only",
                    "false"
                ).lower() == "true"
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

            limit = max(1, min(limit, 100))
            offset = max(0, offset)

            result = get_banners(
                placement=placement,
                banner_type=banner_type,
                status=status,
                active_only=active_only,
                featured_only=featured_only,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get banners",
                "error": str(error)
            }), 500


    # ========================================================
    # Search Banners
    # ========================================================

    @app.route("/api/banners/search", methods=["GET"])
    def search_banners_route():

        try:
            search = request.args.get(
                "search",
                ""
            ).strip()

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

            result = search_banners(
                search=search,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to search banners",
                "error": str(error)
            }), 500


    # ========================================================
    # Get Active Banners For Placement
    # ========================================================

    @app.route(
        "/api/banners/active",
        methods=["GET"]
    )
    def get_active_banners_route():

        try:
            placement = request.args.get(
                "placement",
                "home"
            )

            limit = request.args.get(
                "limit",
                default=20,
                type=int
            )

            limit = max(1, min(limit, 100))

            result = get_active_banners(
                placement=placement,
                limit=limit
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get active banners",
                "error": str(error)
            }), 500


    # ========================================================
    # Get Featured Banners
    # ========================================================

    @app.route(
        "/api/banners/featured",
        methods=["GET"]
    )
    def get_featured_banners_route():

        try:
            placement = request.args.get(
                "placement",
                "home"
            )

            limit = request.args.get(
                "limit",
                default=10,
                type=int
            )

            limit = max(1, min(limit, 100))

            result = get_featured_banners(
                placement=placement,
                limit=limit
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get featured banners",
                "error": str(error)
            }), 500


    # ========================================================
    # Refresh Scheduled / Expired Banner Status
    # ========================================================

    @app.route(
        "/api/banners/refresh-status",
        methods=["POST"]
    )
    def refresh_banner_status_route():

        try:
            result = refresh_banner_status()

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to refresh banner status",
                "error": str(error)
            }), 500


    # ========================================================
    # Get Banner By ID
    # ========================================================

    @app.route(
        "/api/banners/<banner_id>",
        methods=["GET"]
    )
    def get_banner_by_id_route(banner_id):

        try:
            result = get_banner_by_id(
                banner_id=banner_id
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get banner",
                "error": str(error)
            }), 500


    # ========================================================
    # Update Banner
    # ========================================================

    @app.route(
        "/api/banners/<banner_id>",
        methods=["PUT"]
    )
    def update_banner_route(banner_id):

        try:
            data = request.get_json(silent=True) or {}

            result = update_banner(
                banner_id,
                **data
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update banner",
                "error": str(error)
            }), 500


    # ========================================================
    # Update Banner Status
    # ========================================================

    @app.route(
        "/api/banners/<banner_id>/status",
        methods=["PUT"]
    )
    def update_banner_status_route(banner_id):

        try:
            data = request.get_json(silent=True) or {}

            status = data.get("status")

            if not status:
                return jsonify({
                    "success": False,
                    "message": "status is required"
                }), 400

            result = update_banner_status(
                banner_id=banner_id,
                status=status
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update banner status",
                "error": str(error)
            }), 500


    # ========================================================
    # Delete Banner
    # ========================================================

    @app.route(
        "/api/banners/<banner_id>",
        methods=["DELETE"]
    )
    def delete_banner_route(banner_id):

        try:
            result = delete_banner(
                banner_id=banner_id
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to delete banner",
                "error": str(error)
            }), 500


    # ========================================================
    # Increment Banner View
    # ========================================================

    @app.route(
        "/api/banners/<banner_id>/view",
        methods=["POST"]
    )
    def increment_banner_view_route(banner_id):

        try:
            result = increment_banner_view(
                banner_id=banner_id
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update banner view",
                "error": str(error)
            }), 500


    # ========================================================
    # Increment Banner Click
    # ========================================================

    @app.route(
        "/api/banners/<banner_id>/click",
        methods=["POST"]
    )
    def increment_banner_click_route(banner_id):

        try:
            result = increment_banner_click(
                banner_id=banner_id
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update banner click",
                "error": str(error)
            }), 500


    # ========================================================
    # Update Display Order
    # ========================================================

    @app.route(
        "/api/banners/<banner_id>/order",
        methods=["PUT"]
    )
    def update_banner_order_route(banner_id):

        try:
            data = request.get_json(silent=True) or {}

            display_order = data.get("display_order")

            if display_order is None:
                return jsonify({
                    "success": False,
                    "message": "display_order is required"
                }), 400

            try:
                display_order = int(display_order)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": "display_order must be an integer"
                }), 400

            result = update_banner_order(
                banner_id=banner_id,
                display_order=display_order
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update banner order",
                "error": str(error)
            }), 500
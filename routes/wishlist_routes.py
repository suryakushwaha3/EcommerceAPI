from flask import request, jsonify

from operations.wishlist_operation import (
    add_to_wishlist,
    get_wishlist_item,
    get_user_wishlist,
    is_in_wishlist,
    remove_from_wishlist,
    remove_product_from_wishlist,
    restore_wishlist_item,
    update_wishlist_item,
    refresh_wishlist_prices,
    get_price_drop_items,
    get_out_of_stock_items,
    clear_wishlist
)


def wishlist_routes(app):

    # ============================================================
    # Add Product To Wishlist
    # ============================================================

    @app.route("/api/wishlist", methods=["POST"])
    def add_wishlist():
        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")
            product_id = data.get("product_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            if not product_id:
                return jsonify({
                    "success": False,
                    "message": "product_id is required"
                }), 400

            result = add_to_wishlist(
                user_id=user_id,
                product_id=product_id,
                variant_id=data.get("variant_id"),
                source=data.get(
                    "source",
                    "product_page"
                ),
                priority=data.get(
                    "priority",
                    0
                ),
                notify_on_price_drop=data.get(
                    "notify_on_price_drop",
                    False
                ),
                notify_on_stock_available=data.get(
                    "notify_on_stock_available",
                    True
                ),
                notes=data.get("notes")
            )

            return jsonify(result), (
                201 if result.get("success") else 400
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to add product to wishlist",
                "error": str(error)
            }), 500


    # ============================================================
    # Get User Wishlist
    # ============================================================

    @app.route("/api/wishlist/user/<user_id>", methods=["GET"])
    def user_wishlist(user_id):
        try:
            active_only = (
                request.args.get(
                    "active_only",
                    "true"
                ).lower() == "true"
            )

            priority = request.args.get("priority")

            if priority is not None:
                try:
                    priority = int(priority)
                except ValueError:
                    return jsonify({
                        "success": False,
                        "message": "priority must be an integer"
                    }), 400

            try:
                limit = int(
                    request.args.get(
                        "limit",
                        50
                    )
                )
                offset = int(
                    request.args.get(
                        "offset",
                        0
                    )
                )
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "limit and offset must be integers"
                }), 400

            limit = max(1, min(limit, 100))
            offset = max(0, offset)

            result = get_user_wishlist(
                user_id=user_id,
                active_only=active_only,
                priority=priority,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get user wishlist",
                "error": str(error)
            }), 500


    # ============================================================
    # Get Single Wishlist Item
    # ============================================================

    @app.route("/api/wishlist/<wishlist_id>", methods=["GET"])
    def get_wishlist(wishlist_id):
        try:
            user_id = request.args.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = get_wishlist_item(
                wishlist_id=wishlist_id,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get wishlist item",
                "error": str(error)
            }), 500


    # ============================================================
    # Check Product In Wishlist
    # ============================================================

    @app.route("/api/wishlist/check", methods=["GET"])
    def check_wishlist():
        try:
            user_id = request.args.get("user_id")
            product_id = request.args.get("product_id")
            variant_id = request.args.get("variant_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            if not product_id:
                return jsonify({
                    "success": False,
                    "message": "product_id is required"
                }), 400

            result = is_in_wishlist(
                user_id=user_id,
                product_id=product_id,
                variant_id=variant_id
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to check wishlist",
                "error": str(error)
            }), 500


    # ============================================================
    # Remove Wishlist Item
    # ============================================================

    @app.route("/api/wishlist/<wishlist_id>", methods=["DELETE"])
    def remove_wishlist(wishlist_id):
        try:
            user_id = request.args.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = remove_from_wishlist(
                wishlist_id=wishlist_id,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to remove wishlist item",
                "error": str(error)
            }), 500


    # ============================================================
    # Remove Product From Wishlist
    # ============================================================

    @app.route("/api/wishlist/product/<product_id>", methods=["DELETE"])
    def remove_wishlist_product(product_id):
        try:
            user_id = request.args.get("user_id")
            variant_id = request.args.get("variant_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = remove_product_from_wishlist(
                user_id=user_id,
                product_id=product_id,
                variant_id=variant_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to remove product from wishlist",
                "error": str(error)
            }), 500


    # ============================================================
    # Restore Wishlist Item
    # ============================================================

    @app.route("/api/wishlist/<wishlist_id>/restore", methods=["PUT"])
    def restore_wishlist(wishlist_id):
        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = restore_wishlist_item(
                wishlist_id=wishlist_id,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to restore wishlist item",
                "error": str(error)
            }), 500


    # ============================================================
    # Update Wishlist Settings
    # ============================================================

    @app.route("/api/wishlist/<wishlist_id>", methods=["PUT"])
    def update_wishlist(wishlist_id):
        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = update_wishlist_item(
                wishlist_id=wishlist_id,
                user_id=user_id,
                priority=data.get("priority"),
                notify_on_price_drop=data.get(
                    "notify_on_price_drop"
                ),
                notify_on_stock_available=data.get(
                    "notify_on_stock_available"
                ),
                notes=data.get("notes")
            )

            return jsonify(result), (
                200 if result.get("success") else 400
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update wishlist",
                "error": str(error)
            }), 500


    # ============================================================
    # Refresh Wishlist Prices
    # ============================================================

    @app.route(
        "/api/wishlist/user/<user_id>/refresh-prices",
        methods=["POST"]
    )
    def refresh_prices(user_id):
        try:
            result = refresh_wishlist_prices(
                user_id=user_id
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to refresh wishlist prices",
                "error": str(error)
            }), 500


    # ============================================================
    # Get Price Drop Items
    # ============================================================

    @app.route(
        "/api/wishlist/user/<user_id>/price-drops",
        methods=["GET"]
    )
    def price_drop_items(user_id):
        try:
            try:
                limit = int(
                    request.args.get(
                        "limit",
                        20
                    )
                )
                offset = int(
                    request.args.get(
                        "offset",
                        0
                    )
                )
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "limit and offset must be integers"
                }), 400

            limit = max(1, min(limit, 100))
            offset = max(0, offset)

            result = get_price_drop_items(
                user_id=user_id,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get price drop items",
                "error": str(error)
            }), 500


    # ============================================================
    # Get Out Of Stock Items
    # ============================================================

    @app.route(
        "/api/wishlist/user/<user_id>/out-of-stock",
        methods=["GET"]
    )
    def out_of_stock_items(user_id):
        try:
            try:
                limit = int(
                    request.args.get(
                        "limit",
                        20
                    )
                )
                offset = int(
                    request.args.get(
                        "offset",
                        0
                    )
                )
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "limit and offset must be integers"
                }), 400

            limit = max(1, min(limit, 100))
            offset = max(0, offset)

            result = get_out_of_stock_items(
                user_id=user_id,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get out of stock wishlist items",
                "error": str(error)
            }), 500


    # ============================================================
    # Clear Wishlist
    # ============================================================

    @app.route(
        "/api/wishlist/user/<user_id>/clear",
        methods=["DELETE"]
    )
    def clear_user_wishlist(user_id):
        try:
            result = clear_wishlist(
                user_id=user_id
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to clear wishlist",
                "error": str(error)
            }), 500
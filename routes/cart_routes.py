from flask import request, jsonify

from operations.cart_operation import (
    add_to_cart,
    get_cart_item,
    get_user_cart,
    update_cart_quantity,
    remove_from_cart,
    save_for_later,
    move_to_cart,
    select_cart_item,
    select_all_cart_items,
    validate_cart,
    clear_cart,
    restore_cart_item
)


def cart_routes(app):

    # ============================================================
    # Add Product To Cart
    # ============================================================

    @app.route("/api/cart", methods=["POST"])
    def add_cart():
        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")
            product_id = data.get("product_id")
            quantity = data.get("quantity", 1)
            variant_id = data.get("variant_id")

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

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": "quantity must be an integer"
                }), 400

            result = add_to_cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                variant_id=variant_id
            )

            return jsonify(result), (
                201 if result.get("success") else 400
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to add product to cart",
                "error": str(error)
            }), 500


    # ============================================================
    # Get User Cart
    # ============================================================

    @app.route("/api/cart/user/<user_id>", methods=["GET"])
    def user_cart(user_id):
        try:
            selected_only = (
                request.args.get(
                    "selected_only",
                    "false"
                ).lower() == "true"
            )

            include_removed = (
                request.args.get(
                    "include_removed",
                    "false"
                ).lower() == "true"
            )

            result = get_user_cart(
                user_id=user_id,
                selected_only=selected_only,
                include_removed=include_removed
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get user cart",
                "error": str(error)
            }), 500


    # ============================================================
    # Get Single Cart Item
    # ============================================================

    @app.route("/api/cart/<cart_id>", methods=["GET"])
    def get_cart(cart_id):
        try:
            user_id = request.args.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = get_cart_item(
                cart_id=cart_id,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to get cart item",
                "error": str(error)
            }), 500


    # ============================================================
    # Update Cart Quantity
    # ============================================================

    @app.route("/api/cart/<cart_id>/quantity", methods=["PUT"])
    def update_quantity(cart_id):
        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")
            quantity = data.get("quantity")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            if quantity is None:
                return jsonify({
                    "success": False,
                    "message": "quantity is required"
                }), 400

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": "quantity must be an integer"
                }), 400

            result = update_cart_quantity(
                cart_id=cart_id,
                user_id=user_id,
                quantity=quantity
            )

            return jsonify(result), (
                200 if result.get("success") else 400
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update cart quantity",
                "error": str(error)
            }), 500


    # ============================================================
    # Remove Cart Item
    # ============================================================

    @app.route("/api/cart/<cart_id>", methods=["DELETE"])
    def remove_cart(cart_id):
        try:
            user_id = request.args.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = remove_from_cart(
                cart_id=cart_id,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to remove cart item",
                "error": str(error)
            }), 500


    # ============================================================
    # Save For Later
    # ============================================================

    @app.route("/api/cart/<cart_id>/save-for-later", methods=["PUT"])
    def cart_save_for_later(cart_id):
        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = save_for_later(
                cart_id=cart_id,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to save item for later",
                "error": str(error)
            }), 500


    # ============================================================
    # Move Saved Item Back To Cart
    # ============================================================

    @app.route("/api/cart/<cart_id>/move-to-cart", methods=["PUT"])
    def cart_move_to_cart(cart_id):
        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = move_to_cart(
                cart_id=cart_id,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to move item to cart",
                "error": str(error)
            }), 500


    # ============================================================
    # Select / Unselect Cart Item
    # ============================================================

    @app.route("/api/cart/<cart_id>/select", methods=["PUT"])
    def select_cart(cart_id):
        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")
            selected = data.get("selected", True)

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            if isinstance(selected, str):
                selected = selected.lower() == "true"

            result = select_cart_item(
                cart_id=cart_id,
                user_id=user_id,
                selected=selected
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update cart selection",
                "error": str(error)
            }), 500


    # ============================================================
    # Select / Unselect All Cart Items
    # ============================================================

    @app.route("/api/cart/user/<user_id>/select-all", methods=["PUT"])
    def select_all_cart(user_id):
        try:
            data = request.get_json(silent=True) or {}

            selected = data.get("selected", True)

            if isinstance(selected, str):
                selected = selected.lower() == "true"

            result = select_all_cart_items(
                user_id=user_id,
                selected=selected
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update cart selection",
                "error": str(error)
            }), 500


    # ============================================================
    # Validate Cart
    # ============================================================

    @app.route("/api/cart/user/<user_id>/validate", methods=["POST"])
    def cart_validate(user_id):
        try:
            selected_only = (
                request.args.get(
                    "selected_only",
                    "true"
                ).lower() == "true"
            )

            result = validate_cart(
                user_id=user_id,
                selected_only=selected_only
            )

            return jsonify(result), (
                200 if result.get("valid") else 400
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to validate cart",
                "error": str(error)
            }), 500


    # ============================================================
    # Clear Cart
    # ============================================================

    @app.route("/api/cart/user/<user_id>/clear", methods=["DELETE"])
    def cart_clear(user_id):
        try:
            selected_only = (
                request.args.get(
                    "selected_only",
                    "false"
                ).lower() == "true"
            )

            result = clear_cart(
                user_id=user_id,
                selected_only=selected_only
            )

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to clear cart",
                "error": str(error)
            }), 500


    # ============================================================
    # Restore Removed Cart Item
    # ============================================================

    @app.route("/api/cart/<cart_id>/restore", methods=["PUT"])
    def restore_cart(cart_id):
        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            result = restore_cart_item(
                cart_id=cart_id,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to restore cart item",
                "error": str(error)
            }), 500
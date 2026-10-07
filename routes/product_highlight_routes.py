from flask import jsonify, request

from operations.product_highlight_operation import (
    create_product_highlight,
    get_product_highlight_by_id,
    get_product_highlights,
    update_product_highlight,
    delete_product_highlight,
    update_product_highlight_status
)


def _to_bool(value, default=0):
    if value is None:
        return default

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return 1 if value else 0

    value = str(value).strip().lower()

    return 1 if value in (
        "1",
        "true",
        "yes",
        "on"
    ) else 0


def _to_int(value, default=0):
    if value is None or value == "":
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# Product Highlight Routes
# ============================================================

def product_highlight_routes(app):

    # ========================================================
    # Create Product Highlight
    # ========================================================

    @app.route(
        "/api/products/<product_id>/highlights",
        methods=["POST"]
    )
    def create_highlight_route(product_id):

        data = request.get_json(silent=True) or {}

        highlight_text = data.get("highlight_text")

        if not highlight_text:
            return jsonify({
                "success": False,
                "message": "highlight_text is required"
            }), 400

        result = create_product_highlight(
            product_id=product_id,
            highlight_text=highlight_text,
            variant_id=data.get("variant_id"),
            highlight_type=data.get(
                "highlight_type",
                "general"
            ),
            display_order=_to_int(
                data.get("display_order"),
                0
            ),
            is_featured=_to_bool(
                data.get("is_featured"),
                0
            ),
            is_active=_to_bool(
                data.get("is_active"),
                1
            )
        )

        if not result["success"]:

            if result["message"] in (
                "Product not found",
                "Variant not found for this product"
            ):
                return jsonify(result), 404

            return jsonify(result), 400

        return jsonify(result), 201

    # ========================================================
    # Get Product Highlights
    # ========================================================

    @app.route(
        "/api/products/<product_id>/highlights",
        methods=["GET"]
    )
    def get_highlights_route(product_id):

        variant_id = request.args.get(
            "variant_id"
        )

        include_inactive = _to_bool(
            request.args.get(
                "include_inactive"
            ),
            0
        )

        result = get_product_highlights(
            product_id=product_id,
            variant_id=variant_id,
            include_inactive=include_inactive
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200

    # ========================================================
    # Get Highlight By ID
    # ========================================================

    @app.route(
        "/api/products/highlights/<highlight_id>",
        methods=["GET"]
    )
    def get_highlight_by_id_route(highlight_id):

        result = get_product_highlight_by_id(
            highlight_id
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200

    # ========================================================
    # Update Product Highlight
    # ========================================================

    @app.route(
        "/api/products/highlights/<highlight_id>",
        methods=["PUT"]
    )
    def update_highlight_route(highlight_id):

        data = request.get_json(silent=True) or {}

        fields = {}

        allowed_fields = (
            "highlight_text",
            "variant_id",
            "highlight_type",
            "display_order",
            "is_featured",
            "is_active",
            "status"
        )

        for field in allowed_fields:

            if field not in data:
                continue

            value = data[field]

            if field in (
                "is_featured",
                "is_active"
            ):
                value = _to_bool(value)

            elif field == "display_order":
                value = _to_int(value)

            fields[field] = value

        result = update_product_highlight(
            highlight_id,
            **fields
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 200

    # ========================================================
    # Delete Product Highlight
    # ========================================================

    @app.route(
        "/api/products/highlights/<highlight_id>",
        methods=["DELETE"]
    )
    def delete_highlight_route(highlight_id):

        result = delete_product_highlight(
            highlight_id
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200

    # ========================================================
    # Update Highlight Status
    # ========================================================

    @app.route(
        "/api/products/highlights/<highlight_id>/status",
        methods=["PUT"]
    )
    def update_highlight_status_route(highlight_id):

        data = request.get_json(silent=True) or {}

        status = data.get("status")

        if not status:
            return jsonify({
                "success": False,
                "message": "status is required"
            }), 400

        result = update_product_highlight_status(
            highlight_id,
            status
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 200
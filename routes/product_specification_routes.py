from flask import jsonify, request

from operations.product_specification_operation import (
    create_product_specification,
    get_product_specification_by_id,
    get_product_specifications,
    update_product_specification,
    delete_product_specification,
    update_product_specification_status
)


def _to_bool(value, default=0):
    if value is None:
        return default

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return 1 if value else 0

    value = str(value).strip().lower()

    if value in ("1", "true", "yes", "on"):
        return 1

    if value in ("0", "false", "no", "off"):
        return 0

    return default


def _to_int(value, default=0):
    if value is None or value == "":
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def product_specification_routes(app):

    # -----------------------------------------
    # CREATE SPECIFICATION
    # -----------------------------------------
    @app.route(
        "/api/products/<product_id>/specifications",
        methods=["POST"]
    )
    def create_specification(product_id):

        data = request.get_json(silent=True) or {}

        result = create_product_specification(
            product_id=product_id,
            specification_name=data.get("specification_name"),
            specification_value=data.get("specification_value"),
            specification_group=data.get("specification_group"),
            specification_unit=data.get("specification_unit"),
            variant_id=data.get("variant_id"),
            display_order=_to_int(
                data.get("display_order"),
                0
            ),
            is_highlighted=_to_bool(
                data.get("is_highlighted"),
                0
            ),
            is_searchable=_to_bool(
                data.get("is_searchable"),
                0
            )
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 201


    # -----------------------------------------
    # GET ALL PRODUCT SPECIFICATIONS
    # -----------------------------------------
    @app.route(
        "/api/products/<product_id>/specifications",
        methods=["GET"]
    )
    def get_specifications(product_id):

        variant_id = request.args.get("variant_id")

        include_inactive = _to_bool(
            request.args.get("include_inactive"),
            0
        )

        result = get_product_specifications(
            product_id=product_id,
            variant_id=variant_id,
            include_inactive=bool(include_inactive)
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # -----------------------------------------
    # GET SPECIFICATION BY ID
    # -----------------------------------------
    @app.route(
        "/api/products/specifications/<specification_id>",
        methods=["GET"]
    )
    def get_specification(specification_id):

        result = get_product_specification_by_id(
            specification_id
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # -----------------------------------------
    # UPDATE SPECIFICATION
    # -----------------------------------------
    @app.route(
        "/api/products/specifications/<specification_id>",
        methods=["PUT"]
    )
    def update_specification(specification_id):

        data = request.get_json(silent=True) or {}

        result = update_product_specification(
            specification_id=specification_id,
            specification_name=data.get("specification_name"),
            specification_value=data.get("specification_value"),
            specification_group=data.get("specification_group"),
            specification_unit=data.get("specification_unit"),
            variant_id=data.get("variant_id"),
            display_order=(
                _to_int(data.get("display_order"))
                if "display_order" in data
                else None
            ),
            is_highlighted=(
                _to_bool(data.get("is_highlighted"))
                if "is_highlighted" in data
                else None
            ),
            is_searchable=(
                _to_bool(data.get("is_searchable"))
                if "is_searchable" in data
                else None
            )
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 200


    # -----------------------------------------
    # DELETE SPECIFICATION
    # -----------------------------------------
    @app.route(
        "/api/products/specifications/<specification_id>",
        methods=["DELETE"]
    )
    def delete_specification(specification_id):

        result = delete_product_specification(
            specification_id
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # -----------------------------------------
    # UPDATE SPECIFICATION STATUS
    # -----------------------------------------
    @app.route(
        "/api/products/specifications/<specification_id>/status",
        methods=["PUT"]
    )
    def update_specification_status(specification_id):

        data = request.get_json(silent=True) or {}

        status = data.get("status")

        result = update_product_specification_status(
            specification_id,
            status
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 200
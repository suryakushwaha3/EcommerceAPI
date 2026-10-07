from flask import jsonify, request

from operations.product_variant_operation import (
    create_product_variant,
    get_product_variant_by_id,
    get_product_variants,
    update_product_variant,
    delete_product_variant,
    update_product_variant_status
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


def _to_float(value, default=0):
    if value is None or value == "":
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def product_variant_routes(app):

    # =========================================
    # CREATE VARIANT
    # =========================================
    @app.route(
        "/api/products/<product_id>/variants",
        methods=["POST"]
    )
    def create_variant(product_id):

        data = request.get_json(silent=True) or {}

        result = create_product_variant(
            product_id=product_id,
            variant_name=data.get("variant_name"),
            variant_code=data.get("variant_code"),
            sku=data.get("sku"),
            barcode=data.get("barcode"),
            attributes=data.get("attributes"),
            mrp=_to_float(data.get("mrp"), 0),
            selling_price=_to_float(
                data.get("selling_price"),
                0
            ),
            discount_type=data.get(
                "discount_type",
                "percentage"
            ),
            discount_value=_to_float(
                data.get("discount_value"),
                0
            ),
            tax_percentage=_to_float(
                data.get("tax_percentage"),
                0
            ),
            currency=data.get(
                "currency",
                "INR"
            ),
            stock_quantity=_to_int(
                data.get("stock_quantity"),
                0
            ),
            low_stock_threshold=_to_int(
                data.get("low_stock_threshold"),
                5
            ),
            stock_status=data.get(
                "stock_status",
                "in_stock"
            ),
            reserved_quantity=_to_int(
                data.get("reserved_quantity"),
                0
            ),
            sold_quantity=_to_int(
                data.get("sold_quantity"),
                0
            ),
            weight=(
                _to_float(data.get("weight"))
                if data.get("weight") is not None
                else None
            ),
            weight_unit=data.get(
                "weight_unit",
                "kg"
            ),
            length=(
                _to_float(data.get("length"))
                if data.get("length") is not None
                else None
            ),
            width=(
                _to_float(data.get("width"))
                if data.get("width") is not None
                else None
            ),
            height=(
                _to_float(data.get("height"))
                if data.get("height") is not None
                else None
            ),
            dimension_unit=data.get(
                "dimension_unit",
                "cm"
            ),
            is_default=_to_bool(
                data.get("is_default"),
                0
            ),
            is_active=_to_bool(
                data.get("is_active"),
                1
            ),
            sort_order=_to_int(
                data.get("sort_order"),
                0
            )
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 201


    # =========================================
    # GET ALL VARIANTS
    # =========================================
    @app.route(
        "/api/products/<product_id>/variants",
        methods=["GET"]
    )
    def get_variants(product_id):

        include_inactive = _to_bool(
            request.args.get("include_inactive"),
            0
        )

        result = get_product_variants(
            product_id,
            bool(include_inactive)
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # =========================================
    # GET VARIANT BY ID
    # =========================================
    @app.route(
        "/api/products/variants/<variant_id>",
        methods=["GET"]
    )
    def get_variant(variant_id):

        result = get_product_variant_by_id(
            variant_id
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # =========================================
    # UPDATE VARIANT
    # =========================================
    @app.route(
        "/api/products/variants/<variant_id>",
        methods=["PUT"]
    )
    def update_variant(variant_id):

        data = request.get_json(silent=True) or {}

        result = update_product_variant(
            variant_id=variant_id,
            variant_name=data.get("variant_name"),
            variant_code=(
                data.get("variant_code")
                if "variant_code" in data
                else None
            ),
            sku=(
                data.get("sku")
                if "sku" in data
                else None
            ),
            barcode=(
                data.get("barcode")
                if "barcode" in data
                else None
            ),
            attributes=(
                data.get("attributes")
                if "attributes" in data
                else None
            ),
            mrp=(
                _to_float(data.get("mrp"))
                if "mrp" in data
                else None
            ),
            selling_price=(
                _to_float(data.get("selling_price"))
                if "selling_price" in data
                else None
            ),
            discount_type=(
                data.get("discount_type")
                if "discount_type" in data
                else None
            ),
            discount_value=(
                _to_float(data.get("discount_value"))
                if "discount_value" in data
                else None
            ),
            tax_percentage=(
                _to_float(data.get("tax_percentage"))
                if "tax_percentage" in data
                else None
            ),
            currency=(
                data.get("currency")
                if "currency" in data
                else None
            ),
            stock_quantity=(
                _to_int(data.get("stock_quantity"))
                if "stock_quantity" in data
                else None
            ),
            low_stock_threshold=(
                _to_int(
                    data.get("low_stock_threshold")
                )
                if "low_stock_threshold" in data
                else None
            ),
            stock_status=(
                data.get("stock_status")
                if "stock_status" in data
                else None
            ),
            reserved_quantity=(
                _to_int(
                    data.get("reserved_quantity")
                )
                if "reserved_quantity" in data
                else None
            ),
            sold_quantity=(
                _to_int(data.get("sold_quantity"))
                if "sold_quantity" in data
                else None
            ),
            weight=(
                _to_float(data.get("weight"))
                if "weight" in data
                else None
            ),
            weight_unit=(
                data.get("weight_unit")
                if "weight_unit" in data
                else None
            ),
            length=(
                _to_float(data.get("length"))
                if "length" in data
                else None
            ),
            width=(
                _to_float(data.get("width"))
                if "width" in data
                else None
            ),
            height=(
                _to_float(data.get("height"))
                if "height" in data
                else None
            ),
            dimension_unit=(
                data.get("dimension_unit")
                if "dimension_unit" in data
                else None
            ),
            is_default=(
                _to_bool(data.get("is_default"))
                if "is_default" in data
                else None
            ),
            is_active=(
                _to_bool(data.get("is_active"))
                if "is_active" in data
                else None
            ),
            sort_order=(
                _to_int(data.get("sort_order"))
                if "sort_order" in data
                else None
            )
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 200


    # =========================================
    # DELETE VARIANT
    # =========================================
    @app.route(
        "/api/products/variants/<variant_id>",
        methods=["DELETE"]
    )
    def delete_variant(variant_id):

        result = delete_product_variant(
            variant_id
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # =========================================
    # UPDATE VARIANT STATUS
    # =========================================
    @app.route(
        "/api/products/variants/<variant_id>/status",
        methods=["PUT"]
    )
    def update_variant_status(variant_id):

        data = request.get_json(silent=True) or {}

        result = update_product_variant_status(
            variant_id,
            data.get("status")
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 200
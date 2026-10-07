from flask import request, jsonify

from operations.coupon_operation import (
    create_coupon,
    get_coupon_by_id,
    get_coupon_by_code,
    get_coupons,
    validate_coupon,
    calculate_coupon_discount,
    increment_coupon_usage,
    activate_coupon,
    pause_coupon,
    update_coupon,
    update_coupon_status,
    delete_coupon,
    refresh_coupon_status
)


def coupon_routes(app):

    # ============================================================
    # CREATE COUPON
    # ============================================================

    @app.route("/api/coupons", methods=["POST"])
    def create_coupon_route():

        try:
            data = request.get_json(silent=True) or {}

            required_fields = [
                "coupon_code",
                "coupon_name",
                "start_at",
                "end_at"
            ]

            missing_fields = [
                field
                for field in required_fields
                if field not in data
                or data[field] in (None, "")
            ]

            if missing_fields:
                return jsonify({
                    "success": False,
                    "message": "Required fields are missing.",
                    "missing_fields": missing_fields
                }), 400

            coupon = create_coupon(
                coupon_code=data["coupon_code"],
                coupon_name=data["coupon_name"],
                start_at=data["start_at"],
                end_at=data["end_at"],
                discount_type=data.get(
                    "discount_type",
                    "percentage"
                ),
                discount_value=data.get(
                    "discount_value",
                    0
                ),
                description=data.get(
                    "description"
                ),
                maximum_discount=data.get(
                    "maximum_discount"
                ),
                minimum_order_amount=data.get(
                    "minimum_order_amount",
                    0
                ),
                maximum_order_amount=data.get(
                    "maximum_order_amount"
                ),
                minimum_quantity=data.get(
                    "minimum_quantity",
                    1
                ),
                maximum_quantity=data.get(
                    "maximum_quantity"
                ),
                applicable_to=data.get(
                    "applicable_to",
                    "all"
                ),
                target_id=data.get(
                    "target_id"
                ),
                user_id=data.get(
                    "user_id"
                ),
                usage_limit=data.get(
                    "usage_limit"
                ),
                usage_per_user=data.get(
                    "usage_per_user",
                    1
                ),
                is_first_order_only=data.get(
                    "is_first_order_only",
                    False
                ),
                is_stackable=data.get(
                    "is_stackable",
                    False
                ),
                priority=data.get(
                    "priority",
                    0
                ),
                created_by=data.get(
                    "created_by"
                ),
                status=data.get(
                    "status",
                    "scheduled"
                )
            )

            return jsonify({
                "success": True,
                "message": "Coupon created successfully.",
                "coupon": coupon
            }), 201

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to create coupon.",
                "error": str(e)
            }), 500


    # ============================================================
    # GET ALL COUPONS
    # ============================================================

    @app.route("/api/coupons", methods=["GET"])
    def get_coupons_route():

        try:
            status = request.args.get("status")
            discount_type = request.args.get(
                "discount_type"
            )
            applicable_to = request.args.get(
                "applicable_to"
            )

            is_active = request.args.get(
                "is_active"
            )

            if is_active is not None:
                is_active = is_active.lower() in (
                    "true",
                    "1",
                    "yes",
                    "on"
                )

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

            limit = max(
                1,
                min(limit, 100)
            )

            offset = max(
                0,
                offset
            )

            coupons = get_coupons(
                status=status,
                discount_type=discount_type,
                applicable_to=applicable_to,
                is_active=is_active,
                limit=limit,
                offset=offset
            )

            return jsonify({
                "success": True,
                "count": len(coupons),
                "limit": limit,
                "offset": offset,
                "coupons": coupons
            }), 200

        except ValueError:
            return jsonify({
                "success": False,
                "message": "Invalid pagination or query parameter."
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to fetch coupons.",
                "error": str(e)
            }), 500


    # ============================================================
    # GET COUPON BY CODE
    # ============================================================

    @app.route("/api/coupons/code/<coupon_code>", methods=["GET"])
    def get_coupon_by_code_route(coupon_code):

        try:
            coupon = get_coupon_by_code(
                coupon_code
            )

            if not coupon:
                return jsonify({
                    "success": False,
                    "message": "Coupon not found."
                }), 404

            return jsonify({
                "success": True,
                "coupon": coupon
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to fetch coupon.",
                "error": str(e)
            }), 500


    # ============================================================
    # VALIDATE COUPON
    # ============================================================

    @app.route("/api/coupons/validate", methods=["POST"])
    def validate_coupon_route():

        try:
            data = request.get_json(silent=True) or {}

            coupon_code = data.get(
                "coupon_code"
            )

            if not coupon_code:
                return jsonify({
                    "success": False,
                    "message": "Coupon code is required."
                }), 400

            result = validate_coupon(
                coupon_code=coupon_code,
                user_id=data.get(
                    "user_id"
                ),
                product_id=data.get(
                    "product_id"
                ),
                category_id=data.get(
                    "category_id"
                ),
                variant_id=data.get(
                    "variant_id"
                ),
                order_amount=data.get(
                    "order_amount",
                    0
                ),
                quantity=data.get(
                    "quantity",
                    1
                ),
                is_first_order=data.get(
                    "is_first_order",
                    False
                )
            )

            return jsonify({
                "success": True,
                **result
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to validate coupon.",
                "error": str(e)
            }), 500


    # ============================================================
    # CALCULATE COUPON DISCOUNT
    # ============================================================

    @app.route(
        "/api/coupons/calculate-discount",
        methods=["POST"]
    )
    def calculate_coupon_discount_route():

        try:
            data = request.get_json(silent=True) or {}

            coupon_code = data.get(
                "coupon_code"
            )

            if not coupon_code:
                return jsonify({
                    "success": False,
                    "message": "Coupon code is required."
                }), 400

            if data.get("order_amount") is None:
                return jsonify({
                    "success": False,
                    "message": "Order amount is required."
                }), 400

            result = calculate_coupon_discount(
                coupon_code=coupon_code,
                order_amount=data["order_amount"],
                quantity=data.get(
                    "quantity",
                    1
                ),
                user_id=data.get(
                    "user_id"
                ),
                product_id=data.get(
                    "product_id"
                ),
                category_id=data.get(
                    "category_id"
                ),
                variant_id=data.get(
                    "variant_id"
                ),
                is_first_order=data.get(
                    "is_first_order",
                    False
                )
            )

            return jsonify({
                "success": True,
                "message": "Coupon discount calculated successfully.",
                "discount": result
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to calculate coupon discount.",
                "error": str(e)
            }), 500


    # ============================================================
    # REFRESH COUPON STATUS
    # ============================================================

    @app.route(
        "/api/coupons/refresh-status",
        methods=["POST"]
    )
    def refresh_coupon_status_route():

        try:
            result = refresh_coupon_status()

            return jsonify(result), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to refresh coupon status.",
                "error": str(e)
            }), 500


    # ============================================================
    # GET COUPON BY ID
    # ============================================================

    @app.route(
        "/api/coupons/<coupon_id>",
        methods=["GET"]
    )
    def get_coupon_by_id_route(coupon_id):

        try:
            coupon = get_coupon_by_id(
                coupon_id
            )

            if not coupon:
                return jsonify({
                    "success": False,
                    "message": "Coupon not found."
                }), 404

            return jsonify({
                "success": True,
                "coupon": coupon
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to fetch coupon.",
                "error": str(e)
            }), 500


    # ============================================================
    # UPDATE COUPON
    # ============================================================

    @app.route(
        "/api/coupons/<coupon_id>",
        methods=["PUT"]
    )
    def update_coupon_route(coupon_id):

        try:
            data = request.get_json(silent=True) or {}

            if not data:
                return jsonify({
                    "success": False,
                    "message": "No update data provided."
                }), 400

            coupon = update_coupon(
                coupon_id,
                **data
            )

            return jsonify({
                "success": True,
                "message": "Coupon updated successfully.",
                "coupon": coupon
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to update coupon.",
                "error": str(e)
            }), 500


    # ============================================================
    # ACTIVATE COUPON
    # ============================================================

    @app.route(
        "/api/coupons/<coupon_id>/activate",
        methods=["POST"]
    )
    def activate_coupon_route(coupon_id):

        try:
            coupon = activate_coupon(
                coupon_id
            )

            return jsonify({
                "success": True,
                "message": "Coupon activated successfully.",
                "coupon": coupon
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to activate coupon.",
                "error": str(e)
            }), 500


    # ============================================================
    # PAUSE COUPON
    # ============================================================

    @app.route(
        "/api/coupons/<coupon_id>/pause",
        methods=["POST"]
    )
    def pause_coupon_route(coupon_id):

        try:
            coupon = pause_coupon(
                coupon_id
            )

            return jsonify({
                "success": True,
                "message": "Coupon paused successfully.",
                "coupon": coupon
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to pause coupon.",
                "error": str(e)
            }), 500


    # ============================================================
    # UPDATE COUPON STATUS
    # ============================================================

    @app.route(
        "/api/coupons/<coupon_id>/status",
        methods=["PUT"]
    )
    def update_coupon_status_route(coupon_id):

        try:
            data = request.get_json(silent=True) or {}

            status = data.get(
                "status"
            )

            if not status:
                return jsonify({
                    "success": False,
                    "message": "Coupon status is required."
                }), 400

            coupon = update_coupon_status(
                coupon_id,
                status
            )

            return jsonify({
                "success": True,
                "message": "Coupon status updated successfully.",
                "coupon": coupon
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to update coupon status.",
                "error": str(e)
            }), 500


    # ============================================================
    # INCREMENT COUPON USAGE
    # ============================================================

    @app.route(
        "/api/coupons/<coupon_id>/usage",
        methods=["POST"]
    )
    def increment_coupon_usage_route(coupon_id):

        try:
            data = request.get_json(silent=True) or {}

            quantity = data.get(
                "quantity",
                1
            )

            coupon = increment_coupon_usage(
                coupon_id,
                quantity
            )

            return jsonify({
                "success": True,
                "message": "Coupon usage updated successfully.",
                "coupon": coupon
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to update coupon usage.",
                "error": str(e)
            }), 500


    # ============================================================
    # DELETE COUPON
    # ============================================================

    @app.route(
        "/api/coupons/<coupon_id>",
        methods=["DELETE"]
    )
    def delete_coupon_route(coupon_id):

        try:
            result = delete_coupon(
                coupon_id
            )

            return jsonify(result), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 404

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to delete coupon.",
                "error": str(e)
            }), 500
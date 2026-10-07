from flask import request, jsonify

from operations.offer_operation import (
    create_offer,
    get_offer_by_id,
    get_offer_by_code,
    get_offers,
    get_active_offers,
    update_offer,
    activate_offer,
    pause_offer,
    calculate_offer_discount,
    increment_offer_usage,
    update_offer_status,
    delete_offer,
    refresh_offer_status
)


def offer_routes(app):

    # =========================================================
    # CREATE OFFER
    # =========================================================

    @app.route("/api/offers", methods=["POST"])
    def create_offer_route():
        try:
            data = request.get_json(silent=True) or {}

            required_fields = [
                "offer_name",
                "start_at",
                "end_at"
            ]

            missing_fields = [
                field
                for field in required_fields
                if data.get(field) is None
            ]

            if missing_fields:
                return jsonify({
                    "success": False,
                    "message": "Required fields are missing.",
                    "missing_fields": missing_fields
                }), 400

            offer = create_offer(
                offer_name=data["offer_name"],
                start_at=data["start_at"],
                end_at=data["end_at"],
                offer_type=data.get(
                    "offer_type",
                    "percentage"
                ),
                discount_value=data.get(
                    "discount_value",
                    0
                ),
                description=data.get(
                    "description"
                ),
                offer_code=data.get(
                    "offer_code"
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
                priority=data.get(
                    "priority",
                    0
                ),
                is_stackable=data.get(
                    "is_stackable",
                    False
                ),
                is_featured=data.get(
                    "is_featured",
                    False
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
                "message": "Offer created successfully.",
                "data": offer
            }), 201

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to create offer.",
                "error": str(e)
            }), 500

    # =========================================================
    # GET ALL OFFERS
    # =========================================================

    @app.route("/api/offers", methods=["GET"])
    def get_offers_route():
        try:
            status = request.args.get("status")
            offer_type = request.args.get("offer_type")
            applicable_to = request.args.get("applicable_to")

            is_active = request.args.get("is_active")
            is_featured = request.args.get("is_featured")

            if is_active is not None:
                if is_active.lower() not in (
                    "true",
                    "false",
                    "1",
                    "0"
                ):
                    return jsonify({
                        "success": False,
                        "message": "is_active must be true or false."
                    }), 400

                is_active = is_active.lower() in (
                    "true",
                    "1"
                )

            if is_featured is not None:
                if is_featured.lower() not in (
                    "true",
                    "false",
                    "1",
                    "0"
                ):
                    return jsonify({
                        "success": False,
                        "message": "is_featured must be true or false."
                    }), 400

                is_featured = is_featured.lower() in (
                    "true",
                    "1"
                )

            try:
                limit = int(
                    request.args.get("limit", 50)
                )
                offset = int(
                    request.args.get("offset", 0)
                )
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "limit and offset must be integers."
                }), 400

            limit = max(1, min(limit, 100))
            offset = max(0, offset)

            offers = get_offers(
                status=status,
                offer_type=offer_type,
                applicable_to=applicable_to,
                is_active=is_active,
                is_featured=is_featured,
                limit=limit,
                offset=offset
            )

            return jsonify({
                "success": True,
                "count": len(offers),
                "limit": limit,
                "offset": offset,
                "data": offers
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to fetch offers.",
                "error": str(e)
            }), 500

    # =========================================================
    # GET ACTIVE OFFERS
    # =========================================================

    @app.route("/api/offers/active", methods=["GET"])
    def get_active_offers_route():
        try:
            user_id = request.args.get("user_id")
            product_id = request.args.get("product_id")
            category_id = request.args.get("category_id")
            variant_id = request.args.get("variant_id")

            try:
                order_amount = float(
                    request.args.get(
                        "order_amount",
                        0
                    )
                )

                quantity = int(
                    request.args.get(
                        "quantity",
                        1
                    )
                )

                limit = int(
                    request.args.get(
                        "limit",
                        20
                    )
                )

            except ValueError:
                return jsonify({
                    "success": False,
                    "message": (
                        "order_amount, quantity and limit "
                        "must be valid numbers."
                    )
                }), 400

            if order_amount < 0:
                return jsonify({
                    "success": False,
                    "message": "order_amount cannot be negative."
                }), 400

            if quantity < 1:
                return jsonify({
                    "success": False,
                    "message": "quantity must be at least 1."
                }), 400

            limit = max(1, min(limit, 100))

            offers = get_active_offers(
                user_id=user_id,
                product_id=product_id,
                category_id=category_id,
                variant_id=variant_id,
                order_amount=order_amount,
                quantity=quantity,
                limit=limit
            )

            return jsonify({
                "success": True,
                "count": len(offers),
                "data": offers
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to fetch active offers.",
                "error": str(e)
            }), 500

    # =========================================================
    # GET OFFER BY CODE
    # =========================================================

    @app.route(
        "/api/offers/code/<offer_code>",
        methods=["GET"]
    )
    def get_offer_by_code_route(offer_code):
        try:
            offer = get_offer_by_code(
                offer_code
            )

            if not offer:
                return jsonify({
                    "success": False,
                    "message": "Offer not found."
                }), 404

            return jsonify({
                "success": True,
                "data": offer
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to fetch offer.",
                "error": str(e)
            }), 500

    # =========================================================
    # REFRESH OFFER STATUS
    # =========================================================

    @app.route(
        "/api/offers/refresh-status",
        methods=["POST"]
    )
    def refresh_offer_status_route():
        try:
            result = refresh_offer_status()

            return jsonify(result), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to refresh offer statuses.",
                "error": str(e)
            }), 500

    # =========================================================
    # GET OFFER BY ID
    # =========================================================

    @app.route(
        "/api/offers/<offer_id>",
        methods=["GET"]
    )
    def get_offer_route(offer_id):
        try:
            offer = get_offer_by_id(
                offer_id
            )

            if not offer:
                return jsonify({
                    "success": False,
                    "message": "Offer not found."
                }), 404

            return jsonify({
                "success": True,
                "data": offer
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to fetch offer.",
                "error": str(e)
            }), 500

    # =========================================================
    # UPDATE OFFER
    # =========================================================

    @app.route(
        "/api/offers/<offer_id>",
        methods=["PUT"]
    )
    def update_offer_route(offer_id):
        try:
            data = request.get_json(silent=True) or {}

            if not data:
                return jsonify({
                    "success": False,
                    "message": "No update data provided."
                }), 400

            offer = update_offer(
                offer_id,
                **data
            )

            return jsonify({
                "success": True,
                "message": "Offer updated successfully.",
                "data": offer
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to update offer.",
                "error": str(e)
            }), 500

    # =========================================================
    # ACTIVATE OFFER
    # =========================================================

    @app.route(
        "/api/offers/<offer_id>/activate",
        methods=["POST"]
    )
    def activate_offer_route(offer_id):
        try:
            offer = activate_offer(
                offer_id
            )

            return jsonify({
                "success": True,
                "message": "Offer activated successfully.",
                "data": offer
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to activate offer.",
                "error": str(e)
            }), 500

    # =========================================================
    # PAUSE OFFER
    # =========================================================

    @app.route(
        "/api/offers/<offer_id>/pause",
        methods=["POST"]
    )
    def pause_offer_route(offer_id):
        try:
            offer = pause_offer(
                offer_id
            )

            return jsonify({
                "success": True,
                "message": "Offer paused successfully.",
                "data": offer
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to pause offer.",
                "error": str(e)
            }), 500

    # =========================================================
    # CALCULATE OFFER DISCOUNT
    # =========================================================

    @app.route(
        "/api/offers/<offer_id>/calculate",
        methods=["POST"]
    )
    def calculate_offer_discount_route(offer_id):
        try:
            data = request.get_json(silent=True) or {}

            if data.get("order_amount") is None:
                return jsonify({
                    "success": False,
                    "message": "order_amount is required."
                }), 400

            try:
                order_amount = float(
                    data["order_amount"]
                )

                quantity = int(
                    data.get(
                        "quantity",
                        1
                    )
                )

            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": (
                        "order_amount must be a valid number "
                        "and quantity must be an integer."
                    )
                }), 400

            if order_amount < 0:
                return jsonify({
                    "success": False,
                    "message": "order_amount cannot be negative."
                }), 400

            if quantity < 1:
                return jsonify({
                    "success": False,
                    "message": "quantity must be at least 1."
                }), 400

            result = calculate_offer_discount(
                offer_id=offer_id,
                order_amount=order_amount,
                quantity=quantity
            )

            return jsonify({
                "success": True,
                "data": result
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to calculate offer discount.",
                "error": str(e)
            }), 500

    # =========================================================
    # INCREMENT OFFER USAGE
    # =========================================================

    @app.route(
        "/api/offers/<offer_id>/usage",
        methods=["POST"]
    )
    def increment_offer_usage_route(offer_id):
        try:
            data = request.get_json(silent=True) or {}

            try:
                quantity = int(
                    data.get(
                        "quantity",
                        1
                    )
                )
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": "quantity must be an integer."
                }), 400

            if quantity < 1:
                return jsonify({
                    "success": False,
                    "message": "quantity must be greater than zero."
                }), 400

            offer = increment_offer_usage(
                offer_id=offer_id,
                quantity=quantity
            )

            return jsonify({
                "success": True,
                "message": "Offer usage updated successfully.",
                "data": offer
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to update offer usage.",
                "error": str(e)
            }), 500

    # =========================================================
    # UPDATE OFFER STATUS
    # =========================================================

    @app.route(
        "/api/offers/<offer_id>/status",
        methods=["PUT"]
    )
    def update_offer_status_route(offer_id):
        try:
            data = request.get_json(silent=True) or {}

            status = data.get("status")

            if not status:
                return jsonify({
                    "success": False,
                    "message": "status is required."
                }), 400

            offer = update_offer_status(
                offer_id=offer_id,
                status=status
            )

            return jsonify({
                "success": True,
                "message": "Offer status updated successfully.",
                "data": offer
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to update offer status.",
                "error": str(e)
            }), 500

    # =========================================================
    # DELETE OFFER
    # =========================================================

    @app.route(
        "/api/offers/<offer_id>",
        methods=["DELETE"]
    )
    def delete_offer_route(offer_id):
        try:
            result = delete_offer(
                offer_id
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
                "message": "Failed to delete offer.",
                "error": str(e)
            }), 500
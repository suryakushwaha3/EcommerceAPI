from flask import request, jsonify

from operations.order_operation import (
    create_order,
    get_order_by_id,
    get_order_by_number,
    get_user_orders,
    get_orders,
    update_order_status,
    confirm_order,
    process_order,
    pack_order,
    ship_order,
    deliver_order,
    cancel_order,
    request_return,
    update_refund_amount,
    update_tracking,
    delete_order
)


def order_routes(app):

    # ============================================================
    # Internal Helpers
    # ============================================================

    def _json_body():
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return {}

        return data

    def _safe_string(value, field_name, max_length=500):
        if value is None:
            return None

        if not isinstance(value, str):
            return None

        value = value.strip()

        if not value:
            return None

        if len(value) > max_length:
            return None

        return value

    def _safe_positive_int(value, default=None, maximum=None):
        try:
            value = int(value)
        except (TypeError, ValueError):
            return default

        if value < 1:
            return default

        if maximum is not None:
            value = min(value, maximum)

        return value

    def _safe_non_negative_int(value, default=None, maximum=None):
        try:
            value = int(value)
        except (TypeError, ValueError):
            return default

        if value < 0:
            return default

        if maximum is not None:
            value = min(value, maximum)

        return value

    def _safe_float(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None

        if value != value:
            return None

        if value in (float("inf"), float("-inf")):
            return None

        return value

    def _server_error(message):
        return jsonify({
            "success": False,
            "message": message
        }), 500

    def _result_status(result, success_code=200, error_code=400):
        return jsonify(result), (
            success_code
            if result.get("success")
            else error_code
        )

    # ============================================================
    # Create Order
    # ============================================================

    @app.route("/api/orders", methods=["POST"])
    def create_new_order():
        try:
            data = _json_body()

            required_fields = [
                "user_id",
                "items",
                "shipping_name",
                "shipping_phone",
                "shipping_address_line1",
                "shipping_city",
                "shipping_state",
                "shipping_pincode"
            ]

            missing_fields = [
                field
                for field in required_fields
                if data.get(field) is None
            ]

            if missing_fields:
                return jsonify({
                    "success": False,
                    "message": "Required fields are missing",
                    "missing_fields": missing_fields
                }), 400

            user_id = _safe_string(
                data.get("user_id"),
                "user_id",
                100
            )

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id must be a valid string"
                }), 400

            if not isinstance(data["items"], list) or not data["items"]:
                return jsonify({
                    "success": False,
                    "message": "items must be a non-empty list"
                }), 400

            if len(data["items"]) > 100:
                return jsonify({
                    "success": False,
                    "message": "Maximum 100 items are allowed in one order"
                }), 400

            shipping_name = _safe_string(
                data.get("shipping_name"),
                "shipping_name",
                150
            )

            shipping_phone = _safe_string(
                data.get("shipping_phone"),
                "shipping_phone",
                30
            )

            shipping_address_line1 = _safe_string(
                data.get("shipping_address_line1"),
                "shipping_address_line1",
                500
            )

            shipping_city = _safe_string(
                data.get("shipping_city"),
                "shipping_city",
                100
            )

            shipping_state = _safe_string(
                data.get("shipping_state"),
                "shipping_state",
                100
            )

            shipping_pincode = _safe_string(
                data.get("shipping_pincode"),
                "shipping_pincode",
                20
            )

            if not all([
                shipping_name,
                shipping_phone,
                shipping_address_line1,
                shipping_city,
                shipping_state,
                shipping_pincode
            ]):
                return jsonify({
                    "success": False,
                    "message": "Shipping details contain invalid values"
                }), 400

            shipping_email = data.get("shipping_email")

            if shipping_email is not None:
                shipping_email = _safe_string(
                    shipping_email,
                    "shipping_email",
                    254
                )

            shipping_address_line2 = data.get(
                "shipping_address_line2"
            )

            if shipping_address_line2 is not None:
                shipping_address_line2 = _safe_string(
                    shipping_address_line2,
                    "shipping_address_line2",
                    500
                )

            shipping_country = data.get(
                "shipping_country",
                "India"
            )

            shipping_country = _safe_string(
                shipping_country,
                "shipping_country",
                100
            ) or "India"

            billing_name = data.get("billing_name")
            billing_phone = data.get("billing_phone")
            billing_address_line1 = data.get(
                "billing_address_line1"
            )
            billing_address_line2 = data.get(
                "billing_address_line2"
            )
            billing_city = data.get("billing_city")
            billing_state = data.get("billing_state")
            billing_country = data.get("billing_country")
            billing_pincode = data.get("billing_pincode")

            if billing_name is not None:
                billing_name = _safe_string(
                    billing_name,
                    "billing_name",
                    150
                )

            if billing_phone is not None:
                billing_phone = _safe_string(
                    billing_phone,
                    "billing_phone",
                    30
                )

            if billing_address_line1 is not None:
                billing_address_line1 = _safe_string(
                    billing_address_line1,
                    "billing_address_line1",
                    500
                )

            if billing_address_line2 is not None:
                billing_address_line2 = _safe_string(
                    billing_address_line2,
                    "billing_address_line2",
                    500
                )

            if billing_city is not None:
                billing_city = _safe_string(
                    billing_city,
                    "billing_city",
                    100
                )

            if billing_state is not None:
                billing_state = _safe_string(
                    billing_state,
                    "billing_state",
                    100
                )

            if billing_country is not None:
                billing_country = _safe_string(
                    billing_country,
                    "billing_country",
                    100
                )

            if billing_pincode is not None:
                billing_pincode = _safe_string(
                    billing_pincode,
                    "billing_pincode",
                    20
                )

            same_as_shipping = data.get(
                "same_as_shipping",
                True
            )

            if not isinstance(same_as_shipping, bool):
                return jsonify({
                    "success": False,
                    "message": "same_as_shipping must be boolean"
                }), 400

            payment_method = data.get(
                "payment_method",
                "cod"
            )

            payment_method = _safe_string(
                payment_method,
                "payment_method",
                50
            )

            if not payment_method:
                return jsonify({
                    "success": False,
                    "message": "payment_method is invalid"
                }), 400

            coupon_id = data.get("coupon_id")
            offer_id = data.get("offer_id")

            if coupon_id is not None:
                coupon_id = _safe_string(
                    coupon_id,
                    "coupon_id",
                    100
                )

            if offer_id is not None:
                offer_id = _safe_string(
                    offer_id,
                    "offer_id",
                    100
                )

            customer_note = data.get("customer_note")
            internal_note = data.get("internal_note")

            if customer_note is not None:
                customer_note = _safe_string(
                    customer_note,
                    "customer_note",
                    1000
                )

            if internal_note is not None:
                internal_note = _safe_string(
                    internal_note,
                    "internal_note",
                    1000
                )

            result = create_order(
                user_id=user_id,
                items=data["items"],
                shipping_name=shipping_name,
                shipping_phone=shipping_phone,
                shipping_address_line1=shipping_address_line1,
                shipping_city=shipping_city,
                shipping_state=shipping_state,
                shipping_pincode=shipping_pincode,
                payment_method=payment_method,
                shipping_email=shipping_email,
                shipping_address_line2=shipping_address_line2,
                shipping_country=shipping_country,
                billing_name=billing_name,
                billing_phone=billing_phone,
                billing_address_line1=billing_address_line1,
                billing_address_line2=billing_address_line2,
                billing_city=billing_city,
                billing_state=billing_state,
                billing_country=billing_country,
                billing_pincode=billing_pincode,
                same_as_shipping=same_as_shipping,
                coupon_id=coupon_id,
                offer_id=offer_id,
                customer_note=customer_note,
                internal_note=internal_note,
                ip_address=request.remote_addr,
                user_agent=request.headers.get(
                    "User-Agent"
                )
            )

            return jsonify(result), (
                201 if result.get("success") else 400
            )

        except Exception:
            return _server_error(
                "Failed to create order"
            )

    # ============================================================
    # Get Order By ID
    # ============================================================

    @app.route("/api/orders/<order_id>", methods=["GET"])
    def get_order(order_id):
        try:
            order_id = _safe_string(
                order_id,
                "order_id",
                100
            )

            if not order_id:
                return jsonify({
                    "success": False,
                    "message": "Invalid order_id"
                }), 400

            user_id = request.args.get("user_id")

            if user_id is not None:
                user_id = _safe_string(
                    user_id,
                    "user_id",
                    100
                )

                if not user_id:
                    return jsonify({
                        "success": False,
                        "message": "Invalid user_id"
                    }), 400

            result = get_order_by_id(
                order_id=order_id,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception:
            return _server_error(
                "Failed to get order"
            )

    # ============================================================
    # Get Order By Order Number
    # ============================================================

    @app.route(
        "/api/orders/number/<order_number>",
        methods=["GET"]
    )
    def get_order_number(order_number):
        try:
            order_number = _safe_string(
                order_number,
                "order_number",
                100
            )

            if not order_number:
                return jsonify({
                    "success": False,
                    "message": "Invalid order_number"
                }), 400

            user_id = request.args.get("user_id")

            if user_id is not None:
                user_id = _safe_string(
                    user_id,
                    "user_id",
                    100
                )

                if not user_id:
                    return jsonify({
                        "success": False,
                        "message": "Invalid user_id"
                    }), 400

            result = get_order_by_number(
                order_number=order_number,
                user_id=user_id
            )

            return jsonify(result), (
                200 if result.get("success") else 404
            )

        except Exception:
            return _server_error(
                "Failed to get order"
            )

    # ============================================================
    # Get User Orders
    # ============================================================

    @app.route(
        "/api/orders/user/<user_id>",
        methods=["GET"]
    )
    def user_orders(user_id):
        try:
            user_id = _safe_string(
                user_id,
                "user_id",
                100
            )

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "Invalid user_id"
                }), 400

            order_status = request.args.get(
                "order_status"
            )

            payment_status = request.args.get(
                "payment_status"
            )

            if order_status is not None:
                order_status = _safe_string(
                    order_status,
                    "order_status",
                    50
                )

            if payment_status is not None:
                payment_status = _safe_string(
                    payment_status,
                    "payment_status",
                    50
                )

            raw_limit = request.args.get(
                "limit",
                20
            )

            raw_offset = request.args.get(
                "offset",
                0
            )

            try:
                limit = int(raw_limit)
                offset = int(raw_offset)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": (
                        "limit and offset "
                        "must be integers"
                    )
                }), 400

            if limit < 1 or limit > 100:
                return jsonify({
                    "success": False,
                    "message": "limit must be between 1 and 100"
                }), 400

            if offset < 0:
                return jsonify({
                    "success": False,
                    "message": "offset cannot be negative"
                }), 400

            result = get_user_orders(
                user_id=user_id,
                order_status=order_status,
                payment_status=payment_status,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception:
            return _server_error(
                "Failed to get user orders"
            )

    # ============================================================
    # Get All Orders
    # ============================================================

    @app.route("/api/orders", methods=["GET"])
    def all_orders():
        try:
            order_status = request.args.get(
                "order_status"
            )

            payment_status = request.args.get(
                "payment_status"
            )

            user_id = request.args.get(
                "user_id"
            )

            if order_status is not None:
                order_status = _safe_string(
                    order_status,
                    "order_status",
                    50
                )

            if payment_status is not None:
                payment_status = _safe_string(
                    payment_status,
                    "payment_status",
                    50
                )

            if user_id is not None:
                user_id = _safe_string(
                    user_id,
                    "user_id",
                    100
                )

                if not user_id:
                    return jsonify({
                        "success": False,
                        "message": "Invalid user_id"
                    }), 400

            raw_limit = request.args.get(
                "limit",
                50
            )

            raw_offset = request.args.get(
                "offset",
                0
            )

            try:
                limit = int(raw_limit)
                offset = int(raw_offset)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": (
                        "limit and offset "
                        "must be integers"
                    )
                }), 400

            if limit < 1 or limit > 100:
                return jsonify({
                    "success": False,
                    "message": "limit must be between 1 and 100"
                }), 400

            if offset < 0:
                return jsonify({
                    "success": False,
                    "message": "offset cannot be negative"
                }), 400

            result = get_orders(
                order_status=order_status,
                payment_status=payment_status,
                user_id=user_id,
                limit=limit,
                offset=offset
            )

            return jsonify(result), 200

        except Exception:
            return _server_error(
                "Failed to get orders"
            )

    # ============================================================
    # Update Order Status
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/status",
        methods=["PUT"]
    )
    def change_order_status(order_id):
        try:
            data = _json_body()

            order_status = _safe_string(
                data.get("order_status"),
                "order_status",
                50
            )

            if not order_status:
                return jsonify({
                    "success": False,
                    "message": "order_status is required"
                }), 400

            result = update_order_status(
                order_id=order_id,
                order_status=order_status
            )

            return _result_status(
                result,
                200,
                400
            )

        except Exception:
            return _server_error(
                "Failed to update order status"
            )

    # ============================================================
    # Confirm Order
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/confirm",
        methods=["PUT"]
    )
    def confirm_new_order(order_id):
        try:
            result = confirm_order(
                order_id
            )

            return _result_status(
                result,
                200,
                400
            )

        except Exception:
            return _server_error(
                "Failed to confirm order"
            )

    # ============================================================
    # Process Order
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/process",
        methods=["PUT"]
    )
    def process_new_order(order_id):
        try:
            result = process_order(
                order_id
            )

            return _result_status(
                result,
                200,
                400
            )

        except Exception:
            return _server_error(
                "Failed to process order"
            )

    # ============================================================
    # Pack Order
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/pack",
        methods=["PUT"]
    )
    def pack_new_order(order_id):
        try:
            result = pack_order(
                order_id
            )

            return _result_status(
                result,
                200,
                400
            )

        except Exception:
            return _server_error(
                "Failed to pack order"
            )

    # ============================================================
    # Ship Order
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/ship",
        methods=["PUT"]
    )
    def ship_new_order(order_id):
        try:
            data = _json_body()

            courier_name = data.get(
                "courier_name"
            )

            tracking_number = data.get(
                "tracking_number"
            )

            tracking_url = data.get(
                "tracking_url"
            )

            estimated_delivery_date = data.get(
                "estimated_delivery_date"
            )

            if courier_name is not None:
                courier_name = _safe_string(
                    courier_name,
                    "courier_name",
                    150
                )

            if tracking_number is not None:
                tracking_number = _safe_string(
                    tracking_number,
                    "tracking_number",
                    150
                )

            if tracking_url is not None:
                tracking_url = _safe_string(
                    tracking_url,
                    "tracking_url",
                    500
                )

            if estimated_delivery_date is not None:
                estimated_delivery_date = _safe_string(
                    estimated_delivery_date,
                    "estimated_delivery_date",
                    50
                )

            result = ship_order(
                order_id=order_id,
                courier_name=courier_name,
                tracking_number=tracking_number,
                tracking_url=tracking_url,
                estimated_delivery_date=estimated_delivery_date
            )

            return _result_status(
                result,
                200,
                400
            )

        except Exception:
            return _server_error(
                "Failed to ship order"
            )

    # ============================================================
    # Deliver Order
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/deliver",
        methods=["PUT"]
    )
    def deliver_new_order(order_id):
        try:
            result = deliver_order(
                order_id
            )

            return _result_status(
                result,
                200,
                400
            )

        except Exception:
            return _server_error(
                "Failed to deliver order"
            )

    # ============================================================
    # Cancel Order
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/cancel",
        methods=["PUT"]
    )
    def cancel_new_order(order_id):
        try:
            data = _json_body()

            user_id = data.get(
                "user_id"
            )

            reason = data.get(
                "reason"
            )

            if user_id is not None:
                user_id = _safe_string(
                    user_id,
                    "user_id",
                    100
                )

            if reason is not None:
                reason = _safe_string(
                    reason,
                    "reason",
                    500
                )

            result = cancel_order(
                order_id=order_id,
                user_id=user_id,
                reason=reason
            )

            return _result_status(
                result,
                200,
                400
            )

        except Exception:
            return _server_error(
                "Failed to cancel order"
            )

    # ============================================================
    # Request Return
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/return",
        methods=["POST"]
    )
    def return_order(order_id):
        try:
            data = _json_body()

            user_id = data.get(
                "user_id"
            )

            reason = data.get(
                "reason"
            )

            user_id = _safe_string(
                user_id,
                "user_id",
                100
            )

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "user_id is required"
                }), 400

            if reason is not None:
                reason = _safe_string(
                    reason,
                    "reason",
                    500
                )

            result = request_return(
                order_id=order_id,
                user_id=user_id,
                reason=reason
            )

            return _result_status(
                result,
                200,
                400
            )

        except Exception:
            return _server_error(
                "Failed to request return"
            )

    # ============================================================
    # Update Refund Amount
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/refund",
        methods=["PUT"]
    )
    def update_order_refund(order_id):
        try:
            data = _json_body()

            refund_amount = data.get(
                "refund_amount"
            )

            if refund_amount is None:
                return jsonify({
                    "success": False,
                    "message": "refund_amount is required"
                }), 400

            refund_amount = _safe_float(
                refund_amount
            )

            if refund_amount is None:
                return jsonify({
                    "success": False,
                    "message": (
                        "refund_amount must be "
                        "a valid number"
                    )
                }), 400

            if refund_amount < 0:
                return jsonify({
                    "success": False,
                    "message": (
                        "refund_amount cannot "
                        "be negative"
                    )
                }), 400

            result = update_refund_amount(
                order_id=order_id,
                refund_amount=refund_amount
            )

            return _result_status(
                result,
                200,
                400
            )

        except Exception:
            return _server_error(
                "Failed to update refund amount"
            )

    # ============================================================
    # Update Tracking
    # ============================================================

    @app.route(
        "/api/orders/<order_id>/tracking",
        methods=["PUT"]
    )
    def update_order_tracking(order_id):
        try:
            data = _json_body()

            courier_name = data.get(
                "courier_name"
            )

            tracking_number = data.get(
                "tracking_number"
            )

            tracking_url = data.get(
                "tracking_url"
            )

            estimated_delivery_date = data.get(
                "estimated_delivery_date"
            )

            if courier_name is not None:
                courier_name = _safe_string(
                    courier_name,
                    "courier_name",
                    150
                )

            if tracking_number is not None:
                tracking_number = _safe_string(
                    tracking_number,
                    "tracking_number",
                    150
                )

            if tracking_url is not None:
                tracking_url = _safe_string(
                    tracking_url,
                    "tracking_url",
                    500
                )

            if estimated_delivery_date is not None:
                estimated_delivery_date = _safe_string(
                    estimated_delivery_date,
                    "estimated_delivery_date",
                    50
                )

            result = update_tracking(
                order_id=order_id,
                courier_name=courier_name,
                tracking_number=tracking_number,
                tracking_url=tracking_url,
                estimated_delivery_date=estimated_delivery_date
            )

            return _result_status(
                result,
                200,
                404
            )

        except Exception:
            return _server_error(
                "Failed to update tracking"
            )

    # ============================================================
    # Delete Order
    # ============================================================

    @app.route(
        "/api/orders/<order_id>",
        methods=["DELETE"]
    )
    def delete_order_route(order_id):
        try:
            order_id = _safe_string(
                order_id,
                "order_id",
                100
            )

            if not order_id:
                return jsonify({
                    "success": False,
                    "message": "Invalid order_id"
                }), 400

            result = delete_order(
                order_id
            )

            return _result_status(
                result,
                200,
                404
            )

        except Exception:
            return _server_error(
                "Failed to delete order"
            )
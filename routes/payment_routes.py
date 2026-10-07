from flask import request, jsonify

from operations.payment_operation import (
    create_payment,
    get_payment_by_id,
    get_payment_by_transaction_id,
    get_payment_by_order_id,
    get_user_payments,
    get_payments,
    update_payment_status,
    process_payment,
    authorize_payment,
    capture_payment,
    fail_payment,
    cancel_payment,
    create_refund,
    verify_payment,
    process_webhook,
    delete_payment
)


# =========================================================
# HELPERS
# =========================================================

def _safe_error_response(message, status_code=400):
    return jsonify({
        "success": False,
        "message": message
    }), status_code


def _validate_json_body():
    if not request.is_json:
        return None, _safe_error_response(
            "Request body must be JSON.",
            400
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, _safe_error_response(
            "Invalid JSON request body.",
            400
        )

    return data, None


def _get_required_string(data, field_name, max_length=500):
    value = data.get(field_name)

    if value is None:
        raise ValueError(
            f"{field_name} is required."
        )

    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a string."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{field_name} is required."
        )

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} cannot exceed "
            f"{max_length} characters."
        )

    return value


def _get_optional_string(
    data,
    field_name,
    max_length=500
):
    value = data.get(field_name)

    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a string."
        )

    value = value.strip()

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} cannot exceed "
            f"{max_length} characters."
        )

    return value or None


def _get_positive_float(data, field_name):
    value = data.get(field_name)

    if value is None:
        raise ValueError(
            f"{field_name} is required."
        )

    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{field_name} must be a valid number."
        )

    if value <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return value


def _get_optional_float(data, field_name):
    value = data.get(field_name)

    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{field_name} must be a valid number."
        )

    if value <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return value


def _get_pagination(default_limit=50):
    try:
        limit = int(
            request.args.get(
                "limit",
                default_limit
            )
        )

        offset = int(
            request.args.get(
                "offset",
                0
            )
        )

    except (TypeError, ValueError):
        raise ValueError(
            "limit and offset must be valid integers."
        )

    if limit < 1 or limit > 100:
        raise ValueError(
            "limit must be between 1 and 100."
        )

    if offset < 0:
        raise ValueError(
            "offset cannot be negative."
        )

    return limit, offset


def _handle_exception(exception):
    if isinstance(exception, ValueError):
        return _safe_error_response(
            str(exception),
            400
        )

    return _safe_error_response(
        "An internal server error occurred.",
        500
    )


# =========================================================
# PAYMENT ROUTES
# =========================================================

def payment_routes(app):

    # =====================================================
    # CREATE PAYMENT
    # POST /api/payments
    # =====================================================

    @app.route(
        "/api/payments",
        methods=["POST"]
    )
    def create_payment_route():

        data, error = _validate_json_body()

        if error:
            return error

        try:
            order_id = _get_required_string(
                data,
                "order_id",
                100
            )

            user_id = _get_required_string(
                data,
                "user_id",
                100
            )

            payment_method = data.get(
                "payment_method",
                "cod"
            )

            if not isinstance(
                payment_method,
                str
            ):
                raise ValueError(
                    "payment_method must be a string."
                )

            payment_method = payment_method.strip().lower()

            payment_gateway = _get_optional_string(
                data,
                "payment_gateway",
                100
            )

            amount = _get_optional_float(
                data,
                "amount"
            )

            currency = data.get(
                "currency",
                "INR"
            )

            if not isinstance(
                currency,
                str
            ):
                raise ValueError(
                    "currency must be a string."
                )

            currency = currency.strip().upper()

            idempotency_key = _get_optional_string(
                data,
                "idempotency_key",
                255
            )

            gateway_order_id = _get_optional_string(
                data,
                "gateway_order_id",
                255
            )

            ip_address = _get_optional_string(
                data,
                "ip_address",
                100
            )

            user_agent = _get_optional_string(
                data,
                "user_agent",
                1000
            )

            payment_metadata = data.get(
                "payment_metadata"
            )

            if payment_metadata is not None:
                if not isinstance(
                    payment_metadata,
                    str
                ):
                    raise ValueError(
                        "payment_metadata must be a string."
                    )

                if len(payment_metadata) > 10000:
                    raise ValueError(
                        "payment_metadata is too large."
                    )

            payment = create_payment(
                order_id=order_id,
                user_id=user_id,
                payment_method=payment_method,
                payment_gateway=payment_gateway,
                amount=amount,
                currency=currency,
                idempotency_key=idempotency_key,
                gateway_order_id=gateway_order_id,
                ip_address=ip_address,
                user_agent=user_agent,
                payment_metadata=payment_metadata
            )

            return jsonify({
                "success": True,
                "message": "Payment created successfully.",
                "payment": payment
            }), 201

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # GET ALL PAYMENTS
    # GET /api/payments
    # =====================================================

    @app.route(
        "/api/payments",
        methods=["GET"]
    )
    def get_payments_route():

        try:
            payment_status = request.args.get(
                "payment_status"
            )

            payment_method = request.args.get(
                "payment_method"
            )

            payment_gateway = request.args.get(
                "payment_gateway"
            )

            verification_status = request.args.get(
                "verification_status"
            )

            limit, offset = _get_pagination(
                default_limit=50
            )

            payments = get_payments(
                payment_status=payment_status,
                payment_method=payment_method,
                payment_gateway=payment_gateway,
                verification_status=verification_status,
                limit=limit,
                offset=offset
            )

            return jsonify({
                "success": True,
                "count": len(payments),
                "limit": limit,
                "offset": offset,
                "payments": payments
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # GET USER PAYMENTS
    # GET /api/payments/user?user_id=...
    # =====================================================

    @app.route(
        "/api/payments/user",
        methods=["GET"]
    )
    def get_user_payments_route():

        try:
            user_id = request.args.get(
                "user_id"
            )

            if not user_id:
                raise ValueError(
                    "user_id is required."
                )

            user_id = user_id.strip()

            if not user_id:
                raise ValueError(
                    "user_id is required."
                )

            payment_status = request.args.get(
                "payment_status"
            )

            limit, offset = _get_pagination(
                default_limit=20
            )

            payments = get_user_payments(
                user_id=user_id,
                payment_status=payment_status,
                limit=limit,
                offset=offset
            )

            return jsonify({
                "success": True,
                "user_id": user_id,
                "count": len(payments),
                "limit": limit,
                "offset": offset,
                "payments": payments
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # GET PAYMENT BY TRANSACTION ID
    # GET /api/payments/transaction/<transaction_id>
    # =====================================================

    @app.route(
        "/api/payments/transaction/<string:transaction_id>",
        methods=["GET"]
    )
    def get_payment_by_transaction_id_route(
        transaction_id
    ):

        try:
            transaction_id = transaction_id.strip()

            if not transaction_id:
                raise ValueError(
                    "transaction_id is required."
                )

            payment = get_payment_by_transaction_id(
                transaction_id
            )

            if not payment:
                return _safe_error_response(
                    "Payment not found.",
                    404
                )

            return jsonify({
                "success": True,
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # GET PAYMENTS BY ORDER ID
    # GET /api/payments/order/<order_id>
    # =====================================================

    @app.route(
        "/api/payments/order/<string:order_id>",
        methods=["GET"]
    )
    def get_payment_by_order_id_route(
        order_id
    ):

        try:
            order_id = order_id.strip()

            if not order_id:
                raise ValueError(
                    "order_id is required."
                )

            payments = get_payment_by_order_id(
                order_id
            )

            return jsonify({
                "success": True,
                "order_id": order_id,
                "count": len(payments),
                "payments": payments
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # GET PAYMENT BY ID
    # GET /api/payments/<payment_id>
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>",
        methods=["GET"]
    )
    def get_payment_by_id_route(
        payment_id
    ):

        try:
            payment_id = payment_id.strip()

            if not payment_id:
                raise ValueError(
                    "payment_id is required."
                )

            payment = get_payment_by_id(
                payment_id
            )

            if not payment:
                return _safe_error_response(
                    "Payment not found.",
                    404
                )

            return jsonify({
                "success": True,
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # UPDATE PAYMENT STATUS
    # PUT /api/payments/<payment_id>/status
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>/status",
        methods=["PUT"]
    )
    def update_payment_status_route(
        payment_id
    ):

        data, error = _validate_json_body()

        if error:
            return error

        try:
            payment_id = payment_id.strip()

            payment_status = _get_required_string(
                data,
                "payment_status",
                50
            ).lower()

            transaction_id = _get_optional_string(
                data,
                "transaction_id",
                255
            )

            gateway_payment_id = _get_optional_string(
                data,
                "gateway_payment_id",
                255
            )

            failure_code = _get_optional_string(
                data,
                "failure_code",
                255
            )

            failure_message = _get_optional_string(
                data,
                "failure_message",
                1000
            )

            payment = update_payment_status(
                payment_id=payment_id,
                payment_status=payment_status,
                transaction_id=transaction_id,
                gateway_payment_id=gateway_payment_id,
                failure_code=failure_code,
                failure_message=failure_message
            )

            return jsonify({
                "success": True,
                "message": "Payment status updated successfully.",
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # PROCESS PAYMENT
    # POST /api/payments/<payment_id>/process
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>/process",
        methods=["POST"]
    )
    def process_payment_route(
        payment_id
    ):

        data, error = _validate_json_body()

        if error:
            return error

        try:
            transaction_id = _get_optional_string(
                data,
                "transaction_id",
                255
            )

            gateway_payment_id = _get_optional_string(
                data,
                "gateway_payment_id",
                255
            )

            payment = process_payment(
                payment_id=payment_id,
                transaction_id=transaction_id,
                gateway_payment_id=gateway_payment_id
            )

            return jsonify({
                "success": True,
                "message": "Payment processing started.",
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # AUTHORIZE PAYMENT
    # POST /api/payments/<payment_id>/authorize
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>/authorize",
        methods=["POST"]
    )
    def authorize_payment_route(
        payment_id
    ):

        data, error = _validate_json_body()

        if error:
            return error

        try:
            transaction_id = _get_optional_string(
                data,
                "transaction_id",
                255
            )

            gateway_payment_id = _get_optional_string(
                data,
                "gateway_payment_id",
                255
            )

            payment = authorize_payment(
                payment_id=payment_id,
                transaction_id=transaction_id,
                gateway_payment_id=gateway_payment_id
            )

            return jsonify({
                "success": True,
                "message": "Payment authorized successfully.",
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # CAPTURE PAYMENT
    # POST /api/payments/<payment_id>/capture
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>/capture",
        methods=["POST"]
    )
    def capture_payment_route(
        payment_id
    ):

        data, error = _validate_json_body()

        if error:
            return error

        try:
            transaction_id = _get_optional_string(
                data,
                "transaction_id",
                255
            )

            gateway_payment_id = _get_optional_string(
                data,
                "gateway_payment_id",
                255
            )

            payment = capture_payment(
                payment_id=payment_id,
                transaction_id=transaction_id,
                gateway_payment_id=gateway_payment_id
            )

            return jsonify({
                "success": True,
                "message": "Payment captured successfully.",
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # FAIL PAYMENT
    # POST /api/payments/<payment_id>/fail
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>/fail",
        methods=["POST"]
    )
    def fail_payment_route(
        payment_id
    ):

        data, error = _validate_json_body()

        if error:
            return error

        try:
            failure_code = _get_optional_string(
                data,
                "failure_code",
                255
            )

            failure_message = _get_optional_string(
                data,
                "failure_message",
                1000
            )

            payment = fail_payment(
                payment_id=payment_id,
                failure_code=failure_code,
                failure_message=failure_message
            )

            return jsonify({
                "success": True,
                "message": "Payment marked as failed.",
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # CANCEL PAYMENT
    # POST /api/payments/<payment_id>/cancel
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>/cancel",
        methods=["POST"]
    )
    def cancel_payment_route(
        payment_id
    ):

        try:
            payment = cancel_payment(
                payment_id
            )

            return jsonify({
                "success": True,
                "message": "Payment cancelled successfully.",
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # REFUND PAYMENT
    # POST /api/payments/<payment_id>/refund
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>/refund",
        methods=["POST"]
    )
    def create_refund_route(
        payment_id
    ):

        data, error = _validate_json_body()

        if error:
            return error

        try:
            refund_amount = _get_positive_float(
                data,
                "refund_amount"
            )

            refund_transaction_id = _get_optional_string(
                data,
                "refund_transaction_id",
                255
            )

            payment = create_refund(
                payment_id=payment_id,
                refund_amount=refund_amount,
                refund_transaction_id=refund_transaction_id
            )

            return jsonify({
                "success": True,
                "message": "Refund processed successfully.",
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # VERIFY PAYMENT
    # PUT /api/payments/<payment_id>/verify
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>/verify",
        methods=["PUT"]
    )
    def verify_payment_route(
        payment_id
    ):

        data, error = _validate_json_body()

        if error:
            return error

        try:
            verification_status = data.get(
                "verification_status",
                "verified"
            )

            if not isinstance(
                verification_status,
                str
            ):
                raise ValueError(
                    "verification_status must be a string."
                )

            verification_status = (
                verification_status
                .strip()
                .lower()
            )

            payment = verify_payment(
                payment_id=payment_id,
                verification_status=verification_status
            )

            return jsonify({
                "success": True,
                "message": "Payment verification updated successfully.",
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # PAYMENT WEBHOOK
    # POST /api/payments/webhook
    # =====================================================

    @app.route(
        "/api/payments/webhook",
        methods=["POST"]
    )
    def process_webhook_route():

        data, error = _validate_json_body()

        if error:
            return error

        try:
            payment_id = _get_required_string(
                data,
                "payment_id",
                100
            )

            webhook_event_id = _get_required_string(
                data,
                "webhook_event_id",
                255
            )

            payment_status = _get_required_string(
                data,
                "payment_status",
                50
            ).lower()

            gateway_payment_id = _get_optional_string(
                data,
                "gateway_payment_id",
                255
            )

            transaction_id = _get_optional_string(
                data,
                "transaction_id",
                255
            )

            payment = process_webhook(
                payment_id=payment_id,
                webhook_event_id=webhook_event_id,
                payment_status=payment_status,
                gateway_payment_id=gateway_payment_id,
                transaction_id=transaction_id
            )

            return jsonify({
                "success": True,
                "message": "Payment webhook processed successfully.",
                "payment": payment
            }), 200

        except Exception as e:
            return _handle_exception(e)


    # =====================================================
    # DELETE PAYMENT
    # DELETE /api/payments/<payment_id>
    # =====================================================

    @app.route(
        "/api/payments/<string:payment_id>",
        methods=["DELETE"]
    )
    def delete_payment_route(
        payment_id
    ):

        try:
            result = delete_payment(
                payment_id
            )

            return jsonify(
                result
            ), 200

        except Exception as e:
            return _handle_exception(e)
from flask import jsonify


# ============================================================
# SUCCESS RESPONSE
# ============================================================

def success_response(
    message="Request successful.",
    data=None,
    status_code=200,
    **extra
):
    response = {
        "success": True,
        "message": message
    }

    if data is not None:
        response["data"] = data

    response.update(extra)

    return jsonify(response), status_code


# ============================================================
# ERROR RESPONSE
# ============================================================

def error_response(
    message="Something went wrong.",
    status_code=400,
    error=None,
    **extra
):
    response = {
        "success": False,
        "message": message
    }

    if error is not None:
        response["error"] = error

    response.update(extra)

    return jsonify(response), status_code


# ============================================================
# CREATED RESPONSE
# ============================================================

def created_response(
    message="Resource created successfully.",
    data=None,
    **extra
):
    return success_response(
        message=message,
        data=data,
        status_code=201,
        **extra
    )


# ============================================================
# NOT FOUND RESPONSE
# ============================================================

def not_found_response(
    message="Resource not found.",
    **extra
):
    return error_response(
        message=message,
        status_code=404,
        **extra
    )


# ============================================================
# BAD REQUEST RESPONSE
# ============================================================

def bad_request_response(
    message="Invalid request.",
    **extra
):
    return error_response(
        message=message,
        status_code=400,
        **extra
    )


# ============================================================
# UNAUTHORIZED RESPONSE
# ============================================================

def unauthorized_response(
    message="Unauthorized access.",
    **extra
):
    return error_response(
        message=message,
        status_code=401,
        **extra
    )


# ============================================================
# FORBIDDEN RESPONSE
# ============================================================

def forbidden_response(
    message="Access forbidden.",
    **extra
):
    return error_response(
        message=message,
        status_code=403,
        **extra
    )


# ============================================================
# CONFLICT RESPONSE
# ============================================================

def conflict_response(
    message="Resource conflict.",
    **extra
):
    return error_response(
        message=message,
        status_code=409,
        **extra
    )


# ============================================================
# SERVER ERROR RESPONSE
# ============================================================

def server_error_response(
    message="Internal server error.",
    error=None,
    **extra
):
    return error_response(
        message=message,
        status_code=500,
        error=error,
        **extra
    )


# ============================================================
# VALIDATION ERROR RESPONSE
# ============================================================

def validation_error_response(
    message="Validation failed.",
    errors=None,
    **extra
):
    response = {
        "success": False,
        "message": message
    }

    if errors is not None:
        response["errors"] = errors

    response.update(extra)

    return jsonify(response), 422
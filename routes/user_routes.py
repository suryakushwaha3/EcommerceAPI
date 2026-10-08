from flask import request, jsonify

from operations.user_operation import (
    create_user,
    login_user,
    get_user_by_id,
    get_user_by_email,
    update_user_profile,
    change_password,
    create_password_reset_token,
    reset_password,
    get_all_users, 
    verify_email,
    update_user_status,
    delete_user
)


def user_routes(app):

    # ============================================================
    # CREATE USER / SIGN UP
    # POST /api/users
    # ============================================================

    @app.route("/api/users", methods=["POST"])
    def create_user_route():
        try:
            data = request.get_json(silent=True) or {}

            name = data.get("name")
            email = data.get("email")
            password = data.get("password")

            if not name or not email or not password:
                return jsonify({
                    "success": False,
                    "message": "Name, email and password are required"
                }), 400

            result = create_user(
                name=name,
                email=email,
                password=password,
                phone_number=data.get("phone_number"),
                username=data.get("username"),
                profile_image=data.get("profile_image"),
                date_of_birth=data.get("date_of_birth"),
                gender=data.get("gender")
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 201

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to create user",
                "error": str(error)
            }), 500


    # ============================================================
    # LOGIN
    # POST /api/users/login
    # ============================================================

    @app.route("/api/users/login", methods=["POST"])
    def login_user_route():
        try:
            data = request.get_json(silent=True) or {}

            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return jsonify({
                    "success": False,
                    "message": "Email and password are required"
                }), 400

            result = login_user(
                email=email,
                password=password,
                login_ip=request.remote_addr
            )

            if not result.get("success"):
                return jsonify(result), 401

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Login failed",
                "error": str(error)
            }), 500


    # ============================================================
    # GET USER BY ID
    # GET /api/users/<user_id>
    # ============================================================

    @app.route("/api/users/<string:user_id>", methods=["GET"])
    def get_user_by_id_route(user_id):
        try:
            result = get_user_by_id(user_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to fetch user",
                "error": str(error)
            }), 500


    # ============================================================
    # GET USER BY EMAIL
    # GET /api/users/email/<email>
    # ============================================================

    @app.route("/api/users/email/<path:email>", methods=["GET"])
    def get_user_by_email_route(email):
        try:
            result = get_user_by_email(email)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to fetch user",
                "error": str(error)
            }), 500


    # ============================================================
    # UPDATE USER PROFILE
    # PUT /api/users/<user_id>
    # ============================================================

    @app.route("/api/users/<string:user_id>", methods=["PUT"])
    def update_user_profile_route(user_id):
        try:
            data = request.get_json(silent=True) or {}

            result = update_user_profile(
                user_id=user_id,
                name=data.get("name"),
                username=data.get("username"),
                phone_number=data.get("phone_number"),
                profile_image=data.get("profile_image"),
                date_of_birth=data.get("date_of_birth"),
                gender=data.get("gender")
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update profile",
                "error": str(error)
            }), 500


    # ============================================================
    # CHANGE PASSWORD
    # PUT /api/users/<user_id>/change-password
    # ============================================================

    @app.route(
        "/api/users/<string:user_id>/change-password",
        methods=["PUT"]
    )
    def change_password_route(user_id):
        try:
            data = request.get_json(silent=True) or {}

            old_password = data.get("old_password")
            new_password = data.get("new_password")

            if not old_password or not new_password:
                return jsonify({
                    "success": False,
                    "message": "Old password and new password are required"
                }), 400

            result = change_password(
                user_id=user_id,
                old_password=old_password,
                new_password=new_password
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to change password",
                "error": str(error)
            }), 500


    # ============================================================
    # FORGOT PASSWORD
    # POST /api/users/forgot-password
    # ============================================================

    @app.route("/api/users/forgot-password", methods=["POST"])
    def forgot_password_route():
        try:
            data = request.get_json(silent=True) or {}

            email = data.get("email")

            if not email:
                return jsonify({
                    "success": False,
                    "message": "Email is required"
                }), 400

            result = create_password_reset_token(email)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to generate password reset token",
                "error": str(error)
            }), 500


    # ============================================================
    # RESET PASSWORD
    # POST /api/users/reset-password
    # ============================================================

    @app.route("/api/users/reset-password", methods=["POST"])
    def reset_password_route():
        try:
            data = request.get_json(silent=True) or {}

            token = data.get("token")
            new_password = data.get("new_password")

            if not token or not new_password:
                return jsonify({
                    "success": False,
                    "message": "Token and new password are required"
                }), 400

            result = reset_password(
                token=token,
                new_password=new_password
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to reset password",
                "error": str(error)
            }), 500


    # ============================================================
    # VERIFY EMAIL
    # POST /api/users/verify-email
    # ============================================================

    @app.route("/api/users/verify-email", methods=["POST"])
    def verify_email_route():
        try:
            data = request.get_json(silent=True) or {}

            token = data.get("token")

            if not token:
                return jsonify({
                    "success": False,
                    "message": "Verification token is required"
                }), 400

            result = verify_email(token)

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Email verification failed",
                "error": str(error)
            }), 500


    # ============================================================
    # UPDATE USER STATUS
    # PUT /api/users/<user_id>/status
    # ============================================================

    @app.route(
        "/api/users/<string:user_id>/status",
        methods=["PUT"]
    )
    def update_user_status_route(user_id):
        try:
            data = request.get_json(silent=True) or {}

            status = data.get("status")

            if not status:
                return jsonify({
                    "success": False,
                    "message": "Status is required"
                }), 400

            result = update_user_status(
                user_id=user_id,
                status=status
            )

            if not result.get("success"):
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to update user status",
                "error": str(error)
            }), 500


    # ============================================================
    # DELETE USER
    # DELETE /api/users/<user_id>
    # ============================================================

    @app.route(
        "/api/users/<string:user_id>",
        methods=["DELETE"]
    )
    def delete_user_route(user_id):
        try:
            result = delete_user(user_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to delete user",
                "error": str(error)
            }), 500

            # ============================================================
    # GET ALL USERS
    # GET /api/users
    # ============================================================

    @app.route("/api/users", methods=["GET"])
    def get_all_users_route():
        try:
            result = get_all_users()

            if not result.get("success"):
                return jsonify(result), 500

            return jsonify(result), 200

        except Exception as error:
            return jsonify({
                "success": False,
                "message": "Failed to fetch users",
                "error": str(error)
            }), 500
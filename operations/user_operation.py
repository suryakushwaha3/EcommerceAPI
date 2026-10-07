import hashlib
import secrets
from datetime import datetime, timezone

from database.database import get_db_connection


# ============================================================
# Helper Functions
# ============================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _hash_password(password):
    salt = secrets.token_bytes(32)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def _verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            310000
        )

        return secrets.compare_digest(
            password_hash.hex(),
            hash_hex
        )

    except (ValueError, TypeError):
        return False


def _generate_user_id():
    return "USR_" + secrets.token_hex(8).upper()


# ============================================================
# Create User
# ============================================================

def create_user(
    name,
    email,
    password,
    phone_number=None,
    username=None,
    profile_image=None,
    date_of_birth=None,
    gender=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        email = email.strip().lower()

        if username:
            username = username.strip().lower()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        if cursor.fetchone():
            return {
                "success": False,
                "message": "Email already registered"
            }

        if phone_number:
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE phone_number = ?
                """,
                (phone_number,)
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Phone number already registered"
                }

        if username:
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE username = ?
                """,
                (username,)
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Username already exists"
                }

        now = _current_time()

        user_id = _generate_user_id()

        password_hash = _hash_password(password)

        cursor.execute(
            """
            INSERT INTO users (
                user_id,
                name,
                username,
                email,
                phone_number,
                password_hash,
                profile_image,
                date_of_birth,
                gender,
                is_email_verified,
                is_phone_verified,
                account_status,
                is_admin,
                is_seller,
                login_attempts,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 'active', 0, 0, 0, ?, ?)
            """,
            (
                user_id,
                name.strip(),
                username,
                email,
                phone_number,
                password_hash,
                profile_image,
                date_of_birth,
                gender,
                now,
                now
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user_id
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to create user",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Login
# ============================================================

def login_user(email, password, login_ip=None):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        email = email.strip().lower()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND deleted_at IS NULL
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user:
            return {
                "success": False,
                "message": "Invalid email or password"
            }

        user = dict(user)

        if user["account_status"] in (
            "blocked",
            "suspended",
            "deleted"
        ):
            return {
                "success": False,
                "message": "Account is not active"
            }

        if user["login_attempts"] >= 5:
            return {
                "success": False,
                "message": "Too many login attempts"
            }

        if not _verify_password(
            password,
            user["password_hash"]
        ):
            cursor.execute(
                """
                UPDATE users
                SET login_attempts = login_attempts + 1,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (
                    _current_time(),
                    user["user_id"]
                )
            )

            connection.commit()

            return {
                "success": False,
                "message": "Invalid email or password"
            }

        now = _current_time()

        cursor.execute(
            """
            UPDATE users
            SET login_attempts = 0,
                last_login_at = ?,
                last_login_ip = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                now,
                login_ip,
                now,
                user["user_id"]
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "user_id": user["user_id"],
                "name": user["name"],
                "username": user["username"],
                "email": user["email"],
                "phone_number": user["phone_number"],
                "profile_image": user["profile_image"],
                "is_email_verified": user["is_email_verified"],
                "is_phone_verified": user["is_phone_verified"],
                "is_admin": user["is_admin"],
                "is_seller": user["is_seller"]
            }
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Login failed",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Get User By ID
# ============================================================

def get_user_by_id(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                user_id,
                name,
                username,
                email,
                phone_number,
                profile_image,
                date_of_birth,
                gender,
                is_email_verified,
                is_phone_verified,
                account_status,
                is_admin,
                is_seller,
                last_login_at,
                created_at,
                updated_at
            FROM users
            WHERE user_id = ?
            AND deleted_at IS NULL
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        return {
            "success": True,
            "user": dict(user)
        }

    finally:
        connection.close()


# ============================================================
# Get User By Email
# ============================================================

def get_user_by_email(email):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        email = email.strip().lower()

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                username,
                email,
                phone_number,
                profile_image,
                date_of_birth,
                gender,
                account_status,
                is_email_verified,
                is_phone_verified,
                created_at
            FROM users
            WHERE email = ?
            AND deleted_at IS NULL
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        return {
            "success": True,
            "user": dict(user)
        }

    finally:
        connection.close()


# ============================================================
# Update Profile
# ============================================================

def update_user_profile(
    user_id,
    name=None,
    username=None,
    phone_number=None,
    profile_image=None,
    date_of_birth=None,
    gender=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE user_id = ?
            AND deleted_at IS NULL
            """,
            (user_id,)
        )

        if not cursor.fetchone():
            return {
                "success": False,
                "message": "User not found"
            }

        if username:
            username = username.strip().lower()

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE username = ?
                AND user_id != ?
                """,
                (
                    username,
                    user_id
                )
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Username already exists"
                }

        if phone_number:
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE phone_number = ?
                AND user_id != ?
                """,
                (
                    phone_number,
                    user_id
                )
            )

            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Phone number already registered"
                }

        update_fields = []
        values = []

        if name is not None:
            update_fields.append("name = ?")
            values.append(name.strip())

        if username is not None:
            update_fields.append("username = ?")
            values.append(username)

        if phone_number is not None:
            update_fields.append("phone_number = ?")
            values.append(phone_number)

        if profile_image is not None:
            update_fields.append("profile_image = ?")
            values.append(profile_image)

        if date_of_birth is not None:
            update_fields.append("date_of_birth = ?")
            values.append(date_of_birth)

        if gender is not None:
            update_fields.append("gender = ?")
            values.append(gender)

        if not update_fields:
            return {
                "success": False,
                "message": "No data to update"
            }

        update_fields.append("updated_at = ?")
        values.append(_current_time())

        values.append(user_id)

        query = f"""
            UPDATE users
            SET {", ".join(update_fields)}
            WHERE user_id = ?
            AND deleted_at IS NULL
        """

        cursor.execute(query, values)

        connection.commit()

        return {
            "success": True,
            "message": "Profile updated successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update profile",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Change Password
# ============================================================

def change_password(
    user_id,
    old_password,
    new_password
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT password_hash
            FROM users
            WHERE user_id = ?
            AND deleted_at IS NULL
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        if not _verify_password(
            old_password,
            user["password_hash"]
        ):
            return {
                "success": False,
                "message": "Current password is incorrect"
            }

        new_password_hash = _hash_password(new_password)

        now = _current_time()

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?,
                password_changed_at = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                new_password_hash,
                now,
                now,
                user_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Password changed successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to change password",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Generate Password Reset Token
# ============================================================

def create_password_reset_token(email):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        email = email.strip().lower()

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE email = ?
            AND deleted_at IS NULL
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        token = secrets.token_urlsafe(48)

        expiry = datetime.now(
            timezone.utc
        ).timestamp() + 1800

        expiry_time = datetime.fromtimestamp(
            expiry,
            timezone.utc
        ).isoformat()

        cursor.execute(
            """
            UPDATE users
            SET password_reset_token = ?,
                password_reset_expiry = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                token,
                expiry_time,
                _current_time(),
                user["user_id"]
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Password reset token generated",
            "token": token
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to generate reset token",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Reset Password
# ============================================================

def reset_password(token, new_password):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = datetime.now(timezone.utc)

        cursor.execute(
            """
            SELECT user_id, password_reset_expiry
            FROM users
            WHERE password_reset_token = ?
            AND deleted_at IS NULL
            """,
            (token,)
        )

        user = cursor.fetchone()

        if not user:
            return {
                "success": False,
                "message": "Invalid reset token"
            }

        expiry = datetime.fromisoformat(
            user["password_reset_expiry"]
        )

        if now > expiry:
            return {
                "success": False,
                "message": "Reset token has expired"
            }

        password_hash = _hash_password(new_password)

        current_time = _current_time()

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?,
                password_changed_at = ?,
                password_reset_token = NULL,
                password_reset_expiry = NULL,
                login_attempts = 0,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                password_hash,
                current_time,
                current_time,
                user["user_id"]
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Password reset successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to reset password",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Verify Email
# ============================================================

def verify_email(token):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = datetime.now(timezone.utc)

        cursor.execute(
            """
            SELECT user_id, email_verification_expiry
            FROM users
            WHERE email_verification_token = ?
            AND deleted_at IS NULL
            """,
            (token,)
        )

        user = cursor.fetchone()

        if not user:
            return {
                "success": False,
                "message": "Invalid verification token"
            }

        expiry = datetime.fromisoformat(
            user["email_verification_expiry"]
        )

        if now > expiry:
            return {
                "success": False,
                "message": "Verification token has expired"
            }

        current_time = _current_time()

        cursor.execute(
            """
            UPDATE users
            SET is_email_verified = 1,
                email_verification_token = NULL,
                email_verification_expiry = NULL,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                current_time,
                user["user_id"]
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Email verified successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Email verification failed",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Block / Unblock User
# ============================================================

def update_user_status(user_id, status):
    allowed_statuses = (
        "active",
        "inactive",
        "blocked",
        "suspended"
    )

    if status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid account status"
        }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE users
            SET account_status = ?,
                updated_at = ?
            WHERE user_id = ?
            AND deleted_at IS NULL
            """,
            (
                status,
                _current_time(),
                user_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "User not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": f"User status changed to {status}"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to update user status",
            "error": str(error)
        }

    finally:
        connection.close()


# ============================================================
# Soft Delete User
# ============================================================

def delete_user(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        now = _current_time()

        cursor.execute(
            """
            UPDATE users
            SET account_status = 'deleted',
                deleted_at = ?,
                updated_at = ?
            WHERE user_id = ?
            AND deleted_at IS NULL
            """,
            (
                now,
                now,
                user_id
            )
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "User not found"
            }

        connection.commit()

        return {
            "success": True,
            "message": "User deleted successfully"
        }

    except Exception as error:
        connection.rollback()

        return {
            "success": False,
            "message": "Failed to delete user",
            "error": str(error)
        }

    finally:
        connection.close()
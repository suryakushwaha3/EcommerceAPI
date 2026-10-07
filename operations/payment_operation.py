from database.database import get_db_connection
from datetime import datetime, timezone
import math
import uuid


# =========================================================
# CONSTANTS
# =========================================================

ALLOWED_PAYMENT_METHODS = {
    "cod",
    "upi",
    "card",
    "net_banking",
    "wallet",
    "emi",
    "other"
}

ALLOWED_PAYMENT_STATUSES = {
    "pending",
    "processing",
    "authorized",
    "captured",
    "failed",
    "cancelled",
    "expired",
    "refunded",
    "partially_refunded"
}

ALLOWED_VERIFICATION_STATUSES = {
    "pending",
    "verified",
    "failed"
}

ALLOWED_CURRENCIES = {
    "INR"
}

# Valid payment status transitions.
# Same status is also allowed.
PAYMENT_STATUS_TRANSITIONS = {
    "pending": {
        "pending",
        "processing",
        "authorized",
        "captured",
        "failed",
        "cancelled",
        "expired"
    },

    "processing": {
        "processing",
        "authorized",
        "captured",
        "failed",
        "cancelled",
        "expired"
    },

    "authorized": {
        "authorized",
        "captured",
        "failed",
        "cancelled",
        "expired"
    },

    "captured": {
        "captured",
        "partially_refunded",
        "refunded"
    },

    "failed": {
        "failed",
        "processing",
        "pending"
    },

    "cancelled": {
        "cancelled"
    },

    "expired": {
        "expired",
        "pending",
        "processing"
    },

    "partially_refunded": {
        "partially_refunded",
        "refunded"
    },

    "refunded": {
        "refunded"
    }
}


# =========================================================
# HELPERS
# =========================================================

def _current_time():
    return datetime.now(timezone.utc).isoformat()


def _generate_payment_id():
    return f"PAY-{uuid.uuid4().hex[:16].upper()}"


def _is_valid_positive_amount(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return False

    return (
        math.isfinite(value)
        and value > 0
    )


def _is_valid_non_negative_amount(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return False

    return (
        math.isfinite(value)
        and value >= 0
    )


def _clean_string(value, field_name, max_length=500, required=False):
    if value is None:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")

    value = value.strip()

    if required and not value:
        raise ValueError(f"{field_name} is required.")

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} cannot exceed {max_length} characters."
        )

    return value or None


def _validate_payment_method(payment_method):
    payment_method = _clean_string(
        payment_method,
        "payment_method",
        max_length=50,
        required=True
    ).lower()

    if payment_method not in ALLOWED_PAYMENT_METHODS:
        raise ValueError("Invalid payment method.")

    return payment_method


def _validate_currency(currency):
    currency = _clean_string(
        currency,
        "currency",
        max_length=10,
        required=True
    ).upper()

    if currency not in ALLOWED_CURRENCIES:
        raise ValueError("Unsupported currency.")

    return currency


def _validate_payment_status(payment_status):
    payment_status = _clean_string(
        payment_status,
        "payment_status",
        max_length=50,
        required=True
    ).lower()

    if payment_status not in ALLOWED_PAYMENT_STATUSES:
        raise ValueError("Invalid payment status.")

    return payment_status


def _validate_verification_status(verification_status):
    verification_status = _clean_string(
        verification_status,
        "verification_status",
        max_length=50,
        required=True
    ).lower()

    if verification_status not in ALLOWED_VERIFICATION_STATUSES:
        raise ValueError("Invalid verification status.")

    return verification_status


def _validate_order(cursor, order_id):
    order_id = _clean_string(
        order_id,
        "order_id",
        max_length=100,
        required=True
    )

    cursor.execute("""
        SELECT
            order_id,
            user_id,
            total_amount,
            currency,
            payment_status,
            order_status
        FROM orders
        WHERE order_id = ?
        AND deleted_at IS NULL
    """, (order_id,))

    return cursor.fetchone()


def _validate_user(cursor, user_id):
    user_id = _clean_string(
        user_id,
        "user_id",
        max_length=100,
        required=True
    )

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE user_id = ?
        AND account_status = 'active'
        AND deleted_at IS NULL
    """, (user_id,))

    return cursor.fetchone()


def _get_payment_cursor(cursor, payment_id):
    payment_id = _clean_string(
        payment_id,
        "payment_id",
        max_length=100,
        required=True
    )

    cursor.execute("""
        SELECT *
        FROM payments
        WHERE payment_id = ?
        AND deleted_at IS NULL
    """, (payment_id,))

    return cursor.fetchone()


def _validate_status_transition(
    current_status,
    new_status
):
    if current_status not in PAYMENT_STATUS_TRANSITIONS:
        raise ValueError(
            f"Unsupported current payment status: {current_status}"
        )

    allowed_next_statuses = PAYMENT_STATUS_TRANSITIONS[
        current_status
    ]

    if new_status not in allowed_next_statuses:
        raise ValueError(
            f"Payment cannot change from "
            f"'{current_status}' to '{new_status}'."
        )


def _get_payment_by_id_cursor(cursor, payment_id):
    cursor.execute("""
        SELECT *
        FROM payments
        WHERE payment_id = ?
        AND deleted_at IS NULL
    """, (payment_id,))

    payment = cursor.fetchone()

    return dict(payment) if payment else None


# =========================================================
# CREATE PAYMENT
# =========================================================

def create_payment(
    order_id,
    user_id,
    payment_method="cod",
    payment_gateway=None,
    amount=None,
    currency="INR",
    idempotency_key=None,
    gateway_order_id=None,
    ip_address=None,
    user_agent=None,
    payment_metadata=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        order = _validate_order(
            cursor,
            order_id
        )

        if not order:
            raise ValueError("Order not found.")

        if order["user_id"] != user_id:
            raise ValueError(
                "Order does not belong to this user."
            )

        user = _validate_user(
            cursor,
            user_id
        )

        if not user:
            raise ValueError(
                "User not found or inactive."
            )

        payment_method = _validate_payment_method(
            payment_method
        )

        currency = _validate_currency(
            currency
        )

        order_currency = (
            order["currency"] or "INR"
        ).upper()

        if currency != order_currency:
            raise ValueError(
                "Payment currency does not match order currency."
            )

        order_amount = float(
            order["total_amount"] or 0
        )

        if not _is_valid_positive_amount(
            order_amount
        ):
            raise ValueError(
                "Order amount must be greater than zero."
            )

        if amount is None:
            amount = order_amount
        else:
            if not _is_valid_positive_amount(amount):
                raise ValueError(
                    "Payment amount must be greater than zero."
                )

            amount = float(amount)

            if not math.isclose(
                amount,
                order_amount,
                rel_tol=0,
                abs_tol=0.01
            ):
                raise ValueError(
                    "Payment amount does not match order total."
                )

        payment_gateway = _clean_string(
            payment_gateway,
            "payment_gateway",
            max_length=100
        )

        idempotency_key = _clean_string(
            idempotency_key,
            "idempotency_key",
            max_length=255
        )

        gateway_order_id = _clean_string(
            gateway_order_id,
            "gateway_order_id",
            max_length=255
        )

        ip_address = _clean_string(
            ip_address,
            "ip_address",
            max_length=100
        )

        user_agent = _clean_string(
            user_agent,
            "user_agent",
            max_length=1000
        )

        if idempotency_key:
            cursor.execute("""
                SELECT *
                FROM payments
                WHERE idempotency_key = ?
                AND deleted_at IS NULL
            """, (idempotency_key,))

            existing_payment = cursor.fetchone()

            if existing_payment:

                if (
                    existing_payment["order_id"] != order_id
                    or existing_payment["user_id"] != user_id
                ):
                    raise ValueError(
                        "Idempotency key is already associated "
                        "with another payment."
                    )

                return dict(existing_payment)

        payment_id = _generate_payment_id()
        current_time = _current_time()

        cursor.execute("""
            INSERT INTO payments (
                payment_id,
                order_id,
                user_id,
                gateway_order_id,
                payment_gateway,
                payment_method,
                payment_status,
                amount,
                currency,
                idempotency_key,
                payment_attempts,
                verification_status,
                payment_metadata,
                ip_address,
                user_agent,
                initiated_at,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            payment_id,
            order_id,
            user_id,
            gateway_order_id,
            payment_gateway,
            payment_method,
            "pending",
            amount,
            currency,
            idempotency_key,
            1,
            "pending",
            payment_metadata,
            ip_address,
            user_agent,
            current_time,
            current_time,
            current_time
        ))

        connection.commit()

        return _get_payment_by_id_cursor(
            cursor,
            payment_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# GET PAYMENT BY ID
# =========================================================

def get_payment_by_id(payment_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        payment_id = _clean_string(
            payment_id,
            "payment_id",
            max_length=100,
            required=True
        )

        cursor.execute("""
            SELECT *
            FROM payments
            WHERE payment_id = ?
            AND deleted_at IS NULL
        """, (payment_id,))

        payment = cursor.fetchone()

        return dict(payment) if payment else None

    finally:
        connection.close()


# =========================================================
# GET PAYMENT BY TRANSACTION ID
# =========================================================

def get_payment_by_transaction_id(transaction_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        transaction_id = _clean_string(
            transaction_id,
            "transaction_id",
            max_length=255,
            required=True
        )

        cursor.execute("""
            SELECT *
            FROM payments
            WHERE transaction_id = ?
            AND deleted_at IS NULL
        """, (transaction_id,))

        payment = cursor.fetchone()

        return dict(payment) if payment else None

    finally:
        connection.close()


# =========================================================
# GET PAYMENTS BY ORDER ID
# =========================================================

def get_payment_by_order_id(order_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        order_id = _clean_string(
            order_id,
            "order_id",
            max_length=100,
            required=True
        )

        cursor.execute("""
            SELECT *
            FROM payments
            WHERE order_id = ?
            AND deleted_at IS NULL
            ORDER BY created_at DESC
        """, (order_id,))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# =========================================================
# GET USER PAYMENTS
# =========================================================

def get_user_payments(
    user_id,
    payment_status=None,
    limit=20,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        user_id = _clean_string(
            user_id,
            "user_id",
            max_length=100,
            required=True
        )

        if payment_status:
            payment_status = _validate_payment_status(
                payment_status
            )

        limit = max(
            1,
            min(int(limit), 100)
        )

        offset = max(
            0,
            int(offset)
        )

        query = """
            SELECT *
            FROM payments
            WHERE user_id = ?
            AND deleted_at IS NULL
        """

        params = [user_id]

        if payment_status:
            query += """
                AND payment_status = ?
            """
            params.append(payment_status)

        query += """
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([
            limit,
            offset
        ])

        cursor.execute(
            query,
            tuple(params)
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# =========================================================
# GET ALL PAYMENTS
# =========================================================

def get_payments(
    payment_status=None,
    payment_method=None,
    payment_gateway=None,
    verification_status=None,
    limit=50,
    offset=0
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if payment_status:
            payment_status = _validate_payment_status(
                payment_status
            )

        if payment_method:
            payment_method = _validate_payment_method(
                payment_method
            )

        if payment_gateway:
            payment_gateway = _clean_string(
                payment_gateway,
                "payment_gateway",
                max_length=100
            )

        if verification_status:
            verification_status = _validate_verification_status(
                verification_status
            )

        limit = max(
            1,
            min(int(limit), 100)
        )

        offset = max(
            0,
            int(offset)
        )

        query = """
            SELECT *
            FROM payments
            WHERE deleted_at IS NULL
        """

        params = []

        if payment_status:
            query += """
                AND payment_status = ?
            """
            params.append(payment_status)

        if payment_method:
            query += """
                AND payment_method = ?
            """
            params.append(payment_method)

        if payment_gateway:
            query += """
                AND payment_gateway = ?
            """
            params.append(payment_gateway)

        if verification_status:
            query += """
                AND verification_status = ?
            """
            params.append(verification_status)

        query += """
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([
            limit,
            offset
        ])

        cursor.execute(
            query,
            tuple(params)
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# =========================================================
# UPDATE PAYMENT STATUS
# =========================================================

def update_payment_status(
    payment_id,
    payment_status,
    transaction_id=None,
    gateway_payment_id=None,
    failure_code=None,
    failure_message=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        payment_status = _validate_payment_status(
            payment_status
        )

        payment = _get_payment_cursor(
            cursor,
            payment_id
        )

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        current_status = payment[
            "payment_status"
        ]

        _validate_status_transition(
            current_status,
            payment_status
        )

        transaction_id = _clean_string(
            transaction_id,
            "transaction_id",
            max_length=255
        )

        gateway_payment_id = _clean_string(
            gateway_payment_id,
            "gateway_payment_id",
            max_length=255
        )

        failure_code = _clean_string(
            failure_code,
            "failure_code",
            max_length=255
        )

        failure_message = _clean_string(
            failure_message,
            "failure_message",
            max_length=1000
        )

        current_time = _current_time()

        completed_at = None

        if payment_status == "captured":
            completed_at = current_time

        if payment_status not in (
            "failed",
        ):
            failure_code = None
            failure_message = None

        cursor.execute("""
            UPDATE payments
            SET
                payment_status = ?,
                transaction_id = COALESCE(
                    ?,
                    transaction_id
                ),
                gateway_payment_id = COALESCE(
                    ?,
                    gateway_payment_id
                ),
                failure_code = ?,
                failure_message = ?,
                completed_at = COALESCE(
                    ?,
                    completed_at
                ),
                updated_at = ?
            WHERE payment_id = ?
            AND deleted_at IS NULL
        """, (
            payment_status,
            transaction_id,
            gateway_payment_id,
            failure_code,
            failure_message,
            completed_at,
            current_time,
            payment_id
        ))

        if payment_status == "captured":
            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'paid',
                    updated_at = ?
                WHERE order_id = ?
            """, (
                current_time,
                payment["order_id"]
            ))

        elif payment_status == "failed":
            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'failed',
                    updated_at = ?
                WHERE order_id = ?
            """, (
                current_time,
                payment["order_id"]
            ))

        elif payment_status == "cancelled":
            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'cancelled',
                    updated_at = ?
                WHERE order_id = ?
            """, (
                current_time,
                payment["order_id"]
            ))

        elif payment_status == "refunded":
            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'refunded',
                    updated_at = ?
                WHERE order_id = ?
            """, (
                current_time,
                payment["order_id"]
            ))

        elif payment_status == "partially_refunded":
            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'partially_refunded',
                    updated_at = ?
                WHERE order_id = ?
            """, (
                current_time,
                payment["order_id"]
            ))

        connection.commit()

        return _get_payment_by_id_cursor(
            cursor,
            payment_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# PROCESS PAYMENT
# =========================================================

def process_payment(
    payment_id,
    transaction_id=None,
    gateway_payment_id=None
):
    return update_payment_status(
        payment_id=payment_id,
        payment_status="processing",
        transaction_id=transaction_id,
        gateway_payment_id=gateway_payment_id
    )


# =========================================================
# AUTHORIZE PAYMENT
# =========================================================

def authorize_payment(
    payment_id,
    transaction_id=None,
    gateway_payment_id=None
):
    return update_payment_status(
        payment_id=payment_id,
        payment_status="authorized",
        transaction_id=transaction_id,
        gateway_payment_id=gateway_payment_id
    )


# =========================================================
# CAPTURE PAYMENT
# =========================================================

def capture_payment(
    payment_id,
    transaction_id=None,
    gateway_payment_id=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        payment = _get_payment_cursor(
            cursor,
            payment_id
        )

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        if payment["payment_status"] not in (
            "pending",
            "processing",
            "authorized"
        ):
            raise ValueError(
                f"Payment cannot be captured from "
                f"'{payment['payment_status']}' status."
            )

        transaction_id = _clean_string(
            transaction_id,
            "transaction_id",
            max_length=255
        )

        gateway_payment_id = _clean_string(
            gateway_payment_id,
            "gateway_payment_id",
            max_length=255
        )

        current_time = _current_time()

        cursor.execute("""
            UPDATE payments
            SET
                payment_status = 'captured',
                transaction_id = COALESCE(
                    ?,
                    transaction_id
                ),
                gateway_payment_id = COALESCE(
                    ?,
                    gateway_payment_id
                ),
                completed_at = ?,
                updated_at = ?
            WHERE payment_id = ?
            AND deleted_at IS NULL
        """, (
            transaction_id,
            gateway_payment_id,
            current_time,
            current_time,
            payment_id
        ))

        cursor.execute("""
            UPDATE orders
            SET
                payment_status = 'paid',
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
        """, (
            current_time,
            payment["order_id"]
        ))

        connection.commit()

        return _get_payment_by_id_cursor(
            cursor,
            payment_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# FAIL PAYMENT
# =========================================================

def fail_payment(
    payment_id,
    failure_code=None,
    failure_message=None
):
    return update_payment_status(
        payment_id=payment_id,
        payment_status="failed",
        failure_code=failure_code,
        failure_message=failure_message
    )


# =========================================================
# CANCEL PAYMENT
# =========================================================

def cancel_payment(payment_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        payment = _get_payment_cursor(
            cursor,
            payment_id
        )

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        current_status = payment[
            "payment_status"
        ]

        if current_status in (
            "captured",
            "refunded",
            "partially_refunded"
        ):
            raise ValueError(
                "Captured/refunded payment cannot be cancelled. "
                "Use refund instead."
            )

        _validate_status_transition(
            current_status,
            "cancelled"
        )

        current_time = _current_time()

        cursor.execute("""
            UPDATE payments
            SET
                payment_status = 'cancelled',
                updated_at = ?
            WHERE payment_id = ?
            AND deleted_at IS NULL
        """, (
            current_time,
            payment_id
        ))

        cursor.execute("""
            UPDATE orders
            SET
                payment_status = 'cancelled',
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
        """, (
            current_time,
            payment["order_id"]
        ))

        connection.commit()

        return _get_payment_by_id_cursor(
            cursor,
            payment_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# CREATE REFUND
# =========================================================

def create_refund(
    payment_id,
    refund_amount,
    refund_transaction_id=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        payment = _get_payment_cursor(
            cursor,
            payment_id
        )

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        if payment["payment_status"] not in (
            "captured",
            "partially_refunded"
        ):
            raise ValueError(
                "Only captured payments can be refunded."
            )

        if not _is_valid_positive_amount(
            refund_amount
        ):
            raise ValueError(
                "Refund amount must be greater than zero."
            )

        refund_amount = float(
            refund_amount
        )

        already_refunded = float(
            payment["refund_amount"] or 0
        )

        total_amount = float(
            payment["amount"] or 0
        )

        if total_amount <= 0:
            raise ValueError(
                "Payment amount is invalid."
            )

        remaining_amount = (
            total_amount - already_refunded
        )

        if remaining_amount <= 0:
            raise ValueError(
                "Payment has already been fully refunded."
            )

        if refund_amount > remaining_amount:
            raise ValueError(
                "Refund amount exceeds remaining refundable amount."
            )

        refund_transaction_id = _clean_string(
            refund_transaction_id,
            "refund_transaction_id",
            max_length=255
        )

        new_refund_amount = (
            already_refunded + refund_amount
        )

        current_time = _current_time()

        if math.isclose(
            new_refund_amount,
            total_amount,
            rel_tol=0,
            abs_tol=0.01
        ):
            new_payment_status = "refunded"
            new_refund_status = "completed"

            final_refund_amount = total_amount

        else:
            new_payment_status = "partially_refunded"
            new_refund_status = "partial"

            final_refund_amount = new_refund_amount

        cursor.execute("""
            UPDATE payments
            SET
                payment_status = ?,
                refund_status = ?,
                refund_amount = ?,
                refund_transaction_id = COALESCE(
                    ?,
                    refund_transaction_id
                ),
                refunded_at = ?,
                updated_at = ?
            WHERE payment_id = ?
            AND deleted_at IS NULL
        """, (
            new_payment_status,
            new_refund_status,
            final_refund_amount,
            refund_transaction_id,
            current_time,
            current_time,
            payment_id
        ))

        cursor.execute("""
            UPDATE orders
            SET
                refund_amount = ?,
                payment_status = ?,
                refunded_at = ?,
                updated_at = ?
            WHERE order_id = ?
            AND deleted_at IS NULL
        """, (
            final_refund_amount,
            new_payment_status,
            current_time,
            current_time,
            payment["order_id"]
        ))

        connection.commit()

        return _get_payment_by_id_cursor(
            cursor,
            payment_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# VERIFY PAYMENT
# =========================================================

def verify_payment(
    payment_id,
    verification_status="verified"
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        verification_status = _validate_verification_status(
            verification_status
        )

        payment = _get_payment_cursor(
            cursor,
            payment_id
        )

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        current_time = _current_time()

        if verification_status == "verified":
            verified_at = current_time

        elif verification_status == "failed":
            verified_at = None

        else:
            verified_at = None

        cursor.execute("""
            UPDATE payments
            SET
                verification_status = ?,
                verified_at = ?,
                updated_at = ?
            WHERE payment_id = ?
            AND deleted_at IS NULL
        """, (
            verification_status,
            verified_at,
            current_time,
            payment_id
        ))

        connection.commit()

        return _get_payment_by_id_cursor(
            cursor,
            payment_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# PAYMENT WEBHOOK
# =========================================================

def process_webhook(
    payment_id,
    webhook_event_id,
    payment_status,
    gateway_payment_id=None,
    transaction_id=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        payment = _get_payment_cursor(
            cursor,
            payment_id
        )

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        webhook_event_id = _clean_string(
            webhook_event_id,
            "webhook_event_id",
            max_length=255,
            required=True
        )

        payment_status = _validate_payment_status(
            payment_status
        )

        gateway_payment_id = _clean_string(
            gateway_payment_id,
            "gateway_payment_id",
            max_length=255
        )

        transaction_id = _clean_string(
            transaction_id,
            "transaction_id",
            max_length=255
        )

        # -------------------------------------------------
        # WEBHOOK IDEMPOTENCY
        # -------------------------------------------------

        cursor.execute("""
            SELECT payment_id
            FROM payments
            WHERE webhook_event_id = ?
        """, (webhook_event_id,))

        existing_event = cursor.fetchone()

        if existing_event:
            if existing_event["payment_id"] != payment_id:
                raise ValueError(
                    "Webhook event is already associated "
                    "with another payment."
                )

            return dict(payment)

        # -------------------------------------------------
        # STATUS TRANSITION
        # -------------------------------------------------

        current_status = payment[
            "payment_status"
        ]

        _validate_status_transition(
            current_status,
            payment_status
        )

        current_time = _current_time()

        completed_at = None

        if payment_status == "captured":
            completed_at = current_time

        cursor.execute("""
            UPDATE payments
            SET
                payment_status = ?,
                gateway_payment_id = COALESCE(
                    ?,
                    gateway_payment_id
                ),
                transaction_id = COALESCE(
                    ?,
                    transaction_id
                ),
                webhook_received = 1,
                webhook_event_id = ?,
                webhook_received_at = ?,
                completed_at = COALESCE(
                    ?,
                    completed_at
                ),
                updated_at = ?
            WHERE payment_id = ?
            AND deleted_at IS NULL
        """, (
            payment_status,
            gateway_payment_id,
            transaction_id,
            webhook_event_id,
            current_time,
            completed_at,
            current_time,
            payment_id
        ))

        # -------------------------------------------------
        # UPDATE ORDER PAYMENT STATUS
        # -------------------------------------------------

        if payment_status == "captured":

            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'paid',
                    updated_at = ?
                WHERE order_id = ?
                AND deleted_at IS NULL
            """, (
                current_time,
                payment["order_id"]
            ))

        elif payment_status == "failed":

            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'failed',
                    updated_at = ?
                WHERE order_id = ?
                AND deleted_at IS NULL
            """, (
                current_time,
                payment["order_id"]
            ))

        elif payment_status == "cancelled":

            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'cancelled',
                    updated_at = ?
                WHERE order_id = ?
                AND deleted_at IS NULL
            """, (
                current_time,
                payment["order_id"]
            ))

        elif payment_status == "refunded":

            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'refunded',
                    updated_at = ?
                WHERE order_id = ?
                AND deleted_at IS NULL
            """, (
                current_time,
                payment["order_id"]
            ))

        elif payment_status == "partially_refunded":

            cursor.execute("""
                UPDATE orders
                SET
                    payment_status = 'partially_refunded',
                    updated_at = ?
                WHERE order_id = ?
                AND deleted_at IS NULL
            """, (
                current_time,
                payment["order_id"]
            ))

        connection.commit()

        return _get_payment_by_id_cursor(
            cursor,
            payment_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# DELETE PAYMENT
# =========================================================

def delete_payment(payment_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        payment = _get_payment_cursor(
            cursor,
            payment_id
        )

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        # -------------------------------------------------
        # PAYMENT RECORDS SHOULD NOT BE DELETED WHILE
        # A LIVE PAYMENT / REFUND PROCESS IS ACTIVE.
        # -------------------------------------------------

        if payment["payment_status"] in (
            "processing",
            "authorized"
        ):
            raise ValueError(
                "Processing or authorized payment "
                "cannot be deleted."
            )

        current_time = _current_time()

        cursor.execute("""
            UPDATE payments
            SET
                deleted_at = ?,
                updated_at = ?
            WHERE payment_id = ?
            AND deleted_at IS NULL
        """, (
            current_time,
            current_time,
            payment_id
        ))

        connection.commit()

        return {
            "success": True,
            "message": "Payment deleted successfully."
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
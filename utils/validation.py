import re
from datetime import datetime


# ============================================================
# REQUIRED VALUE
# ============================================================

def is_required(value):
    """
    Check whether a value is present and not empty.
    """
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


def validate_required(data, fields):
    """
    Returns a dictionary of missing required fields.
    """
    errors = {}

    for field in fields:
        if field not in data or not is_required(data[field]):
            errors[field] = f"{field} is required."

    return errors


# ============================================================
# STRING VALIDATION
# ============================================================

def validate_string(
    value,
    field_name="value",
    min_length=None,
    max_length=None
):
    if value is None:
        return f"{field_name} is required."

    if not isinstance(value, str):
        return f"{field_name} must be a string."

    value = value.strip()

    if min_length is not None and len(value) < min_length:
        return (
            f"{field_name} must be at least "
            f"{min_length} characters."
        )

    if max_length is not None and len(value) > max_length:
        return (
            f"{field_name} must not exceed "
            f"{max_length} characters."
        )

    return None


# ============================================================
# EMAIL VALIDATION
# ============================================================

def is_valid_email(email):
    if not email or not isinstance(email, str):
        return False

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return bool(
        re.fullmatch(pattern, email.strip())
    )


def validate_email(email):
    if not email:
        return "Email is required."

    if not is_valid_email(email):
        return "Invalid email address."

    return None


# ============================================================
# PHONE VALIDATION
# ============================================================

def is_valid_phone(phone):
    if not phone:
        return False

    phone = str(phone).strip()

    return bool(
        re.fullmatch(r"^\+?[0-9]{10,15}$", phone)
    )


def validate_phone(phone):
    if not phone:
        return "Phone number is required."

    if not is_valid_phone(phone):
        return "Invalid phone number."

    return None


# ============================================================
# PASSWORD VALIDATION
# ============================================================

def validate_password(
    password,
    min_length=8,
    max_length=128
):
    if not password:
        return "Password is required."

    if not isinstance(password, str):
        return "Password must be a string."

    if len(password) < min_length:
        return (
            f"Password must be at least "
            f"{min_length} characters."
        )

    if len(password) > max_length:
        return (
            f"Password must not exceed "
            f"{max_length} characters."
        )

    return None


# ============================================================
# INTEGER VALIDATION
# ============================================================

def is_valid_integer(value):
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def validate_integer(
    value,
    field_name="value",
    minimum=None,
    maximum=None
):
    if value is None:
        return f"{field_name} is required."

    try:
        number = int(value)
    except (TypeError, ValueError):
        return f"{field_name} must be an integer."

    if minimum is not None and number < minimum:
        return (
            f"{field_name} must be at least "
            f"{minimum}."
        )

    if maximum is not None and number > maximum:
        return (
            f"{field_name} must not exceed "
            f"{maximum}."
        )

    return None


# ============================================================
# FLOAT / NUMBER VALIDATION
# ============================================================

def is_valid_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def validate_number(
    value,
    field_name="value",
    minimum=None,
    maximum=None
):
    if value is None:
        return f"{field_name} is required."

    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"{field_name} must be a valid number."

    if minimum is not None and number < minimum:
        return (
            f"{field_name} must be at least "
            f"{minimum}."
        )

    if maximum is not None and number > maximum:
        return (
            f"{field_name} must not exceed "
            f"{maximum}."
        )

    return None


# ============================================================
# BOOLEAN VALIDATION
# ============================================================

def parse_boolean(value, default=None):
    """
    Converts common API boolean values into True/False.

    Examples:
        true, "true", 1, "1", yes, "on" -> True
        false, "false", 0, "0", no, "off" -> False
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        if value == 1:
            return True

        if value == 0:
            return False

    if isinstance(value, str):
        value = value.strip().lower()

        if value in {
            "true",
            "1",
            "yes",
            "y",
            "on"
        }:
            return True

        if value in {
            "false",
            "0",
            "no",
            "n",
            "off"
        }:
            return False

    return default


# ============================================================
# ENUM VALIDATION
# ============================================================

def validate_choice(
    value,
    allowed_values,
    field_name="value"
):
    if value is None:
        return f"{field_name} is required."

    if value not in allowed_values:
        return (
            f"Invalid {field_name}. "
            f"Allowed values: "
            f"{', '.join(map(str, allowed_values))}."
        )

    return None


# ============================================================
# ID VALIDATION
# ============================================================

def validate_id(
    value,
    field_name="id"
):
    if not value:
        return f"{field_name} is required."

    if not isinstance(value, str):
        return f"{field_name} must be a string."

    if not value.strip():
        return f"{field_name} cannot be empty."

    return None


# ============================================================
# UUID VALIDATION
# ============================================================

def is_valid_uuid(value):
    if not value:
        return False

    try:
        import uuid

        uuid.UUID(str(value))
        return True

    except (ValueError, TypeError, AttributeError):
        return False


# ============================================================
# DATE VALIDATION
# ============================================================

def is_valid_datetime(value):
    if not value:
        return False

    try:
        datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00"
            )
        )

        return True

    except ValueError:
        return False


def validate_datetime(
    value,
    field_name="datetime"
):
    if not value:
        return f"{field_name} is required."

    if not is_valid_datetime(value):
        return (
            f"Invalid {field_name} format. "
            f"Use ISO 8601 format."
        )

    return None


# ============================================================
# URL VALIDATION
# ============================================================

def is_valid_url(url):
    if not url or not isinstance(url, str):
        return False

    pattern = re.compile(
        r"^https?://"
        r"(?:[A-Za-z0-9-]+\.)+"
        r"[A-Za-z]{2,}"
        r"(?:/[^\s]*)?$"
    )

    return bool(
        pattern.match(url.strip())
    )


def validate_url(
    url,
    field_name="url",
    required=False
):
    if not url:
        if required:
            return f"{field_name} is required."

        return None

    if not is_valid_url(url):
        return f"Invalid {field_name}."

    return None


# ============================================================
# PAGINATION
# ============================================================

def validate_pagination(
    limit=50,
    offset=0,
    max_limit=100
):
    try:
        limit = int(limit)
        offset = int(offset)
    except (TypeError, ValueError):
        return {
            "valid": False,
            "message": "Limit and offset must be integers."
        }

    if limit < 1:
        return {
            "valid": False,
            "message": "Limit must be greater than zero."
        }

    if limit > max_limit:
        limit = max_limit

    if offset < 0:
        offset = 0

    return {
        "valid": True,
        "limit": limit,
        "offset": offset
    }


# ============================================================
# PRICE VALIDATION
# ============================================================

def validate_price(
    value,
    field_name="price",
    minimum=0
):
    return validate_number(
        value=value,
        field_name=field_name,
        minimum=minimum
    )


# ============================================================
# PERCENTAGE VALIDATION
# ============================================================

def validate_percentage(
    value,
    field_name="percentage"
):
    return validate_number(
        value=value,
        field_name=field_name,
        minimum=0,
        maximum=100
    )


# ============================================================
# PINCODE VALIDATION
# ============================================================

def is_valid_pincode(pincode):
    if not pincode:
        return False

    return bool(
        re.fullmatch(
            r"^[0-9]{6}$",
            str(pincode).strip()
        )
    )


def validate_pincode(pincode):
    if not pincode:
        return "Pincode is required."

    if not is_valid_pincode(pincode):
        return "Invalid pincode."

    return None


# ============================================================
# SLUG VALIDATION
# ============================================================

def is_valid_slug(slug):
    if not slug:
        return False

    return bool(
        re.fullmatch(
            r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
            str(slug).strip()
        )
    )


def validate_slug(slug):
    if not slug:
        return "Slug is required."

    if not is_valid_slug(slug):
        return (
            "Invalid slug. Use lowercase letters, "
            "numbers and hyphens only."
        )

    return None


# ============================================================
# MULTIPLE FIELD VALIDATION
# ============================================================

def collect_validation_errors(
    validations
):
    """
    validations example:

    {
        "email": validate_email(email),
        "phone": validate_phone(phone),
        "password": validate_password(password)
    }

    Returns only fields having errors.
    """

    errors = {}

    for field, error in validations.items():
        if error:
            errors[field] = error

    return errors


# ============================================================
# VALIDATION RESULT
# ============================================================

def is_valid_result(errors):
    return not bool(errors)
import re
import uuid
import secrets
import string
from datetime import datetime, timezone


# ============================================================
# DATETIME HELPERS
# ============================================================

def current_time():
    """
    Return current UTC time in ISO 8601 format.
    """
    return datetime.now(timezone.utc).isoformat()


def parse_datetime(value):
    """
    Safely parse ISO 8601 datetime.
    Returns datetime object or None.
    """
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        return None


# ============================================================
# ID GENERATION
# ============================================================

def generate_id(prefix=None, length=16):
    """
    Generate a unique ID.

    Example:
        generate_id("USR")
        -> USR-A8F21C9D12345678
    """

    unique_part = uuid.uuid4().hex[:length].upper()

    if prefix:
        return f"{prefix.upper()}-{unique_part}"

    return unique_part


def generate_uuid():
    """
    Generate standard UUID string.
    """
    return str(uuid.uuid4())


def generate_token(length=32):
    """
    Generate secure random token.
    """
    return secrets.token_urlsafe(length)


def generate_numeric_code(length=6):
    """
    Generate secure numeric OTP/code.
    """
    digits = string.digits

    return "".join(
        secrets.choice(digits)
        for _ in range(length)
    )


# ============================================================
# STRING HELPERS
# ============================================================

def clean_string(value):
    """
    Safely trim a string.
    """
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    return value.strip()


def normalize_email(email):
    """
    Normalize email for consistent storage/search.
    """
    if not email:
        return None

    return str(email).strip().lower()


def normalize_phone(phone):
    """
    Normalize phone number by removing spaces and dashes.
    """
    if not phone:
        return None

    phone = str(phone).strip()

    return re.sub(
        r"[\s\-()]",
        "",
        phone
    )


def normalize_code(code):
    """
    Normalize coupon/product/etc. codes.
    """
    if not code:
        return None

    return str(code).strip().upper()


# ============================================================
# SLUG HELPERS
# ============================================================

def generate_slug(value):
    """
    Convert text into URL-friendly slug.

    Example:
        "Samsung Galaxy S25 Ultra"
        -> "samsung-galaxy-s25-ultra"
    """

    if not value:
        return ""

    value = str(value).strip().lower()

    value = re.sub(
        r"[^a-z0-9\s-]",
        "",
        value
    )

    value = re.sub(
        r"[\s_-]+",
        "-",
        value
    )

    return value.strip("-")


# ============================================================
# NUMBER HELPERS
# ============================================================

def safe_int(
    value,
    default=0
):
    """
    Safely convert value to integer.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(
    value,
    default=0.0
):
    """
    Safely convert value to float.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(
    value,
    minimum=None,
    maximum=None
):
    """
    Keep a number inside a specified range.
    """

    if minimum is not None:
        value = max(
            value,
            minimum
        )

    if maximum is not None:
        value = min(
            value,
            maximum
        )

    return value


# ============================================================
# BOOLEAN HELPERS
# ============================================================

def to_bool(
    value,
    default=False
):
    """
    Safely convert common API values to boolean.
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
# PAGINATION HELPERS
# ============================================================

def get_pagination(
    limit=50,
    offset=0,
    max_limit=100
):
    """
    Normalize pagination values.
    """

    limit = safe_int(
        limit,
        50
    )

    offset = safe_int(
        offset,
        0
    )

    limit = max(
        1,
        min(limit, max_limit)
    )

    offset = max(
        0,
        offset
    )

    return {
        "limit": limit,
        "offset": offset
    }


def get_pagination_from_args(
    args,
    default_limit=50,
    max_limit=100
):
    """
    Extract pagination directly from Flask request.args.
    """

    return get_pagination(
        limit=args.get(
            "limit",
            default_limit
        ),
        offset=args.get(
            "offset",
            0
        ),
        max_limit=max_limit
    )


# ============================================================
# PRICE / MONEY HELPERS
# ============================================================

def round_money(
    value,
    decimals=2
):
    """
    Round monetary value.
    """
    return round(
        safe_float(value),
        decimals
    )


def calculate_discount_percentage(
    mrp,
    selling_price
):
    """
    Calculate discount percentage.

    Example:
        MRP = 1000
        Selling Price = 800
        Result = 20.0
    """

    mrp = safe_float(mrp)
    selling_price = safe_float(
        selling_price
    )

    if mrp <= 0:
        return 0.0

    discount = (
        (mrp - selling_price)
        / mrp
    ) * 100

    return round(
        max(discount, 0),
        2
    )


def calculate_discount_amount(
    mrp,
    selling_price
):
    """
    Calculate absolute discount amount.
    """

    mrp = safe_float(mrp)
    selling_price = safe_float(
        selling_price
    )

    return round_money(
        max(
            mrp - selling_price,
            0
        )
    )


# ============================================================
# FILE / IMAGE HELPERS
# ============================================================

def get_file_extension(filename):
    """
    Get file extension without dot.
    """
    if not filename:
        return ""

    filename = str(filename)

    if "." not in filename:
        return ""

    return filename.rsplit(
        ".",
        1
    )[1].lower()


def is_allowed_file_extension(
    filename,
    allowed_extensions
):
    """
    Check whether file extension is allowed.
    """

    extension = get_file_extension(
        filename
    )

    return extension in {
        str(ext).lower().lstrip(".")
        for ext in allowed_extensions
    }


def generate_filename(
    extension=None,
    prefix="file"
):
    """
    Generate unique filename.
    """

    unique_part = uuid.uuid4().hex

    if extension:
        extension = str(
            extension
        ).lstrip(".")

        return (
            f"{prefix}_"
            f"{unique_part}."
            f"{extension}"
        )

    return (
        f"{prefix}_"
        f"{unique_part}"
    )


# ============================================================
# DICTIONARY HELPERS
# ============================================================

def remove_none_values(data):
    """
    Remove keys whose values are None.
    """

    if not isinstance(data, dict):
        return data

    return {
        key: value
        for key, value in data.items()
        if value is not None
    }


def pick_fields(
    data,
    fields
):
    """
    Return only selected fields.
    """

    if not isinstance(data, dict):
        return {}

    return {
        field: data[field]
        for field in fields
        if field in data
    }


def exclude_fields(
    data,
    fields
):
    """
    Remove selected fields from dictionary.
    """

    if not isinstance(data, dict):
        return {}

    excluded = set(fields)

    return {
        key: value
        for key, value in data.items()
        if key not in excluded
    }


# ============================================================
# LIST HELPERS
# ============================================================

def unique_list(values):
    """
    Remove duplicate values while preserving order.
    """

    if not values:
        return []

    result = []
    seen = set()

    for value in values:

        if value in seen:
            continue

        seen.add(value)
        result.append(value)

    return result


# ============================================================
# TEXT HELPERS
# ============================================================

def truncate_text(
    text,
    max_length,
    suffix="..."
):
    """
    Safely truncate long text.
    """

    if text is None:
        return None

    text = str(text)

    if len(text) <= max_length:
        return text

    if max_length <= len(suffix):
        return text[:max_length]

    return (
        text[
            :max_length - len(suffix)
        ]
        + suffix
    )


# ============================================================
# SEARCH HELPERS
# ============================================================

def normalize_search_query(query):
    """
    Normalize search query.
    """

    if not query:
        return ""

    query = str(query).strip()

    query = re.sub(
        r"\s+",
        " ",
        query
    )

    return query


# ============================================================
# ORDER / STATUS HELPERS
# ============================================================

def is_status_in(
    status,
    allowed_statuses
):
    """
    Check whether status belongs
    to allowed status collection.
    """

    if not status:
        return False

    return status in allowed_statuses


# ============================================================
# DIFF / UPDATE HELPERS
# ============================================================

def get_changed_fields(
    old_data,
    new_data
):
    """
    Return fields whose values changed.
    """

    if not isinstance(old_data, dict):
        old_data = {}

    if not isinstance(new_data, dict):
        new_data = {}

    changed = {}

    for key, new_value in new_data.items():

        old_value = old_data.get(
            key
        )

        if old_value != new_value:
            changed[key] = new_value

    return changed
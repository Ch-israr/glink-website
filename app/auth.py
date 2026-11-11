"""Admin authentication.

Username is fixed to ``admin``. The password comes ONLY from the
ADMIN_PASSWORD environment variable — there is no default password and
login is refused outright when the variable is not set.

Sessions are a signed, timestamped cookie (itsdangerous), HttpOnly and
SameSite=Lax, valid for 12 hours.
"""
import hashlib
import hmac
import os

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SESSION_COOKIE = "glink_admin"
SESSION_MAX_AGE = 12 * 60 * 60  # 12 hours
ADMIN_USERNAME = "admin"


def _signing_key() -> str | None:
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        return None
    return hashlib.sha256(("glink-admin:" + password).encode("utf-8")).hexdigest()


def _serializer() -> URLSafeTimedSerializer | None:
    key = _signing_key()
    if key is None:
        return None
    return URLSafeTimedSerializer(key, salt="glink-admin-session")


def password_configured() -> bool:
    return bool(os.environ.get("ADMIN_PASSWORD"))


def check_login(username: str, password: str) -> bool:
    """True only when the admin password is configured and matches."""
    expected = os.environ.get("ADMIN_PASSWORD")
    if not expected:
        return False
    if username != ADMIN_USERNAME:
        return False
    return hmac.compare_digest(password, expected)


def create_session_token() -> str | None:
    serializer = _serializer()
    if serializer is None:
        return None
    return serializer.dumps({"user": ADMIN_USERNAME})


def verify_session_token(token: str | None) -> bool:
    if not token:
        return False
    serializer = _serializer()
    if serializer is None:
        return False
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return False
    return data.get("user") == ADMIN_USERNAME

"""Admin authentication.

Username is fixed to ``admin``. The password comes ONLY from the
ADMIN_PASSWORD environment variable — there is no default password and
login is refused outright when the variable is not set.

Sessions are a signed, timestamped cookie (itsdangerous), HttpOnly and
SameSite=Lax, valid for 12 hours. The token carries a random session id
(sid) that is also recorded server-side (see db.py): sign-out deletes
the row, so a signed-out token stops working immediately — logout is
no longer client-side only. Changing the password still invalidates
every session at once, because the signing key is derived from it.
"""
import hashlib
import hmac
import os
import secrets

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from . import db

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
    sid = secrets.token_urlsafe(24)
    db.add_session(sid)
    return serializer.dumps({"user": ADMIN_USERNAME, "sid": sid})


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
    if data.get("user") != ADMIN_USERNAME:
        return False
    sid = data.get("sid")
    if not sid or not db.session_exists(sid):
        return False
    return True


def revoke_session_token(token: str | None) -> None:
    """Delete the session row for this token, if it has a valid signature.

    Expiry is ignored here on purpose: signing out with an already
    expired token should still clear its row.
    """
    if not token:
        return
    serializer = _serializer()
    if serializer is None:
        return
    try:
        data = serializer.loads(token)
    except (BadSignature, SignatureExpired):
        return
    sid = data.get("sid")
    if sid:
        db.delete_session(sid)

"""Admin authentication.

Two kinds of accounts sign in on the same /admin login page:

- The built-in ``admin`` account. The password comes ONLY from the
  ADMIN_PASSWORD environment variable — there is no default password and
  login is refused outright when the variable is not set.
- Employee accounts stored in the database (see db.py), each with a
  username, a scrypt password hash and a role: ``admin``, ``sales``,
  ``accounts`` or ``viewer``. Only the built-in admin can manage users.

Sessions are a signed, timestamped cookie (itsdangerous), HttpOnly and
SameSite=Lax, valid for 12 hours. The token carries a random session id
(sid) that is also recorded server-side (see db.py): sign-out deletes
the row, so a signed-out token stops working immediately — logout is
no longer client-side only. Changing the built-in password still
invalidates every session at once, because the signing key is derived
from it. Resetting an employee's password or removing the account
revokes that user's sessions too.
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

# Employee roles. What each one may do:
#   admin    — everything, including managing users
#   sales    — view enquiries and prices, change nothing
#   accounts — view enquiries and prices, change nothing
#   viewer   — view sizes, prices, FAQ and business info, but NOT enquiries
ROLES = ("admin", "sales", "accounts", "viewer")
ROLES_THAT_VIEW_LEADS = ("admin", "sales", "accounts")


def hash_password(password: str) -> tuple[str, str]:
    """Scrypt-hash a password. Returns (salt_hex, hash_hex)."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=32
    )
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=32
    )
    return hmac.compare_digest(digest, expected)


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


def check_login(username: str, password: str) -> dict | None:
    """Verify a sign-in. Returns {"username", "role"} or None.

    The built-in ``admin`` account checks the ADMIN_PASSWORD env var.
    Any other username checks the database users table (must be active).
    """
    username = (username or "").strip()
    if username == ADMIN_USERNAME:
        expected = os.environ.get("ADMIN_PASSWORD")
        if not expected:
            return None
        if hmac.compare_digest(password, expected):
            return {"username": ADMIN_USERNAME, "role": "admin"}
        return None
    user = db.get_user(username)
    if user is None or not user["active"]:
        return None
    if user["role"] not in ROLES:
        return None
    if verify_password(password, user["salt"], user["password_hash"]):
        return {"username": user["username"], "role": user["role"]}
    return None


def create_session_token(user: dict) -> str | None:
    serializer = _serializer()
    if serializer is None:
        return None
    sid = secrets.token_urlsafe(24)
    db.add_session(sid, user["username"])
    return serializer.dumps({"user": user["username"], "role": user["role"], "sid": sid})


def get_session_user(token: str | None) -> dict | None:
    """The signed-in user ({"username", "role"}) or None."""
    if not token:
        return None
    serializer = _serializer()
    if serializer is None:
        return None
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    username = data.get("user")
    role = data.get("role")
    if not username or role not in ROLES:
        return None
    # The built-in admin always exists; employee accounts must still be
    # present and active, or their session is dead.
    if username != ADMIN_USERNAME:
        user = db.get_user(username)
        if user is None or not user["active"] or user["role"] != role:
            return None
    sid = data.get("sid")
    if not sid or not db.session_exists(sid):
        return None
    return {"username": username, "role": role}


def verify_session_token(token: str | None) -> bool:
    return get_session_user(token) is not None


def revoke_user_sessions(username: str) -> None:
    """Revoke every session of one user (password reset, deactivation, removal)."""
    db.delete_sessions_for_user(username)


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

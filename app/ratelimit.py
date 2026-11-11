"""Small in-memory rate limiting for the admin login and the public lead form.

This is a single-instance service (Render free plan = 1 instance), so
process memory is enough. State resets on restart/redeploy — a restart
clears any lockout; it never creates one.

Client IPs come from ``request.client.host``. Behind Render's proxy that
is only the real visitor IP because uvicorn runs with --proxy-headers
(see Dockerfile); without it every visitor would share the proxy's IP
and one lockout would lock everyone out.
"""
import threading
import time

_LOCK = threading.Lock()

LOGIN_MAX_FAILURES = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60  # 15 minutes

LEADS_MAX = 5
LEADS_WINDOW_SECONDS = 10 * 60  # 5 enquiries per IP per 10 minutes

_login_failures: dict[str, list[float]] = {}
_login_locked_until: dict[str, float] = {}
_lead_hits: dict[str, list[float]] = {}


def _prune(now: float, hits: list[float], window: float) -> list[float]:
    return [t for t in hits if now - t < window]


def login_locked(ip: str) -> float:
    """Seconds remaining on the login lockout for this IP, 0 when not locked."""
    now = time.monotonic()
    with _LOCK:
        until = _login_locked_until.get(ip, 0.0)
        if until <= now:
            return 0.0
        return until - now


def record_login_failure(ip: str) -> None:
    now = time.monotonic()
    with _LOCK:
        hits = _prune(now, _login_failures.get(ip, []), LOGIN_LOCKOUT_SECONDS)
        hits.append(now)
        _login_failures[ip] = hits
        if len(hits) >= LOGIN_MAX_FAILURES:
            _login_locked_until[ip] = now + LOGIN_LOCKOUT_SECONDS


def reset_login_failures(ip: str) -> None:
    with _LOCK:
        _login_failures.pop(ip, None)
        _login_locked_until.pop(ip, None)


def lead_allowed(ip: str) -> bool:
    """True and consume one slot when this IP may submit an enquiry now."""
    now = time.monotonic()
    with _LOCK:
        hits = _prune(now, _lead_hits.get(ip, []), LEADS_WINDOW_SECONDS)
        if len(hits) >= LEADS_MAX:
            return False
        hits.append(now)
        _lead_hits[ip] = hits
        return True

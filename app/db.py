"""SQLite storage for the Glink website.

Tables:
  sizes    - storage unit sizes and monthly "from" prices
  faq      - frequently asked questions shown on the site
  business - key/value business info (WhatsApp, address, rate)
  leads    - quote / contact form submissions
"""
import os
import sqlite3

DEFAULT_SIZES = [
    # (sqft, price_monthly_aed, label, sort_order)
    (50, 472.50, "Studio", 1),
    (80, 756.00, "Studio", 2),
    (100, 945.00, "1 Bedroom", 3),
    (150, 1417.50, "2 Bedroom", 4),
    (180, 1701.00, "2 Bedroom", 5),
]

DEFAULT_FAQ = [
    (
        "Where is Glink's storage facility?",
        "Our storage facility is in Al Sajaa, Sharjah — Plot No. 5108, Warehouse No. 4, "
        "Emirates Industrial City, P.O. Box 64479, Sharjah, UAE. Storage is only offered "
        "in Sharjah, Al Sajaa.",
    ),
    (
        "What storage sizes and prices do you offer?",
        "We offer five unit sizes: 50, 80, 100, 150 and 180 sqft. Storage starts from "
        "AED 9.45 per sqft including VAT — from AED 472.50/month for a 50 sqft unit, "
        "AED 756/month for 80 sqft, AED 945/month for 100 sqft, AED 1,417.50/month for "
        "150 sqft, and AED 1,701/month for 180 sqft. All prices are \"from\" prices, "
        "including VAT.",
    ),
    (
        "Do you offer moving services outside Sharjah?",
        "Yes. Our movers work all over the UAE — villas, apartments and offices — "
        "including packing, loading, transport and unpacking. Storage itself is only "
        "in Sharjah, Al Sajaa.",
    ),
    (
        "What can I store?",
        "Household items, furniture and seasonal gear for personal storage, and "
        "business inventory, documents and equipment for business storage. "
        "Message us on WhatsApp if you are unsure whether your items are suitable.",
    ),
    (
        "How do I get a quote or book a unit?",
        "Message us on WhatsApp at +971 52 923 1913 and tell us what you are storing "
        "or moving and which unit size you need. We will confirm availability and "
        "quote you — no obligation.",
    ),
]

DEFAULT_BUSINESS = {
    "business_name": "Glink Int'L Storage and movers",
    "whatsapp_number": "+971 52 923 1913",
    "whatsapp_link": "https://wa.me/971529231913",
    "address": "Plot No. 5108, Warehouse No. 4, Emirates Industrial City, P.O. Box 64479, Sharjah, UAE",
    "price_per_sqft": "9.45",
    "storage_location": "Al Sajaa, Sharjah",
}


def db_path() -> str:
    path = os.environ.get("DATABASE_PATH", "data/glink.db")
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = connect()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sqft INTEGER NOT NULL,
                price_monthly REAL NOT NULL,
                label TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS business (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                company TEXT NOT NULL DEFAULT '',
                size TEXT NOT NULL DEFAULT '',
                message TEXT NOT NULL DEFAULT '',
                referral_source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS sessions (
                sid TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        # Seed sizes once.
        if conn.execute("SELECT COUNT(*) FROM sizes").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO sizes (sqft, price_monthly, label, sort_order) VALUES (?, ?, ?, ?)",
                DEFAULT_SIZES,
            )
        # Seed FAQ once.
        if conn.execute("SELECT COUNT(*) FROM faq").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO faq (question, answer, sort_order) VALUES (?, ?, ?)",
                [(q, a, i + 1) for i, (q, a) in enumerate(DEFAULT_FAQ)],
            )
        # Seed business info; never overwrite values the admin has changed.
        for key, value in DEFAULT_BUSINESS.items():
            conn.execute(
                "INSERT OR IGNORE INTO business (key, value) VALUES (?, ?)", (key, value)
            )
        conn.commit()
    finally:
        conn.close()


def get_sizes() -> list[dict]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT id, sqft, price_monthly, label FROM sizes ORDER BY sort_order, sqft"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_faq() -> list[dict]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT id, question, answer FROM faq ORDER BY sort_order, id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_business() -> dict:
    conn = connect()
    try:
        rows = conn.execute("SELECT key, value FROM business").fetchall()
        out = dict(DEFAULT_BUSINESS)
        out.update({r["key"]: r["value"] for r in rows})
        return out
    finally:
        conn.close()


def get_leads(limit: int = 200) -> list[dict]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_lead(lead: dict) -> int:
    conn = connect()
    try:
        cur = conn.execute(
            """INSERT INTO leads
               (first_name, last_name, phone, email, company, size, message, referral_source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lead["first_name"],
                lead["last_name"],
                lead["phone"],
                lead.get("email", ""),
                lead.get("company", ""),
                lead.get("size", ""),
                lead.get("message", ""),
                lead.get("referral_source", ""),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_lead(lead_id: int) -> bool:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def replace_sizes(sizes: list[dict]) -> None:
    conn = connect()
    try:
        conn.execute("DELETE FROM sizes")
        for i, s in enumerate(sizes):
            conn.execute(
                "INSERT INTO sizes (sqft, price_monthly, label, sort_order) VALUES (?, ?, ?, ?)",
                (int(s["sqft"]), float(s["price_monthly"]), s.get("label", ""), i + 1),
            )
        conn.commit()
    finally:
        conn.close()


def replace_faq(items: list[dict]) -> None:
    conn = connect()
    try:
        conn.execute("DELETE FROM faq")
        for i, item in enumerate(items):
            conn.execute(
                "INSERT INTO faq (question, answer, sort_order) VALUES (?, ?, ?)",
                (item["question"], item["answer"], i + 1),
            )
        conn.commit()
    finally:
        conn.close()


def update_business(values: dict) -> None:
    allowed = set(DEFAULT_BUSINESS.keys())
    conn = connect()
    try:
        for key, value in values.items():
            if key in allowed:
                conn.execute(
                    "INSERT INTO business (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, str(value)),
                )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Admin sessions — server-side registry so sign-out actually revokes.
#
# The cookie token is still a signed, timestamped itsdangerous token, but
# it now carries a random session id (sid) that must exist in this table.
# Sign-out deletes the row, so a copied/old token stops working at once.
# Rows older than the 12h session lifetime are pruned on each sign-in.
# Stored in SQLite (not process memory) so sessions survive the free
# plan's idle sleep; like everything else on the free plan they reset
# on redeploy, when there is no persistent disk.
# ---------------------------------------------------------------------------

SESSION_LIFETIME_HOURS = 12


def prune_sessions() -> None:
    conn = connect()
    try:
        conn.execute(
            "DELETE FROM sessions WHERE created_at < datetime('now', ?)",
            (f"-{SESSION_LIFETIME_HOURS} hours",),
        )
        conn.commit()
    finally:
        conn.close()


def add_session(sid: str) -> None:
    prune_sessions()
    conn = connect()
    try:
        conn.execute("INSERT INTO sessions (sid) VALUES (?)", (sid,))
        conn.commit()
    finally:
        conn.close()


def session_exists(sid: str) -> bool:
    conn = connect()
    try:
        row = conn.execute("SELECT 1 FROM sessions WHERE sid = ?", (sid,)).fetchone()
        return row is not None
    finally:
        conn.close()


def delete_session(sid: str) -> None:
    conn = connect()
    try:
        conn.execute("DELETE FROM sessions WHERE sid = ?", (sid,))
        conn.commit()
    finally:
        conn.close()

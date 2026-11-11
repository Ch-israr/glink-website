"""Glink Int'L Storage and movers — website.

One FastAPI service serves the public site, the JSON content/lead API,
and the admin panel. Static assets (CSS/JS/images/fonts) live under
/app/static and are mounted at /static. Pages are server-rendered from
templates/ with live content (sizes, FAQ, business info) pulled from
SQLite; the frontend also fetches /api/content on load.
"""
import html
import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import auth, db

BASE = Path(__file__).resolve().parent.parent
TEMPLATES = BASE / "templates"

REFERRAL_SOURCES = [
    "Google Ads",
    "Facebook",
    "Instagram",
    "Movers",
    "Drive by Signboard DIP",
    "Friends or Family",
    "Employee Referrals",
    "Customer Referrals",
    "Others",
]

SIZE_IMAGES = {
    50: "real-50sqft-unit-clean.jpg",
    80: "real-80sqft-unit-clean.jpg",
    100: "real-100sqft-unit-clean.jpg",
    150: "real-150sqft-unit-clean.jpg",
    180: "180sqft-corridor-2048.jpg",
}

app = FastAPI(title="Glink Storage Website", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.on_event("startup")
def startup() -> None:
    db.init_db()


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _read_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def fmt_price(value: float) -> str:
    return f"AED {value:,.2f}"


def size_cards_html(sizes: list[dict]) -> str:
    cards = []
    for s in sizes:
        img = SIZE_IMAGES.get(int(s["sqft"]), "facility-interior-2048.jpg")
        note = (
            "Corridor view — our 180 sqft units are the largest we offer."
            if int(s["sqft"]) == 180
            else f"Our real {int(s['sqft'])} sqft unit at our Al Sajaa facility."
        )
        cards.append(
            f"""<article class="size-card" data-sqft="{int(s['sqft'])}">
              <img src="/static/images/{img}" alt="{int(s['sqft'])} sqft storage unit" loading="lazy">
              <div class="size-card-body">
                <h3>{int(s['sqft'])} sq ft</h3>
                <p class="size-label">{html.escape(s.get('label') or '')}</p>
                <p class="size-note">{note}</p>
                <p class="size-price">from {fmt_price(float(s['price_monthly']))}<span>/month</span></p>
                <p class="size-vat">incl. VAT</p>
                <a class="btn btn-primary" href="/book?size={int(s['sqft'])}">Book this size</a>
              </div>
            </article>"""
        )
    return "\n".join(cards)


def size_rows_html(sizes: list[dict]) -> str:
    rows = []
    for s in sizes:
        rows.append(
            f"""<tr>
              <td>{int(s['sqft'])} sq ft</td>
              <td>{html.escape(s.get('label') or '')}</td>
              <td>from {fmt_price(float(s['price_monthly']))} / month</td>
              <td><a class="btn btn-small" href="/book?size={int(s['sqft'])}">Book</a></td>
            </tr>"""
        )
    return "\n".join(rows)


def faq_html(faq: list[dict]) -> str:
    items = []
    for item in faq:
        items.append(
            f"""<details class="faq-item">
              <summary>{html.escape(item['question'])}</summary>
              <p>{html.escape(item['answer'])}</p>
            </details>"""
        )
    return "\n".join(items)


def size_options_html(sizes: list[dict]) -> str:
    options = ['<option value="">Not sure yet</option>']
    for s in sizes:
        options.append(
            f"<option value=\"{int(s['sqft'])}\">{int(s['sqft'])} sq ft — "
            f"from {fmt_price(float(s['price_monthly']))}/month</option>"
        )
    return "\n".join(options)


def render(name: str) -> HTMLResponse:
    """Render a page template with live content from the database."""
    sizes = db.get_sizes()
    faq = db.get_faq()
    biz = db.get_business()
    page = _read_template(name)
    page = page.replace("<!--HEADER-->", _read_template("header.html"))
    page = page.replace("<!--FOOTER-->", _read_template("footer.html"))
    tokens = {
        "{{BUSINESS_NAME}}": html.escape(biz["business_name"]),
        "{{WA_LINK}}": html.escape(biz["whatsapp_link"]),
        "{{WA_NUMBER}}": html.escape(biz["whatsapp_number"]),
        "{{ADDRESS}}": html.escape(biz["address"]),
        "{{PRICE_PER_SQFT}}": html.escape(biz["price_per_sqft"]),
        "{{STORAGE_LOCATION}}": html.escape(biz["storage_location"]),
        "{{SIZE_CARDS}}": size_cards_html(sizes),
        "{{SIZE_ROWS}}": size_rows_html(sizes),
        "{{FAQ_ITEMS}}": faq_html(faq),
        "{{SIZE_OPTIONS}}": size_options_html(sizes),
    }
    for token, value in tokens.items():
        page = page.replace(token, value)
    return HTMLResponse(page)


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return render("home.html")


@app.get("/personal", response_class=HTMLResponse)
def personal():
    return render("personal.html")


@app.get("/business", response_class=HTMLResponse)
def business():
    return render("business.html")


@app.get("/size-guide", response_class=HTMLResponse)
def size_guide():
    return render("size-guide.html")


@app.get("/logistics", response_class=HTMLResponse)
def logistics():
    return render("logistics.html")


@app.get("/about", response_class=HTMLResponse)
def about():
    return render("about.html")


@app.get("/gallery", response_class=HTMLResponse)
def gallery():
    return render("gallery.html")


@app.get("/book", response_class=HTMLResponse)
def book():
    return render("book.html")


@app.get("/contact", response_class=HTMLResponse)
def contact():
    return render("contact.html")


@app.get("/privacy", response_class=HTMLResponse)
def privacy():
    return render("privacy.html")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/content")
def content():
    return {
        "sizes": db.get_sizes(),
        "faq": db.get_faq(),
        "business": db.get_business(),
        "referral_sources": REFERRAL_SOURCES,
    }


class LeadIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=5, max_length=30)
    email: str = Field(default="", max_length=200)
    company: str = Field(default="", max_length=200)
    size: str = Field(default="", max_length=20)
    message: str = Field(default="", max_length=2000)
    referral_source: str = Field(default="", max_length=50)


@app.post("/api/leads")
def create_lead(lead: LeadIn):
    if lead.referral_source and lead.referral_source not in REFERRAL_SOURCES:
        return JSONResponse(
            {"ok": False, "error": "Unknown referral source."}, status_code=400
        )
    lead_id = db.add_lead(lead.model_dump())
    return {"ok": True, "id": lead_id}


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

def _is_admin(request: Request) -> bool:
    return auth.verify_session_token(request.cookies.get(auth.SESSION_COOKIE))


def _admin_required(request: Request):
    if not _is_admin(request):
        return JSONResponse({"ok": False, "error": "Not signed in."}, status_code=401)
    return None


def _render_admin_login(error: str = "") -> HTMLResponse:
    page = _read_template("admin-login.html")
    page = page.replace("{{ERROR}}", f'<p class="error">{html.escape(error)}</p>' if error else "")
    return HTMLResponse(page)


@app.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request):
    if not _is_admin(request):
        return _render_admin_login()
    page = _read_template("admin.html")
    page = page.replace("{{WA_LINK}}", html.escape(db.get_business()["whatsapp_link"]))
    return HTMLResponse(page)


@app.post("/admin/login", response_class=HTMLResponse)
def admin_login(username: str = Form(...), password: str = Form(...)):
    if not auth.password_configured():
        return _render_admin_login(
            "Admin login is not configured on this server: the ADMIN_PASSWORD "
            "environment variable is not set. Set it and restart the service."
        )
    if not auth.check_login(username, password):
        return _render_admin_login("Invalid username or password.")
    token = auth.create_session_token()
    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie(
        auth.SESSION_COOKIE,
        token,
        max_age=auth.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/admin",
    )
    return response


@app.post("/admin/logout")
def admin_logout():
    response = RedirectResponse("/admin", status_code=303)
    response.delete_cookie(auth.SESSION_COOKIE, path="/admin")
    return response


@app.get("/admin/api/leads")
def admin_list_leads(request: Request):
    denied = _admin_required(request)
    if denied is not None:
        return denied
    return {"ok": True, "leads": db.get_leads()}


@app.delete("/admin/api/leads/{lead_id}")
def admin_delete_lead(request: Request, lead_id: int):
    denied = _admin_required(request)
    if denied is not None:
        return denied
    if not db.delete_lead(lead_id):
        return JSONResponse({"ok": False, "error": "Lead not found."}, status_code=404)
    return {"ok": True}


class SizesIn(BaseModel):
    sizes: list[dict]


@app.put("/admin/api/sizes")
def admin_save_sizes(request: Request, payload: SizesIn):
    denied = _admin_required(request)
    if denied is not None:
        return denied
    try:
        cleaned = [
            {
                "sqft": int(s["sqft"]),
                "price_monthly": float(s["price_monthly"]),
                "label": str(s.get("label", "")),
            }
            for s in payload.sizes
        ]
    except (KeyError, TypeError, ValueError):
        return JSONResponse(
            {"ok": False, "error": "Each size needs sqft and price_monthly."},
            status_code=400,
        )
    if not cleaned:
        return JSONResponse(
            {"ok": False, "error": "At least one size is required."}, status_code=400
        )
    db.replace_sizes(cleaned)
    return {"ok": True, "sizes": db.get_sizes()}


class FaqIn(BaseModel):
    faq: list[dict]


@app.put("/admin/api/faq")
def admin_save_faq(request: Request, payload: FaqIn):
    denied = _admin_required(request)
    if denied is not None:
        return denied
    try:
        cleaned = [
            {"question": str(i["question"]).strip(), "answer": str(i["answer"]).strip()}
            for i in payload.faq
        ]
    except (KeyError, TypeError):
        return JSONResponse(
            {"ok": False, "error": "Each FAQ entry needs a question and an answer."},
            status_code=400,
        )
    cleaned = [c for c in cleaned if c["question"] and c["answer"]]
    db.replace_faq(cleaned)
    return {"ok": True, "faq": db.get_faq()}


class BusinessIn(BaseModel):
    business: dict


@app.put("/admin/api/business")
def admin_save_business(request: Request, payload: BusinessIn):
    denied = _admin_required(request)
    if denied is not None:
        return denied
    db.update_business(payload.business)
    return {"ok": True, "business": db.get_business()}

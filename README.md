# Glink Int'L Storage and movers — Website

A complete, deployable website for Glink Int'L Storage and movers:
movers all over the UAE, storage only in Sharjah, Al Sajaa.

One FastAPI service serves the public site, the JSON content/lead API,
and the admin panel. Stack: Python FastAPI + SQLite (stdlib `sqlite3`) +
vanilla HTML/CSS/JS — no frontend build step.

## Pages

Home, Personal, Business, Size Guide, Logistics, About, Gallery,
Book/Select Size, Contact, Privacy. No blog.

Design follows the competitor-site reverse-engineering (navy `#0C1B33`, orange
`#E8820C`, off-white `#FAFAF8`, DM Sans + DM Serif Display, self-hosted).
All copy, prices, photos and contact details are Glink's own. Quote and
contact forms save the enquiry in SQLite and then open WhatsApp with the
message pre-filled — no email sending.

## Run locally

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
ADMIN_PASSWORD="$(cat ADMIN_PASSWORD.txt)" .venv/bin/python run.py
```

Then open http://127.0.0.1:8000. The admin panel is at
http://127.0.0.1:8000/admin (username `admin`, password from
`ADMIN_PASSWORD.txt`).

A strong random admin password was generated during the build and saved
to `ADMIN_PASSWORD.txt` (gitignored, never commit it). To use a different
password, set the `ADMIN_PASSWORD` environment variable.

## Environment variables

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `ADMIN_PASSWORD` | Yes, for admin login | — | If unset, admin login is refused with a clear error. No default password exists. |
| `DATABASE_PATH` | No | `data/glink.db` | SQLite file. Created on first run and seeded with the Glink sizes, FAQ and business info. |
| `PORT` | No | `8000` | Port the server listens on (Render sets this automatically). |

## Admin panel (`/admin`)

Sign in with username `admin` and the `ADMIN_PASSWORD`. The session is a
signed, HttpOnly, SameSite=Lax cookie, valid for 12 hours. The dashboard
lets you:

1. Edit storage sizes and monthly "from" prices — the live site updates
   immediately (the public pages and `GET /api/content` read from the DB).
2. Edit FAQ entries.
3. Edit business info (WhatsApp number/link, address, price per sqft).
4. View enquiry submissions (newest first) and delete them.

All admin mutations require a valid session.

## API

- `GET /api/health` — `{"ok": true}`
- `GET /api/content` — sizes, FAQ, business info, referral sources
- `POST /api/leads` — JSON body: `first_name`, `last_name`, `phone`,
  `email` (optional), `company` (optional), `size`, `message`,
  `referral_source` (one of: Google Ads, Facebook, Instagram, Movers,
  Drive by Signboard DIP, Friends or Family, Employee Referrals, Customer
  Referrals, Others). Returns `{"ok": true, "id": <n>}`.

## Deploy on Render

1. Push this folder to a GitHub repository.
2. In Render, create a **Web Service** from that repository:
   - Runtime: **Docker** (the `Dockerfile` is included).
   - No build command is needed; Docker handles it.
3. Set these environment variables on the service:
   - `ADMIN_PASSWORD` — copy the value from `ADMIN_PASSWORD.txt`
     (generate a fresh one if you prefer: `python3 -c "import secrets; print(secrets.token_urlsafe(24))"`).
   - `DATABASE_PATH` — `/app/data/glink.db` (already the Docker default).
4. **Important:** Render's filesystem is ephemeral — the SQLite file is
   lost on every restart/redeploy unless you attach a **persistent disk**
   to the service (Render dashboard → service → Disks) mounted at
   `/app/data`. Without a disk, sizes/FAQ/business edits and leads reset
   to the seeded defaults on each deploy. Attach the disk before the
   first deploy if you want admin edits and leads to survive.
5. Deploy. The service listens on Render's `PORT` automatically.

## Project layout

```
app/
  main.py      # FastAPI app: pages, /api/*, /admin
  db.py        # SQLite schema, seeding, queries
  auth.py      # admin password + signed session cookie
static/
  css/style.css
  js/site.js   # content refresh, lead form, size picker
  js/admin.js  # admin dashboard
  images/      # real Glink facility/unit photos (10 files)
  fonts/       # DM Sans + DM Serif Display (self-hosted woff2)
templates/     # server-rendered pages + admin pages
data/          # SQLite database (created at runtime, gitignored)
Dockerfile
requirements.txt
run.py
ADMIN_PASSWORD.txt   # generated admin password (gitignored)
```

## Facts used (the only ones on the site)

- Movers: all over the UAE. Storage: ONLY in Sharjah, Al Sajaa.
- From AED 9.45/sqft incl. VAT. Sizes: 50 → AED 472.50, 80 → 756,
  100 → 945, 150 → 1,417.50, 180 → 1,701 per month (all "from").
- WhatsApp +971 52 923 1913 (https://wa.me/971529231913) — the only
  contact route. No email, no landline.
- Address: Plot No. 5108, Warehouse No. 4, Emirates Industrial City,
  P.O. Box 64479, Sharjah, UAE.

Nothing unverified is claimed on the site: no security or access claims,
no climate or pest-control claims, no lock-and-key claims, no packing or
shipping claims, no insurance claims, and no reviews or ratings.

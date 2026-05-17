"""
alerts.py
---------
Email alert subscription management for NET-EA.

Endpoints:
  POST   /alerts/subscribe          -- create or update a subscription
  DELETE /alerts/unsubscribe/{email} -- remove a subscription
  GET    /alerts/subscriptions       -- list all subscriptions (admin)

Email sending is triggered from main.py on each EONET refresh
when new events are detected that match a subscriber's filters.

Configure via environment variables:
  SMTP_HOST  (default: smtp.gmail.com)
  SMTP_PORT  (default: 587)
  SMTP_USER  -- your Gmail / SMTP username
  SMTP_PASS  -- app password (not your account password)
  SMTP_FROM  -- sender address shown in emails

Gmail setup:
  1. Enable 2-factor authentication
  2. Create an App Password at myaccount.google.com/apppasswords
  3. Set SMTP_USER=you@gmail.com SMTP_PASS=<app_password>
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = logging.getLogger("alerts")
router = APIRouter(prefix="/alerts", tags=["alerts"])

# -- Storage ------------------------------------------------------------------
SUBS_FILE = Path(__file__).parents[2] / "data" / "subscriptions.json"

def load_subs() -> list[dict]:
    if not SUBS_FILE.exists():
        return []
    try:
        return json.loads(SUBS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_subs(subs: list[dict]) -> None:
    SUBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUBS_FILE.write_text(json.dumps(subs, indent=2), encoding="utf-8")

# -- Models -------------------------------------------------------------------
class SubscriptionIn(BaseModel):
    email:      str
    categories: list[str] = []
    countries:  list[str] = []   # ISO2 codes; empty = all countries

# -- Endpoints ----------------------------------------------------------------
@router.post("/subscribe")
def subscribe(sub: SubscriptionIn):
    if "@" not in sub.email:
        raise HTTPException(400, "Invalid email address")
    subs = [s for s in load_subs() if s["email"] != sub.email]
    subs.append({
        "email":      sub.email,
        "categories": sub.categories,
        "countries":  sub.countries,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    save_subs(subs)
    log.info("Subscribed: %s  categories=%s  countries=%s",
             sub.email, sub.categories, sub.countries)
    return {"message": "Subscribed successfully", "email": sub.email}


@router.delete("/unsubscribe/{email}")
def unsubscribe(email: str):
    subs = [s for s in load_subs() if s["email"] != email]
    save_subs(subs)
    log.info("Unsubscribed: %s", email)
    return {"message": "Unsubscribed", "email": email}


@router.get("/subscriptions")
def list_subscriptions():
    return load_subs()


# -- Email sending ------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@net-ea.org")

COUNTRY_NAMES = {
    "DJ":"Djibouti", "ER":"Eritrea",     "ET":"Ethiopia",
    "KE":"Kenya",    "RW":"Rwanda",      "SO":"Somalia",
    "SS":"South Sudan","SD":"Sudan",     "TZ":"Tanzania",
    "UG":"Uganda",   "BI":"Burundi",
}

COUNTRY_BBOX = {
    "SD":{"minLat":9,"maxLat":22,"minLon":21,"maxLon":38},
    "SS":{"minLat":3,"maxLat":12,"minLon":24,"maxLon":36},
    "ET":{"minLat":3,"maxLat":15,"minLon":33,"maxLon":48},
    "ER":{"minLat":12,"maxLat":18,"minLon":36,"maxLon":44},
    "DJ":{"minLat":10,"maxLat":13,"minLon":41,"maxLon":44},
    "SO":{"minLat":-2,"maxLat":12,"minLon":40,"maxLon":52},
    "KE":{"minLat":-5,"maxLat":5,"minLon":33,"maxLon":42},
    "UG":{"minLat":-2,"maxLat":4,"minLon":29,"maxLon":35},
    "TZ":{"minLat":-12,"maxLat":0,"minLon":29,"maxLon":41},
    "RW":{"minLat":-3,"maxLat":0,"minLon":28,"maxLon":31},
    "BI":{"minLat":-5,"maxLat":-2,"minLon":28,"maxLon":31},
}


def _event_country(ev) -> Optional[str]:
    coords = ev.primary_coords
    if not coords:
        return None
    lon, lat = coords[0], coords[1]
    for iso, b in COUNTRY_BBOX.items():
        if b["minLon"] <= lon <= b["maxLon"] and b["minLat"] <= lat <= b["maxLat"]:
            return iso
    return None


def _event_matches(ev, sub: dict) -> bool:
    # Returns True if a new event should alert this subscriber.
    if sub.get("categories") and ev.primary_category not in sub["categories"]:
        return False
    if sub.get("countries"):
        country = _event_country(ev)
        if country not in sub["countries"]:
            return False
    return True


def _build_email(new_events: list, subscriber: dict) -> str:
    # Build a plain-text email body.
    lines = [
        "NET-EA -- Natural Event Tracker for East Africa",
        "",
        f"New events detected ({len(new_events)}):",
        "",
    ]
    for ev in new_events[:10]:
        country = COUNTRY_NAMES.get(_event_country(ev) or "", "")
        date    = (getattr(ev, "latest_date", "") or "")[:10]
        lines.append(f"  - [{ev.primary_category}] {ev.title}")
        if country:
            lines.append(f"    Country: {country}")
        if date:
            lines.append(f"    Date: {date}")
        if ev.link:
            lines.append(f"    Link: {ev.link}")
        lines.append("")

    lines += [
        "---",
        "You are receiving this because you subscribed at NET-EA.",
        "To unsubscribe, visit the Alerts section of the dashboard.",
    ]
    return "\n".join(lines)


def send_alerts(new_events: list) -> None:
    # Called from main.py after each EONET refresh.
    # Sends emails to subscribers whose filters match.
    # Silently skips if SMTP is not configured.
    if not SMTP_USER or not SMTP_PASS:
        log.debug("SMTP not configured -- skipping alert emails")
        return

    subs = load_subs()
    if not subs:
        return

    for sub in subs:
        matched = [ev for ev in new_events if _event_matches(ev, sub)]
        if not matched:
            continue

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"NET-EA: {len(matched)} new event{'s' if len(matched) > 1 else ''} detected"
        msg["From"]    = SMTP_FROM
        msg["To"]      = sub["email"]

        body = _build_email(matched, sub)
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_FROM, [sub["email"]], msg.as_string())
            log.info("Alert sent to %s (%d events)", sub["email"], len(matched))
        except Exception as exc:
            log.warning("Failed to send alert to %s: %s", sub["email"], exc)

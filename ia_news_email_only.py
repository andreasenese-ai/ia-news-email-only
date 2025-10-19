#!/usr/bin/env python3
# ia_news_email_only.py
"""
Agente notizie IA (solo email), per GitHub Actions a 07:50 Europe/Rome.
Deduplica per giorno locale per evitare doppio invio.
"""

import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import feedparser
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
import smtplib

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=intelligenza+artificiale&hl=it&gl=IT&ceid=IT:it",
    "https://news.google.com/rss/search?q=AI+enterprise&hl=en-US&gl=US&ceid=US:en",
]
MAX_ITEMS_PER_RUN = 25
SEEN_FILE = "seen.json"
LAST_SENT_FILE = "last_sent.json"
TZ = ZoneInfo("Europe/Rome")
USER_AGENT = "PRAMAC-IA-NewsAgent/1.0"

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER or "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def today_local():
    return datetime.now(TZ).strftime("%Y-%m-%d")

def already_sent_today():
    data = load_json(LAST_SENT_FILE, {})
    return data.get("date") == today_local()

def mark_sent_today():
    save_json(LAST_SENT_FILE, {"date": today_local()})

def sha(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def fetch_snippet(url: str, max_chars: int = 260) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        p = soup.find("p")
        txt = (p.get_text(" ", strip=True) if p else "").strip()
        if not txt:
            return ""
        return (txt[:max_chars] + ("…" if len(txt) > max_chars else ""))
    except Exception:
        return ""

def gather_items():
    seen = set(load_json(SEEN_FILE, []))
    items = []
    for feed in RSS_FEEDS:
        parsed = feedparser.parse(feed)
        source = parsed.feed.get("title", feed) if getattr(parsed, "feed", None) else feed
        for e in parsed.entries[:MAX_ITEMS_PER_RUN]:
            url = e.get("link") or e.get("id")
            if not url:
                continue
            uid = sha(url)
            if uid in seen:
                continue
            title = (e.get("title") or "").strip() or "(senza titolo)"
            published = e.get("published", e.get("updated", ""))
            snippet = (e.get("summary") or "").strip()
            if not snippet:
                snippet = fetch_snippet(url)
            items.append({
                "id": uid,
                "title": title,
                "url": url,
                "source": source,
                "published": published,
                "snippet": snippet
            })
    return items

def build_email(items):
    if not items:
        return None, None
    now_local = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    subject = f"[IA News] {len(items)} novità — {now_local} Europe/Rome"
    lines = [f"Riepilogo notizie IA — {now_local} Europe/Rome", ""]
    for it in items:
        lines += [
            f"• {it['title']}",
            f"  Sorgente: {it['source']}",
            f"  Pubblicato: {it['published'] or 'N/D'}",
            f"  {it['snippet']}" if it['snippet'] else "  (aprire il link per i dettagli)",
            f"  Link: {it['url']}",
            ""
        ]
    return subject, "\n".join(lines).strip()

def send_email(subject, body):
    if not (SMTP_HOST and SMTP_PORT and EMAIL_FROM and EMAIL_TO):
        raise RuntimeError("Config SMTP mancante: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, EMAIL_TO")
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=25) as s:
        s.ehlo()
        s.starttls()
        if SMTP_USER and SMTP_PASS:
            s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())

def main():
    if already_sent_today():
        print("Già inviata oggi (Europe/Rome).")
        return
    items = gather_items()
    seen = set(load_json(SEEN_FILE, []))
    for it in items:
        seen.add(it["id"])
    save_json(SEEN_FILE, sorted(list(seen)))
    subject, body = build_email(items)
    if subject and body:
        send_email(subject, body)
        print("Email inviata.")
    else:
        print("Nessuna novità.")
    mark_sent_today()

if __name__ == "__main__":
    main()

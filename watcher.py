#!/usr/bin/env python3
import os
import sys
import hashlib
import requests
import time
import json
from urllib.parse import urlparse
from datetime import datetime

URLS = [
    "https://www.castleschool.co.uk/calendar/academic-year-diary.htm",
    "https://www.castleschool.co.uk/uploads/pdf-files/1055-Academic_Year_Diary_202526.pdf",
]

STATE_DIR = os.path.join(os.path.dirname(__file__), "state")
os.makedirs(STATE_DIR, exist_ok=True)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def fn_from_url(url: str) -> str:
    p = urlparse(url)
    slug = p.path.strip("/").replace("/", "_")
    if not slug:
        slug = p.netloc
    return slug

def fetch(url: str):
    # Try HEAD for Last-Modified/ETag first
    headers = {"User-Agent": "calendar-watcher/1.0"}
    head = requests.head(url, allow_redirects=True, timeout=30, headers=headers)
    last_mod = head.headers.get("Last-Modified")
    etag = head.headers.get("ETag")
    # Always GET body to hash (HEAD on some hosts is unreliable)
    r = requests.get(url, allow_redirects=True, timeout=60, headers=headers)
    r.raise_for_status()
    content = r.content
    return content, last_mod, etag

def send_telegram(msg: str):
    if not (BOT_TOKEN and CHAT_ID):
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set; skipping Telegram notify.")
        return False
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "disable_web_page_preview": True}
    resp = requests.post(api, json=payload, timeout=30)
    try:
        ok = resp.json().get("ok", False)
    except Exception:
        ok = False
    if not ok:
        print(f"Telegram send failed: {resp.status_code} {resp.text}")
    return ok

def main():
    any_changes = False
    changes = []
    for url in URLS:
        content, last_mod, etag = fetch(url)
        digest = sha256_bytes(content)
        base = fn_from_url(url)
        hash_path = os.path.join(STATE_DIR, base + ".sha256")
        meta_path = os.path.join(STATE_DIR, base + ".json")

        prev_hash = None
        if os.path.exists(hash_path):
            prev_hash = open(hash_path, "r").read().strip()

        if prev_hash != digest:
            any_changes = True
            changes.append({
                "url": url,
                "previous": prev_hash,
                "current": digest,
                "last_modified": last_mod,
                "etag": etag,
            })
            with open(hash_path, "w") as f:
                f.write(digest)

        meta = {
            "url": url,
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "last_modified": last_mod,
            "etag": etag,
            "sha256": digest,
            "size_bytes": len(content),
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2, sort_keys=True)

    if any_changes:
        items = []
        for c in changes:
            lm = f" (Last-Modified: {c['last_modified']})" if c.get("last_modified") else ""
            items.append(f"• {c['url']}{lm}")
        msg = "Castle School calendar updated\n" + "\n".join(items)
        print(msg)
        send_telegram(msg)
    else:
        print("No changes detected.")

    # Exit 0 even if changed, so Action doesn't fail
    return 0

if __name__ == "__main__":
    sys.exit(main())

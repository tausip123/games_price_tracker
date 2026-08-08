"""
Play Store Price Drop Tracker
------------------------------
Checks the price of a fixed list of apps (apps.json) once a day,
compares against the last known price (stored in prices.db, an
SQLite file committed back to the repo by the GitHub Action),
and sends a Telegram message if the price has dropped.

In-app purchase prices are intentionally ignored - only the base
app price (what you pay to install it) is tracked.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

import requests
from google_play_scraper import app as gp_app

APPS_FILE = "apps.json"
DB_FILE = "prices.db"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def init_db(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            package_id TEXT PRIMARY KEY,
            country TEXT,
            price REAL,
            currency TEXT,
            last_checked TEXT
        )
        """
    )
    conn.commit()


def load_apps():
    with open(APPS_FILE, "r") as f:
        return json.load(f)


def get_current_price(package_id, country):
    """Fetch base app price only. Ignores IAP entirely."""
    data = gp_app(package_id, lang="en", country=country)
    price = data.get("price", 0.0)      # 0.0 if free
    currency = data.get("currency", "USD")
    return price, currency


def get_stored_price(conn, package_id):
    row = conn.execute(
        "SELECT price, currency FROM prices WHERE package_id = ?",
        (package_id,),
    ).fetchone()
    return row  # None if never checked before


def save_price(conn, package_id, country, price, currency):
    conn.execute(
        """
        INSERT INTO prices (package_id, country, price, currency, last_checked)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(package_id) DO UPDATE SET
            price=excluded.price,
            currency=excluded.currency,
            last_checked=excluded.last_checked
        """,
        (package_id, country, price, currency, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[warn] Telegram not configured, skipping notification:")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[error] Failed to send Telegram message: {e}")


def main():
    apps = load_apps()
    conn = sqlite3.connect(DB_FILE)
    init_db(conn)

    for entry in apps:
        package_id = entry["package_id"]
        country = entry.get("country", "us")

        try:
            current_price, currency = get_current_price(package_id, country)
        except Exception as e:
            print(f"[error] Could not fetch price for {package_id}: {e}")
            continue

        stored = get_stored_price(conn, package_id)

        if stored is None:
            print(f"[baseline] {package_id}: {current_price} {currency} (first check, no notification)")
        else:
            old_price, old_currency = stored
            if current_price < old_price:
                msg = (
                    f"Price drop! {package_id}\n"
                    f"{old_price} {old_currency} -> {current_price} {currency}"
                )
                print(f"[drop] {msg}")
                send_telegram_message(msg)
            else:
                print(f"[no change] {package_id}: {current_price} {currency}")

        save_price(conn, package_id, country, current_price, currency)

    conn.close()


if __name__ == "__main__":
    main()

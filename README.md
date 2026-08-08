# Play Store Price Drop Tracker

Tracks the base price of a fixed list of Play Store apps and notifies you on
Telegram when the price drops. In-app purchase prices are ignored on
purpose. Runs daily via GitHub Actions — no server needed.

## 1. Install dependencies (for local testing)

```bash
pip install -r requirements.txt --break-system-packages
```

## 2. Add the apps you want to track

Edit `apps.json`. `package_id` is the app's Play Store ID (found in the
Play Store URL, e.g. `https://play.google.com/store/apps/details?id=com.spotify.music`
-> `com.spotify.music`). `country` is a 2-letter country code (prices can
differ by region).

```json
[
  { "package_id": "com.spotify.music", "country": "us" }
]
```

## 3. Get your Telegram bot token and chat ID

Since you already have a bot, you just need two things:

- **Bot token**: message **@BotFather** on Telegram, send `/mybots`, pick
  your bot, and grab the token (or check wherever you saved it when you
  created it).
- **Chat ID**: send any message to your bot, then run:

```bash
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
```

Look for `"chat":{"id": 123456789, ...}` in the JSON output — that number
is your chat ID.

## 4. Test it locally (optional but recommended)

```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
export TELEGRAM_CHAT_ID="123456789"
python3 track_prices.py
```

First run just records current prices as a baseline (no notification —
nothing to compare against yet). Run it again after manually editing a
price in `prices.db` if you want to confirm a notification actually fires,
or just wait for a real price drop.

## 5. Push this to a GitHub repo

```bash
cd playstore-tracker
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## 6. Add your bot token and chat ID as repo secrets

In your GitHub repo: **Settings -> Secrets and variables -> Actions ->
New repository secret**. Add two secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## 7. That's it — the workflow is already set up

`.github/workflows/daily.yml` is included and will:

- Run automatically every day at 9am UTC (edit the `cron:` line in that
  file to change the time — cron times are always UTC).
- Install dependencies, run `track_prices.py`, and send you a Telegram
  message if any tracked app's price dropped.
- Commit the updated `prices.db` back into the repo so tomorrow's run has
  today's price to compare against.
- Can also be triggered manually anytime from the **Actions** tab in
  your repo (click the workflow, then "Run workflow").

You don't need to do anything else — once the secrets are set and it's
pushed, it just runs daily on its own.

## Notes

- Prices can vary by country — the `country` field per app controls this.
- If an app is free with no paid version, price will just always be `0.0`
  and never trigger a drop. This tracker is really about apps that have a
  fixed paid price, not IAP-based freemium apps.
- `google-play-scraper` is unofficial and reads the public Play Store page.
  If Google changes their page structure it could break — if you start
  seeing `[error] Could not fetch price` for everything, update it:

```bash
pip install -U google-play-scraper --break-system-packages
```

- To add or remove tracked apps later, just edit `apps.json`, commit, and
  push — no other changes needed.

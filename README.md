# Gold Price Tracker 🪙

[![CI](https://github.com/yamanperker123/price_tracking/actions/workflows/ci.yml/badge.svg)](https://github.com/yamanperker123/price_tracking/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A small bot that tracks the **gram gold price (TRY)** and sends an **SMS** to registered phone numbers when the price drops to or below their target.

> Altın fiyatlarını takip edip fiyat belirlenen seviyenin altına düşünce kayıtlı telefonlara SMS gönderen bot.

## Features

- Fetches the live gram gold price from a free Turkish market feed
- Each phone number has its **own target price**
- Sends an SMS via **Twilio** (or prints to the console for local testing)
- **No spam:** one alert per drop. The alert re-arms once the price goes back above the target
- Failed SMS are retried on the next check
- Stores subscribers and price history in **SQLite**
- Simple CLI, Docker image, unit tests and GitHub Actions CI

## How it works

```
 ┌──────────────┐   every N sec   ┌──────────────┐   price <= target   ┌──────────────┐
 │ Price feed   │ ──────────────▶ │ GoldTracker  │ ──────────────────▶ │ SMS (Twilio) │
 │ (gram altın) │                 │              │                     └──────────────┘
 └──────────────┘                 └──────┬───────┘
                                         │ subscribers, price history
                                         ▼
                                  ┌──────────────┐
                                  │   SQLite     │
                                  └──────────────┘
```

| Module | Responsibility |
|---|---|
| `price_sources.py` | Fetches and parses the gold price |
| `notifiers.py` | Sends messages (Twilio SMS or console) |
| `storage.py` | SQLite access, phone number validation |
| `tracker.py` | Decides who gets an alert |
| `cli.py` | Command line interface |

Price sources and notifiers are small interfaces (`Protocol`s), so a new SMS provider or price feed can be added without touching the core logic.

## Getting started

### 1. Install

```bash
git clone https://github.com/yamanperker123/price_tracking.git
cd price_tracking
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
```

By default `NOTIFIER=console`, so messages are printed to the terminal. To send real SMS, create a free [Twilio](https://www.twilio.com/try-twilio) account and fill in:

```env
NOTIFIER=twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
```

> On a Twilio trial account you can only send SMS to numbers you have verified in the Twilio console.

### 3. Use

```bash
# Add a phone number with a target price (TRY)
python -m gold_tracker add 05551112233 --target 6200

# See the current price
python -m gold_tracker price

# Check once and send alerts if needed
python -m gold_tracker check

# Keep running, checking every 5 minutes
python -m gold_tracker run --interval 300

# Other commands
python -m gold_tracker list
python -m gold_tracker history --limit 10
python -m gold_tracker remove 05551112233
```

Example SMS:

```
Altın alarmı: Gram altın 6.150,25 TL seviyesine düştü. Hedefiniz: 6.200,00 TL.
```

## Run with Docker

```bash
docker build -t gold-tracker .

# add a number (data is kept in the ./data folder)
docker run --rm --env-file .env -v "$(pwd)/data:/app/data" gold-tracker add 05551112233 --target 6200

# start tracking
docker run -d --name gold-tracker --env-file .env -v "$(pwd)/data:/app/data" gold-tracker
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `NOTIFIER` | `console` | `console` or `twilio` |
| `TWILIO_ACCOUNT_SID` | – | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | – | Twilio auth token |
| `TWILIO_FROM_NUMBER` | – | Your Twilio phone number |
| `CHECK_INTERVAL_SECONDS` | `300` | Seconds between checks in `run` mode |
| `DB_PATH` | `data/gold_tracker.db` | SQLite file |
| `PRICE_SOURCE_URL` | Truncgil feed | Price feed URL |
| `GOLD_SYMBOL` | `GRA` | Instrument code in the feed (gram gold) |
| `PRICE_FIELD` | `Selling` | `Buying` or `Selling` price |

## Tests

```bash
pip install -r requirements-dev.txt
pytest -v
ruff check .
```

Tests use fake price sources and mocked HTTP calls, so they run offline and never send real SMS.

## Roadmap

- [ ] Percentage-drop alerts (e.g. "notify me if it falls 2% in a day")
- [ ] More instruments (çeyrek altın, USD/TRY)
- [ ] Telegram notifier
- [ ] Small web page to manage subscriptions

## License

[MIT](LICENSE)

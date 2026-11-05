"""Command line interface: python -m gold_tracker <command>."""

from __future__ import annotations

import argparse
import logging
import sys

from .config import Settings
from .notifiers import ConsoleNotifier, Notifier, TwilioSmsNotifier
from .price_sources import PriceSourceError, TruncgilPriceSource
from .storage import Storage
from .tracker import GoldTracker, format_try


def build_notifier(settings: Settings) -> Notifier:
    if settings.notifier == "twilio":
        return TwilioSmsNotifier(
            settings.twilio_account_sid or "",
            settings.twilio_auth_token or "",
            settings.twilio_from_number or "",
        )
    if settings.notifier == "console":
        return ConsoleNotifier()
    raise ValueError(f"Unknown notifier: {settings.notifier}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gold_tracker",
        description="Track gram gold price and get an SMS when it drops below your target.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a phone number with a target price")
    add.add_argument("phone", help="e.g. +905551112233 or 05551112233")
    add.add_argument("--target", type=float, required=True, help="Target price in TRY")

    remove = sub.add_parser("remove", help="Remove a phone number")
    remove.add_argument("phone")

    sub.add_parser("list", help="List phone numbers and their targets")
    sub.add_parser("price", help="Show the current gram gold price")
    sub.add_parser("check", help="Check the price once and send alerts")

    run = sub.add_parser("run", help="Keep checking the price on an interval")
    run.add_argument("--interval", type=int, help="Seconds between checks")

    history = sub.add_parser("history", help="Show recent price checks")
    history.add_argument("--limit", type=int, default=20)

    return parser


def main(argv: list[str] | None = None, settings: Settings | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = settings or Settings.from_env()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    storage = Storage(settings.db_path)
    source = TruncgilPriceSource(
        settings.price_source_url, settings.gold_symbol, settings.price_field
    )

    try:
        if args.command == "add":
            sub = storage.add_subscriber(args.phone, args.target)
            print(f"Added {sub.phone} with target {format_try(sub.target_price)}")
        elif args.command == "remove":
            if storage.remove_subscriber(args.phone):
                print(f"Removed {args.phone}")
            else:
                print(f"{args.phone} was not found")
                return 1
        elif args.command == "list":
            subscribers = storage.list_subscribers()
            if not subscribers:
                print("No phone numbers yet. Add one with: add <phone> --target <price>")
            for s in subscribers:
                status = "alert sent" if s.notified else "waiting"
                print(f"{s.phone:<16} target {format_try(s.target_price):>14}  ({status})")
        elif args.command == "price":
            print(f"Gram gold: {format_try(source.get_price())}")
        elif args.command == "history":
            for point in storage.price_history(args.limit):
                print(f"{point.checked_at}  {format_try(point.price)}")
        else:
            tracker = GoldTracker(source, build_notifier(settings), storage)
            if args.command == "check":
                result = tracker.check_once()
                print(
                    f"Price: {format_try(result.price)} | "
                    f"alerts sent: {len(result.notified)} | failed: {len(result.failed)}"
                )
            else:
                tracker.run_forever(args.interval or settings.check_interval_seconds)
    except (ValueError, PriceSourceError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        storage.close()
    return 0

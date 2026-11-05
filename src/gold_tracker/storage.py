"""SQLite storage for subscribers and price history."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscribers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    phone        TEXT    NOT NULL UNIQUE,
    target_price REAL    NOT NULL CHECK (target_price > 0),
    notified     INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS price_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    price      REAL NOT NULL,
    checked_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Subscriber:
    id: int
    phone: str
    target_price: float
    notified: bool


@dataclass(frozen=True)
class PricePoint:
    price: float
    checked_at: str


def normalize_phone(phone: str) -> str:
    """Return the phone number in E.164 format. Turkish numbers like 0555... are accepted."""
    digits = re.sub(r"[\s\-()]", "", phone)
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = "+90" + digits[1:]
    elif digits.startswith("5") and len(digits) == 10:
        digits = "+90" + digits

    if not PHONE_PATTERN.match(digits):
        raise ValueError(f"Invalid phone number: {phone}")
    return digits


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Storage:
    def __init__(self, db_path: str) -> None:
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # Subscribers -----------------------------------------------------------

    def add_subscriber(self, phone: str, target_price: float) -> Subscriber:
        phone = normalize_phone(phone)
        if target_price <= 0:
            raise ValueError("Target price must be greater than 0")
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO subscribers (phone, target_price, notified, created_at)
                VALUES (?, ?, 0, ?)
                ON CONFLICT(phone) DO UPDATE
                    SET target_price = excluded.target_price, notified = 0
                """,
                (phone, target_price, _now()),
            )
        return self.get_subscriber(phone)

    def get_subscriber(self, phone: str) -> Subscriber:
        row = self.conn.execute(
            "SELECT * FROM subscribers WHERE phone = ?", (normalize_phone(phone),)
        ).fetchone()
        if row is None:
            raise KeyError(phone)
        return self._to_subscriber(row)

    def remove_subscriber(self, phone: str) -> bool:
        with self.conn:
            cursor = self.conn.execute(
                "DELETE FROM subscribers WHERE phone = ?", (normalize_phone(phone),)
            )
        return cursor.rowcount > 0

    def list_subscribers(self) -> list[Subscriber]:
        rows = self.conn.execute("SELECT * FROM subscribers ORDER BY id").fetchall()
        return [self._to_subscriber(row) for row in rows]

    def set_notified(self, subscriber_id: int, notified: bool) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE subscribers SET notified = ? WHERE id = ?",
                (int(notified), subscriber_id),
            )

    @staticmethod
    def _to_subscriber(row: sqlite3.Row) -> Subscriber:
        return Subscriber(
            id=row["id"],
            phone=row["phone"],
            target_price=row["target_price"],
            notified=bool(row["notified"]),
        )

    # Price history ---------------------------------------------------------

    def save_price(self, price: float) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO price_history (price, checked_at) VALUES (?, ?)",
                (price, _now()),
            )

    def price_history(self, limit: int = 20) -> list[PricePoint]:
        rows = self.conn.execute(
            "SELECT price, checked_at FROM price_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [PricePoint(row["price"], row["checked_at"]) for row in rows]

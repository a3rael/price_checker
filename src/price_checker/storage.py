import sqlite3
from datetime import UTC, datetime

from price_checker.models import PriceItem, ProductRecord


def current_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def create_products_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            old_price REAL NOT NULL,
            new_price REAL NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute("PRAGMA table_info(products)")
    columns = {row[1] for row in cursor.fetchall()}

    if "created_at" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN created_at TEXT")

    if "updated_at" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN updated_at TEXT")

    timestamp = current_timestamp()
    cursor.execute(
        """
        UPDATE products
        SET created_at = COALESCE(created_at, ?),
            updated_at = COALESCE(updated_at, ?)
        """,
        (timestamp, timestamp),
    )
    conn.commit()


def save_items(conn: sqlite3.Connection, items: list[PriceItem]) -> int:
    cursor = conn.cursor()

    for item in items:
        timestamp = current_timestamp()
        cursor.execute(
            """
            INSERT INTO products (
                sku, name, old_price, new_price, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                name = excluded.name,
                old_price = excluded.old_price,
                new_price = excluded.new_price,
                updated_at = excluded.updated_at
            """,
            (
                item.sku,
                item.name,
                item.old_price,
                item.new_price,
                timestamp,
                timestamp,
            ),
        )

    conn.commit()
    return len(items)


def count_products(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    row = cursor.fetchone()
    return row[0]


def load_items_from_db(conn: sqlite3.Connection) -> list[PriceItem]:
    cursor = conn.cursor()
    cursor.execute("SELECT sku, name, old_price, new_price FROM products")

    rows = cursor.fetchall()
    items: list[PriceItem] = []

    for row in rows:
        items.append(
            PriceItem(
                sku=row[0],
                name=row[1],
                old_price=row[2],
                new_price=row[3],
            )
        )

    return items


def load_product_records(conn: sqlite3.Connection) -> list[ProductRecord]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sku, name, old_price, new_price, created_at, updated_at
        FROM products
        ORDER BY sku
        """
    )

    rows = cursor.fetchall()
    records: list[ProductRecord] = []

    for row in rows:
        records.append(
            ProductRecord(
                sku=row[0],
                name=row[1],
                old_price=row[2],
                new_price=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        )

    return records

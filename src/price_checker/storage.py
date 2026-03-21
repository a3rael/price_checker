import sqlite3

from price_checker.models import PriceItem


def create_products_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT NOT NULL,
        name TEXT NOT NULL,
        old_price REAL NOT NULL,
        new_price REAL NOT NULL
    )
    """)
    conn.commit()

def save_items(conn: sqlite3.Connection, items: list[PriceItem]) -> int:
    cursor = conn.cursor()

    for item in items:
        cursor.execute(
            """
            INSERT INTO products (sku, name, old_price, new_price)
            VALUES (?, ?, ?, ?)
            """,
            (item.sku, item.name, item.old_price, item.new_price),
        )

    conn.commit()
    return len(items)

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
import sqlite3
from unittest.mock import patch

from price_checker.models import PriceItem
from price_checker.storage import (
    count_products,
    create_products_table,
    load_items_from_db,
    load_product_records,
    save_items,
)


def test_create_products_table_adds_timestamp_columns():
    conn = sqlite3.connect(":memory:")

    create_products_table(conn)

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(products)")
    columns = {row[1] for row in cursor.fetchall()}

    assert "created_at" in columns
    assert "updated_at" in columns


def test_save_items_stores_timestamps():
    conn = sqlite3.connect(":memory:")
    create_products_table(conn)

    with patch(
        "price_checker.storage.current_timestamp",
        return_value="2026-03-21T10:00:00+00:00",
    ):
        saved_count = save_items(
            conn,
            [PriceItem(sku="1001", name="Товар", old_price=100.0, new_price=120.0)],
        )

    cursor = conn.cursor()
    cursor.execute(
        "SELECT sku, created_at, updated_at FROM products WHERE sku = ?",
        ("1001",),
    )
    row = cursor.fetchone()

    assert saved_count == 1
    assert row == (
        "1001",
        "2026-03-21T10:00:00+00:00",
        "2026-03-21T10:00:00+00:00",
    )


def test_save_items_updates_updated_at_and_preserves_created_at():
    conn = sqlite3.connect(":memory:")
    create_products_table(conn)

    with patch(
        "price_checker.storage.current_timestamp",
        side_effect=[
            "2026-03-21T10:00:00+00:00",
            "2026-03-21T11:30:00+00:00",
        ],
    ):
        save_items(
            conn,
            [PriceItem(sku="1001", name="Товар", old_price=100.0, new_price=120.0)],
        )
        save_items(
            conn,
            [PriceItem(sku="1001", name="Товар 2", old_price=120.0, new_price=140.0)],
        )

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name, old_price, new_price, created_at, updated_at
        FROM products
        WHERE sku = ?
        """,
        ("1001",),
    )
    row = cursor.fetchone()

    assert row == (
        "Товар 2",
        120.0,
        140.0,
        "2026-03-21T10:00:00+00:00",
        "2026-03-21T11:30:00+00:00",
    )


def test_load_items_from_db_returns_price_items():
    conn = sqlite3.connect(":memory:")
    create_products_table(conn)
    save_items(
        conn,
        [
            PriceItem(sku="1001", name="Товар", old_price=100.0, new_price=120.0),
            PriceItem(sku="1002", name="Тест", old_price=50.0, new_price=45.0),
        ],
    )

    items = load_items_from_db(conn)

    assert items == [
        PriceItem(sku="1001", name="Товар", old_price=100.0, new_price=120.0),
        PriceItem(sku="1002", name="Тест", old_price=50.0, new_price=45.0),
    ]
    assert count_products(conn) == 2


def test_load_product_records_returns_timestamps():
    conn = sqlite3.connect(":memory:")
    create_products_table(conn)

    with patch(
        "price_checker.storage.current_timestamp",
        return_value="2026-03-21T10:00:00+00:00",
    ):
        save_items(
            conn,
            [PriceItem(sku="1001", name="Товар", old_price=100.0, new_price=120.0)],
        )

    records = load_product_records(conn)

    assert len(records) == 1
    assert records[0].sku == "1001"
    assert records[0].created_at == "2026-03-21T10:00:00+00:00"
    assert records[0].updated_at == "2026-03-21T10:00:00+00:00"

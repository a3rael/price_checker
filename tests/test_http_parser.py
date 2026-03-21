from unittest.mock import Mock, patch

import pytest

from price_checker.http_parser import (
    HTTPDataError,
    extract_items,
    fetch_json,
    load_http_items,
)
from price_checker.models import PriceItem


def test_extract_items_supports_list():
    data = [{"sku": "1001", "name": "Товар", "old_price": "100", "new_price": "90"}]

    result = extract_items(data)

    assert result == data


def test_extract_items_supports_items_field():
    data = {
        "items": [
            {"sku": "1001", "name": "Товар", "old_price": "100", "new_price": "90"}
        ]
    }

    result = extract_items(data)

    assert result == data["items"]


def test_extract_items_rejects_non_object_elements():
    with pytest.raises(HTTPDataError, match="Каждый элемент JSON должен быть объектом"):
        extract_items(["invalid"])


@patch("price_checker.http_parser.requests.get")
def test_fetch_json_returns_response_json(mock_get):
    response = Mock()
    response.json.return_value = {"items": []}
    response.raise_for_status.return_value = None
    mock_get.return_value = response

    result = fetch_json("https://example.com/api/prices")

    assert result == {"items": []}
    mock_get.assert_called_once_with("https://example.com/api/prices", timeout=10.0)


@patch("price_checker.http_parser.requests.get")
def test_load_http_items_parses_valid_json_items(mock_get):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = [
        {"sku": "1001", "name": "Товар", "old_price": "100", "new_price": "120"},
        {"sku": "1002", "name": "Тест", "old_price": "50", "new_price": "45"},
    ]
    mock_get.return_value = response

    items, skipped_count = load_http_items("https://example.com/api/prices")

    assert items == [
        PriceItem(sku="1001", name="Товар", old_price=100.0, new_price=120.0),
        PriceItem(sku="1002", name="Тест", old_price=50.0, new_price=45.0),
    ]
    assert skipped_count == 0


@patch("price_checker.http_parser.requests.get")
def test_load_http_items_skips_invalid_items(mock_get, capsys):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = [
        {"sku": "1001", "name": "Товар", "old_price": "100", "new_price": "120"},
        {"sku": "", "name": "Ошибка", "old_price": "50", "new_price": "45"},
    ]
    mock_get.return_value = response

    items, skipped_count = load_http_items("https://example.com/api/prices")

    assert items == [
        PriceItem(sku="1001", name="Товар", old_price=100.0, new_price=120.0)
    ]
    assert skipped_count == 1
    assert "Элемент 2 пропущен: SKU не может быть пустым" in capsys.readouterr().out

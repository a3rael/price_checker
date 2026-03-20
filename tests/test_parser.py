import pytest

from price_checker.models import PriceItem
from price_checker.parser import (
    parse_row,
    parse_row_data,
    validate_row_data,
    RowValidationError,
)


def test_parse_row_data_extracts_values():
    row = {
        "sku": "1001",
        "name": "Товар",
        "old_price": "100",
        "new_price": "120.5",
    }

    result = parse_row_data(row)

    assert result == {
        "sku": "1001",
        "name": "Товар",
        "old_price": 100.0,
        "new_price": 120.5,
    }


def test_parse_row_data_requires_fields():
    row = {
        "sku": "1001",
        "name": "Товар",
        "old_price": "100",
    }

    with pytest.raises(RowValidationError, match="Отсутствует обязательное поле"):
        parse_row_data(row)


def test_validate_row_data_rejects_empty_sku():
    with pytest.raises(RowValidationError, match="SKU не может быть пустым"):
        validate_row_data(
            sku="",
            name="Товар",
            old_price=100,
            new_price=120,
        )


def test_validate_row_data_rejects_negative_new_price():
    with pytest.raises(
        RowValidationError, match="new_price не может быть отрицательной"
    ):
        validate_row_data(
            sku="1001",
            name="Товар",
            old_price=100,
            new_price=-1,
        )


def test_validate_row_data_rejects_zero_old_price():
    with pytest.raises(RowValidationError, match="old_price не может быть равен 0"):
        validate_row_data(
            sku="1001",
            name="Товар",
            old_price=0,
            new_price=120,
        )


def test_parse_row_builds_price_item():
    row = {
        "sku": "1001",
        "name": "Товар",
        "old_price": "100",
        "new_price": "120",
    }

    result = parse_row(row)

    assert result == PriceItem(
        sku="1001",
        name="Товар",
        old_price=100.0,
        new_price=120.0,
    )

import pytest

from price_checker.models import PriceItem
from price_checker.pricing import is_suspicious_change, price_change_pct


def test_price_change_pct_growth():
    result = price_change_pct(100, 120)
    assert result == 20.0


def test_price_change_pct_drop():
    result = price_change_pct(200, 150)
    assert result == -25.0


def test_price_change_pct_zero_old_price():
    with pytest.raises(ValueError):
        price_change_pct(0, 100)


def test_is_suspicious_change_true():
    item = PriceItem(
        sku="1001",
        name="Тест",
        old_price=100,
        new_price=130,
    )
    assert is_suspicious_change(item) is True


def test_is_suspicious_change_false():
    item = PriceItem(
        sku="1002",
        name="Тест",
        old_price=100,
        new_price=110,
    )
    assert is_suspicious_change(item) is False

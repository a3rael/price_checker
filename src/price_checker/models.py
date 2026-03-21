from dataclasses import dataclass


@dataclass
class PriceItem:
    sku: str
    name: str
    old_price: float
    new_price: float


@dataclass
class ProductRecord:
    sku: str
    name: str
    old_price: float
    new_price: float
    created_at: str
    updated_at: str

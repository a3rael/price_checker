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

@dataclass
class PipelineResult:
    received_count: int
    valid_count: int
    skipped_count: int
    saved_count: int
    total_in_db: int
    suspicious_count: int
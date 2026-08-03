from __future__  import annotations
from dataclasses import dataclass, field


@dataclass 
class SourceConfig:
    name:str
    file_name:str
    key_column:str
    required_columns:tuple[str,...]
    date_columns:tuple[str,...]=field(default_factory=tuple)
    chunk_size:int=5000


ORDERS = SourceConfig(
    name="orders",
    file_name="olist_orders_dataset.csv",
    key_column="order_id",
    required_columns=("order_id", "customer_id", "order_status"),
    date_columns=("order_purchase_timestamp", "order_delivered_customer_date"),
)

ORDER_ITEMS = SourceConfig(
    name="order_items",
    file_name="olist_order_items_dataset.csv",
    key_column="order_id",
    required_columns=("order_id", "product_id", "price", "freight_value"),
)

PAYMENTS = SourceConfig(
    name="payments",
    file_name="olist_order_payments_dataset.csv",
    key_column="order_id",
    required_columns=("order_id", "payment_type", "payment_value"),
)

CUSTOMERS = SourceConfig(
    name="customers",
    file_name="olist_customers_dataset.csv",
    key_column="customer_id",
    required_columns=("customer_id", "customer_city", "customer_state"),
)

PRODUCTS = SourceConfig(
    name="products",
    file_name="olist_products_dataset.csv",
    key_column="product_id",
    required_columns=("product_id", "product_category_name"),
)
ALL_SOURCES: tuple[SourceConfig, ...] = (ORDERS, ORDER_ITEMS, PAYMENTS, CUSTOMERS, PRODUCTS)

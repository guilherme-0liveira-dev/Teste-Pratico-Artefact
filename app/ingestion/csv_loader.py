"""Idempotent CSV Ingestion Pipeline with schema validation and Decimal normalization."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models import Category, Customer, Order, OrderItem, Product, Promotion


def parse_decimal(value: Any) -> Decimal:
    """Parse numeric or string values into exact Decimal amounts."""
    if pd.isna(value) or value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    # Clean string format (e.g., '1.299,00' or '1299.0' or 'R$ 599.9')
    val_str = str(value).replace("R$", "").replace(" ", "").strip()
    # If standard comma decimal (e.g. 599,90) without dots:
    if "," in val_str and "." not in val_str:
        val_str = val_str.replace(",", ".")
    # If Brazilian format with thousand dot and comma decimal (e.g. 1.499,50)
    elif "." in val_str and "," in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    try:
        return Decimal(val_str).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        logger.warning(f"Failed to parse decimal from '{value}', defaulting to 0.00")
        return Decimal("0.00")


def parse_date(value: Any) -> datetime.date | None:
    """Parse dates formatted as YYYY-MM-DD or DD/MM/YYYY into date objects."""
    if pd.isna(value) or not value or str(value).strip() == "":
        return None
    val_str = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    logger.warning(f"Could not parse date string: {value}")
    return None


class CSVIngestionService:
    """Service to discover, validate, and load operational CSV data into SQLite."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or settings.DATA_DIR

    def find_csv_file(self, base_name: str) -> Path | None:
        """Search for CSV file matching base_name or 'desafio_tecnico_ai_eng - {base_name}'."""
        candidates = [
            self.data_dir / f"{base_name}.csv",
            self.data_dir / f"desafio_tecnico_ai_eng - {base_name}.csv",
            settings.BASE_DIR / f"{base_name}.csv",
            settings.BASE_DIR / f"desafio_tecnico_ai_eng - {base_name}.csv",
        ]
        for path in candidates:
            if path.exists() and path.is_file():
                return path
        return None

    def ingest_categories(self, db: Session) -> int:
        file_path = self.find_csv_file("categories")
        if not file_path:
            logger.warning("categories.csv not found, skipping.")
            return 0

        df = pd.read_csv(file_path)
        count = 0
        for _, row in df.iterrows():
            cat_id = int(row["category_id"])
            name = str(row["name"]).strip()
            desc = str(row["description"]).strip() if pd.notna(row.get("description")) else None

            existing = db.query(Category).filter(Category.category_id == cat_id).first()
            if existing:
                existing.name = name
                existing.description = desc
            else:
                db.add(Category(category_id=cat_id, name=name, description=desc))
            count += 1
        db.commit()
        logger.info(f"Ingested {count} categories from {file_path.name}")
        return count

    def ingest_products(self, db: Session) -> int:
        file_path = self.find_csv_file("products")
        if not file_path:
            logger.warning("products.csv not found, skipping.")
            return 0

        df = pd.read_csv(file_path)
        count = 0
        for _, row in df.iterrows():
            prod_id = int(row["product_id"])
            price = parse_decimal(row["price_brl"])
            name = str(row["name"]).strip()
            cat_id = int(row["category_id"])
            desc = str(row["description"]).strip() if pd.notna(row.get("description")) else None
            stock = int(row["stock_quantity"]) if pd.notna(row.get("stock_quantity")) else 0
            status = str(row.get("status", "active")).strip()
            specs = str(row["specs"]).strip() if pd.notna(row.get("specs")) else None
            created = parse_date(row.get("created_at"))

            existing = db.query(Product).filter(Product.product_id == prod_id).first()
            if existing:
                existing.name = name
                existing.price_brl = price
                existing.category_id = cat_id
                existing.description = desc
                existing.stock_quantity = stock
                existing.status = status
                existing.specs = specs
                existing.created_at = created
            else:
                db.add(
                    Product(
                        product_id=prod_id,
                        name=name,
                        price_brl=price,
                        category_id=cat_id,
                        description=desc,
                        stock_quantity=stock,
                        status=status,
                        specs=specs,
                        created_at=created,
                    )
                )
            count += 1
        db.commit()
        logger.info(f"Ingested {count} products from {file_path.name}")
        return count

    def ingest_customers(self, db: Session) -> int:
        file_path = self.find_csv_file("customers")
        if not file_path:
            logger.warning("customers.csv not found, skipping.")
            return 0

        df = pd.read_csv(file_path)
        count = 0
        for _, row in df.iterrows():
            cust_id = int(row["customer_id"])
            name = str(row["name"]).strip()
            phone = str(row["phone"]).strip() if pd.notna(row.get("phone")) else None
            email = str(row["email"]).strip() if pd.notna(row.get("email")) else ""
            city = str(row["city"]).strip() if pd.notna(row.get("city")) else None

            existing = db.query(Customer).filter(Customer.customer_id == cust_id).first()
            if existing:
                existing.name = name
                existing.phone = phone
                existing.email = email
                existing.city = city
            else:
                db.add(
                    Customer(customer_id=cust_id, name=name, phone=phone, email=email, city=city)
                )
            count += 1
        db.commit()
        logger.info(f"Ingested {count} customers from {file_path.name}")
        return count

    def ingest_orders(self, db: Session) -> int:
        file_path = self.find_csv_file("orders")
        if not file_path:
            logger.warning("orders.csv not found, skipping.")
            return 0

        df = pd.read_csv(file_path)
        count = 0
        for _, row in df.iterrows():
            order_id = int(row["order_id"])
            cust_id = int(row["customer_id"])
            order_date = parse_date(row["order_date"]) or datetime.now().date()
            status = str(row["status"]).strip()
            total = parse_decimal(row["total_brl"])
            pay_method = str(row["payment_method"]).strip()
            tracking = (
                str(row["tracking_code"]).strip() if pd.notna(row.get("tracking_code")) else None
            )
            est_delivery = parse_date(row.get("estimated_delivery"))
            notes = str(row["notes"]).strip() if pd.notna(row.get("notes")) else None

            existing = db.query(Order).filter(Order.order_id == order_id).first()
            if existing:
                existing.customer_id = cust_id
                existing.order_date = order_date
                existing.status = status
                existing.total_brl = total
                existing.payment_method = pay_method
                existing.tracking_code = tracking
                existing.estimated_delivery = est_delivery
                existing.notes = notes
            else:
                db.add(
                    Order(
                        order_id=order_id,
                        customer_id=cust_id,
                        order_date=order_date,
                        status=status,
                        total_brl=total,
                        payment_method=pay_method,
                        tracking_code=tracking,
                        estimated_delivery=est_delivery,
                        notes=notes,
                    )
                )
            count += 1
        db.commit()
        logger.info(f"Ingested {count} orders from {file_path.name}")
        return count

    def ingest_order_items(self, db: Session) -> int:
        file_path = self.find_csv_file("order_items")
        if not file_path:
            logger.warning("order_items.csv not found, skipping.")
            return 0

        df = pd.read_csv(file_path)
        # To maintain idempotency, clear existing order items and re-insert
        db.query(OrderItem).delete()
        count = 0
        for _, row in df.iterrows():
            order_id = int(row["order_id"])
            prod_id = int(row["product_id"])
            qty = int(row["quantity"]) if pd.notna(row.get("quantity")) else 1

            db.add(OrderItem(order_id=order_id, product_id=prod_id, quantity=qty))
            count += 1
        db.commit()
        logger.info(f"Ingested {count} order items from {file_path.name}")
        return count

    def ingest_promotions(self, db: Session) -> int:
        file_path = self.find_csv_file("promotions")
        if not file_path:
            logger.warning("promotions.csv not found, skipping.")
            return 0

        df = pd.read_csv(file_path)
        count = 0
        for _, row in df.iterrows():
            promo_id = int(row["promotion_id"])
            prod_id = int(row["product_id"])
            discount = parse_decimal(row["discount_percent"])
            desc = str(row["description"]).strip()
            is_active = bool(int(row["is_active"])) if pd.notna(row.get("is_active")) else False

            existing = db.query(Promotion).filter(Promotion.promotion_id == promo_id).first()
            if existing:
                existing.product_id = prod_id
                existing.discount_percent = discount
                existing.description = desc
                existing.is_active = is_active
            else:
                db.add(
                    Promotion(
                        promotion_id=promo_id,
                        product_id=prod_id,
                        discount_percent=discount,
                        description=desc,
                        is_active=is_active,
                    )
                )
            count += 1
        db.commit()
        logger.info(f"Ingested {count} promotions from {file_path.name}")
        return count

    def ingest_all(self, db: Session) -> dict[str, int]:
        """Execute full relational ingestion pipeline in foreign-key dependency order."""
        summary = {
            "categories": self.ingest_categories(db),
            "products": self.ingest_products(db),
            "customers": self.ingest_customers(db),
            "orders": self.ingest_orders(db),
            "order_items": self.ingest_order_items(db),
            "promotions": self.ingest_promotions(db),
        }
        logger.info(f"All CSVs successfully ingested: {summary}")
        return summary

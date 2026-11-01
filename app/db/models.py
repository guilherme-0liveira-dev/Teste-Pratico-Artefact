"""SQLAlchemy models for Empório da Música operations."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.connection import Base


class Category(Base):
    """Product categories (e.g. Guitarras, Violões, Teclados)."""

    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


class Product(Base):
    """Product catalog records with pricing and stock levels."""

    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    price_brl = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="active", index=True)
    specs = Column(Text, nullable=True)
    created_at = Column(Date, nullable=True)

    category = relationship("Category", back_populates="products")
    promotions = relationship("Promotion", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")

    @property
    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0 and self.status == "active"

    @property
    def price_decimal(self) -> Decimal:
        return Decimal(str(self.price_brl))


class Customer(Base):
    """Customer accounts with contact details."""

    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(150), nullable=False, index=True)
    city = Column(String(100), nullable=True)

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")


class Order(Base):
    """Customer purchase orders with fulfillment tracking."""

    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False, index=True)
    order_date = Column(Date, nullable=False)
    status = Column(
        String(50), nullable=False, index=True
    )  # delivered, shipped, confirmed, pending, cancelled
    total_brl = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(
        String(50), nullable=False
    )  # pix, boleto, debit, credit_3x, credit_6x, credit_12x
    tracking_code = Column(String(100), nullable=True, index=True)
    estimated_delivery = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def total_decimal(self) -> Decimal:
        return Decimal(str(self.total_brl))


class OrderItem(Base):
    """Line items inside customer orders."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Promotion(Base):
    """Active or historical promotional campaigns linked to products."""

    __tablename__ = "promotions"

    promotion_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    discount_percent = Column(Numeric(5, 2), nullable=False)
    description = Column(String(200), nullable=False)
    is_active = Column(Boolean, nullable=False, default=False, index=True)

    product = relationship("Product", back_populates="promotions")

    @property
    def discount_decimal(self) -> Decimal:
        return Decimal(str(self.discount_percent))


class PolicyDocument(Base):
    """Indexed chunks from store policy manual (políticas da loja)."""

    __tablename__ = "policy_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_number = Column(String(50), nullable=True)
    section_title = Column(String(200), nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

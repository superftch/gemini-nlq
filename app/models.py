import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import DECIMAL as SQLDecimal # Renamed to avoid conflict

from app.core.config import Base # Import Base from config

class Client(Base):
    __tablename__ = "clients"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    invoices = relationship("Invoice", back_populates="client")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(PG_UUID(as_uuid=True), ForeignKey("clients.id"))
    invoice_number = Column(String(100), unique=True)
    amount = Column(SQLDecimal(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    issue_date = Column(Date, nullable=False)
    status = Column(String(50), default="pending") # e.g., pending, paid, overdue
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(PG_UUID(as_uuid=True), ForeignKey("invoices.id"))
    amount = Column(SQLDecimal(10, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50)) # e.g., cash, credit_card, bank_transfer
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="payments")
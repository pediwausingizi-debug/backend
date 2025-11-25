# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Firebase UID should be optional since backend JWT will be primary auth
    firebase_uid = Column(String(255), unique=True, index=True, nullable=True)

    name = Column(String(255), nullable=False)
    picture = Column(String(500), nullable=True)

    role = Column(String(50), default="Worker", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    phone = Column(String(50), nullable=True)
    farm_name = Column(String(255), nullable=True)
    farm_location = Column(String(255), nullable=True)
    farm_size = Column(String(50), nullable=True)

    crops = relationship("Crop", back_populates="owner", cascade="all, delete-orphan")
    livestock = relationship("Livestock", back_populates="owner", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="owner", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="owner", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="owner", cascade="all, delete-orphan")
    workers = relationship("Worker", back_populates="owner", cascade="all, delete-orphan")


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    variety = Column(String(255), nullable=True)
    area_hectares = Column(Float, nullable=False, default=0.0)
    planting_date = Column(DateTime, nullable=True)
    expected_harvest = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="crops")


class Livestock(Base):
    __tablename__ = "livestock"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(100), nullable=False)
    breed = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False, default=0)
    age_months = Column(Integer, nullable=True)
    health_status = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="livestock")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=True)
    reorder_level = Column(Float, nullable=True)
    supplier = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="inventory_items")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # income | expense
    category = Column(String(100), nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    description = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(String(100), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="transactions")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    type = Column(String(50), nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="notifications")


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    salary = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="workers")

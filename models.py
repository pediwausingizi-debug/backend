# models.py
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
# ----------------------------------
# FARM
# ----------------------------------
class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    size = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Users in the farm
    users = relationship("User", back_populates="farm")

# ----------------------------------
# USER
# ----------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    firebase_uid = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=False)
    picture = Column(String(500), nullable=True)
    role = Column(String(50), default="Worker", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    phone = Column(String(50), nullable=True)
    farm_name = Column(String(255), nullable=True)
    farm_location = Column(String(255), nullable=True)
    farm_size = Column(String(50), nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    farm = relationship("Farm", back_populates="users")
    crops = relationship("Crop", back_populates="owner", cascade="all, delete-orphan")
    livestock = relationship("Livestock", back_populates="owner", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="owner", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="owner", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="owner", cascade="all, delete-orphan")
    workers = relationship("Worker", back_populates="owner", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="owner", cascade="all, delete-orphan")


# ----------------------------------
# CROP
# ----------------------------------
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

    # GPS mapping
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    image_url = Column(String(500), nullable=True)

    owner = relationship("User", back_populates="crops")
    media = relationship("Media", back_populates="crop", cascade="all, delete-orphan")
    growth_records = relationship("CropGrowth", back_populates="crop", cascade="all, delete-orphan")
    expenses = relationship("ExpenseLink", back_populates="crop", cascade="all, delete-orphan")


# ----------------------------------
# LIVESTOCK
# ----------------------------------
class Livestock(Base):
    __tablename__ = "livestock"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(100), nullable=False)

    # new: category (Cattle, Poultry, Sheep, Goats, etc.)
    category = Column(String(100), nullable=True)

    breed = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False, default=0)
    age_months = Column(Integer, nullable=True)
    health_status = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    image_url = Column(String(500), nullable=True)

    farm = relationship("Farm", back_populates="livestock")
    media = relationship("Media", back_populates="livestock", cascade="all, delete-orphan")
    production_records = relationship("LivestockProduction", back_populates="livestock", cascade="all, delete-orphan")
    expenses = relationship("ExpenseLink", back_populates="livestock", cascade="all, delete-orphan")


# ----------------------------------
# MEDIA TABLE (multiple images)
# ----------------------------------
class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=True)
    livestock_id = Column(Integer, ForeignKey("livestock.id"), nullable=True)

    crop = relationship("Crop", back_populates="media")
    livestock = relationship("Livestock", back_populates="media")


# ----------------------------------
# CROP GROWTH TRACKING
# ----------------------------------
class CropGrowth(Base):
    __tablename__ = "crop_growth"

    id = Column(Integer, primary_key=True)
    crop_id = Column(Integer, ForeignKey("crops.id"))
    date = Column(DateTime, default=datetime.utcnow)
    height_cm = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    crop = relationship("Crop", back_populates="growth_records")


# ----------------------------------
# LIVESTOCK PRODUCTION (milk, eggs, etc)
# ----------------------------------
class LivestockProduction(Base):
    __tablename__ = "livestock_production"

    id = Column(Integer, primary_key=True)
    livestock_id = Column(Integer, ForeignKey("livestock.id"))
    date = Column(DateTime, default=datetime.utcnow)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50))  # litres, kg, eggs
    notes = Column(Text, nullable=True)

    livestock = relationship("Livestock", back_populates="production_records")


# ----------------------------------
# EXPENSE LINK (connect expenses to items)
# ----------------------------------
class ExpenseLink(Base):
    __tablename__ = "expense_links"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=True)
    livestock_id = Column(Integer, ForeignKey("livestock.id"), nullable=True)

    crop = relationship("Crop", back_populates="expenses")
    livestock = relationship("Livestock", back_populates="expenses")
    transaction = relationship("Transaction")


# ----------------------------------
# INVENTORY
# ----------------------------------
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


# ----------------------------------
# TRANSACTIONS
# ----------------------------------
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


# ----------------------------------
# NOTIFICATIONS
# ----------------------------------
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


# ----------------------------------
# WORKERS
# ----------------------------------
class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    salary = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    id_number = Column(String(100), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="workers")


# ----------------------------------
# ACTIVITY LOG (for AI engine)
# ----------------------------------
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(255))
    details = Column(Text)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="activity_logs")

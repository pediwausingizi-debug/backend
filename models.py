from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    Text, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# =========================================================
# FARM
# =========================================================
class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    size = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="farm", cascade="all, delete")
    crops = relationship("Crop", back_populates="farm", cascade="all, delete")
    livestock = relationship("Livestock", back_populates="farm", cascade="all, delete")
    inventory_items = relationship("InventoryItem", back_populates="farm", cascade="all, delete")
    transactions = relationship("Transaction", back_populates="farm", cascade="all, delete")
    notifications = relationship("Notification", back_populates="farm", cascade="all, delete")
    workers = relationship("Worker", back_populates="farm", cascade="all, delete")
    activity_logs = relationship("ActivityLog", back_populates="farm", cascade="all, delete")


# =========================================================
# USER
# =========================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(255), unique=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture = Column(String(500))
    role = Column(String(50), default="Worker")
    phone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    password_hash = Column(String(255), nullable=True)

    farm_name = Column(String(255))
    farm_location = Column(String(255))
    farm_size = Column(String(50))

    email_notifications = Column(Boolean, default=False)
    weekly_reports = Column(Boolean, default=False)

    farm_id = Column(Integer, ForeignKey("farms.id"))
    farm = relationship("Farm", back_populates="users")

    created_crops = relationship("Crop", back_populates="created_by")
    created_livestock = relationship("Livestock", back_populates="created_by")
    created_inventory = relationship("InventoryItem", back_populates="created_by")
    created_transactions = relationship("Transaction", back_populates="created_by")
    created_notifications = relationship("Notification", back_populates="created_by")
    created_workers = relationship("Worker", back_populates="created_by")
    activity_logs = relationship("ActivityLog", back_populates="user")

    plan = Column(String(20), default="free", nullable=False)

    
# =========================================================
# CROP
# =========================================================
class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    variety = Column(String(255))
    area_hectares = Column(Float, default=0.0)
    planting_date = Column(DateTime)
    expected_harvest = Column(DateTime)
    status = Column(String(50))
    location = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    image_url = Column(String(500))
    image_public_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="crops")

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="created_crops")

    growth_records = relationship(
        "CropGrowth",
        back_populates="crop",
        cascade="all, delete-orphan"
    )

    media = relationship("Media", back_populates="crop", cascade="all, delete-orphan")
    expenses = relationship("ExpenseLink", back_populates="crop", cascade="all, delete-orphan")


# =========================================================
# CROP GROWTH  ✅ FIXED
# =========================================================
class CropGrowth(Base):
    __tablename__ = "crop_growth"

    id = Column(Integer, primary_key=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    height_cm = Column(Float)
    notes = Column(Text)

    crop = relationship("Crop", back_populates="growth_records")


# =========================================================
# LIVESTOCK
# =========================================================
class Livestock(Base):
    __tablename__ = "livestock"

    id = Column(Integer, primary_key=True)
    type = Column(String(100), nullable=False)
    category = Column(String(100))
    breed = Column(String(100))
    quantity = Column(Integer, default=0)
    age_months = Column(Integer)
    health_status = Column(String(100))
    location = Column(String(255))
    image_url = Column(String(500))
    image_public_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="livestock")
    last_checkup = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="created_livestock")

    production_records = relationship(
        "LivestockProduction",
        back_populates="livestock",
        cascade="all, delete-orphan"
    )

    media = relationship("Media", back_populates="livestock", cascade="all, delete-orphan")
    expenses = relationship("ExpenseLink", back_populates="livestock", cascade="all, delete-orphan")


# =========================================================
# LIVESTOCK PRODUCTION
# =========================================================
class LivestockProduction(Base):
    __tablename__ = "livestock_production"

    id = Column(Integer, primary_key=True)
    livestock_id = Column(Integer, ForeignKey("livestock.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50))
    notes = Column(Text)

    livestock = relationship("Livestock", back_populates="production_records")


# =========================================================
# MEDIA
# =========================================================
class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop_id = Column(Integer, ForeignKey("crops.id"))
    livestock_id = Column(Integer, ForeignKey("livestock.id"))

    crop = relationship("Crop", back_populates="media")
    livestock = relationship("Livestock", back_populates="media")


# =========================================================
# EXPENSE LINK
# =========================================================
class ExpenseLink(Base):
    __tablename__ = "expense_links"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    crop_id = Column(Integer, ForeignKey("crops.id"))
    livestock_id = Column(Integer, ForeignKey("livestock.id"))

    transaction = relationship("Transaction")
    crop = relationship("Crop", back_populates="expenses")
    livestock = relationship("Livestock", back_populates="expenses")


# =========================================================
# INVENTORY
# =========================================================
class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    quantity = Column(Float, default=0.0)
    unit = Column(String(50))
    reorder_level = Column(Float)
    supplier = Column(String(255))

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="inventory_items")

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="created_inventory")


# =========================================================
# TRANSACTIONS
# =========================================================
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    category = Column(String(100))
    amount = Column(Float, nullable=False)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(String(100))

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="transactions")

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="created_transactions")


# =========================================================
# NOTIFICATIONS
# =========================================================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    type = Column(String(50))
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="notifications")

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="created_notifications")


# =========================================================
# WORKERS
# =========================================================
class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100))
    phone = Column(String(50))
    email = Column(String(255))
    salary = Column(Float)
    status = Column(String(50))
    id_number = Column(String(100))

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="workers")

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="created_workers")


# =========================================================
# ACTIVITY LOGS
# =========================================================
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"))

    action = Column(String(255))
    details = Column(Text)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="activity_logs")
    user = relationship("User", back_populates="activity_logs")

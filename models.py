from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# =====================================================================
# FARM
# =====================================================================
class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    size = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="farm")
    crops = relationship("Crop", back_populates="farm")
    livestock = relationship("Livestock", back_populates="farm")
    inventory_items = relationship("InventoryItem", back_populates="farm")
    transactions = relationship("Transaction", back_populates="farm")
    notifications = relationship("Notification", back_populates="farm")
    workers = relationship("Worker", back_populates="farm")
    activity_logs = relationship("ActivityLog", back_populates="farm")


# =====================================================================
# USER
# =====================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture = Column(String(500))
    role = Column(String(50), default="Worker")
    phone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_name = Column(String(255))
    farm_location = Column(String(255))
    farm_size = Column(String(50))

    farm_id = Column(Integer, ForeignKey("farms.id"))
    farm = relationship("Farm", back_populates="users")

    # Created items
    created_crops = relationship("Crop", back_populates="created_by")
    created_livestock = relationship("Livestock", back_populates="created_by")
    created_inventory = relationship("InventoryItem", back_populates="created_by")
    created_transactions = relationship("Transaction", back_populates="created_by")
    created_notifications = relationship("Notification", back_populates="created_by")
    created_workers = relationship("Worker", back_populates="created_by")

    activity_logs = relationship("ActivityLog", back_populates="user")


# =====================================================================
# CROP
# =====================================================================
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

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="crops")

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="created_crops")

    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # ⭐ NEW FIELD

    image_url = Column(String(500))

    media = relationship("Media", back_populates="crop")
    growth_records = relationship("CropGrowth", back_populates="crop")
    expenses = relationship("ExpenseLink", back_populates="crop")


# =====================================================================
# LIVESTOCK
# =====================================================================
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
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="livestock")

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="created_livestock")

    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # ⭐ NEW FIELD

    image_url = Column(String(500))

    media = relationship("Media", back_populates="livestock")
    production_records = relationship("LivestockProduction", back_populates="livestock")
    expenses = relationship("ExpenseLink", back_populates="livestock")


# =====================================================================
# MEDIA
# =====================================================================
class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop_id = Column(Integer, ForeignKey("crops.id"))
    livestock_id = Column(Integer, ForeignKey("livestock.id"))

    crop = relationship("Crop", back_populates="media")
    livestock = relationship("Livestock", back_populates="media")


# =====================================================================
# INVENTORY
# =====================================================================
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

    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # ⭐ NEW FIELD


# =====================================================================
# TRANSACTIONS
# =====================================================================
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

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # ⭐ NEW FIELD


# =====================================================================
# NOTIFICATIONS
# =====================================================================
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


# =====================================================================
# WORKERS
# =====================================================================
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


# =====================================================================
# ACTIVITY LOGS
# =====================================================================
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

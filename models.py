# models.py
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
    crops = relationship("Crop", back_populates="farm", cascade="all, delete-orphan")
    livestock = relationship("Livestock", back_populates="farm", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="farm", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="farm", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="farm", cascade="all, delete-orphan")
    workers = relationship("Worker", back_populates="farm", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="farm", cascade="all, delete-orphan")


# =====================================================================
# USER
# =====================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture = Column(String(500), nullable=True)
    role = Column(String(50), default="Worker", nullable=False)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    farm_name = Column(String(255), nullable=True)
    farm_location = Column(String(255), nullable=True)
    farm_size = Column(String(50), nullable=True)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    farm = relationship("Farm", back_populates="users")

    # Created items (explicit foreign_keys to avoid ambiguity)
    created_crops = relationship(
        "Crop",
        back_populates="created_by",
        foreign_keys="Crop.created_by_id",
        cascade="all, delete-orphan",
    )
    added_crops = relationship(
        "Crop",
        back_populates="adder",
        foreign_keys="Crop.added_by",
        cascade="all, delete-orphan",
    )

    created_livestock = relationship(
        "Livestock",
        back_populates="created_by",
        foreign_keys="Livestock.created_by_id",
        cascade="all, delete-orphan",
    )
    added_livestock = relationship(
        "Livestock",
        back_populates="adder",
        foreign_keys="Livestock.added_by",
        cascade="all, delete-orphan",
    )

    created_inventory = relationship(
        "InventoryItem",
        back_populates="created_by",
        foreign_keys="InventoryItem.created_by_id",
        cascade="all, delete-orphan",
    )
    added_inventory = relationship(
        "InventoryItem",
        back_populates="adder",
        foreign_keys="InventoryItem.added_by",
        cascade="all, delete-orphan",
    )

    created_transactions = relationship(
        "Transaction",
        back_populates="created_by",
        foreign_keys="Transaction.created_by_id",
        cascade="all, delete-orphan",
    )
    owned_transactions = relationship(
        "Transaction",
        back_populates="owner",
        foreign_keys="Transaction.owner_id",
        cascade="all, delete-orphan",
    )

    created_notifications = relationship(
        "Notification",
        back_populates="created_by",
        foreign_keys="Notification.created_by_id",
        cascade="all, delete-orphan",
    )

    created_workers = relationship(
        "Worker",
        back_populates="created_by",
        foreign_keys="Worker.created_by_id",
        cascade="all, delete-orphan",
    )

    activity_logs = relationship(
        "ActivityLog",
        back_populates="user",
        foreign_keys="ActivityLog.created_by_id",
        cascade="all, delete-orphan",
    )


# =====================================================================
# CROP
# =====================================================================
class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    variety = Column(String(255), nullable=True)
    area_hectares = Column(Float, default=0.0)
    planting_date = Column(DateTime, nullable=True)
    expected_harvest = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="crops")

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship(
        "User",
        back_populates="created_crops",
        foreign_keys=[created_by_id],
    )

    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # separate FK
    adder = relationship(
        "User",
        back_populates="added_crops",
        foreign_keys=[added_by],
    )

    image_url = Column(String(500), nullable=True)

    media = relationship("Media", back_populates="crop", cascade="all, delete-orphan")
    growth_records = relationship("CropGrowth", back_populates="crop", cascade="all, delete-orphan")
    expenses = relationship("ExpenseLink", back_populates="crop", cascade="all, delete-orphan")


# =====================================================================
# LIVESTOCK
# =====================================================================
class Livestock(Base):
    __tablename__ = "livestock"

    id = Column(Integer, primary_key=True)
    type = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)
    breed = Column(String(100), nullable=True)
    quantity = Column(Integer, default=0)
    age_months = Column(Integer, nullable=True)
    health_status = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="livestock")

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship(
        "User",
        back_populates="created_livestock",
        foreign_keys=[created_by_id],
    )

    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    adder = relationship(
        "User",
        back_populates="added_livestock",
        foreign_keys=[added_by],
    )

    image_url = Column(String(500), nullable=True)

    media = relationship("Media", back_populates="livestock", cascade="all, delete-orphan")
    production_records = relationship("LivestockProduction", back_populates="livestock", cascade="all, delete-orphan")
    expenses = relationship("ExpenseLink", back_populates="livestock", cascade="all, delete-orphan")


# =====================================================================
# MEDIA
# =====================================================================
class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=True)
    livestock_id = Column(Integer, ForeignKey("livestock.id"), nullable=True)

    crop = relationship("Crop", back_populates="media")
    livestock = relationship("Livestock", back_populates="media")


# =====================================================================
# INVENTORY
# =====================================================================
class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    quantity = Column(Float, default=0.0)
    unit = Column(String(50), nullable=True)
    reorder_level = Column(Float, nullable=True)
    supplier = Column(String(255), nullable=True)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="inventory_items")

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship(
        "User",
        back_populates="created_inventory",
        foreign_keys=[created_by_id],
    )

    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    adder = relationship(
        "User",
        back_populates="added_inventory",
        foreign_keys=[added_by],
    )


# =====================================================================
# TRANSACTIONS
# =====================================================================
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # income | expense
    category = Column(String(100), nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    description = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(String(100), nullable=True)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="transactions")

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship(
        "User",
        back_populates="created_transactions",
        foreign_keys=[created_by_id],
    )

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship(
        "User",
        back_populates="owned_transactions",
        foreign_keys=[owner_id],
    )


# =====================================================================
# NOTIFICATIONS
# =====================================================================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    type = Column(String(50), nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="notifications")

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship(
        "User",
        back_populates="created_notifications",
        foreign_keys=[created_by_id],
    )


# =====================================================================
# WORKERS
# =====================================================================
class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    salary = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    id_number = Column(String(100), nullable=True)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="workers")

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship(
        "User",
        back_populates="created_workers",
        foreign_keys=[created_by_id],
    )


# =====================================================================
# ACTIVITY LOGS
# =====================================================================
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    action = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="activity_logs")
    user = relationship(
        "User",
        back_populates="activity_logs",
        foreign_keys=[created_by_id],
    )

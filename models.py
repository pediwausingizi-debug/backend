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
    animals = relationship("Animal", back_populates="farm", cascade="all, delete-orphan")
    plots = relationship("Plot", back_populates="farm", cascade="all, delete-orphan")
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
    created_animals = relationship("Animal", back_populates="created_by")
    created_plots = relationship("Plot", back_populates="created_by")
    created_crop_cycles = relationship("CropCycle", back_populates="created_by")
    created_inventory = relationship("InventoryItem", back_populates="created_by")
    created_transactions = relationship("Transaction", back_populates="created_by")
    created_notifications = relationship("Notification", back_populates="created_by")
    created_workers = relationship("Worker", back_populates="created_by")
    activity_logs = relationship("ActivityLog", back_populates="user")
    plan = Column(String, default="free", nullable=False)  # free, pro
    subscription_status = Column(String, default="inactive", nullable=False)  # inactive, active, expired, cancelled
    subscription_started_at = Column(DateTime, nullable=True)
    subscription_expires_at = Column(DateTime, nullable=True)


# =========================================================
# CROP
# Master crop type
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

    crop_cycles = relationship(
        "CropCycle",
        back_populates="crop",
        cascade="all, delete-orphan"
    )

    media = relationship("Media", back_populates="crop", cascade="all, delete-orphan")
    expenses = relationship("ExpenseLink", back_populates="crop", cascade="all, delete-orphan")


# =========================================================
# CROP GROWTH
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
# PLOT / FIELD
# =========================================================
class Plot(Base):
    __tablename__ = "plots"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100))
    location_description = Column(String(255))
    size_hectares = Column(Float, default=0.0)
    soil_type = Column(String(100))
    irrigation_type = Column(String(100))
    status = Column(String(50), default="available")
    latitude = Column(Float)
    longitude = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    farm = relationship("Farm", back_populates="plots")
    created_by = relationship("User", back_populates="created_plots")

    crop_cycles = relationship(
        "CropCycle",
        back_populates="plot",
        cascade="all, delete-orphan"
    )


# =========================================================
# CROP CYCLE / PLANTING RECORD
# =========================================================
class CropCycle(Base):
    __tablename__ = "crop_cycles"

    id = Column(Integer, primary_key=True)
    season = Column(String(100))
    planting_date = Column(DateTime)
    expected_harvest_date = Column(DateTime)
    actual_harvest_date = Column(DateTime)

    area_used_hectares = Column(Float, default=0.0)
    quantity_harvested = Column(Float, default=0.0)
    harvest_unit = Column(String(50))
    selling_price_per_unit = Column(Float, default=0.0)
    total_revenue = Column(Float, default=0.0)

    status = Column(String(50), default="planned")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    plot_id = Column(Integer, ForeignKey("plots.id"), nullable=False)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    farm = relationship("Farm")
    plot = relationship("Plot", back_populates="crop_cycles")
    crop = relationship("Crop", back_populates="crop_cycles")
    created_by = relationship("User", back_populates="created_crop_cycles")

    expenses = relationship(
        "CropCycleExpense",
        back_populates="crop_cycle",
        cascade="all, delete-orphan"
    )
    incomes = relationship(
        "CropCycleIncome",
        back_populates="crop_cycle",
        cascade="all, delete-orphan"
    )


# =========================================================
# CROP CYCLE EXPENSE
# =========================================================
class CropCycleExpense(Base):
    __tablename__ = "crop_cycle_expenses"

    id = Column(Integer, primary_key=True)
    crop_cycle_id = Column(Integer, ForeignKey("crop_cycles.id"), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)

    crop_cycle = relationship("CropCycle", back_populates="expenses")


# =========================================================
# CROP CYCLE INCOME
# =========================================================
class CropCycleIncome(Base):
    __tablename__ = "crop_cycle_incomes"

    id = Column(Integer, primary_key=True)
    crop_cycle_id = Column(Integer, ForeignKey("crop_cycles.id"), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)

    crop_cycle = relationship("CropCycle", back_populates="incomes")


# =========================================================
# LIVESTOCK
# Group-level record
# =========================================================
class Livestock(Base):
    __tablename__ = "livestock"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(String(100), nullable=False)
    category = Column(String(100))
    breed = Column(String(100))
    quantity = Column(Integer, default=1)
    age_months = Column(Integer)
    health_status = Column(String(100))
    location = Column(String(255))
    image_url = Column(String(500))
    image_public_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checkup = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="livestock")

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="created_livestock")

    production_records = relationship(
        "LivestockProduction",
        back_populates="livestock",
        cascade="all, delete-orphan"
    )

    animals = relationship(
        "Animal",
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
# ANIMAL
# =========================================================
class Animal(Base):
    __tablename__ = "animals"

    id = Column(Integer, primary_key=True)
    tag_number = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255))
    type = Column(String(100), nullable=False)
    category = Column(String(100))
    breed = Column(String(100))
    gender = Column(String(50))
    health_status = Column(String(100))
    status = Column(String(50), default="active")
    date_of_birth = Column(DateTime)
    age_months = Column(Integer)
    purchase_price = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    source = Column(String(100))
    location = Column(String(255))
    image_url = Column(String(500))
    image_public_id = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checkup = Column(DateTime)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    livestock_id = Column(Integer, ForeignKey("livestock.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    farm = relationship("Farm", back_populates="animals")
    livestock = relationship("Livestock", back_populates="animals")
    created_by = relationship("User", back_populates="created_animals")

    production_records = relationship(
        "AnimalProduction",
        back_populates="animal",
        cascade="all, delete-orphan"
    )
    expenses = relationship(
        "AnimalExpense",
        back_populates="animal",
        cascade="all, delete-orphan"
    )
    incomes = relationship(
        "AnimalIncome",
        back_populates="animal",
        cascade="all, delete-orphan"
    )


# =========================================================
# ANIMAL PRODUCTION
# =========================================================
class AnimalProduction(Base):
    __tablename__ = "animal_production"

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    production_type = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50))
    notes = Column(Text)

    animal = relationship("Animal", back_populates="production_records")


# =========================================================
# ANIMAL EXPENSE
# =========================================================
class AnimalExpense(Base):
    __tablename__ = "animal_expenses"

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)

    animal = relationship("Animal", back_populates="expenses")


# =========================================================
# ANIMAL INCOME
# =========================================================
class AnimalIncome(Base):
    __tablename__ = "animal_incomes"

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)

    animal = relationship("Animal", back_populates="incomes")


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
    price = Column(Float, default=0.0)
    reorder_level = Column(Float)
    supplier = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

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

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
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
    created_at = Column(DateTime, default=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    farm = relationship("Farm", back_populates="workers")

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
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
    
    # =========================================================
# USER INTERACTIONS / SYSTEM ANALYTICS
# Tracks page visits, feature clicks, and user actions
# =========================================================
class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)

    page = Column(String(100), nullable=False)       # dashboard, livestock, crops, marketplace
    action = Column(String(100), default="page_view") # page_view, button_click, create, update, delete
    details = Column(Text, nullable=True)             # optional JSON/text details

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    farm = relationship("Farm")
    
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)

    plan = Column(String, default="pro", nullable=False)
    status = Column(String, default="pending", nullable=False)
    # pending, active, expired, cancelled, failed

    amount = Column(Float, default=499.0, nullable=False)
    currency = Column(String, default="KES", nullable=False)

    started_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    payment_reference = Column(String, nullable=True)
    checkout_request_id = Column(String, nullable=True)
    merchant_request_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    provider = Column(String, default="mpesa", nullable=False)
    payment_type = Column(String, default="subscription", nullable=False)

    amount = Column(Float, default=499.0, nullable=False)
    currency = Column(String, default="KES", nullable=False)

    phone_number = Column(String, nullable=True)

    status = Column(String, default="pending", nullable=False)
    # pending, success, failed, cancelled

    checkout_request_id = Column(String, nullable=True)
    merchant_request_id = Column(String, nullable=True)
    mpesa_receipt_number = Column(String, nullable=True)

    result_code = Column(String, nullable=True)
    result_description = Column(Text, nullable=True)

    raw_response = Column(Text, nullable=True)
    raw_callback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
# =========================================================
# MARKETPLACE LISTING
# Smart seller listing
# =========================================================
class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    listing_type = Column(String(50), default="product")  # product, input, service
    description = Column(Text)

    quantity = Column(Float, default=0.0)
    unit = Column(String(50))
    price = Column(Float, default=0.0)

    # smart fields
    recommended_price = Column(Float, default=0.0)
    min_price = Column(Float, default=0.0)
    max_price = Column(Float, default=0.0)
    demand_score = Column(Float, default=0.0)   # 0 - 100
    sell_now_score = Column(Float, default=0.0) # 0 - 100
    price_position = Column(String(50))         # below, fair, above
    ai_summary = Column(Text)

    location = Column(String(255))
    image_url = Column(String(500))
    image_public_id = Column(String(255))

    status = Column(String(50), default="active")  # active, sold, hidden, draft, closed
    source_type = Column(String(50))               # manual, crop_cycle, animal, inventory
    source_id = Column(Integer)                    # optional loose link to source record

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    farm = relationship("Farm")
    created_by = relationship("User")

    matches = relationship(
        "MarketplaceMatch",
        back_populates="listing",
        cascade="all, delete-orphan"
    )


# =========================================================
# MARKETPLACE BUYER REQUEST
# Demand-side requests
# =========================================================
class MarketplaceRequest(Base):
    __tablename__ = "marketplace_requests"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text)

    quantity_needed = Column(Float, default=0.0)
    unit = Column(String(50))
    target_price = Column(Float, default=0.0)

    location = Column(String(255))
    deadline = Column(DateTime)

    demand_score = Column(Float, default=0.0)
    ai_summary = Column(Text)

    status = Column(String(50), default="open")  # open, matched, closed, cancelled

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)   # optional if buyer is a farm
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    farm = relationship("Farm")
    created_by = relationship("User")

    matches = relationship(
        "MarketplaceMatch",
        back_populates="request",
        cascade="all, delete-orphan"
    )


# =========================================================
# MARKETPLACE MATCH
# Smart matching between listings and buyer requests
# =========================================================
class MarketplaceMatch(Base):
    __tablename__ = "marketplace_matches"

    id = Column(Integer, primary_key=True)

    listing_id = Column(Integer, ForeignKey("marketplace_listings.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("marketplace_requests.id"), nullable=False)

    match_score = Column(Float, default=0.0)   # 0 - 100
    reason = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("MarketplaceListing", back_populates="matches")
    request = relationship("MarketplaceRequest", back_populates="matches")
    status = Column(String(50), default='pending')
# =========================================================
# MARKETPLACE CONVERSATION
# One chat thread between users around a listing/request/general marketplace talk
# =========================================================
class MarketplaceConversation(Base):
    __tablename__ = "marketplace_conversations"

    id = Column(Integer, primary_key=True)

    conversation_type = Column(String(50), default="listing")  # listing, request, direct
    title = Column(String(255))

    listing_id = Column(Integer, ForeignKey("marketplace_listings.id"), nullable=True)
    request_id = Column(Integer, ForeignKey("marketplace_requests.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    listing = relationship("MarketplaceListing")
    request = relationship("MarketplaceRequest")
    created_by = relationship("User")

    participants = relationship(
        "MarketplaceConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    messages = relationship(
        "MarketplaceMessage",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


# =========================================================
# MARKETPLACE CONVERSATION PARTICIPANTS
# =========================================================
class MarketplaceConversationParticipant(Base):
    __tablename__ = "marketplace_conversation_participants"

    id = Column(Integer, primary_key=True)

    conversation_id = Column(Integer, ForeignKey("marketplace_conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    joined_at = Column(DateTime, default=datetime.utcnow)
    last_read_at = Column(DateTime)

    conversation = relationship("MarketplaceConversation", back_populates="participants")
    user = relationship("User")


# =========================================================
# MARKETPLACE MESSAGE
# =========================================================
class MarketplaceMessage(Base):
    __tablename__ = "marketplace_messages"

    id = Column(Integer, primary_key=True)

    conversation_id = Column(Integer, ForeignKey("marketplace_conversations.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    message_type = Column(String(50), default="text")  # text, image, system
    content = Column(Text, nullable=True)

    image_url = Column(String(500))
    image_public_id = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("MarketplaceConversation", back_populates="messages")
    sender = relationship("User")
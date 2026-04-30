from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import date, datetime


# =====================================================================
# BASE CLASS
# =====================================================================
class SafeModel(BaseModel):
    class Config:
        extra = "ignore"
        arbitrary_types_allowed = True
        from_attributes = True


# =====================================================================
# INVITE
# =====================================================================
class InviteRequest(SafeModel):
    email: EmailStr
    name: Optional[str] = None
    role: Optional[str] = None


# =====================================================================
# USER
# =====================================================================
class UserFirebaseCreate(SafeModel):
    firebase_uid: Optional[str] = None
    email: EmailStr
    name: Optional[str] = None
    role: Optional[str] = "Worker"


class UserRead(SafeModel):
    id: int
    firebase_uid: Optional[str]
    email: EmailStr
    name: Optional[str]
    role: Optional[str]
    created_at: datetime
    phone: Optional[str]

    farm_id: Optional[int]
    farm_name: Optional[str]
    farm_location: Optional[str]
    farm_size: Optional[str]

    email_notifications: bool
    weekly_reports: bool


class UserUpdate(SafeModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    farm_name: Optional[str] = None
    farm_location: Optional[str] = None
    farm_size: Optional[str] = None
    email_notifications: Optional[bool] = None
    weekly_reports: Optional[bool] = None


class UserCreateByAdmin(SafeModel):
    email: EmailStr
    name: Optional[str] = None
    role: Optional[str] = None


# =====================================================================
# MEDIA
# =====================================================================
class MediaRead(SafeModel):
    id: int
    url: str
    created_at: datetime


class ImageSaveRequest(SafeModel):
    url: str
    public_id: Optional[str] = None


# =====================================================================
# CROP
# =====================================================================
class CropCreate(SafeModel):
    name: Optional[str] = None
    variety: Optional[str] = None
    area_hectares: Optional[float] = 0.0
    planting_date: Optional[datetime] = None
    expected_harvest: Optional[datetime] = None
    status: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CropRead(CropCreate):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    image_url: Optional[str]
    media: List[MediaRead] = []
    image_public_id: Optional[str]
    created_at: datetime


# =====================================================================
# CROP GROWTH
# =====================================================================
class CropGrowthCreate(SafeModel):
    height_cm: Optional[float] = None
    notes: Optional[str] = None


class CropGrowthRead(CropGrowthCreate):
    id: int
    crop_id: int
    date: datetime


# =====================================================================
# PLOT / FIELD
# =====================================================================
class PlotCreate(SafeModel):
    name: Optional[str] = None
    code: Optional[str] = None
    location_description: Optional[str] = None
    size_hectares: Optional[float] = 0.0
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    status: Optional[str] = "available"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class PlotRead(PlotCreate):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    created_at: datetime


class PlotUpdate(SafeModel):
    name: Optional[str] = None
    code: Optional[str] = None
    location_description: Optional[str] = None
    size_hectares: Optional[float] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    status: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


# =====================================================================
# CROP CYCLE
# =====================================================================
class CropCycleCreate(SafeModel):
    crop_id: Optional[int] = None
    plot_id: Optional[int] = None
    season: Optional[str] = None
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    actual_harvest_date: Optional[datetime] = None
    area_used_hectares: Optional[float] = 0.0
    quantity_harvested: Optional[float] = 0.0
    harvest_unit: Optional[str] = None
    selling_price_per_unit: Optional[float] = 0.0
    total_revenue: Optional[float] = 0.0
    status: Optional[str] = "planned"
    notes: Optional[str] = None


class CropCycleRead(CropCycleCreate):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    created_at: datetime


class CropCycleUpdate(SafeModel):
    crop_id: Optional[int] = None
    plot_id: Optional[int] = None
    season: Optional[str] = None
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    actual_harvest_date: Optional[datetime] = None
    area_used_hectares: Optional[float] = None
    quantity_harvested: Optional[float] = None
    harvest_unit: Optional[str] = None
    selling_price_per_unit: Optional[float] = None
    total_revenue: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# =====================================================================
# CROP CYCLE EXPENSE
# =====================================================================
class CropCycleExpenseCreate(SafeModel):
    category: Optional[str] = None
    amount: Optional[float] = 0.0
    description: Optional[str] = None
    date: Optional[datetime] = None


class CropCycleExpenseRead(CropCycleExpenseCreate):
    id: int
    crop_cycle_id: int
    date: datetime


# =====================================================================
# CROP CYCLE INCOME
# =====================================================================
class CropCycleIncomeCreate(SafeModel):
    category: Optional[str] = None
    amount: Optional[float] = 0.0
    description: Optional[str] = None
    date: Optional[datetime] = None


class CropCycleIncomeRead(CropCycleIncomeCreate):
    id: int
    crop_cycle_id: int
    date: datetime


# =====================================================================
# CROP CYCLE PROFIT SUMMARY
# =====================================================================
class CropCycleProfitSummary(SafeModel):
    crop_cycle_id: int
    total_income: float = 0.0
    total_expenses: float = 0.0
    net_profit: float = 0.0


# =====================================================================
# LIVESTOCK
# =====================================================================
class LivestockCreate(SafeModel):
    name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    breed: Optional[str] = None
    quantity: Optional[int] = 1
    age_months: Optional[int] = None
    health_status: Optional[str] = None
    location: Optional[str] = None
    last_checkup: Optional[datetime] = None


class LivestockRead(LivestockCreate):
    id: int
    created_at: datetime
    farm_id: int
    created_by_id: Optional[int]
    image_url: Optional[str]
    media: List[MediaRead] = []
    image_public_id: Optional[str]


# =====================================================================
# LIVESTOCK PRODUCTION
# =====================================================================
class LivestockProductionCreate(SafeModel):
    quantity: Optional[float] = 0.0
    unit: Optional[str] = None
    notes: Optional[str] = None
    animal_id: Optional[int] = None
    type: Optional[str] = None


class LivestockProductionRead(LivestockProductionCreate):
    id: int
    livestock_id: int
    date: datetime


# =====================================================================
# ANIMAL
# =====================================================================
class AnimalCreate(SafeModel):
    tag_number: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    health_status: Optional[str] = None
    status: Optional[str] = "active"
    date_of_birth: Optional[datetime] = None
    age_months: Optional[int] = None
    purchase_price: Optional[float] = 0.0
    current_value: Optional[float] = 0.0
    source: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None
    notes: Optional[str] = None
    last_checkup: Optional[datetime] = None
    livestock_id: Optional[int] = None


class AnimalRead(AnimalCreate):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    created_at: datetime


class AnimalUpdate(SafeModel):
    tag_number: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    health_status: Optional[str] = None
    status: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    age_months: Optional[int] = None
    purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    source: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None
    notes: Optional[str] = None
    last_checkup: Optional[datetime] = None
    livestock_id: Optional[int] = None


# =====================================================================
# ANIMAL PRODUCTION
# =====================================================================
class AnimalProductionCreate(SafeModel):
    production_type: Optional[str] = None
    quantity: Optional[float] = 0.0
    unit: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[datetime] = None


class AnimalProductionRead(AnimalProductionCreate):
    id: int
    animal_id: int
    date: datetime


# =====================================================================
# ANIMAL EXPENSE
# =====================================================================
class AnimalExpenseCreate(SafeModel):
    category: Optional[str] = None
    amount: Optional[float] = 0.0
    description: Optional[str] = None
    date: Optional[datetime] = None


class AnimalExpenseRead(AnimalExpenseCreate):
    id: int
    animal_id: int
    date: datetime


# =====================================================================
# ANIMAL INCOME
# =====================================================================
class AnimalIncomeCreate(SafeModel):
    category: Optional[str] = None
    amount: Optional[float] = 0.0
    description: Optional[str] = None
    date: Optional[datetime] = None


class AnimalIncomeRead(AnimalIncomeCreate):
    id: int
    animal_id: int
    date: datetime


# =====================================================================
# ANIMAL PROFIT SUMMARY
# =====================================================================
class AnimalProfitSummary(SafeModel):
    animal_id: int
    total_income: float = 0.0
    total_expenses: float = 0.0
    net_profit: float = 0.0


# =====================================================================
# INVENTORY
# =====================================================================
class InventoryCreate(SafeModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = 0.0
    unit: Optional[str] = None
    price: Optional[float] = 0.0
    reorder_level: Optional[float] = None
    supplier: Optional[str] = None


class InventoryRead(InventoryCreate):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    created_at: Optional[datetime]


# =====================================================================
# TRANSACTIONS
# =====================================================================
class TransactionCreate(SafeModel):
    type: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = 0.0
    description: Optional[str] = None
    date: Optional[datetime] = None
    payment_method: Optional[str] = None


class TransactionRead(TransactionCreate):
    id: int
    farm_id: int
    created_by_id: Optional[int]


# =====================================================================
# EXPENSE LINKS
# =====================================================================
class ExpenseLinkRead(SafeModel):
    id: int
    transaction_id: int
    crop_id: Optional[int]
    livestock_id: Optional[int]


# =====================================================================
# NOTIFICATIONS
# =====================================================================
class NotificationCreate(SafeModel):
    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None
    read: Optional[bool] = False


class NotificationRead(NotificationCreate):
    id: int
    created_at: datetime
    farm_id: int
    created_by_id: Optional[int]


# =====================================================================
# WORKERS
# =====================================================================
class WorkerCreate(SafeModel):
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    salary: Optional[float] = None
    status: Optional[str] = None
    id_number: Optional[str] = None


class WorkerRead(WorkerCreate):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    created_at: Optional[datetime]


# =====================================================================
# ACTIVITY LOG
# =====================================================================
class ActivityLogCreate(SafeModel):
    action: Optional[str] = None
    details: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


class ActivityLogRead(ActivityLogCreate):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    timestamp: datetime
    
# =====================================================================
# MARKETPLACE LISTING
# =====================================================================
class MarketplaceListingCreate(SafeModel):
    title: Optional[str] = None
    category: Optional[str] = None
    listing_type: Optional[str] = "product"
    description: Optional[str] = None

    quantity: Optional[float] = 0.0
    unit: Optional[str] = None
    price: Optional[float] = 0.0

    location: Optional[str] = None
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None

    status: Optional[str] = "active"
    source_type: Optional[str] = None
    source_id: Optional[int] = None


class MarketplaceListingUpdate(SafeModel):
    title: Optional[str] = None
    category: Optional[str] = None
    listing_type: Optional[str] = None
    description: Optional[str] = None

    quantity: Optional[float] = None
    unit: Optional[str] = None
    price: Optional[float] = None

    location: Optional[str] = None
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None

    status: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None


class MarketplaceListingRead(SafeModel):
    id: int
    title: str
    category: str
    listing_type: Optional[str]
    description: Optional[str]

    quantity: Optional[float]
    unit: Optional[str]
    price: Optional[float]

    recommended_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    demand_score: Optional[float]
    sell_now_score: Optional[float]
    price_position: Optional[str]
    ai_summary: Optional[str]

    location: Optional[str]
    image_url: Optional[str]
    image_public_id: Optional[str]

    status: Optional[str]
    source_type: Optional[str]
    source_id: Optional[int]

    farm_id: int
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]


# =====================================================================
# MARKETPLACE REQUEST
# =====================================================================
class MarketplaceRequestCreate(SafeModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    quantity_needed: Optional[float] = 0.0
    unit: Optional[str] = None
    target_price: Optional[float] = 0.0

    location: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = "open"


class MarketplaceRequestUpdate(SafeModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    quantity_needed: Optional[float] = None
    unit: Optional[str] = None
    target_price: Optional[float] = None

    location: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None


class MarketplaceRequestRead(SafeModel):
    id: int
    title: str
    category: str
    description: Optional[str]

    quantity_needed: Optional[float]
    unit: Optional[str]
    target_price: Optional[float]

    location: Optional[str]
    deadline: Optional[datetime]

    demand_score: Optional[float]
    ai_summary: Optional[str]

    status: Optional[str]

    farm_id: Optional[int]
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]


# =====================================================================
# MARKETPLACE STATUS UPDATE
# =====================================================================
class MarketplaceStatusUpdate(SafeModel):
    status: str


# =====================================================================
# MARKETPLACE SMART SUMMARY
# =====================================================================
class MarketplaceSmartSuggestion(SafeModel):
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    title: Optional[str] = None
    category: Optional[str] = None
    suggested_quantity: Optional[float] = 0.0
    unit: Optional[str] = None
    recommended_price: Optional[float] = 0.0
    demand_score: Optional[float] = 0.0
    sell_now_score: Optional[float] = 0.0
    reason: Optional[str] = None


class MarketplaceInsightsRead(SafeModel):
    trending_categories: List[str] = []
    high_demand_requests: int = 0
    active_listings: int = 0
    open_requests: int = 0
    suggestions: List[MarketplaceSmartSuggestion] = []
    
# =====================================================================
# MARKETPLACE CONVERSATION
# =====================================================================
class MarketplaceConversationCreate(SafeModel):
    conversation_type: Optional[str] = "listing"
    title: Optional[str] = None
    listing_id: Optional[int] = None
    request_id: Optional[int] = None
    participant_user_ids: List[int] = []


class MarketplaceConversationRead(SafeModel):
    id: int
    conversation_type: Optional[str]
    title: Optional[str]
    listing_id: Optional[int]
    request_id: Optional[int]
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]


class MarketplaceConversationParticipantRead(SafeModel):
    id: int
    conversation_id: int
    user_id: int
    joined_at: datetime
    last_read_at: Optional[datetime]


# =====================================================================
# MARKETPLACE MESSAGE
# =====================================================================
class MarketplaceMessageCreate(SafeModel):
    content: str
    message_type: Optional[str] = "text"
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None


class MarketplaceMessageRead(SafeModel):
    id: int
    conversation_id: int
    sender_id: int
    message_type: Optional[str]
    content: str
    image_url: Optional[str]
    image_public_id: Optional[str]
    created_at: datetime


# =====================================================================
# CHAT BOOTSTRAP
# Used to create or fetch a conversation from listing/request
# =====================================================================
class MarketplaceChatBootstrap(SafeModel):
    listing_id: Optional[int] = None
    request_id: Optional[int] = None
    participant_user_id: int
    title: Optional[str] = None
    
class MarketplaceMatchStatusUpdate(BaseModel):
    status: str



    
class MarketplaceMatchRead(BaseModel):
    id: int
    listing_id: int
    request_id: int
    match_score: float
    reason: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class MarketplaceMatchAcceptResponse(BaseModel):
    match: MarketplaceMatchRead
    conversation: MarketplaceConversationRead

    model_config = ConfigDict(from_attributes=True)
    
# =====================================================================
# SYSTEM ADMIN ANALYTICS / USER INTERACTIONS
# =====================================================================
class UserInteractionCreate(SafeModel):
    page: str
    action: Optional[str] = "page_view"
    details: Optional[str] = None


class UserInteractionRead(SafeModel):
    id: int
    user_id: Optional[int]
    farm_id: Optional[int]

    page: str
    action: Optional[str]
    details: Optional[str]

    created_at: datetime


class PageInteractionSummary(SafeModel):
    page: str
    visits: int = 0
    actions: int = 0


class AdminAnalyticsOverview(SafeModel):
    total_users: int = 0
    total_farms: int = 0
    total_interactions: int = 0
    active_users_today: int = 0

    total_livestock: int = 0
    total_crops: int = 0
    total_inventory_items: int = 0
    total_workers: int = 0

    marketplace_listings: int = 0
    marketplace_requests: int = 0
    marketplace_matches: int = 0
    marketplace_conversations: int = 0


class AdminAnalyticsPageStats(SafeModel):
    pages: List[PageInteractionSummary] = []


class AdminRecentInteraction(SafeModel):
    id: int
    user_id: Optional[int]
    farm_id: Optional[int]
    user_email: Optional[str] = None
    page: str
    action: Optional[str]
    details: Optional[str]
    created_at: datetime
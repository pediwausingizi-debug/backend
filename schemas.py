from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime


# =====================================================================
# BASE CLASS TO PREVENT 422 ERRORS
# =====================================================================
class SafeModel(BaseModel):
    class Config:
        extra = "ignore"                 # Accept unknown fields
        arbitrary_types_allowed = True
        from_attributes = True           # ORM support


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

    class Config:
        from_attributes = True

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
# LIVESTOCK
# =====================================================================
class LivestockCreate(SafeModel):
    type: Optional[str] = None
    category: Optional[str] = None
    breed: Optional[str] = None
    quantity: Optional[int] = 0
    age_months: Optional[int] = None
    health_status: Optional[str] = None
    location: Optional[str] = None
    last_checkup: Optional[date] = None

class LivestockRead(LivestockCreate):
    id: int
    created_at: datetime
    farm_id: int
    created_by_id: Optional[int]
    added_by: Optional[int] = None
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


class LivestockProductionRead(LivestockProductionCreate):
    id: int
    livestock_id: int
    date: datetime


# =====================================================================
# INVENTORY
# =====================================================================
class InventoryCreate(SafeModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = 0.0
    unit: Optional[str] = None
    reorder_level: Optional[float] = None
    supplier: Optional[str] = None


class InventoryRead(InventoryCreate):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    added_by: Optional[int] = None


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
    owner_id: Optional[int] = None


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

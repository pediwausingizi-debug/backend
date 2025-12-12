from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# =====================================================================
# INVITE
# =====================================================================
class InviteRequest(BaseModel):
    email: EmailStr
    name: str
    role: str  # Manager | Worker


# =====================================================================
# USER
# =====================================================================
class UserFirebaseCreate(BaseModel):
    firebase_uid: str
    email: EmailStr
    name: str
    role: Optional[str] = "Worker"


class UserRead(BaseModel):
    id: int
    firebase_uid: Optional[str]
    email: EmailStr
    name: str
    role: str
    created_at: datetime
    phone: Optional[str]

    farm_id: Optional[int]
    farm_name: Optional[str]
    farm_location: Optional[str]
    farm_size: Optional[str]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    farm_name: Optional[str] = None
    farm_location: Optional[str] = None
    farm_size: Optional[str] = None


class UserCreateByAdmin(BaseModel):
    email: EmailStr
    name: str
    role: str


# =====================================================================
# MEDIA
# =====================================================================
class MediaRead(BaseModel):
    id: int
    url: str
    created_at: datetime

    class Config:
        from_attributes = True


class ImageSaveRequest(BaseModel):
    url: str


# =====================================================================
# CROP
# =====================================================================
class CropBase(BaseModel):
    name: str
    variety: Optional[str] = None
    area_hectares: float = 0.0
    planting_date: Optional[datetime] = None
    expected_harvest: Optional[datetime] = None
    status: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float]
    longitude: Optional[float]


class CropCreate(CropBase):
    pass


class CropRead(CropBase):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    image_url: Optional[str]
    media: List[MediaRead] = []

    class Config:
        from_attributes = True


# =====================================================================
# CROP GROWTH
# =====================================================================
class CropGrowthBase(BaseModel):
    height_cm: Optional[float]
    notes: Optional[str]


class CropGrowthCreate(CropGrowthBase):
    pass


class CropGrowthRead(CropGrowthBase):
    id: int
    crop_id: int
    date: datetime

    class Config:
        from_attributes = True


# =====================================================================
# LIVESTOCK
# =====================================================================
class LivestockBase(BaseModel):
    type: str
    category: Optional[str]
    breed: Optional[str]
    quantity: int = 0
    age_months: Optional[int]
    health_status: Optional[str]
    location: Optional[str]


class LivestockCreate(LivestockBase):
    pass


class LivestockRead(LivestockBase):
    id: int
    created_at: datetime
    farm_id: int
    created_by_id: Optional[int]
    added_by: Optional[int] = None        # ⭐ NEW: matches updated model
    image_url: Optional[str]
    media: List[MediaRead] = []

    class Config:
        from_attributes = True


# =====================================================================
# LIVESTOCK PRODUCTION
# =====================================================================
class LivestockProductionBase(BaseModel):
    quantity: float
    unit: str
    notes: Optional[str]


class LivestockProductionCreate(LivestockProductionBase):
    pass


class LivestockProductionRead(LivestockProductionBase):
    id: int
    livestock_id: int
    date: datetime

    class Config:
        from_attributes = True


# =====================================================================
# INVENTORY
# =====================================================================
class InventoryBase(BaseModel):
    name: str
    category: Optional[str]
    quantity: float = 0.0
    unit: Optional[str]
    reorder_level: Optional[float]
    supplier: Optional[str]


class InventoryCreate(InventoryBase):
    pass


class InventoryRead(InventoryBase):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    added_by: Optional[int] = None         # ⭐ NEW: matches updated model

    class Config:
        from_attributes = True


# =====================================================================
# TRANSACTIONS
# =====================================================================
class TransactionBase(BaseModel):
    type: str
    category: Optional[str]
    amount: float
    description: Optional[str]
    date: Optional[datetime]
    payment_method: Optional[str]


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    farm_id: int
    created_by_id: Optional[int]

    owner_id: Optional[int] = None         # ⭐ NEW: matches updated model

    class Config:
        from_attributes = True


# =====================================================================
# EXPENSE LINK
# =====================================================================
class ExpenseLinkRead(BaseModel):
    id: int
    transaction_id: int
    crop_id: Optional[int]
    livestock_id: Optional[int]

    class Config:
        from_attributes = True


# =====================================================================
# NOTIFICATIONS
# =====================================================================
class NotificationBase(BaseModel):
    title: str
    message: Optional[str]
    type: Optional[str]
    read: Optional[bool] = False


class NotificationCreate(NotificationBase):
    pass


class NotificationRead(NotificationBase):
    id: int
    created_at: datetime
    farm_id: int
    created_by_id: Optional[int]

    class Config:
        from_attributes = True


# =====================================================================
# WORKERS
# =====================================================================
class WorkerBase(BaseModel):
    name: str
    role: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    salary: Optional[float]
    status: Optional[str]
    id_number: Optional[str]


class WorkerCreate(WorkerBase):
    pass


class WorkerRead(WorkerBase):
    id: int
    farm_id: int
    created_by_id: Optional[int]

    class Config:
        from_attributes = True


# =====================================================================
# ACTIVITY LOGS
# =====================================================================
class ActivityLogBase(BaseModel):
    action: str
    details: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[int]


class ActivityLogCreate(ActivityLogBase):
    pass


class ActivityLogRead(ActivityLogBase):
    id: int
    farm_id: int
    created_by_id: Optional[int]
    timestamp: datetime

    class Config:
        from_attributes = True

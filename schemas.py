# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ======================
# USER
# ======================

class UserFirebaseCreate(BaseModel):
    firebase_uid: str
    email: EmailStr
    name: str
    role: Optional[str] = "Worker"


class UserRead(BaseModel):
    id: int
    firebase_uid: Optional[str] = None
    email: EmailStr
    name: str
    role: str
    created_at: datetime

    phone: Optional[str] = None
    farm_name: Optional[str] = None
    farm_location: Optional[str] = None
    farm_size: Optional[str] = None

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
    role: str  # "Manager" or "Worker"


# ======================
# MEDIA (Multiple images)
# ======================

class MediaRead(BaseModel):
    id: int
    url: str
    created_at: datetime

    class Config:
        from_attributes = True


class ImageSaveRequest(BaseModel):
    url: str


# ======================
# Crop
# ======================

class CropBase(BaseModel):
    name: str
    variety: Optional[str] = None
    area_hectares: float = 0.0
    planting_date: Optional[datetime] = None
    expected_harvest: Optional[datetime] = None
    status: Optional[str] = None
    location: Optional[str] = None

    # NEW: GPS
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CropCreate(CropBase):
    pass


class CropRead(CropBase):
    id: int
    owner_id: int
    image_url: Optional[str] = None
    media: List[MediaRead] = []

    class Config:
        from_attributes = True


# ======================
# Crop Growth Tracking
# ======================

class CropGrowthBase(BaseModel):
    height_cm: Optional[float] = None
    notes: Optional[str] = None


class CropGrowthCreate(CropGrowthBase):
    pass


class CropGrowthRead(CropGrowthBase):
    id: int
    crop_id: int
    date: datetime

    class Config:
        from_attributes = True


# ======================
# Livestock
# ======================

class LivestockBase(BaseModel):
    type: str
    breed: Optional[str] = None
    quantity: int = 0
    age_months: Optional[int] = None
    health_status: Optional[str] = None
    location: Optional[str] = None

    # NEW
    category: Optional[str] = None


class LivestockCreate(LivestockBase):
    pass


class LivestockRead(LivestockBase):
    id: int
    created_at: Optional[datetime] = None
    owner_id: int
    image_url: Optional[str] = None
    media: List[MediaRead] = []

    class Config:
        from_attributes = True


# ======================
# Livestock Production
# ======================

class LivestockProductionBase(BaseModel):
    quantity: float
    unit: str
    notes: Optional[str] = None


class LivestockProductionCreate(LivestockProductionBase):
    pass


class LivestockProductionRead(LivestockProductionBase):
    id: int
    livestock_id: int
    date: datetime

    class Config:
        from_attributes = True


# ======================
# Inventory
# ======================

class InventoryBase(BaseModel):
    name: str
    category: Optional[str] = None
    quantity: float = 0.0
    unit: Optional[str] = None
    reorder_level: Optional[float] = None
    supplier: Optional[str] = None


class InventoryCreate(InventoryBase):
    pass


class InventoryRead(InventoryBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


# ======================
# Transaction / Finance
# ======================

class TransactionBase(BaseModel):
    type: str
    category: Optional[str] = None
    amount: float
    description: Optional[str] = None
    date: Optional[datetime] = None
    payment_method: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


# ======================
# Expense Link
# ======================

class ExpenseLinkRead(BaseModel):
    id: int
    transaction_id: int
    crop_id: Optional[int]
    livestock_id: Optional[int]

    class Config:
        from_attributes = True


# ======================
# Notification
# ======================

class NotificationBase(BaseModel):
    title: str
    message: Optional[str] = None
    type: Optional[str] = None
    read: Optional[bool] = False


class NotificationCreate(NotificationBase):
    pass


class NotificationRead(NotificationBase):
    id: int
    created_at: Optional[datetime] = None
    owner_id: int

    class Config:
        from_attributes = True


# ======================
# Worker
# ======================

class WorkerBase(BaseModel):
    name: str
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    salary: Optional[float] = None
    status: Optional[str] = None
    id_number: Optional[str] = None


class WorkerCreate(WorkerBase):
    pass


class WorkerRead(WorkerBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


# ======================
# Activity Log
# ======================

class ActivityLogBase(BaseModel):
    action: str
    details: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


class ActivityLogCreate(ActivityLogBase):
    pass


class ActivityLogRead(ActivityLogBase):
    id: int
    owner_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

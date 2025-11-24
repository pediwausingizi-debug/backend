# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ======================
# User Schemas (Firebase)
# ======================

class UserFirebaseCreate(BaseModel):
    firebase_uid: str
    email: EmailStr
    name: str
    role: Optional[str] = "Worker"


class UserRead(BaseModel):
    id: int
    firebase_uid: str
    email: EmailStr
    name: str
    role: str
    created_at: datetime
    
    phone: Optional[str] = None
    farm_name: Optional[str] = None
    farm_location: Optional[str] = None
    farm_size: Optional[str] = None


    class Config:
        orm_mode = True
        
class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

    farm_name: Optional[str] = None
    farm_location: Optional[str] = None
    farm_size: Optional[str] = None



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


class CropCreate(CropBase):
    pass


class CropRead(CropBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


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


class LivestockCreate(LivestockBase):
    pass


class LivestockRead(LivestockBase):
    id: int
    created_at: Optional[datetime] = None
    owner_id: int

    class Config:
        orm_mode = True


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
        orm_mode = True


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
        orm_mode = True


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
        orm_mode = True


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


class WorkerCreate(WorkerBase):
    pass


class WorkerRead(WorkerBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

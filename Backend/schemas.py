from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import date
from enum import Enum

class BloodType(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class DonorBase(UserBase):
    blood_type: BloodType
    dob: date
    gender: int
    phone: constr(min_length=10, max_length=10)

class DonorCreate(DonorBase):
    pass

class DonorResponse(DonorBase):
    id: int
    class Config:
        from_attributes = True

class ReceiverBase(UserBase):
    required_blood_type: BloodType
    phone: constr(min_length=10, max_length=10)

class ReceiverCreate(ReceiverBase):
    pass

class ReceiverResponse(ReceiverBase):
    id: int
    class Config:
        from_attributes = True

class EmergencyContactBase(BaseModel):
    name: str
    phone: constr(min_length=10, max_length=10)
    email: EmailStr
    relation: str
    user_email: EmailStr  # Email to determine donor/receiver

class EmergencyContactCreate(EmergencyContactBase):
    pass  # donor_id or receiver_id will be assigned based on user_email

class EmergencyContactResponse(EmergencyContactBase):
    id: int
    donor_id: Optional[int] = None
    receiver_id: Optional[int] = None
    class Config:
        from_attributes = True

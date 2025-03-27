from pydantic import BaseModel, EmailStr, constr, validator
from datetime import date
from enum import Enum
from typing import Optional

class BloodType(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"

class Gender(int, Enum):
    MALE = 1
    FEMALE = 2
    OTHER = 3

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class DonorBase(BaseModel):
    email: EmailStr
    blood_type: BloodType
    dob: date
    gender: int
    phone: constr(min_length=10, max_length=10)
    
    @validator('gender')
    def validate_gender(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError('Gender must be 1 (Male), 2 (Female), or 3 (Other)')
        return v

class DonorCreate(DonorBase):
    pass

class DonorResponse(DonorBase):
    id: int
    
    class Config:
        from_attributes = True

class ReceiverBase(BaseModel):
    email: EmailStr
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

class EmergencyContactCreate(EmergencyContactBase):
    pass

class EmergencyContactResponse(EmergencyContactBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True



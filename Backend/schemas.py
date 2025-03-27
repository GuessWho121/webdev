from pydantic import BaseModel, EmailStr, constr
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

# Enum for Gender
class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Donor Schemas
class DonorBase(UserBase):
    blood_type: BloodType
    dob: date
    gender: Gender  # Updated here
    phone: constr(min_length=10, max_length=10)

class DonorCreate(DonorBase):
    pass

class DonorResponse(DonorBase):
    id: int
    class Config:
        from_attributes = True

# Receiver Schemas
class ReceiverBase(UserBase):
    required_blood_type: BloodType
    phone: constr(min_length=10, max_length=10)

class ReceiverCreate(ReceiverBase):
    pass

class ReceiverResponse(ReceiverBase):
    id: int
    class Config:
        from_attributes = True

# Emergency Contact Schemas
class EmergencyContactBase(BaseModel):
    name: str
    phone: constr(min_length=10, max_length=10)
    email: EmailStr
    relation: str
    user_email: EmailStr  # Used to determine donor/receiver

class EmergencyContactCreate(EmergencyContactBase):
    pass

class EmergencyContactResponse(EmergencyContactBase):
    id: int
    class Config:
        from_attributes = True

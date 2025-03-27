import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Date
from sqlalchemy.orm import relationship
from database import Base

# Enum for Blood Types
class BloodType(enum.Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"

# Enum for Gender
class Gender(enum.Enum):
    MALE = 1
    FEMALE = 2
    OTHER = 3

# User Model (Base Class)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    # Define relationship with emergency contacts
    emergency_contacts = relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")

# Donor Model (inherits from User)
class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    blood_type = Column(Enum(BloodType), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(Integer, nullable=False)
    phone = Column(String(10), nullable=False)

    # Define relationship with User
    user = relationship("User", backref="donor_profile", uselist=False)

# Receiver Model (inherits from User)
class Receiver(Base):
    __tablename__ = "receivers"

    id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    required_blood_type = Column(Enum(BloodType), nullable=False)
    phone = Column(String(10), nullable=False)

    # Define relationship with User
    user = relationship("User", backref="receiver_profile", uselist=False)

# Emergency Contact Model
class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    phone = Column(String(10), nullable=False)
    email = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Define relationship with User
    user = relationship("User", back_populates="emergency_contacts")


from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Date, create_engine
from sqlalchemy.orm import relationship
from database import Base, engine
import enum


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

# User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": None
    }

# Donor Model
class Donor(User):
    __tablename__ = "donors"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    blood_type = Column(Enum(BloodType), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(Integer, nullable=False)
    phone = Column(String(10), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "donor"
    }

#Receiver Model 
class Receiver(User):
    __tablename__ = "receivers"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    required_blood_type = Column(Enum(BloodType), nullable=False)
    phone = Column(String(10), nullable=False)
    

    __mapper_args__ = {
        "polymorphic_identity": "receiver"
    }

#EmergencyContact Model
class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String(10), nullable=False)
    email = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=True)
    receiver_id = Column(Integer, ForeignKey("receivers.id"), nullable=True)

    donor = relationship("Donor", back_populates="emergency_contacts")
    receiver = relationship("Receiver", back_populates="emergency_contacts")


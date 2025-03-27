from fastapi import FastAPI, Depends, HTTPException, status, Form, Body
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from database import engine, SessionLocal, Base
from models import User, Donor, Receiver, EmergencyContact, BloodType, Gender
from schema import UserCreate, UserLogin, UserResponse, EmergencyContactCreate, DonorCreate, ReceiverCreate, DonorFormData, ReceiverFormData
from passlib.context import CryptContext
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from pydantic import EmailStr

app = FastAPI()

# Create all tables in the database
Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Check if User Exists (Used in Register & Login)
@app.get("/user_exists")
def user_exists(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    return {"exists": bool(user)}

# Register User
@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    # Hash the password
    hashed_password = pwd_context.hash(user.password)
    
    # Create new user
    db_user = User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# Login User
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    # Find user by email
    db_user = db.query(User).filter(User.email == user.email).first()
    
    # Verify user exists and password is correct
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )

    # Check if user is a donor or receiver
    is_donor = db.query(Donor).filter(Donor.id == db_user.id).first() is not None
    is_receiver = db.query(Receiver).filter(Receiver.id == db_user.id).first() is not None
    
    return JSONResponse(content={
        "message": "Login successful", 
        "user_id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "is_donor": is_donor,
        "is_receiver": is_receiver,
        "redirect": "/dashboard"
    })

# Process Donor Form (set.html)
@app.post("/submit-donor-form")
async def submit_donor_form(form_data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    # Extract email from form data
    email = form_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Find the user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if donor profile already exists
    existing_donor = db.query(Donor).filter(Donor.id == user.id).first()
    if existing_donor:
        raise HTTPException(status_code=400, detail="Donor profile already exists for this user")
    
    # Extract relevant data from form
    try:
        # Map blood group from form to BloodType enum
        blood_group = form_data.get("bloodGroup", "O+")
        blood_type = map_blood_group_to_enum(blood_group)
        
        # Parse date of birth
        dob_str = form_data.get("dob")
        dob = date.fromisoformat(dob_str) if dob_str else date.today()
        
        # Map gender from form to Gender enum
        gender_str = form_data.get("gender", "").upper()
        gender = 1  # Default to MALE
        if gender_str == "FEMALE":
            gender = 2
        elif gender_str == "OTHER":
            gender = 3
        
        # Get phone number
        phone = form_data.get("mobile", "")
        if not phone:
            phone = form_data.get("homePhone", "")
        
        # Create donor profile
        donor = Donor(
            id=user.id,
            blood_type=blood_type,
            dob=dob,
            gender=gender,
            phone=phone
        )
        
        db.add(donor)
        db.commit()
        
        # Process emergency contacts if provided
        emergency_contacts = []
        
        # You can extract emergency contact information if it's in the form
        # For now, we'll assume it's not part of this form
        
        return {"message": "Donor profile created successfully", "user_id": user.id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing donor form: {str(e)}")

# Process Recipient Form (setupr.html)
@app.post("/submit-recipient-form")
async def submit_recipient_form(form_data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    # Extract email from form data
    email = form_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Find the user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if receiver profile already exists
    existing_receiver = db.query(Receiver).filter(Receiver.id == user.id).first()
    if existing_receiver:
        raise HTTPException(status_code=400, detail="Recipient profile already exists for this user")
    
    # Extract relevant data from form
    try:
        # Get required blood type
        blood_unit = form_data.get("bloodUnit", "wholeBlood")
        required_blood_type = map_blood_unit_to_blood_type(blood_unit)
        
        # Get phone number
        phone = form_data.get("contactDetails", "")
        if not phone:
            phone = form_data.get("doctorMobile", "")
        
        # Create receiver profile
        receiver = Receiver(
            id=user.id,
            required_blood_type=required_blood_type,
            phone=phone
        )
        
        db.add(receiver)
        db.commit()
        
        # Process emergency contacts if provided
        # For now, we'll assume it's not part of this form
        
        return {"message": "Recipient profile created successfully", "user_id": user.id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing recipient form: {str(e)}")

# Add Emergency Contacts
@app.post("/add-emergency-contacts/{user_id}")
def add_emergency_contacts(
    user_id: int, 
    contacts: List[EmergencyContactCreate], 
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if user is a donor or receiver
    is_donor = db.query(Donor).filter(Donor.id == user_id).first() is not None
    is_receiver = db.query(Receiver).filter(Receiver.id == user_id).first() is not None
    
    if not (is_donor or is_receiver):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User must be registered as a donor or receiver to add emergency contacts"
        )
    
    # Check if adding these contacts would exceed the limit of 2
    existing_contacts_count = db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).count()
    if existing_contacts_count + len(contacts) > 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"User can have at most 2 emergency contacts. Currently has {existing_contacts_count}."
        )
    
    # Add emergency contacts
    for contact_data in contacts:
        contact = EmergencyContact(
            name=contact_data.name,
            phone=contact_data.phone,
            email=contact_data.email,
            relation=contact_data.relation,
            user_id=user_id
        )
        db.add(contact)
    
    db.commit()
    
    return {"message": "Emergency contacts added successfully"}

# Dashboard Route
@app.get("/dashboard/{user_id}")
def dashboard(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get user profile information
    donor = db.query(Donor).filter(Donor.id == user_id).first()
    receiver = db.query(Receiver).filter(Receiver.id == user_id).first()
    
    # Get emergency contacts
    emergency_contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).all()
    
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        },
        "is_donor": donor is not None,
        "is_receiver": receiver is not None,
        "donor_profile": {
            "blood_type": donor.blood_type.value if donor else None,
            "dob": donor.dob.isoformat() if donor else None,
            "gender": donor.gender if donor else None,
            "phone": donor.phone if donor else None
        } if donor else None,
        "receiver_profile": {
            "required_blood_type": receiver.required_blood_type.value if receiver else None,
            "phone": receiver.phone if receiver else None
        } if receiver else None,
        "emergency_contacts": [
            {
                "id": contact.id,
                "name": contact.name,
                "phone": contact.phone,
                "email": contact.email,
                "relation": contact.relation
            } for contact in emergency_contacts
        ]
    }

# Helper functions
def map_blood_group_to_enum(blood_group: str) -> BloodType:
    """Map blood group string to BloodType enum"""
    blood_group = blood_group.upper().strip()
    mapping = {
        "A+": BloodType.A_POSITIVE,
        "A-": BloodType.A_NEGATIVE,
        "B+": BloodType.B_POSITIVE,
        "B-": BloodType.B_NEGATIVE,
        "AB+": BloodType.AB_POSITIVE,
        "AB-": BloodType.AB_NEGATIVE,
        "O+": BloodType.O_POSITIVE,
        "O-": BloodType.O_NEGATIVE
    }
    return mapping.get(blood_group, BloodType.O_POSITIVE)  # Default to O+ if not found

def map_blood_unit_to_blood_type(blood_unit: str) -> BloodType:
    """Map blood unit type to a default BloodType enum"""
    # For simplicity, we'll map different blood products to specific blood types
    # In a real application, you might want to handle this differently
    mapping = {
        "wholeBlood": BloodType.O_POSITIVE,  # O+ is universal donor for red blood cells
        "packedCells": BloodType.O_NEGATIVE,  # O- is universal donor for packed cells
        "ffp": BloodType.AB_POSITIVE,        # AB+ is universal recipient
        "plasma": BloodType.AB_POSITIVE,     # AB+ is universal recipient for plasma
        "plateletConc": BloodType.A_POSITIVE  # Default to A+ for platelets
    }
    return mapping.get(blood_unit, BloodType.O_POSITIVE)  # Default to O+ if not found

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


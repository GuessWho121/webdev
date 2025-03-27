from fastapi import FastAPI, Depends, HTTPException, status, Form, Body, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
from datetime import date
import enum

from database import engine, SessionLocal, Base
from models import User, Donor, Receiver, EmergencyContact, BloodType, Gender
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Create all tables in the database
Base.metadata.create_all(bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    mapping = {
        "wholeBlood": BloodType.O_POSITIVE,  # O+ is universal donor for red blood cells
        "packedCells": BloodType.O_NEGATIVE,  # O- is universal donor for packed cells
        "ffp": BloodType.AB_POSITIVE,        # AB+ is universal recipient
        "plasma": BloodType.AB_POSITIVE,     # AB+ is universal recipient for plasma
        "plateletConc": BloodType.A_POSITIVE  # Default to A+ for platelets
    }
    return mapping.get(blood_unit, BloodType.O_POSITIVE)  # Default to O+ if not found

# API Routes

# Check if User Exists (Used in Register & Login)
@app.get("/api/user_exists")
def user_exists(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    return {"exists": bool(user)}

# Register User
@app.post("/api/register")
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    userType: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    # Validate password
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long")

    # Hash the password
    hashed_password = pwd_context.hash(password)
    
    # Create new user
    db_user = User(name=name, email=email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Return response based on user type
    if userType == "donor":
        return JSONResponse(content={
            "message": "Registration successful",
            "user_id": db_user.id,
            "email": db_user.email,
            "redirect": "/set.html"
        })
    else:  # recipient
        return JSONResponse(content={
            "message": "Registration successful",
            "user_id": db_user.id,
            "email": db_user.email,
            "redirect": "/setupr.html"
        })

# Login User
@app.post("/api/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Find user by email
    db_user = db.query(User).filter(User.email == email).first()
    
    # Verify user exists and password is correct
    if not db_user or not pwd_context.verify(password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )

    # Check if user is a donor or receiver
    is_donor = db.query(Donor).filter(Donor.id == db_user.id).first() is not None
    is_receiver = db.query(Receiver).filter(Receiver.id == db_user.id).first() is not None
    
    # If user hasn't completed their profile, redirect to appropriate form
    if not is_donor and not is_receiver:
        return JSONResponse(content={
            "message": "Please complete your profile",
            "user_id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "redirect": "/set.html"  # Default to donor form, can be changed based on user preference
        })
    
    return JSONResponse(content={
        "message": "Login successful", 
        "user_id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "is_donor": is_donor,
        "is_receiver": is_receiver,
        "redirect": "/dashboard.html"
    })

# Process Donor Form (set.html)
@app.post("/api/submit-donor-form")
async def submit_donor_form(
    email: str = Form(...),
    name: Optional[str] = Form(None),
    bloodGroup: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    mobile: Optional[str] = Form(None),
    homePhone: Optional[str] = Form(None),
    # Emergency contact 1
    name1: str = Form(...),
    phone1: str = Form(...),
    email1: str = Form(...),
    relation1: str = Form(...),
    # Emergency contact 2
    name2: Optional[str] = Form(None),
    phone2: Optional[str] = Form(None),
    email2: Optional[str] = Form(None),
    relation2: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Find the user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if donor profile already exists
    existing_donor = db.query(Donor).filter(Donor.id == user.id).first()
    if existing_donor:
        raise HTTPException(status_code=400, detail="Donor profile already exists for this user")
    
    # Check if receiver profile exists (user can't be both)
    existing_receiver = db.query(Receiver).filter(Receiver.id == user.id).first()
    if existing_receiver:
        raise HTTPException(status_code=400, detail="User is already registered as a receiver")
    
    try:
        # Map blood group to enum
        blood_type = map_blood_group_to_enum(bloodGroup)
        
        # Parse date of birth
        dob_date = date.fromisoformat(dob) if dob else date.today()
        
        # Map gender
        gender_enum = 1  # Default to MALE
        if gender.upper() == "FEMALE":
            gender_enum = 2
        elif gender.upper() == "OTHER":
            gender_enum = 3
        
        # Get phone number
        phone = mobile if mobile else homePhone
        if not phone:
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        # Create donor profile
        donor = Donor(
            id=user.id,
            blood_type=blood_type,
            dob=dob_date,
            gender=gender_enum,
            phone=phone
        )
        
        db.add(donor)
        
        # Add first emergency contact (required)
        emergency_contact1 = EmergencyContact(
            name=name1,
            phone=phone1,
            email=email1,
            relation=relation1,
            user_id=user.id
        )
        db.add(emergency_contact1)
        
        # Add second emergency contact if provided
        if name2 and phone2 and email2 and relation2:
            emergency_contact2 = EmergencyContact(
                name=name2,
                phone=phone2,
                email=email2,
                relation=relation2,
                user_id=user.id
            )
            db.add(emergency_contact2)
        
        db.commit()
        
        return JSONResponse(content={
            "message": "Donor profile created successfully", 
            "user_id": user.id,
            "redirect": "/dashboard.html"
        })
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing donor form: {str(e)}")

# Process Recipient Form (setupr.html)
@app.post("/api/submit-recipient-form")
async def submit_recipient_form(
    email: str = Form(...),
    bloodUnit: str = Form(...),
    contactDetails: Optional[str] = Form(None),
    doctorMobile: Optional[str] = Form(None),
    # Emergency contact 1
    name1: str = Form(...),
    phone1: str = Form(...),
    email1: str = Form(...),
    relation1: str = Form(...),
    # Emergency contact 2
    name2: Optional[str] = Form(None),
    phone2: Optional[str] = Form(None),
    email2: Optional[str] = Form(None),
    relation2: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Find the user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if receiver profile already exists
    existing_receiver = db.query(Receiver).filter(Receiver.id == user.id).first()
    if existing_receiver:
        raise HTTPException(status_code=400, detail="Recipient profile already exists for this user")
    
    # Check if donor profile exists (user can't be both)
    existing_donor = db.query(Donor).filter(Donor.id == user.id).first()
    if existing_donor:
        raise HTTPException(status_code=400, detail="User is already registered as a donor")
    
    try:
        # Get required blood type
        required_blood_type = map_blood_unit_to_blood_type(bloodUnit)
        
        # Get phone number
        phone = contactDetails if contactDetails else doctorMobile
        if not phone:
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        # Create receiver profile
        receiver = Receiver(
            id=user.id,
            required_blood_type=required_blood_type,
            phone=phone
        )
        
        db.add(receiver)
        
        # Add first emergency contact (required)
        emergency_contact1 = EmergencyContact(
            name=name1,
            phone=phone1,
            email=email1,
            relation=relation1,
            user_id=user.id
        )
        db.add(emergency_contact1)
        
        # Add second emergency contact if provided
        if name2 and phone2 and email2 and relation2:
            emergency_contact2 = EmergencyContact(
                name=name2,
                phone=phone2,
                email=email2,
                relation=relation2,
                user_id=user.id
            )
            db.add(emergency_contact2)
        
        db.commit()
        
        return JSONResponse(content={
            "message": "Recipient profile created successfully", 
            "user_id": user.id,
            "redirect": "/dashboard.html"
        })
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing recipient form: {str(e)}")

# Get User Profile
@app.get("/api/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get user profile information
    donor = db.query(Donor).filter(Donor.id == user_id).first()
    receiver = db.query(Receiver).filter(Receiver.id == user_id).first()
    
    # Get emergency contacts
    emergency_contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).all()
    
    # Calculate age if DOB is available
    age = None
    if donor and donor.dob:
        today = date.today()
        age = today.year - donor.dob.year - ((today.month, today.day) < (donor.dob.month, donor.dob.day))
    
    # Format gender
    gender_str = None
    if donor and donor.gender:
        gender_map = {1: "Male", 2: "Female", 3: "Other"}
        gender_str = gender_map.get(donor.gender)
    
    # Format blood type and Rh factor
    blood_group = None
    rh_factor = None
    if donor and donor.blood_type:
        blood_group = donor.blood_type.value
        rh_factor = "Positive" if "+" in blood_group else "Negative"
    elif receiver and receiver.required_blood_type:
        blood_group = receiver.required_blood_type.value
        rh_factor = "Positive" if "+" in blood_group else "Negative"
    
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        },
        "is_donor": donor is not None,
        "is_receiver": receiver is not None,
        "profile": {
            "blood_group": blood_group,
            "rh_factor": rh_factor,
            "dob": donor.dob.isoformat() if donor and donor.dob else None,
            "age": age,
            "gender": gender_str,
            "phone": donor.phone if donor else (receiver.phone if receiver else None)
        },
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

# Dashboard Route
@app.get("/api/dashboard/{user_id}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


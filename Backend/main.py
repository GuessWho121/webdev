from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from database import engine, SessionLocal, Base
from models import User, Donor, Receiver, EmergencyContact, BloodType, Gender
from schema import UserCreate, UserLogin, UserResponse, EmergencyContactCreate, DonorCreate, ReceiverCreate
from passlib.context import CryptContext
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Check if User Exists
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

# Register Donor
@app.post("/register/donor", status_code=status.HTTP_201_CREATED)
def register_donor(donor_data: DonorCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.email == donor_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. Please register as a user first.")
    
    # Check if donor profile already exists
    existing_donor = db.query(Donor).filter(Donor.id == user.id).first()
    if existing_donor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Donor profile already exists for this user")
    
    # Create donor profile
    donor = Donor(
        id=user.id,
        blood_type=donor_data.blood_type,
        dob=donor_data.dob,
        gender=donor_data.gender,
        phone=donor_data.phone
    )
    
    db.add(donor)
    db.commit()
    
    return {"message": "Donor profile created successfully", "user_id": user.id}

# Register Receiver
@app.post("/register/receiver", status_code=status.HTTP_201_CREATED)
def register_receiver(receiver_data: ReceiverCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.email == receiver_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. Please register as a user first.")
    
    # Check if receiver profile already exists
    existing_receiver = db.query(Receiver).filter(Receiver.id == user.id).first()
    if existing_receiver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receiver profile already exists for this user")
    
    # Create receiver profile
    receiver = Receiver(
        id=user.id,
        required_blood_type=receiver_data.required_blood_type,
        phone=receiver_data.phone
    )
    
    db.add(receiver)
    db.commit()
    
    return {"message": "Receiver profile created successfully", "user_id": user.id}

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

# Get Emergency Contacts
@app.get("/emergency-contacts/{user_id}")
def get_emergency_contacts(user_id: int, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get emergency contacts
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).all()
    
    return [
        {
            "id": contact.id,
            "name": contact.name,
            "phone": contact.phone,
            "email": contact.email,
            "relation": contact.relation
        } for contact in contacts
    ]

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



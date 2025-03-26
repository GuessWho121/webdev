from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import User, Donor, Receiver
from schema import UserCreate, UserLogin, UserResponse
from passlib.context import CryptContext

app = FastAPI()

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Register User (Donor/Receiver)
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = pwd_context.hash(user.password)
    db_user = User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Login User
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "user_id": db_user.id}

# Add Emergency Contacts
@app.post("/add-emergency-contacts/")
def add_emergency_contacts(contacts: List[EmergencyContactCreate], db: Session = Depends(get_db)):
    if len(contacts) > 2:
        raise HTTPException(status_code=400, detail="Only 2 emergency contacts allowed per user.")

    user = db.query(User).filter(User.email == contacts[0].user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_contacts = db.query(EmergencyContact).filter(EmergencyContact.user_email == user.email).count()
    if existing_contacts + len(contacts) > 2:
        raise HTTPException(status_code=400, detail="User already has emergency contacts assigned.")

    emergency_contacts = [EmergencyContact(**contact.dict()) for contact in contacts]
    db.add_all(emergency_contacts)
    db.commit()
    return {"message": "Emergency contacts added successfully"}
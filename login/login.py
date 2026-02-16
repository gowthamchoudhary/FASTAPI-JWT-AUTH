from fastapi import FastAPI, Depends, HTTPException,UploadFile
from passlib.context import CryptContext
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# ==============================
# DATABASE CONFIG
# ==============================

DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

app = FastAPI()

# ==============================
# PASSWORD HASHING
# ==============================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_hash_pwd(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

# ==============================
# DATABASE DEPENDENCY
# ==============================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================
# DATABASE MODEL
# ==============================

class Users(Base):
    __tablename__ = "users"   # IMPORTANT: no space, no comma

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

# Create tables AFTER model definition
Base.metadata.create_all(bind=engine)

# ==============================
# Pydantic Schemas
# ==============================

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    name: str
    password: str

# ==============================
# ROUTES
# ==============================

@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(Users).filter(Users.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = Users(
        name=user.name,
        email=user.email,
        password=generate_hash_pwd(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}


@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    user_db = db.query(Users).filter(Users.name == user.name).first()

    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(user.password, user_db.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {"message": "Login successful"}


UPLOAD_DIRS = "/uploads"
@app.post("/upload")
def upload_profile_pic(files:list[UploadFile]):
    try:
        for file in files:
            file_path = os.path.join(UPLOAD_DIRS,file.filename)
            with open(file_path,'wb') as f:
                f.write(file.file.read())
            return {"message": "File uploaded successfully"}
    except Exception as e:
        return {"error":e.args}
            
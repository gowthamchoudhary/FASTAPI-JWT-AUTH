from fastapi import FastAPI,HTTPException,status
from typing import Annotated
from jose import jwt,JWTError
from datetime import datetime,timedelta,timezone
from fastapi import Depends
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from sqlalchemy.orm import session,sessionmaker
from sqlalchemy import select,create_engine,Column,Integer,String,MetaData,Select
from passlib.context import CryptContext
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = 'postgresql://neondb_owner:npg_M6GBcCYxv2FS@ep-sparkling-butterfly-a1a2czfr-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
SECRET_KEY = "4a2b69e097019a3dbd213c1615def2cb382c9e139cff7417fe8ce3da908075f3"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
#--------------------------------------------------------------------------------------------------------------
app = FastAPI()
engine = create_engine(DATABASE_URL, echo=True)

sessionLocal = sessionmaker(bind=engine,autoflush=False,autocommit=False)
Base = declarative_base()
metadata = MetaData()
#----------------------------------------------------------------------------------------------------------------
class User(Base):
    __tablename__ = "Users"
    id = Column(Integer,primary_key = True,index = True)
    username = Column(String(100),index=True)
    email = Column(String(100),unique=True)
    hashed_password = Column(String)
Base.metadata.create_all(engine)

class Create_user(BaseModel):
    username:str
    email:str
    password:str
class User_response(BaseModel):
    id:int
    username:str
    email:str
#-------------------------------------------------------------------------------------------------------------------------------------------------------------
def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
#----------------------------------------------------------------------------------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Hello World"}

@app.post("/user/",response_model=User_response)
async def create_user(user:Create_user,db:session=Depends(get_db)):
    # db_user = User(**user.model_dump())
   
    db_user = db.query(User).filter(User.email==user.email).first()
    if db_user:
        raise HTTPException(status_code=400,detail="Email already Registered")
    db_user = User(username=user.username,email=user.email,hashed_password=get_hashed_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/user/{user_email}/",response_model=User_response)
async def Extrat_user(user_email:str,db:session=Depends(get_db)):
    db_user = db.query(User).filter(User.email==user_email).first()
    if db_user is None:
        raise HTTPException(status_code=404,detail="user Not Found")
    return db_user


#--------------------------------------------------------------------------------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"])
@app.post("/login")
def login(form_data:OAuth2PasswordRequestForm = Depends(),db:session=Depends(get_db)):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
         raise HTTPException(status_code=4041,detail="Authentication")
    
    access_token = create_token(data = {"sub":user.email})
    return {"access_token":access_token,"token_type":"bearer"}
#---------------------------------------------------------------------------------------------------------------------------------------
def get_user(username:str,db):
    db_user = db.query(User).filter(User.username==username).first()
    if not db_user:
        return None
    return db_user
def authenticate_user(username,password,db):
    db_user = get_user(username,db)
    if not db_user:
        return None
    if not verify_password(password,db_user.hashed_password):
        return None
    return db_user

def verify_password(password,hashed):
    return pwd_context.verify(password,hashed)
def get_hashed_password(password):
    return pwd_context.hash(password)

#------------------------------------------------------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
 
def create_token(data:dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)+(timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

def verify_token(token:str):
        try:
            payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
            return   payload
        except JWTError:
             return None
def get_current_user(token: Annotated[str,Depends(oauth2_scheme)],db=Depends((get_db))):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=404,detail="Invalid")
    # user = db.query(select(User).where(User.email==payload.get("sub"))).first()
    user = db.query(User).filter(User.email==payload.get("sub")).first()

    if not user:
        raise HTTPException(status_code= 404,detail="bro whats wrong with you ")
    return user

    
    
@app.get("/me",response_model=User_response)
def read_me(current_user = Depends(get_current_user)):
    return current_user

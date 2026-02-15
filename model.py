from typing import Optional
from sqlmodel import SQLModel ,Field
from pydantic import EmailStr


class User(SQLModel, table=True):
    id:Optional[int] = Field(default=None,primary_key=True)
    name:str
    eamil   :EmailStr
    phone :int
    file_path:str
class CreateUser(SQLModel):
    name:str
    phone:int
    email:EmailStr

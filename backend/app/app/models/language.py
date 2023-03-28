
from sqlalchemy import Column, Integer, String,DateTime,Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class Language(Base):
    id=Column(Integer,primary_key=True)
    name=Column(String(250))
    created_at=Column(DateTime)
    status=Column(TINYINT)
    
    user_settings=relationship("UserSettings",back_populates="language")   
    
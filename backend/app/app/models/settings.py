from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class Settings(Base):
    #__table_args__ = {'extend_existing': True}
    id=Column(Integer,primary_key=True)
    settings_topic=Column(String(100))
    settings_value=Column(String(250))
    created_at=Column(DateTime)
    status=Column(TINYINT,default=1)    
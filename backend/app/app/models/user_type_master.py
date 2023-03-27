from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class UserTypeMaster(Base):
    #__table_args__ = {'extend_existing': True}
    __tablename__="user_type_master"
    id=Column(Integer,primary_key=True)
    name=Column(String(100))
    description=Column(String(255))
    created_at=Column(DateTime)
    status=Column(TINYINT,default=1)
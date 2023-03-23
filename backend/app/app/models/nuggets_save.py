from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class NuggetsSave(Base):
    __tablename__="nuggets_save"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,comment=" user table id ")  # ForeignKey("user.id")
    nugget_id=Column(Integer,comment=" nuggets table id ") # ForeignKey("nuggets.id")
    created_date=Column(DateTime)
    status=Column(TINYINT,default=1,comment=" 0-Inactive, 1-Active ")
    
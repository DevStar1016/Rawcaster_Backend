from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class NuggetsLikes(Base):
    __tablename__="nuggets_likes"
    id=Column(Integer,primary_key=True)
    nugget_id=Column(Integer,ForeignKey("nuggets.id"),comment=" nuggets table id ")
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table id ")
    created_date=Column(DateTime)
    status=Column(TINYINT,default=1)
    
    user=relationship("User",back_populates="nuggets_likes")
    nuggets=relationship("Nuggets",back_populates="nuggets_likes")
    
    
    
from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class NuggetsMaster(Base):
    __tablename__="nuggets_master"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"))
    content=Column(Text)
    metadata1=Column(BLOB)  #BLOB
    poll_duration=Column(String(15))
    created_date=Column(DateTime)
    modified_date=Column(DateTime)
    status=Column(TINYINT,comment=" 0-Inactive, 1-Active ")
    
    user=relationship("User",back_populates="nuggets_master")
    nuggets=relationship("Nuggets",back_populates="nuggets_master")
    nugget_hash_tags=relationship("NuggetHashTags",back_populates="nuggets_master")
    nugget_poll_voted=relationship("NuggetPollVoted",back_populates="nuggets_master")
    nuggets_attachment=relationship("NuggetsAttachment",back_populates="nuggets_master")
    
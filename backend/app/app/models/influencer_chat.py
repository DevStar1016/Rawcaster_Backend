
from sqlalchemy import Column, Integer, Text,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class InfluencerChat(Base):
    __tablename__="influencer_chat"
    id=Column(Integer,primary_key=True)
    sender_id=Column(Integer,ForeignKey("user.id"),comment="user table ref")
    receiver_id=Column(Integer,ForeignKey("user.id"),comment="user table ref")
    message=Column(Text)
    created_at=Column(DateTime)
    status=Column(TINYINT,nullable=False,default=1,comment="0->Inactive, 1->Active")    
    
    user1=relationship("User",foreign_keys=[sender_id])
    user2=relationship("User",foreign_keys=[receiver_id])

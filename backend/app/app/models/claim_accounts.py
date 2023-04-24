from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class ClaimAccounts(Base):
    __tablename__="claim_accounts"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ")
    influencer_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id")
    first_name=Column(String(100))
    last_name=Column(String(100))
    telephone=Column(String(20))
    email_id=Column(String(100))
    dob=Column(Date)
    location=Column(String(100))
    claim_date=Column(DateTime)
    admin_status=Column(TINYINT,default=0,comment="0-pending")
    created_at=Column(DateTime)
    status=Column(TINYINT,comment="1-Active,0-Inactive")
    
    user1=relationship("User",foreign_keys=[user_id])
    user2=relationship("User",foreign_keys=[influencer_id])
    
   
    
    
from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class OtpLog(Base):
    __tablename__="otp_log"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ") 
    otp=Column(Integer)
    otp_type=Column(TINYINT,comment=" 1->Signup, 2->Login, 3->Forgot password ")
    created_date=Column(DateTime)
    status=Column(TINYINT,default=1,comment=" 0->Inactive, 1->Active ")
    nugget_poll_voted=relationship("NuggetPollVoted",back_populates="nugget_poll_option")
    
    
    user=relationship("User",back_populates="otp_log")
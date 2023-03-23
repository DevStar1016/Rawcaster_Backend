from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL,BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class SignupLog(Base):
    __tablename__="signup_log"
    id=Column(BigInteger,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ") 
    ip=Column(String(50))
    device_type=Column(TINYINT,comment=" 1->Web, 2->Android, 3->IOS ")
    device_details=Column(Text)
    created_date=Column(DateTime)
    status=Column(TINYINT,default=1,comment=" 0->inactive, 1->active ")
    
    user=relationship("User",back_populates="signup_log")
    
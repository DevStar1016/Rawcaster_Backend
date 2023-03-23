from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class UserLoginLog(Base):
    __tablename__="user_login_log"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ") 
    date_time=Column(DateTime)
    login_status=Column(TINYINT,comment=" 0->Failed, 1->success ")
    device_type=Column(TINYINT,comment=" 1->Web, 2->Android, 3->IOS ")
    device_details=Column(Text)
    ip=Column(String(50))
    status=Column(TINYINT,default=1,comment=" 0->inactive, 1->active ")
    
    user=relationship("User",back_populates="user_login_log")
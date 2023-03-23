from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,BigInteger,Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class NotificationSmsEmail(Base):
    __tablename__="notification_sms_email"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"))
    type=Column(TINYINT,default=1,comment=" 1-sms,2-email ")
    mobile_no_email_id=Column(String(500))
    subject=Column(String(250))
    message=Column(Text)
    created_at=Column(DateTime)
    status=Column(TINYINT,default=0,comment="  1- active, 0-deleted  ")
    
    user1=relationship("User",foreign_keys=[user_id])

from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class ApiTokens(Base):
    __tablename__="api_tokens"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ")
    token=Column(String(100))
    created_at=Column(DateTime)
    renewed_at=Column(DateTime)
    validity=Column(TINYINT,nullable=False,default=1,comment="0->Expired, 1->Lifetime ")
    device_type=Column(TINYINT,comment=" 1->Web, 2->APP ")
    device_id=Column(String(255))
    push_device_id=Column(String(255),comment=" FCM id / APNS id based on device type ")
    app_type=Column(TINYINT,comment=" 1- Android, 2-IOS ")
    voip_token=Column(String(255),comment=" IOS VOIP Notification Token ")
    device_ip=Column(String(255))
    status=Column(TINYINT,nullable=False,default=1,comment=" -1->Deleted, 0->inactive, 1->active ")
    
    user=relationship("User",back_populates="api_tokens")
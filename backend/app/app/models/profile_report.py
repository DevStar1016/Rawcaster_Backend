from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class ProfileReport(Base):
    #__table_args__ = {'extend_existing': True}
    __tablename__="profile_report"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" report created by ")
    profile_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id - whom profile is reported ")
    report_type=Column(TINYINT)
    message=Column(String(500))
    reported_date=Column(DateTime)
    report_status=Column(TINYINT,default=0)
    status=Column(TINYINT,default=1,comment=" 0->Inactive, 1->Active ")
    
    user1=relationship("User",foreign_keys=[user_id])
    user2=relationship("User",foreign_keys=[profile_id])
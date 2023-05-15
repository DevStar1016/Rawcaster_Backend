from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class GroupReport(Base):
    __tablename__="group_report"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"))
    group_id=Column(Integer,ForeignKey("friend_groups.id"))
    message=Column(String(500))
    reported_date=Column(DateTime)
    report_status=Column(TINYINT,default=0)

    status=Column(TINYINT,comment="0-inactive,1-active ",default=1)
    
    user=relationship("User",back_populates="group_report")
    friend_groups=relationship("FriendGroups",back_populates="group_report")
    
    
    
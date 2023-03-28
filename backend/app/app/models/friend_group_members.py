from sqlalchemy import Column, Integer, String,DateTime,Text,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class FriendGroupMembers(Base):
    __tablename__="friend_group_members"
    id=Column(Integer,primary_key=True)
    group_id=Column(Integer,ForeignKey("friend_groups.id"),comment=" friend_groups table ref id ")
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ")
    added_date=Column(DateTime)
    added_by=Column(Integer,comment=" user table ref id ")
    is_admin=Column(TINYINT(1),default=0)
    disable_notification=Column(TINYINT(1),default=0)
    status=Column(TINYINT(1),comment="  0->inactive, 1->active  ")
    
    user=relationship("User",back_populates="friend_group_members")
    friend_groups=relationship("FriendGroups",back_populates="friend_group_members")

from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class UserProfileDisplayGroup(Base):
    #__table_args__ = {'extend_existing': True}
    __tablename__="user_profile_display_group"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"))
    profile_id=Column(String(50))
    groupid=Column(Integer,ForeignKey("friend_groups.id"))
    created_date=Column(DateTime)
    status=Column(TINYINT,default=1)
    
    user=relationship("User",back_populates="user_profile_display_group")
    friend_groups=relationship("FriendGroups",back_populates="user_profile_display_group")
    
    
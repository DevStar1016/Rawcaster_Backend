from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class FriendGroups(Base):
    #__table_args__ = {'extend_existing': True}
    __tablename__="friend_groups"
    id=Column(Integer,primary_key=True)
    group_name=Column(String(255))
    group_icon=Column(String(255))
    created_by=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ")
    created_at=Column(DateTime)
    chat_enabled=Column(TINYINT,nullable=False,default=1)
    warning_mail_count=Column(Integer,nullable=False,default=0)
    warning_mail_status=Column(TINYINT,nullable=False,default=0)
    warning_mail_sent_date=Column(DateTime)
    status=Column(TINYINT,nullable=False,default=1,comment="0->Inactive, 1->Active")
    
    event_invitations=relationship("EventInvitations",back_populates="friend_groups")
    user=relationship("User",back_populates="friend_groups")
    friend_group_members=relationship("FriendGroupMembers",back_populates="friend_groups")
    group_chat=relationship("GroupChat",back_populates="friend_groups")
    group_report=relationship("GroupReport",back_populates="friend_groups")
    user_profile_display_group=relationship("UserProfileDisplayGroup",back_populates="friend_groups")
    
    
    
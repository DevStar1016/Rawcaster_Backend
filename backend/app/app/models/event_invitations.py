from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class EventInvitations(Base):
    __tablename__="event_invitations"
    id=Column(Integer,primary_key=True)
    type=Column(TINYINT(4),comment=" 1- Friend, 2- Group, 3-Custom ")
    event_id=Column(Integer,ForeignKey("events.id"),comment=" events table ID ")
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ID ")
    group_id=Column(Integer,ForeignKey("friend_groups.id"),comment=" friend_groups table ID ")
    invite_mail=Column(String(255))
    invite_sent=Column(TINYINT(1),default=0)
    is_changed=Column(TINYINT(1),default=0)
    created_at=Column(DateTime)
    created_by=Column(Integer,ForeignKey("user.id"))
    status=Column(TINYINT(1),nullable=False,default=1,comment="0->Inactive, 1->Active")
    
    events=relationship("Events",back_populates="event_invitations")
    user1=relationship("User",foreign_keys=[user_id])
    user2=relationship("User",foreign_keys=[created_by])
    friend_groups=relationship("FriendGroups",back_populates="event_invitations")
    
    
    
    
from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class FollowUser(Base):
    __tablename__="follow_user"
    id=Column(Integer,primary_key=True)
    follower_userid=Column(Integer,ForeignKey("user.id"))
    following_userid=Column(Integer,ForeignKey("user.id"))
    created_at=Column(DateTime)
    status=Column(TINYINT(1),comment=" -1-deleted,0-inactive,1-active ")
    
    user1=relationship("User",foreign_keys=[follower_userid])
    user2=relationship("User",foreign_keys=[following_userid])
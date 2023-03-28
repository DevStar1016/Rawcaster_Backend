
from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class Notification(Base):
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment="  user table ref id - who receive this notification  ")
    notification_origin_id=Column(Integer,ForeignKey("user.id"),comment="  user table ref id - who send this notification  ")
    notification_type=Column(TINYINT,comment=" 1-nugget create, 2-Nugget Edit, 3-Nugget Comment, 4-nugget Reply, 5-Nugget Like, 6-nugget comment like, 7-Nugget reply like,8-Nugget share, 9-event create, 10-event edit, 11-friend request, 12-friend request approved ")
    ref_id=Column(BigInteger)
    is_read=Column(TINYINT,default=0)
    read_datetime=Column(DateTime)
    created_datetime=Column(DateTime)
    deleted_datetime=Column(DateTime)
    status=Column(TINYINT,default=1,comment="  1- active, 0-deleted  ")
    
    user1=relationship("User",foreign_keys=[user_id])
    user2=relationship("User",foreign_keys=[notification_origin_id])
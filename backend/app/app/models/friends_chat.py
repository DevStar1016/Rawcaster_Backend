from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BigInteger,Time
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class FriendsChat(Base):
    __tablename__="friends_chat"
    id=Column(Integer,primary_key=True)
    msg_code=Column(String(30),comment=" unique code for each chat set by send device ")
    sender_id=Column(Integer,ForeignKey("user.id"))
    receiver_id=Column(Integer,ForeignKey("user.id"))
    sent_type=Column(TINYINT(4),default=1,comment=" 1-Normal,2-reply,3-forward,4-Call ")
    call_duration=Column(Time)
    call_status=Column(TINYINT(1),comment=" 0-Missed call,1-Accepted,2-Ongoing,3-Rejected ")
    parent_msg_id=Column(BigInteger) #ForeignKey("friends_chat.id")
    forwarded_from=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ")
    type=Column(TINYINT(1),default=1,comment=" 1-text,2-image,3-audio,4-video,5-file,6-Audio Call,7-Video Call ")
    msg_from=Column(TINYINT(1),default=1,comment=" 1-web ,2-mobile ")
    message=Column(Text)
    path=Column(String(255))
    sent_datetime=Column(DateTime)
    is_read=Column(TINYINT(1),default=0)
    is_edited=Column(TINYINT(1),default=0,comment=" is edited 1-true 0-false ")
    read_datetime=Column(DateTime)
    is_deleted_for_both=Column(TINYINT(1),default=0)
    sender_delete=Column(Integer)
    receiver_delete=Column(Integer)
    sender_deleted_datetime=Column(DateTime)
    receiver_deleted_datetime=Column(DateTime)

    status=Column(TINYINT(1),nullable=False,default=1,comment="0->Inactive, 1->Active")
    
    # friends_chat=relationship("FriendsChat",back_populates="friends_chat")
    user1=relationship("User",foreign_keys=[sender_id])
    user2=relationship("User",foreign_keys=[receiver_id])
    user3=relationship("User",foreign_keys=[forwarded_from])
    
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    BigInteger,
    Time,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class GroupChat(Base):
    __tablename__ = "group_chat"
    id = Column(Integer, primary_key=True)
    msg_code = Column(
        String(30), comment=" unique code for each chat set by send device "
    )
    group_id = Column(Integer, ForeignKey("friend_groups.id"))
    sender_id = Column(Integer, ForeignKey("user.id"))
    sent_type = Column(
        TINYINT(4), default=1, comment=" 1-Normal,2-reply,3-forward,4-Call "
    )
    call_duration = Column(Time)
    call_status = Column(
        TINYINT(1), comment=" 0-Missed call,1-Accepted,2-Ongoing,3-Rejected "
    )
    parent_msg_id = Column(BigInteger)
    forwarded_from = Column(Integer, comment=" user table ref id ")
    type = Column(
        TINYINT(1),
        default=1,
        comment=" 1-text,2-image,3-audio,4-video,5-file,6-Audio Call,7-Video Call ",
    )
    msg_from = Column(TINYINT(4), default=1, comment=" 1-web ,2-mobile ")
    message = Column(Text)
    path = Column(String(255))
    sent_datetime = Column(DateTime)
    is_edited = Column(TINYINT(1), default=0, comment=" is edited 1-true 0-false ")
    is_deleted_for_all = Column(
        TINYINT(1), default=0, comment=" 0 - No, 1 - all, 2-me "
    )
    status = Column(TINYINT(1), comment="0-inactive,1-active ")

    user = relationship("User", back_populates="group_chat")
    friend_groups = relationship("FriendGroups", back_populates="group_chat")

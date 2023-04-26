
from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class MyFriends(Base):
    __tablename__="my_friends"
    id=Column(Integer,primary_key=True)
    sender_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ",nullable=False)
    receiver_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ",nullable=False)
    request_date=Column(DateTime)
    request_status=Column(TINYINT,comment=" 0->Pending, 1->Accepted, 2->Rejected, 3->Blocked ")
    status_date=Column(DateTime)
    status=Column(TINYINT,default=1,comment=" 0->inactive, 1->active ")
    
    user1=relationship("User",foreign_keys=[sender_id])
    user2=relationship("User",foreign_keys=[receiver_id])
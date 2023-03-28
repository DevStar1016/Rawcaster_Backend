from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class UserStatusChangeLog(Base):
    __tablename__="user_status_change_log"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,comment=" user table ref id ")
    old_status=Column(TINYINT,comment=" 0->verification pending, 1->Active, 2->Suspended, 3->Blocked, 4->Deleted ")
    new_status=Column(TINYINT,comment=" 0->verification pending, 1->Active, 2->Suspended, 3->Blocked, 4->Deleted ")
    changed_at=Column(DateTime)
    changed_by=Column(TINYINT,comment=" user table ref id ")
    note=Column(Text)
    status=Column(TINYINT,default=1,comment=" 0->inactive, 1->active ")

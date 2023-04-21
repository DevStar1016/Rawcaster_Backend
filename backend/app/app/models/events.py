from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,Time,DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class Events(Base):
    id=Column(Integer,primary_key=True)
    title=Column(String(255))
    ref_id=Column(String(255),comment=" Reference ID ")
    server_id=Column(String(10),default="US1")
    type=Column(TINYINT,nullable=False,default=1,comment=" 1 - Event, 2 - Talkshow, 3-Live ")
    description=Column(Text)
    event_type_id=Column(Integer,ForeignKey("event_types.id"),comment=" event_type table ref id ")
    event_layout_id=Column(Integer,ForeignKey("event_layouts.id"))
    event_melody_id=Column(Integer,default=1,comment=" id ref from tabelevent_melody ")
    no_of_participants=Column(Integer)
    duration=Column(Time)
    start_date_time=Column(DateTime)
    cover_img=Column(String(255))
    created_at=Column(DateTime)
    created_by=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ")
    last_updated_at=Column(DateTime)
    total_cost=Column(DECIMAL(10,2))
    paid_amount=Column(DECIMAL(10,2))
    pending_amount=Column(DECIMAL(10,2))
    payment_status=Column(TINYINT,nullable=False,default=0,comment=" 0->Pending, 1->Paid, 2->Partial paid ")
    event_status=Column(TINYINT,nullable=False,default=1,comment=" 0->Cancelled, 1->Upcoming, 2->Ongoing, 3->Completed ")
    waiting_room=Column(TINYINT)
    join_before_host=Column(TINYINT)
    sound_notify=Column(TINYINT)
    user_screenshare=Column(TINYINT)
    status=Column(TINYINT,default=1,nullable=False,comment=" 0->Inactive, 1->Active ")

    user=relationship("User",back_populates="events")
    event_types=relationship("EventTypes",back_populates="events")
    event_layouts=relationship("EventLayouts",back_populates="events")
    event_default_av=relationship("EventDefaultAv",back_populates="events")
    event_invitations=relationship("EventInvitations",back_populates="events")
    event_melody=relationship("EventMelody",back_populates="events")
    event_update_log=relationship("EventUpdateLog",back_populates="events")
    online_payment_details=relationship("OnlinePaymentDetails",back_populates="events")
    event_abuse_report=relationship("EventAbsueReport",back_populates="events")
    
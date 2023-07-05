from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Time, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT, LONGTEXT
from app.db.base_class import Base


class EventUpdateLog(Base):
    __tablename__ = "event_update_log"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), comment=" event table ref id ")
    user_id = Column(Integer, ForeignKey("user.id"), comment="  user table ref id  ")
    no_of_participants = Column(Integer)
    duration = Column(Time)
    amount = Column(DECIMAL(10, 2))
    old_participants = Column(Integer)
    old_duration = Column(Time)
    old_amount = Column(DECIMAL(10, 2))
    new_participants = Column(Integer)
    new_duration = Column(Time)
    new_amount = Column(DECIMAL(10, 2))
    created_at = Column(DateTime)
    status = Column(
        TINYINT, nullable=False, default=1, comment="0->Inactive, 1->Active"
    )

    events = relationship("Events", back_populates="event_update_log")
    user = relationship("User", back_populates="event_update_log")

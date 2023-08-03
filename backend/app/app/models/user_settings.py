from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    online_status = Column(TINYINT, default=1)
    phone_display_status = Column(TINYINT, default=2)
    location_display_status = Column(TINYINT, default=1)
    dob_display_status = Column(TINYINT, default=0)
    bio_display_status = Column(TINYINT, default=1)
    passcode_status = Column(TINYINT, default=0)
    passcode = Column(String(15))
    public_nugget_display = Column(TINYINT, default=1)
    public_event_display = Column(TINYINT, default=1)
    waiting_room = Column(TINYINT, default=1)
    schmoozing_status = Column(TINYINT, default=0)
    breakout_status = Column(TINYINT, default=0)
    join_before_host = Column(TINYINT, default=0)
    auto_record = Column(TINYINT, default=0)
    participant_join_sound = Column(TINYINT, default=0)
    screen_share_status = Column(TINYINT, default=1)
    virtual_background = Column(TINYINT, default=1)
    host_audio = Column(TINYINT, default=1)
    host_video = Column(TINYINT, default=1)
    participant_audio = Column(TINYINT, default=1)
    participant_video = Column(TINYINT, default=1)
    melody = Column(Integer)
    meeting_header_image = Column(String(500)) 
    friend_request = Column(String(5), default=100)
    nuggets = Column(String(5), default=100)
    events = Column(String(5), default=100)
    language_id = Column(
        Integer,
        ForeignKey("language.id"),
        comment="language table reference",
        default=1,
    )
    time_zone = Column(String(25), default="Canada/Eastern (-04:00)")
    date_format = Column(String(25), default=" MM/DD/YYYY ")
    mobile_default_page = Column(TINYINT, default=1)
    default_event_type = Column(TINYINT, default=1)
    manual_acc_active_inactive = Column(TINYINT, default=1)
    # New Column
    lock_nugget = Column(TINYINT, comment="1-Yes,0-No", default=0)
    lock_fans = Column(TINYINT, comment="1-Yes,0-No", default=0)
    lock_my_connection = Column(TINYINT, comment="1-Yes,0-No", default=0)
    lock_my_influencer = Column(TINYINT, comment="1-Yes,0-No", default=0)
    live_event_banner = Column(String(500))
    talkshow_event_banner = Column(String(500))
    read_out_language_id = Column(Integer, ForeignKey("read_out_language.id"))

    status = Column(TINYINT, default=1)

    user = relationship("User", back_populates="user_settings")
    language = relationship("Language", back_populates="user_settings")
    read_out_language = relationship("ReadOutLanguage", back_populates="user_settings")

from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class UserSettings(Base):
    __tablename__="user_settings"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"))
    online_status=Column(TINYINT)
    phone_display_status=Column(TINYINT)
    location_display_status=Column(TINYINT)
    dob_display_status=Column(TINYINT)
    bio_display_status=Column(TINYINT)
    passcode_status=Column(TINYINT)
    passcode=Column(String(15))
    public_nugget_display=Column(TINYINT)
    public_event_display=Column(TINYINT)
    waiting_room=Column(TINYINT)
    schmoozing_status=Column(TINYINT)
    breakout_status=Column(TINYINT)
    join_before_host=Column(TINYINT)
    auto_record=Column(TINYINT)
    participant_join_sound=Column(TINYINT)
    screen_share_status=Column(TINYINT)
    virtual_background=Column(TINYINT)
    host_audio=Column(TINYINT)
    host_video=Column(TINYINT)
    participant_audio=Column(TINYINT)
    participant_video=Column(TINYINT)
    melody=Column(Integer)
    meeting_header_image=Column(String(500))
    friend_request=Column(String(5))
    nuggets=Column(String(5))
    events=Column(String(5))
    language_id=Column(Integer)
    time_zone=Column(String(25))
    date_format=Column(String(25))
    mobile_default_page=Column(TINYINT)
    default_event_type=Column(TINYINT)
    manual_acc_active_inactive=Column(TINYINT)
    status=Column(TINYINT,default=1)
   
    user=relationship("User",back_populates="user_settings")   
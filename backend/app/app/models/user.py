from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    Date,
    Text,
    DECIMAL,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT, TINYTEXT
from app.db.base_class import Base


class User(Base):
    id = Column(Integer, primary_key=True)
    user_ref_id = Column(String(25))
    email_id = Column(String(100))
    is_email_id_verified = Column(TINYINT(1), comment=" 0->No, 1->Yes ")
    password = Column(String(250))
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(100))
    gender = Column(TINYINT(1), comment=" 0->Transgender, 1->Male, 2->Female ")
    other_gender=Column(String(100))
    dob = Column(Date)
    country_code = Column(String(10))
    mobile_no = Column(BigInteger)
    is_mobile_no_verified = Column(TINYINT(4), comment=" 0->No, 1->Yes")
    country_id = Column(
        Integer, ForeignKey("country.id"), comment="country table reference"
    )
    user_code = Column(
        String(25), comment=" A unique code for users sharing purpose like refrrer "
    )
    signup_type = Column(TINYINT(1), comment=" 1->Web, 2->Facebook, 3->Google ")
    signup_social_ref_id = Column(
        String(100), comment=" reference id from facebook or google "
    )
    profile_img = Column(String(500))
    cover_image = Column(String(500))
    website = Column(String(100))
    geo_location = Column(TINYTEXT, default=1, comment=" from google geo location ")
    latitude = Column(DECIMAL(11, 7))
    longitude = Column(DECIMAL(11, 7))
    user_type_id = Column(
        Integer,
        ForeignKey("user_type_master.id"),
        nullable=False,
        default=1,
        comment=" ref user_type_master ",
    )
    user_status_id = Column(
        Integer,
        ForeignKey("user_status_master.id"),
        nullable=False,
        default=1,
        comment=" ref table user_status_master ",
    )
    bio_data = Column(Text)
    created_at = Column(DateTime)
    created_by = Column(Integer)
    online = Column(TINYINT(1), nullable=False, default=0)
    web_online = Column(TINYINT(1), nullable=False, default=0)
    app_online = Column(TINYINT(1), nullable=False, default=0)
    last_seen = Column(DateTime)
    admin_verified_status = Column(
        TINYINT(1), default=1, nullable=False, comment=" 1-approved 0-pending "
    )
    referrer_id = Column(Integer)
    invited_date = Column(DateTime)
    referral_expiry_date = Column(DateTime)
    total_referral_point = Column(Integer, nullable=False, default=0)
    unused_referral_points = Column(Integer, nullable=False, default=0)
    influencer_category = Column(String(20))
    existing_user = Column(TINYINT, default=1)
    chime_user_id = Column(String(100))
    # Newly Added
    work_at = Column(String(100))
    studied_at = Column(String(100))

    status = Column(
        TINYINT(1),
        comment=" 0->verification pending, 1->Active, 2->Suspended, 3->Blocked, 4->Deleted ",
    )

    api_tokens = relationship("ApiTokens", back_populates="user")
    aws_bounce_emails = relationship("AwsBounceEmails", back_populates="user")
    events = relationship("Events", back_populates="user")
    friend_groups = relationship("FriendGroups", back_populates="user")
    event_melody = relationship("EventMelody", back_populates="user")
    event_update_log = relationship("EventUpdateLog", back_populates="user")
    friend_group_members = relationship("FriendGroupMembers", back_populates="user")
    group_chat = relationship("GroupChat", back_populates="user")
    group_report = relationship("GroupReport", back_populates="user")
    login_failure_log = relationship("LoginFailureLog", back_populates="user")
    nuggets = relationship("Nuggets", back_populates="user")
    nuggets_master = relationship("NuggetsMaster", back_populates="user")
    nugget_hash_tags = relationship("NuggetHashTags", back_populates="user")
    nugget_poll_voted = relationship("NuggetPollVoted", back_populates="user")
    nugget_report = relationship("NuggetReport", back_populates="user")
    nugget_view = relationship("NuggetView", back_populates="user")
    online_payment_details = relationship("OnlinePaymentDetails", back_populates="user")
    otp_log = relationship("OtpLog", back_populates="user")
    raw_caster_invites = relationship("RawCasterInvites", back_populates="user")
    signup_log = relationship("SignupLog", back_populates="user")
    user_login_log = relationship("UserLoginLog", back_populates="user")
    user_profile_display_group = relationship(
        "UserProfileDisplayGroup", back_populates="user"
    )
    user_settings = relationship("UserSettings", back_populates="user")
    nuggets_attachment = relationship("NuggetsAttachment", back_populates="user")
    nuggets_comments = relationship("NuggetsComments", back_populates="user")
    nuggets_comments_likes = relationship("NuggetsCommentsLikes", back_populates="user")
    nuggets_likes = relationship("NuggetsLikes", back_populates="user")
    notification_sms_email = relationship("NotificationSmsEmail", back_populates="user")
    user_status_master = relationship("UserStatusMaster", back_populates="user")
    user_type_master = relationship("UserTypeMaster", back_populates="user")
    country = relationship("Country", back_populates="user")
    event_abuse_report = relationship("EventAbuseReport", back_populates="user")
    verify_accounts = relationship("VerifyAccounts", back_populates="user")
    qr_tokens = relationship("QrTokens", back_populates="user")



# ALTER TABLE `user` ADD `verification_token` VARCHAR(255) NULL COMMENT 'id verify token' AFTER `chime_user_id`; 
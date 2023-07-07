from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT, LONGTEXT
from app.db.base_class import Base


class AwsBounceEmails(Base):
    __tablename__ = "aws_bounce_emails"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), comment=" user table ref id ")
    notification_type = Column(String(50))
    bounce_type = Column(String(50))
    email_id = Column(String(100))
    bounce_count = Column(Integer, nullable=False, default=1)
    bounce_datetime = Column(DateTime, nullable=False, default=None)
    status = Column(
        TINYINT,
        nullable=False,
        default=1,
        comment=" -1->Deleted, 0->inactive, 1->active ",
    )

    user = relationship("User", back_populates="aws_bounce_emails")

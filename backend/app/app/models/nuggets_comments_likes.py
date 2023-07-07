from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    DECIMAL,
    BigInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class NuggetsCommentsLikes(Base):
    __tablename__ = "nuggets_comments_likes"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), comment=" User table id ")
    comment_id = Column(
        Integer,
        ForeignKey("nuggets_comments.id"),
        comment=" nuggets_comments table id ",
    )
    nugget_id = Column(Integer, ForeignKey("nuggets.id"), comment=" nuggets table id ")
    created_date = Column(DateTime)
    status = Column(TINYINT, default=1)

    user = relationship("User", back_populates="nuggets_comments_likes")
    nuggets_comments = relationship(
        "NuggetsComments", back_populates="nuggets_comments_likes"
    )
    nuggets = relationship("Nuggets", back_populates="nuggets_comments_likes")

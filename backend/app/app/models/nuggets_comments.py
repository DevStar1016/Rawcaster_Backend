from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class NuggetsComments(Base):
    __tablename__ = "nuggets_comments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), comment=" User table id ")
    nugget_id = Column(Integer, ForeignKey("nuggets.id"), comment=" Nuggets table id ")
    parent_id = Column(Integer, ForeignKey("nuggets_comments.id"))
    content = Column(Text)
    created_date = Column(DateTime)
    modified_date = Column(DateTime)
    status = Column(TINYINT, default=1)

    user = relationship("User", back_populates="nuggets_comments")
    nuggets = relationship("Nuggets", back_populates="nuggets_comments")
    nuggets_comments_likes = relationship(
        "NuggetsCommentsLikes", back_populates="nuggets_comments"
    )

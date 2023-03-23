from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class Nuggets(Base):
    id=Column(Integer,primary_key=True)
    nuggets_id=Column(Integer,ForeignKey("nuggets_master.id"),comment=" nuggets_master table ID ")
    user_id=Column(Integer,ForeignKey("user.id"),comment=" nuggets_master table ID ")
    type=Column(TINYINT,comment=" 1->Original,2->Shared ")
    share_type=Column(TINYINT,comment=" 1->Public, 2->Only me, 3->Groups, 4->Individual, 5->both Group and Individual, 6->All My Friends ")
    created_date=Column(DateTime)
    modified_date=Column(DateTime)
    total_view_count=Column(Integer,default=0)
    warning_mail_count=Column(Integer,default=0)
    warning_mail_status=Column(TINYINT,default=0)
    warning_mail_sent_date=Column(DateTime)
    nugget_status=Column(TINYINT,default=1,comment=" 1->Active,2->deleted,3->blocked ")
    status=Column(TINYINT,default=1)
    
    user=relationship("User",back_populates="nuggets")
    nuggets_master=relationship("NuggetsMaster",back_populates="nuggets")
    nuggets_share_with=relationship("nuggets_share_with",back_populates="nuggets")
    nugget_hash_tags=relationship("NuggetHashTags",back_populates="nuggets")
    nugget_poll_voted=relationship("NuggetPollVoted",back_populates="nuggets")
    nugget_report=relationship("NuggetReport",back_populates="nuggets")
    nugget_view=relationship("NuggetView",back_populates="nuggets")
    nuggets_comments=relationship("NuggetsComments",back_populates="nuggets")
    nuggets_comments_likes=relationship("NuggetsCommentsLikes",back_populates="nuggets")
    nuggets_likes=relationship("NuggetsLikes",back_populates="nuggets")
    
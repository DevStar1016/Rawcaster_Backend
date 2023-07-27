from fastapi import APIRouter, Depends, Form, File, UploadFile, BackgroundTasks
from app.models import *
from app.core import config
from app.core.security import *
from typing import List
from app.utils import *
from app.api import deps
import datetime
from sqlalchemy.orm import Session,aliased
from datetime import datetime, date
from sqlalchemy import func, case, text, Date, extract,distinct,true
import re
import base64
import json
import pytz
import boto3
from urllib.parse import urlparse
from .webservices_2 import croninfluencemember
import ast
from mail_templates.mail_template import *
from moviepy.video.io.VideoFileClip import VideoFileClip
import subprocess
from .chime_chat import *
from better_profanity import profanity

router = APIRouter()


# @router.post("/searchrawcasterusers")
# async def searchrawcasterusers(
#     db: Session = Depends(deps.get_db),
#     token: str = Form(None),
#     auth_code: str = Form(None, description="SALT + token"),
#     search_key: str = Form(None),
#     page_number: str = Form(default=1),
# ):
#     if token == None or token.strip() == "":
#         return {
#             "status": -1,
#             "msg": "Sorry! your login session expired. please login again.",
#         }
#     elif auth_code == None or auth_code.strip() == "":
#         return {"status": -1, "msg": "Auth Code is missing"}
#     elif not str(page_number).isnumeric():
#         return {"status": 0, "msg": "Invalid page Number"}

#     else:
#         access_token = checkToken(db, token.strip())
#         auth_text = token.strip()
#         if checkAuthCode(auth_code.strip(), auth_text) == False:
#             return {"status": 0, "msg": "Authentication failed!"}
#         else:
#             if access_token == False:
#                 return {
#                     "status": -1,
#                     "msg": "Sorry! your login session expired. please login again.",
#                 }
#             else:
#                 login_user_email = ""
#                 get_token_details = (
#                     db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
#                 )

#                 login_user_id = get_token_details.user_id if get_token_details else None
#                 login_user_email = (
#                     get_token_details.user.email_id if get_token_details else None
#                 )

#                 current_page_no = int(page_number)
                
#                 get_user = db.query(
#                     User.id,
#                     User.email_id,
#                     User.user_ref_id,
#                     User.first_name,
#                     User.last_name,
#                     User.display_name,
#                     User.gender,
#                     User.profile_img,
#                     User.geo_location,
#                     User.bio_data,
#                     MyFriends.request_status.label('friend_request_status'),
#                     FollowUser.id.label('follow_id')
#                 ).select_from(User).outerjoin(MyFriends, 
#                     ((MyFriends.sender_id == User.id) | (MyFriends.receiver_id == User.id))
#                     & (MyFriends.status == 1)
#                     & ((MyFriends.sender_id == login_user_id) | (MyFriends.receiver_id == login_user_id))
#                 ).outerjoin(FollowUser,
#                     (FollowUser.following_userid == User.id)
#                     & (FollowUser.follower_userid == login_user_id)
#                 ).filter(User.status == 1, User.id != login_user_id)
                
#                 # Omit blocked users --
#                 request_status = 3
#                 response_type = 1
#                 requested_by = None
#                 get_all_blocked_users = get_friend_requests(
#                     db, login_user_id, requested_by, request_status, response_type
#                 )
#                 blocked_users = get_all_blocked_users["blocked"]

#                 if blocked_users:
#                     get_user = get_user.filter(User.id.not_in(blocked_users))

#                 if search_key:
#                     get_user = get_user.filter(
#                         or_(
#                             User.email_id.ilike(search_key + "%"),
#                             User.mobile_no.ilike(search_key + "%"),
#                             User.display_name.ilike("%" + search_key + "%"),
#                             User.first_name.ilike("%" + search_key + "%"),
#                             User.last_name.ilike("%" + search_key + "%"),
#                         )
#                     )

#                 get_row_count = get_user.count()

#                 if get_row_count < 1:
#                     if login_user_email == search_key:
#                         return {"status": 0, "msg": "No Result found", "invite_flag": 0}
#                     else:
#                         return {"status": 0, "msg": "No Result found", "invite_flag": 1}
#                 else:
#                     default_page_size = 25
#                     limit, offset, total_pages = get_pagination(
#                         get_row_count, current_page_no, default_page_size
#                     )
#                     # Apply Pagination
#                     get_user = (
#                         get_user.order_by(User.first_name.asc())
#                         .limit(limit)
#                         .offset(offset)
#                         .all()
#                     )

#                     user_list = []
                    
#                     for user in get_user:

#                         get_follow_user_details = db.query(FollowUser).filter(
#                             FollowUser.following_userid == user.id
#                         )

#                         get_follow_user = get_follow_user_details.filter(
#                             FollowUser.follower_userid == login_user_id
#                         ).first()

#                         follow_count = get_follow_user_details.count()

#                         mutual_friends = MutualFriends(db, login_user_id, user.id)

#                         user_list.append(
#                             {
#                                 "user_id": user.id,
#                                 "user_ref_id": user.user_ref_id,
#                                 "email_id": user.email_id if user.email_id else "",
#                                 "first_name": user.first_name
#                                 if user.first_name
#                                 else "",
#                                 "last_name": user.last_name if user.last_name else "",
#                                 "display_name": user.display_name
#                                 if user.display_name
#                                 else "",
#                                 "gender": user.gender if user.gender else "",
#                                 "profile_img": user.profile_img
#                                 if user.profile_img
#                                 else "",
#                                 "friend_request_status": user.friend_request_status
#                                 if user.friend_request_status
#                                 else "",
#                                 "follow": True if get_follow_user else False,
#                                 "follow_count": follow_count,
#                                 "location": user.geo_location
#                                 if user.geo_location
#                                 else "",
#                                 "mutual_friends": mutual_friends,
#                                 "bio_data": ProfilePreference(
#                                     db,
#                                     login_user_id,
#                                     user.id,
#                                     "bio_display_status",
#                                     user.bio_data,
#                                 ),
#                             }
#                         )
#                     return {
#                         "status": 1,
#                         "msg": "Success",
#                         "total_pages": total_pages,
#                         "current_page_no": current_page_no,
#                         "users_list": user_list,
#                     }

                    
           
# 26. List Nuggets   OLD-API
@router.post("/listnuggets")  
async def listnuggets(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    my_nuggets: str = Form(None),
    filter_type: str = Form(None, description="1-Influencer"),
    category: str = Form(None, description="Influencer category"),
    user_id: str = Form(None),
    saved: str = Form(None),
    search_key: str = Form(None),
    page_number: str = Form(default=1),
    nugget_type: str = Form(None, description="1-video,2-Other than video,0-all"),
):
    
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif nugget_type and not nugget_type.isnumeric():
        return {"status": 0, "msg": "Invalid Nugget Type"}

    elif nugget_type and not 0 <= int(nugget_type) <= 2:
        return {"status": 0, "msg": "Invalid Nugget Type"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        nugget_type = int(nugget_type) if nugget_type else None
        filter_type = int(filter_type) if filter_type else None
        saved = int(saved) if saved else None

        access_token = checkToken(db, token) if token != "RAWCAST" else True
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )

            user_public_nugget_display_setting = 1
            login_user_id = 0
            if get_token_details:
                login_user_id = get_token_details.user_id

                get_user_settings = (
                    db.query(UserSettings)
                    .filter(UserSettings.user_id == login_user_id)
                    .first()
                )
                if get_user_settings:
                    user_public_nugget_display_setting = (
                        get_user_settings.public_nugget_display
                    )

            current_page_no = int(page_number)
            user_id = int(user_id) if user_id else None

            group_ids = getGroupids(db, login_user_id)
            requested_by = None
            request_status = 1  # Pending
            response_type = 1
            my_frnds = get_friend_requests(
                db, login_user_id, requested_by, request_status, response_type
            )
            my_friends = my_frnds["accepted"]

            my_followings = getFollowings(db, login_user_id)
            type = None
            raw_id = GetRawcasterUserID(db, type)

            get_nuggets = (
                db.query(Nuggets)
                .select_from(Nuggets)
                .join(User, Nuggets.user_id == User.id, isouter=True)
                .join(
                    NuggetsMaster, Nuggets.nuggets_id == NuggetsMaster.id, isouter=True
                )
                .join(
                    NuggetPollVoted,
                    NuggetPollVoted.nugget_id == Nuggets.id,
                    isouter=True,
                )
                .join(
                    NuggetsLikes,
                    (Nuggets.id == NuggetsLikes.nugget_id) & (NuggetsLikes.status == 1),
                    isouter=True,
                )
                .join(
                    NuggetsComments,
                    (Nuggets.id == NuggetsComments.nugget_id)
                    & (NuggetsComments.status == 1),
                    isouter=True,
                )
                .join(
                    NuggetsShareWith,
                    Nuggets.id == NuggetsShareWith.nuggets_id,
                    isouter=True,
                )
                .join(NuggetView, Nuggets.id == NuggetView.nugget_id, isouter=True)
                .join(NuggetsSave, Nuggets.id == NuggetsSave.nugget_id, isouter=True)
                .filter(Nuggets.status == 1)
                .filter(Nuggets.nugget_status == 1)
                .filter(NuggetsMaster.status == 1)
                .group_by(Nuggets.id)
            )

            if search_key:
                get_nuggets = get_nuggets.filter(
                    or_(
                        NuggetsMaster.content.ilike("%" + search_key + "%"),
                        User.display_name.ilike("%" + search_key + "%"),
                        User.first_name.ilike("%" + search_key + "%"),
                        User.last_name.ilike("%" + search_key + "%"),
                    )
                )

            if access_token == "RAWCAST":  # When Customer not login
                get_nuggets = get_nuggets.filter(Nuggets.share_type == 1)

                if nugget_type == 1:  # Video Nugget
                    get_nuggets = get_nuggets.join(
                        NuggetsAttachment,
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                        isouter=True,
                    ).filter(NuggetsAttachment.media_type == "video")

                elif nugget_type == 2:  # Other type
                    get_nuggets = get_nuggets.join(
                        NuggetsAttachment,
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                        isouter=True,
                    ).filter(
                        or_(
                            NuggetsAttachment.media_type == None,
                            NuggetsAttachment.media_type == "image",
                            NuggetsAttachment.media_type == "audio",
                        )
                    )

            elif my_nuggets == 1:
                get_nuggets = get_nuggets.filter(Nuggets.user_id == login_user_id)

            elif saved == 1:
                get_nuggets = get_nuggets.filter(NuggetsSave.user_id == login_user_id)

            elif user_id:
                get_nuggets = get_nuggets.filter(Nuggets.user_id == user_id)

                if login_user_id != user_id:
                    get_nuggets = get_nuggets.filter(
                        Nuggets.user_id == user_id, Nuggets.share_type == 1
                    )

            else:
                if nugget_type == 1:  # Video
                    get_nuggets = get_nuggets.filter(
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                        NuggetsAttachment.media_type == "video",
                    )

                if nugget_type == 2:  # Audio and Image
                    get_nuggets = get_nuggets.outerjoin(
                        NuggetsAttachment,
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                    ).filter(
                        or_(
                            NuggetsAttachment.media_type == None,
                            NuggetsAttachment.media_type == "image",
                            NuggetsAttachment.media_type == "audio",
                        )
                    )

                if filter_type == 1:  # Influencer
                    my_followers = []  # my_followers
                    follow_user = (
                        db.query(FollowUser.following_userid)
                        .filter(FollowUser.follower_userid == login_user_id)
                        .all()
                    )

                    if follow_user:
                        for group_list in follow_user:
                            my_followers.append(group_list.following_userid)

                    get_nuggets = get_nuggets.filter(
                        or_(
                            and_(Nuggets.user_id == login_user_id),
                            and_(Nuggets.user_id.in_(my_followers)),
                            Nuggets.share_type != 2,
                        )
                    )

                elif user_public_nugget_display_setting == 0:  # Rawcaster
                    get_nuggets = get_nuggets.filter(
                        or_(Nuggets.user_id == login_user_id, Nuggets.user_id == raw_id)
                    )

                elif user_public_nugget_display_setting == 1:  # Public
                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(Nuggets.share_type == 1),
                            and_(
                                Nuggets.share_type == 2,
                                Nuggets.user_id == login_user_id,
                            ),
                            and_(
                                Nuggets.share_type == 3,
                                NuggetsShareWith.type == 1,
                                NuggetsShareWith.share_with.in_(group_ids),
                            ),
                            and_(
                                Nuggets.share_type == 4,
                                NuggetsShareWith.type == 2,
                                NuggetsShareWith.share_with.in_([login_user_id]),
                            ),
                            and_(
                                Nuggets.share_type == 6, Nuggets.user_id.in_(my_friends)
                            ),
                            and_(
                                Nuggets.share_type == 7,
                                Nuggets.user_id.in_(my_followings),
                            ),
                            and_(Nuggets.user_id == raw_id),
                        )
                    )

                elif user_public_nugget_display_setting == 2:  # All Connections
                    get_nuggets = get_nuggets.filter(
                        or_(
                            and_(Nuggets.user_id == login_user_id),
                            and_(
                                Nuggets.user_id.in_(my_friends), Nuggets.share_type != 2
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 3:  # Specific Connections
                    my_friends = []  # Selected Connections id's

                    online_group_list = (
                        db.query(UserProfileDisplayGroup)
                        .filter(
                            UserProfileDisplayGroup.user_id == login_user_id,
                            UserProfileDisplayGroup.profile_id
                            == "public_nugget_display",
                        )
                        .all()
                    )

                    if online_group_list:
                        for group_list in online_group_list:
                            my_friends.append(group_list.groupid)
                    get_nuggets = get_nuggets.filter(
                        or_(
                            and_(Nuggets.user_id == login_user_id),
                            and_(
                                Nuggets.user_id.in_(my_friends), Nuggets.share_type != 2
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 4:  # All Groups
                    get_nuggets = get_nuggets.join(
                        FriendGroupMembers,
                        Nuggets.user_id == FriendGroupMembers.user_id,
                        isouter=True,
                    )
                    get_nuggets = get_nuggets.join(
                        FriendGroups, FriendGroupMembers.group_id == FriendGroups.id,isouter=True
                    ).filter(FriendGroups.status == 1)
                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(
                                FriendGroups.created_by == login_user_id,
                                Nuggets.share_type != 2,
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 5:  # Specific Groups
                    my_friends = []
                    online_group_list = (
                        db.query(UserProfileDisplayGroup)
                        .filter(
                            UserProfileDisplayGroup.user_id == login_user_id,
                            UserProfileDisplayGroup.profile_id
                            == "public_nugget_display",
                        )
                        .all()
                    )
                    if online_group_list:
                        for group_list in online_group_list:
                            my_friends.append(group_list.groupid)

                    get_nuggets = get_nuggets.join(
                        FriendGroupMembers,
                        Nuggets.user_id == FriendGroupMembers.user_id,
                    )
                    get_nuggets = get_nuggets.join(
                        FriendGroups, FriendGroupMembers.group_id == FriendGroups.id
                    ).filter(FriendGroups.status == 1)

                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(
                                FriendGroups.id.in_(my_friends), Nuggets.share_type != 2
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 6:  # My influencers
                    my_followers = []  # Selected Connections id's
                    follow_user = (
                        db.query(FollowUser)
                        .filter(FollowUser.follower_userid == login_user_id)
                        .all()
                    )
                    if follow_user:
                        for group_list in follow_user:
                            my_followers.append(group_list.following_userid)

                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(Nuggets.user_id.in_(my_followers)),
                            Nuggets.share_type != 2,
                        )
                    )

                else:  #  Mine only
                    get_nuggets = get_nuggets.filter(
                        or_(Nuggets.user_id == login_user_id)
                    )

                if category:  # Influencer Category
                    
                    get_nuggets = get_nuggets.filter(
                        User.influencer_category.like("%" + category + "%"),
                    )

            # Omit blocked users nuggets
            requested_by = None
            request_status = 3  # Rejected
            response_type = 1

            get_all_blocked_users = get_friend_requests(
                db, login_user_id, requested_by, request_status, response_type
            )

            blocked_users = get_all_blocked_users["blocked"]

            if blocked_users:
                get_nuggets = get_nuggets.filter(Nuggets.user_id.not_in(blocked_users))

            get_nuggets = get_nuggets.order_by(Nuggets.created_date.desc())

            get_nuggets_count = get_nuggets.count()

            if get_nuggets_count < 1:
                return {"status": 0, "msg": "No Result found"}
            else:
                default_page_size = 20
                limit, offset, total_pages = get_pagination(
                    get_nuggets_count, current_page_no, default_page_size
                )

                get_nuggets = get_nuggets.limit(limit).offset(offset).all()
                nuggets_list = []

                for nuggets in get_nuggets:
                    attachments = []
                    poll_options = []
                    is_downloadable = 0
                    tot_likes = (
                        db.query(NuggetsLikes)
                        .filter(
                            NuggetsLikes.nugget_id == nuggets.id,
                            NuggetsLikes.status == 1,
                        )
                        .count()
                    )

                    total_comments = (
                        db.query(NuggetsComments)
                        .filter(NuggetsComments.nugget_id == nuggets.id)
                        .count()
                    )

                    total_views = (
                        db.query(NuggetView)
                        .filter(NuggetView.nugget_id == nuggets.id)
                        .count()
                    )

                    total_vote = (
                        db.query(NuggetPollVoted)
                        .filter(NuggetPollVoted.nugget_id == nuggets.id)
                        .count()
                    )

                    img_count = 0
                    shared_detail = []
                    get_nugget_share = (
                        db.query(NuggetsShareWith)
                        .filter(NuggetsShareWith.nuggets_id == nuggets.id)
                        .all()
                    )

                    if login_user_id == nuggets.user_id and get_nugget_share:
                        shared_group_ids = []
                        type = 0
                        for share_nugget in get_nugget_share:
                            type = share_nugget.type
                            shared_group_ids.append(share_nugget.share_with)

                        if type == 1:
                            friend_groups = (
                                db.query(FriendGroups)
                                .filter(FriendGroups.id.in_(shared_group_ids))
                                .all()
                            )
                            for friend_group in friend_groups:
                                shared_detail.append(
                                    {
                                        "id": friend_group.id,
                                        "name": friend_group.group_name,
                                        "img": friend_group.group_icon,
                                    }
                                )
                        elif type == 2:
                            friend_groups = (
                                db.query(User)
                                .filter(User.id.in_(shared_group_ids))
                                .all()
                            )
                            for friend_group in friend_groups:
                                shared_detail.append(
                                    {
                                        "id": friend_group.id,
                                        "name": friend_group.display_name,
                                        "img": friend_group.profile_img,
                                    }
                                )

                    get_nugget_attachment = db.query(NuggetsAttachment).filter(
                        NuggetsAttachment.nugget_id == nuggets.nuggets_id,
                        NuggetsAttachment.status == 1,
                    )
                    if nugget_type == 1:
                        get_nugget_attachment = get_nugget_attachment.filter(
                            NuggetsAttachment.media_type == "video"
                        )

                    for attach in get_nugget_attachment:
                        if attach.status == 1:
                            attachments.append(
                                {
                                    "media_id": attach.id,
                                    "media_type": attach.media_type,
                                    "media_file_type": attach.media_file_type,
                                    "path": attach.path,
                                }
                            )

                    get_nugget_poll_option = (
                        db.query(NuggetPollOption)
                        .filter(
                            NuggetPollOption.nuggets_master_id == nuggets.nuggets_id,
                            NuggetPollOption.status == 1,
                        )
                        .all()
                    )

                    for option in get_nugget_poll_option:
                        if option.status == 1:
                            poll_options.append(
                                {
                                    "option_id": option.id,
                                    "option_name": option.option_name,
                                    "option_percentage": option.poll_vote_percentage,
                                    "votes": option.votes,
                                }
                            )

                    following = (
                        db.query(FollowUser)
                        .filter(
                            FollowUser.follower_userid == login_user_id,
                            FollowUser.following_userid == nuggets.user_id,
                        )
                        .count()
                    )
                    follow_count = (
                        db.query(FollowUser)
                        .filter(FollowUser.following_userid == nuggets.user_id)
                        .count()
                    )

                    nugget_like = False

                    checklike = (
                        db.query(NuggetsLikes)
                        .filter(
                            NuggetsLikes.nugget_id == nuggets.id,
                            NuggetsLikes.user_id == login_user_id,
                        )
                        .first()
                    )

                    if checklike:
                        nugget_like = True

                    if login_user_id == nuggets.user_id:
                        following = 1

                    voted = (
                        db.query(NuggetPollVoted)
                        .filter(
                            NuggetPollVoted.nugget_id == nuggets.id,
                            NuggetPollVoted.user_id == login_user_id,
                        )
                        .first()
                    )
                    saved = (
                        db.query(NuggetsSave)
                        .filter(
                            NuggetsSave.nugget_id == nuggets.id,
                            NuggetsSave.user_id == login_user_id,
                            NuggetsSave.status == 1,
                        )
                        .count()
                    )

                    if nuggets.share_type == 1:
                        if following == 1:
                            is_downloadable = 1
                        else:
                            user_id = nuggets.user_id
                            get_friend_request = db.query(MyFriends).filter(
                                MyFriends.status == 1, MyFriends.request_status == 1
                            )

                            get_friend_request = (
                                get_friend_request.filter(
                                    or_(
                                        and_(
                                            MyFriends.sender_id == login_user_id,
                                            MyFriends.receiver_id == user_id,
                                        ),
                                        and_(
                                            MyFriends.sender_id == user_id,
                                            MyFriends.receiver_id == login_user_id,
                                        ),
                                    )
                                )
                                .order_by(MyFriends.id.desc())
                                .first()
                            )

                            if get_friend_request:
                                is_downloadable = 1
                    else:
                        is_downloadable = 1

                    # Check account Verification
                    check_verify = (
                        db.query(VerifyAccounts)
                        .filter(
                            VerifyAccounts.user_id == nuggets.user_id,
                            VerifyAccounts.verify_status == 1,
                        )
                        .first()
                    )

                    nuggets_list.append(
                        {
                            "nugget_id": nuggets.id,
                            "content": nuggets.nuggets_master.content,
                            "metadata": nuggets.nuggets_master._metadata,
                            "created_date": common_date(nuggets.created_date)
                            if nuggets.created_date
                            else "",
                            "user_id": nuggets.user_id,
                            "user_ref_id": nuggets.user.user_ref_id
                            if nuggets.user_id
                            else "",
                            "account_verify_type": 1 if check_verify else 0,
                            "type": nuggets.type,
                            "original_user_id": nuggets.nuggets_master.user.id
                            if nuggets.user_id
                            else "",
                            "original_user_name": nuggets.nuggets_master.user.display_name
                            if nuggets.user_id
                            else "",
                            "original_user_image": nuggets.nuggets_master.user.profile_img
                            if nuggets.user_id
                            else "",
                            "user_name": nuggets.user.display_name
                            if nuggets.user_id
                            else "",
                            "user_image": nuggets.user.profile_img
                            if nuggets.user_id
                            else "",
                            "user_status_id": nuggets.user.user_status_id
                            if nuggets.user_id
                            else "",
                            "liked": nugget_like,
                            "viewed": 0,
                            "following": True if following > 0 else False,
                            "follow_count": follow_count,
                            "total_likes": tot_likes,
                            "total_comments": total_comments,
                            "total_views": total_views,
                            "total_media": img_count,
                            "share_type": nuggets.share_type,
                            "media_list": attachments,
                            "is_nugget_owner": 1
                            if nuggets.user_id == login_user_id
                            else 0,
                            "is_master_nugget_owner": 1
                            if nuggets.nuggets_master.user_id == login_user_id
                            else 0,
                            "shared_detail": shared_detail,
                            "shared_with": [],
                            "is_downloadable": is_downloadable,
                            "poll_option": poll_options,
                            "poll_duration": nuggets.nuggets_master.poll_duration,
                            "voted": 1 if voted else 0,
                            "voted_option": voted.poll_option_id if voted else None,
                            "total_vote": total_vote,
                            "saved": True if saved == 1 else False,
                        }
                    )

                return {
                    "status": 1,
                    "msg": "Success",
                    "nuggets_count": get_nuggets_count,
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "nuggets_list": nuggets_list,
                }

 
 
 
 
# @router.post("/show_buffer")
# async def buffer():
#     import mysql.connector

#     # Replace 'your_username', 'your_password', 'your_host', and 'your_database' with your actual MySQL credentials
#     connection = mysql.connector.connect(
#         user='maemysqluser',
#         password='MaeNewMysql2@2@',
#         host='192.168.1.109',
#         database='rawcaster'
#     )

#     cursor = connection.cursor()

#     # new_sort_buffer_size_mb = 5
#     # new_sort_buffer_size_bytes = new_sort_buffer_size_mb * 1024 * 1024

#     # Set the new sort_buffer_size using SQL
#     # print(new_sort_buffer_size_bytes)
#     # cursor.execute(f"SET sort_buffer_size = {new_sort_buffer_size_bytes};")

#     # Commit the changes to the database
#     cursor.execute("SHOW VARIABLES LIKE 'sort_buffer_size'")
#     result = cursor.fetchone()
    
#     connection.commit()

#     if result:
#         print(f"sort_buffer_size: {result[1]}")
#     else:
#         print("sort_buffer_size not found.")

#     cursor.close()
#     connection.close()
    
    
    
    
    
@router.post("/list__nuggets")
async def list__nuggets(
    db:Session= Depends(deps.get_db),
    token: str = Form(None),
    my_nuggets: str = Form(None),
    filter_type: str = Form(None, description="1-Influencer"),
    category: str = Form(None, description="Influencer category"),
    user_id: str = Form(None),
    saved: str = Form(None),
    search_key: str = Form(None),
    page_number: str = Form(default=1),
    nugget_type: str = Form(None, description="1-video,2-Other than video,0-all"),
    ):
    
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login db expired. please login again.",
        }
    elif nugget_type and not nugget_type.isnumeric():
        return {"status": 0, "msg": "Invalid Nuggets Type"}

    elif nugget_type and not 0 <= int(nugget_type) <= 2:
        return {"status": 0, "msg": "Invalid Nuggets Type"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        nugget_type = int(nugget_type) if nugget_type else None
        filter_type = int(filter_type) if filter_type else None
        saved = int(saved) if saved else None

        access_token = checkToken(db, token) if token != "RAWCAST" else True
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login db expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"
            get_token_details = (
                db.query(ApiTokens.user_id,UserSettings.public_nugget_display).join(User,User.id == ApiTokens.user_id).outerjoin(UserSettings,UserSettings.user_id == User.id ).filter(ApiTokens.token == access_token).first()
            )

            user_public_nugget_display_setting = 1
            login_user_id = 0
            if get_token_details:
                login_user_id = get_token_details.user_id
                user_public_nugget_display_setting=get_token_details.public_nugget_display
            
            current_page_no = int(page_number)
            user_id = int(user_id) if user_id else None
            
            group_ids=getGroupids(db,login_user_id)
            requested_by = None
            request_status = 1  # Pending
            response_type = 1
            my_frnds = get_friend_requests(db, login_user_id, requested_by, request_status, response_type)
            
            my_friends = my_frnds["accepted"]
            my_followings = getFollowings(db, login_user_id)
            
            type=None
            raw_id = GetRawcasterUserID(db, type)
            
            get_nuggets = (
                db.query(Nuggets.id,
                         Nuggets.nuggets_id,
                         Nuggets.user_id,
                         Nuggets.type,
                         Nuggets.share_type,
                         Nuggets.created_date,
                         Nuggets.nugget_status,
                         Nuggets.status,
                         NuggetsMaster.content,
                         NuggetsMaster._metadata,
                         NuggetsMaster.poll_duration,
                        #  func.count(distinct(NuggetsLikes.id)).label('tot_likes'),
                        #  func.count(distinct(NuggetView.id)).label('total_views'),
                        #  func.count(distinct(NuggetPollVoted.id)).label("total_vote"),
                        #  func.count(distinct(NuggetsSave.id)).label('is_saved'),
                        #  func.count(distinct(NuggetsComments.id)).label('total_comments')
                        )
                .join(
                    NuggetsMaster, Nuggets.nuggets_id == NuggetsMaster.id, isouter=True
                )
                # .join(
                #     NuggetPollVoted,
                #     NuggetPollVoted.nugget_id == Nuggets.id,
                #     isouter=True,
                # )
                # .join(
                #     NuggetsLikes,
                #     (Nuggets.id == NuggetsLikes.nugget_id) & (NuggetsLikes.status == 1),
                #     isouter=True,
                # )
                # .join(
                #     NuggetsComments,
                #     (Nuggets.id == NuggetsComments.nugget_id)
                #     & (NuggetsComments.status == 1),
                #     isouter=True,
                # )
                .join(
                    NuggetsShareWith,
                    Nuggets.id == NuggetsShareWith.nuggets_id,
                    isouter=True,
                )
                # .join(NuggetView, Nuggets.id == NuggetView.nugget_id, isouter=True)
                .join(NuggetsSave, Nuggets.id == NuggetsSave.nugget_id, isouter=True)
                .filter(Nuggets.status == 1)
                .filter(Nuggets.nugget_status == 1)
                .filter(NuggetsMaster.status == 1)
                .group_by(Nuggets.id)
            )    
            
            if search_key:
                get_nuggets = get_nuggets.filter(
                    or_(
                        NuggetsMaster.content.ilike("%" + search_key + "%"),
                        User.display_name.ilike("%" + search_key + "%"),
                        User.first_name.ilike("%" + search_key + "%"),
                        User.last_name.ilike("%" + search_key + "%"),
                    )
                )
            
            # Criteria for nuggets permission
            if access_token == "RAWCAST":  # When Customer not login
                get_nuggets = get_nuggets.filter(Nuggets.share_type == 1)

                if nugget_type == 1:  # Video Nugget
                    get_nuggets = get_nuggets.join(
                        NuggetsAttachment,
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                        isouter=True,
                    ).filter(NuggetsAttachment.media_type == "video")

                elif nugget_type == 2:  # Other type
                    get_nuggets = get_nuggets.join(
                        NuggetsAttachment,
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                        isouter=True,
                    ).filter(
                        or_(
                            NuggetsAttachment.media_type == None,
                            NuggetsAttachment.media_type == "image",
                            NuggetsAttachment.media_type == "audio",
                        )
                    )

            elif my_nuggets == 1:
                get_nuggets = get_nuggets.filter(Nuggets.user_id == login_user_id)

            elif saved == 1:
                get_nuggets = get_nuggets.filter(NuggetsSave.user_id == login_user_id)

            elif user_id:
                get_nuggets = get_nuggets.filter(Nuggets.user_id == user_id)

                if login_user_id != user_id:
                    get_nuggets = get_nuggets.filter(
                        Nuggets.user_id == user_id, Nuggets.share_type == 1
                    )

            else:
                if nugget_type == 1:  # Video
                    get_nuggets = get_nuggets.filter(
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                        NuggetsAttachment.media_type == "video",
                    )

                if nugget_type == 2:  # Audio and Image
                    get_nuggets = get_nuggets.outerjoin(
                        NuggetsAttachment,
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                    ).filter(
                        or_(
                            NuggetsAttachment.media_type == None,
                            NuggetsAttachment.media_type == "image",
                            NuggetsAttachment.media_type == "audio",
                        )
                    )

                if filter_type == 1:  # Influencer
                    my_followers = []  # my_followers
                    follow_user = (
                        db.query(FollowUser.following_userid)
                        .filter(FollowUser.follower_userid == login_user_id)
                        .all()
                    )

                    if follow_user:
                        for group_list in follow_user:
                            my_followers.append(group_list.following_userid)

                    get_nuggets = get_nuggets.filter(
                        or_(
                            and_(Nuggets.user_id == login_user_id),
                            and_(Nuggets.user_id.in_(my_followers)),
                            Nuggets.share_type != 2,
                        )
                    )

                elif user_public_nugget_display_setting == 0:  # Rawcaster
                    get_nuggets = get_nuggets.filter(
                        or_(Nuggets.user_id == login_user_id, Nuggets.user_id == raw_id)
                    )

                elif user_public_nugget_display_setting == 1:  # Public
                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(Nuggets.share_type == 1),
                            and_(
                                Nuggets.share_type == 2,
                                Nuggets.user_id == login_user_id,
                            ),
                            and_(
                                Nuggets.share_type == 3,
                                NuggetsShareWith.type == 1,
                                NuggetsShareWith.share_with.in_(group_ids),
                            ),
                            and_(
                                Nuggets.share_type == 4,
                                NuggetsShareWith.type == 2,
                                NuggetsShareWith.share_with.in_([login_user_id]),
                            ),
                            and_(
                                Nuggets.share_type == 6, Nuggets.user_id.in_(my_friends)
                            ),
                            and_(
                                Nuggets.share_type == 7,
                                Nuggets.user_id.in_(my_followings),
                            ),
                            and_(Nuggets.user_id == raw_id),
                        )
                    )

                elif user_public_nugget_display_setting == 2:  # All Connections
                    get_nuggets = get_nuggets.filter(
                        or_(
                            and_(Nuggets.user_id == login_user_id),
                            and_(
                                Nuggets.user_id.in_(my_friends), Nuggets.share_type != 2
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 3:  # Specific Connections
                    my_friends = []  # Selected Connections id's

                    online_group_list = (
                        db.query(UserProfileDisplayGroup)
                        .filter(
                            UserProfileDisplayGroup.user_id == login_user_id,
                            UserProfileDisplayGroup.profile_id
                            == "public_nugget_display",
                        )
                        .all()
                    )

                    if online_group_list:
                        for group_list in online_group_list:
                            my_friends.append(group_list.groupid)
                    get_nuggets = get_nuggets.filter(
                        or_(
                            and_(Nuggets.user_id == login_user_id),
                            and_(
                                Nuggets.user_id.in_(my_friends), Nuggets.share_type != 2
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 4:  # All Groups
                    get_nuggets = get_nuggets.join(
                        FriendGroupMembers,
                        Nuggets.user_id == FriendGroupMembers.user_id,
                        isouter=True,
                    )
                    get_nuggets = get_nuggets.join(
                        FriendGroups, FriendGroupMembers.group_id == FriendGroups.id,isouter=True
                    ).filter(FriendGroups.status == 1)
                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(
                                FriendGroups.created_by == login_user_id,
                                Nuggets.share_type != 2,
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 5:  # Specific Groups
                    my_friends = []
                    online_group_list = (
                        db.query(UserProfileDisplayGroup)
                        .filter(
                            UserProfileDisplayGroup.user_id == login_user_id,
                            UserProfileDisplayGroup.profile_id
                            == "public_nugget_display",
                        )
                        .all()
                    )
                    if online_group_list:
                        for group_list in online_group_list:
                            my_friends.append(group_list.groupid)

                    get_nuggets = get_nuggets.join(
                        FriendGroupMembers,
                        Nuggets.user_id == FriendGroupMembers.user_id,
                    )
                    get_nuggets = get_nuggets.join(
                        FriendGroups, FriendGroupMembers.group_id == FriendGroups.id
                    ).filter(FriendGroups.status == 1)

                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(
                                FriendGroups.id.in_(my_friends), Nuggets.share_type != 2
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 6:  # My influencers
                    my_followers = []  # Selected Connections id's
                    follow_user = (
                        db.query(FollowUser)
                        .filter(FollowUser.follower_userid == login_user_id)
                        .all()
                    )
                    if follow_user:
                        for group_list in follow_user:
                            my_followers.append(group_list.following_userid)

                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(Nuggets.user_id.in_(my_followers)),
                            Nuggets.share_type != 2,
                        )
                    )

                else:  #  Mine only
                    get_nuggets = get_nuggets.filter(
                        or_(Nuggets.user_id == login_user_id)
                    )

                if category:  # Influencer Category
                    
                    get_nuggets = get_nuggets.filter(
                        User.influencer_category.like("%" + category + "%"),
                    )

            # Omit blocked users nuggets
            requested_by = None
            request_status = 3  # Rejected
            response_type = 1

            get_all_blocked_users = get_friend_requests(
                db, login_user_id, requested_by, request_status, response_type
            )

            blocked_users = get_all_blocked_users["blocked"]

            if blocked_users:
                get_nuggets = get_nuggets.filter(Nuggets.user_id.not_in(blocked_users))

            get_nuggets = get_nuggets.order_by(Nuggets.created_date.desc())
            get_nuggets_count = get_nuggets.count()
            
            if get_nuggets_count < 1:
                return {"status": 0, "msg": "No Result found"}
            else:
                default_page_size = 20
                limit, offset, total_pages = get_pagination(
                    get_nuggets_count, current_page_no, default_page_size
                )

                get_nuggets = get_nuggets.limit(limit).offset(offset).all()
                nuggets_list = []
               
                for nuggets in get_nuggets:
                    tot_likes=db.query(NuggetsLikes).filter(NuggetsLikes.nugget_id == nuggets.id,NuggetsLikes.status == 1).count()
                    total_views=db.query(NuggetView).filter(NuggetView.nugget_id == nuggets.id).count()
                    total_vote=db.query(NuggetPollVoted).filter(NuggetView.nugget_id == nuggets.id).count()
                    is_saved=db.query(NuggetsSave).filter(NuggetsSave.nugget_id == nuggets.id).count()
                    total_comments=db.query(NuggetsComments).filter(NuggetsComments.nugget_id == nuggets.id,NuggetsComments.status == 1).count()
                    
                    attachments = []
                    poll_options = []
                    is_downloadable = 0

                    img_count = 0
                    shared_detail = []
                    get_nugget_share = (
                        db.query(NuggetsShareWith.type,NuggetsShareWith.share_with)
                        .filter(NuggetsShareWith.nuggets_id == nuggets.id)
                        .all()
                    )

                    if login_user_id == nuggets.user_id and get_nugget_share:
                        shared_group_ids = []
                        type = 0
                        for share_nugget in get_nugget_share:
                            type = share_nugget.type
                            shared_group_ids.append(share_nugget.share_with)

                        if type == 1:
                            friend_groups = (
                                db.query(FriendGroups.id,FriendGroups.group_name,FriendGroups.group_icon)
                                .filter(FriendGroups.id.in_(shared_group_ids))
                                .all()
                            )
                            for friend_group in friend_groups:
                                shared_detail.append(
                                    {
                                        "id": friend_group.id,
                                        "name": friend_group.group_name,
                                        "img": friend_group.group_icon,
                                    }
                                )
                        elif type == 2:
                            friend_groups = (
                                db.query(User.display_name,User.profile_img,User.id)
                                .filter(User.id.in_(shared_group_ids))
                                .all()
                            )
                            for friend_group in friend_groups:
                                shared_detail.append(
                                    {
                                        "id": friend_group.id,
                                        "name": friend_group.display_name,
                                        "img": friend_group.profile_img,
                                    }
                                )

                    get_nugget_attachment = db.query(NuggetsAttachment.id,NuggetsAttachment.media_type,
                        NuggetsAttachment.media_file_type,NuggetsAttachment.path,NuggetsAttachment.status).filter(
                        NuggetsAttachment.nugget_id == nuggets.nuggets_id,
                        NuggetsAttachment.status == 1,
                    )
                    if nugget_type == 1:
                        get_nugget_attachment = get_nugget_attachment.filter(
                            NuggetsAttachment.media_type == "video"
                        )

                    for attach in get_nugget_attachment:
                        if attach.status == 1:
                            attachments.append(
                                {
                                    "media_id": attach.id,
                                    "media_type": attach.media_type,
                                    "media_file_type": attach.media_file_type,
                                    "path": attach.path,
                                }
                            )

                    get_nugget_poll_option = (
                        db.query(NuggetPollOption.id,NuggetPollOption.option_name,NuggetPollOption.poll_vote_percentage,NuggetPollOption.votes,NuggetPollOption.status)
                        .filter(
                            NuggetPollOption.nuggets_master_id == nuggets.nuggets_id,
                            NuggetPollOption.status == 1,
                        )
                        .all()
                    )

                    for option in get_nugget_poll_option:
                        if option.status == 1:
                            poll_options.append(
                                {
                                    "option_id": option.id,
                                    "option_name": option.option_name,
                                    "option_percentage": option.poll_vote_percentage,
                                    "votes": option.votes,
                                }
                            )

                    following = (
                        db.query(FollowUser)
                        .filter(
                            FollowUser.follower_userid == login_user_id,
                            FollowUser.following_userid == nuggets.user_id,
                        )
                        .count()
                    )
                    follow_count = (
                        db.query(FollowUser)
                        .filter(FollowUser.following_userid == nuggets.user_id)
                        .count()
                    )

                    nugget_like = False

                    checklike = (
                        db.query(NuggetsLikes)
                        .filter(
                            NuggetsLikes.nugget_id == nuggets.id,
                            NuggetsLikes.user_id == login_user_id,
                        )
                        .first()
                    )

                    if checklike:
                        nugget_like = True

                    if login_user_id == nuggets.user_id:
                        following = 1
                    # Check Poll voted or Not
                    voted = (
                        db.query(NuggetPollVoted)
                        .filter(
                            NuggetPollVoted.nugget_id == nuggets.id,
                            NuggetPollVoted.user_id == login_user_id,
                        )
                        .first()
                    )

                    if nuggets.share_type == 1:
                        if following == 1:
                            is_downloadable = 1
                        else:
                            user_id = nuggets.user_id
                            get_friend_request = db.query(MyFriends).filter(
                                MyFriends.status == 1, MyFriends.request_status == 1
                            )

                            get_friend_request = (
                                get_friend_request.filter(
                                    or_(
                                        and_(
                                            MyFriends.sender_id == login_user_id,
                                            MyFriends.receiver_id == user_id,
                                        ),
                                        and_(
                                            MyFriends.sender_id == user_id,
                                            MyFriends.receiver_id == login_user_id,
                                        ),
                                    )
                                )
                                .order_by(MyFriends.id.desc())
                                .first()
                            )

                            if get_friend_request:
                                is_downloadable = 1
                    else:
                        is_downloadable = 1

                    # Check account Verification
                    check_verify = (
                        db.query(VerifyAccounts)
                        .filter(
                            VerifyAccounts.user_id == nuggets.user_id,
                            VerifyAccounts.verify_status == 1,
                        )
                        .first()
                    )

                    nuggets_list.append(
                        {
                            "nugget_id": nuggets.id,
                            "content": nuggets.content,
                            "metadata": nuggets._metadata,
                            "created_date": common_date(nuggets.created_date)
                            if nuggets.created_date
                            else "",
                            "user_id": nuggets.user_id,
                            "user_ref_id": nuggets.user.user_ref_id
                            if nuggets.user_id
                            else "",
                            "account_verify_type": 1 if check_verify else 0,
                            "type": nuggets.type,
                            "original_user_id": nuggets.user_id
                            if nuggets.user_id
                            else "",
                            "original_user_name": nuggets.user.display_name
                            if nuggets.user_id
                            else "",
                            "original_user_image": nuggets.user.profile_img
                            if nuggets.user_id
                            else "",
                            "user_name": nuggets.user.display_name
                            if nuggets.user_id
                            else "",
                            "user_image": nuggets.user.profile_img
                            if nuggets.user_id
                            else "",
                            "user_status_id": nuggets.user.user_status_id
                            if nuggets.user_id
                            else "",
                            "liked": nugget_like,
                            "viewed": 0,
                            "following": True if following > 0 else False,
                            "follow_count": follow_count,
                            "total_likes": tot_likes,
                            "total_comments": total_comments,
                            "total_views": total_views,
                            "total_media": img_count,
                            "share_type": nuggets.share_type,
                            "media_list": attachments,
                            "is_nugget_owner": 1
                            if nuggets.user_id == login_user_id
                            else 0,
                            "is_master_nugget_owner": 1
                            if nuggets.user_id == login_user_id
                            else 0,
                            "shared_detail": shared_detail,
                            "shared_with": [],
                            "is_downloadable": is_downloadable,
                            "poll_option": poll_options,
                            "poll_duration": nuggets.poll_duration,
                            "voted": 1 if voted else 0,
                            "voted_option": voted.poll_option_id if voted else None,
                            "total_vote": total_vote if total_vote else 0,
                            "saved": True if is_saved == 1 else False,
                        }
                    )

                return {
                    "status": 1,
                    "msg": "Success",
                    "nuggets_count": get_nuggets_count,
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "nuggets_list": nuggets_list,
                }
            
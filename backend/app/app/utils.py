from sqlalchemy import or_, and_
import math
from app.core.config import settings as st
from datetime import datetime, timedelta
import datetime
from app.models import *
import random, string
import hashlib
import re
import math
import requests
import string
from dateutil.relativedelta import relativedelta
from jose import jwt
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import base64
from PIL import Image
import os, boto3
import sys
import time
from mail_templates.mail_template import *
from cryptography.fernet import Fernet
from app.core import config
import shutil
from pyfcm import FCMNotification
from api.endpoints import chime_chat
from profanityfilter import ProfanityFilter
from gtts import gTTS
from urllib.parse import urlparse
from fastapi import Request
import re

access_key = config.access_key
access_secret = config.access_secret
bucket_name = config.bucket_name

# Email Credential
email_username=config.email_username
email_password=config.email_password

# SMS Credential
sms_access_key=config.sms_access_key
sms_access_secret=config.sms_secret_access_key


def is_date(string, fuzzy=False):
    date_format = "%Y-%m-%d"  # example format to check
    try:
        date = datetime.datetime.strptime(string, date_format)
        return True
    except ValueError:
        return False


def isTimeFormat(input):
    try:
        time.strptime(input, "%H:%M")
        return True
    except ValueError:
        return False


def EncryptandDecrypt(otp, flag=1):
    key = Fernet.generate_key()
    message = otp.encode()
    f = Fernet(key)

    if flag == 1:
        encrypted = f.encrypt(message)
        return encrypted
    else:
        decrypted = f.decrypt(message)
        return decrypted

async def file_upload(file_name, ext, compress):
    base_dir = "rawcaster_uploads"
    try:
        os.makedirs(base_dir, mode=0o777, exist_ok=True)
    except OSError as e:
        sys.exit("Can't create {dir}: {err}".format(dir=base_dir, err=e))

    output_dir = base_dir + "/"

    characters = string.ascii_letters + string.digits
    # Generate the random string
    random_string = "".join(random.choice(characters) for i in range(18))

    filename = f"uploadfile_{random_string}{ext}"
    save_full_path = f"{output_dir}{filename}"
    
    with open(save_full_path, "wb") as buffer:
        shutil.copyfileobj(file_name.file, buffer)
    
    return save_full_path


def upload_to_s3(local_file_pth, s3_bucket_path):
    try:
        client_s3 = boto3.client(
            "s3", aws_access_key_id=access_key, aws_secret_access_key=access_secret
        )  # Connect to S3

        with open(local_file_pth, "rb") as data:  # Upload File To S3
            upload = client_s3.upload_fileobj(
                data, bucket_name, s3_bucket_path, ExtraArgs={"ACL": "public-read"}
            )

        os.remove(local_file_pth)

        url_location = client_s3.get_bucket_location(Bucket=bucket_name)[
            "LocationConstraint"
        ]
        url = f"https://{bucket_name}.s3.{url_location}.amazonaws.com/{s3_bucket_path}"
        return {"status": 1, "url": url}

    except Exception as e:
        return {"status": 0, "msg": f"Unable to upload:{e}"}


async def send_email(db, to_mail, subject, message):
    check_bounce_mail = (
        db.query(AwsBounceEmails).filter(AwsBounceEmails.email_id == to_mail).first()
    )
    if not check_bounce_mail:
        conf = ConnectionConfig(
            MAIL_USERNAME=email_username,
            MAIL_PASSWORD=email_password,
            MAIL_FROM="rawcaster@rawcaster.com",
            MAIL_PORT=587,
            MAIL_SERVER="email-smtp.us-west-2.amazonaws.com",
            MAIL_FROM_NAME="Rawcaster",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )

        message = MessageSchema(
            subject=subject, subtype="html", recipients=[to_mail], body=message
        )

        fm = FastMail(conf)
        await fm.send_message(message)

        return True

    else:
        return False


def sendSMS(mobile_no, message):
    # Create an SNS client
    sns = boto3.client(
        "sns",
        aws_access_key_id=sms_access_key,
        aws_secret_access_key=sms_access_secret,
        region_name="us-east-1",
    )  # Replace 'us-west-2' with your desired AWS region
    mobile_no=mobile_no.replace('+', '')
    # Send the SMS
    response = sns.publish(PhoneNumber=mobile_no, Message=message)
    # Check if the SMS was sent successfully
    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
        print(
            f'SMS sent successfully to {mobile_no} with message ID: {response["MessageId"]}'
        )
        return True
    else:
        print("Failed to send SMS")


def common_date(date, without_time=None):
    datetime = date.strftime("%Y-%m-%d %I:%M:%S")

    if without_time == 1:
        datetime = date.strftime("%Y-%m-%d")

    return datetime


def check_mail(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if re.match(pattern, email):
        return True
    else:
        return False


def checkAuthCode(authcode, auth_text):
    salt = st.SALT_KEY
    auth_text = str(salt) + str(auth_text)
    result = hashlib.sha1(auth_text.encode())
    if authcode == result.hexdigest():
        return True
    else:
        return False


def EmailorMobileNoValidation(email_id):
    email_id = email_id

    if check_mail(email_id) == True:
        return {"status": 1, "type": 1, "email": email_id, "mobile": None}

    elif email_id.isnumeric():
        
        return {"status": 1, "type": 2, "email": None, "mobile": email_id}

    else:
        res = email_id.replace("()+-", "")

        if res.isnumeric():
            return {"status": 1, "type": 2, "email": None, "mobile": res}

        else:
            return {"status": 0, "type": 0, "email": None, "mobile": None}


def pushNotify(db, user_ids, details, login_user_id):
    api_key = "AAAAJndtCwI:APA91bEdwo6X4izLPWkAaoYDIt9zUzrQ8pi_jHUFVne-xMuEDNiqCn1KBSse4TuxRd_5nakioin7l5p8mY7-OhdnXS-SubCqsc-UJS2mDtjJVEY3jq7K9kkE_-3O9LuKJTqPds8Ughi4"
    title = "New notification"
    type = details["type"] if details["type"] else "nuggets"
    message = details["message"] if details["message"] else ""
    data = details["data"] if details["data"] else ""

    get_user = db.query(User).filter(User.id == login_user_id).first()

    if get_user and type != "callend":
        title = get_user.display_name

    get_api_token = db.query(
        ApiTokens.user_id,
        ApiTokens.device_type,
        ApiTokens.push_device_id,
        UserSettings.nuggets,
        UserSettings.events,
        UserSettings.friend_request,
    )

    get_api_token = get_api_token.filter(
        UserSettings.user_id == ApiTokens.user_id,
        ApiTokens.status == 1,
        and_(or_(ApiTokens.push_device_id != None, ApiTokens.push_device_id != "")),
    ).group_by(ApiTokens.push_device_id)

    if user_ids:
        get_api_token = get_api_token.filter(ApiTokens.user_id.in_(user_ids))

    get_api_token = get_api_token.all()
    registration_ids = []

    if get_api_token:
        for token in get_api_token:
            permission_arr = list(str((type == "callend") and "111" or token[type]))
            if len(permission_arr) > 2 and permission_arr[0] == "1":
                push_id = token.push_device_id
                registration_ids.append(push_id)

    registration_ids = [
        registration_ids[i : i + 500] for i in range(0, len(registration_ids), 500)
    ]

    if registration_ids:
        fcmMsg = {}
        fcmFields = []
        fcmMsg.update({"title": title, "body": message, "sound": "default"})

        for register_id in registration_ids:
            if type == "callend" and message == "Call Ended":
                fcmFields.append(
                    {
                        "registration_ids": register_id,  #  expects an array of ids
                        "priority": "high",
                        "notification": fcmMsg,
                        "data": data,
                    }
                )

            else:
                fcmFields.append(
                    {
                        "registration_ids": register_id,  # expects an array of ids
                        #   "priority":'high',
                        "notification": fcmMsg,
                        "data": data,
                    }
                )

            url = "https://fcm.googleapis.com/fcm/send"
            headers = {
                "Authorization": "key=" + api_key,
                "Content-Type": "application/json",
            }
            response = requests.post(url, headers=headers, json=fcmFields)
            result = response.text

            if response.status_code != 200:
                return False
                # print('FCM Send Error:', result)
            else:
                pass
                # do something with result

    return True


def encryptionString():
    return "rawcaster@!@#$QWERTxcvbn"


def friendRequestNotifcationEmail(
    db, senderId, receiverId, flag
):  # flag = 1 Friend Request Received flag = 2 Friend Request Accepted
    if senderId != "" and receiverId != "":
        to = ""
        sunject = ""
        body = ""
        phone = ""
        sms_message = ""

        my_friends = db.query(MyFriends).filter(
            MyFriends.sender_id == senderId,
            MyFriends.receiver_id == receiverId,
            MyFriends.status == 1,
        )
        if flag == 1:
            my_friends = my_friends.filter(MyFriends.request_status == 0).first()

            if my_friends:
                displayName = (
                    my_friends.user1.display_name if my_friends.sender_id else None
                )
                email_id = my_friends.user1.email_id if my_friends.sender_id else None
                profile_img = (
                    my_friends.user1.profile_img if my_friends.sender_id else None
                )
                phone = my_friends.user1.mobile_no if my_friends.sender_id else None

                to = email_id
                subject = "New Connection Request"
                invite_url = inviteBaseurl()
                encrypt_string = encryptionString()
                senderId = f"{senderId}"
                url_path = base64.b64encode(
                    senderId.encode("utf-8") + encrypt_string.encode("utf-8")
                )
                url = f"{invite_url}signin/{url_path}/connectionrequest"

                body = ""  # Pending

                sms_message = (
                    f"New Connection Request From {displayName} in rawcaster.com"
                )

        elif flag == 2:
            my_friends = my_friends.filter(MyFriends.request_status == 1).first()
            if my_friends:
                displayName = (
                    my_friends.user2.display_name if my_friends.receiver_id else None
                )
                email_id = my_friends.user2.email_id if my_friends.receiver_id else None
                profile_img = (
                    my_friends.user2.profile_img if my_friends.receiver_id else None
                )
                phone = my_friends.user2.mobile_no if my_friends.receiver_id else None

                to = email_id
                subject = "Connection Accepted Notification"
                invite_url = inviteBaseurl()
                url_path = base64.b64encode(str(receiverId).encode("utf-8"))

                url = f"{invite_url}signin/{url_path}/connectionrequest"

                body = ""
                sms_message = f"Connection Accepted From {displayName} You`re now connected with {displayName} Clicks on Facebook. You can see his photos, posts and more on his profile"
        return sms_message, body
    else:
        print("Invalid Parameters")


def addNotificationSmsEmail(db, user, email_detail, login_user_id):
    sms_message = email_detail["sms_message"] if "sms_message" in email_detail else ""
    mail_message = (
        email_detail["mail_message"] if "mail_message" in email_detail else ""
    )
    subject = email_detail["subject"] if "subject" in email_detail else ""
    type = email_detail["type"] if "type" in email_detail else "nuggets"
    email = email_detail["email"] if "email" in email_detail else ""

    mobile_nos = ""
    if user:
        get_user = (
            db.query(
                User.id,
                User.country_code,
                User.email_id,
                User.mobile_no,
                UserSettings.nuggets,
                UserSettings.events,
                UserSettings.friend_request,
            )
            .filter(
                UserSettings.user_id == User.id, User.status == 1, User.id.in_(user)
            )
            .all()
        )

        for user in get_user:
            permission_arr = list(user[type])
            if len(permission_arr) > 2 and permission_arr[1] == "1":
                email += user["email_id"] + ","

            elif (
                len(permission_arr) > 2
                and permission_arr[2] == "1"
                and user["mobile_no"] != ''
                and user['mobile_no'] != None
            ):
                mobile_nos += f"{user['country_code']}{str(user['mobile_no'])},"
    # Type 1- Phone number 2- Email
    if email:
        add_notification = NotificationSmsEmail(
            user_id=login_user_id,
            type=2,
            mobile_no_email_id=email,
            subject=subject,
            message=mail_message,
            created_at=datetime.datetime.utcnow(),
            status=0,
        )
        db.add(add_notification)
        db.commit()

    if mobile_nos:
        add_notification = NotificationSmsEmail(
            user_id=login_user_id,
            type=1,
            mobile_no_email_id=mobile_nos,
            subject="",
            message=sms_message,
            created_at=datetime.datetime.utcnow(),
            status=0,
        )
        db.add(add_notification)
        db.commit()

    return True


def get_nugget_detail(db, nugget_id, login_user_id):
    nugget_detail = []
    is_downloadable = 0

    get_nuggets = db.query(Nuggets).filter(Nuggets.id == nugget_id).first()

    if get_nuggets:
        total_likes=get_nuggets.total_like_count
        total_comments=get_nuggets.total_comment_count
        total_views=get_nuggets.total_view_count
        total_pollvote=get_nuggets.total_poll_count
        # total_likes = (
        #     db.query(NuggetsLikes)
        #     .filter(
        #         NuggetsLikes.user_id == login_user_id,
        #         NuggetsLikes.nugget_id == nugget_id,
        #     )
        #     .distinct()
        #     .count()
        # )
        # total_comments = (
        #     db.query(NuggetsComments)
        #     .filter(NuggetsComments.nugget_id == nugget_id, NuggetsComments.status == 1)
        #     .distinct()
        #     .count()
        # )
        # total_views = (
        #     db.query(NuggetView)
        #     .filter(
        #         NuggetView.nugget_id == nugget_id, NuggetView.user_id == login_user_id
        #     )
        #     .distinct()
        #     .count()
        # )
        # total_pollvote = (
        #     db.query(NuggetPollVoted)
        #     .filter(
        #         NuggetPollVoted.user_id == login_user_id,
        #         NuggetPollVoted.nugget_id == nugget_id,
        #     )
        #     .distinct()
        #     .count()
        # )

        attachments = []
        poll_options = []

        # Nugget Attachments
        nugget_attachment = db.query(NuggetsAttachment).filter(
            NuggetsAttachment.nugget_id == get_nuggets.nuggets_id,
            NuggetsAttachment.status == 1,
        )
        get_nugget_attachment_count = nugget_attachment.count()

        get_nugget_attachment = nugget_attachment.all()

        if get_nugget_attachment:
            for nug_attach in get_nugget_attachment:
                attachments.append(
                    {
                        "media_id": nug_attach.id,
                        "media_type": nug_attach.media_type
                        if nug_attach.media_type
                        else "",
                        "media_file_type": nug_attach.media_file_type
                        if nug_attach.media_file_type
                        else "",
                        "path": nug_attach.path if nug_attach.path else "",
                    }
                )

        # Nuggets Poll Option
        get_nugget_poll_option = (
            db.query(NuggetPollOption)
            .filter(
                NuggetPollOption.nuggets_master_id == get_nuggets.nuggets_id,
                NuggetPollOption.status == 1,
            )
            .all()
        )
        if get_nugget_poll_option:
            for poll_nugg in get_nugget_poll_option:
                poll_options.append(
                    {
                        "option_id": poll_nugg.id,
                        "option_name": poll_nugg.option_name
                        if poll_nugg.option_name
                        else "",
                        "option_percentage": poll_nugg.poll_vote_percentage
                        if poll_nugg.poll_vote_percentage
                        else "",
                        "votes": poll_nugg.votes if poll_nugg.votes else 0,
                    }
                )

        shared_with = {}
        shared_detail = []

        if get_nuggets.user_id == login_user_id:  # only when nugget owner
            get_share_nuggets = (
                db.query(NuggetsShareWith)
                .filter(NuggetsShareWith.nuggets_id == nugget_id)
                .all()
            )
            if get_share_nuggets:
                shared_group_ids = []
                type = 0

                for share_nug in get_share_nuggets:
                    type = share_nug.type
                    shared_group_ids.append(share_nug.share_with)

                if type == 1:
                    friend_groups = (
                        db.query(FriendGroups.group_name, FriendGroups.group_icon,
                                 FriendGroups.id)
                        .filter(FriendGroups.id.in_(shared_group_ids))
                        .all()
                    )
                    for frnd_group in friend_groups:
                        shared_detail.append(
                            {
                                "name": frnd_group.group_name
                                if frnd_group.group_name
                                else "",
                                "img": frnd_group.group_icon
                                if frnd_group.group_icon
                                else "",
                                "id": frnd_group.id,
                            }
                        )

                elif type == 2:
                    friend_groups = (
                        db.query(User.display_name, User.profile_img, User.id)
                        .filter(User.id.in_(shared_group_ids))
                        .all()
                    )
                    for frnd_gp in friend_groups:
                        shared_detail.append(
                            {
                                "id": frnd_gp.id,
                                "name": frnd_gp.display_name
                                if frnd_gp.display_name
                                else "",
                                "img": frnd_gp.profile_img
                                if frnd_gp.profile_img
                                else "",
                            }
                        )

            shared_group_list = []
            shared_friends_list = []

            if (
                get_nuggets.share_type == 3
                or get_nuggets.share_type == 4
                or get_nuggets.share_type == 5
            ):
                for shares in get_share_nuggets:
                    if shares.type == 1:
                        shared_group_list.append(shares.share_with)
                    if shares.type == 2:
                        shared_group_list.append(shares.share_with)

            shared_with.update(
                {
                    "shared_friends_list": shared_friends_list,
                    "shared_group_list": shared_group_list,
                }
            )

        following = (
            db.query(FollowUser)
            .filter(
                FollowUser.follower_userid == login_user_id,
                FollowUser.following_userid == get_nuggets.user_id,
            )
            .count()
        )
        follow_count = (
            db.query(FollowUser)
            .filter(FollowUser.following_userid == get_nuggets.user_id)
            .count()
        )

        nugget_like = False
        nugget_view = False
        checklike = (
            db.query(NuggetsLikes)
            .filter(
                NuggetsLikes.nugget_id == get_nuggets.id,
                NuggetsLikes.user_id == login_user_id,
            )
            .first()
        )
        checkview = (
            db.query(NuggetView)
            .filter(
                NuggetView.nugget_id == get_nuggets.id,
                NuggetView.user_id == login_user_id,
            )
            .first()
        )

        if checklike:
            nugget_like = True
        if checkview:
            nugget_view = True

        if login_user_id == get_nuggets.user_id:
            following = 1

        voted = (
            db.query(NuggetPollVoted)
            .filter(
                NuggetPollVoted.nugget_id == get_nuggets.id,
                NuggetPollVoted.user_id == login_user_id,
            )
            .count()
        )
        saved = (
            db.query(NuggetsSave)
            .filter(
                NuggetsSave.nugget_id == get_nuggets.id,
                NuggetsSave.user_id == login_user_id,
            )
            .count()
        )

        if get_nuggets.share_type == 1:
            if following == 1:
                is_downloadable = 1

            else:
                get_friend_requests = (
                    db.query(MyFriends)
                    .filter(
                        or_(
                            MyFriends.receiver_id == get_nuggets.user_id,
                            MyFriends.receiver_id == login_user_id,
                        ),
                        or_(
                            MyFriends.sender_id == login_user_id,
                            MyFriends.sender_id == get_nuggets.user_id,
                        ),
                        MyFriends.status == 1,
                        MyFriends.request_status == 1,
                    )
                    .order_by(MyFriends.id.desc())
                    .first()
                )

                if get_friend_requests:
                    is_downloadable = 1
        else:
            is_downloadable = 1

        nuggets_details = {
            "nugget_id": get_nuggets.id,
            "content": get_nuggets.nuggets_master.content,
            "metadata": get_nuggets.nuggets_master._metadata,
            "created_date": common_date(get_nuggets.created_date)
            if get_nuggets.created_date
            else "",
            "user_id": get_nuggets.user_id,
            "user_ref_id": (
                get_nuggets.user.user_ref_id if get_nuggets.user.user_ref_id else ""
            )
            if get_nuggets.user_id
            else "",
            "type": get_nuggets.type if get_nuggets.type else "",
            "original_user_id": get_nuggets.nuggets_master.user.id,
            "original_user_name": get_nuggets.nuggets_master.user.display_name,
            "original_user_image": get_nuggets.nuggets_master.user.profile_img,
            "user_name": get_nuggets.user.display_name,
            "user_image": get_nuggets.user.profile_img,
            "liked": nugget_like,
            "viewed": nugget_view,
            "following": True if following > 0 else False,
            "follow_count": follow_count,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_views": total_views,
            "total_media": get_nugget_attachment_count,
            "share_type": get_nuggets.share_type if get_nuggets.share_type else "",
            "media_list": attachments,
            "is_nugget_owner": 1 if get_nuggets.user_id == login_user_id else 0,
            "is_master_nugget_owner": 1
            if get_nuggets.nuggets_master.user_id == login_user_id
            else 0,
            "shared_detail": shared_detail,
            "shared_with": shared_with,
            "is_downloadable": is_downloadable,
            "poll_option": poll_options,
            "poll_duration": get_nuggets.nuggets_master.poll_duration
            if get_nuggets.nuggets_master.poll_duration
            else ""
            if get_nuggets.nuggets_id
            else "",
            "voted": voted,
            "total_vote": total_pollvote,
            "saved": True if saved else False,
        }
        return nuggets_details


def getGroupids(db, login_user_id):
    group_ids = []

    if login_user_id:
        friend_group_memebers = (
            db.query(FriendGroupMembers.group_id)
            .filter_by(status=1, user_id=login_user_id)
            .all()
        )
        if friend_group_memebers:
            for group in friend_group_memebers:
                group_ids.append(group.group_id)
    return group_ids


def get_friend_requests(db, login_user_id, requested_by, request_status, response_type):
    pending = []
    accepted = []
    rejected = []
    blocked = []

    my_friends = db.query(MyFriends).filter(MyFriends.status == 1)

    if requested_by == 1:  # Friend request sent from this user to others
        my_friends = my_friends.filter_by(sender_id=login_user_id)

    elif requested_by == 2:  # Friend request reveived from other users to this user
        my_friends = my_friends.filter_by(receiver_id=login_user_id)

    else:  # Both sent and received requests
        my_friends = my_friends.filter(
            (MyFriends.sender_id == login_user_id)
            | (MyFriends.receiver_id == login_user_id)
        )

    if request_status and len(request_status) > 0:
        my_friends = my_friends.filter_by(MyFriends.request_status.in_(request_status))

    get_friend_requests = my_friends.all()

    if get_friend_requests:
        friend_details = []
        for friend_requests in get_friend_requests:
            if friend_requests.sender_id == login_user_id:
                friend_id = friend_requests.receiver_id

                friend_details.append(
                    {
                        "friend_request_id": friend_requests.id,
                        "user_ref_id": friend_requests.user2.user_ref_id
                        if friend_requests.receiver_id
                        else "",
                        "user_id": (
                            friend_requests.user2.id if friend_requests.user2.id else ""
                        )
                        if friend_requests.receiver_id
                        else "",
                        "email_id": (
                            friend_requests.user2.email_id
                            if friend_requests.user2.email_id
                            else ""
                        )
                        if friend_requests.receiver_id
                        else "",
                        "first_name": (
                            friend_requests.user2.first_name
                            if friend_requests.user2.first_name
                            else ""
                        )
                        if friend_requests.receiver_id
                        else "",
                        "last_name": (
                            friend_requests.user2.last_name
                            if friend_requests.user2.last_name
                            else ""
                        )
                        if friend_requests.receiver_id
                        else "",
                        "display_name": (
                            friend_requests.user2.display_name
                            if friend_requests.user2.display_name
                            else ""
                        )
                        if friend_requests.receiver_id
                        else "",
                        "gender": (
                            friend_requests.user2.gender
                            if friend_requests.user2.gender
                            else ""
                        )
                        if friend_requests.receiver_id
                        else "",
                        "profile_img": (
                            friend_requests.user2.profile_img
                            if friend_requests.user2.profile_img
                            else ""
                        )
                        if friend_requests.receiver_id
                        else "",
                    }
                )

            else:
                friend_id = friend_requests.sender_id
                friend_details.append(
                    {
                        "friend_request_id": friend_requests.id,
                        "user_ref_id": friend_requests.user1.user_ref_id
                        if friend_requests.sender_id
                        else "",
                        "user_id": (
                            friend_requests.user1.id if friend_requests.user1.id else ""
                        )
                        if friend_requests.sender_id
                        else "",
                        "email_id": (
                            friend_requests.user1.email_id
                            if friend_requests.user1.email_id
                            else ""
                        )
                        if friend_requests.sender_id
                        else "",
                        "first_name": (
                            friend_requests.user1.first_name
                            if friend_requests.user1.first_name
                            else ""
                        )
                        if friend_requests.sender_id
                        else "",
                        "last_name": (
                            friend_requests.user1.last_name
                            if friend_requests.user1.last_name
                            else ""
                        )
                        if friend_requests.sender_id
                        else "",
                        "display_name": (
                            friend_requests.user1.display_name
                            if friend_requests.user1.display_name
                            else ""
                        )
                        if friend_requests.sender_id
                        else "",
                        "gender": (
                            friend_requests.user1.gender
                            if friend_requests.user1.gender
                            else ""
                        )
                        if friend_requests.sender_id
                        else "",
                        "profile_img": (
                            friend_requests.user1.profile_img
                            if friend_requests.user1.profile_img
                            else ""
                        )
                        if friend_requests.sender_id
                        else "",
                    }
                )

            if response_type == 1:  # only user ids
                if friend_requests.request_status == 0:
                    pending.append(friend_id)  # if pending
                if friend_requests.request_status == 1:
                    accepted.append(friend_id)  # if accepted
                if friend_requests.request_status == 2:
                    rejected.append(friend_id)  # if rejected
                if friend_requests.request_status == 3:
                    blocked.append(friend_id)  # if blocked

            else:
                if friend_requests.request_status == 0:
                    pending.append(friend_details)
                if friend_requests.request_status == 1:
                    accepted.append(friend_details)
                if friend_requests.request_status == 2:
                    rejected.append(friend_details)
                if friend_requests.request_status == 3:
                    blocked.append(friend_details)

    return {
        "pending": pending,
        "accepted": accepted,
        "rejected": rejected,
        "blocked": blocked,
    }


def getFollowings(db, user_id):
    following_ids = []
    if user_id:
        following_users_list = (
            db.query(FollowUser).filter_by(status=1, follower_userid=user_id).all()
        )
        if following_users_list:
            for follow_usr in following_users_list:
                following_ids.append(follow_usr.following_userid)
          
    return following_ids


def NuggetAccessCheck(db, login_user_id, nugget_id):
    group_ids = getGroupids(db, login_user_id)
    
    requested_by = None
    request_status = 1
    response_type = 1
    my_friends_req = get_friend_requests(
        db, login_user_id, requested_by, request_status, response_type
    )
    my_friends = my_friends_req["accepted"]

    my_followings = getFollowings(db, login_user_id)
    type = None
    rawid = GetRawcasterUserID(db, type)

    criteria = db.query(Nuggets)
    criteria = criteria.join(User, Nuggets.user_id == User.id, isouter=True)
    criteria = criteria.join(
        NuggetsMaster, Nuggets.nuggets_id == NuggetsMaster.id, isouter=True
    )
    criteria = criteria.join(
        NuggetsShareWith, Nuggets.id == NuggetsShareWith.nuggets_id, isouter=True
    )
    criteria = criteria.join(
        NuggetView, Nuggets.id == NuggetView.nugget_id, isouter=True
    )
    criteria = criteria.filter(
        Nuggets.status == 1,
        Nuggets.nugget_status == 1,
        NuggetsMaster.status == 1,
        Nuggets.id == nugget_id,
    )
    criteria = criteria.filter(
        or_(
            Nuggets.user_id == login_user_id,
            and_(Nuggets.share_type == 1),
            and_(Nuggets.share_type == 2, Nuggets.user_id == login_user_id),
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
            and_(Nuggets.share_type == 6, Nuggets.user_id.in_(my_friends)),
            and_(Nuggets.share_type == 7, Nuggets.user_id.in_(my_followings)),
            and_(Nuggets.user_id == rawid),
        )
    )

    requested_by = None
    request_status = 3
    response_type = 1

    get_all_blocked_users = get_friend_requests(
        db, login_user_id, requested_by, request_status, response_type
    )

    blocked_users = get_all_blocked_users["blocked"]

    if blocked_users:
        criteria = criteria.filter(Nuggets.user_id.notin_(blocked_users))

    check_nuggets = criteria.count()
    
    if check_nuggets > 0:
        return True
    else:
        return False


def getFollowers(db, login_user_id):
    following_ids = []
    if login_user_id and login_user_id != None and login_user_id != "":
        following_users_list = (
            db.query(FollowUser)
            .filter(
                FollowUser.status == 1, FollowUser.following_userid == login_user_id
            )
            .all()
        )
        if following_users_list:
            for follow_usr in following_users_list:
                following_ids.append(follow_usr.follower_userid)

    return following_ids


def Insertnotification(db, user_id, notification_origin_id, notification_type, ref_id):
    if user_id != notification_origin_id:
        add_notification = Notification(
            user_id=user_id,
            notification_origin_id=notification_origin_id
            if notification_origin_id
            else user_id,
            notification_type=notification_type,
            ref_id=ref_id,
            created_datetime=datetime.datetime.utcnow(),
        )
        db.add(add_notification)
        db.commit()


def nuggetNotifcationEmail(db, nugget_id):
    if nugget_id:
        get_nugget = db.query(Nuggets).filter_by(id=nugget_id, status=1).first()
        if get_nugget:
            postedUserName = (
                (get_nugget.user.display_name if get_nugget.user.display_name else "")
                if get_nugget.user_id
                else ""
            )
            profilePic = (
                (get_nugget.user.profile_img if get_nugget.user.profile_img else "")
                if get_nugget.user_id
                else ""
            )
            postedDate = get_nugget.created_date if get_nugget.created_date else ""
            username = (
                f"{get_nugget.user.first_name if get_nugget.user.first_name else ''} {get_nugget.user.last_name if get_nugget.user.last_name else ''}"
                if get_nugget.user_id
                else ""
            )
            sms_message = f"{username} shares New Nugget in rawcaster.com"

            body = ""

            invite_url = inviteBaseurl()
            nuggetId = base64.b64encode(str(nugget_id).encode("utf-8"))
            meetingUrl = f"{invite_url}share/index.php?id={nuggetId}"

            return sms_message, body


def get_ip():
    response = requests.get('https://ipinfo.io')
    data = response.json()
    userIP = data.get('ip')
    # # response=request.client.host
    # response = requests.get("https://api64.ipify.org?format=json").json()
    return userIP


def FindLocationbyIP(userIP):
    response = requests.get(f"https://ipwhois.app/json/{userIP}/").json()

    if response["success"] == True:
        return {
            "status": 1,
            "ip": userIP,
            "city": response.get("city"),
            "region": response.get("region"),
            "country": response.get("country"),
            "latitude": response.get("latitude"),
            "longitude": response.get("longitude"),
        }
    else:
        return {"status": 0}


def CheckMobileNumber(db, mobile_no, geo_location):
    result = {"status": 0, "msg": "Please enter a valid phone number."}
    if geo_location:
        country = geo_location.split(",")
        if (country != "") and mobile_no != "":
            found = 0
            
            for place in country:
                cty = str(place.replace(".", "")).strip()
                user_country = db.query(Country).filter(Country.name.ilike(cty)).first()

                if user_country and user_country.mobile_no_length != "":


                    mobileno = str(mobile_no).replace("+", "")
                    mobileno = str(mobile_no).replace("-", "")
                    if user_country.id == 156 and geo_location[0:1] == 0:
                        mobileno = geo_location[1:]

                    if str(user_country.mobile_no_length) in str(len(mobile_no)):
                        found = 1
                        result = {
                            "status": 1,
                            "country_code": user_country.country_code,
                            "country_id": user_country.id,
                            "mobile_no": mobileno,
                        }
                        break
                    else:
                        formated_mobileno = mobileno[
                            len(user_country.country_code) - 1 :
                        ]

                        if str(user_country.mobile_no_length) in str(
                            len(formated_mobileno)
                        ):
                            found = 1
                            result = {
                                "status": 1,
                                "country_code": user_country.country_code,
                                "country_id": user_country.id,
                                "mobile_no": formated_mobileno,
                            }
                        break
                else:
                    found = 0

            if found == 0:
                result = {
                    "status": 0,
                    "msg": f"Unable to get Country for this Mobile number",
                }

        else:
            result = {"status": 0, "msg": "Mobile number is empty"}

    else:
        result = {"status": 0, "msg": "Unable to get user location"}
    return result


def inviteBaseurl():
    return "https://prod.rawcaster.com/"
    # return "https://dev.rawcaster.com/"
    # return 'https://rawcaster.com/'


def generateLink(text:str):
    user_ref_id = text.encode("ascii")
    hashed_user_ref_id = (base64.b64encode(user_ref_id)).decode("ascii")
    
    return hashed_user_ref_id

def OTPverificationtype(db, get_user):
    type = 0
    country = ""
    if (get_user and get_user.mobile_no != "") or get_user.email_id != "":
        if get_user.geo_location != "":
            country = (
                (get_user.geo_location).split(",")[-1].strip().rstrip(".")
                if get_user.geo_location
                else ""
            )
        if country != "":
            user_country = (
                db.query(Country)
                .filter(Country.sms_enabled == 1, Country.name == country)
                .first()
            )
            if user_country:
                type = 1
                update_user = (
                    db.query(User)
                    .filter(User.id == get_user.id)
                    .update(
                        {
                            "country_code": user_country.country_code,
                            "country_id": user_country.id,
                        }
                    )
                )
                db.commit()

    return type


def get_friend_requests(db, login_user_id, requested_by, request_status, response_type):
    get_my_friends = db.query(MyFriends).filter(MyFriends.status == 1)

    pending = []
    accepted = []
    rejected = []
    blocked = []
    if requested_by == 1:  # Friend request sent from this user to others
        get_my_friends = get_my_friends.filter(MyFriends.sender_id == login_user_id)

    elif requested_by == 2:  # Friend request reveived from other users to this user
        get_my_friends = get_my_friends.filter(MyFriends.receiver_id == login_user_id)

    else:  # Both sent and received requests
        get_my_friends = get_my_friends.filter(
            or_(
                MyFriends.sender_id == login_user_id,
                MyFriends.receiver_id == login_user_id,
            )
        )

    if request_status:  # pending, accepted, rejected, blocked
        get_my_friends = get_my_friends.filter(
            MyFriends.request_status.in_([request_status])
        )

    get_my_friends = get_my_friends.all()

    if get_my_friends:
        for frnd_request in get_my_friends:
            friend_details = []
            if frnd_request.sender_id == login_user_id:  # Receiver
                friend_id = frnd_request.receiver_id

                friend_details.append(
                    {
                        "friend_request_id": frnd_request.id,
                        "user_ref_id": frnd_request.user1.user_ref_id
                        if frnd_request.receiver_id
                        else None,
                        "user_id": frnd_request.user1.id
                        if frnd_request.receiver_id
                        else None,
                        "email_id": frnd_request.user1.email_id
                        if frnd_request.receiver_id
                        else "",
                        "first_name": frnd_request.user1.first_name
                        if frnd_request.receiver_id
                        else "",
                        "last_name": frnd_request.user1.last_name
                        if frnd_request.receiver_id
                        else "",
                        "display_name": frnd_request.user1.display_name
                        if frnd_request.receiver_id
                        else "",
                        "gender": frnd_request.user1.gender
                        if frnd_request.receiver_id
                        else "",
                        "profile_img": frnd_request.user1.profile_img
                        if frnd_request.receiver_id
                        else "",
                    }
                )

            else:
                friend_id = frnd_request.sender_id
                friend_details.append(
                    {
                        "friend_request_id": frnd_request.id,
                        "user_ref_id": frnd_request.user1.user_ref_id
                        if frnd_request.sender_id
                        else None,
                        "user_id": frnd_request.user1.id
                        if frnd_request.sender_id
                        else None,
                        "email_id": frnd_request.user1.email_id
                        if frnd_request.sender_id
                        else "",
                        "first_name": frnd_request.user1.first_name
                        if frnd_request.sender_id
                        else "",
                        "last_name": frnd_request.user1.last_name
                        if frnd_request.sender_id
                        else "",
                        "display_name": frnd_request.user1.display_name
                        if frnd_request.sender_id
                        else "",
                        "gender": frnd_request.user1.gender
                        if frnd_request.sender_id
                        else "",
                        "profile_img": frnd_request.user1.profile_img
                        if frnd_request.sender_id
                        else "",
                    }
                )

            if response_type == 1:  # only user ids
                if frnd_request.request_status == 0:
                    pending.append(friend_id)  # if pending
                elif frnd_request.request_status == 1:
                    accepted.append(friend_id)  # if accepted
                elif frnd_request.request_status == 2:
                    rejected.append(friend_id)  # if rejected
                elif frnd_request.request_status == 3:
                    blocked.append(friend_id)  # if blocked
            else:
                if frnd_request.request_status == 0:
                    pending += friend_details
                elif frnd_request.request_status == 1:
                    accepted += friend_details
                elif frnd_request.request_status == 2:
                    rejected += friend_details
                elif frnd_request.request_status == 3:
                    blocked += friend_details

    return {
        "pending": pending,
        "accepted": accepted,
        "rejected": rejected,
        "blocked": blocked,
    }


def MutualFriends(db, login_user_id, user_id):
    mutual_friends = 0
    myfriends = get_friend_requests(db, login_user_id, None, None, 1)
    otherfriends = get_friend_requests(db, user_id, None, None, 1)

    if myfriends and otherfriends:
        if myfriends["accepted"] and otherfriends["accepted"]:
            mutual_friends = len(
                set(myfriends["accepted"]).intersection(otherfriends["accepted"])
            )
        else:
            return {"status": 0, "msg": "Mutual Friends failed"}
    return mutual_friends


def IsAccountVerified(db, user_id):
    status = False
    get_user = db.query(User).filter(User.id == user_id).first()

    if get_user and (
        get_user.is_email_id_verified == 1 or get_user.is_mobile_no_verified == 1
    ):
        status = True

    return status


def GetHashTags(content):
    tags = []
    if content != "":
        matches = re.findall(r"(\#\S+)", content, re.UNICODE)
        tags = []
        if matches:
            for match in matches:
                tags.append(match)
    return tags


def StoreHashTags(db, nugget):
    get_nugget = db.query(Nuggets).filter(Nuggets.id == nugget).first()

    if get_nugget.nuggets_master.content and get_nugget.nuggets_master.content != "":
        tags = GetHashTags(get_nugget.nuggets_master.content)

        deleteresult = (
            db.query(NuggetHashTags).filter_by(nugget_id=get_nugget.id).delete()
        )
        db.commit()

        if tags:
            for tag in tags:
                add_NuggetHashTags = NuggetHashTags(
                    nugget_master_id=get_nugget.nuggets_id,
                    nugget_id=get_nugget.id,
                    user_id=get_nugget.user_id,
                    country_id=get_nugget.user.country_id,
                    hash_tag=tag,
                    created_date=datetime.datetime.utcnow(),
                )
                db.add(add_NuggetHashTags)
                db.commit()


def FriendsCount(db, user_id):
    get_friend_requests = (
        db.query(MyFriends)
        .filter(
            MyFriends.status == 1,
            MyFriends.request_status == 1,
            or_(MyFriends.sender_id == user_id, MyFriends.receiver_id == user_id),
        )
        .count()
    )
    return get_friend_requests


def FriendsandGroupPermission(db, myid, otherid, flag):
    if flag == 1:
        get_friend_requests = (
            db.query(MyFriends)
            .filter(
                MyFriends.status == 1,
                MyFriends.request_status == 1,
                or_(MyFriends.sender_id == myid, MyFriends.sender_id == otherid),
                or_(MyFriends.receiver_id == otherid, MyFriends.receiver_id == myid),
            )
            .one()
        )
        if get_friend_requests:
            return True
        else:
            return False
    else:
        groupmember = (
            db.query(FriendGroupMembers)
            .filter(
                FriendGroupMembers.user_id == myid,
                FriendGroupMembers.group_id.in_(otherid),
            )
            .count()
        )
        if groupmember > 0:
            return True
        else:
            return False


def ProfilePreference(db, myid, otherid, field, value):
    settings = db.query(UserSettings).filter(UserSettings.user_id == otherid).first()

    if settings and settings.filed:
        if settings.field == 0:
            return ""

        elif settings.field == 1:
            return value

        elif settings.field == 2:
            flag = 1
            if FriendsandGroupPermission(db, myid, otherid, flag) == True:
                return value
            else:
                return ""

        elif settings.field == 3:
            list = []
            online_group_list = (
                db.query(UserProfileDisplayGroup)
                .filter_by(user_id=otherid, profile_id=field)
                .all()
            )

            if online_group_list:
                for group_list in online_group_list:
                    list.append(group_list.groupid)
            if list != []:
                flag = 2
                if FriendsandGroupPermission(db, myid, list, flag) == True:
                    return value
                else:
                    return ""
    else:
        return False


# def get_pagination(row_count, page, size):
#     current_page_no = page if page >= 1 else 1

#     total_pages = math.ceil(row_count / size)

#     if current_page_no > total_pages:
#         current_page_no = total_pages

#     limit =  current_page_no * size
#     offset = limit - size

#     if limit > row_count:
#         limit = offset + (row_count % size)

#     limit = limit - offset

#     if offset < 0:
#         offset = 0

#     return [limit, offset,total_pages]


def get_pagination(row_count, current_page_no, default_page_size):
    current_page_no = int(current_page_no)

    total_pages = math.ceil(row_count / default_page_size)

    if current_page_no > total_pages:
        current_page_no = total_pages

    limit = current_page_no * default_page_size
    offset = limit - default_page_size

    if limit > row_count:
        limit = offset + row_count % default_page_size

    limit = limit - offset

    return limit, offset, total_pages


def PollVoteCalculation(db, nugget):
    get_nugget_votes = db.query(NuggetPollVoted).filter(
        NuggetPollVoted.nugget_master_id == nugget, NuggetPollVoted.status == 1
    )
    tot_nugget_vote = get_nugget_votes.count()

    nugget_vote_ids = {poll_vote.poll_option_id for poll_vote in get_nugget_votes.all()}

    for poll in nugget_vote_ids:
        individual_poll = db.query(NuggetPollVoted).filter(
            NuggetPollVoted.poll_option_id == poll, NuggetPollVoted.status == 1
        )
        individual_poll_id = individual_poll.first()
        individual_poll_count = individual_poll.count()

        percentage = round((individual_poll_count / tot_nugget_vote) * 100, 2)
        update_nugget_poll = (
            db.query(NuggetPollOption)
            .filter(NuggetPollOption.id == individual_poll_id.poll_option_id)
            .update(
                {"poll_vote_percentage": percentage, "votes": individual_poll_count}
            )
        )
        db.commit()

    # getvotes=db.query(NuggetPollOption.id,NuggetPollOption.option_name,func.count(NuggetPollVoted.id).label('total_votes')).filter(NuggetPollVoted.poll_option_id == NuggetPollOption.id).filter(NuggetPollOption.nuggets_master_id == nugget).all()

    # if getvotes:
    #     total_votes = sum(map(itemgetter('total_votes'), getvotes))
    #     print(total_votes)
    #     for votes in getvotes:
    #         print(votes.id,"id")


def eventPostNotifcationEmail(db, event_id):
    if event_id and event_id.isdigit():
        to = ""
        subject = ""
        body = ""
        phone = ""
        event = db.query(Events).filter_by(id=event_id, status=1).first()
        if event:
            event_invitations = event.event_invitations
            cover_img = event.cover_img
            event_title = event.title
            event_start_time = event.start_date_time
            event_start_time = datetime.datetime.strptime(
                str(event_start_time), "%Y-%m-%d %H:%M:%S"
            )
            eventStartTime = event_start_time.strftime("%-d %B %Y %-I:%M %p")
            subject = "New Event Created"
            invite_url = inviteBaseurl()
            meeting_url = f"{invite_url}joinmeeting/{event.ref_id}"
            event_creator_name = (
                event.created_by.display_name
                if event.created_by and event.created_by.display_name
                else "N/A"
            )
            sms_message = f"Hi, {event_creator_name} is inviting you to join a web event called {event_title}. The link for this Rawcaster event is: {meeting_url}"

            body = event_shared(
                event_creator_name, cover_img, event_title, eventStartTime, meeting_url
            )
            return sms_message, body
    else:
       
        exit()


def compressImage(source, path):
    webroot_path = os.path.abspath(os.path.dirname(__file__))
    destination = os.path.join(webroot_path, path)

    image = Image.open(source)
    image.save("compressed_image.jpg", optimize=True, quality=50)
    # Resize the image
    image.thumbnail((800, 800))
    image.save("resized_image.jpg")
    image.close()

    return image, destination


# def compressImage(source,path):
#     mime_type = mimetypes.guess_type(source)[0]
#     destination=''
#     if mime_type:
#         if mime_type == 'image/jpeg':
#             image=Image.open(source)
#             if hasattr(image, '_getexif'):
#                 exif = image._getexif()
#                 if exif is not None and 274 in exif:
#                     orientation = exif[274]
#                     if orientation == 3:
#                         image = image.rotate(180)
#                     elif orientation == 6:
#                         image = image.rotate(270)
#                     elif orientation == 8:
#                         image = image.rotate(90)

#         elif mime_type == 'image/gif':
#             image=


def get_event_detail(db, event_id, login_user_id):
    event = {}
    event_details = db.query(Events).filter(Events.id == event_id).first()
    if event_details:
       
        event.update(
            {
                "event_id": event_details.id,
                "type": event_details.type if event_details.type else "",
                "event_name": event_details.title if event_details.title else "",
                "reference_id": event_details.ref_id if event_details.ref_id else "",
                "chime_meeting_id":event_details.chime_meeting_id if event_details.chime_meeting_id else "",
                "message": event_details.description
                if event_details.description
                else "",
                "event_type_id": event_details.event_type_id
                if event_details.event_type_id
                else "",
                "event_layout_id": event_details.event_layout_id
                if event_details.event_layout_id
                else "",
                "no_of_participants": event_details.no_of_participants
                if event_details.no_of_participants
                else "",
                "duration": event_details.duration if event_details.duration else "",
                "start_date_time": (
                        event_details.start_date_time
                        if event_details.start_date_time
                        else ""
                    )
                    if event_details.created_at
                    else "",
                "start_date": common_date(
                    ((event_details.start_date_time).date()), without_time=1
                )
                if event_details.start_date_time
                else "",
                "start_time": (event_details.start_date_time).time(),
                "is_host": 1 if event_details.created_by == login_user_id else 0,
                "banner_image": event_details.cover_img
                if event_details.cover_img
                else defaultimage("cover_img"),
                "created_at": common_date(event_details.created_at)
                if event_details.created_at
                else "",
                "original_user_name": event_details.user.display_name
                if event_details.created_by
                else "",
                "original_user_id": event_details.user.id
                if event_details.created_by
                else "",
                "original_user_image": event_details.user.profile_img
                if event_details.created_by
                else "",
                "event_melody_id": event_details.event_melody_id
                if event_details.event_melody_id
                else "",
                "waiting_room": event_details.waiting_room
                if event_details.waiting_room != None
                else 0,
                "join_before_host": event_details.join_before_host
                if event_details.join_before_host != None
                or event_details.join_before_host != ""
                else 0,
                "sound_notify": event_details.sound_notify
                if event_details.sound_notify != None
                or event_details.sound_notify != ""
                else 0,
                "user_screenshare": event_details.user_screenshare
                if event_details.user_screenshare != None
                else 0
            }
        )
        default_melody = (
            db.query(EventMelody).filter_by(id=event_details.event_melody_id).first()
        )
        event.update({"event_melody_type":(1 if "Rawcaster Melody" in default_melody.title else 2 if "Your default" in default_melody.title else 3) if default_melody and default_melody.title else 3})
        
        if default_melody:
            
            event.update({"melodies": {
                        "path": default_melody.path if default_melody.path else None,
                        "type": default_melody.type if default_melody.type else None,
                        "is_default": default_melody.event_id
                        if default_melody.event_id
                        else None,
                    }})

        get_event_default_avs = (
            db.query(EventDefaultAv).filter_by(event_id=event_details.id).all()
        )
        if get_event_default_avs:
            for defaultav in get_event_default_avs:
                event.update(
                    {
                        "default_host_audio": defaultav.default_host_audio,
                        "default_host_video": defaultav.default_host_video,
                        "default_guest_audio": defaultav.default_guest_audio,
                        "default_guest_video": defaultav.default_guest_video,
                    }
                )
        event_invitations = db.query(EventInvitations).filter_by(event_id=event_id, status=1).all()
        
        invite_groups_id = []
        invite_friends_id = []
        invite_mails = []
        if event_invitations:
            for invite in event_invitations:
                if invite.type == 1:
                    invite_friends_id.append(invite.user_id)
                elif invite.type == 2:
                    invite_groups_id.append(invite.group_id)

                elif invite.type == 3:
                    if invite.invite_mail != "":
                        invite_mails.append(invite.invite_mail)
                        
            event.update(
                {
                    "invite_groups_id": invite_groups_id,
                    "invite_friends_id": invite_friends_id,
                    "invite_mails": invite_mails,
                }
            )
    return event


def detect_and_remove_offensive(text):
    pf = ProfanityFilter()
    cleaned_text = pf.censor(text)
    return cleaned_text


def defaultimage(flag):
    url = ""
    if flag == "profile_img":
        url="https://rawcaster.s3.us-west-2.amazonaws.com/profile_image/image_1695442761.png"
        # url = "https://rawcaster.s3.us-west-2.amazonaws.com/profileimage/Image_94081682594499.png"

    elif flag == "cover_img":
        url = "https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_31531698906317.png"
        # url = "https://rawcaster.s3.us-west-2.amazonaws.com/profileimage/image_1688517947.png"

    elif flag == "group_icon":
        url = "https://rawcaster.s3.us-west-2.amazonaws.com/chat/attachment_91971683678695.jpg"

    elif flag == "event_banner":
        url = "https://rawcaster.s3.us-west-2.amazonaws.com/chat/attachment_86991683760798.jpg"

    elif flag == "talkshow":
        url = "https://rawcaster.s3.us-west-2.amazonaws.com/chat/attachment_81511683760885.jpg"

    elif flag == "live":
        url = "https://rawcaster.s3.us-west-2.amazonaws.com/profileimage/image_1688518042.jpg"

    return url


def GetGroupDetails(db, user_id, id):  # Id -Group ID
    members = []
    memberlist = []
    my_group=1
    
    friendGroup = (
        db.query(FriendGroups)
        .filter(FriendGroups.status == 1, FriendGroups.id == id)
        .first()
    )
    if friendGroup:
        friendGroupMember = db.query(FriendGroupMembers).filter(
            FriendGroupMembers.group_id == friendGroup.id
        )

        friendGroupMembers = friendGroupMember.all()
        friend_group_count = friendGroupMember.count()

        members.append(friendGroup.created_by)
        # Group_category
        group_category = None
        if friendGroup.group_name == "My Fans":
            group_category = 1
        if friendGroup.group_name == "My Fans" and friendGroup.created_by != user_id:
            group_category = 2
            my_group=0
        if friendGroup.created_by == user_id and friendGroup.group_name != "My Fans":
            group_category = 3

        memberlist.append(
            {
                "user_id": friendGroup.created_by if friendGroup.created_by else "",
                "member_arn": friendGroup.user.chime_user_id
                if friendGroup.created_by
                else "",
                "email_id": friendGroup.user.email_id if friendGroup.created_by else "",
                "first_name": friendGroup.user.first_name
                if friendGroup.created_by
                else "",
                "last_name": friendGroup.user.last_name
                if friendGroup.created_by
                else "",
                "display_name": friendGroup.user.display_name
                if friendGroup.created_by
                else "",
                "gender": friendGroup.user.gender if friendGroup.created_by else "",
                "profile_img": friendGroup.user.profile_img
                if friendGroup.created_by
                else "",
            }
        )

        if friendGroupMembers:
            for frnd_group in friendGroupMembers:
                members.append(frnd_group.user_id)

                memberlist.append(
                    {
                        "user_id": frnd_group.user_id if frnd_group.user_id else "",
                        "member_arn": frnd_group.user.chime_user_id
                        if frnd_group.user.chime_user_id
                        else "",
                        "email_id": frnd_group.user.email_id
                        if frnd_group.user_id
                        else "",
                        "first_name": frnd_group.user.first_name
                        if frnd_group.user_id
                        else "",
                        "last_name": frnd_group.user.last_name
                        if frnd_group.user_id
                        else "",
                        "display_name": frnd_group.user.display_name
                        if frnd_group.user_id
                        else "",
                        "gender": frnd_group.user.gender if frnd_group.user_id else "",
                        "profile_img": frnd_group.user.profile_img
                        if frnd_group.user_id
                        else "",
                        "last_seen": frnd_group.user.last_seen
                        if frnd_group.user_id
                        else "",
                        "online": "",
                        "typing": 0,
                    }
                )
         # Generate URl
        token_text=f"{friendGroup.user.user_ref_id}//{datetime.datetime.utcnow().replace(tzinfo=None)}//{friendGroup.id}"
        user_ref_id = token_text.encode("ascii")
        
        hashed_user_ref_id = (base64.b64encode(user_ref_id)).decode("ascii")
        
        invite_url = inviteBaseurl()
        join_link = f"{invite_url}signup?ref={hashed_user_ref_id}"
       
        group_details = {
            "group_id": friendGroup.id,
            "group_name": friendGroup.group_name,
            "channel_arn": friendGroup.group_arn if friendGroup.group_arn else None,
            "group_icon": friendGroup.group_icon,
            "group_member_count": friend_group_count,
            "group_owner": friendGroup.created_by,
            "chat_enabled": friendGroup.chat_enabled,
            "group_type": 1,
            "group_category": group_category if group_category else 3,
            "group_member_ids": members,
            "group_members_list": memberlist,
            "typing": 0,
            "my_group":my_group,
            "referral_link":join_link
        }
        return group_details


def paginate(page, size, data, total):
    reply = {"items": data, "total": total, "page": page, "size": size}
    return reply


async def SendOtp(db, user_id, signup_type):
    # Send OTP for Email or MObile number Verification
    otp = generateOTP()
    otp_time = datetime.datetime.utcnow()

    check_user_otp_log = (
        db.query(OtpLog)
        .filter(OtpLog.user_id == user_id)
        .order_by(OtpLog.id.desc())
        .first()
    )

    if check_user_otp_log:
        check_user_otp_log.otp = otp
        check_user_otp_log.created_date = otp_time
        check_user_otp_log.status = 1

        db.commit()
        otp_ref_id = check_user_otp_log.id

    else:
        add_otp_to_log = OtpLog(
            otp_type=1,  # SignUp
            user_id=user_id,
            otp=otp,
            created_at=otp_time,
            status=1,
        )
        db.add(add_otp_to_log)
        db.commit()
        db.refresh(add_otp_to_log)

        otp_ref_id = add_otp_to_log.id

    # Generate Token

    get_user = db.query(User).filter(User.id == user_id).first()
    to_mail = get_user.email_id
    base_url = inviteBaseurl()
    code = EncryptandDecrypt(str(otp))
    link = f"{base_url}rawadmin/site/accountverify?hash={code}"

    subject = "Rawcaster - Verify OTP"

    content = ""
    content += "<table width='600' border='0' align='center' cellpadding='10' cellspacing='0' style='border: 1px solid #e8e8e8;'><tr><td> "
    content += "Hi, Greetings from Rawcaster<br /><br />"
    content += (
        f"Your OTP for Rawcaster account verification is : <b> {otp } </b><br /><br />"
    )
    # content += 'Click this link to validate your account '
    # content += (
    #         f"Click this link to validate your account {link} <br /><br />"
    #                 )
    content += 'Regards,<br />Administration Team<br /><a href="https://rawcaster.com/">Rawcaster.com</a> LLC'
    content += "</td></tr></table>"

    body = mail_content(content)
    
    if int(signup_type) == 1:
        try:
            mail_send = await send_email(db, to_mail, subject, body)
        except Exception as e:
            print(e)
            
    elif int(signup_type) == 2:
        mobile_no = f"{get_user.country_code}{get_user.mobile_no}"
        message = f"{otp} is your OTP for Rawcaster. PLEASE DO NOT SHARE THE OTP WITH ANYONE. 0FfsYZmYTkk"
        try:
            send_sms = sendSMS(mobile_no, message)
        except Exception as e:
            print(e)
    else:
        pass
    return otp_ref_id


def ProfilePreference(db, myid, otherid, field, value):
    settings = db.query(UserSettings).filter(UserSettings.user_id == otherid).first()
    if hasattr(settings, field):
        if getattr(settings, field) == 0:
            return ""

        elif getattr(settings, field) == 1:
            return value

        elif getattr(settings, field) == 2:
            if FriendsandGroupPermission(db, myid, otherid, 1):
                return value
            else:
                return ""

        elif getattr(settings, field) == 3:
            lists = []
            online_group_list = (
                db.query(UserProfileDisplayGroup.groupid)
                .filter(
                    UserProfileDisplayGroup.user_id == otherid,
                    UserProfileDisplayGroup.profile_id == field,
                )
                .all()
            )
            if online_group_list:
                for group_list in online_group_list:
                    lists.append(group_list)
            if len(lists) > 0:
                if FriendsandGroupPermission(db, myid, lists, 2):
                    return value
                else:
                    return ""
            else:
                return ""

    else:
        return value


def FriendsandGroupPermission(db, myid, friendid, flag=1):
    reply = False
    if flag == 1:
        query = db.query(MyFriends)
        query = query.filter_by(status=1)
        query = query.filter_by(request_status=1)
        query = query.filter(
            or_(
                (
                    and_(
                        (MyFriends.sender_id == myid),
                        (MyFriends.receiver_id == friendid),
                    )
                ),
                (
                    and_(
                        (MyFriends.sender_id == friendid),
                        (MyFriends.receiver_id == myid),
                    )
                ),
            )
        )
        get_friend_requests = query.first()

        if get_friend_requests:
            return True
    else:
        query = db.query(FriendGroupMembers)
        query = query.filter_by(user_id=myid)
        query = query.filter(FriendGroupMembers.group_id.in_(friendid))

        # get count
        groupmember = query.count()
        if groupmember > 0:
            reply = True
    return reply


def eventPostNotifcationEmail(db, eventId):
    if eventId != None and eventId != "":
        to = ""
        subject = ""
        body = ""
        phone = ""
        event = db.query(Events).filter_by(id=eventId, status=1).first()
        if event:
            # eventInvitations = event.eventInvitations
            coverImg = event.cover_img
            eventTitle = event.title
            event_start_time = event.start_date_time
            eventStartTime = datetime.datetime.strptime(
                str(event_start_time), "%Y-%m-%d %H:%M:%S"
            ).strftime("%-d %b %Y %-I:%M %p")
            subject = "New Event Created"
            meetingUrl = inviteBaseurl() + "joinmeeting/" + event.ref_id
            eventCreatorName = event.user.display_name if event.created_by else None
            sms_message = f"Hi,{eventCreatorName} is inviting you to join a web event called {eventTitle}. The link for this Rawcaster event is: {meetingUrl}"

            body = event_shared(
                eventCreatorName, coverImg, eventTitle, eventStartTime, meetingUrl
            )
            return (sms_message, body)


def GenerateUserRegID(id):
    dt = str(int(datetime.datetime.utcnow().timestamp()))

    refid = "RA" + str(id) + str(dt) + str(random.randint(10000, 50000))
    return refid


def GetRawcasterUserID(db, type):
    if type == 2:
        email = "helpdesk@rawcaster.com"
    else:
        email = "helpdesk@rawcaster.com"

    get_user = db.query(User).filter(User.email_id == email, User.status == 1).first()
    if get_user:
        return get_user.id
    else:
        return 0


# Update Default Langugae
def updateDefaultLangugae(db,user_id):
    getUserSettings=db.query(UserSettings).filter(UserSettings.user_id == user_id,UserSettings.read_out_language_id == None).first()
    if getUserSettings:
        getUserSettings.read_out_language_id = 27
        getUserSettings.read_out_accent_id= 1
        db.commit()

async def logins(
    db,
    username,
    password,
    device_type,
    device_id,
    push_id,
    login_from,
    voip_token,
    app_type,
    social,
    ip=None
):
    username = username.strip() if username else None

    get_user = (
        db.query(User)
        .filter(
            or_(
                getattr(User, "email_id").like(username),
                getattr(User, "mobile_no").like(username),
            ),
            or_(getattr(User, "email_id") != None, getattr(User, "mobile_no") != None),
        ).order_by(User.id.desc())
        .first()
    )

    if get_user == None or not get_user:        # Invalid User
        type = EmailorMobileNoValidation(username)

        if type["status"] and type["status"] == 1:
            return {
                "status": 2,
                "type": type["type"],
                "msg": "Login Failed. Invalid email id or password.",
            }
        else:
            return {"status": 0, "msg": "Login Failed. Invalid email id or password.."}

    elif get_user.status == 0 and social != 1:                  # Verification Pending
        signup_type = 1 if get_user.email_id else 2
        user_id = get_user.id
        send_otp = await SendOtp(db, user_id, signup_type)

        characters = "".join(random.choices(string.ascii_letters + string.digits, k = 8))
        token_text = ""
        dt = str(int(datetime.datetime.utcnow().timestamp()))

        salt_token = token_text + str(user_id) + str(characters) + str(dt)

        userIP = ip

        add_token = ApiTokens(
            user_id=user_id,
            token=salt_token,
            created_at=datetime.datetime.utcnow(),
            renewed_at=datetime.datetime.utcnow(),
            validity=1,
            device_type=login_from,
            app_type=app_type,
            device_id=device_id,
            push_device_id=push_id,
            voip_token=voip_token,
            device_ip=userIP,
            status=1,
        )
        db.add(add_token)
        db.commit()
        db.refresh(add_token)

        return {
            "status": 1,
            "acc_verify_status": 0,
            "alt_token_id": add_token.id,
            "otp_ref_id": send_otp,
            "msg": "Verification Pending, Redirect to OTP Verify Page",
            "first_time": 1,
            "email_id": username,
            "signup_type": get_user.signup_type,
            "remaining_seconds": 90,
        }

    elif get_user.password != password and social != 1:     #  Invalid password
        if get_user.status == 2:                            #  2- Suspended
            return {"status": 0, "msg": "Your account is currently blocked!"}
        else:
            userIP = ip
            add_failure_login = LoginFailureLog(
                user_id=get_user.id,
                ip=userIP,
                create_at=datetime.datetime.utcnow(),
                status=1,
            )
            db.add(add_failure_login)
            db.commit()

            get_settings = (
                db.query(Settings.settings_value)
                .filter(Settings.settings_topic == "login_block_time")
                .first()
            )
            if get_settings:
                total_block_dur = get_settings.settings_value if get_settings.settings_value else 0
                curretTime = datetime.datetime.utcnow() - timedelta(
                    minutes=int(total_block_dur)
                )

            else:
                total_block_dur = 30
                curretTime = datetime.datetime.utcnow() - timedelta(minutes=30)

                failure_count = (
                    db.query(LoginFailureLog)
                    .filter(
                        LoginFailureLog.user_id == get_user.id,
                        LoginFailureLog.create_at > curretTime,
                    )
                    .count()
                )

                if failure_count > 2:
                    msg = ""
                    if int(total_block_dur) < 60:
                        msg = f"{total_block_dur} minutes"
                    elif int(total_block_dur) == 60:
                        msg = "1 hour"
                    elif int(total_block_dur) > 60:
                        msg = f"{math.floor(total_block_dur/60)} hours {total_block_dur % 60} minutes"

                    return {
                        "status": 0,
                        "msg": f"Your account is currently blocked. Please try again after {msg}",
                    }

        return {"status": 0, "msg": "Login Failed. invalid email id or password"}

    elif get_user.status == 4:  # Account deleted
        return {"status": 0, "msg": "Your account has been removed"}

    elif get_user.status == 3:  # Admin Blocked user!
        return {"status": 0, "msg": "Your account has been removed"}

    elif get_user.status == 2:  # admin suspended user!
        return {"status": 0, "msg": "Your account is currently blocked!"}

    elif get_user.admin_verified_status != 1:  # Admin has to verify!
        return {
            "status": 0,
            "msg": "This is a beta version of Rawcaster. We are allowing limited number of users at the moment. Your account is currently undergoing an approval process by the administrator. Try to logon again later or contact the Rawcaster personnel that requested your participation in the beta program.",
        }
    else:
        get_failur_login = (
            db.query(LoginFailureLog)
            .filter(LoginFailureLog.user_id == get_user.id)
            .delete()
        )
        db.commit()
        
        user_id = get_user.id
        characters = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        token_text = ""
        dt = int(datetime.datetime.utcnow().timestamp())

        token_text = token_text + str(user_id) + str(characters) + str(dt)

        if login_from == 2:
            delete_token = (
                db.query(ApiTokens)
                .filter(ApiTokens.user_id == user_id, ApiTokens.device_type == 2)
                .delete()
            )
            db.commit()
        if login_from == 1:
            delete_token = (
                db.query(ApiTokens)
                .filter(ApiTokens.user_id == user_id, ApiTokens.device_type == 1)
                .delete()
            )
            db.commit()

        salt_token = token_text
        
        userIP = ip

        add_token = ApiTokens(
            user_id=user_id,
            token=token_text,
            created_at=datetime.datetime.utcnow(),
            renewed_at=datetime.datetime.utcnow(),
            validity=1,
            device_type=login_from,
            app_type=app_type,
            device_id=device_id,
            push_device_id=push_id,
            voip_token=voip_token,
            device_ip=userIP,
            status=1,
        )
        db.add(add_token)
        db.commit()

        if add_token:
            exptime = int(dt) + int(dt)

            name = get_user.display_name
            profile_image = get_user.profile_img if get_user.profile_img else None
            salt = st.SALT_KEY
            hash_code = str(token_text) + str(salt)

            new_auth_code = hashlib.sha1(hash_code.encode()).hexdigest()

            user_id = get_user.id
            paylod = {
                "iat": dt,
                "iss": "localhost",
                "exp": exptime,
                "token": token_text,
            }

            token_text = jwt.encode(paylod, st.SECRET_KEY)

            exptime = datetime.datetime.fromtimestamp(int(exptime))
            if login_from == 2:
                # Update Sender
                update_sender = (
                    db.query(FriendsChat)
                    .filter(FriendsChat.sender_id == user_id)
                    .update(
                        {
                            "sender_delete": 1,
                            "sender_deleted_datetime": datetime.datetime.utcnow(),
                        }
                    )
                    .all()
                )
                update_recevicr = (
                    db.query(FriendsChat)
                    .filter(FriendsChat.receiver_id == user_id)
                    .update(
                        {
                            "receiver_delete": 1,
                            "receiver_deleted_datetime": datetime.datetime.utcnow(),
                        }
                    )
                    .all()
                )
                db.commit()

            if get_user.referral_expiry_date != None and get_user.user_status_id == 3:
                if datetime.datetime.utcnow() >= get_user.referral_expiry_date:
                    update_user = (
                        db.query(User)
                        .filter(User.id == get_user.id)
                        .update({"user_status_id": 1, "referral_expiry_date": None})
                    )
                    db.commit()

            # Check Existing user first time sign
            existing_user = 0
            if get_user.existing_user == 1:
                existing_user = 1
            # update existing user flag
            get_user.existing_user = 0
            db.commit()

            # Chime Chat User Create

            check_chat_id = get_user.chime_user_id if get_user.chime_user_id else None
            if not check_chat_id:
                try:
                    create_chat_user = chime_chat.createchimeuser(get_user.email_id)
                except Exception as e:
                    print(f'Chime User:{e}')
                    
                if create_chat_user["status"] == 1:
                    check_chat_id = create_chat_user["data"]["ChimeAppInstanceUserArn"]
                    # Update User Chime ID
                    update_user = (
                        db.query(User)
                        .filter(User.id == get_user.id)
                        .update({"chime_user_id": check_chat_id})
                    )
                    db.commit()
            
            # Verify Account
            if social == 1:
                get_user.is_email_id_verified = 1
                get_user.status= 1
                db.commit()

            updateUserLanguage=updateDefaultLangugae(db,get_user.id)

            return {
                "status": 1,
                "msg": "Success",
                "salt_token": salt_token,
                "token": token_text,
                "email_id": username,
                "expirytime": common_date(exptime),
                "profile_image": profile_image,
                "name": name,
                "user_id": user_id,
                "authcode": new_auth_code,
                "acc_verify_status": get_user.is_email_id_verified if get_user.signup_type == 1 else  get_user.is_mobile_no_verified if get_user.signup_type == 2 else None,
                "signup_type": get_user.signup_type,
                "first_time": 1, # existing_user   ( Existing user first time login - goto influencer page)
                "chime_user_id": check_chat_id,
            }
        else:
            return {"status": 0, "msg": "Failed to Generate Access Token. try again"}


def getModelError(errors):
    if errors != "" or errors != None:
        reply = ""
        for err in errors:
            if err != "" and err != None:
                reply = err

        return reply


def ChangeReferralExpiryDate(db, referrerid):
    referrer = db.query(User).filter(User.id == referrerid).first()
    if referrer:
        expiry_date = referrer.referral_expiry_date
        user_status_id = referrer.user_status_id
        if referrer.user_status_id == 1:
            user_status = (
                db.query(UserStatusMaster).filter(UserStatusMaster.id == 3).first()
            )
            if user_status:
                total_referral_point = int(referrer.total_referral_point) + 1
                if user_status.referral_needed <= total_referral_point:
                    expiry_date = datetime.datetime.utcnow()
                    if referrer.referral_expiry_date != None:
                        expiry_date = referrer.referral_expiry_date
                    expiry_date = datetime.datetime.utcnow() + relativedelta(months=1)

                    total_referral_point = (
                        total_referral_point - user_status.referral_needed
                    )
                    user_status_id = 3

        else:
            total_referral_point = referrer.total_referral_point + 1

        update_user = (
            db.query(User)
            .filter(User.id == referrer.id)
            .update(
                {
                    "user_status_id": user_status_id,
                    "referral_expiry_date": expiry_date,
                    "total_referral_point": total_referral_point,
                }
            )
        )
        db.commit()


def removeZeroFromNumber(mobile_no):
    mobile_no=mobile_no.lstrip('0')
    return mobile_no
    

def checkToken(db, access_token):
    try:
        access_token = access_token.strip()
        payload = jwt.decode(access_token, st.SECRET_KEY, algorithms=["HS256"])

        if payload != "" or payload != None:
            access_token = payload["token"]
            get_token_details = (
                db.query(ApiTokens)
                .filter(ApiTokens.status == 1, ApiTokens.token == access_token)
                .first()
            )
            if not get_token_details:
                return False
            current_time = int(datetime.datetime.utcnow().timestamp())

            last_request_time = int(round((get_token_details.renewed_at).timestamp()))
            if last_request_time + 604800 < current_time:
                get_token_details.status = -1
                db.commit()
                return False
            
            elif get_token_details.user.status == 2:
                return False

            else:
                get_token_details.renewed_at = datetime.datetime.utcnow()
                db.commit()
                return access_token

        else:
            return False
    except:
        return False


def EventAccessCheck(db, userid, eventid):
    status = 0
    user = db.query(User).filter_by(id=userid).first()
    if user:
        event = db.query(Events).filter_by(id=eventid).first()
        if event:
            if event.created_by == userid:  # created by $userid
                status = 1
            elif event.event_type_id == 1:  # Public event
                status = 1

            elif event.event_type_id == 2:  # Private event
                invited = (
                    db.query(EventInvitations)
                    .filter_by(event_id=eventid, user_id=userid)
                    .first()
                )
                if invited:
                    status = 1
                criteria = db.query(EventInvitations).filter_by(
                    event_id=eventid, status=1
                )
                criteria.join(
                    FriendGroupMembers,
                    EventInvitations.group_id == FriendGroupMembers.group_id
                    and FriendGroupMembers.user_id == userid,
                )
                invited = criteria.first()
                if invited:
                    status = 1
                invited = db.query(EventInvitations).filter_by(
                    event_id=eventid, invite_mail=user.email_id
                )
                if invited:
                    status = 1
            elif event.event_type_id == 3:
                follow = (
                    db.query(FollowUser)
                    .filter_by(
                        follower_userid=userid, following_userid=event.created_by
                    )
                    .first()
                )
                if follow:
                    status = 1

    if status == 1:
        return True
    else:
        return False


def generateOTP():
    return random.randint( 100000,999999)
    # return 123456



def is_valid_url(input_str):
    try:
        result = urlparse(input_str)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def textTOAudio(text,target_language,accent):
   
    try:
        tts = gTTS(text,lang=target_language,tld='com')
    except:
        return {"status":0,"msg":"Unable to translate to audio"}  

    base_dir = "rawcaster_uploads"

    try:
        os.makedirs(base_dir, mode=0o777, exist_ok=True)
    except OSError as e:
        sys.exit(
            "Can't create {dir}: {err}".format(dir=base_dir, err=e)
        )

    output_dir = base_dir + "/"

    filename = f"converted_{int(datetime.datetime.now().timestamp())}.mp3"

    save_full_path = f"{output_dir}{filename}"
    # Save the speech as an MP3 file
    try:
        tts.save(save_full_path)
    except Exception as e:
        print(e)
        return {"status":0,"msg":"Unable to translate"}  

    s3_file_path = f"nuggets/converted_audio_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}.mp3"

    result = upload_to_s3(save_full_path, s3_file_path)

    if result["status"] == 1:
        return {
            "status": 1,
            "msg": "success",
            "file_path": result["url"],
            "url": result["url"]
        }
    else:
        return {"status":0,"msg":"Unable to convert"}

#   --------------------------------------------------
# def file_storage(file):

#     base_dir = st.BASE_UPLOAD_FOLDER+"/upload_files/"

#     dt = str(int(datetime.utcnow().timestamp()))

#     try:
#         os.makedirs(base_dir, mode=0o777, exist_ok=True)
#     except OSError as e:
#         sys.exit("Can'Nuggets create {dir}: {err}".format(
#             dir=base_dir, err=e))

#     filename=file.filename

#     file_properties = filename.split(".")

#     file_extension = file_properties[-1]

#     file_properties.pop()
#     file_splitted_name = file_properties[0]


#     write_path = f"{base_dir}{file_splitted_name}{dt}.{file_extension}"
#     db_path = f"/upload_files/{file_splitted_name}{dt}.{file_extension}"

#     with open(write_path, "wb") as new_file:
#         shutil.copyfileobj(file.file, new_file)

#     return db_path


# def common_date_only(date, without_time=None):

#     datetime = date.strftime("%d-%m-%y")

#     if without_time == 1:
#         datetime = date.strftime("%d-%m-%y")

#     return datetime
# def common_time_only(date, without_time=None):

#     datetime = date.strftime("%H:%M:%S")

#     return datetime

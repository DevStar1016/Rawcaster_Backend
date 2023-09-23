from fastapi import APIRouter, Depends, Form, File, UploadFile
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import datetime
from typing import List
from app.core import config
import openai
import json
from pydub import AudioSegment
from gtts import gTTS
import pyttsx3
import googletrans

router = APIRouter()


access_key = config.access_key
access_secret = config.access_secret
bucket_name = config.bucket_name


# 85 Event Abuse Report


@router.post("/addeventabusereport")
async def add_event_abuse_report(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    event_id: str = Form(None),
    message: str = Form(None),
    attachment: UploadFile = File(None),
):
    if token == None or token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."} 
    
    elif event_id == None or not event_id.isnumeric():
        return {"status": 0, "msg": "Event id is missing"}

    elif message == None:
        return {"status": 0, "msg": "Message Cant be Blank"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            event_id = int(event_id)
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id if get_token_details else None

            # Add Abuse Report
            check_event = (
                db.query(Events)
                .filter(Events.id == event_id, Events.status == 1)
                .first()
            )

            if check_event:
                add_abuse_report = EventAbuseReport(
                    event_id=event_id,
                    user_id=login_user_id,
                    message=message,
                    created_at=datetime.utcnow(),
                    status=0,
                )
                db.add(add_abuse_report)
                db.commit()
                db.refresh(add_abuse_report)

                if attachment:
                    file_name = attachment.filename
                    # file_temp=attachment.content_type
                    # file_size=len(await attachment.read())
                    file_ext = os.path.splitext(attachment.filename)[1]
                    file_extensions = [".jpg", ".png", ".jpeg"]

                    if file_ext in file_extensions:
                        try:
                            s3_path = f"events/image_{random.randint(11111,99999)}{int(datetime.utcnow().timestamp())}{file_ext}"
                            uploaded_file_path = file_upload(attachment, compress=None)

                            result = upload_to_s3(uploaded_file_path, s3_path)
                            # Upload to S3
                            if result["status"] == 1:
                                add_abuse_report.attachment = result["url"]
                                add_abuse_report.status = 1

                                db.commit()
                                return {"status": 1, "msg": "Success"}
                            else:
                                return result
                        except Exception as e:
                            print(e)
                            return {"status": 0, "msg": "Unable to Upload File"}

                    else:
                        return {"status": 0, "msg": "Accepted only jpg,png,jpeg"}

                # Update Event Absue Report

                add_abuse_report.status = 1
                db.commit()
                return {"status": 1, "msg": "Success"}
            else:
                return {"status": 0, "msg": "Invalid Event ID"}


# CRON
@router.post("/croninfluencemember")
async def croninfluencemember(
    db: Session = Depends(deps.get_db), user_id: int = Form(None)
):
    if user_id:
        get_user_details = (
            db.query(User).filter(User.id == user_id, User.status == 1).all()
        )
    else:
        get_user_details = db.query(User).filter(User.status == 1).all()

    for usr in get_user_details:
        get_follow_user = (
            db.query(FollowUser)
            .filter(FollowUser.follower_userid == usr.id, FollowUser.status == 1)
            .count()
        )

        if get_follow_user:
            user_status_master = (
                db.query(UserStatusMaster)
                .filter(
                    UserStatusMaster.min_membership_count <= get_follow_user,
                    or_(
                        UserStatusMaster.max_membership_count >= get_follow_user,
                        UserStatusMaster.max_membership_count == None,
                    ),
                )
                .first()
            )

            if user_status_master:
                usr.user_status_id = user_status_master.id
                db.commit()
                return "Done"


# 86  Add Claim Account
@router.post("/addclaimaccount")
async def add_claim_account(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    influencer_id: str = Form(None),
    first_name: str = Form(None),
    last_name: str = Form(None),
    telephone: str = Form(None),
    email_id: str = Form(None),
    dob: str = Form(None),
    location: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif influencer_id == None or not influencer_id.isnumeric():
        return {"status": 0, "msg": "Influence id is missing"}

    elif first_name == None:
        return {"status": 0, "msg": "First Name Cant be Blank"}

    elif email_id == None:
        return {"status": 0, "msg": "Email Cant be Blank"}

    elif dob and is_date(dob) == False:
        return {"status": 0, "msg": "Invalid Date"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id if get_token_details else None
            # Check requests
            check_requests = (
                db.query(ClaimAccounts)
                .filter(
                    ClaimAccounts.user_id == login_user_id,
                    ClaimAccounts.influencer_id == influencer_id,
                )
                .first()
            )
            if not check_requests:
                add_clain = ClaimAccounts(
                    user_id=login_user_id,
                    influencer_id=influencer_id,
                    first_name=first_name.strip(),
                    dob=dob,
                    last_name=last_name,
                    location=location,
                    telephone=telephone,
                    email_id=email_id,
                    claim_date=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    status=1,
                    admin_status=0,
                )
                db.add(add_clain)
                db.commit()
                return {
                    "status": 1,
                    "msg": "You have placed a claim on a predefined influencer profile, We will contact you to validate your claim. Please contact us at info@rawcaster.com if you have any questions.",
                }
            else:
                return {"status": 0, "msg": "Already sent"}


# 86  List UnClaim Account
@router.post("/listunclaimaccount")
async def listunclaimaccount(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    location: str = Form(None),
    gender: str = Form(None),
    age: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if gender and not gender.isnumeric():
        return {"status": 0, "msg": "Invalid Gender type"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id if get_token_details else None

            get_unclaimed_account = (
                db.query(User)
                .join(
                    UserStatusMaster,
                    User.user_status_id == UserStatusMaster.id,
                    isouter=True,
                )
                .filter(User.created_by == 1, UserStatusMaster.type == 2)
            )
            if location:
                get_unclaimed_account = get_unclaimed_account.filter(
                    User.geo_location.ilike("%" + location + "%")
                )
            if gender:
                get_unclaimed_account = get_unclaimed_account.filter(
                    User.geo_location == gender
                )
            if age:
                if not age.isnumeric():
                    return {"status": 0, "msg": "Invalid Age"}
                else:
                    current_year = datetime.utcnow().year
                    get_unclaimed_account = get_unclaimed_account.filter(
                        current_year - extract("year", User.dob) == age
                    )

            unclaimed_accounts = []
            get_unclaimed_account = get_unclaimed_account.all()

            for unclaim in get_unclaimed_account:
                check_claim_account = (
                    db.query(ClaimAccounts)
                    .filter(
                        ClaimAccounts.user_id == login_user_id,
                        ClaimAccounts.influencer_id == unclaim.id,
                    )
                    .first()
                )

                unclaimed_accounts.append(
                    {
                        "user_id": unclaim.id,
                        "email_id": unclaim.email_id if unclaim.email_id else "",
                        "display_name": unclaim.display_name
                        if unclaim.display_name
                        else "",
                        "first_name": unclaim.first_name if unclaim.first_name else "",
                        "last_name": unclaim.last_name if unclaim.last_name else "",
                        "dob": unclaim.dob if unclaim.dob else "",
                        "mobile_no": unclaim.mobile_no if unclaim.mobile_no else "",
                        "location": unclaim.geo_location
                        if unclaim.geo_location
                        else "",
                        "profile_img": unclaim.profile_img
                        if unclaim.profile_img
                        else "",
                        "unclaimed_status": 1 if check_claim_account else 0,
                    }
                )

            return {
                "status": 1,
                "msg": "Success",
                "unclaim_accounts": unclaimed_accounts,
            }


# 87  Influencer Chat
@router.post("/influencerchat")
async def influencerchat(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    type: str = Form(None, description="1-text,2-image,3-audio,4-video"),
    message: str = Form(None),
    attachment: List[UploadFile] = File(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif type == None:
        return {"status": 0, "msg": "Type is missing"}

    elif type == 1 and (message == None or message.strip() == ""):
        return {"status": 0, "msg": "Message cant empty"}

    else:
        type = int(type)

        if not 1 <= type <= 5:
            return {"status": 0, "msg": "Check type"}

        if (type == 2 or type == 3 or type == 4 or type == 5) and not attachment:
            return {"status": 0, "msg": "File missing"}

        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id if get_token_details else None

            # Get Default Friend Group
            get_friend_group = (
                db.query(FriendGroups)
                .filter(
                    FriendGroups.created_by == login_user_id,
                    FriendGroups.status == 1,
                    FriendGroups.group_name == "My Fans",
                )
                .first()
            )
            if not get_friend_group:
                return {"status": 0, "msg": "Check Group"}
            else:
                file_type = [2, 3, 4, 5]
                content = []
                if type == 1:
                    content.append(message)

                elif type in file_type:
                    # if type == 2 or type == 5:
                    for attach in attachment:
                        file_ext = os.path.splitext(attach.filename)[1]

                        uploaded_file_path = file_upload(
                            attach, file_ext, compress=None
                        )
                        s3_file_path = f"Image_{random.randint(1111,9999)}{int(datetime.utcnow().timestamp())}{file_ext}"

                        result = upload_to_s3(uploaded_file_path, s3_file_path)
                        if result["status"] and result["status"] == 1:
                            content.append(result["url"])
                        else:
                            return result

                for msg in content:
                    # Add Group Chat
                    add_group_chat = GroupChat(
                        group_id=get_friend_group.id,
                        sender_id=login_user_id,
                        message=message if type == 1 else None,
                        path=msg if type != 1 else None,
                        type=type,
                        sent_datetime=datetime.utcnow(),
                        status=1,
                    )
                    db.add(add_group_chat)
                    db.commit()
                    db.refresh(add_group_chat)

                return {"status": 1, "msg": "Success"}


# 88  Verify Accounts Only Diamond Members
@router.post("/verifyaccount")
async def add_verify_account(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    first_name: str = Form(None),
    last_name: str = Form(None),
    telephone: str = Form(None),
    email_id: str = Form(None),
    dob: str = Form(None),
    location: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif first_name == None:
        return {"status": 0, "msg": "First Name Can't be Blank"}

    elif email_id == None:
        return {"status": 0, "msg": "Email Can't be Blank"}

    elif dob and is_date(dob) == False:
        return {"status": 0, "msg": "Invalid Date"}
    elif not telephone:
        return {"status": 0, "msg": "Mobile number can't be Blank"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id if get_token_details else None
            # Check Already requested
            get_accounts = (
                db.query(VerifyAccounts)
                .filter(VerifyAccounts.user_id == login_user_id)
                .first()
            )
            if not get_accounts:
                add_clain = VerifyAccounts(
                    user_id=login_user_id,
                    first_name=first_name.strip(),
                    dob=dob,
                    last_name=last_name,
                    location=location,
                    telephone=telephone,
                    email_id=email_id,
                    verify_date=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    status=1,
                    verify_status=0,
                )
                db.add(add_clain)
                db.commit()
                return {
                    "status": 1,
                    "msg": "We will contact you to validate your account verify. Please contact us at info@rawcaster.com if you have any questions.",
                }
            else:
                return {"status": 0, "msg": "you are already requested to verification"}


# 91 AI Chat
@router.post("/aichat")
async def aichat(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    user_query: str = Form(None),
    audio_file: UploadFile = File(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if user_query and len(user_query) > 100:
        return {"status": 0, "msg": "Content length must be less than 100"}

    access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        )
        user_name = get_token_details.user.display_name if get_token_details else None
        created_at = common_date(datetime.utcnow(), None)
        query = None
        if audio_file:
            file_ext = os.path.splitext(audio_file.filename)[1]

            uploaded_file_path = await file_upload(audio_file, file_ext, compress=1)
            # Get Duration of the File
            try:
                audio = AudioSegment.from_file(uploaded_file_path)
                duration_in_seconds = len(audio) / 1000
                if not duration_in_seconds < 120:
                    return {"status": 0, "msg": "Allowed only maximum 2 minutes"}
            except Exception as e:
                return {"status": 0, "msg": "Try again later..."}

            # Upload to S3
            s3_file_path = (
                f"nuggets/audio_{int(datetime.utcnow().timestamp())}{file_ext}"
            )

            result = upload_to_s3(uploaded_file_path, s3_file_path)

            if result["status"] == 1:
                try:
                    transcribe = boto3.client(
                        "transcribe",
                        aws_access_key_id=config.access_key,
                        aws_secret_access_key=config.access_secret,
                        region_name="us-west-2",
                    )

                    job_name = f"my_job_{int(datetime.utcnow().timestamp())}"

                    output_bucket = "rawcaster"
                    output_key = f"transcriptions/converted_text{int(datetime.utcnow().timestamp())}.json"
                    language_code = "en-US"  # Language code of the audio (e.g., en-US for US English)

                    response = transcribe.start_transcription_job(
                        TranscriptionJobName=job_name,
                        LanguageCode=language_code,
                        Media={"MediaFileUri": result["url"]},
                        OutputBucketName=output_bucket,
                        OutputKey=output_key,
                        Settings={
                            "ShowSpeakerLabels": True,
                            "MaxSpeakerLabels": 2,  # Set the expected number of speakers in the audio
                        },
                    )

                    while True:
                        response = transcribe.get_transcription_job(
                            TranscriptionJobName=job_name
                        )
                        status = response["TranscriptionJob"]["TranscriptionJobStatus"]

                        if status == "COMPLETED":
                            result_url = response["TranscriptionJob"]["Transcript"][
                                "TranscriptFileUri"
                            ]

                            # Download the result file
                            s3_client = boto3.client(
                                "s3",
                                aws_access_key_id=config.access_key,
                                aws_secret_access_key=config.access_secret,
                                region_name="us-west-2",
                            )

                            res = (
                                result_url.split("rawcaster/", 1)
                                if result_url
                                else None
                            )
                            splitString = res[1]

                            # Retrieve the JSON file object from S3
                            response = s3_client.get_object(
                                Bucket="rawcaster", Key=splitString
                            )

                            # Read the contents of the JSON file
                            json_data = response["Body"].read().decode("utf-8")
                            # Parse the JSON data
                            parsed_data = json.loads(json_data)

                            # Audio Content
                            query = parsed_data["results"]["transcripts"][0][
                                "transcript"
                            ]
                            break
                        if status == "FAILED":
                            return {"status": 0, "msg": "Unable to convert"}
                except Exception as e:
                    return {"status": 0, "msg": f"Something went wrong...Error:{e}"}

        else:
            query = user_query

        if query:
            try:
                openai.api_key = config.open_ai_key

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a chatbot"},
                        {"role": "user", "content": f"{query}"},
                    ],
                )

                result = ""
                if response:
                    for choice in response.choices:
                        result += choice.message.content

                    return {
                        "status": 1,
                        "type": 1 if audio_file else 0,
                        "query": detect_and_remove_offensive(query),
                        "msg": result,
                        "created_at": created_at,
                    }
                else:
                    return {"status": 0, "msg": "Failed to search"}
            except Exception as e:
                return {"status": 0, "msg": f"Try again later..{e}"}

        else:
            return {
                "status": 1,
                "msg": f"HI {user_name}, I am an Artificial Intelligence (AI), I can answer your question on anything. Speak or type your question here..",
                "created_at": created_at,
            }


# # 89  AI Response Text Audio


@router.post("/texttoaudio")
async def texttoaudio(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    message: str = Form(None),
):
    if not token:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    if not message:
        return {"status": 0, "msg": "Meaage can't be Empty"}

    access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        )
        login_user_id = get_token_details.user_id if get_token_details else None

        get_user_readout_language = (
            db.query(
                UserSettings.id.label("user_setting_id"),
                ReadOutLanguage.id.label("read_out_id"),
                ReadOutLanguage.language_code,
                ReadOutLanguage.language_with_country
            )
            .filter(
                UserSettings.user_id == login_user_id,
                ReadOutLanguage.id == UserSettings.read_out_language_id,
            )
            .first()
        )

        target_language = (
            get_user_readout_language.language_code
            if get_user_readout_language
            else "en"
        )
      
        
        text_content = message
            
        if text_content:
            translator = googletrans.Translator()
            translated = translator.translate(text_content, dest=target_language)   

            text=translated.text

            # Initialize the Polly client
            polly = boto3.client('polly',aws_access_key_id=config.access_key,
                                aws_secret_access_key=config.access_secret,region_name='us-east-1')

            voice_id = 'Joanna'

            # Request speech synthesis
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode=(get_user_readout_language.language_with_country 
                                if get_user_readout_language 
                                else "en-US")
            )
            base_dir = "rawcaster_uploads"

            try:
                os.makedirs(base_dir, mode=0o777, exist_ok=True)
            except OSError as e:
                sys.exit(
                    "Can't create {dir}: {err}".format(dir=base_dir, err=e)
                )

            output_dir = base_dir + "/"

            filename = f"converted_{int(datetime.now().timestamp())}.mp3"

            save_full_path = f"{output_dir}{filename}"
            # Save the speech as an MP3 file
            with open(save_full_path, 'wb') as file:
                file.write(response['AudioStream'].read())

            s3_file_path = f"nuggets/converted_ai_audio_{random.randint(1111,9999)}{int(datetime.utcnow().timestamp())}.mp3"

            result = upload_to_s3(save_full_path, s3_file_path)

            if result["status"] == 1:
                return {
                    "status": 1,
                    "url": result["url"]
                }
            else:
                return {"status":0,"msg":"Unable to convert"}
            


# Audio to Text
@router.post("/nuggetaudiotext")
async def nugget_audio_text(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: int = Form(None),
):
    if not token:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        )
        login_user_id = get_token_details.user_id if get_token_details else None

        get_nugget = (
            db.query(Nuggets.id, NuggetsAttachment.path)
            .filter(
                Nuggets.id == nugget_id,
                NuggetsAttachment.nugget_id == Nuggets.nuggets_id,
                NuggetsAttachment.status == 1,
                NuggetsAttachment.media_type == "audio",
            )
            .first()
        )

        if get_nugget:
            query = None
            get_user_readout_language = (
                db.query(
                    UserSettings.id.label("user_setting_id"),
                    ReadOutLanguage.id.label("read_out_id"),
                    ReadOutLanguage.language_code,
                )
                .filter(
                    UserSettings.user_id == login_user_id,
                    ReadOutLanguage.id == UserSettings.read_out_language_id,
                )
                .first()
            )

            target_language = (
                get_user_readout_language.language_code
                if get_user_readout_language
                else "en"
            )

            supported_language = [
                "ar-AE",
                "en-US",
                "en-IN",
                "es-MX",
                "en-ZA",
                "tr-TR",
                "ru-RU",
                "ro-RO",
                "pt-PT",
                "pl-PL",
                "nl-NL",
                "it-IT",
                "is-IS",
                "fr-FR",
                "fi-FI",
                "es-ES",
                "de-DE",
                "yue-CN",
                "ko-KR",
                "en-NZ",
                "en-GB-WLS",
                "hi-IN",
                "arb",
                "cy-GB",
                "cmn-CN",
                "da-DK",
                "en-AU",
                "pt-BR",
                "nb-NO",
                "sv-SE",
                "ja-JP",
                "es-US",
                "ca-ES",
                "fr-CA",
                "en-GB",
                "de-AT",
            ]
            matching_languages = [
                lang for lang in supported_language if lang.startswith(target_language)
            ]

            try:
                transcribe = boto3.client(
                    "transcribe",
                    aws_access_key_id=config.access_key,
                    aws_secret_access_key=config.access_secret,
                    region_name="us-west-2",
                )

                job_name = f"my_job_{int(datetime.utcnow().timestamp())}"

                output_bucket = "rawcaster"
                output_key = f"transcriptions/converted_text{int(datetime.utcnow().timestamp())}.json"

                response = transcribe.start_transcription_job(
                    TranscriptionJobName=job_name,
                    LanguageCode=matching_languages[0]
                    if matching_languages
                    else "en-IN",
                    Media={"MediaFileUri": get_nugget.path},
                    OutputBucketName=output_bucket,
                    OutputKey=output_key,
                    Settings={
                        "ShowSpeakerLabels": True,
                        "MaxSpeakerLabels": 2,  # Set the expected number of speakers in the audio
                    },
                )

                while True:
                    response = transcribe.get_transcription_job(
                        TranscriptionJobName=job_name
                    )
                    status = response["TranscriptionJob"]["TranscriptionJobStatus"]

                    if status == "COMPLETED":
                        result_url = response["TranscriptionJob"]["Transcript"][
                            "TranscriptFileUri"
                        ]

                        # Download the result file
                        s3_client = boto3.client(
                            "s3",
                            aws_access_key_id=config.access_key,
                            aws_secret_access_key=config.access_secret,
                            region_name="us-west-2",
                        )

                        res = result_url.split("rawcaster/", 1) if result_url else None
                        splitString = res[1]

                        # Retrieve the JSON file object from S3
                        response = s3_client.get_object(
                            Bucket="rawcaster", Key=splitString
                        )

                        # Read the contents of the JSON file
                        json_data = response["Body"].read().decode("utf-8")
                        # Parse the JSON data
                        parsed_data = json.loads(json_data)

                        # Audio Content
                        query = parsed_data["results"]["transcripts"][0]["transcript"]
                        break
                    if status == "FAILED":
                        return {"status": 0, "msg": "Unable to convert"}
            except Exception as e:
                print(e)
                return {"status": 0, "msg": f"Something went wrong..."}

            return {"status": 1, "msg": "Success", "content": query}


@router.post("/generate_qrtoken")
async def generate_qrtoken(db: Session = Depends(deps.get_db), token: str = Form(None)):
    if not token:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    # Check token
    access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        )

        login_user_id = get_token_details.user_id if get_token_details else None

        email_id = (
            (
                (
                    get_token_details.user.email_id
                    if get_token_details.user.email_id
                    else get_token_details.user.mobile_no
                )
                if get_token_details.user_id
                else None
            )
            if get_token_details
            else None
        )

        if email_id:
            random_string = (
                f"{config.settings.SECRET_KEY}{int(datetime.utcnow().timestamp())}"
            )

            check_qr_tokens = (
                db.query(QrTokens)
                .filter(QrTokens.user_id == login_user_id, QrTokens.status == 1)
                .update({"status": 0})
            )
            db.commit()

            # add QR Token
            add_qr_token = QrTokens(
                user_id=login_user_id,
                token=hashlib.sha1(random_string.encode()).hexdigest(),
                status=1,
                created_at=datetime.utcnow(),
                expired_at=datetime.utcnow() + timedelta(minutes=1),
            )
            db.add(add_qr_token)
            db.commit()
            if add_qr_token:
                qr_string = f"email:{email_id}-{random_string}"
                encrypt_string = hashlib.sha1(qr_string.encode()).hexdigest()

                return {"status": 1, "msg": "Success", "qr_token": encrypt_string}
            else:
                return {"status": 0, "msg": "Code generate failed"}

        else:
            return {"status": 0, "msg": "Email id is empty"}


@router.post("/validate_qrtoken")
async def validate_qrtoken(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    qr_token: str = Form(None),
):
    if not token:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if not qr_token:
        return {"status": 0, "msg": "Auth code missing"}

    # Check token
    access_token = checkToken(db, token)
    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        )
        login_user_id = get_token_details.user_id if get_token_details else None

        encrypt_string = hashlib.sha1(qr_token.encode()).hexdigest()
        current_datetime = datetime.utcnow()
        get_qr = (
            db.query(QrTokens)
            .filter(
                QrTokens.user_id == login_user_id,
                QrTokens.token == encrypt_string,
                QrTokens.expired_at >= current_datetime,
                QrTokens.status == 1,
            )
            .order_by(QrTokens.id.desc())
            .first()
        )
        if get_qr:
            get_qr.status = 0
            db.commit()
            # Check Time validation
            return {"status": 1, "msg": "Success"}
        else:
            return {"status": 0, "msg": "Token expired"}


@router.post("/temp_file_upload")
async def temp_file_upload(
    db: Session = Depends(deps.get_db), file: UploadFile = File(None)
):
    file_ext = os.path.splitext(file.filename)[1]

    uploaded_file_path = await file_upload(file, file_ext, compress=1)
    # Get Duration of the File
    try:
        audio = AudioSegment.from_file(uploaded_file_path)
        duration_in_seconds = len(audio) / 1000
        if not duration_in_seconds < 120:
            return {"status": 0, "msg": "Allowed only maximum 2 minutes"}
    except Exception as e:
        print(e)
        return {"status": 0, "msg": "Try again later..."}

    # Upload to S3
    s3_file_path = f"nuggets/audio_{int(datetime.utcnow().timestamp())}{file_ext}"
    bucket_name = "rawcaster"

    client_s3 = boto3.client(
        "s3", aws_access_key_id=access_key, aws_secret_access_key=access_secret
    )  # Connect to S3

    with open(uploaded_file_path, "rb") as data:  # Upload File To S3
        upload = client_s3.upload_fileobj(data, bucket_name, s3_file_path)

    os.remove(uploaded_file_path)

    url_location = client_s3.get_bucket_location(Bucket=bucket_name)[
        "LocationConstraint"
    ]
    url = f"https://{bucket_name}.s3.{url_location}.amazonaws.com/{s3_file_path}"
    return {"status": 1, "url": url}


    
# # 92  Text To Audio Conversion (Nugget Content)
@router.post("/nuggetcontentaudio")
def nuggetcontentaudio(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
    translation_type: str = Form(None, description="1-audio,2-text"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if not nugget_id or not nugget_id.isnumeric():
        return {"status": 0, "msg": "Check your nugget id"}

    if translation_type and not translation_type.isnumeric():
        return {"status": 0, "msg": "Check transalation type"}
    # Check token
    access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        translation_type = int(translation_type) if translation_type else 1
        # check Read Out Language
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        )
        login_user_id = get_token_details.user_id if get_token_details else None
       
        get_user_readout_language = (
            db.query(
                UserSettings.id.label("user_setting_id"),
                ReadOutLanguage.id.label("read_out_id"),
                ReadOutLanguage.audio_support,
                ReadOutLanguage.language,
                UserSettings.read_out_accent_id.label("read_out_accent_id"),
                ReadOutLanguage.language_code,
                ReadOutLanguage.language_with_country
            )
            .join(ReadOutLanguage,ReadOutLanguage.id == UserSettings.read_out_language_id,isouter=True)
            .filter(
                UserSettings.user_id == login_user_id
                
            )
            .first()
        )
        
        target_language = (
            get_user_readout_language.language_code
            if get_user_readout_language
            else "en"
        )
        accent=target_language
        if get_user_readout_language and get_user_readout_language.read_out_accent_id:
            get_accent=db.query(ReadOutAccent).filter(ReadOutAccent.id == get_user_readout_language.read_out_accent_id,
                                                      ReadOutAccent.read_out_language_id == get_user_readout_language.read_out_id).first()
            accent=get_accent.accent_code if get_accent else target_language
        
        # Get nuggets
        get_nugget = (
            db.query(Nuggets)
            .filter(Nuggets.id == nugget_id, Nuggets.status == 1)
            .first()
        )
        
        if get_nugget:
            text_content = get_nugget.nuggets_master.content if get_nugget else None
            
            if text_content:
                translator = googletrans.Translator()
                
                try:
                    translated = translator.translate(text_content, dest=target_language)   
                except:
                    return {"status":0,"msg":"Unable to translate"}  
                
                if translation_type == 2:
                    return {
                        "status": 1,
                        "msg": "success",
                        "translation": translated.text
                    }
                else:
                    if get_user_readout_language and get_user_readout_language.audio_support:
                        text=translated.text
                        try:
                            tts = gTTS(text,lang=target_language,tld=accent)
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

                        filename = f"converted_{int(datetime.now().timestamp())}.mp3"

                        save_full_path = f"{output_dir}{filename}"
                        # Save the speech as an MP3 file
                        try:
                            tts.save(save_full_path)
                        except:
                            return {"status":0,"msg":"Unable to translate"}  
                            

                        s3_file_path = f"nuggets/converted_audio_{random.randint(1111,9999)}{int(datetime.utcnow().timestamp())}.mp3"

                        result = upload_to_s3(save_full_path, s3_file_path)

                        if result["status"] == 1:
                            return {
                                "status": 1,
                                "msg": "success",
                                "file_path": result["url"]
                            }
                        else:
                            return {"status":0,"msg":"Unable to convert"}
                    else:
                        langugae=get_user_readout_language.language if get_user_readout_language else ""
                        return {"status":0,"msg":f"Unable to convert text to audio in the {langugae} language"}
                    
                        

        else:
            return {"status": 0, "msg": "Invalid Nugget"}


# @router.post("/gtts_translate")
# def gtts_translate(
#     db: Session = Depends(deps.get_db),
#     text: str = Form(None),
# ):
#     from googletrans import Translator
#     # Create a Translator object
#     from playsound import playsound
    
#     text = "Hello, how are you?"
#     translator = Translator()
    
#     # Translate to Assamese
#     translated = translator.translate(text,lang='af')
#     tts = gTTS(text=translated.text, lang='af',tld='com')
    
#     tts.save("afrikaans_tts.mp3")
#     # Play the audio file
#     playsound("afrikaans_tts.mp3")

#     return translated.text




# # Initialize the Polly client
# polly = boto3.client('polly',aws_access_key_id=config.access_key,
#                     aws_secret_access_key=config.access_secret,region_name='us-east-1')

# # Define the voice ID and language code for your desired language
# voice_id = 'Joanna'  # Replace 'YourVoiceID' with the appropriate Polly voice ID
# language_code = 'en-US'  # Replace 'YourLanguageCode' with the appropriate language code

# # Request speech synthesis
# response = polly.synthesize_speech(
#     Text=text,
#     OutputFormat='mp3',  # You can choose other formats like 'ogg_vorbis', 'pcm', etc.
#     VoiceId=voice_id,
#     LanguageCode=(get_user_readout_language.language_with_country 
#                   if get_user_readout_language 
#                   else "en-US")
# )
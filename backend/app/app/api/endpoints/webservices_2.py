from fastapi import APIRouter, Depends, Form,File,UploadFile
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import datetime,date
from typing import List
from app.core import config
import openai
from googletrans import Translator


router = APIRouter() 


access_key=config.access_key
access_secret=config.access_secret
bucket_name=config.bucket_name


# 85 Event Abuse Report

 
@router.post("/addeventabusereport")
async def add_event_abuse_report(db:Session=Depends(deps.get_db),token:str=Form(None),event_id:str=Form(None),message:str=Form(None),attachment:UploadFile=File(None)):
    if token == None or token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    
    elif event_id == None or not event_id.isnumeric():
        return {"status":0,"msg":"Event id is missing"}
   
    elif message == None:
        return {"status":0,"msg":"Message Cant be Blank"}
    
    else:
      
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            event_id=int(event_id)
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id = get_token_details.user_id if get_token_details else None
            
            # Add Abuse Report
            check_event=db.query(Events).filter(Events.id == event_id,Events.status == 1).first()
            
            if check_event:
                add_abuse_report=EventAbuseReport(event_id=event_id,user_id=login_user_id,message=message,created_at=datetime.utcnow(),status = 0)
                db.add(add_abuse_report)
                db.commit()
                db.refresh(add_abuse_report)
                
                if attachment:
                    file_name=attachment.filename
                    # file_temp=attachment.content_type
                    # file_size=len(await attachment.read())
                    file_ext = os.path.splitext(attachment.filename)[1]   
                    file_extensions=['.jpg','.png','.jpeg']
                                   
                    if file_ext in file_extensions:
                        try:
                            s3_path=f"events/image_{random.randint(11111,99999)}{int(datetime.utcnow().timestamp())}{file_ext}"
                            uploaded_file_path=file_upload(attachment,compress=None)
                            
                            result=upload_to_s3(uploaded_file_path,s3_path)
                            # Upload to S3
                            if result['status'] == 1:
                                add_abuse_report.attachment = result['url']
                                add_abuse_report.status = 1
                                
                                db.commit()
                                return {"status":1,"msg":"Success"}
                            else:
                                return result
                        except:
                            return {"status":0,"msg":"Unable to Upload File"}
                            
                    else:
                        return {"status":0,"msg":"Accepted only jpg,png,jpeg"}
                
                # Update Event Absue Report
                
                add_abuse_report.status = 1
                db.commit()
                return {"status":1,"msg":"Success"}
            else:
                return {"status":0,"msg":"Invalid Event ID"}
                


# Testing
@router.post("/testaddeventabusereport")
async def testaddeventabusereport(db:Session=Depends(deps.get_db),token:str=Form(None),event_id:str=Form(None),message:str=Form(None),attachment:UploadFile=File(None)):
    if token == None or token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    
    elif event_id == None or not event_id.isnumeric():
        return {"status":0,"msg":"Event id is missing"}
   
    elif message == None:
        return {"status":0,"msg":"Message Cant be Blank"}
    
    else:
      
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            event_id=int(event_id)
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id = get_token_details.user_id if get_token_details else None
            
            # Add Abuse Report
            check_event=db.query(Events).filter(Events.id == event_id,Events.status == 1).first()
            
            if check_event:
                add_abuse_report=EventAbuseReport(event_id=event_id,user_id=login_user_id,message=message,created_at=datetime.utcnow(),status = 0)
                db.add(add_abuse_report)
                db.commit()
                db.refresh(add_abuse_report)
                
                if attachment:
                    file_name=attachment.filename
                    # file_temp=attachment.content_type
                    # file_size=len(await attachment.read())
                    file_ext = os.path.splitext(attachment.filename)[1]   
                    file_extensions=['.jpg','.png','.jpeg']
                                   
                    if file_ext in file_extensions:
                        try:
                            s3_path=f"events/image_{random.randint(11111,99999)}{int(datetime.utcnow().timestamp())}{file_ext}"
                            uploaded_file_path=file_upload(attachment,compress=None)
                            
                            result=upload_to_s3(uploaded_file_path,s3_path)
                            # Upload to S3
                            if result['status'] == 1:
                                add_abuse_report.attachment = result['url']
                                add_abuse_report.status = 1
                                
                                db.commit()
                                return {"status":1,"msg":"Success"}
                            else:
                                return result
                        except:
                            return {"status":0,"msg":"Unable to Upload File"}
                            
                    else:
                        return {"status":0,"msg":"Accepted only jpg,png,jpeg"}
                
                # Update Event Absue Report
                
                add_abuse_report.status = 1
                db.commit()
                return {"status":1,"msg":"Success"}
            else:
                return {"status":0,"msg":"Invalid Event ID"}
                


# CRON
@router.post("/croninfluencemember")
async def croninfluencemember(db:Session=Depends(deps.get_db),user_id:int=Form(None)):
    if user_id:
        get_user_details=db.query(User).filter(User.id == user_id,User.status == 1).all()
    else:
        get_user_details=db.query(User).filter(User.status == 1).all()
        
    for usr in get_user_details:
        get_follow_user=db.query(FollowUser).filter(FollowUser.follower_userid == usr.id,FollowUser.status == 1).count()
        
        if get_follow_user:
            user_status_master=db.query(UserStatusMaster).filter(UserStatusMaster.min_membership_count <= get_follow_user,or_(UserStatusMaster.max_membership_count >=  get_follow_user,UserStatusMaster.max_membership_count == None)).first()
            
            if user_status_master:
                usr.user_status_id = user_status_master.id
                db.commit()
                return "Done"
               


# 86  Add Claim Account
@router.post("/addclaimaccount")
async def add_claim_account(db:Session=Depends(deps.get_db),token:str=Form(None),influencer_id:str=Form(None),first_name:str=Form(None),
                            last_name:str=Form(None),telephone:str=Form(None),email_id:str=Form(None),dob:str=Form(None),location:str=Form(None),
                            ):
    if token == None or token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    
    elif influencer_id == None or not influencer_id.isnumeric():
        return {"status":0,"msg":"Influence id is missing"}
   
    elif first_name == None:
        return {"status":0,"msg":"First Name Cant be Blank"}
    
    elif email_id == None:
        return {"status":0,"msg":"Email Cant be Blank"}
    
    elif dob and is_date(dob) == False:
        return {"status":0,"msg":"Invalid Date"}
    
    else:
      
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id = get_token_details.user_id if get_token_details else None
            # Check requests
            check_requests=db.query(ClaimAccounts).filter(ClaimAccounts.user_id == login_user_id,ClaimAccounts.influencer_id == influencer_id).first()
            if not check_requests:
                add_clain=ClaimAccounts(user_id=login_user_id,influencer_id=influencer_id,first_name=first_name.strip(),dob=dob,last_name=last_name,location=location,
                                        telephone=telephone,email_id=email_id,claim_date=datetime.utcnow(),created_at=datetime.utcnow(),status=1,admin_status=0)
                db.add(add_clain)
                db.commit()
                return {"status":1,"msg":"You have placed a claim on a predefined influencer profile, We will contact you to validate your claim. Please contact us at info@rawcaster.com if you have any questions."}
            else:
                return {"status":0,"msg":"Already sent"}
    


# 86  List UnClaim Account
@router.post("/listunclaimaccount")
async def listunclaimaccount(db:Session=Depends(deps.get_db),token:str=Form(None),location:str=Form(None),gender:str=Form(None),age:str=Form(None)):
    if token == None or token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    if gender and not gender.isnumeric():
        return {"status":0,"msg":"Invalid Gender type"}
        
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id = get_token_details.user_id if get_token_details else None
            
            get_unclaimed_account=db.query(User).join(UserStatusMaster,User.user_status_id == UserStatusMaster.id,isouter=True).filter(User.created_by == 1,UserStatusMaster.type == 2)
            if location:
                get_unclaimed_account=get_unclaimed_account.filter(User.geo_location.ilike("%"+location+"%"))
            if gender:
                get_unclaimed_account=get_unclaimed_account.filter(User.geo_location == gender)
            if age:
                if not age.isnumeric():
                    return {"status":0,"msg":"Invalid Age"}
                else:
                    current_year = datetime.utcnow().year
                    get_unclaimed_account=get_unclaimed_account.filter(current_year - extract('year',User.dob) == age )
                    
            unclaimed_accounts=[]
            get_unclaimed_account=get_unclaimed_account.all()
            
            for unclaim in get_unclaimed_account:

                check_claim_account=db.query(ClaimAccounts).filter(ClaimAccounts.user_id == login_user_id,ClaimAccounts.influencer_id == unclaim.id).first()
                           
                unclaimed_accounts.append({
                                        "user_id":unclaim.id,"email_id":unclaim.email_id if unclaim.email_id else "",
                                        "display_name":unclaim.display_name if unclaim.display_name else "",
                                        "first_name":unclaim.first_name if unclaim.first_name else "","last_name":unclaim.last_name if unclaim.last_name else "",
                                        "dob":unclaim.dob if unclaim.dob else "","mobile_no":unclaim.mobile_no if unclaim.mobile_no else "",
                                        "location":unclaim.geo_location if unclaim.geo_location else "",
                                        "profile_img":unclaim.profile_img if unclaim.profile_img else "",
                                        "unclaimed_status":1 if check_claim_account else 0
                                        
                                        })
            
            return {"status":1,"msg":"Success","unclaim_accounts":unclaimed_accounts}
        


# 87  Influencer Chat
@router.post("/influencerchat")
async def influencerchat(db:Session=Depends(deps.get_db),token:str=Form(None),type:str=Form(None,description="1-text,2-image,3-audio,4-video"),message:str=Form(None),attachment:List[UploadFile]=File(None)):
    if token == None or token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    
    elif type == None:
        return {"status":0,"msg":"Type is missing"}
        
    elif type == 1 and (message == None or message.strip() == ''):
        return {"status":0,"msg":"Message cant empty"}
    
    else:
        type=int(type)
        
        if not 1 <= type <= 5:
            return {"status":0,"msg":"Check type"}
            
        if (type == 2 or type == 3 or type == 4 or type == 5) and not attachment:
            return {"status":0,"msg":"File missing"}
            
        access_token=checkToken(db,token)
        
        if access_token == False:
            
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id = get_token_details.user_id if get_token_details else None
            
            # Get Default Friend Group
            get_friend_group=db.query(FriendGroups).filter(FriendGroups.created_by == login_user_id,FriendGroups.status == 1,FriendGroups.group_name == 'My Fans').first()
            if not get_friend_group:
                return {"status":0,"msg":"Check Group"}
            else:
                file_type=[2,3,4,5]
                content=[]
                if type == 1:
                    content.append(message)
                    
                elif type in file_type:
                    if type == 2 or type == 5:
                        for attachment in attachment:
                            file_ext = os.path.splitext(attachment.filename)[1]
                            
                            uploaded_file_path=file_upload(attachment,compress=1)
                            s3_file_path=f'Image_{random.randint(1111,9999)}{int(datetime.utcnow().timestamp())}{file_ext}'
                            
                            result=upload_to_s3(uploaded_file_path,s3_file_path)
                            if result['status'] and result['status'] == 1:
                                content.append(result['url'])
                            else:
                                return result
                        
                    if type == 4: # Video
                        readed_file=await attachment.read()
                        save_file_path=video_file_upload(readed_file,compress=None)
                        segment_filename = f"video_{random.randint(1111,9999)}{int(datetime.now().timestamp())}.mp4"
                        
                        result=upload_to_s3(save_file_path,segment_filename)
                        if result['status'] and result['status'] == 1:
                            content.append(result['url'])
                        else:
                            return result
                        
                    if type == 3: # Audio
                        readed_file=await attachment.read()
                        save_file_path=await audio_file_upload(readed_file,compress=None)
                        segment_filename = f"audio_{random.randint(1111,9999)}{int(datetime.now().timestamp())}.mp3"
                        
                        result=upload_to_s3(save_file_path,segment_filename)
                        if result['status'] and result['status'] == 1:
                            content.append(result['url'])
                        else:
                            return result
                        
                for msg in content:
                    # Add Group Chat
                    add_group_chat=GroupChat(group_id=get_friend_group.id,sender_id = login_user_id,message=message if type == 1 else None,path=msg if type != 1 else None,type=type,sent_datetime=datetime.utcnow(),status=1)          
                    db.add(add_group_chat)
                    db.commit()
                    db.refresh(add_group_chat)
                    
                return {"status":1,"msg":"Success"}
            





# 88  Verify Accounts Only Diamond Members
@router.post("/verifyaccount")
async def add_verify_account(db:Session=Depends(deps.get_db),token:str=Form(None),first_name:str=Form(None),
                            last_name:str=Form(None),telephone:str=Form(None),email_id:str=Form(None),dob:str=Form(None),location:str=Form(None),
                            ):
    if token == None or token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
   
    elif first_name == None:
        return {"status":0,"msg":"First Name Can't be Blank"}
    
    elif email_id == None:
        return {"status":0,"msg":"Email Can't be Blank"}
    
    elif dob and is_date(dob) == False:
        return {"status":0,"msg":"Invalid Date"}
    elif not telephone:
        return {"status":0,"msg":"Mobile number can't be Blank"}
        
    else:
      
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id = get_token_details.user_id if get_token_details else None
            # Check Already requested
            get_accounts=db.query(VerifyAccounts).filter(VerifyAccounts.user_id == login_user_id).first()
            if not get_accounts:
                
                add_clain=VerifyAccounts(user_id=login_user_id,first_name=first_name.strip(),dob=dob,last_name=last_name,location=location,
                                        telephone=telephone,email_id=email_id,verify_date=datetime.utcnow(),created_at=datetime.utcnow(),status=1,verify_status=0)
                db.add(add_clain)
                db.commit()
                return {"status":1,"msg":"We will contact you to validate your account verify. Please contact us at info@rawcaster.com if you have any questions."}
            else:
                return {"status":0,"msg":"you are already requested to verification"}
                
    


# 91 AI Chat
@router.post("/aichat")
async def aichat(db:Session=Depends(deps.get_db),token:str=Form(None),user_query:str=Form(None)):
    if token == None or token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    
    access_token=checkToken(db,token)    
    if access_token == False:
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        user_name = get_token_details.user.display_name if get_token_details else None
        created_at=common_date(datetime.utcnow(),None)
        if user_query:
            openai.api_key = config.open_ai_key
            
            response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                    {"role": "system", "content": "You are a chatbot"},
                    {"role": "user", "content": f"{user_query}?"},
                ]
                )

            result = ''
            if response:
                for choice in response.choices:
                    result += choice.message.content
                
                return {"status":1,"msg":result,"created_at":created_at}
            else:
                return {"status":0,"msg":"Failed to search"}
        else:
            return {"status":1,"msg":f"HI {user_name}, I am an Artificial Intelligence (AI), I can answer your question on anything. Speak or type your question here..","created_at":created_at}
            
        

# Google Transalate APi Key = AIzaSyAMCCtM2tXa9ytt0a-JzoX74p6iDfDrlzM




# 92  Text To Audio Conversion (Nugget Content)
@router.post("/nuggetcontentaudio")
async def nuggetcontentaudio(db:Session=Depends(deps.get_db),token:str=Form(None),nugget_id:str=Form(None)):
    if token == None or token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    if not nugget_id or not nugget_id.isnumeric():
        return {"status":0,"msg":"Check your nugget id"}
    
    # Check token
    access_token=checkToken(db,token)
        
    if access_token == False:
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        # Get nuggets
        get_nugget=db.query(Nuggets).filter(Nuggets.id == nugget_id,Nuggets.status == 1).first()
        if get_nugget:
            get_exist_audio=db.query(NuggetContentAudio).filter(NuggetContentAudio.nugget_master_id == get_nugget.nuggets_id,NuggetContentAudio.status == 1).first()
            if get_exist_audio:
                return {"status":1,"msg":"Success","file_path":get_exist_audio.path}
            
            else:
                text=get_nugget.nuggets_master.content if get_nugget else None
                
                if text:
                    try:
                        target_language='en'
                    
                        translator = Translator(service_urls=['translate.google.com'])

                        # Detect the source language
                        detected_lang = translator.detect(text).lang

                        # Translate the text to the target language
                        translation = translator.translate(text, src=detected_lang, dest=target_language)
                        
                        translated_text=translation.text
                        
                        # Create an instance of the Polly client
                        polly_client = boto3.Session(
                            aws_access_key_id=config.access_key,
                            aws_secret_access_key=config.access_secret,
                            region_name='us-west-2'  # Replace with your desired AWS region
                            ).client('polly')

                        # Specify the desired voice and output format
                        voice_id = 'Joanna'
                        output_format = 'mp3'

                        # Request speech synthesis
                        response = polly_client.synthesize_speech(
                            Text=translated_text,
                            VoiceId=voice_id,
                            OutputFormat=output_format
                        )
                        # Upload File
                        # base_dir = f"{st.BASE_DIR}rawcaster_uploads"
                        base_dir = "rawcaster_uploads"
                        
                        try:
                            os.makedirs(base_dir, mode=0o777, exist_ok=True)
                        except OSError as e:
                            sys.exit("Can't create {dir}: {err}".format(
                                dir=base_dir, err=e))

                        output_dir = base_dir + "/"
                        
                        filename=f"converted_{int(datetime.now().timestamp())}.mp3"    
                        
                        save_full_path=f'{output_dir}{filename}' 
                        
                        with open(save_full_path, 'wb') as file:
                            file.write(response['AudioStream'].read())
                            
                        s3_file_path=f"nuggets/converted_audio_{random.randint(1111,9999)}{int(datetime.utcnow().timestamp())}.mp3"
                                
                        result=upload_to_s3(save_full_path,s3_file_path)
                        
                        if result['status'] == 1:
                            add_audio_file=NuggetContentAudio(nugget_master_id = get_nugget.nuggets_id,path= result['url'],created_at=datetime.utcnow(),status =1)
                            db.add(add_audio_file)
                            db.commit()
                            db.refresh(add_audio_file)
                            return {"status":1,"msg":"success","file_path":result['url']}
                            
                        else:
                            return result
                    except:
                        return {"status":0,"msg":"Unable to convert"}
                        
        else:
            return {"status":0,"msg":"Invalid Nugget"}
        


# # 89  AI Response Text Audio

@router.post("/texttoaudio")
async def texttoaudio(db:Session=Depends(deps.get_db),token:str=Form(None),message:str=Form(None)):
    if not token:
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        
    if not message:
        return {"status":0,"msg":"Meaage can't be Empty"}
    
    access_token=checkToken(db,token)
        
    if access_token == False:
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        target_language='en'
                    
        translator = Translator(service_urls=['translate.google.com'])
        print(message)
        # Detect the source language
        detected_lang = translator.detect(message).lang

        # Translate the text to the target language
        translation = translator.translate(message, src=detected_lang, dest=target_language)
        
        translated_text=translation.text
        
        # Create an instance of the Polly client
        polly_client = boto3.Session(
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.access_secret,
            region_name='us-west-2'  # Replace with your desired AWS region
        ).client('polly')

        # Specify the desired voice and output format
        voice_id = 'Joanna'
        output_format = 'mp3'

        # Request speech synthesis
        response = polly_client.synthesize_speech(
            Text=translated_text,
            VoiceId=voice_id,
            OutputFormat=output_format
        )
        # Upload File
        base_dir = "rawcaster_uploads/converted_audio"
        
        try:
            os.makedirs(base_dir, mode=0o777, exist_ok=True)
        except OSError as e:
            sys.exit("Can't create {dir}: {err}".format(
                dir=base_dir, err=e))

        output_dir = base_dir + "/"
        
        filename=f"converted_{int(datetime.now().timestamp())}.mp3"    
        
        save_full_path=f'{output_dir}{filename}' 
        
        with open(save_full_path, 'wb') as file:
            file.write(response['AudioStream'].read())
        
        s3_file_path=f"nuggets/converted_ai_audio_{random.randint(1111,9999)}{int(datetime.utcnow().timestamp())}.mp3"
                                
        result=upload_to_s3(save_full_path,s3_file_path)
        return result



# Test
import speech_recognition as sr
# 91 AI Chat Audio Chat
@router.post("/audio_to_text")
async def audio_to_text(audio_file:UploadFile=File(None)):
    transcribe_client = boto3.client('transcribe',aws_access_key_id=config.access_key,
        aws_secret_access_key=config.access_secret,
        region_name='us-west-2')
    
    
    
    def transcribe_audio(file_path):
    # Create an Amazon Transcribe client
        transcribe = boto3.client('transcribe',aws_access_key_id=config.access_key,
            aws_secret_access_key=config.access_secret,
            region_name='us-west-2')

        # Specify the AWS S3 bucket and key where the audio file is located
        bucket_name = 'rawcaster'
        audio_key = 'https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/audio_15291685323973.mp3'  # Replace with your audio file path
        job_name=f"transcription-job-name{int(datetime.utcnow().timestamp())}"
        
        # Start the transcription job
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f's3://{bucket_name}/{audio_key}'},
            MediaFormat='wav',
            LanguageCode='en-US'  # Adjust the language code if needed
        )

        # Wait for the transcription job to complete
        while True:
            response = transcribe.get_transcription_job(
                TranscriptionJobName=job_name
            )
            if response['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break

        # Get the transcription results
        if response['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            transcription_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
            transcription = transcribe.get_transcription_job(
                TranscriptionJobName=job_name
            )['TranscriptionJob']['Transcript']['Results']
            return transcription

        return None  # Transcription job failed

    # Usage example
    audio_file_path = 'path/to/audio/file.wav'  # Replace with your audio file path
    transcription_result = transcribe_audio(audio_file_path)

    if transcription_result:
        print(transcription_result)
    else:
        print('Transcription failed.')
    
    
    
    
    
    
    
    
    # s3 = boto3.client('s3',aws_access_key_id=access_key,aws_secret_access_key=access_secret) # Connect to S3
    
    # # file_path="/home/surya_maestro/Music/Jack Sparrow English Dialogue.wav"
    # audio_file_key="https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/audio_15491685140207.mp3"
    
    # def transcribe_audio_file(file_key):
    #     job_name = f'transcription_job{int(datetime.utcnow().timestamp())}'
    #     job_uri = f's3://rawcaster/{file_key}'

    #     response = transcribe_client.start_transcription_job(
    #         TranscriptionJobName=job_name,
    #         Media={'MediaFileUri': job_uri},
    #         MediaFormat='mp3',  # Specify the correct format of your audio file
    #         LanguageCode='en-US'  # Specify the language code if other than English
    #     )

    #     # Wait for the transcription job to complete
    #     while True:
    #         response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    #         if response['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
    #             break

    #     # Get the transcript
    #     transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
    #     transcript_response = s3.get_object(Bucket=transcript_uri.split('/')[2], Key=transcript_uri.split('/')[3])
    #     transcript = transcript_response['Body'].read().decode('utf-8')

    #     return transcript

    # transcript = transcribe_audio_file(audio_file_key)
    # print(transcript)
    
    # return transcript
    
    
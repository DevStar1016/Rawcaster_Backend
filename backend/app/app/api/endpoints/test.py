from fastapi import APIRouter, Depends, Form,File,UploadFile
from app.models import *
from app.core.security import *
from typing import List
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from datetime import datetime,date,time
from sqlalchemy import func,case,text

from langdetect import detect
from gtts import gTTS
from playsound import playsound
from moviepy.video.io.VideoFileClip import VideoFileClip
import boto3    
import shutil
from moviepy.editor import *
import base64
import os
import subprocess
router = APIRouter() 


access_key="AKIAYFYE6EFYGNPCA32D"
access_secret="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"





@router.post("/chime")
async def chime():

    import boto3

    chime = boto3.client('chime',aws_access_key_id=access_key,aws_secret_access_key=access_secret,region_name='us-east-1')  # Replace 'us-east-1' with your desired AWS region

    response = chime.create_meeting(
        ClientRequestToken='12',
        MediaRegion='us-east-1',
        MeetingHostId='123',
        ExternalMeetingId='12',
       
        )

    return response



@router.post("/meeting_join_url")
async def meeting_join_url():

    import boto3


    chime = boto3.client('chime',aws_access_key_id=access_key,aws_secret_access_key=access_secret, region_name='us-east-1')  # Replace 'us-east-1' with your desired AWS region
    
    meeting_url = "e6481e2b-1142-4a9b-9749-23e7df40bb35:34ff7a2b-b620-4bc5-a547-50da974663de"
    # Extract the meeting ID and attendee details from the meeting URL
    meeting_id = meeting_url.split('/')[-1]
    attendee_id = meeting_url.split('=')[-1]

    # Join the Chime meeting
    response = chime.create_attendee(
        MeetingId=meeting_id,
        ExternalUserId=attendee_id,
    )

    # Extract the join token from the response
    join_token = response['Attendee']['JoinToken']

    # Return the join token
    return join_token


import subprocess
import os

@router.post("/video_upload")
async def video_upload(file:UploadFile=File(None)):
    file_name=file.filename
    file_ext = os.path.splitext(file.filename)[1]
    
    with open(file_name, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    segment_duration = 5 * 60

    video = VideoFileClip(file_name)   # Video Split ( 5 Minutes)
    duration = video.duration
    splited_video_url=[]
    total_duration = video.duration
    
    # if duration < 3000:
    num_segments = math.ceil(total_duration / segment_duration)
    for i in range(num_segments):
    
        start_time = i * segment_duration
        end_time = min((i+1) * segment_duration, total_duration)
        
        segment = video.subclip(start_time, end_time)
        
        # Save the segment as a new file
        
        segment_filename = f"video_clip_{random.randint(1111,9999)}{int(datetime.datetime.now().timestamp())}.mp4"
        segment.write_videofile(segment_filename, audio_codec="aac")
        
        splited_video_url.append(segment_filename)
        
        bucket_name='rawcaster'

        access_key="AKIAYFYE6EFYGNPCA32D"
        access_secret="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"
        # try:
        client_s3 = boto3.client('s3',aws_access_key_id=access_key,aws_secret_access_key=access_secret) # Connect to S3
        s3_file_path=f"nuggets/video_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}.mp4"
        
        with open(segment_filename, 'rb') as data:  # Upload File To S3
            upload=client_s3.upload_fileobj(data, bucket_name, s3_file_path,ExtraArgs={'ACL': 'public-read'})
        
        os.remove(segment_filename)
        
        url_location=client_s3.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
        url = f'https://{bucket_name}.s3.{url_location}.amazonaws.com/{s3_file_path}'
        if url:
            add_nugget_attachment=NuggetsAttachment(user_id=login_user_id,nugget_id=add_nuggets_master.id,
                                media_type=type,media_file_type=file_ext,file_size=file_size,path=url,
                                created_date=datetime.datetime.utcnow(),status =1)
            db.add(add_nugget_attachment)
            db.commit()
            db.refresh(add_nugget_attachment)
            
            # return {"status":1,"url":url}
        else:
            return "Failed to Upload"


       

       
    

    



    # # Create a Chime meeting
    # response = chime.create_meeting(
    #     ClientRequestToken='sadasdasdadadasdaddasd',
    #     MediaRegion='us-east-1'  # Specify the desired AWS region
    # )
    # return response
    # # Retrieve meeting details
    # meeting_id = response['Meeting']['MeetingId']
    # join_token = response['Meeting']['JoinToken']

    # return meeting_id, join_token
 


@router.post("/send_test_mail")
async def send_test_mail():

    conf =  ConnectionConfig(
        MAIL_USERNAME="AKIAYFYE6EFYF3SQOJHI",
        MAIL_PASSWORD="BPkaC3u48gAj15i/YBLMDnICroNWdHXRWHMBYGWlDT6Q",  
        MAIL_FROM="rawcaster@rawcaster.com", 
        MAIL_PORT=587,
        MAIL_SERVER="email-smtp.us-west-2.amazonaws.com",
        MAIL_FROM_NAME='Rawcaster',
        MAIL_STARTTLS = True,
        MAIL_SSL_TLS = False,
        USE_CREDENTIALS = True,
        VALIDATE_CERTS = True
        )
    
    message = MessageSchema(
        subject="Test",
        subtype='html',
        recipients=['suryadurai11@gmail.com'],
        body="Test"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    
    return True


@router.post("/upload_audio/")
async def upload_audio():
    # Importing the module
    # uploading the video we want to edit
    video = VideoFileClip('clip1.mp4')


    # getting width and height of video 1
    width_of_video1 = video.w
    height_of_video1 = video.h

    print("Width and Height of original video : ", end = " ")
    print(str(width_of_video1) + " x ", str(height_of_video1))

    print("#################################")

    # compressing
    video_resized = video.resize(0.2)

    # getting width and height of video 2 which is resized
    width_of_video2 = video_resized.w
    height_of_video2 = video_resized.h

    print("Width and Height of resized video : ", end = " ")
    print(str(width_of_video2) + " x ", str(width_of_video2))

    print("###################################")


    # displaying final clip
 


@router.post("/upload-video/")
async def upload_video(video: UploadFile = File(...), target_size_kb: int = 100):
  
     
    file_path = os.path.abspath(video.filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await video.read())

    output_file = f"s_converted.mp4"
    command = f"ffmpeg -i {file_path} -vcodec libx265 -crf 50 {output_file}"
    subprocess.run(command, shell=True, check=True)

    compressed_size = os.path.getsize(output_file) // 1024

    return compressed_size


# from io import BytesIO


@router.post('/upload')
async def upload_image(image: UploadFile = File(...)):
    file_name=image.filename
    file_temp=image.content_type
    file_size=len(await image.read())
    
    file_ext = os.path.splitext(image.filename)[1]
    # return image
    if 'video' in file_temp:
        return "hi"
    return file_name,file_temp,file_size,file_ext
    # Upload File to Server
    # output_dir,filename=file_upload(image)
    
    # bucket_name='rawcaster'
    # print("""connect to s3""")

    # client_s3 = boto3.client(
    #     's3',
    #     aws_access_key_id=access_key,
    #     aws_secret_access_key=access_secret
    # )

    # print("""upload file to s3""")
    # file_path=image.filename
    # bucket_file_path=f"profileimage/{filename}"
    
    # with open(output_dir, 'rb') as data:
    #     upload=client_s3.upload_fileobj(data, bucket_name, bucket_file_path)

    # os.remove(output_dir)

    # out_pdf_file=f'{bucket_name}/{output_dir}'
    
    # print('done..')
        
# 1 Video Spliting
@router.post("/video_split")
async def video_split(db:Session=Depends(deps.get_db),video_file:UploadFile=File(...)):
    base_dir = f"{st.BASE_DIR}/rawcaster"
    try:
        os.makedirs(base_dir, mode=0o777, exist_ok=True)
    except OSError as e:
        sys.exit("Can't create {dir}: {err}".format(
            dir=base_dir, err=e))

    output_dir = base_dir + "/"
    
    characters = string.ascii_letters + string.digits
    # Generate the random string
    random_string = ''.join(random.choice(characters) for i in range(18))
    filename=f"video_{random_string}.mp4"    
   
    save_full_path=filename 
      
    with open(save_full_path, "wb") as buffer:
        buffer.write(await video_file.read())

    segment_duration = 5 * 60

    video = VideoFileClip(save_full_path)
    duration = video.duration
    url=[]
    total_duration = video.duration
    
    if duration < 3000:
        num_segments = math.ceil(total_duration / segment_duration)
        for i in range(num_segments):
        
            start_time = i * segment_duration
            end_time = min((i+1) * segment_duration, total_duration)
            
            segment = video.subclip(start_time, end_time)
            
            # Save the segment as a new file
            segment_filename = f"output_segment_{i+1}.mp4"
            segment.write_videofile(segment_filename, codec="libx264")
            url.append(segment_filename)
        return url
    else:
        print("fail")


# # def get_ip():
# #     response = requests.get('https://api64.ipify.org?format=json').json()
# #     return response["ip"]


# # def get_location():
# #     ip_address = get_ip()
# #     response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
# #     location_data = {
# #         "ip": ip_address,
# #         "city": response.get("city"),
# #         "region": response.get("region"),
# #         "country": response.get("country_name")
# #     }
# #     return location_data


# # print(get_location())




# # # For Testing
# # @router.post("/test")
# # async def test(db:Session=Depends(deps.get_db),auth_code:str=Form(...)):
# #     # import boto3
    
# #     # polly = boto3.client(
# #     #             'polly',
# #     #             aws_access_key_id=access_key,
# #     #             aws_secret_access_key=access_secret,
# #     #             region_name="us-east-1",
# #     #             )

# #     # # Set the parameters for the speech synthesis
# #     # output_format = 'mp3'
# #     # voice_id = 'Joanna'
# #     # text = 'Hello, this is a test of Amazon Polly.'
    
# #     # lang = detect(text)
# #     # # Call the synthesize_speech() method to generate the audio file
    
# #     # response = polly.synthesize_speech(Text=text, VoiceId=voice_id, OutputFormat=output_format)

# #     # # Save the audio file to disk
# #     # with open('test.mp3', 'wb') as f:
# #     #     f.write(response['AudioStream'].read())
# #     # playsound("test.mp3")
    
   
   
# #     #   ---------------------------------
# #     import os
# #     from google.cloud import translate_v2 as translate
# #     os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/service_account_key.json'
# #     client = translate.Client()
   
# #     result = client.translate('Hello, how are you?', target_language='ta')
# #     print(result['translatedText'])
    
    
    
    
    
# # from langdetect import detect
# # from gtts import gTTS
# # from playsound import playsound
# # from profanityfilter import ProfanityFilter
   
# # For Testing
# # @router.post("/lang")
# # async def lang(db:Session=Depends(deps.get_db),auth_code:str=Form(...)):
# #     from googletrans import Translator
# #     pf=ProfanityFilter()
# #     translator = Translator()
# #     translated = translator.translate('In the Tamil language, the letters formed with each of the twelve vowels and eighteen consonants are called vowels.', dest='ta')
# #     print(translated.text)

# #     filtered_text = pf.censor(translated.text)
    
# #     # Languages
# #     lang = detect(translated.text)
# #     print("language",lang)
    
# #     tts = gTTS(text=filtered_text,lang='ta')
    
    
# #     tts.save("test.mp3")   
# #     playsound("test.mp3")
    

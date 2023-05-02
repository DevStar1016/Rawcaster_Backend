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
import os
import subprocess
router = APIRouter() 


access_key="AKIAYFYE6EFYGNPCA32D"
access_secret="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"



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
async def upload_audio(audio: UploadFile = File(...)):
    uploads_file_name=audio.filename
    
    base_dir = f"{st.BASE_DIR}/rawcaster"
    try:
        os.makedirs(base_dir, mode=0o777, exist_ok=True)
    except OSError as e:
        sys.exit("Can't create {dir}: {err}".format(
            dir=base_dir, err=e))

    output_dir = base_dir + "/"
    
    characters = string.ascii_letters + string.digits
    # Generate the random string
    
    ext = os.path.splitext(uploads_file_name)[-1].lower()
    filename=f"audio_{random.randint(1111,9999)}{datetime.now().timestamp()}{ext}"    
   
    save_full_path=f'{output_dir}{filename}'  
    
    filename = audio.filename
    input_path = os.path.abspath(audio.filename)
    
    output_path = f"{filename}.mp3"
   

    with open(save_full_path, "wb") as buffer: 
        buffer.write(await audio.read())

    subprocess.run(["ffmpeg", "-i", save_full_path, "-ab", "32k", "-y", output_path])

    os.remove(save_full_path)


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
    

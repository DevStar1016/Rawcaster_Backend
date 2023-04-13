from fastapi import APIRouter, Depends, Form,File,UploadFile
from app.models import *
from app.core.security import *
from typing import List
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from datetime import datetime,date,time
from sqlalchemy import func,case,text
import re
import base64
import json
from langdetect import detect
from gtts import gTTS
from playsound import playsound
from profanityfilter import ProfanityFilter
from moviepy.video.io.VideoFileClip import VideoFileClip
import boto3    

router = APIRouter() 


access_key="AKIAYFYE6EFYG6RJOPMF"
access_secret="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"

from io import BytesIO

@router.post('/upload')
async def upload_image(image: UploadFile = File(...)):
    # bucket_name = event['bucket_name']
    # file_name = event['file_name']
    import boto3
    import csv
    import io
    s3Client = boto3.client('s3', aws_access_key_id=access_key,aws_secret_access_key=access_secret)
    def lambda_handler(event, context): 
        #Get our bucket and file name
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
    
        #Get our object 
        response = s3Client.get_object(Bucket=bucket, Key=key)
        #Process the data
        data = response['Body'].read().decode('utf-8')
        reader = csv.reader(io.StringlO(data))
        next(reader)
        for row in reader: 
            print(str.format("Year - {Year, Mileage - Price - {}", row[0], row[1], row[2]))
    

# 1 Video Spliting
@router.post("/video_split")
async def video_split(db:Session=Depends(deps.get_db)):

    segment_duration = 5 * 60

    video = VideoFileClip("/home/radhakrishnan/Desktop/videoplayback.mp4")
    duration = video.duration

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
    else:
        print("fail")


# def get_ip():
#     response = requests.get('https://api64.ipify.org?format=json').json()
#     return response["ip"]


# def get_location():
#     ip_address = get_ip()
#     response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
#     location_data = {
#         "ip": ip_address,
#         "city": response.get("city"),
#         "region": response.get("region"),
#         "country": response.get("country_name")
#     }
#     return location_data


# print(get_location())




# # For Testing
# @router.post("/test")
# async def test(db:Session=Depends(deps.get_db),auth_code:str=Form(...)):
#     # import boto3
    
#     # polly = boto3.client(
#     #             'polly',
#     #             aws_access_key_id=access_key,
#     #             aws_secret_access_key=access_secret,
#     #             region_name="us-east-1",
#     #             )

#     # # Set the parameters for the speech synthesis
#     # output_format = 'mp3'
#     # voice_id = 'Joanna'
#     # text = 'Hello, this is a test of Amazon Polly.'
    
#     # lang = detect(text)
#     # # Call the synthesize_speech() method to generate the audio file
    
#     # response = polly.synthesize_speech(Text=text, VoiceId=voice_id, OutputFormat=output_format)

#     # # Save the audio file to disk
#     # with open('test.mp3', 'wb') as f:
#     #     f.write(response['AudioStream'].read())
#     # playsound("test.mp3")
    
   
   
#     #   ---------------------------------
#     import os
#     from google.cloud import translate_v2 as translate
#     os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/service_account_key.json'
#     client = translate.Client()
   
#     result = client.translate('Hello, how are you?', target_language='ta')
#     print(result['translatedText'])
    
    
    
    
    
# from langdetect import detect
# from gtts import gTTS
# from playsound import playsound
# from profanityfilter import ProfanityFilter
   
# For Testing
# @router.post("/lang")
# async def lang(db:Session=Depends(deps.get_db),auth_code:str=Form(...)):
#     from googletrans import Translator
#     pf=ProfanityFilter()
#     translator = Translator()
#     translated = translator.translate('In the Tamil language, the letters formed with each of the twelve vowels and eighteen consonants are called vowels.', dest='ta')
#     print(translated.text)

#     filtered_text = pf.censor(translated.text)
    
#     # Languages
#     lang = detect(translated.text)
#     print("language",lang)
    
#     tts = gTTS(text=filtered_text,lang='ta')
    
    
#     tts.save("test.mp3")   
#     playsound("test.mp3")
    

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

router = APIRouter() 


@router.post("/video_split")
async def video_split(db:Session=Depends(deps.get_db)):
    clip = VideoFileClip("input_video.mp4")

    # Set the length of each part in seconds
    part_length = 300  # 5 minutes * 60 seconds

    # Calculate the number of parts
    num_parts = int(clip.duration / part_length) + 1

    # Loop through each part and write it to a separate file
    for i in range(num_parts):
        start = i * part_length
        end = min((i + 1) * part_length, clip.duration)
        part = clip.subclip(start, end)
        part.write_videofile(f"output_part_{i}.mp4")

    return "Done"


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
    

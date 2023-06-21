from fastapi import FastAPI, BackgroundTasks
from celery import Celery
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
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
# from better_profanity import profanity

router = APIRouter() 


from profanity import profanity

@router.post("/remove_abusive_words")
async def remove_abusive_words(text:str=Form(None)):
    # language='fr'
    # profanity.load_words(language)
    
    censored = profanity.censor(text)
    return censored


chime = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
            aws_secret_access_key='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',region_name="us-east-1"
            )



@router.post("/create_room")
async def create_room():
    # try:
    response = chime.create_room(
        AccountId='562114208112',
        Name='RawRoom_1',
        # MemberEmail='suryadurai11@gmail.com'
    )
    room_id = response['Room']['RoomId']
    print(f"Chat room created with ID: {room_id}")
    # except :
    #     print(f"Error creating chat room")
        


@router.post("/list_app_instance")
async def list_app_instance():
    response = chime.list_app_instances()

    app_instances = response['AppInstances']
    instance_list=[]
    for app_instance in app_instances:
        app_instance_arn = app_instance['AppInstanceArn']
        instance_list.append(app_instance_arn)
    return instance_list 


@router.post("/create_app_instance")
async def create_app_instance():  

    response = chime.create_app_instance(
        Name='YourAppInstanceName',
        ClientRequestToken='YourUniqueClientRequestToken'
    )

    app_instance_arn = response['AppInstanceArn']
    print(app_instance_arn)
 
 
 

@router.post("/list_channel_arn")
async def list_channel_arn():  
    def get_channel_arn(channel_name, app_instance_arn):
      
        chime = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
                    aws_secret_access_key='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',region_name="us-east-1"
                    )
        response = chime.list_channels(AppInstanceArn=app_instance_arn)
        channels = response['Channels']

        for channel in channels:
            if channel['Name'] == channel_name:
                return channel['ChannelArn']

        return None

    # Example usage
    app_instance_arn = 'arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4'
    channel_name = "channel_1"

    channel_arn = get_channel_arn(channel_name, app_instance_arn)
    if channel_arn:
        print("Channel ARN:", channel_arn)
    else:
        print("Channel not found.")

   
@router.post("/list_bots")
async def list_bots():       
    response = chime.list_bots(
        AccountId='562114208112',
        MaxResults=50,
        NextToken='qwertyuiopasdfg'
    )
    return response

@router.post("/create_channel_arn")
async def create_channel_arn():  
    response = chime.create_channel(
        AppInstanceArn='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4',
        Name='channel_1',
        Mode='UNRESTRICTED',
        Privacy='PUBLIC',
        ChimeBearer='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4'
        
    )
    
    
    region = 'us-east-1'
    aws_account_id = '562114208112'
    app_instance_arn = 'arn:aws:chime:{}:{}:app-instance/abcd1234'.format(region, aws_account_id)
    channel_id = 'channel-1'

    channel_arn = 'arn:aws:chime:{}:{}:app-instance/{}/channel/{}'.format(region, aws_account_id, app_instance_arn, channel_id)
    return channel_arn
    
        
@router.post("/create_app_instance_user")
async def create_app_instance_user(): 
    
    response = chime.create_app_instance_user(
        AppInstanceArn='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4',
        AppInstanceUserId='adb4ff7b-38bc-42fd-b93f-9c3144677ea4',
        Name='Channel_1',
        Metadata='string',
        ClientRequestToken='string',
        Tags=[
            {
                'Key': 'string',
                'Value': 'string'
            },
        ]
        )
    return response
    
    
@router.post("/send_message")
async def send_message(): 
    chime_client=boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
                    aws_secret_access_key='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',region_name="us-east-1"
                    )
    ChannelArn="arn:aws:chime:us-east-1:562114208112:channel/channel_1"
    response = chime_client.send_channel_message(
        ChannelArn=ChannelArn,
        Content='Hello, this is a test message.',
        Persistence='PERSISTENT',
        Type='STANDARD',
        ChimeBearer='arn:aws:chime:us-east-1:562114208112:channel/adb4ff7b-38bc-42fd-b93f-9c3144677ea4'
        )
    message_id = response['MessageId']
    print("Message ID:", message_id)  
    
 
# arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4/user/adb4ff7b-38bc-42fd-b93f-9c3144677ea4

@router.post("/token")
async def token():   
    response = chime.create_app_instance_user(
        AppInstanceArn='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4',
        AppInstanceUserId='adb4ff7b-38bc-42fd-b93f-9c3144677ea4',
        Name='bharath'
            )
    return response



@router.post("/censor_check")
async def censor_check():
    def censor_cut_check(filename, censor_duration_threshold=2, silence_threshold=-40):
        # Load the video or audio file
        if filename.endswith(('.mp4', '.mkv', '.avi')):
            clip = VideoFileClip(filename)
            audio = clip.audio
        elif filename.endswith(('.mp3', '.wav')):
            audio = AudioSegment.from_file(filename)
        else:
            raise ValueError("Unsupported file format.")
       
        # Convert audio to mono (if stereo) for silence detection
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Detect silence segments in the audio
        silent_ranges = detect_silence(audio, min_silence_len=1000, silence_thresh=silence_threshold)

        # Check if any silence segment exceeds the censor duration threshold
        for start, end in silent_ranges:
            duration = (end - start) / 1000  # Convert milliseconds to seconds
            if duration >= censor_duration_threshold:
                return True  # Censor cut detected

        return False  # No censor cut detected
    
    censor_cut_checks=censor_cut_check('/home/surya_maestro/Videos/god.mp4')    
    
    return censor_cut_checks
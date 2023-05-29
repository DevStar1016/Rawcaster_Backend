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
from moviepy.video.io.VideoFileClip import VideoFileClip


router = APIRouter() 
celery_app = Celery("tasks", broker="redis://localhost:8000")

@celery_app.task
def process_data(filename,test,multi_file):
    segment_duration = 5 * 60
    print(test)
    for row in multi_file:
        print(row)
    video = VideoFileClip(filename)   # Video Split ( 5 Minutes)
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
        
        segment_filename = f"video_clip_{random.randint(1111,9999)}{int(datetime.now().timestamp())}.mp4"
        segment.write_videofile(segment_filename, audio_codec="aac")
        
        splited_video_url.append(segment_filename)
        
    # Perform the file processing here
    # This function will run in the background

@router.post("/uploada")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Save the file to a temporary location
    # You can use the file.filename to generate a unique filename or any other logic

    temp_file_path ="/home/surya_maestro/Videos/20minutes1.mp4"
    with open(temp_file_path, "wb") as temp_file:
        while chunk := await file.read(4096):
            temp_file.write(chunk)
    test="sdad"
    # Add the file processing task to the Celery queue
    multi_file=[1,2,3]
    background_tasks.add_task(process_data, temp_file_path,test,multi_file)

    return {"message": "File uploaded and processing started in the background"}
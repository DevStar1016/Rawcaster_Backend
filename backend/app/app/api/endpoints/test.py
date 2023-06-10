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
import cv2

@router.post("/uploada")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Load the video file
    video_path = 'path_to_video_file.mp4'
    video_capture = cv2.VideoCapture(video_path)

    # Define the region to censor (e.g., rectangle coordinates)
    censor_x = 100
    censor_y = 100
    censor_width = 200
    censor_height = 200

    # Loop through each frame in the video
    while video_capture.isOpened():
        # Read the current frame
        ret, frame = video_capture.read()
        
        if not ret:
            break
        
        # Apply the censoring effect
        blurred_region = frame[censor_y:censor_y+censor_height, censor_x:censor_x+censor_width]
        blurred_region = cv2.GaussianBlur(blurred_region, (99, 99), 0)
        frame[censor_y:censor_y+censor_height, censor_x:censor_x+censor_width] = blurred_region
        
        # Display the resulting frame
        cv2.imshow('Censored Video', frame)
        
        # Check for key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture and close all windows
    video_capture.release()
    cv2.destroyAllWindows()

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
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

@router.post("/uploadass")
def process_data():
    try:
    # Code that may raise an exception
        x = 1 / 0
    except Exception as e:
        exception_type = e.__class__
        print(exception_type)

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
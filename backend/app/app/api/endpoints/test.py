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
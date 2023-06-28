# from fastapi import FastAPI, BackgroundTasks
# from celery import Celery
# from fastapi import APIRouter, Depends, Form,File,UploadFile
# from app.models import *
# from app.core.security import *
# from app.utils import *
# from app.api import deps
# from sqlalchemy.orm import Session
# from sqlalchemy import extract
# from datetime import datetime,date
# from typing import List
# from app.core import config
# from moviepy.editor import VideoFileClip
# from pydub import AudioSegment
# # from better_profanity import profanity

# router = APIRouter() 


# from profanity import profanity



# import speech_recognition as sr
# from pydub import AudioSegment
# from pydub.silence import split_on_silence


# @router.post("/sppech_rego")
# async def sppech_rego(text:str=Form(None)):
#     # define the recognizer object
#     r = sr.Recognizer()

#     # load your audio file
#     sound = AudioSegment.from_wav("/home/surya_maestro/Music/Jack Sparrow English Dialogue.wav")

#     # filter out low-frequency background noise
#     filtered_sound = sound.high_pass_filter(1000)

#     # split the filtered audio file into chunks
#     chunks = split_on_silence(filtered_sound, 
#         # specify the minimum silence duration in ms
#         min_silence_len=500, 

#         # specify the silence threshold in dB
#         silence_thresh=filtered_sound.dBFS-14, 

#         # consider only parts of the audio with a length greater than this
#         keep_silence=500
#     )

#     # iterate through each chunk and recognize the speech
#     for i, chunk in enumerate(chunks):
#         # export the chunk to a WAV file
#         chunk.export("chunk{0}.wav".format(i), format="wav")

#         # create a speech recognition object
#         with sr.AudioFile("chunk{0}.wav".format(i)) as source:
#             # adjust the recognizer sensitivity to ambient noise
#             r.adjust_for_ambient_noise(source)

#             # extract audio data from the file
#             audio = r.record(source)

#             # recognize speech using Google Speech Recognition
#             try:
#                 text = r.recognize_google(audio)
#                 print("Chunk {}: {}".format(i+1, text))
#             except sr.UnknownValueError:
#                 print("Chunk {}: Speech Recognition could not understand audio".format(i+1))
#             except sr.RequestError as e:
#                 print("Chunk {}: Could not request results from Speech Recognition service; {0}".format(i+1, e))



# @router.post("/remove_abusive_words")
# async def remove_abusive_words(text:str=Form(None)):
#     # language='fr'
#     # profanity.load_words(language)
    
#     censored = profanity.censor(text)
#     return censored

#                                                         # --------------------- Chime Chat -------------------------------


# @router.post("/censor_check")
# async def censor_check():
#     #     censored_text = text
#     #     censored_indices = predict(text)
#     #     for index in censored_indices:
#     #         censored_text = replace_char_at_index(censored_text, index, '*')
#     #     return censored_text

#     # def replace_char_at_index(text, index, replacement):
#     #     return text[:index] + replacement + text[index+1:]

#     # Text to check for profanity
#     text = "This is a bad word and offensive statement."

#     # Censor profanity in the text
#     censored_text = profanity(text)

#     # Print the censored text
#     print("Censored text:", censored_text)
#     return censored_text
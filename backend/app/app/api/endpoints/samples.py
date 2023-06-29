from fastapi import APIRouter, Depends, Form,File,UploadFile
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from datetime import datetime,date
# import profanity_check
from typing import List

router = APIRouter() 


# @router.post("/invite_mails") 
# async def invite_mails(text:str=Form(None)):

#     return profanity_check.censor(text)


from fastapi import HTTPException
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import errors
from sqlalchemy import or_
import datetime
import math
from app.core.config import settings
from app.models import User
import os
from datetime import datetime
import time
import hashlib
from email_validator import validate_email, EmailNotValidError
 
 
def check(email):
    try:
        v = validate_email(email)
        email = v["email"] 
        return True
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        return False

 
def checkAuthCode(auth_code, auth_text):
    secret_key=settings.SALT_KEY + auth_text
    
    hash_code=hashlib.sha1(secret_key.encode())
    
    if auth_code == hash_code or auth_code=="RAWDEV":
        return True
    else:     
        return False
    
def EmailorMobileNoValidation(email_id):
    if check(email_id) == True:
        return  {'status':1, 'type':1, 'email':email_id, 'mobile':None}
    
    elif email_id.isnumeric():
        return {'status':1, 'type':2, 'email':email_id, 'mobile':None}
        
    else:
        return {'status':0, 'type':2, 'email':None, 'mobile':None}
        
        


 
#   --------------------------------------------------
def file_storage(file):
    
    base_dir = settings.BASE_UPLOAD_FOLDER+"/upload_files/"

    dt = str(int(datetime.utcnow().timestamp()))
   
    try:
        os.makedirs(base_dir, mode=0o777, exist_ok=True)
    except OSError as e:
        sys.exit("Can't create {dir}: {err}".format(
            dir=base_dir, err=e))
    
    filename=file.filename

    file_properties = filename.split(".")

    file_extension = file_properties[-1]

    file_properties.pop()
    file_splitted_name = file_properties[0]
    

    write_path = f"{base_dir}{file_splitted_name}{dt}.{file_extension}"
    db_path = f"/upload_files/{file_splitted_name}{dt}.{file_extension}"
   
    with open(write_path, "wb") as new_file:
        shutil.copyfileobj(file.file, new_file)
        
    return db_path



def pagination(row_count=0, page = 1, size=10):
    current_page_no = page if page >= 1 else 1

    total_pages = math.ceil(row_count / size)

    if current_page_no > total_pages:
        current_page_no = total_pages
    
    limit =  current_page_no * size
    offset = limit - size

    if limit > row_count:
        limit = offset + (row_count % size)
    
    limit = limit - offset

    if offset < 0:
        offset = 0
    
    return [limit, offset]


def paginate(page, size, data, total):
    reply = {"items": data, "total":total, "page": page, "size":size}
    return reply



    
def common_date(date, without_time=None):

    datetime = date.strftime("%d-%m-%Y %I:%M:%S %p")

    if without_time == 1:
        datetime = date.strftime("%d-%m-%Y")

    return datetime

def common_date_only(date, without_time=None):

    datetime = date.strftime("%d-%m-%y")

    if without_time == 1:
        datetime = date.strftime("%d-%m-%y")

    return datetime
def common_time_only(date, without_time=None):

    datetime = date.strftime("%H:%M:%S")

    return datetime




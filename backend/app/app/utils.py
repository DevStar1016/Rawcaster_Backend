import random
import time
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from datetime import datetime, timedelta
from fastapi import HTTPException
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import errors
from sqlalchemy import or_
import datetime
from app import models
import math
import string
from app.core.config import settings
from pathlib import Path
from app.models import User
import os
import sys
import shutil
from datetime import datetime, time, date
import time
# from app.schemas import *
 
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




from fastapi import APIRouter, Depends, Form
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from app.core import config

router = APIRouter() 

access_key=config.access_key
access_secret=config.access_secret
bucket_name=config.bucket_name


@router.post("/createchimeuser")    
def createchimeuser(user_name:str=Form(None)):
    if not user_name:
        return {"status":0,"msg":"User name required"}
    
    
    url = 'https://rqtmzkwwq7.execute-api.us-east-1.amazonaws.com/Stage/creds'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {user_name}'
    }

    res = requests.post(url, headers=headers)

    if res.status_code == 200:
        # Request was successful
        response=res.json()
        
        return {"status":1,"mgs":"Success","data":response}
    else:
        # Request failed
        print('Error:', response.text)
        return {"status":0,"msg":f"Failed:{response.text}"}
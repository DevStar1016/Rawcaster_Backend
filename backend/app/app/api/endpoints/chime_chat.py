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


chime = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
            aws_secret_access_key='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',region_name="us-east-1"
            )


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
    


@router.post("/create_channel")  # Working
async def create_channel(db:Session=Depends(deps.get_db),chime_bearer:str=Form(...),group_name:str=Form(...)):
    
    response = chime.create_channel(
        AppInstanceArn='arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087',
        Name=group_name,
        Mode='UNRESTRICTED',
        Privacy='PUBLIC',
        ChimeBearer=chime_bearer
    )
    # print(chime_bearer)
    return response



@router.post("/addmembers")  # Working
async def addmembers(channel_arn:str=Form(...),chime_bearer:str=Form(...)):
    response = chime.batch_create_channel_membership(
            ChannelArn=channel_arn,
            Type='DEFAULT',
            MemberArns=['arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/user/anon_9eb255a5-877d-4122-96e9-4399fb55ad4d'],
            ChimeBearer=chime_bearer          
        )
    
    # response = chime.list_channel_memberships(
    #     ChannelArn=channel_arn,
    #     Type='DEFAULT',
    #     Role='ADMINISTRATOR',
    #     MaxResults=10,
    #     ChimeBearer=chime_bearer
    # )
    
    return response



@router.post("/send_message")  # Working
async def send_message(channel_arn:str=Form(...),chime_bearer:str=Form(...),message:str=Form(...)):  

    # Send a channel message
    response = chime.send_channel_message(
        ChannelArn=channel_arn,
        Content=message,
        Type='STANDARD',
        Persistence='PERSISTENT',
        ChimeBearer=chime_bearer
    )

    # Check the response
    if response['ResponseMetadata']['HTTPStatusCode'] == 201:
        return 'Channel message sent successfully.'
    else:
        return 'Failed to send channel message.'



@router.post("/delete_channel_membership")  # Working
async def delete_channel_membership(channel_arn:str=Form(...),chime_bearer:str=Form(...),member_id:str=Form(...)):  

    response = chime.delete_channel_membership(
        ChannelArn=channel_arn,
        MemberArn=member_id,
        ChimeBearer=chime_bearer,
    )
    return response



@router.post("/delete_channel")  # Working
async def delete_channel(channel_arn:str=Form(...),chime_bearer:str=Form(...)):  

    response = chime.delete_channel(
        ChannelArn=channel_arn,
        ChimeBearer=chime_bearer
    )
    return response
from fastapi import APIRouter, Depends, Form
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from app.core import config
import datetime
router = APIRouter() 
import uuid

access_key=config.access_key
access_secret=config.access_secret
bucket_name=config.bucket_name



@router.post("/create_meeting")
async def create_meeting(db:Session=Depends(deps.get_db),host_name:str=Form(None)):

    # Create an instance of the Chime client
    chime_client = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
            aws_secret_access_key='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',
            region_name="us-east-1")

    meeting_id = str(uuid.uuid4())  # Generate a unique meeting ID
    
    # start_time = datetime.datetime(2023, 6, 7, 14, 35, 0)  # Replace with the desired start time
    start_time = datetime.datetime.utcnow() + timedelta(minutes=10)  # Start time 10 minutes from now
    end_time = start_time + timedelta(minutes=3) 
    
    try:
        response = chime_client.create_meeting(
            ClientRequestToken=str(uuid.uuid4()),  # Generate a unique request token
            MediaRegion="us-east-1",  # Specify the AWS region for the meeting
            ExternalMeetingId=meeting_id,  # Use the generated meeting ID as the external ID
            MeetingHostId=str(uuid.uuid4()),  # Generate a unique host ID
        
        )
        
        attendee_response = chime_client.create_attendee(
                MeetingId=response['Meeting']['MeetingId'],
                ExternalUserId=host_name if host_name else "Me" 
            )
        
        result={"attendeeResponse":{"Attendee":attendee_response['Attendee']},"meetingResponse":{"Meeting":response['Meeting']}}

        return {"status":1,"msg":"Success","data":result,"owner":1}

    except:
        return {"status":0,"msg":"Failed to Create Meeting"}
     

@router.post("/attendee_meeting")
async def attendee_meeting(db:Session=Depends(deps.get_db),meeting_id:str=Form(None),attendee_name:str=Form(None)):
    
    if not meeting_id:
        return {"status":0,"msg":"Meeting id Required"}
    if not attendee_name:
        return {"status":0,"msg":"Attendee Name Required"}
        
    chime_client = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
            aws_secret_access_key='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',
            region_name="us-east-1")
    
    # Check Meeting is Active or Not
    try:
        response = chime_client.get_meeting(MeetingId=meeting_id)
        # Call the CreateAttendee API to create an attendee for the meeting
        attendee_response = chime_client.create_attendee(
            MeetingId=meeting_id,
            ExternalUserId=attendee_name
        )

        # # Participants 
        # participants_response = chime_client.list_attendees(
        #     MeetingId=meeting_id
        # )

        # attendees = participants_response['Attendees']
        
        result={"attendeeResponse":{"Attendee":attendee_response['Attendee']},"meetingResponse":{"Meeting":response['Meeting']}}
        # return result
        return result
        return {"status":1,"msg":"Success","data":result}
    
        return {"status":1,"msg":"Success","data":result,"participants":attendees,"participants_count":len(attendees)}
    
        
    except chime_client.exceptions.NotFoundException:
        return {'status':0,"msg":"Meeting Expired"}


@router.post("/end_meeting")
async def end_meeting(db:Session=Depends(deps.get_db),meeting_id:str=Form(None)):
    if not meeting_id:
        return {"status":0,"msg":"Meeting Id missing"}
   
    chime_client = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
            aws_secret_access_key='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',region_name="us-east-1")
    try:
        # End the meeting
        response = chime_client.delete_meeting(
            MeetingId=meeting_id
        )
        return {"status":1,"msg":"Success","data":response}
    except:
        return {'status':0,"msg":"Meeting id Not Found"}
        
     
# @router.post("/chec_owner")
# async def chec_owner(db:Session=Depends(deps.get_db),meeting_id:str=Form(None),attendee_id:str=Form(None)):
#     chime = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
#             aws_secret_access_key='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',region_name="us-east-1")

  
#     response = chime.list_attendees(MeetingId=meeting_id)
#     attendees = response['Attendees']
#     return attendees
    
         

# @router.post("/list_meeting_attendees")
# async def list_meeting_attendees(db:Session=Depends(deps.get_db),meeting_id:str=Form(None)):
#     if not meeting_id:
#         return {"status":0,"msg":"Meeting Id required"}
#     try:
#         chime_client = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
#                 aws_secret_access_key='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',
#                 region_name="us-east-1")
#         response = chime_client.list_attendees(
#             MeetingId=meeting_id
#         )

#         attendees = response['Attendees']
#         return {"status":1,"attendees_count":len(attendees),"attendees":attendees}
#     except:
#         return {"status":0,"msg":"Meeting id not found"}
        


# @router.post("/meeting_duration")
# async def meeting_duration(db:Session=Depends(deps.get_db),meeting_id:str=Form(None)):
#     if not meeting_id:
#         return {"status":0,"msg":"meeting id required"}
    
#     chime_client = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
#             aws_secret_access_key='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',region_name="us-east-1")

#     try:
#         # Get meeting details
#         response = chime_client.get_meeting(MeetingId=meeting_id)
#         created_timestamp = response['Meeting']['CreatedTimestamp']

#         # Calculate duration
#         current_time = datetime.now()
#         duration = current_time - created_timestamp

#         # Return duration in seconds
#         return duration.total_seconds()

#     except chime_client.exceptions.NotFoundException:
#         return None

# @router.post("/list_meeting")
# async def list_meeting(db:Session=Depends(deps.get_db)):

#     # Create MediaLive client
#     chime_client = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
#             aws_secret_access_key='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',region_name="us-east-1")
    
#     # List Meeting
#     response = chime_client.list_meetings()
#     meetings = response['Meetings']
#     return meetings 



# @router.post("/get_meeting")
# async def get_meeting(db:Session=Depends(deps.get_db),MeetingId:str=Form(None)):
    
#     chime_client = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
#             aws_secret_access_key='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',
#             region_name="us-east-1")
#     response = chime_client.get_meeting(MeetingId=MeetingId)

    
#     return response




# ---------------------------------------------- Secret --------------------------------------------------------


# #    Create Secret
# import boto3

# # Create a Secrets Manager client
# secrets_manager_client = boto3.client('secretsmanager',  aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
#     aws_secret_access_key='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',
#      region_name="us-east-1")

# # Define the secret name and value
# secret_name = 'my-secret'
# secret_value = {
#     'my-username': 'my-username-value',
#     'my-password': 'my-password-value'
# }

# # Create the secret in Secrets Manager
# response = secrets_manager_client.create_secret(
#     Name=secret_name,
#     SecretString=str(secret_value)
# )

# # Print the ARN (Amazon Resource Name) of the created secret
# print('Created secret ARN:', response['ARN'])


# # Read Secret
# import boto3
# import json

# # Create a Secrets Manager client
# secrets_manager_client = boto3.client('secretsmanager',  aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
#     aws_secret_access_key='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',
#      region_name="us-east-1")

# secret_name = 'my-secret'

# # Retrieve the secret value from Secrets Manager
# response = secrets_manager_client.get_secret_value(SecretId=secret_name)

# # Extract the secret value from the response
# secret_value = response['SecretString']
# # Parse the secret value from JSON to a dictionary
# print(secret_value)


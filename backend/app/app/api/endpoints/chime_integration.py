from fastapi import APIRouter, Depends, Form
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from app.core import config
import datetime
router = APIRouter() 
from pydantic import BaseModel,Field

import uuid

access_key=config.access_key
access_secret=config.access_secret
bucket_name=config.bucket_name


@router.post("/create_meeting")
async def create_meeting(db:Session=Depends(deps.get_db),host_name:str=Form(None)):
    if not host_name:
        return {"status":0,"msg":"Name is missing"}
        
    # Create an instance of the Chime client
    chime_client = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
            aws_secret_access_key='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',
            region_name="us-east-1")

    meeting_id = str(uuid.uuid4())  # Generate a unique meeting ID 
    
    try:
        response = chime_client.create_meeting(
            ClientRequestToken=str(uuid.uuid4()),  # Generate a unique request token
            MediaRegion="us-east-1",  # Specify the AWS region for the meeting
            ExternalMeetingId=meeting_id,  # Use the generated meeting ID as the external ID
            MeetingHostId=str(uuid.uuid4()),  # Generate a unique host ID
        
        )
        
        attendee_response = chime_client.create_attendee(
                MeetingId=response['Meeting']['MeetingId'],
                ExternalUserId=host_name
            )
        
        result={"attendeeResponse":{"Attendee":attendee_response['Attendee']},"meetingResponse":{"Meeting":response['Meeting']}}

        return {"status":1,"msg":"Success","data":result}

    except Exception as e:
        return {"status":0,"msg":f"Failed to Create Meeting.Error:{str(e)}"}
     

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
        
     
     
    #   ---------------------------------  Chime Chat ---------------------------- 
     
chime = boto3.client('chime',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
            aws_secret_access_key='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',region_name="us-east-1"
            )

@router.post("/chime_bearer")   # Working
async def chime_bearer():       

    def create_chime_app_instance_user():
        # Create an Amazon Chime SDK Identity client
        chime_identity_client = boto3.client('chime-sdk-identity',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
                    aws_secret_access_key='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',region_name="us-east-1"
                    )

        # Update the existing App Instance User
        response = chime_identity_client.create_app_instance_user(
            AppInstanceArn='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4',
            AppInstanceUserId='my-user-id',
            Name='mychannel',
            )

        app_instance_user_arn = response['AppInstanceUserArn']

        return app_instance_user_arn
    
    chime_bearer = create_chime_app_instance_user()
    return chime_bearer



@router.post("/create_channel")  # Working
async def create_channel(db:Session=Depends(deps.get_db),token:str=Form(None),group_name:str=Form(None)):
    if not token:
        return {"status":-1,"msg":"Login expired"}
    elif not group_name:
        return {"status":0,"msg":"group name is missing"}
    
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            
            login_user_id=f"{get_token_details.user_id}2"
    
            # Add Bearer User
            chime_identity_client = boto3.client('chime-sdk-identity',aws_access_key_id='AKIAYFYE6EFYG6RJOPMF',
                            aws_secret_access_key='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',region_name="us-east-1"
                            )

            # Update the existing App Instance User
            response = chime_identity_client.create_app_instance_user(
                AppInstanceArn='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4',
                AppInstanceUserId=login_user_id,
                Name=group_name
                )

            chime_bearer = response['AppInstanceUserArn']
            
            response = chime.create_channel(
                AppInstanceArn='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4',
                Name=group_name,
                Mode='UNRESTRICTED',
                Privacy='PRIVATE',
                Metadata='string',
                ChimeBearer=chime_bearer
            )
            print(chime_bearer)
            return response



@router.post("/addmembers")  # Working
async def addmembers(message:str=Form(None),channel_id:str=Form(None)):
    
    response = chime.batch_create_channel_membership(
            ChannelArn='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4/channel/5679933f-db79-4dce-a288-69f4cdfe2577',
            Type='DEFAULT',
            MemberArns=['arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/user/anon_f9dcd5e6-9bde-4464-b415-2de8d6a93cdb'],
            ChimeBearer='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4/user/5392',
        )
    return response
  


@router.post("/send_message")  # Working
async def send_message(message:str=Form(None)):  

    def send_channel_message(channel_arn, content):
        # Send a channel message
        response = chime.send_channel_message(
            ChannelArn=channel_arn,
            Content=content,
            Type='STANDARD',
            Persistence='PERSISTENT',
            ChimeBearer='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4/user/my-user-id'
        )

        # Check the response
        if response['ResponseMetadata']['HTTPStatusCode'] == 201:
            return 'Channel message sent successfully.'
        else:
            return 'Failed to send channel message.'

    # Usage example
    channel_arn = 'arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4/channel/9d4fd6c2-e252-4c9b-ab8c-96df1da313e2'
    message_content = message
    respone=send_channel_message(channel_arn, message_content)
    return respone



@router.post("/list_channel_message")   # Working
async def list_channel_message():

    def list_channel_messages(channel_arn):
        # List channel messages
        response = chime.list_channel_messages(
            ChannelArn=channel_arn,
            SortOrder='ASCENDING',  # Set Assending or Decending
            MaxResults=10,  # Maximum number of messages to retrieve
            ChimeBearer='arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4/user/my-user-id'
        )

        # Process the response
        message_list=[]
        messages = response['ChannelMessages']
        for message in messages:
            message_id = message['MessageId']
            content = message['Content']
            # print(f"Message ID: {message_id}, Content: {content}")
            message_list.append({"message_id":message_id,'content':content})
           
        # Check if there are more messages
        while 'NextToken' in response:
            next_token = response['NextToken']
            response = chime.list_channel_messages(
                ChannelArn=channel_arn,
                NextToken=next_token,
                MaxResults=10
            )
           
            messages = response['ChannelMessages']
            for message in messages:
                message_id = message['MessageId']
                content = message['Content']
                print(f"Message ID: {message_id}, Content: {content}")
        return message_list
    # Usage example
    channel_arn = 'arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4/channel/9d4fd6c2-e252-4c9b-ab8c-96df1da313e2'
    message_list_response=list_channel_messages(channel_arn)
    return message_list_response



     
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


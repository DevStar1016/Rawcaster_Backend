from fastapi import APIRouter, Depends, Form
from app.models import *
from app.core.security import *
from app.utils import checkToken,defaultimage,get_event_detail
from app.api import deps
from sqlalchemy.orm import Session
from app.core import config
import requests
import json,random

router = APIRouter()

access_key = config.access_key
access_secret = config.access_secret
bucket_name = config.bucket_name




#   62.Event Join Validation
@router.post("/externaluserjoin")
async def externalUserJoin(
    db: Session = Depends(deps.get_db),email_id:str=Form(None),
    name:str=Form(None),
    reference_id:str=Form(None)):
    
    if not email_id:
        return {"status": 0, "msg": "Email Id is Missing"}
    if not name:
        return {"status": 0, "msg": "Name is Missing"}
    if not reference_id:
        return {"status": 0, "msg": "Reference Id Required"}
    
    
    checkReference=db.query(Events).filter(Events.ref_id == reference_id).first()
    
    if not checkReference:
        return {"status":0,"msg":"Invalid Meeting Code"}
    else:
        
        event = get_event_detail(db, checkReference.id,None)
        
        currentTimestamp=int(datetime.now().timestamp())
        
        return  {   "status":1,
                    "msg":"Success",
                    "user":{
                        "user_id": int(f"{currentTimestamp}{random.randint(100, 999)}"),
                        "email": email_id,
                        "name": name,
                        "profile_image": defaultimage("profile_img"),
                        "user_status_type": 1
                    },
                    "event":event
                }
    

@router.post("/join_meeting")
def join_meeting(db: Session = Depends(deps.get_db),
        token: str = Form(None),meeting_id: str = Form(None)):
    if not token:
        return {"status": -1, "msg": "Sorry! your login session expired. please login again."}
    
    if not meeting_id:
        return {"status": 0, "msg": "Meeting id required"}
    
    access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
        login_user_id = get_token_details.user_id
        
        headers = {'Content-Type': 'application/json'}
        url = "https://devchimeapi.rawcaster.com/joinmeeting"
        
        data={'userId': login_user_id,'MeetingId':meeting_id}
        try:
            res = requests.post(url, data = json.dumps(data),headers=headers)
            
        except Exception as e:
            return {'status':0,"msg":f"Unable to connect:{e}"}
        
        if res.status_code == 200:
            response = json.loads(res.text)
            try:
                return {"status": 1, "msg": "Success", "attendee": response['result']['Attendee'],"meeting":response['result']['meeting']}
            except:
                return {"status":0,"msg":"Something went wrong"}
        else:
            # Request failed
            print("Error:", (response.text))
            return {"status": 0, "msg": f"Failed:{response.text}"}





@router.post("/attendees")
def attendees(db: Session = Depends(deps.get_db),
        token: str = Form(None),meeting_id: str = Form(None)):
    if not token:
        return {"status": -1, "msg": "Sorry! your login session expired. please login again."}
    
    if not meeting_id:
        return {"status": 0, "msg": "User name required"}
    
    access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
        try:
            url = f"https://devchimeapi.rawcaster.com/getattendeelist/{meeting_id}"
            res = requests.get(url,timeout=30)
            
            if res.status_code == 200:
                response = json.loads(res.text)
            
                return {"status": 1, "msg": "Success", "data":{"Attendees": response['result']['Attendees'],"users":response['result']['users']}}
                
            else:
                print("Error:", (response.text))
                return {"status": 0, "msg": f"Failed:{response.text}"}
        except:
                return {"status":0,"msg":"Something went wrong"}



@router.post("/end_meeting")
def end_meeting(db: Session = Depends(deps.get_db),
        token: str = Form(None),meeting_id: str = Form(None)):
    if not token:
        return {"status": -1, "msg": "Sorry! your login session expired. please login again."}
    
    if not meeting_id:
        return {"status": 0, "msg": "User name required"}
    
    access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
        login_user_id = get_token_details.user_id
        
        headers = {'Content-Type': 'application/json'}
        url = "https://devchimeapi.rawcaster.com/endmeeting"
        
        data={'meetingId':meeting_id}
        try:
            res = requests.post(url, data = json.dumps(data),headers=headers)
            
        except Exception as e:
            return {'status':0,"msg":f"Unable to connect:{e}"}
        
        if res.status_code == 200:
            response = json.loads(res.text)
            try:
                return {"status": 1, "msg": "Success"}
            except:
                return {"status":0,"msg":"Something went wrong"}
        else:
            # Request failed
            print("Error:", (response.text))
            return {"status": 0, "msg": f"Failed:{response.text}"}


@router.post("/exit_meeting")
def exit_meeting(db: Session = Depends(deps.get_db),
        token: str = Form(None),meeting_id: str = Form(None),attendeeId:str=Form(None)):
    if not token:
        return {"status": -1, "msg": "Sorry! your login session expired. please login again."}
    
    if not attendeeId:
        return {"status": 0, "msg": "Attendee id required"}
    
    if not meeting_id:
        return {"status": 0, "msg": "Meeting id required"}
    
    access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
        login_user_id = get_token_details.user_id
        
        headers = {'Content-Type': 'application/json'}
        url = "https://devchimeapi.rawcaster.com/exitmeeting"
        
        data={'meetingId':meeting_id,'attendeeId':attendeeId,"userId":login_user_id}
        try:
            res = requests.post(url, data = json.dumps(data),headers=headers)
            
        except Exception as e:
            return {'status':0,"msg":f"Unable to connect:{e}"}
        
        if res.status_code == 200:
            response = json.loads(res.text)
            try:
                return {"status": 1, "msg": "Success"}
            except:
                return {"status":0,"msg":"Something went wrong"}
        else:
            # Request failed
            print("Error:", (response.text))
            return {"status": 0, "msg": f"Failed:{response.text}"}



# @router.post("/create_meeting")
# async def create_meeting(
#     db: Session = Depends(deps.get_db), host_name: str = Form(None)
# ):
#     if not host_name:
#         return {"status": 0, "msg": "Name is missing"}

#     # Create an instance of the Chime client
#     chime_client = boto3.client(
#         "chime",
#         aws_access_key_id="AKIAYFYE6EFYG6RJOPMF",
#         aws_secret_access_key="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",
#         region_name="us-east-1",
#     )

#     meeting_id = str(uuid.uuid4())  # Generate a unique meeting ID

#     try:
#         response = chime_client.create_meeting(
#             ClientRequestToken=str(uuid.uuid4()),  # Generate a unique request token
#             MediaRegion="us-east-1",  # Specify the AWS region for the meeting
#             ExternalMeetingId=meeting_id,  # Use the generated meeting ID as the external ID
#             MeetingHostId=str(uuid.uuid4()),  # Generate a unique host ID
#         )

#         attendee_response = chime_client.create_attendee(
#             MeetingId=response["Meeting"]["MeetingId"], ExternalUserId=host_name
#         )

#         result = {
#             "attendeeResponse": {"Attendee": attendee_response["Attendee"]},
#             "meetingResponse": {"Meeting": response["Meeting"]},
#         }

#         return {"status": 1, "msg": "Success", "data": result}

#     except Exception as e:
#         return {"status": 0, "msg": f"Failed to Create Meeting.Error:{str(e)}"}


# @router.post("/attendee_meeting")
# async def attendee_meeting(
#     db: Session = Depends(deps.get_db),
#     meeting_id: str = Form(None),
#     attendee_name: str = Form(None),
# ):
#     if not meeting_id:
#         return {"status": 0, "msg": "Meeting id Required"}
#     if not attendee_name:
#         return {"status": 0, "msg": "Attendee Name Required"}

#     chime_client = boto3.client(
#         "chime",
#         aws_access_key_id="AKIAYFYE6EFYG6RJOPMF",
#         aws_secret_access_key="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",
#         region_name="us-east-1",
#     )

#     # Check Meeting is Active or Not
#     try:
#         response = chime_client.get_meeting(MeetingId=meeting_id)
#         # Call the CreateAttendee API to create an attendee for the meeting
#         attendee_response = chime_client.create_attendee(
#             MeetingId=meeting_id, ExternalUserId=attendee_name
#         )

#         # # Participants
#         # participants_response = chime_client.list_attendees(
#         #     MeetingId=meeting_id
#         # )

#         # attendees = participants_response['Attendees']

#         result = {
#             "attendeeResponse": {"Attendee": attendee_response["Attendee"]},
#             "meetingResponse": {"Meeting": response["Meeting"]},
#         }
#         # return result
#         return result
#         return {"status": 1, "msg": "Success", "data": result}

#         return {
#             "status": 1,
#             "msg": "Success",
#             "data": result,
#             "participants": attendees,
#             "participants_count": len(attendees),
#         }

#     except chime_client.exceptions.NotFoundException:
#         return {"status": 0, "msg": "Meeting Expired"}


# @router.post("/end_meeting")
# async def end_meeting(db: Session = Depends(deps.get_db), meeting_id: str = Form(None)):
#     if not meeting_id:
#         return {"status": 0, "msg": "Meeting Id missing"}

#     chime_client = boto3.client(
#         "chime",
#         aws_access_key_id="AKIAYFYE6EFYG6RJOPMF",
#         aws_secret_access_key="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",
#         region_name="us-east-1",
#     )
#     try:
#         # End the meeting
#         response = chime_client.delete_meeting(MeetingId=meeting_id)
#         return {"status": 1, "msg": "Success", "data": response}
#     except:
#         return {"status": 0, "msg": "Meeting id Not Found"}

#     #   ---------------------------------  Chime Chat ----------------------------


# chime = boto3.client(
#     "chime",
#     aws_access_key_id="AKIAYFYE6EFYG6RJOPMF",
#     aws_secret_access_key="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",
#     region_name="us-east-1",
# )


# @router.post("/list_channel_message")  # Working
# async def list_channel_message():
#     def list_channel_messages(channel_arn):
#         # List channel messages
#         response = chime.list_channel_messages(
#             ChannelArn=channel_arn,
#             SortOrder="ASCENDING",  # Set Assending or Decending
#             MaxResults=10,  # Maximum number of messages to retrieve
#             ChimeBearer="arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4/user/my-user-id",
#         )

#         # Process the response
#         message_list = []
#         messages = response["ChannelMessages"]
#         for message in messages:
#             message_id = message["MessageId"]
#             content = message["Content"]
#             # print(f"Message ID: {message_id}, Content: {content}")
#             message_list.append({"message_id": message_id, "content": content})

#         # Check if there are more messages
#         while "NextToken" in response:
#             next_token = response["NextToken"]
#             response = chime.list_channel_messages(
#                 ChannelArn=channel_arn, NextToken=next_token, MaxResults=10
#             )

#             messages = response["ChannelMessages"]
#             for message in messages:
#                 message_id = message["MessageId"]
#                 content = message["Content"]
#                 # print(f"Message ID: {message_id}, Content: {content}")
#         return message_list

#     # Usage example
#     channel_arn = "arn:aws:chime:us-east-1:562114208112:app-instance/adb4ff7b-38bc-42fd-b93f-9c3144677ea4/channel/9d4fd6c2-e252-4c9b-ab8c-96df1da313e2"
#     message_list_response = list_channel_messages(channel_arn)
#     return message_list_response


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







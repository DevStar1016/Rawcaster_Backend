from fastapi import APIRouter, Depends, Form
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from app.core import config
import ast

router = APIRouter()

access_key = config.access_key
access_secret = config.access_secret
bucket_name = config.bucket_name


chime = boto3.client(
    "chime",
    aws_access_key_id=access_key,
    aws_secret_access_key=access_secret,
    region_name="us-east-1",
)


@router.post("/createchimeuser")
def createchimeuser(user_name: str = Form(None)):
    if not user_name:
        return {"status": 0, "msg": "User name required"}

    url = "https://rqtmzkwwq7.execute-api.us-east-1.amazonaws.com/Stage/creds"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_name}",
    }

    res = requests.post(url, headers=headers)

    if res.status_code == 200:
        response = res.json()

        return {"status": 1, "mgs": "Success", "data": response}
    else:
        print("Error:", response.text)
        return {"status": 0, "msg": f"Failed:{response.text}"}



# @router.post("/create_channel")  # Working
def create_channel(chime_bearer: str = Form(...), group_name: str = Form(...)):
    response = chime.create_channel(
        AppInstanceArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087",
        Name=group_name,
        Mode="UNRESTRICTED",
        Privacy="PUBLIC",
        ChimeBearer=chime_bearer,
    )
    return response


# @router.post("/addmembers")  # Working
def addmembers(
    channel_arn: str = Form(...),
    chime_bearer: str = Form(...),
    member_id: Any = Form(..., description="['abc','def']"),
):
    # group_members = ast.literal_eval(member_id) if member_id else []

    response = chime.batch_create_channel_membership(
        ChannelArn=channel_arn,
        Type="DEFAULT",
        MemberArns=member_id,
        ChimeBearer=chime_bearer,
    )

    return response


@router.post("/list_channel_member")  # Working
async def list_channel_member(
    channel_arn: str = Form(...), chime_bearer: str = Form(...)
):
    response = chime.list_channel_memberships(
        ChannelArn=channel_arn,
        Type="DEFAULT",
        Role="ADMINISTRATOR",
        MaxResults=10,
        ChimeBearer=chime_bearer,
    )

    return response


@router.post("/delete_msg")  # Working
async def delete_msg(db: Session = Depends(deps.get_db)):
    response = chime.delete_channel_message(
        ChannelArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/218d6efe-15e1-450e-b4b7-0f4453aeeeb5",
        MessageId="cc18cc90ba9d73c731e675b4d9aac44b7c6d6e9a989b65168c9c46fbe4ba4c03",
        ChimeBearer="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/user/anon_657be7db-40e1-4585-84b8-680ff815ce5e",
    )
    return response


@router.post("/list_channel_msg")  # Working
async def list_channel_msg(db: Session = Depends(deps.get_db), token: str = Form(None)):
    response = chime.list_channel_messages(
        ChannelArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/218d6efe-15e1-450e-b4b7-0f4453aeeeb5",
        SortOrder="ASCENDING",
        MaxResults=50,
        ChimeBearer="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/user/anon_657be7db-40e1-4585-84b8-680ff815ce5e",
    )
    return response


@router.post("/send_message")  # Working
async def send_message(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    group_id: str = Form(None),
    chime_bearer: str = Form(None),
    message: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif message == None or message.strip() == "":
        return {"status": 0, "msg": "message can not be empty."}

    elif not group_id or not group_id.isnumeric():
        return {"status": 0, "msg": "Group Id is missing"}

    elif not chime_bearer or chime_bearer.strip() == "":
        return {"status": 0, "msg": "Bearer is missing"}

    else:
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

            get_group_details = (
                db.query(FriendGroups).filter(FriendGroups.id == group_id).first()
            )
            if get_group_details:
                try:
                    # Send a channel message
                    response = chime.send_channel_message(
                        ChannelArn=get_group_details.group_arn,
                        Content=message,
                        Type="STANDARD",
                        Persistence="PERSISTENT",
                        ChimeBearer=chime_bearer,
                    )

                    # Check the response
                    if response["ResponseMetadata"]["HTTPStatusCode"] == 201:
                        return {
                            "status": 1,
                            "msg": "Channel message sent successfully.",
                        }
                    else:
                        return {"status": 0, "msg": "Failed to send channel message"}

                except Exception as e:
                    return {"status": 0, "msg": f"Message not sent:{e}"}

            else:
                return {"status": 0, "msg": "Invalid Group Id"}


# @router.post("/delete_channel_membership")  # Working
def delete_channel_membership(
    channel_arn: str = Form(...),
    chime_bearer: str = Form(...),
    member_id: str = Form(...),
):
    response = chime.delete_channel_membership(
        ChannelArn=channel_arn,
        MemberArn=member_id,
        ChimeBearer=chime_bearer,
    )
    return response


# @router.post("/delete_channel")  # Working
def delete_channel(channel_arn: str = Form(...), chime_bearer: str = Form(...)):
    response = chime.delete_channel(ChannelArn=channel_arn, ChimeBearer=chime_bearer)
    return response


@router.post("/messaging_session")  # Working
async def messaging_session():
    response = chime.get_messaging_session_endpoint()
    return response



# Mobile CHAT  -  Testing

@router.post("/createChannel")  # Working
def createChannel(chime_bearer: str = Form(...), group_name: str = Form(...)):
    response = chime.create_channel(
        AppInstanceArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087",
        Name=group_name,
        Mode="UNRESTRICTED",
        Privacy="PUBLIC",
        ChimeBearer=chime_bearer,
    )
    return response


@router.post("/addMembers")  # Working
def addMembers(
    channel_arn: str = Form(...),
    chime_bearer: str = Form(...),
    member_id: Any = Form(..., description="['abc','def']"),
):
    print(member_id)
    group_members = ast.literal_eval(member_id) if member_id else []

    response = chime.batch_create_channel_membership(
        ChannelArn=channel_arn,
        Type="DEFAULT",
        MemberArns=group_members,
        ChimeBearer=chime_bearer,
    )

    return response




@router.post("/sendChatMessage")  # Working
async def send_chat_message(
    db: Session = Depends(deps.get_db),
    chime_bearer: str = Form(...),
    message: str = Form(...),
    ):
        
    # Send a channel message
    response = chime.send_channel_message(
        ChannelArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/218d6efe-15e1-450e-b4b7-0f4453aeeeb5",
        Content=message,
        Type="STANDARD",
        Persistence="PERSISTENT",
        ChimeBearer=chime_bearer,
    )

    # Check the response
    if response["ResponseMetadata"]["HTTPStatusCode"] == 201:
        print(response)
        return {
            "status": 1,
            "msg": "Channel message sent successfully.",
        }
    else:
        return {"status": 0, "msg": "Failed to send channel message"}

            

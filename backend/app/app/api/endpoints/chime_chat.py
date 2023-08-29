from fastapi import APIRouter, Depends, Form,File,UploadFile
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from app.core import config

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



@router.post("/send_channel_message")
async def send_channel_message(
    db: Session = Depends(deps.get_db),
    token:str=Form(None),
    channel_id:str=Form(None),
    message: str = Form(None),
    meta_data:str=Form(None)
    ):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
        
    elif channel_id == None or channel_id.strip() == "":
        return {"status": 0, "msg": "Channel id is missing"}

    elif message == None or message.strip() == "":
        return {"status": 0, "msg": "message can not be empty."}

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
            chime_user_id=get_token_details.user.chime_user_id if get_token_details.user_id else None
            
            # file_path=None
            # if meta_data:
                # # File Upload
                # readed_file = meta_data
                # file_ext = os.path.splitext(meta_data.filename)[1]

                # # Upload File to Server
                # uploaded_file_path = await file_upload(
                #     readed_file, file_ext, compress=None)
                
                # # Upload to S3
                # s3_file_path = f"chat/file_upload_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                # result = upload_to_s3(uploaded_file_path, s3_file_path)
                # if result["status"] == 1:
                #     file_path = result["url"]
                # else:
                #     return result
                
        
            # Send a channel message
            response = chime.send_channel_message(
                ChannelArn=channel_id,
                Content=message,
                Type="STANDARD",
                Persistence="PERSISTENT",
                ChimeBearer=chime_user_id,
                Metadata=meta_data if meta_data else ""
            )

            # Check the response
            if response["ResponseMetadata"]["HTTPStatusCode"] == 201:
                return {
                    "status": 1,
                    "msg": "Channel message sent successfully.",
                }
            else:
                return {"status": 0, "msg": "Failed to send channel message"}

            

@router.post("/update_channel_message")  
async def update_channel_message(db:Session=Depends(deps.get_db),
    token:str=Form(None),
    channel_id:str=Form(None),
    message_id:str=Form(None),
    message: str = Form(None)
    ):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
        
    elif channel_id == None or channel_id.strip() == "":
        return {"status": 0, "msg": "Channel id is missing"}
    
    elif message_id == None or message_id.strip() == "":
        return {"status": 0, "msg": "Message Id is missing"}

    elif message == None or message.strip() == "":
        return {"status": 0, "msg": "message can not be empty."}

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
            chime_user_id=get_token_details.user.chime_user_id if get_token_details.user_id else None
        
            # Send a channel message
            response = chime.update_channel_message(
                ChannelArn=channel_id,
                MessageId=message_id,
                Content=message,
                ChimeBearer=chime_user_id,
            )
            # Check the response
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                return {
                    "status": 1,
                    "msg": "Channel message sent successfully.",
                }
            else:
                return {"status": 0, "msg": "Failed to send channel message"}
            


@router.post("/list_channel_message") 
async def list_channel_message(db: Session = Depends(deps.get_db), token: str = Form(None),channel_id:str=Form(None),next_page_token:str=Form(None)):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif channel_id == None or channel_id.strip() == "":
        return {"status": 0, "msg": "Channel Id missing"}
    
    elif next_page_token and next_page_token.strip() == "":
        return {"status": 0, "msg": "Next page token is invalid"}
    
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
            chime_user_id = get_token_details.user.chime_user_id if get_token_details.user_id else None
            
            try:
                params=({ "ChannelArn":channel_id,
                        "SortOrder":"DESCENDING",
                        "MaxResults":10,
                        "ChimeBearer":chime_user_id,
                        "NextToken":next_page_token
                        } 
                        if next_page_token 
                        else{ 
                        "ChannelArn":channel_id,
                        "SortOrder":"DESCENDING",
                        "MaxResults":50,
                        "ChimeBearer":chime_user_id,
                        
                        })
                
                response = chime.list_channel_messages(
                        **params
                    )
                
                return {"status":1,"msg":"Success","data":{"next_page_token":response['NextToken'] if 'NextToken' in response else None,
                                                           "messages":response['ChannelMessages']}}
            except Exception as e:
                return {
                "status": 0,
                "msg": f"Something went wrong:{e}",
            }
                


@router.post("/delete_channel_message")  # Working
async def delete_channel_message(db: Session = Depends(deps.get_db),token:str=Form(None),channel_id:str=Form(None)):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif channel_id == None or channel_id.strip() == "":
        return {"status": 0, "msg": "Channel Id missing."}
        
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
        chime_user_id = get_token_details.user.chime_user_id if get_token_details.user_id else None
    
        response = chime.delete_channel_message(
            ChannelArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/218d6efe-15e1-450e-b4b7-0f4453aeeeb5",
            MessageId="cc18cc90ba9d73c731e675b4d9aac44b7c6d6e9a989b65168c9c46fbe4ba4c03",
            ChimeBearer=chime_user_id
        )
        return response



@router.post("/list_channel_membership")  # Working
async def list_channel_membership():
    response = chime.list_channel_memberships(
            ChannelArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/0d4dec35-c467-41ae-8933-47cfdceb8884"
        )
    # Step 2: Find admin membership
    admin_membership = None
    for membership in response['ChannelMemberships']:
        if membership.get('Type') == 'Administrator':
            admin_membership = membership
            break
    return admin_membership
    if admin_membership:
        # Step 3: Get user details
        admin_user_id = admin_membership['Member']['UserId']
        admin_user_details = chime.get_user(UserName=admin_user_id)
        admin_user_name = admin_user_details['User']['UserName']

        print(f"Administrator of the channel: {admin_user_name}")
    else:
        print("No administrator found for the channel.")
    
    return response


@router.post("/delete")  # Working
async def delete():
    response = chime.delete_channel_message(
            ChannelArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/0d4dec35-c467-41ae-8933-47cfdceb8884",
            MessageId="8163613907bd5d67dae7ca38c15f4234fa64ee1aa24111d822b23a7dd192e753",
            ChimeBearer='arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/user/anon_657be7db-40e1-4585-84b8-680ff815ce5e'
        )
    return response



# @router.post("/send_msg")  # Working
# async def send_msg():
#     # Send a channel message
#     response = chime.send_channel_message(
#         ChannelArn='arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/0d4dec35-c467-41ae-8933-47cfdceb8884',
#         Content='test',
#         Type="STANDARD",
#         Persistence="PERSISTENT",
#         ChimeBearer='arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/user/anon_657be7db-40e1-4585-84b8-680ff815ce5e',
#     )
#     return response



# Mobile CHAT  -  Testing

# @router.post("/createChannel")  # Working
# def createChannel(chime_bearer: str = Form(...), group_name: str = Form(...)):
#     response = chime.create_channel(
#         AppInstanceArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087",
#         Name=group_name,
#         Mode="UNRESTRICTED",
#         Privacy="PUBLIC",
#         ChimeBearer=chime_bearer,
#     )
#     return response

# import ast

# @router.post("/addMembers")  # Working
# def addMembers(
#     channel_arn: str = Form(...),
#     chime_bearer: str = Form(...),
#     member_id: Any = Form(..., description="['abc','def']"),
# ):
#     print(member_id)
#     group_members = ast.literal_eval(member_id) if member_id else []

#     response = chime.batch_create_channel_membership(
#         ChannelArn=channel_arn,
#         Type="DEFAULT",
#         MemberArns=group_members,
#         ChimeBearer=chime_bearer,
#     )

#     return response



# @router.post("/list_channel_member")  # Working
# async def list_channel_member(
#     channel_arn: str = Form(...), chime_bearer: str = Form(...)
# ):
#     response = chime.list_channel_memberships(
#         ChannelArn=channel_arn,
#         Type="DEFAULT",
#         Role="ADMINISTRATOR",
#         MaxResults=10,
#         ChimeBearer=chime_bearer,
#     )

#     return response


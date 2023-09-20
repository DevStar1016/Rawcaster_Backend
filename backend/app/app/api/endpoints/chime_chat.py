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

# import ast
# @router.post("/addmembers")  # Working
def addmembers(
    channel_arn: str = Form(...),
    chime_bearer: str = Form(...),
    member_id: Any = Form(..., description="['abc','def']"),
):
    # group_members = ast.literal_eval(member_id) if member_id else []
    # member_id=json.loads(member_id)
   
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
            print(chime_user_id)
            # Send a channel message
            response = chime.send_channel_message(
                ChannelArn=channel_id,
                Content=message,
                Type="STANDARD",
                Persistence="PERSISTENT",
                ChimeBearer=chime_user_id,
                Metadata=meta_data if meta_data else ""
            )

                # arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/user/anon_b71c2ee9-b38b-45c1-b1f7-9d69c132444c


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
                


@router.post("/auto_group_channel_create")  
async def auto_group_channel_create(db: Session = Depends(deps.get_db),token:str=Form(None),group_id:int=Form(None)):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
            }
    elif not group_id:
         return {"status": 0, "msg": "Group Id missing."}
    
    else:
        getFriendGroup=db.query(FriendGroups).filter(FriendGroups.id == group_id).first()

        if getFriendGroup and getFriendGroup.group_arn == None and getFriendGroup.user.chime_user_id:
            # CreateChannel
            if not getFriendGroup.group_arn:
                
                createchannel=create_channel(chime_bearer=getFriendGroup.user.chime_user_id,
                                            group_name=getFriendGroup.group_name)
                channel_arn = (
                                createchannel["ChannelArn"]
                                if createchannel
                                else None
                            )
            else:
                channel_arn=getFriendGroup.group_arn
                
            if channel_arn:               
                getFriendGroup.group_arn = channel_arn
                
                getGroupMembers=db.query(FriendGroupMembers.user_id).filter(
                    FriendGroupMembers.group_id == getFriendGroup.id
                    ).all()
                
                for member in getGroupMembers:
                    
                    get_user=db.query(User).filter(User.id ==member.user_id).first()
                    # Add Members in Channel
                    usr_arn=None
                    if get_user:
                        if not get_user.chime_user_id: 
                            # Add User in Chime Channel
                            create_chat_user = chime_chat.createchimeuser(get_user.email_id if get_user.email_id else get_user.mobile_no)
                            if create_chat_user["status"] == 1:
                                user_arn = create_chat_user["data"][
                                    "ChimeAppInstanceUserArn"
                                ]
                                # Update User Chime ID
                                get_user.chime_user_id=user_arn
                                db.commit()
                                usr_arn=user_arn
                        else:
                            usr_arn=get_user.chime_user_id
                                      
                        addMemberResponse=addmembers(channel_arn=channel_arn,
                                    chime_bearer=getFriendGroup.user.chime_user_id,
                                    member_id=[usr_arn])
                        print(1)
                db.commit()
                return {"status":1,"msg":"Success","channel_arn":channel_arn}
                    
                
            else:
                return {"status": 0, "msg": "group creation failed"}
            
        else:
            
            return {"status": 1, "msg": "Already Created","channel_arn":getFriendGroup.group_arn}
            



@router.post("/auto_individual_channel_create")  
async def auto_individual_channel_create(db: Session = Depends(deps.get_db),token:str=Form(None),friend_id:int=Form(None)):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
            }
    elif not friend_id:
        return {"status":0,"msg":"Friend Id required"}
    else:
        
        access_token = checkToken(db, token)
        if not access_token:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )

            login_user_id = get_token_details.user_id
            
            getMyFriend=db.query(MyFriends).filter(or_(and_(MyFriends.sender_id == friend_id,MyFriends.receiver_id == login_user_id),and_(MyFriends.sender_id == login_user_id,MyFriends.receiver_id == friend_id)),MyFriends.status == 1).first()
            
            if getMyFriend and getMyFriend.channel_arn == None:
                # CreateChannel
                userId= getMyFriend.sender_id if getMyFriend.sender_id == login_user_id else getMyFriend.receiver_id
                getUser=db.query(User.chime_user_id).filter(User.id == userId).first()
                
                set_unique_channel=f"RAWCAST{int(datetime.datetime.utcnow().timestamp())}"
                createchannel=create_channel(chime_bearer=getUser.chime_user_id,
                                            group_name=set_unique_channel)
                channel_arn = (
                                createchannel["ChannelArn"]
                                if createchannel
                                else None
                            )
                    
                if channel_arn:               
                    getMyFriend.channel_arn = channel_arn
                    
                    memberId=getMyFriend.receiver_id if getMyFriend.sender_id != login_user_id else getMyFriend.sender_id
                    createChimeUser=db.query(User).filter(User.id == memberId).first()
                    memberARN=None
                    if createChimeUser and createChimeUser.chime_user_id == None:
                        create_chat_user = chime_chat.createchimeuser(createChimeUser.email_id if createChimeUser.email_id else createChimeUser.mobile_no)
                        if create_chat_user["status"] == 1:
                            user_arn = create_chat_user["data"][
                                "ChimeAppInstanceUserArn"
                            ]
                            # Update User Chime ID
                            createChimeUser.chime_user_id=user_arn
                            db.commit()
                            memberARN=user_arn
                        
                        
                    else:
                        memberARN=createChimeUser.chime_user_id
                    
                    addMemberResponse=addmembers(channel_arn=channel_arn,
                                chime_bearer=getUser.chime_user_id,
                                member_id=[memberARN])
                    db.commit()
                    return {"status":1,"msg":"Success","channel_arn":channel_arn}
                        
                    
                else:
                    return {"status": 0, "msg": "group creation failed"}
                
            else:
                return {"status": 1, "msg": "Already Created","channel_arn":getMyFriend.channel_arn if getMyFriend.channel_arn else None}


# @router.post("/delete_channel_message")  # Working
# async def delete_channel_message(db: Session = Depends(deps.get_db),token:str=Form(None),channel_id:str=Form(None)):
#     if token == None or token.strip() == "":
#         return {
#             "status": -1,
#             "msg": "Sorry! your login session expired. please login again.",
#         }
#     elif channel_id == None or channel_id.strip() == "":
#         return {"status": 0, "msg": "Channel Id missing."}
        
#     access_token = checkToken(db, token)
    
#     if access_token == False:
#         return {
#             "status": -1,
#             "msg": "Sorry! your login session expired. please login again.",
#         }

#     else:
#         get_token_details = (
#             db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
#         )
#         chime_user_id = get_token_details.user.chime_user_id if get_token_details.user_id else None
    
#         response = chime.delete_channel_message(
#             ChannelArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/218d6efe-15e1-450e-b4b7-0f4453aeeeb5",
#             MessageId="cc18cc90ba9d73c731e675b4d9aac44b7c6d6e9a989b65168c9c46fbe4ba4c03",
#             ChimeBearer=chime_user_id
#         )
#         return response



@router.post("/list_channel_membership")  # Working
async def list_channel_membership():
    response = chime.list_channel_memberships(
            ChannelArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/b4a15833-e97c-4986-939b-7d73a12724ad",
            ChimeBearer="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/user/anon_baa7c3ca-d77a-48e6-b345-22a2d030c269"
        )
    # Step 2: Find admin membership
    admin_membership = None
    for membership in response['ChannelMemberships']:
        if membership.get('Type') == 'Administrator':
            admin_membership = membership
            break
    
    if admin_membership:
        # Step 3: Get user details
        admin_user_id = admin_membership['Member']['UserId']
        admin_user_details = chime.get_user(UserName=admin_user_id)
        admin_user_name = admin_user_details['User']['UserName']

        print(f"Administrator of the channel: {admin_user_name}")
    else:
        print("No administrator found for the channel.")
    
    return response


# @router.post("/delete")  # Working
# async def delete():
#     response = chime.delete_channel_message(
#             ChannelArn="arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/channel/0d4dec35-c467-41ae-8933-47cfdceb8884",
#             MessageId="8163613907bd5d67dae7ca38c15f4234fa64ee1aa24111d822b23a7dd192e753",
#             ChimeBearer='arn:aws:chime:us-east-1:562114208112:app-instance/6ea8908f-999b-4b3d-9fae-fa1153129087/user/anon_657be7db-40e1-4585-84b8-680ff815ce5e'
#         )
#     return response



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


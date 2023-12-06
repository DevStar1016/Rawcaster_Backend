from fastapi import APIRouter, Depends, Form
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
import boto3
import json

# Set the AWS region
region = "us-east-1"

router = APIRouter()

access_key = config.access_key
access_secret = config.access_secret
bucket_name = config.bucket_name


client = boto3.client('secretsmanager',  aws_access_key_id=access_key,
            aws_secret_access_key=access_secret,
            region_name="us-east-1")


# # Create Secrets
@router.post("/createsecret")
async def createsecret(db:Session=Depends(deps.get_db)):
    # Create the secret name
    secret_name = "dev_rawcaster_credentials"

    # Create the secret value
    secret_value = """
    {
    }
    """
    # Create the secret
    response = client.create_secret(SecretString=secret_value,Name=secret_name
    )
    return response


@router.post("/get_secret")
async def get_secret(db:Session=Depends(deps.get_db),secret_name:str=Form(None)):
     
    get_secret_value_response = client.get_secret_value(SecretId='rawcaster_dev_credentials')
    
    data=get_secret_value_response['SecretString']
    return data

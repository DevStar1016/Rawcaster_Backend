from typing import Any, Dict, List, Optional, Union, TypeVar, Generic

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, validator
from fastapi import Query
from fastapi_pagination.default import Page as BasePage, Params as BaseParams
import pytz 
from urllib.parse import quote  

T = TypeVar("T")

class Params(BaseParams):
    size: int = Query(500, gt=0, le=1000, description="Page size")

class Page(BasePage[T], Generic[T]):
    __params_type__ = Params


base_domain = "http://localhost"
base_url =""
base_dir="/var/www/html"
base_domain_url = ""

base_url_segment = "/rawcaster"
base_upload_folder = "local_uploads"

# CBE
# data_base ='mysql+pymysql://python:%s@dev.rawcaster.com/rawcaster' % quote('W3solutions123!@#')

# Dev
# data_base ='mysql+pymysql://python:%s@dev.rawcaster.com/rawcaster' % quote('W3solutions123!@#')

# 108 DB
# data_base = "mysql+pymysql://maemysqluser:MaeNewMysql2@2@@192.168.1.109/rawcaster"
data_base ='mysql+pymysql://maemysqluser:%s@cbe.themaestro.in/rawcaster' % quote('MaeNewMysql2@2@')



api_doc_path = "/docs"

class Settings(BaseSettings):
    API_V1_STR: str = base_url_segment
    BASE_UPLOAD_FOLDER: str = base_upload_folder
    BASEURL:str=base_url
    BASE_DIR=base_dir
    SALT_KEY:str="MaeRaw7sj5d@Pgk*LO7!e4ubz&8b"
    SECRET_KEY:str="MaeRaw567#&ghtDiuc@#9854*sG!"

    DATA_BASE:str = data_base
    BASE_DOMAIN:str = base_domain
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    BASE_DOMAIN_URL:str = base_domain_url
    API_DOC_PATH:str = api_doc_path
    otp_resend_remaining_sec:int = 120
    tz_NY = pytz.timezone('Asia/Kolkata')  


    SERVER_NAME:str = "Rawcaster"
    ROOT_SERVER_BASE_URL:str =""
    SERVER_HOST:AnyHttpUrl="http://localhost:8000"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:8000",  "http://localhost:8080", "http://localhost:3000","https://192.168.1.66:8010","https://192.168.1.66",
                                              "http://localhost:3001", "http://localhost:3002", "https://cbe.themaestro.in", "http://cbe.themaestro.in","https://dev.rawcaster.com"
                                              ]       
    
    PROJECT_NAME:str = "Rawcaster"

    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v

        return data_base

settings = Settings()
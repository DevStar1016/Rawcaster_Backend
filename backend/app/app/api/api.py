from fastapi import APIRouter
from .endpoints import (
    chime_meeting,
    webservices,
    webservices_2,
    chime_meeting,
    chime_chat,
    elastic
)

api_router = APIRouter()

api_router.include_router(elastic.router, tags=["Latency"])

api_router.include_router(chime_chat.router, tags=["Chime Chat"])

api_router.include_router(chime_meeting.router, tags=["Chime Meeting"])

api_router.include_router(webservices_2.router, tags=["Webservices 2"])

api_router.include_router(webservices.router, tags=["Webservices"])


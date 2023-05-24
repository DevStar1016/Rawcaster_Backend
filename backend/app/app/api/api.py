from fastapi import APIRouter
from .endpoints import webservices,webservices_2
api_router = APIRouter()

api_router.include_router(webservices_2.router, tags=["Webservices 2"])

api_router.include_router(webservices.router, tags=["Webservices"])

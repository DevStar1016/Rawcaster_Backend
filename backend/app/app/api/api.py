from fastapi import APIRouter
from .endpoints import webservices,webservices_2,test
api_router = APIRouter()

api_router.include_router(test.router, tags=["Webservices 3"])

api_router.include_router(webservices_2.router, tags=["Webservices 2"])

api_router.include_router(webservices.router, tags=["Webservices"])

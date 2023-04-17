from fastapi import APIRouter
from .endpoints import webservices,test
api_router = APIRouter()

api_router.include_router(test.router, tags=["Work Sheet"])

api_router.include_router(webservices.router, tags=["Webservices"])


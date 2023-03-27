from fastapi import APIRouter
from .endpoints import webservices
api_router = APIRouter()


api_router.include_router(webservices.router, tags=["Webservices"])


from fastapi import APIRouter
from .endpoints import webservices,webservices_2,chime_integration,test
api_router = APIRouter()

# api_router.include_router(test.router, tags=["Test"])

api_router.include_router(chime_integration.router, tags=["Chime"])

api_router.include_router(webservices_2.router, tags=["Webservices 2"])

api_router.include_router(webservices.router, tags=["Webservices"])

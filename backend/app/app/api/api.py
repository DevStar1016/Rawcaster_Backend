from fastapi import APIRouter

from .endpoints import login,webservices

api_router = APIRouter()
 

api_router.include_router(login.router, tags=["Login"])
api_router.include_router(webservices.router, tags=["User"])


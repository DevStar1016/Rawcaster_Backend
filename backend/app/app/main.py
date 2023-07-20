from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import logging

import sys

sys.path.append("../")

from app.api.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/rawcaster/openapi.json",
)


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    uvicorn_logger = logging.getLogger("uvicorn")
    access_logger = logging.getLogger("uvicorn.access")

    # Set up a custom formatter for both the uvicorn and access loggers
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

    # Set the formatter for the uvicorn logger (error logs)
    for handler in uvicorn_logger.handlers:
        handler.setFormatter(formatter)

    # Set the formatter for the access logger
    for handler in access_logger.handlers:
        handler.setFormatter(formatter)


app.include_router(api_router, prefix=settings.API_V1_STR)

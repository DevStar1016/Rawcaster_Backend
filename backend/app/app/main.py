from fastapi import FastAPI, Request, status
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import sys
sys.path.append('../')
from app.api.api import api_router
from app.core.config import settings
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse

from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(docs_url=settings.API_DOC_PATH,
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

# app.mount("/static", StaticFiles(directory="static"), name="static")
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(),
                 }),
    )


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
# from app.api.endpoints import wttest
# if __name__ == '__main__':
    
#     wttest.run()
app.include_router(api_router, prefix=settings.API_V1_STR)

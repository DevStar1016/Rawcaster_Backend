from fastapi import FastAPI
import redis
from fastapi import APIRouter, Depends, Form, File, UploadFile


router = APIRouter()
cache = redis.Redis(host='raew7no6l92n8p4-001.raew7no6l92n8p4.rljwzo.use1.cache.amazonaws.com', port=6379, db=0)

@router.get("/test11")
def get_data():
    value = cache.get("key")
    if value is None:
        # Value not found in cache, fetch from the database
        value = fetch_data_from_database()
        cache.set("key", value)
    return {"data": value}
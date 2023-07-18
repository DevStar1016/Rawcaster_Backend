from fastapi import FastAPI
import redis
from fastapi import APIRouter, Depends, Form, File, UploadFile


router = APIRouter()

@router.get("/elastic_connection")
def elastic_connection():
    from redis import Redis

    cache_endpoint = 'raew7no6l92n8p4-001.raew7no6l92n8p4.rljwzo.use1.cache.amazonaws.com'
    service_port = 6379
    redis = Redis(host=cache_endpoint, port=6379)

    try:
        cache_is_working = redis.ping()    
        print('I am Redis. Try me. I can remember things, only for a short time though :)')
    except Exception as e:
        print('EXCEPTION: host could not be accessed ---> ', repr(e))

from fastapi import FastAPI
import redis
from fastapi import APIRouter, Depends, Form, File, UploadFile


router = APIRouter()
cache = redis.Redis(host='raew7no6l92n8p4-001.raew7no6l92n8p4.rljwzo.use1.cache.amazonaws.com', port=6379, db=0)

@router.post("/elastic_connection")
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
        
    
    
# Replace 'your_elasticache_endpoint' and 'your_elasticache_port' with your actual ElastiCache endpoint and port
elasticache_endpoint = 'raew7no6l92n8p4-001.raew7no6l92n8p4.rljwzo.use1.cache.amazonaws.com'
elasticache_port = 6379

# Create a Redis client
redis_client = redis.StrictRedis(host=elasticache_endpoint, port=elasticache_port, decode_responses=True)



@router.post("/read_root")
def read_root():
    # Write data to Redis
    redis_client.set("key", "value")

    # Read data from Redis
    value = redis_client.get("key")
    return {"message": f"Value in Redis: {value}"}


@router.post("/read_root1")
def read_root1():
    return "Success"
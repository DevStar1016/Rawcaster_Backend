from fastapi import FastAPI
import redis
from fastapi import APIRouter, Depends, Form, File, UploadFile


router = APIRouter()


# cache = redis.Redis(host='raew7no6l92n8p4-001.raew7no6l92n8p4.rljwzo.use1.cache.amazonaws.com', port=6379, db=0)

# @router.get("/test11")
# def get_data():
#     print('test')
#     value = cache.get("key")
#     print(value)
#     if value is None:
#         # Value not found in cache, fetch from the database
#         value = fetch_data_from_database()
#         cache.set("key", value)
#     return {"data": value}

# import aioredis

# async def connect_to_redis():
#     redis_pool = await aioredis.create_redis_pool('redis://raew7no6l92n8p4-001.raew7no6l92n8p4.rljwzo.use1.cache.amazonaws.com:6379')

# @router.on_event("startup")
# async def startup_event():
#     await connect_to_redis()
    

# @router.get('/cache/{key}')
# async def get_value_from_cache(key: str):
#     value = await redis_pool.get(key)
#     if value is None:
#         return {'message': 'Key not found'}
#     else:
#         return {'key': key, 'value': value.decode('utf-8')}
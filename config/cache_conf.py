#redis缓存配置
import json
import redis.asyncio as redis
from typing import Any

REDIS_HOST="redis://:123456@127.0.0.1:6379/0"
# REDIS_PORT=6379
# REDIS_DB=0
#创建redis对象
# redis_client=redis.Redis(
#     host=REDIS_HOST, #redis服务器的主机地址
#     port=REDIS_PORT,#redis服务器的端口号
#     db=REDIS_DB,#redis数据库编号，0-15
#     decode_responses=True#默认是False，表示返回的是字节，True表示返回的是字符串，表示是否将字节数据解码为字符串
# )

redis_client=redis.from_url(
    url=REDIS_HOST,
    decode_responses=True)
#true表示返回字符串，而非字节)
#设置和读取（两种方法：字符串和列表或字典）

#读取缓存：字符串类型
async def get_cache(key:str):
    # return await redis_client.get(key)
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败：{e}")
        return None

#读取缓存：列表或字典类型
async def get_json_cache(key:str):
    try:
        data=await redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"获取缓存失败：{e}")
        return None

#设置缓存,setex(key,expire,value),expire:过期时间：3600s
async def set_cache(key:str,value:Any,expire:int=3600):
    try:
        if isinstance(value,(dict,list)):
            #转字符串再存
            value=json.dumps(value,ensure_ascii=False) #ensure_ascii=False表示不转义,中午正常保存
        await redis_client.setex(key,expire,value)
        return True
    except Exception as e:
        print(f"设置缓存失败：{e}")
        return False
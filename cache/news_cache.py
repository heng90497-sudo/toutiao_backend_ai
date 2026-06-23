#新闻相关的缓存方法：新闻分类的读取和写入
# key-value
from typing import List, Dict, Any, Optional
from config.cache_conf import get_json_cache,set_cache

CATEGORIES_KEY="news:categories"
NEW_LIST_PREFIX="news_list:"

#获取新闻分类缓存
async def get_cached_categories():
    return await get_json_cache(CATEGORIES_KEY)

#写入新闻分类缓存：缓存的数据，过期时间
#expire过期时间：分类、配置7200秒，列表600秒，详情1800秒，验证码120秒->数据越稳定，缓存越持久
async def set_cache_categories(data:List[Dict[str,Any]],expire:int=7200):
    return await set_cache(CATEGORIES_KEY,data,expire)

#写入缓存-新闻列表,为了确保key的唯一性，设计： key="news_list:分类id：页码：每页数量+列表数据+过期时间"
async def set_cache_news_list(category_id:Optional[int],page:int,page_size:int,new_list:List[Dict[str,Any]],expire:int=1800):
    #category_id可能不存在
    category_part=category_id if category_id else "all"
    #定制key
    key=f"{NEW_LIST_PREFIX}{category_part}:{page}:{page_size}"
    return await set_cache(key,new_list,expire)

#获取缓存-新闻列表
async def get_cache_news_list(category_id:Optional[int],page:int,page_size:int):
    category_part=category_id if category_id else "all"
    key=f"{NEW_LIST_PREFIX}{category_part}:{page}:{page_size}"
    return await get_json_cache(key)
#新闻相关数据库操作
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select,func,update

from models.news import News_category,News
from sqlalchemy.ext.asyncio import AsyncSession
from cache.news_cache import get_cached_categories, set_cache_categories, get_cache_news_list, set_cache_news_list
from utils.base import NewsItemBase


#获取分类
async def get_news_category(db:AsyncSession,skip:int=0,limit:int=100):
    #先尝试从缓存中获取数据
    cached_categories=await get_cached_categories()
    if cached_categories:
        return cached_categories

    #缓存中没有，从数据库中获取数据
    stmt=select(News_category).offset(skip).limit(limit)
    res=await db.execute(stmt)
    cat=res.scalars().all()#这是orm数据
    #数据库数据写入缓存
    if cat:
        #用jsonable_encoder转换成json数据
        cat=jsonable_encoder(cat)
        await set_cache_categories(cat)

    return cat

#查询指定分类下的新闻列表
async def get_news_list(db:AsyncSession,category_id,skip:int=0,limit:int=100):
    #先尝试从缓存数据中获取数据
    # 如果缓存中没有数据，则从数据库中获取数据

    #跳过数量skip=(页码-1)*每页数量，页码=skip//每页数量+1
    page=skip//limit+1
    cached_news=await get_cache_news_list(category_id,page,limit)#这里cached_news是Json格式，
    if cached_news:
        # 而前端要求返回的是ORM,所以要转成ORM格式
        return [News(**item) for item in cached_news]

    stmt=select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    res=await db.execute(stmt)
    news_list=res.scalars().all() ##这是ORM数据

    #数据写入缓存
    if news_list:
        # 用jsonable_encoder转换成json数据，方法1：await set_cache_news_list(category_id,page,limit,jsonable_encoder(news_list))
        #方法2：先把ORM转化为Pydantic模型类，再转化为字典
        #by_alias=False:不用别名，模型类中的别名是给前端用的，这里给后端用，不用别名
        new_data=[NewsItemBase.model_validate( item).model_dump(mode="json",by_alias=False) for item in news_list]
        await set_cache_news_list(category_id,page,limit,new_data)

    return news_list

#查询指定分类下的数量
async def get_news_count(db:AsyncSession,category_id:int):
    stmt=select(func.count(News.id)).where(News.category_id == category_id)
    res=await db.execute(stmt)
    return res.scalar_one()

#查询指定id
async def get_news(db:AsyncSession,news_id:int):
    stmt=select(News).where(News.id == news_id)
    res=await db.execute(stmt)
    return res.scalar_one_or_none()

#新闻浏览量增加1
async def increase_news_views(db:AsyncSession,news_id:int):
    stmt=update(News).where(News.id == news_id).values(views=News.views + 1)
    res=await db.execute(stmt)
    await db.commit()
    #检查数据库是否真的修改了数据，返回True
    return res.rowcount>0

#推荐相关新闻09
#order_by:排序，desc:降序，默认是升序
async def get_related_news(db:AsyncSession,news_id:int,category_id:int,limit:int=5):
    stmt=select(News).where(
        News.category_id == category_id,
        News.id != news_id,
    ).order_by(
        News.views.desc(),
        News.publish_time.desc(),
    ).limit(limit)
    res=await db.execute(stmt)
    related_news=res.scalars().all()
    #列表推导式，得到核心数据
    return [ {
        "id": news_detail.id,
        "title": news_detail.title,
        "content": news_detail.content,
        "image": news_detail.image,
        "author": news_detail.author,
        "publishTime": news_detail.publish_time,
        "categoryId": news_detail.category_id,
        "views": news_detail.views,
    }for news_detail in related_news]
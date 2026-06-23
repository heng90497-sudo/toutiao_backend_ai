#新闻相关数据库操作
from sqlalchemy import select,func,update

from models.news import News_category,News
from sqlalchemy.ext.asyncio import AsyncSession

#分页操作
async def get_news_category(db:AsyncSession,skip:int=0,limit:int=100):
    stmt=select(News_category).offset(skip).limit(limit)
    res=await db.execute(stmt)
    return res.scalars().all()

#查询指定分类下的新闻列表
async def get_news_list(db:AsyncSession,category_id,skip:int=0,limit:int=100):
    stmt=select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    res=await db.execute(stmt)
    return res.scalars().all()

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
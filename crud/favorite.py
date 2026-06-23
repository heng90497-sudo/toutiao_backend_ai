#收藏相关数据库操作

from sqlalchemy import select, delete,func
from sqlalchemy.ext.asyncio import AsyncSession

from models.news import News
from models.favorite import Favorite

#检查收藏状态,当前用户受否收藏了这条新闻,返回布尔值
async def check_favorite_status(news_id:int,user_id:int,db:AsyncSession):
    query=select(Favorite).where(Favorite.news_id==news_id,Favorite.user_id==user_id)
    res=await db.execute(query)
    #Ture:没有收藏
    return res.scalar_one_or_none() is None

#添加收藏
async def add_favorite(news_id:int,user_id:int,db:AsyncSession):
    favorite=Favorite(news_id=news_id,user_id=user_id)
    db.add(favorite)

    await db.commit()
    await db.refresh(favorite)
    return favorite

#取消收藏
async def remove_favorite(news_id:int,user_id:int,db:AsyncSession):
    stmt=delete(Favorite).where(Favorite.news_id==news_id,Favorite.user_id==user_id)
    res=await db.execute(stmt)
    await db.commit()
    #影响行数大于0代表删除成功
    return res.rowcount>0

#获取收藏列表:获取的是某个用户的收藏列表+分页功能
async def get_favorite_list(user_id:int,page:int=1,page_size:int=10,db=AsyncSession):
    #总量+收藏的新闻列表
    total_query=select(func.count ()).where(Favorite.user_id==user_id)
    total_res=await db.execute(total_query)
    total=total_res.scalar_one()

    offset=(page-1)*page_size

    #收藏列表要用连表查询-联表查询join()+收藏时间排序+分页
    #select(查询主体,字段别名).join(联表查询的模型类,联表查询的条件).where().order_by().offset().limit()

    #query得到的是列表,里面元素是元组,包含新闻对象News,收藏时间,收藏id
    query=(select(News,Favorite.created_at.label("favorite_created_at"),Favorite.id.label("favorite_id"))
    .join(Favorite,Favorite.news_id==News.id)
    .where(Favorite.user_id==user_id)
           .order_by(Favorite.created_at.desc()).offset(offset).limit(page_size))
    res=await db.execute(query)
    news_list=res.all()
    return total,news_list

#清空当前用户的收藏列表
async def clear_favorite_list(user_id:int,db:AsyncSession):
    stmt=delete(Favorite).where(Favorite.user_id==user_id)
    res=await db.execute(stmt)
    await db.commit()
    #返回收藏数量
    return res.rowcount or 0
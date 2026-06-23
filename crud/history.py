from models.history import History

from sqlalchemy import select,func,delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.news import News


#添加浏览记录
async def add_history(news_id:int,user_id:int,db:AsyncSession):
    history=History(news_id=news_id,user_id=user_id)
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history

#获取收藏列表
async def get_history_list(user_id:int,page:int=1,page_size:int=10,db=AsyncSession):
    #总量+浏览记录
    total_query=select(func.count ()).where(History.user_id==user_id)
    total_res=await db.execute(total_query)
    total=total_res.scalar_one()
    offset=(page-1)*page_size

    #浏览记录联表查询
    query=((select(News,History.id.label("history_id"))
           .join(History,History.news_id==News.id)).where(History.user_id==user_id)
           .order_by(History.view_time.desc()).offset( offset).limit(page_size))
    res=await db.execute(query)
    news_list=res.all()
    return total,news_list


#删除单条浏览记录
async def remove_history(history_id:int,user_id:int,db:AsyncSession):
    stmt=delete(History).where(History.id==history_id,History.user_id==user_id)
    res=await db.execute(stmt)
    await db.commit()
    return res.rowcount>0

#清空浏览历史
async def clear_history_list(user_id:int,db:AsyncSession):
    stmt=delete(History).where(History.user_id==user_id)
    res=await db.execute(stmt)
    await db.commit()
    return res.rowcount or 0
#收藏相关API路由
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from utils.auth import get_current_user
from utils.response import success_respanse
from crud import favorite
from schemas.favorite import FavoriteCheck,FavoriteAddRequest,FavoriteResponse
from models.users import User
router=APIRouter(prefix="/api/favorite", tags=["favorite"])


#检查收藏状态
@router.get("/check")
async def check_favorite_status(
    news_id:int=Query(...,alias="newsId",description="文章ID"),
    user: User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    is_fav=await favorite.check_favorite_status(news_id, user.id, db)
    #为什么要构造这个pydantic模型类:因为success_respanse这个方法,要求的data的类型是pydantic模型类
    return success_respanse(message="检查收藏状态成功",data=FavoriteCheck(isFavorite=is_fav))

#添加收藏
@router.post("/add")
async def add_favorite(
    data:FavoriteAddRequest,
    user:User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    res=await favorite.add_favorite(data.news_id, user.id, db)
    return success_respanse(message="添加收藏成功",data=res)

#取消收藏
@router.delete("/remove")
async def remove_favorite(
    news_id:int=Query(...,alias="newsId",description="文章ID"),
    user:User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    res=await favorite.remove_favorite(news_id, user.id, db)
    if not res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="记录不存在")
    return success_respanse(message="取消收藏成功")

#获取收藏列表
@router.get("/list")
async def get_favorite_list(
    page:int=Query(1,ge=1,description="页码"),
    page_size:int=Query(10,ge=1,le=10,alias="pageSize",description="每页数量"),
    user:User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    total,rows=await favorite.get_favorite_list(user.id, page, page_size, db)
    favorite_list=[{
        **news.__dict__,
        "favorite_time":favorite_time,
        "favorite_id":favorite_id
    } for news,favorite_time,favorite_id in rows]

    has_more=(page * page_size) < total
    data=FavoriteResponse(list=favorite_list,total=total,hasMore=has_more)
    return success_respanse(message="获取收藏列表成功",data=data)

#清空收藏列表
@router.delete("/clear")
async def clear_favorite_list(
    user:User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    res=await favorite.clear_favorite_list(user.id, db)
    return success_respanse(message=f"清空了{res}收藏列表成功")
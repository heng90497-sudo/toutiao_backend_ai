#历史记录相关API路由
from fastapi import APIRouter,Query,Depends,HTTPException
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from utils.auth import get_current_user
from crud import history
from utils.response import success_respanse
from schemas.history import HistoryAddRequest,HistoryResponse
from models.users import User
router=APIRouter(prefix="/api/history", tags=["history"])
#添加浏览记录
@router.post("/add")
async def add_history(
    data:HistoryAddRequest,
    user: User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    res=await history.add_history(data.news_id, user.id, db)
    return success_respanse(message="添加浏览记录成功",data=res)



#获取浏览历史列表
@router.get("/list")
async def get_history_list(
    page:int=Query(1,ge=1,description="页码"),
    page_size:int=Query(10,ge=1,le=100,alias="pageSize",description="每页数量"),
    user:User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    total,rows=await history.get_history_list(user.id, page, page_size, db)
    history_list=[{
        **news.__dict__,
        "view_time":view_time
    } for news,view_time in rows]
    has_more=(page * page_size) < total
    data=HistoryResponse(list=history_list,total=total,hasMore=has_more)
    return success_respanse(message="获取浏览历史列表成功",data=data)

#删除单条浏览记录
@router.delete("/delete/{history_id}")
async def remove_history(
    history_id:int,
    user:User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    res=await history.remove_history(history_id,user.id,db)
    if not res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="记录不存在")
    return success_respanse(message="删除成功")

#清空浏览历史
#清空收藏列表
@router.delete("/clear")
async def clear_favorite_list(
    user:User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    res=await history.clear_history_list(user.id, db)
    return success_respanse(message="清空成功")
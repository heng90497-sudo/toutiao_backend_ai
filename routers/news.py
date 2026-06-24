#新闻API相关路

import sys
import os
import grpc

# 确保能找到 rpc_protos 目录
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rpc_protos"))
import reco_pb2
import reco_pb2_grpc

from config.db_conf import get_db

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from crud import news
from crud import news_cache
#创建APIRouter实例
#prefix="/api/news"：给这个路由下的所有接口统一加一个 URL 前缀
#tags=["new"]：给接口分组，只在【自动生成的 API 文档】里生效
router = APIRouter(prefix="/api/news", tags=["news"])

#接口实现流程
#1、模块化路由-》API接口规范文档
#2、定义模型类-》数据库表
#3、在crud文件夹里封装操作数据库的方法
#4、回到路由处理器种调用crud里封装好的方法


#获取新闻分类
@router.get("/categories")
async def get_categories(db:AsyncSession=Depends(get_db),skip: int = 0, limit: int = 100):
    #先获取数据库里面新闻分类数据->定义模型类->封装查询数据的方法
    category=await news_cache.get_news_category(db,skip=skip,limit=limit)
    return {
        "code": 200,
        "msg": "获取新闻分类成功",
        "data": category
    }

#获取新闻列表
@router.get("/list")
async def get_list(db:AsyncSession=Depends(get_db),
                   category_id: int = Query(...,alias="categoryId"),
                   page: int = 1,
                   page_size: int = Query(10,alias="pageSize",le=100),
                   ):
    #思路：处理分页规则-》查询新闻列表-》计算总量-》计算是否还有更多
    offset = (page - 1) * page_size
    #查询新闻列表
    news_list=await news_cache.get_news_list(db,category_id,offset,page_size)
    #计算总量
    total=await news.get_news_count(db,category_id)
    #计算是否还有更多
    has_more=(offset + len(news_list)) < total
    return {
        "code": 200,
        "message":"success",
        "data":{
            "list":news_list,
            "total":total,
            "has_more":has_more
        }
    }
#获取新闻详情,响应结果：当前新闻详情，浏览量增加1，相关新闻详情-
@router.get("/detail")
async def get_detail(db:AsyncSession=Depends(get_db),news_id:int = Query(...,alias="id")):
    #新闻详情
    news_detail=await news.get_news(db,news_id)
    if not news_detail:
        raise HTTPException(status_code=404,detail="新闻不存在")

    #新闻浏览量增加1
    views_res=await news.increase_news_views(db,news_id)
    if not views_res:
        raise HTTPException(status_code=404,detail="更新浏览量失败")

    #相关新闻
    relates_news=await news.get_related_news(db,news_detail.id,news_detail.category_id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": news_detail.id,
            "title": news_detail.title,
            "content": news_detail.content,
            "image": news_detail.image,
            "author": news_detail.author,
            "publishTime": news_detail.publish_time,
            "categoryId": news_detail.category_id,
            "views": news_detail.views,
            "relatedNews":relates_news
    }
    }


# 获取猜你喜欢（内部调用 gRPC 微服务）
@router.get("/recommend")
async def get_recommendations(user_id: int = 1, num: int = 5):
    """
    前端调用这个 HTTP 接口，
    FastAPI 在底层偷偷用 gRPC 向推荐微服务发请求。
    """
    # 1. 拨通推荐微服务的电话（连上 50051 端口）
    # 注意：这里我们用 grpc.aio.insecure_channel 来支持异步 FastAPI
    async with grpc.aio.insecure_channel("grpc_service:50051") as channel:

        #2、拿到推荐服务器的对象
        stub=reco_pb2_grpc.RecommendServiceStub(channel)
        #3、构建请求包裹
        rep=reco_pb2_grpc.UserIdRequest(user_id=user_id,num_items=num)

        try:
            #4、调用推荐服务
            response=await stub.GetNewsRecommendations(rep)
            #5、拿到结果
            return {
                "code": 200,
                "message": response.message,
                "data": {
                    "recommend_news_ids":list(response.news_ids)
                }
            }
        except grpc.RpcError as e:
            #6、处理异常
            return {
                "code": e.code(),
                "message": f"微服务调用失败：{e.details()}",
                "data": []
            }

import sys
import os
import pytest
import grpc

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"rpc_protos"))
import reco_pb2
import reco_pb2_grpc

@pytest.mark.asyncio
class TestRecommendationRPC:

    """测试正常获取推荐数据"""
    async def test_get_recommendations_success(self):
        #1直接用代码连接50051端口
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            stub = reco_pb2_grpc.RecommendServiceStub(channel)
            #2、构造请求，用户id99，推荐10条
            req=reco_pb2.UserIdRequest(user_id=99,num_items=10)
            #3、调用
            response=await stub.GetNewsRecommendations(req)

            #4、断言
            assert response.message=="推荐成功"
            assert len(response.news_ids)==10,"返回的数量与请求不符"

            #验证返回的是否都是有效的正整数id
            for news_id in response.news_ids:
                assert isinstance(news_id,int) and news_id>0

    """测试边界异常：请求0条数据"""
    async def test_get_recommendations_zero_items(self):
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            stub = reco_pb2_grpc.RecommendServiceStub(channel)
            req=reco_pb2.UserIdRequest(user_id=99,num_items=0)
            response=await stub.GetNewsRecommendations(req)
            #期望：如果请求0条数据，返回的新闻列表长度应该是0
            assert len(response.news_ids)==0

    """测试混沌工程：验证微服务超时情况下的表现"""
    async def test_get_recommendations_timeout(self):
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            stub = reco_pb2_grpc.RecommendServiceStub(channel)
            req=reco_pb2.UserIdRequest(user_id=99,num_items=10)

            #在调用时候强行加一个极短的超时时间0.1秒，因为在服务端写了time.sleep(1),所以这里肯定会触发超时报错
            with pytest.raises(grpc.RpcError) as excinfo:
                await stub.GetNewsRecommendations(req,timeout=0.1)

            #断言抛出的确实是超时错误：DEADLINE_EXCEEDED
            assert excinfo.value.code()==grpc.StatusCode.DEADLINE_EXCEEDED
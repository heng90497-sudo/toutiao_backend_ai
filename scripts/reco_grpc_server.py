# 代表一台独立的服务器，专门负责算推荐算法
import sys
import os
import time
import random
from concurrent import futures
import grpc

# 【排雷】：把项目根目录和 rpc_protos 目录都加进搜索路径
# 解决 gRPC 自动生成的代码互相导包报错的历史遗留坑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "rpc_protos"))


# 导入刚才编译出来的合同文件
from rpc_protos import reco_pb2,reco_pb2_grpc


# ==========================================
# 1. 核心业务：实现我们在 .proto 里定义的接口
# ==========================================
class RecommendService(reco_pb2_grpc.RecommendServiceServicer):
    def GetNewsRecommendations(self, request, context):
        """
        实现我们定义的 GetNewsRecommendations 接口
        """
        # request: 客户端传过来的请求(包含了user_id和num_items)
        # context: gRPC的上下文（可以用来设置报错码等）
        user_id=request.user_id
        num_items=request.num_items
        print(f"📡 [gRPC Server] 收到请求：请为 用户{user_id} 推荐 {num_items} 条新闻。")


        # 模拟耗时
        time.sleep(random.randint(1, 3))

        #模拟从推荐池里算出的推荐新闻ID列表
        recommended_ids=[random.randint(1,5000) for _ in range(num_items)]
        print(f"✅ [gRPC Server] 推荐计算完成：{recommended_ids}")

        # 返回我们在 .proto 里定义的 NewsListResponse 格式
        return reco_pb2.NewsListResponse(news_ids=recommended_ids,message="推荐成功")

    # ==========================================
    # 2. 启动 gRPC 服务器
    # ==========================================
def serve():
    """
    启动 gRPC 服务器
    """
    #创建一个最多支持10个并发的线程池来处理请求
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    #把我们的业务逻辑类注册到grpc服务器上
    reco_pb2_grpc.add_RecommendServiceServicer_to_server(RecommendService(), server)

    #让服务器在本地的50051端口坚守岗位
    server.add_insecure_port('[::]:50051')
    server.start()
    print("[gRPC Server] 推荐微服务启动成功，监听端口 50051")

    #死循环，让服务器永远不退出
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

#应用入口文件
from fastapi import FastAPI
#导入news模块
from routers import news
from routers import users
from routers import favorite
from routers import history
#导包
from fastapi.middleware.cors import CORSMiddleware

from utils.exception_handlers import register_exception_handler

app = FastAPI()

#注册异常处理器
register_exception_handler(app)

#允许的源
origins=[
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]
#添加中间件,解决前后端跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #允许的源，这里是开发阶段"*"代表允许所有源，上线的话需要指定源
    allow_credentials=True, #允许携带cookie
    allow_methods=["*"], #允许所有请求方法
    allow_headers=["*"], #允许所有的请求头
)
@app.get("/")
async def root():
    return {"message": "Hello World"}

#挂载路由
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
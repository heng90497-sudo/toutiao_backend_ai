#数据库配置文件
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

#数据库URL
ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@127.0.0.1:3306/toutiao_test?charset=utf8"

#创建异步引擎
async_engine=create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,#输出SQL日志
    pool_size=10,#持久连接数
    max_overflow=20,#允许额外连接数
)

#创建异步会话工厂
AsyncSessionLocal=async_sessionmaker(
    bind=async_engine,#绑定数据库引擎
    class_=AsyncSession, #生产的是异步会话
    expire_on_commit=False#提交会话后不会过期，不会重新查询数据库
    )

#依赖项，用来获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()



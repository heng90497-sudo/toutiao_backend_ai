# 【测试核心】全局配置、测试数据库连接、公共 Fixture
#在这个要实现每次测试前自动建表，测试后自动删表，并拦截原有的数据库连接，替换为测书库
#pytest测试数据地库不能和压测是冲突的，所以要使用测试数据库
import pytest_asyncio
import pytest
from config.db_conf import get_db
from httpx import AsyncClient,ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession,async_sessionmaker

#导入项目中的模型类和app
from models.users import User
from main import app

#导入数据库依赖
from config.db_conf import get_db

#测试数据库的连接，为了和正式数据库隔离，使用测试数据库
TEST_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/pytest_toutiao?charset=utf8"

#创建测试用的异步引擎
test_engine=create_async_engine(
    TEST_DATABASE_URL ,
    echo=True,#输出SQL日志
    pool_size=10,#持久连接数
    max_overflow=20,#允许额外连接数
)
#创建异步会话工厂
AsyncSessionLocal=async_sessionmaker(
    bind=test_engine,#绑定数据库引擎
    class_=AsyncSession, #生产的是异步会话
    expire_on_commit=False#提交会话后不会过期，不会重新查询数据库
    )

#覆盖原来FastAPI的数据库依赖
async def override_get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

#！！！覆盖FastAPI数据库依赖
app.dependency_overrides[get_db]=override_get_db

#初始化测试数据库（建表/删表）
@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    #测试前：在测试库中创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(User.metadata.drop_all) #先清空旧表
        await conn.run_sync(User.metadata.create_all) #重新建立表

    yield #把控制权交给测试用例，测试用例开始执行

    # 【核心修复】：测试结束后，强制销毁连接池！
    # 这样下一个用例进来时，就不会拿到绑定着“死循环”的旧连接了
    await test_engine.dispose()

#提供异步Http客户端
@pytest_asyncio.fixture
async def async_client():
    #使用httpx的AsyncClient向FastAPI的app服务器发送请求
    async with AsyncClient(transport=ASGITransport(app),base_url="http://test") as client:
        yield client
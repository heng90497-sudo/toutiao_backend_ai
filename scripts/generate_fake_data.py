# [造数据脚本]
import sys
import os
# 【排雷1】：把项目根目录加入环境，完美解决 ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import asyncio
import random
from faker import Faker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

#导入项目地数据库连接和模型
from models.base import Base
from models.users import User
from models.news import News,News_category
from models.history import History
from sqlalchemy.ext.asyncio import AsyncSession
from utils.security import get_hash_password


#============================================================================
#直接在这里配置测试数据库
TEST_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/toutiao_test?charset=utf8"
test_engine=create_async_engine(
    TEST_DATABASE_URL ,
    echo=True,#输出SQL日志
)
AsyncSessionLocal=async_sessionmaker(
    bind=test_engine,#绑定数据库引擎
    class_=AsyncSession, #生产的是异步会话
    expire_on_commit=False#提交会话后不会过期，不会重新查询数据库
    )

#初始化Faker(指定中文)
fake=Faker("zh_CN")

#密码加密:不需要循环给很多个用户挨个加密密码，这回非常耗时，测试数据统一使用同一个密码加密
STATIC_HASHED_PASSWORD=get_hash_password("strong123")


#生成固定地新闻分类
#session是指数据库会话，session.add()添加数据，session.commit()提交数据
async def generate_category(session:AsyncSession):
    category_names=["科技", "财经", "体育", "娱乐", "游戏", "国际", "汽车", "房产","国内","军事","其他"]
    categories=[]
    print("正在生成分类数据。。。")
    for n in category_names:
        category=News_category(name=n)
        categories.append(category)
        session.add(category)
    await session.commit()
    res=await session.execute(News_category.__table__.select())
    return [row.id for row in res.all()]

#生成用户
async def generate_user(session:AsyncSession,count=100):
    print(f"正在生成{count}个假用户。。。")
    users=[]
    for _ in range(count):
        user=User(username=fake.unique.user_name(),
                   password=STATIC_HASHED_PASSWORD,
                   )
        users.append(user)

    #使用add_all批量插入，大幅提升性能
    session.add_all(users)
    await session.commit()

    #获取所有用户id用于后续关联
    res=await session.execute(User.__table__.select())
    return [row.id for row in res.all()]


#生成假新闻
async def generate_news(author_ids,category_ids,session:AsyncSession,count=5000):
    print(f"正在生成{count}条假新闻。。。")
    news_list=[]
    for _ in range(count):
        news=News(
            title=fake.sentence(),
            description=fake.sentence(),
            content=fake.text(),
            image=fake.image_url(),
            author=random.choice(author_ids),
            category_id=random.choice(category_ids),
        )

        news_list.append(news)
        #每1000条提交一次，防止内存撑爆
        if len(news_list)>=1000:
            session.add_all(news_list)
            await session.commit()
            news_list=[]

    #提交剩余地
    if news_list:
        session.add_all(news_list)
        await session.commit()

    res=await session.execute(News.__table__.select())
    news_ids=[row.id for row in res.all()]

#运行
async def main():
    print("正在生成数据...")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)



    async with AsyncSessionLocal() as session:
        try:
            #生成分类
            category_ids=await generate_category(session)
            #生成用户
            author_ids=await generate_user(session,count=100)
            #生成新闻
            await generate_news(author_ids=author_ids,category_ids=category_ids,session=session,count=5000)
            print("数据生成完毕！")
        except Exception as e:
            print(f"发生错误{e}")
            await session.rollback()
        finally:
            # 1. 先关闭当前会话
            await session.close()
            # 2. 关键：销毁整个引擎连接池，释放所有底层mysql连接
            await test_engine.dispose()

if __name__=="__main__":
    asyncio.run(main())
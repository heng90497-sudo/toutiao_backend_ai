#用户相关数据库操作

from fastapi import HTTPException
from  sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User,UserToken
from schemas.users import UserRequest, UserUpdate
from utils import security
import uuid
from datetime import datetime,timedelta


# 根据用户名查询用户
async def get_users_by_username(db: AsyncSession,username: str):
    stmt=select(User).where(User.username == username)
    results = await db.execute(stmt)
    return results.scalar_one_or_none()

#创建用户
async def create_user(db: AsyncSession, user_data: UserRequest):
    #先密码加密
    hash_password=security.get_hash_password(user_data.password)

    #创建一个用户
    user = User(username=user_data.username, password=hash_password)
    #将这个用户添加到数据库中
    db.add(user)
    await db.commit()
    await db.refresh(user) #更新数据，从数据库中读取最新的user
    return user

#生成Token:生成token->设置过期时间->查询数据库当前用户是否有Token:有：更新；没有：添加
async def create_token(db:AsyncSession,user_id:int):
    #生成Toke
    token = str(uuid.uuid4())
    #设置过期时间,timedelta:推迟时间
    expires_at = datetime.now() + timedelta(days=7)
    #查询当前用户是否有token
    stmt=select(UserToken).where(UserToken.id == user_id)
    res=await db.execute(stmt)
    user_token = res.scalar_one_or_none()

    #判断是否有token，有更新，没有添加
    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
        await db.commit()
    else:
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
        await db.commit()
    return token

#验证数据库中是否有这个user
async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_users_by_username(db, username)
    #用户不存在
    if not user:
        return None
    #密码验证
    if not security.verify_password(password, user.password):
        return None
    #验证通过
    return user

#验证Token然后查询用户
async def get_user_by_token(db: AsyncSession, token: str):
    """
    验证Token
    """
    query=select(UserToken).where(UserToken.token == token)
    res=await db.execute(query)
    user_token = res.scalar_one_or_none()
    if not user_token or user_token.expires_at < datetime.now():
        return  None

    # 然后查询用户
    query=select(User).where(User.id == user_token.user_id)
    res=await db.execute(query)
    return res.scalar_one_or_none()

#更新用户信息:update更新->检查token是否有效->获取更新后的用户返回
async def update_user_info(db: AsyncSession, user_data: UserUpdate, username: str):
    #update(User).where(User.username == username).values(字段=值)
    #user_data是pydantic类型,要通过model_dump转化成字典,然后加**解包,
    #然后用exclude_unset=True,exclude_none=True确保用户输入的才提取值,其他不提取
    query=update(User).where(User.username == username).values(**user_data.model_dump(
        exclude_unset=True,exclude_none=True))
    res=await db.execute(query)
    await db.commit()

    #检查更新
    if res.rowcount == 0:
        raise HTTPException(status_code=404,detail="用户不存在")

    #获取以下更新后的用户
    update_user=await get_users_by_username(db,username)
    return update_user

#更新密码:update更新->检查token是否有效->检查旧密码是否正确->更新密码->返回更新后的用户
async def update_password(db: AsyncSession, user:User, old_password: str, new_password: str):
    if not security.verify_password(old_password, user.password):
        raise HTTPException(status_code=400,detail="旧密码错误")
    hash_password=security.get_hash_password(new_password)
    user.password=hash_password
    #为什么要用add添加？
    #规避因为session过期或者关闭导致不能提交的问题
    #由sqlalchemy真正接管,确保可以commit
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True
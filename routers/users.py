#用户相关API路由
import token

from fastapi import APIRouter, Depends, HTTPException, responses

from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdate, UpdatePassword
from crud import users
from utils.response import success_respanse
from utils.auth import get_current_user
from utils.security import verify_password
router=APIRouter(prefix="/api/user", tags=["user"])


#注册用户：,请求体参数（pydantic）：username:str,password:str，封装在schemas.user中
#流程：检查用户是否存在，存在抛出异常，不存在则创建用户（1、密码加密处理passlib(哈希算法)，2、添加数据）
#然后生成访问令牌：用于判断用户登录的状态
@router.post("/register")
async def user_register(user_data:UserRequest,db:AsyncSession=Depends(get_db)):
    #验证用户是否存在，写了全局处理器这里不再需要了
    # existing_user = await users.get_users_by_username(db, user_data.username)
    # if existing_user:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User with this username already exists")
    #不存在则创建用户
    user = await users.create_user(db, user_data)
    token=await users.create_token(db, user.id)
    # return {
    #   "code": 200,
    #   "message": "注册成功",
    #   "data": {
    #     "token": token,
    #     "userInfo": {
    #       "id": user.id,
    #       "username": user.username,
    #       "bio": user.bio,
    #       "avatar": user.avatar
    #     }
    #   }
    # }
    #model_validate(user):将user转化为Pydantic模型
    responses_data=UserAuthResponse(token=token,user_info=UserInfoResponse.model_validate(user))
    return success_respanse(message="注册成功",data=responses_data)

#登录用户
@router.post("/login")
async def user_login(user_data:UserRequest,db:AsyncSession=Depends(get_db)):
    #登录逻辑：验证用户是否存在->验证密码->生成token->返回数据
    user = await users.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="用户名或密码不存在")
    token=await users.create_token(db, user.id)
    responses_data=UserAuthResponse(token=token,user_info=UserInfoResponse.model_validate(user))
    return success_respanse(message="用户登录成功",data=responses_data)

#获取用户信息
#登录成功后，才能获取用户信息：查Token是否有效，然后再查用户是否存在
#流程:查Token查用户->把他们封装成crud->把这个功能整合成一个工具函数->路由导入使用：直接使用依赖注入
@router.get("/info")
async def user_info(user=Depends(get_current_user)):
    return success_respanse(message="用户信息获取成功",data=UserInfoResponse.model_validate(user))

#更新用户信息:验证token->更新(用户输入的数据,作为请求体参数提交)->响应结果
@router.put("/update")
async def update_user_info(user_data:UserUpdate,user=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    user=await users.update_user_info(db, user_data, user.username)
    return success_respanse(message="用户信息更新成功",data=UserInfoResponse.model_validate(user))

@router.put("/password")
async def update_user_password(password_data:UpdatePassword,user=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    #调用方法
    await users.update_password(db, user, password_data.old_password, password_data.new_password)
    return success_respanse(message="密码更新成功",data=UserInfoResponse.model_validate(user))

#测试账号密码,wjwwjw,asdjkl34122
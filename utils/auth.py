# 整合验证用户token，以及验证用户是否存在的方法
import starlette
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_conf import get_db
from crud import users
from fastapi import Depends,HTTPException,Header
from starlette import status

"""
依赖注入：
    1.依赖注入：依赖注入，就是把依赖对象作为参数传入，然后由依赖注入器提供依赖对象
    2.依赖注入器：依赖注入器，就是把依赖对象作为参数传入，然后由依赖注入器提供依赖对象
    3.依赖注入：依赖注入，就是把依赖对象作为参数传入，然后由依赖注入器提供依赖对象
    4.依赖注入器：依赖注入器，就是把依赖对象作为参数传入，然后由依赖注入器提供依赖对象
"""
#authorization: str = Header(...,alias="Authorization"): 在请求头中获取Authorization字段
"""
Authorization:Bearer<token>
Authorization:专门用来放身份信息
Bearer：表示“持有者令牌”
<token>:真正的身份凭证
"""
async def get_current_user(
        db: AsyncSession = Depends(get_db),
        authorization: str = Header(...,alias="Authorization")
):
    # token=authorization.split(" ")[1]->不安全,慎用
    token = authorization.replace("Bearer ", "")
    user = await users.get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="无效令牌或者过期令牌")
    return user
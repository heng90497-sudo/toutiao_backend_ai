#创见加密算法
#导包
from passlib.context import CryptContext

#创建加密上下文,schemes:加密方式;deprecated:兼容新旧版本
pwd_context = CryptContext(schemes=["pbkdf2_sha256"],deprecated="auto")

#密码加密
def get_hash_password(password):
    return pwd_context.hash(password)

#密码验证verify方法返回的是布尔类型
def verify_password(plain_password,hashed_password):
    return pwd_context.verify(plain_password,hashed_password)
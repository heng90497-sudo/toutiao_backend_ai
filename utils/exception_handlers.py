#注册全局异常处理器
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from utils.exception import http_exception_handler,integrity_error_handler,sqlalchemy_error_handler,general_exception_handler

#add_exception_handler = FastAPI 官方提供的方法
#要传 2 个参数：
# 第一个：要捕捉什么错误（如 HTTPException）
# 第二个：出错了交给谁处理（你自己写的处理函数）
def register_exception_handler(app):
    """
    注册全局异常处:子类在前，父类在后；具体在前，抽象在后
    :param app:
    :return:
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
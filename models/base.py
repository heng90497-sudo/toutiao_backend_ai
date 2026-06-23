# 文件：models/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    # 这是所有表共用的基类，里面包含了一个大家都有的 created_at 字段
   pass

from datetime import datetime
from typing import Optional
from pydantic import BaseModel,Field,ConfigDict

class NewsItemBase(BaseModel):
    """
        新闻数据验证模型
    """
    id:int
    title:str
    description:str
    image:Optional[ str]=None
    author:Optional[ str]=None
    category_id:int=Field(alias="categoryId")
    views:int
    publish_time:Optional[datetime]=Field(alias="publishTime")

    model_config = ConfigDict(
        from_attributes=True,#允许从orm对象中获取数据
        populate_by_name=True, #alias和字段名兼容
    )
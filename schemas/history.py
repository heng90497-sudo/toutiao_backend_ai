#历史记录数据验证模型
from pydantic import BaseModel,Field,ConfigDict
from utils.base import NewsItemBase
from datetime import datetime
#添加历史记录
class HistoryAddRequest(BaseModel):
    news_id:int=Field(...,alias="newsId")


#历史浏览记录模型类
class HistoryNewsItemResponse(NewsItemBase):
    view_time:datetime=Field(...,alias="viewTime")
    model_config = ConfigDict(
        populate_by_name=True, #alias和字段名兼容
        from_attributes=True#允许从orm对象中获取数据
    )

class HistoryResponse(BaseModel):
    list:list[HistoryNewsItemResponse]
    total:int
    has_more:bool=Field(...,alias="hasMore")
    model_config = ConfigDict(
        populate_by_name=True, #alias和字段名兼容
        from_attributes=True#允许从orm对象中获取数据
    )
#收藏数据验证模型
from pydantic import BaseModel,Field,ConfigDict

from utils.base import NewsItemBase
from datetime import datetime
#检查收藏
class FavoriteCheck(BaseModel):
    is_favorite:bool=Field(...,alias="isFavorite")
#添加收藏
class FavoriteAddRequest(BaseModel):
    news_id:int=Field(...,alias="newsId")

class FavoriteNewsItemResponse(NewsItemBase):
    favorite_time:datetime=Field(...,alias="favoriteTime")
    favorite_id:int=Field(...,alias="favoriteId")
    model_config = ConfigDict(
        populate_by_name=True, #alias和字段名兼容
        from_attributes=True#允许从orm对象中获取数据
    )

#收藏接口响应模型类
class FavoriteResponse(BaseModel):
    list:list[FavoriteNewsItemResponse]
    total:int
    has_more:bool=Field(...,alias="hasMore")
    model_config = ConfigDict(
        populate_by_name=True, #alias和字段名兼容
        from_attributes=True#允许从orm对象中获取数据
    )
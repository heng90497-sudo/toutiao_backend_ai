from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def success_respanse(message: str="success", data=None):
    content={
        "code":200,
        "message":message,
        "data":data
    }
    #把任何fastapi、pydantic、orm对象都要正常响应，所以这里用jsonable_encoder进行转换
    return JSONResponse(content=jsonable_encoder(content))
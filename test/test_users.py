# 【新增】用户模块测试用例
# 测试用户模块的增删改查功能
# @pytest.mark.asyncio 已经被pytest.ini里的auto替代了，可以直接写async def
import pytest
import allure



@allure.feature("用户注册模块")
class TestUser:

    @allure.story("用户注册")
    async def test_register(self,async_client):
        register_data = {
            "username": "test_user",
            "password": "strong123",
            "nickname": "测试pytest用户",
        }

        with allure.step("测试用户注册"):
            #模拟发送post请求给注册接口
            response=await async_client.post("/api/user/register",json=register_data)

            #断言状态码必须是200或者201
            assert response.status_code==200
            #断言返回的JSON中应该包含成功信息
            data=response.json()
            assert data["message"]=="注册成功"


        with allure.step("测试用户重复注册"):
            response=await async_client.post("/api/user/register",json=register_data)
            assert response.status_code==400



        with allure.step("测试用户登录"):
            login_data={
                "username":"test_user",
                "password":"strong123",
            }
            response_login=await async_client.post("/api/user/login",json=login_data)
            assert response_login.status_code==200
            data_login=response_login.json()

            #核心断言必须返回Token
            assert "token" in data_login["data"]
            assert data_login["message"]=="用户登录成功"


        with allure.step("测试用户信息"):
            token=data_login["data"]["token"]
            headers={"Authorization":f"Bearer {token}"}
            response_info=await async_client.get("/api/user/info",headers=headers)
            assert response_info.status_code==200
            data_info=response_info.json()
            assert data_info["message"]=="用户信息获取成功"
            assert data_info["data"]["username"]==register_data["username"]



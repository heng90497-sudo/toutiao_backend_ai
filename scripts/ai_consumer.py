import sys
import os
# 【排雷】：把当前脚本的上一级（项目根目录）加入 Python 搜索路径
# os.path.abspath：获取它的绝对路径（比如 G:\toutiao_backend\scripts\ai_consumer.py）。
# os.path.dirname：剥掉文件名，拿到父级目录。嵌套两次，就拿到了项目根目录 G:\toutiao_backend。
# sys.path.append：强行把这个根目录塞进 Python 的大脑（寻路清单）里。
c

import asyncio
import json
import aio_pika
from openai import AsyncOpenAI

#导入异步数据库工厂和模型
from config.db_conf import AsyncSessionLocal
from models.news import News

# 配置AI大模型
AI_API_KEY="sk-ws-H.RPHDDIL.xJqt.MEUCICi4oBRCa08z6ZKD6gPjCylh_9FbBpCTqg-QLXlxqjoqAiEAsoKAwN4-1CSWKe-TWaugR1T5R7CJxXGrxDoLrsnRnpo"
AI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
AI_MODEL_NAME="qwen-turbo"

#初始化异步ai客户端
ai_client=AsyncOpenAI(api_key=AI_API_KEY,base_url=AI_BASE_URL)

#调用大模型，生成新闻摘要
async  def generate_ai_summary(content:str)->str:

    try:
        response=await ai_client.chat.completions.create(
            model=AI_MODEL_NAME,
            messages=[
                # role: system代表给AI设定人设，role: user是你喂给它的数据
                {"role":"system","content": "你是一个资深新闻主编。请为以下新闻提取 50 字左右的精简核心摘要。直接输出摘要内容，不要有废话。"},
                # 截取前 1000 字，防止文本太长超载
                {"role":"user","content":content[:1000]}
            ], # type: ignore
            temperature=0.3#温度越低，生成的摘要越严肃、准确
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI调用失败：{e}")
        return "摘要生成失败：网络或API异常"


# 存入数据库
async def save_news_to_db(news_data:dict,summary:str):
    "将处理好的数据持久化到MYsql"
    async with AsyncSessionLocal() as session:
        news=News(
            title=news_data.get("title","无标题"),
            content=news_data.get("content","无正文"),
            description=summary,
            image=news_data.get("image",""),
            author=news_data.get("source","AI聚合"),
            category_id=1#临时默认为第一类
        )
        session.add(news)
        await session.commit()

#3、从队列中拿数据，存入数据库
async def process_message(message:aio_pika.abc.AbstractIncomingMessage):
    """处理拿到的每一条消息"""
    #message.process()会自动发ACK确认
    # 企业级写法：使用了强大的上下文管理器process()。它的逻辑是：
    # 只要里面的代码顺利执行完毕，它自动向RabbitMQ发送一个ACK（收条）：“报告，我安全处理完了，你可以把这个包裹从队列里删了！
    # ”如果存数据库报错了，或者AI挂了（抛出异常），它会自动发送NACK（拒收）：“报告，处理出错了，快把这个包裹重新放回传送带，交给别的消费者处理！”
    # 测开价值：这就是分布式系统中保证“消息绝对不丢失”的终极防线！
    message.process()
    # 是一个异步上下文管理器。RabbitMQ里的数据传过来都是字节码（bytes），所以要先.decode('utf-8')解码成字符串，
    # 再json.loads 转成Python字典。
    async with message.process():
        #拿到数据
        body=message.body.decode('utf-8')
        news_data=json.loads(body)
        print(f"收到新闻：{news_data.get('title')}")

        #2、交给AI大脑思考
        print("🧠 AI 正在极速阅读并生成摘要..")
        summary=await generate_ai_summary(news_data.get('content',''))
        print(f"AI摘要：{summary}")

        #3、数据库
        await save_news_to_db(news_data,summary)
        print("已成功存入数据库")

#启动监听者程序
async def main():
    #连接RabbitMQ
    mq_url="amqp://admin:admin123@127.0.0.1/"
    # connect_robust：带robust（健壮的）后缀，意味着如果RabbitMQ服务端重启了，
    # 它会在后台自动尝试重新连接，不需要你人工重启脚本。
    connection=await aio_pika.connect_robust(mq_url)
    channel=await connection.channel()

    #设置Qos=1:AI每次只拿一篇新闻，处理完，才拿下一篇
    await channel.set_qos(prefetch_count=1)

    #找到raw_news_queue的队列(传送带）
    queue=await channel.declare_queue("raw_news_queue",durable=True)

    #k开始无休止的监听
    # queue.consume这个方法是非阻塞的，会自动处理消息
    print("持续监听中")
    await queue.consume(process_message)

    #让程序永远运行下去
    await asyncio.Future()

if __name__=="__main__":
    # Windows 下可能需要这句策略以防止 Event loop 关闭报错
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
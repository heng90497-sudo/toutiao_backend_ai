#抓新闻
import json
import time

import requests

# 把新闻送进队列（RabbitMQ比喻成快递局），需要填写标准的快递单，pika是python官方指定的专属工具包
#RabbitMQ是用Erlang语言写的，底层走的AMQP协议，pika是一个python库，帮我们把复杂的底层网络协议封装好了，
# 有了它，只需要调用basic_publish,就会帮忙把python字典打包成二进制，然后发送给RabbitMQ，
import pika


# RabbitMQ 连接配置
#注意账号密码要和docker-copmpose.yml中的账号密码一致
MQ_HOST='rabbitmq'
MQ_PORT=5672
MQ_USER='admin'
MQ_PASSWORD='admin123'
MQ_EXCHANGE='raw_news_queue' #传送带（队列）的名字：原始新闻队列

#连接RabbitMQ,获取MQ连接通道
def get_mq_channel():
    credentials=pika.PlainCredentials(MQ_USER,MQ_PASSWORD)
    #在代码和RabbitMQ之间，创建连接和通道（TCP物理连接），并声明队列，这样，后续的代码就可以直接使用连接和通道了
    # 相当于你在你的代码和 RabbitMQ 之间，修了一条跨海大桥（TCP 物理连接）。修桥是非常耗时、极其消耗服务器资源的。
    parameters=pika.ConnectionParameters(MQ_HOST,MQ_PORT,credentials=credentials)
    connection=pika.BlockingConnection(parameters)

    # 果每次发新闻都要重新修一座桥，系统立马就卡死了。
    # 所以 RabbitMQ 设计了 Channel（信道）的概念。相当于在这座大桥上，划出了很多根“虚拟的专用车道”。
    #获取MQ通道（信道）
    channel=connection.channel()

    # 告诉 RabbitMQ：“去检查一下有没有叫 raw_news_queue（MQ_EXCHANGE） 的仓库。
    # 如果没有，马上建一个；如果有，就直接用。durable=True 意思是这个仓库必须是混凝土做的，就算服务器断电重启，里面的新闻也不能丢！”
    #声明队列，durable=True 代表队列持久化，哪怕RabbitMQ重启，传送带也不会消失
    channel.queue_declare(queue=MQ_EXCHANGE,durable=True)
    return connection,channel


#爬虫抓取逻辑（新浪滚动新闻接口）
def fetch_real_news():
    # 去新浪新闻中抓取最新的真实新闻
    print("开始抓取新闻...")
    #这是一个新浪公开的免费API接口，返回最新滚动新闻的JSON数据
    # url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=10&page=1"

    # **“反爬虫伪装”**。加上这段 User-Agent，新浪的服务器就会以为：
    # “嗯，这是一个用着 Windows 10 电脑、开着 Chrome 浏览器的正常人类网友在访问页面。”于是乖乖把数据给你。
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # 准备一个大列表，把几页的数据都装进去
    all_news=[]
    for page in range(1,6):
        url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=50&page={page}"

        try:
            #timeout=5（防无限假死）
            # 如果不加这句，你的脚本会永远卡在这里死等，导致整个生产者程序僵死。加了
            # timeout = 5，意味着“最多等5秒，拿不到数据我直接掀桌子报错”
            print("正在抓取第%s页新闻..."%page)
            response=requests.get(url,headers=headers,timeout=5)
            # raise_for_status()（防静默失败）：如果新浪给你返回了一个 404（找不到网页）或者 500（服务器崩溃），
            # requests 库默认是不会报错的！它会把错误页面当成正常数据给你。加上这句，只要 HTTP 状态码不是 200，它就会立刻主动抛出异常，进入下面的 except 环节。
            response.raise_for_status()
            data=response.json()


            #提取新闻列表

            # data.get("result", {})：去字典里拿 "result"，如果没拿到，别报错，退给我一个空字典 {}
            # .get("data", [])：接着去前面那个结果里拿 "data"，如果没拿到，别报错，退给我一个空列表 []
            news_list=data.get("result",{}).get("data",[])

            all_news.extend(news_list) #把这页数据放进去
            time.sleep(0.5)

        # 可以用下列方式测试
        # Mock 超时异常：模拟网络断开，验证程序是否能正确走到 except 并返回 []。
        # Mock 脏数据：模拟新浪接口返回一个残缺的 JSON {"code": 200}，验证那个 .get().get() 是不是真的能防崩溃。
        except Exception as e:
            print(f"❌ 第 {page} 页抓取失败: {e}")
            break  # 报错了就终止翻页
    print(f"✅ 批量抓取完成！共抓到 {len(all_news)} 条最新实时新闻！\n")
    return all_news


    #主程序：抓取新闻，发送到MQ
def main():
#     1、抓取新闻
    new_list=fetch_real_news()
    if not new_list:
        print("没有新闻")
        return
    # 2、获取MQ连接通道
    print("获取MQ连接通道...")
    connection,channel=get_mq_channel()

    #3.把抓取到的新闻发送到MQ中
    success_count=0
    for news in new_list:
        # 1、解析原始的新闻数据
        news_data = {
            "title": news.get("title"), #得到新浪公开新闻的标题
            "content": news.get("content") or news.get("intro"),# 正文（如果抓不到正文，暂用 intro 顶替，因为模型类的content 设了 nullable=False）
            "image":news.get("pic") or news.get("picUrl") or news.get("imgs")[0] if news.get("imgs") else "",# 图片
            "author":news.get("media_name","网络抓取"),# 作者

            # # 2. 故意留给 AI 大模型去填写的“空白卷”
            # "description": ...  (我们不写！等会儿让 AI 读完 content 后，自动生成 50 字摘要填进来)
            #category_id: ...  (我们不写！等会儿，让 AI 读完 content 后，自动判断它是体育还是财经，然后让消费者填入正确的 ID！)

        }

        #将python 字典转成JSON字符串，因为队列里只能传字符串或字节
        message_body=json.dumps(news_data,ensure_ascii=False)

        #发送消息到队列
        channel.basic_publish(exchange='',  #使用默认交换机
                              routing_key=MQ_EXCHANGE, #指定扔到哪个队列
                              body=message_body,#消息体
                              properties=pika.BasicProperties(
                                  delivery_mode=2,#消息持久化,哪怕断电，扔进去的新闻也不会丢
                              )
                            )
        print(f"已投递到队列：{news_data['title'][:20]}...")
        success_count+=1
        time.sleep(0.1) #稍微停顿下

    #关闭连接
    connection.close()
    print(f"共计将{success_count}条新闻投递到队列中")

if __name__ == '__main__':
    main()
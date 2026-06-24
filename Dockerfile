# 1. 指定纯净版的 Python 3.10 基础环境
FROM python:3.10-slim

# 2. 设置工作目录为 /app,意思是以后所有的命令都在这个目录下执行
WORKDIR /app

# 3. 拷贝依赖清单并安装（使用清华源加速）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 把项目的所有代码拷贝到集装箱里
COPY . .

# 5. 声明暴露 8000 端口
EXPOSE 8000

# （注意：这里我们不写 CMD 启动命令，因为我们要在 docker-compose 里分别为 3 个程序指定不同的启动命令！）
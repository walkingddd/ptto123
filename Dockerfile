# 使用Python 3.12作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置Python不缓冲输出
ENV PYTHONUNBUFFERED=1

# 复制当前目录的内容到容器的/app目录下
COPY . /app

# 创建上传和删除目录
RUN mkdir -p upload delete

# 安装所需的Python包
RUN pip install -U p123client

# 运行Python脚本
CMD ["python", "ptto123.py"]
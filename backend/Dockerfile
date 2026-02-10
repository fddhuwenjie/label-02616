# 使用官方 Python 镜像作为基础镜像（支持 ARM 和 X86）
FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 最终运行镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 从 builder 阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 运行脚本
CMD ["python", "check_enterprise.py"]

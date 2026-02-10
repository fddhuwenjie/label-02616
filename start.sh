#!/bin/bash
# 企业信息检查工具 - 一键启动脚本
# 兼容 macOS / Linux / Windows (Git Bash / WSL)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  企业信息批量检查工具${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 检查 Downloads 目录
if [ ! -d "./Downloads" ]; then
    echo -e "${YELLOW}警告: Downloads 目录不存在，正在创建...${NC}"
    mkdir -p ./Downloads
    echo -e "${YELLOW}请将 Excel 文件放入 Downloads 目录后重新运行${NC}"
    exit 1
fi

# 检查是否有 Excel 文件
EXCEL_COUNT=$(find ./Downloads -name "企业信息批量查询列表_*.xlsx" 2>/dev/null | wc -l | tr -d ' ')
if [ "$EXCEL_COUNT" -eq 0 ]; then
    echo -e "${RED}错误: Downloads 目录中没有找到 Excel 文件${NC}"
    echo -e "${YELLOW}请确保文件名格式为: 企业信息批量查询列表_YYYYMMDD*.xlsx${NC}"
    exit 1
fi
echo -e "找到 ${GREEN}${EXCEL_COUNT}${NC} 个 Excel 文件"
echo ""

# 选择运行方式
echo "请选择运行方式:"
echo "  1) Docker 运行 (推荐)"
echo "  2) 本地 Python 运行"
echo ""
read -p "请输入选项 [1/2]: " choice

# 输入日期
echo ""
echo "请输入要检查的日期 (格式: YYYYMMDD)"
read -p "今日日期 [默认 20251214]: " TODAY_DATE
TODAY_DATE=${TODAY_DATE:-20251214}

read -p "前日日期 [默认 20251213，留空跳过比较]: " PREVIOUS_DATE
PREVIOUS_DATE=${PREVIOUS_DATE:-20251213}

export TODAY_DATE
export PREVIOUS_DATE

case $choice in
    1)
        echo ""
        echo -e "${GREEN}使用 Docker 启动...${NC}"
        
        # 检查 Docker
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}错误: 未安装 Docker${NC}"
            echo "请先安装 Docker: https://docs.docker.com/get-docker/"
            exit 1
        fi
        
        if ! docker info &> /dev/null; then
            echo -e "${RED}错误: Docker 未运行${NC}"
            echo "请先启动 Docker Desktop"
            exit 1
        fi
        
        # 检查 docker-compose 或 docker compose
        if command -v docker-compose &> /dev/null; then
            COMPOSE_CMD="docker-compose"
        elif docker compose version &> /dev/null; then
            COMPOSE_CMD="docker compose"
        else
            echo -e "${RED}错误: 未安装 docker-compose${NC}"
            echo "请安装 Docker Compose: https://docs.docker.com/compose/install/"
            exit 1
        fi
        
        echo "使用: $COMPOSE_CMD"
        
        # 构建并运行
        $COMPOSE_CMD up --build
        ;;
    2)
        echo ""
        echo -e "${GREEN}使用本地 Python 启动...${NC}"
        
        # 检查 Python（优先使用高版本）
        PYTHON_CMD=""
        for cmd in python3.12 python3.11 python3.10 python3 python; do
            if command -v $cmd &> /dev/null; then
                PYTHON_CMD=$cmd
                break
            fi
        done
        
        if [ -z "$PYTHON_CMD" ]; then
            echo -e "${RED}错误: 未安装 Python${NC}"
            exit 1
        fi
        
        echo "使用 Python: $($PYTHON_CMD --version)"
        
        # 安装依赖
        echo "安装依赖..."
        $PYTHON_CMD -m pip install -q -r backend/requirements.txt
        
        # 运行
        echo ""
        $PYTHON_CMD backend/check_enterprise.py
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

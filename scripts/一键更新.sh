#!/bin/bash

# 设置错误即退出
set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       标准文献检索系统 - 一键更新      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}[!] 注意: 此操作将从 GitHub 拉取最新代码，并可能覆盖本地未提交的修改。${NC}"
echo ""

# 提示用户确认
read -p "按 [Enter] 键继续，或按 [Ctrl+C] 取消..."

# 切换到脚本所在目录的上一级（项目根目录）
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
echo -e "${GREEN}[√] 当前目录: ${PROJECT_ROOT}${NC}"
echo ""

# 检查是否安装了 Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}[×] 错误: 未找到 Git 命令！${NC}"
    echo -e "${YELLOW}[!] 请确保已安装 Git 并将其添加到了系统环境变量中。${NC}"
    exit 1
fi

echo -e "${BLUE}[>] 正在获取最新代码状态...${NC}"
if ! git fetch origin; then
    echo -e "${RED}[×] 错误: 无法连接到 GitHub，请检查网络连接！${NC}"
    exit 1
fi

echo -e "${BLUE}[>] 正在拉取并合并最新代码...${NC}"
if ! git pull origin main; then
    echo -e "${YELLOW}[!] 尝试强制更新当前分支...${NC}"
    git reset --hard origin/main
    if ! git pull origin main; then
        echo -e "${RED}[×] 错误: 代码更新失败！${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}[√] 代码更新成功！${NC}"
echo ""

echo -e "${BLUE}[>] 正在检查并更新后端依赖...${NC}"

# 检查虚拟环境并更新依赖
if [ -f ".venv/bin/python" ]; then
    echo -e "${GREEN}[√] 发现虚拟环境，正在更新 Python 依赖...${NC}"
    .venv/bin/python -m pip install -r requirements.txt
else
    echo -e "${GREEN}[√] 使用系统 Python 更新依赖...${NC}"
    python3 -m pip install -r requirements.txt
fi

echo ""
echo -e "${BLUE}[>] 正在检查并更新前端依赖 (如果存在)...${NC}"
if [ -f "web_app/frontend/package.json" ]; then
    if command -v npm &> /dev/null; then
        echo -e "${GREEN}[√] 发现前端项目，正在更新 npm 依赖...${NC}"
        cd web_app/frontend
        npm install
        cd "${PROJECT_ROOT}"
    else
        echo -e "${YELLOW}[!] 未找到 npm 命令，跳过前端依赖更新。${NC}"
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║             更新流程全部完成           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}[√] 您现在可以运行启动脚本启动最新版本的系统了！${NC}"
echo ""
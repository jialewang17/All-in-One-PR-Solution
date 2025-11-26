#!/bin/bash
# 启动一体化个人助理工具 API 服务

echo "🚀 启动一体化个人助理工具 API 服务..."

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
python3 -c "import fastapi" 2>/dev/null || {
    echo "⚠️  依赖未安装，正在安装..."
    pip install -r config/requirements_v1.txt
}

# 设置环境变量
export API_PORT=${API_PORT:-8000}
export API_HOST=${API_HOST:-0.0.0.0}

# 启动服务
echo "✅ 启动服务在 http://${API_HOST}:${API_PORT}"
python3 api/main.py


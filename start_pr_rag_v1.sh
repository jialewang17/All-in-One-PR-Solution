#!/bin/bash
# 公关传播RAG系统 v1.0 启动脚本

echo "🚀 启动公关传播RAG系统 v1.0"
echo "=================================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "📋 Python版本: $python_version"

# 检查必要的Python包
echo "🔍 检查依赖包..."
required_packages=("langchain" "langchain-openai" "langchain-community" "neo4j" "python-dotenv" "PyPDF2" "openpyxl" "pandas" "python-docx" "python-pptx" "beautifulsoup4")

for package in "${required_packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo "✅ $package"
    else
        echo "❌ $package (未安装)"
        echo "请运行: pip install $package"
    fi
done

# 检查环境文件
if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
else
    echo "❌ .env 文件不存在"
    echo "请创建 .env 文件并配置必要的环境变量"
fi

# 检查数据目录
echo "📁 检查数据目录..."
data_dirs=("data" "data/raw" "data/cleaned" "data/json" "data/chunks")
for dir in "${data_dirs[@]}"; do
    if [ -d "$dir" ]; then
        file_count=$(find "$dir" -type f | wc -l)
        echo "✅ $dir ($file_count 文件)"
    else
        echo "❌ $dir (不存在)"
        mkdir -p "$dir"
        echo "✅ 已创建 $dir"
    fi
done

# 检查核心文件
echo "🔧 检查核心文件..."
core_files=("pr_rag_system_v1.py" "pr_rag_config_v1.py" "pr_enhanced_schema.py" "pr_entity_extractor.py" "pr_enhanced_neo4j_integration.py" "pr_enhanced_rag.py")
for file in "${core_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (不存在)"
    fi
done

echo ""
echo "🎯 启动选项:"
echo "1. 启动主程序"
echo "2. 查看系统配置"
echo "3. 运行功能演示"
echo "4. 运行完整测试"
echo "5. 快速查询"
echo "6. 退出"

read -p "请选择 (1-6): " choice

case $choice in
    1)
        echo "🚀 启动主程序..."
        python3 pr_rag_system_v1.py
        ;;
    2)
        echo "📊 查看系统配置..."
        python3 pr_rag_config_v1.py
        ;;
    3)
        echo "🎭 运行功能演示..."
        python3 demo_enhanced_pr_rag.py
        ;;
    4)
        echo "🧪 运行完整测试..."
        python3 test_enhanced_pr_rag.py
        ;;
    5)
        echo "⚡ 快速查询模式..."
        read -p "请输入问题: " question
        python3 ask_pr.py "$question"
        ;;
    6)
        echo "👋 再见！"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

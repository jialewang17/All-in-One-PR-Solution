@echo off
REM 简易冒烟脚本：默认运行关键自检步骤
setlocal

echo === SMOKE: v1.1 完整流程（仅检查功能登记） ===
python manage_features.py list >nul || goto :error

echo === SMOKE: 运行系统状态检查 ===
python tests/test_system_status.py || goto :error

echo === SMOKE: 运行 RAG 端到端测试 (短版) ===
python tests/test_enhanced_pr_rag_v1_1.py --smoke || goto :error

echo === SMOKE: 入口菜单（帮助信息） ===
python pr_rag_system_v1_1.py --help >nul || goto :error

echo ✅ Smoke 测试通过
goto :eof

:error
echo ❌ Smoke 测试失败 - 请检查上方输出
exit /b 1


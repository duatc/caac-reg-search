@echo off
chcp 65001 >nul
echo ==========================================
echo  民航法规智能检索系统
echo ==========================================
echo.
echo 正在启动服务，请稍等...
echo.
echo 启动后请访问: http://localhost:7860
echo 按 Ctrl+C 可停止服务
echo.
echo ==========================================

cd /d "%~dp0"
start http://localhost:7860
CAAC-RegSearch.exe

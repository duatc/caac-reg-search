@echo off
echo ==========================================
echo  民航法规检索系统 - Windows 构建脚本
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.11+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 安装依赖...
pip install -q fastapi uvicorn pydantic jieba rank-bm25 pyinstaller

echo [2/4] 构建 BM25 索引...
python build_index.py

echo [3/4] 编译 Windows 可执行文件...
pyinstaller CAAC-RegSearch.spec --noconfirm

echo [4/4] 打包...
powershell -Command "Compress-Archive -Path 'dist\CAAC-RegSearch\*' -DestinationPath 'CAAC-RegSearch-portable.zip' -Force"

echo.
echo ==========================================
echo  构建完成！
echo  文件位置: CAAC-RegSearch-portable.zip
echo ==========================================
pause

@echo off
chcp 65001 >nul
echo 正在启动 RedoxBid 液流电池储能多市场决策系统...
echo.

cd /d "%~dp0"

if not exist "app\决策主页面.py" (
    echo 错误: 找不到 app\决策主页面.py
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run "app\决策主页面.py"
    goto :end
)

where conda.exe >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=1" %%E in ('conda.exe env list ^| findstr /R /V "^#"') do (
        conda.exe run -n "%%E" python -c "import numpy, pandas, plotly, pyomo.environ, sklearn, streamlit; assert pyomo.environ.SolverFactory('cbc').available(exception_flag=False)" >nul 2>&1
        if not errorlevel 1 (
            conda.exe run -n "%%E" python -m streamlit run "app\决策主页面.py"
            goto :end
        )
    )
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    python -c "import streamlit" >nul 2>&1
    if %errorlevel% equ 0 (
        python -m streamlit run "app\决策主页面.py"
        goto :end
    )
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    py -c "import streamlit" >nul 2>&1
    if %errorlevel% equ 0 (
        py -m streamlit run "app\决策主页面.py"
        goto :end
    )
)

echo 错误: 未找到已安装 Streamlit 的 Python 环境。
echo 请先按照 README.md 创建 .venv 并安装 requirements.txt。

:end
pause

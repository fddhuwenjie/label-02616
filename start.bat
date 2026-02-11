@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================
echo   企业信息批量检查工具
echo ================================
echo.

cd /d "%~dp0"

:: 检查 Downloads 目录
if not exist "Downloads" (
    echo [警告] Downloads 目录不存在，正在创建...
    mkdir Downloads
    echo [提示] 请将 Excel 文件放入 Downloads 目录后重新运行
    pause
    exit /b 1
)

:: 检查是否有 Excel 文件
set EXCEL_COUNT=0
for %%f in (Downloads\企业信息批量查询列表_*.xlsx) do set /a EXCEL_COUNT+=1
if %EXCEL_COUNT%==0 (
    echo [错误] Downloads 目录中没有找到 Excel 文件
    echo [提示] 请确保文件名格式为: 企业信息批量查询列表_YYYYMMDD*.xlsx
    pause
    exit /b 1
)
echo 找到 %EXCEL_COUNT% 个 Excel 文件
echo.

:: 选择运行方式
echo 请选择运行方式:
echo   1) Docker 运行 (推荐，默认)
echo   2) 本地 Python 运行
echo.
set /p choice="请输入选项 [1/2，直接回车默认1]: "
if "!choice!"=="" set choice=1

:: 输入日期
echo.
echo 请输入要检查的日期 (格式: YYYYMMDD)
set /p TODAY_DATE="今日日期 [默认 20251214]: "
if "!TODAY_DATE!"=="" set TODAY_DATE=20251214

set /p PREVIOUS_DATE="前日日期 [默认 20251213，留空跳过比较]: "
if "!PREVIOUS_DATE!"=="" set PREVIOUS_DATE=20251213

if "%choice%"=="1" goto docker_run
if "%choice%"=="2" goto python_run
echo [错误] 无效选项
pause
exit /b 1

:docker_run
echo.
echo [信息] 使用 Docker 启动...

:: 检查 Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未安装 Docker
    echo 请先安装 Docker Desktop: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] Docker 未运行
    echo 请先启动 Docker Desktop
    pause
    exit /b 1
)

:: 检查 docker-compose 或 docker compose
set COMPOSE_CMD=
where docker-compose >nul 2>nul
if %errorlevel%==0 (
    set COMPOSE_CMD=docker-compose
) else (
    docker compose version >nul 2>nul
    if %errorlevel%==0 (
        set COMPOSE_CMD=docker compose
    )
)

if "!COMPOSE_CMD!"=="" (
    echo [错误] 未安装 docker-compose
    echo 请安装 Docker Compose: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo 使用: !COMPOSE_CMD!

!COMPOSE_CMD! up --build -e TODAY_DATE=!TODAY_DATE! -e PREVIOUS_DATE=!PREVIOUS_DATE!
goto end

:python_run
echo.
echo [信息] 使用本地 Python 启动...

:: 检查 Python（优先使用高版本）
set PYTHON_CMD=
for %%p in (python3.12 python3.11 python3.10 python3 python) do (
    if "!PYTHON_CMD!"=="" (
        where %%p >nul 2>nul
        if !errorlevel!==0 set PYTHON_CMD=%%p
    )
)

if "!PYTHON_CMD!"=="" (
    echo [错误] 未安装 Python
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('!PYTHON_CMD! --version') do echo 使用 %%i

:: 安装依赖
echo 安装依赖...
!PYTHON_CMD! -m pip install -q -r backend\requirements.txt

:: 运行
echo.
set TODAY_DATE=!TODAY_DATE!
set PREVIOUS_DATE=!PREVIOUS_DATE!
!PYTHON_CMD! backend\check_enterprise.py
goto end

:end
echo.
pause

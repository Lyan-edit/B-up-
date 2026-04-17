@echo off
setlocal
cd /d "%~dp0"

set "PYTHONPATH=%cd%\src;%PYTHONPATH%"
set "RUNNER="

if exist "%cd%\.venv\Scripts\python.exe" (
  set "RUNNER=%cd%\.venv\Scripts\python.exe"
)

if not defined RUNNER (
  where python >nul 2>nul
  if not errorlevel 1 set "RUNNER=python"
)

if not defined RUNNER (
  where py >nul 2>nul
  if not errorlevel 1 set "RUNNER=py -3"
)

if not defined RUNNER (
  echo.
  echo 未找到可用的 Python 运行环境。
  echo 请先安装 Python 3.11+，或在仓库目录下创建 .venv 虚拟环境。
  echo.
  pause
  exit /b 1
)

echo.
echo 正在启动 B 站 UP 一键抓取...
echo.
call %RUNNER% -m bili_up_crawler --interactive
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
  echo 程序已结束。
) else (
  echo 程序异常退出，退出码：%EXITCODE%
)
echo.
pause
exit /b %EXITCODE%

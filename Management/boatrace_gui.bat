@echo off
rem 1. 自身を最小化状態で再起動する（引数 minimized がない場合のみ）
if not "%~1"=="minimized" (
    start /min cmd /c "%~f0" minimized %*
    exit /b
)

rem 2. Pythonを実行
python "C:\boatrace\UI\boatrace_gui.py"

rem 3. 終了コードが0以外（エラー）なら画面を止める
if %errorlevel% neq 0 (
    echo.
    echo --------------------------------------------------
    echo [ERROR] プログラムが異常終了しました (Code: %errorlevel%)
    echo --------------------------------------------------
    pause
)

@echo off
setlocal enabledelayedexpansion

echo Enter password!
echo.

set /p pw=Password: 

if "%pw%"=="I am cool XD" goto correct
goto wrong


:wrong
cls
echo WRONG!
echo But, It's nothing.

endlocal
exit


:correct
cls
echo CORRECT!

endlocal
exit

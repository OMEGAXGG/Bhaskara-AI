@echo off
REM This script creates a desktop shortcut for your Bhaskara AI application that runs without showing command prompt

REM Set the path to your Python script - using the absolute path without %USERPROFILE%
set SCRIPT_PATH=C:\Projects\Bhaskara AI\AI Assistant Application By PySide\main_gui.py

REM Set the path to your Python interpreter
set PYTHON_PATH=C:\Users\HP\AppData\Local\Programs\Python\Python312\pythonw.exe

REM Set the path to your icon/image file - using the absolute path without %USERPROFILE%
set ICON_PATH=C:\Projects\Bhaskara AI\AI Assistant Application By PySide\Bhaskara AI.ico

REM Set the path for the shortcut on desktop
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Bhaskara AI.lnk

REM Create the shortcut using PowerShell - using pythonw.exe to hide command prompt
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%PYTHON_PATH%'; $Shortcut.Arguments = '\"%SCRIPT_PATH%\"'; $Shortcut.IconLocation = '%ICON_PATH%'; $Shortcut.WorkingDirectory = 'C:\Projects\Bhaskara AI\AI Assistant Application By PySide'; $Shortcut.WindowStyle = 7; $Shortcut.Save()"

echo Shortcut created successfully at %SHORTCUT_PATH%
pause
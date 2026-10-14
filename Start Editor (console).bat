@echo off
rem Same as "Start Editor.vbs" but keeps a console open to show errors.
cd /d "%~dp0"
py -3 "BCSFE Editor.pyw" %*
if errorlevel 1 pause

@echo off

cls
echo Starting the hunter forever ...  

:loop
python hunt.py
goto loop

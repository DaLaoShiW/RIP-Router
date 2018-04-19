@echo off
set /p num="Which example?: "

for /l %%x in (1, 1, 5) do start cmd /k python router.py ./configurations/example-%num%/example-%num%-config-%%x.txt
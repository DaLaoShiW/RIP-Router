@ECHO off

set /p num="Which example?: "
set count=0
for %%x in (../configurations/example-%num%/example-%num%-config-*.txt) do set /a count+=1
for /l %%x in (1, 1, %count%) do start cmd /k "cd ../ && python ./router.py ./configurations/example-%num%/example-%num%-config-%%x.txt"
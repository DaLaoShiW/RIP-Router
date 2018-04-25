#!/bin/bash
echo Which configuration?
read id

num=$(ls ../../configurations/example-$id/example-*.txt | wc -l)

for i in $(seq 1 $num)
do
    gnome-terminal -e "bash -c \"cd ../../; python3 ./router.py ./configurations/example-$id/example-$id-config-$i.txt; exec bash\""
done
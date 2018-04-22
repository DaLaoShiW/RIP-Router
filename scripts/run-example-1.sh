#!/bin/bash

for i in {1..5}
do
    gnome-terminal -e "python3 ../router.py ./configurations/example-1/example-1-config-$i.txt"
done

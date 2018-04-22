import random
import os

inp = """
1:2,3,4,8
2:9,5
3:6,7
4:2
5:7,9,4
6:1
"""
example_num = "2"

config_path = "../configurations/example-" + example_num + "/"
if os.path.isdir(config_path):
    confirm = input("That example configuration already exists. Enter 'y' to confirm overwrite: ").strip().lower()
    if confirm != "y":
        exit()

connections = {}

for line in inp.strip().splitlines():
    line = line.strip()
    parts = line.split(":")
    router = parts[0]
    if router not in connections:
        connections[router] = set(parts[1].split(","))
    else:
        connections[router] |= set(parts[1].split(","))
    for connection in parts[1].split(","):
        if connection not in connections:
            connections[connection] = set(router)
        else:
            connections[connection] |= set(router)

for router in connections:
    config = ""
    config += "router-id " + router + "\n"
    config += "input-ports "
    for connection in connections[router]:
        config += "90" + router + connection + ", "
    config = config[:-2]
    config += "\noutputs "
    for connection in connections[router]:
        randcost = random.randint(1, 4)
        config += "90" + connection + router + "/" + str(randcost) + "/" + connection + ", "
    config = config[:-2]
    config += "\nupdate-period 5"
    config_filename = "example-" + example_num + "-config-" + router + ".txt"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path + config_filename, "w+") as config_file:
        config_file.write(config)



import random
import os
from collections import OrderedDict

inp = """
1:2,3,4,8
2:9,5
3:6,7
4:2
5:7,9,4
6:1
"""
example_num = "2"
update_period = "5"
min_cost = 1
max_cost = 4


class Edge(frozenset):
    def __init__(self, one_node, another_node):
        super().__init__([one_node, another_node])

    def __str__(self):
        return set(map(str, self))

    def __repr__(self):
        return str(set(map(str, self)))


config_path = "../configurations/example-" + example_num + "/"
if os.path.isdir(config_path):
    confirm = input("That example configuration already exists. Enter 'y' to confirm overwrite: ").strip().lower()
    if confirm != "y":
        exit()

edge_costs = {}
for line in inp.strip().splitlines():
    line = line.strip()
    parts = line.split(":")
    router = parts[0]
    neighbours = set(parts[1].split(","))
    for neighbour in neighbours:
        edge = Edge(router, neighbour)
        edge_costs[edge] = random.randint(min_cost, max_cost)
edge_costs = OrderedDict(edge_costs)

connections = {}
for line in inp.strip().splitlines():
    line = line.strip()
    parts = line.split(":")
    router = parts[0]
    neighbours = set(parts[1].split(","))
    if router not in connections:
        connections[router] = neighbours
    else:
        connections[router] |= neighbours
    for neighbour in neighbours:
        if neighbour not in connections:
            connections[neighbour] = set(router)
        else:
            connections[neighbour] |= set(router)

num_routers = max(map(int, connections.keys()))
adj_matrix = [[0 for i in range(num_routers)] for j in range(num_routers)]
for router, neighbours in connections.items():
    for neighbour in neighbours:
        adj_matrix[int(router) - 1][int(neighbour) - 1] = 1

edges = list(edge_costs.keys())
num_edges = len(edge_costs.keys())
inc_matrix = [[0 for k in range(num_edges)] for l in range(num_routers)]
for edge, cost in edge_costs.items():
    edge_num = edges.index(edge)
    edge_list = list(edge)
    node1 = edge_list[0]
    node2 = edge_list[1]
    inc_matrix[int(node1) - 1][edge_num] = cost
    inc_matrix[int(node2) - 1][edge_num] = cost

for router in connections:
    config = ""
    config += "router-id " + router + "\n"
    config += "input-ports "
    for neighbour in connections[router]:
        config += "90" + router + neighbour + ", "
    config = config[:-2]
    config += "\noutputs "
    for neighbour in connections[router]:
        cost = edge_costs[Edge(router, neighbour)]
        config += "90" + neighbour + router + "/" + str(cost) + "/" + neighbour + ", "
    config = config[:-2]
    config += "\nupdate-period " + update_period
    config_filename = "example-" + example_num + "-config-" + router + ".txt"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path + config_filename, "w+") as config_file:
        config_file.write(config)

print("\nConfig files successfully created.\n")
print("VISUALISE USING THIS ONLINE TOOL: http://graphonline.ru/en/")
print("\nADJACENCY MATRIX:")
for line in adj_matrix:
    print(",".join(map(str, line)))
print("\nINCIDENCE MATRIX:")
for line in inc_matrix:
    print(",".join(map(str, line)))

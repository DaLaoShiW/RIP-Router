import random
import os
import re

from router import RouteInfos
import dijkstras

# ////////////////////////////// OPTIONS \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ #
# Router ids must be sequential, starting from 1, skipping no numbers.
undirected_adjacency_list = """
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
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ OPTIONS ////////////////////////////// #

# Check given undirected adjacency list
router_ids = set(
    map(int, [item for item in map(str.strip, re.split("[:,\n]", undirected_adjacency_list.strip())) if item.isdigit()])
)
expected_router_ids = set(range(1, int(max(router_ids)) + 1))
if router_ids != expected_router_ids:
    print("Malformed adjacency list given.")
    print("The following router ids were skipped:", expected_router_ids - router_ids)
    exit()


class Edge(frozenset):
    def __new__(cls, *args):
        return super().__new__(cls, args)

    def __str__(self):
        return str(set(map(str, self)))

    def __repr__(self):
        return str(set(map(str, self)))


# Warn if example configuration already exists.
config_path = "../configurations/example-" + example_num + "/"
if os.path.isdir(config_path):
    confirm = input(
        "That example configuration already exists. Enter 'y' to confirm overwrite (will invalidate network diagram): "
    ).strip().lower()
    if confirm != "y":
        exit()

# Build the edges dictionary, mapping edges (immutable pairs of router ids) to costs (randomly generated), and
# build the connections dictionary, mapping router ids to the set of routers they are connected to.
edge_costs = {}
connections = {}
for line in undirected_adjacency_list.strip().splitlines():
    line = line.strip()
    parts = line.split(":")
    router = parts[0]
    neighbours = set(parts[1].split(","))
    for neighbour in neighbours:
        edge_costs[Edge(router, neighbour)] = random.randint(min_cost, max_cost)
    if router not in connections:
        connections[router] = neighbours
    else:
        connections[router] |= neighbours
    for neighbour in neighbours:
        if neighbour not in connections:
            connections[neighbour] = set(router)
        else:
            connections[neighbour] |= set(router)

# Build the Graph object.
graph = dijkstras.Graph()
for router_id in connections:
    graph.add_node(router_id)
for edge, cost in edge_costs.items():
    graph.add_edge(*edge, distance=cost)

# Initialise both output matrices.
num_routers = len(connections.keys())
num_edges = len(edge_costs.keys())
adjacency_matrix = [[0 for i in range(num_routers)] for j in range(num_routers)]
incidence_matrix = [[0 for k in range(num_edges)] for l in range(num_routers)]

# Build both output matrices.
for edge_num, ((node_1, node_2), cost) in enumerate(edge_costs.items()):
    adjacency_matrix[int(node_1) - 1][int(node_2) - 1] = cost
    adjacency_matrix[int(node_2) - 1][int(node_1) - 1] = cost

    incidence_matrix[int(node_1) - 1][edge_num] = cost
    incidence_matrix[int(node_2) - 1][edge_num] = cost

# Cross check matrices validity
passed = True
for column in zip(*incidence_matrix):
    cost = max(column)
    node_1, node_2 = [index + 1 for index, cost in enumerate(column) if cost != 0]

    passed = adjacency_matrix[int(node_1) - 1][int(node_2) - 1] == cost if passed else False
    passed = adjacency_matrix[int(node_2) - 1][int(node_1) - 1] == cost if passed else False
count = 0
for index_1, row in enumerate(adjacency_matrix):
    for index_2, cost in enumerate(row):
        column = [0 for _ in range(num_routers)]
        router_id_1 = index_1 + 1
        column[index_1] = cost
        column[index_2] = cost
        if any(column):
            passed = column in [list(tuple_column) for tuple_column in zip(*incidence_matrix)] if passed else False
            count += 1
passed = count / 2 == num_edges if passed else False
if not passed:
    print("Sorry! Matrices malformed.")
    exit()

# Build config files needed for router operation.
for router in connections:
    config = "router-id " + router + "\n"
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

# Build expected converged routing table files
for router_id in connections:
    converged_routing_table = "{\n"
    for target_router_id in sorted(connections):
        if router_id == target_router_id:
            continue
        cost, path = dijkstras.shortest_path(graph, router_id, target_router_id)
        first_hop = path[1]  # path[0] is router_id itself.
        converged_routing_table += '\t"{}": {{\n'.format(target_router_id)
        converged_routing_table += '\t\t"{}": {},\n'.format(RouteInfos.FIRST_HOP, first_hop)
        converged_routing_table += '\t\t"{}": {}\n'.format(RouteInfos.COST, cost)
        converged_routing_table += "\t},\n"
    converged_routing_table = converged_routing_table[0:-2]
    converged_routing_table += "\n}"
    expected_dir_path = config_path + "converged-routing-tables/"
    os.makedirs(os.path.dirname(expected_dir_path), exist_ok=True)
    with open(expected_dir_path + "routing-table-" + router_id + ".json", "w+") as expected_file:
        expected_file.write(converged_routing_table)

# Print results.
print("\nConfig files successfully created for example network", example_num + ".\n")
print("VISUALISE USING THIS ONLINE TOOL: http://graphonline.ru/en/")
print("\nADJACENCY MATRIX:")
for line in adjacency_matrix:
    print(",".join(map(str, line)))
print("\nNO COST ADJACENCY MATRIX:")
for line in adjacency_matrix:
    line = [1 if i != 0 else 0 for i in line]
    print(",".join(map(str, line)))
print("\nINCIDENCE MATRIX:")
for line in incidence_matrix:
    print(",".join(map(str, line)))

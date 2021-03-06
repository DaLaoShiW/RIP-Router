import random
import math
import os
import re
import sys

import dijkstras

from router import RouteInfos

sys.path.append('../')

# ////////////////////////////// OPTIONS \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ #
# Router ids must be sequential, starting from 1, skipping no numbers.
undir_adj_list = """
1:2
"""

example_num = "10"
update_period = "5"
min_cost = 1
max_cost = 1

# Used to weight costs.
average_cost = None  # Can be set to None to have no weighting in the range (min_cost, max_cost)
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ OPTIONS ////////////////////////////// #

# Build the costs list, containing the costs that routers will randomly choose from, if costs arent defined in adj list.
if average_cost:
    cost_range = max_cost - min_cost + 1
    costs = []
    # Decent guess at costs with given average.
    for i in range(min_cost, max_cost + 1):
        try:
            amount = round(cost_range / (abs(i - average_cost)))
        except ZeroDivisionError:
            amount = cost_range * 5
        costs += [i] * amount
    # Brute force until the average of the costs is far better.
    while True:
        costs_average = sum(costs)/len(costs)
        difference = costs_average - average_cost
        if abs(difference) < 0.0001:
            break
        if difference > 0:
            costs.append(random.randint(min_cost, math.floor(average_cost)))
        else:
            costs.append(random.randint(math.ceil(average_cost), max_cost))
else:
    costs = [i for i in range(min_cost, max_cost + 1)]


# Check given undirected adjacency list
router_ids = set(
    map(
        int,
        [item for item in map(str.strip, re.split("[:,]|(?:\n|\r\n|\r)", undir_adj_list.strip())) if item.isdigit()]
    )
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
        "Example {} already exists. Enter 'y' to confirm overwrite (will invalidate any diagrams): ".format(example_num)
    ).strip().lower()
    if confirm != "y":
        exit()

# Build the edges dictionary, mapping edges (immutable pairs of router ids) to costs (randomly generated), and
# build the connections dictionary, mapping router ids to the set of routers they are connected to.
edge_costs = {}
connections = {str(i): set() for i in router_ids}
for line in undir_adj_list.strip().splitlines():
    line = line.strip()
    parts = line.split(":")
    router = parts[0]

    full_neighbours = set(parts[1].split(","))
    for neighbour in full_neighbours:
        cost_parts = neighbour.split('w')
        neighbour = cost_parts[0]
        if len(cost_parts) > 1:
            edge_costs[Edge(router, neighbour)] = int(cost_parts[1])
        else:
            edge_costs[Edge(router, neighbour)] = random.choice(costs)

    neighbours = set([part.split('w')[0] for part in parts[1].split(",")])

    connections[router] |= neighbours
    for neighbour in neighbours:
        connections[neighbour] |= {router}

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


def pad_zero(str_num):
    if len(str_num) == 2:
        return str_num
    elif len(str_num) == 1:
        return "0" + str_num

for router in connections:
    config = "router-id " + router + "\n"
    config += "input-ports "
    for neighbour in connections[router]:
        config += "5" + pad_zero(router) + pad_zero(neighbour) + ", "
    config = config[:-2]
    config += "\noutputs "
    for neighbour in connections[router]:
        cost = edge_costs[Edge(router, neighbour)]
        config += "5" + pad_zero(neighbour) + pad_zero(router) + "/" + str(cost) + "/" + neighbour + ", "
    config = config[:-2]
    config += "\nupdate-period " + update_period
    config_filename = "example-" + example_num + "-config-" + router + ".txt"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path + config_filename, "w+") as config_file:
        config_file.write(config)

# Build expected converged routing table files
for router_id in router_ids:
    router_id = str(router_id)
    converged_routing_table = "{\n"
    for target_router_id in router_ids:
        target_router_id = str(target_router_id)
        if router_id == target_router_id:
            continue
        try:
            cost, path = dijkstras.shortest_path(graph, router_id, target_router_id)
            if cost >= 16:
                print("WARNING! A minimum cost path of {} was found (16 or higher).".format(cost))
                input("Enter anything to continue...")
            first_hop = path[1]  # path[0] is router_id itself.
            converged_routing_table += '\t"{}": {{\n'.format(target_router_id)
            converged_routing_table += '\t\t"{}": {},\n'.format(RouteInfos.FIRST_HOP, first_hop)
            converged_routing_table += '\t\t"{}": {}\n'.format(RouteInfos.COST, cost)
            converged_routing_table += "\t},\n"
        except KeyError:
            print("Could not create a path between two nodes of the graph. This probably means the graph described "
                  "by your adjacency list is disjoint")
            exit(1)
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

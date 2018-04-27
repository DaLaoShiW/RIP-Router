import random
import math


class NodeInfo:
    max_degree = "assigned_degree"
    current_neighbours = "current_neighbours"
    

def get_adj_list(num_routers=1, min_degree=1, max_degree=1, connectivity=None, force_connect_close=False):
    if connectivity:
        min_degree = max(1, int((0.5 * connectivity * num_routers)))
        max_degree = math.ceil(1.5 * connectivity * num_routers)
        print("Min degree: {}. Max degree: {}.".format(min_degree, max_degree))

    routers = list(range(1, num_routers + 1))
    connections = {}
    for router in routers:
        connections[router] = {
            NodeInfo.max_degree: random.randint(min_degree, max_degree),
            NodeInfo.current_neighbours: []
        }

    for router in routers:
        assigned_degree = connections[router][NodeInfo.max_degree]
        current_degree = len(connections[router][NodeInfo.current_neighbours])

        if current_degree == assigned_degree:
            continue
        more_degree = assigned_degree - current_degree

        eligible_neighbours = []
        for neighbour in [r for r in routers if r != router]:
            if assigned_degree == 1 and connections[neighbour][NodeInfo.max_degree] == 1:
                continue
            if neighbour in connections[router][NodeInfo.current_neighbours]:
                continue
            if len(connections[neighbour][NodeInfo.current_neighbours]) == connections[neighbour][NodeInfo.max_degree]:
                continue
            eligible_neighbours.append(neighbour)
        if not eligible_neighbours:
            continue

        for _ in range(more_degree):
            if not eligible_neighbours:
                continue
            if not force_connect_close:
                if len(eligible_neighbours) == 1:
                    rand_index = 0
                else:
                    rand_index = random.randint(0, len(eligible_neighbours) - 1)
                rand_neighbour = eligible_neighbours[rand_index]
            if force_connect_close:
                closest_neighbour = min(eligible_neighbours, key=lambda x: abs(x - router))
                rand_neighbour = closest_neighbour

            connections[router][NodeInfo.current_neighbours] += [rand_neighbour]
            connections[rand_neighbour][NodeInfo.current_neighbours] += [router]
            eligible_neighbours.remove(rand_neighbour)

    undir_adj_list = "UNDIRECTED ADJACENCY LIST:"
    for router in routers:
        undir_adj_list += "\n{}:{}".format(router, ",".join(map(str, connections[router][NodeInfo.current_neighbours])))

    return undir_adj_list.strip()

# NOT GURANTEED TO FORM A NON-DISJOINT GRAPH

print(get_adj_list(num_routers=50, min_degree=1, max_degree=3, force_connect_close=True))
# print(get_adj_list(num_routers=10000, connectivity=0.05))

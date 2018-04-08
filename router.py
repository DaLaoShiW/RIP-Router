import sys
import json
import random
import time
import os
from collections import OrderedDict
from select import select

from config_loader import Loader
from packet import *


def simplified_socket_str(a_socket):
    try:
        return "<Socket(" + str(a_socket.getsockname()[1]) + " -> " + str(a_socket.getpeername()[1]) + ")>"
    except OSError:
        return "<Socket(" + str(a_socket.getsockname()[1]) + ")>"


socket.__str__ = simplified_socket_str
socket.__repr__ = simplified_socket_str


class Router:
    INFINITY = 16

    READ_TIMEOUT = 2  # How long the router should wait for sockets to be ready to be read from

    def __init__(self, config_lines):
        self.id = None
        self.input_ports = []
        self.outputs = {}
        self.update_period = None
        self.timeout_length = None
        self.deletion_length = None
        # Assign all variables above
        self.config_loader = Loader(config_lines, self)
        self.config_loader.load()

        self.input_sockets = {}
        self.routing_table = {}

        self.time_of_last_update = time.time()
        self.triggered_updates = []  # List of router ids

    def bind_sockets(self):
        """ Bind sockets to input ports """
        # TODO: use try except block to gracefully handle socket errors such as ports already bound
        for input_port in self.input_ports:
            a_socket = socket(AF_INET, SOCK_DGRAM)
            a_socket.bind(("localhost", input_port))
            self.input_sockets[input_port] = a_socket

    def initialise_routing_table(self):
        """  Initialise the router's routing table """
        os.makedirs(os.path.dirname("./json-memory/"), exist_ok=True)
        with open("./json-memory/routing-table-" + str(self.id) + ".json", "w+") as routing_table_file:
            if routing_table_file.readlines():
                # routing_table_json = json.load(routing_table_file)
                # TODO: check if this json contains at least the info from 'outputs' (might contain more info)
                pass
            else:
                routing_table = {}

                for router_id in self.outputs:
                    inner_object = OrderedDict([
                        ("first_hop", router_id),
                        ("cost", self.outputs[router_id][1]),
                        ("learned_from", "N/A"),
                        ("time", 0)
                    ])
                    row = {router_id: inner_object}
                    routing_table.update(row)

                json.dump(routing_table, routing_table_file, indent=4)
                self.routing_table = routing_table

    def run(self):
        """ Check and process incoming packets (select) and timing events."""
        if self.triggered_updates:
            self.send_updates(self.triggered_updates)
            self.triggered_updates = []

        if time.time() - self.time_of_last_update >= self.update_period:
            print("\tTime to send updates! --->")

            routers_to_delete = []
            # Checking times and stuff
            for router_id, row in self.routing_table.items():
                updated_row = row
                updated_row['time'] = row['time'] + time.time() - self.time_of_last_update

                if row['cost'] != self.INFINITY and updated_row['time'] >= self.timeout_length:
                    updated_row['cost'] = self.INFINITY
                    self.triggered_updates.append(router_id)

                needs_deletion = updated_row['time'] >= self.timeout_length + self.deletion_length

                if updated_row['cost'] == self.INFINITY and needs_deletion:
                    routers_to_delete.append(router_id)

                updated_row = { router_id: updated_row }
                self.routing_table.update(updated_row)

            for router_id in routers_to_delete:
                self.routing_table.pop(router_id)

            self.send_updates(self.routing_table.keys())

            self.time_of_last_update = time.time() + random.randint(-5, 5)

        read_ready = select(self.input_sockets.values(), [], [], self.READ_TIMEOUT)[0]
        for a_socket in read_ready:
            buffer = a_socket.recv(512)
            rip_packet = RIPPacket(buffer)

            input_router_id = rip_packet.from_router_id
            input_router_cost = self.outputs[input_router_id][1]

            self.routing_table[input_router_id]['time'] = 0

            for entry in rip_packet.entries:

                new_cost = min(input_router_cost + entry['cost'], self.INFINITY)

                existing_cost = self.INFINITY
                existing_first_hop = input_router_id

                timer = 0

                if entry['router_id'] in self.routing_table:
                    existing_entry = self.routing_table[entry['router_id']]
                    existing_cost = existing_entry['cost']
                    existing_first_hop = existing_entry['first_hop']
                    timer = existing_entry['time']

                if new_cost == self.INFINITY and existing_cost != self.INFINITY:
                    timer = self.timeout_length
                    self.triggered_updates.append(entry['router_id'])

                if entry['router_id'] == self.id:
                    continue

                if new_cost != self.INFINITY and new_cost == existing_cost and existing_first_hop == input_router_id:
                    self.routing_table[entry['router_id']]['time'] = 0
                    continue

                if new_cost < existing_cost or (new_cost != existing_cost and existing_first_hop == input_router_id):

                    if new_cost != self.INFINITY:
                        timer = 0

                    inner_object = OrderedDict([
                        ("first_hop", input_router_id),
                        ("cost", new_cost),
                        ("learned_from", input_router_id),
                        ("time", timer)
                    ])
                    row = {entry['router_id']: inner_object}

                    self.routing_table.update(row)

            print("Routing Table: ", json.dumps(self.routing_table, indent=4))

    def send_updates(self, router_ids):
        router_ids = set(router_ids)
        for output in self.outputs.values():
            rip_packet = RIPPacket()

            for router_id in router_ids:
                if router_id not in self.routing_table.keys():
                    continue
                row = self.routing_table[router_id]
                # Split Horizon with Poisoned Reverse
                rip_packet.add_entry(router_id, self.INFINITY if row['learned_from'] == router_id else row['cost'])

            rip_packet.send(output[0], self.id)


def main():
    args = sys.argv
    if len(args) < 2:
        print("Missing config filename!")
        return

    config_filename = args[1]
    with open(config_filename, "r") as config_file:
        config_lines = config_file.readlines()

    router = Router(config_lines)
    router.bind_sockets()
    router.initialise_routing_table()
    print(router.routing_table)

    while True:
        router.run()


if __name__ == "__main__":
    main()

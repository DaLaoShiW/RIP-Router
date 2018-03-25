from socket import *
from select import select
from collections import OrderedDict
import sys
import json

import config_loader


def simplified_socket_str(a_socket):
    try:
        return "<Socket(" + str(a_socket.getsockname()[1]) + " -> " + str(a_socket.getpeername()[1]) + ")>"
    except OSError:
        return "<Socket(" + str(a_socket.getsockname()[1]) + ")>"

socket.__str__ = simplified_socket_str
socket.__repr__ = simplified_socket_str


class Router:
    INFINITY = 16

    READ_TIMEOUT = 3  # How long the router should wait for sockets to be ready to be read from.

    def __init__(self, config_lines):
        self.id = None
        self.input_ports = []
        self.outputs = {}
        self.update_period = None
        self.timeout_length = None

        self.config_loader = config_loader.Loader(config_lines, self)
        self.config_loader.load()

        self.input_sockets = {}

        self.routing_table = {}

    def bind_sockets(self):
        """ Bind sockets to input ports """
        for input_port in self.input_ports:
            a_socket = socket(AF_INET, SOCK_DGRAM)
            a_socket.bind(("localhost", input_port))
            self.input_sockets[input_port] = a_socket

    def initialise_routing_table(self):
        """  Initialise the router's routing table """
        with open("./routing-table-" + str(self.id) + ".json", "w+") as routing_table_file:
            if routing_table_file.readlines():
                # routing_table_json = json.load(routing_table_file)
                # TODO: check if this json contains the info from 'outputs'
                pass
            else:
                routing_table = {}
                for router_id in self.outputs:
                    inner_object = OrderedDict([
                        ("first_hop", router_id),
                        ("cost", self.outputs[router_id][1]),
                        ("learned=from", "N/A"),
                        ("time", 0)
                    ])
                    row = {router_id: inner_object}
                    routing_table.update(row)
                json.dump(routing_table, routing_table_file, indent=4)
                self.routing_table = routing_table

    def run(self):
        """ Check and process incoming packets (select) and timing events."""
        read_ready = select(self.input_sockets.values(), [], [], self.READ_TIMEOUT)[0]
        for a_socket in read_ready:
            print("READ READY!", a_socket)
            buffer = a_socket.recv(3)
            print("RECEIVED:", buffer)
        for output in self.outputs.values():
            a_socket = socket(AF_INET, SOCK_DGRAM)
            a_socket.sendto(b"Hey", ("localhost", output[0]))


def main():
    args = sys.argv
    if len(args) < 2:
        print("Missing config filename!")
        return

    config_filename = args[1]
    config_file = open(config_filename, "r")
    config_lines = config_file.readlines()
    config_file.close()

    router = Router(config_lines)
    router.bind_sockets()
    router.initialise_routing_table()

    # while True:
    #     router.run()

if __name__ == "__main__":
    main()

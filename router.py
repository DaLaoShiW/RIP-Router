import json
import random
import time
from datetime import datetime
from collections import OrderedDict
from packet import *
from select import select
import sys
import os

from config_loader import Loader


class Router:
    INFINITY = 16
    READ_TIMEOUT = 1  # How long in seconds a router should wait for sockets to be ready to be read from.

    def __init__(self, config_lines):
        self.id = None
        self.input_ports = []
        self.outputs = {}  # Directly connected routers. Map ids to (port, cost) pairs.
        self.update_period = None
        self.timeout_length = None
        self.deletion_length = None

        # Assign all above variables.
        self.config_loader = Loader(config_lines, self)
        self.config_loader.load()

        self.input_sockets = {}
        self.routing_table = {}

        self.time_of_last_update = int(time.time())
        self.triggered_updates = []  # List of destination router ids.

        self.load = False
        self.verbose = False
        self.config_dir = None

        self.log("Router created!\n" + self.config_loader.get_pretty_config_values())

    def log(self, *args):
        message = " ".join(map(str, args))
        date_time_prefix = "<" + str(datetime.now()).split(".")[0] + "> "
        message = ("\n" + " " * len(date_time_prefix)).join(message.split("\n"))
        os.makedirs(os.path.dirname("./logs/"), exist_ok=True)
        with open("./logs/log-" + str(self.id) + ".txt", "a+") as log_file:
            log_file.write(date_time_prefix + message + "\n\n")

    def check_if_converged(self):
        """ Check to see if the routing table has converged to the expected routing table, if one exists. """
        if os.path.isdir(self.config_dir + "/converged-routing-tables"):
            routing_table_path = "/converged-routing-tables/routing-table-" + str(self.id) + ".json"
            with open(self.config_dir + routing_table_path) as expected_routing_table_file:
                expected_routing_table = json.load(expected_routing_table_file)
                simplified_routing_table = json.loads(json.dumps(self.routing_table))
                matching = True
                for dest_id in expected_routing_table:
                    if dest_id not in simplified_routing_table:
                        matching = False
                        break
                    our_entry = simplified_routing_table[dest_id]
                    expected_entry = expected_routing_table[dest_id]
                    matching = our_entry[RouteInfos.FIRST_HOP] == expected_entry[RouteInfos.FIRST_HOP]
                    if not matching:
                        break
                    matching = our_entry[RouteInfos.COST] == expected_entry[RouteInfos.COST]
                    if not matching:
                        break
                if matching:
                    print("== Routing table matches expected routing table ==")
                    self.log("Routing table converged\n" + self.get_string_routing_table())

    def bind_input_sockets(self):
        """ Bind sockets to input ports. """
        for input_port in self.input_ports:
            a_socket = socket(AF_INET, SOCK_DGRAM)
            try:
                a_socket.bind(("localhost", input_port))
                self.log("Bound input socket to port", input_port)
            except OSError:
                print("Could not bind socket to port " + str(input_port) + ". A socket is already bound to this port.")
                self.log("Could not bind input socket to port", input_port)
                exit(12)
            self.input_sockets[input_port] = a_socket

    def initialise_routing_table(self):
        """  Initialise the router's routing table. """
        os.makedirs(os.path.dirname("./router-memory/"), exist_ok=True)

        # Read the last config directory opened, clear router memory if this is a different config.
        if os.path.isfile("./router-memory/last-config-dir"):
            with open("./router-memory/last-config-dir", 'r+') as last_config_dir:
                if self.config_dir != last_config_dir.readline():
                    [
                        os.remove(os.path.join("./router-memory/", f))
                        for f in os.listdir("./router-memory/") if f.endswith(".json")
                    ]

        # Write current config dir to router-memory
        with open("./router-memory/last-config-dir", 'w') as new_config_dir:
            new_config_dir.write(self.config_dir)

        with open("./router-memory/routing-table-" + str(self.id) + ".json", "a+") as routing_table_file:
            routing_table_file.seek(0)
            if routing_table_file.readlines() and self.load:
                print("Loading routing table from memory")
                routing_table_file.seek(0)

                def object_hook(d):
                    if set(d.keys()) == {RouteInfos.FIRST_HOP, RouteInfos.COST, RouteInfos.TIMER}:
                        return RouteInfo(d[RouteInfos.FIRST_HOP], d[RouteInfos.COST], d[RouteInfos.TIMER])
                    else:
                        return {int(k) if str(k).isdigit() else k: v for k, v in d.items()}
                self.routing_table = json.load(
                    routing_table_file,
                    object_hook=object_hook
                )
                self.log("Routing table loaded from memory")
            else:
                self.log("Initialsing routing table")
                for router_id in self.outputs:
                    self.update_routing_table_entry(router_id, router_id, self.outputs[router_id][1], 0)
        self.save_routing_table()

    def save_routing_table(self):
        """ Save this router's routing table to memory. """
        os.makedirs(os.path.dirname("./router-memory/"), exist_ok=True)
        with open("./router-memory/routing-table-" + str(self.id) + ".json", "w+") as routing_table_file:
            json.dump(self.routing_table, routing_table_file, indent=4)
        self.log("Saved routing table to memory")

    def get_string_routing_table(self):
        """ Print this router's routing table, in a table format. """
        table = ""
        row_format = "{:" + str(len("Destination")) + "} | {:" + str(len("First hop")) + "} {:" + str(len("Cost")) + \
                     "} {:" + str(len("Timer")) + "}"
        table += row_format.format("Destination", "First hop", "Cost", "Timer")
        for dest_id, route_info in sorted(self.routing_table.items(), key=lambda x: x[0]):
            table += "\n" + row_format.format(
                dest_id, route_info[RouteInfos.FIRST_HOP], route_info[RouteInfos.COST], route_info[RouteInfos.TIMER]
            )
        return table

    def update_routing_table_entry(self, router_id, first_hop=None, cost=None, timer=None):
        """ Update or create a particular routing table entry, with given new values. """
        if router_id in self.routing_table:
            entry = self.routing_table[router_id]
            old_entry = entry.copy()
            entry[RouteInfos.FIRST_HOP] = first_hop if first_hop is not None else entry[RouteInfos.FIRST_HOP]
            entry[RouteInfos.COST] = cost if cost is not None else entry[RouteInfos.COST]
            entry[RouteInfos.TIMER] = timer if timer is not None else entry[RouteInfos.TIMER]
            self.routing_table.update({router_id: entry})
            self.log(
                "Updated routing table entry for the route to",
                str(router_id) + "\nOld:", str(old_entry) + "\nNew:", entry
            )
        elif {first_hop, cost, timer} == {None}:
            raise ValueError(
                "If a destination router id not already in the routing table is given, "
                "then all fields (function arguments) must be defined "
            )
        else:
            entry = RouteInfo(first_hop, cost, timer)
            self.routing_table.update({router_id: entry})
            self.log("Created new routing table entry for a route to", str(router_id) + "\nNew:", entry)

    def update_routing_table_timing(self):
        """ Update the router's routing table, based on timing configuration. """
        # Keep track of the routes that need to be deleted from the routing table.
        routes_to_delete = []
        # Iterate over entries in the routing table.
        for router_id, route_info in self.routing_table.items():
            # Update the route's timer field.
            self.update_routing_table_entry(
                router_id,
                timer=route_info[RouteInfos.TIMER] + int(time.time()) - self.time_of_last_update
            )
            # If the route info has timed out (and wasn't already), set the route's cost to infinity.
            timed_out = route_info[RouteInfos.TIMER] >= self.timeout_length
            if timed_out and route_info[RouteInfos.COST] != self.INFINITY:
                self.log("Setting cost of route to", router_id, "to infinity, since it has timed out")
                self.update_routing_table_entry(router_id, cost=self.INFINITY)
                # Sending a triggered update here is redundant, as this method is always called before sending updates.

            # Flag the route for deletion if its update timer field is sufficiently large.
            # Cannot delete them from the routing table now, since it is being iterated over.
            deletion_timed_out = route_info[RouteInfos.TIMER] >= self.deletion_length
            if route_info[RouteInfos.COST] == self.INFINITY and deletion_timed_out:
                self.log("Deleting route to", router_id, "since it has been unreachable for too long")
                routes_to_delete.append(router_id)
        # Delete any and all routes from the routing table, that were flagged for deletion.
        for router_id in routes_to_delete:
            self.routing_table.pop(router_id)
        self.save_routing_table()

    def send_updates(self, destination_router_ids):
        """ Send a RIP update packet for each given destination router id to all outputs (neighbours). """
        # Remove duplicate router ids.
        destination_router_ids = set(destination_router_ids)
        self.log(
            "Sending routing update packets to all neighbours for the routes to",
            ", ".join(map(str, destination_router_ids))
        )
        for neighbour_id, (port, cost) in self.outputs.items():
            # Create the RIP packet to send to this output.
            rip_packet = RIPPacket()
            # Add entries to the RIP packet.
            for destination_router_id in destination_router_ids:
                if destination_router_id not in self.routing_table:
                    continue
                route_info = self.routing_table[destination_router_id]
                # Add the entry, with a cost of infinity if the first hop to the destination is the router this packet
                # is being sent to (split horizon with poisoned reverse).
                rip_packet.add_entry(
                    destination_router_id,
                    self.INFINITY if route_info[RouteInfos.FIRST_HOP] == neighbour_id else route_info[RouteInfos.COST]
                )
            rip_packet.send(port, self.id)

    def process_inputs(self):
        """ Process any and all inputs from neighbour routers. Updating routing table where necessary. """
        # Read any and all information from input sockets.
        read_ready = select(self.input_sockets.values(), [], [], self.READ_TIMEOUT)[0]
        for input_socket in read_ready:

            # Form a RIP Packet from the input socket's buffer.
            buffer = input_socket.recv(512)
            rip_packet = RIPPacket(buffer)

            if not rip_packet.validate():
                continue

            # Get the id of the input (neighbour) router that has sent the update.
            input_router_id = rip_packet.from_router_id
            self.log(
                "Processing routing update packet from router",
                input_router_id, "from port", input_socket.getsockname()[1]
            )

            # Get the cost of the route to the input router that has sent the update.
            input_router_cost = self.outputs[input_router_id][1]
            # Reset the timer field of the route to the input router, as this update verifies it is still alive.
            # If this router's known link cost is less than the existing route, update the cost.
            current_input_router_cost = self.routing_table[input_router_id][RouteInfos.COST]
            input_router_cost_update = None if current_input_router_cost <= input_router_cost else input_router_cost
            self.update_routing_table_entry(input_router_id, timer=0, cost=input_router_cost_update)

            for entry in rip_packet.entries:
                destination_router_id = entry["router_id"]

                # If the entry's cost is over infinity, set it to infinity.
                if entry[RouteInfos.COST] > self.INFINITY:
                    self.log("Received routing update packet entry with a cost larger than infinity")
                    entry[RouteInfos.COST] = self.INFINITY

                # If the entry's destination router id is this router, skip the entry.
                if destination_router_id == self.id:
                    continue

                # Get the update cost of the route based on the cost to the input router, and the input routers cost of
                # the route, limited to infinity.
                update_cost = min(input_router_cost + entry[RouteInfos.COST], self.INFINITY)

                if destination_router_id not in self.routing_table:
                    if update_cost != self.INFINITY:
                        self.log("Processing routing update packet entry for a route not yet in the routing table")
                        # The entry describes a reachable route this router does not have,
                        # so add the route to the routing table.
                        self.update_routing_table_entry(
                            destination_router_id,
                            first_hop=input_router_id,
                            cost=update_cost,
                            timer=0
                        )
                else:
                    self.log("Processing routing update packet entry for a route already in the routing table")
                    existing_route_info = self.routing_table[destination_router_id]
                    input_is_first_hop = input_router_id == existing_route_info[RouteInfos.FIRST_HOP]

                    if input_is_first_hop and update_cost != self.INFINITY:
                        # At the very least, even if the cost hasn't changed, the route's timer should be reset.
                        self.update_routing_table_entry(destination_router_id, timer=0)

                    cost_changed = update_cost != existing_route_info[RouteInfos.COST]
                    cost_lower = update_cost < existing_route_info[RouteInfos.COST]
                    if (input_is_first_hop and cost_changed) or cost_lower:
                        self.log("Processing routing update packet entry with updated cost")
                        self.update_routing_table_entry(
                            destination_router_id,
                            first_hop=input_router_id,
                            cost=update_cost,
                            timer=self.timeout_length if update_cost == self.INFINITY else 0
                        )
                        if update_cost == self.INFINITY:
                            self.log("Cost=INF. Flagging route to", destination_router_id, "for triggered update")
                            self.triggered_updates.append(destination_router_id)

        # Only print and save routing table if there was at least one input to process.
        if read_ready:
            if self.verbose:
                print("<--- Processed input. Routing table:")
            else:
                clear = lambda: os.system('cls')
                clear()

            print(self.config_loader.get_pretty_config_values(self.verbose))
            print(self.get_string_routing_table())
            self.check_if_converged()
            self.save_routing_table()

    def run(self):
        """ Process outputs and inputs. Send any triggered updates and handle timing and garbage collection. """
        while True:
            try:  # Temporary. To avoid Windows 10 bug when using print() statements to cmd.exe stdout.
                # If there is any router ids in the triggered update queue, send the updates.
                if self.triggered_updates:
                    if self.verbose:
                        print("\t---> Sending triggered update(s) to all neighbours.")
                    self.log("Sending triggered update(s) to all neighbours")
                    self.send_updates(self.triggered_updates)
                    # Clear the queue.
                    self.triggered_updates = []

                # If it is time to send updates, update the routing table, then send it.
                if time.time() - self.time_of_last_update >= self.update_period + random.randint(-5, 5):
                    self.log("Updating routing table based on timeouts")
                    self.update_routing_table_timing()
                    if self.verbose:
                        print("\t---> Sending routing table to all neighbours.")
                    self.log("Sending routing table to all neighbours")
                    self.send_updates(self.routing_table.keys())
                    self.time_of_last_update = int(time.time())

                self.process_inputs()
            except OSError:
                pass


# Enum for safer referral to routing table field names.
class RouteInfos:
    FIRST_HOP = "first-hop"
    COST = "cost"
    TIMER = "timer"


class RouteInfo(OrderedDict):
    def __init__(self, first_hop, cost, timer=0):
        super().__init__(
            [(RouteInfos.FIRST_HOP, first_hop),
                (RouteInfos.COST, cost),
                (RouteInfos.TIMER, timer)]
        )

    def __str__(self):
        try:
            return "{" + RouteInfos.FIRST_HOP + ": " + str(self[RouteInfos.FIRST_HOP]) + ", " + \
                   RouteInfos.COST + ": " + str(self[RouteInfos.COST]) + ", " + \
                   RouteInfos.TIMER + ": " + str(self[RouteInfos.TIMER]) + "}"
        except KeyError:
            return repr(self)

    def copy(self):
        return RouteInfo(self[RouteInfos.FIRST_HOP], self[RouteInfos.COST], self[RouteInfos.TIMER])


def main():
    args = sys.argv
    if len(args) < 2:
        print("Missing config filename!")
        return

    config_filename = args[1]
    with open(config_filename) as config_file:
        config_lines = config_file.readlines()

    router = Router(config_lines)
    router.config_dir = "/".join(config_filename.split("/")[:-1])

    options = []
    if len(args) >= 3:
        [options.append(args[i]) for i in range(2, len(args))]

    router.load = "load" in options or "l" in options
    router.verbose = "verbose" in options or "v" in options
    router.bind_input_sockets()
    router.initialise_routing_table()

    router.run()


if __name__ == "__main__":
    main()

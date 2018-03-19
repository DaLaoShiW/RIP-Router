import sys


class Router:
    MIN_PORT = 1024
    MAX_PORT = 64000

    MIN_ROUTER_ID = 1
    MAX_ROUTER_ID = 64000

    INFINITY = 16

    TIMEOUT_UPDATE_RATIO = 6

    def __init__(self, config_lines):
        self.id = None
        self.input_ports = []
        self.outputs = {}
        self.update_period = None
        self.timeout_length = None

        config_functions = {
            'router-id': self.process_router_id,
            'input-ports': self.process_input_ports,
            'outputs': self.process_outputs,
            'update-period': self.process_update_period
        }

        for line in config_lines:
            if line[0] == '#':
                # Ignore any lines that are comments
                continue

            parts = line.split(' ')

            if parts[0] not in config_functions.keys():
                print("Unknown config setting: " + parts[0])
                continue

            config_functions[parts[0]](line)

        print("Configuration loaded!")
        print("-" * 40)

        config_values = {
            'Router ID': self.id,
            'Input Ports': self.input_ports,
            'Output Routers': self.outputs,
            'Update Period': self.update_period,
            'Timeout Length': self.timeout_length
        }

        print(*[title + ": " + str(value) for title, value in config_values.items()], sep="\n")

    def process_router_id(self, line):
        """ Set this router's ID """
        parts = line.split(' ')
        self.id = self.validate_router_id(parts[1])

    def process_input_ports(self, line):
        """ Set the input ports for this router """
        parts = line.split(' ')
        for port in parts[1:]:
            if port[-1] == ',':
                port = port[:-1]

            self.input_ports.append(self.validate_port(port))

    def process_outputs(self, line):
        """ Set and format neighbor routers (outputs) and their metrics """
        parts = line.split(' ')
        for output in parts[1:]:
            if output[-1] == ',':
                output = output[:-1]

            output_parts = output.split('-')

            output_port = self.validate_port(output_parts[0])
            output_router_metric = self.validate_metric(output_parts[1])
            output_router_id = self.validate_router_id(output_parts[2])
            self.outputs[output_router_id] = (output_port, output_router_metric)

    def process_update_period(self, line):
        """ Set periodic update time and timeout duration from config """
        parts = line.split(' ')
        self.update_period = int(parts[1])
        self.timeout_length = self.TIMEOUT_UPDATE_RATIO * self.update_period

    def validate_metric(self, metric):
        """ Validates a router metric to be in the correct range """
        metric = int(metric)

        if metric < 0 or metric > self.INFINITY:
            raise Exception("Invalid metric '" + str(metric) + "', not in range 0-16")

        return metric

    def validate_router_id(self, router_id):
        """ Validates router-ids to be in the correct range """
        router_id = int(router_id)

        if router_id < self.MIN_ROUTER_ID or router_id > self.MAX_ROUTER_ID:
            raise Exception("Invalid router-id '" + str(self.id) + "', not in range 1-64000")

        return router_id

    def validate_port(self, port):
        """ Validates range of port numbers """
        port = int(port)

        if port < self.MIN_PORT or port > self.MAX_PORT:
            raise Exception(
                "Invalid input port '" + str(port) + "', not in range " + str(self.MIN_PORT) + "-" + str(self.MAX_PORT))

        return port

    def run(self):
        """ Checks and processes incoming packets (select) and timing events."""
        pass  # TODO


def main():
    args = sys.argv

    if len(args) < 2:
        print("Missing config filename!")
        return

    config_filename = args[1]
    config_file = open(config_filename, 'r')

    config_lines = config_file.readlines()

    router = Router(config_lines)

    while True:
        router.run()


main()

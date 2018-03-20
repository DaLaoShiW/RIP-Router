import os


class Loader:
    MIN_PORT = 1024
    MAX_PORT = 64000

    MIN_ROUTER_ID = 1
    MAX_ROUTER_ID = 64000

    INFINITY = 16

    TIMEOUT_UPDATE_RATIO = 6

    def __init__(self, config_lines, router):
        self.config_lines = config_lines
        # Map configuration settings to processing functions
        self.config_functions = {
            'router-id': self.process_router_id,
            'input-ports': self.process_input_ports,
            'outputs': self.process_outputs,
            'update-period': self.process_update_period
        }
        self.router = router

    def load(self):
        """ Load the configuration and set the router's variables """

        for line in self.config_lines:
            # Ignore any lines that are comments
            if line[0] != '#':
                parts = line.split(' ')
                if parts[0] not in self.config_functions:
                    print("ERROR: Unknown config setting: " + parts[0])
                else:
                    # Process the line using the relevant function
                    self.config_functions[parts[0]](line)

        if all([self.router.id, self.router.input_ports, self.router.outputs,
                self.router.update_period, self.router.timeout_length]):
            print("Configuration loaded!")
            print("-" * 40)
        else:
            print("ERROR: Incomplete configuration")
            print("-" * 40)

        config_values = [
            ('Router ID', self.router.id),
            ('Input Ports', self.router.input_ports),
            ('Output Routers', self.router.outputs),
            ('Update Period', self.router.update_period),
            ('Timeout Length', self.router.timeout_length)
        ]
        print(*[title + ": " + str(value) for title, value in config_values], sep=os.linesep)

    def process_router_id(self, line):
        """ Set the router's ID """
        parts = line.split(' ')
        self.router.id = self.validate_router_id(parts[1])

    def process_input_ports(self, line):
        """ Set the input ports for the router """
        parts = line.split(' ')
        for port in parts[1:]:
            if port[-1] == ',':
                port = port[:-1]
                self.router.input_ports.append(self.validate_port(port))

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
            self.router.outputs[output_router_id] = (output_port, output_router_metric)

    def process_update_period(self, line):
        """ Set periodic update time and timeout duration for the router """
        parts = line.split(' ')
        self.router.update_period = int(parts[1])
        self.router.timeout_length = self.TIMEOUT_UPDATE_RATIO * self.router.update_period

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
            raise Exception("Invalid router-id '" + str(self.router.id) + "', not in range 1-64000")

        return router_id

    def validate_port(self, port):
        """ Validates range of port numbers """
        port = int(port)

        if port < self.MIN_PORT or port > self.MAX_PORT:
            raise Exception(
                "Invalid input port '" + str(port) + "', not in range " + str(self.MIN_PORT) + "-" + str(self.MAX_PORT))

        return port

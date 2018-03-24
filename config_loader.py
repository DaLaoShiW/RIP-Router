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
        self.line_number = 1
        # Map configuration settings to processing functions
        self.config_functions = {
            "router-id": self.process_router_id,
            "input-ports": self.process_input_ports,
            "outputs": self.process_outputs,
            "update-period": self.process_update_period
        }
        self.router = router

    def load(self):
        """ Load the configuration and set the router's variables """
        for line in self.config_lines:
            line = " ".join(line.split())  # Remove all leading, trailing, and consecutive whitespace
            # Ignore any lines that are comments
            if line[0] != "#":
                parts = line.split(" ")
                if parts[0] not in self.config_functions:
                    print("Unknown config setting: " + parts[0])
                else:
                    # Process the line using the relevant function
                    try:
                        self.config_functions[parts[0]](line)
                    except ValueError as value_error:
                        print("Error in configuration file on line", self.line_number)
                        print(value_error)
                        print()
                        exit(11)
            self.line_number += 1

        if all([self.router.id, self.router.input_ports, self.router.outputs,
                self.router.update_period, self.router.timeout_length]):
            print("Configuration loaded!")
            self.print_config_values()
        else:
            print("Error in configuration file")
            print("Incomplete configuration")
            self.print_config_values()
            print()
            exit(1)

    def print_config_values(self):
        """ Print the router's values, obtained from the config file """
        print("-" * 40)
        config_values = [
            ("Router ID", self.router.id),
            ("Input Ports", self.router.input_ports),
            ("Output Routers", self.router.outputs),
            ("Update Period", self.router.update_period),
            ("Timeout Length", self.router.timeout_length)
        ]
        print(*[title + ": " + str(value) for title, value in config_values], sep=os.linesep)
        print("-" * 40)

    def process_router_id(self, line):
        """ Set the router's ID """
        parts = line.split(" ")
        if len(parts) > 2:
            raise ValueError("Invalid router-id: '" + " ".join(parts[1:]) + "', too many arguments")
        elif len(parts) < 2:
            raise ValueError("No router-id given")
        self.router.id = self.validate_router_id(parts[1].strip())

    def process_input_ports(self, line):
        """ Set the input-ports for the router """
        parts = " ".join(line.split(" ")[1:]).split(",")  # Remove 'input-ports' and split on commas.
        if not any(parts):
            raise ValueError("No input-ports given")
        for port in parts:
            port = port.strip()
            self.router.input_ports.append(self.validate_port(port))

    def process_outputs(self, line):
        """ Set and format neighbor routers (outputs) and their costs/router-ids """
        parts = " ".join(line.split(" ")[1:]).split(",")  # Remove 'outputs' and split on commas.
        if not any(parts):
            raise ValueError("No outputs given")
        for output in parts:
            output = output.strip()
            output_parts = output.split("/")
            if len(output_parts) != 3:
                raise ValueError("Invalid output: '" + output + "', usage: port/cost/router-id")
            output_port = self.validate_port(output_parts[0])
            output_router_cost = self.validate_cost(output_parts[1])
            output_router_id = self.validate_router_id(output_parts[2])
            self.router.outputs[output_router_id] = (output_port, output_router_cost)

    def process_update_period(self, line):
        """ Set periodic update time and timeout duration for the router """
        parts = line.split(" ")
        if len(parts) > 2:
            raise ValueError("Invalid update-period: '" + " ".join(parts[1:]) + "', too many arguments")
        elif len(parts) < 2:
            raise ValueError("No update-period given")
        self.router.update_period = self.validate_update_period(parts[1].strip())
        self.router.timeout_length = self.TIMEOUT_UPDATE_RATIO * self.router.update_period

    def validate_router_id(self, router_id):
        """ Validate a router-id """
        router_id = router_id.strip()
        if not all([True if c.isdigit() else False for c in str(router_id)]):
            raise ValueError("Invalid router-id '" + str(router_id) + "', not a positive integer")
        router_id = int(router_id)
        if router_id < self.MIN_ROUTER_ID or router_id > self.MAX_ROUTER_ID:
            raise ValueError(
                "Invalid router-id: '" + str(router_id) + "', not in range {}-{}".format(
                    self.MIN_ROUTER_ID, self.MAX_ROUTER_ID
                )
            )

        return router_id

    def validate_port(self, port):
        """ Validate a port number """
        port = port.strip()
        if not port or not all([True if c.isdigit() else False for c in str(port)]):
            raise ValueError("Invalid port: '" + str(port) + "', not a positive integer")
        port = int(port)
        if port < self.MIN_PORT or port > self.MAX_PORT:
            raise ValueError(
                "Invalid port: '" + str(port) + "', not in range " + str(self.MIN_PORT) + "-" + str(self.MAX_PORT))

        return port

    def validate_cost(self, cost):
        """ Validate a router cost """
        cost = cost.strip()
        if not all([True if c.isdigit() or c == "-" else False for c in str(cost)]):
            raise ValueError("Invalid cost: '" + str(cost) + "', not an integer")
        cost = int(cost)
        if cost < 0 or cost > self.INFINITY:
            raise ValueError(
                "Invalid cost '" + str(cost) + "', not in range {}-{}".format(
                    0, self.INFINITY
                )
            )

        return cost

    @staticmethod
    def validate_update_period(update_period):
        """ Validate a router update_period """
        update_period = update_period.strip()
        if not all([True if c.isdigit() else False for c in str(update_period)]):
            raise ValueError("Invalid update-period: '" + str(update_period) + "', not a positive integer")
        update_period = int(update_period)

        return update_period

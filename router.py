import sys

import config_loader


class Router:
    INFINITY = 16

    def __init__(self, config_lines):
        self.id = None
        self.input_ports = []
        self.outputs = {}
        self.update_period = None
        self.timeout_length = None

        self.config_loader = config_loader.Loader(config_lines, self)
        self.config_loader.load()

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
    config_file.close()

    router = Router(config_lines)

    # while True:
    #     router.run()


main()

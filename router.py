import sys

def main():
    args = sys.argv

    if len(args) < 2:
        print("Missing config filename!")
        return

    config_filename = args[1]
    config_file = open(config_filename, 'r')

    config_lines = config_file.readlines()
    config_functions = {
        'router-id': process_router_id,
        'input-ports': process_input_ports,
        'outputs': process_outputs,
        'timeout-length': process_timeout_length,
        'update-period': process_update_period
    }

    for line in config_lines:
        if line[0] == '#':
            # Ignore any lines that are comments
            continue
        parts = line.split(' ')
        if parts[0] not in config_functions.keys():
            print("Unknown config setting: "+parts[0])
            continue

        print("Processing: "+parts[0])
        config_functions[parts[0]](line)

def process_router_id(line):
    # TODO
    print(line)

def process_input_ports(line):
    # TODO
    print(line)

def process_outputs(line):
    # TODO
    print(line)

def process_timeout_length(line):
    # TODO
    print(line)

def process_update_period(line):
    # TODO
    print(line)



main()
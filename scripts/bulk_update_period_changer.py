import os
import re

example_to_modify = "3"
new_update_period = "10"

confirm = input(
    "Modifying example " + example_to_modify + "'s router update-periods to " + new_update_period +
    ". Enter 'y' to confirm overwrite: "
).strip().lower()
if confirm != "y":
    exit()


example_path = "../configurations/example-" + example_to_modify + "/"
match_regex = re.compile("example-" + example_to_modify + "-config-[0-9]+.txt")
config_file_names = [name for name in os.listdir(example_path) if re.match(match_regex, name)]

for config_file_name in config_file_names:
    with open(example_path + config_file_name, "r+") as config_file:
        lines = config_file.readlines()
        config_file.seek(0)
        for line in lines:
            if line.split(" ")[0] != "update-period":
                config_file.write(line)
            else:
                config_file.write("update-period " + new_update_period)
        config_file.truncate()

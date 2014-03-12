import fnmatch
import os


class Levels:
    INFO = 1 << 0
    WARNING = 1 << 1
    ERROR = 1 << 2
    SUMMARY = 1 << 3
    message = {INFO: 'INFO', WARNING: 'WARNING', ERROR: 'ERROR', SUMMARY: 'SUMMARY'}


# Default level is to print everything
print_level = Levels.INFO | Levels.WARNING | Levels.ERROR


def do_print(mode, level, string, *args):
    global print_level
    if (level & int(print_level) != level):
        return
    final_string = "%-32s: %-8s: " + string
    final_args = (mode, Levels.message[int(level)])
    final_args += args
    print final_string % final_args


def find_file(path, pattern):
    health_data_file = []
    # For all the local files
    for file in os.listdir(path):
        # If the file math the regexp
        if fnmatch.fnmatch(file, pattern):
            # Let's consider this file
            health_data_file.append(path + "/" + file)

    return health_data_file


def get_item(output, item, item1, item2, item3):
    if item[0] == item1 and item[1] == item2 and item[2] == item3:
        output[item3] = item[3]
        return
    return


def dump_item(output, item, item1, item2, item3):
    if item[0] == item1 and item[1] == item2 and item[2] == item3:
        output.add(item[3])
        return
    return


def get_hosts_list(bench_values):
    systems = set()
    for bench in bench_values:
        for line in bench:
            dump_item(systems, line, 'system', 'product', 'serial')

    return systems


# Extract a sub element from the results
def find_sub_element(bench_values, element, hosts=set()):
    systems = []
    for bench in bench_values:
        system = {'serial': ''}
        stuff = []
        for line in bench:
            get_item(system, line, 'system', 'product', 'serial')
            if element in line[0]:
                stuff.append(line)

        if (len(hosts) == 0) or system['serial'] in hosts:
            system[element] = stuff
            systems.append(system)

    return systems

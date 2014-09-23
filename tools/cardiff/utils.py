import fnmatch
import math
import os


class Levels:
    INFO = 1 << 0
    WARNING = 1 << 1
    ERROR = 1 << 2
    SUMMARY = 1 << 3
    DETAIL = 1 << 4
    message = {INFO: 'INFO', WARNING: 'WARNING', ERROR: 'ERROR', SUMMARY: 'SUMMARY', DETAIL: 'DETAIL'}


# Default level is to print everything
print_level = Levels.INFO | Levels.WARNING | Levels.ERROR


def write_gnuplot_file(filename, index, value):
    if not os.path.isfile(filename):
        with open(filename, "a") as myfile:
            if math.isnan(value) is False:
                myfile.write("%d %.2f\n" % (index, value))
    else:
        new_lines = []
        with open(filename, "r") as f:
            lines = (line.rstrip() for line in f)
            found = False
            for line in lines:
                if (int(line.split()[0].strip()) == index):
                    found = True
                    new_lines.append("%s %.2f" % (line.strip(), value))
                else:
                    new_lines.append("%s" % (line.strip()))
            if found is False:
                new_lines.append("%d %.2f" % (index, value))
        with open(filename, "w") as f:
            f.write('\n'.join(new_lines) + '\n')


def do_print(mode, level, string, *args):
    global print_level
    if (level & int(print_level) != level):
        return
    final_string = "%-34s: %-8s: " + string
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


def get_hosts_list(bench_values, unique_id):
    systems = set()
    for bench in bench_values:
        for line in bench:
            dump_item(systems, line, 'system', 'product', unique_id)

    return systems


# Extract a sub element from the results
def find_sub_element(bench_values, unique_id, element, hosts=set()):
    systems = []
    for bench in bench_values:
        system = {unique_id: ''}
        stuff = []
        for line in bench:
            get_item(system, line, 'system', 'product', unique_id)
            if element in line[0]:
                stuff.append(line)

        if (len(hosts) == 0) or system[unique_id] in hosts:
            system[element] = stuff
            systems.append(system)

    return systems

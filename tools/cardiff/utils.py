import fnmatch
import os


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


# Extract a sub element from the results
def find_sub_element(bench_values, element):
    systems = []
    for bench in bench_values:
        system = {'serial': ''}
        stuff = []
        for line in bench:
            get_item(system, line, 'system', 'product', 'serial')
            if element in line[0]:
                stuff.append(line)

        system[element] = stuff
        systems.append(system)
    return systems

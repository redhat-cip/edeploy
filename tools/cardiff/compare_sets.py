import collections


class Machine:
    def __init__(self, name, value):
        self.name = name
        self.value = value


def compare(sets):
    machines = []
    for current_set in sets:
        my_string = repr(sets[current_set])
        machines.append(Machine(current_set, my_string))

    to_be_sorted = collections.defaultdict(list)
    for machine in machines:
        key = machine.value
        value = machine.name
        to_be_sorted[key].append(value)

    return dict(to_be_sorted)


def print_groups(result, title):
    print "##### %s #####" % title
    for element in result:
        group = result[element]
        print "%d identical systems :" % (len(group))
        print group
        for stuff in sorted(eval(element)):
            print stuff
        print
    print "#####"*2 + "#"*len(title)

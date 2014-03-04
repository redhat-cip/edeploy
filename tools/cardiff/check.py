import re
import compare_sets


def search_item(systems, item, regexp, exclude_list=[]):
    sets = {}
    for system in systems:
        sets[system['serial']] = set()
        current_set = sets[system['serial']]
        for stuff in system[item]:
            m = re.match(regexp, stuff[1])
            if m:
                shall_be_excluded = False
                for exclude in exclude_list:
                    if exclude in stuff[2]:
                        shall_be_excluded = True
                if shall_be_excluded is False:
                    current_set.add(stuff)
    return sets


def physical_disks(systems):
    sets = search_item(systems, "disk", "(\d+)I:(\d+):(\d+)")
    compare_sets.print_groups(compare_sets.compare(sets), "Physical Disks (HP Controllers)")


def logical_disks(systems):
    sets = search_item(systems, "disk", "sd(\S+)", ['simultaneous', 'standalone'])
    compare_sets.print_groups(compare_sets.compare(sets), "Logical Disks")


def systems(systems):
    sets = search_item(systems, "system", "(.*)", ['serial'])
    compare_sets.print_groups(compare_sets.compare(sets), "System")


def firmware(systems):
    sets = search_item(systems, "firmware", "(.*)")
    compare_sets.print_groups(compare_sets.compare(sets), "Firmware")


def memory_timing(systems):
    sets = search_item(systems, "memory", "DDR(.*)")
    compare_sets.print_groups(compare_sets.compare(sets), "Memory Timing(RAM)")


def memory_banks(systems):
    sets = search_item(systems, "memory", "bank(.*)")
    compare_sets.print_groups(compare_sets.compare(sets), "Memory Banks(RAM)")

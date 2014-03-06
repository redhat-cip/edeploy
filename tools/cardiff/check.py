import re
import compare_sets
from pandas import *


def search_item(systems, item, regexp, exclude_list=[], include_list=[]):
    sets = {}
    for system in systems:
        sets[system['serial']] = set()
        current_set = sets[system['serial']]
        for stuff in system[item]:
            m = re.match(regexp, stuff[1])
            if m:
                # If we have an include_list, only those shall be used
                # So everything is exclude by default
                if len(include_list) > 0:
                    shall_be_excluded = True
                else:
                    shall_be_excluded = False

                for include in include_list:
                    if include in stuff[2]:
                        # If something is part of the include list
                        # It is no more excluded
                        shall_be_excluded = False

                for exclude in exclude_list:
                    if exclude in stuff[2]:
                        shall_be_excluded = True
                if shall_be_excluded is False:
                    current_set.add(stuff)
    return sets


def physical_disks(systems):
    sets = search_item(systems, "disk", "(\d+)I:(\d+):(\d+)")
    groups = compare_sets.compare(sets)
    compare_sets.print_groups(groups, "Physical Disks (HP Controllers)")
    return groups


def logical_disks(systems):
    sets = search_item(systems, "disk", "sd(\S+)", ['simultaneous', 'standalone'])
    groups = compare_sets.compare(sets)
    compare_sets.print_groups(groups, "Logical Disks")
    return groups


def compute_variance_percentage(item, df):
    # If we have a single item
    # checking the variance is useless
    if df[item].count() == 1:
        return 0
    return (df[item].std() / df[item].mean() * 100)


def logical_disks_perf(systems, group_number):
    print "Group %d : Checking logical disks perf" % group_number
    sets = search_item(systems, "disk", "sd(\S+)", [], ['simultaneous', 'standalone'])
    modes = ['standalone_randwrite_4k_IOps', 'standalone_randread_4k_IOps', 'standalone_read_1M_IOps', 'standalone_write_1M_IOps',  'simultaneous_randwrite_4k_IOps', 'simultaneous_randread_4k_IOps', 'simultaneous_read_1M_IOps', 'simultaneous_write_1M_IOps']
    for mode in modes:
        results = {}
        for system in sets:
            disks = []
            series = []
            for perf in sets[system]:
                if (perf[2] == mode):
                    if not perf[1] in disks:
                        disks.append(perf[1])
                    series.append(int(perf[3]))
            results[system] = Series(series, index=disks)

        df = DataFrame(results)
        for disk in df.transpose().columns:
            # How much the variance could be far from the average (in %)
            tolerance = 10
            # In random mode, the variance could be higher as
            # we cannot insure the distribution pattern was similar
            if "rand" in mode:
                tolerance = 15

            variance_group = df.transpose()[disk].std()
            mean_group = df.transpose()[disk].mean()
            min_group = mean_group - 2*variance_group
            max_group = mean_group + 2*variance_group

            print "%-32s: INFO    : %s : Group performance : min=%7.2f, mean=%7.2f, max=%7.2f, stddev=%7.2f" % (mode, disk, min_group, mean_group, max_group, variance_group)

            variance_tolerance = compute_variance_percentage(disk, df.transpose())
            if (variance_tolerance > tolerance):
                print "%-32s: ERROR   : %s : Group's variance is too important : %7.2f%% of %7.2f whereas limit is set to %3.2f%%" % (mode, disk, variance_tolerance, mean_group, tolerance)
                print "%-32s: ERROR   : %s : Group performance : UNSTABLE" % (mode, disk)
            else:
                curious_performance = False
                for host in df.columns:
                    mean_host = df[host][disk].mean()
                    #print df[host][disk](df.transpose()[disk])
                    if (mean_host > max_group):
                        curious_performance = True
                        print "%-32s: WARNING : %s : %s : Curious overperformance  %.2f : min_group = %.2f, mean_group = %.2f max_group = %.2f" % (mode, disk, host, mean_host, min_group, mean_group, max_group)
                    elif (mean_host < min_group):
                        curious_performance = True
                        print "%-32s: WARNING : %s : %s : Curious underperformance %.2f : min_group = %.2f, mean_group = %.2f max_group = %.2f" % (mode, disk, host, mean_host, min_group, mean_group, max_group)

                if curious_performance is False:
                    print "%-32s: INFO    : %s : Group performance : CONSISTENT" % (mode, disk)
                else:
                    print "%-32s: WARNING : %s : Group performance : SUSPICIOUS" % (mode, disk)
    print


def systems(systems):
    sets = search_item(systems, "system", "(.*)", ['serial'])
    groups = compare_sets.compare(sets)
    compare_sets.print_groups(groups, "System")
    return groups


def firmware(systems):
    sets = search_item(systems, "firmware", "(.*)")
    groups = compare_sets.compare(sets)
    compare_sets.print_groups(groups, "Firmware")
    return groups


def memory_timing(systems):
    sets = search_item(systems, "memory", "DDR(.*)")
    groups = compare_sets.compare(sets)
    compare_sets.print_groups(groups, "Memory Timing(RAM)")
    return groups


def memory_banks(systems):
    sets = search_item(systems, "memory", "bank(.*)")
    groups = compare_sets.compare(sets)
    compare_sets.print_groups(groups, "Memory Banks(RAM)")
    return groups


def network_interfaces(systems):
    sets = search_item(systems, "network", "(.*)", ['serial', 'ipv4'])
    groups = compare_sets.compare(sets)
    compare_sets.print_groups(groups, "Network Interfaces")
    return groups


def cpu(systems):
    sets = search_item(systems, "cpu", "(.*)", ['bogomips', 'loops_per_sec', 'bandwidth', 'cache_size'])
    groups = compare_sets.compare(sets)
    compare_sets.print_groups(groups, "Processors")
    return groups

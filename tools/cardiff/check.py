import re
import compare_sets
import utils
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
            tolerance_max = 10
            tolerance_min = 2
            # In random mode, the variance could be higher as
            # we cannot insure the distribution pattern was similar
            if "rand" in mode:
                tolerance_min = 5
                tolerance_max = 15

            print_perf(tolerance_min, tolerance_max, df.transpose()[disk], df, mode, disk)
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


def print_perf(tolerance_min, tolerance_max, item, df, mode, title):
    # Tolerance_min represents the min where variance shall be considered (in %)
    # Tolerance_max represents the maximum that variance represent regarding the average (in %)

    variance_group = item.std()
    mean_group = item.mean()
    min_group = mean_group - 2*variance_group
    max_group = mean_group + 2*variance_group

    utils.do_print(mode, utils.Levels.INFO, "%-12s : Group performance : min=%8.2f, mean=%8.2f, max=%8.2f, stddev=%8.2f", title, item.min(), mean_group, item.max(), variance_group)

    variance_tolerance = compute_variance_percentage(title, df.transpose())
    if (variance_tolerance > tolerance_max):
        utils.do_print(mode, utils.Levels.ERROR, "%-12s : Group's variance is too important : %7.2f%% of %7.2f whereas limit is set to %3.2f%%", title, variance_tolerance, mean_group, tolerance_max)
        utils.do_print(mode, utils.Levels.ERROR, "%-12s : Group performance : UNSTABLE", title)
    else:
        curious_performance = False
        for host in df.columns:
            if (("loops_per_sec") in mode) or ("bogomips" in mode):
                mean_host = df[host][title].mean()
            else:
                mean_host = df[host].mean()
            # If the variance is very low, don't try to find the black sheep
            if (variance_tolerance > tolerance_min):
                if (mean_host > max_group):
                    curious_performance = True
                    utils.do_print(mode, utils.Levels.WARNING, "%-12s : %s : Curious overperformance  %7.2f : min_allow_group = %.2f, mean_group = %.2f max_allow_group = %.2f", title, host, mean_host, min_group, mean_group, max_group)
                elif (mean_host < min_group):
                    curious_performance = True
                    utils.do_print(mode, utils.Levels.WARNING, "%-12s : %s : Curious underperformance %7.2f : min_allow_group = %.2f, mean_group = %.2f max_allow_group = %.2f", title, host, mean_host, min_group, mean_group, max_group)

        unit = " "
        if "Effi." in title:
            unit = "%"
        if curious_performance is False:
            utils.do_print(mode, utils.Levels.INFO, "%-12s : Group performance = %7.2f %s : CONSISTENT", title, mean_group, unit)
        else:
            utils.do_print(mode, utils.Levels.WARNING, "%-12s : Group performance = %7.2f %s : SUSPICIOUS", title, mean_group, unit)


def cpu_perf(systems, group_number):
    print "Group %d : Checking CPU  perf" % group_number
    modes = ['bogomips', 'loops_per_sec']
    sets = search_item(systems, "cpu", "(.*)", [], modes)
    global_perf = dict()
    for mode in modes:
        results = {}
        for system in sets:
            cpu = []
            series = []
            for perf in sets[system]:
                if (perf[2] == mode):
                    # We shall split individual cpu benchmarking from the global one
                    if ("_" in perf[1]):
                        if (not perf[1] in cpu):
                            cpu.append(perf[1])
                        series.append(float(perf[3]))
                    elif "loops_per_sec" in mode:
                        global_perf[system] = float(perf[3])
            results[system] = Series(series, index=cpu)

        df = DataFrame(results)
        for cpu in df.transpose().columns:
            print_perf(1, 7, df.transpose()[cpu], df, mode, cpu)

        if mode == "loops_per_sec":
            efficiency = {}
            mode_text = 'CPU Effi.'

            for system in sets:
                host_efficiency_full_load = []
                host_perf = df[system].sum()
                host_efficiency_full_load.append(global_perf[system] / host_perf * 100)
                efficiency[system] = Series(host_efficiency_full_load, index=[mode_text])

            cpu_eff = DataFrame(efficiency)
            print_perf(1, 2, cpu_eff.transpose()[mode_text], cpu_eff, mode, mode_text)

    print


def memory_perf(systems, group_number):
    print "Group %d : Checking CPU  perf" % group_number
    modes = ['1K', '4K', '1M', '16M', '128M', '1G', '2G']
    sets = search_item(systems, "cpu", "(.*)", [], modes)
    for mode in modes:
        real_mode = "Memory benchmark %s" % mode
        results = {}
        threaded_perf = dict()
        forked_perf = dict()
        for system in sets:
            memory = []
            series = []
            threaded_perf[system] = 0
            forked_perf[system] = 0
            for perf in sets[system]:
                if (mode in perf[2]):
                    # We shall split individual cpu benchmarking from the global one
                    if ("logical_" in perf[1]) and (("bandwidth_%s" % mode) in perf[2]):
                        if (not perf[1] in memory):
                            memory.append(perf[1])
                        series.append(float(perf[3]))
                    elif ("threaded_bandwidth_%s" % mode) in perf[2]:
                        threaded_perf[system] = float(perf[3])
                    elif ("forked_bandwidth_%s" % mode) in perf[2]:
                        forked_perf[system] = float(perf[3])
            results[system] = Series(series, index=memory)

        df = DataFrame(results)
        for memory in df.transpose().columns:
            print_perf(1, 7, df.transpose()[memory], df, real_mode, memory)

        for bench_type in ["threaded", "forked"]:
            efficiency = {}
            have_forked_or_threaded = False
            if ("threaded" in bench_type):
                mode_text = "Thread effi."
            else:
                mode_text = "Forked Effi."
            for system in sets:
                host_efficiency_full_load = []
                host_perf = df[system].sum()
                if (host_perf > 0) and (threaded_perf[system] > 0) and (forked_perf[system] > 0):
                    have_forked_or_threaded = True
                    if ("threaded" in bench_type):
                        host_efficiency_full_load.append(threaded_perf[system] / host_perf * 100)
                    else:
                        host_efficiency_full_load.append(forked_perf[system] / host_perf * 100)

                    efficiency[system] = Series(host_efficiency_full_load, index=[mode_text])

            memory_eff = DataFrame(efficiency)
            if have_forked_or_threaded is True:
                print_perf(2, 10, memory_eff.transpose()[mode_text], memory_eff, real_mode, mode_text)
            else:
                utils.do_print(real_mode, utils.Levels.WARNING, "%-12s : Benchmark not run on this group", mode_text)
        print

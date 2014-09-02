#!/usr/bin/env python
#
#  Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#  Author: Erwan Velu  <erwan@enovance.com>
#
#  The license below covers all files distributed with fio unless otherwise
#  noted in the file itself.
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 2 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import sys
import getopt
import check
import utils
import compare_sets


def print_help():
    print 'cardiff -hp '
    print
    print '-h --help                           : Print this help'
    print '-p <pattern> or --pattern <pattern> : A pattern in regexp to select input files'
    print '-l <level>   or --log-level <level> : Show only the log levels selected'
    print '                                    :   level is a comma separated list of the following levels'
    print '                                    :   INFO, ERROR, WARNING, SUMMARY, DETAIL'
    print '                                    :   SUMMARY is the default view'
    print '-g <group> or --group <group>       : Select the target group for DETAIL level (supports regexp)'
    print '-c <cat>   or --category <cat>      : Select the target category for DETAIL level (supports regexp)'
    print '-i <item>  or --item <item>         : Select the item for select group with DETAIL level (supports regexp)'
    print '-I <list>  or --ignore <list>       : Disable the grouping segregration on the coma separated list of components :'
    print '                                        cpu, disk, firmware, memory, network, system '
    print
    print 'Examples:'
    print "cardiff.py -p 'sample/*.hw' -l DETAIL -g '1' -c 'loops_per_sec' -i 'logical_1.*'"
    print "cardiff.py -p 'sample/*.hw' -l DETAIL -g '1' -c 'standalone_rand.*_4k_IOps' -i 'sd.*'"
    print "cardiff.py -p 'sample/*.hw' -l DETAIL -g '0' -c '1G' -i '.*'"
    print "cardiff.py -p '*hw' -I disk,cpu"


def compare_disks(bench_values, systems_groups):
    systems = utils.find_sub_element(bench_values, 'disk')
    groups = check.physical_disks(systems)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))
    groups = check.logical_disks(systems)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_systems(bench_values, systems_groups):
    systems = utils.find_sub_element(bench_values, 'system')
    groups = check.systems(systems)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_firmware(bench_values, systems_groups):
    systems = utils.find_sub_element(bench_values, 'firmware')
    groups = check.firmware(systems)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_memory(bench_values, systems_groups):
    systems = utils.find_sub_element(bench_values, 'memory')
    check.memory_timing(systems)
    groups = check.memory_banks(systems)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_network(bench_values, systems_groups):
    systems = utils.find_sub_element(bench_values, 'network')
    groups = check.network_interfaces(systems)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_cpu(bench_values, systems_groups):
    systems = utils.find_sub_element(bench_values, 'cpu')
    groups = check.cpu(systems)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def group_systems(bench_values, systems_groups, ignore_list):
    if "disk" not in ignore_list:
        compare_disks(bench_values, systems_groups)

    if "system" not in ignore_list:
        compare_systems(bench_values, systems_groups)

    if "firmware" not in ignore_list:
        compare_firmware(bench_values, systems_groups)

    if "memory" not in ignore_list:
        compare_memory(bench_values, systems_groups)

    if "network" not in ignore_list:
        compare_network(bench_values, systems_groups)

    if "cpu" not in ignore_list:
        compare_cpu(bench_values, systems_groups)


def compare_performance(bench_values, systems_groups, detail):
    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, 'disk', group)
        check.logical_disks_perf(systems, systems_groups.index(group), detail)

    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, 'cpu', group)
        check.cpu_perf(systems, systems_groups.index(group), detail)

    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, 'cpu', group)
        check.memory_perf(systems, systems_groups.index(group), detail)


def main(argv):
    pattern = ''
    ignore_list = ''
    detail = {'category': '', 'group': '', 'item': ''}
    try:
        opts, args = getopt.getopt(argv[1:], "hp:l:g:c:i:I:", ['pattern', 'log-level', 'group', 'category', 'item', "ignore"])
    except getopt.GetoptError:
        print "Error: One of the options passed to the cmdline was not supported"
        print "Please fix your command line or read the help (-h option)"
        sys.exit(2)

    utils.print_level = int(utils.Levels.SUMMARY)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit(0)
        elif opt in ("-p", "--pattern"):
            pattern = arg
            pattern = pattern.replace('\\', '')
        elif opt in ("-l", "--log-level"):
            if "list" in arg:
                print_help()
                sys.exit(2)
            utils.print_level = 0
            if utils.Levels.message[utils.Levels.INFO] in arg:
                utils.print_level |= int(utils.Levels.INFO)
            if utils.Levels.message[utils.Levels.WARNING] in arg:
                utils.print_level |= int(utils.Levels.WARNING)
            if utils.Levels.message[utils.Levels.ERROR] in arg:
                utils.print_level |= int(utils.Levels.ERROR)
            if utils.Levels.message[utils.Levels.SUMMARY] in arg:
                utils.print_level |= int(utils.Levels.SUMMARY)
            if utils.Levels.message[utils.Levels.DETAIL] in arg:
                utils.print_level |= int(utils.Levels.DETAIL)
            if utils.print_level == 0:
                print "Error: The log level specified is not part of the supported list !"
                print "Please check the usage of this tool and retry."
                sys.exit(2)
        elif opt in ("-g", "--group"):
            detail['group'] = arg
        elif opt in ("-c", "--category"):
            detail['category'] = arg
        elif opt in ("-i", "--item"):
            detail['item'] = arg
        elif opt in ("-I", "--ignore"):
            ignore_list = arg

    if ((utils.print_level & utils.Levels.DETAIL) == utils.Levels.DETAIL):
        if (len(detail['group']) == 0) or (len(detail['category']) == 0) or (len(detail['item']) == 0):
            print "Error: The DETAIL output requires group, category & item options to be set"
            sys.exit(2)

    if not pattern:
        print "Error: Pattern option is mandatory"
        print_help()
        sys.exit(2)

    # Extracting regex and path
    path = os.path.dirname(pattern)
    if not path:
        path = "."
    else:
        pattern = os.path.basename(pattern)

    if not os.path.isdir(path):
        print "Error: the path %s doesn't exists !" % path
        sys.exit(2)

    health_data_file = utils.find_file(path, pattern)
    if len(health_data_file) == 0:
        print "No log file found with pattern %s!" % pattern
        sys.exit(1)
    else:
        print "%d files Selected with pattern '%s'" % (len(health_data_file), pattern)

    # Extract data from the hw files
    bench_values = []
    for health in health_data_file:
        bench_values.append(eval(open(health).read()))

    # Extracting the host list from the data to get
    # the initial list of hosts. We have here a single group with all the servers
    systems_groups = []
    systems_groups.append(utils.get_hosts_list(bench_values))

    # Let's create groups of similar servers
    group_systems(bench_values, systems_groups, ignore_list)
    compare_sets.print_systems_groups(systems_groups)

    # It's time to compare performance in each group
    compare_performance(bench_values, systems_groups, detail)

# Main
if __name__ == "__main__":
    sys.exit(main(sys.argv))

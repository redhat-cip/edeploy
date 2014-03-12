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
    print '-l <level> or --log-level <level>   : Show only the log levels selected'
    print '                                    :   level is a comma separated list of the following levels'
    print '                                    :   INFO, ERROR, WARNING, SUMMARY'


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


def group_systems(bench_values, systems_groups):
    compare_disks(bench_values, systems_groups)
    compare_systems(bench_values, systems_groups)
    compare_firmware(bench_values, systems_groups)
    compare_memory(bench_values, systems_groups)
    compare_network(bench_values, systems_groups)
    compare_cpu(bench_values, systems_groups)


def compare_performance(bench_values, systems_groups):
    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, 'disk', group)
        check.logical_disks_perf(systems, systems_groups.index(group))

    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, 'cpu', group)
        check.cpu_perf(systems, systems_groups.index(group))

    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, 'cpu', group)
        check.memory_perf(systems, systems_groups.index(group))


def main(argv):
    pattern = ''
    try:
        opts, args = getopt.getopt(argv[1:], "hp:l:", ['pattern', 'log-level'])
    except getopt.GetoptError:
        print "Error: One of the options passed to the cmdline was not supported"
        print "Please fix your command line or read the help (-h option)"
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-p", "--pattern"):
            pattern = arg
            pattern = pattern.replace('\\', '')
        if opt in ("-l", "--log-level"):
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
            if utils.print_level == 0:
                print "Error: The log level specified is not part of the supported list !"
                print "Please check the usage of this tool and retry."
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
    group_systems(bench_values, systems_groups)
    compare_sets.print_systems_groups(systems_groups)

    # It's time to compare performance in each group
    compare_performance(bench_values, systems_groups)

#Main
if __name__ == "__main__":
    sys.exit(main(sys.argv))

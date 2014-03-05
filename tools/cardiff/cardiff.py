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


def main(argv):
    pattern = ''
    try:
        opts, args = getopt.getopt(argv[1:], "hp:", ['pattern'])
    except getopt.GetoptError:
        print "Error: One of the options passed to the cmdline was not supported"
        print "Please fix your command line or read the help (-h option)"
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-p", "--pattern"):
            pattern = arg
            pattern = pattern.replace('\\', '')

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

    bench_values = []
    for health in health_data_file:
        bench_values.append(eval(open(health).read()))

    systems_groups = []
    systems_groups.append(utils.get_hosts_list(bench_values))
    compare_disks(bench_values, systems_groups)
    compare_systems(bench_values, systems_groups)
    compare_firmware(bench_values, systems_groups)
    compare_memory(bench_values, systems_groups)
    compare_network(bench_values, systems_groups)
    compare_cpu(bench_values, systems_groups)
    compare_sets.print_systems_groups(systems_groups)

#Main
if __name__ == "__main__":
    sys.exit(main(sys.argv))

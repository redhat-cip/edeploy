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
import fnmatch
import sys
import getopt
import check


def find_file(path, pattern):
    health_data_file = []
    # For all the local files
    for file in os.listdir(path):
        # If the file math the regexp
        if fnmatch.fnmatch(file, pattern):
            # Let's consider this file
            health_data_file.append(path + "/" + file)

    return health_data_file


def print_help():
    print 'cardiff -hp '
    print
    print '-h --help                           : Print this help'
    print '-p <pattern> or --pattern <pattern> : A pattern in regexp to select input files'


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


def compare_disks(bench_values):
    systems = find_sub_element(bench_values, 'disk')
    check.physical_disks(systems)
    check.logical_disks(systems)

def compare_systems(bench_values):
    systems = find_sub_element(bench_values, 'system')
    check.systems(systems)

def compare_firmware(bench_values):
    systems = find_sub_element(bench_values, 'firmware')
    check.firmware(systems)

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

    health_data_file = find_file(path, pattern)
    if len(health_data_file) == 0:
        print "No log file found with pattern %s!" % pattern
        sys.exit(1)
    else:
        print "%d files Selected with pattern '%s'" % (len(health_data_file), pattern)

    bench_values = []
    for health in health_data_file:
        bench_values.append(eval(open(health).read()))

    compare_disks(bench_values)
    compare_systems(bench_values)
    compare_firmware(bench_values)

#Main
if __name__ == "__main__":
    sys.exit(main(sys.argv))

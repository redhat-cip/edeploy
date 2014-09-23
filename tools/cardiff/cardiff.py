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
import math
import shutil
import numpy


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
    print '-r <dir>   or --rampup <dir>        : Perform the rampup analysis on directory containing results from dahc'
    print '                                        In such mode, no need to provide a pattern'
    print
    print 'Examples:'
    print "cardiff.py -p 'sample/*.hw' -l DETAIL -g '1' -c 'loops_per_sec' -i 'logical_1.*'"
    print "cardiff.py -p 'sample/*.hw' -l DETAIL -g '1' -c 'standalone_rand.*_4k_IOps' -i 'sd.*'"
    print "cardiff.py -p 'sample/*.hw' -l DETAIL -g '0' -c '1G' -i '.*'"
    print "cardiff.py -p '*hw' -I disk,cpu"
    print "cardiff.py -r '/var/lib/edeploy/health/dahc/cpu_load/2014_09_15-12h17'"


def compare_disks(bench_values, unique_id, systems_groups):
    systems = utils.find_sub_element(bench_values, unique_id, 'disk')
    groups = check.physical_disks(systems, unique_id)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))
    groups = check.logical_disks(systems, unique_id)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_systems(bench_values, unique_id, systems_groups):
    systems = utils.find_sub_element(bench_values, unique_id, 'system')
    groups = check.systems(systems, unique_id)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_firmware(bench_values, unique_id, systems_groups):
    systems = utils.find_sub_element(bench_values, unique_id, 'firmware')
    groups = check.firmware(systems, unique_id)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_memory(bench_values, unique_id, systems_groups):
    systems = utils.find_sub_element(bench_values, unique_id, 'memory')
    check.memory_timing(systems, unique_id)
    groups = check.memory_banks(systems, unique_id)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_network(bench_values, unique_id, systems_groups):
    systems = utils.find_sub_element(bench_values, unique_id, 'network')
    groups = check.network_interfaces(systems, unique_id)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def compare_cpu(bench_values, unique_id, systems_groups):
    systems = utils.find_sub_element(bench_values, unique_id, 'cpu')
    groups = check.cpu(systems, unique_id)
    compare_sets.compute_similar_hosts_list(systems_groups, compare_sets.get_hosts_list_from_result(groups))


def group_systems(bench_values, unique_id, systems_groups, ignore_list):
    if "disk" not in ignore_list:
        compare_disks(bench_values, unique_id, systems_groups)

    if "system" not in ignore_list:
        compare_systems(bench_values, unique_id, systems_groups)

    if "firmware" not in ignore_list:
        compare_firmware(bench_values, unique_id, systems_groups)

    if "memory" not in ignore_list:
        compare_memory(bench_values, unique_id, systems_groups)

    if "network" not in ignore_list:
        compare_network(bench_values, unique_id, systems_groups)

    if "cpu" not in ignore_list:
        compare_cpu(bench_values, unique_id, systems_groups)


def compare_performance(bench_values, unique_id, systems_groups, detail, rampup_value=0, current_dir=""):
    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, unique_id, 'disk', group)
        check.logical_disks_perf(systems, unique_id, systems_groups.index(group), detail, rampup_value, current_dir)

    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, unique_id, 'cpu', group)
        check.cpu_perf(systems, unique_id, systems_groups.index(group), detail, rampup_value, current_dir)

    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, unique_id, 'cpu', group)
        check.memory_perf(systems, unique_id, systems_groups.index(group), detail, rampup_value, current_dir)

    for group in systems_groups:
        systems = utils.find_sub_element(bench_values, unique_id, 'network', group)
        check.network_perf(systems, unique_id, systems_groups.index(group), detail, rampup_value, current_dir)


def analyze_data(pattern, ignore_list, detail, rampup_value=0, max_rampup_value=0, current_dir=""):
    if rampup_value > 0:
        pattern = pattern + "*.hw"

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
        if rampup_value == 0:
            print "### %d files Selected with pattern '%s' ###" % (len(health_data_file), pattern)
        else:
            print "########## Rampup: %d / %d hosts #########" % (rampup_value, max_rampup_value)

    # Extract data from the hw files
    bench_values = []
    for health in health_data_file:
        bench_values.append(eval(open(health).read()))

    if (rampup_value > 0):
        unique_id = 'uuid'
    else:
        unique_id = 'serial'

    # Extracting the host list from the data to get
    # the initial list of hosts. We have here a single group with all the servers
    systems_groups = []
    systems_groups.append(utils.get_hosts_list(bench_values, unique_id))

    # Let's create groups of similar servers
    if (rampup_value == 0):
        group_systems(bench_values, unique_id, systems_groups, ignore_list)
        compare_sets.print_systems_groups(systems_groups)

    # It's time to compare performance in each group
    compare_performance(bench_values, unique_id, systems_groups, detail, rampup_value, current_dir)
    print "##########################################"
    print
    return bench_values


def compute_deviance_percentage(metric):
    # If we have a single item
    # checking the variance is useless
    array = numpy.array(metric)
    if len(metric) == 1:
        return 0
    return (numpy.std(array) / numpy.mean(array) * 100)


def compute_metric(current_dir, rampup_value, metric, metric_name):
    array = numpy.array(metric)
    mean_group = numpy.mean(metric)
    deviance_percentage = compute_deviance_percentage(metric)
    deviance = numpy.std(array)
    with open(current_dir+"/%s-mean.plot" % metric_name, "a") as myfile:
        if math.isnan(mean_group) is False:
            myfile.write("%d %.2f\n" % (rampup_value, mean_group))
    with open(current_dir+"/%s-deviance_percentage.plot" % metric_name, "a") as myfile:
        if math.isnan(deviance_percentage) is False:
            myfile.write("%d %.2f\n" % (rampup_value, deviance_percentage))
    with open(current_dir+"/%s-deviance.plot" % metric_name, "a") as myfile:
        if math.isnan(deviance) is False:
            myfile.write("%d %.2f\n" % (rampup_value, deviance))


def compute_metrics(current_dir, rampup_value, job, metrics):
    duration = []
    start_lag = []
    for value in metrics["duration"]:
        duration.append(metrics["duration"][value])
    for value in metrics["start_lag"]:
        start_lag.append(float(metrics["start_lag"][value]) * 1000)  # in ms

    compute_metric(current_dir, rampup_value, duration, "job_duration")
    compute_metric(current_dir, rampup_value, start_lag, "jitter")


def do_plot(current_dir, gpm_dir, title, subtitle, name, unit, expected_value=""):
    filename = current_dir+"/"+name+".gnuplot"
    with open(filename, "a") as f:
        if expected_value:
            f.write("call \'%s/graph2D_expected.gpm\' \'%s' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\'\n" % (gpm_dir, title, subtitle, current_dir+"/"+name+".plot", name, current_dir+name, unit, expected_value))
        else:
            f.write("call \'%s/graph2D.gpm\' \'%s' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\'\n" % (gpm_dir, title, subtitle, current_dir+"/"+name+".plot", name, current_dir+name, unit))
    try:
        os.system("gnuplot %s" % filename)
    except:
        True


def extract_hw_info(hw, level1, level2, level3):
    result = []
    temp_level2 = level2
    for entry in hw:
        if level2 == '*':
            temp_level2 = entry[1]
        if (level1 == entry[0] and temp_level2 == entry[1] and level3 == entry[2]):
            result.append(entry[3])
    return result


def is_virtualized(bench_values):
    if "hypervisor" in extract_hw_info(bench_values[0], 'cpu', 'physical_0', 'flags')[0]:
        return "virtualized"
    return ""


def plot_results(current_dir, rampup_values, job, metrics, bench_values):
    gpm_dir = "./"
    context = ""
    bench_type = job
    unit = {}
    expected_value = {}
    expected_value["job_duration-mean"] = metrics["bench"]["runtime"]
    unit["job_duration-mean"] = "seconds (s)"
    unit["job_duration-deviance"] = unit["job_duration-mean"]
    unit["job_duration-deviance_percentage"] = "% of deviance (vs mean perf)"
    unit["jitter-mean"] = "milliseconds (ms)"
    unit["jitter-deviance"] = unit["jitter-mean"]
    unit["jitter-deviance_percentage"] = "% of deviance (vs mean perf)"
    if "cpu" in job:
        unit["deviance"] = "loops_per_sec"
        unit["deviance_percentage"] = "% of deviance (vs mean perf)"
        unit["mean"] = unit["deviance"]
        unit["sum"] = unit["deviance"]
        context = "%d cpu load per host" % metrics["bench"]["cores"]
        bench_type = "%s power" % job
    if "memory" in job:
        unit["deviance"] = "MB/sec"
        unit["deviance_percentage"] = "% of deviance (vs mean perf)"
        unit["mean"] = unit["deviance"]
        unit["sum"] = unit["deviance"]
        bench_type = "%s bandwidth" % job
        context = "%d %s threads per host, blocksize=%s" % (metrics["bench"]["cores"], metrics["bench"]["mode"], metrics["bench"]["block-size"])
    if "network" in job:
        if metrics["bench"]["mode"] == "bandwidth":
            unit["deviance"] = "Mbit/sec"
            bench_type = "%s %s bandwidth" % (job, metrics["bench"]["connection"])
        elif metrics["bench"]["mode"] == "latency":
            unit["deviance"] = "RRQ/sec"
            bench_type = "%s %s latency" % (job, metrics["bench"]["connection"])
        unit["deviance_percentage"] = "% of deviance (vs mean perf)"
        unit["mean"] = unit["deviance"]
        unit["sum"] = unit["deviance"]
        context = "%d %s threads per host, blocksize=%s" % (metrics["bench"]["cores"], metrics["bench"]["mode"], metrics["bench"]["block-size"])
    for kind in unit:
        title = "Study of %s %s from %d to %d hosts (step=%d)" % (bench_type, kind, min(rampup_values), max(rampup_values), metrics["bench"]["step-hosts"])
        total_disk_size = 0
        for disk_size in extract_hw_info(bench_values[0], 'disk', '*', 'size'):
            total_disk_size = total_disk_size + int(disk_size)
        system = "HW per %s host: %s x %s CPUs, %d MB of RAM, %d disks : %d GB total, %d NICs\\n OS : %s running kernel %s, cpu_arch=%s" % \
            (is_virtualized(bench_values),
                extract_hw_info(bench_values[0], 'cpu', 'physical', 'number')[0],
                extract_hw_info(bench_values[0], 'cpu', 'physical_0', 'product')[0],
                int(extract_hw_info(bench_values[0], 'memory', 'total', 'size')[0]) / 1024 / 1024,
                int(extract_hw_info(bench_values[0], 'disk', 'logical', 'count')[0]),
                total_disk_size,
                len(extract_hw_info(bench_values[0], 'network', '*', 'serial')),
                extract_hw_info(bench_values[0], 'system', 'os', 'version')[0],
                extract_hw_info(bench_values[0], 'system', 'kernel', 'version')[0],
                extract_hw_info(bench_values[0], 'system', 'kernel', 'arch')[0])

        subtitle = "\\nBenchmark setup : %s, runtime=%d seconds, %d hypervisors with %s scheduling\\n%s" % (context, metrics["bench"]["runtime"], len(metrics["affinity"]), metrics["bench"]["affinity"], system)

        if kind in expected_value:
            do_plot(current_dir, gpm_dir, title, subtitle, kind, unit[kind], expected_value[kind])
        else:
            do_plot(current_dir, gpm_dir, title, subtitle, kind, unit[kind])


def main(argv):
    pattern = ''
    rampup = ''
    rampup_values = ''
    ignore_list = ''
    detail = {'category': '', 'group': '', 'item': ''}
    try:
        opts, args = getopt.getopt(argv[1:], "hp:l:g:c:i:I:r:", ['pattern', 'log-level', 'group', 'category', 'item', "ignore", "rampup"])
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
        elif opt in ("-r", "--rampup"):
            rampup = arg
            rampup = rampup.replace('\\', '')
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

    if not pattern and not rampup:
        print "Error: Pattern option is mandatory"
        print_help()
        sys.exit(2)

    if rampup:
        if not os.path.isdir(rampup):
            print "Rampup option shall point a directory"
            print "Error: the path %s doesn't exists !" % rampup
            sys.exit(2)

        if not os.path.isfile(rampup + "/hosts"):
            print "A valid rampup directory shall have a 'hosts' file in it"
            print "Exiting"
            sys.exit(2)

        current_dir = "%s/results/" % (rampup)
        try:
            if os.path.exists(current_dir):
                shutil.rmtree(current_dir)
        except IOError as e:
            print "Unable to delete directory %s" % current_dir
            print e
            sys.exit(2)

        rampup_values = [int(name) for name in os.listdir(rampup) if os.path.isdir(rampup+name)]
        if len(rampup_values) < 2:
            print "A valid rampup directory shall have more than 1 output in it"
            print "Exiting"
            sys.exit(2)

        print "Found %d rampup tests to analyse (from %d host up to %d)" % (len(rampup_values), min(rampup_values), max(rampup_values))

    if rampup_values:
        for job in os.listdir("%s/%s" % (rampup, rampup_values[0])):
            current_dir = "%s/results/%s/" % (rampup, job)
            try:
                if not os.path.exists(current_dir):
                    os.makedirs(current_dir)
            except:
                print "Unable to create directory %s" % current_dir
                sys.exit(2)

            print "Processing Job '%s'" % job
            for rampup_value in sorted(rampup_values):

                metrics = {}
                metrics_file = rampup + "/%d/%s/metrics" % (rampup_value, job)
                if not os.path.isfile(metrics_file):
                    print "Missing metric file for rampup=%d (%s)" % (rampup_value, metrics_file)
                    print "Skipping %d" % rampup_value
                    continue
                metrics = eval(open(metrics_file).read())
                compute_metrics(current_dir, rampup_value, job, metrics)

                bench_values = analyze_data(rampup+'/'+str(rampup_value)+'/'+job+'/', ignore_list, detail, rampup_value, max(rampup_values), current_dir)

            plot_results(current_dir, rampup_values, job, metrics, bench_values)

    else:
        analyze_data(pattern, ignore_list, detail)


# Main
if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python2
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Author: Erwan Velu <erwan.velu@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from SocketServer import BaseRequestHandler, ThreadingTCPServer
import ConfigParser
import socket
import struct
from health_messages import Health_Message as HM
import health_libs as HL
import health_protocol as HP
import logging
import os
import pprint
import sys
import threading
import time
import yaml
import math
import shutil
import getopt


socket_list = {}
lock_socket_list = threading.RLock()
hosts = {}
lock_host = threading.RLock()
hosts_state = {}
results_cpu = {}
results_memory = {}
results_network = {}
results_storage = {}
serv = 0
startup_date = ""
NOTHING_RUN = 0
CPU_RUN = 1 << 0
MEMORY_RUN = 1 << 1
STORAGE_RUN = 1 << 2
NETWORK_RUN = 1 << 3

SCHED_FAIR = "fair"

start_jitter = {}
stop_jitter = {}
running_jitter = False
average = lambda x: sum(x) * 1.0 / len(x)
variance = lambda x: map(lambda y: (y - average(x)) ** 2, x)
stdev = lambda x: math.sqrt(average(variance(x)))


def print_help():
    print 'health-server help '
    print
    print '-h --help                     : Print this help'
    print '-f <file>  or --file <file>   : Mandatory option to select the benchmark file'
    print '-t <title> or --title <title> : Optinal option to define a title to this benchmark'
    print '                                 This is useful to describe a temporary context'


def init_jitter():
    global start_jitter
    global stop_jitter
    global running_jitter

    start_jitter = {}
    stop_jitter = {}
    running_jitter = True


def disable_jitter():
    global running_jitter
    running_jitter = False


def start_time(host):
    timestamp = time.time()

    global start_jitter
    if host not in start_jitter:
        start_jitter[host] = [timestamp]
    else:
        start_jitter[host].append(timestamp)


def stop_time(host):
    timestamp = time.time()

    global stop_jitter
    stop_jitter[host] = timestamp


class SocketHandler(BaseRequestHandler):
    global hosts
    global lock_host
    timeout = 5
    disable_nagle_algorithm = False  # Set TCP_NODELAY socket option

    def handle(self):
        lock_socket_list.acquire()
        socket_list[self.client_address] = self.request
        lock_socket_list.release()

        HP.logger.debug('Got connection from %s' % self.client_address[0])
        while True:
            msg = HP.recv_hm_message(socket_list[self.client_address])
            if not msg:
                continue
            if msg.message != HM.ACK:

                # If we do receive a STARTING message, let's record the starting time
                # No need to continue processing the packet, we can wait the next one
                if msg.action == HM.STARTING:
                    start_time(self.client_address)
                    continue

                if msg.message == HM.DISCONNECT:
                    HP.logger.debug('Disconnecting from %s' %
                                    self.client_address[0])

                    lock_host.acquire()
                    del hosts[self.client_address]
                    del hosts_state[self.client_address]
                    lock_host.release()

                    socket_list[self.client_address].close()

                    lock_socket_list.acquire()
                    del socket_list[self.client_address]
                    lock_socket_list.release()
                    return
                else:
                    lock_host.acquire()
                    hosts[self.client_address] = msg
                    hosts_state[self.client_address] = NOTHING_RUN
                    lock_host.release()

                    if msg.message == HM.MODULE and msg.action == HM.COMPLETED:
                        if running_jitter is True:
                            stop_time(self.client_address)

                        if msg.module == HM.CPU:
                            cpu_completed(self.client_address, msg)
                        elif msg.module == HM.MEMORY:
                            memory_completed(self.client_address, msg)
                        elif msg.module == HM.NETWORK:
                            network_completed(self.client_address, msg)
                        elif msg.module == HM.STORAGE:
                            storage_completed(self.client_address, msg)


def createAndStartServer():
    global serv
    ThreadingTCPServer.allow_reuse_address = True
    serv = ThreadingTCPServer(('', 20000), SocketHandler,
                              bind_and_activate=False)
    l_onoff = 1
    l_linger = 0
    serv.socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                           struct.pack('ii', l_onoff, l_linger))
    serv.server_bind()
    serv.server_activate()
    HP.logger.info('Starting server')
    serv.serve_forever()        # blocking method


def cpu_completed(host, msg):
    global hosts_state
    global results_cpu
    hosts_state[host] &= ~CPU_RUN
    results_cpu[host] = msg.hw


def memory_completed(host, msg):
    global hosts_state
    global results_memory
    hosts_state[host] &= ~MEMORY_RUN
    results_memory[host] = msg.hw


def network_completed(host, msg):
    global hosts_state
    global results_network
    hosts_state[host] &= ~NETWORK_RUN
    results_network[host] = msg.hw


def storage_completed(host, msg):
    global hosts_state
    global results_storage
    hosts_state[host] &= ~STORAGE_RUN
    results_storage[host] = msg.hw


def get_host_list(item):
    global hosts
    global hosts_state
    selected_hosts = {}
    for host in hosts.keys():
        if hosts_state[host] & item == item:
            selected_hosts[host] = True

    return selected_hosts


def compute_affinity(bench=[]):
    affinity = {}
    global hosts

    def acceptable_host(host_list, host):
        if (len(host_list) == 0):
            return True
        if host in host_list:
            return True
        return False

    for host in hosts.keys():
        hw = hosts[host].hw
        system_id = HL.get_value(hw, "system", "product", "serial")

        if len(bench) > 0:
            if acceptable_host(bench['affinity-hosts'], system_id) is False:
                continue

        if system_id not in affinity.keys():
            affinity[system_id] = [host]
        else:
            # If the system is already known, it means that several
            # virtual machines are sharing the same Hypervisor
            affinity[system_id].append(host)

    return affinity


def get_fair_hosts_list(affinity_hosts_list, nb_hosts):
    hosts_list = []

    while (len(hosts_list) < nb_hosts):
        for hypervisor in affinity_hosts_list.keys():
            if (len(affinity_hosts_list[hypervisor]) == 0):
                return hosts_list
            hosts_list.append(affinity_hosts_list[hypervisor].pop())
            if (len(hosts_list) == nb_hosts):
                break

    return hosts_list


def get_fair_hosts_list_per_hv(affinity_hosts_list, nb_hosts):
    hosts_list = {}
    for hypervisor in affinity_hosts_list.keys():
        hosts_list[hypervisor] = []

    selected_hosts = 0
    while (selected_hosts < nb_hosts):
        for hypervisor in affinity_hosts_list.keys():
            if (len(affinity_hosts_list[hypervisor]) == 0):
                return hosts_list
            hosts_list[hypervisor].append(affinity_hosts_list[hypervisor].pop())
            selected_hosts = selected_hosts + 1
            if (selected_hosts == nb_hosts):
                break

    return hosts_list


def get_hosts_list_from_affinity(bench, sorted_list=False):
    affinity_hosts_list = compute_affinity(bench)
    hosts_list = []

    if bench['affinity'] == SCHED_FAIR:
        if sorted_list is False:
            hosts_list = get_fair_hosts_list(affinity_hosts_list, bench['nb-hosts'])
        else:
            hosts_list = get_fair_hosts_list_per_hv(affinity_hosts_list, bench['nb-hosts'])
    else:
        HP.logger.error("Unsupported affinity : %s" % bench['affinity'])

    return hosts_list


def dump_affinity(bench, bench_type):
    HP.logger.debug("Using affinity %s on the following mapping :" % bench['affinity'])
    host_affinity = compute_affinity(bench)
    final_list = {}

    if bench_type == HM.NETWORK:
        return bench['hosts-list']

    for hypervisor in host_affinity.keys():
        for hostname in bench['hosts-list']:
            if hostname in host_affinity[hypervisor]:
                if hypervisor not in final_list.keys():
                    final_list[hypervisor] = [hostname]
                else:
                    final_list[hypervisor].append(hostname)
    return final_list


def start_cpu_bench(bench):
    global hosts_state
    nb_hosts = bench['nb-hosts']
    msg = HM(HM.MODULE, HM.CPU, HM.START)
    msg.cpu_instances = bench['cores']
    msg.running_time = bench['runtime']

    for host in bench['hosts-list']:
        if nb_hosts == 0:
            break
        if host not in get_host_list(CPU_RUN).keys():
            hosts_state[host] |= CPU_RUN
            nb_hosts = nb_hosts - 1
            lock_socket_list.acquire()
            start_time(host)
            HP.send_hm_message(socket_list[host], msg)
            lock_socket_list.release()


def start_memory_bench(bench):
    global hosts_state
    nb_hosts = bench['nb-hosts']
    msg = HM(HM.MODULE, HM.MEMORY, HM.START)
    msg.cpu_instances = bench['cores']
    msg.block_size = bench['block-size']
    msg.running_time = bench['runtime']
    msg.mode = bench['mode']

    for host in bench['hosts-list']:
        if nb_hosts == 0:
            break
        if host not in get_host_list(MEMORY_RUN).keys():
            hosts_state[host] |= MEMORY_RUN
            nb_hosts = nb_hosts - 1
            lock_socket_list.acquire()
            start_time(host)
            HP.send_hm_message(socket_list[host], msg)
            lock_socket_list.release()


def start_storage_bench(bench):
    global hosts_state
    nb_hosts = bench['nb-hosts']
    msg = HM(HM.MODULE, HM.STORAGE, HM.START)
    msg.block_size = bench['block-size']
    msg.access = bench['access']
    msg.running_time = bench['runtime']
    msg.mode = bench['mode']
    msg.device = bench['device']
    msg.rampup_time = bench['rampup-time']

    for host in bench['hosts-list']:
        if nb_hosts == 0:
            break
        if host not in get_host_list(STORAGE_RUN).keys():
            hosts_state[host] |= STORAGE_RUN
            nb_hosts = nb_hosts - 1
            lock_socket_list.acquire()
            start_time(host)
            HP.send_hm_message(socket_list[host], msg)
            lock_socket_list.release()


def prepare_network_bench(bench, mode):
    global hosts_state
    nb_hosts = bench['nb-hosts']
    msg = HM(HM.MODULE, HM.NETWORK, mode)
    msg.network_test = bench['mode']
    msg.network_connection = bench['connection']
    msg.peer_servers = bench['ip-list'].items()
    msg.ports_list = bench['port-list']

    for hv in bench['hosts-list']:
        for host in bench['hosts-list'][hv]:
            if nb_hosts == 0:
                break
            if host not in get_host_list(NETWORK_RUN).keys():
                hosts_state[host] |= NETWORK_RUN
                nb_hosts = nb_hosts - 1
                lock_socket_list.acquire()
                msg.my_peer_name = bench['ip-list'][host]
                HP.send_hm_message(socket_list[host], msg)
                lock_socket_list.release()

    string_mode = ""
    if mode == HM.INIT:
        string_mode = "Initialisation"
    else:
        string_mode = "Cleaning"

    HP.logger.info("NETWORK: %s in progress" % string_mode)
    max_timeout = 45
    timeout = 0
    while (get_host_list(NETWORK_RUN).keys()):
        timeout = timeout + 1
        time.sleep(1)
        if timeout == max_timeout:
            HP.logger.error("NETWORK: Failed to %s the following hosts : " % string_mode + str(get_host_list(NETWORK_RUN).keys()))
            return False
    return True


def start_network_bench(bench):
    global hosts_state
    nb_hosts = bench['nb-hosts']
    msg = HM(HM.MODULE, HM.NETWORK, HM.START)
    msg.block_size = bench['block-size']
    msg.running_time = bench['runtime']
    msg.network_test = bench['mode']
    msg.network_connection = bench['connection']
    msg.ports_list = bench['port-list']
    bench['arity_groups'] = []
    arity_group = []
    used_hosts = []
    ip_list = {}

    while nb_hosts > 0:
        for hv in bench['hosts-list']:
            for host in bench['hosts-list'][hv]:
                if nb_hosts == 0:
                    break
                # We shall not use the same host twice
                if host in used_hosts:
                    continue
                used_hosts.append(host)
                arity_group.append(host)
                ip_list[host] = bench['ip-list'][host]
                nb_hosts = nb_hosts - 1
                if len(arity_group) == bench['arity']:
                    bench['arity_groups'].append(arity_group)
                    msg.peer_servers = ip_list.items()
                    for peer_server in arity_group:
                        if peer_server not in get_host_list(NETWORK_RUN).keys():
                            msg.my_peer_name = bench['ip-list'][peer_server]
                            hosts_state[peer_server] |= NETWORK_RUN
                            lock_socket_list.acquire()
                            start_time(peer_server)
                            HP.send_hm_message(socket_list[peer_server], msg)
                            lock_socket_list.release()
                    arity_group = []
                    ip_list = {}
                # We shall break to switch to another hypervisor
                break
        if nb_hosts == 0:
            return


def disconnect_clients():
    global serv
    global hosts
    msg = HM(HM.DISCONNECT)
    HP.logger.info("Asking %d hosts to disconnect" % len(hosts.keys()))
    for host in hosts.keys():
        lock_socket_list.acquire()
        HP.send_hm_message(socket_list[host], msg)
        lock_socket_list.release()

    while(hosts.keys()):
        time.sleep(1)
        HP.logger.info("Still %d hosts connected" % len(hosts.keys()))

    HP.logger.info("All hosts disconnected")
    serv.shutdown()
    serv.socket.close()


def save_hw(items, name, hwdir):
    'Save hw items for inspection on the server.'
    try:
        filename = os.path.join(hwdir, name + '.hw')
        pprint.pprint(items, stream=open(filename, 'w'))
    except Exception, xcpt:
        HP.logger.error("exception while saving hw file: %s" % str(xcpt))


def dump_hosts(log_dir):
    global hosts
    unique_hosts_list = []
    for host in hosts.keys():
        uuid = HL.get_value(hosts[host].hw, "system", "product", "serial")
        if uuid not in unique_hosts_list:
            unique_hosts_list.append(uuid)
    pprint.pprint(unique_hosts_list, stream=open(log_dir+"/hosts", 'w'))
    pprint.pprint(compute_affinity(), stream=open(log_dir+"/affinity", 'w'))


def prepare_metrics(log_dir, bench, bench_type):
    dest_dir = log_dir + '/%d/' % bench['nb-hosts']
    if bench_type == HM.CPU:
        dest_dir = dest_dir + "/cpu-" + bench['name']
    elif bench_type == HM.MEMORY:
        dest_dir = dest_dir + "/memory-" + bench['name']
    elif bench_type == HM.NETWORK:
        dest_dir = dest_dir + "/network-" + bench['name']
    elif bench_type == HM.STORAGE:
        dest_dir = dest_dir + "/storage-" + bench['name']
    else:
        HL.fatal_error("Unknown benchmark type in prepare_metrics")

    try:
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)
    except OSError, e:
        HL.fatal_error("Cannot create %s directory (%s)" % (dest_dir, e.errno))

    output = {}
    output['bench'] = bench
    output['affinity'] = dump_affinity(bench, bench_type)
    pprint.pprint(output, stream=open(dest_dir+"/metrics", 'w'))
    return dest_dir


def compute_metrics(dest_dir, bench, bench_type):
    if bench_type == HM.CPU:
        results = results_cpu
    elif bench_type == HM.MEMORY:
        results = results_memory
    elif bench_type == HM.NETWORK:
        results = results_network
    elif bench_type == HM.STORAGE:
        results = results_storage
    else:
        HL.fatal_error("Unknown benchmark type in compute_metrics")

    delta_start_jitter = {}
    duration = {}
    real_start = {}

    for host in results.keys():
        # Checking jitter settings
        if host not in start_jitter:
            HP.logger.error("Host %s should have a jitter value !" % host)
        else:
            if len(start_jitter[host]) < 2:
                HP.logger.error("Not enough start jitter information for host %s" % host)
            else:
                real_start[host] = start_jitter[host][1]
                delta_start_jitter[host] = (start_jitter[host][1] - start_jitter[host][0])
                duration[host] = (stop_jitter[host] - start_jitter[host][1])
                if (float(duration[host]) > float(bench['runtime'] + 1)):
                    HP.logger.error("Host %s took too much time : %.2f while expecting %d" % (host, duration[host], bench['runtime']))

        HP.logger.debug("Dumping result from host %s" % str(host))
        filename_and_macs = HL.generate_filename_and_macs(results[host])
        save_hw(results[host], filename_and_macs['sysname'], dest_dir)

    output = {}
    output['bench'] = bench
    output['hosts'] = results.keys()
    output['affinity'] = dump_affinity(bench, bench_type)
    output['start_time'] = real_start
    output['start_lag'] = delta_start_jitter
    output['duration'] = duration
    pprint.pprint(output, stream=open(dest_dir+"/metrics", 'w'))


def get_default_value(job, item, default_value):
    return job.get(item, default_value)


def prepare_log_dir(name):
    config = ConfigParser.ConfigParser()
    config.read('/etc/edeploy.conf')

    def config_get(section, name, default):
        'Secured config getter.'
        try:
            return config.get(section, name)
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            return default

    cfg_dir = os.path.normpath(config_get('SERVER', 'HEALTHDIR', '')) + '/'
    dirname = startup_date
    dest_dir = cfg_dir + 'dahc/%s/' % name + dirname

    try:
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)
    except OSError, e:
        HL.fatal_error("Cannot create %s directory (%s)" % (dest_dir, e.errno))

    HP.logger.info("Results will be stored in %s" % dest_dir)
    return dest_dir


def compute_nb_hosts_series(bench):
    nb_hosts_series = []

    # Insure that min_hosts is always part of the serie
    nb_hosts_series.append(bench['min_hosts'])

    # Using the modulo to get the number of interations we have
    for modulo in xrange(1, divmod(bench['max_hosts'], bench['step-hosts'])[0]+1):
        nb_hosts = modulo * bench['step-hosts']
        # Don't save hosts that are below min_hosts
        if nb_hosts > bench['min_hosts']:
            nb_hosts_series.append(nb_hosts)

    # Insure that the max_hosts is always part of the serie
    if bench['max_hosts'] not in nb_hosts_series:
        nb_hosts_series.append(bench['max_hosts'])

    return nb_hosts_series


def parse_job_config(bench, job, component, log_dir):
    bench['component'] = component
    bench['step-hosts'] = get_default_value(job, 'step-hosts', 1)
    bench['name'] = get_default_value(job, 'name', '')
    bench['affinity'] = get_default_value(job, 'affinity', SCHED_FAIR)
    bench['runtime'] = get_default_value(job, 'runtime', bench['runtime'])
    affinity_list = get_default_value(job, 'affinity-hosts', '')
    affinity_hosts = []
    if affinity_list:
        for manual_host in affinity_list.split(","):
            affinity_hosts.append(manual_host.strip())

    bench['affinity-hosts'] = affinity_hosts
    if len(bench['affinity-hosts']) > 0:
        if len(bench['affinity-hosts']) != len(compute_affinity(bench)):
            HP.logger.error("ERROR: Available hypervisors is different than affinity-hosts")
            HP.logger.error("ERROR: %d hypervisors while we expect %d" % (len(compute_affinity(bench)), len(bench['affinity-hosts'])))
            HP.logger.error("ERROR: Please check %s/affinity to see detected hypervisors" % log_dir)
            return False

    required_hosts = get_default_value(job, 'required-hosts',
                                       bench['required-hosts'])
    if "-" in str(required_hosts):
        min_hosts = int(str(required_hosts).split("-")[0])
        max_hosts = int(str(required_hosts).split("-")[1])
    else:
        min_hosts = required_hosts
        max_hosts = min_hosts

    if max_hosts < 1:
        max_hosts = min_hosts
        HP.logger.error("ERROR: required-hosts shall be greater than"
                        " 0, defaulting to global required-hosts=%d"
                        % max_hosts)
        return False

    if max_hosts > bench['required-hosts']:
        HP.logger.error("ERROR: The maximum number of hosts to tests"
                        " is greater than the amount of available"
                        " hosts.")
        return False

    bench['min_hosts'] = min_hosts
    bench['max_hosts'] = max_hosts

    return True


def select_vms_from_networks(bench):
    port_add = 0
    port_list = {}
    hosts_selected_ip = {}
    for hv in bench['hosts-list']:
        for host in bench['hosts-list'][hv]:
            ipv4_list = HL.get_multiple_values(hosts[host].hw, "network", "*", "ipv4")
            match_network = False
            # Let's check if one of the IP of a host match at least one network
            # If so, let's save the resulting IP
            for ip in ipv4_list:
                for network in bench['network-hosts'].split(','):
                    if HL.is_in_network(ip, network.strip()):
                            hosts_selected_ip[host] = ip
                            port_list[host] = HM.port_base + port_add
                            port_add += 1
                            match_network = True

            # If the host is not part of the network we look at
            # Let's remove it from the possible host list
            if match_network is False:
                bench['hosts-list'][hv].remove(host)

    bench['port-list'] = port_list
    bench['ip-list'] = hosts_selected_ip


def do_network_job(bench_all, current_job, log_dir, total_runtime):
    bench = dict(bench_all)

    # In the network bench, step-hosts shall be modulo 2
    bench['step-hosts'] = get_default_value(current_job, 'step-hosts', 2)
    bench['arity'] = get_default_value(current_job, 'arity', 2)

    if parse_job_config(bench, current_job, HM.NETWORK, log_dir) is True:
        # Only consider to watch step-hosts vs arity if we have some rampup
        if (int(bench['min_hosts']) != int(bench['max_hosts'])):
            if ((int(bench['step-hosts']) % int(bench['arity'])) != 0):
                HP.logger.error("NETWORK: step-hosts shall be modulo arity (%d)" % int(bench['arity']))
                HP.logger.error("NETWORK: Canceling Test")
                return False

        if ((int(bench['min_hosts']) % int(bench['arity'])) != 0) or ((int(bench['max_hosts']) % int(bench['arity'])) != 0):
            HP.logger.error("NETWORK: min and max-hosts shall be modulo arity %d" % int(bench['arity']))
            HP.logger.error("NETWORK: Canceling Test")
            return False

        nb_loops = 0
        hosts_series = compute_nb_hosts_series(bench)
        for nb_hosts in hosts_series:
            nb_loops = nb_loops + 1
            iter_bench = dict(bench)
            iter_bench['cores'] = get_default_value(current_job, 'cores', 1)
            iter_bench['block-size'] = get_default_value(current_job, 'block-size', "0")
            iter_bench['mode'] = get_default_value(current_job, 'mode', HM.BANDWIDTH)
            iter_bench['network-hosts'] = get_default_value(current_job, 'network-hosts', "0.0.0.0/0")
            iter_bench['connection'] = get_default_value(current_job, 'connection', HM.TCP)
            iter_bench['nb-hosts'] = nb_hosts
            total_runtime += iter_bench['runtime']

            iter_bench['hosts-list'] = get_hosts_list_from_affinity(iter_bench, True)
            unsorted_list = get_hosts_list_from_affinity(iter_bench)

            if (len(unsorted_list) < iter_bench['nb-hosts']):
                HP.logger.error("NETWORK: %d hosts expected while affinity only provides %d hosts available" % (iter_bench['nb-hosts'], len(unsorted_list)))
                HP.logger.error("NETWORK: Canceling test %d / %d" % ((iter_bench['nb-hosts'], iter_bench['max_hosts'])))
                continue

            select_vms_from_networks(iter_bench)

            if (len(iter_bench['ip-list']) < iter_bench['nb-hosts']):
                HP.logger.error("NETWORK: %d hosts expected while ip-based filtering only provides %d hosts available" % (iter_bench['nb-hosts'], len(iter_bench['ip-list'])))
                HP.logger.error("NETWORK: Canceling test %d / %d" % ((iter_bench['nb-hosts'], iter_bench['max_hosts'])))
                continue

            if (nb_hosts % iter_bench['arity'] != 0):
                HP.logger.error("NETWORK: It's impossible to get an arity=%d with %d hosts" % (iter_bench['arity'], len(iter_bench['nb-hosts'])))
                HP.logger.error("NETWORK: Canceling test %d / %d" % ((iter_bench['nb-hosts'], iter_bench['max_hosts'])))
                continue

            metrics_log_dir = prepare_metrics(log_dir, iter_bench, HM.NETWORK)

            if prepare_network_bench(iter_bench, HM.INIT) is False:
                HP.logger.error("NETWORK: Unable to complete initialisation")
                HP.logger.error("NETWORK: Canceling test %d / %d" % ((iter_bench['nb-hosts'], iter_bench['max_hosts'])))
                prepare_network_bench(iter_bench, HM.CLEAN)
                continue

            if iter_bench['block-size'] != "0":
                HP.logger.info("NETWORK: Waiting %s bench @%s %d / %d"
                               " to finish on %d hosts (step = %d): should take"
                               " %d seconds" % (iter_bench['mode'], iter_bench['block-size'], nb_loops, len(hosts_series),
                                                iter_bench['nb-hosts'], iter_bench['step-hosts'],
                                                iter_bench['runtime']))
            else:
                HP.logger.info("NETWORK: Waiting %s bench %d / %d"
                               " to finish on %d hosts (step = %d): should take"
                               " %d seconds" % (iter_bench['mode'], nb_loops, len(hosts_series),
                                                iter_bench['nb-hosts'], iter_bench['step-hosts'],
                                                iter_bench['runtime']))

            init_jitter()

            start_network_bench(iter_bench)

            time.sleep(bench['runtime'])

            while (get_host_list(NETWORK_RUN).keys()):
                time.sleep(1)

            disable_jitter()

            compute_metrics(metrics_log_dir, iter_bench, HM.NETWORK)

            prepare_network_bench(iter_bench, HM.CLEAN)
    else:
        HP.logger.error("NETWORK: Canceling Test")


def do_storage_job(bench_all, current_job, log_dir, total_runtime):
    bench = dict(bench_all)

    if parse_job_config(bench, current_job, HM.STORAGE, log_dir) is True:
        nb_loops = 0
        hosts_series = compute_nb_hosts_series(bench)
        for nb_hosts in hosts_series:
            nb_loops = nb_loops + 1
            iter_bench = dict(bench)
            iter_bench['cores'] = get_default_value(current_job, 'cores', 1)
            iter_bench['block-size'] = get_default_value(current_job, 'block-size', "4k")
            iter_bench['mode'] = get_default_value(current_job, 'mode', HM.RANDOM)
            iter_bench['access'] = get_default_value(current_job, 'access', HM.READ)
            iter_bench['device'] = get_default_value(current_job, 'device', "vda")
            iter_bench['rampup-time'] = get_default_value(current_job, 'rampup-time', "5")
            iter_bench['nb-hosts'] = nb_hosts
            total_runtime += iter_bench['runtime']

            iter_bench['hosts-list'] = get_hosts_list_from_affinity(iter_bench)

            if (iter_bench['rampup-time'] > iter_bench['runtime']):
                HP.logger.error("STORAGE: Rampup time (%s) is bigger than runtime (%s" %
                                (iter_bench['rampup-time'], iter_bench['runtime']))
                HP.logger.error("STORAGE: Canceling Test")
                return

            if (len(iter_bench['hosts-list']) < iter_bench['nb-hosts']):
                HP.logger.error("STORAGE: %d hosts expected while affinity only provides %d hosts available" % (iter_bench['nb-hosts'], len(iter_bench['hosts-list'])))
                HP.logger.error("STORAGE: Canceling test %d / %d" % ((iter_bench['nb-hosts'], iter_bench['max_hosts'])))
                continue

            HP.logger.info("STORAGE: Waiting %s %s bench %s@%s %d / %d"
                           " to finish on %d hosts (step = %d): should take"
                           " %d seconds" % (iter_bench['mode'], iter_bench['access'], iter_bench['device'],
                                            iter_bench['block-size'], nb_loops, len(hosts_series),
                                            iter_bench['nb-hosts'], iter_bench['step-hosts'],
                                            iter_bench['runtime']))

            metrics_log_dir = prepare_metrics(log_dir, iter_bench, HM.STORAGE)

            init_jitter()

            start_storage_bench(iter_bench)

            time.sleep(bench['runtime'])

            while (get_host_list(STORAGE_RUN).keys()):
                time.sleep(1)

            disable_jitter()

            compute_metrics(metrics_log_dir, iter_bench, HM.STORAGE)
    else:
        HP.logger.error("STORAGE: Canceling Test")


def do_memory_job(bench_all, current_job, log_dir, total_runtime):
    bench = dict(bench_all)

    if parse_job_config(bench, current_job, HM.MEMORY, log_dir) is True:
        nb_loops = 0
        hosts_series = compute_nb_hosts_series(bench)
        for nb_hosts in hosts_series:
            nb_loops = nb_loops + 1
            iter_bench = dict(bench)
            iter_bench['cores'] = get_default_value(current_job, 'cores', 1)
            iter_bench['block-size'] = get_default_value(current_job, 'block-size', "128M")
            iter_bench['mode'] = get_default_value(current_job, 'mode', HM.FORKED)
            iter_bench['nb-hosts'] = nb_hosts
            total_runtime += iter_bench['runtime']

            iter_bench['hosts-list'] = get_hosts_list_from_affinity(iter_bench)

            if (len(iter_bench['hosts-list']) < iter_bench['nb-hosts']):
                HP.logger.error("MEMORY: %d hosts expected while affinity only provides %d hosts available" % (iter_bench['nb-hosts'], len(iter_bench['hosts-list'])))
                HP.logger.error("MEMORY: Canceling test %d / %d" % ((iter_bench['nb-hosts'], iter_bench['max_hosts'])))
                continue

            HP.logger.info("MEMORY: Waiting bench @%s %d / %d"
                           " to finish on %d hosts (step = %d): should take"
                           " %d seconds" % (iter_bench['block-size'], nb_loops, len(hosts_series),
                                            iter_bench['nb-hosts'], iter_bench['step-hosts'],
                                            iter_bench['runtime']))

            metrics_log_dir = prepare_metrics(log_dir, iter_bench, HM.MEMORY)

            init_jitter()

            start_memory_bench(iter_bench)

            time.sleep(bench['runtime'])

            while (get_host_list(MEMORY_RUN).keys()):
                time.sleep(1)

            disable_jitter()

            compute_metrics(metrics_log_dir, iter_bench, HM.MEMORY)
    else:
        HP.logger.error("MEMORY: Canceling Test")


def do_cpu_job(bench_all, current_job, log_dir, total_runtime):
    bench = dict(bench_all)

    if parse_job_config(bench, current_job, HM.CPU, log_dir) is True:
        nb_loops = 0
        hosts_series = compute_nb_hosts_series(bench)
        for nb_hosts in hosts_series:
            nb_loops = nb_loops + 1
            iter_bench = dict(bench)
            iter_bench['cores'] = get_default_value(current_job, 'cores', 1)
            iter_bench['nb-hosts'] = nb_hosts
            total_runtime += iter_bench['runtime']

            iter_bench['hosts-list'] = get_hosts_list_from_affinity(iter_bench)

            if (len(iter_bench['hosts-list']) < iter_bench['nb-hosts']):
                HP.logger.error("CPU: %d hosts expected while affinity only provides %d hosts available" % (iter_bench['nb-hosts'], len(iter_bench['hosts-list'])))
                HP.logger.error("CPU: Canceling test %d / %d" % ((iter_bench['nb-hosts'], iter_bench['max_hosts'])))
                continue

            HP.logger.info("CPU: Waiting bench %d / %d"
                           " to finish on %d hosts (step = %d): should take"
                           " %d seconds" % (nb_loops, len(hosts_series),
                                            iter_bench['nb-hosts'], iter_bench['step-hosts'],
                                            iter_bench['runtime']))

            metrics_log_dir = prepare_metrics(log_dir, iter_bench, HM.CPU)

            init_jitter()

            start_cpu_bench(iter_bench)

            time.sleep(bench['runtime'])

            while (get_host_list(CPU_RUN).keys()):
                time.sleep(1)

            disable_jitter()

            compute_metrics(metrics_log_dir, iter_bench, HM.CPU)
    else:
        HP.logger.error("CPU: Canceling Test")


def non_interactive_mode(filename, title):
    global hosts
    total_runtime = 0
    name = "undefined"
    bench_all = {}

    bench_all['title'] = title

    job = yaml.load(file(filename, 'r'))
    if job['name'] is None:
        HP.logger.error("Missing name parameter in yaml file")
        disconnect_clients()
        return
    else:
        name = job['name']

    if job['required-hosts'] is None:
        HP.logger.error("Missing required-hosts parameter in yaml file")
        disconnect_clients()
        return

    bench_all['required-hosts'] = int(job['required-hosts'])
    if bench_all['required-hosts'] < 1:
        HP.logger.error("required-hosts shall be greater than 0")
        disconnect_clients()
        return

    bench_all['runtime'] = get_default_value(job, 'runtime', 10)
    bench_all['required-hypervisors'] = get_default_value(job, 'required-hypervisors', 0)

    log_dir = prepare_log_dir(name)

    # Saving original yaml file
    shutil.copy2(filename, log_dir)
    if (int(bench_all['required-hypervisors']) > 0):
        HP.logger.info("Expecting %d hosts on %d hypervisors to start job %s" %
                       (bench_all['required-hosts'], int(bench_all['required-hypervisors']),
                           name))
    else:
        HP.logger.info("Expecting %d hosts to start job %s" %
                       (bench_all['required-hosts'], name))
    hosts_count = len(hosts.keys())
    previous_hosts_count = hosts_count
    while (int(hosts_count) < bench_all['required-hosts']):
        if (hosts_count != previous_hosts_count):
            HP.logger.info("Still %d hosts to connect" % (bench_all['required-hosts'] - int(hosts_count)))
            previous_hosts_count = hosts_count
            dump_hosts(log_dir)
        hosts_count = len(hosts.keys())
        time.sleep(1)

    dump_hosts(log_dir)

    if len(compute_affinity()) < int(bench_all['required-hypervisors']):
        HP.logger.error("%d hypervisors expected but only %d found" % (bench_all['required-hypervisors'], len(compute_affinity())))
        HP.logger.error("Please adjust 'required-hypervisors' option")
        HP.logger.error("Exiting")
        disconnect_clients()
        return

    HP.logger.info("Starting %s" % name)
    for next_job in job['jobs']:
        HP.logger.info("Starting job %s" % next_job)
        global results_network
        global results_cpu
        global results_memory
        global results_storage
        results_network = {}
        results_cpu = {}
        results_memory = {}
        results_storage = {}
        current_job = job['jobs'][next_job]
        current_job['name'] = next_job
        if 'component' not in current_job.keys():
            HP.logger.error("Missing component in job %s, canceling job" % current_job['name'])
            continue
        if "cpu" in current_job['component']:
                do_cpu_job(bench_all, current_job, log_dir, total_runtime)
        if "memory" in current_job['component']:
                do_memory_job(bench_all, current_job, log_dir, total_runtime)
        if "network" in current_job['component']:
                do_network_job(bench_all, current_job, log_dir, total_runtime)
        if "storage" in current_job['component']:
                do_storage_job(bench_all, current_job, log_dir, total_runtime)

    HP.logger.info("End of %s" % name)
    HP.logger.info("Results are available here : %s" % log_dir)
    disconnect_clients()


if __name__ == '__main__':

    HP.start_log('/var/log/health-server.log', logging.INFO)
    input_file = ""
    title = ""
    startup_date = time.strftime("%Y_%m_%d-%Hh%M", time.localtime())

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:t:", ['file', 'title'])
    except getopt.GetoptError:
        print "Error: One of the options passed to the cmdline was not supported"
        print "Please fix your command line or read the help (-h option)"
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit(0)
        elif opt in ("-f", "--file"):
            input_file = arg
        elif opt in ("-t", "--title"):
            title = arg

    if not input_file:
        HP.logger.error("You must provide a yaml file as argument")
        sys.exit(1)

    if not title:
        title = startup_date
        HP.logger.info("No title provided, setup a default one to %s" % title)

    myThread = threading.Thread(target=createAndStartServer)
    myThread.start()

    non_interactive = threading.Thread(target=non_interactive_mode,
                                       args=tuple([input_file, title]))
    non_interactive.start()

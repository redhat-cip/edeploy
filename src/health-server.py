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

socket_list = {}
lock_socket_list = threading.RLock()
hosts = {}
lock_host = threading.RLock()
hosts_state = {}
results_cpu = {}
serv = 0
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


def get_host_list(item):
    global hosts
    global hosts_state
    selected_hosts = {}
    for host in hosts.keys():
        if hosts_state[host] & item == item:
            selected_hosts[host] = True

    return selected_hosts


def compute_affinity(affinity_hosts):
    affinity = {}

    def acceptable_host(host_list, host):
        if (len(host_list) == 0):
            return True
        if host in host_list:
            return True
        return False

    for host in hosts.keys():
        hw = hosts[host].hw
        system_id = HL.get_value(hw, "system", "product", "serial")

        if acceptable_host(affinity_hosts, system_id) is False:
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


def get_hosts_list_from_affinity(nb_hosts, affinity, affinity_hosts):
    affinity_hosts_list = compute_affinity(affinity_hosts)
    hosts_list = []

    if affinity == SCHED_FAIR:
        hosts_list = get_fair_hosts_list(affinity_hosts_list, nb_hosts)
    else:
        HP.logger.error("Unsupported affinity : %s" % affinity)

    return hosts_list


def dump_affinity(affinity, affinity_hosts, selected_host_list, dest_dir):
    HP.logger.info("Using affinity %s on the following mapping :" % affinity)
    host_affinity = compute_affinity(affinity_hosts)
    final_list = {}
    for hypervisor in host_affinity.keys():
        for hostname in selected_host_list:
            if hostname in host_affinity[hypervisor]:
                if hypervisor not in final_list.keys():
                    final_list[hypervisor] = [hostname]
                else:
                    final_list[hypervisor].append(hostname)

    pprint.pprint(final_list)
    pprint.pprint(final_list, stream=open(dest_dir+"/affinity", 'w'))


def start_cpu_bench(nb_hosts, hosts_list, runtime, cores):
    global hosts_state
    msg = HM(HM.MODULE, HM.CPU, HM.START)
    msg.cpu_instances = cores
    msg.running_time = runtime

    for host in hosts_list:
        if nb_hosts == 0:
            break
        if host not in get_host_list(CPU_RUN).keys():
            hosts_state[host] |= CPU_RUN
            nb_hosts = nb_hosts - 1
            lock_socket_list.acquire()
            start_time(host)
            HP.send_hm_message(socket_list[host], msg)
            lock_socket_list.release()


def disconnect_clients():
    global serv
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
    unique_hosts_list = []
    for host in hosts.keys():
        uuid = HL.get_value(hosts[host].hw, "system", "product", "serial")
        if uuid not in unique_hosts_list:
            unique_hosts_list.append(uuid)
    pprint.pprint(unique_hosts_list, stream=open(log_dir+"/hosts", 'w'))


def compute_results(log_dir, nb_hosts, affinity, affinity_hosts, hosts_list, runtime):
    dest_dir = log_dir + '/%d/' % nb_hosts

    try:
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)
    except OSError, e:
        HL.fatal_error("Cannot create %s directory (%s)" % (dest_dir, e.errno))

    dump_affinity(affinity, affinity_hosts, hosts_list, dest_dir)

    delta_start_jitter = {}
    duration = {}
    real_start = []

    for host in results_cpu.keys():
        # Checking jitter settings
        if host not in start_jitter:
            HP.logger.error("Host %s should have a jitter value !" % host)
        else:
            if len(start_jitter[host]) < 2:
                HP.logger.error("Not enough start jitter information for host %s" % host)
            else:
                real_start.append(start_jitter[host][1])
                delta_start_jitter[host] = (start_jitter[host][1] - start_jitter[host][0])
                duration[host] = (stop_jitter[host] - start_jitter[host][1])
                if (float(duration[host]) > float(runtime + 1)):
                    HP.logger.error("Host %s took too much time : %.2f while expecting %d" % (host, duration[host], runtime))

        HP.logger.info("Dumping cpu result from host %s" % str(host))
        filename_and_macs = HL.generate_filename_and_macs(results_cpu[host])
        save_hw(results_cpu[host], filename_and_macs['sysname'], dest_dir)

    pprint.pprint("RESULT")
    pprint.pprint(delta_start_jitter)
    pprint.pprint(duration)
    pprint.pprint(stdev(real_start))


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
    dirname = time.strftime("%Y_%m_%d-%Hh%M", time.localtime())
    dest_dir = cfg_dir + 'dahc/%s/' % name + dirname

    try:
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)
    except OSError, e:
        HL.fatal_error("Cannot create %s directory (%s)" % (dest_dir, e.errno))

    HP.logger.info("Results will be stored in %s" % dest_dir)
    return dest_dir


def compute_nb_hosts_series(min_hosts, max_hosts, step_hosts):
    nb_hosts_series = []

    # Insure that min_hosts is always part of the serie
    nb_hosts_series.append(min_hosts)
    
    # Using the modulo to get the number of interations we have
    for modulo in xrange(1, divmod(max_hosts, step_hosts)[0]+1):
        nb_hosts = modulo * step_hosts
        # Don't save hosts that are below min_hosts
        if nb_hosts > min_hosts:
            nb_hosts_series.append(nb_hosts)

    # Insure that the max_hosts is always part of the serie
    if max_hosts not in nb_hosts_series:
        nb_hosts_series.append(max_hosts)

    return nb_hosts_series


def non_interactive_mode(filename):
    total_runtime = 0
    name = "undefined"

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

    required_hosts = job['required-hosts']
    if required_hosts < 1:
        HP.logger.error("required-hosts shall be greater than 0")
        disconnect_clients()
        return

    runtime = get_default_value(job, 'runtime', 0)

    log_dir = prepare_log_dir(name)

    HP.logger.info("Expecting %d hosts to start job %s" %
                   (required_hosts, name))
    hosts_count = len(hosts.keys())
    previous_hosts_count = hosts_count
    while (int(hosts_count) < int(required_hosts)):
        if (hosts_count != previous_hosts_count):
            HP.logger.info("Still %d hosts to connect" % (int(required_hosts) - int(hosts_count)))
            previous_hosts_count = hosts_count
        hosts_count = len(hosts.keys())
        time.sleep(1)

    dump_hosts(log_dir)

    HP.logger.info("Starting job %s" % name)
    cpu_job = job['cpu']
    if cpu_job:
            cancel_job = False
            step_hosts = get_default_value(cpu_job, 'step-hosts', 1)
            affinity = get_default_value(cpu_job, 'affinity', SCHED_FAIR)
            affinity_list = get_default_value(cpu_job, 'affinity-hosts', '')
            affinity_hosts = []
            if affinity_list:
                for manual_host in affinity_list.split(","):
                    affinity_hosts.append(manual_host.strip())

            required_cpu_hosts = get_default_value(cpu_job, 'required-hosts',
                                                   required_hosts)
            if "-" in str(required_cpu_hosts):
                min_hosts = int(str(required_cpu_hosts).split("-")[0])
                max_hosts = int(str(required_cpu_hosts).split("-")[1])
            else:
                min_hosts = required_cpu_hosts
                max_hosts = min_hosts

            if max_hosts < 1:
                max_hosts = min_hosts
                HP.logger.error("CPU: required-hosts shall be greater than"
                                " 0, defaulting to global required-hosts=%d"
                                % max_hosts)
                cancel_job = True

            if max_hosts > required_hosts:
                HP.logger.error("CPU: The maximum number of hosts to tests"
                                " is greater than the amount of available"
                                " hosts.")
                cancel_job = True

            if cancel_job is False:
                for nb_hosts in compute_nb_hosts_series(min_hosts, max_hosts, step_hosts):
                    cpu_runtime = get_default_value(cpu_job, 'runtime',
                                                    runtime)
                    total_runtime += cpu_runtime
                    cores = get_default_value(cpu_job, 'cores', 1)
                    hosts_list = get_hosts_list_from_affinity(nb_hosts, affinity, affinity_hosts)

                    if (len(hosts_list) < nb_hosts):
                        HP.logger.error("CPU: %d hosts expected while affinity only provides %d hosts available" % (nb_hosts, len(hosts_list)))
                        HP.logger.error("CPU: Canceling test %d / %d" % ((nb_hosts, max_hosts)))
                        continue

                    HP.logger.info("CPU: Waiting bench %d / %d (step = %d)"
                                   " to finish on %d hosts : should take"
                                   " %d seconds" % (nb_hosts, max_hosts,
                                                    step_hosts, nb_hosts,
                                                    cpu_runtime))

                    init_jitter()

                    start_cpu_bench(nb_hosts, hosts_list, cpu_runtime, cores)

                    time.sleep(cpu_runtime)

                    while (get_host_list(CPU_RUN).keys()):
                        time.sleep(1)

                    disable_jitter()

                    compute_results(log_dir, nb_hosts, affinity, affinity_hosts, hosts_list, cpu_runtime)
            else:
                HP.logger.error("CPU: Canceling Test")
    HP.logger.info("End of job %s" % name)
    disconnect_clients()


if __name__ == '__main__':

    HP.start_log('/var/tmp/health-server.log', logging.INFO)

    if len(sys.argv) < 2:
        HP.logger.error("You must provide a yaml file as argument")
        sys.exit(1)

    myThread = threading.Thread(target=createAndStartServer)
    myThread.start()

    non_interactive = threading.Thread(target=non_interactive_mode,
                                       args=tuple([sys.argv[1]]))
    non_interactive.start()

#!/usr/bin/python2

import curses
import curses.textpad
import curses.ascii
import fcntl
from SocketServer import BaseRequestHandler, ThreadingTCPServer
import socket
import struct
from health_messages import Health_Message as HM
import health_protocol as HP
import logging
import os
import sys    
import termios
import traceback
import threading
import time
import yaml

socket_list = {}
lock_socket_list = threading.RLock()
hosts = {}
lock_host = threading.RLock()
hosts_state = {}
results_cpu = {}
serv = 0
NOTHING_RUN = 0
CPU_RUN     = 1 << 0
MEMORY_RUN  = 1 << 1
STORAGE_RUN = 1 << 2
NETWORK_RUN = 1 << 3

class SocketHandler(BaseRequestHandler):
    global hosts
    global lock_host
    timeout = 5
    disable_nagle_algorithm = False # Set TCP_NODELAY socket option

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
                if msg.message == HM.DISCONNECT:
                    HP.logger.debug('Disconnecting from %s' % self.client_address[0])

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
                        if msg.module == HM.CPU:
                            cpu_completed(self.client_address, msg)


def createAndStartServer():
    global serv
    ThreadingTCPServer.allow_reuse_address = True
    serv = ThreadingTCPServer(('', 20000), SocketHandler, bind_and_activate=False)
    l_onoff = 1                                                                                                                                                           
    l_linger = 0                                                                                                                                                          
    serv.socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', l_onoff, l_linger))
    serv.server_bind()
    serv.server_activate()
    HP.logger.info('Starting server')
    serv.serve_forever() #blocking method


def cpu_completed(host, msg):
    global hosts_state
    global results_cpu
    hosts_state[host] |= CPU_RUN
    results_cpu[host] = msg.hw


def get_host_list(item):
    global hosts
    global hosts_state
    selected_hosts = {}
    for host in hosts.keys():
        if hosts_state[host] & item == item:
            selected_hosts[host] = True

    return selected_hosts

def start_cpu_bench(nb_hosts, runtime):
    msg = HM(HM.MODULE, HM.CPU, HM.START)
    msg.cpu_instances = 1
    msg.running_time = runtime
    for host in hosts.keys():
        if nb_hosts == 0:
            break;
        if not host in get_host_list(CPU_RUN).keys():
            nb_hosts = nb_hosts - 1
            lock_socket_list.acquire()
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


def compute_results():
    for host in results_cpu.keys():
        HP.logger.info("Dumping cpu result from host %s" % str(host))
        print results_cpu[host]


def get_default_value(job, item, default_value):
    return job.get(item, default_value)


def non_interactive_mode():
    total_runtime = 0
    name = "undefined"

    job = yaml.load(file('test.yaml','r'))
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

    HP.logger.info("Expecting %d hosts to start job %s" % (required_hosts, name))
    while (len(hosts.keys()) < required_hosts):
        time.sleep(1)

    HP.logger.info("Starting job %s" % name)
    cpu_job = job['cpu']
    if cpu_job:
            cpu_runtime = get_default_value(cpu_job, 'runtime', runtime)
            total_runtime += cpu_runtime
            required_cpu_hosts = get_default_value(cpu_job, 'required-hosts', required_hosts)
            if required_cpu_hosts < 1:
                required_cpu_hosts = required_hosts
                HP.logger.error("CPU: required-hosts shall be greater than 0, defaulting to global required-hosts=%d" % required_cpu_hosts)
            HP.logger.info("CPU job will take %d seconds on %d hosts" % (cpu_runtime, required_cpu_hosts))
            start_cpu_bench(required_cpu_hosts, cpu_runtime)

    HP.logger.info("Waiting bench to finish (should take %d seconds)" % total_runtime)
    while (get_host_list(CPU_RUN).keys()):
            time.sleep(1)
    HP.logger.info("End of job %s" % name)
    compute_results()
    disconnect_clients()


if __name__=='__main__':

    HP.start_log('/var/tmp/health-server.log', logging.DEBUG)

    myThread = threading.Thread(target=createAndStartServer)
    myThread.start()

    non_interactive = threading.Thread(target=non_interactive_mode)
    non_interactive.start()


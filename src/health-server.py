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
hosts_cpu = {}
lock_cpu = threading.RLock()
results_cpu = {}
serv = 0
cpu = 0


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
                    lock_host.release()

                    socket_list[self.client_address].close()

                    lock_socket_list.acquire()
                    del socket_list[self.client_address]
                    lock_socket_list.release()
                    return
                else:
                    lock_host.acquire()
                    hosts[self.client_address] = msg
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


def update_time(screen):
    global cpu
    global hosts
    while 1:
        connected = len(hosts.keys())

        bar_str = "CPU:%s" % cpu
        host_str = "C:%d" % connected
        screen.addstr(39, 0, "%s" % bar_str)
        screen.addstr(40, 0, "%s" % host_str)
        screen.addstr(0, 0, time.strftime("%a, %d %b %Y %H:%M:%S"))
        screen.refresh()
        time.sleep(1)

def cpu_completed(host, msg):
    global hosts
    global cpu
    del hosts_cpu[host]
    cpu = cpu - 1
    results_cpu[host] = msg.hw



def change_cpu(amount):
    global cpu
    global hosts
    if (cpu + amount > 0):
#        if amount < 0:
        if amount > 0:
            msg = HM(HM.MODULE, HM.CPU, HM.START)
            msg.cpu_instances = 1
            msg.running_time = 10
            for host in hosts.keys():
                if not host in hosts_cpu.keys():
                    hosts_cpu[host] = True
                    lock_socket_list.acquire()
                    HP.send_hm_message(socket_list[host], msg)
                    lock_socket_list.release()
           
        cpu = cpu + amount
                

def interactive_mode():
    global cpu
    try:
        stdscr = curses.initscr()
        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        curses.noecho()
        curses.cbreak()

        # In keypad mode, escape sequences for special keys
        # (like the cursor keys) will be interpreted and
        # a special value like curses.KEY_LEFT will be returned
        stdscr.keypad(1)

        stdscr.clear()
        clock = threading.Thread(target=update_time, args=(stdscr,))
        clock.daemon = True
        clock.start()
        while 1:
            c = stdscr.getch()
            if c == ord('c'):
                    change_cpu(-1)
            elif c == ord('C'):
                    change_cpu(+1)
            elif c == ord('q'):
                break  # Exit the while()
            elif c == curses.KEY_HOME:
                x = y = 0

        # Set everything back to normal
        clock.stop()
        stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()                 # Terminate curses
    except:
        # In event of error, restore terminal to sane state.
        stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        traceback.print_exc()           # Print the exceptionif __name__ == '__main__':


def start_cpu_bench(nb_hosts, runtime):
    msg = HM(HM.MODULE, HM.CPU, HM.START)
    msg.cpu_instances = 1
    msg.running_time = runtime
    for host in hosts.keys():
        if nb_hosts == 0:
            break;
        if not host in hosts_cpu.keys():
            nb_hosts = nb_hosts - 1
            hosts_cpu[host] = True
            lock_socket_list.acquire()
            HP.send_hm_message(socket_list[host], msg)
            lock_socket_list.release()


def disconnect_clients():
    global serv
    msg = HM(HM.DISCONNECT)
    for host in hosts.keys():
            lock_socket_list.acquire()
            HP.send_hm_message(socket_list[host], msg)
            lock_socket_list.release()
    serv.shutdown()
    serv.socket.close()

def compute_results():
    for host in results_cpu.keys():
        HP.logger.info("Dumping cpu result from host %s" % host)
        print results_cpu[host]

def non_interactive_mode():
    runtime = 0
    job = yaml.load(file('test.yaml','r'))
    HP.logger.info("Expecting %d hosts to start job %s" % (job['required-host-count'], job['name']))
    while (len(hosts.keys()) < job['required-host-count']):
        time.sleep(1)
    HP.logger.info("Starting job %s" % job['name'])
    cpu_job = job['cpu']
    if cpu_job:
            runtime += cpu_job['runtime']
            start_cpu_bench(job['required-host-count'], cpu_job['runtime'])

    HP.logger.info("Waiting bench to finish (should take %d seconds)" % runtime)
    while (hosts_cpu.keys()):
            time.sleep(1)
    HP.logger.info("End of job %s" % job['name'])
    compute_results()
    disconnect_clients()


if __name__=='__main__':

    HP.start_log('/var/tmp/health-server.log', logging.DEBUG)

    myThread = threading.Thread(target=createAndStartServer)
    myThread.start()

    non_interactive = threading.Thread(target=non_interactive_mode)
    non_interactive.start()

#    interactive = threading.Thread(target=interactive_mode)
#    interactive.start()


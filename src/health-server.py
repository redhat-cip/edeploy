#!/usr/bin/python3

import curses
import curses.textpad
import curses.ascii
import fcntl
from socketserver import BaseRequestHandler, ThreadingTCPServer
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

socket_list = {}
lock_socket_list = threading.RLock()
hosts = {}
lock_host = threading.RLock()
hosts_cpu = {}
lock_cpu = threading.RLock()
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

                    lock_socket_list.acquire()
                    del socket_list[self.client_address]
                    lock_socket_list.release()

                    socket_list[self.client_address].close()
                    return
                else:
                    lock_host.acquire()
                    hosts[self.client_address] = msg.message
                    lock_host.release()


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
        connected = 0
        lock_host.acquire()
        for key in hosts.keys():
            msg_type = HM(hosts[key]).message
            if msg_type == HM.CONNECT:
                connected = connected + 1
        lock_host.release()

        bar_str = "CPU:%s" % cpu
        host_str = "C:%d" % connected
        screen.addstr(39, 0, "%s" % bar_str)
        screen.addstr(40, 0, "%s" % host_str)
        screen.addstr(0, 0, time.strftime("%a, %d %b %Y %H:%M:%S"))
        screen.refresh()
        time.sleep(1)

def change_cpu(amount):
    global cpu
    global hosts
    if (cpu + amount > 0):
#        if amount < 0:
        if amount > 0:
            msg = HM(HM.MODULE, HM.CPU, HM.START)
            msg.instance = 1
            msg.running_time = 2
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


if __name__=='__main__':

    HP.start_log('/var/tmp/health-server.log', logging.DEBUG)

    myThread = threading.Thread(target=createAndStartServer)
    myThread.start()

    interactive = threading.Thread(target=interactive_mode)
    interactive.start()


#!/usr/bin/env python
#
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
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

import sys
import socket
import struct
import cPickle
import time
import threading
timestamp={}
server_list={}
semaphore=threading.Semaphore()
synthesis=False
discovery=True

''' How many seconds between sending a keep alive message '''
KEEP_ALIVE=2

''' Amount of seconds no system shall {dis]appear '''
DISCOVERY_TIME=5*KEEP_ALIVE

''' Multicast Address used to communicate '''
MCAST_GRP = '224.1.1.1'

''' Mutlicast Port used to communicate '''
MCAST_PORT = 10987

def get_mac(hw, level1, level2):
    ''' Extract a Mac Address from an hw list '''
    for entry in hw:
        if (level1==entry[0] and level2==entry[2]):
            return entry[3]
    return None

def get_ip_list(hw):
    ''' Extract All IPV4 addresses from hw list '''
    ip_list=[]
    for entry in hw:
        if (entry[0]=='network') and (entry[2]=='ipv4'):
           ip_list.append(entry[3])
    return ip_list

''' Server is made for receiving keepalives and manage them '''
def start_server():
    global server_list
    global timestamp
    global synthesis
    global discovery

    ''' Let's bind a server to the Multicast group '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MCAST_GRP, MCAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    ''' Until we got a synthesis list from another server '''
    while not synthesis:
      answer={}
      ''' Let's get keepalives from servers '''
      answer=cPickle.loads(sock.recv(10240))

      ''' Let's protect shared variables with the scrubbing '''
      semaphore.acquire()

      ''' If the keepalive is Synthesis, we shall only consider this list '''
      if 'SYNTHESIS' in answer.keys():
          sys.stderr.write("Received Synthesis\n")
          server_list={}
          timestamp={}
          synthesis=True
          ''' We are no more in a discovery phase, that will kill client '''
          discovery=False

          ''' We shall not keep the Synthesis entry as it doesn't mean a server '''
          del(answer['SYNTHESIS'])

          ''' We shall wait at least 2 Keep alives to insure client completed his task '''
          time.sleep(2*KEEP_ALIVE)

      for key in answer.keys():
        if not key in server_list.keys():
            ''' Let's add the new server if we didn't knew it '''
            if not synthesis:
                sys.stderr.write('Adding %s\n'%key)
            server_list[key]=answer[key]
            timestamp[key]=time.time()
        else:
            ''' We knew that server, let's refresh the timestamp '''
            sys.stderr.write('Received Keepalive from %s\n'%key)
            timestamp[key]=time.time()

      ''' No more concurrency with scrubbing, let's releae the semaphore '''
      semaphore.release()

    sys.stderr.write("Exiting server\n")

''' Client is made for generating keepalives'''
def start_client(hw):
    global discovery
    ''' Let's find all IPV4 addresses we know about the system '''
    my_ip_list=get_ip_list(hw)

    ''' Let's find our mac address '''
    mac_addr='%s'%get_mac(hw,'network', 'serial')

    ''' Let's prepare a host entry '''
    host_info={}
    host_info[mac_addr]=my_ip_list

    ''' Let's prepare the socket '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    ''' While we are in discovery mode, let's send keepalives '''
    while discovery:
        sys.stderr.write("Sending keepalive for %s\n"%mac_addr)
        sock.sendto(cPickle.dumps(host_info), (MCAST_GRP, MCAST_PORT))
        time.sleep(KEEP_ALIVE)
    sys.stderr.write("Exiting Client, end of discovery\n")

def fatal_error(error):
    '''Report a shell script with the error message and log
    the message on stderr.'''
    sys.stderr.write('%s\n' % error)
    sys.exit(1)

''' Scrubbing is made for deleting server that didn't sent keepalive on time '''
def scrub_timestamp():
    global discovery
    global timestamp
    global server_list
    previous_system_count=0
    previous_time=time.time()
    system_count=0

    ''' Scurbbing have only a meaning during discovery '''
    while discovery:
        current_time=time.time()
        semaphore.acquire()

        ''' Let's check all entries we knew '''
        for key in timestamp.keys():
            ''' If we missed two consecutive keep alive,'''
            if current_time > timestamp[key]+(KEEP_ALIVE*3):
                ''' We need to delete this server '''
                sys.stderr.write('Deleting too old entry : %s\n'%key)
                del timestamp[key]
                del server_list[key]
        #sys.stderr.write("%d systems detected\n"%len(timestamp.keys()))
        system_count=len(timestamp.keys())
        semaphore.release()

        ''' If the number of known systems changed + or -, let's save the current time & amount of servers '''
        if (system_count != previous_system_count):
            previous_system_count=system_count
            previous_time=current_time
        else:
            ''' Let's wait until we didn't got any changes since DISCOVERY_TIME seconds '''
            if current_time-previous_time >= DISCOVERY_TIME:
                ''' We are no more in discovery, that will kill the client '''
                discovery=False
                sys.stderr.write("About to send the synthesis\n")
                ''' We need to wait two keep alive to insure client completed his task '''
                time.sleep(2*KEEP_ALIVE)

                ''' If a synthesis got received in between, there is no more thing to do '''
                if synthesis:
                    sys.stderr.write("Received synthesis in between, aborting our\n")
                    return

                ''' It's time to send the synthesis to the other nodes '''
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                server_list['SYNTHESIS']=True
                sock.sendto(cPickle.dumps(server_list), (MCAST_GRP, MCAST_PORT))
                sys.stderr.write("End of Discovery with %d systems!\n"%system_count)
                return
        ''' Let's wait a KEEP_ALIVE seconds before scrubbing again '''
        time.sleep(KEEP_ALIVE)

def print_result():
    global server_list
    sys.stderr.write("Synthesis result\n")
    for key in server_list:
        sys.stderr.write("Server %s -> "%key)
        for ip in server_list[key]:
            sys.stderr.write("%s "%ip)
        sys.stderr.write("\n")


def _main():
    hw = eval(open(sys.argv[1]).read(-1))

    ''' Let's start the client '''
    client = threading.Thread(target = start_client, args = tuple([hw]))
    client.start()

    ''' Let's start scrubbing the server list '''
    scrub = threading.Thread(target = scrub_timestamp)
    scrub.start()

    ''' Let's start the server side '''
    start_server()

    ''' Let's wait scrub & client completed '''
    scrub.join()
    client.join()

    print_result()

if __name__ == "__main__":
    _main()

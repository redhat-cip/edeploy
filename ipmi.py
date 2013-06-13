#!/usr/bin/env python

import commands

def ipmi_setup_user(channel,username,password):
	state, output = commands.getstatusoutput('ipmitool user set name 1 %s' % username)
	state, output = commands.getstatusoutput('ipmitool user set password 1 %s' % password)
	state, output = commands.getstatusoutput('ipmitool user priv 1 4 %d' % channel)
	state, output = commands.getstatusoutput('ipmitool user enable')
	state, output = commands.getstatusoutput('ipmitool user test 1 16 %s' % password)
	if state != 0:
		return False

def ipmi_restart_bmc():
    state, output = commands.getstatusoutput('ipmitool bmc reset cold')

def ipmi_setup_network(channel,ip,netmask,gateway,vlan_id):
    state, output = commands.getstatusoutput('ipmitool lan set %d ipsrc static' % channel)
    state, output = commands.getstatusoutput('ipmitool lan set %d ipaddr %s' % (channel, ip))
    state, output = commands.getstatusoutput('ipmitool lan set %d netmask %s' % (channel, netmask))
    state, output = commands.getstatusoutput('ipmitool lan set %d defgw %s' % (channel, gateway))
    state, output = commands.getstatusoutput('ipmitool lan set %d arp respond on' % channel)

    if vlan >= 0:
    	state, output = commands.getstatusoutput('ipmitool lan set %d vlan id %d' % (channel, vlan_id))
    else:
    	state, output = commands.getstatusoutput('ipmitool lan set %d vlan id off' % channel)

    # We need to restart the bmc to insure the setup is properly done
    ipmi_restart_bmc

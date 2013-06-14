import commands
import sys

def setup_user(channel, username, password):
	sys.stderr.write('Info: ipmi_setup_user: Setting user="%s", password="%s" on channel %s\n' % (username,password,channel))
	state, output = commands.getstatusoutput('ipmitool user set name 1 %s' % username)
	state, output = commands.getstatusoutput('ipmitool user set password 1 %s' % password)
	state, output = commands.getstatusoutput('ipmitool user priv 1 4 %s' % channel)
	state, output = commands.getstatusoutput('ipmitool user enable')
	state, output = commands.getstatusoutput('ipmitool user test 1 16 %s' % password)
	if state == 0:
    		sys.stderr.write('Info: ipmi_setup_user: Setting user successful !\n')
	else:
		sys.stderr.write('Err: ipmi_setup_user: Setting user failed !\n' )
		return False

def restart_bmc():
    sys.stderr.write('Info: Restarting IPMI BMC')
    state, output = commands.getstatusoutput('ipmitool bmc reset cold')

def setup_network(channel, ip, netmask, gateway, vlan_id=-1):
    sys.stderr.write('Info: ipmi_setup_network: Setting network ip="%s", netmask="%s", gateway="%s", vland_id="%d" on channel %s\n' % (ip,netmask,gateway,vlan_id,channel))
    state, output = commands.getstatusoutput('ipmitool lan set %s ipsrc static' % channel)
    state, output = commands.getstatusoutput('ipmitool lan set %s ipaddr %s' % (channel, ip))
    state, output = commands.getstatusoutput('ipmitool lan set %s netmask %s' % (channel, netmask))
    state, output = commands.getstatusoutput('ipmitool lan set %s defgw %s' % (channel, gateway))
    state, output = commands.getstatusoutput('ipmitool lan set %s arp respond on' % channel)

    if vlan_id >= 0:
    	state, output = commands.getstatusoutput('ipmitool lan set %s vlan id %d' % (channel, vlan_id))
    else:
    	state, output = commands.getstatusoutput('ipmitool lan set %s vlan id off' % channel)

    # We need to restart the bmc to insure the setup is properly done
    restart_bmc()

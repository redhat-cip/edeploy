import detect
import os
import subprocess
import platform
from subprocess import Popen, PIPE
import sys


def parse_lldtool(hw_lst, interface_name, lines):
    content = ""
    header = ""
    sub_header = ""
    for line in lines:
        if line.startswith('\t'):
            content = line.strip().strip('\n').strip('\t').replace("/", "_")
        else:
            header = line
            header = line.strip().strip('\n').strip('\t').replace("/", "_").replace(" TLV", "")
            content = ""
            sub_header = ""
        if header and content:
            if ":" in content:
                line = content.split(":")
                if (len(line) == 2) and (line[1] == ''):
                    sub_header = line[0].strip().strip('\n').strip('\t').replace("/", "_"). replace(" TLV:", "")
                    header = header + "/" + sub_header
                    continue
                else:
                    left = line[0].strip().strip('\n').strip('\t').replace("/", "_")
                    right = content.replace(left+":", "").strip().strip('\n').strip('\t').replace("/", "_")
                    # If we never had this sub_header for this header
                    # let's add one
                    if (left != sub_header):
                        sub_header = left
                        header = header + "/" + sub_header
                    content = right
            hw_lst.append(('lldp', interface_name, header, content))

    return hw_lst


def get_lld_status(hw_lst, interface_name):
    return parse_lldtool(hw_lst, interface_name, detect.output_lines("lldptool -t -n -i %s" % interface_name))


def parse_ethtool(hw_lst, interface_name, lines):
    content = ""
    header = ""
    sub_header = ""
    original_header = ""
    for line in lines:
        if interface_name in line:
            continue
        data = line.split(":")
        line = line.strip('\n')
        if line.startswith('\t'):
            sub_header = data[0].replace('\t', '').strip()
            header = "%s/%s" % (original_header, sub_header)
        else:
            sub_header = ""
            header = data[0]
            original_header = header

        header = header.replace('\t', '').strip()
        content = ''.join(data[1:]).replace('\t', '').strip()
        if not content:
            continue
        hw_lst.append(('network', interface_name, header, content))

    return hw_lst


def get_ethtool_status(hw_lst, interface_name):
    parse_ethtool(hw_lst, interface_name, detect.output_lines("ethtool -a %s" % interface_name))
    parse_ethtool(hw_lst, interface_name, detect.output_lines("ethtool -k %s" % interface_name))


def read_smart_field(hw, line, device, item, title):
    if item in line:
        if "temperature" in title:
            try:
                hw.append(("disk", device, "SMART/%s" % (title), line.split(item)[1].strip().split()[0]))
                hw.append(("disk", device, "SMART/%s_unit" % (title), line.split(item)[1].strip().split()[1]))
            except:
                sys.stderr.write("read_smart_field: Error while searching for %s in %s\n" % (item, line))
        else:
            value = ""
            for result in line.split(item)[1:]:
                value = "%s %s" % (value, result.strip())
            hw.append(("disk", device, "SMART/%s" % (title), value.strip()))
            return value.strip()
    return ""


def read_smart_scsi_error_log(hw, line, device_name, error_log):
    result = line.split()
    if len(result) > 7:
        hw.append(("disk", device_name, "SMART/%s_%s" % (error_log, "total_corrected_errors"), result[4].strip()))
        hw.append(("disk", device_name, "SMART/%s_%s" % (error_log, "gigabytes_processed"), result[6].strip()))
        hw.append(("disk", device_name, "SMART/%s_%s" % (error_log, "total_uncorrected_errors"), result[7].strip()))


def read_SMART_SCSI(hw, device, optional_flag="", mode=""):
    optional_string = ""
    if optional_flag:
        optional_string = " with %s" % optional_flag

    device_name = os.path.basename(device)
    if mode:
        device_name = "%s{%s}" % (device_name, optional_flag.split()[1])

    sdparm_cmd = subprocess.Popen("smartctl -a %s %s" % (device, optional_flag), shell=True, stdout=subprocess.PIPE)
    vendor = ""
    product = ""
    for line in sdparm_cmd.stdout:
        line = line.strip()
        # This disk doesn't exists or doesn't support SMART
        if "INQUIRY failed" in line:
            return

        # Behing a SCSI raid controller, we can have ATA devices
        if line.startswith("ID#"):
            return read_SMART_ata(hw, device, optional_flag, mode)

        temp = read_smart_field(hw, line, device_name, "Vendor:", "vendor")
        if temp:
            sys.stderr.write("read_smart_scsi: Found S.M.A.R.T information on %s%s\n" % (device, optional_string))
            vendor = temp
            continue

        temp = read_smart_field(hw, line, device_name, "Product:", "product")
        if temp:
            product = temp
            continue

        if line.startswith("Device does not support SMART") or ("Unavailable - device lacks SMART capability." in line):
            # Device is said no to support smart but on some RAID arrays we can bypass it
            if optional_flag == "":
                if (vendor == "DELL") and ("PERC" in product):
                    for pdisk_number in xrange(0, 24):
                        read_SMART_SCSI(hw, device, "-d megaraid,%d" % pdisk_number, "megaraid")
                if (vendor == "HP") and ("LOGICAL VOLUME" in product):
                    for pdisk_number in xrange(0, 24):
                        read_SMART_SCSI(hw, device, "-d cciss,%d" % pdisk_number, "cciss")
            return hw

        read_smart_field(hw, line, device_name, "Serial number:", "serial_number")
        read_smart_field(hw, line, device_name, "SMART Health Status:", "health")
        read_smart_field(hw, line, device_name, "Specified cycle count over device lifetime:", "specified_start_stop_cycle_count_over_lifetime")
        read_smart_field(hw, line, device_name, "Accumulated start-stop cycles:", "start_stop_cycle_count")
        read_smart_field(hw, line, device_name, "Specified load-unload count over device lifetime:", "specified_load_count_over_lifetime")
        read_smart_field(hw, line, device_name, "Accumulated load-unload cycles:", "load_count")
        read_smart_field(hw, line, device_name, "number of hours powered up =", "power_on_hours")
        read_smart_field(hw, line, device_name, "Blocks sent to initiator =", "blocks_sent")
        read_smart_field(hw, line, device_name, "Blocks received from initiator =", "blocks_received")
        read_smart_field(hw, line, device_name, "Blocks read from cache and sent to initiator =", "blocks_read_from_cache")
        read_smart_field(hw, line, device_name, "Non-medium error count:", "non_medium_errors_count")
        read_smart_field(hw, line, device_name, "Current Drive Temperature:", "current_drive_temperature")
        read_smart_field(hw, line, device_name, "Drive Trip Temperature:", "drive_trip_temperature")
        read_smart_field(hw, line, device_name, "Manufactured in ", "manufacture_date")

        for error_log in ["read", "write", "verify"]:
            if line.startswith("%s:" % error_log):
                read_smart_scsi_error_log(hw, line, device_name, error_log)
                continue


def read_SMART_ata(hw, device, optional_flag="", mode=""):
    found_ID = False
    device_name = os.path.basename(device)
    optional_string = ""
    if optional_flag:
        optional_string = " with %s" % optional_flag

    values = {}
    if mode:
        device_name = "%s{%s}" % (device_name, optional_flag.split()[1])

    sdparm_cmd = subprocess.Popen("smartctl -a %s %s" % (device, optional_flag), shell=True, stdout=subprocess.PIPE)
    for line in sdparm_cmd.stdout:
        line = line.strip()

        if read_smart_field(hw, line, device_name, "Device Model:", "device_model"):
            sys.stderr.write("read_smart_ata: Found S.M.A.R.T information on %s%s\n" % (device, optional_string))
            continue

        if read_smart_field(hw, line, device_name, "Serial Number:", "serial_number"):
            continue

        if read_smart_field(hw, line, device_name, "Firmware Version:", "firmware_version"):
            continue

        if line.startswith("ID#"):
            found_ID = True
            continue
        if found_ID is False:
            continue
        elif len(line) == 0:
            break
        try:
            fields = line.split()
            if (len(fields) < 10):
                raise
            values["id"] = fields[0]
            values["name"] = fields[1]
            values["flag"] = fields[2]
            values["value"] = fields[3]
            values["worst"] = fields[4]
            values["thresh"] = fields[5]
            values["type"] = fields[6]
            values["updated"] = fields[7]
            values["when_failed"] = fields[8]
            if values["when_failed"] == "-":
                values["when_failed"] = "NEVER"
            raw_values = fields[9:]
            raw_value = ""
            for raw in raw_values:
                raw_value = "%s %s" % (raw_value, raw)
            values["raw"] = raw_value

            for title in ["value", "worst", "thresh", "when_failed", "raw"]:
                hw.append(("disk", device_name, "SMART/%s(%s)/%s" % (values["name"], values["id"], title), values[title]))

        except:
            sys.stderr.write("read_smart: failed to read line : %s\n" % line)
            continue


def which(program):
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def read_SMART(hw, device, optional_flag=""):
    if not which("smartctl"):
        sys.stderr.write("Cannot find smartctl, exiting\n")
        return

    optional_string = ""
    if optional_flag:
        optional_string = " with %s" % optional_flag

    if (os.path.exists(device)):
        sys.stderr.write("read_smart: Reading S.M.A.R.T information on %s%s\n" % (device, optional_string))
        sdparm_cmd = subprocess.Popen("smartctl -a %s %s" % (device, optional_flag), shell=True, stdout=subprocess.PIPE)
        for line in sdparm_cmd.stdout:
            line = line.strip()
            if line.startswith("Device does not support SMART") or \
                ("Unavailable - device lacks SMART capability" in line) or \
                    line.startswith("Device supports SMART and is Enabled"):
                return read_SMART_SCSI(hw, device, optional_flag)

            if line.startswith("ID#"):
                return read_SMART_ata(hw, device, optional_flag)

        # If no ID# was found, let's retry with "-d ata"
        if optional_flag == "":
            return read_SMART(hw, device, "-d ata")

    else:
        sys.stderr.write("read_smart: no device %s\n" % device)
        return


def get_ddr_timing(hw_):
    'Report the DDR timings'
    sys.stderr.write('Reporting DDR Timings\n')
    found = False
    cmd = subprocess.Popen('ddr-timings-%s' % platform.machine(),
                           shell=True, stdout=subprocess.PIPE)
# DDR   tCL   tRCD  tRP   tRAS  tRRD  tRFC  tWR   tWTPr tRTPr tFAW  B2B
# 0 |  11    15    15    31     7   511    11    31    15    63    31

    for line in cmd.stdout:
        if 'is a Triple' in line:
            hw_.append(('memory', 'DDR', 'type', '3'))
            continue

        if 'is a Dual' in line:
            hw_.append(('memory', 'DDR', 'type', '2'))
            continue

        if 'is a Single' in line:
            hw_.append(('memory', 'DDR', 'type', '1'))
            continue

        if 'is a Zero' in line:
            hw_.append(('memory', 'DDR', 'type', '0'))
            continue

        if "DDR" in line:
            found = True
            continue

        if (found is True):
            (ddr_channel, tCL, tRCD, tRP, tRAS,
             tRRD, tRFC, tWR, tWTPr,
             tRTPr, tFAW, B2B) = line.rstrip('\n').replace('|', ' ').split()
            ddr_channel = ddr_channel.replace('#', '')
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tCL', tCL))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRCD', tRCD))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRP', tRP))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRAS', tRAS))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRRD', tRRD))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRFC', tRFC))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tWR', tWR))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tWTPr', tWTPr))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRTPr', tRTPr))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tFAW', tFAW))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'B2B', B2B))


def parse_ipmi_sdr(hrdw, output):
    for line in output:
        items = line.split("|")
        if len(items) < 3:
            continue

        if "Not Readable" in line:
            hrdw.append(('ipmi', items[0].strip(), 'value', 'Not Readable'))
            continue

        hrdw.append(('ipmi', items[0].strip(), 'value', '%s' % items[1].split()[0].strip()))
        units = ""
        for unit in items[1].split()[1:]:
            units = "%s %s" % (units, unit.strip())
        units = units.strip()
        if units:
            hrdw.append(('ipmi', items[0].strip(), 'unit', units))


def ipmi_sdr(hrdw):
    ipmi_cmd = Popen("ipmitool -I open sdr",
                     shell=True,
                     stdout=PIPE)
    parse_ipmi_sdr(hrdw, ipmi_cmd.stdout)

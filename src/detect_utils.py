import detect


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

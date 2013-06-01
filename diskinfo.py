import os
import commands

def sizeingb(size):
    return (size * 512) / (1000 * 1000 * 1000)

def disksize(name):
    s = open('/sys/block/' + name + '/size').read(-1)
    return sizeingb(long(s))

def disknames():
    return [name for name in os.listdir('/sys/block') if name[1] == 'd' and name[0] in 'shv']

def parse_hdparm_output(s):
    res = s.split(' = ')
    if len(res) != 2:
        return 0.0
    try:
        mbsec = res[1].split(' ')[-2]
        return float(mbsec)
    except (ValueError, KeyError):
        return 0.0

def diskperfs(names):
    return {name : parse_hdparm_output(commands.getoutput('hdparm -t /dev/%s' % name)) for name in names}

def disksizes(names):
    return {name : disksize(name) for name in names}

if __name__ == "__main__":
    names = disknames()
    sizes = disksizes(names)
    names = [name for name, size in sizes.items() if size > 0]
    perfs = diskperfs(names)
    for name in names:
        print '%s %d GB (%.2f MB/s)' % (name, sizes[name], perfs[name])

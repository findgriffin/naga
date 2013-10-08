#! /usr/bin/env python
""" naga.py 
This is the file that users should run when calling naga from the command
line.
"""

import optparse
import subprocess
import time
import logging

DIVIDE = 'NAGA_DIVIDE'
INFO_DEFAULT = 'load'
INFO_CHOICES = {
 'load': ['/bin/cat', '/proc/loadavg', '&&', '/bin/cat', '/proc/cpuinfo', '|',
     '/bin/grep', "'model name'", '|', 'wc', '-l'],
 'memory': ['/usr/bin/free', '-m'],
 'cpu': ['/bin/cat', '/proc/stat', '&&', '/bin/sleep', '1', '&&', '/bin/cat',
     '/proc/stat'],
 'disk':['/usr/bin/vmstat', '10', '2'],
 'network': [
    '/bin/ls', '/sys/class/net/', '&&', '/bin/echo', DIVIDE, '&&',
    '/bin/cat', '/sys/class/net/*/statistics/rx_bytes', '&&', 
    '/bin/cat', '/sys/class/net/*/statistics/tx_bytes', '&&',
    '/bin/sleep', '10', '&&',
    '/bin/cat', '/sys/class/net/*/statistics/rx_bytes', '&&', 
    '/bin/cat', '/sys/class/net/*/statistics/tx_bytes',
    ],
 'filesystem': ['/bin/df', '-P']
 }

INFO_LEVELS = {
 'load'     : [1.0, 2.0],
 'memory'   : [0.9, 0.95],
 'cpu'      : [0.8, 0.9],
 'network'  : [5, 10], # Megabytes/s
 'disk'     : [10,30], # Megabytes/s
 'filesystem': [0.7, 0.8],
        }

INFO_UNITS  = {
 'load'     : '',
 'memory'   : '%',
 'cpu'      : '%',
 'disk'     : 'MB/s',
 'network'  : 'MB/s',
 'filesystem': '%',
}

def timecheck(start_time, timeout, after, proc=None,):
    """ Check if timeout has expired, exit with unknown status if it has."""
    if time.time()-start_time > timeout:
        if proc is not None:
            proc.terminate()
        raise NagaExit(3, 'timeout after %s (%ss)' % (after, timeout))

def parse_opts():
    """ Parse the command line options given to naga."""
    desc = 'A python plugin for the Nagios monitoring system that connects \
to remote hosts via ssh.'
    epilog = """Naga supports the following information types and special \
arguments:
 INFO        SPECIAL ARGUMENTS
 load        n/a
 memory      n/a
 cpu         cpu0, cpu1... (default is total)
 disk        n/a
 network     wlan0, eth0... (default is total)
 filesystem  /, /dev/sda1... (default is /)
"""
    optparse.OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = optparse.OptionParser(description=desc, epilog=epilog)

    # optparse automatically sets up --help for us
    parser.add_option('-t', '--timeout', default='30',
        help='Set timeout (in seconds)')
    parser.add_option('-w', '--warning',
        help='Warning threshold (percentage)')
    parser.add_option('-c', '--critical',
        help='Critical threshold (percentage)')
    parser.add_option('-H', '--hostname', default='localhost',
        help='The hostname or ip of target system.')
    parser.add_option('-v', '--verbose', action='store_true',
        help='Enable verbose output.')

    parser.add_option('-b', '--binary', default='/usr/bin/ssh',
        help='Path to ssh binary on host.')
    parser.add_option('-l', '--logname',
        help='The login/username on remote host. (defaults to current user)')
    parser.add_option('-a', '--authentication',
        help='Authentication password for user at remote host')
    parser.add_option('-p', '--port',
        help='SSH port to use at remote host')
    parser.add_option('-k', '--key',
        help='SSH private key file to use.')
    parser.add_option('-i', '--information', default=INFO_DEFAULT,
            choices=list(INFO_CHOICES.keys()),
        help='Which type of information to return.')
    parser.add_option('-s', '--special',
        help='Any special arguments (specific to each information type)')
    parser.add_option('--capture',
        help='Capture output of ssh, used for testing and debugging only.')

    return parser.parse_args()

def connect(hostname, info, timeout, binary, start_time=None, **kwargs):
    """ Connect to remote machine via ssh and run relevant command."""
    if start_time == None:
        start_time = time.time()
    cmd1 = [binary]
    if 'logname' in kwargs:
        user = kwargs['logname']
    else:
        import getpass
        user = getpass.getuser()
    
    if 'key' in kwargs:
        cmd1 += ['-i', kwargs['key']]
    if 'port' in kwargs:
        hostname += str(kwargs['port'])
    cmd1.append('%s@%s' % (user, hostname))
    cmd = cmd1 + ['"'] + INFO_CHOICES[info] + ['"']
    logging.debug('about to Popen %s', ' '.join(cmd))
    proc = subprocess.Popen(' '.join(cmd), shell=True, stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE)
    while proc.poll() is None:
        timecheck(start_time, timeout, 'waiting for Popen', proc)
        sleep = min(float(timeout)/10, 1)
        logging.debug('waiting for proc.poll(), sleeping for %s seconds', 
                sleep)
        time.sleep(sleep)
    ret = proc.returncode
    out = proc.stdout.read()
    err = proc.stderr.read()
    return ret, out, err

def memory(out, **kwargs):
    """Get information about memory usage."""
    lines = out.splitlines()
    line1 = lines[1].split()
    line2 = lines[2].split()
    detail = [
            ('total' , int(line1[1])),
            ('used'  , int(line2[2])),
            ('free'  , int(line2[3])),
            ('shared', int(line1[4])),
            ('buff'  , int(line1[5])),
            ('cache' , int(line1[6])),
        ]
    level = float(detail[1][1]) / detail[0][1]
    return level, detail, ''

def load(out, **kwargs):
    """Get load information."""
    lines = out.splitlines()
    split = lines[0].split()
    cores = int(lines[1])
    desc = [
           ('load1',  split[0], '', 0, cores),
           ('load5', split[1]),
           ('load15', split[2]),
           ('running', split[3].split('/')[0]),
            ]
    return float(split[0])/cores, desc, 'x %s cores' % cores

def cpu(out, **kwargs):
    """Get cpu usage."""
    if 'special' in kwargs:
        cpu_n = kwargs['special']
    else: 
        cpu_n = ''
    if cpu_n == '': 
        offset = 0
    elif cpu_n.startswith('cpu') and cpu_n in out:
        cpu_n = cpu_n
        offset = int(cpu_n[3:])
    else:
        raise NagaExit(3, 'invalid cpu: %s' % cpu_n)
    lines  = out.splitlines()
    length = len(lines)
    if not length % 2 == 0:
        raise NagaExit(3, 'successive calls of /proc/stat were too different')
    # columns
    # user, nice, system, idle, iowait, irq, softirq
    state_t0 = lines[0+offset].split()[1:]
    state_t1 = lines[length/2+offset].split()[1:]
    diff = [sum((int(b), -int(a))) for a, b in zip(state_t0, state_t1)]
    total = sum(diff)
    ratio = [float(x)/y for x, y in zip(diff, [total]*len(diff))]
    detail = [
            ('cpu'     , (sum(ratio)-ratio[3])*100, '%'),
            ('user'    , ratio[0]*100, '%'),
            ('nice'    , ratio[1]*100, '%'),
            ('system'  , ratio[2]*100, '%'),
            ('idle'    , ratio[3]*100, '%'),
            ('iowait'  , ratio[4]*100, '%'),
            ('irq'     , ratio[5]*100, '%'),
            ('softirq' , ratio[6]*100, '%'),
        ]
    return detail[0][1]/100, detail, cpu_n

def disk(out, **kwargs):
    """ Get disk io."""
    mega = 1024*1024
    if 'block' in kwargs:
        block = kwargs['block']
    else:
        block = 4096
    lines = out.splitlines()
    mb_in  = int(lines[-1].split()[8])*block/mega
    mb_out = int(lines[-1].split()[8])*block/mega
    desc = 'in_persec=%sMB;out_persec=%sMB' % (mb_in, mb_out)
    return mb_in+mb_out, desc, ''

def filesystem(out, **kwargs):
    """ Get filesystem usage."""
    systems = {}
    last_fs = None
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 1:
            last_fs = parts[0]
            continue
        if len(parts) == 5:
            parts.insert(0, last_fs)
        # Expected output of df:
        # filesystem blocks used available use% mounted
        try: 
            systems[parts[5]] = [parts[0], int(parts[1]), int(parts[2]), 
                    int(parts[3])]
        except ValueError:
            # if we can't convert to int, skip line and carry on
            pass

    if not 'special' in kwargs:
        fsys = '/'
    else:
        fsys = kwargs['special']
    if not fsys in systems:
        raise NagaExit(3, 'could not find filesystem %s | %s' % (fsys, out))
    fs_info = systems[fsys]
    
    detail = []
    for name, info in list(systems.items()):
        if info[0].startswith('/dev/') or name == '/':
            data = [str(i) for i in [info[1], '', '', 0, info[2]]]
            detail.append(("'"+name+"'", ';'.join(data)))

    return float(fs_info[2]) / fs_info[1], detail, 'on %s' % fsys

def network(out, **kwargs):
    """ Get network usage."""
    if_default = ['eth', 'wlan', 'wwan']
    ifaces = out.split(DIVIDE)[0].split()
    data   = out.split(DIVIDE)[1].split()
    iface = None
    if 'special' in kwargs:
        if kwargs['special'] in ifaces:
            iface = kwargs['special']
        else:
            raise NagaExit(3, 'invalid interface %s' % kwargs['special'])
    else:
        for i in if_default:
            for j in ifaces:
                if j.startswith(i) and data[ifaces.index(j)] != 0:
                    iface = j
                    break
            if iface is not None:
                break
    result = [data[i:i+len(ifaces)] for i in range(0, len(data), len(ifaces))]
    rx_diff = [sum((int(b), -int(a))) for a, b in zip(result[0], result[2])]
    tx_diff = [sum((int(b), -int(a))) for a, b in zip(result[1], result[3])]
    desc = []
    for i in range(len(ifaces)):
        desc.append((ifaces[i]+'_rx', rx_diff[i]))
        desc.append((ifaces[i]+'_tx', tx_diff[i]))
    i = ifaces.index(iface)
    level = (rx_diff[i]+tx_diff[i])/1024.0/1024
    return level, desc, 'on %s' % iface

def finish(info, level, detail, extra, **kwargs):
    """ Exit with correct status and message."""
    unit = INFO_UNITS[info]
    if unit == '%':
        converted = format_num(level*100)
    else:
        converted = format_num(level)
    if 'warn' in kwargs and kwargs['warn'] is not None:
        warn = kwargs['warn']
    else:
        warn = INFO_LEVELS[info][0]
    if 'crit' in kwargs and kwargs['crit'] is not None:
        crit = kwargs['crit']
    else:
        crit = INFO_LEVELS[info][1]
    perfdata = build_perfdata(detail)
    if warn >= crit:
        raise NagaExit(1, 'warn (%s) > crit (%s) for %s' % (warn, crit,
                info), perfdata)
    if level < warn and level < crit:
        raise NagaExit(0, '%s usage is %s%s %s' % (info, converted, unit,
            extra), perfdata)
    if level >= warn and level < crit:
        raise NagaExit(1, '%s usage is high %s%s %s' % (info, converted,
                unit, extra), perfdata)
    if level >= crit:
        raise NagaExit(2, '%s usage is critical %s%s %s' % (info,
                converted, unit, extra), perfdata)
    else:
        raise NagaExit(3, 'Unknown: no conditions were met', desc=perfdata)

def build_perfdata(data):
    if type(data) == list:
        items = []
        for item in data:
            out =  '='.join([format_num(i) for i in item[:2]])
            out += ';'.join([format_num(i) for i in item[2:]])
            items.append(out)
        return ' '.join(items)
    return data

def format_num(i, sigfig=2):
    if type(i) == str:
        return i
    elif type(i) == int or type(i) == int:
        return str(i)
    elif type(i) == float:
        if i < 10**sigfig:
            return str(round(i, sigfig))
        else:
            return str(int(round(i, 0)))

def main():
    """ Called when running naga from command line."""
    start = time.time()

    required = ['information', 'hostname', 'binary', 'timeout', 'warning',
            'critical']
    opts = parse_opts()
    if opts[0].verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif opts[0].capture:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    info = opts[0].information
    tout = float(opts[0].timeout)
    try:
        warn = float(opts[0].warning)
    except TypeError:
        warn = None
    try:
        crit = float(opts[0].critical)
    except TypeError:
        crit = None
    kwargs = {}
    for key, val in list(opts[0].__dict__.items()):
        if key not in required and val is not None:
            kwargs[key] = val

    if not info in list(globals().keys()):
        raise NagaExit(3, 'Could not find processing method for %s' % info)
    logging.debug('about to connect to %s', opts[0].hostname)
    out = connect(opts[0].hostname, info, tout, opts[0].binary, 
            start, **kwargs)
    logging.debug('return of ssh command: %s', out[0])
    logging.debug('stdout of ssh command: %s', out[1])
    logging.debug('stderr of ssh command: %s', out[2])
    timecheck(start, tout, 'after running connect()')
    if not out[0] == 0:
        raise NagaExit(3, 'ssh command returncode %s' % out[0],
                'out=%s;err=%s ' % out[1:])
        
    if 'capture' in kwargs:
        capture_output(out, kwargs['capture'])

    level, detail, extra = globals()[info](out[1], **kwargs)
    timecheck(start, tout, 'after running %s()' % info)
    finish(info, level, detail, extra, warn=warn, crit=crit)

def capture_output(out, location):
    """Capture the output out (usually of ssh command) and print to file."""
    logging.info('capturing output into %s', location)
    with open(location, 'wb') as capt:
        capt.write(out[1])


class NagaExit(SystemExit):
    """Raised when we want to exit from naga."""

    prefix = {0: 'OK', 1: 'Warning', 2: 'Critical', 3: 'Unknown'}
    
    def __init__(self, status, msg, desc=None):
        self.code = status
        self.msg = msg
        self.desc = desc
        print(self.collate_output())
        super(NagaExit, self).__init__()

    def collate_output(self):
        """Produce output conforming to nagios plugin guidelines."""
        out = [self.prefix[self.code]+':', self.msg]
        if self.desc is not None:
            out.extend(['|', self.desc])
        return ' '.join(out)

if __name__ == "__main__":
    main()

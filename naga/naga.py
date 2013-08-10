#! /usr/bin/env python
""" naga.py 
This is the file that users should run when calling naga from the command
line.
"""

import optparse
import subprocess
import time

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
 'filesystem': ['/bin/df']
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
    desc = """
    A python plugin for the Nagios monitoring system that connects to remote
    hosts via ssh.  """

    parser = optparse.OptionParser(description=desc)

    # optparse automatically sets up --help for us
    parser.add_option('-t', '--timeout', default='30',
        help='Set timeout (in seconds)')
    parser.add_option('-w', '--warning',
        help='Warning threshold (percentage)')
    parser.add_option('-c', '--critical',
        help='Critical threshold (percentage)')
    parser.add_option('-H', '--hostname', default='localhost',
        help='The hostname or ip of the system to connect to.')
    parser.add_option('-v', '--verbose', action='store_true',
        help='Enable verbose output.')

    parser.add_option('-b', '--binary', default='/usr/bin/ssh',
        help='Path to ssh binary on host.')
    parser.add_option('-l', '--logname',
        help='The login/username used to connect to the remote host. \
                (defaults to current user)')
    parser.add_option('-a', '--authentication',
        help='Authentication password for user at remote host')
    parser.add_option('-p', '--port',
        help='SSH port to use at remote host')
    parser.add_option('-k', '--key',
        help='SSH private key file to use.')
    parser.add_option('-i', '--information', default=INFO_DEFAULT,
            choices=INFO_CHOICES.keys(),
        help='Which type of information to return.')
    parser.add_option('-s', '--special',
        help='Any special arguments (specific to each information type)')

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
    if 'verbose' in kwargs:
        print 'about to Popen %s' % ' '.join(cmd)
    proc = subprocess.Popen(' '.join(cmd), shell=True, stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE)
    while proc.poll() is None:
        timecheck(start_time, timeout, 'waiting for Popen', proc)
        time.sleep(float(timeout)/10)
    ret = proc.returncode
    out = proc.stdout.read()
    err = proc.stderr.read()
    return ret, out, err

def memory(ret, out, err, **kwargs):
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
    return level, detail

def load(ret, out, err, **kwargs):
    """Get load information."""
    lines = out.splitlines()
    split = lines[0].split()
    cores = int(lines[1])
    desc = [
           ('5min',  split[0]),
           ('10min', split[1]),
           ('15min', split[2]),
           ('running', split[3].split('/')[0]),
           ('procs', split[3].split('/')[1]),
           ('last', split[4]),
           ('cores', cores),
            ]
    return float(split[0])/cores, desc, ''

def cpu(ret, out, err, **kwargs):
    """Get cpu usage."""
    lines  = out.splitlines()
    length = len(lines)
    if not length % 2 == 0:
        raise NagaExit(3, 'successive calls of /proc/stat were too different')
    # columns
    # user, nice, system, idle, iowait, irq, softirq
    state = [lines[0].split()[1:], lines[length/2].split()[1:]]
    diff = [sum((int(b), -int(a))) for a, b in zip(*state)]
    total   = sum(diff)
    detail = [
            ('user'    , diff[0]),
            ('nice'    , diff[1]),
            ('system'  , diff[2]),
            ('idle'    , diff[3]),
            ('iowait'  , diff[4]),
            ('irq'     , diff[5]),
            ('softirq' , diff[6]),
        ]
    level = float(total - detail[3][1]) / total
    return level, detail, ''

def disk(ret, out, err, start=None, **kwargs):
    """ Get disk io."""
    mega = 1024*1024
    if 'block' in kwargs:
        block = kwargs['block']
    else:
        block = 4096
    lines = out.splitlines()
    mb_in  = int(lines[-1].split()[8])*block/mega
    mb_out = int(lines[-1].split()[8])*block/mega
    desc = 'mb_in=%s;mb_out=%s' % (mb_in, mb_out)
    return mb_in+mb_out, desc, ''

def filesystem(ret, out, err, **kwargs):
    """ Get filesystem usage."""
    systems = {}
    for line in out.splitlines()[1:]:
        parts = line.split()
        # filesystem blocks used available use% mounted
        systems[parts[5]] = [parts[0], int(parts[1]), int(parts[2]), 
                int(parts[3])]
    if not filesystem in kwargs:
        fsys = '/'
    else:
        fsys = kwargs['fsys']
    if not fsys in systems:
        print 'Unknown: could not find filesystem %s | %s' % (fsys, out)
        exit(3)
    fs_info = systems[fsys]
    
    detail = []
    for name, info in systems.items():
        if info[0].startswith('/dev/') or name == '/':
            data = ';'.join([str(i) for i in info[:3]])
            detail.append((name, data))

    return float(fs_info[2]) / fs_info[1], detail, 'on %s' % fsys

def network(ret, out, err, **kwargs):
    """ Get network usage."""
    ifaces = out.split(DIVIDE)[0].split()
    data   = out.split(DIVIDE)[1].split()
    n = len(ifaces)
    result = [data[i:i+n] for i in xrange(0, len(data), n)]
    
    raise NotImplementedError

def finish(info, level, detail, extra, **kwargs):
    """ Exit with correct status and message."""
    unit = INFO_UNITS[info]
    if unit == '%':
        converted = level*100
    else:
        converted = level
    if 'warn' in kwargs and kwargs['warn'] is not None:
        warn = kwargs['warn']
    else:
        warn = INFO_LEVELS[info][0]
    if 'crit' in kwargs and kwargs['crit'] is not None:
        crit = kwargs['crit']
    else:
        crit = INFO_LEVELS[info][1]
    if type(detail) == list:
        detail = ';'.join(['='.join((k, str(v))) for k, v in detail])
    if warn >= crit:
        raise NagaExit(1, 'warn (%s) > crit (%s) for %s' % (warn, crit,
                info), detail)
    if level < warn and level < crit:
        raise NagaExit(0, '%s usage is %.2g%s %s' % (info, converted, unit,
            extra), detail)
    if level >= warn and level < crit:
        raise NagaExit(1, '%s usage is high %.2g%s %s' % (info, converted,
                unit, extra), detail)
    if level >= crit:
        raise NagaExit(2, '%s usage is critical %.2g%s %s' % (info,
                converted, unit, extra), detail)
    else:
        raise NagaExit(3, 'Unknown: no conditions were met', desc=detail)

def main():
    """ Called when running naga from command line."""
    start = time.time()

    required = ['information', 'hostname', 'binary', 'timeout', 'warning',
            'critical']
    opts = parse_opts()
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
    for key, val in opts[0].__dict__.items():
        if key not in required and val is not None:
            kwargs[key] = val

    out = connect(opts[0].hostname, info, tout, opts[0].binary, 
            start, **kwargs)
    if not out[0] == 0:
        raise NagaExit(3, 'ssh command returncode %s' % out[0],
                'out=%s;err=%s ' % out[1:])
    timecheck(start, tout, 'setup')
    if info in globals().keys():
        level, detail, extra = globals()[info](out[0], out[1], out[2],
                start=start, timeout=tout)
        timecheck(start, tout, 'after running connect()')
        finish(info, level, detail, extra, warn=warn, crit=crit)
    else:
        raise NagaExit(3, 'Could not find processing method for %s' % info)

class NagaExit(SystemExit):

    prefix = {0: 'OK', 1: 'Warning', 2: 'Critical', 3: 'Unknown'}
    
    def __init__(self, status, msg, desc=None):
        self.status = status
        self.msg = msg
        self.desc = desc
        print self.collate_output()
        super(NagaExit, self).__init__()

    def collate_output(self):
        out = [self.prefix[self.status]+':', self.msg]
        if self.desc is not None:
            out.extend(['|', self.desc])
        return ' '.join(out)

if __name__ == "__main__":
    main()

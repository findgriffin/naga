#! /usr/bin/env python
""" naga.py 
This is the file that users should run when calling naga from the command
line.
"""

import optparse
import subprocess
import time
INFO_DEFAULT = 'load'
INFO_CHOICES = {
 'load': ['/bin/cat', '/proc/loadavg'],
 'uptime':['/bin/cat', '/proc/uptime'],
 'memory': ['/usr/bin/free', '-m'],
 'cpu': ['/bin/cat', '/proc/stat'],
#'network': '',
#'disk':'',
 }

def timecheck(start_time, timeout, proc=None):
    if time.time()-start_time > timeout:
        if proc is not None:
            proc.terminate()
        raise TimeoutError

def parse_opts():
    start_time = time.time()
    desc = """
    A python plugin for the Nagios monitoring system that connects to remote
    hosts via ssh.  """

    parser = optparse.OptionParser(description=desc)

    # optparse automatically sets up --help for us
    parser.add_option('-t', '--timeout', default='10',
        help='Set timeout (in seconds)')
    parser.add_option('-w', '--warning',
        help='Warning threshold (percentage)')
    parser.add_option('-c', '--critical',
        help='Critical threshold (percentage)')
    parser.add_option('-H', '--hostname', default='localhost',
        help='The hostname or ip of the system to connect to.')
    parser.add_option('-v', '--verbose', action='store_true',
        help='Enable verbose output.')

    parser.add_option('-l', '--logname',
        help='The login/username used to connect to the remote host')
    parser.add_option('-a', '--authentication',
        help='Authentication password for user at remote host')
    parser.add_option('-p', '--port',
        help='SSH port to use at remote host')
    parser.add_option('-k', '--key',
        help='SSH private key file to use.')
    parser.add_option('-i', '--information', default=INFO_DEFAULT,
            choices=INFO_CHOICES.keys(),
        help='Which type of information to return.')

    return parser.parse_args()

def connect(hostname, info, timeout, start_time=None, **kwargs):
    if start_time == None:
        start_time = time.time()
    if 'user' in kwargs:
        user = kwargs['user']
    else:
        import getpass
        user = getpass.getuser()

    cmd1 = ['/usr/bin/ssh', '%s@%s' % (user, hostname)]
    cmd = cmd1 + INFO_CHOICES[info]
    if 'verbose' in kwargs:
        print 'about to Popen %s' % ' '.join(cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE)
    while proc.poll() is None:
        timecheck(start_time, timeout, proc)
        time.sleep(float(timeout)/10)
    ret = proc.returncode
    out = proc.stdout.read()
    err = proc.stderr.read()
    return ret, out, err

def memory(ret, out, err, start=None, **kwargs):
    raise NotImplementedError

def load(ret, out, err, start=None, **kwargs):
    warn = 0.7
    crit = 0.9
    return 0, 'no detail yet', warn, crit

def uptime(ret, out, err, start=None, **kwargs):
    raise NotImplementedError

def cpu(ret, out, err, start=None, **kwargs):
    raise NotImplementedError

def finish(level, info, detail, warn, crit):
    if warn >= crit:
        print 'Warning: warn (%s) > crit (%s) for %s | %s' % (warn, crit,
                info, detail)
        exit(1)
    if level < warn and level < crit:
        print 'OK: %s usage %s | %s' % (info, level, detail) 
        exit(0)
    if level > warn and level < crit:
        print 'Warning: %s usage high %s | %s' % (info, level, detail)
        exit(1)
    if level > crit:
        print 'Critical: %s usage critical %s | %s' % (info, level, detail)
        exit(2)
    else:
        print 'Unknown: no conditions were met'+detail
        exit(3)

def main():
    start = time.time()

    opts = parse_opts()
    info = opts[0].information
    host = opts[0].hostname
    try:
        warn = float(opts[0].warning)
    except TypeError:
        warn = None
    try:
        crit = float(opts[0].critical)
    except TypeError:
        crit = None
    timeout = float(opts[0].timeout)

    ret, out, err = connect(host, info, timeout, start)
    timecheck(start, timeout)
    if info in globals().keys():
        level, detail, warn, crit = globals()[info](ret, out, err, 
                start=start, timeout=timeout)
        timecheck(start, timeout)
        finish(level, info, detail, warn, crit)
    else:
        print 'Unknown: Could not find processing method for %s' % info
        exit(3)
    
if __name__ == "__main__":
    main()

class TimeoutError(LookupError):
    print 'Unknown: timeout'
    exit(3)

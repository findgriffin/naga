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

def timecheck(start_time, timeout, after, proc=None,):
    """ Check if timeout has expired, exit with unknown status if it has."""
    if time.time()-start_time > timeout:
        if proc is not None:
            proc.terminate()
        print 'Unknown: timeout after %s (%ss)' % (after, timeout)
        exit(3)

def parse_opts():
    """ Parse the command line options given to naga."""
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
    cmd = cmd1 + INFO_CHOICES[info]
    if 'verbose' in kwargs:
        print 'about to Popen %s' % ' '.join(cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE)
    while proc.poll() is None:
        timecheck(start_time, timeout, 'waiting for Popen', proc)
        time.sleep(float(timeout)/10)
    ret = proc.returncode
    out = proc.stdout.read()
    err = proc.stderr.read()
    return ret, out, err

def memory(ret, out, err, start=None, **kwargs):
    """Get information about memory usage."""
    raise NotImplementedError

def load(ret, out, err, start=None, **kwargs):
    """Get load information."""
    warn = 0.7
    crit = 0.9
    return 0, 'no detail yet', warn, crit

def uptime(ret, out, err, start=None, **kwargs):
    """Get uptime."""
    raise NotImplementedError

def cpu(ret, out, err, start=None, **kwargs):
    """Get cpu usage."""
    raise NotImplementedError

def finish(level, info, detail, warn, crit):
    """ Exit with correct status and message."""
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
    """ Called when running naga from command line."""
    start = time.time()

    opts = parse_opts()
    info = opts[0].information
    host = opts[0].hostname
    sshb = opts[0].binary
    tout = float(opts[0].timeout)
    try:
        warn = float(opts[0].warning)
    except TypeError:
        warn = None
    try:
        crit = float(opts[0].critical)
    except TypeError:
        crit = None
    

    ret, out, err = connect(host, info, tout, sshb, start)
    timecheck(start, tout, 'setup')
    if info in globals().keys():
        level, detail, warn, crit = globals()[info](ret, out, err, 
                start=start, timeout=tout)
        timecheck(start, tout, 'after running connect()')
        finish(level, info, detail, warn, crit)
    else:
        print 'Unknown: Could not find processing method for %s' % info
        exit(3)
    
if __name__ == "__main__":
    main()

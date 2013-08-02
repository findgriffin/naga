""" naga.py 

"""

import optparse

desc = """
A python plugin for the Nagios monitoring system that connects to remote hosts
via ssh.  """

parser = optparse.OptionParser(description=desc)

# optparse automatically sets up --help for us
parser.add_option('-t', '--timeout',
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

options = parser.parse_args()

print options

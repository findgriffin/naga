naga
====

A python plugin for the Nagios monitoring system that connects to remote hosts
via ssh. 

Naga has some key requirements:
 * NO dependencies on the remote host (only use system commands/files).
 * Few dependencies on the local host i.e. nagios server.
 * Work on python 2.6+ (because that is the RedHat 6 default)
 * Conform to Nagios [plugin gudelines](http://nagiosplug.sourceforge.net/developer-guidelines.html).

Naga can collect the following kinds of information:
 * load (niy)
 * uptime (niy)
 * memory usage (niy)
 * cpu (niy)
 * network (niy)
 * disk (niy)

(niy) = not implemented yet

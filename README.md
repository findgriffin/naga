naga
====

A python plugin for the Nagios monitoring system that connects to remote hosts
via ssh. 

Naga has some key requirements:
 * NO dependencies on the remote host (only use system commands/files).
 * Few dependencies on the local host i.e. nagios server.
 * Work on python 2.6+ (because that is the default for RedHat 6)
 * Conform to Nagios [plugin gudelines][pgl].

Naga can collect the following kinds of information:
 * load 
 * memory usage 
 * cpu (usage)
 * disk (io)
 * filesystem (usage)

The following further information types are planned:
 * network (io)

[pgl]: http://nagiosplug.sourceforge.net/developer-guidelines.html


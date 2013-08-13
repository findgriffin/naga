# naga

A python plugin for the Nagios monitoring system that connects to remote hosts
via ssh. 

The key requirements of naga are:
 * NO dependencies on the remote host (only use system commands/files).
 * Few dependencies on the local host i.e. nagios server. (only python 2.6+)
 * Conform to Nagios [plugin gudelines][pgl].

Naga can collect the following kinds of information:
 * load 
 * memory (used/free space)
 * cpu
 * disk (io)
 * filesystem (used/free space)
 * network (io)


Obviously since naga connects to remote machines via ssh it will not be
suitable for monitoring large numbers of machines. The intended use cases for
naga are for when you can't or don't want to install any special software on
the remote machine.


### Installation


To install copy naga.py to /usr/lib/nagios/plugins/ or wherever you have your
nagios plugins installed. You then need to define a command in your nagios
config. One example follows:

    define command {
        command_name naga_check_host
        command_line /usr/lib/nagios/plugins/naga -H $HOSTNAME$ -i $SERVICEDESC$ 
        }

Then you can define a service like so:

    define service {
        hostgroup_name          ssh-servers
        service_description     load
        check_sommand           naga_check_host
        use                     generic-service
        }


### Testing

As of 13 Aug 2013 Naga has been tested on Ubuntu 12.04, 13.04 and RedHat 6.4. A
small python test suite (using unittest/nose) is also provided. Your mileage
may vary on other operating systems. The goal was to use system commands and
files that will always be available, so please log bugs/issues if that is not
the case.

To run the tests install nose, then cd to project directory and run:

   nosetests  

If the ssh command returns some output that naga cannot process then you can
add the argument `--capture=test/static/filename.txt` to capture the output for
further debugging. If you're really adventurous you can write a regression test
in `test/testnaga.py` using the captured output.

[pgl]: http://nagiosplug.sourceforge.net/developer-guidelines.html

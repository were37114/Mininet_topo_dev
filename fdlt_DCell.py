#!/usr/bin/python

"CS244 Assignment 2: Buffer Sizing"

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Link, Intf, TCLink
from mininet.topo import Topo
from mininet.util import dumpNodeConnections
import logging
import os
import subprocess
from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
import termcolor as T
from argparse import ArgumentParser
import sys
from util.monitor import monitor_qlen
from util.helper import stdev


logging.basicConfig(filename='./DCell.log', level=logging.INFO)
logger = logging.getLogger(__name__)


def cprint(s, color, cr=True):
    """Print in color
       s: string to print
       color: color to use"""
    if cr:
        print T.colored(s, color)
    else:
        print T.colored(s, color),


# Parse arguments

parser = ArgumentParser(description="Buffer sizing tests")
parser.add_argument('--levels',
                    '-l',
                    dest="levels",
                    type=int,
                    action="store",
                    help="Number of DCell levels",
                    required=True)

parser.add_argument('-n',
                    dest="n",
                    action="store",
                    type=int,
                    help="Number of servers in a level 0 DCell",
                    required=True)
# Expt parameters
args = parser.parse_args()

lg.setLogLevel('info')

# Topology to be instantiated in Mininet
class DCellTopo(Topo):
    "Star topology for Buffer Sizing experiment"

    def __init__(self, n=3, levels=2):
        # Add default members to class.
        super(DCellTopo, self ).__init__()
        self.n = n
        self.levels = levels
        self.create_topology()

    def create_topology(self):
        self.build_d_cells(0, self.levels, [])
        print "created topology"

    def build_d_cells(self, suffix, level, hosts):
        #Part I:
        if level is 0:
            master = self.addSwitch('master-%s' % (21 + suffix / self.n))
            print "added master switch 'master-%s'" % (21 + suffix / self.n)
            for i in range(self.n):
                mac_addr = "00:00:00:00:00:"
                if suffix+i+1 < 10:
                    mac_addr += "0%s" % (suffix+i+1)
                else:
                    mac_addr += "%s" % (suffix+i+1)

                print mac_addr
                
                host = self.addHost('h-%s' % (suffix + i + 1), mac = mac_addr)
                print "added host 'h-%s'" % (suffix + i + 1)
                
                switch = self.addSwitch('s-%s' % (suffix + i + 1))
                print "added switch 's-%s'" % (suffix + i + 1)
                
                hosts.append(switch) #TODO change this to switches not hosts?

                self.addLink(host, switch, bw=1000)
                self.addLink(switch, master, bw=1000)
            return

        #Part II:
        for i in range(self.calc_g(level)):
            self.build_d_cells(suffix+i*self.calc_t(level-1), level-1, hosts)
            
        #Part III:
        for i in range(self.calc_t(level-1)):
            for j in range(i+1, self.calc_g(level)):
                #calculate uid
                uid1 = self.calc_uid(level, i, j-1)
                uid2 = self.calc_uid(level, j, i)
                #add link between hosts
                self.addLink(hosts[uid1], hosts[uid2], bw=1000)

    def calc_uid(self, level, i, j):
        return i * self.calc_t(level-1) + j

    def calc_g(self, level):
        if level is 0:
            return 1
        return self.calc_t(level-1)+1
    
    def calc_t(self, level):
        if level is 0:
            return self.n
        return self.calc_g(level) * self.calc_t(level-1);



def main():
    topo = DCellTopo(n=args.n, levels=args.levels)
    CONTROLLER_IP = "192.168.56.104"
    CONTROLLER_PORT = 6653
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=None)
    net.addController(
        'controller', controller=RemoteController,
        ip=CONTROLLER_IP, port=CONTROLLER_PORT)
    net.start()
    
    dumpNodeConnections(net.hosts)
'''
    print "SLEEPING 3 SEC"
    sleep(3)
    print "DONE SLEEPING"
'''
    h1 = net.getNodeByName("h-1")
    h2 = net.getNodeByName("h-2")
    h5 = net.getNodeByName("h-5")
    h20 = net.getNodeByName("h-20")
    '''
    print h1.cmd('ping -c1', h2.IP())
    print h1.cmd('ping -c1', h5.IP())
    print h1.cmd('ping -c1', h20.IP())
    
    net.pingAll()
    
    net.iperf(hosts=(h1,h2))
    net.iperf(hosts=(h1,h5))
    net.iperf(hosts=(h1,h20))
    
    net.stop()
'''

if __name__ == '__main__':
    try:
        main()
    except:
        print "-"*80
        print "Caught exception.  Cleaning up..."
        print "-"*80
        import traceback
        traceback.print_exc()
        os.system("killall -9 top bwm-ng tcpdump cat mnexec iperf; mn -c")


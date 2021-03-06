import os

from mininet.log import setLogLevel, info #, error
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.cli import CLI
import time

from debug_utils import *
from net_utils import *

class MyTopo(Topo):
	def __init__(self):
		Topo.__init__(self)

		m0 = self.addHost('m0')
		w0 = self.addHost('w0')
		w1 = self.addHost('w1')
		d = self.addHost('d')
		c0 = self.addHost('c0')
		c1 = self.addHost('c1')

		sw0 = self.addSwitch('sw0')

		cluster_link_opts = dict(bw=1000, delay='0.1ms', loss=0, max_queue_size=1000, use_htb=True)
		edge_link_opts = dict(bw=1000, delay='1ms', loss=0, max_queue_size=1000, use_htb=True)
		self.addLink(m0, sw0, **cluster_link_opts)
		self.addLink(w0, sw0, **cluster_link_opts)
		self.addLink(w1, sw0, **cluster_link_opts)
		self.addLink(d, sw0, **cluster_link_opts)
		self.addLink(c0, sw0, **edge_link_opts)
		self.addLink(c1, sw0, **edge_link_opts)

if __name__ == '__main__':
	setLogLevel('info')
	net = Mininet(topo=MyTopo(), link=TCLink, controller=OVSController)

	m0 = net.getNodeByName('m0')
	m0.setIP(ip='10.0.0.0', prefixLen=32)
	m0.setMAC(mac='00:00:00:00:00:00')

	w0, w1 = net.getNodeByName('w0', 'w1')
	w0.setIP(ip='10.0.1.0', prefixLen=32)
	w1.setIP(ip='10.0.1.1', prefixLen=32)
	w0.setMAC(mac='00:00:00:00:01:00')
	w1.setMAC(mac='00:00:00:00:01:01')

	d = net.getNodeByName('d')
	d.setIP(ip='10.0.3.0', prefixLen=32)
	d.setMAC(mac='00:00:00:00:03:00')

	c0, c1 = net.getNodeByName('c0', 'c1')
	c0.setIP(ip='10.0.2.0', prefixLen=32)
	c1.setIP(ip='10.0.2.1', prefixLen=32)
	c0.setMAC(mac='00:00:00:00:02:00')
	c1.setMAC(mac='00:00:00:00:02:01')

	## To fix "network is unreachable"
	m0.setDefaultRoute(intf='m0-eth0')
	w0.setDefaultRoute(intf='w0-eth0')
	w1.setDefaultRoute(intf='w1-eth0')
	d.setDefaultRoute(intf='d-eth0')
	c0.setDefaultRoute(intf='c0-eth0')
	c1.setDefaultRoute(intf='c1-eth0')

	net.start()
	run_dashboard_server(d)
	run_workers([w0, w1])
	run_masters([m0])
	CLI(net)
	pkill()
	net.stop()

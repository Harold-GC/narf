#!/usr/bin/env python
#
# Copyright (c) 2021 Nutanix Inc. All rights reserved.
#
# Author: harold.gutierrez@nutanix.com
#
# Report cluster activity from arithmos

from __future__ import division

import sys
sys.path.insert(0, '/usr/local/nutanix/bin/')

import env

import datetime


from stats.arithmos import stats_util
from util.interfaces.interfaces import NutanixInterfaces
from stats.arithmos.interface.arithmos_type_pb2 import ArithmosEntityProto, VM

NODE_FIELD_NAMES=["node_name", "hypervisor_cpu_usage_ppm","hypervisor_memory_usage_ppm",
                  "num_iops", "avg_io_latency_usecs", "io_bandwidth_kBps"]

# List all the nodes in the cluster.
def arithmos_nodes():
    all_nodes = []
    
    interfaces = NutanixInterfaces()
    arithmos_client = interfaces.arithmos_client
    stats = stats_util.get_master_arithmos_entities(
	interfaces.arithmos_client, ArithmosEntityProto.kNode,
        field_names=NODE_FIELD_NAMES)	
    for node_stat in stats:
	node = {
	    "node_name": node_stat.node_name,
            "hypervisor_cpu_usage_percent": node_stat.stats.hypervisor_cpu_usage_ppm / 10000,
            "hypervisor_memory_usage_percent": node_stat.stats.hypervisor_memory_usage_ppm / 10000,
            "num_iops": node_stat.stats.common_stats.num_iops,
            "avg_io_latency_msecs": node_stat.stats.common_stats.avg_io_latency_usecs / 1000,
            "io_bandwidth_kBps": float(node_stat.stats.common_stats.io_bandwidth_kBps /1024)
	}	
	all_nodes.append(node)	
    return all_nodes

today = datetime.date.today()
time = datetime.datetime.now().strftime("%H:%M:%S")
print("{0:<13} {1:<10} {2:>6} {3:>6} {4:>6} {5:>6} {6:>6}".format(str(today), "Node","CPU%","MEM%", "IOPs", "B/W", "Lat"))
for node in arithmos_nodes():
    print("{0:<13} {n[node_name]:<10} {n[hypervisor_cpu_usage_percent]:>6.2f} {n[hypervisor_memory_usage_percent]:>6.2f} {n[num_iops]:>6} {n[io_bandwidth_kBps]:>6.2f} {n[avg_io_latency_msecs]:>6.2f}".format(str(time), n=node))


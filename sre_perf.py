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
import time
import datetime
import argparse

from stats.arithmos import stats_util
from util.interfaces.interfaces import NutanixInterfaces
from stats.arithmos.interface.arithmos_type_pb2 import ArithmosEntityProto, VM

class NodeReporter():
  """Reports for Nodes"""

  def __init__(self):
    self.NODE_FIELD_NAMES=["node_name", "hypervisor_cpu_usage_ppm","hypervisor_memory_usage_ppm",
                  "num_iops", "avg_io_latency_usecs", "io_bandwidth_kBps"]

  def _overal_live_report(self):
    all_nodes = []
    
    interfaces = NutanixInterfaces()
    arithmos_client = interfaces.arithmos_client
    stats = stats_util.get_master_arithmos_entities(
      interfaces.arithmos_client, ArithmosEntityProto.kNode,
      field_names=self.NODE_FIELD_NAMES)	
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

  def print_overal_live_report(self, sec, count):
    i = 0
    while i < count:
      i += 1
      today = datetime.date.today()
      time_now = datetime.datetime.now().strftime("%H:%M:%S")
      print("{0:<13} {1:<10} {2:>6} {3:>6} {4:>6} {5:>6} {6:>6}".format(str(today), "Node","CPU%","MEM%", "IOPs", "B/W", "LAT"))
      for node in self._overal_live_report():
        print("{0:<13} {n[node_name]:<10} {n[hypervisor_cpu_usage_percent]:>6.2f} {n[hypervisor_memory_usage_percent]:>6.2f} {n[num_iops]:>6} {n[io_bandwidth_kBps]:>6.2f} {n[avg_io_latency_msecs]:>6.2f}".format(str(time_now), n=node))
      print("")
      time.sleep(sec)



if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Report cluster activity from arithmos",
    epilog='"When you eliminate the impossible, whatever remains, however improbable, must be the truth." Spock.'
  )
  parser.add_argument('--nodes', '-n', action='store_true', help="Overal nodes activity report")
  parser.add_argument('sec', type=int, nargs="?", default=0, help="Interval in seconds")
  parser.add_argument('count', type=int, nargs="?", default=1000, help="Number of iterations")
  args = parser.parse_args()
  #print(args)

  if args.nodes:
    node_reporter = NodeReporter()
    node_reporter.print_overal_live_report(args.sec, args.count)

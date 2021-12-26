#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: harold.gutierrez@nutanix.com
#
# Report cluster activity from arithmos
#

from __future__ import division

import sys
sys.path.insert(0, '/usr/local/nutanix/bin/')

import signal, os
import env
import time
import datetime
import argparse
import curses

from stats.arithmos import stats_util
from util.interfaces.interfaces import NutanixInterfaces
from stats.arithmos.interface.arithmos_type_pb2 import *
from stats.arithmos.interface.arithmos_interface_pb2 import (
  AgentGetEntitiesArg, MasterGetEntitiesArg)
from serviceability.interface.analytics.arithmos_rpc_client import (
  ArithmosDataProcessing)


class Reporter(object):
  """Reporter base """

  def __init__(self):
    self.interfaces = NutanixInterfaces()
    self.arithmos_interface = ArithmosDataProcessing()
    self.arithmos_client = self.interfaces.arithmos_client
    self.FIELD_NAMES=[]
    
  def _get_live_stats(self, entity_type, sort_criteria=None,
                      filter_criteria=None, search_term=None,
                      field_name_list=None):
    arithmos_interface = ArithmosDataProcessing()
    ret = arithmos_interface.MasterGetEntitiesStats(
      entity_type, sort_criteria, filter_criteria, search_term,
      requested_field_name_list=field_name_list)
    if ret:
      response = ret.response
      if response.error == ArithmosErrorProto.kNoError:
        return response

  def _get_generic_stats_dict(self, generic_stat_list):
    """
    Transform generic_stat_list returned from arithmos into a dictionary.
    Arithmos returns generic_stats in the form of:

      generic_stat_list {
        stat_name: "memory_usage_ppm"
        stat_value: 23030
      }

    This functions transform this into:
       { "memory_usage_ppm": 23030 }

    Making it easy to handle by reporters and Ui.
    """
    ret = {}
    for generic_stat in generic_stat_list:
      ret[generic_stat.stat_name] = generic_stat.stat_value
    return ret

  
class NodeReporter(Reporter):
  """Reports for Nodes"""

  def __init__(self):
    Reporter.__init__(self)
    self._ARITHMOS_ENTITY_PROTO = ArithmosEntityProto.kNode    
    self.max_node_name_width = 0
    self.sort_conversion = {
      "name": "node_name",
      "cpu": "-hypervisor_cpu_usage_ppm",
      "mem": "-hypervisor_memory_usage_ppm",
      "iops": "-num_iops",
      "bw": "-io_bandwidth_kBps",
      "lat" : "-avg_io_latency_usecs"
    }
    
  def _get_node_live_stats(self, sort_criteria=None, filter_criteria=None,
                           search_term=None, field_name_list=None):
    response = self._get_live_stats(self._ARITHMOS_ENTITY_PROTO,
                                    sort_criteria, filter_criteria,
                                    search_term, field_name_list)
    entity_list = response.entity_list.node
    return entity_list
    
  def overal_live_report(self, sort="name"):
    field_names=["node_name", "hypervisor_cpu_usage_ppm",
                 "hypervisor_memory_usage_ppm","num_iops",
                 "avg_io_latency_usecs", "io_bandwidth_kBps"]

    sort_by = self.sort_conversion[sort]
    all_nodes = []
    stats = self._get_node_live_stats(field_name_list=field_names,
                                      sort_criteria=sort_by)
    for node_stat in stats:
      node = {
	"node_name": node_stat.node_name,
        "hypervisor_cpu_usage_percent":
          node_stat.stats.hypervisor_cpu_usage_ppm / 10000,
        "hypervisor_memory_usage_percent":
          node_stat.stats.hypervisor_memory_usage_ppm / 10000,
        "num_iops":
          node_stat.stats.common_stats.num_iops,
        "avg_io_latency_msecs":
          node_stat.stats.common_stats.avg_io_latency_usecs / 1000,
        "io_bandwidth_kBps":
          float(node_stat.stats.common_stats.io_bandwidth_kBps /1024)
      }

      # Set value to slice node name. Max is 30 character. This is used for
      # displaying the information
      if len(node["node_name"]) > 30:
        self.max_node_name_width = 30
        node["node_name"] = node["node_name"][:30]            
      elif len(node["node_name"]) > self.max_node_name_width:
        self.max_node_name_width = len(node["node_name"])
      all_nodes.append(node)
    return all_nodes


class VmReporter(Reporter):
  """Reports for UVMs"""

  def __init__(self):
    Reporter.__init__(self)
    self.ARITHMOS_ENTITY_PROTO = ArithmosEntityProto.kVM
    self.max_vm_name_width = 0
    self.sort_conversion = {
      "name": "vm_name",
      "cpu": "-hypervisor_cpu_usage_ppm",
      "mem": "-memory_usage_ppm",
      "iops": "-controller_num_iops",
      "bw": "-controller_io_bandwidth_kBps",
      "lat" : "-controller_avg_io_latency_usecs"
    }

  def _get_vm_live_stats(self, sort_criteria=None, filter_criteria=None,
                           search_term=None, field_name_list=None):
    response = self._get_live_stats(self.ARITHMOS_ENTITY_PROTO,
                                    sort_criteria, filter_criteria,
                                    search_term, field_name_list)
    entity_list = response.entity_list.vm
    return entity_list

    
  def overal_live_report(self, sort="name"):
    field_names=["vm_name", "hypervisor_cpu_usage_ppm", "memory_usage_ppm",
                 "controller_num_iops", "controller_io_bandwidth_kBps",
                 "controller_avg_io_latency_usecs"]

    sort_by = self.sort_conversion[sort]
    all_vms = []
    stats = self._get_vm_live_stats(field_name_list=field_names,
                                    sort_criteria=sort_by)
    for vm_stat in stats:

      generic_stats = self._get_generic_stats_dict(
        vm_stat.stats.generic_stat_list)
      # For VMs without memory_usage_ppm assign 0 instead
      if "memory_usage_ppm" not in generic_stats:
        generic_stats[u"memory_usage_ppm"] = 0
        
      vm = {
	"vm_name": vm_stat.vm_name,
        "hypervisor_cpu_usage_percent":
          vm_stat.stats.hypervisor_cpu_usage_ppm / 10000,
        "memory_usage_percent":
          generic_stats["memory_usage_ppm"] /10000,
        "controller_num_iops":
          vm_stat.stats.common_stats.controller_num_iops,
        "controller_io_bandwidth_kBps":
          vm_stat.stats.common_stats.controller_io_bandwidth_kBps /1024,
        "controller_avg_io_latency_msecs":
          vm_stat.stats.common_stats.controller_avg_io_latency_usecs / 1000
      }

      # Set value to slice vm name. Max is 30 character. This is used for
      # displaying the information
      if len(vm["vm_name"]) > 30:
        self.max_vm_name_width = 30
        vm["vm_name"] = vm["vm_name"][:30]            
      elif len(vm["vm_name"]) > self.max_vm_name_width:
        self.max_vm_name_width = len(vm["vm_name"])
      
      all_vms.append(vm)	
    return all_vms
      
  
class Ui(object):
  """Display base"""

  def __init__(self):
    self.node_reporter = NodeReporter()
    self.vm_reporter = VmReporter()
    
class UiCli(Ui):
  """CLI interface"""

  def nodes_overal_live_report(self, sec, count, sort="name"):
    i = 0
    while i < count:
      i += 1
      today = datetime.date.today()
      time_now = datetime.datetime.now().strftime("%H:%M:%S")
      nodes = self.node_reporter.overal_live_report(sort)
      print("{time:<11} {node:<{width}} {cpu:>6} {mem:>6} {iops:>6} {bw:>6} "
            "{lat:>6}".format(
              time=str(today),
              node="Node",
              cpu="CPU%",
              mem="MEM%",
              iops="IOPs",
              bw = "B/W",
              lat="LAT",
              width=self.node_reporter.max_node_name_width
      ))
      for node in nodes:
        print("{time:<11} "
              "{n[node_name]:<{width}} "
              "{n[hypervisor_cpu_usage_percent]:>6.2f} "
              "{n[hypervisor_memory_usage_percent]:>6.2f} "
              "{n[num_iops]:>6} "
              "{n[io_bandwidth_kBps]:>6.2f} "
              "{n[avg_io_latency_msecs]:>6.2f} "
              .format(time=str(time_now),
                      n=node,
                      width=self.node_reporter.max_node_name_width))
      print("")
      time.sleep(sec)

  def uvms_overal_live_report(self, sec, count, sort="name"):
    i = 0
    while i < count:
      i += 1
      today = datetime.date.today()
      time_now = datetime.datetime.now().strftime("%H:%M:%S")
      vms = self.vm_reporter.overal_live_report(sort)
      print("{time:<11} {vm:<{width}} {cpu:>6} {mem:>6} {iops:>6} {bw:>6} "
            "{lat:>6}".format(
              time=str(today),
              vm="VM Name",
              cpu="CPU%",
              mem="MEM%",
              iops="IOPs",
              bw = "B/W",
              lat="LAT",
              width=self.vm_reporter.max_vm_name_width
      ))
      for vm in vms:
        print("{0:<11} {v[vm_name]:<{width}} "
              "{v[hypervisor_cpu_usage_percent]:>6.2f} "
              "{v[memory_usage_percent]:>6.2f} "
              "{v[controller_num_iops]:>6} "
              "{v[controller_io_bandwidth_kBps]:>6.2f} "
              "{v[controller_avg_io_latency_msecs]:>6.2f} "
              .format(str(time_now),
                      v=vm,
                      width=self.vm_reporter.max_vm_name_width))
      print("")
      time.sleep(sec)
      
      
class UiInteractive(Ui):
  """Interactive interface"""
  def __init__(self):
    Ui.__init__(self)
    self.stdscr = curses.initscr()
    self.nodes_cpu_pad = curses.newpad(
      len(self.node_reporter.overal_live_report()) + 3, 80)
    self.nodes_cpu_pad.border()

  def open_screen(self, stdscr):
    self.stdscr.clear()
    self.stdscr.nodelay(1)
    key = 0

    # Set invisible cursor
    curses.curs_set(0)
    
    # Start colors in curses
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)    
    
    while (key != ord('q')):
    #while(True):
      # Initialization
      self.stdscr.clear()
      height, width = stdscr.getmaxyx()
      
      # Declaration of strings
      title = " SRE Perf "[:width-1]

      self.stdscr.border()
        
      # Turning on attributes for title
      self.stdscr.attron(curses.color_pair(2))
      self.stdscr.attron(curses.A_BOLD)
      
      # Rendering title
      self.stdscr.addstr(0, 5, title)
      self.stdscr.addstr(0, width - 12,
                         datetime.datetime.now().strftime("%H:%M:%S"))
      
      # Turning off attributes for title
      self.stdscr.attroff(curses.color_pair(2))
      self.stdscr.attroff(curses.A_BOLD)

      self.display_nodes_cpu_pad(2,1)
      
      # Refresh the screen
      self.stdscr.noutrefresh()

      # Stage all updates
      curses.doupdate()
      
      # Wait for next input
      time.sleep(3)
      key = self.stdscr.getch()

  def display_nodes_cpu_pad(self, y, x):
    self.stdscr.noutrefresh()

    self.nodes_cpu_pad.attron(curses.A_BOLD)
    self.nodes_cpu_pad.addstr(0, 3, " Nodes CPU ")
    self.nodes_cpu_pad.attroff(curses.color_pair(2))
    self.nodes_cpu_pad.attroff(curses.A_BOLD)
    
    self.nodes_cpu_pad.addstr(1, 1, "{0:<20} {1:>5} |{2:50}"
                              .format("Name","CPU%","0%         |25%         "
                                      "|50%        |75%     100%|"))

    nodes = self.node_reporter.overal_live_report()
    for i in range(0, len(nodes)):
      node = nodes[i]
      rangex = int(0.5 * node["hypervisor_cpu_usage_percent"])
      self.nodes_cpu_pad.addstr(i + 2, 1, "{0:<20} {1:>5.2f} |{2:50}"
                                .format(node["node_name"],
                                        node["hypervisor_cpu_usage_percent"],
                                        "#" * rangex))      

    self.nodes_cpu_pad.noutrefresh(0, 0, y, x, 9, 80)


if __name__ == "__main__":
  try:
    parser = argparse.ArgumentParser(
      description="Report cluster activity",
      epilog='"When you eliminate the impossible, whatever remains,'
             'however improbable, must be the truth." Spock.'
    )
    parser.add_argument('--nodes', '-n', action='store_true',
                        help="Overal nodes activity report")
    parser.add_argument('--uvms', '-v', action='store_true',
                        help="Overal user VMs activity report")
    parser.add_argument('--sort', '-s',
                        choices=["name", "cpu","mem","iops","bw", "lat"],
                        default="name", help="Sort output")    
    parser.add_argument('--test', '-t', action='store_true',
                        help="Place holder for testing new features")    
    parser.add_argument('sec', type=int, nargs="?", default=3,
                        help="Interval in seconds")
    parser.add_argument('count', type=int, nargs="?", default=1000,
                        help="Number of iterations")
    args = parser.parse_args()
    
    if args.nodes:
      ui_cli = UiCli()
      try:
        ui_cli.nodes_overal_live_report(args.sec, args.count, args.sort)
      except KeyboardInterrupt:
        print("Goodbye")
        exit(0)
      
    elif args.uvms:
      ui_cli = UiCli()
      try:
        ui_cli.uvms_overal_live_report(args.sec, args.count, args.sort)
      except KeyboardInterrupt:
        print("Goodbye : )")
        exit(0)
      
    elif args.test:
      print("==== TESTING ====")
      #vm_reporter = VmReporter()
      #vm_reporter.test_data_processing()
      
    else:
      ui_interactive = UiInteractive()
      curses.wrapper(ui_interactive.open_screen)

  except IOError:
    # Python flushes standard streams on exit; redirect remaining output
    # to devnull to avoid another BrokenPipeError at shutdown
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    sys.exit(1)  # Python exits with error code 1 on EPIPE

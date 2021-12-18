#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Nutanix Inc. All rights reserved.
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
from stats.arithmos.interface.arithmos_type_pb2 import ArithmosEntityProto, VM

class Reporter(object):
  """Reporter base """

  def __init__(self):
    self.interfaces = NutanixInterfaces()
    self.arithmos_client = self.interfaces.arithmos_client
    self.FIELD_NAMES=[]
    
  def get_stats(self):
    return stats_util.get_master_arithmos_entities(
      self.interfaces.arithmos_client, self.ARITHMOS_ENTITY_PROTO,
      field_names=self.FIELD_NAMES)	

  
class NodeReporter(Reporter):
  """Reports for Nodes"""

  def __init__(self):
    Reporter.__init__(self)
    self.FIELD_NAMES=["node_name", "hypervisor_cpu_usage_ppm","hypervisor_memory_usage_ppm",
                  "num_iops", "avg_io_latency_usecs", "io_bandwidth_kBps"]
    self.ARITHMOS_ENTITY_PROTO = ArithmosEntityProto.kNode

  def overal_live_report(self):
    all_nodes = []
    stats = self.get_stats()
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

  
class Ui(object):
  """Display base"""

  def __init__(self):
    self.node_reporter = NodeReporter()

    
class UiCli(Ui):
  """CLI interface"""

  def print_overal_live_report(self, sec, count):
    i = 0
    while i < count:
      i += 1
      today = datetime.date.today()
      time_now = datetime.datetime.now().strftime("%H:%M:%S")
      print("{0:<13} {1:<10} {2:>6} {3:>6} {4:>6} {5:>6} {6:>6}".format(str(today), "Node","CPU%","MEM%", "IOPs", "B/W", "LAT"))
      for node in self.node_reporter.overal_live_report():
        print("{0:<13} {n[node_name]:<10} {n[hypervisor_cpu_usage_percent]:>6.2f} {n[hypervisor_memory_usage_percent]:>6.2f} {n[num_iops]:>6} {n[io_bandwidth_kBps]:>6.2f} {n[avg_io_latency_msecs]:>6.2f}".format(str(time_now), n=node))
      print("")
      time.sleep(sec)

      
class UiInteractive(Ui):
  """Interactive interface"""
  def __init__(self):
    Ui.__init__(self)
    self.stdscr = curses.initscr()
    self.nodes_cpu_pad = curses.newpad(len(self.node_reporter.overal_live_report()) + 3, 80)
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
      self.stdscr.addstr(0, width - 12, datetime.datetime.now().strftime("%H:%M:%S"))
      
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
    
    self.nodes_cpu_pad.addstr(1, 1, "{0:<20} {1:>5} |{2:50}".format("Name","CPU%","0%         |25%         |50%        |75%     100%|"))

    nodes = self.node_reporter.overal_live_report()
    for i in range(0, len(nodes)):
      node = nodes[i]
      rangex = int(0.5 * node["hypervisor_cpu_usage_percent"])
      self.nodes_cpu_pad.addstr(i + 2, 1, "{0:<20} {1:>5.2f} |{2:50}".format(node["node_name"],
                                                                          node["hypervisor_cpu_usage_percent"],
                                                                          "#" * rangex))      

    self.nodes_cpu_pad.noutrefresh(0, 0, y, x, 9, 80)

    
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Report cluster activity from arithmos",
    epilog='"When you eliminate the impossible, whatever remains, however improbable, must be the truth." Spock.'
  )
  parser.add_argument('--nodes', '-n', action='store_true', help="Overal nodes activity report")
  parser.add_argument('sec', type=int, nargs="?", default=3, help="Interval in seconds")
  parser.add_argument('count', type=int, nargs="?", default=1000, help="Number of iterations")
  args = parser.parse_args()
#  print(args)

  if args.nodes:
    ui_cli = UiCli()
    try:
      ui_cli.print_overal_live_report(args.sec, args.count)
    except KeyboardInterrupt:
      print("Goodbye")
      exit(0)
      
  else:
    ui_interactive = UiInteractive()
    curses.wrapper(ui_interactive.open_screen)


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

#from stats.arithmos import stats_util
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
    ret = self.arithmos_interface.MasterGetEntitiesStats(
      entity_type, sort_criteria, filter_criteria, search_term,
      requested_field_name_list=field_name_list)
    if ret:
      response = ret.response
      if response.error == ArithmosErrorProto.kNoError:
        return response

  def _get_time_range_stat_values(self, entity_id, stat,
                                  start, end, sampling_interval):
    resp = self.arithmos_interface.MasterGetTimeRangeStats(entity_id,
                                    self._ARITHMOS_ENTITY_PROTO, stat,
                                    start, end,
                                    sampling_interval)
    if resp:
      for res in resp.response_list:
        if res.error == ArithmosErrorProto.kNoError:
          return res.time_range_stat.value_list

  def _get_time_range_stat_average(self, entity_id, stat,
                                   start, end, sampling_interval=30):
    values = self._get_time_range_stat_values(entity_id, stat,
                                              start, end,
                                              sampling_interval)
    if values:
      counter = 0
      sum = 0
      for value in values:
        if value > 0:
          counter += 1
          sum += value
      if sum > 0:
        return sum / counter
    return -1
      
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

  def _zeroed_missing_stats(self, stats, desired_stat_list):
    """
    If an entity is missing an stat in the returned data from arithmos
    then it's necessary to fill the missing information to fill the
    fields when it's displayed by the Ui.

    This function takes an actual list of stats and a list of desired
    stats. If a stat in the desired list is missing from the stat list
    then it add it with a value of 0 and returns a new list.

    TODO: There may be a better way to do this. 
          Review if this is valid.
    """
    for desired_stat in desired_stat_list:
      if desired_stat not in stats:
        stats[desired_stat] = 0
    return stats

  
class NodeReporter(Reporter):
  """Reports for Nodes"""

  def __init__(self):
    Reporter.__init__(self)
    self._ARITHMOS_ENTITY_PROTO = ArithmosEntityProto.kNode    
    self.max_node_name_width = 0

    # TODO: Get rid of sort_arithmos_conversion in favor of sort_conversion
    #       and lambda sorting.
    self.sort_arithmos_conversion = {
      "name": "node_name",
      "cpu": "-hypervisor_cpu_usage_ppm",
      "mem": "-hypervisor_memory_usage_ppm",
      "iops": "-num_iops",
      "bw": "-io_bandwidth_kBps",
      "lat" : "-avg_io_latency_usecs"
    }

    self.sort_conversion = {
      "name": "node_name",
      "cpu": "hypervisor_cpu_usage_percent",
      "mem": "hypervisor_memory_usage_percent",
      "iops": "num_iops",
      "bw": "io_bandwidth_mBps",
      "lat" : "avg_io_latency_msecs"
    }
    
    self.nodes = self._get_node_live_stats(sort_criteria="node_name",
                                           field_name_list=["node_name", "id"])
    
  def _get_node_live_stats(self, sort_criteria=None, filter_criteria=None,
                           search_term=None, field_name_list=None):
    response = self._get_live_stats(self._ARITHMOS_ENTITY_PROTO,
                                    sort_criteria, filter_criteria,
                                    search_term, field_name_list)
    entity_list = response.entity_list.node
    return entity_list
      
  def overall_live_report(self, sort="name"):
    field_names=["node_name", "hypervisor_cpu_usage_ppm",
                 "hypervisor_memory_usage_ppm","num_iops",
                 "avg_io_latency_usecs", "io_bandwidth_kBps"]

    if sort in self.sort_conversion.keys():
      sort_by = self.sort_conversion[sort]
    else:
      sort_by = self.sort_conversion["name"]

    
    filter_by= ""
    all_nodes = []
    stats = self._get_node_live_stats(field_name_list=field_names,
                                      filter_criteria=filter_by)
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
        "io_bandwidth_mBps":
          float(node_stat.stats.common_stats.io_bandwidth_kBps /1024)
      }

      # Set value to slice node name. Max is 30 character. This is used for
      # displaying the information
      # TODO: Move this to UI class.
      if len(node["node_name"]) > 30:
        self.max_node_name_width = 30
        node["node_name"] = node["node_name"][:30]            
      elif len(node["node_name"]) > self.max_node_name_width:
        self.max_node_name_width = len(node["node_name"])
      all_nodes.append(node)
    if sort_by == "node_name":
      return sorted(all_nodes, key = lambda node: node[sort_by])
    else:
      return sorted(all_nodes, key = lambda node: node[sort_by], reverse=True)

  def overall_time_range_report(self, start, end, sort="name"):
    if sort in self.sort_conversion.keys():
      sort_by = self.sort_conversion[sort]
    else:
      sort_by = self.sort_conversion["name"]

    sampling_interval=30
    all_nodes = []
    for node in self.nodes:
      node_stats = {
        "node_name": node.node_name,
        "hypervisor_cpu_usage_percent":
          self._get_time_range_stat_average(
            node.id, "hypervisor_cpu_usage_ppm", start, end,
            sampling_interval) / 10000,
        "hypervisor_memory_usage_percent":
          self._get_time_range_stat_average(
            node.id, "hypervisor_memory_usage_ppm", start, end,
            sampling_interval) / 10000,
        "num_iops":
          int(self._get_time_range_stat_average(
            node.id, "num_iops", start, end, sampling_interval)),
        "avg_io_latency_msecs":
          self._get_time_range_stat_average(
            node.id, "avg_io_latency_usecs", start, end,
            sampling_interval) / 1000,
        "io_bandwidth_mBps":
          self._get_time_range_stat_average(
            node.id, "io_bandwidth_kBps", start, end,
            sampling_interval) / 1024,
      }
      all_nodes.append(node_stats)
    if sort_by == "node_name":
      return sorted(all_nodes, key = lambda node: node[sort_by])
    else:
      return sorted(all_nodes, key = lambda node: node[sort_by], reverse=True)

class VmReporter(Reporter):
  """Reports for UVMs"""

  def __init__(self):
    Reporter.__init__(self)
    self.ARITHMOS_ENTITY_PROTO = ArithmosEntityProto.kVM
    self.max_vm_name_width = 0

    # The reason this conversion exists is because we want to abstract
    # the actual attribute names with something more human friendly 
    # and easy to remember. We also want to abstract this from the
    # UI classes.
    self.sort_arithmos_conversion = {
      "name": "vm_name",
      "cpu": "-hypervisor_cpu_usage_ppm",
      "rdy": "-hypervisor.cpu_ready_time_ppm",
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

  def overall_live_report(self, sort="name", node_names=[]):
    field_names=["vm_name",
                 "hypervisor_cpu_usage_ppm",
                 "hypervisor.cpu_ready_time_ppm",
                 "memory_usage_ppm","controller_num_iops",
                 "controller_io_bandwidth_kBps",
                 "controller_avg_io_latency_usecs"]

    sort_by = self.sort_arithmos_conversion[sort]

    filter_by= "power_state==on"
    if node_names:
      node_names_str = ",".join(["node_name==" + node_name
                                 for node_name in node_names])
      filter_by += ";" + node_names_str

    stats = self._get_vm_live_stats(field_name_list=field_names,
                                    sort_criteria=sort_by,
                                    filter_criteria=filter_by)

    all_vms = []
    for vm_stat in stats:

      # Convert stats from Arithmos generic stat format into a dictionary.
      #
      # GENERIC STAT FORMAT IS LIKE:
      # generic_stat_list {
      #   stat_name: "memory_usage_ppm"
      #   stat_value: 23030
      # }
      #
      # IT IS TRANSFORMED INTO THIS:
      #  { "memory_usage_ppm": 23030 }
      generic_stats = self._get_generic_stats_dict(
        vm_stat.stats.generic_stat_list)

      # List of stats that arithmos return in generic stats format value.
      # It's necessary to explictly know which stats Arithmos return in
      # generic stat format.
      generic_stat_names = ["memory_usage_ppm",
                            "hypervisor.cpu_ready_time_ppm"]

      # Lastly, it's necessary to fill with zeros the missing stats.
      generic_stats = self._zeroed_missing_stats(generic_stats,
                                                 generic_stat_names)

      # I don't know which other stats might be missing from the data returned
      # from Arithmos, so more workarounds like previous one may be needed
      # in the future.
      # Function _zeroed_missing_stats() should work for most cases.

      vm = {
	"vm_name": vm_stat.vm_name,
        "hypervisor_cpu_usage_percent":
          vm_stat.stats.hypervisor_cpu_usage_ppm / 10000,
        "hypervisor.cpu_ready_time_ppm":
          generic_stats["hypervisor.cpu_ready_time_ppm"] / 10000,
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

  def nodes_overall_live_report(self, sec, count, sort="name"):
    if not sec or sec < 0:
      sec = 0
      count = 1
    else:
      if not count or count < 0: count = 1000
    i = 0
    while i < count:
      time.sleep(sec)
      i += 1
      today = datetime.date.today()
      time_now = datetime.datetime.now().strftime("%H:%M:%S")
      nodes = self.node_reporter.overall_live_report(sort)
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
              "{n[io_bandwidth_mBps]:>6.2f} "
              "{n[avg_io_latency_msecs]:>6.2f} "
              .format(time=str(time_now),
                      n=node,
                      width=self.node_reporter.max_node_name_width))
      print("")

  def _nodes_time_range_report_helper(self, start_time, end_time, sort="name"):
    i = 0
    usec_start = int(start_time.strftime("%s") + "000000")
    usec_end = int(end_time.strftime("%s") + "000000")
    nodes = self.node_reporter.overall_time_range_report(
      usec_start,usec_end,sort)
    print("{time:<21} {node:<{width}} {cpu:>6} {mem:>6} {iops:>6} {bw:>6} "
          "{lat:>6}".format(
            time=start_time.strftime("%Y/%m/%d-%H:%M:%S"),
            node="Node",
            cpu="CPU%",
            mem="MEM%",
            iops="IOPs",
            bw = "B/W",
            lat="LAT",
            width=self.node_reporter.max_node_name_width))
    for node in nodes:
      print("{time:<21} "
            "{n[node_name]:<{width}} "
            "{n[hypervisor_cpu_usage_percent]:>6.2f} "
            "{n[hypervisor_memory_usage_percent]:>6.2f} "
            "{n[num_iops]:>6} "
            "{n[io_bandwidth_mBps]:>6.2f} "
            "{n[avg_io_latency_msecs]:>6.2f} "
            .format(time=start_time.strftime("%Y/%m/%d-%H:%M:%S"),
                    n=node,
                    width=self.node_reporter.max_node_name_width))
    print("")

  def nodes_time_range_report(self, start_time, end_time,
                              sec=None, sort="name"):
    if (end_time - start_time ).seconds < 30:
      print("ERROR: Invalid dates, difference between start and "
        "end is less than 30 seconds.\n"
        "       Minimum time difference for historic report is 30 seconds.")
      return False
    if not sec:
      self._nodes_time_range_report_helper(start_time, end_time, sort)
      return True
    elif sec < 30:
      print("INFO: Invalid interval, minimum value 30 seconds for "
            "historic report. \n"
            "      Setting interval to 30 seconds.")
      sec = 30
    step_time = start_time
    delta_time = start_time + datetime.timedelta(seconds=sec)
    if delta_time > end_time:
      print("INFO: Invalid interval, greater than the difference "
            "between start and end time.\n"
            "      Setting single interval between start and end.")
      self._nodes_time_range_report_helper(start_time, end_time, sort)
    else:
      while step_time < end_time:
        self._nodes_time_range_report_helper(step_time, delta_time, sort)
        step_time = delta_time
        delta_time += datetime.timedelta(seconds=sec)

  def uvms_overall_live_report(self, sec, count, sort="name", node_names=[]):
    if not sec or sec < 0:
      sec = 0
      count = 1
    else:
      if not count or count < 0: count = 1000
    i = 0
    while i < count:
      i += 1
      today = datetime.date.today()
      time_now = datetime.datetime.now().strftime("%H:%M:%S")
      vms = self.vm_reporter.overall_live_report(sort, node_names)
      print("{time:<11} {vm:<{width}} {cpu:>6} {rdy:>6} {mem:>6} {iops:>6} "
            "{bw:>6} {lat:>6}".format(
              time=str(today),
              vm="VM Name",
              cpu="CPU%",
              rdy="RDY%",
              mem="MEM%",
              iops="IOPs",
              bw = "B/W",
              lat="LAT",
              width=self.vm_reporter.max_vm_name_width
      ))
      for vm in vms:
        print("{0:<11} {v[vm_name]:<{width}} "
              "{v[hypervisor_cpu_usage_percent]:>6.2f} "
              "{v[hypervisor.cpu_ready_time_ppm]:>6.2f} "
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
    """
    TODO:
      + Find a better way to get Y for pads, the use of overall_live_report()
        is an unnecessary call to arithmos.
    """
    Ui.__init__(self)
    self.stdscr = curses.initscr()
    self.nodes_cpu_pad = curses.newpad(
      len(self.node_reporter.overall_live_report()) + 3, 80)
    self.nodes_cpu_pad.border()

    self.vm_overall_pad = curses.newpad(
      len(self.vm_reporter.overall_live_report()) + 3, 80)
    self.vm_overall_pad.border()
    
    self.initialize_colors()
    self.initialize_strings()

    self.key = 0
    self.sort = "cpu"
    self.height = 0
    self.width = 0
    
  def initialize_colors(self):
    # Color pair constants
    self.RED = 1
    self.GREEN = 2
    self.YELLOW = 3
    self.BLUE = 4
    self.MAGENTA = 5
    self.CYAN = 6
    self.WHITE_BLACK = 7
    
    # Start colors in curses
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(self.RED, curses.COLOR_RED, -1)    
    curses.init_pair(self.GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(self.YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(self.BLUE, curses.COLOR_BLUE, -1)
    curses.init_pair(self.MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(self.CYAN, curses.COLOR_CYAN, -1)    
    curses.init_pair(self.WHITE_BLACK, curses.COLOR_WHITE, curses.COLOR_BLACK)    

  def initialize_strings(self):
    """
    More strings should be initialized for this function to make sense.
    TODO: Remove if not necessary.
    """
    self.title = " NARF "

  def safe_noautorefresh(self, pad,
                         pad_min_y, pad_min_x,
                         screen_y, screen_x,
                         pad_desired_height, pad_desired_width):
    """
    It safely display a pad without going beyond window boundaries.
    Avoid to crash if window is resized.
    TODO: 
      + For the time being it assume the pad is displayed from 0, 0
        pad position. This means it will always receive pad_min_y
        and pad_min_x with 0 value. Other values may make this 
        function to crash.
    """
    main_screen_max_absolute_y = screen_y + pad_desired_height
    main_screen_max_absolute_x = screen_x + pad_desired_width

    if self.height < main_screen_max_absolute_y:
      main_screen_max_absolute_y = self.height - 2

    if self.width < main_screen_max_absolute_x:
      main_screen_max_absolute_x = self.width - 2

    pad.noutrefresh(pad_min_y, pad_min_x,
                    screen_y, screen_x,
                    main_screen_max_absolute_y, main_screen_max_absolute_x)

  def get_sort_label(self, sort_key):
    if sort_key == ord('r'): return "rdy"
    if sort_key == ord('m'): return "mem"
    if sort_key == ord('i'): return "iops"
    if sort_key == ord('b'): return "bw"
    if sort_key == ord('l'): return "lat"
    if sort_key == ord('c'): return "cpu"
    return self.sort


  def render_header(self):
    # Turning on attributes for title
    self.stdscr.attron(curses.color_pair(self.RED))
    self.stdscr.attron(curses.A_BOLD)

    # Rendering title
    self.stdscr.addstr(0, 5, self.title)
    self.stdscr.addstr(0, self.width - 12,
                       datetime.datetime.now().strftime(" %H:%M:%S "))

    # Turning off attributes for title
    self.stdscr.attroff(curses.color_pair(self.RED))
    self.stdscr.attroff(curses.A_BOLD)

  def render_nodes_cpu_pad(self, y, x):
    self.stdscr.noutrefresh()
    pad_size_y, pad_size_x =self.nodes_cpu_pad.getmaxyx()
    
    self.nodes_cpu_pad.attron(curses.A_BOLD)
    self.nodes_cpu_pad.addstr(0, 3, " Nodes CPU ")
    
    self.nodes_cpu_pad.addstr(1, 1, "{0:<20} {1:>5} |{2:50}"
                  .format("Name",
                          "CPU%",
                          "0%         |25%         |50%        |75%     100%|"))

    self.nodes_cpu_pad.attroff(curses.A_BOLD)

    nodes = self.node_reporter.overall_live_report()
    for i in range(0, len(nodes)):
      node = nodes[i]
      rangex = int(0.5 * node["hypervisor_cpu_usage_percent"])
      self.nodes_cpu_pad.addstr(i + 2, 1, "{0:<20} {1:>5.2f} |{2:50}"
                                .format(node["node_name"][:20],
                                        node["hypervisor_cpu_usage_percent"],
                                        "#" * rangex))      

    self.safe_noautorefresh(self.nodes_cpu_pad, 0, 0, y, x, pad_size_y, 80)
    return y + pad_size_y

  def render_vm_overall_pad(self, y, x):
    self.stdscr.noutrefresh()
    pad_size_y, pad_size_x =self.vm_overall_pad.getmaxyx()

    self.sort = self.get_sort_label(self.key)

    self.vm_overall_pad.attron(curses.A_BOLD)
    self.vm_overall_pad.addstr(0, 3, " Overall VMs ")
    self.vm_overall_pad.attroff(curses.A_BOLD)

    self.vm_overall_pad.addstr(0, pad_size_x - 15, " Sort: {} "
                               .format(self.sort))

    self.vm_overall_pad.attron(curses.A_BOLD)
    self.vm_overall_pad.addstr(1, 1,
            "{vm:<{width}} {cpu:>6} {rdy:>6} {mem:>6} {iops:>6} {bw:>6} "
            "{lat:>6}".format(
              vm="VM Name",
              cpu="CPU%",
              rdy="RDY%",
              mem="MEM%",
              iops="IOPs",
              bw = "B/W",
              lat="LAT",
              width=self.vm_reporter.max_vm_name_width))

    self.vm_overall_pad.attroff(curses.A_BOLD)

    vms = self.vm_reporter.overall_live_report(self.sort)
    for i in range(0, len(vms)):
      vm = vms[i]
      self.vm_overall_pad.addstr(i + 2, 1,
                    "{v[vm_name]:<{max_vm_name_width}} "
                    "{v[hypervisor_cpu_usage_percent]:>6.2f} "
                    "{v[hypervisor.cpu_ready_time_ppm]:>6.2f} "
                    "{v[memory_usage_percent]:>6.2f} "
                    "{v[controller_num_iops]:>6} "
                    "{v[controller_io_bandwidth_kBps]:>6.2f} "
                    "{v[controller_avg_io_latency_msecs]:>6.2f} "
                    .format(v=vm,
                        max_vm_name_width=self.vm_reporter.max_vm_name_width))

    self.safe_noautorefresh(self.vm_overall_pad, 0, 0, y, x, pad_size_y, 80)
    return y + pad_size_y
          
  def render_main_screen(self, stdscr):
    self.stdscr.clear()
    self.stdscr.nodelay(1)

    # Set invisible cursor
    curses.curs_set(0)

    while (self.key != ord('q')):
      
      current_y_position = 2

      # Initialization
      self.stdscr.clear()
      self.height, self.width = stdscr.getmaxyx()
      self.stdscr.border()

      self.render_header()

      if current_y_position < self.height:
        current_y_position = self.render_nodes_cpu_pad(current_y_position,1)

      if current_y_position < self.height - 2:
        current_y_position = self.render_vm_overall_pad(current_y_position,1)
      
      # Refresh the screen
      self.stdscr.noutrefresh()

      # Stage all updates
      curses.doupdate()
      
      # Wait for next input
      time.sleep(1)
      self.key = self.stdscr.getch()

      
def valid_date(date_string):
  try:
    return datetime.datetime.strptime(date_string, "%Y/%m/%d-%H:%M:%S")
  except ValueError:
    msg = "Invalid date: {0!r}".format(date_string)
    raise argparse.ArgumentTypeError(msg)


# TODO: Need to do a better job here.
#       Too much logic for a main function.
#       Move this to a main class.
if __name__ == "__main__":
  try:
    parser = argparse.ArgumentParser(
      description="Report cluster activity",
      epilog='"When you eliminate the impossible, whatever remains, '
             'however improbable, must be the truth." Spock.'
    )
    parser.add_argument('--nodes', '-n', action='store_true',
                        help="Overall nodes activity report")
    parser.add_argument('--node-name', '-N', action='append',
                        help="Filter VMs by node name")
    parser.add_argument('--uvms', '-v', action='store_true',
                        help="Overall user VMs activity report")
    parser.add_argument('--sort', '-s',
                        choices=["name", "cpu", "rdy", "mem",
                                 "iops","bw", "lat"],
                        default="name", help="Sort output")
    parser.add_argument( "-start-time", "-S", 
                         help="Start time in format YYYY/MM/DD-hh:mm:ss. "
                               "Specified in local time.",
                         type=valid_date)    
    parser.add_argument( "-end-time", "-E", 
                         help="End time in format YYYY/MM/DD-hh:mm:ss. "
                               "Specified in local time",
                         type=valid_date)    
    parser.add_argument('--test', '-t', action='store_true',
                        help="Place holder for testing new features")    
    parser.add_argument('sec', type=int, nargs="?", default=None,
                        help="Interval in seconds")
    parser.add_argument('count', type=int, nargs="?", default=None,
                        help="Number of iterations")
    args = parser.parse_args()

    if args.start_time and args.end_time:
      if args.start_time >= args.end_time:
        parser.print_usage()
        print("Invalid date: --start-time must be before --end-time")
        exit(1)
 
    if args.nodes:
      try:
        ui_cli = UiCli()        

        if not args.start_time and not args.end_time:
          ui_cli.nodes_overall_live_report(args.sec, args.count, args.sort)
        elif args.start_time and args.end_time:
          ui_cli.nodes_time_range_report(args.start_time,
                                         args.end_time,
                                         args.sec,
                                         args.sort)
        else:
          parser.print_usage()
          print("Invalid date: Arguments --start-time and "
                "--end-time should come together")
          
      except KeyboardInterrupt:
        print("Narf!")
        exit(0)

    elif args.uvms:
      try:
        ui_cli = UiCli()        
        ui_cli.uvms_overall_live_report(args.sec,
                                        args.count,
                                        args.sort,
                                        args.node_name)
      except KeyboardInterrupt:
        print("Zort!")
        exit(0)
      
    elif args.test:
      print("==== TESTING ====")
      #vm_reporter = VmReporter()
      #vm_reporter.test_data_processing()

      node_reporter = NodeReporter()
      #print(datetime.datetime.strptime("2022/01/01-12:00:00", "%Y/%m/%d-%H:%M:%S"))
      #print(args.start_time.strftime('%s'))
      ui_cli = UiCli()
      ui_cli.nodes_time_range_report(args.start_time,args.end_time,"foo")
      
    else:
      ui_interactive = UiInteractive()
      curses.wrapper(ui_interactive.render_main_screen)

  except IOError:
    # Python flushes standard streams on exit; redirect remaining output
    # to devnull to avoid another BrokenPipeError at shutdown
    # see https://docs.python.org/3/library/signal.html#note-on-sigpipe
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    sys.exit(1)  # Python exits with error code 1 on EPIPE

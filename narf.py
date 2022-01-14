#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: harold.gutierrez@nutanix.com
#
# Report cluster activity from arithmos
#

from __future__ import division

import sys  # noqa: E402
sys.path.insert(0, '/usr/local/nutanix/bin/')  # noqa: E402

import os
import signal
import uuid
import curses
import argparse
import datetime
import time
import env

from util.interfaces.interfaces import NutanixInterfaces  # noqa: E402
from stats.arithmos.interface.arithmos_type_pb2 import *  # noqa: E402
from stats.arithmos.interface.arithmos_interface_pb2 import (
    AgentGetEntitiesArg, MasterGetEntitiesArg)  # noqa: E402
from serviceability.interface.analytics.arithmos_rpc_client import (
    ArithmosDataProcessing)  # noqa: E402


# from stats.arithmos import stats_util


class Reporter(object):
    """Reporter base """

    def __init__(self):
        self.interfaces = NutanixInterfaces()
        self.arithmos_interface = ArithmosDataProcessing()
        self.arithmos_client = self.interfaces.arithmos_client
        self.FIELD_NAMES = []

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
                stats[desired_stat] = -1
        return stats

    def _get_generic_attribute_dict(self, generic_attribute_list):
        """
        Transform generic_attribute_list returned from arithmos into a dictionary.
        Arithmos returns generic_attribute in the form of:

          generic_attribute_list {
            attribute_name: "vm_uuid"
            attribute_value_str: "00c43e1e-33db-4c91-9819-9b2e6f7b6111"
          }

        This functions transform this into:
           { "vm_uuid": "00c43e1e-33db-4c91-9819-9b2e6f7b6111" }

        Making it easy to handle by reporters and Ui.
        """
        ret = {}
        for generic_attribute in generic_attribute_list:
            ret[generic_attribute.attribute_name] = \
                generic_attribute.attribute_value_str
        return ret

    def _zeroed_missing_attribute(self, attributes, desired_attribute_list):
        """
        If an entity is missing an attribute in the returned data from arithmos
        then it's necessary to fill the missing information to fill the
        fields when it's displayed by the Ui.

        This function takes an actual list of attributes and a list of desired
        attributes. If a attribute in the desired list is missing from the attribute list
        then it add it with a value of "-" and returns a new list.

        TODO: There may be a better way to do this.
              Review if this is valid.
        """
        for desired_attribute in desired_attribute_list:
            if desired_attribute not in attributes:
                attributes[desired_attribute] = "-"
        return attributes


class ClusterReporter(Reporter):
    """Reports for Clusters"""

    def __init__(self):
        Reporter.__init__(self)
        self._ARITHMOS_ENTITY_PROTO = ArithmosEntityProto.kCluster
        self.max_cluster_name_width = 0

        self.cluster = self._get_cluster_live_stats(
            field_name_list=["cluster_name", "id"])
        self.name = self.cluster[0].cluster_name
        self.cluster_id = self.cluster[0].id

    def _get_cluster_live_stats(self, sort_criteria=None, filter_criteria=None,
                                search_term=None, field_name_list=None):
        response = self._get_live_stats(self._ARITHMOS_ENTITY_PROTO,
                                        sort_criteria, filter_criteria,
                                        search_term, field_name_list)
        entity_list = response.entity_list.cluster
        return entity_list

    def overall_live_report(self, sort="name"):
        field_names = ["cluster_name", "hypervisor_cpu_usage_ppm",
                       "hypervisor_memory_usage_ppm", "hypervisor_num_iops",
                       "controller_num_iops", "num_iops",
                       "avg_io_latency_usecs", "io_bandwidth_kBps"]

        pass


class NodeReporter(Reporter):
    """Reports for Nodes"""

    def __init__(self):
        Reporter.__init__(self)
        self._ARITHMOS_ENTITY_PROTO = ArithmosEntityProto.kNode
        self.max_node_name_width = 0

        self.sort_conversion = {
            "name": "node_name",
            "cpu": "hypervisor_cpu_usage_percent",
            "mem": "hypervisor_memory_usage_percent",
            "iops": "num_iops",
            "bw": "io_bandwidth_mBps",
            "lat": "avg_io_latency_msecs"
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
        field_names = ["node_name", "id", "hypervisor_cpu_usage_ppm",
                       "hypervisor_memory_usage_ppm", "hypervisor_num_iops",
                       "controller_num_iops", "num_iops",
                       "avg_io_latency_usecs", "io_bandwidth_kBps"]

        if sort in self.sort_conversion.keys():
            sort_by = self.sort_conversion[sort]
        else:
            sort_by = self.sort_conversion["name"]

        filter_by = ""
        all_nodes = []
        stats = self._get_node_live_stats(field_name_list=field_names,
                                          filter_criteria=filter_by)
        for node_stat in stats:
            node = {
                "node_name": node_stat.node_name,
                "node_id": node_stat.id,
                "hypervisor_cpu_usage_percent":
                node_stat.stats.hypervisor_cpu_usage_ppm / 10000,
                "hypervisor_memory_usage_percent":
                node_stat.stats.hypervisor_memory_usage_ppm / 10000,
                "controller_num_iops":
                node_stat.stats.common_stats.controller_num_iops,
                "hypervisor_num_iops":
                node_stat.stats.common_stats.hypervisor_num_iops,
                "num_iops":
                node_stat.stats.common_stats.num_iops,
                "avg_io_latency_msecs":
                node_stat.stats.common_stats.avg_io_latency_usecs / 1000,
                "io_bandwidth_mBps":
                float(node_stat.stats.common_stats.io_bandwidth_kBps / 1024)
            }
            all_nodes.append(node)

        if sort_by == "node_name":
            return sorted(all_nodes, key=lambda node: node[sort_by])
        else:
            return sorted(all_nodes, key=lambda node: node[sort_by], reverse=True)

    def overall_time_range_report(self, start, end, sort="name", nodes=[]):
        if sort in self.sort_conversion.keys():
            sort_by = self.sort_conversion[sort]
        else:
            sort_by = self.sort_conversion["name"]

        sampling_interval = 30
        all_nodes = []
        for node in self.nodes:
            node_stats = {
                "node_name": node.node_name,
                "node_id": node.id,
                "hypervisor_cpu_usage_percent":
                self._get_time_range_stat_average(
                    node.id, "hypervisor_cpu_usage_ppm", start, end,
                    sampling_interval) / 10000,
                "hypervisor_memory_usage_percent":
                self._get_time_range_stat_average(
                    node.id, "hypervisor_memory_usage_ppm", start, end,
                    sampling_interval) / 10000,
                "controller_num_iops":
                self._get_time_range_stat_average(
                    node.id, "controller_num_iops", start, end,
                    sampling_interval),
                "hypervisor_num_iops":
                self._get_time_range_stat_average(
                    node.id, "hypervisor_num_iops", start, end,
                    sampling_interval),
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
            return sorted(all_nodes, key=lambda node: node[sort_by])
        else:
            return sorted(all_nodes, key=lambda node: node[sort_by], reverse=True)


class VmReporter(Reporter):
    """Reports for UVMs"""

    def __init__(self):
        Reporter.__init__(self)
        self._ARITHMOS_ENTITY_PROTO = ArithmosEntityProto.kVM
        self.max_vm_name_width = 0

        # The reason this conversion exists is because we want to abstract
        # the actual attribute names with something more human friendly
        # and easy to remember. We also want to abstract this from the
        # UI classes.
        self.sort_conversion = {
            "name": "vm_name",
            "cpu": "hypervisor_cpu_usage_percent",
            "rdy": "hypervisor_cpu_ready_time_percent",
            "mem": "memory_usage_percent",
            "iops": "controller_num_iops",
            "bw": "controller_io_bandwidth_mBps",
            "lat": "controller_avg_io_latency_msecs"
        }

    def _get_vm_live_stats(self, sort_criteria=None, filter_criteria=None,
                           search_term=None, field_name_list=None):
        response = self._get_live_stats(self._ARITHMOS_ENTITY_PROTO,
                                        sort_criteria, filter_criteria,
                                        search_term, field_name_list)
        entity_list = response.entity_list.vm
        return entity_list

    def overall_live_report(self, sort="name", node_names=[]):
        field_names = ["vm_name", "id", "node_name",
                       "hypervisor_cpu_usage_ppm",
                       "hypervisor.cpu_ready_time_ppm",
                       "memory_usage_ppm", "controller_num_iops",
                       "hypervisor_num_iops", "num_iops",
                       "controller_io_bandwidth_kBps",
                       "controller_avg_io_latency_usecs"]

        if sort in self.sort_conversion.keys():
            sort_by = self.sort_conversion[sort]
        else:
            sort_by = self.sort_conversion["name"]

        filter_by = "power_state==on"
        if node_names:
            node_names_str = ",".join(["node_name==" + node_name
                                       for node_name in node_names])
            filter_by += ";" + node_names_str

        stats = self._get_vm_live_stats(field_name_list=field_names,
                                        filter_criteria=filter_by)

        all_vms = []
        for vm_stat in stats:

            # Convert a known list of generic_stats into a dictionary
            generic_stats = self._get_generic_stats_dict(
                vm_stat.stats.generic_stat_list)
            generic_stat_names = ["memory_usage_ppm",
                                  "hypervisor.cpu_ready_time_ppm"]
            generic_stats = self._zeroed_missing_stats(generic_stats,
                                                       generic_stat_names)

            # Convert a known list of generic_attributes into a dictionary
            generic_attributes = self._get_generic_attribute_dict(
                vm_stat.generic_attribute_list)
            generic_attribute_names = ["node_name"]
            generic_attributes = self._zeroed_missing_attribute(generic_attributes,
                                                                generic_attribute_names)

            # I don't know which other stats might be missing from the data returned
            # from Arithmos, so more workarounds like previous one may be needed
            # in the future.
            # Function _zeroed_missing_stats() should work for most cases.
            vm = {
                "vm_name": vm_stat.vm_name,
                "node_name": generic_attributes["node_name"],
                "hypervisor_cpu_usage_percent":
                vm_stat.stats.hypervisor_cpu_usage_ppm / 10000,
                "hypervisor_cpu_ready_time_percent":
                generic_stats["hypervisor.cpu_ready_time_ppm"] / 10000,
                "memory_usage_percent":
                generic_stats["memory_usage_ppm"] / 10000,
                "controller_num_iops":
                vm_stat.stats.common_stats.controller_num_iops,
                "hypervisor_num_iops":
                vm_stat.stats.common_stats.hypervisor_num_iops,
                "num_iops":
                vm_stat.stats.common_stats.num_iops,
                "controller_io_bandwidth_mBps":
                vm_stat.stats.common_stats.controller_io_bandwidth_kBps / 1024,
                "controller_avg_io_latency_msecs":
                vm_stat.stats.common_stats.controller_avg_io_latency_usecs / 1000
            }
            all_vms.append(vm)

        if sort_by == "vm_name":
            return sorted(all_vms, key=lambda node: node[sort_by])
        else:
            return sorted(all_vms, key=lambda node: node[sort_by], reverse=True)

    def overall_time_range_report(self, start, end, sort="name", node_names=[]):
        if sort in self.sort_conversion.keys():
            sort_by = self.sort_conversion[sort]
        else:
            sort_by = self.sort_conversion["name"]

        # TODO: Needs to test on the behavior of when a VM is shutdown,
        #       and see if there is a way to confirm in which host a VM
        #       was running during time period of the report.
        #
        # Following code filter by running VMs:
        # filter_by = "power_state==on"
        # if node_names:
        #  node_names_str = ",".join(["node_name==" + node_name
        #                             for node_name in node_names])
        #  filter_by += ";" + node_names_str
        #
        filter_by = ""
        if node_names:
            filter_by = ",".join(["node_name==" + node_name
                                  for node_name in node_names])

        vm_list = self._get_vm_live_stats(field_name_list=["vm_name", "id",
                                                           "node_name"],
                                          filter_criteria=filter_by)
        generic_attribute_names = ["node_name"]

        sampling_interval = 30
        all_vms = []
        for vm in vm_list:
            # Convert a known list of generic_attributes into a dictionary
            generic_attributes = self._get_generic_attribute_dict(
                vm.generic_attribute_list)
            generic_attributes = self._zeroed_missing_attribute(generic_attributes,
                                                                generic_attribute_names)

            vm = {
                "vm_name": vm.vm_name,
                "vm_id": vm.id,
                "node_name": generic_attributes["node_name"],
                "hypervisor_cpu_usage_percent":
                self._get_time_range_stat_average(
                    vm.id, "hypervisor_cpu_usage_ppm", start, end,
                    sampling_interval) / 10000,
                "hypervisor_cpu_ready_time_percent":
                self._get_time_range_stat_average(
                    vm.id, "hypervisor.cpu_ready_time_ppm", start, end,
                    sampling_interval) / 10000,
                "memory_usage_percent":
                self._get_time_range_stat_average(
                    vm.id, "memory_usage_ppm", start, end,
                    sampling_interval) / 10000,
                "controller_num_iops":
                int(self._get_time_range_stat_average(
                    vm.id, "controller_num_iops", start, end,
                    sampling_interval)),
                "hypervisor_num_iops":
                int(self._get_time_range_stat_average(
                    vm.id, "hypervisor_num_iops", start, end,
                    sampling_interval)),
                "num_iops":
                int(self._get_time_range_stat_average(
                    vm.id, "num_iops", start, end,
                    sampling_interval)),
                "controller_io_bandwidth_mBps":
                self._get_time_range_stat_average(
                    vm.id, "controller_io_bandwidth_kBps", start, end,
                    sampling_interval) / 1024,
                "controller_avg_io_latency_msecs":
                self._get_time_range_stat_average(
                    vm.id, "controller_avg_io_latency_usecs", start, end,
                    sampling_interval) / 1000,
            }
            all_vms.append(vm)

        if sort_by == "vm_name":
            return sorted(all_vms, key=lambda vm: vm[sort_by])
        else:
            return sorted(all_vms, key=lambda node: node[sort_by], reverse=True)


class Ui(object):
    """Display base"""

    def __init__(self):
        self.cluster_reporter = ClusterReporter()
        self.node_reporter = NodeReporter()
        self.vm_reporter = VmReporter()
        self.UiUuid = uuid.uuid1()

    def time_validator(self, start_time, end_time,
                       sec=None):
        """
        Check start_time, end_time and sec are valid. Returns sec or a valid
        value for sec if possible, if there is no valid value for sec returns -1.
        """
        if start_time >= end_time:
            parser.print_usage()
            print("ERROR: Invalid date: Start time must be before end time")
            return -1

        if ((end_time - start_time).days < 1
                and (end_time - start_time).seconds < 30):
            parser.print_usage()
            print("ERROR: Invalid dates: difference between start and "
                  "end is less than 30 seconds.\n"
                  "       Minimum time difference for historic report is 30 seconds.")
            return -1
        elif not sec:
            print("INFO: Not interval indicated, setting "
                  "interval to 60 seconds.")
            sec = 60
        elif sec < 30:
            print("INFO: Invalid interval: minimum value 30 seconds for "
                  "historic report. \n"
                  "      Setting interval to 30 seconds.")
            sec = 30

        delta_time = start_time + datetime.timedelta(seconds=sec)
        if delta_time > end_time:
            sec = int(end_time.strftime("%s")) - int(start_time.strftime("%s"))
            print("INFO: Invalid interval: greater than the difference "
                  "between start and end time.\n"
                  "      Setting interval to difference between start and end."
                  " Interval = " + str(sec))
            return sec
        return sec


class UiCli(Ui):
    """CLI interface"""

    # TODO: Need to review this report_time_validator function.
    #       If need to validate time for functions with different
    #       a different set of parameters this function is limited
    #       and will not work.
    #
    # Proposal: Make time validator a function that returns boolean
    #           and the time_range_reports to use it and exit if false.
    def report_time_validator(self, report_function, start_time, end_time,
                              sec=None, sort="name", nodes=[]):
        if start_time >= end_time:
            parser.print_usage()
            print("ERROR: Invalid date: Start time must be before end time")
            return False

        if ((end_time - start_time).days < 1
                and (end_time - start_time).seconds < 30):
            parser.print_usage()
            print("ERROR: Invalid dates: difference between start and "
                  "end is less than 30 seconds.\n"
                  "       Minimum time difference for historic report is 30 seconds.")
            return False
        if not sec:
            report_function(start_time, end_time, sort, nodes)
            return True
        elif sec < 30:
            print("INFO: Invalid interval: minimum value 30 seconds for "
                  "historic report. \n"
                  "      Setting interval to 30 seconds.")
            sec = 30

        step_time = start_time
        delta_time = start_time + datetime.timedelta(seconds=sec)
        if delta_time > end_time:
            print("INFO: Invalid interval: greater than the difference "
                  "between start and end time.\n"
                  "      Setting single interval between start and end.")
            report_function(start_time, end_time, sort, nodes)
            return True
        else:
            while step_time < end_time:
                report_function(step_time, delta_time, sort, nodes)
                step_time = delta_time
                delta_time += datetime.timedelta(seconds=sec)
            return True

    def nodes_overall_live_report(self, sec, count, sort="name"):
        if not sec or sec < 0:
            sec = 0
            count = 1
        else:
            if not count or count < 0:
                count = 1000
        i = 0
        while i < count:
            time.sleep(sec)
            i += 1
            today = datetime.date.today()
            time_now = datetime.datetime.now().strftime("%H:%M:%S")
            nodes = self.node_reporter.overall_live_report(sort)
            print("{time:<11} {node:<20} {cpu:>6} {mem:>6} "
                  "{ciops:>8} {hiops:>8} {iops:>8} {bw:>8} "
                  "{lat:>8}".format(
                      time=str(today),
                      node="Node",
                      cpu="CPU%",
                      mem="MEM%",
                      ciops="cIOPs",
                      hiops="hIOPs",
                      iops="IOPs",
                      bw="B/W[MB]",
                      lat="LAT[ms]",
                  ))
            for node in nodes:
                print("{time:<11} "
                      "{node_name:<20} "
                      "{n[hypervisor_cpu_usage_percent]:>6.2f} "
                      "{n[hypervisor_memory_usage_percent]:>6.2f} "
                      "{n[controller_num_iops]:>8.2f} "
                      "{n[hypervisor_num_iops]:>8.2f} "
                      "{n[num_iops]:>8.2f} "
                      "{n[io_bandwidth_mBps]:>8.2f} "
                      "{n[avg_io_latency_msecs]:>8.2f} "
                      .format(time=str(time_now),
                              n=node,
                              node_name=node["node_name"][:20]))
            print("")

    def nodes_overall_time_range_report(self, start_time, end_time, sort="name", hosts=[]):
        usec_start = int(start_time.strftime("%s") + "000000")
        usec_end = int(end_time.strftime("%s") + "000000")
        nodes = self.node_reporter.overall_time_range_report(
            usec_start, usec_end, sort)
        print("{time:<21} {node:<20} {cpu:>6} {mem:>6} "
              "{ciops:>8} {hiops:>8} {iops:>8} {bw:>8} "
              "{lat:>8}".format(
                  time=start_time.strftime("%Y/%m/%d-%H:%M:%S"),
                  node="Node",
                  cpu="CPU%",
                  mem="MEM%",
                  ciops="cIOPs",
                  hiops="hIOPs",
                  iops="IOPs",
                  bw="B/W[MB]",
                  lat="LAT[ms]"))
        for node in nodes:
            print("{time:<21} "
                  "{node_name:<20} "
                  "{n[hypervisor_cpu_usage_percent]:>6.2f} "
                  "{n[hypervisor_memory_usage_percent]:>6.2f} "
                  "{n[controller_num_iops]:>8.2f} "
                  "{n[hypervisor_num_iops]:>8.2f} "
                  "{n[num_iops]:>8.2f} "
                  "{n[io_bandwidth_mBps]:>8.2f} "
                  "{n[avg_io_latency_msecs]:>8.2f} "
                  .format(time=start_time.strftime("%Y/%m/%d-%H:%M:%S"),
                          n=node,
                          node_name=node["node_name"][:20]))
        print("")

    def uvms_overall_live_report(self, sec, count, sort="name", node_names=[]):
        if not sec or sec < 0:
            sec = 0
            count = 1
        else:
            if not count or count < 0:
                count = 1000
        i = 0
        while i < count:
            i += 1
            today = datetime.date.today()
            time_now = datetime.datetime.now().strftime("%H:%M:%S")
            vms = self.vm_reporter.overall_live_report(sort, node_names)
            print("{time:<11} {vm:<30} {cpu:>6} {rdy:>6} {mem:>6} "
                  "{ciops:>6} {hiops:>6} {iops:>6} {bw:>8} {lat:>8}".format(
                      time=str(today),
                      vm="VM Name",
                      cpu="CPU%",
                      rdy="RDY%",
                      mem="MEM%",
                      ciops="cIOPs",
                      hiops="hIOPs",
                      iops="IOPs",
                      bw="B/W[MB]",
                      lat="LAT[ms]",
                      width=self.vm_reporter.max_vm_name_width
                  ))
            for vm in vms:
                print("{0:<11} {vm_name:<30} "
                      "{v[hypervisor_cpu_usage_percent]:>6.2f} "
                      "{v[hypervisor_cpu_ready_time_percent]:>6.2f} "
                      "{v[memory_usage_percent]:>6.2f} "
                      "{v[controller_num_iops]:>6} "
                      "{v[hypervisor_num_iops]:>6} "
                      "{v[num_iops]:>6} "
                      "{v[controller_io_bandwidth_mBps]:>8.2f} "
                      "{v[controller_avg_io_latency_msecs]:>8.2f} "
                      .format(str(time_now),
                              vm_name=vm["vm_name"][:30],
                              v=vm))
            print("")
            time.sleep(sec)

    def uvms_overall_time_range_report(self, start_time, end_time,
                                       sort="name", node_names=[]):
        usec_start = int(start_time.strftime("%s") + "000000")
        usec_end = int(end_time.strftime("%s") + "000000")
        vms = self.vm_reporter.overall_time_range_report(usec_start, usec_end,
                                                         sort, node_names)
        print("{time:<21} {vm:<30} {cpu:>6} {rdy:>6} {mem:>6} "
              "{ciops:>6} {hiops:>6} {iops:>6} {bw:>8} {lat:>8}".format(
                  time=start_time.strftime("%Y/%m/%d-%H:%M:%S"),
                  vm="VM Name",
                  cpu="CPU%",
                  rdy="RDY%",
                  mem="MEM%",
                  ciops="cIOPs",
                  hiops="hIOPs",
                  iops="IOPs",
                  bw="B/W[MB]",
                  lat="LAT[ms]"
              ))
        for vm in vms:
            print("{time:<21} {vm_name:<30} "
                  "{v[hypervisor_cpu_usage_percent]:>6.2f} "
                  "{v[hypervisor_cpu_ready_time_percent]:>6.2f} "
                  "{v[memory_usage_percent]:>6.2f} "
                  "{v[controller_num_iops]:>6.0f} "
                  "{v[hypervisor_num_iops]:>6.0f} "
                  "{v[num_iops]:>6.0f} "
                  "{v[controller_io_bandwidth_mBps]:>8.2f} "
                  "{v[controller_avg_io_latency_msecs]:>8.2f} "
                  .format(time=start_time.strftime("%Y/%m/%d-%H:%M:%S"),
                          vm_name=vm["vm_name"][:30],
                          v=vm))
        print("")


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
            len(self.node_reporter.overall_live_report()) + 3, 87)
        self.nodes_cpu_pad.border()

        self.nodes_io_pad = curses.newpad(
            len(self.node_reporter.overall_live_report()) + 3, 87)
        self.nodes_io_pad.border()

        self.vm_overall_pad = curses.newpad(
            len(self.vm_reporter.overall_live_report()) + 3, 87)
        self.vm_overall_pad.border()

        self.initialize_colors()
        self.initialize_strings()

        self.key = 0
        self.vm_sort = "cpu"
        self.nodes_sort = "name"
        self.nodes_pad = "cpu"
        self.nodes = []
        self.active_node = None
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
        self.BLACK_WHITE = 8

        # Start colors in curses
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(self.RED, curses.COLOR_RED, -1)
        curses.init_pair(self.GREEN, curses.COLOR_GREEN, -1)
        curses.init_pair(self.YELLOW, curses.COLOR_YELLOW, -1)
        curses.init_pair(self.BLUE, curses.COLOR_BLUE, -1)
        curses.init_pair(self.MAGENTA, curses.COLOR_MAGENTA, -1)
        curses.init_pair(self.CYAN, curses.COLOR_CYAN, -1)
        curses.init_pair(self.WHITE_BLACK, curses.COLOR_WHITE,
                         curses.COLOR_BLACK)
        curses.init_pair(self.BLACK_WHITE, curses.COLOR_BLACK,
                         curses.COLOR_WHITE)

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

    def get_nodes_sort_label(self, sort_key):
        if sort_key == ord('N'):
            return "name"
        if sort_key == ord('C'):
            return "cpu"
        if sort_key == ord('M'):
            return "mem"
        if sort_key == ord('I'):
            return "iops"
        if sort_key == ord('B'):
            return "bw"
        if sort_key == ord('L'):
            return "lat"
        return self.nodes_sort

    def get_vm_sort_label(self, sort_key):
        if sort_key == ord('r'):
            return "rdy"
        if sort_key == ord('m'):
            return "mem"
        if sort_key == ord('i'):
            return "iops"
        if sort_key == ord('b'):
            return "bw"
        if sort_key == ord('l'):
            return "lat"
        if sort_key == ord('c'):
            return "cpu"
        return self.vm_sort

    def toggle_nodes_pad(self, toggle_key):
        if toggle_key == ord('n'):
            if self.nodes_pad == "cpu":
                self.nodes_pad = "iops"
            elif self.nodes_pad == "iops":
                self.nodes_pad = "cpu"

    def toggle_active_node(self, toggle_key):
        if toggle_key == ord('\t'):
            for i in range(0, len(self.nodes)):
                node = self.nodes[i]
                if not self.active_node:
                    self.active_node = node["node_name"]
                    return
                elif i == len(self.nodes) - 1 and node["node_name"] == self.active_node:
                    self.active_node = None
                    return
                elif node["node_name"] == self.active_node:
                    self.active_node = self.nodes[i + 1]["node_name"]
                    return

    def handle_key_press(self):
        self.key = self.stdscr.getch()
        self.nodes_sort = self.get_nodes_sort_label(self.key)
        self.vm_sort = self.get_vm_sort_label(self.key)
        self.toggle_nodes_pad(self.key)
        self.toggle_active_node(self.key)

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
        pad_size_y, pad_size_x = self.nodes_cpu_pad.getmaxyx()

        self.nodes_cpu_pad.attron(curses.A_BOLD)
        self.nodes_cpu_pad.addstr(0, 3, " Nodes CPU ")
        self.nodes_cpu_pad.attroff(curses.A_BOLD)

        self.nodes_cpu_pad.addstr(0, pad_size_x - 15, " Sort: {0:<4} "
                                  .format(self.nodes_sort))

        self.nodes_cpu_pad.attron(curses.A_BOLD)

        self.nodes_cpu_pad.addstr(1, 1, "{0:<20} {1:>6} {2:>6}|{3:50}"
                                  .format("Name",
                                          "MEM%",
                                          "CPU%",
                                          "0%         |25%         |50%        |75%     100%|"))

        self.nodes_cpu_pad.attroff(curses.A_BOLD)

        self.nodes = self.node_reporter.overall_live_report(self.nodes_sort)
        for i in range(0, len(self.nodes)):
            node = self.nodes[i]
            rangex = int(0.5 * node["hypervisor_cpu_usage_percent"])

            if node["node_name"] == self.active_node:
                self.nodes_cpu_pad.attron(curses.color_pair(self.BLACK_WHITE))
                self.nodes_cpu_pad.attron(curses.A_BOLD)

            self.nodes_cpu_pad.addstr(i + 2, 1, "{0:<20} {1:>6.2f} {2:>6.2f}|{3:50}"
                                      .format(node["node_name"][:20],
                                              node["hypervisor_memory_usage_percent"],
                                              node["hypervisor_cpu_usage_percent"],
                                              "#" * rangex))
            if node["node_name"] == self.active_node:
                self.nodes_cpu_pad.attroff(curses.color_pair(self.BLACK_WHITE))
                self.nodes_cpu_pad.attroff(curses.A_BOLD)

        self.safe_noautorefresh(self.nodes_cpu_pad, 0, 0, y, x,
                                pad_size_y, pad_size_x)
        return y + pad_size_y

    def render_nodes_io_pad(self, y, x):
        self.stdscr.noutrefresh()
        pad_size_y, pad_size_x = self.nodes_cpu_pad.getmaxyx()

        self.nodes_io_pad.attron(curses.A_BOLD)
        self.nodes_io_pad.addstr(0, 3, " Nodes IOPs ")
        self.nodes_io_pad.attroff(curses.A_BOLD)

        self.nodes_io_pad.addstr(0, pad_size_x - 15, " Sort: {0:<4} "
                                 .format(self.nodes_sort))

        self.nodes_io_pad.attron(curses.A_BOLD)

        self.nodes_io_pad.addstr(1, 1, "{0:<20} {1:>8} {2:>8} {3:>8} {4:>8} {5:>6}"
                                 .format("Name",
                                         "cIOPs",
                                         "hIOPs",
                                         "IOPs",
                                         "B/W[MB]",
                                         "Lat[ms]"))

        self.nodes_io_pad.attroff(curses.A_BOLD)

        self.nodes = self.node_reporter.overall_live_report(self.nodes_sort)
        for i in range(0, len(self.nodes)):
            node = self.nodes[i]

            if node["node_name"] == self.active_node:
                self.nodes_io_pad.attron(curses.color_pair(self.BLACK_WHITE))
                self.nodes_io_pad.attron(curses.A_BOLD)

            self.nodes_io_pad.addstr(i + 2, 1, "{0:<20} {1:>8} {2:>8} "
                                     "{3:>8} {4:>8.2f} {5:>6.2f}"
                                     .format(node["node_name"][:20],
                                             node["controller_num_iops"],
                                             node["hypervisor_num_iops"],
                                             node["num_iops"],
                                             node["io_bandwidth_mBps"],
                                             node["avg_io_latency_msecs"]))

            if node["node_name"] == self.active_node:
                self.nodes_io_pad.attroff(curses.color_pair(self.BLACK_WHITE))
                self.nodes_io_pad.attroff(curses.A_BOLD)

        self.safe_noautorefresh(self.nodes_io_pad, 0, 0, y, x,
                                pad_size_y, pad_size_x)
        return y + pad_size_y

    def render_vm_overall_pad(self, y, x):
        self.stdscr.noutrefresh()
        self.vm_overall_pad.clear()

        if self.active_node:
            vms = self.vm_reporter.overall_live_report(
                self.vm_sort, [self.active_node])
        else:
            vms = self.vm_reporter.overall_live_report(
                self.vm_sort)
        self.vm_overall_pad = curses.newpad(len(vms) + 3, 87)
        self.vm_overall_pad.border()

        pad_size_y, pad_size_x = self.vm_overall_pad.getmaxyx()

        self.vm_overall_pad.attron(curses.A_BOLD)
        self.vm_overall_pad.addstr(0, 3, " Overall VMs ")
        self.vm_overall_pad.attroff(curses.A_BOLD)

        self.vm_overall_pad.addstr(0, pad_size_x - 15, " Sort: {0:<4} "
                                   .format(self.vm_sort))

        if self.active_node:
            self.vm_overall_pad.attron(curses.color_pair(self.BLACK_WHITE))
        self.vm_overall_pad.attron(curses.A_BOLD)
        self.vm_overall_pad.addstr(1, 1,
                                   " {vm_name:<30} {cpu:>6} {rdy:>6} {mem:>6} {ciops:>6} "
                                   "{hiops:>6} {bw:>8} {lat:>8}".format(
                                       vm_name="VM Name",
                                       cpu="CPU%",
                                       rdy="RDY%",
                                       mem="MEM%",
                                       ciops="cIOPs",
                                       hiops="hIOPs",
                                       iops="IOPs",
                                       bw="B/W[MB]",
                                       lat="LAT[ms]"))

        self.vm_overall_pad.attroff(curses.A_BOLD)
        if self.active_node:
            self.vm_overall_pad.attroff(curses.color_pair(self.BLACK_WHITE))

        for i in range(0, len(vms)):
            vm = vms[i]

            self.vm_overall_pad.addstr(i + 2, 1,
                                       " {v[vm_name]:<30} "
                                       "{v[hypervisor_cpu_usage_percent]:>6.2f} "
                                       "{v[hypervisor_cpu_ready_time_percent]:>6.2f} "
                                       "{v[memory_usage_percent]:>6.2f} "
                                       "{v[controller_num_iops]:>6} "
                                       "{v[hypervisor_num_iops]:>6} "
                                       "{v[controller_io_bandwidth_mBps]:>8.2f} "
                                       "{v[controller_avg_io_latency_msecs]:>8.2f} "
                                       .format(v=vm, vm_name=vm["vm_name"][:30]))

        self.safe_noautorefresh(self.vm_overall_pad, 0, 0, y, x,
                                pad_size_y, pad_size_x)
        return y + pad_size_y

    def render_main_screen(self, stdscr):
        self.stdscr.clear()
        self.stdscr.nodelay(1)

        # Set invisible cursor
        curses.curs_set(0)

        refresh_time = datetime.datetime.now() - datetime.timedelta(0, 2)
        while (self.key != ord('q')):

            self.handle_key_press()

            if refresh_time < datetime.datetime.now() or self.key != -1:
                current_y_position = 2

                # Initialization
                self.stdscr.clear()
                self.height, self.width = stdscr.getmaxyx()
                self.stdscr.border()

                self.render_header()

                # Display nodes pad
                if current_y_position < self.height:
                    if self.nodes_pad == "cpu":
                        current_y_position = self.render_nodes_cpu_pad(
                            current_y_position, 1)
                    elif self.nodes_pad == "iops":
                        current_y_position = self.render_nodes_io_pad(
                            current_y_position, 1)

                # Display VMs pad
                if current_y_position < self.height - 2:
                    current_y_position = self.render_vm_overall_pad(
                        current_y_position, 1)

                # Refresh the screen
                self.stdscr.noutrefresh()

                # Stage all updates
                curses.doupdate()

                # Calculate time for next screen refresh.
                # TODO: Enable hability to change refresh rate.
                refresh_time = datetime.datetime.now() + datetime.timedelta(0, 3)


class UiExporter(Ui):

    def __init__(self):
        """
        TODO:
          + Find a better way to get Y for pads, the use of overall_live_report()
            is an unnecessary call to arithmos.
        """
        Ui.__init__(self)
        self.export_file = "narf.{}.line".format(self.UiUuid)

    def write_node_datapoint(self, export_file, start_time, end_time,
                             sort="name", hosts=[]):
        """
        Get measurements for nodes.
        """
        export_file.write("# Nodes datapoints for interval {}\n"
                          .format(start_time.strftime("%Y/%m/%d-%H:%M:%S")))
        usec_start = int(start_time.strftime("%s") + "000000")
        usec_end = int(end_time.strftime("%s") + "000000")
        nodes = self.node_reporter.overall_time_range_report(
            usec_start, usec_end, sort)
        for node in nodes:
            # Tags in lexicographic order to improve performance at influxDB
            export_file.write("node,"
                              "clusterId={cluster_id},"
                              "clusterName={cluster_name},"
                              "entityId={n[node_id]},"
                              "entityName={n[node_name]},"
                              "exportId={export_id} "
                              "hypervisorCpuUsagePercent={n[hypervisor_cpu_usage_percent]:.2f},"
                              "hypervisorMemoryUsagePercent={n[hypervisor_memory_usage_percent]:.2f},"
                              "controllerNumIops={n[controller_num_iops]:.0f},"
                              "hypervisorNumIops={n[hypervisor_num_iops]:.0f},"
                              "numIops={n[num_iops]:.0f},"
                              "ioBandwidthMBps={n[io_bandwidth_mBps]:.2f},"
                              "avgIoLatencyMsecs={n[avg_io_latency_msecs]:.2f} "
                              "{time_usec}\n"
                              .format(export_id=self.UiUuid,
                                      cluster_id=self.cluster_reporter.cluster_id,
                                      cluster_name=self.cluster_reporter.name,
                                      n=node,
                                      time_usec=usec_start)
                              )
        return True

    def write_vms_datapoint(self, export_file, start_time, end_time,
                            sort="name", hosts=[]):
        """
        Get measurements for VMs.
        """
        export_file.write("# VMs datapoints for interval {}\n"
                          .format(start_time.strftime("%Y/%m/%d-%H:%M:%S")))
        usec_start = int(start_time.strftime("%s") + "000000")
        usec_end = int(end_time.strftime("%s") + "000000")
        vms = self.vm_reporter.overall_time_range_report(
            usec_start, usec_end, sort)
        for vm in vms:
            # Tags in lexicographic order to improve performance at influxDB
            export_file.write("vm,"
                              "clusterId={cluster_id},"
                              "clusterName={cluster_name},"
                              "entityId={v[vm_id]},"
                              "entityName={vm_name},"
                              "exportId={export_id},"
                              "nodeName={v[node_name]} "
                              "hypervisorCpuUsagePercent={v[hypervisor_cpu_usage_percent]:.2f},"
                              "hypervisorCpuReadyTimePercent={v[hypervisor_cpu_ready_time_percent]:.2f},"
                              "memoryUsagePercent={v[memory_usage_percent]:.2f},"
                              "controllerNumIops={v[controller_num_iops]:.0f},"
                              "hypervisorNumIops={v[hypervisor_num_iops]:.0f},"
                              "numIops={v[num_iops]:.0f},"
                              "controllerIoBandwidth_MBps={v[controller_io_bandwidth_mBps]:.2f},"
                              "controllerAvgIoLatency_msecs={v[controller_avg_io_latency_msecs]:.2f} "
                              "{time_usec}\n"
                              .format(export_id=self.UiUuid,
                                      cluster_id=self.cluster_reporter.cluster_id,
                                      cluster_name=self.cluster_reporter.name,
                                      v=vm,
                                      vm_name=vm["vm_name"].replace(" ", "\ "),
                                      time_usec=usec_start)
                              )
        return True

    def export_data(self, start_time, end_time, sec=None, sort="name", nodes=[]):
        """
        Generate a report file.
        """
        sec = self.time_validator(start_time, end_time, sec)
        if sec > -1:
            export_file = open(self.export_file, "a")
            step_time = start_time
            delta_time = start_time + datetime.timedelta(seconds=sec)
            print("INFO: Exporting datapoints. Collection ID: {}."
                  .format(self.UiUuid))
            print("INFO: Export file: {}".format(self.export_file))
            while step_time < end_time:
                print("INFO: Collecting datapoints for interval {}"
                      .format(step_time.strftime("%Y/%m/%d-%H:%M:%S")))
                self.write_node_datapoint(export_file, step_time, delta_time,
                                          sort, nodes)
                self.write_vms_datapoint(export_file, step_time, delta_time,
                                         sort, nodes)
                step_time = delta_time
                delta_time += datetime.timedelta(seconds=sec)
            export_file.close()
            print("INFO: Export completed.")
        return True


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
                                     "iops", "bw", "lat"],
                            default="name", help="Sort output")
        parser.add_argument("-start-time", "-S",
                            help="Start time in format YYYY/MM/DD-hh:mm:ss. "
                            "Specified in local time.",
                            type=valid_date)
        parser.add_argument("-end-time", "-E",
                            help="End time in format YYYY/MM/DD-hh:mm:ss. "
                            "Specified in local time",
                            type=valid_date)
        parser.add_argument('--export', '-e', action='store_true',
                            help="Export data to files in line protocol")
        parser.add_argument('--test', '-t', action='store_true',
                            help="Place holder for testing new features")
        parser.add_argument('sec', type=int, nargs="?", default=None,
                            help="Interval in seconds")
        parser.add_argument('count', type=int, nargs="?", default=None,
                            help="Number of iterations")
        args = parser.parse_args()

        if args.nodes:
            try:
                ui_cli = UiCli()

                if not args.start_time and not args.end_time:
                    ui_cli.nodes_overall_live_report(
                        args.sec, args.count, args.sort)
                elif args.start_time and args.end_time:
                    ui_cli.report_time_validator(ui_cli.nodes_overall_time_range_report,
                                                 args.start_time,
                                                 args.end_time,
                                                 args.sec,
                                                 args.sort)
                else:
                    parser.print_usage()
                    print("ERROR: Invalid date: Arguments --start-time and "
                          "--end-time should come together")

            except KeyboardInterrupt:
                print("Narf!")
                exit(0)

        elif args.uvms:
            try:
                ui_cli = UiCli()
                if not args.start_time and not args.end_time:
                    ui_cli.uvms_overall_live_report(args.sec,
                                                    args.count,
                                                    args.sort,
                                                    args.node_name)
                elif args.start_time and args.end_time:
                    ui_cli.report_time_validator(ui_cli.uvms_overall_time_range_report,
                                                 args.start_time,
                                                 args.end_time,
                                                 args.sec,
                                                 args.sort,
                                                 args.node_name)
                else:
                    parser.print_usage()
                    print("ERROR: Invalid date: Arguments --start-time and "
                          "--end-time should come together")

            except KeyboardInterrupt:
                print("Zort!")
                exit(0)

        elif args.export:
            if args.start_time and args.end_time:
                ui_exporter = UiExporter()
                ui_exporter.export_data(
                    args.start_time, args.end_time, args.sec)
            else:
                parser.print_usage()
                print("ERROR: Invalid date: Arguments --start-time and"
                      " --end-time needed by --export argument.")
        elif args.test:
            print("==== TESTING ====")

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

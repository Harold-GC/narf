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

# ~~~ Report fields definitions ~~~
# Arithmos fields are used by the report methods in the reporter classes,
# These fields needs to be mapped by the _get_*_dic() methods in reporters.
# The reason this atributes needs to be mapped is because some are
# transformed, for example "hypervisor_cpu_usage_ppm" is divided by 10000
# and transformed into "hypervisor_cpu_usage_percent".
#
#   node_stat.stats.hypervisor_cpu_usage_ppm / 10000
#                           =
#             hypervisor_cpu_usage_percent
#
# Cli fields are used by the UiCli class in the formater methods and
# describe how the information needs to be displayed on console.
# Keys in Cli fields correspond to the ones in dictionaries returned
# by the _get_*dic() methods in reporters.
#
# +--------------+
# |   Arithmos   | --->  hypervisor_cpu_usage_ppm     ---> 89000
# +--------------+
#       |
#       V
# +--------------+
# | NodeReporter | --->  hypervisor_cpu_usage_percent ---> 89000 / 10000 = 8.9%
# +--------------+
#       |
#       V
# +--------------+>      key:    hypervisor_cpu_usage_percent
# |   UiCli      | --->  header: CPU%
# +--------------+       width:  6    (min width)
#                        align:  >    (aligned right)
#                        format: .2f  (2 decimal float)
#                                      |
#                                      |
#                                      V
#                        +- Console output -------
#                        | $ ./narf.py -n
#                        | 2022/01/16-02:13:04 | Node                   CPU%   [...]
#                        | 2022/01/16-02:13:04 | Prolix1                8.90   [...]
#                        | [...]
#
#
# TODO: Move report fields definitions to a config file.
# TODO: Classes should also be splitted in modules, at least one module
#       for reporters and one for Ui's needs to be created.
# TODO: Think about merging arithmo and CLI stats. This will help in a
#       simple report definitaion language for the framework.
#
# ~~~ ~~~

# ========================================================================
# Definition of Nodes reports.
#
# NODES_CVM_REPORTS_ATRITHMOS_FIELDS is used to complement node reports
# with CVM information.
#
# NODES_*_REPORT_ARITHMOS_FIELDS define arithmos kNode fields for node reports.
#

NODES_CVM_REPORTS_ATRITHMOS_FIELDS = (
    [
        "id", "vm_name", "node_id", "hypervisor_cpu_usage_ppm",
        "hypervisor.cpu_ready_time_ppm", "memory_usage_ppm"
    ]
)

NODES_OVERALL_REPORT_ARITHMOS_FIELDS = (
    [
        "node_name", "id", "hypervisor_cpu_usage_ppm",
        "hypervisor_memory_usage_ppm", "hypervisor_num_iops",
        "controller_num_iops", "num_iops",
        "io_bandwidth_kBps", "avg_io_latency_usecs"
    ]
)

NODES_OVERALL_REPORT_CLI_FIELDS = (
    [
        {"key": "node_name", "header": "Node",
            "width": 20, "align": "<", "format": ".20"},
        {"key": "hypervisor_cpu_usage_percent", "header": "hCPU%",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "hypervisor_memory_usage_percent", "header": "hMEM%",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor_cpu_usage_percent", "header": "cCPU%",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor.cpu_ready_time_percent", "header": "cRDY%",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "cvm_memory_usage_percent", "header": "cMEM%",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "hypervisor_num_iops", "header": "hIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_iops", "header": "cIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "num_iops", "header": "bIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "io_bandwidth_mBps",
            "header": "bB/W[MB]", "width": 8, "align": ">", "format": ".2f"},
        {"key": "avg_io_latency_msecs",
            "header": "bLAT[ms]", "width": 8, "align": ">", "format": ".2f"}
    ]
)

NODES_CONTROLLER_REPORT_ARITHMOS_FIELDS = (
    [
        "node_name", "id",
        "hypervisor_cpu_usage_ppm",
        "hypervisor_memory_usage_ppm",

        "controller_num_iops",
        "controller_num_read_iops",
        "controller_num_write_iops",

        "controller_io_bandwidth_kBps",
        "controller_read_io_bandwidth_kBps",
        "controller_write_io_bandwidth_kBps",

        "controller_avg_io_latency_usecs",
        "controller_avg_read_io_latency_usecs",
        "controller_avg_write_io_latency_usecs"

    ]
)

NODES_CONTROLLER_REPORT_CLI_FIELDS = (
    [
        {"key": "node_name", "header": "Node",
            "width": 20, "align": "<", "format": ".20"},
        {"key": "hypervisor_cpu_usage_percent", "header": "hCPU%",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "hypervisor_memory_usage_percent", "header": "hMEM%",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor_cpu_usage_percent", "header": "cCPU%",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor.cpu_ready_time_percent", "header": "cRDY%",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "cvm_memory_usage_percent", "header": "cMEM%",
            "width": 8, "align": ">", "format": ".2f"},

        {"key": "controller_num_iops", "header": "cIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_read_iops", "header": "cRIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_write_iops", "header": "cWIOPS",
            "width": 8, "align": ">", "format": ".2f"},

        {"key": "controller_io_bandwidth_mBps",
            "header": "cB/W[MB]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "controller_read_io_bandwidth_mBps",
            "header": "cRB/W[MB]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "controller_write_io_bandwidth_mBps",
            "header": "cWB/W[MB]", "width": 9, "align": ">", "format": ".2f"},

        {"key": "controller_avg_io_latency_msecs",
            "header": "cLAT[ms]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "controller_avg_read_io_latency_msecs",
            "header": "cRLAT[ms]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "controller_avg_write_io_latency_msecs",
            "header": "cWLAT[ms]", "width": 9, "align": ">", "format": ".2f"}
    ]
)

NODES_IOPS_REPORT_ARITHMOS_FIELDS = (
    [
        "node_name", "id",
        "hypervisor_cpu_usage_ppm", "hypervisor_memory_usage_ppm",

        "hypervisor_num_iops",
        "hypervisor_num_read_iops", "hypervisor_num_write_iops",

        "controller_num_iops",
        "controller_num_read_iops", "controller_num_write_iops",

        "num_iops",
        "num_read_iops", "num_write_iops"
    ]
)

NODES_IOPS_REPORT_CLI_FIELDS = (
    [
        {"key": "node_name", "header": "Node",
            "width": 20, "align": "<", "format": ".20"},
        {"key": "hypervisor_cpu_usage_percent", "header": "hCPU%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "hypervisor_memory_usage_percent", "header": "hMEM%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor_cpu_usage_percent", "header": "cCPU%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor.cpu_ready_time_percent", "header": "cRDY%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "cvm_memory_usage_percent", "header": "cMEM%",
            "width": 6, "align": ">", "format": ".2f"},


        {"key": "hypervisor_num_iops", "header": "hIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "hypervisor_num_read_iops", "header": "hRIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "hypervisor_num_write_iops", "header": "hWIOPS",
            "width": 8, "align": ">", "format": ".2f"},

        {"key": "controller_num_iops", "header": "cIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_read_iops", "header": "cRIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_write_iops", "header": "cWIOPS",
            "width": 8, "align": ">", "format": ".2f"},

        {"key": "num_iops", "header": "bIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "num_read_iops", "header": "bRIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "num_write_iops", "header": "bWIOPS",
            "width": 8, "align": ">", "format": ".2f"}
    ]
)

NODES_BANDWIDTH_REPORT_ARITHMOS_FIELDS = (
    [
        "node_name", "id",
        "hypervisor_cpu_usage_ppm", "hypervisor_memory_usage_ppm",

        "hypervisor_io_bandwidth_kBps",
        "hypervisor_read_io_bandwidth_kBps",
        "hypervisor_write_io_bandwidth_kBps",

        "controller_io_bandwidth_kBps",
        "controller_read_io_bandwidth_kBps",
        "controller_write_io_bandwidth_kBps",

        "io_bandwidth_kBps",
        "read_io_bandwidth_kBps",
        "write_io_bandwidth_kBps",
    ]
)

NODES_BANDWIDTH_REPORT_CLI_FIELDS = (
    [
        {"key": "node_name", "header": "Node",
            "width": 20, "align": "<", "format": ".20"},
        {"key": "hypervisor_cpu_usage_percent", "header": "hCPU%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "hypervisor_memory_usage_percent", "header": "hMEM%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor_cpu_usage_percent", "header": "cCPU%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor.cpu_ready_time_percent", "header": "cRDY%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "cvm_memory_usage_percent", "header": "cMEM%",
            "width": 6, "align": ">", "format": ".2f"},

        {"key": "hypervisor_io_bandwidth_mBps",
            "header": "hB/W[MB]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "hypervisor_read_io_bandwidth_mBps",
            "header": "hRB/W[MB]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "hypervisor_write_io_bandwidth_mBps",
            "header": "hWB/W[MB]", "width": 9, "align": ">", "format": ".2f"},

        {"key": "controller_io_bandwidth_mBps",
            "header": "cB/W[MB]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "controller_read_io_bandwidth_mBps",
            "header": "cRB/W[MB]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "controller_write_io_bandwidth_mBps",
            "header": "cWB/W[MB]", "width": 9, "align": ">", "format": ".2f"},

        {"key": "io_bandwidth_mBps",
            "header": "B/W[MB]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "read_io_bandwidth_mBps",
            "header": "RB/W[MB]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "write_io_bandwidth_mBps",
            "header": "WB/W[MB]", "width": 9, "align": ">", "format": ".2f"},
    ]
)


NODES_LATENCY_REPORT_ARITHMOS_FIELDS = (
    [
        "node_name", "id",
        "hypervisor_cpu_usage_ppm", "hypervisor_memory_usage_ppm",
        "hypervisor_avg_io_latency_usecs",
        "hypervisor_avg_read_io_latency_usecs",
        "hypervisor_avg_write_io_latency_usecs",
        "controller_avg_io_latency_usecs",
        "controller_avg_read_io_latency_usecs",
        "controller_avg_write_io_latency_usecs",
        "avg_io_latency_usecs",
        "avg_read_io_latency_usecs",
        "avg_write_io_latency_usecs",

    ]
)

NODES_LATENCY_REPORT_CLI_FIELDS = (
    [
        {"key": "node_name", "header": "Node",
            "width": 20, "align": "<", "format": ".20"},
        {"key": "hypervisor_cpu_usage_percent", "header": "hCPU%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "hypervisor_memory_usage_percent", "header": "hMEM%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor_cpu_usage_percent", "header": "cCPU%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "cvm_hypervisor.cpu_ready_time_percent", "header": "cRDY%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "cvm_memory_usage_percent", "header": "cMEM%",
            "width": 6, "align": ">", "format": ".2f"},

        {"key": "hypervisor_avg_io_latency_msecs",
            "header": "hLAT[ms]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "hypervisor_avg_read_io_latency_msecs",
            "header": "hRLAT[ms]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "hypervisor_avg_write_io_latency_msecs",
            "header": "hWLAT[ms]", "width": 9, "align": ">", "format": ".2f"},

        {"key": "controller_avg_io_latency_msecs",
            "header": "cLAT[ms]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "controller_avg_read_io_latency_msecs",
            "header": "cRLAT[ms]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "controller_avg_write_io_latency_msecs",
            "header": "cWLAT[ms]", "width": 9, "align": ">", "format": ".2f"},

        {"key": "avg_io_latency_msecs",
            "header": "LAT[ms]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "avg_read_io_latency_msecs",
            "header": "RLAT[ms]", "width": 9, "align": ">", "format": ".2f"},
        {"key": "avg_write_io_latency_msecs",
            "header": "WLAT[ms]", "width": 9, "align": ">", "format": ".2f"}
    ]
)

# ========================================================================
# Definition of VM reports.
VM_OVERALL_REPORT_ARITHMOS_FIELDS = (
    [
        "vm_name", "id", "node_name", "node_id",
        "hypervisor_cpu_usage_ppm",
        "hypervisor.cpu_ready_time_ppm",
        "memory_usage_ppm", "hypervisor_num_iops",
        "controller_num_iops",
        "controller_io_bandwidth_kBps",
        "controller_avg_io_latency_usecs",
    ]
)

VM_OVERALL_REPORT_CLI_FIELDS = (
    [
        {"key": "vm_name", "header": "VM Name",
            "width": 26, "align": "<", "format": ".20"},
        {"key": "hypervisor_cpu_usage_percent", "header": "CPU%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "hypervisor.cpu_ready_time_percent", "header": "RDY%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "memory_usage_percent", "header": "MEM%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "hypervisor_num_iops", "header": "hIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_iops", "header": "cIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_io_bandwidth_mBps",
            "header": "cB/W[MB]", "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_avg_io_latency_msecs",
            "header": "cLAT[ms]", "width": 8, "align": ">", "format": ".2f"}

    ]
)

VM_IOPS_REPORT_ARITHMOS_FIELDS = (
    [
        "vm_name", "id", "node_name",
        "hypervisor_cpu_usage_ppm", "memory_usage_ppm",

        "hypervisor_num_iops",
        "hypervisor_num_read_iops", "hypervisor_num_write_iops",

        "controller_num_iops",
        "controller_num_read_iops", "controller_num_write_iops",
    ]
)

VM_IOPS_REPORT_CLI_FIELDS = (
    [
        {"key": "vm_name", "header": "Node",
            "width": 26, "align": "<", "format": ".20"},
        {"key": "hypervisor_cpu_usage_percent", "header": "CPU%",
            "width": 6, "align": ">", "format": ".2f"},
        {"key": "memory_usage_percent", "header": "MEM%",
            "width": 6, "align": ">", "format": ".2f"},

        {"key": "hypervisor_num_iops", "header": "hIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "hypervisor_num_read_iops", "header": "hRIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "hypervisor_num_write_iops", "header": "hWIOPS",
            "width": 8, "align": ">", "format": ".2f"},

        {"key": "controller_num_iops", "header": "cIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_read_iops", "header": "cRIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_write_iops", "header": "cWIOPS",
            "width": 8, "align": ">", "format": ".2f"},

    ]
)

# ========================================================================
# Definition of volume_group reports.
VG_OVERALL_REPORT_ARITHMOS_FIELDS = (
    [
        "volume_group_name", "id",
        "num_virtual_disks",
        "controller_num_iops",
        "controller_num_read_iops",
        "controller_num_write_iops",
        "controller_io_bandwidth_kBps",
        "controller_avg_io_latency_usecs"
    ]
)

VG_OVERALL_REPORT_CLI_FIELDS = (
    [
        {"key": "volume_group_name", "header": "VG name",
            "width": 29, "align": "<", "format": ".29"},
        {"key": "num_virtual_disks", "header": "vDiks",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_iops", "header": "IOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_read_iops", "header": "RIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_num_write_iops", "header": "WIOPS",
            "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_io_bandwidth_mBps",
            "header": "cB/W[MB]", "width": 8, "align": ">", "format": ".2f"},
        {"key": "controller_avg_io_latency_msecs",
            "header": "cLAT[ms]", "width": 8, "align": ">", "format": ".2f"}
    ]
)

# ========================================================================


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

    def _stats_unit_conversion(self, entities_dict):
        """
        Receive a list of entity dictionaries with stats and makes the name
        and unit conversion.  Is used to return a dictionary to UIs with the
        stats in desired units and names. For example:

        Arithmos stat memory_usage_ppm is changed to memory_usage_percent, and
        the value is changed from parts per million to percentage.

        It uses the stat names to identify the current unit value and change it
        to an arbitrary desired unit.
        """
        ret = []
        for entity in entities_dict:
            converted_entity = {}
            for key in entity.keys():
                new_key = ""
                if "ppm" in key:
                    new_key = key.replace("ppm", "percent")
                    new_value = entity[key] / 10000
                    converted_entity[new_key] = new_value
                elif "kBps" in key:
                    new_key = key.replace("kBps", "mBps")
                    new_value = entity[key] / 1024
                    converted_entity[new_key] = new_value
                elif "bytes" in key:
                    new_key = key.replace("bytes", "Mbytes")
                    new_value = entity[key] / 1048576
                    converted_entity[new_key] = new_value
                elif "usecs" in key:
                    new_key = key.replace("usecs", "msecs")
                    new_value = entity[key] / 1000
                    converted_entity[new_key] = new_value
                else:
                    new_key = key
                    converted_entity[new_key] = entity[new_key]

                # Set back to -1 if we divided in the previos statements.
                # This is because arithmos returns -1 when there is no data.
                if converted_entity[new_key] < 0:
                    converted_entity[new_key] = -1
            ret.append(converted_entity)

        return ret

    def _get_entity_stats_from_proto(self, entity, field_list):
        """
        Get an entity protobufer and return a dictionary with
        desired fields.
        Missing fields are populated with -1.
        """
        entity_dict = {}

        if hasattr(entity, "stats"):
            stats = entity.stats

            for tmp_stat in stats.DESCRIPTOR.fields:
                if (tmp_stat.name != "common_stats" and
                   tmp_stat.name != "generic_stat_list"):
                    if tmp_stat.name in field_list:
                        entity_dict[tmp_stat.name] = getattr(
                            stats, tmp_stat.name)

            if hasattr(stats, "common_stats"):
                for tmp_common_stat in stats.common_stats.DESCRIPTOR.fields:
                    if tmp_common_stat.name in field_list:
                        entity_dict[tmp_common_stat.name] = getattr(
                            stats.common_stats, tmp_common_stat.name)

            if hasattr(stats, "generic_stat_list"):
                for tmp_generic_stat in stats.generic_stat_list:
                    entity_dict[tmp_generic_stat.stat_name] = tmp_generic_stat.stat_value

        if hasattr(entity, "generic_attribute_list"):
            for tmp_generic_attr in entity.generic_attribute_list:
                name = None
                value = None
                for field, _ in tmp_generic_attr.ListFields():
                    if field.name == "attribute_name":
                        name = str(getattr(tmp_generic_attr, field.name))
                    elif field.name == "attribute_value_str":
                        value = getattr(tmp_generic_attr, str(field.name))
                    elif field.name == "attribute_value_int":
                        value = getattr(tmp_generic_attr, field.name)
                    elif hasattr(generic_attr, "attribute_value_str_list"):
                        value = getattr(tmp_generic_attr, field.name)
                if name is not None and value is not None:
                    entity_dict[name] = value

        # Method returns a dictionary with all fields in field_list,
        # if there is a missing field, populate with -1.
        for field in field_list:
            if not field in entity_dict.keys():
                entity_dict[field] = -1

        return entity_dict

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

        TODO: This is unnecessary, review this method for removal. If so this needs
              to be done in Ui not in reporter.
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

        TODO: This is unnecessary, review this method for removal. If so this needs
              to be done in Ui not in reporter.
        """
        for desired_attribute in desired_attribute_list:
            if desired_attribute not in attributes:
                attributes[desired_attribute] = "-"
        return attributes

    def _sort_entity_dict(self, nodes_stats_dic, sort, default_sort_field="name"):
        """
        Get a list of entities dictionaries and a sort key. The sort key is
        translated into a field using 'self.sort_conversion' and is
        equivalent to an arithmos field. Then the list is sorted based on
        this criteria.

        The conversion dictionary 'self.sort_conversion' needs to be defined in the
        subclasses according to their sorting criteria.
        """
        if sort in self.sort_conversion.keys():
            sort_by = self.sort_conversion[sort]
        else:
            sort_by = self.sort_conversion[default_sort_field]

        # This is because the default sort field "name" is the only alphabetic,
        # other fields are are numeric and needs to be sorted in reverse.
        # TODO: May need to think better about this later.
        if sort_by == self.sort_conversion[default_sort_field]:
            return sorted(nodes_stats_dic,
                          key=lambda node: node[sort_by])
        else:
            return sorted(nodes_stats_dic,
                          key=lambda node: node[sort_by], reverse=True)


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
    """Reports for Nodes."""

    def __init__(self):
        """Class constructor."""
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
                                               field_name_list=["node_name",
                                                                "id"])

    def _get_node_live_stats(self, sort_criteria=None, filter_criteria=None,
                             search_term=None, field_name_list=None):
        """Return node stats in arithmos proto."""
        response = self._get_live_stats(self._ARITHMOS_ENTITY_PROTO,
                                        sort_criteria, filter_criteria,
                                        search_term, field_name_list)
        entity_list = response.entity_list.node
        return entity_list

    def _get_live_stats_dic(self, entity_list, field_list):
        """Return dictionary with node live stats."""
        node_stats_dic = []
        for node_entity in entity_list:
            node_dict = self._get_entity_stats_from_proto(
                node_entity, field_list)
            node_dict["id"] = node_entity.id
            node_dict["node_name"] = str(node_entity.node_name)
            node_stats_dic.append(node_dict)
        return node_stats_dic

    def _get_cvm_live_stats(self, node_id, field_list=[]):
        """Return CVM live stats."""
        vm_reporter = VmReporter()
        filter_criteria = "node_id==" + node_id + ";is_cvm==1"

        ret = vm_reporter._get_vm_live_stats(
            filter_criteria=filter_criteria, field_list=field_list)
        ret = vm_reporter._get_live_stats_dic(ret, field_list)
        return ret[0]

    def _inject_cvm_live_stats(self, nodes):
        """Inject CVM stats into nodes dictionary."""
        ret = []
        for node in nodes:
            cvm = self._get_cvm_live_stats(
                node["id"], field_list=NODES_CVM_REPORTS_ATRITHMOS_FIELDS)

            for cvm_stat in NODES_CVM_REPORTS_ATRITHMOS_FIELDS:
                node["cvm_" + cvm_stat] = (
                    cvm[cvm_stat])
            ret.append(node)
        return ret

    def _live_report(self, field_list, sort="name"):
        """Return dictionary with node and CVM live stats."""
        # Get nodes and stats in arithmos proto format
        entity_list = self._get_node_live_stats(
            field_name_list=field_list,
            filter_criteria="")

        # Convert arithmos proto into dictionary
        ret = self._get_live_stats_dic(entity_list, field_list)

        # Add CVMs stats into node list
        ret = self._inject_cvm_live_stats(ret)

        # Do unit conversion
        ret = self._stats_unit_conversion(ret)
        return self._sort_entity_dict(ret, sort)

    def overall_live_report(self, sort="name"):
        """Return dictionary with nodes overall stats."""
        return self._live_report(NODES_OVERALL_REPORT_ARITHMOS_FIELDS, sort)

    def controller_live_report(self, sort="name"):
        """Return dictionary with nodes overall stats."""
        return self._live_report(NODES_CONTROLLER_REPORT_ARITHMOS_FIELDS, sort)

    def iops_live_report(self, sort="name"):
        """Return dictionary with live nodes IOPS stats."""
        return self._live_report(NODES_IOPS_REPORT_ARITHMOS_FIELDS, sort)

    def bw_live_report(self, sort="name"):
        """Return dictionary with live nodes bandwidth stats."""
        return self._live_report(NODES_BANDWIDTH_REPORT_ARITHMOS_FIELDS, sort)

    def lat_live_report(self, sort="name"):
        """Return dictionary with live nodes bandwidth stats."""
        return self._live_report(NODES_LATENCY_REPORT_ARITHMOS_FIELDS, sort)

    def _get_time_range_stats_dic(self, field_list,
                                  start, end, sampling_interval=30):
        """Return dictionary with node time range stats."""
        nodes_stats_dic = []
        for node_pivot in self.nodes:
            node = {}
            for field in field_list:
                value = self._get_time_range_stat_average(
                    node_pivot.id, field, start, end,
                    sampling_interval
                )
                node[field] = value
            node["node_name"] = str(node_pivot.node_name)
            node["node_id"] = int(node_pivot.id)
            nodes_stats_dic.append(node)
        return nodes_stats_dic

    def _get_cvm_time_range_stats(self, node_id, field_list, start, end):
        """Return CVM time range stats."""
        vm_reporter = VmReporter()
        filter_by = "node_id==" + str(node_id) + ";is_cvm==1"

        vm_list = vm_reporter._get_vm_live_stats(field_list=["vm_name", "id",
                                                             "node_name"],
                                                 filter_criteria=filter_by)
        ret = vm_reporter._get_time_range_stats_dic(
            vm_list, field_list, start, end)
        return ret[0]

    def _inject_cvm_time_range_stats(self, nodes, start, end):
        """Inject CVM stats into nodes dictionary."""
        ret = []
        for node in nodes:
            cvm = self._get_cvm_time_range_stats(
                node["node_id"], NODES_CVM_REPORTS_ATRITHMOS_FIELDS,
                start, end)
            for cvm_stat in NODES_CVM_REPORTS_ATRITHMOS_FIELDS:
                node["cvm_" + cvm_stat] = (
                    cvm[cvm_stat])
            ret.append(node)
        return ret

    def _time_range_report(self, field_list, start, end, sort="name"):
        """Return dictionary with node and CVM time range stats."""
        # Get nodes and stats in arithmos proto format
        entity_list = self._get_time_range_stats_dic(field_list, start, end)

        # Add CVMs stats into node list
        ret = self._inject_cvm_time_range_stats(entity_list, start, end)

        # Do unit conversion
        ret = self._stats_unit_conversion(ret)

        return self._sort_entity_dict(ret, sort)

    def overall_time_range_report(self, start, end, sort="name", nodes=[]):
        """Return dictionary with time range nodes overall stats."""
        return self._time_range_report(NODES_OVERALL_REPORT_ARITHMOS_FIELDS,
                                       start, end, sort)

    def controller_time_range_report(self, start, end, sort="name", nodes=[]):
        """Return dictionary with time range nodes controller stats."""
        return self._time_range_report(NODES_CONTROLLER_REPORT_ARITHMOS_FIELDS,
                                       start, end, sort)

    def iops_time_range_report(self, start, end, sort="name", nodes=[]):
        """Return dictionary with time range node IOPS stats."""
        return self._time_range_report(NODES_IOPS_REPORT_ARITHMOS_FIELDS,
                                       start, end, sort)

    def bw_time_range_report(self, start, end, sort="name", nodes=[]):
        """Return dictionary with time range nodes bandwidth stats."""
        return self._time_range_report(NODES_BANDWIDTH_REPORT_ARITHMOS_FIELDS,
                                       start, end, sort)

    def lat_time_range_report(self, start, end, sort="name", nodes=[]):
        """Return dictionary with time range nodes bandwidth stats."""
        return self._time_range_report(NODES_LATENCY_REPORT_ARITHMOS_FIELDS,
                                       start, end, sort)


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
            "rdy": "hypervisor.cpu_ready_time_percent",
            "mem": "memory_usage_percent",
            "iops": "controller_num_iops",
            "bw": "controller_io_bandwidth_mBps",
            "lat": "controller_avg_io_latency_msecs"
        }

        self.sort_conversion_arithmos = {
            "name": "vm_name",
            "cpu": "-hypervisor_cpu_usage_ppm",
            "rdy": "hypervisor.cpu_ready_time_ppm",
            "mem": "-memory_usage_ppm",
            "iops": "-controller_num_iops",
            "bw": "-controller_io_bandwidth_kBps",
            "lat": "-controller_avg_io_latency_usecs"
        }

    def _get_vm_live_stats(self, sort_criteria=None, filter_criteria=None,
                           search_term=None, field_list=None):
        response = self._get_live_stats(self._ARITHMOS_ENTITY_PROTO,
                                        sort_criteria, filter_criteria,
                                        search_term, field_list)
        entity_list = response.entity_list.vm
        return entity_list

    def _get_live_stats_dic(self, entity_list, field_list):
        """
        Get an entity_list as returned from MasterGetEntitiesStats,
        parse the entities and stats to a dictinary and returns.
        """
        vm_stats_dic = []
        for vm_entity in entity_list:
            vm_dict = self._get_entity_stats_from_proto(vm_entity, field_list)
            vm_dict["id"] = vm_entity.id
            vm_dict["vm_name"] = vm_entity.vm_name.encode('utf-8')
            vm_stats_dic.append(vm_dict)
        return vm_stats_dic

    def _get_time_range_stats_dic(self, entity_list, field_list,
                                  start, end, sampling_interval=30):
        """
        Get an entity_list as returned from MasterGetEntitiesStats,
        parse the entities and stats to a dictinary and returns.
        """
        vm_stats_dic = []
        for vm_pivot in entity_list:
            vm = {}
            for field in field_list:
                value = self._get_time_range_stat_average(
                    vm_pivot.id, field, start, end,
                    sampling_interval
                )
                vm[field] = value
            vm["vm_name"] = vm_pivot.vm_name.encode('utf-8')
            vm["id"] = vm_pivot.id
            vm_stats_dic.append(vm)
        return vm_stats_dic

    def _get_arithmos_sort_field(self, sort, default_sort_field="name"):
        """
        Returns the arithmos field for sort criteria. The sort key is
        translated using 'self.sort_conversion_arithmos' into an arithmos field.

        There is another method _sort_entity_dict() in superclass for sorting.
        The reason we also need arithmos sort criteria is because there is a maximum
        numbers of entities returned by arithmos, if sort_criteria is not indicated
        when calling MasterGetEntitiesStats() there is a risk of missing some of the
        top VMs.

        """
        if sort in self.sort_conversion.keys():
            sort_by_arithmos = self.sort_conversion_arithmos[sort]
        else:
            sort_by_arithmos = self.sort_conversion_arithmos[default_sort_field]

    def _get_arithmos_filter_criteria_string(self, node_names=[],
                                             node_ids=[], power_on=True):
        """Return a valid filter_criteria string for Arithmos."""
        filter_criteria = []

        if power_on:
            filter_criteria.append("power_state==on")

        if node_names:
            node_names_str = ",".join(["node_name==" + node_name
                                       for node_name in node_names])
            filter_criteria.append(node_names_str)

        if node_ids:
            node_ids_str = ",".join(["node_id==" + node_id
                                     for node_id in node_ids])
            filter_criteria.append(node_ids_str)

        filter_str = ""

        if len(filter_criteria) > 0:
            for i in range(len(filter_criteria) - 1):
                filter_str += filter_criteria[i] + ";"
            filter_str += filter_criteria[-1]

        return filter_str

    def _live_report(self, field_list, sort="name",
                     node_names=[], node_ids=[]):
        """Return dictionary with VM live stats."""
        sort_by_arithmos = self._get_arithmos_sort_field(sort)
        filter_str = self._get_arithmos_filter_criteria_string(
            node_names=node_names, node_ids=node_ids)

        entity_list = self._get_vm_live_stats(
            field_list=field_list,
            filter_criteria=filter_str,
            sort_criteria=sort_by_arithmos)

        ret = self._get_live_stats_dic(entity_list,
                                       field_list)
        ret = self._stats_unit_conversion(ret)

        return self._sort_entity_dict(ret, sort)

    def overall_live_report(self, sort="name", node_names=[], node_ids=[]):
        """Return dictionary with VM overall stats.

        Args:
            sort (str): Criteria for sort entities.
            node_names (list): List of nodes names for filter entities.
            node_ids (list: List of node ids for filter entities.

        Return:
            Dictionary with VM entities and live stats as
            specified by the field_list
        """
        return self._live_report(VM_OVERALL_REPORT_ARITHMOS_FIELDS,
                                 sort, node_names, node_ids)

    def iops_live_report(self, sort="name", node_names=[], node_ids=[]):
        """Return dictionary with VM IOPS stats.

        Args:
            sort (str): Criteria for sort entities.
            node_names (list): List of nodes names for filter entities.
            node_ids (list: List of node ids for filter entities.

        Return:
            Dictionary with VM entities and live stats as
            specified by the field_list
        """
        return self._live_report(VM_IOPS_REPORT_ARITHMOS_FIELDS,
                                 sort, node_names, node_ids)

    def _get_vm_time_range_stats(self):
        pass

    def _time_range_report(self, start, end, field_list, sort="name", node_names=[]):
        # sort_by_arithmos = self._get_arithmos_sort_field(sort)
        # filter_by = self._get_arithmos_filter_criteria_string(
        #     node_names, power_on=False)
        #
        # vm_list = self._get_vm_live_stats(field_list=["vm_name", "id",
        #                                               "node_name"],
        #                                   filter_criteria=filter_by,
        #                                   sort_criteria=sort_by_arithmos)
        #
        # generic_attribute_names = ["node_name"]
        # ret = self._get_time_range_stats_dic(vm_list, VM_OVERALL_REPORT_ARITHMOS_FIELDS,
        #                                      start, end)
        # ret = self._stats_unit_conversion(ret)
        #
        # return self._sort_entity_dict(ret, sort)
        pass

    def overall_time_range_report(self, start, end, sort="name", node_names=[]):
        sort_by_arithmos = self._get_arithmos_sort_field(sort)
        filter_by = self._get_arithmos_filter_criteria_string(
            node_names, power_on=False)

        vm_list = self._get_vm_live_stats(field_list=["vm_name", "id",
                                                      "node_name"],
                                          filter_criteria=filter_by,
                                          sort_criteria=sort_by_arithmos)

        generic_attribute_names = ["node_name"]
        ret = self._get_time_range_stats_dic(vm_list, VM_OVERALL_REPORT_ARITHMOS_FIELDS,
                                             start, end)
        ret = self._stats_unit_conversion(ret)

        return self._sort_entity_dict(ret, sort)


class VgReporter(Reporter):
    """Reporter for Volume Groups"""

    def __init__(self):
        Reporter.__init__(self)
        self._ARITHMOS_ENTITY_PROTO = ArithmosEntityProto.kVolumeGroup

        # The reason this conversion exists is because we want to abstract
        # the actual attribute names with something more human friendly
        # and easy to remember. We also want to abstract this from the
        # UI classes.
        self.sort_conversion = {
            "name": "volume_group_name",
            "iops": "controller_num_iops",
            "bw": "controller_io_bandwidth_mBps",
            "lat": "controller_avg_io_latency_msecs",
            "vdisks": "num_virtual_disks"
        }

        self.sort_conversion_arithmos = {
            "name": "volume_group_name",
            "iops": "-controller_num_iops",
            "bw": "-controller_io_bandwidth_kBps",
            "lat": "-controller_avg_io_latency_usecs",
            "vdisks": "-num_virtual_disks"
        }

    def _get_vg_live_stats(self, sort_criteria=None, filter_criteria=None,
                           search_term=None, field_list=None):
        response = self._get_live_stats(self._ARITHMOS_ENTITY_PROTO,
                                        sort_criteria, filter_criteria,
                                        search_term, field_list)
        entity_list = response.entity_list.volume_group
        return entity_list

    def _get_live_stats_dic(self, entity_list, field_list):
        """
        Get an entity_list as returned from MasterGetEntitiesStats,
        parse the entities and stats to a dictinary and returns.
        """
        vg_stats_dic = []
        for vg_entity in entity_list:
            vg_dict = self._get_entity_stats_from_proto(vg_entity, field_list)
            vg_dict["id"] = vg_entity.id
            vg_dict["volume_group_name"] = vg_dict["volume_group_name"].encode(
                'utf-8')
            vg_stats_dic.append(vg_dict)
        return vg_stats_dic

    def _get_time_range_stats_dic(self, entity_list, field_list,
                                  start, end, sampling_interval=30):
        """
        Get an entity_list as returned from MasterGetEntitiesStats,
        parse the entities and stats to a dictinary and returns.
        """
        vg_stats_dic = []
        for vg_pivot in entity_list:
            vg = {}
            for field in field_list:
                value = self._get_time_range_stat_average(
                    vg_pivot.id, field, start, end,
                    sampling_interval
                )
                vg[field] = value
            vg["volume_group_name"] = vg_pivot.volume_group_name.encode(
                'utf-8')
            vg["id"] = vg_pivot.id
            vg_stats_dic.append(vg)
        return vg_stats_dic

    def _get_arithmos_sort_field(self, sort, default_sort_field="name"):
        """
        Returns the arithmos field for sort criteria. The sort key is
        translated using 'self.sort_conversion_arithmos' into an arithmos field.

        There is another method _sort_entity_dict() in superclass for sorting.
        The reason we also need arithmos sort criteria is because there is a maximum
        numbers of entities returned by arithmos, if sort_criteria is not indicated
        when calling MasterGetEntitiesStats() there is a risk of missing some of the
        top VMs.

        """
        if sort in self.sort_conversion.keys():
            sort_by_arithmos = self.sort_conversion_arithmos[sort]
        else:
            sort_by_arithmos = self.sort_conversion_arithmos[default_sort_field]
        return sort_by_arithmos

    def overall_live_report(self, sort="name"):
        """
        Returns a sorted dictionary with volume groups overall stats.
        """
        sort_by_arithmos = self._get_arithmos_sort_field(sort)

        entity_list = self._get_vg_live_stats(
            field_list=VG_OVERALL_REPORT_ARITHMOS_FIELDS,
            sort_criteria=sort_by_arithmos)
        ret = self._get_live_stats_dic(entity_list,
                                       VG_OVERALL_REPORT_ARITHMOS_FIELDS)
        ret = self._stats_unit_conversion(ret)

        return self._sort_entity_dict(ret, sort)


class Ui(object):
    """Display base"""

    def __init__(self):
        self.cluster_reporter = ClusterReporter()
        self.node_reporter = NodeReporter()
        self.vm_reporter = VmReporter()
        self.vg_reporter = VgReporter()
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

    def _report_format_printer(self, field_list, entity_list, str_time):
        """
        """
        header_format_string = ""
        entity_format_string = ""
        for i in range(len(field_list)):
            header_format_string += ("{" +
                                     str(i) + ":" +
                                     field_list[i]["align"] +
                                     str(field_list[i]["width"]) +
                                     "} "
                                     )
            entity_format_string += ("{" +
                                     str(i) + ":" +
                                     field_list[i]["align"] +
                                     str(field_list[i]["width"]) +
                                     field_list[i]["format"] +
                                     "} "
                                     )
        header_list = []
        for i in range(len(field_list)):
            header_list.append(field_list[i]["header"])

        BOLD = '\033[1m'
        END = '\033[0m'
        print((BOLD + str_time + " | " +
               header_format_string + END).format(*header_list))

        for entity in entity_list:
            entity_stat_list = []
            for i in range(len(field_list)):
                stat_key = field_list[i]["key"]
                stat_value = entity[stat_key]
                entity_stat_list.append(stat_value)
            print(str_time + " | " +
                  entity_format_string.format(*entity_stat_list))

        print("")
        return True

    def nodes_live_report(self, sec, count, sort="name",
                          node_names=[], report_type="overall"):
        """
        Print nodes live reports.
        """
        if not sec or sec < 0:
            sec = 0
            count = 1
        else:
            if not count or count < 0:
                count = 1000
        for i in range(count):
            time.sleep(sec)
            time_now = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
            if report_type == "overall":
                entity_list = self.node_reporter.overall_live_report(sort)
                self._report_format_printer(
                    NODES_OVERALL_REPORT_CLI_FIELDS, entity_list, time_now)
            elif report_type == "controller":
                entity_list = self.node_reporter.controller_live_report(sort)
                self._report_format_printer(
                    NODES_CONTROLLER_REPORT_CLI_FIELDS, entity_list, time_now)
            elif report_type == "iops":
                entity_list = self.node_reporter.iops_live_report(sort)
                self._report_format_printer(
                    NODES_IOPS_REPORT_CLI_FIELDS, entity_list, time_now)
            elif report_type == "bw":
                entity_list = self.node_reporter.bw_live_report(sort)
                self._report_format_printer(
                    NODES_BANDWIDTH_REPORT_CLI_FIELDS, entity_list, time_now)
            elif report_type == "lat":
                entity_list = self.node_reporter.lat_live_report(sort)
                self._report_format_printer(
                    NODES_LATENCY_REPORT_CLI_FIELDS, entity_list, time_now)
            else:
                parser.print_usage()
                sys.stderr.write(
                    "ERROR: Report type \"{}\" not implmented for nodes.\n"
                    .format(report_type))
                return False

        return True

    def nodes_time_range_report(self, start_time, end_time, sec=None,
                                sort="name", node_names=[],
                                report_type="overall"):
        """
        Print nodes overall time range report.
        """
        sec = self.time_validator(start_time, end_time, sec)
        if sec > -1:
            step_time = start_time
            delta_time = start_time + datetime.timedelta(seconds=sec)
            while step_time < end_time:
                usec_step = int(step_time.strftime("%s") + "000000")
                usec_delta = int(delta_time.strftime("%s") + "000000")

                if report_type == "overall":
                    entity_list = self.node_reporter.overall_time_range_report(
                        usec_step, usec_delta, sort)
                    self._report_format_printer(
                        NODES_OVERALL_REPORT_CLI_FIELDS,
                        entity_list,
                        step_time.strftime("%Y/%m/%d-%H:%M:%S")
                    )
                elif report_type == "controller":
                    entity_list = self.node_reporter.controller_time_range_report(
                        usec_step, usec_delta, sort)
                    self._report_format_printer(
                        NODES_CONTROLLER_REPORT_CLI_FIELDS,
                        entity_list,
                        step_time.strftime("%Y/%m/%d-%H:%M:%S")
                    )
                elif report_type == "iops":
                    entity_list = self.node_reporter.iops_time_range_report(
                        usec_step, usec_delta, sort)
                    self._report_format_printer(
                        NODES_IOPS_REPORT_CLI_FIELDS,
                        entity_list,
                        step_time.strftime("%Y/%m/%d-%H:%M:%S")
                    )
                elif report_type == "bw":
                    entity_list = self.node_reporter.bw_time_range_report(
                        usec_step, usec_delta, sort)
                    self._report_format_printer(
                        NODES_BANDWIDTH_REPORT_CLI_FIELDS,
                        entity_list,
                        step_time.strftime("%Y/%m/%d-%H:%M:%S")
                    )
                elif report_type == "lat":
                    entity_list = self.node_reporter.lat_time_range_report(
                        usec_step, usec_delta, sort)
                    self._report_format_printer(
                        NODES_LATENCY_REPORT_CLI_FIELDS,
                        entity_list,
                        step_time.strftime("%Y/%m/%d-%H:%M:%S")
                    )
                else:
                    parser.print_usage()
                    sys.stderr.write(
                        "ERROR: Report type \"{}\" not implmented for nodes.\n"
                        .format(report_type))
                    return False

                step_time = delta_time
                delta_time += datetime.timedelta(seconds=sec)
            return True
        return False

    def uvms_live_report(self, sec, count, sort="name",
                         node_names=[], report_type="overall"):
        """
        Print UVMs live report.
        """
        if not sec or sec < 0:
            sec = 0
            count = 1
        else:
            if not count or count < 0:
                count = 1000

        for i in range(count):
            time.sleep(sec)
            time_now = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
            if report_type == "overall":
                entity_list = self.vm_reporter.overall_live_report(
                    sort, node_names)
                self._report_format_printer(
                    VM_OVERALL_REPORT_CLI_FIELDS, entity_list, time_now)
            elif report_type == "iops":
                entity_list = self.vm_reporter.iops_live_report(
                    sort, node_names)
                self._report_format_printer(
                    VM_IOPS_REPORT_CLI_FIELDS, entity_list, time_now)
            else:
                parser.print_usage()
                sys.stderr.write(
                    "ERROR: Report type \"{}\" not implmented for VMs.\n"
                    .format(report_type))
                return False

    def uvms_time_range_report(self, start_time, end_time, sec=None,
                               sort="name", node_names=[],
                               report_type="overall"):
        """
        Print UVMs time range report.
        """
        sec = self.time_validator(start_time, end_time, sec)
        if sec > -1:
            step_time = start_time
            delta_time = start_time + datetime.timedelta(seconds=sec)
            while step_time < end_time:
                usec_step = int(step_time.strftime("%s") + "000000")
                usec_delta = int(delta_time.strftime("%s") + "000000")

                if report_type == "overall":
                    entity_list = self.vm_reporter.overall_time_range_report(
                        usec_step, usec_delta, sort, node_names)
                    self._report_format_printer(
                        VM_OVERALL_REPORT_CLI_FIELDS,
                        entity_list,
                        step_time.strftime("%Y/%m/%d-%H:%M:%S")
                    )
                else:
                    parser.print_usage()
                    sys.stderr.write(
                        "ERROR: Report type \"{}\" not implmented for VMs.\n"
                        .format(report_type))
                    return False

                step_time = delta_time
                delta_time += datetime.timedelta(seconds=sec)

    def vg_live_report(self, sec, count, sort="name",
                       report_type="overall"):
        """
        Print VGs time range report.
        """
        if not sec or sec < 0:
            sec = 0
            count = 1
        else:
            if not count or count < 0:
                count = 1000

        for i in range(count):
            time.sleep(sec)
            time_now = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
            if report_type == "overall":
                entity_list = self.vg_reporter.overall_live_report(sort)
                self._report_format_printer(
                    VG_OVERALL_REPORT_CLI_FIELDS, entity_list, time_now)
            else:
                parser.print_usage()
                sys.stderr.write(
                    "ERROR: Report type \"{}\" not implmented for VGs.\n"
                    .format(report_type))
                return False

    def vg_time_range_report(self, start_time, end_time, sec=None,
                             sort="name", node_names=[],
                             report_type="overall"):
        """
        Print VGs time range report.
        """
        parser.print_usage()
        sys.stderr.write(
            "ERROR: Time range report not implmented for VGs.\n"
            .format(report_type))
        return False


class UiInteractive(Ui):
    """Interactive interface"""

    def __init__(self):
        """
        TODO:
          + Find a better way to get Y for pads, the use of overall_live_report()
            is an unnecessary call to arithmos.
          + It's not necessary to set the size here. Now it's set dynamically in
            the formater function.
        """
        Ui.__init__(self)

        self.stdscr = curses.initscr()

        self.help_widget_pad = curses.newpad(15, 30)
        self.help_widget_pad.border()

        self.nodes_cpu_pad = curses.newpad(
            len(self.node_reporter.overall_live_report()) + 3, 87)
        self.nodes_cpu_pad.border()

        self.nodes_io_pad = curses.newpad(
            len(self.node_reporter.overall_live_report()) + 3, 87)
        self.nodes_io_pad.border()

        self.entities_pad = curses.newpad(
            len(self.vm_reporter.overall_live_report()) + 3, 87)
        self.entities_pad.border()

        self.initialize_colors()
        self.initialize_strings()

        self.key = 0
        self.nodes_sort = "name"
        self.vm_sort = "cpu"
        self.vg_sort = "name"
        self.nodes_pad = "cpu"
        self.entities_pad_to_display = "vm"
        self.help_pad_to_display = "widget"
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
        if screen_x > self.width:
            return False

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

    def get_vg_sort_label(self, sort_key):
        if sort_key == ord('i'):
            return "iops"
        if sort_key == ord('b'):
            return "bw"
        if sort_key == ord('l'):
            return "lat"
        if sort_key == ord('d'):
            return "vdisks"
        return self.vg_sort

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
                    self.active_node = node["id"]
                    return
                elif i == len(self.nodes) - 1 and node["id"] == self.active_node:
                    self.active_node = None
                    return
                elif node["id"] == self.active_node:
                    self.active_node = self.nodes[i + 1]["id"]
                    return

    def toggle_entities_pad(self, toggle_key):
        if toggle_key == ord('g'):
            self.entities_pad_to_display = "vg"
        elif toggle_key == ord('v'):
            self.entities_pad_to_display = "vm"

    def toggle_help_pad(self, toggle_key):
        if toggle_key == ord('h'):
            if self.help_pad_to_display == "none":
                self.help_pad_to_display = "widget"
            else:
                self.help_pad_to_display = "none"

    def handle_key_press(self):
        self.key = self.stdscr.getch()
        self.nodes_sort = self.get_nodes_sort_label(self.key)
        self.vm_sort = self.get_vm_sort_label(self.key)
        self.vg_sort = self.get_vg_sort_label(self.key)
        self.toggle_nodes_pad(self.key)
        self.toggle_active_node(self.key)
        self.toggle_entities_pad(self.key)
        self.toggle_help_pad(self.key)

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

    def render_help_pad(self, y, x):
        self.stdscr.noutrefresh()
        pad_size_y, pad_size_x = self.help_widget_pad.getmaxyx()

        self.help_widget_pad.attron(curses.A_BOLD)
        self.help_widget_pad.addstr(0, 3, " Hotkeys ")
        self.help_widget_pad.attroff(curses.A_BOLD)

        self.help_widget_pad.addstr(1,  1, "~~~ PADs ~~~~~~~~~~~~~~~~~~~")
        self.help_widget_pad.addstr(2,  1, "n:   Toggle node pad")
        self.help_widget_pad.addstr(3,  1, "v:   Virtual machines pad")
        self.help_widget_pad.addstr(4,  1, "g:   Volume group pad")
        self.help_widget_pad.addstr(5,  1, "TAB: Filter VMs by nodes")
        self.help_widget_pad.addstr(7,  1, "~~~ Sort ~~~~~~~~~~~~~~~~~~~")
        self.help_widget_pad.addstr(8,  1, "VM/VG: (c)pu, (r)dy , (m)em")
        self.help_widget_pad.addstr(9,  1, "       (i)ops, (b)/w, (l)at")
        self.help_widget_pad.addstr(10,  1, "       (d)isks")
        self.help_widget_pad.addstr(11,  1, "Nodes: (N)ame, (C)pu, (I)OPS")
        self.help_widget_pad.addstr(12, 1, "       (B)/W, (L)AT")

        self.safe_noautorefresh(self.help_widget_pad, 0, 0, y, x,
                                pad_size_y, pad_size_x)

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

            if node["id"] == self.active_node:
                self.nodes_cpu_pad.attron(curses.color_pair(self.BLACK_WHITE))
                self.nodes_cpu_pad.attron(curses.A_BOLD)

            self.nodes_cpu_pad.addstr(i + 2, 1, "{0:<20} {1:>6.2f} {2:>6.2f}|{3:50}"
                                      .format(node["node_name"][:20],
                                              node["hypervisor_memory_usage_percent"],
                                              node["hypervisor_cpu_usage_percent"],
                                              "#" * rangex))
            if node["id"] == self.active_node:
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

        self.nodes_io_pad.addstr(1, 1, "{0:<20} {1:>6} {2:>6} {3:>8} {4:>8} {5:>8} {6:>8} {7:>6}"
                                 .format("Name",
                                         "MEM%",
                                         "CPU%",
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

            self.nodes_io_pad.addstr(i + 2, 1, "{0:<20} {1:>6.2f} {2:>6.2f} {3:>8} {4:>8} "
                                     "{5:>8} {6:>8.2f} {7:>6.2f}"
                                     .format(node["node_name"][:20],
                                             node["hypervisor_memory_usage_percent"],
                                             node["hypervisor_cpu_usage_percent"],
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

    def _render_entity_list(self, y, x, field_list, entity_list,
                            title, title_sort, highlight_header=False):
        """
        Helper method to print entities lists.
        """
        header_format_string = ""
        entity_format_string = ""
        for i in range(len(field_list)):
            header_format_string += ("{" +
                                     str(i) + ":" +
                                     field_list[i]["align"] +
                                     str(field_list[i]["width"]) +
                                     "} "
                                     )
            entity_format_string += ("{" +
                                     str(i) + ":" +
                                     field_list[i]["align"] +
                                     str(field_list[i]["width"]) +
                                     field_list[i]["format"] +
                                     "} "
                                     )
        header_list = []
        for i in range(len(field_list)):
            header_list.append(field_list[i]["header"])

        self.stdscr.noutrefresh()
        self.entities_pad.clear()

        self.entities_pad = curses.newpad(
            len(entity_list) + 3, len(header_format_string.format(*header_list)) + 3)
        self.entities_pad.border()

        pad_size_y, pad_size_x = self.entities_pad.getmaxyx()

        self.entities_pad.attron(curses.A_BOLD)
        self.entities_pad.addstr(0, 3, " " + title + " ")
        self.entities_pad.attroff(curses.A_BOLD)

        self.entities_pad.addstr(0, pad_size_x - 15, title_sort)

        # Print header
        if highlight_header:
            self.entities_pad.attron(curses.color_pair(self.BLACK_WHITE))
        self.entities_pad.attron(curses.A_BOLD)
        self.entities_pad.addstr(
            1, 2, header_format_string.format(*header_list))
        self.entities_pad.attroff(curses.A_BOLD)
        if highlight_header:
            self.entities_pad.attroff(curses.color_pair(self.BLACK_WHITE))

        # Print entities list
        for line_num in range(0, len(entity_list)):
            entity = entity_list[line_num]
            entity_stat_list = []
            for i in range(len(field_list)):
                stat_key = field_list[i]["key"]
                stat_value = entity[stat_key]
                entity_stat_list.append(stat_value)
            self.entities_pad.addstr(
                line_num + 2, 2, entity_format_string.format(*entity_stat_list))

        self.safe_noautorefresh(self.entities_pad, 0, 0, y, x,
                                pad_size_y, pad_size_x)
        return y + pad_size_y

    def render_vg_list(self, y, x):

        vgs = self.vg_reporter.overall_live_report(self.vg_sort)

        return self._render_entity_list(
            y, x, VG_OVERALL_REPORT_CLI_FIELDS, vgs, "Volume Groups",
            " Sort: {0:<4} ".format(self.vg_sort))

    def render_vm_list(self, y, x):
        if self.active_node:
            vms = self.vm_reporter.overall_live_report(
                self.vm_sort, node_ids=[self.active_node])
            highlight_header = True
        else:
            vms = self.vm_reporter.overall_live_report(
                self.vm_sort)
            highlight_header = False

        return self._render_entity_list(
            y, x, VM_OVERALL_REPORT_CLI_FIELDS, vms, "Virtual Machines",
            " Sort: {0:<4} ".format(self.vm_sort), highlight_header)

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

                # Display help pad
                if self.help_pad_to_display == "widget":
                    self.render_help_pad(2, 88)

                # Display nodes pad
                if current_y_position < self.height:
                    if self.nodes_pad == "cpu":
                        current_y_position = self.render_nodes_cpu_pad(
                            current_y_position, 1)
                    elif self.nodes_pad == "iops":
                        current_y_position = self.render_nodes_io_pad(
                            current_y_position, 1)

                # Display entities pad
                if current_y_position < self.height - 2:
                    if self.entities_pad_to_display == "vm":
                        current_y_position = self.render_vm_list(
                            current_y_position, 1)
                    elif self.entities_pad_to_display == "vg":
                        current_y_position = self.render_vg_list(
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
                              "entityId={v[id]},"
                              "entityName={vm_name},"
                              "exportId={export_id},"
                              "nodeName={v[node_name]} "
                              "hypervisorCpuUsagePercent={v[hypervisor_cpu_usage_percent]:.2f},"
                              "hypervisorCpuReadyTimePercent={v[hypervisor.cpu_ready_time_percent]:.2f},"
                              "memoryUsagePercent={v[memory_usage_percent]:.2f},"
                              "controllerNumIops={v[controller_num_iops]:.0f},"
                              "hypervisorNumIops={v[hypervisor_num_iops]:.0f},"
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
                            help="Nodes activity report")
        parser.add_argument('--node-name', '-N', action='append',
                            help="Filter VMs by node name")
        parser.add_argument('--uvms', '-v', action='store_true',
                            help="VMs activity report")
        parser.add_argument('--volume-groups', '-g', action='store_true',
                            help="Volume Groups activity report")
        parser.add_argument('--sort', '-s',
                            choices=["name", "cpu", "rdy", "mem",
                                     "iops", "bw", "lat", "vdisks"],
                            default="name", help="Sort output")
        parser.add_argument('--report-type', '-t',
                            choices=["controller", "iops", "bw", "lat"],
                            default="overall", help="Report type")
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
        parser.add_argument('--test', action='store_true',
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
                    ui_cli.nodes_live_report(
                        args.sec, args.count, args.sort, report_type=args.report_type)
                elif args.start_time and args.end_time:
                    ui_cli.nodes_time_range_report(args.start_time,
                                                   args.end_time,
                                                   args.sec,
                                                   args.sort,
                                                   report_type=args.report_type)
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
                    ui_cli.uvms_live_report(args.sec,
                                            args.count,
                                            args.sort,
                                            args.node_name,
                                            args.report_type)
                elif args.start_time and args.end_time:
                    ui_cli.uvms_time_range_report(args.start_time,
                                                  args.end_time,
                                                  args.sec,
                                                  args.sort,
                                                  args.node_name,
                                                  report_type=args.report_type)
                else:
                    parser.print_usage()
                    print("ERROR: Invalid date: Arguments --start-time and "
                          "--end-time should come together")

            except KeyboardInterrupt:
                print("Zort!")
                exit(0)

        elif args.volume_groups:
            try:
                ui_cli = UiCli()
                if not args.start_time and not args.end_time:
                    ui_cli.vg_live_report(args.sec,
                                          args.count,
                                          args.sort)
                else:
                    ui_cli.vg_time_range_report(args.start_time,
                                                args.end_time,
                                                args.sec,
                                                args.sort,
                                                args.node_name,
                                                report_type=args.report_type)
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

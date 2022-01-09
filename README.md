# NARF

NARF stands for **N**utanix **A**ctivity **R**eport **F**acilitator.

Inspired in old school UNIX commands like `sar`, `iostat` and `top`, aim to be a simple tool to query and report information from Nutanix clusters performance datasource (arithmos DB). Later will add a feature to export the data into files that can be uploaded to a graphical tool like Grafana.

## Usage
```
usage: narf.py [-h] [--nodes] [--node-name NODE_NAME] [--uvms]
               [--sort {name,cpu,rdy,mem,iops,bw,lat}] [--test]
               [sec] [count]

Report cluster activity

positional arguments:
  sec                   Interval in seconds
  count                 Number of iterations

optional arguments:
  -h, --help            show this help message and exit
  --nodes, -n           Overall nodes activity report
  --node-name NODE_NAME, -N NODE_NAME
                        Filter VMs by node name
  --uvms, -v            Overall user VMs activity report
  --sort {name,cpu,rdy,mem,iops,bw,lat}, -s {name,cpu,rdy,mem,iops,bw,lat}
                        Sort output
  --test, -t            Place holder for testing new features

"When you eliminate the impossible, whatever remains, however improbable, must
be the truth." Spock.
```

## Sample outputs
### Node report
```
nutanix@NTNX-CVM:10.66.38.141:~$ ./narf.py -n 2 2
2021-12-17    Node         CPU%   MEM%   IOPs    B/W    LAT
12:09:15      Prolix1     91.48  55.24     53   2.20   1.18
12:09:15      Prolix2     77.12  83.58     71   2.60   0.53
12:09:15      Prolix3     90.74  73.87     27   1.37   0.93
12:09:15      Prolix4     75.27  96.23    449  18.90   0.35
12:09:15      Prolix5     75.03  93.75     81   2.12   0.20

2021-12-17    Node         CPU%   MEM%   IOPs    B/W    LAT
12:09:18      Prolix1     91.48  55.24     53   2.20   1.18
12:09:18      Prolix2     77.12  83.58     71   2.60   0.53
12:09:18      Prolix3     90.74  73.87     27   1.37   0.93
12:09:18      Prolix4     75.27  96.23     19   1.25   1.28
12:09:18      Prolix5     75.03  93.75     81   2.12   0.20
```

### VM Report sorted by CPU
```
nutanix@NTNX-CVM:10.66.38.141:~$ ./narf.py -v -s cpu | head -30
2021-12-28  VM Name                          CPU%   RDY%   MEM%   IOPs    B/W    LAT
21:23:58    NTNX-xxxxxxxxxxxx-A-CVM        100.00   4.25  67.97      0   0.00   0.00
21:23:58    NTNX-xxxxxxxxxxxx-C-CVM         89.40   0.98  65.31      0   0.00   0.00
21:23:58    W2019                           86.63   0.39   6.63      0   0.00   0.00
21:23:58    NTNX-xxxxxxxxxxxx-D-CVM         54.69   0.19  65.88      0   0.00   0.00
21:23:58    NTNX-Omega-2                    43.84  10.60  51.55     23   0.17   3.71
21:23:58    prolix-pc                       43.43   3.53  71.17    130   1.47   4.66
21:23:58    harold-ocp-cp-2                 38.66  30.62  60.22     34   0.40   2.00
21:23:58    harold-ocp-cp-3                 36.33  30.60  56.76     35   0.45   2.25
21:23:58    NTNX-Prolix2-CVM                35.09   0.27  65.58      0   0.00   0.00
21:23:58    NTNX-Observer                   33.28   0.29  74.06   1040  24.11   1.57
21:23:58    harold-ocp-cp-1                 32.38  29.57  52.85     34   0.42   1.93
21:23:58    NTNX-Omega-1                    30.91   1.61  54.67     30   0.21   6.04
21:23:58    Asterix_and_Obelix_witness      27.42   0.06  57.99     15   0.10   2.62
21:23:58    NKSQL Server 2014 VM            24.66   0.13  35.28    380   5.93   1.33
21:23:58    NTNX-Prolix4-CVM                24.43   0.67  64.28      0   0.00   0.00
21:23:58    NTNX-Omega-3                    17.91   0.04  55.96     25   0.17   2.76
21:23:58    harold-ocp-app-2                15.79   2.52  59.61      1   0.05   3.31
21:23:58    rhtest                          13.90   0.72  54.19      0   0.00   1.21
21:23:58    PostgreSQLVM1                   10.31   1.89  88.60      0   0.00   2.13
21:23:58    vbr                              7.00   0.04  48.36      3   0.04   1.53
21:23:58    ERA                              6.90   0.05  13.75      1   0.02   1.69
21:23:58    SQL2019                          6.80   0.27  27.22      1   0.01   2.23
21:23:58    W2019-UEFI                       6.44   0.09   0.00      0   0.00   0.00
21:23:58    NTNX-FA-FilesAnalyticsProlix     5.59   0.08  57.56      2   0.04   1.82
21:23:58    TD-Win2k12-CV                    5.33   5.06  40.01     10   0.51   2.83
21:23:58    Xendesktop                       5.02   0.32  21.29      3   0.03   1.18
21:23:58    MYSQL_ERA                        4.68   0.51  81.84      0   0.00   6.25
21:23:58    log_server                       4.39   0.52  40.14      7   0.20   2.98
21:23:58    karbon-nh-karbon-099282-k8s-ma   3.93   0.10  22.31      1   0.02   2.48
```

### Filter VMs by node and sort by CPU ready time
```
nutanix@NTNX-CVM:10.66.38.141:~/tmp$ ./narf.py -vN Prolix1 -s rdy 1 1
2021-12-28  VM Name                          CPU%   RDY%   MEM%   IOPs    B/W    LAT
23:24:48    harold-ocp-cp-2                 26.98  11.78  55.86     27   0.25   2.02
23:24:48    harold-ocp-cp-1                 24.38  11.68  48.14     35   0.28   2.35
23:24:48    harold-ocp-cp-3                 25.24  11.61  52.27     28   0.25   2.37
23:24:48    NTNX-Omega-2                    25.06   3.29  51.49     29   0.19   3.46
23:24:48    NTNX-14SM15510002-A-CVM         62.20   2.17  67.74      0   0.00   0.00
23:24:48    harold-ocp-bootstrap             1.60   1.50  17.19      2   0.01   1.31
23:24:48    WinAdminCenter-core              2.31   1.37  41.00      2   0.02   1.76
23:24:48    harold-ocp-svc                   1.23   1.35  16.91      0   0.00   6.90
23:24:48    harold-ocp-app-1                 1.04   0.76  10.29     20   0.11   1.88
23:24:48    pkruchok-w2k12                   0.28   0.68  15.13      0   0.00   0.00
23:24:48    Ubuntu-1                         0.38   0.28  60.83      0   0.00   0.00
23:24:48    tar-c8-1                         1.16   0.28  52.45      0   0.00   0.00
23:24:48    vm-0-2112                        0.41   0.27  44.98      0   0.01   1.04
23:24:48    CentOS8                          0.03   0.19  26.64      0   0.00   0.00
23:24:48    To be Removed - vm-0-211213-03   0.19   0.19  43.87      1   0.02   1.27
23:24:48    CentOS7                          0.13   0.19  10.03      0   0.00   0.00
23:24:48    alpine-HAProxy                   0.74   0.16  10.14      0   0.00   1.18
23:24:48    CentOS_puppet_agent              0.18   0.11  21.98      0   0.00  10.86
```

### Time range node report with one hour sample
```
nutanix@NTNX-CVM:10.66.38.142:~/tmp$ ./narf.py -ns lat -S 2022/01/01-09:00:00 -E 2022/01/01-12:00:00 3600
2022/01/01-09:00:00   Node   CPU%   MEM%   IOPs    B/W    LAT
2022/01/01-09:00:00   Prolix3  95.13  73.91     41   2.04   1.40 
2022/01/01-09:00:00   Prolix4  75.71  96.21     51   2.08   1.27 
2022/01/01-09:00:00   Prolix2  72.12  70.75     36   1.49   1.16 
2022/01/01-09:00:00   Prolix1  86.39  61.39     45   1.91   1.06 
2022/01/01-09:00:00   Prolix5  73.74  88.97    197   6.06   0.66 

2022/01/01-10:00:00   Node   CPU%   MEM%   IOPs    B/W    LAT
2022/01/01-10:00:00   Prolix4  76.45  96.21     52   2.02   1.25 
2022/01/01-10:00:00   Prolix2  71.26  70.76     33   1.37   1.13 
2022/01/01-10:00:00   Prolix3  95.36  73.91     65   2.40   1.05 
2022/01/01-10:00:00   Prolix1  86.20  61.40     44   1.73   0.97 
2022/01/01-10:00:00   Prolix5  73.43  88.98    151   4.97   0.63 

2022/01/01-11:00:00   Node   CPU%   MEM%   IOPs    B/W    LAT
2022/01/01-11:00:00   Prolix4  77.58  96.22     41   1.60   1.34 
2022/01/01-11:00:00   Prolix3  95.39  73.92     56   2.15   1.27 
2022/01/01-11:00:00   Prolix2  72.27  70.77     36   1.37   1.14 
2022/01/01-11:00:00   Prolix1  86.06  61.41     48   1.82   1.01 
2022/01/01-11:00:00   Prolix5  74.20  88.98    181   5.22   0.68 
```

### Time range VM report with single sample sorted by latency
```
nutanix@NTNX-CVM:10.66.38.142:~/tmp$ ./narf.py -vs lat -N prolix1 -S 2022/01/01-09:00:00 -E 2022/01/01-12:00:00
2022/01/01-09:00:00   VM Name                          CPU%   RDY%   MEM%   IOPs    B/W    LAT
2022/01/01-09:00:00   CentOS8                          0.13   0.26  27.39     -1   0.00   9.04 
2022/01/01-09:00:00   harold-ocp-svc                   1.27   1.61  17.82      1   0.00   7.85 
2022/01/01-09:00:00   CentOS7                          0.18   0.22  10.04     -1   0.00   6.77 
2022/01/01-09:00:00   Ubuntu-1.                        0.40   0.30  30.64      1   0.00   5.58 
2022/01/01-09:00:00   xray                             4.26   3.40  36.68      1   0.05   3.91 
2022/01/01-09:00:00   NTNX-Omega-2                    31.07   4.91  55.05     29   0.26   3.49 
2022/01/01-09:00:00   harold-ocp-cp-1                 23.95  14.52  57.99     35   0.48   2.66 
2022/01/01-09:00:00   harold-ocp-cp-3                 23.55  14.70  55.06     34   0.42   2.57 
2022/01/01-09:00:00   harold-ocp-cp-2                 24.08  14.97  57.24     34   0.38   2.49 
2022/01/01-09:00:00   harold-ocp-bootstrap             1.67   1.68  17.94      3   0.02   2.02 
2022/01/01-09:00:00   Citrix-ddc2                      5.25   3.43  53.46      7   0.17   1.99 
2022/01/01-09:00:00   harold-ocp-app-1                 1.15   1.34  10.62     16   0.08   1.88 
2022/01/01-09:00:00   WinAdminCenter-core              2.59   1.26  42.21      2   0.02   1.86 
2022/01/01-09:00:00   pkruchok-w2k12                   0.41   0.82  17.83      1   0.00   1.79 
2022/01/01-09:00:00   alpine-HAProxy                   0.78   0.23  10.15     -1   0.00   1.71 
2022/01/01-09:00:00   vm-0-2112                        0.35   0.31  45.15      1   0.02   1.42 
2022/01/01-09:00:00   tar-c8-1                         0.07   0.08  18.48     -1  -0.00  -0.00 
2022/01/01-09:00:00   NTNX-xxxxxxxxxxxx-A-CVM         62.35   2.57  69.67     -1  -0.00  -0.00 
```

### Interactive mode (top like interface)

<img src="https://user-images.githubusercontent.com/52970459/147422400-2ced603b-d3b1-49ed-a6dd-4068668d2308.jpg" alt="narf_interactive" style="width: 550px;">

## Design

Reporter classes abstract the datasource from the UI classes. Reporter classes are in charge of collect stats from the cluster datasource (Arithmos) and pass the information to UI classes in form of simple native data structures (Python arrays and dictionaries). In this way, if the datasource is changed later (for example from Arithmos to IDF) there will be no need to modify the Ui classes, it will only be needed to change the Reporter classes.

The ```Ui``` super class will hold the attributes that links to all reporters but will not implement any method for presenting information (it's an interface), this assume every UI subclass will need every reporter. Ui subclasses will implement neccesary methods to display information accordingly making use of reporters defined in the super class.

As for the Reporter classes the relationship between super and sub classes and the methods they need to implement is slightly more complicated because the way data is returned from Arithmos. Wherever possible one should prefer to implement a method in the superclass; breakdown a method so that the generic part of the code is moved to the super class while leaving the specifics to entity reporter is a valid resource, as seen in the method ```_get_live_stats()``` in super class ```Reporter``` which is used by ```_get_node_live_stats()``` in the ```NodeReporter``` and ```_get_vm_live_stats()``` in the ```VmReporter``` sub classes (This is aligned with the principles of avoiding code duplication and procuring easy maintenance). More reporters will be needed as more reports for different entities are added, e.g ```VdiskReporter```.

![narf_uml](https://user-images.githubusercontent.com/52970459/147408692-5d58b9f6-593f-4ebc-b818-305c892a6cca.png)

## Exporter schema definition

For the exporter feature NARF create line protocol files that can be imported to InfluxDB. Each entity type has an schema. All schemas have the following tags to be able to differentiate the collection and cluster where they come from: _exportId_, _clusterId_ and _clusterName_, this means all datapoints for all schemas in a collection will have the same value for these three tags. Another two common tags _entityId_ and _entityName_ enable the unequivocal identification of each entity, all datapoints for a given entity will have the same values for these tags. It is through the measurement name that entity type can be identified.

A datapoint looks like this:

```
   node,exportId=0,clusterId=20986,clusterName=Prolix,entityId=1234,entityName=Prolix1 hypervisorCpuUsagePercent=85.88 ... 1641405558000000000
   ---- --------------------------------------------- -------------------------------- -------------------------------->   -------------------
    |                       |                                          |                               |                            |
Measurement     Collection and cluster tags                       Entity tags                     Field keys                    Timestamp

```

This schema has been defined following best practices documented here:

https://docs.influxdata.com/influxdb/v2.1/write-data/best-practices/schema-design/

### Node schema

__Schema definition:__

+ Measurement: node
+ Tag key: exportId
+ Tag key: clusterId
+ Tag key: clusterName
+ Tag key: entityId
+ Tag key: entityName
+ Field key: hypervisorCpuUsagePercent
+ Field key: hypervisorMemoryUsagePercent
+ Field key: controllerNumIops
+ Field key: hypervisorNumIops
+ Field key: numIops
+ Field key: ioBandwidthMBps
+ Field key: avgIoLatencyMsecs

__Example__

This sample:
```
                      Node                   CPU%   MEM%    cIOPs    hIOPs     IOPs  B/W[MB]  LAT[ms]
2022/01/05-10:00:00   Prolix1               85.88  59.91   163.32    -1.00    62.00     3.01     1.01
2022/01/05-11:00:00   Prolix1               86.39  59.91   158.04    -1.00    70.00     2.95     1.10
2022/01/05-12:00:00   Prolix1               86.46  59.92   177.65    -1.00   160.00     5.08     1.14
```

Translate in this line protocol:
```
node,exportId=0,clusterId=20986,clusterName=Prolix,entityId=1234,entityName=Prolix1 hypervisorCpuUsagePercent=85.88,hypervisorMemoryUsagePercent=59.91,controllerNumIops=163.32,hypervisor_num_iops=-1.00,numIops=62.00,ioBandwidthMBps=3.01,avgIoLatencyMsecs=1.01 1641405558000000000
node,exportId=0,clusterId=20986,clusterName=Prolix,entityId=1234,entityName=Prolix1 hypervisorCpuUsagePercent=86.39,hypervisorMemoryUsagePercent=59.91,controllerNumIops=158.04,hypervisor_num_iops=-1.00,numIops=70.00,ioBandwidthMBps=2.95,avgIoLatencyMsecs=1.10 1641409164000000000
node,exportId=0,clusterId=20986,clusterName=Prolix,entityId=1234,entityName=Prolix1 hypervisorCpuUsagePercent=86.46,hypervisorMemoryUsagePercent=59.92,controllerNumIops=177.65,hypervisor_num_iops=-1.00,numIops=160.00,ioBandwidthMBps5.08,avgIoLatencyMsecs=1.14 1641412770000000000
```

### VM Schema

__Schema definition:__

- Measurement: vm
- Tag key: clusterId
- Tag key: clusterName
- tag key: entityId
- Tag key: entityName
- Tag key: exportId
- Tag key: nodeName
- Field key: hypervisorCpuUsagePercent
- Field key: hypervisorCpuReadyTimePercent
- Field key: memoryUsagePercent
- Field key: controllerNumIops
- Field key: hypervisorNumIops
- Field key: numIops
- Field key: controllerIoBandwidthMBps
- Field key: controllerAvgIoLatencyMsecs

__Example__

This sample:
```
                      VM Name                          CPU%   RDY%   MEM%  cIOPs  hIOPs   IOPs  B/W[MB]  LAT[ms]
2022/01/03-09:00:00   harold-ocp-cp-1                 24.36  15.48  63.02     33     -1     -1     0.47     2.81
2022/01/03-10:00:00   harold-ocp-cp-1                 23.70  14.61  64.03     33     -1     -1     0.45     2.79
2022/01/03-11:00:00   harold-ocp-cp-1                 25.24  16.87  61.20     34     -1     -1     0.48     2.86
```

Translate in this line protocol:
```
vm,clusterId=20986,clusterName=Prolix,entityId=98765,entityName=harold-ocp-cp-1,exportId=0,nodeName=Prolix1 hypervisorCpuUsagePercent=24.36,hypervisorCpuReadyTimePercent=15.48,memoryUsagePercent=63.02,controllerNumIops=33,hypervisorNumIops=-1,numIops=-1,controllerIoBandwidthMBps=0.47,controllerAvgIoLatencyMsecs=2.81 1641405558000000000
vm,clusterId=20986,clusterName=Prolix,entityId=98765,entityName=harold-ocp-cp-1,exportId=0,nodeName=Prolix1 hypervisorCpuUsagePercent=23.70,hypervisorCpuReadyTimePercent=14.61,memoryUsagePercent=64.03,controllerNumIops=33,hypervisorNumIops=-1,numIops=-1,controllerIoBandwidthMBps=0.45,controllerAvgIoLatencyMsecs=2.79 1641409164000000000
vm,clusterId=20986,clusterName=Prolix,entityId=98765,entityName=harold-ocp-cp-1,exportId=0,nodeName=Prolix1 hypervisorCpuUsagePercent=25.24,hypervisorCpuReadyTimePercent=16.87,memoryUsagePercent=61.20,controllerNumIops=34,hypervisorNumIops=-1,numIops=-1,controllerIoBandwidthMBps=0.48,controllerAvgIoLatencyMsecs=2.86 1641412770000000000
```

## Advantages
 - Provide easy access to cluster performance activity in any use case where access to the web interface via browser is not available.
 - NARF allows to select a refresh rate specified in seconds from CLI (this will be added to interactive as well), this is timely way to look at cluster activity.
 - For people familiarized with UNIX/Linux environments who prefer CLI than UI, NARF is a nice altenative to the web interface.

## Limitations
 - For live reports it only displays running VMs. Assuming stopped VMs has no impact on cluster performance.
 - Historic reports doesn't filter by running VMs, but it doesn't account for VM migrations. This is, at the moment for historic reports a VM is listed in the host where is currently running.
 - Display a maximum of 252 VMs. This is the max number of entities that Arithmos query returns.

## arithmos_cli case and why narf
```arithmos_cli``` provide quite some flexibility for different types of queries, while this is very powerfull, data is not presented in a human friendly way making it difficult to analyze, and command parameters tends to be complex and hard to remember for most day to day tasks. ```narf``` is not as comprehensive as arithmos, it just has a handfull of genral purpose reports with a small set of paramters to easy remembering, data is tabulated to make it easy to analyze, filter and transform piping to traditional UNIX/Linux commands. 

## Changelog
Splitting tasks/features according to each interface, some taks intertwine between interfaces but it should be fine, I'm putting them where are more relevant.

### Todo
- CLI interface - Eveything for inLine outputs
  - [ ] Add name filtering in node report (-N argument)
- Interactive interface - top like interface
  - [ ] VM specific report - implement a pad with VM cpu/rdy/mem/controller iops, etc, plus vDisks.
  - [ ] Add capability to change refresh rate.
- Data exporter - Time range report, to be able to query historical data and export to files.
  - [ ] Nodes time range report
  - [ ] VM time range report
  - [ ] Define and implement export files. Probably in JSON format. 


### In Progress
- CLI interface - Eveything for inLine outputs
  - [ ] Zort
- Interactive interface - top like interface
  - [ ] Add CPU ready time to overall VM report.
  - [ ] Sort VMs
- Data exporter - Time range report, to be able to query historical data and export to files.
  - [ ] Zort

### Done ✓
- CLI interface - Eveything for inLine outputs
  - [X] Display only running VMs.
  - [x] CLI sort node and vm report by cpu, mem, etc @harold Dec 26, 2021
  - [x] CLI vm report @harold Dec 25, 2021
  - [x] CLI node report @harold Dec 17, 2021
- Interactive interface - top like interface
  - [X] Add VM list @harold Dec 27, 2021
  - [x] Node CPU graph @harold Dec 19, 2021
- Data exporter - Time range report, to be able to query historical data and export to files.
  - [x] Zort

## Why narf?
I had almost decided to change the name from `sre_perf` to `nar` for a while, to make it sound more UNIX like (I thougth about `nstat` but that's already in use), then one day it start lingering in my head as `narf`, that's when I remembered about _Pinky and The Brain_... the sound "_just say narf_" is some sort of "_jacuna matata_" from Pinky, the reflection of The Brain just before the song is quite cliche but I still believe with a deep meaning.

Initially the letter ***F*** had no meaning, and it was there just to make the command sounds fun (fun things are memorable, more easy to remember), then a friend suggested ***F***acilitator and I found it quite convenient.

[![narf](https://user-images.githubusercontent.com/52970459/147395459-03f77395-12cb-429a-a7fa-0b773353e7b6.jpg)](https://www.youtube.com/watch?v=lZBQ0tXA-QM)

> "So what if the numbers don't make sense on a chart?
>
> Who said you've got to be smart?
> 
> Paint your nose, chill some flan
> 
> And remember to pre-grease the pan"

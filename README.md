# NARF

NARF stands for **N**utanix **A**ctivity **R**eport **F**acilitator.

Inspired in old school UNIX commands like `sar`, `iostat` and `top`, aim to be a simple tool to query and report information from Nutanix clusters performance datasource (arithmos DB). Later will add a feature to export the data into files that can be uploaded to a graphical tool like Grafana.

## Usage
```
usage: narf.py [-h] [--nodes] [--node-name NODE_NAME] [--uvms]
               [--sort {name,cpu,rdy,mem,iops,bw,lat}]
               [-start-time START_TIME] [-end-time END_TIME] [--export]
               [--test]
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
  -start-time START_TIME, -S START_TIME
                        Start time in format YYYY/MM/DD-hh:mm:ss. Specified in
                        local time.
  -end-time END_TIME, -E END_TIME
                        End time in format YYYY/MM/DD-hh:mm:ss. Specified in
                        local time
  --export, -e          Export data to files in line protocol
  --test, -t            Place holder for testing new features

"When you eliminate the impossible, whatever remains, however improbable, must
be the truth." Spock.
```

## Sample outputs
### Node report
```
nutanix@NTNX-CVM:10.66.38.141:~$ ./narf.py -n 2 2
2022-01-12  Node      CPU%   MEM%    cIOPs    hIOPs     IOPs  B/W[MB]  LAT[ms]
00:00:16    Prolix1  89.15  65.97   248.00     0.00    57.00     2.78     0.84 
00:00:16    Prolix2  65.94  81.68   120.00     0.00    58.00     3.17     0.96 
00:00:16    Prolix3  97.78  96.28   336.00     0.00   133.00     6.79     2.44 
00:00:16    Prolix4  86.37  95.47  1623.00     0.00    48.00     1.77     1.07 
00:00:16    Prolix5  51.88  65.00    56.00     0.00   323.00    11.08     0.34 

2022-01-12  Node      CPU%   MEM%    cIOPs    hIOPs     IOPs  B/W[MB]  LAT[ms]
00:00:18    Prolix1  89.15  65.97   248.00     0.00    57.00     2.78     0.84 
00:00:18    Prolix2  65.94  81.68   120.00     0.00    58.00     3.17     0.96 
00:00:18    Prolix3  97.78  96.28   336.00     0.00   133.00     6.79     2.44 
00:00:18    Prolix4  86.37  95.47  1561.00     0.00    99.00     7.71     1.85 
00:00:18    Prolix5  51.88  65.00    56.00     0.00   323.00    11.08     0.34 

```

### VM Report sorted by CPU
```
nutanix@NTNX-CVM:10.66.38.141:~$ ./narf.py -v -s cpu | head -30
2022-01-12  VM Name                          CPU%   RDY%   MEM%  cIOPs  hIOPs   IOPs  B/W[MB]  LAT[ms]
00:00:53    albert-W2019                    91.75   0.07   6.63      0      0      0     0.00     0.00 
00:00:53    NTNX-14SM15510002-C-CVM         74.67   4.74  66.85      0      0      0     0.00     0.00 
00:00:53    Asterix_and_Obelix_witness      69.52   0.00  78.98     38      0      0     0.60     5.27 
00:00:53    NTNX-Prolix4-CVM                69.36   2.53  70.63      0      0      0     0.00     0.00 
00:00:53    NTNX-14SM15510002-A-CVM         52.53   3.43  68.03      0      0      0     0.00     0.00 
00:00:53    NTNX-13SM31310001-D-CVM         39.46   0.07  70.01      0      0      0     0.00     0.00 
00:00:53    TD-Win2k12-CV                   36.70  80.89  42.24      5      0      0     0.04     2.07 
00:00:53    prolix-pc                       35.61  83.11  73.10    203      0      0     5.10     3.75 
00:00:53    MM-Windows                      32.37   3.51  28.58    300      0      0     3.39     2.13 
00:00:53    NTNX-Omega-2                    31.27   4.61  61.51     47      0      0     0.34     3.21 
00:00:53    To be Removed - NTNX-arlind-1   30.37   5.59  49.55     40      0      0     0.30     4.89 
00:00:53    Daniil_rhtest                   30.36   1.93  54.99      7      0      0     0.08     1.58 
00:00:53    NTNX-Omega-1                    25.24  62.75  65.21     30      0      0     0.22     4.29 
00:00:53    To be Removed - NTNX-arlind-3   24.47  63.93  54.87     23      0      0     0.16     7.29 
00:00:53    harold-ocp-cp-1                 24.46  14.51  66.12     39      0      0     0.51     2.34 
00:00:53    harold-ocp-cp-2                 23.13  15.05  58.88     36      0      0     0.44     2.42 
00:00:53    harold-ocp-cp-3                 22.86  14.93  59.56     57      0      0     0.69     3.72 
00:00:53    NTNX-Prolix2-CVM                22.62   0.49  71.08      0      0      0     0.00     0.00 
00:00:53    Janagan_PostgreSQLVM1           15.91   4.01  91.10      0      0      0     0.00    15.61 
00:00:53    NTNX-Omega-3                    15.04   0.09  66.35     49      0      0     0.36     2.85 
00:00:53    harold-ocp-app-2                13.76  47.22  70.56      0      0      0     0.04     3.72 
00:00:53    NTNX-Observer                   13.03   1.39  99.74   1031      0      0    32.62     1.48 
00:00:53    To be Removed - NTNX-arlind-2   12.63   0.13  46.61     31      0      0     0.22     4.77 
00:00:53    JanaganSQL2019                  11.93   1.73  44.68      2      0      0     0.02     1.65 
00:00:53    Xendesktop                       9.07  54.00  27.12      2      0      0     0.02     2.28 
00:00:53    Janagan-ERA                      9.02  28.33  13.33      1      0      0     0.01     2.34 
00:00:53    sergei_era_01                    7.95   2.36  12.59      1      0      0     0.01     2.50 
00:00:53    pavel-vbr                        7.02   0.05  51.57      2      0      0     0.03     1.35 
00:00:53    Janagan_MYSQL_ERA                6.67   1.31  82.09      0      0      0     0.00     7.01
```

### Filter VMs by node and sort by CPU ready time
```
nutanix@NTNX-CVM:10.66.38.141:~/tmp$ ./narf.py -vN Prolix1 -s rdy 1 1
2022-01-12  VM Name                         CPU%   RDY%   MEM%  cIOPs  hIOPs   IOPs  B/W[MB]  LAT[ms]
00:02:23    harold-ocp-cp-2                17.23  18.09  58.93     28      0      0     0.40     3.64 
00:02:23    harold-ocp-cp-3                16.50  16.72  59.49     26      0      0     0.38     4.45 
00:02:23    harold-ocp-cp-1                17.31  16.35  66.30     27      0      0     0.37     2.83 
00:02:23    NTNX-Omega-2                   20.31   6.16  61.60     25      0      0     0.19     6.25 
00:02:23    To be Removed - NTNX-arlind-1  15.70   5.98  49.76     18      0      0     0.13     7.28 
00:02:23    user2                           4.13   5.11  52.67      0      0      0     0.00     3.23 
00:02:23    Anas-Citrix-ddc2                3.56   3.31  58.58      3      0      0     0.03     2.24 
00:02:23    NTNX-14SM15510002-A-CVM        44.81   3.18  69.62      0      0      0     0.00     0.00 
00:02:23    user3                           0.66   2.71  70.39      0      0      0     0.00     1.66 
00:02:23    harold-ocp-bootstrap            1.27   2.17  19.69      2      0      0     0.01     1.98 
00:02:23    ioan-WinAdminCenter-core        1.53   1.78  44.18      2      0      0     0.02     2.38 
00:02:23    harold-ocp-svc                  0.83   1.74  19.14      0      0      0     0.00    10.43 
00:02:23    harold-ocp-app-1                0.64   1.38  10.51     12      0      0     0.06     2.17 
00:02:23    tar-c8-1                        0.80   0.89  55.93      2      0      0     0.01     3.52 
00:02:23    ioan-alpine-HAProxy             0.53   0.67  10.13      0      0      0     0.00     1.64 
00:02:23    Nemanja_Ubuntu-1                0.28   0.55  33.60      0      0      0     0.00     0.00 
00:02:23    Kirill-CentOS8                  0.29   0.39  41.28      0      0      0     0.00     1.90 
00:02:23    narf_influx                     0.16   0.26   9.57      0      0      0     0.00     1.77 
00:02:23    Pavel.CentOS7                   0.09   0.21  10.52      0      0      0     0.00     2.75 
```

### Time range node report with one hour sample
```
nutanix@NTNX-CVM:10.66.38.142:~/tmp$ ./narf.py -ns lat -S 2022/01/01-09:00:00 -E 2022/01/01-12:00:00 3600
2022/01/01-09:00:00   Node                   CPU%   MEM%    cIOPs    hIOPs     IOPs  B/W[MB]  LAT[ms]
2022/01/01-09:00:00   Prolix3               95.13  73.91   173.26    -1.00    41.00     2.04     1.40 
2022/01/01-09:00:00   Prolix4               75.71  96.21  1213.31    -1.00    51.00     2.08     1.27 
2022/01/01-09:00:00   Prolix2               72.12  70.75    46.14    -1.00    36.00     1.49     1.16 
2022/01/01-09:00:00   Prolix1               86.39  61.39   168.86    -1.00    45.00     1.91     1.06 
2022/01/01-09:00:00   Prolix5               73.74  88.97   646.31    -1.00   197.00     6.06     0.66 

2022/01/01-10:00:00   Node                   CPU%   MEM%    cIOPs    hIOPs     IOPs  B/W[MB]  LAT[ms]
2022/01/01-10:00:00   Prolix4               76.45  96.21  1331.34    -1.00    52.00     2.02     1.25 
2022/01/01-10:00:00   Prolix2               71.26  70.76    45.54    -1.00    33.00     1.37     1.13 
2022/01/01-10:00:00   Prolix3               95.36  73.91   186.78    -1.00    65.00     2.40     1.05 
2022/01/01-10:00:00   Prolix1               86.20  61.40   168.97    -1.00    44.00     1.73     0.97 
2022/01/01-10:00:00   Prolix5               73.43  88.98   684.89    -1.00   151.00     4.97     0.63 

2022/01/01-11:00:00   Node                   CPU%   MEM%    cIOPs    hIOPs     IOPs  B/W[MB]  LAT[ms]
2022/01/01-11:00:00   Prolix4               77.58  96.22  1419.55    -1.00    41.00     1.60     1.34 
2022/01/01-11:00:00   Prolix3               95.39  73.92   192.05    -1.00    56.00     2.15     1.27 
2022/01/01-11:00:00   Prolix2               72.27  70.77    47.08    -1.00    36.00     1.37     1.14 
2022/01/01-11:00:00   Prolix1               86.06  61.41   174.47    -1.00    48.00     1.82     1.01 
2022/01/01-11:00:00   Prolix5               74.20  88.98   646.07    -1.00   181.00     5.22     0.68 
```

### Time range VM report with single sample sorted by latency
```
nutanix@NTNX-CVM:10.66.38.142:~/tmp$ ./narf.py -vs lat -N prolix1 -S 2022/01/01-09:00:00 -E 2022/01/01-12:00:00
2022/01/01-09:00:00   VM Name                          CPU%   RDY%   MEM%  cIOPs  hIOPs   IOPs  B/W[MB]  LAT[ms]
2022/01/01-09:00:00   Kirill-CentOS8                   0.13   0.26  27.39     -1     -1     -1     0.00     9.04 
2022/01/01-09:00:00   harold-ocp-svc                   1.27   1.61  17.82      1     -1     -1     0.00     7.85 
2022/01/01-09:00:00   Pavel.CentOS7                    0.18   0.22  10.04     -1     -1     -1     0.00     6.77 
2022/01/01-09:00:00   Nemanja_Ubuntu-1                 0.40   0.30  30.64      1     -1     -1     0.00     5.58 
2022/01/01-09:00:00   NTNX-Omega-2                    31.07   4.91  55.05     29     -1     -1     0.26     3.49 
2022/01/01-09:00:00   harold-ocp-cp-1                 23.95  14.52  57.99     35     -1     -1     0.48     2.66 
2022/01/01-09:00:00   harold-ocp-cp-3                 23.55  14.70  55.06     34     -1     -1     0.42     2.57 
2022/01/01-09:00:00   harold-ocp-cp-2                 24.08  14.97  57.24     34     -1     -1     0.38     2.49 
2022/01/01-09:00:00   harold-ocp-bootstrap             1.67   1.68  17.94      3     -1     -1     0.02     2.02 
2022/01/01-09:00:00   Anas-Citrix-ddc2                 5.25   3.43  53.46      7     -1     -1     0.17     1.99 
2022/01/01-09:00:00   harold-ocp-app-1                 1.15   1.34  10.62     16     -1     -1     0.08     1.88 
2022/01/01-09:00:00   ioan-WinAdminCenter-core         2.59   1.26  42.21      2     -1     -1     0.02     1.86 
2022/01/01-09:00:00   ioan-alpine-HAProxy              0.78   0.23  10.15     -1     -1     -1     0.00     1.71 
2022/01/01-09:00:00   user3                           -0.00  -0.00  -0.00     -1     -1     -1    -0.00    -0.00 
2022/01/01-09:00:00   user2                           -0.00  -0.00  -0.00     -1     -1     -1    -0.00    -0.00 
2022/01/01-09:00:00   narf_influx                     -0.00  -0.00  -0.00     -1     -1     -1    -0.00    -0.00 
2022/01/01-09:00:00   To be Removed - NTNX-arlind-1   -0.00  -0.00  -0.00     -1     -1     -1    -0.00    -0.00 
2022/01/01-09:00:00   tar-c8-1                         0.07   0.08  18.48     -1     -1     -1    -0.00    -0.00 
2022/01/01-09:00:00   NTNX-14SM15510002-A-CVM         62.35   2.57  69.67     -1     -1     -1    -0.00    -0.00 
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
  - [ ] Zort 


### In Progress
- CLI interface - Eveything for inLine outputs
  - [ ] Add read/write fields for lat,bw and iops. Maybe and extended report option?
- Interactive interface - top like interface
  - [ ] Add the hability to filter VMs by hosts. With tab key.
- Data exporter - Time range report, to be able to query historical data and export to files.
  - [ ] Work on InfluxDB queries.

### Done ✓
- CLI interface - Eveything for inLine outputs
  - [X] Display only running VMs. Dec 28, 2021
  - [x] CLI sort node and vm report by cpu, mem, etc @harold Dec 26, 2021
  - [x] CLI vm report @harold Dec 25, 2021
  - [x] CLI node report @harold Dec 17, 2021
- Interactive interface - top like interface
  - [X] Add VM list @harold Dec 27, 2021
  - [x] Node CPU graph @harold Dec 19, 2021
  - [X] Sort VMs @harold Dec 28, 2021
  - [X] Add CPU ready time to overall VM report @harold Dec 29, 2021
- Data exporter - Time range report, to be able to query historical data and export to files.
  - [X] Nodes time range report @harold Jan 9, 2022
  - [X] VM time range report @harold Jan 9, 2022
  - [X] Define export files in line protocol format @harold Jan 9, 2022

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

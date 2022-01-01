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

### Interactive mode (top like interface)

<img src="https://user-images.githubusercontent.com/52970459/147422400-2ced603b-d3b1-49ed-a6dd-4068668d2308.jpg" alt="narf_interactive" style="width: 550px;">

## Design

Reporter classes abstract the datasource from the UI classes. Reporter classes are in charge of collect stats from the cluster datasource (Arithmos) and pass the information to UI classes in form of simple native data structures (Python arrays and dictionaries). In this way, if the datasource is changed later (for example from Arithmos to IDF) there will be no need to modify the Ui classes, it will only be needed to change the Reporter classes.

The ```Ui``` super class will hold the attributes that links to all reporters but will not implement any method for presenting information (it's an interface), this assume every UI subclass will need every reporter. Ui subclasses will implement neccesary methods to display information accordingly making use of reporters defined in the super class.

As for the Reporter classes the relationship between super and sub classes and the methods they need to implement is slightly more complicated because the way data is returned from Arithmos. Wherever possible one should prefer to implement a method in the superclass; breakdown a method so that the generic part of the code is moved to the super class while leaving the specifics to entity reporter is a valid resource, as seen in the method ```_get_live_stats()``` in super class ```Reporter``` which is used by ```_get_node_live_stats()``` in the ```NodeReporter``` and ```_get_vm_live_stats()``` in the ```VmReporter``` sub classes (This is aligned with the principles of avoiding code duplication and procuring easy maintenance). More reporters will be needed as more reports for different entities are added, e.g ```VdiskReporter```.

![narf_uml](https://user-images.githubusercontent.com/52970459/147408692-5d58b9f6-593f-4ebc-b818-305c892a6cca.png)

## Advantages
 - Provide easy access to cluster performance activity in any use case where access to the web interface via browser is not available.
 - NARF allows to select a refresh rate specified in seconds from CLI (this will be added to interactive as well), this is timely way to look at cluster activity.
 - For people familiarized with UNIX/Linux environments who prefer CLI than UI, NARF is a nice altenative to the web interface.

## Limitations
 - It only displays Power ON VMs. This is by design, VMs that are not running has no impact on cluster performance.
 - Display a maximum of 252 VMs. This is the max number of entities that Arithmos query returns.

## arithmos_cli case and why narf is needed
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

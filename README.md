# NARF

NARF stands for **N**utanix **A**ctivity **R**eport **F**acilitator.

Inspired in old school UNIX commands like `sar`, `iostat` and `top`, aim to be a simple tool to query and report information from Nutanix clusters performance datasource (arithmos DB). Later will add a feature to export the data into files that can be uploaded to a graphical tool like Grafana.

## Usage
```
usage: narf.py [-h] [--nodes] [--uvms] [--sort {name,cpu,mem,iops,bw,lat}]
               [sec] [count]

Report cluster activity

positional arguments:
  sec                   Interval in seconds
  count                 Number of iterations

optional arguments:
  -h, --help            show this help message and exit
  --nodes, -n           Overal nodes activity report
  --uvms, -v            Overal user VMs activity report
  --sort {name,cpu,mem,iops,bw,lat}, -s {name,cpu,mem,iops,bw,lat}
                        Sort output

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
nutanix@NTNX-CVM:10.66.38.141:~$ ./narf.py -vs cpu 3 | head -30
2021-12-27  VM Name                          CPU%   MEM%   IOPs    B/W    LAT
18:41:58    prolix-pc                       78.23  43.32    418  16.23   3.60 
18:41:58    W2019                           77.06   6.63      0   0.00   0.00 
18:41:58    NTNX-xxxxxxxxxxxx-C-CVM         67.81  64.94      0   0.00   0.00 
18:41:58    NTNX-Prolix2-CVM                53.68  60.97      0   0.00   0.00 
18:41:58    NTNX-Omega-1                    41.06  50.93     28   0.57   5.13 
18:41:58    NTNX-xxxxxxxxxxxx-D-CVM         35.42  65.32      0   0.00   0.00 
18:41:58    NTNX-xxxxxxxxxxxx-A-CVM         30.27  65.18      0   0.00   0.00 
18:41:58    NTNX-Omega-3                    29.18  53.02     28   0.20   3.63 
18:41:58    Asterix_and_Obelix_witness      22.91  51.37     20   0.12   2.85 
18:41:58    NTNX-Prolix4-CVM                19.43  63.87      0   0.00   0.00 
18:41:58    NTNX-Omega-2                    19.17  47.22     28   0.19   3.16 
18:41:58    harold-ocp-cp-2                 18.27  52.03     41   0.41   2.17 
18:41:58    harold-ocp-cp-3                 17.67  47.79     43   0.45   2.17 
18:41:58    harold-ocp-cp-1                 16.61  41.00     65   1.10   4.27 
18:41:58    NTNX-Observer                   15.92  99.76   1151  33.27   2.00 
18:41:58    windows_2016_clone.             14.19  30.96      5   0.03   1.76 
18:41:58    harold-ocp-app-2                13.79  55.20      2   0.05   2.20 
18:41:58    NTNX-FA-FilesAnalyticsProlix     9.10  50.16      3   0.04   2.32 
18:41:58    PostgreSQLVM1.                   8.58  88.97      0   0.00   2.98 
18:41:58    SQL2019.                         6.06  25.80      1   0.01   1.50 
18:41:58    rhtest.                          5.91  53.35      0   0.00   1.60 
18:41:58    ERA.                             5.42  13.73      0   0.01   1.63 
18:41:58    W2019-UEFI                       5.17   0.00      0   0.00   0.00 
18:41:58    NK-Era-new                       5.10   9.93      0   0.00   2.05 
18:41:58    TD-Win2k12-CV                    4.36  23.62      8   0.07   1.75 
18:41:58    Xendesktop                       4.04  19.40      3   0.03   1.44 
18:41:58    vbr                              3.87  47.28      1   0.02   1.59 
18:41:58    Win2019                          3.83  24.35      1   0.01   1.67 
18:41:58    karbon-nh-karbon-099282-k8s-ma   3.70  19.91      0   0.02   2.00 
```

### Interactive mode (top like interface)

<img src="https://user-images.githubusercontent.com/52970459/147422400-2ced603b-d3b1-49ed-a6dd-4068668d2308.jpg" alt="narf_interactive" style="width: 550px;">

## Design

Reporter classes abstract the datasource from the UI classes. Reporter classes are in charge of collect stats from the cluster datasource (Arithmos) and pass the information to UI classes in form of simple native data structures (Python arrays and dictionaries). In this way, if the datasource is changed later (for example from Arithmos to IDF) there will be no need to modify the Ui classes, it will only be needed to change the Reporter classes.

The ```Ui``` super class will hold the attributes that links to all reporters but will not implement any method for presenting information (it's an interface), this assume every UI subclass will need every reporter. Ui subclasses will implement neccesary methods to display information accordingly making use of reporters defined in the super class.

As for the Reporter classes the relationship between super and sub classes and the methods they need to implement is slightly more complicated because the way data is returned from Arithmos. Wherever possible one should prefer to implement a method in the superclass; breakdown a method so that the generic part of the code is moved to the super class while leaving the specifics to entity reporter is a valid resource, as seen in the method ```_get_live_stats()``` in super class ```Reporter``` which is used by ```_get_node_live_stats()``` in the ```NodeReporter``` and ```_get_vm_live_stats()``` in the ```VmReporter``` sub classes (This is aligned with the principles of avoiding code duplication and procuring easy maintenance). More reporters will be needed as more reports for different entities are added, e.g ```VdiskReporter```.

![narf_uml](https://user-images.githubusercontent.com/52970459/147408692-5d58b9f6-593f-4ebc-b818-305c892a6cca.png)

## Changelog

Splitting tasks/features according to each interface, some taks intertwine between interfaces but it should be fine, I'm putting them where are more relevant.

### Todo
- CLI interface - Eveything for inLine outputs
  - [ ] Remove VMs in power state off.
- Interactive interface - top like interface
  - [ ] VM specific report - implement a pad with VM cpu/rdy/mem/controller iops, etc, plus vDisks.
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

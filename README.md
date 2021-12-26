# NARF

NARF stands for **N**utanix **A**ctivity **R**eport (the F has no meaning, just makes the command sounds fun).

Inspired in old school UNIX commands like `sar`, `iostat` and `top`, aim to be a simple tool to query and report information from arithmos DB in Nutanix clusters. Later will add a feature to export the data into files that can be uploaded to a graphical tool like Grafana.

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
nutanix@CVM:10.10.10.10:~/tmp$ ./narf.py -n 2 2
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
nutanix@NTNX-14SM15510002-A-CVM:10.10.10.10:~/tmp$ ./narf.py -vs cpu 3 | head -30
2021-12-26  VM Name                          CPU%   MEM%   IOPs    B/W    LAT
02:45:07    albert-W2019                    81.39   0.00      0   0.00   0.00 
02:45:07    NTNX-xxxxxxxxxxxxx-C-CVM         65.34  64.40      0   0.00   0.00 
02:45:07    NTNX-xxxxxxxxxxxxx-A-CVM         63.25  67.97      0   0.00   0.00 
02:45:07    NTNX-xxxxxxxxxxxxx-D-CVM         60.40  68.05      0   0.00   0.00 
02:45:07    prolix-pc                       44.61  77.60    198   2.05   4.52 
02:45:07    branislav-w10pro                43.34  35.07    306  19.71   1.78 
02:45:07    NTNX-Prolix4-CVM                40.18  62.94      0   0.00   0.00 
02:45:07    NTNX-Observer                   36.36  64.62     22   7.01   0.55 
02:45:07    NTNX-Prolix2-CVM                34.61  66.99      0   0.00   0.00 
02:45:07    NTNX-Omega-2                    31.21  80.29     29   0.20   3.91 
02:45:07    Daniil_rhtest                   30.33  65.91      0   0.00   1.27 
02:45:07    harold-ocp-cp-2                 27.75  64.40     30   0.41   2.13 
02:45:07    NTNX-Omega-1                    26.90  63.28     24   0.16   5.85 
02:45:07    infra-nllinux                   25.38   9.93      2   0.01   1.78 
02:45:07    harold-ocp-cp-3                 24.50  55.93     30   0.44   2.22 
02:45:07    harold-ocp-cp-1                 24.24  45.82     30   0.44   2.16 
02:45:07    Asterix_and_Obelix_witness      21.50  68.20     15   0.10   2.78 
02:45:07    NTNX-Omega-3                    20.84  64.91     30   0.22   3.19 
02:45:07    NKSQL Server 2014 VM            19.58  39.26    459   6.50   1.32 
02:45:07    harold-ocp-app-2                19.46  92.10    928  79.80   1.90 
02:45:07    pavel-vbr                       16.66  72.96      3   0.04   1.78 
02:45:07    harold-ocp-app-1                14.93  69.41      2   0.03   3.21 
02:45:07    Janagan_PostgreSQLVM1           14.47  93.35      0   0.00   2.64 
02:45:07    JanaganSQL2019                  12.51  44.86      1   0.01   1.70 
02:45:07    sergei_era_01                    9.78  17.96      0   0.01   1.39 
02:45:07    NTNX-FA-FilesAnalyticsProlix     7.43  60.40      3   0.04   2.23 
02:45:07    Janagan_MYSQL_ERA                7.20  83.56      0   0.00   1.95 
02:45:07    infra-dc01                       7.17  28.53     19   0.24   1.30 
02:45:07    TD-Win2k12-CV                    6.78  48.12      8   0.10   1.77 
nutanix@NTNX-14SM15510002-A-CVM:10.10.10.10:~/tmp$ 
```

## Design

Reporter classes abstract the datasource from the UI classes. Reporter classes are in charge of collect stats from Arithmos and pass the information to UI classes in form of simple native data structures (Python arrays and dictionaries). In this way, if the datasource is changed later (for example from Arithmos to IDF) there will be no needed to modify the Ui classes, it will only be needed to change the Reporter classes.

The ```Ui``` super class will hold the attributes that links to all reporters but will not implement any method for presenting information (it's an interface), this assume every UI subclass will need every reporter. Ui subclasses will implement neccesary methods to display information accordingly making use of reporters defined in the super class.

As for the Reporter classes the relationship between super and sub classes and the methods they need to implement is slightly more complicated because the way data is returned from Arithmos. Wherever possible one should prefer to implement a method in the superclass, breakdown a method so that the generic part of the code is moved to the super class while leaving the specifics to entity reporter is a valid resource, as seen in the method ```_get_live_stats()``` in super class ```Reporter``` which is called by ```_get_node_live_stats()``` in the ```NodeReporter``` and ```_get_vm_live_stats()``` in the ```VmReporter``` sub classes (This is aligned with the principles of avoiding code duplication and easy the maintenance).

![narf_uml](https://user-images.githubusercontent.com/52970459/147408692-5d58b9f6-593f-4ebc-b818-305c892a6cca.png)

## Why narf?
I had almost decided to change the name from `sre_perf` to `nar` for a while, to make it sound more UNIX like (I thougth about `nstat` but that's already in use), then during Christmas it start to linger in my head as `narf`, that's when I remembered about _Pinky and The Brain_... the sound "_just say narf_" is some sort of "_jacuna matata_" from Pinky, the reflection of The Brain just before the song is quite cliche but I still believe with a deep meaning.

[![narf](https://user-images.githubusercontent.com/52970459/147395459-03f77395-12cb-429a-a7fa-0b773353e7b6.jpg)](https://www.youtube.com/watch?v=lZBQ0tXA-QM)

> "So what if the numbers don't make sense on a chart?
>
> Who said you've got to be smart?
> 
> Paint your nose, chill some flan
> 
> And remember to pre-grease the pan"

# NARF

NARF stands for **N**utanix **A**ctivity **R**eport (the F has no meaning, just makes the command sounds fun).

Inspired in old school UNIX commands like `sar`, `iostat` and `top`, aim to be a simple tool to query and report information from arithmos DB in Nutanix clusters. Later will add a feature to export the data into files that can be uploaded to a graphical tool like Grafana.

## Usage
```
usage: narf.py [-h] [--nodes] [sec] [count]

Report cluster activity from arithmos

positional arguments:
  sec          Interval in seconds
  count        Number of iterations

optional arguments:
  -h, --help   show this help message and exit
  --nodes, -n  Overal nodes activity report

"When you eliminate the impossible, whatever remains, however improbable, must
be the truth." Spock.
```

## Sample output
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

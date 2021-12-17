# SRE Performance tool

Inspired in old school UNIX commands like sar and iostat, aim to be a simple tool to query and report information from arithmos DB.

## Usage

usage: sre_perf.py [-h] [--nodes] [sec] [count]

Report cluster activity from arithmos

positional arguments:
  sec          Interval in seconds
  count        Number of iterations

optional arguments:
  -h, --help   show this help message and exit
  --nodes, -n  Overal nodes activity report

"When you eliminate the impossible, whatever remains, however improbable, must
be the truth." Spock.

## Sample output

nutanix@CVM:10.66.38.41:~/tmp$ ./sre_perf.py -n 2 2
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


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

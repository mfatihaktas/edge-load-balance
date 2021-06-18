#!/bin/bash
echo $1 $2 $3

PY=python3

if [ $1 = 'n' ]; then
  $PY net.py
elif [ $1 = 'nt' ]; then
  $PY net_test.py
elif [ $1 = 'c' ]; then
  [ -z "$2" ] && { echo "Which client [0, *] ?"; exit 1; }
  $PY -u client.py --i=$2 --mid_ip_m='{"m0": "10.0.1.0"}'
elif [ $1 = 'm' ]; then
  pkill -f client.py
  pkill -f master.py
  [ -z "$2" ] && { echo "Which master [0, *] ?"; exit 1; }
  # $PY -u master.py --i=$2 --wip_l='["10.0.2.0"]' # 'null'
  $PY -u master.py --i=$2 --wip_l='["10.0.2.0","10.0.2.1"]' # 'null'
  # $PY -u master.py --i=$2 --wip_l='["10.0.2.0","10.0.2.1"]' 2>&1 > master.log
  # $PY -u master.py --i=$2 --wip_l='["10.0.2.0","10.0.2.1"]' 2> master.log
elif [ $1 = 'w' ]; then
  # rm *.png *.log
  [ -z "$2" ] && { echo "Which worker [0, *] ?"; exit 1; }
  $PY -u worker.py --i=$2
elif [ $1 = 'tc' ]; then
  rm *.pcap
  tcpdump -i s0-eth0 'port 5000' -w tcpdump_s0.pcap
elif [ $1 = 'tr' ]; then
  tcpdump -nn -r tcpdump_s0.pcap | less
elif [ $1 = 'r' ]; then
  $PY rvs.py
else
  echo "Arg did not match!"
fi

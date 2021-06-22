#!/bin/bash
echo $1 $2 $3

PY=python3

if [ $1 = 'n' ]; then
  $PY net.py
elif [ $1 = 's' ]; then
  source ./bin/activate
elif [ $1 = 'nt' ]; then
  $PY net_test.py
elif [ $1 = 'c' ]; then
  [ -z "$2" ] && { echo "Which client [0, *] ?"; exit 1; }
  $PY -u client.py --i=$2 --mean_inter_gen_time=0.1 --num_reqs_to_finish=1000000 --mid_ip_m='{"m0": "10.0.1.0"}' --dashboard_server_ip='10.0.3.0'
elif [ $1 = 'cm' ]; then
  # $PY -u client.py --i=$2 --mid_ip_m='{"m0": "192.168.49.2"}' --mport=30000
  # $PY -u client.py --i=$2 --mid_ip_m='{"m0": "10.106.162.193"}' --mport=30000
  $PY -u client.py --i=$2 --mean_inter_gen_time=1 --num_reqs_to_finish=1000000000 --mid_ip_m='{"m0": "127.0.0.1"}' --mport=$3 # --dashboard_server_ip='dashboard-service'
elif [ $1 = 'm' ]; then
  # $PY -u master.py --i=$2 --wip_l='["10.0.2.0"]'
  $PY -u master.py --i=$2 --wip_l='["10.0.2.0","10.0.2.1"]' --dashboard_server_ip='10.0.3.0'
  # $PY -u master.py --i=$2 --wip_l='["10.0.2.0","10.0.2.1"]' 2>&1 > master.log
  # $PY -u master.py --i=$2 --wip_l='["10.0.2.0","10.0.2.1"]' 2> master.log
elif [ $1 = 'w' ]; then
  # rm *.png *.log
  $PY -u worker.py --i=$2
elif [ $1 = 'd' ]; then
  rm dashboard/static/image/*.png
  $PY dashboard/dashboard.py
elif [ $1 = 'k' ]; then
  pkill -f client.py
  pkill -f master.py
  pkill -f worker.py
  pkill -f dashboard.py
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

#!/bin/bash
echo $1 $2 $3

PY=python3

if [ $1 = 's' ]; then
  source ./bin/activate
elif [ $1 = 'n' ]; then
  $PY net_single_master.py
elif [ $1 = 'n2' ]; then
  $PY net_two_masters.py
elif [ $1 = 'c' ]; then
  [ -z "$2" ] && { echo "Which client [0, *] ?"; exit 1; }
  $PY -u client.py --i=$2 --mean_inter_gen_time=0.2 --mid_addr_m='{"m0": ["10.0.0.0", "null"]}' --dashboard_server_addr='["10.0.3.0", "null"]'
elif [ $1 = 'c2' ]; then
  $PY -u client.py --log_to_std=0 --i=0 --d=2 --inter_probe_num_reqs=20 --mean_inter_gen_time=0.1 --mid_addr_m='{"m0": ["10.0.0.0", "null"], "m1": ["10.0.0.1", "null"]}' --dashboard_server_addr='["10.0.3.0", "null"]'
elif [ $1 = 'cm' ]; then
  # $PY -u client.py --i=$2 --mid_addr_m='{"m0": ["192.168.49.2", "null"]}' --mport=30000
  # $PY -u client.py --i=$2 --mid_addr_m='{"m0": ["10.106.162.193", "null"]}' --mport=30000
  $PY -u client.py --i=$2 --mean_inter_gen_time=1 --mid_addr_m='{"m0": ["127.0.0.1", '$3']}'
elif [ $1 = 'cmo' ]; then
  M0_IP=
  DASHBOARD_SERVER_IP=
  $PY -u client.py --i=$2 --mean_inter_gen_time=0.12 --mid_addr_m='{"'$M0_IP'": ["10.101.185.226", "null"]}' --dashboard_server_addr='["'$DASHBOARD_SERVER_IP'", "null"]'
elif [ $1 = 'cm2' ]; then
  $PY -u client.py --log_to_std=0 --i=$2 --d=2 --inter_probe_num_reqs=20 --mean_inter_gen_time=0.1 --mid_addr_m='{"m0": ["127.0.0.1", '$3'], "m1": ["127.0.0.1", '$4']}' --dashboard_server_addr='["127.0.0.1", '$5']'
elif [ $1 = 'cmo2' ]; then
  M0_IP=
  M1_IP=
  DASHBOARD_SERVER_IP=
  $PY -u client.py --i=$2 --d=2 --inter_probe_num_reqs=20 --mean_inter_gen_time=0.1 --mid_addr_m='{"m0": ["'$M0_IP'", "null"], "m1": ["'$M1_IP'", "null"]}' --dashboard_server_addr='["'$DASHBOARD_SERVER_IP'", "null"]'
elif [ $1 = 'm' ]; then
  # $PY -u master.py --i=$2 --wip_l='["10.0.1.0"]'
  $PY -u master.py --log_to_std=0 --i=$2 --wip_l='["10.0.1.0","10.0.1.1"]' --dashboard_server_ip='10.0.3.0'
  # $PY -u master.py --i=$2 --wip_l='["10.0.1.0","10.0.1.1"]' 2>&1 > master.log
  # $PY -u master.py --i=$2 --wip_l='["10.0.1.0","10.0.1.1"]' 2> master.log
elif [ $1 = 'm0' ]; then
  $PY -u master.py --log_to_std=0 --i=0 --wip_l='["10.0.1.0"]' --dashboard_server_ip='10.0.3.0'
elif [ $1 = 'm1' ]; then
  $PY -u master.py --log_to_std=0 --i=1 --wip_l='["10.0.1.1"]' --dashboard_server_ip='10.0.3.0'
elif [ $1 = 'w' ]; then
  # rm *.png *.log
  $PY -u worker.py --log_to_std=0 --i=$2
elif [ $1 = 'd' ]; then
  rm dashboard/static/image/*.png
  $PY dashboard/dashboard.py --log_to_std=0
elif [ $1 = 'djs' ]; then
  rm dashboard/static/image/*.png
  $PY dashboard/dashboard_js.py --log_to_std=0
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
elif [ $1 = 'p' ]; then
  $PY plot.py
elif [ $1 = 'pu' ]; then
  $PY plot_utils.py
elif [ $1 = 'clean' ]; then
  rm_ () {
    [ -z "$1" ] && { echo "Label?"; exit 1; }
    SUBFOLDER="sim_$1"

    rm $SUBFOLDER/*.json
    rm $SUBFOLDER/*.png
    rm $SUBFOLDER/sbatch_*
  }

  rm_ 'common'
  rm_ 'podc'
  rm_ 'ts'
  rm_ 'rr'
  rm_ 'ucb'
elif [ $1 = 'mfn' ]; then
  ## Second answer here:
  ## https://stackoverflow.com/questions/9612090/how-to-loop-through-file-names-returned-by-find
  ## -E is necessary on Mac
  # find -E . -regex '.*.wlen.*.' -print0 | while read -d $'\0' path
  find . -regex '.*.wlen.*.' -print0 | while read -d $'\0' path
  do
    echo -e "path:\n $path"
    new_path=`echo "$path" | sed s/wlen/w/g`
    echo -e "new_path:\n $new_path"
    mv "$path" "$new_path"
  done
else
  echo "Arg did not match!"
fi

#!/bin/bash
echo $1 $2 $3

PY=python3

if [ $1 = 's' ]; then
  $PY sim.py
  # $PY sim.py --hetero_clusters='False' --N_fluctuating_frac=0.3 --serv_time_rv='exp'
  # $PY sim.py --hetero_clusters='True' --N_fluctuating_frac=0 --serv_time_rv='disc'
elif [ $1 = 'r' ]; then
  $PY rvs.py
else
  echo "Arg did not match!"
fi

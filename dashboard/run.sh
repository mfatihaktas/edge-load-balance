#!/bin/bash
echo $1 $2 $3

PY=python3

if [ $1 = 'd' ]; then
  rm static/image/*.png
  $PY dashboard.py
elif [ $1 = 't' ]; then
  $PY test_objs.py --dashboard_server_ip='192.168.43.49'
else
  echo "Arg did not match!"
fi

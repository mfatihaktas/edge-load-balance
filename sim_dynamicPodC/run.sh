#!/bin/bash
echo $1 $2 $3

PY=python3

if [ $1 = 's' ]; then
  $PY sim.py
else
  echo "Arg did not match!"
fi

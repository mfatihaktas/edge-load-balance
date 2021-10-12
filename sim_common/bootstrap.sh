#!/bin/bash
echo $1 $2 $3

PY=python3

if [ $1 = 'r' ]; then
  $PY bootstrap.py
elif [ $1 = 'c' ]; then
  rm "bootstrap_data"/*.json
else
  echo "Arg did not match!"
fi

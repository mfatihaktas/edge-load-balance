#!/bin/bash
echo $1 $2 $3

PY=python3

if [ $1 = 'f' ]; then
  $PY main.py
elif [ $1 = 't' ]; then
  $PY test_objs.py
else
  echo "Arg did not match!"
fi

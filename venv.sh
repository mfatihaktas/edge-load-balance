#!/bin/bash

VENV_DIR=./venv

if [ $1 = 'setup' ]; then
  python3 -m venv $VENV_DIR
elif [ $1 = 'install' ]; then
  pip3 install -r requirements.txt
  pip3 install -r sim_common/requirements.txt
elif [ $1 = 'source' ]; then
  source $VENV_DIR/bin/activate
else
  echo "Arg did not match; arg= "$1
fi

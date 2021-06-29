#!/bin/bash
echo $1 $2 $3

SB=sb4

IMG_MASTER=mehmet-sb4-kube-master.ndz
IMG_WORKER=mehmet-sb4-kube-worker.ndz

NODE_MASTER=node1-1
NODE_WORKER_L=('node1-3', 'node1-4')
printf -v NODE_WORKERS_COMMA_SEPARATED "%s"  "${NODE_WORKER_L[@]}"
# echo "NODE_WORKERS_COMMA_SEPARATED= "$NODE_WORKERS_COMMA_SEPARATED

if [ $1 = 'stat' ]; then
  omf stat -t all
elif [ $1 = 'ssh' ]; then
  if [ $2 = 'm' ]; then
    NODE=$NODE_MASTER
  elif [ $2 = 'w' ]; then
    [ -z "$3" ] && { echo "Which worker [0, *] ?"; exit 1; }
    NODE=${NODE_WORKER_L[$3]}
  fi
  ssh root@$NODE
elif [ $1 = 'loadm' ]; then
  echo "Loading master..."
  omf load -i $IMG_MASTER -t $NODE_MASTER
elif [ $1 = 'loadw' ]; then
  echo "Loading workers..."
  for NODE_WORKER in "${NODE_WORKER_L[@]}"; do
    echo "Loading NODE_WORKER= "$NODE_WORKER
    omf load -i $IMG_WORKER -t $NODE_WORKER
  done
elif [ $1 = 'on' ]; then
  omf tell -a on -t $NODE_MASTER','$NODE_WORKERS_COMMA_SEPARATED
elif [ $1 = 'off' ]; then
  omf tell -a offs -t $NODE_MASTER','$NODE_WORKERS_COMMA_SEPARATED
elif [ $1 = 'offh' ]; then
  omf tell -a offh -t $NODE_MASTER','$NODE_WORKERS_COMMA_SEPARATED
elif [ $1 = 'reboot' ]; then
  omf tell -a reboot -t $NODE_MASTER','$NODE_WORKERS_COMMA_SEPARATED
elif [ $1 = 'scpm' ]; then
  scp -r ~/edge-load-balance root@$MASTER:~/
elif [ $1 = 'wj' ]; then
  # MASTER_IP=10.14.1.1
  MASTER_IP=$(ssh root@node1-1 'ifconfig enp11s0' | awk -F ' *|:' '/inet /{print $3}')
  echo "MASTER_IP= "$MASTER_IP

  for NODE_WORKER in "${NODE_WORKER_L[@]}"; do
    ssh root@$NODE_WORKER 'kubeadm reset; kubeadm join '$MASTER_IP':6443 --token mjy4sp.pi7ccsb51uvss86r --discovery-token-ca-cert-hash sha256:8dfcc2e99802a3d2540b5650b23cea241f9efe8812625c71d607cccbef523deb'
  done
else
  echo "Argument did not match !"
fi

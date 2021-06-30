#!/bin/bash
echo $1 $2 $3

KUBECTL=kubectl

if [ $1 = 'm' ]; then
  minikube delete
  minikube config set memory 12384
  # Works on orbit nodes with root login
  minikube start --force --driver=docker
elif [ $1 = 'mt' ]; then
  minikube tunnel
elif [ $1 = 'bash' ]; then
  POD_NAME=$2
  [ -z "$POD_NAME" ] && { echo "Pod name?"; exit 1; }
  $KUBECTL exec --stdin --tty $POD_NAME -- /bin/bash
elif [ $1 = 'log' ]; then
  POD_NAME=$2
  $KUBECTL logs -p $POD_NAME
elif [ $1 = 'en' ]; then
  # Assigns an external ip to a service (LoadBalancer). This is needed only in minikube.
  minikube service edge-master-nodeport
elif [ $1 = 'en2' ]; then
  minikube service edge-master-nodeport-$2
elif [ $1 = 'ed' ]; then
  minikube service dashboard-service
elif [ $1 = 't' ]; then
  minikube tunnel
elif [ $1 = 'ru' ]; then
  $KUBECTL run -i --tty ubuntu --image=ubuntu --restart=Never -- /bin/bash
elif [ $1 = 'rc' ]; then
  $KUBECTL delete pod/custom
  # $KUBECTL run -i --tty custom --image=praqma/network-multitool --restart=Never
  # $KUBECTL run -i --tty custom --image=weibeld/docker-ubuntu-networking --restart=Never -- /bin/bash
  # $KUBECTL run -i --tty custom --restart=Never --image=eddiehale/utils /bin/bash
  $KUBECTL run -i --tty custom --restart=Never --image=python:3 /bin/bash
else
  echo "Arg did not match!"
fi

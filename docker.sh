#!/bin/bash
echo $1 $2 $3

# Note: container host address: docker.for.mac.localhost

DOCKER=docker
IMG_NAME=mfatihaktas/edge-load-balance # :latest
CONT_NAME=edge-service
NET_NAME=edge-net

if [ $1 = 'b' ]; then
  rm *.png *.log
  $DOCKER build -t $IMG_NAME .
elif [ $1 = 'rn' ]; then
  $DOCKER run --name nginx  -d -p 8080:80 nginx
elif [ $1 = 'ri' ]; then
  $DOCKER run --name $CONT_NAME -it --rm --net bridge $IMG_NAME /bin/bash
elif [ $1 = 'rmd' ]; then
  [ -z "$2" ] && { echo "Which master [0, *] ?"; exit 1; }
  # $DOCKER run --name $CONT_NAME -it --rm $IMG_NAME ping localhost # Test that should work
  $DOCKER run --name $CONT_NAME -d -it --rm $IMG_NAME python3 -u /home/app/master.py --i=$2
elif [ $1 = 'rmi' ]; then
  [ -z "$2" ] && { echo "Which master [0, *] ?"; exit 1; }
  # --net $NET_NAME --ip 192.168.1.0
  # -p 5000:5000/tcp -p 5000:5000/udp \
  $DOCKER run --name edge-master -it --rm \
          --net bridge \
          $IMG_NAME python3 -u /home/app/master.py --i=$2 --wip_l='null'
elif [ $1 = 'rc' ]; then
  [ -z "$2" ] && { echo "Which client [0, *] ?"; exit 1; }
  # -p 5000:5000/tcp -p 5000:5000/udp \
  $DOCKER run --name edge-client -it --rm \
          --net bridge \
          $IMG_NAME python3 -u /home/app/client.py --i=$2 --mid_ip_m='{"m0": "10.0.1.0"}' #'{"m0": "172.17.0.2"}'
elif [ $1 = 'stop' ]; then
  $DOCKER stop $CONT_NAME
elif [ $1 = 'kill' ]; then
  $DOCKER kill $CONT_NAME
elif [ $1 = 'bash' ]; then
  # $DOCKER exec -it $CONT_NAME bash
  $DOCKER exec -it $2 bash
elif [ $1 = 'lsc' ]; then
  $DOCKER ps --all
elif [ $1 = 'lsi' ]; then
  $DOCKER images
elif [ $1  = 'tag' ]; then
  $DOCKER tag $IMG_NAME $HUB_IMG_NAME
elif [ $1  = 'rm' ]; then
  $DOCKER rm $2
elif [ $1 = 'rmi' ]; then
  $DOCKER image rm $2
elif [ $1 = 'push' ]; then
  $DOCKER push $IMG_NAME
elif [ $1 = 'pull' ]; then
  $DOCKER pull $2
elif [ $1 = 'cn' ]; then
  $DOCKER network create --subnet=192.168.0.0/16 $NET_NAME
elif [ $1 = 'rn' ]; then
  $DOCKER network rm $NET_NAME
elif [ $1 = 'lsn' ]; then
  $DOCKER network ls
else
  echo "Arg did not match!"
fi

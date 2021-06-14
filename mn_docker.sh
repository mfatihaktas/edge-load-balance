#!/bin/bash
echo $1 $2 $3

DOCKER=docker
IMG_NAME=mfatihaktas/mininet
CONT_NAME=mn # $2

FOLDER=edge-load-balance

if [ $1 = 'xterm' ]; then
  nohup socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\" &
  # lsof -i TCP:6000
elif [ $1 = 'rd' ]; then
  $DOCKER run --name $CONT_NAME -d -it --rm --privileged --net=host \
              -e DISPLAY=docker.for.mac.host.internal:0 \
              -v /tmp/.X11-unix:/tmp/.X11-unix \
              -v /lib/modules:/lib/modules \
              -v ~/Desktop/$FOLDER:/root/$FOLDER \
              $IMG_NAME
elif [ $1 = 'r' ]; then
  $DOCKER run --name $CONT_NAME -it --rm --privileged --net=host \
              -e DISPLAY=docker.for.mac.host.internal:0 \
              -v /tmp/.X11-unix:/tmp/.X11-unix \
              -v /lib/modules:/lib/modules \
              -v ~/Desktop/$FOLDER:/root/$FOLDER \
              $IMG_NAME bash
elif [ $1  = 'start' ]; then
  $DOCKER start $CONT_NAME
elif [ $1 = 'stop' ]; then
  $DOCKER stop $CONT_NAME
elif [ $1 = 'kill' ]; then
  $DOCKER kill $CONT_NAME
elif [ $1 = 'bash' ]; then
  $DOCKER exec -it $CONT_NAME bash
elif [ $1 = 'inspect' ]; then
  $DOCKER inspect $CONT_NAME
elif [ $1 = 'lsc' ]; then
  $DOCKER ps --all
elif [ $1  = 'save' ]; then
  $DOCKER save $CONT_NAME -o ~/Desktop/$CONT_NAME.tar
elif [ $1 = 'lsi' ]; then
  $DOCKER images
elif [ $1 = 'commit' ]; then
  $DOCKER commit $CONT_NAME $IMG_NAME
elif [ $1  = 'tag' ]; then
  NEW_CONT_NAME=$3
  $DOCKER tag $CONT_NAME $NEW_CONT_NAME
elif [ $1  = 'rm' ]; then
  $DOCKER rm $CONT_NAME
elif [ $1 = 'push' ]; then
  $DOCKER push $IMG_NAME
elif [ $1 = 'pull' ]; then
  $DOCKER pull $IMG_NAME
elif [ $1 = 'rmi' ]; then
  echo "Will remove the image: $IMG_NAME. Are you sure?"
  read answer
  $DOCKER image rm $IMG_NAME
else
  echo "Argument did not match !"
fi

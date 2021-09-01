#!/bin/bash
PS=$(docker ps | grep vision-edge-controller)
CONTAINER=$(echo $PS | awk '{print $1}')
IMAGE=$(echo $PS | awk '{print $2}')
echo "Installing Web Utilities"
for i in `find . -type d -not -path "."`
do
        echo $i
        docker cp $i $CONTAINER:/opt/ibm/vision-edge/ui
done
docker commit $CONTAINER $IMAGE

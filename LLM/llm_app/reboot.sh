#!/bin/bash

# Define the container name
CONTAINER_NAME="llm_app"

# Stop the container if it's running
echo "Stopping container: $CONTAINER_NAME"
sudo docker stop $CONTAINER_NAME

# Remove the container
echo "Removing container: $CONTAINER_NAME"
sudo docker rm $CONTAINER_NAME

# Start a new instance of the container
echo "Builing a new instance of the container: $CONTAINER_NAME"
sudo docker build -t llm_app .

echo "Running a new instance of the container: $CONTAINER_NAME"                    #-v /This is the path on the host machine                               :/This is the path in the container  
sudo docker run -v /home/ifo/Desktop/8.felev/Szakdolgozat/App_Deployement/llm_app:/app -v /home/ifo/Desktop/8.felev/Szakdolgozat/App_Deployement/llm_app/database:/home/appuser/database -d --privileged -it --name llm_app -p 5000:5000 llm_app 

echo "Container $CONTAINER_NAME has been rebooted."

#!/bin/bash

docker-compose down

docker system prune -f
docker volume prune -f

docker rmi llm_app nginx

docker-compose up --build



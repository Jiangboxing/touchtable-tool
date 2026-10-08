#!/bin/sh
echo DEMKit install script for docker
echo This script expects you to have docker up and running!
echo Furthermore, it is wise to have your docker-compose file configured
echo -------------------------------------------------------------------
echo Starting with building the Docker image
docker build -t demkit .
echo Bringing up InfluxDB and Grafana in Docker compose
docker-compose up -d
echo Fetching demkit data and updates
docker run -t demkit -c "update.sh"
echo "Do you wish to install the example?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) docker run -t demkit -c "obtainexample.sh";;
        No ) docker run -t demkit;exit;;
    esac
done
echo "Do you wish to generate ALPG data (this takes a long time?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) docker run -t demkit -c "setupalpg.sh"; docker run -t demkit;;
        No ) docker run -t demkit;exit;;
    esac
done

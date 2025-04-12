#!/usr/bin/env bash

echo "Stopping mc_dash service..."
sudo service mc_dash stop
sleep 1
echo "Updating mc_dash..."
git pull
sleep 1
echo "Cleaning up old files..."
find . -type d -name "__pycache__" -exec rm -r {} +
sleep 1
echo "Starting mc_dash service..."
sudo service mc_dash start
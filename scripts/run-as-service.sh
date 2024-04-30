#!/bin/bash

sudo cp scripts/docker-compose.service /etc/systemd/system/docker-compose@.service

sudo systemctl daemon-reload
sudo systemctl enable docker-compose@scorpion-defaults
sudo systemctl start docker-compose@scorpion-defaults

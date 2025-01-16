#!/bin/bash

# sudo mkdir -p /etc/docker/compose/scorpion-defaults
# sudo cp docker-compose.yaml /etc/docker/compose/scorpion-defaults/docker-compose.yaml
# sudo cp .env /etc/docker/compose/scorpion-defaults/.env

sudo cp scripts/docker-compose.service /etc/systemd/system/docker-compose@.service

sudo systemctl daemon-reload
sudo systemctl enable docker-compose@scorpion-defaults
sudo systemctl start docker-compose@scorpion-defaults

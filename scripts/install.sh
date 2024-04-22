#!/bin/bash

# config settings on a raspberry pi
function set_config() {
  local line=$1

  if sudo grep -q "$line" /boot/firmware/config.txt; then
    sudo sed -i "s@$line'.*'@$line@" /boot/firmware/config.txt
  else
    sudo sed -i '$a'"$line"'' /boot/firmware/config.txt
  fi
}

function set_alias() {
  local alias=$1
  local alias_target=$2

  if sudo grep -q "alias $alias=" ~/.bashrc; then
    sed -i "s@alias $alias='.*'@alias $alias=$alias_target@" ~/.bashrc
  else
    echo "alias $alias=$alias_target" >> ~/.bashrc
  fi
}

cd $HOME/ct-flows

# updates and packages
sudo apt-get update -y
sudo apt-get full-upgrade -y

sudo apt-get -y install python3.11
sudo apt-get -y install python3-pip
sudo apt-get -y install python3.11-venv
sudo apt-get -y install python-is-python3
sudo apt-get -y install nginx


# git module install
python -m venv .venv --system-site-packages
# shellcheck source=/dev/null
source .venv/bin/activate
python -m pip install -e .

# python streamlit app as service optional button and stats display for pi
mkdir -p tmp


sudo cp scripts/services/app.service tmp/app.service
sed -i "s|{{HOME}}|$HOME|g" tmp/app.service
sudo cp scripts/services/app-service-start.sh tmp/app.sh
sed -i "s|{{HOME}}|$HOME|g" tmp/app.sh
sudo cp tmp/app.sh scripts/app.sh
sudo chmod +x scripts/app.sh
sudo systemctl daemon-reload
sudo systemctl enable app.service
# sudo systemctl start app.service

# # app webserver
sudo cp scripts/nginx/app /etc/nginx/sites-available
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled
sudo systemctl restart nginx

# # cli alias
alias="flows"
alias_target="$HOME/ct-flows/.venv/bin/flows"
set_alias "$alias" "$alias_target"

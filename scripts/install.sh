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


# Specific to Raspberry PI
# sudo apt-get -y install i2c-tools libgpiod-dev python3-libgpiod
# sudo raspi-config nonint do_i2c 0
# sudo raspi-config nonint do_spi 0
# sudo raspi-config nonint do_ssh 0
# sudo raspi-config nonint disable_raspi_config_at_boot 0
# set_config "usb_max_current_enable=1"

# network manager interfaces and defaults using network manager
# sudo nmcli connection delete id ipstatic
# sudo nmcli connection delete id dhcp
# sudo nmcli c add ifname eth0 type ethernet con-name ipstatic
# sudo nmcli c add ifname eth0 type ethernet con-name dhcp
# sudo nmcli con mod ipstatic ipv4.method manual ipv4.addresses 192.168.1.241/24 ipv4.gateway 192.168.1.1 ipv4.may-fail no ipv6.method disabled connection.autoconnect no connection.autoconnect-priority -1
# sudo nmcli con mod dhcp ipv4.method auto ipv4.addresses '' ipv4.gateway '' ipv4.may-fail no ipv4.dhcp-timeout 20 ipv6.method disabled connection.autoconnect yes connection.autoconnect-priority 10 connection.autoconnect-retries 3
# sudo nmcli con down ipstatic
# sudo nmcli con up dhcp

# git module install
python -m venv .venv --system-site-packages
# shellcheck source=/dev/null
source .venv/bin/activate
python -m pip install -e .  # add [pi] after the . to install for the pi

# python streamlit app as service optional button and stats display for pi

sed -i "s|{{HOME}}|$HOME|g" scripts/services/stats.service
sed -i "s|{{HOME}}|$HOME|g" scripts/services/button.service
sed -i "s|{{HOME}}|$HOME|g" scripts/services/stats.service

# sudo cp  /etc/systemd/system/stats.service
# sudo cp scripts/services/button.service /etc/systemd/system/button.service
sudo cp scripts/services/app.service /etc/systemd/system/app.service
sudo systemctl daemon-reload
sudo systemctl enable app.service
# sudo systemctl enable stats.service
# sudo systemctl enable button.service
sudo systemctl start app.service
# sudo systemctl start stats.service
# sudo systemctl start button.service

# # app webserver
sudo cp scripts/nginx/app /etc/nginx/sites-available
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled
sudo systemctl restart nginx

# # cli alias
alias="flows"
alias_target="$HOME/ct-flows/.venv/bin/flows"
set_alias "$alias" "$alias_target"

#set git for remote pushes
# git config --global user.name "User"
# git config --global user.email "Email"

#!/bin/bash


function set_alias() {
  local alias=$1
  local alias_target=$2

  if sudo grep -q "alias $alias=" ~/.bashrc; then
    sed -i "s@alias $alias='.*'@alias $alias=$alias_target@" ~/.bashrc
  else
    echo "alias $alias=$alias_target" >> ~/.bashrc
  fi
}

# git module install
python -m venv .venv --system-site-packages
# shellcheck source=/dev/null
source .venv/bin/activate
python -m pip install -e .  # add [pi] after the . to install for the pi

# python streamlit app as service
sudo cp scripts/services/app.service /etc/systemd/system/app.service
sudo systemctl daemon-reload
sudo systemctl enable app.service
sudo systemctl start app.service

# # app webserver
sudo cp scripts/nginx/app /etc/nginx/sites-available
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled
sudo systemctl restart nginx

# # cli alias
alias="{{CLI_NAME}}"
alias_target="/home/{{USER}}/{{REPO_NAME}}/.venv/bin/{{CLI_NAME}}"
set_alias "$alias" "$alias_target"

#set git for remote pushes
# git config --global user.name "User"
# git config --global user.email "Email"


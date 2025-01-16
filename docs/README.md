# Scorpion Defaults

Creates a docker that runs a webpage to compare and set a list of default parameters for Evertz Scorpion

## Setup


### Clone git and create env


```
git clone https://github.com/ctus-dev/scorpion-defaults.git
cd scorpion-defaults
echo 'SCORPION_USER={{USER}}
SCORPION_PASS={{PASS}}' > .env
```

### Set config/config.json for the following required options:

```
{
    "CONTROL_PREFIX": "10.244.245",
    "JWT_ENABLED": true,
    "SCORPION_CONTROL_PORT": "80",
    "TRUNK_A_PREFIX": "10.101.245",
    "TRUNK_B_PREFIX": "10.102.245"
}
```

### Add one of the following setups to config/config.json:

-   Using range to build both the ip and NMOS name (This would create 3 scorpions; SCPN6-004 @ 10.244.245.4, SCPN6-005@ 10.244.245.5, SCPN6-006@ 10.244.245.6)
    > Note: SCORPION_RANGE will take precedence over SCORPION_LIST if both are included and SCORPION_RANGE is not set to null

```
    "SCORPION_RANGE": "4-6",
    "SCORPION_RANGE_NAME_PFIX": "SCPN6-"
```

-   Or defining and list of scorpions

```
    "SCORPION_LIST": {
        "SCPN6-4": "10.244.245.4",
        "SCPN6-5": "10.244.245.5",
        "SCPN6-6": "10.244.245.6"
    }
```

### If JWT_ENABLED for API Auth:

-   Set .env file in the root folder with scorpion user name and password (Replace {{USER}} and {{PASS}})
    > Note: After first use config.json will include the keys SCORPION_TOKEN and SCORPION_TIMEOUT

```
echo 'SCORPION_USER={{USER}}
SCORPION_PASS={{PASS}}' > .env
```

### Set Default Parameters:

set config/default_params.json with all paramters you would like to be run and checked against. Parameters reference includes most commands that can be set or going to the Scorpion control page > Settings > API > Parameters to the get the full list

> Note: Parameters 5204 (NMOS Name) and 6000 (TRUNK IP) are derived from the config json

-   Example

```
{
    "59": 1,
    "5100": 127,
    "116": 30,
    "120": 1,
    "122": -7,
    "123": 0,
    "124": "10.244.240.1",
    "164": 0,
    "165": 1,
    "166": 0,
    "5200": 1,
    "5201": 1,
    "5202": "testsuite.nmos.tv",
    "5203": "172.16.126.121",
    "5204": "DERIVED from config"
}
```

### Build and run Docker

```
docker compose up --build
```

## Run as service

Script adds docker compose systemd service and starts docker on startup

-   change scripts/docker-compose.service working directory to your home directory (or wherever you cloned the git to)

```
chmod +x scripts/run-as-service.sh
./run-as-service.sh
```


## Updates
stop the service

```
sudo systemctl stop docker-compose@scorpion-defaults

```

make your changes then build
```
sudo docker compose build
```

then start the service

```
sudo systemctl start docker-compose@scorpion-defaults
```
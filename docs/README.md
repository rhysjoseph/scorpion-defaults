# {{REPO_NAME}}

Template Setup

Replacements

-   {{USER}} : linux user to install everything to
-   {{REPO_NAME}} : repo name in snake case
-   ((CLI_NAME)) : Cli command name for entry point

## Install

```
cd ~
sudo rm -d -r {{REPO_NAME}}
git clone https://github.com/ctus-dev/{{REPO_NAME}}.git
cd {{REPO_NAME}}
chmod +x scripts/install.sh
scripts/install.sh
```

## Operation

### Web GUI

_Web GUI address x.x.x.x/settings_

-   Network

    -   Set Static IP - Changes mode to static and sets address

        > <img src="assets/network.png" alt="network" width="500"/>

    -   Bitmask Calculator - computes subnet mask address from bit mask

        > <img src="assets/bitmask.png" alt="bitmask" width="500"/>

---

### CLI

| Title             | Command                                           | Desscription                                        |
| ----------------- | ------------------------------------------------- | --------------------------------------------------- |
| Version           | `{{CLI_NAME}} --version`                          | Returns current cli version                         |
| Update            | `{{CLI_NAME}} update`                             | Software Update                                     |
| Net - DHCP        | `{{CLI_NAME}} net dhcp`                           | Switches device to DHCP mode                        |
| Net - Static      | `{{CLI_NAME}} net static *ip address* *gateway*`  | Switches device to static and sets address          |
| Net - Reset       | `{{CLI_NAME}} net reset`                          | Resets to static ip and sets mode to DHCP           |
| Display - Stats   | `{{CLI_NAME}} display stats --enable/--no-enable` | Runs system stats on device screen                  |
| Display - Message | `{{CLI_NAME}} display message *text*`             | Stops Stats and displays a message on device screen |

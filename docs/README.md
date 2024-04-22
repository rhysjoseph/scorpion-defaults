# ct-flows

Template Setup

Replacements

-   ct-flows : repo name in snake case
-   flows : Cli command name for entry point

## Install

```
cd ~
sudo rm -d -r ct-flows
git clone https://github.com/ctus-dev/ct-flows.git
cd ct-flows
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

| Title             | Command                                    | Desscription                                        |
| ----------------- | ------------------------------------------ | --------------------------------------------------- |
| Version           | `flows --version`                          | Returns current cli version                         |
| Update            | `flows update`                             | Software Update                                     |
| Net - DHCP        | `flows net dhcp`                           | Switches device to DHCP mode                        |
| Net - Static      | `flows net static *ip address* *gateway*`  | Switches device to static and sets address          |
| Net - Reset       | `flows net reset`                          | Resets to static ip and sets mode to DHCP           |
| Display - Stats   | `flows display stats --enable/--no-enable` | Runs system stats on device screen                  |
| Display - Message | `flows display message *text*`             | Stops Stats and displays a message on device screen |

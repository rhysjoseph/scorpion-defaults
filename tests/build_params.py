import json
import re

data = {}
with open("src/scorpion/parameters.txt") as f:
    lines = f.read().split("\n")

current = None
for line in lines:
    match = re.match("control-varid:(\d+)", line)
    if match:
        current = match.group(1)
        data[current] = {}
    else:
        if not current:
            continue
        if len(line.split(":")) > 1:
            key, value = line.split(":", 1)
            if key == "control-name":
                value = value.lower().replace(" ", "_")
            data[current][key.strip()] = value.strip()


sorted_d = dict(sorted(data.items(), key=lambda x: int(x[0])))
with open("src/scorpion/parameters.json", "w") as f:
    f.write(json.dumps(sorted_d))
print(data)

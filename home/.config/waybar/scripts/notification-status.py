#!/usr/bin/env python3
import json
import subprocess

process = subprocess.Popen(["swaync-client", "-swb"], stdout=subprocess.PIPE, text=True)
for line in process.stdout:
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        continue
    alt = str(data.get("alt", "none"))
    data["text"] = " "
    if "inhibited" in alt:
        data["class"] = "inhibited"
    elif "dnd" in alt:
        data["class"] = "dnd"
    else:
        data["class"] = "normal"
    print(json.dumps(data), flush=True)

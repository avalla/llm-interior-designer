# A sidecar that answers one request and dies: the shell must start a new one and repeat the request (lib.rs tests).
import json
import sys

line = sys.stdin.readline()
req = json.loads(line)
if req["method"] == "fail":
    print(json.dumps(dict(id=req["id"], error="ValueError: asked to fail")), flush=True)
else:
    print(json.dumps(dict(id=req["id"], result=dict(echo=req["params"]))), flush=True)

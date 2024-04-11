import json
from datetime import datetime

with open('eod.csv', 'r') as f:
    data = [x.split(',', 1) for x in f.read().split('\n') if x]
    data = [x for x in data if datetime.fromtimestamp(float(x[0])).month == 3]

res = {}
for row in data:
    pnl = json.loads(row[1].replace("'", '"'))
    for k, v in pnl.items():
        res[k] = res.get(k, 0.0) + v

print(res)

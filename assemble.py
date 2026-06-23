import json, datetime

with open('dashboard_data.json', encoding='utf-8') as f:
    data = json.load(f)

with open('dashboard_template.html', encoding='utf-8') as f:
    tpl = f.read()

num_ports = len(data['port'])
num_countries = len(data['country'])

html = tpl.replace('__DATA_JSON__', json.dumps(data, separators=(',',':')))
html = html.replace('__NUM_PORTS__', str(num_ports))
html = html.replace('__NUM_COUNTRIES__', str(num_countries))
html = html.replace('__GEN_DATE__', datetime.date.today().isoformat())

out_path = 'index.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

import os
print('Written', out_path, os.path.getsize(out_path)/1e6, 'MB')

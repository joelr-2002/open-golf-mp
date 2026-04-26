import json

with open('/home/engine/project/data/ui/ui.ui', 'r') as f:
    data = json.load(f)

# Copy play button template
play_btn = next(e for e in data['entities'] if e['name'] == 'play_button')

import copy

host_btn = copy.deepcopy(play_btn)
host_btn['name'] = 'host_button'
host_btn['anchor'] = [0.5, 0.85]
for e in host_btn['up_entities']:
    e['parent'] = 'host_button'
    if e['type'] == 'text':
        e['text'] = 'HOST LAN'
for e in host_btn['down_entities']:
    e['parent'] = 'host_button'
    if e['type'] == 'text':
        e['text'] = 'HOST LAN'

join_btn = copy.deepcopy(play_btn)
join_btn['name'] = 'join_button'
join_btn['anchor'] = [0.5, 0.95]
for e in join_btn['up_entities']:
    e['parent'] = 'join_button'
    if e['type'] == 'text':
        e['text'] = 'JOIN LAN'
for e in join_btn['down_entities']:
    e['parent'] = 'join_button'
    if e['type'] == 'text':
        e['text'] = 'JOIN LAN'

data['entities'].extend([host_btn, join_btn])

with open('/home/engine/project/data/ui/ui.ui', 'w') as f:
    json.dump(data, f, indent=4)


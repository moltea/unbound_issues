"""Modrinth → Discord: posts versions that are not in posted.txt yet (oldest first)."""
import json, os, urllib.request, urllib.error

PROJECT = 'unbound_mod'
STATE = os.path.join(os.path.dirname(__file__), 'posted.txt')
UA = {'User-Agent': 'moltea/unbound_issues release-feed'}


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # the project is not public yet
        raise


versions = get(f'https://api.modrinth.com/v2/project/{PROJECT}/version')
if not versions:
    print('no public versions yet')
    raise SystemExit(0)
posted = set(open(STATE).read().split()) if os.path.exists(STATE) else set()
fresh = [v for v in sorted(versions, key=lambda v: v['date_published']) if v['id'] not in posted]
first_run = not posted
if first_run:
    fresh = fresh[-2:]  # first run: announce only the newest release (one file per loader), remember the rest
for v in fresh:
    loaders = ', '.join(l.capitalize() if l != 'neoforge' else 'NeoForge' for l in v['loaders'])
    text = (v.get('changelog') or '').strip()
    if len(text) > 3500:
        text = text[:3500].rsplit('\n', 1)[0] + '\n…'
    embed = {
        'title': f"{v['name']}",
        'url': f"https://modrinth.com/mod/{PROJECT}/version/{v['id']}",
        'description': text,
        'color': 0x1BD96A,
        'fields': [
            {'name': 'Loader', 'value': loaders or '—', 'inline': True},
            {'name': 'Minecraft', 'value': ', '.join(v['game_versions']) or '—', 'inline': True},
            {'name': 'Channel', 'value': v['version_type'].capitalize(), 'inline': True},
        ],
        'timestamp': v['date_published'],
    }
    role = os.environ.get('ROLE')
    body = {'content': f'<@&{role}>' if role else '', 'embeds': [embed],
            'allowed_mentions': {'roles': [role] if role else []}}
    req = urllib.request.Request(os.environ['WEBHOOK'], data=json.dumps(body).encode(),
                                 headers={**UA, 'Content-Type': 'application/json'}, method='POST')
    urllib.request.urlopen(req).close()
    print('posted', v['version_number'])
posted |= {v['id'] for v in versions}
with open(STATE, 'w') as f:
    f.write('\n'.join(sorted(posted)) + '\n')

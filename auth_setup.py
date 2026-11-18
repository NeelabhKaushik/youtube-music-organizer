"""Consume browser headers locally from stdin; never echo credentials."""
import json
import os
import sys
from pathlib import Path
from ytmusicapi import setup

os.umask(0o077)
path = Path(__file__).resolve().parent / 'secrets' / 'browser.json'
path.parent.mkdir(exist_ok=True, mode=0o700)
try:
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError('Empty input')
    parsed = json.loads(setup(headers_raw=raw))
    allowed = {'cookie', 'authorization', 'x-goog-authuser', 'x-goog-pageid', 'user-agent'}
    headers = {key.lower(): value for key, value in parsed.items() if key.lower() in allowed}
    if not headers.get('cookie') or not headers.get('authorization'):
        raise ValueError('Missing session headers')
    headers.update({'accept': '*/*', 'content-type': 'application/json',
                    'x-origin': 'https://music.youtube.com'})
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(headers))
    temporary.chmod(0o600)
    temporary.replace(path)
    path.chmod(0o600)
except Exception:
    print('Authentication setup failed. Copy complete request headers and retry.', file=sys.stderr)
    sys.exit(1)
print('Saved local authentication. No account changes were made.')

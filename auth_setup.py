"""Consume browser headers locally from stdin; never echo credentials."""
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
    setup(filepath=str(path), headers_raw=raw)
    path.chmod(0o600)
except Exception:
    print('Authentication setup failed. Copy complete request headers and retry.', file=sys.stderr)
    sys.exit(1)
print('Saved local authentication. No account changes were made.')

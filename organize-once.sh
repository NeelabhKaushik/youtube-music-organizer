#!/usr/bin/env bash
# Export once, classify locally, display the preview, and wait for approval.
set -euo pipefail
cd -- "$(dirname -- "$0")"
umask 077

mode=${1:-run}
case "$mode" in run|auth|review) ;; *) echo 'Usage: organize-once.sh [auth|run|review]' >&2; exit 2 ;; esac
runtime=$(mktemp -d)
trap 'rm -rf -- "$runtime"' EXIT
python3 -m venv "$runtime"
python="$runtime/bin/python"

if [[ $mode == auth ]]; then
  "$python" -m pip install -q --no-cache-dir -r requirements.txt
  "$python" auth_setup.py
  exit
fi

if [[ $mode == run ]]; then
  if [[ ! -f secrets/browser.json ]]; then
    echo 'Set up local browser authentication first. See README.md.' >&2
    exit 1
  fi
  model=${YTMO_MODEL:-qwen3:4b}
  if [[ ! $model =~ ^[a-zA-Z0-9_.-]+:[a-zA-Z0-9_.-]+$ || $model == *cloud* ]]; then
    echo 'Choose an installed local Ollama model.' >&2
    exit 1
  fi
  if ! curl -fsS http://127.0.0.1:11434/api/tags | "$python" -c '
import json, sys
sys.exit(not any(m["name"] == sys.argv[1] and not m.get("remote_host")
                 for m in json.load(sys.stdin)["models"]))
' "$model"; then
    echo "Start Ollama and install the local model with: ollama pull $model" >&2
    exit 1
  fi
  if [[ ! -f data/library.json ]]; then
    "$python" -m pip install -q --no-cache-dir -r requirements.txt
    "$python" organizer.py export
  fi
  "$python" classify_local.py "$model"
else
  "$python" organizer.py preview
fi

hash=$("$python" -c 'import json; print(json.load(open("data/plan.json"))["approval_hash"])')
echo 'Inspect data/preview.csv before approving. Press Enter to stop at the preview.'
if [[ ! -t 0 ]]; then exit 0; fi
read -r -p 'Type the approval hash displayed above to create the private playlists: ' approval
if [[ $approval != "$hash" ]]; then
  echo 'Stopped at the preview.'
  exit 0
fi
args=()
if "$python" -c 'import json; raise SystemExit(json.load(open("data/plan.json"))["completeness_verified"])'; then
  read -r -p 'Export completeness is unverified. Type accept-incomplete to proceed: ' incomplete
  [[ $incomplete == accept-incomplete ]] || exit 0
  args+=(--accept-incomplete)
fi
"$python" -m pip install -q --no-cache-dir -r requirements.txt
"$python" organizer.py apply --approve "$hash" "${args[@]}"

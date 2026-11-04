#!/usr/bin/env bash
# install-guard.sh: turn the no-slop hook guard on or off, or show its status.
#   install-guard.sh on|off|status [--scope project|user] [--settings-file PATH] [--force]
# project scope (default): <git root or cwd>/.claude/settings.local.json; user scope: ~/.claude/settings.json.
# Adds a Stop hook and a PreToolUse Edit|MultiEdit|Write hook, timeout 20. Each command is a fail-open sh wrapper:
#   sh -c 'command -v python3 >/dev/null 2>&1 && [ -f "<ABS>/slop-check.py" ] && exec python3 -I "<ABS>/slop-check.py" <ARGS> || exit 0'
# A hook is ours when its command contains "slop-check.py". No other key is touched.
# on: OK only when the hook command and its group matcher are byte-identical to the ones on would write and the
# script exists; FIXED when added or replaced (old form, other args, other matcher, moved path; --force replaces always). off: removes every slop-check hook. status: per scope, on <path> / off / broken <path>.
set -euo pipefail

usage() { echo "usage: $0 on|off|status [--scope project|user] [--settings-file PATH] [--force]" >&2; exit 2; }
[ $# -ge 1 ] || usage
action="$1"; shift
case "$action" in on|off|status) ;; *) usage ;; esac
scope=""; file=""; force=0
while [ $# -gt 0 ]; do
  case "$1" in
    --scope) [ $# -ge 2 ] || usage; scope="$2"; shift 2 ;;
    --settings-file) [ $# -ge 2 ] || usage; file="$2"; shift 2 ;;
    --force) force=1; shift ;;
    *) usage ;;
  esac
done
case "$scope" in ""|project|user) ;; *) usage ;; esac

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
checker="$here/slop-check.py"
[ -f "$checker" ] || { echo "BLOCKED missing $checker" >&2; exit 1; }

project_file() {
  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"
  echo "$root/.claude/settings.local.json"
}
user_file() { echo "$HOME/.claude/settings.json"; }

targets=()
if [ -n "$file" ]; then
  targets=("custom=$file")
elif [ "$action" = status ] && [ -z "$scope" ]; then
  targets=("project=$(project_file)" "user=$(user_file)")
elif [ "$scope" = user ]; then
  targets=("user=$(user_file)")
else
  targets=("project=$(project_file)")
fi

rc=0
for t in "${targets[@]}"; do
  python3 -I - "$action" "${t%%=*}" "${t#*=}" "$checker" "$force" <<'PY' || rc=1
import json, os, re, sys, tempfile

action, label, path, checker, force = sys.argv[1:6]
force = force == "1"
if re.search(r"[\"'$`\\]", checker):
    print(f"BLOCKED {label}: script path has a quote, $, backtick or backslash: {checker}")
    sys.exit(1)

def wrap(args):
    return (f"sh -c 'command -v python3 >/dev/null 2>&1 && [ -f \"{checker}\" ] && "
            f"exec python3 -I \"{checker}\" {args} || exit 0'")

HOOKS = [("Stop", None, wrap("--stop-hook --strict-top --top-words 250")),
         ("PreToolUse", "Edit|MultiEdit|Write", wrap("--pretooluse"))]
MARK = "slop-check.py"

def load():
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    return json.loads(raw) if raw.strip() else {}

def save(data):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".settings.")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)

def named_path(cmd):
    m = re.search(r'"([^"]*slop-check\.py)"', cmd) or re.search(r"(\S*slop-check\.py)", cmd)
    return m.group(1).strip("'") if m else ""

def ours_with_matcher(data, event):
    """Our hooks on one event as (group matcher or None, command) pairs."""
    out = []
    for group in (data.get("hooks") or {}).get(event) or []:
        for h in (group.get("hooks") or []) if isinstance(group, dict) else []:
            cmd = str(h.get("command", "")) if isinstance(h, dict) else ""
            if MARK in cmd:
                out.append((group.get("matcher"), cmd))
    return out

def ours(data, event):
    return [cmd for _, cmd in ours_with_matcher(data, event)]

def strip(data, event):
    """Remove our hooks from one event; return the removed commands."""
    groups = data["hooks"].get(event)
    if not isinstance(groups, list):
        return []
    kept, removed = [], []
    for group in groups:
        hs = group.get("hooks") if isinstance(group, dict) else None
        if not isinstance(hs, list):
            kept.append(group)
            continue
        rest = [h for h in hs if not (isinstance(h, dict) and MARK in str(h.get("command", "")))]
        removed += [h["command"] for h in hs if h not in rest]
        if rest or not hs:
            kept.append(dict(group, hooks=rest) if len(rest) != len(hs) else group)
    if kept:
        data["hooks"][event] = kept
    else:
        del data["hooks"][event]
    return removed

try:
    data = load()
except ValueError as e:
    print(f"BLOCKED {label} {path}: invalid JSON ({e})")
    sys.exit(1)
if data is not None and (not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict)):
    print(f"BLOCKED {label} {path}: settings or its hooks key is not a JSON object")
    sys.exit(1)

if action == "status":
    found = {ev: ours(data or {}, ev) for ev, _, _ in HOOKS}
    paths = [named_path(c) for cmds in found.values() for c in cmds]
    missing = [p or "(no path)" for p in paths if not (p and os.path.isfile(p))]
    if not paths:
        state = "off"
    elif missing:
        state = f"broken {missing[0]}"
    elif not all(found.values()):
        state = "broken missing " + ",".join(ev for ev, c in found.items() if not c) + " hook"
    else:
        state = f"on {paths[0]}"
    print(f"{label} {path}: {state}")
    sys.exit(0)

if action == "on":
    data = {} if data is None else data
    data.setdefault("hooks", {})
    changed = False
    for event, matcher, cmd in HOOKS:
        existing = ours_with_matcher(data, event)
        if existing == [(matcher, cmd)] and not force and os.path.isfile(checker):
            print(f"OK {label} {event} hook present: {checker}")
            continue
        strip(data, event)
        group = {"matcher": matcher} if matcher else {}
        group["hooks"] = [{"type": "command", "command": cmd, "timeout": 20}]
        data["hooks"].setdefault(event, []).append(group)
        changed = True
        print(f"FIXED {label} {event} hook {'replaced' if existing else 'added'}: {checker}")
    if changed:
        save(data)
    sys.exit(0)

# off
if data is None or not data.get("hooks"):
    print(f"SKIP {label} {path}: no hooks to remove")
    sys.exit(0)
changed = False
for event in list(data["hooks"].keys()):
    for cmd in strip(data, event):
        changed = True
        print(f"FIXED {label} {event} hook removed: {cmd}")
if changed:
    if not data["hooks"]:
        del data["hooks"]
    save(data)
else:
    print(f"SKIP {label} {path}: no slop-check hook found")
PY
done
exit "$rc"

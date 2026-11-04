# no-slop scripts

SKILL.md works without these scripts; they are optional enforcement. Python 3.9+, stdlib only.

- `slop-check.py` checks prose. Code, frontmatter, inline code, URLs, paths and IDs are masked first.
- `install-guard.sh` adds or removes the two Claude Code hooks that run the checker.
- `test_slop_check.py` holds the unit tests.

| Command | Exit codes |
|---|---|
| `python3 -I slop-check.py FILE...` (profile `file`) | 0 clean or advisory only, 1 any BLOCK |
| `python3 -I slop-check.py < text.txt` (profile `reply`) | 0 or 1 |
| `python3 -I slop-check.py --stop-hook` (Stop hook JSON on stdin) | 0 pass, 2 BLOCK (repair text on stderr) |
| `python3 -I slop-check.py --pretooluse` (Write/Edit/MultiEdit JSON on stdin) | always 0; a deny is JSON on stdout |
| `bash install-guard.sh on\|off\|status [--scope project\|user] [--settings-file PATH] [--force]` | 0, 1 on invalid settings |
| `python3 -I -m unittest discover -s scripts -p "test_*.py"` | unittest |

Options: `--profile reply|file|handoff|message|procedure`, `--json`, `--max-sentence N`, `--cap-chars N`,
`--top-words N`, `--strict-top`, `--lexicon PATH`, `--require-sections "A,B"`, `--durable-pattern REGEX`,
`--quiet`, `--version`.

Before checking, the script joins hard-wrapped lines of a paragraph, masks fenced code, inline code,
URLs, paths and identifiers, and skips table rows, headings and blockquotes for sentence checks. LEX and
HEDGE skip a phrase inside a short double-quoted span, so a rule that names a banned phrase is not a hit.

Hook commands. `on` writes each hook as a shell wrapper around the absolute script path:
`sh -c 'command -v python3 >/dev/null 2>&1 && [ -f "<ABS>/slop-check.py" ] && exec python3 -I "<ABS>/slop-check.py" <ARGS> || exit 0'`.
The Stop hook passes `--stop-hook --strict-top --top-words 250`; the PreToolUse hook (matcher `Edit|MultiEdit|Write`,
timeout 20) passes `--pretooluse`. When python3 or the script is missing, the hook exits 0 and the session
goes on. `on` prints OK when a hook exists with the same command and matcher and its script path exists, and FIXED when it adds a hook or
replaces one whose path is gone. `--force` replaces the hooks always. `off` removes every hook whose
command contains `slop-check.py`. `status` prints `on <path>`, `off` or `broken <missing path>` per scope.

Caveats. A Write of an existing file is judged on its touched blocks only, so an append-only log is not denied for its history.
Blocks end at a blank line, a heading, a code fence or a list-item start; a block is touched when one of its lines is not in the old file, and it is judged whole.
An Edit or MultiEdit of an existing file is applied to the file first and judged the same way; when an `old_string` is not found, the gate checks the `new_string` text alone. The write gate checks only paths that match the durable pattern, case-insensitive:
`(^|[/_.-])(NEXT_SESSION|HANDOFF|HANDOVER|DECISIONS|MEMORY|PLAN)[^/]*\.md$|(^|/)memories/.*\.md$|(^|/)\.serena/.*\.md$` (markdown only).
It denies one path at most
2 times per session, then allows it silently. The count lives in `${TMPDIR:-/tmp}/no-slop-guard/<session_id>/`;
a state error allows the write. It uses the handoff profile for NEXT_SESSION, HANDOFF and HANDOVER paths and
the file profile otherwise, so TOP does not apply to files. The Stop hook passes when `stop_hook_active` is
true, when the reply has under 40 words, and when more than half of its lines are fenced code. Its repair
text starts with `no-slop:` and has at most 600 characters. An internal error in either hook exits 0.

For wizard authors. Run `bash <ABS>/install-guard.sh on --scope user`, where `<ABS>` is the scripts folder of
the installed skill. A second run prints OK and changes nothing. To read the state, run
`bash <ABS>/install-guard.sh status --scope user` and parse the text after the colon.

| ID | Severity | Threshold | Evidence source |
|---|---|---|---|
| S60 | BLOCK | sentence > 60 words | headinthebox gist; yaplint |
| S40 | ADVISORY | sentence > 40 words; mean, p90, share > 30 reported | headinthebox; agent-style |
| S25x3 | ADVISORY | 3 or more sentences > 25 words | issue #92175 (no measurement) |
| NEG | BLOCK at 2, ADVISORY at 1 | "not X, it's Y" family, negation-first opener; "not ... but" only after just, only or merely | unjargon; yaplint; corpus README |
| HEDGE | BLOCK | "should work" type hedge, no evidence token | yaplint H1 |
| FILL | BLOCK | filler opener at start, sign-off in last 2 lines | yaplint OPENERS / ANYWHERE |
| CODE-AS-NAME | ADVISORY | 3 or more distinct codes (R7, Q-E1, §7.1) in prose | corpus code_refs |
| COUNT | ADVISORY | "three things", "for two reasons" | corpus counting_announcements |
| TRANS | ADVISORY | more than 1 transition opener in a paragraph | agent-style RULE-D |
| CLOSER | ADVISORY | paragraph ends with "Overall," and similar | agent-style RULE-E |
| LEX | ADVISORY | about 30 built-in terms plus `--lexicon` | agent-style RULE-06; unjargon; yaplint |
| CAP | BLOCK | `message` profile: text > 3000 chars | digest budget |
| TOP | ADVISORY (`--strict-top`: BLOCK) | `reply` profile: words above the `--- detail ---` line (or all) > 150 | no-slop Reply shape; untested |
| SECTIONS | ADVISORY | `handoff` profile: missing Goal, First step, State, Decisions, Open, Traps, Glossary, Pointers (case-insensitive prefix match) | Handoff shape, `references/shapes.md` section 3 |
| LINES | ADVISORY | `handoff` profile: > 80 non-empty lines | handoff contract |

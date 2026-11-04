#!/usr/bin/env python3
"""slop-check: stdlib prose checker for the no-slop skill (Python 3.9+, runs under `python3 -I`).

Modes: FILE... | - (stdin text, also the default) | --stop-hook | --pretooluse.

Checks (BLOCK gates; ADVISORY never gates) [evidence source]:
  S60          BLOCK     sentence over --max-sentence words, default 60 [headinthebox gist; yaplint]
  S40          ADVISORY  sentence over 40 words; summary prints mean, p90, share over 30 [headinthebox; agent-style]
  S25x3        ADVISORY  three or more sentences over 25 words in one text [issue #92175; no measurement]
  NEG          BLOCK>=2  "X is not Y, it's Z" family and negation-first openers, one hit per sentence,
                         ADVISORY at 1; "not ... but" counts only after just/only/merely, so a plain
                         failure report ("did not start, but ...") is not a hit
                         [unjargon not-x-but-y; yaplint CONTRAST_OPENER; corpus README]
  HEDGE        BLOCK     "should work"-type hedge with no evidence token in the sentence [yaplint H1]
  FILL         BLOCK     filler opener at the start or sign-off in the last 2 lines [yaplint OPENERS/ANYWHERE]
  CODE-AS-NAME ADVISORY  3 or more distinct section/finding codes (R7, Q-E1, §7.1) in prose [corpus code_refs]
  COUNT        ADVISORY  counting announcement ("three things", "for two reasons") [corpus counting_announcements]
  TRANS        ADVISORY  more than one transition opener in one paragraph [agent-style RULE-D]
  CLOSER       ADVISORY  paragraph ends with a summary closer ("Overall," ...) [agent-style RULE-E]
  LEX          ADVISORY  built-in ~30-term lexicon plus --lexicon file; skips short quoted spans
                         [agent-style RULE-06; unjargon; yaplint]
  CAP          BLOCK     message profile: text longer than --cap-chars, default 3000 [Slack digest budget]
  TOP          ADVISORY  reply profile: words above the '--- detail ---' line (or the whole text) over
                         --top-words, default 150; --strict-top makes it BLOCK [no-slop Reply shape; untested]
  SECTIONS     ADVISORY  handoff profile: required heading missing; defaults follow the Handoff shape (Goal, First
                         step, State, Decisions, Open, Traps, Glossary, Pointers), case-insensitive prefix
                         match, so "Open items" counts as Open [no-slop handoff contract]
  LINES        ADVISORY  handoff profile: more than 80 non-empty lines [no-slop handoff contract]

Exit codes: 0 clean or advisory-only; 1 any BLOCK (file/stdin); 2 BLOCK in --stop-hook.
Hook modes fail open: an internal error exits 0 with the error on stderr. Wrapped paragraph lines are joined first.
--stop-hook passes (exit 0) when stop_hook_active is true, when last_assistant_message is missing or under 40
words, or when more than half of its lines are fenced code; otherwise a BLOCK exits 2 with a repair message
(starts "no-slop:", at most 600 chars) on stderr.
--pretooluse checks only paths matching --durable-pattern, case-insensitive; the default DURABLE_DEFAULT is
  (^|[/_.-])(NEXT_SESSION|HANDOFF|HANDOVER|DECISIONS|MEMORY|PLAN)[^/]*\\.md$|(^|/)memories/.*\\.md$|(^|/)\\.serena/.*\\.md$
(markdown files only). A Write or an Edit/MultiEdit of an existing file is judged on its touched blocks only:
an edit is applied to the file first (first occurrence, or all with replace_all); the result is split into
blocks at blank lines, headings, fences (a fenced region is one block) and list-item starts; a block is
touched when any of its lines (rstripped) is absent from the old file; the touched blocks are judged whole,
joined with blank lines. When an old_string is not found the check falls back to the new_string text alone.
It uses
the handoff profile for NEXT_SESSION|HANDOFF|HANDOVER paths, else file. Deny cap: it denies one file_path at
most DENY_CAP (2) times per session, then allows silently. The count lives in
${TMPDIR:-/tmp}/no-slop-guard/<session_id>/denials.json (session_id "default" when absent); any state error allows.
"""
import argparse
import json
import math
import os
import re
import sys
import tempfile

VERSION = "0.1.0"
DURABLE_DEFAULT = r"(^|[/_.-])(NEXT_SESSION|HANDOFF|HANDOVER|DECISIONS|MEMORY|PLAN)[^/]*\.md$|(^|/)memories/.*\.md$|(^|/)\.serena/.*\.md$"
DENY_CAP = 2
STOP_MIN_WORDS = 40
SECTIONS_DEFAULT = "Goal,First step,State,Decisions,Open,Traps,Glossary,Pointers"
I = re.IGNORECASE

# ---------- preprocessing ----------
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def _fence_marker(line):
    """The fence run of a line ('```', '````', '~~~'...), or None. A fence closes only on a run of the
    same character at least as long as the one that opened it (CommonMark), so a ```` block may contain
    ``` fences without ending."""
    m = FENCE.match(line)
    return m.group(1) if m else None


def _fence_step(open_marker, line):
    """Given the marker of the currently open fence (or None), return the new open marker after this line
    and whether the line itself is a fence line."""
    mk = _fence_marker(line)
    if mk is None:
        return open_marker, False
    if open_marker is None:
        return mk, True
    if mk[0] == open_marker[0] and len(mk) >= len(open_marker):
        return None, True
    return open_marker, True  # a shorter or different fence inside an open block is content
INLINE_CODE = re.compile(r"`[^`\n]+`")
URL = re.compile(r"https?://\S+")
PATHLIKE = re.compile(r"(?<!\S)(?:~/|\./)\S*|(?<!\S)(?=\S*/)(?=\S*\.)\S+")
UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
HEX = re.compile(r"\b[0-9a-fA-F]{8,}\b")
TICKET = re.compile(r"\b[A-Z]{2,}-\d+\b")
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
WORD = re.compile(r"\b[\w'-]+\b")


def mask(line):
    line = line.replace("’", "'").replace("‘", "'")
    for rx in (INLINE_CODE, URL, PATHLIKE, UUID, HEX, TICKET):
        line = rx.sub("XREF", line)
    return line


class Doc:
    """Parsed text: kept lines (code and frontmatter blanked), sentences with line and paragraph ids."""

    def __init__(self, text):
        self.raw = text
        lines = text.replace("\r\n", "\n").split("\n")
        start = 0
        if lines and lines[0].strip() == "---":
            for j in range(1, len(lines)):
                if lines[j].strip() in ("---", "..."):
                    start = j + 1
                    break
        self.start = start
        self.lines = [""] * start + lines[start:]  # index = line number - 1
        self.headings, self.sentences, self.prose = [], [], []  # prose: (lineno, masked text)
        open_marker, buf = None, None  # buf: [first line number, parts, is_list_item]

        def flush():
            nonlocal buf
            if buf:
                self._add_para(buf[0], " ".join(buf[1]))
            buf = None

        for idx in range(start, len(lines)):
            ln, line = idx + 1, lines[idx]
            was_open = open_marker is not None
            open_marker, is_fence = _fence_step(open_marker, line)
            if is_fence:
                self.lines[idx] = ""
                flush()
                continue
            if was_open:
                self.lines[idx] = ""
                continue
            s = line.strip()
            if not s or s.startswith(("|", ">")) or s in ("---", "..."):
                flush()
                continue
            if s.startswith("#"):
                flush()
                self.headings.append(s.lstrip("#").strip())
                continue
            if BULLET.match(line):
                flush()
                buf = [ln, [BULLET.sub("", line).strip()], True]
            elif buf and (not buf[2] or line.startswith("  ")):
                buf[1].append(s)  # wrapped paragraph or indented list-item continuation
            else:
                flush()
                buf = [ln, [s], False]
        flush()

    def _add_para(self, ln, joined):
        """Mask one joined paragraph and split it into sentences; ln = its first line."""
        m, para = mask(joined), len(self.prose)
        self.prose.append((ln, m))
        for sent in SENT_SPLIT.split(m):
            if sent.strip():
                self.sentences.append({"line": ln, "para": para, "text": sent.strip(),
                                       "words": len(WORD.findall(sent))})

    def sentence_at(self, ln, col):
        """Index of the sentence on line ln that contains column col of the masked line."""
        cands = [i for i, s in enumerate(self.sentences) if s["line"] == ln]
        text = dict(self.prose)[ln]
        pos = 0
        for i in cands:
            pos = text.find(self.sentences[i]["text"], pos)
            if col < pos + len(self.sentences[i]["text"]):
                return i
            pos += len(self.sentences[i]["text"])
        return cands[-1] if cands else -1


# ---------- patterns ----------
NEG_RX = [re.compile(p, I) for p in (
    # unjargon not-x-but-y
    r"\b(?:it|this|that|the (?:problem|issue|point))(?:'?s not|\s+is\s+not|\s+isn'?t|\s+was\s+not|\s+wasn'?t)\b"
    r"[^.!?\n]{1,60}[,;]\s*(?:it|this|that)(?:'?s|\s+is|\s+was)\b",
    # corpus README neg_parallelism (five)
    r"\bnot\s+[^.;:,—–!?\n]{1,60}?\s*([,;—–]|\s-)\s*(it'?s|it is|rather|just)\b",
    r"\bnot\s+[^.!?\n]{1,60}[.!?]\s+(it'?s|it is)\b",
    r"\bnot\s+(just|only|merely)\s+(\w+\s+){0,5}?\w+,?\s+but\b",
    r"\b(isn'?t|is not|wasn'?t|aren'?t)\s+[^.;—–!?\n]{1,60}?\s*[;—–:]\s*(it'?s|it is|they'?re|that'?s)\b",
    r"(^|[.!?]\s+)not an?\s+[^.!?\n]{1,60}[.!?]\s+an?\s+\w",
)]
NEG_OPENER = re.compile(r"^\s*(it|this|that)(?:'s| is)\s+not\b", I)  # yaplint CONTRAST_OPENER
QUOTE_SPAN_RX = re.compile(r'["\u201c]([^"\u201d]{1,80})["\u201d]')


def _in_quotes(text, pos):
    """True when position pos falls inside a short double-quoted span (under 8 words)."""
    for m in QUOTE_SPAN_RX.finditer(text):
        if m.start() <= pos < m.end() and len(m.group(1).split()) < 8:
            return True
    return False


HEDGE_RX = re.compile(r"\b(should work|probably works|should be fine|likely works|seems to work|appears to work)\b", I)
EVIDENCE_RX = re.compile(r"\d|%|XREF|\btest|\bran\b|\blog|\bverified\b|\bmeasured\b|\boutput\b", I)
OPENER_RX = re.compile(r"^\W*(Great question|Certainly|Sure[,!]|Absolutely|Here's|Here is (?:a|an|the)\b|Let me\b|"
                       r"I'd be happy|Looking at|Diving into|Let's dive)", I)
SIGNOFF_RX = re.compile(r"\b(Hope this helps|Let me know if|Feel free to|Happy to|Don't hesitate|I hope)\b", I)
CODE_RX = [re.compile(r"(?<![\w#/.-])(?!XREF)[A-Z]{1,2}\d{1,3}(?:\.\d+)*\b"), re.compile(r"\bQ-[A-Z]{1,2}\d+\b"),
           re.compile(r"§\d+(?:\.\d+)*"), re.compile(r"\bsee \d+\.\d+", I)]
N = r"(?:two|three|four|five)"
COUNT_RX = re.compile(rf"\bfor {N} reasons\b|\b(?:two|three|four|five|six) (?:things|points|changes|issues|options|"
                      rf"questions|parts|steps|problems|findings|gaps|risks|caveats)\b|\bthere (?:are|were) {N}\b", I)
TRANS_RX = re.compile(r"^\W*(Additionally|Furthermore|Moreover|In addition|Notably|Importantly|Crucially|Ultimately)\b", I)
CLOSER_RX = re.compile(r"^\W*(Overall,|In summary,|In short,|To sum up|In conclusion|So, to answer)", I)
QUOTED = re.compile(r"\"[^\"\n]*\"|\u201c[^\u201d\n]*\u201d")  # LEX skips short quoted spans (a skill names its bans)
LEX = {
    "load-bearing": r"\bload[- ]bearing\b", "the crux": r"\bthe crux\b", "worth naming": r"\bworth naming\b",
    "north star": r"\bnorth star\b", "seam": r"\bseams?\b", "papercut": r"\bpaper ?cuts?\b",
    "gated on": r"\bgated on\b", "wired up": r"\bwired up\b", "belt and braces": r"\bbelt[- ]and[- ]braces\b",
    "pressure test": r"\bpressure[- ]test", "unlock": r"(?<!the )\bunlock(?:s|ed|ing)?\b", "lever": r"\blevers?\b",
    "delve": r"\bdelv(?:e|es|ed|ing)\b", "tapestry": r"\btapestry\b",
    "leverage (verb)": r"\bleverag(?:es|ed|ing)\b|\b(?:to|we|can|will|you|they|and|could|should) leverage\b",
    "robust": r"\brobust(?:ly|ness)?\b", "seamless": r"\bseamless(?:ly)?\b", "cutting-edge": r"\bcutting[- ]edge\b",
    "game-changer": r"\bgame[- ]chang(?:er|ing)\b", "it's worth noting": r"\bit'?s worth noting\b",
    "serves as": r"\bserves as\b", "that's where": r"\b(?:that|this|here)'?s where\b", "at its core": r"\bat its core\b",
    "under the hood": r"\bunder the hood\b", "the real X is": r"\bthe real \w+ is\b", "the unlock": r"\bthe unlock\b",
    "elegant": r"\belegant(?:ly)?\b", "nuanced": r"\bnuanced\b", "holistic": r"\bholistic(?:ally)?\b",
    "synergy": r"\bsynerg(?:y|ies)\b",
}


# ---------- checks ----------
def clip(s, n):
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def first_words(s, n=12):
    return " ".join(s.split()[:n]) + (" …" if len(s.split()) > n else "")


def check(text, profile, args):
    d, out = Doc(text), []

    def add(cid, sev, line, excerpt, fix):
        out.append({"check": cid, "severity": sev, "line": line, "excerpt": clip(excerpt, 100), "fix": clip(fix, 80)})

    sents = d.sentences
    for s in sents:
        if s["words"] > args.max_sentence:
            add("S60", "BLOCK", s["line"], f"{s['words']} words: {first_words(s['text'])}",
                f"split into sentences of 25 words or fewer, one fact each")
        elif s["words"] > 40:
            add("S40", "ADVISORY", s["line"], f"{s['words']} words: {first_words(s['text'])}",
                "split it; one fact per sentence")
    long25 = [s for s in sents if s["words"] > 25]
    if len(long25) >= 3:
        add("S25x3", "ADVISORY", long25[0]["line"], f"{len(long25)} sentences over 25 words",
            "shorten the long sentences")

    neg = {}
    for ln, m in d.prose:
        for rx in NEG_RX:
            for hit in rx.finditer(m):
                i = d.sentence_at(ln, hit.start() + (len(hit.group(1) or "") if rx.pattern.startswith("(^|") else 0))
                neg.setdefault(i, hit.group(0).lstrip(".!? \t"))
    for i, s in enumerate(sents):
        if NEG_OPENER.match(s["text"]):
            neg.setdefault(i, s["text"])
    neg.pop(-1, None)
    sev = "BLOCK" if len(neg) >= 2 else "ADVISORY"
    for i in sorted(neg):
        add("NEG", sev, sents[i]["line"], neg[i], "state what it is; drop the negated foil")

    for s in sents:
        h = HEDGE_RX.search(s["text"])
        if h and _in_quotes(s["text"], h.start()):
            continue  # the sentence quotes the phrase (a rule that names it), it does not use it
        if h and not EVIDENCE_RX.search(s["text"]):
            add("HEDGE", "BLOCK", s["line"], s["text"], "cite the test, log or number, or say it is untested")

    if d.prose:
        ln, m = d.prose[0]
        o = OPENER_RX.match(m)
        if o:
            add("FILL", "BLOCK", ln, m, f"delete the opener '{o.group(1)}'; start with the answer")
    tail = [(i + 1, l) for i, l in enumerate(d.lines) if l.strip()][-2:]
    for ln, l in tail:
        so = SIGNOFF_RX.search(l)
        if so:
            add("FILL", "BLOCK", ln, l[so.start():].strip(), f"delete the sign-off '{so.group(1)}'")

    codes, first_ln = [], None
    for ln, m in d.prose:
        for rx in CODE_RX:
            for c in rx.finditer(m):
                if c.group(0) not in codes:
                    codes.append(c.group(0))
                    first_ln = first_ln or ln
    if len(codes) >= 3:
        add("CODE-AS-NAME", "ADVISORY", first_ln, f"{len(codes)} codes: {', '.join(codes[:3])}",
            "name each thing in words; keep a code once, in parentheses")

    for ln, m in d.prose:
        for c in COUNT_RX.finditer(m):
            add("COUNT", "ADVISORY", ln, c.group(0), "drop the count; list the items")

    paras = {}
    for s in sents:
        paras.setdefault(s["para"], []).append(s)
    for group in paras.values():
        tr = [s for s in group if TRANS_RX.match(s["text"])]
        if len(tr) > 1:
            add("TRANS", "ADVISORY", tr[1]["line"], tr[1]["text"], "drop the transition words; let order carry the link")
        if CLOSER_RX.match(group[-1]["text"]):
            add("CLOSER", "ADVISORY", group[-1]["line"], group[-1]["text"], "delete the recap sentence")

    lex = dict(LEX)
    for term in args.extra_lexicon:
        lex.setdefault(term, r"\b" + re.escape(term) + r"\b")
    for term, pat in lex.items():
        rx, hits = re.compile(pat, I), []
        for ln, m in d.prose:
            quoted = [q.span() for q in QUOTED.finditer(m) if len(WORD.findall(q.group(0))) < 8]
            hits += [ln for h in rx.finditer(m) if not any(a <= h.start() < b for a, b in quoted)]
        if hits:
            add("LEX", "ADVISORY", hits[0], f"{term} x{len(hits)}", "use the plain word")

    if profile == "message" and len(text) > args.cap_chars:
        add("CAP", "BLOCK", 1, f"{len(text)} chars > {args.cap_chars}", f"cut to {args.cap_chars} chars; answer first")
    if profile == "reply":
        # Top layer = the text above the first detail separator ('--- detail ---' or a bare '---' line
        # after the first line); with no separator the whole text is the top layer.
        lines = text.replace("\r\n", "\n").split("\n")
        cut = len(lines)
        for i, l in enumerate(lines[1:], 1):
            if re.match(r"^\s*---(\s*detail\s*---)?\s*$", l, re.I):
                cut = i
                break
        top_words = len(WORD.findall(" ".join(lines[:cut])))
        if top_words > args.top_words:
            add("TOP", "BLOCK" if args.strict_top else "ADVISORY", 1,
                f"{top_words} words above the detail line > {args.top_words}",
                "move claims below a '--- detail ---' line or into the file; do not compress sentences")
    if profile == "handoff":
        heads = [re.sub(r"^\d+[.)]?\s*", "", h).lower() for h in d.headings]
        for name in [x.strip() for x in args.require_sections.split(",") if x.strip()]:
            if not any(h.startswith(name.lower()) for h in heads):
                add("SECTIONS", "ADVISORY", 1, f"missing heading: {name}", f"add a '## {name}' section")
        nonempty = sum(1 for l in text.replace("\r\n", "\n").split("\n")[d.start:] if l.strip())
        if nonempty > 80:
            add("LINES", "ADVISORY", 1, f"{nonempty} non-empty lines > 80", "cut to 80 lines or fewer; link the details")

    lens = sorted(s["words"] for s in sents)
    n = len(lens)
    summary = {"sentences": n, "mean": round(sum(lens) / n, 1) if n else 0.0,
               "p90": lens[max(0, math.ceil(0.9 * n) - 1)] if n else 0,
               "over30": round(100.0 * sum(1 for x in lens if x > 30) / n, 1) if n else 0.0,
               "over40": sum(1 for x in lens if x > 40),
               "blocks": sum(1 for f in out if f["severity"] == "BLOCK"),
               "advisories": sum(1 for f in out if f["severity"] == "ADVISORY")}
    out.sort(key=lambda f: (f["severity"] != "BLOCK", f["line"]))
    return out, summary


# ---------- output ----------
def human(findings, summary):
    lines = [f"{f['severity']} {f['check']} L{f['line']}: {f['excerpt']} → {f['fix']}" for f in findings]
    lines.append("sentences={sentences} mean={mean} p90={p90} over30={over30}% over40={over40} "
                 "blocks={blocks} advisories={advisories}".format(**summary))
    return "\n".join(lines)


def repair_message(findings, limit=600):
    blocks = [f for f in findings if f["severity"] == "BLOCK"]
    head = "no-slop: rewrite once. "
    tail = " Keep every fact, number, path and warning; change the register only. No apology."
    parts, budget = [], limit - len(head) - len(tail)
    for f in blocks:
        p = f"{f['check']}: \"{clip(f['excerpt'], 70)}\" → {f['fix']}."
        if len(" ".join(parts + [p])) > budget:
            break
        parts.append(p)
    return (head + " ".join(parts) + tail)[:limit]


def build_args(argv):
    ap = argparse.ArgumentParser(prog="slop-check.py", description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="*", help="files to check; '-' or none = stdin text")
    ap.add_argument("--stop-hook", action="store_true", help="read Stop hook JSON from stdin")
    ap.add_argument("--pretooluse", action="store_true", help="read PreToolUse (Write|Edit|MultiEdit) JSON from stdin")
    ap.add_argument("--profile", choices=["reply", "file", "handoff", "message", "procedure"])
    ap.add_argument("--json", action="store_true", help="print findings as a JSON list")
    ap.add_argument("--max-sentence", type=int, default=60)
    ap.add_argument("--cap-chars", type=int, default=3000)
    ap.add_argument("--top-words", type=int, default=150, help="reply profile: word budget above the detail line")
    ap.add_argument("--strict-top", action="store_true", help="reply profile: make TOP a BLOCK instead of ADVISORY")
    ap.add_argument("--lexicon", help="extra advisory terms, one per line")
    ap.add_argument("--require-sections", default=SECTIONS_DEFAULT)
    ap.add_argument("--durable-pattern", default=DURABLE_DEFAULT, help="--pretooluse: path regex to check")
    ap.add_argument("--quiet", action="store_true", help="no output; exit code only")
    ap.add_argument("--version", action="version", version=f"slop-check {VERSION}")
    args = ap.parse_args(argv)
    args.extra_lexicon = []
    if args.lexicon:
        with open(args.lexicon, encoding="utf-8") as fh:
            args.extra_lexicon = [l.strip() for l in fh if l.strip() and not l.lstrip().startswith("#")]
    return args


def run_stop_hook(args):
    data = json.loads(sys.stdin.read() or "{}")
    if data.get("stop_hook_active"):
        return 0
    text = data.get("last_assistant_message")
    if not isinstance(text, str) or len(WORD.findall(text)) < STOP_MIN_WORDS or mostly_code(text):
        return 0
    findings, _ = check(text, args.profile or "reply", args)
    if any(f["severity"] == "BLOCK" for f in findings):
        sys.stderr.write(repair_message(findings) + "\n")
        return 2
    return 0


def mostly_code(text):
    """True when more than half of the non-empty lines are fence markers or inside a fenced block."""
    total = code = 0
    open_marker = None
    for line in text.replace("\r\n", "\n").split("\n"):
        was_open = open_marker is not None
        open_marker, is_fence = _fence_step(open_marker, line)
        if line.strip():
            total += 1
            code += 1 if (is_fence or was_open) else 0
    return total > 0 and code * 2 > total


def _deny_allowed(data, path):
    """Count one denial of path in this session; False once DENY_CAP is reached or on any state error."""
    try:
        sid = re.sub(r"[^A-Za-z0-9_.-]", "_", str(data.get("session_id") or "default"))[:128].strip(".") or "default"
        d = os.path.join(os.environ.get("TMPDIR") or "/tmp", "no-slop-guard", sid)
        os.makedirs(d, exist_ok=True)
        state = os.path.join(d, "denials.json")
        counts = {}
        if os.path.exists(state):
            with open(state, encoding="utf-8") as fh:
                counts = json.load(fh)
            if not isinstance(counts, dict):
                return False
        n = int(counts.get(path, 0))
        if n >= DENY_CAP:
            return False
        counts[path] = n + 1
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".denials.")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(counts, fh)
        os.replace(tmp, state)
        return True
    except Exception:  # fail open
        return False


LIST_START = re.compile(r"^\s*([-*+]|\d+[.)])\s")


def touched_blocks(new, old):
    """The blocks of new that hold a line absent from old, joined with blank lines. A block ends at a blank
    line, a heading, a fence or a list-item start; a heading line is a block of its own, a fenced region (fence
    to fence) is one block."""
    old_lines = set(l.rstrip() for l in old.replace("\r\n", "\n").split("\n"))
    blocks, cur, open_marker = [], [], None

    def end():
        if cur:
            blocks.append(list(cur))
            del cur[:]

    for line in new.replace("\r\n", "\n").split("\n"):
        was_open = open_marker is not None
        open_marker, is_fence = _fence_step(open_marker, line)
        if is_fence:
            if not was_open:
                end()
            cur.append(line)
            if was_open and open_marker is None:
                end()
            continue
        if was_open:
            cur.append(line)
            continue
        if not line.strip():
            end()
        elif line.lstrip().startswith("#"):
            end()
            blocks.append([line])
        else:
            if LIST_START.match(line):
                end()
            cur.append(line)
    end()
    return "\n\n".join("\n".join(b) for b in blocks if any(l.rstrip() not in old_lines for l in b))


def _apply_edits(old, edits):
    """Apply Edit/MultiEdit edits in order; None when any old_string is missing or not found."""
    new = old
    for e in edits:
        a, b = e.get("old_string"), e.get("new_string")
        if not isinstance(a, str) or not isinstance(b, str) or not a or a not in new:
            return None
        new = new.replace(a, b) if e.get("replace_all") is True else new.replace(a, b, 1)
    return new


def run_pretooluse(args):
    data = json.loads(sys.stdin.read() or "{}")
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ""
    if not isinstance(path, str) or not path or not re.search(args.durable_pattern, path, I):
        return 0
    content = ti.get("content")
    if isinstance(ti.get("edits"), list):
        edits = [e for e in ti["edits"] if isinstance(e, dict)]
    elif "old_string" in ti or "new_string" in ti:
        edits = [ti]
    else:
        edits = []
    if isinstance(content, str) and content:
        text, whole = content, True
    else:
        text, whole = "\n".join(str(e.get("new_string") or "") for e in edits), False
    if os.path.isfile(path) and (whole or edits):
        # Judge only the blocks that hold a new line, whole, so an append-only log with old long sentences is
        # not denied for its history, and an edit inside a wrapped paragraph is judged with its whole paragraph.
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                old = fh.read()
            if not whole:
                done = _apply_edits(old, edits)
                if done is not None:
                    text, whole = done, True
            if whole:
                text = touched_blocks(text, old)
        except Exception:  # fail open to the fragment or content as given
            pass
    if not text.strip():
        return 0
    auto = "handoff" if re.search(r"NEXT_SESSION|HANDOFF|HANDOVER", path, I) else "file"
    findings, _ = check(text, args.profile or auto, args)
    if any(f["severity"] == "BLOCK" for f in findings) and _deny_allowed(data, path):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": repair_message(findings)}}, indent=1))
    return 0


def main(argv=None):
    args = build_args(sys.argv[1:] if argv is None else argv)
    if args.stop_hook or args.pretooluse:
        try:
            return run_stop_hook(args) if args.stop_hook else run_pretooluse(args)
        except Exception as e:  # fail open: a style gate must never brick a session
            sys.stderr.write(f"slop-check: internal error, passing: {e!r}\n")
            return 0
    targets = args.paths or ["-"]
    any_block, all_json, reports = False, [], []
    for p in targets:
        if p == "-":
            text, profile = sys.stdin.read(), args.profile or "reply"
        else:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
            profile = args.profile or "file"
        findings, summary = check(text, profile, args)
        any_block = any_block or summary["blocks"] > 0
        if args.json:
            all_json += [dict(f, file=p) for f in findings]
        else:
            reports.append((f"== {p}\n" if len(targets) > 1 else "") + human(findings, summary))
    if not args.quiet:
        print(json.dumps(all_json, indent=1, ensure_ascii=False) if args.json else "\n".join(reports))
    return 1 if any_block else 0


if __name__ == "__main__":
    sys.exit(main())

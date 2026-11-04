"""Tests for slop-check.py. Run: python3 -I -m unittest discover -s <this dir> -p "test_*.py"."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "slop-check.py")
INSTALLER = os.path.join(HERE, "install-guard.sh")

SLOP = (
    "Great question! The cache is not a bug, it's a contract gap that we found while reading the "
    "comparator code and the carrier code together during the long afternoon review with the whole "
    "team present and the dashboards open on every screen in the room so that everyone could see the "
    "numbers move as we changed the flags one at a time and wrote down each result.\n"
    "It's not a regression. It's a missing guard.\n"
    "The new path should work for every site.\n"
    "Three things matter next: R7, Q-E1 and the note in §7.1.2.\n"
    "Overall, the plan holds.\n\n"
    "Hope this helps!\n"
)
CLEAN = (
    "The comparator reads the totals before normalization. "
    "It flags 12 zero-tax lines on each run. "
    "The fix is in ECP-13392 and moves the read after normalization.\n"
)
FENCED = (
    "The script below prints a report.\n\n```\n"
    + " ".join(["word"] * 80) + ".\n```\n"
)
TABLE = (
    "| id | text |\n|---|---|\n| 1 | " + " ".join(["word"] * 80) + " it should work, not a bug, it's fine |\n"
)
LONG70 = " ".join(["word"] * 70) + "."


def run(args, stdin, tmpdir=None):
    """Run the checker; hook state goes to tmpdir (a fresh temp dir when None)."""
    own = tmpdir is None
    tmpdir = tempfile.mkdtemp() if own else tmpdir
    try:
        env = dict(os.environ, TMPDIR=tmpdir)
        return subprocess.run([sys.executable, "-I", SCRIPT] + args, input=stdin, env=env,
                              capture_output=True, text=True, timeout=30)
    finally:
        if own:
            shutil.rmtree(tmpdir, ignore_errors=True)


def ids(stdin, *args):
    r = run(["--json"] + list(args), stdin)
    return r, [f["check"] for f in json.loads(r.stdout)]


class TextModes(unittest.TestCase):
    def test_slop_paragraph_triggers_expected_checks(self):
        r, found = ids(SLOP)
        for cid in ("S60", "HEDGE", "FILL", "CODE-AS-NAME", "COUNT", "CLOSER"):
            self.assertIn(cid, found, cid)
        self.assertGreaterEqual(found.count("NEG"), 2)
        neg = [f for f in json.loads(r.stdout) if f["check"] == "NEG"]
        self.assertTrue(all(f["severity"] == "BLOCK" for f in neg))
        self.assertEqual(r.returncode, 1)

    def test_clean_paragraph_has_no_findings(self):
        r, found = ids(CLEAN)
        self.assertEqual(found, [])
        self.assertEqual(r.returncode, 0)

    def test_fenced_code_is_ignored(self):
        _, found = ids(FENCED)
        self.assertNotIn("S60", found)
        self.assertNotIn("S40", found)

    def test_table_only_has_no_sentence_findings(self):
        r, found = ids(TABLE)
        self.assertEqual(found, [])
        self.assertEqual(r.returncode, 0)

    def test_human_output_has_summary_line(self):
        r = run([], CLEAN)
        self.assertRegex(r.stdout.strip().splitlines()[-1], r"^sentences=3 mean=[\d.]+ p90=\d+ over30=")

    def test_wrapped_long_sentence_triggers_s60(self):
        words = LONG70[:-1].split()
        wrapped = "\n".join(" ".join(words[i:i + 18]) for i in range(0, 70, 18)) + ".\n"
        self.assertEqual(len(wrapped.strip().splitlines()), 4)
        r, found = ids(wrapped)
        self.assertIn("S60", found)
        self.assertEqual(json.loads(r.stdout)[0]["line"], 1)

    def test_wrapped_list_item_continuation_joins(self):
        words = LONG70[:-1].split()
        item = "- " + " ".join(words[:35]) + "\n  " + " ".join(words[35:]) + ".\n- Short item.\n"
        _, found = ids(item)
        self.assertIn("S60", found)

    def test_lex_skips_short_quotes_and_table_cells(self):
        quoted = 'Avoid coined jargon ("the unlock", \u201cload-bearing\u201d, "the seam").\n'
        table = "| term | note |\n|---|---|\n| load-bearing | banned |\n"
        for text in (quoted, table):
            _, found = ids(text)
            self.assertNotIn("LEX", found, text)
        _, found = ids("The load-bearing wall is the seam.\n")
        self.assertEqual(found.count("LEX"), 2)

    def test_message_cap_and_handoff_sections(self):
        _, found = ids("x " * 1600, "--profile", "message")
        self.assertIn("CAP", found)
        _, found = ids("# Goal\nShip it.\n", "--profile", "handoff")
        self.assertEqual(found.count("SECTIONS"), 7)

    def test_handoff_written_to_the_shape_has_no_sections_finding(self):
        heads = ["Goal", "First step", "State", "Decisions that bind", "Open items", "Traps", "Glossary", "Pointers"]
        text = "".join("## %d. %s\nThe item is short.\n\n" % (i + 1, h) for i, h in enumerate(heads))
        _, found = ids(text, "--profile", "handoff")
        self.assertNotIn("SECTIONS", found)
        _, found = ids(text.replace("## 6. Traps\n", "## 6. Risks\n"), "--profile", "handoff")
        self.assertEqual(found.count("SECTIONS"), 1)


class NegNarrowing(unittest.TestCase):
    PLAIN = ("The integration suite did not start, but the unit suite covers the changed mapper. "
             "I could not reach the staging API from this box, but the logs show the same error. "
             "The mapper change is small. "
             "I ran the unit suite twice on the branch and both runs passed with no new warnings. "
             "Next I will retry the integration suite after the runner restarts.")

    def test_plain_failure_reports_pass_the_stop_hook(self):
        import re
        self.assertEqual(len(re.findall(r"\b[\w'-]+\b", self.PLAIN)), 64)
        r = run(["--stop-hook", "--strict-top", "--top-words", "250"],
                json.dumps({"last_assistant_message": self.PLAIN}))
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        _, found = ids(self.PLAIN)
        self.assertNotIn("NEG", found)

    def test_not_just_but_and_not_a_x_still_block(self):
        r, found = ids("It's not just fast, but cheap. Not a bug. A design flaw.\n")
        neg = [f for f in json.loads(r.stdout) if f["check"] == "NEG"]
        self.assertEqual(len(neg), 2)
        self.assertTrue(all(f["severity"] == "BLOCK" for f in neg))
        self.assertEqual(r.returncode, 1)


class StopHook(unittest.TestCase):
    def test_active_flag_passes_silently(self):
        r = run(["--stop-hook"], json.dumps({"stop_hook_active": True, "last_assistant_message": SLOP}))
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_blocking_message_exits_2(self):
        r = run(["--stop-hook"], json.dumps({"stop_hook_active": False, "last_assistant_message": SLOP}))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.strip())
        self.assertLessEqual(len(r.stderr.strip()), 600)

    def test_bad_json_fails_open(self):
        r = run(["--stop-hook"], "not json")
        self.assertEqual(r.returncode, 0)


class PreToolUse(unittest.TestCase):
    def payload(self, path):
        return json.dumps({"tool_name": "Write", "tool_input": {"file_path": path, "content": LONG70}})

    def test_durable_file_is_denied(self):
        r = run(["--pretooluse"], self.payload("/repo/.claude/claude-docs/NEXT_SESSION_PROMPT.md"))
        self.assertEqual(r.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', r.stdout)

    def test_handoff_path_uses_handoff_profile(self):
        pre = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "/x/HANDOFF.md", "content": LONG70}})
        r = run(["--pretooluse"], pre)
        self.assertIn('"permissionDecision": "deny"', r.stdout)
        clean = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "/x/next_session.md",
                                                                  "content": "# Goal\nShip it.\n"}})
        self.assertEqual(run(["--pretooluse"], clean).stdout, "")

    def test_source_file_is_ignored(self):
        r = run(["--pretooluse"], self.payload("/repo/src/foo.scala"))
        self.assertEqual((r.returncode, r.stdout), (0, ""))


class StopHookSkips(unittest.TestCase):
    def test_short_message_passes(self):
        msg = "It's not a bug, it's fine. Should work. Hope this helps!"
        self.assertLess(len(msg.split()), 40)
        r = run(["--stop-hook"], json.dumps({"last_assistant_message": msg}))
        self.assertEqual((r.returncode, r.stderr), (0, ""))

    def test_code_only_message_passes(self):
        code = "```\n" + "\n".join(" ".join(["token"] * 20) for _ in range(20)) + "\n```\n"
        r = run(["--stop-hook", "--strict-top", "--top-words", "250"], json.dumps({"last_assistant_message": code}))
        self.assertEqual((r.returncode, r.stderr), (0, ""))

    def test_repair_message_prefix(self):
        r = run(["--stop-hook"], json.dumps({"last_assistant_message": SLOP}))
        self.assertTrue(r.stderr.startswith("no-slop:"))


class DenyCap(unittest.TestCase):
    def test_third_denial_of_same_path_allows(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        pre = json.dumps({"session_id": "s1", "tool_name": "Write",
                          "tool_input": {"file_path": "/x/NEXT_SESSION.md", "content": LONG70}})
        outs = [run(["--pretooluse"], pre, tmp).stdout for _ in range(3)]
        self.assertIn('"permissionDecision": "deny"', outs[0])
        self.assertIn('"permissionDecision": "deny"', outs[1])
        self.assertEqual(outs[2], "")
        other = pre.replace('"s1"', '"s2"')
        self.assertIn('"permissionDecision": "deny"', run(["--pretooluse"], other, tmp).stdout)

    def test_durable_pattern_is_markdown_only(self):
        def gated(path):
            pre = json.dumps({"tool_name": "Write", "tool_input": {"file_path": path, "content": LONG70}})
            return '"permissionDecision": "deny"' in run(["--pretooluse"], pre).stdout
        for path in ("src/PlanService.scala", "docs/explanation.md"):
            self.assertFalse(gated(path), path)
        for path in ("docs/PLAN.md", "notes/MY_PLAN-2026.md", ".serena/memories/core.md"):
            self.assertTrue(gated(path), path)

    def test_claude_docs_design_note_is_not_gated(self):
        pre = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "/r/.claude/claude-docs/x/design.md",
                                                               "content": LONG70}})
        self.assertEqual(run(["--pretooluse"], pre).stdout, "")


class Installer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.settings = os.path.join(self.tmp, "settings.json")

    def guard(self, *args, installer=INSTALLER):
        r = subprocess.run(["bash", installer] + list(args) + ["--settings-file", self.settings],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def hooks(self):
        with open(self.settings, encoding="utf-8") as fh:
            data = json.load(fh)
        return {ev: [h["command"] for g in groups for h in g["hooks"]]
                for ev, groups in data.get("hooks", {}).items()}

    def copy_scripts(self, name):
        d = os.path.join(self.tmp, name)
        os.makedirs(d)
        for f in ("slop-check.py", "install-guard.sh"):
            shutil.copy(os.path.join(HERE, f), d)
        return d

    def test_on_writes_fail_open_wrapper(self):
        self.guard("on")
        abs_ = os.path.realpath(SCRIPT)
        pre = "sh -c 'command -v python3 >/dev/null 2>&1 && [ -f \"%s\" ] && exec python3 -I \"%s\" " % (abs_, abs_)
        self.assertEqual(self.hooks(), {"Stop": [pre + "--stop-hook --strict-top --top-words 250 || exit 0'"],
                                        "PreToolUse": [pre + "--pretooluse || exit 0'"]})
        with open(self.settings, encoding="utf-8") as fh:
            group = json.load(fh)["hooks"]["PreToolUse"][0]
        self.assertEqual((group["matcher"], group["hooks"][0]["timeout"]), ("Edit|MultiEdit|Write", 20))
        stop = self.hooks()["Stop"][0]
        payload = json.dumps({"last_assistant_message": SLOP})
        self.assertEqual(subprocess.run(stop, shell=True, input=payload, text=True, capture_output=True).returncode, 2)
        broken = stop.replace(abs_, os.path.join(self.tmp, "gone", "slop-check.py"))
        self.assertEqual(subprocess.run(broken, shell=True, input=payload, text=True, capture_output=True).returncode, 0)

    def test_on_twice_is_ok_and_single(self):
        self.guard("on")
        out = self.guard("on")
        self.assertEqual([l.split()[0] for l in out.splitlines()], ["OK", "OK"])
        self.assertEqual({ev: len(c) for ev, c in self.hooks().items()}, {"Stop": 1, "PreToolUse": 1})
        self.assertEqual([l.split()[0] for l in self.guard("on", "--force").splitlines()], ["FIXED", "FIXED"])
        self.assertEqual({ev: len(c) for ev, c in self.hooks().items()}, {"Stop": 1, "PreToolUse": 1})

    def test_on_after_move_fixes_path(self):
        old = self.copy_scripts("old")
        self.guard("on", installer=os.path.join(old, "install-guard.sh"))
        new = os.path.join(self.tmp, "new")
        os.rename(old, new)
        self.assertTrue(self.guard("status", installer=os.path.join(new, "install-guard.sh")).strip()
                        .endswith("broken " + os.path.join(os.path.realpath(self.tmp), "old", "slop-check.py")))
        out = self.guard("on", installer=os.path.join(new, "install-guard.sh"))
        self.assertEqual([l.split()[0] for l in out.splitlines()], ["FIXED", "FIXED"])
        for cmds in self.hooks().values():
            self.assertEqual(len(cmds), 1)
            self.assertIn(os.path.join(os.path.realpath(new), "slop-check.py"), cmds[0])
            self.assertNotIn("/old/", cmds[0])
        self.assertIn(": on ", self.guard("status", installer=os.path.join(new, "install-guard.sh")))

    def test_on_repairs_old_unwrapped_form(self):
        old = "python3 -I %s --stop-hook" % os.path.realpath(SCRIPT)
        with open(self.settings, "w", encoding="utf-8") as fh:
            json.dump({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": old, "timeout": 20}]}]}}, fh)
        out = self.guard("on")
        self.assertTrue(out.splitlines()[0].startswith("FIXED custom Stop hook replaced"), out)
        stop = self.hooks()["Stop"]
        self.assertEqual(len(stop), 1)
        self.assertTrue(stop[0].startswith("sh -c 'command -v python3"), stop[0])
        self.assertIn("--stop-hook --strict-top --top-words 250 || exit 0'", stop[0])

    def test_on_replaces_hook_whose_matcher_differs(self):
        self.guard("on")
        with open(self.settings, encoding="utf-8") as fh:
            data = json.load(fh)
        data["hooks"]["PreToolUse"][0]["matcher"] = "Edit|Write"
        with open(self.settings, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        out = self.guard("on").splitlines()
        self.assertTrue(out[0].startswith("OK custom Stop"), out)
        self.assertTrue(out[1].startswith("FIXED custom PreToolUse hook replaced"), out)
        with open(self.settings, encoding="utf-8") as fh:
            groups = json.load(fh)["hooks"]["PreToolUse"]
        self.assertEqual([g["matcher"] for g in groups], ["Edit|MultiEdit|Write"])
        self.assertEqual([l.split()[0] for l in self.guard("on").splitlines()], ["OK", "OK"])

    def test_off_removes_both_and_keeps_other_hooks(self):
        with open(self.settings, "w", encoding="utf-8") as fh:
            json.dump({"model": "x", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo hi"}]}]}}, fh)
        self.guard("on")
        out = self.guard("off")
        self.assertEqual(sorted(l.split()[2] for l in out.splitlines()), ["PreToolUse", "Stop"])
        self.assertEqual(self.hooks(), {"Stop": ["echo hi"]})
        self.assertTrue(self.guard("status").strip().endswith(": off"))


class TopLayerTests(unittest.TestCase):
    def _run(self, text, *extra):
        import subprocess, sys, os
        here = os.path.dirname(os.path.abspath(__file__))
        r = subprocess.run([sys.executable, "-I", os.path.join(here, "slop-check.py"), "--profile", "reply", *extra],
                           input=text, capture_output=True, text=True)
        return r.returncode, r.stdout

    def test_top_over_budget_is_advisory(self):
        text = ("The build passed. " * 90) + "\n--- detail ---\nMore here."
        code, out = self._run(text)
        self.assertEqual(code, 0)
        self.assertIn("ADVISORY TOP", out)

    def test_top_under_budget_with_detail_below(self):
        text = "The build passed on commit abc12345.\n--- detail ---\n" + ("Log line here. " * 200)
        code, out = self._run(text)
        self.assertNotIn("TOP", out)

    def test_strict_top_blocks(self):
        text = ("The build passed. " * 90)
        code, out = self._run(text, "--strict-top")
        self.assertEqual(code, 1)
        self.assertIn("BLOCK TOP", out)




class NestedFenceTests(unittest.TestCase):
    def test_four_backtick_block_may_contain_three_backtick_fences(self):
        import subprocess, sys, os
        here = os.path.dirname(os.path.abspath(__file__))
        long = "word " * 70
        text = ("Short intro.\n\n````markdown\n## config\n```yaml\n# " + long + "\n```\n````\n\nShort outro.\n")
        r = subprocess.run([sys.executable, "-I", os.path.join(here, "slop-check.py"), "--profile", "file", "-"],
                           input=text, capture_output=True, text=True)
        self.assertNotIn("S60", r.stdout)
        self.assertEqual(r.returncode, 0)


class WriteGateNewLinesTests(unittest.TestCase):
    def test_existing_file_old_long_lines_are_not_judged(self):
        import subprocess, sys, os, json, tempfile
        here = os.path.dirname(os.path.abspath(__file__))
        long = "This old entry keeps going with another clause and yet another qualifier so that it runs well past sixty words, " * 4
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "DECISIONS.md")
            with open(path, "w") as fh:
                fh.write("# Log\n\n- " + long + "\n")
            payload = {"session_id": "t", "tool_name": "Write",
                       "tool_input": {"file_path": path, "content": "# Log\n\n- " + long + "\n- New entry: the guard is on. Status: decided.\n"}}
            env = dict(os.environ, TMPDIR=d)
            r = subprocess.run([sys.executable, "-I", os.path.join(here, "slop-check.py"), "--pretooluse"],
                               input=json.dumps(payload), capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")
            payload["tool_input"]["content"] += "- " + long.replace("old", "new") + "\n"
            r = subprocess.run([sys.executable, "-I", os.path.join(here, "slop-check.py"), "--pretooluse"],
                               input=json.dumps(payload), capture_output=True, text=True, env=env)
            self.assertIn('"permissionDecision": "deny"', r.stdout)


class EditGateCompletionTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.path = os.path.join(self.d, "DECISIONS.md")

    def write(self, body):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("# Log\n\n" + body + "\n")

    def gate(self, tool_input, tool="Edit"):
        ti = dict(tool_input, file_path=self.path)
        return run(["--pretooluse"], json.dumps({"session_id": "e", "tool_name": tool, "tool_input": ti}), self.d)

    @staticmethod
    def sentence(n):
        return " ".join("word%d" % i for i in range(n)) + "."

    def test_edit_that_completes_a_long_line_is_denied(self):
        self.write(self.sentence(60))  # at the limit: S60 needs more than 60 words
        r = self.gate({"old_string": "word7 word8", "new_string": "word7 extra word8"})
        self.assertEqual(r.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', r.stdout)

    def test_multiedit_applies_every_edit_in_order(self):
        self.write(self.sentence(59))
        r = self.gate({"edits": [{"old_string": "word3 ", "new_string": "word3 one "},
                                 {"old_string": "one word4", "new_string": "one two word4"}]}, tool="MultiEdit")
        self.assertIn('"permissionDecision": "deny"', r.stdout)

    def test_edit_with_fine_fragment_and_fine_line_is_allowed(self):
        self.write("The guard is on. Status: decided.")
        r = self.gate({"old_string": "decided", "new_string": "decided on 2026-11-02"})
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_old_string_not_found_falls_back_to_new_string(self):
        self.write("The guard is on.")
        r = self.gate({"old_string": "absent text", "new_string": "Short new line."})
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        r = self.gate({"old_string": "absent text", "new_string": LONG70})
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertIn('"permissionDecision": "deny"', r.stdout)


class WriteGateBlockTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.path = os.path.join(self.d, "DECISIONS.md")

    @staticmethod
    def wrapped(prefix, n, indent=""):
        import textwrap
        return textwrap.fill(" ".join("%s%d" % (prefix, i) for i in range(n)) + ".", 100,
                             subsequent_indent=indent)

    def write(self, text):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def gate(self, tool, ti):
        ti = dict(ti, file_path=self.path)
        return run(["--pretooluse"], json.dumps({"session_id": "b", "tool_name": tool, "tool_input": ti}), self.d)

    def base(self):
        return ("# Log\n\n" + self.wrapped("word", 60) + "\n\n- " + self.wrapped("item", 80, "  ") + "\n")

    def test_edit_inside_a_wrapped_paragraph_judges_the_whole_paragraph(self):
        text = self.base()
        self.assertGreater(len(self.wrapped("word", 60).splitlines()), 2)
        self.write(text)
        r = self.gate("Edit", {"old_string": "word7 word8", "new_string": "word7 extra word8"})
        self.assertEqual(r.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', r.stdout)

    def test_append_after_an_old_wrapped_bullet_judges_only_the_new_bullet(self):
        text = self.base()
        self.write(text)
        last = text.rstrip("\n").split("\n")[-1]
        r = self.gate("Edit", {"old_string": last, "new_string": last + "\n- Short new bullet."})
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_whole_file_write_judges_only_the_changed_paragraph(self):
        a, b = self.wrapped("alpha", 61), self.wrapped("beta", 30)
        old = "# Log\n\n" + a + "\n\n" + b + "\n"
        self.write(old)
        r = self.gate("Write", {"content": old.replace("beta5 ", "gamma5 ")})
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        r = self.gate("Write", {"content": old.replace("alpha5 ", "gamma5 ")})
        self.assertEqual(r.returncode, 0)
        self.assertIn('"permissionDecision": "deny"', r.stdout)


if __name__ == "__main__":
    unittest.main()

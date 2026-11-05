"""The runner: one subprocess per stage run, its record on disk, reconciliation after a restart, cancel.

Every heavy call is a subprocess of the main venv's python in its own process group, with stdout and stderr in the
record's log.txt. A stage's outputs are written to a `.part` path and renamed on exit 0, so an output that exists is
one that finished; `done` marks the record. A finished render is never overwritten (a new name); a rerun of the
registration moves the previous prep aside (in/<seq>_prev_<stamp>, keys.jpg copied forward), a rerun of the readers
replaces its folder, and a new page keeps the previous one beside its record and under its round. After a restart a
`running` or `cancelling` record whose process is gone is reconciled from its files (done, refused, cancelled) or
marked lost, never left pending.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import fnmatch
import os
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, inside, log, md5_file, now_iso, read_json, rel, stamp, tail_lines, write_json
from reveal_studio.jobs.candidates import candidates, rounds
from reveal_studio.jobs.plans import run_warnings
from reveal_studio.jobs.records import outputs_of, progress_of, record_dir, records
from reveal_studio.jobs.rounds import open_round
from reveal_studio.jobs.store import job_dirs
from reveal_studio.registry.flows import identity_of
from reveal_studio.runner.argv import ScriptFlags, argv_for, coerce

__all__ = ["Runner", "progress_of"]


def script_of(rec: Json) -> str | None:
    """The script a record runs, as its own argv names it (argv[1], repo-relative): the pid check and cancel look for
    it in the process's arguments, whatever flow's script it is."""
    argv = rec.get("argv") or []
    return str(argv[1]) if len(argv) > 1 else None


def _same(name: str, patterns: list[str]) -> bool:
    """Whether an output's file name is one of the stage's identity files (STUDIO.md §4: equal md5s say "unchanged")."""
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def _remove(p: Path) -> None:
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()


class Runner:
    """Holds the children this process started (`procs`), the records re-attached after a restart (`watching`) and
    the lock every record write takes (`state_lock`)."""

    def __init__(self, settings: Settings, flags: ScriptFlags) -> None:
        self.settings = settings
        self.flags = flags
        self.procs: dict[str, subprocess.Popen[bytes]] = {}
        self.watching: set[str] = set()
        self.state_lock = threading.Lock()

    progress_of = staticmethod(progress_of)

    def _rel(self, p: Path) -> str:
        return rel(p, self.settings.root)

    def start_stage(self, d: Path, job: Json, stage: Json, knobs: Json | None) -> Json:
        """Starts one run of a script stage into a new record; refuses (409) what the gates refuse."""
        knobs = coerce(stage, knobs)
        if stage["kind"] != "script":
            raise StudioError(f"the {stage['name']} stage is not a process", 400)
        if stage["name"] == "render" and not int(knobs.get("draft", 0)):
            rs = rounds(d)
            if rs and not rs[-1].get("grade") and not rs[-1].get("ungraded_by_his_word"):
                raise StudioError(
                    f"round {rs[-1]['n']} has no grade text: save his words, or mark the round ungraded by his word, "
                    "before the next round's first full render",
                    409,
                    {"round": rs[-1]["n"]},
                )
        if stage["name"] == "registration":
            busy = [r["id"] for r in records(d) if r["state"] in ("running", "cancelling")]
            if busy:
                raise StudioError(f"the registration waits: {', '.join(busy)} still read the prep", 409)
        rid = f"{stamp()}_{stage['name']}"
        rec_dir = d / "stages" / rid
        k = 1
        while rec_dir.exists():
            k += 1
            rec_dir = d / "stages" / f"{rid}_{k}"
        rid = rec_dir.name
        rec_dir.mkdir(parents=True)
        try:
            argv, out_final, out_part, inputs = argv_for(self.settings, self.flags, stage, d, job, knobs, rec_dir)
            warnings = run_warnings(self.settings, d, stage["name"], knobs, job["flow"])  # rulings warn, never refuse
            script = self.settings.root / argv[1]  # the record stamps the md5 of the script it runs
            if not script.is_file():
                raise StudioError(f"{argv[1]} is missing: the {stage['name']} stage cannot start", 409)
            script_md5 = md5_file(script)
            if out_final.exists() and stage["name"] == "render":
                raise StudioError(
                    f"{self._rel(out_final)} exists: choose another name (a finished render is never overwritten)", 409
                )
            for r in records(d):
                if r["state"] == "running" and r.get("out_part") == self._rel(out_part):
                    raise StudioError(f"{r['id']} is still running into {self._rel(out_part)}", 409)
            in_place = out_part == out_final  # a script that writes its output in place (director_page.py)
            previous = None
            if in_place:
                if out_final.is_file():  # the previous file is kept beside the record, since nothing is renamed
                    previous = f"previous_{out_final.name}"
                    shutil.copy2(out_final, rec_dir / previous)
            elif out_part.exists():
                _remove(out_part)
        except StudioError:
            shutil.rmtree(rec_dir, ignore_errors=True)
            raise
        with open(rec_dir / "log.txt", "ab") as logf:
            p = subprocess.Popen(
                argv,
                cwd=str(self.settings.root),
                stdout=logf,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"},
            )
        rec: Json = {
            "id": rid,
            "stage": stage["name"],
            "state": "running",
            "argv": argv,
            "pid": p.pid,
            "started": now_iso(),
            "ended": None,
            "wall_s": None,
            "exit_code": None,
            "knobs": knobs,
            "inputs": inputs,
            "outputs": [],
            "script_md5": script_md5,
            "out_part": self._rel(out_part),
            "out_final": self._rel(out_final),
            "terminal": stage["terminal"],
            "log": "log.txt",
            "ui_version": self.settings.ui_version,
            "warnings": warnings,
        }
        if in_place:
            rec["in_place"] = True
            rec["previous"] = previous
        write_json(rec_dir / "stage.json", rec)
        self.procs[rid] = p
        threading.Thread(target=self._wait, args=(d, rid, p), daemon=True).start()
        log(f"{job['id']} {rid}: pid {p.pid}: {' '.join(argv)}")
        return rec

    def _wait(self, d: Path, rid: str, p: subprocess.Popen[bytes]) -> None:
        rc = p.wait()
        self.procs.pop(rid, None)
        self.finalize(d, rid, rc)

    def finalize(self, d: Path, rid: str, rc: int | None) -> Json | None:
        """Writes the terminal state of a record from its exit code (None: unknown, after a restart) and its files."""
        rec_dir = d / "stages" / rid
        root = self.settings.root
        with self.state_lock:
            rec: Json | None = read_json(rec_dir / "stage.json")
            if not rec or rec["state"] not in ("running", "cancelling"):
                return rec
            out_part = (root / rec["out_part"]) if rec.get("out_part") else None
            out_final = (root / rec["out_final"]) if rec.get("out_final") else None
            term = rec.get("terminal")
            have = False
            if out_part is not None and out_part.exists():
                have = (out_part / term).exists() if out_part.is_dir() else True
            in_place = out_part is not None and out_part == out_final
            if in_place and rc is None:
                have = False  # an in-place file cannot say whether the restarted run finished: the record is lost
            lines = [ln for ln in tail_lines(rec_dir / "log.txt", 60) if ln.strip()]
            failed_line = next((ln for ln in reversed(lines) if ln.startswith("FAILED:")), None)
            if rec["state"] == "cancelling":
                rec["state"] = "cancelled"
                rec["reason"] = "cancelled; the server restarted before the record was written"
                if (
                    out_part is not None
                    and out_part.exists()
                    and ".part" in out_part.name
                    and inside(out_part, self.settings.runs)
                ):
                    _remove(out_part)
            elif (rc == 0 or rc is None) and have and out_part is not None and out_final is not None:
                if in_place:
                    pass  # written in place: the previous file was copied beside the record before the run
                elif out_final.exists():
                    if rec["stage"] == "registration":
                        prev = out_final.with_name(out_final.name + "_prev_" + stamp())
                        os.replace(out_final, prev)
                        if (prev / "keys.jpg").exists():  # the existing pages link in/<seq>/keys.jpg
                            shutil.copy2(prev / "keys.jpg", out_part / "keys.jpg")
                        rec["note"] = (
                            f"the previous prep moved to {rel(prev, root)}; "
                            "the renders and readers made from it are stale"
                        )
                    elif rec["stage"] == "page":
                        prev = rec_dir / "previous_index.html"
                        shutil.copy2(out_final, prev)
                        rec["note"] = "the previous page is kept under its round and beside this record"
                    elif out_final.is_dir():
                        shutil.rmtree(out_final)  # readers: derived files, replaced
                    else:
                        out_final.unlink()
                if not in_place:
                    os.replace(out_part, out_final)
                rec["state"] = "done"
                if rc is None:
                    rec["note"] = (
                        rec.get("note", "")
                        + " finished after a restart: the exit code is unknown; the terminal file was present"
                    ).strip()
                (rec_dir / "done").write_text(now_iso())
            elif failed_line and (rc == 2 or rc is None):
                rec["state"] = "refused"
                rec["reason"] = failed_line
            elif rc is None:
                rec["state"] = "lost"
                rec["reason"] = "the server restarted while the stage ran and no terminal file was found: run it again"
                if (
                    out_part is not None
                    and out_part.exists()
                    and ".part" in out_part.name
                    and inside(out_part, self.settings.runs)
                ):
                    _remove(out_part)
                    rec["note"] = "the partial .part folder was removed"
            else:
                rec["state"] = "failed"
                rec["reason"] = (lines[-1] if lines else f"exit {rc} with an empty log")[-300:]
            rec["ended"] = now_iso()
            try:
                rec["wall_s"] = round(
                    (
                        dt.datetime.fromisoformat(rec["ended"]) - dt.datetime.fromisoformat(rec["started"])
                    ).total_seconds(),
                    1,
                )
            except ValueError:
                rec["wall_s"] = None
            rec["exit_code"] = rc
            write_json(rec_dir / "stage.json", rec)
        if (
            rec["state"] == "done" and out_final is not None
        ):  # the md5s outside the lock: a render with --frames holds 50–300 files
            outputs = outputs_of(self.settings, out_final)
            if rec["stage"] == "readers":
                outputs += [
                    {
                        "path": rel(q, root),
                        "md5": md5_file(q),
                        "bytes": q.stat().st_size,
                        "note": "written beside the prep by readers (a plan's depth effects read it there)",
                    }
                    for q in sorted(out_final.parent.glob("depth_k*.npy"))
                ]
            patterns = identity_of((read_json(d / "job.json") or {}).get("flow"), rec["stage"])
            mine = sorted((Path(o["path"]).name, o["md5"]) for o in outputs if _same(Path(o["path"]).name, patterns))
            prev_recs = [
                r
                for r in records(d)
                if r["stage"] == rec["stage"] and r["state"] == "done" and r["id"] != rid and r.get("outputs")
            ]
            unchanged = None
            if mine and prev_recs:
                theirs = sorted(
                    (Path(o["path"]).name, o["md5"])
                    for o in prev_recs[-1]["outputs"]
                    if _same(Path(o["path"]).name, patterns)
                )
                if theirs == mine:
                    unchanged = prev_recs[-1]["id"]
            with self.state_lock:
                fresh: Json = read_json(rec_dir / "stage.json")
                fresh["outputs"] = outputs
                if unchanged:
                    fresh["unchanged_from"] = (
                        unchanged  # STUDIO.md §4: a rerun whose outputs' md5s equal the previous run's says so
                    )
                write_json(rec_dir / "stage.json", fresh)
            rec = fresh
        log(f"{d.name} {rid}: {rec['state']}" + (f" ({rec.get('reason')})" if rec.get("reason") else ""))
        if rec["state"] == "done":
            self.after_done(d, rec)
        return rec

    def after_done(self, d: Path, rec: Json) -> None:
        """What a finished stage adds to the job: a page opens a round (jobs/rounds.py: page.md5 beside the page)."""
        if rec["stage"] != "page":
            return
        job: Json = read_json(d / "job.json")
        page = self.settings.root / rec["out_final"]
        variants = list(rec["knobs"].get("variants") or [])  # [] = every full render in name order (backlog T76)
        names = variants or [c["name"] for c in candidates(self.settings, d, job) if c["kind"] == "full"]
        open_round(d, page, names, variants=variants, record=rec["id"], override=rec["knobs"].get("override") or None)

    def pid_alive(self, pid: int, rec: Json | None = None) -> bool:
        """Whether the pid runs; with a record, whether it runs that record's own script (its argv[1]) into that
        record's .part path, so a live child of any flow re-attaches and a stranger reusing the pid is never one."""
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        try:
            args = subprocess.run(
                ["ps", "-o", "args=", "-p", str(pid)], capture_output=True, text=True, timeout=5
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return True
        if rec is None:
            return bool(args.strip())
        script = script_of(rec)
        needle = rec.get("out_part") or "\0"
        if rec.get("in_place"):  # the page script names the folder it writes into, never the file
            needle = str(Path(needle).parent)
        return bool(script) and str(script) in args and needle in args

    def _watch_pid(self, d: Path, rid: str, pid: int) -> None:
        while self.pid_alive(pid):
            time.sleep(1)
        self.watching.discard(rid)
        self.finalize(d, rid, None)

    def reconcile(self, d: Path, rec: Json) -> Json:
        """A running record whose process this server did not start: alive → watched; gone → done from its files, else
        lost."""
        if rec.get("state") not in ("running", "cancelling") or rec["id"] in self.procs:
            return rec
        if self.pid_alive(rec["pid"], rec):
            if rec["id"] not in self.watching:
                self.watching.add(rec["id"])
                threading.Thread(target=self._watch_pid, args=(d, rec["id"], rec["pid"]), daemon=True).start()
                log(f"{d.name} {rec['id']}: pid {rec['pid']} still runs after a restart; re-attached")
            return rec
        return self.finalize(d, rec["id"], None) or rec

    def reconcile_all(self) -> int:
        """Reconciles every running or cancelling record of every job; returns how many it found."""
        n = 0
        for d in job_dirs(self.settings):
            for r in records(d):
                if r.get("state") in ("running", "cancelling"):
                    self.reconcile(d, r)
                    n += 1
        if n:
            log(f"reconciled {n} running record(s) at start")
        return n

    def cancel(self, d: Path, rid: str) -> Json:
        """SIGTERM to the record's process group after the pid identity check, SIGKILL after 5 s; the .part removed."""
        rec_dir = record_dir(d, rid)
        rec: Json = read_json(rec_dir / "stage.json")
        if rec["state"] == "running" and rid not in self.procs and not self.pid_alive(rec["pid"], rec):
            return self.reconcile(d, rec)  # the process is gone (or the pid is a stranger's): no signal
        with self.state_lock:
            rec = read_json(rec_dir / "stage.json")
            if rec["state"] != "running":
                raise StudioError(f"{rid} is {rec['state']}, not running", 409)
            rec["state"] = "cancelling"
            write_json(rec_dir / "stage.json", rec)
        with contextlib.suppress(ProcessLookupError):
            os.killpg(rec["pid"], signal.SIGTERM)
        p = self.procs.get(rid)
        deadline = time.time() + 5
        while self.pid_alive(rec["pid"]) and time.time() < deadline:
            time.sleep(0.2)
        if self.pid_alive(rec["pid"]):
            with contextlib.suppress(ProcessLookupError):
                os.killpg(rec["pid"], signal.SIGKILL)
        if p is not None:
            with contextlib.suppress(subprocess.TimeoutExpired):
                p.wait(timeout=5)
        self.procs.pop(rid, None)
        with self.state_lock:
            rec = read_json(rec_dir / "stage.json")
            rec["state"] = "cancelled"
            rec["ended"] = now_iso()
            rec["wall_s"] = round(
                (dt.datetime.fromisoformat(rec["ended"]) - dt.datetime.fromisoformat(rec["started"])).total_seconds(), 1
            )
            rec["reason"] = "cancelled by you"
            out_part = (self.settings.root / rec["out_part"]) if rec.get("out_part") else None
            if (
                out_part is not None
                and out_part.exists()
                and ".part" in out_part.name
                and inside(out_part, self.settings.runs)
            ):
                _remove(out_part)
                rec["note"] = "the .part folder was removed"
            write_json(rec_dir / "stage.json", rec)
        log(f"{d.name} {rid}: cancelled")
        return rec

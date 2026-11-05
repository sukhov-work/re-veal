"""Where jobs live and how one is found, read, made from a folder of stills, or adopted from an existing run folder.

  benchmarks/runs/<date>/studio/<job_id>/
    job.json                 {id, flow, created, ui_version, root, seq, inputs: [{name, path, sha256, bytes}], adopted}
    raw/<seq>/<nn>.jpg       symlinks to the originals in capture order (a new job; `prep` reads this folder)
    stages/<stamp>_<name>/   stage.json and log.txt: one record per run; `done` marks a finished one
    plans/<name>.json        the plans this job rendered, each with a provenance block
    requests/, answers/      the session's inbox (skeptic_<stamp>.json) and what it wrote back
    rounds/<n>/round.json    a page over the candidates, its md5, his grade text verbatim
    owner_frames/            frames he marked
    cache/                   thumbnails and decoded frames (derived; safe to delete)
The run folder `root` (the job folder itself, or an adopted run folder) keeps `loop_seq.py page`'s layout:
in/<seq>/ the prep, <seq>/<name>/ the full renders, drafts/<seq>/<name>/ the drafts, index.html and page.md5.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, inside, log, md5_file, now_iso, read_json, rel, sha256_file, stamp, write_json
from reveal_studio.registry.loop import FLOWS
from reveal_studio.registry.schema import ID_RE, NAME_RE


def studio_dir(settings: Settings, date: str | None = None) -> Path:
    return settings.runs / (date or settings.runs_date) / "studio"


def job_dirs(settings: Settings) -> list[Path]:
    """Every job folder of every date, oldest first by `created`."""
    out = [jj.parent for jj in settings.runs.glob("*/studio/*/job.json")]
    return sorted(out, key=lambda d: (read_json(d / "job.json", {}) or {}).get("created", ""))


def find_job(settings: Settings, jid: str) -> Path:
    if not ID_RE.match(jid or ""):
        raise StudioError("a job id is letters, digits, dot, dash and underscore", 400)
    for jj in settings.runs.glob(f"*/studio/{jid}/job.json"):
        return jj.parent
    raise StudioError(f"no job {jid}", 404)


def load_job(settings: Settings, jid: str) -> tuple[Path, Json]:
    d = find_job(settings, jid)
    job = read_json(d / "job.json")
    if not job:
        raise StudioError(f"{rel(d, settings.root)}/job.json is unreadable", 500)
    return d, job


def job_root(settings: Settings, job: Json) -> Path:
    """The run folder the job reads and writes its prep, renders and page in."""
    root: str = job["root"]
    return (settings.root / root).resolve()


def prep_dir(settings: Settings, job: Json) -> Path:
    seq: str = job["seq"]
    return job_root(settings, job) / "in" / seq


def list_stills(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg") and not p.name.startswith("."))


def create_job(
    settings: Settings, flow: str, folder: str | None = None, adopt: str | None = None, seq: str | None = None
) -> Json:
    """A new job from a folder of developed JPGs (symlinks and sha256s), or an adopted run folder (round 1 = page)."""
    if flow not in FLOWS:
        raise StudioError(
            f"the flow is one of {sorted(FLOWS)} "
            "(phase A1 builds the loop flow; align, pair and director are phases B and C)",
            400,
        )
    if adopt:
        # imported here: candidates reads job_root from this module
        from reveal_studio.jobs.candidates import candidates

        root = (settings.root / adopt).resolve()
        if not inside(root, settings.runs) or not root.is_dir():
            raise StudioError("a run folder to adopt lies under benchmarks/runs/", 400)
        if not seq or not NAME_RE.match(seq):
            raise StudioError("adopt needs the sequence's name (the folder under in/)", 400)
        prep = read_json(root / "in" / seq / "prep.json")
        if not prep:
            raise StudioError(f"{rel(root, settings.root)}/in/{seq}/prep.json not found: nothing to adopt", 404)
        jid = f"{flow}_{seq}_{stamp()}"
        d = studio_dir(settings) / jid
        d.mkdir(parents=True)
        inputs = [
            {
                "name": Path(s["source"]).name,
                "path": s["source"],
                "sha256": s["sha256"],
                "bytes": s["bytes"],
                "native": s.get("native"),
            }
            for s in prep.get("sources", [])
        ]
        job: Json = {
            "id": jid,
            "flow": flow,
            "created": now_iso(),
            "ui_version": settings.ui_version,
            "root": rel(root, settings.root),
            "seq": seq,
            "inputs": inputs,
            "adopted": True,
            "adopted_from": rel(root, settings.root),
        }
        write_json(d / "job.json", job)
        page = root / "index.html"
        if page.exists():
            md5v = md5_file(page)
            recorded = (root / "page.md5").read_text().split()[0] if (root / "page.md5").exists() else None
            names = [c["name"] for c in candidates(settings, d, job) if c["kind"] == "full"]
            (d / "rounds" / "1").mkdir(parents=True, exist_ok=True)
            shutil.copy2(page, d / "rounds" / "1" / "index.html")
            write_json(
                d / "rounds" / "1" / "round.json",
                {
                    "n": 1,
                    "at": now_iso(),
                    "candidates": names,
                    "page_md5": md5v,
                    "page_md5_recorded": recorded,
                    "page": "index.html",
                    "override": None,
                    "grade": None,
                    "ungraded_by_his_word": None,
                    "note": "adopted: the page the session built before the studio existed",
                },
            )
        log(
            f"job {jid}: adopted {rel(root, settings.root)} "
            f"({len(inputs)} stills, page {'yes' if page.exists() else 'no'})"
        )
        return job
    if not folder:
        raise StudioError("a new job needs a folder of developed JPGs, or a run folder to adopt", 400)
    src = Path(folder).expanduser()
    if not src.is_absolute():
        src = settings.root / src
    src = src.resolve()
    if not src.is_dir():
        raise StudioError(f"{src} is not a folder", 400)
    stills = list_stills(src)
    if len(stills) < 2:
        raise StudioError(
            f"{src}: {len(stills)} developed JPGs, need 2 or more "
            "(prep reads .jpg and .jpeg only; convert HEIC or PNG stills first)",
            400,
        )
    seq = seq or re.sub(r"[^a-z0-9]+", "_", src.name.lower()).strip("_")[:40] or "seq"
    if not NAME_RE.match(seq):
        raise StudioError("the sequence's name is letters, digits, dash and underscore", 400)
    jid = f"{flow}_{seq}_{stamp()}"
    d = studio_dir(settings) / jid
    raw = d / "raw" / seq
    raw.mkdir(parents=True)
    inputs = []
    for i, p in enumerate(stills, 1):
        link = raw / f"{i:02d}.jpg"
        os.symlink(p, link)
        inputs.append(
            {
                "name": p.name,
                "path": str(p),
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
                "link": rel(link, settings.root),
            }
        )
    job = {
        "id": jid,
        "flow": flow,
        "created": now_iso(),
        "ui_version": settings.ui_version,
        "root": rel(d, settings.root),
        "seq": seq,
        "inputs": inputs,
        "adopted": False,
        "source_folder": str(src),
    }
    write_json(d / "job.json", job)
    log(f"job {jid}: {len(stills)} stills of {src} linked under {rel(raw, settings.root)}")
    return job

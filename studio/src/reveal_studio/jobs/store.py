"""Where jobs live and how one is found, read, or made: a loop job from a folder of stills or an adopted run folder,
a pair job from a fixture pair or two photos, a director job from a pair that a director plan names.

  benchmarks/runs/<date>/studio/<job_id>/
    job.json                 {id, flow, created, ui_version, root, seq, inputs: [{name, path, sha256, bytes}], adopted}
                             (every flow writes `seq`: the sequence, or the pair's name; a pair's or a director's
                             inputs carry `role` A or B and keep their extension in the link)
    raw/<seq>/<nn>.jpg       symlinks to the originals in capture order (a new job; `prep` reads this folder)
    raw/<pair>/A.<ext>, B.<ext>   a pair or director job's two photos (transitions.py picks its reader by suffix)
    stages/<stamp>_<name>/   stage.json and log.txt: one record per run; `done` marks a finished one
    plans/<name>.json        the plans this job rendered, each with a provenance block
    requests/, answers/      the session's inbox (skeptic_<stamp>.json) and what it wrote back
    rounds/<n>/round.json    a page over the candidates, its md5, his grade text verbatim
    owner_frames/            frames he marked
    cache/                   thumbnails and decoded frames (derived; safe to delete)
The run folder `root` (the job folder itself, or an adopted run folder) keeps `loop_seq.py page`'s layout:
in/<seq>/ the prep, <seq>/<name>/ the full renders, drafts/<seq>/<name>/ the drafts, index.html and page.md5.
A director job's root is its run/ folder, the folder director_page.py reads; its job.json also names the layer and
matte roots, the layer table and the matte count of each photo, and the helper files the pair's plans name.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, inside, log, md5_file, now_iso, read_json, rel, sha256_file, stamp, write_json
from reveal_studio.registry.flows import ALL_FLOWS, FLOWS
from reveal_studio.registry.pair import RESERVED_NAMES
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
    settings: Settings,
    flow: str,
    folder: str | None = None,
    adopt: str | None = None,
    seq: str | None = None,
    *,
    fixture: str | None = None,
    a: str | None = None,
    b: str | None = None,
    pair: str | None = None,
) -> Json:
    """A new job of an enabled flow (POST /api/jobs): a loop job from a folder of developed JPGs or an adopted run
    folder, a pair job from a fixture pair or two photos, a director job from a pair a director plan names. A flow that
    is registered but not enabled is refused here; its creator below is what its builder and the tests call."""
    if flow not in FLOWS:
        off = [f for f in ALL_FLOWS if f not in FLOWS]
        later = f" ({' and '.join(off)} {'is' if len(off) == 1 else 'are'} registered but not built yet)" if off else ""
        raise StudioError(f"the flow is one of {sorted(FLOWS)}{later}", 400)
    if flow == "pair":
        return create_pair_job(settings, fixture=fixture, a=a, b=b, seq=seq)
    if flow == "director":
        return create_director_job(settings, pair or fixture)
    if adopt:
        return adopt_loop_job(settings, adopt, seq)
    return create_loop_job(settings, folder, seq)


def adopt_loop_job(settings: Settings, adopt: str, seq: str | None) -> Json:
    """A run folder made before the studio (benchmarks/runs/<date>/<run>) as a loop job: its page becomes round 1."""
    flow = "loop"
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
        f"job {jid}: adopted {rel(root, settings.root)} ({len(inputs)} stills, page {'yes' if page.exists() else 'no'})"
    )
    return job


def create_loop_job(settings: Settings, folder: str | None, seq: str | None) -> Json:
    """A new loop job from a folder of developed JPGs: one symlink per still in capture order and a sha256 each."""
    flow = "loop"
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


def slug(text: str, fallback: str) -> str:
    """Lowercase letters and digits, every other run of characters one underscore, at most 40: a name NAME_RE takes."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or fallback


def fixture_photos(settings: Settings, name: str) -> tuple[Path, Path]:
    """The fixture pair's two photos: the first fixtures/<name>_S.* and fixtures/<name>_F.* in name order, the rule of
    layered_probe.py's find_pair, which the director renderer's plans follow."""
    if not NAME_RE.match(name or ""):
        raise StudioError("a pair's name is letters, digits, dash and underscore", 400)
    found = [
        sorted(p for p in settings.fixtures.glob(f"{name}_{side}.*") if p.is_file() and not p.name.startswith("."))
        for side in ("S", "F")
    ]
    if not found[0] or not found[1]:
        raise StudioError(
            f"no fixture pair {name}: {rel(settings.fixtures, settings.root)}/{name}_S.* and _F.* are both needed", 404
        )
    return found[0][0], found[1][0]


def _photo(settings: Settings, given: str, role: str) -> Path:
    p = Path(given).expanduser()
    p = (p if p.is_absolute() else settings.root / p).resolve()
    if not p.is_file():
        raise StudioError(f"photo {role}: {p} is not a file", 400)
    return p


def _link(settings: Settings, raw: Path, role: str, src: Path) -> Json:
    """raw/<seq>/<role><ext>: a symlink to the original, its extension kept, with the original's sha256. `link` is the
    link's own repo-relative path (rel() would resolve it to the original, a fixture inside the root)."""
    link = raw / f"{role}{src.suffix}"
    os.symlink(src, link)
    return {
        "role": role,
        "name": src.name,
        "path": str(src),
        "sha256": sha256_file(src),
        "bytes": src.stat().st_size,
        "link": str(link.relative_to(settings.root)),
    }


def _new_dir(settings: Settings, flow: str, seq: str) -> tuple[str, Path, Path]:
    """The id, the job folder and its raw/<seq>/ folder, made (one-second ids: the known defect of ARCHITECTURE.md)."""
    jid = f"{flow}_{seq}_{stamp()}"
    d = studio_dir(settings) / jid
    raw = d / "raw" / seq
    raw.mkdir(parents=True)
    return jid, d, raw


def create_pair_job(
    settings: Settings,
    fixture: str | None = None,
    a: str | None = None,
    b: str | None = None,
    seq: str | None = None,
) -> Json:
    """A pair job from a fixture pair (`fixture`: its name, which is also `seq`) or from two photos `a` and `b` (each
    a path, or one relative to the root; `seq` a slug of the two file stems unless given). Each photo is linked, never
    copied."""
    if fixture:
        photos = fixture_photos(settings, fixture)
        seq = seq or fixture
    elif a and b:
        photos = (_photo(settings, a, "A"), _photo(settings, b, "B"))
        seq = seq or slug(f"{photos[0].stem}_{photos[1].stem}", "pair")
    else:
        raise StudioError("a pair job needs a fixture pair's name, or two photos a and b", 400)
    if not NAME_RE.match(seq):
        raise StudioError("the pair's name is letters, digits, dash and underscore", 400)
    if seq in RESERVED_NAMES:
        raise StudioError(
            f"the pair's name {seq!r} is a folder of the job itself (its full renders would sit inside another stage's "
            "folder): choose another name",
            400,
        )
    jid, d, raw = _new_dir(settings, "pair", seq)
    inputs = [_link(settings, raw, "A", photos[0]), _link(settings, raw, "B", photos[1])]
    job: Json = {
        "id": jid,
        "flow": "pair",
        "created": now_iso(),
        "ui_version": settings.ui_version,
        "root": rel(d, settings.root),
        "seq": seq,
        "inputs": inputs,
        "fixture": fixture or None,
        "adopted": False,
    }
    write_json(d / "job.json", job)
    log(f"job {jid}: photos {photos[0].name} and {photos[1].name} linked under {rel(raw, settings.root)}")
    return job


def director_plans_of(settings: Settings, pair: str) -> list[tuple[Path, Json]]:
    """The frozen director plans (scripts/research/plans/*.json, not the loops/ folder) whose `pair` is this one."""
    out = []
    for p in sorted(settings.director_plans.glob("*.json")):
        plan = read_json(p)
        if isinstance(plan, dict) and plan.get("pair") == pair:
            out.append((p, plan))
    return out


def _keyframes(o: Any, out: list[str]) -> list[str]:
    """Every string of every `keyframes` list in a plan, in order, each once: the generated helper pictures."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "keyframes" and isinstance(v, list):
                out += [x for x in v if isinstance(x, str) and x not in out]
            else:
                _keyframes(v, out)
    elif isinstance(o, list):
        for v in o:
            _keyframes(v, out)
    return out


def _table(settings: Settings, layers: Path, photo: str) -> tuple[Json | None, list[int] | None]:
    """A photo's layer table (<layers>/<photo>/layers.json) as {path, sha256, elements}, and its element ids."""
    f = layers / photo / "layers.json"
    t = read_json(f)
    if not isinstance(t, dict):
        return None, None
    ids = [int(e["id"]) for e in t.get("elements") or [] if isinstance(e, dict) and "id" in e]
    return {"path": rel(f, settings.root), "sha256": sha256_file(f), "elements": len(ids)}, ids


def _mattes(mattes: Path, photo: str, ids: list[int] | None) -> Json:
    """A photo's matte files (<mattes>/<photo>/el_<id>.png): the count, and the element ids without one."""
    folder = mattes / photo
    have = {int(p.stem[3:]) for p in folder.glob("el_*.png") if p.stem[3:].isdigit()} if folder.is_dir() else set()
    return {"count": len(have), "missing": None if ids is None else [i for i in ids if i not in have]}


def create_director_job(settings: Settings, pair: str | None) -> Json:
    """A director job for a fixture pair that a director plan names: the two photos linked as records (the renderer
    reads fixtures/ by the plan's pair), the layer table and the matte count of each photo, and the helper files the
    pair's plans name, hashed. A pair without a plan is refused before any folder is made."""
    if not pair or not NAME_RE.match(pair):
        raise StudioError("a director job names its pair: letters, digits, dash and underscore", 400)
    plans = director_plans_of(settings, pair)
    if not plans:
        raise StudioError(
            f"no plan under {rel(settings.director_plans, settings.root)}/ names the pair {pair}: "
            "a director job renders a plan",
            400,
        )
    photos = fixture_photos(settings, pair)
    jid, d, raw = _new_dir(settings, "director", pair)
    (d / "run").mkdir()
    inputs = [_link(settings, raw, "A", photos[0]), _link(settings, raw, "B", photos[1])]
    tables: Json = {}
    mattes: Json = {}
    for role, p in zip(("A", "B"), photos, strict=True):
        tables[role], ids = _table(settings, settings.layers_dir, p.stem)
        mattes[role] = _mattes(settings.mattes_dir, p.stem, ids)
    names = _keyframes([plan for _, plan in plans], [])
    helpers = [
        {"path": h, "sha256": sha256_file(settings.root / h) if (settings.root / h).is_file() else None} for h in names
    ]
    job: Json = {
        "id": jid,
        "flow": "director",
        "created": now_iso(),
        "ui_version": settings.ui_version,
        "root": rel(d / "run", settings.root),
        "seq": pair,
        "pair": pair,
        "inputs": inputs,
        "layers_dir": rel(settings.layers_dir, settings.root),
        "mattes_dir": rel(settings.mattes_dir, settings.root),
        "tables": tables,
        "mattes": mattes,
        "helpers": helpers,
        "adopted": False,
    }
    write_json(d / "job.json", job)
    log(f"job {jid}: the pair {pair} ({len(plans)} plans, {len(helpers)} helper files) under {rel(d, settings.root)}")
    return job

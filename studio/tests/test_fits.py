"""views/fits.py: the registration's named windows under each fit, from prep.json as `loop_seq.py prep --windows`
writes it (SCHEMA.md 2026-11-05; research/2026-11-05/loopseq_a2.md §2.1), on a synthetic prep and on the real angel
preps of the research run when they are present."""

from __future__ import annotations

import pytest

from reveal_studio.fs import Json, read_json
from reveal_studio.views.fits import FIT_ORDER, fits_summary

from .conftest import REPO


def fit(dx: float, dy: float, corr: float = 0.99, edge: bool = False) -> Json:
    return {"dx": dx, "dy": dy, "corr": corr, "edge": edge}


def synthetic_prep() -> Json:
    """Three frames: frame 1 with every fit in a scrambled key order, frame 2 a declared cut, frame 3 chained."""
    return {
        "reference": 0,
        "crop": [29, 0, 1395, 1770],
        "windows": {"ring_top": [422, 371, 582, 441], "exit_sign": [1084, 20, 1284, 130], "edge_box": [0, 10, 40, 60]},
        "frames": [
            {"method": "reference"},
            {
                "method": "sift+magsac + lock",
                "lock": {"windows": [[422, 371, 582, 441]], "offsets_px": [[6.14, -12.59]], "shift_px": [-4.93, 11.48]},
                "windows": {
                    "ring_top": {
                        "box": [422, 371, 582, 441],
                        "box_canvas": [393, 371, 553, 441],
                        "fits": {
                            "final": fit(1.4, -1.09, 0.994),
                            "ecc": fit(1.38, -12.29),
                            "all": fit(6.14, -12.59, 0.992),
                            "far": fit(5.25, -7.32, 0.994),
                        },
                    },
                    "exit_sign": {
                        "box": [1084, 20, 1284, 130],
                        "box_canvas": [1055, 20, 1255, 130],
                        "fits": {"all": fit(1.58, 15.62), "final": fit(-3.39, 27.09, 0.977)},
                    },
                    "edge_box": {
                        "box": [0, 10, 40, 60],
                        "box_canvas": None,
                        "fits": {"all": fit(30.0, -2.0, 0.6, True), "final": fit(30.0, -2.0, 0.6, True)},
                    },
                },
            },
            {"method": "cut"},
            {
                "method": "sift+magsac via frame 2",
                "windows": {
                    "ring_top": {"box": [422, 371, 582, 441], "box_canvas": None, "fits": {"chain": fit(-0.3, 0.0)}},
                },
            },
        ],
    }


def test_no_windows_no_table() -> None:
    # A prep made without --windows has no top-level `windows`: the panel draws no table.
    assert fits_summary({"frames": [{}, {"method": "sift+magsac"}]}) is None
    assert fits_summary(None) is None and fits_summary({"windows": "x"}) is None


def test_the_fits_come_in_the_prep_order_whatever_the_keys_order() -> None:
    s = fits_summary(synthetic_prep())
    assert s is not None
    assert FIT_ORDER == ("all", "far", "chain", "ecc", "final")
    # Mutation: iterating the fits in the file's key order (final first) turns these red.
    assert s["fits"] == ["all", "far", "chain", "ecc", "final"]
    f1, f3 = s["frames"]
    assert f1["fits"] == ["all", "far", "ecc", "final"]  # frame 1 made no chain: no column for it
    assert f3["fits"] == ["chain"]
    assert list(f1["rows"][0]["cells"]) == ["all", "far", "ecc", "final"]


def test_cells_carry_dx_dy_corr_edge_and_the_length() -> None:
    s = fits_summary(synthetic_prep())
    assert s is not None
    rows = {r["name"]: r for r in s["frames"][0]["rows"]}
    assert [r["name"] for r in s["frames"][0]["rows"]] == ["ring_top", "exit_sign", "edge_box"]  # the boxes' order
    ring = rows["ring_top"]
    assert ring["box"] == [422, 371, 582, 441] and ring["box_canvas"] == [393, 371, 553, 441]
    assert ring["cells"]["final"] == {"dx": 1.4, "dy": -1.09, "corr": 0.994, "edge": False, "px": 1.77}
    assert ring["cells"]["all"]["px"] == 14.01  # hypot(6.14, 12.59) = 14.0075
    # A window without a fit the frame made has an empty cell, never a zero. Mutation: 0.0 for a missing fit.
    assert rows["exit_sign"]["cells"]["far"] is None and rows["exit_sign"]["cells"]["ecc"] is None
    assert rows["edge_box"]["cells"]["all"]["edge"] is True and rows["edge_box"]["box_canvas"] is None


def test_the_lock_shift_and_the_largest_offset_per_fit() -> None:
    s = fits_summary(synthetic_prep())
    assert s is not None
    f1 = s["frames"][0]
    assert f1["i"] == 1 and f1["method"] == "sift+magsac + lock" and f1["lock_shift"] == [-4.93, 11.48]
    # Per fit, the window whose offset is longest. Under final the edge box's bound (30.07 px) beats the exit sign's
    # 27.30 px and keeps its edge flag. Mutation: leaving edge cells out names the exit sign and turns this red.
    assert f1["largest"]["final"] == {"name": "edge_box", "dx": 30.0, "dy": -2.0, "px": 30.07, "edge": True}
    assert f1["largest"]["far"]["name"] == "ring_top" and f1["largest"]["ecc"]["px"] == 12.37
    assert s["frames"][1]["lock_shift"] is None
    # The cut frame is listed as unmeasured, not dropped silently. Mutation: dropping `unmeasured` turns this red.
    assert s["unmeasured"] == [2]


ANGEL = REPO / "benchmarks" / "runs" / "2026-11-05" / "loopseq" / "windows"


@pytest.mark.integration
@pytest.mark.skipif(not (ANGEL / "angel_lock" / "prep.json").is_file(), reason=f"no research prep under {ANGEL}")
def test_the_real_angel_preps_reproduce_the_sheets_table() -> None:
    # benchmarks/2026-11-04-angel.md, the registration table; research/2026-11-05/loopseq_a2.md §3.
    lock = fits_summary(read_json(ANGEL / "angel_lock" / "prep.json"))
    assert lock is not None and lock["fits"] == ["all", "final"] and len(lock["names"]) == 10
    (f1,) = lock["frames"]
    rows = {r["name"]: r["cells"] for r in f1["rows"]}
    assert (rows["ring_top"]["final"]["dx"], rows["ring_top"]["final"]["dy"]) == (1.4, -1.09)
    assert (rows["ring_top"]["all"]["dx"], rows["ring_top"]["all"]["dy"]) == (6.14, -12.59)
    assert f1["lock_shift"] == [-4.93, 11.48]
    ring = [rows[n]["final"]["px"] for n in ("ring_top", "ring_left", "ring_right")]
    assert max(ring) <= 2.15  # "final holds the three ring windows within 2.14 px"
    assert f1["largest"]["final"]["name"] == "exit_sign"
    assert not any(c["edge"] for r in rows.values() for c in r.values() if c)  # no angel window hit the border
    far = fits_summary(read_json(ANGEL / "angel_far" / "prep.json"))
    assert far is not None and far["fits"] == ["all", "far", "final"]
    cells = {r["name"]: r["cells"] for r in far["frames"][0]["rows"]}
    assert (cells["ring_top"]["far"]["dx"], cells["ring_top"]["far"]["dy"]) == (5.25, -7.32)

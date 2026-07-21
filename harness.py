#!/usr/bin/env python3
"""
Sandbox harness for reveal.py. Mirrors the organizer project's working
method: numbered assertions, synthetic inputs with known ground truth,
monkeypatched optional layers, and a real HTTP round-trip against the
stdlib server. Run: python3 harness.py
"""

import io
import json
import shutil
import socket
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
import uuid
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np
import cv2
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reveal as rv

PASS = 0
FAIL = 0


def check(n, desc, cond):
    global PASS, FAIL
    ok = bool(cond)
    PASS += ok
    FAIL += (not ok)
    print(f"  [{'ok' if ok else 'XX'}] {n:>3} {desc}")
    return ok


rng = np.random.default_rng(11)


def synth(w=1200, h=900, seed=11):
    r = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.uint8)
    gx = np.linspace(40, 200, w, dtype=np.float32)
    img[:] = np.stack([np.tile(gx, (h, 1))] * 3, -1).astype(np.uint8)
    for _ in range(140):
        c = tuple(int(v) for v in r.integers(30, 255, 3))
        cv2.circle(img, (int(r.integers(0, w)), int(r.integers(0, h))),
                   int(r.integers(6, 40)), c, -1)
    for x in range(0, w, 90):
        cv2.line(img, (x, 0), (x, h), (250, 250, 250), 2)
    for y in range(0, h, 70):
        cv2.line(img, (0, y), (w, y), (10, 10, 10), 2)
    n = r.normal(0, 6, img.shape).astype(np.float32)
    return np.clip(img.astype(np.float32) + n, 0, 255).astype(np.uint8)


def true_h(w, h):
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 1.6, 1.04)
    H = np.vstack([M, [0, 0, 1]]).astype(np.float64)
    H[0, 2] += 18
    H[1, 2] -= 11
    H[2, 0] = 4e-6
    H[2, 1] = -3e-6
    return H


def make_pair(w=1200, h=900, expose=True, patch=True):
    """Returns (A, B, H_true, patch_rect). B = A seen through inv(H_true)
    with an exposure change and a changed-content patch."""
    A = synth(w, h)
    H = true_h(w, h)
    B = cv2.warpPerspective(A, np.linalg.inv(H), (w, h),
                            flags=cv2.INTER_LINEAR)
    if expose:
        B = np.clip(B.astype(np.float32) * 1.25 + 12, 0, 255).astype(np.uint8)
    rect = (int(w * 0.35), int(h * 0.30), int(w * 0.65), int(h * 0.70))
    if patch:
        cv2.rectangle(B, rect[:2], rect[2:], (200, 40, 160), -1)
        cv2.putText(B, "AFTER", (rect[0] + 30, (rect[1] + rect[3]) // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 0), 8)
    return A, B, H, rect


def corner_err(Ha, Hb, w, h):
    c = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    return float(np.linalg.norm(
        cv2.perspectiveTransform(c, Ha).reshape(-1, 2)
        - cv2.perspectiveTransform(c, Hb).reshape(-1, 2), axis=1).max())


TMP = Path(tempfile.mkdtemp(prefix="reveal-harness-"))


# ===========================================================================
print("== A. multipart parser ==")
boundary = "----XyZ123"
fbytes = b"\x00\x01\r\n--not-a-boundary\r\n\xff\xfe" * 40
body = (
    f"--{boundary}\r\n"
    'Content-Disposition: form-data; name="before"; filename="a.jpg"\r\n'
    "Content-Type: image/jpeg\r\n\r\n").encode() + fbytes + (
    f"\r\n--{boundary}\r\n"
    'Content-Disposition: form-data; name="after"; filename="b b.png"\r\n'
    "\r\n").encode() + b"PNGDATA" + (
    f"\r\n--{boundary}--\r\n").encode()
f = rv.parse_multipart(body, f'multipart/form-data; boundary={boundary}')
check(1, "two fields parsed", set(f) == {"before", "after"})
check(2, "binary body incl. CRLF preserved byte-exact",
      f["before"]["data"] == fbytes)
check(3, "filename with space parsed, basename only",
      f["after"]["filename"] == "b b.png" and f["after"]["data"] == b"PNGDATA")
try:
    rv.parse_multipart(b"x", "application/json")
    check(4, "missing boundary raises", False)
except ValueError:
    check(4, "missing boundary raises", True)
q = rv.parse_multipart(body, f'multipart/form-data; boundary="{boundary}"')
check(5, "quoted boundary accepted", q["before"]["data"] == fbytes)

# ===========================================================================
print("== B. decode layer ==")
img = Image.new("RGB", (100, 60), (200, 30, 30))
ex = Image.Exif()
ex[274] = 6                                    # orientation: rotate 90 CW
p_jpg = TMP / "orient.jpg"
img.save(p_jpg, exif=ex)
arr = rv.load_image_rgb(p_jpg)
check(6, "EXIF orientation 6 applied (100x60 -> 60x100)",
      arr.shape[0] == 100 and arr.shape[1] == 60)

p_heic = TMP / "t.heic"
Image.fromarray(synth(320, 240, seed=3)).save(p_heic, format="HEIF")
arr = rv.load_image_rgb(p_heic)
check(7, "HEIC decode roundtrip", arr.shape == (240, 320, 3))

_saved = rv.rawpy
rv.rawpy = None
(TMP / "x.arw").write_bytes(b"fake")
try:
    try:
        rv.load_image_rgb(TMP / "x.arw")
        check(8, "RAW without rawpy -> clean AlignError", False)
    except rv.AlignError as e:
        check(8, "RAW without rawpy -> clean AlignError", "rawpy" in str(e))
finally:
    rv.rawpy = _saved


class _FakeRaw:
    def __init__(self, path):
        self.path = path
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def postprocess(self, **kw):
        assert kw.get("use_camera_wb") is True
        return np.full((10, 20, 3), 77, np.uint8)


class _FakeRawpy:
    imread = staticmethod(lambda p: _FakeRaw(p))


rv.rawpy = _FakeRawpy()
try:
    (TMP / "x.dng").write_bytes(b"fake")
    arr = rv.load_image_rgb(TMP / "x.dng")
    check(9, "DNG routed through rawpy.postprocess(use_camera_wb)",
          arr.shape == (10, 20, 3) and arr[0, 0, 0] == 77)
finally:
    rv.rawpy = _saved

try:
    (TMP / "x.xyz").write_bytes(b"?")
    rv.load_image_rgb(TMP / "x.xyz")
    check(10, "unsupported extension -> AlignError", False)
except rv.AlignError:
    check(10, "unsupported extension -> AlignError", True)
try:
    rv.load_image_rgb(TMP / "missing.jpg")
    check(11, "missing file -> AlignError", False)
except rv.AlignError:
    check(11, "missing file -> AlignError", True)

# ===========================================================================
print("== C. geometry recovery (SIFT + MAGSAC + ECC) ==")
A, B, H_true, rect = make_pair()
h, w = A.shape[:2]
est = rv.estimate_alignment(rv.gray_of(A), rv.gray_of(B))
err = corner_err(est["H"], H_true, w, h)
check(12, f"method is sift ({est['method']})", est["method"] == "sift")
check(13, f"corner error vs ground truth < 1.5 px (got {err:.2f})", err < 1.5)
check(14, f"inliers >= 30 (got {est['inliers']})",
      est["inliers"] >= rv.CFG["min_inliers"])
check(15, f"inlier RMSE <= 2 px (got {est['rmse']:.2f})",
      est["rmse"] <= rv.CFG["good_rmse"])
check(16, "ECC refinement converged (rho present)",
      est["ecc_rho"] is not None and est["ecc_rho"] > 0.5)

print("== D. fallbacks and clean failure ==")
pts = rv._detect_and_match(rv.gray_of(A), rv.gray_of(B), "orb", rv.CFG)
est_orb = rv._estimate_h(*pts, rv.CFG) if pts else None
check(17, "ORB path yields a sane homography",
      est_orb is not None and rv._h_sane(est_orb[0], B.shape, A.shape, rv.CFG)
      and corner_err(est_orb[0], H_true, w, h) < 6.0)
X = synth(800, 600, seed=1)
Y = synth(800, 600, seed=99)[::-1, ::-1]       # unrelated content
try:
    rv.estimate_alignment(rv.gray_of(X), rv.gray_of(Y))
    failed_clean = False
except rv.AlignError:
    failed_clean = True
except Exception:
    failed_clean = False
check(18, "unrelated pair fails with AlignError, not a crash", failed_clean)

print("== E. scale transport ==")
Ah = cv2.resize(A, (w // 2, h // 2))
Bh = cv2.resize(B, (w // 2, h // 2))
est2 = rv.estimate_alignment(rv.gray_of(Ah), rv.gray_of(Bh))
Hf = rv.scale_h(est2["H"], 2.0, 2.0)
check(19, f"half-res estimate transports to full res < 3 px "
          f"(got {corner_err(Hf, H_true, w, h):.2f})",
      corner_err(Hf, H_true, w, h) < 3.0)

# ===========================================================================
print("== F. changed region and periphery ==")
warped = cv2.warpPerspective(B, est["H"], (w, h))
valid = rv.warp_valid_mask(B.shape, est["H"], (w, h))
gA, gW = rv.gray_of(A), rv.gray_of(warped)
changed = rv.changed_region_mask(A, warped, valid)
peri = rv.peripheral_mask(valid, changed)
pm = np.zeros((h, w), np.uint8)
cv2.rectangle(pm, rect[:2], rect[2:], 255, -1)
inter = ((changed > 0) & (pm > 0)).sum() / max(1, (pm > 0).sum())
check(20, f"changed mask covers >=60% of the injected patch "
          f"(got {inter:.2f})", inter >= 0.60)
leak = ((peri > 0) & (pm > 0)).sum() / max(1, (pm > 0).sum())
check(21, f"peripheral mask excludes the patch (<5% leak, got {leak:.2f})",
      leak < 0.05)

print("== G. exposure matching ==")
bh0 = rv.bhattacharyya(gA, gW, peri)
stats = rv.exposure_params(A, warped, peri)
matched = rv.apply_exposure(warped, stats, 100)
bh1 = rv.bhattacharyya(gA, rv.gray_of(matched), peri)
gapl0 = abs(float(gA[peri > 0].mean()) - float(gW[peri > 0].mean()))
gapl1 = abs(float(gA[peri > 0].mean())
            - float(rv.gray_of(matched)[peri > 0].mean()))
check(22, f"exposure match: luma gap {gapl0:.1f}->{gapl1:.1f} (>=80% closed),"
          f" Bhattacharyya {bh0:.3f}->{bh1:.3f} (>=30% down)",
      stats is not None and gapl1 < 0.2 * gapl0 and bh1 < bh0 * 0.7)
same = rv.apply_exposure(warped, stats, 0)
check(23, "strength 0 is a no-op", np.array_equal(same, warped))

print("== H. crop rectangle ==")
x, y, cw, ch = rv.crop_rect(valid)
sub = valid[y:y + ch, x:x + cw]
check(24, "crop rect fully inside valid warp", (sub > 0).all())
check(25, "crop keeps >50% of frame for a small warp",
      cw * ch > 0.5 * w * h and cw % 2 == 0 and ch % 2 == 0)

# ===========================================================================
print("== I. job pipeline + manual compose ==")
pa, pb = TMP / "A.png", TMP / "B.png"
Image.fromarray(A).save(pa)
Image.fromarray(B).save(pb)
job = rv.Job(uuid.uuid4().hex[:16], TMP / "wd")
rv.run_alignment(job, pa, pb)
st = job.status()
check(26, "pipeline reaches ready", st["state"] == "ready")
check(27, "primary stop metric passed", st["metrics"]["passed"] is True)
check(28, "exposure auto-enabled on the lit-differently pair",
      st["params"]["exposure"] > 0)
check(29, "confidence is high (>=80)", st["metrics"]["confidence"] >= 80)
M = rv.manual_matrix({"dx": 0.02, "dy": -0.01}, 1000, 800)
pt = M @ np.array([300.0, 500.0, 1.0])
pt /= pt[2]
check(30, "manual translation is exact (+20, -8 px)",
      abs(pt[0] - 320) < 1e-6 and abs(pt[1] - 492) < 1e-6)
M = rv.manual_matrix({"rot": 2.0, "scale": 1.05}, 1000, 800)
ctr = M @ np.array([500.0, 400.0, 1.0])
ctr /= ctr[2]
check(31, "rotation+scale pivot on the image center",
      abs(ctr[0] - 500) < 1e-6 and abs(ctr[1] - 400) < 1e-6)
r0a, r0b = rv._render_pair(job, 1400, rv.default_params())
p2 = rv.default_params()
p2["dx"] = 0.02
r1a, r1b = rv._render_pair(job, 1400, p2)
check(32, "dx render: valid crop moves, images stay paired and change",
      r0a.shape == r0b.shape and r1a.shape == r1b.shape
      and (r0b.shape != r1b.shape or not np.array_equal(r0b, r1b)))

print("== J. residual flow guard ==")
A2, B2, H2, _ = make_pair(patch=False, expose=False)
g2 = rv.gray_of(A2)
w2 = cv2.warpPerspective(B2, rv.estimate_alignment(
    g2, rv.gray_of(B2))["H"], (A2.shape[1], A2.shape[0]))
v2 = rv.warp_valid_mask(B2.shape, H2, (A2.shape[1], A2.shape[0]))
c2 = rv.changed_region_mask(g2, rv.gray_of(w2), v2)
p2m = rv.peripheral_mask(v2, c2)
flow = rv.residual_flow(g2, rv.gray_of(w2), p2m, v2)
check(33, "pure-homography pair: residual is None (noise) or capped",
      flow is None or float(np.linalg.norm(flow, axis=2).max())
      <= rv.CFG["residual_cap"] + 1e-3)

# ===========================================================================
print("== K. headless CLI ==")
outdir = TMP / "cli"
rc = rv.main(["align", str(pa), str(pb), "--out", str(outdir),
              "--video", "--aspect", "1:1", "--seconds", "3.0"])
check(34, "align exits 0", rc == 0)
check(35, "stills + metrics.json written",
      (outdir / "before.jpg").exists()
      and (outdir / "after_aligned.jpg").exists()
      and (outdir / "metrics.json").exists())

print("== L. video export ==")
vp = outdir / "transition.mp4"
cap = cv2.VideoCapture(str(vp))
fps = cap.get(cv2.CAP_PROP_FPS)
nf = cap.get(cv2.CAP_PROP_FRAME_COUNT)
vw = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
vh = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
ok0, first = cap.read()
cap.release()
check(36, f"mp4 opens, 1080x1080 @30fps (got {vw:.0f}x{vh:.0f}@{fps:.0f})",
      ok0 and vw == 1080 and vh == 1080 and abs(fps - 30) < 0.5)
dur = nf / max(fps, 1)
check(37, f"duration ~3.0 s (got {dur:.2f})", abs(dur - 3.0) < 0.35)

# ===========================================================================
print("== M. HTTP end-to-end ==")
rv.WORKDIR = TMP / "srv"
httpd = ThreadingHTTPServer(("127.0.0.1", 0), rv.Handler)
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{port}"
check(38, "server bound to 127.0.0.1 only",
      httpd.server_address[0] == "127.0.0.1")


def req(method, path, data=None, headers=None):
    r = urllib.request.Request(base + path, data=data, method=method,
                               headers=headers or {})
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


st_, body_, _ = req("GET", "/")
check(39, "GET / serves the page", st_ == 200 and b"Reveal" in body_
      and rv.VERSION.encode() in body_)

bnd = "----harness"
jb = io.BytesIO()
for name, path in (("before", pa), ("after", pb)):
    jb.write(f"--{bnd}\r\nContent-Disposition: form-data; "
             f'name="{name}"; filename="{path.name}"\r\n\r\n'.encode())
    jb.write(path.read_bytes())
    jb.write(b"\r\n")
jb.write(f"--{bnd}--\r\n".encode())
st_, body_, _ = req("POST", "/api/job", jb.getvalue(),
                    {"Content-Type": f"multipart/form-data; boundary={bnd}"})
jid = json.loads(body_)["id"]
check(40, "upload accepted", st_ == 200 and jid)

deadline = time.time() + 120
state = None
while time.time() < deadline:
    st_, body_, _ = req("GET", f"/api/job/{jid}/status")
    state = json.loads(body_)["state"]
    if state in ("ready", "failed"):
        break
    time.sleep(0.4)
check(41, f"job reaches ready over HTTP (got {state})", state == "ready")

st_, img_b, _ = req("GET", f"/api/job/{jid}/img/before")
st2_, img_a, _ = req("GET", f"/api/job/{jid}/img/after")
check(42, "both previews are JPEGs",
      img_b[:2] == b"\xff\xd8" and img_a[:2] == b"\xff\xd8")

st_, body_, _ = req("POST", f"/api/job/{jid}/tune",
                    json.dumps({"dx": 0.02, "exposure": 40}).encode())
tuned = json.loads(body_)
check(43, "tune clamps and echoes params", st_ == 200
      and abs(tuned["params"]["dx"] - 0.02) < 1e-9
      and tuned["params"]["exposure"] == 40)
st_, img_a2, _ = req("GET", f"/api/job/{jid}/img/after")
check(44, "tuned preview differs", img_a2 != img_a)
st_, body_, _ = req("POST", f"/api/job/{jid}/tune",
                    json.dumps({"dx": 9.9, "rot": -99}).encode())
tuned = json.loads(body_)
check(45, "out-of-range params clamped to limits",
      tuned["params"]["dx"] == rv.CFG["tune_shift"]
      and tuned["params"]["rot"] == -rv.CFG["tune_rot"])

st_, _, _ = req("POST", f"/api/job/{jid}/export",
                json.dumps({"video": False}).encode())
deadline = time.time() + 120
while time.time() < deadline:
    st_, body_, _ = req("GET", f"/api/job/{jid}/status")
    j = json.loads(body_)
    if j["state"] == "ready" and "after_aligned" in j["exports"]:
        break
    time.sleep(0.4)
check(46, "photo export completes", "after_aligned" in j["exports"])
st_, dl, hh = req("GET", f"/api/job/{jid}/download/after_aligned")
check(47, "download works with attachment header",
      st_ == 200 and dl[:2] == b"\xff\xd8"
      and "attachment" in hh.get("Content-Disposition", ""))

st_, _, _ = req("GET", "/api/job/deadbeefdeadbeef/status")
check(48, "unknown job -> 404", st_ == 404)
st_, _, _ = req("GET", f"/api/job/{jid}/download/../../etc/passwd")
check(49, "traversal-shaped download -> 404", st_ == 404)
st_, _, _ = req("GET", "/api/job/" + "%2e%2e%2f" * 3 + "/status")
check(50, "encoded traversal job id -> 404", st_ == 404)

bad = io.BytesIO()
bad.write(f"--{bnd}\r\nContent-Disposition: form-data; "
          f'name="before"; filename="x.exe"\r\n\r\nMZ\r\n'.encode())
bad.write(f"--{bnd}\r\nContent-Disposition: form-data; "
          f'name="after"; filename="y.jpg"\r\n\r\nJJ\r\n'.encode())
bad.write(f"--{bnd}--\r\n".encode())
st_, body_, _ = req("POST", "/api/job", bad.getvalue(),
                    {"Content-Type": f"multipart/form-data; boundary={bnd}"})
check(51, "unsupported upload type -> 400", st_ == 400)

httpd.shutdown()

# ===========================================================================
print("== N. matching modes (loose) ==")
lp = rv.profile("loose")
rp = rv.profile("reshot")
check(52, "profiles: loose overrides, reshot untouched, unknown -> reshot",
      lp["min_inliers"] == 12 and lp["similarity_fallback"] is True
      and rp["min_inliers"] == rv.CFG["min_inliers"]
      and rv.profile("nonsense")["mode"] == "reshot")
cl = rv._clamp_params({"dx": 0.12, "rot": 10, "scale": 1.2}, lp)
cs = rv._clamp_params({"dx": 0.12, "rot": 10, "scale": 1.2}, rp)
check(53, "clamps are mode-aware (loose keeps 0.12/10deg, strict cuts)",
      abs(cl["dx"] - 0.12) < 1e-9 and cl["rot"] == 10 and cl["scale"] == 1.2
      and cs["dx"] == rp["tune_shift"] and cs["rot"] == rp["tune_rot"]
      and abs(cs["scale"] - (1 + rp["tune_scale"])) < 1e-9)

r2 = np.random.default_rng(4)
n = 120
ptsB_s = r2.uniform(50, 900, (n, 2)).astype(np.float32)
th, sc, tx, ty = np.radians(8.0), 0.7, 40.0, -25.0
R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]) * sc
ptsA_s = (ptsB_s @ R.T + [tx, ty]).astype(np.float32)
ptsA_s += r2.normal(0, 0.6, ptsA_s.shape).astype(np.float32)
out_idx = r2.choice(n, 36, replace=False)          # 30% outliers
ptsA_s[out_idx] = r2.uniform(0, 900, (36, 2)).astype(np.float32)
sim = rv._estimate_similarity(ptsA_s, ptsB_s, lp)
H_sim_true = np.array([[R[0, 0], R[0, 1], tx], [R[1, 0], R[1, 1], ty],
                       [0, 0, 1.0]])
check(54, "similarity estimator survives 30% outliers (<2 px corner err)",
      sim is not None
      and corner_err(sim[0], H_sim_true, 900, 900) < 2.0
      and sim[1] >= 60)

H_aff, rho_aff = rv._ecc_refine(rv.gray_of(A), rv.gray_of(B), est["H"],
                                lp, motion="affine")
check(55, "affine ECC path runs and returns a sane transform",
      rv._h_sane(H_aff, B.shape, A.shape, lp))


def scene_(seed, w=1100, h=850):
    r = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = r.integers(40, 90, 3)
    for _ in range(120):
        c = tuple(int(v) for v in r.integers(20, 200, 3))
        cv2.circle(img, (int(r.integers(0, w)), int(r.integers(0, h))),
                   int(r.integers(4, 30)), c, -1)
    return img


def draw_obj(img, cx, cy, s, ang, variant=0):
    ov = np.zeros((400, 400, 3), np.uint8)
    pal = [((120, 160, 200), (240, 210, 90), (180, 60, 90), "No.7"),
           ((150, 120, 190), (90, 210, 180), (200, 120, 60), "No.9")][variant]
    j = 12 * variant
    cv2.rectangle(ov, (60, 40 + j), (340, 360), pal[0], -1)
    cv2.circle(ov, (200 + j, 130), 70 - j // 2, pal[1], -1)
    cv2.circle(ov, (200 + j, 130), 32, pal[2], -1)
    cv2.rectangle(ov, (110, 230 + j), (290, 330), (250, 245, 235), -1)
    cv2.putText(ov, pal[3], (130, 300 + j),
                cv2.FONT_HERSHEY_SIMPLEX, 1.6, (30, 30, 30), 5)
    cv2.rectangle(ov, (60, 40 + j), (340, 360), (25, 25, 25), 6)
    M = cv2.getRotationMatrix2D((200, 200), ang, s)
    M[0, 2] += cx - 200
    M[1, 2] += cy - 200
    warped = cv2.warpAffine(ov, M, (img.shape[1], img.shape[0]))
    msk = warped.sum(axis=2) > 0
    img[msk] = warped[msk]
    return img


SA = draw_obj(scene_(1), 520, 430, 1.0, 0)
SB = draw_obj(scene_(2), 610, 380, 0.62, 9)
try:
    rv.estimate_alignment(rv.gray_of(SA), rv.gray_of(SB), rp)
    strict_refused = False
except rv.AlignError:
    strict_refused = True
est_l = rv.estimate_alignment(rv.gray_of(SA), rv.gray_of(SB), lp)
check(56, "big-scale look-alike: strict refuses, loose aligns "
          f"({est_l['method']}, {est_l['inliers']} inl, "
          f"{est_l['rmse']:.2f} px)",
      strict_refused and est_l["inliers"] >= lp["min_inliers"]
      and est_l["rmse"] <= lp["good_rmse"])

PA = draw_obj(scene_(1), 520, 430, 1.0, 0, variant=0)
PB = draw_obj(scene_(2), 600, 400, 0.85, 7, variant=1)
try:
    est_s2 = rv.estimate_alignment(rv.gray_of(PA), rv.gray_of(PB), rp)
    # CLASSICAL matching must not align a similar-but-different pair under
    # strict gates. The learned matcher legitimately may: if it clears the
    # strict sanity gates, inlier floor and RMSE bar, refusing would be
    # pedantic. So the contract is "classical must refuse", not "strict
    # must fail" (which merely encoded SIFT's limits).
    strict_classical_refused = est_s2["method"].startswith("learned")
    strict_note = f"strict aligned via {est_s2['method']}"
except rv.AlignError:
    strict_classical_refused = True
    strict_note = "strict refused"
est_p = rv.estimate_alignment(rv.gray_of(PA), rv.gray_of(PB), lp)
check(57, f"similar-but-different object: loose aligns it "
          f"({est_p['method']}, {est_p['inliers']} inl); {strict_note}",
      strict_classical_refused and est_p["inliers"] >= lp["min_inliers"])

QA = draw_obj(scene_(5), 520, 430, 1.0, 0, variant=0)
QB = draw_obj(scene_(5), 540, 425, 1.0, 2, variant=1)
est_q = rv.estimate_alignment(rv.gray_of(QA), rv.gray_of(QB), rp)
check(58, "same scene, swapped subject still passes in strict mode",
      est_q["inliers"] >= rp["min_inliers"]
      and est_q["rmse"] <= rp["good_rmse"])

pl_a, pl_b = TMP / "LA.png", TMP / "LB.png"
Image.fromarray(SA).save(pl_a)
Image.fromarray(SB).save(pl_b)
ljob = rv.Job(uuid.uuid4().hex[:16], TMP / "wd2", mode="loose")
rv.run_alignment(ljob, pl_a, pl_b)
lst = ljob.status()
check(59, "loose job: ready, mode+limits in status, residual forced off",
      lst["state"] == "ready" and lst["mode"] == "loose"
      and lst["limits"]["shift"] == lp["tune_shift"]
      and ljob.flow_work is None)

# HTTP: mode field round-trip and mode-aware clamping
bnd2 = "----modeharness"
mb = io.BytesIO()
for name, path in (("before", pl_a), ("after", pl_b)):
    mb.write(f"--{bnd2}\r\nContent-Disposition: form-data; "
             f'name="{name}"; filename="{path.name}"\r\n\r\n'.encode())
    mb.write(path.read_bytes())
    mb.write(b"\r\n")
mb.write(f"--{bnd2}\r\nContent-Disposition: form-data; "
         f'name="mode"\r\n\r\nloose\r\n'.encode())
mb.write(f"--{bnd2}--\r\n".encode())
httpd2 = ThreadingHTTPServer(("127.0.0.1", 0), rv.Handler)
port2 = httpd2.server_address[1]
threading.Thread(target=httpd2.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{port2}"
st_, body_, _ = req("POST", "/api/job", mb.getvalue(),
                    {"Content-Type":
                     f"multipart/form-data; boundary={bnd2}"})
jid2 = json.loads(body_)["id"]
deadline = time.time() + 120
while time.time() < deadline:
    st_, body_, _ = req("GET", f"/api/job/{jid2}/status")
    j2 = json.loads(body_)
    if j2["state"] in ("ready", "failed"):
        break
    time.sleep(0.4)
check(60, "HTTP loose upload: ready, mode echoed, wide limits",
      j2["state"] == "ready" and j2["mode"] == "loose"
      and j2["limits"]["shift"] == lp["tune_shift"])
st_, body_, _ = req("POST", f"/api/job/{jid2}/tune",
                    json.dumps({"dx": 0.12, "rot": 10}).encode())
t2 = json.loads(body_)
check(61, "HTTP tune honors loose ranges (dx 0.12 kept)",
      st_ == 200 and abs(t2["params"]["dx"] - 0.12) < 1e-9
      and t2["params"]["rot"] == 10)
mb2 = io.BytesIO()
for name, path in (("before", pa), ("after", pb)):
    mb2.write(f"--{bnd2}\r\nContent-Disposition: form-data; "
              f'name="{name}"; filename="{path.name}"\r\n\r\n'.encode())
    mb2.write(path.read_bytes())
    mb2.write(b"\r\n")
mb2.write(f"--{bnd2}\r\nContent-Disposition: form-data; "
          f'name="mode"\r\n\r\nEVIL\r\n'.encode())
mb2.write(f"--{bnd2}--\r\n".encode())
st_, body_, _ = req("POST", "/api/job", mb2.getvalue(),
                    {"Content-Type":
                     f"multipart/form-data; boundary={bnd2}"})
jid3 = json.loads(body_)["id"]
st_, body_, _ = req("GET", f"/api/job/{jid3}/status")
check(62, "unknown mode value falls back to reshot",
      json.loads(body_)["mode"] == "reshot")
httpd2.shutdown()

# ===========================================================================
print("== O. rigid-subject residual flow (field defect: wavy box edges) ==")
hole = np.zeros((200, 200), np.uint8)
cv2.rectangle(hole, (40, 40), (160, 160), 255, 12)      # ring with hole
filled = rv._fill_holes(hole)
check(63, "changed-mask hole filling closes enclosed interiors",
      filled[100, 100] == 255 and filled[10, 10] == 0)

RW, RH = 1100, 800
RX0, RY0, RX1, RY1 = 440, 200, 680, 650
RM = 26


def _rwall(seed):
    r = np.random.default_rng(seed)
    img = np.full((RH, RW, 3), 205, np.uint8)
    img = np.clip(img.astype(np.float32)
                  + r.normal(0, 5, (RH, RW, 1)), 0, 255).astype(np.uint8)
    for y in (110, 150, 690):
        cv2.line(img, (0, y), (RW, y), (150, 148, 145), 5)
    for gx in range(50, 360, 48):
        cv2.rectangle(img, (gx, 30), (gx + 28, 90), (40, 40, 42), 3)
        cv2.rectangle(img, (gx + 700, 30), (gx + 728, 90), (40, 40, 42), 3)
    for px in range(0, RW, 60):
        cv2.line(img, (px, 715), (px - 30, RH), (120, 118, 115), 3)
    return img


def _rbox(img, seed, offset, base, border):
    r = np.random.default_rng(seed)
    cv2.rectangle(img, (RX0, RY0), (RX1, RY1), base, -1)
    for _ in range(22):
        pts = np.stack([r.uniform(RX0 + RM + 8, RX1 - RM - 8, 6),
                        r.uniform(RY0 + RM + 8, RY1 - RM - 8, 6)], 1)
        pts[:, 0] += offset
        col = tuple(int(v) for v in r.integers(20, 120, 3))
        cv2.polylines(img, [np.clip(pts, (RX0 + RM, RY0 + RM),
                                    (RX1 - RM, RY1 - RM)).astype(np.int32)],
                      False, col, int(r.integers(4, 9)), cv2.LINE_AA)
    cv2.rectangle(img, (RX0, RY0), (RX1, RY1), border, 6)
    return img


def _rpair(repaint):
    A_ = _rbox(_rwall(1), 10, 0, (186, 184, 180), (30, 30, 30))
    if repaint:
        AF = _rbox(_rwall(1), 77, 5, (172, 182, 168), (55, 40, 35))
    else:
        AF = _rbox(_rwall(1), 77, 5, (186, 184, 180), (30, 30, 30))
    Ht = np.vstack([cv2.getRotationMatrix2D((RW / 2, RH / 2), 0.7, 1.02),
                    [0, 0, 1]])
    Ht[0, 2] += 8
    Ht[1, 2] -= 5
    B_ = cv2.warpPerspective(AF, np.linalg.inv(Ht), (RW, RH),
                             borderMode=cv2.BORDER_REPLICATE)
    yy, xx = np.mgrid[0:RH, 0:RW].astype(np.float32)
    f = 1 + 2.5e-8 * ((xx - RW / 2) ** 2 + (yy - RH / 2) ** 2)
    B_ = cv2.remap(B_, RW / 2 + (xx - RW / 2) * f, RH / 2 + (yy - RH / 2) * f,
                   cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return A_, np.clip(B_.astype(np.float32) * 1.1 + 5, 0, 255).astype(np.uint8)


def _edge_wobble(img, x0, y_lo, y_hi):
    """High-frequency bending of a vertical edge: residual from a fitted
    quadratic (a smooth lens-arc lives in the quadratic; wobble does not),
    tracking the SIGNED wall->dark transition so the detector cannot flip
    between the border's two sides (a bistability that faked 8.5 px of
    wobble during v1.3.0 development)."""
    g = rv.gray_of(img).astype(np.float32)
    xs, ys = [], []
    for y in range(y_lo, y_hi, 6):
        w_ = g[y, x0 - 10:x0 + 10]
        d = np.diff(w_)
        x = int(np.argmin(d))                    # strongest darkening
        if -d[x] > 20 and 0 < x < len(d) - 1:
            sub = (d[x - 1] - d[x + 1]) / (2 * (d[x - 1] - 2 * d[x]
                                                + d[x + 1]) + 1e-9)
            xs.append(x0 - 10 + x + 0.5 + np.clip(sub, -0.5, 0.5))
            ys.append(y)
    xs, ys = np.array(xs), np.array(ys, float)
    Q = np.vstack([ys ** 2, ys, np.ones_like(ys)]).T
    c, *_ = np.linalg.lstsq(Q, xs, rcond=None)
    return float(np.abs(xs - Q @ c).max())


def _residual_case(repaint):
    A_, B_ = _rpair(repaint)
    gA_ = rv.gray_of(A_)
    pr = rv.profile("reshot")
    est_ = rv.estimate_alignment(gA_, rv.gray_of(B_), pr, A_, B_)
    Hw = est_["H"]
    warped_ = cv2.warpPerspective(B_, Hw, (RW, RH))
    valid_ = rv.warp_valid_mask(B_.shape, Hw, (RW, RH))
    changed_ = rv.changed_region_mask(A_, warped_, valid_)
    peri_ = rv.peripheral_mask(valid_, changed_)
    flow_ = rv.residual_flow(gA_, rv.gray_of(warped_), peri_, valid_,
                             changed_)
    out_ = rv.apply_residual(warped_, flow_, 1.0) \
        if flow_ is not None else warped_
    w0 = _edge_wobble(warped_, RX0, RY0 + 40, RY1 - 40)
    w1 = _edge_wobble(out_, RX0, RY0 + 40, RY1 - 40)
    return w0, w1, flow_, est_, (gA_, warped_)


w0r, w1r, flow_r, est_rep, _ = _residual_case(repaint=True)
check(64, f"full repaint: fitted field never adds subject-edge wobble "
          f"({w0r:.2f} -> {w1r:.2f} px)",
      w1r <= max(w0r, 0.6) + 0.05)
w0s, w1s, flow_s, est_str, probeimgs = _residual_case(repaint=False)
check(65, f"sparse-change subject: no added wobble "
          f"({w0s:.2f} -> {w1s:.2f} px)",
      w1s <= max(w0s, 0.6) + 0.05)
check(66, "masked ECC converges on the repaint pair (rho present, high)",
      est_rep["ecc_rho"] is not None and est_rep["ecc_rho"] > 0.6)

# unmasked path (no color args) unchanged and still accurate: reuse pair C
est_nc = rv.estimate_alignment(rv.gray_of(A), rv.gray_of(B))
check(67, "estimate without color args still works (back-compat path)",
      est_nc["inliers"] >= rv.CFG["min_inliers"]
      and corner_err(est_nc["H"], H_true, w, h) < 1.5)

# ground truth agreement: on the sparse-change pair the true residual at
# probe points (template match) must be matched by the fitted field, so
# the enhancement cannot silently die and stay green
gA_, warped_ = probeimgs
agree = True
n_prb = 0
if flow_s is not None:
    for (px_, py_) in ((112, 60), (812, 60), (300, 760), (764, 60)):
        pa = gA_[py_ - 9:py_ + 10, px_ - 20:px_ + 20].astype(np.float32)
        strip = rv.gray_of(warped_)[py_ - 9:py_ + 10,
                                    px_ - 30:px_ + 30].astype(np.float32)
        if pa.std() < 6:
            continue
        r_ = cv2.matchTemplate(strip, pa, cv2.TM_CCOEFF_NORMED)
        _, mx, _, ml = cv2.minMaxLoc(r_)
        if mx < 0.5:
            continue
        n_prb += 1
        agree &= abs((ml[0] - 10) - flow_s[py_, px_, 0]) <= 1.0
check(68, f"fitted field matches template-matched true residual at "
          f"{n_prb} probes (<=1 px)", flow_s is not None and n_prb >= 2
      and agree)

# a wild residual must be rejected whole, never clipped into gradients
yy_, xx_ = np.mgrid[0:RH, 0:RW].astype(np.float32)
f_ = 1 + 2.5e-7 * ((xx_ - RW / 2) ** 2 + (yy_ - RH / 2) ** 2)
A9, _B9 = _rpair(repaint=False)
B9 = cv2.remap(A9, RW / 2 + (xx_ - RW / 2) * f_,
               RH / 2 + (yy_ - RH / 2) * f_, cv2.INTER_LINEAR,
               borderMode=cv2.BORDER_REPLICATE)
g9 = rv.gray_of(A9)
v9 = np.full((RH, RW), 255, np.uint8)
c9 = np.zeros((RH, RW), np.uint8)
p9 = rv.peripheral_mask(v9, c9)
fl9 = rv.residual_flow(g9, rv.gray_of(B9), p9, v9, c9)
check(69, "over-cap residual rejected whole (None), not clipped",
      fl9 is None)

# ===========================================================================
print("== P. scene-independent confidence (v1.3.1) ==")
check(70, "confidence is monotone in reprojection error",
      rv.confidence_score(200, 0.5) > rv.confidence_score(200, 1.5)
      > rv.confidence_score(200, 3.0) > rv.confidence_score(200, 4.5))
check(71, "an excellent real-world alignment scores >= 90 "
          f"(458 inliers, 0.74 px -> {rv.confidence_score(458, 0.74)})",
      rv.confidence_score(458, 0.74) >= 90)
check(72, "failing the local-maximum test is penalized",
      rv.confidence_score(458, 0.74, local_max=False)
      == int(round(rv.confidence_score(458, 0.74)
                   * rv.CFG["not_max_penalty"])))
check(73, "score no longer depends on raw SSIM (scene-dependent ceiling)",
      "peri_ssim" not in rv.confidence_score.__code__.co_varnames)

# peak sharpness: sensitive to real misalignment, and honest about it
gAe = rv.gray_of(A)
gBe = rv.gray_of(B)
sizeE = (gAe.shape[1], gAe.shape[0])
He = est["H"]
we = cv2.warpPerspective(B, He, sizeE)
ve = rv.warp_valid_mask(B.shape, He, sizeE)
pee = rv.peripheral_mask(ve, rv.changed_region_mask(A, we, ve))
sh_true = rv.peak_sharpness(gAe, gBe, He, pee, sizeE)
Toff = np.array([[1, 0, 7.0], [0, 1, 3.0], [0, 0, 1]], float)
sh_off = rv.peak_sharpness(gAe, gBe, Toff @ He, pee, sizeE)
check(74, "found alignment IS a local max of peripheral similarity; a "
          "7 px offset is NOT",
      sh_true is not None and sh_true[2] is True
      and sh_off is not None and sh_off[2] is False)
check(75, "peak_sharpness declines when the periphery is too small",
      rv.peak_sharpness(gAe, gBe, He, np.zeros_like(pee), sizeE) is None)
check(76, "metrics carry sharpness + local_max as diagnostics",
      "sharpness" in st["metrics"] and "local_max" in st["metrics"]
      and st["metrics"]["local_max"] is True)

# ===========================================================================
print("== Q. learned matcher (DISK + LightGlue, optional) ==")
if not rv.learned_available():
    print("  [--]  77-79 skipped: torch + kornia not installed (optional)")
else:
    # the ONLY justification for the dependency: rescue what SIFT cannot do
    HH, WW = 900, 1200

    def _tiles(bright, seed):
        img = np.full((HH, WW, 3), 180, np.uint8)
        for yy in range(0, HH, 60):
            for xx in range(0, WW, 60):
                cv2.rectangle(img, (xx + 2, yy + 2), (xx + 56, yy + 56),
                              (168, 166, 164), -1)
        rr = np.random.default_rng(seed)
        img = np.clip(img.astype(np.float32)
                      + rr.normal(0, 2, (HH, WW, 1)), 0, 255).astype(np.uint8)
        return np.clip(img.astype(np.float32) * bright, 0,
                       255).astype(np.uint8)

    Ah = _tiles(1.0, 1)
    Hh = np.vstack([cv2.getRotationMatrix2D((WW / 2, HH / 2), 1.5, 1.03),
                    [0, 0, 1]])
    Hh[0, 2] += 14
    Bh = cv2.warpPerspective(_tiles(0.55, 1), np.linalg.inv(Hh), (WW, HH),
                             borderMode=cv2.BORDER_REPLICATE)
    gAh, gBh = rv.gray_of(Ah), rv.gray_of(Bh)
    ph = rv.profile("reshot")
    sift_h = rv._detect_and_match(gAh, gBh, "sift", ph)
    est_sift = rv._estimate_h(*sift_h, ph) if sift_h else None
    sift_ok = bool(est_sift
                   and rv._h_sane(est_sift[0], Bh.shape, Ah.shape, ph)
                   and est_sift[1] >= ph["min_inliers"])
    pts_l = rv._match_learned(gAh, gBh, ph)
    est_l = rv._estimate_h(*pts_l, ph) if pts_l else None
    ch = np.float32([[0, 0], [WW, 0], [WW, HH], [0, HH]]).reshape(-1, 1, 2)
    err_l = (float(np.linalg.norm(
        cv2.perspectiveTransform(ch, est_l[0]).reshape(-1, 2)
        - cv2.perspectiveTransform(ch, Hh).reshape(-1, 2), axis=1).max())
        if est_l else 1e9)
    check(77, f"low-texture repetitive pair: SIFT fails, learned rescues it "
              f"({0 if not est_l else est_l[1]} inliers, {err_l:.1f} px "
              f"corner error)",
          (not sift_ok) and est_l is not None and err_l < 3.0)

    # inlier count is NOT comparable across matchers: arbitration must
    # pick on peripheral SSIM, not on the bigger number
    good = rv.estimate_alignment(rv.gray_of(A), rv.gray_of(B),
                                 rv.profile("reshot"), A, B)["H"]
    bad = np.array([[1, 0, 9.0], [0, 1, 4.0], [0, 0, 1]], float) @ good
    cands = [("learned", bad, 9999, 0.1), ("sift", good, 10, 0.9)]
    won = rv._arbitrate(cands, rv.gray_of(A), rv.gray_of(B), A, B, good)
    check(78, "arbitration prefers the visually better candidate even when "
              "the other reports 1000x the inliers",
          won is not None and won[0] == "sift")
    check(79, "learned weights are cached and checksum-intact",
          rv.learned_weights_cached(deep=True))

    man = rv.learned_manifest()
    inside = str(rv._ckpt_dir()).startswith(str(rv.MODELS_DIR))
    check(80, f"model files live INSIDE the project ({len(man['files'])} "
              f"files, {sum(f['size'] for f in man['files'])/1e6:.0f} MB), "
              f"not in a global ~/.cache",
          inside and rv.MODELS_DIR.exists()
          and all((rv._ckpt_dir() / f["name"]).exists()
                  for f in man["files"])
          and man.get("verified") is True
          and man.get("self_test_matches", 0) > 10)

    # THE offline proof: kill every socket, reload the models from disk,
    # and run a real match. Catches any lazily-downloaded file that only
    # a forward pass would request.
    class _DeadSocket:
        def __init__(self, *a, **k):
            raise OSError("network blocked by harness")

    _rs, _rc = socket.socket, socket.create_connection
    socket.socket = _DeadSocket
    socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(
        OSError("network blocked by harness"))
    try:
        rv._LEARNED = None                     # force a cold load from disk
        gs, gs2 = rv._selftest_pair()
        off = rv._match_learned(gs, gs2, rv.profile("reshot"))
    finally:
        socket.socket, socket.create_connection = _rs, _rc
        rv._LEARNED = None
    check(81, f"runs with ALL sockets blocked: cold-loads from ./models and "
              f"matches {0 if off is None else len(off[0])} points",
          off is not None and len(off[0]) > 100)

    # and it must never silently reach for the network during a job
    _bak = rv.LEARNED_MANIFEST.read_text()
    rv.LEARNED_MANIFEST.unlink()
    rv._LEARNED = None
    try:
        rv._learned_models()
        _guarded = False
    except rv.AlignError:
        _guarded = True
    except Exception:
        _guarded = False
    finally:
        rv.LEARNED_MANIFEST.write_text(_bak)
        rv._LEARNED = None
    check(82, "with model files missing it REFUSES to download mid-job and "
              "says to run setup", _guarded)

# ===========================================================================
print(f"\n{PASS} passed, {FAIL} failed")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)

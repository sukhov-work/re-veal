"""TR5 research probe: RoMa outdoor (romatch) on the CPU over prepared pair dirs.

Not part of either tool. Runs in a SCRATCH venv (`python -m venv v && v/bin/pip install romatch`),
never in `.venv`; weights download into TORCH_HOME (set below to a folder next to this script's
working directory, override with the env var) on first use — 1,217,586,395 + 445,647,516 bytes.
Each pair dir needs A.png, B.png (the transitions canvas, from scripts/research/compare_fields.py
--prepare) and dis_dAB.npy / dis_wA.npy. Writes roma_dAB/dBA/wA/wB.npy per dir (canvas px on the
source grid, the transitions convention) and prints one JSON line per pair. 2026-09-14."""
import os, sys, time, json
os.environ.setdefault("TORCH_HOME", os.path.join(os.getcwd(), "roma_torch_home"))
import numpy as np, cv2, torch
from PIL import Image
torch.set_num_threads(os.cpu_count())
from romatch import roma_outdoor
t0 = time.time()
model = roma_outdoor(device="cpu"); model.eval()
print(json.dumps({"load_s": round(time.time() - t0, 1), "threads": torch.get_num_threads()}), flush=True)

def to_disp(half, H, W):
    """half: (hs, ws, 4) normalized (src xy, dst xy) -> displacement on the src grid in canvas px."""
    src = np.stack([(half[..., 0] + 1) * W / 2, (half[..., 1] + 1) * H / 2], -1)
    dst = np.stack([(half[..., 2] + 1) * W / 2, (half[..., 3] + 1) * H / 2], -1)
    d = (dst - src).astype(np.float32)
    return cv2.resize(d, (W, H), interpolation=cv2.INTER_LINEAR)

for d in sys.argv[1:]:
    pa, pb = os.path.join(d, "A.png"), os.path.join(d, "B.png")
    W, H = Image.open(pa).size
    t = time.time()
    with torch.no_grad():
        warp, cert = model.match(pa, pb, device="cpu")
    match_s = round(time.time() - t, 2)
    if warp.dim() == 4:
        warp, cert = warp[0], cert[0]
    warp, cert = warp.cpu().numpy(), cert.cpu().numpy().astype(np.float32)
    ws = warp.shape[1] // 2
    dAB = to_disp(warp[:, :ws], H, W)                      # A grid -> B
    right = warp[:, ws:]                                   # (B_to_A xy, B grid xy)
    dBA = to_disp(np.concatenate([right[..., 2:], right[..., :2]], -1), H, W)   # B grid -> A
    wA = cv2.resize(cert[:, :ws], (W, H), interpolation=cv2.INTER_LINEAR)
    wB = cv2.resize(cert[:, ws:], (W, H), interpolation=cv2.INTER_LINEAR)
    for k, v in (("dAB", dAB), ("dBA", dBA), ("wA", wA), ("wB", wB)):
        np.save(os.path.join(d, f"roma_{k}.npy"), v)
    dis = np.load(os.path.join(d, "dis_dAB.npy")); wdis = np.load(os.path.join(d, "dis_wA.npy"))
    diff = np.linalg.norm(dAB - dis, axis=2)
    both = (wA > 0.5) & (wdis > 0.5)
    # forward-backward consistency of RoMa's own two halves, as transitions computes it
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    back = cv2.remap(dBA, gx + dAB[..., 0], gy + dAB[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    fb = np.linalg.norm(dAB + back, axis=2)
    out = {"pair": os.path.basename(d), "canvas": [W, H], "match_s": match_s,
           "roma_cert_mean": round(float(wA.mean()), 3), "roma_cert_gt_0.5": round(float((wA > 0.5).mean()), 3),
           "dis_cert_mean": round(float(wdis.mean()), 3),
           "roma_median_disp_px": round(float(np.median(np.linalg.norm(dAB, axis=2))), 2),
           "dis_median_disp_px": round(float(np.median(np.linalg.norm(dis, axis=2))), 2),
           "median_diff_px_all": round(float(np.median(diff)), 2),
           "median_diff_px_both_confident": round(float(np.median(diff[both])), 2) if both.any() else None,
           "frac_both_confident": round(float(both.mean()), 3),
           "frac_diff_gt_5px": round(float((diff > 5).mean()), 3),
           "roma_fb_err_median_px": round(float(np.median(fb)), 2)}
    with open(os.path.join(d, "roma.json"), "w") as fh:
        json.dump(out, fh)
    print(json.dumps(out), flush=True)

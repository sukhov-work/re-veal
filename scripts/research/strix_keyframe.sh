#!/usr/bin/env bash
# One-shot keyframe on the Strix Halo box (plan §Rank 2026-09-26 item 4; research track F, 2026-09-26).
# NOT RUN YET (2026-09-26: the box was unreachable from the Mac). Read benchmarks/runs/2026-09-26/research/track_F.md first.
#
# Shape: stable-diffusion.cpp's Vulkan container (no ROCm, no /dev/kfd, host drivers untouched),
# pinned by digest, run as the unprivileged user with /dev/dri only, no network, read-only root,
# a CPU-side memory cap, a pid cap, an OOM score that makes THIS job die first, a wall-clock
# timeout, and a systemd sleep inhibitor so the box's idle auto-suspend waits for the job.
# The cgroup cap does NOT cover GPU (GTT) pages on this APU (ROCm/legacy-rocm-build#6370), so the
# pre-flight below refuses to start unless enough memory is free beside the resident LLMs, and
# the model choice keeps the whole job under ~24 GB (Qwen-Image-Edit-2511 Q4_K_M 13.2 GB +
# Qwen2.5-VL-7B Q4_K_M 4.7 GB + mmproj 0.85 GB + VAE 0.25 GB + compute buffers).
#
# Reach (2026-09-26 probe): the box's Tailscale was logged out; the path that works is the prod box as a
# jump host over the direct link: `ssh -J beelink yevhen@10.10.10.2`. Wake a suspended box first with
# `ssh beelink '~/epistemic-filter/deploy/halo/wake-halo.sh'`. The user is not in the `docker` group
# (rootful Docker 28.2.2), so the container runs under `sudo docker` with `--user` set to the calling
# user (no persistent change on the box); set DOCKER="docker" if the owner adds the group.
# Host facts: Ubuntu 25.10, kernel 6.17, ROCm 7.1 on the host (unused here), Vulkan 1.4 RADV GFX1151
# (Mesa 25.2.8), 121 GB RAM with about 35 GB available beside the resident LLMs, GTT 123 GB / 53 GB used.
#
# Usage on the box (after `touch ~/halo-hold` for the session; remove it afterwards):
#   MODELS=~/keyframes/models IN=~/keyframes/in OUT=~/keyframes/out \
#   PROMPT="..." SEED=20260926 ./strix_keyframe.sh before.png after.png kf_01
# Run it twice with the same arguments and compare `sha256sum $OUT/kf_01*.png`: the keyframe is
# only usable if the two runs agree byte for byte (determinism gate).
set -euo pipefail
IMG="ghcr.io/leejet/stable-diffusion.cpp@sha256:0ab8e0e0ef3c51db7132f5e15c9e5615a529ea4156573409e8c4b4c97ee1ac37"  # master-vulkan, 2026-09-25
MODELS="${MODELS:?models dir}"; IN="${IN:?input dir}"; OUT="${OUT:?output dir}"
A="${1:?before image (in $IN)}"; B="${2:?after image (in $IN)}"; NAME="${3:-kf}"
PROMPT="${PROMPT:?prompt}"; SEED="${SEED:-20260926}"
NEED_GB="${NEED_GB:-26}"
W="${W:-1024}"; H="${H:-1024}"          # output size; the canvas of mismatch_4 is 1920x1092, so W=1344 H=768 keeps its ratio (2026-09-26)
MAX_VRAM="${MAX_VRAM:-20}"; MEM_CAP="${MEM_CAP:-12g}"   # the GPU budget (GiB) and the CPU-side cgroup cap; raise only after a measured failure
DOCKER="${DOCKER:-sudo docker}"   # the user is not in the docker group on this box (2026-09-26)
# ---- pre-flight: free RAM and free GTT beside the resident LLMs -------------------------------
avail_gb=$(awk '/MemAvailable/ {printf "%d", $2/1048576}' /proc/meminfo)
gtt_total=$(cat /sys/class/drm/card*/device/mem_info_gtt_total 2>/dev/null | head -1 || echo 0)
gtt_used=$(cat /sys/class/drm/card*/device/mem_info_gtt_used 2>/dev/null | head -1 || echo 0)
gtt_free_gb=$(( (gtt_total - gtt_used) / 1073741824 ))
echo "pre-flight: MemAvailable ${avail_gb} GB, GTT free ${gtt_free_gb} GB, need ${NEED_GB} GB"
if [ "$avail_gb" -lt "$NEED_GB" ] || { [ "$gtt_total" -gt 0 ] && [ "$gtt_free_gb" -lt "$NEED_GB" ]; }; then
  echo "REFUSED: not enough free memory beside the resident models; try again later" >&2; exit 3
fi
mkdir -p "$OUT"
RENDER_GID=$(getent group render | cut -d: -f3); VIDEO_GID=$(getent group video | cut -d: -f3)
# the sleep inhibitor needs interactive polkit authentication over a non-interactive ssh session
# ("Failed to inhibit: Interactive authentication required", first run 2026-09-26); the box's idle
# suspend is guarded by ~/halo-hold (touch it for the session), so the inhibitor is a bonus: probe
# it once and run without it when it is refused
INHIBIT=""
if systemd-inhibit --what=sleep:idle --why="probe" -- true >/dev/null 2>&1; then
  INHIBIT="systemd-inhibit --what=sleep:idle --why=keyframe-$NAME --"
else
  echo "note: systemd-inhibit refused in this session; relying on ~/halo-hold ($([ -e ~/halo-hold ] && echo present || echo ABSENT))"
fi
$INHIBIT timeout 45m $DOCKER run --rm --init \
  --user "$(id -u):$(id -g)" --group-add "$RENDER_GID" --group-add "$VIDEO_GID" \
  --device /dev/dri --network none --read-only --tmpfs /tmp \
  --memory "$MEM_CAP" --memory-swap "$MEM_CAP" --pids-limit 256 --cpus 8 --oom-score-adj 1000 \
  -v "$MODELS":/models:ro -v "$IN":/in:ro -v "$OUT":/output "$IMG" \
  --diffusion-model /models/qwen-image-edit-2511-Q4_K_M.gguf \
  --llm /models/Qwen2.5-VL-7B-Instruct.Q4_K_M.gguf \
  --llm_vision /models/Qwen2.5-VL-7B-Instruct.mmproj-Q8_0.gguf \
  --vae /models/qwen_image_vae.safetensors \
  --model-args qwen_image_zero_cond_t=true \
  -r "/in/$A" -r "/in/$B" -p "$PROMPT" \
  --cfg-scale 2.5 --sampling-method euler --flow-shift 3 --diffusion-fa --vae-tiling \
  --max-vram "$MAX_VRAM" --seed "$SEED" --rng cpu --sampler-rng cpu -W "$W" -H "$H" \
  -o "/output/${NAME}.png"
# manifest beside the keyframe: everything a re-render needs to reproduce it
cat > "$OUT/${NAME}.manifest.json" <<EOF
{"image": "$IMG", "models": $(ls -1 "$MODELS" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read().split()))'),
 "before": "$A", "after": "$B", "prompt": $(printf '%s' "$PROMPT" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))'),
 "seed": $SEED, "cfg": 2.5, "sampler": "euler", "flow_shift": 3, "size": [$W, $H], "max_vram": $MAX_VRAM, "mem_cap": "$MEM_CAP",
 "sha256": "$(sha256sum "$OUT/${NAME}.png" | cut -d' ' -f1)", "date": "$(date -Is)"}
EOF
echo "wrote $OUT/${NAME}.png and its manifest"

# Naming conventions — Reveal (as practised in reveal.py / harness.py, 2026-09-13)

- Functions `snake_case`; module-private helpers `_leading_underscore` (`_estimate_h`, `_arbitrate`).
- CLI entry points `cmd_<verb>` (`cmd_check`, `cmd_warmup`, `cmd_align`); HTTP handlers
  `do_GET`/`do_POST` dispatching to `_post_<noun>` / `_send` / `_err`.
- Constants `UPPER_CASE` at module top (`CFG`, `MODES`, `ASPECTS`, `DEFAULT_PORT`, `WORKDIR`,
  `VERSION`); config keys `snake_case` with a unit suffix where one applies (`ecc_trust_px`,
  `residual_cap`, `expo_auto_bhatta`).
- Frames: A = BEFORE = reference, B = AFTER = warped; `H`/`H_ba` is B→A; suffixes `_work`, `_mid`,
  `_full` name the resolution a quantity lives at; `gray*`/`color*`/`rgb*` name the channel space.
- Mode names are short lowercase words (`reshot`, `loose`); video styles likewise (`wipe`, `fade`);
  aspects are the literal ratio strings (`"4:5"`, `"original"`).
- Harness: sections are lettered `== X. name ==`, checks numbered globally; descriptions are one
  sentence stating the property, in lowercase, with the measured number interpolated.
- Version: `VERSION` file and `reveal.py:91` carry the same string; bump minor for a capability,
  patch for a fix; the harness count and HANDOFF header cite the version.
- Job dirs `_reveal/jobs/<16-hex id>/`; exports `before.jpg`, `after_aligned.jpg`, `reveal_<aspect>.mp4`
  (check the allow-list in `Handler` before adding a download name).

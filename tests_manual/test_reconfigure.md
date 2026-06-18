# Tombstone — `test_reconfigure.py` (RETIRED 2026-06-18, stage 9)

**Origin:** `cjm-transcription-plugin-qwen3-forced-aligner/tests_manual/test_reconfigure.py` (2026-05-25). Per-tool instance of the **substrate CR-4 reconfigure contract** (canonical framing: `cjm-media-plugin-silero-vad/tests_manual/test_reconfigure.md`).

**What it validated (contract-level, fake model):** `reconfigure(model_id` flip`)` → `RELOAD_TRIGGER` → `_release_model` + `_apply_config`; `on_disable` releases (CR-2).

**Coverage status:** UNIQUE (substrate reconfigure delta path). **Reimplementation target:** the single `cjm-substrate` reconfigure test (supersedes all per-tool copies).

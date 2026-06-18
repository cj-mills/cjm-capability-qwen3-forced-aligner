# Tombstone — `validate_qwen3_e2e.py` (RETIRED 2026-06-18, stage 9)

**Origin:** `cjm-transcription-plugin-qwen3-forced-aligner/tests_manual/validate_qwen3_e2e.py` (Phase-3-bundle era).
**Retired because:** imported `ForcedAlignResult` from the now-dissolved `cjm-transcription-plugin-system.forced_alignment_core` shim (GitHub-archived 2026-06-18; the DTO now lives in `cjm-capability-primitives.forced_alignment`). Per the stage-9 decision the pre-overhaul `tests_manual` cohort is **retired, not patched**.

**What it validated:** cjm-hf-plugin-utils adoption (HFCacheConfig mixin + snapshot_download_with_progress + load_pretrained_with_oom) + cjm-torch-plugin-utils; heartbeat-wrapped HF Hub model load; WORKER_ENV migration (templated `HF_HOME`); the `self._config → self.config` rename; v2.0 manifest shape; and a real forced-alignment run (audio + transcript) with empirical-DB assertions.

**Coverage status:** SUPERSEDED — `cjm-transcript-decomp-core` exercises qwen3-FA end-to-end on the task channel (the two-input `forced_alignment` task; decomp's M×(VAD ∥ T×FA) composition); schema-v2 validation covers the manifest.

**Reimplementation target:** none required (cores are the standing harness).

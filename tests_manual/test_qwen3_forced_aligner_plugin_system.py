"""
Integration Test: Qwen3 Forced Aligner Plugin via PluginManager

Verifies that the Qwen3 forced alignment plugin can be loaded and executed
over the process boundary through the plugin system.

Run from the cjm-transcription-plugin-qwen3-forced-aligner conda environment:
    python tests_manual/test_qwen3_forced_aligner_plugin_system.py
"""

import asyncio
import os
import sys
from pathlib import Path

from cjm_plugin_system.core.manager import PluginManager
from cjm_plugin_system.core.scheduling import SafetyScheduler


PLUGIN_NAME = "cjm-transcription-plugin-qwen3-forced-aligner"

# Test files relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
TEST_FILES = PROJECT_ROOT / "test_files"
SHORT_AUDIO = TEST_FILES / "short_test_audio.mp3"
SHORT_TEXT_FILE = TEST_FILES / "short_test_audio.txt"
LONG_AUDIO = TEST_FILES / "02 - 1. Laying Plans.mp3"
LONG_TEXT_FILE = TEST_FILES / "02 - 1. Laying Plans.txt"


async def test_discover_and_load():
    """Verify the plugin is discovered and loads via PluginManager."""
    print("=" * 60)
    print("TEST: Discover and Load via PluginManager")
    print("=" * 60)

    manager = PluginManager(scheduler=SafetyScheduler())
    manager.discover_manifests()

    plugin_meta = next((item for item in manager.discovered if item.name == PLUGIN_NAME), None)
    if not plugin_meta:
        print(f"  Plugin {PLUGIN_NAME} not found in discovered manifests.")
        print("  Have you run 'cjm-ctl install-all --plugins plugins_test.yaml'?")
        return None
    print(f"  Discovered: {plugin_meta.name} v{plugin_meta.version}")

    if not manager.load_plugin(plugin_meta, {"language": "English"}):
        print("  Failed to load plugin.")
        return None
    print("  Loaded successfully")

    proxy = manager.plugins.get(PLUGIN_NAME)
    assert proxy is not None, "Plugin proxy not found after loading"
    print(f"  Proxy available: {PLUGIN_NAME}")

    print("  PASSED\n")
    return manager


async def test_execute_short_audio(manager: PluginManager):
    """Verify forced alignment works with short audio via proxy."""
    print("=" * 60)
    print("TEST: Execute with short audio")
    print("=" * 60)

    if not SHORT_AUDIO.exists() or not SHORT_TEXT_FILE.exists():
        print(f"  SKIPPED -- test files not found\n")
        return

    text = SHORT_TEXT_FILE.read_text().strip()
    print(f"  Audio: {SHORT_AUDIO.name}")
    print(f"  Text: {text[:60]}...")

    result = await manager.execute_plugin_async(
        PLUGIN_NAME,
        audio=str(SHORT_AUDIO),
        text=text,
    )

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    items = result.get("items", [])
    metadata = result.get("metadata", {})

    assert len(items) > 0, "Expected at least one aligned word"
    assert all("text" in item and "start_time" in item and "end_time" in item for item in items)
    assert metadata.get("model_id") == "Qwen/Qwen3-ForcedAligner-0.6B"

    print(f"  Aligned {len(items)} words")
    print(f"  First 5 items:")
    for item in items[:5]:
        print(f"    {item['text']:15s} {item['start_time']:.2f}s - {item['end_time']:.2f}s")
    print(f"  Metadata: model_id={metadata.get('model_id')}, language={metadata.get('language')}")

    print("  PASSED\n")


async def test_execute_long_audio(manager: PluginManager):
    """Verify forced alignment works with longer audio (~4 min)."""
    print("=" * 60)
    print("TEST: Execute with long audio (Laying Plans)")
    print("=" * 60)

    if not LONG_AUDIO.exists() or not LONG_TEXT_FILE.exists():
        print(f"  SKIPPED -- test files not found\n")
        return

    text = LONG_TEXT_FILE.read_text().strip()
    word_count = len(text.split())
    print(f"  Audio: {LONG_AUDIO.name}")
    print(f"  Text: {word_count} words")

    result = await manager.execute_plugin_async(
        PLUGIN_NAME,
        audio=str(LONG_AUDIO),
        text=text,
    )

    items = result.get("items", [])
    assert len(items) > 0, "Expected at least one aligned word"

    # Check timestamps are monotonically non-decreasing
    for i in range(1, len(items)):
        assert items[i]["start_time"] >= items[i - 1]["start_time"], (
            f"Non-monotonic timestamps at index {i}: "
            f"{items[i-1]['start_time']} -> {items[i]['start_time']}"
        )

    print(f"  Aligned {len(items)} words (input had {word_count} words)")
    print(f"  Time range: {items[0]['start_time']:.2f}s - {items[-1]['end_time']:.2f}s")
    print(f"  First 3: {[item['text'] for item in items[:3]]}")
    print(f"  Last 3: {[item['text'] for item in items[-3:]]}")

    print("  PASSED\n")


async def test_progress_polling(manager: PluginManager):
    """Verify progress reporting works during execution."""
    print("=" * 60)
    print("TEST: Progress polling during execution")
    print("=" * 60)

    if not SHORT_AUDIO.exists() or not SHORT_TEXT_FILE.exists():
        print(f"  SKIPPED -- test files not found\n")
        return

    text = SHORT_TEXT_FILE.read_text().strip()
    proxy = manager.plugins.get(PLUGIN_NAME)

    # Start execution as a task so we can poll progress
    exec_task = asyncio.create_task(
        manager.execute_plugin_async(
            PLUGIN_NAME,
            audio=str(SHORT_AUDIO),
            text=text,
        )
    )

    # Poll progress a few times
    progress_seen = []
    for _ in range(20):
        try:
            progress = await proxy.get_progress_async()
            if progress and progress.get("progress", 0) > 0:
                progress_seen.append(progress)
                print(f"  Progress: {progress['progress']:.0%} - {progress.get('message', '')}")
        except Exception:
            pass
        await asyncio.sleep(0.5)
        if exec_task.done():
            break

    result = await exec_task
    assert isinstance(result, dict)
    assert len(result.get("items", [])) > 0

    if progress_seen:
        print(f"  Captured {len(progress_seen)} progress updates")
    else:
        print("  No progress updates captured (execution may have been too fast)")

    print("  PASSED\n")


async def run_integration():
    print()
    manager = await test_discover_and_load()
    if manager is None:
        print("Aborting -- plugin not available.")
        sys.exit(1)

    await test_execute_short_audio(manager)
    await test_execute_long_audio(manager)
    await test_progress_polling(manager)

    manager.unload_all()
    print("=" * 60)
    print("ALL PLUGIN SYSTEM TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_integration())

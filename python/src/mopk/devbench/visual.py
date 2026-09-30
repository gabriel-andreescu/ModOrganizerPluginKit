"""Golden image checks through DevBench's capture tool.

Goldens live at <goldens>/<recording>/<variant>/<checkpointId>.png. An optional
<goldens>/<recording>/thresholds.json holds "_default" and per-checkpoint
{"threshold", "regions"} settings, which DevBench scores with SSIM.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from .client import Client

DEFAULT_THRESHOLD = 0.98


def checkpoint_settings(recording_dir: Path, checkpoint_id: str) -> dict:
    path = recording_dir / "thresholds.json"
    thresholds = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    settings = dict(thresholds.get("_default", {}))
    settings.update(thresholds.get(checkpoint_id, {}))
    settings.setdefault("threshold", DEFAULT_THRESHOLD)
    return settings


class Visual:
    def __init__(self, client: Client, goldens: Path, artifacts: Path, *, update: bool):
        self.client = client
        self.goldens = goldens
        self.artifacts = artifacts
        self.update = update

    def check(
        self,
        kind: str,
        checkpoint_id: str,
        *,
        recording: str,
        variant: str = "default",
        arguments: dict | None = None,
    ) -> dict:
        """Capture a checkpoint and compare it with its golden.

        With --visual-update, the capture replaces the golden instead.
        """
        recording_dir = self.goldens / recording
        golden = recording_dir / variant / f"{checkpoint_id}.png"
        request = {
            **(arguments or {}),
            "kind": kind,
            "checkpointId": checkpoint_id,
            "recording": recording,
            "variant": variant,
        }
        if self.update:
            result = self.client.capture(request)
            if result.get("inconclusive"):
                pytest.fail(
                    f"Capture for {checkpoint_id} cannot become a golden: "
                    f"{result.get('inconclusiveReason')}"
                )
            golden.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(result["path"], golden)
            return result

        if not golden.is_file():
            pytest.fail(
                f"No golden at {golden}. Run with --visual-update and review the image"
            )
        settings = checkpoint_settings(recording_dir, checkpoint_id)
        request["golden"] = str(golden.resolve())
        request["threshold"] = settings["threshold"]
        if "regions" in settings:
            request["regions"] = settings["regions"]
        result = self.client.capture(request)
        if result.get("inconclusive"):
            pytest.skip(
                f"Capture for {checkpoint_id} is not comparable: "
                f"{result.get('inconclusiveReason')}"
            )
        if "goldenError" in result:
            pytest.fail(f"Cannot compare {checkpoint_id}: {result['goldenError']}")
        if not result["passed"]:
            candidate = self.artifacts / f"{checkpoint_id}.png"
            shutil.copyfile(result["path"], candidate)
            shutil.copyfile(golden, self.artifacts / f"{checkpoint_id}.golden.png")
            failed = [
                f"{region['name']} {region['ssim']:.4f} < {region['threshold']:.4f}"
                for region in result.get("regions", [])
                if not region["passed"]
            ]
            detail = f" Regions: {', '.join(failed)}." if failed else ""
            pytest.fail(
                f"{checkpoint_id} SSIM {result['ssim']:.4f} is below "
                f"{result['threshold']:.4f}.{detail} Candidate: {candidate}. "
                f"Golden: {golden}"
            )
        return result

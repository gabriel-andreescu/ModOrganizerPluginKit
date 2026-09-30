import json

import pytest

from mopk.devbench.visual import Visual


class Capture:
    def __init__(self, tmp_path, result):
        self.image = tmp_path / "capture.png"
        self.image.write_bytes(b"candidate")
        self.result = {"path": str(self.image), "inconclusive": False, **result}
        self.requests = []

    def capture(self, request):
        self.requests.append(request)
        return self.result


def visual(tmp_path, client, *, update=False):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    return Visual(client, tmp_path / "goldens", artifacts, update=update)


def test_update_replaces_the_golden_with_the_capture(tmp_path):
    client = Capture(tmp_path, {})

    visual(tmp_path, client, update=True).check(
        "preview_nif", "barrel", recording="fo4", arguments={"id": 3}
    )

    assert (tmp_path / "goldens/fo4/default/barrel.png").read_bytes() == b"candidate"
    assert client.requests == [
        {
            "id": 3,
            "kind": "preview_nif",
            "checkpointId": "barrel",
            "recording": "fo4",
            "variant": "default",
        }
    ]


def test_compare_sends_golden_and_checkpoint_thresholds(tmp_path):
    golden = tmp_path / "goldens/fo4/default/barrel.png"
    golden.parent.mkdir(parents=True)
    golden.write_bytes(b"golden")
    regions = [{"name": "muzzle", "x": 0.5, "w": 0.5}]
    (tmp_path / "goldens/fo4/thresholds.json").write_text(
        json.dumps({"_default": {"threshold": 0.9}, "barrel": {"regions": regions}})
    )
    client = Capture(tmp_path, {"ssim": 0.95, "threshold": 0.9, "passed": True})

    visual(tmp_path, client).check("preview_nif", "barrel", recording="fo4")

    request = client.requests[0]
    assert request["golden"] == str(golden.resolve())
    assert (request["threshold"], request["regions"]) == (0.9, regions)


def test_mismatch_fails_and_keeps_both_images(tmp_path):
    golden = tmp_path / "goldens/fo4/default/barrel.png"
    golden.parent.mkdir(parents=True)
    golden.write_bytes(b"golden")
    client = Capture(tmp_path, {"ssim": 0.5, "threshold": 0.98, "passed": False})

    with pytest.raises(
        pytest.fail.Exception, match="barrel SSIM 0.5000 is below 0.9800"
    ):
        visual(tmp_path, client).check("preview_nif", "barrel", recording="fo4")

    assert (tmp_path / "artifacts/barrel.png").read_bytes() == b"candidate"
    assert (tmp_path / "artifacts/barrel.golden.png").read_bytes() == b"golden"


def test_missing_golden_fails_before_capturing(tmp_path):
    client = Capture(tmp_path, {})

    with pytest.raises(pytest.fail.Exception, match="--visual-update"):
        visual(tmp_path, client).check("preview_nif", "barrel", recording="fo4")
    assert client.requests == []

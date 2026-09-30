# DevBench

MOPK provides a Python client and pytest fixtures for MO2's
[DevBench](https://github.com/gabriel-andreescu/modorganizer-dev_bench), plus a
native API package for plugins that register their own tools or capture
providers.

## Python setup

Requires Python 3.11+. In a plugin's Python project:

```powershell
uv add --dev "modorganizer-plugin-kit[test] @ git+https://github.com/gabriel-andreescu/ModOrganizerPluginKit.git#subdirectory=python"
```

Install [DevBench](https://github.com/gabriel-andreescu/modorganizer-dev_bench)
in MO2. The Python client uses its REST API and does not require native API
integration in the plugin being tested.

```python
from mopk.devbench import Client, find_instance

with Client.for_instance(find_instance(instance="Skyrim")) as client:
    mods = client.call("mods", {"action": "list"})
```

Each running MO2 publishes an instance record. `find_instance()` returns the one
live instance matching every given selector: `install` (the MO2 directory),
`instance` (the instance name) and `pid`. It raises when none or several match.

## Pytest

Load the fixtures in the suite's `conftest.py`:

```python
pytest_plugins = ["mopk.devbench.pytest_plugin"]
```

A startup check in `tests/mo2/test_startup.py`:

```python
import pytest


@pytest.mark.mo2
def test_startup(devbench):
    assert devbench.health()["ok"]
```

Start MO2, then run the suite:

```powershell
uv run pytest tests/mo2 --mo2-tests
```

| Option                | Purpose                                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------------------- |
| `--mo2-tests`         | Enable MO2 tests. Without it, tests marked `mo2` and tests using the DevBench session are skipped.   |
| `--devbench-install`  | Select the MO2 install directory.                                                                    |
| `--devbench-instance` | Select the MO2 instance name.                                                                        |
| `--devbench-pid`      | Select the MO2 process.                                                                              |
| `--devbench-url`      | Connect to this HTTP loopback address instead of discovering an instance.                            |
| `--mo2-results`       | Transcript and failed capture directory, defaulting to `test-results/mo2`.                           |
| `--visual-update`     | Replace [goldens](#goldens) with new captures instead of comparing. Review the images before commit. |

Instance selection uses pytest's configuration. In `pyproject.toml`:

```toml
[tool.pytest.ini_options]
devbench_instance = "Skyrim"
```

| Setting                 | Default         | Purpose                                                        |
| ----------------------- | --------------- | -------------------------------------------------------------- |
| `devbench_install`      | Empty           | MO2 install directory to select.                               |
| `devbench_instance`     | Empty           | MO2 instance name to select.                                   |
| `devbench_timeout`      | `30`            | HTTP request timeout in seconds.                               |
| `devbench_wait_timeout` | `30`            | Default timeout of the `wait_for` fixture in seconds.          |
| `devbench_goldens`      | `tests/goldens` | Golden image directory, relative to the pytest root directory. |

Command-line selectors override the settings. The session connects once, when
its first test requests the client. Run MO2 tests without pytest-xdist workers.

| Fixture            | Value                                                                                                                  |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `devbench`         | Client with a separate JSON transcript for each test.                                                                  |
| `devbench_session` | Shared client for the test session.                                                                                    |
| `mo2_artifacts`    | Output directory for the current test.                                                                                 |
| `visual`           | [Golden checks](#goldens) for the current test.                                                                        |
| `wait_for`         | [`mopk.testing.wait_for`](#helpers) with the configured timeout. Pass `timeout=` to override it for a particular wait. |

## Goldens

`visual.check()` runs DevBench's `capture` tool and compares the image with a
reference PNG using SSIM:

```python
@pytest.mark.mo2
def test_render(visual):
    visual.check("my_plugin", "startup", recording="views", arguments={"width": 512})
```

The first argument is the capture `kind`, usually a capture provider the plugin
registers. `arguments` are passed to the provider. The golden is read from
`<devbench_goldens>/<recording>/<variant>/<checkpointId>.png`, and `variant`
defaults to `default`.

Run once with `--visual-update` to write the goldens. On a mismatch, the test
fails and copies the capture and the golden to `mo2_artifacts`. A capture
DevBench reports as inconclusive, such as one that includes UI when UI was
excluded, skips instead.

The default threshold is `0.98`. Override it in
`<devbench_goldens>/<recording>/thresholds.json`, for all checkpoints of the
recording or for one:

```json
{
  "_default": { "threshold": 0.98 },
  "startup": {
    "threshold": 0.95,
    "regions": [
      {
        "name": "status bar",
        "x": 0,
        "y": 0.9,
        "w": 1,
        "h": 0.1,
        "threshold": 0.9
      }
    ]
  }
}
```

`regions` are scored separately in 0 to 1 image coordinates. When present, the
check passes only if every region passes.

## Helpers

Import from `mopk.devbench`:

| Helper                                                    | Use                                                                    |
| --------------------------------------------------------- | ---------------------------------------------------------------------- |
| `Client(base_url, *, session=None, timeout=30)`           | HTTP client. Use as a context manager or call `close()` when finished. |
| `Client.for_instance(instance, *, timeout=30)`            | Client for a discovered instance, bound to its process session.        |
| `find_instance(*, install=None, instance=None, pid=None)` | Returns the one live MO2 matching the selectors.                       |

A client bound to a session fails instead of reaching another MO2 that later
takes the same port.

### Client methods

| Method                                                     | Behavior                                                                                                                                      |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `call(tool, arguments=None, *, record=True, timeout=None)` | Returns the tool's JSON result. Raises on HTTP errors or results reporting `isError: true`. `timeout` overrides the client's request timeout. |
| `capture(arguments, *, timeout=None)`                      | Runs `capture` and returns its structured result, including the saved image's `path`.                                                         |
| `health(*, timeout=None)`                                  | Returns the host's health response.                                                                                                           |
| `tools()`                                                  | Returns the host's tool descriptors by name.                                                                                                  |

All timeouts use seconds.

Import general test helpers from `mopk.testing`:

| Helper                                | Use                                                   |
| ------------------------------------- | ----------------------------------------------------- |
| `wait_for(read, predicate=bool, ...)` | Poll until a condition passes or its timeout expires. |

## Native API

With [MOPK configured](building.md), add the DevBench API package to the plugin
target:

```lua
add_requires("devbench-api 0.1.0", {system = false})

target("Plugin")
    add_packages("devbench-api")
    add_rules("@devbench-api/integration")
```

The API package supplies `DevBenchAPI.h`, the `DevBenchQt.h` handler adapter and
the API's companion source. The integration rule compiles the companion source
into the target.

For interface acquisition, tool registration, capture providers and the Qt
adapter, see DevBench's
[extension API](https://github.com/gabriel-andreescu/modorganizer-dev_bench/blob/main/docs/plugin-authors/extensions.md).

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mopk.devbench import DevBenchError, find_instance, instances


@pytest.fixture
def mo2(tmp_path, monkeypatch):
    records = tmp_path / "devbench" / "mo2" / "instances"
    records.mkdir(parents=True)
    servers = []
    running = set()
    requests = []
    monkeypatch.setattr(instances, "_running", lambda pid: pid in running)

    def start(pid, *, install, instance="", session=None, live=True, port=None):
        if port is not None:
            record = {
                "install": install,
                "instance": instance,
                "session": session or f"session-{pid}",
                "pid": pid,
                "exe": f"{install}\\ModOrganizer.exe",
                "port": port,
            }
            (records / f"{pid}.json").write_text(json.dumps(record), encoding="utf-8")
            return port
        running.add(pid)
        identity = {
            "install": install,
            "instance": instance,
            "session": session or f"session-{pid}",
            "pid": pid,
            "exe": f"{install}\\ModOrganizer.exe",
        }

        class Health(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(pid)
                body = json.dumps({**identity, "port": port, "ok": True}).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Health)
        port = server.server_address[1]
        if live:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            servers.append(server)
        else:
            server.server_close()
        record = {**identity, "port": port}
        if not live:
            record["session"] = "stale"
        (records / f"{pid}.json").write_text(json.dumps(record), encoding="utf-8")
        return port

    start.requests = requests
    yield start
    for server in servers:
        server.shutdown()
        server.server_close()


def test_selects_the_only_live_instance_and_ignores_stale_records(mo2, tmp_path):
    port = mo2(100, install="C:\\MO2", instance="Skyrim")
    mo2(200, install="C:\\Old", live=False)

    found = find_instance(local_app_data=tmp_path)

    assert found.base_url == f"http://127.0.0.1:{port}"
    assert (found.pid, found.session, found.instance) == (100, "session-100", "Skyrim")


def test_selectors_narrow_several_live_instances(mo2, tmp_path):
    mo2(100, install="C:\\MO2", instance="Skyrim")
    mo2(200, install="C:\\MO2", instance="Fallout 4")
    mo2(300, install="C:\\Beta")

    with pytest.raises(DevBenchError, match="Multiple live MO2 instances"):
        find_instance(local_app_data=tmp_path)
    assert find_instance(instance="fallout 4", local_app_data=tmp_path).pid == 200
    assert find_instance(install="c:\\beta", local_app_data=tmp_path).pid == 300
    assert find_instance(pid=100, local_app_data=tmp_path).pid == 100
    with pytest.raises(
        DevBenchError, match=r"MO2 not running: MO2 \(instance Oblivion\)"
    ):
        find_instance(instance="Oblivion", local_app_data=tmp_path)


def test_records_of_exited_processes_are_not_probed(mo2, tmp_path):
    port = mo2(100, install="C:\\MO2", instance="Skyrim")
    for pid in range(200, 215):
        mo2(pid, install="C:\\MO2", instance="Skyrim", port=port)

    assert find_instance(local_app_data=tmp_path).pid == 100
    assert mo2.requests == [100]

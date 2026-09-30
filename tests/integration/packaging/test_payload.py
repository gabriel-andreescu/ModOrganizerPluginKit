import os


def test_payload_follows_input_changes(payload_module):
    stage, invoke = payload_module
    plugin = stage / "plugin.dll"
    plugin.write_bytes(b"original")
    payload = invoke()
    assert (payload / "plugin.dll").read_bytes() == b"original"

    # XMake compares modification times in whole seconds.
    changed = plugin.stat().st_mtime + 2
    plugin.write_bytes(b"modified")
    os.utime(plugin, (changed, changed))
    assert (invoke() / "plugin.dll").read_bytes() == b"modified"

    plugin.unlink()
    assert not (invoke() / "plugin.dll").exists()


def test_asset_overrides_and_removed_override(payload_module):
    stage, invoke = payload_module
    (stage / "config.ini").write_text("base")
    override = stage.parent / "Overrides"
    override.mkdir(parents=True)
    (override / "config.ini").write_text("override")
    script = stage.parent / "xmake.lua"
    script.write_text(
        script.read_text() + '\nadd_installfiles("Missing/(**)", "Overrides/(**)")\n'
    )
    payload = invoke()
    assert (payload / "config.ini").read_text() == "override"
    (override / "config.ini").unlink()
    invoke()
    assert (payload / "config.ini").read_text() == "base"

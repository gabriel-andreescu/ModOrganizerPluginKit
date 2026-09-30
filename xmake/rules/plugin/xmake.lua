rule("plugin")
add_deps("@self/native.compiler", "qt.shared")
on_load(function(target)
    import("core.project.config")
    -- Qt's moc objects only depend on their header, so each MO2 release needs its own build tree.
    local release = path.join(config.builddir(), "mo2-" .. config.get("mo2"))
    target:set("objectdir", path.join(release, ".objs"))
    target:set("autogendir", path.join(release, ".gens"))
    target:set("dependir", path.join(release, ".deps"))
    target:set("targetdir", path.join(release, target:plat(), target:arch(), config.mode()))
    -- Qt's rule configures first and would otherwise select C++17.
    if #table.wrap(target:get("languages")) == 0 then
        target:set("languages", "c++23")
    end
    target:add("frameworks", "QtCore", "QtGui", "QtWidgets", "QtNetwork", "QtQuickWidgets")
end)
after_config(function(target)
    import("core.project.config")
    import("core.base.semver")
    if not is_mode("debug") then
        -- Qt's rule defines this only in release mode. MO2 rejects plugins whose metadata claims debug Qt.
        target:add("defines", "QT_NO_DEBUG")
    end
    target:add("defines", format('MOPK_MO2_VERSION="%s"', config.get("mo2")))
    local version = target:version()
    if version then
        version = semver.new(version)
        target:add(
            "defines",
            "MOPK_VERSION_MAJOR=" .. version:major(),
            "MOPK_VERSION_MINOR=" .. version:minor(),
            "MOPK_VERSION_PATCH=" .. version:patch()
        )
    end
    target:add("installfiles", target:targetfile())
    if target:symbolfile() then
        target:add("installfiles", target:symbolfile())
    end
end)

set_defaultarchs("x64")
set_defaultmode("releasedbg")
set_config("runtimes", "MD")

-- Qt loads plugins built against an older minor version, so every release builds with the oldest Qt.
add_requires("qt6base 6.7.1", { system = false })
-- xmake-requires.lock keeps only the current configuration's packages, so every release is required.
-- XMake reads the description before resolving options, so the default release applies until then.
local selected = get_config("mo2") or "2.5.2"
for _, release in ipairs({ "2.5.2", "2.5.3beta12" }) do
    add_requires("mo2-uibase " .. release, {
        system = false,
        alias = release == selected and "mo2-uibase" or "mo2-uibase-" .. release,
    })
end

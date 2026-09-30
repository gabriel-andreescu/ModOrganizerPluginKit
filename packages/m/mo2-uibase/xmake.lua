package("mo2-uibase")
set_homepage("https://github.com/ModOrganizer2/modorganizer-uibase")
set_description("Mod Organizer 2 plugin interfaces")
set_license("LGPL-3.0-or-later")
add_urls(
    "https://github.com/ModOrganizer2/modorganizer/releases/download/v$(version)/Mod.Organizer-$(version)-uibase.7z"
)
add_versions("2.5.2", "cf066a13556f004f558bfa69fac61aa1ace700280db337259bfb6f1aaa1d5e5c")
add_versions("2.5.3beta12", "local")
on_load(function(package)
    local local_sdk = path.join(os.scriptdir(), package:version_str())
    if os.isdir(local_sdk) then
        -- MO2 publishes no SDK for betas, so they install from the recipe directory.
        package:set("urls", {})
        package:set("sourcedir", local_sdk)
    else
        -- Released SDK headers include game_features headers without their directory.
        package:add("includedirs", "include", "include/uibase/game_features")
    end
end)
on_install("windows|x64", function(package)
    import("core.tool.toolchain")
    import("lib.detect.find_tool")
    if os.isfile("uibase.lib") then
        os.cp("**.h", package:installdir("include/uibase"), { rootdir = "." })
        os.cp("uibase.lib", package:installdir("lib"))
    else
        os.cp("include/*", package:installdir("include"))
        -- versioning.h derives from uibase's QString formatter without including it.
        io.replace(
            path.join(package:installdir("include"), "uibase", "versioning.h"),
            '#include "exceptions.h"',
            '#include "exceptions.h"\n#include "formatters/qt.h"',
            { plain = true }
        )
        local msvc = toolchain.load("msvc", { plat = package:plat(), arch = package:arch() })
        assert(msvc:check(), "MSVC is required to create the uibase import library")
        local envs = msvc:runenvs()
        local lib = assert(find_tool("lib", { envs = envs }), "lib.exe not found")
        os.mkdir(package:installdir("lib"))
        os.vrunv(lib.program, {
            "/nologo",
            "/machine:x64",
            "/def:uibase.def",
            "/out:" .. path.join(package:installdir("lib"), "uibase.lib"),
        }, { envs = envs })
    end
end)

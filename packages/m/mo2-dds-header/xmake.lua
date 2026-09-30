package("mo2-dds-header")
set_kind("library", { headeronly = true })
set_homepage("https://github.com/microsoft/DirectXTex")
set_description("DirectXTex DDS header")
set_license("MIT")
local tags = { ["2024.06"] = "jun2024" }
add_urls("https://raw.githubusercontent.com/microsoft/DirectXTex/$(version)/DirectXTex/DDS.h", {
    version = function(version)
        return tags[tostring(version)]
    end,
})
add_versions("2024.06", "d24d7f9f736a331a564046a38faff29bb55578e0ceca1b28951bbde52b6cb3cf")
on_install(function(package)
    os.cp(package:originfile(), path.join(package:installdir("include"), "DDS.h"))
end)

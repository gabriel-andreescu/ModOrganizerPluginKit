package("devbench-api")
set_kind("library", { headeronly = true })
set_homepage("https://github.com/gabriel-andreescu/modorganizer-dev_bench")
set_description("DevBench plugin API")
set_license("MIT")
add_urls("https://github.com/gabriel-andreescu/modorganizer-dev_bench/archive/$(version).tar.gz", {
    version = function(version)
        local revisions = {
            ["0.1.0"] = "6d657e625a8f8af87f4d4bc84dadcedd07b96a81",
        }
        return revisions[tostring(version)]
    end,
})
add_versions("0.1.0", "183a4330b5e988abae0b7ac35ce1ee447e46acca00cb753836e5bdfca7058f53")
on_install(function(package)
    os.cp("include/DevBenchAPI.h", package:installdir("include"))
    os.cp("include/DevBenchQt.h", package:installdir("include"))
    os.cp("include/DevBenchAPI.cpp", package:installdir("share"))
end)

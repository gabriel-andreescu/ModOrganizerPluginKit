rule("integration")
on_config(function(target)
    local source = path.join(target:pkg("devbench-api"):installdir(), "share/DevBenchAPI.cpp")
    -- Generated sources avoid embedding the package-cache path in object paths.
    local staged = path.join(target:autogendir(), "devbench", "DevBenchAPI.cpp")
    os.cp(source, staged, { copy_if_different = true })
    target:add("files", staged)
end)

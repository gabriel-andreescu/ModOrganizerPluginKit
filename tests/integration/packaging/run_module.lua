function main(operation, name, payload, configuration, mo2)
    local config = import("core.project.config")
    config.load()
    config.set("mo2", mo2)
    local project = import("core.project.project")
    local target = assert(project.target(name))
    local modules = path.join(os.scriptdir(), "../../../xmake/modules")
    if operation == "deploy" then
        import("deployment", { rootdir = modules }).deploy(target, payload)
    elseif operation == "package" or operation == "package-real" then
        local json = import("core.base.json")
        if operation == "package" then
            import("utils.archive").archive = function(output, files, options)
                local contents = {}
                for _, file in ipairs(files) do
                    contents[file:gsub("\\", "/")] = io.readfile(path.join(options.curdir, file))
                end
                json.savefile(output, contents)
            end
        end
        import("packaging", { rootdir = modules }).package(target, payload, json.decode(configuration))
    else
        raise("Unknown operation: " .. operation)
    end
end

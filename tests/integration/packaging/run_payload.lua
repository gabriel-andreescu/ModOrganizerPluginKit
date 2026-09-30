function main(requestfile)
    local json = import("core.base.json")
    local config = import("core.project.config")
    local request = json.loadfile(requestfile)
    config.load()
    config.set("mo2", request.mo2)
    local modules = path.join(os.scriptdir(), "../../../xmake/modules")
    local target = import("core.project.project").target("TestPlugin")
    target:data_set("mopk.package", { options = {} })
    local result = { output = import("payload", { rootdir = modules }).prepare(target) }
    json.savefile(requestfile .. ".result", result)
end

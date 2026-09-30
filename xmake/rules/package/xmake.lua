rule("package")
on_load(function(target)
    target:set("kind", "phony")
    target:data_set("mopk.package", {
        options = target:extraconf("rules", "@addon/mopk/package") or {},
    })
end)
after_load(function(target)
    for _, name in ipairs(target:data("mopk.package").options.targets or {}) do
        target:add("deps", name, { inherit = false })
    end
end)
after_build(function(target)
    import("core.project.config")
    local payload = import("@self.payload").prepare(target)
    if config.get("deploy") then
        import("@self.deployment").deploy(target, payload)
    end
end)
on_package(function(target)
    local payload = import("@self.payload").prepare(target)
    import("@self.packaging").package(target, payload, target:data("mopk.package"))
end)

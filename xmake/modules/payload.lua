import("core.project.depend")
import("core.project.config")

function collect(target, output)
    local selected = {}
    local function include(source_target)
        local sources, destinations = source_target:installfiles(output)
        for index, source in ipairs(sources) do
            if path.filename(source):lower() ~= ".gitkeep" then
                local destination = path.relative(destinations[index], output)
                selected[destination:lower()] = { source = source, destination = destination }
            end
        end
    end
    for _, name in ipairs(target:data("mopk.package").options.targets or {}) do
        include(assert(target:dep(name), "Unknown package target: " .. name))
    end
    include(target)
    local inputs = table.values(selected)
    table.sort(inputs, function(left, right)
        return left.destination < right.destination
    end)
    return inputs
end

function prepare(target)
    if target:data("mopk.payload") then
        return target:data("mopk.payload")
    end
    local plugin = target:data("mopk.package")
    local directory = path.join(config.builddir(), "mopk", (target:fullname():gsub("::", "/")))
    local output = path.join(directory, "payload")
    local inputs = collect(target, output)
    local files, layout = {}, {}
    for _, input in ipairs(inputs) do
        table.insert(files, input.source)
        table.insert(layout, input.destination)
    end
    local implementation = os.files(path.join(os.scriptdir(), "**"))
    table.sort(implementation)
    table.join2(files, implementation)
    depend.on_changed(function()
        local stage = os.tmpfile() .. ".dir"
        os.mkdir(stage)
        try({
            function()
                for _, input in ipairs(inputs) do
                    os.cp(input.source, path.join(stage, input.destination))
                end
                if os.exists(output) then
                    os.rm(output)
                end
                os.mv(stage, output)
            end,
            finally({
                function(ok, errors)
                    os.tryrm(stage)
                    if not ok then
                        raise(errors)
                    end
                end,
            }),
        })
    end, {
        dependfile = path.join(config.directory(), "mopk", target:fullname():gsub("::", "/"), "payload.d"),
        files = files,
        values = {
            config.get("mo2"),
            target:name(),
            output,
            string.serialize(plugin.options, { orderkeys = true }),
            layout,
        },
        changed = not os.isdir(output),
    })
    target:data_set("mopk.payload", output)
    return output
end

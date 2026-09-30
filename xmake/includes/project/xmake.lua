option("deploy", { default = true, description = "Deploy configured targets" })
option("distdir", { description = "Package output directory" })
option("mo2", {
    default = "2.5.2",
    values = { "2.5.2", "2.5.3beta12" },
    description = "Mod Organizer 2 release to build for",
})

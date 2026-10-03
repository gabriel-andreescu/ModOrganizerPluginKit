# Dependencies and MO2 releases

## MO2 releases

| Release       | uibase                                                                                                | Qt used by builds |
| ------------- | ----------------------------------------------------------------------------------------------------- | ----------------- |
| `2.5.2`       | MO2's published SDK.                                                                                  | 6.7.1             |
| `2.5.3beta12` | Headers from the beta's source archive, with an import library created from its `uibase.dll` exports. | 6.7.1             |

MO2 2.5.3 betas ship Qt 6.11. Qt loads plugins built against an older minor
version, so every release builds against the Qt that MO2 2.5.2 ships.

The beta's import library links against exactly what that beta exports. A header
declaring a function the DLL does not export fails at link time instead of when
MO2 loads the plugin.

## Library sources

| Dependency         | Source used by MOPK                                                                                                                                                                  | MOPK changes                                               |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| uibase 2.5.2       | MO2's `Mod.Organizer-2.5.2-uibase.7z` release asset, pinned in [the recipe](../../../packages/m/mo2-uibase/xmake.lua)                                                                | `include/uibase/game_features` include path.               |
| uibase 2.5.3beta12 | The beta's source archive and `uibase.dll`, stored in [the recipe directory](../../../packages/m/mo2-uibase/2.5.3beta12)                                                             | Missing `formatters/qt.h` include added to `versioning.h`. |
| Qt                 | [xmake-repo](https://github.com/xmake-io/xmake-repo)'s `qt6base` binaries, installed through aqtinstall                                                                              | None.                                                      |
| libbsarch          | [ModOrganizer2/libbsarch](https://github.com/ModOrganizer2/libbsarch)'s release, pinned in [the recipe](../../../packages/m/mo2-libbsarch/xmake.lua)                                 | Headers and import libraries only.                         |
| DevBench API       | [DevBench](https://github.com/gabriel-andreescu/modorganizer-dev_bench)'s release archive, pinned by commit and checksum in [the recipe](../../../packages/d/devbench-api/xmake.lua) | Packages the MIT API headers and companion source.         |
| DDS header         | DirectXTex's `DDS.h`, pinned in [the recipe](../../../packages/m/mo2-dds-header/xmake.lua)                                                                                           | Header installed unchanged.                                |

Include uibase headers through their directory, for example
`#include <uibase/iplugin.h>`. The headers keep their LGPL-3.0 notices.

Plugins that read Bethesda archives require libbsarch. MO2 ships its DLL:

```lua
add_requires("mo2-libbsarch 0.1.2", {system = false})

target("Plugin")
    add_packages("qt6base", "mo2-uibase", "mo2-libbsarch")
```

## Contributing

Contributions to wow.export are welcome, please file a pull-request with adequate details.

Pull-requests are expected to be complete. If a pull-request requires significant work by a maintainer to merge then it will be rejected - consider making a feature suggestion instead!

> [!IMPORTANT] Pull-requests that add third-party libraries, use external services or adjust the build pipeline without first consulting the #wow-export-dev channel will be rejected.

Development of wow.export is actively discussed in [#wow-export-dev](https://discord.gg/kC3EzAYBtf). While participation is not mandatory for pull-requests, those wishing to contribute frequently are expected to be present.

If you plan to make a large contribution, it is expected that you would open a self-assigned tracking issue and co-ordinate with the active maintainers before starting.

Open-issues that have an assignee and are not listed as "Backlog" on the roadmap are currently championed by a maintainer. Contributors should not target these issues.

## Roadmap

The developers maintain a [public roadmap](https://github.com/users/Kruithne/projects/1/views/9) to help give insight and organization to the development process. Before contributing, it's recommended to consult this.

## Building (Developers Only)

### Prerequisites
- **Bun** 1.2 or above (required)
- **Node.js** v24.9.0 or above (required for native add-ons)
- **Python 3** (required for node-gyp; this checkout was built with Python 3.13)
- **node-gyp** (required for building native add-ons): `npm install -g node-gyp@latest`
- **Build tools** (platform-specific):
  - Windows: Visual Studio Build Tools with C++ support
  - Linux: `build-essential` package (`sudo apt-get install build-essential`)
  - macOS: Xcode Command Line Tools

### Build Steps
```
git clone https://github.com/Kruithne/wow.export.git
cd wow.export
bun install

# This will list available builds.
bun ./build.js

# This will compile -all- available builds.
bun ./build.js *

# Substitute <BUILD> for the build(s) you wish to compile, space-delimitated.
bun ./build.js <BUILD1> <BUILD2> ...
```

**Note**: The build process will automatically download nw.js headers and handle native add-on compilation if any are present in the `node_addons/` directory.

### Visual Studio CMake workspace

Open the repository with **File > Open > Folder** and select `x64-debug` or
`x64-release`. Install the Visual Studio C++ CMake tools (CMake 3.21+ and Ninja).
If CMake was previously disabled, set `enableCMake` to `true` in
`.vs/CMakeWorkspaceSettings.json`, then reopen the folder.

The default build compiles `native_geometry` and copies its DLL beside the
Blender addon. Close Blender before replacing a helper DLL it has loaded.
Select `wow_export_app` to run the existing Bun/NW.js application build, which
also builds the helper. Install the prerequisites above and run `bun install`
first. The native Node addon pipeline remains in `build/build-native-addons.js`.

From a Visual Studio x64 developer terminal:

```powershell
cmake --preset x64-release
cmake --build --preset native-release
# Or build the full application:
cmake --build --preset app-release
```

Use `x64-debug`, `native-debug`, and `app-debug` for development. Build outputs
and personal Visual Studio settings are ignored by Git.

## Debugging (Developers Only)
> **Note**: Debugging is currently only supported on Windows.

To debug wow.export, compile a `win-x64-debug` build using the build script. This will produce a bare-bones build using the SDK framework and without any production polish. Upon starting the debug version, DevTools will be automatically launched alongside the application.

For the debug build, source code will not be compiled, rather a symlink is created. This means changes to the source code are instantly reflected in the application, simply run `chrome.runtime.reload()` in DevTools console to refresh sources (pressing F5 does not drop references and will lead to memory leaks).

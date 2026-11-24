# G6-X

G6-X is an experimental Xbox Series compatibility workspace for Windows. It builds a native Direct3D 12 runtime, integrates Leonida’s Vulkan research tools, and can compare PE import reports from both projects and XCL. The primary runtime is derived from VIctory.

**GTA VI gameplay remains unverified.** VIctory reported reaching the world, where it showed a title card followed by a dark scene, dropped draws, and roughly 0.5–1.8 seconds per frame. The pinned Leonida revision boots a synthetic title end to end. Leonida’s public status still reports that the retail game has yet to boot. G6-X validation uses synthetic fixtures and Windows system executables. [VIctory status](https://github.com/Marvisak/VIctory/blob/d2a4bae1f49533ef5cb512fd1b1ba1513f2e1989/README.md#status-2026-11-23) · [Leonida status](https://github.com/ubiquitarianism/leonida/blob/1c93c8697078c3ccbd6f374caf5bb3ab0b6bc8e4/README.md#project-status)

## Quick start

```powershell
git clone --recurse-submodules https://github.com/devz-on/G6-X.git
cd G6-X
python g6x.py --help
python g6x.py inspect "$env:SystemRoot\System32\whoami.exe" --json
```

The last command uses Leonida’s Python inspector and does not run the executable. It needs Python 3.12+ and the Leonida checkout. If you cloned without submodules, fetch them with `git submodule update --init --recursive`. GitHub’s source ZIP omits the submodule contents.

To update an existing clone, run `git pull --ff-only` and `git submodule update --init --recursive`.

## Build and compare

| Backend | Requirements | Build from the repository root |
| --- | --- | --- |
| G6-X native runtime | Windows 10/11 x64, MSVC C++ build tools, Windows SDK and Rustup. Rust is pinned by the workspace. Title execution also needs AVX2 and D3D12 Shader Model 6.6, with mesh shaders for world rendering. | `python g6x.py build runtime` |
| XCL | Windows x64, Rust stable MSVC, Windows SDK and DXC. See upstream for GPU, Gaming Services and Windows 10 Agility SDK requirements. | `python g6x.py build xcl` |
| Leonida runtime | CMake 3.24+, C++20 and Windows SDK 10.0.26100+ for the Windows loader. Install the Vulkan SDK for the Vulkan path. The build on other systems provides the portable targets available on that host. | `python g6x.py build leonida` |

The build command runs each backend in its own workspace. The two Rust builds use lockfiles. A successful Windows build creates `runtime/target/release/g6x-runtime.exe` or `upstream/xcl/target/release/xcl.exe`. Leonida’s CMake output goes under `upstream/leonida/runtime/build/`, with a configuration subdirectory for multi-config generators. [XCL build notes](https://github.com/ivall/xcl/blob/1ec4c98cda119432a4b3f205e146fba2d6f8379a/README.md#building-and-usage) · [Leonida build notes](https://github.com/ubiquitarianism/leonida/blob/1c93c8697078c3ccbd6f374caf5bb3ab0b6bc8e4/README.md#how-to-build)

```powershell
$image = 'D:\g6x-data\game\title.exe'
python g6x.py inspect "$image" --backend all
python g6x.py inspect "$image" --backend all --json |
    Set-Content -Encoding utf8 'D:\g6x-data\imports.json'
```

- Use `--backend runtime`, `--backend xcl` or `--backend leonida` for one inspector. Leonida is the default. For custom Cargo output locations, pass `--runtime-bin` or `--xcl-bin`.
- The JSON schema labels each DLL, function and normal or delay-load import and includes each inspector’s reported statuses. `unreported` in the table means the inspector did not return that import. JSON omits that backend from the row.
- Leonida classifies the DLL’s location or need for a shim. G6-X reports function-level HLE or Windows pass-through and unresolved imports. XCL can additionally report a bundled DLL or a stub. These classifications answer different questions and help narrow down an import discrepancy. An HLE match gives no assurance that the implementation covers every call the title makes.
- Existing native commands remain available under `g6x-runtime --help`, including `census`, `lib-exports`, `shader-info` and `translate`.

## Run the native runtime

Use an already-readable executable from your own copy of the game. Keep the executable, caches, reports and any generated data outside the checkout. Edit a copy of the [configuration example](runtime/g6x.example.toml) if you need custom paths.

```powershell
$runtime = '.\runtime\target\release\g6x-runtime.exe'
$image = 'D:\g6x-data\game\title.exe'

& $runtime config
& $runtime run "$image"               # Map and bind imports
& $runtime run "$image" --execute     # Start the title
```

Set `VICTORY_CONFIG` to your configuration file’s absolute path, or run from a directory with a local `g6x.toml`. The runtime accepts legacy `victory.toml` and `VICTORY_*` settings. It defaults to `%LOCALAPPDATA%\G6-X\data` for saves and `%LOCALAPPDATA%\G6-X\cache` for caches. Use `VICTORY_DATA_DIR` and `VICTORY_CACHE_DIR` to select existing locations explicitly.

BCPack decoding reads a compatible local table file from `G6X_BCPACK_TABLES`. G6-X excludes the table blob because VIctory’s asset policy says its license does not cover that blob. When the variable is unset or the file cannot be read or parsed, the runtime logs the cause on the first BCPack request and those requests fail. Uncompressed reads and zlib-only requests continue to work. [Asset policy](runtime/docs/asset-policy.md)

World load can hang a hardware GPU and trigger a display-driver reset, as documented upstream. For diagnostics with the software adapter, build with the `diagnostics` feature and set `VICTORY_D3D12_WARP=1`. Review logs under the configured data directory before sharing a reproduction. [Runtime diagnostics](runtime/README.md#debugging)

## What remains

| Area | Work remaining | How to verify progress |
| --- | --- | --- |
| World rendering | Resolve dropped draws and dark world frames. Track missing mesh, vertex, pixel and compute translations, including 64-bit image atomics and merged geometry. | Start with the translated-shader report and a software-adapter capture. On an owned package and known GPU, confirm visible world frames, frame time and lack of a driver reset. |
| Graphics and streaming | Validate indirect draws, render-target metadata planes, ray-tracing builder shaders, and BCPack streaming with legitimately supplied local tables. | Use a synthetic regression for each failure, then check the same title scene with runtime logs. |
| Leonida Vulkan | Exercise the loader against the retail title and verify mesh draws, indirect draw state, stream output and wave64 behavior across 32- and 64-lane GPUs. | Compare the import reports and follow the Vulkan validation plan at the pinned revision. [Vulkan plan](https://github.com/ubiquitarianism/leonida/blob/1c93c8697078c3ccbd6f374caf5bb3ab0b6bc8e4/docs/d3d12_vulkan.md) |
| XCL compatibility | Verify the exact title build independently, including mesh pipeline creation and progression beyond menus. | Compare XCL import diagnostics and its local `report.json` against a reproducible synthetic baseline. [XCL handoff](https://github.com/ivall/xcl/blob/1ec4c98cda119432a4b3f205e146fba2d6f8379a/HANDOFF.md) |
| Audio and platform behavior | Check in-title Opus output, reverb, speech, text entry, relaunch, save recovery and controller behavior. | Reproduce each on a known title build with native runtime diagnostics. |

## Verify and contribute

The Windows validation run built both Rust release binaries. G6-X passed 266 native tests with 4 ignored, and the three inspectors reported the synthetic DLL’s normal and delay-load imports. XCL reported 715 passes and 41 ignored across its workspace suite and synthetic launch test.

Leonida’s previous pin ran all 6,105 semantic tests with no failing modules. At the current pin, the Windows loader rebuilt and passed its bounds and synthetic launch tests. The changed semantic tests and new Python tests passed. The PE inspector reported 59 passes and one skip.

Four Leonida Vulkan parity tests reproduced failures on Windows with AMD Radeon 760M Graphics. The checked cases were row-major alias readback (`d3d12_texture_tiles`), indirect dispatch argument validation (`d3d12_execute_indirect_validation`), depth clear behavior (`d3d12_clear`) and pipeline library blob validation (`d3d12_pipeline_library_host`). These are standalone upstream tests. The synthetic title launch and G6-X import comparison work independently of those graphics cases.

```powershell
python -m unittest discover -s tests

Push-Location runtime
cargo test --locked --workspace
cargo xtask policy
Pop-Location

Push-Location upstream/xcl
.\scripts\test.ps1
Pop-Location

Push-Location upstream/leonida
python -I tests/test_pe_inspect.py
python -I scripts/run_semantic_tests.py tests/semantic
ctest --test-dir runtime/build -C RelWithDebInfo --output-on-failure
Pop-Location
```

Leonida’s semantic suite uses the SPIR-V assembler and validator on `PATH`. Additional runtime tests depend on tools such as AMDGPU `llvm-mc`, SDL3, `glslangValidator`, Vulkan and compatible hardware. XCL reports environment-dependent GPU skips through its test script. [Leonida testing](https://github.com/ubiquitarianism/leonida/blob/1c93c8697078c3ccbd6f374caf5bb3ab0b6bc8e4/docs/testing.md)

For a runtime issue, record the backend and commit, OS, GPU and driver, build profile, and the first failing step. Provide a source-based synthetic fixture when possible. Game data, keys, extracted assets, shaders and dumps belong outside the repository.

## Source layout and credit

```text
g6x.py                   Build and PE import comparison CLI
runtime/
  cli/                   g6x-runtime commands
  components/            Loader, HLE, graphics, shaders, formats and shared code
  docs/                  Runtime architecture and asset policy
  tests/                 Synthetic runtime fixtures
  xtask/                 Source-tree and staged-asset checks
upstream/
  leonida/               Pinned Vulkan runtime and research tools
  xcl/                   Pinned D3D12 compatibility layer
tests/                   Tests for the G6-X CLI
```

| Source | Revision | License |
| --- | --- | --- |
| [VIctory by Marvisak and contributors](https://github.com/Marvisak/VIctory/tree/d2a4bae1f49533ef5cb512fd1b1ba1513f2e1989) | `d2a4bae1f49533ef5cb512fd1b1ba1513f2e1989` | GPL-3.0-or-later |
| [Leonida Continued by ubiquitarianism, NotRexed and contributors](https://github.com/ubiquitarianism/leonida/tree/1c93c8697078c3ccbd6f374caf5bb3ab0b6bc8e4) | `1c93c8697078c3ccbd6f374caf5bb3ab0b6bc8e4` | GPL-3.0-or-later |
| [XCL by ivall and contributors](https://github.com/ivall/xcl/tree/1ec4c98cda119432a4b3f205e146fba2d6f8379a) | `1ec4c98cda119432a4b3f205e146fba2d6f8379a` | GPL-2.0-only |

G6-X and the modified native runtime are GPL-3.0-or-later. The comparison tool calls the upstream inspectors as separate processes. XCL’s GPL-2.0-only code stays in its own build and retains its license. The upstream trees provide their own third-party notices. See the [G6-X license](LICENSE), [native runtime provenance and change notice](runtime/UPSTREAM.md) and [GNU GPL compatibility guidance](https://www.gnu.org/licenses/gpl-faq.html#v2v3Compatibility).

G6-X is an independent project. Grand Theft Auto, Xbox and other marks belong to their respective owners.

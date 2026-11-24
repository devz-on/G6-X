# Native runtime provenance

This workspace is a modified version of [Marvisak/VIctory](https://github.com/Marvisak/VIctory), based on commit [`d2a4bae1f49533ef5cb512fd1b1ba1513f2e1989`](https://github.com/Marvisak/VIctory/tree/d2a4bae1f49533ef5cb512fd1b1ba1513f2e1989). Credit for the original code belongs to Marvisak and the upstream contributors. See [LICENSE](LICENSE).

G6-X modified this source on 2026-11-24.

- Renamed the executable and configuration example and reorganized the workspace into `cli/` and `components/`.
- Added machine-readable PE import inspection for cross-backend comparison.
- Fixed import census totals for named imports that use different linker hints.
- Changed BCPack to load a user-provided table file at runtime. The imported snapshot excludes the upstream BCPack table binary, which upstream identifies as outside its license.
- Adapted the asset-policy checks and hook for the nested runtime workspace.
- Made frame clock tests account for late scheduling and added a deterministic check for skipped and repeated ticks.

Internal Rust library package names and legacy `VICTORY_*` environment variables retain the upstream names for compatibility.

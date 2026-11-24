#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build and compare the Xbox compatibility tools included in G6-X."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
SOURCES = {
    "leonida": ROOT / "upstream" / "leonida",
    "runtime": ROOT / "runtime",
    "xcl": ROOT / "upstream" / "xcl",
}


def source(backend, marker):
    directory = SOURCES[backend]
    if not (directory / marker).is_file():
        raise ValueError(
            f"{backend} source is missing. Run git submodule update --init --recursive "
            "from the G6-X checkout."
        )
    return directory


def build(backend):
    if backend in ("runtime", "xcl"):
        directory = source(backend, "Cargo.toml")
        scope = ["-p", "g6x-runtime"] if backend == "runtime" else ["--workspace"]
        subprocess.run(["cargo", "build", "--release", "--locked", *scope], cwd=directory, check=True)
        return

    directory = source(backend, "runtime/CMakeLists.txt")
    config = "RelWithDebInfo"
    subprocess.run(
        ["cmake", "-S", "runtime", "-B", "runtime/build", f"-DCMAKE_BUILD_TYPE={config}"],
        cwd=directory,
        check=True,
    )
    subprocess.run(
        ["cmake", "--build", "runtime/build", "--config", config, "--parallel"],
        cwd=directory,
        check=True,
    )


def inspect_leonida(image):
    directory = source("leonida", "tools/pe_inspect.py")
    with tempfile.TemporaryDirectory(prefix="g6x-pe-") as scratch:
        subprocess.run(
            [sys.executable, "-X", "utf8", "-I", "tools/pe_inspect.py", str(image), "--out", scratch],
            cwd=directory,
            stdout=subprocess.DEVNULL,
            check=True,
        )
        report = Path(scratch) / (image.name + ".json")
        return json.loads(report.read_text(encoding="utf-8"))


def inspect_native(backend, image, binary):
    if binary is None:
        executable = "g6x-runtime" if backend == "runtime" else "xcl"
        name = executable + (".exe" if os.name == "nt" else "")
        binary = SOURCES[backend] / "target" / "release" / name
    if not binary.is_file():
        raise ValueError(
            f"{backend} binary not found at {binary}. Build it with "
            f"python g6x.py build {backend} or pass --{backend}-bin."
        )
    env = os.environ.copy()
    if backend == "xcl":
        env.pop("XCL_HOST", None)
    result = subprocess.run(
        [str(binary.resolve()), "inspect", str(image), "--json"],
        env=env,
        stdout=subprocess.PIPE,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)


def import_rows(backend, report):
    for entry in report["imports"]:
        dll = entry["dll"].lower()
        if backend == "leonida":
            for function in entry["functions"]:
                yield (dll, function, entry["kind"]), entry["where"]
        else:
            kind = "delay" if entry["delay"] else "normal"
            yield (dll, entry["function"], kind), entry["status"]


def compare(image, reports):
    by_import = {}
    for backend, report in reports.items():
        for key, status in import_rows(backend, report):
            statuses = by_import.setdefault(key, {})
            statuses.setdefault(backend, set()).add(status)

    imports = []
    for (dll, function, kind), statuses in sorted(by_import.items()):
        imports.append({
            "dll": dll,
            "function": function,
            "kind": kind,
            "status": {backend: sorted(values) for backend, values in statuses.items()},
        })
    return {"schema_version": 1, "image": image.name, "backends": list(reports), "imports": imports}


def inspect(args):
    image = args.image.resolve()
    if not image.is_file():
        raise ValueError(f"image file not found: {args.image}")

    selected = SOURCES if args.backend == "all" else (args.backend,)
    binaries = {"runtime": args.runtime_bin, "xcl": args.xcl_bin}
    reports = {}
    for backend in selected:
        try:
            reports[backend] = (
                inspect_leonida(image) if backend == "leonida"
                else inspect_native(backend, image, binaries[backend])
            )
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            # Keep paths and the upstream error readable while leaving stdout empty on failure.
            detail = f"inspector exited with code {error.returncode}" if isinstance(
                error, subprocess.CalledProcessError
            ) else str(error)
            raise ValueError(f"{backend}: {detail}") from error

    result = compare(image, reports)
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"{result['image']} | {len(result['imports'])} distinct imports")
    for row in result["imports"]:
        statuses = " | ".join(
            f"{backend}={', '.join(row['status'].get(backend, ['unreported']))}"
            for backend in result["backends"]
        )
        print(f"{row['dll']}!{row['function']} [{row['kind']}] | {statuses}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build", help="build one backend using its own toolchain")
    build_parser.add_argument("backend", choices=SOURCES)

    scan = commands.add_parser("inspect", help="compare PE imports without executing the input")
    scan.add_argument("image", type=Path, help="an already-readable EXE or DLL")
    scan.add_argument("--backend", choices=[*SOURCES, "all"], default="leonida")
    scan.add_argument("--runtime-bin", type=Path, help="path to g6x-runtime")
    scan.add_argument("--xcl-bin", type=Path, help="path to an XCL executable")
    scan.add_argument("--json", action="store_true", help="write a machine-readable report to stdout")
    args = parser.parse_args()

    try:
        if args.command == "build":
            build(args.backend)
        else:
            inspect(args)
    except subprocess.CalledProcessError as error:
        print(f"g6x: {args.backend} build failed (exit code {error.returncode})", file=sys.stderr)
        return error.returncode if error.returncode > 0 else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"g6x: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

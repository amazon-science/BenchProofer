# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""`swebench-unified` — the single argparse entry point (docs/reproducing.md).
Each subcommand thinly delegates to its owning module (see _COMMANDS); heavy
modules are imported lazily so `--help` works without eval/verifier/agent
dependencies installed.
"""
from __future__ import annotations

import argparse
import contextlib
import os
import sys
import time


def _extract_benchmark_dir(argv: list[str]) -> list[str]:
    """Pull a global `--benchmark-dir NAME` (or `--benchmark-dir=NAME`) out of
    argv and export it as SBU_BENCHMARK_DIR before anything imports paths, so
    the constructed-bundle root is set for this process AND the build_one
    subprocesses `--all` spawns (which inherit the env). Returns argv without
    it."""
    out: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--benchmark-dir":
            if i + 1 >= len(argv):
                print("--benchmark-dir requires a value", file=sys.stderr)
                raise SystemExit(2)
            os.environ["SBU_BENCHMARK_DIR"] = argv[i + 1]
            i += 2
        elif a.startswith("--benchmark-dir="):
            os.environ["SBU_BENCHMARK_DIR"] = a.split("=", 1)[1]
            i += 1
        else:
            out.append(a)
            i += 1
    return out


@contextlib.contextmanager
def _argv(prog: str, args: list[str]):
    """Delegate to a module main() that parses sys.argv itself."""
    saved = sys.argv
    sys.argv = [prog, *args]
    try:
        yield
    finally:
        sys.argv = saved


def _cmd_construct(argv: list[str]) -> int:
    # Peek at --all to pick the entry point; everything else is that module's own
    # argparse.
    peek = argparse.ArgumentParser(add_help=False)
    peek.add_argument("--all", action="store_true")
    known, _ = peek.parse_known_args(argv)
    if known.all:
        from .construct.run_all import main as run_all_main
        return run_all_main([a for a in argv if a != "--all"])
    from .construct.build_one import main as build_one_main
    if {"-h", "--help"} & set(argv):
        # Two parsers behind one subcommand. Without this, `construct --help`
        # shows build_one's flags and names neither `--all` nor the driver flags,
        # so the fan-out reads as unsupported and its dry run as nonexistent --
        # which is how an operator ends up starting the real thing to find out.
        # `finally`, so the note is printed on argparse's own SystemExit path and
        # that exit still propagates: every other subcommand's --help exits, and
        # this one must not become the exception.
        try:
            return build_one_main(argv) or 0
        finally:
            print("\n--all builds a WORKLIST instead of one bundle: one build "
                  "per cell, so one\nagent run per cell against your model "
                  "credentials.\n"
                  "  swebench-unified construct --backend <b> --all --dry-run  "
                  "# worklist + preconditions, launches nothing\n"
                  "  swebench-unified construct --backend <b> --all --help     "
                  "# the driver's flags (--limit/--only/--instances/--jobs)")
    return build_one_main(argv)


def _cmd_eval(argv: list[str]) -> int:
    from .eval.run import main as eval_main
    with _argv("swebench-unified eval", argv):
        return eval_main()


def _cmd_score(argv: list[str]) -> int:
    from .eval.score import main as score_main
    with _argv("swebench-unified score", argv):
        return score_main()


def _cmd_fetch_dataset(argv: list[str]) -> int:
    # ONE registry-driven fetch script for every benchmark (source, destination
    # and column contract come from its entry), so a port adds no dispatch here.
    # It is not on the package path; load by file.
    import importlib.util

    from .benchmarks import active
    from .paths import SCRIPTS_ROOT
    spec = importlib.util.spec_from_file_location(
        "swebench_unified._fetch_dataset", SCRIPTS_ROOT / "fetch_dataset.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # default to the active benchmark; --benchmark/-h go straight through.
    return mod.main(argv or ["--benchmark", active().name])


def _cmd_gates(argv: list[str]) -> int:
    # The backend names come from the registry, so a port needs no edit here (and
    # a second hand-written list cannot go stale against it).
    from .backends import BACKENDS
    ap = argparse.ArgumentParser(
        prog="swebench-unified gates",
        description="re-run gate subsets on existing bundles")
    ap.add_argument("--backend", required=True, choices=sorted(BACKENDS))
    ap.add_argument("instances", nargs="+", metavar="ID")
    ap.add_argument("--gates", nargs="*", default=None,
                    help="explicit gate names, space- or comma-separated "
                         "(default: all mechanical)")
    ap.add_argument("--static-only", action="store_true")
    ap.add_argument("--docker-only", action="store_true")
    ap.add_argument("--mode", choices=["feedback", "strict"], default="strict")
    ap.add_argument("--no-record", action="store_true",
                    help="don't write verdicts into the bundle's meta.json")
    args = ap.parse_args(argv)

    from .gates import ALL_GATES, DOCKER_GATES, STATIC_GATES, run_gates
    if args.gates:
        names = list(args.gates)
    elif args.static_only:
        names = list(STATIC_GATES)
    elif args.docker_only:
        names = list(DOCKER_GATES)
    else:
        names = list(ALL_GATES)

    worst = 0
    for iid in args.instances:
        start = time.monotonic()
        results = run_gates(iid, args.backend, names, mode=args.mode,
                            record=not args.no_record)
        elapsed = round(time.monotonic() - start, 1)
        blocked = any(r.status in ("fail", "error") for r in results)
        status = ("blocked" if blocked else
                  "timeout" if any(r.status == "timeout" for r in results) else "ok")
        print(f"[{iid}] {status} ({elapsed}s): "
              + " ".join(f"{r.gate}={r.status}" for r in results))
        for r in results:
            if not r.ok:
                print(f"    {r.gate}: {r.detail}")
        if blocked:
            worst = 1
    return worst


_COMMANDS = {
    "construct": (_cmd_construct,
                  "build one bundle (--backend --instance) or every instance (--all)"),
    "eval": (_cmd_eval, "frontier-model evaluation harness (eval/run.py flags)"),
    "score": (_cmd_score, "mechanical consumer scorer (eval/score.py flags)"),
    "gates": (_cmd_gates, "re-run gate subsets on existing bundles"),
    "fetch-dataset": (_cmd_fetch_dataset,
                      "download + freeze a benchmark (default SBU_BENCHMARK) into data/"),
}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    argv = _extract_benchmark_dir(argv)
    ap = argparse.ArgumentParser(
        prog="swebench-unified",
        description="unified verified-SWE-bench pipeline (see docs/architecture.md)",
        epilog="run `swebench-unified <command> --help` for command flags")
    ap.add_argument("--benchmark-dir", metavar="NAME_OR_PATH",
                    help="constructed-bundle root (default: benchmark/; a bare "
                         "name is under the project root). Sets SBU_BENCHMARK_DIR.")
    ap.add_argument("command", choices=sorted(_COMMANDS),
                    help="; ".join(f"{k}: {v[1]}" for k, v in _COMMANDS.items()))
    ap.add_argument("args", nargs=argparse.REMAINDER)
    if not argv:
        ap.print_help()
        return 2
    ns = ap.parse_args(argv[:1])
    handler = _COMMANDS[ns.command][0]
    return handler(argv[1:])


if __name__ == "__main__":
    sys.exit(main())

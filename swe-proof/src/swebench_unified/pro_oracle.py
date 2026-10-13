# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""SWE-bench Pro in-container resolve oracle (G-RESOLVE for resolve_style="pro").

Pro does not use the `swebench` pip harness: it ships its own images
(jefzda/sweap-images:<dockerhub_tag>, repo at /app) and grades a candidate by
running pytest over the row's selected test files, then checking every
FAIL_TO_PASS and PASS_TO_PASS test passes. This module reproduces that model
behind the same `run_resolve(...) -> ResolveResult` interface the Verified path
uses, so G-RESOLVE, the construction loop, and the flaky-retry logic are
unchanged.

Per-instance execution (faithful to Pro's entryscript.sh):
  cd /app
  <before_repo_set_cmd>   # reset --hard base; clean; checkout base;
                          # checkout <fix_commit> -- <test files>  (restores
                          # the reference test files — Pro ignores test_patch)
  git apply /work/patch.diff       (the candidate)
  <pytest wrapper> -v <selected_test_files_to_run>

The candidate patch is applied AFTER the base reset but the test-file checkout
(last line of before_repo_set_cmd) runs after that, so it overwrites any test
files the candidate touched with the reference versions — matching Pro.

Grading: parse `<nodeid> PASSED|FAILED|...` from pytest -v; resolved iff
(FAIL_TO_PASS ∪ PASS_TO_PASS) ⊆ {nodeids that PASSED}. XFAIL→PASSED, XPASS→FAILED
(Pro's convention). A test that never appears in the output is NOT passed.
"""
from __future__ import annotations

import json
import re
import shlex

from .docker_exec import _sg_docker, ensure_image, image_name
from .harness import ResolveResult

# pytest -v line: "path/to/test.py::Class::test_x[param] PASSED [ 42%]". The
# nodeid may contain spaces inside a `[param]` (e.g. a parametrize id like
# `test_str[False-False-<no find flags>]`), so its BODY is matched with `.+?`
# (not `\S+`, which truncates at the first space and drops the result). The
# leading path token before the first `::` stays `\S+` so a prefixed noise/
# summary line (`FAILED path::test - msg`, `INFO path::test PASSED`) cannot be
# read as a nodeid — a real result line always begins with the nodeid. The
# status is terminated by a word boundary (tolerating pytest trailers like
# `[ 42%]` or `SKIPPED (reason)`), and the non-greedy body stops at the first
# ` <STATUS>` since parametrize ids never contain a bare status word.
_RESULT_RE = re.compile(
    r"^(?P<nodeid>\S+::.+?)\s+(?P<status>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b")

_PASS_STATUSES = {"PASSED", "XFAIL"}   # Pro maps XFAIL->pass, XPASS->fail

# repos needing a display/session wrapper around pytest (qutebrowser is a GUI
# app: offscreen Qt + a dbus session under a virtual X server).
# QTWEBENGINE_DISABLE_SANDBOX=1: QtWebEngine's Chromium renderer cannot start
# its setuid/namespace sandbox inside an unprivileged container and SIGSEGVs on
# the first webengine test, aborting pytest before it emits the RC marker --
# independent of any candidate patch. Disabling the sandbox is the standard
# container workaround and does not change any test's pass/fail semantics.
# -o addopts="": qutebrowser's pytest.ini sets `addopts = --strict …` with
# `filterwarnings = error`; the image's pytest 7.4.2 escalates the --strict
# deprecation (PytestRemovedIn8Warning) into a config-time crash before any
# test runs (rc=1, zero result lines). Neutralize the repo addopts — our
# explicit flags already provide the verbosity the parser needs.
# ansible/ansible: reproduces how ansible's own unit-test runner (`ansible-test
# units`) grades -- the environment the Pro FAIL_TO_PASS/PASS_TO_PASS baselines
# were recorded under, without which even the GOLD patch grades not-resolved:
#   (1) --forked (pytest-forked; ansible-test units passes `--boxed` per
#       test/lib/ansible_test/_internal/units/__init__.py): several
#       selected test files must run in ONE pytest process (Pro concatenates
#       `selected_test_files_to_run`). test_collection_loader.py installs a
#       process-global AnsibleCollectionFinder that then breaks test_galaxy.py's
#       setUpClass with `NotImplementedError: an AnsibleCollectionFinder has not
#       been installed in this process` — pure cross-file state pollution.
#       Per-process isolation is exactly ansible-test's `--boxed`; it changes no
#       single test's pass/fail semantics (a single-file bundle grades
#       identically with and without it).
#       CONDITIONAL: pytest-forked is NOT shipped in every ansible image —
#       the pytest>=8 generation lacks it (and pip can't fetch it offline), so
#       a hardcoded --forked makes pytest abort with exit 4
#       `unrecognized arguments: --forked` before any test runs and EVERY
#       candidate incl. gold grades as a harness error. The entryscript probes
#       `import pytest_forked` and expands $SBU_FORKED to --forked only when
#       the plugin exists. Without the plugin the worst case is cross-file
#       pollution making gold grade not-resolved (visible fail, bundle parked);
#       pollution only ADDS failures, so dropping the flag can never flip a
#       wrong candidate to a silent pass.
#   (2) ANSIBLE_DEVEL_WARNING=false: ansible-test's ansible_environment sets this
#       (test/lib/ansible_test/_internal/ansible_util.py: "Don't show warnings
#       that CI is running devel"). Without it, GalaxyCLI emits an extra
#       Display.warning ("running the development version of Ansible") on every
#       run, so the collection-install tests that assert an exact
#       `mock_warning.call_count` fail off-by-one. It suppresses only the devel
#       banner — no test's real behaviour changes. -p no:cacheprovider also
#       matches ansible-test units.
_PYTEST_WRAPPER = {
    "qutebrowser/qutebrowser":
        "QTWEBENGINE_DISABLE_SANDBOX=1 QT_QPA_PLATFORM=offscreen "
        "dbus-run-session -- xvfb-run -a "
        'python -m pytest -v --disable-warnings --benchmark-disable -o addopts=""',
    "ansible/ansible":
        "ANSIBLE_DEVEL_WARNING=false "
        "python -m pytest -v --disable-warnings -p no:cacheprovider $SBU_FORKED",
}
_DEFAULT_PYTEST = "python -m pytest -v --disable-warnings"

# Shell fragment defining $SBU_FORKED for the wrapper above: --forked iff the
# plugin is importable (see the ansible/ansible comment). Runs under `set -e`;
# an `if` condition's failure doesn't trip errexit, so the probe cannot abort.
_FORKED_PROBE = ('if python -c "import pytest_forked" 2>/dev/null; '
                 'then SBU_FORKED=--forked; else SBU_FORKED=; fi')

# Qt-wrapper probe for image drift: some qutebrowser images ship ONLY PyQt6,
# while the checked-out tree's qutebrowser/qt/machinery.py still defaults to
# PyQt5 (the image build's `sed` of _DEFAULT_WRAPPER doesn't survive the
# harness's `git reset --hard`), so conftest import dies with
# ModuleNotFoundError: PyQt5 -> pytest exit 4 for EVERY candidate incl. gold.
# machinery honours QUTE_QT_WRAPPER, so export PyQt6 exactly when PyQt5 is
# absent and PyQt6 present. No-op on PyQt5 images and on non-Qt repos (both
# imports fail -> var not set).
_QT_WRAPPER_PROBE = (
    'if ! python -c "import PyQt5" 2>/dev/null && '
    'python -c "import PyQt6" 2>/dev/null; '
    'then export QUTE_QT_WRAPPER=PyQt6; fi')


def parse_pytest(stdout: str) -> dict[str, str]:
    """{nodeid: status} from pytest -v output (last status wins if repeated)."""
    out: dict[str, str] = {}
    for line in stdout.splitlines():
        m = _RESULT_RE.match(line.strip())
        if m:
            out[m.group("nodeid")] = m.group("status")
    return out


def _collapse_slashes(s: str) -> str:
    """Collapse runs of 2+ `/` to a single `/`. Some Pro rows store required
    node-ids captured by a tool that squashed `//` to `/`, so a parametrize id
    embedding a URL is stored `https:/host/...` where pytest emits
    `https://host/...` (ansible galaxy `test_cache_id[...]`, `test_wait_import_
    task[...]`). Collapsing BOTH sides identically before comparison restores
    the match. Single slashes (path separators, single-slash URL segments) are
    untouched, so this only ever merges — never splits — and cannot introduce a
    false EXACT match between two genuinely distinct ids (they would have to
    differ ONLY by `//` vs `/`, and even then the all-PASS guard below keeps
    grading sound: a differing status blocks resolution)."""
    return re.sub(r"/{2,}", "/", s)


def _satisfied(required_id: str, results: dict[str, str]) -> bool:
    """Is `required_id` satisfied by the pytest results?

    Normal case: an exact nodeid that must have PASSED (XFAIL counts as pass).

    Slash-collapsed case: a required id whose only corruption is squashed `//`
    (see `_collapse_slashes`) matches the real result under slash-normalization.
    Satisfied iff every result whose normalized id equals the normalized
    required id PASSED (and at least one exists).

    Truncated case: some Pro rows store required ids captured by a tool that
    split on whitespace, so a parametrized id with a space inside its `[param]`
    is stored cut off mid-bracket (no closing `]`), e.g.
    `...::test_normalize_isbn[123-456-789-X` for the real
    `...::test_normalize_isbn[123-456-789-X -123456789X]`. The vendor tool can
    also drop a trailing quote/char, so the boundary after the stored prefix is
    not always the split whitespace — it may be any NON-word character (e.g.
    ansible `...content[{"de` for `...content[{"de" "finit" ...]`, boundary
    `"`). Our parser captures the FULL id, so exact match fails. Reconstruct by
    matching (under slash-normalization) only nodeids where the char right after
    the prefix is a non-word char (whitespace, quote, bracket, ...) — a
    word-char boundary (alnum / `-` / `_`) would swallow a sibling case like
    `[123-456-789-XY]` and is rejected. The truncation is lossy: two distinct
    required cases can collapse to the SAME prefix, so >1 match is expected and
    legitimate. Satisfied iff at least one such nodeid exists AND all of them
    PASSED (any FAILED case under the prefix means a required test did not
    pass). 0 matches = the required case is absent => unresolved."""
    if required_id in results:
        return results[required_id] in _PASS_STATUSES
    nreq = _collapse_slashes(required_id)
    # slash-only corruption: exact match after normalizing both sides.
    norm_exact = [st for nid, st in results.items()
                  if _collapse_slashes(nid) == nreq]
    if norm_exact:
        return all(st in _PASS_STATUSES for st in norm_exact)
    # truncated required id (mid-`[param]`, no closing bracket): reconstruct in
    # normalized space, requiring a non-word boundary so we don't match a longer
    # sibling param (`[123-X` must not match `[123-XY]`).
    if "[" in nreq and not nreq.endswith("]"):
        matches = []
        for nid, st in results.items():
            nnid = _collapse_slashes(nid)
            if nnid.startswith(nreq) and len(nnid) > len(nreq):
                bchar = nnid[len(nreq)]
                if not (bchar.isalnum() or bchar in "-_"):
                    matches.append(st)
        return bool(matches) and all(st in _PASS_STATUSES for st in matches)
    return False


def grade(results: dict[str, str], fail_to_pass: list[str],
          pass_to_pass: list[str]) -> tuple[bool, dict]:
    """resolved iff every F2P and P2P nodeid PASSED. Returns (resolved, detail).

    Node-ids are matched via `_satisfied`, which handles both exact ids and the
    whitespace-truncated parametrize ids some Pro rows ship."""
    f2p_missing = [t for t in fail_to_pass if not _satisfied(t, results)]
    p2p_missing = [t for t in pass_to_pass if not _satisfied(t, results)]
    missing = f2p_missing + p2p_missing
    required = list(fail_to_pass) + list(pass_to_pass)
    resolved = not missing
    detail = {
        "n_required": len(required),
        "n_passed_required": len(required) - len(missing),
        "f2p_failing": f2p_missing[:8],
        "p2p_failing": p2p_missing[:8],
        "n_tests_seen": len(results),
    }
    return resolved, detail


def _decode_list(v) -> list[str]:
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.strip():
        return json.loads(v)
    return []


# entryscript sentinels. The candidate patch failing to apply is a real
# "not resolved" verdict (not a harness error); the pytest exit code is emitted
# so grading can require a clean pytest run (exit 0/1) and never grade resolved
# off a collection/usage abort (exit 2-5) whose stdout happens to carry PASSED
# lines.
PATCH_APPLY_FAILED = "SBU_PRO_PATCH_APPLY_FAILED"
_RC_MARKER = "SBU_PRO_PYTEST_RC="
_RC_RE = re.compile(rf"^{re.escape(_RC_MARKER)}(\d+)$", re.M)


def _validate_test_files(files: list[str]) -> None:
    """Reject anything that isn't a plain path — a `-k`/`--maxfail` entry would
    change what pytest collects. Belt-and-braces with the `--` separator."""
    for f in files:
        if not isinstance(f, str) or f.startswith("-") or not f.strip():
            raise ValueError(f"bad selected test file {f!r}")


def _sanitize_test_files(files: list[str]) -> list[str]:
    """Collapse vendor-truncated node-id selectors to their file path.

    A Pro row may store full pytest NODE-IDS in `selected_test_files_to_run`
    with some cut off at the first whitespace inside `[param]` (no closing `]`)
    — the same vendor truncation `_satisfied` handles on the GRADING side.
    Passed verbatim to pytest they are malformed selectors: `ERROR: not found`
    per entry, exit 4 (usage error), so every candidate incl. gold grades as a
    harness error. Selecting the whole FILE instead runs a superset of the
    intended cases, which is sound here: grading only reads the statuses of the
    row's required F2P/P2P ids (and a superset can only surface MORE failures,
    never hide one).

    When a file has ANY truncated selector, ALL its node-id selectors collapse
    to the one file entry — mixing `f.py::intact_id` with a bare `f.py` makes
    pytest's collection dedupe keep only the node-id picks, so the required
    truncated cases would never execute and gold would grade not-resolved.
    Files with only intact balanced node-ids keep them verbatim. Dedupes, keeps
    first-appearance order."""
    truncated_files = {f.split("::", 1)[0] for f in files
                       if "::" in f and f.count("[") != f.count("]")}
    out: list[str] = []
    for f in files:
        base = f.split("::", 1)[0]
        if base in truncated_files:
            f = base
        if f not in out:
            out.append(f)
    return out


def _widen_to_required(files: list[str], required: list[str]) -> list[str]:
    """Collapse a file's node-id selectors to the bare file when the selection
    does not cover every required (F2P/P2P) id in that file.

    A Pro row may select fewer node-ids from a file than grading requires from
    it; the uncovered required ids then never RUN, so every candidate incl. gold
    grades as required tests not passing. Running the whole file is a sound
    superset for the same reason as the truncation collapse above: grading reads
    only the required ids' statuses, and extra tests can only surface more
    failures, never hide one. Selections that already cover their required ids
    are returned unchanged."""
    bare = {f for f in files if "::" not in f}
    selids = set(files)
    widen = {r.split("::", 1)[0] for r in required
             if r.split("::", 1)[0] not in bare and r not in selids}
    if not widen:
        return files
    out: list[str] = []
    for f in files:
        base = f.split("::", 1)[0]
        if base in widen:
            f = base
        if f not in out:
            out.append(f)
    # a required file absent from the selection entirely (no selector to
    # collapse) must still be ADDED, or its required ids silently never run
    # (no current Pro row hits this — defensive)
    for base in sorted(widen):
        if base not in out:
            out.append(base)
    return out


REINSTALL_FAILED = "SBU_PRO_REINSTALL_FAILED"


def _entryscript(row: dict, workdir: str) -> str:
    pro = row.get("pro") or {}
    before = (pro.get("before_repo_set_cmd") or "").strip()
    test_files = _sanitize_test_files(_decode_list(pro.get("selected_test_files_to_run")))
    test_files = _widen_to_required(
        test_files, _decode_list(row.get("FAIL_TO_PASS"))
        + _decode_list(row.get("PASS_TO_PASS")))
    _validate_test_files(test_files)
    pytest_cmd = _PYTEST_WRAPPER.get(row["repo"], _DEFAULT_PYTEST)
    files = " ".join(shlex.quote(f) for f in test_files)
    wd = shlex.quote(workdir)
    # top-level import name for the stale-import probe (all three Pro repos'
    # package == the repo basename: ansible, openlibrary, qutebrowser)
    pkg = row["repo"].rsplit("/", 1)[-1].replace("-", "_")
    # `before` (reset base + restore reference test files) must succeed — a
    # failure there is a harness/env error (`set -e` aborts, no RC marker). The
    # candidate `git apply` is allowed to fail: emit a sentinel and skip pytest
    # so a non-applying candidate grades as not-resolved, not a harness error.
    #
    # CRITICAL: after the patch applies to the source tree we MUST make `import
    # <pkg>` resolve to that patched tree, or pytest silently imports the STALE
    # package `build.sh` `pip install`ed into site-packages and every candidate
    # (even gold) grades not-resolved. Two Pro install shapes:
    #   - non-editable `pip install .` (e.g. ansible, whose package lives at
    #     /app/lib/ansible so PYTHONPATH=/app alone does NOT expose it) — the
    #     patched tree is only picked up after a reinstall;
    #   - editable `pip install -e .` (e.g. qutebrowser) — already reflects /app.
    # A best-effort editable reinstall (`--no-build-isolation --no-deps`, offline
    # + fast: no build sandbox, deps already present) covers the first shape and
    # is a cheap no-op for the second; PYTHONPATH=/app covers repos that import
    # straight from the worktree root (e.g. openlibrary). Reinstall failure is a
    # harness/env error (sentinel, no RC marker) — never a silent stale-import
    # pass. `-- {files}` stops pytest treating a path as an option; the RC marker
    # lets grading require a clean pytest exit.
    # --use-pep517: without it, pip's LEGACY editable path (`setup.py develop`)
    # internally re-execs `pip install -e . --use-pep517 --no-deps` WITHOUT our
    # --no-build-isolation, so that subprocess tries to fetch setuptools from
    # the image's dead localhost index (127.0.0.1:9876) and the reinstall fails.
    # Passing --use-pep517 at top level keeps the build in-process where
    # --no-build-isolation applies.
    # Reinstall failure is only FATAL when it leaves a stale-import risk: some
    # openlibrary images cannot build editable metadata at all (setup.py
    # imports Cython, absent from the image), yet openlibrary is NOT
    # pip-installed there — imports already resolve from the patched worktree
    # via PYTHONPATH, so no stale copy exists and the sentinel would falsely
    # error every candidate incl. gold. On reinstall failure we probe where the
    # repo's top-level package actually imports from (under PYTHONPATH={wd}):
    # inside the worktree => patched code is what tests will see, proceed;
    # anywhere else (a surviving site-packages copy) => the original
    # stale-import hazard, emit the sentinel.
    #
    # errexit stays ON through setup (a `before`/env failure must abort with no
    # RC marker => harness error, not a not-resolved verdict). The two commands
    # that are ALLOWED to fail with a specific verdict use explicit `if !`
    # guards, so errexit need not be disabled for them. Only pytest itself runs
    # under `set +e`, since a nonzero pytest rc (tests failed) is a real graded
    # outcome, not an abort — and we capture that rc explicitly.
    # stale-import probe (run under PYTHONPATH={wd}): where does the package
    # import from? Prints the module's file path, empty on ImportError.
    probe = (f'PYTHONPATH={wd} python -c "import {pkg}; '
             f'print({pkg}.__file__)" 2>/dev/null || true')
    return "\n".join([
        "set -e",
        f"cd {wd}",
        before,
        f"if ! git apply -v /work/patch.diff; then echo {PATCH_APPLY_FAILED}; exit 0; fi",
        f"if ! python -m pip install -e {wd} --use-pep517 --no-build-isolation "
        f"--no-deps -q; then",
        # reinstall failed: only fatal if imports would hit a stale copy
        # OUTSIDE the worktree (see comment above). case pattern {wd}/* =>
        # imports resolve inside the patched tree, safe to proceed.
        f'  SBU_PKG_FILE=$({probe})',
        f'  case "$SBU_PKG_FILE" in {workdir}/*) : ;; *) '
        f"echo {REINSTALL_FAILED}; exit 0;; esac",
        "fi",
        # The editable reinstall can build_ext IN PLACE from the image's stale
        # pre-generated C sources, dropping a compiled .so beside a module the
        # candidate patched — Python then imports the stale .so, silently
        # shadowing the patched .py (measured 2026-08-18 on openlibrary-7bf32385:
        # update_work.cpython-311.so appears only AFTER the reinstall and grades
        # the GOLD patch not-resolved, 18/43; the probe above cannot see it
        # because the package ROOT still resolves in the worktree). Remove any
        # in-tree extension module that shadows a same-name .py; compiled-only
        # extensions (no adjacent .py) are left alone.
        f'find {wd} -name "*.cpython-*.so" -o -name "*.pyd" | '
        'while read -r so; do sopy="${so%%.cpython-*}.py"; '
        '[ -f "$sopy" ] && rm -f "$so"; done || true',
        f"export PYTHONPATH={wd}:$PYTHONPATH",
        _FORKED_PROBE,
        _QT_WRAPPER_PROBE,
        "set +e",
        f"{pytest_cmd} -- {files}",
        "rc=$?",
        "set -e",
        f'echo "{_RC_MARKER}$rc"',
    ])


def _run_once(instance_id: str, patch: str, row: dict, timeout: int) -> ResolveResult:
    import tempfile
    from pathlib import Path

    from .benchmarks import active
    bench = active()
    err = ensure_image(instance_id)
    if err:
        return ResolveResult(False, False, instance_id, {}, err)
    canonical = image_name(instance_id, row)
    work = Path(tempfile.mkdtemp(prefix=f"sbu_pro_{instance_id[:24]}_", dir="/tmp"))
    try:
        (work / "patch.diff").write_text(patch if patch.endswith("\n") else patch + "\n")
        script = _entryscript(row, bench.container_workdir)
        (work / "entryscript.sh").write_text(script)
        # Pro images set ENTRYPOINT [/bin/bash]; override it so our script path
        # isn't appended as an arg to a bash-running-bash.
        docker_args = [
            "run", "--rm", "-v", f"{work}:/work:ro",
            "--entrypoint", "/bin/bash",
            canonical, "/work/entryscript.sh",
        ]
        try:
            r = _sg_docker(docker_args, timeout=timeout)
        except Exception as e:  # includes TimeoutExpired
            name = type(e).__name__
            if name == "TimeoutExpired":
                return ResolveResult(False, False, instance_id, {},
                                     f"pro harness timed out ({timeout}s)")
            return ResolveResult(False, False, instance_id, {},
                                 f"pro harness error: {name}: {e}")
        stdout = r.stdout or ""
        # candidate patch didn't apply: a real not-resolved verdict (completed),
        # not a harness error.
        if PATCH_APPLY_FAILED in stdout:
            return ResolveResult(False, True, instance_id,
                                 {"patch_applied": False},
                                 "candidate patch did not apply")
        # reinstall of the patched tree failed: a harness/env error (completed=
        # False), NEVER a silent not-resolved off the stale installed package.
        if REINSTALL_FAILED in stdout:
            tail = ((r.stderr or "")[-400:] or stdout[-400:]).strip()
            return ResolveResult(False, False, instance_id, {"stderr_tail": tail},
                                 "pro harness could not reinstall the patched tree")
        # Require a clean pytest exit. pytest: 0=all passed, 1=tests failed,
        # 2=interrupted, 3=internal error, 4=usage, 5=no tests collected. Only
        # 0/1 are real test outcomes; 2-5 are incomplete — never grade resolved
        # off an aborted run whose stdout happens to carry PASSED lines.
        rc_m = _RC_RE.search(stdout)
        if rc_m is None:
            tail = ((r.stderr or "")[-400:] or stdout[-400:]).strip()
            return ResolveResult(False, False, instance_id, {"stderr_tail": tail},
                                 "pro harness did not reach pytest (setup error)")
        pytest_rc = int(rc_m.group(1))
        if pytest_rc not in (0, 1):
            tail = ((r.stderr or "")[-400:] or stdout[-400:]).strip()
            return ResolveResult(False, False, instance_id,
                                 {"pytest_rc": pytest_rc, "stderr_tail": tail},
                                 f"pytest did not complete (exit {pytest_rc}: "
                                 "collection/usage/internal error)")
        fail_to_pass = _decode_list(row.get("FAIL_TO_PASS"))
        pass_to_pass = _decode_list(row.get("PASS_TO_PASS"))
        results = parse_pytest(stdout)
        if not results:
            tail = ((r.stderr or "")[-400:] or stdout[-400:]).strip()
            return ResolveResult(False, False, instance_id,
                                 {"stderr_tail": tail, "pytest_rc": pytest_rc},
                                 "pro harness produced no parseable pytest output")
        resolved, detail = grade(results, fail_to_pass, pass_to_pass)
        detail["pytest_rc"] = pytest_rc
        return ResolveResult(
            resolved, True, instance_id, detail,
            "resolved" if resolved else
            f"{len(detail['f2p_failing']) + len(detail['p2p_failing'])} "
            "required test(s) not passing")
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)


def run_resolve_pro(instance_id: str, patch: str, row: dict, *,
                    timeout: int = 3600, retries: int = 2) -> ResolveResult:
    """Pro G-RESOLVE with the same resolved-on-any-attempt flaky policy as the
    Verified path."""
    last = _run_once(instance_id, patch, row, timeout)
    if last.resolved or not last.completed or retries <= 0:
        return last
    saw_resolved = False
    n = 1
    for k in range(1, retries + 1):
        n += 1
        attempt = _run_once(instance_id, patch, row, timeout)
        if attempt.resolved:
            attempt.attempts = n
            attempt.flaky = True
            attempt.note = f"resolved on retry {k}/{retries} (flaky)"
            return attempt
        if not attempt.completed:
            attempt.attempts = n
            return attempt
        last = attempt
    last.attempts = n
    last.flaky = saw_resolved
    last.note = f"required tests not passing in {n} attempts (consistent)"
    return last

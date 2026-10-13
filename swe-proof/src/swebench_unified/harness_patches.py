# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Documented, minimal runtime patches for `swebench==4.1.0`.

Each fixes a HARNESS/ENVIRONMENT defect with upstream provenance; none changes
what any task requires. Differential behavior was re-verified for each:
FAIL_TO_PASS still fails at base_commit and passes with the gold patch.

PATCH 1 — backport of upstream fix #518 (unreleased as of 4.1.0): when a
test_patch only ADDS test files, get_modified_files() returns [] and the eval
script's reset degenerates to a bare `git checkout <base_commit>`, undoing
image-setup modifications (e.g. sphinx's `pytest -rA` sed) so a passing gold
patch grades unresolved. Affects the 3 new-file-only instances
(django-16877, sphinx-8595, sphinx-9711; the two sphinx ones misgrade).
Replicates upstream verbatim: checkout modified files, `rm -f` new files,
never a bare checkout.

PATCH 2 — dataset corrections from SWE-bench maintainers (branch
`fix/verified-dataset`, commits 50b9f47/c6d4cfa, issues #505/#487), applied
at dataset load:
- astropy__astropy-7606 (#505): P2P names `test_compose_roundtrip[]` but
  pytest renders the id as `[unit0]`; the test passes under its real name.
  Rename it.
- django__django-10097 (#487): the discriminating tests are the 6
  `test_URLValidator_raises_error_*` entries from the test_patch; add them to
  FAIL_TO_PASS (strictly STRONGER acceptance, verified in our run logs).
- django__django-10097 P2P: 5 generic_inline_admin tests ERROR identically at
  base and with gold (measured, deterministic) — earlier tests leak
  ROOT_URLCONF into their settings, patch-independent isolation breakage in
  the rebuilt 2025 image. A test failing at base cannot be PASS_TO_PASS;
  exclude the 5 (the other 1427 stay enforced).

PATCH 3 — per-instance environment repairs (upstream issue #484, astropy 3.1's
2019-era pins vs the 2025-rebuilt images):
- astropy__astropy-8872: collection dies (LooseVersion DeprecationWarning
  under setuptools-68 escalated to a collection error);
  SETUPTOOLS_USE_DISTUTILS=stdlib restores it.
- astropy__astropy-8707: pytest 7.4 nose-deprecation warnings error every
  test setup; ignoring DeprecationWarning restores execution.
Exports appended to the eval script for exactly these two instance_ids; test
assertions untouched.

PATCH 5 — a suite that drives a live HTTP service is pointed at a local copy of
it (see oracle_services). psf/requests' suite talks to httpbin, and when the
public host answers 503 every one of those tests fails whatever is applied,
reproducibly so for a patch that changes no source. The suite's own HTTPBIN_URL
override is what is used, so the same assertions run against the same service;
only the third party's uptime leaves the verdict.

PATCH 6 — an evaluation container is given a CPU quota. Upstream creates it with
no limit, so a suite that sizes its thread pool from the host CPU count takes the
whole machine, and every other process on it then runs against its wall clock and
records a timeout — which reads downstream as evidence about a specification when
it is evidence about the machine. A quota cannot change what a test decides: it
is a cgroup bandwidth limit and leaves `sched_getaffinity` alone, so the suite
still sizes its pool from the same CPU count and every reduction runs over the
same number of threads in the same order. (A cpuset would NOT be safe here — it
changes the visible CPU count, and with it the thread count and the order of
floating-point reductions.) Quota only costs wall clock, and only for a container
that wanted more than its share.

PATCH 4 (a network-flaky linkcheck P2P exclusion) and PATCH 5b (the one
assertion a local service instance cannot grade) are documented inline at the
tables that configure them, below.

Import this module BEFORE building test specs (see run_evaluation.py).
"""
from __future__ import annotations

import json
import os

from unidiff import PatchSet

import swebench.harness.docker_build as _docker_build
import swebench.harness.run_evaluation as _run_evaluation
import swebench.harness.test_spec.create_scripts as _create_scripts
import swebench.harness.test_spec.python as _python
import swebench.harness.utils as _utils
from swebench.harness.constants import MAP_REPO_VERSION_TO_SPECS
from swebench.harness.test_spec.python import (
    get_modified_files,
    get_test_directives,
)

from .oracle_services import service_env_lines

_HEREDOC_DELIMITER = "EOF_114329324912"
_START_TEST_OUTPUT = ">>>>> Start Test Output"
_END_TEST_OUTPUT = ">>>>> End Test Output"


# --- PATCH 2: dataset corrections (upstream issues #505, #487) -------------

def _fix_7606_p2p(p2p: list[str]) -> list[str]:
    return [
        t.replace("test_compose_roundtrip[]", "test_compose_roundtrip[unit0]")
        for t in p2p
    ]


def _fix_10097_f2p(f2p: list[str]) -> list[str]:
    return f2p + [
        f"test_URLValidator_raises_error_{n} (validators.tests.TestSimpleValidators)"
        for n in range(352, 358)
    ]


_10097_ENV_BROKEN_P2P = {
    "test_add (generic_inline_admin.tests.GenericInlineAdminWithUniqueTogetherTest)",
    "test_delete (generic_inline_admin.tests.GenericInlineAdminWithUniqueTogetherTest)",
    "test_no_param (generic_inline_admin.tests.GenericInlineAdminParametersTest)",
    "test_basic_add_GET (generic_inline_admin.tests.GenericAdminViewTest)",
    "test_basic_edit_GET (generic_inline_admin.tests.GenericAdminViewTest)",
}


def _fix_10097_p2p(p2p: list[str]) -> list[str]:
    return [t for t in p2p if t not in _10097_ENV_BROKEN_P2P]


# PATCH 4 — network-flaky linkcheck P2P exclusion. sphinx-8269/-8475 carry
# test_defaults / test_defaults_json in PASS_TO_PASS; neither is touched by
# the test_patch, and both assert exact response strings from LIVE external
# URLs that return non-deterministic results in the eval sandbox, failing
# patch-independently (the F2P fix tests PASS with gold in both cases). A
# verdict governed by live-internet weather cannot be a deterministic P2P;
# exclude the two (same shape as PATCH 2's #487 exclusion).
_LINKCHECK_NETWORK_FLAKY_P2P = {
    "tests/test_build_linkcheck.py::test_defaults",
    "tests/test_build_linkcheck.py::test_defaults_json",
}


def _drop_linkcheck_flaky_p2p(p2p: list[str]) -> list[str]:
    return [t for t in p2p if t not in _LINKCHECK_NETWORK_FLAKY_P2P]


# PATCH 5b — the one assertion a LOCAL service instance cannot grade.
# psf/requests' test_mixed_case_scheme_acceptable re-addresses the httpbin host
# under eight scheme spellings, four of them https, reusing `parts.netloc` from
# HTTPBIN_URL. The public host answers both schemes on their default ports, so
# netloc carries no port and https reaches the TLS listener; a local instance is
# one server on one port, so the four https spellings cannot be answered whatever
# the patch does. Excluded for the same reason PATCH 4 excludes the linkcheck pair
# -- it is not grading the patch. Repo-keyed: the assertion is the suite's, not one
# instance's.
_LOCAL_SERVICE_UNGRADABLE_P2P = {
    "test_requests.py::RequestsTestCase::test_mixed_case_scheme_acceptable",
}


def _drop_local_service_ungradable_p2p(p2p: list[str]) -> list[str]:
    return [t for t in p2p if t not in _LOCAL_SERVICE_UNGRADABLE_P2P]


REPO_CORRECTIONS = {
    "psf/requests": {"PASS_TO_PASS": _drop_local_service_ungradable_p2p},
}

DATASET_CORRECTIONS = {
    "astropy__astropy-7606": {"PASS_TO_PASS": _fix_7606_p2p},
    "django__django-10097": {
        "FAIL_TO_PASS": _fix_10097_f2p,
        "PASS_TO_PASS": _fix_10097_p2p,
    },
    "sphinx-doc__sphinx-8269": {"PASS_TO_PASS": _drop_linkcheck_flaky_p2p},
    "sphinx-doc__sphinx-8475": {"PASS_TO_PASS": _drop_linkcheck_flaky_p2p},
}


def _apply_dataset_corrections(dataset: list[dict]) -> list[dict]:
    out = []
    for row in dataset:
        # Repo-wide first, then this instance's own: both APPLY, they do not
        # override each other. An instance-keyed fix replacing a repo-keyed one
        # for the same field would silently un-exclude a test the suite cannot
        # grade, and nothing downstream would say so.
        fixes: dict[str, list] = {}
        for layer in (REPO_CORRECTIONS.get(row.get("repo", ""), {}),
                      DATASET_CORRECTIONS.get(row.get("instance_id", ""), {})):
            for field, fn in layer.items():
                fixes.setdefault(field, []).append(fn)
        if fixes:
            row = dict(row)
            for field, fns in fixes.items():
                val = row[field]
                as_str = isinstance(val, str)
                lst = json.loads(val) if as_str else list(val)
                for fn in fns:
                    lst = fn(lst)
                row[field] = json.dumps(lst) if as_str else lst
        out.append(row)
    return out


_orig_load = _utils.load_swebench_dataset


def load_swebench_dataset_corrected(*args, **kwargs):
    return _apply_dataset_corrections(_orig_load(*args, **kwargs))


# --- PATCH 3: per-instance environment repairs (upstream issue #484) -------

EVAL_ENV_REPAIRS = {
    "astropy__astropy-8872": ["export SETUPTOOLS_USE_DISTUTILS=stdlib"],
    "astropy__astropy-8707": [
        'export PYTEST_ADDOPTS="-p warnings -W ignore::DeprecationWarning"'
    ],
}


def get_new_files(patch: str) -> list[str]:
    """Files a patch creates (source is /dev/null). From upstream #518."""
    new_files = []
    for file in PatchSet(patch):
        if file.source_file == "/dev/null":
            target = file.target_file
            if target.startswith("b/"):
                target = target[2:]
            new_files.append(target)
    return new_files


def make_eval_script_list_py(
    instance, specs, env_name, repo_directory, base_commit, test_patch
) -> list:
    """swebench 4.1.0's make_eval_script_list_py + upstream fix #518 (PATCH 1)
    + per-instance env repairs (PATCH 3)."""
    modified_files = get_modified_files(test_patch)
    new_files = get_new_files(test_patch)
    reset_commands = []
    if modified_files:
        reset_commands.append(f"git checkout {base_commit} {' '.join(modified_files)}")
    if new_files:
        reset_commands.append(f"rm -f {' '.join(new_files)}")
    apply_test_patch_command = (
        f"git apply -v - <<'{_HEREDOC_DELIMITER}'\n{test_patch}\n{_HEREDOC_DELIMITER}"
    )
    test_command = " ".join(
        [
            MAP_REPO_VERSION_TO_SPECS[instance["repo"]][instance["version"]][
                "test_cmd"
            ],
            *get_test_directives(instance),
        ]
    )
    eval_commands = [
        "source /opt/miniconda3/bin/activate",
        f"conda activate {env_name}",
        f"cd {repo_directory}",
    ]
    eval_commands += EVAL_ENV_REPAIRS.get(instance["instance_id"], [])
    # PATCH 5: point suites that drive a live HTTP service at a local one, so a
    # third-party outage cannot decide the verdict. No-op for every repo that
    # needs nothing, and for any service that fails to start.
    eval_commands += service_env_lines(instance)
    if "eval_commands" in specs:
        eval_commands += specs["eval_commands"]
    eval_commands += [
        f"git config --global --add safe.directory {repo_directory}",
        f"cd {repo_directory}",
        "git status",
        "git show",
        f"git -c core.fileMode=false diff {base_commit}",
        "source /opt/miniconda3/bin/activate",
        f"conda activate {env_name}",
    ]
    if "install" in specs:
        eval_commands.append(specs["install"])
    eval_commands += [
        *reset_commands,
        apply_test_patch_command,
        f": '{_START_TEST_OUTPUT}'",
        test_command,
        f": '{_END_TEST_OUTPUT}'",
        *reset_commands,
    ]
    return eval_commands


# --- PATCH 6: a CPU quota for the evaluation container ---------------------

CPU_PERIOD = 100_000  # microseconds; the cgroup default
_orig_build_container = _docker_build.build_container


def resolve_cpu_quota() -> int:
    """CPU quota for one evaluation container, in `CPU_PERIOD` microseconds.

    `SBU_RESOLVE_CPUS` is the limit in cores and `0` turns the cap off. The
    default is a quarter of the machine's cores, floored at 8: enough that no
    single evaluation container can starve the concurrent verifiers and resolves
    (PATCH 6), and self-disabling on a small machine, since a quota at or above
    the core count is not a limit at all.
    """
    raw = os.environ.get("SBU_RESOLVE_CPUS", "").strip()
    if raw:
        cores = float(raw)
    else:
        cores = max(8.0, (os.cpu_count() or 8) / 4.0)
    return 0 if cores <= 0 else int(cores * CPU_PERIOD)


def build_container(*args, **kwargs):
    """`build_container` + a CPU quota (PATCH 6).

    Applied by updating the created container rather than by re-implementing
    upstream's create call, which would have to be kept in step with its image
    build/pull branches. `build_container` returns the container CREATED and not
    yet started, and an update at that point is written to its host config, so
    the limit is in force for the whole run.
    """
    container = _orig_build_container(*args, **kwargs)
    quota = resolve_cpu_quota()
    if container is not None and quota:
        try:
            container.update(cpu_period=CPU_PERIOD, cpu_quota=quota)
        except Exception:
            # A host whose cgroup does not support bandwidth control still runs
            # the evaluation; it just runs it unbounded, as upstream does.
            pass
    return container


def apply() -> None:
    """Install the patches into the imported swebench modules.

    load_swebench_dataset is rebound at its SOURCE (swebench.harness.utils) so
    later imports — including the fresh `__main__` copy runpy executes in our
    wrapper — pick up the corrected function; the already-imported
    run_evaluation module is rebound directly."""
    _python.make_eval_script_list_py = make_eval_script_list_py
    # create_scripts binds the symbol at import time; rebind there too.
    _create_scripts.make_eval_script_list_py = make_eval_script_list_py
    _utils.load_swebench_dataset = load_swebench_dataset_corrected
    _run_evaluation.load_swebench_dataset = load_swebench_dataset_corrected
    _docker_build.build_container = build_container
    _run_evaluation.build_container = build_container


apply()

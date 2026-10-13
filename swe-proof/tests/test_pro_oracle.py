# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""SWE-bench Pro resolve oracle — pure-function tests (no Docker/network)."""
from __future__ import annotations

from swebench_unified import pro_oracle
from swebench_unified.benchmarks import REGISTRY


PYTEST_OUT = """\
============================= test session starts ==============================
collected 4 items

test/units/utils/test_vars.py::TestVariableUtils::test_combine_vars_replace PASSED [ 25%]
test/units/utils/test_vars.py::TestVariableUtils::test_combine_vars_merge PASSED [ 50%]
test/units/utils/test_vars.py::TestVariableUtils::test_old_behavior FAILED [ 75%]
test/units/utils/test_vars.py::TestVariableUtils::test_skipped SKIPPED [100%]
=========================== short test summary info ============================
"""


def test_parse_pytest():
    r = pro_oracle.parse_pytest(PYTEST_OUT)
    assert (r["test/units/utils/test_vars.py::TestVariableUtils::test_combine_vars_replace"]
            == "PASSED")
    assert r["test/units/utils/test_vars.py::TestVariableUtils::test_old_behavior"] == "FAILED"
    assert r["test/units/utils/test_vars.py::TestVariableUtils::test_skipped"] == "SKIPPED"
    assert len(r) == 4


def test_parse_xfail_xpass():
    out = ("pkg/t.py::a XFAIL [ 50%]\n"
           "pkg/t.py::b XPASS [100%]\n")
    r = pro_oracle.parse_pytest(out)
    assert r["pkg/t.py::a"] == "XFAIL" and r["pkg/t.py::b"] == "XPASS"


def test_parse_nodeid_with_spaces_in_param():
    # A parametrize id may contain spaces (e.g. qutebrowser's _FindFlags
    # test_str[False-False-<no find flags>]); the nodeid must still be parsed
    # in full — a `\S+`-based nodeid would truncate at the space and drop the
    # result, spuriously grading a PASSED required test as not-passing.
    out = (
        "tests/t.py::TestFindFlags::test_str[True-True-FindCaseSensitively|FindBackward]"
        " PASSED [ 88%]\n"
        "tests/t.py::TestFindFlags::test_str[False-False-<no find flags>] PASSED [100%]\n"
        "tests/t.py::TestX::test_y[a b c] FAILED\n"
        "tests/t.py::TestX::test_skip[x y] SKIPPED (unsupported)\n"
        "some random prose line PASSED but not a nodeid\n"
        "INFO tests/t.py::TestX::test_prefixed PASSED\n"
        "FAILED tests/t.py::TestX::test_summary - AssertionError: boom\n"
    )
    r = pro_oracle.parse_pytest(out)
    assert r["tests/t.py::TestFindFlags::test_str[False-False-<no find flags>]"] == "PASSED"
    assert (r["tests/t.py::TestFindFlags::test_str[True-True-FindCaseSensitively|FindBackward]"]
            == "PASSED")
    assert r["tests/t.py::TestX::test_y[a b c]"] == "FAILED"
    assert r["tests/t.py::TestX::test_skip[x y]"] == "SKIPPED"  # inline trailer ok
    # the prose line, the space-prefixed line, and the summary "FAILED
    # <nodeid>" line are not results (nodeid must lead, no space before path)
    assert len(r) == 4


def test_grade_resolved():
    results = {"a::t1": "PASSED", "a::t2": "PASSED", "a::t3": "PASSED"}
    resolved, detail = pro_oracle.grade(results, ["a::t1"], ["a::t2", "a::t3"])
    assert resolved is True
    assert detail["n_required"] == 3 and detail["n_passed_required"] == 3


def test_grade_f2p_failing():
    results = {"a::t1": "FAILED", "a::t2": "PASSED"}
    resolved, detail = pro_oracle.grade(results, ["a::t1"], ["a::t2"])
    assert resolved is False and detail["f2p_failing"] == ["a::t1"]


def test_grade_p2p_regressed():
    results = {"a::t1": "PASSED", "a::t2": "FAILED"}
    resolved, detail = pro_oracle.grade(results, ["a::t1"], ["a::t2"])
    assert resolved is False and detail["p2p_failing"] == ["a::t2"]


def test_grade_missing_test_is_not_passed():
    # a required nodeid that never appears in output counts as not passed.
    results = {"a::t1": "PASSED"}
    resolved, detail = pro_oracle.grade(results, ["a::t1"], ["a::t2_missing"])
    assert resolved is False and detail["p2p_failing"] == ["a::t2_missing"]


def test_grade_xfail_passes_xpass_fails():
    results = {"a::t1": "XFAIL", "a::t2": "XPASS"}
    resolved, _ = pro_oracle.grade(results, ["a::t1"], [])
    assert resolved is True
    resolved2, _ = pro_oracle.grade(results, ["a::t2"], [])
    assert resolved2 is False


def test_entryscript_default_repo():
    row = {
        "repo": "ansible/ansible",
        "pro": {
            "before_repo_set_cmd": "git reset --hard BASE\ngit clean -fd\n"
                                   "git checkout BASE\n"
                                   "git checkout FIX -- test/units/utils/test_vars.py",
            "selected_test_files_to_run": '["test/units/utils/test_vars.py"]',
        },
    }
    s = pro_oracle._entryscript(row, "/app")
    assert "cd /app" in s
    assert "git checkout FIX -- test/units/utils/test_vars.py" in s
    # candidate applied AFTER the reference test-file checkout
    assert s.index("git apply -v /work/patch.diff") > s.index("git checkout FIX")
    # a non-applying candidate emits the sentinel and skips pytest (not-resolved,
    # not a harness error)
    assert pro_oracle.PATCH_APPLY_FAILED in s
    assert "python -m pytest -v" in s
    assert "test/units/utils/test_vars.py" in s.split("python -m pytest")[1]


def test_entryscript_reinstalls_patched_tree_and_sets_pythonpath():
    # Regression: the patch is applied to the /app source tree, but pytest was
    # importing the STALE package pip-installed into site-packages, so every
    # candidate (incl. gold) graded not-resolved. The entryscript must reinstall
    # the patched tree (editable) and export PYTHONPATH so imports resolve to it.
    row = {"repo": "ansible/ansible",
           "pro": {"before_repo_set_cmd": "git reset --hard BASE",
                   "selected_test_files_to_run": '["a/t.py"]'}}
    s = pro_oracle._entryscript(row, "/app")
    assert "pip install -e /app" in s
    # --use-pep517: legacy `setup.py develop` re-execs pip
    # WITHOUT --no-build-isolation, which then dials the image's dead localhost
    # index for setuptools and fails the reinstall on newer ansible images.
    assert "--use-pep517" in s
    assert "export PYTHONPATH=/app" in s
    # reinstall happens AFTER the patch applies and BEFORE pytest runs
    assert s.index("pip install -e /app") > s.index("git apply -v /work/patch.diff")
    assert s.index("pip install -e /app") < s.index("pytest")
    # a failed reinstall is a harness error (sentinel), never a stale-import pass
    assert pro_oracle.REINSTALL_FAILED in s


def test_grade_truncated_parametrize_id_prefix_match():
    # Regression: some Pro rows store required node-ids truncated at the first
    # whitespace inside a `[param]` (no closing `]`). The parser captures the
    # full id, so exact match fails; grade() must prefix-match a truncated
    # required id against the full parsed id(s).
    results = {
        "f.py::t[123-456-789-X -123456789X]": "PASSED",
        "f.py::t[ISBN: 123-456-789-X -123456789X]": "PASSED",
        "f.py::exact": "PASSED",
    }
    # truncated F2P ids (as stored by the vendor) resolve via prefix match
    resolved, _ = pro_oracle.grade(
        results, ["f.py::t[123-456-789-X", "f.py::t[ISBN:"], ["f.py::exact"])
    assert resolved is True


def test_grade_truncated_id_multi_match_all_pass_is_satisfied():
    # The vendor truncation is lossy: two distinct required cases can collapse
    # to the SAME stored prefix. All matching cases passing => satisfied.
    results = {"f.py::t[a x]": "PASSED", "f.py::t[a y]": "PASSED"}
    resolved, _ = pro_oracle.grade(results, ["f.py::t[a"], [])
    assert resolved is True


def test_grade_truncated_id_multi_match_one_failing_not_satisfied():
    # If any case under the truncated prefix FAILED, a required test did not
    # pass => not satisfied.
    results = {"f.py::t[a x]": "PASSED", "f.py::t[a y]": "FAILED"}
    resolved, detail = pro_oracle.grade(results, ["f.py::t[a"], [])
    assert resolved is False
    assert detail["f2p_failing"] == ["f.py::t[a"]


def test_grade_truncated_id_does_not_match_longer_sibling_param():
    # `t[123-X` must match `t[123-X ...]` (dropped whitespace) but NOT the
    # sibling `t[123-XY]` — else a plain startswith would false-match.
    results = {"f.py::t[123-X -456]": "PASSED", "f.py::t[123-XY]": "FAILED"}
    resolved, _ = pro_oracle.grade(results, ["f.py::t[123-X"], [])
    assert resolved is True


def test_grade_truncated_id_no_match_not_satisfied():
    resolved, _ = pro_oracle.grade({"f.py::other": "PASSED"}, ["f.py::ghost["], [])
    assert resolved is False


def test_grade_slash_collapsed_url_param_id():
    # Regression (ansible galaxy de5858f4...): some Pro rows store required ids
    # whose `//` was squashed to `/` by the capture tool, so a parametrize id
    # embedding a URL is stored `https:/host/...` while pytest emits
    # `https://host/...`. grade() must match under slash-normalization.
    real = "test/units/galaxy/test_api.py::test_cache_id[http://hostname:80/path-hostname:80]"
    stored = "test/units/galaxy/test_api.py::test_cache_id[http:/hostname:80/path-hostname:80]"
    resolved, _ = pro_oracle.grade({real: "PASSED"}, [stored], [])
    assert resolved is True
    # a FAILED real case under the same normalized id blocks resolution
    resolved2, _ = pro_oracle.grade({real: "FAILED"}, [stored], [])
    assert resolved2 is False


def test_grade_slash_collapse_does_not_confuse_distinct_ids():
    # Two genuinely distinct results must not be merged: normalization only
    # merges `//`->`/`, and the all-PASS guard keeps grading sound even if two
    # normalized ids collide.
    results = {"a::t[x/y]": "PASSED", "a::t[x/z]": "FAILED"}
    # required id that normalizes to neither -> not satisfied
    resolved, _ = pro_oracle.grade(results, ["a::t[x/w]"], [])
    assert resolved is False


def test_grade_truncated_at_nonwhitespace_boundary():
    # Regression (ansible galaxy): the capture tool can truncate at a non-
    # whitespace boundary too — `...content[{"de` for the real
    # `...content[{"de" "finit" "ely" ['invalid"]}]` (boundary is `"`). The
    # truncation reconstruction must accept any NON-word boundary char, not
    # only whitespace.
    real = 'f.py::test_cache_invalid_cache_content[{"de" "finit" "ely" [\'invalid"]}]'
    stored = 'f.py::test_cache_invalid_cache_content[{"de'
    resolved, _ = pro_oracle.grade({real: "PASSED"}, [stored], [])
    assert resolved is True


def test_grade_truncated_nonword_boundary_still_rejects_word_sibling():
    # `t[123-X` must still NOT match the sibling `t[123-XY]` (a word-char
    # boundary), even with the widened non-word-boundary rule.
    results = {"f.py::t[123-XY]": "PASSED"}
    resolved, _ = pro_oracle.grade(results, ["f.py::t[123-X"], [])
    assert resolved is False


def test_entryscript_has_rc_marker_and_separator():
    row = {"repo": "ansible/ansible",
           "pro": {"before_repo_set_cmd": "git reset --hard BASE",
                   "selected_test_files_to_run": '["a/t.py"]'}}
    s = pro_oracle._entryscript(row, "/app")
    assert pro_oracle._RC_MARKER in s          # exit code emitted for gating
    assert "-- a/t.py" in s                     # options/paths separator


def test_entryscript_rejects_option_like_test_file():
    import pytest
    row = {"repo": "ansible/ansible",
           "pro": {"before_repo_set_cmd": "git reset --hard BASE",
                   "selected_test_files_to_run": '["-k", "evil"]'}}
    with pytest.raises(ValueError):
        pro_oracle._entryscript(row, "/app")


def test_entryscript_qutebrowser_wrapper():
    row = {
        "repo": "qutebrowser/qutebrowser",
        "pro": {
            "before_repo_set_cmd": "git reset --hard BASE",
            "selected_test_files_to_run": '["tests/unit/utils/test_version.py"]',
        },
    }
    s = pro_oracle._entryscript(row, "/app")
    assert "QT_QPA_PLATFORM=offscreen" in s and "dbus-run-session" in s


def test_entryscript_qt_wrapper_is_probed():
    # Regression: some qutebrowser images ship
    # only PyQt6 while the tree's machinery.py defaults to PyQt5 (the image
    # build's sed doesn't survive `git reset --hard`), so conftest import died
    # with ModuleNotFoundError -> exit 4 for every candidate incl. gold. The
    # entryscript must export QUTE_QT_WRAPPER=PyQt6 via a runtime probe.
    row = {"repo": "qutebrowser/qutebrowser",
           "pro": {"before_repo_set_cmd": "git reset --hard BASE",
                   "selected_test_files_to_run": '["tests/unit/utils/test_version.py"]'}}
    s = pro_oracle._entryscript(row, "/app")
    assert "QUTE_QT_WRAPPER=PyQt6" in s
    assert 'python -c "import PyQt5"' in s  # probed, never hardcoded


def test_entryscript_ansible_forked_is_probed_not_hardcoded():
    # Regression: the ansible wrapper used to hardcode
    # --forked, but the pytest>=8 image generation ships WITHOUT pytest-forked
    # (not installable offline), so pytest aborted with exit 4 `unrecognized
    # arguments: --forked` and every candidate incl. GOLD graded as a harness
    # error. The flag must be applied via a runtime probe.
    row = {"repo": "ansible/ansible",
           "pro": {"before_repo_set_cmd": "git reset --hard BASE",
                   "selected_test_files_to_run": '["a/t.py"]'}}
    s = pro_oracle._entryscript(row, "/app")
    # no literal --forked in the pytest invocation line
    pytest_line = next(ln for ln in s.splitlines() if "python -m pytest" in ln)
    assert "--forked" not in pytest_line
    assert "$SBU_FORKED" in pytest_line
    # the probe defines SBU_FORKED before pytest runs and only sets --forked
    # when the plugin imports
    assert pro_oracle._FORKED_PROBE in s
    assert s.index(pro_oracle._FORKED_PROBE) < s.index("python -m pytest")
    assert 'import pytest_forked' in pro_oracle._FORKED_PROBE
    assert "SBU_FORKED=--forked" in pro_oracle._FORKED_PROBE


def test_entryscript_forked_probe_cannot_abort_under_errexit():
    # The probe runs under `set -e` (before the set +e pytest block); a missing
    # plugin must select the empty value via the if/else, never abort the
    # script (which would be a false harness error with no RC marker).
    assert pro_oracle._FORKED_PROBE.startswith("if ")
    assert "else SBU_FORKED=; fi" in pro_oracle._FORKED_PROBE
    row = {"repo": "ansible/ansible",
           "pro": {"before_repo_set_cmd": "git reset --hard BASE",
                   "selected_test_files_to_run": '["a/t.py"]'}}
    s = pro_oracle._entryscript(row, "/app")
    # probe sits in the errexit region: after set -e, before set +e
    assert s.index("set -e") < s.index(pro_oracle._FORKED_PROBE) < s.index("set +e")


def test_entryscript_reinstall_failure_tolerated_when_imports_stay_in_worktree():
    # Regression: some openlibrary images cannot
    # build editable metadata at all (setup.py imports Cython, absent from the
    # image), yet openlibrary is NOT pip-installed there — imports already
    # resolve from the patched worktree via PYTHONPATH, so the unconditional
    # REINSTALL_FAILED sentinel falsely errored every candidate incl. gold.
    # On reinstall failure the entryscript must probe where the package
    # imports from and only emit the sentinel when it resolves OUTSIDE the
    # worktree (a real stale-import hazard).
    row = {"repo": "internetarchive/openlibrary",
           "pro": {"before_repo_set_cmd": "git reset --hard BASE",
                   "selected_test_files_to_run": '["a/t.py"]'}}
    s = pro_oracle._entryscript(row, "/app")
    assert pro_oracle.REINSTALL_FAILED in s
    # probe imports the repo's top-level package under the worktree PYTHONPATH
    assert 'import openlibrary' in s
    assert "PYTHONPATH=/app python -c" in s
    # in-worktree import path => proceed; anything else => sentinel
    assert 'case "$SBU_PKG_FILE" in /app/*)' in s
    # the sentinel is inside the failure branch, not unconditional
    fail_branch = s.split("if ! python -m pip install")[1].split("\nfi")[0]
    assert pro_oracle.REINSTALL_FAILED in fail_branch


def test_entryscript_pkg_probe_uses_repo_basename():
    for repo, pkg in (("ansible/ansible", "ansible"),
                      ("qutebrowser/qutebrowser", "qutebrowser"),
                      ("internetarchive/openlibrary", "openlibrary")):
        row = {"repo": repo,
               "pro": {"before_repo_set_cmd": "git reset --hard BASE",
                       "selected_test_files_to_run": '["a/t.py"]'}}
        s = pro_oracle._entryscript(row, "/app")
        assert f"import {pkg}; print({pkg}.__file__)" in s


def test_entryscript_non_ansible_repos_have_no_forked_probe_dependency():
    # Other repos' wrappers don't reference $SBU_FORKED; the probe line is
    # harmless but the pytest command must not depend on it.
    for repo in ("qutebrowser/qutebrowser", "someone/other"):
        row = {"repo": repo,
               "pro": {"before_repo_set_cmd": "git reset --hard BASE",
                       "selected_test_files_to_run": '["a/t.py"]'}}
        s = pro_oracle._entryscript(row, "/app")
        pytest_line = next(ln for ln in s.splitlines() if "python -m pytest" in ln)
        assert "$SBU_FORKED" not in pytest_line
        assert "--forked" not in pytest_line


def test_pro_benchmark_image_name_from_row():
    b = REGISTRY["swe_bench_pro_python"]
    row = {"pro": {"dockerhub_tag": "ansible.ansible-xyz-vabc"}}
    assert b.image_name("instance_ansible__ansible-xyz", row) == \
        "jefzda/sweap-images:ansible.ansible-xyz-vabc"


def test_pro_benchmark_image_name_needs_row():
    import pytest
    b = REGISTRY["swe_bench_pro_python"]
    with pytest.raises(ValueError):
        b.image_name("instance_x", None)


def test_sanitize_truncated_nodeid_selectors_collapse_to_file():
    # Regression: one Pro row stores full pytest
    # node-ids in selected_test_files_to_run, 27/48 vendor-truncated at the
    # whitespace inside [param] (no closing ]). Passed verbatim, pytest emits
    # `ERROR: not found` per selector and exits 4 => gold graded harness error.
    # A file with ANY truncated selector collapses to ONE bare-file entry —
    # its intact node-ids must collapse too (mixing `f.py::id` with bare
    # `f.py` makes pytest keep only the node-id picks, so the truncated
    # cases still never run). Files with only intact ids keep them verbatim.
    files = [
        "test/units/modules/test_mount_facts.py::test_list[gen-\\nUUID=6b8b",  # truncated
        "test/units/modules/test_mount_facts.py::test_dedup[True-False]",      # intact, same file
        "test/units/modules/test_mount_facts.py::test_plain",                  # no param, same file
        "test/units/other/test_x.py::test_ok[a-b]",                            # intact, clean file
        "test/units/other/test_y.py",                                          # plain file
    ]
    out = pro_oracle._sanitize_test_files(files)
    # the whole mount_facts file collapses to a single bare entry
    assert out.count("test/units/modules/test_mount_facts.py") == 1
    assert not any("test_mount_facts.py::" in f for f in out)
    # a clean file's intact node-id survives verbatim; plain files pass through
    assert "test/units/other/test_x.py::test_ok[a-b]" in out
    assert "test/units/other/test_y.py" in out
    assert len(out) == 3


def test_widen_to_required_covers_uncovered_ids():
    # Regression: one Pro row (ansible 9a21e247,
    # sys_info) selects 6 node-ids but grading requires 14 ids from the same
    # file — the uncovered 8 never RUN, so even gold graded "8 required tests
    # not passing". The selection must widen to the bare file (sound superset).
    files = ["test/units/a.py::test_p[x-y]", "test/units/b.py::test_q"]
    required = ["test/units/a.py::test_p[x-y]", "test/units/a.py::TestC::test_r",
                "test/units/b.py::test_q"]
    out = pro_oracle._widen_to_required(files, required)
    assert out == ["test/units/a.py", "test/units/b.py::test_q"]


def test_widen_to_required_noop_when_covered():
    files = ["test/units/a.py", "test/units/b.py::test_q"]
    required = ["test/units/a.py::TestC::test_r", "test/units/b.py::test_q"]
    assert pro_oracle._widen_to_required(files, required) == files


def test_widen_to_required_adds_absent_required_file():
    # Codex-critic finding: a required file absent from the selection entirely
    # must be ADDED, not silently dropped (no current Pro row hits this).
    files = ["test/units/a.py::test_p"]
    required = ["test/units/b.py::test_y"]
    out = pro_oracle._widen_to_required(files, required)
    assert out == ["test/units/a.py::test_p", "test/units/b.py"]

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The AGENT-evaluation container path takes its container facts from the
benchmark registry — and the SWE-bench_Verified path is byte-for-byte what it
always was.

Both halves matter and they pull in opposite directions:

* eval/ used to hardcode `/testbed`, the conda activation, and no `--entrypoint`,
  which made the "adaptable to any benchmark" claim false on this subsystem:
  pointed at SWE-bench Pro it would put the agent in a directory that does not
  exist, with the wrong python, in a container that exits at once (Pro images set
  `ENTRYPOINT ["/bin/bash"]`, so `sleep infinity` arrives as a script name — and
  `docker run -d` still returns 0, so start() would report success and every
  later exec fail).
* the Verified path has produced real evaluation numbers. So the composed docker
  argv and the composed shell string are pinned here LITERALLY. If a later
  refactor moves a byte of them, this file fails rather than the results
  quietly becoming incomparable with the ones already published.

Nothing here needs docker: `_sg` is the single funnel every docker call in
eval/container.py goes through, so capturing it captures the invocation.
"""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from swebench_unified import benchmarks
from swebench_unified.eval import adapter as adapter_mod
from swebench_unified.eval import agent as agent_mod
from swebench_unified.eval import audit, metrics
from swebench_unified.eval import container as container_mod
from swebench_unified.eval import prompts as eval_prompts

SRC = Path(__file__).resolve().parents[1] / "src"

VERIFIED = benchmarks.REGISTRY["swe_bench_verified"]
PRO = benchmarks.REGISTRY["swe_bench_pro_python"]

# The exact activation the Verified images need, spelled once, in the registry.
# Written out here (not read from the registry) precisely so a change to the
# registry value shows up as a failure on the eval path too.
VERIFIED_ACTIVATE = "source /opt/miniconda3/bin/activate testbed"


class _Recorder:
    """Stand-in for eval.container._sg: records argv, reports success."""

    def __init__(self, stdout: str = "SANITIZE-OK"):
        self.calls: list[list[str]] = []
        self.stdout = stdout

    def __call__(self, args, timeout=None):
        self.calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout=self.stdout, stderr="")

    def of(self, subcommand: str) -> list[str]:
        """The MOST RECENT call of this subcommand (start() execs the sanitizer,
        so a later assertion about exec must not read that one)."""
        hit = [a for a in self.calls if a and a[0] == subcommand]
        assert hit, f"no docker {subcommand} recorded (calls: {self.calls})"
        return hit[-1]


@pytest.fixture()
def rec(monkeypatch):
    r = _Recorder()
    monkeypatch.setattr(container_mod, "_sg", r)
    monkeypatch.setattr(container_mod.docker_exec, "image_name", lambda iid, *a, **k: "IMG")
    return r


def _container(bench, rec, **kw):
    c = container_mod.EvalContainer("django__django-11276", "abc123", bench=bench, **kw)
    c.ensure_image = lambda: None          # no pull
    return c


def _exec_shell(rec: _Recorder) -> str:
    """The shell string handed to `docker exec ... /bin/bash -lc <here>`."""
    a = rec.of("exec")
    assert a[2:4] == ["/bin/bash", "-lc"], a
    return a[4]


# --------------------------------------------------------------------------
# Verified: the byte-for-byte control
# --------------------------------------------------------------------------

def test_verified_run_argv_is_unchanged_and_passes_no_entrypoint(rec):
    c = _container(VERIFIED, rec)
    assert c.start(mem="8g", cpus="4") is None
    assert len([a for a in rec.calls if a[0] == "run"]) == 1
    assert rec.of("run") == [
        "run", "-d", "--name", c.name, "--network", "none",
        "--memory", "8g", "--cpus", "4",
        "IMG", "sleep", "infinity",
    ]
    # the image's own ENTRYPOINT is used: adding the flag here would change the
    # container every published Verified run was measured in
    assert "--entrypoint" not in rec.of("run")


def test_verified_exec_composes_exactly_the_shell_string_it_always_did(rec):
    c = _container(VERIFIED, rec, sanitize=False)
    assert c.start() is None
    c.exec("pytest -q")
    assert _exec_shell(rec) == (
        "source /opt/miniconda3/bin/activate testbed 2>/dev/null; "
        "cd /testbed 2>/dev/null; pytest -q")


def test_verified_agent_shell_sets_no_pythonpath(rec):
    """Verified images install the repo into the conda env, so the agent command
    set nothing. The gate path DOES set PYTHONPATH; copying that here would
    change the Verified bytes, hence the separate registry flag."""
    c = _container(VERIFIED, rec, sanitize=False)
    c.start()
    c.exec("python -c 'import django'")
    assert "PYTHONPATH" not in _exec_shell(rec)
    assert VERIFIED.container_agent_pythonpath is False


def test_verified_sanitizer_runs_on_the_checkout(rec):
    c = _container(VERIFIED, rec)
    assert c.start() is None
    # $2 is the repo dir: the .git that gets stripped is the one the agent gets
    assert _exec_shell(rec).endswith("bash /sanitize.sh abc123 /testbed")


def test_verified_patch_is_extracted_from_the_checkout(rec):
    c = _container(VERIFIED, rec, sanitize=False)
    c.start()
    c.extract_patch()
    assert _exec_shell(rec).startswith(
        "source /opt/miniconda3/bin/activate testbed 2>/dev/null; "
        "cd /testbed 2>/dev/null; cd /testbed && git add -AN >/dev/null 2>&1; "
        "git diff __base -- . ")


def test_verified_nuclear_sanitize_reinitialises_the_checkout(rec):
    c = _container(VERIFIED, rec, nuclear=True)
    assert c.start() is None
    assert "cd /testbed && rm -rf .git && git init -q" in _exec_shell(rec)


# --------------------------------------------------------------------------
# Pro: /app, no activation, an explicit /bin/bash entrypoint
# --------------------------------------------------------------------------

def test_pro_overrides_the_entrypoint_and_passes_the_keepalive_as_c(rec):
    c = _container(PRO, rec)
    assert c.start(mem="8g", cpus="4") is None
    a = rec.of("run")
    assert a[a.index("--entrypoint") + 1] == "/bin/bash"
    # entrypoint IS the shell, so the cmd must not re-prepend one
    assert a[a.index("IMG") + 1:] == ["-c", "sleep infinity"]


def test_pro_exec_has_no_activation_and_cds_to_app(rec):
    c = _container(PRO, rec, sanitize=False)
    c.start()
    c.exec("pytest -q")
    shell = _exec_shell(rec)
    assert "activate" not in shell and "miniconda" not in shell
    assert shell.startswith("cd /app 2>/dev/null; ")
    assert shell.endswith("pytest -q")


def test_pro_agent_shell_points_pythonpath_at_the_checkout(rec):
    """Pro's ansible images keep the package at /app/lib/ansible with a STALE
    pre-patch copy in site-packages, so the agent's own `import ansible` would
    read unpatched code."""
    c = _container(PRO, rec, sanitize=False)
    c.start()
    c.exec("python -c 'import ansible'")
    assert "export PYTHONPATH=/app/lib:/app${PYTHONPATH:+:$PYTHONPATH}; " in _exec_shell(rec)


def test_pro_sanitizer_and_patch_use_app(rec):
    c = _container(PRO, rec)
    assert c.start() is None
    assert _exec_shell(rec).endswith("bash /sanitize.sh abc123 /app")
    c.extract_patch()
    assert "cd /app && git add -AN" in _exec_shell(rec)


def test_the_benchmark_is_resolved_from_the_environment_when_not_injected(rec, monkeypatch):
    """`bench=` is a test seam only. A real run reads the active benchmark in
    __init__, the way docker_exec.run_in_container does."""
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_pro_python")
    assert container_mod.EvalContainer("i", "c").workdir == "/app"
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    assert container_mod.EvalContainer("i", "c").workdir == "/testbed"


# --------------------------------------------------------------------------
# Agent-visible text: the same rule, and identical bytes for Verified
# --------------------------------------------------------------------------

def test_bash_and_submit_tool_text_is_unchanged_for_verified():
    assert agent_mod.tool_bash("/testbed").description == (
        "Run a bash command inside the repository container (cwd /testbed, "
        "with the project's Python env active). Use it to read/edit files, run the "
        "existing public tests, grep, etc. Returns stdout+stderr (truncated).")
    assert agent_mod.tool_submit("/testbed").description == (
        "Finalize your solution. The patch is captured automatically as the "
        "git diff of your edits to /testbed against the base commit. In modes that "
        "require a verified model, also pass model_path (the file you verified).")


def test_bash_and_submit_tool_text_follows_the_workdir():
    for spec in (agent_mod.tool_bash("/app"), agent_mod.tool_submit("/app")):
        assert "/app" in spec.description
        assert "/testbed" not in spec.description


def test_the_agent_builds_its_tools_from_the_container_workdir():
    a = adapter_mod.get_adapter("nagini")
    ag = agent_mod.EvalAgent(a, SimpleNamespace(offers_verifier=True),
                             SimpleNamespace(workdir="/app"), provider=None)
    assert ag.workdir == "/app"
    for spec in ag._tools():
        assert "/testbed" not in spec.description
        assert "/testbed" not in str(spec.properties)


@pytest.mark.parametrize("backend,want", [
    ("nagini", ("/testbed/model.py", "/testbed/spec.py", "/model.py")),
    ("velvet", ("/testbed/Solution.lean", "/testbed/Model.lean", "/Solution.lean")),
    ("lean", ("/testbed/Solution.lean", "/testbed/Model.lean", "/Solution.lean")),
    ("ears", ("/testbed/requirements.md", "/requirements.md")),
])
def test_guess_model_paths_are_unchanged_for_verified(backend, want, monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    assert adapter_mod.get_adapter(backend).guess_model_paths() == want


def test_guess_model_paths_follow_the_workdir():
    a = adapter_mod.get_adapter("nagini")
    assert a.guess_model_paths("/app") == ("/app/model.py", "/app/spec.py", "/model.py")


@pytest.mark.parametrize("backend,want", [
    ("nagini", "e.g. /testbed/model.py"),
    ("velvet", "e.g. /testbed/Solution.lean"),
    ("lean", "e.g. /testbed/Solution.lean"),
    ("ears", "e.g. /testbed/requirements.md"),
])
def test_verify_tool_example_path_is_unchanged_for_verified(backend, want, monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    spec = adapter_mod.get_adapter(backend).verify_tool_spec()
    assert want in spec.properties["path"]["description"]


def test_verify_tool_example_path_follows_the_workdir():
    spec = adapter_mod.get_adapter("nagini").verify_tool_spec("/app")
    desc = spec.properties["path"]["description"]
    assert "e.g. /app/model.py" in desc and "/testbed" not in desc


# --------------------------------------------------------------------------
# Prompts: the same fact, rendered from the registry
# --------------------------------------------------------------------------

_ADAPTER = SimpleNamespace(backend=SimpleNamespace(name="nagini"))


def _task(mode: int):
    return SimpleNamespace(mode=mode, backend="nagini", repo="django/django",
                           gives_localization=True)


def test_common_rules_render_the_verified_directory_verbatim(monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    text = eval_prompts._common_rules(_ADAPTER, _task(0))
    assert text.startswith(
        "You are working inside a checkout of the `django/django` repository at "
        "its base commit, in the directory /testbed. Use the `bash` tool to read "
        "and edit files, and to run the repository's existing tests. Make your "
        "changes directly in /testbed.")
    assert "diff of your source edits to /testbed." in text


def test_mode_task_renders_the_verified_directory_verbatim(monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    assert eval_prompts._mode_task(_ADAPTER, _task(0)).startswith(
        "Your task: edit the code in /testbed so the issue described below is "
        "resolved.")
    assert "/testbed/model.py" in eval_prompts._mode_task(_ADAPTER, _task(1))


@pytest.mark.parametrize("mode", [0, 1, 2, 3, 4, 10, 100])
def test_no_eval_prompt_names_another_benchmarks_directory(mode, monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_pro_python")
    text = (eval_prompts._common_rules(_ADAPTER, _task(mode))
            + eval_prompts._mode_task(_ADAPTER, _task(mode)))
    assert "/testbed" not in text
    assert "/app" in text
    assert "{" not in text and "}" not in text     # nothing left unsubstituted


def test_an_unrenderable_prompt_names_the_file(tmp_path, monkeypatch):
    """Making the mode prompts format targets means an override with a bare brace
    now raises. It must say WHICH file: the failure happens inside the agent
    subprocess, where a bare KeyError reads as a model that never submitted."""
    from swebench_unified import prompts as prompt_registry
    (tmp_path / "shared").mkdir()
    bad = tmp_path / "shared" / "eval_mode_0.md"
    bad.write_text("edit {workdir}; payload {gate, verdict}\n")
    monkeypatch.setenv("SBU_PROMPTS_DIR", str(tmp_path))
    with pytest.raises(prompt_registry.PromptRenderError) as ei:
        prompt_registry.load_prompt("eval_mode_0", workdir="/app")
    assert str(bad) in str(ei.value)


# --------------------------------------------------------------------------
# The two consumers that run after the container is gone
# --------------------------------------------------------------------------

def test_repo_edit_detection_follows_the_workdir():
    ed = metrics._is_repo_patch_edit
    assert ed("sed -i 's/a/b/' /testbed/django/db/query.py", "/testbed")
    # a NON-.py edit was invisible on any benchmark that checks out elsewhere:
    # only the hardcoded /testbed/ disjunct could have caught it
    assert ed("sed -i 's/a/b/' /app/lib/ansible/cli.cfg", "/app")
    assert not ed("sed -i 's/a/b/' /app/lib/ansible/cli.cfg", "/testbed")


def test_absolute_dotgit_reads_are_flagged_at_the_configured_workdir():
    traj = [{"kind": "bash", "command": "cat /app/.git/config"}]
    labels = [f.label for f in audit.screen("i", traj, workdir="/app").flags]
    assert "dotgit-read" in labels
    # and the Verified spelling still flags under Verified
    traj_v = [{"kind": "bash", "command": "cat /testbed/.git/config"}]
    assert "dotgit-read" in [
        f.label for f in audit.screen("i", traj_v, workdir="/testbed").flags]
    # a path outside the configured checkout is not an absolute .git read there
    assert "dotgit-read" not in [
        f.label for f in audit.screen("i", traj, workdir="/testbed").flags]


def test_relative_dotgit_reads_are_still_flagged_on_any_benchmark():
    traj = [{"kind": "bash", "command": "cat .git/packed-refs"}]
    for wd in ("/testbed", "/app"):
        assert "dotgit-read" in [
            f.label for f in audit.screen("i", traj, workdir=wd).flags]


def test_audit_defaults_to_the_active_benchmark(monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_pro_python")
    traj = [{"kind": "bash", "command": "cat /app/.git/config"}]
    assert "dotgit-read" in [f.label for f in audit.screen("i", traj).flags]


# --------------------------------------------------------------------------
# The reason this drifted: two copies of one fact
# --------------------------------------------------------------------------

EVAL_DIR = SRC / "swebench_unified" / "eval"

# Container facts the registry declares. A literal copy of any of these in eval/
# is how the subsystem drifted away from the gate path in the first place: the
# gate half was made benchmark-driven and the agent half kept its own constants,
# and nothing failed.
FORBIDDEN_LITERALS = ("/testbed", "/app/", VERIFIED_ACTIVATE, "/opt/miniconda3")


def _string_literals(path: Path):
    """Every string literal in a module EXCEPT docstrings, with line numbers.

    Docstrings are excluded on purpose: prose is allowed — required, even — to
    say "/testbed on Verified, /app on Pro" while explaining the rule. What must
    not exist is a container path the CODE uses.
    """
    tree = ast.parse(path.read_text())
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) \
                    and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docs.add(id(body[0].value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docs:
            yield node.lineno, node.value


@pytest.mark.parametrize("path", sorted(EVAL_DIR.glob("*.py")),
                         ids=lambda p: p.name)
def test_no_container_default_is_duplicated_in_eval(path):
    bad = [(ln, s) for ln, s in _string_literals(path)
           if any(lit in s for lit in FORBIDDEN_LITERALS)]
    assert not bad, (
        f"{path.name} hardcodes a container fact the Benchmark registry already "
        f"declares (container_workdir / container_env_activate): {bad}. Read it "
        f"off the active benchmark, as docker_exec.run_in_container does — the "
        f"dataclass defaults in benchmarks.py are the one place these live.")


def test_the_registry_is_where_those_defaults_live():
    src = (SRC / "swebench_unified" / "benchmarks.py").read_text()
    assert VERIFIED.container_env_activate == VERIFIED_ACTIVATE
    assert src.count(f'"{VERIFIED_ACTIVATE}"') >= 1
    assert VERIFIED.container_workdir == "/testbed"
    assert PRO.container_workdir == "/app"
    assert PRO.container_entrypoint == "/bin/bash"
    assert VERIFIED.container_entrypoint is None


def test_the_pythonpath_template_has_one_definition():
    """docker_exec used to spell `{workdir}/lib:{workdir}` itself; the agent path
    needs the same string, and two copies of it is the defect this file is about.

    Safe to move because `docker_exec.py` is not one of the sources a recorded
    verdict is pinned to: it is absent from `pbt_certify.judgment_paths()` and
    from `gates.base._HARNESS_FILES`, so this refactor ages no record. Any file
    that IS in one of those sets must be left alone for cosmetic gain, since an
    edit there restages every cell in the corpus.
    """
    assert VERIFIED.container_pythonpath == "/testbed/lib:/testbed"
    assert PRO.container_pythonpath == "/app/lib:/app"
    dx = (SRC / "swebench_unified" / "docker_exec.py").read_text()
    assert "bench.container_pythonpath" in dx
    assert '/lib:' not in dx

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Benchmark provider seam.

The pipeline was born bound to SWE-bench_Verified: the frozen dataset path, the
Docker image-naming scheme, and the official-harness parameters (dataset_name /
namespace / image_tag) were all hard-coded. A `Benchmark` bundles those into one
value so a second benchmark (e.g. the SWE-bench Pro Python subset) is a registry
entry, not a scatter of edits.

The ACTIVE benchmark is resolved once from `SBU_BENCHMARK` (default
`swe_bench_verified`), mirroring `SBU_RUN_PREFIX`. `paths.py` reads the active
benchmark's dataset locations at import, so existing `from ..paths import
DATASET_JSONL` consumers are unchanged. Where the frozen data lives is
`data_root()` (SBU_DATA_ROOT), and adding a benchmark is one registry entry plus,
if its rows are not already the frozen schema, a row mapping. Neither has to be
an edit to this repository: `SBU_BENCHMARK_SPEC` points at a JSON file declaring
the same fields, and `row_map` / `row_filter` name the mapping as
`module:function`. See `external_benchmarks`.

Row-schema contract (the frozen JSONL every downstream reader assumes): each row
carries at least `instance_id, repo, base_commit, patch, test_patch,
problem_statement, FAIL_TO_PASS, PASS_TO_PASS, environment_setup_commit`.
Construction and the static gates need only these; the Docker oracle (G-RESOLVE /
G-CONF / G-AX) additionally needs prebuilt per-instance images + a compatible
harness -- gated by `supports_docker_oracle`. The contract is machine-checked at
freeze time, per row, by `scripts/fetch_dataset.py:row_complaints`, whose
`REQUIRED_FIELDS` is its one definition.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

# Self-contained (no import from paths): paths.py imports THIS module to resolve
# dataset locations, so the dependency must be one-directional to avoid a cycle.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DATA_ROOT = _PROJECT_ROOT / "data"


def data_root() -> Path:
    """Root of the frozen per-benchmark data (`<root>/<data_subdir>/test.jsonl`).

    SBU_DATA_ROOT relocates it, so a new benchmark can be fetched and smoke-tested
    without freezing a dataset into the checkout. Resolved at CALL time: a
    module-level constant binds one root at import, which no test fixture can move
    -- the same trap active_workdir() below documents. A bare relative value is
    taken under the project root, matching paths.TASKS_ROOT (SBU_BENCHMARK_DIR).
    THE one definition: paths.py resolves its dataset locations through the active
    Benchmark instead of re-deriving `<project root>/data`.
    """
    env = os.environ.get("SBU_DATA_ROOT")
    if not env:
        return _DEFAULT_DATA_ROOT
    p = Path(env)
    return p if p.is_absolute() else _PROJECT_ROOT / p


# The graders G-RESOLVE knows how to drive; see `resolve_style` below.
_RESOLVE_STYLES = ("swebench", "pro")


@dataclass(frozen=True)
class Benchmark:
    name: str
    data_subdir: str          # frozen data under <data_root()>/<data_subdir>/
    hf_dataset: str           # HuggingFace dataset id (fetch source)
    # --- Docker oracle ---
    # supports_docker_oracle gates G-RESOLVE (the correctness oracle).
    supports_docker_oracle: bool
    # supports_generated_script_gates gates G-CONF / G-AX, which run our
    # generated conformance_check.py / axiom_check.py inside the instance image
    # (via container_workdir + container_env_activate below). Keep it False for
    # a benchmark whose image plumbing -- checkout path, python env -- has not
    # been validated for those scripts yet: a wrong workdir or a missing env
    # activation makes every check script error out, which looks like a spec
    # defect rather than a harness gap.
    supports_generated_script_gates: bool = True
    # how G-RESOLVE grades: "swebench" = the official pip harness (Verified);
    # "pro" = our in-container runner in pro_oracle.py (SWE-bench Pro).
    resolve_style: str = "swebench"
    dataset_name: str = ""    # official-harness --dataset_name (G-RESOLVE)
    namespace: str | None = None   # official-harness --namespace
    image_tag: str = "latest"      # official-harness --instance_image_tag
    # image name template; {key} is the instance_id with '__' -> the sub token.
    # The alternative is to read the tag out of the row: `image_from_row_key`
    # below, exactly one of the two.
    image_template: str = ""
    image_id_sub: str = "_1776_"
    # Pro images: jefzda/sweap-images:<dockerhub_tag>, pulled DIRECT from Docker
    # Hub (the mirror.gcr.io retag trick only covers library/GCR images), repo
    # checkout at /app (Verified uses /testbed).
    # Dotted path to the tag WITHIN the frozen row: "pro.dockerhub_tag" reads
    # row["pro"]["dockerhub_tag"], "image_tag" reads it at the top level. A path
    # rather than a bare key because the sub-object a benchmark keeps its image
    # under is its own; hardcoding one benchmark's ("pro") made this seam usable
    # by exactly that benchmark.
    image_from_row_key: str = ""
    image_repo: str = ""           # e.g. "jefzda/sweap-images"
    pull_via_mirror: bool = True
    container_workdir: str = "/testbed"
    # shell prefix that activates the in-image python env before running a
    # generated check script (G-CONF/G-AX) or the agent's own bash tool.
    # Verified images ship a conda `testbed` env; Pro images use the system
    # python (no activation). The JOINER is the caller's: the gate path chains
    # it with ` && ` (a failed activation must abort the check), the agent path
    # with `; 2>/dev/null` (an agent's shell must survive it).
    container_env_activate: str = "source /opt/miniconda3/bin/activate testbed"
    container_entrypoint: str | None = None  # None = image default; Pro = /bin/bash
    # Whether a shell handed to the AGENT (eval/container.py) needs PYTHONPATH
    # pointed at the checkout (`container_pythonpath`). Verified images install
    # the repo into the conda `testbed` env, so `import <pkg>` already resolves
    # the checkout and the agent's command sets nothing; Pro's ansible images
    # keep the package at /app/lib/ansible with a STALE pre-patch copy in
    # site-packages, so without it the agent's own `import ansible` reads the
    # stale copy. The GATE path sets it unconditionally (it runs a script from
    # /work, outside the checkout), which is why this flag is agent-only.
    container_agent_pythonpath: bool = False
    # --- frozen-write contract, read by scripts/fetch_dataset.py ---
    hf_split: str = "test"    # both shipped benchmarks freeze `test`; not universal
    # A dataset that is not one loadable split needs one of these: `hf_config` is
    # the configuration name (`load_dataset`'s `name`), `hf_data_files` the file or
    # glob to read inside the dataset repository. Both empty for a dataset whose
    # default configuration loads on its own -- every shipped benchmark -- and the
    # fetch then makes exactly the call it made before these fields existed.
    # `hf_dataset` may also be a local directory, which is the same seam offline.
    hf_config: str = ""
    hf_data_files: str = ""
    # upstream_columns is the strict check that catches an upstream schema drift.
    # For a benchmark whose rows ARE the frozen schema it is exact, ORDER
    # included, because the upstream order is the frozen key order: a silent
    # reorder would rewrite every line and read as tampering in G-INTEGRITY. For
    # one the fetch script maps (Pro), it lists the columns the mapping reads and
    # only presence is checked, with frozen_columns giving the emitted key order.
    upstream_columns: tuple[str, ...] = ()
    frozen_columns: tuple[str, ...] = ()   # () = same as upstream_columns
    # Row adapters as `module:function` paths, resolved by scripts/fetch_dataset.py
    # when the rows are not already the frozen schema. They exist so a benchmark
    # declared OUTSIDE this package (see `external_benchmarks`) can bring its own
    # mapping instead of needing an entry added to that script's table.
    row_filter: str = ""   # (row) -> bool: keep this upstream row
    row_map: str = ""      # (row) -> dict: upstream row -> frozen row
    # --- where the task repositories are mirrored from ---
    # scripts/setup_repos.py formats this with the row's `repo`. A benchmark whose
    # repositories are not on GitHub states its own host here; one whose code
    # exists only inside its images cannot be mirrored from any URL and is built
    # with `--repo PATH` instead (construct/build_one.py).
    repo_url_template: str = "https://github.com/{repo}.git"

    def __post_init__(self) -> None:
        """Refuse an entry whose settings cannot be acted on: a clone URL that is
        the same for every repository, or Docker settings naming no image or grader.

        Every field below has a Verified-shaped default, which is what makes a new
        entry short -- and also what lets one be silently wrong. `image_name`
        raises when the oracle is declared absent, but with it declared PRESENT
        and no template set the format string is empty, so the puller was handed
        `""` and reported a missing image rather than a missing setting. The same
        shape reaches the official harness as a bare `--dataset_name`. A
        constructor check is the one place that sees the whole combination.
        """
        if "{repo}" not in self.repo_url_template:
            raise ValueError(
                f"benchmark {self.name!r} has repo_url_template="
                f"{self.repo_url_template!r}, which does not name {{repo}}: every "
                "task repository would be mirrored from one URL")
        if not self.supports_docker_oracle:
            return
        named = bool(self.image_template) + bool(self.image_from_row_key)
        if named != 1:
            raise ValueError(
                f"benchmark {self.name!r} declares a Docker oracle, so exactly one "
                "of image_template / image_from_row_key must be set "
                f"(image_template={self.image_template!r}, "
                f"image_from_row_key={self.image_from_row_key!r})")
        if self.image_from_row_key and not self.image_repo:
            raise ValueError(
                f"benchmark {self.name!r} names the image from the row, so "
                "image_repo must give the repository it is a tag of")
        if self.resolve_style not in _RESOLVE_STYLES:
            # harness.run_resolve branches on "pro" and takes the official
            # harness otherwise, so an unrecognised style is not an error there:
            # it is Verified's grader silently applied to another benchmark.
            raise ValueError(
                f"benchmark {self.name!r} has resolve_style="
                f"{self.resolve_style!r}; known: {sorted(_RESOLVE_STYLES)}. A new "
                "benchmark whose grading fits neither needs its own oracle, or "
                "supports_docker_oracle=False until it has one")
        if self.resolve_style == "swebench" and not self.dataset_name:
            raise ValueError(
                f"benchmark {self.name!r} grades with the official harness, so "
                "dataset_name must be the dataset that harness loads")

    @property
    def container_pythonpath(self) -> str:
        """PYTHONPATH that resolves in-tree source for a non-editable checkout:
        `<workdir>/lib` FIRST (Pro's ansible images keep the repo package there
        while a stale pre-patch copy sits in site-packages), then the checkout
        itself. Harmless when lib/ is absent. One definition, shared by the gate
        path (docker_exec) and the agent path (eval/container)."""
        return f"{self.container_workdir}/lib:{self.container_workdir}"

    @property
    def data_dir(self) -> Path:
        return data_root() / self.data_subdir

    @property
    def dataset_jsonl(self) -> Path:
        return self.data_dir / "test.jsonl"

    @property
    def eval_localization(self) -> Path:
        return self.data_dir / "eval_localization.json"

    @property
    def frozen_instances(self) -> Path:
        return self.data_dir / "eval_frozen.txt"

    def image_name(self, instance_id: str, row: dict | None = None) -> str:
        """Docker image for an instance. One benchmark derives it from the id,
        another reads it out of the frozen row at `image_from_row_key`. Raise
        loudly rather than pull a wrong image."""
        if not self.supports_docker_oracle:
            raise NotImplementedError(
                f"benchmark {self.name!r} has no wired Docker oracle "
                "(image naming + harness); construction runs static gates only")
        if self.image_from_row_key:
            if row is None:
                raise ValueError(
                    f"benchmark {self.name!r} needs the frozen row to name the "
                    f"image (key {self.image_from_row_key!r})")
            tag: object = row
            for seg in self.image_from_row_key.split("."):
                tag = (tag or {}).get(seg) if isinstance(tag, dict) else None
            if not tag or not isinstance(tag, str):
                raise ValueError(
                    f"{instance_id}: row has no {self.image_from_row_key} to "
                    "name the image from")
            return f"{self.image_repo}:{tag}"
        key = instance_id.replace("__", self.image_id_sub)
        return self.image_template.format(key=key, tag=self.image_tag)


_VERIFIED = Benchmark(
    name="swe_bench_verified",
    data_subdir="swe_bench_verified",
    hf_dataset="princeton-nlp/SWE-bench_Verified",
    # upstream order as of datasets 5.0.1; it is also the frozen key order, so
    # this tuple is what makes data/swe_bench_verified/test.jsonl reproducible
    # (sha256 1c830d40…) across checkouts.
    upstream_columns=(
        "repo", "instance_id", "base_commit", "patch", "test_patch",
        "problem_statement", "hints_text", "created_at", "version",
        "FAIL_TO_PASS", "PASS_TO_PASS", "environment_setup_commit", "difficulty",
    ),
    supports_docker_oracle=True,
    resolve_style="swebench",
    dataset_name="princeton-nlp/SWE-bench_Verified",
    namespace="swebench",
    image_tag="latest",
    image_template="swebench/sweb.eval.x86_64.{key}:{tag}",
    container_workdir="/testbed",
    container_env_activate="source /opt/miniconda3/bin/activate testbed",
)

# SWE-bench Pro, Python subset (266 rows across ansible / openlibrary /
# qutebrowser). Ingested by scripts/fetch_dataset.py, which maps Pro's row schema
# onto the frozen one (_ADAPTERS there). G-RESOLVE uses our own in-container
# runner (pro_oracle.py) since Pro ships its own images + harness, not the
# swebench pip package.
#
# G-CONF/G-AX run our generated check scripts; the container plumbing is
# Pro-aware (workdir /app, no conda activation, system python, /bin/bash
# entrypoint) and validated live on Pro images across all 3 repos.
_PRO_PYTHON = Benchmark(
    name="swe_bench_pro_python",
    data_subdir="swe_bench_pro_python",
    hf_dataset="ScaleAI/SWE-bench_Pro",
    # mapped, so these are the columns the mapping reads (presence-checked) …
    upstream_columns=(
        "repo", "instance_id", "base_commit", "patch", "test_patch",
        "problem_statement", "requirements", "interface", "repo_language",
        "fail_to_pass", "pass_to_pass", "issue_specificity", "issue_categories",
        "before_repo_set_cmd", "selected_test_files_to_run", "dockerhub_tag",
    ),
    # … and this is the key order written (Verified's, minus what Pro lacks, plus
    # the `pro` sub-object): sha256 2c4d6771….
    frozen_columns=(
        "repo", "instance_id", "base_commit", "patch", "test_patch",
        "problem_statement", "hints_text", "version",
        "FAIL_TO_PASS", "PASS_TO_PASS", "environment_setup_commit", "pro",
    ),
    supports_docker_oracle=True,
    supports_generated_script_gates=True,
    resolve_style="pro",
    image_from_row_key="pro.dockerhub_tag",
    image_repo="jefzda/sweap-images",
    pull_via_mirror=False,
    container_workdir="/app",
    container_env_activate="",   # system python; no conda env
    container_entrypoint="/bin/bash",
    container_agent_pythonpath=True,   # /app/lib first: stale copy in site-packages
)

# SWE-bench-Live, `verified` split: 500 python instances over 100 repos, another
# curator and another row schema. A third benchmark registered to exercise the
# adapter seam rather than restate it: scripts/fetch_dataset.py `_ADAPTERS` maps
# the rows (list FAIL_TO_PASS/PASS_TO_PASS, datetime `created_at`, no `version`,
# no `environment_setup_commit`, a struct `difficulty`) and no gate changed.
# Freeze `verified`, not `test`/`full`: upstream grows those monthly, and
# G-INTEGRITY compares every bundle against the frozen file.
#
# supports_docker_oracle=False because neither shipped resolve_style fits: the
# official harness indexes MAP_REPO_VERSION_TO_SPECS[repo][row["version"]] and
# these rows carry no `version`, so an oracle here means a new resolve_style over
# the rows' own `test_cmds` + `log_parser` (kept under `live`). G-RESOLVE then
# skips explicitly rather than pulling an image. The container settings are read
# from the image config over the registry; the inherited Verified default would
# activate a conda env these images do not have. `image_template` stays unset
# because the real tags lowercase the instance id, so a template would silently
# misname the ids that are not already lowercase.
# See tests/test_third_benchmark_smoke.py for what is validated end to end.
_LIVE_VERIFIED = Benchmark(
    name="swe_bench_live_verified",
    data_subdir="swe_bench_live_verified",
    hf_dataset="SWE-bench-Live/SWE-bench-Live",
    hf_split="verified",       # NOT `test`: that split grows every month
    # mapped, so these are the columns the mapping reads (presence-checked) …
    upstream_columns=(
        "repo", "pull_number", "instance_id", "issue_numbers", "base_commit",
        "patch", "test_patch", "problem_statement", "hints_text", "created_at",
        "commit_url", "test_cmds", "log_parser", "difficulty",
        "FAIL_TO_PASS", "PASS_TO_PASS",
    ),
    # … and this is the key order written: Verified's, minus `difficulty` (Live's
    # is a different TYPE under the same name, so it moves into `live` rather than
    # silently changing what the column means), plus the `live` sub-object.
    frozen_columns=(
        "repo", "instance_id", "base_commit", "patch", "test_patch",
        "problem_statement", "hints_text", "created_at", "version",
        "FAIL_TO_PASS", "PASS_TO_PASS", "environment_setup_commit", "live",
    ),
    supports_docker_oracle=False,
    supports_generated_script_gates=False,
    container_workdir="/testbed",
    container_env_activate="",   # system python; no conda env in these images
)

# SWE-Gym, `lite` split: 230 python instances over 11 repos, a third curator and
# a third row shape. A fourth entry earns its place by measuring a DIFFERENT part
# of the seam than Live does: the rows carry a real `version`, no
# `environment_setup_commit` column at all, and nothing worth preserving beyond
# the frozen schema -- so this is the one entry whose frozen row is the contract
# and nothing else, with no sub-object. It also freezes `train`, which is the only
# exercise `hf_split` gets outside the two shipped values.
#
# supports_docker_oracle=False, and for a different reason from Live's: `version`
# IS present here, but the official harness indexes
# MAP_REPO_VERSION_TO_SPECS[repo][version] and that table has no entry for
# Project-MONAI/MONAI, facebookresearch/hydra or conan-io/conan, so it cannot
# build an environment for most of this split. SWE-Gym publishes its own
# per-instance images under its own naming; grading here means a new
# resolve_style over those, and until one exists G-RESOLVE skips explicitly
# rather than pulling an image. `container_env_activate` is empty for the same
# reason as Live: the inherited Verified default would activate a conda env these
# images do not have.
_GYM_LITE = Benchmark(
    name="swe_gym_lite",
    data_subdir="swe_gym_lite",
    hf_dataset="SWE-Gym/SWE-Gym-Lite",
    hf_split="train",
    # mapped, so these are the columns the mapping reads (presence-checked) …
    upstream_columns=(
        "instance_id", "hints_text", "patch", "test_patch", "created_at",
        "problem_statement", "repo", "base_commit", "version",
        "PASS_TO_PASS", "FAIL_TO_PASS",
    ),
    # … and this is the key order written: Verified's, minus `difficulty`, which
    # this curator does not publish. `environment_setup_commit` is emitted from
    # `base_commit` (there is no upstream column for it) so that every frozen
    # file has one meaning for the key setup_repos.py reads without a default.
    frozen_columns=(
        "repo", "instance_id", "base_commit", "patch", "test_patch",
        "problem_statement", "hints_text", "created_at", "version",
        "FAIL_TO_PASS", "PASS_TO_PASS", "environment_setup_commit",
    ),
    supports_docker_oracle=False,
    supports_generated_script_gates=False,
    container_workdir="/testbed",
    container_env_activate="",   # system python; no conda env in these images
)

REGISTRY = {b.name: b
            for b in (_VERIFIED, _PRO_PYTHON, _LIVE_VERIFIED, _GYM_LITE)}
DEFAULT_BENCHMARK = "swe_bench_verified"

SPEC_ENV = "SBU_BENCHMARK_SPEC"


def external_benchmarks() -> dict[str, Benchmark]:
    """Benchmarks declared outside this package, from `SBU_BENCHMARK_SPEC`.

    A path (or `os.pathsep`-separated paths) to a JSON file holding one entry, a
    list of entries, or `{"benchmarks": [...]}`; each entry is the `Benchmark`
    fields above. This is the seam that makes adapting the pipeline to another
    benchmark need no edit to this repository: point the env var at your own file
    and every consumer of `registry()` sees it. Unknown keys, a bad type and a
    name that would shadow a built-in are all refused, because a typo would
    otherwise silently leave a Verified-shaped default in place.
    """
    out: dict[str, Benchmark] = {}
    known = {f.name for f in fields(Benchmark)}
    tuple_keys = ("upstream_columns", "frozen_columns")
    for part in os.environ.get(SPEC_ENV, "").split(os.pathsep):
        if not part:
            continue
        path = Path(part).expanduser()
        try:
            doc = json.loads(path.read_text())
        except OSError as exc:
            raise SystemExit(f"{SPEC_ENV}: {exc}")
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{SPEC_ENV}: {path}: {exc}")
        if isinstance(doc, dict):
            doc = doc.get("benchmarks", [doc])
        if not isinstance(doc, list):
            raise SystemExit(f"{SPEC_ENV}: {path}: expected an object or a list")
        for entry in doc:
            if not isinstance(entry, dict):
                raise SystemExit(f"{SPEC_ENV}: {path}: every entry must be an object")
            unknown = sorted(set(entry) - known)
            if unknown:
                raise SystemExit(
                    f"{SPEC_ENV}: {path}: unknown field(s) {unknown}; "
                    f"known: {sorted(known)}")
            kw: dict[str, Any] = {k: (tuple(v) if k in tuple_keys else v)
                        for k, v in entry.items()}
            try:
                bench = Benchmark(**kw)
            except (TypeError, ValueError) as exc:
                raise SystemExit(f"{SPEC_ENV}: {path}: {exc}")
            if bench.name in REGISTRY:
                raise SystemExit(
                    f"{SPEC_ENV}: {path}: {bench.name!r} is a built-in benchmark; "
                    "an external entry may not shadow one")
            out[bench.name] = bench
    return out


def registry() -> dict[str, Benchmark]:
    """Every known benchmark: the built-ins plus whatever `SPEC_ENV` declares.

    Resolved at CALL time, like `data_root()`, so a spec exported after import is
    still seen.
    """
    return {**REGISTRY, **external_benchmarks()}


def active() -> Benchmark:
    name = os.environ.get("SBU_BENCHMARK", DEFAULT_BENCHMARK)
    known = registry()
    try:
        return known[name]
    except KeyError:
        raise SystemExit(
            f"unknown SBU_BENCHMARK={name!r}; known: {sorted(known)} "
            f"(declare another with {SPEC_ENV})")


def active_workdir() -> str:
    """The active benchmark's checkout directory.

    Its own function because several consumers need exactly this one fact and
    hold no Benchmark: the eval prompt assembler, the trajectory audit screen and
    the metrics rollup (the last two run after the container is gone, and are
    also recomputed offline over saved trajectories). Every one of them resolves
    it at CALL time -- a module-level constant would bind one benchmark's path at
    import, which is precisely how the eval path drifted from the gate path.
    Callers that DO hold a container use its already-resolved `workdir`.
    """
    return active().container_workdir

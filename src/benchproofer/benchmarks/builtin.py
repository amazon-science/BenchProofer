# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Adapters for public benchmarks published on the Hugging Face Hub.

Seven benchmarks, four shapes:

* **HumanEval** and **BigCodeBench** ship a stub with a docstring and a test
  program, so a task is one module plus an inline test.
* **MBPP** ships a natural-language prompt and assertions, with no stub.
* **GSM8K** ships a question and a numeric answer, and no code at all. It is here
  because a tool that can only formalize programming benchmarks is not general.
* **SWE-bench Verified**, **SWE-bench Lite** and **SWE-bench Pro** ship a repository
  at a commit and two lists of test ids, and are judged inside a container.

Every adapter pins its dataset to a commit and a SHA-256 per file, so two people
who run the same command read the same bytes. Nothing else in the tool knows which
of these a task came from.
"""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from ..core.plugin import Availability
from ..core.task import (
    OracleSpec,
    Reference,
    Repository,
    SourceFile,
    Task,
    TaskContext,
)
from ..errors import BenchmarkError
from ..util.digest import digest_json
from ..util.patch import touched_paths
from .base import Benchmark, BenchmarkInfo, LoadRequest
from .dataset import DatasetSpec, fetch, hub_availability, read_rows

__all__ = [
    "HubBenchmark",
    "bigcodebench",
    "gsm8k",
    "humaneval",
    "mbpp",
    "swebench_lite",
    "swebench_pro",
    "swebench_verified",
]

_DEF = re.compile(r"^def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
_FINAL_ANSWER = re.compile(r"####\s*(?P<value>[-\d.,/]+)")
#: SWE-bench publishes one image per instance, with ``__`` escaped because a Docker
#: tag may not contain it.
_IMAGE = "swebench/sweb.eval.x86_64.{slug}:latest"
#: SWE-bench Pro publishes one image per instance too, and names the tag in a column
#: of the dataset rather than deriving it, so the column is used verbatim.
_PRO_IMAGE = "jefzda/sweap-images:{tag}"
#: Where every SWE-bench Pro image keeps the working copy.
_PRO_ROOT = "/app"

#: Runs a unittest ``TestCases`` class and exits non-zero when it fails, which is
#: how BigCodeBench's test programs are meant to be driven.
_UNITTEST_MAIN = """

import sys as _sys
import unittest as _unittest

_suite = _unittest.defaultTestLoader.loadTestsFromName(
    "TestCases", _sys.modules["__main__"]
)
_result = _unittest.TextTestRunner(verbosity=0).run(_suite)
_sys.exit(0 if _result.wasSuccessful() else 1)
"""


class HubBenchmark(Benchmark):
    """Base class for a benchmark published as pinned files on the Hub."""

    #: The pinned dataset this adapter reads.
    spec: ClassVar[DatasetSpec]

    def availability(self) -> Availability:
        """Report whether the Hub client is importable."""
        return hub_availability()

    def load(self, request: LoadRequest) -> Iterator[Task]:
        """Fetch the pinned files and normalize every row."""
        paths = fetch(self.spec, request.cache_dir, offline=request.offline)
        rows = (row for path in paths for row in read_rows(path))
        return self.take(self._tasks(rows), request)

    def _tasks(self, rows: Iterator[dict[str, Any]]) -> Iterator[Task]:
        for index, row in enumerate(rows):
            task = self.normalize(row, index)
            if task is not None:
                yield task

    def normalize(self, row: dict[str, Any], index: int) -> Task | None:
        """Turn one upstream row into a task, or None to skip it."""
        raise NotImplementedError

    def _field(self, row: dict[str, Any], name: str) -> Any:
        if name not in row:
            raise BenchmarkError(f"{self.spec.pin}: row is missing field {name!r}")
        return row[name]


# ---------------------------------------------------------------------------
# Stub-and-test benchmarks
# ---------------------------------------------------------------------------


class HumanEvalBenchmark(HubBenchmark):
    """OpenAI HumanEval: 164 hand-written Python function tasks."""

    name: ClassVar[str] = "humaneval"
    spec: ClassVar[DatasetSpec] = DatasetSpec(
        repo_id="openai/openai_humaneval",
        revision="7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544",
        files=("openai_humaneval/test-00000-of-00001.parquet",),
        license="MIT",
        url="https://huggingface.co/datasets/openai/openai_humaneval",
        digests={
            "openai_humaneval/test-00000-of-00001.parquet": (
                "sha256:2f2871a15fbc95b6c683043359f4ed8e144c5a1c4f24f25f66bc51f598dfcfb6"
            )
        },
    )

    def info(self) -> BenchmarkInfo:
        """Describe HumanEval."""
        return BenchmarkInfo(
            name=self.name,
            title="HumanEval",
            summary="Function-level Python synthesis from a docstring, with unit tests.",
            url=self.spec.url,
            license=self.spec.license,
            oracle="inline-tests",
            size=164,
        )

    def normalize(self, row: dict[str, Any], index: int) -> Task:
        """One module, one stub, one test program."""
        prompt = str(self._field(row, "prompt"))
        entry = str(self._field(row, "entry_point"))
        tests = f"{self._field(row, 'test')}\n\ncheck({entry})\n"
        return Task(
            benchmark=self.name,
            task_id=str(self._field(row, "task_id")),
            statement=prompt,
            context=TaskContext(
                files=(SourceFile(path="solution.py", content=prompt),),
                entry_points=(entry,),
            ),
            reference=Reference(
                files=(
                    SourceFile(
                        path="solution.py",
                        content=prompt + str(self._field(row, "canonical_solution")),
                    ),
                ),
                symbols=(entry,),
            ),
            oracle=OracleSpec(kind="inline-tests", tests=(tests,), timeout_s=60),
            metadata={"dataset": self.spec.pin},
            source_digest=digest_json(row),
        )


class BigCodeBenchmark(HubBenchmark):
    """BigCodeBench: library-heavy Python tasks with unittest suites."""

    name: ClassVar[str] = "bigcodebench"
    spec: ClassVar[DatasetSpec] = DatasetSpec(
        repo_id="bigcode/bigcodebench",
        revision="b74c0d0bf70d2c0bc459be537895cca163007f1a",
        files=("data/v0.1.4-00000-of-00001.parquet",),
        license="Apache-2.0",
        url="https://huggingface.co/datasets/bigcode/bigcodebench",
        digests={
            "data/v0.1.4-00000-of-00001.parquet": (
                "sha256:d9a4965821c9507ebdfb551c288656b2d5fe553234f5183044333ca8a4018267"
            )
        },
    )

    def info(self) -> BenchmarkInfo:
        """Describe BigCodeBench."""
        return BenchmarkInfo(
            name=self.name,
            title="BigCodeBench v0.1.4",
            summary=(
                "Python tasks that compose third-party libraries, with unittest "
                "suites. Its oracle needs those libraries installed."
            ),
            url=self.spec.url,
            license=self.spec.license,
            oracle="inline-tests",
            size=1140,
        )

    def normalize(self, row: dict[str, Any], index: int) -> Task:
        """One module whose stub already carries its imports."""
        prompt = str(self._field(row, "complete_prompt"))
        stub = str(row.get("code_prompt") or prompt)
        entry = str(self._field(row, "entry_point"))
        tests = f"{self._field(row, 'test')}{_UNITTEST_MAIN}"
        libs = row.get("libs")
        return Task(
            benchmark=self.name,
            task_id=str(self._field(row, "task_id")),
            statement=prompt,
            context=TaskContext(
                files=(SourceFile(path="solution.py", content=stub),),
                entry_points=(entry,),
            ),
            reference=Reference(
                files=(
                    SourceFile(
                        path="solution.py",
                        content=prompt + str(self._field(row, "canonical_solution")),
                    ),
                ),
                symbols=(entry,),
            ),
            oracle=OracleSpec(kind="inline-tests", tests=(tests,), timeout_s=120),
            metadata={"dataset": self.spec.pin, "libs": libs},
            source_digest=digest_json(row),
        )


# ---------------------------------------------------------------------------
# Prompt-and-assertion benchmarks
# ---------------------------------------------------------------------------


class MbppBenchmark(HubBenchmark):
    """MBPP: short Python tasks stated in prose and checked by assertions."""

    name: ClassVar[str] = "mbpp"
    spec: ClassVar[DatasetSpec] = DatasetSpec(
        repo_id="google-research-datasets/mbpp",
        revision="4bb6404fdc6cacfda99d4ac4205087b89d32030c",
        files=("full/test-00000-of-00001.parquet",),
        license="CC-BY-4.0",
        url="https://huggingface.co/datasets/google-research-datasets/mbpp",
        digests={
            "full/test-00000-of-00001.parquet": (
                "sha256:566fd53060ffba5766dace1d1e2f4c38906781526de222b0dfbdbc325b696c77"
            )
        },
    )

    def info(self) -> BenchmarkInfo:
        """Describe MBPP."""
        return BenchmarkInfo(
            name=self.name,
            title="MBPP (test split)",
            summary=(
                "Prose task statements with assertion tests and no starting code, "
                "so the specification is written from the statement alone."
            ),
            url=self.spec.url,
            license=self.spec.license,
            oracle="inline-tests",
            size=500,
        )

    def normalize(self, row: dict[str, Any], index: int) -> Task:
        """No stub: the statement and the assertions are the whole task."""
        code = str(self._field(row, "code"))
        setup = str(row.get("test_setup_code") or "")
        asserts = [str(line) for line in self._field(row, "test_list")]
        program = "\n".join([part for part in (setup, *asserts) if part.strip()]) + "\n"
        return Task(
            benchmark=self.name,
            task_id=f"MBPP/{self._field(row, 'task_id')}",
            statement=str(self._field(row, "text")),
            context=TaskContext(entry_points=tuple(_DEF.findall(code))),
            reference=Reference(
                files=(SourceFile(path="solution.py", content=code),),
                symbols=tuple(_DEF.findall(code)),
            ),
            oracle=OracleSpec(kind="inline-tests", tests=(program,), timeout_s=60),
            metadata={
                "dataset": self.spec.pin,
                "challenge_tests": list(row.get("challenge_test_list") or ()),
            },
            source_digest=digest_json(row),
        )


class Gsm8kBenchmark(HubBenchmark):
    """GSM8K: grade-school word problems with a single numeric answer."""

    name: ClassVar[str] = "gsm8k"
    spec: ClassVar[DatasetSpec] = DatasetSpec(
        repo_id="openai/gsm8k",
        revision="740312add88f781978c0658806c59bc2815b9866",
        files=("main/test-00000-of-00001.parquet",),
        license="MIT",
        url="https://huggingface.co/datasets/openai/gsm8k",
        digests={
            "main/test-00000-of-00001.parquet": (
                "sha256:ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59"
            )
        },
    )

    def info(self) -> BenchmarkInfo:
        """Describe GSM8K."""
        return BenchmarkInfo(
            name=self.name,
            title="GSM8K (test split)",
            summary=(
                "Arithmetic word problems whose answer is a number, formalized as "
                "an arithmetic obligation rather than a program."
            ),
            url=self.spec.url,
            license=self.spec.license,
            oracle="answer",
            size=1319,
            languages=("natural-language",),
        )

    def normalize(self, row: dict[str, Any], index: int) -> Task | None:
        """The rationale is kept as metadata; the answer is the oracle."""
        rationale = str(self._field(row, "answer"))
        match = _FINAL_ANSWER.search(rationale)
        if match is None:
            return None
        answer = match.group("value").replace(",", "").strip()
        return Task(
            benchmark=self.name,
            task_id=f"GSM8K/test/{index:04d}",
            statement=str(self._field(row, "question")),
            language="natural-language",
            reference=Reference(answer=answer),
            oracle=OracleSpec(kind="answer", expected=answer),
            metadata={"dataset": self.spec.pin, "rationale": rationale},
            source_digest=digest_json(row),
        )


# ---------------------------------------------------------------------------
# Repository benchmarks
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Runner:
    """How one repository drives its test suite and reports the result.

    Most Python projects use pytest. A few use their own runner, which wants module
    labels rather than paths and prints a different report, so the adapter states
    which and the oracle reads it accordingly.

    The runner is pointed at the files the benchmark's test patch touches rather
    than at individual test ids, which is what these benchmarks' own reproduction code does.
    The declared ids remain the obligations; they are read back from the report.
    """

    command: tuple[str, ...]
    log_format: str = "pytest"
    #: What to pass the runner: the files the benchmark's test patch touches, or those
    #: files as dotted module labels.
    targets: Literal["files", "modules"] = "files"
    #: Shell lines the container needs before the command will work, such as the
    #: environment variables the project's own test script exports.
    setup: tuple[str, ...] = ()
    #: When set, this runner only drives tests under this path prefix. A task that
    #: requires one somewhere else belongs to a different runner and is skipped rather
    #: than handed to this one, whose report would then be about the wrong thing. A
    #: target elsewhere that no required test lives in, such as a fixture the test
    #: patch adds beside an integration target, is left out of the run.
    scope: str = ""


_PYTEST = Runner(command=("python", "-m", "pytest", "-rA", "--tb=no", "-p", "no:cacheprovider"))
#: Repositories in the SWE-bench family that are not driven by pytest. This mirrors
#: what the original benchmark's reproduction code does for them.
_RUNNERS: dict[str, Runner] = {
    "django/django": Runner(
        command=(
            "./tests/runtests.py",
            "--verbosity",
            "2",
            "--settings=test_sqlite",
            "--parallel",
            "1",
        ),
        log_format="unittest",
        targets="modules",
    ),
    "sympy/sympy": Runner(
        command=("bin/test", "-C", "--verbose"),
        log_format="sympy",
        targets="files",
    ),
}
#: Test files whose suites reach live services, such as Sphinx's linkcheck builder.
#: SWE-bench recorded their test lists with the network up, and under ``--tb=no`` an
#: offline failure carries no sign of the blocked connection for the oracle to
#: recognize, so a task that runs one declares the network.
_NEEDS_NETWORK = frozenset({"tests/test_build_linkcheck.py"})


class SweBenchmark(HubBenchmark):
    """Shared normalization for the SWE-bench family."""

    #: Number of instances, for the catalog.
    instances: ClassVar[int] = 0
    #: Human-readable variant name.
    variant: ClassVar[str] = ""

    def info(self) -> BenchmarkInfo:
        """Describe this SWE-bench variant."""
        return BenchmarkInfo(
            name=self.name,
            title=f"SWE-bench {self.variant}",
            summary=(
                "Real GitHub issues resolved by a patch to a Python repository, "
                "judged by the project's own test suite inside a container."
            ),
            url=self.spec.url,
            license=self.spec.license,
            oracle="docker",
            size=self.instances,
        )

    def normalize(self, row: dict[str, Any], index: int) -> Task:
        """A repository at a commit, a test patch, and two lists of test ids."""
        instance = str(self._field(row, "instance_id"))
        image = _IMAGE.format(slug=instance.replace("__", "_1776_"))
        repo = str(self._field(row, "repo"))
        runner = _RUNNERS.get(repo, _PYTEST)
        test_patch = str(self._field(row, "test_patch"))
        must_pass = _id_list(row, "FAIL_TO_PASS")
        must_keep = _id_list(row, "PASS_TO_PASS")
        targets = _targets(runner, test_patch, must_pass + must_keep)
        return Task(
            benchmark=self.name,
            task_id=instance,
            statement=str(self._field(row, "problem_statement")),
            context=TaskContext(
                repository=Repository(
                    url=f"https://github.com/{repo}",
                    commit=str(self._field(row, "base_commit")),
                    image=image,
                    subdir="/testbed",
                )
            ),
            reference=Reference(patch=str(self._field(row, "patch"))),
            oracle=OracleSpec(
                kind="docker",
                tests=must_pass,
                regression=must_keep,
                targets=targets,
                files=(SourceFile(path="tests.patch", content=test_patch),),
                setup=(
                    "source /opt/miniconda3/bin/activate 2>/dev/null || true",
                    "conda activate testbed 2>/dev/null || true",
                    "cd /testbed",
                    "git checkout -- . 2>/dev/null || true",
                ),
                command=runner.command,
                log_format=runner.log_format,
                image=image,
                network=any(path in _NEEDS_NETWORK for path in targets),
                timeout_s=1800,
            ),
            metadata={
                "dataset": self.spec.pin,
                "repo": repo,
                "version": row.get("version"),
                "environment_setup_commit": row.get("environment_setup_commit"),
                "difficulty": row.get("difficulty"),
            },
            source_digest=digest_json(row),
        )


class SweBenchVerified(SweBenchmark):
    """SWE-bench Verified: 500 instances screened by human annotators."""

    name: ClassVar[str] = "swebench-verified"
    variant: ClassVar[str] = "Verified"
    instances: ClassVar[int] = 500
    spec: ClassVar[DatasetSpec] = DatasetSpec(
        repo_id="princeton-nlp/SWE-bench_Verified",
        revision="c104f840cc67f8b6eec6f759ebc8b2693d585d4a",
        files=("data/test-00000-of-00001.parquet",),
        license="see the dataset card",
        url="https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified",
        digests={
            "data/test-00000-of-00001.parquet": (
                "sha256:a45b1fe4e2f0c8390b2b2938ac83e92ed5979000856808f3679c07812e9e6dcd"
            )
        },
    )


class SweBenchLite(SweBenchmark):
    """SWE-bench Lite: 300 instances chosen for a cheaper evaluation."""

    name: ClassVar[str] = "swebench-lite"
    variant: ClassVar[str] = "Lite"
    instances: ClassVar[int] = 300
    spec: ClassVar[DatasetSpec] = DatasetSpec(
        repo_id="princeton-nlp/SWE-bench_Lite",
        revision="6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2",
        files=("data/test-00000-of-00001.parquet",),
        license="see the dataset card",
        url="https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite",
        digests={
            "data/test-00000-of-00001.parquet": (
                "sha256:7a21f37b8bc179c7db5beeb14e88ac538ba283455c776e6b2535bbfb6e3551b4"
            )
        },
    )


#: How each SWE-bench Pro repository drives its suite, taken from the run script the
#: benchmark publishes per instance, since that is the command its two lists of test
#: ids were recorded under.
#:
#: A repository absent from this table is one whose tests Benchproofer cannot read: the
#: Go, JavaScript and TypeScript instances report through `go test`, mocha or jest,
#: and no reader in `benchproofer.oracles.summaries` understands those. Their rows are
#: skipped, because an oracle that cannot read its own report returns "undecided" for
#: every candidate, which is worse than declining the task.
_PRO_RUNNERS: dict[str, Runner] = {
    "internetarchive/openlibrary": Runner(
        command=("pytest", "-v", "--tb=short"),
        setup=(
            f"export PYTHONPATH={_PRO_ROOT}",
            f"export OL_CONFIG={_PRO_ROOT}/conf/openlibrary.yml",
        ),
    ),
    "qutebrowser/qutebrowser": Runner(
        # `--override-ini=addopts=` drops the project's coverage plugin and its
        # warnings-as-errors, neither of which is part of the question asked here.
        # `python -m pytest`, as the run scripts have it, puts the working copy on
        # `sys.path`, which conftest needs in an image with no installed qutebrowser.
        command=(
            "python",
            "-m",
            "pytest",
            "--override-ini=addopts=",
            "-v",
            "--disable-warnings",
            "--benchmark-disable",
        ),
        setup=(
            "export QT_QPA_PLATFORM=offscreen",
            # The checkout defaults to PyQt5 and some images ship only PyQt6, so the
            # wrapper and pytest-qt's API are set to whichever the image has.
            (
                'if python -c "import PyQt5.QtCore" 2>/dev/null; then '
                "export PYTEST_QT_API=pyqt5 QUTE_QT_WRAPPER=PyQt5; "
                'elif python -c "import PyQt6.QtCore" 2>/dev/null; then '
                "export PYTEST_QT_API=pyqt6 QUTE_QT_WRAPPER=PyQt6; fi"
            ),
            # The sandbox is turned off by its own variable: setting
            # `QTWEBENGINE_CHROMIUM_FLAGS` makes qutebrowser log a startup warning,
            # which its tests of that startup fail on.
            "export QTWEBENGINE_DISABLE_SANDBOX=1",
        ),
    ),
    "ansible/ansible": Runner(
        # Driven as the benchmark's own run scripts drive each image: `ansible-test
        # units` where pytest-xdist is installed (it passes `-n auto`, which pytest
        # without xdist rejects before any test runs) and the image's ansible-test
        # accepts the interpreter's version, and pytest directly otherwise. Either way
        # the ids are rooted at the repository, as the benchmark records them.
        #
        # The version is read off the interpreter on the path, the one each run script
        # names: the images span Python 3.8 to 3.12, naming another version fails where
        # it is not installed, and an older ansible-test reads `--python default` as
        # every installed version, a system one without pytest among them.
        #
        # `lib` and `test/lib` go first on PYTHONPATH, as the run scripts export them.
        # The package lives at `lib/ansible`, and some images also carry a non-editable
        # install of the base commit, which `import ansible` in a probe -- `conformance.py`
        # or `axioms.py`, which gets only the checkout's root prepended -- would reach.
        command=("bp_ansible_units",),
        setup=(
            f"export PYTHONPATH={_PRO_ROOT}/lib:{_PRO_ROOT}/test/lib:{_PRO_ROOT}",
            (
                "bp_ansible_units() { "
                "local v; "
                """v=$(python -c 'import sys; print("%d.%d" % sys.version_info[:2])'); """
                'if python -c "import xdist" 2>/dev/null && '
                f'{_PRO_ROOT}/bin/ansible-test units --python "$v" --help >/dev/null 2>&1; '
                f'then {_PRO_ROOT}/bin/ansible-test units --python "$v" --verbose "$@"; '
                'else python -m pytest -v -p no:cacheprovider "$@"; fi; }'
            ),
        ),
        scope="test/units/",
    ),
}


class SweBenchPro(HubBenchmark):
    """SWE-bench Pro: long-horizon issues from repositories held back from training.

    Instances span eleven repositories in four languages. This adapter covers the
    three Python ones, whose suites its container oracle can drive and whose reports
    it can read; `_PRO_RUNNERS` says what happens to the rest and why.
    """

    name: ClassVar[str] = "swebench-pro"
    spec: ClassVar[DatasetSpec] = DatasetSpec(
        repo_id="ScaleAI/SWE-bench_Pro",
        revision="7ab5114912baf22bb098818e604c02fe7ad2c11f",
        files=("data/test-00000-of-00001.parquet",),
        license="see the dataset card",
        url="https://huggingface.co/datasets/ScaleAI/SWE-bench_Pro",
        digests={
            "data/test-00000-of-00001.parquet": (
                "sha256:c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8"
            )
        },
    )

    def info(self) -> BenchmarkInfo:
        """Describe SWE-bench Pro, and how much of it this adapter reaches."""
        return BenchmarkInfo(
            name=self.name,
            title="SWE-bench Pro (Python instances)",
            summary=(
                "Long-horizon issues resolved by a patch that spans several files, "
                "judged by the project's own suite inside a container. The Go and "
                "JavaScript instances are skipped: their runners report in formats "
                "Benchproofer has no reader for."
            ),
            url=self.spec.url,
            license=self.spec.license,
            oracle="docker",
            size=266,
        )

    def normalize(self, row: dict[str, Any], index: int) -> Task | None:
        """A repository at a commit, a prepared image, and two lists of test ids."""
        repo = str(self._field(row, "repo"))
        runner = _PRO_RUNNERS.get(repo)
        tests = _id_list(row, "fail_to_pass")
        regression = _id_list(row, "pass_to_pass")
        if runner is None or not all(t.startswith(runner.scope) for t in tests + regression):
            return None
        # Some rows list node ids among the files, and a runner such as ansible-test reads
        # each target as a pattern, which a parameter in brackets breaks; the file holds
        # the test either way, and the report is read back by id.
        targets = tuple(
            dict.fromkeys(
                path.split("::", 1)[0]
                for path in _id_list(row, "selected_test_files_to_run")
                if path.startswith(runner.scope)
            )
        )
        if not targets:
            return None
        image = _PRO_IMAGE.format(tag=self._field(row, "dockerhub_tag"))
        return Task(
            benchmark=self.name,
            task_id=str(self._field(row, "instance_id")),
            statement=_pro_statement(row),
            context=TaskContext(
                repository=Repository(
                    url=f"https://github.com/{repo}",
                    commit=str(self._field(row, "base_commit")),
                    image=image,
                    subdir=_PRO_ROOT,
                )
            ),
            reference=Reference(patch=str(self._field(row, "patch"))),
            oracle=OracleSpec(
                kind="docker",
                tests=tests,
                regression=regression,
                targets=targets,
                # The benchmark's own preparation ends by checking the tests out of
                # the commit that fixed the issue, so there is no test patch to apply;
                # the patch is kept in `metadata`, for the prompts that show the tests.
                setup=(
                    f"cd {_PRO_ROOT}",
                    *_lines(str(self._field(row, "before_repo_set_cmd"))),
                    *runner.setup,
                ),
                command=runner.command,
                log_format=runner.log_format,
                image=image,
                timeout_s=1800,
            ),
            metadata={
                "dataset": self.spec.pin,
                "repo": repo,
                "version": row.get("version"),
                "test_patch": str(row.get("test_patch") or ""),
            },
            source_digest=digest_json(row),
        )


def _pro_statement(row: dict[str, Any]) -> str:
    """Assemble the task as SWE-bench Pro states it.

    Pro states an issue in three parts: the report, the behaviour a fix has to have,
    and the interface it has to expose. All three are what the benchmark hands a
    solver, and the last two are what a specification can be written from, so all
    three are kept. None of them is the reference patch. A part the dataset stores as a JSON
    string literal, quotes and escapes included, is read as the text it encodes.
    """
    parts = [_unquoted(str(row.get("problem_statement") or ""))]
    for heading, field in (("Requirements", "requirements"), ("Interface", "interface")):
        body = _unquoted(str(row.get(field) or ""))
        if body:
            parts.append(f"## {heading}\n\n{body}")
    return "\n\n".join(part.strip() for part in parts if part.strip()) + "\n"


def _unquoted(text: str) -> str:
    """``text`` stripped, and decoded where the whole of it is one JSON string literal."""
    text = text.strip()
    if len(text) < 2 or not (text.startswith('"') and text.endswith('"')):
        return text
    try:
        decoded = json.loads(text)
    except ValueError:
        return text
    return decoded.strip() if isinstance(decoded, str) else text


def _lines(script: str) -> tuple[str, ...]:
    """The non-empty lines of a shell fragment stored as one string."""
    return tuple(line.strip() for line in script.splitlines() if line.strip())


def _targets(runner: Runner, test_patch: str, ids: tuple[str, ...]) -> tuple[str, ...]:
    """Work out what to hand the runner.

    The test patch names the files the benchmark added its tests to. A patch that
    only adds a fixture names no source file, so the declared ids are used as the
    fallback source of file names; without one the runner would be handed nothing
    and would collect the entire suite.
    """
    paths = touched_paths(test_patch, source_only=True) or _id_files(ids)
    if runner.targets == "files":
        return paths
    return tuple(
        path.removesuffix(".py").removeprefix("tests/").replace("/", ".") for path in paths
    )


def _id_files(ids: tuple[str, ...]) -> tuple[str, ...]:
    """The distinct files named by a list of pytest node ids."""
    found: dict[str, None] = {}
    for node in ids:
        head = node.split("::", 1)[0]
        if head.endswith(".py"):
            found.setdefault(head, None)
    return tuple(found)


def _id_list(row: dict[str, Any], field: str) -> tuple[str, ...]:
    """Read a list of names that a row stores as one string.

    SWE-bench writes JSON. SWE-bench Pro writes the repr of a Python list, whose
    single quotes JSON rejects. Both are literals, and are read as literals: nothing
    in a dataset is evaluated.
    """
    value = row.get(field)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(value)
            except (SyntaxError, ValueError) as exc:
                raise BenchmarkError(f"{field} is not a list literal: {exc}") from exc
    if value is None:
        return ()
    if isinstance(value, str):
        raise BenchmarkError(f"{field} holds a string where a list of names belongs")
    return tuple(str(item) for item in value)


def humaneval() -> HumanEvalBenchmark:
    """Entry point factory."""
    return HumanEvalBenchmark()


def mbpp() -> MbppBenchmark:
    """Entry point factory."""
    return MbppBenchmark()


def bigcodebench() -> BigCodeBenchmark:
    """Entry point factory."""
    return BigCodeBenchmark()


def gsm8k() -> Gsm8kBenchmark:
    """Entry point factory."""
    return Gsm8kBenchmark()


def swebench_verified() -> SweBenchVerified:
    """Entry point factory."""
    return SweBenchVerified()


def swebench_lite() -> SweBenchLite:
    """Entry point factory."""
    return SweBenchLite()


def swebench_pro() -> SweBenchPro:
    """Entry point factory."""
    return SweBenchPro()

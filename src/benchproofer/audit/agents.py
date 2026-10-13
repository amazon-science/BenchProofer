# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The review as agent sessions: one per auditor, each in a workspace of its own.

This is how `verified-swebench` reviews. Each question is put to its own session on the
reviewing model, and the session does what a reviewer does: it reads the bundle and the
repository, writes an attack, puts it to the checker, runs it against the real code, and
tries again. What comes back is submissions, defects, fuzzers, judgments and rulings, which
the gates judge on the same terms whoever wrote them.

An auditor's workspace holds a copy of the bundle laid out as a bundle root, a copy of the
repository, a scratch directory, and a `tools` script (`audit.tools`) that runs the checker,
the gates a submission is judged by, and the task's environment. The disclosure auditor is the
exception: it reads blind, so its workspace holds the specification a solver is shown and
the task statement, and neither the implementation nor the golden patch.

Nothing a session writes is taken on trust. A submission is read back from the path the
session names, and filed only if it carries the shipped specification byte for byte and is
not a repeat of one already on record; a repository patch is filed only if it is a diff. A
fuzzer is filed only against a callee the specification assumes. Every one is then re-run by
the gates over the bundle itself.

Three things carry over from the reviews before. The attack auditor is shown what the review
before it filed, with what the gates ruled: while the specification it attacked stands,
those submissions stay on record and the auditor writes new ones; once a repair changed it,
they are not run again, and the auditor first writes again each attack the gates ruled a
weakness, unless the repair's entry for it shows it was not a defect. An auditor whose last
judgment found fault is shown what it found, each finding with the repair's entry for it,
and judges a decline: a finding the repair declined with evidence is withdrawn if the
evidence holds and kept, saying why not, if it does not, and one the repair neither
resolved nor declined stays open. And the faithfulness auditor is shown what the review found
in this run's earlier rounds, so that a finding asking for what an earlier one called too
strict is seen as one.

The attack validation auditor is asked only about submissions the gates have run: the attacks
and controls that cannot be determined by execution and that the current verdicts of the two
submission gates list without a ruling (`unruled`), each with what the gates established,
beside the faithfulness auditor's coverage table.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Any, get_args

from ..backends.base import Backend
from ..config import Settings
from ..core import material, rounds, sites, variant, witness, workcopy
from ..core.axioms import AFTER_REFERENCE, PROTOCOL, declared_in
from ..core.axioms import HARNESS as AXIOM_HARNESS
from ..core.bundle import (
    PRESERVING,
    RULINGS,
    AuditRole,
    Bundle,
    Coverage,
    Defect,
    Fuzzer,
    Judgment,
    Operation,
    OperationKind,
    Review,
    Ruling,
    Submission,
    SubmissionKind,
)
from ..core.differential import HARNESS as DIFFERENTIAL_HARNESS
from ..core.differential import TRANSLITERATED, arguments
from ..core.readings import readings, ruling_reads
from ..core.scripts import SCRATCH, lay_out, tools_rules
from ..core.task import Task
from ..errors import BenchproofError
from ..llm.agentic import EDIT, READ_ONLY, AgentSession, SessionSpec, StepOutcome
from ..llm.base import Provider
from ..log import logger
from ..util.fsio import read_text, read_text_or_empty, write_text
from ..util.patch import is_diff
from . import prompts
from .session import (
    _KIND_NOTE,
    ASKS,
    JUDGED_ROLES,
    LANE_OF,
    LANE_READS,
    LANES,
    VERDICTS,
    Audit,
    Filed,
    Fuzzed,
    Lane,
    _among,
    _author,
    _highest,
    _impl,
    _stamped,
    _system,
    added_block,
    assumed,
    attack_stands,
    axioms_digest,
    examined,
    kept_fuzzers,
    roles_for,
    unattacked,
    unruled,
)

__all__ = ["Reviewers"]

log = logger(__name__)

#: How many of a session's own findings, and of the repair's words about them, a later
#: session of the same auditor is shown.
FINDING_LIMIT = 12
#: The schema fields the auditors' payloads share: a submitted file's path, and a judgment.
_FILE = {"type": "string", "description": "the file's path under the scratch directory"}
_VERDICT = {"type": "string", "enum": list(VERDICTS), "description": "the judgment"}
_SUMMARY = {"type": "string", "description": "one sentence saying why"}
_FINDINGS = {
    "type": "array",
    "items": {"type": "string"},
    "description": "one entry per defect, with the input that shows it; none when sound",
}
_CHECKED = {
    "type": "array",
    "items": {"type": "string"},
    "description": "one entry per thing you checked and found clean, with what you ran",
}
#: A control's refutation witness, which only a checker that needs one to read a refusal asks
#: for (`Backend.witness_required`); the control's witness test goes with it.
_REFUTATION = "refutation"
#: What an auditor hands over through the submit tool: an auditor that files programs hands over
#: files as well as fields, and a judging auditor only the fields.
_HANDOVER = {
    "files": (
        "What is checked is what you hand over through the submit tool: files you wrote in "
        "the scratch directory, named by path, and the fields it asks for, each re-checked "
        "as above, so your submission is evidence, not a verdict."
    ),
    "fields": (
        "What is recorded is what you hand over through the submit tool: the fields it asks "
        "for. No file of yours is handed over, so a finding states in its own words what "
        "shows it."
    ),
}
_FIELDS: dict[Lane, tuple[dict[str, Any], tuple[str, ...]]] = {
    "attack": (
        {
            "attacks": {
                "type": "array",
                "description": "every wrong implementation you wrote",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": _FILE,
                        "claim": {
                            "type": "string",
                            "description": "what it gets wrong, and on which input",
                        },
                        "patch": {
                            "type": "string",
                            "description": (
                                "the path of its equivalent patch; needed when it cannot "
                                "run as written or conformance.py cannot decide it, and "
                                "run whenever it is filed"
                            ),
                        },
                        "test": {
                            "type": "string",
                            "description": (
                                "the path of its witness test, a Python program that passes "
                                "on the fixed code and fails with its equivalent patch"
                            ),
                        },
                        "cites": {
                            "type": "string",
                            "description": (
                                "what its witness test checks: the statement's sentence, "
                                "quoted, or the id of the FAIL_TO_PASS test, or of the "
                                "PASS_TO_PASS test the test patch adds or edits"
                            ),
                        },
                    },
                    "required": ["file", "claim"],
                },
            },
            "controls": {
                "type": "array",
                "description": "every correct implementation you wrote",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": _FILE,
                        "claim": {
                            "type": "string",
                            "description": (
                                "how it computes the result, and how that differs; for one "
                                "the checker still refuses, what you tried"
                            ),
                        },
                        _REFUTATION: {
                            "type": "string",
                            "description": (
                                "for one the checker refuses, the path of its refutation "
                                "witness, a claim proved at one input"
                            ),
                        },
                        "test": {
                            "type": "string",
                            "description": (
                                "the path of its witness test, a Python program that passes "
                                "where the fixed code returns what it returns at the "
                                "witness's input"
                            ),
                        },
                    },
                    "required": ["file", "claim"],
                },
            },
            "defects": {
                "type": "array",
                "description": (
                    "every defect you showed by running code that no attack of yours shows"
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "defect": {"type": "string", "description": "what is wrong"},
                        "function": {
                            "type": "string",
                            "description": (
                                "the function conformance.py compares, by the name it prints"
                            ),
                        },
                        "input": {
                            "type": "string",
                            "description": (
                                "the arguments that function is called with, as a Python "
                                "tuple literal"
                            ),
                        },
                        "repository": {
                            "type": "string",
                            "description": "what the repository does on it, as you ran it",
                        },
                        "specification": {
                            "type": "string",
                            "description": "what the specification states on it",
                        },
                    },
                    "required": ["defect", "function", "input", "repository", "specification"],
                },
            },
        },
        ("attacks", "controls"),
    ),
    "fuzz": (
        {
            "fuzzers": {
                "type": "array",
                "description": "one program per unchanged callee",
                "items": {
                    "type": "object",
                    "properties": {
                        "callee": {"type": "string", "description": "the callee it attacks"},
                        "file": _FILE,
                        "claim": {"type": "string", "description": "what it tests"},
                    },
                    "required": ["callee", "file"],
                },
            },
        },
        ("fuzzers",),
    ),
    "faithfulness": (
        {
            "verdict": _VERDICT,
            "summary": _SUMMARY,
            "coverage": {
                "type": "array",
                "description": "one row per behavior of a function the fix changes",
                "items": {
                    "type": "object",
                    "properties": {
                        "behavior": {
                            "type": "string",
                            "description": "what the fixed code does, for which inputs",
                        },
                        "tested_by": {
                            "type": "string",
                            "description": (
                                "the FAIL_TO_PASS test, or the PASS_TO_PASS test the test "
                                "patch adds or edits, that checks it, by its id; empty, "
                                "not 'none', when none does"
                            ),
                        },
                        "covered_by": {
                            "type": "string",
                            "description": "the obligation stating it, quoted; empty if none",
                        },
                        "note": {"type": "string"},
                    },
                    "required": ["behavior", "tested_by", "covered_by"],
                },
            },
            "findings": _FINDINGS,
            "checked": _CHECKED,
        },
        ("verdict", "summary", "coverage"),
    ),
    "equivalence": (
        {
            "verdict": _VERDICT,
            "summary": _SUMMARY,
            "operations": {
                "type": "array",
                "description": "one entry per operation of the implementation",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {
                            "type": "string",
                            "enum": list(get_args(OperationKind)),
                        },
                        "detail": {
                            "type": "string",
                            "description": (
                                "the implementation's operation, and the golden patch's"
                            ),
                        },
                    },
                    "required": ["kind", "detail"],
                },
            },
            "findings": _FINDINGS,
            "checked": _CHECKED,
        },
        ("verdict", "summary", "operations"),
    ),
    "disclosure": (
        {"verdict": _VERDICT, "summary": _SUMMARY, "findings": _FINDINGS, "checked": _CHECKED},
        ("verdict", "summary"),
    ),
    "validation": (
        {
            "rulings": {
                "type": "array",
                "description": "one ruling per attack or control you were shown",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "the id of the attack or control",
                        },
                        "ruling": {
                            "type": "string",
                            "enum": [*RULINGS["weakness"], *RULINGS["control"]],
                            "description": (
                                "for an attack, succeeds or fails; for a control, too_strong, "
                                "unproved or incorrect"
                            ),
                        },
                        "input": {
                            "type": "string",
                            "description": (
                                "the input the ruling rests on; for an attack with a "
                                "witness test, the input the test runs and the behaviour it "
                                "checks there"
                            ),
                        },
                        "rests_on": {
                            "type": "string",
                            "description": (
                                "the sentence of the statement, quoted, the id of the test, or "
                                "the obligation, quoted, that the ruling rests on; for an "
                                "attack with a witness test, what the test cites"
                            ),
                        },
                        "why": {
                            "type": "string",
                            "description": "what you ran, and what it showed",
                        },
                    },
                    "required": ["id", "ruling", "input", "rests_on"],
                },
            },
        },
        ("rulings",),
    ),
}


class Reviewers:
    """Review one bundle with one agent session per auditor.

    ``provider`` is the reviewing provider, used for the review's identity only, so that the
    reviewer is named as the bundle's author is, by provider and model; ``session`` runs on
    that provider's model.
    """

    def __init__(
        self,
        *,
        session: AgentSession,
        provider: Provider,
        backend: Backend,
        settings: Settings,
        oracle: object | None = None,
    ) -> None:
        self.session = session
        self.provider = provider
        self.backend = backend
        self.settings = settings
        self.oracle = oracle

    def run(self, bundle: Bundle, task: Task, lanes: Sequence[Lane] = LANES) -> Audit:
        """Review one bundle, asking only the auditors named.

        An auditor that ended without submitting files nothing, and what that auditor filed
        before is kept: the gates then report it as stale or missing, which is the
        accurate account of a review that did not happen. The attack validation auditor rules
        on the attacks and controls that cannot be determined by execution, as the verdicts
        list them when this review starts (`_cases`), so `pipeline.audit.review` asks it on its
        own, once the gates have run what the others filed.

        Raises:
            BundleError: The bundle has no solution file to review, or its recorded
                review is unreadable.
            ProviderError: An auditor's session could not be started at all, which is the
                tool failing rather than a review finding nothing (`_session`).
        """
        solution = bundle.solution()
        recorded = bundle.audit()
        digests = readings(bundle, self.backend)
        notes: list[str] = []
        sessions: list[dict[str, Any]] = []
        root = bundle.scratch(self.settings.cache_dir, "review")
        earlier = recorded.submissions if recorded is not None else ()
        # What the attack auditor filed against the specification as it stands is judged
        # beside what it files now; what it filed against another is replaced by it.
        stands = attack_stands(recorded, digests)
        standing = earlier if stands else ()
        kept = kept_fuzzers(recorded, solution, self.backend)

        submissions: tuple[Filed, ...] = ()
        # What the attack auditor showed that is not an attack: an earlier review's stays on
        # record as its submissions do, beside this review's while the specification stands.
        # One filed with no function `conformance.py` can be handed its input on is dropped.
        defects = tuple(
            item for item in (recorded.defects if recorded is not None else ()) if item.function
        )
        fuzzers: tuple[Fuzzed, ...] = ()
        rulings = recorded.rulings if recorded is not None else ()
        cases = _cases(bundle, recorded)
        judgments: list[Judgment] = []
        ran: list[str] = []
        roles = roles_for(task)
        for lane in lanes:
            if lane in ("faithfulness", "equivalence", "disclosure") and lane not in roles:
                notes.append(
                    f"the task ships no golden patch, so the review was not asked the "
                    f"{lane} question; its gate reports it as undecided"
                )
                continue
            if lane == "fuzz" and not unattacked(solution, self.backend, kept):
                continue
            if lane == "validation" and not cases:
                continue
            outcome = self._session(
                lane,
                bundle,
                task,
                solution,
                recorded,
                kept,
                root,
                notes,
                judgments,
                cases,
            )
            if outcome is None:
                continue
            workspace, result = outcome
            sessions.append(_record(lane, result))
            payload = result.payload
            if lane == "validation":
                # Each attack or control it was shown counts as asked, ruled on or not.
                rulings = _ruled(payload, cases, recorded, digests)
            if payload is None:
                detail = result.detail or "no detail"
                notes.append(
                    f"{lane}: the session ended without submitting ({detail}), so this "
                    "auditor filed nothing"
                )
                continue
            ran.append(lane)
            if lane == "attack":
                submissions = self._filed(
                    payload, workspace, solution, bundle, earlier, standing, notes
                )
                defects = (
                    *(defects if stands else ()),
                    *_defects(payload, _compared(bundle), notes),
                )
            elif lane == "fuzz":
                fuzzers = self._fuzzers(payload, workspace, solution, kept, notes)
            elif lane != "validation":
                judgment = _judgment(lane, payload)
                if judgment is not None:
                    judgments.append(_stamped(judgment, digests))

        asked = {judgment.role for judgment in judgments}
        return Audit(
            task_key=task.key,
            backend=self.backend.name,
            provider=self.provider.name,
            model=self.provider.config.model,
            author=_author(bundle),
            submissions=submissions,
            kept=standing if "attack" in ran else earlier,
            defects=defects,
            fuzzers=fuzzers,
            kept_fuzzers=kept,
            rulings=rulings,
            judgments=tuple(judgments),
            kept_judgments=tuple(
                judgment
                for judgment in (recorded.judgments if recorded else ())
                if judgment.role not in asked
            ),
            examined=examined(recorded, digests, [lane for lane in ran if lane in LANE_READS]),
            sessions=tuple(sessions),
            notes=tuple(notes),
        )

    # ---- one auditor -------------------------------------------------------

    def _session(
        self,
        lane: Lane,
        bundle: Bundle,
        task: Task,
        solution: str,
        recorded: Review | None,
        kept: tuple[Fuzzer, ...],
        root: Path,
        notes: list[str],
        judged: Sequence[Judgment],
        cases: Sequence[tuple[Submission, str]],
    ) -> tuple[Path, StepOutcome] | None:
        """Lay out one auditor's workspace and run its session.

        ``judged`` are the judgments this review reached before, whose coverage table the attack
        validation auditor is shown in place of the one on record, and ``cases`` what it rules
        on (`_cases`).

        Returns:
            Where the session ran and what it reported; or None where the workspace could not
            be laid out, which is noted and leaves the auditor unasked.

        Raises:
            ProviderError: The session could not be started at all. That is the tool
                failing rather than a reviewer finding nothing, and a review recorded as
                though the auditor had reported would be read as an auditor that did; the run
                ends on it instead.
        """
        workspace = root / lane
        try:
            if lane == "disclosure":
                shutil.rmtree(workspace, ignore_errors=True)
                (workspace / SCRATCH).mkdir(parents=True)
                fields = self._blind(workspace, bundle, task, solution)
                tools = READ_ONLY
            else:
                fields = self._laid_out(workspace, bundle, task, lane)
                tools = EDIT
            fields.update(self._fields(lane, task, solution, recorded, kept, bundle))
            if lane == "validation":
                write_text(workspace / STATEMENT, task.statement or material.NOTHING)
                fields["cases"] = _cases_block(cases, fields["bundle"])
                fields["coverage"] = _coverage_block(bundle, recorded, judged, self.backend)
            prompt = prompts.render(f"agent-{lane}", **fields)
        except BenchproofError as exc:
            notes.append(f"{lane}: the workspace could not be laid out ({exc})")
            return None
        schema, required = _schema(lane, self.backend)
        request = SessionSpec(
            system=prompts.render(
                "agent-system",
                review=_system(self.backend, lane),
                handover=_HANDOVER[
                    "fields" if lane in JUDGED_ROLES or lane == "validation" else "files"
                ],
            ),
            prompt=prompt,
            cwd=workspace,
            submit="review",
            fields=schema,
            required=required,
            tools=tools,
            max_turns=self.settings.review_turns,
            timeout_s=self.settings.review_timeout_s,
            report=prompts.render("agent-report"),
        )
        result = self.session.run(request)
        log.info(
            "review %s of %s: %d turn(s), %d tool use(s), %.0fs%s",
            lane,
            task.key,
            result.turns,
            result.tool_uses,
            result.duration_s,
            f", {result.detail}" if result.detail else "",
        )
        return workspace, result

    def _laid_out(
        self, workspace: Path, bundle: Bundle, task: Task, lane: Lane
    ) -> dict[str, str]:
        """A copy of the bundle, the repository and the tests, and the tools over them.

        Only the copies of the attack auditor and the attack validation auditor keep the review
        on record, whose submissions each is shown, and what the gates made of them. A judging
        auditor reads the bundle afresh: an earlier verdict beside the question is a verdict to
        copy rather than a reason to look.
        """
        copy = lay_out(workspace, task, self.backend.name, self.settings)
        shutil.copytree(bundle.root, copy.root, dirs_exist_ok=True)
        if lane not in ("attack", "validation"):
            shutil.rmtree(copy.audit_dir, ignore_errors=True)
            _unjudged(copy)
        repository = workspace / "repository"
        found = workcopy.materialize(
            task,
            into=bundle.scratch(self.settings.cache_dir, "review-workcopy"),
            oracle=self.oracle,
        )
        shutil.copytree(found.root, repository, symlinks=True)
        tests = workspace / "tests"
        for source in task.oracle.files:
            if source.content:
                write_text(tests / source.path, source.content)
        patch = material.test_patch(task)
        if patch and not (tests / "tests.patch").exists():
            write_text(tests / "tests.patch", patch)
        for index, program in enumerate(_programs(task), 1):
            write_text(tests / f"program-{index}.py", program)
        return {
            "task": task.key,
            "bundle": copy.root.relative_to(workspace).as_posix(),
            "solution": bundle.solution_path.name,
            "repository": "repository",
            "scratch": SCRATCH,
            "tools": "./tools",
            "tools_rules": tools_rules(
                self.settings,
                task,
                self.backend,
                session_s=self.settings.review_timeout_s,
            ),
        }

    def _blind(
        self, workspace: Path, bundle: Bundle, task: Task, solution: str
    ) -> dict[str, str]:
        """A solver's view, and neither the implementation nor the golden patch.

        The specification as a solver reads it, the statement, and the code before the fix,
        which a solver has in front of it: each function the golden patch changes, whole, as
        it read before the fix, from the repository the other auditors are given. Content that
        code already has is public, so the question is what the specification reveals
        beyond it.
        """
        write_text(workspace / "spec.txt", self.backend.spec_view(solution))
        write_text(workspace / "statement.md", material.statement_block(task))
        found = workcopy.materialize(
            task,
            into=bundle.scratch(self.settings.cache_dir, "review-workcopy"),
            oracle=self.oracle,
        )
        fix = workcopy.touched(task, found, task.reference.patch or "")
        write_text(
            workspace / "before.md",
            material.pre_fix_block(task, fix) or "(the task ships none)",
        )
        return {
            "task": task.key,
            "spec": "spec.txt",
            "statement": "statement.md",
            "before": "before.md",
        }

    def _fields(
        self,
        lane: Lane,
        task: Task,
        solution: str,
        recorded: Review | None,
        kept: tuple[Fuzzer, ...],
        bundle: Bundle,
    ) -> dict[str, str]:
        """What one auditor's prompt says beyond the workspace."""
        regions = variant.rule(variant.owned(solution, self.backend))
        if lane == "attack":
            return {
                "tests": _tests_block(task, bundle),
                "attacks": str(max(1, self.settings.audit_attacks)),
                "controls": str(max(1, self.settings.audit_controls)),
                "min_controls": str(max(1, self.settings.audit_min_controls)),
                "regions": regions,
                "kind_note": _KIND_NOTE[self.backend.kind],
                "on_record": _on_record_block(
                    recorded, attack_stands(recorded, readings(bundle, self.backend)), bundle
                ),
                "refutation": _refutation_block(solution, self.backend),
                "compared": _compared_block(bundle),
            }
        if lane == "fuzz":
            return {
                "callees": "\n".join(
                    f"* `{callee}`" for callee in unattacked(solution, self.backend, kept)
                ),
                "protocol": PROTOCOL,
                "reference": AFTER_REFERENCE if task.reference.patch else "",
                "witnesses": _witnesses_block(bundle),
            }
        if lane == "disclosure":
            return {}
        if lane == "validation":
            return {
                "statement": STATEMENT,
                "tests": _tests_block(task, bundle),
                "fix": material.reference_block(task),
                "regions": regions,
            }
        fields = {
            "findings": _findings_block(lane, recorded, bundle),
            "regions": regions,
        }
        if lane in ("equivalence", "faithfulness"):
            # Both state the rule for callees, which this run's rounds relax for the callees
            # they list (`rounds.eligible`).
            fields["inputs_rules"] = rounds.inputs_rules(
                rounds.eligible(rounds.directory(bundle, self.settings.cache_dir), self.backend)
            )
        if lane == "equivalence":
            fields["added"] = added_block(bundle, self.backend)
            fields["modeled"] = _modeled_block(solution, self.backend)
            fields["port"] = _port_block(bundle, self.backend)
            fields["conformance"] = _undiscriminating_block(bundle)
            fields["programs"] = _programs_block(bundle, self.settings.cache_dir)
        if lane == "faithfulness":
            changed = sites.changed(task, bundle.manifest().provenance.get(sites.RECORD))
            fields["tests"] = _tests_block(task, bundle)
            fields["fix"] = material.reference_block(task)
            fields["functions"] = (
                material.changed_block(task, changed.golden) or "* (the fix is not a diff)"
            )
            fields["earlier"] = _earlier_block(bundle, self.settings.cache_dir)
        return fields

    # ---- what came back -------------------------------------------------

    def _filed(
        self,
        payload: dict[str, Any],
        workspace: Path,
        solution: str,
        bundle: Bundle,
        earlier: tuple[Submission, ...],
        standing: tuple[Submission, ...],
        notes: list[str],
    ) -> tuple[Filed, ...]:
        """Read back the attack auditor's files, keeping those that can be evidence.

        A file repeating the shipped implementation, or one of those ``standing`` beside
        it, is not filed. Ids are numbered past those of every ``earlier`` submission, so
        none names two implementations within a run.
        """
        known = [_impl(solution, self.backend)]
        for item in standing:
            try:
                known.append(_impl(bundle.submission_source(item), self.backend))
            except BenchproofError:
                continue
        filed: list[Filed] = []
        for kind, noun in ASKS:
            index = _highest([item for item in earlier if item.kind == kind]) + 1
            for entry in _entries(payload.get(f"{noun}s")):
                source = _named(workspace, entry.get("file"), notes, noun)
                if source is None or not self._admissible(source, solution, known, noun, notes):
                    continue
                patch = ""
                if kind == "weakness" and str(entry.get("patch") or "").strip():
                    patch = _named(workspace, entry.get("patch"), notes, "patch") or ""
                    if patch and not is_diff(patch):
                        notes.append(
                            f"{noun}-{index}: the patch filed with it is not a unified diff, "
                            "so it was filed without one"
                        )
                        patch = ""
                known.append(_impl(source, self.backend))
                # A control's witness goes with a refutation witness, which only a checker
                # whose refusal needs one to say anything reads.
                attack = kind == "weakness"
                witnessed = attack or self.backend.witness_required
                filed.append(
                    Filed(
                        id=f"{noun}-{index}",
                        kind=kind,
                        claim=str(entry.get("claim") or ""),
                        file=f"{noun}-{index}{self.backend.extension}",
                        source=source,
                        patch=patch,
                        test=(
                            _optional(workspace, entry, "test", notes, "witness test")
                            if witnessed
                            else ""
                        ),
                        cites=str(entry.get("cites") or "").strip() if attack else "",
                        refutation=(
                            ""
                            if attack or not witnessed
                            else _optional(
                                workspace, entry, _REFUTATION, notes, "refutation witness"
                            )
                        ),
                    )
                )
                index += 1
        if all(item.kind != "weakness" for item in filed) and all(
            item.kind != "weakness" for item in standing
        ):
            notes.append(
                "the review filed no attack, so audit.spec_completeness (the completeness "
                "gate) has nothing to re-run"
            )
        return tuple(filed)

    def _admissible(
        self, source: str, solution: str, known: list[str], noun: str, notes: list[str]
    ) -> bool:
        """Whether a submitted file can be evidence: readable, the shipped spec, no repeat."""
        try:
            body = _impl(source, self.backend)
        except BenchproofError as exc:
            notes.append(
                f"a submitted {noun} has no readable marker regions ({exc}), so it was not "
                "filed"
            )
            return False
        if not self.backend.same_spec(solution, source):
            notes.append(
                f"a submitted {noun} has a specification other than the shipped one, so "
                "it was not filed"
            )
            return False
        if _among(body, known, self.backend):
            notes.append(
                f"a submitted {noun} repeats an implementation already on record, so it was "
                "not filed"
            )
            return False
        return True

    def _fuzzers(
        self,
        payload: dict[str, Any],
        workspace: Path,
        solution: str,
        kept: tuple[Fuzzer, ...],
        notes: list[str],
    ) -> tuple[Fuzzed, ...]:
        """Read back the fuzz auditor's programs, one per callee it was asked to attack."""
        known = set(assumed(solution, self.backend))
        wanted = set(unattacked(solution, self.backend, kept))
        against = axioms_digest(solution, self.backend)
        index = _highest(kept) + 1
        written: list[Fuzzed] = []
        for entry in _entries(payload.get("fuzzers")):
            callee = str(entry.get("callee") or "")
            if callee not in known:
                notes.append(
                    f"a fuzzer names {callee!r}, which the specification does not assume"
                )
                continue
            if callee not in wanted:
                continue
            source = _named(workspace, entry.get("file"), notes, "fuzzer")
            if source is None:
                continue
            written.append(
                Fuzzed(
                    id=f"fuzz-{index}",
                    callee=callee,
                    claim=str(entry.get("claim") or ""),
                    source=source,
                    against=against,
                )
            )
            wanted.discard(callee)
            index += 1
        return tuple(written)


def _judgment(role: AuditRole, payload: dict[str, Any]) -> Judgment | None:
    """A judgment from a judging auditor's payload, or None when it carries no verdict."""
    verdict = str(payload.get("verdict") or "").strip().lower()
    if verdict not in VERDICTS:
        return None
    findings = _strings(payload.get("findings"))
    operations: tuple[Operation, ...] = ()
    if role == "equivalence":
        operations = tuple(
            Operation(
                kind=kind if kind in PRESERVING else "changed",  # type: ignore[arg-type]
                detail=str(entry.get("detail") or ""),
            )
            for entry in _entries(payload.get("operations"))
            for kind in [str(entry.get("kind") or "").strip().lower()]
        )
    coverage: tuple[Coverage, ...] = ()
    if role == "faithfulness":
        coverage = tuple(
            Coverage(
                behavior=str(entry.get("behavior") or ""),
                tested_by=str(entry.get("tested_by") or ""),
                covered_by=str(entry.get("covered_by") or ""),
                note=str(entry.get("note") or ""),
            )
            for entry in _entries(payload.get("coverage"))
            if str(entry.get("behavior") or "").strip()
        )
    return Judgment(
        role=role,
        verdict=verdict,  # type: ignore[arg-type]
        summary=str(payload.get("summary") or ""),
        findings=findings,
        checked=_strings(payload.get("checked")),
        operations=operations,
        coverage=coverage,
    )


def _defects(
    payload: dict[str, Any], compared: Sequence[str], notes: list[str]
) -> tuple[Defect, ...]:
    """The defects an attack auditor's payload names that `conformance.py` can be handed.

    Each names a function among those ``compared`` and an input that reads back as an argument
    tuple (`differential.arguments`), kept in that spelling; one that does not is noted and not
    filed, since its input could not be put to `conformance.py` (`core.replay`).
    """
    filed: list[Defect] = []
    for entry in _entries(payload.get("defects")):
        defect = str(entry.get("defect") or "").strip()
        if not defect:
            continue
        function = str(entry.get("function") or "").strip()
        spelled = arguments(str(entry.get("input") or ""))
        if function not in compared or spelled is None:
            why = (
                f"its function, `{function or 'none'}`, is not one conformance.py compares"
                if function not in compared
                else "its input is not an argument tuple written as a Python literal"
            )
            notes.append(
                f"attack: the defect '{material.clip(defect, 200)}' was not filed: {why}"
            )
            continue
        filed.append(
            Defect(
                defect=defect,
                function=function,
                input=spelled,
                repository=str(entry.get("repository") or "").strip(),
                specification=str(entry.get("specification") or "").strip(),
            )
        )
    return tuple(filed)


def _compared(bundle: Bundle) -> tuple[str, ...]:
    """The functions the recorded `impl.conformance` verdict says `conformance.py` compared."""
    recorded = bundle.manifest().verdicts.get("impl.conformance")
    rows = recorded.details.get("compared") if recorded is not None else None
    return tuple(
        dict.fromkeys(
            str(row["symbol"])
            for row in (rows if isinstance(rows, list) else ())
            if isinstance(row, dict) and row.get("symbol")
        )
    )


def _compared_block(bundle: Bundle) -> str:
    """The functions a defect may name (`_compared`), as the attack auditor is told them."""
    names = _compared(bundle)
    if not names:
        return "`conformance.py` has compared no function yet, so no defect can be filed."
    return f"The function is one of these: {', '.join(f'`{name}`' for name in names)}."


#: Where the attack validation auditor's workspace holds the task's statement, so a sentence of
#: it can be quoted character for character.
STATEMENT = "statement.md"
#: How much of the attack auditor's claim about a submission the attack validation auditor is
#: shown.
CLAIM_LIMIT = 1_500
#: How a submission of each kind is described to the attack validation auditor.
_KIND_WORDS: dict[SubmissionKind, str] = {
    "weakness": "a wrong implementation the specification should refute",
    "control": "a correct implementation the specification should accept",
}


def _cases(bundle: Bundle, recorded: Review | None) -> list[tuple[Submission, str]]:
    """The submissions on record the attack validation auditor rules on (`unruled`).

    Each with what the gates established about it.
    """
    listed = unruled(bundle)
    if not listed or recorded is None:
        return []
    return [(item, listed[item.id]) for item in recorded.submissions if item.id in listed]


def _cases_block(cases: Sequence[tuple[Submission, str]], bundle: str) -> str:
    """Each attack or control the attack validation auditor rules on.

    Each with its files and what was found.
    """
    entries: list[str] = []
    for item, said in cases:
        files = [f"Its file is `{bundle}/audit/{item.file}`"]
        if item.shadow:
            files.append(f"the equivalent patch filed with it `{bundle}/audit/{item.shadow}`")
        if item.test:
            files.append(
                f"its witness test `{bundle}/audit/{item.test}`"
                + (f', which cites "{item.cites.strip()}"' if item.cites.strip() else "")
            )
        if item.refutation.strip():
            files.append(
                f"its refutation witness is under `refutation` in `{bundle}/audit/index.toml`"
            )
        claim = material.clip(item.claim.strip(), CLAIM_LIMIT) or "none was filed."
        entries.append(
            "\n\n".join(
                [
                    f"### `{item.id}`, filed as {_KIND_WORDS[item.kind]}",
                    f"What the gates established: {said}",
                    f"The attack auditor's claim: {claim}",
                    "; ".join(files) + ".",
                ]
            )
        )
    return "\n\n".join(entries)


def _coverage_block(
    bundle: Bundle, recorded: Review | None, judged: Sequence[Judgment], backend: Backend
) -> str:
    """The faithfulness auditor's coverage table, from this review or else the current one."""
    judgment = next((item for item in judged if item.role == "faithfulness"), None)
    if judgment is None and recorded is not None:
        judgment = recorded.judgment("faithfulness")
        if judgment is not None and (
            not judgment.reads or judgment.stale(readings(bundle, backend))
        ):
            judgment = None
    if judgment is None or not judgment.coverage:
        return (
            "No current coverage table of the faithfulness auditor's is on record, so set each "
            "behaviour against the statement and the tests yourself."
        )
    rows = "\n".join(
        f"| {material.cell(row.behavior)} | {material.cell(row.tested_by) or '-'} | "
        f"{material.cell(row.covered_by) or '-'} |"
        for row in judgment.coverage
    )
    return (
        "The faithfulness auditor listed each behaviour of the functions the fix changes, with "
        "the test that checks it and the obligation that states it. A row with no test is a "
        "behaviour no FAIL_TO_PASS test, and no PASS_TO_PASS test the test patch adds or "
        "edits, checks.\n\n"
        "| behaviour | tested by | covered by |\n| --- | --- | --- |\n" + rows
    )


def _ruled(
    payload: dict[str, Any] | None,
    cases: Sequence[tuple[Submission, str]],
    recorded: Review | None,
    digests: dict[str, str],
) -> tuple[Ruling, ...]:
    """The rulings on record once the attack validation auditor reported on ``cases``.

    One per attack or control it was shown, reached from the files as they are
    (`ruling_reads`): what it ruled, or no ruling where it gave none, which counts as asked all
    the same. One shown again with its files as they were counts as asked once more
    (`Ruling.asked`). The rulings on the other submissions on record are kept.
    """
    given: dict[str, dict[str, Any]] = {}
    for entry in _entries((payload or {}).get("rulings")):
        given.setdefault(str(entry.get("id") or "").strip(), entry)
    earlier = {item.id: item for item in recorded.rulings} if recorded is not None else {}
    shown = {item.id for item, _ in cases}
    fresh: list[Ruling] = []
    for item, _ in cases:
        reads = ruling_reads(item, digests)
        before = earlier.get(item.id)
        entry = given.get(item.id, {})
        fresh.append(
            Ruling(
                id=item.id,
                ruling=str(entry.get("ruling") or "").strip().lower(),
                input=str(entry.get("input") or "").strip(),
                rests_on=str(entry.get("rests_on") or "").strip(),
                why=str(entry.get("why") or "").strip(),
                asked=before.asked + 1 if before is not None and before.reads == reads else 1,
                reads=reads,
            )
        )
    return (*(item for name, item in earlier.items() if name not in shown), *fresh)


def _strings(value: object) -> tuple[str, ...]:
    """The non-blank strings of an array a session submitted."""
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if str(item).strip())


def _entries(value: object) -> list[dict[str, Any]]:
    """The objects of an array a session submitted, skipping anything that is not one."""
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, dict)]


def _schema(lane: Lane, backend: Backend) -> tuple[dict[str, Any], tuple[str, ...]]:
    """One auditor's report fields, a control's refutation witness only where it is read."""
    schema, required = _FIELDS[lane]
    if lane != "attack" or backend.witness_required:
        return schema, required
    controls = schema["controls"]
    properties = {
        name: field
        for name, field in controls["items"]["properties"].items()
        if name not in (_REFUTATION, "test")
    }
    trimmed = {**controls, "items": {**controls["items"], "properties": properties}}
    return {**schema, "controls": trimmed}, required


def _optional(
    workspace: Path, entry: dict[str, Any], field: str, notes: list[str], what: str
) -> str:
    """The file an entry's ``field`` names, "" where it names none or none can be read."""
    if not str(entry.get(field) or "").strip():
        return ""
    return _named(workspace, entry.get(field), notes, what) or ""


def _named(workspace: Path, named: object, notes: list[str], what: str) -> str | None:
    """Read a file a session named, if it is one inside its own workspace."""
    text = str(named or "").strip()
    if not text:
        notes.append(f"a {what} was submitted without a file")
        return None
    path = Path(text)
    path = (path if path.is_absolute() else workspace / path).resolve()
    if not path.is_relative_to(workspace.resolve()) or not path.is_file():
        notes.append(f"a {what} names {text!r}, which is not a file in the workspace")
        return None
    return read_text(path)


def _unjudged(copy: Bundle) -> None:
    """Take the review and what the gates made of it out of a copy's `manifest.json`."""
    if not copy.manifest_path.is_file():
        return
    manifest = copy.manifest()
    manifest.verdicts = {
        gate: verdict
        for gate, verdict in manifest.verdicts.items()
        if not gate.startswith("audit.")
    }
    manifest.provenance = {
        key: value for key, value in manifest.provenance.items() if key != "review"
    }
    copy.save_manifest(manifest)


def _tests_block(task: Task, bundle: Bundle) -> str:
    """Where an auditor's workspace holds the benchmark's tests, and which say what the task is.

    Those are the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds or edits.
    """
    held: list[str] = []
    if material.test_patch(task):
        held.append(
            "`tests/tests.patch` is its test patch, which adds or edits the tests it judges a "
            "fix by; `repository/` does not have it applied, so a test the patch adds is not "
            "there."
        )
    files = [
        f"`tests/{source.path}`"
        for source in task.oracle.files
        if source.content and source.path != "tests.patch"
    ]
    if files:
        held.append(f"The files it runs its tests with are in `tests/`: {', '.join(files)}.")
    failing = _bullets([name for name in task.oracle.tests if "\n" not in name])
    failing += [
        f"* the test program `tests/program-{index}.py`"
        for index, _ in enumerate(_programs(task), 1)
    ]
    changed = sites.changed(task, bundle.manifest().provenance.get(sites.RECORD))
    patched = _bullets(material.patched_regression(task, changed.tests, changed.cases))
    return prompts.render(
        "tests",
        held=" ".join(held),
        failing="\n".join(failing) or "* (the task names none)",
        patched="\n".join(patched) or "* (none)",
    )


def _programs(task: Task) -> list[str]:
    """The task's tests that are whole programs rather than test ids."""
    return [test for test in task.oracle.tests if "\n" in test]


def _bullets(names: Sequence[str]) -> list[str]:
    """Test ids as prompt bullets, the first `material.NAMED_TESTS` of them and a count."""
    lines = [f"* `{name}`" for name in names[: material.NAMED_TESTS]]
    if len(names) > material.NAMED_TESTS:
        lines.append(f"* ... and {len(names) - material.NAMED_TESTS} more")
    return lines


def _record(lane: str, outcome: StepOutcome) -> dict[str, Any]:
    """What `manifest.json` keeps of one review session."""
    return {
        "lane": lane,
        "submitted": outcome.submitted,
        "turns": outcome.turns,
        "tool_uses": outcome.tool_uses,
        "duration_s": round(outcome.duration_s, 1),
        "detail": outcome.detail,
        "actions": list(outcome.actions),
    }


def _on_record_block(recorded: Review | None, stands: bool, bundle: Bundle) -> str:
    """What the review before this one filed, with what the gates ruled, or "" for nothing.

    Where the specification it attacked still ``stands``, every submission stays on record
    and is judged with the auditor's own, so the auditor writes new ones. Otherwise they are not
    run again, and the auditor is shown each earlier attack with the repair's entry for it, to
    write again against the specification as it now stands the ones the gates ruled a
    weakness, as `verified-swebench`'s audit writes again any counterexample a prior
    pass named.
    """
    if recorded is None:
        return ""
    listed = [item for item in recorded.submissions if stands or item.kind == "weakness"]
    if not listed:
        return ""
    # Both submission gates record every submission's ruling; either one's will do.
    verdict = bundle.manifest().verdicts.get("audit.spec_completeness")
    found = verdict.details.get("rulings") if verdict is not None else None
    rulings: dict[str, str] = found if isinstance(found, dict) else {}
    answers, said = _repair_answers(bundle)
    lines: list[str] = []
    for item in listed:
        claim = item.claim or "no claim filed"
        lines += [
            f"* `audit/{item.file}` ({item.kind}, `{item.id}`): {claim}",
            f"  * The gates ruled: {rulings.get(item.id) or 'nothing they recorded'}",
        ]
        if not stands:
            named = rf"(?<![\w-]){re.escape(item.id)}(?![\w-])"
            answer = next(
                (words for text, words in answers.items() if re.search(named, text)),
                "The repair's report says nothing of it.",
            )
            lines.append(f"  * {answer}")
    if stands:
        return (
            "## Already on record\n\n"
            "An earlier review filed these against the specification as it now stands, each "
            "with the kind it was filed as: `weakness` for a wrong implementation the "
            "specification accepts, `control` for a correct one it should accept. They stay "
            "on record, and the gates re-run them with yours each time they judge the bundle. "
            "Write new ones, different from them: Benchproofer drops a repeat.\n\n"
            + "\n".join(lines)
        )
    return (
        "## Attacks an earlier review filed\n\n"
        "An earlier review filed these attacks against the specification as it stood before "
        "a repair, each below with what the gates ruled and the repair's entry for it, and "
        "its file still under `audit/`. They are not run again: the gates judge the "
        "submissions of this review. First write again each counterexample the earlier "
        "review found: write each attack the gates ruled a weakness of the specification "
        "again, the same wrong behaviour against the specification as it now stands, unless "
        "the repair's entry for it shows with evidence that it was not a defect. Then write "
        "new attacks, until you have as many as asked for above.\n\n"
        + "\n".join(lines)
        + (f"\n\nThe repair since then said: {said}" if said else "")
    )


def _findings_block(lane: str, recorded: Review | None, bundle: Bundle) -> str:
    """What this auditor found last time, each finding with the repair's entry for it.

    Empty where there is nothing to carry: no judgment on record, or a sound one with no
    findings. The auditor judges a decline: a finding the repair declined with evidence is
    withdrawn if the evidence holds and kept, saying why not, if it does not; one the repair
    neither resolved nor declined stays open.
    """
    previous = recorded.judgment(lane) if recorded is not None else None  # type: ignore[arg-type]
    if previous is None or (previous.verdict == "sound" and not previous.findings):
        return ""
    answers, said = _repair_answers(bundle)
    lines = [f"* {previous.summary}"] if previous.summary else []
    for finding in previous.findings[:FINDING_LIMIT]:
        answer = answers.get(finding, "The repair's report says nothing of it.")
        lines += [f"* {finding}", f"  * {answer}"]
    return (
        "## Findings on record\n\n"
        f"An earlier review of this question gave the verdict `{previous.verdict}`"
        + (":\n\n" + "\n".join(lines) if lines else ".")
        + (f"\n\nThe repair since then said: {said}" if said else "")
        + (
            "\n\nCheck each finding against the specification as it now stands. Where the "
            "repair declined one, saying with its evidence that it is not a defect, judge "
            "that evidence: if it holds, withdraw the finding; if it does not, keep the "
            "finding and say why the evidence does not hold. A finding the repair neither "
            "resolved nor declined stays open until the specification addresses it. Include "
            "in your findings every one that still holds."
            if previous.findings
            else ""
        )
    )


#: What an auditor is told the repair did about one finding, by the report's outcome for it.
_DID: dict[str, str] = {
    rounds.RESOLVED: "The repair resolved it",
    rounds.NOT_A_DEFECT: "The repair found it no defect and changed nothing for it",
    rounds.NOT_REACHED: "The repair did not reach it",
}


def _repair_answers(bundle: Bundle) -> tuple[dict[str, str], str]:
    """The last repair session's entry for each finding it was briefed with, and its account.

    Each finding by its text in the brief, with what the report's entry for it said: that
    the repair resolved it, found it no defect, or did not reach it (`rounds.outcome`), and
    the words it gave, whole. Then the session's summary and why its work was refused, where
    it was.
    """
    history = bundle.manifest().provenance.get("repairs")
    last = history[-1] if isinstance(history, list) and history else None
    session = last.get("session") if isinstance(last, dict) else None
    if not isinstance(session, dict):
        return {}, ""
    texts = rounds.briefed(session)
    answers: dict[str, str] = {}
    for number, entry in rounds.reported(session).items():
        if number not in texts:
            continue
        words = str(entry.get("witness") or "").strip()
        did = _DID[rounds.outcome(entry)]
        answers[texts[number]] = did + (f": {words}" if words else ".")
    parts = [str(session.get(key) or "").strip() for key in ("summary", "refused")]
    return answers, " ".join(part for part in parts if part)


def _refutation_block(solution: str, backend: Backend) -> str:
    """What a control's refutation witness and its witness test are, or "" where none is read.

    Only a checker whose refusal says nothing without one asks for it
    (`Backend.witness_required`); its rules are the ones a rival's refutation witness is
    drafted to (`core.witness.rules`).
    """
    if not backend.witness_required:
        return ""
    rules = witness.rules(solution, backend, "control")
    return "\n" + prompts.render("refutation", tools="./tools", witness_rules=rules)


def _modeled_block(solution: str, backend: Backend) -> str:
    """Which callees the `axioms` region has a `benchproofer:models` line for.

    Read off the solution file, so that the equivalence auditor sets each `modeled` row against
    the lines that are there rather than against its reading of the region.
    """
    modeled = [item.callee for item in declared_in(solution, backend.comment) if item.modeled]
    if not modeled:
        return (
            "The `axioms` region has no `benchproofer:models` line, so no row is `modeled`: "
            "a definition computing a callee's result is under no such line, and its row is "
            "`changed`."
        )
    listed = "\n".join(f"* `{callee}`" for callee in dict.fromkeys(modeled))
    return (
        "The `axioms` region has a `benchproofer:models` line for these callees, and only a "
        f"call of one of them, computed by the definition under its line, is `modeled`:\n\n"
        f"{listed}\n\nA definition computing any other callee's result is under no such "
        "line, and its row is `changed`."
    )


def _undiscriminating_block(bundle: Bundle) -> str:
    """The conformance gate's note that `conformance.py` agrees before the fix too, or "".

    For the equivalence auditor, whose rules say what the repository side of
    `conformance.py` must call.
    """
    recorded = bundle.manifest().verdicts.get("impl.conformance")
    note = recorded.details.get("undiscriminating") if recorded is not None else None
    if not isinstance(note, str) or not note.strip():
        return ""
    return (
        "## What `conformance.py` showed against the code before the fix\n\n"
        "Benchproofer ran `conformance.py` a second time, against the task's base commit, "
        f"and noted: {note}. Its agreement with the fixed code is then no evidence about "
        "the behaviour the fix changes. Read its repository side against the rule above "
        "on `conformance.py`: whether it calls the repository's code for each function the "
        "golden patch changes that the specification models, and whether what it compares "
        "is what the fix changes."
    )


def _port_block(bundle: Bundle, backend: Backend) -> str:
    """The equivalence auditor's check of the Python port `conformance.py` compares, or "".

    Where `impl.conformance` found that `conformance.py` cannot carry the implementation
    verbatim (`TRANSLITERATED`): written in a language the repository cannot run, or using
    the checker's own values. The gate then checks no line of what it compares.
    """
    recorded = bundle.manifest().verdicts.get("impl.conformance")
    if recorded is None or recorded.details.get("provenance") != TRANSLITERATED:
        return ""
    why = (
        f"it is written in {backend.language}, which the repository's Python cannot run"
        if backend.extension != ".py"
        else "it uses values only the checker has, such as "
        + ", ".join(f"`{token}`" for token in backend.foreign_tokens)
    )
    return prompts.render("port", why=why, solution=bundle.solution_path.name)


#: How much of what repairs changed in the bundle's programs an auditor is shown.
PROGRAMS_LIMIT = 12_000


def _programs_block(bundle: Bundle, cache_dir: Path) -> str:
    """What changed in `conformance.py` and `axioms.py` since the last round, or "".

    Set against the bundle as this run's last round judged it (`core.rounds`): what a
    repair changed in them since, which the gates run again and no gate checks for
    comparing less than the specification needs.
    """
    history = rounds.directory(bundle, cache_dir)
    kept = rounds.archived(history)
    if not kept:
        return ""
    last = history / kept[-1][0]
    diff = material.changes(
        [
            (name, read_text_or_empty(last / name), read_text_or_empty(bundle.root / name))
            for name in (DIFFERENTIAL_HARNESS, AXIOM_HARNESS)
        ],
        PROGRAMS_LIMIT,
        before=f"round-{kept[-1][0]}",
        after="now",
    )
    return prompts.render("programs", diff=diff) if diff else ""


def _earlier_block(bundle: Bundle, cache_dir: Path) -> str:
    """What the review found in this run's earlier rounds, one line per finding, or "".

    The review's own gates only (`LANE_OF`), in each round the loop kept (`core.rounds`), so
    that a finding undoing what an earlier one asked for is seen as one.
    """
    lines: list[str] = []
    for name, manifest in rounds.archived(rounds.directory(bundle, cache_dir)):
        found = rounds.outline(
            verdict for gate, verdict in manifest.verdicts.items() if gate in LANE_OF
        )
        lines += [f"* Round {name}:", *(f"  {line}" for line in found)] if found else []
    if not lines:
        return ""
    return (
        "## What the review found in earlier rounds\n\n"
        "The review of the specification as it stood in this run's earlier rounds found these, "
        "each given by its first sentence:\n\n"
        + "\n".join(lines)
        + "\n\nA finding of yours that asks for what one of these said demands more than the "
        "task, or that calls too strict what one of these asked for, says so, and decides "
        "which is right against the fixed code and the tests that say what the task is."
    )


def _witnesses_block(bundle: Bundle) -> str:
    """What fuzzers found against an earlier form of the assumptions, to try first."""
    recorded = bundle.manifest().verdicts.get("audit.axiom_soundness")
    found = recorded.details.get("witnesses") if recorded is not None else None
    if not isinstance(found, list) or not found:
        return ""
    listed = "\n".join(f"* `{item}`" for item in found[:FINDING_LIMIT] if isinstance(item, str))
    return (
        "## Found before\n\n"
        "An earlier fuzzer reported these disagreements with the assumptions as they stood "
        "then. Try them against the assumptions as they stand now before anything else:\n\n"
        f"{listed}"
    )

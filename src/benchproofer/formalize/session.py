# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The formalization session: drafting one bundle's artifacts.

A session turns one task into the files a bundle needs, in this order:

1. **solution**: specification and implementation, by the run's agent session in a
   workspace of its own, with the repository, the tests and the checker at hand
   (`Formalizer._solution_by_agent`); a run with no session drafts nothing;
2. **pre-fix implementation** (`twins/`): the code before the fix under the same
   specification, which the specification has to reject;
3. **property-based test suite** (`rivals/`): cases that attack the specification from three
   sides -- wrong implementations it must refute, correct ones it must admit, and a probe on
   the reference implementation exhibiting that its obligations hold at the task's own
   inputs, with a second probe at a PASS_TO_PASS test's input where one hands a function the
   fix changes an input;
4. **correspondence**: `correspondence.md`, each operation of the implementation set
   against the one the fix performs in its place;
5. **conformance**: `conformance.py`, which compares a Python copy of the implementation with
   the code the golden patch leaves in the repository;
6. **axioms**: when the specification assumes a callee rather than modeling it,
   `axioms.py`, which checks each assumption against the callee it represents.

Each after the solution is one request, but for `conformance.py`, which is run once where
its gate will run it and sent back once when that run establishes nothing. A solution the
checker refuses goes to a proof session where the backend's files carry their proofs
(`prove.Prover`). Whatever the checker or a gate objects to after that is the repair
session's to fix: an agent with the checker, the gates and the repository at hand, which
edits these files as they stand rather than having them drafted again.

Two rules shape the code. First, the checker is used here as *feedback only*. A
result produced during drafting is never a verdict: verdicts come from gates, which
re-run the checker over the artifacts as they were written to disk. Second, an
artifact is kept whatever the checker said about it. A rival that verifies when it
should have been refuted is the most valuable thing a session can produce, so it is
recorded rather than retried away.

A repair session (`Formalizer.repair_by_agent`) leaves the bundle for the gates to judge, and
nothing is drafted after it: a file it leaves missing fails its gate, so its request carries
the rules of each file the bundle lacks or its findings are about, from the rules files the
requests above state them in.
"""

from __future__ import annotations

import json
import re
import shutil
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from ..backends.base import Backend, BackendKind, CheckResult
from ..config import Settings
from ..core import (
    differential,
    extract,
    markers,
    material,
    sites,
    variant,
    witness,
    workcopy,
)
from ..core.axioms import (
    AFTER_REFERENCE,
    HARNESS,
    PROTOCOL,
    callees,
    declared,
    with_declarations,
)
from ..core.bundle import RIVAL_EXPECTATION, Bundle, RivalKind
from ..core.differential import DEADLINE_SHARE, REPLAY, protocol_for
from ..core.differential import HARNESS as DIFFERENTIAL_HARNESS
from ..core.rounds import NOT_A_DEFECT, NOT_REACHED, OUTCOMES, RESOLVED
from ..core.scripts import SCRATCH, lay_out, tools_rules
from ..core.session import Exchange, Journal, Session, quoted
from ..core.task import Task
from ..errors import BenchproofError, ProviderError
from ..gates import battery as gate_battery
from ..gates.audit import OUTSIDE, entries_under
from ..llm.agentic import EDIT, AgentSession, SessionSpec, StepOutcome
from ..llm.base import Message, Provider
from ..llm.resolve import NO_SESSION
from ..log import logger
from ..oracles.base import Oracle, OracleStatus, Program
from ..util.fsio import read_text, read_text_or_empty, write_text
from ..util.patch import Edited
from . import prompts
from .prove import ProofKind, Prover

__all__ = ["AUTHORED", "Draft", "Exchange", "Formalization", "Formalizer"]

log = logger(__name__)

#: How many cases of each kind the property-based test suite asks for. Two wrong implementations
#: and one correct alternative is the smallest property-based test suite that can catch a
#: specification that is too weak and one that is too strong; the probe is the third question,
#: and `battery_plan` is what decides whether this checker can be asked it. A second probe is
#: drafted where a PASS_TO_PASS test hands a function the fix changes an input
#: (`Formalizer._regression`).
BATTERY_PLAN: tuple[tuple[RivalKind, int], ...] = (
    ("uniqueness", 2),
    ("soundness", 1),
    ("admissibility", 1),
)
#: The kind, and the id, of the pre-fix implementation: one per bundle.
TWIN = "twin"
#: Longest checker or program output pasted back into a prompt.
OUTPUT_LIMIT = 4_000

#: What an accepting verdict means, by the kind of checker, for the system prompt.
_KIND_NOTE = {
    BackendKind.PROVER: (
        "an accepting verdict means the implementation provably satisfies the "
        "specification for every input its preconditions admit."
    ),
    BackendKind.FALSIFIER: (
        "an accepting verdict means only that no counterexample was found within its "
        "search budget, so a property that is merely hard to falsify is not thereby "
        "established. Write properties that are cheap to test and sharp."
    ),
}

#: What a repair session reports, as `verified-swebench`'s repair agents do: the outcome,
#: what changed, what it did about each briefed finding and its evidence, and each input it
#: excluded that the specification admitted.
_REPAIR_FIELDS: dict[str, object] = {
    "status": {
        "type": "string",
        "enum": ["REPAIRED", "NO-REPAIR-NEEDED", "BLOCKED"],
        "description": "how the repair ended",
    },
    "summary": {
        "type": "string",
        "description": "two sentences: what you changed and why",
    },
    "findings": {
        "type": "array",
        "description": "one entry for each numbered finding in the brief",
        "items": {
            "type": "object",
            "properties": {
                "finding": {
                    "type": "string",
                    "description": "its number in the brief, such as `8` or `12.1`",
                },
                "outcome": {
                    "type": "string",
                    "enum": list(OUTCOMES),
                    "description": (
                        f"`{RESOLVED}` when your change resolves it; `{NOT_A_DEFECT}` when "
                        "you established that it is no defect and changed nothing for it; "
                        f"`{NOT_REACHED}` when you did not get to it or could not close it"
                    ),
                },
                "witness": {
                    "type": "string",
                    "description": (
                        f"for `{RESOLVED}`: the counterexample it addresses, an input, a wrong "
                        "implementation, or the line the finding quotes, and what the real "
                        f"function does on it, citing file and line; for `{NOT_A_DEFECT}`: "
                        "the evidence that it is none, an input and what the real function "
                        "does on it or the line of the task or the specification that shows "
                        f"it, citing file and line; for `{NOT_REACHED}`: what you established "
                        "about it"
                    ),
                },
            },
            "required": ["finding", "outcome"],
        },
    },
    "excluded": {
        "type": "string",
        "description": (
            "each input the repair excludes that the specification admitted before, and "
            "where: the precondition, the `Outside the bridge` entry or the change to "
            "conformance.py; for an entry of one of the three kinds that are not a "
            "narrowing, which kind and the evidence; empty when it excludes nothing"
        ),
    },
    "checker": {
        "type": "string",
        "description": (
            "the last lines the checker printed on your solution file, from `./tools verify` "
            "or `./check --only spec.verifies`"
        ),
    },
}
_REPAIR_REQUIRED: tuple[str, ...] = ("status", "summary")
#: What the session drafting the solution reports, after `verified-swebench`'s author
#: (`worker.md`'s final report): whether the checker accepted the file, what it models, how
#: each unchanged callee is stated, and what the specification leaves out, which opens the
#: two sections of `correspondence.md` that say so (`_correspondence`).
_DRAFT_FIELDS: dict[str, object] = {
    "status": {
        "type": "string",
        "enum": ["VERIFIED", "BLOCKED"],
        "description": "VERIFIED once ./tools verify accepts the file, BLOCKED otherwise",
    },
    "summary": {
        "type": "string",
        "description": "two sentences: what the specification models and how",
    },
    "modeled": {
        "type": "array",
        "items": {"type": "string"},
        "description": "each repository function the specification models, as a dotted path",
    },
    "callees": {
        "type": "string",
        "description": (
            "each unchanged callee the changed code calls: modelled under a `models` line or "
            "an axiom, where it is defined as file:line, and what it does"
        ),
    },
    "not_modeled": {
        "type": "string",
        "description": (
            "what the fix changes that the specification does not model, each by its file or "
            "function, and why; `Nothing.` when it models all of it"
        ),
    },
    "outside": {
        "type": "string",
        "description": (
            "each input the model's domain leaves out, as an `Outside the bridge` entry: "
            "which of the three kinds, the inputs, and why, naming the branch or the line for "
            "the third; `Nothing.` when it leaves none out"
        ),
    },
    "blocked": {
        "type": "string",
        "description": "when BLOCKED: what stands in the way, and what you tried",
    },
    "checker": {
        "type": "string",
        "description": "the last lines `./tools verify` printed on your solution file",
    },
}
_DRAFT_REQUIRED: tuple[str, ...] = ("status", "summary")
#: The fields of the drafting report `correspondence.md` is drafted from, and the section
#: of it each opens.
_EXCLUSIONS: tuple[tuple[str, str], ...] = (
    ("not_modeled", "Not modeled"),
    ("outside", OUTSIDE),
)
#: Where the drafting session's workspace holds each file the fix touches, as it reads after.
FIXED = "fixed"
#: Where a repair session's workspace holds its request, to read again.
BRIEF = "brief.md"
#: The author's files besides the solution, which a repair session may edit, by the
#: bundle-relative name they are compared under: the pre-fix implementations, the property-based
#: test suite, `correspondence.md`, `conformance.py` and `axioms.py`.
AUTHORED: tuple[str, ...] = (
    "twins",
    "rivals",
    "correspondence.md",
    DIFFERENTIAL_HARNESS,
    HARNESS,
)
#: What a repair writing a pre-fix implementation, or a case of the property-based test suite,
#: is told of the index its refutation witness goes in, under a checker that needs one; and
#: what a repair writing `correspondence.md` is told of `Outside the bridge`, whose kinds the
#: request states elsewhere.
_TWIN_WITNESS = (
    "Its refutation witness is the `witness` of its table in `twins/index.toml`, a `[[twin]]` "
    'with `id = "twin"`, `file = "twin{extension}"`, `rationale` and `witness`.'
)
_RIVAL_WITNESS = "A case that expects `refute` also has a `witness`, its refutation witness."
_OUTSIDE_BELOW = (
    "It names the inputs on which the implementation is not set against the golden patch, "
    "each with why: the three kinds of entry it may hold, and how each is checked, are "
    "under `What you may not do` below."
)
#: Why a uniqueness case is told the pre-fix implementation, as each request for one says it.
_DIFFERENT_MISTAKE = (
    "Pick a mistake {it} does not make: a rival that computes what it computes tests nothing "
    "the bundle has not tested, and is set aside."
)
#: Where a repair session's workspace holds the files each auditor left in its own,
#: one directory per auditor.
REVIEWED = "review"
#: The ways a correct case the checker refused falls short of a proof of its own under every
#: checker, which a repair is told after the backend's own (`Backend.refused_cases`).
_REFUSED_CASES: tuple[str, ...] = (
    "**Dropping a framing assert / invariant / lemma.** A correct case written differently "
    "must keep the proof obligations it still needs. Change the executable shape, not the "
    "invariants.",
    "**A case that times out.** A timeout is never a rejection; it establishes nothing. Keep "
    "cases small.",
)
#: What a repair session is told of the refutation witness, under a checker that needs one
#: (`Backend.witness_required`).
_REWITNESS = (
    "\nUnder this checker a case of the property-based test suite that expects `refute`, and "
    "the pre-fix implementation, each have a refutation witness, the `witness` of their entry "
    "in `rivals/index.toml` and `twins/index.toml`: a claim proved at one concrete input that "
    "holds of the case and fails of the reference implementation, which is what shows that "
    "the specification, rather than the case's own proof, is what rejects it. A case you "
    "rewrite to be rejected needs its witness again, about the case you leave; the gate's "
    "own `--only` (`spec.strength.battery`, or `spec.discriminates` for the pre-fix "
    "implementation) builds it as the gate will.\n"
)
_BRIEF: dict[str, str] = {
    "uniqueness": (
        "A uniqueness rival is wrong: on at least one input the specification admits, "
        "it produces a result the task considers incorrect. Pick a mistake a competent "
        "programmer could plausibly make, not a stub and not a constant. The checker "
        "must reject it. If it accepts, the specification is too weak, which is exactly "
        "what this case exists to find out."
    ),
    "soundness": (
        "A soundness rival is correct, and written differently from the reference "
        "implementation: another algorithm, another traversal order, another data "
        "structure. The checker must accept it. If it rejects, the specification pins "
        "down one implementation instead of describing the task."
    ),
    # From `verified-swebench`'s `prompts/shared/pbt_author.md` §3, ADMISSIBILITY. Where a
    # probe goes and what it states are the backend's (`Backend.probe_placement`,
    # `Backend.probe_brief`, which fills `{states}`): a Nagini probe sits inside the
    # specified method, where a call to that method recurses and the checker refuses it on
    # the method's own termination measure.
    "admissibility": (
        "An admissibility case, or probe, is not a rival. Show the precondition admits a "
        "normal input of the shape {tests} use: {states} "
        "If the specification has NO precondition, admissibility becomes the same question "
        "one level down: is the postcondition SATISFIABLE (non-contradictory) at the inputs "
        "{tests} exercise? Give the result for two or three real inputs, one assertion "
        "each.\n"
        "\n"
        "Leave the reference implementation and the solution file's proof running unchanged "
        "alongside, so that a failure cannot be the case's own proof failing rather than "
        "the specification.\n"
        "\n"
        "The checker must accept it. If it rejects, the precondition is too strong: it "
        "excludes {excluded}, and every other gate agrees with the specification because "
        "they are all judged against that same precondition. No rival can find this, which "
        "is why the probe exists."
    ),
}
#: Whose inputs a probe takes, and what a precondition that rejects it excludes: by
#: whether it is the probe at the PASS_TO_PASS tests' inputs (`_brief`).
_PROBED: dict[bool, tuple[str, str]] = {
    False: ("the FAIL_TO_PASS tests", "the very inputs the task is about"),
    True: (
        "the PASS_TO_PASS tests below",
        "inputs the PASS_TO_PASS tests hand a function the fix changes, which the model's "
        "domain has to admit",
    ),
}

#: How the request for a case names it: a rival, or an admissibility case, which its brief
#: says is not a rival.
_CASE: dict[str, str] = {
    "uniqueness": "a uniqueness rival",
    "soundness": "a soundness rival",
    "admissibility": "an admissibility case",
}

#: What a reject case drafted by a request is asked for after its regions, where a rejection
#: alone attributes nothing; `witness-rules.md` says what the witness must be. See
#: `core.witness` for why, and `Backend.witness_required` for where.
_WITNESS = "\nThen add a **second** fenced code block holding a refutation witness.\n\n"


@dataclass(frozen=True, slots=True)
class Draft:
    """One variant of the accepted solution: a pre-fix implementation or a rival.

    `source` is a complete solution file, produced by splicing the regions the model
    wrote into the solution file, so its specification is identical to the solution file's
    by construction.
    """

    id: str
    kind: str
    rationale: str
    source: str
    #: What the checker said while drafting. Kept for the record; the gates decide.
    check: CheckResult | None = None
    #: The claim that makes this variant's rejection attributable to the specification, where
    #: the backend requires one: that of a reject case of the property-based test suite, or the
    #: pre-fix implementation's. See `core.witness`.
    witness: str = ""
    #: What a proof session on this case reported, in one line, empty where none ran. A case the
    #: checker had to accept and refused is a defect of the case, which a repair fixes -- unless
    #: a session has already spent its budget on the proof and failed, which is a gap in the
    #: bundle's evidence rather than something to fix. The gate cannot tell the two apart from
    #: the file, so the record travels with the case. A pre-fix implementation is meant to be
    #: refused, so what it records is the session on its witness.
    proof_session: str = ""

    @property
    def expectation(self) -> str:
        """The verdict this draft's specification has to reach: verify or refute."""
        return RIVAL_EXPECTATION.get(self.kind, "refute")

    @property
    def found(self) -> str:
        """What the checker said of this case, against what the case expected.

        The expectation alone does not say whether the case behaved, so a reader of the
        shipped index cannot tell a correct case the checker accepted from one it refused
        on a step of the case's own proof. Where the two agree this is the expectation;
        where they do not it names what happened instead, and a case a proof session was
        already spent on is `unproved`, which is the gap the property-based test suite reports.
        """
        expectation = self.expectation
        if self.check is None or not self.check.decided:
            return (
                f"{expectation}: undecided, the checker reached no verdict"
                if self.check is not None
                else ""
            )
        if self.check.verified == (expectation == "verify"):
            return expectation
        if expectation == "verify" and self.proof_session:
            return (
                f"{expectation}: unproved, correct but the checker rejected a step of its own "
                "proof"
            )
        return f"{expectation}: {self.check.status}"


@dataclass(frozen=True, slots=True)
class Formalization:
    """Everything one session produced for one task and backend."""

    task_key: str
    backend: str
    provider: str
    model: str
    solution: str
    accepted: bool
    check: CheckResult
    rounds: int
    twins: tuple[Draft, ...] = ()
    rivals: tuple[Draft, ...] = ()
    correspondence: str = ""
    #: `conformance.py` comparing the implementation with the repository's own
    #: code, empty when there is no reference solution to compare it with.
    conformance: str = ""
    #: `axioms.py`, empty when the specification assumes nothing.
    axioms: str = ""
    exchanges: tuple[Exchange, ...] = ()
    notes: tuple[str, ...] = ()
    #: What `manifest.json` keeps of the session that drafted the solution, as of a repair
    #: session; empty for a formalization no session drafted.
    session: dict[str, Any] = field(default_factory=dict)

    @property
    def input_tokens(self) -> int:
        """Tokens sent across the whole session."""
        return sum(exchange.input_tokens for exchange in self.exchanges)

    @property
    def output_tokens(self) -> int:
        """Tokens received across the whole session."""
        return sum(exchange.output_tokens for exchange in self.exchanges)

    def provenance(self) -> dict[str, Any]:
        """The session's record, for the bundle manifest.

        Deliberately free of prompt and reply text: a bundle is judged on its
        artifacts, and a transcript in `manifest.json` invites reading the model's
        explanation as evidence.
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "rounds": self.rounds,
            "accepted": self.accepted,
            "checker_status": str(self.check.status),
            "checker_detail": self.check.detail,
            "requests": [exchange.record() for exchange in self.exchanges],
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            **({"session": dict(self.session)} if self.session else {}),
            "notes": list(self.notes),
        }


class Formalizer(Session):
    """Draft a task's artifacts with one provider and one backend.

    A `Formalizer` is stateless between tasks: everything about a task lives in the
    `Formalization` it returns, so one instance can serve a whole run. One that repairs a
    bundle is made for it, with what its `manifest.json` records (`changed`).
    """

    def __init__(
        self,
        *,
        provider: Provider,
        backend: Backend,
        settings: Settings,
        workdir: Path,
        session: AgentSession | None = None,
        oracle: Oracle | None = None,
        changed: sites.Changed | None = None,
    ) -> None:
        super().__init__(provider=provider, settings=settings, prompts=prompts.LIBRARY)
        self.backend = backend
        self.workdir = Path(workdir)
        #: An agent session, for the stages that need turns of their own: the solution, a
        #: proof, a repair. None when the run has none, and then the solution and the repair
        #: raise and a proof does not happen and says so.
        self.session = session
        #: The task's oracle, asked for the working copy that stage reads.
        self.oracle = oracle
        #: What the golden patch and the test patch define or edit, as `manifest.json` of the
        #: bundle being repaired records it (`sites.changed`). None when drafting, where it
        #: is read from each task's working copy (`record`).
        self.changed = changed
        #: Each task's working copy, the files its fix and its test patch touch, before and
        #: after each, by task and patch, and what those patches define or edit: laid out
        #: and read once however many stages read them.
        self._copies: dict[str, workcopy.WorkCopy] = {}
        self._sources: dict[tuple[str, str], workcopy.Touched] = {}
        self._records: dict[str, dict[str, Any]] = {}
        self._materials: dict[str, str] = {}

    # ---- the session ----------------------------------------------------

    def run(self, task: Task) -> Formalization:
        """Formalize one task.

        The solution is drafted by the run's agent session, every artifact after it by
        requests.

        Returns:
            A `Formalization`, whether or not the checker accepted the solution. A
            rejected draft is still worth writing down: it is the record of a task
            this configuration could not formalize.

        Raises:
            ProviderError: The run has no agent session, the model could not be reached at
                all, or the drafting session failed before it wrote the solution file, so no
                artifact exists to record. Failures after the solution is drafted are noted
                in the result instead, and the artifacts already drafted are kept.
        """
        journal = Journal()
        system = self._system()
        solution, check, record = self._solution_by_agent(task, journal)
        if not solution:
            return _with(
                replace(self._formalization(task, solution, check, rounds=0), session=record),
                journal,
            )
        solution, check, _ = self._prove(task, solution, check, journal, label="solution")

        formalization = replace(
            self._formalization(task, solution, check, rounds=1), session=record
        )
        if not check.verified:
            journal.note(
                f"the checker did not accept the solution ({check.status}: {check.detail}), "
                "so no further artifact was drafted"
            )
            return _with(formalization, journal)

        twins = self._twin(task, solution, system, journal)
        rivals = self._battery(task, solution, system, journal, twins)
        correspondence = self._correspondence(task, solution, journal, drafted=record)
        return _with(
            formalization,
            journal,
            twins=twins,
            rivals=rivals,
            correspondence=correspondence,
            conformance=self._conformance(
                task, solution, journal, correspondence=correspondence
            ),
            axioms=self._axioms(task, solution, journal),
        )

    def repair_by_agent(
        self,
        task: Task,
        *,
        workspace: Path,
        bundle: Path,
        rounds: Path,
        history: str,
        scratch: Path,
        failing: Sequence[str],
        check: str,
        refused: str,
        checked: str,
        on_record: Sequence[str],
        artifacts: Sequence[str],
        lacking: Sequence[str],
        inputs_rules: str,
    ) -> StepOutcome:
        """Have an agent session repair the bundle in a workspace of its own.

        The session is given what `verified-swebench` gives its repair agents: the bundle
        as it stands, every earlier round of this run, the task, and the repository with the
        benchmark's tests as it runs them (`lay_out_repository`), on disk, with the tools to
        read them, run the checker and the gates, and edit the author's files. ``scratch``
        is the directory its own files go in, which the request names, so that nothing it
        writes reaches a directory the backend's checker shares. ``history`` follows the
        request's findings with what the rounds before them found. What it writes is not
        taken on trust: the caller reads back the files it allows a repair to change, and
        every gate judges them; nothing is drafted after it. ``refused`` tells it of the
        sessions before it whose work was not taken, and opens the request. ``checked`` says
        what the checker did on the solution when the gates last judged it, which the
        request puts beside the checker's time limit. ``on_record`` names the functions the
        bundle has inputs on record for, which `conformance.py` is handed under those names.

        ``artifacts`` names the files beside the solution, as `AUTHORED` names them, whose
        rules the request gives, one section each (`_artifact_rules`): those the bundle
        lacks, ``lacking``, which the request asks it to write, and those the findings are
        about. A repair that touches one file is not handed the rules of every other.
        ``inputs_rules`` lists the unchanged callees this run's rounds let it take the result
        of as an input, with the rule for doing so (`rounds.inputs_rules`), or is empty.

        The request is also written to the workspace, `BRIEF`, for the session to read again
        once its context has been compacted.

        Raises:
            ProviderError: No session is configured, or it could not be started.
        """
        if self.session is None:
            raise ProviderError(NO_SESSION.format(stage="repairing a bundle"))
        repository = workspace / "repository"
        tests_state, refused_tests = self.lay_out_repository(task, workspace)
        if refused_tests:
            log.info("the test patch does not apply to %s: %s", task.key, refused_tests)
        relative = {
            name: path.relative_to(workspace).as_posix()
            for name, path in (
                ("bundle", bundle),
                ("rounds", rounds),
                ("repository", repository),
                ("scratch", scratch),
                ("task_file", bundle.parent / "task.json"),
            )
        }
        prompt = prompts.render(
            "repair-agent",
            task=task.key,
            brief=BRIEF,
            refused=refused,
            failing="\n".join(f"* {line}" for line in failing) or "* (none recorded)",
            first=(
                " A gate holding a finding the last repair did not reach comes first."
                if _repaired_before(bundle)
                else ""
            ),
            history=history,
            workspace=workspace.as_posix(),
            check=check,
            solution=self.backend.solution_filename(),
            audit=(
                " `audit/` is the review: every implementation the reviewer filed, with the "
                "reviewer's one-sentence statement of what it shows, the controls and "
                "fuzzers, and `index.toml` with the judgments; each attack a finding above "
                "names is listed beneath it with its file and its claim."
                if (bundle / "audit" / "index.toml").is_file()
                else ""
            ),
            beside=_beside(bundle),
            tests_state=tests_state,
            review=(
                f"* `{REVIEWED}/<auditor>/{SCRATCH}/` holds the files each auditor left in "
                f"its own workspace: a finding that names a file under `{SCRATCH}/` names "
                "the one there, under the auditor that found it.\n"
                if (workspace / REVIEWED).is_dir()
                else ""
            ),
            earlier=(
                "5. **Check it against the earlier rounds listed above** before you add it. "
                "An obligation that pins again what an earlier round's finding called a demand "
                "the task does not make brings that finding back: tell the witness apart some "
                "other way. Correct an obligation a finding called wrong to what the fixed "
                "code does rather than delete it, where one of the benchmark's tests checks "
                "the value it pins: without it, an implementation that gets that value wrong "
                "verifies.\n"
                if history
                else ""
            ),
            budget=(
                f"{self.settings.repair_timeout_s / 60:.0f} minutes of wall clock and "
                f"{self.settings.repair_turns} turns"
            ),
            tools_rules=tools_rules(
                self.settings,
                task,
                self.backend,
                session_s=self.settings.repair_timeout_s,
                check=True,
            ),
            checked=checked,
            classes="\n".join(
                f"{number}. {text}"
                for number, text in enumerate((*self.backend.refused_cases, *_REFUSED_CASES), 1)
            ),
            witness=_REWITNESS if self.backend.witness_required else "",
            twins_index=(
                " and `twins/index.toml`" if (bundle / "twins" / "index.toml").is_file() else ""
            ),
            kept=_kept(self.backend),
            lacking=_lacking(lacking),
            artifacts=self._artifact_rules(
                task,
                read_text_or_empty(bundle / self.backend.solution_filename()),
                artifacts,
                on_record,
            ),
            tests=_tests_section(
                task, self._changed(task).tests, cases=self._changed(task).cases
            ),
            inputs_rules=inputs_rules,
            **relative,
        )
        write_text(workspace / BRIEF, prompt)
        request = SessionSpec(
            system=prompts.render("repair-agent-system", drafting=self._system()),
            prompt=prompt,
            cwd=workspace,
            submit="repair",
            fields=_REPAIR_FIELDS,
            required=_REPAIR_REQUIRED,
            tools=EDIT,
            writable=(bundle,),
            max_turns=self.settings.repair_turns,
            timeout_s=self.settings.repair_timeout_s,
            report=prompts.render("repair-agent-report"),
        )
        return self.session.run(request)

    def _artifact_rules(
        self, task: Task, solution: str, wanted: Sequence[str], on_record: Sequence[str]
    ) -> str:
        """What each file of ``wanted`` must be, a section each, for a repair to write it.

        The rules are the ones the request drafting the file states, from the same rules
        files; around them, what a repair needs that a reply does not: where the file goes
        and, for a case, its entry in the index beside it. ``solution`` is the solution file
        the repair is given.
        """
        extension = self.backend.extension
        try:
            allowed = variant.owned(solution, self.backend)
        except BenchproofError:
            allowed = ("impl",)
        sections: list[str] = []
        for name in (name for name in AUTHORED if name in wanted):
            if name == "twins":
                witness = _witness_rules(solution, self.backend, TWIN)
                section = prompts.render(
                    "repair-twins",
                    extension=extension,
                    twins_rules=_twins_rules(allowed),
                    witness=(
                        f"\n{_TWIN_WITNESS.format(extension=extension)}\n\n{witness}"
                        if witness
                        else ""
                    ),
                )
            elif name == "rivals":
                witness = _witness_rules(solution, self.backend, gate_battery.UNIQUENESS)
                section = prompts.render(
                    "repair-rivals",
                    extension=extension,
                    rivals_rules=prompts.render(
                        "rivals-rules",
                        kinds=self._suite(task, allowed),
                        regions=variant.rule(allowed),
                    ).rstrip(),
                    witness=f"\n{_RIVAL_WITNESS}\n\n{witness}" if witness else "",
                )
            elif name == "correspondence.md":
                section = prompts.render(
                    "repair-correspondence",
                    correspondence_rules=prompts.render(
                        "correspondence-rules", outside_rules=_OUTSIDE_BELOW
                    ).rstrip(),
                )
            elif name == DIFFERENTIAL_HARNESS:
                section = prompts.render(
                    "repair-conformance",
                    comparison_rules=self._comparison_rules(task, solution, on_record),
                )
            else:
                section = prompts.render(
                    "repair-axioms", axioms_rules=self._axioms_rules(task, quoted=False)
                )
            sections.append(section)
        return "".join(f"{section.rstrip()}\n\n" for section in sections)

    def _suite(self, task: Task, allowed: Sequence[str]) -> str:
        """The cases of the property-based test suite under this checker, for a repair.

        As drafting plans them (`_battery`): a second admissibility case among them where a
        PASS_TO_PASS test hands a function the fix changes an input (`_regression`).
        """
        states = self.backend.probe_brief
        lines = ["It holds these cases, each a file of its own named by its id:"]
        for kind, count in battery_plan(self.backend):
            ids = [f"`{kind}-{index}`" for index in range(1, count + 1)]
            named = ids[0] if len(ids) == 1 else f"{', '.join(ids[:-1])} and {ids[-1]}"
            lines.append(
                f'**{named}** (`kind = "{kind}"`, `expect = "{RIVAL_EXPECTATION[kind]}"`). '
                + _brief(kind, states)
            )
            if kind == gate_battery.UNIQUENESS:
                lines.append(
                    _DIFFERENT_MISTAKE.format(it="the pre-fix implementation in `twins/`")
                )
            if kind == "admissibility":
                if regression := self._regression(task):
                    lines.append(
                        f"**`{kind}-{count + 1}`**, of the same kind. "
                        + _brief(kind, states, regression)
                    )
                lines.append(
                    "An admissibility case writes its regions so:\n\n"
                    + variant.probe_rule(allowed, self.backend.probe_placement)
                )
        return "\n\n".join(lines)

    def lay_out_repository(self, task: Task, workspace: Path) -> tuple[str, str]:
        """Put a copy of the task's working copy in ``workspace``, with the tests as run.

        At `workspace/repository`, a copy, because a session that can write must not reach
        the working copy the other stages read the repository from. As the oracle stages
        the tests: the files it ships whole are written over the tree, and the test patch,
        where there is one, is applied to it and kept beside it as `tests.patch`, so each
        test reads as the benchmark runs it.

        Returns:
            What a session is told of the tests and patches in the copy (`_tests_state`),
            and why the test patch did not apply, or "".
        """
        repository = workspace / "repository"
        shutil.copytree(self._copy(task).root, repository, symlinks=True)
        staged = material.test_files(task)
        for source in staged:
            write_text(repository / source.path, source.content or "")
        patch = material.test_patch(task)
        refused = workcopy.apply(repository, patch) if patch else ""
        if patch:
            write_text(workspace / "tests.patch", patch)
        state = _tests_state(
            patch,
            refused,
            staged=bool(staged),
            golden=bool(task.reference.patch),
            repository=repository.name,
        )
        return state, refused

    def _formalization(
        self, task: Task, solution: str, check: CheckResult, *, rounds: int
    ) -> Formalization:
        """What this provider and backend made of ``solution``, before any other artifact."""
        return Formalization(
            task_key=task.key,
            backend=self.backend.name,
            provider=self.provider.name,
            model=self.provider.config.model,
            solution=solution,
            accepted=check.verified,
            check=check,
            rounds=rounds,
        )

    # ---- the repository -------------------------------------------------

    def _copy(self, task: Task) -> workcopy.WorkCopy:
        """The task's working copy, laid out once and reused by every stage that reads it."""
        found = self._copies.get(task.key)
        if found is None:
            found = workcopy.materialize(
                task, into=self.workdir / "workcopy", oracle=self.oracle
            )
            self._copies[task.key] = found
        return found

    def _fixed(self, task: Task) -> workcopy.Touched:
        """The source files the golden patch touches, as they read before it and after it.

        Empty for a task whose reference is not a patch, and for one whose files are not
        on this machine; the prompts then carry the patch alone.
        """
        return self._touched(task, task.reference.patch or "")

    def record(self, task: Task) -> dict[str, Any]:
        """What the golden patch and the test patch define or edit, as manifest.json keeps it.

        Read from the task's working copy once (`sites.record`).
        """
        found = self._records.get(task.key)
        if found is None:
            tests = self._touched(task, material.test_patch(task))
            found = sites.record(task, self._fixed(task), tests)
            self._records[task.key] = found
        return found

    def _material(self, task: Task) -> str:
        """What every request after the solution is shown of the task, rendered once.

        The statement, the tests the benchmark judges the fix by with the test patch, the
        golden patch, and each function it changes, whole, before it and after it
        (`material.task_block`): what the requests' own rules refer to, so the same block
        goes into each of them.
        """
        found = self._materials.get(task.key)
        if found is None:
            changed = self._changed(task)
            found = material.task_block(
                task, tests=changed.tests, fix=self._fixed(task), cases=changed.cases
            )
            self._materials[task.key] = found
        return found

    def _changed(self, task: Task) -> sites.Changed:
        """What the task's patches define or edit, as `sites.changed` reads it.

        In a repair, what the bundle's `manifest.json` records; when drafting, the working
        copy's reading (`record`).
        """
        if self.changed is not None:
            return self.changed
        return sites.changed(task, self.record(task))

    def _touched(self, task: Task, patch: str) -> workcopy.Touched:
        """The source files ``patch`` touches, before and after it, read once per task."""
        if not patch.strip():
            return workcopy.Touched()
        found = self._sources.get((task.key, patch))
        if found is None:
            found = workcopy.touched(task, self._copy(task), patch)
            self._sources[task.key, patch] = found
        return found

    # ---- stages ---------------------------------------------------------

    def _prove(
        self,
        task: Task,
        source: str,
        check: CheckResult,
        journal: Journal,
        *,
        label: str,
        kind: ProofKind = "claim",
    ) -> tuple[str, CheckResult, str]:
        """Hand a file the checker refused to a proof session, and keep what may be kept.

        Only under a backend whose files carry their proofs, where a refusal can be a
        proof missing a step rather than a claim that is false. The session writes the
        proof with the checker at hand (`prove.Prover`); its file replaces this one only
        when the specification and implementation are unchanged and the checker accepts
        it. ``kind`` says what the file claims: its own claim, or an admissibility probe's.

        Returns:
            The file, what the checker says of it, and what the session reported, in one
            line, empty where no session ran (`Draft.proof_session`).
        """
        if check.verified or not self.backend.proof_carrying or not self.settings.prove_agent:
            return source, check, ""
        if self.session is None:
            journal.note(
                f"{label}: the checker refused the file and this run has no agent session, "
                "so no proof session was run"
            )
            return source, check, ""
        proved = Prover(
            session=self.session,
            backend=self.backend,
            settings=self.settings,
            workdir=self.workdir,
        ).prove(task, source, check, label=label, kind=kind)
        spent = proved.session
        summary = (
            f"{label}: a proof session ({spent.get('turns', 0)} turn(s), "
            f"{spent.get('duration_s', 0)}s, reported {spent.get('status', 'nothing')})"
        )
        if proved.kept:
            journal.note(f"{summary} wrote a proof the checker accepts, which was kept")
            return proved.source, proved.check, f"{summary} wrote a proof the checker accepts"
        goal = f"; stuck on {spent['goal']}" if spent.get("goal") else ""
        journal.note(f"{summary} was not kept: {proved.refused}{goal}")
        return proved.source, proved.check, f"{summary} did not close it: {proved.refused}"

    def _solution_by_agent(
        self, task: Task, journal: Journal
    ) -> tuple[str, CheckResult, dict[str, Any]]:
        """Have the agent session write the solution file in a workspace of its own.

        The workspace is laid out as a repair session's is (`core.scripts.lay_out`): the
        solution file holding the backend's template, a copy of the repository with the
        benchmark's test patch applied or the test files its oracle ships written in, so each
        test reads as the benchmark runs it, and the files the fix touches as they read after
        it. The session reads what the file has to
        be about there instead of in excerpts chosen for it, runs the checker itself, and
        reports (`_DRAFT_FIELDS`). Only the solution file is read back, and it is put to the
        checker again here.

        Returns:
            The file, empty when the session left none that reads as one; what the checker
            says of it; and what `manifest.json` keeps of the session.

        Raises:
            ProviderError: The session failed before it wrote the solution file, whether it
                could not be started or stopped part-way.
        """
        if self.session is None:
            raise ProviderError(NO_SESSION.format(stage="drafting the solution"))
        workspace = self.workdir / "draft"
        copy = lay_out(workspace, task, self.backend.name, self.settings)
        target = copy.root / self.backend.solution_filename()
        template = self.backend.template()
        write_text(target, template)
        repository = workspace / "repository"
        tests_state, refused = self.lay_out_repository(task, workspace)
        if refused:
            journal.note(
                f"solution: the test patch does not apply to the repository: {refused}"
            )
        fixed = self._fixed(task).after
        for path, text in fixed.items():
            write_text(workspace / FIXED / path, text)
        sites = _sites_block(task, self._changed(task).golden)
        tests = self._changed(task).tests
        request = SessionSpec(
            system=self._system(),
            prompt=prompts.render(
                "draft-agent",
                task=task.key,
                workspace=workspace.as_posix(),
                file=target.relative_to(workspace).as_posix(),
                task_file=copy.task_path.relative_to(workspace).as_posix(),
                reference=(
                    f" `{copy.reference_path.relative_to(workspace).as_posix()}` beside it "
                    "is the golden patch as a unified diff."
                    if task.reference.patch
                    else ""
                ),
                repository=repository.name,
                copy=self._copy(task).detail,
                tests_state=tests_state,
                fixed=(
                    f"* `{FIXED}/` holds each source file the fix touches, whole, as it reads "
                    "after it: the code the comparison calls, so a default, a guard or a "
                    "helper outside the hunks of the patch is there too.\n"
                    if fixed
                    else ""
                ),
                scratch=SCRATCH,
                tests=_tests_section(task, tests, cases=self._changed(task).cases),
                sites=sites,
                tools_rules=tools_rules(
                    self.settings,
                    task,
                    self.backend,
                    session_s=self.settings.draft_timeout_s,
                ),
                budget=(
                    f"{self.settings.draft_timeout_s / 60:.0f} minutes of wall clock and "
                    f"{self.settings.draft_turns} turns"
                ),
            ),
            cwd=workspace,
            submit="draft",
            fields=_DRAFT_FIELDS,
            required=_DRAFT_REQUIRED,
            tools=EDIT,
            writable=(target,),
            max_turns=self.settings.draft_turns,
            timeout_s=self.settings.draft_timeout_s,
            report=prompts.render("draft-agent-report"),
        )
        try:
            outcome = self.session.run(request)
        except ProviderError as exc:
            # What the session left in the file is taken whatever it reports, so one that
            # failed after writing it has drafted it; one that left the template has not.
            if not _left(target, template):
                raise
            journal.note(f"solution: the drafting session failed part-way: {exc}")
            record: dict[str, Any] = {
                "by": "session",
                "model": self.session.model,
                "detail": str(exc),
            }
        else:
            payload, packed = _unpacked(outcome.payload or {}, _DRAFT_FIELDS)
            if packed:
                journal.note(
                    "solution: the drafting report wrote "
                    + ", ".join(f"`{name}`" for name in packed)
                    + " inside another field, and they were read out of it"
                )
                outcome = replace(outcome, payload=payload)
            record = {
                "by": "session",
                "model": self.session.model,
                **outcome.record(tuple(_DRAFT_FIELDS)),
            }
            journal.note(
                f"solution: a drafting session ({outcome.turns} turn(s), {outcome.tool_uses} "
                f"tool use(s), {outcome.duration_s:.0f}s) reported "
                f"{payload.get('status') or 'nothing'}"
                + (f": {payload['summary']}" if payload.get("summary") else "")
                + (f" ({outcome.detail})" if outcome.detail else "")
            )
            if payload.get("blocked"):
                journal.note(
                    "solution: what the drafting session reported blocked it: "
                    f"{payload['blocked']}"
                )
        written = _left(target, template)
        why = ""
        if not written:
            why = "the drafting session wrote no solution file"
        else:
            try:
                markers.parse(written, self.backend.comment)
            except BenchproofError as exc:
                why = f"the solution file the drafting session left cannot be read: {exc}"
        if why:
            journal.note(f"solution: {why}")
            return "", CheckResult.unknown(why), record
        return written, self._check(written, "solution-session"), record

    def _twin(
        self, task: Task, solution: str, system: str, journal: Journal
    ) -> tuple[Draft, ...]:
        """Draft the pre-fix implementation, when the task ships the code the fix replaced.

        The pre-fix implementation is offered the regions a variant owns (`variant.owned`), in
        file order, exactly as a rival is. Every implementation region, because a model of
        several functions keeps the pre-fix difference in whichever of them the fix changed and
        a pre-fix implementation offered only the first could not write it there; and the proof
        of them, because a pre-fix implementation that could not touch the proof would ship the
        solution file's -- a tactic script tuned to the fixed implementation, which stops
        closing over the pre-fix one whether or not the specification tells the two programs
        apart.

        Under a checker where a reshaped implementation stops any proof closing
        (`Backend.witness_required`), the pre-fix implementation is asked for a refutation
        witness as well, as a reject case of the property-based test suite is: the claim that
        makes its refusal the specification's.

        Whether there is a pre-fix implementation to draft is `material.has_pre_fix`, the
        predicate the discriminates gate reads, so the two agree about which tasks have one.
        """
        if not material.has_pre_fix(task):
            journal.note(
                "the task ships no code the fix replaced, so no pre-fix implementation was "
                "drafted; the discrimination check (spec.discriminates) reads the same "
                "predicate and reports the question as not applicable rather than the pre-fix "
                "implementation as missing"
            )
            return ()
        draft = self._variant(
            TWIN,
            TWIN,
            TWIN,
            self._twin_prompt(task, solution),
            solution,
            system,
            journal,
            allowed=variant.owned(solution, self.backend),
            task=task,
        )
        return (draft,) if draft else ()

    def _accepted_proof(self, solution: str, source: str) -> str | None:
        """``source`` with the solution file's proof regions in place of its own.

        None where that does not make it admissible either: the case's implementation
        regions reach for a banned token too, or the file cannot be spliced.
        """
        try:
            restored = markers.transplant(source, solution, self.backend.comment, "proof")
        except BenchproofError:
            return None
        if restored == source or not variant.scope(solution, restored, self.backend):
            return None
        return restored

    def _twin_prompt(self, task: Task, solution: str) -> str:
        """The request for the pre-fix implementation of ``solution``."""
        return prompts.render(
            "twin",
            solution=solution,
            material=self._material(task),
            twins_rules=_twins_rules(variant.owned(solution, self.backend)),
            witness=_witness_block(solution, self.backend, TWIN),
        )

    def _battery(
        self, task: Task, solution: str, system: str, journal: Journal, twins: Sequence[Draft]
    ) -> tuple[Draft, ...]:
        """Draft the property-based test suite, one rival at a time.

        Rivals of the same kind are drafted in sequence and each is told what the earlier ones
        did, because two independent requests at temperature zero would otherwise write the same
        attack twice and the property-based test suite would claim a breadth it does not have. A
        uniqueness case is shown the pre-fix implementation for the same reason: the mistake the
        pre-fix implementation makes is the one `spec.discriminates` already asks about, so a
        rival repeating it adds nothing. Whether two cases really are the same case is
        `spec.strength.battery`'s to decide, over every case rather than within one kind.
        """
        drafts: list[Draft] = []
        allowed = variant.owned(solution, self.backend)
        twin = twins[0].source if twins else ""
        for kind, count in battery_plan(self.backend):
            tried: list[str] = []
            # Each case's PASS_TO_PASS tests: none, but for a second probe at their inputs.
            regressions = [""] * count
            if kind == "admissibility" and (shown := self._regression(task)):
                regressions.append(shown)
            for index, regression in enumerate(regressions, 1):
                rival_id = f"{kind}-{index}"
                prompt = self._rival_prompt(
                    task, solution, kind, tried, allowed, twin=twin, regression=regression
                )
                draft = self._variant(
                    "rival",
                    rival_id,
                    kind,
                    prompt,
                    solution,
                    system,
                    journal,
                    allowed=allowed,
                    task=task,
                )
                if draft is None:
                    continue
                tried.append(_body(draft.source, self.backend))
                drafts.append(draft)
        if not drafts:
            journal.note(
                "no rival survived drafting, so the bundle ships no property-based test suite"
            )
        return tuple(drafts)

    def _rival_prompt(
        self,
        task: Task,
        solution: str,
        kind: str,
        tried: Sequence[str],
        allowed: tuple[str, ...],
        *,
        twin: str = "",
        regression: str = "",
    ) -> str:
        """The request for one case of the property-based test suite of this kind.

        ``twin`` is the pre-fix implementation, shown to a uniqueness case only: the mistake it
        makes is the one the bundle already tests, so a rival repeating it is set aside.
        ``regression`` is the PASS_TO_PASS tests a probe takes its inputs from instead of the
        FAIL_TO_PASS tests' (`_regression`).
        """
        return prompts.render(
            "rival",
            solution=solution,
            material=self._material(task),
            case=_CASE[kind],
            rivals_rules=prompts.render(
                "rivals-rules",
                kinds=_brief(kind, self.backend.probe_brief, regression),
                regions=(
                    variant.probe_rule(allowed, self.backend.probe_placement)
                    if kind == "admissibility"
                    else variant.rule(allowed)
                ),
            ).rstrip(),
            tried=_tried_block(tried),
            twin=_twin_block(_body(twin, self.backend))
            if kind == gate_battery.UNIQUENESS
            else "",
            witness=_witness_block(solution, self.backend, kind),
        )

    def _regression(self, task: Task) -> str:
        """The PASS_TO_PASS tests a second probe takes its inputs from, as prompt text, or "".

        Those the test patch adds or edits, and those whose own code calls a function the fix
        changes, from the test patch's files as they read after it
        (`material.regression_block`).
        """
        changed = self._changed(task)
        return material.regression_block(
            task,
            self._touched(task, material.test_patch(task)).after,
            sites.calls(sites.sites(task, changed.golden)),
            changed.tests,
            changed.cases,
        )

    def _correspondence(
        self,
        task: Task,
        solution: str,
        journal: Journal,
        *,
        drafted: dict[str, Any],
    ) -> str:
        """Draft `correspondence.md`, and what the specification leaves out.

        It says how the implementation corresponds to the fix, operation by operation. One
        request. Nothing reads the document mechanically: it is the claim the
        equivalence review checks, and the account of omissions the faithfulness review
        reads first, so an omission or a wrong row is theirs to find. ``drafted`` is what
        the session that drafted the solution reported, whose account of what it left out
        the two sections that say so start from (`_EXCLUSIONS`).
        """
        prompt = prompts.render(
            "correspondence",
            solution=solution,
            material=self._material(task),
            drafted=_drafted_block(drafted),
        )
        system = self._system("correspondence-system")
        reply = self.turn("correspondence", prompt, system, journal, take=_prose)
        return reply[0] if reply is not None else ""

    def _conformance(
        self,
        task: Task,
        solution: str,
        journal: Journal,
        *,
        correspondence: str = "",
    ) -> str:
        """Draft `conformance.py` comparing the implementation with the repository's own code.

        The runnable form of the `impl` region is that region with the checker's own
        annotations deleted, a mechanical projection the session computes and puts in the
        prompt: a Python implementation is copied as written, and any other is ported into
        Python line by line (`conformance-port`). The model's work is the
        comparison -- which function in the repository to reach, how to reach it, and what
        inputs to draw, the ones the benchmark's tests build first. ``correspondence`` is the
        bundle's `correspondence.md`, whose `Outside the bridge` entries the drafting request
        shows (`_outside_block`).

        `conformance.py` is then run where the gate will run it and sent back once when the run
        establishes nothing, such as a function it declares it cannot compare or a program that
        fails to start, which only a run shows.

        Skipped when there is nothing to compare against: a task with no reference
        solution has no repository code the implementation represents, and the gate
        reports that as not applicable rather than as a missing `conformance.py`.
        """
        if task.reference.is_empty:
            return ""
        # One body per function the specification models, each marked with the region
        # `conformance.py` has to carry it in when there is more than one.
        bodies = differential.executables(solution, self.backend)
        executable = (
            next(iter(bodies.values()))
            if len(bodies) == 1
            else "\n\n".join(
                markers.wrap(differential.COMMENT, name, body) for name, body in bodies.items()
            )
        )

        python = self.backend.extension == ".py"
        prompt = prompts.render(
            "conformance",
            solution=solution,
            material=self._material(task),
            code=(
                "This is its implementation with the checker's own annotations taken out, "
                "which is the code that has to run:"
                if python
                else f"This is its implementation, in {self.backend.language}, which Python "
                "cannot run, so `conformance.py` runs a port of it into Python:"
            ),
            implementation=executable,
            comparison_rules=self._comparison_rules(task, solution, ()),
            outside=_outside_block(correspondence),
        )
        system = self._system("program-system")
        taken = self.turn("conformance", prompt, system, journal, take=extract.harness)
        if taken is None:
            journal.note(
                f"no {DIFFERENTIAL_HARNESS} was drafted, so the conformance gate has "
                "nothing to run and will leave this bundle short of the oracle level"
            )
            return ""

        # A declared gap is sent back once a session, asking for a bridge. The request is
        # kept here, so that a redraft declaring a gap again is believed.
        bridged: list[str] = []

        def objection(harness: str, attempt: int) -> tuple[str, str]:
            reported = differential.skipped_regions(harness, solution, self.backend.comment)
            return self._objection(
                task, harness, bodies, attempt, journal, bridged=bridged, skipped=reported
            )

        source, wrong = self._redrafted(prompt, system, journal, taken, objection=objection)
        if wrong in bridged:
            # Kept unchanged when asked for a bridge, or the redraft could not be used.
            journal.note(
                f"the {DIFFERENTIAL_HARNESS} ends its redrafts still reporting a function it "
                f"cannot compare ({wrong}), so the report stands and the conformance gate "
                "is what weighs it"
            )
        elif wrong:
            journal.note(
                f"the {DIFFERENTIAL_HARNESS} is still unusable after its redraft "
                f"({wrong}), so the "
                "conformance gate will not pass this bundle and the repair loop is what has to "
                "address it"
            )
        return source

    def _comparison_rules(self, task: Task, solution: str, on_record: Sequence[str]) -> str:
        """How `conformance.py` is written and what it is held to (`comparison-rules.md`).

        ``on_record`` names the functions the bundle has inputs on record for.
        """
        return prompts.render(
            "comparison-rules",
            sites=_compared_sites(task, self._changed(task).golden, self._fixed(task).after),
            assumed=_assumed(solution, self.backend.comment),
            conformance_rules=self._conformance_rules(task),
            recorded=_recorded(on_record),
        ).rstrip()

    def _redrafted(
        self,
        prompt: str,
        system: str,
        journal: Journal,
        taken: tuple[str, str],
        *,
        objection: Callable[[str, int], tuple[str, str]],
    ) -> tuple[str, str]:
        """Send a drafted `conformance.py` back once, in the conversation that wrote it.

        A stage that can see the gate will reject what it just wrote asks again rather
        than shipping it with a note: a bundle written anyway costs a full judging pass to
        be told what was already known here. It asks in the same conversation, so the
        redraft is a correction of the program the model wrote and can see, not a second
        attempt that may repeat the first.

        Args:
            prompt: The request that drafted the program, which opens the conversation.
            taken: The program drafted and the reply it came from.
            objection: What is wrong with a program, given it and the round it was drafted
                in: the objection and the follow-up saying so, both "" when nothing is.

        Returns:
            The program drafted last, and the objection still standing against it, ""
            when none is. A redraft that is not a program, or repeats the first one
            unchanged, leaves the first one in place.
        """
        source, reply = taken
        wrong, follow_up = objection(source, 1)
        if not wrong:
            return source, wrong
        journal.note(
            f"the {DIFFERENTIAL_HARNESS} drafted in attempt 1 cannot establish "
            f"anything: {wrong}"
        )
        messages = [Message.user(prompt), *quoted(reply), Message.user(follow_up)]
        try:
            completion = self.ask("conformance", 2, messages, system, journal)
        except ProviderError as exc:
            # What was drafted is kept, as `turn` keeps it: the gate is still the one to
            # judge it, and the rest of the session is worth finishing.
            journal.note(f"conformance round 2: the provider failed: {exc}")
            return source, wrong
        try:
            redrafted = extract.harness(completion.text)
        except BenchproofError as exc:
            journal.note(f"conformance round 2: {self.unusable(exc, completion)}")
            return source, wrong
        if redrafted == source:
            return source, wrong
        return redrafted, objection(redrafted, 2)[0]

    def _objection(
        self,
        task: Task,
        harness: str,
        bodies: dict[str, str],
        attempt: int,
        journal: Journal,
        *,
        bridged: list[str],
        skipped: Sequence[str],
    ) -> tuple[str, str]:
        """Why this `conformance.py` cannot establish anything, and the follow-up that says so.

        Both are "" when nothing says so. What the file shows is asked first, since it
        needs no container; a `conformance.py` that passes that is run once.
        ``bridged`` holds the objections that asked for a bridge this session, and gains
        the one this run makes, if it makes one. ``skipped`` names the implementation
        regions whose function the program reports it does not compare
        (`differential.skipped_regions`), which it need not copy.
        """
        wrong = self._unusable(task, harness, bodies, skipped=skipped)
        if wrong:
            return wrong, prompts.render("conformance-repair", objection=wrong)
        ran = self._ran(task, harness, attempt, journal, bridged=bridged)
        if ran is None:
            return "", ""
        wrong, output = ran
        # A declared gap asks for a bridge; anything else, for the program corrected.
        demand = prompts.render("conformance-bridge").strip() if wrong in bridged else _CORRECT
        return wrong, prompts.render(
            "conformance-run",
            objection=wrong,
            output=_tail(output, OUTPUT_LIMIT) or "(nothing)",
            demand=demand,
        )

    def _ran(
        self,
        task: Task,
        harness: str,
        attempt: int,
        journal: Journal,
        *,
        bridged: list[str],
    ) -> tuple[str, str] | None:
        """Run `conformance.py` as the gate will, and say what makes the run establish nothing.

        Returns the objection and what the program printed, or None when the run
        compared something or could not be made. The run is the gate's -- the task's own
        environment, the golden patch applied, the same budget -- and so are the
        objections, in its order:

        * a run the budget cut short, which unlike one the environment could not make is
          the program's doing;
        * a comparison with a name no module it imports defines;
        * a `benchproofer:` line no line of the protocol parses, quoted beside the shape
          the protocol gives it: the gate counts a comparison printed that way as none,
          and without the line the redraft would be told only that it compared nothing;
        * a function it reports it cannot compare, sent back once asking for a bridge,
          since that is as often a function easily reached -- a method whose object can be
          built, a wrapper around a callable a stub can stand in for -- as one nothing
          here can call, and believed when a redraft declares it again. A report from a
          failed import, or from a program that failed having compared nothing, is the
          program failing to start, and is sent back as the crash it is;
        * a failed run naming no disagreement, and a run that compared nothing.

        A disagreement, and an input it reports it did not compare (`blocked`, read as the
        gate reads it), are left alone for the gate to weigh: either may be a finding about
        the specification, and put back to the model that wrote the program, either is too
        easily silenced by changing the measurement -- no longer drawing the input the
        repository raises on, say -- which turns a finding into a pass.
        """
        if self.oracle is None:
            return None
        result = self.oracle.probe(
            task,
            Program(source=harness, label="conformance", with_reference=True),
            workdir=self.workdir / f"conformance-run-{attempt}",
            timeout_s=self.settings.harness_timeout_s,
        )
        output = result.output
        # Before the status, which records a run the budget cut short as an error.
        if result.timed_out:
            return (
                f"it did not finish within {self.settings.harness_timeout_s} seconds "
                f"({result.detail}), so it reported nothing; it has to stop drawing when "
                "its own deadline passes and print what it compared by then"
            ), output
        if result.status in (OracleStatus.UNAVAILABLE, OracleStatus.ERROR):
            journal.note(
                f"the {DIFFERENTIAL_HARNESS} could not be run while drafting "
                f"({result.detail}), so the conformance gate is the first to run it"
            )
            return None
        adrift = differential.ungrounded(output, harness)
        if adrift and result.resolved:
            return (
                "it reports comparing " + ", ".join(f"`{name}`" for name in adrift) + ", "
                "which names no module it imports, so what it compared the implementation "
                "with is code of its own rather than the repository's"
            ), output
        if differential.disagreements(output):
            return None
        unread = differential.unparsed(output)
        if unread:
            # Before everything below, which reads the report as though it were whole.
            return (
                f"it printed {len(unread):,} line(s) starting with `benchproofer:` that no "
                "line of the protocol parses, so the gate reads nothing from them and treats "
                "a comparison reported that way as none: "
                + "; ".join(
                    f"`{line}`, where the protocol has "
                    + " or ".join(f"`{shape}`" for shape in differential.shapes_for(line))
                    for line in differential.clipped(unread)
                )
                + ". Print each report in its shape: a function as the one dotted path it "
                "is reached at, with no space in it, a count as a number in digits right "
                "after the function, and any description after those"
            ), output
        if differential.blocked(output):
            return None
        declined = differential.unsupported(output)
        if declined:
            listed = "; ".join(f"`{item}`" for item in declined)
            imported = any(_IMPORT_FAILED.search(item) for item in declined)
            if imported or _RAISED_ON_IMPORT.search(output):
                return (
                    f"it reports {listed} as skipped because an import failed, which "
                    "is this program failing to start rather than a function nothing here "
                    "can call: the module path it imports is wrong, or the name is not "
                    "defined there"
                ), output
            if not result.resolved and not differential.compared(output):
                return (
                    f"it failed ({result.detail}) having compared nothing, so it does not "
                    f"run in the task's environment; it reports {listed} as skipped, "
                    "but a program that never reached a comparison has not found a "
                    "function nothing here can call"
                ), output
            if bridged:
                journal.note(
                    f"the {DIFFERENTIAL_HARNESS} still reports {listed} as skipped after "
                    "it was asked once to reach it another way, so the report stands and the "
                    "conformance gate is what weighs it"
                )
                return None
            wrong = (
                f"it reports {listed} as skipped, so it establishes nothing about that "
                "part of the implementation"
            )
            bridged.append(wrong)
            return wrong, output
        if not result.resolved:
            return (
                f"it failed without naming a disagreement ({result.detail}), so it does "
                "not run in the task's environment"
            ), output
        if not differential.compared(output):
            return "it ran and reported comparing nothing", output
        return None

    def _unusable(
        self, task: Task, harness: str, bodies: dict[str, str], *, skipped: Sequence[str]
    ) -> str:
        """Why this `conformance.py` cannot establish anything, or "" when nothing says so.

        The objections are the gate's own, read off the file rather than from a run, so
        none needs a container to decide them: a `conformance.py` importing a name the
        repository does not define dies on its first line; and one that does not contain
        the implementation verbatim, where it runs as written, compares a second
        implementation, apart from the regions in ``skipped``, which it does not compare.

        What `conformance.py` imports is judged against the repository itself where there is a
        working copy of it, and against the fixed files the fix touches: judged against
        the task's text alone, a real class the statement and the patch never mention
        would be reported as missing.
        """
        copy = self._copy(task)
        known = "\n".join((material.citable(task), *self._fixed(task).after.values()))
        unknown = differential.invented(harness, known, tree=copy.root if copy.whole else None)
        if unknown:
            return (
                "it imports " + ", ".join(f"`{name}`" for name in unknown) + ", which the "
                "repository does not define, so it will fail on its import line"
            )
        # Only where a runnable form exists at all: an implementation using the
        # verifier's own values has to be translated, and the gate reads that as the
        # weaker kind of comparison rather than as a `conformance.py` that fell short.
        direct = all(
            differential.provenance(self.backend.extension, body, self.backend.foreign_tokens)
            == differential.DIRECT
            for body in bodies.values()
        )
        missing = differential.uncopied(harness, bodies, skipped=skipped) if direct else None
        if missing is not None:
            return (
                "it does not contain the verified implementation verbatim, so what it "
                "compares is a second implementation rather than the one the checker "
                f"accepted: {differential.lacking(missing)}"
            )
        return ""

    def _axioms(self, task: Task, solution: str, journal: Journal) -> str:
        """Draft `axioms.py` grounding whatever the specification assumes.

        Skipped when the `axioms` region names no callee, which is the common case: a task
        whose callees are all part of the implementation has nothing to ground, and the
        gate reports that as not applicable rather than as missing.

        The declarations the gate holds `axioms.py` to carrying are written in by the
        tool. What running it finds is `spec.axioms_grounded`'s to report, and the repair's
        to address.
        """
        region = markers.parse(solution, self.backend.comment).get("axioms")
        if region is None:
            return ""
        assumed = callees(declared(region.text, self.backend.comment))
        if not assumed:
            return ""

        prompt = prompts.render(
            "axioms",
            solution=solution,
            material=self._material(task),
            callees=", ".join(f"`{callee}`" for callee in assumed),
            axioms_rules=self._axioms_rules(task, quoted=True),
        )

        def take(reply: str) -> str:
            drafted = extract.code(reply)
            # Where the gate holds `axioms.py` to carrying the region's declarations, the
            # tool writes them in rather than asking for a copy that can come back reflowed.
            if self.backend.extension != ".py":
                return drafted
            return with_declarations(drafted, region.text, self.backend.comment)

        taken = self.turn("axioms", prompt, self._system("program-system"), journal, take=take)
        if taken is None:
            journal.note(
                f"the specification assumes {', '.join(assumed)} and no {HARNESS} was "
                "drafted, so the axioms gate will fail this bundle"
            )
            return ""
        return taken[0]

    # ---- shared machinery ------------------------------------------------

    def _variant(
        self,
        stage: str,
        variant_id: str,
        kind: str,
        prompt: str,
        solution: str,
        system: str,
        journal: Journal,
        *,
        allowed: Sequence[str],
        task: Task,
    ) -> Draft | None:
        """Draft one variant of the accepted solution: a pre-fix implementation or a rival.

        The regions the model writes are spliced into the solution file, so the variant
        shares its specification byte for byte; a probe's function written at the top level
        after the implementation region goes into the region with it, since that is where a
        model asked for a function after the shipped body writes one. The checker runs
        once for the record, and the variant is kept whatever it says: the gate judges it.

        A case meant to be refused whose proof gives up gets the solution file's proof back
        where a witness attributes its refusal. A case that must verify and is refused goes to a
        proof session (`_prove`), and a witness the checker refuses to one of its own
        (`_prove_witness`).
        """
        wanted = _wants_witness(self.backend, kind)

        def take(reply: str) -> str:
            return variant.assemble(
                solution,
                reply,
                self.backend,
                allowed=allowed,
                probe=kind == "admissibility",
                witnessed=wanted,
            )

        taken = self.turn(stage, prompt, system, journal, take=take)
        if taken is None:
            return None
        source, reply = taken
        rationale = extract.field(reply, "RATIONALE")
        claim = extract.witness(reply) if wanted else ""
        expectation = RIVAL_EXPECTATION.get(kind)
        # A case meant to be refused whose own proof uses a tactic the solution file does not --
        # a pre-fix implementation or a wrong rival ending in `sorry`, since no honest proof of
        # it closes -- is rejected by the gate unread. Its witness, not its proof, is what shows
        # the specification rejects it, so the solution file's proof in its place loses nothing.
        if (
            wanted
            and not variant.scope(solution, source, self.backend)
            and (restored := self._accepted_proof(solution, source))
        ):
            journal.note(
                f"{stage} {variant_id}: its proof reached for a tactic the solution file "
                "does not use, so the solution file's proof was put back; its witness is what "
                "shows the specification rejects it"
            )
            source = restored
        check = self._check(source, f"{stage}-{variant_id}")
        attempted = ""
        if expectation == "verify" and not check.verified:
            # A probe's assertions sit in the implementation region rather than in the
            # proof: their proofs are the session's to write, and what each states is not.
            source, check, attempted = self._prove(
                task,
                source,
                check,
                journal,
                label=f"{stage}-{variant_id}",
                kind="probe" if kind == "admissibility" else "claim",
            )

        judged_by = (
            "discrimination check" if kind == TWIN else "property-based falsification gate"
        )
        if wanted and not claim:
            journal.note(
                f"{stage} {variant_id}: no refutation witness in the reply, so for the "
                f"{judged_by} no claim proved at one input shows that the specification, "
                "rather than the case's own proof, is what rejects it"
            )
        elif wanted:
            claim, tried = self._prove_witness(
                task, source, claim, journal, label=f"{stage}-{variant_id}", accepted=solution
            )
            # A pre-fix implementation and a case of the property-based test suite alike record
            # what a proof session on their witness reported (`Draft.proof_session`), which is
            # how `spec.discriminates` and the property-based test suite tell a witness nobody
            # could prove from one nobody tried.
            attempted = tried or attempted
        return Draft(
            id=variant_id,
            kind=kind,
            rationale=rationale or f"{kind} variant of the reference implementation",
            source=source,
            check=check,
            witness=claim,
            proof_session=attempted,
        )

    def _prove_witness(
        self,
        task: Task,
        source: str,
        claim: str,
        journal: Journal,
        *,
        label: str,
        accepted: str,
    ) -> tuple[str, str]:
        """A variant's refutation witness, its proof written by a proof session if it fails.

        A witness claims, at one input, that the variant -- a reject case of the property-based
        test suite, or the pre-fix implementation -- violates the specification, and its proof
        is what a request writes blind: which tactic closes a goal depends on the goal the
        checker prints. So it is built as the gates build it (`witness.probe`), and one the
        checker refuses goes to a proof session with its statement held as written. What the
        session wrote replaces it only when it states the same claims and holds of the variant;
        whether it also fails against the reference implementation is the gate's to judge. A
        witness the gate's screens refuse before building it (`witness.objections`) gets no
        proof session, which could not make it one the gate admits.

        Returns:
            The witness, and what a proof session on it reported in one line, empty where
            none ran.
        """
        if (
            not self.backend.proof_carrying
            or not self.settings.prove_agent
            or self.session is None
        ):
            return claim, ""
        refused = witness.objections(accepted, source, claim, self.backend)
        if refused:
            journal.note(
                f"{label}: its refutation witness is one the gates refuse before building it "
                f"({'; '.join(refused)}), so no proof session was spent on it"
            )
            return claim, ""
        comment = self.backend.comment
        # The gate's build, with the witness in the last of the proof regions it empties
        # rather than after them, so the session's edits there are the witness's alone.
        emptied = witness.probe(source, "", self.backend)
        try:
            region = markers.named(markers.parse(emptied, comment), "proof")[-1]
            framed = markers.replace_region(emptied, comment, region, claim.strip())
        except (BenchproofError, IndexError):
            return claim, ""
        check = self._check(framed, f"{label}-witness")
        if check.verified or not check.decided:
            return claim, ""
        proved = Prover(
            session=self.session,
            backend=self.backend,
            settings=self.settings,
            workdir=self.workdir,
        ).prove(task, framed, check, label=f"{label}-witness", kind="witness")
        spent = proved.session
        summary = (
            f"{label}: a proof session on its refutation witness ({spent.get('turns', 0)} "
            f"turn(s), reported {spent.get('status', 'nothing')})"
        )
        written = ""
        if proved.kept:
            with suppress(BenchproofError):
                written = markers.parse(proved.source, comment)[region].text.strip()
        heads = (*_WITNESS_HEADS, *self.backend.proof_tokens)
        if not written:
            why = proved.refused or "it wrote no witness"
            journal.note(f"{summary} was not kept: {why}")
            return claim, f"{summary} did not close it: {why}"
        if markers.claims(written, comment, heads) != markers.claims(claim, comment, heads):
            journal.note(f"{summary} was not kept: it changed what the witness states")
            return claim, f"{summary} was not kept: it changed what the witness states"
        journal.note(f"{summary} wrote a proof the checker accepts, which was kept")
        return written, f"{summary} wrote a proof the checker accepts"

    def _check(self, source: str, label: str) -> CheckResult:
        """Run the checker on ``source`` in a workdir of its own, for feedback."""
        return self.backend.check(
            source,
            workdir=self.workdir / label,
            timeout_s=self.backend.budget(self.settings.verify_timeout_s),
        )

    def _system(self, name: str = "system") -> str:
        """Render a system prompt for this backend.

        ``system`` for what writes regions of the solution file: the drafting session, the
        pre-fix implementation and the property-based test suite's rivals; ``program-system``
        for the requests writing `conformance.py` and `axioms.py`; ``correspondence-system``
        for the one writing `correspondence.md`. Each is handed only the fields it names.
        """
        banned = self.backend.banned_tokens
        fields: dict[str, Callable[[], str]] = {
            "backend": lambda: self.backend.name,
            "language": lambda: self.backend.language,
            "kind": lambda: str(self.backend.kind),
            "kind_note": lambda: _KIND_NOTE[self.backend.kind],
            "comment": lambda: self.backend.comment,
            "banned": lambda: (
                "Do not use " + ", ".join(f"`{token.strip()}`" for token in banned)
                if banned
                else "Do not discharge an obligation by assuming it."
            ),
            "imports": self._import_rule,
            "assumptions": self.backend.callees,
            "guidance": self.backend.guidance,
        }
        named = set(_FIELD.findall(prompts.template(name)))
        return prompts.render(
            name, **{key: value() for key, value in fields.items() if key in named}
        )

    def _import_rule(self) -> str:
        """What this backend lets the file reach for outside itself.

        A rule the gate enforces and the prompt never states costs a round for nothing:
        a session copying fixed code that reaches for the clock or a source of
        randomness writes the import that code had, and the file is rejected for a
        module nobody told it about. Naming the list also names the way out, which is
        the same one every callee stated as an axiom takes. A backend that polices no list still
        has the tool's own limit, since the file is checked where the tool writes it.
        """
        allowed = self.backend.allowed_imports
        if not allowed:
            return (
                "The checker reads this file where Benchproofer writes it and fetches "
                "nothing for it, so whatever the file imports or includes has to come "
                "with the toolchain: a library the checker ships is fine, a file of "
                "your own beside it is not."
            )
        listed = ", ".join(f"`{name}`" for name in allowed)
        return (
            f"The file may import {listed}, and nothing else. Where the fixed code "
            "calls something outside that list -- the clock, the filesystem, the "
            "network, a source of randomness -- assume that callee in the `axioms` "
            "region rather than importing it: an implementation whose result depends on "
            "what the checker cannot see is not one it can decide anything about."
        )

    def _conformance_rules(self, task: Task) -> str:
        """The rules `conformance.py` is held to, at this run's target and deadline."""
        return protocol_for(
            self.settings.inputs_for(task.benchmark),
            self.settings.harness_timeout_s * DEADLINE_SHARE,
            ported=self.backend.extension != ".py",
        )

    def _axioms_rules(self, task: Task, *, quoted: bool) -> str:
        """What `axioms.py` must be and do (`axioms-rules.md`).

        ``quoted`` says whether Benchproofer writes the quotation of the declarations in
        (`_grounding_rule`).
        """
        return prompts.render(
            "axioms-rules",
            verbatim=self._grounding_rule(quoted=quoted),
            protocol=PROTOCOL,
            reference=AFTER_REFERENCE if task.reference.patch else "",
        ).rstrip()

    def _grounding_rule(self, *, quoted: bool) -> str:
        """The containment rule the axioms gate will apply to `axioms.py`.

        ``quoted`` says whether Benchproofer writes the quotation in, as it does for an
        `axioms.py` drafted by a request. A repair keeps the quotation in step itself, which
        its request says of both programs (`_kept`).
        """
        if self.backend.extension != ".py":
            return (
                f"It restates each axiom and each model from {self.backend.language} in "
                "Python, close enough that a reviewer can put the two side by side and see "
                "they say the same thing."
            )
        who = (
            "Benchproofer writes them in itself, quoted as comments after your program, so you "
            "need not copy them."
            if quoted
            else "The declarations are quoted as comments after the program."
        )
        return (
            "It is held to the declarations of the `axioms` region, as code or quoted, so that "
            f"the model it checks is the one the checker was given. {who} Do not import or run "
            "a declaration written in the verifier's contract library: the task's environment "
            "does not have that library, and a program that imports it does not start. A "
            "declaration that is plain Python may be kept as code and called."
        )


def _repaired_before(bundle: Path) -> bool:
    """Whether `manifest.json` of the bundle at ``bundle`` records a repair."""
    try:
        repairs = Bundle(bundle).manifest().provenance.get("repairs")
    except BenchproofError:
        return False
    return bool(repairs)


def _kept(backend: Backend) -> str:
    """What a repair is told of the copies `conformance.py` and `axioms.py` hold.

    Benchproofer does not carry an edit of the solution file into either, so the repair does,
    and the gates hold what it leaves to the solution file it leaves.
    """
    if backend.extension == ".py":
        return (
            "Benchproofer does not update either. `conformance.py` holds the implementation, "
            "verbatim where it runs as Python, and its gate fails one whose copy is not the "
            "implementation you leave; `axioms.py` quotes the declarations of the `axioms` "
            "region, and its gate fails one that lacks a declaration of the region you leave. "
            "Where you change the implementation or that region, change the copy or the "
            "quotation as well."
        )
    return (
        "Benchproofer does not update either. `conformance.py` holds a port of the "
        "implementation into Python, and `axioms.py` restates the `axioms` region in Python: "
        "where you change the implementation or that region, change the port or the "
        "restatement as well."
    )


def _lacking(names: Sequence[str]) -> str:
    """What a repair is told of the files beside the solution the bundle lacks; "" for none."""
    shown = [_SHOWN.get(name, f"`{name}`") for name in names]
    if not shown:
        return ""
    listed = shown[0] if len(shown) == 1 else f"{', '.join(shown[:-1])} or {shown[-1]}"
    which = (
        "it, as the section below says"
        if len(shown) == 1
        else "each, as the sections below say"
    )
    return f" The bundle has no {listed} yet: write {which}."


#: How a repair's request names a file of `AUTHORED` the bundle lacks.
_SHOWN: dict[str, str] = {
    "twins": "pre-fix implementation in `twins/`",
    "rivals": "property-based test suite in `rivals/`",
}


def _beside(bundle: Path) -> str:
    """What a repair's brief says of the author's files beside the solution, by those it has.

    A directory counts once it holds a file.
    """
    names = [
        f"`{name}`"
        for name in (DIFFERENTIAL_HARNESS, HARNESS, "correspondence.md", "rivals/", "twins/")
        if (bundle / name).is_file()
        or ((bundle / name).is_dir() and any((bundle / name).iterdir()))
    ]
    if not names:
        return ""
    listed = names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"
    verb = "is" if len(names) == 1 else "are"
    return f"{listed} {verb} beside it."


def _sites_block(task: Task, edited: Edited) -> str:
    """What the specification has to be a model of, for the prompts that decide it.

    The wording is `verified-swebench`'s, revised for one file rather than its two
    artifacts: `prompts/nagini/spec_guide.md` §0 directive 3 (a model of the fix, not a
    re-imagining), §3 (each changed function its own function) and §2 (type modeling),
    with directive 6's leakage rule, and `worker.md`'s "read the changed functions AND
    their callees". Its line-for-line skeleton requirement is not carried over.

    Silent for a task whose fix names nothing and writes no file that is not Python, which
    is every task whose fix is not a patch: there is no list to point into, and a
    paragraph about one would be noise. ``edited`` is what the fix defines or edits.
    """
    allowed = sites.sites(task, edited)
    written = sites.others(task)
    if not allowed and not written:
        return ""
    return prompts.render(
        "sites",
        listed=sites.listed(allowed),
        others=_others(
            written,
            "A behavior in one of them that the FAIL_TO_PASS tests or the PASS_TO_PASS tests "
            "the test patch adds or edits check is part of the fix: model it as the code there "
            "computes it.",
        ),
    )


def _others(paths: Sequence[str], then: str) -> str:
    """The files the golden patch writes that are not Python, then ``then``; "" for none."""
    if not paths:
        return ""
    return (
        "\nIt also writes these files, which are not Python:\n\n"
        + "\n".join(f"* `{path}`" for path in paths)
        + f"\n\n{then}\n"
    )


def _tests_section(task: Task, tests: Edited, *, cases: Edited) -> str:
    """The tests the benchmark judges the fix by, as a section of a prompt; or nothing.

    Shown to the drafter and to a repair, as `verified-swebench`'s author is shown them
    (`prompts/nagini/spec_guide.md`'s opening and directive 4): which function the model
    has to be about, and what its result has to state, are read off the tests and not off
    the patch alone. The leakage screen covers the test patch for the same reason the gold
    patch, so quoting a line of it fails the bundle. The test patch itself is left out, for
    a session that reads the tests whole. ``cases`` holds the tests the test patch edits
    only in their decorators (`material.patched_regression`).

    Silent for a task whose oracle runs nothing, which has no tests to point at.
    """
    block = material.tests_block(task, tests, diff=False, cases=cases)
    if not block:
        return ""
    return (
        "## The tests the benchmark judges the fix by\n\n"
        "A fix is correct when the benchmark's tests report the task resolved: every test "
        "below passes. These are what the specification has to be strong enough to "
        "demand. Reproducing a line of the test patch in the specification leaks the "
        "golden patch, as quoting the fix does.\n\n" + block
    )


def _left(target: Path, template: str) -> str:
    """The file a drafting session left at ``target``; "" where it left none or the template."""
    written = read_text(target) if target.is_file() else ""
    return "" if written.strip() in ("", template.strip()) else written


def _tests_state(
    patch: str, refused: str, *, staged: bool, golden: bool, repository: str
) -> str:
    """What a session is told of the tests and patches in its copy of the repository.

    ``patch`` is the test patch, ``refused`` why it did not apply, ``staged`` whether the
    oracle's test files are written into the copy, and ``golden`` whether the golden patch is
    a diff, which the working copy keeps at its root. The test patch is written beside the
    copy, whose directory is ``repository``.
    """
    said = []
    beside = f"`tests.patch`, beside `{repository}/`,"
    if staged:
        said.append("The files the benchmark's tests run with are written into it whole.")
    if patch and not refused:
        said.append(
            "The diff the benchmark applies to its tests is applied, so each test reads as "
            f"the benchmark runs it; {beside} is that diff."
        )
    elif patch:
        said.append(
            f"The diff the benchmark applies to its tests, {beside} does not apply to "
            "it, so read a test that diff adds or edits there."
        )
    if golden:
        said.append("`reference.patch` at its root is the golden patch, which is not applied.")
    return "".join(f"{sentence} " for sentence in said)


def _drafted_block(record: dict[str, Any]) -> str:
    """What the drafting session reported its specification leaves out, or "" for nothing.

    For the request drafting `correspondence.md`, whose `Not modeled` and `Outside the bridge`
    sections start from it (`_EXCLUSIONS`).
    """
    said = [
        (heading, text)
        for key, heading in _EXCLUSIONS
        if (text := str(record.get(key) or "").strip())
    ]
    if not said:
        return ""
    return (
        "## What the drafter reported leaving out\n\n"
        "The session that wrote the solution file reported, as below, what its specification "
        "leaves out. Start the two sections that say so from it: keep each item that holds, "
        "with its reason, correct one that does not, and add what it missed.\n\n"
        + "\n\n".join(f"### {heading}\n\n{text}" for heading, text in said)
        + "\n\n"
    )


def _unpacked(
    payload: dict[str, Any], fields: dict[str, object]
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """``payload`` with the fields its report wrote inside another field read out of it.

    A submit call that lost its structure carries the later fields in the text of an
    earlier one, as `<name>` sections: `... </summary> <callees">...</callees>`. Each
    field the payload lacks that opens such a section is taken out of the text, the text
    keeping what comes before it; an array field reads as JSON or one item a line.

    Returns:
        The payload, and the fields read out of another's text, in order.
    """
    found = dict(payload)
    missing = [name for name in fields if name not in found]
    if not missing:
        return found, ()
    opening = re.compile(r"<(?P<name>" + "|".join(map(re.escape, missing)) + r")\"?>")
    packed: list[str] = []
    for key, value in payload.items():
        if not isinstance(value, str) or not (sections := list(opening.finditer(value))):
            continue
        found[key] = _closed(value[: sections[0].start()], key)
        for index, section in enumerate(sections):
            name = section.group("name")
            end = sections[index + 1].start() if index + 1 < len(sections) else len(value)
            if name not in packed:
                found[name] = _typed(_closed(value[section.end() : end], name), fields[name])
                packed.append(name)
    return found, tuple(packed)


def _closed(text: str, name: str) -> str:
    """``text`` without the `</name>` that closes it, stripped."""
    return re.sub(rf"\s*</{re.escape(name)}>\s*$", "", text.strip()).strip()


def _typed(text: str, schema: object) -> object:
    """A field read out of another's text, as the type its schema gives it."""
    if not (isinstance(schema, dict) and schema.get("type") == "array"):
        return text
    with suppress(ValueError):
        listed = json.loads(text)
        if isinstance(listed, list):
            return listed
    return [line.strip(" -*") for line in text.splitlines() if line.strip(" -*")]


def _outside_block(correspondence: str) -> str:
    """What ``correspondence`` lists under `Outside the bridge`, for the conformance prompt.

    Nothing when it lists nothing there. What `conformance.py` does with the inputs an entry
    names is the protocol's to say (`conformance-rules.md`).
    """
    entries = entries_under(correspondence, OUTSIDE)
    if not entries:
        return ""
    return f"## What `correspondence.md` lists under `{OUTSIDE}`\n\n{entries}\n\n"


def _recorded(functions: Sequence[str]) -> str:
    """What the conformance prompt says of the inputs on record, or "" when there are none.

    They are kept under the names an earlier `conformance.py` reported its functions by, and
    handed to this one under those names, so one that names a function otherwise leaves
    them uncompared and the gate does not pass it.
    """
    if not functions:
        return ""
    names = ", ".join(f"`{name}`" for name in functions)
    return (
        f"\n\nBenchproofer has inputs on record for {names}, and hands them to this file "
        f"in `{REPLAY}` under exactly those names, the ones an earlier `conformance.py` "
        "reported. Compare each of these functions, and print its lines, under that name."
    )


def _compared_sites(task: Task, edited: Edited, fixed: dict[str, str]) -> str:
    """The same list, as the conformance prompt needs it: what `conformance.py` compares with.

    After `verified-swebench`'s `worker.md` on `conformance_check.py`, which "bridges any type
    simplifications from mapping.md ... and diffs the shadow against the patched repo function".
    There the binding is a file of its own; here it is the docstring of `conformance.py`.
    ``edited`` is what the fix defines or edits, and ``fixed`` the files it touches, after it,
    which also name the functions that read a module-level name the fix edits (`sites.readers`).
    """
    readers = sites.readers(task.reference.patch or "", fixed)
    found = sites.sites(task, edited)
    allowed = {
        path: tuple(sorted({*found.get(path, ()), *readers.get(path, ())}))
        for path in [*found, *(path for path in readers if path not in found)]
    }
    written = sites.others(task)
    if not allowed and not written:
        return ""
    return (
        "The fix defines or edits these, or a module-level name they read, and the "
        "specification models one or more of them, "
        "under whatever type abstraction it chose. Diff each shadow -- the `shadow_` "
        "function holding a modeled function's code, as the rules below describe -- against "
        "the patched repository function it models:\n\n"
        + sites.listed(allowed)
        + _others(
            written,
            "Code of one of them that the specification models is compared by running it "
            "the way the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds or "
            "edits run it.",
        ).rstrip()
    )


def _assumed(solution: str, comment: str) -> str:
    """What `conformance.py` must do about each callee the specification assumes.

    A `@ContractOnly` callee has a contract and no body, so the file the checker read has
    nothing there to run. A stub of the program's own in its place would compare the
    repository with code from the program, which agrees whatever the repository does, as a
    comparison with code of its own does (`ungrounded`). So the call has to reach the real
    function. A callee the file models has a body, which the copy runs, so the comparison
    checks that definition as well. One sentence saying so when the specification assumes
    nothing, or when the file's regions cannot be read, as a repair may be given one.
    """
    try:
        region = markers.parse(solution, comment, required=()).get("axioms")
    except BenchproofError:
        region = None
    found = declared(region.text if region else "", comment)
    assumptions = tuple(one for one in found if not one.modeled)
    if not assumptions:
        return "Nothing. The implementation reaches no callee the checker took on trust."
    named = ", ".join(f"`{callee}`" for callee in callees(assumptions))
    return (
        f"The specification assumes {named}, which the checker read as a contract with "
        "no body. Where the copy of the implementation calls one of those, "
        "`conformance.py` must call the **real** function out of the repository -- import "
        "it like any other. Writing a stub of your own there would compare the repository "
        "with code from this file, which agrees whatever the repository does."
    )


def _with(base: Formalization, journal: Journal, **updates: Any) -> Formalization:
    """Attach the journal to a formalization, plus whatever else was produced."""
    return replace(
        base, exchanges=tuple(journal.exchanges), notes=tuple(journal.notes), **updates
    )


def _prose(reply: str) -> str:
    """Take a reply that is prose rather than code, refusing an empty one."""
    text = reply.strip()
    if not text:
        raise BenchproofError("the reply is empty")
    return text + "\n"


def _tail(text: str, limit: int) -> str:
    """The last ``limit`` characters of a program's output, saying how much was dropped.

    The end rather than the start, because a program that died says why last.
    """
    text = text.strip()
    if len(text) <= limit:
        return text
    return f"[... {len(text) - limit} earlier characters, not shown ...]\n\n{text[-limit:]}"


def battery_plan(backend: Backend) -> tuple[tuple[RivalKind, int], ...]:
    """The property-based test suite to draft under this checker.

    A probe establishes something by having its assertions *discharged*, so under a
    checker whose accepting verdict is a search that found no counterexample there is
    nothing for one to be: the assertions are never reached. `spec.strength.battery` does
    not ask for the kind there either, and the two decisions are the same decision.
    """
    wanted = frozenset(gate_battery.balanced(backend))
    return tuple((kind, count) for kind, count in BATTERY_PLAN if kind in wanted)


#: The words a witness states its claim with (`core.witness`).
_WITNESS_HEADS = ("theorem", "lemma", "example")

#: What a `conformance.py` sent back after its run is asked for, when the program is what went
#: wrong rather than the comparison it reports.
_CORRECT = (
    "Write the whole program again, corrected. Keep the implementation it contains exactly "
    "as it is, and keep comparing it with the function the fix changes."
)
#: A `skipped` report whose reason is a failed import. A `conformance.py` that cannot import
#: what it compares has not found a function nothing here can call; it has a module path
#: or a name wrong, which is its own error to fix.
_IMPORT_FAILED = re.compile(
    r"ModuleNotFoundError|ImportError|No module named|cannot import|could not import|"
    r"unable to import|failed to import|import(?:ing)? failed",
    re.IGNORECASE,
)
#: The last line Python prints for an import that raised, or a `conformance.py` prints for one.
_RAISED_ON_IMPORT = re.compile(r"^\s*(?:ModuleNotFoundError|ImportError)\b", re.MULTILINE)
#: A field a prompt template names, `$name` or `${name}`.
_FIELD = re.compile(r"\$\{?(\w+)")


def _wants_witness(backend: Backend, kind: str) -> bool:
    """Whether a variant of this kind has to carry a refutation witness.

    Only the variants the checker is supposed to *refuse*: a reject case of the property-based
    test suite, and the pre-fix implementation, whose refusal is `spec.discriminates`'s whole
    question. A rival expected to verify needs no witness: an accepting verdict is about the
    specification whatever the proof script does, and there is nothing to attribute.
    """
    refused = kind == TWIN or RIVAL_EXPECTATION.get(kind) == "refute"
    return backend.witness_required and refused


def _twins_rules(allowed: Sequence[str]) -> str:
    """What a pre-fix implementation writing the regions ``allowed`` must be."""
    return prompts.render("twins-rules", regions=variant.rule(allowed)).rstrip()


def _witness_block(solution: str, backend: Backend, kind: str) -> str:
    """What a request drafting a variant of this kind is asked of its witness, or nothing."""
    rules = _witness_rules(solution, backend, kind)
    return _WITNESS + rules if rules else ""


def _witness_rules(solution: str, backend: Backend, kind: str) -> str:
    """What the refutation witness of a variant of this kind must be, or nothing."""
    if not _wants_witness(backend, kind):
        return ""
    return witness.rules(solution, backend, TWIN if kind == TWIN else "rival")


def _brief(kind: str, states: str, regression: str = "") -> str:
    """What a case of ``kind`` is for, with ``states``, a probe's claim, filled in.

    A probe takes its inputs from the FAIL_TO_PASS tests, or, given ``regression``, from the
    PASS_TO_PASS tests it shows, which follow the brief.
    """
    tests, excluded = _PROBED[bool(regression)]
    brief = (
        _BRIEF[kind]
        .replace("{states}", states)
        .replace("{tests}", tests)
        .replace("{excluded}", excluded)
    )
    if not regression:
        return brief
    return (
        f"{brief}\n\nThe PASS_TO_PASS tests to take the inputs from, each whole as it reads "
        f"after the test patch:\n\n{regression}"
    )


def _tried_block(bodies: Sequence[str]) -> str:
    """Tell the model which cases of this kind it has already written; "" for none.

    Each case's implementation regions are shown in their sentinels, as `_body` gives them,
    and the block ends in a blank line, as the request's sections do.
    """
    listed = "\n\n".join(material.fenced(body) for body in bodies if body.strip())
    if not listed:
        return ""
    return (
        "You have already written the case(s) below for this same specification. "
        f"Write a different one, aimed at a different obligation or input:\n\n{listed}\n\n"
    )


def _twin_block(twin: str) -> str:
    """Show a uniqueness case the pre-fix implementation the bundle ships, not to repeat."""
    if not twin.strip():
        return ""
    return (
        "The bundle already ships the implementation below as the one the fix replaced, "
        "and the specification already has to reject it. "
        f"{_DIFFERENT_MISTAKE.format(it='this one')}\n\n{material.fenced(twin)}\n\n"
    )


def _body(source: str, backend: Backend) -> str:
    """A variant's implementation regions, each in its sentinels; "" for an unreadable file."""
    try:
        regions = markers.parse(source, backend.comment, required=())
    except BenchproofError:
        return ""
    return "\n\n".join(
        markers.wrap(backend.comment, name, regions[name].text)
        for name in markers.named(regions, "impl")
    )

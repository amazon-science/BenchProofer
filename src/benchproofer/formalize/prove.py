# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Proofs written by an agent session, with the specification held fixed.

Under a prover a file is accepted when its proof goes through, and one request rarely
writes a proof that does: the tactic that closes a goal depends on the goal the checker
prints, which nobody sees before running it. The proof is also the one part of a file
whose correctness the checker decides alone, so it is the part a session can be left to
iterate on. It edits the proof, runs the checker, reads the goal it is stuck on, and edits
again, as `verified-swebench`'s proof agent does.

A session proves one of three things (`ProofKind`): the file's own claim, an admissibility
probe's claims beside the reference implementation, or a refutation witness, and its request
says which, and so what reporting `fail` means.

What the session hands back is kept only if the specification and the implementation are
the ones it was given. The proof annotations a backend names in `proof_annotations` are
compared out, since they sit inside the implementation: a Velvet loop's invariants in its
`do` block, a Nagini `Invariant` or `Assert` in the method body. A probe's claims are
compared out too, and each has to be stated again as it was. What is kept is also held to
the backend's banned tokens and put to the checker again, with the axiom screen of a
backend that has one. The session's own report says why it stopped, and nothing more.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..backends.base import Backend, CheckResult
from ..config import Settings
from ..core import markers, material, variant
from ..core.scripts import SCRATCH, lay_out, tools_rules
from ..core.task import Task
from ..errors import BenchproofError, ProviderError
from ..llm.agentic import EDIT, AgentSession, SessionSpec
from ..util.fsio import read_text, write_text
from . import prompts

__all__ = ["PROVE_FIELDS", "ProofKind", "Proved", "Prover"]

#: Longest checker output quoted in the request, in characters.
OUTPUT_LIMIT = 6_000

#: What the session reports when it stops.
PROVE_FIELDS: dict[str, Any] = {
    "status": {
        "type": "string",
        "enum": ["ok", "stuck", "fail"],
        "description": (
            "ok once the checker accepts the file; stuck when an obligation will not close; "
            "fail when the claim is false"
        ),
    },
    "goal": {
        "type": "string",
        "description": "when stuck, the goal the checker printed and the property it needs",
    },
    "notes": {"type": "string", "description": "the strategy used, and the key lemmas"},
}
#: The playbook each backend's request carries, by backend name.
_PLAYBOOK = {"lean4": "prove-lean", "velvet": "prove-velvet"}
#: How a proof is written under each backend, for the session's system prompt, by backend
#: name; another backend is told only which constructs are refused (`_method`).
_METHOD = {"lean4": "prove-tactics", "velvet": "prove-tactics", "nagini": "prove-nagini"}

#: What a proof session is asked to prove: the file's own claim, which the solution file
#: and a case expected to verify make; an admissibility probe's claims, stated beside the
#: reference implementation and its proof; or a refutation witness in the `proof` region,
#: that the file's implementation violates the specification at one input. Each has its
#: own account of what the file claims, and so of what `fail` reports (`prove-<kind>`).
ProofKind = Literal["claim", "probe", "witness"]


@dataclass(frozen=True, slots=True)
class Proved:
    """What one proof session left, and what became of it."""

    #: The file to keep: the session's when it was admissible and accepted, else the one
    #: it was given.
    source: str
    check: CheckResult
    #: Why the session's file was not kept, empty when it was.
    refused: str = ""
    #: The session's own record: its status, budget spent, and what it said.
    session: dict[str, Any] = field(default_factory=dict)

    @property
    def kept(self) -> bool:
        """Whether the session's file is the one returned."""
        return not self.refused


class Prover:
    """Run proof sessions for one backend, each in a workspace of its own."""

    def __init__(
        self, *, session: AgentSession, backend: Backend, settings: Settings, workdir: Path
    ) -> None:
        self.session = session
        self.backend = backend
        self.settings = settings
        self.workdir = Path(workdir)

    def prove(
        self,
        task: Task,
        source: str,
        check: CheckResult,
        *,
        label: str,
        kind: ProofKind = "claim",
    ) -> Proved:
        """Ask a session to prove ``source``, and keep what it wrote only if it may be kept.

        Args:
            task: The task the file is about, for the checker's bundle.
            source: The file the checker refused.
            check: What the checker said of it.
            label: A name for this session's workspace, unique within the run.
            kind: What the session is to prove. For a probe, the claims the backend's
                `probe_claims` open inside the implementation are the probe's, which the
                session may prove and may not restate (`inadmissible`).

        Raises:
            ProviderError: The session could not be started at all, so it is the provider
                that failed and not the proof.
        """
        workspace = self.workdir / "prove" / label
        copy = lay_out(workspace, task, self.backend.name, self.settings)
        target = copy.root / self.backend.solution_filename()
        write_text(target, source)
        file = target.relative_to(workspace).as_posix()
        statements = self.backend.probe_claims if kind == "probe" else ()
        playbook = _PLAYBOOK.get(self.backend.name)
        request = SessionSpec(
            system=prompts.render(
                "prove-agent-system",
                language=self.backend.language,
                method=_method(self.backend),
            ),
            prompt=prompts.render(
                "prove-agent",
                file=file,
                language=self.backend.language,
                diagnostics=material.clip(check.output or check.detail, OUTPUT_LIMIT)
                or "(no output)",
                kind=prompts.render(f"prove-{kind}", claims=_listed(statements)),
                editable=_editable(source, self.backend, statements),
                workspace=workspace.as_posix(),
                scratch=SCRATCH,
                tools="./tools",
                tools_rules=tools_rules(
                    self.settings,
                    task,
                    self.backend,
                    session_s=self.settings.prove_timeout_s,
                ),
                playbook=prompts.render(playbook) if playbook else "",
            ),
            cwd=workspace,
            submit="proof",
            fields=PROVE_FIELDS,
            required=("status",),
            tools=EDIT,
            writable=(target,),
            max_turns=self.settings.prove_turns,
            timeout_s=self.settings.prove_timeout_s,
        )
        try:
            outcome = self.session.run(request)
        except ProviderError:
            # A session that never started read nothing and wrote nothing, so there is no
            # proof it failed to find. Recorded as a refusal it would be charged to the
            # file and spend the round that asked for it; raised, it stops the run and
            # says the provider is what failed.
            raise
        except BenchproofError as exc:
            return Proved(
                source=source, check=check, refused=f"the session could not run ({exc})"
            )
        payload = outcome.payload or {}
        record: dict[str, Any] = {
            "status": str(payload.get("status") or "no report"),
            "goal": str(payload.get("goal") or ""),
            "notes": str(payload.get("notes") or ""),
            "turns": outcome.turns,
            "tool_uses": outcome.tool_uses,
            "duration_s": round(outcome.duration_s, 1),
        }
        written = read_text(target) if target.is_file() else ""
        if written == source:
            return Proved(
                source=source,
                check=check,
                refused="the session left the file as it was",
                session=record,
            )
        why = self.inadmissible(source, written, statements)
        if why:
            return Proved(source=source, check=check, refused=why, session=record)
        again = self.backend.check(
            written,
            workdir=workspace / "check",
            timeout_s=self.backend.budget(self.settings.verify_timeout_s),
        )
        if not again.verified:
            return Proved(
                source=source,
                check=check,
                refused=f"the checker still refuses it ({again.status}: {again.detail})",
                session=record,
            )
        closure = self.backend.closure(
            written,
            workdir=workspace / "closure",
            timeout_s=self.backend.budget(self.settings.verify_timeout_s),
        )
        if closure is not None and not closure.closed:
            return Proved(
                source=source,
                check=check,
                refused=f"the proof was not shown complete, with no sorry or extra axiom: "
                f"{closure.detail}",
                session=record,
            )
        return Proved(source=written, check=again, session=record)

    def inadmissible(self, before: str, after: str, statements: Sequence[str] = ()) -> str:
        """Why ``after`` may not replace ``before``, or "" when it may.

        It must carry the same specification and, proof annotations aside, the same
        implementation, and none of the backend's banned tokens.

        ``statements`` names the words that open a claim inside the implementation the
        session was allowed to reprove. Those are set aside from the implementation
        comparison, as the proof annotations are, and each claim ``before`` states with one
        is then required back word for word: a probe whose assertion the session rewrote
        asserts something the case was not offering as evidence. A claim the session added
        is a step of the proof, such as a Nagini `Assert` stating a fact the next one needs.
        """
        comment = self.backend.comment
        try:
            markers.parse(after, comment)
        except BenchproofError as exc:
            return f"its markers cannot be read ({exc})"
        if not self.backend.same_spec(before, after):
            return "it changes the specification"
        aside = (*self.backend.proof_annotations, *statements)
        if _implementation(before, self.backend, aside) != (
            _implementation(after, self.backend, aside)
        ):
            return "it changes the implementation"
        if statements and not set(_stated(before, self.backend, statements)) <= set(
            _stated(after, self.backend, statements)
        ):
            return "it changes what the implementation's own claims state"
        masked = markers.mask_comments(after, comment)
        banned = [token for token in self.backend.banned_tokens if token in masked]
        if banned:
            return "it uses " + ", ".join(f"`{token}`" for token in banned)
        return ""


def _method(backend: Backend) -> str:
    """How a proof is written under ``backend``, for the session's system prompt."""
    named = _METHOD.get(backend.name)
    if named:
        return prompts.render(named).strip()
    refused = _listed(backend.banned_tokens)
    return "Close every obligation with a real proof" + (
        f", and with none of {refused}, which discharge one without establishing it."
        if refused
        else "."
    )


def _editable(source: str, backend: Backend, statements: Sequence[str]) -> str:
    """What a proof session may write in ``source``, and what is fixed, in its request's words.

    The `proof` region where the file has one; the backend's proof annotations inside the
    implementation, which the session may add, change or remove; and the proof of each of a
    probe's ``statements``, whose claims stay as they are.
    """
    try:
        owned = variant.owned(source, backend)
    except BenchproofError:
        owned = ()
    proof = any(markers.kind(name) == "proof" for name in owned)
    lines: list[str] = []
    if proof:
        lines.append(
            "* The `proof` region: replace every unproved step in it with a real proof, and "
            "put a lemma the proof needs there, before the claim that uses it."
        )
    if backend.proof_annotations:
        mine = (
            ", apart from the probe's own claims below"
            if set(backend.proof_annotations) & set(statements)
            else ""
        )
        annotations = _listed(backend.proof_annotations, "and")
        lines.append(
            f"* The proof annotations inside `impl` -- {annotations} -- which you may add, "
            f"change or remove{mine}: they are the proof's, not the implementation's."
        )
    if statements:
        lines.append(
            f"* The proof of each claim the probe makes with {_listed(statements)} inside "
            "`impl`: what each of those claims states stays exactly as it is, and you may "
            "add claims of your own that help establish them."
        )
    regions = "`impl` and `proof`" if proof else "`impl`"
    lines.append(
        f"\nEverything else in the file is fixed: the specification -- every region but "
        f"{regions} -- and the code of the implementation in `impl`."
    )
    return "\n".join(lines)


def _listed(words: Sequence[str], last: str = "or") -> str:
    """Words as a list of code spans, the last joined with ``last``."""
    spans = [f"`{word.strip()}`" for word in words]
    return ", ".join(spans[:-1]) + f" {last} {spans[-1]}" if len(spans) > 1 else "".join(spans)


def _implementation(source: str, backend: Backend, aside: Sequence[str]) -> str:
    """The implementation regions' code, layout and the ``aside`` statements apart."""
    try:
        regions = markers.parse(source, backend.comment)
    except BenchproofError:
        return ""
    body = markers.joined(regions, "impl")
    return variant.fingerprint(variant.set_apart(body, aside)[0], backend)


def _stated(source: str, backend: Backend, openers: Sequence[str]) -> list[str]:
    """The claims the implementation regions state with one of ``openers``.

    Read one statement at a time (`variant.set_apart`), each up to where its proof starts
    (`markers.claims`), so that a claim with no proof of its own, such as a Nagini `Assert`,
    ends where its statement does.
    """
    try:
        regions = markers.parse(source, backend.comment)
    except BenchproofError:
        return []
    blocks = variant.set_apart(markers.joined(regions, "impl"), openers)[1]
    return [
        claim for block in blocks for claim in markers.claims(block, backend.comment, openers)
    ]

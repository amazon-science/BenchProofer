# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The account a passing role publishes when nothing was graded for it.

Three of the four audit roles a bundle records can reach a pass with no per-attack
outcome table behind it, and until this composed one they published a 70-character
counter, or a reviewer's essay, under a heading that says `pass` with nothing in the
record saying what KIND of verdict that is. Measured over `benchmark-verified` this
composer owns 3025 of the recorded notes -- 1392 G-PANEL-2, 1483 G-PANEL-3, 75 G-EQ,
75 G-PANEL-1 -- which is more than `audit_note` next door.

Two shapes, because two reasons for the gap, and `compose` dispatches on the gate key:
the key is what decides which sentences are true, and both sets are closed, so a role in
neither is declined rather than described in the other's terms.

`_compose_judgment` serves the two roles with no oracle at all, for which
`_derive_audit_verdict` keeps the reviewer's self-report and records the reviewer's prose
as the note. There is nothing to tabulate and nothing it would be honest to tabulate, so
what this composes is not a summary of the account but the frame the account is missing:
which question the role answers (JUDGMENT_QUESTION), in which vocabulary it is answered,
which MECHANICAL gates bear on the same artifact and what they recorded, and which of
the bundle's files the account cites and ships.

`_compose_ungraded` serves a MECHANIZED role whose round wrote no outcome table and
whose per-attack outcomes are English rather than a closed vocabulary. It restates the
machine sentence's own count and then NAMES the gap: a reader of the "Audit verdicts"
card cannot otherwise tell a role whose evidence ships in the bundle from one whose
evidence was never retained, and the second is a limitation of the released artifact
that the artifact should state. Fabricating a table out of prose bullets is the one
thing that would be worse than the counter.

What neither shape reads is the reviewer's argument -- not a count out of it, not a
finding, not a "no divergence was found". Every clause is the recorded verdict token, a
sibling gate's recorded status, the machine sentence's own number, or a `stat` for a
file the bundle ships, because a sentence lifted out of an essay is prose republished as
a measurement and being wrong about one in the reassuring direction is the whole failure
mode of a release surface. So it declines instead of guessing, and the declines are the
interesting half: an `agent_verdict` outside the role's vocabulary, a recorded count
that contradicts itself, a `LEAKAGE` pass with no accepted relaxation to rest on. Each
is a disagreement between what the reviewer said and what the cell records, which is a
finding about the cell.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

from . import audit_note

# Taken from `audit_note` rather than restated, here and in JUDGMENT_TAIL_BAN: the two
# modules compose into one field that one router reads, so a note either would reject
# must not be publishable by the other, and a second copy of a ban is a second thing to
# forget. See `audit_note.FORBIDDEN` for why that test is a case-insensitive SUBSTRING
# one.
BODY_BAND = audit_note.BODY_BAND

# The idempotence marker, emitted by both shapes and by no machine-generated note.
# Without one a second pass would compose FROM the composed note -- the count regex
# below still matches inside it -- and nest the paragraphs a level deeper every run, on
# a field the fleet reads back.
UNGRADED_MARKER = "**How far this record can be re-checked.**"
# The exact opening of the judgment text, and the seam a publisher splits the composed
# half off at, so it has to be an exact string and not a marker somewhere in the
# paragraph: a seam that landed one paragraph early would republish the reviewer's essay
# under a second heading. A note already carrying it is declined (measured: no
# un-composed note does).
JUDGMENT_LEAD = "**What was measured.** This role asks "

# `_compose_ungraded`'s input: 150 records, every one a `G-EQ`/`G-PANEL-1` pair from a
# round predating the composer that emits `Attack N -> outcome` lines. The count comes
# from the machine sentence, not from the payload, which on all 150 is the contentless
# `{model, recorded, recorded_as}`. Two shapes, both the harness's: `7 attacks re-run`
# (148 records) and `17 admissible attacks re-run of 17 submitted` (2). A note matching
# neither is DECLINED rather than described without a count -- an invented number is
# what this module exists to avoid.
UNGRADED_COUNT_RE = re.compile(
    r"(\d+)\s+(?:admissible\s+)?attacks?\s+re-run(?:\s+of\s+(\d+)\s+submitted)?")
# The clause that licenses the non-vacuity sentence, asserted only where the record
# asserts it; measured, all 150 do.
CONTROL_PHRASE = "positive control verifies"
# The disclosure a record of this class writes about ITSELF (102 of 150), and the
# pre-composer headings identifying a round whose account is a per-gate table plus each
# reviewer's essay quoted in full (42 of 150). Both are tested against the record text,
# so the sentence about where the evidence lives is never a guess about which round
# wrote it.
BODIES_ABSENT_MARK = "_The attack bodies behind this role's verdict"
LEGACY_HEAD_RE = re.compile(r"^#{2,3}\s+(?:Sub-review|Per-gate)\b", re.M)

# The one `audit_note` decline this fallback answers, and the two gates it answers it
# for. Named rather than "any decline" because the others are findings: an outcome
# outside `OUTCOME_GLOSS` on a PASSING role means the record's evidence and its status
# disagree, and a paragraph saying "none verified without resolving" would publish the
# status over the evidence. Those stay declined and reported.
UNGRADED_REASONS = frozenset({"no per-attack outcomes recorded"})
MECH_GATES = ("G-EQ", "G-PANEL-1")

# Each judged role's own vocabulary, which is not the mechanized roles' (`SOUND`/`WEAK`)
# and not the other judged role's. Measured: G-PANEL-2 records FAITHFUL on 1999 of 2000
# cells (the other records UNFAITHFUL and fails, so it never reaches here), G-PANEL-3
# NO-LEAKAGE on 1989 and LEAKAGE on 11 -- accepted, see RELAXED_VERDICT.
JUDGMENT_PASS_VERDICT = {
    "G-PANEL-2": frozenset({"FAITHFUL", "PASS", "SOUND"}),
    "G-PANEL-3": frozenset({"NO-LEAKAGE", "PASS", "SOUND"}),
}
# A leakage relaxation is recorded as status `pass` PLUS a note and never as a status of
# its own (`gates/panel.py`: "leakage relaxation is recorded as 'pass' + note, never a
# status"), because `record_audit` rejects `relaxed` here -- that is G-LEAK's
# disposition. So the pairing is a valid record whose meaning is the opposite of the
# ordinary one: a disclosure a reviewer ACCEPTED, not an absent one. Composing it as "no
# leakage found" would publish the status over the evidence, which is the one thing this
# module exists not to do.
RELAXED_VERDICT = {"G-PANEL-3": "LEAKAGE"}

# The router words a judged role's ADDED text may not carry: FORBIDDEN itself for one
# role, and for the other FORBIDDEN minus exactly its own vocabulary and nothing else,
# since `NO-LEAKAGE` contains `LEAKAGE` as a substring and the blunt ban would make it
# impossible to record that verdict in the words the harness records it in. Safe here
# and not for a mechanized role, for a reason in the router rather than in the words:
# `triage._ROLE_REMEDY` maps both gates to the faithfulness lane BY GATE KEY, so
# `defect_class` never reads their prose -- the vocabulary scan runs only for the legacy
# `G-PANEL` rollup, consulted only when one of the three per-role records is MISSING, in
# which case this note is not in the record either. The `BROKEN`/`WEAK` half stays
# absolute even so, because that is the half that routes a green cell to the expensive
# spec-repair lane.
JUDGMENT_TAIL_BAN = {
    "G-PANEL-2": audit_note.FORBIDDEN,
    "G-PANEL-3": re.compile(r"BROKEN|WEAK|UNFAITHFUL", re.IGNORECASE),
}

# The question each role answers, restated so a reader of the "Audit verdicts" card can
# tell the four roles apart. Both paraphrase the role names in `gates/panel.py:ROLES`
# and what `_derive_audit_verdict` documents them as judging; neither says anything
# about THIS cell. Membership here is also what makes a gate key a judged role at all.
JUDGMENT_QUESTION = {
    "G-PANEL-2":
        "whether the specification still describes the function it stands in "
        "for -- whether the abstract model diverges from that function on an "
        "input the function accepts, and whether the specification has been "
        "strengthened past it so that a correct implementation would be "
        "excluded",
    "G-PANEL-3":
        "whether the consumer-facing spec view discloses the reference edit -- "
        "whether a solver reading only the specification could reconstruct the "
        "fix instead of deriving it from the public problem statement",
}

# Mechanical gates that judge the SAME artifact these roles judge, so a reader has
# something re-runnable next to a verdict that is not. Quoted with the status the cell
# records and no gloss. A gate recorded as `skip` reached no verdict and is left out
# rather than described -- measured, G-AX is a skip on 265 cells and G-CONF on 57 -- so
# the sentence claims only what the cell records, never completeness.
JUDGMENT_SIBLINGS = {
    "G-PANEL-2": (("G-CONF", "the conformance battery over the modelled "
                             "function"),
                  ("G-AX", "the axiom battery")),
    "G-PANEL-3": (("G-LEAK", "the mechanical leakage screen over the same "
                             "spec view"),),
}

# Bundle files a judgment account is likely to cite, so the sentence naming them can be
# a `stat` rather than a guess, in the order the sentence lists them. The solution file
# is `model.py` on nagini and `Solution.lean` on the two Lean backends
# (`backend.language.solution_filename`); both are named here and resolved by what the
# bundle SHIPS, so this never has to know the backend.
CITABLE = ("model.py", "Solution.lean", "properties.py", "conformance_check.py",
           "axiom_check.py", "mapping.md", "refinement.md",
           "RELAXED_LEAKAGE.md")
# Past this the list stops being a starting point and becomes an inventory.
CITED_BUDGET = 4

# The band for the ADDED text, not for the whole note -- which is why it is not
# `BODY_BAND`. A judgment note opens with a reviewer's essay of a median 2092 and a
# maximum 10971 characters, so a bound on the total would decline exactly the longest
# records: the ones whose reader most needs to be told what kind of verdict it is.
# Shortening the essay is a different job; this never deletes a character.
JUDGMENT_TAIL_BAND = (400, 2400)


def already_composed(text: str) -> bool:
    """Whether this note already carries an account, from here or from next door.

    Both of this module's markers and both of `audit_note`'s, because the four
    compositions write one field: a note that already holds a table must not also be told
    it has no table, and checking `JUDGMENT_LEAD` too keeps the seam a publisher splits
    at unambiguous.
    """
    return (audit_note.already_composed(text)
            or UNGRADED_MARKER in text or JUDGMENT_LEAD in text)


def recorded_statuses(gates: Mapping[str, object]) -> dict[str, str]:
    """The sibling gates' recorded status tokens, and nothing else from them.

    Separated from the composer so the composer cannot reach anything else in an entry --
    not its note, not its counts. A gate with no recorded string status is absent from
    the result, which `_sibling_clause` reads as "reached no verdict here".
    """
    out: dict[str, str] = {}
    for gk, _gloss in sum(JUDGMENT_SIBLINGS.values(), ()):
        e = gates.get(gk)
        if isinstance(e, dict) and isinstance(e.get("status"), str):
            out[gk] = e["status"].strip()
    return out


def cited_files(note: str, shipped: Iterable[str]) -> list[str]:
    """Which of `CITABLE` the account names, of those the bundle ships.

    A file the account CITES but the bundle does not ship is not returned: 348 cells cite
    `RELAXED_LEAKAGE.md` without shipping it, and restating that citation in composed
    prose would entrench a dangling one under a fresh heading -- the citation itself is
    `leakage_note`'s business.
    """
    ships = set(shipped)
    return [n for n in CITABLE if n in note and n in ships]


def _sibling_clause(gate: str, siblings: Mapping[str, str]) -> str:
    """What the cell records for the mechanical gates over the same artifact.

    Only a gate that reached a verdict is named, with the status token verbatim. A `skip`
    is left out rather than glossed: it is not a measurement, and a sentence explaining
    why one is absent would be about the pipeline.
    """
    named = [f"{gk} `{siblings[gk]}` ({gloss})"
             for gk, gloss in JUDGMENT_SIBLINGS.get(gate, ())
             if siblings.get(gk) and siblings[gk].lower() != "skip"]
    if not named:
        return ""
    lead = ("The mechanical checks over the same artifact are"
            if len(named) != 1 else
            "The mechanical check over the same artifact is")
    return (f" {lead} recorded separately and re-runnable from the bundle: "
            + "; ".join(named) + ".")


def _cited_clause(gate: str, cited: Iterable[str]) -> str:
    """The bundle's own files the account names, as a "start here" list.

    A name the ROLE may not print is dropped rather than declined over:
    `RELAXED_LEAKAGE.md` contains the substring G-PANEL-2's ban keys on, and 2 cells ship
    it and cite it from a faithfulness account. Losing one entry costs a reader nothing
    re-checkable -- the other names are still there, and that file is the leakage role's
    business -- while declining costs those cells the whole block.
    """
    ban = JUDGMENT_TAIL_BAN[gate]
    names = [n for n in cited if not ban.search(n)][:CITED_BUDGET]
    if not names:
        return ""
    ships = "which ships" if len(names) == 1 else "all of which ship"
    return (" The account names " + ", ".join(f"`{n}`" for n in names)
            + f", {ships} in this bundle, so a reader can start there.")


def _compose_ungraded(note: str, record: str) -> tuple[str | None, str]:
    """A mechanized role whose round wrote no per-attack table."""
    if audit_note.PROBE_NOTE_RE.match(note.strip().partition("\n")[0].strip()):
        # Every sentence below is in the wrong-implementation vocabulary, which is false
        # of a probe-suite record: nothing verifies there and HOLDING is the good
        # outcome. Such a record whose outcome lines went missing has no honest account
        # available here, so it is declined rather than described in the other backend's
        # terms. Measured: no `ears` record needs this today; the guard is what keeps
        # the fallback from becoming the false framing `audit_note`'s whitelist
        # prevented.
        return None, "the machine sentence is the probe-suite shape"
    m = UNGRADED_COUNT_RE.search(note)
    if not m:
        return None, "no recorded attack count in the note"
    ran = int(m.group(1))
    submitted = int(m.group(2)) if m.group(2) else None
    if submitted is not None and submitted < ran:
        # Not arithmetic this may repair: both numbers come out of the same sentence, so
        # disagreement means the sentence is not the shape it looks like, and every
        # clause below reads it.
        return None, "recorded counts disagree (submitted < re-run)"

    plural = "s" if ran != 1 else ""
    measured = (f"**What was measured.** The audit submitted {submitted} "
                f"candidate wrong implementations against this specification and "
                f"re-ran the {ran} of them that changed only the implementation, "
                f"leaving the specification as this bundle ships it; the other "
                f"{submitted - ran} did not, so they do not test this "
                f"specification."
                if submitted is not None and submitted != ran else
                f"**What was measured.** The audit re-ran {ran} candidate wrong "
                f"implementation{plural} against this specification, each "
                f"changing the implementation and leaving the specification as "
                f"this bundle ships it.")
    measured += (" None of them verified without also resolving the instance, "
                 "which is what a counterexample to `verify => correct` would "
                 "require.")
    if CONTROL_PHRASE in note:
        measured += (" The positive control verifies, so the specification is "
                     "satisfiable by a correct implementation and that outcome "
                     "is not an artifact of a specification nothing can satisfy.")

    if LEGACY_HEAD_RE.search(record):
        where = (f"{UNGRADED_MARKER} The per-attack account is recorded in this "
                 f"cell's audit record in the format that audit round used: a "
                 f"per-gate verdict table and each reviewer's account quoted in "
                 f"full, rather than the graded per-attack table later rounds "
                 f"emit. It is not restated here because summarising it would "
                 f"mean re-grading prose, and the record itself is the better "
                 f"source.")
    else:
        where = (f"{UNGRADED_MARKER} The attack sources are not carried in this "
                 f"bundle. The count above and the positive-control outcome are "
                 f"what the harness recorded; the sources and their individual "
                 f"outcomes are not, so this role is the one part of the cell a "
                 f"reader cannot re-run from the bundle alone."
                 + (" The audit record states the same limitation."
                    if BODIES_ABSENT_MARK in record else ""))

    body = "\n\n".join([note.strip(), measured, where]).rstrip() + "\n"
    # `audit_note`'s three guards, applied to the WHOLE body: both ends of this shape
    # are composed here, so unlike the probe account next door there is no recorded
    # sentence to hold harmless.
    return audit_note._finish(body, body)


def _compose_judgment(gate: str, note: str, agent_verdict: str,
                      siblings: Mapping[str, str],
                      cited: Iterable[str]) -> tuple[str | None, str]:
    """A role with no oracle: the recorded verdict, its siblings, its citations."""
    verdict = (agent_verdict or "").strip().upper()
    allowed = JUDGMENT_PASS_VERDICT[gate]
    relaxed_word = RELAXED_VERDICT.get(gate)
    is_relaxed = bool(relaxed_word) and verdict == relaxed_word
    if not (verdict in allowed or is_relaxed):
        return None, f"agent verdict {verdict[:24]!r} not in this role's vocabulary"
    if not note.strip():
        return None, "no recorded note to compose from"

    leak = siblings.get("G-LEAK", "")
    measured = (f"{JUDGMENT_LEAD}{JUDGMENT_QUESTION[gate]}. "
                f"The reviewer recorded {verdict}.")
    if is_relaxed:
        # The pass and the verdict do not contradict each other, and saying so is the
        # point: the note records a disposition, not an absence. The disposition has to
        # be IN the record, though. All 11 of these cells record G-LEAK as `relaxed`; a
        # twelfth that did not would be a pass whose only stated ground is a leak
        # nothing accepted, and writing the sentence anyway would manufacture the
        # acceptance it rests on.
        if leak.lower() != "relaxed":
            return None, (f"agent recorded {verdict} but G-LEAK is "
                          f"{leak or 'unrecorded'!r}, not `relaxed`")
        measured += (
            " The record is a pass because the disclosure it names had already "
            "been accepted by a reviewer: an accepted relaxation is the leakage "
            "GATE's disposition to record, and this cell records G-LEAK as "
            "`relaxed`. This role defers to that disposition rather than "
            "re-failing the cell, and is recorded as a pass with a note because "
            "`relaxed` is not a status it may take. So the pass rests on an "
            "accepted disclosure and not on the absence of one.")
    else:
        measured += (
            " It is a judgment and not a machine re-run: unlike the two "
            "mechanized roles, nothing is submitted to the verifier for it and "
            "no candidate implementation is graded, so the recorded status is "
            "that judgment and the account above is the evidence for it rather "
            "than a summary of a measurement made elsewhere.")
        if gate == "G-PANEL-3" and leak.lower() == "relaxed":
            measured += (
                " This cell separately records G-LEAK as `relaxed`, which is a "
                "disclosure a reviewer accepted rather than the absence of one.")

    where = (f"{UNGRADED_MARKER} This role records no per-attack table because "
             f"nothing was re-run for it, so the account above is the whole of "
             f"its evidence and this is the part of the cell whose verdict is "
             f"prose by construction.")
    where += _sibling_clause(gate, siblings)
    where += _cited_clause(gate, cited)

    tail = f"{measured}\n\n{where}"
    if JUDGMENT_TAIL_BAN[gate].search(tail):
        # Unreachable for the text above and checked anyway: this is the field the
        # repair router reads back, and the one word that must never reach it from here
        # is the one that sends a green cell to the spec-repair lane.
        return None, "composed text carries router vocabulary"
    lo, hi = JUDGMENT_TAIL_BAND
    if not (lo <= len(tail) <= hi):
        return None, f"composed tail {len(tail)} outside {lo}..{hi}"
    body = f"{note.strip()}\n\n{tail}\n"
    if audit_note.LEADING_INCONCLUSIVE.match(body):
        return None, "composed note opens with INCONCLUSIVE"
    return body, ""


def compose(gate: str, note: str, *, agent_verdict: str = "",
            gates: Mapping[str, object] | None = None,
            shipped: Iterable[str] = (), record: str = "",
            ) -> tuple[str | None, str]:
    """The recorded note plus its frame, or (None, why-not).

    `gate` decides the shape, and BOTH sets are closed. A key in neither is declined
    rather than served by whichever shape is left: the fallback's sentences are about
    candidate wrong implementations, and its count regex would happily read `re-ran
    7 attacks` out of a reviewer's essay for a role that graded nothing. That
    fallback is licensed by `UNGRADED_REASONS` and nothing else, so a caller reaches
    it only after `audit_note.compose` has said the record holds no outcome table.

    `gates` is `meta.json`'s gate map, read for sibling STATUSES only; `shipped` is
    the bundle's file names, so a citation is a `stat` and not a guess; `record` is
    the audit record text, read by the fallback for the two properties that say
    where its evidence lives. All three are what the record already contains, which
    is the whole licence for what gets written.
    """
    if already_composed(note):
        return None, "already composed"
    if gate in JUDGMENT_QUESTION:
        return _compose_judgment(gate, note, agent_verdict,
                                 recorded_statuses(gates or {}),
                                 cited_files(note, shipped))
    if gate in MECH_GATES:
        return _compose_ungraded(note, record)
    return None, f"{gate} is not a role this composes for"

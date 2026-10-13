# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The account a passing mechanized audit role publishes about its own evidence.

`_derive_audit_verdict` re-runs the reviewer's attacks itself and records one
sentence about what happened:

    eq: 7 admissible attacks re-run of 7 submitted, none breaks the spec;
    positive control verifies

That is a faithful summary and a poor artifact. A reader of the "Audit verdicts"
card wants the four things it leaves out -- what a candidate attack IS, what
happened to each, what the positive control establishes, and whether the original
defect was among them -- and all four are already in hand at the moment the
sentence is written. So the sentence keeps its first line, byte for byte, and this
composes the account underneath it from the per-attack outcomes the runner just
recorded. Nothing here measures anything: every clause restates a recorded label.

Two vocabularies, because two arbiters. On a gated backend the entries are
candidate wrong implementations and a verifier judged each one, so a rejection is
the good outcome (`_compose_attacks`). On `ears` there is no verifier and the
entries are executable requirement probes judged by their own exit status, where
HOLDING is the good outcome (`_compose_probes`). `compose` dispatches on the
recorded labels rather than on the backend name, since the labels are what decide
which sentences are true.

Declines rather than guessing. An outcome label outside the whitelist, or a
recorded sentence that is not the shape parsed here, means the record's evidence
and its status disagree -- a finding about the cell, not a layout to smooth over.
"""
from __future__ import annotations

import re
from collections import Counter

# The marker that makes the composition idempotent: this header is emitted on
# every composed note and appears in no machine-generated one. `viz.render`
# enables MarkdownIt tables and allows the tags through its nh3 allowlist, so it
# renders as a table rather than as literal pipes.
TABLE_MARKER = "| re-run outcome | attacks | source |"
# Deliberately a second name: that header says "re-run outcome" about wrong
# implementations a verifier judged, and this one is probe scripts judged by their
# own exit status. Two names also keep the two classes countable in a corpus grep.
PROBE_TABLE_MARKER = "| probe outcome | probes | source |"

# Per-row cap on the attack-name list: 25 basenames in one table cell is the
# "too long" failure this is meant to be the other side of.
NAMES_BUDGET = 320
# Under the floor the note is still a counter; over the ceiling it is the other
# failure. One card renders all of these, so all of them share the band.
BODY_BAND = (300, 2500)

# Vocabulary the defect router keys on, as a SUBSTRING test because that is what
# the router does (`defect_class` upper-cases the note and asks `any(t in txt ...)`,
# so the ordinary word "weakness" contains "WEAK"). The check is as blunt as the
# thing it defends against, and the prose below avoids the whole family rather
# than relying on it.
FORBIDDEN = re.compile(r"BROKEN|WEAK|UNFAITHFUL|LEAKAGE", re.IGNORECASE)
LEADING_INCONCLUSIVE = re.compile(r"^\s*(?:[\w-]+:\s*)?INCONCLUSIVE\b")

# The closed set of per-attack labels this will describe, and the gloss for each.
# The labels a passing role can also carry -- `inconclusive`, and a candidate
# whose patch failed to apply so the oracle graded nothing -- are absent on
# purpose: each names a grading that did not happen, and meeting one here means
# the evidence contradicts the status.
#
# The glosses are written rather than quoted from the harness because the
# harness's own gloss for `correct echo` ends "not a weakness", which contains the
# substring the router keys on. See FORBIDDEN.
OUTCOME_GLOSS = {
    "rejected":
        "does not verify against this specification, so the specification "
        "excludes it",
    "correct echo":
        "verifies, and its patch resolves the instance, so it is a correct "
        "implementation and not a counterexample",
    "same-spec AND verifies — candidate":
        "verifies, and was referred to the correctness oracle; this role is "
        "recorded as passing only when no referred attack refutes the "
        "specification",
    "not a counterexample":
        "changed the specification rather than only the implementation, so it "
        "does not test the specification this bundle ships",
}

# One entry, and that is the measurement: on this backend the recorded label is
# what says the probe HELD, and the only other outcomes `_derive_ears_verdict`
# can write are a violation (the requirements mandate something the shipped patch
# does not do) and an inconclusive run -- each of which fails the gate.
PROBE_GLOSS = {
    "holds on the patched tree":
        "holds on the gold-patched tree, so the shipped patch exhibits the "
        "behavior that probe's cited requirement mandates",
}

# The sentence `_derive_ears_verdict` writes for a passing role. Its three numbers
# are the whole record of the candidate-patch search -- the ledger below it
# carries the probes and never the candidates -- so they are parsed rather than
# recomputed, and a sentence that does not match is declined.
PROBE_NOTE_RE = re.compile(
    r"^(?:[\w.-]+:\s+)?(\d+) requirement probes hold on the patched tree; "
    r"(\d+)/(\d+) weak-candidate\(s\) rejected by the probe suite; "
    r"positive control discriminates base vs patched\.?$")


def outcome_label(res: str) -> str:
    """The recorded outcome reduced to its label.

    The runner writes `<label> (<gloss>)` and sometimes appends `[<detail>]`:

        rejected (same spec, does not verify — good)
        correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

    The gloss and the detail are about this run of this attack; the label is the
    graded outcome, and the only part with a closed vocabulary.
    """
    lab = res.strip()
    for sep in (" (", " ["):
        cut = lab.find(sep)
        if cut > 0:
            lab = lab[:cut]
    return lab.strip()


def _by_label(pairs: list[tuple[str, str]]) -> dict[str, list[str]]:
    """The recorded names grouped by outcome, in the order they were re-run.

    The names are the most informative thing in the record after the outcome
    itself: an author calls the file after what it does (`atk_3_offbyone`,
    `probe_4_incompatible_units_raise`), so the list says which families the
    specification was actually tried against.
    """
    out: dict[str, list[str]] = {}
    for name, label in pairs:
        out.setdefault(label, []).append(name)
    return out


def _source_cell(names: list[str], names_ok: bool) -> str:
    """The table's `source` column for one outcome's entries.

    `names_ok` is false when a NAME would carry router vocabulary into the note
    (`atk13_weak_stub.lean`). A name is not something this may rewrite, so the
    column says where the names are instead of dropping the cell -- verdict.md is
    rendered by the card immediately below, so nothing becomes unreachable.
    """
    if not names_ok:
        return "listed per attack in the audit record below"
    shown: list[str] = []
    used = 0
    for name in names:
        if used + len(name) + 4 > NAMES_BUDGET and shown:
            shown.append(f"+{len(names) - len(shown)} more")
            break
        shown.append(f"`{name}`")
        used += len(name) + 4
    return ", ".join(shown)


def _finish(body: str, added: str) -> tuple[str | None, str]:
    """The three guards a composed note passes, or (None, why-not).

    `added` is the text whose router vocabulary is checked, and it is separate
    because on the probe path it is not the whole body: the recorded sentence
    kept verbatim there is the harness's own `K/M weak-candidate(s) rejected by
    the probe suite`, which matches FORBIDDEN before a word of the composition
    exists. What must never happen is this module ADDING the vocabulary; what the
    recorded sentence already publishes is `build_one`'s to change.
    """
    if FORBIDDEN.search(added):
        return None, "composed note carries router vocabulary"
    if LEADING_INCONCLUSIVE.match(body):
        return None, "composed note opens with INCONCLUSIVE"
    lo, hi = BODY_BAND
    if not (lo <= len(body) <= hi):
        return None, f"composed length {len(body)} outside {lo}..{hi}"
    return body, ""


def _table(marker: str, gloss: dict[str, str],
           pairs: list[tuple[str, str]]) -> list[str]:
    counts = Counter(label for _n, label in pairs)
    by_label = _by_label(pairs)
    names_ok = not FORBIDDEN.search(" ".join(n for n, _l in pairs))
    rows = [f"| {gloss[label]} | {k} | {_source_cell(by_label[label], names_ok)} |"
            for label, k in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    return [marker, "| --- | ---: | --- |", *rows]


def _compose_attacks(note: str, pairs: list[tuple[str, str]], control: str,
                     prepatch: bool | None) -> tuple[str | None, str]:
    """The gated backends' account: candidate wrong implementations, verifier."""
    unknown = sorted({label or "(no label)" for _n, label in pairs
                      if label not in OUTCOME_GLOSS})
    if unknown:
        return None, f"outcome not in the whitelist: {'; '.join(unknown)[:80]}"

    n = len(pairs)
    lines = [note.strip(), "",
             # Deliberately narrow. It does NOT claim every attack carries the
             # spec region unchanged -- the `not a counterexample` outcome exists
             # precisely because some do not, and a summary asserting otherwise
             # would be contradicted by its own table two lines later.
             f"**What was measured.** The harness re-ran {n} candidate wrong "
             f"implementation{'s' if n != 1 else ''} submitted against this "
             f"specification, recording for each whether it verifies and, where "
             f"it does, whether its patch resolves the instance. An attack that "
             f"verifies without resolving would be a counterexample to "
             f"`verify => correct`; the graded outcomes were:",
             "",
             *_table(TABLE_MARKER, OUTCOME_GLOSS, pairs)]

    tail = []
    if control:
        tail.append(f"The positive control `{control}` verifies, so the "
                    f"specification is satisfiable by a correct implementation "
                    f"and the outcomes above are not an artifact of a spec "
                    f"nothing can satisfy.")
    if prepatch is True:
        tail.append("The bug this instance fixes is re-encoded as one of the "
                    "attacks above, so the specification is checked to exclude "
                    "the original defect and not merely to admit the fix.")
    elif prepatch is False:
        tail.append("The bug this instance fixes is not among the attacks above; "
                    "that it is excluded is established by the prepatch twin "
                    "under G-VERIFY rather than here.")
    if tail:
        lines += ["", "**Non-vacuity.** " + " ".join(tail)]

    body = "\n".join(lines).rstrip() + "\n"
    return _finish(body, body)


def _compose_probes(note: str, pairs: list[tuple[str, str]], control: str,
                    prepatch: bool | None) -> tuple[str | None, str]:
    """The `ears` account: requirement probes, judged by their own exit status."""
    m = PROBE_NOTE_RE.match(note.strip().partition("\n")[0].strip())
    if not m:
        return None, "machine sentence is not the probe-suite shape"
    probes, rejected, candidates = (int(m.group(i)) for i in (1, 2, 3))
    if probes != len(pairs):
        return None, (f"sentence records {probes} probes, {len(pairs)} outcome "
                      f"lines were recorded")
    if not 1 <= rejected <= candidates:
        # The floor for a clean pass is >= 1 candidate exercised AND >= 1 rejected
        # by the suite: probes that merely hold prove conformance, not
        # discriminating power. A passing role recorded with neither is its
        # evidence contradicting its status.
        return None, (f"{rejected}/{candidates} candidates rejected is not a "
                      f"passing shape for this role")

    added = [
        f"**What was measured.** This backend has no verifier: the arbiter is a "
        f"suite of executable probes, each a standalone script that encodes a "
        f"behavior one cited requirement mandates and exits 0 only where the tree "
        f"it runs against exhibits it. The harness re-ran {probes} such "
        f"probe{'s' if probes != 1 else ''} against the gold-patched tree; a "
        f"probe that FAILED there would mean the requirements mandate something "
        f"the shipped patch does not do. The recorded outcomes were:",
        "",
        *_table(PROBE_TABLE_MARKER, PROBE_GLOSS, pairs)]

    # `weak` is the word the harness's own sentence uses for these and the one
    # word this may not repeat (see FORBIDDEN); "alternative candidate patch" is
    # the same thing named by what it is. The tally is phrased per shape rather
    # than as "K of M", which reads as a shortfall where K IS M.
    if rejected == candidates:
        tally = ("The suite rejected it" if candidates == 1
                 else f"The suite rejected all {candidates}")
    else:
        tally = f"The suite rejected {rejected} of the {candidates}"
    disc = (f"**Discriminating power.** Probes that hold show conformance, not "
            f"discriminating power, so the audit also submitted {candidates} "
            f"alternative candidate patch{'' if candidates == 1 else 'es'}, "
            f"claimed to satisfy every cited requirement, and ran the same suite "
            f"against {'it' if candidates == 1 else 'them'}. {tally}: a probe "
            f"encoding a cited requirement fails under "
            f"{'it' if rejected == 1 else 'each of those'}, so the requirements "
            f"as the probes read them exclude an implementation claimed to "
            f"satisfy them.")
    if rejected < candidates:
        # Said as what the record says -- not rejected -- and no more. What the
        # oracle returned for those is not written per candidate anywhere in the
        # bundle; the gate's rule below is what a reader can check the pass against.
        left = candidates - rejected
        disc += (f" The other {left} {'was' if left == 1 else 'were'} not "
                 f"rejected by the suite.")
    disc += (" A candidate that conformed to every probe and yet did not resolve "
             "the instance would have shown the requirements admit an "
             "implementation that does not fix it, which is the refutation this "
             "half searches for; this role is recorded as passing only where none "
             "does.")

    # The control here is a DISCRIMINATION witness, not a satisfiability one, so
    # it gets its own sentence and never the gated path's. `prepatch` is the same
    # base run on this backend (the control legs double as `prepatch_reproduced`),
    # so it is folded in rather than published as independent evidence.
    nv = ("**Non-vacuity.** The positive control "
          + (f"`{control}` " if control else "")
          + "holds on the gold-patched tree and fails at base, so the suite "
            "separates the two trees rather than holding on either.")
    if control and control in [n for n, _l in pairs]:
        nv += " It is one of the probes above, counted in the table there."
    if prepatch is True:
        # The literal recorded line is never reproduced: `_PREPATCH_RE` matches it
        # anchored at a line start, and a composed paragraph that reflowed onto
        # one would be read back as a second flag.
        nv += (" The prepatch flag above records the defect this instance fixes "
               "as re-encoded among these probes; on this backend that is the "
               "same run at base, not a further check.")

    text = "\n".join([*added, "", disc, "", nv])
    body = "\n".join([note.strip(), "", text]).rstrip() + "\n"
    return _finish(body, text)


def already_composed(text: str) -> bool:
    return TABLE_MARKER in text or PROBE_TABLE_MARKER in text


def compose(note: str, attacks: list[dict], *, control: str = "",
            prepatch: bool | None = None) -> tuple[str | None, str]:
    """The recorded sentence plus its account, or (None, why-not).

    `attacks` is `[{name, result}, ...]` as `_capture_attacks` builds it, with
    `result` the label `_derive_audit_verdict` wrote. A MIXED label set falls to
    the wrong-impl path, which reports the probe labels as outside its whitelist:
    one role has one arbiter, so a record drawing on both vocabularies is not a
    layout to compose by halves.
    """
    if already_composed(note):
        return None, "already composed"
    pairs = [(str(a.get("name") or ""), outcome_label(str(a.get("result") or "")))
             for a in attacks]
    if not pairs:
        return None, "no per-attack outcomes recorded"
    probes = all(label in PROBE_GLOSS for _n, label in pairs)
    fn = _compose_probes if probes else _compose_attacks
    return fn(note, pairs, control, prepatch)

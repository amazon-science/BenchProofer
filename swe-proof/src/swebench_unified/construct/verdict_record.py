# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Compose the per-cell `verdict.md` audit record, and merge it over the record
already on disk.

One section per audit role, never consolidated: each carries that role's
machine-derived status, the agent's advisory prose, and for a mechanized role the
attack sources that were re-run. The merge is here because a role that reached no
verdict has said nothing about the bundle, and rendering its empty section over
the previous one would destroy the only published copy of the evidence.
"""
from __future__ import annotations

import difflib
import json
import re

from .audit_roles import (
    _GATE_DERIVE_ROLE, _GATE_ROLE_LABEL, _ROLE_LABEL_ORDER, _ROLE_READS)
from .release_prose import (
    dedupe_trailing_notes, is_absent_evidence, publish_note, sanitize_code)


# fenced-code language for each backend's attack impls (best-effort highlight).
_ATTACK_LANG = {"nagini": "python", "lean": "lean", "velvet": "lean",
                "ears": "python"}  # ears attacks are python probe scripts

# The caption for a positive control that is byte-identical to the cell's spec
# file, which is the shape a control is SUPPOSED to have. Named at module level so
# every renderer of a control caption reads the same sentence.
CONTROL_IS_BASELINE = (
    "identical to the cell's spec file: the unmodified correct implementation,"
    " which is what a non-vacuity control has to be, so there is no diff to show")

# Why a block is a diff, said ONCE per role rather than once per block. It is a
# property of the whole battery -- every attack is the same spec file with a
# different implementation -- so repeating it under each attack restates one
# sentence once per block. The other captions `_attack_excerpt` returns are
# per-block FINDINGS about that one attack, so they stay where they are;
# `_render_attack_block` hoists this one and only this one.
DIFF_CAPTION = ("shown as a diff against the cell's spec file, which it"
                " is otherwise identical to -- that is what makes it a"
                " same-spec attack")

# The hoisted form: keyed off the fence language, so it stays true in a battery
# where only some blocks diffed (no baseline, or an attack equal to it).
DIFF_LEAD_IN = ("A `diff` block below is against that spec file, which the"
                " attack it belongs to is otherwise identical to.")

# Every word a role head's status slot may hold. `_render_sections` writes the
# recorded gate status there, or `—` for a role with no status recorded at all,
# and the tools that judge a PUBLISHED head against the stamp it renders read this
# set to tell a stale status from a reviewer's advisory verdict published in the
# same slot (`scripts/verdict_prose_lint.py`'s `role-heading-agent-status`,
# `scripts/audit_recheck.align_role`). Widening it narrows that finding, so it
# belongs to the composer rather than to either reader.
STATUSES = ("pass", "fail", "error", "skip", "relaxed", "vacuous",
            "unsatisfiable", "would-fail", "—")


def _attack_excerpt(src: str, baseline: str | None, lang: str,
                    role: str = "attack") -> tuple[list[str], str]:
    """One attack rendered as what it CHANGED, plus a caption for the block.

    Every attack is the cell's own spec file with a different implementation --
    that is what `same_spec` enforces and what the runner re-checks -- so pasting
    each one whole republishes the spec once per attack. It is the single reason
    these records are the size they are: a cell with twenty attacks carries twenty
    near-identical copies of one file, and the repeated `# axioms-start` /
    `# pure-end` markers a reader sees scrolling through one are the same model.py
    over and over.

    So publish the diff against the baseline instead. It is also easier to read
    than the thing it replaces, because the handful of lines that make the
    implementation wrong stop being buried in the several hundred that do not.

    Nothing here truncates, and that is deliberate rather than lazy. `meta.json`
    does NOT retain attack sources, so this file is the only record of them that
    ships. A diff against a baseline in the same bundle is lossless, because the
    baseline plus the diff is the attack; dropping the tail of either would
    destroy the sole copy of the evidence the cell's verdict rests on.
    Compression by de-duplication is safe, compression by elision is not.

    Falls back to the whole source when there is no baseline to diff against: a
    caller assembling sections by hand, or a bundle with no spec file to read.

    `role` decides what "identical to the baseline" MEANS, because the two blocks
    this renders are opposite claims. An ATTACK equal to the spec file changes
    nothing and so demonstrates nothing -- worth warning about. The POSITIVE
    CONTROL is supposed to be the unmodified correct implementation: that is the
    whole construction of a non-vacuity check, and equality with the baseline is
    the evidence it is one. Captioning both with the attack's warning publishes,
    under a PASSING gate, the sentence that the control "cannot demonstrate
    anything" -- a record undermining itself over a property it in fact
    establishes.
    """
    body = sanitize_code(src).rstrip()
    if not body:
        return [], ""
    if baseline:
        base = sanitize_code(baseline).rstrip()
        if base == body:
            return ([], CONTROL_IS_BASELINE if role == "control" else
                    "identical to the cell's spec file: this attack changes"
                    " nothing, so it cannot demonstrate anything")
        # Headers dropped BY POSITION, not by prefix: a deleted Lean comment
        # renders as `---- proof-start`, which a prefix filter eats as a file
        # header, and the diff then omits a deletion it was meant to record.
        raw = list(difflib.unified_diff(base.splitlines(), body.splitlines(),
                                        n=3, lineterm=""))
        cut = next((i for i, ln in enumerate(raw) if ln.startswith("@@")),
                   len(raw))
        diff = raw[cut:]
        if diff:
            return ["", "```diff", *diff, "```"], DIFF_CAPTION
    fence = f"```{lang}" if lang else "```"
    return ["", fence, *body.splitlines(), "```"], ""


def _render_attack_block(bk: str, attacks: list[dict],
                         positive_control: dict | None,
                         prepatch_reproduced,
                         baseline: str | None = None) -> list[str]:
    """The attacks/positive-control evidence for a mechanized role (G-EQ /
    G-PANEL-1). attacks = [{name, src, result}]; each is a same-spec wrong-impl
    the runner re-verified. Empty [] => this role's verdict was derived without
    the attack bodies being kept alongside it."""
    lang = _ATTACK_LANG.get(bk, "")
    out = []
    if not attacks:
        # Say what the reader can and cannot check, and nothing about the
        # pipeline: the count and the positive control are recorded, the
        # bodies behind them are not, so this role's verdict is not
        # independently re-checkable from the published bundle alone.
        out += ["", "_The attack bodies behind this role's verdict are not "
                "carried in this bundle. The count of attacks re-run and the "
                "positive-control outcome are recorded above; the sources "
                "themselves are not, so this role is the one part of the cell "
                "a reader cannot re-verify from the bundle alone._"]
        return out
    # "rejects them all" is not what this block shows and never was. An attack
    # the front end could not translate was never judged, and an `echo` -- a
    # same-spec implementation that is in fact CORRECT -- is supposed to verify
    # and is adjudicated by the resolve oracle instead. Claiming the spec rejected
    # every one of them contradicts the labels printed directly underneath.
    # Rendered before the lead-in is written, because the lead-in has to say
    # whether anything below it is a diff.
    body, diffed = [], False
    for i, a in enumerate(attacks, 1):
        res = (a.get("result") or "").strip()
        head = f"Attack {i} — `{a.get('name', f'attack_{i}')}`"
        if res:
            head += f" → {res}"
        block, caption = _attack_excerpt(a.get("src") or "", baseline, lang)
        if caption == DIFF_CAPTION:
            caption, diffed = "", True
        body += ["", head + (f" ({caption})" if caption else "")]
        body += block
    if positive_control:
        block, caption = _attack_excerpt(
            positive_control.get("src") or "", baseline, lang, role="control")
        if caption == DIFF_CAPTION:
            caption, diffed = "", True
        body += ["", "**Positive control** (a correct impl that MUST verify — "
                 f"non-vacuity): `{positive_control.get('name', 'control')}`"
                 + (f" ({caption})" if caption else "")]
        body += block
    out += ["", f"**Attacks re-run ({len(attacks)}):** each keeps the spec "
            "byte-for-byte and changes only the implementation; a TIGHT/SOUND "
            "spec rejects every one that reached the verifier."
            + (f" {DIFF_LEAD_IN}" if diffed else "")]
    out += body
    if prepatch_reproduced is not None:
        out += ["", f"Prepatch bug re-encoded as an attack: "
                f"`{bool(prepatch_reproduced)}`."]
    return out


def _published_field(v, *, structure: bool = True) -> str:
    """One recorded meta.json field, in the register a reader of the published
    corpus needs.

    Coerces a possibly-non-string field to trimmed text (some older bundles
    recorded a note as a dict / list), then drops scratch directories, absolute
    checkout paths, narration about the audit host and build-time tool names.
    Applied HERE, at the one place the record is composed, because a re-gate
    re-renders every role's prose from its fresh fields -- so scrubbing the
    rendered file would be undone by the next audit that runs.

    `structure=False` for a field rendered INLINE: `promote_structure` marks up
    an auditor's NOTE, where a line in capitals is a heading the auditor wrote,
    and it is wrong on a one-word field that ends up inside another line. See the
    `agent_verdict` call in `_render_sections`.
    """
    if v is None:
        return ""
    return publish_note(v if isinstance(v, str) else json.dumps(v),
                        structure=structure)


def _render_sections(backend_name: str, sections: list[dict],
                     baseline: str | None) -> list[str]:
    """Every role's published block, numbered in the order given: the heading,
    the recorded status bullet, the machine verdict, any counterexample
    transcript, the attacks a mechanized role re-ran, and the reviewer's own
    closing prose."""
    lines: list[str] = []
    for n, sec in enumerate(sections, 1):
        gate = sec.get("gate", "")
        label = _GATE_ROLE_LABEL.get(gate, gate)
        status = _published_field(sec.get("status")) or "—"
        # The agent's advisory verdict is a ONE-WORD LABEL and it is rendered
        # inside this section's `## Role n` heading, so the structuring pass has
        # to be off for it. `promote_structure` reads a whole line in capitals as
        # a heading the auditor wrote and prefixes `####`, which is right for a
        # note body and turns `SOUND` into `#### SOUND` -- a heading marker
        # nested inside a heading, published as `(agent: #### SOUND)`.
        #
        # The `####` is never recorded: it is inserted here, so the fix belongs
        # here and a re-render of an existing record picks it up.
        av = _published_field(sec.get("agent_verdict"), structure=False)
        head = f"## Role {n} — {label}: {status}"
        if av:
            head += f" (agent: {av})"
        lines += [head, ""]
        lines.append(f"- **status (recorded):** `{status}`")
        note = _published_field(sec.get("note"))
        if note:
            lines += _render_note(note)
        # A counterexample block is a TRANSCRIPT of what ran, so it gets the
        # reference-only pass: dropping a line from a transcript would
        # misrepresent the measurement it is evidence for.
        cx = sanitize_code(sec.get("counterexample")
                           if isinstance(sec.get("counterexample"), str)
                           else _published_field(sec.get("counterexample"))).strip()
        # `is_absent_evidence`, not just truthiness: an agent that recorded the
        # field as a Python value rather than as text leaves the literal word
        # `None` there, which renders as a code block whose entire content is
        # that word -- a caption promising a transcript over a fence holding a
        # placeholder. Such a block only ever appears in a role that PASSED,
        # where the role's own machine verdict already says no counterexample
        # was found.
        if cx and not is_absent_evidence(cx):
            lines += ["", "Counterexample / evidence:", "", "```", cx, "```"]
        if sec.get("mechanized"):
            lines += _render_attack_block(
                backend_name, sec.get("attacks") or [],
                sec.get("positive_control"), sec.get("prepatch_reproduced"),
                baseline)
        # A judgment role's `note` is the reviewing agent's own prose and the
        # payload carries the same prose under `notes`, so this closing paragraph
        # would republish the machine-verdict block a kilobyte further up.
        notes = dedupe_trailing_notes(note, _published_field(sec.get("notes")))
        if notes:
            lines += ["", notes]
        lines.append("")
    return lines


def compose_verdict_md(instance_id: str, backend_name: str,
                       sections: list[dict],
                       baseline: str | None = None) -> str:
    """Render the agentic-audit prose into a standalone, inspectable per-task
    verdict.md record. ONE section PER GATE ROLE (G-EQ, G-PANEL-1, G-PANEL-2,
    G-PANEL-3) — not consolidated — each with its machine-RE-DERIVED status/note,
    the agent's advisory verdict/notes, and (for the mechanized roles) the actual
    ATTACK source that was re-run. The recorded gate status in meta.json remains
    the source of truth for green; everything here is advisory evidence."""
    lines = [f"# P2 adversarial audit — {instance_id}",
             "",
             f"Backend: `{backend_name}`. One section per audit role below. "
             "Each role's status/note is the MACHINE-derived verdict (the runner "
             "re-runs the submitted attacks); the agent's own verdict and notes "
             "are advisory context, not the source of truth for green.",
             ""]
    lines += _render_sections(backend_name, sections, baseline)
    return "\n".join(lines).rstrip() + "\n"


def _render_note(note: str) -> list[str]:
    """A role's machine verdict, as Markdown that survives being rendered.

    The note was emitted as the tail of a list item -- `- **machine verdict:**
    <note>`. That is correct for the mechanized roles, whose note is one line,
    and wrong for the judgment roles, whose note is the reviewing agent's own
    prose, with its own numbered lists, inline code and paragraph breaks. A
    multi-line string pasted after a list marker leaves the list at the first
    newline, so from the second line on the enumeration is reparsed at top level
    -- its `1.` items start a new list, indented fragments become code blocks,
    and the reader of the published corpus sees the audit's reasoning as
    run-together fragments. Every faithfulness and leakage note is affected.

    So a single-line note stays in the list, where it reads as one more recorded
    field, and a multi-line note becomes its own labelled block, where its own
    structure is what Markdown sees. Neither branch alters a character of the
    note itself: this decides where it is placed, not what it says.
    """
    body = note.strip()
    if "\n" not in body:
        return [f"- **machine verdict:** {body}"]
    return ["", "**Machine verdict**", "", body]


def _role_label(sec: dict) -> str:
    g = str(sec.get("gate") or "")
    return _GATE_ROLE_LABEL.get(g, g)


def _section_inconclusive(sec: dict) -> bool:
    """Whether the DERIVATION judged this section inconclusive.

    Not a substring search for the word. For the judgment roles the recorded note
    IS the agent's own prose, and an agent that merely uses the word -- saying
    which mechanical gate was *not* inconclusive, for instance -- was read as
    having said nothing. That is not a cosmetic misread, because the retry loop
    overwrites the section unconditionally, so a real pass could be thrown away
    and replaced by whatever a re-run produced under the same load.

    The derivation records its own answer under `inconclusive`, so the production
    path reads no prose. The fallback is for a section assembled by hand (a
    caller of `merge_verdict_md`, a test): every derived INCONCLUSIVE is emitted
    by this module as `<role>: INCONCLUSIVE` with a fail status, and agent prose
    satisfies neither test. It has to default to retaining evidence rather than
    to discarding it, which is why an absent flag is not simply "conclusive".
    """
    if "inconclusive" in sec:
        return bool(sec["inconclusive"])
    if sec.get("status") != "fail":
        return False
    role = _GATE_DERIVE_ROLE.get(str(sec.get("gate") or ""),
                                 str(sec.get("agent_role") or ""))
    return str(sec.get("note") or "").lstrip().startswith(f"{role}: INCONCLUSIVE")


def _keeps_prior_verdict(bundle, sec: dict, prior: dict) -> bool:
    """Whether this inconclusive section must leave `prior`'s pass standing.

    A role that reached no verdict has said nothing about the bundle. Stamping
    its silence as `fail` over a pass that was DERIVED on the same bytes -- by
    re-running that role's attacks through the verifier and the resolve oracle --
    replaces a measurement with an outage, and the cell then cannot leave the
    worklist: the re-audit picks it up, the role fails to launch again, and the
    outage re-confirms itself -- while the `sources` digests still match the files
    on disk byte for byte.

    `verdict.md` already implements exactly this policy for the EVIDENCE
    (`merge_verdict_md` retains the prior block under a line naming the failed
    attempt); this is the same rule for the STAMP, which was the only place the
    two records disagreed.

    Narrow on purpose, and none of the three conditions is redundant:

      * the derivation must have judged the section INCONCLUSIVE -- a
        substantive `fail` is a finding and must overwrite anything;
      * the prior stamp must be a `pass`, so nothing is ever promoted here;
      * the prior stamp's `sources` must equal the CURRENT digests of the files
        this role reads. A pass about bytes that have since changed is stale and
        has to be re-earned; keeping it would be the one way this guard could
        vouch for a spec nobody audited.
    """
    if not _section_inconclusive(sec):
        return False
    if prior.get("status") != "pass":
        return False
    recorded = prior.get("sources")
    if not recorded:
        return False
    from ..gates.base import source_digests
    role = _GATE_DERIVE_ROLE.get(str(sec.get("gate") or ""),
                                 str(sec.get("agent_role") or ""))
    current = source_digests(bundle, _ROLE_READS.get(role, ()))
    return bool(current) and current == recorded


def _split_role_blocks(md: str) -> dict[str, str]:
    """`{gate label -> that role's rendered block}` for an existing verdict.md.

    Keyed on the label rather than the role number, because a run that reaches a
    different set of roles renumbers the sections.
    """
    out: dict[str, str] = {}
    for block in re.split(r"(?m)^(?=## Role )", md)[1:]:
        m = re.match(r"## Role \d+ — ([^:]+):", block)
        if m:
            out[m.group(1).strip()] = block.rstrip() + "\n"
    return out


def merge_verdict_md(instance_id: str, backend_name: str, sections: list[dict],
                     prior: str | None, stamp: str,
                     baseline: str | None = None) -> str:
    """Compose verdict.md WITHOUT trading retained evidence for a stub.

    A role that failed to launch has said nothing about the bundle, and rendering
    its empty section over the previous one destroys the attack bodies, positive
    controls and counterexamples an audit that DID run produced -- the evidence a
    reader needs in order to judge the cell at all, and the most expensive thing
    in the artifact. So a role whose fresh section is INCONCLUSIVE keeps its prior
    block, under a line saying the latest attempt did not run. meta.json still
    records the failed attempt -- as a status when the retained block is itself a
    fail or describes bytes that have since moved, and as
    `last_inconclusive_attempt` beside a still-valid pass (`_keeps_prior_verdict`)
    -- so the cell is never silently reported as audited.

    Per ROLE, not per file: a run where one role dies and three succeed keeps the
    three new blocks and the one old one.

    A role the run never ATTEMPTED is kept for the same reason, and this is a
    separate case from the one above. `sections` holds only the roles this run
    reached, so a scoped re-audit (`audit_refresh --only panel_2,panel_3`, which is
    how a repair agent re-earns the two roles its edit invalidated) produced a
    `fresh` file containing those two sections and nothing else -- and the eq and
    panel_1 blocks, with their attack bodies, would be dropped from the published
    record while meta.json went on holding both gates' full pass.

    Carried through verbatim and with no added prose. The block is the rendering
    of a record meta.json still holds, so publishing it says exactly what the
    record says; and whether that record is fresh for the spec on disk is decided
    by `check_stamp_freshness` and `audit_freshness.py`, both required release
    checks. Dropping the block does not make the record fresher -- it only hides
    it from the one reader who cannot run those checks.
    """
    fresh = compose_verdict_md(instance_id, backend_name, sections, baseline)
    if not prior:
        return fresh
    old = _split_role_blocks(prior)
    if not old:
        return fresh
    kept = 0
    for sec in sections:
        label = _role_label(sec)
        block = old.get(label)
        if not block or not _section_inconclusive(sec):
            continue
        # Only retain what is actually bigger than the stub replacing it, so a
        # failed attempt can never resurrect an older failed attempt's stub.
        if "INCONCLUSIVE" in block.split("\n\n", 2)[0] or len(block) < 400:
            continue
        sec["_retained"] = block
        kept += 1
    # Roles this run did not address at all, in the canonical order, so a scoped
    # run cannot reorder the file either.
    addressed = {_role_label(sec) for sec in sections}
    unaddressed = [(lbl, old[lbl]) for lbl in _ROLE_LABEL_ORDER
                   if lbl in old and lbl not in addressed]
    unaddressed += [(lbl, blk) for lbl, blk in old.items()
                    if lbl not in addressed and lbl not in _ROLE_LABEL_ORDER]
    if not kept and not unaddressed:
        return fresh
    out = _split_role_blocks(fresh)
    body = [fresh.split("\n## ", 1)[0].rstrip(), ""]
    # One ordered list of (label, retained-block-or-None) over BOTH sets, so the
    # numbering is consecutive across them however they interleave. Sorted by the
    # canonical role order and stable, so a label outside the canon keeps its
    # position relative to its own kind rather than being dropped.
    rank = {lbl: i for i, lbl in enumerate(_ROLE_LABEL_ORDER)}
    plan: list[tuple[str, str | None]] = [
        (_role_label(sec), sec.pop("_retained", None)) for sec in sections]
    plan += unaddressed
    plan.sort(key=lambda p: rank.get(p[0], len(rank)))
    unattempted = {lbl for lbl, _ in unaddressed}
    for n, (label, block) in enumerate(plan, 1):
        if block is None:
            # Renumbered too: `fresh` numbered its sections 1..len(sections), and
            # a scoped run interleaves them with blocks it did not render, so the
            # fresh numbering is only correct when nothing is spliced in.
            body += [re.sub(r"^## Role \d+", f"## Role {n}",
                            out.get(label, "").rstrip()), ""]
            continue
        # Renumber the retained heading so the sections still read 1..N.
        head, _, rest = block.partition("\n")
        head = re.sub(r"^## Role \d+", f"## Role {n}", head.rstrip())
        if label in unattempted:
            body += [head, rest.rstrip(), ""]
            continue
        body += [head,
                 "",
                 f"> The audit attempt at {stamp} did not reach a verdict for "
                 "this role (the role could not be launched; meta.json records "
                 "that attempt). Everything below is the evidence from the last "
                 "audit that DID reach one, retained deliberately.",
                 rest.rstrip(), ""]
    return "\n".join(body).rstrip() + "\n"

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""`parse_verdict` has to hand back the BYTES that are in the record.

It is the only reader of the attack sources, and two consumers act on what it
returns rather than merely displaying it:

  * `recheck_cell` RE-VERIFIES the attacks it returns, so a source that comes back
    altered is verified in place of the one that was recorded. A source that no
    longer parses is recorded as REJECTED, which makes the spec look STRONGER than
    it is -- the one direction this corpus must never drift in.
  * `check_stamp_freshness._retained_control` compares the returned control against
    the solution on disk to certify an audit record for free. An altered control
    fails that comparison on a cell where nothing moved.

So fidelity is the property under test, not formatting. The regression that
motivated these: the parser split with `str.splitlines()`, which breaks on U+2028,
U+2029, U+000B, U+000C, U+001C-1E and U+0085 as well as on newlines, and rebuilt
each block by joining on `\n`. A spec whose SUBJECT is line-break handling
contains those characters as literals, so its retained blocks came back with them
rewritten -- same length, zero difflib differences, not equal.
"""
from __future__ import annotations

from audit_recheck import parse_verdict

SPEC = """\
-- spec-start
theorem correct (c : Char) : isBreak c = true := by simp [isBreak]
-- spec-end
-- impl-start
def isBreak (c : Char) : Bool := c == '\\n'
-- impl-end
"""


def _record(*, attack: str, control: str, label: str = "rejected") -> str:
    """A verdict.md in the shape the composer emits and this parser reads."""
    return (
        "## Role 1 — G-EQ (spec-too-weak)\n"
        "\n"
        "The spec was attacked as follows.\n"
        "\n"
        f"Attack 1 — `atk_1.lean` → {label}\n"
        "\n"
        f"```lean\n{attack}```\n"
        "\n"
        "**Positive control** (a correct impl that MUST verify — non-vacuity): "
        "`atk_pos.lean`\n"
        "\n"
        f"```lean\n{control}```\n"
    )


# ---- attribution ----

def test_attack_and_control_land_in_their_own_slots():
    md = _record(attack=SPEC.replace("'\\n'", "'x'"), control=SPEC)
    sec = parse_verdict(md)["G-EQ"]
    assert [n for n, _s, _o in sec["attacks"]] == ["atk_1.lean"]
    assert sec["control"][0] == "atk_pos.lean"


def test_the_retained_label_is_carried_through():
    """`classify_old` reads this string to decide whether an attack still needs an
    oracle, so losing it would silently drop the attack from re-checking."""
    md = _record(attack=SPEC, control=SPEC, label="verifies but does not resolve")
    _n, _s, old = parse_verdict(md)["G-EQ"]["attacks"][0]
    assert old == "verifies but does not resolve"


def test_prose_outside_a_block_is_not_mistaken_for_a_source():
    """Only a block a caption opened is entered, so the roles' argument prose
    cannot arrive as an attack body."""
    md = _record(attack=SPEC, control=SPEC)
    assert "The spec was attacked" not in parse_verdict(md)["G-EQ"]["attacks"][0][1]


# ---- fidelity: what comes back must be what went in ----

def test_an_ordinary_source_round_trips_exactly():
    attack = SPEC.replace("'\\n'", "'x'")
    got = parse_verdict(_record(attack=attack, control=SPEC))["G-EQ"]
    assert got["attacks"][0][1] == attack.rstrip("\n")
    assert got["control"][1] == SPEC.rstrip("\n")


def test_a_source_containing_a_unicode_line_separator_round_trips():
    r"""The regression. U+2028/U+2029 are `splitlines()` boundaries but not `\n`,
    so a spec about line breaks came back with its literals rewritten."""
    attack = SPEC.replace("c == '\\n'",
                          "c == ' ' || c == ' '")
    got = parse_verdict(_record(attack=attack, control=attack))["G-EQ"]
    assert got["attacks"][0][1] == attack.rstrip("\n")
    assert got["control"][1] == attack.rstrip("\n")
    # and the characters are still literals, not newlines
    assert " " in got["control"][1] and " " in got["control"][1]


def test_every_splitlines_only_break_round_trips():
    r"""One per character `splitlines()` breaks on and `split("\n")` does not, so a
    future change back to `splitlines()` cannot pass by handling only U+2028."""
    for ch in ("\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", " ", " "):
        attack = SPEC.replace("'\\n'", f"'{ch}'")
        got = parse_verdict(_record(attack=attack, control=SPEC))["G-EQ"]
        assert got["attacks"][0][1] == attack.rstrip("\n"), f"U+{ord(ch):04X}"
        assert ch in got["attacks"][0][1], f"U+{ord(ch):04X} became a newline"


def test_a_blank_line_inside_a_source_is_preserved():
    """A dropped blank line changes nothing semantically and everything about the
    byte comparison the freshness check makes against the file on disk."""
    attack = SPEC.replace("-- impl-start", "\n-- impl-start")
    got = parse_verdict(_record(attack=attack, control=SPEC))["G-EQ"]
    assert got["attacks"][0][1] == attack.rstrip("\n")


# ---- the other recorded field ----

def test_prepatch_flag_is_read_as_a_bool():
    md = _record(attack=SPEC, control=SPEC).replace(
        "**Positive control**",
        "Prepatch bug re-encoded as an attack: `True`\n\n**Positive control**")
    assert parse_verdict(md)["G-EQ"]["prepatch_reproduced"] is True


def test_a_record_with_no_role_heading_yields_nothing():
    """Rather than attributing blocks to whichever gate happened to be last."""
    assert parse_verdict("```lean\nwhatever\n```\n") == {}


# ---- a role that points at another role's battery ----
#
# One `eq` agent scores both G-EQ and G-PANEL-1 (`build_one._AUDIT_AGENTS`), so a
# record would otherwise publish one battery twice. It drops the second copy and
# leaves a sentence naming the role it stands for. That sentence is
# part of the grammar, not decoration: without resolving it this parser would hand
# `_verdict_of` zero attacks for the de-duplicated gate and report "only 0 attacks
# (need >= 5)" on every one of those records. It resolves by POSITION and only
# after the names line up, because the whole warrant for dropping the bodies was
# that they were byte-identical in order.

_XREF = ("_The {n} attack bodies behind this role are not republished in this"
         " section: each is byte-identical to the block published under `{gate}`"
         " (Role 1 above, spec-too-weak), and each was compared byte for byte"
         " before it was dropped._")


def _pair(*, names=("atk_1.lean", "atk_2.lean"), xref_names=None,
          claimed=None, gate="G-EQ") -> str:
    """G-EQ publishing two bodies, then G-PANEL-1 pointing at them."""
    xref_names = names if xref_names is None else xref_names
    out = ["## Role 1 — G-EQ (spec-too-weak)", ""]
    for i, n in enumerate(names, 1):
        body = SPEC.replace("'\\n'", f"'{i}'")
        out += [f"Attack {i} — `{n}` → rejected", "", f"```lean\n{body}```", ""]
    out += ["**Positive control** (a correct impl that MUST verify — "
            "non-vacuity): `atk_pos.lean`", "", f"```lean\n{SPEC}```", "",
            "## Role 2 — G-PANEL-1 (spec-too-weak)", "",
            _XREF.format(n=claimed if claimed is not None else len(xref_names),
                         gate=gate), ""]
    for i, n in enumerate(xref_names, 1):
        out += [f"Attack {i} — `{n}` → rejected", ""]
    out += ["**Positive control** (a correct impl that MUST verify — "
            "non-vacuity): `atk_pos.lean`", "", f"```lean\n{SPEC}```", ""]
    return "\n".join(out)


def test_a_cross_referencing_role_returns_the_sources_it_points_at():
    got = parse_verdict(_pair())
    assert [(n, s) for n, s, _o in got["G-PANEL-1"]["attacks"]] \
        == [(n, s) for n, s, _o in got["G-EQ"]["attacks"]]
    assert len(got["G-PANEL-1"]["attacks"]) == 2


def test_a_cross_referencing_role_keeps_its_own_control_and_labels():
    """It inherits sources, not judgments: records do label the same attack
    differently under the two gates."""
    md = _pair().replace("Attack 2 — `atk_2.lean` → rejected\n\n**Positive",
                         "Attack 2 — `atk_2.lean` → correct echo\n\n**Positive")
    got = parse_verdict(md)
    assert [o for _n, _s, o in got["G-EQ"]["attacks"]] == ["rejected", "rejected"]
    assert [o for _n, _s, o in got["G-PANEL-1"]["attacks"]] \
        == ["rejected", "correct echo"]
    assert got["G-PANEL-1"]["control"][0] == "atk_pos.lean"


def test_a_cross_reference_whose_names_disagree_resolves_to_nothing():
    """Pairing by position under a name that does not match would re-verify one
    attack file's bytes as another's, and a rejection recorded against the wrong
    name is worse than no record."""
    md = _pair(xref_names=("atk_1.lean", "atk_9.lean"))
    assert parse_verdict(md)["G-PANEL-1"]["attacks"] == []


def test_a_cross_reference_claiming_the_wrong_count_resolves_to_nothing():
    """The count is the sentence's own check on itself; if the section has been
    edited since, the claim is stale and nothing is inherited."""
    assert parse_verdict(_pair(claimed=3))["G-PANEL-1"]["attacks"] == []


def test_a_cross_reference_to_an_absent_role_resolves_to_nothing():
    assert parse_verdict(_pair(gate="G-MUT"))["G-PANEL-1"]["attacks"] == []


def test_a_role_that_publishes_a_body_of_its_own_ignores_the_sentence():
    """Retained bytes always win. A stale sentence left in a section that has since
    published something cannot displace what is literally there, and the parser
    returns the one body rather than silently mixing the two sources -- which is
    the safe direction: `_verdict_of` then reports the attack floor unmet and the
    record is re-audited instead of cleared on inherited evidence."""
    md = _pair().replace(
        "Attack 2 — `atk_2.lean` → rejected\n\n**Positive",
        "Attack 2 — `atk_2.lean` → rejected\n\n```lean\nOWN BODY\n```\n\n**Positive")
    got = parse_verdict(md)
    assert [s for _n, s, _o in got["G-PANEL-1"]["attacks"]] == ["OWN BODY"]


def test_a_cross_reference_to_a_bodyless_attack_resolves_to_nothing():
    """A source role that names an attack but retains no block for it cannot lend
    it. Inheriting the rest would return fewer attacks than the sentence claims,
    which reads as a short battery rather than as an unresolvable reference."""
    body = SPEC.replace("'\\n'", "'2'")               # what `_pair` gives atk_2
    md = _pair().replace(f"```lean\n{body}```\n\n**Positive", "**Positive")
    assert body not in md
    got = parse_verdict(md)
    assert len(got["G-EQ"]["attacks"]) == 1        # atk_2's block is gone
    assert got["G-PANEL-1"]["attacks"] == []

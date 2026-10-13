"""properties.py — G-PBT falsification battery for django__django-12308 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct displayJson`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  displayJson (v : ValueView) return (out : String)
    ensures out = jsonDisplay v

The method renders a JSON-typed field's stored value for read-only display. The
value is abstracted to its three observable facts — ``present`` (does the value
count as present), ``prep`` (the outcome of preparing it as JSON text: either
``json text`` on success or ``unserializable`` on failure), and ``generic`` (the
generic textual rendering, which itself renders an absent value as the empty
marker). The sole ensures pins the whole outcome as a total function of those
three facts:

  jsonDisplay v
    = if v.present then
        (match v.prep with json text => text | unserializable => v.generic)
      else v.generic

This is a THREE-WAY CHOICE, and the ensures pins all three independent arms:

  * (J) present ∧ prep = json text  -> out = text
        the DISCRIMINATING arm: a present, serializable value must be shown as
        its JSON text, NOT via the generic rendering. This is the behaviour the
        change introduces.
  * (F) present ∧ prep = unserializable -> out = generic
        the fallback arm: a present value with no JSON form passes through the
        generic rendering UNCHANGED (identity — no extra wrapping).
  * (A) ¬present -> out = generic
        an absent value uses the generic rendering (which is the empty marker).

The three INPUT binders of ``jsonDisplay`` are all free (no ``require``) and the
post-image must hold for EVERY value of each:
  * ``present`` — the presence flag; selects arm (A) vs the (J)/(F) split.
  * ``prep``    — the JSON-preparation outcome; selects (J) vs (F).
  * ``generic`` — the fallback text; the surfaced value on arms (F) and (A).

ADVERSARIAL READ of the classes (mirrors the nagini sibling; the sibling models
the STRUCTURAL recursive serialiser deeply — brackets, ", " separators, per-token
double-quote delimiters — whereas this backend R-collapses the serialiser into
the OPAQUE ``PrepResult.json text`` field, validated == the real JSON preparer
by axiom_check.py. What this backend models is the CHOICE among the three
prepared outcomes. The sibling's structural rivals therefore do not survive as
distinct rivals here — the distinction they attack lives inside the opaque
``text`` — but the observable the F2P actually asserts (a serializable value must
render as its JSON text, not its generic repr) IS pinned by arm (J) and attacked
by the always-generic rival; see the footer for the case-by-case accounting):

  * STRUCTURAL-SERIALISER rivals (drop-separator, wrong-delimiter, no-brackets) —
    PARTIALLY R-COLLAPSED. The sibling attacks the internal shape of the
    serialised text (whether ", " separates siblings, whether the per-token
    delimiter is the interchange double-quote or the host single-quote, whether
    the array brackets are present). This backend does not COMPUTE that internal
    shape: ``text`` arrives as a field of the value view, validated == the real
    JSON preparer's output by the axiom lane (G-AX). So no rival here can
    mis-BUILD the text, and the sub-token distinctions (which separator, which
    per-token delimiter) genuinely have no counterpart.
    But ``text`` is a transparent ``String`` the impl must PASS THROUGH, and the
    ensures pins ``out`` to that exact string, so a rival CAN mangle it on the way
    out — and such a rival is refutable at a literal ``text`` by the ordinary
    tester witness. That is the expressible residue of this class, and it is
    carried by two rivals: ``weak-mangle-json-payload`` (re-wrap the prepared text
    in an extra delimiter pair) and ``weak-truncate-json-payload`` (drop its
    outermost characters — the carrier's counterpart of the sibling's
    "outer structural characters dropped" rival). Without them the battery would
    only ever have shown that the spec pins WHICH ARM is taken, never that it pins
    the surfaced text; every decision-level rival ignores ``text`` entirely.
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rival keeps the gold body then writes back into a read-only
    sequence input carrying only a fractional heap permission and is rejected for
    INSUFFICIENT PERMISSION. Lean and Velvet are referentially transparent: every
    parameter is an immutable value, this method declares no ``mut`` binder, there
    is no heap and no aliasing. No read-only input to overwrite and no permission
    system to trip, so the class is vacuous. No substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION: INAPPLICABLE as a shipped reject case, but NOT
    vacuous, and two claims in the earlier version of this bullet are withdrawn.
    True part: the frozen impl is STRAIGHT-LINE (no loop), so there is no loop in
    the frozen body to make spin and this bundle ships no divergence rival. False
    part: "a diverging rival cannot even be written" (a rival rewrites the whole
    impl region and may splice a loop), and "there is no ``method``-level
    termination obligation exposed to the spec" (there is one, and it is what does
    the work). This bundle sets ``loom.semantics.termination "total"``, so a
    postcondition is claimed of ALL runs, not only terminating ones, and the
    verifier demands a decreasing measure on every loop AND discharges its
    descent; the setting cannot drift from ``open TotalCorrectness DemonicChoice``
    because the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` with body
    ``z := z + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. (The sibling carries no
    diverge rival either.)
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is ``jsonDisplay v``, a concrete
    ``def`` in the ``pure`` region computing the outcome from the method's own
    argument (the ``axioms`` region is empty; the opaque field ``prep`` is one of
    ``v``'s own observable facts, not an answer key the impl could echo). The
    unique satisfier IS the grounded three-way choice, so the honest positives are
    the cheapest faithful reshapes (the ``pos-*`` cases).
  * CHOICE / PARTIAL-DOMAIN — heavily exercised. A rival can be correct on part of
    the value domain yet diverge on a sub-domain: the always-generic rival is
    correct wherever the generic rendering coincides with the JSON text (and on
    every non-serializable / absent value) but wrong on the discriminating (J)
    arm; the ignore-present rival is correct on every present value but wrong on
    an absent one; the wrap-fallback rival is correct on (J) and (A) but wrong on
    the (F) fallback identity.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop): its
extracted program reduces fully under ``decide``. Each reject rival carries a
machine-checked refutation ``witness`` — a Velvet tester statement
``displayJsonTester <v> = false`` at ONE concrete ``ValueView`` (literal
``present`` / ``prep`` / ``generic`` — no opaque terms, so no conditioning and no
binder-consistency obligation), checked in a file whose ``prove_correct`` block
has been stripped so no tactic script can mask the verdict. ``ValueView`` /
``PrepResult`` / ``String`` are all decidable, so the tester derivation needs no
extra instance (no ``deriving instance``, no ``axiom`` / ``sorry`` /
``native_decide``). Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival and FAILS
(``decide`` proves the proposition false) against the frozen solution, so each
rejection is a genuine spec refutation and not mechanical tactic breakage.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``; ``prep`` and
``generic`` are deep-model references (A-reference) validated == the real callees
by ``axiom_check.py`` (G-AX), never consumed by the proof, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12308"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block (and, for reshapes/admissibility, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    let out : String :=\n"
    "      if v.present then\n"
    "        match v.prep with\n"
    "        | PrepResult.json text => text\n"
    "        | PrepResult.unserializable => v.generic\n"
    "      else v.generic\n"
    "    return out\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct displayJson by\n  loom_solve\n  simp [jsonDisplay]"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `displayJsonTester <v> = false` says the extracted program's result
# ---- violates the postcondition at that concrete input. Checked in a file
# ---- whose `prove_correct` block is stripped. `ValueView` / `PrepResult` /
# ---- `String` are decidable already, so no extra instance is derived.
_TESTER = (
    "extract_program_for displayJson\n"
    "prove_precondition_decidable_for displayJson\n"
    "prove_postcondition_decidable_for displayJson\n"
    "derive_tester_for displayJson\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each computes the SAME three-way choice and only
    # reshapes the executable surface; the reproof stays a `loom_solve` plus a
    # small case split away from the frozen script.
    # =====================================================================
    {
        "id": "pos-match-prep-first",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: dispatch on `prep` FIRST, folding the presence test into the
        # json arm (present-and-json => text, else generic). Same outcome on
        # every input: the json arm surfaces `text` exactly when present, the
        # unserializable arm and the not-present case both surface `generic`.
        # Proof retuned (the do-block changed shape) via a case split.
        "module": _impl_reproved(
            "    let out : String :=\n"
            "      match v.prep with\n"
            "      | PrepResult.json text => if v.present then text else v.generic\n"
            "      | PrepResult.unserializable => v.generic\n"
            "    return out",
            "prove_correct displayJson by\n"
            "  loom_solve\n"
            "  simp [jsonDisplay]\n"
            "  cases v.prep <;> cases v.present <;> rfl"),
        "rationale": "dispatching on `prep` first and folding the presence test "
                     "into the json arm computes the SAME value on every input "
                     "(present-and-json surfaces `text`; the unserializable arm "
                     "and the not-present case both surface `generic`), so "
                     "`out = jsonDisplay v` still holds; a correct reshape must "
                     "verify, else SPEC-TOO-STRONG on dispatch order.",
    },
    {
        "id": "pos-negate-present-swap",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the presence guard, take the absent case first, and
        # bind the fallback rendering to a typed local reused on both fallback
        # paths. Same value flow; the reproof is a `loom_solve` plus a case split.
        "module": _impl_reproved(
            "    let fallback : String := v.generic\n"
            "    let out : String :=\n"
            "      if ! v.present then fallback\n"
            "      else\n"
            "        match v.prep with\n"
            "        | PrepResult.json text => text\n"
            "        | PrepResult.unserializable => fallback\n"
            "    return out",
            "prove_correct displayJson by\n"
            "  loom_solve\n"
            "  simp [jsonDisplay]\n"
            "  cases v.present <;> cases v.prep <;> rfl"),
        "rationale": "negating the presence guard, taking the absent case first, "
                     "and binding the fallback rendering to a shared local leaves "
                     "the three-way choice identical (`!present` selects the "
                     "fallback exactly where `present` did not, and both fallback "
                     "paths surface the same `generic`), so `out = jsonDisplay v` "
                     "is unchanged; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on branch order / fallback binding.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). The
    # residual admissibility risk on a total-domain spec is that the
    # discriminating arm is DEGENERATE — a choice that never actually separated
    # the JSON text from the generic rendering would read like a live one. This
    # case discharges an in-region assert pinning that at an F2P-shaped point the
    # discriminating (J) arm genuinely surfaces the JSON text and NOT the generic
    # rendering. The rest of the impl is kept verbatim so the method's own
    # obligation still discharges; the proof is retuned to also close the assert.
    # =====================================================================
    {
        "id": "admiss-choice-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (jsonDisplay { present := true, prep := PrepResult.json \"dq\", generic := \"sq\" } = \"dq\" ∧\n"
            "       jsonDisplay { present := true, prep := PrepResult.json \"dq\", generic := \"sq\" } ≠ \"sq\"))\n"
            "    let out : String :=\n"
            "      if v.present then\n"
            "        match v.prep with\n"
            "        | PrepResult.json text => text\n"
            "        | PrepResult.unserializable => v.generic\n"
            "      else v.generic\n"
            "    return out",
            "prove_correct displayJson by\n"
            "  loom_solve <;> simp [jsonDisplay]"),
        "rationale": "the discriminating (J) arm is satisfiable AND "
                     "non-degenerate at an F2P-shaped point: for a present, "
                     "serializable value whose JSON text differs from its generic "
                     "rendering, `jsonDisplay` surfaces the JSON text "
                     "(`= \"dq\"`) and NOT the generic rendering (`≠ \"sq\"`), so "
                     "the choice really does fork the two. The in-region assert "
                     "must discharge (else the discriminating arm would be "
                     "degenerate / the obligation vacuous); the impl is kept "
                     "verbatim so the ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete `ValueView` by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-always-generic",
        "kind": "uniqueness",
        "expect": "reject",
        # (J)-attack — the literal pre-patch behaviour: ignore `prep` entirely and
        # always surface the generic rendering. Correct on the fallback (F) and
        # absent (A) arms, but on a present serializable value it shows the
        # generic repr instead of the JSON text.
        "module": _impl(
            "    let out : String := v.generic\n"
            "    return out"),
        "refinement": "always surfacing the generic rendering IS the pre-patch "
                      "behaviour: a JSON-typed value with no dedicated arm falls "
                      "through to the generic rendering, so a present serializable "
                      "value is shown via its host repr (single-quoted, invalid "
                      "JSON) instead of its JSON text. Its faithful counterpart is "
                      "the unchanged repo, which the F2P test — asserting the JSON "
                      "text for a present serializable value — fails on. It is the "
                      "precise change the spec senses (G-DIFF); it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = jsonDisplay v` on the discriminating (J) "
                     "arm: for a present value with `prep = json text` the "
                     "post-image demands `text`, but the rival surfaces `generic`. "
                     "Refuted at a present, serializable value whose JSON text "
                     "(`\"A\"`) differs from its generic rendering (`\"B\"`) — the "
                     "sub-domain where this rival is wrong and the other two "
                     "rivals (absent / non-serializable) are correct.",
        "witness": _witness(
            'displayJsonTester { present := true, prep := PrepResult.json "A", generic := "B" }'),
    },
    {
        "id": "weak-ignore-present",
        "kind": "uniqueness",
        "expect": "reject",
        # (A)-attack — drop the presence test: always dispatch on `prep`, so an
        # absent value is rendered through its (nominal) JSON preparation instead
        # of the generic empty marker. Correct on every present value, wrong on an
        # absent one.
        "module": _impl(
            "    let out : String :=\n"
            "      match v.prep with\n"
            "      | PrepResult.json text => text\n"
            "      | PrepResult.unserializable => v.generic\n"
            "    return out"),
        "refinement": "dropping the presence test is what a real patch that "
                      "prepared the value as JSON WITHOUT first checking presence "
                      "would do. For an absent value it surfaces the JSON "
                      "preparation of that value (e.g. the JSON null literal) "
                      "instead of the empty marker, so the null-display test — "
                      "asserting the empty marker for an absent value — fails. It "
                      "would NOT resolve (it breaks a PASS_TO_PASS behaviour even "
                      "where it satisfies the F2P).",
        "rationale": "REJECT from `out = jsonDisplay v` on the absent (A) arm: for "
                     "`¬present` the post-image demands `generic`, but the rival "
                     "surfaces the `prep` text. Refuted at an ABSENT value "
                     "(`present := false`) whose JSON preparation (`\"null\"`) "
                     "differs from its generic rendering (`\"-\"`) — the "
                     "sub-domain where this rival alone is wrong. Varies the "
                     "`present` binder against the other rivals.",
        "witness": _witness(
            'displayJsonTester { present := false, prep := PrepResult.json "null", generic := "-" }'),
    },
    {
        "id": "weak-mangle-json-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # (J)-PAYLOAD attack — the decision is right (present+serializable DOES
        # take the json arm) but the surfaced text is not the prepared JSON text
        # VERBATIM: it is re-wrapped in an extra delimiter pair. Attacks the
        # `text` binder of `prep = json text`, which the always-generic rival
        # (which never looks at `text` at all) leaves untouched.
        "module": _impl(
            "    let out : String :=\n"
            "      if v.present then\n"
            "        match v.prep with\n"
            "        | PrepResult.json text => \"\\\"\" ++ text ++ \"\\\"\"\n"
            "        | PrepResult.unserializable => v.generic\n"
            "      else v.generic\n"
            "    return out"),
        "refinement": "re-wrapping the prepared JSON text in an extra delimiter "
                      "pair is what a real patch that added its own quoting layer "
                      "around the prepared text (rather than surfacing that text "
                      "as-is) would do. For a present serializable value it emits "
                      "the JSON text with an added outer quote pair, so the "
                      "subtest whose expected value is the bare JSON text fails. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = jsonDisplay v` on the discriminating (J) "
                     "arm: the post-image demands exactly `text`, and any "
                     "transformation of it — even one that keeps the arm choice "
                     "correct — cannot match. Refuted at a present, serializable "
                     "value (`prep = json \"J\"`). This rival varies the `text` "
                     "payload, which no decision-level rival does: it establishes "
                     "that the spec pins the SURFACED TEXT and not merely which "
                     "of the three arms was selected.",
        "witness": _witness(
            'displayJsonTester { present := true, prep := PrepResult.json "J", generic := "G" }'),
    },
    {
        "id": "weak-truncate-json-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # (J)-PAYLOAD attack, second shape — truncate the OUTERMOST characters of
        # the prepared JSON text instead of surfacing it verbatim. Correct only
        # when the prepared text is empty; wrong on every non-empty one. This is
        # the carrier's expressible counterpart of the sibling's structural
        # "outer delimiters dropped" rival (see the footer accounting).
        "module": _impl(
            "    let out : String :=\n"
            "      if v.present then\n"
            "        match v.prep with\n"
            "        | PrepResult.json text => (text.dropRight 1).drop 1\n"
            "        | PrepResult.unserializable => v.generic\n"
            "      else v.generic\n"
            "    return out"),
        "refinement": "dropping the outermost characters of the prepared JSON "
                      "text is what a real patch that sliced the prepared text "
                      "before displaying it would do. A structured value's "
                      "prepared text loses its outer structural characters, so it "
                      "is no longer the valid JSON the subtest expects. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = jsonDisplay v` on the discriminating (J) "
                     "arm: the post-image demands `text` itself, so an impl that "
                     "surfaces a proper substring of it cannot match. Refuted at "
                     "a present, serializable value whose prepared text is "
                     "`\"[1]\"` — a PARTIAL-DOMAIN rival, correct exactly on the "
                     "empty prepared text and wrong on every non-empty one, so "
                     "the refutation point must have a non-empty `text`.",
        "witness": _witness(
            'displayJsonTester { present := true, prep := PrepResult.json "[1]", generic := "G" }'),
    },
    {
        "id": "weak-wrap-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # (F)-attack — the fallback identity: on a present non-serializable value
        # the gold surfaces the generic rendering UNCHANGED; this rival wraps it
        # in an extra delimiter pair. The decision (present/serializable vs not)
        # is exactly right; only the fallback payload is mangled. Built to abuse
        # the `generic` binder on the (F) arm, which the decision rivals hold
        # correct.
        "module": _impl(
            "    let out : String :=\n"
            "      if v.present then\n"
            "        match v.prep with\n"
            "        | PrepResult.json text => text\n"
            "        | PrepResult.unserializable => \"'\" ++ v.generic ++ \"'\"\n"
            "      else v.generic\n"
            "    return out"),
        "refinement": "wrapping the fallback rendering in an extra delimiter pair "
                      "is what a real patch that re-quoted the generic rendering on "
                      "the non-serializable branch (rather than returning it as-is) "
                      "would do. For a present value with no JSON form it surfaces "
                      "the generic text with an added outer quote pair, "
                      "contradicting the F2P subtest whose expected value is the "
                      "generic rendering with NO outer quotes. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = jsonDisplay v` on the fallback (F) arm: "
                     "for a present value with `prep = unserializable` the "
                     "post-image demands `generic` (identity), but the rival "
                     "surfaces `\"'\" ++ generic ++ \"'\"`. Refuted at a present, "
                     "non-serializable value with a non-empty generic rendering "
                     "(`\"G\"`) — the point that makes the (F) arm's dependence on "
                     "`generic` observable and exercises `prep = unserializable`, "
                     "which the other rivals do not.",
        "witness": _witness(
            'displayJsonTester { present := true, prep := PrepResult.unserializable, generic := "G" }'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness — one of which is the mandatory frame-
# mutation rival). Every one is accounted for below. The sibling models the
# STRUCTURAL recursive interchange serialiser DEEPLY — the per-node dispatch, the
# ", " sibling separator, the array/object brackets, and the per-token quote
# delimiter — over read-only inputs carrying fractional heap permissions. This
# backend models only the display CHOICE among three prepared outcomes
# (`jsonDisplay` over `present` / `prep` / `generic`): the serialised text is the
# single OPAQUE field `prep = json text`, validated == the real JSON preparer by
# axiom_check.py (G-AX). So the sibling's structural rivals — which attack the
# internal shape of that text — have no distinct counterpart here; at the choice
# level they all reduce to "used the generic rendering (host repr) instead of the
# JSON text", which the always-generic rival captures. What this backend ADDS is
# the presence arm (A) and the fallback-identity arm (F), each with its own rival.
#
#   sibling case                    -> here                         disposition
#   -----------------------------------------------------------------------------
#   pos-serialize-reorder           -> pos-match-prep-first         RE-AIMED (reshape
#                                                                    of the choice)
#   pos-dsv-copyloop-reshape        -> pos-negate-present-swap      RE-AIMED (reshape
#                                                                    of the choice)
#   admissibility-f2p-string-node   -> admiss-choice-nondegenerate  RE-AIMED
#   frame-mutation-empty            -> (none)                       VACUOUS
#   wrong-delimiter-single-quote    -> weak-mangle-json-payload     PORTED (payload
#                                                                    re-delimited)
#   single-token-no-brackets        -> weak-truncate-json-payload   PORTED (outer
#                                                                    chars dropped)
#   partial-domain-drop-separator   -> (none)                       R-COLLAPSED
#   wrong-fallback-extra-wrap       -> weak-wrap-fallback           PORTED (F arm)
#   (no sibling)                    -> weak-ignore-present          ADDED (A arm)
#
# 3 ported, 3 re-aimed, 1 R-collapsed away, 1 vacuous; 1 rival added for the
# presence arm this backend newly models.
#
# PORTED (wrong-delimiter -> weak-mangle-json-payload; no-brackets ->
#   weak-truncate-json-payload): an earlier accounting recorded these two as
#   R-collapsed onto the (J)-attack on the grounds that "there is nothing
#   transparent to refute inside `text`". That reason was WRONG and this battery
#   was repaired accordingly. It is true that no rival here can mis-BUILD the
#   serialised text — `text` arrives as a field, validated == the real JSON
#   preparer by G-AX — so the sub-token distinctions (which separator, which
#   per-token delimiter) have no counterpart. But `text` is a transparent `String`
#   the impl PASSES THROUGH and the ensures pins `out` to it exactly, so a rival
#   that transforms it on the way out is both writable and refutable at a literal
#   `text`. Both rivals were confirmed by real builds: witness elaborates against
#   the rival, and on the frozen solution `decide` evaluates the tester and reports
#   the proposition FALSE (a plain evaluation, not a tactic gap). Collapsing them
#   onto `weak-always-generic` lost a real distinction: that rival never reads
#   `text`, so the battery previously demonstrated only that the spec pins WHICH
#   ARM is chosen, never that it pins the SURFACED TEXT.
# R-COLLAPSED (drop-separator): the sibling's separator rival attacks whether ", "
#   separates siblings INSIDE the serialised text. That is a property of how the
#   text is BUILT, and this backend never builds it — `text` is a field validated
#   == the real preparer's output by G-AX. A rival can only transform the text it
#   is handed, which is what the two ported payload rivals above do; "the same text
#   but assembled with a different separator" is not a state this carrier can
#   express, so no distinct witness exists. The F2P behaviour it ultimately breaks
#   (a serializable value must render as its valid JSON text) is pinned by arm (J)
#   and defended by three rivals now: the arm choice (weak-always-generic) and the
#   payload identity (weak-mangle/weak-truncate-json-payload).
# VACUOUS (frame-mutation-empty): the sibling's MANDATORY frame-mutation rival
#   keeps the gold body then writes back into a read-only sequence input granted
#   only at half permission, and must be rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent: every parameter is an immutable
#   value, the method declares no `mut` binder, there is no heap and no aliasing.
#   No read-only input to overwrite and no permission system to trip, so the class
#   is vacuous. No substitute is fabricated.
# RE-AIMED (positives): the sibling's two positive controls reshape a recursive
#   `serialize` dispatch and a copy LOOP; this backend's frozen impl is
#   straight-line with no recursion and no loop, so those exact reshapes do not
#   exist. Their SPIRIT — "structurally different, behaviourally identical" — is
#   carried by two reshapes of the three-way choice: dispatch on `prep` first
#   (pos-match-prep-first) and negate the presence guard with a shared fallback
#   local (pos-negate-present-swap). Both compute the same value on every input;
#   the reproof is `loom_solve` plus a case split.
# RE-AIMED (admissibility): the sibling asserts the half-permission admits a
#   normal F2P-shaped node. This backend's method has NO precondition and no
#   permission surface, so that probe is degenerate (every input is in-domain). It
#   is re-aimed at the residual total-domain risk — that the discriminating arm is
#   DEGENERATE — via an in-region assert that at an F2P-shaped point the (J) arm
#   surfaces the JSON text (`= "dq"`) and NOT the generic rendering (`≠ "sq"`).
# PORTED (wrong-fallback-extra-wrap): the sibling's fallback rival wraps the
#   pass-through printout in an extra delimiter pair; this ports directly to the
#   (F) arm — wrap `generic` in an extra quote pair on the non-serializable
#   branch. Refuted at a present, non-serializable value with a non-empty generic
#   rendering.
# ADDED (weak-ignore-present): the sibling's serialiser has no presence gate to
#   model — its rivals never touch the `not present` decision. This backend's
#   ensures pins the absent arm (A) as an independent top-level behaviour with its
#   own free binder `present`. A battery whose every rival held `present` fixed
#   would never demonstrate the spec's dependence on it, so this rival drops the
#   presence test and is refuted at an ABSENT value whose JSON preparation differs
#   from its generic rendering — the point that makes (A) observable. Its faithful
#   counterpart breaks the null-display PASS_TO_PASS behaviour.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the three input binders of
#   the sole ensures (pts = 5 distinct input points):
#     present  — true  (always-generic, J-arm),
#                false (ignore-present, A-arm),
#                true  (wrap-fallback, F-arm),
#                true  (mangle-payload / truncate-payload, J-arm):
#                varied true/false, not held fixed.
#     prep     — json "A" (always-generic),
#                json "null" (ignore-present),
#                unserializable (wrap-fallback),
#                json "J" (mangle-payload),
#                json "[1]" (truncate-payload): both `json text` and
#                `unserializable` constructors exercised, and the `text` PAYLOAD
#                of the `json` constructor is itself varied — the payload rivals
#                are refutable only because `out` is pinned to that exact string.
#     generic  — "B" / "-" / "G": all non-empty and distinct from the surfaced
#                JSON text, and both the (F) and (A) rivals DEPEND on `generic`
#                being the pinned value.
#   Every independent top-level arm of the post-image is attacked, and the (J) arm
#   is attacked at BOTH levels it can fail: the arm CHOICE (always-generic surfaces
#   `generic` where `text` is demanded) and the arm PAYLOAD (mangle/truncate take
#   the right arm but do not surface `text` verbatim). The absent (A) arm
#   (ignore-present) and the fallback-identity (F) arm (wrap-fallback) complete it.
#   Note the payload rivals differ in DOMAIN: mangle-payload is wrong on every
#   present serializable value, truncate-payload only on a non-empty `text`
#   (partial-domain), so its witness must carry a non-empty prepared text.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (`prep` / `generic` are A-reference deep-model references checked
# by axiom_check.py, not consumed by the proof), and this gate ignores AXIOM_TESTS
# regardless.
AXIOM_TESTS = []

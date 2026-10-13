"""properties.py — G-PBT falsification battery for django__django-10999 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct parseDurationSeconds`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  parseDurationSeconds (text : List Char) return (out : Option Int)
    require text ≠ []
    require ∀ c ∈ text, isDigit c ∨ c = ':' ∨ c = '-'
    ensures out = parseDuration text

The method reports the signed total seconds of a colon-separated, sign-prefixed
numeric time component (at most three base-sixty groups). The single load-bearing
``ensures`` pins ``out`` to the deep, fully-unfolded ``parseDuration`` — a pure
``def`` over the method's own argument (``axioms`` region empty; no opaque answer
key to echo). ``parseDuration`` composes several independent behaviours, each
separately attackable:

  * WHOLE-VALUE SIGN — a leading minus negates the ENTIRE base-sixty magnitude
    (every group), not merely the leading group. ``decode`` multiplies the whole
    folded magnitude by ``st.sign``.
  * INNER-SIGN REJECTION — a minus anywhere but the very first position makes the
    component ill-formed (``none``). ``step`` invalidates on a ``'-'`` once
    ``st.seen`` is true.
  * BASE-SIXTY FOLD — closed groups are combined base-sixty
    (``acc := acc * 60 + cur``), right-aligned; a plain sum or a wrong weight
    produces a different total.
  * VALIDITY — a trailing/empty group, a fourth group, or a non-alphabet
    character yields ``none``.

ONE INPUT BINDER, ``text``, free over the whole modeled alphabet. The reject
witnesses drive it to distinct shapes — a two-group leading-minus literal, a
three-group leading-minus literal, an inner-minus literal, and a three-group
positive literal — so the manifest demonstrates the post-image's dependence on
the sign placement, the group count, and the base-sixty combination rather than
on a single pinned shape (pts = 4 distinct input points).

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``parseDurationSecondsTester text = false`` says the
extracted program's result violates the postcondition at that concrete input)
and closes by ``decide``, checked in a file whose ``prove_correct`` block has
been stripped so no tactic script can mask the verdict. ``decide`` reduces the
extracted program by kernel computation; a program shaped as a ``while`` loop
over the character stream does NOT reduce to ``isTrue`` / ``isFalse`` (the loop's
fixpoint is opaque to the kernel). So each reject rival is expressed as a
LOOP-FREE impl that computes its (wrong) value directly by folding over the
character list with the pure helpers — still a wrong implementation sharing the
frozen spec, but one whose extracted tester ``decide``s over the concrete literal.
This is a witnessing convenience, not a weakening: the frozen spec is untouched
and each rival's divergence from ``parseDuration`` is real at the witnessed input
(both halves were checked with ``scripts/lean_verify.sh`` — every witness
elaborates against its rival and gets stuck / fails against the frozen loop-based
solution).

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only sequence input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent: ``text`` is an
    immutable ``List Char`` value, this bundle declares no ``mut`` binder among
    the inputs, and there is no heap or aliasing. There is no read-only input to
    overwrite and no permission system to trip, so the class is vacuous. No
    substitute is fabricated (per the porting map, legitimately dropped here).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``parseDuration text``, a fully-unfolded ``def`` over the
    method's own argument; the only way to satisfy the ensures is to actually
    parse the component correctly, which the positive controls do honestly.
  * CONTROL-FLOW-EFFECT — N/A. The method returns a pure ``Option Int``; there is
    no raise / side-effect difference invisible to the value abstraction.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets a
    sub-behaviour right on most of the domain yet diverges on one (the leading
    sign, the inner sign, or the base-sixty combination).
"""
from pathlib import Path

INSTANCE = "django__django-10999"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the whole gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Rivals that reshape the executable surface
# ---- entirely swap on this block.
_IMPL = """    -- impl-start
    let mut st := initPS
    let mut i := 0
    while i < text.length
      -- invariants-start
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant st = (text.take i).foldl step initPS
      done_with i = text.length
      decreasing text.length - i
      -- invariants-end
    do
      st := step st text[i]!
      i := i + 1
    return decode st
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the two loop-body lines, wholly inside the impl region and unique. The
# ---- loop-preserving positive reshapes only these (naming the exposed
# ---- character in a local `let`), leaving the loop, invariants and frozen
# ---- proof script intact.
_LOOP_BODY = """    do
      st := step st text[i]!
      i := i + 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival that reshapes the impl into a single expression, or the
# ---- admissibility case that adds an in-region assert, may retune it without
# ---- touching the spec or dropping the `prove_correct parseDurationSeconds`
# ---- obligation.
_PROOF_GOLD = """prove_correct parseDurationSeconds by
  loom_solve
  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
  · simp_all [parseDuration, List.take_length]"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the impl is a single expression there is no
# ---- loop invariant to peel, so `loom_solve` alone discharges the equality (for
# ---- a correct reshape) or leaves nothing (for the reject rivals it FAILS,
# ---- which is the point). Reject rivals retune the proof to this shape so the
# ---- rejection is attributable to the spec (the witness), not to a proof script
# ---- tuned to a loop that no longer exists.
_PROOF_FLAT = "prove_correct parseDurationSeconds by\n  loom_solve"


def _rewrite_impl(new_block, proof=_PROOF_FLAT):
    """Full variant: whole impl block replaced, proof retuned."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `parseDurationSecondsTester text = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped. Every argument is
# ---- a concrete character-literal list so `decide` reduces the (loop-free)
# ---- extracted program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for parseDurationSeconds\n"
            "prove_precondition_decidable_for parseDurationSeconds\n"
            "prove_postcondition_decidable_for parseDurationSeconds\n"
            "derive_tester_for parseDurationSeconds\n\n" + body)


def _witness(literal):
    return _tester(
        f'example : parseDurationSecondsTester ("{literal}".toList) = false := by\n'
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no loop at all — maximally structurally different from the gold
        # left-to-right scan. `out` IS `parseDuration text`, so the ensures holds
        # trivially; the reproof is a bare `loom_solve` (no loop invariant to
        # peel).
        "module": _rewrite_impl(
            "    -- impl-start\n    return parseDuration text\n    -- impl-end"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`parseDuration text` directly (no loop). `out` IS `parseDuration "
            "text`, so `out = parseDuration text` holds on the whole domain; the "
            "reproof is `loom_solve`. If this fails to verify the spec is over-fit "
            "to the scan code shape (SPEC-TOO-STRONG). Also the honest "
            "no-ungrounded-echo control: the model is the real work, so a direct "
            "return is correct, not a cheat."),
    },
    {
        "id": "pos-control-named-char",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole loop, the invariants and the frozen proof script; only
        # names the exposed character in a local `let` before stepping.
        # Observationally identical for every input.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "    do\n"
            "      let c := text[i]!\n"
            "      st := step st c\n"
            "      i := i + 1"),
        "rationale": (
            "naming the exposed character in a local `let c` before stepping folds "
            "the same `step` over the same stream, so `out = parseDuration text` "
            "still holds on the whole domain; the loop, invariants and frozen proof "
            "script are untouched. A correct reshape must verify, else the "
            "postcondition is SPEC-TOO-STRONG (rejects a faithful impl over the "
            "shape of the loop body)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method's `require`s (non-empty, {digit,:,-} alphabet)
    # are satisfied by every F2P-shaped input, so the sibling's "a normal input
    # satisfies the precondition" probe is degenerate. The residual admissibility
    # risk on this domain is that the post-image is DEGENERATE at the interesting
    # point — a spec no impl distinguishes reads exactly like one every impl
    # meets. This case discharges an in-region `assert`, at two fully concrete
    # F2P-shaped inputs, that the post-image is NON-DEGENERATE: a three-group
    # leading-minus literal yields the WHOLE-magnitude negation (-4530, not the
    # per-group value), and an inner-minus literal yields `none` — the two
    # behaviours the fix pins, genuinely distinct. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the proof is
    # retuned only to also clear the assert goal by `decide`.
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      parseDuration \"-1:15:30\".toList = some (-4530) ∧\n"
                  "      parseDuration \"-01:-01\".toList = none))\n"),
            _PROOF_GOLD,
            "prove_correct parseDurationSeconds by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [foldl_take_succ step initPS text i (by omega), ← invariant_2])\n"
            "    | (simp_all [parseDuration, List.take_length])\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs: a three-group leading-minus literal must decode to exactly "
            "-4530 — the WHOLE base-sixty magnitude negated (-(1*3600 + 15*60 + "
            "30)), not the per-group value — and an inner-minus literal must decode "
            "to `none`. The in-region assert must discharge (else the obligation is "
            "degenerate at the point the fix cares about); the impl is kept verbatim "
            "so the method's own `ensures` still discharges."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is expressed as a
    # LOOP-FREE fold (single expression over the pure helpers) so its extracted
    # tester `decide`s (see the CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-drop-sign",
        "kind": "uniqueness",
        "expect": "reject",
        # Scan correctly with `step`, but decode the magnitude WITHOUT the overall
        # sign: the leading minus is read but never applied, so every leading-minus
        # literal returns +magnitude. Correct on every non-minus input.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let st := text.foldl step initPS\n"
            "    return (if st.valid = false then none\n"
            "            else if st.curlen = 0 then none\n"
            "            else some (st.acc * 60 + st.cur))\n"
            "    -- impl-end"),
        "refinement": (
            "this ignores the overall sign entirely (returns +magnitude on a "
            "leading-minus literal: -15:30 -> 930 instead of -930). A faithful real "
            "patch that dropped the sign application would report positive durations "
            "for negative literals and FAIL the failing scenario, which pins the "
            "leading-minus two-group literal to its negated total. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = parseDuration text` via the WHOLE-VALUE-SIGN "
            "behaviour: `decode` multiplies the folded magnitude by `st.sign`, and "
            "this rival drops that factor, so the two disagree on every "
            "leading-minus input. Verifying would be SPEC-TOO-WEAK (the sign is "
            "unpinned). Refuted at a two-group leading-minus literal (-15:30)."),
        "witness": _witness("-15:30"),
    },
    {
        "id": "weak-perfield-sign",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behaviour: the leading minus scales only the FIRST group and
        # is reset to +1 at the first separator, so the sign does not carry to the
        # groups that follow it. Correct on single-group and non-minus inputs.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let st := text.foldl (fun st c =>\n"
            "      if st.valid = false then st\n"
            "      else if c = '-' then\n"
            "        (if st.seen then { st with valid := false, seen := true }\n"
            "         else { st with sign := -1, seen := true })\n"
            "      else if c = ':' then\n"
            "        (if st.curlen = 0 then { st with valid := false, seen := true }\n"
            "         else if st.groups = 3 then { st with valid := false, seen := true }\n"
            "         else { st with acc := st.acc * 60 + st.sign * st.cur, cur := 0, sign := 1,\n"
            "                        groups := st.groups + 1, curlen := 0, seen := true })\n"
            "      else if isDigit c then\n"
            "        { st with cur := st.cur * 10 + digitVal c, curlen := st.curlen + 1, seen := true }\n"
            "      else { st with valid := false, seen := true }) initPS\n"
            "    return decode st\n"
            "    -- impl-end"),
        "refinement": (
            "this IS the pre-fix behaviour: the minus attaches to only the leading "
            "group and is reset at the first separator, so -1:15:30 -> "
            "-(1)*3600 + 15*60 + 30 = -2670 not -4530, and -15:30 -> -15*60 + 30 = "
            "-870 not -930. Its faithful real counterpart is the pre-fix pattern, "
            "which FAILS the failing scenario (now pinning the whole magnitude "
            "negated). It would NOT resolve."),
        "rationale": (
            "REJECT from `out = parseDuration text` via the WHOLE-VALUE-SIGN "
            "behaviour: the frozen model carries the sign across every group, this "
            "rival resets it at each separator, so the two disagree on every "
            "multi-group leading-minus input. Verifying would be SPEC-TOO-WEAK "
            "(admits the pre-fix per-group sign). Refuted at a three-group "
            "leading-minus literal (-1:15:30) — where the near-miss's divergence "
            "from the drop-sign rival is visible (the following groups carry no "
            "sign)."),
        "witness": _witness("-1:15:30"),
    },
    {
        "id": "weak-inner-sign-accept",
        "kind": "uniqueness",
        "expect": "reject",
        # The second pre-fix behaviour: a '-' anywhere sets the sign instead of
        # invalidating once a character has been seen, so an inner-minus literal
        # matches and produces a value instead of `none`. Correct on every
        # non-inner-sign input.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let st := text.foldl (fun st c =>\n"
            "      if st.valid = false then st\n"
            "      else if c = '-' then { st with sign := -1, seen := true }\n"
            "      else if c = ':' then\n"
            "        (if st.curlen = 0 then { st with valid := false, seen := true }\n"
            "         else if st.groups = 3 then { st with valid := false, seen := true }\n"
            "         else { st with acc := st.acc * 60 + st.cur, cur := 0,\n"
            "                        groups := st.groups + 1, curlen := 0, seen := true })\n"
            "      else if isDigit c then\n"
            "        { st with cur := st.cur * 10 + digitVal c, curlen := st.curlen + 1, seen := true }\n"
            "      else { st with valid := false, seen := true }) initPS\n"
            "    return decode st\n"
            "    -- impl-end"),
        "refinement": (
            "this IS the second pre-fix behaviour: a minus after a separator is "
            "accepted rather than making the component ill-formed, so an "
            "inner-minus literal like -01:-01 still produces a value instead of "
            "`none`. Its faithful real counterpart is the pre-fix pattern, which "
            "FAILS the failing scenario (now pinning an inner-minus literal to "
            "None). It would NOT resolve."),
        "rationale": (
            "REJECT from `out = parseDuration text` via the INNER-SIGN-REJECTION "
            "behaviour: the frozen model invalidates on a '-' once a character has "
            "been seen (yielding `none`); this rival re-sets the sign instead, so "
            "the two disagree on every inner-minus input. Verifying would be "
            "SPEC-TOO-WEAK (admits inner-sign acceptance). Refuted at an "
            "inner-minus literal (-01:-01), the only witness that drives the "
            "validity/none behaviour."),
        "witness": _witness("-01:-01"),
    },
    {
        "id": "weak-base-sixty-misfold",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no sibling): attacks the BASE-SIXTY FOLD clause — a structural
        # behaviour of `parseDuration` this bundle models transparently that the
        # sibling folded into an opaque deep-model term. Closes each group by
        # ADDING it (`acc := acc + cur`) instead of weighting base-sixty
        # (`acc := acc * 60 + cur`), so the reported total mis-combines the groups.
        # Correct on single-group inputs (no separator fires).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let st := text.foldl (fun st c =>\n"
            "      if st.valid = false then st\n"
            "      else if c = '-' then\n"
            "        (if st.seen then { st with valid := false, seen := true }\n"
            "         else { st with sign := -1, seen := true })\n"
            "      else if c = ':' then\n"
            "        (if st.curlen = 0 then { st with valid := false, seen := true }\n"
            "         else if st.groups = 3 then { st with valid := false, seen := true }\n"
            "         else { st with acc := st.acc + st.cur, cur := 0,\n"
            "                        groups := st.groups + 1, curlen := 0, seen := true })\n"
            "      else if isDigit c then\n"
            "        { st with cur := st.cur * 10 + digitVal c, curlen := st.curlen + 1, seen := true }\n"
            "      else { st with valid := false, seen := true }) initPS\n"
            "    return decode st\n"
            "    -- impl-end"),
        "refinement": (
            "closing a group by adding it rather than weighting base-sixty "
            "mis-combines the components: 1:2:3 -> (1+2)*60 + 3 = 183 instead of "
            "1*3600 + 2*60 + 3 = 3723. A real patch that got the base-sixty "
            "combination wrong would report the wrong number of seconds for every "
            "multi-group duration and FAIL the hours/minutes/seconds and negative "
            "scenarios, which pin the exact totals. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = parseDuration text` via the BASE-SIXTY-FOLD "
            "behaviour: `decode`/`step` combine closed groups as `acc * 60 + cur`; "
            "this rival sums them, so the two disagree whenever the leading groups "
            "are non-zero. Verifying would be SPEC-TOO-WEAK (the base-sixty weight "
            "is unpinned). Refuted at a three-group positive literal (1:2:3), which "
            "moves the sign binder to positive and the group count to the maximum."),
        "witness": _witness("1:2:3"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness — one of which is the mandatory frame-
# mutation rival) plus 2 AXIOM_TESTS. The sibling models the same parse but over
# a `List[int]` of pre-extracted field magnitudes carrying a fractional heap
# permission, with the base-sixty value computed by a verified backward `while`
# loop (`clock_value`/`signed_total`/`pow60` as @Pure deep models). This backend
# models the parse deeply and CONCRETELY from the raw character stream
# (`step`/`decode`/`parseDuration`, the pure region), so the sign, the inner-sign
# rejection, the base-sixty fold AND the validity are all transparent `def`s of
# `text`; there is no axiom and no permission surface.
#
#   sibling case                 -> here                              disposition
#   -----------------------------------------------------------------------
#   pos-control-direct-oracle    -> pos-control-direct-model          PORTED
#   pos-control-local-reshape    -> pos-control-named-char            PORTED (reshaped)
#   admiss-negative-clock        -> admiss-postimage-nondegenerate    RE-AIMED
#   frame-mutate-fields          -> (none)                            VACUOUS
#   partial-perfield-sign        -> weak-perfield-sign                PORTED
#   partial-drop-sign            -> weak-drop-sign                     PORTED
#   partial-inner-sign-value     -> weak-inner-sign-accept            PORTED
#   (no sibling)                 -> weak-base-sixty-misfold           ADDED (clause cov.)
#   ax-ref-sound / ax-containment-> (none)                            DROPPED (G-AX lane)
#
# 4 ported, 1 ported-reshaped, 1 re-aimed, 1 vacuous, 1 added; 2 axiom-lane dropped.
#
# VACUOUS (frame-mutate-fields): the sibling's MANDATORY frame-mutation rival
#   keeps the gold body then writes back into a read-only sequence input granted
#   only at half permission, and must be rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent: `text` is an immutable `List Char`
#   value, the method declares no `mut` binder among the inputs, there is no heap
#   and no aliasing. There is no read-only input to overwrite and no permission
#   system to trip, so the class is vacuous. No substitute is fabricated.
# RE-AIMED (admissibility): the sibling establishes that a normal F2P-shaped input
#   can meet the half-permission + arity + non-negativity precondition. This
#   backend's `require`s (non-empty, {digit,:,-} alphabet) are met by every
#   F2P-shaped input and there is no permission surface, so that probe is
#   degenerate. It is re-aimed at the residual total-domain risk — that the
#   post-image is DEGENERATE at the interesting point — via an in-region assert
#   that a three-group leading-minus literal decodes to the whole-magnitude
#   negation (-4530) and an inner-minus literal decodes to `none`.
# PORTED-RESHAPED (pos-control-local-reshape): the sibling reshapes the final sign
#   application into a local `signed` while keeping the backward fold and every
#   invariant/assert. This backend's sign application lives inside `decode` (out
#   of the impl region), so the exact reshape does not exist; the reshape SPIRIT —
#   "structurally different, behaviourally identical, loop and proof intact" — is
#   carried by pos-control-named-char (name the exposed character in a local `let`
#   before stepping). Same result on every input; the frozen proof is untouched.
# ADDED (weak-base-sixty-misfold): the sibling's base-sixty magnitude is an opaque
#   @Pure deep model (`clock_value`/`pow60`) exercised only in the axiom lane, so
#   the sibling has no reject rival for a mis-weighted fold. This backend models
#   the fold TRANSPARENTLY (`acc * 60 + cur` in `step`/`decode`), an independent
#   top-level behaviour of the post-image, so it gets its own binder-coverage rival
#   (sum instead of base-sixty weight), refuted at a three-group positive literal.
# DROPPED (ax-ref-sound / ax-containment): the sibling's two AXIOM_TESTS re-run the
#   @Pure deep-model soundness/containment check in Docker. mapping.md §3 records
#   that this bundle has NO axiom and NO A-reference: the changed op is the function
#   under change, modeled deeply and CONCRETELY and validated by G-CONF (which
#   applies the patch), so G-AX skips. There is no axiom lane to mirror; this gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = parseDuration text`
#   has ONE binder, `text`, and it is driven to FOUR distinct input points (pts=4)
#   that between them exercise every independent top-level behaviour of the
#   post-image:
#     - WHOLE-VALUE SIGN         : weak-drop-sign (-15:30), weak-perfield-sign
#                                  (-1:15:30) — the sign dropped vs applied only to
#                                  the leading group;
#     - INNER-SIGN REJECTION /    : weak-inner-sign-accept (-01:-01) — an inner
#       VALIDITY (none)             minus that must yield `none`;
#     - BASE-SIXTY FOLD          : weak-base-sixty-misfold (1:2:3) — the group
#                                  combination weight.
#   The sign placement (leading vs inner vs none), the group count (2 / 3),
#   and the base-sixty combination are each moved; the drop-sign and
#   per-group-sign rivals do NOT share a witness (they diverge from gold at
#   different totals and the per-group near-miss only shows its extra error on a
#   multi-group input, so it carries the three-group literal that distinguishes
#   it).
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (deep concrete model, G-CONF
#   not G-AX); this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []

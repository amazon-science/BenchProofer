"""properties.py — G-PBT falsification battery for django__django-15987 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct detectCollision`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the refutation SUBJECT, which here is a ``witness_reference`` rather than
the frozen solution; see WITNESS MECHANICS for the four builds that establish
why the frozen solution cannot serve as one).

DEFENDED SURFACE (one contracted method over a candidate location and a
collection of stored entries):

  detectCollision (target : List Char) (entries : List Entry) return (out : Bool)
    ensures out = matchesText target entries      -- THE load-bearing (and only) clause

An ``Entry`` carries two fields: ``text`` (its canonical textual rendering) and
``wrapped`` (whether the entry is held as a structured value rather than a plain
text value). ``matchesText`` is a fully-unfolded front-recursive ``def`` in the
``pure`` region:

  matchesText target (e :: es) = (e.text == target) || matchesText target es
  matchesText target []        = false

so the single clause pins the presence test as the disjunction, over EVERY entry
at EVERY position, of the TEXT-ONLY comparison ``e.text == target``. That fixes
several independent sub-behaviours of a candidate presence test:

  * TEXT-ONLY: the comparison looks only at ``text`` — an entry's storage form
    (``wrapped``) is immaterial. A candidate whose match depends on ``wrapped``
    (a match suppressed for structured entries) violates the clause: the
    disjunction is ``true`` on a text-equal entry regardless of how it is stored.
  * FULL-SCAN / POSITION-INDEPENDENCE: the disjunction ranges over the WHOLE
    collection; a text-equal entry at ANY index forces ``true``. A candidate that
    ignores some position (the first entry, or all but the last) violates the
    clause whenever the only text-equal entry sits at the ignored position.
  * DETECTION (both directions): the clause is an EQUALITY, so it pins absence
    as hard as presence. Any text-equal entry forces ``true``, so a candidate that
    always reports absence violates it on any collection carrying a match; and a
    collection with no text-equal entry forces ``false``, so a candidate that
    always reports presence violates it there (at the empty collection already).

``matchesText`` is GROUNDED in the inputs (a total fold over ``entries``); the
``axioms`` region is empty (``matchesText`` is a deep model computing the outcome
from the method's own arguments, NOT a consumed answer key), so there is no wrong
echo to build and the ungrounded-oracle probe is replaced by two honest positive
controls. The INPUT BINDERS are ``target`` and ``entries`` (the latter varying in
both element ``text``, element ``wrapped``, position of the match, and length).

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY frame-mutation rivals (write back into one of the two read-only
    sequence inputs, each granted only at ``Acc(list_pred(.), 1/2)``, and be
    rejected for INSUFFICIENT PERMISSION). Lean and Velvet are referentially
    transparent: ``target`` and ``entries`` are immutable values, this bundle
    declares NO ``mut`` binder over any input, and there is no heap and no
    aliasing — so there is no read-only input to overwrite and no permission
    system to trip. The class is vacuous; no substitute is fabricated.
  * ADMISSIBILITY — APPLIES, RE-AIMED. The nagini sibling reads both
    half-permission inputs at a reachable index to prove the precondition admits a
    normal input. This method declares NO ``require`` clause, so the sibling's
    literal probe is vacuous — but "no precondition" is NOT a reason to drop the
    lane. The analogue on a total carrier is the obligation being UNSATISFIABLE or
    DEGENERATE at exactly an F2P-shaped input, which a positive that discharges
    the obligation at that concrete input tests directly. Landed as
    ``admiss-f2p-wrapped-point``: a live in-region ``assert`` demanding the
    post-image take DISTINCT non-trivial values at the two shapes that matter —
    ``true`` at a single text-equal entry held as a STRUCTURED value (the F2P
    shape) and ``false`` at a single non-matching plain-text entry — with the
    frozen impl kept verbatim so the method's own ``ensures`` discharges too.
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. The nagini
    value-double-mask (the exact pre-patch bug) and the two partial-domain rivals
    re-express directly onto the TEXT-ONLY and FULL-SCAN sub-behaviours of the
    single clause, plus the constant-false near-miss and its over-reporting
    mirror (constant-true, refuted at the empty collection).
  * UNGROUNDED-ORACLE ECHO — N/A. ``matchesText`` is a total ``def`` over the
    method's own inputs; there is no answer key to echo. Replaced by the two
    honest positive controls (a structurally different loop + the direct impl).

WITNESS MECHANICS. The carrier is fully TRANSPARENT (``matchesText`` computes on
``Char`` / ``Bool`` literals), so a witness reaches the impl through Velvet's
extractor: ``extract_program_for detectCollision`` gives ``detectCollisionExec
target entries = NonDetT.run (detectCollision target entries)``, and the witness
states ``detectCollisionExec t es ≠ DivM.res (matchesText t es)`` at a concrete
``(t, es)`` — with ``decide`` closing the residual literal (no opaque leaf, no
carrier conditioning, so no witness binds a hypothesis and there is no
joint-satisfiability obligation). Each reject rival is a straight-line loop-free
CLOSED FORM whose extracted program DOES reduce to a literal, so the witness
ELABORATES against the rival (checked: exit 0).

The DISCRIMINATING SUBJECT is NOT the frozen impl, and every reject case says so
explicitly via ``witness_reference``. The frozen impl carries a ``while`` loop
whose extracted program elaborates to an unreduced ``forIn Lean.Loop.mk`` term
under ``loom.semantics.choice "demonic"``, and Lean cannot synthesize a
``Decidable`` instance for ANY proposition about it. Measured, four builds per
case: the honest witness fails on the frozen impl with

    error: failed to synthesize
      Decidable ¬(NonDetT.run do let r ← forIn Lean.Loop.mk ...)

and a FORGERY asserting the OPPOSITE (``=`` for ``≠``, i.e. claiming the frozen
impl is CORRECT at that input) fails with the SAME error modulo the flipped
connective — ``Decidable ((NonDetT.run do ...`` — so the frozen impl's exit code
carries NO information about the claim and could not attest to anything. Each
case therefore names ``pos-control-direct`` (a VERIFYING impl of this same spec,
independently required to build, whose extracted program reduces) as the
refutation subject. Against THAT subject the exit code tracks the claim: the
honest witness fails with the semantic

    error: Tactic `decide` proved that the proposition False is false

while the flipped-claim forgery fails with a DIFFERENT error (``No goals to be
solved`` — the claim was already discharged), which is what makes the refutation
real rather than a tactic mismatch.

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom``; the sole callee
``str(d)`` is folded into an R-refinement — each ``Entry`` carries its already
coerced ``text`` — validated by ``conformance_check.py`` / G-CONF, not
axiomatized). Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15987"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct detectCollision
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the backward per-entry loop plus the
# final return). Reject rivals replace it with a loop-free closed form (so their
# extracted program reduces under decide); the direct positive control replaces
# it with `return (matchesText target entries)`.
_IMPL = (
    "    let mut found := false\n"
    "    let mut i := entries.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ entries.length\n"
    "      invariant found = matchesText target (entries.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let e := entries[i - 1]!\n"
    "      found := (e.text == target) || found\n"
    "      i := i - 1\n"
    "    return found"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The single per-entry accumulation step (the text comparison OR-ed into the
# running flag). The loop-preserving positive control commutes this `||`.
_STEP = "      found := (e.text == target) || found\n"

assert _BASE.count(_STEP) == 1, "accumulation step drifted from expected text"

# The frozen prove_correct tactic body (unique in the file, elided from the spec
# view). The direct positive control retunes it (the loop is gone, so `loom_solve`
# alone closes the residual goal); the commuted control retunes it with a single
# commutativity rewrite; every reject rival keeps it as-is (it fails to close the
# wrong impl — the intended rejection — but the witness, not the tactic failure,
# is what the gate scores).
_PROOF = (
    "prove_correct detectCollision by\n"
    "  loom_solve\n"
    "  rw [matchesText_drop_step target entries i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _rival(expr: str) -> str:
    """Solution.lean whose impl body is a single loop-free `return (<expr>)`."""
    return _swap(_BASE, _IMPL, f"    return ({expr})")


# ---- the refutation SUBJECT every reject case is discriminated against.
# ---- NOT the frozen impl: its extracted `while` loop admits no `Decidable`
# ---- instance for any proposition, so its exit code is claim-independent (a
# ---- forgery asserting the frozen impl is CORRECT fails with the same error).
# ---- This is `pos-control-direct`'s module: the same frozen spec, a VERIFYING
# ---- impl (so it cannot violate the spec at any input, which is what makes
# ---- refuting a witness against it sound), and loop-free, so it REDUCES and
# ---- the exit code tracks the claim. The gate re-checks both properties
# ---- (shares the spec; verifies) before using it.
_REFERENCE = _swap(
    _swap(_BASE, _IMPL, "    return (matchesText target entries)"),
    _PROOF,
    "prove_correct detectCollision by\n  loom_solve")


# ---- witness preamble. The spec is a `method` CONTRACT over a fully-transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `detectCollisionExec t es` is `NonDetT.run (detectCollision t es)`;
# ---- `≠ DivM.res (matchesText t es)` says the impl's output contradicts the
# ---- postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict. The loop-free rival reduces under `decide`; gold's loop stays
# ---- stuck, so the same witness fails on gold — the required discrimination.
_EXTRACT = "extract_program_for detectCollision\n\n"


def _witness(tgt: str, ents: str) -> str:
    return _EXTRACT + (
        f"example : detectCollisionExec {tgt} {ents} ≠ "
        f"DivM.res (matchesText {tgt} {ents}) := by\n"
        "  unfold detectCollisionExec detectCollision\n"
        "  simp [NonDetT.run, pure]\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT impl
    # that keeps the frozen backward loop and its invariants BYTE-IDENTICAL, only
    # commuting the accumulation step (`found || (e.text == target)` instead of
    # `(e.text == target) || found`). Boolean `||` is commutative, so every loop
    # invariant and the `out = matchesText target entries` obligation still hold;
    # the proof needs only a single `Bool.or_comm` rewrite to match the reshaped
    # order. A faithful correct reshape that could NOT verify would mean the clause
    # is over-fit to one syntactic OR-order => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-commuted-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _STEP,
                  "      found := found || (e.text == target)\n"),
            _PROOF,
            "prove_correct detectCollision by\n"
            "  loom_solve\n"
            "  rw [matchesText_drop_step target entries i (by omega) (by omega)]\n"
            "  simp_all [Bool.or_comm]"),
        "rationale": "commuting the accumulation `||` computes the SAME flag on "
                     "every step (Boolean OR is commutative), so the loop invariant "
                     "`found = matchesText target (entries.drop i)` and the ensures "
                     "`out = matchesText target entries` still hold; the reproof is "
                     "the frozen script plus one `Bool.or_comm`. A correct reshape "
                     "must verify, else the clause is SPEC-TOO-STRONG on OR-order.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). `matchesText target entries` is GROUNDED in the
    # arguments (a total fold), so `return matchesText target entries` is a correct
    # fully-grounded implementation, not an ungrounded-oracle echo — and it doubles
    # as proof the spec is not echo-vulnerable: any WRONG constant/echo fails
    # `out = matchesText target entries`. The loop is gone, so the frozen proof
    # body's loop reasoning is unneeded and the residual goal closes under
    # `loom_solve` alone.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _REFERENCE,
        "rationale": "the post-image `matchesText target entries` is GROUNDED in "
                     "the inputs (a total fold, no opaque answer key), so `return "
                     "matchesText target entries` is the honest cheapest CORRECT "
                     "impl. It MUST verify — the clause is literally `out = "
                     "matchesText target entries` — else the single postcondition "
                     "clause is SPEC-TOO-STRONG. Also shows the spec is not "
                     "echo-vulnerable: any wrong constant/echo fails the clause.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's literal probe (a half-permission read at a
    # reachable index) is vacuous here: no `require` clause exists. RE-AIMED at
    # the residual admissibility risk on a TOTAL carrier — that the obligation is
    # UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped input. One live
    # in-region `assert` pins the post-image to two DISTINCT non-trivial values at
    # the two shapes that matter:
    #   (a) `true` at a single entry that text-matches the candidate but is held
    #       as a STRUCTURED value (`wrapped = true`) — the F2P shape, and the one
    #       point at which an over-strong obligation would be unsatisfiable; and
    #   (b) `false` at a single non-matching plain-text entry — so the image is
    #       not collapsed to the constant `true`.
    # The frozen impl is kept VERBATIM so the method's own `ensures` discharges
    # too; the proof adds one `decide` for the extra assert goal (both regions are
    # elided from the spec view). The assert is LIVE, not decorative: flipping
    # either conjunct leaves `decide` refuting it semantically ("Tactic `decide`
    # proved that the proposition ... is false"), checked with two real builds.
    # =====================================================================
    {
        "id": "admiss-f2p-wrapped-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    assert (with_name_prefix `admiss\n"
                  "      (matchesText \"f\".toList [Entry.mk \"f\".toList true] = true\n"
                  "        ∧ matchesText \"f\".toList [Entry.mk \"g\".toList false] "
                  "= false))\n"
                  + _IMPL),
            _PROOF,
            "prove_correct detectCollision by\n"
            "  loom_solve\n"
            "  · decide\n"
            "  rw [matchesText_drop_step target entries i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": "the sole obligation is SATISFIABLE and NON-DEGENERATE at an "
                     "F2P-shaped input: it demands `true` at a single entry whose "
                     "text matches the candidate while being held as a STRUCTURED "
                     "value (`wrapped = true`) — the exact point an over-strong "
                     "obligation would exclude — and `false` at a single "
                     "non-matching plain-text entry, so the post-image is not a "
                     "constant collapse. The in-region assert must discharge (else "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so the "
                     "`ensures` discharges as well. Flipping either conjunct makes "
                     "`decide` refute it, so the assert is live.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- TEXT-ONLY sub-behaviour: the EXACT pre-patch bug ----
    # Match only entries stored as plain text (`wrapped = false`); a text-equal
    # entry held as a STRUCTURED value is suppressed. This is precisely the bug the
    # gold fix removes.
    {
        "id": "weak-prepatch-wrapped-suppression",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "entries.any (fun e => e.text == target && ! e.wrapped)"),
        "refinement": "this IS the pre-patch behaviour: the membership test "
                      "compares the candidate against the raw stored elements, so a "
                      "duplicate held as a STRUCTURED value (never raw-equal to the "
                      "candidate text) goes undetected — matched here by only "
                      "accepting entries with `wrapped = false`. Its faithful "
                      "counterpart is the unchanged repo, which fails to report the "
                      "collision when the configured entry is a structured "
                      "path-like value — exactly the new FAIL_TO_PASS "
                      "(a single such entry), which it FAILS. It would NOT resolve.",
        "rationale": "REJECT from `out = matchesText target entries` (TEXT-ONLY "
                     "sub-behaviour): `matchesText` compares only `text`, so a "
                     "text-equal entry forces the disjunction `true` regardless of "
                     "`wrapped`; the rival returns `false` on a text-equal entry "
                     "with `wrapped = true`. Refuted at a single-entry collection "
                     "whose only entry is a text-match held as a structured value — "
                     "the sub-domain where the bug lives, and the ONLY witness that "
                     "varies the `wrapped` field to `true`.",
        "witness": _witness('"a".toList', '[Entry.mk "a".toList true]'),
        "witness_reference": _REFERENCE,
    },

    # ---- FULL-SCAN sub-behaviour: ignore the first entry (index 0) ----
    {
        "id": "weak-skip-first-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every position EXCEPT index 0: a text-equal entry listed
        # FIRST is never detected.
        "module": _rival(
            "(match entries with "
            "| [] => false "
            "| _ :: rest => rest.any (fun e => e.text == target))"),
        "refinement": "a real patch whose membership test skips the first "
                      "configured entry misses a candidate location listed as that "
                      "first entry; the failing test uses a single-entry collection "
                      "(the match at index 0), so this variant fails to report the "
                      "collision and would NOT resolve.",
        "rationale": "REJECT from `out = matchesText target entries` (FULL-SCAN "
                     "sub-behaviour): `matchesText` ranges over the whole "
                     "collection, so a match at index 0 forces `true`; the rival "
                     "drops the first entry and returns `false`. Refuted at a "
                     "two-entry collection whose ONLY text-match is the first "
                     "entry (both entries plain-text, `wrapped = false`) — varies "
                     "`entries` to a match-at-front shape.",
        "witness": _witness(
            '"a".toList',
            '[Entry.mk "a".toList false, Entry.mk "b".toList false]'),
        "witness_reference": _REFERENCE,
    },

    # ---- FULL-SCAN sub-behaviour: consult ONLY the last entry ----
    {
        "id": "weak-only-last-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Report presence from the LAST configured entry alone: correct when the
        # match (if any) is last, wrong whenever a match exists only at an earlier
        # position.
        "module": _rival(
            "(match entries.getLast? with "
            "| none => false | some e => e.text == target)"),
        "refinement": "a real patch whose membership test consults only the last "
                      "configured entry misses a candidate location listed at any "
                      "earlier position; for a multi-entry collection with the "
                      "match not last it fails to report the collision and would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = matchesText target entries` (FULL-SCAN "
                     "sub-behaviour): a match at an earlier index forces the "
                     "disjunction `true`, but the rival looks only at the last "
                     "entry and returns `false`. Refuted at a three-entry "
                     "collection whose only text-match sits in the MIDDLE (index "
                     "1, not last) — varies `entries` to a match-not-last shape and "
                     "to length three.",
        "witness": _witness(
            '"m".toList',
            '[Entry.mk "x".toList false, Entry.mk "m".toList false, '
            'Entry.mk "z".toList true]'),
        "witness_reference": _REFERENCE,
    },

    # ---- DETECTION sub-behaviour: constant absence (near-miss) ----
    {
        "id": "weak-constant-false",
        "kind": "uniqueness",
        "expect": "reject",
        # The cheapest wrong impl: never reports presence. Correct only on the
        # no-match sub-domain.
        "module": _rival("false"),
        "refinement": "a real patch that always reports 'not present' never "
                      "signals the collision even when a candidate location IS "
                      "among the configured entries; it fails the failing test "
                      "(which requires the collision to be reported) and the "
                      "duplicate-guard passing tests, and would NOT resolve.",
        "rationale": "REJECT from `out = matchesText target entries` (DETECTION "
                     "sub-behaviour): on any collection carrying a text-match the "
                     "disjunction is `true` while the rival returns `false`. "
                     "Refuted at a single plain-text entry that text-matches the "
                     "candidate (`wrapped = false`) — the cheapest matching input.",
        "witness": _witness('"c".toList', '[Entry.mk "c".toList false]'),
        "witness_reference": _REFERENCE,
    },

    # ---- DETECTION sub-behaviour, the OTHER direction: constant presence ----
    # Every rival above UNDER-reports (returns `false` where the disjunction is
    # `true`), so an impl that OVER-reports was unattacked: the clause is an
    # equality, and it pins absence just as hard as presence. `return true` is
    # correct on exactly the match sub-domain and wrong everywhere else — refuted
    # at the EMPTY collection, where `matchesText` is `false` by its base case.
    # This is also the only witness that varies `entries` to length 0.
    {
        "id": "weak-constant-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("true"),
        "refinement": "a real patch that always reports 'present' signals a "
                      "collision for EVERY application, including ones whose "
                      "default location is not among the configured entries — so "
                      "it breaks the passing tests that require no collision to be "
                      "reported for an unlisted default location (and would make "
                      "the check fire on an empty configuration). It trades the "
                      "failing test for a broad regression and would NOT resolve.",
        "rationale": "REJECT from `out = matchesText target entries` (DETECTION "
                     "sub-behaviour, over-reporting direction): the clause is an "
                     "EQUALITY, so it pins absence too — on a collection carrying "
                     "no text-match the disjunction is `false` while the rival "
                     "returns `true`. Refuted at the EMPTY collection, where "
                     "`matchesText` is `false` by its base case: the cheapest "
                     "no-match input, and the only witness at length 0.",
        "witness": _witness('"a".toList', '([] : List Entry)'),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation rivals, 4 uniqueness rivals) plus a
# 1-case AXIOM lane. This bundle models the SAME purely-functional core — whether
# a candidate location coincides, by text, with any configured entry — over a
# carrier of `Entry` values (each carrying `text` and a `wrapped` storage flag),
# via a backward per-entry fold. The positive control and the value/partial-domain
# rivals port near 1:1; the two frame cases and the admissibility case are
# genuinely vacuous on a referentially-transparent, precondition-free carrier; and
# a second positive control is added.
#
#   sibling case                              -> here                          disp.
#   -------------------------------------------------------------------------------
#   pos-control-disjunctive-accumulator       -> pos-control-commuted-accumulator  PORTED
#   admiss-reachable-read                      -> admiss-f2p-wrapped-point      RE-AIMED
#   frame-mutation-write-value_matches         -> (none)                        VACUOUS
#   frame-mutation-write-is_path_object        -> (none)                        VACUOUS
#   weak-prepatch-pathobject-suppression       -> weak-prepatch-wrapped-suppression  PORTED
#   partial-domain-skip-index-0                -> weak-skip-first-entry         PORTED
#   partial-domain-only-last                   -> weak-only-last-entry          PORTED
#   weak-constant-false                        -> weak-constant-false           PORTED
#   (no sibling)                               -> pos-control-direct            ADDED (2nd pos.)
#   (no sibling)                               -> weak-constant-true            ADDED (over-report)
#   AXIOM_TESTS (1, ax-soundness)              -> (none)                        DROPPED (G-AX)
#
# 5 ported, 1 re-aimed, 2 added, 2 vacuous, 1 dropped = 8 SPEC cases
# (2 soundness, 1 admissibility, 5 uniqueness).
#
# PORTED (positive control): the sibling replaces the branch with a branch-free
#   disjunctive accumulator `result = result or value_matches[i-1]`, keeping the
#   backward sweep and the drop-framing intact. This backend's frozen impl already
#   IS a disjunctive accumulator (`found := (e.text == target) || found`), so the
#   analogous structurally-different-but-correct reshape commutes that `||`; the
#   loop and every invariant stay byte-identical and the reproof is the frozen
#   script plus one `Bool.or_comm`. Verified to build.
# PORTED (weak-prepatch-wrapped-suppression): the sibling's value-double-mask
#   `value_matches[i-1] and not is_path_object[i-1]` lets path-object-ness suppress
#   a real text match — the exact pre-patch bug. It re-expresses onto this carrier
#   as `e.text == target && ! e.wrapped`: match only plain-text entries, suppress a
#   text-equal STRUCTURED entry. Refuted at a single wrapped text-match, the ONLY
#   witness varying `wrapped` to `true` — the load-bearing sub-behaviour of the fix.
# PORTED (weak-skip-first-entry / weak-only-last-entry): the sibling's two
#   partial-domain rivals (skip index 0 / pin only the last index) re-express onto
#   the FULL-SCAN sub-behaviour of `matchesText` — drop the first entry / consult
#   only the last. Each refinement carries over: a faithful counterpart that skips
#   the first configured entry misses a single-entry match (the F2P shape), and one
#   that consults only the last misses an earlier match — neither resolves.
# PORTED (weak-constant-false): the always-miss near-miss ports verbatim as
#   `return false`; correct only on the no-match sub-domain, refuted on any match.
# ADDED (pos-control-direct): a second positive control this backend affords —
#   `return matchesText target entries`, the cheapest grounded correct impl. Guards
#   the clause against being SPEC-TOO-STRONG and demonstrates the post-image is not
#   an echo-vulnerable oracle (it is a total def over the method's own inputs).
# VACUOUS (frame-mutation x2): the sibling carries these MANDATORY because
#   `value_matches` and `is_path_object` are each held at half permission and a
#   rival can illegally store into them. This backend is referentially transparent
#   and declares no `mut` binder — `target`/`entries` are immutable values with no
#   heap footprint — so there is no read-only input to overwrite and no permission
#   system to trip. No substitute is fabricated.
# RE-AIMED (admiss-reachable-read -> admiss-f2p-wrapped-point): the sibling reads
#   both half-permission inputs at a reachable index to prove the precondition
#   admits a normal input. This method declares NO `require` clause, so that
#   literal probe is vacuous — but the LANE is not, and "no precondition" is not a
#   reason to drop it: the analogue on a total carrier is the obligation being
#   unsatisfiable or degenerate at exactly an F2P-shaped input. Landed as a live
#   in-region `assert` demanding two DISTINCT non-trivial post-images — `true` at a
#   single text-matching entry held as a STRUCTURED value (the F2P shape and the
#   point an over-strong obligation would exclude), `false` at a single
#   non-matching plain-text entry — with the frozen impl kept verbatim so the
#   method's own `ensures` discharges too. Liveness checked: flipping either
#   conjunct leaves `decide` refuting it. This restores PRECOND-TOO-STRONG as a
#   tested direction; an earlier revision of this battery dropped the lane.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no axiom
#   `ensures` (the `str(d)` coercion is folded into an R-refinement carried by
#   `Entry.text` and validated by conformance_check.py / G-CONF, not axiomatized),
#   and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders of
#   the sole ensures (pts = 4 distinct input points):
#     target   — "a" (prepatch), "a" (skip-first), "m" (only-last), "c"
#                (constant-false), "a" (constant-true): the candidate text is
#                varied, and each witness pairs it with an entry list where it
#                genuinely matches, or (constant-true) genuinely does NOT.
#     entries  — varied across ALL of its observable axes:
#                * element `wrapped`: `true` (prepatch — the ONLY witness at true)
#                  vs `false` (all others), so the TEXT-ONLY sub-behaviour is
#                  demonstrated (a rival keying on `wrapped` is caught) and no other
#                  rival silently depends on `wrapped`;
#                * match POSITION: index 0 (skip-first), middle index 1 of 3
#                  (only-last), single entry (prepatch, constant-false), NO match
#                  anywhere (constant-true);
#                * length: 0 (constant-true — the base case), 1 (prepatch,
#                  constant-false), 2 (skip-first), 3 (only-last).
#   Every independent sub-behaviour of the single clause is attacked: TEXT-ONLY
#   (prepatch), FULL-SCAN in both directions (skip-first / only-last), and
#   DETECTION in both directions (constant-false under-reports, constant-true
#   over-reports). Both positive controls defend the whole clause and the
#   admissibility case pins the post-image non-degenerate at the F2P shape.
#   No two rivals are refuted at the same input.
#   PROBED FOR SPEC HOLES during audit and NOT shipped (none verified, so none is
#   a hole): storage-form-only match (`! e.wrapped`), non-empty test, first-char
#   comparison, skip-LAST, only-FIRST, and a length-parity gate — all six were
#   rejected by the frozen spec. Two further CORRECT reshapes were proven to
#   verify (a forward `List.any` closed form and a forward-sweeping loop with a
#   `take`-based invariant), so the clause is not over-fit to the backward sweep.
# WITNESS DISCRIMINATION (four real builds per reject case; see WITNESS MECHANICS
#   for the exact error strings): each witness ELABORATES against its loop-free
#   rival (exit 0 — the extracted program reduces to a literal that provably
#   differs from `matchesText` at the probed input) and FAILS against the
#   `witness_reference` with a SEMANTIC refutation, "Tactic `decide` proved that
#   the proposition False is false". The reference, not the frozen impl, is the
#   subject BECAUSE the frozen impl discriminates nothing: its extracted `while`
#   loop admits no `Decidable` instance, and a forgery asserting the OPPOSITE claim
#   fails there with the same error, so its exit code is claim-independent. Against
#   the reference the forgery fails DIFFERENTLY ("No goals to be solved"), which is
#   what makes each exit code evidence about the claim. No witness binds a
#   hypothesis (the carrier is fully transparent), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears.
AXIOM_TESTS = []

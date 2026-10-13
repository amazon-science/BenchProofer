"""properties.py — G-PBT falsification battery for pytest-dev__pytest-8399 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region — and, for the admissibility case, an in-region
``assert`` — differs, both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct privatizeName`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method, ``privatizeName``):

  privatizeName (base : List Char) return (out : List Char)
    ensures out = '_' :: base            <-- STRUCTURAL: head is the marker AND
                                             the descriptive label carries verbatim
    ensures out.head? = some '_'         <-- MARKER: the leading code point is '_'

A framework component synthesizes a lookup identifier for an auto-generated
helper. The consumer-facing default listing HIDES any identifier whose leading
code point is the underscore marker, surfacing it only under a verbose flag; to
keep these synthesized helpers out of the default listing the produced
identifier must begin with that marker while otherwise carrying its full
descriptive label unchanged. ``base`` is a free, read-only immutable value; there
is NO ``require`` clause, so the admitted domain is total and the equality must
hold for EVERY descriptive label. The two clauses together pin: (a) a leading
underscore marker, and (b) the label body carried verbatim after it.

GROUNDED, NOT AN ORACLE ECHO. Both clauses are stated directly over the method's
own argument ``base`` (a single front cons) — the ``axioms`` region declares
nothing and there is no opaque callee. The cheapest honest impl IS the front
cons, so the ungrounded-oracle-echo class is N/A and the positive controls are
value-shape reshapes that stay correct.

TWO soundness positives, deliberately of DIFFERENT proof difficulty, because on
this carrier "a different shape" is cheap to fake. Measured with the real
verifier: ``['_'] ++ base = '_' :: base`` is closed by bare ``rfl`` — the append
reshape is DEFINITIONALLY the frozen impl, so it re-runs the frozen proof on a
syntactically-different but reduction-identical term. That is a real (if weak)
check that the obligation is re-elaborated, not a probe of spec strength. So a
SECOND positive is carried whose equality is NOT definitional: ``rfl`` on
``(base.reverse ++ ['_']).reverse = '_' :: base`` fails with ``Type mismatch``
(measured), because it needs ``List.reverse_append`` / ``reverse_reverse``
rewriting rather than reduction. That case is what actually tests whether the
frozen obligation admits a faithful correct impl the frozen tactic must WORK to
close — the SPEC-TOO-STRONG direction. Both verify (exit 0, measured).

BINDER / CLAUSE COVERAGE. ``base`` is the sole binder of both clauses. The FIVE
reject witnesses probe distinct labels of FOUR DIFFERENT lengths — empty
(``[]``), length-1 (``['q']``), length-2 (``['x','y']`` and ``['a','b']``),
length-3 (``['p','q','r']``) — so a rival that mishandled only one label shape
cannot pass every witness, and the single binder is genuinely varied. The
variation is MEANINGFUL, not two spellings of one point: the empty label is the
corner where the impl's output has no body at all (``head?`` is ``none`` for the
no-prepend rival), and each length is the point at which its own rival's output
actually diverges from ``'_' :: base``.

The two independent clauses are attacked SEPARATELY, which is what keeps either
from riding on the other:

  * Three rejects (no-prepend, wrong-marker, marker-not-leading) break the
    leading marker and so violate BOTH top-level clauses at their point.
  * Two rejects (weak-body-corrupted-carry, weak-doubled-marker) SATISFY the
    ``head?`` marker clause while violating the structural equality ALONE, so
    they ISOLATE the verbatim-carry clause ``out = '_' :: base`` — the clause the
    other three never attack on its own. They corrupt the carried body at
    OPPOSITE ends: a trailing insertion (``'_' :: base ++ ['z']``) and a leading
    one (``'_' :: '_' :: base``). The leading-insertion case matters most because
    it is the near-miss the downstream default-listing observation cannot see at
    all — a doubly-marked identifier is hidden exactly as a singly-marked one is
    — so its rejection is attributable to the frozen spec and nothing else.

The verbatim-carry half is thus attacked NEGATIVELY (two rejects, both ends) and
defended POSITIVELY (two soundness positives + the admissibility corner).

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling attacks a
    read-only input held at a fractional heap permission by WRITING back into
    it. Lean and Velvet are referentially transparent: every parameter is an
    immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to overwrite and no
    substitute probe to build. Reported as vacuous, not fabricated (see footer).
  * PARTIAL-DOMAIN / carry-corruption — PORTED as weak-body-corrupted-carry
    (audit restored it; the original port dropped it). The frozen spec pins
    verbatim carry as an INDEPENDENT clause `out = '_' :: base`, so a rival that
    prepends the marker correctly but corrupts the carried body is genuinely
    WRONG against the spec (not merely F2P-invisible): it satisfies the `head?`
    marker clause while violating the structural clause. It is the only reject
    that isolates clause 1 alone. See footer for the reversal argument.
  * TERMINATION / diverge — the spec REJECTS the measure-less form, so this is
    NOT a spec hole in that direction; it is nonetheless unshippable as a reject
    case for a MEASURED MECHANICAL reason. This bundle sets
    ``set_option loom.semantics.termination "total"`` (line 4 of the frozen
    file), so the verifier emits a termination obligation and the nagini
    sibling's P1 attack (compute the right name, then loop forever) is answered
    by the same direction of obligation ``MustTerminate`` supplies there.
    Re-derived with real builds, not inherited:
      - impl region ``while true do pure ()`` then ``return base`` (an
        unambiguously wrong value) -> exit 1, ``error: Decreasing annotations
        are required in total correctness semantics``. A rejection attributable
        to the spec.
      - a witness against that same rival -> exit 1 as well, because the
        missing-measure error is raised on the METHOD DECLARATION, which the
        witness file RETAINS after the ``prove_correct`` block is stripped. So
        witness half 1 (must ELABORATE against the rival) is unmeetable and the
        case could only ever record ``witness-unproven``. Measured: the same
        build additionally shows ``decide`` failed for
        ``privatizeNameTester ['a','b'] = false``.
      - the SHARPER rival, which cannot be dismissed as merely missing the
        annotation, CARRIES a measure that does not decrease: ``while 0 < 1``
        with ``done_with 1 < 0`` and ``decreasing (0 : Nat)``. It is REJECTED
        TOO, at exit 1, on the MEASURE's own descent goal: ``unsolved goals
        case «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0``. An earlier revision of
        this file recorded that shape as VERIFYING at exit 0 and escalated it
        as a residual corpus-wide spec hole; that is RETRACTED here on
        re-measurement, and the footer carries the same retraction.
    This disposition TRACKS the termination option and must be re-derived if it
    ever moves. There is NO residual hole in the other direction: both diverging
    shapes this carrier can express are rejected, and the mechanism is in the
    frozen header. ``set_option loom.semantics.termination "total"`` itself
    opens the ``TotalCorrectness`` scope (Loom, ``MonadAlgebras/WP/Options.lean``,
    ``openScope `TotalCorrectness``), line 7 of the frozen file opens it again
    explicitly, and ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the
    ``measure`` and emits ``⌜measure b' < measure b⌝`` as a goal the proof must
    discharge. Only the ``PartialCorrectness`` twin takes a measure and drops
    it, which is why the two lines have to move together and do here.
  * UNGROUNDED-ORACLE ECHO — N/A (see above): both post-image clauses are
    total, fully-transparent functions of the single input binder.

AXIOM lane: the ``axioms`` region declares no ``axiom`` (the identifier is built
purely from its given label; no callee is consulted). ``AXIOM_TESTS`` is dropped;
the gate ignores it regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-8399"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl region: the ENTIRE `-- impl-start` .. `-- impl-end` block
# ---- (a single front cons). It lies wholly inside the one impl region and is
# ---- unique in Solution.lean; both facts are asserted at load by _swap. Each
# ---- variant re-emits the `-- impl-start` / `-- impl-end` markers so the region
# ---- boundary is preserved exactly. ----------------------------------------
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    return '_' :: base\n"
    "    -- impl-end"
)
assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- The frozen impl statement (the return expression) and the frozen proof
# ---- header, each unique in the file. Rivals swap only the return expression;
# ---- the admissibility case prepends an in-region `assert` and leaves the proof
# ---- header + `loom_solve` body untouched (loom_solve discharges the extra
# ---- decidable side goal on concrete literals). Both facts asserted at load.
_GOLD_RET = "    return '_' :: base"
assert _BASE.count(_GOLD_RET) == 1, "frozen return expr drifted / not unique"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block.
    `body` is the text BETWEEN the markers; we wrap it back in the exact
    `-- impl-start` / `-- impl-end` markers so the region boundary is intact."""
    block = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_BASE, _GOLD_IMPL, block)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `privatizeNameTester base = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete label. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. `List Char` has DecidableEq, so the postcondition is
# ---- decidable and every witness closes by `decide` — for the rival it holds
# ---- (its output violates the spec at that label), for the frozen solution it
# ---- FAILS (gold satisfies the spec at every label), which is the required
# ---- discrimination half.
_TESTER = ("extract_program_for privatizeName\n"
           "prove_precondition_decidable_for privatizeName\n"
           "prove_postcondition_decidable_for privatizeName\n"
           "derive_tester_for privatizeName\n\n")


SPEC_TESTS = [
    # =====================================================================
    # (1) POSITIVE CONTROL (soundness) — structurally different but CORRECT.
    # The append value-shape `['_'] ++ base` computes the identical identifier
    # as the front cons `'_' :: base` (definitionally, `['_'] ++ base` reduces to
    # `'_' :: base`), so both clauses `out = '_' :: base` and
    # `out.head? = some '_'` still discharge under the frozen `loom_solve`. If a
    # faithful correct impl could NOT verify => SPEC-TOO-STRONG on impl shape.
    # Doubles as the honest cheapest positive control: the post-image is
    # grounded, so the cheapest correct impl IS the real prepend — no wrong echo.
    # =====================================================================
    {
        "id": "pos-control-append-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("    return ['_'] ++ base"),
        "rationale": "a correct reshape that builds the identifier by appending "
                     "the label to a one-element marker list (`['_'] ++ base`) "
                     "instead of a front cons computes the identical value, so "
                     "both clauses (`out = '_' :: base` and `out.head? = some "
                     "'_'`) still discharge under the frozen proof. Else "
                     "SPEC-TOO-STRONG on impl shape. Cheapest honest positive "
                     "control: the post-image is grounded in `base`, so the "
                     "cheapest correct impl IS the real prepend — no wrong echo. "
                     "NOTE (audit): this equality is DEFINITIONAL (bare `rfl` "
                     "closes `['_'] ++ base = '_' :: base`, measured), so this "
                     "case checks that the obligation is re-elaborated on a "
                     "different term, NOT that the spec admits a shape the proof "
                     "must work to close. `pos-control-reverse-roundtrip` is the "
                     "non-definitional companion that does test that.",
    },

    # =====================================================================
    # (1b) POSITIVE CONTROL, NON-DEFINITIONAL (soundness) — the real
    # SPEC-TOO-STRONG probe. Audit-added: the append reshape above is
    # definitionally the frozen impl (`rfl` closes it), so it cannot detect a
    # spec that only admits impls reducible to the frozen term. This reshape
    # builds the identifier by appending the marker to the REVERSED label and
    # reversing the result — a faithful correct impl computing the identical
    # value, whose equality to `'_' :: base` is NOT definitional: `rfl` on
    # `(base.reverse ++ ['_']).reverse = '_' :: base` fails with `Type mismatch`
    # (measured), needing `List.reverse_append`/`reverse_reverse`. It VERIFIES
    # under the frozen `loom_solve` (exit 0, measured), so the spec is not
    # over-fitted to the frozen impl's reduction behaviour. Had it failed, that
    # would have been SPEC-TOO-STRONG on impl shape.
    # =====================================================================
    {
        "id": "pos-control-reverse-roundtrip",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("    return (base.reverse ++ ['_']).reverse"),
        "rationale": "a correct reshape that appends the marker to the REVERSED "
                     "descriptive label and reverses the result computes the "
                     "identical identifier, but — unlike the append reshape — its "
                     "equality to `'_' :: base` is NOT definitional (bare `rfl` "
                     "fails with `Type mismatch`; it needs reverse_append / "
                     "reverse_reverse). It must still verify: both clauses "
                     "(`out = '_' :: base`, `out.head? = some '_'`) hold of the "
                     "same value. This is the case that actually probes "
                     "SPEC-TOO-STRONG on impl shape — a spec admitting only impls "
                     "that REDUCE to the frozen term would reject this faithful "
                     "one. Audit-added; the pre-existing positive was defeq to "
                     "the frozen impl and could not detect that.",
    },

    # =====================================================================
    # (2) ADMISSIBILITY — no `require` clause exists, so the sibling's "a normal
    # input satisfies the precondition" probe is vacuous. Re-aimed at the
    # residual admissibility risk on a total domain: that the post-image is
    # DEGENERATE / unsatisfiable at the decisive point. The impl is kept verbatim
    # so the method's own obligation still discharges under the frozen proof; an
    # in-region `assert` pins the post-image at an F2P-shaped label, demanding the
    # leading marker be present AND the label body carried verbatim in order
    # (`'_' :: ['a','b'] = ['_','a','b']` and its `head? = some '_'`). The assert
    # is live, not decoration: a false claim about the same point leaves an
    # unsolved goal (verified below by construction). `loom_solve` discharges the
    # extra decidable side goal on concrete literals, so the proof body is
    # unchanged and the obligation statement stays byte-identical.
    # =====================================================================
    {
        "id": "admiss-f2p-corner-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _GOLD_RET,
            "    assert (with_name_prefix `assert\n"
            "      (('_' :: ['a', 'b'] = ['_', 'a', 'b']) ∧\n"
            "       (('_' :: ['a', 'b']).head? = some '_')))\n"
            "    return '_' :: base"),
        "rationale": "the post-image is satisfiable AND non-degenerate at an "
                     "F2P-shaped label: prepending the marker to a non-empty "
                     "label must yield the marker followed by the label body in "
                     "order (`'_' :: ['a','b'] = ['_','a','b']`) with leading "
                     "code point `'_'` — not the marker dropped or the body "
                     "reordered. The in-region assert must discharge (else the "
                     "obligation is degenerate at the interesting point); the "
                     "impl is kept verbatim so both clauses still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS rivals (reject) — wrong impls sharing the frozen spec, each a
    # straight-line return (so its witness is `decide`-able) with a
    # machine-checked refutation witness, and the refinement argument that its
    # faithful real counterpart would NOT resolve the failing observation. The
    # failing observation is: the synthesized identifier is HIDDEN from the
    # default listing, which the consumer keys on solely via a LEADING marker.
    # Rivals (3)-(5) break the leading marker a DIFFERENT way, at a DIFFERENT
    # label length, so those three violate both clauses while varying the binder;
    # rivals (6)-(7) instead keep the leading marker and corrupt the carried body
    # at its tail / its front, isolating the structural clause on its own.
    # =====================================================================

    # (3) NO-PREPEND — the pre-image behaviour: return the label unchanged, with
    # NO marker prepended. This IS the reported bug (the identifier keeps its
    # ordinary-letter prefix). Wrong on every label; refuted at the EMPTY label
    # (length-0 corner) where the marker is entirely absent.
    {
        "id": "weak-no-prepend-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return base"),
        "refinement": "this is the pre-image behaviour the fix corrects: the "
                      "identifier keeps its ordinary descriptive prefix with no "
                      "leading marker, so the default listing SHOWS it (the very "
                      "reported failure) and the failing observation — the "
                      "identifier is hidden by default — is not satisfied. It "
                      "would NOT resolve.",
        "rationale": "REJECT from both clauses: at any label the post-image "
                     "demands a leading marker (`out = '_' :: base`, "
                     "`out.head? = some '_'`) but the impl returns the label "
                     "verbatim. Refuted at the empty label `[]` (length-0 "
                     "corner): gold yields `['_']`, the impl yields `[]`, whose "
                     "`head?` is `none`.",
        "witness": _TESTER +
                   "example : privatizeNameTester ([] : List Char) = false := by\n"
                   "  decide\n",
    },

    # (4) WRONG-MARKER — prepend a DIFFERENT separator code point ('.') instead
    # of the underscore marker. Distinct from no-prepend: a marker IS added, but
    # the wrong one. Refuted at a length-2 label.
    {
        "id": "weak-wrong-marker-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return '.' :: base"),
        "refinement": "a counterpart prefixing the identifier with a "
                      "non-underscore separator is NOT recognized by the "
                      "listing's hide rule (which keys on the underscore marker "
                      "specifically), so the synthesized helper is still shown at "
                      "default verbosity and the failing observation — hidden by "
                      "default — is not satisfied. It would NOT resolve.",
        "rationale": "REJECT from both clauses: the post-image demands leading "
                     "`'_'`, the impl prepends `'.'`. Refuted at `['x','y']` "
                     "(length-2 label): gold `['_','x','y']`, impl `['.','x','y']` "
                     "whose `head?` is `some '.'` != `some '_'`.",
        "witness": _TESTER +
                   "example : privatizeNameTester ['x', 'y'] = false := by\n"
                   "  decide\n",
    },

    # (5) MARKER-NOT-LEADING — the marker code point IS present but NOT at the
    # front (a stray code point precedes it). Distinct from wrong-marker: the
    # right marker char appears, just misplaced — so this rival specifically
    # attacks the `head?` clause (the identifier CONTAINS '_' but does not BEGIN
    # with it). Refuted at a length-3 label.
    {
        "id": "weak-marker-not-leading",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return ' ' :: '_' :: base"),
        "refinement": "a counterpart whose identifier contains the marker but "
                      "does not BEGIN with it is not hidden by the listing rule "
                      "(which keys on the LEADING code point), so the synthesized "
                      "helper is still shown at default verbosity and the failing "
                      "observation — hidden by default — is not satisfied. It "
                      "would NOT resolve.",
        "rationale": "REJECT chiefly from the `head?` clause (`out.head? = some "
                     "'_'`) and equally from the structural clause: the marker is "
                     "present but a stray code point leads. Refuted at "
                     "`['p','q','r']` (length-3 label): gold "
                     "`['_','p','q','r']`, impl `[' ','_','p','q','r']` whose "
                     "`head?` is `some ' '` != `some '_'`.",
        "witness": _TESTER +
                   "example : privatizeNameTester ['p', 'q', 'r'] = false := by\n"
                   "  decide\n",
    },

    # (6) BODY-CORRUPTED — the leading marker is present AND leading (so the
    # `head?` marker clause is SATISFIED), but the carried label body is not kept
    # verbatim (a stray code point is appended). This is the ONLY reject that
    # isolates the STRUCTURAL clause `out = '_' :: base` on its own: the three
    # rivals above each break the leading marker and so violate BOTH clauses at
    # once, leaving the verbatim-carry half attacked only positively (by the
    # positive control + admissibility corner). This rival flips exactly one
    # clause. Audit-added (attack F): the sibling's partial-domain-corrupt-last
    # case is EXPRESSIBLE here — the frozen spec pins verbatim carry as an
    # independent clause (`out = '_' :: base`), the witness discriminates
    # (rival elaborates, gold FAILS by a semantic `decide` refutation), and
    # attack D confirmed the spec correctly rejects body corruption. The drop
    # reasoning conflated the downstream F2P observation (keys on the leading
    # marker only) with the frozen spec (which demands verbatim carry).
    {
        "id": "weak-body-corrupted-carry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return '_' :: base ++ ['z']"),
        "refinement": "a counterpart that prepends the marker correctly but does "
                      "not carry the descriptive label body verbatim (a stray "
                      "code point trails the body) produces an identifier that is "
                      "NOT `'_' :: base`; the synthesized helper's lookup "
                      "identifier no longer equals its intended descriptive label "
                      "with the marker, so the modeled name-construction op is not "
                      "reproduced. It would NOT resolve.",
        "rationale": "REJECT from the STRUCTURAL clause `out = '_' :: base` in "
                     "isolation: the `head?` marker clause is SATISFIED (the "
                     "output still begins with `'_'`), but the label body is not "
                     "carried verbatim. Refuted at `['a','b']` (F2P-shaped "
                     "label): gold yields `['_','a','b']`, the impl yields "
                     "`['_','a','b','z']`, which differs from `'_' :: base` while "
                     "still having `head? = some '_'`. This is the only reject "
                     "that attacks clause 1 alone.",
        "witness": _TESTER +
                   "example : privatizeNameTester ['a', 'b'] = false := by\n"
                   "  decide\n",
    },

    # (7) DOUBLED MARKER — audit-added (attack D). The marker is present AND
    # leading (so the `head?` clause is SATISFIED, as in (6)), but a SECOND
    # marker code point is inserted, so the carried body is `'_' :: base`
    # rather than `base`. This is the near-miss the battery left unattacked:
    # every existing rival either breaks the leading marker (3, 4, 5) or
    # corrupts the body at its TAIL (6). A rival that corrupts the body at its
    # FRONT — the position the marker itself occupies — is the one an impl
    # would most plausibly produce (prepending unconditionally to a label that
    # is already marked), and it is precisely the class the downstream listing
    # rule CANNOT see: `'__x'` is hidden by default exactly like `'_x'`, so
    # only the frozen spec's verbatim-carry clause rejects it. Confirmed by
    # build: the rival is rejected (exit 1, unsolved goals), its witness
    # elaborates against the rival (exit 0) and FAILS against the frozen
    # solution (exit 1) with a plain-evaluation `decide` refutation, and the
    # flipped-claim forgery pair inverts cleanly (gold 0 / rival 1). Probes a
    # FOURTH label length (1).
    {
        "id": "weak-doubled-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return '_' :: '_' :: base"),
        "refinement": "a counterpart that prepends the marker unconditionally to "
                      "a label that already carries one produces an identifier "
                      "whose body is not the intended descriptive label: the "
                      "synthesized helper's lookup identifier differs from the "
                      "label it is supposed to name, so the modeled "
                      "name-construction op is not reproduced and any consumer "
                      "resolving the helper BY that identifier misses it. Note "
                      "this rival is invisible to the default-listing observation "
                      "(a doubly-marked identifier is hidden just as a "
                      "singly-marked one is), so only the frozen spec's "
                      "verbatim-carry clause catches it. It would NOT resolve.",
        "rationale": "REJECT from the STRUCTURAL clause `out = '_' :: base` alone: "
                     "the `head?` marker clause is SATISFIED (the output still "
                     "begins with `'_'`), but the carried body is `'_' :: base`, "
                     "not `base`. Together with weak-body-corrupted-carry this "
                     "attacks the verbatim-carry clause at BOTH ends of the body "
                     "(front insertion here, tail insertion there). Refuted at "
                     "`['q']` (length-1 label, a fourth distinct length): gold "
                     "yields `['_','q']`, the impl yields `['_','_','q']`, which "
                     "differs from `'_' :: base` while still having "
                     "`head? = some '_'`.",
        "witness": _TESTER +
                   "example : privatizeNameTester ['q'] = false := by\n"
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals) over `generated_fixture_name`
# (carrier `List[int]` with a length-carrying loop + termination + fractional
# permissions). This bundle models the same purely-functional core as a single
# front cons `privatizeName` (carrier `List Char`) with two clauses
# (`out = '_' :: base`, `out.head? = some '_'`), so every sibling case with a
# counterpart lands on those two clauses, re-expressed against `List Char`.
#
#   sibling case                       -> here
#   ---------------------------------------------------------------------
#   pos-control-local-reshape           -> pos-control-append-reshape       PORTED
#   admissibility-fstring-label         -> admiss-f2p-corner-nondegenerate  RE-AIMED
#   frame-mutate-readonly-label         -> (none)                           VACUOUS
#   wrong-marker-dot-prefix             -> weak-wrong-marker-dot            PORTED
#   partial-domain-corrupt-last-char    -> weak-body-corrupted-carry        PORTED (audit)
#   diverge-before-return               -> (none)         SPEC REJECTS / UNWITNESSABLE
#   no-prepend-prepatch-noop            -> weak-no-prepend-prepatch         PORTED
#   + weak-marker-not-leading           (added; head?-clause + binder coverage)
#   + pos-control-reverse-roundtrip     (added by audit; NON-DEFINITIONAL positive)
#   + weak-doubled-marker               (added by audit; front-of-body corruption)
#
# RE-AIMED (admissibility): the sibling re-states in-domain facts (len>0, first
#   code point != marker) discharged from its `Requires`. This bundle has NO
#   `require` clause, so "admits a normal input" is vacuous; the case is re-aimed
#   at proving the post-image is satisfiable AND non-degenerate at an F2P-shaped
#   label (leading marker present, label body carried in order). The in-region
#   assert is discharged symbolically against concrete literals so the frozen
#   `loom_solve` still closes.
#
# VACUOUS (frame-mutation): the sibling's rival WRITES a read-only input held at
#   a fractional heap permission. This backend is referentially transparent, has
#   no heap and no aliasing, and this bundle declares NO `mut` binder — there is
#   no read-only input to overwrite and no discriminating witness could exist.
#   Not fabricated. DEMONSTRATED by the audit rather than asserted: an impl region
#   of `base := base` (the direct transliteration of the sibling's write) is
#   refused by the FRONT END, exit 1 — "`base` cannot be mutated, only variables
#   declared using `let mut` can be mutated", followed by "Failed to parse an
#   assertion without names: WPGen sorry". That is a parse/front-end refusal, not
#   a spec rejection, so there is no rival here whose rejection could be
#   attributed to the frozen spec: the class is genuinely absent on this carrier,
#   not a rival the spec declines to reject.
#
# PORTED (audit) — partial-domain-corrupt-last-char -> weak-body-corrupted-carry.
#   The original port DROPPED this, arguing the downstream F2P observation
#   (identifier HIDDEN by default) keys SOLELY on the LEADING marker, so a rival
#   that prepends the marker but corrupts the carried body is still hidden and
#   thus a "spurious reject". The audit REVERSED that: the audit's obligation is
#   to the FROZEN SPEC, which pins verbatim carry as an INDEPENDENT top-level
#   clause `out = '_' :: base` (G-PANEL-2 validated `'_' :: base` faithful to the
#   real `"_" + base`, so a body-corrupting impl is genuinely wrong, not merely
#   F2P-invisible). It is fully EXPRESSIBLE on this carrier: the rival
#   (`'_' :: base ++ ['z']`) SATISFIES the `head?` marker clause yet VIOLATES the
#   structural clause, its witness discriminates (rival elaborates exit 0, gold
#   FAILS exit 1 by a semantic `decide` refutation at `['a','b']`), and attack D
#   confirmed the spec correctly rejects body corruption. It is the ONLY reject
#   that isolates clause 1 alone — the other three break the leading marker and
#   so hit both clauses at once. The drop reasoning conflated the F2P observation
#   with the frozen spec; the case is restored.
#
# diverge-before-return — SPEC REJECTS IT; UNSHIPPABLE FOR A MECHANICAL REASON.
#   (CORRECTED BY AUDIT. The earlier text here claimed this bundle runs under
#   `loom.semantics.termination "partial"` and that a diverging impl would
#   therefore VERIFY vacuously. That was FALSE about the artifact it ships beside:
#   line 4 of the frozen Solution.lean reads `"total"`. The two settings invert
#   the correct disposition, so the claim is re-derived below with real builds
#   rather than inherited, and it must be re-derived again if the option moves.)
#
#   The sibling's P1 attack (compute the right name, then loop forever before
#   returning it) is caught there by an explicit `MustTerminate(len(label)+2)`
#   obligation. Under `"total"` this bundle emits a termination obligation that
#   answers the same attack in the same direction:
#     * impl region `while true do pure ()` then `return base` (an unambiguously
#       WRONG value) -> exit 1, `error: Decreasing annotations are required in
#       total correctness semantics`. So the spec does NOT admit a diverging
#       impl, and this is not a hole in that direction.
#   It is still not shipped as a reject case, for a MEASURED mechanical reason:
#   a velvet reject case needs a witness that ELABORATES against the rival, but
#   the missing-measure error is raised on the METHOD DECLARATION, which the
#   witness file RETAINS after the `prove_correct` block is stripped. Measured:
#   the witness build against that rival exits 1 on that same loop error, and
#   additionally shows `Tactic `decide` failed for proposition
#   privatizeNameTester ['a','b'] = false`. Witness half 1 is unmeetable, so the
#   case could only ever record `witness-unproven`. Closed by the spec and
#   unrepresentable in the manifest — NOT an admitted rival, and not vacuous.
#
#   NO RESIDUAL HOLE IN THE OTHER DIRECTION, and this paragraph RETRACTS one a
#   previous revision escalated. That revision claimed the `"total"` obligation
#   "accepts ANY measure expression without proving it decreases", and reported an
#   impl region of `while 0 < 1` carrying `done_with False` and
#   `decreasing (0 : Nat)`, returning the unmarked `base`, as VERIFYING at exit 0.
#   RE-MEASURED with a real build on this bundle, that shape is REJECTED at exit 1
#   on the measure's OWN descent goal:
#       unsolved goals
#       case «decreasing_1: (0 : Nat)» ... |- 0 < 0
#   So the strict-decrease side condition IS proven, and the constant measure
#   fails it. The mechanism is in the frozen header: line 4's
#   `set_option loom.semantics.termination "total"` itself opens the
#   `TotalCorrectness` scope (Loom, `MonadAlgebras/WP/Options.lean`, the
#   `openScope `TotalCorrectness` arm), line 7 opens it again explicitly, and
#   `TotalCorrectness.WPGen.forWithInvariantLoop` takes the `measure` and emits
#   `measure b' < measure b` as a goal. Only the `PartialCorrectness` twin takes a
#   measure and discards it. Nothing from this class is escalated as a spec hole,
#   and the class is still unshippable as a reject case here for the WITNESS
#   reason above and not a semantic one: a rejected rival's own file does not
#   compile, so no appended witness can elaborate against it.
#
# ADDED (1, no direct sibling counterpart) — weak-marker-not-leading. The marker
#   code point is present but NOT at the front. This attacks the `out.head? =
#   some '_'` clause specifically (the identifier CONTAINS the marker yet does
#   not BEGIN with it, so the listing rule would not hide it), and moves the
#   binder to a third label length. Together the three reject witnesses probe
#   labels of length 0 / 2 / 3 (`pts=3`), so the single binder `base` is varied
#   and no label shape is pinned; each violates BOTH top-level clauses, so both
#   independent clauses are attacked.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   `axiom` (the identifier is built purely from its given label), and the gate
#   ignores AXIOM_TESTS anyway.
#
# ---------------------------------------------------------------------------
# WHAT THE INDEPENDENT AUDIT MEASURED. Every exit code below was observed on a
# real `scripts/lean_verify.sh` build, so a later reader need not redo them.
#
# ATTACK A (statement integrity) — CLEAN on all cases. The consumer spec view of
#   every variant is BYTE-IDENTICAL to the frozen file (checked with
#   `markers.spec_view`), the `method privatizeName` signature and both `ensures`
#   lines are untouched, the single `prove_correct privatizeName` header survives,
#   and `variant_scope.variant_problems` returns [] for every case. No
#   reformatted-statement hiding place.
#
# ATTACK B (witness discrimination, re-derived) — all FIVE reject witnesses
#   rebuilt by hand on both sides. Rival exit 0 / gold exit 1 in every case, and
#   every gold-side failure is a PLAIN EVALUATION refutation of the concrete
#   claim: "Tactic `decide` proved that the proposition privatizeNameTester <pt>
#   = false is false" at [] / ['x','y'] / ['p','q','r'] / ['a','b'] / ['q']. No
#   missing identifier, no type error, no stuck unfolding, no timeout.
#
# ATTACK B' (the FORGERY test) — run on all five even though a plain evaluation
#   does not require it, because it is cheap here and it is the only thing that
#   proves the exit code tracks the CLAIM. Flipping `= false` to `= true` inverts
#   both sides exactly: the flipped claim now ELABORATES against the frozen
#   solution (exit 0) and FAILS against each rival (exit 1, "`decide` proved that
#   the proposition privatizeNameTester <pt> = true is false"). So gold's exit
#   code carries real information about what is claimed at that label; none of
#   these cases is hollow.
#
# ATTACK C (is the rival wrong, or just different?) — all five rivals differ from
#   gold OBSERVABLY on this carrier, and each was rejected by the verifier at
#   exit 1 with `unsolved goals` on the frozen obligation. `List Char` has
#   DecidableEq and collapses nothing relevant (no Nat truncation, no Option
#   collapse, no coercion): the rivals' outputs are literally different lists at
#   the witnessed labels, which the `decide` evaluations above confirm. None is
#   vacuous.
#
# ATTACK D (SPEC-TOO-WEAK probe) — FOUR new wrong impls the battery did not
#   contain, aimed at what the existing rivals left unattacked. ALL correctly
#   REJECTED (exit 1, `unsolved goals`), so no spec hole in this direction:
#     * `'_' :: '_' :: base`            doubled marker (head? satisfied)  -> 1
#     * `base ++ ['_']`                 marker at the END, not the front  -> 1
#     * `'_' :: base.reverse`           marker right, body order reversed -> 1
#     * `if base.isEmpty then base else '_' :: base`
#                                       correct EXCEPT on the empty label
#                                       (a partial-domain / sub-domain probe) -> 1
#   The first was strong enough to SHIP and is now `weak-doubled-marker`.
#
# ATTACK E (SPEC-TOO-STRONG probe) — FOUR new correct reshapes, ALL VERIFY
#   (exit 0), so the spec is not over-fitted to the frozen impl's shape:
#     * `(base.reverse ++ ['_']).reverse`   NON-definitional (rfl fails) -> 0
#     * `if base.isEmpty then ['_'] else '_' :: base`
#                                            NON-definitional (rfl fails) -> 0
#     * `List.cons '_' base`                definitional                  -> 0
#     * `([['_'], base]).flatten`           NON-definitional (rfl fails) -> 0
#   The first was the most informative and is now `pos-control-reverse-roundtrip`.
#   No faithful correct impl was found that the spec rejects.
#
# ADMISSIBILITY LIVENESS — the in-region assert is LIVE, not decoration, and this
#   was verified by CONSTRUCTION rather than asserted: replacing its claim with a
#   FALSE one about the same point (`'_' :: ['a','b'] = ['a','b','_']`, the marker
#   moved to the tail) makes the build FAIL at exit 1 with `unsolved goals`, while
#   the shipped true claim verifies at exit 0. So the frozen obligation is not
#   degenerate at the F2P-shaped label: the post-image really is satisfiable there
#   and really does pin the marker's POSITION, not merely its presence.
#
# THREE DEFECTS FOUND AND FIXED (this file only; the frozen artifact is untouched):
#   1. The divergence lane was recorded against the WRONG SEMANTICS — the prose
#      twice claimed `termination "partial"` where the frozen file reads `"total"`,
#      and drew the opposite disposition from it. Corrected and re-derived above.
#   2. The SOLE soundness positive was DEFINITIONALLY EQUAL to the frozen impl
#      (bare `rfl` closes `['_'] ++ base = '_' :: base`), so it could not detect a
#      spec admitting only impls that reduce to the frozen term. A
#      non-definitional companion positive was added.
#   3. The verbatim-carry clause was attacked at only ONE end of the body (a
#      trailing insertion). The front-of-body corruption — the near-miss the
#      downstream listing observation cannot see AT ALL — was added as
#      `weak-doubled-marker`, which also moves the binder to a fourth label
#      length.
# ---------------------------------------------------------------------------
AXIOM_TESTS = []

"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25232 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region of ``initialFillStatistics`` is changed — the consumer
spec view elides that region and the ``prove_correct`` body, so
``markers.same_spec`` holds and the ``prove_correct initialFillStatistics``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: it must ELABORATE
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over two read-only scalar inputs):

  initialFillStatistics (fillValue : Option Rat) (nFeatures : Nat)
      return (stats : List Rat)
    ensures stats = List.replicate nFeatures (resolveFill fillValue)          (C1)

Models the first-round constant initialization of the missing-value fill: for a
feature count, it must report one initial fill value per feature, and every
per-feature value must be the CONFIGURED constant (default-resolved to the
neutral numerical ``0`` when none is configured). ``resolveFill`` is a fully
transparent recursive ``def`` (``none => 0``; ``some v => v``) — NOT an opaque
answer key. The single top-level ``ensures`` clause folds two facets over the
sole value carrier ``List Rat``:

  (value)  every one of the ``nFeatures`` entries equals ``resolveFill
           fillValue`` — THE discriminating facet the failing test observes
           (a configured constant of ``100`` must reach every feature, not be
           dropped in favour of the default ``0``);
  (length) the reported vector has exactly ``nFeatures`` entries.

Both facets are grounded in the two input binders (``fillValue`` via
``resolveFill``, ``nFeatures`` via ``List.replicate``); there is no answer key
to echo (``resolveFill`` is a concrete ``def`` and the ``axioms`` region is
empty — the unchanged single-pass constant-fill helper is a ``:|`` choice stub
``constantFill`` whose soundness is G-AX's job, not this gate's). The method has
NO ``require`` clause, so the admitted domain is total.

CARRIER NOTE — the value carrier is ``List Rat``, which HAS ``DecidableEq``, and
``resolveFill`` computes. So the sibling velvet tester route is AVAILABLE:
``derive_tester_for`` synthesises ``initialFillStatisticsTester`` and each reject
witness states ``initialFillStatisticsTester <fillValue> <nFeatures> = false``,
closed by ``decide`` at a concrete input.

Why each witness FAILS against gold: SEMANTICS, not reducibility. The frozen
impl's ``…Exec`` reduces perfectly well in the kernel — the ``:|`` choice is
resolved by the ``findableEqListRat`` instance, whose ``find := fun _ => some v``
the kernel unfolds — so on gold ``decide`` DOES fire and evaluates the tester to
``true``, refuting the witness's ``= false`` claim with

    Tactic `decide` proved that the proposition
      initialFillStatisticsTester (some 100) 1 = false
    is false

i.e. the exact SEMANTIC refutation the discrimination check is supposed to read.
Measured for all five witnesses with scripts/lean_verify.sh (rival exit 0, gold
exit 1 carrying that message).

The ``noncomputable section`` wrapper around the tester directives is
LOAD-BEARING, not cosmetic. Without it, the four generated definitions trip the
compiler's IR check against the frozen impl (``initialFillStatisticsExec ...
depends on declaration 'initialFillStatistics', which has no executable code``)
and gold's build fails on THAT before ``decide`` is ever consulted. Gold then
fails for ANY appended claim regardless of truth, so its exit code carries no
information — and a forged "witness" asserting the rival is CORRECT at an
agreement point (``initialFillStatisticsTester none 0 = true``, the opposite of a
refutation) clears both halves and is recorded as a refutation. Measured on the
unwrapped form: forgery rival exit 0, gold exit 1, and the gate's own
``_STUCK_REDUCTION`` screen does not catch it (the message is an IR-check
failure, not a stuck reduction). Wrapped, the IR check is skipped, gold's only
possible error is ``decide``'s verdict, and the same forgery is correctly caught
(gold exit 0 => ``witness-vacuous``). Verified for the added sign-domain rival
too. Do not remove the wrapper.

Each rival is a STRAIGHT-LINE impl that builds the vector directly (no stub
call), so its ``…Exec`` reduces and ``decide`` closes. Every witness binds NO
variables and states its refutation at literal inputs, so the gate's
consistency probe is trivially satisfiable (no opaque-term conditioning needed —
both the carrier and ``resolveFill`` are transparent).

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS, and it was already vacuous on the
    nagini sibling: both formal parameters are SCALARS passed by value
    (``Optional[int]`` / ``int`` there; ``Option Rat`` / ``Nat`` here), so there
    is no read-only aliased input to overwrite. The sibling records
    ``has_readonly_input == False`` and ships NO frame rival; this backend adds a
    second reason (referential transparency: ``fillValue``/``nFeatures`` are
    immutable values, no ``mut`` parameter, no heap, no permission system). No
    substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. C1 is a total function of the two inputs
    (``resolveFill`` is a concrete ``def``, not an axiomatized oracle); there is
    no opaque answer key a wrong impl could echo. The sibling makes the same
    call. The cheapest correct impl builds ``List.replicate nFeatures
    (resolveFill fillValue)`` directly, which the positive controls cover
    honestly.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` over immutable
    values, no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: rivals
    that are right on part of the domain but drop the configured constant
    (falling back to the default), corrupt a single feature (first / last), or
    report the wrong number of features (one too many / empty).

WITNESS PLACEMENT. The six reject witnesses sit at SIX DISTINCT input points —
``(some 100, 1)``, ``(some 7, 2)``, ``(some 100, 4)``, ``(some 42, 3)``,
``(none, 2)``, ``(some (-5), 2)`` — so ``fillValue`` moves over ``none``, several
positive ``some`` values, and a NEGATIVE ``some``, and ``nFeatures`` over
{1,2,3,4} (pts=6). The value facet is attacked by weak-default-zero,
weak-partial-first, weak-partial-last, weak-sign-collapse; the length facet by
weak-len-long and weak-empty. The variation is meaningful rather than two
spellings of one point: each rival is refuted at an input where it disagrees with
C1 and where at least one OTHER rival agrees with C1, so no witness is a
restatement of another (weak-sign-collapse is the sharpest case — its rival is
correct at all five of the other witnesses' inputs).

AXIOM lane: DROPPED. The axiom lane is G-AX's job; this gate ignores
``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25232"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The ENTIRE frozen impl region of the modeled changed
# ---- function `initialFillStatistics`: it calls the unchanged single-pass
# ---- constant-fill helper (the `:|` stub `constantFill`) with the forwarded
# ---- configured constant and returns its per-feature vector. Lies wholly
# ---- inside the single `-- impl-start`/`-- impl-end` region of that method and
# ---- is unique in Solution.lean.
_GOLD_IMPL = """    -- impl-start
    -- Set up the constant-strategy fill helper with the configured constant,
    -- then read the per-feature initial fill values it produces.
    let stats ← constantFill fillValue nFeatures
    return stats
    -- impl-end"""
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# The frozen proof is `loom_solve` and closes every correct reshape below without
# retuning; rivals keep it verbatim (the rejection is carried by the witness, not
# the tactic script). Anchored only to fail loudly on drift.
_GOLD_PROOF = "prove_correct initialFillStatistics by\n  loom_solve"
assert _BASE.count(_GOLD_PROOF) == 1, "proof region drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl region body replaced."""
    return _swap(_BASE, _GOLD_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `initialFillStatisticsTester <fillValue> <nFeatures> = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped; no
# ---- `axiom`/`sorry`/`native_decide`.
# ---- The `noncomputable section` wrapper is REQUIRED for discrimination, not a
# ---- style choice: unwrapped, the generated defs fail the compiler IR check
# ---- against the frozen impl and gold's build dies before `decide` runs, so its
# ---- exit code stops discriminating and a forged non-refutation passes both
# ---- halves (measured; see CARRIER NOTE). Wrapped, `decide` is the only thing
# ---- that can fail on gold, so gold exit 1 means "gold satisfies the spec here".
_TESTER = (
    "noncomputable section\n"
    "extract_program_for initialFillStatistics\n"
    "prove_precondition_decidable_for initialFillStatistics\n"
    "prove_postcondition_decidable_for initialFillStatistics\n"
    "derive_tester_for initialFillStatistics\n"
    "end\n\n"
)


def _witness(fill_lit, n_lit):
    return _TESTER + (
        f"example : initialFillStatisticsTester {fill_lit} {n_lit} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct-replicate",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the call to the constant-fill helper stub entirely and
        # build the per-feature vector directly as `List.replicate nFeatures
        # (resolveFill fillValue)`. This is the honest cheapest-correct impl and
        # is structurally very different from gold (no callee at all); the frozen
        # `loom_solve` closes it unchanged.
        "module": _impl("    return List.replicate nFeatures (resolveFill fillValue)"),
        "rationale": "a straight-line construction (`return List.replicate "
        "nFeatures (resolveFill fillValue)`) is the simplest correct impl; it "
        "meets C1 by definition, with NO call to the constant-fill helper. If it "
        "fails to verify the postcondition is over-fit to the callee form => "
        "SPEC-TOO-STRONG. Verified: closes under the frozen `loom_solve`.",
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: carry the configured constant through an intermediate local
        # unchanged, call the helper, and return through a second local. Same
        # computation, different executable shape; the frozen proof is kept.
        "module": _impl(
            "    let carried := fillValue\n"
            "    let filled ← constantFill carried nFeatures\n"
            "    let out := filled\n"
            "    return out"
        ),
        "rationale": "a local-variable reshape: carry `fillValue` through an "
        "intermediate local unchanged, call the helper, return through a second "
        "local. Same computation, different shape; keeps the frozen proof valid. "
        "Must verify, else the spec is over-fit to the exact call shape => "
        "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The method has NO `require` clause, so the
    # nagini "a normal F2P-shaped input satisfies the precondition" probe is
    # vacuous on the total domain — nothing could exclude any input. Re-aimed at
    # the residual admissibility risk: that the post-image is DEGENERATE (e.g.
    # constant / never varying with the configured constant) so that no rival
    # could be distinguished. This case discharges an in-region `assert`, at
    # concrete points, that the reported vector genuinely VARIES with the inputs
    # — a 2-feature configured-100 input reports a length-2 vector, the 0-feature
    # input the empty vector, and the resolved value for a configured `some 100`
    # DIFFERS from the resolved default of `none`. The frozen callee call and the
    # obligation are kept verbatim so C1 still discharges; the assert is live (a
    # false claim leaves an unsolved goal — confirmed empirically) and closes
    # under the frozen `loom_solve`.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    -- impl-start\n"
            "    assert (with_name_prefix `adm\n"
            "      ((List.replicate 2 (resolveFill (some (100 : Rat)))).length = 2 ∧\n"
            "       (List.replicate 0 (resolveFill (none : Option Rat))).length = 0 ∧\n"
            "       resolveFill (some (100 : Rat)) ≠ resolveFill none))\n"
            "    -- Set up the constant-strategy fill helper with the configured constant,\n"
            "    -- then read the per-feature initial fill values it produces.\n"
            "    let stats ← constantFill fillValue nFeatures\n"
            "    return stats\n"
            "    -- impl-end"),
        "rationale": "the post-image is non-degenerate: the reported length "
        "genuinely varies with the feature count (2 for a 2-feature input, 0 for "
        "a 0-feature input) and the resolved per-feature value genuinely depends "
        "on the configured constant (`resolveFill (some 100) ≠ resolveFill "
        "none`), so the spec actually constrains the result rather than admitting "
        "a constant. The in-region assert must discharge (else the modeled "
        "behavior would be degenerate); the frozen callee call and obligation are "
        "kept verbatim so C1 still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line impl (so its `…Exec` reduces)
    # carrying a machine-checked refutation witness at a DISTINCT concrete input,
    # plus the refinement argument that its faithful real counterpart would NOT
    # resolve the failing test test_iterative_imputer_constant_fill_value.
    # =====================================================================
    {
        "id": "weak-default-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behavior: ignore the configured constant and report the
        # neutral default for every feature. Correct only when none is configured
        # (or the configured constant IS the default); wrong whenever a non-zero
        # constant is configured.
        "module": _impl("    return List.replicate nFeatures (0 : Rat)"),
        "refinement": "this is the pre-change behavior: the first-round constant "
        "initializer is set up WITHOUT forwarding the configured constant, so the "
        "single-pass helper falls back to the neutral numerical default for every "
        "feature. With the failing test's configured constant of 100 the reported "
        "per-feature values would all be 0, but the test asserts every entry "
        "equals 100 — so the test still FAILS and the patch does not resolve. A "
        "verifying rival here would be a true verify-not-resolve break.",
        "rationale": "REJECT from C1 (value facet): for a configured `some 100` "
        "the spec demands every entry equal `resolveFill (some 100) = 100`, but "
        "the rival reports 0. Refuted at `(some 100, 1)`, where the rival reports "
        "`[0]` and C1 demands `[100]` — the configured-constant sub-domain the "
        "failing test exercises.",
        "witness": _witness("(some (100:Rat))", "1"),
    },
    {
        "id": "weak-partial-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Fill honestly, then corrupt feature 0 to the default. Correct only when
        # the configured constant is the default; wrong at feature 0 otherwise.
        "module": _impl(
            "    return (List.replicate nFeatures (resolveFill fillValue)).set 0 0"),
        "refinement": "a counterpart that special-cases the FIRST feature (an "
        "off-by-one that leaves the initial feature at the default) reports the "
        "wrong value for that feature. The failing test compares every entry, so "
        "it still FAILS on the first feature and the patch does not resolve. A "
        "verify-not-resolve break.",
        "rationale": "REJECT from C1 (value facet) at feature 0: the corrupting "
        "write sets entry 0 to 0, but the spec requires entry 0 to equal "
        "`resolveFill fillValue`, which fails whenever that is non-zero. Refuted "
        "at `(some 7, 2)`, where the rival reports `[0, 7]` and C1 demands "
        "`[7, 7]`.",
        "witness": _witness("(some (7:Rat))", "2"),
    },
    {
        "id": "weak-partial-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Fill honestly, then corrupt the LAST feature to the default. Isolates a
        # trailing off-by-one distinct from the leading one.
        "module": _impl(
            "    return (List.replicate nFeatures (resolveFill fillValue)).set "
            "(nFeatures - 1) 0"),
        "refinement": "a counterpart with a trailing off-by-one (a traversal that "
        "stops one feature short, leaving the final feature at the default) "
        "reports the wrong value for the last feature. The failing test's array "
        "has several features and every entry is compared, so it still FAILS on "
        "the last and the patch does not resolve. A verify-not-resolve break.",
        "rationale": "REJECT from C1 (value facet) at feature nFeatures-1: the "
        "corrupting write sets the last entry to 0, but the spec requires it to "
        "equal `resolveFill fillValue`. Refuted at `(some 100, 4)`, where the "
        "rival reports `[100,100,100,0]` and C1 demands four 100s — a trailing "
        "drop distinct from the leading drop of weak-partial-first.",
        "witness": _witness("(some (100:Rat))", "4"),
    },
    {
        "id": "weak-len-long",
        "kind": "uniqueness",
        "expect": "reject",
        # Fill the RIGHT value but ONE feature too many. Every entry equals
        # `resolveFill fillValue` so the value facet holds, isolating the length
        # facet.
        "module": _impl(
            "    return List.replicate (nFeatures + 1) (resolveFill fillValue)"),
        "refinement": "a counterpart that installs one constant too many (an "
        "off-by-one over-allocation of the per-feature vector) reports a vector "
        "of length n+1 while the data has n features. The failing test requires "
        "the reported vector to match the feature count; a length-(n+1) vector "
        "mismatches the data and the patch does not resolve. A verify-not-resolve "
        "break against the length facet.",
        "rationale": "REJECT from C1 (length facet): the reported vector has "
        "nFeatures+1 entries, not nFeatures. The value facet holds (every entry "
        "is `resolveFill fillValue`), isolating the length facet. Refuted at "
        "`(some 42, 3)`, where the rival reports four 42s and C1 demands three.",
        "witness": _witness("(some (42:Rat))", "3"),
    },
    {
        "id": "weak-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the empty vector: no per-feature constant installed at all. The
        # value facet is vacuously satisfied (no entries), isolating the length
        # facet from the value facet. Refuted even with `none` configured.
        "module": _impl("    return ([] : List Rat)"),
        "refinement": "a counterpart that reports an empty / unpopulated vector "
        "installs no per-feature constant at all; the failing test reads the "
        "reported per-feature values and the comparison against the configured "
        "constant fails on the empty vector (and downstream shape handling "
        "breaks), so the patch does not resolve. A verify-not-resolve break "
        "isolating the length facet from the value facet.",
        "rationale": "REJECT from C1 (length facet): for nFeatures > 0 the empty "
        "vector has the wrong length. The value facet is vacuously true over an "
        "empty vector, so ONLY the length facet fails. Refuted at `(none, 2)`, "
        "where the rival reports `[]` and C1 demands a length-2 vector — a "
        "distinct length break that also exercises the `none`/default branch of "
        "`resolveFill` no other reject witness reaches.",
        "witness": _witness("none", "2"),
    },
    {
        "id": "weak-sign-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by the adversarial audit. Every other rival's witness sits at a
        # NON-NEGATIVE configured constant (100, 7, 100, 42, none/0), so the
        # whole negative sub-domain of `fillValue` went unattacked: a rival that
        # is right on non-negative constants and wrong only on negative ones was
        # untested. This one collapses the sign of the resolved constant, so it
        # agrees with C1 on every non-negative configured constant and violates
        # it on every negative one.
        "module": _impl(
            "    let v := resolveFill fillValue\n"
            "    let m := if v < 0 then -v else v\n"
            "    return List.replicate nFeatures m"),
        "refinement": "a counterpart that normalizes the sign of the configured "
        "constant before installing it (a magnitude-only carry-through) reports "
        "the wrong per-feature value whenever a negative constant is configured. "
        "The failing test compares the reported values against the configured "
        "constant exactly, so with a negative configuration every entry differs "
        "in sign and the test still FAILS — the patch does not resolve. A "
        "verify-not-resolve break on a sub-domain the other rivals leave open.",
        "rationale": "REJECT from C1 (value facet) on the NEGATIVE sub-domain of "
        "`fillValue`: the spec demands every entry equal `resolveFill fillValue` "
        "exactly, but the rival installs its magnitude. Refuted at "
        "`(some (-5), 2)`, where the rival reports `[5, 5]` and C1 demands "
        "`[-5, -5]` — the only reject witness at a negative configured constant, "
        "and the only one whose rival is CORRECT at every point the other four "
        "witnesses test (so it is not a restatement of any of them).",
        "witness": _witness("(some (-5:Rat))", "2"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus 2 AXIOM_TESTS, and the
# sibling contracts `initial_constant_fill(requested: Optional[int], n_features:
# int) -> List[int]` — the same purely-functional core this bundle models. So the
# port is close to 1:1, with the classes re-expressed on the `List Rat` carrier.
#
#   sibling case (nagini)     -> here
#   ---------------------------------------------------------------------
#   pos-explicit-loop          -> pos-direct-replicate       RE-SHAPED
#   pos-local-reshape          -> pos-local-reshape          PORTED
#   admiss-nonvacuous          -> admiss-nondegenerate       RE-AIMED
#   weak-default-zero          -> weak-default-zero          PORTED (G-DIFF prepatch)
#   weak-partial-first         -> weak-partial-first         PORTED
#   weak-partial-last          -> weak-partial-last          PORTED
#   weak-len-long              -> weak-len-long              PORTED
#   weak-empty                 -> weak-empty                 PORTED
#   (none — no sibling case)   -> weak-sign-collapse         ADDED BY AUDIT
#
# 7 ported, 1 re-aimed, 1 added. Nothing dropped for difficulty.
#
# ADDED (weak-sign-collapse): the adversarial audit found the negative sub-domain
#   of `fillValue` unattacked — all five ported witnesses sit at non-negative
#   configured constants, so a magnitude-only carry-through was untested. The
#   added rival is wrong exactly there and correct at every other witness's input.
#
# RE-SHAPED (pos-explicit-loop): the sibling builds the per-feature vector with an
#   explicit forward-append loop appending `resolved_value(requested)` n_features
#   times (no axiom call). Velvet bans `for`, and a hand-rolled backward `while`
#   accumulator would need a drop-step lemma the frozen proof does not carry; the
#   structural analog that preserves the intent ("build it directly, without the
#   callee") is `return List.replicate nFeatures (resolveFill fillValue)` — a
#   loop-free construction with NO call to the constant-fill helper, exactly as
#   structurally-distant from gold as the sibling's loop is. Closes under the
#   frozen `loom_solve`.
# RE-AIMED (admiss-nonvacuous): the sibling asserts the precondition is
#   establishable for a normal input. This method has NO `require` clause, so
#   nothing could exclude any input on the total domain — that probe is vacuous.
#   Re-aimed at proving the post-image is NON-DEGENERATE: the reported length
#   varies with the feature count AND the resolved value depends on the configured
#   constant, discharged by an in-region assert (both facets are decidable on the
#   transparent carrier).
# FRAME / PERMISSION-MUTATION: the sibling explicitly documents this class DOES
#   NOT APPLY — both parameters are scalars passed by value, so there is no
#   read-only aliased input to overwrite (has_readonly_input == False,
#   frame_mutation_included == False), and it ships NO frame rival. Nothing to
#   port; on this backend the class is doubly vacuous (referential transparency,
#   no `mut` parameter, no heap, no permission system). No substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# BINDER / CLAUSE COVERAGE. The input binders are `fillValue : Option Rat` and
#   `nFeatures : Nat`; the single top-level clause C1 folds two facets (value:
#   every entry = resolveFill fillValue; length: len = nFeatures). C1 is DEFENDED
#   by the two positive controls and the admissibility case and ATTACKED by all
#   six rivals: the value facet by weak-default-zero, weak-partial-first,
#   weak-partial-last, weak-sign-collapse; the length facet by weak-len-long,
#   weak-empty.
#   `fillValue` is varied across `some 100`, `some 7`, `some 100`, `some 42`,
#   `none`, `some (-5)` (both the `some` and `none` branches of `resolveFill` are
#   exercised, and the `some` branch over both signs — weak-default-zero pins the
#   configured-constant sub-domain the failing test observes, weak-empty the
#   `none`/default branch, weak-sign-collapse the negative sub-domain).
#   `nFeatures` is varied across 1, 2, 4, 3, 2, 2. Six DISTINCT witness inputs
#   (pts=6): (some 100, 1), (some 7, 2), (some 100, 4), (some 42, 3), (none, 2),
#   (some (-5), 2) — so no clause is demonstrated at a single pinned point and
#   both binders are abused.
#
# WHAT THE AUDIT PROBED AND DID NOT BREAK. New WRONG impls, all correctly
#   rejected by the frozen spec on the CLAUSE (an unsolved `ensures_1` goal, not a
#   tactic mismatch): a wrong `none`-branch default (`none => 1`); one feature too
#   FEW (`replicate (nFeatures - 1) …`, which Nat-truncates at 0 rather than
#   collapsing); a per-feature doubling; a prepended extra head; a cap at two
#   features (`replicate (min nFeatures 2) …`); and the reshaped prepatch that
#   forwards `none` THROUGH the callee (rejected with the callee's `ensures` in
#   hand: `x = replicate n (resolveFill none)` ⊬ `x = replicate n (resolveFill
#   fillValue)`). New CORRECT reshapes, all accepted under the frozen proof: an
#   explicit `match` on the Option in place of `resolveFill`; re-wrapping the
#   resolved constant back into `some` before the callee call; and reversing the
#   constant vector. So no SPEC-TOO-WEAK and no SPEC-TOO-STRONG hole was found on
#   either facet.
#   One correct reshape, `(replicate nFeatures (resolveFill fillValue)).map
#   (fun x => x)`, is NOT accepted under the frozen `loom_solve` alone (residual
#   goal `List.map (fun x => x) (replicate …) = replicate …`). That is a TACTIC
#   gap, not a spec hole, and it is demonstrated rather than asserted: the same
#   impl verifies once the proof is retuned (`loom_solve <;> simp`, and also
#   `loom_solve; simp [List.map_id']`), which a real SPEC-TOO-STRONG hole could not
#   do. Not shipped as a positive control: a positive that needs its proof retuned
#   attests to `simp`'s lemma set rather than to the spec.
#
# WITNESS FORM. The value carrier `List Rat` HAS `DecidableEq` and `resolveFill`
#   computes, so the tester route is available: `derive_tester_for` synthesises
#   `initialFillStatisticsTester` and each witness closes
#   `initialFillStatisticsTester <fillValue> <nFeatures> = false` by `decide`.
#   Each rival is a STRAIGHT-LINE impl, and gold's `…Exec` ALSO reduces — the `:|`
#   choice resolves through the `findableEqListRat` instance, whose
#   `find := fun _ => some v` the kernel unfolds. So on gold `decide` genuinely
#   FIRES and evaluates the tester to `true`, refuting the witness's `= false`
#   claim SEMANTICALLY ("`decide` proved that the proposition … is false"). That
#   is why the tester directives are wrapped in `noncomputable section`: unwrapped,
#   the generated defs trip the compiler IR check against gold's noncomputable
#   impl, gold's build dies before `decide` runs, and its exit code discriminates
#   NOTHING — a forged non-refutation then passes both halves. See the CARRIER
#   NOTE; both forms were measured. Every witness binds NO variables, so the
#   consistency probe is trivially satisfiable.
#   Confirmed empirically with scripts/lean_verify.sh for all SIX rivals: each
#   witness ELABORATES against its rival (exit 0) and FAILS against the frozen
#   solution (exit 1) with the `decide`-verdict message above, each rival module
#   does NOT verify under the frozen proof (exit 1), and a forged witness asserting
#   a rival is CORRECT at an agreement point is caught (gold exit 0).
#
# AXIOM_TESTS: dropped. The axiom lane (constant_statistics / the `constantFill`
#   `:|` stub) is G-AX's job; this gate ignores AXIOM_TESTS.
AXIOM_TESTS = []

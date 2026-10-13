"""properties.py — G-PBT falsification battery for django__django-15525 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct naturalKeyForLoadedRecord``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method over a target-database name and a
mutable store handle:

  naturalKeyForLoadedRecord (targetDb : String) (mut storeHandle : Option String)
      return (key : List String)
    require storeHandle = none
    ensures storeHandle = some targetDb
    ensures key = naturalKeyVia (some targetDb)

The freshly built record's store handle ``storeHandle`` comes in unset
(``none`` — the ``require``), is genuinely mutated, and its post-state is pinned
EXACTLY to ``some targetDb``. The natural key is derived by an UNCHANGED routine
deferred to as the ``opaque`` free function ``naturalKeyVia : Option String →
List String`` — no constraining ``axiom`` (nothing is claimed about WHAT it
returns, only that the operation feeds it the right handle; mapping.md §3, the
G-AX skip). The load-bearing property is the ORDER: the handle must be
associated FIRST and the key derived AFTER, so the returned key is
``naturalKeyVia (some targetDb)`` (the derivation at the target handle), NOT
``naturalKeyVia`` at the incoming ``none`` handle.

TWO independent top-level clauses, each load-bearing:
  (1) ``storeHandle = some targetDb`` — the record is associated with the target
      database. TRANSPARENT (``Option String`` with decidable equality). A body
      that leaves the handle at its incoming ``none``, or associates it with a
      DIFFERENT database, fails here. This is the changed frame, pinned to its
      exact post-state (directive 5).
  (2) ``key = naturalKeyVia (some targetDb)`` — the key is the derivation at the
      TARGET handle. OPAQUE RHS. A body that derives the key at the WRONG handle
      fails here, whether that handle is the pre-association ``none`` (the order
      bug) or any other wrong handle, including a NON-``none`` one derived from
      the input (weak-mangled-key-argument) — so the clause pins the derivation
      argument positively rather than merely excluding the stale handle. Grounded in the input ``targetDb`` via the handle it feeds the
      derivation, NOT an answer-key a wrong impl could echo: the only way to make
      the key equal ``naturalKeyVia (some targetDb)`` is to feed the derivation a
      handle equal to ``some targetDb``, i.e. to associate before deriving.

BINDER STRUCTURE (read before judging binder coverage). Both clauses depend on
the sole input binder ``targetDb`` (clause 1 pins the handle to it; clause 2
pins the derivation argument to it). ``storeHandle`` is fixed by the ``require``
to ``none`` at entry, so the only free input is ``targetDb``. The seven reject
witnesses drive ``targetDb`` over SEVEN distinct values — ``"beta"`` /
``"alpha"`` / ``"default"`` / ``"gamma"`` / ``"epsilon"`` / ``"zeta"`` /
``"delta"`` — so the binder is varied rather than pinned, and each rival is
refuted at its own distinguishing point. (``storeHandle`` is reported as pinned to ``none`` by the coverage
reporter; that is forced by ``require storeHandle = none``, not a gap — every
admissible input has it ``none``, so there is no other value to drive it to.)

WITNESS PLACEMENT — why NOT the tester machinery here. The method's
postcondition equates the returned ``key`` to the OPAQUE ``naturalKeyVia (some
targetDb)``; ``derive_tester_for`` would emit ``decide (key = naturalKeyVia
(some targetDb) ∧ …)``, and ``decide`` gets stuck on the opaque term. So each
reject witness instead states the refutation directly against the extracted
program: ``(naturalKeyForLoadedRecord tgt none).run`` reduces to ``DivM.res
(<the impl's (key, handle) at that input>)``, and the witness asserts it differs
from ``DivM.res (naturalKeyVia (some tgt), some tgt)`` (the post-image pair). It
is checked in a file whose frozen ``prove_correct`` block has been stripped, so
no tactic script can mask the verdict.

  * Clause-(1) rivals (unrouted / wrong-db / mangled-alias / partial /
    skip-assoc-keep-assert) are refuted on the TRANSPARENT handle component: the
    state part of the ``run`` pair is ``none``, ``some "wrongdb"``, or
    ``some (tgt ++ "-x")``, decidably ≠ ``some tgt`` — no conditioning needed.
  * The clause-(2) rivals derive the key at the WRONG handle while the post-image
    requires ``naturalKeyVia (some tgt)``; two opaque terms are not decidably
    distinct, so each refutation is CONDITIONED on a satisfiable single
    hypothesis that the derivation genuinely differs at the two handles — the
    order bug on ``naturalKeyVia none ≠ naturalKeyVia (some tgt)``, and
    weak-mangled-key-argument on ``naturalKeyVia (some (tgt ++ "-x")) ≠
    naturalKeyVia (some tgt)`` (the F2P sub-domain where the related row is
    present under one handle and absent under the other). Each is ONE hypothesis
    about the SAME opaque function at two DIFFERENT arguments; it is satisfiable
    (``naturalKeyVia`` is an arbitrary free function, so the two values may
    differ), so the consistency probe cannot derive ``False`` from it.

Each reject witness below was run against BOTH the rival (exit 0) and the frozen
solution (exit 1) with two real builds and was SEEN to discriminate.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling holds the result
    object at a full/half heap permission an impl could overwrite. Lean and
    Velvet are referentially transparent: ``storeHandle`` is a ``mut`` VALUE
    binder with no heap footprint, no aliasing, and no fractional-permission
    system — the unchanged-frame obligation is instead discharged by pinning
    ``storeHandle``'s exact post-state (clause 1). There is no read-only heap
    input to overwrite and no substitute probe to build. Not fabricated (porting
    map: vacuous on a referentially-transparent backend).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
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
  * UNGROUNDED-ORACLE ECHO — N/A. Clause (2) pins the key to the derivation at a
    handle the impl controls, not to a free answer-key. The only satisfier is
    feeding ``naturalKeyVia`` a handle equal to ``some targetDb`` — i.e. doing the
    association before the derivation — so an "echo" is exactly the honest impl.

AXIOM lane: EMPTY (the ``axioms`` region declares a single ``opaque`` free
function with NO asserted ``ensures`` to validate; mapping.md §3 records the
G-AX skip). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15525"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen impl body (the association, the derivation
# ---- from the updated handle, and the return), verbatim. It lies wholly inside
# ---- the single -- impl-start / -- impl-end region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap), so every variant's
# ---- edit keeps same_spec by construction and leaves the frozen
# ---- `prove_correct naturalKeyForLoadedRecord` STATEMENT intact.
_IMPL = (
    "    storeHandle := some targetDb\n"
    "    let key := naturalKeyVia storeHandle\n"
    "    return key"
)
assert _BASE.count(_IMPL) == 1, "naturalKeyForLoadedRecord impl region drifted from expected text"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case may retune the tactic script without
# ---- touching the spec statement or dropping the obligation. Unique in file.
_GOLD_PROOF = "prove_correct naturalKeyForLoadedRecord by\n  loom_solve"
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Full Solution.lean with ONLY naturalKeyForLoadedRecord's impl body replaced."""
    return _swap(_BASE, _IMPL, body)


def _proof(tactics):
    """Full Solution.lean with ONLY the `prove_correct` TACTIC BODY replaced.

    The impl region and every spec byte are untouched, and the obligation header
    `prove_correct naturalKeyForLoadedRecord` is preserved, so `same_spec` holds
    and `variant_scope` still sees the obligation. Used by the admissibility
    case, which has to discharge a claim at a CONCRETE input *before* closing the
    frozen obligation verbatim — a thing the impl region cannot express here (see
    that case's rationale).
    """
    return _swap(_BASE, _GOLD_PROOF,
                 "prove_correct naturalKeyForLoadedRecord by\n" + tactics
                 + "  loom_solve")


# ---- witness snippets. The gate builds the discriminator file itself: it takes
# ---- the case's `module`, STRIPS its `prove_correct` block (so no tactic script
# ---- can mask the verdict), and appends the `witness` snippet below. So each
# ---- `witness` is JUST the `example`, stated against the extracted `VelvetM`
# ---- program: `(naturalKeyForLoadedRecord tgt none).run` reduces to `DivM.res
# ---- (<impl (key, handle) at that input>)`, and the witness asserts it differs
# ---- from `DivM.res (naturalKeyVia (some tgt), some tgt)` (the post-image pair).
# ---- No `sorry`/`admit`/`native_decide`; the only `opaque`/free symbols it names
# ---- (`naturalKeyForLoadedRecord`, `naturalKeyVia`) are declared by the frozen
# ---- solution too, so they exist on both sides of the two-build check.


# =====================================================================
# reject impl bodies (each shares the frozen spec; only the impl differs)
# =====================================================================

# associate with the WRONG database (a constant `"wrongdb"`) instead of the
# target. Both clauses fail: the handle is some "wrongdb" ≠ some targetDb, and
# the key is naturalKeyVia (some "wrongdb"). The witness refutes on the
# transparent handle clause (1).
_WRONG_DB = (
    "    storeHandle := some \"wrongdb\"\n"
    "    return naturalKeyVia storeHandle"
)

# THE PRE-PATCH BUG (order): derive the key from the handle while it is still
# UNSET, THEN associate. The handle ends up correct (clause 1 holds) but the key
# is naturalKeyVia none, not naturalKeyVia (some targetDb) — clause (2) fails.
_ORDER_BUG = (
    "    let key := naturalKeyVia storeHandle\n"
    "    storeHandle := some targetDb\n"
    "    return key"
)

# never associate at all: leave the handle none and derive at none (the buggy
# skeleton verbatim). BOTH clauses fail. The witness refutes on clause (1).
_UNROUTED = "    return naturalKeyVia storeHandle"

# a PARTIAL fix: associate only on a sub-domain (when the target is a particular
# database), leaving the handle unset otherwise. Correct on that sub-domain,
# wrong on the rest — refuted at a target OUTSIDE the guarded set.
_PARTIAL = (
    "    if targetDb = \"other\" then\n"
    "      storeHandle := some targetDb\n"
    "    else\n"
    "      storeHandle := none\n"
    "    return naturalKeyVia (some targetDb)"
)

# associate with a MANGLED alias DERIVED from the target (`targetDb ++ "-x"`)
# rather than the target itself. Strictly stronger than the constant-wrong-alias
# rival: a constant coincides with the target on the one-point sub-domain
# targetDb = "wrongdb", whereas a mangled derivation is wrong at EVERY input
# (`s ++ "-x" ≠ s` for all `s`). This is the input-dependent wrong-handle shape;
# refuted on the transparent handle clause (1).
_MANGLED_ALIAS = (
    "    storeHandle := some (targetDb ++ \"-x\")\n"
    "    return naturalKeyVia storeHandle"
)

# a near-miss: never associate the record, but ASSERT a true fact about the
# derivation at the target handle — "checking" success against the right handle
# while the record itself is left unassociated. The in-region assert discharges
# (it is a reflexive truth about the target-handle derivation) and so proves
# nothing about the OBSERVABLES; the handle is still `none`. Refuted on clause
# (1). Distinct from _UNROUTED in shape (an auxiliary in-impl proof obligation
# over the correct handle is present and satisfied) though it shares its defect.
_SKIP_ASSOC_KEEP_ASSERT = (
    "    assert (with_name_prefix `chk\n"
    "      (naturalKeyVia (some targetDb) = naturalKeyVia (some targetDb)))\n"
    "    return naturalKeyVia storeHandle"
)

# associate the record CORRECTLY (clause 1 holds exactly), but derive the key at
# an INPUT-DERIVED wrong handle (`some (targetDb ++ "-x")`) rather than at the
# handle the record was associated with. The clause-2 counterpart of
# _MANGLED_ALIAS, and the second clause-2 rival: it isolates clause (2) from
# clause (1) at a NON-`none` derivation argument, so the key clause is shown to
# pin the derivation argument to `some targetDb` per se rather than merely to
# rule out the pre-association `none`. Wrong at EVERY input (`s ++ "-x" ≠ s`),
# so no sub-domain rescues it. Refuted on clause (2), conditioned on the opaque
# derivation differing at the two handles.
_MANGLED_KEY_ARG = (
    "    storeHandle := some targetDb\n"
    "    return naturalKeyVia (some (targetDb ++ \"-x\"))"
)


# =====================================================================
# soundness positive impl bodies (structurally different, CORRECT)
# =====================================================================

# inline the derivation argument: associate the handle, then derive directly
# from `storeHandle` in the return (no intermediate `let key`). Same order, same
# observable — both clauses discharge under the frozen `loom_solve`.
_POS_INLINE = (
    "    storeHandle := some targetDb\n"
    "    return naturalKeyVia storeHandle"
)

# associate the handle, then derive from the LITERAL `some targetDb` rather than
# re-reading the (now-equal) handle. Definitionally the frozen return after the
# assignment; both clauses discharge under the frozen `loom_solve`.
_POS_EXPLICIT = (
    "    storeHandle := some targetDb\n"
    "    return naturalKeyVia (some targetDb)"
)


# =====================================================================
# admissibility — the obligation DISCHARGED BY EVALUATION at exactly the
# F2P-shaped input, as a `have`, before the frozen obligation is closed verbatim.
#
# REPAIRED by an independent audit. The previous version put an in-region
# `assert ((none : Option String) = none ∧ (some "other" : Option String) ≠ none)`
# and claimed it showed the precondition holds at the F2P corner. It did not: that
# conjunction is a CLOSED tautology about `Option` literals that mentions neither
# `storeHandle` nor `targetDb` nor the obligation. Measured — appended verbatim as
# a standalone `example ... := by simp` against the frozen solution it elaborates
# on its own (EXIT 0), so it discharges regardless of what the `require` says and
# would keep discharging under an UNSATISFIABLE precondition. That is precisely
# the PRECOND-TOO-STRONG direction the lane exists to detect, so the case attested
# nothing. (Its liveness — a false conjunct leaves an unsolved goal — was real but
# is not the property at issue: a live channel carrying a spec-blind claim is
# still spec-blind.)
#
# The analogue on a total carrier is the obligation being UNSATISFIABLE at an
# F2P-shaped input, which is tested by discharging it AT that concrete input. So
# this case proves, by evaluation, that the modeled operation's post-image at the
# regression input (load a freshly built record, handle `none`, into the
# non-default database "other") is exactly the pair the two `ensures` clauses
# demand — `(naturalKeyVia (some "other"), some "other")`. If the precondition or
# the post-image were unsatisfiable at that corner the `have` could not close.
# `adm_real` additionally pins the transition as non-degenerate (the association
# is a real state change, not a no-op) at that same input.
#
# It goes in the PROOF body rather than the impl region because an in-region
# `assert` emits an `assertGadget` that blocks the very evaluation the `have`
# needs: the combined form leaves the unsolved goal
# `(NonDetT.run do assertGadget (True ∧ some "other" ≠ none); NonDetT.pure ...)
#  = DivM.res (naturalKeyVia (some "other"), some "other")` (EXIT 1, measured).
# The tactic body is elided from the consumer spec view, so `same_spec` holds; the
# obligation header survives and `loom_solve` still closes it verbatim, so this
# remains a genuine `expect="verify"` of the frozen spec (variant_scope: clean).
# =====================================================================
_ADMISS_PROOF = (
    "  have adm_f2p :\n"
    "      (naturalKeyForLoadedRecord \"other\" none).run\n"
    "        = DivM.res (naturalKeyVia (some \"other\"), some \"other\") := by\n"
    "    simp only [naturalKeyForLoadedRecord, NonDetT.run, pure]\n"
    "  have adm_real : (some \"other\" : Option String) ≠ none := by simp\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG on the SHAPE of
    # the impl. Each keeps the byte-identical two-clause obligation and the
    # frozen `loom_solve` script; only the executable surface is reshaped. Both
    # verified out-of-band with real builds (EXIT 0).
    # =====================================================================
    {
        "id": "pos-control-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_INLINE),
        "rationale": "structurally different CORRECT impl: associate the handle, "
                     "then derive the key DIRECTLY from `storeHandle` in the return "
                     "(no intermediate `let key`). The order is unchanged "
                     "(associate-then-derive), so `storeHandle = some targetDb` (1) "
                     "and `key = naturalKeyVia (some targetDb)` (2) both still "
                     "discharge under the frozen `loom_solve`. If a faithful correct "
                     "reshape cannot verify => SPEC-TOO-STRONG. Verified "
                     "out-of-band (EXIT 0).",
    },
    {
        "id": "pos-control-explicit-target",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_EXPLICIT),
        "rationale": "structurally different CORRECT impl: associate the handle, "
                     "then derive from the LITERAL `some targetDb` rather than "
                     "re-reading the (now byte-equal) handle. Definitionally the "
                     "frozen return after the assignment, so both clauses discharge "
                     "under the frozen `loom_solve`. A second reshape of a different "
                     "shape (constant derivation argument). If it FAILS => "
                     "SPEC-TOO-STRONG. Verified out-of-band (EXIT 0).",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation discharged BY EVALUATION at exactly the
    # F2P-shaped input, as a `have`, before the frozen obligation is closed
    # verbatim. REPAIRED by an independent audit: the previous version's
    # in-region assert was a CLOSED tautology about `Option` literals that
    # elaborates standalone against the frozen solution (EXIT 0, measured), so it
    # discharged independently of the `require` and would survive an
    # UNSATISFIABLE precondition — attesting nothing in the one direction this
    # lane detects. See the `_ADMISS_PROOF` comment for the full measurement.
    # MUST verify, else PRECOND-TOO-STRONG at the point that matters.
    # =====================================================================
    {
        "id": "admiss-fresh-handle-real-transition",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof(_ADMISS_PROOF),
        "rationale": "the modeled behaviour is ADMISSIBLE and non-degenerate at the "
                     "F2P corner, shown by discharging the obligation at that "
                     "CONCRETE input rather than by asserting a truth about it. "
                     "`adm_f2p` evaluates the operation at the regression scenario — "
                     "a freshly built record (handle `none`, so the `require` is "
                     "satisfied) loaded into the non-default database \"other\" — and "
                     "proves its post-image is EXACTLY the pair both `ensures` "
                     "clauses demand, `(naturalKeyVia (some \"other\"), some "
                     "\"other\")`. Were the precondition or the post-image "
                     "unsatisfiable at that corner the `have` could not close, which "
                     "is the PRECOND-TOO-STRONG signal. `adm_real` pins the "
                     "transition as a REAL state change at the same input (not a "
                     "no-op). Only the tactic body changes — elided from the spec "
                     "view — so the obligation header survives and `loom_solve` "
                     "still closes the frozen clauses verbatim. Verified with a real "
                     "build (EXIT 0), and LIVE: falsifying the post-image to "
                     "`(naturalKeyVia (some \"other\"), none)` leaves an unsolved "
                     "goal (EXIT 1). It sits in the proof body because an in-region "
                     "`assert` emits an `assertGadget` that blocks the evaluation "
                     "the `have` needs (measured, EXIT 1).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. The seven rivals attack
    # BOTH clauses — (1) by unrouted / wrong-db / partial / mangled-alias /
    # skip-assoc-keep-assert, (2) by the order bug and by mangled-key-argument
    # (a NON-`none` input-derived wrong derivation argument) — and drive the sole
    # binder `targetDb` over SEVEN distinct values.
    # =====================================================================
    {
        "id": "weak-unrouted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNROUTED),
        "refinement": "this IS the pre-patch behaviour: the freshly built record is "
                      "never associated with the target database before its natural "
                      "key is derived, so reference-following during the derivation "
                      "resolves against the default database. On the failing "
                      "scenario the related row exists only in the non-default "
                      "target database, so following the reference against the "
                      "default database finds no row and the load fails — exactly "
                      "the reported error. The un-patched code does NOT resolve.",
        "rationale": "REJECT from BOTH clauses; witnessed on clause (1) "
                     "`storeHandle = some targetDb`: the handle is left at its "
                     "incoming `none`, so the run's state part is `none` ≠ "
                     "`some \"beta\"`, a decidable clash on the transparent handle "
                     "component (no conditioning). (Clause (2) also fails — the key "
                     "is `naturalKeyVia none` — but clause 1 alone refutes.) If it "
                     "VERIFIES the spec admits the pre-patch bug => SPEC-TOO-WEAK. "
                     "Refuted at targetDb = \"beta\"; witness ELABORATES against the "
                     "rival (EXIT 0) and FAILS on gold (EXIT 1).",
        "witness":
            'example :\n'
            '    (naturalKeyForLoadedRecord "beta" none).run\n'
            '      ≠ DivM.res (naturalKeyVia (some "beta"), some "beta") := by\n'
            '  simp only [naturalKeyForLoadedRecord, NonDetT.run, pure]\n'
            '  intro heq\n'
            '  injection heq with h1\n'
            '  injection h1 with hk hs\n'
            '  exact absurd hs (by simp)\n',
    },
    {
        "id": "weak-wrong-database",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_DB),
        "refinement": "associates the record with a DIFFERENT database than the "
                      "target (a miscomputed handle). Reference-following during the "
                      "derivation then resolves against the wrong database, which on "
                      "the failing scenario lacks the related row, so the load fails "
                      "exactly as the bug. A real patch that set the handle to the "
                      "wrong alias would NOT resolve.",
        "rationale": "REJECT from clause (1) `storeHandle = some targetDb`: the "
                     "handle is set to `some \"wrongdb\"`, which is decidably ≠ "
                     "`some targetDb` whenever targetDb ≠ \"wrongdb\". Refuted at "
                     "targetDb = \"alpha\": the run's state part is `some \"wrongdb\"` "
                     "≠ `some \"alpha\"`, a transparent clash (no conditioning). "
                     "Gold's run gives `some \"alpha\"`, so the witness fails on gold. "
                     "If it VERIFIES => SPEC-TOO-WEAK (the handle unpinned). Witness "
                     "seen to discriminate (rival EXIT 0, gold EXIT 1).",
        "witness":
            'example :\n'
            '    (naturalKeyForLoadedRecord "alpha" none).run\n'
            '      ≠ DivM.res (naturalKeyVia (some "alpha"), some "alpha") := by\n'
            '  simp only [naturalKeyForLoadedRecord, NonDetT.run, pure]\n'
            '  intro heq\n'
            '  injection heq with h1\n'
            '  injection h1 with hk hs\n'
            '  exact absurd hs (by simp)\n',
    },
    {
        "id": "weak-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL),
        "refinement": "a partial fix that associates the record with the target "
                      "database only on a SUB-DOMAIN (here when the target is one "
                      "particular database) and leaves it unassociated otherwise — "
                      "modelling a patch that guarded the association behind a "
                      "predicate on the target alias that does not always hold. On a "
                      "target outside the guarded set the record stays unassociated "
                      "and the derivation resolves against the default database, "
                      "raising the same failure. Correct on part of the domain, "
                      "wrong on the rest; it does NOT resolve for the skipped "
                      "sub-domain.",
        "rationale": "REJECT from clause (1) `storeHandle = some targetDb` on the "
                     "targetDb ≠ \"other\" sub-domain: the else branch leaves the "
                     "handle `none`. Refuted at targetDb = \"default\" (outside the "
                     "guarded set): the run's state part is `none` ≠ `some "
                     "\"default\"`, a transparent clash after reducing the `if` by "
                     "`if_neg (\"default\" ≠ \"other\")`. Gold's run associates for "
                     "every target, so the witness fails on gold. Partial-domain "
                     "divergence the unconditional pin (1) catches; if it VERIFIES "
                     "=> SPEC-TOO-WEAK. Witness seen to discriminate (rival EXIT 0, "
                     "gold EXIT 1).",
        "witness":
            'example :\n'
            '    (naturalKeyForLoadedRecord "default" none).run\n'
            '      ≠ DivM.res (naturalKeyVia (some "default"), some "default") := by\n'
            '  simp only [naturalKeyForLoadedRecord, NonDetT.run, pure,\n'
            '    if_neg (by decide : ¬ ("default" = "other"))]\n'
            '  intro heq\n'
            '  injection heq with h1\n'
            '  injection h1 with hk hs\n'
            '  exact absurd hs (by simp)\n',
    },
    {
        "id": "weak-order-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ORDER_BUG),
        "refinement": "THE order bug: derive the natural key from the store handle "
                      "while it is still UNSET, THEN associate. The handle ends up "
                      "correct, but the key was derived before the association, so "
                      "reference-following resolved against the default database — "
                      "on the failing scenario the related row is absent there and "
                      "the derivation fails. This is the exact ordering the fix "
                      "corrects (associate FIRST, derive AFTER); a patch that "
                      "reversed the order would NOT resolve. It is the load-bearing "
                      "clause the change pins (the G-DIFF discriminator).",
        "rationale": "REJECT from clause (2) `key = naturalKeyVia (some targetDb)`: "
                     "the rival returns `naturalKeyVia none` (the derivation at the "
                     "pre-association handle), while the spec pins the derivation at "
                     "`some targetDb`. The RHS is OPAQUE, so the refutation is "
                     "CONDITIONED on the satisfiable single hypothesis "
                     "`naturalKeyVia none ≠ naturalKeyVia (some \"gamma\")` (the F2P "
                     "sub-domain where the derivation genuinely differs between the "
                     "default and target databases — the related row present in one "
                     "and absent from the other). Under that hypothesis the rival's "
                     "key differs from the required one; gold's run returns "
                     "`naturalKeyVia (some \"gamma\")` and cannot meet the "
                     "disequality. The handle clause (1) is kept correct so the ONLY "
                     "failing clause is the key. Refuted at targetDb = \"gamma\". "
                     "Witness seen to discriminate (rival EXIT 0, gold EXIT 1); the "
                     "lone hypothesis is satisfiable (an arbitrary free function may "
                     "differ at two arguments), so no `False` is derivable from it.",
        "witness":
            'example (h : naturalKeyVia none ≠ naturalKeyVia (some "gamma")) :\n'
            '    (naturalKeyForLoadedRecord "gamma" none).run\n'
            '      ≠ DivM.res (naturalKeyVia (some "gamma"), some "gamma") := by\n'
            '  simp only [naturalKeyForLoadedRecord, NonDetT.run, pure]\n'
            '  intro heq\n'
            '  injection heq with h1\n'
            '  injection h1 with hk hs\n'
            '  exact h hk\n',
    },
    {
        "id": "weak-mangled-alias",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_MANGLED_ALIAS),
        "refinement": "associates the record with an alias DERIVED from the target but "
                      "not equal to it (a miscomputed alias — the target with a suffix "
                      "appended). Reference-following during the derivation then "
                      "resolves against a database that is not the one the record is "
                      "being loaded into; on the failing scenario that database lacks "
                      "the related record, so the load fails exactly as the bug. Unlike "
                      "a wrong CONSTANT alias, this is wrong at EVERY target (no "
                      "coincidence sub-domain), so it models a patch whose alias "
                      "computation is systematically off. It does NOT resolve.",
        "rationale": "REJECT from clause (1) `storeHandle = some targetDb`: the handle "
                     "is set to `some (targetDb ++ \"-x\")`, which differs from `some "
                     "targetDb` for EVERY targetDb (appending a non-empty suffix cannot "
                     "return the same string). This is strictly stronger than the "
                     "constant-alias rival, whose wrongness has a one-point escape "
                     "(targetDb = \"wrongdb\"): here the input-DERIVED handle is wrong "
                     "on the whole domain, so no precondition or sub-domain could "
                     "rescue it. Refuted at targetDb = \"epsilon\": the run's state part "
                     "is `some \"epsilon-x\"` ≠ `some \"epsilon\"`, a transparent clash "
                     "(no conditioning). Gold's run gives `some \"epsilon\"`, so the "
                     "witness fails on gold with reflexive hypotheses and an unprovable "
                     "`False`. If it VERIFIES => SPEC-TOO-WEAK (the handle unpinned "
                     "against input-derived miscomputation). Witness seen to "
                     "discriminate (rival EXIT 0, gold EXIT 1).",
        "witness":
            'example :\n'
            '    (naturalKeyForLoadedRecord "epsilon" none).run\n'
            '      ≠ DivM.res (naturalKeyVia (some "epsilon"), some "epsilon") := by\n'
            '  simp only [naturalKeyForLoadedRecord, NonDetT.run, pure]\n'
            '  intro heq\n'
            '  injection heq with h1\n'
            '  injection h1 with hk hs\n'
            '  exact absurd hs (by simp)\n',
    },
    {
        "id": "weak-skip-assoc-keep-assert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SKIP_ASSOC_KEEP_ASSERT),
        "refinement": "the near-miss: never associate the record, but carry an in-impl "
                      "proof obligation ABOUT the derivation at the target handle — "
                      "modelling a patch that 'validated' the key against the database "
                      "it meant to load into while never actually associating the "
                      "record with it. The obligation is satisfiable (it is a truth "
                      "about the target-handle derivation), so a reader might take it "
                      "for the fix; but the record's own handle is untouched, so the "
                      "real reference-following still resolves against the default "
                      "database and the load fails exactly as the bug. A check over the "
                      "right handle is not the same as associating the record. It does "
                      "NOT resolve.",
        "rationale": "REJECT from clause (1) `storeHandle = some targetDb`: the handle "
                     "is left at its incoming `none`. The in-region assert discharges "
                     "(reflexivity of the target-handle derivation) and is precisely "
                     "what makes this a near-miss rather than a restatement of "
                     "weak-unrouted: an auxiliary obligation over the CORRECT handle is "
                     "present and satisfied, yet establishes nothing about the "
                     "OBSERVABLES the spec pins (the mutated handle and the returned "
                     "key). This confirms the spec observes the handle itself, not an "
                     "in-impl claim about the right database. Refuted at targetDb = "
                     "\"zeta\": the run's state part is `none` ≠ `some \"zeta\"`, a "
                     "transparent clash (no conditioning). If it VERIFIES => "
                     "SPEC-TOO-WEAK (an auxiliary assert could substitute for the "
                     "association). Witness seen to discriminate (rival EXIT 0, gold "
                     "EXIT 1).",
        "witness":
            'example :\n'
            '    (naturalKeyForLoadedRecord "zeta" none).run\n'
            '      ≠ DivM.res (naturalKeyVia (some "zeta"), some "zeta") := by\n'
            '  simp only [naturalKeyForLoadedRecord, NonDetT.run, pure]\n'
            '  intro heq\n'
            '  injection heq with h1\n'
            '  injection h1 with hk hs\n'
            '  exact absurd hs (by simp)\n',
    },
    {
        "id": "weak-mangled-key-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_MANGLED_KEY_ARG),
        "refinement": "associates the record with the target database correctly, but "
                      "derives the natural key as some OTHER database would see it — an "
                      "alias derived from the target but not equal to it. Modelling a "
                      "patch that fixed the record's association yet routed the "
                      "reference-following derivation through a separately (mis)computed "
                      "alias, so the related-record lookup still queries a database that "
                      "is not the one being loaded into. On the failing scenario that "
                      "database lacks the related row, so the load fails exactly as the "
                      "bug even though the record's own association now looks right. It "
                      "does NOT resolve.",
        "rationale": "REJECT from clause (2) `key = naturalKeyVia (some targetDb)` — the "
                     "SECOND clause-2 rival, and the one that shows clause (2) pins its "
                     "derivation argument POSITIVELY rather than merely excluding the "
                     "pre-association `none`. weak-order-bug refutes at the argument "
                     "`none`, which is also what the precondition fixes the incoming "
                     "handle to, so on its own it leaves open the reading that clause (2) "
                     "only forbids the stale handle. Here the handle clause (1) is kept "
                     "EXACTLY correct and the derivation argument is a NON-`none`, "
                     "input-DERIVED wrong alias `some (targetDb ++ \"-x\")` (wrong at "
                     "every input, since appending a non-empty suffix cannot return the "
                     "same string), so clause (2) is the only failing clause and it fails "
                     "at a fresh point in the argument space. The RHS is OPAQUE, so the "
                     "refutation is CONDITIONED on the satisfiable single hypothesis "
                     "`naturalKeyVia (some \"delta-x\") ≠ naturalKeyVia (some \"delta\")` "
                     "— one arbitrary free function at two DIFFERENT arguments, so no "
                     "`False` is derivable from it (consistency probe fails, as required). "
                     "Refuted at targetDb = \"delta\", a SEVENTH distinct binder value. "
                     "If it VERIFIES => SPEC-TOO-WEAK (the derivation argument unpinned "
                     "against input-derived miscomputation). Witness seen to discriminate "
                     "(rival EXIT 0, gold EXIT 1, probe EXIT 1).",
        "witness":
            'example (h : naturalKeyVia (some "delta-x") ≠ naturalKeyVia (some "delta")) :\n'
            '    (naturalKeyForLoadedRecord "delta" none).run\n'
            '      ≠ DivM.res (naturalKeyVia (some "delta"), some "delta") := by\n'
            '  simp only [naturalKeyForLoadedRecord, NonDetT.run, pure]\n'
            '  intro heq\n'
            '  injection heq with h1\n'
            '  injection h1 with hk hs\n'
            '  exact h hk\n',
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 5 uniqueness/partial-domain rivals —
# uniq-unrouted, uniq-default-store, uniq-partial-positive-only,
# uniq-off-by-routing, uniq-skip-assoc-keep-assert; the count read "4" until a
# third audit checked it against the sibling file) plus an empty AXIOM lane. It contracts `build_with_natural_key(target_store,
# default_store, record_store)` over THREE pass-by-value int store ids, pinning
# `Result().routed == target_store` (A2) and a pure `dereference_succeeds` (A3).
# This velvet bundle models the SAME routine at a NARROWER, more faithful
# carrier: the store handle is an `Option String` mutated in place, and the
# natural-key derivation is deferred to the `opaque naturalKeyVia` of that handle
# (so clause 2 pins the ORDER — derive at the associated handle — directly,
# rather than through a pure `dereference_succeeds` predicate over ints). Every
# sibling case is accounted for below.
#
#   sibling case (nagini)         -> here
#   -----------------------------------------------------------------------
#   pos-control-direct            -> pos-control-explicit-target       RE-EXPRESSED
#   pos-control-via-record-store  -> pos-control-inline                RE-EXPRESSED
#   admiss-f2p-shaped-input       -> admiss-fresh-handle-real-transition RE-AIMED
#   uniq-unrouted                 -> weak-unrouted                     PORTED (prepatch)
#   uniq-default-store            -> weak-wrong-database               PORTED
#   uniq-partial-positive-only    -> weak-partial-domain               PORTED
#   uniq-off-by-routing           -> weak-mangled-alias                PORTED
#   uniq-skip-assoc-keep-assert   -> weak-skip-assoc-keep-assert        PORTED
#   (no nagini analogue)          -> weak-order-bug                    ADDED (clause 2 / G-DIFF)
#   (no nagini analogue)          -> weak-mangled-key-argument         ADDED (clause 2, non-`none` arg)
#   AXIOM_TESTS (empty)           -> (none)                            DROPPED (G-AX)
#
# 5 uniqueness ported + 2 added uniqueness + 2 soundness re-expressed + 1
# admissibility re-aimed = 10 velvet cases: 2 soundness verify
# (pos-control-inline, pos-control-explicit-target) + 1 admissibility verify
# (admiss-fresh-handle-real-transition) + 7 uniqueness reject (weak-unrouted,
# weak-wrong-database, weak-partial-domain, weak-order-bug, weak-mangled-alias,
# weak-skip-assoc-keep-assert, weak-mangled-key-argument) = 3 verify + 7 reject.
#
# AUDIT NOTE (both of the last two rows were corrected by an independent audit).
# They previously read FOLDED and N/A respectively, on the reasoning that a
# string alias has no "off-by-one neighbour" and that this carrier has no
# in-impl assertion channel over a wrong handle. Both reasons were re-derived
# with real builds and both were WRONG:
#   * the off-by rival's load-bearing property is an input-DERIVED wrong handle
#     (wrong on the whole domain, unlike a constant, which coincides with the
#     target on a one-point sub-domain). `some (targetDb ++ "-x")` expresses
#     exactly that on a String alias; it is not a duplicate of the constant
#     rival but strictly stronger, and it lands (rival EXIT 0 / gold EXIT 1).
#   * this carrier DOES have an in-region assertion channel (the same one the
#     admissibility case uses), so "assert over the right handle while leaving
#     the record unassociated" is directly expressible and also lands
#     (rival EXIT 0 / gold EXIT 1). Both are now shipped as real cases.
#
# RE-EXPRESSED (soundness x2): the nagini positives build the instance already
#   associated (`ModelInstance(target_store)`) or via the pinned-equal
#   record_store. On this carrier the association is an explicit `mut` assignment,
#   so the faithful reshapes are (a) deriving the key inline from the freshly
#   associated handle (pos-control-inline) and (b) deriving from the literal
#   `some targetDb` after the assignment (pos-control-explicit-target). Both keep
#   the associate-then-derive order and discharge under the frozen `loom_solve`
#   (EXIT 0).
# RE-AIMED (admissibility): the nagini probe injects concrete F2P store ids and
#   asserts the three Requires clauses. Here the single `require storeHandle =
#   none` is probed by DISCHARGING THE OBLIGATION at the F2P input: `adm_f2p`
#   evaluates the operation at (targetDb = "other", handle `none`) and proves its
#   post-image is exactly the pair both `ensures` clauses demand, with `adm_real`
#   pinning the transition non-degenerate there. Establishes PRECOND admissible
#   and the mutation non-degenerate at the point that matters.
#   REPAIRED by a third independent audit. The earlier form asserted
#   `(none : Option String) = none ∧ some "other" ≠ none` in the impl region and
#   claimed that showed the precondition holds. It is a CLOSED tautology over
#   `Option` literals — it names neither `storeHandle` nor `targetDb` nor the
#   obligation — and appended standalone to the frozen solution as
#   `example ... := by simp` it elaborates on its own (EXIT 0, measured). So it
#   discharged no matter what the `require` said, and would have discharged under
#   an unsatisfiable precondition: exactly the PRECOND-TOO-STRONG case the lane
#   exists to catch. Its liveness was real and beside the point.
# PORTED (uniq-unrouted -> weak-unrouted): the pre-patch bug verbatim (never
#   associate; derive at the unset handle). The headline reject; refuted on the
#   transparent handle clause (1). PORTED (uniq-default-store -> weak-wrong-
#   database): associate with the wrong database (a constant) instead of the
#   target; refuted on clause (1). PORTED (uniq-partial-positive-only ->
#   weak-partial-domain): associate only on a sub-domain; refuted on clause (1)
#   at a target outside the guarded set (targetDb = "default" ≠ "other").
# PORTED (uniq-off-by-routing -> weak-mangled-alias): the nagini rival routes to
#   `default_store + 1`, whose point is not the arithmetic but that the wrong
#   handle is DERIVED FROM AN INPUT rather than constant — so it is wrong on the
#   whole domain, where a constant escapes on the one-point sub-domain
#   targetDb = "wrongdb". The String counterpart is `some (targetDb ++ "-x")`
#   (`s ++ "-x" ≠ s` for every `s`); refuted on clause (1) at targetDb =
#   "epsilon". Shipped rather than folded: strictly stronger than the constant
#   rival, not a duplicate of it.
# ADDED (weak-order-bug): clause (2) — the ORDER pin `key = naturalKeyVia (some
#   targetDb)` — is the load-bearing discriminator this bundle adds (the nagini
#   surface pinned routing through an int-valued `dereference_succeeds`, not an
#   order over an opaque derivation). To attack clause (2) directly, the order-bug
#   rival derives the key BEFORE associating; refuted by CONDITIONING on the
#   opaque `naturalKeyVia`. This is the G-DIFF discriminator (the prepatch,
#   Solution_prepatch.lean, is exactly this rival) — a real, load-bearing clause,
#   not fabricated coverage.
# ADDED (weak-mangled-key-argument): a SECOND clause-(2) rival, added by a later
#   independent audit that found clause (2) attacked at only ONE point in the
#   derivation-argument space. weak-order-bug refutes at the argument `none`,
#   which is also the value the `require` fixes the incoming handle to, so on its
#   own it leaves open the reading that clause (2) merely forbids the STALE
#   handle. This rival keeps clause (1) exactly correct and derives at a
#   NON-`none`, input-DERIVED wrong alias `some (targetDb ++ "-x")` (wrong at
#   every input), so clause (2) is the sole failing clause at a fresh argument
#   point — evidence that the clause pins its derivation argument POSITIVELY.
#   Machine-checked: module alone EXIT 1 on exactly
#   `ensures_1: key = naturalKeyVia (some targetDb)`; witness rival EXIT 0,
#   gold EXIT 1 (Application type mismatch showing gold derived at the target
#   handle, so the conditioning hypothesis cannot apply to it), probe EXIT 1.
# PORTED (uniq-skip-assoc-keep-assert -> weak-skip-assoc-keep-assert): the
#   nagini near-miss builds the instance unrouted but asserts dereference-success
#   against the store directly, i.e. it "validates" against the handle it should
#   have used while never associating the record. This carrier DOES have that
#   channel — the in-region `assert (with_name_prefix ...)` the admissibility
#   case already uses — so the shape is directly expressible: assert the (true,
#   discharging) fact `naturalKeyVia (some targetDb) = naturalKeyVia (some
#   targetDb)` and then return the derivation at the UNSET handle. The assert
#   discharges, which is the whole point: an auxiliary obligation over the
#   correct handle establishes nothing about the observables, so clause (1)
#   still refutes it (targetDb = "zeta"). Distinct from weak-unrouted in shape,
#   and it confirms the spec observes the handle rather than an in-impl claim.
# DROPPED (AXIOM_TESTS): the sibling's axiom lane is already empty; the velvet
#   bundle declares a single `opaque` free function with no asserted contract to
#   validate (mapping.md §3, G-AX skip). The gate ignores AXIOM_TESTS regardless.
# VACUOUS (frame/permission-mutation): the nagini sibling notes FRAME-MUTATION is
#   N/A even there (all inputs pass-by-value int; the only object, the result, is
#   constructed inside the impl). On this referentially-transparent backend it is
#   vacuous a fortiori: `storeHandle` is a `mut` VALUE binder with no heap
#   footprint, no aliasing, no fractional permissions — no read-only field to
#   overwrite and no substitute probe. Not fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
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
# COVERAGE. The sole obligation (`prove_correct naturalKeyForLoadedRecord`) is
# DEFENDED (two soundness positives + the admissibility case) and ATTACKED (seven
# reject rivals). BOTH independent top-level clauses are attacked: clause (1)
# `storeHandle = some targetDb` by weak-unrouted (handle none), weak-wrong-database
# (handle a wrong CONSTANT), weak-mangled-alias (handle an input-DERIVED wrong
# alias, wrong on the whole domain), weak-partial-domain (handle none on a
# sub-domain), and weak-skip-assoc-keep-assert (handle none despite a discharging
# in-impl claim about the right handle); clause (2) `key = naturalKeyVia (some
# targetDb)` by weak-order-bug (key derived at the pre-association `none` handle)
# and weak-mangled-key-argument (key derived at a NON-`none`, input-DERIVED wrong
# handle while clause 1 stays exactly correct) — both refuted by conditioning on
# the opaque derivation, and together they pin the derivation argument positively
# rather than only excluding the stale handle. The sole free input binder
# `targetDb` is VARIED across SEVEN distinct values — "beta" (unrouted), "alpha"
# (wrong-database), "default" (partial-domain), "gamma" (order-bug), "epsilon"
# (mangled-alias), "zeta" (skip-assoc-keep-assert), "delta"
# (mangled-key-argument). `storeHandle` is pinned to `none` by the `require`,
# which is the precondition and not a coverage gap. The reject lane is NON-EMPTY,
# so SPEC-TOO-WEAK is detectable.
#
# PER-CLAUSE ATTRIBUTION (measured, second independent audit). Each rival's module
# was built alone and its FAILING GOAL read, to confirm the rejection is the clause
# the rationale names rather than a tactic mismatch: weak-unrouted and
# weak-skip-assoc-keep-assert fail BOTH `ensures_1`/`ensures_2` on
# `naturalKeyVia storeHandleOld = naturalKeyVia (some targetDb)` and
# `storeHandleOld = some targetDb`; weak-wrong-database on `some "wrongdb" =
# some targetDb`; weak-mangled-alias on `some (targetDb ++ "-x") = some targetDb`;
# weak-partial-domain on `none = some targetDb` under `if_neg : ¬targetDb =
# "other"` (clause 1 only, as claimed); weak-order-bug and
# weak-mangled-key-argument on `ensures_1` ONLY (clause 2 in isolation). Every
# rejection is attributable to a named ensures clause.
#
# INDEPENDENT AUDIT (attacks D/E, real builds, all recorded). SPEC-TOO-WEAK probe:
# ten NEW wrong impls beyond the shipped rivals have now been checked and ALL were
# rejected — derive at a literal `none` while the handle is set correctly (EXIT 1);
# return a constant `[]` key (EXIT 1); the two rivals shipped by the first audit;
# and, from the second audit, a non-`none` input-derived wrong derivation argument
# (EXIT 1, now shipped as weak-mangled-key-argument), a constant non-`none` wrong
# derivation argument `some "wrongdb"` (EXIT 1), the order bug reshaped as a
# let-bound STALE COPY of the pre-state handle (EXIT 1), and a clause-(2) PARTIAL
# rival correct on `targetDb = "other"` and deriving at `none` elsewhere (EXIT 1,
# failing under `if_neg`). No wrong impl was found that the frozen spec admits.
# SPEC-TOO-STRONG probe: seven NEW correct reshapes, all accepted — assign a
# scratch alias then overwrite with the target; derive from the literal `some
# targetDb` BEFORE the assignment (order-irrelevant when the derivation argument
# is the literal, so still correct); bind the handle through a `let`; branch on the
# precondition `storeHandle = none` with a dead wrong else-branch; a two-armed `if`
# on `targetDb` with BOTH arms correct (EXIT 0); a transient input-derived WRONG
# write corrected before deriving (EXIT 0); and a `match` on the handle with both
# arms correct, which needs a retuned tactic body (see below). So the spec is
# neither too weak nor too strong on the shapes probed.
#
# ONE TOOLING LIMIT, NOT A SPEC HOLE (measured, second audit). A correct reshape
# that destructures the `mut` handle with `match storeHandle with | none => ... |
# some _ => ...` — both arms associating with the target and deriving correctly —
# FAILS under the frozen `loom_solve` with `Failed to parse an assertion without
# names: WPGen (match storeHandleOld with | none => pure (naturalKeyVia (some
# targetDb), some targetDb) | some val => pure (...))`. The error is in weakest-
# precondition GENERATION over a `match` on the mutated binder, not a spec
# rejection: both arms have already reduced to the SAME correct post-image. It is
# the tactic/WPGen surface, and it is in-scope to retune a proof body, so the same
# reshape VERIFIES (EXIT 0) with `intros <;> simp_all <;> loom_solve`. A minimal
# repro is a `match` with identical arms; a `match` on a Bool instead of on the
# handle verifies under the frozen script (EXIT 0). Recorded so the limit is
# visible; NOT shipped as a case, since a positive control whose point is a tactic
# retune tests the script rather than the spec.
#
# ASSERT / HAVE LIVENESS (re-derived independently, third audit, real builds).
# The admissibility case's `adm_f2p` is LIVE and SPEC-ANCHORED: falsifying its
# post-image to `(naturalKeyVia (some "other"), none)` leaves an unsolved goal
# (EXIT 1), and unlike the in-region assert it replaced it cannot be discharged
# without evaluating the operation at the F2P input.
# weak-skip-assoc-keep-assert's `chk` assert is a LIVE channel, not ignored
# decoration: making it false (`naturalKeyVia (some targetDb) = naturalKeyVia
# none`) adds its own unsolved goal `chk_1` ALONGSIDE the clause-(1) failure
# (EXIT 1, re-measured this audit) — so the shipped version's assert genuinely
# discharges while the observables still refute, which is what makes it a
# near-miss. NOTE the `chk` assert is nonetheless a claim about `naturalKeyVia` at
# the target handle, i.e. about the spec's own vocabulary, which is why it models
# a near-miss; the admissibility assert it superficially resembled was a claim
# about `Option` literals only, which is why that one had to go.
#
# THIRD INDEPENDENT AUDIT (attacks A/B/B'/C/D/E/F, real builds).
# A (statement integrity): all 10 modules reconstructed as frozen-prefix +
#   impl-body + frozen-suffix and diffed byte-for-byte; the `require`, both
#   `ensures`, the method header and the `prove_correct` header are identical in
#   every case. No reformatted or weakened statement.
# B (witness re-derivation): all 7 reject witnesses rebuilt on both sides.
#   Every one: rival EXIT 0, gold EXIT 1. The 2 conditioned witnesses' consistency
#   probes both EXIT 1 (hypotheses satisfiable, as required).
# B' (FORGERY test, mandatory for the two `Application type mismatch`
#   signatures — and run on all 7 anyway). Flipping the claim (asserting the
#   post-image EQUALS the run, i.e. that the impl is CORRECT there) inverts every
#   case exactly: gold EXIT 0, rival EXIT 1. So gold's exit code tracks the CLAIM,
#   not the file. Type-revealing probes (`exact (hk : Nat)`) print the hypothesis's
#   real type per side and confirm the two mismatch signatures are semantic:
#   weak-order-bug gold `naturalKeyVia (some "gamma") = naturalKeyVia (some
#   "gamma")` vs rival `naturalKeyVia none = naturalKeyVia (some "gamma")`;
#   weak-mangled-key-argument gold `naturalKeyVia (some "delta") = naturalKeyVia
#   (some "delta")` vs rival `naturalKeyVia (some ("delta" ++ "-x")) =
#   naturalKeyVia (some "delta")`. Gold's is reflexive — it derived at the target
#   handle — and the rival's is not. Genuine refutations, not tactic mismatches.
# C (rival wrongness): the flip builds settle it mechanically. For each rival the
#   post-image equation HOLDS of gold (EXIT 0) and FAILS of the rival (EXIT 1), so
#   every rival is observably distinct from the frozen impl on this carrier. No
#   vacuous case to drop.
# D (SPEC-TOO-WEAK): nine further NEW wrong impls, ALL rejected (EXIT 1) — key
#   derived at the literal target while the handle is never set; a constant
#   non-`none` wrong derivation argument `some "otherdb"`; associate correctly then
#   RESET the handle to `none` before returning; derivation at `some ""`; handle
#   set to `some (targetDb ++ targetDb)`; derivation at the literal `none`; a
#   clause-2 partial correct only on `targetDb = "other"`; a constant `[]` key; and
#   a "compensating" pair (handle mangled, key at the true target). No wrong impl
#   the frozen spec admits was found.
# E (SPEC-TOO-STRONG): six further NEW correct reshapes, ALL verified (EXIT 0) —
#   scratch alias then overwrite; a `let`-bound handle used for both the write and
#   the derivation; derive from the literal BEFORE the assignment; a two-armed `if`
#   with both arms correct; a transient input-derived WRONG write corrected before
#   deriving; and the frozen impl plus a discharging in-region assert naming the
#   post-state. No faithful correct reshape the spec rejects was found.
# F: see the accounting above — every nagini case is mapped, none dropped.
# Coverage reporter's sole finding (`storeHandle` pinned to `none` across all
#   reject witnesses) is forced by `require storeHandle = none`: every admissible
#   input has it `none`, so there is no other value to drive it to. The varied
#   binder `targetDb` takes seven distinct values, and each is a point where that
#   rival's post-image genuinely differs from gold's (established by the flip
#   builds above), so the variation is MEANINGFUL and not two spellings of one
#   point.
AXIOM_TESTS = []

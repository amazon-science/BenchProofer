"""properties.py — G-PBT falsification battery for django__django-11206 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_formatNumber`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models a spelled-out ``format_small(coeff, exponent, decimal_pos) ->
Optional[List[int]]`` core: it materialises the collapsed value's code-point list
element-by-element and pins BOTH the smallness DECISION (P1/P2) and the exact
zero RENDERING (P4, the ``[48,46]+zeros`` list). This Lean bundle models the SAME
fix — "a magnitude below the smallest representable unit at the requested
precision is rendered exactly as zero" — but over a NARROWER carrier: the value
is a ``ℚ`` and the whole rendering procedure is delegated to an ``opaque
renderDecimal`` callee. So the only modeled behavior is the SMALLNESS ADJUSTMENT
``snapValue`` — which ℚ value is handed to the renderer — and the postcondition
is the single clause

    result = renderDecimal (snapValue number decimalPos) decimalSep decimalPos
               grouping thousandSep forceGrouping useL10n.

Consequence for the port (see the accounting block at the bottom): the nagini
smallness-decision rivals (non-strict cutoff, no threshold floor, over-collapse,
never-collapse) ALL carry over as attacks on ``snapValue``; the nagini RENDERING
rivals (dp==0 stray separator, extra leading zero) carry over only PARTIALLY —
their specific digit-shape defects live inside the opaque callee and have no
counterpart, but the clause still pins that the result IS a rendering, so the
coarsest rendering defect is expressible and is carried
(``rival-fabricate-zero-string``). That is carrier narrowing, recorded, not a
dropped-because-hard case.

DEFENDED SURFACE (one modeled behavior, one top-level clause, but a two-armed
carrier). ``snapValue number decimalPos`` is:

  * (none arm)  ``decimalPos = none``  → ``number`` unchanged (no precision
    requested, so no smallness adjustment ever fires);
  * (some arm)  ``decimalPos = some d`` → ``0`` when ``|number| < cutoffOf d``,
    else ``number``; where ``cutoffOf d = 1 / 10 ^ (max d 1)`` is the smallest
    magnitude that still affects a visible place — the ``max d 1`` floor is the
    load-bearing detail (requesting zero places still uses the tenths threshold).

The postcondition then feeds ``snapValue …`` to ``renderDecimal``. Because
``renderDecimal`` is opaque, a rival that hands it the WRONG ℚ is refutable
without knowing what the renderer computes: whenever the rival's snapped value
differs from gold's, ``renderDecimal wrong … ≠ renderDecimal gold …`` is exactly
the sub-domain where the rival is wrong (see WITNESSES).

AUDIT NOTE (witness discrimination points re-derived). An earlier revision of two
reject cases stated its refutation at a ℚ pair the SPEC separates but the real
rendering procedure does NOT — a point where the rival's snapped value differs
from gold's yet both render to the SAME string. Such a witness still clears the
gate (the carrier is opaque, so ``renderDecimal a … ≠ renderDecimal b …`` is
satisfiable as a hypothesis for any distinct ``a``/``b``, and the consistency
probe cannot refute it), but it names a sub-domain on which the rival is not
OBSERVABLY wrong, so its refutation attests to less than the case claims. Both
were re-pointed at inputs where the rendering procedure genuinely separates the
two snapped values (see the per-case notes on ``rival-no-threshold-floor`` and
``rival-never-collapse``). Every reject witness in this battery is checked with
three real builds: it
ELABORATES against its rival, FAILS on the frozen solution by a SEMANTIC type
mismatch (the residual goal reduces to a self-inequality gold cannot satisfy, not
a missing identifier and not a stuck reduction), and its consistency probe fails
to derive ``False``.

BINDER STRUCTURE. The spec predicate has EIGHT binders; the load-bearing INPUT
binders for the modeled behavior are ``number`` (the magnitude) and
``decimalPos`` (present/absent + the precision ``d`` that sets the cutoff). The
five presentation binders (``decimalSep``, ``grouping``, ``thousandSep``,
``forceGrouping``, ``useL10n``) are pure pass-throughs to the opaque renderer —
the fix never inspects them — but the reject witnesses still VARY all five so no
position is pinned to a single value across the battery. ``number`` ranges over
{1/100, 1/2, 5, 1/100000, 1/10^200}, ``decimalPos`` over {none, some 0, some 2,
some 3}, so the some/none fork and several precisions are all exercised
(``pts`` distinct input tuples, one per reject case).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling already records
    this class as N/A: its three parameters are ``int`` (by value) and the only
    ``Acc`` is on the freshly built result. On this referentially transparent
    carrier it is doubly vacuous — ``number``/``decimalPos``/… are immutable
    values, there is no aliasing and no read-only cell to overwrite. No
    substitute probe is fabricated (porting map: vacuous here).

  * CONTROL-FLOW-EFFECT / capability token — VACUOUS. The nagini sibling records
    it N/A (the only fork is produce-a-rendering vs return-None, fully visible to
    the value abstraction). Here there is no ``Option`` return and no
    side-effect at all — the result is a single ``String`` fully pinned to the
    inputs. Nothing to model.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the
    inputs: ``result = renderDecimal (snapValue number decimalPos) …`` where
    ``snapValue`` is a spelled-out function of the inputs. There is no opaque
    ANSWER KEY an impl could echo — ``renderDecimal`` is applied to a value the
    impl must itself compute correctly, so producing the right string IS doing
    the snap. In its place the battery carries honest cheapest-impl POSITIVE
    CONTROLS that must verify (ports nagini's ``pos-control-grounded-guard``).

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_formatNumber``
    is a total Lean ``def``; a diverging implementation cannot be written at all,
    so there is no ``diverge-*`` rival to port (the nagini sibling carries none
    either).

  * PARTIAL-DOMAIN on the smallness decision — APPLIES. This is the real attack
    surface and the whole nagini uniqueness lane lands here: the strict-vs-non-
    strict cutoff edge, the ``max d 1`` threshold floor, the
    always-collapse and never-collapse forks, plus one attack the nagini rivals
    could not express (the ``none`` arm — nagini has no ``decimal_pos is None``
    row because its ``format_small`` is only reached with a precision).

WITNESSES — conditioning on the opaque carrier. On a tactic-proof backend "did
not verify" is the DEFAULT outcome of reshaping an implementation (the frozen
``cases decimalPos … rfl`` proof is tuned to the frozen form), so a rejection
alone attributes nothing to the spec. Every ``expect="reject"`` case therefore
carries a Lean snippet that refutes the spec at one concrete input. Because
``renderDecimal`` is opaque there is no VALUE to compute, so each witness
CONDITIONS on the carrier with a single hypothesis
``renderDecimal <rival-value> … ≠ renderDecimal <gold-value> …`` and derives the
contradiction from it. The hypothesis is satisfiable (one assumption about
``renderDecimal`` at two distinct argument tuples — never two assumptions about
the same term, so the gate's consistency probe cannot derive ``False``), and it
holds precisely on the sub-domain where the rival is wrong: whenever the renderer
distinguishes the two snapped values, the rival's string differs from the spec's.
Each witness was checked with two real ``lake env lean`` builds — it ELABORATES
against its rival and FAILS on the frozen solution — so it discriminates rather
than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
real formatting routine whose smallness guard is subtly wrong (non-strict
compare, missing threshold floor, unconditional or absent replacement), so on
the F2P
decimal rows (``1e-200`` @ dp=2 must render ``0.00``; ``1e-8`` @ dp=8 must render
``0.00000001``; a huge magnitude must NOT collapse) the emitted string mismatches
the expected fixture — so the faithful patch would NOT resolve.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` re-run the A-reference soundness
of the deep models; on lean the axiom lane is G-AX's job and this gate ignores
``AXIOM_TESTS``. This bundle consumes no ``axiom`` (``renderDecimal`` is declared
``opaque`` and the proof uses no property of it), so there is nothing to probe.
"""
from pathlib import Path

INSTANCE = "django__django-11206"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The whole smallness-adjustment block of the impl loop (the `match` that snaps
# `n` to 0 when a precision is requested and the magnitude is below the cutoff).
# Replaced wholesale by the collapse-fork rivals + positive controls.
_MATCH_BLOCK = """  match decimalPos with
  | some d =>
      let cutoff := cutoffOf d
      if |n| < cutoff then
        n := 0
  | none => pure ()"""

# The strict magnitude comparison (the cutoff edge) — for the non-strict rival.
_STRICT = "      if |n| < cutoff then"

# The cutoff computation, WITH the `max d 1` floor via `cutoffOf` — for the
# no-floor rival (which recomputes the cutoff as 1/10^d, dropping the floor).
_CUTOFF = "      let cutoff := cutoffOf d"

# The renderer CALL SITE — the eight-argument application whose ℚ position the
# collapse rivals attack. Named separately so a rival can corrupt one of the seven
# NON-ℚ positions instead (the pass-through-precision rival below).
_CALL = "  return renderDecimal n decimalSep decimalPos grouping thousandSep"

# The full impl body — for the grounded-guard positive (call `snapValue` directly).
_IMPL_BODY = """  let mut n := number
  match decimalPos with
  | some d =>
      let cutoff := cutoffOf d
      if |n| < cutoff then
        n := 0
  | none => pure ()
  return renderDecimal n decimalSep decimalPos grouping thousandSep
    forceGrouping useL10n"""

# The full proof body — re-proved (to `rfl`) by the grounded-guard positive,
# whose impl is definitionally the spec's RHS. Lies wholly inside the proof
# region, so same_spec holds and the theorem STATEMENT stays byte-identical.
_PROOF_BODY = """  intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
  unfold problem_spec_formatNumber implementation_formatNumber snapValue
  cases decimalPos with
  | none => rfl
  | some d =>
      simp only [Id.run, bind, pure]
      by_cases h : |number| < cutoffOf d
      · simp only [h, if_true]
      · simp only [h, if_false]"""

# The frozen proof's intro line — for the admissibility positive to prepend a
# ground `have` without touching the theorem STATEMENT or the spec view.
_INTRO = "  intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n"


# ---------------------------------------------------------------------------
# witness scaffold. Conditions on the opaque renderer: ONE hypothesis that it
# separates the rival's snapped value from gold's, then reduces the spec at a
# concrete input and closes by that hypothesis. `simp only [Id.run]` collapses
# the `Id.run do` wrapper; `norm_num [cutoffOf]` decides the concrete magnitude
# comparison (`|number| < cutoffOf d`) that selects the branch; `exact h`
# discharges the residual `¬ pure (renderDecimal rival …) = renderDecimal gold …`
# (`pure` is defeq to identity in `Id`). For the `none`-arm rival no cutoff
# comparison arises, so `norm_num` is omitted.
#
# `rival_dp` overrides the decimalPos the RIVAL side of the hypothesis is applied
# at. The collapse rivals all mis-compute the ℚ argument and pass the other seven
# positions through, so for them the two renderer applications differ only in the
# ℚ slot and the default (same decimalPos on both sides) is right. A rival that
# corrupts a PASS-THROUGH position instead differs from gold in that position and
# NOT in the ℚ one, so its hypothesis has to be stated with the rival's own value
# there — see `rival-passthrough-precision`.
# ---------------------------------------------------------------------------
def _w(number, decimalPos, sep, grp, tsep, fg, l10n, rival_val, gold_val,
       *, needs_cutoff=True, rival_dp=None):
    args = f'{number} {sep} {decimalPos} {grp} {tsep} {fg} {l10n}'
    tail = "  norm_num [cutoffOf]\n" if needs_cutoff else ""
    rdp = rival_dp if rival_dp is not None else decimalPos
    return (
        f"example (h : renderDecimal {rival_val} {sep} {rdp} {grp} "
        f"{tsep} {fg} {l10n}\n"
        f"             ≠ renderDecimal {gold_val} {sep} {decimalPos} {grp} "
        f"{tsep} {fg} {l10n}) :\n"
        f"    ¬ problem_spec_formatNumber {args}\n"
        f"        (implementation_formatNumber {args}) := by\n"
        "  unfold problem_spec_formatNumber implementation_formatNumber snapValue\n"
        "  simp only [Id.run]\n"
        f"{tail}"
        "  exact h\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_formatNumber` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-control-grounded-guard",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest CORRECT impl of the modeled behavior: hand `renderDecimal` the
        # pure `snapValue number decimalPos` directly, instead of recomputing the
        # snap with a local `mut` + `match` + `if`. Definitionally the spec's RHS,
        # so the proof re-proves to `rfl`. Ports nagini's
        # pos-control-grounded-guard: there `is_small = below_cutoff(...)` uses the
        # grounded oracle directly; here `snapValue` IS that grounded function and
        # the impl calls it directly. Also the echo-class positive control: the
        # postcondition is grounded, there is no wrong value to echo.
        "module": _swaps(
            _BASE,
            (_IMPL_BODY,
             "  return renderDecimal (snapValue number decimalPos) decimalSep "
             "decimalPos\n    grouping thousandSep forceGrouping useL10n"),
            (_PROOF_BODY,
             "  intro number decimalSep decimalPos grouping thousandSep "
             "forceGrouping useL10n\n  rfl"),
        ),
        "rationale": "the cheapest CORRECT impl computes the snapped value with "
                     "the pure `snapValue` function directly and renders it; it is "
                     "definitionally the postcondition's RHS, so it verifies "
                     "(proof re-proves to `rfl`; statement byte-identical, no new "
                     "axiom/lemma). If it failed => SPEC-TOO-STRONG (over-fit to "
                     "the inline `mut`/`match`/`if` form of the adjustment). Ports "
                     "nagini's pos-control-grounded-guard.",
    },
    {
        "id": "pos-control-reorder-match",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT reshape: reorder the `match` arms
        # (handle `none` first, `some` second) and inline the `let cutoff` into
        # the `if`. Same values on every input, different executable shape. The
        # frozen proof (`cases decimalPos` with `none => rfl`) still closes
        # because the impl reduces identically. Ports nagini's
        # pos-control-reorder-decision.
        "module": _swap(
            _BASE, _MATCH_BLOCK,
            """  match decimalPos with
  | none => pure ()
  | some d =>
      if |n| < cutoffOf d then
        n := 0"""),
        "rationale": "a structurally-different but CORRECT reshape (match arms "
                     "reordered, `cutoff` inlined) computes the SAME snapped value "
                     "on every input, so the single postcondition clause still "
                     "holds; the frozen proof closes unchanged. If it failed => "
                     "SPEC-TOO-STRONG (over-fit to one branch order). Ports "
                     "nagini's pos-control-reorder-decision.",
    },
    {
        "id": "pos-control-two-sided-compare",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT-ADDED positive control. Both pre-existing positives are
        # DEFINITIONALLY EQUAL to the frozen impl: grounded-guard closes by `rfl`
        # and reorder-match reduces identically under the frozen script, so
        # neither one tests whether the spec accepts a correct impl whose
        # BRANCH CONDITION is a different decidable proposition. This one does:
        # it replaces `|n| < cutoffOf d` with the two-sided conjunction
        # `-cutoffOf d < n ∧ n < cutoffOf d`, which is provably equivalent but
        # NOT defeq (a different `Decidable` instance selects the branch), so the
        # proof needs real `abs_lt` bridging in both directions rather than
        # reduction. Verified by build: exit 0.
        "module": _swaps(
            _BASE,
            (_MATCH_BLOCK,
             """  match decimalPos with
  | some d =>
      if -cutoffOf d < n ∧ n < cutoffOf d then
        n := 0
  | none => pure ()"""),
            (_PROOF_BODY,
             """  intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
  unfold problem_spec_formatNumber implementation_formatNumber snapValue
  cases decimalPos with
  | none => rfl
  | some d =>
      simp only [Id.run, bind, pure]
      by_cases h : |number| < cutoffOf d
      · rw [if_pos h, if_pos (abs_lt.mp h)]
      · rw [if_neg h, if_neg (fun hc => h (abs_lt.mpr hc))]"""),
        ),
        "rationale": "a CORRECT impl whose branch condition is a DIFFERENT "
                     "decidable proposition — the two-sided `-cutoffOf d < n ∧ n < "
                     "cutoffOf d` instead of `|n| < cutoffOf d`. Equivalent on every "
                     "input (`abs_lt`), so the single postcondition clause still "
                     "holds, but NOT definitionally equal to the frozen impl: the "
                     "branch is selected by a different `Decidable` instance, so the "
                     "proof must bridge with `abs_lt` in both directions rather than "
                     "reduce. This is the strongest available SPEC-TOO-STRONG "
                     "control: the other two positives are both defeq to the frozen "
                     "impl, so a spec over-fit to the frozen COMPARISON FORM (rather "
                     "than to the branch order or the mut/match syntax) would be "
                     "invisible to them and is caught here. If it failed => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at the real
    # F2P input. Discharge the postcondition at 1e-200 @ dp=2 (the problem-
    # statement magnitude, where the collapse fires) as a ground `have`, then
    # close the frozen obligation verbatim. Nothing is assumed: no new
    # declaration, statement byte-identical, ground instance is a `have`
    # prepended to the existing tactic body. Ports nagini's admiss-f2p-shaped.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # THIRD-AUDIT REPAIR (the ground instance was not pinned to the F2P
        # SUB-DOMAIN). The previous revision's `have` discharged only the
        # postcondition at 1e-200 @ dp=2, and measurement showed that script is
        # INSENSITIVE to which branch of the modeled behavior the point lands in:
        # the byte-identical tactic body also closes at number=5 @ dp=2 (build:
        # exit 0), where the collapse does NOT fire. So it established "the
        # obligation is satisfiable at SOME concrete input" — true, but weaker
        # than the rationale claimed, since the whole point of an F2P-shaped
        # admissibility positive is that the obligation is satisfiable at an
        # input where the FIXED behavior is the one being exercised. Repaired by
        # prepending a second ground `have` that pins the collapse actually
        # firing there — `snapValue (1/10^200) (some 2) = 0` — so the magnitude
        # comparison is decided by the script rather than bypassed. Measured
        # load-bearing: the same `have` shape at an above-cutoff point
        # (`snapValue 5 (some 2) = 0`) FAILS with `unsolved goals ⊢ False`
        # (exit 1), so this arithmetic tracks the sub-domain and is not a
        # tautology that any point would satisfy.
        "module": _swap(
            _BASE, _INTRO,
            "  have _snap : snapValue (1/10^200) (some 2) = 0 := by\n"
            "    unfold snapValue\n"
            "    norm_num [cutoffOf]\n"
            "  have _f2p : problem_spec_formatNumber (1/10^200) \".\" (some 2) 0 "
            "\"\" false none\n"
            "      (implementation_formatNumber (1/10^200) \".\" (some 2) 0 \"\" "
            "false none) := by\n"
            "    unfold problem_spec_formatNumber implementation_formatNumber "
            "snapValue\n"
            "    simp only [Id.run]\n"
            "    norm_num [cutoffOf]\n"
            "    rfl\n"
            + _INTRO),
        "rationale": "the obligation is discharged at the real F2P magnitude "
                     "1e-200 @ decimal_pos=2 by evaluation as a `have`, and the "
                     "collapse is separately pinned to FIRE there (`snapValue "
                     "(1/10^200) (some 2) = 0`, decided by `norm_num [cutoffOf]`) "
                     "so the ground instance lands in the sub-domain the fix "
                     "governs rather than merely at some arbitrary input; then the "
                     "frozen obligation is closed verbatim. Verifies (else the "
                     "modeled behavior would be unsatisfiable at exactly a normal "
                     "F2P input — the analogue of PRECOND-TOO-STRONG). The "
                     "`snapValue … = 0` step is measured load-bearing: the "
                     "identical step at an above-cutoff point (`snapValue 5 "
                     "(some 2) = 0`) fails with `unsolved goals ⊢ False`, so it "
                     "discriminates the collapse sub-domain. Nothing is assumed: "
                     "no new declaration, statement byte-identical. Ports "
                     "nagini's admiss-f2p-shaped.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness that
    # conditions on the opaque renderer to pin the violation at one input.
    # =====================================================================

    # ---- non-strict cutoff edge (attacks the `some` arm's comparison) ----
    {
        "id": "rival-non-strict-cutoff",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse at magnitudes EXACTLY equal to the cutoff too (`≤` instead of
        # `<`). Everything strictly below/above is handled as gold; only the
        # exact-cutoff edge flips.
        "module": _swap(_BASE, _STRICT, "      if |n| ≤ cutoff then"),
        "refinement": "uses a non-strict `abs(number) <= cutoff` guard. The value "
                      "1/100 @ decimal_pos=2 sits EXACTLY at the cutoff "
                      "(cutoffOf 2 = 1/100), so the rival snaps it to 0 and renders "
                      "'0.00' where gold keeps it and renders '0.01'. A faithful "
                      "real patch with `<=` would render the boundary decimal rows "
                      "(the F2P strict-edge cases: '== cutoff: NOT below') as all "
                      "zeros, so it would NOT resolve.",
        "rationale": "REJECT from the postcondition: at |number| = cutoffOf d the "
                     "spec's `snapValue` leaves `number` (strict `<` is false) so "
                     "the result is `renderDecimal number …`, but the rival snaps "
                     "to 0 and renders `renderDecimal 0 …`. Refuted at number=1/100, "
                     "decimalPos=some 2 (magnitude exactly at the cutoff), where "
                     "the two renderer calls differ. If it verified => "
                     "SPEC-TOO-WEAK (non-strict cutoff admitted).",
        "witness": _w("(1/100)", "(some 2)", '"."', "0", '""', "false", "none",
                      "0", "(1/100)"),
        # (presentation binders are parse-safe — no commas/spaces inside string
        #  literals — so the coverage tool reads every witness positionally.)
    },

    # ---- no threshold floor (attacks the `max d 1` floor at dp==0) ----
    {
        "id": "rival-no-threshold-floor",
        "kind": "uniqueness",
        "expect": "reject",
        # Recompute the cutoff as 1/10^d, DROPPING the `max d 1` floor, so at
        # decimalPos=some 0 the cutoff becomes 1/10^0 = 1 instead of the real
        # 1/10 = cutoffOf 0. Values in [1/10, 1) at dp=0 are wrongly collapsed.
        "module": _swap(_BASE, _CUTOFF, "      let cutoff := (1 : ℚ) / 10 ^ d"),
        "refinement": "drops the `max(decimal_pos, 1)` threshold floor, so "
                      "at decimal_pos=0 the cutoff becomes 10**0 = 1 instead of "
                      "the floored 0.1. Every magnitude in "
                      "[0.1, 1) at decimal_pos=0 is then wrongly snapped to zero. "
                      "For a NEGATIVE such magnitude the rendering procedure keeps "
                      "the sign, so the divergence is OBSERVABLE in the emitted "
                      "string: measured against the real rendering procedure, "
                      "(-0.5, decimal_pos=0) renders '-0' under the correct floored "
                      "cutoff and '0' under the floorless one. "
                      "HONEST SCOPE (audit-measured, do not strengthen this): unlike "
                      "the other rivals here, this one is NOT witnessed by the "
                      "shipped test rows. The suite contains exactly one "
                      "decimal_pos=0 row and its magnitude is far below both "
                      "cutoffs, so a faithful floorless patch fails ZERO rows and "
                      "WOULD resolve as scored. Its wrongness is real but "
                      "test-invisible, which is precisely why the spec must pin the "
                      "floor: the clause is what rejects it, not the fixture.",
        # AUDIT REPAIR (witness discrimination). The previous point was
        # number=1/2 @ dp=0: the spec does separate it (gold leaves 1/2, the
        # floorless rival snaps to 0), but the real rendering procedure truncates
        # to zero visible decimals, so BOTH snapped values render to the same
        # string and the rival is not observably wrong there. Re-pointed at
        # number=-(1/2) @ dp=0, still exactly the [0.1,1)-at-dp-0 sub-domain the
        # dropped floor mis-handles, but where the two snapped values DO render
        # differently (the surviving negative keeps its sign, the snapped zero
        # does not). Verified: witness elaborates against the rival (exit 0),
        # fails on the frozen solution by a semantic type mismatch (exit 1), and
        # the consistency probe cannot derive False (exit 1).
        "rationale": "REJECT from the postcondition at decimalPos=some 0: the spec "
                     "uses `cutoffOf 0 = 1/10^(max 0 1) = 1/10`, and |-(1/2)| is "
                     "NOT below it, so `snapValue` leaves the value; the floorless "
                     "rival uses cutoff 1 and snaps to 0. Refuted at "
                     "number=-(1/2), decimalPos=some 0, where `renderDecimal 0 … ≠ "
                     "renderDecimal (-(1/2)) …` — a point at which the rendering "
                     "procedure separates the two snapped values, so the rival is "
                     "observably wrong and not merely reshaped. If it verified => "
                     "SPEC-TOO-WEAK (threshold floor unpinned).",
        "witness": _w("(-(1/2))", "(some 0)", '";"', "3", '"x"', "true",
                      "(some true)", "0", "(-(1/2))"),
    },

    # ---- over-collapse: always snap to 0 when a precision is requested ----
    {
        "id": "rival-over-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # Snap unconditionally in the `some` arm (drop the magnitude guard).
        "module": _swap(
            _BASE, _MATCH_BLOCK,
            """  match decimalPos with
  | some _ =>
      n := 0
  | none => pure ()"""),
        "refinement": "snaps EVERY value to 0 whenever a decimal_pos is given "
                      "(no magnitude guard). A large magnitude like 5 @ "
                      "decimal_pos=2 (which must render '5.00') is wrongly rendered "
                      "'0.00'. A real patch that always replaced the value with "
                      "zero whenever a decimal_pos was supplied would fail "
                      "every ordinary decimal row, NOT resolving.",
        "rationale": "REJECT from the postcondition: for a not-small value the "
                     "spec's `snapValue` leaves `number`, but the rival always "
                     "hands 0 to the renderer. Refuted at number=5, "
                     "decimalPos=some 2 (well above the cutoff), where "
                     "`renderDecimal 0 … ≠ renderDecimal 5 …`. If it verified => "
                     "SPEC-TOO-WEAK (no smallness gate). Ports nagini's "
                     "rival-over-collapse.",
        "witness": _w("5", "(some 2)", '"-"', "1", '"z"', "false", "(some false)",
                      "0", "5"),
    },

    # ---- never-collapse: the documented pre-patch behavior ----
    {
        "id": "rival-never-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # Never snap: the `some` arm is a no-op, so `n` stays `number` always.
        # This is exactly the pre-patch behavior (no smallness guard at all).
        "module": _swap(
            _BASE, _MATCH_BLOCK,
            """  match decimalPos with
  | some _ => pure ()
  | none => pure ()"""),
        "refinement": "never snaps — exactly the pre-patch behavior (the guard is "
                      "absent). A below-window magnitude falls through unchanged "
                      "and is rendered on its own instead of as the all-zeros "
                      "string; on the reported bug magnitude (1e-200 @ dp=2) that "
                      "means the scientific '1.00e-200' instead of '0.00', and on a "
                      "small NEGATIVE below-window value it means a signed zero "
                      "instead of the unsigned one — precisely the defect, so the "
                      "F2P decimal rows stay failing: it would NOT resolve.",
        # AUDIT REPAIR (witness discrimination). The previous point was
        # number=1/100000 @ dp=3: the spec separates it (gold snaps to 0, the
        # rival keeps 1e-5), but the rendering procedure truncates to three
        # visible decimals, so both snapped values render to the same string and
        # the rival is not observably wrong there. Re-pointed at
        # number=-(1/100000) @ dp=3, still squarely inside the below-cutoff
        # sub-domain the missing collapse mis-handles (cutoffOf 3 = 1/1000), but
        # where the two snapped values DO render differently: the unsnapped
        # negative carries a sign the snapped zero does not. Verified: witness
        # elaborates against the rival (exit 0), fails on the frozen solution by a
        # semantic type mismatch (exit 1), consistency probe cannot derive False
        # (exit 1).
        "rationale": "REJECT from the postcondition: for a below-cutoff value the "
                     "spec's `snapValue` returns 0, but the rival hands `number` to "
                     "the renderer. Refuted at number=-(1/100000), "
                     "decimalPos=some 3 (cutoffOf 3 = 1/1000, so the magnitude is "
                     "below it and must snap), where `renderDecimal (-(1/100000)) … "
                     "≠ renderDecimal 0 …` — a point at which the rendering "
                     "procedure separates the two snapped values, so the rival is "
                     "observably wrong and not merely reshaped. If it verified => "
                     "SPEC-TOO-WEAK (the collapse is not demanded). Ports nagini's "
                     "rival-never-collapse.",
        "witness": _w("(-(1/100000))", "(some 3)", '"."', "2", "\"'\"", "true",
                      "none", "(-(1/100000))", "0"),
    },

    # ---- snap on the `none` arm (attacks the "no precision => unchanged" arm) ----
    {
        "id": "rival-snap-when-no-precision",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED rival (see accounting): snap to 0 even when NO precision is
        # requested (`none` arm sets `n := 0`). The `some` arm is correct. This is
        # the only rival exercising the `none` branch of the modeled behavior; the
        # nagini rivals cannot express it (its `format_small` is only reached with
        # a decimal_pos).
        "module": _swap(
            _BASE, _MATCH_BLOCK,
            """  match decimalPos with
  | some d =>
      let cutoff := cutoffOf d
      if |n| < cutoff then
        n := 0
  | none => n := 0"""),
        "refinement": "snaps to 0 even when NO number of decimal places is "
                      "requested (decimal_pos is None). The gold guard runs ONLY "
                      "under `decimal_pos is not None`; a real patch that zeroed "
                      "the value unconditionally would replace every "
                      "no-precision-specified value with '0', failing every "
                      "None-decimal_pos row, NOT resolving.",
        "rationale": "REJECT from the postcondition on the `none` arm: the spec's "
                     "`snapValue number none = number`, but the rival hands 0 to "
                     "the renderer. Refuted at number=5, decimalPos=none, where "
                     "`renderDecimal 0 … ≠ renderDecimal 5 …`. This is the sole "
                     "rival exercising the none arm. If it verified => "
                     "SPEC-TOO-WEAK (the no-precision pass-through unpinned).",
        "witness": _w("5", "none", '"."', "0", '""', "false", "none",
                      "0", "5", needs_cutoff=False),
    },

    # ---- corrupt a PASS-THROUGH position of the renderer call ----
    {
        "id": "rival-passthrough-precision",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED rival (see accounting). The postcondition pins ALL EIGHT
        # arguments of the renderer application, but every other rival in this
        # battery attacks the ℚ position only — the five presentation binders and
        # the `decimalPos` pass-through are varied across the witnesses yet never
        # themselves CORRUPTED, so nothing in the battery demonstrated that the
        # spec pins the requested precision the renderer is handed. This rival
        # snaps correctly and then renders at a CONSTANT precision, ignoring the
        # requested one. It leaves the `snapValue` computation untouched, so it is
        # the only rival whose rejection is attributable to the clause's
        # pass-through structure rather than to the smallness decision.
        "module": _swap(
            _BASE, _CALL,
            "  return renderDecimal n decimalSep (some 2) grouping thousandSep"),
        "refinement": "renders at a hardcoded two visible decimal places instead of "
                      "the requested count, while getting the smallness decision "
                      "exactly right. A real patch that pinned the visible-place "
                      "count to a constant inside the rendering call would emit the "
                      "wrong number of decimals on every row requesting a different "
                      "count — including the eight-place rows and the "
                      "three-place row the reported magnitude lands on — so it would "
                      "NOT resolve.",
        "rationale": "REJECT from the postcondition's pass-through structure: the "
                     "clause requires the renderer be applied to the ORIGINAL "
                     "`decimalPos`, and this rival applies it to a constant. "
                     "Refuted at number=5, decimalPos=some 4 (above the cutoff, so "
                     "`snapValue` leaves 5 and the smallness decision is not at "
                     "issue), where `renderDecimal 5 … (some 2) … ≠ renderDecimal 5 "
                     "… (some 4) …` — the two applications differ in the precision "
                     "position and in nothing else. If it verified => SPEC-TOO-WEAK "
                     "(the requested precision is not pinned through to the "
                     "renderer). Verified: witness elaborates against the rival "
                     "(exit 0), fails on the frozen solution by a semantic type "
                     "mismatch (exit 1), probe cannot derive False (exit 1).",
        "witness": _w("5", "(some 4)", '"."', "0", '""', "false", "none",
                      "5", "5", rival_dp="(some 2)"),
    },

    # ---- corrupt a PRESENTATION pass-through position (the two separators) ----
    {
        "id": "rival-passthrough-separators",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED rival. `rival-passthrough-precision` closed the `decimalPos`
        # pass-through, but the FIVE presentation binders (`decimalSep`,
        # `grouping`, `thousandSep`, `forceGrouping`, `useL10n`) were still only
        # VARIED across witnesses and never CORRUPTED by any variant — and
        # variation is not attack. This rival hands the renderer the two separator
        # arguments in swapped positions, snapping perfectly correctly, so its
        # rejection is attributable purely to the clause pinning WHICH argument
        # goes in WHICH presentation slot.
        "module": _swap(
            _BASE, _CALL,
            "  return renderDecimal n thousandSep decimalPos grouping decimalSep"),
        "refinement": "passes the two separator arguments to the rendering tail in "
                      "swapped positions, while getting the smallness decision "
                      "exactly right. A real patch that transposed them would emit "
                      "the thousands symbol where the decimal symbol belongs on every "
                      "row that supplies distinct separators — verified against the "
                      "real rendering procedure at (number=5, decimal_pos=2, "
                      "decimal_sep='.', thousand_sep=','), which renders '5.00' "
                      "correctly and '5,00' under the swap — so it would NOT resolve.",
        "rationale": "REJECT from the postcondition's pass-through structure: the "
                     "clause requires the renderer be applied to `decimalSep` and "
                     "`thousandSep` in their own positions, and this rival transposes "
                     "them. Refuted at number=5, decimalPos=some 2 (above the cutoff, "
                     "so `snapValue` leaves 5 and the smallness decision is not at "
                     "issue), with decimalSep='.' and thousandSep=',' distinct, where "
                     "`renderDecimal 5 \",\" … \".\" … ≠ renderDecimal 5 \".\" … "
                     "\",\" …`. The hypothesis is TRUE under the real rendering "
                     "procedure ('5,00' vs '5.00'), so the rival is observably wrong "
                     "and not merely reshaped. If it verified => SPEC-TOO-WEAK (the "
                     "presentation arguments are not pinned to their positions). "
                     "Verified with real builds: variant does not verify (exit 1), "
                     "witness elaborates against the rival (exit 0), fails on the "
                     "frozen solution (exit 1), probe cannot derive False (exit 1), "
                     "and the flipped-claim forgery FAILS on gold where the shipped "
                     "witness's `rfl` counterpart SUCCEEDS — so gold's exit code "
                     "tracks the claim.",
        "witness": ('example (h : renderDecimal 5 "," (some 2) 3 "." true none\n'
                    '             ≠ renderDecimal 5 "." (some 2) 3 "," true none) :\n'
                    '    ¬ problem_spec_formatNumber 5 "." (some 2) 3 "," true none\n'
                    '        (implementation_formatNumber 5 "." (some 2) 3 "," true '
                    'none) := by\n'
                    '  unfold problem_spec_formatNumber implementation_formatNumber '
                    'snapValue\n'
                    '  simp only [Id.run]\n'
                    '  norm_num [cutoffOf]\n'
                    '  exact h\n'),
    },

    # ---- bypass the renderer entirely: fabricate the output string ----
    {
        "id": "rival-fabricate-zero-string",
        "kind": "uniqueness",
        "expect": "reject",
        # THIRD-AUDIT-ADDED rival, and the expressible analogue of the two nagini
        # RENDERING cases the port recorded as dropped-for-carrier. The accounting
        # block reasoned that because the rendering is delegated to an opaque
        # callee "there is no list shape for a rival to mis-build", and concluded
        # nothing on the rendering side is attackable here. That conclusion is too
        # strong, and this rival is the counterexample: the postcondition does not
        # merely pin the renderer's ARGUMENTS, it pins that the result IS the
        # renderer applied to them. So a rival can still get the rendering wrong
        # in the one way this carrier can see — by not calling the renderer at all
        # and emitting a literal instead. Every other rival here computes
        # `renderDecimal <something>`; this one returns a constant string, so it is
        # the only case attacking the clause's outermost structure (that the result
        # is a RENDERING) rather than one of the renderer's eight arguments.
        "module": _swap(_BASE, _IMPL_BODY, '  return "0"'),
        "refinement": "hardcodes the collapsed-value output instead of running the "
                      "value through the rendering procedure. A real patch that "
                      "short-circuited to a literal '0' would emit that string for "
                      "every input — no separator, no padding to the requested "
                      "places, no grouping, no sign — so it would fail essentially "
                      "every decimal row including the F2P ones (the reported "
                      "magnitude at decimal_pos=2 must render a zero PADDED to two "
                      "visible places, not the bare digit), and would NOT resolve.",
        "rationale": "REJECT from the postcondition's outermost structure: the "
                     "clause requires `result = renderDecimal (snapValue …) …`, so "
                     "the result must BE the rendering procedure's output, and this "
                     "rival returns a literal. Refuted at number=1/10^200, "
                     "decimalPos=some 2 (the F2P magnitude, below the cutoff, so "
                     "the snap fires and gold's result is `renderDecimal 0 …`), "
                     "where `renderDecimal 0 … ≠ \"0\"` — TRUE under the real "
                     "rendering procedure, which pads the collapsed zero to the two "
                     "requested places ('0.00') rather than emitting the bare "
                     "digit, so the rival is observably wrong and not merely "
                     "reshaped. If it verified => SPEC-TOO-WEAK (the clause would "
                     "not actually demand that the output be a rendering). Verified "
                     "with real builds: variant does not verify (exit 1), witness "
                     "elaborates against the rival (exit 0), fails on the frozen "
                     "solution (exit 1), consistency probe cannot derive False "
                     "(exit 1), and the flipped-claim forgery VERIFIES on gold "
                     "(exit 0) while FAILING on the rival (exit 1, `Tactic 'rfl' "
                     "failed: pure \"0\" is not definitionally equal to "
                     "renderDecimal 0 …`) — so gold's exit code tracks the claim.",
        "witness": ('example (h : renderDecimal 0 "." (some 2) 0 "" false none '
                    '≠ "0") :\n'
                    '    ¬ problem_spec_formatNumber (1/10^200) "." (some 2) 0 "" '
                    'false none\n'
                    '        (implementation_formatNumber (1/10^200) "." (some 2) '
                    '0 "" false none) := by\n'
                    '  unfold problem_spec_formatNumber implementation_formatNumber '
                    'snapValue\n'
                    '  simp only [Id.run]\n'
                    '  norm_num [cutoffOf]\n'
                    '  exact fun hc => h hc.symm\n'),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (3 positive
# controls — grounded-guard, reorder-decision, admissibility — and 6
# uniqueness/partial-domain rivals) plus a 3-probe AXIOM lane. This lean bundle
# models a NARROWER surface: the whole rendering procedure is delegated to an
# opaque callee, so the only modeled behavior is the smallness adjustment
# `snapValue`, and the postcondition is the single clause `result = renderDecimal
# (snapValue …) …`. Every sibling case attached to the modeled DECISION carries
# over; the two attached to the (here-unmodeled) RENDERING do not.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-grounded-guard   -> pos-control-grounded-guard   PORTED (re-proved)
#   pos-control-reorder-decision -> pos-control-reorder-match     PORTED
#   admiss-f2p-shaped            -> admiss-f2p-shaped             RE-EXPRESSED
#   rival-non-strict-cutoff      -> rival-non-strict-cutoff       PORTED
#   rival-no-threshold-floor     -> rival-no-threshold-floor      PORTED
#   rival-over-collapse          -> rival-over-collapse           PORTED
#   rival-never-collapse         -> rival-never-collapse          PORTED
#   rival-dp0-stray-separator    -> rival-fabricate-zero-string  PARTIAL (audit3)
#   rival-extra-leading-zero     -> rival-fabricate-zero-string  PARTIAL (audit3)
#   (none)                       -> rival-snap-when-no-precision   ADDED (none arm)
#   (none)                       -> rival-passthrough-precision  ADDED (audit: pass-thru)
#   (none)                       -> rival-passthrough-separators ADDED (audit2: presentation)
#   (none)                       -> pos-control-two-sided-compare ADDED (audit2: non-defeq)
#   AXIOM_TESTS (3)              -> (none)                         DROPPED (G-AX)
#
# PARTIAL (rival-dp0-stray-separator, rival-extra-leading-zero): both attack
#   nagini's P4, which pins the exact code-point LIST of the zero rendering
#   (`[48]` at dp==0, `[48,46]+zeros` at dp>=1). This lean bundle does not model
#   that list: the rendering is delegated to the `opaque renderDecimal`, so the
#   SPECIFIC digit-shape defects those two rivals inject — a stray separator at
#   dp==0, a doubled leading zero at dp>=1 — genuinely have no counterpart here.
#   There is no list term for a rival to mis-build, and that much is real carrier
#   narrowing rather than a case dropped for difficulty.
#
#   THIRD-AUDIT CORRECTION, and it is a correction of this block's REASONING, not
#   of its disposition for those two specific defects. The earlier revision went
#   on to conclude that the rendering side is therefore UNATTACKABLE on this
#   carrier — "the postcondition only pins WHICH ℚ value is rendered, not the
#   resulting string's shape" — and recorded the whole lane as inexpressible. That
#   inference is wrong, and `rival-fabricate-zero-string` is the measured
#   counterexample. The clause is `result = renderDecimal (snapValue …) …`: it
#   pins not only the renderer's arguments but that the result IS the renderer
#   applied to them. So the coarsest rendering defect the carrier CAN see remains
#   expressible — an impl that does not call the renderer at all and returns a
#   literal string — and it is now carried, with a witness whose hypothesis
#   (`renderDecimal 0 "." (some 2) … ≠ "0"`) is TRUE under the real rendering
#   procedure, which pads the collapsed zero to the requested places. What stays
#   inexpressible is the FINE-GRAINED digit shape (which separator, how many
#   leading zeros), because that lives inside the opaque callee. The honest
#   accounting is therefore PARTIAL rather than DROPPED: the lane is narrowed, not
#   absent.
# RE-EXPRESSED (admiss-f2p-shaped): the sibling's admissibility is a self-call
#   establishing the precondition `coeff>=0 and decimal_pos>=0`. This bundle's
#   theorem carries NO precondition (the spec is total), so the honest analogue
#   is to discharge the POSTCONDITION at the real F2P magnitude (1e-200 @ dp=2,
#   where the collapse fires) as a `have`, proving the modeled behavior is
#   satisfiable at a normal F2P input, then close the frozen obligation verbatim.
# ADDED (rival-snap-when-no-precision): the modeled `snapValue` has a two-armed
#   carrier (`some d` / `none`); the four ported decision rivals all attack the
#   `some` arm. The `none` arm ("no precision requested => value unchanged") is a
#   real, load-bearing branch of the SAME modeled behavior that no ported rival
#   touched, so one rival is added to attack it. It is not fabricated for an
#   unmodeled behavior — the nagini sibling simply could not express it (its
#   `format_small` is only reached with a precision).
# ADDED (rival-passthrough-precision, audit): the postcondition pins all EIGHT
#   arguments of the renderer application, but every other rival attacks the ℚ
#   position. The presentation binders and `decimalPos` are VARIED across the
#   witnesses and so are not pinned to a single value, but variation is not
#   attack: no case demonstrated that the spec forces the REQUESTED precision
#   through to the renderer, so a rival that snaps correctly and then renders at a
#   constant precision was unprobed. It is added to close that, and it is the only
#   rival whose rejection is attributable to the clause's pass-through structure
#   rather than to the smallness decision.
# ADDED (rival-passthrough-separators, second audit): rival-passthrough-precision
#   closed the `decimalPos` slot, but the FIVE presentation binders remained only
#   VARIED and never CORRUPTED — the same "variation is not attack" gap, one
#   argument group over. A rival that transposes `decimalSep` and `thousandSep`
#   while snapping perfectly is rejected purely by the clause pinning each
#   argument to its own position, and the hypothesis is TRUE under the real
#   rendering procedure ('5,00' vs '5.00' at number=5, dp=2, sep='.', tsep=',').
# ADDED (pos-control-two-sided-compare, second audit): BOTH pre-existing
#   soundness positives are definitionally equal to the frozen impl —
#   grounded-guard closes by `rfl` and reorder-match reduces identically under
#   the frozen script — so neither could detect a spec over-fit to the frozen
#   COMPARISON FORM as opposed to its branch order or syntax. The added positive
#   swaps `|n| < cutoffOf d` for the equivalent-but-not-defeq two-sided
#   conjunction, whose branch is selected by a different `Decidable` instance and
#   whose proof therefore needs real `abs_lt` bridging rather than reduction.
# VACUOUS (frame/permission mutation; control-flow effect; divergence): recorded
#   in the DEFENDED SURFACE docstring. Referential transparency + a total Lean
#   `def` collapse all three; no substitute probe is fabricated.
#
# POINT SPREAD. The eight reject witnesses probe eight input tuples:
#   (number, decimalPos)  [+ varied presentation binders]
#     (1/100,      some 2)   rival-non-strict-cutoff      some-arm, cutoff edge
#     (-(1/2),     some 0)   rival-no-threshold-floor     some-arm, dp==0 floor
#     (5,          some 2)   rival-over-collapse          some-arm, above cutoff
#     (-(1/100000),some 3)   rival-never-collapse         some-arm, below cutoff
#     (5,          none)     rival-snap-when-no-precision  none-arm
#     (5,          some 4)   rival-passthrough-precision   precision pass-through
#     (5,          some 2)   rival-passthrough-separators  presentation pass-through
#     (1/10^200,   some 2)   rival-fabricate-zero-string   result-is-a-rendering
#   The last point is the real F2P magnitude, so the reject lane and the
#   admissibility positive now meet at the same input from opposite directions:
#   the positive shows the obligation is SATISFIABLE there (and that the collapse
#   fires), the rival shows it is VIOLATED there by an impl that skips the
#   renderer.
#   number ∈ {1/100, -(1/2), 5, -(1/100000)} (both signs, so the magnitude
#   comparison is exercised on either side of zero), decimalPos ∈ {some 0, some 2,
#   some 3, some 4, none}, and the five presentation binders each take >=2 distinct
#   values across the witnesses, so no input binder is pinned.
#
#   The two NEGATIVE points are load-bearing rather than decorative, and this is
#   the substance of the first audit repair: on the sub-domain each of those two
#   rivals mis-handles, the rendering procedure separates the rival's snapped value
#   from gold's only when the surviving value carries a sign the snapped zero does
#   not. At the positive counterparts (1/2 @ dp=0, 1e-5 @ dp=3) the requested
#   precision truncates both snapped values to the same string, so the rival is
#   reshaped there but not observably wrong, and a witness stated at such a point
#   clears the gate while attesting to less than the case claims.
#
# GOLD-SIDE FAILURE MODE (second audit, established by real builds rather than by
#   reading the error text). Every reject case here records a `Type mismatch h`
#   gold_signature, which is an application/type mismatch and therefore has to
#   clear the FORGERY test before it counts as a semantic refutation. It does,
#   decisively, and the mechanism is worth stating because it is the opposite of
#   the hollow shape: for all EIGHT witnesses, a forgery that flips the claim
#   (drops the `¬`) and closes by `rfl` instead of `exact h` VERIFIES against the
#   frozen solution (exit 0) and FAILS against the rival (exit 1, `Tactic 'rfl'
#   failed`, showing the two concretely distinct renderer applications). So gold
#   really does satisfy the postcondition at each witness point by REDUCTION —
#   gold's exit code tracks the claim, the residual goal on gold is a genuine
#   self-identity the witness's `≠` hypothesis cannot inhabit, and the mismatch is
#   a refutation rather than a stuck term. (The bare `exact h` forgery fails on
#   both sides, which alone would have been uninformative; the `rfl` variant is
#   what separates them.) Re-measured independently in the third audit on all
#   eight cases, plus a type-REVEALING build (`exact (h : Nat)`) on both sides of
#   each: `h` prints its real, concrete `renderDecimal … ≠ renderDecimal …` type
#   on gold and on the rival alike — never `True` — so no `simp` step silently
#   proved the equation away on either side.
#
# SPEC PROBES (third audit, D and E; recorded so the next audit does not repeat
#   them). SPEC-TOO-WEAK probe — six NEW wrong impls the battery did not contain
#   were built against the frozen spec and ALL were rejected on the obligation:
#   dropping the `abs` so the comparison is signed; snapping to the cutoff instead
#   of to zero; flooring the threshold at 2 instead of 1; a cutoff one decade too
#   large; corrupting the `grouping` pass-through; corrupting the two Bool
#   pass-throughs. The first four fail with `unsolved goals` and the last two with
#   `Tactic 'rfl' failed`, i.e. the postcondition catches each. SPEC-TOO-STRONG
#   probe — three NEW correct reshapes were built and ALL verify (exit 0): the
#   comparison direction flipped (`cutoffOf d ≤ |n|` with the arms swapped); the
#   division multiplied out (`|n| * 10^(max d 1) < 1`, bridged by `lt_div_iff₀`);
#   and the snap factored into an impl-region helper `def` called from the loop.
#   So the spec admits every faithful reshape tried and rejects every wrong impl
#   tried: no hole found in either direction.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (`renderDecimal` is opaque, the proof uses no property of it),
# so there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []

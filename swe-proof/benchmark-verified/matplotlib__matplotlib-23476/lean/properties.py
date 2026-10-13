"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-23476 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so ``markers.same_spec``
holds and the ``theorem correct_serializedFigureDpi`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect:"reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` holds of the rival while FAILING
on the frozen solution).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``); it
carries over that battery's adversarial ARGUMENT and re-expresses it against this
backend's carrier. It is not a translation of the nagini text.

DEFENDED SURFACE (one total function of two data items)
-------------------------------------------------------
A single modeled function selects the resolution value recorded into a figure's
serialized state, from the current working resolution and an optional recorded
baseline:

  serializedFigureDpi (currentDpi : Rat) (baselineDpi : Option Rat) : Rat

The postcondition ``problem_spec_serializedFigureDpi`` has two independent
top-level clauses over its two input binders:

  (SEL)  ∀ d, baselineDpi = some d → result = d      (baseline present ⇒ record it)
  (FALL) baselineDpi = none → result = currentDpi     (baseline absent ⇒ record current)

WHAT DRIVES THE REJECTS. Both clauses are discriminating and each fixes a
different sub-domain of the ``baselineDpi`` binder. The defect the gold change
repairs is that the serialized resolution was the *current* (possibly rescaled)
value even when a baseline existed; the fix records the baseline whenever one is
present. So (SEL) is the load-bearing clause the F2P pins, and (FALL) is the
must-not-regress clause on the no-baseline sub-domain that the ordinary
(P2P) pickling paths exercise.

  * ``ignore-baseline`` attacks (SEL): a rival that always records the current
    resolution ignores a recorded baseline. This is exactly the pre-patch
    behavior — the F2P scenario has a present baseline (42) and a rescaled
    current value (294), so the rival records 294 and the F2P assertion
    ``fig2.dpi == 42`` FAILS. Refuted at ``(294, some 42)``.
  * ``bad-fallback`` attacks (FALL): a rival correct on the present sub-domain
    (records the baseline) but wrong when no baseline exists — it records a fixed
    default (0) rather than the current resolution, corrupting every never-
    rescaled figure. Refuted at ``(100, none)``.

  * ``sel-near-miss-one-baseline`` attacks (SEL) again, but at the QUANTIFIER
    rather than at the branch: it honors the baseline for every value except one
    ordinary resolution (72), where it keeps the current value. Refuted at
    ``(144, some 72)``.

Because the rejects vary ``baselineDpi`` across BOTH of its shapes (``some``
and ``none``) at distinct current-value points, the battery exercises the binder
across both sub-domains: a rival mishandling only the present branch is caught by
``ignore-baseline`` while ``bad-fallback`` independently pins the absent branch.
The ``currentDpi`` binder is varied too (294 vs 100 vs 144), and it is the
load-bearing input precisely on the (FALL) sub-domain that ``bad-fallback``
probes. The first two rivals are wrong at EVERY point of the branch they attack,
so each is refuted by the first input of that shape; ``sel-near-miss-one-
baseline`` is the one that pins (SEL)'s ``∀ d`` as a quantifier — it agrees with
gold everywhere else, survives both other witnesses (checked by real builds), and
so distinguishes "(SEL) holds for every recorded baseline" from "(SEL) holds at
the F2P's baseline".

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
impl's exact elaboration — so a rejection alone attributes nothing to the spec.
Each ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input, stated by unfolding the spec
predicate and the rival impl directly and closing by ``decide``. The carrier is
fully transparent (``Rat`` literals, ``Option``), so no term needs conditioning
and no witness binds a hypothesis — there is no consistency obligation. Each
witness was checked with two real builds: it ELABORATES against its rival and
FAILS against the frozen solution (gold records the baseline / falls back to the
current value, which the witness input distinguishes), so each discriminates
rather than asserting a tautology.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle models the imperative state-capture mutation over a
mutable ``Dict[int,int]`` held at FULL permission, and its cases split into a
value-selection family and a FRAME family (which entries of the state dict may
change). This lean carrier is referentially transparent and models only the pure
value selection — the single observable component the patch changes — as a total
function returning the selected resolution. The correspondence and omissions:

  * nagini ``weak-drop-selection`` (pre-patch: leave the recorded value at the
    scaled current one) and ``weak-inverted-selection`` (keep the live value when
    a baseline is present) both attack the present-baseline selection ↦
    ``ignore-baseline`` here (record current, ignore baseline). Both nagini rivals
    fail on the same (SEL) sub-domain for the same reason; here they collapse to
    one rival, refuted at the F2P-shaped ``(294, some 42)``.
  * nagini ``partial-domain-uncond-original`` (unconditionally write the
    baseline value, wrong when no baseline exists) ↦ ``bad-fallback`` here (wrong
    on the absent sub-domain). On this carrier ``baselineDpi = none`` leaves no
    baseline value to write, so the faithful rival is one that records a default
    (0) on the absent branch; it violates (FALL) at ``(100, none)``.
  * FRAME / PERMISSION MUTATION (nagini ``frame-violation-writes-baseline`` and
    ``frame-violation-adds-key``, MANDATORY there) — VACUOUS here. Lean is
    referentially transparent: the modeled function returns a single ``Rat``
    value and carries no mutable state dict, no heap permission, no other entries
    to preserve and no key membership to frame. There is no read-only region to
    overwrite and no aliasing, so both frame rivals have no counterpart and no
    substitute is fabricated. This is the class the mapping predicts is collapsed
    by carrier narrowing (the lean bundle models only the purely functional
    selection core; the state-dict framing the nagini spec pins is not modeled).
  * NON-TERMINATION (nagini ``weak-diverge-no-terminate``) — VACUOUS here, but
    not because the rival is unwritable. A self-recursive ``partial def`` IS
    admissible variant text (``partial`` is not an assumption token), and it was
    built: the file does NOT elaborate, because ``partial`` makes the constant
    opaque to the frozen proof's ``unfold``. That is the point — on lean a
    ``partial def`` is not logically diverging; it denotes some arbitrary
    inhabitant, so the rival is simply an unprovable one, NOT a vacuously
    verifying one. There is no partial-correctness escape on this backend for a
    spec stated as an equation on the returned value, so the class yields no
    shippable rival: a rejection here would attribute to an unfolding failure
    rather than to the spec, which is exactly what a witness is required to rule
    out. (On velvet under ``partial`` termination semantics this class IS a known
    spec hole; see ``the corpus-wide termination-semantics finding``. Lean is unaffected.)
  * nagini ``pos-reorder-grounded`` (structurally different but correct) ↦
    ``pos-getd`` / ``pos-fun-reorder`` here: a point-free ``Option.getD`` form and
    a plain functional ``match`` with the branches reordered, both correct and
    both re-proven (the ``correct_serializedFigureDpi`` statement byte-identical,
    no helper lemma, no axiom, no assumption token). nagini
    ``admiss-poststate-reached`` (the gold body plus an in-region assertion that
    the discriminating clause holds at a normal F2P-shaped input) ↦
    ``admiss-ground-instance``: a ``have`` inside the frozen proof body that
    discharges the spec predicate at ``(294, some 42)`` by evaluation, then the
    frozen obligation closes verbatim.

AXIOM lane: the nagini ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's job
and this gate ignores it. This bundle has no ``opaque``/``axiom`` pair (the
selection is modeled directly over transparent data), so there is no oracle to
echo; the spec is grounded in the two input binders via equality.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23476"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The whole gold impl (impl region). Unique; lies entirely inside impl-start /
# impl-end.
_IMPL_GOLD = (
    "def implementation_serializedFigureDpi\n"
    "    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat := Id.run do\n"
    "  let mut value := currentDpi\n"
    "  match baselineDpi with\n"
    "  | some d => value := d\n"
    "  | none   => pure ()\n"
    "  return value"
)

# The head of the proof region (impl-unfold lines) — for the admissibility
# ground instance. Unique in the file.
_PROOF_HEAD = (
    "  intro currentDpi baselineDpi\n"
    "  unfold problem_spec_serializedFigureDpi implementation_serializedFigureDpi"
)


# ---- witness helper ---------------------------------------------------------
# A reject witness states the spec predicate directly at one concrete transparent
# input and refutes it by `decide` (no opaque term to condition on, so no
# hypothesis is bound and there is no consistency obligation).

def _wit(cur, base):
    return (
        f"example : ¬ problem_spec_serializedFigureDpi {cur} {base}\n"
        f"    (implementation_serializedFigureDpi {cur} {base}) := by\n"
        f"  unfold problem_spec_serializedFigureDpi implementation_serializedFigureDpi\n"
        f"  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify (else the spec is over-fit => SPEC-
    # TOO-STRONG). Each keeps the `theorem correct_serializedFigureDpi`
    # statement byte-identical; a proof that closes the new shape is supplied
    # inside the proof region — no helper lemma, no axiom, no assumption token.
    # =====================================================================
    {
        "id": "pos-getd",
        "kind": "soundness",
        "expect": "verify",
        # Point-free selection via `Option.getD`: same value on every input, a
        # different executable shape (no `Id.run do`, no mutable local). The
        # frozen tactic body still closes it (both reduce to the same case split
        # on `baselineDpi`).
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_serializedFigureDpi\n"
            "    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat :=\n"
            "  baselineDpi.getD currentDpi",
        ),
        "rationale": "a correct point-free reshape (the baseline-or-current cascade "
                     "written as `Option.getD`) must satisfy both clauses (SEL) and "
                     "(FALL); if it cannot, the spec is over-fit to the exact "
                     "imperative spelling => SPEC-TOO-STRONG. Proof: the frozen "
                     "tactic body closes unchanged (the `getD` form case-splits on "
                     "`baselineDpi` to the same two branches).",
    },
    {
        "id": "pos-fun-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Plain functional `match` with the branches REORDERED (none first): same
        # value on every input, a different control-flow shape. Reproved with the
        # frozen tactic body (the `cases` split still discharges both clauses).
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_serializedFigureDpi\n"
            "    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat :=\n"
            "  match baselineDpi with\n"
            "  | none   => currentDpi\n"
            "  | some d => d",
        ),
        "rationale": "a structurally-different but correct impl (functional `match` "
                     "with the branches reordered) must verify (else SPEC-TOO-"
                     "STRONG). Proof: the frozen tactic body closes it — the "
                     "`cases baselineDpi` split reduces each branch to `rfl`.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at a normal, F2P-shaped input rather than only provable in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the modeled
    # behavior is total), so the nagini precondition-admission probe has no binder
    # to attack here; the honest analogue discharges the spec predicate at a
    # ground input matching the F2P scenario (present baseline 42, rescaled
    # current 294) by evaluation, inside the proof region, alongside the frozen
    # obligation. If that ground instance could not be discharged, the modeled
    # behavior would be unsatisfiable at exactly the input shape the F2P
    # exercises. Nothing is assumed: no new declaration, the theorem statement is
    # byte-identical, and the ground instance is a `have` inside the existing
    # tactic body.
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_HEAD,
            "  have _ground : problem_spec_serializedFigureDpi 294 (some 42)\n"
            "      (implementation_serializedFigureDpi 294 (some 42)) := by\n"
            "    unfold problem_spec_serializedFigureDpi implementation_serializedFigureDpi\n"
            "    decide\n"
            "  intro currentDpi baselineDpi\n"
            "  unfold problem_spec_serializedFigureDpi implementation_serializedFigureDpi",
        ),
        "rationale": "the selection obligation is discharged at a ground F2P-shaped "
                     "input (present baseline 42, rescaled current 294) by "
                     "evaluation, then the frozen obligation is closed verbatim. "
                     "Verifies (else the spec is unsatisfiable at the normal input, "
                     "the analogue of PRECOND-TOO-STRONG).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the frozen
    # spec that MUST be rejected. Each carries (a) the refinement argument that
    # its faithful real patch would NOT resolve the F2P/P2P, so a verifying rival
    # is a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "ignore-baseline",
        "kind": "uniqueness",
        "expect": "reject",
        # Always record the current resolution, ignoring any recorded baseline.
        # This IS the pre-patch behavior.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_serializedFigureDpi\n"
            "    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat :=\n"
            "  currentDpi",
        ),
        "refinement": "a routine that records the current working resolution even "
                      "when a baseline exists is exactly the pre-patch behavior: on "
                      "the F2P scenario the baseline is 42 and the current value is "
                      "the rescaled 42*7=294, so the serialized resolution is 294 "
                      "and the restored `fig2.dpi == 42` assertion FAILS (and each "
                      "cycle re-scales, doubling without bound). It does NOT resolve.",
        "rationale": "REJECT from clause (SEL) (∀ d, baselineDpi = some d → result = "
                     "d): at an input with a present baseline differing from the "
                     "current value the rival returns the current value while the "
                     "spec requires the baseline. If it verified => SPEC-TOO-WEAK "
                     "(admits the pre-patch selection).",
        "witness": _wit("294", "(some 42)"),
    },
    {
        "id": "bad-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on the present sub-domain (records the baseline) but records a
        # fixed default (0) when no baseline exists.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_serializedFigureDpi\n"
            "    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat :=\n"
            "  baselineDpi.getD 0",
        ),
        "refinement": "a patch that records the baseline when present but a fixed "
                      "default when absent corrupts every never-rescaled figure: "
                      "when no baseline was ever recorded the serialized resolution "
                      "should stay the figure's current working value, but this "
                      "rival writes 0 (a garbage resolution). Ordinary pickling "
                      "(the no-baseline P2P paths) would restore the wrong "
                      "resolution — it does NOT faithfully reproduce gold and does "
                      "NOT resolve the full set.",
        "rationale": "REJECT from clause (FALL) (baselineDpi = none → result = "
                     "currentDpi): on the absent sub-domain the rival returns 0 "
                     "while the spec requires the current resolution. If it verified "
                     "=> SPEC-TOO-WEAK (the no-baseline fallback is unconstrained). "
                     "Pins the absent-baseline sub-domain that `ignore-baseline` "
                     "does not touch.",
        "witness": _wit("100", "none"),
    },
    {
        "id": "sel-near-miss-one-baseline",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS on (SEL): records the baseline on the present branch and the
        # current value on the absent branch — i.e. correct on EVERY input except
        # those whose baseline is one particular ordinary resolution (72), where it
        # falls back to the current value. Added by audit: both other rivals are
        # wrong at every point of the branch they attack, so each is refuted by the
        # first input of that shape and neither exercises the `∀ d` quantifier of
        # (SEL) discriminatingly. This rival SURVIVES both existing witnesses
        # (verified by real builds at `(294, some 42)` and `(100, none)`), so it
        # probes a sub-domain the battery previously left unattacked: (SEL) must
        # hold for EVERY recorded baseline `d`, not merely for the F2P's one.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_serializedFigureDpi\n"
            "    (currentDpi : Rat) (baselineDpi : Option Rat) : Rat :=\n"
            "  match baselineDpi with\n"
            "  | some d => if d = 72 then currentDpi else d\n"
            "  | none   => currentDpi",
        ),
        "refinement": "a routine that honors the recorded baseline for most values "
                      "but silently keeps the current working resolution when the "
                      "baseline happens to be one ordinary resolution (72) is not "
                      "gold: every figure whose baseline is that resolution still "
                      "round-trips to the rescaled value and still grows on each "
                      "cycle. It happens to agree with gold on the F2P scenario "
                      "(whose baseline is 42), so it is not caught by that test "
                      "alone, but it diverges from gold on the ordinary-resolution "
                      "sub-domain the routine pickling paths exercise — it does NOT "
                      "faithfully reproduce gold and does NOT resolve the full set.",
        "rationale": "REJECT from clause (SEL) (∀ d, baselineDpi = some d → result = "
                     "d): the clause is universally quantified over the recorded "
                     "baseline, so an impl correct at all but one baseline value "
                     "still violates it — at `(144, some 72)` the rival returns 144 "
                     "while the spec requires 72. If it verified => SPEC-TOO-WEAK "
                     "(the (SEL) quantifier would be pinned only pointwise at the "
                     "F2P's baseline rather than for every `d`).",
        "witness": _wit("144", "(some 72)"),
    },
]

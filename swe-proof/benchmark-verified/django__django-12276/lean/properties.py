"""properties.py — G-PBT falsification battery for django__django-12276 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_useRequiredAttribute`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts ``requires_value(control, value_present)`` over an ``UploadControl``
object carrying a half-permission ``hidden`` field, and pins the result to the
TOTAL function ``generic_requires_value(control.hidden) and not value_present``
where ``generic_requires_value(hidden)`` is an A-consumed axiom fixed to
``not hidden``. This Lean bundle models the SAME single purely-functional core
over a pure ``Bool × Bool`` carrier: the base rule ``generic_requires_value(hidden)
== not hidden`` is INLINED DEEPLY as ``!isHidden`` (no opaque callee, so the
nagini axiom lane collapses — see below), and the decision becomes
``result = (!isHidden && !initialPresent)``. The two nagini observable inputs map
as:

  * ``control.hidden``    -> ``isHidden : Bool``       (identity)
  * ``value_present``     -> ``initialPresent : Bool`` (truthiness of the initial value)
  * ``generic_requires_value(control.hidden)`` -> ``!isHidden`` (inlined base rule)

Every nagini partial-domain rival carries over as an attack on the single
top-level equation; the two positive controls and the admissibility case carry
over as faithful correct impls; the nagini frame/permission-mutation class is
VACUOUS here (referential transparency — see ``assessment``); the nagini axiom
lane is DROPPED (G-AX's job, and empty here anyway).

DEFENDED SURFACE (one modeled behavior; ONE top-level clause, TWO input binders).
``problem_spec_useRequiredAttribute isHidden initialPresent result`` pins EXACTLY:

  * (C0)  ``result = (!isHidden && !initialPresent)`` — the element is marked
    required exactly when the base rule applies (the input is not hidden) AND no
    initial value is present. This is a TOTAL function of the two inputs, so
    echoing the oracle IS the correct behavior; the genuine attack surface is a
    partial-domain rival that gets one of the two facts wrong.

The BEHAVIOURAL DISCRIMINATOR (the fix): a present (truthy) initial value must
SUPPRESS the required marker even where the base rule would request it. The
pre-fix behavior returned only the base rule ``!isHidden`` (ignoring the initial
value); the ``drop-value`` rival below IS that pre-fix behavior, and on a visible
element carrying an initial value it advertises required where the fix demands
it be suppressed.

BINDER STRUCTURE. The spec predicate has TWO input binders: ``isHidden`` and
``initialPresent``. Both are load-bearing (a rival mishandling only one must be
caught) and both are varied across the reject witnesses: ``isHidden`` takes both
``true`` and ``false`` across the four rivals, ``initialPresent`` likewise, and
the four witnesses probe four DISTINCT input tuples (``pts=4``), the full
``Bool × Bool`` product.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's mandatory
    frame-mutation rival overwrites the half-permission ``control.hidden`` field
    to make the postcondition trivially hold, and relies on Viper rejecting the
    illegal write. On this referentially transparent carrier there is no heap, no
    aliasing, no ``mut`` input binder, and no read-only cell to overwrite —
    ``isHidden``/``initialPresent`` are immutable Boolean values. The class is
    VACUOUS; no substitute probe is fabricated (porting map: vacuous here).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result`` is
    pinned by a structural Boolean equation over the two inputs. There is no
    opaque answer key an implementation could echo — computing ``!isHidden &&
    !initialPresent`` IS doing the work. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the ``Bool ×
    Bool`` domain but diverging where the fix bites: dropping the initial-value
    factor (the pre-fix bug); dropping the base-rule factor; XOR instead of AND;
    and the constant-false near-miss.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` proof is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet that states the spec
predicate directly at one CONCRETE ``(isHidden, initialPresent)`` corner and
closes by ``decide`` (the carrier is pure ``Bool``, so ``decide`` computes both
the rival's output and the spec's target with no opaque term in the way). Each
witness binds NOTHING in its head (both inputs are ground Boolean literals), so
there are no hypotheses whose consistency could be in question. Each was checked
with two real ``lake env lean`` builds to HOLD of its rival and to FAIL on the
frozen solution, so it discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
decision that mishandles one of the two facts, so on the F2P inputs
(``use_required_attribute(None)`` must be True on a visible element,
``use_required_attribute('resume.txt')`` must be False, and the rendering test
pins the same on a form) the emitted required-marker decision disagrees with the
expected one — so the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the base rule is modeled deeply as ``!isHidden``); the axiom lane
belongs to G-AX, and the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-12276"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The single impl line inside `-- impl-start`/`-- impl-end`.
_GOLD_IMPL = "  return (!isHidden) && (!initialPresent)"

# The frozen proof body inside `-- proof-start`/`-- proof-end`. The frozen `rfl`
# closes only for the frozen impl's syntactic form; a reshaped-but-correct
# positive re-proves by casing the two Booleans. Swapping this block leaves the
# `correct_useRequiredAttribute` STATEMENT byte-identical (the theorem signature
# lines above are untouched) and adds no axiom/lemma.
_PROOF_BODY = (
    "  intro isHidden initialPresent\n"
    "  unfold problem_spec_useRequiredAttribute implementation_useRequiredAttribute\n"
    "  rfl"
)
_PROOF_CASES = (
    "  intro isHidden initialPresent\n"
    "  unfold problem_spec_useRequiredAttribute implementation_useRequiredAttribute\n"
    "  cases isHidden <;> cases initialPresent <;> rfl"
)


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate at one concrete corner; `decide`
# computes both the rival's output and the spec target (pure Bool, no opaque
# term). Binds nothing in the head -> no hypothesis-consistency question.
# ---------------------------------------------------------------------------
def _w(isHidden, initialPresent):
    pt = f"{isHidden} {initialPresent}"
    return (
        f"example : ¬ problem_spec_useRequiredAttribute {pt}\n"
        f"    (implementation_useRequiredAttribute {pt}) := by\n"
        "  unfold problem_spec_useRequiredAttribute implementation_useRequiredAttribute\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_useRequiredAttribute` STATEMENT byte-identical and adds no
    # axiom/lemma; only the impl body and the proof tactic body change.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch-REORDER: decide on the initial value FIRST (present => never
        # required), else fall through to the base rule. Same values, different
        # control flow. Re-proved by casing the two Booleans (the frozen `rfl`
        # does not reduce the `if` on a variable). (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_GOLD_IMPL,
             "  if initialPresent then return false else return (!isHidden)"),
            (_PROOF_BODY, _PROOF_CASES),
        ),
        "rationale": "structurally-different CORRECT impl (decide on the initial "
                     "value first, else the base rule); computes the SAME result on "
                     "every (isHidden, initialPresent), so C0 still holds — else "
                     "SPEC-TOO-STRONG. Re-proved by casing the two Booleans; "
                     "statement byte-identical, no new axiom/lemma. Ports nagini's "
                     "pos-control-reorder.",
    },
    {
        "id": "pos-locals-commuted",
        "kind": "soundness",
        "expect": "verify",
        # De Morgan / local-variable reshape: compute the base decision and the
        # absence-of-initial into typed locals, return their conjunction in the
        # OPPOSITE operand order. Boolean `&&` is commutative here, so this equals
        # the gold result. Re-proved by casing the two Booleans (commuted `&&` is
        # not defeq to the gold order by `rfl`). (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_GOLD_IMPL,
             "  let g := !isHidden\n"
             "  let absent := !initialPresent\n"
             "  return (absent && g)"),
            (_PROOF_BODY, _PROOF_CASES),
        ),
        "rationale": "correct impl via typed locals + commuted boolean `&&` (both "
                     "operands Bool). Second independent positive witness that a "
                     "faithful correct impl of a different shape verifies — else "
                     "SPEC-TOO-STRONG. Re-proved by casing the two Booleans; "
                     "statement byte-identical, no new axiom/lemma. Ports nagini's "
                     "pos-control-locals.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The nagini precondition-admission self-call
    # re-expresses as: discharge the spec predicate by evaluation at the F2P
    # no-initial-value case (a visible element, isHidden=false, initialPresent=
    # false, where the result is True) as a `have`, then close the frozen
    # obligation verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical, ground instance is a `have` prepended to the tactic body.
    # (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-novalue",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_useRequiredAttribute false false\n"
            "      (implementation_useRequiredAttribute false false) := by\n"
            "    unfold problem_spec_useRequiredAttribute implementation_useRequiredAttribute\n"
            "    decide\n"
            + _PROOF_BODY),
        "rationale": "the obligation is discharged at the F2P no-initial-value case "
                     "(a visible element with no initial value: isHidden=false, "
                     "initialPresent=false, result=true) by evaluation as a `have`, "
                     "then the frozen obligation is closed verbatim. Verifies (else "
                     "the modeled behavior would be unsatisfiable at exactly a normal "
                     "F2P input — the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, statement byte-identical, ground "
                     "instance is a `have` in the existing tactic body. Ports "
                     "nagini's admiss-novalue.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, and (b) a witness pinning the violation
    # at one concrete input. The frozen proof is kept as-is (it fails against the
    # reshaped impl -> the case does not verify); the witness attributes the
    # rejection to the spec.
    # =====================================================================

    # ---- the fix itself: drop the initial-value factor (pre-patch bug) ----
    {
        "id": "drop-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, "  return (!isHidden)"),
        "refinement": "this IS the pre-patch behavior: the decision returns only the "
                      "base rule (not hidden), ignoring the initial value. The "
                      "faithful real patch is the EMPTY change (no override added), "
                      "which is exactly the state the F2P tests FAIL on: a visible "
                      "element carrying an initial value would advertise required "
                      "(True) where the fix demands it be suppressed (False), and the "
                      "rendering test expects no required marker with an initial "
                      "value present. Does NOT resolve.",
        "rationale": "REJECT from C0: the spec pins `!isHidden && !initialPresent` "
                     "but the rival emits `!isHidden`, which differ whenever the "
                     "base rule holds AND an initial value is present. Refuted at "
                     "(isHidden=false, initialPresent=true): spec demands False, the "
                     "rival returns True.",
        "witness": _w("false", "true"),
    },

    # ---- drop the base-rule factor ----
    {
        "id": "drop-base-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, "  return (!initialPresent)"),
        "refinement": "drops the base-rule factor and returns only the absence of an "
                      "initial value. A faithful real patch behaving this way makes a "
                      "HIDDEN element advertise required whenever it carries no "
                      "initial value — abandoning the unchanged base rule (a hidden "
                      "input is never required) that the no-value regression cases "
                      "rely on. It diverges from the base behavior and would NOT "
                      "resolve.",
        "rationale": "REJECT from C0: the spec pins `!isHidden && !initialPresent` "
                     "but the rival emits `!initialPresent`, which differ whenever "
                     "the element is hidden and no initial value is present. Refuted "
                     "at (isHidden=true, initialPresent=false): spec demands False, "
                     "the rival returns True.",
        "witness": _w("true", "false"),
    },

    # ---- XOR instead of AND ----
    {
        "id": "xor-not-and",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, "  return ((!isHidden) != initialPresent)"),
        "refinement": "computes an XOR of the base rule and the initial-value "
                      "presence instead of the conjunction. A faithful real patch of "
                      "this shape, on a hidden element carrying a usable initial "
                      "value, would advertise required (True) where both the base "
                      "rule (hidden => not required) and the present-value "
                      "suppression demand False. It diverges from the intended "
                      "conjunction and would NOT resolve.",
        "rationale": "REJECT from C0: XOR agrees with the gold AND on three of the "
                     "four corners but on (isHidden=true, initialPresent=true) the "
                     "gold result is False while `(!true) != true` = "
                     "`false != true` = True. Refuted at that corner.",
        "witness": _w("true", "true"),
    },

    # ---- supporting near-miss: constant False ----
    {
        "id": "const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, "  return false"),
        "refinement": "a real patch returning a constant False makes EVERY element "
                      "non-required, so the F2P no-initial-value case (a visible "
                      "element with no initial value must be required, True) and the "
                      "rendering test (required marker present with no initial value) "
                      "both fail. Does NOT resolve.",
        "rationale": "supporting near-miss from C0: correct on every corner where the "
                     "gold result is False, wrong on (isHidden=false, "
                     "initialPresent=false) where the spec demands True. Refuted at "
                     "that corner.",
        "witness": _w("false", "false"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation, 4 partial-domain
# rivals) plus a 2-probe AXIOM lane. This bundle models the SAME single
# purely-functional core (the required-marker decision) and re-expresses every
# sibling case that has a counterpart on the pure Bool carrier.
#
#   sibling case               -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder        -> pos-branch-reorder      PORTED (re-proved)
#   pos-control-locals         -> pos-locals-commuted     PORTED (re-proved)
#   admiss-novalue             -> admiss-f2p-novalue      RE-EXPRESSED
#   frame-mut-write-hidden     -> (none)                  VACUOUS (see below)
#   partial-drop-value         -> drop-value              PORTED
#   partial-drop-generic       -> drop-base-rule          PORTED
#   partial-xor                -> xor-not-and             PORTED
#   supporting-const-false     -> const-false             PORTED
#   AXIOM_TESTS (2)            -> (none)                  DROPPED (G-AX)
#
# RE-EXPRESSED (admiss-f2p-novalue): the sibling's admissibility case builds a
#   fresh visible UploadControl and asserts the half-permission precondition
#   admits it and the self-call goes through. This carrier has no heap
#   precondition (the frozen theorem quantifies over all Bool × Bool with no
#   hypotheses), so the honest analogue is to discharge the POSTCONDITION at the
#   smallest F2P-shaped input (the no-initial-value visible element, result True)
#   as a `have`, proving the modeled behavior is satisfiable at a normal input,
#   then close the frozen obligation verbatim.
# VACUOUS (frame-mut-write-hidden): the sibling's mandatory frame-mutation rival
#   overwrites the half-permission `control.hidden` field and relies on Viper
#   rejecting the illegal write. On this referentially transparent carrier there
#   is no heap, no aliasing, no `mut` input binder, and no read-only cell to
#   overwrite — the inputs are immutable Boolean values. The class is vacuous; no
#   substitute probe is fabricated (porting map: vacuous here).
# DROPPED (AXIOM_TESTS): the sibling probes the A-consumed `generic_requires_value`
#   axiom against the real inherited base callee. This bundle models that base
#   rule DEEPLY as `!isHidden` (no `opaque` callee, no `axiom`), so there is
#   nothing to probe; the axiom lane belongs to G-AX and is ignored here.
#
# POINT SPREAD. The four reject witnesses probe four DISTINCT input tuples (the
# full Bool × Bool product, pts=4):
#     (isHidden, initialPresent) =
#       (false, true)   drop-value     C0
#       (true,  false)  drop-base-rule C0
#       (true,  true)   xor-not-and    C0
#       (false, false)  const-false    C0
#   Across them isHidden ∈ {false, true} and initialPresent ∈ {false, true}, so
#   neither input binder is pinned: a rival mishandling either input alone is
#   caught. The spec has a single top-level clause (the Boolean equation), which
#   every rival attacks.
AXIOM_TESTS = []

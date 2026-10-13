"""properties.py — G-PBT falsification battery for pydata__xarray-3993 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the selector-routing prologue as a permission-carrying procedure over an
``Optional[int]`` pair returning a ``Routed`` object plus a control-flow effect
(raise / deprecation signal). This Lean bundle models the SAME purely-functional
core as ONE total function over the two optional selectors returning an
``Except``-carried outcome ``(value, warned)``: the rejected call is
``Except.error``; an honoured call is ``Except.ok`` of the downstream
integration applied to the resolved selector paired with whether the deprecation
notice fired. Every nagini case therefore carries over as an attack on ONE
clause of the one modeled obligation; the mapping of each nagini case to its Lean
counterpart (or its principled omission) is in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior). The result is fully pinned for every
input by three mutually-exclusive, exhaustive antecedents over the two selectors:

  * (C1) BOTH selectors supplied  →  the call is rejected (``Except.error``);
  * (C2) ONLY the legacy selector supplied  →  integrate along the legacy
    selector AND raise the deprecation notice (``Except.ok (…, true)``);
  * (C3) the legacy selector absent  →  integrate along the primary selector
    (which may itself be absent) with NO notice (``Except.ok (…, false)``).

The BEHAVIOURAL DISCRIMINATOR (the fix): the deprecation notice fires on EXACTLY
the legacy-selector-only call and nowhere else, and in that one case the LEGACY
selector — not the (absent) primary one — reaches the downstream integration.
The pre-fix behavior routed the legacy selector through but raised no notice;
that rival is the primary partial-domain attack below.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini value parameters are plain
    ``Option`` values; there is no frame-mutation rival to express and no
    substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — NOT LANDABLE as a reject case here, for a
    reason that was MEASURED rather than assumed. The nagini bundle carries a
    ``diverge`` rival (W6) that spins forever on the primary-selector path and
    verified under the pre-fix contract. The port originally recorded this as
    "a diverging implementation cannot be written at all"; that is FALSE and is
    corrected here. Rewriting the impl as a ``partial def`` whose
    primary-selector path recurses on itself IS expressible, IS in variant
    scope, and elaborates as a declaration (the return type ``Except Unit …``
    is ``Inhabited`` via ``Except.error ()``, so ``partial`` needs no extra
    instance). The measured outcome: that rival is REJECTED (the frozen tactic
    body cannot reduce a ``partial def``), but NO refutation witness can be
    built against it either — ``rfl`` cannot reduce the opaque term, so the
    witness fails on the RIVAL, the half that must succeed. The reason is not a
    tactic gap: in Lean's logic a ``partial def`` is TOTAL and its value on the
    recursing path is UNDERDETERMINED, not wrong, so there is no true
    refutation to state — the spec may well hold of it. Divergence is simply
    not observable on this carrier, so the distinction the nagini
    ``MustTerminate`` obligation drew collapses. Rejected-but-unwitnessable
    means the case would land as ``witness-unproven`` (inconclusive), which is
    exactly the vacuous rejection the witness rule exists to refuse. Nothing to
    port, and NOT a spec hole: the rival does not verify. Re-measured
    independently at audit: the ``partial def`` rival builds to exit 1, and its
    witness against the RIVAL also exits 1 (``unsolved goals … ⊢ False`` with the
    hypothesis left as an unreduced application), confirming the half that must
    succeed does not. SCOPE NOTE: the known divergence spec hole recorded in
    ``the corpus-wide termination-semantics finding`` is a VELVET matter — it is the
    ``loom.semantics.termination "partial"`` set_option admitting a diverging impl
    vacuously, measured on 401 velvet bundles, with lean and nagini explicitly
    unaffected. This is a lean bundle with a total ``def``, so that finding does
    not apply here and is deliberately NOT re-reported as a new hole.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: the honoured
    result is pinned equal to ``integrateAlong`` applied to the resolved selector
    (a term built only from the inputs and the universally-quantified downstream
    step). There is no opaque answer key an implementation could echo; the impl
    still has to select the branch and route the right selector. In its place the
    battery carries honest cheapest-implementation POSITIVE CONTROLS.

  * PARTIAL-DOMAIN / VALUE + CONTROL-FLOW — APPLIES. Rivals correct on part of
    the domain but diverging where the fix bites: never raise the notice; always
    raise it; route the wrong (absent) selector on the legacy-only call; return
    normally on the both-supplied input instead of rejecting; reject every call.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. Each was checked to HOLD of its rival and to FAIL
on the frozen solution, so it discriminates rather than asserting a tautology.
The carrier computes: ``integrateAlong`` is instantiated at a concrete
``fun o => o.getD k`` (an honest, arbitrary total function — NOT an oracle the
spec references) so the honoured payload reduces to a decidable ``Nat`` and every
witness closes by ``rfl``-reduction of the rival impl plus a Boolean/``Nat``
disagreement (or ``Except.noConfusion`` on the ``ok``/``error`` split).

WHY THE GOLD-SIDE FAILURE CARRIES INFORMATION (the shape of the evidence, since
"the build failed" is not by itself evidence of anything). Each witness pins the
rival's value at its input with ``have hr : implementation_integrate … = <v> :=
rfl`` and only then derives the contradiction. That ``rfl`` is a PLAIN EVALUATION
of a closed term over ``Option Nat``: it is the step that fails on the frozen
solution, and it fails with a *concrete* mismatch naming the value the witness
claimed, e.g. ``expected implementation_integrate (fun o => o.getD 0) none
(some 3) = Except.ok (3, false)`` — because the frozen impl evaluates to
``(3, true)`` there instead. Nothing is opaque, unfoldable, or undecidable on
either side: the identical ``rfl`` SUCCEEDS against the rival, so identifiers,
types and unfolding are all demonstrably fine and the only thing that changed is
the value. Consequently the gold-side exit code TRACKS THE CLAIM rather than
being a standing property of the carrier — restate any of these witnesses with its
value flipped to the frozen one and the gold build goes green while the rival
build goes red, the exact mirror image. That is the property a reject case needs
and the property a stuck reduction, a missing ``Decidable`` instance or a
unification failure on an unnormalised term would each lack.

BINDER / POINT SPREAD. The reject witnesses move both selector binders rather
than fixing them at one point. ``coord`` takes ``none`` (W1, W3, W6, W7) and
``some`` (W2, W4, W5, W8); ``dim`` takes ``none`` (W2, W5, W6, W8) and ``some``
(W1, W3, W4, W7). All three spec antecedents are represented: both-supplied (W4),
legacy-only (W1, W3, W7), legacy-absent (W2, W5, W6, W8). W3 specifically
demonstrates that the LEGACY selector, not the absent primary one, must reach
``integrateAlong`` on the legacy-only call (the argument-routing attack); W8 is
its MIRROR on the other honoured clause — the PRIMARY selector, not the absent
legacy one, must reach ``integrateAlong`` on the primary-only call. W6 covers the
one input class the others leave unattacked: the NEITHER-supplied call, which the
legacy-absent clause C3 reaches by collapsing two rows of the resolution table
into ``dim = none`` (see ``mapping.md``); every other reject case probes a row
where at least one selector is present. The eight reject witnesses probe eight
DISTINCT inputs; no two share a refutation point. The downstream-step binder
``integrateAlong`` is also varied across witnesses (instantiated at distinct
arbitrary total functions ``fun o => o.getD k`` for different ``k``) so no rival
mishandling it would slip through unexercised.

CLAUSE x COMPONENT COVERAGE. Every clause is attacked in every direction its
outcome can fail. The outcome has two independent axes — the ``ok``/``error``
CONSTRUCTOR, and (when ``ok``) the two payload COMPONENTS — and a rival can be
wrong on either without being wrong on the other:

  * C1 (both-supplied, pins ``error``): constructor attacked by W4 (returns
    ``ok``). No payload axis exists here — the clause pins ``Except.error ()``,
    which carries none.
  * C2 (legacy-only, pins ``ok (integrateAlong dim, true)``): value component
    attacked by W3 (routes the absent primary selector), flag component by W1
    (drops the notice), CONSTRUCTOR by W7 (refuses the call outright).
  * C3 (legacy-absent, pins ``ok (integrateAlong coord, false)``): VALUE
    component attacked by W8 (routes the absent legacy selector), flag component
    by W2 (primary-only row) and W6 (neither-supplied row), constructor by W5
    (rejects an honoured call).

W7 and W8 are AUDIT ADDITIONS, each closing one cell this table asserted but did
not fill. W7 closed C2's ok/error CONSTRUCTOR axis: W1 and W3 both hand the rival
an ``ok`` and attack only what is inside it, so nothing established that C2 forces
an honoured outcome AT ALL rather than merely constraining the payload of one. A
rival that widens the rejection guard to refuse the legacy spelling outright is
wrong on exactly that axis, and it is wrong in the direction a conservative
misreading of a deprecation actually goes (refuse the deprecated call rather than
honour-and-warn). W7's rival is NOT subsumed by W5: W5 rejects unconditionally and
is refuted on the legacy-ABSENT row, whereas W7's rival honours the
primary-selector call correctly and is wrong only where the legacy spelling is
used.

W8 closes C3's VALUE axis, which a SECOND audit pass found still blank while this
table's own opening sentence claimed every clause was attacked in every direction
its outcome can fail. Before W8, every rival reaching C3 was wrong about the
outcome's SHELL rather than about which selector was integrated along: W2 and W6
flip only the notice flag, W5 replaces the whole honoured outcome with a
rejection. So nothing in the battery established that C3 pins ``integrateAlong
coord`` rather than merely ``integrateAlong <something>`` paired with ``false`` —
the routed-selector obligation was DEMONSTRATED on the legacy-only clause (by W3)
and merely ASSUMED on the legacy-absent one. That asymmetry sits exactly where the
argument-routing half of this behavior lives: the whole point of the resolution
rules is WHICH selector reaches the downstream step, and C3 is the clause carrying
the ordinary, non-deprecated call — the one the P2P surface exercises. W8's rival
routes the legacy selector on EVERY honoured call, so on the primary-only row it
integrates along the ABSENT legacy selector while the notice flag stays correct:
the mirror image of W3, wrong on exactly one axis of exactly one clause, and
correct on the both-supplied and legacy-only rows that W4/W7 cover.

AXIOM lane: EMPTY here. The downstream integration ``integrateAlong`` is a
universally-quantified parameter (an A-reference), not a consumed ``axiom``; the
bundle declares no ``opaque`` and consumes no ``axiom``. The axiom lane belongs to
G-AX; this gate ignores it, and the nagini ``AXIOM_TESTS`` (also empty there) are
dropped.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-3993"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the admissibility
# positive that re-proves, the proof region) so same_spec stays byte-identical.

# The whole frozen impl body (impl region).
_IMPL_BODY = (
    "  if dim.isSome && coord.isSome then\n"
    "    return Except.error ()\n"
    "  let mut effective := coord\n"
    "  let mut warned := false\n"
    "  if dim.isSome && coord.isNone then\n"
    "    effective := dim\n"
    "    warned := true\n"
    "  return Except.ok (integrateAlong effective, warned)"
)

# The legacy-only arm's two mutations (route the legacy selector + raise notice).
_I_LEGACY_ARM = "    effective := dim\n    warned := true"

# The `warned` initialiser (impl region).
_I_WARNED_INIT = "  let mut warned := false"

# The `warned` initialiser plus the whole legacy arm and the return (impl
# region) — replaced wholesale by the W6 near-miss, which derives the notice
# flag from the PRIMARY selector's absence instead of the legacy selector's
# presence.
_I_ARM_AND_RETURN = (
    "  let mut warned := false\n"
    "  if dim.isSome && coord.isNone then\n"
    "    effective := dim\n"
    "    warned := true\n"
    "  return Except.ok (integrateAlong effective, warned)"
)

# The `effective` initialiser plus the legacy arm and the return (impl region) —
# replaced wholesale by the W8 near-miss, which routes the LEGACY selector on
# every honoured call instead of the resolved one.
_I_EFFECTIVE_AND_RETURN = (
    "  let mut effective := coord\n"
    "  let mut warned := false\n"
    "  if dim.isSome && coord.isNone then\n"
    "    effective := dim\n"
    "    warned := true\n"
    "  return Except.ok (integrateAlong effective, warned)"
)

# The both-supplied rejection guard + the line after it (impl region).
_I_REJECT_GUARD = (
    "  if dim.isSome && coord.isSome then\n"
    "    return Except.error ()\n"
    "  let mut effective := coord"
)

# The frozen proof body (proof region).
_P_FROZEN = (
    "  refine ⟨?_, ?_, ?_⟩ <;> intro h <;>\n"
    "    cases coord <;> cases dim <;>\n"
    "    simp_all [implementation_integrate, Id.run] <;> rfl"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. Keeps the theorem statement AND
    # the frozen proof body byte-identical.
    #
    # Ports nagini case `pos-reorder`: the nagini positive used an early-return
    # cascade with NO mutable `deprecated` local and NO `coord = dim`
    # reassignment. The analogous Lean reshape drops both `let mut` locals and
    # returns each honoured outcome directly. The definitional value on every
    # input is unchanged, so the frozen `cases … <;> simp_all <;> rfl` still
    # closes (no helper lemma, no axiom, no assumption token introduced).
    # =====================================================================
    {
        "id": "pos-early-return-cascade",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  if dim.isSome && coord.isSome then\n"
            "    return Except.error ()\n"
            "  if dim.isSome && coord.isNone then\n"
            "    return Except.ok (integrateAlong dim, true)\n"
            "  return Except.ok (integrateAlong coord, false)",
        ),
        "rationale": "structurally-different CORRECT impl: an early-return "
                     "cascade with no mutable `effective`/`warned` locals and no "
                     "reassignment; each return discharges directly against C1 "
                     "(reject), C2 (legacy-only routes the legacy selector with "
                     "the notice) and C3 (legacy-absent routes the primary "
                     "selector, no notice). The resolved value is identical on "
                     "every input, so `problem_spec_integrate …` still holds. "
                     "Must verify, else SPEC-TOO-STRONG. Branch/return reshape "
                     "only — no loop/fold/induction — so the frozen proof body "
                     "closes unchanged. Ports nagini's `pos-reorder`.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped honoured input. The
    # frozen theorem carries NO precondition hypothesis (the modeled behavior is
    # total, so `∀` is unguarded), so the nagini precondition-admission probe has
    # no binder to attack here; the honest analogue is to discharge the spec
    # predicate at a ground legacy-only input (the F2P call da.integrate(dim=…))
    # alongside the frozen obligation. Ports nagini `admiss-legacy-only`.
    # =====================================================================
    {
        "id": "admiss-legacy-only-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P-shaped legacy-only input, then close
        # the frozen obligation verbatim. Nothing is assumed: no new declaration,
        # the theorem statement is byte-identical, and the ground instance is a
        # `have` inside the existing tactic body (proof region only).
        "module": _swap(
            _BASE, _P_FROZEN,
            "  have _ground : problem_spec_integrate (fun o => (o.getD 0 : Nat)) "
            "(none : Option Nat) (some 3)\n"
            "      (implementation_integrate (fun o => (o.getD 0 : Nat)) "
            "(none : Option Nat) (some 3)) :=\n"
            "    ⟨by intro h; simp_all [implementation_integrate, Id.run],\n"
            "     by intro _; rfl,\n"
            "     by intro h; simp_all⟩\n"
            + _P_FROZEN,
        ),
        "rationale": "the obligation is discharged at a ground legacy-only "
                     "honoured input (the F2P scenario: legacy selector supplied, "
                     "primary absent — da.integrate(dim=…)) before the frozen "
                     "obligation is closed verbatim. Verifies, else the modeled "
                     "behavior is unsatisfiable at exactly the input the F2P "
                     "exercises (the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, statement byte-identical, the "
                     "ground instance is a `have` inside the existing tactic "
                     "body. Ports nagini's `admiss-legacy-only`. THIS LANE DOES "
                     "BITE, and the bite was measured rather than argued: the "
                     "`have` names the ground input's outcome CONCRETELY, so it "
                     "fails against an impl that resolves that input differently. "
                     "Transplanting this exact tactic body onto the W1 rival "
                     "(which drops the notice on precisely this legacy-only call) "
                     "makes the `have`'s middle component fail on its own — "
                     "`rfl` reports `implementation_integrate (fun o => o.getD 0) "
                     "none (some 3)` is not definitionally equal to "
                     "`Except.ok ((fun o => o.getD 0) (some 3), true)` — i.e. the "
                     "ground instance is refuted at the F2P-shaped point "
                     "independently of the universally-quantified obligation. So "
                     "this case is not a restatement of the soundness positive: it "
                     "pins satisfiability at the one concrete input the F2P "
                     "exercises, which is the analogue of PRECOND-TOO-STRONG on a "
                     "total carrier.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break, and (b) a refutation witness
    # pinning the violation at one concrete input, checked to hold of the rival
    # and FAIL on the frozen solution.
    # =====================================================================

    # ---- W1: never raise the deprecation notice (THE discriminator) ----
    {
        "id": "w1-never-deprecate",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: route the legacy selector through but NEVER set the
        # notice flag (drop the `warned := true` mutation of the legacy arm).
        "module": _swap(_BASE, _I_LEGACY_ARM, "    effective := dim"),
        "refinement": "this IS the pre-fix behavior: the legacy selector is "
                      "routed through but no deprecation notice is raised. The "
                      "F2P asserts that the legacy-selector-only call raises a "
                      "deprecation notice (pytest.warns); the no-notice patch "
                      "emits none and that assertion FAILS, so the faithful real "
                      "patch would NOT resolve.",
        "rationale": "REJECT from clause C2: on the legacy-only input the spec "
                     "pins `warned = true` but the rival returns `warned = false`, "
                     "so `result` differs. THE discriminating clause; "
                     "partial-domain (legacy-only sub-domain). Binder point: "
                     "coord=none, dim=some.",
        "witness": (
            "-- Refuted at the legacy-only input (coord absent, legacy selector\n"
            "-- present): the rival returns warned=false where C2 demands true.\n"
            "-- integrateAlong is instantiated at an arbitrary total function\n"
            "-- (varied per witness, not an oracle the spec references).\n"
            "example : ¬ problem_spec_integrate (fun o => (o.getD 0 : Nat)) "
            "(none : Option Nat) (some 3)\n"
            "    (implementation_integrate (fun o => (o.getD 0 : Nat)) "
            "(none : Option Nat) (some 3)) := by\n"
            "  intro h\n"
            "  have h2 := h.2.1 ⟨rfl, rfl⟩\n"
            "  have hr : implementation_integrate (fun o => (o.getD 0 : Nat)) "
            "(none : Option Nat) (some 3)\n"
            "      = Except.ok (3, false) := rfl\n"
            "  rw [hr] at h2\n"
            "  simp only [Except.ok.injEq, Prod.mk.injEq] at h2\n"
            "  exact absurd h2.2 (by decide)\n"
        ),
    },

    # ---- W2: always raise the deprecation notice ----
    {
        "id": "w2-always-deprecate",
        "kind": "uniqueness",
        "expect": "reject",
        # Initialise the notice flag to `true`, so it fires even on the
        # primary-selector-only call (and the neither-supplied call).
        "module": _swap(_BASE, _I_WARNED_INIT, "  let mut warned := true"),
        "refinement": "a real patch raising the deprecation notice "
                      "UNCONDITIONALLY (hoisted above the legacy-selector guard) "
                      "would warn on the ordinary primary-selector call too. The "
                      "P2P suite calls the operation via the primary selector "
                      "expecting NO notice, so the benign path becomes noisy. "
                      "HONEST SCOPE (checked, not assumed): the project's pytest "
                      "config does NOT turn warnings into errors globally, so a "
                      "spurious notice is not by itself a test failure on every "
                      "P2P call — the F2P assertion is a `warns` context, which an "
                      "always-warn patch still satisfies. What refutes this rival "
                      "is the specified behavior: the notice must fire on EXACTLY "
                      "the legacy-selector call, and a notice on a call that used "
                      "no deprecated spelling is a false report to the caller. So "
                      "read W2 as pinning the 'and nowhere else' half of the "
                      "discriminator — the half a resolution-only argument cannot "
                      "reach — rather than as a would-not-resolve claim.",
        "rationale": "REJECT from clause C3: on the legacy-absent input "
                     "(dim=none, coord supplied) the spec pins `warned = false` "
                     "but the rival returns `warned = true`, so `result` differs. "
                     "Partial-domain (primary-only sub-domain). Binder point: "
                     "coord=some, dim=none.",
        "witness": (
            "-- Refuted at the primary-only input (legacy selector absent): the\n"
            "-- rival returns warned=true where C3 demands false.\n"
            "example : ¬ problem_spec_integrate (fun o => (o.getD 10 : Nat)) "
            "(some 5) (none : Option Nat)\n"
            "    (implementation_integrate (fun o => (o.getD 10 : Nat)) (some 5) "
            "(none : Option Nat)) := by\n"
            "  intro h\n"
            "  have h2 := h.2.2 rfl\n"
            "  have hr : implementation_integrate (fun o => (o.getD 10 : Nat)) "
            "(some 5) (none : Option Nat)\n"
            "      = Except.ok (5, true) := rfl\n"
            "  rw [hr] at h2\n"
            "  simp only [Except.ok.injEq, Prod.mk.injEq] at h2\n"
            "  exact absurd h2.2 (by decide)\n"
        ),
    },

    # ---- W3: route the WRONG (absent) selector on the legacy-only call ----
    {
        "id": "w3-wrong-selector",
        "kind": "uniqueness",
        "expect": "reject",
        # Raise the notice correctly, but FORGET to route the legacy selector:
        # leave `effective` at the (absent) primary selector on the legacy arm.
        "module": _swap(_BASE, _I_LEGACY_ARM, "    warned := true"),
        "refinement": "a real patch that raised the notice but dropped the "
                      "`coord = dim` reassignment would integrate along the "
                      "wrong/absent coordinate on the legacy-selector-only call — "
                      "the call would error or integrate along the missing "
                      "selector rather than the one the caller named. The F2P "
                      "call must SUCCEED returning the legacy-selector integral "
                      "(only warning), so it would NOT resolve.",
        "rationale": "REJECT from clause C2 (the routed-selector component): the "
                     "spec pins the honoured value to `integrateAlong dim` (the "
                     "legacy selector) but the rival passes the absent primary "
                     "selector, so the integrated value differs while the notice "
                     "flag agrees. Argument-routing attack. Binder point: "
                     "coord=none, dim=some — DISTINCT from W1 (different legacy "
                     "value) so the two legacy-only rivals probe their own "
                     "points.",
        "witness": (
            "-- Refuted at a legacy-only input: the rival integrates along the\n"
            "-- absent primary selector (integrateAlong none = 3) where C2 demands\n"
            "-- the legacy selector's integral (integrateAlong (some 7) = 7).\n"
            "example : ¬ problem_spec_integrate (fun o => (o.getD 3 : Nat)) "
            "(none : Option Nat) (some 7)\n"
            "    (implementation_integrate (fun o => (o.getD 3 : Nat)) "
            "(none : Option Nat) (some 7)) := by\n"
            "  intro h\n"
            "  have h2 := h.2.1 ⟨rfl, rfl⟩\n"
            "  have hr : implementation_integrate (fun o => (o.getD 3 : Nat)) "
            "(none : Option Nat) (some 7)\n"
            "      = Except.ok (3, true) := rfl\n"
            "  rw [hr] at h2\n"
            "  simp only [Except.ok.injEq, Prod.mk.injEq] at h2\n"
            "  exact absurd h2.1 (by decide)\n"
        ),
    },

    # ---- W4: return normally on the both-supplied input instead of rejecting --
    {
        "id": "w4-no-reject",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the both-supplied rejection guard: on a contradictory call return
        # a normal honoured outcome (routing the primary selector) rather than
        # rejecting.
        "module": _swap(_BASE, _I_REJECT_GUARD, "  let mut effective := coord"),
        "refinement": "a real patch that dropped the both-supplied rejection "
                      "guard would SILENTLY proceed (integrating along the "
                      "primary selector) when a caller supplies BOTH selectors, "
                      "so a contradictory call would be answered instead of "
                      "refused. HONEST SCOPE OF THIS CLAIM (checked against the "
                      "test surface rather than asserted): no test in the F2P or "
                      "P2P set supplies both selectors at once, so this rival is "
                      "not refuted by a test — it is refuted by the specified "
                      "behavior, which requires the contradictory call to be "
                      "rejected. That makes W4 a SPEC-strength case rather than an "
                      "F2P-resolution case, and it belongs in the battery on that "
                      "basis: clause C1 is a load-bearing part of the modeled "
                      "behavior (it is the reason the two spellings can coexist at "
                      "all), and a spec that left it free would admit an impl that "
                      "resolves this instance while silently accepting a call the "
                      "behavior says is contradictory. Do not read this case as "
                      "'would NOT resolve'; the earlier wording claimed a "
                      "pytest.raises on a both-supplied call that the test surface "
                      "does not contain.",
        "rationale": "REJECT from clause C1: on the both-supplied input the spec "
                     "pins `result = Except.error ()` but the rival returns "
                     "`Except.ok`, so the outcome constructor itself differs. "
                     "Control-flow-effect (reject vs return). Binder point: "
                     "coord=some, dim=some — the ONLY rival at the both-supplied "
                     "antecedent.",
        "witness": (
            "-- Refuted at the both-supplied input: the rival returns ok where\n"
            "-- C1 demands error.\n"
            "example : ¬ problem_spec_integrate (fun o => (o.getD 20 : Nat)) "
            "(some 5) (some 3)\n"
            "    (implementation_integrate (fun o => (o.getD 20 : Nat)) (some 5) "
            "(some 3)) := by\n"
            "  intro h\n"
            "  have h2 := h.1 ⟨rfl, rfl⟩\n"
            "  have hr : implementation_integrate (fun o => (o.getD 20 : Nat)) "
            "(some 5) (some 3)\n"
            "      = Except.ok (5, false) := rfl\n"
            "  rw [hr] at h2\n"
            "  exact Except.noConfusion h2\n"
        ),
    },

    # ---- W5: reject every call (over-broad refusal) ----
    {
        "id": "w5-always-reject",
        "kind": "uniqueness",
        "expect": "reject",
        # Reject unconditionally: return `Except.error ()` for every input,
        # including the honoured single-selector calls.
        "module": _swap(_BASE, _IMPL_BODY, "  return Except.error ()"),
        "refinement": "a real patch whose guard rejected on ANY supplied selector "
                      "(or rejected unconditionally) would refuse the ordinary "
                      "honoured calls outright. The F2P call must SUCCEED (only "
                      "warning); an unconditional refusal raises instead of "
                      "returning, so it would NOT resolve.",
        "rationale": "REJECT from clause C3: on the legacy-absent input "
                     "(dim=none, coord supplied) the spec pins an honoured "
                     "`Except.ok` outcome but the rival returns `Except.error`, "
                     "so the outcome constructor differs. Over-broad-refusal / "
                     "control-flow-effect case. Binder point: coord=some, "
                     "dim=none — a distinct legacy-absent point from W2.",
        "witness": (
            "-- Refuted at an honoured legacy-absent input: the rival rejects\n"
            "-- where C3 demands an ok outcome.\n"
            "example : ¬ problem_spec_integrate (fun o => (o.getD 30 : Nat)) "
            "(some 9) (none : Option Nat)\n"
            "    (implementation_integrate (fun o => (o.getD 30 : Nat)) (some 9) "
            "(none : Option Nat)) := by\n"
            "  intro h\n"
            "  have h2 := h.2.2 rfl\n"
            "  have hr : implementation_integrate (fun o => (o.getD 30 : Nat)) "
            "(some 9) (none : Option Nat)\n"
            "      = Except.error () := rfl\n"
            "  rw [hr] at h2\n"
            "  exact Except.noConfusion h2\n"
        ),
    },

    # ---- W6: derive the notice from the PRIMARY selector's absence ----
    # AUDIT ADDITION. The five rivals above leave one input class of the
    # resolution table unattacked: the call with NEITHER selector supplied.
    # Clause C3 reaches it by collapsing two rows into the single antecedent
    # `dim = none`, so a rival that is correct on all three of the OTHER rows and
    # wrong only there was not exercised. This near-miss sources the notice flag
    # from `coord.isNone` rather than from the legacy selector's presence: the two
    # agree on both-supplied (rejected before the flag is read), on legacy-only
    # (coord absent -> true, correct) and on primary-only (coord present ->
    # false, correct), and disagree ONLY on the neither-supplied call, where the
    # rival raises a spurious notice. The tightest wrong impl in the battery.
    {
        "id": "w6-warn-on-absent-primary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ARM_AND_RETURN,
            "  if dim.isSome && coord.isNone then\n"
            "    effective := dim\n"
            "  return Except.ok (integrateAlong effective, coord.isNone)",
        ),
        "refinement": "a real patch that conditioned the deprecation notice on "
                      "the PRIMARY selector being omitted (rather than on the "
                      "legacy one being supplied) warns on the bare call that "
                      "names no coordinate at all — a call that selects nothing "
                      "and uses no deprecated spelling, so it has nothing to be "
                      "warned about. It agrees with the correct behavior on every "
                      "call that DOES name a coordinate, so the F2P assertion "
                      "still passes; the P2P surface is where it breaks, since a "
                      "notice on a call that used no legacy spelling is a false "
                      "deprecation report to the caller. HONEST SCOPE (same check "
                      "as W2): the project's pytest config does not promote "
                      "warnings to errors globally, so this is a "
                      "specified-behavior refutation — the notice must fire on "
                      "EXACTLY the legacy-selector call — and not a claim that a "
                      "named test goes red.",
        "rationale": "REJECT from clause C3: on the neither-supplied input "
                     "(dim=none, coord=none) the spec pins `warned = false` but "
                     "the rival returns `warned = true`, so `result` differs. "
                     "Partial-domain, and the NARROWEST one in the battery — the "
                     "rival is observationally identical to the frozen impl on "
                     "the other three rows of the resolution table. Binder point: "
                     "coord=none, dim=none — the one input class W1–W5 never "
                     "reach.",
        "witness": (
            "-- Refuted at the neither-supplied input (both selectors absent):\n"
            "-- the rival raises the notice where C3 demands warned=false. This is\n"
            "-- the sub-row C3 collapses, so no other witness lands here.\n"
            "example : ¬ problem_spec_integrate (fun o => (o.getD 4 : Nat)) "
            "(none : Option Nat) (none : Option Nat)\n"
            "    (implementation_integrate (fun o => (o.getD 4 : Nat)) "
            "(none : Option Nat) (none : Option Nat)) := by\n"
            "  intro h\n"
            "  have h2 := h.2.2 rfl\n"
            "  have hr : implementation_integrate (fun o => (o.getD 4 : Nat)) "
            "(none : Option Nat) (none : Option Nat)\n"
            "      = Except.ok (4, true) := rfl\n"
            "  rw [hr] at h2\n"
            "  simp only [Except.ok.injEq, Prod.mk.injEq] at h2\n"
            "  exact absurd h2.2 (by decide)\n"
        ),
    },

    # ---- W7: refuse the legacy spelling outright instead of honour-and-warn ----
    # AUDIT ADDITION (second pass). The clause x component table in the module
    # docstring had exactly one blank cell: C2's ok/error CONSTRUCTOR axis. W1 and
    # W3 both attack C2, but both hand the rival an honoured `ok` outcome and
    # disagree only about what is INSIDE it (the flag; the routed selector), so
    # neither establishes that C2 forces an honoured outcome at all rather than
    # merely constraining the payload of one. W5 does attack the constructor, but
    # it rejects unconditionally and its witness lands on the legacy-ABSENT row, so
    # it says nothing about C2 specifically.
    #
    # This rival widens the rejection guard from "both supplied" to "the legacy
    # selector supplied", i.e. it refuses the deprecated spelling instead of
    # honouring it with a notice. That is the conservative misreading of a
    # deprecation a real author is most likely to make (refuse the old spelling
    # rather than accept-and-warn), and it is correct on both of the other rows it
    # can reach: the primary-only and neither-supplied calls are honoured exactly
    # as the frozen impl honours them. Wrong on exactly one axis of exactly one
    # clause.
    {
        "id": "w7-refuse-legacy-spelling",
        "kind": "uniqueness",
        "expect": "reject",
        # Widen the guard: reject whenever the legacy selector is present, rather
        # than only when BOTH selectors are. The legacy arm below is then dead.
        "module": _swap(
            _BASE, _I_REJECT_GUARD,
            "  if dim.isSome then\n"
            "    return Except.error ()\n"
            "  let mut effective := coord",
        ),
        "refinement": "a real patch that treated the deprecated spelling as no "
                      "longer accepted — refusing the call rather than honouring "
                      "it and emitting the notice — turns the legacy-selector call "
                      "into an error. The F2P scenario requires that exact call to "
                      "SUCCEED (returning the integral along the named coordinate) "
                      "while merely warning; a refusal raises instead of "
                      "returning, so the F2P assertion fails and the patch would "
                      "NOT resolve. Unlike W2/W4/W5 this claim needs no appeal to "
                      "warning filters or to untested input classes: it is refuted "
                      "by the F2P call itself, which is why this case is the "
                      "strongest resolution-grounded rival in the battery.",
        "rationale": "REJECT from clause C2 (the outcome CONSTRUCTOR component): on "
                     "the legacy-only input the spec pins an honoured "
                     "`Except.ok (integrateAlong dim, true)` but the rival returns "
                     "`Except.error ()`, so the constructor itself differs. This is "
                     "the one clause x component cell W1-W6 leave blank — W1 and W3 "
                     "attack C2's payload only (flag, routed value) and W5's "
                     "constructor attack lands on C3 — so before this case nothing "
                     "established that C2 demands an honoured outcome at all. "
                     "Over-broad-refusal, narrowed to the legacy spelling: NOT "
                     "subsumed by W5, since this rival honours the primary-selector "
                     "call correctly and is wrong only where the deprecated "
                     "spelling is used. Binder point: coord=none, dim=some 6 — "
                     "distinct from W1 (some 3) and W3 (some 7), and "
                     "`integrateAlong` instantiated at `getD 8`, a k no other "
                     "witness uses.",
        "witness": (
            "-- Refuted at a legacy-only input: the rival REJECTS the call where C2\n"
            "-- demands an honoured `ok` outcome. The `rfl` below is a plain\n"
            "-- evaluation of a closed term, so it succeeds against the rival and\n"
            "-- fails on the frozen solution with a concrete mismatch naming the\n"
            "-- value claimed — the failure tracks the claim, not the carrier.\n"
            "example : ¬ problem_spec_integrate (fun o => (o.getD 8 : Nat)) "
            "(none : Option Nat) (some 6)\n"
            "    (implementation_integrate (fun o => (o.getD 8 : Nat)) "
            "(none : Option Nat) (some 6)) := by\n"
            "  intro h\n"
            "  have h2 := h.2.1 ⟨rfl, rfl⟩\n"
            "  have hr : implementation_integrate (fun o => (o.getD 8 : Nat)) "
            "(none : Option Nat) (some 6)\n"
            "      = Except.error () := rfl\n"
            "  rw [hr] at h2\n"
            "  exact Except.noConfusion h2\n"
        ),
    },

    # ---- W8: route the LEGACY selector on every honoured call --------------
    # AUDIT ADDITION (second pass). The clause x component table above claimed
    # every clause was attacked in every direction its outcome can fail, and one
    # cell was still blank: C3's VALUE component. Every rival that reached C3
    # attacked the outcome's shell rather than the routed selector — W2 and W6
    # flip only the notice flag, W5 swaps the whole honoured outcome for a
    # rejection — so nothing established that C3 pins `integrateAlong coord`
    # rather than merely `integrateAlong <anything>` paired with `false`. The
    # routed-selector obligation was demonstrated on the legacy-only clause (W3)
    # and simply assumed on the legacy-absent one, which is the clause carrying
    # the ordinary non-deprecated call.
    #
    # This rival keeps the notice logic EXACTLY right and hands the downstream
    # step the legacy selector unconditionally. On the both-supplied row it is
    # rejected before the routing is read; on the legacy-only row routing the
    # legacy selector is correct and the notice fires, so it agrees with the
    # frozen impl there too. It diverges only on the legacy-ABSENT rows, where it
    # integrates along the absent legacy selector instead of the primary one the
    # caller named — the exact mirror of W3, on the other honoured clause.
    {
        "id": "w8-route-legacy-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_EFFECTIVE_AND_RETURN,
            "  let mut warned := false\n"
            "  if dim.isSome && coord.isNone then\n"
            "    warned := true\n"
            "  return Except.ok (integrateAlong dim, warned)",
        ),
        "refinement": "a real patch that resolved the coordinate by always "
                      "handing the downstream step the legacy keyword — for "
                      "instance by copying the resolution in the wrong direction, "
                      "so the legacy name is what is threaded through rather than "
                      "the primary one — integrates along nothing on the ordinary "
                      "call that names the coordinate the preferred way. The P2P "
                      "surface calls the operation through the PRIMARY selector "
                      "(the units-test computation cases invoke it that way) and "
                      "expects the integral along the coordinate it named; this "
                      "rival passes the absent legacy selector instead, so the "
                      "downstream step receives no coordinate and the ordinary "
                      "call cannot return the right result. It would NOT resolve, "
                      "and unlike W2/W4/W6 the claim needs no appeal to warning "
                      "filters or untested input classes: the value the honoured "
                      "call returns is wrong on a row the kept tests exercise.",
        "rationale": "REJECT from clause C3 (the routed-selector VALUE "
                     "component): on the legacy-absent input the spec pins the "
                     "honoured value to `integrateAlong coord` (the primary "
                     "selector) but the rival passes the absent legacy selector, "
                     "so the integrated value differs while the notice flag "
                     "agrees. The MIRROR of W3, which makes the same "
                     "argument-routing attack on C2; before this case C3's value "
                     "axis was the one blank cell in the coverage table. Binder "
                     "point: coord=some 11, dim=none — a third distinct "
                     "legacy-absent point (W2 uses some 5, W5 some 9), with "
                     "`integrateAlong` at `getD 40`, a k no other witness uses.",
        "witness": (
            "-- Refuted at a primary-only input: the rival integrates along the\n"
            "-- absent legacy selector (integrateAlong none = 40) where C3 demands\n"
            "-- the primary selector's integral (integrateAlong (some 11) = 11).\n"
            "-- The notice flag agrees on this row, so only the VALUE component\n"
            "-- separates the two — which is the cell this case exists to fill.\n"
            "example : ¬ problem_spec_integrate (fun o => (o.getD 40 : Nat)) "
            "(some 11) (none : Option Nat)\n"
            "    (implementation_integrate (fun o => (o.getD 40 : Nat)) (some 11) "
            "(none : Option Nat)) := by\n"
            "  intro h\n"
            "  have h2 := h.2.2 rfl\n"
            "  have hr : implementation_integrate (fun o => (o.getD 40 : Nat)) "
            "(some 11) (none : Option Nat)\n"
            "      = Except.ok (40, false) := rfl\n"
            "  rw [hr] at h2\n"
            "  simp only [Except.ok.injEq, Prod.mk.injEq] at h2\n"
            "  exact absurd h2.1 (by decide)\n"
        ),
    },
]

# No AXIOM lane here: the downstream integration is a universally-quantified
# parameter (an A-reference), not a consumed `axiom`; the bundle declares no
# `opaque` and consumes no `axiom`. The nagini AXIOM_TESTS were also empty;
# dropped.
AXIOM_TESTS = []

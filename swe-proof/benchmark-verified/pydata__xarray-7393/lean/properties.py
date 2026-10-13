"""G-PBT manifest for pydata__xarray-7393 (lean) — adversarial falsification.

A port of the nagini sibling's spec lane, re-expressed against this bundle's
carrier. Not a Lean module: a record of adversarial cases the G-PBT gate
executes. Every SPEC_TESTS case is a full `Solution.lean` variant that shares
the FROZEN spec byte-for-byte (only the `impl` region — and, where a positive
must reprove, the `proof` region — is edited), so `markers.same_spec` holds by
construction and any verdict is attributable to the postcondition rather than
to a tampered spec.

DEFENDED SURFACE
================

ONE modeled obligation: `theorem correct_arrayConvert`, over

    implementation_arrayConvert
      (selfDtype   : Dtype)            -- the wrapper's stored original element type
      (dtypeArg    : Option Dtype)     -- the optionally requested element type
      (level       : Option Level)     -- selected labelled level, or none
      (rawArray    : NpArray)          -- the raw level value array (its own `dtype`
                                       --   may have been widened; the values have not)
      (superArray  : Dtype → NpArray)  -- the non-level conversion, as a function of
                                       --   the effective element type
      : NpArray

The postcondition is a single total functional equation:

    result = (match level with
              | some _ => castArray (effectiveDtype selfDtype dtypeArg) rawArray.data
              | none   => superArray (effectiveDtype selfDtype dtypeArg))

Read as four INDEPENDENT load-bearing commitments, each attacked below:

  (A) SELECTED-LEVEL ELEMENT TYPE. For `level = some _` the result's `dtype` is
      `effectiveDtype selfDtype dtypeArg`. Crucially `rawArray.dtype` does NOT
      occur anywhere in the postcondition, so the spec FORBIDS the result from
      advertising the raw array's own (possibly widened) element type. This is
      the discriminating clause — it is what separates the resolving behavior
      from the behavior the reported issue describes.
      Attacked by: `weak-raw-type-leak`, `nearmiss-default-leaks-raw-type`.

  (B) THE EFFECTIVE-TYPE RESOLUTION. `effectiveDtype selfDtype dtypeArg =
      dtypeArg.getD selfDtype` pins BOTH arms: an explicit request wins, and
      absent one the stored original is used. `effectiveDtype` is a grounded
      pure helper (fully unfolded over the arguments, no opaque answer key), so
      there is nothing for a rival to echo without doing the work.
      Attacked by: `partial-ignore-requested` (some-arm), and (A)'s rivals plus
      `weak-none-branch-selfdtype` (none-arm).

  (C) VALUE PRESERVATION. `castArray` carries `rawArray.data` through unchanged,
      so the result's `data` is exactly the raw level values — same length, same
      order, same elements. All three of those are independent: a rival can get
      the length right and the order wrong, or both right and one element wrong.
      Attacked on length by: `value-extra-element`, `value-drop-last`; on ORDER
      by `value-permute-order` (length- and multiset-preserving); on ELEMENT
      IDENTITY by `value-clamp-negatives` (length- and order-preserving).
      Attacked additionally by two SPARSE rivals, `value-rewrite-large` and
      `value-permute-long-only`, tuned to agree with gold at every other witness
      point in the battery (all of which carry values in [-3, 9] in lists of
      length <= 2) and to diverge only at a large value / a length-3 list. They
      demonstrate the commitment is pinned over the WHOLE carrier and not merely
      on the sub-domain the other witnesses sample — an evasion a battery of
      dense rivals alone cannot rule out.

  (D) BRANCH SELECTION, and the level's IRRELEVANCE BEYOND selected-vs-not. The
      `some`/`none` split must follow `level`, and the `some` arm must be
      identical for EVERY selected level: `level`'s identity is bound by the
      spec but never consulted, so no result may depend on it.
      Attacked by: `branch-ignore-level` (branch selection),
      `partial-level-identity` (identity-independence).

There is no `Prop`-level precondition: `correct_arrayConvert` is a bare
`∀`-statement with no hypothesis binder, and every input type is inhabited, so
the obligation is total over the carrier.

WITNESSES
=========

On a tactic-proof backend "did not verify" is the DEFAULT outcome of reshaping
an impl — the frozen script (`cases dtypeArg <;> cases level <;> rfl`) is tuned
to the frozen impl's syntactic form — so a merely-reshaped correct impl fails
identically to a divergent one. Every `expect="reject"` case therefore carries a
`witness`: a snippet asserting `¬ problem_spec_arrayConvert …` at one CONCRETE
input, closed by `decide`. The whole carrier is `decide`-able here (`Dtype` and
`Level` are `Nat`, `NpArray` derives `DecidableEq`, `superArray` is supplied as
a literal `fun`), so no witness needs to condition on an opaque term and none
binds a hypothesis — there are no assumptions that could be inconsistent.

Every witness below was built against the rival (must elaborate) and against
the frozen solution (must fail) before shipping; all twelve discriminate, and
each gold-side failure is a SEMANTIC refutation (`decide` reduces fully and
reports the negated claim false at the literal point) rather than an unknown
name or a stuck reduction.

Each was additionally checked to be a CLAIM-TRACKING discriminator, not merely a
failing build: for every witness, the same snippet with its `¬` dropped — i.e.
asserting the impl IS correct at that point — was built against both subjects,
and both exit codes INVERT (gold 1→0, rival 0→1). So gold's exit code carries
information about what the witness claims, which is what distinguishes a
refutation from a build that fails for a syntactic reason at every claim.

BINDER COVERAGE
===============

The twelve witnesses probe twelve DISTINCT input points and every input binder
is moved across them, so no rival could have escaped by mishandling a binder the
battery holds fixed (listed in manifest order):

  selfDtype   : 8, 1, 9, 1, 1, 4, 6, 2, 3, 5, 5, 3
  dtypeArg    : some 5, none, some 5, some 5, none, none, none, none, none,
                none, none, none
  level       : some 3, some 4, some 1, none, none, some 0, some 3, some 3,
                some 2, some 1, some 1, some 2
  rawArray    : {2,[7,9]}, {2,[7,9]}, {5,[3]}, {2,[7,9]}, {2,[7,9]}, {2,[7,9]},
                {6,[]}, {2,[7,9]}, {3,[7,9]}, {5,[-3,2]}, {5,[200]},
                {3,[7,9,11]}
  superArray  : d↦{d,[]}, d↦{d,[]}, d↦{d,[]}, d↦{d,[]}, d↦{d,[5]}, d↦{d,[]},
                _↦{0,[4]}, _↦{0,[]}, d↦{d,[]}, d↦{d,[]}, d↦{d,[]}, d↦{d,[]}

Note in particular that `rawArray.dtype` is probed both DIFFERENT from the
effective type (the widened case, e.g. raw `2` against effective `5`) and EQUAL
to it (`partial-ignore-requested`, raw `5` = effective `5`), so a rival cannot
hide in the sub-domain where the raw type happens to already be right. The
`data` binder is likewise moved off the non-negative, length-≥2, non-palindromic
default: an EMPTY list (`value-extra-element`), a singleton (`partial-ignore-
requested`), a list carrying a NEGATIVE value (`value-clamp-negatives`), a LARGE
value (`value-rewrite-large`) and a length-3 list (`value-permute-long-only`),
so the three independent halves of clause (C) — length, order, element identity
— are each demonstrated at a point where the other two agree with gold, and each
of order and element identity is demonstrated twice: once densely and once at a
point tuned to evade every other witness in the battery.

PORTED / OMITTED
================

Ported from nagini: both soundness positives (branch reorder, resolve via the
shared pure helper) plus a third, stronger positive that reshapes the selected-
level arm into a conditional and reproves it; the ADMISSIBILITY positive,
re-expressed for a total carrier (see below); the element-type-leak rival, the
ignore-the-requested-type rival, and both value-corruption rivals. Added here
because this carrier models them and nagini's does not: the none-branch
resolution rival, the branch-selection rival, the level-identity rival, a
near-miss that agrees with gold on the requested-given sub-domain, the order
and element-identity rivals that complete clause (C), and two SPARSE value
rivals tuned to evade every other witness point in the battery.

Omitted, with reasons (see the submission assessment for the full argument):

  * nagini's two FRAME-MUTATION rivals (`frame-mutate-append`,
    `frame-mutate-index-store`). Those are rejected by fractional permissions:
    a read-only input held at a half predicate cannot be written. Lean is
    referentially transparent — there is no aliasing, no permission, and
    `rawArray` cannot be mutated by any expressible impl — so the class is
    VACUOUS on this carrier, not merely hard. DEMONSTRATED rather than asserted:
    the nearest expressible analogue, an impl that rebinds a LOCAL copy of the
    input (`let mut ra := rawArray; ra := { ra with data := ra.data ++ [0] }`)
    before returning the gold result, still VERIFIES under the frozen tactic
    script — the write is unobservable, so there is no rejection here to
    attribute to anything, and a case built on it would be a mislabeled
    positive. Its content (the source values are not disturbed) is what clause
    (C) already pins from the result side, and (C) is attacked by six rivals
    covering length, order, and element identity — the last two both densely and
    at a point tuned to evade the rest of the battery.
  * nagini's AXIOM_TESTS. The axiom lane is G-AX's job and this gate ignores it;
    this bundle declares no callee axiom in any case.

nagini's ADMISSIBILITY case (`admiss-precond-halfperm`) is PORTED, not omitted,
as `admiss-ground-f2p-point`. Its nagini form asserts a read-only
half-permission is in hand at entry, and this carrier has no permission system
and no hypothesis binder to satisfy — but "the frozen obligation has no
precondition" is NOT a reason to drop the lane. The lane exists to detect
PRECOND-TOO-STRONG, whose analogue on a total carrier is the obligation being
UNSATISFIABLE at exactly an F2P-shaped input, and a positive that discharges the
obligation at that concrete input BY EVALUATION tests that directly. So the case
fixes the F2P-shaped point (narrow stored original, no requested type, a selected
level, a widened raw array), discharges the spec there as a `have`, and then
closes the frozen obligation verbatim. It is not a relabelled soundness positive:
the three soundness cases quantify and reshape the impl, whereas this one keeps
the frozen impl and evaluates the spec at a ground point. It is load-bearing —
the ground `have` asserting the raw array's widened element type instead of the
effective one is REFUTED by `decide` at that same point.

There is NO divergence / non-termination rival in the nagini sibling, so nothing
of that class is dropped. Had there been one it would be vacuous here rather
than a known hole: `implementation_arrayConvert` is a total Lean `def`, so a
diverging implementation cannot be written at all (contrast velvet under
`loom.semantics.termination "partial"`, where such a rival verifies vacuously —
the corpus-wide termination-semantics finding).
"""
from pathlib import Path

INSTANCE = "pydata__xarray-7393"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. `_IMPL` is the whole body of the frozen `impl` region (everything
# after the `:= Id.run do` line, up to `-- impl-end`); `_PROOF` is the whole
# tactic body of the frozen `proof` region. Both lie ENTIRELY inside the region
# they name and both are unique in the file, so every _swap below is confined to
# the impl region — plus, for the one positive that reshapes the selected-level
# arm, the proof region it must legitimately reprove.
# ---------------------------------------------------------------------------
_IMPL = (
    "  -- Default the requested data type to the wrapper's stored original.\n"
    "  let mut dtype := dtypeArg\n"
    "  if dtype.isNone then\n"
    "    dtype := some selfDtype\n"
    "  let d := dtype.getD selfDtype\n"
    "  match level with\n"
    "  | some _ =>\n"
    "      -- A selected level: re-present the raw level values at the effective type.\n"
    "      return castArray d rawArray.data\n"
    "  | none   =>\n"
    "      -- No selected level: defer to the underlying non-level conversion.\n"
    "      return superArray d"
)

_PROOF = (
    "  unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype\n"
    "  cases dtypeArg <;> cases level <;> rfl"
)

# The frozen proof's `intro` line, unique in the file and wholly inside the proof
# region, so the admissibility positive can PREPEND a ground `have` without
# touching the `theorem correct_arrayConvert` statement or the spec view.
_P_INTRO = "  intro selfDtype dtypeArg level rawArray superArray"

assert _BASE.count(_IMPL) == 1, "impl anchor drifted"
assert _BASE.count(_PROOF) == 1, "proof anchor drifted"
assert _BASE.count(_P_INTRO) == 1, "proof intro anchor drifted"


def _impl(body):
    """A variant that edits ONLY the impl region (frozen proof carried over)."""
    return _swap(_BASE, _IMPL, body)


def _impl_proof(body, proof):
    """A variant that edits the impl region and reproves the SAME obligation.

    Only the tactic body changes; the `theorem correct_arrayConvert` statement
    stays byte-identical, so the obligation survives intact.
    """
    return _swap(_swap(_BASE, _IMPL, body), _PROOF, proof)


def _witness(selfDtype, dtypeArg, level, rawArray, superArray):
    """`¬ problem_spec_arrayConvert <point> (implementation_arrayConvert <point>)`.

    The spec is applied directly at a literal point and closed by `decide`: the
    rival's own result is fed in as the `result` argument, so the snippet says
    exactly "at this input the rival's output is not what the spec demands".
    It elaborates against a rival that diverges here and FAILS against the
    frozen solution, which satisfies the spec everywhere.
    """
    point = (f"{selfDtype} {dtypeArg} {level}\n"
             f"    {rawArray} ({superArray})")
    return (f"example : ¬ problem_spec_arrayConvert {point}\n"
            f"    (implementation_arrayConvert {point}) := by\n"
            "  unfold problem_spec_arrayConvert implementation_arrayConvert\n"
            "  decide")


_SUP_ID = "fun d => { dtype := d, data := [] }"


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): resolve the effective type by cases -----
    # Gold resolves with a mutable default (`let mut dtype := dtypeArg; if
    # dtype.isNone then …; dtype.getD selfDtype`). Here the same value is
    # obtained by a direct `match` on the optional request. `effectiveDtype
    # selfDtype dtypeArg = dtypeArg.getD selfDtype` agrees with this on both
    # arms and on every input, so the frozen tactic script still closes: a pure
    # reshape with no proof gap. MUST verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-resolve-by-cases",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "  -- Resolve the effective data type by cases on whether one was requested.\n"
            "  let d := match dtypeArg with\n"
            "           | some t => t\n"
            "           | none   => selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray d rawArray.data\n"
            "  | none   =>\n"
            "      return superArray d"),
        "rationale": "a behaviourally identical reshape: the effective element type "
                     "is resolved by a direct case split on the optional request "
                     "instead of by defaulting a mutable binding, which agrees with "
                     "`dtypeArg.getD selfDtype` on both arms at every input. Both "
                     "postcondition arms and every clause (A)-(D) are untouched, and "
                     "the frozen tactic body still closes the obligation. If this were "
                     "rejected the spec would be pinning an incidental syntactic shape "
                     "rather than the behavior (SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): resolve via the shared pure helper ------
    # `effectiveDtype` is the spec's OWN spelling of the resolution and is in
    # scope for the impl. Calling it directly is the cheapest correct impl. This
    # is the honest analogue of nagini's "cheapest impl" control: the helper is
    # fully grounded in the arguments (no opaque answer key), so calling it IS
    # doing the work, not echoing an oracle. MUST verify.
    {
        "id": "pos-effective-type-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "  -- Resolve the effective data type with the shared helper.\n"
            "  let d := effectiveDtype selfDtype dtypeArg\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray d rawArray.data\n"
            "  | none   =>\n"
            "      return superArray d"),
        "rationale": "the shared pure helper is the spec's own spelling of the "
                     "effective-type resolution, and it is in scope for the impl; "
                     "computing the effective type by calling it is the cheapest "
                     "CORRECT impl and must verify (else SPEC-TOO-STRONG). It is not "
                     "an oracle echo: the helper is fully unfolded over the arguments "
                     "with no opaque answer key, so calling it is doing the work. "
                     "Defends clause (B) from the other side — the resolution the spec "
                     "names is satisfiable by an impl that computes exactly it.",
    },

    # -- POSITIVE CONTROL (soundness): skip a redundant re-presentation --------
    # Structurally the most different correct impl: when the raw array ALREADY
    # carries the effective element type, return it as-is; otherwise re-present.
    # Correct because `castArray d rawArray.data = rawArray` exactly when
    # `rawArray.dtype = d` (NpArray has only the two fields), so both branches
    # agree with the postcondition. The frozen `rfl` cannot see through the
    # conditional, so this positive REPROVES the identical obligation statement
    # with a new tactic body (`split` + the equality hypothesis). This is the
    # case that shows the spec constrains the OBSERVABLE result and not the
    # route taken to it.
    {
        "id": "pos-skip-redundant-cast",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      -- Already carrying the effective type: nothing to re-present.\n"
            "      if rawArray.dtype == d then\n"
            "        return rawArray\n"
            "      else\n"
            "        return castArray d rawArray.data\n"
            "  | none   =>\n"
            "      return superArray d",
            "  unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype\n"
            "  cases level with\n"
            "  | none => rfl\n"
            "  | some l =>\n"
            "    simp only [Id.run]\n"
            "    split\n"
            "    · next h =>\n"
            "        simp only [beq_iff_eq] at h\n"
            "        simp only [castArray, ← h]\n"
            "        rfl\n"
            "    · rfl"),
        "rationale": "a structurally different CORRECT impl: the selected-level arm "
                     "short-circuits when the raw array already carries the effective "
                     "element type, and re-presents the values otherwise. Both branches "
                     "satisfy the postcondition, since an array whose element type "
                     "already equals the effective one is componentwise equal to the "
                     "re-presented array (the carrier has only the two observed "
                     "fields). The frozen `rfl` cannot see through the conditional, so "
                     "the obligation is REPROVEN with a new tactic body while the "
                     "`theorem correct_arrayConvert` statement stays byte-identical — "
                     "no weakening, no helper lemma. This is the strongest available "
                     "check that the spec pins the observable result rather than the "
                     "syntactic route to it; a rejection would be SPEC-TOO-STRONG.",
    },

    # -- ADMISSIBILITY: the obligation is SATISFIABLE at an F2P-shaped input ----
    # The analogue, on a total carrier, of nagini's precondition-admission case.
    # `correct_arrayConvert` carries no `Prop`-level hypothesis, so "the
    # precondition is too strong" cannot arise as a hypothesis that fails to hold
    # — but the SAME failure mode does arise as the obligation being
    # UNSATISFIABLE at exactly a normal, F2P-shaped input. That is what this case
    # tests directly: discharge the spec predicate BY EVALUATION at the concrete
    # F2P-shaped point (a narrow stored original type, NO requested type — the
    # call shape the FAIL_TO_PASS tests drive — a selected level, and a raw value
    # array whose own element type has been widened away from the original), as a
    # `have`, and then close the frozen obligation verbatim.
    #
    # Load-bearing rather than decorative, and DEMONSTRATED so: the second `have`
    # pins the ground result to the EFFECTIVE type (1) with the raw values
    # carried through. The same `have` asserting the raw array's widened type (2)
    # instead is REFUTED by `decide` at this point, so the ground instance
    # genuinely exhibits the discriminating clause at the F2P shape and does not
    # merely restate the theorem. Nothing is assumed: no new declaration, no new
    # axiom, statement byte-identical, and the ground instance is a `have`
    # prepended to the existing tactic body.
    {
        "id": "admiss-ground-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_arrayConvert 1 none (some 0)\n"
            "      { dtype := 2, data := [7, 9] } "
            "(fun d => { dtype := d, data := [] })\n"
            "      (implementation_arrayConvert 1 none (some 0)\n"
            "        { dtype := 2, data := [7, 9] } "
            "(fun d => { dtype := d, data := [] })) := by\n"
            "    unfold problem_spec_arrayConvert implementation_arrayConvert\n"
            "    decide\n"
            "  have _ground_value : implementation_arrayConvert 1 none (some 0)\n"
            "      { dtype := 2, data := [7, 9] } "
            "(fun d => { dtype := d, data := [] })\n"
            "      = { dtype := 1, data := [7, 9] } := by\n"
            "    unfold implementation_arrayConvert\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged BY EVALUATION at a concrete "
                     "F2P-shaped input — stored original element type 1, NO "
                     "requested type (the call shape the FAIL_TO_PASS tests "
                     "drive), a selected level, and a raw value array whose own "
                     "element type has been widened to 2 — as a `have`, after "
                     "which the frozen obligation is closed verbatim. This is the "
                     "analogue of PRECOND-TOO-STRONG on a total carrier: the "
                     "frozen theorem has no hypothesis binder that could be too "
                     "strong, but the obligation could still be UNSATISFIABLE at "
                     "exactly a normal input, and that is what this case refutes. "
                     "It is not a relabelled soundness positive: it fixes a "
                     "concrete point and evaluates the spec there rather than "
                     "quantifying, and the second `have` pins the ground result to "
                     "the EFFECTIVE type with the raw values carried through. That "
                     "`have` is load-bearing — asserting the raw array's widened "
                     "element type instead is refuted by `decide` at this very "
                     "point — so the ground instance exhibits the discriminating "
                     "clause at the F2P shape. Nothing is assumed: no new "
                     "declaration or axiom, statement byte-identical, `have` "
                     "prepended to the existing tactic body.",
    },

    # -- RAW-TYPE LEAK (uniqueness): return the raw level array verbatim -------
    # The port of nagini's `weak-storage-leak`, and the direct analogue of this
    # bundle's own prepatch: for a selected level the raw value array is handed
    # back untouched, so the result advertises the raw array's own (possibly
    # widened) element type instead of the effective one. Refuted wherever
    # rawArray.dtype != effectiveDtype selfDtype dtypeArg. The witness picks the
    # requested-given arm (dtypeArg = some 5, raw dtype 2) so it is refuted by
    # clause (A) alone and not by any accident of the defaulting.
    {
        "id": "weak-raw-type-leak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return rawArray\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("8", "(some 5)", "(some 3)",
                            "{ dtype := 2, data := [7, 9] }", _SUP_ID),
        "refinement": "handing the selected level's raw value array straight back is "
                      "exactly the behavior the reported issue describes: the array "
                      "then reports whatever element type the underlying machinery gave "
                      "it, which for a narrow original type is a widened one. The "
                      "FAIL_TO_PASS tests assert that the value array's reported "
                      "element type still equals the original narrow one after a level "
                      "is built, and this behavior returns the widened type instead, so "
                      "both parametrisations keep failing. A faithful real version of "
                      "this rival therefore does NOT resolve.",
        "rationale": "rejected by clause (A): the postcondition demands `result = "
                     "castArray (effectiveDtype selfDtype dtypeArg) rawArray.data` for "
                     "a selected level, and `rawArray.dtype` does not occur in the "
                     "postcondition at all, so returning the raw array is refuted "
                     "wherever its element type differs from the effective one. The "
                     "witness sits at selfDtype=8, dtypeArg=some 5, level=some 3, "
                     "rawArray.dtype=2: the effective type is 5, the rival reports 2. "
                     "If this verified the spec would admit the reported behavior — "
                     "SPEC-TOO-WEAK, and the whole discriminating clause would be "
                     "unpinned.",
    },

    # -- NEAR-MISS (uniqueness): honour a request, leak the raw type otherwise -
    # Strictly closer to gold than the rival above: it re-presents correctly
    # whenever a type IS requested, and leaks the raw type only on the
    # no-request arm. That is precisely the sub-domain the FAIL_TO_PASS tests
    # drive, so it needs its OWN witness at dtypeArg = none — the raw-type-leak
    # witness above (dtypeArg = some 5) does not refute it, since the two rivals
    # agree with gold on different halves of the domain.
    {
        "id": "nearmiss-default-leaks-raw-type",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      match dtypeArg with\n"
            "      | some t => return castArray t rawArray.data\n"
            "      | none   => return rawArray\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("1", "none", "(some 4)",
                            "{ dtype := 2, data := [7, 9] }", _SUP_ID),
        "refinement": "this rival honours an explicitly requested element type and "
                      "diverges only when none is requested — which is exactly the "
                      "call shape the FAIL_TO_PASS tests exercise (they read the value "
                      "array with no explicit request and compare its reported element "
                      "type against the original narrow one). On that arm it returns "
                      "the raw, possibly widened array, so the tests still fail and a "
                      "faithful real version does not resolve. It is a NEAR-MISS, not "
                      "an equivalent: it agrees with gold on the requested-given "
                      "sub-domain, which is why it carries its own witness rather than "
                      "sharing the raw-type-leak one.",
        "rationale": "rejected by clause (A) on the no-request arm, together with the "
                     "`none` arm of the resolution (B): with dtypeArg=none the "
                     "effective type is selfDtype=1, but the rival returns the raw "
                     "array reporting 2. The witness is placed at dtypeArg=none, "
                     "level=some 4, deliberately DIFFERENT from the raw-type-leak "
                     "witness's dtypeArg=some 5 — the sub-domain this rival claims to "
                     "be wrong on is the one the manifest demonstrates it on. If it "
                     "verified, the defaulting arm of the resolution would be unpinned "
                     "for a selected level (SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): ignore the requested type ----------------
    # The port of nagini's `partial-ignore-requested`: always resolve to the
    # stored original, discarding an explicit request. Correct on the
    # no-request sub-domain (where the effective type IS the stored original),
    # divergent whenever a request is given and differs. The witness also
    # exercises the case rawArray.dtype == effectiveDtype: the rival is refuted
    # even where the raw type happens to already be the right one, so it cannot
    # hide behind the raw array.
    {
        "id": "partial-ignore-requested",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray selfDtype rawArray.data\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("9", "(some 5)", "(some 1)",
                            "{ dtype := 5, data := [3] }", _SUP_ID),
        "refinement": "always resolving to the wrapper's stored original element type "
                      "discards the caller's explicit request, so the conversion no "
                      "longer honours the type it was asked for. A conversion entry "
                      "point that ignores its own requested-type argument is not the "
                      "resolving change: it is behaviourally unequal to gold on every "
                      "call that supplies a type, and that argument is part of the "
                      "public conversion protocol the wrapper implements — a caller who "
                      "asks for a type and is silently handed another has no way to "
                      "detect it. The requested-type argument is the ONLY reason the "
                      "parameter exists, so an implementation free to ignore it is not "
                      "an implementation of this entry point. (The claim here is "
                      "behavioural inequality with gold on the explicit-request "
                      "sub-domain, which is what makes this a non-resolving rival; it "
                      "is deliberately NOT a claim that some named test in the suite "
                      "exercises that sub-domain — the FAIL_TO_PASS tests drive the "
                      "no-request arm, and this manifest does not assert a "
                      "PASS_TO_PASS test it has not identified.)",
        "rationale": "rejected by the some-arm of the resolution (B): the "
                     "postcondition's element type is `dtypeArg.getD selfDtype`, which "
                     "is the REQUESTED type whenever one is supplied, so the rival is "
                     "refuted wherever the request differs from the stored original. "
                     "The witness sits at selfDtype=9, dtypeArg=some 5 — and "
                     "deliberately at rawArray.dtype=5, EQUAL to the effective type, so "
                     "the refutation is attributable to the discarded request alone and "
                     "the battery probes the raw-type-agrees sub-domain too. If it "
                     "verified, the requested-type arm would be unpinned "
                     "(SPEC-TOO-WEAK).",
    },

    # -- NONE-BRANCH (uniqueness): pass the stored original downstream ---------
    # No nagini counterpart — nagini's carrier does not model the non-level
    # branch at all. The spec pins the argument handed to the downstream
    # conversion as the EFFECTIVE type; this rival hands it the stored original,
    # dropping an explicit request. Refutable without knowing anything about the
    # downstream conversion: it is supplied as an input function, so a witness
    # picks one that distinguishes the two arguments.
    {
        "id": "weak-none-branch-selfdtype",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray d rawArray.data\n"
            "  | none   =>\n"
            "      return superArray selfDtype"),
        "witness": _witness("1", "(some 5)", "none",
                            "{ dtype := 2, data := [7, 9] }", _SUP_ID),
        "refinement": "on the unselected-level branch the conversion must defer "
                      "downstream at the EFFECTIVE element type. Passing the stored "
                      "original instead silently drops an explicit request on that "
                      "whole branch, so every conversion of a wrapper without a "
                      "selected level at an explicitly requested type produces the "
                      "wrong element type. That branch is the ordinary (non-level) path "
                      "and is untouched by the resolving change, so a version that "
                      "alters it is changing behavior the fix does not: it is "
                      "behaviourally unequal to gold wherever a request is supplied on "
                      "that branch, and therefore not the resolving change. (Stated as "
                      "inequality with gold on that sub-domain, not as a claim about a "
                      "particular named test — this manifest does not assert a "
                      "PASS_TO_PASS test it has not identified.)",
        "rationale": "rejected by the none-arm of the postcondition: `result = "
                     "superArray (effectiveDtype selfDtype dtypeArg)`. The downstream "
                     "conversion is a modeled INPUT, so the rival is refuted by "
                     "attacking the ARGUMENT rather than the result: at selfDtype=1, "
                     "dtypeArg=some 5, level=none with the supplied conversion `fun d "
                     "=> { dtype := d, data := [] }`, the spec demands the array at 5 "
                     "and the rival produces the array at 1. This is the only reject "
                     "case at level=none together with `branch-ignore-level`, so "
                     "without it the level binder's none arm would be attacked by "
                     "nothing. If it verified, the effective type would be unpinned on "
                     "the entire unselected-level branch (SPEC-TOO-WEAK).",
    },

    # -- BRANCH SELECTION (uniqueness): ignore the level entirely --------------
    # No nagini counterpart. The rival always takes the selected-level route,
    # never consulting `level`, so the non-level branch's result is produced by
    # the wrong route. Refutes clause (D) directly: the branch must FOLLOW the
    # level binder.
    {
        "id": "branch-ignore-level",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  return castArray d rawArray.data"),
        "witness": _witness("1", "none", "none",
                            "{ dtype := 2, data := [7, 9] }",
                            "fun d => { dtype := d, data := [5] }"),
        "refinement": "re-presenting the raw level values unconditionally means a "
                      "wrapper with NO selected level also gets answered from level "
                      "values, bypassing the ordinary conversion route entirely. That "
                      "route is not touched by the resolving change and is what the "
                      "overwhelming majority of the PASS_TO_PASS suite exercises, so "
                      "collapsing it into the level route breaks currently passing "
                      "behavior; it does not resolve.",
        "rationale": "rejected by clause (D): the postcondition's `match level with` "
                     "makes the branch a function of the level binder, and at "
                     "level=none the result must be whatever the downstream conversion "
                     "yields at the effective type. The witness supplies a downstream "
                     "conversion whose values (`[5]`) differ from the raw level values "
                     "(`[7, 9]`), so the two routes are distinguishable at "
                     "selfDtype=1, dtypeArg=none, level=none — this varies the "
                     "superArray binder away from the identity-shaped one the other "
                     "witnesses use. If it verified, the branch condition itself would "
                     "be unpinned (SPEC-TOO-WEAK).",
    },

    # -- LEVEL IDENTITY (uniqueness): re-present only for some levels ----------
    # No nagini counterpart. `level` is bound by the spec but its IDENTITY is
    # never consulted — the some-arm is the same for every selected level. This
    # rival makes the behavior depend on which level was selected, so it is
    # correct on most of the domain and divergent on one distinguished level.
    # Its witness must therefore sit at that level, which is also the only
    # witness in the battery at level = some 0.
    {
        "id": "partial-level-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some l =>\n"
            "      if l == 0 then\n"
            "        return rawArray\n"
            "      else\n"
            "        return castArray d rawArray.data\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("4", "none", "(some 0)",
                            "{ dtype := 2, data := [7, 9] }", _SUP_ID),
        "refinement": "re-presenting the values for some selected levels but handing "
                      "back the raw array for others makes the element type the "
                      "conversion reports depend on WHICH level was selected. The "
                      "resolving change is uniform over levels; a version that "
                      "special-cases one level still reports a widened element type "
                      "whenever that level is the one being read, so the FAIL_TO_PASS "
                      "tests fail for any input that lands on it. It would resolve only "
                      "by accident of which level the tests happen to use, and is "
                      "behaviourally unequal to gold, so it is not the resolving "
                      "change.",
        "rationale": "rejected by clause (D)'s identity-independence half: the "
                     "postcondition's some-arm is `castArray (effectiveDtype selfDtype "
                     "dtypeArg) rawArray.data` with the level's identity DISCARDED "
                     "(`some _`), so every selected level must be answered the same "
                     "way. The witness sits at the distinguished level (level=some 0, "
                     "selfDtype=4, dtypeArg=none, effective type 4 vs the raw 2) — the "
                     "sub-domain this rival is actually wrong on, and a level value no "
                     "other witness uses. If it verified, the spec would permit the "
                     "result to depend on the level's identity (SPEC-TOO-WEAK).",
    },

    # -- VALUE CORRUPTION (uniqueness): an extra trailing value ----------------
    # Port of nagini's `value-extra-element`. Correct element type, but the
    # materialised values are one longer than the raw level values. Note the
    # witness runs on an EMPTY raw array, which makes the length divergence
    # maximally simple and also probes the empty-input edge of the data binder.
    {
        "id": "value-extra-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray d (rawArray.data ++ [0])\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("6", "none", "(some 3)",
                            "{ dtype := 6, data := [] }",
                            "fun _ => { dtype := 0, data := [4] }"),
        "refinement": "re-presenting a level's values at a different element type "
                      "preserves their count and content; emitting an extra trailing "
                      "value produces an array of the wrong length. The tests read the "
                      "produced value array itself (and the surrounding suite compares "
                      "these arrays elementwise and checks their shapes), so a version "
                      "that lengthens the level's values is observably divergent from "
                      "gold and does not resolve.",
        "rationale": "rejected by clause (C): `castArray` carries `rawArray.data` "
                     "through unchanged, so the result's values must be exactly the raw "
                     "level values; an appended element makes them one longer. The "
                     "witness uses an EMPTY raw array (rawArray = { dtype := 6, data := "
                     "[] }, the only empty-data point in the battery) so the divergence "
                     "is [0] vs [], and it holds the element type CORRECT "
                     "(selfDtype=6 = rawArray.dtype = the effective type) so the "
                     "refutation is attributable to the values alone and not to clause "
                     "(A). If it verified, value preservation would be unpinned "
                     "(SPEC-TOO-WEAK).",
    },

    # -- VALUE CORRUPTION (uniqueness): drop the last value --------------------
    # Port of nagini's `value-drop-last`. The mirror-image length divergence,
    # kept as a separate case because it fails on the opposite side: it is
    # CORRECT on the empty input (where dropLast is a no-op) and divergent on
    # every non-empty one, so it is not the same rival as the one above and does
    # not share its witness (whose raw array is empty).
    {
        "id": "value-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray d (rawArray.data.dropLast)\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("2", "none", "(some 3)",
                            "{ dtype := 2, data := [7, 9] }",
                            "fun _ => { dtype := 0, data := [] }"),
        "refinement": "stopping one value short emits a shorter array than the level "
                      "actually holds — the level's last label goes missing. The "
                      "produced value array is exactly what the tests observe, so a "
                      "truncating version diverges from gold on every non-empty level "
                      "and does not resolve.",
        "rationale": "rejected by clause (C), on the opposite side from "
                     "`value-extra-element`: the result's values must be the FULL raw "
                     "level values, and dropping the last leaves them one short on any "
                     "non-empty input. This rival is CORRECT on the empty input, so it "
                     "cannot share the extra-element witness (whose raw array is "
                     "empty); its own witness is at rawArray = { dtype := 2, data := "
                     "[7, 9] }, where the rival yields [7] against the demanded "
                     "[7, 9]. The element type is again held correct (effective type 2 "
                     "= rawArray.dtype) so the refutation is attributable to the values "
                     "alone. If it verified, value preservation would be unpinned "
                     "(SPEC-TOO-WEAK).",
    },

    # -- VALUE CORRUPTION (uniqueness): reverse the order ----------------------
    # No nagini counterpart, and the gap the two length rivals above leave open:
    # both of them change the LENGTH, so a rival that keeps the length (and even
    # the multiset of values) and only disturbs the ORDER is unattacked by the
    # battery as ported. Clause (C) pins the order too — `castArray` carries the
    # list through, and a `List` is ordered — so this must be rejected. The
    # witness holds the element type CORRECT (selfDtype = rawArray.dtype = the
    # effective type) and uses a non-palindromic value list, so the refutation is
    # attributable to the order alone.
    {
        "id": "value-permute-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray d rawArray.data.reverse\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("3", "none", "(some 2)",
                            "{ dtype := 3, data := [7, 9] }", _SUP_ID),
        "refinement": "re-presenting a level's values at a different element type "
                      "preserves their ORDER: the value at each position still "
                      "describes the same label. Emitting them back-to-front keeps the "
                      "count and the set of values but misaligns every position, so "
                      "the produced array no longer corresponds label-for-label to the "
                      "level it was read from. The tests read the produced value array "
                      "and compare it elementwise, so a reordering version is "
                      "observably divergent from gold on any level whose values are not "
                      "palindromic, and it does not resolve.",
        "rationale": "rejected by clause (C)'s ORDER half, which neither length rival "
                     "reaches: `castArray` carries `rawArray.data` through as a `List`, "
                     "which is ordered, so the result's values must match position for "
                     "position and not merely in count or as a multiset. The witness is "
                     "at rawArray = { dtype := 3, data := [7, 9] } where the rival "
                     "yields [9, 7] against the demanded [7, 9]; the element type is "
                     "held correct (selfDtype=3 = rawArray.dtype = the effective type) "
                     "so the refutation is attributable to the order alone and not to "
                     "clause (A). If it verified, a rival could permute the level's "
                     "values freely (SPEC-TOO-WEAK).",
    },

    # -- VALUE CORRUPTION (uniqueness): perturb one element ---------------------
    # No nagini counterpart. The third independent half of clause (C): this rival
    # keeps the length AND the order and changes only an element's VALUE, so it
    # is unattacked by the length rivals and by the order rival above. Correct on
    # every input whose values are all non-negative, divergent on any other, so
    # its witness must sit at a level carrying a negative value.
    {
        "id": "value-clamp-negatives",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray d (rawArray.data.map (fun x => if x < 0 then 0 else x))\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("5", "none", "(some 1)",
                            "{ dtype := 5, data := [-3, 2] }", _SUP_ID),
        "refinement": "re-presenting a level's values at a different element type "
                      "changes how they are carried, never WHAT they are: the values "
                      "are unchanged as long as they are in range for the element type "
                      "involved. Flooring the negative ones at zero silently rewrites "
                      "the level's labels, so a level holding negative values reads "
                      "back wrong. The tests read the produced value array and compare "
                      "it against the level's actual values, so a clamping version is "
                      "observably divergent from gold and does not resolve.",
        "rationale": "rejected by clause (C)'s ELEMENT-IDENTITY half, which the length "
                     "and order rivals both leave open: `castArray` carries "
                     "`rawArray.data` through unchanged, so every element must be the "
                     "raw one, not a rewritten one. This rival is CORRECT wherever the "
                     "values are all non-negative — including at every other witness "
                     "point in this battery — so it needs its own witness at a negative "
                     "value: rawArray = { dtype := 5, data := [-3, 2] }, where it "
                     "yields [0, 2] against the demanded [-3, 2]. Length, order and the "
                     "element type are all held correct (selfDtype=5 = rawArray.dtype = "
                     "the effective type), so the refutation is attributable to the "
                     "element value alone. If it verified, the spec would permit the "
                     "level's values to be rewritten in place (SPEC-TOO-WEAK).",
    },

    # -- SPARSE ELEMENT REWRITE (uniqueness): perturb only LARGE values ---------
    # Added by the independent audit as a tuned attack-D rival. Every other value
    # rival in the battery is DENSE — wrong on a broad sub-domain that the other
    # cases' witness points already intersect. This one is deliberately tuned to
    # EVADE the whole battery as it stood: it rewrites an element only when the
    # value exceeds 100, and every pre-existing witness point carries values in
    # [-3, 9], so `value-extra-element`, `value-drop-last`, `value-permute-order`
    # and `value-clamp-negatives` all agree with it at their own points. It is
    # nonetheless REJECTED, which is the load-bearing fact: the spec pins
    # `rawArray.data` at EVERY value, not merely on the sub-domain the battery
    # happens to sample. Its witness must therefore sit at a large value, and it
    # is the only point in the battery that does.
    {
        "id": "value-rewrite-large",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray d (rawArray.data.map (fun x => if x > 100 then 0 else x))\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("5", "none", "(some 1)",
                            "{ dtype := 5, data := [200] }", _SUP_ID),
        "refinement": "re-presenting a level's values at a different element type "
                      "never changes WHAT the values are, at any magnitude. Zeroing "
                      "the large ones silently rewrites the level's labels wherever a "
                      "level happens to carry a large value, so such a level reads "
                      "back wrong while small-valued levels look fine. The tests read "
                      "the produced value array and compare it against the level's "
                      "actual values, so this is observably divergent from gold on any "
                      "level carrying a large value and does not resolve. It is a "
                      "particularly dishonest near-miss precisely because it looks "
                      "correct on small test data.",
        "rationale": "rejected by clause (C)'s element-identity half, at a point NO "
                     "other case in the battery reaches. This rival is tuned to evade "
                     "every other witness: all of the other points carry values in "
                     "[-3, 9], where this impl is exactly gold, so it survives the "
                     "battery as ported and is caught only by its own witness at "
                     "rawArray = { dtype := 5, data := [200] }, where it yields [0] "
                     "against the demanded [200]. Length, order and the element type "
                     "are all held correct (selfDtype=5 = rawArray.dtype = the "
                     "effective type), so the refutation is attributable to the "
                     "element value alone. Its purpose is to demonstrate that the "
                     "spec constrains the values over the WHOLE carrier rather than "
                     "on the sub-domain the other witnesses sample (SPEC-TOO-WEAK if "
                     "it verified).",
    },

    # -- SPARSE REORDER (uniqueness): permute only LONGER value lists -----------
    # Added by the independent audit, the order-half twin of the rival above and
    # tuned the same way. `value-permute-order` reverses unconditionally, and its
    # witness (and every other witness in the battery) uses a list of length <= 2;
    # this rival reverses only lists LONGER than 2, so it agrees with gold at every
    # pre-existing point — including at `value-permute-order`'s own witness, where
    # the list has length 2 and is left alone. It is still rejected, so the order
    # commitment holds at every length and not only where the battery samples it.
    {
        "id": "value-permute-long-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let d := dtypeArg.getD selfDtype\n"
            "  match level with\n"
            "  | some _ =>\n"
            "      return castArray d "
            "(if rawArray.data.length > 2 then rawArray.data.reverse else rawArray.data)\n"
            "  | none   =>\n"
            "      return superArray d"),
        "witness": _witness("3", "none", "(some 2)",
                            "{ dtype := 3, data := [7, 9, 11] }", _SUP_ID),
        "refinement": "the positional correspondence between a level's values and its "
                      "labels holds at every length; a version that reverses only the "
                      "longer levels misaligns every position for exactly those levels "
                      "while leaving short ones intact. The tests compare the produced "
                      "value array elementwise, so this diverges observably from gold "
                      "on any level holding more than two values and does not resolve. "
                      "Like the large-value rewrite above it is a near-miss that looks "
                      "correct on small test data.",
        "rationale": "rejected by clause (C)'s ORDER half at a LENGTH no other case "
                     "reaches. Tuned to evade the battery as it stood: every other "
                     "witness point carries at most two values, and this impl is "
                     "exactly gold on those, so even `value-permute-order`'s own "
                     "witness (a length-2 list) fails to refute it. Its own witness is "
                     "the battery's only length-3 point, rawArray = { dtype := 3, data "
                     ":= [7, 9, 11] }, where it yields [11, 9, 7] against the demanded "
                     "[7, 9, 11]; the element type is held correct (selfDtype=3 = "
                     "rawArray.dtype = the effective type) so the refutation is "
                     "attributable to the order alone. Demonstrates that the order "
                     "commitment is pinned at every length (SPEC-TOO-WEAK if it "
                     "verified).",
    },
]

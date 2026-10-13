# properties.py — G-PBT spec-falsification manifest for astropy__astropy-8872
# (lean backend). NOT a Lean module: a record of adversarial cases. The runner
# writes each `module` to a temp file, elaborates it under the pinned workspace,
# and checks same_spec against the frozen Solution.lean. Every case edits ONLY
# the impl region (and, for the soundness positives, the proof body), so
# markers.same_spec holds by construction and every rejection is attributable to
# the postcondition rather than to a tampered spec.
#
# Ported from the nagini sibling's battery (nagini/properties.py); that file is
# the design document, this one re-expresses its adversarial arguments against
# this backend's carrier. See `assessment` in the submitted payload for the
# case-by-case port map. An audit re-derived every nagini case this port had
# dropped and landed the ones that were expressible after all: the bool rival
# (`also-promote-bool-reuse`) and the width-keyed rival on the second obligation
# (`width-keyed-reuse`), plus the admissibility lane and two rivals closing
# target/preservation gaps on the reuse obligation.
#
# A SECOND, INDEPENDENT audit re-derived every witness against the real verifier
# (14 reject cases x 4 builds: rival, frozen, and a FORGERY of each asserting the
# opposite claim). Every rival elaborated its witness (exit 0) and every witness
# failed on the frozen solution by PLAIN EVALUATION — "Tactic `decide` proved
# that the proposition ... is false" — while the flipped-claim forgery inverted
# both exit codes exactly (frozen 0, rival 1). So each gold-side exit code
# carries full information about the claim it was asked, which is the property a
# witness must have and the one a recorded SOUND cannot show on its own.
#
# That audit also found FOUR refinement arguments that overclaimed what the
# real test suite observes, and rewrote them (`also-promote-object-reuse`,
# `width-keyed-reuse`, `frame-widen-reuse`, `never-promote-general`). The
# rivals themselves were all genuinely wrong against the frozen postconditions
# and all remain; what was false was the downstream claim that a specific
# assertion in the test suite would catch each one. The corrected form is
# recorded per case below, and the general lesson is stated once here: the two
# obligations are NOT observed symmetrically by the tests. Only ONE input in the
# whole suite reaches the fast-reuse decision under an observable assertion (an
# integer-typed input re-wrapped with no element type requested), because the
# other re-wrapping sites either request no copy — which returns before the
# element-type decision is consulted at all — or assert only identity, memory
# order and shape, which a reshaped element type preserves. Three reuse rivals
# (`drop-signed-reuse`, `never-promote-reuse`, `wrong-target-reuse`) do land on
# that one observable input and their refinements are sound as written. The rest
# of the reuse lane is pinned by the SPEC being faithful to the intended
# decision, not by a test, and now says so.
#
# DEFENDED SURFACE (read Solution.lean + mapping.md + refinement.md):
#   Two total pure functions over a three-field element-type record
#   (`DType`: kind : Char, canHoldSingle : Bool, structured : Bool). Both return
#   a `DType` — the element type the array is finally stored under.
#
#   Load-bearing postconditions, each an exact equality against an `if`:
#     problem_spec_resolveDtype dt r := r = if promoteGeneral dt then floatDType else dt
#     problem_spec_reuseDtype   dt r := r = if promoteReuse   dt then floatDType else dt
#   where promoteGeneral dt := dt.kind = 'i' || dt.kind = 'u' || dt.kind = 'O'
#     and promoteReuse   dt := dt.kind = 'i' || dt.kind = 'u'.
#
#   Each postcondition has THREE independently attackable parts, and the roster
#   below attacks all three on BOTH obligations:
#     (a) the promotion CONDITION — which element-type categories promote;
#     (b) the promotion TARGET — that a promoted input becomes exactly the
#         default floating type;
#     (c) the PRESERVATION arm — that a non-promoted input is returned exactly
#         as given, every field included.
#   An earlier revision of this manifest made that claim while attacking (b) and
#   (c) on the general path ONLY; `wrong-target-reuse` and `frame-widen-reuse`
#   are what make it true. The two preservation-arm rivals also clobber
#   DIFFERENT fields (`canHoldSingle`, `structured`), so between them every
#   non-`kind` component of a preserved record is pinned.
#
#   THE CLAUSE BY WHICH THE TWO OBLIGATIONS DIFFER is the generic-object
#   exception, and an audit found it probed in ONE direction only: a rival that
#   removed it from the general path (`drop-object-general`), and nothing that
#   forced the reuse condition to EXCLUDE it. So a spec whose reuse predicate
#   also promoted `'O'` — the two obligations conflated the other way — passed
#   every other case here. `also-promote-object-reuse` closes that, and the two
#   object-point rivals now pin the clause to the general path from both sides.
#
#   THE DISCRIMINATOR the fix establishes: the decision is a function of `kind`
#   ALONE, never of `canHoldSingle` (the storage-width observable). A
#   lower-precision floating type is `kind = 'f'` with `canHoldSingle = false`,
#   so the spec ranges over the very input a width-keyed decision gets wrong.
#
# WHY THERE IS NO PERMISSION/FRAME-MUTATION CASE in the nagini sense: Lean is
#   referentially transparent — there is no fractional read permission and no
#   aliased input to mutate, so that nagini class is VACUOUS here. Its Lean
#   analogue is the *unconstrained output component* (SPEC_GUIDE §0.5), which IS
#   attacked, on both obligations and through every non-`kind` field, by
#   `frame-narrow-preserved`, `frame-widen-reuse`, `wrong-promotion-target` and
#   `wrong-target-reuse`.
#
# WHY THERE IS NO DIVERGENCE / NON-TERMINATION CASE: the nagini sibling carries
#   none, and on this backend the class is genuinely vacuous rather than a spec
#   hole — `implementation_*` is a total Lean `def`, so a diverging rival cannot
#   be written at all. (Contrast velvet under
#   `loom.semantics.termination "partial"`, where it is a KNOWN SPEC HOLE; see
#   the corpus-wide termination-semantics finding. That does not apply to a lean bundle.)
#
# THE ADMISSIBILITY LANE (`admiss-ground-f2p-points`): nagini guards both
#   functions with `Requires(realizable(...))`; here each obligation is an
#   unconditional `∀ (dt : DType), problem_spec_... dt (implementation_... dt)`,
#   so there is no precondition binder to attack directly. An earlier revision of
#   this manifest concluded from that there was nothing for an admissibility
#   driver to discharge. That reason is WRONG and the case below is the
#   correction: on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
#   obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
#   positive that discharges the spec predicate at those concrete inputs BY
#   EVALUATION — as a `have`, before closing the frozen obligation verbatim —
#   tests directly. Grounded at eight points spanning both obligations,
#   including the lower-precision float that is the whole point of this cell: if
#   any `have` failed to `decide`, the spec would be unsatisfiable at a real
#   element type and no impl could ever be correct there.
#
# WHY NO UNGROUNDED-ORACLE ECHO CASE: the postcondition's right-hand side is a
#   fully-unfolded `if` over the input record — it IS the work, not an opaque
#   answer key. There is no opaque callee anywhere in this bundle (the `axioms`
#   region is empty), so every witness below states the spec at a concrete
#   literal input and closes by `decide`; no conditioning on the carrier is
#   needed, and no witness binds anything.

from pathlib import Path

INSTANCE = "astropy__astropy-8872"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- region anchors -------------------------------------------------------
# Each lies ENTIRELY inside the region it names and is unique in the file (the
# two impl bodies differ in the predicate they call, the two proof bodies in the
# names they unfold), so the manifest breaks loudly if the frozen file changes.

_GEN_IMPL = """  let mut result := dt
  if promoteGeneral dt then
    result := floatDType
  return result
"""
_REU_IMPL = """  let mut result := dt
  if promoteReuse dt then
    result := floatDType
  return result
"""
_GEN_PROOF = """  intro dt
  unfold problem_spec_resolveDtype implementation_resolveDtype
  simp only [Id.run]
  by_cases h : promoteGeneral dt <;> simp [h] <;> rfl
"""
_REU_PROOF = """  intro dt
  unfold problem_spec_reuseDtype implementation_reuseDtype
  simp only [Id.run]
  by_cases h : promoteReuse dt <;> simp [h] <;> rfl
"""

# Input points the witnesses probe. Named so the roster reads as a table and so
# no two rivals silently share a point.
_NARROW_FLOAT = "{ kind := 'f', canHoldSingle := false, structured := false }"
_WIDE_FLOAT = "{ kind := 'f', canHoldSingle := true,  structured := false }"
_OBJECT = "{ kind := 'O', canHoldSingle := true,  structured := false }"
_COMPLEX = "{ kind := 'c', canHoldSingle := true,  structured := false }"
_RECORD = "{ kind := 'V', canHoldSingle := false, structured := true }"
_SIGNED = "{ kind := 'i', canHoldSingle := false, structured := false }"
_UNSIGNED = "{ kind := 'u', canHoldSingle := false, structured := false }"
_BOOL = "{ kind := 'b', canHoldSingle := false, structured := false }"
_TEXT = "{ kind := 'S', canHoldSingle := false, structured := false }"


def _ground_have(name, fn, point):
    """A `have` discharging `problem_spec_<fn>` at one concrete literal input.

    The admissibility probe on a total carrier: each `have` closes BY EVALUATION
    (`decide` on a fully-literal record), so it succeeds only if the frozen
    obligation is actually SATISFIABLE at that input. Prepended to the frozen
    tactic body, which then closes the obligation verbatim.
    """
    return (
        f"  have {name} : problem_spec_{fn}\n"
        f"      {point}\n"
        f"      (implementation_{fn}\n"
        f"        {point}) := by\n"
        f"    unfold problem_spec_{fn} implementation_{fn}\n"
        f"    decide\n"
    )


def _witness(fn, point):
    """A refutation of `problem_spec_<fn>` at one concrete literal input.

    Elaborates against a rival that disagrees with the spec there; fails against
    the frozen solution, which satisfies the spec at every input. Binds nothing,
    so there are no assumptions that could be jointly unsatisfiable.
    """
    return (
        f"example : ¬ problem_spec_{fn}\n"
        f"    {point}\n"
        f"    (implementation_{fn}\n"
        f"      {point}) := by\n"
        f"  unfold problem_spec_{fn} implementation_{fn}\n"
        f"  decide\n"
    )


# =========================================================================
# SOUNDNESS POSITIVES (expect="verify") — structurally different but CORRECT
# impls, each reproven inside the frozen `theorem correct_*` statement. A
# rejection here would be SPEC-TOO-STRONG.
# =========================================================================

# Branch-explicit shape: two early returns instead of a mutable accumulator.
# The obligation is reproven, not weakened; only the tactic body differs.
_POS_GENERAL = _swap(
    _swap(_BASE, _GEN_IMPL,
          """  if promoteGeneral dt then
    return floatDType
  else
    return dt
"""),
    _GEN_PROOF,
    """  intro dt
  unfold problem_spec_resolveDtype implementation_resolveDtype
  simp only [Id.run]
  by_cases h : promoteGeneral dt <;> simp [h] <;> rfl
""",
)

# Polarity flip: initialise the accumulator to the default floating type and
# overwrite it on the NEGATED test. Same function, opposite default.
_POS_REUSE = _swap(
    _swap(_BASE, _REU_IMPL,
          """  let mut result := floatDType
  if !promoteReuse dt then
    result := dt
  return result
"""),
    _REU_PROOF,
    """  intro dt
  unfold problem_spec_reuseDtype implementation_reuseDtype
  simp only [Id.run]
  by_cases h : promoteReuse dt <;> simp [h] <;> rfl
""",
)

# Both sites at once, each a different shape, and each spelling the category
# test out inline instead of calling the shared predicate — so the frozen spec
# must admit a faithful rewrite of the whole module, helper calls included.
_POS_BOTH = _swap(
    _swap(
        _swap(
            _swap(_BASE, _GEN_IMPL,
                  """  let promote : Bool := dt.kind = 'i' || dt.kind = 'u' || dt.kind = 'O'
  let mut result := floatDType
  if promote = false then
    result := dt
  return result
"""),
            _GEN_PROOF,
            """  intro dt
  unfold problem_spec_resolveDtype implementation_resolveDtype promoteGeneral
  simp only [Id.run]
  by_cases h : (dt.kind = 'i' || dt.kind = 'u' || dt.kind = 'O') = true <;>
    simp [h] <;> rfl
"""),
        _REU_IMPL,
        """  let promote : Bool := dt.kind = 'i' || dt.kind = 'u'
  if promote then
    return floatDType
  else
    return dt
"""),
    _REU_PROOF,
    """  intro dt
  unfold problem_spec_reuseDtype implementation_reuseDtype promoteReuse
  simp only [Id.run]
  by_cases h : (dt.kind = 'i' || dt.kind = 'u') = true <;> simp [h] <;> rfl
""",
)


# =========================================================================
# UNIQUENESS RIVALS (expect="reject") — same-spec WRONG impls. Each carries a
# witness that has been SEEN to elaborate against the rival and fail against the
# frozen solution.
# =========================================================================

# (a) CONDITION attacks on the general path -------------------------------

# The headline defect, reborn as a same-spec rival: key the decision on the
# storage-width observable instead of on the element-type category.
_R_WIDTH_GENERAL = _swap(_BASE, _GEN_IMPL,
                         """  let mut result := dt
  if !(dt.canHoldSingle || dt.structured) || dt.kind = 'O' then
    result := floatDType
  return result
""")

# Uses the fast-reuse predicate on the general path, dropping the
# generic-object exception that only the general path carries.
_R_DROP_OBJECT = _swap(_BASE, _GEN_IMPL,
                       """  let mut result := dt
  if dt.kind = 'i' || dt.kind = 'u' then
    result := floatDType
  return result
""")

# Also promotes the complex category.
_R_COMPLEX = _swap(_BASE, _GEN_IMPL,
                   """  let mut result := dt
  if promoteGeneral dt || dt.kind = 'c' then
    result := floatDType
  return result
""")

# Also promotes record/structured element types.
_R_RECORD = _swap(_BASE, _GEN_IMPL,
                  """  let mut result := dt
  if promoteGeneral dt || dt.structured then
    result := floatDType
  return result
""")

# Promotes nothing at all on the general path.
_R_NEVER_GENERAL = _swap(_BASE, _GEN_IMPL,
                         """  let mut result := dt
  return result
""")

# (b) TARGET attack -------------------------------------------------------

# Promotes to a RECORD floating type rather than to the plain default one, so
# the condition is right and the target is wrong.
_R_WRONG_TARGET = _swap(_BASE, _GEN_IMPL,
                        """  let mut result := dt
  if promoteGeneral dt then
    result := { kind := 'f', canHoldSingle := true, structured := true }
  return result
""")

# (c) PRESERVATION-ARM attack --------------------------------------------

# Preserves the category but silently narrows the preserved type's capability
# to hold a single-precision value — the Lean analogue of leaving an output
# component unconstrained (SPEC_GUIDE §0.5).
_R_FRAME_NARROW = _swap(_BASE, _GEN_IMPL,
                        """  let mut result := { dt with canHoldSingle := false }
  if promoteGeneral dt then
    result := floatDType
  return result
""")

# (d) the fast-reuse obligation ------------------------------------------

# Promotes only the unsigned category, leaving the signed one unpromoted.
_R_DROP_SIGNED_REUSE = _swap(_BASE, _REU_IMPL,
                             """  let mut result := dt
  if dt.kind = 'u' then
    result := floatDType
  return result
""")

# Promotes nothing at all on the fast-reuse path.
_R_NEVER_REUSE = _swap(_BASE, _REU_IMPL,
                       """  let mut result := dt
  return result
""")

# Keys the FAST-REUSE decision on the storage-width observable instead of on
# `kind` — the width-keyed defect on the second obligation. The battery attacked
# this shape only on the general path, so without this rival a spec that got the
# general condition right and the reuse condition width-keyed would pass.
_R_WIDTH_REUSE = _swap(_BASE, _REU_IMPL,
                       """  let mut result := dt
  if !(dt.canHoldSingle || dt.structured) then
    result := floatDType
  return result
""")

# Fast reuse ALSO promotes the boolean category. Ported from the nagini
# sibling's `weak-coerce-bool-homog`, which the first pass of this port dropped.
_R_BOOL_REUSE = _swap(_BASE, _REU_IMPL,
                      """  let mut result := dt
  if promoteReuse dt || dt.kind = 'b' then
    result := floatDType
  return result
""")

# Fast reuse gets the CONDITION right and the TARGET wrong: promotes to a
# narrow floating type rather than to the default one. The target arm was
# attacked only on the general path.
_R_TARGET_REUSE = _swap(_BASE, _REU_IMPL,
                        """  let mut result := dt
  if promoteReuse dt then
    result := { kind := 'f', canHoldSingle := false, structured := false }
  return result
""")

# Fast reuse clobbers the PRESERVATION arm: a preserved type comes back marked
# structured. The preservation arm was attacked only on the general path, and
# only through the `canHoldSingle` field.
_R_FRAME_REUSE = _swap(_BASE, _REU_IMPL,
                       """  let mut result := { dt with structured := true }
  if promoteReuse dt then
    result := floatDType
  return result
""")

# Also promotes the TEXT categories on the general path. The frozen predicate's
# own documented claim is that text element types are kept as given, and an audit
# found no case in the roster holding a text `kind` at all — so a spec whose
# general condition also promoted text satisfied every other case here. Text is a
# real category the carrier ranges over (`kind = 'S'`), and the general path is
# where a text input is rejected as non-numeric only AFTER the element type is
# observed, so the decision is defined on it.
_R_TEXT_GENERAL = _swap(_BASE, _GEN_IMPL,
                        """  let mut result := dt
  if promoteGeneral dt || dt.kind = 'S' || dt.kind = 'U' then
    result := floatDType
  return result
""")

# Fast reuse ALSO promotes the generic-object category — i.e. it uses the
# GENERAL-path predicate on the reuse path. The clause by which the two
# obligations differ was attacked in one direction only (`drop-object-general`
# removes it from the general path); nothing forced the reuse condition to
# EXCLUDE it, so a spec that conflated the two obligations in this direction
# went unprobed. Witnessed at the generic-object point on the reuse obligation,
# where `promoteReuse` is false so the spec demands the input back unchanged.
_R_OBJECT_REUSE = _swap(_BASE, _REU_IMPL,
                        """  let mut result := dt
  if promoteReuse dt || dt.kind = 'O' then
    result := floatDType
  return result
""")

# ---------------------------------------------------------------------------
# ADMISSIBILITY — ground both obligations at F2P-shaped inputs by evaluation,
# then close each frozen obligation verbatim. Touches only the proof bodies.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _swap(_BASE, _GEN_PROOF,
          _ground_have("_g_narrow", "resolveDtype", _NARROW_FLOAT)
          + _ground_have("_g_wide", "resolveDtype", _WIDE_FLOAT)
          + _ground_have("_g_signed", "resolveDtype", _SIGNED)
          + _ground_have("_g_object", "resolveDtype", _OBJECT)
          + _ground_have("_g_record", "resolveDtype", _RECORD)
          + _GEN_PROOF),
    _REU_PROOF,
    _ground_have("_r_signed", "reuseDtype", _SIGNED)
    + _ground_have("_r_unsigned", "reuseDtype", _UNSIGNED)
    + _ground_have("_r_narrow", "reuseDtype", _NARROW_FLOAT)
    + _REU_PROOF,
)


SPEC_TESTS = [
    # ---------------- soundness positives ----------------
    {
        "id": "pos-general-branch-explicit",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_GENERAL,
        "rationale": "structurally different but semantically identical general-path "
                     "impl: two early returns in place of a mutable accumulator. "
                     "Reproven inside the byte-identical `theorem correct_resolveDtype` "
                     "statement (only the tactic body differs; no helper lemma, no new "
                     "axiom, no sorry). Must verify against "
                     "`result = if promoteGeneral dt then floatDType else dt`, else the "
                     "spec is SPEC-TOO-STRONG — it would be pinning the accumulator "
                     "shape rather than the input→output relation.",
    },
    {
        "id": "pos-reuse-polarity-flip",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REUSE,
        "rationale": "fast-reuse positive control with the branch polarity inverted: "
                     "initialise the accumulator to the default floating type and "
                     "overwrite it when the category test FAILS. Semantically equal to "
                     "the frozen impl on every input; reproven under the identical "
                     "`theorem correct_reuseDtype` statement. Must verify.",
    },
    {
        "id": "pos-both-sites-inlined",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BOTH,
        "rationale": "BOTH obligations rewritten at once, each in a different shape, and "
                     "each spelling the category test out inline rather than calling the "
                     "shared predicate — so the rewrite reaches through the helper the "
                     "postcondition itself is phrased over. Both proofs additionally "
                     "unfold that predicate. Confirms the frozen spec admits a faithful "
                     "full-module rewrite, not just a local reshape.",
    },

    # ---------------- uniqueness rivals: general path, CONDITION ----------------
    {
        "id": "width-keyed-general",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_WIDTH_GENERAL,
        "witness": _witness("resolveDtype", _NARROW_FLOAT),
        "rationale": "THE headline rival. Keys the general-path decision on the storage "
                     "observables (`canHoldSingle`, `structured`) instead of on `kind`, "
                     "which is precisely the discriminator the fix establishes. "
                     "Rejection comes from the postcondition's promotion CONDITION at "
                     "the lower-precision floating point "
                     "(kind='f', canHoldSingle=false, structured=false): "
                     "`promoteGeneral` is false there so the spec demands the input back "
                     "unchanged, while the rival promotes it to the default floating "
                     "type. Varies `canHoldSingle` against frame-narrow-preserved's "
                     "wide float at the same `kind`, which is what isolates the width "
                     "observable as the thing the decision must NOT read.",
        "refinement": "its faithful patch keys the general-path decision on whether the "
                     "element type can absorb a single-precision value, so a "
                     "lower-precision floating input is promoted to the default floating "
                     "type instead of being kept. That is exactly the "
                     "dtype-preservation assertion the test patch adds to "
                     "test_preserve_dtype (the narrow-float array must come back with "
                     "its own element type), so the F2P test FAILS and the patch does "
                     "NOT resolve. A verifying rival here would therefore be a genuine "
                     "verify-does-not-imply-resolve break.",
    },
    {
        "id": "drop-object-general",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP_OBJECT,
        "witness": _witness("resolveDtype", _OBJECT),
        "rationale": "uses the fast-reuse predicate on the general path, dropping the "
                     "generic-object exception that distinguishes the two obligations. "
                     "Rejection from the promotion CONDITION at "
                     "(kind='O', canHoldSingle=true, structured=false): `promoteGeneral` "
                     "is true so the spec demands the default floating type, and the "
                     "rival returns the object type unchanged. This is the one rival "
                     "that probes the clause by which the two obligations DIFFER, so "
                     "without it a spec that conflated them would go unnoticed.",
        "refinement": "its faithful patch omits the generic-object category from the "
                     "general-path promotion set, so a value whose elements numpy stores "
                     "as generic Python objects (the decimal input in "
                     "test_preserve_dtype) keeps the object element type instead of "
                     "becoming the default floating type. That assertion is part of the "
                     "F2P test and predates the fix, so the patch FAILS the F2P and does "
                     "NOT resolve.",
    },
    {
        "id": "also-promote-complex-general",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_COMPLEX,
        "witness": _witness("resolveDtype", _COMPLEX),
        "rationale": "near-miss that agrees with the spec on every category except "
                     "complex. Rejection from the promotion CONDITION at "
                     "(kind='c', canHoldSingle=true, structured=false): the spec "
                     "preserves the complex type, the rival promotes it. Distinct input "
                     "point from every other rival, so its claimed sub-domain is the one "
                     "the manifest actually demonstrates.",
        "refinement": "its faithful patch adds the complex category to the promotion "
                     "set, so a complex input is stored as the default floating type — "
                     "a lossy conversion that discards the imaginary part. A "
                     "PASS_TO_PASS display test (TestQuantityDisplay::test_repr_latex) "
                     "renders quantities built from complex values and asserts the "
                     "output carries BOTH components, e.g. the scalar one renders as "
                     "`(1+2i)`; against a real-valued store the imaginary part is gone "
                     "and the rendered string does not match. So that P2P test FAILS "
                     "and the patch does NOT resolve, independently of the F2P. "
                     "(Verified against the test file at the base commit: exactly one "
                     "P2P test asserts on those complex-valued fixtures, not several.)",
    },
    {
        "id": "also-promote-record-general",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_RECORD,
        "witness": _witness("resolveDtype", _RECORD),
        "rationale": "reads the `structured` observable as a promotion trigger. "
                     "Rejection from the promotion CONDITION at "
                     "(kind='V', canHoldSingle=false, structured=true): the spec "
                     "preserves a record type, the rival promotes it. This is the only "
                     "reject case holding `structured = true`, so it is what stops that "
                     "binder from being pinned to `false` across the whole battery.",
        "refinement": "its faithful patch promotes record/structured inputs to the "
                     "default floating type, collapsing a multi-field array into a plain "
                     "numeric one. A PASS_TO_PASS array test builds a three-field record "
                     "array, wraps it, and then indexes the result BY FIELD NAME and "
                     "compares whole records; against a flattened array those accesses "
                     "fail outright. So the P2P suite FAILS and the patch does NOT "
                     "resolve.",
    },
    {
        "id": "never-promote-general",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_NEVER_GENERAL,
        "witness": _witness("resolveDtype", _UNSIGNED),
        "rationale": "degenerate rival: the general path returns its input untouched, so "
                     "the promotion CONDITION is never consulted. Witnessed at "
                     "(kind='u', canHoldSingle=false, structured=false), where the spec "
                     "demands the default floating type and the rival returns the "
                     "unsigned type. Witnessing at the UNSIGNED point rather than the "
                     "signed one is deliberate: it is the only place the unsigned arm of "
                     "`promoteGeneral` is exercised on this obligation, and a rival that "
                     "handled signed but not unsigned integers would otherwise slip "
                     "through the whole battery.",
        "refinement": "its faithful patch never coerces on the general path, so the "
                     "generic-object input keeps the object element type instead of "
                     "becoming the default floating type. That contradicts an "
                     "assertion present in the F2P test ALREADY at the base commit, so "
                     "the F2P FAILS and the patch does NOT resolve. Narrowed by audit: "
                     "an earlier revision also claimed integer inputs keeping their "
                     "integer element type is observed on this path, and it is not — "
                     "the only integer input in that test either requests its element "
                     "type explicitly (so no decision is made) or reaches the OTHER "
                     "obligation by re-wrapping. The object half alone is sufficient "
                     "and is what the argument now rests on. Note also that this "
                     "rival is WITNESSED at the unsigned point, which no test "
                     "exercises at all; that is deliberate and is a statement about "
                     "the SPEC, whose promotion condition must cover both integer "
                     "categories, not a claim that a test observes the unsigned one.",
    },

    {
        "id": "also-promote-text-general",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_TEXT_GENERAL,
        "witness": _witness("resolveDtype", _TEXT),
        "rationale": "near-miss that agrees with the spec on every category except the "
                     "TEXT ones, which it also promotes. Rejection from the promotion "
                     "CONDITION at (kind='S', canHoldSingle=false, structured=false): "
                     "`promoteGeneral` is false there, so the spec demands the input "
                     "back unchanged, while the rival promotes it to the default "
                     "floating type. Added by audit: the frozen predicate's own "
                     "documented claim lists text among the categories kept as given, "
                     "and NO case in the roster held a text `kind`, so that clause of "
                     "the claim was unprobed — a spec whose general condition also "
                     "promoted text satisfied every other case in this manifest. Also "
                     "the only case exercising a `kind` outside the "
                     "{i,u,f,b,c,O,V} set the rest of the battery spans, which is what "
                     "stops the condition from being pinned only on the categories the "
                     "frozen predicate happens to name.",
        "refinement": "its faithful patch adds the text categories to the general-path "
                     "promotion set. Argued from the CONTRACT rather than from a test, "
                     "and deliberately so: a text input is refused as non-numeric on "
                     "this path, so no test observes the decision at a text element "
                     "type, and this refinement claims none. What makes the rival wrong "
                     "is that the documented behaviour the change establishes converts "
                     "exactly the integer and generic-object categories by default; a "
                     "patch converting text as well implements a different decision. "
                     "The spec is therefore stricter here than the harness observes, "
                     "which is the safe direction, and the soundness lane separately "
                     "confirms faithful reshapes still verify.",
    },

    # ---------------- uniqueness rival: general path, TARGET ----------------
    {
        "id": "wrong-promotion-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_WRONG_TARGET,
        "witness": _witness("resolveDtype", _SIGNED),
        "rationale": "gets the promotion CONDITION exactly right and the promotion "
                     "TARGET wrong: promotes to a record floating type instead of the "
                     "plain default one. Rejection from the `then` arm of the "
                     "postcondition's equality at "
                     "(kind='i', canHoldSingle=false, structured=false) — the spec pins "
                     "the result to `floatDType`, whose `structured` field is false. "
                     "This is the only rival attacking the target rather than the "
                     "condition, so it is what stops the spec from being satisfiable by "
                     "'promote to SOMETHING floating'.",
        "refinement": "its faithful patch coerces the right inputs but materialises them "
                     "under a record element type rather than the plain default floating "
                     "one. A PASS_TO_PASS array test wraps an integer range and then "
                     "does elementwise arithmetic on the result and compares against a "
                     "plain numeric array; that arithmetic is not defined for a "
                     "multi-field element type, so the P2P suite FAILS and the patch "
                     "does NOT resolve.",
    },

    # ---------------- uniqueness rival: general path, PRESERVATION ARM ----------------
    {
        "id": "frame-narrow-preserved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_FRAME_NARROW,
        "witness": _witness("resolveDtype", _WIDE_FLOAT),
        "rationale": "the Lean analogue of nagini's frame attack (SPEC_GUIDE §0.5, an "
                     "unconstrained output component rather than a permission "
                     "violation): the promotion decision is correct, but a PRESERVED "
                     "type comes back with its `canHoldSingle` field rewritten to false. "
                     "Rejection from the `else` arm, which pins the result to be exactly "
                     "`dt`, at (kind='f', canHoldSingle=true, structured=false). "
                     "Deliberately witnessed at the WIDE float while width-keyed-general "
                     "is witnessed at the narrow one: same `kind`, opposite "
                     "`canHoldSingle`, so the pair demonstrates the spec's dependence on "
                     "that binder in both directions instead of only where the frozen "
                     "impl happens to branch.",
        "refinement": "its faithful patch preserves the element-type category but stores "
                     "a preserved floating input at reduced precision. "
                     "test_preserve_dtype asserts that a single-precision array comes "
                     "back with its OWN element type — an assertion present at the base "
                     "commit, not merely added by the test patch — and a narrowed "
                     "element type is not equal to it. So the F2P FAILS and the patch "
                     "does NOT resolve.",
    },

    # ---------------- uniqueness rivals: fast-reuse obligation ----------------
    {
        "id": "drop-signed-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP_SIGNED_REUSE,
        "witness": _witness("reuseDtype", _SIGNED),
        "rationale": "attacks the SECOND obligation's promotion CONDITION: promotes only "
                     "the unsigned category, leaving the signed one unpromoted. "
                     "Rejection at (kind='i', canHoldSingle=false, structured=false), "
                     "where `promoteReuse` is true and the rival returns the input. "
                     "Pairs with never-promote-reuse (witnessed at the unsigned point) "
                     "so both arms of `promoteReuse` are separately discriminated rather "
                     "than the disjunction being probed only as a whole.",
        "refinement": "its faithful patch drops the signed-integer category from the "
                     "fast-reuse promotion set. test_preserve_dtype constructs an "
                     "integer-typed quantity with an explicit element type and then "
                     "re-wraps it with none given — the fast-reuse path — and asserts the "
                     "result is the default floating type. Under this patch it stays a "
                     "signed integer, so the F2P FAILS and the patch does NOT resolve. "
                     "This is the fast-reuse behaviour the F2P genuinely observes. The "
                     "unsigned side of the same disjunction is covered by "
                     "never-promote-reuse and the width-keyed shape by "
                     "width-keyed-reuse.",
    },
    {
        "id": "never-promote-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_NEVER_REUSE,
        "witness": _witness("reuseDtype", _UNSIGNED),
        "rationale": "degenerate rival on the fast-reuse obligation: returns its input "
                     "untouched. Witnessed at "
                     "(kind='u', canHoldSingle=false, structured=false) — the unsigned "
                     "arm of `promoteReuse`, an input point no other reuse rival uses, "
                     "so every reuse rival refutes at a DIFFERENT point and no "
                     "rationale claims a sub-domain the manifest fails to demonstrate. "
                     "Pairs with drop-signed-reuse (witnessed at the signed point) so "
                     "both arms of the disjunction are separately discriminated.",
        "refinement": "its faithful patch never coerces on the fast-reuse path, so "
                     "re-wrapping an integer-typed quantity with no element type "
                     "requested leaves it an integer. test_preserve_dtype asserts that "
                     "result is the default floating type — an assertion present at the "
                     "base commit — so the F2P FAILS and the patch does NOT resolve.",
    },
    {
        "id": "width-keyed-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_WIDTH_REUSE,
        "witness": _witness("reuseDtype", _NARROW_FLOAT),
        "rationale": "the headline width-keyed defect carried onto the SECOND obligation, "
                     "which the rest of the battery attacks only on the general path. "
                     "Keys the fast-reuse decision on the storage observables instead of "
                     "on `kind`. Rejection from the promotion CONDITION at the "
                     "lower-precision float (kind='f', canHoldSingle=false, "
                     "structured=false): `promoteReuse` is false there so the spec "
                     "demands the input back unchanged, while the rival promotes it. "
                     "Without this case a spec whose general condition read `kind` and "
                     "whose reuse condition read width would pass the whole battery.",
        "refinement": "its faithful patch keys the fast-reuse decision on whether the "
                     "element type can absorb a single-precision value, so re-wrapping a "
                     "lower-precision floating quantity with no element type requested "
                     "promotes it instead of keeping it. An earlier revision of this "
                     "refinement credited that to the narrow-float assertion the test "
                     "patch adds; that is FALSE and is withdrawn — the narrow-float "
                     "input there is a plain array, not a quantity, so it is built on "
                     "the general construction path and never reaches the fast-reuse "
                     "decision. (`width-keyed-general` makes the same argument on the "
                     "general path and IS sound, because its rival sits where that "
                     "input lands.) The correct argument is the documented contract: "
                     "the behaviour the change establishes is that the storage-width "
                     "observable stops driving the decision on BOTH paths, in favour of "
                     "the element-type category, and a patch that leaves the reuse path "
                     "width-keyed has not made that change. The case is kept for the "
                     "SPEC reason stated in its rationale — without it, a spec whose "
                     "general condition read the category and whose reuse condition read "
                     "the width would satisfy this whole manifest.",
    },
    {
        "id": "also-promote-bool-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_BOOL_REUSE,
        "witness": _witness("reuseDtype", _BOOL),
        "rationale": "near-miss that agrees with the spec on every category except "
                     "boolean, which it also promotes. Rejection from the promotion "
                     "CONDITION at (kind='b', canHoldSingle=false, structured=false): "
                     "the spec preserves the boolean type, the rival promotes it. This is "
                     "the only case in the battery holding kind='b', so it is what stops "
                     "the boolean category from being unconstrained across every "
                     "obligation. Ports the nagini sibling's bool rival, which the first "
                     "pass of this port dropped.",
        "refinement": "its faithful patch adds the boolean category to the fast-reuse "
                     "promotion set, so re-wrapping a boolean-typed quantity with no "
                     "element type requested silently converts it to the default floating "
                     "type. The docstring the change ships states that only integer and "
                     "generic-object inputs are converted by default, so a patch that "
                     "also converts booleans contradicts the documented contract it is "
                     "supposed to establish and is not the gold behaviour.",
    },
    {
        "id": "wrong-target-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_TARGET_REUSE,
        "witness": _witness("reuseDtype", _SIGNED),
        "rationale": "gets the fast-reuse promotion CONDITION exactly right and the "
                     "TARGET wrong: promotes to a lower-precision floating type instead "
                     "of the default one. Rejection from the `then` arm of the second "
                     "postcondition's equality at (kind='i', canHoldSingle=false, "
                     "structured=false), where the spec pins the result to `floatDType`, "
                     "whose `canHoldSingle` field is true. The target arm was previously "
                     "attacked only on the general path, so this is what stops the reuse "
                     "obligation from being satisfiable by 'promote to SOMETHING "
                     "floating'.",
        "refinement": "its faithful patch coerces the right inputs on the fast-reuse path "
                     "but materialises them at reduced precision rather than under the "
                     "default floating type. test_preserve_dtype re-wraps an "
                     "integer-typed quantity with none given and asserts the result is "
                     "exactly the default floating type; a reduced-precision type is not "
                     "equal to it, so the F2P FAILS and the patch does NOT resolve.",
    },
    {
        "id": "frame-widen-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_FRAME_REUSE,
        "witness": _witness("reuseDtype", _WIDE_FLOAT),
        "rationale": "the unconstrained-output-component attack (SPEC_GUIDE §0.5) on the "
                     "SECOND obligation, and through a DIFFERENT field than "
                     "frame-narrow-preserved uses: the promotion decision is correct, but "
                     "a PRESERVED type comes back marked structured. Rejection from the "
                     "`else` arm, which pins the result to be exactly `dt`, at "
                     "(kind='f', canHoldSingle=true, structured=false). Together with "
                     "frame-narrow-preserved this pins both non-`kind` fields of the "
                     "preserved record, on both obligations, rather than only the one the "
                     "general path happened to expose.",
        "refinement": "its faithful patch preserves the element-type category on the "
                     "fast-reuse path but re-materialises the preserved input as a "
                     "multi-field record type. THREE successive revisions of this "
                     "refinement each named a test that catches that, and all three "
                     "were wrong; the withdrawal is itself the finding and is recorded "
                     "rather than quietly replaced. Not the elementwise-arithmetic "
                     "assertions (revision 1); not the buffer-identity or "
                     "memory-order/shape ones (revision 2), because the identity "
                     "assertions all request NO copy, which returns before the "
                     "element-type decision is consulted at all, and a 1-D record "
                     "array reports both C- and F-contiguous with its shape intact, so "
                     "the order and shape assertions still hold under the rival; and "
                     "not a re-wrap that asks for a different unit (revision 3), "
                     "because that converts FIRST and then requests no copy, returning "
                     "early for the same reason. Enumerating every re-wrapping site in "
                     "the F2P and P2P sets leaves exactly four that reach this "
                     "decision on its PRESERVE arm, and all four assert only identity, "
                     "contiguity flags, or shape — each of which a record-typed "
                     "re-materialisation satisfies, checked by evaluating the "
                     "construction directly (ndim 3 and shape (1,1,10) exactly as "
                     "asserted). So NO test in the suite observes this rival and this "
                     "refinement claims none. The case is kept on the CONTRACT: the "
                     "reuse path is specified to return a non-promoted input exactly "
                     "as given, and re-materialising it under a multi-field element "
                     "type is not returning it as given. The spec is thus stricter "
                     "here than the harness can observe, which is the SAFE direction — "
                     "it pins an output component the tests leave free (SPEC_GUIDE "
                     "§0.5), and the soundness lane separately confirms every faithful "
                     "reshape still verifies.",
    },

    {
        "id": "also-promote-object-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_OBJECT_REUSE,
        "witness": _witness("reuseDtype", _OBJECT),
        "rationale": "closes the one clause the battery probed in a single "
                     "direction: the generic-object exception is the ONLY thing by "
                     "which the two obligations differ, and `drop-object-general` "
                     "attacks only its removal from the general path. Nothing forced "
                     "the fast-reuse condition to EXCLUDE that category, so a spec "
                     "whose reuse predicate was `kind = 'i' || kind = 'u' || "
                     "kind = 'O'` — the two obligations conflated in the other "
                     "direction — satisfied every other case in this manifest. "
                     "Rejection from the second postcondition's promotion CONDITION "
                     "at (kind='O', canHoldSingle=true, structured=false): "
                     "`promoteReuse` is false there, so the spec demands the object "
                     "type back unchanged, while the rival promotes it to the default "
                     "floating type. Paired with `drop-object-general` at the same "
                     "input point on the OTHER obligation, the two together pin the "
                     "generic-object clause to the general path exactly.",
        "refinement": "its faithful patch applies the general-path promotion set on "
                     "the fast-reuse path, so re-wrapping a quantity whose elements "
                     "are held as generic Python objects, with no element type "
                     "requested, converts it to the default floating type instead of "
                     "keeping the object type. NOT observed by any test in the "
                     "suite, and an earlier revision of this refinement claimed "
                     "otherwise: it said the object-typed quantity built with an "
                     "explicit element-type request reaches the reuse path by being "
                     "re-wrapped. It is not re-wrapped anywhere, so that argument was "
                     "false and is withdrawn. The correct argument is CONTRACT, not "
                     "test: the documented behaviour the change ships distinguishes "
                     "the two construction paths precisely by whether the "
                     "generic-object exception applies, and a patch applying it on "
                     "both paths does not implement that contract — it is a different "
                     "decision that happens to be unobserved. It is therefore not the "
                     "gold behaviour, and the case is kept because the SPEC must pin "
                     "the clause the contract distinguishes even where no test "
                     "exercises it; a spec that let this through would be satisfied by "
                     "the two obligations conflated, which is exactly the confusion "
                     "the frozen postconditions exist to rule out.",
    },

    # ---------------- admissibility ----------------
    {
        "id": "admiss-ground-f2p-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "PRECOND-TOO-STRONG probe. The frozen obligations are unconditional "
                     "`∀ (dt : DType)`, so there is no precondition binder to attack "
                     "directly; on a total carrier the analogue is the obligation being "
                     "UNSATISFIABLE at an F2P-shaped input. This case discharges the spec "
                     "predicate BY EVALUATION (`decide` on fully-literal records) at "
                     "eight concrete points spanning both obligations — the "
                     "lower-precision float and the wide float that the "
                     "preservation-arm assertions observe, the signed and unsigned "
                     "integers and the generic-object input that the promotion "
                     "assertions observe, and a record type — as `have`s prepended to "
                     "each frozen tactic body, which then closes the obligation "
                     "verbatim. Every point is a real element type. If any `have` failed "
                     "to `decide`, the spec would be unsatisfiable at an input the F2P "
                     "actually exercises and NO implementation could be correct there; "
                     "the statement is byte-identical, so this can only pass by the "
                     "obligation genuinely holding at each point.",
    },
]

# The axiom lane is G-AX's job and this gate ignores it; the `axioms` region of
# the frozen solution is empty in any case (no opaque callee is consumed), so
# there is nothing an axiom case could target.
AXIOM_TESTS = []

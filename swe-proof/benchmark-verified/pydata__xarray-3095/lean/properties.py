"""properties.py — G-PBT falsification battery for pydata__xarray-3095 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_copy`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total function copying an index-backed variable):

  copy (deep : Bool) (v : IVar) : IVar

  The variable ``v`` carries dimension names (``dims``), attributes (``attrs``),
  and a data wrapper (``data``) with an element-value sequence (``values``), the
  element type reported by the underlying sequence (``native``), and the
  separately RECORDED element type of the wrapper (``dtype``). The recorded
  ``dtype`` can be finer-grained than ``native``: a fixed-width text element
  type is recorded distinctly even though a re-derivation from the sequence
  flattens it to the generic catch-all type. The two INPUTS are the ``deep`` flag
  and the source variable ``v``.

  The postcondition ``problem_spec_copy deep v result`` is a conjunction of FIVE
  INDEPENDENT top-level clauses, each pinning one component of ``result`` to its
  value in the input ``v`` (frame discipline, §0.5 — every component is pinned so
  a wrong impl cannot put anything else anywhere):

    * CLAUSE 1 — ``result.dims = v.dims`` (dimension names carried over).
    * CLAUSE 2 — ``result.attrs = v.attrs`` (attributes carried over).
    * CLAUSE 3 — ``result.data.values = v.data.values`` (element values carried
      over; a deep copy duplicates the sequence, a shallow copy shares it, and
      the observable content is identical either way).
    * CLAUSE 4 — ``result.data.native = v.data.native`` (underlying-sequence
      element type carried over). Independently load-bearing, and measured so:
      delete this clause from the postcondition and the ``weak-clobber-native``
      rival below VERIFIES against the weakened spec, so no other clause is
      catching it. It therefore carries its own rival rather than being declared
      covered by the positive controls (a correct impl satisfies every clause
      whether or not the spec states it, so positives cannot defend a clause).
    * CLAUSE 5 — ``result.data.dtype = v.data.dtype`` — THE LOAD-BEARING clause.
      The copy reproduces the RECORDED element type, never re-derived from the
      sequence. This is the behavior the change introduces and the behavior the
      F2P observable turns on: for a value whose recorded ``dtype`` differs from
      its ``native`` type (the fixed-width-text case), a copy that re-derived the
      type from the sequence would report ``native`` instead of the recorded
      ``dtype`` — the regression. Clauses 4 and 5 pin BOTH types precisely, which
      is exactly what discriminates the fix: the copy must keep the recorded one,
      which may differ from the re-derived one.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, demonstrated rather than asserted.
    The nagini rival writes the read-only input (``self.stored_dtype = dtype``,
    value-NEUTRAL) and is rejected there for INSUFFICIENT PERMISSION — a
    permission fact, not a value fact. The nearest expressible analogue here is
    a local ``let mut src := v`` rebound with ``{ src with data := { src.data
    with dtype := src.data.dtype } }`` before assembling the copy. That WAS
    built and it VERIFIES (exit 0), which is the correct outcome and exactly why
    the class is vacuous: ``v`` is an immutable value, the rebinding shadows a
    local and cannot be observed by any caller, so there is no permission to be
    insufficient and nothing for a spec to reject. Recorded as vacuous because a
    faithful port of the rival is CORRECT here, not because it is inexpressible.
    Its ADVERSARIAL INTENT — "the recorded type must survive the copy" — is
    carried over structurally as CLAUSE 5, attacked by the re-derivation and
    constant-object rivals below (see ``assessment``).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: every clause
    is an equality against a component of the input ``v``. The bundle declares no
    ``opaque``/``axiom`` (see meta.json), so there is no answer key an
    implementation could echo without doing the work. The nagini direct-carryover
    positive control is preserved as a soundness positive below.

  * PARTIAL-DOMAIN / re-derivation (nagini _REDERIVE, the pre-patch bug) and
    PARTIAL-DOMAIN / constant object code (nagini _CONSTOBJ) — both attack
    CLAUSE 5 and both port directly: a copy that takes the recorded type from the
    sequence (``native``), and a copy that collapses the recorded type to the
    generic catch-all. They are distinct rivals refuted at DIFFERENT input points
    (see BINDER COVERAGE).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases deep <;> exact ⟨rfl,…⟩`` script
is tuned to the frozen form — so a rejection alone attributes nothing to the
spec. Every ``expect="reject"`` case therefore carries a Lean snippet stating the
spec predicate directly at a ``decide``-able concrete input; each was built and
checked to HOLD of its rival (exit 0) and to FAIL on the frozen solution (``decide``
proves the negation false — exit 1), so it discriminates rather than asserting a
tautology.

BINDER COVERAGE. The two input binders are ``deep : Bool`` and ``v : IVar``.
The reject witnesses vary BOTH: ``deep`` takes ``true`` (re-derive, dims-drop,
values-drop) and ``false`` (constant-object, attrs-drop, native-clobber); ``v``
takes six distinct shapes with different ``dims``/``attrs``/``values`` and both
the text-vs-catch-all discriminating shape (``native = object`` ≠ ``dtype =
unicode w``) and the numeric-coincident shape (``native = dtype``). ``pts`` = 6
distinct input points.

The variation is MEANINGFUL, not two spellings of one point, and this was
measured rather than argued — for each of the two type-clause rivals the witness
was rebuilt at the OTHER point in the same binder and failed to hold, so the
chosen point is the one that does the work:

  * ``weak-rederive-from-sequence`` is refuted at ``deep = true`` and its witness
    restated at ``deep = false`` on the same ``v`` FAILS to build (exit 1) — the
    rival is genuinely CORRECT on the shallow path, so ``deep`` is a
    discriminating binder and not decoration. This is also why ``deep`` must be
    varied at all: a rival that mishandles only one flag value is invisible to a
    battery that pins the flag.
  * ``weak-const-catchall-dtype`` is refuted at ``dtype = unicode 5`` and its
    witness restated at ``dtype = object`` (the already-catch-all sub-domain)
    FAILS to build (exit 1), which is the machine-checked form of the
    PARTIAL-DOMAIN claim in its ``refinement``: the rival really is correct on
    that sub-domain and wrong off it.

The ``deep`` flag is nonetheless a WEAK binder for the two clauses it cannot
separate: the modeled result is content-identical for both flag values (a deep
copy duplicates and a shallow copy shares the same element values), so no rival
can be built that is wrong for exactly one flag value on CLAUSES 1/2/4/5. That
is a property of the carrier — the duplicate-vs-share distinction is not
observable through a value-level model of the sequence — and it is the reason
``pos-elementwise-duplicate`` rebuilds the sequence element-wise on the deep
path: it exercises the only shape of the distinction this carrier can see.

OUT-OF-BATTERY PROBES (run with the real verifier while auditing this battery;
not shipped as cases, recorded here so the coverage claim is falsifiable). Seven
further WRONG impls were built against the frozen spec and every one was
REJECTED (exit 1): clobber the underlying-sequence type to the catch-all; SWAP
the recorded and underlying-sequence types; re-derive only when the recorded type
is already the catch-all (a sentinel-style fallback); duplicate the dimension
names; bump a fixed-width text width by one; reverse the element sequence; and
carry the recorded type only on the deep path while collapsing it on the shallow
path. Five further CORRECT reshapes were built and every one VERIFIED (exit 0):
return the input unchanged; branch on ``deep`` with a ``match``; factor the data
copy into an impl-region helper ``def``; map ``id`` over the sequence; and
reverse the sequence twice. No wrong impl verified and no correct impl was
rejected, so no SPEC-TOO-WEAK or SPEC-TOO-STRONG hole was found on the surface
these probes reach.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references model the
copy DEEPLY (carry the recorded ``dtype`` verbatim); there is no consumed callee
axiom for a PBT axiom lane to re-discharge (that lane is G-AX's in any case).
AXIOM_TESTS is therefore empty. The nagini AXIOM_TEST (an in-container real-callee
faithfulness probe) is dropped per the port contract — the axiom lane is G-AX's
job and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-3095"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique, entirely inside the region it edits) ----
# The full impl-region body (between -- impl-start / -- impl-end). Swapping the
# whole body keeps the spec view (and hence same_spec) byte-identical.
_IMPL_GOLD = (
    "def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do\n"
    "  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share\n"
    "  -- it on a shallow copy (content is identical either way), and re-attach the\n"
    "  -- ORIGINAL stored element type rather than re-deriving one.\n"
    "  let mut arr := v.data.values\n"
    "  if deep then\n"
    "    arr := v.data.values\n"
    "  let newData : IndexData :=\n"
    "    { values := arr, native := v.data.native, dtype := v.data.dtype }\n"
    "  return { dims := v.dims, attrs := v.attrs, data := newData }"
)
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted"

# The record-construction line that assembles the copied data wrapper — unique,
# entirely inside the impl region. Editing only its `dtype :=` / `values :=`
# field, or the outer `return { dims/attrs ... }`, keeps every other clause gold.
_I_NEWDATA = (
    "  let newData : IndexData :=\n"
    "    { values := arr, native := v.data.native, dtype := v.data.dtype }\n"
)
_I_RETURN = "  return { dims := v.dims, attrs := v.attrs, data := newData }"

# The frozen tactic body (everything after `:= by`; unique). Prepending a `have`
# for the admissibility ground instance keeps the STATEMENT byte-identical.
_PROOF_BODY = (
    "  intro deep v\n"
    "  unfold problem_spec_copy implementation_copy\n"
    "  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩\n"
)
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_copy` STATEMENT byte-identical and introduces no
    # new lemma, axiom, or assumption token.
    #
    # The first two reshape the impl while staying rfl-definitionally equal to
    # the frozen one (the frozen tactic body still closes them verbatim), so they
    # probe the spec only as far as gold already does — honest, but weak. The
    # third (`pos-elementwise-duplicate`) is deliberately NOT definitionally
    # gold: the frozen tactic body does not close it, so a clause is genuinely
    # re-proven and the spec is tested for content-equality rather than sequence
    # identity. All three are kept: the cheap two pin the frame, the third pins
    # the strength.
    # =====================================================================
    {
        "id": "pos-direct-construct",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: drop the mutable-accumulator `Id.run do` / `if`
        # branch entirely and construct the result record directly, carrying
        # every component from the input. Same value on every input.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_copy (deep : Bool) (v : IVar) : IVar :=\n"
            "  { dims := v.dims, attrs := v.attrs,\n"
            "    data := { values := v.data.values, native := v.data.native,\n"
            "              dtype := v.data.dtype } }",
        ),
        "rationale": "a correct reshape that constructs the copy directly (no "
                     "`Id.run do`, no branch) and carries dims/attrs/values/"
                     "native/dtype from the input must satisfy all five spec "
                     "clauses; if it cannot, the spec is SPEC-TOO-STRONG. Proof: "
                     "the frozen tactic body is retained — after `unfold`, `cases "
                     "deep` leaves each of the five equalities as `rfl` (the "
                     "direct construction is definitionally the recorded value). "
                     "Defends CLAUSES 1-5. No helper lemma or new declaration.",
    },
    {
        "id": "pos-reorder-locals",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: keep `Id.run do` but bind the recorded dtype, the
        # native type, and the values to named locals FIRST (reordered reads),
        # then assemble. Equivalent to gold on every input.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do\n"
            "  let keptDtype := v.data.dtype\n"
            "  let nativeType := v.data.native\n"
            "  let vals := v.data.values\n"
            "  let newData : IndexData :=\n"
            "    { values := vals, native := nativeType, dtype := keptDtype }\n"
            "  return { dims := v.dims, attrs := v.attrs, data := newData }",
        ),
        "rationale": "a correct reshape that reads the recorded dtype, the native "
                     "type, and the values into named locals (reordered) before "
                     "assembling the copy equals gold pointwise, so all five spec "
                     "clauses still hold; must verify, else SPEC-TOO-STRONG. "
                     "Proof: the frozen tactic body is retained — the `let`-bound "
                     "locals inline definitionally and each `cases deep` arm is "
                     "`rfl`. Defends CLAUSES 1-5. No helper lemma or new "
                     "declaration.",
    },

    {
        "id": "pos-elementwise-duplicate",
        "kind": "soundness",
        "expect": "verify",
        # The two positives above are honest but WEAK: each closes under the
        # frozen tactic body verbatim, i.e. each is rfl-definitionally the frozen
        # impl, so neither exercises the spec beyond what gold already does. This
        # one is NOT definitionally gold — measured: with the frozen tactic body
        # retained it FAILS to build (the values clause is no longer `rfl`), so it
        # needs a genuine re-proof of CLAUSE 3 and therefore tests that the spec
        # accepts a copy whose element sequence is rebuilt rather than aliased.
        # A deep copy duplicates the sequence element-by-element (observably the
        # same content); a shallow copy shares it — the real distinction the
        # `deep` flag names, modeled as far as this carrier can see it.
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                "def implementation_copy (deep : Bool) (v : IVar) : IVar :=\n"
                "  let dup := if deep then v.data.values.map id else v.data.values\n"
                "  { dims := v.dims, attrs := v.attrs,\n"
                "    data := { values := dup, native := v.data.native,\n"
                "              dtype := v.data.dtype } }",
            ),
            _PROOF_BODY,
            "  intro deep v\n"
            "  unfold problem_spec_copy implementation_copy\n"
            "  cases deep <;> refine ⟨rfl, rfl, ?_, rfl, rfl⟩ <;> simp\n",
        ),
        "rationale": "a correct reshape that REBUILDS the element sequence on a "
                     "deep copy (element-wise duplication) instead of aliasing it, "
                     "and shares it on a shallow copy, must still satisfy all five "
                     "clauses — the duplicated sequence has the same content, which "
                     "is all CLAUSE 3 asks. Unlike the two positives above this is "
                     "NOT definitionally the frozen impl: the frozen tactic body "
                     "does not close it, so CLAUSE 3 is re-proven (`simp` discharges "
                     "`(v.data.values.map id) = v.data.values`) rather than being "
                     "`rfl`. If the spec rejected this it would be SPEC-TOO-STRONG: "
                     "it would be demanding sequence IDENTITY where it should demand "
                     "content equality. Defends CLAUSES 1-5. The re-proof stays "
                     "inside the proof region; no helper lemma, axiom, or new "
                     "declaration is introduced and the theorem STATEMENT is "
                     "byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the behavior is total, so `∀` is unguarded), so nagini's
    # precondition-admission probe has no binder to attack here; the honest
    # analogue is to discharge the spec predicate at the F2P ground input (a deep
    # copy of a fixed-width-text value whose recorded dtype differs from its
    # native type) inside the proof region, alongside the frozen obligation. If
    # that ground instance could not be discharged, the modeled behavior would be
    # unsatisfiable at exactly the discriminating input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-text-deep-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_copy true\n"
            "      { dims := [\"x\"], attrs := [(\"foo\", \"bar\")],\n"
            "        data := { values := [\"baz\"], native := Dtype.object, dtype := Dtype.unicode 3 } }\n"
            "      (implementation_copy true\n"
            "        { dims := [\"x\"], attrs := [(\"foo\", \"bar\")],\n"
            "          data := { values := [\"baz\"], native := Dtype.object, dtype := Dtype.unicode 3 } }) := by\n"
            "    unfold problem_spec_copy implementation_copy\n"
            "    decide\n"
            + _PROOF_BODY,
        ),
        "rationale": "the obligation is discharged at the F2P ground input (a deep "
                     "copy of a fixed-width-text value: native = object catch-all "
                     "but recorded dtype = unicode 3, the discriminating shape) by "
                     "`decide`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the spec is unsatisfiable at the normal "
                     "discriminating input, the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: the theorem STATEMENT is byte-identical, "
                     "the ground instance is a `have` inside the existing tactic "
                     "body, and no new declaration/axiom/`sorry` is introduced.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve, so a verifying
    # rival would be a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness pinning the violation at one
    # concrete input (checked to hold of the rival and fail on gold).
    # =====================================================================

    # ---- CLAUSE 5 (the recorded element type = the change) ----
    {
        "id": "weak-rederive-from-sequence",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: on a deep copy take the copied wrapper's recorded
        # type from the underlying sequence (native) instead of the recorded
        # dtype. Correct on the numeric sub-domain (native = dtype), wrong on the
        # fixed-width-text shape (native = catch-all != dtype). Diverges only on
        # CLAUSE 5, and only for deep = true.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do\n"
            "  let mut arr := v.data.values\n"
            "  let mut dt := v.data.dtype\n"
            "  if deep then\n"
            "    arr := v.data.values\n"
            "    dt := v.data.native\n"
            "  let newData : IndexData :=\n"
            "    { values := arr, native := v.data.native, dtype := dt }\n"
            "  return { dims := v.dims, attrs := v.attrs, data := newData }",
        ),
        "refinement": "this is the pre-patch behaviour: on a deep copy the wrapper "
                      "is rebuilt from the duplicated sequence ALONE, so its "
                      "recorded type is re-derived from the sequence. For a "
                      "fixed-width-text value the sequence's re-derived type is the "
                      "generic catch-all, so the recorded type collapses to the "
                      "catch-all — casting the text type away. The F2P observable "
                      "pins the recorded type to survive a deep copy, so a faithful "
                      "patch that re-derives it FAILS the discriminating F2P and "
                      "does NOT resolve. (Correct on numeric values where the two "
                      "types coincide, hence PARTIAL-DOMAIN.)",
        "rationale": "REJECT from CLAUSE 5 (`result.data.dtype = v.data.dtype`): on "
                     "the text witness (deep = true, native = object catch-all != "
                     "dtype = unicode 3) the rival yields native, so "
                     "`result.data.dtype = v.data.native != v.data.dtype`. The spec "
                     "pins the RECORDED type, so the re-derived one is refuted. "
                     "Varies binder `deep` at true and `v` at the discriminating "
                     "text shape.",
        "witness": (
            "-- Refuted on a deep copy of a fixed-width-text value: the recorded\n"
            "-- element type (unicode 3) must survive, but the rival substitutes\n"
            "-- the re-derived catch-all type (object) taken from the sequence.\n"
            "example : ¬ problem_spec_copy true\n"
            "    { dims := [\"x\"], attrs := [(\"foo\", \"bar\")],\n"
            "      data := { values := [\"baz\"], native := Dtype.object, dtype := Dtype.unicode 3 } }\n"
            "    (implementation_copy true\n"
            "      { dims := [\"x\"], attrs := [(\"foo\", \"bar\")],\n"
            "        data := { values := [\"baz\"], native := Dtype.object, dtype := Dtype.unicode 3 } }) := by\n"
            "  unfold problem_spec_copy implementation_copy\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-const-catchall-dtype",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse the copied wrapper's recorded type to the generic catch-all
        # unconditionally (the lossy fallback). Correct only when the original's
        # recorded type is already the catch-all; wrong on every other type.
        # Refuted at a SHALLOW copy so the `deep = false` flag is also exercised.
        "module": _swap(
            _BASE, _I_NEWDATA,
            "  let newData : IndexData :=\n"
            "    { values := arr, native := v.data.native, dtype := Dtype.object }\n",
        ),
        "refinement": "hard-coding the copied wrapper's recorded type to the "
                      "generic catch-all reports the catch-all for every copied "
                      "value regardless of its recorded type. The copy tests pin "
                      "the ORIGINAL recorded type to survive for numeric AND text "
                      "values, so the catch-all mismatches everywhere the recorded "
                      "type is not already the catch-all — a faithful such patch "
                      "FAILS the copy tests and does NOT resolve. It happens to "
                      "agree only on the already-catch-all sub-domain.",
        "rationale": "REJECT from CLAUSE 5 (`result.data.dtype = v.data.dtype`): at "
                     "a shallow copy of a value whose recorded type is unicode 5 "
                     "the spec requires unicode 5 but the rival returns the "
                     "catch-all object, so `result.data.dtype != v.data.dtype`. "
                     "Correct only when the recorded type is already object, hence "
                     "PARTIAL-DOMAIN. Varies binder `deep` at false and `v` at a "
                     "distinct text shape (native = object, dtype = unicode 5).",
        "witness": (
            "-- Refuted on a shallow copy of a fixed-width-text value: the recorded\n"
            "-- element type (unicode 5) must survive, but the rival always reports\n"
            "-- the generic catch-all type (object).\n"
            "example : ¬ problem_spec_copy false\n"
            "    { dims := [\"y\"], attrs := [(\"a\", \"b\")],\n"
            "      data := { values := [\"p\", \"q\"], native := Dtype.object, dtype := Dtype.unicode 5 } }\n"
            "    (implementation_copy false\n"
            "      { dims := [\"y\"], attrs := [(\"a\", \"b\")],\n"
            "        data := { values := [\"p\", \"q\"], native := Dtype.object, dtype := Dtype.unicode 5 } }) := by\n"
            "  unfold problem_spec_copy implementation_copy\n"
            "  decide\n"
        ),
    },

    # ---- CLAUSE 4 (the underlying-sequence element type) ----
    # CLAUSE 4 is independently LOAD-BEARING and gets its own rival. Measured
    # with the real verifier: delete `result.data.native = v.data.native` from
    # the postcondition and the rival below VERIFIES against the weakened spec
    # (exit 0), so no other clause catches it — a positive control cannot defend
    # a clause, since a correct impl satisfies every clause whether or not the
    # spec states it. The rival is refuted at a NUMERIC-COINCIDENT shape
    # (native = dtype = other 7), which is what keeps it a clause-4 attack and
    # not a second clause-5 attack: it leaves the recorded `dtype` untouched and
    # diverges only on the underlying-sequence type.
    {
        "id": "weak-clobber-native",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the copied wrapper's underlying-sequence type as the generic
        # catch-all instead of carrying the original's. Diverges only on
        # CLAUSE 4; the recorded `dtype` is still carried over faithfully.
        "module": _swap(
            _BASE, _I_NEWDATA,
            "  let newData : IndexData :=\n"
            "    { values := arr, native := Dtype.object, dtype := v.data.dtype }\n",
        ),
        "refinement": "the copy's underlying sequence is the original's sequence "
                      "(duplicated or shared), so the element type that sequence "
                      "reports must come over with it. A patch that reported the "
                      "generic catch-all for the copy's sequence instead would "
                      "describe a copy whose sequence disagrees with the source's "
                      "on a value where the source's sequence is NOT the catch-all "
                      "(any numeric element type), so the copy is not identical to "
                      "the original and the copy tests over numeric element types "
                      "FAIL — such a patch does NOT resolve. Correct only on the "
                      "already-catch-all sub-domain, hence PARTIAL-DOMAIN.",
        "rationale": "REJECT from CLAUSE 4 (`result.data.native = v.data.native`): "
                     "at a shallow copy of a numeric-coincident value (native = "
                     "dtype = other 7) the spec requires the copy's "
                     "underlying-sequence type to be other 7 but the rival returns "
                     "object, so `result.data.native != v.data.native`. CLAUSE 5 is "
                     "NOT what refutes it — the recorded dtype is carried over "
                     "correctly — which is why the witness is pinned at a shape "
                     "where native = dtype. Varies binder `deep` at false and `v` "
                     "at a sixth distinct shape.",
        "witness": (
            "-- Refuted on a copy of a value whose underlying sequence reports a\n"
            "-- concrete (non-catch-all) element type: that type must come over\n"
            "-- with the sequence, but the rival reports the catch-all instead.\n"
            "-- The recorded dtype is untouched here, so this pins CLAUSE 4 alone.\n"
            "example : ¬ problem_spec_copy false\n"
            "    { dims := [\"w\"], attrs := [(\"c\", \"d\")],\n"
            "      data := { values := [\"r\", \"s\"], native := Dtype.other 7, dtype := Dtype.other 7 } }\n"
            "    (implementation_copy false\n"
            "      { dims := [\"w\"], attrs := [(\"c\", \"d\")],\n"
            "        data := { values := [\"r\", \"s\"], native := Dtype.other 7, dtype := Dtype.other 7 } }) := by\n"
            "  unfold problem_spec_copy implementation_copy\n"
            "  decide\n"
        ),
    },

    # ---- CLAUSE 1 (dims) — frame discipline on the surrounding metadata ----
    {
        "id": "weak-drop-dims",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame violation: return empty dimension names instead of carrying the
        # original's. Diverges only on CLAUSE 1.
        "module": _swap(
            _BASE, _I_RETURN,
            "  return { dims := [], attrs := v.attrs, data := newData }",
        ),
        "refinement": "dropping the dimension names produces a copy that no longer "
                      "names its axes; a copy that faithfully lost the dims would "
                      "not be identical to the original and the copy tests (which "
                      "assert the copy is identical to the source) FAIL, so such a "
                      "patch does NOT resolve. Frame-discipline analogue: a "
                      "carried-over component must be reproduced, not blanked.",
        "rationale": "REJECT from CLAUSE 1 (`result.dims = v.dims`): at a variable "
                     "with dims = [\"z\"] the spec requires the copy to carry "
                     "[\"z\"] but the rival returns [], so `result.dims != v.dims`. "
                     "Varies binder `deep` at true and `v` at a numeric-coincident "
                     "shape with a non-empty distinct `dims`.",
        "witness": (
            "-- Refuted where the source names a dimension: the copy must carry the\n"
            "-- same dimension names, but the rival blanks them.\n"
            "example : ¬ problem_spec_copy true\n"
            "    { dims := [\"z\"], attrs := [(\"k\", \"v\")],\n"
            "      data := { values := [\"m\"], native := Dtype.other 1, dtype := Dtype.other 1 } }\n"
            "    (implementation_copy true\n"
            "      { dims := [\"z\"], attrs := [(\"k\", \"v\")],\n"
            "        data := { values := [\"m\"], native := Dtype.other 1, dtype := Dtype.other 1 } }) := by\n"
            "  unfold problem_spec_copy implementation_copy\n"
            "  decide\n"
        ),
    },

    # ---- CLAUSE 2 (attrs) — frame discipline on the surrounding metadata ----
    {
        "id": "weak-drop-attrs",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame violation: return empty attributes instead of carrying the
        # original's. Diverges only on CLAUSE 2. Refuted at a SHALLOW copy.
        "module": _swap(
            _BASE, _I_RETURN,
            "  return { dims := v.dims, attrs := [], data := newData }",
        ),
        "refinement": "discarding the attributes produces a copy that loses the "
                      "source's metadata; a copy that faithfully dropped the attrs "
                      "would not be identical to the original and the copy tests "
                      "(which assert identity, including attributes) FAIL, so such "
                      "a patch does NOT resolve. Frame-discipline analogue on a "
                      "second carried-over component.",
        "rationale": "REJECT from CLAUSE 2 (`result.attrs = v.attrs`): at a "
                     "variable with attrs = [(\"foo\", \"bar\")] the spec requires "
                     "the copy to carry them but the rival returns [], so "
                     "`result.attrs != v.attrs`. Varies binder `deep` at false and "
                     "`v` at a distinct numeric-coincident shape with a non-empty "
                     "`attrs`.",
        "witness": (
            "-- Refuted where the source has attributes: the copy must carry the\n"
            "-- same attributes, but the rival discards them.\n"
            "example : ¬ problem_spec_copy false\n"
            "    { dims := [\"d\"], attrs := [(\"foo\", \"bar\")],\n"
            "      data := { values := [\"n\"], native := Dtype.other 2, dtype := Dtype.other 2 } }\n"
            "    (implementation_copy false\n"
            "      { dims := [\"d\"], attrs := [(\"foo\", \"bar\")],\n"
            "        data := { values := [\"n\"], native := Dtype.other 2, dtype := Dtype.other 2 } }) := by\n"
            "  unfold problem_spec_copy implementation_copy\n"
            "  decide\n"
        ),
    },

    # ---- CLAUSE 3 (values) — the copied element sequence ----
    {
        "id": "weak-drop-values",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame violation on the data payload: return an empty element sequence
        # instead of the copied one. Diverges only on CLAUSE 3.
        "module": _swap(
            _BASE, _I_NEWDATA,
            "  let newData : IndexData :=\n"
            "    { values := [], native := v.data.native, dtype := v.data.dtype }\n",
        ),
        "refinement": "returning an empty element sequence produces a copy that "
                      "drops the data payload; a copy that faithfully lost its "
                      "values would not equal the source and the copy tests (which "
                      "assert the copied values match) FAIL, so such a patch does "
                      "NOT resolve. This attacks the copied-content clause "
                      "independently of the type clauses.",
        "rationale": "REJECT from CLAUSE 3 (`result.data.values = v.data.values`): "
                     "at a variable whose values = [\"baz\"] the spec requires the "
                     "copy to carry [\"baz\"] but the rival returns [], so "
                     "`result.data.values != v.data.values`. Varies binder `deep` "
                     "at true and `v` at a distinct numeric-coincident shape.",
        "witness": (
            "-- Refuted where the source carries element values: the copy must\n"
            "-- reproduce the same values, but the rival returns an empty sequence.\n"
            "example : ¬ problem_spec_copy true\n"
            "    { dims := [\"c\"], attrs := [(\"g\", \"h\")],\n"
            "      data := { values := [\"baz\"], native := Dtype.other 3, dtype := Dtype.other 3 } }\n"
            "    (implementation_copy true\n"
            "      { dims := [\"c\"], attrs := [(\"g\", \"h\")],\n"
            "        data := { values := [\"baz\"], native := Dtype.other 3, dtype := Dtype.other 3 } }) := by\n"
            "  unfold problem_spec_copy implementation_copy\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model callee to re-discharge here: the copy is
# modeled directly (every result component is an equality against the input), so
# there is no in-model axiom obligation for the PBT axiom lane. The nagini
# AXIOM_TEST (a real-callee faithfulness probe) is dropped — that lane is G-AX's.
AXIOM_TESTS = []

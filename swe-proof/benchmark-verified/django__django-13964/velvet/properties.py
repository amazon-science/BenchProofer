"""properties.py — G-PBT falsification battery for django__django-13964 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct fillEmptyKeyRefs`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is judged by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and be
REFUTED against a verifying impl of the same spec; here that subject is the
named ``witness_reference``, for the reason in the CARRIER NOTE).

DEFENDED SURFACE (one contracted method over a finite list of stored
references). The single obligation is

    fillEmptyKeyRefs (refs : List KeyRef)
        require ∀ r ∈ refs, r.targetKey ≠ absentValue
        ensures out = resolvedKeys refs

with ``resolvedKeys`` mapping, element by element and in order,
``resolvedKey stored targetKey = if isEmpty stored then targetKey else stored``:
for each reference, when the recorded key is EMPTY (absent, an empty text value,
or an empty collection — the structural notion of an empty value, not merely an
absent one) the referenced object's key is adopted; otherwise the recorded key
is kept unchanged. ``refs`` is the sole input binder; each element carries a
``stored`` field (the recorded key) and a ``targetKey`` field (the key now
carried by the referenced object). The load-bearing content is the WIDENED
trigger: an empty-but-present recorded key (canonically the empty string used
for a non-numeric primary key) is filled, where the pre-image filled only the
strictly-absent case.

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``PyVal`` is an inductive with ``DecidableEq``, and ``isEmpty`` /
``resolvedKey`` / ``resolvedKeys`` are concrete ``def``s in the ``pure`` region
(the ``axioms`` region declares nothing). So each rival's violation reduces to a
decidable equality of concrete values and a ``decide`` witness at a small
literal input states it. The reject lane is therefore fully expressible — no
NO-REJECT-LANE collapse. The method ALSO carries a real ``require`` clause, so
the admissibility class is not vacuous either.

WHY EVERY REJECT NAMES A ``witness_reference`` (measured, not argued). The
FROZEN impl keeps a ``while`` loop, and under
``set_option loom.semantics.choice "demonic"`` that loop's fixpoint elaborates
through ``Classical.choice``, which the kernel cannot unfold. So ``decide``
against the frozen tester is stuck for EVERY claim, true or false, and the
frozen-side exit code carries NO information — the ``witness-undecided``
pathology. Measured on this bundle, two builds, one error:

    frozen + the real witness (``... = false``)  -> exit 1,
        `Tactic `decide` failed ... did not reduce to `isTrue` or `isFalse``
    frozen + the OPPOSITE claim (``... = true``) -> exit 1, IDENTICAL error

Had these cases been left to be refuted against gold, a forged witness
asserting a rival is CORRECT would have cleared both halves. The repair is the
sanctioned one: every reject case names ``_LOOPFREE`` as its
``witness_reference`` — a loop-free impl that returns the resolved-key list
directly, shares the frozen spec, and VERIFIES (shipped as the
``pos-closed-form`` positive, so the battery itself records that loop-freeness
is not what any rival is rejected for). Against it the tester genuinely reduces
and ``decide`` REFUTES each witness semantically:
``Tactic `decide` proved that the proposition ... = false is false`` (exit 1,
all five). The reference was also confirmed to be a two-way oracle, not an impl
that fails everything: a TRUE claim about it PROVES (exit 0). That is the
discrimination a stuck gold-side build cannot supply.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``fillEmptyKeyRefsTester args = false`` says the extracted program's result
violates the postcondition at that concrete input, checked in a file whose
``prove_correct`` block has been stripped (no tactic script can mask the
verdict). No witness binds a hypothesis — every input is a concrete literal — so
no witness can be inconsistent and no consistency probe is needed.

WITNESS PLACEMENT. The five rejects probe five DISTINCT input points, so the
input binder ``refs`` — and the ``stored`` / ``targetKey`` fields it carries —
is genuinely varied rather than pinned. Both branches of ``resolvedKey`` are
attacked (empty-stored adoption AND non-empty-stored preservation), the exact
adopted value is pinned both by a wholly-wrong value and by a NEAR-MISS that
gets all but the last character right, and the traversal order is attacked at a
two-element list.

DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
is REJECTED rather than admitted. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
two lines have to move together, and they do here. Under the total scope a
postcondition is claimed of ALL runs, not only of terminating ones, and the
verifier emits a descent obligation ``measure b' < measure b`` for every loop
in the impl (1 loop here, measure ``i``). A rival that loops without a measure
is refused outright (``Decreasing annotations are required in total correctness
semantics``), and a rival that supplies a CONSTANT measure to dodge that is
refused on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin <
spin``), re-measured on this bundle with a real build. Divergence therefore
does not discharge the ``ensures`` clauses vacuously. It is still not shipped
as a G-PBT reject case, and the reason is the witness contract rather than a
spec weakness. A reject case must carry a witness that ELABORATES
against the rival, and neither diverging shape gets past that. With NO measure
the descent obligation fails at the ``method`` itself, ahead of any appended
tester, and the witness file retains the ``method`` (it strips only the
``prove_correct`` obligations), so the rival module does not compile at all. With
a measure that does not decrease the refusal moves to the ``prove_correct`` site,
which IS stripped, so that module does elaborate; but the rival's post-image is
then an unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
``onDoneGadget`` / ``decreasingGadget``, which the kernel will not normalise to a
value a concrete-input tester can decide. Either way the gate returns
``witness-unproven``, an inconclusive outcome. Measured through
the gate's own ``_check_witness``, even ``example : True := trivial`` comes
back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
would fail the whole battery rather than pass a case. That is the right
behavior: a diverging impl has no output at any input, so there is no value for
a witness to disagree with, and its rejection is a judgement of the termination
obligation rather than a postcondition violation at a point. Recorded as
REJECTED-BY-SPEC and not expressible as a witnessed case, which is neither a
spec hole nor a battery gap.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
notion of an empty value is an A-reference validated by axiom_check.py (G-AX's
job), not a consumed contract. The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13964"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating loop over
# the references. Reject rivals replace this with a loop-free closed form (so
# their tester reduces under `decide`).
_IMPL = """    let mut result : List PyVal := []
    let mut i := refs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ refs.length
      invariant result = resolvedKeys (refs.drop i)
      done_with i = 0
      decreasing i
    do
      let r := refs[i - 1]!
      result := resolvedKey r.stored r.targetKey :: result
      i := i - 1
    return result"""
assert _BASE.count(_IMPL) == 1, "fillEmptyKeyRefs impl region drifted from expected text"

# The three per-iteration loop lines; a positive control may reshape them while
# keeping the loop and the invariant, so the frozen proof still closes.
_LOOP_BODY = """      let r := refs[i - 1]!
      result := resolvedKey r.stored r.targetKey :: result
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop body drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    let mut result : List PyVal := []"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A positive control that collapses the loop to the closed form the
# post-image names retunes this to a bare `loom_solve`; the tactic body is
# elided from the spec view, so this is a proof reshape, not a spec change.
_PROOF = """prove_correct fillEmptyKeyRefs by
  loom_solve
  rw [resolvedKeys_drop_step refs i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. A loop-free impl that returns the resolved-key list
# directly: it shares the frozen spec and it VERIFIES, so it cannot violate the
# postcondition at any input and a genuine witness must be refuted against it.
# Unlike the frozen impl it contains no `while`, so its tester REDUCES and the
# refutation is decided rather than stuck (see the CARRIER NOTE). Shipped as the
# `pos-closed-form` positive below, so the gate independently records that this
# impl verifies and that loop-freeness is not what any rival is rejected for.
# One text shared by every reject case, so the gate verifies it exactly once.
# ---------------------------------------------------------------------------
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL, "    return (resolvedKeys refs)"),
    _PROOF, "prove_correct fillEmptyKeyRefs by\n  loom_solve")


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `fillEmptyKeyRefsTester args = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
_TESTER = (
    "extract_program_for fillEmptyKeyRefs\n"
    "prove_precondition_decidable_for fillEmptyKeyRefs\n"
    "prove_postcondition_decidable_for fillEmptyKeyRefs\n"
    "derive_tester_for fillEmptyKeyRefs\n\n"
)


def _witness(refs_literal):
    return _TESTER + f"example : fillEmptyKeyRefsTester {refs_literal} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = resolvedKeys refs`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same resolved-key list; the loop-specific
        # proof is retuned to a bare `loom_solve` since the impl now matches the
        # post-image syntactically. This is ALSO the `witness_reference` every
        # reject case is refuted against, so the gate's record of this case
        # verifying is what licenses that whole lane.
        "module": _LOOPFREE,
        "rationale": "a loop-free impl that returns the resolved-key list directly "
                     "must satisfy `out = resolvedKeys refs`; a correct reshape of "
                     "the modeled behaviour verifying is exactly what "
                     "SPEC-TOO-STRONG would deny. Exercises the obligation from a "
                     "maximally different (loop-free) control-flow shape, and is "
                     "shipped as the shared `witness_reference` so the battery "
                     "records on its own that loop-freeness is not the ground any "
                     "rival is rejected on.",
    },
    {
        "id": "pos-inverted-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the loop and the invariant, but INVERT the per-reference
        # guard and swap its branches — test `stored` for NON-emptiness and keep
        # it in the `then`, adopting `targetKey` in the `else`. This is the true
        # analogue of the sibling's guard-inversion positive.
        #
        # An earlier revision shipped a let-bind reshape here instead
        # (`let k := resolvedKey r.stored r.targetKey; result := k :: result`).
        # That was a DEFECTIVE positive: a `let` is zeta-reducible, so the impl
        # was DEFINITIONALLY EQUAL to the frozen one and the frozen proof body
        # closed it byte-for-byte untouched. It verified honestly while testing
        # nothing beyond what the frozen file already establishes. The inverted
        # guard is not definitionally equal — `if !(isEmpty s) then s else t` and
        # `resolvedKey s t` reduce to each other only after a CASE SPLIT on
        # `isEmpty s`, which is why this case must supply the `inv` lemma before
        # `loom_solve` rather than reusing the frozen script verbatim. That is
        # what makes it a real exercise of the obligation from a reshaped surface.
        "module": _swap(
            _swap(
                _BASE, _LOOP_BODY,
                "      let r := refs[i - 1]!\n"
                "      result := (if !(isEmpty r.stored) then r.stored"
                " else r.targetKey) :: result\n"
                "      i := i - 1"),
            _PROOF,
            "prove_correct fillEmptyKeyRefs by\n"
            "  have inv : ∀ s t : PyVal,\n"
            "      (if !(isEmpty s) then s else t) = resolvedKey s t := by\n"
            "    intro s t\n"
            "    cases h : isEmpty s <;> simp [resolvedKey, h]\n"
            "  loom_solve\n"
            "  rw [resolvedKeys_drop_step refs i (by omega) (by omega)]\n"
            "  simp_all [inv]"),
        "rationale": "inverting the per-reference guard and swapping its branches "
                     "computes the same list element-for-element, so "
                     "`out = resolvedKeys refs` still holds and a correct reshape "
                     "must verify. Unlike a let-bind reshape this is NOT "
                     "definitionally equal to the frozen impl — the two agree only "
                     "after a case split on `isEmpty stored`, so the case genuinely "
                     "re-discharges the obligation rather than re-running the frozen "
                     "proof. (Sibling: pos-reorder, whose transformation is exactly "
                     "this guard inversion.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries a `require` clause, so the domain is
    # not total; the residual risk is that the post-image is UNSATISFIABLE /
    # DEGENERATE at the interesting point (a spec no impl can meet reads like a
    # spec every impl meets). This case discharges an in-region assert at an
    # F2P-shaped point, establishing that the post-image really does demand
    # ADOPTION when the recorded key is an empty-but-present value AND
    # PRESERVATION when it is non-empty — the two branches of the per-element
    # decision. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the assert is live (a false claim about the
    # same point leaves an unsolved goal), and the proof's alternation gains one
    # `decide` arm to close the ground assert. Both probed inputs satisfy the
    # `require` clause, so the precondition is shown inhabited on a normal input.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `assert\n"
                "      (resolvedKeys [{stored := PyVal.pyStr [], targetKey := PyVal.pyStr ['j']}]\n"
                "         = [PyVal.pyStr ['j']] ∧\n"
                "       resolvedKeys [{stored := PyVal.pyStr ['x'], targetKey := PyVal.pyStr ['j']}]\n"
                "         = [PyVal.pyStr ['x']]))\n"
                + _IMPL_TOP),
            _PROOF,
            "prove_correct fillEmptyKeyRefs by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [resolvedKeys_drop_step refs i (by omega) (by omega)]; simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: it demands the referenced key be ADOPTED "
                     "when the recorded key is an empty-but-present value (empty "
                     "text) and the recorded key be KEPT when it is non-empty. The "
                     "in-region assert must discharge (else the obligation is "
                     "unsatisfiable / PRECOND-TOO-STRONG); the impl is kept verbatim "
                     "so `out = resolvedKeys refs` still verifies. Both inputs meet "
                     "the `require` clause, so the precondition is inhabited on a "
                     "normal input. (Sibling: admiss-empty-string, re-aimed.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test. Each names `_LOOPFREE` as its
    # witness_reference: the frozen tester cannot decide anything (CARRIER
    # NOTE), so refuting against gold would attest to a refutation never
    # performed.
    # =====================================================================
    {
        "id": "weak-none-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image behaviour: a recorded key is filled ONLY when it is
        # strictly absent, NOT when it is an empty-but-present value such as the
        # empty text used for a non-numeric primary key. Correct on the absent
        # and non-empty sub-domains; diverges exactly on the empty-but-present
        # sub-domain — the case the desired behaviour adds.
        "module": _swap(
            _BASE, _IMPL,
            "    return (refs.map (fun r =>\n"
            "      if r.stored = PyVal.pyNone then r.targetKey else r.stored))"),
        "refinement": "this is the literal pre-image: filling only the strictly "
                      "absent recorded key leaves an empty-but-present key (the "
                      "empty text of a non-numeric primary key) unfilled, so the "
                      "referring row keeps the empty key instead of the referenced "
                      "object's key — exactly the data-loss the failing test "
                      "catches. It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedKeys refs`: at a one-element list "
                     "whose recorded key is an empty-but-present value, the "
                     "post-image demands the referenced key be adopted while the "
                     "impl keeps the empty key. Refuted on the empty-but-present "
                     "sub-domain (`isEmpty stored` true, `stored ≠ pyNone`). "
                     "(Sibling: partial-none-only.)",
        "witness": _witness(
            "[{stored := PyVal.pyStr [], targetKey := PyVal.pyStr ['j']}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the emptiness guard: ALWAYS adopt the referenced key. Correct on
        # every empty recorded key; diverges on the non-empty sub-domain, where
        # it clobbers a deliberately-recorded key with the referenced one.
        "module": _swap(
            _BASE, _IMPL, "    return (refs.map (fun r => r.targetKey))"),
        "refinement": "a counterpart that unconditionally adopts the referenced "
                      "key overwrites a deliberately-recorded, non-empty key; the "
                      "pre-existing tests that record a key deliberately and assert "
                      "it is preserved after save would break. It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedKeys refs`: at a one-element list "
                     "whose recorded key is non-empty, the post-image demands the "
                     "recorded key be KEPT while the impl adopts the referenced "
                     "one. Refuted on the non-empty sub-domain (`isEmpty stored` "
                     "false) — the branch weak-none-only agrees with gold on. "
                     "(Sibling: clobber-deliberate-key.)",
        "witness": _witness(
            "[{stored := PyVal.pyStr ['x'], targetKey := PyVal.pyStr ['j']}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # On the empty sub-domain, store a FIXED plausible non-empty key instead
        # of the referenced object's actual key. Fires on the right sub-domain
        # (every empty recorded key) and yields a non-empty result, but the
        # CONTENTS are wrong — this attacks whether the post-image pins the EXACT
        # adopted value, not merely that something non-empty is stored.
        "module": _swap(
            _BASE, _IMPL,
            "    return (refs.map (fun r =>\n"
            "      if isEmpty r.stored then PyVal.pyInt 0 else r.stored))"),
        "refinement": "a counterpart that fills an empty recorded key with a "
                      "fixed/wrong value instead of the referenced object's key "
                      "sets the referring row's key to the wrong value; the "
                      "failing test asserts it equals the referenced object's key, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from `out = resolvedKeys refs`: at an empty recorded "
                     "key the post-image pins the adopted value to the reference's "
                     "`targetKey`, and the impl stores a fixed value distinct from "
                     "it. Refuted at a distinct (stored, targetKey) pair (an empty "
                     "collection and an integer key) so the field shapes are not "
                     "held fixed. (Sibling: value-double-mask.)",
        "witness": _witness(
            "[{stored := PyVal.pyColl 0, targetKey := PyVal.pyInt 7}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-truncate-adopted",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the adopted CONTENTS: fire on exactly the right
        # sub-domain and adopt the referenced object's key, but drop its last
        # character. Strictly closer to the desired behaviour than
        # weak-wrong-value — it agrees with gold on every non-text key and on
        # every non-empty recorded key, and even on text keys it gets all but
        # the final character right — so it earns its OWN witness rather than
        # sharing weak-wrong-value's.
        #
        # The witness is stated at a MULTI-CHARACTER key so the refutation
        # exhibits a truncation that is genuinely partial (`['a','b','c']` ->
        # `['a','b']`, a non-empty but wrong key) rather than the degenerate
        # collapse to the empty key that a length-1 target produces. Measured, so
        # the claim is not overstated: this rival is ALSO refutable at a length-1
        # key (rebuilt against the reference impl, exit 0), so the 3-character
        # point is what makes the counterexample INFORMATIVE about exact
        # contents, not what makes it possible.
        "module": _swap(
            _BASE, _IMPL,
            "    return (refs.map (fun r =>\n"
            "      if isEmpty r.stored then\n"
            "        (match r.targetKey with\n"
            "         | PyVal.pyStr cs => PyVal.pyStr cs.dropLast\n"
            "         | v => v)\n"
            "      else r.stored))"),
        "refinement": "a counterpart that adopted the referenced object's key but "
                      "stored a truncated copy of it (a stray slice) would leave "
                      "the referring row holding a key one character short of the "
                      "referenced object's; the failing test asserts the two are "
                      "EQUAL, so a near-miss fails it just as a wholly wrong value "
                      "does. It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedKeys refs`: the post-image pins "
                     "the adopted value to `targetKey` EXACTLY, so dropping its "
                     "last character violates it. Refuted at a multi-character "
                     "text key — the only witness in the battery whose key has "
                     "length > 1 — so the counterexample exhibits a PARTIAL "
                     "truncation (a non-empty but wrong key) and not merely the "
                     "collapse to an empty key a length-1 target would give. "
                     "(Sibling: partial-drop-last, ported in its own right rather "
                     "than merged: `pyStr` carries a `List Char`, so the sibling's "
                     "truncation IS expressible on this carrier.)",
        "witness": _witness(
            "[{stored := PyVal.pyStr [], targetKey := PyVal.pyStr ['a','b','c']}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve every reference correctly but emit the results in REVERSED
        # order. Every per-element decision is right; only the traversal order is
        # wrong — a clause that exists here because the carrier is a LIST of
        # references (the single-target sibling has no order to attack). Refuted
        # only on a list of length >= 2.
        "module": _swap(
            _BASE, _IMPL, "    return ((resolvedKeys refs).reverse)"),
        "refinement": "a counterpart that resolved each reference correctly but "
                      "associated the results with the wrong references (reversed "
                      "traversal) would write each referring row's key from a "
                      "different relation's referenced object; the tests assert "
                      "each row adopts ITS OWN referenced key. It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedKeys refs`: `resolvedKeys` fixes "
                     "the per-index correspondence, and reversing it disagrees on "
                     "any list of length >= 2 with distinct elements. Refuted at a "
                     "two-element list — the only reject varying `refs.length` "
                     "beyond one, so the traversal-order clause the list carrier "
                     "introduces is attacked. (ADDED for the list carrier.)",
        "witness": _witness(
            "[{stored := PyVal.pyStr ['a'], targetKey := PyVal.pyStr ['z']}, "
            "{stored := PyVal.pyStr ['b'], targetKey := PyVal.pyStr ['z']}]"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 1 frame-mutation rival, 4
# uniqueness/partial-domain rivals) plus 1 AXIOM_TESTS entry. The sibling
# contracts one function, `adopt_referenced_key_if_unset`, over a SINGLE
# SaveTarget with a fractional heap permission on `related_key`; this bundle
# contracts one method, `fillEmptyKeyRefs`, over a LIST of references with a deep
# `resolvedKeys` fold and no axioms. The two surfaces model the SAME per-element
# decision (adopt the referenced key iff the recorded one is empty), so the port
# is near-1:1 with two carrier consequences: the frame-mutation rival is vacuous
# here, and the list carrier ADDS a traversal-order clause the single-target
# sibling cannot express.
#
#   sibling case              kind          -> here                    disposition
#   ---------------------------------------------------------------------------
#   pos-reorder               soundness     -> pos-inverted-guard      PORTED
#   (—)                       soundness     -> pos-closed-form         ADDED
#   admiss-empty-string       admissibility -> admiss-grounded         RE-AIMED
#   frame-write-related-key   uniqueness    -> (none)                  VACUOUS
#   partial-none-only         uniqueness    -> weak-none-only          PORTED
#   value-double-mask         uniqueness    -> weak-wrong-value        PORTED
#   partial-drop-last         uniqueness    -> weak-truncate-adopted    PORTED
#   clobber-deliberate-key    uniqueness    -> weak-clobber            PORTED
#   (—)                       uniqueness    -> weak-reversed           ADDED
#   (—)                       divergence    -> (none)                  SPEC-CLOSED
#   ax-empty-values-membership axiom        -> (none)                  G-AX
#
# PORTED (pos-reorder -> pos-inverted-guard): the sibling's correct reshape
#   (guard inverted, branches reordered) ports DIRECTLY here — invert the
#   per-reference emptiness test and swap its branches, keeping the loop and the
#   front-recursive invariant. An earlier revision shipped a let-bind reshape
#   instead, which was a defective positive: a `let` is zeta-reducible, so that
#   impl was DEFINITIONALLY EQUAL to the frozen one and the frozen proof body
#   closed it verbatim — it verified honestly while exercising nothing. The
#   inverted guard needs a case split on `isEmpty stored` (supplied as the `inv`
#   lemma), so the obligation is genuinely re-discharged. pos-closed-form is ADDED
#   to defend the obligation from a maximally different (loop-free) shape AND to
#   serve as the reject lane's `witness_reference`.
# RE-AIMED (admiss-empty-string -> admiss-grounded): the sibling establishes that
#   an F2P-shaped input meets every Requires clause. That probe survives here (the
#   `require` clause is met by both probed inputs), but the sharper residual risk
#   on this transparent carrier is a degenerate post-image, so the case is
#   re-aimed to a live in-region assert pinning BOTH branches of the per-element
#   decision (adopt on empty-but-present, keep on non-empty) at the F2P point.
# VACUOUS (frame-write-related-key): the sibling's mandatory frame-mutation rival
#   writes to the half-permission read-only `related_key`. This backend is
#   referentially transparent and `refs` is declared read-only (not `mut`), so
#   there is no read-only input to overwrite and no substitute probe. Omitted as
#   vacuous, NOT fabricated.
# PORTED (the three value rivals, each in its OWN right): partial-none-only ->
#   weak-none-only (the literal pre-image bug, refuted on the empty-but-present
#   sub-domain). clobber-deliberate-key -> weak-clobber (refuted on the non-empty
#   sub-domain). value-double-mask -> weak-wrong-value (a fixed constant instead
#   of the referenced key). partial-drop-last -> weak-truncate-adopted: an
#   earlier revision MERGED this into weak-wrong-value on the reasoning that a
#   stored `PyVal` is atomic with no character-level structure to truncate. That
#   was WRONG — `pyStr` carries a `List Char` — and the merge cost the battery its
#   only multi-character input point, leaving the exact-contents claim
#   undemonstrated on the sub-domain where a near-miss actually lives. It is
#   restored as its own case with its own witness at a 3-character key, since it
#   agrees with gold over strictly more of the domain than weak-wrong-value does
#   and so must not share its witness.
# ADDED (weak-reversed): the list carrier introduces a traversal-ORDER clause the
#   single-target sibling has no analogue for. `resolvedKeys` fixes the per-index
#   correspondence between a referring row and its own referenced object; a rival
#   that resolves each element correctly but reverses the association is refutable
#   only on a length >= 2 list.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# AXIOM_TESTS (1): dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   the structural empty-value notion against the real membership test); the
#   notion is modeled deeply here as an A-reference with no consumed axiom, and
#   this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has one input binder,
#   `refs : List KeyRef`, whose elements carry `stored` and `targetKey`, and one
#   top-level clause, `out = resolvedKeys refs`, which internally branches on
#   `isEmpty stored`. The five reject witnesses probe five DISTINCT input points
#   (pts=5): an empty-text recorded key (adopt branch), a non-empty recorded key
#   (keep branch), an empty-collection recorded key with an integer target key
#   (exact-value pin at distinct field shapes), an empty-text recorded key with a
#   3-character target key (the near-miss truncation point), and a two-element
#   list (traversal order). Thus `stored` ranges over pyStr []/pyStr ['x']/pyColl
#   0/pyStr ['a']/pyStr ['b'], `targetKey` over pyStr ['j']/pyInt 7/pyStr
#   ['a','b','c']/pyStr ['z'], the adopted key's LENGTH over 1 and 3, and
#   `refs.length` over 1 and 2 — none held fixed. Both branches of `resolvedKey`
#   are attacked, the adopted value is pinned both grossly and to the last
#   character, and the per-index order is attacked, so no rival that mishandled
#   only a fixed-value binder could slip through.
#
# INDEPENDENT AUDIT PROBES (built with the real verifier; not shipped as cases,
# recorded so the next reader need not re-measure). Neither direction found a
# hole in the frozen spec.
#   SPEC-TOO-WEAK probes — four NEW wrong impls beyond the shipped rivals, each
#   built and then refuted against the reference impl at a concrete input
#   (rival exit 0 / reference exit 1, i.e. all four are genuinely refutable):
#     * the emptiness test NARROWED so an empty collection is not counted empty
#       (refuted at `stored := pyColl 0`);
#     * the emptiness test WIDENED so the number zero counts as empty, which
#       clobbers a deliberate numeric key (refuted at `stored := pyInt 0`);
#     * the two fields of the per-element decision TRANSPOSED
#       (`resolvedKey targetKey stored`);
#     * only the head reference resolved, the tail passed through unresolved
#       (refuted at a two-element list).
#   PRECONDITION probe — an impl behaving arbitrarily where a referenced key IS
#   absent VERIFIES (exit 0), as it must: the `require` clause excludes that
#   region. Confirms the precondition is load-bearing rather than decorative,
#   and that admiss-grounded's two probed inputs sit inside the admitted domain.
#   SPEC-TOO-STRONG probes — three further CORRECT reshapes all verify once given
#   a real proof (the guard inlined rather than calling `resolvedKey`; the guard
#   inverted at the map level; a `foldr` with the opposite association). Each
#   initially failed with `unsolved goals` on the true semantic goal — a PROOF
#   gap, not a spec rejection, and each closed with a one-line induction. So the
#   spec admits faithful reshapes and the reject lane's failures are not merely
#   the frozen tactic script being brittle.
AXIOM_TESTS = []

"""properties.py — G-PBT falsification battery for sympy__sympy-14248 (lean).

NOT a Lean module; a record of adversarial cases the G-PBT runner executes
against the frozen `Solution.lean` and stamps with a verdict.

Ported from the nagini sibling's battery (tasks/sympy__sympy-14248/
properties.py). See 'PORT NOTES' at the bottom for what carried over, what
became vacuous on this carrier, and what was dropped.

Defended surface
================

ONE modeled obligation: `correct_renderSum`, quantified over every
`terms : List String` with NO precondition hypothesis, pinned by

    problem_spec_renderSum terms result  :=  result = renderSum terms

`renderSum` is a DEEPLY-SPELLED-OUT fold (`signParts` + the first-connective
elision + the single-space join), fully a function of the one input binder. It is
not an opaque answer-key: there is no `opaque` declaration and no consumed axiom
anywhere in the bundle, so a rival cannot "echo an oracle" — echoing reduces to
performing the modeled computation itself. That collapses the
ungrounded-oracle-echo class, exactly as it did on nagini.

What IS attackable is the joining discipline, and the postcondition has four
independent behavioural commitments that a rival can each violate separately:

  (a) ORDER — the summands appear left to right in input order
      (`signParts` is a left fold appending at the back);
  (b) CONNECTIVE CHOICE — a leading-minus summand contributes a subtraction
      connective, every other summand an addition connective;
  (c) BODY NORMALISATION — a leading-minus summand contributes its text with
      that minus REMOVED (`t.drop 1`), so the sign is carried by the connective
      and not duplicated in the body;
  (d) FIRST-CONNECTIVE ELISION + SPACING — the very first connective is dropped
      when it is an addition and KEPT when it is a subtraction, and the
      remaining pieces are joined with single spaces.

Each of the seven reject cases below attacks exactly one of (a)-(d) — or, in
`weak-empty-head-default`'s case, the fallback the assembly reads when there is no
connective at all — and the seven witnesses probe seven DISTINCT input points,
including all three boundary shapes the obligation must admit (the empty list, a
single positive summand, a single negative summand).

Witness mechanics on this carrier
=================================

The one input binder is `List String`, and the spec branches on
`String.startsWith`. That predicate is compiled by well-founded recursion
(`String.substrEq` loops over UTF-8 byte positions), so it does NOT reduce in the
kernel: `decide`, `rfl`, `decide +kernel`, `simp` with the full
`startsWith`/`toSubstring`/`Substring.take`/`substrEq.eq_def` unfolding set, and
`unseal` all leave the goal stuck at

    match "-B".startsWith "-", true with | ... -- did not reduce to isTrue/isFalse

Every OTHER operation the spec uses (`String.drop`, `String.intercalate`,
`List.headD`, `List.tail`, string equality on literals) reduces fine. So each
witness at a NON-EMPTY input CONDITIONS on the one non-reducing term — one
hypothesis per distinct summand literal, stating which way that literal's
leading-minus test goes — and then decides the rest. The hypotheses are the ground
truth about those literals (`"-B"` does start with `"-"`; `"A"` does not), so they
are jointly satisfiable: the gate's `False`-derivation probe was run against each
witness's binder group and fails on all of them, as required.
`weak-empty-head-default`'s witness binds nothing and needs no `simp` step at all,
because at the empty list there is no summand whose predicate could get stuck; it
decides outright, and carries no hypotheses for the probe to examine.

Because these witnesses close by `decide` on a concrete string equality, the
gold-side failure is an evaluation verdict rather than a stuck reduction: each
one fails on the frozen solution with `decide` proving `False` is false. That the
exit code tracks the CLAIM and not just the shape was confirmed per case by
building the flipped claim (the same witness with the `¬` dropped) against the
frozen solution: it fails with a DIFFERENT error (`No goals to be solved` — `simp`
having already closed the true equation), and dropping the trailing `decide` from
that flipped claim makes it BUILD, i.e. gold provably satisfies the postcondition
at every point these witnesses refute the rivals at.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14248"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- unique impl-region anchors (each occurs exactly once in Solution.lean) ---
# The whole per-summand decision, inside the loop body.
_IMPL_BRANCH = '''    if t.startsWith "-" then
      l := l ++ ["-", t.drop 1]
    else
      l := l ++ ["+", t]'''
# The subtraction arm alone (body normalisation).
_IMPL_SUB_ARM = '      l := l ++ ["-", t.drop 1]'
# The traversal.
_IMPL_FOR = "  for t in terms do"
# The first-connective elision.
_IMPL_ELIDE = '  let firstSign := if firstSign = "+" then "" else firstSign\n'
# The head projection, WITH its following line so the anchor is unique (the same
# `headD` line also appears in the pure `renderSum`, which is spec and untouchable).
_IMPL_HEAD = '''  let firstSign := l.headD "+"
  let rest := l.tail'''
# The joining step.
_IMPL_JOIN = '  return firstSign ++ String.intercalate " " rest'
# The whole result-assembly tail.
_IMPL_TAIL = '''  let firstSign := l.headD "+"
  let rest := l.tail
  let firstSign := if firstSign = "+" then "" else firstSign
  return firstSign ++ String.intercalate " " rest'''

# ---- unique proof-region anchors ---------------------------------------------
_PROOF_INTRO = '''  intro terms
  unfold problem_spec_renderSum implementation_renderSum renderSum'''
_PROOF_TAIL = '''  simp only [Id.run]
  rw [key]
  rfl'''
_HELPER_STMT = '''    (Id.run (forIn terms init (fun t r =>
        if t.startsWith "-" = true then
          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
        else
          pure (ForInStep.yield (r ++ ["+", t])))))'''
_HELPER_BODY = '''      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]'''
_PROOF_KEY = '''  have key : (forIn terms ([] : List String) (fun t r =>
      if t.startsWith "-" = true then do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
      else do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
      = signParts terms := loop_helper_renderSum terms []'''


# =========================== WITNESS CONSTRUCTION =============================
# One hypothesis per DISTINCT summand literal appearing in the probed input,
# stating the ground truth about that literal's leading-minus test. Weakest
# assumption set the refutation needs: nothing is assumed about any other
# string, and no literal is constrained twice.
_HYP = {
    "A": 'hA : ("A").startsWith "-" = false',
    "B": 'hB : ("B").startsWith "-" = false',
    "-B": 'hnB : ("-B").startsWith "-" = true',
    "-A*B": 'hnAB : ("-A*B").startsWith "-" = true',
}


def _witness(terms):
    """Refutation of the postcondition at the concrete input `terms`.

    States `¬ problem_spec_renderSum terms (implementation_renderSum terms)`:
    unfold both sides, rewrite away the one non-reducing predicate with the
    conditioning hypotheses, then decide the resulting concrete string equality.
    """
    seen = list(dict.fromkeys(terms))
    for t in seen:
        if t not in _HYP:
            raise AssertionError(f"no hypothesis for summand {t!r}")
    binders = " ".join(f"({_HYP[t]})" for t in seen)
    names = ", ".join(_HYP[t].split(" :")[0] for t in seen)
    lst = "[" + ", ".join(f'"{t}"' for t in terms) + "]"
    head = f"example {binders} :\n" if binders else "example :\n"
    simp = f"  simp [{names}]\n" if names else ""
    return (head
            + f"    ¬ problem_spec_renderSum {lst}\n"
            f"      (implementation_renderSum {lst}) := by\n"
            f"  unfold problem_spec_renderSum implementation_renderSum "
            f"renderSum signParts\n"
            + simp
            + "  decide\n")


# =========================== POSITIVE CONTROLS ===============================
# Structurally-different but CORRECT impls that MUST verify (else
# SPEC-TOO-STRONG). Each reproves `correct_renderSum` with its statement
# byte-identical; only the tactic body changes. Both shapes were chosen to stay
# close to the frozen proof (no new induction, no helper lemma, no new
# declaration of any kind) so the case stays cheap to verify.

# (1) Result assembly by pattern match instead of headD/tail projection.
_POS_MATCH_TAIL = '''  match l with
  | [] => return ""
  | s :: rest =>
    if s = "+" then
      return String.intercalate " " rest
    else
      return s ++ String.intercalate " " rest'''
_POS_MATCH_PROOF = '''  simp only [Id.run]
  rw [key]
  cases h : signParts terms with
  | nil => rfl
  | cons s rest =>
    by_cases hs : s = "+" <;> simp [hs, Id.run, bind, pure]'''

# (2) Per-summand decision with the two arms swapped under a negated test.
_POS_FLIP_BRANCH = '''    if t.startsWith "-" = false then
      l := l ++ ["+", t]
    else
      l := l ++ ["-", t.drop 1]'''
_POS_FLIP_HELPER_STMT = '''    (Id.run (forIn terms init (fun t r =>
        if t.startsWith "-" = false then
          (pure (ForInStep.yield (r ++ ["+", t])) : Id _)
        else
          pure (ForInStep.yield (r ++ ["-", t.drop 1])))))'''
_POS_FLIP_HELPER_BODY = ('''      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq,
                 Bool.false_eq_true, Bool.true_eq_false]''')
_POS_FLIP_KEY = '''  have key : (forIn terms ([] : List String) (fun t r =>
      if t.startsWith "-" = false then do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["+", t]))
      else do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["-", t.drop 1]))) : Id (List String))
      = signParts terms := loop_helper_renderSum terms []'''


# =============================== ADMISSIBILITY ===============================
# The obligation binds every `terms : List String` with no precondition
# hypothesis, so both boundary shapes must be in domain and reach a normal
# return. We establish them explicitly INSIDE the proof region (as `have`s over
# the frozen spec predicate, discharged and then discarded), and then close the
# same obligation by the frozen route. If a boundary shape could not be
# discharged for a legitimate input, the obligation would be unsatisfiable
# there => PRECOND-TOO-STRONG / vacuous domain.
_ADMISS_PROOF = '''  intro terms
  -- admissibility: the boundary shapes the obligation must admit — the empty
  -- summand list, and a single summand of either sign — are in domain and reach
  -- a normal return, so the quantified obligation is not vacuous there.
  have h_empty : problem_spec_renderSum []
      (implementation_renderSum []) := by
    unfold problem_spec_renderSum implementation_renderSum renderSum signParts
    rfl
  have h_one : ∀ t : String, problem_spec_renderSum [t]
      (implementation_renderSum [t]) := by
    intro t
    unfold problem_spec_renderSum implementation_renderSum renderSum signParts
    by_cases ht : t.startsWith "-" = true <;> simp [ht, Id.run, bind, pure]
  -- admissibility at the concrete multi-summand shape the F2P exercises: the
  -- obligation is SATISFIABLE at that exact input, discharged by evaluation
  -- (each summand's leading-minus test split explicitly, since that predicate is
  -- the one term this carrier will not reduce on its own).
  have h_f2p : problem_spec_renderSum ["-B", "-A*B", "A"]
      (implementation_renderSum ["-B", "-A*B", "A"]) := by
    unfold problem_spec_renderSum implementation_renderSum renderSum signParts
    by_cases h1 : ("-B").startsWith "-" = true <;>
      by_cases h2 : ("-A*B").startsWith "-" = true <;>
        by_cases h3 : ("A").startsWith "-" = true <;>
          simp [h1, h2, h3, Id.run, bind, pure]
  clear h_empty h_one h_f2p
  unfold problem_spec_renderSum implementation_renderSum renderSum'''


SPEC_TESTS = [
    # ----------------------------- soundness ------------------------------
    {
        "id": "pos-match-assembly",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_TAIL, _POS_MATCH_TAIL),
                        _PROOF_TAIL, _POS_MATCH_PROOF),
        "rationale": "Correct impl, different shape: the assembled working list is "
                     "consumed by a pattern match on its head/rest instead of the "
                     "`headD`/`tail` projections, and the first-connective elision "
                     "becomes a branch returning either the joined remainder or the "
                     "kept connective glued to it. Same function of `terms`; the "
                     "obligation `correct_renderSum` is reproven with a byte-identical "
                     "statement by case-splitting `signParts terms` where the frozen "
                     "proof closed by `rfl`. No new declaration, no helper lemma. MUST "
                     "verify; if not => SPEC-TOO-STRONG (the postcondition would be "
                     "pinning the projection syntax rather than the rendered result).",
    },
    {
        "id": "pos-flipped-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_swap(_swap(
            _BASE, _IMPL_BRANCH, _POS_FLIP_BRANCH),
            _HELPER_STMT, _POS_FLIP_HELPER_STMT),
            _HELPER_BODY, _POS_FLIP_HELPER_BODY),
            _PROOF_KEY, _POS_FLIP_KEY),
        "rationale": "Correct impl, different shape: the per-summand decision tests the "
                     "leading-minus predicate NEGATED and swaps the two arms, so the "
                     "addition arm is taken first. Observationally identical; the "
                     "obligation is reproven by the same accumulator induction with the "
                     "branch orientation carried through. MUST verify — a spec that "
                     "rejected this would be pinning which arm of the decision comes "
                     "first, not the joining behaviour => SPEC-TOO-STRONG.",
    },
    # --------------------------- admissibility ----------------------------
    {
        "id": "admiss-boundary-shapes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_INTRO, _ADMISS_PROOF),
        "rationale": "The obligation quantifies over every summand list with NO "
                     "precondition hypothesis, so every shape must be admitted. Inside "
                     "the proof region we discharge the postcondition explicitly at the "
                     "two boundary shapes — the empty list, and a single summand of "
                     "EITHER sign (both arms of the leading-minus decision) — then close "
                     "the same obligation by the frozen route. These are exactly the "
                     "shapes where the joining loop runs zero or one time, i.e. where an "
                     "over-strong domain restriction would bite. All discharge; if not "
                     "=> the spec is unsatisfiable on a legitimate input.",
    },
    # ------------------- (b) connective choice (reject) -------------------
    {
        "id": "weak-plus-join",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BRANCH, '''    l := l ++ ["+", t]'''),
        "witness": _witness(["-B", "-A*B", "A"]),
        "refinement": "This is the pre-patch behaviour: every summand is joined with an "
                      "addition connective and kept verbatim, so a summand already "
                      "carrying a leading minus is displayed as the ADDITION of a negated "
                      "quantity. On the F2P-shaped input `[\"-B\", \"-A*B\", \"A\"]` the "
                      "required output is `-B - A*B + A` but this yields "
                      "`-B + -A*B + A`. That is precisely the rendering the issue reports "
                      "as wrong, so the faithful real patch is the unpatched code and "
                      "test_MatrixSymbol_printing / test_MatrixElement_printing do NOT "
                      "resolve.",
        "rationale": "Attacks clause (b), connective choice, and (c) body normalisation "
                      "at once — it is the whole decision removed. Partial-domain: "
                      "correct exactly on inputs where NO summand carries a leading "
                      "minus, wrong on every sign-bearing input the F2P exercises. "
                      "Refuted by `result = renderSum terms`, whose `signParts` emits "
                      "`[\"-\", t.drop 1]` for a leading-minus summand. Witness probes a "
                      "three-summand input with the leading-minus summands in first and "
                      "middle position; if it verified, the spec would not see the "
                      "reported bug at all => SPEC-TOO-WEAK.",
    },
    # ------------------- (c) body normalisation (reject) -------------------
    {
        "id": "weak-minus-not-stripped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_SUB_ARM, '      l := l ++ ["-", t]'),
        "witness": _witness(["A", "-B"]),
        "refinement": "Chooses the subtraction connective correctly but does NOT remove "
                      "the leading minus from the summand's body, so the sign is "
                      "duplicated: on `[\"A\", \"-B\"]` the required output is `A - B` but "
                      "this yields `A - -B`. A patch that emitted the subtraction "
                      "connective while leaving the term text untouched would render a "
                      "double sign and FAIL test_MatrixSymbol_printing, which asserts the "
                      "exact string.",
        "rationale": "Attacks clause (c) ALONE, in isolation from (b): a NEAR-MISS of "
                      "weak-plus-join that agrees with gold on the connective and on "
                      "every minus-free input, diverging only in the body of a "
                      "leading-minus summand. Given its own witness at a distinct, "
                      "minimal two-summand input (positive first, negative second) rather "
                      "than sharing weak-plus-join's, since it fails for a different "
                      "reason on a smaller sub-domain. Refuted by `signParts`'s "
                      "`t.drop 1`.",
    },
    # ------------- (d) first-connective elision + spacing (reject) --------
    {
        "id": "weak-no-first-elision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_ELIDE, ""),
        "witness": _witness(["A"]),
        "refinement": "Never elides the very first connective, so a sum whose first "
                      "summand is positive acquires a spurious leading addition sign: on "
                      "the single-summand input `[\"A\"]` the required output is `A` but "
                      "this yields `+A`. Every asserted string in "
                      "test_MatrixSymbol_printing / test_MatrixElement_printing begins "
                      "with the first summand's own text, so a patch omitting the elision "
                      "does NOT resolve.",
        "rationale": "Attacks clause (d), the elision half. Partial-domain: correct on no "
                      "input at all whose first summand is positive; the complement of "
                      "weak-elide-any-first-sign below. Witness probes the SINGLE-POSITIVE "
                      "boundary shape — the smallest input that exposes the elision, and "
                      "an input point no other witness uses — so the manifest "
                      "demonstrates the spec's dependence on the first summand's sign "
                      "independently of list length.",
    },
    {
        "id": "weak-elide-any-first-sign",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_ELIDE, '  let firstSign := ""\n'),
        "witness": _witness(["-B"]),
        "refinement": "Elides the first connective UNCONDITIONALLY, so a sum whose first "
                      "summand is negative silently loses its leading minus and changes "
                      "sign: on the single-summand input `[\"-B\"]` the required output is "
                      "`-B` but this yields `B`. The F2P assertions include outputs that "
                      "begin with a negative summand, so a patch that blanked the first "
                      "connective regardless of which one it is does NOT resolve.",
        "rationale": "Attacks clause (d) from the opposite direction to "
                      "weak-no-first-elision, and is the sharper of the two: it agrees "
                      "with gold on EVERY input whose first summand is positive, so it is "
                      "refutable only at a negative-leading input. Witness probes the "
                      "SINGLE-NEGATIVE boundary shape — the input point that "
                      "discriminates it and that no other witness in this battery uses. "
                      "Refuted by `renderSum`'s conditional elision, which keeps a "
                      "subtraction connective and glues it to the first body.",
    },
    {
        "id": "weak-no-space-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_JOIN,
                        '  return firstSign ++ String.intercalate "" rest'),
        "witness": _witness(["B", "-A*B"]),
        "refinement": "Joins the connectives and bodies with no separator, so the "
                      "connectives run into the surrounding text: on `[\"B\", \"-A*B\"]` "
                      "the required output is `B - A*B` but this yields `B-A*B`. The F2P "
                      "tests compare against exact strings with single spaces around "
                      "every connective, so a patch that dropped the separator does NOT "
                      "resolve.",
        "rationale": "Attacks clause (d), the spacing half, with the connective CHOICE "
                      "and the body normalisation both left correct — so it isolates the "
                      "one commitment the other rivals leave untested. Refuted by "
                      "`renderSum`'s `String.intercalate \" \"`. Witness probes a "
                      "two-summand input with the signs in the opposite arrangement to "
                      "weak-minus-not-stripped's (`B` positive first, `-A*B` negative "
                      "second, both literals distinct from that case's), so the two "
                      "near-adjacent cases do not collapse onto one probed point.",
    },
    {
        "id": "weak-empty-head-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_HEAD,
                        '  let firstSign := l.headD "-"\n  let rest := l.tail'),
        "witness": _witness([]),
        "refinement": "Changes the fallback used when there is no connective to read at "
                      "all — i.e. when the summand list is EMPTY. On every non-empty "
                      "input the working list starts with a real connective, so the "
                      "fallback is never consulted and this agrees with the required "
                      "behaviour exactly; on the empty list the required output is the "
                      "empty string but this yields `-`, a bare sign with nothing to "
                      "sign. A patch that picked the wrong fallback would emit that "
                      "stray character for an empty additive expression.",
        "rationale": "Attacks the ONE input point the other six rivals cannot reach: the "
                      "empty summand list. Every other reject case in this battery is "
                      "refuted at a non-empty input, and each of them is observationally "
                      "IDENTICAL to the frozen spec at `[]` (checked by evaluation: all "
                      "six agree with gold there), so before this case the manifest "
                      "demonstrated nothing about the spec's commitment at the empty "
                      "list. This rival is the exact complement — correct on every "
                      "non-empty input, wrong only at `[]` — which makes it the sharpest "
                      "possible probe of that binder point. Its witness needs NO "
                      "conditioning hypothesis, because nothing branches on the "
                      "leading-minus predicate when there is no summand to test, so it "
                      "is also the battery's only unconditioned refutation.",
    },
    # ----------------------- (a) order (reject) ---------------------------
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_FOR, "  for t in terms.reverse do"),
        "witness": _witness(["A", "B"]),
        "refinement": "Traverses the summands back to front, so the displayed sum lists "
                      "them in reverse input order: on `[\"A\", \"B\"]` the required "
                      "output is `A + B` but this yields `B + A`. The F2P assertions are "
                      "exact strings in the argument order sympy hands over, so a patch "
                      "that reversed the traversal does NOT resolve.",
        "rationale": "Attacks clause (a), order — the only clause the sign-handling "
                      "rivals leave entirely alone, and the one an author focused on the "
                      "reported symptom would forget to defend. Witness probes an input "
                      "of two DISTINCT POSITIVE summands, where order is the sole "
                      "observable difference: this is the only witness in the battery "
                      "that holds the leading-minus predicate false on every summand, so "
                      "it varies that binder in the direction the other five do not.",
    },
]


# ============================== PORT NOTES ====================================
#
# Nagini cases dropped, with the demonstrated reason for each:
#
#  * frame-sum-write / frame-sum-space-write / frame-product-write — the whole
#    frame-mutation class. Nagini's inputs carry Acc(list_pred(xs), 1/2), so a
#    write to an input is rejected for insufficient permission. This carrier has
#    no permission system at all: the input is an immutable `List String` value,
#    `l := ...` rebinds a local, and there is no expressible edit that "writes to
#    the input". The distinction is collapsed by the carrier, not by the port.
#
#  * weak-space-as-str-discipline / weak-space-text-negativity — both attack
#    `render_sum_space`, the PRETTY site, whose decision keys on a STRUCTURAL
#    negativity fact carried alongside the rendered text as a separate input
#    (`negs`). This bundle models one routine, the text-keyed one, whose only
#    input is the summand list (mapping.md: one Lean model covers the str and
#    latex sites, which are byte-identical in algorithm). With no `negs` binder in
#    the frozen signature there is no term for either rival to perturb — and the
#    signature is spec, so a case could not add one without changing the spec.
#
#  * weak-product-drop-neg / weak-product-always-neg — both attack
#    `render_product`, a SECOND modeled function (the multiplicative join, with
#    its own `neg` flag). meta.json's modeled_functions lists exactly one entry
#    for this bundle; the product routine is not in this bundle's defended
#    surface, so there is nothing here for these rivals to be rivals of.
#
#  * weak-sum-plusjoin -> ported as `weak-plus-join`; weak-sum-head-strip ->
#    ported as `weak-elide-any-first-sign` (same attack: the first summand's sign
#    dropped unconditionally). pos-sum-reshape / pos-product-reshape ->
#    `pos-match-assembly` and `pos-flipped-branch`. admiss-sum-readable ->
#    `admiss-boundary-shapes`, which additionally discharges the obligation at the
#    concrete F2P-shaped input.
#
# Divergence lane: the frozen solution sets no `loom.semantics.termination`
# option, and its impl is a total `def` over a bounded `for`. A diverging rival
# has to be written `partial def`, and a `partial def` on this carrier is opaque —
# `unfold` and `simp only` both refuse it ("failed to unfold
# `implementation_renderSum`"), so the obligation cannot be closed AND no witness
# can refute it: a witness conditioned on the opaque term (`hv : impl ["A"] =
# "ZZZ"`) elaborates against the frozen solution too, i.e. it is vacuous rather
# than discriminating. So the class is a KNOWN HOLE on this carrier, not a
# shippable reject case: the rival is rejected, but for opacity rather than for
# the spec, and nothing attributable can be built.
#
# G-AX is the axiom lane's job and this gate ignores it; meta.json records
# axioms == [] and opaque_callees == [] for this bundle anyway.
AXIOM_TESTS = []  # type: list

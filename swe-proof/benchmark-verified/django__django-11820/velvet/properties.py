"""properties.py — G-PBT (spec-lane) falsification battery for
django__django-11820, PORTED from the nagini bundle's design doc to the velvet
(Lean 4 + Velvet) carrier. NOT a Velvet module: a record of adversarial,
instance-specific cases. The runner writes each `module` to a temp file,
verifies it, and checks markers.same_spec against the frozen Solution.lean.
Every case edits ONLY text inside the `-- impl-start` / `-- impl-end` region
(and, for the reshapes that need it, the `prove_correct` tactic body — both of
which the consumer spec view elides), so the frozen spec (the `ensures`, the
pure model, the `prove_correct checkOrderingRef` obligation with a byte-
identical statement) is provably untouched and `markers.same_spec` holds by
construction.

DEFENDED SURFACE (from Solution.lean + mapping.md + instance.json):
  method checkOrderingRef
      (lookup : Model → Part → Option Field) (aliasField : Model → Field)
      (hasTransform : Field → Part → Bool) (cls0 : Model) (parts : List Part)
      return (out : Bool)
    ensures out = orderingRefInvalid lookup aliasField hasTransform cls0 parts

There is ONE contracted method and ONE load-bearing `ensures` clause. It pins
the result to `orderingRefInvalid …`, a total, fully-unfolded DEEP model (the
`axioms` region is empty — no opaque answer key) of the left-to-right walk over
the chain of parts of one dotted reference. The walk folds `stepWalk` from a
seed rooted at `cls0` and returns whether the reference ends up flagged. It
composes three independently-attackable sub-behaviors of `stepWalk`:
  * the ALIAS part resolves against the current model's identity field
    (`aliasField m`) directly — NOT through the plain field resolver `lookup`
    (which would fail to resolve it); attacked by R1;
  * after a SUCCESSFUL NON-relation resolution the chain steps off the model
    graph (`cur := none`), so a following part has no model to resolve against
    and the reference is flagged — NOT left at the current model, which would
    let a following part spuriously resolve; attacked by R2;
  * an UNRESOLVED part is flagged UNLESS it is a registered transform of the
    last resolved field (`flagOnUnresolved` consults `hasTransform`) — the
    escape hatch is NOT dropped; attacked by R3.

The FIVE input binders are all free and the post-image must hold for EVERY
value of each:
  * `lookup      : Model → Part → Option Field`  — the plain field resolver;
  * `aliasField  : Model → Field`                — the model's identity field;
  * `hasTransform: Field → Part → Bool`          — the registered-transform test;
  * `cls0        : Model`                          — the seed model;
  * `parts       : List Part`                      — the chain of parts.

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling's
    mandatory frame-mutation rival writes back into a read-only `path` input
    carrying only a fractional heap permission (`Acc(list_pred(path),1/2)`) and
    is rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: every binder is an immutable value/function, this method
    declares no `mut` binder over its inputs, there is no heap and no aliasing.
    There is no read-only input to overwrite and no permission system to trip,
    so the class is vacuous. No substitute is fabricated (per the porting map,
    this class is legitimately dropped rather than replaced).
  * DIVERGENCE / NON-TERMINATION — a KNOWN SPEC HOLE that survives `total`, and
    a lane that is UNSHIPPABLE here for a mechanical reason, not a vacuous one.
    CORRECTED BY THE AUDIT: this bundle is `set_option
    loom.semantics.termination "total"`, NOT "partial" — the earlier text here
    asserted "partial" and every conclusion it drew from that was wrong. Under
    `total` the disposition has to be re-derived, and it was, with real builds:
      (a) A rival whose loop carries NO `decreasing` clause IS rejected —
          `error: Decreasing annotations are required in total correctness
          semantics` (exit 1). But that error is raised at the `method`
          declaration, which is OUTSIDE the region the witness file strips, so
          it fires in the RIVAL-side witness build too: measured exit 1 on the
          rival side, which is the half that must SUCCEED. The gate would record
          `witness-unproven` (inconclusive) and the whole battery would go
          MALFORMED-TESTS. A `witness_reference` cannot rescue it either — that
          substitutes the GOLD side, while the un-elaborable term is on the
          rival side. So this rival is not shippable regardless of its merit.
      (b) `total` DOES close the class, and an earlier revision of this bullet
          claimed the opposite: that the `decreasing` annotation is accepted
          without being PROVEN to decrease, so a rival could supply a bogus
          measure and be admitted. That is RETRACTED, at the shape the earlier
          revision itself named. A loop whose body never changes its measure
          variable (`let mut q : Nat := 1; while q > 0 / invariant 0 ≤ q /
          done_with q = 0 / decreasing q do q := q`), spliced at the impl anchor
          with each proof reduced to a bare `loom_solve`, is REJECTED: exit 1,
          `unsolved goals`, `case «decreasing_1: q»`, residual `⊢ q < q`. The
          refusal lands on the MEASURE's own descent goal, so it is not the
          annotation linter of (a) and cannot be laundered by writing an
          annotation. The mechanism is in Loom, not in a tactic:
          `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop`
          (`Loom/MonadAlgebras/NonDetT/Basic.lean:544`) takes `measure : β -> Nat`
          and emits `measure b' < measure b`; only the `PartialCorrectness` twin
          (:211) takes an `Option ℕ` and DISCARDS it. So no rival hangs on the
          F2P-shaped input and still satisfies this spec.
    Disposition: CLOSED BY THE SEMANTICS, not a hole and not a vacuous class.
    Nothing is escalated. Nothing is shippable in this lane either, by (a): the
    rejection fires at the `method` declaration, which the witness file retains,
    so no witness can elaborate against the rival and the gate would record
    `witness-unproven`. That is a witness-contract limit, not a spec weakness, so
    the nagini `diverge-nonempty-path` case stays omitted (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to
    `orderingRefInvalid …`, computed entirely from the method's own arguments by
    a concrete `def` in the `pure` region; the `axioms` region is empty. An impl
    that "echoes the oracle" IS the correct impl; the honest controls are the
    structurally-different reshapes (V1/V2).
  * PARTIAL-DOMAIN / VALUE — heavily exercised. Each reject rival is correct on
    a sub-domain but diverges once its target sub-behavior is exercised: the pk-
    alias branch (R1), the non-relation descent-termination (R2), and the
    transform escape hatch (R3).

WITNESS MECHANICS ON THIS BUNDLE — and the SUBJECT each witness is refuted
against, which is the whole substance of the attestation here.

The spec is a `method` CONTRACT, not a bare predicate, so each witness reaches
it through Velvet's own tester machinery: `checkOrderingRefTester … = false`
says the extracted program's result violates the postcondition at that concrete
input, checked in a file whose `prove_correct` block has been stripped (no
tactic script can mask the verdict). Each reject rival is a LOOP-FREE closed
form (a `List.foldl` of an inline step), so ITS tester kernel-reduces under
`decide`. The three FREE FUNCTION binders (`lookup`, `aliasField`,
`hasTransform`) are instantiated at concrete decidable lambdas, so the tester
reduces fully. No witness binds a hypothesis (all inputs are concrete
literals), so there is no consistency obligation. No `sorry`/`admit`/
`native_decide` is used.

THE FROZEN SOLUTION CANNOT SERVE AS THE SECOND SUBJECT, and it is important not
to mistake its exit code for evidence. Its impl carries a `while` loop, which
under `loom.semantics.choice "demonic"` elaborates through `Classical.choice`;
the kernel cannot unfold that, so `decide` on the frozen tester is STUCK rather
than deciding. Measured, for every witness below: gold exits 1 with

    Tactic `decide` failed for proposition … checkOrderingRefTester … = false
    … did not reduce to `isTrue` or `isFalse`.

and the FORGERY that flips the claim to `… = true` — i.e. asserting gold is
CORRECT at that point, the opposite of a refutation — fails against gold with
the byte-identical error modulo the flipped literal. Re-measured by the audit on
all five reject cases: gold exit 1 and forgery-on-gold exit 1, and `diff` of the
two logs shows the ONLY differences are the `false`/`true` literal itself (three
occurrences: the proposition, the instance, and the `with` line). So gold's exit
code carries NO information about the claim, and a witness scored against gold
alone would be hollow.

What makes each rejection real is the second subject the gate actually uses: an
expect="verify" positive from this battery (`pos-closed-form`), which shares the
frozen spec, VERIFIES, and DOES reduce. Against it every witness below fails
with a plain evaluation —

    Tactic `decide` proved that the proposition … = false is false

— while the flipped-claim forgery ELABORATES (exit 0). That pair is the
refutation: the exit code tracks the claim, so it attests to the spec and not to
a tactic mismatch. Recorded per case under `witness_subject` in meta.json.

Each rival module (with the frozen proof) was also confirmed NOT to verify, and
each rival's DEFECT was confirmed OBSERVABLE — the pure model `orderingRefInvalid`
and the rival's own fold were evaluated at the witness input and disagree, so no
rival is a mere reshape.

AXIOM lane: EMPTY by design. The `axioms` region declares no `axiom`; the three
schema accessors are FREE INPUTS (`lookup`/`aliasField`/`hasTransform`), an
A-reference the R/I legs differential-test (G-CONF's job), NOT a consumed
contract. The gate ignores `AXIOM_TESTS` regardless. `AXIOM_TESTS = []`.
"""
from pathlib import Path

INSTANCE = "django__django-11820"
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

# The WHOLE executable body of the method: the forward-fold accumulating loop
# over the parts. Reject rivals replace this with a loop-free closed form (so
# their tester reduces under `decide`); the closed-form positive control does
# too.
_IMPL_BODY = """    let mut st : WalkState := initState cls0
    let mut i := 0
    while i < parts.length
      invariant i ≤ parts.length
      invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform) (initState cls0)
      done_with i = parts.length
      decreasing parts.length - i
    do
      let p := parts[i]!
      st := stepWalk lookup aliasField hasTransform st p
      i := i + 1
    return st.2.2
"""

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    -- impl-start\n    let mut st : WalkState := initState cls0"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). Some positive controls retune it; the tactic body is elided from the
# spec view, so this is a proof reshape, not a spec change.
_PROOF = """prove_correct checkOrderingRef by
  loom_solve
  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform) (initState cls0)» =>
    have hi : i < parts.length := by omega
    rw [invariant_2, walk_take_step lookup aliasField hasTransform cls0 parts i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  all_goals simp_all [orderingRefInvalid]"""


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `checkOrderingRefTester … = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
def _tester(body):
    return ("extract_program_for checkOrderingRef\n"
            "prove_precondition_decidable_for checkOrderingRef\n"
            "prove_postcondition_decidable_for checkOrderingRef\n"
            "derive_tester_for checkOrderingRef\n\n" + body)


# A loop-free closed form of the walk with ONE inline step-defect injected.
# `{step}` is the body of the fold's step function (the `match cur with …`),
# swapped in per rival. Because it is a plain `List.foldl` over a literal list,
# its tester kernel-reduces under `decide`.
def _closed(step):
    return ("    return (parts.foldl (fun st p =>\n"
            "      let cur := st.1\n"
            "      let last := st.2.1\n"
            "      let flag := st.2.2\n"
            f"{step}"
            "      ) (initState cls0)).2.2\n")


SPEC_TESTS = []

# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl of the modeled behavior cannot verify,
# the spec is SPEC-TOO-STRONG. Each keeps the `ensures` obligation and only
# reshapes the executable surface (and, where needed, retunes the tactic body).
# ===========================================================================

# ---------------------------------------------------------------------------
# V1. POSITIVE CONTROL — closed form. Collapse the accumulating loop into the
#     value the post-image names directly (`orderingRefInvalid …`). A maximally
#     different control-flow shape (no loop, no accumulator) computing the same
#     decision; the loop-specific proof is dropped since the impl now matches
#     the post-image syntactically and `loom_solve` closes it alone.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "pos-closed-form",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap2(
        _IMPL_BODY,
        "    return orderingRefInvalid lookup aliasField hasTransform cls0 parts\n",
        _PROOF,
        "prove_correct checkOrderingRef by\n  loom_solve"),
    "rationale": "A loop-free impl that returns the walk's verdict directly must "
                 "satisfy `out = orderingRefInvalid …`; a correct reshape of the "
                 "modeled behaviour verifying is exactly what SPEC-TOO-STRONG "
                 "would deny. Exercises the sole `ensures` clause from a "
                 "maximally different (loop-free) control-flow shape. "
                 "(soundness — sibling of pos-cheapest-return-oracle.)",
})

# ---------------------------------------------------------------------------
# V2. POSITIVE CONTROL — inline + reorder. Inline `stepWalk` into the loop body
#     and reorder the branch dispatch (alias-part test lifted above the plain
#     resolution), keeping the loop, invariant and forward-fold structure so the
#     frozen proof still discharges after one defeq `rfl` on the inlined step.
#     Behaviour-identical, so it must verify (else SPEC-TOO-STRONG on the impl
#     shape). Sibling of nagini pos-reorder-branches.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "pos-inline-reorder-step",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap2(
        _IMPL_BODY,
        "    let mut st : WalkState := initState cls0\n"
        "    let mut i := 0\n"
        "    while i < parts.length\n"
        "      invariant i ≤ parts.length\n"
        "      invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform) (initState cls0)\n"
        "      done_with i = parts.length\n"
        "      decreasing parts.length - i\n"
        "    do\n"
        "      let p := parts[i]!\n"
        "      let cur := st.1\n"
        "      let last := st.2.1\n"
        "      let flag := st.2.2\n"
        "      let newSt : WalkState :=\n"
        "        match cur with\n"
        "        | none   => (none, last, flag || flagOnUnresolved hasTransform last p)\n"
        "        | some m =>\n"
        "            if p.isAlias then\n"
        "              let f := aliasField m\n"
        "              (if f.isRel then some f.relModel else none, some f, flag)\n"
        "            else\n"
        "              match lookup m p with\n"
        "              | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
        "              | none   => (some m, last, flag || flagOnUnresolved hasTransform last p)\n"
        "      st := newSt\n"
        "      i := i + 1\n"
        "    return st.2.2\n",
        "        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]\n"
        "  all_goals simp_all [orderingRefInvalid]",
        "        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]\n"
        "    rfl\n"
        "  all_goals simp_all [orderingRefInvalid]"),
    "rationale": "Inlining `stepWalk` and lifting the alias-part test above the "
                 "plain resolution computes the same accumulator state-for-state "
                 "with the loop and forward-fold invariant unchanged, so "
                 "`out = orderingRefInvalid …` still holds and the frozen proof "
                 "closes after one defeq `rfl`. A correct reshape must verify "
                 "(else SPEC-TOO-STRONG on the impl shape). (soundness)",
})

# ===========================================================================
# ADMISSIBILITY — the method carries no `require` clause, so the "a normal input
# satisfies the precondition" probe is not where the risk sits. The residual
# risk is that the post-image is DEGENERATE / UNSATISFIABLE at the interesting
# point — that it does not actually demand a NOT-flagged verdict for a validly
# resolving reference while demanding a FLAGGED verdict for one that steps off
# the graph. This case discharges an in-region assert pinning both at concrete
# inputs; the impl is kept verbatim so the method's own obligation still
# discharges, and the proof's alternation gains one `decide` arm.
# ===========================================================================
SPEC_TESTS.append({
    "id": "admiss-grounded",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap2(
        _IMPL_TOP,
        "    -- impl-start\n"
        "    assert (with_name_prefix `admiss\n"
        "      (orderingRefInvalid\n"
        "          (fun _ p => if p.name = 1 then some { isRel := true, relModel := 1 } else none)\n"
        "          (fun _ => { isRel := false, relModel := 0 }) (fun _ _ => false) 0\n"
        "          [{ name := 1, isAlias := false }, { name := 0, isAlias := true }] = false ∧\n"
        "       orderingRefInvalid\n"
        "          (fun _ p => if p.name = 1 then some { isRel := true, relModel := 1 }\n"
        "                      else if p.name = 2 then some { isRel := false, relModel := 0 } else none)\n"
        "          (fun _ => { isRel := false, relModel := 0 }) (fun _ _ => false) 0\n"
        "          [{ name := 1, isAlias := false }, { name := 2, isAlias := false },\n"
        "           { name := 3, isAlias := false }] = true))\n"
        "    let mut st : WalkState := initState cls0",
        "  all_goals simp_all [orderingRefInvalid]",
        "  all_goals first | decide | simp_all [orderingRefInvalid]"),
    "rationale": "The post-image is satisfiable AND non-degenerate at the two "
                 "F2P-SHAPED points, which is what makes this the admissibility "
                 "analogue on a total carrier: the obligation must not be "
                 "unsatisfiable at exactly the inputs the failing tests describe. "
                 "Point 1 is a RELATION part followed by the identity ALIAS part "
                 "(the shape whose verdict must be NOT-flagged — the reference is "
                 "legitimate). Point 2 is a RELATION part, then a NON-RELATION "
                 "part, then a further part (the shape whose verdict must be "
                 "FLAGGED — the descent ended, so the trailing part cannot "
                 "resolve). Both are discharged BY EVALUATION as an in-region "
                 "assert before the frozen obligation closes verbatim, so it is "
                 "the concrete verdicts that are pinned, not a restatement. Both "
                 "are genuinely non-trivial: flipping either conjunct's expected "
                 "value leaves `unsolved goals` (measured), so the assert is "
                 "load-bearing. The two earlier points this case carried (a single "
                 "ordinary part, resolving and not) were NOT F2P-shaped — no "
                 "relation, no alias, no descent — and pinned only the one-step "
                 "fold. The impl is kept verbatim so `out = orderingRefInvalid …` "
                 "still verifies. (admissibility — re-aimed from nagini "
                 "admiss-normal-related-path.)",
})

# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected, each a loop-free closed form (so its tester kernel-reduces)
# with a machine-checked refutation witness at a concrete input, and the
# refinement argument that its faithful real counterpart would NOT resolve the
# failing test.
# ===========================================================================

# ---------------------------------------------------------------------------
# R1. UNIQUENESS — the pk-alias fix reverted (nagini pk-alias-reverted). Route
#     the alias part through the plain resolver `lookup` with NO special case,
#     so an alias part that `lookup` cannot resolve is wrongly flagged. Correct
#     on every reference containing no alias part; diverges the moment an alias
#     part appears. Attacks the alias sub-behavior of the sole ensures clause.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "weak-alias-via-lookup",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _IMPL_BODY,
        _closed(
            "      match cur with\n"
            "      | none   => (none, last, flag || flagOnUnresolved hasTransform last p)\n"
            "      | some m =>\n"
            "          match lookup m p with\n"
            "          | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
            "          | none   => (some m, last, flag || flagOnUnresolved hasTransform last p)\n")),
    "refinement": "This is the literal pre-image behaviour: the identity-alias "
                  "part is resolved through the plain field resolver instead of "
                  "the model's identity field. The plain resolver has no entry "
                  "for the alias, so the reference is wrongly flagged; the "
                  "failing test asserts that a related reference whose trailing "
                  "part is the identity alias raises NO report, so this rival "
                  "reports one and would NOT resolve — it is exactly the change "
                  "the spec senses.",
    "rationale": "REJECT from `out = orderingRefInvalid …` at the alias sub-"
                 "behavior: the frozen `stepWalk` resolves an alias part via "
                 "`aliasField m` (which succeeds), but the rival routes it "
                 "through `lookup m p`, which returns `none`, so the reference "
                 "is flagged where gold leaves it valid. Refuted at a single "
                 "alias part whose `lookup` yields `none`. NOTE: this witness "
                 "does NOT exercise the alias-descent path — with one part and "
                 "nothing following it, `aliasField`'s `isRel` is unobservable "
                 "(gold's verdict is `false` for BOTH isRel values at this "
                 "input, measured by evaluation). The descent branch is "
                 "attacked separately by weak-alias-no-descent.",
    "witness": _tester(
        "example :\n"
        "    checkOrderingRefTester\n"
        "      (fun _ _ => none)\n"
        "      (fun _ => { isRel := true, relModel := 2 })\n"
        "      (fun _ _ => false)\n"
        "      1\n"
        "      [{ name := 0, isAlias := true }]\n"
        "      = false := by\n"
        "  decide\n"),
})

# ---------------------------------------------------------------------------
# R2. UNIQUENESS — the non-relation descent-termination reverted (nagini
#     non-relation-reset-reverted). After a SUCCESSFUL non-relation resolution
#     leave the current model in place (`some m`) instead of stepping off the
#     graph (`none`), so a following part spuriously resolves against the same
#     model. Correct on any reference of length <= 1 or one that never follows a
#     non-relation field with another part; diverges on the multi-hop-through-a-
#     non-relation-field sub-domain. Attacks the descent-termination sub-behavior.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "weak-nonrel-no-terminate",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _IMPL_BODY,
        _closed(
            "      match cur with\n"
            "      | none   => (none, last, flag || flagOnUnresolved hasTransform last p)\n"
            "      | some m =>\n"
            "          if p.isAlias then\n"
            "            let f := aliasField m\n"
            "            (if f.isRel then some f.relModel else none, some f, flag)\n"
            "          else\n"
            "            match lookup m p with\n"
            "            | some f => (if f.isRel then some f.relModel else some m, some f, flag)\n"
            "            | none   => (some m, last, flag || flagOnUnresolved hasTransform last p)\n")),
    "refinement": "This is the literal pre-image behaviour: after resolving a "
                  "non-relation field the walk does NOT step off the model graph, "
                  "so a following part is re-resolved against the same model and "
                  "spuriously succeeds. The failing test constructs a reference "
                  "that hops through a non-relation field into a further part and "
                  "asserts a report IS raised; this rival leaves it unflagged, so "
                  "it would NOT resolve.",
    "rationale": "REJECT from `out = orderingRefInvalid …` at the descent-"
                 "termination sub-behavior: the frozen `stepWalk` sets "
                 "`cur := none` after a non-relation field, so a following part "
                 "hits the `none` arm and is flagged; the rival leaves "
                 "`cur := some m`, so the following part resolves and the "
                 "reference stays valid. Refuted at two non-relation parts "
                 "(varies `parts` length and the lookup/descent binders).",
    "witness": _tester(
        "example :\n"
        "    checkOrderingRefTester\n"
        "      (fun _ _ => some { isRel := false, relModel := 0 })\n"
        "      (fun _ => { isRel := false, relModel := 0 })\n"
        "      (fun _ _ => false)\n"
        "      3\n"
        "      [{ name := 0, isAlias := false }, { name := 1, isAlias := false }]\n"
        "      = false := by\n"
        "  decide\n"),
})

# ---------------------------------------------------------------------------
# R3. UNIQUENESS — the transform escape hatch dropped (nagini
#     transform-rescue-dropped). In BOTH unresolved arms (cur = none and a
#     failing `lookup`) flag unconditionally, ignoring `hasTransform`. Correct on
#     any reference whose unresolved parts are never registered transforms;
#     diverges on a reference whose trailing part is a registered transform of
#     the last resolved field (legitimate, must NOT be flagged). Attacks the
#     transform sub-behavior and varies the hasTransform binder.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "weak-drop-transform-escape",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _IMPL_BODY,
        _closed(
            "      match cur with\n"
            "      | none   => (none, last, true)\n"
            "      | some m =>\n"
            "          if p.isAlias then\n"
            "            let f := aliasField m\n"
            "            (if f.isRel then some f.relModel else none, some f, flag)\n"
            "          else\n"
            "            match lookup m p with\n"
            "            | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
            "            | none   => (some m, last, true)\n")),
    "refinement": "The real-patch counterpart would report on any unresolved "
                  "part unconditionally, dropping the escape hatch that admits a "
                  "trailing part naming a registered transform of the last "
                  "resolved field. A legitimate reference ordering by such a "
                  "registered transform would then spuriously raise a report — a "
                  "regression on the transform-tail behaviour the validator "
                  "preserves — so it would NOT resolve.",
    "rationale": "REJECT from `out = orderingRefInvalid …` at the transform "
                 "sub-behavior: `flagOnUnresolved` flags an unresolved part only "
                 "when it is NOT a registered transform of the last field "
                 "(`!hasTransform f p`), but the rival flags unconditionally, so "
                 "it disagrees with gold whenever `hasTransform` holds of the "
                 "trailing part. Refuted at a non-relation field followed by a "
                 "part that fails to resolve but IS a registered transform "
                 "(`hasTransform` = true — the value R1/R2 hold at false).",
    "witness": _tester(
        "example :\n"
        "    checkOrderingRefTester\n"
        "      (fun _ p => if p.name = 0 then some { isRel := false, relModel := 0 } else none)\n"
        "      (fun _ => { isRel := false, relModel := 0 })\n"
        "      (fun _ _ => true)\n"
        "      5\n"
        "      [{ name := 0, isAlias := false }, { name := 1, isAlias := false }]\n"
        "      = false := by\n"
        "  decide\n"),
})


# ---------------------------------------------------------------------------
# R4. UNIQUENESS — the ALIAS DESCENT dropped (added by the adversarial audit; no
#     nagini sibling). R1 reverts WHICH accessor resolves the alias part, but its
#     single-part witness cannot see what the alias part does to `cur`
#     afterwards: with nothing following, `aliasField`'s `isRel` is unobservable.
#     This rival keeps the alias branch and the correct accessor but never
#     descends — `cur := none` regardless of `isRel` — so a part FOLLOWING an
#     alias that names a relation has no model to resolve against and is wrongly
#     flagged. Correct on every reference whose alias part is last (which is most
#     of them, and all of R1's domain); diverges the moment a part follows a
#     relation-valued alias. This is the clause the battery previously left
#     unattacked.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "weak-alias-no-descent",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _IMPL_BODY,
        _closed(
            "      match cur with\n"
            "      | none   => (none, last, flag || flagOnUnresolved hasTransform last p)\n"
            "      | some m =>\n"
            "          if p.isAlias then\n"
            "            let f := aliasField m\n"
            "            (none, some f, flag)\n"
            "          else\n"
            "            match lookup m p with\n"
            "            | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
            "            | none   => (some m, last, flag || flagOnUnresolved hasTransform last p)\n")),
    "refinement": "A counterpart that resolves the identity alias correctly but "
                  "then treats the resolved field as if it could never be a "
                  "relation, so the chain always stops there. A reference that "
                  "orders by a further part reached THROUGH an identity alias "
                  "that denotes a relation would then spuriously raise a report, "
                  "where the validator resolves it — so it would NOT resolve.",
    "rationale": "REJECT from `out = orderingRefInvalid …` at the ALIAS-DESCENT "
                 "clause: the frozen `stepWalk` continues into `f.relModel` when "
                 "the alias's field is a relation, but the rival hands back "
                 "`none`, so a following part hits the `none` arm and is flagged. "
                 "This is the sub-behaviour weak-alias-via-lookup cannot reach "
                 "(its chain is one part long, so the descent is unobservable). "
                 "Refuted at a RELATION-valued `aliasField` followed by a part "
                 "that resolves — the point where gold's verdict genuinely "
                 "depends on `aliasField.isRel` (measured: `false` for "
                 "isRel=true, `true` for isRel=false).",
    "witness": _tester(
        "example :\n"
        "    checkOrderingRefTester\n"
        "      (fun _ p => if p.name = 3 then some { isRel := false, relModel := 0 } else none)\n"
        "      (fun _ => { isRel := true, relModel := 6 })\n"
        "      (fun _ _ => false)\n"
        "      2\n"
        "      [{ name := 0, isAlias := true }, { name := 3, isAlias := false }]\n"
        "      = false := by\n"
        "  decide\n"),
})

# ---------------------------------------------------------------------------
# R5. UNIQUENESS — flag accumulation not MONOTONE (added by the adversarial
#     audit; no nagini sibling). Every existing rival attacks WHEN the flag is
#     raised; none attacks whether a flag once raised STAYS raised. This rival
#     drops the `flag ||` disjunction in both unresolved arms, so the verdict
#     reflects only the LAST part: an earlier part that legitimately flagged the
#     reference is silently forgiven by a later part that happens to be rescued
#     by the transform hatch. Correct on every reference with at most one
#     unresolved part; diverges once two unresolved parts disagree.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "weak-flag-not-monotone",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _IMPL_BODY,
        _closed(
            "      match cur with\n"
            "      | none   => (none, last, flagOnUnresolved hasTransform last p)\n"
            "      | some m =>\n"
            "          if p.isAlias then\n"
            "            let f := aliasField m\n"
            "            (if f.isRel then some f.relModel else none, some f, flag)\n"
            "          else\n"
            "            match lookup m p with\n"
            "            | some f => (if f.isRel then some f.relModel else none, some f, flag)\n"
            "            | none   => (some m, last, flagOnUnresolved hasTransform last p)\n")),
    "refinement": "A counterpart that recomputes the report decision per part "
                  "instead of accumulating it — the report for a reference is "
                  "kept only if its LAST part warrants one. A reference whose "
                  "earlier part is genuinely unresolvable but whose trailing "
                  "part is a registered transform would then be accepted "
                  "silently, so the invalid reference goes unreported and the "
                  "assertion that it IS reported fails — it would NOT resolve.",
    "rationale": "REJECT from `out = orderingRefInvalid …` at the ACCUMULATION "
                 "structure of the fold, which no other rival touches: gold "
                 "threads `flag || flagOnUnresolved …`, so the verdict is the "
                 "disjunction over all parts, while the rival overwrites it, "
                 "making the verdict a function of the final part alone. Refuted "
                 "at a chain whose middle part is unresolved with no transform "
                 "(gold flags) and whose trailing part is unresolved but IS a "
                 "registered transform (the rival un-flags): gold `true`, rival "
                 "`false`, measured by evaluation. Varies `parts` to length 3 and "
                 "`hasTransform` to a PART-DEPENDENT lambda — the first in this "
                 "battery that is neither constant.",
    "witness": _tester(
        "example :\n"
        "    checkOrderingRefTester\n"
        "      (fun _ p => if p.name = 0 then some { isRel := false, relModel := 0 } else none)\n"
        "      (fun _ => { isRel := false, relModel := 0 })\n"
        "      (fun _ p => p.name = 2)\n"
        "      7\n"
        "      [{ name := 0, isAlias := false }, { name := 1, isAlias := false },\n"
        "       { name := 2, isAlias := false }]\n"
        "      = false := by\n"
        "  decide\n"),
})


# ===========================================================================
# Nagini -> velvet accounting. This battery ships 8 SPEC cases: the 6 ported ones
# plus TWO rivals added by the adversarial audit (weak-alias-no-descent,
# weak-flag-not-monotone) that attack clauses the port left unprobed — the alias
# DESCENT and the fold's ACCUMULATION. The nagini sibling ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 1 mandatory frame-mutation rival, 3
# partial-domain uniqueness rivals, 1 divergence rival) plus 2 AXIOM_TESTS
# entries. It contracts ONE modeled function, `check_related_path`, over a
# read-only `List[int]` path carrying a fractional heap permission, with FIVE
# @ContractOnly graph accessors (resolve_kind / relation_target / pk_kind /
# pk_target / transform_present). This bundle contracts the SAME core behaviour
# (thread the three schema accessors across the chain of parts of one reference
# and decide whether it is flagged) as a single method `checkOrderingRef` over
# an immutable `List Part`, PARAMETRIC in three free function inputs — so the
# five nagini accessors collapse into `lookup`/`aliasField`/`hasTransform` and
# become free inputs rather than axioms. The value surface carries across
# intact; the permission surface does not exist here.
#
#   nagini case                       kind          -> here                        disposition
#   -----------------------------------------------------------------------------------------------
#   frame-mutation-write-path         uniqueness    -> (none)                       VACUOUS
#   pk-alias-reverted                 uniqueness    -> weak-alias-via-lookup        PORTED
#   non-relation-reset-reverted       uniqueness    -> weak-nonrel-no-terminate     PORTED
#   transform-rescue-dropped          uniqueness    -> weak-drop-transform-escape   PORTED
#   diverge-nonempty-path             uniqueness    -> (none)                       SPEC-CLOSED
#   pos-cheapest-return-oracle        soundness     -> pos-closed-form              PORTED
#   pos-reorder-branches              soundness     -> pos-inline-reorder-step      PORTED
#   admiss-normal-related-path        admissibility -> admiss-grounded              RE-AIMED
#   (none — audit-added)              uniqueness    -> weak-alias-no-descent        NEW
#   (none — audit-added)              uniqueness    -> weak-flag-not-monotone       NEW
#   ax-sound-graph-functions          axiom         -> (none)                       G-AX lane
#   ax-cover-caller-domain            axiom         -> (none)                       G-AX lane
#
# VACUOUS (frame-mutation-write-path): the nagini rival keeps the gold body then
#   writes path[0] into the read-only `path` granted only at half permission, and
#   must be rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: every binder is an immutable value/function, the method declares
#   no `mut` binder over its inputs, there is no heap and no aliasing. There is no
#   read-only input to overwrite and no permission system to trip, so the class is
#   vacuous. No substitute fabricated (per the porting map).
# CLOSED BY THE SEMANTICS (diverge-nonempty-path): on nagini this is rejected by
#   the MustTerminate(2) obligation. CORRECTED BY THE AUDIT, twice. This bundle is
#   `total`, not `partial`, so the disposition was re-derived with real builds; see
#   the DIVERGENCE bullet in the header. Summary: (a) the no-measure rival's
#   rejection is raised at the `method` declaration, which the witness file
#   retains, so the RIVAL-side witness build fails too (exit 1) and the gate would
#   score the case `witness-unproven` => MALFORMED-TESTS; and (b) `total` DOES
#   close the class. An earlier revision claimed it does not, on the ground that a
#   `decreasing` annotation is accepted without being proven to decrease, and
#   reported a loop annotated `decreasing i` while `i` increases as VERIFYING at
#   exit 0. Rebuilt, that shape is REJECTED: a loop whose body never changes its
#   measure (`while q > 0 / invariant 0 <= q / done_with q = 0 / decreasing q`,
#   body `q := q`) exits 1 on the measure's own goal, `case «decreasing_1: q»`,
#   residual `q < q`. So the spec does NOT admit an impl that hangs on the
#   F2P-shaped input, nothing is an open spec hole, and the class is unshippable
#   only for the witness reason in (a).
# RE-AIMED (admiss-normal-related-path -> admiss-grounded): the nagini case
#   establishes that the half-permission grant on `path` is held and root>=0 is
#   usable — a permission/precondition fact with no analogue on a referentially-
#   transparent carrier with no `require` clause. Re-aimed to the sharper residual
#   risk here: a degenerate post-image. It discharges a live in-region assert
#   pinning NOT-flagged (a validly resolving part) and FLAGGED (a part that fails
#   to resolve with nothing to host a transform).
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job. Here the schema
#   accessors are not axiomatized oracles but the FREE inputs
#   `lookup`/`aliasField`/`hasTransform` (an A-reference the R/I legs differential-
#   test), so there is no consumed contract to probe in this lane, and the gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the five input binders of
#   the sole ensures (pts = 3 distinct input points):
#     parts       — [alias] (R1), [nonrel, nonrel] (R2), [nonrel, unresolved] (R3),
#                   [alias, resolves] (R4), [nonrel, unresolved, transform] (R5):
#                   varies length (1, 2 and 3) and the isAlias flag, and covers
#                   the alias / resolves-non-rel / resolves-relation /
#                   fails-to-resolve part shapes, in leading, middle and trailing
#                   position.
#     lookup      — const `none` (R1), const `some non-rel` (R2), name-conditional
#                   some/none (R3, R4, R5): all three resolution outcomes
#                   exercised.
#     aliasField  — MEANINGFULLY varied only by R4. R1 passes a RELATION identity
#                   field, but its chain is ONE part long, so nothing follows the
#                   descent and gold's verdict is `false` for BOTH isRel values at
#                   that input (measured) — the binder is present but inert there.
#                   R4 is the case whose refutation genuinely depends on it: at
#                   R4's input gold is `false` for isRel=true and `true` for
#                   isRel=false. R2/R3/R5 use a non-relation field.
#     hasTransform— false (R1, R2, R4), const true (R3), PART-DEPENDENT
#                   `fun _ p => p.name = 2` (R5): both constant values plus a
#                   non-constant lambda. R3's refutation depends on it being true
#                   and R5's on it being true for the trailing part and false for
#                   the middle one, so the binder is not held fixed and its
#                   variation is verdict-changing, not two spellings of one point.
#     cls0        — 1 (R1), 3 (R2), 5 (R3), 2 (R4), 7 (R5): varied across the
#                   witnesses. The seed model's identity does not by itself affect
#                   the verdict (the accessors are free functions threaded
#                   identically by rival and gold, and the graph is abstract Nat
#                   ids), so this variation is bookkeeping, not coverage — noted
#                   rather than claimed.
#   Every independent sub-behavior of the sole post-image is attacked: the alias
#   RESOLUTION (R1), the alias DESCENT (R4), the non-relation descent-termination
#   (R2), the transform escape hatch (R3), and the fold's ACCUMULATION structure
#   (R5). No two rivals share a witness input. Each rival's defect was confirmed
#   OBSERVABLE by evaluating `orderingRefInvalid` and the rival's own fold at the
#   witness input (they disagree), so no case rests on a mere reshape; and each
#   witness was confirmed to DISCRIMINATE against the subject the gate scores it
#   on — a verifying positive of this battery — with the flipped-claim forgery
#   elaborating there (exit 0) while the witness fails by plain evaluation. See
#   WITNESS MECHANICS above for why gold itself is not that subject.
#
# AXIOM_TESTS: dropped (see above).
AXIOM_TESTS = []

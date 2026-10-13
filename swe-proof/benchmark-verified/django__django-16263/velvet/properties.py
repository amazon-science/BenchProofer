"""properties.py — G-PBT falsification battery for django__django-16263 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct countQueryShape`` obligation survives) and swaps in a
candidate implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, two ``ensures`` clauses):

  countQueryShape (annos : List Annotation) (added : List Added)
      (groupByTuple isSliced distinct combinator havingFilter : Bool)
      return (res : Plan)
    ensures res.needsNesting = needsNesting annos (added.map (·.name))
              groupByTuple isSliced distinct combinator havingFilter
    ensures res.keptNames = keptNames res.needsNesting distinct annos added

  The method decides the shape of a counting query over a set of already-declared
  alias entries: whether the count must run inside a nested query, and which
  alias names survive into the produced SQL. There is NO ``require`` clause, so
  the domain is every input tuple, and the ``axioms`` region is EMPTY — both
  clauses are pinned to fully-unfolded ``def``s over the method's own arguments
  (``needsNesting`` / ``anyPriorAggregate`` / ``isExisting`` / ``keptNames`` /
  ``maskFold`` / ``referencedNames``), so there is no opaque answer-key term a
  wrong impl could echo without doing the work. The ungrounded-oracle-echo class
  is therefore N/A, and the honest structural reshape serves as the positive
  control instead.

  CLAUSE 1 (``needsNesting``) is a disjunction of five independently-attackable
  triggers — ``groupByTuple``, ``isSliced``, ``anyPriorAggregate annos names
  havingFilter``, ``distinct``, ``combinator`` — where the middle one is itself
  compound: a PRIOR alias entry is one that is in the visible SELECT set and is
  NOT among the added names (``isExisting``), and it forces nesting only when it
  itself summarises rows OR is windowed; a row-summarising filter
  (``havingFilter``) forces nesting on its own. Four axes live inside that one
  disjunct — the SELECT-set filter, the not-among-the-added filter, the
  summarises-or-windowed predicate, and the filter channel — and each is attacked
  separately below.

  CLAUSE 2 (``keptNames``) is a three-way branch: no nesting -> just the added
  names; nesting without duplicate-row collapsing -> ``maskFold added`` (each
  added name TOGETHER WITH every name it refers to, so an unreferenced prior
  entry is dropped); nesting WITH duplicate-row collapsing -> pruning suppressed,
  every visible prior entry retained alongside the added names. All three arms,
  plus the reference channel inside ``maskFold``, are attacked.

  SEVEN INPUT BINDERS: ``annos`` (each element carrying ``name`` / ``selected`` /
  ``isAggregate`` / ``isWindow``), ``added`` (each carrying ``name`` and an
  ``expr`` reference tree), and the five booleans. ``distinct`` is load-bearing
  TWICE (a nesting trigger AND the mask-branch selector) and ``res.needsNesting``
  feeds clause 2, so the two clauses are coupled; the reject witnesses drive the
  binders to ELEVEN distinct input points so no binder is pinned at one value
  across the rival set.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``countQueryShapeTester annos added … = false`` says
the extracted program's result violates the postcondition at that concrete
input) and closes by ``decide``, checked in a file whose ``prove_correct`` block
has been stripped so no tactic script can mask the verdict. ``decide`` reduces
the extracted program by kernel computation; the frozen program contains a
``while`` loop over the added entries and its fixpoint is opaque to the kernel,
so a witness applied to the frozen solution gets STUCK (``reduction got stuck at
the Decidable instance``) — which is the required FAIL-on-gold half. Each reject
rival is therefore expressed as a LOOP-FREE impl computing its (wrong) plan
directly from the pure helpers, so its extracted tester ``decide``s over the
concrete literals. This is a witnessing convenience, not a weakening: the frozen
spec is untouched, every rival's divergence from the spec is real at the
witnessed input, and the gold BEHAVIOUR was independently confirmed to SATISFY
the postcondition at all eleven points (a loop-free but semantically-gold impl
discharges ``countQueryShapeTester … = true`` by ``decide`` at every one of
them), so FAIL-on-gold is genuine discrimination and not merely a reduction
artifact. Every witness states its refutation at fully concrete literals — no
hypothesis binders at all — so the gate's inconsistent-binder probe is
degenerate by construction.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally-different but
    behaviourally identical impls must verify, else the spec is SPEC-TOO-STRONG
    on the shape of the impl.
  * ADMISSIBILITY — the sibling's probe self-asserts that an F2P-shaped input
    satisfies its fractional-permission precondition. This backend has NO
    ``require`` clause at all and no permission surface, so that probe is
    degenerate; the residual risk on an unrestricted domain is a DEGENERATE
    post-image, and the case is re-aimed accordingly.
  * FRAME / PERMISSION MUTATION — VACUOUS on this backend. The sibling carries
    two MANDATORY cases here because its read-only sequence inputs are held at a
    fractional heap permission an impl can illegally overwrite. Lean/Velvet are
    referentially transparent: ``annos`` and ``added`` are immutable values
    declared read-only (not ``mut``), there is no heap, no aliasing, no ``Old``
    and no permission system, so there is no read-only input to overwrite and no
    frame clause to violate. The class has no carrier analogue; NOT ported, and
    no substitute fabricated.
  * DIVERGENCE / NON-TERMINATION — REJECTED by this bundle's carrier, so it is
    neither a hole nor vacuous; it is UNSHIPPABLE for a tooling reason. See the
    footer.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: every rival gets most of
    the domain right and diverges on one sub-domain.
"""
from pathlib import Path

INSTANCE = "django__django-16263"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the impl region (or is the `prove_correct`
# tactic body), and each is asserted unique at load, so every _swap keeps
# same_spec and preserves the `prove_correct countQueryShape` obligation.
# ---------------------------------------------------------------------------

# The WHOLE gold impl block, markers included. Reject rivals and the loop-free
# positive replace this block wholesale.
_IMPL = _BASE[_BASE.index("    -- impl-start"):
              _BASE.index("    -- impl-end") + len("    -- impl-end")]
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# The `-- impl-start` marker line: the admissibility case inserts an in-region
# `assert` immediately after it and keeps the entire gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# The loop body, wholly inside the impl region. The loop-preserving positive
# reshapes ONLY these lines, leaving the loop, its invariants and the frozen
# proof script intact.
_LOOP_BODY = """    do
      let a := added[i - 1]!
      m := (a.name :: referencedNames a.expr) ++ m
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# The frozen proof body (tactic script only — elided from the spec view). A
# variant that removes the loop has no invariant to peel, so it retunes this to
# the flat shape; the `prove_correct countQueryShape` header always survives.
_PROOF_GOLD = _BASE[_BASE.index("prove_correct countQueryShape by"):].rstrip()
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# A loop-free proof body: with the impl a straight-line expression there is no
# loop invariant, so `loom_solve` alone discharges the two ensures (for a correct
# reshape) or leaves them unsolved (for the rivals, which is the point). The
# rivals retune to this shape so the rejection is attributable to the spec — via
# the witness — and never to a tactic script tuned to a loop that is gone.
_PROOF_FLAT = "prove_correct countQueryShape by\n  loom_solve"


# ---------------------------------------------------------------------------
# The loop-free impl template. Each reject rival perturbs exactly ONE hole,
# leaving every other hole at its gold value, so its divergence from the spec is
# confined to one clause / one axis and the `refinement` argument is about that
# axis alone.
# ---------------------------------------------------------------------------

_EXISTING_GOLD = "annos.filter (isExisting names)"
_PRIOR_GOLD = "(existing.any (fun a => a.isAggregate || a.isWindow)) || havingFilter"
_NESTING_GOLD = "nesting"
_KEPT_GOLD = "keptNames nesting distinct annos added"


def _flat(existing=_EXISTING_GOLD, prior=_PRIOR_GOLD,
          nesting=_NESTING_GOLD, kept=_KEPT_GOLD, proof=_PROOF_FLAT):
    """Full variant: whole impl block replaced by a loop-free form, proof
    retuned to the flat shape."""
    block = f"""    -- impl-start
    let names := added.map (·.name)
    let existing := {existing}
    let priorAgg := {prior}
    let nesting := groupByTuple || isSliced || priorAgg || distinct || combinator
    let kept := {kept}
    return {{ needsNesting := {nesting}, keptNames := kept }}
    -- impl-end"""
    return _swap(_swap(_BASE, _IMPL, block), _PROOF_GOLD, proof)


# ---------------------------------------------------------------------------
# Witness plumbing. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches the post-image through Velvet's own tester machinery:
# `countQueryShapeTester annos added gbt isl dist comb hf = false` says the
# extracted program's plan violates the method's postcondition at that concrete
# input. Every argument is a literal, so `decide` reduces the (loop-free) rival
# program without getting stuck; against the frozen loop it gets stuck, which is
# the required FAIL-on-gold half.
# ---------------------------------------------------------------------------

def _b(x):
    return "true" if x else "false"


def _A(name, selected, is_aggregate, is_window):
    """A concrete prior-alias-entry literal for a witness input point."""
    return ('{name := "%s", selected := %s, isAggregate := %s, isWindow := %s}'
            % (name, _b(selected), _b(is_aggregate), _b(is_window)))


def _Add(name, expr):
    """A concrete added-entry literal."""
    return '{name := "%s", expr := %s}' % (name, expr)


def _ref(name):
    """An expression that refers to exactly one alias name."""
    return 'Expr.reference "%s"' % name


_NO_REF = "Expr.composite []"   # an expression that refers to nothing


def _nested_ref(name):
    """A COMPOSITE expression whose referred-to name sits one level DOWN.

    The reference channel has two arms: `referencedNames (.reference s) = [s]`
    (the base case) and `referencedNames (.composite es)` recursing through the
    children. A `.reference` literal and an empty `.composite` between them
    exercise only the base case and the empty list, so a rival that collects
    references at the TOP LEVEL ONLY agrees with gold on both. This drives the
    RECURSIVE arm, which is what makes such a rival refutable.
    """
    return 'Expr.composite [%s]' % _ref(name)


def _witness(annos, added, group_by_tuple=False, is_sliced=False,
             distinct=False, combinator=False, having_filter=False):
    return ("\n"
            "extract_program_for countQueryShape\n"
            "prove_precondition_decidable_for countQueryShape\n"
            "prove_postcondition_decidable_for countQueryShape\n"
            "derive_tester_for countQueryShape\n\n"
            "example : countQueryShapeTester\n"
            "    [%s]\n"
            "    [%s]\n"
            "    %s %s %s %s %s = false := by\n"
            "  decide\n"
            % (", ".join(annos), ", ".join(added),
               _b(group_by_tuple), _b(is_sliced), _b(distinct),
               _b(combinator), _b(having_filter)))


SPEC_TESTS = [

    # =====================================================================
    # SOUNDNESS / POSITIVE CONTROLS — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen code shape rather than to the
    # behaviour). Both were confirmed to build green.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest correct impl: no loop at all — compute the nesting
        # decision and return the grounded retained-name model directly, so the
        # executable surface is maximally different from the frozen backward
        # fold. Both `ensures` hold by definition; the reproof is a bare
        # `loom_solve` (there is no loop invariant left to peel).
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    let names := added.map (·.name)\n"
                  "    let nesting := needsNesting annos names groupByTuple "
                  "isSliced distinct\n"
                  "                     combinator havingFilter\n"
                  "    return { needsNesting := nesting,\n"
                  "             keptNames := keptNames nesting distinct annos added }\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_FLAT),
        "rationale": (
            "a structurally-different but CORRECT impl — the whole backward fold "
            "replaced by a direct return of the grounded models `needsNesting …` "
            "and `keptNames …` — MUST verify on the whole domain, else both "
            "ensures clauses are SPEC-TOO-STRONG (pinned to the frozen loop's "
            "shape rather than to its behaviour). Doubles as the honest "
            "no-ungrounded-echo control: the two clauses are pinned to "
            "fully-unfolded defs over the method's own arguments, so computing "
            "them IS the work and a direct return is correct, not a cheat. "
            "(Sibling: pos-control-esfd-accumulate / pos-control-ick-accumulate, "
            "re-shaped — the sibling's positives reshape two per-element loop "
            "bodies into boolean accumulates; the loop-free closed form is the "
            "maximally-different correct shape on this carrier.)"),
    },
    {
        "id": "pos-control-named-contribution",
        "kind": "soundness",
        "expect": "verify",
        # The minimal-edit correct reshape, at the other extreme: keep the whole
        # loop, its invariants and the frozen proof script byte-for-byte, and
        # only name the exposed entry's contribution in a local `let` before
        # prepending it. Observationally identical at every input; the frozen
        # drop-step lemma still closes the loop-body goal untouched.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "    do\n"
            "      let a := added[i - 1]!\n"
            "      let contrib := a.name :: referencedNames a.expr\n"
            "      m := contrib ++ m\n"
            "      i := i - 1"),
        "rationale": (
            "naming the exposed entry's contribution in a local `let contrib` "
            "before prepending it folds the same entries in the same order, so "
            "both ensures still hold on the whole domain; the loop, its "
            "invariants and the frozen proof script are untouched. A correct "
            "reshape must verify, else the spec is SPEC-TOO-STRONG over the shape "
            "of the loop BODY (the sharper failure: the direct-model positive "
            "would still pass a spec over-fit to a straight-line impl). "
            "(Sibling: pos-control-ick-accumulate — a minimal in-loop reshape "
            "that keeps the invariant and the linking step.)"),
    },

    {
        "id": "pos-control-forward-fold",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (attack E). The two shipped positives sit at the two
        # ends of ONE axis (loop present / loop absent) but both fold the added
        # entries BACKWARD, accumulating by prepending. This one keeps a loop and
        # reverses its DIRECTION: it counts up from 0, appends each contribution
        # to the tail, and carries a forward `added.take i` invariant with its own
        # `decreasing added.length - i` measure. Observationally identical (the
        # same entries in the same order), but nothing of the frozen loop's
        # shape survives — neither the index direction, nor the accumulation
        # side, nor the invariant, nor the drop-step lemma the frozen proof
        # applies. The linking step is re-proven from scratch as an inline
        # induction over `List.take`, so the case reproves the obligation rather
        # than restating it.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    let names := added.map (·.name)\n"
                  "    let existing := annos.filter (isExisting names)\n"
                  "    let priorAgg := (existing.any (fun a => a.isAggregate || "
                  "a.isWindow)) || havingFilter\n"
                  "    let nesting := groupByTuple || isSliced || priorAgg || "
                  "distinct || combinator\n"
                  "    let mut m : List String := []\n"
                  "    let mut i := 0\n"
                  "    while i < added.length\n"
                  "      invariant 0 ≤ i ∧ i ≤ added.length\n"
                  "      invariant m = maskFold (added.take i)\n"
                  "      done_with i = added.length\n"
                  "      decreasing added.length - i\n"
                  "    do\n"
                  "      let a := added[i]!\n"
                  "      m := m ++ (a.name :: referencedNames a.expr)\n"
                  "      i := i + 1\n"
                  "    let kept :=\n"
                  "      if nesting then\n"
                  "        if distinct then names ++ existing.map (·.name) else m\n"
                  "      else names\n"
                  "    return { needsNesting := nesting, keptNames := kept }\n"
                  "    -- impl-end"),
            _PROOF_GOLD,
            "prove_correct countQueryShape by\n"
            "  loom_solve\n"
            "  · have key : ∀ (l : List Added) (k : Nat), k < l.length →\n"
            "        maskFold (l.take k) ++ (l[k]!.name :: referencedNames l[k]!.expr)\n"
            "          = maskFold (l.take (k + 1)) := by\n"
            "      intro l\n"
            "      induction l with\n"
            "      | nil => intro k hk; simp at hk\n"
            "      | cons a rest ih =>\n"
            "        intro k hk\n"
            "        cases k with\n"
            "        | zero => simp [maskFold]\n"
            "        | succ n =>\n"
            "          have hn : n < rest.length := by simp at hk; omega\n"
            "          have hg : (a :: rest)[n + 1]! = rest[n]! := by\n"
            "            simp [List.getElem!_eq_getElem?_getD]\n"
            "          rw [List.take_succ_cons, List.take_succ_cons, maskFold_cons, "
            "maskFold_cons,\n"
            "              hg, List.append_assoc, ih n hn]\n"
            "    have h := key added i (by omega)\n"
            "    simp_all\n"
            "  all_goals simp_all [keptNames, needsNesting, anyPriorAggregate]\n"),
        "rationale": (
            "a correct impl that folds the added entries in the OPPOSITE "
            "DIRECTION — forward from 0, appending rather than prepending, under "
            "a forward `added.take i` invariant and its own decreasing measure — "
            "must verify, else clause 2 is SPEC-TOO-STRONG on the direction of "
            "the fold specifically. The two shipped positives do not test this: "
            "one removes the loop entirely and the other keeps the frozen loop "
            "verbatim, so BOTH accumulate backward and a spec over-fit to the "
            "backward fold would pass them. Nothing of the frozen loop's shape "
            "survives here, and the linking step is re-proven from scratch by "
            "induction over `List.take` rather than by the frozen "
            "`maskFold_drop_step` lemma — so this is a reproof, not a restatement."),
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling asserts that an F2P-shaped input satisfies its
    # half-permission Requires. This backend has NO `require` clause at all (the
    # domain is every input tuple) and no permission surface, so that probe is
    # degenerate. The sharper residual risk on an unrestricted domain is a
    # DEGENERATE post-image: a spec no input distinguishes reads exactly like one
    # every impl meets. This case discharges an in-region `assert`, at concrete
    # scenario-shaped inputs, that the post-image is NON-DEGENERATE across BOTH
    # clauses: a prior entry that does not summarise rows does NOT force nesting
    # while one that does DOES (clause 1, the discriminator the failing scenarios
    # observe), and the retained-name set differs between the two nested arms —
    # under duplicate-row collapsing an unreferenced prior entry SURVIVES, and
    # without it the referenced entry is retained by the reference channel
    # (clause 2). The impl is kept verbatim so the method's own obligation still
    # discharges; the proof gains a `decide` arm for the assert goal. Confirmed
    # to build green.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      needsNesting [" + _A("p", True, False, False) + "]\n"
                  '        ["c"] false false false false false = false ∧\n'
                  "      needsNesting [" + _A("p", True, True, False) + "]\n"
                  '        ["c"] false false false false false = true ∧\n'
                  "      keptNames true false\n"
                  "        [" + _A("p", True, False, False) + "]\n"
                  "        [" + _Add("c", _ref("p")) + '] = ["c", "p"] ∧\n'
                  # The two NESTED arms at ONE SHARED input, so the pair
                  # exhibits them DISAGREEING rather than merely each having a
                  # value: with nothing referred to, the non-collapsing arm
                  # PRUNES the prior entry to just the added name, while the
                  # collapsing arm RETAINS it. Without the shared-input pair the
                  # assert pinned two arms at two different inputs that happen
                  # to share a value, which demonstrates no disagreement at all.
                  "      keptNames true false\n"
                  "        [" + _A("p", True, False, False) + "]\n"
                  "        [" + _Add("c", _NO_REF) + '] = ["c"] ∧\n'
                  "      keptNames true true\n"
                  "        [" + _A("p", True, False, False) + "]\n"
                  "        [" + _Add("c", _NO_REF) + '] = ["c", "p"]))\n'),
            _PROOF_GOLD,
            "prove_correct countQueryShape by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [maskFold_drop_step added i (by omega) (by omega)]; simp_all)\n"
            "    | simp_all [keptNames, needsNesting, anyPriorAggregate]\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at scenario-shaped "
            "inputs: a visible prior entry that does not summarise rows must give "
            "NO nesting while the same entry summarising rows must give nesting "
            "(clause 1 — the discriminator the failing scenarios observe), and "
            "the two nested arms of clause 2 must DISAGREE at one shared input — "
            "with nothing referred to, the non-collapsing arm prunes the prior "
            "entry away (`[\"c\"]`) while the collapsing arm retains it "
            "(`[\"c\", \"p\"]`) — plus the reference channel widening the "
            "non-collapsing arm back to the referred-to entry. The assert must "
            "discharge (else the obligation is degenerate on this domain); the "
            "impl is kept verbatim so both ensures still verify. (Sibling: "
            "admiss-esfd-read-input, re-aimed from precondition admissibility to "
            "post-image non-degeneracy, since this backend has no `require` and "
            "no permission surface for the sibling's Acc(...,1/2) probe.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input, and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each is a LOOP-FREE closed
    # form (see the CARRIER NOTE) perturbing exactly ONE axis of the frozen impl.
    # Every one was confirmed by two real builds: the witness elaborates against
    # the rival and fails against the frozen solution.
    # =====================================================================

    # ---- CLAUSE 1, the summarises-or-windowed axis -----------------------
    {
        "id": "weak-nesting-presence-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Nesting is forced by the mere PRESENCE of a prior visible alias entry,
        # ignoring whether that entry actually summarises rows or is windowed.
        # This is the pre-image skeleton of clause 1 (Solution_prepatch.lean).
        # Correct on every input with no prior visible entry, and on every input
        # whose prior entries all summarise; diverges exactly on a visible prior
        # entry that summarises NOTHING.
        "module": _flat(prior="!existing.isEmpty || havingFilter"),
        "refinement": (
            "this is the pre-change nesting rule: any previously-declared visible "
            "alias entry forces the count into a nested query, whether or not it "
            "summarises rows. Its faithful real counterpart leaves the "
            "unconditional nesting in place, so a plain non-summarising prior "
            "alias entry still produces the extra nested query the scenario "
            "forbids — the observed statement count stays at two where one is "
            "asserted. It resolves NOTHING: this is precisely the behaviour the "
            "change removes."),
        "rationale": (
            "REJECT from clause 1 (`res.needsNesting = needsNesting …`) via the "
            "`anyPriorAggregate` disjunct: on a single visible prior entry with "
            "`isAggregate = false` and `isWindow = false`, no filter and no "
            "structural trigger, the spec requires `false` but the rival returns "
            "`true`. Verifying would be SPEC-TOO-WEAK — the summarises-or-windowed "
            "discriminator entirely unpinned. Refuted at exactly that point; it "
            "is the only witness that holds a visible prior entry at "
            "isAggregate=false AND isWindow=false with every boolean false. "
            "(Sibling: partial-domain-esfd-presence-only.)"),
        "witness": _witness([_A("p", True, False, False)],
                            [_Add("c", _NO_REF)]),
    },
    {
        "id": "weak-nesting-drop-window",
        "kind": "uniqueness",
        "expect": "reject",
        # A near-miss of the above: keep the summarises-rows test but drop the
        # WINDOWED half of the prior-entry predicate. Agrees with gold on every
        # input the presence-only rival gets wrong AND on every row-summarising
        # prior entry; diverges only on a prior entry that is windowed WITHOUT
        # summarising rows — a strictly smaller sub-domain, so it gets its own
        # witness rather than sharing one.
        "module": _flat(prior="(existing.any (fun a => a.isAggregate)) || havingFilter"),
        "refinement": (
            "a faithful counterpart that tested only whether a prior alias entry "
            "summarises rows, and not whether it is a windowed expression, would "
            "skip the nested query for a query carrying a windowed prior alias "
            "entry. A windowed expression is evaluated over the result rows, so "
            "collapsing them to a single count row without nesting changes the "
            "value it computes: the count would be taken over the wrong row set. "
            "It leaves the windowed half of the condition unimplemented and so "
            "resolves nothing on any scenario carrying one, while agreeing with "
            "the change everywhere else."),
        "rationale": (
            "REJECT from clause 1 via the second half of `anyPriorAggregate`'s "
            "element predicate (`a.isAggregate || a.isWindow`): on a visible prior "
            "entry with `isAggregate = false` and `isWindow = true` the spec "
            "requires `true` and the rival returns `false`. This is the sub-domain "
            "the presence-only rival gets RIGHT, so the two do not share a "
            "witness; it is also the only witness that drives `isWindow` to true, "
            "making that field demonstrably load-bearing. Verifying would be "
            "SPEC-TOO-WEAK (the windowed channel unpinned). (Sibling: the "
            "predicate axis of partial-domain-esfd-presence-only, split out — the "
            "sibling's carrier folds both flags into one `summ` bit, so it cannot "
            "separate them; this carrier keeps them as distinct fields and the "
            "battery must attack each.)"),
        "witness": _witness([_A("p", True, False, True)],
                            [_Add("c", _NO_REF)]),
    },

    # ---- CLAUSE 1, the which-entries-count axes -------------------------
    {
        "id": "weak-nesting-all-declared",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the visible-SELECT-set half of `isExisting`: consider EVERY
        # declared alias entry, including one that is merely declared and not
        # part of the visible SELECT set. Correct whenever every declared entry
        # is visible; diverges on a declared-but-not-visible summarising entry.
        "module": _flat(existing="annos"),
        "refinement": (
            "this is the pre-change source axis: the decision is taken over ALL "
            "declared alias entries rather than only those in the query's visible "
            "SELECT set. Its faithful counterpart still forces the nested query "
            "for an alias entry that summarises rows but was declared without "
            "being selected — the entry is never emitted, so nesting buys nothing "
            "and the scenario that asserts a single statement for exactly that "
            "shape still observes two. It resolves nothing."),
        "rationale": (
            "REJECT from clause 1 via `isExisting`'s `a.selected` conjunct: on a "
            "single declared entry with `selected = false` that summarises rows, "
            "the spec requires `false` (the entry is not a PRIOR entry at all) but "
            "the rival returns `true`. This is the only witness holding `selected` "
            "at false, so that field is demonstrably load-bearing. Verifying would "
            "be SPEC-TOO-WEAK (the visible-SELECT-set restriction unpinned). "
            "(Sibling: partial-domain-esfd-source-all.)"),
        "witness": _witness([_A("p", False, True, False)],
                            [_Add("c", _NO_REF)]),
    },
    {
        "id": "weak-nesting-counts-added",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the other half of `isExisting`: keep the visible-SELECT-set test
        # but stop excluding the names being ADDED for the summary itself, so the
        # summary's own entry is counted as a prior one and forces nesting
        # against itself. Correct whenever no added name collides with a visible
        # entry; diverges exactly on the collision.
        "module": _flat(existing="annos.filter (fun a => a.selected)"),
        "refinement": (
            "a faithful counterpart that failed to exclude the names being added "
            "for the summary itself would treat the summary's own alias entry as a "
            "pre-existing one: since the summary always summarises rows, EVERY "
            "such query would be forced into a nested query regardless of what was "
            "declared before it. That is strictly worse than the pre-change "
            "behaviour — it re-introduces the extra nested query on exactly the "
            "shapes the scenarios assert a single statement for, so it resolves "
            "nothing."),
        "rationale": (
            "REJECT from clause 1 via `isExisting`'s `!(names.contains a.name)` "
            "conjunct: when the sole visible summarising entry's name is one of "
            "the added names, the spec requires `false` (it is not a PRIOR entry) "
            "but the rival returns `true`. This is the only witness where an "
            "`annos` name COLLIDES with an `added` name, so the name field and the "
            "not-among-the-added restriction are demonstrably load-bearing — no "
            "other rival's witness moves them. Verifying would be SPEC-TOO-WEAK. "
            "(Sibling: the `alias not in added_aggregate_names` half of the "
            "decision, which the sibling's carrier folds into its `selected` bit "
            "and cannot probe separately.)"),
        "witness": _witness([_A("c", True, True, False)],
                            [_Add("c", _NO_REF)]),
    },
    {
        "id": "weak-nesting-drop-filter",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the row-summarising-filter channel from the prior-entry disjunct.
        # Correct on every input with no such filter, i.e. on every other
        # witness's point; diverges exactly when the filter is the sole trigger.
        "module": _flat(prior="existing.any (fun a => a.isAggregate || a.isWindow)"),
        "refinement": (
            "a faithful counterpart that read only the declared alias entries and "
            "ignored a retained row-summarising filter would run the count "
            "flat whenever such a filter is the only reason nesting is needed. "
            "The filter restricts which groups survive, so evaluating it in the "
            "same flat statement as the count produces the count over the "
            "unrestricted rows — a wrong number, not merely an extra statement. "
            "It resolves nothing on any shape carrying such a filter."),
        "rationale": (
            "REJECT from clause 1 via `anyPriorAggregate`'s `|| havingFilter` "
            "disjunct: with NO declared alias entries at all and "
            "`havingFilter = true`, the spec requires `true` and the rival returns "
            "`false`. This is the only witness driving `havingFilter` to true, and "
            "the only one with `annos = []`, so both are demonstrably "
            "load-bearing. Verifying would be SPEC-TOO-WEAK (the filter channel "
            "unpinned). (Sibling: the `filter_summary != 0` disjunct of "
            "existing_summary_forces_derived, unattacked there and attacked here.)"),
        "witness": _witness([], [_Add("c", _NO_REF)], having_filter=True),
    },
    {
        "id": "weak-nesting-drop-combinator",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop one of the plain structural triggers of the top-level disjunction.
        # Correct on every input where that trigger is off — every other witness
        # point — and diverges exactly when it is the sole trigger. Cheap and
        # mechanical, but it is what demonstrates the binder is load-bearing.
        "module": _flat(nesting="groupByTuple || isSliced || priorAgg || distinct"),
        "refinement": (
            "a faithful counterpart that dropped this structural trigger would run "
            "the count flat over a query built by combining several result sets. "
            "The combination has to be materialised before the rows can be "
            "counted, so counting in the same statement counts the wrong rows — a "
            "wrong number on a shape the existing suite already pins, so it "
            "resolves nothing and additionally breaks behaviour the change "
            "preserves."),
        "rationale": (
            "REJECT from clause 1 via the `|| combinator` disjunct: with every "
            "other trigger off, no declared entries and `combinator = true`, the "
            "spec requires `true` and the rival returns `false`. This is the only "
            "witness driving `combinator` to true, so that binder is demonstrably "
            "load-bearing — a rival mishandling only it would be caught by no "
            "other case. Verifying would be SPEC-TOO-WEAK (a top-level trigger "
            "unpinned). (Sibling: no counterpart — the sibling's carrier hard-wires "
            "the structural triggers out of its decision and exposes only the "
            "compound prior-entry disjunct; this carrier makes them explicit "
            "binders, so the battery must attack them.)"),
        "witness": _witness([], [_Add("c", _NO_REF)], combinator=True),
    },
    {
        "id": "weak-nesting-drop-groupbytuple",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). The shipped battery drove `groupByTuple` to
        # true only in the two reference-channel witnesses, where it serves
        # merely as a NESTING TRIGGER for a clause-2 attack — no rival
        # mishandled the trigger itself. So a spec that dropped this disjunct
        # entirely passed the whole shipped battery: every clause-1 rival holds
        # `groupByTuple = false`, and the two clause-2 rivals agree with gold on
        # clause 1. Drops the disjunct; correct wherever the trigger is off,
        # diverges exactly where it is the sole trigger.
        "module": _flat(nesting="isSliced || priorAgg || distinct || combinator"),
        "refinement": (
            "a faithful counterpart that dropped this structural trigger would "
            "run the count flat over a query that groups its rows into tuples. "
            "The grouping is what defines the rows to be counted, so counting "
            "in the same statement counts the pre-grouping rows and returns a "
            "wrong number on a shape the existing suite already pins — it "
            "resolves nothing and additionally breaks behaviour the change "
            "preserves."),
        "rationale": (
            "REJECT from clause 1 via the `groupByTuple ||` disjunct: with every "
            "other trigger off, no declared entries and `groupByTuple = true`, "
            "the spec requires `true` and the rival returns `false`. Verifying "
            "would be SPEC-TOO-WEAK (a top-level trigger unpinned). Refuted at "
            "`annos = []` with `groupByTuple` the sole trigger, an input point no "
            "other case occupies: the two witnesses that drive `groupByTuple` "
            "true both carry a prior entry AND attack clause 2, so neither "
            "refutes a rival that mishandles this disjunct. (Sibling: no "
            "counterpart — the sibling hard-wires the structural triggers out of "
            "its decision; this carrier makes them explicit binders.)"),
        "witness": _witness([], [_Add("c", _NO_REF)], group_by_tuple=True),
    },
    {
        "id": "weak-nesting-drop-sliced",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). The mirror of the above for the other plain
        # trigger. `isSliced` was likewise driven true by exactly one shipped
        # witness (weak-kept-retain-all-when-nested), and there only to REACH
        # the nested arm for a clause-2 attack, so a spec dropping this disjunct
        # also passed the shipped battery.
        "module": _flat(nesting="groupByTuple || priorAgg || distinct || combinator"),
        "refinement": (
            "a faithful counterpart that dropped this trigger would run the "
            "count flat over a query that has already been narrowed to a window "
            "of rows. The narrowing has to be applied before the rows can be "
            "counted, so counting in the same statement counts the un-narrowed "
            "set — a wrong number on a shape the existing suite pins, so it "
            "resolves nothing."),
        "rationale": (
            "REJECT from clause 1 via the `|| isSliced` disjunct: with every "
            "other trigger off, no declared entries and `isSliced = true`, the "
            "spec requires `true` and the rival returns `false`. Verifying would "
            "be SPEC-TOO-WEAK. Refuted at `annos = []` with `isSliced` the sole "
            "trigger — a point no other case occupies, since the one shipped "
            "witness driving `isSliced` carries a prior entry and attacks clause "
            "2, so it does not refute a rival that mishandles this disjunct. "
            "(Sibling: no counterpart, as above.)"),
        "witness": _witness([], [_Add("c", _NO_REF)], is_sliced=True),
    },
    {
        "id": "weak-nesting-drop-distinct-trigger",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). `distinct` is load-bearing TWICE, and the
        # shipped battery only pinned the SECOND role: weak-kept-prune-under-
        # collapsing attacks clause 2's collapsing arm and agrees with gold on
        # clause 1. So a rival that keeps the clause-2 arm but drops `distinct`
        # from the NESTING disjunct passed the whole shipped battery. Correct
        # wherever some other trigger fires; diverges where `distinct` alone
        # would have forced nesting.
        "module": _flat(nesting="groupByTuple || isSliced || priorAgg || combinator"),
        "refinement": (
            "a faithful counterpart that ignored duplicate-row collapsing as a "
            "reason to nest would count the collapsed rows in the same flat "
            "statement that performs the collapsing. The collapse has to happen "
            "before the rows are counted, so the count comes out over the "
            "uncollapsed set — too large, on exactly the shapes the existing "
            "suite pins. It resolves nothing."),
        "rationale": (
            "REJECT from clause 1 via the `|| distinct` disjunct specifically — "
            "as distinct from `distinct`'s OTHER role selecting clause 2's "
            "retention arm: with every other trigger off, no declared entries "
            "and `distinct = true`, the spec requires `true` and the rival "
            "returns `false`. This pins the binder's clause-1 role, which the "
            "prune-under-collapsing rival does not: that rival agrees with gold "
            "on clause 1 everywhere. Verifying would be SPEC-TOO-WEAK. Refuted "
            "at `annos = []`, a point no other case occupies. (Sibling: no "
            "counterpart — the sibling's carrier has no duplicate-collapsing "
            "input at all.)"),
        "witness": _witness([], [_Add("c", _NO_REF)], distinct=True),
    },
    {
        "id": "weak-nesting-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # The polarity check: return the negation of the nesting decision. Cheap
        # and mechanical, but it carries a real refinement and it is what pins the
        # POLARITY of clause 1 (every other clause-1 rival only moves the
        # boundary; none of them would catch a wholesale inversion).
        "module": _flat(nesting="!nesting"),
        "refinement": (
            "returning the inverse nests exactly the queries that must stay flat "
            "and flattens exactly those that must nest: it adds the extra nested "
            "query to a plain query and strips it from one carrying a "
            "row-summarising prior alias entry, where the flat form counts the "
            "grouped rows instead of the whole set. Its faithful counterpart is "
            "wrong in both directions at once and resolves no scenario, failing "
            "much of the behaviour the change preserves as well."),
        "rationale": (
            "REJECT from clause 1: `!nesting` contradicts `res.needsNesting = "
            "needsNesting …` at every input where the decision is determinate. "
            "Refuted at a visible prior entry that summarises rows — where the "
            "spec requires `true` — the sub-domain on which every boundary-moving "
            "clause-1 rival above AGREES with gold, so this case is what pins the "
            "polarity rather than the boundary and it shares no witness. "
            "(Sibling: support-esfd-inverted.)"),
        "witness": _witness([_A("p", True, True, False)],
                            [_Add("c", _NO_REF)]),
    },

    # ---- CLAUSE 2, the retained-name set --------------------------------
    {
        "id": "weak-kept-drop-reference-channel",
        "kind": "uniqueness",
        "expect": "reject",
        # In the nested, non-duplicate-collapsing arm, retain ONLY the added
        # names and drop the names they REFER TO. Correct whenever nothing is
        # referred to (every other clause-2 witness's point) and on both other
        # arms; diverges exactly on a prior entry that a pushed-out summary
        # refers to.
        "module": _flat(kept="if nesting then (if distinct then names ++ "
                             "existing.map (·.name) else names) else names"),
        "refinement": (
            "a faithful counterpart that narrowed the retained set to the added "
            "names alone, never widening it by the names those additions refer "
            "to, would drop a prior alias entry that the pushed-out summary "
            "depends on. The summary's reference to it would then resolve to "
            "nothing and the statement would not run at all — the scenario that "
            "asserts a referred-to prior entry SURVIVES into the produced SQL "
            "fails outright, so it resolves nothing."),
        "rationale": (
            "REJECT from clause 2 (`res.keptNames = keptNames …`) via `maskFold`'s "
            "`referencedNames a.expr` half: in the nested non-collapsing arm the "
            "spec requires each added name TOGETHER WITH the names it refers to, "
            "and the rival returns the added names alone. This is the only witness "
            "whose `added` entry carries a non-trivial reference tree "
            "(`Expr.reference`), so the `expr` field and the whole reference "
            "channel are demonstrably load-bearing. Verifying would be "
            "SPEC-TOO-WEAK (the reference channel unpinned). (Sibling: "
            "partial-domain-ick-drop-refs.)"),
        "witness": _witness([_A("p", True, False, False)],
                            [_Add("c", _ref("p"))], group_by_tuple=True),
    },
    {
        "id": "weak-kept-shallow-reference-channel",
        "kind": "uniqueness",
        "expect": "reject",
        # The NEAR-MISS of the case above, and the one channel every other rival
        # leaves unattacked: keep the reference channel but collect only the
        # names an added entry refers to DIRECTLY, never descending into a
        # composite sub-expression. `referencedNames` is defined by recursion
        # over the expression tree, and its recursive arm is the only part of
        # the spec no other witness drives: every other witness holds `expr` at
        # `Expr.reference _` (the base case) or `Expr.composite []` (the empty
        # list), and this rival agrees with gold on BOTH. It diverges only where
        # a referred-to name sits one or more levels down.
        "module": _flat(
            kept="if nesting then (if distinct then names ++ "
                 "existing.map (·.name) else added.flatMap (fun a => a.name :: "
                 "(match a.expr with | Expr.reference s => [s] "
                 "| Expr.composite _ => []))) else names"),
        "refinement": (
            "a faithful counterpart that read only the outermost node of each "
            "added summary's expression would find the names it refers to "
            "directly and miss every name reached through a compound "
            "sub-expression. Real summary expressions are trees — a summary "
            "wrapping its reference in any enclosing operation puts that "
            "reference one level down — so the prior alias entry the summary "
            "depends on is dropped from the produced SQL exactly as in the "
            "drop-the-channel rival above, and the statement referring to it "
            "does not run. It resolves the referred-to-entry-survives scenario "
            "only for the shallowest possible expression shape and fails it for "
            "every nested one, so it resolves nothing in general."),
        "rationale": (
            "REJECT from clause 2 via the RECURSIVE arm of `referencedNames` "
            "(`.composite es => referencedNamesList es`): with the referred-to "
            "name nested inside a composite, the spec requires the added name "
            "TOGETHER WITH that name and the rival returns the added name alone. "
            "This is the only witness whose `expr` is a NON-EMPTY composite, so "
            "it is the only case that drives `referencedNames` past its base "
            "case and its empty-list case — the drop-reference-channel rival "
            "above is refuted at a bare `Expr.reference`, which this rival gets "
            "RIGHT, so the two share no witness. Without this case a spec that "
            "unfolded only the top level of the expression tree would pass the "
            "whole battery: SPEC-TOO-WEAK on the recursion itself. (Sibling: no "
            "counterpart — the sibling's `ref_tree` is a FLAT integer-coded "
            "list, so its collector has no recursive arm to under-implement; "
            "this carrier models the expression as a genuine tree and the "
            "battery must attack its depth.)"),
        "witness": _witness([_A("p", True, False, False)],
                            [_Add("c", _nested_ref("p"))],
                            group_by_tuple=True),
    },
    {
        "id": "weak-kept-retain-all-when-nested",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image skeleton of clause 2 (Solution_prepatch_2.lean): once
        # nested, retain EVERY visible prior entry — never prune the ones the
        # summary does not refer to. Correct on the non-nested arm and on the
        # duplicate-collapsing arm (where the spec agrees); diverges exactly on
        # the nested non-collapsing arm with an unreferred-to prior entry.
        "module": _flat(kept="if nesting then names ++ existing.map (·.name) else names"),
        "refinement": (
            "this is the pre-change retention rule: once the count is nested, "
            "every visible previously-declared alias entry survives into the "
            "produced SQL because the implementation is not selective about which "
            "to drop. Its faithful counterpart leaves an alias entry that the "
            "summary never refers to inside the emitted statement, which is "
            "exactly what the scenario asserting its ABSENCE forbids — the very "
            "waste the change is about. It resolves nothing."),
        "rationale": (
            "REJECT from clause 2 via the nested non-collapsing arm: the spec "
            "requires `maskFold added` (added names plus what they refer to, so an "
            "unreferred-to prior entry is DROPPED) and the rival appends every "
            "visible prior entry. Refuted with `distinct = false` and a prior "
            "entry nothing refers to — the sub-domain the retain-under-collapsing "
            "arm agrees with gold on, so it shares no witness with the "
            "prune-under-collapsing rival below; the trigger is `isSliced`, which "
            "no other witness drives, so that binder is load-bearing too. "
            "(Sibling: partial-domain-ick-keep-all.)"),
        "witness": _witness([_A("p", True, False, False)],
                            [_Add("c", _NO_REF)], is_sliced=True),
    },
    {
        "id": "weak-kept-prune-under-collapsing",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact mirror of the above: prune ALWAYS once nested, i.e. drop the
        # suppression of pruning when the query collapses duplicate rows. Correct
        # on the non-nested arm and on the whole nested non-collapsing arm;
        # diverges only when duplicate-row collapsing is in force. This is the
        # sub-domain where `distinct` is load-bearing for CLAUSE 2 specifically,
        # distinct from its role as a clause-1 trigger.
        "module": _flat(kept="if nesting then maskFold added else names"),
        "refinement": (
            "a faithful counterpart that narrowed the retained set even when the "
            "query collapses duplicate rows would change WHICH rows collapse: the "
            "set of retained alias entries is part of what makes two rows "
            "identical, so dropping entries merges rows that must stay distinct "
            "and the count comes out too small. It would resolve nothing on any "
            "duplicate-collapsing shape and would break counting behaviour the "
            "change preserves, while agreeing with the change everywhere else."),
        "rationale": (
            "REJECT from clause 2 via its `if distinct` arm: when the query "
            "collapses duplicate rows the spec requires every visible prior entry "
            "retained ALONGSIDE the added names, and the rival prunes to "
            "`maskFold added`. This is the witness that makes `distinct` "
            "load-bearing for CLAUSE 2 in particular — it is the sole binder "
            "distinguishing this point from the retain-all rival's, which sits at "
            "the same shape with `distinct = false` and the opposite verdict, so "
            "the two do NOT share a witness. Verifying would be SPEC-TOO-WEAK "
            "(the collapsing-suppression arm unpinned). (Sibling: no counterpart "
            "— the sibling's carrier has no duplicate-collapsing input, so this "
            "arm is unattackable there and must be attacked here.)"),
        "witness": _witness([_A("p", True, False, False)],
                            [_Add("c", _NO_REF)], distinct=True),
    },
    {
        "id": "weak-kept-collapsing-arm-all-declared",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). Clause 2's collapsing arm re-uses
        # `isExisting` to decide WHICH prior entries it retains, and no shipped
        # rival attacked that reuse: weak-nesting-all-declared drops the
        # visible-SELECT-set conjunct in clause ONE (and holds `distinct` false,
        # so it never reaches this arm), while every clause-2 rival keeps the arm
        # verbatim. So a rival that filters correctly for the nesting decision
        # but retains EVERY declared entry under duplicate-row collapsing passed
        # the whole shipped battery. Diverges on a declared-but-not-visible entry
        # with collapsing in force.
        "module": _flat(kept="if nesting then (if distinct then names ++ "
                             "annos.map (·.name) else maskFold added) else names"),
        "refinement": (
            "a faithful counterpart that retained every declared alias entry — "
            "rather than only those in the query's visible SELECT set — under "
            "duplicate-row collapsing would emit entries the query never "
            "selected into the produced SQL. Each one widens the tuple the "
            "collapsing compares, so rows that must merge stay distinct and the "
            "count comes out too large. It resolves nothing on any collapsing "
            "shape carrying a declared-but-unselected entry."),
        "rationale": (
            "REJECT from clause 2's collapsing arm via `isExisting`'s "
            "`a.selected` conjunct: with `distinct = true` and a single declared "
            "entry that is NOT in the visible SELECT set, the spec retains only "
            "the added name and the rival appends the unselected entry's name. "
            "This is the only case that drives `selected = false` THROUGH clause "
            "2 — weak-nesting-all-declared moves the same field in clause 1 and "
            "holds `distinct` false, so it never reaches this arm and does not "
            "refute this rival. Verifying would be SPEC-TOO-WEAK (the "
            "collapsing arm's own filter unpinned)."),
        "witness": _witness([_A("p", False, False, False)],
                            [_Add("c", _NO_REF)], distinct=True),
    },
    {
        "id": "weak-kept-collapsing-arm-counts-added",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). The other half of the same gap: keep the
        # visible-SELECT-set test in the collapsing arm but stop excluding the
        # names being ADDED, so the summary's own entry is retained twice. The
        # shipped weak-nesting-counts-added attacks this conjunct in clause ONE
        # only, at `distinct = false`, so it leaves this arm unprobed. Diverges
        # exactly on an added-name collision with collapsing in force.
        "module": _flat(kept="if nesting then (if distinct then names ++ "
                             "(annos.filter (fun a => a.selected)).map (·.name) "
                             "else maskFold added) else names"),
        "refinement": (
            "a faithful counterpart that failed to exclude the names being added "
            "for the summary would retain the summary's own alias entry a second "
            "time alongside itself under duplicate-row collapsing. The duplicate "
            "entry widens the tuple the collapsing compares, so the collapse no "
            "longer merges the rows it must and the count comes out too large — "
            "on exactly the shapes the scenarios assert a correct count for, so "
            "it resolves nothing."),
        "rationale": (
            "REJECT from clause 2's collapsing arm via `isExisting`'s "
            "`!(names.contains a.name)` conjunct: with `distinct = true` and the "
            "sole visible entry's name equal to the added name, the spec retains "
            "the added name ALONE and the rival retains it twice. This is the "
            "only case moving the name-collision axis through clause 2 — "
            "weak-nesting-counts-added moves it in clause 1 at `distinct = "
            "false`, agreeing with gold here. It also drives a non-trivial "
            "`expr` at `distinct = true`, which no other witness does. Verifying "
            "would be SPEC-TOO-WEAK."),
        "witness": _witness([_A("c", True, False, False)],
                            [_Add("c", _ref("p"))], distinct=True),
    },
    {
        "id": "weak-kept-mask-drops-own-name",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). `maskFold` contributes TWO things per added
        # entry — the entry's OWN name and the names it refers to — and the
        # shipped battery attacked only the second (drop-reference-channel,
        # shallow-reference-channel). A rival that keeps the reference channel
        # intact but drops each added entry's own name from the nested
        # non-collapsing arm therefore passed the whole shipped battery: it
        # agrees with gold on both other arms and on the reference channel
        # itself. This pins the `a.name ::` half of `maskFold_cons`.
        "module": _flat(kept="if nesting then (if distinct then names ++ "
                             "existing.map (·.name) else added.flatMap "
                             "(fun a => referencedNames a.expr)) else names"),
        "refinement": (
            "a faithful counterpart that widened the retained set by everything "
            "the additions refer to, but omitted the additions' OWN names, would "
            "drop the summary alias itself from the produced SQL. The outer "
            "query selects that alias, so it would resolve to nothing and the "
            "statement would not run at all — every counting scenario fails "
            "outright, so it resolves nothing."),
        "rationale": (
            "REJECT from clause 2 via `maskFold`'s `a.name ::` half: in the "
            "nested non-collapsing arm the spec requires each added name "
            "TOGETHER WITH the names it refers to, and the rival returns only "
            "the referred-to names. This is the only rival attacking the "
            "own-name half of the fold — the two reference-channel rivals both "
            "keep it and attack the other half, so neither refutes this one. "
            "Refuted with an added entry that refers to NOTHING, where the "
            "rival's retained set is empty and the spec's is `[\"c\"]`. "
            "Verifying would be SPEC-TOO-WEAK (half of `maskFold` unpinned)."),
        "witness": _witness([_A("p", True, False, False)],
                            [_Add("c", _NO_REF)], group_by_tuple=True),
    },
    {
        "id": "weak-kept-retain-all-when-flat",
        "kind": "uniqueness",
        "expect": "reject",
        # The third arm of clause 2, which no rival above touches: when NO
        # nesting happens, retain every visible prior entry instead of only the
        # added names. Correct on both nested arms; diverges exactly on the flat
        # arm with a visible prior entry present.
        "module": _flat(kept="if nesting then keptNames nesting distinct annos added "
                             "else names ++ existing.map (·.name)"),
        "refinement": (
            "a faithful counterpart that kept every visible previously-declared "
            "alias entry in the flat (un-nested) case would emit those entries in "
            "a statement whose whole purpose is to return one summary row. Each "
            "retained entry re-introduces the grouping that the flat form exists "
            "to avoid, so the statement returns one row per group instead of one "
            "summary row — the count comes back wrong (and the flat path is "
            "exactly the path the scenarios that assert a single un-nested "
            "statement take), so it resolves nothing."),
        "rationale": (
            "REJECT from clause 2 via its `else` (no-nesting) arm: with nesting "
            "false the spec requires the added names ALONE (prior entries are "
            "inlined away) and the rival appends every visible prior entry. This "
            "is the third arm of clause 2 and the only rival that attacks it — "
            "every other clause-2 rival agrees with gold here, so it shares no "
            "witness. Refuted at TWO visible prior entries, the only witness with "
            "`annos.length > 1`, so the spec's dependence on the whole list rather "
            "than on a single head element is demonstrated. Verifying would be "
            "SPEC-TOO-WEAK (the flat arm unpinned). (Sibling: no counterpart — "
            "the sibling models only the nested mask, so its carrier has no flat "
            "arm to attack.)"),
        "witness": _witness([_A("p", True, False, False), _A("q", True, False, False)],
                            [_Add("c", _NO_REF)]),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING
#
# The sibling battery ships 10 SPEC cases (2 soundness positives, 1
# admissibility, 7 uniqueness rivals — two of them MANDATORY frame-mutation
# rivals and two of them divergence rivals) plus 3 AXIOM_TESTS. It contracts TWO
# functions over integer-coded list carriers under fractional permissions; this
# bundle contracts ONE method whose two `ensures` clauses cover the SAME two
# decisions (the nesting predicate and the retained-name set) over structured
# carriers. So the two decisions map across intact, while the permission and
# termination machinery does not.
#
#   sibling case                        kind          -> here                             disposition
#   ------------------------------------------------------------------------------------------------
#   pos-control-esfd-accumulate         soundness     -> pos-control-direct-model         RE-SHAPED
#   pos-control-ick-accumulate          soundness     -> pos-control-named-contribution   RE-SHAPED
#                                                        (+ pos-control-forward-fold       ADDED BY AUDIT)
#   admiss-esfd-read-input              admissibility -> admiss-nondegenerate             RE-AIMED
#   partial-domain-esfd-presence-only   uniqueness    -> weak-nesting-presence-only       PORTED
#                                                        (+ weak-nesting-drop-window       SPLIT OUT)
#   partial-domain-esfd-source-all      uniqueness    -> weak-nesting-all-declared        PORTED
#                                                        (+ weak-nesting-counts-added      SPLIT OUT)
#   partial-domain-ick-keep-all         uniqueness    -> weak-kept-retain-all-when-nested PORTED
#   partial-domain-ick-drop-refs        uniqueness    -> weak-kept-drop-reference-channel PORTED
#                                                        (+ weak-kept-shallow-reference-channel SPLIT OUT)
#   support-esfd-inverted               uniqueness    -> weak-nesting-inverted            PORTED
#   fm-esfd-overwrite-selected          uniqueness    -> (none)                           VACUOUS (carrier)
#   fm-ick-overwrite-reftree            uniqueness    -> (none)                           VACUOUS (carrier)
#   weak-nonterm-esfd                   uniqueness    -> (none)                           SPEC-CLOSED
#   weak-nonterm-ick                    uniqueness    -> (none)                           SPEC-CLOSED
#   AXIOM_TESTS (3)                     axiom         -> (none)                           OUT OF LANE (G-AX)
#
# 5 uniqueness ported (3 of them additionally SPLIT because this carrier keeps a
# distinction the sibling's integer coding collapses), 9 uniqueness ADDED for
# surface the sibling does not model (3 shipped by the port, 6 ADDED BY AUDIT via
# attack D), 2 soundness re-shaped plus 1 ADDED BY AUDIT via attack E, 1
# admissibility re-aimed; 2 uniqueness vacuous by carrier, 2 rejected by the
# carrier but unshippable for a tooling reason, 3 axiom cases out of lane.
#
# ADDED BY AUDIT (attack D, 6 uniqueness). Each attacks surface every SHIPPED
#   rival left unprobed, and each was confirmed rejected by a real build with a
#   witness that elaborates against the rival and refutes semantically on a
#   verifying positive:
#     weak-nesting-drop-groupbytuple / -drop-sliced — the two plain structural
#       triggers the shipped battery drove true only as a means of REACHING the
#       nested arm for a clause-2 attack, never as the thing under attack;
#     weak-nesting-drop-distinct-trigger — `distinct` is load-bearing TWICE and
#       the port pinned only its clause-2 role;
#     weak-kept-collapsing-arm-all-declared / -counts-added — clause 2's
#       collapsing arm re-uses `isExisting`, and both of its conjuncts were
#       attacked in clause 1 only, at `distinct = false`, so neither reached
#       this arm;
#     weak-kept-mask-drops-own-name — `maskFold` contributes the added entry's
#       OWN name as well as its references, and the port attacked only the
#       reference half.
# ADDED BY AUDIT (attack E, 1 soundness). pos-control-forward-fold: both shipped
#   positives accumulate the fold BACKWARD (one keeps the frozen loop verbatim,
#   the other removes it), so a spec over-fit to the backward direction passed
#   both. The forward-fold reshape verifies (exit 0) with the linking step
#   re-proven by induction over `List.take`, so clause 2 is not over-fit to the
#   fold's direction.
#
# RE-SHAPED (the two positives). The sibling reshapes two per-element loop bodies
#   into boolean accumulates. This bundle has ONE loop (the retained-name fold),
#   so the two positives are re-aimed at the two ends of the reshape spectrum
#   instead: the loop-free closed form (maximally different control flow, proof
#   retuned to a bare `loom_solve`) and a minimal in-loop edit that keeps the
#   frozen invariants and the frozen proof script byte-for-byte. Together they
#   defend the obligation against a spec over-fit to the impl as a whole AND
#   against one over-fit to the loop body specifically.
# RE-AIMED (admiss-esfd-read-input -> admiss-nondegenerate). The sibling asserts
#   its half-permission Requires is establishable for a scenario-shaped input.
#   This method has NO `require` clause at all and no permission surface, so the
#   probe is degenerate; it is re-aimed at the sharper residual risk on an
#   unrestricted domain — a DEGENERATE post-image — via an in-region assert
#   pinning both clauses at scenario-shaped inputs (nesting on/off across the
#   summarising discriminator, and the two nested arms of the retained-name set
#   differing).
# SPLIT OUT (3 cases). The sibling's carrier codes each declared entry as two
#   ints, folding `contains_aggregate` and `contains_over_clause` into ONE `summ`
#   bit and `alias in annotation_select` plus `alias not in added` into ONE
#   `selected` bit. This carrier keeps all four as separate fields, so a rival
#   that mishandles only the windowed flag, or only the not-among-the-added
#   restriction, is expressible HERE and invisible there — hence
#   weak-nesting-drop-window and weak-nesting-counts-added. Carrier widening, the
#   mirror of the narrowing that drops cases elsewhere.
#   The third split is on DEPTH: the sibling's `ref_tree` is a FLAT
#   integer-coded list, so its `collect_refs` has no recursive arm, whereas this
#   carrier's `Expr` is a genuine tree and `referencedNames` recurses through
#   `.composite`. A rival collecting only TOP-LEVEL references is therefore
#   expressible here and invisible there — hence
#   weak-kept-shallow-reference-channel, added by AUDIT after the shipped
#   battery was found to hold `expr` at the base case (`Expr.reference _`) or
#   the empty composite in all eleven of its witnesses, leaving the recursion
#   itself unprobed.
# ADDED (3 cases) for surface with no sibling counterpart, all of it real spec
#   this battery would otherwise leave unattacked: weak-nesting-drop-combinator
#   (the sibling hard-wires the plain structural triggers out of its decision;
#   here they are explicit binders), weak-kept-prune-under-collapsing (the
#   sibling has no duplicate-row-collapsing input, so clause 2's third arm does
#   not exist there), and weak-kept-retain-all-when-flat (the sibling models only
#   the nested mask, so it has no flat arm).
# VACUOUS BY CARRIER (fm-esfd-overwrite-selected, fm-ick-overwrite-reftree). Both
#   are MANDATORY in the sibling because its list inputs are held at a fractional
#   heap permission `Acc(...,1/2)`: a rival can write to the carrier it was handed
#   (zeroing the visible-SELECT bits, or injecting the alias into every reference
#   tree) to satisfy the postcondition without observing the real input, and the
#   permission system rejects it. Lean/Velvet are referentially transparent:
#   `annos` and `added` are immutable values declared read-only (not `mut`), there
#   is no heap, no aliasing, no `Old` and no permission system, so there is no
#   read-only input to overwrite and no frame clause to violate. The class has no
#   carrier analogue and NOTHING was fabricated in its place — a substitute would
#   test the substitute, not the frame guarantee.
# REJECTED BY THE CARRIER, UNSHIPPABLE FOR A TOOLING REASON (weak-nonterm-esfd,
#   weak-nonterm-ick). CORRECTED BY AUDIT. The shipped battery recorded this class
#   as a KNOWN SPEC HOLE, asserting that "this bundle carries
#   `set_option loom.semantics.termination "total"`, under which the postcondition
#   is claimed only of TERMINATING runs". That reads the option BACKWARDS: under
#   `total` the verifier discharges a termination obligation, and it is `partial`
#   that admits a diverging impl vacuously. The prose named the right option value
#   and attached the wrong consequence to it, so a real rejection was documented
#   as a spec hole.
#
#   Re-measured against the real verifier during the audit, four diverging shapes,
#   all REJECTED (exit 1):
#     * `while true do pure ()` spliced at the head of the frozen body, proof
#       reduced to a bare `loom_solve` (the canonical corpus probe shape)
#       -> `error: Decreasing annotations are required in total correctness
#       semantics`;
#     * the same prefix returning the unambiguously WRONG plan
#       `{needsNesting := false, keptNames := []}` -> the identical error;
#     * a spin carrying a CONSTANT `decreasing j` measure -> rejected, the measure
#       obligation is not satisfiable;
#     * a `while true ... done_with False` spin -> rejected.
#   So the frozen spec does NOT admit a diverging rival. There is no `partial`
#   cohort to sit outside of either: all 500 velvet bundles set `"total"`, and the
#   `set_option` elaborator itself runs `openScope `TotalCorrectness`
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so the option and the `open`
#   cannot disagree.
#
#   The class is nonetheless NOT shippable as a reject case here, and the reason is
#   TOOLING rather than the spec. A reject case needs a witness that ELABORATES
#   against the rival, and the diverging rival does not compile at all: the
#   `Decreasing annotations are required` error fires inside the impl region, so
#   the witness file built on that rival fails for that error rather than for its
#   own claim. Measured, both diverging shapes, witness-against-rival exit 1 with
#   `Decreasing annotations are required in total correctness semantics` as the
#   first error — which the gate correctly reads as `witness-unproven`, an
#   INCONCLUSIVE outcome that would make the whole battery MALFORMED-TESTS. A
#   rival the carrier refuses to elaborate cannot be witnessed, so the disposition
#   is "rejected by the carrier, unshippable", which is neither a hole (the spec
#   is strong here) nor vacuous (the class exists and the carrier answers it).
#   Corpus check: no `total` velvet cell ships a divergence reject case, for this
#   reason.
# OUT OF LANE (AXIOM_TESTS). The sibling ships 3 axiom probes for its
#   `collect_refs` deep model. This bundle's counterpart deep model is
#   `referencedNames`, likewise NOT a consumed axiom (mapping.md §3.1: the
#   `axioms` region is empty), and validating it against the real callee is
#   G-AX's job via `axiom_check.py`. This gate ignores AXIOM_TESTS, so the lane
#   is left empty rather than duplicated.
#
# ---------------------------------------------------------------------------
# OBLIGATION / CLAUSE / BINDER COVERAGE (what the gate does NOT check)
#
# The single obligation `prove_correct countQueryShape` is DEFENDED by 4
# expect="verify" cases and ATTACKED by 18 expect="reject" rivals.
#
# CLAUSES. Both top-level `ensures` are attacked, and every independent
# sub-structure within them:
#   clause 1 (needsNesting) — the compound prior-entry disjunct on all four of
#     its axes (presence-only; the windowed half; the visible-SELECT-set filter;
#     the not-among-the-added filter), the filter channel, ALL FOUR plain
#     structural triggers separately (`combinator`, and — ADDED BY AUDIT —
#     `groupByTuple`, `isSliced`, and `distinct` in its clause-1 role), and the
#     polarity of the whole clause: 10 rivals.
#   clause 2 (keptNames) — all THREE arms (flat / nested-non-collapsing /
#     nested-collapsing), BOTH halves of `maskFold`'s per-entry contribution (the
#     entry's OWN name — ADDED BY AUDIT — and the reference channel), BOTH arms of
#     that reference channel (the base case `.reference` and the RECURSION through
#     `.composite`), and BOTH conjuncts of the `isExisting` filter as re-used
#     inside the collapsing arm (ADDED BY AUDIT): 8 rivals.
#
# BINDERS. Eighteen distinct witness input points (no two reject cases share an
# input), and every input binder is MOVED by some witness while the rest are held:
#   annos            — [] (drop-filter, drop-combinator, drop-groupbytuple,
#                      drop-sliced, drop-distinct-trigger), one entry (12 rivals),
#                      two entries (retain-all-when-flat)
#   .selected        — true (most) / false (all-declared in clause 1,
#                      collapsing-arm-all-declared in clause 2)
#   .isAggregate     — false (most) / true (all-declared, counts-added, inverted)
#   .isWindow        — false (most) / true (drop-window)
#   .name            — distinct from the added name (most) / COLLIDING with it
#                      (counts-added in clause 1,
#                      collapsing-arm-counts-added in clause 2)
#   added[].expr     — refers to nothing, `Expr.composite []` (most) / refers to
#                      a prior entry DIRECTLY, `Expr.reference`
#                      (drop-reference-channel, collapsing-arm-counts-added) /
#                      refers to one through a NESTED composite
#                      (shallow-reference-channel). The three values
#                      hit the three distinct arms of `referencedNames`: the
#                      empty list, the base case, and the recursion. Two
#                      spellings of "refers to nothing" would move the binder
#                      without moving the spec's verdict; these do not.
#   groupByTuple     — true (drop-reference-channel, shallow-reference-channel,
#                      mask-drops-own-name, and — as the thing under attack —
#                      drop-groupbytuple) / false (rest)
#   isSliced         — true (retain-all-when-nested, drop-sliced) / false (rest)
#   distinct         — true (prune-under-collapsing, drop-distinct-trigger,
#                      collapsing-arm-all-declared, collapsing-arm-counts-added)
#                      / false (rest)
#   combinator       — true (drop-combinator) / false (rest)
#   havingFilter     — true (drop-filter) / false (rest)
# Each of the five booleans is now attacked AS A CLAUSE-1 TRIGGER IN ITS OWN
# RIGHT, at `annos = []` with every other trigger off, by exactly one rival —
# the shape that proves it load-bearing, since a rival mishandling only that
# binder is caught by that case alone. The shipped battery had this property for
# `combinator` and `havingFilter` only: `groupByTuple`, `isSliced` and `distinct`
# were driven true solely to REACH a nested arm for a clause-2 attack, where the
# rival agrees with gold on clause 1 and therefore does not pin the trigger.
# Closed by the three audit-added `weak-nesting-drop-*` rivals. `added` is held at a
# single entry throughout: the retained-name fold is defined element-wise
# (`maskFold` prepends one contribution per entry) and the loop is defended by
# the two positives over the WHOLE domain, so no rival is refutable only at
# `added.length > 1`; the list dimension of `annos`, which the branch structure
# does depend on, IS moved (0 / 1 / 2 entries).
#
# ---------------------------------------------------------------------------
# AUDIT NOTE — THE RETAINED-NAME CLAUSE IS ORDER- AND DUPLICATE-SENSITIVE
#
# `res.keptNames` is a `List String` compared with `=`, i.e. as a LIST. The
# consumer view it abstracts is a name SET (mapping.md §2 records the carrier as
# order-/dup-insensitive and says the comparison is by membership). Clause 2 is
# therefore STRICTER than the behaviour it models, and two faithful impls are
# rejected for a reason that is not a behavioural difference. Both were measured
# against the real verifier during the audit, and neither is shipped as a case,
# because a `soundness` case must VERIFY and these do not:
#
#   * a permuted-but-set-equal retained list in the duplicate-collapsing arm
#     (`existing.map (·.name) ++ names` instead of `names ++ existing.map …`)
#     leaves the goal `xs ++ ys = ys ++ xs`, which is false as a list equality
#     and unprovable;
#   * a DE-DUPLICATED mask (`(maskFold added).eraseDups`) — which is what the
#     real code produces, since it accumulates into a set — is likewise
#     rejected: with two added entries referring to the SAME prior name the
#     spec's demanded list carries that name TWICE, and no set-valued impl can
#     produce a repeated element.
#
# This is a property of the FROZEN spec, so it is recorded here rather than
# patched: tightening the clause to set equality edits `Solution.lean` and must
# re-clear the equivalence, differential, conformance and panel gates, which is
# outside this lane. It is NOT a `spec_holes` entry in the audit sense — it makes
# the spec too STRONG, never admitting a wrong impl — and it does not weaken any
# case above: every rival here diverges from the spec in MEMBERSHIP at its
# witness point, not merely in order or multiplicity, so each rejection would
# stand under set semantics too. Escalated for the spec lane to decide, with the
# concrete inputs above as the evidence.
AXIOM_TESTS = []

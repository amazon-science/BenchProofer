"""properties.py — G-PBT falsification battery for pydata__xarray-7229 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_where``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function; three labelled-object inputs plus a
retention flag):

  where (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj
      result = expectedResult cond a b keep_attrs produces

  A labelled object carries a top-level attribute bag, an optional own name, a
  container flag, and two lists of named components (data variables and
  coordinates), each with its own attribute bag. The combined data/structure is
  produced by an opaque combination routine `select_combine cond a b keep_attrs`; this
  spec pins ONLY how the result components' attribute bags are populated. The
  postcondition folds several inseparable sub-decisions, each tied to a binder:

    * WHETHER A COMBINED OBJECT IS YIELDED AT ALL — governed by `produces`, the
      observation of this same call that says whether the per-component
      consultations the rebuild needs can be carried out. When it is false the
      outcome is `none`; the two arms are attacked by their own rivals below.
    * WHETHER attributes are rebuilt at all — governed by `keep_attrs`. When it
      is false the combined object is returned verbatim.
    * WHICH SHAPE — the container-promotion special case fires exactly when `b`
      is a container and `a` is not (`b.isContainer && !a.isContainer`), driven
      by the two objects' container flags.
    * WHERE each attribute bag COMES FROM — the essential guarantee: a result
      component's attributes are what resolving the component's own NAME against
      `a` yields (`lookupAttrs a nm`); the top-level bag is placed at top level
      (or emptied on promotion, with the promoted data variable receiving `a`'s
      top-level bag).
    * HOW a name RESOLVES against `a` — a staged lookup: `a`'s own kind answers
      first for a name it RESERVES (yielding whatever bag that answer carries —
      `a`'s top-level bag when the answer is a view of the whole object, the
      empty bag otherwise), an unreserved name is sought among `a`'s components
      (data variables then coordinates), and a name that is neither yields the
      empty bag. Each stage, and each outcome of the reserved stage, is attacked
      by its own rival below.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because its modeled source collections are held
    at fractional (read-only) permission and a rival that overwrites one is
    rejected for insufficient permission. Lean is referentially transparent: the
    inputs are plain immutable values, there is no half-permission to violate
    and no aliasing to exploit, so this class has NO expressible instance here.
    No substitute is fabricated (mapping.md: the impl reads only component names
    and rewrites the freshly-built result's bags; the inputs cannot be mutated).
    Demonstrated rather than asserted, since "the carrier collapses this" is a
    reason that has to be shown: the nearest value-level shadow of a source
    write IS expressible — rebuild from a locally CORRUPTED copy of `a`
    (`let a' := { a with coords := a.coords.map (fun c => { c with attrs := [] }) }`,
    then resolve every name against `a'`) — and it is REJECTED (measured: exit 1,
    `Tactic \`rfl\` failed`). But that rival is a value error in the rebuild's
    SOURCE, which the coord/var-broadcast rivals below already cover as a class;
    it is not a frame violation, because the corruption is a fresh local value
    and `a` itself is unreachable for writing. So the nagini case's actual
    content — "the rejection is for insufficient PERMISSION, not for a value
    mismatch" — has no analogue: every rejection on this carrier is a value
    mismatch. That is the demonstration, and it is why nothing is ported.

  * DIVERGENCE / NON-TERMINATION — EXPRESSIBLE as an impl but NOT SHIPPABLE as a
    reject case here, which is a narrower claim than "cannot be written" and is
    the one that was actually measured. The frozen solution sets no
    `loom.semantics.termination` option at all (that option is velvet's; no lean
    bundle in this corpus carries one), so the carrier is the total one: a
    non-terminating `implementation_where` cannot be a plain Lean `def`, because
    the elaborator demands a decreasing measure — a bare self-call variant is
    rejected with `fail to show termination for implementation_where`,
    `failed to infer structural recursion`. It CAN be written with `partial`,
    and such a variant does stay inside `variant_scope` (measured:
    `variant_problems == []`) and does fail to verify. What blocks it is the
    witness half, not the impl half, and that was measured on both available
    shapes rather than argued:
      - `partial def implementation_where := implementation_where …` — the
        witness build fails against the RIVAL itself with `Tactic \`unfold\`
        failed to unfold \`implementation_where\``, because a `partial` def has
        no equation to unfold. A witness that does not hold of the rival is
        `witness-unproven`, i.e. an INCONCLUSIVE case, which forces
        MALFORMED-TESTS rather than a pass.
      - a `partial` helper consumed by an otherwise-gold rebuild
        (`partial def spin (n : Nat) : Attrs := spin (n + 1)`, written into the
        coordinate bag) — the same witness reaches `decide` and gets stuck:
        `reduction got stuck at the Decidable instance List.hasDecEq (spin 0) …
        did not reduce to \`isTrue\` or \`isFalse\``. That is precisely the
        `witness-undecided` screen, and it is stuck for EVERY claim regardless
        of truth, so its exit code would attest to a refutation the kernel never
        performed.
    So the disposition is a KNOWN LIMIT of the witness lane on an irreducible
    term, not a vacuous class and not a spec hole: the frozen obligation does
    reject every diverging impl the carrier admits (both variants above are
    exit 1), and there is simply no witness that can attribute that rejection to
    the spec. No case is fabricated for it, because a case whose witness cannot
    hold of its own rival fails this gate rather than strengthening it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition equals a TOTAL function
    (`expectedResult`) built structurally from the inputs and the opaque
    combination; there is no axiomatized answer key an impl could echo. In
    particular the optional-outcome arm is driven by the `produces` BINDER, not
    by an axiom about the inputs, so an impl cannot discharge it by appealing to
    an ungrounded oracle — it must branch on the binder, and the two rivals
    weak-no-object-arm-ignored / weak-no-object-arm-overreach reject the impls
    that collapse that branch to a constant in either direction. The honest
    analogue is the cheapest-correct POSITIVE CONTROL below.

  * VALUE / DOUBLE-MASK, PARTIAL-DOMAIN, and REGIME rivals — APPLY, and are the
    load-bearing lane. The pre-patch bug broadcast `a`'s single top-level bag
    onto every rebuilt component (coordinates included) instead of copying each
    component's like-named bag; the promotion regime independently mishandled
    the emptied top-level bag and the promoted data variable. Each rival below
    isolates one such sub-decision and is refuted at the sub-domain where it
    diverges from gold.

WITNESSES over an OPAQUE carrier. `select_combine` is `opaque`, so no literal
input decides the goal by computation — `decide` would stick on the opaque
term. Each reject witness therefore CONDITIONS on the carrier: it fixes the
three objects and the flag to concrete literals and assumes ONE hypothesis
`h : select_combine <lit> <lit> <lit> <flag> = <lit>` naming the combined object's
structure. Under that single hypothesis the goal reduces to a decidable
comparison of two concrete `XObj`s. The claim each witness makes is: *for a
combined object of this shape, the rival's rebuilt attributes differ from what
the spec requires* — a statement true of the rival and false of gold. Each was
built against BOTH files: it ELABORATES against the rival and FAILS on the
frozen solution (a real discriminator, not a tautology). One hypothesis per
witness about a single opaque application, so the assumptions are trivially
jointly satisfiable (no `witness-inconsistent` risk).

Every witness closes by `decide`, and that is load-bearing rather than
stylistic. A gold-side failure is admissible evidence only if it CHANGES when
the claim changes, and a witness left to `simp` does not have that property
here: `simp` cannot finish the concrete `Option XObj` comparison either way, so
it stops with `unsolved goals` on the frozen solution for the refutation AND for
the flipped claim alike, and gold's exit code then carries no information about
what was asserted. Two of the optional-outcome witnesses were closed that way
and have been rewritten to unfold `rebuildFrom`/`lookupAttrs` and `decide`
instead; the flipped-claim control now builds (exit 0) against the frozen
solution while the refutation fails on it with `decide` reporting the
proposition `is false`, so each of those exit codes tracks its claim. Any future
edit to a witness's closer must preserve that: a witness whose gold-side error
is byte-identical under a flipped claim proves nothing, however honest its
recorded outcome looks.

BINDER COVERAGE. (`result` is the output.) `cond` never influences the modeled attribute rebuild
(the impl reads only `select_combine`'s output structure and `a`'s components),
so it is held fixed by design — see 'assessment'. The frozen spec binds
`cond`, `a`, `b`, `keep_attrs`, `produces`. The reject witnesses vary:
  * `produces` — `false` (the no-object-arm-ignored rival, whose witness is
    decided with no hypothesis about the combination routine) AND `true` (all
    others), so BOTH arms of the optional outcome are exercised and neither is
    pinned.
  * `keep_attrs` — `false` (ignore-flag rival) AND `true` (all others), so the
    retention gate is exercised, not pinned.
  * `b.isContainer` — `false` (non-promotion rivals) AND `true` (promotion
    rivals), and `a.isContainer` is held `false` so the two container flags
    jointly select each regime.
  * `a` — varied across shapes: a coordinate-bearing `a`, a data-variable-
    bearing `a`, and a bare-named `a` for the promotion rivals.
  * component-list LENGTH — one component (the wholesale rivals) AND two (the
    two partial-domain head-skip rivals), so the rebuild's universally-
    quantified reach over a multi-component list is exercised and not just its
    behavior at a singleton.
Every top-level regime of the postcondition (no object yielded; keep=false;
non-promotion rebuild; promotion rebuild) is attacked by at least one reject
case, and within the two rebuild regimes every WRITE the spec prescribes is
attacked by a rival that breaks that write and nothing else. The last of those
to be closed was the ordinary regime's own top-level write
(`topAttrs := a.topAttrs`): the promotion rival attacks the mirror clause
(`topAttrs := []`) and the ignore-flag rival reaches the non-promotion write only
at keep_attrs = FALSE, where the spec's demand is the opposite one, so
weak-nonpromo-top-dropped is what pins it at keep_attrs = true. Its witness sets
every component list EMPTY, so the top-level bag is the only thing its comparison
can turn on.

The SOUNDNESS lane likewise carries two positives rather than one, because a
single reshape that the FROZEN tactic body still closes unchanged demonstrates
only that the spec admits impls definitionally equal to gold's.
`pos-reorder-field-updates` is of that kind by construction (its three record
updates are on disjoint fields, so they commute definitionally).
`pos-recursive-rebuild` is not: it replaces `List.map` with a structurally
recursive helper, so the rebuilt lists are only PROVABLY equal to the spec's
`comps.map (...)` and the variant must supply the bridging induction itself. That
is the probe that actually tests SPEC-TOO-STRONG — whether the spec admits a
faithful correct impl whose rebuild does not reduce to the spec's own term.

The ADMISSIBILITY lane carries two ground instances rather than one, for the
same reason the reject lane carries both regimes: a single instance fires one
arm of the shape decision and leaves the other arm's clauses vacuous, so
satisfiability would be demonstrated on half the surface and assumed on the
other half. `admiss-f2p-dataarray-coord` discharges the obligation in the
non-promotion regime and `admiss-f2p-promotion-shape` in the promotion regime
(where the emptied top-level bag and the promoted data variable's bag are the
clauses that only exist).

PARTIAL-DOMAIN coverage. The broadcast/leak/drop rivals are each wrong on the
WHOLE of their regime, so each is refutable at a single-component carrier and
none of them tests that the rebuild reaches EVERY element of a component list.
The two head-skip rivals close that: they are correct on the tail of the list
and wrong only at its head, so their witnesses are decided by a component the
rival gets wrong while an adjacent one it gets right sits beside it in the same
list. (This is the class the nagini sibling carries as its coord/var
first-slot-empty pair; it is expressible here and is ported, not dropped.)
The two resolution-order rivals are the same class in the NAME domain rather
than the list domain: `weak-reserved-skipped` is correct on every name `a` does
not reserve and wrong only on the reserved ones, and `weak-reserved-collapsed`
is correct on the reserved names whose answer is a whole-object view and wrong
on the (majority) reserved names whose answer carries no bag. Their witnesses
put a reserved name and a like-named component on the SAME object, so the stage
order — not the presence of a component — decides the comparison.

AXIOM lane: EMPTY. meta.json declares the combination routine as an A-reference
deep-model (validated == the real callee by G-AX), not a consumed `_prop`
axiom; the proof consumes no axiom. So there is no in-model axiom obligation for
this gate to re-discharge. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-7229"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors — the FULL impl def and the FULL correct_where tactic body, so
# every replacement lands entirely inside the region it means to edit and the
# manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------
_IMPL_GOLD = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

_TACTIC_BODY = (
    "  intro cond a b keep_attrs produces\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  cases produces with\n"
    "  | false =>\n"
    "    cases keep_attrs with\n"
    "    | false => rfl\n"
    "    | true =>\n"
    "      by_cases h1 : b.isContainer && !a.isContainer\n"
    "      · simp only [Id.run, h1, if_true]\n"
    "        cases a.name with\n"
    "        | none => rfl\n"
    "        | some nm => rfl\n"
    "      · simp only [Id.run, h1]\n"
    "        rfl\n"
    "  | true =>\n"
    "    cases keep_attrs with\n"
    "    | false => rfl\n"
    "    | true =>\n"
    "      by_cases h1 : b.isContainer && !a.isContainer\n"
    "      · simp only [Id.run, h1, if_true, rebuildFrom]\n"
    "        cases a.name with\n"
    "        | none => rfl\n"
    "        | some nm => rfl\n"
    "      · simp only [Id.run, h1, rebuildFrom]\n"
    "        rfl"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_TACTIC_BODY) == 1, "proof region drifted; update _TACTIC_BODY"


def _impl(body):
    """A full Solution.lean variant with the gold impl body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — a structurally-different but CORRECT impl. The
# three record-field updates (topAttrs / dataVars / coords) are on DISJOINT
# fields, so reordering them yields the byte-identical value in every regime.
# The frozen tactic script still closes the reordered shape (the field updates
# commute definitionally), so the obligation is re-proved with the frozen proof
# body — no new lemma, axiom, or assumption token, statement byte-identical.
# ---------------------------------------------------------------------------
_POS_REORDER = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with topAttrs := [] }\n"
    "    else\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)


# ---------------------------------------------------------------------------
# SECOND POSITIVE CONTROL (soundness) — a reshape that changes the rebuild's
# CONTROL STRUCTURE rather than a statement order. `_POS_REORDER` above permutes
# three record updates that commute definitionally, so the frozen tactic body
# closes it unchanged; that is honest but weak as a SPEC-TOO-STRONG probe,
# because a permutation of definitionally-commuting writes is nearly the
# smallest reshape there is. This one replaces `List.map` with a STRUCTURALLY
# RECURSIVE helper over the component list, so the rebuilt lists are no longer
# the same TERM as the spec's `comps.map (...)` — they are only provably equal,
# by an induction the variant's own proof supplies. That makes it the reshape
# that actually exercises "any faithful correct impl is admitted", since the
# frozen `rfl`-shaped script provably cannot close it: the bridging lemma is
# needed. Statement byte-identical; the helper is an impl-region `def` (which
# `variant_scope` permits) and the bridge is a `have` inside the proof region,
# so no new top-level theorem, axiom, or `sorry`.
# ---------------------------------------------------------------------------
_POS_RECURSIVE = (
    "def rebuildEach (a : XObj) : List Component → List Component\n"
    "  | [] => []\n"
    "  | c :: rest => { c with attrs := lookupAttrs a c.name } :: rebuildEach a rest\n"
    "\n"
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := rebuildEach a result.coords }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := rebuildEach a result.dataVars }\n"
    "      result := { result with\n"
    "        coords := rebuildEach a result.coords }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

_POS_RECURSIVE_PROOF = (
    "  have hre : ∀ (a : XObj) (l : List Component),\n"
    "      rebuildEach a l = l.map (fun c => { c with attrs := lookupAttrs a c.name }) := by\n"
    "    intro a l\n"
    "    induction l with\n"
    "    | nil => rfl\n"
    "    | cons c rest ih => simp only [rebuildEach, List.map_cons, ih]\n"
    "  intro cond a b keep_attrs produces\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  cases produces <;> cases keep_attrs <;>\n"
    "    by_cases h1 : b.isContainer && !a.isContainer <;>\n"
    "    simp only [Id.run, h1, if_true, if_false, rebuildFrom, hre] <;>\n"
    "    first\n"
    "      | rfl\n"
    "      | (cases a.name <;> rfl)\n"
    "      | (cases hn : a.name <;> simp only [hn] <;> rfl)"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (verify) — confirm the obligation is SATISFIABLE (non-vacuous)
# at the normal, F2P-shaped input rather than only provable in the abstract. The
# frozen theorem carries NO precondition hypothesis (the behavior is total), so
# nagini's precondition-admission probe has no binder to attack; the honest
# analogue is to discharge the spec predicate at the F2P ground input (the
# 3-object DataArray scenario with a coordinate 'a' bearing its own attrs)
# inside the proof region, alongside the frozen obligation. If that ground
# instance could not be discharged, the modeled behavior would be unsatisfiable
# at exactly the input the F2P exercises (the analogue of PRECOND-TOO-STRONG).
# ---------------------------------------------------------------------------
_ADMISS_HAVE = (
    "  have _ground :\n"
    "      problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"attr\",\"x_da\")], some \"x\", false, [], [⟨\"a\", [(\"attr\",\"x_coord\")]⟩], []⟩\n"
    "        ⟨[], none, false, [], [⟨\"a\", []⟩], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"attr\",\"x_da\")], some \"x\", false, [], [⟨\"a\", [(\"attr\",\"x_coord\")]⟩], []⟩\n"
    "          ⟨[], none, false, [], [⟨\"a\", []⟩], []⟩\n"
    "          true true) := by\n"
    "    unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "    rfl\n"
)


# ADMISSIBILITY, second shape — the PROMOTION regime. The ground instance above
# fires the NON-promotion arm, so it leaves the promotion branch's own clauses
# (the emptied top-level bag, and the promoted data variable receiving `a`'s
# top-level bag) untouched: satisfiability is demonstrated for one arm of the
# shape decision and merely assumed for the other. This second instance
# discharges the obligation with the container flags selecting promotion — `a` a
# named non-container carrying its own top-level bag and a coordinate, `b` a
# container — so BOTH arms are shown satisfiable at an F2P-shaped input. (This is
# the second admissibility case the nagini sibling carries as
# admiss-f2p-shaped-input-unmatched, whose point is exactly that the first
# probe leaves the regime-dependent clauses vacuous.)
_ADMISS_PROMO_HAVE = (
    "  have _ground_promo :\n"
    "      problem_spec_where\n"
    "        ⟨[], none, false, [], [⟨\"a\", [(\"attr\",\"cond_coord\")]⟩], []⟩\n"
    "        ⟨[(\"attr\",\"x_da\")], some \"x\", false, [], [⟨\"a\", [(\"attr\",\"x_coord\")]⟩], []⟩\n"
    "        ⟨[(\"attr\",\"y_ds\")], none, true, [⟨\"x\", [(\"attr\",\"y_da\")]⟩],"
    " [⟨\"a\", [(\"attr\",\"y_coord\")]⟩], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [⟨\"a\", [(\"attr\",\"cond_coord\")]⟩], []⟩\n"
    "          ⟨[(\"attr\",\"x_da\")], some \"x\", false, [], [⟨\"a\", [(\"attr\",\"x_coord\")]⟩], []⟩\n"
    "          ⟨[(\"attr\",\"y_ds\")], none, true, [⟨\"x\", [(\"attr\",\"y_da\")]⟩],"
    " [⟨\"a\", [(\"attr\",\"y_coord\")]⟩], []⟩\n"
    "          true true) := by\n"
    "    unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "    rfl\n"
)


# ---------------------------------------------------------------------------
# UNIQUENESS rivals (expect="reject"). Each is a full impl def with ONE
# sub-decision broken; the spec and the theorem STATEMENT stay byte-identical.
# ---------------------------------------------------------------------------

# COORD-BROADCAST — the headline bug: in the ordinary (non-promotion) regime the
# rebuilt coordinate bags are set to `a`'s single top-level bag instead of the
# like-named component's bag.
_COORD_BROADCAST = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := a.topAttrs }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

# VAR-BROADCAST — ordinary regime, data-variable bags set to `a`'s top-level bag
# instead of the like-named component's bag.
_VAR_BROADCAST = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := a.topAttrs }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

# PROMO-TOP-LEAK — promotion regime leaves the result's top-level bag as `a`'s
# top-level bag instead of emptying it.
_PROMO_TOP_LEAK = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

# PROMO-SLOT-DROP — promotion regime writes the like-named component's bag
# (`lookupAttrs a nm`) to the promoted data variable instead of `a`'s top-level
# bag, so a promoted object with no like-named component loses its attributes.
_PROMO_SLOT_DROP = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := lookupAttrs a c.name } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

# NONPROMO-TOP-DROPPED — the ORDINARY regime's top-level clause, which no other
# rival attacks: every component bag is rebuilt exactly as the spec demands, but
# the result's own top-level bag is left as the combination routine produced it
# instead of being taken from `a`. The mirror of the promotion rival above (which
# leaves `a`'s bag where the spec demands EMPTY); this one leaves the carrier's
# bag where the spec demands `a`'s. Without it the whole non-promotion top-level
# write was pinned only indirectly, by the ignore-flag rival at keep_attrs=false.
_NONPROMO_TOP_DROPPED = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

# IGNORE-FLAG — rebuild attributes unconditionally, ignoring `keep_attrs`, so
# the combined object is NOT returned verbatim when retention is off.
_IGNORE_FLAG = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if true then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

# COORD-HEAD-SKIP — PARTIAL-DOMAIN in the coordinate carrier. Every coordinate
# but the FIRST is rebuilt from its like-named component of `a`; the head
# coordinate keeps whatever bag the combination routine gave it. Correct on the
# whole tail of the coordinate list, wrong at the head — the near-miss shape a
# rival that broadcasts wholesale cannot express.
_COORD_HEAD_SKIP = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        coords := (match result.coords with\n"
    "                   | [] => []\n"
    "                   | c :: rest => c :: rest.map (fun d => { d with attrs := lookupAttrs a d.name })) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

# VAR-HEAD-SKIP — the PARTIAL-DOMAIN counterpart in the data-variable carrier:
# every data variable but the FIRST is rebuilt from its like-named component of
# `a`; the head variable keeps the combination routine's bag.
_VAR_HEAD_SKIP = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := (match result.dataVars with\n"
    "                     | [] => []\n"
    "                     | c :: rest => c :: rest.map (fun d => { d with attrs := lookupAttrs a d.name })) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)


# ---------------------------------------------------------------------------
# Witnesses (see module docstring). Each conditions on ONE opaque application of
# the combination routine and states the spec predicate at a fully concrete
# input, so the goal reduces to a decidable XObj comparison.
# ---------------------------------------------------------------------------
_W_COORD_BROADCAST = (
    "-- Non-promotion regime with a coordinate 'c' bearing its own bag [(\"k\",\"cv\")].\n"
    "-- The spec keeps that per-coordinate bag; broadcasting `a`'s top-level bag\n"
    "-- [(\"t\",\"A\")] onto the coordinate instead is refuted here.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[(\"z\",\"zz\")], none, false, [], [⟨\"c\", []⟩], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], []⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  simp only [h]\n"
    "  decide\n"
)

_W_VAR_BROADCAST = (
    "-- Non-promotion regime with a data variable 'd' bearing its own bag\n"
    "-- [(\"k\",\"dv\")]. The spec keeps that per-variable bag; broadcasting `a`'s\n"
    "-- top-level bag onto the data variable instead is refuted here.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [⟨\"d\", [(\"k\",\"dv\")]⟩], [], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[(\"z\",\"zz\")], none, false, [⟨\"d\", []⟩], [], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [⟨\"d\", [(\"k\",\"dv\")]⟩], [], []⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [⟨\"d\", [(\"k\",\"dv\")]⟩], [], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  simp only [h]\n"
    "  decide\n"
)

_W_PROMO_TOP_LEAK = (
    "-- Promotion regime (b container, a not): the spec empties the result's\n"
    "-- top-level bag. A combined object whose top-level bag is [(\"z\",\"zz\")]\n"
    "-- must be emptied; leaving `a`'s top-level bag [(\"t\",\"A\")] there is refuted.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "          ⟨[], none, true, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[(\"z\",\"zz\")], none, true, [], [], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "        ⟨[], none, true, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "          ⟨[], none, true, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  simp only [h]\n"
    "  decide\n"
)

_W_PROMO_SLOT_DROP = (
    "-- Promotion regime: the promoted data variable (named 'x', matching `a`'s\n"
    "-- own name) must receive `a`'s top-level bag [(\"t\",\"A\")]. `a` has no\n"
    "-- like-named component, so drawing the bag from a same-name lookup yields []\n"
    "-- and drops the promoted variable's attributes — refuted here.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "          ⟨[], none, true, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[], none, true, [⟨\"x\", []⟩], [], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "        ⟨[], none, true, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "          ⟨[], none, true, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult lookupAttrs\n"
    "  simp only [h]\n"
    "  decide\n"
)

_W_NONPROMO_TOP_DROPPED = (
    "-- Non-promotion regime (b NOT a container): the spec places `a`'s top-level\n"
    "-- bag [(\"t\",\"A\")] at the result's top level. A combined object carrying\n"
    "-- [(\"z\",\"zz\")] there must have it replaced; leaving the combination\n"
    "-- routine's own bag in place is refuted here. Every component list is empty,\n"
    "-- so the top-level clause is the ONLY thing this comparison can turn on.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[(\"z\",\"zz\")], none, false, [], [], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  simp only [h]\n"
    "  decide\n"
)

_W_IGNORE_FLAG = (
    "-- Retention OFF (keep_attrs = false): the spec returns the combined object\n"
    "-- VERBATIM, keeping its top-level bag [(\"z\",\"zz\")]. Rebuilding regardless\n"
    "-- of the flag (overwriting it with `a`'s top-level bag) is refuted here.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], some \"cnd\", false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          false\n"
    "        = ⟨[(\"z\",\"zz\")], none, false, [], [], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], some \"cnd\", false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        false true\n"
    "        (implementation_where\n"
    "          ⟨[], some \"cnd\", false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          false true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  simp only [h]\n"
    "  decide\n"
)


_W_COORD_HEAD_SKIP = (
    "-- Non-promotion regime with TWO coordinates. The spec rebuilds EVERY\n"
    "-- coordinate from the like-named component of `a`, so the head coordinate\n"
    "-- 'c1' must receive `a`'s bag [(\"k\",\"c1\")] and not keep the combination\n"
    "-- routine's [(\"z\",\"zz\")]. The tail coordinate 'c2' is rebuilt identically by\n"
    "-- gold and by the rival, so the HEAD alone decides this comparison — that is\n"
    "-- what makes it a partial-domain (near-miss) refutation rather than a\n"
    "-- wholesale one.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c1\", [(\"k\",\"c1\")]⟩, ⟨\"c2\", [(\"k\",\"c2\")]⟩], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[], none, false, [], [⟨\"c1\", [(\"z\",\"zz\")]⟩, ⟨\"c2\", []⟩], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c1\", [(\"k\",\"c1\")]⟩, ⟨\"c2\", [(\"k\",\"c2\")]⟩], []⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c1\", [(\"k\",\"c1\")]⟩, ⟨\"c2\", [(\"k\",\"c2\")]⟩], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  simp only [h]\n"
    "  decide\n"
)

_W_VAR_HEAD_SKIP = (
    "-- Non-promotion regime with TWO data variables. The spec rebuilds EVERY data\n"
    "-- variable from the like-named component of `a`, so the head variable 'd1'\n"
    "-- must receive `a`'s bag [(\"k\",\"d1\")] and not keep the combination routine's\n"
    "-- [(\"z\",\"zz\")]. The tail variable 'd2' is rebuilt identically by gold and by\n"
    "-- the rival, so the HEAD alone decides — a partial-domain refutation in the\n"
    "-- data-variable carrier.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [⟨\"d1\", [(\"k\",\"d1\")]⟩, ⟨\"d2\", [(\"k\",\"d2\")]⟩], [], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[], none, false, [⟨\"d1\", [(\"z\",\"zz\")]⟩, ⟨\"d2\", []⟩], [], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [⟨\"d1\", [(\"k\",\"d1\")]⟩, ⟨\"d2\", [(\"k\",\"d2\")]⟩], [], []⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [⟨\"d1\", [(\"k\",\"d1\")]⟩, ⟨\"d2\", [(\"k\",\"d2\")]⟩], [], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  simp only [h]\n"
    "  decide\n"
)


# RESERVED-SKIPPED — resolves each component's name against `a`'s COMPONENTS
# only, skipping the stage where `a`'s own kind answers for a name it reserves.
# Correct on every unreserved name (the whole tail of the name domain) and wrong
# exactly where the object itself answers, so this is the partial-domain rival
# for the resolution-order stage.
_RESERVED_SKIPPED = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let comp := fun (nm : String) =>\n"
    "    match (a.dataVars ++ a.coords).find? (fun c => c.name == nm) with\n"
    "    | some c => c.attrs\n"
    "    | none => []\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := comp c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := comp c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := comp c.name }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)

# RESERVED-COLLAPSED — honours the reserved stage but collapses its two outcomes
# into one, handing every reserved name `a`'s top-level bag instead of the bag
# that name's own answer carries. Correct for the reserved names whose answer IS
# a whole-object view, wrong for every reserved name that carries no bag.
_RESERVED_COLLAPSED = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let res := fun (nm : String) =>\n"
    "    match a.reserved.find? (fun e => e.1 == nm) with\n"
    "    | some _ => a.topAttrs\n"
    "    | none =>\n"
    "      match (a.dataVars ++ a.coords).find? (fun c => c.name == nm) with\n"
    "      | some c => c.attrs\n"
    "      | none => []\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := res c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := res c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := res c.name }) }\n"
    "  if produces then\n"
    "    return some result\n"
    "  else\n"
    "    return none"
)


_W_RESERVED_SKIPPED = (
    "-- Non-promotion regime. `a` RESERVES the name 'c' (its own kind answers for\n"
    "-- that name, and that answer is a view of the whole object, so it carries\n"
    "-- `a`'s top-level bag [(\"t\",\"A\")]) AND also has a coordinate 'c' with its own\n"
    "-- bag [(\"k\",\"cv\")]. Resolving 'c' against `a` must stop at the reserved\n"
    "-- stage and yield [(\"t\",\"A\")]; searching the components only, and so\n"
    "-- yielding [(\"k\",\"cv\")], is refuted here.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], [(\"c\", [(\"t\",\"A\")])]⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[(\"z\",\"zz\")], none, false, [], [⟨\"c\", []⟩], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], [(\"c\", [(\"t\",\"A\")])]⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], [(\"c\", [(\"t\",\"A\")])]⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  simp only [h]\n"
    "  decide\n"
)

_W_RESERVED_COLLAPSED = (
    "-- Non-promotion regime. `a` RESERVES the name 'c' with an answer that carries\n"
    "-- NO bag (the reserved entry pairs 'c' with the empty bag), and also has a\n"
    "-- coordinate 'c'. Resolving 'c' must yield that reserved answer's bag — the\n"
    "-- EMPTY one — not `a`'s top-level bag [(\"t\",\"A\")]; handing every reserved\n"
    "-- name the top-level bag instead is refuted here.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], [(\"c\", [])]⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[(\"z\",\"zz\")], none, false, [], [⟨\"c\", [(\"z\",\"zz\")]⟩], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], [(\"c\", [])]⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], [(\"c\", [])]⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "  simp only [h]\n"
    "  decide\n"
)


# NO-OBJECT-ARM IGNORED — carries out the retention rebuild correctly in every
# regime but always reports a combined object, ignoring the observation that says
# this call yields none. Correct on exactly the calls that DO yield an object
# (where the new clause pins the value) and wrong on every call that does not.
_ALWAYS_OBJECT = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "  return some result"
)

# NO-OBJECT-ARM OVERREACH — the converse: reports no object on every call, so it
# is correct exactly on the calls that yield none and wrong on every call that
# does yield one. Together with the rival above this pins BOTH directions of the
# optional-outcome clause, so neither arm can be collapsed into the other.
_NEVER_OBJECT = (
    "def implementation_where\n"
    "    (cond a b : XObj) (keep_attrs produces : Bool) : Option XObj := Id.run do\n"
    "  let mut result := select_combine cond a b keep_attrs\n"
    "  if keep_attrs then\n"
    "    if b.isContainer && !a.isContainer then\n"
    "      result := { result with topAttrs := [] }\n"
    "      match a.name with\n"
    "      | some nm =>\n"
    "          result := { result with\n"
    "            dataVars := result.dataVars.map\n"
    "              (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c) }\n"
    "      | none => pure ()\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "    else\n"
    "      result := { result with topAttrs := a.topAttrs }\n"
    "      result := { result with\n"
    "        dataVars := result.dataVars.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "      result := { result with\n"
    "        coords := result.coords.map (fun c => { c with attrs := lookupAttrs a c.name }) }\n"
    "  let _ := result\n"
    "  return none"
)

_W_ALWAYS_OBJECT = (
    "-- A call that yields NO object (`produces` false). The spec pins the\n"
    "-- outcome to `none`; reporting a combined object anyway is refuted here.\n"
    "-- No hypothesis about the combination routine is needed: on this arm the\n"
    "-- specified outcome does not mention it.\n"
    "example :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], []⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        true false\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true false) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "    rebuildFrom lookupAttrs\n"
    "  decide\n"
)

_W_NEVER_OBJECT = (
    "-- A call that DOES yield an object (`produces` true). The spec pins the\n"
    "-- outcome to `some` of the combined object with attributes retained;\n"
    "-- reporting no object is refuted here.\n"
    "example\n"
    "    (h : select_combine\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true\n"
    "        = ⟨[(\"z\",\"zz\")], none, false, [], [⟨\"c\", []⟩], []⟩) :\n"
    "    ¬ problem_spec_where\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], []⟩\n"
    "        ⟨[], none, false, [], [], []⟩\n"
    "        true true\n"
    "        (implementation_where\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          ⟨[(\"t\",\"A\")], some \"x\", false, [], [⟨\"c\", [(\"k\",\"cv\")]⟩], []⟩\n"
    "          ⟨[], none, false, [], [], []⟩\n"
    "          true true) := by\n"
    "  unfold problem_spec_where implementation_where expectedResult retainedResult\n"
    "    rebuildFrom lookupAttrs\n"
    "  simp only [h]\n"
    "  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. Statement byte-identical; the
    # frozen tactic body still closes the reordered shape (disjoint field
    # updates commute definitionally). No helper lemma, axiom, or assumption.
    # =====================================================================
    {
        "id": "pos-reorder-field-updates",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "a correct reshape that applies the three result-field updates "
            "(top-level bag / data variables / coordinates) in a DIFFERENT order "
            "in both regimes. The updates are on disjoint record fields, so they "
            "commute definitionally and the produced value is byte-identical to "
            "gold on every input; every clause of `result = expectedResult cond a "
            "b keep_attrs produces` still holds. Verifies with the frozen tactic body "
            "(re-proved for the new shape, no new declaration/axiom); if it could "
            "not, the spec would be SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-recursive-rebuild",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD, _POS_RECURSIVE),
            _TACTIC_BODY, _POS_RECURSIVE_PROOF),
        "rationale": (
            "the SECOND soundness probe, and a strictly larger reshape than "
            "pos-reorder-field-updates: the component rebuild is written as a "
            "STRUCTURALLY RECURSIVE helper `rebuildEach` over the component list "
            "instead of `List.map`, so the rebuilt lists are no longer the same "
            "TERM as the spec's `comps.map (fun c => ...)` — they are only "
            "provably equal, by an induction the variant's own proof supplies as "
            "a `have`. That is what makes it a real SPEC-TOO-STRONG probe: the "
            "reorder case is closed by the frozen tactic body UNCHANGED (its "
            "three record updates commute definitionally, so nothing had to be "
            "reproven), whereas this one provably cannot be — the bridging lemma "
            "is required — so it tests that the spec admits a faithful correct "
            "impl whose rebuild does not reduce to the spec's own. It VERIFIES "
            "(measured), i.e. the spec is not SPEC-TOO-STRONG on this axis. "
            "Statement byte-identical; `rebuildEach` is an impl-region `def` and "
            "the bridge is a `have` inside the existing proof region, so no new "
            "top-level theorem, axiom or `sorry`."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY (verify) — the obligation is SATISFIABLE at the normal,
    # F2P-shaped input, discharged as a `have` inside the proof region alongside
    # the frozen obligation. Statement byte-identical; nothing assumed.
    # =====================================================================
    {
        "id": "admiss-f2p-dataarray-coord",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _TACTIC_BODY, _ADMISS_HAVE + _TACTIC_BODY),
        "rationale": (
            "the obligation is discharged at the F2P ground input (the 3-object "
            "DataArray scenario: `a` has top-level bag [(\"attr\",\"x_da\")] and a "
            "coordinate 'a' bearing [(\"attr\",\"x_coord\")]; keep_attrs = true; "
            "non-promotion) by `rfl` on the concrete objects, then the frozen "
            "obligation is closed verbatim. Verifies (else the modeled behavior "
            "is unsatisfiable at the normal input, the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: the theorem STATEMENT is "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body, and no new declaration/axiom/`sorry` is introduced."
        ),
    },
    {
        "id": "admiss-f2p-promotion-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _TACTIC_BODY, _ADMISS_PROMO_HAVE + _TACTIC_BODY),
        "rationale": (
            "the SECOND admissibility shape, and the one the case above cannot "
            "reach: that instance fires the non-promotion arm, so the promotion "
            "regime's own clauses (top-level bag emptied; the data variable named "
            "by `a` receiving `a`'s top-level bag) are vacuous in it. Here the "
            "container flags select promotion — `a` a non-container named \"x\" "
            "with top-level bag [(\"attr\",\"x_da\")] and a coordinate 'a' bearing "
            "[(\"attr\",\"x_coord\")], `b` a container carrying a like-named data "
            "variable and its own top-level bag — and the obligation is discharged "
            "there by `rfl` on the concrete objects before the frozen obligation is "
            "closed verbatim. So satisfiability is demonstrated on BOTH arms of the "
            "shape decision rather than on one and assumed on the other; if this "
            "ground instance could not be discharged, the modeled behavior would be "
            "unsatisfiable at an F2P-shaped promotion input (the analogue of "
            "PRECOND-TOO-STRONG). Statement byte-identical, nothing assumed: the "
            "instance is a `have` inside the existing tactic body, with no new "
            "declaration/axiom/`sorry`."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation witness
    # conditioning on the opaque combination routine at one concrete input.
    # =====================================================================
    {
        "id": "weak-coord-broadcast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_COORD_BROADCAST),
        "refinement": (
            "this is EXACTLY the reported defect: in the ordinary regime each "
            "rebuilt coordinate bag is set to `a`'s single top-level bag instead "
            "of the like-named coordinate's own bag. Its faithful real patch is "
            "the pre-fix behavior. The F2P constructs an object whose coordinate "
            "'a' has attributes distinct from the top-level bag and asserts the "
            "coordinate keeps ITS OWN attributes; the identity comparison then "
            "fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause pinning every rebuilt component's bag to "
            "`lookupAttrs a c.name` (the like-named component of `a`), never `a`'s "
            "top-level bag. At a combined object with a coordinate 'c' whose bag "
            "differs from `a`'s top-level bag, the spec demands the per-coordinate "
            "bag but the rival writes the top-level bag. Refuted in the "
            "non-promotion regime (b.isContainer = false)."
        ),
        "witness": _W_COORD_BROADCAST,
    },
    {
        "id": "weak-var-broadcast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_VAR_BROADCAST),
        "refinement": (
            "the ordinary-regime counterpart in the data-variable carrier: each "
            "rebuilt data-variable bag is set to `a`'s top-level bag instead of "
            "the like-named variable's own bag. A real patch with this behavior "
            "would give every data variable `a`'s global attributes; the F2P "
            "asserts a data variable keeps ITS OWN attributes, so the comparison "
            "fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the same guarantee (each component's bag is the "
            "like-named component's, not the top-level bag), attacked in the "
            "data-variable position. At a combined object with a data variable 'd' "
            "whose bag differs from `a`'s top-level bag, the spec demands the "
            "per-variable bag but the rival writes the top-level bag. Refuted in "
            "the non-promotion regime with a data-variable-bearing `a`, varying "
            "that carrier off the coordinate rival above."
        ),
        "witness": _W_VAR_BROADCAST,
    },
    {
        "id": "weak-promo-top-leak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PROMO_TOP_LEAK),
        "refinement": (
            "the promotion regime (b a container, a not) must EMPTY the result's "
            "top-level bag; this rival leaves `a`'s top-level bag there. A real "
            "patch with this behavior would surface `a`'s global attributes on the "
            "promoted container; the F2P promotion scenario asserts the promoted "
            "container's global attributes come from the container leg (empty for "
            "the promoted-DataArray case), so the comparison fails. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the promotion-regime clause `topAttrs := []`. With "
            "`b.isContainer = true` and `a.isContainer = false`, a combined object "
            "whose top-level bag is non-empty must be emptied; the rival keeps "
            "`a`'s top-level bag, so the result differs. Refuted where the "
            "container flags select the promotion regime (b.isContainer = true), "
            "varying that binder off the non-promotion rivals."
        ),
        "witness": _W_PROMO_TOP_LEAK,
    },
    {
        "id": "weak-promo-slot-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PROMO_SLOT_DROP),
        "refinement": (
            "in the promotion regime the data variable bearing `a`'s own name "
            "must receive `a`'s TOP-LEVEL bag (a promoted to a single data "
            "variable); this rival instead draws it from a like-named-component "
            "lookup, which is empty when `a` has no such component, dropping the "
            "promoted variable's attributes. The F2P promotion scenario asserts "
            "the promoted data variable carries `a`'s attributes, so the "
            "comparison fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the promotion-regime clause writing `a.topAttrs` to the "
            "data variable whose name equals `a.name`. At a combined object with a "
            "data variable 'x' matching `a`'s name, where `a` carries a non-empty "
            "top-level bag but has no like-named component, the spec demands the "
            "top-level bag while the rival's same-name lookup yields the empty "
            "bag. Refuted in the promotion regime."
        ),
        "witness": _W_PROMO_SLOT_DROP,
    },
    {
        "id": "weak-nonpromo-top-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NONPROMO_TOP_DROPPED),
        "refinement": (
            "in the ordinary regime the result's top-level bag must be taken "
            "from `a`; this rival rebuilds every component correctly but leaves "
            "the result's own top-level bag as the combination routine produced "
            "it. A real patch with this behavior would retain per-component "
            "attributes while dropping the object's GLOBAL ones, and the F2P "
            "asserts the retained object's own top-level attributes are `a`'s "
            "(distinct from the ones the combination routine merges), so the "
            "identity comparison fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the non-promotion clause `topAttrs := a.topAttrs` — the "
            "ONE clause of the postcondition no other rival attacks directly. "
            "weak-promo-top-leak attacks the mirror clause (`topAttrs := []`) in "
            "the promotion regime, and weak-ignore-keep-attrs only reaches this "
            "write at keep_attrs = FALSE, where the spec's demand is the opposite "
            "(pass the bag through untouched); so before this case the ordinary "
            "regime's top-level write was pinned in neither direction at "
            "keep_attrs = true. Refuted at a combined object whose top-level bag "
            "differs from `a`'s with every component list EMPTY, so the top-level "
            "bag is the only thing the comparison can turn on."
        ),
        "witness": _W_NONPROMO_TOP_DROPPED,
    },
    {
        "id": "weak-ignore-keep-attrs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IGNORE_FLAG),
        "refinement": (
            "rebuilding attributes unconditionally ignores the retention flag; "
            "when retention is off the combined object must be returned VERBATIM. "
            "A real patch that rebuilt attributes regardless of the flag would "
            "overwrite attributes that the pre-existing keep_attrs=False tests "
            "require to pass through unchanged, so those tests fail. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the top-level `if !keep_attrs then r` arm: with "
            "keep_attrs = false the spec returns `select_combine cond a b false` "
            "verbatim, but the rival rebuilds the top-level bag from `a`. At a "
            "combined object whose top-level bag differs from `a`'s, the results "
            "diverge. Refuted with keep_attrs = false, varying that binder off "
            "the `true` value every other rival holds."
        ),
        "witness": _W_IGNORE_FLAG,
    },

    # =====================================================================
    # PARTIAL-DOMAIN near-misses. Every rival above is wrong on the WHOLE of
    # its regime, so each is refutable at a single-component carrier and none
    # tests that the rebuild covers every component of a MULTI-component list.
    # These two are correct on the tail of the component list and wrong only at
    # its head, so their witnesses are decided by a component the rival gets
    # wrong while an adjacent one it gets right is also present.
    # =====================================================================
    {
        "id": "weak-coord-head-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_COORD_HEAD_SKIP),
        "refinement": (
            "the rebuild covers every coordinate but the first, which keeps "
            "whatever bag the combination routine produced. A real patch with "
            "this behavior would rebuild all but one coordinate correctly; the "
            "F2P builds an object whose coordinate carries its own attributes "
            "distinct from the top-level bag and asserts that coordinate keeps "
            "ITS OWN attributes. At the one-coordinate F2P shape that coordinate "
            "IS the head, so it is exactly the coordinate left unrebuilt and the "
            "identity comparison fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the universally-quantified reach of the rebuild clause: "
            "`rebuildFrom a r.coords` maps EVERY coordinate to `lookupAttrs a "
            "c.name`, not all-but-one. Refuted at a combined object with two "
            "coordinates where the tail is rebuilt identically by gold and by "
            "the rival, so the head coordinate alone decides the comparison — a "
            "near-miss the wholesale-broadcast rivals cannot express."
        ),
        "witness": _W_COORD_HEAD_SKIP,
    },
    {
        "id": "weak-var-head-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_VAR_HEAD_SKIP),
        "refinement": (
            "the data-variable counterpart: every data variable but the first is "
            "rebuilt from its like-named component of `a`, the head keeping the "
            "combination routine's bag. A real patch with this behavior would "
            "leave the first data variable's attributes as the combination "
            "produced them; the F2P container scenario asserts a data variable "
            "carries the attributes drawn from `a`'s like-named component, so "
            "the comparison fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the same universally-quantified reach in the OTHER "
            "carrier: `rebuildFrom a r.dataVars` covers every data variable. "
            "Refuted at a combined object with two data variables where the tail "
            "is rebuilt identically by both, so the head variable alone decides. "
            "Varies the component-list LENGTH (two components, not one) off "
            "every other reject case."
        ),
        "witness": _W_VAR_HEAD_SKIP,
    },

    # =====================================================================
    # RESOLUTION-ORDER rivals. Resolving a component's name against `a` has
    # STAGES: `a`'s own kind answers first for a name it reserves, and only an
    # unreserved name reaches the components. Every rival above varies WHICH
    # components are rebuilt or from WHERE at the whole-bag level; these two
    # attack the staged lookup itself — one skipping the reserved stage, one
    # collapsing its two outcomes — so the stage is pinned rather than assumed.
    # =====================================================================
    {
        "id": "weak-reserved-skipped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RESERVED_SKIPPED),
        "refinement": (
            "the rival resolves each component's name against `a`'s COMPONENTS "
            "only, never letting `a`'s own kind answer for a name it reserves. "
            "A real patch with this behavior would have to bypass the host "
            "language's own attribute resolution — reaching the variable "
            "namespace for a name the object's class already answers — which the "
            "real lookup cannot do. It is wrong on exactly the reserved names, so "
            "the hidden cases that pin what a reserved name resolves to fail. It "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the FIRST stage of `lookupAttrs`: when `a` reserves the "
            "name, the bag is the one that reserved answer carries, not the "
            "like-named component's. Refuted at an `a` that both reserves 'c' "
            "(with a whole-object-view answer, so the bag is `a`'s top-level one) "
            "and has a coordinate 'c' with a DIFFERENT own bag, so the two stages "
            "disagree and the stage order alone decides. Correct on every "
            "unreserved name, which is what makes it a partial-domain near-miss "
            "rather than a wholesale one."
        ),
        "witness": _W_RESERVED_SKIPPED,
    },
    {
        "id": "weak-reserved-collapsed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RESERVED_COLLAPSED),
        "refinement": (
            "the rival honours the reserved stage but collapses its two outcomes, "
            "handing EVERY reserved name `a`'s top-level bag instead of the bag "
            "that name's own answer carries. A real patch with this behavior would "
            "attach the object's global attributes to every component whose name "
            "the class reserves, including the majority whose class-level answer "
            "carries no attributes at all, so the hidden cases pinning the "
            "bag-less outcome fail. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the reserved stage yielding the RECORDED bag of the "
            "reserved answer, which for most reserved names is the EMPTY bag. "
            "Refuted at an `a` reserving 'c' with an empty-bag answer while "
            "carrying a non-empty top-level bag: the spec demands the empty bag, "
            "the rival writes the top-level bag. Complements the skipped-stage "
            "rival by varying the reserved entry's BAG rather than the stage "
            "order, so neither outcome of the stage is left unpinned."
        ),
        "witness": _W_RESERVED_COLLAPSED,
    },
    {
        "id": "weak-no-object-arm-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_OBJECT),
        "refinement": (
            "the rebuild itself is gold, but the outcome always reports a "
            "combined object, including on the calls that yield none. Its "
            "faithful real counterpart is a routine that presses on with the "
            "per-component consultations even where they cannot be carried out "
            "and hands back a combined object built from whatever it got. That "
            "is not the behavior the F2P scenarios exercise (they all yield "
            "objects) but it is a DIFFERENT function from the specified one, so "
            "the spec must not admit it."
        ),
        "rationale": (
            "REJECT from the optional-outcome clause: when `produces` is false "
            "the outcome is pinned to `none`. This rival is correct on exactly "
            "the calls where the retention clause pins a value and wrong on "
            "every call that yields no object, so it isolates the new arm and "
            "nothing else. Its witness needs no hypothesis about the "
            "combination routine, since on that arm the specified outcome does "
            "not mention it."
        ),
        "witness": _W_ALWAYS_OBJECT,
    },
    {
        "id": "weak-no-object-arm-overreach",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NEVER_OBJECT),
        "refinement": (
            "the converse over-reach: no call is reported as yielding an "
            "object. Its faithful real counterpart never returns a combined "
            "object at all, so every F2P scenario — each of which asserts "
            "concrete retained attributes on a returned object — fails "
            "immediately. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the same clause read in the other direction: when "
            "`produces` is true the outcome is `some` of the combined object "
            "with attributes retained. Paired with "
            "weak-no-object-arm-ignored this pins BOTH arms, so the optional "
            "outcome cannot be collapsed to a constant in either direction and "
            "the clause is not a free pass. Refuted at the same input as the "
            "headline rival, with the observation set the other way."
        ),
        "witness": _W_NEVER_OBJECT,
    },
]


# The combination routine is an A-reference deep-model (validated == the real
# callee by G-AX), not a consumed `_prop` axiom; the proof consumes no axiom.
# So there is no in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []

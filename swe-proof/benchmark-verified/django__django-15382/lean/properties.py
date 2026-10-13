"""properties.py — PBT falsification manifest for django__django-15382 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Every case edits ONLY the implementation region
(and, for the soundness positives, the proof body), so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition rather than to a tampered spec. The
`theorem correct_compileExistenceCheck` STATEMENT is re-emitted byte-identically
by each positive; no case adds an axiom, a helper lemma, `sorry`, `admit`, or
`native_decide`.

DEFENDED SURFACE
----------------
The modeled function is the pure dispatch that renders a (possibly negated)
existence test over a subquery:

    implementation_compileExistenceCheck
        (negated : Bool)
        (inner   : Except RenderFailure (String × List String))
        : Except RenderFailure (String × List String)

pinned by the single load-bearing clause `problem_spec_compileExistenceCheck`,
which is a total match on `inner` and therefore decomposes into THREE
independent top-level clauses, each of which the reject lane attacks:

  * C-EMPTY  `inner = .error .emptyResult` →
        `result = if negated then .ok ("", []) else .error .emptyResult`
    Two independent facts on the negated side (the fragment is EXACTLY the empty
    string, and the parameter list is EXACTLY empty) and one on the non-negated
    side (the signal PROPAGATES rather than becoming a normal result). This is
    the clause the instance turns on.
  * C-OTHER  `inner = .error .other` → `result = .error .other`
    A non-empty-result failure propagates unchanged, for BOTH values of
    `negated` — i.e. only the empty-result signal is ever special-cased, and the
    failure identity is preserved.
  * C-OK     `inner = .ok (sql, params)` →
        `result = .ok ((if negated then "NOT " ++ sql else sql), params)`
    Four independent facts: the fragment is the inner one when not negated, it
    is the inner one under a textual negation prefix when negated, that prefix
    is exactly `"NOT "` (attacked by `prefix-text-nearmiss`), and the bind
    parameters are passed through UNCHANGED — as a VALUE, so their presence
    (`drop-params-ok`), their ORDER (`params-reordered`) and their MULTIPLICITY
    (`params-deduplicated`) are each pinned by a separate rival. Read the
    parameter component as three facts, not one: a rival can get any two right
    and the third wrong, and the second audit found exactly that (see CASES ADDED
    BY THE SECOND ADVERSARIAL AUDIT).

The carrier is FULLY TRANSPARENT — `RenderFailure` is a two-constructor
`inductive` with `DecidableEq`, the fragment is a `String`, the parameters a
`List String`, and there is no `opaque` callee anywhere (the generic subquery
renderer is taken as the boundary INPUT `inner`, not axiomatized). So every
rival is refutable at concrete literals and no witness needs to condition on
the carrier; correspondingly no witness binds a hypothesis, so none can be
`witness-inconsistent`.

BINDER COVERAGE
---------------
There are exactly two input binders, and the reject witnesses vary both, in
every combination the spec branches on:

  * `negated` — probed at `true` (propagate-negated-empty, nonempty-fragment,
    fabricate-params-empty, other-failure-swallowed, drop-not-prefix,
    drop-params-ok) AND at `false` (swallow-signal-always, prefix-always,
    fabricate-fragment-ok, other-as-empty-signal).
  * `inner` — probed at all three constructors: `.error .emptyResult`, `.error
    .other`, and `.ok (sql, params)`. Within the `.ok` payload the witnesses use
    a non-trivial fragment (`"s = 1"`, so a dropped/fabricated prefix is
    observable) and a MULTI-element parameter list of DISTINCT tokens
    (`["p1", "p2"]`, so a dropped, fabricated, or PERMUTED parameter list is
    observable independently of the fragment — distinctness matters, since a
    repeated or single-element list is a fixed point of `reverse` and would make
    `params-reordered`'s witness vacuous); `drop-params-ok` deliberately pairs an
    EMPTY fragment with a non-empty parameter list, so it discriminates on the
    parameter component alone and cannot be confused with a fragment-level
    failure. `params-deduplicated` is the one case that must NOT use distinct
    tokens: its witness list is `["p1", "p1"]`, because a list of distinct tokens
    is a fixed point of a multiplicity-collapsing map and would make ITS witness
    vacuous the same way a repeated list would for `params-reordered`. So the
    `.ok` parameter payload is probed at BOTH shapes deliberately, and neither
    shape subsumes the other.

That leaves no binder held at a single value across the reject lane, and no
top-level clause of the postcondition unattacked.

The spec is additionally known to be DETERMINISTIC, which bounds how weak it can
be: `∀ negated inner r1 r2, spec negated inner r1 → spec negated inner r2 →
r1 = r2` was proved in the audit (a `match inner` with `simp_all` per arm), and
so was the corollary that any result satisfying the spec equals the frozen impl's
(`spec negated inner r → r = implementation_… negated inner`). A postcondition
that pins its result uniquely at every input admits exactly one function
extensionally, so no wrong implementation of this dispatch can verify — SPEC-TOO-WEAK
is unreachable here, and each reject case's content is which clause-component its
witness attributes the refutation to.

Read that bound narrowly. It says every wrong impl is REJECTED; it does not say the
shipped witnesses ATTRIBUTE every wrong impl's error, and the two are independently
checkable. The second audit wrote seven fresh wrong impls: all seven were rejected
(so the determinism argument holds up under attack, and `spec_holes` is empty), but
one of them — collapsing repeated bind parameters — was discriminated by ZERO of the
twelve then-shipped witnesses, all twelve of which elaborated against it. That is a
witness-coverage gap, not a spec hole, and it is why `params-deduplicated` ships.

PORTING NOTES (which nagini cases port, which are omitted and why)
------------------------------------------------------------------
The nagini sibling models `render_exists(satisfiable, negated) -> List[int]`
with an exception-carrying contract (`Exsures(EmptyResultSet, …)`) and an
`inner_fragment` @Pure @ContractOnly companion. Here the inner renderer's
OUTCOME is the boundary input, so nagini's `satisfiable` flag becomes the
`inner` constructor and nagini's exception channel becomes the `Except` result.
Case by case:

  * `atk-raise-unsatneg` (nagini's pre-patch bug; rejects on E1/C1) →
    `propagate-negated-empty`. Same argument: on a NEGATED test over a subquery
    known to match nothing, propagate the signal instead of rendering the empty
    fragment. Refuted by C-EMPTY.
  * `atk-neverraise` (rejects on C1) → `swallow-signal-always`. Same argument:
    the signal is swallowed on the NON-negated side too, where it must
    propagate.
  * `atk-junk-unsatneg` + `atk-false-pred` + `atk-space-unsatneg` (three nagini
    rivals all rejecting on C3 `len(Result()) == 0`, differing only in WHICH
    non-empty fragment they fabricate) → collapsed to ONE case,
    `nonempty-fragment`. On this carrier the fragment is a `String` compared for
    equality against `""`, so all three fail at the same input for the same
    reason (`"" ≠ <anything non-empty>`) and would share a witness verbatim;
    shipping three would claim three sub-domains the manifest demonstrates once.
    Kept the always-true-predicate shape, which is the one a real patch would
    plausibly reach for. The collapse was re-derived in the audit: the other two
    shapes (single space `" "`, always-false `"0=1"`) were built as fresh rivals
    and each is refuted by a witness at the SAME input `(true, .error
    .emptyResult)` with the same tactic, confirming they are one point of the
    spec rather than three. NOTE that this collapse is sound only because these
    three differ in the fragment VALUE at one input; it is not a license to
    collapse rivals that differ in WHICH clause-component they violate, which is
    why the audit added `prefix-text-nearmiss` and `params-reordered` rather than
    treating them as more of the same.
  * `atk-fabricate-echo` (nagini's ungrounded-oracle ECHO probe, rejects on
    C4/C5) → `fabricate-fragment-ok`. The argument carries but the mechanism
    does not: nagini needed a witness-unique @ContractOnly companion because its
    spec could only name the renderer's output through an oracle. Here the
    fragment is a bound VARIABLE of the input, so `result = .ok (sql, params)`
    is grounded in the input by construction and there is no oracle to echo —
    the case degenerates into an ordinary fragment-fabrication rival, which is
    what it is shipped as.
  * `atk-noprefix` (rejects on C5) → `drop-not-prefix`.
  * `atk-prefix-always` (rejects on C4) → `prefix-always`.
  * `pos-structdiff` → `pos-functional-form`; `pos-reorder` →
    `pos-negated-first`. Both re-proved for their new impl shape with the
    theorem statement byte-identical (see below). Neither is trivially the frozen
    impl: the audit renamed gold's impl and asked `rfl` whether the two functions
    are definitionally equal, and BOTH probes failed with `goldImpl is not
    definitionally equal to implementation_compileExistenceCheck`. So each
    positive is a genuine reshape whose proof had to be re-closed, not a restated
    gold that would verify while testing nothing. Three FURTHER correct reshapes
    were built in the audit and all verify (exit 0), so the spec is not over-fit:
    a flat six-way `match negated, inner` using `String.append`; the negation
    conditional lifted OUTSIDE the pair constructor via `cond`; and a version
    factoring the prefix into an impl-region helper `def`. FIVE more were built in
    the second audit and all five also verify: a `bif`-guarded form with the
    failure arms matched separately; a `match negated with` returning through
    `String.append`; a precomputed-prefix form; one that round-trips the parameter
    list through `List.reverse` twice (closed with `simp [List.reverse_reverse]`);
    and one that builds the fragment at the `String.mk`/`List Char` level, which
    needed `cases negated <;> simp [String.ext_iff, String.data_append]`. Note the
    last two: neither closes under the frozen proof's `rfl` script, and the naive
    reading of that is "the spec rejects a faithful correct impl, SPEC-TOO-STRONG".
    It is not — both are provable, the first script tried was simply the wrong
    one. A soundness-hole claim on this bundle needs the tactic search exhausted
    before it is believed.
  * `admiss-f2p` → `admiss-f2p-empty-signal`. This case WAS omitted, twice, and
    both times for a reason the second audit measured and found WRONG. The
    original port omitted it as "vacuous"; the first audit re-derived that and
    concurred, on the argument that the lean obligation is `∀ negated inner,
    problem_spec …` with NO precondition hypothesis, so the F2P-shaped input is
    admitted by construction and an admissibility positive "would assert only
    that a total function is total". The premise is true and the conclusion does
    not follow. The absence of a precondition means the PRECONDITION half of the
    class is vacuous; it says nothing about the other half. On a total carrier the
    analogue of nagini's precondition-admission self-call is that the OBLIGATION
    is SATISFIABLE at exactly the F2P-shaped input — a postcondition can perfectly
    well be unsatisfiable at a normal input while the impl is total, and the
    reject lane cannot see that, because every reject case asks whether a WRONG
    impl is refuted, never whether the frozen one is dischargeable at a NAMED
    point. So the class is expressible and load-bearing here, and it is now
    shipped: the positive pins the impl's value at (`negated = true`,
    empty-result signal) by EVALUATION, discharges the spec predicate at that
    concrete input as a `have`, does the same for the non-negated companion, and
    only then closes the frozen obligation verbatim. Built with
    scripts/lean_verify.sh, exit 0. Recorded here at length because "the frozen
    obligation has no precondition" is a plausible-sounding omission rationale
    that a reviewer will meet again, and it is not sufficient on its own.
  * nagini's FRAME / permission class (`Acc(list_pred(Result()))`, clause C2 —
    output ownership) has no counterpart: Lean is referentially transparent, so
    there is no fractional permission and no aliasing to abuse. Unlike some
    bundles the result here carries no input container that a rival could mutate
    on a pass-through path — the parameter list IS pinned, but as a value
    equality (see `drop-params-ok`), which is the C-OK content clause and not a
    frame obligation. No substitute fabricated.
  * the divergence / non-termination class is genuinely VACUOUS on lean, and the
    second audit re-measured this against the frozen file's own termination
    setting rather than assuming it: `Solution.lean` carries NO
    `set_option loom.semantics.termination` line and
    `implementation_compileExistenceCheck` is a total Lean `def`, which is the
    "total" disposition — under it a diverging rival must be UNSHIPPABLE, and it
    is. Three shapes were tried. A self-recursive plain `def` is rejected by the
    elaborator itself (`fail to show termination`), so it never becomes a variant.
    The two shapes that DO elaborate only do so by going opaque — marking the
    recursion `partial`, or an unbounded `while` — and opacity is exactly what
    kills the witness: five witness shapes were built against each, and the four
    evaluating shapes fail on BOTH sides (nothing reduces), while the fifth, which
    conditions the impl's value on a hypothesis, ELABORATES on both the rival and
    the frozen solution — i.e. it is vacuous and would land as
    `witness-inconsistent`, not as a refutation. So there is no admissible
    diverging rival AND no discriminating witness for the ones that elaborate.
    (Contrast velvet under `set_option loom.semantics.termination "partial"`,
    where the same class is a KNOWN SPEC HOLE rather than vacuous — see
    `the corpus-wide termination-semantics finding`. Nothing to port here either way, but the reason
    differs, and it is the termination setting that decides which reason applies.)
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores
    it. (Moot regardless — this bundle consumes no axiom: `axioms = []`.)

CASES ADDED BEYOND THE NAGINI SIBLING
-------------------------------------
Nagini's carrier folded every failure into one exception type and its result
type carried no parameter component, so three clause-components of this spec had
no nagini rival at all. Each is attacked here:

  * `other-failure-swallowed` and `other-as-empty-signal` attack C-OTHER — the
    only rivals that reach the `.error .other` constructor. Without them a rival
    that special-cased EVERY failure, not just the empty-result signal, would
    verify unnoticed.
  * `fabricate-params-empty` and `drop-params-ok` attack the PARAMETER component
    of C-EMPTY and C-OK respectively. Every other witness would be satisfied by
    a rival that returned the right fragment with the wrong parameters.

CASES ADDED BY THE ADVERSARIAL AUDIT
------------------------------------
Two clause-components had no rival in the ported lane. Both gaps were found by
writing fresh wrong impls and confirming each is refutable at a concrete input,
and both are components the ported witnesses provably do NOT pin:

  * `prefix-text-nearmiss` — the ported lane pinned WHETHER the negation prefix
    is applied (`drop-not-prefix`, `prefix-always`) but never WHAT it is, so a
    prefix off by its separating space was unattacked.
  * `params-reordered` — `drop-params-ok` pins only that the parameter list is
    not discarded, so a PERMUTED list was unattacked even though the spec pins
    `params` as a value.

Ten further wrong impls written during the audit are already covered by the
shipped lane and are deliberately NOT shipped, to avoid claiming sub-domains the
manifest would only re-demonstrate: reversed-empty-signal identity, the two
collapsed fragment shapes (`" "`, `"0=1"`), lowercase and suffix prefix variants,
a doubled prefix, parameter fabrication on the `.ok` negated side, parameter drop
on the non-negated side, the mirror of `other-failure-swallowed`, and conflating
the two negated paths. Each was confirmed refutable, so their omission is
redundancy and not a gap.

CASES ADDED BY THE SECOND ADVERSARIAL AUDIT
-------------------------------------------
Two more, each closing a gap the previous two passes asserted was not there:

  * `admiss-f2p-empty-signal` — the admissibility class, twice omitted on a
    rationale that does not carry. See the `admiss-f2p` entry above for the full
    correction; the short version is that "the frozen obligation has no
    precondition" retires only the precondition half of the class, and the
    satisfiable-at-an-F2P-shaped-input half is both expressible on this carrier
    and unreachable by every other lane here.
  * `params-deduplicated` — the MULTIPLICITY component of C-OK's parameter
    passthrough. The gap was found by a witness×rival matrix rather than by
    reading: seven fresh wrong impls were each built against all twelve shipped
    witnesses, and where every other rival was caught by three to six of them,
    the multiplicity-collapsing one was caught by NONE. The cause is systematic —
    every `.ok` witness in the lane used a DISTINCT-token parameter list, and such
    a list is a fixed point of the collapse — which is the general lesson: a
    witness's discriminating power depends on the SHAPE of its literal, not only
    on the input constructor it names, so "both values of `negated`, all three
    constructors of `inner`" is not by itself full coverage of a payload.

The reject lane's own soundness was re-checked at the same time and holds: all
fourteen rival modules fail to verify, all fourteen witnesses elaborate against
their rival and fail against the frozen solution with `unsolved goals ⊢ False`,
and — because a gold-side failure only proves the battery discriminates if the
exit code tracks the CLAIM — each witness was rebuilt with its claim flipped, a
control that inverts both exit codes in all fourteen cases (gold 0, rival 1). No
case passes because of a missing identifier, an unfolding failure, or a timeout.

WITNESSES
---------
Every reject case carries a `witness`: an `example` negating the spec predicate
at one concrete input, checked in a file with the frozen obligation stripped.
Each was built BOTH ways with `scripts/lean_verify.sh` — exit 0 against the
rival (the rival provably contradicts the spec) and exit 1 against the frozen
solution (a real discriminator, not a tautology). The gold-side failure is in
every case `error: unsolved goals ⊢ False`: `simp` fully REDUCED the claim and
gold provably satisfies the spec at that input, so the failure is a semantic
refutation and not a missing identifier, a type error, an unfolding failure, or a
timeout. All 20 builds (10 rival + 10 gold) were re-run independently in the
audit and reproduced these exit codes; the audit-added cases were built the same
way. The second audit re-ran the whole lane again — 14 rival + 14 gold — and
added the FORGERY control described above (14 more pairs), which is what upgrades
"the gold-side error looks semantic" from a reading to a measurement: if gold
failed for a claim-independent reason, flipping the claim would not flip its exit
code, and it does, every time.

`decide` does NOT close these goals, and the audit re-measured this rather than
taking it on faith: on both gold and a rival, a `decide` witness fails with
`failed to synthesize Decidable`, because the `Id.run do` block leaves a
`__do_jp`-shaped term (visible verbatim in the error) that the `Decidable`
instance will not reduce through. Note this is a synthesis failure on BOTH sides,
so a `decide` witness here would land as `witness-unproven` (an inconclusive
MALFORMED-TESTS case), not as a silent vacuous pass. The witnesses therefore
`simp` after unfolding, which reduces the monadic scaffolding and closes for the
rival while leaving `⊢ False` on gold.

No witness binds a hypothesis (`consistency_probe` returns None for all of them),
so none can be `witness-inconsistent` — there is nothing to be inconsistent. That
is a property of the carrier being fully transparent, not an omission.
"""
from pathlib import Path

INSTANCE = "django__django-15382"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring, asserting it
    matched, so silent drift (Solution.lean edited) fails loudly at import."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — each lies ENTIRELY inside the impl region of
# Solution.lean and is unique across the whole file.
# ---------------------------------------------------------------------------

# The whole empty-result-signal arm (the negated/non-negated dispatch). Unique:
# the spec region spells the same behavior as an `if … then … else` expression
# on one line, not as two `return` statements.
_ARM_EMPTY = (
    "      if negated then\n"
    '        return .ok ("", [])\n'
    "      else\n"
    "        return .error .emptyResult"
)

# The other-failure arm. Unique: the spec region has no `return`.
_ARM_OTHER = (
    "  | .error .other =>\n"
    "      return .error .other"
)

# The inner-success arm (mutable fragment + conditional negation prefix).
_ARM_OK = (
    "      let mut sql := sql\n"
    "      if negated then\n"
    '        sql := "NOT " ++ sql\n'
    "      return .ok (sql, params)"
)

# The complete gold impl declaration, replaced wholesale by each positive.
_GOLD_IMPL = (
    "def implementation_compileExistenceCheck\n"
    "    (negated : Bool) (inner : Except RenderFailure (String × List String)) :\n"
    "    Except RenderFailure (String × List String) := Id.run do\n"
    "  match inner with\n"
    "  | .error .emptyResult =>\n"
    + _ARM_EMPTY + "\n"
    + _ARM_OTHER + "\n"
    "  | .ok (sql, params) =>\n"
    + _ARM_OK
)
if _BASE.count(_GOLD_IMPL) != 1:
    raise AssertionError("gold impl region drift")

# The frozen obligation STATEMENT, re-emitted byte-identically by every
# positive so `variant_scope` sees the same theorem with only a new tactic body.
_THM_STMT = (
    "theorem correct_compileExistenceCheck :\n"
    "    ∀ (negated : Bool) (inner : Except RenderFailure (String × List String)),\n"
    "      problem_spec_compileExistenceCheck negated inner\n"
    "        (implementation_compileExistenceCheck negated inner) := by"
)
if _BASE.count(_THM_STMT) != 1:
    raise AssertionError("theorem statement drift")

_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"


def _swap_proof(src: str, new_proof_body: str) -> str:
    """Replace everything strictly between the proof markers. The theorem
    statement is re-emitted verbatim inside `new_proof_body`; only the tactic
    body changes, which `variant_scope` permits."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_proof_body + "\n" + src[e:]


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-functional-form) A structurally different CORRECT impl: a pure functional
# expression (no `Id.run do`, no `let mut`), with the negation prefix chosen by
# an inline conditional inside the returned pair rather than by mutating a local.
# Same behavior on every one of the six (negated, inner-constructor) points.
_POS_FUNCTIONAL_IMPL = (
    "def implementation_compileExistenceCheck\n"
    "    (negated : Bool) (inner : Except RenderFailure (String × List String)) :\n"
    "    Except RenderFailure (String × List String) :=\n"
    "  match inner with\n"
    '  | .error .emptyResult => if negated then .ok ("", []) else .error .emptyResult\n'
    "  | .error .other => .error .other\n"
    '  | .ok (sql, params) => .ok ((if negated then "NOT " ++ sql else sql), params)'
)
_POS_FUNCTIONAL = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_FUNCTIONAL_IMPL),
    _THM_STMT + "\n"
    "  intro negated inner\n"
    "  unfold problem_spec_compileExistenceCheck implementation_compileExistenceCheck\n"
    "  match inner with\n"
    "  | .error .emptyResult => cases negated <;> rfl\n"
    "  | .error .other => rfl\n"
    "  | .ok (sql, params) => rfl\n",
)

# (pos-negated-first) The SAME behavior with the dispatch order INVERTED: split
# on `negated` at the top level and match the inner outcome inside each branch,
# so the negation prefix is applied at the point of construction and the two
# failure arms are duplicated. Semantically identical; a completely different
# branch structure from gold.
_POS_NEGFIRST_IMPL = (
    "def implementation_compileExistenceCheck\n"
    "    (negated : Bool) (inner : Except RenderFailure (String × List String)) :\n"
    "    Except RenderFailure (String × List String) := Id.run do\n"
    "  if negated then\n"
    "    match inner with\n"
    '    | .error .emptyResult => return .ok ("", [])\n'
    "    | .error .other => return .error .other\n"
    '    | .ok (sql, params) => return .ok ("NOT " ++ sql, params)\n'
    "  else\n"
    "    match inner with\n"
    "    | .error .emptyResult => return .error .emptyResult\n"
    "    | .error .other => return .error .other\n"
    "    | .ok (sql, params) => return .ok (sql, params)"
)
_POS_NEGFIRST = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_NEGFIRST_IMPL),
    _THM_STMT + "\n"
    "  intro negated inner\n"
    "  unfold problem_spec_compileExistenceCheck implementation_compileExistenceCheck\n"
    "  match negated, inner with\n"
    "  | true, .error .emptyResult => rfl\n"
    "  | true, .error .other => rfl\n"
    "  | true, .ok (sql, params) => rfl\n"
    "  | false, .error .emptyResult => rfl\n"
    "  | false, .error .other => rfl\n"
    "  | false, .ok (sql, params) => rfl\n",
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# --- C-EMPTY: the empty-result-signal arm -----------------------------------

# (propagate-negated-empty) Propagate the signal for BOTH values of `negated`:
# the negated side never renders the empty fragment. This is the pre-patch shape.
_R_PROPAGATE = _swap(_BASE, _ARM_EMPTY, "      return .error .emptyResult")

# (swallow-signal-always) The mirror: render the empty fragment for BOTH values
# of `negated`, so a NON-negated test over a match-nothing subquery becomes a
# normal no-op result instead of propagating.
_R_SWALLOW = _swap(_BASE, _ARM_EMPTY, '      return .ok ("", [])')

# (nonempty-fragment) Correct control flow, wrong fragment CONTENT: on the
# negated side return an always-true predicate fragment instead of the empty
# fragment the spec pins.
_R_NONEMPTY = _swap(
    _BASE, _ARM_EMPTY,
    "      if negated then\n"
    '        return .ok ("1=1", [])\n'
    "      else\n"
    "        return .error .emptyResult",
)

# (fabricate-params-empty) Correct fragment, wrong PARAMETERS: the negated side
# returns the empty fragment but attaches a bind parameter, where the spec pins
# the parameter list empty. Isolates the parameter component of C-EMPTY.
_R_FABPARAMS = _swap(
    _BASE, _ARM_EMPTY,
    "      if negated then\n"
    '        return .ok ("", ["p"])\n'
    "      else\n"
    "        return .error .emptyResult",
)

# --- C-OTHER: the other-failure arm -----------------------------------------

# (other-failure-swallowed) Special-case a NON-empty-result failure the same way
# as the empty-result signal when negated, instead of propagating it unchanged.
_R_OTHERSWALLOW = _swap(
    _BASE, _ARM_OTHER,
    "  | .error .other =>\n"
    "      if negated then\n"
    '        return .ok ("", [])\n'
    "      else\n"
    "        return .error .other",
)

# (other-as-empty-signal) Propagate a failure but with the WRONG identity: report
# every other failure as the dedicated empty-result signal. Attacks C-OTHER's
# identity-preservation at `negated = false`.
_R_OTHERASEMPTY = _swap(
    _BASE, _ARM_OTHER,
    "  | .error .other =>\n"
    "      return .error .emptyResult",
)

# --- C-OK: the inner-success arm -------------------------------------------

# (fabricate-fragment-ok) Discard the inner fragment and return a fabricated one
# (still correctly NOT-prefixed when negated, so only the fragment identity is
# wrong).
_R_FABFRAG = _swap(
    _BASE, _ARM_OK,
    '      let mut sql := "X"\n'
    "      if negated then\n"
    '        sql := "NOT " ++ sql\n'
    "      return .ok (sql, params)",
)

# (drop-not-prefix) Never apply the negation prefix: the negated form renders as
# the bare inner fragment.
_R_NOPREFIX = _swap(_BASE, _ARM_OK, "      return .ok (sql, params)")

# (prefix-always) Apply the negation prefix unconditionally, so a NON-negated
# test renders as its own negation.
_R_PREFIXALWAYS = _swap(
    _BASE, _ARM_OK,
    "      let mut sql := sql\n"
    '      sql := "NOT " ++ sql\n'
    "      return .ok (sql, params)",
)

# (drop-params-ok) Correct fragment in both forms, but the inner bind parameters
# are dropped instead of passed through. Isolates the parameter component of
# C-OK.
_R_DROPPARAMS = _swap(
    _BASE, _ARM_OK,
    "      let mut sql := sql\n"
    "      if negated then\n"
    '        sql := "NOT " ++ sql\n'
    "      return .ok (sql, [])",
)

# (prefix-text-nearmiss) The negation IS applied conditionally, on the right side
# of the dispatch, and the parameters pass through — only the prefix TEXT is off
# by one character (the separating space is missing). Added by audit: every other
# C-OK rival either drops the prefix wholesale or applies it unconditionally, so
# none of them pins the prefix STRING. Without this a rival that emits a
# run-together prefix — which changes the rendered predicate's meaning, since the
# negation would fuse onto the following token — satisfies every other witness in
# the lane.
_R_PREFIXTEXT = _swap(
    _BASE, _ARM_OK,
    "      let mut sql := sql\n"
    "      if negated then\n"
    '        sql := "NOT" ++ sql\n'
    "      return .ok (sql, params)",
)

# (params-reordered) The inner bind parameters are all still present, and the
# fragment is correct in both forms — but their ORDER is reversed. Added by
# audit: `drop-params-ok` pins only that the parameter list is not DISCARDED, so
# a rival that permutes it satisfies that witness. Bind parameters are
# positional, so order is part of the value the spec pins (`params` unchanged),
# not an incidental detail.
_R_PARAMSREV = _swap(
    _BASE, _ARM_OK,
    "      let mut sql := sql\n"
    "      if negated then\n"
    '        sql := "NOT " ++ sql\n'
    "      return .ok (sql, params.reverse)",
)

# (params-deduplicated) Every DISTINCT bind parameter is present, in the input's
# ORDER, and the fragment is correct in both forms — only repeated parameters are
# collapsed to one occurrence, so the list's MULTIPLICITY is wrong. Added by the
# second audit: `drop-params-ok` pins non-discard and `params-reordered` pins
# order, but BOTH of their witnesses (and every other `.ok` witness in the lane)
# use lists of DISTINCT tokens, which are fixed points of a dedup — so this rival
# satisfied all twelve shipped witnesses. Verified by building each of them
# against it: 12 of 12 elaborate, i.e. none discriminates it. Bind parameters are
# positional and a placeholder count must match its text, so multiplicity is part
# of the value the spec pins.
_R_PARAMSDEDUP = _swap(
    _BASE, _ARM_OK,
    "      let mut sql := sql\n"
    "      if negated then\n"
    '        sql := "NOT " ++ sql\n'
    "      return .ok (sql, params.dedup)",
)


# ===========================================================================
# ADMISSIBILITY POSITIVE — expect "verify"
# ===========================================================================
# The lean obligation carries no precondition hypothesis, so nagini's
# precondition-admission self-call has no direct analogue. Its analogue on a
# TOTAL carrier is the obligation being SATISFIABLE at exactly an F2P-shaped
# input, which this case tests directly: the impl's value at that input is pinned
# by evaluation (`rfl`, no `decide` — see the tactic note below), the spec
# predicate is then discharged AT that concrete input as a `have`, and only then
# is the frozen obligation closed verbatim. Both empty-result points are covered:
# the negated one (the F2P shape) and its non-negated companion (propagation).
#
# Nothing is assumed and nothing is restated: no new declaration, no new axiom,
# the `have`s are prepended INSIDE the existing tactic body, and the theorem
# STATEMENT is re-emitted byte-identically. If this failed to verify, the modeled
# behavior would be unsatisfiable at a normal input — the analogue of
# PRECOND-TOO-STRONG — which no other lane in this battery would detect.
_POS_ADMISS = _swap_proof(
    _BASE,
    _THM_STMT + "\n"
    "  have _f2p_value : implementation_compileExistenceCheck true (.error .emptyResult)\n"
    '      = .ok ("", []) := by\n'
    "    unfold implementation_compileExistenceCheck\n"
    "    rfl\n"
    "  have _f2p_ground : problem_spec_compileExistenceCheck true (.error .emptyResult)\n"
    "      (implementation_compileExistenceCheck true (.error .emptyResult)) := by\n"
    "    unfold problem_spec_compileExistenceCheck\n"
    "    rw [_f2p_value]\n"
    "    rfl\n"
    "  have _companion_value : implementation_compileExistenceCheck false (.error .emptyResult)\n"
    "      = .error .emptyResult := by\n"
    "    unfold implementation_compileExistenceCheck\n"
    "    rfl\n"
    "  have _companion_ground : problem_spec_compileExistenceCheck false (.error .emptyResult)\n"
    "      (implementation_compileExistenceCheck false (.error .emptyResult)) := by\n"
    "    unfold problem_spec_compileExistenceCheck\n"
    "    rw [_companion_value]\n"
    "    rfl\n"
    "  intro negated inner\n"
    "  unfold problem_spec_compileExistenceCheck implementation_compileExistenceCheck\n"
    "  match inner with\n"
    "  | .error .emptyResult => cases negated <;> rfl\n"
    "  | .error .other => rfl\n"
    "  | .ok (sql, params) => cases negated <;> rfl\n",
)


# --- witnesses (checked in a file with the frozen obligation removed) -------
# Each negates the spec predicate at ONE concrete input. The carrier is fully
# transparent, so no witness binds a hypothesis (there is nothing to be
# inconsistent). `simp` rather than `decide`: the `Decidable` instance does not
# reduce through the `Id.run do` join points, which would leave the witness
# vacuous (elaborating against gold too). Every one below was built both ways
# (rival exit 0, gold exit 1).

def _wit(negated: str, inner: str) -> str:
    return (
        "example : ¬ problem_spec_compileExistenceCheck\n"
        f"    {negated} {inner}\n"
        f"    (implementation_compileExistenceCheck {negated} {inner}) := by\n"
        "  unfold problem_spec_compileExistenceCheck implementation_compileExistenceCheck\n"
        "  simp"
    )


# negated + empty-result signal: gold => .ok ("", []), rival => .error .emptyResult.
_W_PROPAGATE = _wit("true", "(.error .emptyResult)")
# NON-negated + empty-result signal: gold propagates, rival => .ok ("", []).
_W_SWALLOW = _wit("false", "(.error .emptyResult)")
# negated + empty-result signal: gold's fragment is "", the rival's is "1=1".
_W_NONEMPTY = _wit("true", "(.error .emptyResult)")
# negated + empty-result signal: gold's parameters are [], the rival's are ["p"].
_W_FABPARAMS = _wit("true", "(.error .emptyResult)")
# negated + OTHER failure: gold propagates .error .other, rival => .ok ("", []).
_W_OTHERSWALLOW = _wit("true", "(.error .other)")
# NON-negated + OTHER failure: gold propagates .error .other, rival reports the
# empty-result signal instead. The only witness at (false, .other).
_W_OTHERASEMPTY = _wit("false", "(.error .other)")
# NON-negated success with a non-trivial fragment and two parameters: gold
# returns "s = 1", the rival returns "X".
_W_FABFRAG = _wit("false", '(.ok ("s = 1", ["p1", "p2"]))')
# negated success: gold returns "NOT s = 1", the rival the bare "s = 1".
_W_NOPREFIX = _wit("true", '(.ok ("s = 1", ["p1"]))')
# NON-negated success: gold returns "s = 1", the rival "NOT s = 1".
_W_PREFIXALWAYS = _wit("false", '(.ok ("s = 1", ["p1"]))')
# negated success with an EMPTY fragment and a two-element parameter list: the
# fragment component agrees with gold ("NOT " ++ "" on both sides), so this
# witness discriminates on the PARAMETER component alone — gold passes
# ["p1", "p2"] through, the rival returns [].
_W_DROPPARAMS = _wit("true", '(.ok ("", ["p1", "p2"]))')
# negated success: gold returns "NOT s = 1", the rival the run-together
# "NOTs = 1". Discriminates on the prefix TEXT with the prefix still applied
# conditionally and the parameters still passed through.
_W_PREFIXTEXT = _wit("true", '(.ok ("s = 1", ["p1"]))')
# negated success with TWO DISTINCT parameters, so a reversal is observable (a
# one-element or repeated list would be a fixed point of `reverse` and the
# witness would be vacuous). Fragment agrees with gold on both sides.
_W_PARAMSREV = _wit("true", '(.ok ("s = 1", ["p1", "p2"]))')
# negated success with a REPEATED parameter, which is what makes a dedup
# observable: every list of distinct tokens (including both lists used above) is
# a fixed point of `dedup`, so this is the only input in the lane at which a
# multiplicity-collapsing rival differs from the frozen impl at all. Fragment
# agrees with gold on both sides, so the refutation is attributable to the
# parameter component alone.
_W_PARAMSDEDUP = _wit("true", '(.ok ("s = 1", ["p1", "p1"]))')


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a structurally-different but CORRECT impl: a pure functional "
                  "expression (no `Id.run do`, no `let mut`) that chooses the "
                  "negation prefix with an inline conditional inside the returned "
                  "pair instead of mutating a local. Agrees with the frozen impl at "
                  "all six (negated, inner-constructor) points. The obligation is "
                  "re-proved for the new shape with a byte-identical theorem "
                  "statement (`intro`, `unfold`, then a match on `inner` with "
                  "`cases negated <;> rfl` on the empty-result arm). Verified with "
                  "scripts/lean_verify.sh (exit 0). If it failed to verify, the spec "
                  "would be over-fit to the imperative shape => SPEC-TOO-STRONG."},
    {"id": "pos-negated-first", "kind": "soundness", "expect": "verify",
     "module": _POS_NEGFIRST,
     "rationale": "a second correct impl with the DISPATCH ORDER inverted: split on "
                  "`negated` at the top level and match the inner outcome inside "
                  "each branch, so the negation prefix is applied at the point of "
                  "construction and both failure arms are duplicated. A completely "
                  "different branch structure from the frozen impl, same behavior. "
                  "Proof re-closed by enumerating all six `negated, inner` cases with "
                  "`rfl`. Verified with scripts/lean_verify.sh (exit 0). If it failed "
                  "to verify, the spec would be over-fit to one branch order => "
                  "SPEC-TOO-STRONG."},

    # ---- admissibility positive (must VERIFY) ----
    {"id": "admiss-f2p-empty-signal", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "the obligation is SATISFIABLE at exactly an F2P-shaped input. "
                  "The frozen obligation carries no precondition hypothesis, so "
                  "the analogue on this total carrier is not 'the precondition "
                  "admits the input' but 'the postcondition is dischargeable "
                  "there': the impl's value at (negated = true, empty-result "
                  "signal) is pinned by EVALUATION (`unfold` then `rfl`), the spec "
                  "predicate is discharged AT that concrete input as a `have`, and "
                  "the frozen obligation is then closed verbatim. The non-negated "
                  "companion point (propagation) is discharged the same way, so "
                  "both empty-result points are covered. Nothing is assumed: no "
                  "new declaration, no new axiom, `have`s prepended inside the "
                  "existing tactic body, theorem statement byte-identical. If it "
                  "failed to verify, the modeled behavior would be unsatisfiable "
                  "at a normal input => PRECOND-TOO-STRONG, which no other lane "
                  "here would detect. Verified with scripts/lean_verify.sh "
                  "(exit 0). NOTE `decide` does NOT work in place of `rfl` here "
                  "(`failed to synthesize Decidable`, measured on this bundle): "
                  "the `Id.run do` block leaves a join-point-shaped term the "
                  "`Decidable` instance will not reduce through."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "propagate-negated-empty", "kind": "uniqueness", "expect": "reject",
     "module": _R_PROPAGATE, "witness": _W_PROPAGATE,
     "refinement": "this IS the pre-patch behavior. Its faithful real patch lets the "
                   "match-nothing signal escape a NEGATED existence test, so the "
                   "surrounding predicate is discarded wholesale instead of keeping "
                   "its other conditions; the F2P test asserts the surviving "
                   "conditions still select their row and instead observes an empty "
                   "result — it does NOT resolve. A verifying rival here is therefore "
                   "a true verify-does-not-imply-resolve break.",
     "rationale": "attacks C-EMPTY on the `negated = true` side: the spec pins "
                  "`result = .ok (\"\", [])` there, the rival propagates the signal. "
                  "Witness at (true, .error .emptyResult). Built both ways with "
                  "scripts/lean_verify.sh (rival exit 0, gold exit 1)."},
    {"id": "swallow-signal-always", "kind": "uniqueness", "expect": "reject",
     "module": _R_SWALLOW, "witness": _W_SWALLOW,
     "refinement": "its faithful real patch turns a NON-negated existence test over a "
                   "match-nothing subquery into a no-op contribution, so a predicate "
                   "that must select nothing instead leaves the surrounding filter "
                   "unconstrained and selects every row; the tests that assert an "
                   "existence test over an empty selection matches NOTHING would "
                   "fail — it does NOT resolve.",
     "rationale": "attacks C-EMPTY on the `negated = false` side, which the spec pins "
                  "to `.error .emptyResult` (propagation), i.e. the clause forbids a "
                  "normal result there. The mirror of propagate-negated-empty, and "
                  "the only rival that varies `negated` to false on this "
                  "constructor. Witness at (false, .error .emptyResult). Built both "
                  "ways (rival exit 0, gold exit 1)."},
    {"id": "nonempty-fragment", "kind": "uniqueness", "expect": "reject",
     "module": _R_NONEMPTY, "witness": _W_NONEMPTY,
     "refinement": "its faithful real patch renders an always-true predicate fragment "
                   "where the behavior demands a no-op contribution. That is not the "
                   "gold rendering, and it changes the emitted statement's shape on "
                   "every affected query, so the tests that compare the rendered "
                   "predicate (and any backend that rejects the injected fragment) "
                   "would differ from gold — it is not guaranteed to resolve, so a "
                   "rival verifying here would be a spec hole, not a second correct "
                   "fix.",
     "rationale": "attacks the FRAGMENT-CONTENT component of C-EMPTY: control flow is "
                  "correct (a normal result on the negated side) but the fragment is "
                  "non-empty where the spec pins exactly \"\". Collapses nagini's "
                  "three C3 rivals (junk / always-false / single-space), which on this "
                  "carrier all fail at the same input for the same reason "
                  "(String equality against \"\"). Witness at (true, .error "
                  ".emptyResult). Built both ways (rival exit 0, gold exit 1)."},
    {"id": "fabricate-params-empty", "kind": "uniqueness", "expect": "reject",
     "module": _R_FABPARAMS, "witness": _W_FABPARAMS,
     "refinement": "its faithful real patch attaches a bind parameter to a fragment "
                   "that has no placeholder for it, so the emitted statement's "
                   "parameter list no longer matches its text; execution fails or "
                   "binds the surrounding predicate's parameters at the wrong "
                   "positions, and the F2P test does NOT resolve.",
     "rationale": "attacks the PARAMETER component of C-EMPTY, which pins the "
                  "parameter list to `[]` independently of the fragment. Fragment is "
                  "correct, so no other witness in the lane would catch it. Witness "
                  "at (true, .error .emptyResult). Built both ways (rival exit 0, "
                  "gold exit 1)."},
    {"id": "other-failure-swallowed", "kind": "uniqueness", "expect": "reject",
     "module": _R_OTHERSWALLOW, "witness": _W_OTHERSWALLOW,
     "refinement": "its faithful real patch catches EVERY inner-render failure rather "
                   "than only the dedicated match-nothing signal, so a genuine render "
                   "error is silently converted into a no-op contribution: a broken "
                   "query renders as an unconstrained filter and returns rows instead "
                   "of surfacing the failure. Tests that assert the error surfaces "
                   "would fail — it does NOT resolve.",
     "rationale": "attacks C-OTHER (`result = .error .other`, for both values of "
                  "`negated`), i.e. the clause that only the dedicated signal is ever "
                  "special-cased. One of only two rivals reaching the `.error .other` "
                  "constructor; without it, over-broad failure handling would verify "
                  "unnoticed. Witness at (true, .error .other). Built both ways "
                  "(rival exit 0, gold exit 1)."},
    {"id": "other-as-empty-signal", "kind": "uniqueness", "expect": "reject",
     "module": _R_OTHERASEMPTY, "witness": _W_OTHERASEMPTY,
     "refinement": "its faithful real patch propagates a failure but re-labels it as "
                   "the dedicated match-nothing signal, so an unrelated render error "
                   "is interpreted upstream as 'this subquery matches no rows' and "
                   "silently rewrites the surrounding predicate instead of surfacing. "
                   "The tests that distinguish the two outcomes would fail — it does "
                   "NOT resolve.",
     "rationale": "attacks the failure-IDENTITY half of C-OTHER: the rival still "
                  "propagates a failure (so a spec that only pinned 'some failure "
                  "escapes' would admit it) but with the wrong constructor. The only "
                  "witness at (negated = false, .error .other), so it is also what "
                  "keeps the `negated` binder varied on this constructor. Built both "
                  "ways (rival exit 0, gold exit 1)."},
    {"id": "fabricate-fragment-ok", "kind": "uniqueness", "expect": "reject",
     "module": _R_FABFRAG, "witness": _W_FABFRAG,
     "refinement": "its faithful real patch discards the fragment the inner renderer "
                   "produced and emits a fabricated one (correctly negated when "
                   "needed), so every rendered existence test — negated or not — "
                   "carries the wrong text while its parameters still belong to the "
                   "discarded fragment; the tests that exercise a satisfiable "
                   "subquery would fail — it does NOT resolve.",
     "rationale": "attacks the FRAGMENT component of C-OK, which grounds the result "
                  "in the input binder (`result = .ok (… sql …, params)`). Nagini "
                  "needed a witness-unique companion here because its spec could only "
                  "name the renderer's output through an oracle; on this carrier the "
                  "fragment IS a bound variable of the input, so the clause is "
                  "grounded by construction and this degenerates into an ordinary "
                  "fabrication rival. Witness at (false, .ok (\"s = 1\", [\"p1\", "
                  "\"p2\"])) — a non-trivial fragment, so the substitution is "
                  "observable. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "drop-not-prefix", "kind": "uniqueness", "expect": "reject",
     "module": _R_NOPREFIX, "witness": _W_NOPREFIX,
     "refinement": "its faithful real patch never applies the textual negation, so a "
                   "negated existence test renders as its non-negated form and "
                   "selects the complement of the intended rows; the negated-form "
                   "tests would fail — it does NOT resolve.",
     "rationale": "attacks the negated half of C-OK (`if negated then \"NOT \" ++ sql`). "
                  "Witness at (true, .ok (\"s = 1\", [\"p1\"])) — a non-empty fragment, "
                  "so the missing prefix is observable. Built both ways (rival exit 0, "
                  "gold exit 1)."},
    {"id": "prefix-always", "kind": "uniqueness", "expect": "reject",
     "module": _R_PREFIXALWAYS, "witness": _W_PREFIXALWAYS,
     "refinement": "its faithful real patch applies the textual negation "
                   "unconditionally, so a plain existence test renders as its "
                   "negation and selects the complement rows; the non-negated tests "
                   "would fail — it does NOT resolve.",
     "rationale": "the mirror of drop-not-prefix: attacks the NON-negated half of "
                  "C-OK (`else sql`, no prefix). Witness at (false, .ok (\"s = 1\", "
                  "[\"p1\"])). Built both ways (rival exit 0, gold exit 1)."},
    {"id": "drop-params-ok", "kind": "uniqueness", "expect": "reject",
     "module": _R_DROPPARAMS, "witness": _W_DROPPARAMS,
     "refinement": "its faithful real patch renders the correct fragment text but "
                   "drops the inner renderer's bind parameters, so every placeholder "
                   "in the emitted statement is left unbound (or bound to the "
                   "surrounding predicate's parameters, shifted); any query whose "
                   "subquery carries parameters fails or returns wrong rows — it does "
                   "NOT resolve.",
     "rationale": "attacks the PARAMETER-passthrough component of C-OK, which the "
                  "spec pins to the input `params` unchanged in BOTH negated forms. "
                  "Witness at (true, .ok (\"\", [\"p1\", \"p2\"])): the fragment "
                  "component AGREES with gold at this point (\"NOT \" ++ \"\" on both "
                  "sides), so the refutation is attributable to the parameter "
                  "component alone and cannot be confused with a fragment-level "
                  "failure. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "prefix-text-nearmiss", "kind": "uniqueness", "expect": "reject",
     "module": _R_PREFIXTEXT, "witness": _W_PREFIXTEXT,
     "refinement": "its faithful real patch renders the negation run together "
                   "with the fragment it negates, so the emitted predicate is not "
                   "the gold text: the negation keyword fuses onto the following "
                   "token and the backend either rejects the statement or parses a "
                   "different predicate than intended. The tests that compare the "
                   "rendered negated predicate would differ from gold — it does "
                   "NOT resolve.",
     "rationale": "added by the audit. Attacks the prefix TEXT of C-OK, which the "
                  "spec pins to exactly \"NOT \" ++ sql. The prefix is still "
                  "applied conditionally and only on the negated side, and the "
                  "parameters still pass through, so neither drop-not-prefix nor "
                  "prefix-always nor either parameter rival discriminates it: the "
                  "shipped lane pinned WHETHER the prefix is applied but never "
                  "WHAT it is. Witness at (true, .ok (\"s = 1\", [\"p1\"])). Built "
                  "both ways (rival exit 0, gold exit 1)."},
    {"id": "params-reordered", "kind": "uniqueness", "expect": "reject",
     "module": _R_PARAMSREV, "witness": _W_PARAMSREV,
     "refinement": "its faithful real patch keeps every bind parameter but emits "
                   "them in the wrong ORDER, and bind parameters are positional: "
                   "each placeholder in the emitted statement is filled from the "
                   "wrong value, so a subquery carrying two or more parameters "
                   "silently matches the wrong rows (or fails on a type mismatch). "
                   "It does NOT resolve.",
     "rationale": "added by the audit. Attacks the ORDER half of C-OK's parameter "
                  "passthrough. drop-params-ok pins only that the list is not "
                  "DISCARDED — its witness is satisfied by any impl returning a "
                  "non-empty list — so a permuting rival was unattacked, even "
                  "though `result = .ok (…, params)` pins the list as a VALUE. "
                  "Witness at (true, .ok (\"s = 1\", [\"p1\", \"p2\"])): two "
                  "DISTINCT tokens, so the reversal is observable rather than a "
                  "fixed point. Built both ways (rival exit 0, gold exit 1)."},

    {"id": "params-deduplicated", "kind": "uniqueness", "expect": "reject",
     "module": _R_PARAMSDEDUP, "witness": _W_PARAMSDEDUP,
     "refinement": "its faithful real patch keeps every DISTINCT bind parameter, "
                   "in the input's order, and emits the correct fragment in both "
                   "forms — it only collapses repeated parameters to a single "
                   "occurrence. Bind parameters are positional and consumed one "
                   "per placeholder, so as soon as the same value legitimately "
                   "occurs twice the emitted list is SHORTER than the fragment "
                   "expects and every placeholder after the collapse is filled "
                   "from the wrong value (or the statement is rejected outright "
                   "for a parameter-count mismatch). It does NOT resolve.",
     "rationale": "added by the second audit, and the only genuine coverage gap it "
                  "found. drop-params-ok pins that the list is not DISCARDED and "
                  "params-reordered pins its ORDER, but MULTIPLICITY was "
                  "unattacked: every `.ok` witness in the shipped lane uses a list "
                  "of DISTINCT tokens, and such a list is a fixed point of a "
                  "multiplicity-collapsing map. Measured, not argued — each of the "
                  "twelve shipped witnesses was rebuilt against this rival and all "
                  "twelve ELABORATE, i.e. none discriminates it, while every other "
                  "wrong impl written during that audit was caught by three to six "
                  "of them. Witness at (true, .ok (\"s = 1\", [\"p1\", \"p1\"])): a "
                  "REPEATED token, the only shape at which the collapse is "
                  "observable, with the fragment agreeing with the frozen impl on "
                  "both sides so the refutation is attributable to the parameter "
                  "component alone. Built both ways (rival exit 0, gold exit 1 with "
                  "`unsolved goals ⊢ False`), and the claim-flipped forgery control "
                  "inverts both exit codes."},
]

# P2 adversarial audit — psf__requests-1724

Modeled function: request-method normalization at the top of `Session.request`
(`requests/sessions.py`, base_commit `1ba83c4`). Gold patch inserts
`method = builtin_str(method)` immediately before `Request(method = method.upper(), …)`.

Frozen spec:
```
problem_spec_normalizeMethod method result :=
  result.chars = method.chars.map Char.toUpper ∧ result.wide = false
```

Mechanical preconditions (re-run, not trusted from bundle):
- `Solution.lean` verifies, exit 0 (compiles, no sorry).
- `#print axioms correct_normalizeMethod` → `[propext]` only. No `sorryAx`, no
  custom axioms. Clean.
- `Solution_prepatch.lean` fails (exit 1) exactly on the `result.wide = false`
  clause: `(pure {…, wide := method.wide}).wide = false` — G-DIFF behavior, the
  prepatch buggy skeleton does not close. Confirmed.
- `python -m swebench_lean.markers` → exit 0 (spec-region byte identity holds
  between Solution.lean and Solution_prepatch.lean).

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

The frozen spec pins BOTH output components: `result.chars` is pinned to
`method.chars.map Char.toUpper` and `result.wide` is pinned to `false`. There is
zero residual degree of freedom — the spec is a total function graph. Any
`implementation_normalizeMethod` whose `correct_normalizeMethod` closes must
therefore be extensionally identical to the gold normalization on every input,
hence its refined patch produces the same observable method (uppercased native
string) and resolves.

Attack attempted: an alternative impl that mirrors a NON-resolving patch — it
upper-cases but does NOT coerce to native (keeps the input width):
```
def implementation_normalizeMethod (method : PyStr) : PyStr := Id.run do
  let mut m := method
  m := { m with chars := m.chars.map Char.toUpper }
  return m
```
This is the prepatch skeleton (a patch that omits the `builtin_str` fix → does
NOT resolve). Its proof fails with `⊢ method.wide = false` (cannot be closed,
verified). So no closing alt-impl that fails to resolve exists. G-EQ holds.

**Recorded machine verdict.** eq: 7 attacks re-run, none breaks the spec; positive control verifies

The section above is this audit round's own account of the role, argued in prose: where it quotes an attack it quotes it as illustration, and no outcome is recorded there for the individual re-runs it counts. The recorded sentence above and the paragraphs below are what the harness retained about them.

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

Working from the spec view alone (problem_spec + `PyStr` + no callee axioms),
I attempted a WRONG impl that returns the input chars unchanged (no uppercase),
native width:
```
def implementation_normalizeMethod (method : PyStr) : PyStr :=
  { chars := method.chars, wide := false }
```
Proof fails with unsolved goal `method.chars = List.map Char.toUpper method.chars`
(false in general — e.g. `['p']`). The spec's first conjunct pins the content to
the uppercased form, the second pins `wide = false`. Together they uniquely
determine the output as a function of the input, so NO wrong implementation can
close. Spec is biconditional-tight. TIGHT.

**Recorded machine verdict.** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

The section above is this audit round's own account of the role, argued in prose: where it quotes an attack it quotes it as illustration, and no outcome is recorded there for the individual re-runs it counts. The recorded sentence above and the paragraphs below are what the harness retained about them.

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

Verified against the real repo at base_commit:
- Buggy callee is literally `req = Request(method = method.upper(), …)` with no
  prior coercion (`requests/sessions.py`, confirmed via worktree-free
  `git show` of the bare mirror).
- `requests/compat.py`: under Py2 `builtin_str = str` (native byte str) while
  `str = unicode`; under Py3 `builtin_str = str`. So `builtin_str(m)` coerces a
  wide/unicode text string to a native byte string, identity on ASCII content —
  exactly the model `{ m with wide := false }`.
- `.upper()` on ASCII HTTP method tokens ⟷ `List.map Char.toUpper` (ASCII case
  fold), length-preserving, code-point-for-code-point identical on the modeled
  domain. `Char.toUpper` (ASCII-only) could diverge from full-Unicode
  `str.upper()` ONLY on non-ASCII input, which is outside the documented and
  G-CONF-enforced ASCII method-token domain.
- Order matches: model clears `wide` then maps `toUpper`, mirroring the patch's
  coerce-then-upper order (and the two ops are independent anyway).
- The discriminating `wide` flag is a Py2-only unicode/str distinction not
  runtime-observable on the Py3.9 testbed; the bundle correctly relegates it to
  G-DIFF (prepatch fails on it) rather than G-CONF runtime differential. This is
  an honest, documented faithfulness boundary, not drift. The model does not
  over-constrain relative to real behavior on its stated domain. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

The public `problem_statement` already states the exact buggy line
(`req.method = method.upper()`), diagnoses the cause ("u'POST' is infecting the
header with unicode when it should be a string"), and frames the fix (coerce the
method to a native string). The spec view (native-vs-wide normalization, upper
casing) reveals nothing beyond what the public statement discloses. `hints_text`
is empty and is not relied upon. NO-LEAKAGE.

## Verdicts
- G-EQ = pass (SOUND)
- G-PANEL = pass (TIGHT ∧ FAITHFUL ∧ NO-LEAKAGE)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

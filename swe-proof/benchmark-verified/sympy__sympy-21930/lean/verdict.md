# P2 adversarial audit — sympy__sympy-21930

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies. The three specs (problem_spec_tensorMarkup/bosonCreatorMarkup/fermionCreatorMarkup) are TOTAL, UNCONDITIONAL exact-string equalities (result = "<exact string>", universally quantified, no precondition guard) with NO consumed oracle axiom (joinNames is a plain def / A-reference). This is the tightest possible spec shape: any verifying impl must reproduce the gold output on every input. All 6 distinct wrong impls failed to close (exit 1) and each was independently disproved on a concrete witness via `decide` (disproof.lean exit 0), so no proof can close for any of them; there is nothing to materialize into a patch.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
   let mut lo := ""
   for i in lower do
     lo := lo ++ i
-  return "{" ++ sym ++ "^{" ++ up ++ "}_{" ++ lo ++ "}}"
+  return sym ++ "^{" ++ up ++ "}_{" ++ lo ++ "}"
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,7 +102,7 @@
 /-- Skeleton of the bosonic raising-token renderer: assemble the token from the
 state name and enclose it in a single outer brace pair. -/
 def implementation_bosonCreatorMarkup (name : String) : String := Id.run do
-  return "{b^\\dagger_{" ++ name ++ "}}"
+  return "{b^\\dagger_" ++ name ++ "}"
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
     (sym : String) (upper lower : List String) : String := Id.run do
   let mut up := ""
   for i in upper do
-    up := up ++ i
+    up := i ++ up
   let mut lo := ""
   for i in lower do
     lo := lo ++ i
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,7 +124,7 @@
 /-- Skeleton of the fermionic raising-token renderer: assemble the token from the
 state name and enclose it in a single outer brace pair. -/
 def implementation_fermionCreatorMarkup (name : String) : String := Id.run do
-  return "{a^\\dagger_{" ++ name ++ "}}"
+  return "{b^\\dagger_{" ++ name ++ "}}"
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
   let mut lo := ""
   for i in lower do
     lo := lo ++ i
-  return "{" ++ sym ++ "^{" ++ up ++ "}_{" ++ lo ++ "}}"
+  return "{{" ++ sym ++ "^{" ++ up ++ "}_{" ++ lo ++ "}}}"
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
   let mut lo := ""
   for i in lower do
     lo := lo ++ i
-  return "{" ++ sym ++ "^{" ++ up ++ "}_{" ++ lo ++ "}}"
+  return "{" ++ sym ++ "^{" ++ lo ++ "}_{" ++ up ++ "}}"
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Typeset-markup rendering of three second-quantization carriers.

Each carrier renders to a typeset markup token built from its own data. A bare
token whose body already carries a subscript (and, for the dagger operators, a
superscript) is ambiguous when the surrounding context appends a further
superscript: the trailing exponent would bind only to the last group of the
token rather than to the token as a whole. The desired behavior is therefore to
emit each token as ONE self-contained group — the entire token enclosed in a
single outer brace pair — so that any following exponent binds to the whole
token.

We model the three renderers value-level, as `String`:

* an indexed symbol with an upper index block and a lower index block,
  rendered `{<sym>^{<upper>}_{<lower>}}` where each index block is the in-order
  concatenation of its index names;
* a bosonic raising token rendered `{b^\dagger_{<name>}}`;
* a fermionic raising token rendered `{a^\dagger_{<name>}}`.

In every case the rendered string must be the inner token enclosed in a single
outer brace pair.
-/

-- axioms-start
/- No unchanged callee is consumed as a property axiom. Each renderer is a
self-contained value-level string construction over its own inputs (the symbol
text and the index/state names), modeled deeply below and validated against the
real renderers by the differential conformance check. -/
-- axioms-end

-- pure-start
/-- In-order concatenation of a list of index names, mirroring the empty-string
join `"".join(names)`. Front-recursive so it pairs with the accumulator loop in
`implementation_tensorMarkup`. -/
def joinNames : List String → String
  | [] => ""
  | x :: xs => x ++ joinNames xs
-- pure-end

-- post-conditions-start
/-- An indexed symbol renders to its inner token `<sym>^{<upper>}_{<lower>}`
(with each index block the in-order concatenation of its index names), enclosed
in a single outer brace pair. -/
def problem_spec_tensorMarkup
    (sym : String) (upper lower : List String) (result : String) : Prop :=
  result = "{" ++ sym ++ "^{" ++ joinNames upper ++ "}_{" ++ joinNames lower ++ "}}"
-- post-conditions-end

-- impl-start
/-- Skeleton of the indexed-symbol renderer: join the upper index names, join the
lower index names, then assemble the token and enclose it in a single outer brace
pair. -/
def implementation_tensorMarkup
    (sym : String) (upper lower : List String) : String := Id.run do
  let mut up := ""
  for i in upper do
    up := up ++ i
  let mut lo := ""
  for i in lower do
    lo := lo ++ i
  return "{" ++ sym ++ "^{" ++ up ++ "}_{" ++ lo ++ "}}"
-- impl-end

-- proof-start
/-- The accumulator loop `for i in xs do acc := acc ++ i` (in desugared `forIn`
form, generalized over the starting accumulator) appends the in-order
concatenation of `xs` to the initial accumulator. -/
theorem tensorMarkup_loop_eq (xs : List String) (init : String) :
    (forIn xs init (fun i r => pure (ForInStep.yield (r ++ i))) : Id String)
      = init ++ joinNames xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, joinNames, String.append_empty]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih]
    simp only [joinNames, String.append_assoc]

theorem correct_tensorMarkup :
    ∀ (sym : String) (upper lower : List String),
      problem_spec_tensorMarkup sym upper lower
        (implementation_tensorMarkup sym upper lower) := by
  intro sym upper lower
  unfold problem_spec_tensorMarkup implementation_tensorMarkup
  simp only [Id.run, bind]
  rw [tensorMarkup_loop_eq, tensorMarkup_loop_eq]
  simp only [String.empty_append, pure, String.append_assoc]
-- proof-end

-- post-conditions-start
/-- The bosonic raising token renders to `b^\dagger_{<name>}` enclosed in a
single outer brace pair. -/
def problem_spec_bosonCreatorMarkup (name : String) (result : String) : Prop :=
  result = "{b^\\dagger_{" ++ name ++ "}}"
-- post-conditions-end

-- impl-start
/-- Skeleton of the bosonic raising-token renderer: assemble the token from the
state name and enclose it in a single outer brace pair. -/
def implementation_bosonCreatorMarkup (name : String) : String := Id.run do
  return "{b^\\dagger_{" ++ name ++ "}}"
-- impl-end

-- proof-start
theorem correct_bosonCreatorMarkup :
    ∀ (name : String),
      problem_spec_bosonCreatorMarkup name
        (implementation_bosonCreatorMarkup name) := by
  intro name; rfl
-- proof-end

-- post-conditions-start
/-- The fermionic raising token renders to `a^\dagger_{<name>}` enclosed in a
single outer brace pair. -/
def problem_spec_fermionCreatorMarkup (name : String) (result : String) : Prop :=
  result = "{a^\\dagger_{" ++ name ++ "}}"
-- post-conditions-end

-- impl-start
/-- Skeleton of the fermionic raising-token renderer: assemble the token from the
state name and enclose it in a single outer brace pair. -/
def implementation_fermionCreatorMarkup (name : String) : String := Id.run do
  return "{a^\\dagger_{" ++ name ++ "}}"
-- impl-end

-- proof-start
theorem correct_fermionCreatorMarkup :
    ∀ (name : String),
      problem_spec_fermionCreatorMarkup name
        (implementation_fermionCreatorMarkup name) := by
  intro name; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Base commit worktree (de446c6d85).

SAME_SPEC: all 6 attacks + positive control return same_spec=True (spec_view collapses BOTH impl and proof regions on the lean backend, so only axioms/pure/post/spec regions must stay byte-identical — they do).

VERIFICATIONS (bash scripts/lean_verify.sh <f>), run concurrently in 2 batches of <=4:
- pos_control.lean exit=0 (verifies, empty output, no sorry).
- atk_1 (tensor drops outer braces = the prepatch bug) exit=1.
- atk_2 (boson missing inner '{' / brace, single-group token) exit=1.
- atk_3 (tensor reverses upper-join order: acc := i ++ up) exit=1.
- atk_4 (fermion echoes boson 'b' token instead of 'a') exit=1.
- atk_5 (tensor emits DOUBLE outer braces '{{...}}') exit=1.
- atk_6 (tensor swaps upper/lower index blocks) exit=1.
All 6 failures are genuine unsolved-goal elaboration errors on false string equalities (tails inspected) — NOT sorry (exit 3) and NOT timeout (exit 124).

GENUINE-FALSITY WITNESSES: disproof.lean encodes each wrong impl and proves `impl(witness) ≠ spec_rhs(witness)` by `decide` for all 6 (exit=0). E.g. atk_1: i1 "t" ["a"] ["i"] ≠ "{t^{a}_{i}}"; atk_2: i2 "0" ≠ "{b^\dagger_{0}}"; atk_6: swap on ["a"]/["i"]. So the specs genuinely reject every wrong impl; no proof (clean-axiom or otherwise) can exist for them. Therefore step-2 (materialize faithful patch + run_resolve) is VACUOUS — no verifying wrong impl exists to break the spec.

AXIOMS: `#print axioms` (axcheck.lean, exit 0): correct_tensorMarkup depends on [propext, Quot.sound]; correct_bosonCreatorMarkup and correct_fermionCreatorMarkup depend on no axioms. Clean — no sorryAx, no custom/bundle axiom.

REFINEMENT.MD AUDIT: every leg is I or A-reference; no kind-3. Tensor legs #1/#2 are A-reference (accumulator loop / joinNames == "".join([i.name for i in self.args[1|2]])), validated by axiom_check.py (G-AX). Legs #3 (tensor), boson #1, fermion #1 are I (identical concrete string assembly). A-reference correspondence CONFIRMED against real callees in secondquant.py: AntiSymmetricTensor._latex returns "{%s^{%s}_{%s}}" % (self.symbol, "".join([i.name for i in self.args[1]]), "".join([i.name for i in self.args[2]])); CreateBoson._latex returns "{b^\\dagger_{%s}}" % self.state.name; CreateFermion._latex returns "{a^\\dagger_{%s}}" % self.state.name. All match the gold Lean templates byte-for-byte, including the fixed single outer brace pair. No axiom is consumed (mapping.md/refinement.md 'conf_skip=false', joinNames is a def). A-legs mechanically covered by G-CONF/G-AX; R legs by type bijection in mapping.md.

CONCLUSION: verify⇒correct holds for this bundle. SOUND after 6 attacks run, none breaks it (none even verifies).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies. The three specs (problem_spec_tensorMarkup/bosonCreatorMarkup/fermionCreatorMarkup) are TOTAL, UNCONDITIONAL exact-string equalities (result = "<exact string>", universally quantified, no precondition guard) with NO consumed oracle axiom (joinNames is a plain def / A-reference). This is the tightest possible spec shape: any verifying impl must reproduce the gold output on every input. All 6 distinct wrong impls failed to close (exit 1) and each was independently disproved on a concrete witness via `decide` (disproof.lean exit 0), so no proof can close for any of them; there is nothing to materialize into a patch.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Typeset-markup rendering of three second-quantization carriers.

Each carrier renders to a typeset markup token built from its own data. A bare
token whose body already carries a subscript (and, for the dagger operators, a
superscript) is ambiguous when the surrounding context appends a further
superscript: the trailing exponent would bind only to the last group of the
token rather than to the token as a whole. The desired behavior is therefore to
emit each token as ONE self-contained group — the entire token enclosed in a
single outer brace pair — so that any following exponent binds to the whole
token.

We model the three renderers value-level, as `String`:

* an indexed symbol with an upper index block and a lower index block,
  rendered `{<sym>^{<upper>}_{<lower>}}` where each index block is the in-order
  concatenation of its index names;
* a bosonic raising token rendered `{b^\dagger_{<name>}}`;
* a fermionic raising token rendered `{a^\dagger_{<name>}}`.

In every case the rendered string must be the inner token enclosed in a single
outer brace pair.
-/

-- axioms-start
/- No unchanged callee is consumed as a property axiom. Each renderer is a
self-contained value-level string construction over its own inputs (the symbol
text and the index/state names), modeled deeply below and validated against the
real renderers by the differential conformance check. -/
-- axioms-end

-- pure-start
/-- In-order concatenation of a list of index names, mirroring the empty-string
join `"".join(names)`. Front-recursive so it pairs with the accumulator loop in
`implementation_tensorMarkup`. -/
def joinNames : List String → String
  | [] => ""
  | x :: xs => x ++ joinNames xs
-- pure-end

-- post-conditions-start
/-- An indexed symbol renders to its inner token `<sym>^{<upper>}_{<lower>}`
(with each index block the in-order concatenation of its index names), enclosed
in a single outer brace pair. -/
def problem_spec_tensorMarkup
    (sym : String) (upper lower : List String) (result : String) : Prop :=
  result = "{" ++ sym ++ "^{" ++ joinNames upper ++ "}_{" ++ joinNames lower ++ "}}"
-- post-conditions-end

-- impl-start
/-- Skeleton of the indexed-symbol renderer: join the upper index names, join the
lower index names, then assemble the token and enclose it in a single outer brace
pair. -/
def implementation_tensorMarkup
    (sym : String) (upper lower : List String) : String := Id.run do
  let mut up := ""
  for i in upper do
    up := up ++ i
  let mut lo := ""
  for i in lower do
    lo := lo ++ i
  return "{" ++ sym ++ "^{" ++ up ++ "}_{" ++ lo ++ "}}"
-- impl-end

-- proof-start
/-- The accumulator loop `for i in xs do acc := acc ++ i` (in desugared `forIn`
form, generalized over the starting accumulator) appends the in-order
concatenation of `xs` to the initial accumulator. -/
theorem tensorMarkup_loop_eq (xs : List String) (init : String) :
    (forIn xs init (fun i r => pure (ForInStep.yield (r ++ i))) : Id String)
      = init ++ joinNames xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, joinNames, String.append_empty]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih]
    simp only [joinNames, String.append_assoc]

theorem correct_tensorMarkup :
    ∀ (sym : String) (upper lower : List String),
      problem_spec_tensorMarkup sym upper lower
        (implementation_tensorMarkup sym upper lower) := by
  intro sym upper lower
  unfold problem_spec_tensorMarkup implementation_tensorMarkup
  simp only [Id.run, bind]
  rw [tensorMarkup_loop_eq, tensorMarkup_loop_eq]
  simp only [String.empty_append, pure, String.append_assoc]
-- proof-end

-- post-conditions-start
/-- The bosonic raising token renders to `b^\dagger_{<name>}` enclosed in a
single outer brace pair. -/
def problem_spec_bosonCreatorMarkup (name : String) (result : String) : Prop :=
  result = "{b^\\dagger_{" ++ name ++ "}}"
-- post-conditions-end

-- impl-start
/-- Skeleton of the bosonic raising-token renderer: assemble the token from the
state name and enclose it in a single outer brace pair. -/
def implementation_bosonCreatorMarkup (name : String) : String := Id.run do
  return "{b^\\dagger_{" ++ name ++ "}}"
-- impl-end

-- proof-start
theorem correct_bosonCreatorMarkup :
    ∀ (name : String),
      problem_spec_bosonCreatorMarkup name
        (implementation_bosonCreatorMarkup name) := by
  intro name; rfl
-- proof-end

-- post-conditions-start
/-- The fermionic raising token renders to `a^\dagger_{<name>}` enclosed in a
single outer brace pair. -/
def problem_spec_fermionCreatorMarkup (name : String) (result : String) : Prop :=
  result = "{a^\\dagger_{" ++ name ++ "}}"
-- post-conditions-end

-- impl-start
/-- Skeleton of the fermionic raising-token renderer: assemble the token from the
state name and enclose it in a single outer brace pair. -/
def implementation_fermionCreatorMarkup (name : String) : String := Id.run do
  return "{a^\\dagger_{" ++ name ++ "}}"
-- impl-end

-- proof-start
theorem correct_fermionCreatorMarkup :
    ∀ (name : String),
      problem_spec_fermionCreatorMarkup name
        (implementation_fermionCreatorMarkup name) := by
  intro name; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Base commit worktree (de446c6d85).

SAME_SPEC: all 6 attacks + positive control return same_spec=True (spec_view collapses BOTH impl and proof regions on the lean backend, so only axioms/pure/post/spec regions must stay byte-identical — they do).

VERIFICATIONS (bash scripts/lean_verify.sh <f>), run concurrently in 2 batches of <=4:
- pos_control.lean exit=0 (verifies, empty output, no sorry).
- atk_1 (tensor drops outer braces = the prepatch bug) exit=1.
- atk_2 (boson missing inner '{' / brace, single-group token) exit=1.
- atk_3 (tensor reverses upper-join order: acc := i ++ up) exit=1.
- atk_4 (fermion echoes boson 'b' token instead of 'a') exit=1.
- atk_5 (tensor emits DOUBLE outer braces '{{...}}') exit=1.
- atk_6 (tensor swaps upper/lower index blocks) exit=1.
All 6 failures are genuine unsolved-goal elaboration errors on false string equalities (tails inspected) — NOT sorry (exit 3) and NOT timeout (exit 124).

GENUINE-FALSITY WITNESSES: disproof.lean encodes each wrong impl and proves `impl(witness) ≠ spec_rhs(witness)` by `decide` for all 6 (exit=0). E.g. atk_1: i1 "t" ["a"] ["i"] ≠ "{t^{a}_{i}}"; atk_2: i2 "0" ≠ "{b^\dagger_{0}}"; atk_6: swap on ["a"]/["i"]. So the specs genuinely reject every wrong impl; no proof (clean-axiom or otherwise) can exist for them. Therefore step-2 (materialize faithful patch + run_resolve) is VACUOUS — no verifying wrong impl exists to break the spec.

AXIOMS: `#print axioms` (axcheck.lean, exit 0): correct_tensorMarkup depends on [propext, Quot.sound]; correct_bosonCreatorMarkup and correct_fermionCreatorMarkup depend on no axioms. Clean — no sorryAx, no custom/bundle axiom.

REFINEMENT.MD AUDIT: every leg is I or A-reference; no kind-3. Tensor legs #1/#2 are A-reference (accumulator loop / joinNames == "".join([i.name for i in self.args[1|2]])), validated by axiom_check.py (G-AX). Legs #3 (tensor), boson #1, fermion #1 are I (identical concrete string assembly). A-reference correspondence CONFIRMED against real callees in secondquant.py: AntiSymmetricTensor._latex returns "{%s^{%s}_{%s}}" % (self.symbol, "".join([i.name for i in self.args[1]]), "".join([i.name for i in self.args[2]])); CreateBoson._latex returns "{b^\\dagger_{%s}}" % self.state.name; CreateFermion._latex returns "{a^\\dagger_{%s}}" % self.state.name. All match the gold Lean templates byte-for-byte, including the fixed single outer brace pair. No axiom is consumed (mapping.md/refinement.md 'conf_skip=false', joinNames is a def). A-legs mechanically covered by G-CONF/G-AX; R legs by type bijection in mapping.md.

CONCLUSION: verify⇒correct holds for this bundle. SOUND after 6 attacks run, none breaks it (none even verifies).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the three second-quantization _latex renderers in sympy/physics/secondquant.py. Modeled at the correct boundary: the post-patch real callees (verified in worktree @ de446c6d, gold patch applied) are exactly AntiSymmetricTensor._latex -> '{%s^{%s}_{%s}}' % (self.symbol, ''.join(upper names), ''.join(lower names)); (b) CreateBoson._latex -> '{b^\dagger_{%s}}' % self.state.name; (c) CreateFermion._latex -> '{a^\dagger_{%s}}' % self.state.name.

The spec postconditions pin result to exactly '{'++sym++'^{'++joinNames upper++'}_{'++joinNames lower++'}}' and the two dagger variants, with joinNames == ''.join. These are byte-identical to the real templates. Differential test (Python shadow mirroring the Lean impl/spec vs the REAL patched _latex over each object's canonical args): 103,027 checks (boson/fermion/tensor), including digit and non-ASCII (α,β,ψ) names and empty index lists (0..4), 0 disagreements. So the modeled function AGREES with the real callee on every tested input; no input drives them apart.

Spec region byte-identical across all three prepatch variants (same_spec True/True/True with lean backend). Proof genuine: lean_verify exit 0; #print axioms clean — correct_tensorMarkup depends only on [propext, Quot.sound] (no sorryAx), the two dagger correctness proofs depend on no axioms. printer argument correctly not modeled (never read). Index objects' only observable contribution is .name, mapped to List String in argument order — faithful to canonicalization. No diverging input found; spec is neither too strong nor drifts from real behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rendered the consumer spec view via swebench_unified.markers.spec_view (lean backend). What the spec view discloses about the gold edit does not exceed the public problem_statement.

Public problem_statement already states BOTH the defect and the exact fix: the double-superscript rendering bug 'b^\dagger_{0}^{2}' and the remedy verbatim — 'It should be correct by adding curly brackets "{b^\dagger_{0}}^{2}"', i.e. wrap the token in one outer brace pair. hints_text is empty, so no reliance on hints.

Spec-view content checked line by line:
- Postconditions (problem_spec_*Markup) require each rendered token to equal the inner token enclosed in a single outer brace pair ('{'...'}'). This encodes the CORRECT (post-fix) output — but a behavioral post-condition stating the desired result is intrinsic to any faithful spec and is exactly the fix the problem_statement spells out in words. The consumer must still supply impl + proof; G-DIFF confirms the bare/brace-less prepatch variants (1/2/3) fail, so the spec is not solved by inspection.
- The docstring narrates pre-state (bare token, trailing exponent binds to last group) → desired single-group behavior. This is the same causal explanation the problem_statement gives; it introduces nothing gold-specific.
- No gold-diff line is reproduced; no diff markers; no patched file path (secondquant.py absent); patched repo symbols (AntiSymmetricTensor/CreateBoson/CreateFermion, self.args, self.state.name, _latex) are NOT echoed — the spec uses abstract *Markup identifiers and value-level String models. No bug/fix narration vocabulary (bug/fix/patch/regression/...).
- The spec covers three renderers while the problem_statement's minimal example only shows the bosonic 'b^\dagger'. This is a faithful generalization of the publicly-stated fix mechanism ('add curly brackets' to cure the double-superscript problem) to the structurally identical fermionic 'a^\dagger' token and the indexed-symbol token; it is not a gold-specific disclosure beyond the public statement's own general framing.

Mechanical G-LEAK recorded pass ('spec view clean', failures []); bundle is not relaxed (no RELAXED_LEAKAGE.md, meta status pass). My semantic review agrees: the spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

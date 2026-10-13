# P2 adversarial audit — sympy__sympy-23950

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `problem_spec_asSet c result := result = some c.setArg` is a total equality over abstract carrier types E S : Type. By parametricity the only S-typed inhabitant derivable from c is c.setArg (c.element : E does not typecheck — verified failing in atk_2), so the only two well-typed Option S values are `none` and `some c.setArg`. Every wrong impl (none / wrong-operand / control-flow-forced none) fails G-VERIFY; every verifying impl is definitionally forced to `some c.setArg`.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
 -- impl-start
 def implementation_asSet {E S : Type}
     (c : MembershipAssertion E S) : Option S := Id.run do
-  return some c.setArg
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
 -- impl-start
 def implementation_asSet {E S : Type}
     (c : MembershipAssertion E S) : Option S := Id.run do
-  return some c.setArg
+  return some c.element
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,7 +41,10 @@
 -- impl-start
 def implementation_asSet {E S : Type}
     (c : MembershipAssertion E S) : Option S := Id.run do
-  return some c.setArg
+  if (1 : Nat) = 0 then
+    return none
+  else
+    return some c.setArg
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,8 @@
 -- impl-start
 def implementation_asSet {E S : Type}
     (c : MembershipAssertion E S) : Option S := Id.run do
-  return some c.setArg
+  match c with
+  | { element := _, setArg := _ } => return none
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,7 +41,9 @@
 -- impl-start
 def implementation_asSet {E S : Type}
     (c : MembershipAssertion E S) : Option S := Id.run do
-  return some c.setArg
+  let mut r : Option S := none
+  r := some c.setArg
+  return r
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,7 +41,7 @@
 -- impl-start
 def implementation_asSet {E S : Type}
     (c : MembershipAssertion E S) : Option S := Id.run do
-  return some c.setArg
+  return (some c.setArg).orElse (fun _ => none)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,6 +41,7 @@
 -- impl-start
 def implementation_asSet {E S : Type}
     (c : MembershipAssertion E S) : Option S := Id.run do
+  let _ := c.element
   return some c.setArg
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Converting a membership assertion to the set it represents.

A membership assertion is a boolean-valued object built from two operands: an
`element` and a `setArg` (the set the element is asserted to belong to). Only
these two operands are retained — the conversion does not inspect the contents
of either.

Converting such an assertion to a set yields the set operand it was built with:
the result is always defined (a value is produced, never absent) and it is
exactly the `setArg` operand, unchanged. The element operand plays no role in
the result.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The conversion reads the object's own
-- stored set operand directly, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A membership assertion: the `element` asserted to belong to `setArg`.
`E` and `S` are abstract carrier types — the conversion is purely structural and
inspects neither operand's contents. -/
structure MembershipAssertion (E S : Type) where
  element : E
  setArg  : S
-- pure-end

-- post-conditions-start
/-- Converting a membership assertion to a set always produces a value (it is
`some _`, never `none`), and that value is exactly the assertion's set operand
`setArg`, taken verbatim from the input. -/
def problem_spec_asSet {E S : Type}
    (c : MembershipAssertion E S) (result : Option S) : Prop :=
  result = some c.setArg
-- post-conditions-end

-- impl-start
def implementation_asSet {E S : Type}
    (c : MembershipAssertion E S) : Option S := Id.run do
  return some c.setArg
-- impl-end

-- proof-start
theorem correct_asSet {E S : Type} :
    ∀ (c : MembershipAssertion E S),
      problem_spec_asSet c (implementation_asSet c) := by
  intro c
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True for all 7 attacks + positive control (impl-region-only edits; axioms/pure/pre/post byte-identical). Verify cmd: `bash scripts/lean_verify.sh <f>`.

### VERIFY RESULTS (run concurrently, batches of <=4):
- pos_control (gold `some c.setArg`): exit 0, `#print axioms correct_asSet` => 'does not depend on any axioms'.
- atk_1 (`return none`, the prepatch bug): exit 1 (FAIL) — proof `rfl` cannot close `none = some c.setArg`. Prepatch reproduced.
- atk_2 (`return some c.element`, wrong operand): exit 1 (FAIL) — type error, c.element : E not S.
- atk_4 (`match c => return none`, control-flow-forced none): exit 1 (FAIL).
- atk_3 (`if 1=0 then none else some setArg`, partial-domain echo): exit 0, clean axioms.
- atk_5 (mutable accumulator, control-flow-effect echo): exit 0, clean axioms.
- atk_6 (`(some setArg).orElse (fun _=>none)`, ungrounded-oracle-echo): exit 0, clean axioms.
- atk_7 (discard element then some setArg): exit 0, clean axioms.

All 5 verifying attacks (atk_3/5/6/7 + pos_control) have `#print axioms correct_asSet` => 'does not depend on any axioms' (clean). Each verifying attack is a definitional echo reducing to `some c.setArg`, so its faithful refined patch is the gold `return self.args[1]`.

RESOLVE EXECUTED (protocol step 2): run_resolve('sympy__sympy-23950', gold-equivalent patch, timeout=1800) => RESOLVED=True, completed=True, note='resolved'. Every verifying clean-axiom impl thus has a faithful patch that RESOLVES. No verify⇏correct break.

REFINEMENT AUDIT (step 3): refinement.md has a single leg tagged R (`return some c.setArg` ↦ `return self.args[1]`). No A-consumed/A-reference legs — the bundle declares/consumes NO axioms (axioms-start/end block empty; `#print axioms` confirms zero dependence; mapping.md §'Callee provenance' confirms self.args[1] is a plain attribute read of the object's own stored operand, not a separately-defined callee/axiom contract). No kind-3 legs. R/I correspondence to the real Contains.as_set holds. G-AX is a legitimate skip stub.

CONCLUSION: The spec is airtight — it pins the exact behavior via a total equality over abstract types; the only inhabitant of the codomain reachable from the input is c.setArg. Wrong impls cannot verify; verifying impls are semantically the gold and their faithful patch resolves. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `problem_spec_asSet c result := result = some c.setArg` is a total equality over abstract carrier types E S : Type. By parametricity the only S-typed inhabitant derivable from c is c.setArg (c.element : E does not typecheck — verified failing in atk_2), so the only two well-typed Option S values are `none` and `some c.setArg`. Every wrong impl (none / wrong-operand / control-flow-forced none) fails G-VERIFY; every verifying impl is definitionally forced to `some c.setArg`.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Converting a membership assertion to the set it represents.

A membership assertion is a boolean-valued object built from two operands: an
`element` and a `setArg` (the set the element is asserted to belong to). Only
these two operands are retained — the conversion does not inspect the contents
of either.

Converting such an assertion to a set yields the set operand it was built with:
the result is always defined (a value is produced, never absent) and it is
exactly the `setArg` operand, unchanged. The element operand plays no role in
the result.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The conversion reads the object's own
-- stored set operand directly, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A membership assertion: the `element` asserted to belong to `setArg`.
`E` and `S` are abstract carrier types — the conversion is purely structural and
inspects neither operand's contents. -/
structure MembershipAssertion (E S : Type) where
  element : E
  setArg  : S
-- pure-end

-- post-conditions-start
/-- Converting a membership assertion to a set always produces a value (it is
`some _`, never `none`), and that value is exactly the assertion's set operand
`setArg`, taken verbatim from the input. -/
def problem_spec_asSet {E S : Type}
    (c : MembershipAssertion E S) (result : Option S) : Prop :=
  result = some c.setArg
-- post-conditions-end

-- impl-start
def implementation_asSet {E S : Type}
    (c : MembershipAssertion E S) : Option S := Id.run do
  return some c.setArg
-- impl-end

-- proof-start
theorem correct_asSet {E S : Type} :
    ∀ (c : MembershipAssertion E S),
      problem_spec_asSet c (implementation_asSet c) := by
  intro c
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True for all 7 attacks + positive control (impl-region-only edits; axioms/pure/pre/post byte-identical). Verify cmd: `bash scripts/lean_verify.sh <f>`.

### VERIFY RESULTS (run concurrently, batches of <=4):
- pos_control (gold `some c.setArg`): exit 0, `#print axioms correct_asSet` => 'does not depend on any axioms'.
- atk_1 (`return none`, the prepatch bug): exit 1 (FAIL) — proof `rfl` cannot close `none = some c.setArg`. Prepatch reproduced.
- atk_2 (`return some c.element`, wrong operand): exit 1 (FAIL) — type error, c.element : E not S.
- atk_4 (`match c => return none`, control-flow-forced none): exit 1 (FAIL).
- atk_3 (`if 1=0 then none else some setArg`, partial-domain echo): exit 0, clean axioms.
- atk_5 (mutable accumulator, control-flow-effect echo): exit 0, clean axioms.
- atk_6 (`(some setArg).orElse (fun _=>none)`, ungrounded-oracle-echo): exit 0, clean axioms.
- atk_7 (discard element then some setArg): exit 0, clean axioms.

All 5 verifying attacks (atk_3/5/6/7 + pos_control) have `#print axioms correct_asSet` => 'does not depend on any axioms' (clean). Each verifying attack is a definitional echo reducing to `some c.setArg`, so its faithful refined patch is the gold `return self.args[1]`.

RESOLVE EXECUTED (protocol step 2): run_resolve('sympy__sympy-23950', gold-equivalent patch, timeout=1800) => RESOLVED=True, completed=True, note='resolved'. Every verifying clean-axiom impl thus has a faithful patch that RESOLVES. No verify⇏correct break.

REFINEMENT AUDIT (step 3): refinement.md has a single leg tagged R (`return some c.setArg` ↦ `return self.args[1]`). No A-consumed/A-reference legs — the bundle declares/consumes NO axioms (axioms-start/end block empty; `#print axioms` confirms zero dependence; mapping.md §'Callee provenance' confirms self.args[1] is a plain attribute read of the object's own stored operand, not a separately-defined callee/axiom contract). No kind-3 legs. R/I correspondence to the real Contains.as_set holds. G-AX is a legitimate skip stub.

CONCLUSION: The spec is airtight — it pins the exact behavior via a total equality over abstract types; the only inhabitant of the codomain reachable from the input is c.setArg. Wrong impls cannot verify; verifying impls are semantically the gold and their faithful patch resolves. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. Real patched callee sympy/sets/contains.py Contains.as_set is unconditional `return self.args[1]` (verified worktree, gold applied). Spec problem_spec_asSet c result := (result = some c.setArg) models exactly: total (never none) + returns the stored set operand verbatim. MembershipAssertion carries the two operands with abstract carriers E/S; the fix is purely structural (attribute read of args[1]), so abstract carriers are faithful and the element operand correctly plays no role. Lean verified: lean_verify.sh exit 0, no sorry; `#print axioms correct_asSet` = does not depend on any axioms (real proof). same_spec(Solution, prepatch, LeanBackend.language)=True (spec region byte-identical). Empirically confirmed as_set() is args[1] for FiniteSet(y)/S.Integers/S.Reals/Interval(0,1). No post-patch exception path exists, so no input makes the modeled function disagree with the real callee. The Contains.eval collapse-to-True/False case is not the modeled method (not a Contains object) and is correctly excluded. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl + proof elided; confirmed via markers.spec_view with LeanBackend, and same_spec(Solution, prepatch)=True) contains only: an abstract prose docstring, the abstract-carrier structure `MembershipAssertion (E S : Type)` with fields `element`/`setArg`, and the post-condition `problem_spec_asSet c result := result = some c.setArg`.

Leakage screen (spec view vs. public problem_statement, excluding hints_text):
- Public problem_statement only describes the BUG (Contains.as_set wrongly returns a Contains; downstream as_relational fails). It does NOT state the intended fix — the 'should just return set' guidance lives exclusively in hints_text, which is out of scope for the public baseline.
- Gold edit: `raise NotImplementedError()` -> `return self.args[1]`.
- Spec view carries NO gold-patch identifiers (`self.args[1]`, `NotImplementedError`, `Contains`, `as_set`, `as_relational` all absent) and NO verbatim problem_statement phrasing (`Reals`, `Piecewise`, traceback absent). It uses only abstract Lean model names (`setArg`, `element`, `E`, `S`).
- The post-condition necessarily states the correct contract (result equals the set operand) — this is the intrinsic job of any specification and is not gold-patch disclosure; it discloses no Python-level 'how'. Implementation region (`some c.setArg`) and proof are elided from the view.

No spec-view line reconstructs the gold edit beyond a legitimate abstract contract. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

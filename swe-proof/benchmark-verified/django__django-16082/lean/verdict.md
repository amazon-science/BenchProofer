# P2 adversarial audit — django__django-16082

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_partial.lean`, `atk_3_boundary.lean`, `atk_4_controlflow.lean`, `atk_6_strict_match.lean`, `atk_7_none.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_resolveCombinedType op lhs rhs result := (result = resolveSpec op lhs rhs) is an EXACT total functional equation over the entire finite domain (6 ArithOp x 4 FieldKind x 4 FieldKind = 96 inputs). Any implementation whose correct_ closes is forced to equal resolveSpec pointwise, which pins the fixed behavior including the discriminating mixed-kind MOD promotion resolveSpec modOp integerKind decimalKind = some decimalKind. Every genuinely-wrong impl I built fails to close at exactly those discriminating inputs; the only same-spec impl that closes with clean axioms (atk_5_echo) literally returns resolveSpec and is behaviorally the gold-correct function, and its faithful patch RESOLVES (=True). Hence verify => correct holds; no verify-but-not-correct witness exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,7 +101,7 @@
   let mut combinators : List ComboRow := []
   if sameKindOps.contains op then
     combinators := combinators ++ sameKindRows
-  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
+  if ([ArithOp.add, .sub, .mul, .div] : List ArithOp).contains op then
     combinators := combinators ++ mixedKindRows
   for (clhs, crhs, combined) in combinators do
     if kindMatches lhs clhs && kindMatches rhs crhs then
```

Attack 2 — `atk_2_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,16 +97,19 @@
 
 -- impl-start
 def implementation_resolveCombinedType
-    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind := Id.run do
-  let mut combinators : List ComboRow := []
-  if sameKindOps.contains op then
-    combinators := combinators ++ sameKindRows
-  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
-    combinators := combinators ++ mixedKindRows
-  for (clhs, crhs, combined) in combinators do
-    if kindMatches lhs clhs && kindMatches rhs crhs then
-      return some combined
-  return none
+    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind :=
+  match op, lhs, rhs with
+  | .powOp, .autoKind, .autoKind => none
+  | _, _, _ => Id.run do
+      let mut combinators : List ComboRow := []
+      if sameKindOps.contains op then
+        combinators := combinators ++ sameKindRows
+      if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
+        combinators := combinators ++ mixedKindRows
+      for (clhs, crhs, combined) in combinators do
+        if kindMatches lhs clhs && kindMatches rhs crhs then
+          return some combined
+      return none
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,7 +102,12 @@
   if sameKindOps.contains op then
     combinators := combinators ++ sameKindRows
   if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
-    combinators := combinators ++ mixedKindRows
+    -- boundary tamper: reorder so a wrong row matches first for (int,decimal)
+    combinators := combinators ++
+      [(.integerKind, .decimalKind, .integerKind),
+       (.decimalKind, .integerKind, .decimalKind),
+       (.integerKind, .floatKind,   .floatKind),
+       (.floatKind,   .integerKind, .floatKind)]
   for (clhs, crhs, combined) in combinators do
     if kindMatches lhs clhs && kindMatches rhs crhs then
       return some combined
```

Attack 4 — `atk_4_controlflow.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,9 +103,9 @@
     combinators := combinators ++ sameKindRows
   if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
     combinators := combinators ++ mixedKindRows
-  for (clhs, crhs, combined) in combinators do
-    if kindMatches lhs clhs && kindMatches rhs crhs then
-      return some combined
+  -- control-flow bug: ignore the slot test, return the first row's kind if any row exists
+  for (_clhs, _crhs, combined) in combinators do
+    return some combined
   return none
 -- impl-end
 
```

Attack 5 — `atk_5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -97,16 +97,8 @@
 
 -- impl-start
 def implementation_resolveCombinedType
-    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind := Id.run do
-  let mut combinators : List ComboRow := []
-  if sameKindOps.contains op then
-    combinators := combinators ++ sameKindRows
-  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
-    combinators := combinators ++ mixedKindRows
-  for (clhs, crhs, combined) in combinators do
-    if kindMatches lhs clhs && kindMatches rhs crhs then
-      return some combined
-  return none
+    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind :=
+  resolveSpec op lhs rhs
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6_strict_match.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,7 @@
   if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
     combinators := combinators ++ mixedKindRows
   for (clhs, crhs, combined) in combinators do
-    if kindMatches lhs clhs && kindMatches rhs crhs then
+    if lhs == clhs && rhs == crhs then   -- strict equality: drops auto<:int subtype match
       return some combined
   return none
 -- impl-end
```

Attack 7 — `atk_7_none.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,16 +97,7 @@
 
 -- impl-start
 def implementation_resolveCombinedType
-    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind := Id.run do
-  let mut combinators : List ComboRow := []
-  if sameKindOps.contains op then
-    combinators := combinators ++ sameKindRows
-  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
-    combinators := combinators ++ mixedKindRows
-  for (clhs, crhs, combined) in combinators do
-    if kindMatches lhs clhs && kindMatches rhs crhs then
-      return some combined
-  return none
+    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind := none
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature: the only callee the modeled
-- function relies on is the runtime subclass test, which is reproduced concretely
-- as a total Boolean relation over the finite set of numeric field kinds (see the
-- `pure` region). Its agreement with the real subclass predicate is validated
-- executably (G-AX) rather than assumed, so the axioms region stays empty. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The numeric field kinds that participate in arithmetic-type resolution. -/
inductive FieldKind where
  | integerKind
  | floatKind
  | decimalKind
  | autoKind
  deriving DecidableEq, BEq, Repr

/-- The arithmetic operators whose result kind is resolved from the operand
kinds. -/
inductive ArithOp where
  | add
  | sub
  | mul
  | div
  | modOp
  | powOp
  deriving DecidableEq, BEq, Repr

/-- A registered combination row: a left operand kind, a right operand kind, and
the resulting kind. -/
abbrev ComboRow := FieldKind × FieldKind × FieldKind

/-- Operand-kind compatibility: a kind is accepted by a slot of kind `target`
when it is `target` itself, or a specialization of it. The only specialization
among the numeric kinds is that the auto-increment integer kind is a kind of
plain integer. Total and decidable — no runtime callee is assumed. -/
def kindMatches : FieldKind → FieldKind → Bool
  | .autoKind, .integerKind => true
  | a, b => a == b

/-- Rows registered for operations whose operands share the same kind. -/
def sameKindRows : List ComboRow :=
  [(.integerKind, .integerKind, .integerKind),
   (.floatKind,   .floatKind,   .floatKind),
   (.decimalKind, .decimalKind, .decimalKind)]

/-- Rows registered for operations that accept operands of mixed numeric kind,
promoting to the wider kind. -/
def mixedKindRows : List ComboRow :=
  [(.integerKind, .decimalKind, .decimalKind),
   (.decimalKind, .integerKind, .decimalKind),
   (.integerKind, .floatKind,   .floatKind),
   (.floatKind,   .integerKind, .floatKind)]

/-- Operators that support same-kind numeric operands. -/
def sameKindOps : List ArithOp := [.add, .sub, .mul, .div, .modOp, .powOp]

/-- Operators that promote operands of differing numeric kind to the wider kind:
addition, subtraction, multiplication, division, and remainder. Exponentiation is
not among them — a mixed-kind power has no registered promotion. -/
def mixedKindOps : List ArithOp := [.add, .sub, .mul, .div, .modOp]

/-- Scan registered rows in order, returning the result kind of the first row
whose operand slots both accept the given operand kinds. -/
def firstMatch : List ComboRow → FieldKind → FieldKind → Option FieldKind
  | [], _, _ => none
  | (clhs, crhs, combined) :: rest, lhs, rhs =>
      if kindMatches lhs clhs && kindMatches rhs crhs then some combined
      else firstMatch rest lhs rhs

/-- The combination rows registered for a given operator, same-kind rows first,
then mixed-kind rows (the registration order). -/
def combosFor (op : ArithOp) : List ComboRow :=
  (if sameKindOps.contains op then sameKindRows else []) ++
  (if mixedKindOps.contains op then mixedKindRows else [])

/-- The result kind an operator yields for the given operand kinds: the first
registered combination that accepts both operands, or none. -/
def resolveSpec (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind :=
  firstMatch (combosFor op) lhs rhs
-- pure-end

-- post-conditions-start
/-- The resolved result kind is exactly the first registered combination for the
operator whose two operand slots both accept the operand kinds (or none when no
registered combination accepts them). This pins the result for every operator and
operand-kind pair — including mixed numeric kinds under the remainder operator,
which must promote to the wider kind. -/
def problem_spec_resolveCombinedType
    (op : ArithOp) (lhs rhs : FieldKind) (result : Option FieldKind) : Prop :=
  result = resolveSpec op lhs rhs
-- post-conditions-end

-- impl-start
def implementation_resolveCombinedType
    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind := Id.run do
  let mut combinators : List ComboRow := []
  if sameKindOps.contains op then
    combinators := combinators ++ sameKindRows
  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
    combinators := combinators ++ mixedKindRows
  for (clhs, crhs, combined) in combinators do
    if kindMatches lhs clhs && kindMatches rhs crhs then
      return some combined
  return none
-- impl-end

-- proof-start
theorem correct_resolveCombinedType :
    ∀ (op : ArithOp) (lhs rhs : FieldKind),
    problem_spec_resolveCombinedType op lhs rhs
      (implementation_resolveCombinedType op lhs rhs) := by
  intro op lhs rhs
  cases op <;> cases lhs <;> cases rhs <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: same_spec(Solution.lean, atk_N) == True for all 7 attacks + pos_control (swebench_unified.markers.same_spec, lean backend). Only the impl region was edited; axioms/pure/pre/post byte-identical. axioms region is EMPTY, pure region fully concrete.

VERIFY COMMANDS: bash scripts/lean_verify.sh <file> (run concurrently, <=4 at a time, 2 batches).

### Results
- pos_control.lean: exit 0; #print axioms => [propext] (clean, no sorry/_prop). Positive control verifies.
- atk_1_prepatch (drop modOp from mixed-kind ops = the real prepatch bug): exit 1, genuine unsolved goal at case modOp.autoKind.decimalKind. PREPATCH REPRODUCED.
- atk_2_partial (partial-domain: override powOp autoKind autoKind => none): exit 1, unsolved goal at powOp.autoKind.autoKind.
- atk_3_boundary (wrong wider-kind: (int,decimal)->integerKind row first): exit 1, unsolved goal at modOp.autoKind.decimalKind.
- atk_4_controlflow (ignore slot test, return first row unconditionally): exit 1.
- atk_5_echo (return resolveSpec verbatim - ungrounded-oracle echo): exit 0; #print axioms => does not depend on any axioms (clean). CLOSES.
- atk_6_strict_match (use lhs==clhs && rhs==crhs, dropping auto<:int subtype match): exit 1.
- atk_7_none (degenerate: always none): exit 1.

CLOSING WRONG-IMPL RESOLVE CHECK (mandatory): only atk_5_echo closes with clean axioms. It returns resolveSpec, i.e. behaviorally the gold-correct fixed function (mixed-kind MOD promotes). Its faithful refined patch (add Combinable.MOD to the different-type numeric connector tuple = the gold edit) was materialized (patch_atk_5.diff) and RUN through the official harness: run_resolve(django__django-16082, patch, timeout=1800) => resolved=True, completed=True, attempts=1, flaky=False. FAIL_TO_PASS test_resolve_output_field_number and test_resolve_output_field_with_null both pass; all PASS_TO_PASS pass. Per the 2026-08-06 eq/panel_1 policy, a same-spec verifying impl whose refined patch RESOLVES is NOT a weakness (it is a resolving echo of the gold). So NO break: there is no impl with a closing clean-axiom proof whose faithful patch fails to resolve.

REFINEMENT.MD AUDIT: legs are R (#1 type refinement connector/class<->ArithOp/FieldKind; #3 changed op = adding modOp to mixedKindOps, modeled deeply NOT axiomatized), I (#2 same-type rows unchanged; #5 fall-off-loop -> none), A-reference (#4 kindMatches deep-models issubclass over the finite numeric lattice, validated == real issubclass by G-AX, concrete/decidable so proof consumes no _prop axiom). No A-consumed legs (axioms region empty; proof is structural cases <;> rfl). NO kind-3 legs. The single A-reference leg's correspondence holds: over the four modeled numeric kinds the only proper subclass relation is AutoField<:IntegerField (issubclass(Auto,Integer)==True), exactly matching kindMatches (.autoKind .integerKind => true; else a==b); consistent with mapping.md's empirically-verified issubclass lattice and the base-vs-patched behavior table.

CONCLUSION: The frozen spec is an exact functional equation that pins the fix pointwise; verify => resolve on this bundle. >=7 distinct wrong impls run (partial-domain, boundary, control-flow-effect, strict-match, degenerate, prepatch, plus resolving-echo); none breaks the spec. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_partial.lean`, `atk_3_boundary.lean`, `atk_4_controlflow.lean`, `atk_6_strict_match.lean`, `atk_7_none.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_resolveCombinedType op lhs rhs result := (result = resolveSpec op lhs rhs) is an EXACT total functional equation over the entire finite domain (6 ArithOp x 4 FieldKind x 4 FieldKind = 96 inputs). Any implementation whose correct_ closes is forced to equal resolveSpec pointwise, which pins the fixed behavior including the discriminating mixed-kind MOD promotion resolveSpec modOp integerKind decimalKind = some decimalKind. Every genuinely-wrong impl I built fails to close at exactly those discriminating inputs; the only same-spec impl that closes with clean axioms (atk_5_echo) literally returns resolveSpec and is behaviorally the gold-correct function, and its faithful patch RESOLVES (=True). Hence verify => correct holds; no verify-but-not-correct witness exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_controlflow.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_strict_match.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_none.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature: the only callee the modeled
-- function relies on is the runtime subclass test, which is reproduced concretely
-- as a total Boolean relation over the finite set of numeric field kinds (see the
-- `pure` region). Its agreement with the real subclass predicate is validated
-- executably (G-AX) rather than assumed, so the axioms region stays empty. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The numeric field kinds that participate in arithmetic-type resolution. -/
inductive FieldKind where
  | integerKind
  | floatKind
  | decimalKind
  | autoKind
  deriving DecidableEq, BEq, Repr

/-- The arithmetic operators whose result kind is resolved from the operand
kinds. -/
inductive ArithOp where
  | add
  | sub
  | mul
  | div
  | modOp
  | powOp
  deriving DecidableEq, BEq, Repr

/-- A registered combination row: a left operand kind, a right operand kind, and
the resulting kind. -/
abbrev ComboRow := FieldKind × FieldKind × FieldKind

/-- Operand-kind compatibility: a kind is accepted by a slot of kind `target`
when it is `target` itself, or a specialization of it. The only specialization
among the numeric kinds is that the auto-increment integer kind is a kind of
plain integer. Total and decidable — no runtime callee is assumed. -/
def kindMatches : FieldKind → FieldKind → Bool
  | .autoKind, .integerKind => true
  | a, b => a == b

/-- Rows registered for operations whose operands share the same kind. -/
def sameKindRows : List ComboRow :=
  [(.integerKind, .integerKind, .integerKind),
   (.floatKind,   .floatKind,   .floatKind),
   (.decimalKind, .decimalKind, .decimalKind)]

/-- Rows registered for operations that accept operands of mixed numeric kind,
promoting to the wider kind. -/
def mixedKindRows : List ComboRow :=
  [(.integerKind, .decimalKind, .decimalKind),
   (.decimalKind, .integerKind, .decimalKind),
   (.integerKind, .floatKind,   .floatKind),
   (.floatKind,   .integerKind, .floatKind)]

/-- Operators that support same-kind numeric operands. -/
def sameKindOps : List ArithOp := [.add, .sub, .mul, .div, .modOp, .powOp]

/-- Operators that promote operands of differing numeric kind to the wider kind:
addition, subtraction, multiplication, division, and remainder. Exponentiation is
not among them — a mixed-kind power has no registered promotion. -/
def mixedKindOps : List ArithOp := [.add, .sub, .mul, .div, .modOp]

/-- Scan registered rows in order, returning the result kind of the first row
whose operand slots both accept the given operand kinds. -/
def firstMatch : List ComboRow → FieldKind → FieldKind → Option FieldKind
  | [], _, _ => none
  | (clhs, crhs, combined) :: rest, lhs, rhs =>
      if kindMatches lhs clhs && kindMatches rhs crhs then some combined
      else firstMatch rest lhs rhs

/-- The combination rows registered for a given operator, same-kind rows first,
then mixed-kind rows (the registration order). -/
def combosFor (op : ArithOp) : List ComboRow :=
  (if sameKindOps.contains op then sameKindRows else []) ++
  (if mixedKindOps.contains op then mixedKindRows else [])

/-- The result kind an operator yields for the given operand kinds: the first
registered combination that accepts both operands, or none. -/
def resolveSpec (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind :=
  firstMatch (combosFor op) lhs rhs
-- pure-end

-- post-conditions-start
/-- The resolved result kind is exactly the first registered combination for the
operator whose two operand slots both accept the operand kinds (or none when no
registered combination accepts them). This pins the result for every operator and
operand-kind pair — including mixed numeric kinds under the remainder operator,
which must promote to the wider kind. -/
def problem_spec_resolveCombinedType
    (op : ArithOp) (lhs rhs : FieldKind) (result : Option FieldKind) : Prop :=
  result = resolveSpec op lhs rhs
-- post-conditions-end

-- impl-start
def implementation_resolveCombinedType
    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind := Id.run do
  let mut combinators : List ComboRow := []
  if sameKindOps.contains op then
    combinators := combinators ++ sameKindRows
  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then
    combinators := combinators ++ mixedKindRows
  for (clhs, crhs, combined) in combinators do
    if kindMatches lhs clhs && kindMatches rhs crhs then
      return some combined
  return none
-- impl-end

-- proof-start
theorem correct_resolveCombinedType :
    ∀ (op : ArithOp) (lhs rhs : FieldKind),
    problem_spec_resolveCombinedType op lhs rhs
      (implementation_resolveCombinedType op lhs rhs) := by
  intro op lhs rhs
  cases op <;> cases lhs <;> cases rhs <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: same_spec(Solution.lean, atk_N) == True for all 7 attacks + pos_control (swebench_unified.markers.same_spec, lean backend). Only the impl region was edited; axioms/pure/pre/post byte-identical. axioms region is EMPTY, pure region fully concrete.

VERIFY COMMANDS: bash scripts/lean_verify.sh <file> (run concurrently, <=4 at a time, 2 batches).

### Results
- pos_control.lean: exit 0; #print axioms => [propext] (clean, no sorry/_prop). Positive control verifies.
- atk_1_prepatch (drop modOp from mixed-kind ops = the real prepatch bug): exit 1, genuine unsolved goal at case modOp.autoKind.decimalKind. PREPATCH REPRODUCED.
- atk_2_partial (partial-domain: override powOp autoKind autoKind => none): exit 1, unsolved goal at powOp.autoKind.autoKind.
- atk_3_boundary (wrong wider-kind: (int,decimal)->integerKind row first): exit 1, unsolved goal at modOp.autoKind.decimalKind.
- atk_4_controlflow (ignore slot test, return first row unconditionally): exit 1.
- atk_5_echo (return resolveSpec verbatim - ungrounded-oracle echo): exit 0; #print axioms => does not depend on any axioms (clean). CLOSES.
- atk_6_strict_match (use lhs==clhs && rhs==crhs, dropping auto<:int subtype match): exit 1.
- atk_7_none (degenerate: always none): exit 1.

CLOSING WRONG-IMPL RESOLVE CHECK (mandatory): only atk_5_echo closes with clean axioms. It returns resolveSpec, i.e. behaviorally the gold-correct fixed function (mixed-kind MOD promotes). Its faithful refined patch (add Combinable.MOD to the different-type numeric connector tuple = the gold edit) was materialized (patch_atk_5.diff) and RUN through the official harness: run_resolve(django__django-16082, patch, timeout=1800) => resolved=True, completed=True, attempts=1, flaky=False. FAIL_TO_PASS test_resolve_output_field_number and test_resolve_output_field_with_null both pass; all PASS_TO_PASS pass. Per the 2026-08-06 eq/panel_1 policy, a same-spec verifying impl whose refined patch RESOLVES is NOT a weakness (it is a resolving echo of the gold). So NO break: there is no impl with a closing clean-axiom proof whose faithful patch fails to resolve.

REFINEMENT.MD AUDIT: legs are R (#1 type refinement connector/class<->ArithOp/FieldKind; #3 changed op = adding modOp to mixedKindOps, modeled deeply NOT axiomatized), I (#2 same-type rows unchanged; #5 fall-off-loop -> none), A-reference (#4 kindMatches deep-models issubclass over the finite numeric lattice, validated == real issubclass by G-AX, concrete/decidable so proof consumes no _prop axiom). No A-consumed legs (axioms region empty; proof is structural cases <;> rfl). NO kind-3 legs. The single A-reference leg's correspondence holds: over the four modeled numeric kinds the only proper subclass relation is AutoField<:IntegerField (issubclass(Auto,Integer)==True), exactly matching kindMatches (.autoKind .integerKind => true; else a==b); consistent with mapping.md's empirically-verified issubclass lattice and the base-vs-patched behavior table.

CONCLUSION: The frozen spec is an exact functional equation that pins the fix pointwise; verify => resolve on this bundle. >=7 distinct wrong impls run (partial-domain, boundary, control-flow-effect, strict-match, degenerate, prepatch, plus resolving-echo); none breaks the spec. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for the modeled function resolveSpec (the frozen spec: problem_spec_resolveCombinedType op lhs rhs result := result = resolveSpec op lhs rhs) against the real Django _resolve_combined_type at the base_commit with gold patch applied (expressions.py:622-628).

Method: transcribed the Lean spec (combosFor, kindMatches, sameKindOps=[add,sub,mul,div,modOp,powOp], mixedKindOps=[add,sub,mul,div,modOp], sameKindRows, mixedKindRows, firstMatch) into Python and compared against the live real function over the ENTIRE modeled domain = 6 arithmetic ops x 4 numeric FieldKinds (Integer/Float/Decimal/Auto) squared = 96 inputs. Result: 0 mismatches.

Corroborating facts:
- subclass lattice verified empirically against the real repo: only issubclass(AutoField, IntegerField)==True beyond reflexivity among the four numeric kinds -> exactly matches kindMatches (.autoKind .integerKind => true, else a==b).
- registration order (same-type dict then different-type dict) matches combosFor (sameKindRows ++ mixedKindRows); _connector_combinators is a defaultdict(list) appended in table order.
- the fix: gold patch adds Combinable.MOD to the different-type numeric connector tuple (expressions.py:524-540). Post-patch real MOD promotes mixed kinds (Int,Decimal)->Decimal, (Int,Float)->Float etc. The spec includes modOp in mixedKindOps -> agrees on every MOD case.
- POW is absent from the different-type tuple in the real repo; spec excludes powOp from mixedKindOps -> mixed-kind POW = none in both. Confirmed.

Spec integrity checks: same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical); lean_verify.sh exit 0; #print axioms correct_resolveCombinedType = [propext] only (no sorryAx, no _prop axiom), so the verified spec is genuinely resolveSpec.

Scope note: bitwise/date-time/NULL connectors and NoneType operands are outside the modeled ArithOp x numeric-FieldKind domain and are untouched by the fix; their exclusion is legitimate, not a faithfulness gap. The spec is not too strong: it pins exactly the real post-patch behavior over the modeled domain with no divergence found on any input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the Lean spec view (Solution.lean with impl+proof regions elided) against the PUBLIC problem_statement only (not hints_text). Gold edit = add `Combinable.MOD` to the different-type numeric connector tuple in django/db/models/expressions.py, i.e. mixed-kind MOD must promote to the wider numeric type like other arithmetic operators. The problem_statement already discloses this behavior fully ('MOD ... if the types are different (Decimal and Integer), it doesn't resolve the result to a Decimal type, like it does for other mathematical operators').

Mechanical G-LEAK screen: PASS (0 hard failures). Verified directly via leakage.screen: no diff markers; the gold-changed line 'Combinable.MOD,' is NOT reproduced (view is abstract Lean, not Python); no patched file path/module path; changed-symbol set is {'hash'} (from the `def __hash__` section header, non-distinctive) and does not appear; no narration terms (bug/fix/previously/etc.) in spec-view comments.

Semantic review: the spec is expressed entirely in abstract modeled types (FieldKind, ArithOp, combosFor, kindMatches, resolveSpec) — none of the actual Django repo symbols (_resolve_combined_type, _connector_combinations, Combinable, issubclass, register_combinable_fields, output_field, expressions.py) appear in the spec view. The post-condition docstring states MOD 'must promote to the wider kind' — but this is exactly the behavior the public problem_statement already specifies, not a disclosure of the edit's location or mechanism. The mention that exponentiation is excluded is a modeling-boundary note about an unedited operator and does not localize the fix. same_spec(Solution, Solution_prepatch)=True confirms the spec view is edit-neutral (prepatch shares the identical spec; only the elided impl differs). Nothing in the spec view reveals the gold edit beyond what the problem_statement already makes public.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-11815

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,10 +31,8 @@
 -- impl-start
 def implementation_serializeEnum
     (module className name payload : List Char) : List Char := Id.run do
-  -- The member's stored payload is no longer consulted when forming the text;
-  -- the member is referenced by its identifier as a quoted subscript.
-  let _ := payload
-  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
+  let _ := name
+  return module ++ ['.'] ++ className ++ ['('] ++ payload ++ [')']
 -- impl-end
 
 -- proof-start
@@ -44,5 +42,5 @@
       (implementation_serializeEnum module className name payload) := by
   intro module className name payload
   unfold problem_spec_serializeEnum implementation_serializeEnum
-  rfl
+  simp [quoted]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,10 +31,11 @@
 -- impl-start
 def implementation_serializeEnum
     (module className name payload : List Char) : List Char := Id.run do
-  -- The member's stored payload is no longer consulted when forming the text;
-  -- the member is referenced by its identifier as a quoted subscript.
   let _ := payload
-  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
+  if name = [] then
+    return module ++ ['.'] ++ className
+  else
+    return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
 -- impl-end
 
 -- proof-start
@@ -44,5 +45,6 @@
       (implementation_serializeEnum module className name payload) := by
   intro module className name payload
   unfold problem_spec_serializeEnum implementation_serializeEnum
-  rfl
+  simp [quoted]
+  cases name <;> simp
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,10 +31,8 @@
 -- impl-start
 def implementation_serializeEnum
     (module className name payload : List Char) : List Char := Id.run do
-  -- The member's stored payload is no longer consulted when forming the text;
-  -- the member is referenced by its identifier as a quoted subscript.
   let _ := payload
-  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
+  return module ++ ['.'] ++ className ++ ['['] ++ quoted name
 -- impl-end
 
 -- proof-start
@@ -44,5 +42,5 @@
       (implementation_serializeEnum module className name payload) := by
   intro module className name payload
   unfold problem_spec_serializeEnum implementation_serializeEnum
-  rfl
+  simp [quoted]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,10 +31,10 @@
 -- impl-start
 def implementation_serializeEnum
     (module className name payload : List Char) : List Char := Id.run do
-  -- The member's stored payload is no longer consulted when forming the text;
-  -- the member is referenced by its identifier as a quoted subscript.
-  let _ := payload
-  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
+  if payload = [] then
+    return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
+  else
+    return module ++ ['.'] ++ className ++ ['('] ++ payload ++ [')']
 -- impl-end
 
 -- proof-start
@@ -44,5 +44,6 @@
       (implementation_serializeEnum module className name payload) := by
   intro module className name payload
   unfold problem_spec_serializeEnum implementation_serializeEnum
-  rfl
+  simp [quoted]
+  cases payload <;> simp
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,10 +31,8 @@
 -- impl-start
 def implementation_serializeEnum
     (module className name payload : List Char) : List Char := Id.run do
-  -- The member's stored payload is no longer consulted when forming the text;
-  -- the member is referenced by its identifier as a quoted subscript.
   let _ := payload
-  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
+  return module ++ ['.'] ++ className ++ ['['] ++ (['"'] ++ name ++ ['"']) ++ [']']
 -- impl-end
 
 -- proof-start
@@ -44,5 +42,5 @@
       (implementation_serializeEnum module className name payload) := by
   intro module className name payload
   unfold problem_spec_serializeEnum implementation_serializeEnum
-  rfl
+  simp [quoted]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,10 +31,8 @@
 -- impl-start
 def implementation_serializeEnum
     (module className name payload : List Char) : List Char := Id.run do
-  -- The member's stored payload is no longer consulted when forming the text;
-  -- the member is referenced by its identifier as a quoted subscript.
   let _ := payload
-  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
+  return className ++ ['.'] ++ module ++ ['['] ++ quoted name ++ [']']
 -- impl-end
 
 -- proof-start
@@ -44,5 +42,5 @@
       (implementation_serializeEnum module className name payload) := by
   intro module className name payload
   unfold problem_spec_serializeEnum implementation_serializeEnum
-  rfl
+  simp [quoted]
 -- proof-end
```

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,10 +31,8 @@
 -- impl-start
 def implementation_serializeEnum
     (module className name payload : List Char) : List Char := Id.run do
-  -- The member's stored payload is no longer consulted when forming the text;
-  -- the member is referenced by its identifier as a quoted subscript.
   let _ := payload
-  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
+  return module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ name ++ ['\'']) ++ [']']
 -- impl-end
 
 -- proof-start
@@ -43,6 +41,6 @@
     problem_spec_serializeEnum module className name
       (implementation_serializeEnum module className name payload) := by
   intro module className name payload
-  unfold problem_spec_serializeEnum implementation_serializeEnum
+  unfold problem_spec_serializeEnum implementation_serializeEnum quoted
   rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The rendered reference text
-- is produced by substituting the carrier's parts into a constant literal
-- template; that substitution is reproduced concretely as an I op (an
-- order-preserving concatenation with literal punctuation), not abstracted behind
-- a model. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The quoted form of an identifier: the identifier wrapped in single quotes.
A reference identifier (which contains no quote characters) is rendered as the
identifier surrounded by a single-quote on each side. -/
def quoted (s : List Char) : List Char := ['\''] ++ s ++ ['\'']
-- pure-end

-- post-conditions-start
/-- The rendered reference text for a member of an enumerated type. It is the
qualifying module path, a dot, the type name, then the member selected by its
*identifier* written as a quoted subscript: an opening bracket, the quoted
identifier, and a closing bracket — in that order. Every component is pinned to
its input: the text is determined entirely by the module path, the type name,
and the member identifier; it does NOT depend on the member's stored payload. -/
def problem_spec_serializeEnum
    (module className name : List Char) (result : List Char) : Prop :=
  result = module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
-- post-conditions-end

-- impl-start
def implementation_serializeEnum
    (module className name payload : List Char) : List Char := Id.run do
  -- The member's stored payload is no longer consulted when forming the text;
  -- the member is referenced by its identifier as a quoted subscript.
  let _ := payload
  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
-- impl-end

-- proof-start
theorem correct_serializeEnum :
    ∀ (module className name payload : List Char),
    problem_spec_serializeEnum module className name
      (implementation_serializeEnum module className name payload) := by
  intro module className name payload
  unfold problem_spec_serializeEnum implementation_serializeEnum
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL SUMMARY. Spec is a TOTAL functional equation with no precondition, no oracle, no existential: problem_spec_serializeEnum module className name result := result = module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']. same_spec forces the axioms region byte-identical (empty). Any impl that closes correct_serializeEnum must equal gold on ALL inputs.

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently in two batches of 4; verdicts re-derived by the runner):
- pos_control.lean (gold impl): EXIT 0. `#print axioms correct_serializeEnum` => 'does not depend on any axioms' (clean).
- atk_1.lean  (prepatch bug: payload rendered as positional paren call '(payload)', identifier ignored): same_spec=True, EXIT 1, error 'unsolved goals' @42:70. PREPATCH REPRODUCED.
- atk_2.lean  (partial-domain: correct except returns '.className' with no subscript when name = []): same_spec=True, EXIT 1, 'unsolved goals' @45:70.
- atk_3.lean  (boundary: drops the closing ']'): same_spec=True, EXIT 1, 'unsolved goals' @42:70.
- atk_4.lean  (control-flow-effect: branches on payload emptiness — gold shape iff payload=[], else paren call): same_spec=True, EXIT 1, 'unsolved goals' @44:70.
- atk_5.lean  (ungrounded-oracle echo: uses double-quote ["] instead of single-quote around name): same_spec=True, EXIT 1, 'unsolved goals' @42:70.
- atk_6.lean  (wrong order: className and module swapped): same_spec=True, EXIT 1, 'unsolved goals' @42:70.
- atk_echo.lean (behaviorally EQUIVALENT: quoted inlined as ['\''] ++ name ++ ['\'']): same_spec=True, EXIT 0, clean axioms ('does not depend on any axioms'). Its faithful patch IS the gold patch (materialized above); it is a correct impl, so it correctly resolves — NOT a break.

All six wrong impls fail with genuine 'unsolved goals' (proof error, exit 1) — NOT sorry (exit 3) and NOT a tactic-syntax error (no 'unknown identifier'/'expected'). Because NO wrong impl closed with clean axioms, protocol step 2 triggers no falsifying resolve run: there is no verifying-but-wrong candidate to materialize. Only the equivalent echo and gold verify, and both faithfully map to the resolving gold patch.

REFINEMENT.MD AUDIT: rows 1-3 = R (str<->List Char bijection; the CHANGED op %r-of-identifier modeled deeply/concretely as `quoted`, NOT axiomatized), rows 4-6 = I (fixed-order concatenation into the literal template; payload dropped; imports set out of modeled scope). NO A-consumed, NO A-reference, NO kind-3 legs. mapping.md confirms the sole callee serializer_factory(self.value.value).serialize() is DELETED by the patch, so no UNCHANGED-callee property is consumed => empty axioms region is legitimate; G-AX is a correct skip stub. Correspondence to the real callee (%-substitution into '%s.%s[%r]') holds and is reproduced concretely.

VERDICT: SOUND. >=6 distinct same-spec wrong impls attacked; none closes. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The rendered reference text
-- is produced by substituting the carrier's parts into a constant literal
-- template; that substitution is reproduced concretely as an I op (an
-- order-preserving concatenation with literal punctuation), not abstracted behind
-- a model. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The quoted form of an identifier: the identifier wrapped in single quotes.
A reference identifier (which contains no quote characters) is rendered as the
identifier surrounded by a single-quote on each side. -/
def quoted (s : List Char) : List Char := ['\''] ++ s ++ ['\'']
-- pure-end

-- post-conditions-start
/-- The rendered reference text for a member of an enumerated type. It is the
qualifying module path, a dot, the type name, then the member selected by its
*identifier* written as a quoted subscript: an opening bracket, the quoted
identifier, and a closing bracket — in that order. Every component is pinned to
its input: the text is determined entirely by the module path, the type name,
and the member identifier; it does NOT depend on the member's stored payload. -/
def problem_spec_serializeEnum
    (module className name : List Char) (result : List Char) : Prop :=
  result = module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
-- post-conditions-end

-- impl-start
def implementation_serializeEnum
    (module className name payload : List Char) : List Char := Id.run do
  -- The member's stored payload is no longer consulted when forming the text;
  -- the member is referenced by its identifier as a quoted subscript.
  let _ := payload
  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']
-- impl-end

-- proof-start
theorem correct_serializeEnum :
    ∀ (module className name payload : List Char),
    problem_spec_serializeEnum module className name
      (implementation_serializeEnum module className name payload) := by
  intro module className name payload
  unfold problem_spec_serializeEnum implementation_serializeEnum
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL SUMMARY. Spec is a TOTAL functional equation with no precondition, no oracle, no existential: problem_spec_serializeEnum module className name result := result = module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']. same_spec forces the axioms region byte-identical (empty). Any impl that closes correct_serializeEnum must equal gold on ALL inputs.

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently in two batches of 4; verdicts re-derived by the runner):
- pos_control.lean (gold impl): EXIT 0. `#print axioms correct_serializeEnum` => 'does not depend on any axioms' (clean).
- atk_1.lean  (prepatch bug: payload rendered as positional paren call '(payload)', identifier ignored): same_spec=True, EXIT 1, error 'unsolved goals' @42:70. PREPATCH REPRODUCED.
- atk_2.lean  (partial-domain: correct except returns '.className' with no subscript when name = []): same_spec=True, EXIT 1, 'unsolved goals' @45:70.
- atk_3.lean  (boundary: drops the closing ']'): same_spec=True, EXIT 1, 'unsolved goals' @42:70.
- atk_4.lean  (control-flow-effect: branches on payload emptiness — gold shape iff payload=[], else paren call): same_spec=True, EXIT 1, 'unsolved goals' @44:70.
- atk_5.lean  (ungrounded-oracle echo: uses double-quote ["] instead of single-quote around name): same_spec=True, EXIT 1, 'unsolved goals' @42:70.
- atk_6.lean  (wrong order: className and module swapped): same_spec=True, EXIT 1, 'unsolved goals' @42:70.
- atk_echo.lean (behaviorally EQUIVALENT: quoted inlined as ['\''] ++ name ++ ['\'']): same_spec=True, EXIT 0, clean axioms ('does not depend on any axioms'). Its faithful patch IS the gold patch (materialized above); it is a correct impl, so it correctly resolves — NOT a break.

All six wrong impls fail with genuine 'unsolved goals' (proof error, exit 1) — NOT sorry (exit 3) and NOT a tactic-syntax error (no 'unknown identifier'/'expected'). Because NO wrong impl closed with clean axioms, protocol step 2 triggers no falsifying resolve run: there is no verifying-but-wrong candidate to materialize. Only the equivalent echo and gold verify, and both faithfully map to the resolving gold patch.

REFINEMENT.MD AUDIT: rows 1-3 = R (str<->List Char bijection; the CHANGED op %r-of-identifier modeled deeply/concretely as `quoted`, NOT axiomatized), rows 4-6 = I (fixed-order concatenation into the literal template; payload dropped; imports set out of modeled scope). NO A-consumed, NO A-reference, NO kind-3 legs. mapping.md confirms the sole callee serializer_factory(self.value.value).serialize() is DELETED by the patch, so no UNCHANGED-callee property is consumed => empty axioms region is legitimate; G-AX is a correct skip stub. Correspondence to the real callee (%-substitution into '%s.%s[%r]') holds and is reproduced concretely.

VERDICT: SOUND. >=6 distinct same-spec wrong impls attacked; none closes. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-11815 lean bundle.

Setup verified:
- same_spec(Solution.lean, Solution_prepatch.lean, lean_tables) => True: axioms/pure/post-conditions regions byte-identical between patched and prepatch.
- lean_verify.sh exit 0 (compiles, no sorry); #print axioms correct_serializeEnum => 'does not depend on any axioms' (no sorryAx, genuine proof by rfl).

Real callee: EnumSerializer.serialize at base_commit e02f67ef, patched to `'%s.%s[%r]' % (module, enum_class.__name__, self.value.name)` returning tuple[0]; payload path (serializer_factory(self.value.value).serialize()) deleted.

Spec: result = module ++ '.' ++ className ++ '[' ++ quoted name ++ ']' with quoted s = '\'' ++ s ++ '\'', payload discarded.

Modeling checks:
- The only non-identity op is %r of the member identifier modeled as wrapping in single quotes. Enum member names (class-syntax) are Python identifiers; repr of an identifier (incl. unicode letters, digits, underscore) is always single-quoted and never escaped since identifiers contain no quotes/backslashes. Empirically confirmed 0 divergence over 200k random identifiers including unicode ('unicode' with diacritics). So %r-name == 'name' on the entire modeled domain.
- module and className pass through unchanged (fixed-order concatenation with literal '.', '[', ']'). Faithful.
- Payload genuinely unused post-patch; spec's payload-independence matches. Faithful.
- conformance_check.py fuzz domain draws names from identifier chars only, matching the real Enum member-name domain; not overly narrow relative to the callee's actual domain.
- base_commit gold uses __name__ (not __qualname__ as in later commits); className models __name__ correctly. For nested enums __qualname__ would differ, but the gold at base_commit uses __name__, so the model tracks the actual patched behavior.

No input found where the modeled function disagrees with the real patched callee. The spec is not too strong and does not drift. Prepatch impl (paren/payload form) correctly fails to close against the frozen spec (G-DIFF present).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (axioms/pure/post-conditions regions) verified via markers.spec_view for lean backend; same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Lexical leakage.screen passes with zero hard_failures.

Gold edit for django-11815: EnumSerializer.serialize renders an enum member by its NAME as a quoted bracket subscript ('%s.%s[%r]' % (module, class, self.value.name)) instead of by its value in parens ('%s.%s(%s)'). The discriminating change is name-not-value + bracket-subscript form Class['NAME'].

This is ALREADY fully disclosed in the public problem_statement, which is unusually explicit: it states the migration 'uses the value of the Enum object instead of the its name', gives the buggy output default=Status('Good'), states 'It should be: default=Status['GOOD']', and asks that the generated code 'use the name of the Status Enum GOOD, not the value'. Both the target form (Class['NAME']) and the discriminating semantics (name not value; bracket subscript) are public.

The spec view's post-condition (result = module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']) and docstring ('member selected by its identifier written as a quoted subscript ... does NOT depend on the member's stored payload') encode exactly the behavior the problem_statement already dictates. No information beyond the public problem_statement is exposed: no hidden F2P test literals, no gold-patch-internal structure, no import-set details beyond the public issue. The module-path/dot prefix is generic serialization framing, not a gold discriminator. A faithful spec necessarily pins the target behavior; here that behavior is maximally public, so there is no leakage beyond problem_statement (and hints_text was not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

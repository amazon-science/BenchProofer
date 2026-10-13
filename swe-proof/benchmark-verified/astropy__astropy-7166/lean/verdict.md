# P2 adversarial audit — astropy__astropy-7166

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closes. Proven mechanically: the postcondition problem_spec_inheritDocstrings pins result.length = members.length AND, per index, key/isFunction/isDataDescriptor verbatim and doc = (if eligible then superDoc key else original doc). I independently re-proved spec_unique (meta_check.lean, EXIT=0, axioms [propext,Classical.choice,Quot.sound]) that the spec UNIQUELY determines the output list; hence any impl whose correct_ closes is observationally identical to the gold on every input and MUST produce post-patch behavior. Step 2 (materialize+resolve) is vacuous — zero verifying attacks.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
     (superDoc : List Char → Option (List Char)) : List Member := Id.run do
   let mut result : List Member := []
   for m in members do
-    if eligible m then
+    if m.isFunction && isPublicMember m.key && m.doc.isNone then
       result := result ++ [{ m with doc := superDoc m.key }]
     else
       result := result ++ [m]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,14 +79,8 @@
 
 -- impl-start
 def implementation_inheritDocstrings (members : List Member)
-    (superDoc : List Char → Option (List Char)) : List Member := Id.run do
-  let mut result : List Member := []
-  for m in members do
-    if eligible m then
-      result := result ++ [{ m with doc := superDoc m.key }]
-    else
-      result := result ++ [m]
-  return result
+    (superDoc : List Char → Option (List Char)) : List Member :=
+  members
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
     (superDoc : List Char → Option (List Char)) : List Member := Id.run do
   let mut result : List Member := []
   for m in members do
-    if eligible m then
+    if (m.isFunction || m.isDataDescriptor) && isPublicMember m.key then
       result := result ++ [{ m with doc := superDoc m.key }]
     else
       result := result ++ [m]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
     (superDoc : List Char → Option (List Char)) : List Member := Id.run do
   let mut result : List Member := []
   for m in members do
-    if eligible m then
+    if m.isDataDescriptor && isPublicMember m.key && m.doc.isNone then
       result := result ++ [{ m with doc := superDoc m.key }]
     else
       result := result ++ [m]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
   let mut result : List Member := []
   for m in members do
     if eligible m then
-      result := result ++ [{ m with doc := superDoc m.key }]
+      result := result ++ [{ m with doc := some ['X'] }]
     else
       result := result ++ [m]
   return result
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,14 +79,8 @@
 
 -- impl-start
 def implementation_inheritDocstrings (members : List Member)
-    (superDoc : List Char → Option (List Char)) : List Member := Id.run do
-  let mut result : List Member := []
-  for m in members do
-    if eligible m then
-      result := result ++ [{ m with doc := superDoc m.key }]
-    else
-      result := result ++ [m]
-  return result
+    (superDoc : List Char → Option (List Char)) : List Member :=
+  members.map (fun m => { m with doc := superDoc m.key })
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
     (superDoc : List Char → Option (List Char)) : List Member := Id.run do
   let mut result : List Member := []
   for m in members do
-    if eligible m then
+    if (m.isFunction || m.isDataDescriptor) && m.doc.isNone then
       result := result ++ [{ m with doc := superDoc m.key }]
     else
       result := result ++ [m]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Filling in missing documentation strings for the members of a freshly created
class from the base classes those members override.

When a class is built, each of its own members is examined. A member is a named
entry carrying three observable attributes: whether it is an ordinary callable,
whether it is a descriptor that mediates attribute access, and the documentation
string it currently has (which may be absent). For each *public* member that is
either a callable or such a descriptor and that currently has NO documentation
string of its own, the missing string is filled in from the corresponding member
resolved through the class's base classes (its inherited documentation, which may
itself be absent). Every other member, and every already-documented member, is
left exactly as it was — its name, its kind, and its documentation string are
unchanged.

A name counts as public when it is a dunder name (begins and ends with a double
underscore and is longer than four characters) or when it does not begin with a
single underscore.

The inherited documentation available to a member is supplied as part of the
input (the resolved view of the base classes); the desired behavior is stated
abstractly as an input→output relation. The implementation and correctness proof
are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The base-class resolution
-- (which documentation string a member would inherit) is supplied as an input
-- function, and the membership/eligibility test is spelled out concretely below;
-- so there is nothing to axiomatize.
-- axioms-end

-- pure-start
/-- A single class member: its name, whether it is an ordinary callable, whether
it is an attribute-access descriptor, and its current documentation string (if
any). -/
structure Member where
  key : List Char
  isFunction : Bool
  isDataDescriptor : Bool
  doc : Option (List Char)
deriving Inhabited, DecidableEq

/-- A name is public when it is a long dunder name (begins and ends with a
double underscore and has length > 4) or does not begin with a single
underscore. -/
def isPublicMember (key : List Char) : Bool :=
  (key.take 2 == ['_', '_'] && key.reverse.take 2 == ['_', '_'] && key.length > 4)
  || (key.head? != some '_')

/-- A member is eligible to have its missing documentation filled in when it is a
callable or an attribute-access descriptor, its name is public, and it has no
documentation string of its own. -/
def eligible (m : Member) : Bool :=
  (m.isFunction || m.isDataDescriptor) && isPublicMember m.key && m.doc.isNone
-- pure-end

-- post-conditions-start
/-- The result has one entry per input member, in the same order. For each
member: its name, its callable flag, and its descriptor flag are preserved
verbatim. Its documentation string is the inherited string `superDoc m.key`
exactly when the member is eligible (callable or descriptor, public, currently
undocumented), and is its original documentation string otherwise. -/
def problem_spec_inheritDocstrings (members : List Member)
    (superDoc : List Char → Option (List Char)) (result : List Member) : Prop :=
  result.length = members.length ∧
  (∀ i, i < members.length →
    (result.getD i default).key = (members.getD i default).key ∧
    (result.getD i default).isFunction = (members.getD i default).isFunction ∧
    (result.getD i default).isDataDescriptor = (members.getD i default).isDataDescriptor ∧
    (result.getD i default).doc =
      (if eligible (members.getD i default)
        then superDoc (members.getD i default).key
        else (members.getD i default).doc))
-- post-conditions-end

-- impl-start
def implementation_inheritDocstrings (members : List Member)
    (superDoc : List Char → Option (List Char)) : List Member := Id.run do
  let mut result : List Member := []
  for m in members do
    if eligible m then
      result := result ++ [{ m with doc := superDoc m.key }]
    else
      result := result ++ [m]
  return result
-- impl-end

-- proof-start
theorem correct_inheritDocstrings :
    ∀ (members : List Member) (superDoc : List Char → Option (List Char)),
      problem_spec_inheritDocstrings members superDoc
        (implementation_inheritDocstrings members superDoc) := by
  have helper : ∀ (members : List Member) (superDoc : List Char → Option (List Char)) (init : List Member),
      Id.run (forIn members init (fun m r =>
          (if eligible m = true then
            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))
          else
            pure (ForInStep.yield (r ++ [m]))))) =
        init ++ members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m) := by
    intro members superDoc init
    induction members generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil, Id.run]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : eligible a <;> simp [h, ih, List.append_assoc]
  intro members superDoc
  have key : implementation_inheritDocstrings members superDoc =
      members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m) := by
    show Id.run (forIn members ([] : List Member) (fun m r =>
          (if eligible m = true then
            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))
          else
            pure (ForInStep.yield (r ++ [m]))))) = _
    rw [helper]
    simp
  rw [key]
  refine ⟨by simp, ?_⟩
  intro i hi
  have hlen : i < (members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m)).length := by
    simpa using hi
  rw [List.getD_eq_getElem _ _ hlen, List.getD_eq_getElem _ _ hi, List.getElem_map]
  by_cases h : eligible members[i] <;> simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol results

same_spec (lean backend) = True for all 7 attacks + pos_control (impl region edited only; axioms/pure/pre/post byte-identical).

VERIFICATION (bash scripts/lean_verify.sh <f>), run concurrently (<=4 background jobs):
- pos_control.lean: EXIT=0, no sorry. #print axioms correct_inheritDocstrings = [propext, Classical.choice, Quot.sound] (clean). POSITIVE CONTROL PASSES.
- atk_1.lean (prepatch: isFunction only, drops isDataDescriptor): EXIT=1 (gold proof fails to close).
- atk_2.lean (identity, fills nothing): EXIT=1.
- atk_3.lean (drops doc.isNone guard, boundary): EXIT=1.
- atk_4.lean (isDataDescriptor only, partial-domain): EXIT=1.
- atk_5.lean (ungrounded-oracle echo, fills const ['X'] not superDoc): EXIT=1.
- atk_6.lean (ignores eligible, fills superDoc for all, control-flow-effect): EXIT=1.
- atk_7.lean (drops isPublicMember, fills private members, boundary): EXIT=1.
All wrong impls carrying the gold proof fail; errors are genuine ('show'/rfl pattern mismatch, unsolved goals) not timeouts.

### META-VERIFICATION (meta_check.lean / meta_axioms.lean, EXIT=0):
- spec_unique re-proved independently: postcondition pins length + 4 fields per index => output uniquely determined. axioms [propext,Classical.choice,Quot.sound].
- prepatch_violates_spec proved MANUALLY (native_decide unavailable due to superDoc function; used intro/obtain/decide on the concrete doc field at witness memBar={key=['b','a','r'],isFunction=false,isDataDescriptor=true,doc=none}, sd=fun _=>some ['B','A','R']). axioms [propext]. Confirms prepatch (isFunction-only) provably violates spec.
Because spec_unique holds, NO closing wrong impl can exist => step-2 resolve runs are vacuous (patches={}). This is why verify=>correct here.

### A-LEG AUDIT (refinement.md / mapping.md / axiom_check.py):
- No 'axiom'/'opaque'/'sorry' declared in Solution.lean. axiom_check.py = justified status=skip (no consumed callee axioms). Zero A-consumed legs (no kind-3).
- Two A-reference legs: (1) Member.isFunction/isDataDescriptor flags <-> inspect.isfunction/inspect.isdatadescriptor(val); (2) superDoc:List Char->Option (List Char) folds the UNCHANGED getattr/MRO walk (cls.__mro__[1:]) as an input function. Both validated == real callees by G-CONF (conformance_check.py, pinned seed 20240627), not axiomatized. Correspondence holds: eligible = (isFunction||isDataDescriptor)&&isPublicMember&&doc.isNone exactly mirrors the post-patch Python guard; isPublicMember mirrors is_public_member.
- Every refinement.md leg is R / A-reference / I. No kind-3.

Prepatch bug reproduced: Solution_prepatch.lean carries 1 sorry; atk_1 re-encodes the exact buggy guard and provably fails (EXIT=1), matching the FAIL_TO_PASS (test_inherit_docstrings, property inheriting base docstring).

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls attacked; positive control verifies clean; spec proven uniquely determining; no verifying wrong impl exists so no non-resolving faithful patch can exist; A-legs sound.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closes. Proven mechanically: the postcondition problem_spec_inheritDocstrings pins result.length = members.length AND, per index, key/isFunction/isDataDescriptor verbatim and doc = (if eligible then superDoc key else original doc). I independently re-proved spec_unique (meta_check.lean, EXIT=0, axioms [propext,Classical.choice,Quot.sound]) that the spec UNIQUELY determines the output list; hence any impl whose correct_ closes is observationally identical to the gold on every input and MUST produce post-patch behavior. Step 2 (materialize+resolve) is vacuous — zero verifying attacks.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Filling in missing documentation strings for the members of a freshly created
class from the base classes those members override.

When a class is built, each of its own members is examined. A member is a named
entry carrying three observable attributes: whether it is an ordinary callable,
whether it is a descriptor that mediates attribute access, and the documentation
string it currently has (which may be absent). For each *public* member that is
either a callable or such a descriptor and that currently has NO documentation
string of its own, the missing string is filled in from the corresponding member
resolved through the class's base classes (its inherited documentation, which may
itself be absent). Every other member, and every already-documented member, is
left exactly as it was — its name, its kind, and its documentation string are
unchanged.

A name counts as public when it is a dunder name (begins and ends with a double
underscore and is longer than four characters) or when it does not begin with a
single underscore.

The inherited documentation available to a member is supplied as part of the
input (the resolved view of the base classes); the desired behavior is stated
abstractly as an input→output relation. The implementation and correctness proof
are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The base-class resolution
-- (which documentation string a member would inherit) is supplied as an input
-- function, and the membership/eligibility test is spelled out concretely below;
-- so there is nothing to axiomatize.
-- axioms-end

-- pure-start
/-- A single class member: its name, whether it is an ordinary callable, whether
it is an attribute-access descriptor, and its current documentation string (if
any). -/
structure Member where
  key : List Char
  isFunction : Bool
  isDataDescriptor : Bool
  doc : Option (List Char)
deriving Inhabited, DecidableEq

/-- A name is public when it is a long dunder name (begins and ends with a
double underscore and has length > 4) or does not begin with a single
underscore. -/
def isPublicMember (key : List Char) : Bool :=
  (key.take 2 == ['_', '_'] && key.reverse.take 2 == ['_', '_'] && key.length > 4)
  || (key.head? != some '_')

/-- A member is eligible to have its missing documentation filled in when it is a
callable or an attribute-access descriptor, its name is public, and it has no
documentation string of its own. -/
def eligible (m : Member) : Bool :=
  (m.isFunction || m.isDataDescriptor) && isPublicMember m.key && m.doc.isNone
-- pure-end

-- post-conditions-start
/-- The result has one entry per input member, in the same order. For each
member: its name, its callable flag, and its descriptor flag are preserved
verbatim. Its documentation string is the inherited string `superDoc m.key`
exactly when the member is eligible (callable or descriptor, public, currently
undocumented), and is its original documentation string otherwise. -/
def problem_spec_inheritDocstrings (members : List Member)
    (superDoc : List Char → Option (List Char)) (result : List Member) : Prop :=
  result.length = members.length ∧
  (∀ i, i < members.length →
    (result.getD i default).key = (members.getD i default).key ∧
    (result.getD i default).isFunction = (members.getD i default).isFunction ∧
    (result.getD i default).isDataDescriptor = (members.getD i default).isDataDescriptor ∧
    (result.getD i default).doc =
      (if eligible (members.getD i default)
        then superDoc (members.getD i default).key
        else (members.getD i default).doc))
-- post-conditions-end

-- impl-start
def implementation_inheritDocstrings (members : List Member)
    (superDoc : List Char → Option (List Char)) : List Member := Id.run do
  let mut result : List Member := []
  for m in members do
    if eligible m then
      result := result ++ [{ m with doc := superDoc m.key }]
    else
      result := result ++ [m]
  return result
-- impl-end

-- proof-start
theorem correct_inheritDocstrings :
    ∀ (members : List Member) (superDoc : List Char → Option (List Char)),
      problem_spec_inheritDocstrings members superDoc
        (implementation_inheritDocstrings members superDoc) := by
  have helper : ∀ (members : List Member) (superDoc : List Char → Option (List Char)) (init : List Member),
      Id.run (forIn members init (fun m r =>
          (if eligible m = true then
            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))
          else
            pure (ForInStep.yield (r ++ [m]))))) =
        init ++ members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m) := by
    intro members superDoc init
    induction members generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil, Id.run]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : eligible a <;> simp [h, ih, List.append_assoc]
  intro members superDoc
  have key : implementation_inheritDocstrings members superDoc =
      members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m) := by
    show Id.run (forIn members ([] : List Member) (fun m r =>
          (if eligible m = true then
            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))
          else
            pure (ForInStep.yield (r ++ [m]))))) = _
    rw [helper]
    simp
  rw [key]
  refine ⟨by simp, ?_⟩
  intro i hi
  have hlen : i < (members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m)).length := by
    simpa using hi
  rw [List.getD_eq_getElem _ _ hlen, List.getD_eq_getElem _ _ hi, List.getElem_map]
  by_cases h : eligible members[i] <;> simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol results

same_spec (lean backend) = True for all 7 attacks + pos_control (impl region edited only; axioms/pure/pre/post byte-identical).

VERIFICATION (bash scripts/lean_verify.sh <f>), run concurrently (<=4 background jobs):
- pos_control.lean: EXIT=0, no sorry. #print axioms correct_inheritDocstrings = [propext, Classical.choice, Quot.sound] (clean). POSITIVE CONTROL PASSES.
- atk_1.lean (prepatch: isFunction only, drops isDataDescriptor): EXIT=1 (gold proof fails to close).
- atk_2.lean (identity, fills nothing): EXIT=1.
- atk_3.lean (drops doc.isNone guard, boundary): EXIT=1.
- atk_4.lean (isDataDescriptor only, partial-domain): EXIT=1.
- atk_5.lean (ungrounded-oracle echo, fills const ['X'] not superDoc): EXIT=1.
- atk_6.lean (ignores eligible, fills superDoc for all, control-flow-effect): EXIT=1.
- atk_7.lean (drops isPublicMember, fills private members, boundary): EXIT=1.
All wrong impls carrying the gold proof fail; errors are genuine ('show'/rfl pattern mismatch, unsolved goals) not timeouts.

### META-VERIFICATION (meta_check.lean / meta_axioms.lean, EXIT=0):
- spec_unique re-proved independently: postcondition pins length + 4 fields per index => output uniquely determined. axioms [propext,Classical.choice,Quot.sound].
- prepatch_violates_spec proved MANUALLY (native_decide unavailable due to superDoc function; used intro/obtain/decide on the concrete doc field at witness memBar={key=['b','a','r'],isFunction=false,isDataDescriptor=true,doc=none}, sd=fun _=>some ['B','A','R']). axioms [propext]. Confirms prepatch (isFunction-only) provably violates spec.
Because spec_unique holds, NO closing wrong impl can exist => step-2 resolve runs are vacuous (patches={}). This is why verify=>correct here.

### A-LEG AUDIT (refinement.md / mapping.md / axiom_check.py):
- No 'axiom'/'opaque'/'sorry' declared in Solution.lean. axiom_check.py = justified status=skip (no consumed callee axioms). Zero A-consumed legs (no kind-3).
- Two A-reference legs: (1) Member.isFunction/isDataDescriptor flags <-> inspect.isfunction/inspect.isdatadescriptor(val); (2) superDoc:List Char->Option (List Char) folds the UNCHANGED getattr/MRO walk (cls.__mro__[1:]) as an input function. Both validated == real callees by G-CONF (conformance_check.py, pinned seed 20240627), not axiomatized. Correspondence holds: eligible = (isFunction||isDataDescriptor)&&isPublicMember&&doc.isNone exactly mirrors the post-patch Python guard; isPublicMember mirrors is_public_member.
- Every refinement.md leg is R / A-reference / I. No kind-3.

Prepatch bug reproduced: Solution_prepatch.lean carries 1 sorry; atk_1 re-encodes the exact buggy guard and provably fails (EXIT=1), matching the FAIL_TO_PASS (test_inherit_docstrings, property inheriting base docstring).

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls attacked; positive control verifies clean; spec proven uniquely determining; no verifying wrong impl exists so no non-resolving faithful patch can exist; A-legs sound.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for astropy__astropy-7166 lean bundle. Modeled function = the per-member docstring-filling loop of InheritDocstrings.__init__ at astropy/utils/misc.py:523-540 @ base_commit 26d147868f (verified against real source via `git show 26d147868f:astropy/utils/misc.py`).

### Mechanical checks
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- #print axioms correct_inheritDocstrings -> [propext, Classical.choice, Quot.sound] only; no sorryAx => proof is genuine.
- same_spec(Solution, Solution_prepatch, LeanBackend.language) = True; the spec region (imports/pure/post-conditions/axioms) is byte-identical, only impl+proof differ.

### FAITHFULNESS OF SPEC vs REAL CALLEE:
1. isPublicMember matches real is_public_member on every edge case:
   - startswith('__') <-> key.take 2 == ['_','_'] (both False when len<2)
   - endswith('__') <-> key.reverse.take 2 == ['_','_'] (order-agnostic, correct)
   - len(key)>4 <-> key.length>4 (code-point count both sides)
   - not startswith('_') <-> key.head? != some '_' (empty key -> both public; leading '_' -> both non-public)
   Boundary keys '', 'a', '_a', '__', '___', '__ab__' all agree.
2. eligible = (isFunction || isDataDescriptor) && isPublicMember && doc.isNone exactly mirrors the POST-PATCH guard `(inspect.isfunction(val) or inspect.isdatadescriptor(val)) and is_public_member(key) and val.__doc__ is None`.
3. Frame is correct: the real metaclass only mutates val.__doc__ in place; namespace order and length of dct.items() are preserved, and key/isfunction/isdatadescriptor are never changed. The spec's postcondition preserves length, per-index key + both flags, and sets doc := superDoc(key) iff eligible else original doc.
4. superDoc (the unchanged getattr/MRO walk over cls.__mro__[1:]) is a FREE universally-quantified input function (A-reference). Because the theorem is proved for ALL superDoc, the spec cannot be too strong relative to the real MRO resolution — it is instantiated to whatever the real callee returns; correctness of that instantiation is a G-CONF concern (validated separately, seed 20240627), not a drift/too-strong concern.

No input was found on which the modeled function disagrees with the real InheritDocstrings.__init__ docstring-filling behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently reproduced. (1) same_spec(Solution_prepatch, Solution) = True via swebench_unified.markers + LeanBackend.language — spec view (problem_statement, structure, isPublicMember, eligible, post-condition) is byte-identical between the buggy and gold twins; the guard difference lives entirely in the elided impl/proof regions, so the projection is not tailored to the edit. (2) Mechanical leakage.screen (lean flavor, gold_patch + problem_statement only) returned 0 hard_failures, 0 warnings. Only patch-changed symbol extracted = {is_public_member} (a hunk-context helper, not the behavioral change), and it is absent from the spec view (spec uses camelCase isPublicMember). (3) Full spec-view scan: no diff markers, no patched file path (misc.py), no 'inspect.', no 'property'/'metaclass', no fix/bug/previously/was narration. Gold edit is guard widened from inspect.isfunction(val) to (inspect.isfunction(val) or inspect.isdatadescriptor(val)); inspect.isdatadescriptor is never named — the spec abstracts to symmetric boolean flags isFunction||isDataDescriptor and prose 'descriptor that mediates attribute access'. A solver cannot tell a change occurred nor which disjunct was added; the descriptor concept is already public via problem_statement ('doesn't work for properties' — a property IS a data descriptor). Including isDataDescriptor is required for spec adequacy, not a tell. mapping.md/refinement.md quote the literal gold diff but are private audit artifacts, not the solver-visible spec view. Solution.lean compiles (exit 0), axioms clean (propext, Classical.choice, Quot.sound; no sorryAx). No spec-view line reconstructs the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — sphinx-doc__sphinx-9698

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. problem_spec_getIndexText is a total function pinning result to exactly one string per input tuple in every branch (none-branch splits exclusively on modname=empty vs non-empty; some-branch covers all 8 Bool combos via chained implications classmethod / not-cm & prop / not-cm & not-prop & static / not-cm & not-prop & not-static). Any closing impl is therefore extensionally equal to gold; no verify-not-implies-correct gap. The single closing impl (atk_6, a behaviorally-equivalent echo) has faithful patch == gold edit, which RESOLVES=True.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,7 @@
     if isClassmethod then
       return methname ++ "() (" ++ clsname ++ " class method)"
     else if isProperty then
-      return methname ++ " (" ++ clsname ++ " property)"
+      return methname ++ "() (" ++ clsname ++ " property)"
     else if isStaticmethod then
       return methname ++ "() (" ++ clsname ++ " static method)"
     else
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,7 +88,7 @@
   | some (clsname0, methname) =>
     let mut clsname := clsname0
     if addModuleNames && modname != "" then
-      clsname := modname ++ "." ++ clsname0
+      clsname := clsname0
     if isClassmethod then
       return methname ++ "() (" ++ clsname ++ " class method)"
     else if isProperty then
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,10 +81,7 @@
     (isClassmethod isProperty isStaticmethod addModuleNames : Bool) : String := Id.run do
   match rsplitLastDot name with
   | none =>
-    if modname != "" then
-      return name ++ "() (in module " ++ modname ++ ")"
-    else
-      return name ++ "()"
+    return name ++ "()"
   | some (clsname0, methname) =>
     let mut clsname := clsname0
     if addModuleNames && modname != "" then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,10 +91,10 @@
       clsname := modname ++ "." ++ clsname0
     if isClassmethod then
       return methname ++ "() (" ++ clsname ++ " class method)"
+    else if isStaticmethod then
+      return methname ++ "() (" ++ clsname ++ " static method)"
     else if isProperty then
       return methname ++ " (" ++ clsname ++ " property)"
-    else if isStaticmethod then
-      return methname ++ "() (" ++ clsname ++ " static method)"
     else
       return methname ++ "() (" ++ clsname ++ " method)"
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
       return name ++ "()"
   | some (clsname0, methname) =>
     let mut clsname := clsname0
-    if addModuleNames && modname != "" then
+    if addModuleNames || modname != "" then
       clsname := modname ++ "." ++ clsname0
     if isClassmethod then
       return methname ++ "() (" ++ clsname ++ " class method)"
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -86,17 +86,12 @@
     else
       return name ++ "()"
   | some (clsname0, methname) =>
-    let mut clsname := clsname0
-    if addModuleNames && modname != "" then
-      clsname := modname ++ "." ++ clsname0
-    if isClassmethod then
-      return methname ++ "() (" ++ clsname ++ " class method)"
-    else if isProperty then
-      return methname ++ " (" ++ clsname ++ " property)"
-    else if isStaticmethod then
-      return methname ++ "() (" ++ clsname ++ " static method)"
-    else
-      return methname ++ "() (" ++ clsname ++ " method)"
+    let clsname := if addModuleNames && modname != "" then modname ++ "." ++ clsname0 else clsname0
+    match isClassmethod, isProperty, isStaticmethod with
+    | true,  _,     _     => return methname ++ "() (" ++ clsname ++ " class method)"
+    | false, true,  _     => return methname ++ " (" ++ clsname ++ " property)"
+    | false, false, true  => return methname ++ "() (" ++ clsname ++ " static method)"
+    | false, false, false => return methname ++ "() (" ++ clsname ++ " method)"
 -- impl-end
 
 -- proof-start
@@ -117,9 +112,6 @@
       exact if_pos hm
     · intro hm
       simp only [bne_iff_ne, hm, ne_eq, not_true_eq_false, if_false]
-  · refine ⟨?_, ?_, ?_, ?_⟩
-    · intro h; subst h; simp only [if_true]; split <;> rfl
-    · intro h1 h2; subst h1; subst h2; simp only; split <;> rfl
-    · intro h1 h2 h3; subst h1; subst h2; subst h3; simp only; split <;> rfl
-    · intro h1 h2 h3; subst h1; subst h2; subst h3; simp only; split <;> rfl
+  · cases isClassmethod <;> cases isProperty <;> cases isStaticmethod <;>
+      refine ⟨?_, ?_, ?_, ?_⟩ <;> intros <;> first | rfl | contradiction
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the index-entry label for a documented class member.

When a member of a class is documented, a single index entry is registered for
it. The text of that entry is assembled from:

  * the member's fully-qualified dotted name (e.g. `Class.member`), from which the
    leading class part and the trailing member part are separated at the final
    dot;
  * the enclosing module name, which may be empty;
  * a flag selecting whether the module name is prepended to the class part;
  * and the *kind* of member it is — an ordinary method, a class method, a static
    method, or a value-like attribute exposed without a call.

The label distinguishes the kinds with a parenthesised qualifier naming the
class. For the call-like kinds (ordinary method, class method, static method) the
member name is shown with an empty argument list appended, reflecting that the
member is invoked. For the value-like kind, the member is referred to by its bare
name, with no argument list, because it is accessed rather than called.

When the dotted name has no separating dot, the class part cannot be formed, and
the label falls back to naming the member alone (with an empty argument list),
optionally qualified by the module it lives in.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The dotted-name
-- separation, the optional module-name qualification, and the assembly of the
-- label are all modeled directly as string operations over the inputs; there is
-- no opaque callee whose contract the proof must assume.
-- axioms-end

-- pure-start
/-- Separate a dotted name at its FINAL dot, as a right split into two parts.
Returns `none` when the name contains no dot (no class part can be formed);
otherwise `some (before, after)` where `after` is the trailing segment and
`before` is everything preceding the final dot, rejoined with dots. -/
def rsplitLastDot (s : String) : Option (String × String) :=
  match (s.splitOn ".").reverse with
  | []        => none
  | [_]       => none
  | last :: rest => some (String.intercalate "." rest.reverse, last)
-- pure-end

-- post-conditions-start
/-- The index-entry label is fully pinned to the inputs in every case:

  * when the name has no separating dot, the label is the bare member name with an
    empty argument list, qualified by the module name when one is present;
  * when the name splits, the class part is the trailing-class component,
    optionally prefixed by the module name, and the label is one of four
    determined shapes selected by the member kind — the call-like kinds carry an empty
    argument list after the member name, the value-like kind does not.

Every branch determines the result, so no output component is left free. -/
def problem_spec_getIndexText (name modname : String)
    (isClassmethod isProperty isStaticmethod addModuleNames : Bool)
    (result : String) : Prop :=
  match rsplitLastDot name with
  | none =>
      (modname ≠ "" → result = name ++ "() (in module " ++ modname ++ ")") ∧
      (modname = "" → result = name ++ "()")
  | some (clsname0, methname) =>
      let clsname :=
        if addModuleNames && modname != "" then modname ++ "." ++ clsname0 else clsname0
      (isClassmethod = true →
          result = methname ++ "() (" ++ clsname ++ " class method)") ∧
      (isClassmethod = false → isProperty = true →
          result = methname ++ " (" ++ clsname ++ " property)") ∧
      (isClassmethod = false → isProperty = false → isStaticmethod = true →
          result = methname ++ "() (" ++ clsname ++ " static method)") ∧
      (isClassmethod = false → isProperty = false → isStaticmethod = false →
          result = methname ++ "() (" ++ clsname ++ " method)")
-- post-conditions-end

-- impl-start
def implementation_getIndexText (name modname : String)
    (isClassmethod isProperty isStaticmethod addModuleNames : Bool) : String := Id.run do
  match rsplitLastDot name with
  | none =>
    if modname != "" then
      return name ++ "() (in module " ++ modname ++ ")"
    else
      return name ++ "()"
  | some (clsname0, methname) =>
    let mut clsname := clsname0
    if addModuleNames && modname != "" then
      clsname := modname ++ "." ++ clsname0
    if isClassmethod then
      return methname ++ "() (" ++ clsname ++ " class method)"
    else if isProperty then
      return methname ++ " (" ++ clsname ++ " property)"
    else if isStaticmethod then
      return methname ++ "() (" ++ clsname ++ " static method)"
    else
      return methname ++ "() (" ++ clsname ++ " method)"
-- impl-end

-- proof-start
theorem correct_getIndexText :
    ∀ (name modname : String)
      (isClassmethod isProperty isStaticmethod addModuleNames : Bool),
      problem_spec_getIndexText name modname
        isClassmethod isProperty isStaticmethod addModuleNames
        (implementation_getIndexText name modname
          isClassmethod isProperty isStaticmethod addModuleNames) := by
  intro name modname isClassmethod isProperty isStaticmethod addModuleNames
  unfold problem_spec_getIndexText implementation_getIndexText
  simp only [Id.run, bind, pure]
  split
  · constructor
    · intro hm
      simp only [bne_iff_ne]
      exact if_pos hm
    · intro hm
      simp only [bne_iff_ne, hm, ne_eq, not_true_eq_false, if_false]
  · refine ⟨?_, ?_, ?_, ?_⟩
    · intro h; subst h; simp only [if_true]; split <;> rfl
    · intro h1 h2; subst h1; subst h2; simp only; split <;> rfl
    · intro h1 h2 h3; subst h1; subst h2; subst h3; simp only; split <;> rfl
    · intro h1 h2 h3; subst h1; subst h2; subst h3; simp only; split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

python=python. same_spec=True verified for all 6 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical). Verifications run concurrently as background jobs (<=4). Commands: `bash scripts/lean_verify.sh <file>`. RESULTS: pos_control exit=0 (verifies). atk_1 (property-arm boundary: restore prepatch '()' bug) exit=1, 'not definitionally equal'. atk_2 (drop module-name prefix, partial-domain) exit=1. atk_3 (collapse none-branch to always name++'()' , control-flow-effect) exit=1 type-mismatch. atk_4 (reorder kind dispatch: static before property, control-flow) exit=1. atk_5 (change prefix condition && to ||, boundary) exit=1. atk_6 (ungrounded-oracle echo: restructured match-on-3-Bools dispatch + full case-split proof, behaviorally identical) exit=0; `#print axioms correct_getIndexText` => [propext, Quot.sound] (clean, no sorryAx/Classical/native).

PROTOCOL step 2: atk_6 is the only impl closing with clean axioms => materialized its faithful patch (patch_atk6.diff, == gold edit since behaviorally identical) and ran run_resolve('sphinx-doc__sphinx-9698', ...): first run failed with 'no report — harness error/image pull failure' due to Docker build read-timeout under contention (20 running containers, 60s docker API timeout, BuildImageError ReadTimeout in run_instance.log — NOT a genuine non-resolve); pre-pulled swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-9698:latest then re-ran run_resolve => RESOLVED=True COMPLETED=True FLAKY=False note='resolved'. Echo policy satisfied: verifying => resolving, not a break.

REFINEMENT AUDIT: all 9 legs tagged R or R/I; NO A-consumed / A-reference legs; axiom_check.py is a legitimate skip stub (rsplit/'.'.join/gettext/% modeled deeply as string ops, meta axioms=[] deep_model_references=[]); no kind-3 leg; no callee-contract correspondence to validate. Conclusion: spec is a functional graph, closing impl <=> extensionally-gold, so verify implies correct here. No counterexample. SOUND after 6 attacks (5 diverging all rejected by carried proof; 1 echo verifies+resolves).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. problem_spec_getIndexText is a total function pinning result to exactly one string per input tuple in every branch (none-branch splits exclusively on modname=empty vs non-empty; some-branch covers all 8 Bool combos via chained implications classmethod / not-cm & prop / not-cm & not-prop & static / not-cm & not-prop & not-static). Any closing impl is therefore extensionally equal to gold; no verify-not-implies-correct gap. The single closing impl (atk_6, a behaviorally-equivalent echo) has faithful patch == gold edit, which RESOLVES=True.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the index-entry label for a documented class member.

When a member of a class is documented, a single index entry is registered for
it. The text of that entry is assembled from:

  * the member's fully-qualified dotted name (e.g. `Class.member`), from which the
    leading class part and the trailing member part are separated at the final
    dot;
  * the enclosing module name, which may be empty;
  * a flag selecting whether the module name is prepended to the class part;
  * and the *kind* of member it is — an ordinary method, a class method, a static
    method, or a value-like attribute exposed without a call.

The label distinguishes the kinds with a parenthesised qualifier naming the
class. For the call-like kinds (ordinary method, class method, static method) the
member name is shown with an empty argument list appended, reflecting that the
member is invoked. For the value-like kind, the member is referred to by its bare
name, with no argument list, because it is accessed rather than called.

When the dotted name has no separating dot, the class part cannot be formed, and
the label falls back to naming the member alone (with an empty argument list),
optionally qualified by the module it lives in.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The dotted-name
-- separation, the optional module-name qualification, and the assembly of the
-- label are all modeled directly as string operations over the inputs; there is
-- no opaque callee whose contract the proof must assume.
-- axioms-end

-- pure-start
/-- Separate a dotted name at its FINAL dot, as a right split into two parts.
Returns `none` when the name contains no dot (no class part can be formed);
otherwise `some (before, after)` where `after` is the trailing segment and
`before` is everything preceding the final dot, rejoined with dots. -/
def rsplitLastDot (s : String) : Option (String × String) :=
  match (s.splitOn ".").reverse with
  | []        => none
  | [_]       => none
  | last :: rest => some (String.intercalate "." rest.reverse, last)
-- pure-end

-- post-conditions-start
/-- The index-entry label is fully pinned to the inputs in every case:

  * when the name has no separating dot, the label is the bare member name with an
    empty argument list, qualified by the module name when one is present;
  * when the name splits, the class part is the trailing-class component,
    optionally prefixed by the module name, and the label is one of four
    determined shapes selected by the member kind — the call-like kinds carry an empty
    argument list after the member name, the value-like kind does not.

Every branch determines the result, so no output component is left free. -/
def problem_spec_getIndexText (name modname : String)
    (isClassmethod isProperty isStaticmethod addModuleNames : Bool)
    (result : String) : Prop :=
  match rsplitLastDot name with
  | none =>
      (modname ≠ "" → result = name ++ "() (in module " ++ modname ++ ")") ∧
      (modname = "" → result = name ++ "()")
  | some (clsname0, methname) =>
      let clsname :=
        if addModuleNames && modname != "" then modname ++ "." ++ clsname0 else clsname0
      (isClassmethod = true →
          result = methname ++ "() (" ++ clsname ++ " class method)") ∧
      (isClassmethod = false → isProperty = true →
          result = methname ++ " (" ++ clsname ++ " property)") ∧
      (isClassmethod = false → isProperty = false → isStaticmethod = true →
          result = methname ++ "() (" ++ clsname ++ " static method)") ∧
      (isClassmethod = false → isProperty = false → isStaticmethod = false →
          result = methname ++ "() (" ++ clsname ++ " method)")
-- post-conditions-end

-- impl-start
def implementation_getIndexText (name modname : String)
    (isClassmethod isProperty isStaticmethod addModuleNames : Bool) : String := Id.run do
  match rsplitLastDot name with
  | none =>
    if modname != "" then
      return name ++ "() (in module " ++ modname ++ ")"
    else
      return name ++ "()"
  | some (clsname0, methname) =>
    let mut clsname := clsname0
    if addModuleNames && modname != "" then
      clsname := modname ++ "." ++ clsname0
    if isClassmethod then
      return methname ++ "() (" ++ clsname ++ " class method)"
    else if isProperty then
      return methname ++ " (" ++ clsname ++ " property)"
    else if isStaticmethod then
      return methname ++ "() (" ++ clsname ++ " static method)"
    else
      return methname ++ "() (" ++ clsname ++ " method)"
-- impl-end

-- proof-start
theorem correct_getIndexText :
    ∀ (name modname : String)
      (isClassmethod isProperty isStaticmethod addModuleNames : Bool),
      problem_spec_getIndexText name modname
        isClassmethod isProperty isStaticmethod addModuleNames
        (implementation_getIndexText name modname
          isClassmethod isProperty isStaticmethod addModuleNames) := by
  intro name modname isClassmethod isProperty isStaticmethod addModuleNames
  unfold problem_spec_getIndexText implementation_getIndexText
  simp only [Id.run, bind, pure]
  split
  · constructor
    · intro hm
      simp only [bne_iff_ne]
      exact if_pos hm
    · intro hm
      simp only [bne_iff_ne, hm, ne_eq, not_true_eq_false, if_false]
  · refine ⟨?_, ?_, ?_, ?_⟩
    · intro h; subst h; simp only [if_true]; split <;> rfl
    · intro h1 h2; subst h1; subst h2; simp only; split <;> rfl
    · intro h1 h2 h3; subst h1; subst h2; subst h3; simp only; split <;> rfl
    · intro h1 h2 h3; subst h1; subst h2; subst h3; simp only; split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

python=python. same_spec=True verified for all 6 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical). Verifications run concurrently as background jobs (<=4). Commands: `bash scripts/lean_verify.sh <file>`. RESULTS: pos_control exit=0 (verifies). atk_1 (property-arm boundary: restore prepatch '()' bug) exit=1, 'not definitionally equal'. atk_2 (drop module-name prefix, partial-domain) exit=1. atk_3 (collapse none-branch to always name++'()' , control-flow-effect) exit=1 type-mismatch. atk_4 (reorder kind dispatch: static before property, control-flow) exit=1. atk_5 (change prefix condition && to ||, boundary) exit=1. atk_6 (ungrounded-oracle echo: restructured match-on-3-Bools dispatch + full case-split proof, behaviorally identical) exit=0; `#print axioms correct_getIndexText` => [propext, Quot.sound] (clean, no sorryAx/Classical/native).

PROTOCOL step 2: atk_6 is the only impl closing with clean axioms => materialized its faithful patch (patch_atk6.diff, == gold edit since behaviorally identical) and ran run_resolve('sphinx-doc__sphinx-9698', ...): first run failed with 'no report — harness error/image pull failure' due to Docker build read-timeout under contention (20 running containers, 60s docker API timeout, BuildImageError ReadTimeout in run_instance.log — NOT a genuine non-resolve); pre-pulled swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-9698:latest then re-ran run_resolve => RESOLVED=True COMPLETED=True FLAKY=False note='resolved'. Echo policy satisfied: verifying => resolving, not a break.

REFINEMENT AUDIT: all 9 legs tagged R or R/I; NO A-consumed / A-reference legs; axiom_check.py is a legitimate skip stub (rsplit/'.'.join/gettext/% modeled deeply as string ops, meta axioms=[] deep_model_references=[]); no kind-3 leg; no callee-contract correspondence to validate. Conclusion: spec is a functional graph, closing impl <=> extensionally-gold, so verify implies correct here. No counterexample. SOUND after 6 attacks (5 diverging all rejected by carried proof; 1 echo verifies+resolves).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift from real callee) assessment for sphinx-doc__sphinx-9698, modeled fn PyMethod.get_index_text (sphinx/domains/python.py:784-803, post-patch). Checks performed:

1. same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True — the graded spec region (docstring + rsplitLastDot pure def + problem_spec_getIndexText post-condition) is byte-identical between patch and prepatch; only the impl `property` arm differs (prepatch has spurious `()`). Spec view confirmed neutral.

2. Lean proof `correct_getIndexText` compiles clean (lean_verify exit 0) and `#print axioms` = [propext, Quot.sound] — no sorryAx, genuine proof.

3. rsplitLastDot corner-case behavior verified in Lean and matches Python `str.rsplit('.',1)` semantics EXACTLY on '', 'a', 'a.b', '.b', 'a.', '.', 'a..b', 'a.b.c', '...' (no-dot -> none matches unpack ValueError; multi-dot splits on final dot; empty segments agree).

4. DECISIVE CHECK: differential test of the Lean spec model (transliterated) against the REAL PyMethod.get_index_text callee extracted verbatim from the base_commit worktree (f050a7775, post-patch source confirmed to contain '%s (%s property)') and driven with a mocked self (options set + env.config.add_module_names). 768 enumerated edge cases + 300000 seeded-fuzz inputs = 300768 total, 0 divergences. gettext `_()` modeled as identity (correct under default/test locale, which is what the FAIL_TO_PASS test uses); unused `cls` element of name_cls correctly not modeled.

5. conformance_check.py (in-process oracle vs shadow) passes 120768 checks.

The spec is neither too strong nor drifting: it agrees with the real callee on every tested input including all string corner cases. No diverging input exists. Spec is a faithful model of the post-patch behavior, and it correctly excludes the prepatch buggy behavior (property arm with `()`), which is the intended discriminating clause.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (verified via markers.spec_view, LeanBackend tables) and same_spec(Solution, Solution_prepatch)=True — the spec region is byte-identical across the fix, so the spec is not tailored to the gold impl.

Gold edit: property arm '%s() (%s property)' -> '%s (%s property)', i.e. remove the empty argument list '()' after the member name for the value-like (property) kind, leaving call-like kinds (method/classmethod/staticmethod) unchanged.

The public problem_statement already discloses this exact fix in plain terms: 'An index entry with parens was registered for py:method directive with :property: option. It should not have parens.' and 'An index entry for the property should not have parens.' The distinction 'property → no parens; call-like kinds → parens' is therefore fully public.

Spec-view content assessed: (1) the /-! ... -/ docstring uses neutral behavioral vocabulary ('index-entry label', 'value-like kind', 'bare name, with no argument list', 'call-like kinds ... empty argument list appended') — no diff line, file path, format-string literal, or edit narration; (2) the postcondition problem_spec_getIndexText encodes the correct post-patch behavior (property result = methname ++ " (" ++ clsname ++ " property)" with no '()'), which is the standard role of a specification and matches only what the public statement already reveals; it does not reveal the property fix beyond the public statement. No ambiguity is being resolved in the gold's favor — the public statement is unambiguous about the intended behavior.

The impl and proof regions are elided in the spec view (impl-start/proof-start placeholders), so the mechanical edit itself is not shown. No gold-patch specifics or problem-statement phrasing leaked. mapping.md/refinement.md are not part of the consumer spec view. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

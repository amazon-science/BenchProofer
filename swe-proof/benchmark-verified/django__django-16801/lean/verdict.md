# P2 adversarial audit — django__django-16801

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,11 @@
   result = (!isAbstract && (truthy widthField || truthy heightField))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_connectPostInit
     (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
-  if !isAbstract && (truthy widthField || truthy heightField) then
+  if !isAbstract then
     return true
   return false
 -- impl-end
@@ -70,6 +71,8 @@
   unfold problem_spec_connectPostInit implementation_connectPostInit
   simp only [Id.run]
   by_cases h : !isAbstract && (truthy widthField || truthy heightField)
-  · simp only [h, if_true]; rfl
-  · simp only [h, if_false, Bool.false_eq_true]; rfl
+  · simp only [h, if_true]
+    cases hi : isAbstract <;> simp_all
+  · simp only [h, if_false, Bool.false_eq_true]
+    cases hi : isAbstract <;> simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,11 @@
   result = (!isAbstract && (truthy widthField || truthy heightField))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_connectPostInit
     (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
-  if !isAbstract && (truthy widthField || truthy heightField) then
+  if !isAbstract && (truthy widthField && truthy heightField) then
     return true
   return false
 -- impl-end
@@ -69,7 +70,11 @@
   intro isAbstract widthField heightField
   unfold problem_spec_connectPostInit implementation_connectPostInit
   simp only [Id.run]
-  by_cases h : !isAbstract && (truthy widthField || truthy heightField)
-  · simp only [h, if_true]; rfl
-  · simp only [h, if_false, Bool.false_eq_true]; rfl
+  by_cases h : !isAbstract && (truthy widthField && truthy heightField)
+  · simp only [h, if_true]
+    cases hw : truthy widthField <;> cases hh : truthy heightField <;>
+      cases ha : isAbstract <;> simp_all
+  · simp only [h, if_false, Bool.false_eq_true]
+    cases hw : truthy widthField <;> cases hh : truthy heightField <;>
+      cases ha : isAbstract <;> simp_all
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,11 @@
   result = (!isAbstract && (truthy widthField || truthy heightField))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_connectPostInit
     (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
-  if !isAbstract && (truthy widthField || truthy heightField) then
+  if truthy widthField || truthy heightField then
     return true
   return false
 -- impl-end
@@ -69,7 +70,9 @@
   intro isAbstract widthField heightField
   unfold problem_spec_connectPostInit implementation_connectPostInit
   simp only [Id.run]
-  by_cases h : !isAbstract && (truthy widthField || truthy heightField)
-  · simp only [h, if_true]; rfl
-  · simp only [h, if_false, Bool.false_eq_true]; rfl
+  by_cases h : truthy widthField || truthy heightField
+  · simp only [h, if_true]
+    cases ha : isAbstract <;> simp_all
+  · simp only [h, if_false, Bool.false_eq_true]
+    cases ha : isAbstract <;> simp_all
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,11 @@
   result = (!isAbstract && (truthy widthField || truthy heightField))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_connectPostInit
     (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
-  if !isAbstract && (truthy widthField || truthy heightField) then
+  if !isAbstract && truthy widthField then
     return true
   return false
 -- impl-end
@@ -69,7 +70,11 @@
   intro isAbstract widthField heightField
   unfold problem_spec_connectPostInit implementation_connectPostInit
   simp only [Id.run]
-  by_cases h : !isAbstract && (truthy widthField || truthy heightField)
-  · simp only [h, if_true]; rfl
-  · simp only [h, if_false, Bool.false_eq_true]; rfl
+  by_cases h : !isAbstract && truthy widthField
+  · simp only [h, if_true]
+    cases ha : isAbstract <;> cases hw : truthy widthField <;>
+      cases hh : truthy heightField <;> simp_all
+  · simp only [h, if_false, Bool.false_eq_true]
+    cases ha : isAbstract <;> cases hw : truthy widthField <;>
+      cases hh : truthy heightField <;> simp_all
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,12 +53,11 @@
   result = (!isAbstract && (truthy widthField || truthy heightField))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_connectPostInit
     (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
-  if !isAbstract && (truthy widthField || truthy heightField) then
-    return true
-  return false
+  return true
 -- impl-end
 
 -- proof-start
@@ -69,7 +68,6 @@
   intro isAbstract widthField heightField
   unfold problem_spec_connectPostInit implementation_connectPostInit
   simp only [Id.run]
-  by_cases h : !isAbstract && (truthy widthField || truthy heightField)
-  · simp only [h, if_true]; rfl
-  · simp only [h, if_false, Bool.false_eq_true]; rfl
+  cases ha : isAbstract <;> cases hw : truthy widthField <;>
+    cases hh : truthy heightField <;> simp_all
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,11 @@
   result = (!isAbstract && (truthy widthField || truthy heightField))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_connectPostInit
     (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
-  if !isAbstract && (truthy widthField || truthy heightField) then
+  if isAbstract && (truthy widthField || truthy heightField) then
     return true
   return false
 -- impl-end
@@ -69,7 +70,9 @@
   intro isAbstract widthField heightField
   unfold problem_spec_connectPostInit implementation_connectPostInit
   simp only [Id.run]
-  by_cases h : !isAbstract && (truthy widthField || truthy heightField)
-  · simp only [h, if_true]; rfl
-  · simp only [h, if_false, Bool.false_eq_true]; rfl
+  by_cases h : isAbstract && (truthy widthField || truthy heightField)
+  · simp only [h, if_true]
+    cases ha : isAbstract <;> simp_all
+  · simp only [h, if_false, Bool.false_eq_true]
+    cases ha : isAbstract <;> simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a model installs the post-initialization handler that keeps an
image-valued field's associated width / height attributes in sync.

Such a handler is registered against a model so that, after each instance is
initialized, the width and height attributes that mirror the stored image can be
refreshed. Registering and firing the handler costs time on every instance
initialization, so it is worth installing only when it actually has work to do.

The handler has work to do only when the field tracks at least one dimension —
that is, it names a width attribute or a height attribute. When neither a width
nor a height attribute is tracked, the handler would do nothing, so it is not
installed. Abstract models never receive initialized instances, so they never
install it either.

The decision is therefore fully determined by three facts about the model and
the field: whether the model is abstract, whether a (non-empty) width attribute
is named, and whether a (non-empty) height attribute is named. The handler is
installed exactly when the model is concrete and the field names a width
attribute or a height attribute.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads only three already-available facts about the model and the field — a
-- concrete/abstract flag and the two optional attribute names the field tracks —
-- and combines them with boolean connectives and a non-empty-name test. All are
-- modeled directly (`Bool`, `Option String`, a non-empty-string test), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A tracked attribute name counts as "configured" exactly when it is present
and non-empty (an absent or empty name configures nothing). Mirrors the
truthiness of an optional identifier string. -/
def truthy (o : Option String) : Bool :=
  match o with
  | none   => false
  | some s => !s.isEmpty
-- pure-end

-- post-conditions-start
/-- The post-initialization dimension-sync handler is installed (`result = true`)
exactly when the model is concrete (not abstract) and the field names at least
one of a width attribute or a height attribute; otherwise it is not installed
(`result = false`). The single output is fully determined by the three inputs
(directive 5 frame: no output component is left unconstrained). -/
def problem_spec_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) (result : Bool) : Prop :=
  result = (!isAbstract && (truthy widthField || truthy heightField))
-- post-conditions-end


-- impl-start
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool :=
  !(isAbstract || (!truthy widthField && !truthy heightField))
-- impl-end

-- proof-start
theorem correct_connectPostInit :
    ∀ (isAbstract : Bool) (widthField heightField : Option String),
      problem_spec_connectPostInit isAbstract widthField heightField
        (implementation_connectPostInit isAbstract widthField heightField) := by
  intro isAbstract widthField heightField
  unfold problem_spec_connectPostInit implementation_connectPostInit
  cases isAbstract <;>
    cases hw : truthy widthField <;> cases hh : truthy heightField <;> simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL FUNCTIONAL EQUALITY: problem_spec_connectPostInit pins result = (!isAbstract && (truthy widthField || truthy heightField)) uniquely for every input. Any impl that closes correct_connectPostInit must be extensionally equal to the gold decision on all inputs; divergence on any input makes the equality literally false there (unprovable). All same_spec=True confirmed via swebench_unified.markers.same_spec for all 7 files (byte-identical spec regions, lines 1-55).

ATTACKS (6 distinct wrong impls, all same_spec=True, verified concurrently in batches of <=4 via `bash scripts/lean_verify.sh <f>`):
- atk_1 prepatch bug (`if !isAbstract then true`, ignores fields) -> EXIT 1, 'unsolved goals' (also the prepatch reproduction).
- atk_2 AND instead of OR (both dims required) -> EXIT 1, 'unsolved goals'.
- atk_3 drop the !isAbstract conjunct -> EXIT 1, 'unsolved goals'.
- atk_4 width-only, ignores height (partial-domain) -> EXIT 1, 'unsolved goals'.
- atk_5 ungrounded-oracle echo (always true) -> EXIT 1, 'unsolved goals'.
- atk_6 control-flow-effect: inverted `isAbstract && (...)` -> EXIT 1, 'unsolved goals'.
NO wrong impl closed. Failures are genuine logical impossibility (unsolved goals from a false equality), NOT tactic weakness -> confirmed by machine-checked refutations in refute.lean: `example : ¬ problem_spec_connectPostInit false none none true` closes by decide; `¬ problem_spec_connectPostInit true (some "w") none true` closes by decide; AND-swap witness (some w, none) closes by decide. All examples typecheck (only intentional placeholder sorry + cosmetic unused-var warnings).

Because NO wrong impl closes with clean axioms, there is NO faithful patch to materialize/resolve (patches={}); the verify=>correct implication cannot be broken via a divergent verifying impl.

POSITIVE CONTROL: pos.lean (de Morgan rewrite `!(isAbstract || (!truthy widthField && !truthy heightField))`) -> `bash scripts/lean_verify.sh pos.lean` EXIT 0; `#print axioms correct_connectPostInit` => 'depends on axioms: [propext]' (no sorryAx, no custom axioms). Extensionally identical to gold, so it resolves identically.

REFINEMENT.MD AUDIT: legs 1(R),2(R),3(I=the fixed op),4(R),5(R). No A-consumed, no A-reference, no kind-3. axiom_check.py is a confirmed skip stub (axioms=[], deep_model_references=[]); mapping.md ties result=true <=> signals.post_init.connect(...) runs, matching the post-patch guard `not cls._meta.abstract and (self.width_field or self.height_field)`. No A-leg correspondence gap to exploit (pure boolean decision over three already-available facts; no unchanged callee consumed). conformance_check.py exhaustively differential-tests the R/I shadow vs an in-process replica of the post-patch guard.

VERDICT: SOUND. >=6 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, AND/OR/conjunct swaps) all fail to close; positive control verifies with clean axioms; prepatch bug reproduced. verify => correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a model installs the post-initialization handler that keeps an
image-valued field's associated width / height attributes in sync.

Such a handler is registered against a model so that, after each instance is
initialized, the width and height attributes that mirror the stored image can be
refreshed. Registering and firing the handler costs time on every instance
initialization, so it is worth installing only when it actually has work to do.

The handler has work to do only when the field tracks at least one dimension —
that is, it names a width attribute or a height attribute. When neither a width
nor a height attribute is tracked, the handler would do nothing, so it is not
installed. Abstract models never receive initialized instances, so they never
install it either.

The decision is therefore fully determined by three facts about the model and
the field: whether the model is abstract, whether a (non-empty) width attribute
is named, and whether a (non-empty) height attribute is named. The handler is
installed exactly when the model is concrete and the field names a width
attribute or a height attribute.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads only three already-available facts about the model and the field — a
-- concrete/abstract flag and the two optional attribute names the field tracks —
-- and combines them with boolean connectives and a non-empty-name test. All are
-- modeled directly (`Bool`, `Option String`, a non-empty-string test), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A tracked attribute name counts as "configured" exactly when it is present
and non-empty (an absent or empty name configures nothing). Mirrors the
truthiness of an optional identifier string. -/
def truthy (o : Option String) : Bool :=
  match o with
  | none   => false
  | some s => !s.isEmpty
-- pure-end

-- post-conditions-start
/-- The post-initialization dimension-sync handler is installed (`result = true`)
exactly when the model is concrete (not abstract) and the field names at least
one of a width attribute or a height attribute; otherwise it is not installed
(`result = false`). The single output is fully determined by the three inputs
(directive 5 frame: no output component is left unconstrained). -/
def problem_spec_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) (result : Bool) : Prop :=
  result = (!isAbstract && (truthy widthField || truthy heightField))
-- post-conditions-end


-- impl-start
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool :=
  !(isAbstract || (!truthy widthField && !truthy heightField))
-- impl-end

-- proof-start
theorem correct_connectPostInit :
    ∀ (isAbstract : Bool) (widthField heightField : Option String),
      problem_spec_connectPostInit isAbstract widthField heightField
        (implementation_connectPostInit isAbstract widthField heightField) := by
  intro isAbstract widthField heightField
  unfold problem_spec_connectPostInit implementation_connectPostInit
  cases isAbstract <;>
    cases hw : truthy widthField <;> cases hh : truthy heightField <;> simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL FUNCTIONAL EQUALITY: problem_spec_connectPostInit pins result = (!isAbstract && (truthy widthField || truthy heightField)) uniquely for every input. Any impl that closes correct_connectPostInit must be extensionally equal to the gold decision on all inputs; divergence on any input makes the equality literally false there (unprovable). All same_spec=True confirmed via swebench_unified.markers.same_spec for all 7 files (byte-identical spec regions, lines 1-55).

ATTACKS (6 distinct wrong impls, all same_spec=True, verified concurrently in batches of <=4 via `bash scripts/lean_verify.sh <f>`):
- atk_1 prepatch bug (`if !isAbstract then true`, ignores fields) -> EXIT 1, 'unsolved goals' (also the prepatch reproduction).
- atk_2 AND instead of OR (both dims required) -> EXIT 1, 'unsolved goals'.
- atk_3 drop the !isAbstract conjunct -> EXIT 1, 'unsolved goals'.
- atk_4 width-only, ignores height (partial-domain) -> EXIT 1, 'unsolved goals'.
- atk_5 ungrounded-oracle echo (always true) -> EXIT 1, 'unsolved goals'.
- atk_6 control-flow-effect: inverted `isAbstract && (...)` -> EXIT 1, 'unsolved goals'.
NO wrong impl closed. Failures are genuine logical impossibility (unsolved goals from a false equality), NOT tactic weakness -> confirmed by machine-checked refutations in refute.lean: `example : ¬ problem_spec_connectPostInit false none none true` closes by decide; `¬ problem_spec_connectPostInit true (some "w") none true` closes by decide; AND-swap witness (some w, none) closes by decide. All examples typecheck (only intentional placeholder sorry + cosmetic unused-var warnings).

Because NO wrong impl closes with clean axioms, there is NO faithful patch to materialize/resolve (patches={}); the verify=>correct implication cannot be broken via a divergent verifying impl.

POSITIVE CONTROL: pos.lean (de Morgan rewrite `!(isAbstract || (!truthy widthField && !truthy heightField))`) -> `bash scripts/lean_verify.sh pos.lean` EXIT 0; `#print axioms correct_connectPostInit` => 'depends on axioms: [propext]' (no sorryAx, no custom axioms). Extensionally identical to gold, so it resolves identically.

REFINEMENT.MD AUDIT: legs 1(R),2(R),3(I=the fixed op),4(R),5(R). No A-consumed, no A-reference, no kind-3. axiom_check.py is a confirmed skip stub (axioms=[], deep_model_references=[]); mapping.md ties result=true <=> signals.post_init.connect(...) runs, matching the post-patch guard `not cls._meta.abstract and (self.width_field or self.height_field)`. No A-leg correspondence gap to exploit (pure boolean decision over three already-available facts; no unchanged callee consumed). conformance_check.py exhaustively differential-tests the R/I shadow vs an in-process replica of the post-patch guard.

VERDICT: SOUND. >=6 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, AND/OR/conjunct swaps) all fail to close; positive control verifies with clean axioms; prepatch bug reproduced. verify => correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-16801 lean bundle. Modeled function = the connection decision in ImageField.contribute_to_class (django/db/models/fields/files.py). Post-patch (gold) guard at base 3b62d8c83e: `not cls._meta.abstract and (self.width_field or self.height_field)`, verified verbatim worktree via patch.diff and `git show 3b62d8c83e:.../files.py`.

Spec: problem_spec_connectPostInit = (result = (!isAbstract && (truthy widthField || truthy heightField))), with truthy: none->false, some s-> !s.isEmpty. This is an EXACT transliteration of the real post-patch guard:
- isAbstract:Bool <-> cls._meta.abstract:bool (identity).
- widthField/heightField:Option String <-> self.width_field/self.height_field used in boolean position; truthy mirrors Python bool(): bool(None)=False (none->false), bool("")=False (some ""->false), bool(nonempty)=True (some s->!isEmpty). All three or-operand cases and the outer and/not compose exactly as Python evaluates them.
- result:Bool <-> whether signals.post_init.connect(...) is reached = truth value of the guard, which is exactly what the F2P test test_post_init_not_connected observes.

Searched for a diverging input: none exists. Whitespace name (some " ") -> truthy=true matching bool(" ")=True; some "" -> false matching bool("")=False (a harmless domain widening, since Django only produces None/nonempty). The spec is fully determined for ALL inputs (directive-5 frame, no unconstrained component) and grounded structurally in the three inputs, not equated to an ungrounded oracle, so it is neither too strong nor drifting. update_dimension_fields and post_init.connect are correctly NOT modeled: the observable behavior is solely the connection decision. Second gold hunk is out of scope and irrelevant to the F2P regression (correctly argued in mapping.md).

Supporting checks: (1) Solution.lean compiles, lean_verify.sh EXIT=0. (2) `#print axioms correct_connectPostInit` -> depends only on [propext]; NO sorryAx, proof genuine. (3) same_spec(Solution, Solution_prepatch, lean tables) = True -> spec region byte-identical; the prepatch impl (tests only !isAbstract) genuinely fails the SAME spec on (isAbstract=false, both fields falsy), the correct discriminating input. (4) conformance_check.py exhaustively enumerates abstract x {absent,empty,set}^2 + 1e5 fuzz, oracle==shadow with 0 disagreements. No faithfulness defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen) passes with zero hard_failures; same_spec(post, prepatch) is True. Semantic review: the spec view describes only the abstract target behavior — 'the handler is installed exactly when the model is concrete and the field names a width attribute or a height attribute' — every element of which is ALREADY public in the problem_statement, which explicitly names the post_init signal handler and states it is a noop when width_field/height_field are not set and that removing it then has no effect. The gold edit (adding `and (self.width_field or self.height_field)` to the `if not cls._meta.abstract:` guard) is thus fully disclosed by the public task, not by the spec. No patched identifiers appear (contribute_to_class, update_dimension_fields, signals.post_init.connect, cls._meta.abstract are all absent from the view); no gold-diff line reproduced; no diff marker; no patched file/module path; no bug/fix narration in comments. The 'abstract models never install it' clause reflects the PRE-EXISTING guard (present in prepatch), so it reveals nothing about the change. Judged against problem_statement only, not hints_text. No line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

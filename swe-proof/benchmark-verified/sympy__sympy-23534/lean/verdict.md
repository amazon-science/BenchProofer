# P2 adversarial audit — sympy__sympy-23534

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_5.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   | NameSpec.seq items =>
     let mut result : List SymResult := []
     for nm in items.attach do
-      result := result ++ [implementation_symbols cls nm.val]
+      result := result ++ [implementation_symbols defaultClass nm.val]
     return SymResult.node result
 termination_by names
 decreasing_by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
 -- impl-start
 def implementation_symbols (cls : ClassId) (names : NameSpec) : SymResult := Id.run do
   match names with
-  | NameSpec.tok s => return SymResult.leaf cls s
+  | NameSpec.tok s => return SymResult.leaf cls (s ++ "!")
   | NameSpec.seq items =>
     let mut result : List SymResult := []
     for nm in items.attach do
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   | NameSpec.seq items =>
     let mut result : List SymResult := []
     for nm in items.attach do
-      result := result ++ [implementation_symbols cls nm.val]
+      result := [implementation_symbols cls nm.val] ++ result
     return SymResult.node result
 termination_by names
 decreasing_by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
 -- impl-start
 def implementation_symbols (cls : ClassId) (names : NameSpec) : SymResult := Id.run do
   match names with
-  | NameSpec.tok s => return SymResult.leaf cls s
+  | NameSpec.tok s => return SymResult.leaf defaultClass s
   | NameSpec.seq items =>
     let mut result : List SymResult := []
     for nm in items.attach do
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,7 @@
   match names with
   | NameSpec.tok s => return SymResult.leaf cls s
   | NameSpec.seq items =>
-    let mut result : List SymResult := []
-    for nm in items.attach do
-      result := result ++ [implementation_symbols cls nm.val]
-    return SymResult.node result
+    return SymResult.node []
 termination_by names
 decreasing_by
   simp_wf
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
 -- impl-start
 def implementation_symbols (cls : ClassId) (names : NameSpec) : SymResult := Id.run do
   match names with
-  | NameSpec.tok s => return SymResult.leaf cls s
+  | NameSpec.tok s => return SymResult.leaf (cls + 1) s
   | NameSpec.seq items =>
     let mut result : List SymResult := []
     for nm in items.attach do
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   | NameSpec.seq items =>
     let mut result : List SymResult := []
     for nm in items.attach do
-      result := result ++ [implementation_symbols cls nm.val]
+      result := result ++ [implementation_symbols cls nm.val, implementation_symbols cls nm.val]
     return SymResult.node result
 termination_by names
 decreasing_by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_5.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing a batch of symbol-like objects from a `names` argument.

`names` is either a single name token or an arbitrarily nested sequence of such
tokens. The caller may request a target class (`cls`) for the constructed
objects (the default class, or some other symbol-like class such as a function
class). The exported behavior: the requested target class must reach EVERY
constructed object, including objects produced from tokens nested below one or
more sequence layers, and the result must mirror the nesting shape of `names`.
-/

-- axioms-start
/-- An opaque tag identifying the target class requested for constructed
objects; `defaultClass` is the tag of the default class. -/
abbrev ClassId := Nat

/-- The default target class. -/
def defaultClass : ClassId := 0

/-- A name argument: either a single token, or a nested sequence of name
arguments. -/
inductive NameSpec where
  | tok : String → NameSpec
  | seq : List NameSpec → NameSpec
deriving Repr, Inhabited

/-- The constructed result mirroring the nesting shape of the input: a leaf
tagged with the class it was built under together with its source token, or a
container of sub-results. The class tag is the observable component the
specification constrains. -/
inductive SymResult where
  | leaf : ClassId → String → SymResult
  | node : List SymResult → SymResult
deriving Repr, Inhabited
-- axioms-end

-- pure-start
/-- Relational specification of the desired construction. A token maps to a leaf
tagged with THE REQUESTED CLASS and that token; a sequence maps to a container
of the same length whose entries are the recursively-specified results, each
carrying the SAME requested class. -/
inductive BuildsUnder (cls : ClassId) : NameSpec → SymResult → Prop where
  | tok (s : String) : BuildsUnder cls (NameSpec.tok s) (SymResult.leaf cls s)
  | seq (items : List NameSpec) (rs : List SymResult) :
      List.Forall₂ (BuildsUnder cls) items rs →
      BuildsUnder cls (NameSpec.seq items) (SymResult.node rs)
-- pure-end

-- post-conditions-start
/-- `result` is a correct construction of `names` for the requested class `cls`:
the shape mirrors `names`, and the requested class reaches every leaf. -/
def problem_spec_symbols (cls : ClassId) (names : NameSpec) (result : SymResult) : Prop :=
  BuildsUnder cls names result
-- post-conditions-end

-- impl-start
def implementation_symbols (cls : ClassId) (names : NameSpec) : SymResult := Id.run do
  match names with
  | NameSpec.tok s => return SymResult.leaf cls s
  | NameSpec.seq items =>
    let mut result : List SymResult := []
    for nm in items.attach do
      result := result ++ [implementation_symbols cls nm.val]
    return SymResult.node result
termination_by names
decreasing_by
  simp_wf
  exact lt_of_lt_of_le (List.sizeOf_lt_of_mem nm.property) (Nat.le_add_left _ _)
-- impl-end

-- proof-start
/-- The desugared `for … do result := result ++ [g nm]` loop wrapped in the
final `SymResult.node` reduces to `node (acc ++ l.map g)`, generalized over the
accumulator. -/
theorem loop_lem {α : Type} (l : List α) (g : α → SymResult) (acc : List SymResult) :
    (Id.run (do
      let r ← forIn l acc (fun nm r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [g nm])))
      pure (SymResult.node r))) = SymResult.node (acc ++ l.map g) := by
  induction l generalizing acc with
  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]; simp

theorem tok_unfold (cls : ClassId) (s : String) :
    implementation_symbols cls (NameSpec.tok s) = SymResult.leaf cls s := by
  conv_lhs => unfold implementation_symbols
  rfl

theorem seq_unfold (cls : ClassId) (items : List NameSpec) :
    implementation_symbols cls (NameSpec.seq items) =
      SymResult.node (items.map (fun nm => implementation_symbols cls nm)) := by
  conv_lhs => unfold implementation_symbols
  rw [loop_lem]
  simp

theorem correct_symbols : ∀ (cls : ClassId) (names : NameSpec),
    problem_spec_symbols cls names (implementation_symbols cls names) := by
  intro cls names
  unfold problem_spec_symbols
  induction names using NameSpec.rec with
  | tok s => rw [tok_unfold]; exact BuildsUnder.tok s
  | seq items ih => rw [seq_unfold]; exact BuildsUnder.seq items _ ih
  | nil => exact List.Forall₂.nil
  | cons head tail ih1 ih2 => exact List.Forall₂.cons ih1 ih2
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec BuildsUnder is a DETERMINISTIC functional graph: `tok s` admits only the constructor `leaf cls s` (class tag AND token pinned); `seq items` requires `Forall2 (BuildsUnder cls) items rs`, pinning length + order + pointwise sub-results. By structural induction, problem_spec_symbols cls names result <-> result = (gold impl) cls names. Every NameSpec input is reachable and implementation_symbols is total, so ANY impl differing from gold on any input fails problem_spec_symbols there -- no closing proof can exist for a wrong impl.

Confirmed empirically with 7 DISTINCT same-spec (same_spec=True for all 7 + positive control) wrong impls, all carrying the gold-shaped proof; each run via `bash scripts/lean_verify.sh <path>`: atk_1 (prepatch bug: recursion drops cls -> defaultClass on nested leaves) -- EXIT 1 (unsolved goals @ proof line 96); reproduces the prepatch defect exactly. atk_2 (boundary: leaf token s ++ "!") -- EXIT 1 (rfl failed @ 92). atk_3 (control-flow-effect: prepend instead of append -> reverses order) -- EXIT 1 (rewrite failed @ 98). atk_4 (partial-domain: token leaf tagged defaultClass, ignores cls) -- EXIT 1 (rfl failed @ 92). atk_6 (ungrounded-oracle echo: seq always returns node []) -- EXIT 1 (rewrite failed @ 95). atk_7 (class offset: leaf tagged cls+1) -- EXIT 1 (rfl failed @ 92). atk_8 (wrong length: each element duplicated) -- EXIT 1 (rewrite failed @ 98).

All failures are in the PROOF region (lines 92-98); the impls compile and terminate fine (only atk_6 non-recursive), so these are genuine spec-proof failures, not incidental errors. Each impl confirmed to differ from gold in the impl region via diff. Positive control atk_5 = exact gold: EXIT 0, and `#print axioms correct_symbols` = [propext, Quot.sound] (CLEAN -- no sorryAx / Classical.choice). Protocol step 2: NO wrong impl closes with a clean-axiom proof, so there is NO verifying-but-non-resolving patch to materialize (patches={} vacuously); verify=>correct cannot be broken.

Protocol step 3 (refinement.md audit): 5 legs, all R (1,2,4) or I (3,5); no kind-3 changed-inexpressible op, no consumed axiom, no opaque A-reference callee. axiom_check.py is a legitimate skip stub (axioms:[]); the token-construction leaf modeled concretely as SymResult.leaf cls s, token-parsing internals (range expansion/escape/collapsing) abstracted to the class tag the fix governs, orthogonal internals covered by G-CONF against patched sympy.symbols. A-legs correspondence holds: no deep-model callee. Verdict SOUND: >=5 attacks run, none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_5.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_5.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing a batch of symbol-like objects from a `names` argument.

`names` is either a single name token or an arbitrarily nested sequence of such
tokens. The caller may request a target class (`cls`) for the constructed
objects (the default class, or some other symbol-like class such as a function
class). The exported behavior: the requested target class must reach EVERY
constructed object, including objects produced from tokens nested below one or
more sequence layers, and the result must mirror the nesting shape of `names`.
-/

-- axioms-start
/-- An opaque tag identifying the target class requested for constructed
objects; `defaultClass` is the tag of the default class. -/
abbrev ClassId := Nat

/-- The default target class. -/
def defaultClass : ClassId := 0

/-- A name argument: either a single token, or a nested sequence of name
arguments. -/
inductive NameSpec where
  | tok : String → NameSpec
  | seq : List NameSpec → NameSpec
deriving Repr, Inhabited

/-- The constructed result mirroring the nesting shape of the input: a leaf
tagged with the class it was built under together with its source token, or a
container of sub-results. The class tag is the observable component the
specification constrains. -/
inductive SymResult where
  | leaf : ClassId → String → SymResult
  | node : List SymResult → SymResult
deriving Repr, Inhabited
-- axioms-end

-- pure-start
/-- Relational specification of the desired construction. A token maps to a leaf
tagged with THE REQUESTED CLASS and that token; a sequence maps to a container
of the same length whose entries are the recursively-specified results, each
carrying the SAME requested class. -/
inductive BuildsUnder (cls : ClassId) : NameSpec → SymResult → Prop where
  | tok (s : String) : BuildsUnder cls (NameSpec.tok s) (SymResult.leaf cls s)
  | seq (items : List NameSpec) (rs : List SymResult) :
      List.Forall₂ (BuildsUnder cls) items rs →
      BuildsUnder cls (NameSpec.seq items) (SymResult.node rs)
-- pure-end

-- post-conditions-start
/-- `result` is a correct construction of `names` for the requested class `cls`:
the shape mirrors `names`, and the requested class reaches every leaf. -/
def problem_spec_symbols (cls : ClassId) (names : NameSpec) (result : SymResult) : Prop :=
  BuildsUnder cls names result
-- post-conditions-end

-- impl-start
def implementation_symbols (cls : ClassId) (names : NameSpec) : SymResult := Id.run do
  match names with
  | NameSpec.tok s => return SymResult.leaf cls s
  | NameSpec.seq items =>
    let mut result : List SymResult := []
    for nm in items.attach do
      result := result ++ [implementation_symbols cls nm.val]
    return SymResult.node result
termination_by names
decreasing_by
  simp_wf
  exact lt_of_lt_of_le (List.sizeOf_lt_of_mem nm.property) (Nat.le_add_left _ _)
-- impl-end

-- proof-start
/-- The desugared `for … do result := result ++ [g nm]` loop wrapped in the
final `SymResult.node` reduces to `node (acc ++ l.map g)`, generalized over the
accumulator. -/
theorem loop_lem {α : Type} (l : List α) (g : α → SymResult) (acc : List SymResult) :
    (Id.run (do
      let r ← forIn l acc (fun nm r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [g nm])))
      pure (SymResult.node r))) = SymResult.node (acc ++ l.map g) := by
  induction l generalizing acc with
  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]; simp

theorem tok_unfold (cls : ClassId) (s : String) :
    implementation_symbols cls (NameSpec.tok s) = SymResult.leaf cls s := by
  conv_lhs => unfold implementation_symbols
  rfl

theorem seq_unfold (cls : ClassId) (items : List NameSpec) :
    implementation_symbols cls (NameSpec.seq items) =
      SymResult.node (items.map (fun nm => implementation_symbols cls nm)) := by
  conv_lhs => unfold implementation_symbols
  rw [loop_lem]
  simp

theorem correct_symbols : ∀ (cls : ClassId) (names : NameSpec),
    problem_spec_symbols cls names (implementation_symbols cls names) := by
  intro cls names
  unfold problem_spec_symbols
  induction names using NameSpec.rec with
  | tok s => rw [tok_unfold]; exact BuildsUnder.tok s
  | seq items ih => rw [seq_unfold]; exact BuildsUnder.seq items _ ih
  | nil => exact List.Forall₂.nil
  | cons head tail ih1 ih2 => exact List.Forall₂.cons ih1 ih2
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec BuildsUnder is a DETERMINISTIC functional graph: `tok s` admits only the constructor `leaf cls s` (class tag AND token pinned); `seq items` requires `Forall2 (BuildsUnder cls) items rs`, pinning length + order + pointwise sub-results. By structural induction, problem_spec_symbols cls names result <-> result = (gold impl) cls names. Every NameSpec input is reachable and implementation_symbols is total, so ANY impl differing from gold on any input fails problem_spec_symbols there -- no closing proof can exist for a wrong impl.

Confirmed empirically with 7 DISTINCT same-spec (same_spec=True for all 7 + positive control) wrong impls, all carrying the gold-shaped proof; each run via `bash scripts/lean_verify.sh <path>`: atk_1 (prepatch bug: recursion drops cls -> defaultClass on nested leaves) -- EXIT 1 (unsolved goals @ proof line 96); reproduces the prepatch defect exactly. atk_2 (boundary: leaf token s ++ "!") -- EXIT 1 (rfl failed @ 92). atk_3 (control-flow-effect: prepend instead of append -> reverses order) -- EXIT 1 (rewrite failed @ 98). atk_4 (partial-domain: token leaf tagged defaultClass, ignores cls) -- EXIT 1 (rfl failed @ 92). atk_6 (ungrounded-oracle echo: seq always returns node []) -- EXIT 1 (rewrite failed @ 95). atk_7 (class offset: leaf tagged cls+1) -- EXIT 1 (rfl failed @ 92). atk_8 (wrong length: each element duplicated) -- EXIT 1 (rewrite failed @ 98).

All failures are in the PROOF region (lines 92-98); the impls compile and terminate fine (only atk_6 non-recursive), so these are genuine spec-proof failures, not incidental errors. Each impl confirmed to differ from gold in the impl region via diff. Positive control atk_5 = exact gold: EXIT 0, and `#print axioms correct_symbols` = [propext, Quot.sound] (CLEAN -- no sorryAx / Classical.choice). Protocol step 2: NO wrong impl closes with a clean-axiom proof, so there is NO verifying-but-non-resolving patch to materialize (patches={} vacuously); verify=>correct cannot be broken.

Protocol step 3 (refinement.md audit): 5 legs, all R (1,2,4) or I (3,5); no kind-3 changed-inexpressible op, no consumed axiom, no opaque A-reference callee. axiom_check.py is a legitimate skip stub (axioms:[]); the token-construction leaf modeled concretely as SymResult.leaf cls s, token-parsing internals (range expansion/escape/collapsing) abstracted to the class tag the fix governs, orthogonal internals covered by G-CONF against patched sympy.symbols. A-legs correspondence holds: no deep-model callee. Verdict SOUND: >=5 attacks run, none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec over lean backend = True); frozen spec confirmed. Solution.lean compiles clean (lean_verify exit 0); #print axioms correct_symbols = [propext, Quot.sound], no sorryAx (proof real). Faithfulness attack failed: the modeled observable (class-tag reaches every leaf, shape mirrors nesting) matches the real patched callee at base_commit 832c24fec1 (gold patch symbols(name,**args)->symbols(name,cls=cls,**args) applied). Tests: 30,000 random nested tuple/list inputs comparing each nested leaf's type() vs top-level symbols(token,cls=cls) -> 0 divergences; G-CONF 0/100000; range tokens (q:2->(q0,q1)), empty ranges (a:0->()), and shape preservation type(names)(result) all confirmed with every produced object of class cls. The token->single-leaf abstraction (collapsing range expansion/count/parsing internals) is a DECLARED projection (mapping.md/refinement.md), not a distortion: it drops count but faithfully preserves the sole observable the fix governs (the class tag). **args held orthogonal as declared. No input makes the spec claim something the real fixed callee violates; the spec is not over-strong. No diverging input exists on the modeled observable.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen on the lean spec view returns passed=True, zero hard_failures). Verified spec region is byte-identical: same_spec(Solution.lean, Solution_prepatch.lean)=True, so the postcondition/axiom/pure spec text does not depend on the gold fix. Spec view (recomputed) elides both impl and proof regions, so the buggy pre-patch recursion vs the fixed cls-threading recursion is never exposed to the consumer.

Gold edit: `symbols(name, **args)` -> `symbols(name, cls=cls, **args)` in the else/sequence branch (sympy/core/symbol.py) — thread the requested class through the recursive call so it reaches tokens nested under extra parentheses.

Leakage assessment vs the PUBLIC problem_statement (not hints): the problem_statement already discloses the full observable essence — `symbols(('q:2','u:2'), cls=Function)` should yield Function/UndefinedFunction objects but the 'extra layer of parentheses' instead produces default Symbols; expected vs actual class is stated verbatim. The spec's `BuildsUnder` relation (requested class must reach EVERY leaf, including leaves nested below sequence layers, mirroring the input shape) is a faithful formalization of that publicly-stated desired behavior, not a disclosure of the edit mechanism. It reveals nothing about the gold edit beyond what the task already makes public.

Negative checks: no diff markers, patched file path (sympy/core/symbol.py) or dotted module path in the view; no gold-patch changed line reproduced (>=8 chars normalized); no narration tokens (bug/fix/patch/etc.); no spec-view identifier or comment echoing a patched repo symbol not already in the problem statement (the fix touches no distinctive def/class name; `symbols`/`cls` appear only in prose describing behavior and are already public in the problem_statement). Comments describe intended behavior abstractly and do not narrate the edit. Not a relaxed bundle. Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
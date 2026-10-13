# P2 adversarial audit — scikit-learn__scikit-learn-13439

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 
 -- impl-start
 def implementation_len (self : CompSeq) : Option Nat := Id.run do
-  return some self.steps.length
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 
 -- impl-start
 def implementation_len (self : CompSeq) : Option Nat := Id.run do
-  return some self.steps.length
+  return some (self.steps.length + 1)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,10 @@
 
 -- impl-start
 def implementation_len (self : CompSeq) : Option Nat := Id.run do
-  return some self.steps.length
+  if self.steps.isEmpty then
+    return some 0
+  else
+    return some (self.steps.length + 1)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -48,7 +48,7 @@
 
 -- impl-start
 def implementation_len (self : CompSeq) : Option Nat := Id.run do
-  return some self.steps.length
+  return some (self.steps.map (fun s => s.name)).length
 -- impl-end
 
 -- proof-start
@@ -56,5 +56,5 @@
     ∀ (self : CompSeq), problem_spec_len self (implementation_len self) := by
   intro self
   unfold problem_spec_len implementation_len
-  rfl
+  simp [List.length_map]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 
 -- impl-start
 def implementation_len (self : CompSeq) : Option Nat := Id.run do
-  return some self.steps.length
+  return some 2
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -48,7 +48,7 @@
 
 -- impl-start
 def implementation_len (self : CompSeq) : Option Nat := Id.run do
-  return some self.steps.length
+  return some self.steps.reverse.length
 -- impl-end
 
 -- proof-start
@@ -56,5 +56,5 @@
     ∀ (self : CompSeq), problem_spec_len self (implementation_len self) := by
   intro self
   unfold problem_spec_len implementation_len
-  rfl
+  simp [List.length_reverse]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The size of a sequential composition of named processing steps.

A composition is built from an ordered list of steps, each a named component.
Asking for the size of such a composition reports how many steps it contains —
the same count as the underlying list of steps.

The result is carried in `Option` to record whether the size query is defined:
a defined size is `some n`; an undefined size is `none`. For a composition the
size is always defined and equals the number of steps it holds.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Reporting the
-- size of the composition reads only the length of its underlying ordered list
-- of steps, which is modeled directly as `List.length`. There is no
-- `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- One step of a composition: a named component. Only the presence of the step
in the ordered list matters for the size query; `name` and `component` are the
observed parts of a step and are never inspected when counting. -/
structure CompStep where
  /-- the user-given name of the step -/
  name : String
  /-- opaque stand-in for the step's component object (never inspected here) -/
  component : String
deriving DecidableEq, Repr

/-- A sequential composition, observed through its ordered list of steps. -/
structure CompSeq where
  /-- the ordered list of steps -/
  steps : List CompStep
deriving Repr
-- pure-end

-- post-conditions-start
/-- The size of a composition is defined and equals the number of steps it
contains (directive 5 frame: the count is pinned to the input's step list, the
only thing the query reads). -/
def problem_spec_len (self : CompSeq) (result : Option Nat) : Prop :=
  result = some self.steps.length
-- post-conditions-end

-- impl-start
def implementation_len (self : CompSeq) : Option Nat := Id.run do
  return some self.steps.length
-- impl-end

-- proof-start
theorem correct_len :
    ∀ (self : CompSeq), problem_spec_len self (implementation_len self) := by
  intro self
  unfold problem_spec_len implementation_len
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a complete equational pin: problem_spec_len self result := result = some self.steps.length. len() has no params, no branches, single modeled op List.length (= Python len(list)). refinement.md legs all R/I; axioms=[] deep_model_references=[] (G-AX skip stub is legitimate — no callee contract to mis-model; A-leg correspondence vacuously holds vs real callee len(self.steps)). same_spec=True for all 6 attacks + positive control (checked via swebench_unified.markers.same_spec, lean backend).

### ATTACKS (project root; cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch bug `return none` (byte-identical to Solution_prepatch.lean impl): exit=1 (does NOT close). prepatch reproduced.
- atk_2 boundary off-by-one `some (steps.length+1)`: exit=1.
- atk_3 partial-domain `if isEmpty then some 0 else some (length+1)`: exit=1.
- atk_4 control-flow-effect `some (steps.map (fun s=>s.name)).length` (length-preserving): exit=0 CLOSES. #print axioms correct_len -> depends on axioms: [propext] (clean, no sorryAx/custom axiom).
- atk_5 ungrounded-oracle echo `some 2` (test asserts len==2): exit=1.
- atk_6 control-flow-effect `some steps.reverse.length` (length-preserving): exit=0 CLOSES. #print axioms -> [propext] clean.
positive control (gold `some steps.length`): exit=0.

### RESOLVE (swebench_unified.harness.run_resolve, docker oracle, timeout 1800):
- gold patch (len(self.steps)): resolved=True completed=True.
- atk_4 faithful patch (len([name for name,_ in self.steps])): resolved=True completed=True note=resolved.
- atk_6 faithful patch (len(list(reversed(self.steps)))): resolved=True completed=True note=resolved.
(First concurrent atk_4/atk_6 resolve attempts returned completed=False 'no report — harness error' under heavy contention/race; re-run sequentially both COMPLETED and RESOLVED. Baseline gold resolve also completed=True, confirming harness health.)

Both impls whose proof closes with clean axioms have materialized faithful patches that RESOLVE. Every impl that would NOT resolve (none, off-by-one, partial-domain, constant echo) FAILED to close the proof. No closing-but-non-resolving alternative exists -> verify⇒correct holds. VERDICT SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The size of a sequential composition of named processing steps.

A composition is built from an ordered list of steps, each a named component.
Asking for the size of such a composition reports how many steps it contains —
the same count as the underlying list of steps.

The result is carried in `Option` to record whether the size query is defined:
a defined size is `some n`; an undefined size is `none`. For a composition the
size is always defined and equals the number of steps it holds.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Reporting the
-- size of the composition reads only the length of its underlying ordered list
-- of steps, which is modeled directly as `List.length`. There is no
-- `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- One step of a composition: a named component. Only the presence of the step
in the ordered list matters for the size query; `name` and `component` are the
observed parts of a step and are never inspected when counting. -/
structure CompStep where
  /-- the user-given name of the step -/
  name : String
  /-- opaque stand-in for the step's component object (never inspected here) -/
  component : String
deriving DecidableEq, Repr

/-- A sequential composition, observed through its ordered list of steps. -/
structure CompSeq where
  /-- the ordered list of steps -/
  steps : List CompStep
deriving Repr
-- pure-end

-- post-conditions-start
/-- The size of a composition is defined and equals the number of steps it
contains (directive 5 frame: the count is pinned to the input's step list, the
only thing the query reads). -/
def problem_spec_len (self : CompSeq) (result : Option Nat) : Prop :=
  result = some self.steps.length
-- post-conditions-end

-- impl-start
def implementation_len (self : CompSeq) : Option Nat := Id.run do
  return some self.steps.length
-- impl-end

-- proof-start
theorem correct_len :
    ∀ (self : CompSeq), problem_spec_len self (implementation_len self) := by
  intro self
  unfold problem_spec_len implementation_len
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a complete equational pin: problem_spec_len self result := result = some self.steps.length. len() has no params, no branches, single modeled op List.length (= Python len(list)). refinement.md legs all R/I; axioms=[] deep_model_references=[] (G-AX skip stub is legitimate — no callee contract to mis-model; A-leg correspondence vacuously holds vs real callee len(self.steps)). same_spec=True for all 6 attacks + positive control (checked via swebench_unified.markers.same_spec, lean backend).

### ATTACKS (project root; cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch bug `return none` (byte-identical to Solution_prepatch.lean impl): exit=1 (does NOT close). prepatch reproduced.
- atk_2 boundary off-by-one `some (steps.length+1)`: exit=1.
- atk_3 partial-domain `if isEmpty then some 0 else some (length+1)`: exit=1.
- atk_4 control-flow-effect `some (steps.map (fun s=>s.name)).length` (length-preserving): exit=0 CLOSES. #print axioms correct_len -> depends on axioms: [propext] (clean, no sorryAx/custom axiom).
- atk_5 ungrounded-oracle echo `some 2` (test asserts len==2): exit=1.
- atk_6 control-flow-effect `some steps.reverse.length` (length-preserving): exit=0 CLOSES. #print axioms -> [propext] clean.
positive control (gold `some steps.length`): exit=0.

### RESOLVE (swebench_unified.harness.run_resolve, docker oracle, timeout 1800):
- gold patch (len(self.steps)): resolved=True completed=True.
- atk_4 faithful patch (len([name for name,_ in self.steps])): resolved=True completed=True note=resolved.
- atk_6 faithful patch (len(list(reversed(self.steps)))): resolved=True completed=True note=resolved.
(First concurrent atk_4/atk_6 resolve attempts returned completed=False 'no report — harness error' under heavy contention/race; re-run sequentially both COMPLETED and RESOLVED. Baseline gold resolve also completed=True, confirming harness health.)

Both impls whose proof closes with clean axioms have materialized faithful patches that RESOLVE. Every impl that would NOT resolve (none, off-by-one, partial-domain, constant echo) FAILED to close the proof. No closing-but-non-resolving alternative exists -> verify⇒correct holds. VERDICT SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function is the gold-patch addition Pipeline.__len__(self): return len(self.steps). Spec: problem_spec_len self result := result = some self.steps.length. Verification: lean_verify.sh exit 0, no sorry; #print axioms correct_len => 'does not depend on any axioms' (genuine rfl proof, no sorryAx). same_spec(Solution, Solution_prepatch, lean-backend) = True — spec region byte-identical; only impl differs (some steps.length vs none). Faithfulness: the bijection self.steps:list[(name,transform)] <-> List CompStep is content-blind and length-preserving, and Python len(list) <-> Lean List.length are identical on the step count. Post-patch __len__ ALWAYS returns a non-negative int equal to len(self.steps); it never raises and never reads a step's name/transform. The spec pins result to exactly some self.steps.length, which is precisely that value on every composition — no input where the modeled function disagrees with the real callee. Not too strong: the none case (pre-patch TypeError, no __len__) is correctly rejected, which is the intended discriminating clause, not spec drift. conformance_check.py differential-tests shadow==len(steps) over lengths 0..256 plus 120k fuzzed step lists with varied names/components (0 disagreements). Nat vs Python int gives no realizable divergence (list length bounded by memory).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage screen of the solver-visible spec view (Solution.lean: docstring + CompStep/CompSeq structures + problem_spec_len) against the PUBLIC problem_statement only (hints excluded). Public problem_statement openly names Pipeline, `__len__` (title: 'Pipeline should implement __len__'), len(pipe), pipe[:len(pipe)], and the steps list. The gold edit adds `def __len__(self): return len(self.steps)`. The spec view discloses only the abstract post-condition `result = some self.steps.length` ('size of a sequential composition equals the number of steps it holds') — which is exactly the required specification and is directly derivable from the public statement (len of a pipeline built from a list of steps = count of steps). It contains NONE of the gold-diff/beyond-problem_statement specifics: no `Pipeline`, no `__len__`, no python `self.steps`, no `pipeline.py` path, no `_iter`/`__getitem__` neighbor tokens, no diff marker/hunk header, no reproduced gold-diff line, and no bug->fix mechanism narration. Structures are abstract (CompSeq/CompStep) with name/component explicitly marked never-inspected. The gold-specific provenance (Pipeline.__len__, self.steps, pipeline.py:204, _iter) lives only in mapping.md/refinement.md/meta.json, which are builder-side derivation artifacts, not the solver spec view. Spec region confirmed byte-identical between Solution.lean and Solution_prepatch.lean (impl differs: `some self.steps.length` vs `none`), consistent with recorded G-PANEL-3 same_spec=True. Nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-11603

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_construct is a TOTAL exact-equality postcondition: for every (kind, distinct, filter) it pins the result to Except.error AggError.distinctNotAllowed iff (distinct ∧ ¬permitsDistinct kind), else Except.ok {kind, distinct, filter} with all three fields fixed. Any pointwise-deviant implementation therefore cannot satisfy it, and its proof cannot close. All 7 same-spec wrong impls failed to verify, each on its precise discriminating input (shown in the error goals). No verifying wrong impl exists, so there is no faithful patch to materialize/resolve — verify⇒correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,6 +74,7 @@
     | .avg => true
     | .count => true
     | .sum => true
+    | .max => true
     | _ => false
   if distinct && !permitted then
     return Except.error AggError.distinctNotAllowed
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,9 +71,7 @@
 def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
     Except AggError AggState := Id.run do
   let permitted : Bool := match kind with
-    | .avg => true
     | .count => true
-    | .sum => true
     | _ => false
   if distinct && !permitted then
     return Except.error AggError.distinctNotAllowed
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,6 @@
     return Except.error AggError.distinctNotAllowed
   let mut st : AggState := { kind := kind, distinct := false, filter := none }
   st := { st with distinct := distinct }
-  st := { st with filter := filter }
   return Except.ok st
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,18 +69,8 @@
 
 -- impl-start
 def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
-    Except AggError AggState := Id.run do
-  let permitted : Bool := match kind with
-    | .avg => true
-    | .count => true
-    | .sum => true
-    | _ => false
-  if distinct && !permitted then
-    return Except.error AggError.distinctNotAllowed
-  let mut st : AggState := { kind := kind, distinct := false, filter := none }
-  st := { st with distinct := distinct }
-  st := { st with filter := filter }
-  return Except.ok st
+    Except AggError AggState :=
+  Except.ok { kind := kind, distinct := distinct, filter := filter }
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,6 @@
   if distinct && !permitted then
     return Except.error AggError.distinctNotAllowed
   let mut st : AggState := { kind := kind, distinct := false, filter := none }
-  st := { st with distinct := distinct }
   st := { st with filter := filter }
   return Except.ok st
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,7 @@
     | .count => true
     | .sum => true
     | _ => false
-  if distinct && !permitted then
+  if distinct && permitted then
     return Except.error AggError.distinctNotAllowed
   let mut st : AggState := { kind := kind, distinct := false, filter := none }
   st := { st with distinct := distinct }
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,13 +74,11 @@
     | .avg => true
     | .count => true
     | .sum => true
+    | .min => true
     | _ => false
   if distinct && !permitted then
     return Except.error AggError.distinctNotAllowed
-  let mut st : AggState := { kind := kind, distinct := false, filter := none }
-  st := { st with distinct := distinct }
-  st := { st with filter := filter }
-  return Except.ok st
+  return Except.ok { kind := kind, distinct := distinct, filter := filter }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing an aggregate computation with a request to operate over only the
DISTINCT values of its argument.

Each aggregate computation has a kind (averaging, counting, summation, maximum,
minimum, and the two statistical-dispersion kinds). Whether a kind may be asked
to range over only distinct values is a per-kind policy: the averaging,
counting, and summation kinds support it; the others do not.

Constructing an aggregate is an input→output relation: given the kind, whether
distinct operation is requested, and an optional row filter, the construction
either fails — exactly when distinct operation is requested for a kind whose
policy forbids it — or succeeds, yielding an aggregate that records the
requested distinct flag and filter unchanged.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the construction is
-- modeled deeply with concrete operations (a per-kind policy lookup, a guarded
-- failure, and field assignments).
-- axioms-end

-- pure-start
/-- The kinds of aggregate computation (one per concrete aggregate). -/
inductive AggKind where
  | avg | count | sum | max | min | stdDev | variance
deriving DecidableEq, Repr

/-- The single failure observable here: distinct operation was requested for a
kind whose policy forbids it. -/
inductive AggError where
  | distinctNotAllowed
deriving DecidableEq, Repr

/-- A constructed aggregate, carrying only the fields relevant to this behavior:
its kind, whether it ranges over distinct values, and its optional row filter. -/
structure AggState where
  kind : AggKind
  distinct : Bool
  filter : Option String
deriving DecidableEq, Repr

/-- The per-kind distinct policy: the averaging, counting, and summation kinds
may range over distinct values; the others may not. -/
def permitsDistinct : AggKind → Bool
  | .avg => true
  | .count => true
  | .sum => true
  | _ => false
-- pure-end

-- post-conditions-start
/-- Constructing an aggregate fails exactly when distinct operation is requested
for a kind whose policy forbids it; otherwise it succeeds, recording the kind,
the requested distinct flag, and the filter unchanged. -/
def problem_spec_construct (kind : AggKind) (distinct : Bool) (filter : Option String)
    (result : Except AggError AggState) : Prop :=
  if distinct = true ∧ permitsDistinct kind = false then
    result = Except.error AggError.distinctNotAllowed
  else
    result = Except.ok { kind := kind, distinct := distinct, filter := filter }
-- post-conditions-end

-- impl-start
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  let permitted : Bool := match kind with
    | .avg => true
    | .count => true
    | .sum => true
    | _ => false
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st
-- impl-end

-- proof-start
theorem correct_construct :
    ∀ (kind : AggKind) (distinct : Bool) (filter : Option String),
      problem_spec_construct kind distinct filter
        (implementation_construct kind distinct filter) := by
  intro kind distinct filter
  unfold problem_spec_construct implementation_construct permitsDistinct
  cases kind <;> cases distinct <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 verifier python for same_spec.

SAME_SPEC: all 7 attacks return same_spec=True vs Solution.lean (axioms/pure/pre/post byte-identical; only impl region edited). Verified via swebench_unified.markers.same_spec + backends.get_backend('lean').

### COMMANDS (each: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4 at a time):
- positive_control.lean -> exit 0 (verifies, no sorry). #print axioms correct_construct => 'does not depend on any axioms' (clean). [log_pos.txt, log_axcheck.txt]
- prepatch.lean -> exit 1 (FAILS to close on sum×distinct=true; reproduces F2P bug test_distinct_on_aggregate). [log_prepatch.txt]
- atk_1.lean (partial-domain / over-permissive: also permit .max) -> exit 1, goal stuck on kind=max,distinct=true (spec wants error, impl gives ok).
- atk_2.lean (prepatch echo: only .count permits) -> exit 1, stuck on kind=sum,distinct=true.
- atk_3.lean (control-flow-effect: dropped filter assignment) -> exit 1, stuck on variance,distinct=false (filter mismatch).
- atk_4.lean (boundary: never error, always Except.ok) -> exit 1, stuck on variance,distinct=true (spec wants error).
- atk_5.lean (dropped distinct-flag write; records false) -> exit 1, stuck on sum,distinct=true.
- atk_6.lean (inverted guard: error when distinct && permitted) -> exit 1, stuck on variance,distinct=true.
- atk_7.lean (ungrounded-oracle echo + off-by: also permit .min) -> exit 1, stuck on min,distinct=true.

RESULT: 7/7 same-spec wrong impls FAIL to close; positive control PASSES with zero axioms. Because NO wrong impl produced a closing clean-axiom proof, protocol step 2 (materialize faithful patch + run_resolve) has no applicable candidates — no resolve run required, none omitted.

A-LEG / REFINEMENT AUDIT (plan §4 focus): refinement.md declares NO axioms — grep '^\s*axiom ' Solution.lean => NONE; axiom_check.py is a legitimate SKIP STUB (deep model, per mapping.md callee-provenance: super().__init__ abstracted out, not a consumed/reference callee). Leg tags: 5×R + 1×I, zero kind-3, zero A-consumed/A-reference — no axiom correspondence to falsify. Model↔patch correspondence is faithful: permitsDistinct/permitted (post-patch policy avg/count/sum=true) ↔ per-class allow_distinct as patched; `if distinct && !permitted -> Except.error` ↔ `if distinct and not self.allow_distinct: raise TypeError`; field writes ↔ self.distinct/self.filter; Except.ok ↔ successful construction. The R/I surface is differentially tested by G-CONF/conformance_check.py against the real patched aggregate classes (full matrix + 1.2e5 draws, seed 20240612). Correspondence holds.

VERDICT: SOUND — spec is a total exact-equality postcondition; ≥5 (7) distinct same-spec wrong impls all fail to verify while the gold verifies with clean axioms; no verify⇏correct gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_construct is a TOTAL exact-equality postcondition: for every (kind, distinct, filter) it pins the result to Except.error AggError.distinctNotAllowed iff (distinct ∧ ¬permitsDistinct kind), else Except.ok {kind, distinct, filter} with all three fields fixed. Any pointwise-deviant implementation therefore cannot satisfy it, and its proof cannot close. All 7 same-spec wrong impls failed to verify, each on its precise discriminating input (shown in the error goals). No verifying wrong impl exists, so there is no faithful patch to materialize/resolve — verify⇒correct holds.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing an aggregate computation with a request to operate over only the
DISTINCT values of its argument.

Each aggregate computation has a kind (averaging, counting, summation, maximum,
minimum, and the two statistical-dispersion kinds). Whether a kind may be asked
to range over only distinct values is a per-kind policy: the averaging,
counting, and summation kinds support it; the others do not.

Constructing an aggregate is an input→output relation: given the kind, whether
distinct operation is requested, and an optional row filter, the construction
either fails — exactly when distinct operation is requested for a kind whose
policy forbids it — or succeeds, yielding an aggregate that records the
requested distinct flag and filter unchanged.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the construction is
-- modeled deeply with concrete operations (a per-kind policy lookup, a guarded
-- failure, and field assignments).
-- axioms-end

-- pure-start
/-- The kinds of aggregate computation (one per concrete aggregate). -/
inductive AggKind where
  | avg | count | sum | max | min | stdDev | variance
deriving DecidableEq, Repr

/-- The single failure observable here: distinct operation was requested for a
kind whose policy forbids it. -/
inductive AggError where
  | distinctNotAllowed
deriving DecidableEq, Repr

/-- A constructed aggregate, carrying only the fields relevant to this behavior:
its kind, whether it ranges over distinct values, and its optional row filter. -/
structure AggState where
  kind : AggKind
  distinct : Bool
  filter : Option String
deriving DecidableEq, Repr

/-- The per-kind distinct policy: the averaging, counting, and summation kinds
may range over distinct values; the others may not. -/
def permitsDistinct : AggKind → Bool
  | .avg => true
  | .count => true
  | .sum => true
  | _ => false
-- pure-end

-- post-conditions-start
/-- Constructing an aggregate fails exactly when distinct operation is requested
for a kind whose policy forbids it; otherwise it succeeds, recording the kind,
the requested distinct flag, and the filter unchanged. -/
def problem_spec_construct (kind : AggKind) (distinct : Bool) (filter : Option String)
    (result : Except AggError AggState) : Prop :=
  if distinct = true ∧ permitsDistinct kind = false then
    result = Except.error AggError.distinctNotAllowed
  else
    result = Except.ok { kind := kind, distinct := distinct, filter := filter }
-- post-conditions-end

-- impl-start
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  let permitted : Bool := match kind with
    | .avg => true
    | .count => true
    | .sum => true
    | _ => false
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st
-- impl-end

-- proof-start
theorem correct_construct :
    ∀ (kind : AggKind) (distinct : Bool) (filter : Option String),
      problem_spec_construct kind distinct filter
        (implementation_construct kind distinct filter) := by
  intro kind distinct filter
  unfold problem_spec_construct implementation_construct permitsDistinct
  cases kind <;> cases distinct <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 verifier python for same_spec.

SAME_SPEC: all 7 attacks return same_spec=True vs Solution.lean (axioms/pure/pre/post byte-identical; only impl region edited). Verified via swebench_unified.markers.same_spec + backends.get_backend('lean').

### COMMANDS (each: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4 at a time):
- positive_control.lean -> exit 0 (verifies, no sorry). #print axioms correct_construct => 'does not depend on any axioms' (clean). [log_pos.txt, log_axcheck.txt]
- prepatch.lean -> exit 1 (FAILS to close on sum×distinct=true; reproduces F2P bug test_distinct_on_aggregate). [log_prepatch.txt]
- atk_1.lean (partial-domain / over-permissive: also permit .max) -> exit 1, goal stuck on kind=max,distinct=true (spec wants error, impl gives ok).
- atk_2.lean (prepatch echo: only .count permits) -> exit 1, stuck on kind=sum,distinct=true.
- atk_3.lean (control-flow-effect: dropped filter assignment) -> exit 1, stuck on variance,distinct=false (filter mismatch).
- atk_4.lean (boundary: never error, always Except.ok) -> exit 1, stuck on variance,distinct=true (spec wants error).
- atk_5.lean (dropped distinct-flag write; records false) -> exit 1, stuck on sum,distinct=true.
- atk_6.lean (inverted guard: error when distinct && permitted) -> exit 1, stuck on variance,distinct=true.
- atk_7.lean (ungrounded-oracle echo + off-by: also permit .min) -> exit 1, stuck on min,distinct=true.

RESULT: 7/7 same-spec wrong impls FAIL to close; positive control PASSES with zero axioms. Because NO wrong impl produced a closing clean-axiom proof, protocol step 2 (materialize faithful patch + run_resolve) has no applicable candidates — no resolve run required, none omitted.

A-LEG / REFINEMENT AUDIT (plan §4 focus): refinement.md declares NO axioms — grep '^\s*axiom ' Solution.lean => NONE; axiom_check.py is a legitimate SKIP STUB (deep model, per mapping.md callee-provenance: super().__init__ abstracted out, not a consumed/reference callee). Leg tags: 5×R + 1×I, zero kind-3, zero A-consumed/A-reference — no axiom correspondence to falsify. Model↔patch correspondence is faithful: permitsDistinct/permitted (post-patch policy avg/count/sum=true) ↔ per-class allow_distinct as patched; `if distinct && !permitted -> Except.error` ↔ `if distinct and not self.allow_distinct: raise TypeError`; field writes ↔ self.distinct/self.filter; Except.ok ↔ successful construction. The R/I surface is differentially tested by G-CONF/conformance_check.py against the real patched aggregate classes (full matrix + 1.2e5 draws, seed 20240612). Correspondence holds.

VERDICT: SOUND — spec is a total exact-equality postcondition; ≥5 (7) distinct same-spec wrong impls all fail to verify while the gold verifies with clean axioms; no verify⇏correct gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no divergence found. Verification: (1) lean_verify.sh exit 0; `#print axioms correct_construct` => 'does not depend on any axioms' (no sorryAx, proof genuine). (2) markers.same_spec(local, reference, lean_tables)=True — frozen spec region byte-identical to reference. (3) Modeled function `construct` maps Aggregate.__init__ (django/db/models/aggregates.py:24-29 @ f618e033 + gold patch). Real guard `if distinct and not self.allow_distinct: raise TypeError(...)` then stores self.distinct/self.filter exactly matches spec: error iff (distinct ∧ ¬permitsDistinct kind) else ok recording distinct+filter unchanged. permitsDistinct={avg,count,sum:true; max,min,stdDev,variance:false} matches real post-patch allow_distinct across ALL 7 kinds (Count=True base :108, Avg+Sum patched, rest inherit Aggregate.allow_distinct=False). Verified per-class __init__ overrides (Count, StdDev, Variance) route distinct through **extra into super().__init__, so the guard applies uniformly — no kind escapes the modeled policy, spec is not too strong on any kind. (4) Abstractions (filter presence-only; super().__init__/Star-filter ValueError excluded) are correctly scoped to the distinct-policy observable and don't over-claim on the modeled domain. (5) G-CONF: full (kind×distinct×filter) matrix + 120k random draws vs real patched classes => 0 disagreements. Spec is neither too strong nor drifting relative to the real repo behavior. G-EQ=fail in meta is an equivalence-attack artifact, orthogonal to this panel-2 faithfulness question.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is frozen (swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean) == True) and the mechanical G-LEAK screen passes clean (no diff markers, no reproduced gold line, no patched file/module path, no spec-view identifier or comment naming a patched repo symbol, no narration). Semantic review of the spec view: the gold edit adds `allow_distinct = True` to Avg and Sum in django/db/models/aggregates.py. The PUBLIC problem_statement already spells the fix out verbatim: 'Add DISTINCT support for Avg and Sum aggregates ... just involve setting these classes as allowing DISTINCT, and could also be applied to Min and Max (although pointless).' The spec view states only the abstract desired contract: permitsDistinct is true for avg/count/sum and false for max/min/stdDev/variance, with an Except-carrier construction relation. This reveals nothing beyond the problem statement: (1) avg/sum permitting distinct is exactly what the public issue demands; (2) count's true is pre-existing base behavior, not the edit; (3) max/min false matches the patch not touching them, consistent with the issue's 'pointless for Min and Max'. No Python class names (Avg/Sum/Count), no `allow_distinct` attribute name, no Aggregate.__init__ symbol, and no file path appear. The actual pre->post EDIT (buggy base policy where only count permits distinct vs. fixed policy) lives entirely in the impl region, which is ELIDED from the spec view (impl/proof regions show 'elided — supplied by the consumer'). The distinguishing information is confined to the elided impl, not the frozen spec. No leakage of the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

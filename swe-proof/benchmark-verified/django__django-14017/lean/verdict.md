# P2 adversarial audit — django__django-14017

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
 -- impl-start
 def implementation_mergeFilters
     (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do
-  if !(other.isFilter || other.boolValued) then
+  if !other.isFilter then
     return MergeResult.rejected
   if other.empty then
     return MergeResult.keepLeft
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,10 +79,10 @@
     (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do
   if !(other.isFilter || other.boolValued) then
     return MergeResult.rejected
+  if self.empty then
+    return MergeResult.keepRight
   if other.empty then
     return MergeResult.keepLeft
-  if self.empty then
-    return MergeResult.keepRight
   return MergeResult.merged conn
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,8 +79,6 @@
     (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do
   if !(other.isFilter || other.boolValued) then
     return MergeResult.rejected
-  if other.empty then
-    return MergeResult.keepLeft
   if self.empty then
     return MergeResult.keepRight
   return MergeResult.merged conn
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
 -- impl-start
 def implementation_mergeFilters
     (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do
-  if !(other.isFilter || other.boolValued) then
+  if !(other.isFilter && other.boolValued) then
     return MergeResult.rejected
   if other.empty then
     return MergeResult.keepLeft
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,10 +79,6 @@
     (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do
   if !(other.isFilter || other.boolValued) then
     return MergeResult.rejected
-  if other.empty then
-    return MergeResult.keepLeft
-  if self.empty then
-    return MergeResult.keepRight
   return MergeResult.merged conn
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,8 +77,6 @@
 -- impl-start
 def implementation_mergeFilters
     (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do
-  if !(other.isFilter || other.boolValued) then
-    return MergeResult.rejected
   if other.empty then
     return MergeResult.keepLeft
   if self.empty then
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,9 +80,9 @@
   if !(other.isFilter || other.boolValued) then
     return MergeResult.rejected
   if other.empty then
+    return MergeResult.keepRight
+  if self.empty then
     return MergeResult.keepLeft
-  if self.empty then
-    return MergeResult.keepRight
   return MergeResult.merged conn
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is consumed by the modeled behavior. The decision the
-- modeled procedure makes (whether an operand may be merged, and which branch is
-- taken) is determined entirely by observable attributes of the two operands,
-- which are carried as fields of the input carriers below and modeled deeply.
-- Hence there is no `opaque` callee and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- A logical connector used to merge two filter conditions. -/
inductive Connector
  | and_
  | or_
  deriving DecidableEq, Repr

/-- The left-hand operand: a filter node. The only behaviourally relevant
attribute here is whether it is *empty* (carries no sub-conditions). -/
structure FilterNode where
  /-- `true` iff this filter node carries no sub-conditions. -/
  empty : Bool
  deriving DecidableEq, Repr

/-- The right-hand operand of a merge. Three observable attributes drive the
behaviour:
* `isFilter` — whether the operand is itself a filter node;
* `boolValued` — whether the operand is a standalone boolean-valued condition
  (i.e. usable on its own as a filter), exactly the property the merge inspects;
* `empty` — whether the operand is itself trivial (carries no content), which is
  observed uniformly for any accepted operand. -/
structure Operand where
  isFilter : Bool
  boolValued : Bool
  empty : Bool
  deriving DecidableEq, Repr

/-- Outcome of attempting to merge the left filter node with the operand under a
connector. -/
inductive MergeResult
  | /-- the operand is not a valid thing to merge: the merge is rejected. -/
    rejected
  | /-- the operand contributes nothing: the result is (a copy of) the left node. -/
    keepLeft
  | /-- the left node contributes nothing: the result is (a copy of) the operand. -/
    keepRight
  | /-- a fresh combined node is built, joining both operands under `conn`. -/
    merged (conn : Connector)
  deriving DecidableEq, Repr

/-- The mergeability test: an operand may be merged iff it is itself a filter
node, or it is a standalone boolean-valued condition. -/
def mergeable (other : Operand) : Bool :=
  other.isFilter || other.boolValued
-- pure-end

-- post-conditions-start
/-- Merging the left filter node `self` with `other` under connector `conn`:
* if `other` is neither a filter node nor a standalone boolean condition, the
  merge is rejected;
* otherwise the outcome is fully determined: an empty operand contributes
  nothing (the left node is kept), failing that an empty left node contributes
  nothing (the operand is kept), and otherwise a fresh node merging both under
  `conn` is produced. -/
def problem_spec_mergeFilters
    (self : FilterNode) (other : Operand) (conn : Connector)
    (result : MergeResult) : Prop :=
  (mergeable other = false ↔ result = MergeResult.rejected)
  ∧ (mergeable other = true →
      result =
        (if other.empty then MergeResult.keepLeft
         else if self.empty then MergeResult.keepRight
         else MergeResult.merged conn))
-- post-conditions-end

-- impl-start
def implementation_mergeFilters
    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do
  if !(other.isFilter || other.boolValued) then
    return MergeResult.rejected
  if other.empty then
    return MergeResult.keepLeft
  if self.empty then
    return MergeResult.keepRight
  return MergeResult.merged conn
-- impl-end

-- proof-start
theorem correct_mergeFilters :
    ∀ (self : FilterNode) (other : Operand) (conn : Connector),
      problem_spec_mergeFilters self other conn
        (implementation_mergeFilters self other conn) := by
  intro self other conn
  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable
  obtain ⟨se⟩ := self
  obtain ⟨of, ob, oe⟩ := other
  cases conn <;> cases se <;> cases of <;> cases ob <;> cases oe <;> decide
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_mergeFilters is a TOTAL, deterministic functional spec. It pins `result` uniquely for every input: (mergeable other = false ↔ result = rejected) AND (mergeable other = true → result = the exact `if other.empty then keepLeft else if self.empty then keepRight else merged conn` cascade). mergeable = other.isFilter || other.boolValued. There is no slack: any impl whose correct_ proof closes must be extensionally gold-equal, hence its patch must resolve.

SAME-SPEC: all 7 attacks + positive control are byte-identical spec via swebench_unified.markers.same_spec (get_backend('lean')) => True. Only the impl region edited; axioms/pure/pre/post byte-identical.

### VERIFICATION (project root; ran concurrently in 2 batches of 4 via background bash jobs; cmd `bash scripts/lean_verify.sh <path>`):
  pos_control.lean => exit 0 (clean, empty output, no sorry). #print axioms correct_mergeFilters => 'does not depend on any axioms' (clean).
  atk_1 (PREPATCH BUG: guard `!other.isFilter`, drops boolValued disjunct — wrongly rejects standalone conditional operand) => exit 1. decide reports goal false (isFilter=false,boolValued=true operand: prepatch returns rejected, spec requires non-rejected). Prepatch bug reproduced.
  atk_2 (boundary: swap empty-check order, self.empty before other.empty) => exit 1.
  atk_3 (control-flow-effect: drop the other.empty short-circuit) => exit 1.
  atk_4 (wrong guard: && instead of ||) => exit 1.
  atk_5 (always merged when mergeable; ignore empty short-circuits) => exit 1.
  atk_6 (ungrounded-oracle echo: never reject, accept everything) => exit 1.
  atk_7 (swap keepLeft/keepRight outcomes) => exit 1.
All 7 attacks retained the GOLD proof tactic (cases <;> decide) — strongest closing attempt — and all fail with genuine `... is false` decide goals (not sorry/import artifacts; logs inspected). No wrong impl produced a closing clean-axiom proof, so NO faithful patch needed materializing/resolving (patches={}); verify⇒correct holds on all attacks.

REFINEMENT.MD AUDIT: 5 legs, all tagged R (type refinement); zero kind-3 (changed-inexpressible) legs. axioms region legitimately empty — the modeled decision (guard + branch selection) is a language-level observation of operand attributes (isinstance(other,Q); getattr(other,'conditional',False) is True; bool() of self/other) modeled DEEPLY as struct fields Operand.{isFilter,boolValued,empty} / FilterNode.empty; no external repo callee is consumed by the proof, so there are NO A-legs (A-consumed or A-reference) whose correspondence could fail, and G-AX is a valid skip stub (meta G-AX status=pass, skip). R-mapping matches patch.diff exactly: post-patch guard `isinstance(other,Q) or getattr(other,'conditional',False) is True` ↔ `other.isFilter || other.boolValued`; empty short-circuits (`not other`/`not self` via tree.Node.__bool__) ↔ Operand.empty/FilterNode.empty; conn AND/OR ↔ Connector.and_/or_. Cross-validated by G-CONF (conformance_check.py, 120024 inputs, seed=14017, 0 disagreements against real post-patch Q._combine).

CONCLUSION: The spec strictly discriminates gold from every bug variant including the actual prepatch bug; ≥5 (here 7) distinct wrong impls attempted with the strongest proof tactic, none verifies, so none required a resolve run. Spec is SOUND (verify⇒correct).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

-- axioms-start
-- No UNCHANGED callee is consumed by the modeled behavior. The decision the
-- modeled procedure makes (whether an operand may be merged, and which branch is
-- taken) is determined entirely by observable attributes of the two operands,
-- which are carried as fields of the input carriers below and modeled deeply.
-- Hence there is no `opaque` callee and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- A logical connector used to merge two filter conditions. -/
inductive Connector
  | and_
  | or_
  deriving DecidableEq, Repr

/-- The left-hand operand: a filter node. The only behaviourally relevant
attribute here is whether it is *empty* (carries no sub-conditions). -/
structure FilterNode where
  /-- `true` iff this filter node carries no sub-conditions. -/
  empty : Bool
  deriving DecidableEq, Repr

/-- The right-hand operand of a merge. Three observable attributes drive the
behaviour:
* `isFilter` — whether the operand is itself a filter node;
* `boolValued` — whether the operand is a standalone boolean-valued condition
  (i.e. usable on its own as a filter), exactly the property the merge inspects;
* `empty` — whether the operand is itself trivial (carries no content), which is
  observed uniformly for any accepted operand. -/
structure Operand where
  isFilter : Bool
  boolValued : Bool
  empty : Bool
  deriving DecidableEq, Repr

/-- Outcome of attempting to merge the left filter node with the operand under a
connector. -/
inductive MergeResult
  | /-- the operand is not a valid thing to merge: the merge is rejected. -/
    rejected
  | /-- the operand contributes nothing: the result is (a copy of) the left node. -/
    keepLeft
  | /-- the left node contributes nothing: the result is (a copy of) the operand. -/
    keepRight
  | /-- a fresh combined node is built, joining both operands under `conn`. -/
    merged (conn : Connector)
  deriving DecidableEq, Repr

/-- The mergeability test: an operand may be merged iff it is itself a filter
node, or it is a standalone boolean-valued condition. -/
def mergeable (other : Operand) : Bool :=
  other.isFilter || other.boolValued
-- pure-end

-- post-conditions-start
/-- Merging the left filter node `self` with `other` under connector `conn`:
* if `other` is neither a filter node nor a standalone boolean condition, the
  merge is rejected;
* otherwise the outcome is fully determined: an empty operand contributes
  nothing (the left node is kept), failing that an empty left node contributes
  nothing (the operand is kept), and otherwise a fresh node merging both under
  `conn` is produced. -/
def problem_spec_mergeFilters
    (self : FilterNode) (other : Operand) (conn : Connector)
    (result : MergeResult) : Prop :=
  (mergeable other = false ↔ result = MergeResult.rejected)
  ∧ (mergeable other = true →
      result =
        (if other.empty then MergeResult.keepLeft
         else if self.empty then MergeResult.keepRight
         else MergeResult.merged conn))
-- post-conditions-end

-- impl-start
def implementation_mergeFilters
    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do
  if !(other.isFilter || other.boolValued) then
    return MergeResult.rejected
  if other.empty then
    return MergeResult.keepLeft
  if self.empty then
    return MergeResult.keepRight
  return MergeResult.merged conn
-- impl-end

-- proof-start
theorem correct_mergeFilters :
    ∀ (self : FilterNode) (other : Operand) (conn : Connector),
      problem_spec_mergeFilters self other conn
        (implementation_mergeFilters self other conn) := by
  intro self other conn
  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable
  obtain ⟨se⟩ := self
  obtain ⟨of, ob, oe⟩ := other
  cases conn <;> cases se <;> cases of <;> cases ob <;> cases oe <;> decide
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_mergeFilters is a TOTAL, deterministic functional spec. It pins `result` uniquely for every input: (mergeable other = false ↔ result = rejected) AND (mergeable other = true → result = the exact `if other.empty then keepLeft else if self.empty then keepRight else merged conn` cascade). mergeable = other.isFilter || other.boolValued. There is no slack: any impl whose correct_ proof closes must be extensionally gold-equal, hence its patch must resolve.

SAME-SPEC: all 7 attacks + positive control are byte-identical spec via swebench_unified.markers.same_spec (get_backend('lean')) => True. Only the impl region edited; axioms/pure/pre/post byte-identical.

### VERIFICATION (project root; ran concurrently in 2 batches of 4 via background bash jobs; cmd `bash scripts/lean_verify.sh <path>`):
  pos_control.lean => exit 0 (clean, empty output, no sorry). #print axioms correct_mergeFilters => 'does not depend on any axioms' (clean).
  atk_1 (PREPATCH BUG: guard `!other.isFilter`, drops boolValued disjunct — wrongly rejects standalone conditional operand) => exit 1. decide reports goal false (isFilter=false,boolValued=true operand: prepatch returns rejected, spec requires non-rejected). Prepatch bug reproduced.
  atk_2 (boundary: swap empty-check order, self.empty before other.empty) => exit 1.
  atk_3 (control-flow-effect: drop the other.empty short-circuit) => exit 1.
  atk_4 (wrong guard: && instead of ||) => exit 1.
  atk_5 (always merged when mergeable; ignore empty short-circuits) => exit 1.
  atk_6 (ungrounded-oracle echo: never reject, accept everything) => exit 1.
  atk_7 (swap keepLeft/keepRight outcomes) => exit 1.
All 7 attacks retained the GOLD proof tactic (cases <;> decide) — strongest closing attempt — and all fail with genuine `... is false` decide goals (not sorry/import artifacts; logs inspected). No wrong impl produced a closing clean-axiom proof, so NO faithful patch needed materializing/resolving (patches={}); verify⇒correct holds on all attacks.

REFINEMENT.MD AUDIT: 5 legs, all tagged R (type refinement); zero kind-3 (changed-inexpressible) legs. axioms region legitimately empty — the modeled decision (guard + branch selection) is a language-level observation of operand attributes (isinstance(other,Q); getattr(other,'conditional',False) is True; bool() of self/other) modeled DEEPLY as struct fields Operand.{isFilter,boolValued,empty} / FilterNode.empty; no external repo callee is consumed by the proof, so there are NO A-legs (A-consumed or A-reference) whose correspondence could fail, and G-AX is a valid skip stub (meta G-AX status=pass, skip). R-mapping matches patch.diff exactly: post-patch guard `isinstance(other,Q) or getattr(other,'conditional',False) is True` ↔ `other.isFilter || other.boolValued`; empty short-circuits (`not other`/`not self` via tree.Node.__bool__) ↔ Operand.empty/FilterNode.empty; conn AND/OR ↔ Connector.and_/or_. Cross-validated by G-CONF (conformance_check.py, 120024 inputs, seed=14017, 0 disagreements against real post-patch Q._combine).

CONCLUSION: The spec strictly discriminates gold from every bug variant including the actual prepatch bug; ≥5 (here 7) distinct wrong impls attempted with the strongest proof tactic, none verifies, so none required a resolve run. Spec is SOUND (verify⇒correct).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-14017 lean bundle (modeled fn Q._combine post-patch). MECHANICAL: same_spec(Solution, Solution_prepatch)=True (spec region byte-identical); scripts/lean_verify.sh Solution.lean exit 0 (compiles, no sorry); `#print axioms correct_mergeFilters` => does not depend on any axioms (proof real, no sorryAx). SEMANTIC: base HEAD is pre-patch, worktree has gold patch applied so its _combine is the modeled post-patch behavior. spec mergeable = isFilter||boolValued maps exactly to post-patch guard `isinstance(other,Q) or getattr(other,'conditional',False) is True` via mapping.md bijection (isFilter:=isinstance(other,Q), boolValued:=getattr(...,'conditional',False) is True, empty:=not bool(other)). Branch order (other.empty->keepLeft, self.empty->keepRight, else merged conn) matches real `if not other / elif not self / else`. Ran an independent differential test of the spec post-conditions vs the REAL post-patch Q._combine over a diverse operand zoo: Q()/Q(x=1); conditional=True truthy; conditional=True falsey; conditional=1 (non-`is True` -> correctly rejected); conditional='yes'; missing attribute; no-__bool__ object; x2 self states x2 connectors => 0 divergences. Confirmed non-vacuous: on a boolValued-only operand (isFilter=F,boolValued=T) spec yields 'merged' matching post-patch, while pre-patch impl would 'reject' -> spec captures exactly the fix. No diverging input found; spec is neither too strong nor drifting. Note conformance_check.py errors ('No module named django') if run in an env without django installed, but that is a runner-env artifact, not a spec defect; verified directly against the worktree django source instead.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, lean flavor) passes: no diff markers, no gold-patch line reproduced (>=8 chars), no patched file path/module, no spec-view identifier embedding a distinctive patched symbol, no bug/fix narration in comments. same_spec(Solution, Solution_prepatch) = True (spec region byte-identical). Semantic review beyond the lexical screen: the gold edit broadens the guard `if not isinstance(other, Q):` to also accept `getattr(other,'conditional',False) is True`. The public problem_statement ALREADY discloses (a) the modeled function `Q._combine`, (b) the exact buggy guard line via the traceback, and (c) the target fix — that `Q() & Exists(...)` must work, i.e. a standalone boolean-valued expression (Exists) must be accepted. The spec view encodes only abstract correct behavior: `mergeable other = other.isFilter || other.boolValued` ("an operand may be merged iff it is itself a filter node, or it is a standalone boolean-valued condition"). The concrete gold discriminator name `conditional` never appears in the spec view (abstracted to the generic field `boolValued`); identifiers (FilterNode, Operand, MergeResult, mergeFilters) are all generic and do not echo any patched repo symbol. Encoding the target post-condition is inherent to any faithful correctness spec and merely restates what the task already makes public; it does not localize or trivialize the edit beyond the public problem_statement. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

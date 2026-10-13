# P2 adversarial audit — django__django-13569

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `atk_7_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,9 +57,11 @@
 def randomGroupingColumns
     (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=
   Id.run do
-    return []
+    if self.function = "RANDOM" then
+      return []
+    else
+      return [self.function]
 -- impl-end
-
 -- proof-start
 theorem correct_randomGroupingColumns :
     ∀ (self : OrderingExpr) (outAlias : Option String),
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,9 +57,10 @@
 def randomGroupingColumns
     (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=
   Id.run do
-    return []
+    match outAlias with
+    | none => return []
+    | some _ => return [self.function]
 -- impl-end
-
 -- proof-start
 theorem correct_randomGroupingColumns :
     ∀ (self : OrderingExpr) (outAlias : Option String),
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,9 +57,8 @@
 def randomGroupingColumns
     (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=
   Id.run do
-    return []
+    return [self.function]
 -- impl-end
-
 -- proof-start
 theorem correct_randomGroupingColumns :
     ∀ (self : OrderingExpr) (outAlias : Option String),
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -57,9 +57,10 @@
 def randomGroupingColumns
     (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=
   Id.run do
-    return []
+    let mut acc : List GroupByCol := [self.function]
+    acc := []
+    return acc
 -- impl-end
-
 -- proof-start
 theorem correct_randomGroupingColumns :
     ∀ (self : OrderingExpr) (outAlias : Option String),
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,9 +57,8 @@
 def randomGroupingColumns
     (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=
   Id.run do
-    return []
+    return [""]
 -- impl-end
-
 -- proof-start
 theorem correct_randomGroupingColumns :
     ∀ (self : OrderingExpr) (outAlias : Option String),
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,9 +57,11 @@
 def randomGroupingColumns
     (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=
   Id.run do
-    return []
+    if self.function.length = 0 then
+      return []
+    else
+      return [self.function]
 -- impl-end
-
 -- proof-start
 theorem correct_randomGroupingColumns :
     ∀ (self : OrderingExpr) (outAlias : Option String),
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Grouping columns contributed by a non-deterministic ordering expression.

When an aggregated result set is also ordered, each ordering term is asked which
underlying stored columns it adds to the grouping of the result. A plain column
reference contributes that column; an aggregate contributes the columns of its
operands. But an ordering term that is a non-deterministic value generator — a
random-value function with arity zero and therefore no underlying stored column —
has nothing to group on. Asking such a term for its grouping columns must yield
the empty collection, so that ordering a result randomly never alters how the
aggregated rows are grouped.

This file models that single query: given such a non-deterministic ordering
expression (and an optional output outAlias), the list of grouping columns it
contributes is empty.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The behavior
-- being modeled — the grouping-column contribution of a non-deterministic
-- ordering expression — is a leaf computation that always returns an empty
-- collection regardless of its inputs, so there is no `opaque`/`axiom` callee
-- whose contract the proof consumes.
-- axioms-end

-- pure-start
/-- A column that participates in the grouping of an aggregated result set,
identified by the SQL fragment it compiles to. -/
abbrev GroupByCol := String

/-- A scalar expression that can appear as an ordering term, identified by the
SQL function it emits (e.g. the non-deterministic random-value generator). Such a
generator has arity zero — no operand expressions and so no underlying stored
column. -/
structure OrderingExpr where
  /-- the SQL function this ordering expression emits. -/
  function : String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The grouping-column contribution of a non-deterministic ordering expression
is empty: such a term adds no columns to the grouping of an aggregated result set,
for any expression and any output `outAlias`. The result is pinned exactly to the
empty collection (directive 5: the sole output component is fully determined),
grounded structurally rather than by any oracle. -/
def problem_spec_randomGroupingColumns
    (self : OrderingExpr) (outAlias : Option String)
    (result : List GroupByCol) : Prop :=
  result = []
-- post-conditions-end

-- impl-start
def randomGroupingColumns
    (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=
  Id.run do
    return []
-- impl-end
-- proof-start
theorem correct_randomGroupingColumns :
    ∀ (self : OrderingExpr) (outAlias : Option String),
      problem_spec_randomGroupingColumns self outAlias
        (randomGroupingColumns self outAlias) := by
  intro self outAlias
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC:** problem_spec_randomGroupingColumns self outAlias result := (result = []). The postcondition pins the SOLE output component EXACTLY to the empty list for ALL inputs (self:OrderingExpr, outAlias:Option String) — no oracle, no free/underconstrained component (directive 5 fully-determined; directive 8 no ungrounded oracle). Consequence: any impl that returns a non-[] value on ANY input makes theorem correct_randomGroupingColumns literally FALSE, so NO proof body can close it. Spec regions per same_spec = axioms/pure/pre/post; all attacks edit only impl (proof free); same_spec=True for all 6 attacks + positive control (verified programmatically).

PROTOCOL / ATTACK RESULTS (project root; cmd: `bash scripts/lean_verify.sh <f>`; verifications run concurrently ≤4):
- atk_1 (partial-domain: [] iff function=="RANDOM", else [self.function]) -> exit 1. Proof rfl fails; theorem false for function!="RANDOM". REJECTED by verify (correct).
- atk_2 (alias-boundary: [] iff outAlias=none, else [self.function]) -> exit 1. Theorem false when outAlias=some _. REJECTED (correct).
- atk_3 (PREPATCH bug: return [self.function] always) -> exit 1. rfl fails (LHS [self.function] vs RHS []). PREPATCH REPRODUCED: gold proof does not close on the buggy impl. REJECTED (correct).
- atk_5 (ungrounded-oracle echo: return [""]) -> exit 1. [""] != []. REJECTED (correct).
- atk_6 (control-flow branch on function.length: [] iff length=0 else [self.function]) -> exit 1. Theorem false for nonempty function. REJECTED (correct).
- atk_4 (control-flow-effect: let mut acc:=[self.function]; acc:=[]; return acc) -> exit 0 VERIFIES. #print axioms => 'does not depend on any axioms' (CLEAN). BUT: the mutation overwrites the singleton, so acc reduces to [] on EVERY input — behaviorally IDENTICAL to gold. Its faithful refined patch is therefore the gold override `def get_group_by_cols(self, alias=None): return []`.

MANDATED RESOLVE RUN for the ONLY wrong-shaped verifying impl (atk_4): materialized atk_4.patch and ran run_resolve('django__django-13569', patch, timeout=1200, retries=1) => RESOLVED: True, completed: True, note='resolved'. It RESOLVES, so it does NOT break the spec (verify⇒correct holds for it because it is gold-equivalent).

Positive control atk_7_pos (gold return []) -> exit 0, #print axioms clean (no axioms). 

**WHY NO WRONG-IMPL CAN SURVIVE:** the spec is a total pointwise equality to a constant; the theorem quantifies over all inputs, so verification is possible iff the impl is extensionally == gold (constant []). No same-spec impl can both (a) diverge from gold on any input and (b) verify. The single verifying non-gold-syntax impl (atk_4) is provably gold-equivalent and its patch resolves. verify⇒correct is NOT falsifiable here.

**REFINEMENT.MD AUDIT:** 3 legs — #1 self:OrderingExpr param = R (type refinement, Random receiver modeled by SQL function name, arity-0); #2 outAlias:Option String = R (optional alias, ignored by body, matches real code); #3 return [] = I (the fix, byte-for-byte the post-patch override). NO kind-3 legs; NO A-consumed/A-reference legs (the A-legs the reviewer must scrutinize are absent by design). axioms region = justified empty comment: the changed op Random.get_group_by_cols is a LEAF returning constant []; SPEC_GUIDE §3 says a deeply-modeled changed op is not axiomatized, so no opaque/axiom callee contract is consumed — G-AX skips (axiom_check.py stub), consistent with #print axioms showing zero axiom dependence. mapping.md callee provenance (BaseExpression.get_group_by_cols is the REPLACED default, not a consumed unchanged callee) is consistent with the real repo code and the patch. Model↔patch correspondence holds: Lean constant [] ↔ Python return [].

**VERDICT:** SOUND. 6 same-spec wrong-impl attacks encoded (partial-domain, alias-boundary, prepatch bug, oracle-echo, length-branch, control-flow-effect) + positive control; all 5 genuinely-wrong impls fail to verify; the 1 wrong-shaped impl that verifies is gold-equivalent and its faithful patch RESOLVES (executed). Prepatch reproduced. No A-leg defects. No verify⇏correct counterexample exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `atk_7_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Grouping columns contributed by a non-deterministic ordering expression.

When an aggregated result set is also ordered, each ordering term is asked which
underlying stored columns it adds to the grouping of the result. A plain column
reference contributes that column; an aggregate contributes the columns of its
operands. But an ordering term that is a non-deterministic value generator — a
random-value function with arity zero and therefore no underlying stored column —
has nothing to group on. Asking such a term for its grouping columns must yield
the empty collection, so that ordering a result randomly never alters how the
aggregated rows are grouped.

This file models that single query: given such a non-deterministic ordering
expression (and an optional output outAlias), the list of grouping columns it
contributes is empty.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The behavior
-- being modeled — the grouping-column contribution of a non-deterministic
-- ordering expression — is a leaf computation that always returns an empty
-- collection regardless of its inputs, so there is no `opaque`/`axiom` callee
-- whose contract the proof consumes.
-- axioms-end

-- pure-start
/-- A column that participates in the grouping of an aggregated result set,
identified by the SQL fragment it compiles to. -/
abbrev GroupByCol := String

/-- A scalar expression that can appear as an ordering term, identified by the
SQL function it emits (e.g. the non-deterministic random-value generator). Such a
generator has arity zero — no operand expressions and so no underlying stored
column. -/
structure OrderingExpr where
  /-- the SQL function this ordering expression emits. -/
  function : String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The grouping-column contribution of a non-deterministic ordering expression
is empty: such a term adds no columns to the grouping of an aggregated result set,
for any expression and any output `outAlias`. The result is pinned exactly to the
empty collection (directive 5: the sole output component is fully determined),
grounded structurally rather than by any oracle. -/
def problem_spec_randomGroupingColumns
    (self : OrderingExpr) (outAlias : Option String)
    (result : List GroupByCol) : Prop :=
  result = []
-- post-conditions-end

-- impl-start
def randomGroupingColumns
    (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=
  Id.run do
    return []
-- impl-end
-- proof-start
theorem correct_randomGroupingColumns :
    ∀ (self : OrderingExpr) (outAlias : Option String),
      problem_spec_randomGroupingColumns self outAlias
        (randomGroupingColumns self outAlias) := by
  intro self outAlias
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC:** problem_spec_randomGroupingColumns self outAlias result := (result = []). The postcondition pins the SOLE output component EXACTLY to the empty list for ALL inputs (self:OrderingExpr, outAlias:Option String) — no oracle, no free/underconstrained component (directive 5 fully-determined; directive 8 no ungrounded oracle). Consequence: any impl that returns a non-[] value on ANY input makes theorem correct_randomGroupingColumns literally FALSE, so NO proof body can close it. Spec regions per same_spec = axioms/pure/pre/post; all attacks edit only impl (proof free); same_spec=True for all 6 attacks + positive control (verified programmatically).

PROTOCOL / ATTACK RESULTS (project root; cmd: `bash scripts/lean_verify.sh <f>`; verifications run concurrently ≤4):
- atk_1 (partial-domain: [] iff function=="RANDOM", else [self.function]) -> exit 1. Proof rfl fails; theorem false for function!="RANDOM". REJECTED by verify (correct).
- atk_2 (alias-boundary: [] iff outAlias=none, else [self.function]) -> exit 1. Theorem false when outAlias=some _. REJECTED (correct).
- atk_3 (PREPATCH bug: return [self.function] always) -> exit 1. rfl fails (LHS [self.function] vs RHS []). PREPATCH REPRODUCED: gold proof does not close on the buggy impl. REJECTED (correct).
- atk_5 (ungrounded-oracle echo: return [""]) -> exit 1. [""] != []. REJECTED (correct).
- atk_6 (control-flow branch on function.length: [] iff length=0 else [self.function]) -> exit 1. Theorem false for nonempty function. REJECTED (correct).
- atk_4 (control-flow-effect: let mut acc:=[self.function]; acc:=[]; return acc) -> exit 0 VERIFIES. #print axioms => 'does not depend on any axioms' (CLEAN). BUT: the mutation overwrites the singleton, so acc reduces to [] on EVERY input — behaviorally IDENTICAL to gold. Its faithful refined patch is therefore the gold override `def get_group_by_cols(self, alias=None): return []`.

MANDATED RESOLVE RUN for the ONLY wrong-shaped verifying impl (atk_4): materialized atk_4.patch and ran run_resolve('django__django-13569', patch, timeout=1200, retries=1) => RESOLVED: True, completed: True, note='resolved'. It RESOLVES, so it does NOT break the spec (verify⇒correct holds for it because it is gold-equivalent).

Positive control atk_7_pos (gold return []) -> exit 0, #print axioms clean (no axioms). 

**WHY NO WRONG-IMPL CAN SURVIVE:** the spec is a total pointwise equality to a constant; the theorem quantifies over all inputs, so verification is possible iff the impl is extensionally == gold (constant []). No same-spec impl can both (a) diverge from gold on any input and (b) verify. The single verifying non-gold-syntax impl (atk_4) is provably gold-equivalent and its patch resolves. verify⇒correct is NOT falsifiable here.

**REFINEMENT.MD AUDIT:** 3 legs — #1 self:OrderingExpr param = R (type refinement, Random receiver modeled by SQL function name, arity-0); #2 outAlias:Option String = R (optional alias, ignored by body, matches real code); #3 return [] = I (the fix, byte-for-byte the post-patch override). NO kind-3 legs; NO A-consumed/A-reference legs (the A-legs the reviewer must scrutinize are absent by design). axioms region = justified empty comment: the changed op Random.get_group_by_cols is a LEAF returning constant []; SPEC_GUIDE §3 says a deeply-modeled changed op is not axiomatized, so no opaque/axiom callee contract is consumed — G-AX skips (axiom_check.py stub), consistent with #print axioms showing zero axiom dependence. mapping.md callee provenance (BaseExpression.get_group_by_cols is the REPLACED default, not a consumed unchanged callee) is consistent with the real repo code and the patch. Model↔patch correspondence holds: Lean constant [] ↔ Python return [].

**VERDICT:** SOUND. 6 same-spec wrong-impl attacks encoded (partial-domain, alias-boundary, prepatch bug, oracle-echo, length-branch, control-flow-effect) + positive control; all 5 genuinely-wrong impls fail to verify; the 1 wrong-shaped impl that verifies is gold-equivalent and its faithful patch RESOLVES (executed). Prepatch reproduced. No A-leg defects. No verify⇏correct counterexample exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for django__django-13569 lean bundle.

**Modeled function:** post-patch Random.get_group_by_cols(self, alias=None) in django/db/models/functions/math.py. Verified in the worktree that the patch adds exactly:
    def get_group_by_cols(self, alias=None):
        return []
This is a constant function returning [] for every receiver and every alias, branching on nothing.

**Spec:** problem_spec_randomGroupingColumns self outAlias result := (result = []) — pins the sole output component to full equality with the empty list.

**Faithfulness verdict:** FAITHFUL. There is NO input (self, outAlias) on which the spec disagrees with the real callee. The real callee always returns []; the spec requires precisely []. 
- Not too strong: the spec forbids nothing the real function ever produces (it only ever produces []).
- Not too weak: fully pinned to [], no unconstrained component, no ungrounded oracle.
- The Lean domain abstraction (OrderingExpr = {function}, Option String alias) is sound: the real body reads neither input, so any modeling of the input domain agrees. The prepatch buggy behavior ([self]) is correctly excluded by the spec (matches G-DIFF pass: prepatch fails to verify).

Evidence:
- same_spec(Solution, Solution_prepatch, lean) = True (spec region byte-identical; drift enforceable).
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry; only unused-variable warnings).
- #print axioms correct_randomGroupingColumns -> 'does not depend on any axioms' (real proof, no sorryAx).

No spec-drift / faithfulness defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen passes (rep.passed=True, no hard failures) and same_spec byte-identity holds. Spec-view identifiers are randomGroupingColumns / GroupByCol / OrderingExpr — none embeds the patched symbol get_group_by_cols; changed symbols {as_oracle, get_group_by_cols} do not appear. No patched file path (django/db/models/functions/math.py), no diff markers, no reproduced gold-diff line, no bug/fix narration in comments. Semantic check: the spec view restates only behavior already public in problem_statement — the issue explicitly says order_by('?') injects RANDOM() into GROUP BY, that 'the random function call has nothing to do with the aggregation', and even proposes excluding Random from the group-by contribution. The spec view abstractly encodes 'a non-deterministic random ordering term contributes an empty grouping-column list (result = [])', which is fully derivable from the public issue. It does NOT reveal the gold's specific locus (an override method on the Random class in math.py) — indeed problem_statement proposes a different fix site (SQLCompiler.get_group_by). Gold-edit location/symbol details live only in mapping.md/refinement.md/meta.json, which are not part of the spec view. Nothing exceeds the public problem_statement (hints_text not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

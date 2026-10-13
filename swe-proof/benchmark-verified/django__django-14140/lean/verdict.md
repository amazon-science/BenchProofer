# P2 adversarial audit — django__django-14140

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
@@ -83,10 +83,15 @@
 def implementation_deconstruct
     (path : String) (children : List Child)
     (connector : Connector) (negated : Bool) : Deconstructed := Id.run do
-  let args := children
+  let mut args : List Child := []
   let mut kw : Kwargs := { pair := none, connector := none, negated := false }
-  if connector ≠ Connector.cAnd then
-    kw := { kw with connector := some connector }
+  if children.length = 1 ∧ ¬ (children.headI.isNode) then
+    let child := children.headI
+    kw := { kw with pair := some (child.asPair.getD ("", "")) }
+  else
+    args := children
+    if connector ≠ Connector.cAnd then
+      kw := { kw with connector := some connector }
   if negated then
     kw := { kw with negated := true }
   return { path := path, args := args, kwargs := kw }
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
     (connector : Connector) (negated : Bool) : Deconstructed := Id.run do
   let args := children
   let mut kw : Kwargs := { pair := none, connector := none, negated := false }
-  if connector ≠ Connector.cAnd then
+  if connector = Connector.cAnd then
     kw := { kw with connector := some connector }
   if negated then
     kw := { kw with negated := true }
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,8 +87,7 @@
   let mut kw : Kwargs := { pair := none, connector := none, negated := false }
   if connector ≠ Connector.cAnd then
     kw := { kw with connector := some connector }
-  if negated then
-    kw := { kw with negated := true }
+  kw := { kw with negated := true }
   return { path := path, args := args, kwargs := kw }
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
 def implementation_deconstruct
     (path : String) (children : List Child)
     (connector : Connector) (negated : Bool) : Deconstructed := Id.run do
-  let args := children
+  let args := children.reverse
   let mut kw : Kwargs := { pair := none, connector := none, negated := false }
   if connector ≠ Connector.cAnd then
     kw := { kw with connector := some connector }
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,8 +87,6 @@
   let mut kw : Kwargs := { pair := none, connector := none, negated := false }
   if connector ≠ Connector.cAnd then
     kw := { kw with connector := some connector }
-  if negated then
-    kw := { kw with negated := true }
   return { path := path, args := args, kwargs := kw }
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,9 +84,7 @@
     (path : String) (children : List Child)
     (connector : Connector) (negated : Bool) : Deconstructed := Id.run do
   let args := children
-  let mut kw : Kwargs := { pair := none, connector := none, negated := false }
-  if connector ≠ Connector.cAnd then
-    kw := { kw with connector := some connector }
+  let mut kw : Kwargs := { pair := some ("", ""), connector := some connector, negated := false }
   if negated then
     kw := { kw with negated := true }
   return { path := path, args := args, kwargs := kw }
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior: `deconstruct` derives
-- its `(args, kwargs)` result purely from the node's stored components
-- (the child sequence, the combinator, and the negation flag) using only
-- language primitives (tuple/dict construction), which are modeled directly.
-- Hence there is no `opaque` callee and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- The logical combinator of a filter node. `cAnd` is the default. -/
inductive Connector where
  | cAnd
  | cOr
deriving DecidableEq, Inhabited, Repr

/-- A single child stored in a filter node. A node's children are either
key/value lookup pairs (index-addressable as `child[0]`/`child[1]`), standalone
conditional expressions (which carry a single value and are NOT index-addressable),
or nested filter nodes. `label` is an opaque tag for the latter two — the
decomposition never inspects their internal content. -/
inductive Child where
  | cond (key val : String)
  | expr (label : String)
  | nested (label : String)
deriving DecidableEq, Inhabited, Repr

/-- Whether a child is itself a nested filter node (`isinstance(child, Q)`). -/
def Child.isNode : Child → Bool
  | .nested _ => true
  | _ => false

/-- Index-addressing a child as a length-2 pair (`child[0]`, `child[1]`).
Defined only for key/value lookup children; `none` for the others (a standalone
expression child has no subscript, the source of the read failure when a single
such child is subscripted unconditionally). -/
def Child.asPair : Child → Option (String × String)
  | .cond k v => some (k, v)
  | _ => none

/-- The keyword-argument mapping returned by the decomposition. It can carry an
inlined key/value entry (the `pair`), the non-default combinator (`connector`),
and the negation flag (`negated`). -/
structure Kwargs where
  pair : Option (String × String)
  connector : Option Connector
  negated : Bool
deriving DecidableEq, Repr

/-- The decomposition triple of a filter node: an import path, the positional
arguments, and the keyword arguments. -/
structure Deconstructed where
  path : String
  args : List Child
  kwargs : Kwargs
deriving Repr
-- pure-end

-- post-conditions-start
/-- The decomposition of a filter node. The `path` is carried through unchanged.
Every child of the node is placed positionally into `args`, in order. The keyword
arguments carry no inlined key/value entry; they record the combinator only when
it is non-default, and the negation flag only when the node is negated.

This pins the result component-wise to the node's stored inputs (frame
discipline): `args` is exactly the child sequence, `kwargs.connector` is present
iff the combinator differs from the default, `kwargs.negated` mirrors the flag,
and `kwargs.pair` is always absent. -/
def problem_spec_deconstruct
    (path : String) (children : List Child)
    (connector : Connector) (negated : Bool)
    (result : Deconstructed) : Prop :=
  result.path = path ∧
  result.args = children ∧
  result.kwargs.pair = none ∧
  result.kwargs.connector = (if connector = Connector.cAnd then none else some connector) ∧
  result.kwargs.negated = negated
-- post-conditions-end

-- impl-start
def implementation_deconstruct
    (path : String) (children : List Child)
    (connector : Connector) (negated : Bool) : Deconstructed := Id.run do
  let args := children
  let mut kw : Kwargs := { pair := none, connector := none, negated := false }
  if connector ≠ Connector.cAnd then
    kw := { kw with connector := some connector }
  if negated then
    kw := { kw with negated := true }
  return { path := path, args := args, kwargs := kw }
-- impl-end

-- proof-start
theorem correct_deconstruct :
    ∀ (path : String) (children : List Child)
      (connector : Connector) (negated : Bool),
      problem_spec_deconstruct path children connector negated
        (implementation_deconstruct path children connector negated) := by
  intro path children connector negated
  unfold problem_spec_deconstruct implementation_deconstruct
  cases negated <;> by_cases hc : connector = Connector.cAnd <;>
    simp only [hc, ne_eq, not_true, not_false_iff, if_true, if_false, Id.run] <;>
    exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_deconstruct fully pins ALL FIVE output components (result.path=path, result.args=children, kwargs.pair=none, kwargs.connector = if connector=cAnd then none else some connector, kwargs.negated=negated) as a total deterministic function of the inputs. The correct output is therefore unique, so any spec-satisfying impl must be extensionally equal to the gold on the whole modeled domain.

AXIOM/A-LEG AUDIT: The axioms region is EMPTY (bytes identical across all files; same_spec=True). refinement.md legs 1-6 are all R/I; there is NO opaque callee, NO consumed _prop axiom, and NO A-reference deep model (mapping.md 'Callee provenance': deconstruct invokes no unchanged repo callee post-patch — only language primitives tuple(...)/dict, modeled directly). No kind-3 legs. So there are no A-legs to break and no deep-model correspondence to falsify; the R/I legs are covered by G-CONF. #print axioms on the positive control = [propext, Quot.sound] (standard, clean, no sorry, no custom axiom).

Commands:
- same_spec via swebench_unified.markers.same_spec (lean backend) => True for pos + atk_1..atk_6.
- Verify: bash scripts/lean_verify.sh <file>, run concurrently in batches of <=4.

### Results
- pos.lean (gold impl): EXIT=0 (verifies). pos_ax.lean with #print axioms correct_deconstruct => depends on axioms: [propext, Quot.sound]. Clean.
- atk_1 (prepatch bug: single-child partial-domain special case -> args=[], pair=some): EXIT=1, error line 110 'Application type mismatch' (rfl witness on args/pair fails). PREPATCH REPRODUCED (byte-equivalent skeleton to Solution_prepatch.lean; the gold proof tactic replaces the prepatch's sorry and genuinely fails to close).
- atk_2 (boundary: inverted connector condition, records when =cAnd): EXIT=1, error line 105 type mismatch on kwargs.connector rfl.
- atk_3 (control-flow-effect: unconditionally sets negated:=true): EXIT=1, error line 104 type mismatch on kwargs.negated rfl.
- atk_4 (ungrounded-oracle echo: children.reverse into args): EXIT=1, error line 105 type mismatch on args rfl.
- atk_5 (boundary: drops negation handling): EXIT=1, error line 103 type mismatch on kwargs.negated rfl.
- atk_6 (partial-domain: always record connector + spurious pair=some("","")): EXIT=1, error line 103 type mismatch on pair/connector rfl.

All 6 wrong impls are same_spec=True and fail with GENUINE proof-closure errors (missing rfl witnesses because the impl output diverges from the pinned spec) — NOT parse/syntax errors. Since NO wrong impl produced a closing clean-axiom proof, the verify=>correct implication is not falsifiable here and no faithful patch needed to be materialized/resolved (patches={}). The fully-pinned postcondition leaves no slack for a spec-satisfying-but-behaviorally-wrong impl. Verdict SOUND.

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

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior: `deconstruct` derives
-- its `(args, kwargs)` result purely from the node's stored components
-- (the child sequence, the combinator, and the negation flag) using only
-- language primitives (tuple/dict construction), which are modeled directly.
-- Hence there is no `opaque` callee and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- The logical combinator of a filter node. `cAnd` is the default. -/
inductive Connector where
  | cAnd
  | cOr
deriving DecidableEq, Inhabited, Repr

/-- A single child stored in a filter node. A node's children are either
key/value lookup pairs (index-addressable as `child[0]`/`child[1]`), standalone
conditional expressions (which carry a single value and are NOT index-addressable),
or nested filter nodes. `label` is an opaque tag for the latter two — the
decomposition never inspects their internal content. -/
inductive Child where
  | cond (key val : String)
  | expr (label : String)
  | nested (label : String)
deriving DecidableEq, Inhabited, Repr

/-- Whether a child is itself a nested filter node (`isinstance(child, Q)`). -/
def Child.isNode : Child → Bool
  | .nested _ => true
  | _ => false

/-- Index-addressing a child as a length-2 pair (`child[0]`, `child[1]`).
Defined only for key/value lookup children; `none` for the others (a standalone
expression child has no subscript, the source of the read failure when a single
such child is subscripted unconditionally). -/
def Child.asPair : Child → Option (String × String)
  | .cond k v => some (k, v)
  | _ => none

/-- The keyword-argument mapping returned by the decomposition. It can carry an
inlined key/value entry (the `pair`), the non-default combinator (`connector`),
and the negation flag (`negated`). -/
structure Kwargs where
  pair : Option (String × String)
  connector : Option Connector
  negated : Bool
deriving DecidableEq, Repr

/-- The decomposition triple of a filter node: an import path, the positional
arguments, and the keyword arguments. -/
structure Deconstructed where
  path : String
  args : List Child
  kwargs : Kwargs
deriving Repr
-- pure-end

-- post-conditions-start
/-- The decomposition of a filter node. The `path` is carried through unchanged.
Every child of the node is placed positionally into `args`, in order. The keyword
arguments carry no inlined key/value entry; they record the combinator only when
it is non-default, and the negation flag only when the node is negated.

This pins the result component-wise to the node's stored inputs (frame
discipline): `args` is exactly the child sequence, `kwargs.connector` is present
iff the combinator differs from the default, `kwargs.negated` mirrors the flag,
and `kwargs.pair` is always absent. -/
def problem_spec_deconstruct
    (path : String) (children : List Child)
    (connector : Connector) (negated : Bool)
    (result : Deconstructed) : Prop :=
  result.path = path ∧
  result.args = children ∧
  result.kwargs.pair = none ∧
  result.kwargs.connector = (if connector = Connector.cAnd then none else some connector) ∧
  result.kwargs.negated = negated
-- post-conditions-end

-- impl-start
def implementation_deconstruct
    (path : String) (children : List Child)
    (connector : Connector) (negated : Bool) : Deconstructed := Id.run do
  let args := children
  let mut kw : Kwargs := { pair := none, connector := none, negated := false }
  if connector ≠ Connector.cAnd then
    kw := { kw with connector := some connector }
  if negated then
    kw := { kw with negated := true }
  return { path := path, args := args, kwargs := kw }
-- impl-end

-- proof-start
theorem correct_deconstruct :
    ∀ (path : String) (children : List Child)
      (connector : Connector) (negated : Bool),
      problem_spec_deconstruct path children connector negated
        (implementation_deconstruct path children connector negated) := by
  intro path children connector negated
  unfold problem_spec_deconstruct implementation_deconstruct
  cases negated <;> by_cases hc : connector = Connector.cAnd <;>
    simp only [hc, ne_eq, not_true, not_false_iff, if_true, if_false, Id.run] <;>
    exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_deconstruct fully pins ALL FIVE output components (result.path=path, result.args=children, kwargs.pair=none, kwargs.connector = if connector=cAnd then none else some connector, kwargs.negated=negated) as a total deterministic function of the inputs. The correct output is therefore unique, so any spec-satisfying impl must be extensionally equal to the gold on the whole modeled domain.

AXIOM/A-LEG AUDIT: The axioms region is EMPTY (bytes identical across all files; same_spec=True). refinement.md legs 1-6 are all R/I; there is NO opaque callee, NO consumed _prop axiom, and NO A-reference deep model (mapping.md 'Callee provenance': deconstruct invokes no unchanged repo callee post-patch — only language primitives tuple(...)/dict, modeled directly). No kind-3 legs. So there are no A-legs to break and no deep-model correspondence to falsify; the R/I legs are covered by G-CONF. #print axioms on the positive control = [propext, Quot.sound] (standard, clean, no sorry, no custom axiom).

Commands:
- same_spec via swebench_unified.markers.same_spec (lean backend) => True for pos + atk_1..atk_6.
- Verify: bash scripts/lean_verify.sh <file>, run concurrently in batches of <=4.

### Results
- pos.lean (gold impl): EXIT=0 (verifies). pos_ax.lean with #print axioms correct_deconstruct => depends on axioms: [propext, Quot.sound]. Clean.
- atk_1 (prepatch bug: single-child partial-domain special case -> args=[], pair=some): EXIT=1, error line 110 'Application type mismatch' (rfl witness on args/pair fails). PREPATCH REPRODUCED (byte-equivalent skeleton to Solution_prepatch.lean; the gold proof tactic replaces the prepatch's sorry and genuinely fails to close).
- atk_2 (boundary: inverted connector condition, records when =cAnd): EXIT=1, error line 105 type mismatch on kwargs.connector rfl.
- atk_3 (control-flow-effect: unconditionally sets negated:=true): EXIT=1, error line 104 type mismatch on kwargs.negated rfl.
- atk_4 (ungrounded-oracle echo: children.reverse into args): EXIT=1, error line 105 type mismatch on args rfl.
- atk_5 (boundary: drops negation handling): EXIT=1, error line 103 type mismatch on kwargs.negated rfl.
- atk_6 (partial-domain: always record connector + spurious pair=some("","")): EXIT=1, error line 103 type mismatch on pair/connector rfl.

All 6 wrong impls are same_spec=True and fail with GENUINE proof-closure errors (missing rfl witnesses because the impl output diverges from the pinned spec) — NOT parse/syntax errors. Since NO wrong impl produced a closing clean-axiom proof, the verify=>correct implication is not falsifiable here and no faithful patch needed to be materialized/resolved (patches={}). The fully-pinned postcondition leaves no slack for a spec-satisfying-but-behaviorally-wrong impl. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14140, modeled function Q.deconstruct (post-patch (args, kwargs) derivation from a node's stored components).

VERDICT: FAITHFUL — no input in the modeled domain makes problem_spec_deconstruct disagree with the real post-patch callee.

Evidence:
1. Post-patch gold body (django/db/models/query_utils.py, confirmed, which is at/after the patch): args = tuple(self.children); kwargs = {}; if self.connector != self.default: kwargs['_connector']=self.connector; if self.negated: kwargs['_negated']=True; return path, args, kwargs. patch.diff removes exactly the pre-patch single-non-Q-child special case that inlined {child[0]:child[1]}.
2. Spec clause-by-clause mirrors this: result.path=path (input-independent unchanged prefix, frame-pinned), result.args=children (order-preserving identity, matches tuple(self.children)), result.kwargs.pair=none (never inlined post-patch), result.kwargs.connector = (cAnd -> none else some connector) matching '_connector' present iff connector != default(AND), result.kwargs.negated = negated matching '_negated' iff self.negated. Every post-patch observable is pinned; nothing over-constrained.
3. Connector two-value abstraction (cAnd/cOr) is sound: Node.__init__ sets connector = connector or self.default and _combine/__and__/__or__ only ever assign AND/OR; Q.default = AND. So the modeled value domain equals the real one — no reachable connector value is excluded, and even a restriction could only weaken (not strengthen) the spec.
4. Lean: scripts/lean_verify.sh exit 0 (compiles, no sorry). #print axioms correct_deconstruct -> [propext, Quot.sound] only (no sorryAx; genuine proof).
5. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True (spec region byte-identical).
6. G-CONF differential fuzz (conformance_check.py, seed=14140): 120010 inputs including all F2P boundary cases (single cond child, single Exists/expr child, negated, empty, multi-child, OR) -> 0 disagreements between R/I shadow and an independent reconstruction of the post-patch body.

G-AX correctly skip: modeled behavior uses only language primitives (tuple/dict construction), no unchanged repo callee axiomatized, axioms region empty. No spec-too-strong defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, zero hard_failures): no diff markers, no reproduced gold-patch line (>=8 chars normalized), no patched file/module path, no spec-view identifier embedding a patched repo symbol, no narration keywords in comments/docstrings. Spec region byte-identical to Solution_prepatch (same_spec=True). Semantic review vs the SOLVER-VISIBLE problem_statement only (hints_text excluded): the problem_statement already states the fix verbatim ('Patch ... removes the special case, meaning single-child Q objects deconstruct into args instead of kwargs'), displays the exact TypeError: 'Exists' object is not subscriptable crash with the kwargs={child[0]:child[1]} mechanism, and contrasts the 1-child vs 2-child deconstruct outputs. The spec view's postcondition (args = children, kwargs.pair = none always, connector iff non-default, negated mirrors flag) and the Child.asPair/Child.expr 'not index-addressable / read failure' docstrings are exactly this publicly-stated behavior. Nothing in the spec view exceeds the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

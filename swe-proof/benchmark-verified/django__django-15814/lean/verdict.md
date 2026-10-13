# P2 adversarial audit — django__django-15814

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closed its proof, so there is no verifying-but-non-resolving impl. The postcondition (result.length = steps.length AND for all i m, steps[i]? = some m -> result[i]? = some (baseOf m)) fully pins result = steps.map baseOf, leaving zero functional latitude; any closing implementation is extensionally equal to the gold and therefore resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
     (steps : List RelModel) : List Nat := Id.run do
   let mut keys : List Nat := []
   for m in steps do
-    let curModel := baseOf m
+    let curModel := m.ident
     keys := keys ++ [curModel]
   return keys
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
     (steps : List RelModel) : List Nat := Id.run do
   let mut keys : List Nat := []
   for m in steps do
-    let curModel := baseOf m
+    let curModel := if m.baseIdent == 0 then m.ident else m.baseIdent
     keys := keys ++ [curModel]
   return keys
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,7 @@
   for m in steps do
     let curModel := baseOf m
     keys := keys ++ [curModel]
-  return keys
+  return keys.dropLast
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
   let mut keys : List Nat := []
   for m in steps do
     let curModel := baseOf m
-    keys := keys ++ [curModel]
+    keys := [curModel] ++ keys
   return keys
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,9 +72,8 @@
 def implementation_relationModelKeys
     (steps : List RelModel) : List Nat := Id.run do
   let mut keys : List Nat := []
-  for m in steps do
-    let curModel := baseOf m
-    keys := keys ++ [curModel]
+  for _m in steps do
+    keys := keys ++ [0]
   return keys
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
     (steps : List RelModel) : List Nat := Id.run do
   let mut keys : List Nat := []
   for m in steps do
-    let curModel := baseOf m
+    let curModel := baseOf m + 1
     keys := keys ++ [curModel]
   return keys
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
     (steps : List RelModel) : List Nat := Id.run do
   let mut keys : List Nat := []
   for m in steps do
-    let curModel := baseOf m
+    let curModel := if m.ident == m.baseIdent then baseOf m else m.ident
     keys := keys ++ [curModel]
   return keys
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the model key under which each traversed relation's identifier columns
are recorded when planning which columns a query must load.

When a query restricts the fields it loads to a subset reached through related
models, it walks the chain of relations one step at a time. At each step it
reaches a target model and must record, keyed by that model, that the model's
identifier column has to be loaded (otherwise the rows for that model cannot be
assembled).

A model can be either a base model — one that owns its own storage and identifier
column — or an alias model that shares the storage and identifier column of an
underlying base model while remaining a distinct model object. Two alias models of
the same base, and an alias and its base, all share one storage and one identifier
column.

The desired behavior: at every relation step the identifier requirement is keyed
under the *base* model that owns the shared storage — never under an alias.
Keying under an alias would record the requirement against a model object that
does not, by itself, own the identifier column, leaving the load plan unable to
locate that column for the shared storage. For a model that is already a base
model, its base is itself, so keying is unchanged. The recorded keys are produced
one per step, in traversal order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The choice of
-- which model to key each step under is modeled DEEPLY over each step's resolved
-- model (its own identity together with the identity of the base model whose
-- storage it shares), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- One resolved relation-step target model, restricted to the observed aspects:
* `ident` — the identity of the model object reached by this step (which may be an
  alias model sharing another model's storage);
* `baseIdent` — the identity of the base model that owns the shared storage and
  identifier column. For a base model (one that owns its own storage) `baseIdent`
  equals `ident`; for an alias model it is the underlying base's identity. -/
structure RelModel where
  ident : Nat
  baseIdent : Nat
deriving DecidableEq, Repr

/-- The base model that owns the storage shared by this step's model: the model
under which the step's identifier requirement must be keyed. Idempotent on base
models (where `baseIdent = ident`). -/
def baseOf (m : RelModel) : Nat :=
  m.baseIdent
-- pure-end

-- post-conditions-start
/-- The produced key list is fully pinned to the traversed steps:

  * it has exactly one key per relation step, in traversal order; and
  * each key is the identity of the base model that owns the step's shared storage
    (`baseIdent`) — never the (possibly alias) resolved model itself.

Every produced key is determined for every step, so no output component is left
free. -/
def problem_spec_relationModelKeys
    (steps : List RelModel) (result : List Nat) : Prop :=
  result.length = steps.length ∧
  ∀ (i : Nat) (m : RelModel), steps[i]? = some m →
    result[i]? = some (baseOf m)
-- post-conditions-end

-- impl-start
def implementation_relationModelKeys
    (steps : List RelModel) : List Nat := Id.run do
  let mut keys : List Nat := []
  for m in steps do
    let curModel := baseOf m
    keys := keys ++ [curModel]
  return keys
-- impl-end

-- proof-start
theorem correct_relationModelKeys :
    ∀ (steps : List RelModel),
      problem_spec_relationModelKeys steps
        (implementation_relationModelKeys steps) := by
  intro steps
  -- Helper: the cleaned `forIn` loop, generalized over the accumulator, equals
  -- the prefix accumulator appended with `steps.map baseOf` (Route B).
  have hkey : ∀ (init : List Nat),
      Id.run (forIn steps init
        (fun m keys => (.yield (keys ++ [baseOf m]) : ForInStep (List Nat))))
        = init ++ steps.map baseOf := by
    intro init
    induction steps generalizing init with
    | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih (init ++ [baseOf a])]
      simp [List.append_assoc]
  -- Bridge the desugared loop body to the cleaned form and discharge the impl.
  have himpl : implementation_relationModelKeys steps = steps.map baseOf := by
    show Id.run (forIn steps []
        (fun m keys => (.yield (keys ++ [baseOf m]) : ForInStep (List Nat)))) = _
    rw [hkey []]
    simp
  refine ⟨?_, ?_⟩
  · rw [himpl]; simp
  · intro i m hi
    rw [himpl, List.getElem?_map, hi]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Commands: 'bash scripts/lean_verify.sh <file>' (run concurrently in background, <=4 at a time) and '#print axioms correct_relationModelKeys' appended to pc for the axiom check.

### RESULTS (exit code / axioms):
- pc.lean (positive control, gold impl baseOf m): exit 0 (verifies, no sorry). #print axioms correct_relationModelKeys => 'depends on axioms: [propext, Quot.sound]' -- CLEAN, no sorryAx (pc_ax.lean exit 0).
- atk_1.lean (prepatch bug, curModel := m.ident): exit 1 -- PREPATCH BUG REPRODUCED. Error: implementation_relationModelKeys steps != List.map baseOf steps.
- atk_2.lean (partial-domain: if baseIdent==0 then ident else baseIdent): exit 1.
- atk_3.lean (boundary: keys.dropLast, length wrong): exit 1.
- atk_4.lean (control-flow-effect: prepend => reversed traversal order): exit 1.
- atk_5.lean (ungrounded-oracle echo: constant key 0 per step): exit 1.
- atk_6.lean (off-by-one value: baseOf m + 1): exit 1.
- atk_7.lean (only-correct-on-base branch: if ident==baseIdent then baseOf m else m.ident, i.e. m.ident always, wrong on proxies): exit 1.

All 7 same-spec wrong impls FAILED to close (exit 1). The elaboration errors confirm the theorem is genuinely false for each (impl not defeq to List.map baseOf steps). No wrong impl closed with clean axioms, so protocol step 2 (materialize+resolve a faithful patch for a closing wrong impl) has nothing to run -- there is no verify-but-not-resolve witness. Only closing impls are extensionally equal to the gold (echoes) which resolve.

REFINEMENT AUDIT: 5 legs, all R (rows 2/3/4) or I (rows 1/5); no A-consumed, no A-reference, no kind-3. Changed op cur_model._meta.concrete_model is deeply modeled via baseIdent (legitimate per SPEC_GUIDE 3), not axiomatized; axioms region empty, G-AX skips (axiom_check.py = skip stub). Deep-model correspondence baseOf <-> cur_model._meta.concrete_model holds: concrete/base model's concrete_model is itself (idempotent, baseIdent=ident); proxy's is its concrete base (baseIdent!=ident). Verified against base_commit semantics per verdict.md (base.py:226/228, options.py:141-142).

COSMETIC (non-blocking): mapping.md refers to concreteIdent/concreteOf while frozen Solution.lean uses baseIdent/baseOf -- same concept, naming drift in prose only; spec/proof/markers internally consistent and verify clean.

VERDICT: SOUND. >=5 distinct attacks (7 total) run to completion; none produced a closing clean-axiom proof, and the fully-pinned postcondition admits no verifying-but-non-resolving impl. Spec is not broken (verify => correct holds for this bundle).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closed its proof, so there is no verifying-but-non-resolving impl. The postcondition (result.length = steps.length AND for all i m, steps[i]? = some m -> result[i]? = some (baseOf m)) fully pins result = steps.map baseOf, leaving zero functional latitude; any closing implementation is extensionally equal to the gold and therefore resolves.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the model key under which each traversed relation's identifier columns
are recorded when planning which columns a query must load.

When a query restricts the fields it loads to a subset reached through related
models, it walks the chain of relations one step at a time. At each step it
reaches a target model and must record, keyed by that model, that the model's
identifier column has to be loaded (otherwise the rows for that model cannot be
assembled).

A model can be either a base model — one that owns its own storage and identifier
column — or an alias model that shares the storage and identifier column of an
underlying base model while remaining a distinct model object. Two alias models of
the same base, and an alias and its base, all share one storage and one identifier
column.

The desired behavior: at every relation step the identifier requirement is keyed
under the *base* model that owns the shared storage — never under an alias.
Keying under an alias would record the requirement against a model object that
does not, by itself, own the identifier column, leaving the load plan unable to
locate that column for the shared storage. For a model that is already a base
model, its base is itself, so keying is unchanged. The recorded keys are produced
one per step, in traversal order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The choice of
-- which model to key each step under is modeled DEEPLY over each step's resolved
-- model (its own identity together with the identity of the base model whose
-- storage it shares), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- One resolved relation-step target model, restricted to the observed aspects:
* `ident` — the identity of the model object reached by this step (which may be an
  alias model sharing another model's storage);
* `baseIdent` — the identity of the base model that owns the shared storage and
  identifier column. For a base model (one that owns its own storage) `baseIdent`
  equals `ident`; for an alias model it is the underlying base's identity. -/
structure RelModel where
  ident : Nat
  baseIdent : Nat
deriving DecidableEq, Repr

/-- The base model that owns the storage shared by this step's model: the model
under which the step's identifier requirement must be keyed. Idempotent on base
models (where `baseIdent = ident`). -/
def baseOf (m : RelModel) : Nat :=
  m.baseIdent
-- pure-end

-- post-conditions-start
/-- The produced key list is fully pinned to the traversed steps:

  * it has exactly one key per relation step, in traversal order; and
  * each key is the identity of the base model that owns the step's shared storage
    (`baseIdent`) — never the (possibly alias) resolved model itself.

Every produced key is determined for every step, so no output component is left
free. -/
def problem_spec_relationModelKeys
    (steps : List RelModel) (result : List Nat) : Prop :=
  result.length = steps.length ∧
  ∀ (i : Nat) (m : RelModel), steps[i]? = some m →
    result[i]? = some (baseOf m)
-- post-conditions-end

-- impl-start
def implementation_relationModelKeys
    (steps : List RelModel) : List Nat := Id.run do
  let mut keys : List Nat := []
  for m in steps do
    let curModel := baseOf m
    keys := keys ++ [curModel]
  return keys
-- impl-end

-- proof-start
theorem correct_relationModelKeys :
    ∀ (steps : List RelModel),
      problem_spec_relationModelKeys steps
        (implementation_relationModelKeys steps) := by
  intro steps
  -- Helper: the cleaned `forIn` loop, generalized over the accumulator, equals
  -- the prefix accumulator appended with `steps.map baseOf` (Route B).
  have hkey : ∀ (init : List Nat),
      Id.run (forIn steps init
        (fun m keys => (.yield (keys ++ [baseOf m]) : ForInStep (List Nat))))
        = init ++ steps.map baseOf := by
    intro init
    induction steps generalizing init with
    | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih (init ++ [baseOf a])]
      simp [List.append_assoc]
  -- Bridge the desugared loop body to the cleaned form and discharge the impl.
  have himpl : implementation_relationModelKeys steps = steps.map baseOf := by
    show Id.run (forIn steps []
        (fun m keys => (.yield (keys ++ [baseOf m]) : ForInStep (List Nat)))) = _
    rw [hkey []]
    simp
  refine ⟨?_, ?_⟩
  · rw [himpl]; simp
  · intro i m hi
    rw [himpl, List.getElem?_map, hi]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Commands: 'bash scripts/lean_verify.sh <file>' (run concurrently in background, <=4 at a time) and '#print axioms correct_relationModelKeys' appended to pc for the axiom check.

### RESULTS (exit code / axioms):
- pc.lean (positive control, gold impl baseOf m): exit 0 (verifies, no sorry). #print axioms correct_relationModelKeys => 'depends on axioms: [propext, Quot.sound]' -- CLEAN, no sorryAx (pc_ax.lean exit 0).
- atk_1.lean (prepatch bug, curModel := m.ident): exit 1 -- PREPATCH BUG REPRODUCED. Error: implementation_relationModelKeys steps != List.map baseOf steps.
- atk_2.lean (partial-domain: if baseIdent==0 then ident else baseIdent): exit 1.
- atk_3.lean (boundary: keys.dropLast, length wrong): exit 1.
- atk_4.lean (control-flow-effect: prepend => reversed traversal order): exit 1.
- atk_5.lean (ungrounded-oracle echo: constant key 0 per step): exit 1.
- atk_6.lean (off-by-one value: baseOf m + 1): exit 1.
- atk_7.lean (only-correct-on-base branch: if ident==baseIdent then baseOf m else m.ident, i.e. m.ident always, wrong on proxies): exit 1.

All 7 same-spec wrong impls FAILED to close (exit 1). The elaboration errors confirm the theorem is genuinely false for each (impl not defeq to List.map baseOf steps). No wrong impl closed with clean axioms, so protocol step 2 (materialize+resolve a faithful patch for a closing wrong impl) has nothing to run -- there is no verify-but-not-resolve witness. Only closing impls are extensionally equal to the gold (echoes) which resolve.

REFINEMENT AUDIT: 5 legs, all R (rows 2/3/4) or I (rows 1/5); no A-consumed, no A-reference, no kind-3. Changed op cur_model._meta.concrete_model is deeply modeled via baseIdent (legitimate per SPEC_GUIDE 3), not axiomatized; axioms region empty, G-AX skips (axiom_check.py = skip stub). Deep-model correspondence baseOf <-> cur_model._meta.concrete_model holds: concrete/base model's concrete_model is itself (idempotent, baseIdent=ident); proxy's is its concrete base (baseIdent!=ident). Verified against base_commit semantics per verdict.md (base.py:226/228, options.py:141-142).

COSMETIC (non-blocking): mapping.md refers to concreteIdent/concreteOf while frozen Solution.lean uses baseIdent/baseOf -- same concept, naming drift in prose only; spec/proof/markers internally consistent and verify clean.

VERDICT: SOUND. >=5 distinct attacks (7 total) run to completion; none produced a closing clean-axiom proof, and the fully-pinned postcondition admits no verifying-but-non-resolving impl. Spec is not broken (verify => correct holds for this bundle).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of django__django-15814 (lean). Modeled function = per-step body of the `for name in parts[:-1]` loop in Query.deferred_to_data (django/db/models/sql/query.py:719-753). Verified against the REAL repo at base_commit 5eb6a2b33d70b9889e1cafa12594ad6f80773d3a (git show confirms base code keys `add_to_dict(must_include, cur_model, opts.pk)` on the resolved cur_model as-is). Gold patch (dataset) inserts exactly one line: `cur_model = cur_model._meta.concrete_model` before the key registration; patch_equals_gold=True. So post-patch each relation step keys the pk requirement under the CONCRETE (base) model rather than the resolved (possibly proxy) model.

Modeling faithfulness: the UNCHANGED resolution branch (source.related_model / source.remote_field.model) is correctly folded into already-resolved inputs `steps : List RelModel`; each RelModel carries `ident` (resolved model, possibly proxy) and `baseIdent` (concrete base). `baseOf m = m.baseIdent` is the deep model of `cur_model._meta.concrete_model`. Spec `problem_spec_relationModelKeys` pins result.length = steps.length AND result[i] = baseOf m for every step in order — i.e. exactly the post-patch key sequence `steps.map baseOf`. Idempotence on non-proxy models (concrete_model is the class itself, options.py:141-142) is captured by baseIdent=ident.

Abstracting model objects as Nat and concrete-resolution as an independent field over-approximates nothing observable: for every step the real callee produces cur_model._meta.concrete_model as the key, matching baseOf on every input. I searched for a diverging input (empty steps -> empty; base-only steps -> identity; proxy steps -> base) and found none; the two agree pointwise. Spec is not too strong: it pins only the keyed MODEL per step (which the patch changes), leaving unmodeled the unchanged pk value and set-merge semantics — no over-constraint of an output the real behavior leaves free.

Mechanical checks: Solution.lean compiles via scripts/lean_verify.sh (exit 0). `#print axioms correct_relationModelKeys` = [propext, Quot.sound] — NO sorryAx, proof is genuine. same_spec(Solution, Solution_prepatch, lean backend)=True (spec region byte-identical). Solution_prepatch.lean (buggy: key = m.ident) FAILS verification (exit 1), confirming G-DIFF bug visibility corresponding to FAIL_TO_PASS test_select_related_only (proxy relation -> concrete base key). Conclusion: spec faithfully models the real repo callee; no drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged vs the public problem_statement. Gold edit = the single added line `cur_model = cur_model._meta.concrete_model` (normalize resolved model to its concrete base before keying). The public problem_statement ALREADY discloses this fix verbatim ('replace opts = cur_model._meta by opts = cur_model._meta.concrete_model._meta'), so proxy/concrete-model normalization is public. The Solution.lean spec view (axioms+pure+post regions; impl & proof elided to placeholders by _lean_spec_view) describes the behavior only abstractly — 'base model' vs 'alias model', 'shared storage and identifier column', key under the base never the alias, idempotent when baseIdent=ident. It uses no gold-patch tokens (no concrete_model, no proxy, no _meta, no line numbers) and no problem-statement phrasing. same_spec(Solution, Solution_prepatch)=True confirms spec regions are byte-identical across the pass/fail pair, so the fix is not encoded in a spec diff, and the impl carrying the actual key choice (baseOf) is elided from the view. Every concept surfaced is a strict abstraction of what the public statement already spells out concretely; nothing leaks beyond problem_statement. meta gates all pass, conf_skip=false, patch_equals_gold=true.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
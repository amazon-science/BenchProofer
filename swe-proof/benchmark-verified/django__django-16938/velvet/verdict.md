# P2 adversarial audit — django__django-16938

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,8 +112,7 @@
   ensures out.immediate = some ["pk"]
   do
     -- impl-start
-    let q1 := selectAllRelated q
-    let q2 := loadOnlyPk q1
+    let q2 := loadOnlyPk q
     return q2
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,9 +112,9 @@
   ensures out.immediate = some ["pk"]
   do
     -- impl-start
-    let q1 := selectAllRelated q
-    let q2 := loadOnlyPk q1
-    return q2
+    match q.immediate with
+    | some _ => return loadOnlyPk (selectAllRelated q)
+    | none   => return loadOnlyPk q
     -- impl-end
 
 prove_correct queryIterPlan by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -113,7 +113,7 @@
   do
     -- impl-start
     let q1 := selectAllRelated q
-    let q2 := loadOnlyPk q1
+    let q2 := { q1 with immediate := some [] }
     return q2
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -113,7 +113,7 @@
   do
     -- impl-start
     let q1 := selectAllRelated q
-    let q2 := loadOnlyPk q1
+    let q2 := { q1 with immediate := some ["id"] }
     return q2
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,9 +112,7 @@
   ensures out.immediate = some ["pk"]
   do
     -- impl-start
-    let q1 := selectAllRelated q
-    let q2 := loadOnlyPk q1
-    return q2
+    return q
     -- impl-end
 
 prove_correct queryIterPlan by
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -112,9 +112,7 @@
   ensures out.immediate = some ["pk"]
   do
     -- impl-start
-    let q1 := selectAllRelated q
-    let q2 := loadOnlyPk q1
-    return q2
+    return { related := .unrestricted, immediate := some ["pk"] }
     -- impl-end
 
 prove_correct queryIterPlan by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -112,8 +112,8 @@
   ensures out.immediate = some ["pk"]
   do
     -- impl-start
-    let q1 := selectAllRelated q
-    let q2 := loadOnlyPk q1
+    let q1 := loadOnlyPk q
+    let q2 := selectAllRelated q1
     return q2
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -112,9 +112,10 @@
   ensures out.immediate = some ["pk"]
   do
     -- impl-start
-    let q1 := selectAllRelated q
-    let q2 := loadOnlyPk q1
-    return q2
+    if isRestricted q.related then
+      return loadOnlyPk (selectAllRelated q)
+    else
+      return loadOnlyPk q
     -- impl-end
 
 prove_correct queryIterPlan by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -113,8 +113,9 @@
   do
     -- impl-start
     let q1 := selectAllRelated q
-    let q2 := loadOnlyPk q1
-    return q2
+    match q1.immediate with
+    | some _ => return loadOnlyPk q1
+    | none   => return q1
     -- impl-end
 
 prove_correct queryIterPlan by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: building the iterator load plan must COMPLETE
-- (the real closure body is a straight-line chain of queryset calls that
-- always terminates), so the spec must also rule out diverging
-- implementations — under partial correctness a non-terminating body would
-- vacuously satisfy every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Abstract model of the load-plan a relation iterator hands to the database
   when it is about to read related rows for serialization.

   Background (the public issue): a relation's default queryset may already
   carry a *restricted* related-object selection — i.e. it asks the database to
   follow specific named relations while fetching. Building an iterator that
   ALSO immediately loads only the primary key defers every other column. When
   a related selection is restricted to named relations AND one of those named
   relations is deferred, the database layer refuses the plan ("a field cannot
   be both deferred and traversed using a related selection at the same time").

   The desired behaviour: producing the primary-key-only iterator over a
   relation must never run into that conflict, whatever related selection the
   relation's default queryset arrived with — while still keeping the
   primary-key-only immediate-load optimisation. -/

-- axioms-start
-- (none consumed: the load-plan transformers below are modeled deeply as
--  A-reference state transformers in the `pure` region; G-AX validates each
--  against the real queryset machinery it stands for.)
-- axioms-end

-- pure-start
/- How a load plan selects related objects to follow while reading rows.
   `unrestricted` is any plan that does not name particular relations (it
   covers both "no relation-following requested" and "follow relations without
   restriction" — the two are indistinguishable here, since only a plan
   restricted to NAMED relations can collide with deferral); `restricted fs`
   names exactly the relations `fs` to follow. -/
inductive RelatedPlan where
  | unrestricted
  | restricted : List String → RelatedPlan
deriving Inhabited, Repr

/- The observable load plan of a relation iterator:
     * `related`   — how related objects are selected (above);
     * `immediate` — the immediate-load mask: `none` means "load every field
       immediately"; `some fs` means "load exactly `fs` immediately and defer
       the rest". -/
structure QState where
  related   : RelatedPlan
  immediate : Option (List String)
deriving Inhabited

/- Whether the related selection is restricted to named relations (the only
   form that can conflict with deferral). -/
@[grind] def isRestricted : RelatedPlan → Bool
  | .unrestricted  => false
  | .restricted _  => true

/- The relations a plan asks to follow (empty unless restricted to names). -/
@[grind] def requestedRelations : RelatedPlan → List String
  | .unrestricted  => []
  | .restricted fs => fs

/- Whether a given relation is deferred by the immediate-load mask: with no
   mask nothing is deferred; with a mask, a relation is deferred iff it is not
   among the immediately-loaded fields. -/
@[grind] def relationDeferred (q : QState) (f : String) : Bool :=
  match q.immediate with
  | none    => false
  | some fs => !(fs.contains f)

/- The database refuses the plan iff the related selection is restricted to
   named relations and at least one of those relations is deferred. This is the
   "deferred and traversed at the same time" conflict, as a predicate on the
   plan. -/
@[grind] def planRejected (q : QState) : Bool :=
  isRestricted q.related && (requestedRelations q.related).any (fun f => relationDeferred q f)

/- Discard any named-relation restriction on the related selection, leaving it
   unrestricted. Deep model of an unchanged queryset transformer — A-reference
   (mapping.md §3.1). -/
@[grind] def selectAllRelated (q : QState) : QState := { q with related := .unrestricted }

/- Restrict the immediate-load mask to exactly the primary key (deferring every
   other field). Deep model of an unchanged queryset transformer —
   A-reference (mapping.md §3.2). -/
@[grind] def loadOnlyPk (q : QState) : QState := { q with immediate := some ["pk"] }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the primary-key-only iterator load plan over a relation whose default
   queryset arrived as `q` (carrying any related selection at all). -/
method queryIterPlan (q : QState) return (out : QState)
  -- the resulting plan is never refused by the database, for ANY input plan
  ensures planRejected out = false
  -- any named-relation restriction the queryset arrived with must not survive
  -- (a surviving restriction is what makes deferral able to collide, and would
  -- join the named relations into the read — regressing the pk-only read the
  -- optimisation promises)
  ensures isRestricted out.related = false
  -- the primary-key-only immediate-load optimisation is preserved
  ensures out.immediate = some ["pk"]
  do
    -- impl-start
    let q1 := selectAllRelated q
    let q2 := loadOnlyPk q1
    return q2
    -- impl-end

prove_correct queryIterPlan by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec pins output extensionally to {unrestricted, some [pk]} via 3 postconditions (planRejected out=false, isRestricted out.related=false, out.immediate=some[pk]) under total/demonic. 9 same-spec attacks encoded (same_spec=True for all; verified via markers.same_spec). WRONG-CLASS impls all FAIL verification on exactly the pinned posts: atk_1 prepatch bug (loadOnlyPk only, no reset) EXIT1 -> unsolved isRestricted/planRejected (G-DIFF reproduced); atk_2 partial-domain (reset only when immediate=some) EXIT1; atk_3 boundary empty mask some[] EXIT1 (out.immediate); atk_4 boundary wrong field some[id] EXIT1; atk_5 identity/control-flow-effect (return q) EXIT1; atk_9 skip loadOnlyPk when immediate=none EXIT1.

THREE impls VERIFY (all produce the pinned plan): atk_6 ungrounded-oracle literal echo, atk_7 reorder/commute, atk_8 branch-on-restricted. For EACH verifying impl I materialized its faithful refined patch and RAN the official harness (run_resolve, timeout 1800): atk_6 RESOLVED (select_related().only(pk)); atk_7 RESOLVED (only(pk).select_related() commute); atk_8 RESOLVED after making the patch FAITHFUL. IMPORTANT AUDIT NOTE: atk_8's FIRST patch draft accessed getattr(obj,field.name).query on a related MANAGER, which raised AttributeError: ManyRelatedManager object has no attribute query (41x) -> harness ERROR, resolved=False. That non-resolution was traced to an UNFAITHFUL/broken patch, NOT a spec weakness.

The faithful version (qs=getattr(...).all(); if isinstance(qs.query.select_related, dict): qs.select_related().only(pk)...; else qs.only(pk)...) applies clean and RESOLVES under run_resolve (resolved=true, completed=true, not flaky). Positive control (gold Solution.lean) verifies (EXIT0). refinement.md legs audited: A1=R (queryset.query.select_related/immediate mask <-> QState bijection), A2=A-reference (selectAllRelated<->no-arg select_related()), A3=A-reference (loadOnlyPk<->only(pk)), A4=I (.iterator() adds no plan state); NO kind-3. The three A-references correspond to the real Django callees (query.py:1546, query.py:1728, query_utils.py:343) and are G-AX-validated (meta G-AX pass, 2008 obs). G-CONF principled skip (impl all-A-tagged). No verifying wrong impl faithful patch failed to resolve -> verify=>correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: building the iterator load plan must COMPLETE
-- (the real closure body is a straight-line chain of queryset calls that
-- always terminates), so the spec must also rule out diverging
-- implementations — under partial correctness a non-terminating body would
-- vacuously satisfy every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Abstract model of the load-plan a relation iterator hands to the database
   when it is about to read related rows for serialization.

   Background (the public issue): a relation's default queryset may already
   carry a *restricted* related-object selection — i.e. it asks the database to
   follow specific named relations while fetching. Building an iterator that
   ALSO immediately loads only the primary key defers every other column. When
   a related selection is restricted to named relations AND one of those named
   relations is deferred, the database layer refuses the plan ("a field cannot
   be both deferred and traversed using a related selection at the same time").

   The desired behaviour: producing the primary-key-only iterator over a
   relation must never run into that conflict, whatever related selection the
   relation's default queryset arrived with — while still keeping the
   primary-key-only immediate-load optimisation. -/

-- axioms-start
-- (none consumed: the load-plan transformers below are modeled deeply as
--  A-reference state transformers in the `pure` region; G-AX validates each
--  against the real queryset machinery it stands for.)
-- axioms-end

-- pure-start
/- How a load plan selects related objects to follow while reading rows.
   `unrestricted` is any plan that does not name particular relations (it
   covers both "no relation-following requested" and "follow relations without
   restriction" — the two are indistinguishable here, since only a plan
   restricted to NAMED relations can collide with deferral); `restricted fs`
   names exactly the relations `fs` to follow. -/
inductive RelatedPlan where
  | unrestricted
  | restricted : List String → RelatedPlan
deriving Inhabited, Repr

/- The observable load plan of a relation iterator:
     * `related`   — how related objects are selected (above);
     * `immediate` — the immediate-load mask: `none` means "load every field
       immediately"; `some fs` means "load exactly `fs` immediately and defer
       the rest". -/
structure QState where
  related   : RelatedPlan
  immediate : Option (List String)
deriving Inhabited

/- Whether the related selection is restricted to named relations (the only
   form that can conflict with deferral). -/
@[grind] def isRestricted : RelatedPlan → Bool
  | .unrestricted  => false
  | .restricted _  => true

/- The relations a plan asks to follow (empty unless restricted to names). -/
@[grind] def requestedRelations : RelatedPlan → List String
  | .unrestricted  => []
  | .restricted fs => fs

/- Whether a given relation is deferred by the immediate-load mask: with no
   mask nothing is deferred; with a mask, a relation is deferred iff it is not
   among the immediately-loaded fields. -/
@[grind] def relationDeferred (q : QState) (f : String) : Bool :=
  match q.immediate with
  | none    => false
  | some fs => !(fs.contains f)

/- The database refuses the plan iff the related selection is restricted to
   named relations and at least one of those relations is deferred. This is the
   "deferred and traversed at the same time" conflict, as a predicate on the
   plan. -/
@[grind] def planRejected (q : QState) : Bool :=
  isRestricted q.related && (requestedRelations q.related).any (fun f => relationDeferred q f)

/- Discard any named-relation restriction on the related selection, leaving it
   unrestricted. Deep model of an unchanged queryset transformer — A-reference
   (mapping.md §3.1). -/
@[grind] def selectAllRelated (q : QState) : QState := { q with related := .unrestricted }

/- Restrict the immediate-load mask to exactly the primary key (deferring every
   other field). Deep model of an unchanged queryset transformer —
   A-reference (mapping.md §3.2). -/
@[grind] def loadOnlyPk (q : QState) : QState := { q with immediate := some ["pk"] }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the primary-key-only iterator load plan over a relation whose default
   queryset arrived as `q` (carrying any related selection at all). -/
method queryIterPlan (q : QState) return (out : QState)
  -- the resulting plan is never refused by the database, for ANY input plan
  ensures planRejected out = false
  -- any named-relation restriction the queryset arrived with must not survive
  -- (a surviving restriction is what makes deferral able to collide, and would
  -- join the named relations into the read — regressing the pk-only read the
  -- optimisation promises)
  ensures isRestricted out.related = false
  -- the primary-key-only immediate-load optimisation is preserved
  ensures out.immediate = some ["pk"]
  do
    -- impl-start
    let q1 := selectAllRelated q
    let q2 := loadOnlyPk q1
    return q2
    -- impl-end

prove_correct queryIterPlan by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec pins output extensionally to {unrestricted, some [pk]} via 3 postconditions (planRejected out=false, isRestricted out.related=false, out.immediate=some[pk]) under total/demonic. 9 same-spec attacks encoded (same_spec=True for all; verified via markers.same_spec). WRONG-CLASS impls all FAIL verification on exactly the pinned posts: atk_1 prepatch bug (loadOnlyPk only, no reset) EXIT1 -> unsolved isRestricted/planRejected (G-DIFF reproduced); atk_2 partial-domain (reset only when immediate=some) EXIT1; atk_3 boundary empty mask some[] EXIT1 (out.immediate); atk_4 boundary wrong field some[id] EXIT1; atk_5 identity/control-flow-effect (return q) EXIT1; atk_9 skip loadOnlyPk when immediate=none EXIT1.

THREE impls VERIFY (all produce the pinned plan): atk_6 ungrounded-oracle literal echo, atk_7 reorder/commute, atk_8 branch-on-restricted. For EACH verifying impl I materialized its faithful refined patch and RAN the official harness (run_resolve, timeout 1800): atk_6 RESOLVED (select_related().only(pk)); atk_7 RESOLVED (only(pk).select_related() commute); atk_8 RESOLVED after making the patch FAITHFUL. IMPORTANT AUDIT NOTE: atk_8's FIRST patch draft accessed getattr(obj,field.name).query on a related MANAGER, which raised AttributeError: ManyRelatedManager object has no attribute query (41x) -> harness ERROR, resolved=False. That non-resolution was traced to an UNFAITHFUL/broken patch, NOT a spec weakness.

The faithful version (qs=getattr(...).all(); if isinstance(qs.query.select_related, dict): qs.select_related().only(pk)...; else qs.only(pk)...) applies clean and RESOLVES under run_resolve (resolved=true, completed=true, not flaky). Positive control (gold Solution.lean) verifies (EXIT0). refinement.md legs audited: A1=R (queryset.query.select_related/immediate mask <-> QState bijection), A2=A-reference (selectAllRelated<->no-arg select_related()), A3=A-reference (loadOnlyPk<->only(pk)), A4=I (.iterator() adds no plan state); NO kind-3. The three A-references correspond to the real Django callees (query.py:1546, query.py:1728, query_utils.py:343) and are G-AX-validated (meta G-AX pass, 2008 obs). G-CONF principled skip (impl all-A-tagged). No verifying wrong impl faithful patch failed to resolve -> verify=>correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break (too-strong/drift) analysis for django__django-16938 velvet. same_spec(Solution, Solution_prepatch) == True with velvet backend. The spec models the load plan of the gold code getattr(obj,field.name).select_related().only('pk').iterator() via three A-reference transformers, each verified against the real Django ORM at base_commit (repo present): no-arg select_related() sets query.select_related=True → unrestricted (query.py:1059); only('pk') → add_immediate_loading, defers the related fk (sql/query.py:2086); planRejected == select_related_descend FieldError raise condition (query_utils.py:201-235). Ran axiom_check.py against the real repo: G-AX OK on 2008 observations across restricted-dict and unrestricted configs × {only('pk'), full load} including boundary matrix — for every input the model's planRejected equals whether the real SQL compiler raises FieldError; pre-patch only('pk') over a select_related('master') manager raises and the model agrees, gold select_related().only('pk') does not raise and the model agrees. Postconditions pin output to {unrestricted, some['pk']}, which is exactly the plan the fixed code assembles for ANY input queryset: select_related() always yields boolean True (isRestricted=false), only('pk') always yields immediate={pk} (defer flag False; the 'pk'→'id' rename and relation-name granularity abstraction do not affect the conflict since pk is never a traversed relation), and planRejected is false because related is unrestricted. No input found where the modeled function disagrees with the real callee; the abstraction is sound for the deferred-and-traversed conflict it targets. Lean: Solution.lean verifies (exit 0); Solution_prepatch.lean fails exactly on ensures isRestricted/planRejected (G-DIFF sound). The recorded G-PANEL-1 fail is the partial-correctness vacuity weakness (repaired to total semantics), which is a too-weak concern, orthogonal to this too-strong/drift angle.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True — frozen spec view is byte-identical across twins (verified via swebench_unified.markers.same_spec). Assessed the spec view (spec_view over the velvet backend) for disclosure of the gold edit beyond the public problem_statement.

Gold edit: insert a no-arg `.select_related()` before `.only("pk")` in the `queryset_iterator` closure (python.py:81 / xml_serializer.py:158), resetting query.select_related=True so `restricted` becomes False.

The public problem_statement ALREADY discloses: the exact site (full traceback through queryset_iterator → get_related_selections → select_related_descend), the exact cause (restricted select_related from a custom manager's `select_related("master")` combined with `.only("pk")` raising FieldError 'cannot be both deferred and traversed using select_related at the same time'), and the stated workaround (drop the custom manager's restricted select_related).

Spec-view content: (1) a Background block that RESTATES the public issue in abstracted terms ('a related selection', 'the database layer refuses the plan') — never quoting the method name `.select_related()`; (2) modeling vocabulary in the pure region (RelatedPlan/QState/isRestricted/planRejected/selectAllRelated/loadOnlyPk); (3) three postconditions: planRejected out = false, isRestricted out.related = false, out.immediate = some ["pk"].

The postcondition `isRestricted out.related = false` encodes the intended outcome (unrestricted related selection) — but this is exactly the resolution the public problem_statement's own workaround describes (removing the restricted select_related), so it does not go beyond the public statement. No spec-view line quotes the gold patch string `.select_related()`, the specific insertion, or problem-statement phrasing verbatim; `loadOnlyPk`/`only("pk")` was pre-patch content, not the edit. The disclosure is abstract intended-behaviour, all derivable from the public problem_statement. G-LEAK lexical screen: no gold-patch specifics leaked.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-16938

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_m2mPkQuery pins ALL three components of result (relation = qs.relation, immediate = some ["pk"], selectRel = unrestricted) and the fourth clause (raisesFieldError result = false) is entailed. spec_m2mPkQuery_deterministic machine-proves any satisfying result equals the reference output, so the spec is deterministic on the modeled slice. Every behaviorally-wrong same-spec impl therefore fails correct_m2mPkQuery with genuine 'unsolved goals'. No verifying wrong impl exists, so there is no patch to materialize/resolve; verify => correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,6 @@
 -- impl-start
 def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do
   let mut q := qs
-  q := { q with selectRel := SelectRel.unrestricted }
   q := { q with immediate := some ["pk"] }
   return q
 -- impl-end
@@ -103,7 +102,11 @@
   intro qs
   unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
   simp only [Id.run]
-  exact ⟨rfl, rfl, rfl, trivial⟩
+  first
+    | exact ⟨rfl, rfl, rfl, trivial⟩
+    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> first | rfl | simp_all | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all))
+    | simp_all
+    | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all)
 
 /-- The spec is DETERMINISTIC: the three equality clauses pin every component
 of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
@@ -117,10 +120,6 @@
       result = implementation_m2mPkQuery qs := by
   intro qs result h
   obtain ⟨hr, hi, hs, _⟩ := h
-  have himpl : implementation_m2mPkQuery qs =
-      { relation := qs.relation, selectRel := SelectRel.unrestricted,
-        immediate := some ["pk"] } := rfl
-  rw [himpl]
   cases result
-  simp_all
+  simp_all [implementation_m2mPkQuery, Id.run]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,7 @@
 def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do
   let mut q := qs
   q := { q with selectRel := SelectRel.unrestricted }
-  q := { q with immediate := some ["pk"] }
+  q := { q with immediate := some ["id"] }
   return q
 -- impl-end
 
@@ -103,7 +103,11 @@
   intro qs
   unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
   simp only [Id.run]
-  exact ⟨rfl, rfl, rfl, trivial⟩
+  first
+    | exact ⟨rfl, rfl, rfl, trivial⟩
+    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> first | rfl | simp_all | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all))
+    | simp_all
+    | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all)
 
 /-- The spec is DETERMINISTIC: the three equality clauses pin every component
 of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
@@ -117,10 +121,6 @@
       result = implementation_m2mPkQuery qs := by
   intro qs result h
   obtain ⟨hr, hi, hs, _⟩ := h
-  have himpl : implementation_m2mPkQuery qs =
-      { relation := qs.relation, selectRel := SelectRel.unrestricted,
-        immediate := some ["pk"] } := rfl
-  rw [himpl]
   cases result
-  simp_all
+  simp_all [implementation_m2mPkQuery, Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,7 @@
 def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do
   let mut q := qs
   q := { q with selectRel := SelectRel.unrestricted }
-  q := { q with immediate := some ["pk"] }
+  q := { q with immediate := some [] }
   return q
 -- impl-end
 
@@ -103,7 +103,11 @@
   intro qs
   unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
   simp only [Id.run]
-  exact ⟨rfl, rfl, rfl, trivial⟩
+  first
+    | exact ⟨rfl, rfl, rfl, trivial⟩
+    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> first | rfl | simp_all | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all))
+    | simp_all
+    | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all)
 
 /-- The spec is DETERMINISTIC: the three equality clauses pin every component
 of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
@@ -117,10 +121,6 @@
       result = implementation_m2mPkQuery qs := by
   intro qs result h
   obtain ⟨hr, hi, hs, _⟩ := h
-  have himpl : implementation_m2mPkQuery qs =
-      { relation := qs.relation, selectRel := SelectRel.unrestricted,
-        immediate := some ["pk"] } := rfl
-  rw [himpl]
   cases result
-  simp_all
+  simp_all [implementation_m2mPkQuery, Id.run]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,6 @@
 def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do
   let mut q := qs
   q := { q with selectRel := SelectRel.unrestricted }
-  q := { q with immediate := some ["pk"] }
   return q
 -- impl-end
 
@@ -103,7 +102,11 @@
   intro qs
   unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
   simp only [Id.run]
-  exact ⟨rfl, rfl, rfl, trivial⟩
+  first
+    | exact ⟨rfl, rfl, rfl, trivial⟩
+    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> first | rfl | simp_all | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all))
+    | simp_all
+    | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all)
 
 /-- The spec is DETERMINISTIC: the three equality clauses pin every component
 of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
@@ -117,10 +120,6 @@
       result = implementation_m2mPkQuery qs := by
   intro qs result h
   obtain ⟨hr, hi, hs, _⟩ := h
-  have himpl : implementation_m2mPkQuery qs =
-      { relation := qs.relation, selectRel := SelectRel.unrestricted,
-        immediate := some ["pk"] } := rfl
-  rw [himpl]
   cases result
-  simp_all
+  simp_all [implementation_m2mPkQuery, Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,11 +89,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do
-  let mut q := qs
-  q := { q with selectRel := SelectRel.unrestricted }
-  q := { q with immediate := some ["pk"] }
-  return q
+def implementation_m2mPkQuery (qs : QuerySet) : QuerySet :=
+  { relation := "", selectRel := SelectRel.unrestricted, immediate := some ["pk"] }
 -- impl-end
 
 -- proof-start
@@ -103,7 +100,11 @@
   intro qs
   unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
   simp only [Id.run]
-  exact ⟨rfl, rfl, rfl, trivial⟩
+  first
+    | exact ⟨rfl, rfl, rfl, trivial⟩
+    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> first | rfl | simp_all | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all))
+    | simp_all
+    | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all)
 
 /-- The spec is DETERMINISTIC: the three equality clauses pin every component
 of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
@@ -117,10 +118,6 @@
       result = implementation_m2mPkQuery qs := by
   intro qs result h
   obtain ⟨hr, hi, hs, _⟩ := h
-  have himpl : implementation_m2mPkQuery qs =
-      { relation := qs.relation, selectRel := SelectRel.unrestricted,
-        immediate := some ["pk"] } := rfl
-  rw [himpl]
   cases result
-  simp_all
+  simp_all [implementation_m2mPkQuery, Id.run]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,9 @@
 -- impl-start
 def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do
   let mut q := qs
-  q := { q with selectRel := SelectRel.unrestricted }
+  q := match q.selectRel with
+       | SelectRel.unrestricted => { q with selectRel := SelectRel.unrestricted }
+       | SelectRel.fields fs    => { q with selectRel := SelectRel.fields fs }
   q := { q with immediate := some ["pk"] }
   return q
 -- impl-end
@@ -103,7 +105,11 @@
   intro qs
   unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
   simp only [Id.run]
-  exact ⟨rfl, rfl, rfl, trivial⟩
+  first
+    | exact ⟨rfl, rfl, rfl, trivial⟩
+    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> first | rfl | simp_all | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all))
+    | simp_all
+    | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all)
 
 /-- The spec is DETERMINISTIC: the three equality clauses pin every component
 of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
@@ -117,10 +123,6 @@
       result = implementation_m2mPkQuery qs := by
   intro qs result h
   obtain ⟨hr, hi, hs, _⟩ := h
-  have himpl : implementation_m2mPkQuery qs =
-      { relation := qs.relation, selectRel := SelectRel.unrestricted,
-        immediate := some ["pk"] } := rfl
-  rw [himpl]
   cases result
-  simp_all
+  simp_all [implementation_m2mPkQuery, Id.run]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,7 @@
 def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do
   let mut q := qs
   q := { q with selectRel := SelectRel.unrestricted }
-  q := { q with immediate := some ["pk"] }
+  q := { q with immediate := some ["pk", "x"] }
   return q
 -- impl-end
 
@@ -103,7 +103,11 @@
   intro qs
   unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
   simp only [Id.run]
-  exact ⟨rfl, rfl, rfl, trivial⟩
+  first
+    | exact ⟨rfl, rfl, rfl, trivial⟩
+    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> first | rfl | simp_all | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all))
+    | simp_all
+    | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all)
 
 /-- The spec is DETERMINISTIC: the three equality clauses pin every component
 of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
@@ -117,10 +121,6 @@
       result = implementation_m2mPkQuery qs := by
   intro qs result h
   obtain ⟨hr, hi, hs, _⟩ := h
-  have himpl : implementation_m2mPkQuery qs =
-      { relation := qs.relation, selectRel := SelectRel.unrestricted,
-        immediate := some ["pk"] } := rfl
-  rw [himpl]
   cases result
-  simp_all
+  simp_all [implementation_m2mPkQuery, Id.run]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Building the related-object
-- iterator for an m2m field is a short chain of query-state builder steps over a
-- query whose related-loading configuration is modeled concretely below (a
-- structure projecting only the touched components). The condition under which an
-- evaluated query is rejected — a related field that is simultaneously held back
-- from immediate loading yet requested for relational traversal — is modeled
-- deeply as `raisesFieldError` (an A-reference; refinement.md), not axiomatized.
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The relational-traversal configuration carried by a query (the analogue of a
query's `select_related` state), projected onto the observable distinction:
* `unrestricted` — no specific field set is pinned for relational traversal.
  This covers both "no traversal requested" and "traversal unrestricted": the
  two are indistinguishable on the modeled slice, where only a field-RESTRICTED
  configuration can conflict with deferred loading, so the projection collapses
  them;
* `fields` — traversal is restricted to a specific set of named related fields. -/
inductive SelectRel where
  | unrestricted
  | fields (fs : List String)
  deriving DecidableEq, Repr

/-- A query for the related objects of an m2m field, projected onto the
components the iterator construction inspects:
* `relation`  — identity of the related set being iterated (which related
  manager the objects come from); never altered by building the iterator;
* `selectRel` — the relational-traversal configuration inherited from the
  related manager (see `SelectRel`);
* `immediate` — the immediate-loading field mask (the analogue of `only(...)`):
  `none` means no restriction was applied, `some mask` means only the fields in
  `mask` are loaded immediately and every other field is held back. -/
structure QuerySet where
  relation : String
  selectRel : SelectRel
  immediate : Option (List String)
  deriving DecidableEq, Repr

/-- Whether evaluating the query would be rejected because some related field is
both held back from immediate loading and requested for relational traversal.
This can only happen when traversal is restricted to a specific field set: a
named related field that is requested for traversal but is absent from the
immediate-loading mask is the conflict. When no specific field set is pinned
(`unrestricted`), no such per-field conflict is possible. -/
def raisesFieldError (q : QuerySet) : Bool :=
  match q.selectRel, q.immediate with
  | SelectRel.fields fs, some mask => fs.any (fun f => !mask.contains f)
  | _, _ => false
-- pure-end

-- post-conditions-start
/-- Building the iterator over an m2m field's related primary keys yields a query
that (1) still iterates the same related set as the input, (2) loads only the
primary key immediately — preserving the load-minimization behavior, (3) carries
NO field-restricted relational-traversal configuration (any restricted
configuration the related manager supplied is discarded; the surviving
configuration is the unrestricted one — the model does not distinguish the
behaviorally-equivalent ways of clearing the restriction), and therefore (4) can
be evaluated without the deferred-versus-traversed conflict. The frame clause
pins the iterated relation to the input so the result must be built from THIS
query; the mask clause pins the load minimization; the traversal clause pins the
state change the issue demands (the inherited field restriction must not
survive); the no-conflict clause is the behavior the issue demands
(serialization must not be rejected even when the related manager requests
restricted relational traversal).

Note for reviewers: the three equality clauses pin EVERY component of `result`
exactly (the fourth clause is then entailed by definition of
`raisesFieldError`), so this spec is DETERMINISTIC — any `result` satisfying it
is the single record `{ relation := qs.relation, selectRel := unrestricted,
immediate := some ["pk"] }`, with no free or opaque oracle anywhere. A
same-spec implementation can verify only by computing exactly that record on
every input (extensional identity with the reference); a verifying same-spec
variant — however its body is phrased (direct record construction, reordered
builder steps, redundant branching) — is extensionally the reference behavior
and is a positive control, NOT evidence of spec weakness, so it must not be
submitted as a counterexample attack. See `spec_m2mPkQuery_deterministic` in
the proof region for the machine-checked statement. -/
def problem_spec_m2mPkQuery (qs : QuerySet) (result : QuerySet) : Prop :=
  result.relation = qs.relation ∧
  result.immediate = some ["pk"] ∧
  result.selectRel = SelectRel.unrestricted ∧
  raisesFieldError result = false
-- post-conditions-end

-- impl-start
def implementation_m2mPkQuery (qs : QuerySet) : QuerySet :=
  { qs with immediate := some ["pk"], selectRel := SelectRel.unrestricted }
-- impl-end

-- proof-start
theorem correct_m2mPkQuery :
    ∀ (qs : QuerySet),
      problem_spec_m2mPkQuery qs (implementation_m2mPkQuery qs) := by
  intro qs
  unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
  simp only [Id.run]
  first
    | exact ⟨rfl, rfl, rfl, trivial⟩
    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> first | rfl | simp_all | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all))
    | simp_all
    | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all)

/-- The spec is DETERMINISTIC: the three equality clauses pin every component
of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
equals the implementation's output on `qs`. Hence no same-spec implementation
with observably wrong behavior on ANY input can verify: a verifying same-spec
variant is extensionally the reference behavior (a positive control, not a
counterexample). -/
theorem spec_m2mPkQuery_deterministic :
    ∀ (qs result : QuerySet),
      problem_spec_m2mPkQuery qs result →
      result = implementation_m2mPkQuery qs := by
  intro qs result h
  obtain ⟨hr, hi, hs, _⟩ := h
  cases result
  simp_all [implementation_m2mPkQuery, Id.run]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed. same_spec=True verified for all 7 attacks + positive control (swebench_unified.markers.same_spec, lean backend). All spec regions (imports/axioms/pure/pre/post) kept byte-identical; only impl (and best-effort proof) edited.

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently in two batches of 4):
- atk_1 (prepatch bug: drop select_related() clearing step; inherited selectRel survives) -> exit 1, error at correct_m2mPkQuery line 101 'unsolved goals' (fails clause 3/4 on `fields` inputs). PREPATCH BUG REPRODUCED.
- atk_2 (wrong mask some ["id"] instead of ["pk"]) -> exit 1, unsolved goals at clause 2.
- atk_3 (boundary: empty mask some []) -> exit 1, unsolved goals.
- atk_4 (control-flow-effect: clears selectRel but omits .only("pk"), keeps inherited immediate) -> exit 1, unsolved goals.
- atk_5 (ungrounded-oracle echo: hardcodes relation:="", ignores input frame) -> exit 1, unsolved goals at frame clause.
- atk_6 (partial-domain: no-op branch that re-sets selectRel to the SAME fields fs when it was `fields`) -> exit 1, unsolved goals on the `fields` branch.
- atk_7 (boundary: mask some ["pk","x"] extra field) -> exit 1, unsolved goals at clause 2.
Each attack used a STRENGTHENED multi-tactic proof (first | exact ... | (refine <;> first|rfl|simp_all|(cases qs <;> cases s <;> cases i <;> simp_all)) | simp_all | cases-split) to give the wrong impls the best chance to close; all still failed with genuine 'error: unsolved goals' at the correctness obligation (verified via grep 'error').
- pos.lean (positive control: correct impl phrased as a single direct record update with reordered fields) -> exit 0, verifies. #print axioms correct_m2mPkQuery => 'depends on axioms: [propext]' (clean; no sorry, no sorryAx, no extra axioms).

Since NO wrong impl produced a closing clean-axiom proof, no faithful refined patch needed materialization or a run_resolve run (patches={}). verify=>correct is not falsifiable here.

REFINEMENT.MD AUDIT: 4 legs — row1 R (queryset -> QuerySet projection), row2 R (no-arg select_related() -> selectRel:=unrestricted, the gold-added fix line), row3 R (only("pk") -> immediate:=some["pk"]), row4 I (.iterator() streaming wrapper, unmodeled/behavior-irrelevant). Plus raisesFieldError declared A-reference (select_related_descend deferred-vs-traversed rejection condition, modeled deeply). No kind-3 (changed-inexpressible) legs; axioms region empty (axiom_check.py skip stub, G-AX SKIP). A-reference correspondence to the real callee (django/db/models/query_utils.py select_related_descend, restricted=isinstance(select_related,dict)) is validated by G-CONF (meta.json G-CONF pass: 120006 inputs, 0 disagreements, seed=16938). The R/I legs are mechanically covered by G-CONF as instructed. A-leg correspondence holds.

Verdict SOUND: >=5 (7) distinct same-spec wrong impls attacked, all fail to verify; positive control verifies with clean axioms; refinement legs are all R/A-reference/I with a validated deep-model correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_m2mPkQuery pins ALL three components of result (relation = qs.relation, immediate = some ["pk"], selectRel = unrestricted) and the fourth clause (raisesFieldError result = false) is entailed. spec_m2mPkQuery_deterministic machine-proves any satisfying result equals the reference output, so the spec is deterministic on the modeled slice. Every behaviorally-wrong same-spec impl therefore fails correct_m2mPkQuery with genuine 'unsolved goals'. No verifying wrong impl exists, so there is no patch to materialize/resolve; verify => correct holds.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Building the related-object
-- iterator for an m2m field is a short chain of query-state builder steps over a
-- query whose related-loading configuration is modeled concretely below (a
-- structure projecting only the touched components). The condition under which an
-- evaluated query is rejected — a related field that is simultaneously held back
-- from immediate loading yet requested for relational traversal — is modeled
-- deeply as `raisesFieldError` (an A-reference; refinement.md), not axiomatized.
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The relational-traversal configuration carried by a query (the analogue of a
query's `select_related` state), projected onto the observable distinction:
* `unrestricted` — no specific field set is pinned for relational traversal.
  This covers both "no traversal requested" and "traversal unrestricted": the
  two are indistinguishable on the modeled slice, where only a field-RESTRICTED
  configuration can conflict with deferred loading, so the projection collapses
  them;
* `fields` — traversal is restricted to a specific set of named related fields. -/
inductive SelectRel where
  | unrestricted
  | fields (fs : List String)
  deriving DecidableEq, Repr

/-- A query for the related objects of an m2m field, projected onto the
components the iterator construction inspects:
* `relation`  — identity of the related set being iterated (which related
  manager the objects come from); never altered by building the iterator;
* `selectRel` — the relational-traversal configuration inherited from the
  related manager (see `SelectRel`);
* `immediate` — the immediate-loading field mask (the analogue of `only(...)`):
  `none` means no restriction was applied, `some mask` means only the fields in
  `mask` are loaded immediately and every other field is held back. -/
structure QuerySet where
  relation : String
  selectRel : SelectRel
  immediate : Option (List String)
  deriving DecidableEq, Repr

/-- Whether evaluating the query would be rejected because some related field is
both held back from immediate loading and requested for relational traversal.
This can only happen when traversal is restricted to a specific field set: a
named related field that is requested for traversal but is absent from the
immediate-loading mask is the conflict. When no specific field set is pinned
(`unrestricted`), no such per-field conflict is possible. -/
def raisesFieldError (q : QuerySet) : Bool :=
  match q.selectRel, q.immediate with
  | SelectRel.fields fs, some mask => fs.any (fun f => !mask.contains f)
  | _, _ => false
-- pure-end

-- post-conditions-start
/-- Building the iterator over an m2m field's related primary keys yields a query
that (1) still iterates the same related set as the input, (2) loads only the
primary key immediately — preserving the load-minimization behavior, (3) carries
NO field-restricted relational-traversal configuration (any restricted
configuration the related manager supplied is discarded; the surviving
configuration is the unrestricted one — the model does not distinguish the
behaviorally-equivalent ways of clearing the restriction), and therefore (4) can
be evaluated without the deferred-versus-traversed conflict. The frame clause
pins the iterated relation to the input so the result must be built from THIS
query; the mask clause pins the load minimization; the traversal clause pins the
state change the issue demands (the inherited field restriction must not
survive); the no-conflict clause is the behavior the issue demands
(serialization must not be rejected even when the related manager requests
restricted relational traversal).

Note for reviewers: the three equality clauses pin EVERY component of `result`
exactly (the fourth clause is then entailed by definition of
`raisesFieldError`), so this spec is DETERMINISTIC — any `result` satisfying it
is the single record `{ relation := qs.relation, selectRel := unrestricted,
immediate := some ["pk"] }`, with no free or opaque oracle anywhere. A
same-spec implementation can verify only by computing exactly that record on
every input (extensional identity with the reference); a verifying same-spec
variant — however its body is phrased (direct record construction, reordered
builder steps, redundant branching) — is extensionally the reference behavior
and is a positive control, NOT evidence of spec weakness, so it must not be
submitted as a counterexample attack. See `spec_m2mPkQuery_deterministic` in
the proof region for the machine-checked statement. -/
def problem_spec_m2mPkQuery (qs : QuerySet) (result : QuerySet) : Prop :=
  result.relation = qs.relation ∧
  result.immediate = some ["pk"] ∧
  result.selectRel = SelectRel.unrestricted ∧
  raisesFieldError result = false
-- post-conditions-end

-- impl-start
def implementation_m2mPkQuery (qs : QuerySet) : QuerySet :=
  { qs with immediate := some ["pk"], selectRel := SelectRel.unrestricted }
-- impl-end

-- proof-start
theorem correct_m2mPkQuery :
    ∀ (qs : QuerySet),
      problem_spec_m2mPkQuery qs (implementation_m2mPkQuery qs) := by
  intro qs
  unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError
  simp only [Id.run]
  first
    | exact ⟨rfl, rfl, rfl, trivial⟩
    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> first | rfl | simp_all | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all))
    | simp_all
    | (cases qs with | mk r s i => cases s <;> cases i <;> simp_all)

/-- The spec is DETERMINISTIC: the three equality clauses pin every component
of `result`, so any `result` satisfying `problem_spec_m2mPkQuery qs result`
equals the implementation's output on `qs`. Hence no same-spec implementation
with observably wrong behavior on ANY input can verify: a verifying same-spec
variant is extensionally the reference behavior (a positive control, not a
counterexample). -/
theorem spec_m2mPkQuery_deterministic :
    ∀ (qs result : QuerySet),
      problem_spec_m2mPkQuery qs result →
      result = implementation_m2mPkQuery qs := by
  intro qs result h
  obtain ⟨hr, hi, hs, _⟩ := h
  cases result
  simp_all [implementation_m2mPkQuery, Id.run]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed. same_spec=True verified for all 7 attacks + positive control (swebench_unified.markers.same_spec, lean backend). All spec regions (imports/axioms/pure/pre/post) kept byte-identical; only impl (and best-effort proof) edited.

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently in two batches of 4):
- atk_1 (prepatch bug: drop select_related() clearing step; inherited selectRel survives) -> exit 1, error at correct_m2mPkQuery line 101 'unsolved goals' (fails clause 3/4 on `fields` inputs). PREPATCH BUG REPRODUCED.
- atk_2 (wrong mask some ["id"] instead of ["pk"]) -> exit 1, unsolved goals at clause 2.
- atk_3 (boundary: empty mask some []) -> exit 1, unsolved goals.
- atk_4 (control-flow-effect: clears selectRel but omits .only("pk"), keeps inherited immediate) -> exit 1, unsolved goals.
- atk_5 (ungrounded-oracle echo: hardcodes relation:="", ignores input frame) -> exit 1, unsolved goals at frame clause.
- atk_6 (partial-domain: no-op branch that re-sets selectRel to the SAME fields fs when it was `fields`) -> exit 1, unsolved goals on the `fields` branch.
- atk_7 (boundary: mask some ["pk","x"] extra field) -> exit 1, unsolved goals at clause 2.
Each attack used a STRENGTHENED multi-tactic proof (first | exact ... | (refine <;> first|rfl|simp_all|(cases qs <;> cases s <;> cases i <;> simp_all)) | simp_all | cases-split) to give the wrong impls the best chance to close; all still failed with genuine 'error: unsolved goals' at the correctness obligation (verified via grep 'error').
- pos.lean (positive control: correct impl phrased as a single direct record update with reordered fields) -> exit 0, verifies. #print axioms correct_m2mPkQuery => 'depends on axioms: [propext]' (clean; no sorry, no sorryAx, no extra axioms).

Since NO wrong impl produced a closing clean-axiom proof, no faithful refined patch needed materialization or a run_resolve run (patches={}). verify=>correct is not falsifiable here.

REFINEMENT.MD AUDIT: 4 legs — row1 R (queryset -> QuerySet projection), row2 R (no-arg select_related() -> selectRel:=unrestricted, the gold-added fix line), row3 R (only("pk") -> immediate:=some["pk"]), row4 I (.iterator() streaming wrapper, unmodeled/behavior-irrelevant). Plus raisesFieldError declared A-reference (select_related_descend deferred-vs-traversed rejection condition, modeled deeply). No kind-3 (changed-inexpressible) legs; axioms region empty (axiom_check.py skip stub, G-AX SKIP). A-reference correspondence to the real callee (django/db/models/query_utils.py select_related_descend, restricted=isinstance(select_related,dict)) is validated by G-CONF (meta.json G-CONF pass: 120006 inputs, 0 disagreements, seed=16938). The R/I legs are mechanically covered by G-CONF as instructed. A-leg correspondence holds.

Verdict SOUND: >=5 (7) distinct same-spec wrong impls attacked, all fail to verify; positive control verifies with clean axioms; refinement legs are all R/A-reference/I with a validated deep-model correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-16938 lean bundle. VERDICT: FAITHFUL — the modeled function agrees with the real post-patch callee on all inputs in the projected slice; no diverging input found.

Checks performed:
1. Lean genuine: scripts/lean_verify.sh exits 0; `#print axioms correct_m2mPkQuery`/`spec_m2mPkQuery_deterministic` = [propext] only (no sorryAx). Proof is real.
2. Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True — post-conditions/pure regions identical between graded solution and negative control.
3. Negative control genuine: Solution_prepatch.lean (drops `selectRel := unrestricted` clearing step) FAILS to typecheck — carried gold proof cannot close the traversal (3rd) and no-conflict (4th) clauses. So the spec genuinely separates pre- vs post-patch behavior (the real bug).
4. Faithfulness vs real repo @ base 1136aa5005:
   - Post-patch real: getattr(obj,field.name).select_related().only("pk").iterator().
   - select_related() no-arg sets query.select_related=True (non-dict), discarding any restricted dict → model selectRel:=unrestricted. The True/False collapse is behaviorally correct: restricted=isinstance(select_related,dict) is False for both; .select_related(None) is an equally-valid fix, so the projection is NOT spec-too-strong (it deliberately avoids encoding which clearing call gold used).
   - only("pk") → add_immediate_loading REPLACES any prior immediate mask with {pk} → model immediate:=some ["pk"] (matches: model discards input immediate list unconditionally, as does the real code by replacement).
   - relation (related-set identity) unchanged by builder chain → result.relation = qs.relation.
   - raisesFieldError mirrors select_related_descend's raise condition (restricted ∧ select_mask ∧ field∈requested ∧ field∉select_mask). On the always-unrestricted result it is trivially false, matching that the fix makes restricted=False so the FieldError branch cannot fire.
   - F2P scenario evaluated (custom manager select_related("master") + only("pk") deferring master): model yields {relation, unrestricted, some["pk"]}, raisesFieldError=false — exactly the real post-patch outcome (no FieldError).
5. Spec is deterministic (spec_m2mPkQuery_deterministic proven): any result satisfying problem_spec equals implementation output, so a same-spec verifying variant is a positive control, not evidence of weakness.

.iterator() is behavior-irrelevant to the FieldError condition/load mask and correctly unmodeled. No input causes the model to disagree with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold line, no patched file/module path django/core/serializers/python.py|xml_serializer.py in view, changed symbols handle_m2m/m2m_value absent, no narration). same_spec(post,pre)=True (prepatch shares identical spec view). relaxed_leakage=None so strict applies and is clean. Semantic review: problem_statement already publicly names select_related, only, the deferred-vs-traversed FieldError, and the custom-manager scenario. The spec view uses only those public concepts. The postcondition pins the abstract required end-state (selectRel=unrestricted, immediate=some ["pk"], raisesFieldError result=false) — the legitimate content of a faithful spec, not the gold edit. Critically the SelectRel type collapses the two non-dict select_related values (no-arg True vs select_related(None) False) into one 'unrestricted' constructor, so the spec deliberately does NOT encode WHICH clearing API gold used; select_related(None) equally satisfies. No mention of the queryset_iterator fix site, serializer files, or the verbatim gold API insertion; comments describe behavior not the edit. The specific gold fix (insert no-arg .select_related() before .only("pk")) is not disclosed beyond the public problem_statement (it lives in hints_text only).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

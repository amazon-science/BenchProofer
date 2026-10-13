# P2 adversarial audit — django__django-14672

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,12 +60,19 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Pre-patch bug: a present list stays a list (hlist) rather than being
+canonicalised to a tuple. -/
+def rawTF : FieldSeq → HVal
+  | .absent     => HVal.hnone
+  | .astuple xs => HVal.htuple (xs.map HVal.hstr)
+  | .aslist  xs => HVal.hlist  (xs.map HVal.hstr)
+
 def implementation_m2mIdentity
     (base : List HVal) (through : HVal)
     (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
   let mut acc : List HVal := base
   acc := acc ++ [through]
-  acc := acc ++ [canonTF throughFields]
+  acc := acc ++ [rawTF throughFields]
   acc := acc ++ [dbConstraint]
   return acc
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,14 +60,17 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Partial-domain: canonicalises tuples correctly but mishandles the list case
+by reversing the field-name order. -/
+def canonTF2 : FieldSeq → HVal
+  | .absent     => HVal.hnone
+  | .astuple xs => HVal.htuple (xs.map HVal.hstr)
+  | .aslist  xs => HVal.htuple (xs.reverse.map HVal.hstr)
+
 def implementation_m2mIdentity
     (base : List HVal) (through : HVal)
-    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
-  let mut acc : List HVal := base
-  acc := acc ++ [through]
-  acc := acc ++ [canonTF throughFields]
-  acc := acc ++ [dbConstraint]
-  return acc
+    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal :=
+  base ++ [through, canonTF2 throughFields, dbConstraint]
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,14 +60,17 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Boundary bug: an empty present sequence is treated as absent (hnone)
+instead of the empty tuple. -/
+def canonTF3 : FieldSeq → HVal
+  | .absent     => HVal.hnone
+  | .astuple xs => if xs.isEmpty then HVal.hnone else HVal.htuple (xs.map HVal.hstr)
+  | .aslist  xs => if xs.isEmpty then HVal.hnone else HVal.htuple (xs.map HVal.hstr)
+
 def implementation_m2mIdentity
     (base : List HVal) (through : HVal)
-    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
-  let mut acc : List HVal := base
-  acc := acc ++ [through]
-  acc := acc ++ [canonTF throughFields]
-  acc := acc ++ [dbConstraint]
-  return acc
+    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal :=
+  base ++ [through, canonTF3 throughFields, dbConstraint]
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,13 +60,15 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Control-flow bug: the through model and db_constraint flag are emitted in
+the wrong order. -/
 def implementation_m2mIdentity
     (base : List HVal) (through : HVal)
     (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
   let mut acc : List HVal := base
+  acc := acc ++ [dbConstraint]
+  acc := acc ++ [canonTF throughFields]
   acc := acc ++ [through]
-  acc := acc ++ [canonTF throughFields]
-  acc := acc ++ [dbConstraint]
   return acc
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,14 +60,11 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Ungrounded oracle echo: returns the specification RHS verbatim. -/
 def implementation_m2mIdentity
     (base : List HVal) (through : HVal)
-    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
-  let mut acc : List HVal := base
-  acc := acc ++ [through]
-  acc := acc ++ [canonTF throughFields]
-  acc := acc ++ [dbConstraint]
-  return acc
+    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal :=
+  base ++ [through, canonTF throughFields, dbConstraint]
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,14 +60,13 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Rearranged but extensionally-equal: builds the tail then prepends base via
+a fold over the fixed component list. -/
 def implementation_m2mIdentity
     (base : List HVal) (through : HVal)
-    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
-  let mut acc : List HVal := base
-  acc := acc ++ [through]
-  acc := acc ++ [canonTF throughFields]
-  acc := acc ++ [dbConstraint]
-  return acc
+    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal :=
+  let tail := [through] ++ [canonTF throughFields] ++ [dbConstraint]
+  base ++ tail
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,14 +60,11 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Missing-component bug: the field-name sequence slot is dropped from the key. -/
 def implementation_m2mIdentity
     (base : List HVal) (through : HVal)
-    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
-  let mut acc : List HVal := base
-  acc := acc ++ [through]
-  acc := acc ++ [canonTF throughFields]
-  acc := acc ++ [dbConstraint]
-  return acc
+    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal :=
+  base ++ [through, dbConstraint]
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The canonicalisation of a
-- field-name sequence into a hashable form is modeled DEEPLY (the `canonTF` map
-- below) rather than axiomatized, so the standard-library reference routine it
-- mirrors is validated as an A-reference by G-AX. The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A Python value as it appears inside the comparison/identity key of a related
relation. We only model the shapes that occur in the identity key: atomic
strings, the absence of a value, hashable tuples, and (non-hashable) lists. -/
inductive HVal where
  | hstr   (s : String)
  | hnone
  | htuple (xs : List HVal)
  | hlist  (xs : List HVal)
deriving Repr

/-- A field-name sequence parameter. It is either absent, a tuple of names, or a
list of names. Tuples are already in hashable form; a list is not. -/
inductive FieldSeq where
  | absent
  | astuple (xs : List String)
  | aslist  (xs : List String)
deriving Repr

/-- Canonical hashable form of a field-name sequence: an absent value stays
absent, and any present sequence (tuple or list) becomes a tuple of its names.
Mirrors the standard-library routine that normalises an arbitrary value into one
that produces a stable hash for equal values. -/
def canonTF : FieldSeq → HVal
  | .absent     => HVal.hnone
  | .astuple xs => HVal.htuple (xs.map HVal.hstr)
  | .aslist  xs => HVal.htuple (xs.map HVal.hstr)

/-- A value is in hashable form when it is not a list and, recursively at the one
level of nesting we model, contains no list element. -/
def hvalHashable : HVal → Bool
  | .hstr _    => true
  | .hnone     => true
  | .hlist _   => false
  | .htuple xs => xs.all (fun v => match v with | .hlist _ => false | _ => true)
-- pure-end

-- post-conditions-start
/-- The identity key of the relation is the unchanged prefix `base` followed by
the `through` model, then the field-name sequence in CANONICAL HASHABLE form, and
finally the `dbConstraint` flag. The unchanged components are pinned to their
inputs; the field-name slot is exactly the canonical hashable form of the input
sequence, so the whole key is always hashable. -/
def problem_spec_m2mIdentity
    (base : List HVal) (through : HVal)
    (throughFields : FieldSeq) (dbConstraint : HVal)
    (result : List HVal) : Prop :=
  result = base ++ [through, canonTF throughFields, dbConstraint]
-- post-conditions-end

-- impl-start
def implementation_m2mIdentity
    (base : List HVal) (through : HVal)
    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
  let mut acc : List HVal := base
  acc := acc ++ [through]
  acc := acc ++ [canonTF throughFields]
  acc := acc ++ [dbConstraint]
  return acc
-- impl-end

-- proof-start
theorem correct_m2mIdentity :
    ∀ (base : List HVal) (through : HVal)
      (throughFields : FieldSeq) (dbConstraint : HVal),
      problem_spec_m2mIdentity base through throughFields dbConstraint
        (implementation_m2mIdentity base through throughFields dbConstraint) := by
  intro base through throughFields dbConstraint
  unfold problem_spec_m2mIdentity implementation_m2mIdentity
  simp only [Id.run, pure, List.append_assoc, List.cons_append, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a fully-pinned universal exact equality: problem_spec_m2mIdentity ... := result = base ++ [through, canonTF throughFields, dbConstraint]. No weakness clause / disjunction, so any verifying impl must be extensionally equal to gold. Ran 7 same-spec attacks (all same_spec=True), verified concurrently (<=4/batch) via scripts/lean_verify.sh (300s).

WRONG impls (all fail to elaborate, exit=1): atk_1 prepatch bug (rawTF: .aslist stays HVal.hlist not htuple); atk_2 partial-domain (reverses list field-name order); atk_3 boundary (empty present seq collapses to hnone instead of htuple []); atk_4 control-flow-effect (through and dbConstraint positions swapped); atk_7 missing-component (through_fields slot dropped). prepatch reproduced = atk_1 fails as expected (G-DIFF signal).

VERIFYING impls (exit=0, clean axioms [propext] only, no sorryAx): atk_5 ungrounded-oracle echo (returns spec RHS verbatim); atk_6 extensionally-equal rearrangement (builds tail then base++tail). BOTH compute exactly base ++ [through, canonTF throughFields, dbConstraint] = gold value pointwise. Their faithful refined Python patch is therefore the gold patch itself (make_hashable(self.through_fields)); materialized in `patches` and RUN through official harness run_resolve('django__django-14672', gold_patch, timeout=1200) => resolved=True, note='resolved'. So neither verifying attack breaks the spec (verify=>correct holds for the exhibited candidates).

Positive control: gold Solution.lean verifies (exit=0), #print axioms correct_m2mIdentity => [propext] (clean).

A-leg / refinement audit (focus area): refinement.md legs = row1 I, row2 I, row3 A-reference (canonTF <-> make_hashable), row4 I, row5 I; no A-consumed, no kind-3 (changed-inexpressible). A-reference correspondence VALIDATED: ran axiom_check.py (G-AX) => 'G-AX OK: canonTF == make_hashable on all through_fields probes (seed=14672, 50009 cases)', exit=0. canonTF maps both .astuple and .aslist to HVal.htuple, matching make_hashable (tuple already hashable -> returned unchanged; list -> tuple(map(make_hashable,.))) over the None|tuple[str]|list[str] domain the fix actually feeds. Domain restriction is sound (make_hashable is general but only ever receives self.through_fields).

Conclusion: SOUND. >=5 distinct attacks run; every closing-clean-axiom candidate has a materialized faithful patch that RESOLVES under the harness. No verify=>correct violation found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The canonicalisation of a
-- field-name sequence into a hashable form is modeled DEEPLY (the `canonTF` map
-- below) rather than axiomatized, so the standard-library reference routine it
-- mirrors is validated as an A-reference by G-AX. The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A Python value as it appears inside the comparison/identity key of a related
relation. We only model the shapes that occur in the identity key: atomic
strings, the absence of a value, hashable tuples, and (non-hashable) lists. -/
inductive HVal where
  | hstr   (s : String)
  | hnone
  | htuple (xs : List HVal)
  | hlist  (xs : List HVal)
deriving Repr

/-- A field-name sequence parameter. It is either absent, a tuple of names, or a
list of names. Tuples are already in hashable form; a list is not. -/
inductive FieldSeq where
  | absent
  | astuple (xs : List String)
  | aslist  (xs : List String)
deriving Repr

/-- Canonical hashable form of a field-name sequence: an absent value stays
absent, and any present sequence (tuple or list) becomes a tuple of its names.
Mirrors the standard-library routine that normalises an arbitrary value into one
that produces a stable hash for equal values. -/
def canonTF : FieldSeq → HVal
  | .absent     => HVal.hnone
  | .astuple xs => HVal.htuple (xs.map HVal.hstr)
  | .aslist  xs => HVal.htuple (xs.map HVal.hstr)

/-- A value is in hashable form when it is not a list and, recursively at the one
level of nesting we model, contains no list element. -/
def hvalHashable : HVal → Bool
  | .hstr _    => true
  | .hnone     => true
  | .hlist _   => false
  | .htuple xs => xs.all (fun v => match v with | .hlist _ => false | _ => true)
-- pure-end

-- post-conditions-start
/-- The identity key of the relation is the unchanged prefix `base` followed by
the `through` model, then the field-name sequence in CANONICAL HASHABLE form, and
finally the `dbConstraint` flag. The unchanged components are pinned to their
inputs; the field-name slot is exactly the canonical hashable form of the input
sequence, so the whole key is always hashable. -/
def problem_spec_m2mIdentity
    (base : List HVal) (through : HVal)
    (throughFields : FieldSeq) (dbConstraint : HVal)
    (result : List HVal) : Prop :=
  result = base ++ [through, canonTF throughFields, dbConstraint]
-- post-conditions-end

-- impl-start
def implementation_m2mIdentity
    (base : List HVal) (through : HVal)
    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do
  let mut acc : List HVal := base
  acc := acc ++ [through]
  acc := acc ++ [canonTF throughFields]
  acc := acc ++ [dbConstraint]
  return acc
-- impl-end

-- proof-start
theorem correct_m2mIdentity :
    ∀ (base : List HVal) (through : HVal)
      (throughFields : FieldSeq) (dbConstraint : HVal),
      problem_spec_m2mIdentity base through throughFields dbConstraint
        (implementation_m2mIdentity base through throughFields dbConstraint) := by
  intro base through throughFields dbConstraint
  unfold problem_spec_m2mIdentity implementation_m2mIdentity
  simp only [Id.run, pure, List.append_assoc, List.cons_append, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a fully-pinned universal exact equality: problem_spec_m2mIdentity ... := result = base ++ [through, canonTF throughFields, dbConstraint]. No weakness clause / disjunction, so any verifying impl must be extensionally equal to gold. Ran 7 same-spec attacks (all same_spec=True), verified concurrently (<=4/batch) via scripts/lean_verify.sh (300s).

WRONG impls (all fail to elaborate, exit=1): atk_1 prepatch bug (rawTF: .aslist stays HVal.hlist not htuple); atk_2 partial-domain (reverses list field-name order); atk_3 boundary (empty present seq collapses to hnone instead of htuple []); atk_4 control-flow-effect (through and dbConstraint positions swapped); atk_7 missing-component (through_fields slot dropped). prepatch reproduced = atk_1 fails as expected (G-DIFF signal).

VERIFYING impls (exit=0, clean axioms [propext] only, no sorryAx): atk_5 ungrounded-oracle echo (returns spec RHS verbatim); atk_6 extensionally-equal rearrangement (builds tail then base++tail). BOTH compute exactly base ++ [through, canonTF throughFields, dbConstraint] = gold value pointwise. Their faithful refined Python patch is therefore the gold patch itself (make_hashable(self.through_fields)); materialized in `patches` and RUN through official harness run_resolve('django__django-14672', gold_patch, timeout=1200) => resolved=True, note='resolved'. So neither verifying attack breaks the spec (verify=>correct holds for the exhibited candidates).

Positive control: gold Solution.lean verifies (exit=0), #print axioms correct_m2mIdentity => [propext] (clean).

A-leg / refinement audit (focus area): refinement.md legs = row1 I, row2 I, row3 A-reference (canonTF <-> make_hashable), row4 I, row5 I; no A-consumed, no kind-3 (changed-inexpressible). A-reference correspondence VALIDATED: ran axiom_check.py (G-AX) => 'G-AX OK: canonTF == make_hashable on all through_fields probes (seed=14672, 50009 cases)', exit=0. canonTF maps both .astuple and .aslist to HVal.htuple, matching make_hashable (tuple already hashable -> returned unchanged; list -> tuple(map(make_hashable,.))) over the None|tuple[str]|list[str] domain the fix actually feeds. Domain restriction is sound (make_hashable is general but only ever receives self.through_fields).

Conclusion: SOUND. >=5 distinct attacks run; every closing-clean-axiom candidate has a materialized faithful patch that RESOLVES under the harness. No verify=>correct violation found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function is ManyToManyRel.identity post-patch (django/db/models/fields/reverse_related.py, base_commit 00ea883): super().identity + (self.through, make_hashable(self.through_fields), self.db_constraint). Spec: result = base ++ [through, canonTF throughFields, dbConstraint]. canonTF matches the real callee make_hashable exactly on the through_fields domain (None|tuple[str]|list[str]): absent->hnone (make_hashable(None)=None); astuple->htuple(map hstr) (already-hashable tuple returned unchanged); aslist->htuple(map hstr) (unhashable list -> tuple(map(make_hashable,...))). Both list and tuple inputs canonicalise to the same htuple, which is precisely the observable the fix/F2P tests pin (equal, hashable identity keys). Boundary cases []/() both -> htuple []. base/through/dbConstraint carried verbatim, matching super().identity + (...). Nested-list elements cannot occur in the real through_fields domain (field-name strings only), so the model's shape restriction is a legitimate G-AX/G-CONF domain restriction, not drift. VERIFICATION: lean_verify.sh exit 0; #print axioms correct_m2mIdentity => [propext] only (no sorryAx, proof genuine); same_spec(Solution, Solution_prepatch, LeanBackend.language)=True (byte-identical frozen spec, legitimate same-spec/different-impl pair). No input where the spec disagrees with the real repo behavior. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (swebench_unified.leakage.screen over the lean spec view) PASSES: no diff markers, no gold-patch line reproduced, no patched file path/module, no patched-symbol echo (changed symbols set is empty since the gold hunk touches no def/class name), no narration. same_spec(Solution.lean, Solution_prepatch.lean) = True — spec regions byte-identical prepatch/postpatch, so the discriminator lives only in the impl/proof (elided from the view). Semantic G-PANEL-3 judgment: the gold edit is wrapping self.through_fields in make_hashable(...). This is ALREADY fully public in problem_statement: title 'Missing call `make_hashable` on `through_fields` in `ManyToManyRel`', the TypeError: unhashable type: 'list' trace, and closing 'Solution: Add missing make_hashable call on self.through_fields in ManyToManyRel.' The spec view models the field-name slot as 'CANONICAL HASHABLE form' (canonTF) — a faithful abstraction of the publicly-stated make_hashable behavior, not a disclosure beyond the problem_statement. No file path, no repo symbol (identity/ManyToManyRel), and no diff specifics appear in the view. Nothing leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

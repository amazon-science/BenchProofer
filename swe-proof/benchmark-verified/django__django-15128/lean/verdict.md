# P2 adversarial audit — django__django-15128

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so no faithful patch could be materialized/resolved. The postcondition is a full closed-form list equality (result = aliases.zipIdx.filterMap (fun p => if isReserved reserved p.1 then none else some (p.1, freshName pfx p.2))) grounded entirely in the inputs, leaving zero behavioral wiggle room. Each of the 7 wrong impls was additionally PROVEN to violate the spec via native_decide on a discriminating input (ref_1..7 all exit 0), e.g. contiguous renumbering (atk_2) yields (7,"T0") on reserved=[5],aliases=[5,7] where the spec demands (7,"T1").
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,8 +64,6 @@
     List (Nat × String) := Id.run do
   let mut changeMap : List (Nat × String) := []
   for p in aliases.zipIdx do
-    if isReserved reserved p.1 then
-      continue
     changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
   return changeMap
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,13 +61,9 @@
 -- impl-start
 def implementation_renumberAliases
     (pfx : String) (reserved : List Nat) (aliases : List Nat) :
-    List (Nat × String) := Id.run do
-  let mut changeMap : List (Nat × String) := []
-  for p in aliases.zipIdx do
-    if isReserved reserved p.1 then
-      continue
-    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
-  return changeMap
+    List (Nat × String) :=
+  (aliases.filter (fun a => ! isReserved reserved a)).zipIdx.map
+    (fun p => (p.1, freshName pfx p.2))
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
   for p in aliases.zipIdx do
     if isReserved reserved p.1 then
       continue
-    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
+    changeMap := changeMap ++ [(p.1, freshName pfx (p.2 + 1))]
   return changeMap
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
   for p in aliases.zipIdx do
     if isReserved reserved p.1 then
       continue
-    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
+    changeMap := [(p.1, freshName pfx p.2)] ++ changeMap
   return changeMap
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,12 +62,13 @@
 def implementation_renumberAliases
     (pfx : String) (reserved : List Nat) (aliases : List Nat) :
     List (Nat × String) := Id.run do
-  let mut changeMap : List (Nat × String) := []
-  for p in aliases.zipIdx do
-    if isReserved reserved p.1 then
-      continue
-    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
-  return changeMap
+  if reserved.isEmpty then
+    let mut changeMap : List (Nat × String) := []
+    for p in aliases.zipIdx do
+      changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
+    return changeMap
+  else
+    return []
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
     List (Nat × String) := Id.run do
   let mut changeMap : List (Nat × String) := []
   for p in aliases.zipIdx do
-    if isReserved reserved p.1 then
+    if ! isReserved reserved p.1 then
       continue
     changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
   return changeMap
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
   for p in aliases.zipIdx do
     if isReserved reserved p.1 then
       continue
-    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
+    changeMap := changeMap ++ [(p.1, freshName pfx p.1)]
   return changeMap
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a renaming plan that gives each of an ordered collection of identifiers
a fresh, sequentially numbered name — while leaving a designated set of
identifiers untouched.

We are given an ordered list of current identifiers, a fresh name prefix, and a
set of identifiers that must be preserved (kept under their current name). The
renaming plan is an ordered association list pairing each *non-preserved*
identifier with a new name built from the prefix and that identifier's position.

The numbering is positional over the WHOLE collection: each identifier's number
is its 0-based index in the original ordered collection, regardless of whether
some earlier identifiers were preserved and therefore omitted from the plan. So
preserving an identifier removes its entry from the plan but does not renumber
the identifiers that follow it.

A preserved identifier never appears as a key in the plan, so the plan never
asks to rename it; every other identifier appears exactly once, mapped to its
positional fresh name.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The renaming
-- plan is a pure function of the ordered identifiers, the preserved set, and the
-- prefix; the downstream step that applies the plan is not part of the modeled
-- value, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Whether an identifier is preserved (left untouched, hence excluded from the
renaming plan). Modeled by membership in the reserved list. -/
def isReserved (reserved : List Nat) (a : Nat) : Bool :=
  reserved.contains a

/-- The fresh name an identifier receives: the prefix followed by the decimal
form of the identifier's 0-based position in the original ordered collection. -/
def freshName (pfx : String) (pos : Nat) : String :=
  pfx ++ toString pos
-- pure-end

-- post-conditions-start
/-- The renaming plan lists, in original order, the `(identifier, fresh name)`
entry of exactly the non-preserved identifiers. Each kept identifier's fresh
name is built from the prefix and the identifier's index in the FULL ordered
collection (preserved identifiers still consume their index). Every component is
pinned: the keys are precisely the non-preserved identifiers in order, and each
value is its positional fresh name — nothing is invented, reordered, or
renumbered. -/
def problem_spec_renumberAliases
    (pfx : String) (reserved : List Nat) (aliases : List Nat)
    (result : List (Nat × String)) : Prop :=
  result =
    (aliases.zipIdx).filterMap (fun p =>
      if isReserved reserved p.1 then none
      else some (p.1, freshName pfx p.2))
-- post-conditions-end

-- impl-start
def implementation_renumberAliases
    (pfx : String) (reserved : List Nat) (aliases : List Nat) :
    List (Nat × String) := Id.run do
  let mut changeMap : List (Nat × String) := []
  for p in aliases.zipIdx do
    if isReserved reserved p.1 then
      continue
    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
  return changeMap
-- impl-end

-- proof-start
/-- The cleaned `forIn` accumulation loop over the indexed aliases equals
prepending the running accumulator to the `filterMap` of the remaining items.
Proven by induction on the list, generalized over the accumulator (Route B). -/
theorem helper_renum (xs : List (Nat × Nat)) (pfx : String) (reserved : List Nat)
    (init : List (Nat × String)) :
    (Id.run (forIn xs init (fun p r =>
        (if isReserved reserved p.1 = true then ForInStep.yield r
         else ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]) : Id (ForInStep (List (Nat × String))))))) =
      init ++ xs.filterMap (fun p =>
        if isReserved reserved p.1 = true then none else some (p.1, freshName pfx p.2)) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.filterMap_nil, List.append_nil, Id.run]; rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.filterMap_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : isReserved reserved a.1 = true
    · simp only [if_pos h, ih]
    · simp only [if_neg h, ih, List.append_assoc, List.cons_append, List.nil_append]

theorem correct_renumberAliases :
    ∀ (pfx : String) (reserved : List Nat) (aliases : List Nat),
      problem_spec_renumberAliases pfx reserved aliases
        (implementation_renumberAliases pfx reserved aliases) := by
  intro pfx reserved aliases
  unfold problem_spec_renumberAliases implementation_renumberAliases
  simp only [Id.run]
  have hbody :
      (forIn aliases.zipIdx ([] : List (Nat × String)) fun p r =>
          if isReserved reserved p.1 = true then pure (ForInStep.yield r)
          else do
            pure PUnit.unit
            pure PUnit.unit
            pure (ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]))) =
      (forIn aliases.zipIdx ([] : List (Nat × String)) fun p r =>
          (if isReserved reserved p.1 = true then ForInStep.yield r
           else ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]) : Id (ForInStep (List (Nat × String))))) := rfl
  rw [hbody]
  have := helper_renum aliases.zipIdx pfx reserved []
  simp only [Id.run] at this
  rw [this, List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: worked entirely. Built 7 DISTINCT same-spec wrong impls by editing ONLY the impl region (axioms/pure/pre/post byte-identical): atk_1 prepatch bug (no reserved filter, emits every alias), atk_2 contiguous renumbering (filter-then-zipIdx, pos among survivors), atk_3 boundary off-by-one (pos+1), atk_4 control-flow-effect (prepend->order reversed), atk_5 partial-domain (correct only when reserved empty else []), atk_6 inverted predicate (keep reserved/drop others), atk_7 ungrounded-echo (uses alias p.1 as position instead of index p.2). same_spec=True for all 7 (verified via swebench_unified.markers.same_spec + get_backend('lean')).

### COMMANDS (run; verifications launched concurrently <=4 at a time as background jobs):
  bash scripts/lean_verify.sh <D>/atk_N.lean
RESULTS: atk_1..7 ALL exit 1 (gold proof fails to close; error is 'rewrite failed / simp made no progress' — genuine proof error, not syntax). No wrong impl verifies with clean axioms => NO patch materialization/resolve needed (step 2 vacuous; nothing to run through run_resolve).

POSITIVE CONTROL: pos_control.lean (exact gold impl) exit 0; pos_axioms.lean with '#print axioms correct_renumberAliases' exit 0 => [propext, Quot.sound], no sorryAx (clean).

MECHANICAL TOTALITY PROOF: for each wrong impl I materialized ref_N.lean = spec header + that impl + 'theorem wrong_violates_N : ¬ problem_spec_renumberAliases <input> (implementation_renumberAliases <input>) := by unfold ...; native_decide'. ref_1..7 ALL exit 0 — each wrong impl is machine-proven to violate the frozen spec on a discriminating input. So the spec admits ONLY the gold value; no custom proof (not merely the carried gold proof) could ever close any wrong impl. verify => correct holds.

prepatch_reproduced=true: atk_1 is the prepatch bug (Solution_prepatch.lean impl) and its carried gold proof fails to close (exit 1), reproducing the buggy-behavior rejection.

REFINEMENT AUDIT (refinement.md + mapping.md): all 5 legs are R/I, NO A-legs. axioms region is intentionally empty (documented: the renaming plan is a pure function of aliases/reserved/pfx; downstream change_aliases is unchanged by the patch and not part of the modeled value — correct per SPEC_GUIDE §3, a deeply-modeled changed decision is not axiomatized). Legs: #1 accumulator [] <-> {} (R, lossless dict<->ordered assoc list, distinct keys), #2 aliases.zipIdx <-> enumerate(self.alias_map) (R, position over FULL enumeration so reserved alias still consumes its index), #3 if isReserved...continue <-> if alias not in exclude (I, the fixed op), #4 changeMap++[(p.1,freshName pfx p.2)] <-> alias:'%s%d'%(prefix,pos) (R), #5 return changeMap <-> dict handed to change_aliases (R). No kind-3 leg. Correspondence holds; the modeled value IS exactly the change map the patch alters. Since there are no A-legs, the deep-model/callee-reference concern (the focus of this A-leg review) is vacuously satisfied — verified by reading axioms region byte-identical and empty across Solution.lean/atk files.

VERDICT: SOUND. >=5 (7) distinct attacks run and verified; none verifies with a clean-axiom closing proof, so verify=>correct is not falsified. Positive control verifies clean. No resolve run was needed because no attack produced a verifying artifact requiring a patch.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so no faithful patch could be materialized/resolved. The postcondition is a full closed-form list equality (result = aliases.zipIdx.filterMap (fun p => if isReserved reserved p.1 then none else some (p.1, freshName pfx p.2))) grounded entirely in the inputs, leaving zero behavioral wiggle room. Each of the 7 wrong impls was additionally PROVEN to violate the spec via native_decide on a discriminating input (ref_1..7 all exit 0), e.g. contiguous renumbering (atk_2) yields (7,"T0") on reserved=[5],aliases=[5,7] where the spec demands (7,"T1").
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a renaming plan that gives each of an ordered collection of identifiers
a fresh, sequentially numbered name — while leaving a designated set of
identifiers untouched.

We are given an ordered list of current identifiers, a fresh name prefix, and a
set of identifiers that must be preserved (kept under their current name). The
renaming plan is an ordered association list pairing each *non-preserved*
identifier with a new name built from the prefix and that identifier's position.

The numbering is positional over the WHOLE collection: each identifier's number
is its 0-based index in the original ordered collection, regardless of whether
some earlier identifiers were preserved and therefore omitted from the plan. So
preserving an identifier removes its entry from the plan but does not renumber
the identifiers that follow it.

A preserved identifier never appears as a key in the plan, so the plan never
asks to rename it; every other identifier appears exactly once, mapped to its
positional fresh name.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The renaming
-- plan is a pure function of the ordered identifiers, the preserved set, and the
-- prefix; the downstream step that applies the plan is not part of the modeled
-- value, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Whether an identifier is preserved (left untouched, hence excluded from the
renaming plan). Modeled by membership in the reserved list. -/
def isReserved (reserved : List Nat) (a : Nat) : Bool :=
  reserved.contains a

/-- The fresh name an identifier receives: the prefix followed by the decimal
form of the identifier's 0-based position in the original ordered collection. -/
def freshName (pfx : String) (pos : Nat) : String :=
  pfx ++ toString pos
-- pure-end

-- post-conditions-start
/-- The renaming plan lists, in original order, the `(identifier, fresh name)`
entry of exactly the non-preserved identifiers. Each kept identifier's fresh
name is built from the prefix and the identifier's index in the FULL ordered
collection (preserved identifiers still consume their index). Every component is
pinned: the keys are precisely the non-preserved identifiers in order, and each
value is its positional fresh name — nothing is invented, reordered, or
renumbered. -/
def problem_spec_renumberAliases
    (pfx : String) (reserved : List Nat) (aliases : List Nat)
    (result : List (Nat × String)) : Prop :=
  result =
    (aliases.zipIdx).filterMap (fun p =>
      if isReserved reserved p.1 then none
      else some (p.1, freshName pfx p.2))
-- post-conditions-end

-- impl-start
def implementation_renumberAliases
    (pfx : String) (reserved : List Nat) (aliases : List Nat) :
    List (Nat × String) := Id.run do
  let mut changeMap : List (Nat × String) := []
  for p in aliases.zipIdx do
    if isReserved reserved p.1 then
      continue
    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
  return changeMap
-- impl-end

-- proof-start
/-- The cleaned `forIn` accumulation loop over the indexed aliases equals
prepending the running accumulator to the `filterMap` of the remaining items.
Proven by induction on the list, generalized over the accumulator (Route B). -/
theorem helper_renum (xs : List (Nat × Nat)) (pfx : String) (reserved : List Nat)
    (init : List (Nat × String)) :
    (Id.run (forIn xs init (fun p r =>
        (if isReserved reserved p.1 = true then ForInStep.yield r
         else ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]) : Id (ForInStep (List (Nat × String))))))) =
      init ++ xs.filterMap (fun p =>
        if isReserved reserved p.1 = true then none else some (p.1, freshName pfx p.2)) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.filterMap_nil, List.append_nil, Id.run]; rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.filterMap_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : isReserved reserved a.1 = true
    · simp only [if_pos h, ih]
    · simp only [if_neg h, ih, List.append_assoc, List.cons_append, List.nil_append]

theorem correct_renumberAliases :
    ∀ (pfx : String) (reserved : List Nat) (aliases : List Nat),
      problem_spec_renumberAliases pfx reserved aliases
        (implementation_renumberAliases pfx reserved aliases) := by
  intro pfx reserved aliases
  unfold problem_spec_renumberAliases implementation_renumberAliases
  simp only [Id.run]
  have hbody :
      (forIn aliases.zipIdx ([] : List (Nat × String)) fun p r =>
          if isReserved reserved p.1 = true then pure (ForInStep.yield r)
          else do
            pure PUnit.unit
            pure PUnit.unit
            pure (ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]))) =
      (forIn aliases.zipIdx ([] : List (Nat × String)) fun p r =>
          (if isReserved reserved p.1 = true then ForInStep.yield r
           else ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]) : Id (ForInStep (List (Nat × String))))) := rfl
  rw [hbody]
  have := helper_renum aliases.zipIdx pfx reserved []
  simp only [Id.run] at this
  rw [this, List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: worked entirely. Built 7 DISTINCT same-spec wrong impls by editing ONLY the impl region (axioms/pure/pre/post byte-identical): atk_1 prepatch bug (no reserved filter, emits every alias), atk_2 contiguous renumbering (filter-then-zipIdx, pos among survivors), atk_3 boundary off-by-one (pos+1), atk_4 control-flow-effect (prepend->order reversed), atk_5 partial-domain (correct only when reserved empty else []), atk_6 inverted predicate (keep reserved/drop others), atk_7 ungrounded-echo (uses alias p.1 as position instead of index p.2). same_spec=True for all 7 (verified via swebench_unified.markers.same_spec + get_backend('lean')).

### COMMANDS (run; verifications launched concurrently <=4 at a time as background jobs):
  bash scripts/lean_verify.sh <D>/atk_N.lean
RESULTS: atk_1..7 ALL exit 1 (gold proof fails to close; error is 'rewrite failed / simp made no progress' — genuine proof error, not syntax). No wrong impl verifies with clean axioms => NO patch materialization/resolve needed (step 2 vacuous; nothing to run through run_resolve).

POSITIVE CONTROL: pos_control.lean (exact gold impl) exit 0; pos_axioms.lean with '#print axioms correct_renumberAliases' exit 0 => [propext, Quot.sound], no sorryAx (clean).

MECHANICAL TOTALITY PROOF: for each wrong impl I materialized ref_N.lean = spec header + that impl + 'theorem wrong_violates_N : ¬ problem_spec_renumberAliases <input> (implementation_renumberAliases <input>) := by unfold ...; native_decide'. ref_1..7 ALL exit 0 — each wrong impl is machine-proven to violate the frozen spec on a discriminating input. So the spec admits ONLY the gold value; no custom proof (not merely the carried gold proof) could ever close any wrong impl. verify => correct holds.

prepatch_reproduced=true: atk_1 is the prepatch bug (Solution_prepatch.lean impl) and its carried gold proof fails to close (exit 1), reproducing the buggy-behavior rejection.

REFINEMENT AUDIT (refinement.md + mapping.md): all 5 legs are R/I, NO A-legs. axioms region is intentionally empty (documented: the renaming plan is a pure function of aliases/reserved/pfx; downstream change_aliases is unchanged by the patch and not part of the modeled value — correct per SPEC_GUIDE §3, a deeply-modeled changed decision is not axiomatized). Legs: #1 accumulator [] <-> {} (R, lossless dict<->ordered assoc list, distinct keys), #2 aliases.zipIdx <-> enumerate(self.alias_map) (R, position over FULL enumeration so reserved alias still consumes its index), #3 if isReserved...continue <-> if alias not in exclude (I, the fixed op), #4 changeMap++[(p.1,freshName pfx p.2)] <-> alias:'%s%d'%(prefix,pos) (R), #5 return changeMap <-> dict handed to change_aliases (R). No kind-3 leg. Correspondence holds; the modeled value IS exactly the change map the patch alters. Since there are no A-legs, the deep-model/callee-reference concern (the focus of this A-leg review) is vacuously satisfied — verified by reading axioms region byte-identical and empty across Solution.lean/atk files.

VERDICT: SOUND. >=5 (7) distinct attacks run and verified; none verifies with a clean-axiom closing proof, so verify=>correct is not falsified. Positive control verifies clean. No resolve run was needed because no attack produced a verifying artifact requiring a patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) attack found no divergence. Solution.lean compiles clean (lean_verify.sh exit 0); #print axioms correct_renumberAliases = [propext, Quot.sound] (no sorryAx, real proof). same_spec(Solution, Solution_prepatch) = True with lean backend (spec region byte-identical). The worktree at base_commit 859a87d873 already carries the post-patch bump_prefix comprehension `{alias: '%s%d' % (self.alias_prefix, pos) for pos, alias in enumerate(self.alias_map) if alias not in exclude}`. The Lean spec models this as aliases.zipIdx.filterMap (drop reserved, else (alias, pfx++toString pos)). Verified equivalences: (a) positional number is index over the FULL enumeration incl. reserved -> zipIdx exact; (b) `alias not in exclude` -> reserved.contains; (c) '%s%d' % (prefix,pos) -> pfx++toString pos identical decimal for Nat>=0; (d) insertion-ordered dict <-> ordered assoc list, lossless because alias_map keys (hence aliases) are distinct. Ran a 500k-input differential test (alias lists len 0-8 distinct, reserved subsets incl empty/None/absent-alias/base-alias, varied uppercase prefixes) against the verbatim Python comprehension: 0 dict-content mismatches AND 0 insertion-order mismatches. Modeling boundary is correct -- the modeled value is precisely the change map the patch alters; downstream change_aliases is unchanged and out of scope. No input where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (hard_failures=[]); spec region byte-identical vs Solution_prepatch.lean (same_spec=True); no relaxed_leakage flag / RELAXED_LEAKAGE.md, recorded status is genuine 'pass'. Spec view is fully domain-abstracted: no django symbols (bump_prefix, change_aliases, combine, exclude, alias_prefix, get_initial_alias), no file/module path, no diff markers, no reproduced gold-patch line, no bug/fix narration. The 'preserved set' / exclude concept and positional-numbering detail are inherent properties of the post-patch function that any faithful spec must express as an abstract mathematical relation (filterMap over zipIdx); they do not reveal the edit location or the patch mechanism, and do not go beyond what specifying the target function requires. No gold-edit reconstruction beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

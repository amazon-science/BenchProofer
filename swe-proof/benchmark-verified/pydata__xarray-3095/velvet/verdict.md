# P2 adversarial audit — pydata__xarray-3095

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_1.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's three postconditions (out.values=self.values, out.storedDtype=self.storedDtype, out.inferredDtype=self.inferredDtype) fully determine the output record for both `adapterCopy` and `indexVariableCopy`, so every verifying impl is extensionally identical on the modeled observables. The only unmodeled dimension is the PHYSICAL deep-copy behaviour (whether the underlying ndarray is duplicated), which four distinct verifying wrong impls (atk_1 always-shallow, atk_6 non-delegating inline shallow, atk_7 let-bound shallow, atk_8 forwards deep=True unconditionally) vary. All four faithful refined patches RESOLVE under the official harness, because the F2P/P2P test test_copy gates its source_ndarray identity assertions behind `if self.cls is Variable:` — the IndexVariable class (whose method the gold patch changes) NEVER asserts physical-copy identity; only element values and dtype are observed, which every verifying impl preserves. Hence verify⇒correct holds for this spec on the hidden tests.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,11 +67,7 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    -- `deep` selects whether the underlying values are physically duplicated;
-    -- either choice yields the same element values, so the resulting carrier is
-    -- the original's values in both cases.
-    let arr := if deep then self.values else self.values
-    return { values := arr, storedDtype := self.storedDtype,
+    return { values := self.values, storedDtype := self.storedDtype,
              inferredDtype := self.inferredDtype }
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,11 +67,7 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    -- `deep` selects whether the underlying values are physically duplicated;
-    -- either choice yields the same element values, so the resulting carrier is
-    -- the original's values in both cases.
-    let arr := if deep then self.values else self.values
-    return { values := arr, storedDtype := self.storedDtype,
+    return { values := self.values, storedDtype := self.inferredDtype,
              inferredDtype := self.inferredDtype }
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,11 +67,7 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    -- `deep` selects whether the underlying values are physically duplicated;
-    -- either choice yields the same element values, so the resulting carrier is
-    -- the original's values in both cases.
-    let arr := if deep then self.values else self.values
-    return { values := arr, storedDtype := self.storedDtype,
+    return { values := self.values, storedDtype := self.storedDtype,
              inferredDtype := self.inferredDtype }
     -- impl-end
 
@@ -95,8 +91,8 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    let data ← adapterCopy self deep
-    return data
+    return { values := self.values, storedDtype := self.inferredDtype,
+             inferredDtype := self.inferredDtype }
     -- impl-end
 
 prove_correct indexVariableCopy by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,11 +67,7 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    -- `deep` selects whether the underlying values are physically duplicated;
-    -- either choice yields the same element values, so the resulting carrier is
-    -- the original's values in both cases.
-    let arr := if deep then self.values else self.values
-    return { values := arr, storedDtype := self.storedDtype,
+    return { values := [], storedDtype := self.storedDtype,
              inferredDtype := self.inferredDtype }
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,7 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    -- `deep` selects whether the underlying values are physically duplicated;
-    -- either choice yields the same element values, so the resulting carrier is
-    -- the original's values in both cases.
-    let arr := if deep then self.values else self.values
+    let arr := if deep then self.values else ([] : List Int)
     return { values := arr, storedDtype := self.storedDtype,
              inferredDtype := self.inferredDtype }
     -- impl-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,11 +67,7 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    -- `deep` selects whether the underlying values are physically duplicated;
-    -- either choice yields the same element values, so the resulting carrier is
-    -- the original's values in both cases.
-    let arr := if deep then self.values else self.values
-    return { values := arr, storedDtype := self.storedDtype,
+    return { values := self.values, storedDtype := self.storedDtype,
              inferredDtype := self.inferredDtype }
     -- impl-end
 
@@ -95,8 +91,8 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    let data ← adapterCopy self deep
-    return data
+    return { values := self.values, storedDtype := self.storedDtype,
+             inferredDtype := self.inferredDtype }
     -- impl-end
 
 prove_correct indexVariableCopy by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,11 +67,9 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    -- `deep` selects whether the underlying values are physically duplicated;
-    -- either choice yields the same element values, so the resulting carrier is
-    -- the original's values in both cases.
-    let arr := if deep then self.values else self.values
-    return { values := arr, storedDtype := self.storedDtype,
+    let vals := self.values
+    let sd := self.storedDtype
+    return { values := vals, storedDtype := sd,
              inferredDtype := self.inferredDtype }
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,11 +67,7 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    -- `deep` selects whether the underlying values are physically duplicated;
-    -- either choice yields the same element values, so the resulting carrier is
-    -- the original's values in both cases.
-    let arr := if deep then self.values else self.values
-    return { values := arr, storedDtype := self.storedDtype,
+    return { values := self.values, storedDtype := self.storedDtype,
              inferredDtype := self.inferredDtype }
     -- impl-end
 
@@ -95,7 +91,7 @@
   ensures out.inferredDtype = self.inferredDtype
   do
     -- impl-start
-    let data ← adapterCopy self deep
+    let data ← adapterCopy self true
     return data
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total-correctness semantics: the real copy is a straight-line construction
   (clone the underlying values, rebuild the wrapper) that always COMPLETES,
   so the spec must also rule out implementations that diverge — under
   partial correctness a non-terminating body would vacuously satisfy every
   postcondition. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The dtype-preserving clone is modeled deeply
--  as a record construction. The fact that an index's underlying array
--  representation may re-derive a DIFFERENT element dtype than the one the
--  wrapper stores — the property that makes preservation observable — is
--  carried as a plain input field (`inferredDtype`) and validated against the
--  real wrapper behaviour by axiom_check.py (G-AX) as an A-reference. Nothing
--  is consumed as an axiom.)
-- axioms-end

-- pure-start
/- A wrapper around a one-dimensional index that records both its element
   values and the precise element dtype it presents.

   `values` are the ordered element identities the index carries.
   `storedDtype` is the precise element dtype the wrapper presents (e.g. a
   fixed-width unicode dtype). `inferredDtype` is the element dtype that would
   be re-derived purely from the wrapper's underlying array representation,
   ignoring the stored dtype; for some kinds of element this re-derived dtype
   DIFFERS from `storedDtype` because the underlying representation cannot carry
   the precise stored dtype (it falls back to a generic object dtype), and for
   others the two agree. The dtype is modeled by its name (a `String`); the
   element values by a `List Int` (their ordered identities). -/
structure IndexAdapter where
  values : List Int
  storedDtype : String
  inferredDtype : String
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Copying an index wrapper returns a fresh wrapper with the SAME element values
   and the SAME stored element dtype as the original. The stored dtype must be
   carried through unchanged — never re-derived from the underlying array
   representation, which for some element kinds would yield a different
   (generic) dtype. The `deep` flag governs only whether the underlying values
   are physically duplicated; it does not affect the observable element values
   or the stored dtype, which are identical for either setting.

   The dtype that would be re-derived from the copy's underlying representation
   (`inferredDtype`) is a property of the element values alone; since the values
   are unchanged, it too is identical to the original's.

   `self` and `deep` are read-only (not `mut`); a fresh wrapper is constructed
   and nothing is mutated (directive 5). -/
method adapterCopy (self : IndexAdapter) (deep : Bool) return (out : IndexAdapter)
  ensures out.values = self.values
  ensures out.storedDtype = self.storedDtype
  ensures out.inferredDtype = self.inferredDtype
  do
    -- impl-start
    -- `deep` selects whether the underlying values are physically duplicated;
    -- either choice yields the same element values, so the resulting carrier is
    -- the original's values in both cases.
    let arr := if deep then self.values else self.values
    return { values := arr, storedDtype := self.storedDtype,
             inferredDtype := self.inferredDtype }
    -- impl-end

prove_correct adapterCopy by
  loom_solve

/- An index-valued variable copies its data by delegating to the wrapper's own
   copy, which preserves the stored element dtype. The result therefore carries
   the same element values and the same stored element dtype as the original,
   for either setting of `deep` — copying never silently changes the element
   dtype of an index.

   As with the wrapper copy, the re-derived (`inferredDtype`) dtype is a
   property of the unchanged element values and is therefore identical too.

   `self` and `deep` are read-only (not `mut`); nothing is mutated
   (directive 5). -/
method indexVariableCopy (self : IndexAdapter) (deep : Bool) return (out : IndexAdapter)
  ensures out.values = self.values
  ensures out.storedDtype = self.storedDtype
  ensures out.inferredDtype = self.inferredDtype
  do
    -- impl-start
    let data ← adapterCopy self deep
    return data
    -- impl-end

prove_correct indexVariableCopy by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 attacks + pos_control confirmed True via swebench_unified.markers.same_spec (velvet lang). Frozen spec byte-identical outside impl regions.

pos_control (correct impl): exit 0 (verifies) — positive control PASSES.
- atk_1 always-shallow adapterCopy (identity, ignores deep): exit 0 VERIFIES.
- atk_2 dtype re-inferred at wrapper (storedDtype:=inferredDtype): exit 1 FAILS (expected).
- atk_3 PREPATCH BUG at indexVariableCopy (storedDtype:=inferredDtype): exit 1 FAILS — unsolved goal `self.inferredDtype = self.storedDtype`, exactly refinement.md §B's claim. PREPATCH REPRODUCED.
- atk_4 wrong values ([]): exit 1 FAILS (expected).
- atk_5 partial-domain (deep=false leg -> []): exit 1 FAILS under total+demonic (expected).
- atk_6 inline non-delegating identity IndexVariable.copy: exit 0 VERIFIES.
- atk_7 let-binding shallow adapterCopy: exit 0 VERIFIES.
- atk_8 IndexVariable.copy forwards deep=True unconditionally: exit 0 VERIFIES.

RESOLVE (swebench_unified.harness.run_resolve, official Docker oracle, timeout 1800, image swebench/sweb.eval.x86_64.pydata_1776_xarray-3095):
- gold baseline: resolved=True completed=True (sanity — harness works, F2P test_copy[str-True] passes).
- atk_1 faithful patch: resolved=True.
- atk_6 faithful patch: resolved=True.
- atk_7 faithful patch: resolved=True.
- atk_8 faithful patch: resolved=True.
All four verifying wrong impls' materialized faithful patches APPLY CLEAN at base_commit (git apply --check) and RESOLVE. No verifying impl breaks the spec.

REFINEMENT.MD AUDIT: every leg is R / I / A-reference; NO A-consumed, NO kind-3. §A (adapterCopy) A1-A4 all R/I; §B (indexVariableCopy) B2 is callee-under-spec (proof consumes adapterCopy_correct, supplied by prove_correct — not a dead axiom); §C confirms empty axioms region; §D A-reference facts EMPIRICALLY GROUNDED against real xarray 0.15.1: re-inference gap holds (<U3 stored str96 -> re-derived object; float64/int64 preserved), patched IndexVariable.copy preserves stored dtype for deep True/False. §E: the one genuinely-changed op (dtype passthrough) is modeled deeply via `storedDtype := self.storedDtype`, not axiomatized.

WHY SOUND (why the tight spec is legitimate, not a false negative on breakage): the postconditions pin all three record fields, so verify⇒the modeled observables (values + stored dtype + inferred dtype) match gold. The tests observe exactly those for IndexVariable (dtype preservation + assert_identical value equality); physical-copy identity is asserted only for the base Variable class, whose method the patch does not touch, so no verifying impl can diverge on a tested observable. verify⇒correct confirmed by 4 executed resolve runs.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_1.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's three postconditions (out.values=self.values, out.storedDtype=self.storedDtype, out.inferredDtype=self.inferredDtype) fully determine the output record for both `adapterCopy` and `indexVariableCopy`, so every verifying impl is extensionally identical on the modeled observables. The only unmodeled dimension is the PHYSICAL deep-copy behaviour (whether the underlying ndarray is duplicated), which four distinct verifying wrong impls (atk_1 always-shallow, atk_6 non-delegating inline shallow, atk_7 let-bound shallow, atk_8 forwards deep=True unconditionally) vary. All four faithful refined patches RESOLVE under the official harness, because the F2P/P2P test test_copy gates its source_ndarray identity assertions behind `if self.cls is Variable:` — the IndexVariable class (whose method the gold patch changes) NEVER asserts physical-copy identity; only element values and dtype are observed, which every verifying impl preserves. Hence verify⇒correct holds for this spec on the hidden tests.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total-correctness semantics: the real copy is a straight-line construction
   (clone the underlying values, rebuild the wrapper) that always COMPLETES,
   so the spec must also rule out implementations that diverge — under
   partial correctness a non-terminating body would vacuously satisfy every
   postcondition. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The dtype-preserving clone is modeled deeply
--  as a record construction. The fact that an index's underlying array
--  representation may re-derive a DIFFERENT element dtype than the one the
--  wrapper stores — the property that makes preservation observable — is
--  carried as a plain input field (`inferredDtype`) and validated against the
--  real wrapper behaviour by axiom_check.py (G-AX) as an A-reference. Nothing
--  is consumed as an axiom.)
-- axioms-end

-- pure-start
/- A wrapper around a one-dimensional index that records both its element
   values and the precise element dtype it presents.

   `values` are the ordered element identities the index carries.
   `storedDtype` is the precise element dtype the wrapper presents (e.g. a
   fixed-width unicode dtype). `inferredDtype` is the element dtype that would
   be re-derived purely from the wrapper's underlying array representation,
   ignoring the stored dtype; for some kinds of element this re-derived dtype
   DIFFERS from `storedDtype` because the underlying representation cannot carry
   the precise stored dtype (it falls back to a generic object dtype), and for
   others the two agree. The dtype is modeled by its name (a `String`); the
   element values by a `List Int` (their ordered identities). -/
structure IndexAdapter where
  values : List Int
  storedDtype : String
  inferredDtype : String
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Copying an index wrapper returns a fresh wrapper with the SAME element values
   and the SAME stored element dtype as the original. The stored dtype must be
   carried through unchanged — never re-derived from the underlying array
   representation, which for some element kinds would yield a different
   (generic) dtype. The `deep` flag governs only whether the underlying values
   are physically duplicated; it does not affect the observable element values
   or the stored dtype, which are identical for either setting.

   The dtype that would be re-derived from the copy's underlying representation
   (`inferredDtype`) is a property of the element values alone; since the values
   are unchanged, it too is identical to the original's.

   `self` and `deep` are read-only (not `mut`); a fresh wrapper is constructed
   and nothing is mutated (directive 5). -/
method adapterCopy (self : IndexAdapter) (deep : Bool) return (out : IndexAdapter)
  ensures out.values = self.values
  ensures out.storedDtype = self.storedDtype
  ensures out.inferredDtype = self.inferredDtype
  do
    -- impl-start
    -- `deep` selects whether the underlying values are physically duplicated;
    -- either choice yields the same element values, so the resulting carrier is
    -- the original's values in both cases.
    let arr := if deep then self.values else self.values
    return { values := arr, storedDtype := self.storedDtype,
             inferredDtype := self.inferredDtype }
    -- impl-end

prove_correct adapterCopy by
  loom_solve

/- An index-valued variable copies its data by delegating to the wrapper's own
   copy, which preserves the stored element dtype. The result therefore carries
   the same element values and the same stored element dtype as the original,
   for either setting of `deep` — copying never silently changes the element
   dtype of an index.

   As with the wrapper copy, the re-derived (`inferredDtype`) dtype is a
   property of the unchanged element values and is therefore identical too.

   `self` and `deep` are read-only (not `mut`); nothing is mutated
   (directive 5). -/
method indexVariableCopy (self : IndexAdapter) (deep : Bool) return (out : IndexAdapter)
  ensures out.values = self.values
  ensures out.storedDtype = self.storedDtype
  ensures out.inferredDtype = self.inferredDtype
  do
    -- impl-start
    let data ← adapterCopy self deep
    return data
    -- impl-end

prove_correct indexVariableCopy by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 attacks + pos_control confirmed True via swebench_unified.markers.same_spec (velvet lang). Frozen spec byte-identical outside impl regions.

pos_control (correct impl): exit 0 (verifies) — positive control PASSES.
- atk_1 always-shallow adapterCopy (identity, ignores deep): exit 0 VERIFIES.
- atk_2 dtype re-inferred at wrapper (storedDtype:=inferredDtype): exit 1 FAILS (expected).
- atk_3 PREPATCH BUG at indexVariableCopy (storedDtype:=inferredDtype): exit 1 FAILS — unsolved goal `self.inferredDtype = self.storedDtype`, exactly refinement.md §B's claim. PREPATCH REPRODUCED.
- atk_4 wrong values ([]): exit 1 FAILS (expected).
- atk_5 partial-domain (deep=false leg -> []): exit 1 FAILS under total+demonic (expected).
- atk_6 inline non-delegating identity IndexVariable.copy: exit 0 VERIFIES.
- atk_7 let-binding shallow adapterCopy: exit 0 VERIFIES.
- atk_8 IndexVariable.copy forwards deep=True unconditionally: exit 0 VERIFIES.

RESOLVE (swebench_unified.harness.run_resolve, official Docker oracle, timeout 1800, image swebench/sweb.eval.x86_64.pydata_1776_xarray-3095):
- gold baseline: resolved=True completed=True (sanity — harness works, F2P test_copy[str-True] passes).
- atk_1 faithful patch: resolved=True.
- atk_6 faithful patch: resolved=True.
- atk_7 faithful patch: resolved=True.
- atk_8 faithful patch: resolved=True.
All four verifying wrong impls' materialized faithful patches APPLY CLEAN at base_commit (git apply --check) and RESOLVE. No verifying impl breaks the spec.

REFINEMENT.MD AUDIT: every leg is R / I / A-reference; NO A-consumed, NO kind-3. §A (adapterCopy) A1-A4 all R/I; §B (indexVariableCopy) B2 is callee-under-spec (proof consumes adapterCopy_correct, supplied by prove_correct — not a dead axiom); §C confirms empty axioms region; §D A-reference facts EMPIRICALLY GROUNDED against real xarray 0.15.1: re-inference gap holds (<U3 stored str96 -> re-derived object; float64/int64 preserved), patched IndexVariable.copy preserves stored dtype for deep True/False. §E: the one genuinely-changed op (dtype passthrough) is modeled deeply via `storedDtype := self.storedDtype`, not axiomatized.

WHY SOUND (why the tight spec is legitimate, not a false negative on breakage): the postconditions pin all three record fields, so verify⇒the modeled observables (values + stored dtype + inferred dtype) match gold. The tests observe exactly those for IndexVariable (dtype preservation + assert_identical value equality); physical-copy identity is asserted only for the base Variable class, whose method the patch does not touch, so no verifying impl can diverge on a tested observable. verify⇒correct confirmed by 4 executed resolve runs.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on pydata__xarray-3095 velvet bundle. Conclusion: FAITHFUL — the modeled functions (adapterCopy / indexVariableCopy) agree with the real repo callees on every tested input; no diverging input found.

### Verification performed
1. Spec region byte-identical: region_hashes computed from Solution.lean via swebench_unified.markers.region_hashes(velvet) MATCH meta.json exactly (axioms/pure/impl/spec_view all True); same_spec(Solution, Solution_prepatch, velvet) == True.
2. Solution.lean elaborates clean (lean_verify exit 0). Solution_prepatch.lean FAILS with unsolved goal `self.inferredDtype = self.storedDtype` at the storedDtype postcondition — the spec genuinely senses the bug (dtype must be carried through, not re-derived). G-DIFF confirmed.
3. Model postconditions (out.values=self.values, out.storedDtype=self.storedDtype, out.inferredDtype=self.inferredDtype, for either deep) checked against the REAL patched repo (worktree):
   - axiom_check.py (G-AX) passes on real repo: re-inference gap sound on 10 arrays (unicode drops to object, float/int preserved), patched copy preserves stored dtype + inferred dtype + values on 20 cases, 4 real IndexVariable cases.
   - conformance_check.py (G-CONF, seed 3095) passes: 200018 PandasIndexAdapter.copy + 200018 IndexVariable.copy cases, 0 disagreements.
   - Independent adversarial probing: datetime64, timedelta64, bool, complex, object, empty-unicode <U1, nan-float, int8, uint64, 100-char string, pandas MultiIndex, PeriodIndex — ZERO divergences in the three modeled observables for deep=True/False. End-to-end IndexVariable.copy over <U3/float64/int64 all preserve dtype and values.
4. Domain check: the only inputs that raise (2-D array, categorical) fail at index CONSTRUCTION (PandasIndexAdapter.__init__), which is outside adapterCopy's domain (it takes an already-built IndexAdapter). These are not copy-time divergences and do not constitute spec drift.

The abstraction (opaque Int element identities; dtype modeled by its .name String) is a sound, non-over-strong model. The postconditions capture exactly the guarantees the real callee provides. No input on which the modeled function disagrees with the real callee was found; the spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (rendered via markers.spec_view) reveals no gold-edit specifics beyond the public problem_statement, which already discloses the full symptom-level fix (copy(deep=True) casts unicode <U* indices to object; a copy-path regression; correct behavior preserves index dtype across deep/shallow copy on Dataset/DataArray). Mechanical G-LEAK screen PASSES (no diff markers, no reproduced gold-patch lines, no patched file path/module, no narration terms). The spec names only abstractions — IndexAdapter, adapterCopy, indexVariableCopy — never the patched repo symbols (PandasIndexAdapter, IndexVariable), the file paths (indexing.py, variable.py), the newly-added copy method, the self._dtype threading, or the delegation refactor. The only patched def/class symbol surfacing lexically is 'copy', which is explicitly public in the problem_statement (copy(deep=True)), so it leaks nothing. Postconditions (out.storedDtype = self.storedDtype, out.values, out.inferredDtype) and docstrings state the REQUIRED behavior (dtype preservation on copy) — exactly the publicly-stated ask — not the code edit; describing discriminating behavior is a spec's job, not disclosure. The abstract 'falls back to a generic object dtype' language mirrors the unicode→object behavior already shown in the problem_statement, not the specific gold change. Discriminator lives entirely in the elided impl: same_spec(Solution, Solution_prepatch)=True (byte-identical spec region), and prepatch differs only in impl, failing out.storedDtype = self.storedDtype. A solver given problem_statement + this spec view cannot reconstruct the gold edit any more than from the problem_statement alone. No leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

# P2 adversarial audit — pytest-dev__pytest-5840

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
The pre-patch bug (Solution_prepatch.lean, reproduced at prepatch.lean) keys/looks up the cache under the SECONDARY representation (k = ⟨loc, KeyRepr.secondary⟩) while consumers probe with probeKey loc = ⟨loc, primary⟩. On a miss it stores the fresh module under a key a later primary probe can never find, so `ensures 3` (regLookup registry (probeKey loc) = some out) is unsatisfiable — verify FAILS (exit 1, unsolved goals), exactly mirroring the real F2P lookup miss (unique_path/LocalPath vs Path.resolve()/PosixPath: == but hash-distinct dict keys). This is the discriminating counterexample; no VERIFYING wrong impl exists.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,13 +120,7 @@
   ensures regLookup registry (probeKey loc) = some out
   do
     -- impl-start
-    let k : Key := probeKey loc
-    let cached := regLookup registry k
-    if cached.isSome then
-      return cached.getD freshMod
-    else
-      registry := registry ++ [(k, freshMod)]
-      return freshMod
+    return freshMod
     -- impl-end
 
 prove_correct registerModule by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,10 +122,10 @@
     -- impl-start
     let k : Key := probeKey loc
     let cached := regLookup registry k
+    registry := registry ++ [(k, freshMod)]
     if cached.isSome then
       return cached.getD freshMod
     else
-      registry := registry ++ [(k, freshMod)]
       return freshMod
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,13 +120,13 @@
   ensures regLookup registry (probeKey loc) = some out
   do
     -- impl-start
-    let k : Key := probeKey loc
+let k : Key := probeKey loc
     let cached := regLookup registry k
     if cached.isSome then
-      return cached.getD freshMod
+      return freshMod
     else
       registry := registry ++ [(k, freshMod)]
-      return freshMod
+      return cached.getD freshMod
     -- impl-end
 
 prove_correct registerModule by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,13 +120,13 @@
   ensures regLookup registry (probeKey loc) = some out
   do
     -- impl-start
-    let k : Key := probeKey loc
+let k : Key := probeKey loc
     let cached := regLookup registry k
     if cached.isSome then
       return cached.getD freshMod
     else
       registry := registry ++ [(k, freshMod)]
-      return freshMod
+      return 0
     -- impl-end
 
 prove_correct registerModule by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,13 +120,9 @@
   ensures regLookup registry (probeKey loc) = some out
   do
     -- impl-start
-    let k : Key := probeKey loc
-    let cached := regLookup registry k
-    if cached.isSome then
-      return cached.getD freshMod
-    else
-      registry := registry ++ [(k, freshMod)]
-      return freshMod
+let k : Key := probeKey loc
+    registry := registry ++ [(k, freshMod)]
+    return freshMod
     -- impl-end
 
 prove_correct registerModule by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,12 +120,12 @@
   ensures regLookup registry (probeKey loc) = some out
   do
     -- impl-start
-    let k : Key := probeKey loc
+let k : Key := probeKey loc
     let cached := regLookup registry k
     if cached.isSome then
       return cached.getD freshMod
     else
-      registry := registry ++ [(k, freshMod)]
+      registry := registry ++ [(⟨loc, KeyRepr.secondary⟩, freshMod)]
       return freshMod
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The routine that produces a module for a path that has
-- not been seen before is an UNCHANGED callee whose result the cache decision
-- never inspects; it is taken as a free input `freshMod`, so the spec makes no
-- behavioural claim about it and holds for every value (an R refinement —
-- mapping.md §3, refinement.md §C). The two ways a path may be turned into a
-- cache key are modeled DEEPLY by `Key`/`KeyRepr` below (a deep-model reference,
-- validated against the real path objects by axiom_check.py / G-AX), NOT behind
-- a consumed axiom.
-- axioms-end

-- pure-start
/- A module identity. Only equality is ever observed (whether two lookups return
   the same loaded module), so a bare identifier suffices. -/
abbrev Module := Nat

/- The two ways the same filesystem location can be turned into a key object for
   the module cache. Both denote the same location, yet as cache keys they are
   NOT interchangeable: a cache keyed under one representation does not answer a
   lookup made under the other. `primary` is the representation every consumer
   computes when it probes the cache; `secondary` is an alternative key object
   for the same location. (On the real system the two key objects compare equal
   as strings but hash differently, so they are distinct dictionary keys — the
   distinction `axiom_check.py`/G-AX validates against the real path objects.) -/
inductive KeyRepr where
  | primary
  | secondary
deriving DecidableEq, Inhabited, Repr

/- A cache key: the filesystem location it denotes together with which key
   representation produced it. Two keys answer the same lookup iff BOTH the
   location and the representation match (structural equality = dictionary-key
   identity, mapping.md §2). -/
structure Key where
  loc : Nat
  rep : KeyRepr
deriving DecidableEq, Inhabited, Repr

/- The key every consumer uses to probe the cache for a location: the `primary`
   representation. The cache is correct exactly when an entry registered for a
   location can be found again under this key. -/
def probeKey (loc : Nat) : Key := ⟨loc, KeyRepr.primary⟩

/- Look a key up in the cache (an association list of key→module). Front-recursive
   so a single unfold is available; returns the module of the first matching
   entry, `none` if the key is absent. Matching is full structural key equality. -/
def regLookup : List (Key × Module) → Key → Option Module
  | [],            _ => none
  | (k, m) :: rest, q => if k = q then some m else regLookup rest q

@[grind, simp] lemma regLookup_nil (q : Key) : regLookup [] q = none := rfl
@[grind, simp] lemma regLookup_cons (k : Key) (m : Module)
    (rest : List (Key × Module)) (q : Key) :
    regLookup ((k, m) :: rest) q = if k = q then some m else regLookup rest q := rfl

/- Appending a fresh entry for a key not yet present makes that key resolve to
   the appended module. The single fact the registration branch needs. -/
/- A present cache entry equals `some` of the value read out of it: the
   cache-hit branch returns exactly the module already stored. -/
@[grind] lemma some_getD_of_isSome {α : Type} (o : Option α) (d : α)
    (h : o.isSome = true) : o = some (o.getD d) := by
  cases o with
  | none => simp at h
  | some v => rfl

@[grind] lemma regLookup_append_fresh (reg : List (Key × Module)) (k : Key) (m : Module)
    (h : regLookup reg k = none) :
    regLookup (reg ++ [(k, m)]) k = some m := by
  induction reg with
  | nil => simp
  | cons hd tl ih =>
    obtain ⟨k', m'⟩ := hd
    rw [List.cons_append, regLookup_cons]
    rw [regLookup_cons] at h
    by_cases hk : k' = k
    · rw [if_pos hk] at h; exact absurd h (by simp)
    · rw [if_neg hk] at h; rw [if_neg hk]; exact ih h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Obtain the module associated with a filesystem location through a shared
   module cache, importing it only once.

   The cache (`registry`) maps a path-derived key to the loaded module. A
   consumer always probes the cache under the location's `primary` key
   (`probeKey loc`). The desired behaviour:

   * if the `primary` key for this location is already registered, return the
     module found there and leave the cache exactly as it was (the import is
     performed at most once per location);
   * otherwise register the freshly produced module under the location's
     `primary` key and return it.

   The post-state is pinned so that, in every case, a subsequent probe of the
   cache under `probeKey loc` finds the returned module — i.e. the entry MUST be
   stored under the same key representation that lookups use, never under a
   merely same-location alternative.

   `loc` and `freshMod` are read-only (not `mut`); `registry` is the only mutated
   state and its post-state is pinned exactly in each branch (directive 5). -/
method registerModule (mut registry : List (Key × Module)) (loc : Nat) (freshMod : Module)
    return (out : Module)
  ensures ∀ m, regLookup registryOld (probeKey loc) = some m →
            (out = m ∧ registry = registryOld)
  ensures regLookup registryOld (probeKey loc) = none →
            (out = freshMod ∧ registry = registryOld ++ [(probeKey loc, freshMod)])
  ensures regLookup registry (probeKey loc) = some out
  do
    -- impl-start
    let k : Key := probeKey loc
    let cached := regLookup registry k
    if cached.isSome then
      return cached.getD freshMod
    else
      registry := registry ++ [(k, freshMod)]
      return freshMod
    -- impl-end

prove_correct registerModule by
  loom_solve
  simp_all [probeKey, regLookup_append_fresh]
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed in fresh scratch, root. same_spec(velvet) == True for ALL 6 attacks + pos_control + prepatch (verified via swebench_unified.markers.same_spec + get_backend('velvet')). Verify cmd per file: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4/batch.

RESULTS (exit codes): pos_control=0 (VERIFIES, correct impl). All 6 same-spec wrong impls FAIL to verify (exit 1, semantic 'unsolved goals', NOT parse errors — confirmed by inspecting .out logs; atk_2 had an initial indentation glitch that was fixed to a clean semantic failure and re-verified). prepatch=1 (fails ensures3, G-DIFF reproduced).
  atk_1: partial-domain — always `return freshMod`, no register (fails ensures2 miss-branch registry + ensures3). exit1.
  atk_2: control-flow-effect — append on EVERY path incl. hit (violates ensures1 registry=registryOld). exit1.
  atk_3: boundary — branches swapped (return freshMod on hit / cached.getD on miss). exit1.
  atk_4: ungrounded-oracle echo — miss-branch returns literal 0 instead of freshMod (violates ensures2/ensures3). exit1.
  atk_5: control-flow — never look up; always append+return freshMod (violates ensures1 on hit). exit1.
  atk_6: wrong-key — miss-branch stores under ⟨loc,secondary⟩ (violates ensures2 post-state + ensures3). exit1.

No VERIFYING wrong impl was found, so the mandatory materialize-faithful-patch + run_resolve step had NO candidates — patches={} (correctly, since resolve is only required for a verifying wrong impl whose patch might fail). No resolve run was needed to reach a verdict; nothing could break verify⇒correct because nothing else verified.

WHY SOUND (spec is fully pinned): the 3 ensures clauses determine out AND the entire registry post-state in BOTH branches (hit: out=m ∧ registry=registryOld; miss: out=freshMod ∧ registry=registryOld++[(probeKey loc,freshMod)]; plus ensures3 probe-finds-result). Every degree of freedom an impl could perturb (returned value, mutation presence/target, key representation) is constrained; my 6 attacks cover the four required families and all are rejected by loom_solve/simp_all.

REFINEMENT.MD LEG AUDIT (A-focus): A1/A2=R; A3=A-reference+I (Key/KeyRepr deep model of the changed key-construction — validated by axiom_check.py/G-AX); A4=I; A5=I+R; §C freshMod=R (free input, correctly NOT a consumed axiom — avoids dead-axiom over-claim); §D asserts no kind-3 and no consumed axioms (axioms region empty). The sole A-reference's correspondence to the real callees holds: axiom_check.py reconstructs unique_path VERBATIM from pre-patch pathlib.py, builds real primary=Path(str(p)).resolve() and secondary=unique_path(p) on 10 boundary paths (incl. #5819 Foo/, #5792 mixed-case) + 3000 seeded(5840) fuzz paths, and asserts prim==sec (value-equal) yet prim NOT in {sec:...} and hash(prim)!=hash(sec) (distinct dict keys) — exactly the model's ⟨loc,primary⟩≠⟨loc,secondary⟩ and regLookup[(⟨loc,secondary⟩,m)](probeKey loc)=none. Model↔patch correspondence (mapping.md §1/§2/§3) is faithful. No kind-3 leg.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
The pre-patch bug (Solution_prepatch.lean, reproduced at prepatch.lean) keys/looks up the cache under the SECONDARY representation (k = ⟨loc, KeyRepr.secondary⟩) while consumers probe with probeKey loc = ⟨loc, primary⟩. On a miss it stores the fresh module under a key a later primary probe can never find, so `ensures 3` (regLookup registry (probeKey loc) = some out) is unsatisfiable — verify FAILS (exit 1, unsolved goals), exactly mirroring the real F2P lookup miss (unique_path/LocalPath vs Path.resolve()/PosixPath: == but hash-distinct dict keys). This is the discriminating counterexample; no VERIFYING wrong impl exists.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The routine that produces a module for a path that has
-- not been seen before is an UNCHANGED callee whose result the cache decision
-- never inspects; it is taken as a free input `freshMod`, so the spec makes no
-- behavioural claim about it and holds for every value (an R refinement —
-- mapping.md §3, refinement.md §C). The two ways a path may be turned into a
-- cache key are modeled DEEPLY by `Key`/`KeyRepr` below (a deep-model reference,
-- validated against the real path objects by axiom_check.py / G-AX), NOT behind
-- a consumed axiom.
-- axioms-end

-- pure-start
/- A module identity. Only equality is ever observed (whether two lookups return
   the same loaded module), so a bare identifier suffices. -/
abbrev Module := Nat

/- The two ways the same filesystem location can be turned into a key object for
   the module cache. Both denote the same location, yet as cache keys they are
   NOT interchangeable: a cache keyed under one representation does not answer a
   lookup made under the other. `primary` is the representation every consumer
   computes when it probes the cache; `secondary` is an alternative key object
   for the same location. (On the real system the two key objects compare equal
   as strings but hash differently, so they are distinct dictionary keys — the
   distinction `axiom_check.py`/G-AX validates against the real path objects.) -/
inductive KeyRepr where
  | primary
  | secondary
deriving DecidableEq, Inhabited, Repr

/- A cache key: the filesystem location it denotes together with which key
   representation produced it. Two keys answer the same lookup iff BOTH the
   location and the representation match (structural equality = dictionary-key
   identity, mapping.md §2). -/
structure Key where
  loc : Nat
  rep : KeyRepr
deriving DecidableEq, Inhabited, Repr

/- The key every consumer uses to probe the cache for a location: the `primary`
   representation. The cache is correct exactly when an entry registered for a
   location can be found again under this key. -/
def probeKey (loc : Nat) : Key := ⟨loc, KeyRepr.primary⟩

/- Look a key up in the cache (an association list of key→module). Front-recursive
   so a single unfold is available; returns the module of the first matching
   entry, `none` if the key is absent. Matching is full structural key equality. -/
def regLookup : List (Key × Module) → Key → Option Module
  | [],            _ => none
  | (k, m) :: rest, q => if k = q then some m else regLookup rest q

@[grind, simp] lemma regLookup_nil (q : Key) : regLookup [] q = none := rfl
@[grind, simp] lemma regLookup_cons (k : Key) (m : Module)
    (rest : List (Key × Module)) (q : Key) :
    regLookup ((k, m) :: rest) q = if k = q then some m else regLookup rest q := rfl

/- Appending a fresh entry for a key not yet present makes that key resolve to
   the appended module. The single fact the registration branch needs. -/
/- A present cache entry equals `some` of the value read out of it: the
   cache-hit branch returns exactly the module already stored. -/
@[grind] lemma some_getD_of_isSome {α : Type} (o : Option α) (d : α)
    (h : o.isSome = true) : o = some (o.getD d) := by
  cases o with
  | none => simp at h
  | some v => rfl

@[grind] lemma regLookup_append_fresh (reg : List (Key × Module)) (k : Key) (m : Module)
    (h : regLookup reg k = none) :
    regLookup (reg ++ [(k, m)]) k = some m := by
  induction reg with
  | nil => simp
  | cons hd tl ih =>
    obtain ⟨k', m'⟩ := hd
    rw [List.cons_append, regLookup_cons]
    rw [regLookup_cons] at h
    by_cases hk : k' = k
    · rw [if_pos hk] at h; exact absurd h (by simp)
    · rw [if_neg hk] at h; rw [if_neg hk]; exact ih h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Obtain the module associated with a filesystem location through a shared
   module cache, importing it only once.

   The cache (`registry`) maps a path-derived key to the loaded module. A
   consumer always probes the cache under the location's `primary` key
   (`probeKey loc`). The desired behaviour:

   * if the `primary` key for this location is already registered, return the
     module found there and leave the cache exactly as it was (the import is
     performed at most once per location);
   * otherwise register the freshly produced module under the location's
     `primary` key and return it.

   The post-state is pinned so that, in every case, a subsequent probe of the
   cache under `probeKey loc` finds the returned module — i.e. the entry MUST be
   stored under the same key representation that lookups use, never under a
   merely same-location alternative.

   `loc` and `freshMod` are read-only (not `mut`); `registry` is the only mutated
   state and its post-state is pinned exactly in each branch (directive 5). -/
method registerModule (mut registry : List (Key × Module)) (loc : Nat) (freshMod : Module)
    return (out : Module)
  ensures ∀ m, regLookup registryOld (probeKey loc) = some m →
            (out = m ∧ registry = registryOld)
  ensures regLookup registryOld (probeKey loc) = none →
            (out = freshMod ∧ registry = registryOld ++ [(probeKey loc, freshMod)])
  ensures regLookup registry (probeKey loc) = some out
  do
    -- impl-start
    let k : Key := probeKey loc
    let cached := regLookup registry k
    if cached.isSome then
      return cached.getD freshMod
    else
      registry := registry ++ [(k, freshMod)]
      return freshMod
    -- impl-end

prove_correct registerModule by
  loom_solve
  simp_all [probeKey, regLookup_append_fresh]
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed in fresh scratch, root. same_spec(velvet) == True for ALL 6 attacks + pos_control + prepatch (verified via swebench_unified.markers.same_spec + get_backend('velvet')). Verify cmd per file: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4/batch.

RESULTS (exit codes): pos_control=0 (VERIFIES, correct impl). All 6 same-spec wrong impls FAIL to verify (exit 1, semantic 'unsolved goals', NOT parse errors — confirmed by inspecting .out logs; atk_2 had an initial indentation glitch that was fixed to a clean semantic failure and re-verified). prepatch=1 (fails ensures3, G-DIFF reproduced).
  atk_1: partial-domain — always `return freshMod`, no register (fails ensures2 miss-branch registry + ensures3). exit1.
  atk_2: control-flow-effect — append on EVERY path incl. hit (violates ensures1 registry=registryOld). exit1.
  atk_3: boundary — branches swapped (return freshMod on hit / cached.getD on miss). exit1.
  atk_4: ungrounded-oracle echo — miss-branch returns literal 0 instead of freshMod (violates ensures2/ensures3). exit1.
  atk_5: control-flow — never look up; always append+return freshMod (violates ensures1 on hit). exit1.
  atk_6: wrong-key — miss-branch stores under ⟨loc,secondary⟩ (violates ensures2 post-state + ensures3). exit1.

No VERIFYING wrong impl was found, so the mandatory materialize-faithful-patch + run_resolve step had NO candidates — patches={} (correctly, since resolve is only required for a verifying wrong impl whose patch might fail). No resolve run was needed to reach a verdict; nothing could break verify⇒correct because nothing else verified.

WHY SOUND (spec is fully pinned): the 3 ensures clauses determine out AND the entire registry post-state in BOTH branches (hit: out=m ∧ registry=registryOld; miss: out=freshMod ∧ registry=registryOld++[(probeKey loc,freshMod)]; plus ensures3 probe-finds-result). Every degree of freedom an impl could perturb (returned value, mutation presence/target, key representation) is constrained; my 6 attacks cover the four required families and all are rejected by loom_solve/simp_all.

REFINEMENT.MD LEG AUDIT (A-focus): A1/A2=R; A3=A-reference+I (Key/KeyRepr deep model of the changed key-construction — validated by axiom_check.py/G-AX); A4=I; A5=I+R; §C freshMod=R (free input, correctly NOT a consumed axiom — avoids dead-axiom over-claim); §D asserts no kind-3 and no consumed axioms (axioms region empty). The sole A-reference's correspondence to the real callees holds: axiom_check.py reconstructs unique_path VERBATIM from pre-patch pathlib.py, builds real primary=Path(str(p)).resolve() and secondary=unique_path(p) on 10 boundary paths (incl. #5819 Foo/, #5792 mixed-case) + 3000 seeded(5840) fuzz paths, and asserts prim==sec (value-equal) yet prim NOT in {sec:...} and hash(prim)!=hash(sec) (distinct dict keys) — exactly the model's ⟨loc,primary⟩≠⟨loc,secondary⟩ and regLookup[(⟨loc,secondary⟩,m)](probeKey loc)=none. Model↔patch correspondence (mapping.md §1/§2/§3) is faithful. No kind-3 leg.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found. (1) Spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec => True; Solution verifies (lean_verify exit 0); prepatch correctly fails the pinned post-state clause `regLookup registry (probeKey loc) = some out` (G-DIFF), exactly mirroring the real pre-patch F2P miss. (2) The model registerModule faithfully abstracts post-patch _importconftest: registry:List(Key x Module) <-> self._conftestpath2mod dict (first-match lookup, append insert; order-irrelevant, at-most-one insert per location); probeKey loc = <loc,primary> <-> key=Path(str(conftestpath)).resolve(); freshMod <-> pyimport() result taken as a free input since the patch never inspects the value, only the KEY. (3) All three postconditions checked against the real callee and hold: HIT returns the stored module with the cache untouched (freshMod ignored, matches real early-return); MISS inserts under the primary key and returns freshMod (append-at-end is a faithful assoc-list image of dict insertion, lookup-equivalent); post-probe finds out in both branches. (4) Abstraction boundaries are legitimate scope choices, not spec drift: the exceptional pyimport()-raises path is outside the total-correctness domain (freshMod denotes a successfully loaded module), and side effects on _conftest_plugins/_dirpath2confmods are unmodeled other-state not observed by the F2P cache assertion `key in conftest._conftestpath2mod`. (5) The single discriminating behavior (store AND probe under the same `primary` representation, never a same-location `secondary`) is deep-modeled and matches the gold patch; the distinct-dict-key fact is deferred to G-AX/axiom_check.py. Spec is neither too strong nor too weak on the modeled domain; no input observed where the model disagrees with the real post-patch _importconftest cache behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction) for pytest-dev__pytest-5840 (velvet). (1) Spec-region integrity: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True; the two files diff ONLY inside the elided impl region (post-patch `let k := probeKey loc` = <loc,primary>; prepatch `let k := <loc,secondary>`). The gold discriminator lives entirely in the impl the spec view elides. (2) Mechanical lexical screen (leakage.screen) passes, zero hard failures; G-LEAK meta = pass 'spec view clean'. (3) The rendered spec view contains NONE of the gold-patch identifiers: no unique_path, normcase, Path, resolve, _conftestpath2mod, _importconftest, pathlib, conftest, or any repo file path. All symbols are abstracted (registerModule, Key, KeyRepr, primary/secondary, probeKey, regLookup, loc, freshMod). (4) Semantically, the spec view only states the abstract behavioral requirement — the cache entry must be stored under the same key representation consumers probe with (primary), not a same-location alternative (secondary). This is the faithful spec of the fixed function, as every spec must be; it does NOT reveal the concrete gold mechanism (Path(str(p)).resolve() as primary vs unique_path/normcase(realpath) as secondary). That concrete binding lives only in mapping.md/axiom_check.py, which are auditor artifacts and NOT part of the consumer spec view. A solver still must localize _importconftest and choose the case-preserving resolved key in the real repo. (5) Relative to the public problem_statement (which already exposes the casing/lowercasing symptom), the spec adds only abstract structural framing, not gold identifiers or the specific API choice. Hints_text (which mentions normcase/Path.resolve) is correctly excluded from the baseline. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

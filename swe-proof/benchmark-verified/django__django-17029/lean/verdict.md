# P2 adversarial audit — django__django-17029

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
None. The postcondition problem_spec_clearCaches fully pins the output to ⟨[], [], st.ready⟩ for every input st (result.nameLookupCache = [] ∧ result.entityListCache = [] ∧ result.ready = st.ready). Any genuinely-wrong impl makes the proof goal reduce to a false proposition, so NO wrong impl closes under ANY proof — there is no closing-proof wrong impl to route through resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,12 +63,8 @@
 -- impl-start
 def implementation_clearCaches (st : CacheRegistry) : CacheRegistry := Id.run do
   let mut s := st
-  -- discard the name-lookup cache
-  s := { s with nameLookupCache := [] }
-  -- discard the entity-list cache
+  -- BUG: name-lookup cache NOT cleared (the exact prepatch omission)
   s := { s with entityListCache := [] }
-  -- a readiness-gated refresh of per-entity metadata runs here; it touches a
-  -- separate metadata layer and leaves both result caches (and `ready`) intact
   return s
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,12 +63,8 @@
 -- impl-start
 def implementation_clearCaches (st : CacheRegistry) : CacheRegistry := Id.run do
   let mut s := st
-  -- discard the name-lookup cache
   s := { s with nameLookupCache := [] }
-  -- discard the entity-list cache
-  s := { s with entityListCache := [] }
-  -- a readiness-gated refresh of per-entity metadata runs here; it touches a
-  -- separate metadata layer and leaves both result caches (and `ready`) intact
+  -- BUG: entity-list cache NOT cleared
   return s
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,12 +63,9 @@
 -- impl-start
 def implementation_clearCaches (st : CacheRegistry) : CacheRegistry := Id.run do
   let mut s := st
-  -- discard the name-lookup cache
   s := { s with nameLookupCache := [] }
-  -- discard the entity-list cache
   s := { s with entityListCache := [] }
-  -- a readiness-gated refresh of per-entity metadata runs here; it touches a
-  -- separate metadata layer and leaves both result caches (and `ready`) intact
+  s := { s with ready := !st.ready }
   return s
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,15 +61,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_clearCaches (st : CacheRegistry) : CacheRegistry := Id.run do
-  let mut s := st
-  -- discard the name-lookup cache
-  s := { s with nameLookupCache := [] }
-  -- discard the entity-list cache
-  s := { s with entityListCache := [] }
-  -- a readiness-gated refresh of per-entity metadata runs here; it touches a
-  -- separate metadata layer and leaves both result caches (and `ready`) intact
-  return s
+def implementation_clearCaches (st : CacheRegistry) : CacheRegistry :=
+  if st.ready then { st with nameLookupCache := [], entityListCache := [] }
+  else st
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,15 +61,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_clearCaches (st : CacheRegistry) : CacheRegistry := Id.run do
-  let mut s := st
-  -- discard the name-lookup cache
-  s := { s with nameLookupCache := [] }
-  -- discard the entity-list cache
-  s := { s with entityListCache := [] }
-  -- a readiness-gated refresh of per-entity metadata runs here; it touches a
-  -- separate metadata layer and leaves both result caches (and `ready`) intact
-  return s
+def implementation_clearCaches (st : CacheRegistry) : CacheRegistry :=
+  { st with nameLookupCache := st.nameLookupCache.tail, entityListCache := [] }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,15 +61,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_clearCaches (st : CacheRegistry) : CacheRegistry := Id.run do
-  let mut s := st
-  -- discard the name-lookup cache
-  s := { s with nameLookupCache := [] }
-  -- discard the entity-list cache
-  s := { s with entityListCache := [] }
-  -- a readiness-gated refresh of per-entity metadata runs here; it touches a
-  -- separate metadata layer and leaves both result caches (and `ready`) intact
-  return s
+def implementation_clearCaches (st : CacheRegistry) : CacheRegistry :=
+  { nameLookupCache := [], entityListCache := [], ready := true }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,15 +61,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_clearCaches (st : CacheRegistry) : CacheRegistry := Id.run do
-  let mut s := st
-  -- discard the name-lookup cache
-  s := { s with nameLookupCache := [] }
-  -- discard the entity-list cache
-  s := { s with entityListCache := [] }
-  -- a readiness-gated refresh of per-entity metadata runs here; it touches a
-  -- separate metadata layer and leaves both result caches (and `ready`) intact
-  return s
+def implementation_clearCaches (st : CacheRegistry) : CacheRegistry :=
+  { st with
+      nameLookupCache := if st.nameLookupCache = [] then st.nameLookupCache else [],
+      entityListCache := [] }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Discarding the memoized results held by an application registry.

A registry memoizes the answers of two independent query methods in two separate
result caches:

  * a name-lookup cache, mapping a queried string to the resolved name (or to
    "no such name"), and
  * an entity-list cache, mapping a pair of inclusion flags to the list of
    registered entities those flags select.

The registry also carries a readiness flag that governs an auxiliary refresh of
per-entity metadata. That refresh touches a separate metadata layer and is not
part of the two result caches.

The "discard" operation exists so that callers can return the registry to a
clean state whenever the underlying registry contents may have changed: after it
runs, *every* memoized result must be gone, so that the next query is recomputed
from the current registry contents rather than served from a stale cache. The
readiness flag is only consulted, never altered.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The registry's cache state and its
-- readiness flag enter as plain data (lists of memoized key/value pairs and a
-- boolean), and the only operation performed is discarding the memoized
-- entries, modeled directly below. Hence no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The cache state of an application registry, modeled by the two independent
result caches it memoizes plus its readiness flag.

  * `nameLookupCache`: memoized answers of the name-lookup query — each entry
    pairs the queried string with the resolved name (`some n`) or "no such
    name" (`none`).
  * `entityListCache`: memoized answers of the entity-list query — each entry
    pairs the two inclusion flags with the selected entity names.
  * `ready`: the readiness flag (consulted by the auxiliary metadata refresh,
    never modified by the discard operation). -/
structure CacheRegistry where
  nameLookupCache : List (String × Option String)
  entityListCache : List ((Bool × Bool) × List String)
  ready : Bool
-- pure-end

-- post-conditions-start
/-- The discard operation fully pins the resulting registry state to its input:

  * BOTH result caches are empty afterwards (`nameLookupCache = []` and
    `entityListCache = []`) — no memoized result of either query may survive;
  * the readiness flag is unchanged (frame: the operation only consults it). -/
def problem_spec_clearCaches (st : CacheRegistry) (result : CacheRegistry) : Prop :=
  result.nameLookupCache = [] ∧
  result.entityListCache = [] ∧
  result.ready = st.ready
-- post-conditions-end

-- impl-start
def implementation_clearCaches (st : CacheRegistry) : CacheRegistry :=
  { nameLookupCache := [], entityListCache := [], ready := st.ready }
-- impl-end

-- proof-start
theorem correct_clearCaches :
    ∀ (st : CacheRegistry),
      problem_spec_clearCaches st (implementation_clearCaches st) := by
  intro st
  refine ⟨rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same-spec confirmed True for all 8 files via swebench_unified.markers.same_spec (axioms/pure/pre/post byte-identical; only impl region edited). meta.json: axioms=[], deep_model_references=[], conf_skip=false.

### VERIFICATION RESULTS (project root; cmd: bash scripts/lean_verify.sh <f>):
- atk_1 (PREPATCH BUG: omits nameLookupCache:=[], leaves st's name cache) EXIT=1 FAIL. Reproduces the real bug; goal needs st.nameLookupCache=[] for arbitrary st → false.
- atk_2 (omit entityListCache:=[]) EXIT=1 FAIL.
- atk_3 (control-flow-effect: flips ready := !st.ready, violating frame) EXIT=1 FAIL.
- atk_4 (partial-domain: only clears when st.ready, else identity) EXIT=1 FAIL.
- atk_5 (boundary: nameLookupCache := .tail instead of []) EXIT=1 FAIL.
- atk_6 (ungrounded-oracle echo: constant ⟨[],[],true⟩, ready hard-coded) EXIT=1 FAIL — goal needs true=st.ready → false.
- atk_7 (control-flow echo: if st.nameLookupCache=[] then it else []; extensionally always [], gold-equivalent) EXIT=1 (carried refine ⟨rfl,rfl,rfl⟩ can't discharge the definitional if but impl IS correct; not a spec gap — a correct proof exists).
- pos_control (alternate CORRECT impl: constructor ⟨[],[],st.ready⟩) EXIT=0 VERIFIES.
- pos_axiom (pos_control + #print axioms correct_clearCaches) EXIT=0; output: "'correct_clearCaches' does not depend on any axioms" → CLEAN AXIOMS.

WHY NO RESOLVE RUN: protocol step 2 requires materializing+resolving a faithful patch ONLY for wrong impls whose proof CLOSES with clean axioms. Zero wrong impls close (the spec fully pins the 3-tuple output), so no such patch exists. verify⇒correct holds here.

REFINEMENT AUDIT (refinement.md): 4 legs — #1 carrier bind = I; #2 nameLookupCache:=[] ↔ get_swappable_settings_name.cache_clear() (the ADDED gold line) = R; #3 entityListCache:=[] ↔ get_models.cache_clear() = R; #4 return / if self.ready refresh no-op ↔ metadata-refresh block (separate metadata layer, never refills caches) = I. All legs R or I; no A-consumed, no A-reference, no kind-3. Consistent with meta.json axioms=[] & deep_model_references=[]. No A-leg callee correspondence to audit. R/I legs are G-CONF-covered (conformance_check.py differential-tests shadow vs real patched Apps.clear_cache via cache_info().currsize over 1e5 inputs, seed 17029).

prepatch_reproduced=true (atk_1 = exact prepatch omission, fails verification).

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
None. The postcondition problem_spec_clearCaches fully pins the output to ⟨[], [], st.ready⟩ for every input st (result.nameLookupCache = [] ∧ result.entityListCache = [] ∧ result.ready = st.ready). Any genuinely-wrong impl makes the proof goal reduce to a false proposition, so NO wrong impl closes under ANY proof — there is no closing-proof wrong impl to route through resolve.
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
Discarding the memoized results held by an application registry.

A registry memoizes the answers of two independent query methods in two separate
result caches:

  * a name-lookup cache, mapping a queried string to the resolved name (or to
    "no such name"), and
  * an entity-list cache, mapping a pair of inclusion flags to the list of
    registered entities those flags select.

The registry also carries a readiness flag that governs an auxiliary refresh of
per-entity metadata. That refresh touches a separate metadata layer and is not
part of the two result caches.

The "discard" operation exists so that callers can return the registry to a
clean state whenever the underlying registry contents may have changed: after it
runs, *every* memoized result must be gone, so that the next query is recomputed
from the current registry contents rather than served from a stale cache. The
readiness flag is only consulted, never altered.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The registry's cache state and its
-- readiness flag enter as plain data (lists of memoized key/value pairs and a
-- boolean), and the only operation performed is discarding the memoized
-- entries, modeled directly below. Hence no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The cache state of an application registry, modeled by the two independent
result caches it memoizes plus its readiness flag.

  * `nameLookupCache`: memoized answers of the name-lookup query — each entry
    pairs the queried string with the resolved name (`some n`) or "no such
    name" (`none`).
  * `entityListCache`: memoized answers of the entity-list query — each entry
    pairs the two inclusion flags with the selected entity names.
  * `ready`: the readiness flag (consulted by the auxiliary metadata refresh,
    never modified by the discard operation). -/
structure CacheRegistry where
  nameLookupCache : List (String × Option String)
  entityListCache : List ((Bool × Bool) × List String)
  ready : Bool
-- pure-end

-- post-conditions-start
/-- The discard operation fully pins the resulting registry state to its input:

  * BOTH result caches are empty afterwards (`nameLookupCache = []` and
    `entityListCache = []`) — no memoized result of either query may survive;
  * the readiness flag is unchanged (frame: the operation only consults it). -/
def problem_spec_clearCaches (st : CacheRegistry) (result : CacheRegistry) : Prop :=
  result.nameLookupCache = [] ∧
  result.entityListCache = [] ∧
  result.ready = st.ready
-- post-conditions-end

-- impl-start
def implementation_clearCaches (st : CacheRegistry) : CacheRegistry :=
  { nameLookupCache := [], entityListCache := [], ready := st.ready }
-- impl-end

-- proof-start
theorem correct_clearCaches :
    ∀ (st : CacheRegistry),
      problem_spec_clearCaches st (implementation_clearCaches st) := by
  intro st
  refine ⟨rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same-spec confirmed True for all 8 files via swebench_unified.markers.same_spec (axioms/pure/pre/post byte-identical; only impl region edited). meta.json: axioms=[], deep_model_references=[], conf_skip=false.

### VERIFICATION RESULTS (project root; cmd: bash scripts/lean_verify.sh <f>):
- atk_1 (PREPATCH BUG: omits nameLookupCache:=[], leaves st's name cache) EXIT=1 FAIL. Reproduces the real bug; goal needs st.nameLookupCache=[] for arbitrary st → false.
- atk_2 (omit entityListCache:=[]) EXIT=1 FAIL.
- atk_3 (control-flow-effect: flips ready := !st.ready, violating frame) EXIT=1 FAIL.
- atk_4 (partial-domain: only clears when st.ready, else identity) EXIT=1 FAIL.
- atk_5 (boundary: nameLookupCache := .tail instead of []) EXIT=1 FAIL.
- atk_6 (ungrounded-oracle echo: constant ⟨[],[],true⟩, ready hard-coded) EXIT=1 FAIL — goal needs true=st.ready → false.
- atk_7 (control-flow echo: if st.nameLookupCache=[] then it else []; extensionally always [], gold-equivalent) EXIT=1 (carried refine ⟨rfl,rfl,rfl⟩ can't discharge the definitional if but impl IS correct; not a spec gap — a correct proof exists).
- pos_control (alternate CORRECT impl: constructor ⟨[],[],st.ready⟩) EXIT=0 VERIFIES.
- pos_axiom (pos_control + #print axioms correct_clearCaches) EXIT=0; output: "'correct_clearCaches' does not depend on any axioms" → CLEAN AXIOMS.

WHY NO RESOLVE RUN: protocol step 2 requires materializing+resolving a faithful patch ONLY for wrong impls whose proof CLOSES with clean axioms. Zero wrong impls close (the spec fully pins the 3-tuple output), so no such patch exists. verify⇒correct holds here.

REFINEMENT AUDIT (refinement.md): 4 legs — #1 carrier bind = I; #2 nameLookupCache:=[] ↔ get_swappable_settings_name.cache_clear() (the ADDED gold line) = R; #3 entityListCache:=[] ↔ get_models.cache_clear() = R; #4 return / if self.ready refresh no-op ↔ metadata-refresh block (separate metadata layer, never refills caches) = I. All legs R or I; no A-consumed, no A-reference, no kind-3. Consistent with meta.json axioms=[] & deep_model_references=[]. No A-leg callee correspondence to audit. R/I legs are G-CONF-covered (conformance_check.py differential-tests shadow vs real patched Apps.clear_cache via cache_info().currsize over 1e5 inputs, seed 17029).

prepatch_reproduced=true (atk_1 = exact prepatch omission, fails verification).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-17029 lean bundle. VERIFICATION PERFORMED: (1) Solution.lean compiles under lean_verify.sh (exit 0, no sorry); `#print axioms correct_clearCaches` reports 'does not depend on any axioms' — proof is genuine, not sorryAx-backed. (2) Spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (LeanBackend.language tables): same_spec=True, spec_signature equal. Only the impl differs (prepatch omits `nameLookupCache := []`, the exact gold-patch line). Real callee inspected in post-patch worktree registry.py:370 Apps.clear_cache.

MODEL vs REAL CALLEE: post-condition problem_spec_clearCaches requires result.nameLookupCache=[] ∧ result.entityListCache=[] ∧ result.ready=st.ready. Real clear_cache: (a) get_swappable_settings_name.cache_clear() -> nameLookupCache currsize->0 unconditionally; (b) get_models.cache_clear() -> entityListCache currsize->0 unconditionally; (c) `if self.ready:` runs model._meta._expire_cache() over app_config.get_models(...) — the AppConfig method, NOT the functools-cached Apps.get_models — and the source comment explicitly states it circumvents self.get_models() precisely to avoid refilling the cache. Thus even when ready=True the branch neither repopulates either functools result cache nor re-invokes get_swappable_settings_name, and never mutates self.ready.

CONCLUSION: For every input registry state (any ready value, any cache contents), the real callee empties BOTH caches and preserves ready — matching the spec exactly. The spec is not too strong: no diverging input exists where the real callee would leave a cache non-empty or change ready. FAITHFUL. No divergence found; searched the ready=True branch (the only conditional path) specifically, since a naive model might have assumed it refills caches — it does not, per source + comment. mapping.md/refinement.md accurately describe the callee. The F2P bug is purely the missing first cache_clear line, which the spec's nameLookupCache=[] clause captures and the prepatch impl (correctly) fails.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view for django__django-17029/lean does not leak the gold edit beyond the public problem_statement.

Gold edit: adds `self.get_swappable_settings_name.cache_clear()` to Apps.clear_cache (django/apps/registry.py). This fix is ALREADY fully public in problem_statement, which literally states 'Apps.clear_cache() does not clear get_swappable_settings_name cache' and 'I propose to add: self.get_swappable_settings_name.cache_clear() line to def clear_cache.' So the very existence of two caches and the requirement to clear both is public via the task (not hints_text).

Spec-view checks (all clean):
- No diff markers; the changed gold line does not appear (mechanical screen PASSED, hard_failures=[]).
- No patched file path (django/apps/registry.py) or module path in the spec view.
- Identifiers are fully abstracted: nameLookupCache / entityListCache / ready — none echo the repo symbols get_swappable_settings_name / get_models / clear_cache. The single distinctive changed symbol computed by the screen (`clear_cache`) appears nowhere in spec-view identifiers or comments.
- No bug/fix narration in the docstring/comments.
- Post-condition (`nameLookupCache = [] ∧ entityListCache = [] ∧ ready = st.ready`) pins that BOTH caches are emptied — but that is precisely the public content of the problem_statement, not extra gold-localization.

Cross-checked spec invariance: same_spec(Solution.lean, Solution_prepatch.lean) = True — the spec view is byte-identical between patched and prepatch bundles, so the discriminator (which op the gold added) lives entirely in the elided impl region, not in the consumer-visible spec. The spec faithfully describes the publicly-known behavior without revealing the edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

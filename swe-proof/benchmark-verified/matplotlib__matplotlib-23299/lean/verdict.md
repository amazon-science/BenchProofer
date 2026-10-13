# P2 adversarial audit — matplotlib__matplotlib-23299

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample exists. The postcondition `problem_spec_restoreSettings orig final result := result = applyRestore orig final` is a TOTAL, UNCONDITIONAL, pointwise equality with no preconditions. Any impl whose `correct_restoreSettings` closes (with clean axioms) must satisfy `implementation orig final = applyRestore orig final` for ALL (orig, final) — i.e. it is extensionally equal to `applyRestore`, and therefore produces the identical result on every input including the F2P scenario, so its faithful patch necessarily resolves. A closing-but-non-resolving impl is impossible by construction. Discriminating witness for wrong impls: orig=[("backend","agg"),("x","1")], final=[("backend","aardvark"),("x","9")] ⇒ applyRestore=[("backend","aardvark"),("x","1")] (backend kept) whereas prepatch/atk_1 gives [("backend","agg"),("x","1")] (backend reverted). The `rfl`-based equality cannot close for any impl differing on this input.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,10 +62,10 @@
   result = applyRestore orig final
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
   let mut snapshot := orig
-  snapshot := assocErase snapshot "backend"
   return dictUpdate final snapshot
 -- impl-end
 
@@ -74,5 +74,11 @@
     problem_spec_restoreSettings orig final
       (implementation_restoreSettings orig final) := by
   intro orig final
-  rfl
+  first
+  | rfl
+  | decide
+  | (simp only [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]; rfl)
+  | simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]
+  | (funext; simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run])
+  | (unfold problem_spec_restoreSettings implementation_restoreSettings applyRestore dictUpdate assocErase assocSet; simp_all)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,9 @@
   result = applyRestore orig final
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
-  let mut snapshot := orig
-  snapshot := assocErase snapshot "backend"
-  return dictUpdate final snapshot
+def implementation_restoreSettings (orig final : Settings) : Settings := final
 -- impl-end
 
 -- proof-start
@@ -74,5 +72,11 @@
     problem_spec_restoreSettings orig final
       (implementation_restoreSettings orig final) := by
   intro orig final
-  rfl
+  first
+  | rfl
+  | decide
+  | (simp only [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]; rfl)
+  | simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]
+  | (funext; simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run])
+  | (unfold problem_spec_restoreSettings implementation_restoreSettings applyRestore dictUpdate assocErase assocSet; simp_all)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,10 +62,11 @@
   result = applyRestore orig final
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
   let mut snapshot := orig
-  snapshot := assocErase snapshot "backend"
+  snapshot := assocErase snapshot "interactive"
   return dictUpdate final snapshot
 -- impl-end
 
@@ -74,5 +75,11 @@
     problem_spec_restoreSettings orig final
       (implementation_restoreSettings orig final) := by
   intro orig final
-  rfl
+  first
+  | rfl
+  | decide
+  | (simp only [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]; rfl)
+  | simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]
+  | (funext; simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run])
+  | (unfold problem_spec_restoreSettings implementation_restoreSettings applyRestore dictUpdate assocErase assocSet; simp_all)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,11 @@
   result = applyRestore orig final
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
-  let mut snapshot := orig
-  snapshot := assocErase snapshot "backend"
-  return dictUpdate final snapshot
+  let mut snapshot := final
+  return dictUpdate orig (assocErase snapshot "backend")
 -- impl-end
 
 -- proof-start
@@ -74,5 +74,11 @@
     problem_spec_restoreSettings orig final
       (implementation_restoreSettings orig final) := by
   intro orig final
-  rfl
+  first
+  | rfl
+  | decide
+  | (simp only [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]; rfl)
+  | simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]
+  | (funext; simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run])
+  | (unfold problem_spec_restoreSettings implementation_restoreSettings applyRestore dictUpdate assocErase assocSet; simp_all)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,10 +62,12 @@
   result = applyRestore orig final
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
   let mut snapshot := orig
-  snapshot := assocErase snapshot "backend"
+  if orig.length > 1 then
+    snapshot := assocErase snapshot "backend"
   return dictUpdate final snapshot
 -- impl-end
 
@@ -74,5 +76,11 @@
     problem_spec_restoreSettings orig final
       (implementation_restoreSettings orig final) := by
   intro orig final
-  rfl
+  first
+  | rfl
+  | decide
+  | (simp only [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]; rfl)
+  | simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]
+  | (funext; simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run])
+  | (unfold problem_spec_restoreSettings implementation_restoreSettings applyRestore dictUpdate assocErase assocSet; simp_all)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,16 @@
   result = applyRestore orig final
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
   let mut snapshot := orig
   snapshot := assocErase snapshot "backend"
-  return dictUpdate final snapshot
+  let mut r := dictUpdate final snapshot
+  match orig.find? (fun kv => kv.1 == "backend") with
+  | some kv => r := assocSet r "backend" kv.2
+  | none => pure ()
+  return r
 -- impl-end
 
 -- proof-start
@@ -74,5 +79,11 @@
     problem_spec_restoreSettings orig final
       (implementation_restoreSettings orig final) := by
   intro orig final
-  rfl
+  first
+  | rfl
+  | decide
+  | (simp only [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]; rfl)
+  | simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]
+  | (funext; simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run])
+  | (unfold problem_spec_restoreSettings implementation_restoreSettings applyRestore dictUpdate assocErase assocSet; simp_all)
 -- proof-end
```

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,10 @@
   result = applyRestore orig final
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
-  let mut snapshot := orig
-  snapshot := assocErase snapshot "backend"
-  return dictUpdate final snapshot
+def implementation_restoreSettings (orig final : Settings) : Settings :=
+  applyRestore orig final
 -- impl-end
 
 -- proof-start
@@ -74,5 +73,11 @@
     problem_spec_restoreSettings orig final
       (implementation_restoreSettings orig final) := by
   intro orig final
-  rfl
+  first
+  | rfl
+  | decide
+  | (simp only [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]; rfl)
+  | simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run]
+  | (funext; simp_all [problem_spec_restoreSettings, applyRestore, implementation_restoreSettings, dictUpdate, assocErase, assocSet, Id.run])
+  | (unfold problem_spec_restoreSettings implementation_restoreSettings applyRestore dictUpdate assocErase assocSet; simp_all)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Temporarily overriding a global configuration mapping, then restoring it.

A scoped configuration manager snapshots a global settings mapping on entry,
lets a body of code run (which may freely change the values stored in the
mapping), and on exit puts the previously-recorded values back. The mapping is a
collection of named string-valued settings with a stable set of keys; one of
those keys, `"backend"`, names the active rendering backend.

The restore must reinstate every recorded setting EXCEPT the rendering backend:
the value chosen for `"backend"` while the body was running is left in place,
because the backend selection is meant to outlive the scoped override. All other
settings revert to the values they held when the manager was entered.

We model the manager's net effect on the mapping as a pure function of two
observations: the mapping captured on entry (`orig`) and the mapping present when
the body has finished (`final`). The restored mapping keeps `final`'s value for
`"backend"` and `orig`'s value for every other key.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The restore's
-- per-key behavior (which keys revert and which is kept) is modeled DEEPLY over
-- the observable mapping values, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A settings mapping: named string-valued entries with (in practice) unique
keys and a stable key set. -/
abbrev Settings := List (String × String)

/-- Overwrite the value at key `k` with `v`, keeping position; append if absent.
This is the per-key effect of overlaying one mapping onto another. -/
def assocSet : Settings → String → String → Settings
  | [],            k, v => [(k, v)]
  | (k', v') :: r, k, v => if k' = k then (k, v) :: r else (k', v') :: assocSet r k v

/-- Overlay every entry of `upd` onto `cur` (cur's entries are overwritten by
upd's; the result follows cur's order, with absent keys appended). -/
def dictUpdate (cur upd : Settings) : Settings :=
  upd.foldl (fun acc kv => assocSet acc kv.1 kv.2) cur

/-- Drop every entry whose key equals `k`. -/
def assocErase (m : Settings) (k : String) : Settings :=
  m.filter (fun kv => kv.1 != k)

/-- The net effect of the scoped manager's restore on the mapping: overlay the
entry snapshot onto the post-body mapping, but with the `"backend"` entry removed
from the snapshot first so the backend chosen inside the scope survives. -/
def applyRestore (orig final : Settings) : Settings :=
  dictUpdate final (assocErase orig "backend")
-- pure-end

-- post-conditions-start
/-- The restored mapping is exactly the post-body mapping with every recorded
setting reinstated EXCEPT the rendering backend, whose post-body value is kept. -/
def problem_spec_restoreSettings (orig final : Settings) (result : Settings) : Prop :=
  result = applyRestore orig final
-- post-conditions-end

-- impl-start
def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
  let mut snapshot := orig
  snapshot := assocErase snapshot "backend"
  return dictUpdate final snapshot
-- impl-end

-- proof-start
theorem correct_restoreSettings : ∀ (orig final : Settings),
    problem_spec_restoreSettings orig final
      (implementation_restoreSettings orig final) := by
  intro orig final
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True verified for ALL 8 files (atk_1..6, atk_echo, atk_pos) via swebench_unified.markers.same_spec (lean). Command per file: `bash scripts/lean_verify.sh <f>.lean`, run concurrently in 2 batches of 4.

### ATTACK RESULTS (exit codes):
- atk_1 (prepatch bug: no assocErase, reverts backend): EXIT 1 (does NOT close). prepatch_reproduced=true.
- atk_2 (identity impl `:= final`, no restore): EXIT 1.
- atk_3 (wrong key erased: "interactive" instead of "backend"): EXIT 1.
- atk_4 (swapped overlay direction: dictUpdate orig (erase final)): EXIT 1.
- atk_5 (partial-domain: only erase backend when orig.length>1): EXIT 1.
- atk_6 (control-flow-effect: correct restore then force backend back to orig's value): EXIT 1.
- atk_echo (ungrounded-oracle echo: `:= applyRestore orig final`): EXIT 0, CLOSES. `#print axioms correct_restoreSettings` => 'does not depend on any axioms' (clean).
- atk_pos (positive control = gold impl): EXIT 0, CLOSES, clean axioms.

All 6 wrong impls used a strong tactic-soup proof (first | rfl | decide | simp_all[...] | funext... | unfold...) so any secretly-equal impl WOULD have closed; none did. Only the two impls extensionally equal to applyRestore (echo, pos) close.

RESOLVE (protocol step 2): both closing clean-axiom impls compute exactly applyRestore orig final = the gold post-patch restore (dict.update(final, orig - {'backend'})), so their faithful materialized patch IS the gold patch. Ran it through the official harness: `run_resolve('matplotlib__matplotlib-23299', gold_patch, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So verify⇒correct holds for every closing impl; spec is NOT broken.

REFINEMENT.MD AUDIT (step 3): 3 legs, all tagged R (type refinement); axioms region empty, G-AX skips; no A-consumed, no A-reference, no kind-3. Leg1 snapshot capture ↔ orig=dict(rcParams.copy()); Leg2 assocErase snapshot "backend" ↔ del orig['backend'] (the fix); Leg3 dictUpdate final snapshot ↔ dict.update(rcParams,orig) in finally (live rcParams at exit = final). Body callees (rc_file, rcParams.update) legitimately subsumed into input `final` via net-effect model — no separate A-reference required. Domain invariant (backend always in orig) documented; assocErase is total so model faithful regardless of key presence. R legs mechanically covered by G-CONF. Audit passes.

VERDICT: SOUND. ≥6 distinct same-spec wrong impls attempted (partial-domain=atk_5, boundary/wrong-key=atk_3, control-flow-effect=atk_6, ungrounded-oracle echo=atk_echo, prepatch=atk_1, identity=atk_2, direction-swap=atk_4); none with a closing clean-axiom proof has a non-resolving faithful patch. The structural barrier (total unconditional exact equality) makes closing-but-non-resolving impossible.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample exists. The postcondition `problem_spec_restoreSettings orig final result := result = applyRestore orig final` is a TOTAL, UNCONDITIONAL, pointwise equality with no preconditions. Any impl whose `correct_restoreSettings` closes (with clean axioms) must satisfy `implementation orig final = applyRestore orig final` for ALL (orig, final) — i.e. it is extensionally equal to `applyRestore`, and therefore produces the identical result on every input including the F2P scenario, so its faithful patch necessarily resolves. A closing-but-non-resolving impl is impossible by construction. Discriminating witness for wrong impls: orig=[("backend","agg"),("x","1")], final=[("backend","aardvark"),("x","9")] ⇒ applyRestore=[("backend","aardvark"),("x","1")] (backend kept) whereas prepatch/atk_1 gives [("backend","agg"),("x","1")] (backend reverted). The `rfl`-based equality cannot close for any impl differing on this input.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Temporarily overriding a global configuration mapping, then restoring it.

A scoped configuration manager snapshots a global settings mapping on entry,
lets a body of code run (which may freely change the values stored in the
mapping), and on exit puts the previously-recorded values back. The mapping is a
collection of named string-valued settings with a stable set of keys; one of
those keys, `"backend"`, names the active rendering backend.

The restore must reinstate every recorded setting EXCEPT the rendering backend:
the value chosen for `"backend"` while the body was running is left in place,
because the backend selection is meant to outlive the scoped override. All other
settings revert to the values they held when the manager was entered.

We model the manager's net effect on the mapping as a pure function of two
observations: the mapping captured on entry (`orig`) and the mapping present when
the body has finished (`final`). The restored mapping keeps `final`'s value for
`"backend"` and `orig`'s value for every other key.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The restore's
-- per-key behavior (which keys revert and which is kept) is modeled DEEPLY over
-- the observable mapping values, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A settings mapping: named string-valued entries with (in practice) unique
keys and a stable key set. -/
abbrev Settings := List (String × String)

/-- Overwrite the value at key `k` with `v`, keeping position; append if absent.
This is the per-key effect of overlaying one mapping onto another. -/
def assocSet : Settings → String → String → Settings
  | [],            k, v => [(k, v)]
  | (k', v') :: r, k, v => if k' = k then (k, v) :: r else (k', v') :: assocSet r k v

/-- Overlay every entry of `upd` onto `cur` (cur's entries are overwritten by
upd's; the result follows cur's order, with absent keys appended). -/
def dictUpdate (cur upd : Settings) : Settings :=
  upd.foldl (fun acc kv => assocSet acc kv.1 kv.2) cur

/-- Drop every entry whose key equals `k`. -/
def assocErase (m : Settings) (k : String) : Settings :=
  m.filter (fun kv => kv.1 != k)

/-- The net effect of the scoped manager's restore on the mapping: overlay the
entry snapshot onto the post-body mapping, but with the `"backend"` entry removed
from the snapshot first so the backend chosen inside the scope survives. -/
def applyRestore (orig final : Settings) : Settings :=
  dictUpdate final (assocErase orig "backend")
-- pure-end

-- post-conditions-start
/-- The restored mapping is exactly the post-body mapping with every recorded
setting reinstated EXCEPT the rendering backend, whose post-body value is kept. -/
def problem_spec_restoreSettings (orig final : Settings) (result : Settings) : Prop :=
  result = applyRestore orig final
-- post-conditions-end

-- impl-start
def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
  let mut snapshot := orig
  snapshot := assocErase snapshot "backend"
  return dictUpdate final snapshot
-- impl-end

-- proof-start
theorem correct_restoreSettings : ∀ (orig final : Settings),
    problem_spec_restoreSettings orig final
      (implementation_restoreSettings orig final) := by
  intro orig final
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True verified for ALL 8 files (atk_1..6, atk_echo, atk_pos) via swebench_unified.markers.same_spec (lean). Command per file: `bash scripts/lean_verify.sh <f>.lean`, run concurrently in 2 batches of 4.

### ATTACK RESULTS (exit codes):
- atk_1 (prepatch bug: no assocErase, reverts backend): EXIT 1 (does NOT close). prepatch_reproduced=true.
- atk_2 (identity impl `:= final`, no restore): EXIT 1.
- atk_3 (wrong key erased: "interactive" instead of "backend"): EXIT 1.
- atk_4 (swapped overlay direction: dictUpdate orig (erase final)): EXIT 1.
- atk_5 (partial-domain: only erase backend when orig.length>1): EXIT 1.
- atk_6 (control-flow-effect: correct restore then force backend back to orig's value): EXIT 1.
- atk_echo (ungrounded-oracle echo: `:= applyRestore orig final`): EXIT 0, CLOSES. `#print axioms correct_restoreSettings` => 'does not depend on any axioms' (clean).
- atk_pos (positive control = gold impl): EXIT 0, CLOSES, clean axioms.

All 6 wrong impls used a strong tactic-soup proof (first | rfl | decide | simp_all[...] | funext... | unfold...) so any secretly-equal impl WOULD have closed; none did. Only the two impls extensionally equal to applyRestore (echo, pos) close.

RESOLVE (protocol step 2): both closing clean-axiom impls compute exactly applyRestore orig final = the gold post-patch restore (dict.update(final, orig - {'backend'})), so their faithful materialized patch IS the gold patch. Ran it through the official harness: `run_resolve('matplotlib__matplotlib-23299', gold_patch, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So verify⇒correct holds for every closing impl; spec is NOT broken.

REFINEMENT.MD AUDIT (step 3): 3 legs, all tagged R (type refinement); axioms region empty, G-AX skips; no A-consumed, no A-reference, no kind-3. Leg1 snapshot capture ↔ orig=dict(rcParams.copy()); Leg2 assocErase snapshot "backend" ↔ del orig['backend'] (the fix); Leg3 dictUpdate final snapshot ↔ dict.update(rcParams,orig) in finally (live rcParams at exit = final). Body callees (rc_file, rcParams.update) legitimately subsumed into input `final` via net-effect model — no separate A-reference required. Domain invariant (backend always in orig) documented; assocErase is total so model faithful regardless of key presence. R legs mechanically covered by G-CONF. Audit passes.

VERDICT: SOUND. ≥6 distinct same-spec wrong impls attempted (partial-domain=atk_5, boundary/wrong-key=atk_3, control-flow-effect=atk_6, ungrounded-oracle echo=atk_echo, prepatch=atk_1, identity=atk_2, direction-swap=atk_4); none with a closing clean-axiom proof has a non-resolving faithful patch. The structural barrier (total unconditional exact equality) makes closing-but-non-resolving impossible.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical checks: (1) scripts/lean_verify.sh on Solution.lean exits 0 (compiles, no sorry). (2) `#print axioms correct_restoreSettings` => 'does not depend on any axioms' — proof is genuine, not sorryAx. (3) same_spec(Solution, Solution_prepatch, LeanBackend) = True — spec region (axioms/pure/post-conditions) byte-identical; the fix (assocErase snapshot "backend") sits only in the impl region, and the prepatch carries `sorry` (G-DIFF as intended). Semantic faithfulness: the spec applyRestore orig final = dictUpdate final (assocErase orig "backend") faithfully models the post-patch rc_context restore verified against the real worktree at base_commit 3eadeacc (worktree already carries gold patch: `orig = dict(rcParams.copy()); del orig['backend']; ... finally: dict.update(rcParams, orig)`). G-CONF conformance_check.py passes (120k inputs, 0 disagreements). Independent 300k-input differential of the Lean spec against GENUINE Python dict.update/del semantics: 0 divergences, order-preserving. Out-of-domain probes (mismatched key sets, orig extra keys) also match. Backend key correctly keeps final's value; all other keys revert to orig — matches F2P test_no_backend_reset_rccontext. Spec is deep, not over-strong; no in-domain input makes the modeled function disagree with the real callee.

Counterexample / evidence:

```
n/a — no in-domain counterexample. Out-of-domain KeyError case shown above is precluded by the rcParams always-has-'backend' invariant.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (hard_failures=[], warnings=[]); spec-region byte-identity confirmed via markers.same_spec (post vs prepatch True). Independent semantic review vs the SOLVER-VISIBLE problem_statement only (hints_text excluded):

Public problem_statement baseline: fully describes the bug symptom — get_backend() clears figures from Gcf.figs when the first figure was created inside rc_context; names rc_context, get_backend, and 'backend'. It does not state the fix mechanism.

Spec view discloses ONLY the irreducible correctness postcondition: 'the restore must reinstate every recorded setting EXCEPT the rendering backend; the value chosen for backend while the body was running is left in place.' This is abstracted — matplotlib/rcParams/rc_context/get_backend are NOT named (rendered as 'scoped configuration manager' / 'global settings mapping'). No file path (lib/matplotlib/__init__.py), no gold-diff tokens (del orig['backend'], dict(rcParams.copy())), no diff markers, no patched repo symbol echoed, no bug/fix narration lexicon.

The single distinctive retained term, 'backend', is already public in the problem_statement. Stating which keys revert and which survive is the unavoidable specification of correctness for any snapshot/restore manager — the irreducible content a verified spec must state, not a transcription or localization of the gold edit. The spec reveals WHAT correct behavior is, never the HOW/WHERE of the edit beyond what the public bug report already implies.

Verified preliminaries: lean_verify.sh not re-run here but recorded gates show G-GOLD/G-DIFF/G-EQ pass; the panel-3 decision does not hinge on compile status. Verdict: NO-LEAKAGE — consistent with the recorded audit and the G-LEAK mechanical pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

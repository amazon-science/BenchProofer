# P2 adversarial audit — django__django-14315

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,15 +40,16 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_runshell_env
     (osEnviron : List (String × String))
     (env : Option (List (String × String))) : Option (List (String × String)) :=
   Id.run do
   let mut env := env
   if envIsSet env then
+    env := none
+  else
     env := some (combineEnv osEnviron (env.getD []))
-  else
-    env := none
   return env
 -- impl-end
 
@@ -86,6 +87,7 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_client_env
     (env : List (String × String)) : Option (List (String × String)) :=
   Id.run do
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,16 +40,12 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_runshell_env
     (osEnviron : List (String × String))
     (env : Option (List (String × String))) : Option (List (String × String)) :=
   Id.run do
-  let mut env := env
-  if envIsSet env then
-    env := some (combineEnv osEnviron (env.getD []))
-  else
-    env := none
-  return env
+  return some (combineEnv osEnviron (env.getD []))
 -- impl-end
 
 -- proof-start
@@ -86,6 +82,7 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_client_env
     (env : List (String × String)) : Option (List (String × String)) :=
   Id.run do
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,6 +40,7 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_runshell_env
     (osEnviron : List (String × String))
     (env : Option (List (String × String))) : Option (List (String × String)) :=
@@ -86,12 +87,11 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_client_env
     (env : List (String × String)) : Option (List (String × String)) :=
   Id.run do
-  if env.isEmpty then
-    return none
-  return some env
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,6 +40,7 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_runshell_env
     (osEnviron : List (String × String))
     (env : Option (List (String × String))) : Option (List (String × String)) :=
@@ -86,12 +87,13 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_client_env
     (env : List (String × String)) : Option (List (String × String)) :=
   Id.run do
   if env.isEmpty then
-    return none
-  return some env
+    return some env
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,13 +40,14 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_runshell_env
     (osEnviron : List (String × String))
     (env : Option (List (String × String))) : Option (List (String × String)) :=
   Id.run do
   let mut env := env
   if envIsSet env then
-    env := some (combineEnv osEnviron (env.getD []))
+    env := some (combineEnv (env.getD []) osEnviron)
   else
     env := none
   return env
@@ -86,6 +87,7 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_client_env
     (env : List (String × String)) : Option (List (String × String)) :=
   Id.run do
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,15 +40,19 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_runshell_env
     (osEnviron : List (String × String))
     (env : Option (List (String × String))) : Option (List (String × String)) :=
   Id.run do
   let mut env := env
-  if envIsSet env then
-    env := some (combineEnv osEnviron (env.getD []))
-  else
-    env := none
+  match env with
+  | some [_] => env := none
+  | _ =>
+    if envIsSet env then
+      env := some (combineEnv osEnviron (env.getD []))
+    else
+      env := none
   return env
 -- impl-end
 
@@ -86,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_client_env
     (env : List (String × String)) : Option (List (String × String)) :=
   Id.run do
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- Overlay a set of named overrides onto an ambient set of named values,
producing the combined environment in which the overrides take precedence on any
shared name. This is the unchanged ambient-overlay operation used only when there
is at least one override to apply; the desired behaviour below does not depend on
its internal result, so no property of it is consumed by the proof (its agreement
with the real overlay is exercised separately). -/
opaque combineEnv :
  List (String × String) → List (String × String) → List (String × String)
-- axioms-end

-- pure-start
/-- Whether a (possibly-absent) environment is considered "present": it is
present exactly when it is supplied and contains at least one entry. An absent
environment and a supplied-but-empty one are both treated as not present. -/
def envIsSet (env : Option (List (String × String))) : Bool :=
  match env with
  | none => false
  | some kvs => !kvs.isEmpty
-- pure-end

-- post-conditions-start
/-- Desired behaviour for resolving the environment handed to a spawned child.
The input is the ambient environment and an optionally-supplied override
environment. When the override is not present (absent, or supplied but empty),
the resolved environment is "absent" so the child inherits the ambient one. When
the override is present (supplied and non-empty), the resolved environment is the
ambient one overlaid with the overrides. The result is fully determined by the
two cases. -/
def problem_spec_runshell_env
    (osEnviron : List (String × String))
    (env : Option (List (String × String)))
    (result : Option (List (String × String))) : Prop :=
  (envIsSet env = false → result = none) ∧
  (∀ kvs, env = some kvs → kvs ≠ [] →
      result = some (combineEnv osEnviron kvs))
-- post-conditions-end

-- impl-start
def implementation_runshell_env
    (osEnviron : List (String × String))
    (env : Option (List (String × String))) : Option (List (String × String)) :=
  Id.run do
  let mut env := env
  if envIsSet env then
    env := some (combineEnv osEnviron (env.getD []))
  else
    env := none
  return env
-- impl-end

-- proof-start
theorem correct_runshell_env :
    ∀ (osEnviron : List (String × String))
      (env : Option (List (String × String))),
    problem_spec_runshell_env osEnviron env
      (implementation_runshell_env osEnviron env) := by
  intro osEnviron env
  unfold problem_spec_runshell_env implementation_runshell_env
  simp only [Id.run]
  refine ⟨?_, ?_⟩
  · intro h
    simp only [h]
    rfl
  · intro kvs henv hne
    subst henv
    have h1 : envIsSet (some kvs) = true := by
      simp [envIsSet, hne]
    simp only [h1, if_true, Option.getD_some]
    rfl
-- proof-end

-- post-conditions-start
/-- Desired behaviour for the override environment a command builder reports. The
builder always assembles a concrete set of overrides (possibly empty). When that
set is empty it must be reported as "absent" (so downstream the ambient
environment is inherited); when it is non-empty it is reported unchanged. -/
def problem_spec_client_env
    (env : List (String × String))
    (result : Option (List (String × String))) : Prop :=
  (env = [] → result = none) ∧
  (env ≠ [] → result = some env)
-- post-conditions-end

-- impl-start
def implementation_client_env
    (env : List (String × String)) : Option (List (String × String)) :=
  Id.run do
  if env.isEmpty then
    return none
  return some env
-- impl-end

-- proof-start
theorem correct_client_env :
    ∀ (env : List (String × String)),
    problem_spec_client_env env (implementation_client_env env) := by
  intro env
  unfold problem_spec_client_env implementation_client_env
  simp only [Id.run]
  refine ⟨?_, ?_⟩
  · intro h
    simp only [h, List.isEmpty_nil, if_true]
    rfl
  · intro hne
    have he : env.isEmpty = false := by simp [hne]
    simp only [he]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Twin-artifact bundle (2 independent functions). Both specs are TOTAL, fully-deterministic relations pinning every input to a unique value: problem_spec_runshell_env (envIsSet env=false -> result=none [covers none and some []]; some kvs, kvs<>[] -> some (combineEnv osEnviron kvs)); problem_spec_client_env ([]->none; <>[]->some env). Any behaviorally-wrong impl yields a FALSE theorem, unprovable in sound Lean.

Project root corrected to; used venv python python for same_spec. All 6 attacks + 2 prepatch reproductions confirmed same_spec=True; pos_control same_spec=True.

Positive control: `bash scripts/lean_verify.sh .../pos_control.lean` exit 0; #print axioms correct_runshell_env / correct_client_env = [propext, Quot.sound] (clean, no sorryAx, no consumed opaque property).

6 DISTINCT same-spec wrong impls (impl-region-only edits, spec/axioms/pure/post byte-identical):
- atk_1: fn1 control-flow branch swap (present->none, absent->overlay) -> exit 1.
- atk_2: fn1 ungrounded-oracle echo (always some(combineEnv ...), never none) -> exit 1.
- atk_3: fn2 always none -> exit 1.
- atk_4: fn2 branch swap (empty->some env, nonempty->none) -> exit 1.
- atk_5 (A-LEG, key): fn1 combineEnv ARG-ORDER swap `some (combineEnv (env.getD []) osEnviron)` -> exit 1. Fails because combineEnv is opaque with NO consumed property, so the spec's `some (combineEnv osEnviron kvs)` pins argument order (os.environ first, overrides win) and the swap is unprovable. Confirms the A-reference correspondence to `{**os.environ, **env}` is genuinely constrained (also enforced by G-CONF: 240011 inputs, 0 disagreements, seed 14315).
- atk_6: fn1 partial-domain (singleton override -> none) -> exit 1.

All ran via `bash scripts/lean_verify.sh <file>` concurrently (<=4 jobs). To rule out that only the carried gold proof fails, I also built *_auto variants replacing the proof body with aggressive automation (unfold; simp_all[envIsSet,Id.run]; aesop; fallbacks) for atk_1,2,3,4,5,6 — every one exit 1 (unsolved goals / no progress). No wrong impl closes with any proof.

prepatch_reproduced=true: prepatch_1 (real fn1 bug, else-branch omitted) exit 1; prepatch_2 (real fn2 bug, return some env) exit 1 — both fail against frozen spec (G-DIFF signal).

No verifying attack exists => no faithful patch to materialize/resolve (patches={}); no run_resolve run was needed and none is missing.

refinement.md audit: legs are all R / A-reference / I; 0 A-consumed rows; NO kind-3 (changed-inexpressible) op. Single A-reference leg (combineEnv <-> dict-spread merge) correspondence holds — validated by spec arg-order (atk_5) + G-CONF shadow with real merge; consistent with G-AX skip (no combineEnv_prop axiom, no dead axiom). No spec break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
import Mathlib
-- imports-end

-- axioms-start
/-- Overlay a set of named overrides onto an ambient set of named values,
producing the combined environment in which the overrides take precedence on any
shared name. This is the unchanged ambient-overlay operation used only when there
is at least one override to apply; the desired behaviour below does not depend on
its internal result, so no property of it is consumed by the proof (its agreement
with the real overlay is exercised separately). -/
opaque combineEnv :
  List (String × String) → List (String × String) → List (String × String)
-- axioms-end

-- pure-start
/-- Whether a (possibly-absent) environment is considered "present": it is
present exactly when it is supplied and contains at least one entry. An absent
environment and a supplied-but-empty one are both treated as not present. -/
def envIsSet (env : Option (List (String × String))) : Bool :=
  match env with
  | none => false
  | some kvs => !kvs.isEmpty
-- pure-end

-- post-conditions-start
/-- Desired behaviour for resolving the environment handed to a spawned child.
The input is the ambient environment and an optionally-supplied override
environment. When the override is not present (absent, or supplied but empty),
the resolved environment is "absent" so the child inherits the ambient one. When
the override is present (supplied and non-empty), the resolved environment is the
ambient one overlaid with the overrides. The result is fully determined by the
two cases. -/
def problem_spec_runshell_env
    (osEnviron : List (String × String))
    (env : Option (List (String × String)))
    (result : Option (List (String × String))) : Prop :=
  (envIsSet env = false → result = none) ∧
  (∀ kvs, env = some kvs → kvs ≠ [] →
      result = some (combineEnv osEnviron kvs))
-- post-conditions-end

-- impl-start
def implementation_runshell_env
    (osEnviron : List (String × String))
    (env : Option (List (String × String))) : Option (List (String × String)) :=
  Id.run do
  let mut env := env
  if envIsSet env then
    env := some (combineEnv osEnviron (env.getD []))
  else
    env := none
  return env
-- impl-end

-- proof-start
theorem correct_runshell_env :
    ∀ (osEnviron : List (String × String))
      (env : Option (List (String × String))),
    problem_spec_runshell_env osEnviron env
      (implementation_runshell_env osEnviron env) := by
  intro osEnviron env
  unfold problem_spec_runshell_env implementation_runshell_env
  simp only [Id.run]
  refine ⟨?_, ?_⟩
  · intro h
    simp only [h]
    rfl
  · intro kvs henv hne
    subst henv
    have h1 : envIsSet (some kvs) = true := by
      simp [envIsSet, hne]
    simp only [h1, if_true, Option.getD_some]
    rfl
-- proof-end

-- post-conditions-start
/-- Desired behaviour for the override environment a command builder reports. The
builder always assembles a concrete set of overrides (possibly empty). When that
set is empty it must be reported as "absent" (so downstream the ambient
environment is inherited); when it is non-empty it is reported unchanged. -/
def problem_spec_client_env
    (env : List (String × String))
    (result : Option (List (String × String))) : Prop :=
  (env = [] → result = none) ∧
  (env ≠ [] → result = some env)
-- post-conditions-end

-- impl-start
def implementation_client_env
    (env : List (String × String)) : Option (List (String × String)) :=
  Id.run do
  if env.isEmpty then
    return none
  return some env
-- impl-end

-- proof-start
theorem correct_client_env :
    ∀ (env : List (String × String)),
    problem_spec_client_env env (implementation_client_env env) := by
  intro env
  unfold problem_spec_client_env implementation_client_env
  simp only [Id.run]
  refine ⟨?_, ?_⟩
  · intro h
    simp only [h, List.isEmpty_nil, if_true]
    rfl
  · intro hne
    have he : env.isEmpty = false := by simp [hne]
    simp only [he]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Twin-artifact bundle (2 independent functions). Both specs are TOTAL, fully-deterministic relations pinning every input to a unique value: problem_spec_runshell_env (envIsSet env=false -> result=none [covers none and some []]; some kvs, kvs<>[] -> some (combineEnv osEnviron kvs)); problem_spec_client_env ([]->none; <>[]->some env). Any behaviorally-wrong impl yields a FALSE theorem, unprovable in sound Lean.

Project root corrected to; used venv python python for same_spec. All 6 attacks + 2 prepatch reproductions confirmed same_spec=True; pos_control same_spec=True.

Positive control: `bash scripts/lean_verify.sh .../pos_control.lean` exit 0; #print axioms correct_runshell_env / correct_client_env = [propext, Quot.sound] (clean, no sorryAx, no consumed opaque property).

6 DISTINCT same-spec wrong impls (impl-region-only edits, spec/axioms/pure/post byte-identical):
- atk_1: fn1 control-flow branch swap (present->none, absent->overlay) -> exit 1.
- atk_2: fn1 ungrounded-oracle echo (always some(combineEnv ...), never none) -> exit 1.
- atk_3: fn2 always none -> exit 1.
- atk_4: fn2 branch swap (empty->some env, nonempty->none) -> exit 1.
- atk_5 (A-LEG, key): fn1 combineEnv ARG-ORDER swap `some (combineEnv (env.getD []) osEnviron)` -> exit 1. Fails because combineEnv is opaque with NO consumed property, so the spec's `some (combineEnv osEnviron kvs)` pins argument order (os.environ first, overrides win) and the swap is unprovable. Confirms the A-reference correspondence to `{**os.environ, **env}` is genuinely constrained (also enforced by G-CONF: 240011 inputs, 0 disagreements, seed 14315).
- atk_6: fn1 partial-domain (singleton override -> none) -> exit 1.

All ran via `bash scripts/lean_verify.sh <file>` concurrently (<=4 jobs). To rule out that only the carried gold proof fails, I also built *_auto variants replacing the proof body with aggressive automation (unfold; simp_all[envIsSet,Id.run]; aesop; fallbacks) for atk_1,2,3,4,5,6 — every one exit 1 (unsolved goals / no progress). No wrong impl closes with any proof.

prepatch_reproduced=true: prepatch_1 (real fn1 bug, else-branch omitted) exit 1; prepatch_2 (real fn2 bug, return some env) exit 1 — both fail against frozen spec (G-DIFF signal).

No verifying attack exists => no faithful patch to materialize/resolve (patches={}); no run_resolve run was needed and none is missing.

refinement.md audit: legs are all R / A-reference / I; 0 A-consumed rows; NO kind-3 (changed-inexpressible) op. Single A-reference leg (combineEnv <-> dict-spread merge) correspondence holds — validated by spec arg-order (atk_5) + G-CONF shadow with real merge; consistent with G-AX skip (no combineEnv_prop axiom, no dead axiom). No spec break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: could NOT break the spec. (1) Spec regions byte-identical across Solution + both prepatch variants (same_spec=True); recorded region_hashes match current file exactly — no drift/tamper. (2) Solution.lean compiles exit 0; #print axioms = [propext, Quot.sound] only (no sorryAx) — proof genuine. (3) Modeling faithful to real repo @ base 187118203: Function 1 (runshell env: `env = {**os.environ, **env} if env else None`) — envIsSet (none/some[]→false, some(_::_)→true) exactly mirrors Python bool(env) which is falsy for both None and {}; opaque combineEnv⇄{**os.environ,**env} validated by G-CONF vs the REAL dict merge (240011 inputs, 0 disagreements). Function 2 (settings_to_cmd_args_env: `return args, (env or None)`) — spec env=[]→none, env≠[]→some env matches {}-falsy→None and non-empty→env. All F2P boundary inputs (env∈{None,{}}→None; empty postgresql env→None) satisfy the spec. Tested candidate diverging inputs: env=none, env=some[], env=some[(k,v)], empty/non-empty client env — every one agrees between spec and real callee. No input found where the modeled function disagrees with the real repo behavior; spec is not too strong (empty→absent discriminator is exactly the gold fix, not an over-constraint). combineEnv opacity + G-CONF closes the only abstraction. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = abstract post-conditions + docstrings + opaque combineEnv + envIsSet helper; impl/proof regions properly elided (verified via markers.spec_view with LeanBackend). The two post-conditions ('envIsSet env = false → result = none' / 'env = [] → result = none, else unchanged') formalize exactly the behavior the PUBLIC problem_statement already states: 'postgresql client returns empty dict instead of None for env; as a result os.environ is not used and empty env passed to subprocess' — i.e. empty env must normalize to None so os.environ is inherited. No spec-view line quotes the gold patch tokens ('{**os.environ, **env} if env else None', 'env or None') or reveals an implementation strategy beyond the public statement. The combineEnv docstring describes only the UNCHANGED overlay (present in both pre/post code), not the fix's discriminator. Gates recorded G-EQ pass (6 attacks, none break), G-DIFF pass (both prepatch variants fail). No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

# P2 adversarial audit — django__django-16493

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_always_none.lean`, `atk_always_some.lean`, `atk_flip.lean`, `atk_record_eval.lean`, `atk_wrong_fallback.lean`, `atk_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no wrong impl closes. The spec problem_spec_recordedStorage pins result to one exact expression: (let s := oc.getD es; if s = ds then none else some s). Any verifying impl must be pointwise-equal to that expression, hence extensionally identical to gold and resolving. Every attack was shown to disagree with the spec on a concrete input, so its correct_recordedStorage is a false ∀-statement and unprovable (lean_verify exit 1, genuine 'unsolved goals' reducing to ⊢ False or non-derivable equalities). Example disagreements: prepatch(oc=some 1,es=0,ds=0): spec=some 1 vs impl=none; always_some(oc=none,es=0,ds=0): spec=none vs some 0; record_eval(oc=some 1,es=2,ds=0): spec=some 1 vs some 2; wrong_fallback/oracle_echo(oc=none,es=5,ds=0): spec=some 5 vs none.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,7 @@
     Option Nat := Id.run do
   let storage := originalCallable.getD evaluatedStorage
   let mut result : Option Nat := none
-  if storage ≠ defaultStorage then
+  if evaluatedStorage ≠ defaultStorage then
     result := some storage
   return result
 -- impl-end
```

Attack 2 — `atk_always_none.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,11 +37,8 @@
 def implementation_recordedStorage
     (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :
     Option Nat := Id.run do
-  let storage := originalCallable.getD evaluatedStorage
-  let mut result : Option Nat := none
-  if storage ≠ defaultStorage then
-    result := some storage
-  return result
+  let _storage := originalCallable.getD evaluatedStorage
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_always_some.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,10 +38,7 @@
     (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :
     Option Nat := Id.run do
   let storage := originalCallable.getD evaluatedStorage
-  let mut result : Option Nat := none
-  if storage ≠ defaultStorage then
-    result := some storage
-  return result
+  return some storage
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_flip.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,9 +38,9 @@
     (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :
     Option Nat := Id.run do
   let storage := originalCallable.getD evaluatedStorage
-  let mut result : Option Nat := none
+  let mut result : Option Nat := some storage
   if storage ≠ defaultStorage then
-    result := some storage
+    result := none
   return result
 -- impl-end
 
```

Attack 5 — `atk_record_eval.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
   let storage := originalCallable.getD evaluatedStorage
   let mut result : Option Nat := none
   if storage ≠ defaultStorage then
-    result := some storage
+    result := some evaluatedStorage
   return result
 -- impl-end
 
```

Attack 6 — `atk_wrong_fallback.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,7 @@
 def implementation_recordedStorage
     (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :
     Option Nat := Id.run do
-  let storage := originalCallable.getD evaluatedStorage
+  let storage := originalCallable.getD defaultStorage
   let mut result : Option Nat := none
   if storage ≠ defaultStorage then
     result := some storage
```

Attack 7 — `atk_oracle_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -36,12 +36,10 @@
 -- impl-start
 def implementation_recordedStorage
     (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :
-    Option Nat := Id.run do
-  let storage := originalCallable.getD evaluatedStorage
-  let mut result : Option Nat := none
-  if storage ≠ defaultStorage then
-    result := some storage
-  return result
+    Option Nat :=
+  match originalCallable with
+  | some c => if c = defaultStorage then none else some c
+  | none => none
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The configuration that
-- precedes the modeled decision (the surrounding serialization that produces the
-- other recorded entries) is orthogonal to which storage reference is recorded,
-- and the identity comparison itself is modeled DEEPLY below rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- When a field's configuration is serialized into a reconstructable form, the
storage reference that gets recorded is the *original* storage specification: the
caller-supplied callable when one was supplied, otherwise the configured storage
instance. That reference is recorded only when it differs from the default
storage; when it coincides with the default it is left out entirely.

Storage objects are compared by identity, modeled here as a numeric identity
(`Nat`); `none` means no storage reference is recorded, `some s` means the
reference `s` is recorded. Every component of the decision is pinned to the
inputs: the recorded reference, and whether one is recorded at all, are fully
determined by the original specification and the default identity. -/
def problem_spec_recordedStorage
    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat)
    (result : Option Nat) : Prop :=
  result =
    (let storage := originalCallable.getD evaluatedStorage
     if storage = defaultStorage then none else some storage)
-- post-conditions-end

-- impl-start
def implementation_recordedStorage
    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :
    Option Nat :=
  let storage := match originalCallable with
    | some c => c
    | none => evaluatedStorage
  if storage = defaultStorage then none else some storage
-- impl-end

-- proof-start
theorem correct_recordedStorage :
    ∀ (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat),
    problem_spec_recordedStorage originalCallable evaluatedStorage defaultStorage
      (implementation_recordedStorage originalCallable evaluatedStorage defaultStorage) := by
  intro originalCallable evaluatedStorage defaultStorage
  unfold problem_spec_recordedStorage implementation_recordedStorage
  cases originalCallable with
  | none => simp [Option.getD]
  | some c => simp [Option.getD]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. same_spec confirmed True for all 8 files (spec region imports/axioms/pure/post-conditions byte-identical): `python -c "from swebench_unified.markers import same_spec; ..."` -> all True.

ATTACKS (7 distinct wrong impls, ≥ the required 5). Each: copy Solution.lean header (through post-conditions-end) byte-identical, edit ONLY impl region + reuse gold proof skeleton. Verified concurrently (2 background batches of 4) via `bash scripts/lean_verify.sh <file>`:
  1. atk_prepatch (prepatch bug: tests evaluatedStorage≠defaultStorage) -> EXIT 1, unsolved goal ⊢ ¬evaluatedStorage=defaultStorage (not interderivable). PREPATCH REPRODUCED unclosable, matching verdict.md/refinement.md G-DIFF signal.
  2. atk_always_none (return none) -> EXIT 1, ⊢ False (neg case).
  3. atk_always_some (return some storage, drop guard) -> EXIT 1, ⊢ False (pos case).
  4. atk_flip (inverted guard) -> EXIT 1, ⊢ False (neg case).
  5. atk_record_eval (record evaluatedStorage instead of original reference) -> EXIT 1, ⊢ evaluatedStorage = oc.getD evaluatedStorage (not derivable).
  6. atk_wrong_fallback (getD defaultStorage instead of evaluatedStorage) -> EXIT 1, mismatched if-expression, not derivable.
  7. atk_oracle_echo (match on originalCallable only; none->none, dropping the evaluatedStorage fallback) -> EXIT 1, unsolved goals in both cases.
All 7 fail with GENUINE `error: unsolved goals` (grep confirms 1-2 unsolved-goal errors each), not linter/skeleton artifacts: each goal reduces to a false proposition, and each impl provably disagrees with the pinned spec expression on a concrete input (see counterexample). Therefore NONE closes.

STEP-2 TRIGGER EMPTY: since no wrong impl produced a closing clean-axiom proof, there is no faithful patch to materialize/resolve. patches={} accordingly. (verify⇏correct cannot arise: the only way to close is to equal the gold expression pointwise, which resolves.)

POSITIVE CONTROL: pos_control.lean — surface-different correct impl (match form computing the original reference, then `if storage=defaultStorage then none else some storage`), proof by `cases originalCallable` + `simp [Option.getD]`. lean_verify EXIT 0. `#print axioms correct_recordedStorage` -> `[propext]` (clean; no sorryAx, no _prop). same_spec True. Confirms the spec ADMITS the gold behavior and clean axioms are achievable — so the 7 non-closures are real spec strength, not an over-restrictive harness.

REFINEMENT.MD AUDIT: 6 legs, all tagged R or I (rows 1-4 R type/moved-op refinements, row 5 R changed-op = the fix's identity-test-against-original-reference, row 6 I). No A-consumed and no A-reference rows: axioms region empty, G-AX is a legitimate skip stub (axiom_check.py returns status=skip with reason 'no consumed axiom and no A-reference deep model'). No kind-3 changed-inexpressible op. The two touched callees (getattr-with-default -> Option.getD; `is not default_storage` identity test -> Nat inequality) are reproduced concretely as R ops, not abstracted behind a deep model — so there are no A-legs whose correspondence could break; A-leg audit passes vacuously. mapping.md type bijection (Python object identity <-> Nat, callable-presence <-> Option, recorded-key <-> some/none) is coherent and matches conformance_check.py's real-`is` differential shadow.

CONCLUSION: The frozen spec is functional and pins result exactly; verify ⇒ correct holds. ≥5 distinct attacks run, all fail to close, positive control closes with clean axioms, prepatch reproduced unclosable, refinement legs all R/I with vacuous-but-valid A-audit. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_always_none.lean`, `atk_always_some.lean`, `atk_flip.lean`, `atk_record_eval.lean`, `atk_wrong_fallback.lean`, `atk_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no wrong impl closes. The spec problem_spec_recordedStorage pins result to one exact expression: (let s := oc.getD es; if s = ds then none else some s). Any verifying impl must be pointwise-equal to that expression, hence extensionally identical to gold and resolving. Every attack was shown to disagree with the spec on a concrete input, so its correct_recordedStorage is a false ∀-statement and unprovable (lean_verify exit 1, genuine 'unsolved goals' reducing to ⊢ False or non-derivable equalities). Example disagreements: prepatch(oc=some 1,es=0,ds=0): spec=some 1 vs impl=none; always_some(oc=none,es=0,ds=0): spec=none vs some 0; record_eval(oc=some 1,es=2,ds=0): spec=some 1 vs some 2; wrong_fallback/oracle_echo(oc=none,es=5,ds=0): spec=some 5 vs none.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_always_none.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_always_some.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_flip.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_record_eval.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_wrong_fallback.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_oracle_echo.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The configuration that
-- precedes the modeled decision (the surrounding serialization that produces the
-- other recorded entries) is orthogonal to which storage reference is recorded,
-- and the identity comparison itself is modeled DEEPLY below rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- When a field's configuration is serialized into a reconstructable form, the
storage reference that gets recorded is the *original* storage specification: the
caller-supplied callable when one was supplied, otherwise the configured storage
instance. That reference is recorded only when it differs from the default
storage; when it coincides with the default it is left out entirely.

Storage objects are compared by identity, modeled here as a numeric identity
(`Nat`); `none` means no storage reference is recorded, `some s` means the
reference `s` is recorded. Every component of the decision is pinned to the
inputs: the recorded reference, and whether one is recorded at all, are fully
determined by the original specification and the default identity. -/
def problem_spec_recordedStorage
    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat)
    (result : Option Nat) : Prop :=
  result =
    (let storage := originalCallable.getD evaluatedStorage
     if storage = defaultStorage then none else some storage)
-- post-conditions-end

-- impl-start
def implementation_recordedStorage
    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :
    Option Nat :=
  let storage := match originalCallable with
    | some c => c
    | none => evaluatedStorage
  if storage = defaultStorage then none else some storage
-- impl-end

-- proof-start
theorem correct_recordedStorage :
    ∀ (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat),
    problem_spec_recordedStorage originalCallable evaluatedStorage defaultStorage
      (implementation_recordedStorage originalCallable evaluatedStorage defaultStorage) := by
  intro originalCallable evaluatedStorage defaultStorage
  unfold problem_spec_recordedStorage implementation_recordedStorage
  cases originalCallable with
  | none => simp [Option.getD]
  | some c => simp [Option.getD]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. same_spec confirmed True for all 8 files (spec region imports/axioms/pure/post-conditions byte-identical): `python -c "from swebench_unified.markers import same_spec; ..."` -> all True.

ATTACKS (7 distinct wrong impls, ≥ the required 5). Each: copy Solution.lean header (through post-conditions-end) byte-identical, edit ONLY impl region + reuse gold proof skeleton. Verified concurrently (2 background batches of 4) via `bash scripts/lean_verify.sh <file>`:
  1. atk_prepatch (prepatch bug: tests evaluatedStorage≠defaultStorage) -> EXIT 1, unsolved goal ⊢ ¬evaluatedStorage=defaultStorage (not interderivable). PREPATCH REPRODUCED unclosable, matching verdict.md/refinement.md G-DIFF signal.
  2. atk_always_none (return none) -> EXIT 1, ⊢ False (neg case).
  3. atk_always_some (return some storage, drop guard) -> EXIT 1, ⊢ False (pos case).
  4. atk_flip (inverted guard) -> EXIT 1, ⊢ False (neg case).
  5. atk_record_eval (record evaluatedStorage instead of original reference) -> EXIT 1, ⊢ evaluatedStorage = oc.getD evaluatedStorage (not derivable).
  6. atk_wrong_fallback (getD defaultStorage instead of evaluatedStorage) -> EXIT 1, mismatched if-expression, not derivable.
  7. atk_oracle_echo (match on originalCallable only; none->none, dropping the evaluatedStorage fallback) -> EXIT 1, unsolved goals in both cases.
All 7 fail with GENUINE `error: unsolved goals` (grep confirms 1-2 unsolved-goal errors each), not linter/skeleton artifacts: each goal reduces to a false proposition, and each impl provably disagrees with the pinned spec expression on a concrete input (see counterexample). Therefore NONE closes.

STEP-2 TRIGGER EMPTY: since no wrong impl produced a closing clean-axiom proof, there is no faithful patch to materialize/resolve. patches={} accordingly. (verify⇏correct cannot arise: the only way to close is to equal the gold expression pointwise, which resolves.)

POSITIVE CONTROL: pos_control.lean — surface-different correct impl (match form computing the original reference, then `if storage=defaultStorage then none else some storage`), proof by `cases originalCallable` + `simp [Option.getD]`. lean_verify EXIT 0. `#print axioms correct_recordedStorage` -> `[propext]` (clean; no sorryAx, no _prop). same_spec True. Confirms the spec ADMITS the gold behavior and clean axioms are achievable — so the 7 non-closures are real spec strength, not an over-restrictive harness.

REFINEMENT.MD AUDIT: 6 legs, all tagged R or I (rows 1-4 R type/moved-op refinements, row 5 R changed-op = the fix's identity-test-against-original-reference, row 6 I). No A-consumed and no A-reference rows: axioms region empty, G-AX is a legitimate skip stub (axiom_check.py returns status=skip with reason 'no consumed axiom and no A-reference deep model'). No kind-3 changed-inexpressible op. The two touched callees (getattr-with-default -> Option.getD; `is not default_storage` identity test -> Nat inequality) are reproduced concretely as R ops, not abstracted behind a deep model — so there are no A-legs whose correspondence could break; A-leg audit passes vacuously. mapping.md type bijection (Python object identity <-> Nat, callable-presence <-> Option, recorded-key <-> some/none) is coherent and matches conformance_check.py's real-`is` differential shadow.

CONCLUSION: The frozen spec is functional and pins result exactly; verify ⇒ correct holds. ≥5 distinct attacks run, all fail to close, positive control closes with clean axioms, prepatch reproduced unclosable, refinement legs all R/I with vacuous-but-valid A-audit. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-16493 lean bundle. Modeled projection = the storage-kwarg decision inside FileField.deconstruct (django/db/models/fields/files.py:293-300), i.e. which storage reference (if any) is recorded in kwargs['storage'].

Verification performed:
- Solution.lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry/error).
- `#print axioms correct_recordedStorage` -> [propext] only; NO sorryAx, so the proof is genuine (not a fake close).
- swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) = True: the spec region (axioms/pure/post-conditions) is byte-identical between the post-patch and prepatch variants, so the prepatch buggy impl is measured against the SAME frozen spec (G-DIFF integrity holds).
- Gold patch confirmed in dataset: hoist `storage = getattr(self, '_storage_callable', self.storage)` BEFORE the `is not default_storage` test; base_commit worktree (commit 2c7846d992) carries the buggy pre-hoist form, as expected.

Spec:  result = (let storage := originalCallable.getD evaluatedStorage; if storage = defaultStorage then none else some storage)
Patched Python: storage = _storage_callable if present else self.storage; kwargs['storage']=storage iff storage is not default_storage (else key absent).

Case analysis over the full model domain (originalCallable : Option Nat, evaluatedStorage, defaultStorage : Nat):
1. originalCallable = some c: real uses storage=_storage_callable=c and ignores self.storage, records c iff c is not default. Spec: getD yields c, records some c iff c != default. evaluatedStorage irrelevant in BOTH. Match, incl. the F2P discriminating case (a non-default callable c that evaluates to default: c != default => some c recorded).
2. originalCallable = none: real falls back to self.storage (evaluated) vs default; spec uses evaluatedStorage vs default. Match.
Identity: Python is/is-not maps to Nat equality via the mapping.md bijection (distinct objects -> distinct Nat; same object -> same Nat). Objects equal by == but not by `is` map to distinct Nats, consistent with `is`. No conflation either direction.

No reachable (or unreachable) input found where the modeled function disagrees with the real patched callee; the spec is a total deterministic equality exactly reproducing the pure identity-comparison decision. The reduced scope (name/path/args/max_length/upload_to unmodeled) is a coverage weakening, NOT a strengthening/drift, and does not make the modeled projection unfaithful. No spec-too-strong defect exists.

Confirmed FAITHFUL; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over Solution.lean: imports + axioms + pure + post-conditions regions; impl/proof elided) does NOT leak the gold edit beyond the public problem_statement.

Mechanical G-LEAK screen: PASS (hard_failures=[]). Verified independently: no diff markers, no patched file path (django/db/models/fields/files.py absent), no dotted module path, no gold-patch line reproduced, no spec-view identifier embedding a patched repo symbol, no bug/fix narration.

Semantic assessment: the problem_statement is itself highly explicit about the correct behavior — it publicly states that deconstruct tests `self.storage is not default_storage` against the *evaluated* version, that this is wrong for a callable returning default_storage, and that the callable should be recorded as a reference. The spec `problem_spec_recordedStorage` encodes exactly that intended post-condition: record the ORIGINAL storage specification (callable when supplied via `originalCallable.getD evaluatedStorage`, else the evaluated instance), only when it differs from default. Every element of the spec is already derivable from the public problem_statement, so the spec reveals nothing about the gold edit beyond what the task already discloses. Comments describe behavior abstractly ('serialized into a reconstructable form', 'recorded only when it differs from the default') with no edit/bug/fix narration.

Identifiers are abstracted (originalCallable/evaluatedStorage/defaultStorage/recordedStorage); patched symbol `deconstruct` appears nowhere in the spec view (and is itself public), and `_storage_callable` does not appear.

Out-of-scope artifacts: refinement.md and mapping.md do quote the gold patch snippet and `_storage_callable` verbatim, but these are construction/auditor documents, NOT part of the consumer-visible spec view that panel_3 judges. No LEAKAGE.

No RELAXED_LEAKAGE.md and meta relaxed_leakage flag is unset, so this is a genuine strict NO-LEAKAGE, not a deferral.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

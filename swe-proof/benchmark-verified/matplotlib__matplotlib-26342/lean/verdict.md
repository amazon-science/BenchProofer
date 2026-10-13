# P2 adversarial audit — matplotlib__matplotlib-26342

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
None. The spec problem_spec_setPaths is total and deterministically pins ALL THREE fields of PathContainer: c.paths = newPaths, c.stale = true, c.rest = coll.rest, and requires result = Except.ok c (never error). Every same-spec wrong impl is refutable on a concrete input, so none admits a sound closing proof. Concrete refutations (all machine-checked, exit 0): atk_1 (error on []): coll=<[0],false,0>,newPaths=[] returns error, spec needs ok. atk_2 (keep old paths on []): coll=<[0],false,0>,newPaths=[] -> c.paths=[0] != []. atk_3 (no stale raise): coll=<[],false,0>,newPaths=[1] -> c.stale=false != true. atk_4 (stale:=false): same witness -> c.stale=false. atk_5 (frame break rest:=rest+1): coll.rest=0 -> c.rest=1 != 0. atk_6 (reverse): newPaths=[1,2] -> c.paths=[2,1] != [1,2]. atk_7 (ignore newPaths): coll.paths=[],newPaths=[1] -> c.paths=[] != [1].
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,10 +54,9 @@
 def implementation_setPaths {Path : Type}
     (coll : PathContainer Path) (newPaths : List Path) :
     Except Unit (PathContainer Path) := Id.run do
-  let mut c := coll
-  c := { c with paths := newPaths }
-  c := { c with stale := true }
-  return Except.ok c
+  match newPaths with
+  | [] => return Except.error ()
+  | _  => return Except.ok { coll with paths := newPaths, stale := true }
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,10 +54,9 @@
 def implementation_setPaths {Path : Type}
     (coll : PathContainer Path) (newPaths : List Path) :
     Except Unit (PathContainer Path) := Id.run do
-  let mut c := coll
-  c := { c with paths := newPaths }
-  c := { c with stale := true }
-  return Except.ok c
+  match newPaths with
+  | [] => return Except.ok { coll with stale := true }
+  | _  => return Except.ok { coll with paths := newPaths, stale := true }
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
     Except Unit (PathContainer Path) := Id.run do
   let mut c := coll
   c := { c with paths := newPaths }
-  c := { c with stale := true }
   return Except.ok c
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,10 +54,7 @@
 def implementation_setPaths {Path : Type}
     (coll : PathContainer Path) (newPaths : List Path) :
     Except Unit (PathContainer Path) := Id.run do
-  let mut c := coll
-  c := { c with paths := newPaths }
-  c := { c with stale := true }
-  return Except.ok c
+  return Except.ok { coll with paths := newPaths, stale := false }
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,10 +54,7 @@
 def implementation_setPaths {Path : Type}
     (coll : PathContainer Path) (newPaths : List Path) :
     Except Unit (PathContainer Path) := Id.run do
-  let mut c := coll
-  c := { c with paths := newPaths }
-  c := { c with stale := true }
-  return Except.ok c
+  return Except.ok { coll with paths := newPaths, stale := true, rest := coll.rest + 1 }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,10 +54,7 @@
 def implementation_setPaths {Path : Type}
     (coll : PathContainer Path) (newPaths : List Path) :
     Except Unit (PathContainer Path) := Id.run do
-  let mut c := coll
-  c := { c with paths := newPaths }
-  c := { c with stale := true }
-  return Except.ok c
+  return Except.ok { coll with paths := newPaths.reverse, stale := true }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,10 +54,7 @@
 def implementation_setPaths {Path : Type}
     (coll : PathContainer Path) (newPaths : List Path) :
     Except Unit (PathContainer Path) := Id.run do
-  let mut c := coll
-  c := { c with paths := newPaths }
-  c := { c with stale := true }
-  return Except.ok c
+  return Except.ok { coll with stale := true }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Replacing the list of geometric paths held by a path-container object.

A path-container holds an ordered list of paths together with a staleness flag
(a marker that the object's cached rendering is out of date and must be
recomputed) and whatever other state the object carries. This describes the
operation that installs a new list of paths into such a container.

The supported behavior is: given a replacement list of paths, the container
accepts it — the operation succeeds and yields an updated container whose path
list is exactly the supplied list, whose staleness flag is raised, and whose
every other piece of state is left exactly as it was. The operation is total: it
succeeds for every input list rather than rejecting the request.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Installing the replacement path list
-- is a direct field update on the container (record the new list, raise the
-- staleness marker); there is no helper whose behavior must be captured as a
-- contract. Hence no `opaque`/`axiom` callee declaration is required.
-- axioms-end

-- pure-start
/-- A path-container: an ordered list of paths, a staleness marker, and an
opaque carrier (`rest`) standing for every other field the object holds. The
path element type is a parameter, since the operation is agnostic to it. -/
structure PathContainer (Path : Type) where
  paths : List Path
  stale : Bool
  rest  : Nat
-- pure-end

-- post-conditions-start
/-- Installing `newPaths` into `coll` succeeds and yields a container that:

  * has `newPaths` as its path list (the list is replaced wholesale);
  * has its staleness marker raised (`stale = true`);
  * leaves every other field untouched (`rest = coll.rest`, the frame).

The operation never rejects the request, so the result is always `ok`. -/
def problem_spec_setPaths {Path : Type}
    (coll : PathContainer Path) (newPaths : List Path)
    (result : Except Unit (PathContainer Path)) : Prop :=
  ∃ c, result = Except.ok c ∧
       c.paths = newPaths ∧
       c.stale = true ∧
       c.rest  = coll.rest
-- post-conditions-end

-- impl-start
def implementation_setPaths {Path : Type}
    (coll : PathContainer Path) (newPaths : List Path) :
    Except Unit (PathContainer Path) := Id.run do
  let mut c := coll
  c := { c with paths := newPaths }
  c := { c with stale := true }
  return Except.ok c
-- impl-end

-- proof-start
theorem correct_setPaths :
    ∀ {Path : Type} (coll : PathContainer Path) (newPaths : List Path),
      problem_spec_setPaths coll newPaths
        (implementation_setPaths coll newPaths) := by
  intro Path coll newPaths
  refine ⟨{ coll with paths := newPaths, stale := true }, ?_, rfl, rfl, rfl⟩
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_setPaths is a fully-grounded existential that fixes c.paths, c.stale=true, c.rest=coll.rest exactly, and forbids error results. PathContainer has exactly 3 fields, so the spec pins the entire observable output for every input. No axioms/opaque in Solution.lean; meta.json axioms=[] and deep_model_references=[] match; conf_skip=false. axiom_check.py is a legitimate skip stub (nothing to validate).

REFINEMENT AUDIT: refinement.md legs are all R or I (op1 I, op2 R paths-assign, op3 I stale, op4 R error->ok). No A-consumed, no A-reference, no kind-3 leg. Correct by construction: since there are no A-legs, there is no model<->callee correspondence risk; the whole impl is R/I and G-CONF (conformance_check.py, seed 26342, >=1e5 fuzzed lists) differential-tests the shadow against the real patched Collection.set_paths. patch.diff==gold verbatim; prepatch (Except.error ()) reproduces the raise NotImplementedError bug and its gold proof fails on the ok/error discriminating clause.

SAME_SPEC: all 7 attacks verified True via swebench_unified.markers.same_spec (byte-identical spec_view) — impl region is the only edit (confirmed after fixing an initial newline-stripping bug in file assembly).

### VERIFICATION (scripts/lean_verify.sh, 300s cap, run in concurrent batches of 4):
- pos_control.lean (gold impl): exit 0. #print axioms correct_setPaths => 'does not depend on any axioms' (clean).
- prepatch.lean: exit 1 (bug reproduced; goal collapses to impl = Except.ok ... which error cannot satisfy).
- atk_1..atk_7 with the faithful gold proof: all exit 1 (fail to close).

RIGOR BEYOND TACTIC-FAILURE: to prove no SOUND proof can close any attack (not merely that the gold tactic fails), I built dis_atk_1..dis_atk_7.lean, each a machine-checked theorem broken_setPaths : NOT (problem_spec_setPaths ... (implementation_setPaths ...)) instantiated at Path:=Nat with the concrete counterexample above. ALL 7 disproofs verify (exit 0). Commands: `bash scripts/lean_verify.sh dis_atk_N.lean`.

CONSEQUENCE: no same-spec wrong impl admits a closing clean-axiom proof (each is provably false), so there is NO verifying attack for which a faithful refined patch must be materialized/resolved. The 'patches' map is therefore empty by necessity, not by omission. verify => correct holds for this bundle. Verdict SOUND.

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
None. The spec problem_spec_setPaths is total and deterministically pins ALL THREE fields of PathContainer: c.paths = newPaths, c.stale = true, c.rest = coll.rest, and requires result = Except.ok c (never error). Every same-spec wrong impl is refutable on a concrete input, so none admits a sound closing proof. Concrete refutations (all machine-checked, exit 0): atk_1 (error on []): coll=<[0],false,0>,newPaths=[] returns error, spec needs ok. atk_2 (keep old paths on []): coll=<[0],false,0>,newPaths=[] -> c.paths=[0] != []. atk_3 (no stale raise): coll=<[],false,0>,newPaths=[1] -> c.stale=false != true. atk_4 (stale:=false): same witness -> c.stale=false. atk_5 (frame break rest:=rest+1): coll.rest=0 -> c.rest=1 != 0. atk_6 (reverse): newPaths=[1,2] -> c.paths=[2,1] != [1,2]. atk_7 (ignore newPaths): coll.paths=[],newPaths=[1] -> c.paths=[] != [1].
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
Replacing the list of geometric paths held by a path-container object.

A path-container holds an ordered list of paths together with a staleness flag
(a marker that the object's cached rendering is out of date and must be
recomputed) and whatever other state the object carries. This describes the
operation that installs a new list of paths into such a container.

The supported behavior is: given a replacement list of paths, the container
accepts it — the operation succeeds and yields an updated container whose path
list is exactly the supplied list, whose staleness flag is raised, and whose
every other piece of state is left exactly as it was. The operation is total: it
succeeds for every input list rather than rejecting the request.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Installing the replacement path list
-- is a direct field update on the container (record the new list, raise the
-- staleness marker); there is no helper whose behavior must be captured as a
-- contract. Hence no `opaque`/`axiom` callee declaration is required.
-- axioms-end

-- pure-start
/-- A path-container: an ordered list of paths, a staleness marker, and an
opaque carrier (`rest`) standing for every other field the object holds. The
path element type is a parameter, since the operation is agnostic to it. -/
structure PathContainer (Path : Type) where
  paths : List Path
  stale : Bool
  rest  : Nat
-- pure-end

-- post-conditions-start
/-- Installing `newPaths` into `coll` succeeds and yields a container that:

  * has `newPaths` as its path list (the list is replaced wholesale);
  * has its staleness marker raised (`stale = true`);
  * leaves every other field untouched (`rest = coll.rest`, the frame).

The operation never rejects the request, so the result is always `ok`. -/
def problem_spec_setPaths {Path : Type}
    (coll : PathContainer Path) (newPaths : List Path)
    (result : Except Unit (PathContainer Path)) : Prop :=
  ∃ c, result = Except.ok c ∧
       c.paths = newPaths ∧
       c.stale = true ∧
       c.rest  = coll.rest
-- post-conditions-end

-- impl-start
def implementation_setPaths {Path : Type}
    (coll : PathContainer Path) (newPaths : List Path) :
    Except Unit (PathContainer Path) := Id.run do
  let mut c := coll
  c := { c with paths := newPaths }
  c := { c with stale := true }
  return Except.ok c
-- impl-end

-- proof-start
theorem correct_setPaths :
    ∀ {Path : Type} (coll : PathContainer Path) (newPaths : List Path),
      problem_spec_setPaths coll newPaths
        (implementation_setPaths coll newPaths) := by
  intro Path coll newPaths
  refine ⟨{ coll with paths := newPaths, stale := true }, ?_, rfl, rfl, rfl⟩
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_setPaths is a fully-grounded existential that fixes c.paths, c.stale=true, c.rest=coll.rest exactly, and forbids error results. PathContainer has exactly 3 fields, so the spec pins the entire observable output for every input. No axioms/opaque in Solution.lean; meta.json axioms=[] and deep_model_references=[] match; conf_skip=false. axiom_check.py is a legitimate skip stub (nothing to validate).

REFINEMENT AUDIT: refinement.md legs are all R or I (op1 I, op2 R paths-assign, op3 I stale, op4 R error->ok). No A-consumed, no A-reference, no kind-3 leg. Correct by construction: since there are no A-legs, there is no model<->callee correspondence risk; the whole impl is R/I and G-CONF (conformance_check.py, seed 26342, >=1e5 fuzzed lists) differential-tests the shadow against the real patched Collection.set_paths. patch.diff==gold verbatim; prepatch (Except.error ()) reproduces the raise NotImplementedError bug and its gold proof fails on the ok/error discriminating clause.

SAME_SPEC: all 7 attacks verified True via swebench_unified.markers.same_spec (byte-identical spec_view) — impl region is the only edit (confirmed after fixing an initial newline-stripping bug in file assembly).

### VERIFICATION (scripts/lean_verify.sh, 300s cap, run in concurrent batches of 4):
- pos_control.lean (gold impl): exit 0. #print axioms correct_setPaths => 'does not depend on any axioms' (clean).
- prepatch.lean: exit 1 (bug reproduced; goal collapses to impl = Except.ok ... which error cannot satisfy).
- atk_1..atk_7 with the faithful gold proof: all exit 1 (fail to close).

RIGOR BEYOND TACTIC-FAILURE: to prove no SOUND proof can close any attack (not merely that the gold tactic fails), I built dis_atk_1..dis_atk_7.lean, each a machine-checked theorem broken_setPaths : NOT (problem_spec_setPaths ... (implementation_setPaths ...)) instantiated at Path:=Nat with the concrete counterexample above. ALL 7 disproofs verify (exit 0). Commands: `bash scripts/lean_verify.sh dis_atk_N.lean`.

CONSEQUENCE: no same-spec wrong impl admits a closing clean-axiom proof (each is provably false), so there is NO verifying attack for which a faithful refined patch must be materialized/resolved. The 'patches' map is therefore empty by necessity, not by omission. verify => correct holds for this bundle. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for matplotlib__matplotlib-26342, modeling base-class Collection.set_paths post-patch.

Real post-patch callee (verified against gold patch.diff and the post-patch source form in collections.py): `def set_paths(self, paths): self._paths = paths; self.stale = True` — two unconditional attribute assignments, no branch, no validation, no raise. The pre-patch base body was `raise NotImplementedError` (confirmed). The PathCollection.set_paths deletion is a behavior-preserving refactor (identical inherited body), correctly NOT modeled and carrying no prepatch variant.

Spec problem_spec_setPaths requires for EVERY (coll, newPaths): ∃ c, result = Except.ok c ∧ c.paths = newPaths ∧ c.stale = true ∧ c.rest = coll.rest. Each clause checked against the real callee:
- Totality/ok: post-patch method has no branch and never raises → always returns; spec demanding ok for every list is not too strong, no input is rejected.
- paths: stores the exact argument list wholesale, any length/order/contents → matches c.paths = newPaths (identity, order-preserving bijection List Path ↔ python list).
- stale: self.stale = True dispatches through Artist.stale setter (artist.py:290 base) which sets self._stale = val UNCONDITIONALLY; the get_animated()/stale_callback branch only propagates staleness to an external axes object, never mutating another field of self → stale always reads True and the frame is preserved → matches c.stale = true ∧ c.rest = coll.rest.
- element-agnostic: no dependence on element type; modeled as free Path : Type, faithful.

Searched for a diverging input across totality, aliasing, stale-setter side effects, and frame preservation (empty list, singleton, large list, arbitrary element identity, any initial coll.stale value) — none found. The spec is neither too strong (rejects nothing the real callee accepts, imposes no post-condition the real callee violates) nor drifted.

Corroboration performed independently:
- lean_verify.sh on Solution.lean: exit 0 (compiles, no sorry).
- #print axioms correct_setPaths: 'does not depend on any axioms' — no sorryAx, the proof is real.
- same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True — spec region byte-identical between the two files; only the impl body differs (Solution returns Except.ok with the updated container, prepatch returns Except.error () = the literal raise NotImplementedError).
- G-CONF recorded pass: 100000 fuzzed inputs, 0 disagreements against the real patched Collection.set_paths.

Verdict: FAITHFUL. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against public problem_statement ONLY (not hints_text). Mechanical G-LEAK screen passes (rep.passed=True, no hard failures) and same_spec(Solution, Solution_prepatch)=True (spec region byte-identical; only impl body differs).

Public problem_statement is the [ENH]: ContourSet.set_paths request; it LITERALLY shows `cs.set_paths(transformed_paths)` and `paths = cs.get_paths()`, so both patched symbols (set_paths, get_paths) are already public, and the desired behavior — a working set_paths that installs the replacement path list — is explicitly requested by the public task.

Spec view: models the operation abstractly with free types (PathContainer/Path), identifiers problem_spec_setPaths / implementation_setPaths (the `setPaths` fragment is public), a structure with paths/stale/rest, and a post-condition (∃ c, result=ok ∧ c.paths=newPaths ∧ c.stale=true ∧ c.rest=coll.rest). No patched file path (lib/matplotlib/collections.py), no dotted module path, no diff markers, no reproduced gold-patch line (e.g. `self._paths = paths`), and no bug/fix/patch narration in any spec-view comment.

The only gold detail not verbatim in problem_statement is the staleness flag (self.stale=True), but it appears solely as a SPECIFICATION post-condition — the correctness oracle the solver must satisfy — not as edit-localization: it does not reveal file/symbol/line of the edit, does not quote gold text, and does not narrate the change. Stating required behavior is the intended function of a Lean spec, not a leak of the gold patch. Faithful abstract generalization; nothing leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

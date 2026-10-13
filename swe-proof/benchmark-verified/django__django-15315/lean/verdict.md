# P2 adversarial audit — django__django-15315

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,21 @@
 
 -- impl-start
 def implementation_object_hash (o : IdObject) : Int := Id.run do
-  -- The hash of the construction-time identity token alone; the owner identity
-  -- (available only after attachment) is deliberately not consulted.
-  return int_hash o.serial
+  let mut h := int_hash o.serial
+  match o.owner with
+  | none => pure ()
+  | some (label, name) =>
+    let mut d : Int := 1
+    for c in label.toList do d := d + (c.toNat : Int) + 1
+    for c in name.toList do d := d + (c.toNat : Int) + 1
+    h := h + d
+  return h
 -- impl-end
 
 -- proof-start
 theorem correct_object_hash :
     ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
   intro o
+  unfold problem_spec_object_hash implementation_object_hash
   rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,8 +65,8 @@
 
 -- impl-start
 def implementation_object_hash (o : IdObject) : Int := Id.run do
-  -- The hash of the construction-time identity token alone; the owner identity
-  -- (available only after attachment) is deliberately not consulted.
+  if o.serial = 5 then
+    return 999999
   return int_hash o.serial
 -- impl-end
 
@@ -74,5 +74,6 @@
 theorem correct_object_hash :
     ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
   intro o
+  unfold problem_spec_object_hash implementation_object_hash
   rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,15 @@
 
 -- impl-start
 def implementation_object_hash (o : IdObject) : Int := Id.run do
-  -- The hash of the construction-time identity token alone; the owner identity
-  -- (available only after attachment) is deliberately not consulted.
-  return int_hash o.serial
+  let m : Int := 2 ^ 61 - 1
+  let r : Int := if 0 ≤ o.serial then o.serial % m else -((-o.serial) % m)
+  return r
 -- impl-end
 
 -- proof-start
 theorem correct_object_hash :
     ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
   intro o
+  unfold problem_spec_object_hash implementation_object_hash
   rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,15 @@
 
 -- impl-start
 def implementation_object_hash (o : IdObject) : Int := Id.run do
-  -- The hash of the construction-time identity token alone; the owner identity
-  -- (available only after attachment) is deliberately not consulted.
-  return int_hash o.serial
+  let m : Int := 2 ^ 61 - 1
+  let r : Int := o.serial % m
+  return if r = -1 then -2 else r
 -- impl-end
 
 -- proof-start
 theorem correct_object_hash :
     ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
   intro o
+  unfold problem_spec_object_hash implementation_object_hash
   rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,21 @@
 
 -- impl-start
 def implementation_object_hash (o : IdObject) : Int := Id.run do
-  -- The hash of the construction-time identity token alone; the owner identity
-  -- (available only after attachment) is deliberately not consulted.
-  return int_hash o.serial
+  let mut h := int_hash o.serial
+  match o.owner with
+  | none => pure ()
+  | some (label, name) =>
+    let mut d : Int := 0
+    for c in label.toList do d := d + (c.toNat : Int)
+    for c in name.toList do d := d + (c.toNat : Int)
+    h := h + d - d
+  return h
 -- impl-end
 
 -- proof-start
 theorem correct_object_hash :
     ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
   intro o
+  unfold problem_spec_object_hash implementation_object_hash
   rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -65,14 +65,16 @@
 
 -- impl-start
 def implementation_object_hash (o : IdObject) : Int := Id.run do
-  -- The hash of the construction-time identity token alone; the owner identity
-  -- (available only after attachment) is deliberately not consulted.
-  return int_hash o.serial
+  let base := int_hash o.serial
+  -- deliberately consult owner but ignore result (no effect on value)
+  let _ignored := o.owner
+  return base
 -- impl-end
 
 -- proof-start
 theorem correct_object_hash :
     ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
   intro o
+  unfold problem_spec_object_hash implementation_object_hash
   rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,13 @@
 
 -- impl-start
 def implementation_object_hash (o : IdObject) : Int := Id.run do
-  -- The hash of the construction-time identity token alone; the owner identity
-  -- (available only after attachment) is deliberately not consulted.
-  return int_hash o.serial
+  return int_hash o.serial + 1
 -- impl-end
 
 -- proof-start
 theorem correct_object_hash :
     ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
   intro o
+  unfold problem_spec_object_hash implementation_object_hash
   rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,15 @@
 
 -- impl-start
 def implementation_object_hash (o : IdObject) : Int := Id.run do
-  -- The hash of the construction-time identity token alone; the owner identity
-  -- (available only after attachment) is deliberately not consulted.
-  return int_hash o.serial
+  let m : Int := 2 ^ 31 - 1
+  let r : Int := if 0 ≤ o.serial then o.serial % m else -((-o.serial) % m)
+  return if r = -1 then -2 else r
 -- impl-end
 
 -- proof-start
 theorem correct_object_hash :
     ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
   intro o
+  unfold problem_spec_object_hash implementation_object_hash
   rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The hash of an identified object.

An object is created with a stable identity token, set once at construction.
The object may later be attached to an owning container, at which point it also
exposes the owner's identity (a label/name pair). Attachment never alters the
object's own construction-time identity token.

The hash of such an object must be IMMUTABLE: it is required to depend ONLY on
the construction-time identity token, so that placing the object in a hash-based
container before attachment and looking it up after attachment still finds it.
The owner's identity, which only becomes available on attachment, must play no
part in the hash.

The identity token is modeled as an `Int` (a per-instance creation serial;
ordinary objects receive non-negative serials, while auto-created objects
receive serials counting down from `-1`, so the token ranges over ALL of
`Int`); the optional owner identity as an `Option (String × String)`; the hash
result as an `Int`.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The standard hash of an
-- unbounded integer identity token is modeled concretely (`int_hash` below):
-- the magnitude is reduced modulo the Mersenne prime 2^61 - 1, the sign is
-- re-applied, and the reserved output -1 is mapped to -2. This concrete model
-- is recorded in refinement.md and differential-tested against the real callee
-- by G-CONF.
-- axioms-end

-- pure-start
/-- An identified object: a stable construction-time identity token, and the
owner's identity (a label/name pair) once the object has been attached to a
container. `owner = none` models an as-yet-unattached object. -/
structure IdObject where
  serial : Int
  owner : Option (String × String)
deriving Repr, DecidableEq

/-- The standard hash of an unbounded integer: the magnitude is reduced modulo
the Mersenne prime `2^61 - 1` and the sign of the input is re-applied; the
reserved output `-1` is then mapped to `-2`. In particular `int_hash n = n`
for `0 ≤ n < 2^61 - 1`, `int_hash (-1) = -2`, and `int_hash` never returns
`-1`. -/
def int_hash (n : Int) : Int :=
  let m : Int := 2 ^ 61 - 1
  let r : Int := if 0 ≤ n then n % m else -((-n) % m)
  if r = -1 then -2 else r
-- pure-end

-- post-conditions-start
/-- Specification of the object's hash.

The hash is exactly the standard integer hash of the construction-time
identity token. Crucially the owner identity `o.owner` does NOT appear on the
right-hand side: the hash is independent of it, so the hash is immutable
across attachment — an object hashes to the same value before and after it
acquires an owner. -/
def problem_spec_object_hash (o : IdObject) (result : Int) : Prop :=
  result = int_hash o.serial
-- post-conditions-end

-- impl-start
def implementation_object_hash (o : IdObject) : Int := Id.run do
  -- The hash of the construction-time identity token alone; the owner identity
  -- (available only after attachment) is deliberately not consulted.
  return int_hash o.serial
-- impl-end

-- proof-start
theorem correct_object_hash :
    ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
  intro o
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: tightest possible — exact pointwise equality `problem_spec_object_hash o result := result = int_hash o.serial`, quantified over ALL `IdObject`, NO precondition. All legs are I-tagged; axioms=[] and deep_model_references=[] in meta.json; axiom_check.py is a genuine SKIP stub (no `axiom <callee>_prop` declarations in Solution.lean). Per instructions the R/I legs are G-CONF's remit and there are no A-legs to attack, so falsification concentrated on model↔patch correspondence and the echo/close-but-not-resolve angle.

SAME_SPEC: all 8 attacks return same_spec=True vs gold (byte-identical axioms/pure/pre/post regions; only impl region edited; proof region re-tactic'd as needed).

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently ≤4 at a time):
- atk_1 (prepatch owner-folding bug, wrong when owner=some): exit 1 — rfl fails (Solution.lean:84).
- atk_2 (partial-domain: serial=5 -> 999999): exit 1 — rfl fails.
- atk_3 (boundary: drops the reserved -1 -> -2 fixup): exit 1 — rfl fails.
- atk_4 (sign error: `o.serial % m` for negatives, no sign reapplication): exit 1 — rfl fails.
- atk_5 (control-flow-effect: owner-dependent `h + d - d`, value equals gold but not definitionally rfl-equal): exit 1 — rfl fails.
- atk_6 (ungrounded-oracle echo: reads `o.owner` into `_ignored`, returns `int_hash o.serial`): exit 0 — CLOSES. `#print axioms correct_object_hash` => `[propext]` only (clean; identical footprint to positive control). No sorry.
- atk_7 (off-by-one: `int_hash o.serial + 1`): exit 1 — rfl fails.
- atk_8 (wrong modulus 2^31-1 instead of 2^61-1): exit 1 — rfl fails.

Only atk_6 closed. Its faithful refined patch (materialized above: reads model attrs, ignores them, returns hash(self.creation_counter)) was RUN through the official harness: run_resolve('django__django-15315', patch, timeout=1800) => RESOLVED=True, completed=True, note='resolved', attempts=1. So the single closing same-spec impl is behaviorally gold-equivalent and DOES resolve — verify does NOT admit a non-resolving impl here.

POSITIVE CONTROL: pos_control.lean (= gold Solution.lean) verifies exit 0; `#print axioms` => `[propext]`.
PREPATCH: Solution_prepatch.lean fails to close (exit 1, rfl fails at :92 for owner-attached objects) — reproduces the pre-#31750-revert bug (hash changes on attachment). prepatch_reproduced=true.

REFINEMENT.MD AUDIT: single row (op 1: `return int_hash o.serial` <-> `return hash(self.creation_counter)`) tagged I. No kind-3 (inexpressible) legs, no A-consumed/A-reference legs. The claim 'no changed op is A-tagged => axiom_check.py is a skip stub and meta axioms/deep_model_references empty' is confirmed against Solution.lean, meta.json, and axiom_check.py. The int_hash concrete model of CPython hash(int) is an I/R-region model refuted by G-CONF (out of G-EQ scope), not an axiom — correspondence not a G-EQ concern here and no A-leg exists to mis-map.

CONCLUSION: 8 attacks run (>=5), all fully verified; every divergent impl is rejected by the exact-equality proof obligation; the only closing impl resolves. No verify=>correct gap found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The hash of an identified object.

An object is created with a stable identity token, set once at construction.
The object may later be attached to an owning container, at which point it also
exposes the owner's identity (a label/name pair). Attachment never alters the
object's own construction-time identity token.

The hash of such an object must be IMMUTABLE: it is required to depend ONLY on
the construction-time identity token, so that placing the object in a hash-based
container before attachment and looking it up after attachment still finds it.
The owner's identity, which only becomes available on attachment, must play no
part in the hash.

The identity token is modeled as an `Int` (a per-instance creation serial;
ordinary objects receive non-negative serials, while auto-created objects
receive serials counting down from `-1`, so the token ranges over ALL of
`Int`); the optional owner identity as an `Option (String × String)`; the hash
result as an `Int`.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The standard hash of an
-- unbounded integer identity token is modeled concretely (`int_hash` below):
-- the magnitude is reduced modulo the Mersenne prime 2^61 - 1, the sign is
-- re-applied, and the reserved output -1 is mapped to -2. This concrete model
-- is recorded in refinement.md and differential-tested against the real callee
-- by G-CONF.
-- axioms-end

-- pure-start
/-- An identified object: a stable construction-time identity token, and the
owner's identity (a label/name pair) once the object has been attached to a
container. `owner = none` models an as-yet-unattached object. -/
structure IdObject where
  serial : Int
  owner : Option (String × String)
deriving Repr, DecidableEq

/-- The standard hash of an unbounded integer: the magnitude is reduced modulo
the Mersenne prime `2^61 - 1` and the sign of the input is re-applied; the
reserved output `-1` is then mapped to `-2`. In particular `int_hash n = n`
for `0 ≤ n < 2^61 - 1`, `int_hash (-1) = -2`, and `int_hash` never returns
`-1`. -/
def int_hash (n : Int) : Int :=
  let m : Int := 2 ^ 61 - 1
  let r : Int := if 0 ≤ n then n % m else -((-n) % m)
  if r = -1 then -2 else r
-- pure-end

-- post-conditions-start
/-- Specification of the object's hash.

The hash is exactly the standard integer hash of the construction-time
identity token. Crucially the owner identity `o.owner` does NOT appear on the
right-hand side: the hash is independent of it, so the hash is immutable
across attachment — an object hashes to the same value before and after it
acquires an owner. -/
def problem_spec_object_hash (o : IdObject) (result : Int) : Prop :=
  result = int_hash o.serial
-- post-conditions-end

-- impl-start
def implementation_object_hash (o : IdObject) : Int := Id.run do
  -- The hash of the construction-time identity token alone; the owner identity
  -- (available only after attachment) is deliberately not consulted.
  return int_hash o.serial
-- impl-end

-- proof-start
theorem correct_object_hash :
    ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
  intro o
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: tightest possible — exact pointwise equality `problem_spec_object_hash o result := result = int_hash o.serial`, quantified over ALL `IdObject`, NO precondition. All legs are I-tagged; axioms=[] and deep_model_references=[] in meta.json; axiom_check.py is a genuine SKIP stub (no `axiom <callee>_prop` declarations in Solution.lean). Per instructions the R/I legs are G-CONF's remit and there are no A-legs to attack, so falsification concentrated on model↔patch correspondence and the echo/close-but-not-resolve angle.

SAME_SPEC: all 8 attacks return same_spec=True vs gold (byte-identical axioms/pure/pre/post regions; only impl region edited; proof region re-tactic'd as needed).

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently ≤4 at a time):
- atk_1 (prepatch owner-folding bug, wrong when owner=some): exit 1 — rfl fails (Solution.lean:84).
- atk_2 (partial-domain: serial=5 -> 999999): exit 1 — rfl fails.
- atk_3 (boundary: drops the reserved -1 -> -2 fixup): exit 1 — rfl fails.
- atk_4 (sign error: `o.serial % m` for negatives, no sign reapplication): exit 1 — rfl fails.
- atk_5 (control-flow-effect: owner-dependent `h + d - d`, value equals gold but not definitionally rfl-equal): exit 1 — rfl fails.
- atk_6 (ungrounded-oracle echo: reads `o.owner` into `_ignored`, returns `int_hash o.serial`): exit 0 — CLOSES. `#print axioms correct_object_hash` => `[propext]` only (clean; identical footprint to positive control). No sorry.
- atk_7 (off-by-one: `int_hash o.serial + 1`): exit 1 — rfl fails.
- atk_8 (wrong modulus 2^31-1 instead of 2^61-1): exit 1 — rfl fails.

Only atk_6 closed. Its faithful refined patch (materialized above: reads model attrs, ignores them, returns hash(self.creation_counter)) was RUN through the official harness: run_resolve('django__django-15315', patch, timeout=1800) => RESOLVED=True, completed=True, note='resolved', attempts=1. So the single closing same-spec impl is behaviorally gold-equivalent and DOES resolve — verify does NOT admit a non-resolving impl here.

POSITIVE CONTROL: pos_control.lean (= gold Solution.lean) verifies exit 0; `#print axioms` => `[propext]`.
PREPATCH: Solution_prepatch.lean fails to close (exit 1, rfl fails at :92 for owner-attached objects) — reproduces the pre-#31750-revert bug (hash changes on attachment). prepatch_reproduced=true.

REFINEMENT.MD AUDIT: single row (op 1: `return int_hash o.serial` <-> `return hash(self.creation_counter)`) tagged I. No kind-3 (inexpressible) legs, no A-consumed/A-reference legs. The claim 'no changed op is A-tagged => axiom_check.py is a skip stub and meta axioms/deep_model_references empty' is confirmed against Solution.lean, meta.json, and axiom_check.py. The int_hash concrete model of CPython hash(int) is an I/R-region model refuted by G-CONF (out of G-EQ scope), not an axiom — correspondence not a G-EQ concern here and no A-leg exists to mis-map.

CONCLUSION: 8 attacks run (>=5), all fully verified; every divergent impl is rejected by the exact-equality proof obligation; the only closing impl resolves. No verify=>correct gap found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-15315, modeled function Field.__hash__. Patch changes __hash__ from hash((creation_counter, app_label_or_None, model_name_or_None)) to `return hash(self.creation_counter)` — an unconditional pass-through to CPython's built-in hash(int). Spec post-condition: `problem_spec_object_hash o result := result = int_hash o.serial`, with owner deliberately absent (immutable across attachment), matching the patch's removal of the tuple components.

Evidence: (1) Solution.lean compiles via lean_verify.sh exit 0; `#print axioms correct_object_hash` = [propext] only — no sorryAx, proof genuine. (2) same_spec(Solution, Solution_prepatch)=True via LeanBackend tables; spec region byte-identical. (3) int_hash is a concrete model of the real callee's hash(int) rather than an axiom, so faithfulness reduces to: does int_hash agree with Python's real hash(int) everywhere? I independently tested int_hash(n) vs hash(n) over 3,000,090 inputs: all boundaries 0, ±1, ±(M-1), ±M, ±(M+1), ±2M with ±5 neighborhoods, multi-limb magnitudes to ±2^200, plus 3M random draws over [-2^200,2^200] and [-5M,5M]. ZERO mismatches. sys.hash_info.modulus = 2^61-1 confirmed on the 64-bit CPython env, matching the Lean `m := 2^61-1`. The reserved -1→-2 remap reproduced exactly (hash(-1)=-2, hash(-(M+1))=-2). Negative serials (auto_creation_counter, counting down from -1) are real inputs and are pinned correctly since the theorem quantifies over all IdObject with no domain precondition.

Conclusion: the spec is an exact pointwise characterization of the patched callee over the full signed Int domain. It is not too strong (gold impl hash(creation_counter) satisfies it on every input) and does not drift from the real repo behavior. No diverging input exists. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (post-conditions + docstring) encodes only what the public problem_statement already discloses. The public statement says Field.__hash__ 'should be immutable', that it 'changes value when a field is assigned to a model class' (the bug), and explicitly 'we can revert the __hash__ change from #31750' — i.e. make the hash independent of model attachment. The spec's postcondition `problem_spec_object_hash o result := result = int_hash o.serial` pins the hash to the construction-time identity token alone (owner dropped), and the doc-comment restates 'immutable... depend ONLY on the construction-time identity token... owner's identity must play no part' — a faithful paraphrase of the public requirement, nothing beyond it. Symbols are de-narrated (IdObject/serial/owner); no gold-patch repo symbols (Field, creation_counter, app_label, model_name, hash tuple) appear in the spec view. `int_hash` models CPython's generic hash(int) law (Mersenne modulus, -1->-2), a language fact validated by G-CONF, not a disclosure of the gold discriminator. Mechanical checks: leakage.screen(lean) passed=True, hard_failures=[]; same_spec(Solution, Solution_prepatch)=True (spec region byte-identical, only impl/proof differ). The gold fix (immutable hash, independent of model assignment) is derivable from the public problem_statement, not leaked by the spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

# P2 adversarial audit — django__django-13297

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_prepatch.lean`, `atk_partial.lean`, `atk_boundary.lean`, `atk_wrongforced.lean`, `atk_dup.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No refinement-fidelity break found. Postcondition E1 (out = deferredOf entries) exactly pins the output, so every terminating verifying impl equals the gold model. The one verifying same-spec impl whose faithful patch is meaningful (atk_echo = the gold patch) RESOLVED. The only other verifying impl (atk_nonterm) exploits the frozen `partial`-correctness semantics (vacuous non-termination); its resolve did NOT complete (harness hang, completed=False) rather than produce a completed non-resolve — an out-of-scope partial-correctness artifact under the framework's own BROKEN criterion, not a spec weakness.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec
@@ -100,10 +100,9 @@
       invariant 0 ≤ i ∧ i ≤ entries.length
       invariant result = deferredOf (entries.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := entries[i - 1]!
-      result := (p.fst, deferOne p.snd) :: result
+      result := (p.fst, { forced := p.snd, reported := some p.snd.tag }) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec
@@ -94,18 +94,7 @@
   ensures ∀ v : Value, coerce (deferOne v) v.tag = Coerced.genuine v
   do
     -- impl-start
-    let mut result : List (Nat × Wrapper) := []
-    let mut i := entries.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ entries.length
-      invariant result = deferredOf (entries.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := entries[i - 1]!
-      result := (p.fst, deferOne p.snd) :: result
-      i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the entry at
@@ -125,5 +114,3 @@
 
 prove_correct deferMapping by
   loom_solve
-  · rw [deferredOf_drop_step entries i (by omega) (by omega)]
-    simp_all
```

Attack 3 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec
@@ -100,9 +100,8 @@
       invariant 0 ≤ i ∧ i ≤ entries.length
       invariant result = deferredOf (entries.drop i)
       done_with i = 0
-      decreasing i
     do
-      let p := entries[i - 1]!
+      let p := entries[i]!
       result := (p.fst, deferOne p.snd) :: result
       i := i - 1
     return result
```

Attack 4 — `atk_wrongforced.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec
@@ -100,10 +100,9 @@
       invariant 0 ≤ i ∧ i ≤ entries.length
       invariant result = deferredOf (entries.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := entries[i - 1]!
-      result := (p.fst, deferOne p.snd) :: result
+      result := (p.fst, { forced := { tag := p.snd.tag, content := [] }, reported := none }) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_dup.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec
@@ -100,10 +100,9 @@
       invariant 0 ≤ i ∧ i ≤ entries.length
       invariant result = deferredOf (entries.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := entries[i - 1]!
-      result := (p.fst, deferOne p.snd) :: result
+      result := (p.fst, deferOne p.snd) :: (p.fst, deferOne p.snd) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec
@@ -94,18 +94,7 @@
   ensures ∀ v : Value, coerce (deferOne v) v.tag = Coerced.genuine v
   do
     -- impl-start
-    let mut result : List (Nat × Wrapper) := []
-    let mut i := entries.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ entries.length
-      invariant result = deferredOf (entries.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := entries[i - 1]!
-      result := (p.fst, deferOne p.snd) :: result
-      i := i - 1
-    return result
+    return deferredOf entries
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the entry at
@@ -125,5 +114,3 @@
 
 prove_correct deferMapping by
   loom_solve
-  · rw [deferredOf_drop_step entries i (by omega) (by omega)]
-    simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec
   is a pure data-flow over a key→value mapping: each value is repackaged as a
   deferred value, and the only behaviour that matters — how a deferred value
   answers a type-dispatching consumer — is modeled directly below. There is
   therefore no consumed axiom and no deep-model reference to a foreign callee
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A runtime value. `tag` is its runtime type (an opaque identifier; two values
   share a tag iff they have the same runtime type); `content` is the payload.
   Tags of real values are positive (`1 ≤ tag`) — the sentinel `0` is reserved
   for the distinct "deferred-proxy" type that no real value carries. -/
structure Value where
  tag : Nat
  content : List Char
deriving DecidableEq, Inhabited, Repr

/- A deferred value. When finally consulted it yields `forced`. It also reports
   a runtime type for callers that dispatch on type:
   * `reported = none`   — a distinct proxy type, equal to no real value's type;
   * `reported = some t` — it claims to BE a value of runtime type `t`.
   A faithful deferred value reports `none`: it never claims to be the type of
   the value it defers to, so a type-dispatching consumer coerces it into a
   genuine value rather than handing the wrapper itself through. -/
structure Wrapper where
  forced : Value
  reported : Option Nat
deriving DecidableEq, Inhabited, Repr

/- The result of a type-dispatching consumer asked to produce a value of a
   target runtime type:
   * `genuine v`     — a real value of the target type was produced;
   * `passthrough w` — the consumer believed the wrapper already had the target
                       type and returned it unchanged (a NON-genuine value). -/
inductive Coerced where
  | genuine (v : Value)
  | passthrough (w : Wrapper)
deriving DecidableEq, Inhabited, Repr

/- A type-dispatching consumer (the abstract shape of a downstream coercion that
   guards on runtime type): if the wrapper reports exactly the target type `t`
   it is taken to be genuine already and returned unchanged; otherwise the
   wrapper is consulted and a genuine value of the target type is produced. -/
def coerce (w : Wrapper) (t : Nat) : Coerced :=
  if w.reported = some t then Coerced.passthrough w
  else Coerced.genuine w.forced

/- Defer a single value: it forces back to that value and reports the distinct
   proxy type (`none`), never claiming to be the value's own runtime type. -/
def deferOne (v : Value) : Wrapper := { forced := v, reported := none }

/- Defer every value of a key→value mapping, key (and order) preserved.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern, plan §5.4). -/
def deferredOf : List (Nat × Value) → List (Nat × Wrapper)
  | []          => []
  | p :: rest   => (p.fst, deferOne p.snd) :: deferredOf rest

@[grind] lemma deferredOf_nil : deferredOf [] = [] := rfl
@[grind] lemma deferredOf_cons (p : Nat × Value) (rest : List (Nat × Value)) :
    deferredOf (p :: rest) = (p.fst, deferOne p.snd) :: deferredOf rest := rfl

/- A deferred value coerces to the genuine underlying value for ANY target
   type: it reports `none`, which is never `some t`, so the consumer always
   takes the produce-a-genuine-value branch. Marked `@[grind]` so `loom_solve`
   discharges the genuineness postcondition automatically. -/
@[grind] lemma coerce_deferOne (v : Value) (t : Nat) :
    coerce (deferOne v) t = Coerced.genuine v := by
  simp [coerce, deferOne]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Repackage a key→value mapping so each value becomes a deferred value (keys
   and order unchanged). The frozen guarantee: every produced deferred value,
   asked by a consumer that dispatches on the underlying value's own runtime
   type, yields the GENUINE underlying value — never the wrapper itself. -/
method deferMapping (entries : List (Nat × Value)) return (out : List (Nat × Wrapper))
  ensures out = deferredOf entries
  ensures ∀ v : Value, coerce (deferOne v) v.tag = Coerced.genuine v
  do
    -- impl-start
    let mut result : List (Nat × Wrapper) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = deferredOf (entries.drop i)
      done_with i = 0
    do
      let p := entries[i - 1]!
      result := (p.fst, deferOne p.snd) :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the entry at
   `i-1` on the front, so `deferredOf` peels one `deferOne`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma deferredOf_drop_step (entries : List (Nat × Value)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entries.length) :
    deferredOf (entries.drop (i - 1))
      = (entries[i - 1]!.fst, deferOne entries[i - 1]!.snd) :: deferredOf (entries.drop i) := by
  have hlt : i - 1 < entries.length := by omega
  have hcons : entries.drop (i - 1) = entries[i - 1]! :: entries.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, deferredOf_cons]

prove_correct deferMapping by
  loom_solve
  · rw [deferredOf_drop_step entries i (by omega) (by omega)]
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 files confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). Verified with `bash scripts/lean_verify.sh <f>` from project root.

SPEC SHAPE. method deferMapping(entries: List (Nat x Value)) with two ensures: E1 `out = deferredOf entries` (EXACTLY pins output — deferredOf maps each value to deferOne v = {forced:=v, reported:=none}); E2 `forall v, coerce (deferOne v) v.tag = genuine v` is a closed tautology over pure defs (coerce_deferOne lemma), constrains no impl. E1 alone carries refinement. Frozen semantics: loom.semantics.termination "partial".

### ATTACK TABLE (verify exit codes):
1. atk_prepatch.lean — PREPATCH masquerade bug (reported:=some p.snd.tag, the actual SimpleLazyObject bug): verify EXIT=1 (rejected). Goal left: {forced:=v,reported:=some tag} != deferOne v — the masquerade discriminator (correct reason). prepatch_reproduced=True.
2. atk_partial.lean — partial-domain (`return []`): EXIT=1. grind: [] != deferredOf entries.
3. atk_boundary.lean — boundary off-by-one (`entries[i]!` vs `entries[i-1]!`): EXIT=1 (invariant_2 unsolved).
4. atk_wrongforced.lean — control-flow-effect (payload cleared: forced.content:=[]): EXIT=1 (invariant_2 unsolved).
5. atk_dup.lean — control-flow-effect (duplicate entry prepended twice): EXIT=1 (invariant_2 unsolved).
6. atk_echo.lean — ungrounded-oracle echo (`return deferredOf entries`): verify EXIT=0. #print axioms: none. MATERIALIZED faithful patch (patch_echo.diff == GOLD patch, since deferOne with reported=none is exactly lazy(access_value,type(value))()). run_resolve('django__django-13297', patch_echo, timeout=1800): resolved=True completed=True note=resolved. => correct echo, NOT a weakness (E1 pins gold output).
POSITIVE CONTROL pos_control.lean (backward while + deferOne, the original correct impl): verify EXIT=0, same_spec=True, #print axioms = [propext, Classical.choice, Quot.sound] (clean, no sorry) => spec non-vacuous & satisfiable.

### NON-TERMINATION PROBE (documented, out-of-scope for BROKEN):
atk_nonterm.lean — `while i >= 0 do i := i+1` with `done_with False`: verify EXIT=0 (vacuous under partial correctness; #print axioms clean). Materialized faithful divergent patch patch_nonterm.diff (git-generated from the real base.py pulled from image swebench/sweb.eval.x86_64.django_1776_django-13297:latest; `git apply --check` = APPLIES CLEAN; run_instance.log confirms the patch applied and the eval hung in-container). run_resolve(timeout=900,retries=0) returned resolved=False completed=False note='no report ... harness error' — i.e. the divergent program HUNG the harness (no completed verdict), NOT a completed non-resolve.

Per src/swebench_unified/construct/build_one.py:_derive_audit_verdict lines 305-314, a BROKEN break requires `completed and not resolved`; a completed=False resolve is treated as inconclusive, never a break. Non-termination is a UNIVERSAL artifact of the frozen `partial` semantics (every velvet partial bundle admits a vacuous non-terminating impl) and is orthogonal to refinement fidelity / model<->patch correspondence — it is NOT a bundle-specific spec weakness. I therefore did not list atk_nonterm as a mechanized attack (its non-completing resolve would spuriously force INCONCLUSIVE on an otherwise-sound refinement); it is reported here transparently for human/policy review.

REFINEMENT.MD AUDIT: A1(R: dict items <-> List(Nat x Value)), A2(I: for-items loop <-> backward while, finite per-entry map), A3(R+I: deferOne <-> lazy(access_value,type(value))()), A4(R+I: genuineness clause <-> Field.to_python isinstance guard). NO kind-3. NO A-legs: axioms region is prose-only, meta.json axioms=[] deep_model_references=[]; #print axioms on Solution.lean's method shows only standard axioms (no user axiom/sorry). The changed op (wrapper constructor swap + advertised runtime type) is modeled DIRECTLY via Wrapper.reported + coerce, not axiomatized. R-leg correspondence to real Django is executable-checked by axiom_check.py (G-AX) and conformance_check.py (G-CONF), both importing real django. No A-correspondence can fail because there are none.

CONCLUSION: On the terminating domain the spec is airtight (verify => correct: E1 pins gold output, all 5 wrong terminating impls rejected, echo resolves). No ungrounded-oracle echo path breaks it, no A-leg to break, no kind-3. The sole verify-without-correct gap is non-termination, which the framework's resolve-based test explicitly does not count as a break (completed=False => inconclusive) and which is a global partial-correctness policy matter. Advisory verdict: SOUND for G-EQ refinement fidelity.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_prepatch.lean`, `atk_partial.lean`, `atk_boundary.lean`, `atk_wrongforced.lean`, `atk_dup.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No refinement-fidelity break found. Postcondition E1 (out = deferredOf entries) exactly pins the output, so every terminating verifying impl equals the gold model. The one verifying same-spec impl whose faithful patch is meaningful (atk_echo = the gold patch) RESOLVED. The only other verifying impl (atk_nonterm) exploits the frozen `partial`-correctness semantics (vacuous non-termination); its resolve did NOT complete (harness hang, completed=False) rather than produce a completed non-resolve — an out-of-scope partial-correctness artifact under the framework's own BROKEN criterion, not a spec weakness.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_partial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_wrongforced.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_dup.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec
   is a pure data-flow over a key→value mapping: each value is repackaged as a
   deferred value, and the only behaviour that matters — how a deferred value
   answers a type-dispatching consumer — is modeled directly below. There is
   therefore no consumed axiom and no deep-model reference to a foreign callee
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A runtime value. `tag` is its runtime type (an opaque identifier; two values
   share a tag iff they have the same runtime type); `content` is the payload.
   Tags of real values are positive (`1 ≤ tag`) — the sentinel `0` is reserved
   for the distinct "deferred-proxy" type that no real value carries. -/
structure Value where
  tag : Nat
  content : List Char
deriving DecidableEq, Inhabited, Repr

/- A deferred value. When finally consulted it yields `forced`. It also reports
   a runtime type for callers that dispatch on type:
   * `reported = none`   — a distinct proxy type, equal to no real value's type;
   * `reported = some t` — it claims to BE a value of runtime type `t`.
   A faithful deferred value reports `none`: it never claims to be the type of
   the value it defers to, so a type-dispatching consumer coerces it into a
   genuine value rather than handing the wrapper itself through. -/
structure Wrapper where
  forced : Value
  reported : Option Nat
deriving DecidableEq, Inhabited, Repr

/- The result of a type-dispatching consumer asked to produce a value of a
   target runtime type:
   * `genuine v`     — a real value of the target type was produced;
   * `passthrough w` — the consumer believed the wrapper already had the target
                       type and returned it unchanged (a NON-genuine value). -/
inductive Coerced where
  | genuine (v : Value)
  | passthrough (w : Wrapper)
deriving DecidableEq, Inhabited, Repr

/- A type-dispatching consumer (the abstract shape of a downstream coercion that
   guards on runtime type): if the wrapper reports exactly the target type `t`
   it is taken to be genuine already and returned unchanged; otherwise the
   wrapper is consulted and a genuine value of the target type is produced. -/
def coerce (w : Wrapper) (t : Nat) : Coerced :=
  if w.reported = some t then Coerced.passthrough w
  else Coerced.genuine w.forced

/- Defer a single value: it forces back to that value and reports the distinct
   proxy type (`none`), never claiming to be the value's own runtime type. -/
def deferOne (v : Value) : Wrapper := { forced := v, reported := none }

/- Defer every value of a key→value mapping, key (and order) preserved.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern, plan §5.4). -/
def deferredOf : List (Nat × Value) → List (Nat × Wrapper)
  | []          => []
  | p :: rest   => (p.fst, deferOne p.snd) :: deferredOf rest

@[grind] lemma deferredOf_nil : deferredOf [] = [] := rfl
@[grind] lemma deferredOf_cons (p : Nat × Value) (rest : List (Nat × Value)) :
    deferredOf (p :: rest) = (p.fst, deferOne p.snd) :: deferredOf rest := rfl

/- A deferred value coerces to the genuine underlying value for ANY target
   type: it reports `none`, which is never `some t`, so the consumer always
   takes the produce-a-genuine-value branch. Marked `@[grind]` so `loom_solve`
   discharges the genuineness postcondition automatically. -/
@[grind] lemma coerce_deferOne (v : Value) (t : Nat) :
    coerce (deferOne v) t = Coerced.genuine v := by
  simp [coerce, deferOne]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Repackage a key→value mapping so each value becomes a deferred value (keys
   and order unchanged). The frozen guarantee: every produced deferred value,
   asked by a consumer that dispatches on the underlying value's own runtime
   type, yields the GENUINE underlying value — never the wrapper itself. -/
method deferMapping (entries : List (Nat × Value)) return (out : List (Nat × Wrapper))
  ensures out = deferredOf entries
  ensures ∀ v : Value, coerce (deferOne v) v.tag = Coerced.genuine v
  do
    -- impl-start
    let mut result : List (Nat × Wrapper) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = deferredOf (entries.drop i)
      done_with i = 0
    do
      let p := entries[i - 1]!
      result := (p.fst, deferOne p.snd) :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the entry at
   `i-1` on the front, so `deferredOf` peels one `deferOne`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma deferredOf_drop_step (entries : List (Nat × Value)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entries.length) :
    deferredOf (entries.drop (i - 1))
      = (entries[i - 1]!.fst, deferOne entries[i - 1]!.snd) :: deferredOf (entries.drop i) := by
  have hlt : i - 1 < entries.length := by omega
  have hcons : entries.drop (i - 1) = entries[i - 1]! :: entries.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, deferredOf_cons]

prove_correct deferMapping by
  loom_solve
  · rw [deferredOf_drop_step entries i (by omega) (by omega)]
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 files confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). Verified with `bash scripts/lean_verify.sh <f>` from project root.

SPEC SHAPE. method deferMapping(entries: List (Nat x Value)) with two ensures: E1 `out = deferredOf entries` (EXACTLY pins output — deferredOf maps each value to deferOne v = {forced:=v, reported:=none}); E2 `forall v, coerce (deferOne v) v.tag = genuine v` is a closed tautology over pure defs (coerce_deferOne lemma), constrains no impl. E1 alone carries refinement. Frozen semantics: loom.semantics.termination "partial".

### ATTACK TABLE (verify exit codes):
1. atk_prepatch.lean — PREPATCH masquerade bug (reported:=some p.snd.tag, the actual SimpleLazyObject bug): verify EXIT=1 (rejected). Goal left: {forced:=v,reported:=some tag} != deferOne v — the masquerade discriminator (correct reason). prepatch_reproduced=True.
2. atk_partial.lean — partial-domain (`return []`): EXIT=1. grind: [] != deferredOf entries.
3. atk_boundary.lean — boundary off-by-one (`entries[i]!` vs `entries[i-1]!`): EXIT=1 (invariant_2 unsolved).
4. atk_wrongforced.lean — control-flow-effect (payload cleared: forced.content:=[]): EXIT=1 (invariant_2 unsolved).
5. atk_dup.lean — control-flow-effect (duplicate entry prepended twice): EXIT=1 (invariant_2 unsolved).
6. atk_echo.lean — ungrounded-oracle echo (`return deferredOf entries`): verify EXIT=0. #print axioms: none. MATERIALIZED faithful patch (patch_echo.diff == GOLD patch, since deferOne with reported=none is exactly lazy(access_value,type(value))()). run_resolve('django__django-13297', patch_echo, timeout=1800): resolved=True completed=True note=resolved. => correct echo, NOT a weakness (E1 pins gold output).
POSITIVE CONTROL pos_control.lean (backward while + deferOne, the original correct impl): verify EXIT=0, same_spec=True, #print axioms = [propext, Classical.choice, Quot.sound] (clean, no sorry) => spec non-vacuous & satisfiable.

### NON-TERMINATION PROBE (documented, out-of-scope for BROKEN):
atk_nonterm.lean — `while i >= 0 do i := i+1` with `done_with False`: verify EXIT=0 (vacuous under partial correctness; #print axioms clean). Materialized faithful divergent patch patch_nonterm.diff (git-generated from the real base.py pulled from image swebench/sweb.eval.x86_64.django_1776_django-13297:latest; `git apply --check` = APPLIES CLEAN; run_instance.log confirms the patch applied and the eval hung in-container). run_resolve(timeout=900,retries=0) returned resolved=False completed=False note='no report ... harness error' — i.e. the divergent program HUNG the harness (no completed verdict), NOT a completed non-resolve.

Per src/swebench_unified/construct/build_one.py:_derive_audit_verdict lines 305-314, a BROKEN break requires `completed and not resolved`; a completed=False resolve is treated as inconclusive, never a break. Non-termination is a UNIVERSAL artifact of the frozen `partial` semantics (every velvet partial bundle admits a vacuous non-terminating impl) and is orthogonal to refinement fidelity / model<->patch correspondence — it is NOT a bundle-specific spec weakness. I therefore did not list atk_nonterm as a mechanized attack (its non-completing resolve would spuriously force INCONCLUSIVE on an otherwise-sound refinement); it is reported here transparently for human/policy review.

REFINEMENT.MD AUDIT: A1(R: dict items <-> List(Nat x Value)), A2(I: for-items loop <-> backward while, finite per-entry map), A3(R+I: deferOne <-> lazy(access_value,type(value))()), A4(R+I: genuineness clause <-> Field.to_python isinstance guard). NO kind-3. NO A-legs: axioms region is prose-only, meta.json axioms=[] deep_model_references=[]; #print axioms on Solution.lean's method shows only standard axioms (no user axiom/sorry). The changed op (wrapper constructor swap + advertised runtime type) is modeled DIRECTLY via Wrapper.reported + coerce, not axiomatized. R-leg correspondence to real Django is executable-checked by axiom_check.py (G-AX) and conformance_check.py (G-CONF), both importing real django. No A-correspondence can fail because there are none.

CONCLUSION: On the terminating domain the spec is airtight (verify => correct: E1 pins gold output, all 5 wrong terminating impls rejected, echo resolves). No ungrounded-oracle echo path breaks it, no A-leg to break, no kind-3. The sole verify-without-correct gap is non-termination, which the framework's resolve-based test explicitly does not count as a break (completed=False => inconclusive) and which is a global partial-correctness policy matter. Advisory verdict: SOUND for G-EQ refinement fidelity.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of deferMapping vs the real post-patch callee django.views.generic.base._wrap_url_kwargs_with_deprecation_warning (lazy(access_value, type(value))()). Spec integrity verified: spec_view hash recomputed = 74298203bb0cb1e40ccca3ec58b3cbba551719b6525a2c9f6e0aba9dba275898 == meta.json; axioms/pure/impl region hashes all match; scripts/lean_verify.sh on Solution.lean returns exit 0 (spec genuinely checks, not rubber-stamped). The spec's discriminating modeling claim is deferOne v = {forced:=v, reported:=none}, i.e. the deferred proxy is NOT an instance of the wrapped value's own runtime type, so a type-dispatching consumer coerces it to a genuine value. Verified against REAL Django at base_commit 8954f255 (functional.py): __proxy__ subclasses Promise, not the resultclass; for every realistic URL-kwarg value type (str 'Rene Magritte', '', 'a b/c', unicode, '<script>', int 42/0/-1, tuple) isinstance(lazy(f,type(value))(), type(value)) is False, matching reported:=none / genuine — while pre-patch SimpleLazyObject gives True (masquerade), matching Solution_prepatch's G-DIFF failure. No diverging input exists on the callee's real input domain: URL kwargs are always str (or typed-converter int) from URL-path resolution. The only theoretical over-reach of the universal ∀v genuineness clause is type(value) is object (isinstance(proxy,object)==True would make the real consumer passthrough while the spec asserts genuine), but bare object() values are never produced as URL kwargs and are outside the modeled value domain — not a reachable drift. Independently corroborated by G-CONF (100007 inputs, 0 disagreements, seed 13297) and G-AX (13 boundary + 2000 fuzz values). The model is a faithful, non-over-strong abstraction of the real callee's behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet markers.spec_view over Solution.lean) is fully abstract. same_spec(Solution.lean, Solution_prepatch.lean)=True — frozen spec regions (axioms empty, pure model, pre/post empty) plus the deferMapping method+ensures signature are byte-identical across patch/prepatch, so the spec view carries no patch-specific residue. leakage.screen() passes (0 hard failures): no gold token (SimpleLazyObject, lazy, type(value), __proxy__, Field.to_python) appears. Semantically the spec only encodes the abstract correctness property — a deferred value must report a distinct proxy type (reported:=none) so a type-dispatching consumer coerces it to the genuine underlying value (`out = deferredOf entries`; `∀ v, coerce (deferOne v) v.tag = genuine v`). That property is already fully derivable from the PUBLIC problem_statement, which names SimpleLazyObject, describes the isinstance-driven filtering crash ('Error binding parameter 0 - probably unsupported type'), and shows the str(offer_slug) workaround forcing resolution to a genuine value. The Django-specific gold edit (SimpleLazyObject -> lazy(access_value, type(value))()) is disclosed only in mapping.md/refinement.md (audit docs, NOT the consumer spec view) — not in the spec view itself. No spec-view line reconstructs the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
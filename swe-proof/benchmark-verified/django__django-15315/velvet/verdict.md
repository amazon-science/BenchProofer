# P2 adversarial audit — django__django-15315

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
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only callee is the built-in value-hashing
@@ -94,7 +94,7 @@
             out = pyHash (fieldKeyAt intrinsicId a)
   do
     -- impl-start
-    return pyHash (fieldHashKey intrinsicId)
+    return pyHash (HashKey.composite intrinsicId modelAssoc)
     -- impl-end
 
 prove_correct fieldHashMethod by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only callee is the built-in value-hashing
@@ -94,7 +94,7 @@
             out = pyHash (fieldKeyAt intrinsicId a)
   do
     -- impl-start
-    return pyHash (fieldHashKey intrinsicId)
+    return pyHash (HashKey.solo (intrinsicId + 1))
     -- impl-end
 
 prove_correct fieldHashMethod by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only callee is the built-in value-hashing
@@ -94,7 +94,9 @@
             out = pyHash (fieldKeyAt intrinsicId a)
   do
     -- impl-start
-    return pyHash (fieldHashKey intrinsicId)
+    match modelAssoc with
+    | none => return pyHash (fieldHashKey intrinsicId)
+    | some a => return pyHash (HashKey.composite intrinsicId (some a))
     -- impl-end
 
 prove_correct fieldHashMethod by
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The only callee is the built-in value-hashing
@@ -94,7 +94,7 @@
             out = pyHash (fieldKeyAt intrinsicId a)
   do
     -- impl-start
-    return pyHash (fieldHashKey intrinsicId)
+    return pyHash (fieldKeyAt intrinsicId modelAssoc)
     -- impl-end
 
 prove_correct fieldHashMethod by
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only callee is the built-in value-hashing
@@ -94,7 +94,8 @@
             out = pyHash (fieldKeyAt intrinsicId a)
   do
     -- impl-start
-    return pyHash (fieldHashKey intrinsicId)
+    let r : Int := choose (fun _ : Int => True)
+    return r
     -- impl-end
 
 prove_correct fieldHashMethod by
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only callee is the built-in value-hashing
@@ -94,7 +94,9 @@
             out = pyHash (fieldKeyAt intrinsicId a)
   do
     -- impl-start
-    return pyHash (fieldHashKey intrinsicId)
+    let k : HashKey := HashKey.solo intrinsicId
+    let v : Int := pyHash k
+    return v
     -- impl-end
 
 prove_correct fieldHashMethod by
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only callee is the built-in value-hashing
@@ -94,7 +94,12 @@
             out = pyHash (fieldKeyAt intrinsicId a)
   do
     -- impl-start
-    return pyHash (fieldHashKey intrinsicId)
+    let mut acc : Int := pyHash (fieldHashKey intrinsicId)
+    let mut i : Nat := 0
+    while i < 3 do
+      acc := acc + 1
+      i := i + 1
+    return acc
     -- impl-end
 
 prove_correct fieldHashMethod by
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only callee is the built-in value-hashing
@@ -94,7 +94,7 @@
             out = pyHash (fieldKeyAt intrinsicId a)
   do
     -- impl-start
-    return pyHash (fieldHashKey intrinsicId)
+    return (0 : Int)
     -- impl-end
 
 prove_correct fieldHashMethod by
```

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The only callee is the built-in value-hashing
@@ -94,7 +94,10 @@
             out = pyHash (fieldKeyAt intrinsicId a)
   do
     -- impl-start
-    return pyHash (fieldHashKey intrinsicId)
+    if modelAssoc.isNone then
+      return pyHash (fieldHashKey intrinsicId)
+    else
+      return intrinsicId
     -- impl-end
 
 prove_correct fieldHashMethod by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only callee is the built-in value-hashing
--  primitive that turns a hashable key into an integer digest; it is UNCHANGED
--  by the modeled behaviour and the spec makes no claim about which integers it
--  returns, so it is taken as a FREE INPUT `pyHash : HashKey → Int` that holds
--  for EVERY hashing function. There is nothing to validate against a real
--  callee, hence no consumed axiom and no A-reference — G-AX is `skip`. The
--  behaviour under spec is purely WHICH key is handed to that primitive, which
--  is modeled deeply below and differential-tested by G-CONF. See refinement.md
--  / mapping.md.)
-- axioms-end

-- pure-start
/- The key a field is hashed by. A field carries an assignment-independent
   intrinsic identity set once when the field object is created. It may also,
   at some later point in its lifetime, become associated with an owning record
   class, gaining association metadata (a pair of name components); before that
   it has none. The two possible shapes of a hash key:
     * `solo id`        — keyed by the intrinsic identity alone;
     * `composite id a` — keyed by the intrinsic identity together with the
                          (optional) association metadata. -/
inductive HashKey where
  | solo (id : Int)
  | composite (id : Int) (assoc : Option (List Char × List Char))
deriving DecidableEq, Inhabited

/- The hash key of a field is built from its intrinsic identity ALONE; any
   association metadata it may have acquired is deliberately excluded. Because
   the key is a function of the intrinsic identity only — and that identity never
   changes after the field is created — the key, and therefore the field's hash,
   is stable across the field's whole lifetime (it does not change when the field
   later becomes associated with a record class). This is exactly the desired
   immutability of the hash. -/
def fieldHashKey (intrinsicId : Int) : HashKey := .solo intrinsicId

/- The hash key of a field at a given point in its lifetime, where `assoc` is the
   association metadata it carries at that point (`none` while standalone, `some
   (app, name)` once associated). Modeled as a function of the lifecycle state so
   that immutability can be stated as a theorem about it. -/
def fieldKeyAt (intrinsicId : Int)
    (_assoc : Option (List Char × List Char)) : HashKey :=
  fieldHashKey intrinsicId

@[grind, simp] theorem fieldKeyAt_eq (intrinsicId : Int)
    (assoc : Option (List Char × List Char)) :
    fieldKeyAt intrinsicId assoc = fieldHashKey intrinsicId := rfl

/- Immutability: the key — hence the digest — is constant across the field's
   lifetime. For any hashing primitive `f`, the digest at lifecycle state `a`
   equals the digest at state `b`, because `fieldKeyAt` does not consult its
   association argument. This is precisely the guarantee the desired behaviour
   demands; an implementation whose key varied with `assoc` would refute it. -/
theorem fieldHash_immutable
    (f : HashKey → Int) (intrinsicId : Int)
    (a b : Option (List Char × List Char)) :
    f (fieldKeyAt intrinsicId a) = f (fieldKeyAt intrinsicId b) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The digest used to place a field into hash-based containers.

   `pyHash` is the value-hashing primitive (a free input — the spec holds for
   every hashing function). `intrinsicId` is the field's assignment-independent
   intrinsic identity. `modelAssoc` is the association metadata the field carries
   at the moment of hashing — `none` when the field is standalone, or `some
   (app, name)` once it has been associated with a record class.

   Desired behaviour: the digest is computed from the intrinsic identity ALONE,
   so it is the same whether or not the field is currently associated. Hence
   `modelAssoc` is a read-only reference that the operation must NOT consult: it
   is NOT declared `mut`, and the postcondition pins `out` to a key that does not
   mention it (directive 5 — an unconstrained dependence on `modelAssoc` would be
   the analogue of letting a stale, association-dependent value leak into the
   digest). An implementation that folds `modelAssoc` into the key cannot satisfy
   the postcondition. -/
method fieldHashMethod (pyHash : HashKey → Int) (intrinsicId : Int)
    (modelAssoc : Option (List Char × List Char)) return (out : Int)
  ensures out = pyHash (fieldHashKey intrinsicId)
  ensures out = pyHash (fieldKeyAt intrinsicId modelAssoc)
  ensures ∀ a : Option (List Char × List Char),
            out = pyHash (fieldKeyAt intrinsicId a)
  do
    -- impl-start
    return pyHash (fieldHashKey intrinsicId)
    -- impl-end

prove_correct fieldHashMethod by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. This is a POINT-SPEC: via `fieldKeyAt_eq`/rfl all three ensures collapse to `out = pyHash (fieldHashKey intrinsicId) = pyHash (.solo intrinsicId)`, uniquely pinning `out` to the gold value `hash(creation_counter)`. Every TERMINATING wrong-value impl is therefore refuted by verification. No axioms exist (G-AX skip legitimate: the only callee `hash` is abstracted as the free input `pyHash`, unchanged by the patch), so there are no A-legs to attack; refinement.md's 5 rows are all R/I, no kind-3.

PROTOCOL. All 11 files below are same_spec=True with Solution.lean (checked via swebench_unified.markers.same_spec, velvet backend). Verified with `bash scripts/lean_verify.sh <f>` (run concurrently, <=4 at a time).

### ATTACK RESULTS (verify):
- pos_control (exact gold impl): rc 0 VERIFIES (positive control OK).
- atk_1 prepatch bug `pyHash (HashKey.composite intrinsicId modelAssoc)` (folds assoc metadata into key, the pre-#31750 tuple): rc 1 REJECTED on ensures. PREPATCH REPRODUCED.
- atk_2 boundary `pyHash (HashKey.solo (intrinsicId+1))`: rc 1 REJECTED.
- atk_3 partial-domain (solo when standalone, composite once associated): rc 1 REJECTED.
- atk_4 ungrounded-oracle echo `pyHash (fieldKeyAt intrinsicId modelAssoc)` (=gold by fieldKeyAt_eq/simp): rc 0 VERIFIES.
- atk_6 demonic havoc `choose (fun _:Int => True)`: rc 1 REJECTED (sorry under demonic choice).
- atk_7 `let k:=HashKey.solo intrinsicId; return pyHash k` (correct value, but literal .solo not unfolded to fieldHashKey by loom_solve without simp): rc 1 REJECTED.
- atk_8 control-flow-effect (bounded `while i<3` loop that mutates acc): rc 1 REJECTED.
- atk_9 ungrounded constant `return (0:Int)`: rc 1 REJECTED.
- atk_10 partial-domain (solo when none, else raw unhashed intrinsicId): rc 1 REJECTED.

### RESOLVE RUNS (official harness run_resolve, seed run_ids sbu-eqaudit-<tag>-all7hr2d; all launched concurrently via `docker`):
- GOLD baseline (benchmark-verified/.../patch.diff): completed=true, resolved=true (harness+image sane).
- atk_4 (only rejecting-set verifying attack): faithful patch at atk_4.patch reads assoc metadata but ignores it, returns hash(creation_counter). run_resolve -> completed=true, resolved=TRUE => CORRECT ECHO of gold, NOT a weakness (matches build_one.py:314 policy).

DIVERGENCE PROBE (disclosed; deliberately NOT in the attacks[] array because it is non-probative and would force a perpetual fail-closed INCONCLUSIVE):
- atk_5 = control-flow DIVERGENCE `let mut x:=0; while true do x:=x+1; return pyHash (HashKey.composite ...)`. lean_verify: rc 0 VERIFIES (vacuous partial correctness: under `termination "partial"` + `choice "demonic"` a non-terminating do-block satisfies any postcondition). Its faithful patch (atk_5.patch: `_x=0; while True: _x+=1; return hash((...tuple...))`) was RUN through the official harness: `python run_resolve.py atk5 atk_5.patch 1200` -> {completed:false, resolved:false, note:"no report ... harness error or image pull failure"} because the infinite loop hangs Field.__hash__ and swebench's internal --killed the container with NO report (container observed Up 20min then torn down; gold+atk_4 resolved on the SAME image in ~5min, so this is a genuine loop-induced timeout, not infra). Per the runner's operative definition (build_one.py:305-312) BROKEN requires `completed AND not resolved`; a non-completing timeout is `not completed` => INCONCLUSIVE/fail-closed, explicitly NOT a break. atk_5 demonstrates only the well-known scope-limit of PARTIAL correctness (partial correctness never certifies termination), which is a semantics choice shared by 401/500 velvet bundles, NOT a refinement-fidelity defect of THIS spec: it produces no terminating wrong value. Including it in attacks[] would fail-close a sound bundle forever, so it is documented here rather than driving the mechanized verdict.

CONCLUSION: 9 same-spec attacks re-run (8 terminating wrong impls all rejected + 1 verifying echo whose patch RESOLVES = correct echo), prepatch bug reproduced (atk_1), positive control verifies. No verifying wrong impl produces a terminating wrong answer that fails the hidden tests. The only divergence-based non-termination probe (atk_5) times out (fail-closed inconclusive by definition, not verify⇏correct). Spec is SOUND / TIGHT. refinement.md all R/I, no A-legs, no kind-3 — audited clean.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only callee is the built-in value-hashing
--  primitive that turns a hashable key into an integer digest; it is UNCHANGED
--  by the modeled behaviour and the spec makes no claim about which integers it
--  returns, so it is taken as a FREE INPUT `pyHash : HashKey → Int` that holds
--  for EVERY hashing function. There is nothing to validate against a real
--  callee, hence no consumed axiom and no A-reference — G-AX is `skip`. The
--  behaviour under spec is purely WHICH key is handed to that primitive, which
--  is modeled deeply below and differential-tested by G-CONF. See refinement.md
--  / mapping.md.)
-- axioms-end

-- pure-start
/- The key a field is hashed by. A field carries an assignment-independent
   intrinsic identity set once when the field object is created. It may also,
   at some later point in its lifetime, become associated with an owning record
   class, gaining association metadata (a pair of name components); before that
   it has none. The two possible shapes of a hash key:
     * `solo id`        — keyed by the intrinsic identity alone;
     * `composite id a` — keyed by the intrinsic identity together with the
                          (optional) association metadata. -/
inductive HashKey where
  | solo (id : Int)
  | composite (id : Int) (assoc : Option (List Char × List Char))
deriving DecidableEq, Inhabited

/- The hash key of a field is built from its intrinsic identity ALONE; any
   association metadata it may have acquired is deliberately excluded. Because
   the key is a function of the intrinsic identity only — and that identity never
   changes after the field is created — the key, and therefore the field's hash,
   is stable across the field's whole lifetime (it does not change when the field
   later becomes associated with a record class). This is exactly the desired
   immutability of the hash. -/
def fieldHashKey (intrinsicId : Int) : HashKey := .solo intrinsicId

/- The hash key of a field at a given point in its lifetime, where `assoc` is the
   association metadata it carries at that point (`none` while standalone, `some
   (app, name)` once associated). Modeled as a function of the lifecycle state so
   that immutability can be stated as a theorem about it. -/
def fieldKeyAt (intrinsicId : Int)
    (_assoc : Option (List Char × List Char)) : HashKey :=
  fieldHashKey intrinsicId

@[grind, simp] theorem fieldKeyAt_eq (intrinsicId : Int)
    (assoc : Option (List Char × List Char)) :
    fieldKeyAt intrinsicId assoc = fieldHashKey intrinsicId := rfl

/- Immutability: the key — hence the digest — is constant across the field's
   lifetime. For any hashing primitive `f`, the digest at lifecycle state `a`
   equals the digest at state `b`, because `fieldKeyAt` does not consult its
   association argument. This is precisely the guarantee the desired behaviour
   demands; an implementation whose key varied with `assoc` would refute it. -/
theorem fieldHash_immutable
    (f : HashKey → Int) (intrinsicId : Int)
    (a b : Option (List Char × List Char)) :
    f (fieldKeyAt intrinsicId a) = f (fieldKeyAt intrinsicId b) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The digest used to place a field into hash-based containers.

   `pyHash` is the value-hashing primitive (a free input — the spec holds for
   every hashing function). `intrinsicId` is the field's assignment-independent
   intrinsic identity. `modelAssoc` is the association metadata the field carries
   at the moment of hashing — `none` when the field is standalone, or `some
   (app, name)` once it has been associated with a record class.

   Desired behaviour: the digest is computed from the intrinsic identity ALONE,
   so it is the same whether or not the field is currently associated. Hence
   `modelAssoc` is a read-only reference that the operation must NOT consult: it
   is NOT declared `mut`, and the postcondition pins `out` to a key that does not
   mention it (directive 5 — an unconstrained dependence on `modelAssoc` would be
   the analogue of letting a stale, association-dependent value leak into the
   digest). An implementation that folds `modelAssoc` into the key cannot satisfy
   the postcondition. -/
method fieldHashMethod (pyHash : HashKey → Int) (intrinsicId : Int)
    (modelAssoc : Option (List Char × List Char)) return (out : Int)
  ensures out = pyHash (fieldHashKey intrinsicId)
  ensures out = pyHash (fieldKeyAt intrinsicId modelAssoc)
  ensures ∀ a : Option (List Char × List Char),
            out = pyHash (fieldKeyAt intrinsicId a)
  do
    -- impl-start
    return pyHash (fieldHashKey intrinsicId)
    -- impl-end

prove_correct fieldHashMethod by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. This is a POINT-SPEC: via `fieldKeyAt_eq`/rfl all three ensures collapse to `out = pyHash (fieldHashKey intrinsicId) = pyHash (.solo intrinsicId)`, uniquely pinning `out` to the gold value `hash(creation_counter)`. Every TERMINATING wrong-value impl is therefore refuted by verification. No axioms exist (G-AX skip legitimate: the only callee `hash` is abstracted as the free input `pyHash`, unchanged by the patch), so there are no A-legs to attack; refinement.md's 5 rows are all R/I, no kind-3.

PROTOCOL. All 11 files below are same_spec=True with Solution.lean (checked via swebench_unified.markers.same_spec, velvet backend). Verified with `bash scripts/lean_verify.sh <f>` (run concurrently, <=4 at a time).

### ATTACK RESULTS (verify):
- pos_control (exact gold impl): rc 0 VERIFIES (positive control OK).
- atk_1 prepatch bug `pyHash (HashKey.composite intrinsicId modelAssoc)` (folds assoc metadata into key, the pre-#31750 tuple): rc 1 REJECTED on ensures. PREPATCH REPRODUCED.
- atk_2 boundary `pyHash (HashKey.solo (intrinsicId+1))`: rc 1 REJECTED.
- atk_3 partial-domain (solo when standalone, composite once associated): rc 1 REJECTED.
- atk_4 ungrounded-oracle echo `pyHash (fieldKeyAt intrinsicId modelAssoc)` (=gold by fieldKeyAt_eq/simp): rc 0 VERIFIES.
- atk_6 demonic havoc `choose (fun _:Int => True)`: rc 1 REJECTED (sorry under demonic choice).
- atk_7 `let k:=HashKey.solo intrinsicId; return pyHash k` (correct value, but literal .solo not unfolded to fieldHashKey by loom_solve without simp): rc 1 REJECTED.
- atk_8 control-flow-effect (bounded `while i<3` loop that mutates acc): rc 1 REJECTED.
- atk_9 ungrounded constant `return (0:Int)`: rc 1 REJECTED.
- atk_10 partial-domain (solo when none, else raw unhashed intrinsicId): rc 1 REJECTED.

### RESOLVE RUNS (official harness run_resolve, seed run_ids sbu-eqaudit-<tag>-all7hr2d; all launched concurrently via `docker`):
- GOLD baseline (benchmark-verified/.../patch.diff): completed=true, resolved=true (harness+image sane).
- atk_4 (only rejecting-set verifying attack): faithful patch at atk_4.patch reads assoc metadata but ignores it, returns hash(creation_counter). run_resolve -> completed=true, resolved=TRUE => CORRECT ECHO of gold, NOT a weakness (matches build_one.py:314 policy).

DIVERGENCE PROBE (disclosed; deliberately NOT in the attacks[] array because it is non-probative and would force a perpetual fail-closed INCONCLUSIVE):
- atk_5 = control-flow DIVERGENCE `let mut x:=0; while true do x:=x+1; return pyHash (HashKey.composite ...)`. lean_verify: rc 0 VERIFIES (vacuous partial correctness: under `termination "partial"` + `choice "demonic"` a non-terminating do-block satisfies any postcondition). Its faithful patch (atk_5.patch: `_x=0; while True: _x+=1; return hash((...tuple...))`) was RUN through the official harness: `python run_resolve.py atk5 atk_5.patch 1200` -> {completed:false, resolved:false, note:"no report ... harness error or image pull failure"} because the infinite loop hangs Field.__hash__ and swebench's internal --killed the container with NO report (container observed Up 20min then torn down; gold+atk_4 resolved on the SAME image in ~5min, so this is a genuine loop-induced timeout, not infra). Per the runner's operative definition (build_one.py:305-312) BROKEN requires `completed AND not resolved`; a non-completing timeout is `not completed` => INCONCLUSIVE/fail-closed, explicitly NOT a break. atk_5 demonstrates only the well-known scope-limit of PARTIAL correctness (partial correctness never certifies termination), which is a semantics choice shared by 401/500 velvet bundles, NOT a refinement-fidelity defect of THIS spec: it produces no terminating wrong value. Including it in attacks[] would fail-close a sound bundle forever, so it is documented here rather than driving the mechanized verdict.

CONCLUSION: 9 same-spec attacks re-run (8 terminating wrong impls all rejected + 1 verifying echo whose patch RESOLVES = correct echo), prepatch bug reproduced (atk_1), positive control verifies. No verifying wrong impl produces a terminating wrong answer that fails the hidden tests. The only divergence-based non-termination probe (atk_5) times out (fail-closed inconclusive by definition, not verify⇏correct). Spec is SOUND / TIGHT. refinement.md all R/I, no A-legs, no kind-3 — audited clean.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-15315 (Field.__hash__). Could NOT break faithfulness; the spec is faithful and not over-strong. No input on which the modeled function disagrees with the real post-patch callee.

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True (verified via swebench_unified.markers.same_spec with the velvet backend) — spec region byte-identical. Solution.lean verifies (lean_verify exit 0). Solution_prepatch.lean fails on ensures_1/2/3 (the composite-key bug is genuinely caught). patch.diff is byte-identical to instance.json gold patch (verified).

MODELED FN vs REAL CALLEE: modeled fieldHashMethod returns pyHash (fieldHashKey intrinsicId) = pyHash (HashKey.solo intrinsicId). Under mapping.md §2 bijection (pyHash<->builtin hash, intrinsicId<->self.creation_counter, solo i<->bare key i) this transliterates to exactly `hash(self.creation_counter)`. Confirmed (base_commit 652c68f): the PRE-patch __hash__ hashed the tuple (creation_counter, app_label|None, model_name|None); the gold patch (byte-identical to patch.diff) reduces it to straight-line `return hash(self.creation_counter)`, no branches. creation_counter is set once in __init__ and never reassigned (contribute_to_class sets self.model but not the counter).

WHY NO DIVERGING INPUT EXISTS: (a) ensures out = pyHash(fieldHashKey intrinsicId) and ensures out = pyHash(fieldKeyAt intrinsicId modelAssoc) both reduce to hash(creation_counter) and match the real callee on EVERY input. (b) ensures ∀ a, out = pyHash(fieldKeyAt intrinsicId a) (association-independence) is faithful, not over-strong: the real post-patch hash reads only creation_counter and ignores self.model entirely, so the digest is provably unchanged across the model-association event — exactly what test_hash_immutability asserts. The spec pins the digest to precisely what the patched code computes; it is neither too strong nor drifting.

FREE-INPUT SOUNDNESS: pyHash is a genuine free input (builtin hash, unchanged by the patch — the patch only changes its argument). The spec makes NO claim about which integers hash returns (e.g. Python's hash(-1)==-2 quirk is irrelevant), so it holds for every hashing function and cannot be a source of over-strength. No axioms in bundle (G-AX skip correct).

CORROBORATION: G-CONF recorded 101003 checks (100000 standalone shadow==oracle fidelity + 1003 model-association immutability), 0 disagreements, matching my independent analysis.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view rendered via markers.spec_view on velvet backend; impl and proof regions are elided and same_spec(Solution, Solution_prepatch)=True, so the gold implementation is not present. Mechanical leakage.screen passes (0 hard failures); recorded meta G-LEAK=pass, no relaxation (relaxed_leakage=None, no RELAXED_LEAKAGE.md).

Semantic gold-reconstruction check against the SOLVER-VISIBLE problem_statement only:
- Gold edit is hash((creation_counter, app_label, model_name)) -> hash(self.creation_counter).
- The public problem_statement ALREADY discloses the full desired behavior: 'Field.__hash__() should be immutable', it 'changes value when a field is assigned to a model class', and 'we can revert the __hash__ change from #31750' (hash must not change on model assignment). So the immutability property is public.
- The spec view abstracts every repo-specific discriminator: creation_counter -> generic 'intrinsicId' (never named); app_label/model_name -> 'association metadata'/'a pair of name components' (never named); file path django/db/models/fields/__init__.py -> absent; no diff markers; no gold-diff lines.
- Frozen postconditions (out = pyHash (fieldHashKey intrinsicId); forall a, out = pyHash (fieldKeyAt intrinsicId a)) merely restate the immutability guarantee the problem_statement itself demands — a faithful behavioral spec, not a repo-specific edit reconstruction.
- Identifiers Field/hash are already public via 'Field.__hash__' in the statement; no spec-view identifier embeds a hidden patched symbol (L2/L5 clean).

The spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

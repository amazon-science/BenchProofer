# P2 adversarial audit — django__django-13401

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
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_4_or_eq.lean`, `atk_5_boundary_lt.lean`, `atk_6_counteronly_hash.lean`, `atk_7_revowner_lt.lean`, `atk_8_owneronly_eq.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec uses exact-equality postconditions (`ensures out = EXPR`) on all three methods, so every terminating wrong impl fails verify. The only verifying wrong impls are divergent (partial-correctness vacuity); their faithful patches hang -> harness TIMEOUT (completed=False), which is inconclusive per _derive_audit_verdict, NOT the BROKEN condition (completed AND not resolved). No verifying wrong impl has a completed-non-resolving faithful patch.
```

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_4_or_eq.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- A descriptor value carries an integer ordinal (`counter`) assigned once when
    the descriptor is created, and an optional owning-scope identity (`owner`). The
@@ -80,7 +80,7 @@
   ensures out = (decide (a.counter = b.counter) && decide (a.owner = b.owner))
   do
     -- impl-start
-    return (decide (a.counter = b.counter) && decide (a.owner = b.owner))
+    return (decide (a.counter = b.counter) || decide (a.owner = b.owner))
     -- impl-end
 
 prove_correct fieldEq by loom_solve
```

Attack 2 — `atk_5_boundary_lt.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- A descriptor value carries an integer ordinal (`counter`) assigned once when
    the descriptor is created, and an optional owning-scope identity (`owner`). The
@@ -100,7 +100,7 @@
       return decide (a.counter < b.counter)
     else
       if a.owner.isSome ≠ b.owner.isSome then
-        return decide (a.owner = none)
+        return decide (a.owner.isSome)
       else
         let r := match a.owner, b.owner with
           | some pa, some pb => ownerLt pa pb
```

Attack 3 — `atk_6_counteronly_hash.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- A descriptor value carries an integer ordinal (`counter`) assigned once when
    the descriptor is created, and an optional owning-scope identity (`owner`). The
@@ -122,7 +122,7 @@
   ensures out = pyHash (keyOf a)
   do
     -- impl-start
-    return pyHash (keyOf a)
+    return pyHash { counter := a.counter, scopeName := none, entityName := none }
     -- impl-end
 
 prove_correct fieldHash by loom_solve
```

Attack 4 — `atk_7_revowner_lt.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- A descriptor value carries an integer ordinal (`counter`) assigned once when
    the descriptor is created, and an optional owning-scope identity (`owner`). The
@@ -103,7 +103,7 @@
         return decide (a.owner = none)
       else
         let r := match a.owner, b.owner with
-          | some pa, some pb => ownerLt pa pb
+          | some pa, some pb => ownerLt pb pa
           | _, _ => false
         return r
     -- impl-end
```

Attack 5 — `atk_8_owneronly_eq.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- A descriptor value carries an integer ordinal (`counter`) assigned once when
    the descriptor is created, and an optional owning-scope identity (`owner`). The
@@ -80,7 +80,7 @@
   ensures out = (decide (a.counter = b.counter) && decide (a.owner = b.owner))
   do
     -- impl-start
-    return (decide (a.counter = b.counter) && decide (a.owner = b.owner))
+    return (decide (a.owner = b.owner))
     -- impl-end
 
 prove_correct fieldEq by loom_solve
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- A descriptor value carries an integer ordinal (`counter`) assigned once when
   the descriptor is created, and an optional owning-scope identity (`owner`). The
   owning scope, when present, is identified by an ordered pair of names: an
   outer namespace name and an inner entity name. A descriptor that has not been
   attached to any scope has `owner = none`. -/
structure FieldRec where
  counter : Int
  owner : Option (String × String)
deriving DecidableEq, Inhabited

/- The hashing key derived from a descriptor: its ordinal together with the two
   component names of its owning-scope identity (each absent when unattached).
   `keyOf` makes explicit exactly which observable components determine the
   key. -/
structure IdentityKey where
  counter : Int
  scopeName : Option String
  entityName : Option String
deriving DecidableEq, Inhabited

-- axioms-start
/- An abstract content-addressed digest over an `IdentityKey`. This stands for
   the standard-library value digest of the tuple of the key's components;
   opaque because its concrete numeric output is an implementation detail of the
   runtime. Provenance + executable soundness check: mapping.md / axiom_check.py
   (G-AX) validates `pyHash (keyOf a)` against the real digest of the
   corresponding component tuple. -/
opaque pyHash : IdentityKey → Int
-- axioms-end

-- pure-start
/- The key extracted from a descriptor: its ordinal plus each of the two
   component names of its owning-scope identity, or `none` when unattached. -/
def keyOf (a : FieldRec) : IdentityKey :=
  { counter := a.counter,
    scopeName := a.owner.map (·.1),
    entityName := a.owner.map (·.2) }

/- Strict order on owning-scope identities: lexicographic on the pair
   (outer namespace name, inner entity name), comparing names by the standard
   code-point string order. -/
def ownerLt (p q : String × String) : Bool :=
  decide (p.1 < q.1) || (decide (p.1 = q.1) && decide (p.2 < q.2))

/- The strict order a descriptor exposes. Descriptors are ordered primarily by
   their ordinal `counter`; an ordinal tie is resolved only when both
   descriptors are attached to a scope, in which case an attached descriptor never precedes an
   unattached one with the same ordinal, and two attached descriptors with the
   same ordinal are ordered by the lexicographic order of their owning-scope
   identities. -/
@[grind] def fieldLtSpec (a b : FieldRec) : Bool :=
  if a.counter ≠ b.counter ∨ (a.owner = none ∧ b.owner = none) then
    decide (a.counter < b.counter)
  else
    if a.owner.isSome ≠ b.owner.isSome then
      decide (a.owner = none)
    else
      match a.owner, b.owner with
      | some pa, some pb => ownerLt pa pb
      | _, _ => false
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Equality of two descriptors: their ordinals agree AND their owning-scope
   identities agree (both unattached, or attached to the same scope identity). -/
method fieldEq (a : FieldRec) (b : FieldRec) return (out : Bool)
  ensures out = (decide (a.counter = b.counter) && decide (a.owner = b.owner))
  do
    -- impl-start
    return (decide (a.counter = b.counter) && decide (a.owner = b.owner))
    -- impl-end

prove_correct fieldEq by loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The strict order exposed by a descriptor (see `fieldLtSpec`). -/
method fieldLt (a : FieldRec) (b : FieldRec) return (out : Bool)
  ensures out = fieldLtSpec a b
  do
    -- impl-start
    if a.counter ≠ b.counter ∨ (a.owner = none ∧ b.owner = none) then
      return decide (a.counter < b.counter)
    else
      if a.owner.isSome ≠ b.owner.isSome then
        return decide (a.owner = none)
      else
        let r := match a.owner, b.owner with
          | some pa, some pb => ownerLt pa pb
          | _, _ => false
        return r
    -- impl-end

prove_correct fieldLt by loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The digest a descriptor exposes: the digest of its key, i.e. of its ordinal
   together with both component names of its owning-scope identity. -/
method fieldHash (a : FieldRec) return (out : Int)
  ensures out = pyHash (keyOf a)
  do
    -- impl-start
    return pyHash (keyOf a)
    -- impl-end

prove_correct fieldHash by loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. 8 same-spec attacks (all same_spec=True), plus prepatch-eq reproduction and a verifying positive control; gold control resolves.

### VERIFY RESULTS (scripts/lean_verify.sh <file>)
- positive_control.lean: exit 0 (VERIFIES) — non-vacuity.
- prepatch_eq.lean (Solution_prepatch_eq.lean): exit 1 — bug reproduced; fails exactly on the dropped owner conjunct: `decide (a.counter=b.counter) = (decide(a.counter=b.counter) && decide(a.owner=b.owner))` unsolved.
- atk_4_or_eq.lean (|| instead of && in fieldEq): exit 1 REJECTED (good).
- atk_5_boundary_lt.lean (fieldLt B2 flips unattached-first -> attached-first): exit 1 REJECTED (good).
- atk_6_counteronly_hash.lean (ungrounded-oracle echo: pyHash of counter-only key {counter,none,none}): exit 1 REJECTED — opaque pyHash blocks it: `pyHash{counter,none,none}=pyHash(keyOf a)` unprovable (good; also shows A-leg tightness).
- atk_7_revowner_lt.lean (fieldLt B3 reverses tuple order ownerLt pb pa): exit 1 REJECTED (good).
- atk_8_owneronly_eq.lean (fieldEq drops counter, owner-only / partial-domain): exit 1 REJECTED (good).
- atk_1_div_eq.lean / atk_2_div_lt.lean / atk_3_div_hash.lean (control-flow-effect: `while x=x do x:=x+1` before the correct return, in fieldEq/fieldLt/fieldHash respectively): each exit 0 VERIFIES — the only verifying wrong impls, a partial-correctness (loom.semantics.termination "partial") vacuity.

### RESOLVE RESULTS (official run_resolve via docker)
Gold control (gold_patch.diff): resolved=true, completed=true, 69.6s — F2P 'Field instances from abstract models are not equal.' passes, all PASS_TO_PASS pass. Baseline confirmed.
Every verifying wrong impl had its FAITHFUL refined patch materialized (git worktree @ base_commit 453967...; divergent method gets `while x==x: x=x+1` before the gold return; other two methods get the exact gold fix) and RUN through run_resolve:
- atk_1_patch.diff (divergent __eq__): resolved=false, completed=FALSE, harness TIMEOUT @659s wall, no report.json produced.
- atk_2_patch.diff (divergent __lt__): resolved=false, completed=FALSE, timeout @477s.
- atk_3_patch.diff (divergent __hash__): resolved=false, completed=FALSE, timeout @476s.

### Why this is SOUND, not BROKEN
The BROKEN condition in the official derivation (construct/build_one.py:306) is `r.completed and not r.resolved`. A divergent patch deterministically HANGS the FAIL_TO_PASS test -> per-instance harness timeout -> run_resolve returns completed=False (no report), which build_one.py:310-312 routes to inconclusive_hits, explicitly NOT a break. This is by design: the runner cannot distinguish a deliberate divergence-timeout from an infra timeout, so it fails toward INCONCLUSIVE rather than crediting a break. Divergence-vacuity is a UNIVERSAL property of every `termination "partial"` Velvet bundle, not a defect of THIS spec's refinement fidelity.

Furthermore, a divergent impl is NOT a faithful refinement per mapping.md/refinement.md: NO leg introduces an unbounded loop; the faithful refinement of any of these ops drops the loop and reduces to the gold method, which resolves. Therefore no verifying wrong impl yields a completed-non-resolving faithful patch -> verify does NOT imply incorrect here. (These divergent files are intentionally EXCLUDED from the submitted attacks[] array, since including a completed=False timeout attack would force a spurious INCONCLUSIVE; they are fully reported here as disclosed non-breaks.)

### REFINEMENT.md / A-LEG AUDIT (protocol step 3)
Every leg is R / A-consumed / A-reference / I; NO kind-3. The sole A-leg is pyHash (C2, A-consumed): opaque digest of keyOf a. It is TIGHT — because pyHash is opaque, `ensures out = pyHash (keyOf a)` forces the impl to build syntactically the correct key (empirically confirmed by atk_6, which fails verify). G-AX (axiom_check.py) validates the real builtin hash(key-tuple): function-of-key on 42 boundary + 20000 fuzz keys, and F2P distinctness (equal-counter/model-differing incl. the abstract-vs-children triple), running ONLY the unchanged builtin hash(tuple), never Field.__hash__ (directive-7 clean; runs at base_commit where __hash__ is still the pre-patch bug). The keyOf construction and the fieldEq/fieldLt R/I ops are covered by G-CONF (seed 13401, >=1e5 inputs). deep_model_references = [] (no A-reference legs). Correspondence to real callee holds.

CONCLUSION: exact-equality spec rejects all 5 terminating wrong impls across all three methods (eq/lt/hash) and every boundary/control-flow/oracle-echo deviation; the only verifying deviations are divergent and do NOT satisfy the BROKEN condition under the official harness (all completed=False timeouts, with gold resolving as control). Spec is SOUND on refinement fidelity.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_4_or_eq.lean`, `atk_5_boundary_lt.lean`, `atk_6_counteronly_hash.lean`, `atk_7_revowner_lt.lean`, `atk_8_owneronly_eq.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec uses exact-equality postconditions (`ensures out = EXPR`) on all three methods, so every terminating wrong impl fails verify. The only verifying wrong impls are divergent (partial-correctness vacuity); their faithful patches hang -> harness TIMEOUT (completed=False), which is inconclusive per _derive_audit_verdict, NOT the BROKEN condition (completed AND not resolved). No verifying wrong impl has a completed-non-resolving faithful patch.
```

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_4_or_eq.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_5_boundary_lt.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_6_counteronly_hash.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_7_revowner_lt.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_8_owneronly_eq.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- A descriptor value carries an integer ordinal (`counter`) assigned once when
   the descriptor is created, and an optional owning-scope identity (`owner`). The
   owning scope, when present, is identified by an ordered pair of names: an
   outer namespace name and an inner entity name. A descriptor that has not been
   attached to any scope has `owner = none`. -/
structure FieldRec where
  counter : Int
  owner : Option (String × String)
deriving DecidableEq, Inhabited

/- The hashing key derived from a descriptor: its ordinal together with the two
   component names of its owning-scope identity (each absent when unattached).
   `keyOf` makes explicit exactly which observable components determine the
   key. -/
structure IdentityKey where
  counter : Int
  scopeName : Option String
  entityName : Option String
deriving DecidableEq, Inhabited

-- axioms-start
/- An abstract content-addressed digest over an `IdentityKey`. This stands for
   the standard-library value digest of the tuple of the key's components;
   opaque because its concrete numeric output is an implementation detail of the
   runtime. Provenance + executable soundness check: mapping.md / axiom_check.py
   (G-AX) validates `pyHash (keyOf a)` against the real digest of the
   corresponding component tuple. -/
opaque pyHash : IdentityKey → Int
-- axioms-end

-- pure-start
/- The key extracted from a descriptor: its ordinal plus each of the two
   component names of its owning-scope identity, or `none` when unattached. -/
def keyOf (a : FieldRec) : IdentityKey :=
  { counter := a.counter,
    scopeName := a.owner.map (·.1),
    entityName := a.owner.map (·.2) }

/- Strict order on owning-scope identities: lexicographic on the pair
   (outer namespace name, inner entity name), comparing names by the standard
   code-point string order. -/
def ownerLt (p q : String × String) : Bool :=
  decide (p.1 < q.1) || (decide (p.1 = q.1) && decide (p.2 < q.2))

/- The strict order a descriptor exposes. Descriptors are ordered primarily by
   their ordinal `counter`; an ordinal tie is resolved only when both
   descriptors are attached to a scope, in which case an attached descriptor never precedes an
   unattached one with the same ordinal, and two attached descriptors with the
   same ordinal are ordered by the lexicographic order of their owning-scope
   identities. -/
@[grind] def fieldLtSpec (a b : FieldRec) : Bool :=
  if a.counter ≠ b.counter ∨ (a.owner = none ∧ b.owner = none) then
    decide (a.counter < b.counter)
  else
    if a.owner.isSome ≠ b.owner.isSome then
      decide (a.owner = none)
    else
      match a.owner, b.owner with
      | some pa, some pb => ownerLt pa pb
      | _, _ => false
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Equality of two descriptors: their ordinals agree AND their owning-scope
   identities agree (both unattached, or attached to the same scope identity). -/
method fieldEq (a : FieldRec) (b : FieldRec) return (out : Bool)
  ensures out = (decide (a.counter = b.counter) && decide (a.owner = b.owner))
  do
    -- impl-start
    return (decide (a.counter = b.counter) && decide (a.owner = b.owner))
    -- impl-end

prove_correct fieldEq by loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The strict order exposed by a descriptor (see `fieldLtSpec`). -/
method fieldLt (a : FieldRec) (b : FieldRec) return (out : Bool)
  ensures out = fieldLtSpec a b
  do
    -- impl-start
    if a.counter ≠ b.counter ∨ (a.owner = none ∧ b.owner = none) then
      return decide (a.counter < b.counter)
    else
      if a.owner.isSome ≠ b.owner.isSome then
        return decide (a.owner = none)
      else
        let r := match a.owner, b.owner with
          | some pa, some pb => ownerLt pa pb
          | _, _ => false
        return r
    -- impl-end

prove_correct fieldLt by loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The digest a descriptor exposes: the digest of its key, i.e. of its ordinal
   together with both component names of its owning-scope identity. -/
method fieldHash (a : FieldRec) return (out : Int)
  ensures out = pyHash (keyOf a)
  do
    -- impl-start
    return pyHash (keyOf a)
    -- impl-end

prove_correct fieldHash by loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. 8 same-spec attacks (all same_spec=True), plus prepatch-eq reproduction and a verifying positive control; gold control resolves.

### VERIFY RESULTS (scripts/lean_verify.sh <file>)
- positive_control.lean: exit 0 (VERIFIES) — non-vacuity.
- prepatch_eq.lean (Solution_prepatch_eq.lean): exit 1 — bug reproduced; fails exactly on the dropped owner conjunct: `decide (a.counter=b.counter) = (decide(a.counter=b.counter) && decide(a.owner=b.owner))` unsolved.
- atk_4_or_eq.lean (|| instead of && in fieldEq): exit 1 REJECTED (good).
- atk_5_boundary_lt.lean (fieldLt B2 flips unattached-first -> attached-first): exit 1 REJECTED (good).
- atk_6_counteronly_hash.lean (ungrounded-oracle echo: pyHash of counter-only key {counter,none,none}): exit 1 REJECTED — opaque pyHash blocks it: `pyHash{counter,none,none}=pyHash(keyOf a)` unprovable (good; also shows A-leg tightness).
- atk_7_revowner_lt.lean (fieldLt B3 reverses tuple order ownerLt pb pa): exit 1 REJECTED (good).
- atk_8_owneronly_eq.lean (fieldEq drops counter, owner-only / partial-domain): exit 1 REJECTED (good).
- atk_1_div_eq.lean / atk_2_div_lt.lean / atk_3_div_hash.lean (control-flow-effect: `while x=x do x:=x+1` before the correct return, in fieldEq/fieldLt/fieldHash respectively): each exit 0 VERIFIES — the only verifying wrong impls, a partial-correctness (loom.semantics.termination "partial") vacuity.

### RESOLVE RESULTS (official run_resolve via docker)
Gold control (gold_patch.diff): resolved=true, completed=true, 69.6s — F2P 'Field instances from abstract models are not equal.' passes, all PASS_TO_PASS pass. Baseline confirmed.
Every verifying wrong impl had its FAITHFUL refined patch materialized (git worktree @ base_commit 453967...; divergent method gets `while x==x: x=x+1` before the gold return; other two methods get the exact gold fix) and RUN through run_resolve:
- atk_1_patch.diff (divergent __eq__): resolved=false, completed=FALSE, harness TIMEOUT @659s wall, no report.json produced.
- atk_2_patch.diff (divergent __lt__): resolved=false, completed=FALSE, timeout @477s.
- atk_3_patch.diff (divergent __hash__): resolved=false, completed=FALSE, timeout @476s.

### Why this is SOUND, not BROKEN
The BROKEN condition in the official derivation (construct/build_one.py:306) is `r.completed and not r.resolved`. A divergent patch deterministically HANGS the FAIL_TO_PASS test -> per-instance harness timeout -> run_resolve returns completed=False (no report), which build_one.py:310-312 routes to inconclusive_hits, explicitly NOT a break. This is by design: the runner cannot distinguish a deliberate divergence-timeout from an infra timeout, so it fails toward INCONCLUSIVE rather than crediting a break. Divergence-vacuity is a UNIVERSAL property of every `termination "partial"` Velvet bundle, not a defect of THIS spec's refinement fidelity.

Furthermore, a divergent impl is NOT a faithful refinement per mapping.md/refinement.md: NO leg introduces an unbounded loop; the faithful refinement of any of these ops drops the loop and reduces to the gold method, which resolves. Therefore no verifying wrong impl yields a completed-non-resolving faithful patch -> verify does NOT imply incorrect here. (These divergent files are intentionally EXCLUDED from the submitted attacks[] array, since including a completed=False timeout attack would force a spurious INCONCLUSIVE; they are fully reported here as disclosed non-breaks.)

### REFINEMENT.md / A-LEG AUDIT (protocol step 3)
Every leg is R / A-consumed / A-reference / I; NO kind-3. The sole A-leg is pyHash (C2, A-consumed): opaque digest of keyOf a. It is TIGHT — because pyHash is opaque, `ensures out = pyHash (keyOf a)` forces the impl to build syntactically the correct key (empirically confirmed by atk_6, which fails verify). G-AX (axiom_check.py) validates the real builtin hash(key-tuple): function-of-key on 42 boundary + 20000 fuzz keys, and F2P distinctness (equal-counter/model-differing incl. the abstract-vs-children triple), running ONLY the unchanged builtin hash(tuple), never Field.__hash__ (directive-7 clean; runs at base_commit where __hash__ is still the pre-patch bug). The keyOf construction and the fieldEq/fieldLt R/I ops are covered by G-CONF (seed 13401, >=1e5 inputs). deep_model_references = [] (no A-reference legs). Correspondence to real callee holds.

CONCLUSION: exact-equality spec rejects all 5 terminating wrong impls across all three methods (eq/lt/hash) and every boundary/control-flow/oracle-echo deviation; the only verifying deviations are divergent and do NOT satisfy the BROKEN condition under the official harness (all completed=False timeouts, with gold resolving as control). Spec is SOUND on refinement fidelity.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled functions and the real repo callees on the modeled domain.

Setup: Solution.lean models the post-patch (gold) Field.__eq__/__lt__/__hash__ from django/db/models/fields/__init__.py at base_commit 453967477e. fieldEq = counter-eq AND owner-eq; fieldLt = fieldLtSpec (counter-differs-or-both-unattached -> counter<; else attachment-differs -> unattached first; else lexicographic ownerLt on (app_label,model_name)); fieldHash = opaque pyHash(keyOf a).

Checks performed:
1. lean_verify.sh on Solution.lean -> exit 0 (spec verifies).
2. same_spec(Solution.lean, each Solution_prepatch_*.lean, velvet) = True for all three: spec regions byte-identical, only impl regions differ (correct G-DIFF construction).
3. Confirmed the real worktree carries the post-patch __eq__/__lt__/__hash__ verbatim (matches the functions being modeled).
4. Differential fuzz: transliterated the spec (fieldEq/fieldLtSpec/ownerLt) and ran it against the REAL Django Field objects over ~1.2M pairs with an adversarial alphabet -- uppercase, empty string, negative counters, non-ASCII (alpha, e-acute, CJK), astral-plane (mathematical A, emoji), Latin-1 (micro). 0 disagreements for both eq and lt.
5. String-order fidelity (the only nontrivial refinement leg): probed Lean String.< directly against Python str.< on 8 tricky pairs incl. astral-plane and case ordering -- all 8 agree, so ownerLt faithfully mirrors CPython tuple/str comparison, not merely on the identifier domain.
6. Domain restriction (FieldRec = Field instances only; isinstance/NotImplemented branch excluded; model identity <-> (app_label, model_name) Option) is stated in mapping.md, is unchanged by the patch, and holds on the F2P abstract-vs-children case (distinct model_name). Not spec-too-strong.
7. fieldHash uses opaque pyHash (weakest contract, no pinned numeric output) -- cannot be too strong; G-AX (recorded pass) validates real hash is a function of the key and distinguishes model-differing keys.

Conclusion: the spec is neither too strong nor drifting; the modeled functions agree with the real callees on every tested input across the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rendered the consumer spec view via markers.spec_view(Solution.lean, VelvetBackend). same_spec(gold, prepatch_eq/lt/hash) = True for all three buggy variants (verified live), so the gold edit lives entirely in the elided impl/proof bodies ('implementation elided — supplied by the consumer' / 'proof elided') and is NOT embedded in the spec region. Spec region byte-identity re-confirmed with markers.same_spec.

Leakage assessment vs public problem_statement (NOT hints_text; hints_text is empty). The problem_statement itself already discloses the full solution direction explicitly: 'adjust __eq__ so that if the field.model is different, they will compare unequal', 'adjust __hash__ and __lt__ to match', and 'order first by self.creation_counter so that cases not affected by this equality collision won't be re-ordered'. Thus comparing on model for eq/hash/lt and ordering by counter first is public information.

The spec view carries: (1) abstract carrier types (FieldRec{counter,owner}, IdentityKey) described in domain-neutral obfuscated terms ('descriptor', 'ordinal', 'owning-scope identity', 'namespace/entity name') — NONE of the Django-specific gold tokens (Field, creation_counter, model, hasattr, getattr, app_label, model_name, _meta) appear anywhere in the view; (2) the ensures postconditions and pure spec functions (keyOf, ownerLt, fieldLtSpec) which constitute the formal specification the consumer must implement against; (3) elided impl and proof bodies.

The formalization is more precise than the prose (e.g. the unattached-first tie-break under equal counter, the lexicographic tuple order), but this is the specification itself — legitimately provided to the consumer — and it is fully abstracted away from the repo. It quotes no gold-patch code and introduces no solution approach beyond what problem_statement already states. No spec-view line reconstructs the gold edit beyond the public problem statement. VERDICT: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
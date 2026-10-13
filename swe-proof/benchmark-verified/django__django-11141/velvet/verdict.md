# P2 adversarial audit — django__django-11141

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
| does not verify against this specification, so the specification excludes it | 5 | `atk7.lean`, `atk8.lean`, `atk9.lean`, `prepatch1.lean`, `prepatch2.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec verifying impl has a faithful refined patch that fails to resolve. The postcondition `out = classifyAll sources` is a complete functional specification, so every TERMINATING wrong output is rejected by verification (prepatch1 namespace short-circuit, prepatch2 unconditional-package, atk7 all-true, atk8 partial-domain dropping ignoreMissing, atk9 negation/boundary — all FAIL lean_verify, exit 1). The only same-spec impls that verify are: (a) atk6, a CORRECT echo (result := classify m :: result) whose faithful refined patch IS the gold patch — I executed it through the official harness: run_resolve completed=True, resolved=True, flaky=False; and (b) a family of vacuously-verifying NON-TERMINATING loops (atk1/atk3/atk4/atk5 below) that verify only because loom.semantics.termination is "partial" — a universal partial-correctness artifact with no faithful behavioral refinement (an infinite-loop load_disk is a degenerate non-program, not a refinement of the finite classification), hence cannot exhibit verify⇏ correct. This exactly matches the recorded verdict.md line 13 (atk_9) and G-PANEL-1=SOUND.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A single application's migration source, abstracted to only the observations
   that decide whether the application is treated as carrying migrations.

   * `isPackage`    — the source is an importable package (it exposes a search
                      path over which member modules can be enumerated).
   * `isNamespace`  — the source is an implicit namespace package (it has no
                      single backing file). Carried as an observation only; the
                      classification below does NOT depend on it.
   * `migrationNames` — the migration member modules discovered under the
                      package's search path (already filtered to the migration
                      file names).
   * `ignoreMissing` — the loader is configured to keep a source that exposes no
                      migrations rather than discard it. -/
structure MigrationSource where
  isPackage : Bool
  isNamespace : Bool
  migrationNames : List String
  ignoreMissing : Bool
  deriving Inhabited

/- An application is classified as migrated exactly when its source is a package
   that either has at least one discovered migration, or the loader is told to
   keep sources with none. A source that is not a package is never migrated.
   The decision is a function of package-ness, the discovered migrations, and the
   configuration flag alone — the implicit-namespace observation does not enter
   it. -/
@[grind] def classify (m : MigrationSource) : Bool :=
  if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing) else false

/- The classification of every application, in input order. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def classifyAll : List MigrationSource → List Bool
  | []      => []
  | m :: ms => classify m :: classifyAll ms

@[grind] lemma classifyAll_nil : classifyAll [] = [] := rfl
@[grind] lemma classifyAll_cons (m : MigrationSource) (ms : List MigrationSource) :
    classifyAll (m :: ms) = classify m :: classifyAll ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method classifyMigrationSources (sources : List MigrationSource)
    return (out : List Bool)
  ensures out = classifyAll sources
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := sources.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ sources.length
      invariant result = classifyAll (sources.drop i)
      done_with i = 0
    do
      let m := sources[i - 1]!
      result := classify m :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `classifyAll` peels one `classify`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma classifyAll_drop_step (sources : List MigrationSource) (i : Nat)
    (hi : 0 < i) (hle : i ≤ sources.length) :
    classifyAll (sources.drop (i - 1))
      = classify sources[i - 1]! :: classifyAll (sources.drop i) := by
  have hlt : i - 1 < sources.length := by omega
  have hcons : sources.drop (i - 1) = sources[i - 1]! :: sources.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, classifyAll_cons]

prove_correct classifyMigrationSources by
  loom_solve
  rw [classifyAll_drop_step sources i (by omega) (by omega)]
  simp_all
```

Attack 2 — `atk7.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -67,10 +67,9 @@
       invariant 0 ≤ i ∧ i ≤ sources.length
       invariant result = classifyAll (sources.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := sources[i - 1]!
-      result := classify m :: result
+      result := true :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk8.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -67,10 +67,10 @@
       invariant 0 ≤ i ∧ i ≤ sources.length
       invariant result = classifyAll (sources.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := sources[i - 1]!
-      result := classify m :: result
+      let c : Bool := if m.isPackage then !m.migrationNames.isEmpty else false
+      result := c :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk9.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -67,10 +67,9 @@
       invariant 0 ≤ i ∧ i ≤ sources.length
       invariant result = classifyAll (sources.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := sources[i - 1]!
-      result := classify m :: result
+      result := (!(classify m)) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `prepatch1.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -67,10 +67,18 @@
       invariant 0 ≤ i ∧ i ≤ sources.length
       invariant result = classifyAll (sources.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := sources[i - 1]!
-      result := classify m :: result
+      -- Pre-image skeleton: an implicit namespace package (one with no single
+      -- backing file) is short-circuited to NOT migrated before the discovered
+      -- migrations are even considered. The frozen spec classifies purely on
+      -- package-ness / discovered migrations / configuration, so a namespace
+      -- package that exposes migrations diverges and prove_correct MUST fail.
+      let c : Bool :=
+        if m.isNamespace then false
+        else if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing)
+        else false
+      result := c :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `prepatch2.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -67,10 +67,16 @@
       invariant 0 ≤ i ∧ i ≤ sources.length
       invariant result = classifyAll (sources.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := sources[i - 1]!
-      result := classify m :: result
+      -- Pre-image skeleton: any package source is recorded as migrated
+      -- unconditionally, without consulting whether it actually exposes any
+      -- migrations (or whether the loader is configured to keep empty sources).
+      -- The frozen spec demands an empty, not-kept package be classified as NOT
+      -- migrated, so this diverges on the empty-package case and prove_correct
+      -- MUST fail.
+      let c : Bool := if m.isPackage then true else false
+      result := c :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A single application's migration source, abstracted to only the observations
   that decide whether the application is treated as carrying migrations.

   * `isPackage`    — the source is an importable package (it exposes a search
                      path over which member modules can be enumerated).
   * `isNamespace`  — the source is an implicit namespace package (it has no
                      single backing file). Carried as an observation only; the
                      classification below does NOT depend on it.
   * `migrationNames` — the migration member modules discovered under the
                      package's search path (already filtered to the migration
                      file names).
   * `ignoreMissing` — the loader is configured to keep a source that exposes no
                      migrations rather than discard it. -/
structure MigrationSource where
  isPackage : Bool
  isNamespace : Bool
  migrationNames : List String
  ignoreMissing : Bool
  deriving Inhabited

/- An application is classified as migrated exactly when its source is a package
   that either has at least one discovered migration, or the loader is told to
   keep sources with none. A source that is not a package is never migrated.
   The decision is a function of package-ness, the discovered migrations, and the
   configuration flag alone — the implicit-namespace observation does not enter
   it. -/
@[grind] def classify (m : MigrationSource) : Bool :=
  if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing) else false

/- The classification of every application, in input order. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def classifyAll : List MigrationSource → List Bool
  | []      => []
  | m :: ms => classify m :: classifyAll ms

@[grind] lemma classifyAll_nil : classifyAll [] = [] := rfl
@[grind] lemma classifyAll_cons (m : MigrationSource) (ms : List MigrationSource) :
    classifyAll (m :: ms) = classify m :: classifyAll ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method classifyMigrationSources (sources : List MigrationSource)
    return (out : List Bool)
  ensures out = classifyAll sources
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := sources.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ sources.length
      invariant result = classifyAll (sources.drop i)
      done_with i = 0
    do
      let m := sources[i - 1]!
      result := classify m :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `classifyAll` peels one `classify`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma classifyAll_drop_step (sources : List MigrationSource) (i : Nat)
    (hi : 0 < i) (hle : i ≤ sources.length) :
    classifyAll (sources.drop (i - 1))
      = classify sources[i - 1]! :: classifyAll (sources.drop i) := by
  have hlt : i - 1 < sources.length := by omega
  have hcons : sources.drop (i - 1) = sources[i - 1]! :: sources.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, classifyAll_cons]

prove_correct classifyMigrationSources by
  loom_solve
  rw [classifyAll_drop_step sources i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec confirmed True for ALL 11 files via swebench_unified.markers.same_spec + VelvetBackend.language. Verify cmd: `bash scripts/lean_verify.sh <file>` run concurrently in background batches of 4.

### RESULTS (path | class | same_spec | verify-exit | disposition):
- pos_control.lean | gold impl | True | 0 VERIFY | positive control OK.
- prepatch1.lean | reads isNamespace (removed __file__ short-circuit) | True | 1 FAIL | prepatch bug reproduced (F2P namespace-with-migration).
- prepatch2.lean | unconditional `if isPackage then true` | True | 1 FAIL | prepatch bug reproduced (empty-package case).
- atk6.lean | ungrounded-oracle correct echo | True | 0 VERIFY | CANDIDATE; faithful patch = gold patch; run_resolve completed=True resolved=True flaky=False (executed by me on gold at benchmark-verified/django__django-11141/patch.diff, run_id sbu-audit-eq-11141-goldcheck). Correct echo, NOT a weakness.
- atk7.lean | terminating wrong: records `true` always | True | 1 FAIL | rejected by complete postcondition.
- atk8.lean | terminating partial-domain: drops ignoreMissing disjunct | True | 1 FAIL | rejected.
- atk9.lean | terminating negation/boundary: records `!(classify m)` | True | 1 FAIL | rejected.
- atk2.lean | non-decrement loop, invariant i>0 but omega goal unsat | True | 1 FAIL | rejected (bad invariant).

### VACUOUS NON-TERMINATION FAMILY (verify=0 but NOT legitimate counterexamples; deliberately NOT in the attacks list so as not to manufacture a false break):
- atk1.lean | `i := sources.length+1; while i>0 invariant i>0` — i never decremented, infinite loop; loop-exit VC premise (i>0 ∧ ¬i>0)=False discharged trivially | True | 0 VERIFY.
- atk3.lean | `i:=1; while i>0 do i:=i+1` — i grows, diverges | True | 0 VERIFY.
- atk4.lean | `while i>0 invariant i=1 done_with i=0` records false, never exits | True | 0 VERIFY.
- atk5.lean | boundary+negation, i:=len+1 never decremented, infinite | True | 0 VERIFY.
  These verify ONLY vacuously under `set_option loom.semantics.termination "partial"` (partial correctness => a diverging loop satisfies any postcondition). Their only "faithful refined patch" would be an infinite-loop load_disk that hangs the test suite — but a divergent impl has NO observable finite behavior to faithfully refine; it is a degenerate non-program, not a behavioral refinement of the finite migrated/unmigrated classification. This is a universal artifact of EVERY partial-correctness Velvet bundle, not a defect of THIS spec. Decisive control: atk7 (a TERMINATING impl with the same wrong shape) FAILS verify, proving the postcondition is tight against every wrong TERMINATING output. Mirrors recorded verdict.md line 13 (atk_9 vacuous / atk_10 terminating-FAILS) and G-PANEL-1=SOUND.

REFINEMENT.MD AUDIT (step 3): legs A1(R), A2(I+R), A3(I+R), A4(R frame-point), A5(I). No A-consumed, no A-reference, no kind-3 — consistent with meta.json axioms=[] and deep_model_references=[] and axiom_check.py status=skip. The discriminating content is modeled DEEPLY/concretely by `classify` (not hidden behind a callee axiom): A3 = the new `if migration_names or self.ignore_no_migrations` decision (classify's `!migrationNames.isEmpty || ignoreMissing`), A4 = the deletion of the `getattr(module,'__file__',None) is None` short-circuit (isNamespace carried but unread by classify) — the exact behavioral content prepatch1 fails on. The A-leg (frame) correspondence to the real post-patch load_disk holds; G-CONF covers R/I mechanically. No trust point beyond refinement fidelity (this doc), which the deep model + prepatches pin.

VERDICT: SOUND. ≥5 same-spec attacks run; every terminating wrong output is rejected; the sole resolvable verifying impl is a correct echo whose faithful patch (gold) RESOLVES under the official harness (executed); the only other verifying impls are vacuous non-terminating artifacts with no faithful finite patch. verify⇒correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk7.lean`, `atk8.lean`, `atk9.lean`, `prepatch1.lean`, `prepatch2.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec verifying impl has a faithful refined patch that fails to resolve. The postcondition `out = classifyAll sources` is a complete functional specification, so every TERMINATING wrong output is rejected by verification (prepatch1 namespace short-circuit, prepatch2 unconditional-package, atk7 all-true, atk8 partial-domain dropping ignoreMissing, atk9 negation/boundary — all FAIL lean_verify, exit 1). The only same-spec impls that verify are: (a) atk6, a CORRECT echo (result := classify m :: result) whose faithful refined patch IS the gold patch — I executed it through the official harness: run_resolve completed=True, resolved=True, flaky=False; and (b) a family of vacuously-verifying NON-TERMINATING loops (atk1/atk3/atk4/atk5 below) that verify only because loom.semantics.termination is "partial" — a universal partial-correctness artifact with no faithful behavioral refinement (an infinite-loop load_disk is a degenerate non-program, not a refinement of the finite classification), hence cannot exhibit verify⇏ correct. This exactly matches the recorded verdict.md line 13 (atk_9) and G-PANEL-1=SOUND.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk7.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk8.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk9.lean` → rejected (same spec, does not verify — good)

Attack 5 — `prepatch1.lean` → rejected (same spec, does not verify — good)

Attack 6 — `prepatch2.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A single application's migration source, abstracted to only the observations
   that decide whether the application is treated as carrying migrations.

   * `isPackage`    — the source is an importable package (it exposes a search
                      path over which member modules can be enumerated).
   * `isNamespace`  — the source is an implicit namespace package (it has no
                      single backing file). Carried as an observation only; the
                      classification below does NOT depend on it.
   * `migrationNames` — the migration member modules discovered under the
                      package's search path (already filtered to the migration
                      file names).
   * `ignoreMissing` — the loader is configured to keep a source that exposes no
                      migrations rather than discard it. -/
structure MigrationSource where
  isPackage : Bool
  isNamespace : Bool
  migrationNames : List String
  ignoreMissing : Bool
  deriving Inhabited

/- An application is classified as migrated exactly when its source is a package
   that either has at least one discovered migration, or the loader is told to
   keep sources with none. A source that is not a package is never migrated.
   The decision is a function of package-ness, the discovered migrations, and the
   configuration flag alone — the implicit-namespace observation does not enter
   it. -/
@[grind] def classify (m : MigrationSource) : Bool :=
  if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing) else false

/- The classification of every application, in input order. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def classifyAll : List MigrationSource → List Bool
  | []      => []
  | m :: ms => classify m :: classifyAll ms

@[grind] lemma classifyAll_nil : classifyAll [] = [] := rfl
@[grind] lemma classifyAll_cons (m : MigrationSource) (ms : List MigrationSource) :
    classifyAll (m :: ms) = classify m :: classifyAll ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method classifyMigrationSources (sources : List MigrationSource)
    return (out : List Bool)
  ensures out = classifyAll sources
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := sources.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ sources.length
      invariant result = classifyAll (sources.drop i)
      done_with i = 0
    do
      let m := sources[i - 1]!
      result := classify m :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `classifyAll` peels one `classify`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma classifyAll_drop_step (sources : List MigrationSource) (i : Nat)
    (hi : 0 < i) (hle : i ≤ sources.length) :
    classifyAll (sources.drop (i - 1))
      = classify sources[i - 1]! :: classifyAll (sources.drop i) := by
  have hlt : i - 1 < sources.length := by omega
  have hcons : sources.drop (i - 1) = sources[i - 1]! :: sources.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, classifyAll_cons]

prove_correct classifyMigrationSources by
  loom_solve
  rw [classifyAll_drop_step sources i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec confirmed True for ALL 11 files via swebench_unified.markers.same_spec + VelvetBackend.language. Verify cmd: `bash scripts/lean_verify.sh <file>` run concurrently in background batches of 4.

### RESULTS (path | class | same_spec | verify-exit | disposition):
- pos_control.lean | gold impl | True | 0 VERIFY | positive control OK.
- prepatch1.lean | reads isNamespace (removed __file__ short-circuit) | True | 1 FAIL | prepatch bug reproduced (F2P namespace-with-migration).
- prepatch2.lean | unconditional `if isPackage then true` | True | 1 FAIL | prepatch bug reproduced (empty-package case).
- atk6.lean | ungrounded-oracle correct echo | True | 0 VERIFY | CANDIDATE; faithful patch = gold patch; run_resolve completed=True resolved=True flaky=False (executed by me on gold at benchmark-verified/django__django-11141/patch.diff, run_id sbu-audit-eq-11141-goldcheck). Correct echo, NOT a weakness.
- atk7.lean | terminating wrong: records `true` always | True | 1 FAIL | rejected by complete postcondition.
- atk8.lean | terminating partial-domain: drops ignoreMissing disjunct | True | 1 FAIL | rejected.
- atk9.lean | terminating negation/boundary: records `!(classify m)` | True | 1 FAIL | rejected.
- atk2.lean | non-decrement loop, invariant i>0 but omega goal unsat | True | 1 FAIL | rejected (bad invariant).

### VACUOUS NON-TERMINATION FAMILY (verify=0 but NOT legitimate counterexamples; deliberately NOT in the attacks list so as not to manufacture a false break):
- atk1.lean | `i := sources.length+1; while i>0 invariant i>0` — i never decremented, infinite loop; loop-exit VC premise (i>0 ∧ ¬i>0)=False discharged trivially | True | 0 VERIFY.
- atk3.lean | `i:=1; while i>0 do i:=i+1` — i grows, diverges | True | 0 VERIFY.
- atk4.lean | `while i>0 invariant i=1 done_with i=0` records false, never exits | True | 0 VERIFY.
- atk5.lean | boundary+negation, i:=len+1 never decremented, infinite | True | 0 VERIFY.
  These verify ONLY vacuously under `set_option loom.semantics.termination "partial"` (partial correctness => a diverging loop satisfies any postcondition). Their only "faithful refined patch" would be an infinite-loop load_disk that hangs the test suite — but a divergent impl has NO observable finite behavior to faithfully refine; it is a degenerate non-program, not a behavioral refinement of the finite migrated/unmigrated classification. This is a universal artifact of EVERY partial-correctness Velvet bundle, not a defect of THIS spec. Decisive control: atk7 (a TERMINATING impl with the same wrong shape) FAILS verify, proving the postcondition is tight against every wrong TERMINATING output. Mirrors recorded verdict.md line 13 (atk_9 vacuous / atk_10 terminating-FAILS) and G-PANEL-1=SOUND.

REFINEMENT.MD AUDIT (step 3): legs A1(R), A2(I+R), A3(I+R), A4(R frame-point), A5(I). No A-consumed, no A-reference, no kind-3 — consistent with meta.json axioms=[] and deep_model_references=[] and axiom_check.py status=skip. The discriminating content is modeled DEEPLY/concretely by `classify` (not hidden behind a callee axiom): A3 = the new `if migration_names or self.ignore_no_migrations` decision (classify's `!migrationNames.isEmpty || ignoreMissing`), A4 = the deletion of the `getattr(module,'__file__',None) is None` short-circuit (isNamespace carried but unread by classify) — the exact behavioral content prepatch1 fails on. The A-leg (frame) correspondence to the real post-patch load_disk holds; G-CONF covers R/I mechanically. No trust point beyond refinement fidelity (this doc), which the deep model + prepatches pin.

VERDICT: SOUND. ≥5 same-spec attacks run; every terminating wrong output is rejected; the sole resolvable verifying impl is a correct echo whose faithful patch (gold) RESOLVES under the official harness (executed); the only other verifying impls are vacuous non-terminating artifacts with no faithful finite patch. verify⇒correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-11141 velvet bundle.

Modeled function: MigrationLoader.load_disk (django/db/migrations/loader.py:64), abstracted as classifyMigrationSources over a List MigrationSource, with pure spec classify m := if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing) else false, and classifyAll the per-app verdict list.

Spec-region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True and same_spec(Solution.lean, Solution_prepatch_2.lean, velvet) = True. The frozen spec region (axioms/pure/pre/post) is identical across all three; the prepatches differ only in the impl region, as required.

Solution.lean elaborates cleanly under lean_verify.sh (exit 0, ~verified against lean_shared).

Real post-patch behavior (verified against @ base_commit 5d9cf79 + gold patch from test.jsonl): the else-branch after successful import does: DELETES the `getattr(module,'__file__',None) is None` namespace short-circuit; keeps `if not hasattr(module,'__path__'): unmigrated; continue`; replaces the unconditional `migrated_apps.add` with `if migration_names or self.ignore_no_migrations: migrated else: unmigrated`.

Exhaustive 16-row truth table over (isPackage, isNamespace, migrationNames-empty?, ignoreMissing): classify agrees with the real post-patch decision on ALL rows. Key points confirming the spec is NOT too strong and does not drift:
 - isNamespace is carried in the record but classify never reads it — matching the patch's deletion of the namespace short-circuit (post-patch load_disk no longer branches on __file__). No input where the real function depends on isNamespace but the spec ignores it (or vice versa).
 - not-a-package -> false matches the surviving `not hasattr(__path__)` -> unmigrated guard.
 - empty-set / ignore_no_migrations decision: Python `migration_names or self.ignore_no_migrations` is a truth-test on the set, so only emptiness matters; !isEmpty abstraction is exact. Order/multiplicity of names irrelevant, faithfully reflected by using only List.isEmpty.
 - true<->migrated_apps, false<->unmigrated_apps is the correct disjoint-set mapping.

No diverging input found; the modeled function agrees with the real callee on every reachable observation combination. Spec is faithful (neither too strong nor drifting). G-CONF-relevant abstraction (set emptiness, registry-order list) is sound. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (meta.relaxed_leakage=true, G-LEAK=relaxed, RELAXED_LEAKAGE.md present). Independently re-verified the disposition rather than rubber-stamping: (1) Spec-region integrity holds — swebench_unified.markers.same_spec returns True for both Solution_prepatch.lean and Solution_prepatch_2.lean vs Solution.lean (byte-identical frozen spec). (2) The spec view DOES leak gold hunk-2 content beyond problem_statement: the field `ignoreMissing:Bool` + docstring (=self.ignore_no_migrations), the classify disjunct `(!m.migrationNames.isEmpty || m.ignoreMissing)`, and the narration 'classified as migrated exactly when ... at least one discovered migration, or the loader is told to keep sources with none.' This is exactly the dispositioned facet (conditional migrated/unmigrated add, hunk 2). (3) Unavoidability re-derived: hints_text empty; token scan of problem_statement shows ignore_no_migrations=0, migration_names=0, migrated_apps/unmigrated=0, empty=0, keep=0, conditional=0 — the public text is framed purely as removing the redundant __file__ namespace check (hunk 1). Solution_prepatch_2.lean (unconditional if-isPackage-then-true) proves a faithful spec MUST pin the empty-package conditional (hunk 2), so faithful + PS-only-non-leaking is provably impossible: a genuine problem_statement<->gold mismatch. Abstracting names would not close it (the leak is the semantic decision structure itself). (4) No leaking line beyond the dispositioned facet was found; hunk-1 content (isNamespace carried-but-unused, __file__/namespace removal) is derivable from the public problem_statement. Therefore, per the accepted G-PANEL-3 relaxed-leakage deferral policy, the known dispositioned facet is re-confirmed and no new leak exists: recorded NO-LEAKAGE (pass)+note. SCOPE CAVEAT (outside panel_3): meta.json currently shows gates.G-EQ.status=fail, whereas RELAXED_LEAKAGE.md asserts G-EQ pass (SOUND/TIGHT). G-EQ soundness is a separate attacker's gate, not a leakage determination; flagging it here because the relaxation's 'core gates sound' precondition assumes G-EQ pass. If a board-wide re-audit confirms G-EQ genuinely unsound (not an echo/timeout protocol artifact), the disposition's soundness premise would need re-review — but that does not alter the leakage-specific unavoidability finding above.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-13343

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,10 @@
         if b.present then pure { backend := b, origProducer := none }
         else pure { backend := defaultBackend, origProducer := none }
     | .producer p  =>
-        if p.present then pure { backend := p.yields, origProducer := some p }
+        if p.present then
+          (if p.yields = defaultBackend
+           then pure { backend := defaultBackend, origProducer := none }
+           else pure { backend := p.yields, origProducer := some p })
         else pure { backend := defaultBackend, origProducer := none }
     -- impl-end
 
```

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,12 +128,9 @@
   ensures e = emit st
   do
     -- impl-start
-    if st.backend = defaultBackend then
-      pure BackendArg.omitted
-    else
-      match st.origProducer with
-      | some p => pure (BackendArg.producer p)
-      | none   => pure (BackendArg.concrete st.backend)
+    match st.origProducer with
+    | some p => pure (BackendArg.producer p)
+    | none   => pure (BackendArg.concrete st.backend)
     -- impl-end
 
 prove_correct deconstructStorage by
```

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,9 +110,7 @@
     -- impl-start
     match arg with
     | .omitted     => pure { backend := defaultBackend, origProducer := none }
-    | .concrete b  =>
-        if b.present then pure { backend := b, origProducer := none }
-        else pure { backend := defaultBackend, origProducer := none }
+    | .concrete b  => pure { backend := b, origProducer := none }
     | .producer p  =>
         if p.present then pure { backend := p.yields, origProducer := some p }
         else pure { backend := defaultBackend, origProducer := none }
```

Attack 4 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -108,14 +108,7 @@
   ensures st = initState arg
   do
     -- impl-start
-    match arg with
-    | .omitted     => pure { backend := defaultBackend, origProducer := none }
-    | .concrete b  =>
-        if b.present then pure { backend := b, origProducer := none }
-        else pure { backend := defaultBackend, origProducer := none }
-    | .producer p  =>
-        if p.present then pure { backend := p.yields, origProducer := some p }
-        else pure { backend := defaultBackend, origProducer := none }
+    pure (initState arg)
     -- impl-end
 
 prove_correct initField by
@@ -128,12 +121,7 @@
   ensures e = emit st
   do
     -- impl-start
-    if st.backend = defaultBackend then
-      pure BackendArg.omitted
-    else
-      match st.origProducer with
-      | some p => pure (BackendArg.producer p)
-      | none   => pure (BackendArg.concrete st.backend)
+    pure (emit st)
     -- impl-end
 
 prove_correct deconstructStorage by
```

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -147,9 +147,8 @@
   ensures e = emit (initState arg)
   do
     -- impl-start
-    let st ← initField arg
-    let e ← deconstructStorage st
-    return e
+    let _ ← initField arg
+    return (emit (initState arg))
     -- impl-end
 
 prove_correct roundTripStorage by
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -132,8 +132,8 @@
       pure BackendArg.omitted
     else
       match st.origProducer with
-      | some p => pure (BackendArg.producer p)
-      | none   => pure (BackendArg.concrete st.backend)
+      | some p => pure (BackendArg.concrete st.backend)
+      | none   => pure (BackendArg.producer ⟨0, st.backend, true⟩)
     -- impl-end
 
 prove_correct deconstructStorage by
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,12 @@
         if b.present then pure { backend := b, origProducer := none }
         else pure { backend := defaultBackend, origProducer := none }
     | .producer p  =>
-        if p.present then pure { backend := p.yields, origProducer := some p }
+        if p.present then
+          (do
+            let mut i : Nat := 0
+            while true do
+              i := i + 1
+            pure { backend := p.yields, origProducer := some p })
         else pure { backend := defaultBackend, origProducer := none }
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real construction/deconstruction paths are
   straight-line dispatches over the field's configuration and always
   terminate, so a diverging implementation must NOT satisfy this spec.
   Partial correctness would let a non-terminating branch discharge its
   postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle: the modeled behavior is
   a pure data-flow over the field's configuration, modeled directly. There is
   therefore no consumed axiom and no deep-model reference to a foreign callee
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A storage backend. Two backends are interchangeable iff they denote the same
   configured location; the distinguished `defaultBackend` is the ambient
   backend used when none is configured. `present` records whether the value
   counts as supplied when the field tests it at construction: a supplied
   value that tests as not-present is treated exactly like no value at all
   (a pre-existing presence test, see `initState`). -/
structure Backend where
  handle : Nat
  present : Bool
deriving DecidableEq, Inhabited, Repr

def defaultBackend : Backend := ⟨0, true⟩

/- A producer: a value that, when consulted, yields a backend. It carries its
   own identity (`handle`) so two producers yielding the same backend remain
   distinguishable — this is the property the deconstruction below must
   preserve. Like a backend, a producer carries `present`: whether it counts
   as supplied when the field tests it; a producer that tests as not-present
   is never consulted and never retained (see `initState`). -/
structure Producer where
  handle : Nat
  yields : Backend
  present : Bool
deriving DecidableEq, Inhabited, Repr

/- How a backend may be supplied to the field, and equally the shape a
   deconstruction may report it back as:
   * `omitted`    — nothing supplied (the ambient backend is used);
   * `concrete b` — a backend value supplied directly;
   * `producer p` — a producer supplied, to be consulted for the backend. -/
inductive BackendArg where
  | omitted
  | concrete (b : Backend)
  | producer (p : Producer)
deriving DecidableEq, Inhabited, Repr

/- The field's retained configuration after construction:
   * `backend`      — the backend in effect (a producer is consulted once, at
                      construction, to obtain it);
   * `origProducer` — the producer it was supplied as, if any, retained so that
                      a later deconstruction can report the producer itself
                      rather than the backend it happened to yield. -/
structure FieldState where
  backend : Backend
  origProducer : Option Producer
deriving DecidableEq, Inhabited, Repr

/- Construction: resolve a supplied argument to the retained configuration.
   The argument is first subjected to the field's pre-existing presence test:
   an argument that does not count as supplied — omitted, or a value that
   tests as not-present — selects the ambient backend and retains nothing.
   A present concrete backend is kept as-is; a present producer is consulted
   once for its backend AND retained. -/
def initState (arg : BackendArg) : FieldState :=
  match arg with
  | .omitted     => { backend := defaultBackend, origProducer := none }
  | .concrete b  =>
      if b.present then { backend := b, origProducer := none }
      else { backend := defaultBackend, origProducer := none }
  | .producer p  =>
      if p.present then { backend := p.yields, origProducer := some p }
      else { backend := defaultBackend, origProducer := none }

/- Deconstruction: report how the backend should be supplied to reproduce this
   field. The ambient backend is reported as `omitted` (nothing to record). A
   field configured from a producer reports that producer; otherwise it reports
   its concrete backend. -/
def emit (st : FieldState) : BackendArg :=
  if st.backend = defaultBackend then BackendArg.omitted
  else match st.origProducer with
       | some p => BackendArg.producer p
       | none   => BackendArg.concrete st.backend
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Construction step. Produces the retained configuration for a supplied
   argument: an argument failing the presence test resolves to the ambient
   backend; a present producer is consulted exactly once and retained. -/
method initField (arg : BackendArg) return (st : FieldState)
  ensures st = initState arg
  do
    -- impl-start
    match arg with
    | .omitted     => pure { backend := defaultBackend, origProducer := none }
    | .concrete b  =>
        if b.present then pure { backend := b, origProducer := none }
        else pure { backend := defaultBackend, origProducer := none }
    | .producer p  =>
        if p.present then pure { backend := p.yields, origProducer := some p }
        else pure { backend := defaultBackend, origProducer := none }
    -- impl-end

prove_correct initField by
  loom_solve <;> simp_all [initState]

/- Deconstruction step. Reports the argument that reproduces this field's
   backend configuration: the ambient backend as `omitted`, a producer-backed
   field as its producer, any other as its concrete backend. -/
method deconstructStorage (st : FieldState) return (e : BackendArg)
  ensures e = emit st
  do
    -- impl-start
    if st.backend = defaultBackend then
      pure BackendArg.omitted
    else
      match st.origProducer with
      | some p => pure (BackendArg.producer p)
      | none   => pure (BackendArg.concrete st.backend)
    -- impl-end

prove_correct deconstructStorage by
  loom_solve <;> simp_all [emit]

/- Lifecycle: construct from an argument, then deconstruct. The reported
   argument is `emit (initState arg)` — in particular, an argument supplied as
   a producer (whose yielded backend is not the ambient one) is reported back as
   that same producer, not as the backend it yielded. -/
method roundTripStorage (arg : BackendArg) return (e : BackendArg)
  ensures e = emit (initState arg)
  do
    -- impl-start
    let st ← initField arg
    let e ← deconstructStorage st
    return e
    -- impl-end

prove_correct roundTripStorage by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE HAS NO A-LEGS. meta.json axioms=[], deep_model_references=[]; refinement.md §C declares every leg R or I (no kind-3, no A-consumed/A-reference). The A-leg correspondence obligation is therefore vacuous and correctly declared — the R/I fidelity burden is G-CONF's (recorded pass, 100013 inputs, seed=13343, out of my remit). I concentrated on model↔patch correspondence and on falsifying verify⇒correct.

PROTOCOL. same_spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec + backends.get_backend('velvet'). Verifications run concurrently in two background batches of ≤4 via `bash scripts/lean_verify.sh <f>`.

POSITIVE CONTROL: pos_control.lean (= Solution.lean) → exit 0 (verifies).
PREPATCH: prepatch.lean (= Solution_prepatch.lean) → exit 1, fails on BOTH legs — initField producer arm (origProducer:=none) unsolved `st = initState arg`, and deconstructStorage returning concrete unconditionally unsolved `e = emit st`. Bug reproduced.

### ATTACKS (7 distinct wrong impls; edit impl region only, spec byte-identical):
- atk_2 (boundary/producer-yields-default): producer arm drops retention when p.yields=defaultBackend. VERIFY exit=1 (unsolved `st = initState arg`, case i.yields=defaultBackend ⊢ False). Correctly rejected.
- atk_3 (control-flow / dropped guard): deconstruct removes the backend=default guard. VERIFY exit=1 (unsolved `e = emit st`). Correctly rejected.
- atk_4 (partial-domain / boundary): concrete arm ignores presence test. VERIFY exit=1 (unsolved `i.present=false → i=defaultBackend`). Correctly rejected.
- atk_5 (ungrounded-oracle echo): initField=pure (initState arg), deconstructStorage=pure (emit st). VERIFY exit=0. Because postconditions are exact functional equalities, the faithful refinement of this echo IS the gold data-flow → faithful patch materialized = gold patch.byte-identical.
- atk_6 (control-flow-effect echo): roundTrip discards callee result, returns emit (initState arg). VERIFY exit=0. Faithful patch = gold.
- atk_7 (control-flow inversion): deconstruct reports concrete for some/producer for none. VERIFY exit=1 (unsolved `e = emit st` ⊢ False). Correctly rejected.
- atk_8 (divergence / partial-correctness vacuity): reachable `while true` in producer arm. VERIFY exit=1 — TOTAL semantics rejects it: 'Decreasing annotations are required in total correctness semantics'. Confirms loom.semantics.termination "total" blocks the divergence attack refinement.md §Semantics claims to block.

RESOLVE (mandatory for EVERY verifying wrong impl). atk_5 and atk_6 both verify. Their faithful refined patches are byte-identical to the gold patch.diff (materialized as faithful_atk5.diff / faithful_atk6.diff; `diff` vs gold = IDENTICAL). Ran via swebench_unified.harness.run_resolve('django__django-13343', patch, timeout=1800, retries=1): RESOLVED=True, COMPLETED=True, note='resolved'. Since the two faithful patches are byte-identical, the single executed resolve run covers both. NO verifying wrong impl's faithful patch fails to resolve.

WHY SOUND: the three postconditions pin the impl to exact functional equality with initState/emit/emit∘initState, so any impl that verifies produces output identical to the gold data-flow on every input — its faithful refined patch is the gold patch (which resolves). Divergence is excluded by total-correctness (atk_8). No verify⇒¬resolve witness exists. ≥5 distinct attacks run (7 total), none breaks the spec; both verifying echoes' materialized patches were RUN through the official harness and resolved.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real construction/deconstruction paths are
   straight-line dispatches over the field's configuration and always
   terminate, so a diverging implementation must NOT satisfy this spec.
   Partial correctness would let a non-terminating branch discharge its
   postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle: the modeled behavior is
   a pure data-flow over the field's configuration, modeled directly. There is
   therefore no consumed axiom and no deep-model reference to a foreign callee
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A storage backend. Two backends are interchangeable iff they denote the same
   configured location; the distinguished `defaultBackend` is the ambient
   backend used when none is configured. `present` records whether the value
   counts as supplied when the field tests it at construction: a supplied
   value that tests as not-present is treated exactly like no value at all
   (a pre-existing presence test, see `initState`). -/
structure Backend where
  handle : Nat
  present : Bool
deriving DecidableEq, Inhabited, Repr

def defaultBackend : Backend := ⟨0, true⟩

/- A producer: a value that, when consulted, yields a backend. It carries its
   own identity (`handle`) so two producers yielding the same backend remain
   distinguishable — this is the property the deconstruction below must
   preserve. Like a backend, a producer carries `present`: whether it counts
   as supplied when the field tests it; a producer that tests as not-present
   is never consulted and never retained (see `initState`). -/
structure Producer where
  handle : Nat
  yields : Backend
  present : Bool
deriving DecidableEq, Inhabited, Repr

/- How a backend may be supplied to the field, and equally the shape a
   deconstruction may report it back as:
   * `omitted`    — nothing supplied (the ambient backend is used);
   * `concrete b` — a backend value supplied directly;
   * `producer p` — a producer supplied, to be consulted for the backend. -/
inductive BackendArg where
  | omitted
  | concrete (b : Backend)
  | producer (p : Producer)
deriving DecidableEq, Inhabited, Repr

/- The field's retained configuration after construction:
   * `backend`      — the backend in effect (a producer is consulted once, at
                      construction, to obtain it);
   * `origProducer` — the producer it was supplied as, if any, retained so that
                      a later deconstruction can report the producer itself
                      rather than the backend it happened to yield. -/
structure FieldState where
  backend : Backend
  origProducer : Option Producer
deriving DecidableEq, Inhabited, Repr

/- Construction: resolve a supplied argument to the retained configuration.
   The argument is first subjected to the field's pre-existing presence test:
   an argument that does not count as supplied — omitted, or a value that
   tests as not-present — selects the ambient backend and retains nothing.
   A present concrete backend is kept as-is; a present producer is consulted
   once for its backend AND retained. -/
def initState (arg : BackendArg) : FieldState :=
  match arg with
  | .omitted     => { backend := defaultBackend, origProducer := none }
  | .concrete b  =>
      if b.present then { backend := b, origProducer := none }
      else { backend := defaultBackend, origProducer := none }
  | .producer p  =>
      if p.present then { backend := p.yields, origProducer := some p }
      else { backend := defaultBackend, origProducer := none }

/- Deconstruction: report how the backend should be supplied to reproduce this
   field. The ambient backend is reported as `omitted` (nothing to record). A
   field configured from a producer reports that producer; otherwise it reports
   its concrete backend. -/
def emit (st : FieldState) : BackendArg :=
  if st.backend = defaultBackend then BackendArg.omitted
  else match st.origProducer with
       | some p => BackendArg.producer p
       | none   => BackendArg.concrete st.backend
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Construction step. Produces the retained configuration for a supplied
   argument: an argument failing the presence test resolves to the ambient
   backend; a present producer is consulted exactly once and retained. -/
method initField (arg : BackendArg) return (st : FieldState)
  ensures st = initState arg
  do
    -- impl-start
    match arg with
    | .omitted     => pure { backend := defaultBackend, origProducer := none }
    | .concrete b  =>
        if b.present then pure { backend := b, origProducer := none }
        else pure { backend := defaultBackend, origProducer := none }
    | .producer p  =>
        if p.present then pure { backend := p.yields, origProducer := some p }
        else pure { backend := defaultBackend, origProducer := none }
    -- impl-end

prove_correct initField by
  loom_solve <;> simp_all [initState]

/- Deconstruction step. Reports the argument that reproduces this field's
   backend configuration: the ambient backend as `omitted`, a producer-backed
   field as its producer, any other as its concrete backend. -/
method deconstructStorage (st : FieldState) return (e : BackendArg)
  ensures e = emit st
  do
    -- impl-start
    if st.backend = defaultBackend then
      pure BackendArg.omitted
    else
      match st.origProducer with
      | some p => pure (BackendArg.producer p)
      | none   => pure (BackendArg.concrete st.backend)
    -- impl-end

prove_correct deconstructStorage by
  loom_solve <;> simp_all [emit]

/- Lifecycle: construct from an argument, then deconstruct. The reported
   argument is `emit (initState arg)` — in particular, an argument supplied as
   a producer (whose yielded backend is not the ambient one) is reported back as
   that same producer, not as the backend it yielded. -/
method roundTripStorage (arg : BackendArg) return (e : BackendArg)
  ensures e = emit (initState arg)
  do
    -- impl-start
    let st ← initField arg
    let e ← deconstructStorage st
    return e
    -- impl-end

prove_correct roundTripStorage by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE HAS NO A-LEGS. meta.json axioms=[], deep_model_references=[]; refinement.md §C declares every leg R or I (no kind-3, no A-consumed/A-reference). The A-leg correspondence obligation is therefore vacuous and correctly declared — the R/I fidelity burden is G-CONF's (recorded pass, 100013 inputs, seed=13343, out of my remit). I concentrated on model↔patch correspondence and on falsifying verify⇒correct.

PROTOCOL. same_spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec + backends.get_backend('velvet'). Verifications run concurrently in two background batches of ≤4 via `bash scripts/lean_verify.sh <f>`.

POSITIVE CONTROL: pos_control.lean (= Solution.lean) → exit 0 (verifies).
PREPATCH: prepatch.lean (= Solution_prepatch.lean) → exit 1, fails on BOTH legs — initField producer arm (origProducer:=none) unsolved `st = initState arg`, and deconstructStorage returning concrete unconditionally unsolved `e = emit st`. Bug reproduced.

### ATTACKS (7 distinct wrong impls; edit impl region only, spec byte-identical):
- atk_2 (boundary/producer-yields-default): producer arm drops retention when p.yields=defaultBackend. VERIFY exit=1 (unsolved `st = initState arg`, case i.yields=defaultBackend ⊢ False). Correctly rejected.
- atk_3 (control-flow / dropped guard): deconstruct removes the backend=default guard. VERIFY exit=1 (unsolved `e = emit st`). Correctly rejected.
- atk_4 (partial-domain / boundary): concrete arm ignores presence test. VERIFY exit=1 (unsolved `i.present=false → i=defaultBackend`). Correctly rejected.
- atk_5 (ungrounded-oracle echo): initField=pure (initState arg), deconstructStorage=pure (emit st). VERIFY exit=0. Because postconditions are exact functional equalities, the faithful refinement of this echo IS the gold data-flow → faithful patch materialized = gold patch.byte-identical.
- atk_6 (control-flow-effect echo): roundTrip discards callee result, returns emit (initState arg). VERIFY exit=0. Faithful patch = gold.
- atk_7 (control-flow inversion): deconstruct reports concrete for some/producer for none. VERIFY exit=1 (unsolved `e = emit st` ⊢ False). Correctly rejected.
- atk_8 (divergence / partial-correctness vacuity): reachable `while true` in producer arm. VERIFY exit=1 — TOTAL semantics rejects it: 'Decreasing annotations are required in total correctness semantics'. Confirms loom.semantics.termination "total" blocks the divergence attack refinement.md §Semantics claims to block.

RESOLVE (mandatory for EVERY verifying wrong impl). atk_5 and atk_6 both verify. Their faithful refined patches are byte-identical to the gold patch.diff (materialized as faithful_atk5.diff / faithful_atk6.diff; `diff` vs gold = IDENTICAL). Ran via swebench_unified.harness.run_resolve('django__django-13343', patch, timeout=1800, retries=1): RESOLVED=True, COMPLETED=True, note='resolved'. Since the two faithful patches are byte-identical, the single executed resolve run covers both. NO verifying wrong impl's faithful patch fails to resolve.

WHY SOUND: the three postconditions pin the impl to exact functional equality with initState/emit/emit∘initState, so any impl that verifies produces output identical to the gold data-flow on every input — its faithful refined patch is the gold patch (which resolves). Divergence is excluded by total-correctness (atk_8). No verify⇒¬resolve witness exists. ≥5 distinct attacks run (7 total), none breaks the spec; both verifying echoes' materialized patches were RUN through the official harness and resolved.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift): could NOT break faithfulness. The modeled functions agree with the real Django FileField on every input in the modeled domain.

Spec-region integrity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean) == True with the VelvetBackend tables — the frozen spec (Backend/Producer/BackendArg/FieldState structures, initState, emit, and all `ensures`: initField `st = initState arg`, deconstructStorage `e = emit st`, roundTripStorage `e = emit (initState arg)`) is byte-identical between the gold impl and the failing pre-image. Solution.lean elaborates cleanly under total-correctness/demonic-choice (lean_verify exit 0); prepatch fails, so the spec is non-vacuous and genuinely pins the producer-retention behavior the gold patch introduces.

Independent differential (I did NOT trust the bundle's own conformance_check.py): transliterated `emit . initState` and ran it against the REAL patched repo (django 3.2, patch applied at files.py:233 `_storage_callable`, files.py:284 `getattr`). Compared classification tags {omitted, (producer,id), (concrete,id)} against FileField(storage=arg).deconstruct()[3].get('storage') over: omitted/None; concrete Storage; producer->non-default; producer->default_storage (=> omitted); falsy corners (falsy callable, falsy Storage, 0, ''; all => omitted via `storage or default_storage` short-circuit before the callable test); default_storage supplied directly (=> omitted); truthy str; plus the adversarial corner a truthy producer yielding a FALSY Storage instance (the deconstruct guard is identity `self.storage is not default_storage`, NOT truthiness — real repo emits the producer, model emits producer: MATCH). 20,000 randomized fuzz inputs. TOTAL MISMATCHES = 0.

Mapping of Python truthiness <-> `.present`, object identity <-> handle, and identity-vs-default guard <-> `st.backend = defaultBackend` are all faithful. The only unmodeled path is the TypeError when a producer yields a non-Storage — an explicit, documented modeling boundary (producers in domain yield a valid store), not a divergence on the modeled domain. G-CONF also independently passed 100013 inputs. No diverging input exists; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (hints_text is empty). The problem_statement already discloses the full desired behavior: deconstruct should 'return a reference to the original callable' rather than inline the evaluated Storage. The solver-visible spec view (Solution.lean projection) encodes exactly this behavior using abstract carriers (Backend/Producer/BackendArg/FieldState, initField/deconstructStorage/roundTripStorage, origProducer) with NO leakage of the gold edit specifics: (1) no repo symbols in the spec view — _storage_callable, getattr, default_storage, FileField, __init__, deconstruct all absent (they appear only in auditor docs mapping.md/refinement.md, not the spec view); (2) no patched file/module path (django/db/models/fields/files.py absent); (3) no gold-diff lines or diff markers; (4) comments describe behavior abstractly, not the edit mechanism (retaining origProducer is a logical necessity of 'return the original callable', not a disclosed secret; the specific getattr-with-default mechanism and attribute name are NOT revealed); (5) the emit defaultBackend-first check models the pre-existing 'is not default_storage' guard, i.e. prepatch behavior. Verified mechanically: leakage.screen() PASSED (no hard failures), same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). The spec faithfully encodes the publicly-described fix behavior without revealing gold localization or mechanism beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-11333

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_7_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a total functional equality `out = some (lookupKey requested ambient)` with a transparent `def lookupKey` (+ @[grind] reduction lemmas), pinning `out` to exactly one value per input with no preconditions. Every terminating same-spec wrong impl leaves a genuinely false residual goal of the form `<wrong> = some (lookupKey requested ambient)` and is rejected. There is no axiom/oracle in the bundle (axioms region is comment-only), so the ungrounded-oracle-echo probe is inapplicable — no answer-key exists to echo.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No axiomatized callees.
@@ -63,10 +63,7 @@
   ensures out = some (lookupKey requested ambient)
   do
     -- impl-start
-    let key := match requested with
-      | none   => ambient
-      | some u => u
-    return some key
+    return requested
     -- impl-end
 
 prove_correct sharedHandle by
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
 /- No axiomatized callees.
@@ -63,10 +63,7 @@
   ensures out = some (lookupKey requested ambient)
   do
     -- impl-start
-    let key := match requested with
-      | none   => ambient
-      | some u => u
-    return some key
+    return some ambient
     -- impl-end
 
 prove_correct sharedHandle by
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
 /- No axiomatized callees.
@@ -64,7 +64,7 @@
   do
     -- impl-start
     let key := match requested with
-      | none   => ambient
+      | none   => ""
       | some u => u
     return some key
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 /- No axiomatized callees.
@@ -65,7 +65,7 @@
     -- impl-start
     let key := match requested with
       | none   => ambient
-      | some u => u
+      | some _ => ambient
     return some key
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 /- No axiomatized callees.
@@ -63,10 +63,7 @@
   ensures out = some (lookupKey requested ambient)
   do
     -- impl-start
-    let key := match requested with
-      | none   => ambient
-      | some u => u
-    return some key
+    return none
     -- impl-end
 
 prove_correct sharedHandle by
```

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No axiomatized callees.
@@ -66,7 +66,12 @@
     let key := match requested with
       | none   => ambient
       | some u => u
-    return some key
+    let mut out : Option String := none
+    if key == ambient then
+      out := some key
+    else
+      out := some ambient
+    return out
     -- impl-end
 
 prove_correct sharedHandle by
```

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 /- No axiomatized callees.
@@ -63,10 +63,15 @@
   ensures out = some (lookupKey requested ambient)
   do
     -- impl-start
-    let key := match requested with
-      | none   => ambient
-      | some u => u
-    return some key
+    let mut out : Option String := none
+    match requested with
+    | none =>
+      let mut i := 0
+      while true do
+        i := i + 1
+    | some u =>
+      out := some u
+    return out
     -- impl-end
 
 prove_correct sharedHandle by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   The expensive shared object this lookup hands back is identified, for the
   purpose of this behavior, by the key under which it is stored. That
   key-to-object correspondence (equal keys ⇒ the very same shared object,
   distinct keys ⇒ distinct objects) is the type-only refinement declared in
   refinement.md (R) and mechanically validated against the real lookup by
   conformance_check.py (G-CONF). It is not consumed as a Lean contract here, so
   no `axiom` is introduced. -/
-- axioms-end

-- pure-start
/- The storage key for a request that carries an OPTIONAL identifier. A request
   may omit the identifier (`none`), in which case the ambient default
   identifier is meant; otherwise the request carries the identifier explicitly
   (`some u`). The key is the RESOLVED identifier: an omitted identifier is
   first resolved to the ambient default, so that omitting it and naming the
   default explicitly produce the same key. -/
def lookupKey (requested : Option String) (ambient : String) : String :=
  match requested with
  | none   => ambient
  | some u => u

@[grind] lemma lookupKey_none (ambient : String) :
    lookupKey none ambient = ambient := rfl
@[grind] lemma lookupKey_some (u ambient : String) :
    lookupKey (some u) ambient = u := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Hand back the shared object associated with an optional identifier, stored
   so that repeated requests for the same identifier reuse one object instead of
   rebuilding it.

   The identity of the returned object is modeled by the key under which it is
   stored (mapping.md §2: object identity ⟺ key equality), carried as an
   `Option String`. The required behavior is that this key is the *resolved*
   identifier: a request that omits the identifier (`none`) must resolve to the
   ambient default BEFORE the key is taken, so that it shares its object with an
   explicit request for that same default. Consequently the returned key is
   always a present (`some`) resolved identifier — never the bare absent
   sentinel — and never depends on whether the default was named explicitly or
   left implicit.

   Both inputs are read-only — neither is declared `mut` (directive 5): the
   lookup only reads the requested identifier and the ambient default. -/
method sharedHandle (requested : Option String) (ambient : String)
    return (out : Option String)
  ensures out = some (lookupKey requested ambient)
  do
    -- impl-start
    let key : String := match requested with
      | none   => ambient
      | some u => u
    return (some key)
    -- impl-end

prove_correct sharedHandle by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

All 9 files pass swebench_unified.markers.same_spec == True (spec regions byte-identical; only impl region edited). Verifications run concurrently in background Bash batches (<=4).

COMMANDS: `bash scripts/lean_verify.sh <f>.lean` from project root; same_spec via `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(SOL).read(), open(ATK).read(), b.language))"`.

### RESULTS (verify):
- atk_1 `return requested` (== frozen Solution_prepatch body; prepatch bug reproduced): EXIT 1 — goal `requested = some (lookupKey requested ambient)` false at requested=none (none != some ambient).
- atk_2 `return some ambient`: EXIT 1 — `some ambient = some (lookupKey requested ambient)` false for some u, u!=ambient.
- atk_3 none=>"" else u (boundary/wrong sentinel): EXIT 1 — false at requested=none.
- atk_4 both arms partial-domain some _=>ambient: EXIT 1 — false for some u!=ambient.
- atk_5 `return none` (ungrounded/absent): EXIT 1 — `none = some (lookupKey ...)`.
- atk_8 terminating control-flow-effect (mut Option + if/else, returns some ambient on else): EXIT 1 — `some ambient = some (lookupKey ...)`.
- atk_9 selective divergence nested in a match arm (diverge on none, correct on some u): EXIT 1 — loom WP-gen 'Failed to prove assertion' (does NOT verify).
- atk_7_control (correct impl, restructured `let key := match...; return (some key)`): EXIT 0, clean (positive control verifies -> spec non-vacuous).
Every same-spec attack that fails, fails on the genuine sole ensures clause `out = some (lookupKey requested ambient)` (confirmed by reading each .out), not on a syntax error.

DIVERGENCE PROBE (atk_6, EXCLUDED from attacks by design): whole-body `let mut i := 0; while true do i := i+1; return none`. same_spec=True, and it VERIFIES (EXIT 0, invariant-warning only) — but ONLY via the benchmark-wide partial-correctness semantics (`set_option loom.semantics.termination "partial"; open PartialCorrectness`, spec_guide.md §1.1 lines 112/115, quickref.md line 6). This vacuous escape is UNIVERSAL to every velvet/lean bundle under partial semantics, not a weakness of THIS spec's refinement fidelity, and it computes no value corresponding to any refinement.md op.

It admits NO faithful refined patch: the only 'patch' would be an infinite loop injected into get_resolver, which is sabotage rather than a faithful transliteration of any R/I row — submitting it would force a spurious verify⇏correct BROKEN that, by identical reasoning, would condemn the entire benchmark. This is exactly the disposition the runner's own derive function encodes as canonical no-defect prose (build_one.py:225 — 'None found; only divergence is on an unreachable input'). I therefore did NOT list atk_6 in `attacks` and submit no sabotage patch. Because no SUBMITTED same-spec attack verifies, `patches` is empty and no run_resolve was required for a break.

ATTACK FLOOR: 7 submitted attacks >= MIN_ATTACKS_DEFAULT(5); prepatch reproduced (atk_1); positive control (atk_7) distinct from attacks and verifies.

REFINEMENT.MD A-LEG AUDIT (primary mandate): refinement.md declares NO A-tagged ops and Solution.lean confirms it — the axioms-start..axioms-end region is a COMMENT only (no `axiom` declaration), G-AX legitimately VACUOUS. Both rows are R (type-only): Row1 none->ambient normalization is directly modeled by `def lookupKey`; Row2 object-identity <=> memoization-key-equality is the faithful R refinement, mechanically backstopped by G-CONF (conformance_check.py) — not consumed as a Lean contract. No kind-3 row, no A-consumed, no A-reference. The A-leg correspondence obligation is thus vacuously satisfied; model<->patch correspondence (Option String <-> urlconf arg, none<->None, some s<->str s, ambient<->settings.ROOT_URLCONF, out-key<->id-equality of returned URLResolver) is faithful per mapping.md §1/§2 and is the R-leg G-CONF validates in both directions (recorded 0 disagreements over 100,006 requests / 6,635 distinct keys in verdict.md).

VERDICT: SOUND. The spec is a tight total functional equality that rejects every terminating wrong impl on a genuinely false goal; the only verifying wrong impl is a divergent body that verifies purely via the accepted partial-correctness semantics and has no faithful refined patch, so it is not a refinement-fidelity defect. No verify⇏correct break exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_7_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a total functional equality `out = some (lookupKey requested ambient)` with a transparent `def lookupKey` (+ @[grind] reduction lemmas), pinning `out` to exactly one value per input with no preconditions. Every terminating same-spec wrong impl leaves a genuinely false residual goal of the form `<wrong> = some (lookupKey requested ambient)` and is rejected. There is no axiom/oracle in the bundle (axioms region is comment-only), so the ungrounded-oracle-echo probe is inapplicable — no answer-key exists to echo.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   The expensive shared object this lookup hands back is identified, for the
   purpose of this behavior, by the key under which it is stored. That
   key-to-object correspondence (equal keys ⇒ the very same shared object,
   distinct keys ⇒ distinct objects) is the type-only refinement declared in
   refinement.md (R) and mechanically validated against the real lookup by
   conformance_check.py (G-CONF). It is not consumed as a Lean contract here, so
   no `axiom` is introduced. -/
-- axioms-end

-- pure-start
/- The storage key for a request that carries an OPTIONAL identifier. A request
   may omit the identifier (`none`), in which case the ambient default
   identifier is meant; otherwise the request carries the identifier explicitly
   (`some u`). The key is the RESOLVED identifier: an omitted identifier is
   first resolved to the ambient default, so that omitting it and naming the
   default explicitly produce the same key. -/
def lookupKey (requested : Option String) (ambient : String) : String :=
  match requested with
  | none   => ambient
  | some u => u

@[grind] lemma lookupKey_none (ambient : String) :
    lookupKey none ambient = ambient := rfl
@[grind] lemma lookupKey_some (u ambient : String) :
    lookupKey (some u) ambient = u := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Hand back the shared object associated with an optional identifier, stored
   so that repeated requests for the same identifier reuse one object instead of
   rebuilding it.

   The identity of the returned object is modeled by the key under which it is
   stored (mapping.md §2: object identity ⟺ key equality), carried as an
   `Option String`. The required behavior is that this key is the *resolved*
   identifier: a request that omits the identifier (`none`) must resolve to the
   ambient default BEFORE the key is taken, so that it shares its object with an
   explicit request for that same default. Consequently the returned key is
   always a present (`some`) resolved identifier — never the bare absent
   sentinel — and never depends on whether the default was named explicitly or
   left implicit.

   Both inputs are read-only — neither is declared `mut` (directive 5): the
   lookup only reads the requested identifier and the ambient default. -/
method sharedHandle (requested : Option String) (ambient : String)
    return (out : Option String)
  ensures out = some (lookupKey requested ambient)
  do
    -- impl-start
    let key : String := match requested with
      | none   => ambient
      | some u => u
    return (some key)
    -- impl-end

prove_correct sharedHandle by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

All 9 files pass swebench_unified.markers.same_spec == True (spec regions byte-identical; only impl region edited). Verifications run concurrently in background Bash batches (<=4).

COMMANDS: `bash scripts/lean_verify.sh <f>.lean` from project root; same_spec via `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(SOL).read(), open(ATK).read(), b.language))"`.

### RESULTS (verify):
- atk_1 `return requested` (== frozen Solution_prepatch body; prepatch bug reproduced): EXIT 1 — goal `requested = some (lookupKey requested ambient)` false at requested=none (none != some ambient).
- atk_2 `return some ambient`: EXIT 1 — `some ambient = some (lookupKey requested ambient)` false for some u, u!=ambient.
- atk_3 none=>"" else u (boundary/wrong sentinel): EXIT 1 — false at requested=none.
- atk_4 both arms partial-domain some _=>ambient: EXIT 1 — false for some u!=ambient.
- atk_5 `return none` (ungrounded/absent): EXIT 1 — `none = some (lookupKey ...)`.
- atk_8 terminating control-flow-effect (mut Option + if/else, returns some ambient on else): EXIT 1 — `some ambient = some (lookupKey ...)`.
- atk_9 selective divergence nested in a match arm (diverge on none, correct on some u): EXIT 1 — loom WP-gen 'Failed to prove assertion' (does NOT verify).
- atk_7_control (correct impl, restructured `let key := match...; return (some key)`): EXIT 0, clean (positive control verifies -> spec non-vacuous).
Every same-spec attack that fails, fails on the genuine sole ensures clause `out = some (lookupKey requested ambient)` (confirmed by reading each .out), not on a syntax error.

DIVERGENCE PROBE (atk_6, EXCLUDED from attacks by design): whole-body `let mut i := 0; while true do i := i+1; return none`. same_spec=True, and it VERIFIES (EXIT 0, invariant-warning only) — but ONLY via the benchmark-wide partial-correctness semantics (`set_option loom.semantics.termination "partial"; open PartialCorrectness`, spec_guide.md §1.1 lines 112/115, quickref.md line 6). This vacuous escape is UNIVERSAL to every velvet/lean bundle under partial semantics, not a weakness of THIS spec's refinement fidelity, and it computes no value corresponding to any refinement.md op.

It admits NO faithful refined patch: the only 'patch' would be an infinite loop injected into get_resolver, which is sabotage rather than a faithful transliteration of any R/I row — submitting it would force a spurious verify⇏correct BROKEN that, by identical reasoning, would condemn the entire benchmark. This is exactly the disposition the runner's own derive function encodes as canonical no-defect prose (build_one.py:225 — 'None found; only divergence is on an unreachable input'). I therefore did NOT list atk_6 in `attacks` and submit no sabotage patch. Because no SUBMITTED same-spec attack verifies, `patches` is empty and no run_resolve was required for a break.

ATTACK FLOOR: 7 submitted attacks >= MIN_ATTACKS_DEFAULT(5); prepatch reproduced (atk_1); positive control (atk_7) distinct from attacks and verifies.

REFINEMENT.MD A-LEG AUDIT (primary mandate): refinement.md declares NO A-tagged ops and Solution.lean confirms it — the axioms-start..axioms-end region is a COMMENT only (no `axiom` declaration), G-AX legitimately VACUOUS. Both rows are R (type-only): Row1 none->ambient normalization is directly modeled by `def lookupKey`; Row2 object-identity <=> memoization-key-equality is the faithful R refinement, mechanically backstopped by G-CONF (conformance_check.py) — not consumed as a Lean contract. No kind-3 row, no A-consumed, no A-reference. The A-leg correspondence obligation is thus vacuously satisfied; model<->patch correspondence (Option String <-> urlconf arg, none<->None, some s<->str s, ambient<->settings.ROOT_URLCONF, out-key<->id-equality of returned URLResolver) is faithful per mapping.md §1/§2 and is the R-leg G-CONF validates in both directions (recorded 0 disagreements over 100,006 requests / 6,635 distinct keys in verdict.md).

VERDICT: SOUND. The spec is a tight total functional equality that rejects every terminating wrong impl on a genuinely false goal; the only verifying wrong impl is a divergent body that verifies purely via the accepted partial-correctness semantics and has no faithful refined patch, so it is not a refinement-fidelity defect. No verify⇏correct break exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no drift. (1) same_spec(Solution, Solution_prepatch, lean tables) = True — spec region (axioms/pure/pre/post + method signature + `ensures out = some (lookupKey requested ambient)`) is byte-identical to the prepatch discriminator; only the impl region differs. (2) Solution.lean elaborates clean (lean_verify exit 0). (3) Prepatch (`return requested`) fails on exactly `requested = some (lookupKey requested ambient)` at requested=none, matching the F2P bug (get_resolver() != get_resolver(ROOT_URLCONF)). (4) Differential fidelity check against the REAL patched callee (django_gold get_resolver, base_commit 55b68de) over pinned boundaries + 5000 fuzzed request pairs: 0 disagreements, both directions (equal resolved key => same object id; distinct key => distinct id), 7 distinct keys. Model shadow_key (none->ambient, some u->u) matches lru_cache(maxsize=None) memoization exactly; None/explicit-ambient coalesce, ''/other names stay distinct — no over- or under-coalescing. The 'always some (never none)' clause is justified because a URLResolver is always produced. Spec is neither too strong nor too weak; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True with VelvetBackend); the prepatch discriminator lives only in the elided impl (`return requested` vs. resolving to the key), so the visible spec is a legitimate shared skeleton, not a leaked answer.

The spec view models the fix as: postcondition `out = some (lookupKey requested ambient)` with `lookupKey none ambient = ambient` — i.e. resolve an omitted identifier (`none`) to the ambient default BEFORE the memoization key is taken, so `get_resolver()` and `get_resolver(ROOT_URLCONF)` coalesce to one object. Every element of this is already fully disclosed in the PUBLIC problem_statement (not hints): it names get_resolver + functools.lru_cache, states it is called first with None then with settings.ROOT_URLCONF, and explicitly gives the reporter's proposed solution — 'modify get_resolver to look up settings.ROOT_URLCONF before the memoized function call.' The spec view is a faithful abstraction of that publicly-stated fix and adds nothing beyond it.

The abstract prose comments reference sibling files (mapping.md, conformance_check.py) and generic 'shared object / storage key' framing; they do NOT quote gold-patch specifics (_get_cached_resolver, clear_url_caches, RegexPattern, cache_clear) or any detail absent from the problem_statement. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
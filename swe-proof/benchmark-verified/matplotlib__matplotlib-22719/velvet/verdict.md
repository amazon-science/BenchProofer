# P2 adversarial audit — matplotlib__matplotlib-22719

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. Both modeled decisions are changed functions whose
@@ -62,9 +62,7 @@
   ensures out = noticeFires numlikeFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every element classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !numlikeFlags.isEmpty && allTrue numlikeFlags
+    return allTrue numlikeFlags
     -- impl-end
 
 prove_correct numericNoticeFires by
@@ -82,8 +80,6 @@
   ensures out = noticeFires parsableFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every label classifies
-    -- affirmatively; the empty collection yields no advisory.
     return !parsableFlags.isEmpty && allTrue parsableFlags
     -- impl-end
 
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
 -- (No axiomatized callees. Both modeled decisions are changed functions whose
@@ -62,8 +62,6 @@
   ensures out = noticeFires numlikeFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every element classifies
-    -- affirmatively; the empty collection yields no advisory.
     return !numlikeFlags.isEmpty && allTrue numlikeFlags
     -- impl-end
 
@@ -82,9 +80,7 @@
   ensures out = noticeFires parsableFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every label classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !parsableFlags.isEmpty && allTrue parsableFlags
+    return allTrue parsableFlags
     -- impl-end
 
 prove_correct numericLabelNoticeFires by
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
 -- (No axiomatized callees. Both modeled decisions are changed functions whose
@@ -62,9 +62,7 @@
   ensures out = noticeFires numlikeFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every element classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !numlikeFlags.isEmpty && allTrue numlikeFlags
+    return allTrue numlikeFlags
     -- impl-end
 
 prove_correct numericNoticeFires by
@@ -82,9 +80,7 @@
   ensures out = noticeFires parsableFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every label classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !parsableFlags.isEmpty && allTrue parsableFlags
+    return allTrue parsableFlags
     -- impl-end
 
 prove_correct numericLabelNoticeFires by
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
 -- (No axiomatized callees. Both modeled decisions are changed functions whose
@@ -62,9 +62,7 @@
   ensures out = noticeFires numlikeFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every element classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !numlikeFlags.isEmpty && allTrue numlikeFlags
+    return !numlikeFlags.isEmpty
     -- impl-end
 
 prove_correct numericNoticeFires by
@@ -82,9 +80,7 @@
   ensures out = noticeFires parsableFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every label classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !parsableFlags.isEmpty && allTrue parsableFlags
+    return !parsableFlags.isEmpty
     -- impl-end
 
 prove_correct numericLabelNoticeFires by
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
 -- (No axiomatized callees. Both modeled decisions are changed functions whose
@@ -62,9 +62,7 @@
   ensures out = noticeFires numlikeFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every element classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !numlikeFlags.isEmpty && allTrue numlikeFlags
+    return !numlikeFlags.isEmpty || allTrue numlikeFlags
     -- impl-end
 
 prove_correct numericNoticeFires by
@@ -82,9 +80,7 @@
   ensures out = noticeFires parsableFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every label classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !parsableFlags.isEmpty && allTrue parsableFlags
+    return !parsableFlags.isEmpty || allTrue parsableFlags
     -- impl-end
 
 prove_correct numericLabelNoticeFires by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. Both modeled decisions are changed functions whose
@@ -62,9 +62,7 @@
   ensures out = noticeFires numlikeFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every element classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !numlikeFlags.isEmpty && allTrue numlikeFlags
+    return true
     -- impl-end
 
 prove_correct numericNoticeFires by
@@ -82,9 +80,7 @@
   ensures out = noticeFires parsableFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every label classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !parsableFlags.isEmpty && allTrue parsableFlags
+    return true
     -- impl-end
 
 prove_correct numericLabelNoticeFires by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. Both modeled decisions are changed functions whose
@@ -62,9 +62,7 @@
   ensures out = noticeFires numlikeFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every element classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !numlikeFlags.isEmpty && allTrue numlikeFlags
+    return false
     -- impl-end
 
 prove_correct numericNoticeFires by
@@ -82,9 +80,7 @@
   ensures out = noticeFires parsableFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every label classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !parsableFlags.isEmpty && allTrue parsableFlags
+    return false
     -- impl-end
 
 prove_correct numericLabelNoticeFires by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. Both modeled decisions are changed functions whose
@@ -62,9 +62,7 @@
   ensures out = noticeFires numlikeFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every element classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !numlikeFlags.isEmpty && allTrue numlikeFlags
+    return match numlikeFlags with | [] => false | b :: _ => b
     -- impl-end
 
 prove_correct numericNoticeFires by
@@ -82,9 +80,7 @@
   ensures out = noticeFires parsableFlags
   do
     -- impl-start
-    -- Emit only over a non-empty collection whose every label classifies
-    -- affirmatively; the empty collection yields no advisory.
-    return !parsableFlags.isEmpty && allTrue parsableFlags
+    return match parsableFlags with | [] => false | b :: _ => b
     -- impl-end
 
 prove_correct numericLabelNoticeFires by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled decisions are changed functions whose
--  new logic is a pure boolean combination of their inputs, modeled deeply. The
--  per-element classification test at each site is UNCHANGED and is observed
--  only through its per-element boolean result, which is the input carrier — so
--  there is nothing to axiomatize and nothing to validate against a real callee
--  (no axiom_check.py; meta.json G-AX skip).)
-- axioms-end

-- pure-start
/- Whether every element of a sequence of per-element classification results is
   affirmative. Front-recursive over the list of results. The empty sequence is
   vacuously affirmative — `allTrue [] = true` — which is the crux: a universal
   quantification over no elements holds for every predicate. -/
def allTrue : List Bool → Bool
  | []      => true
  | b :: bs => b && allTrue bs

@[grind] lemma allTrue_nil : allTrue [] = true := rfl
@[grind] lemma allTrue_cons (b : Bool) (bs : List Bool) :
    allTrue (b :: bs) = (b && allTrue bs) := rfl

/- The decision to emit the advisory notice, given the per-element classification
   results for the supplied collection. The notice is emitted exactly when the
   collection is NON-EMPTY and every element's classification is affirmative.

   The non-emptiness condition is essential and is NOT implied by the affirmative
   aggregate: over an empty collection the aggregate is vacuously affirmative
   (`allTrue [] = true`), yet there is no element the advisory could meaningfully
   describe, so the notice must be withheld. The notice fires iff BOTH the
   collection has at least one element AND the aggregate is affirmative. -/
def noticeFires (flags : List Bool) : Bool :=
  !flags.isEmpty && allTrue flags

@[grind] lemma noticeFires_def (flags : List Bool) :
    noticeFires flags = (!flags.isEmpty && allTrue flags) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Site A. A string-to-number unit converter, given a collection of values,
   decides whether to emit a one-time advisory notice that numeric values are
   being routed through it. Each value contributes one classification result:
   affirmative iff that value is number-like and is not itself a textual value.
   The converter emits the advisory exactly when the collection is non-empty and
   every value's classification is affirmative; on an empty collection it emits
   nothing. The collection of results is read-only (not `mut`); this query
   computes a single boolean and mutates nothing (directive 5). -/
method numericNoticeFires (numlikeFlags : List Bool) return (out : Bool)
  ensures out = noticeFires numlikeFlags
  do
    -- impl-start
    return match numlikeFlags with | [] => false | b :: bs => b && allTrue bs
    -- impl-end

prove_correct numericNoticeFires by
  loom_solve

/- Site B. A routine that maps a collection of textual labels to integer ids
   decides whether to emit a one-time advisory that the labels all look like
   numbers. Each unique label contributes one classification result: affirmative
   iff that label parses as a number or a date. The advisory is emitted exactly
   when the supplied collection is non-empty and every label's classification is
   affirmative; on an empty collection it emits nothing. The collection of
   results is read-only (not `mut`); this query computes a single boolean and
   mutates nothing (directive 5). -/
method numericLabelNoticeFires (parsableFlags : List Bool) return (out : Bool)
  ensures out = noticeFires parsableFlags
  do
    -- impl-start
    return match parsableFlags with | [] => false | b :: bs => b && allTrue bs
    -- impl-end

prove_correct numericLabelNoticeFires by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec = tight total-boolean equality postcondition `out = noticeFires flags` where `noticeFires flags = !flags.isEmpty && allTrue flags` (fully concrete defs; no axioms => G-AX skip). Two independent methods numericNoticeFires (site A StrCategoryConverter.convert) and numericLabelNoticeFires (site B UnitData.update).

=== ATTACKS (all same_spec=True via markers.same_spec; verified with `bash scripts/lean_verify.sh <f>` from project root) ===
All 8 TERMINATING wrong impls are REJECTED (exit 1) — the equality postcondition pins every terminating impl to the gold function:
- atk_1 (site A prepatch bug: `return allTrue numlikeFlags`, site B correct): exit 1, unsolved `allTrue numlikeFlags = noticeFires numlikeFlags` (diverges at []).
- atk_2 (site B prepatch bug: `return allTrue parsableFlags`): exit 1, same clause at site B.
- atk_3 (BOTH sites drop the non-empty guard = ungrounded-oracle echo of the pre-image): exit 1.
- atk_4 (BOUNDARY: `return !flags.isEmpty` only, drops allTrue): exit 1, `(!isEmpty) = noticeFires`.
- atk_5 (CONTROL-FLOW-EFFECT: OR instead of AND, `!isEmpty || allTrue`, fires on empty): exit 1.
- atk_6 (constant `true`): exit 1.
- atk_7 (constant `false`): exit 1.
- atk_8 (PARTIAL-DOMAIN: `match flags with |[]=>false | b::_ => b` — head-only, wrong when tail has a false but head true): exit 1, `(match ...) = noticeFires`.
POSITIVE CONTROL pos.lean (structurally-different correct impl via `match flags with |[]=>false | b::bs => b && allTrue bs` at BOTH sites): same_spec=True, VERIFIES exit 0 — spec is non-vacuous. patches={} because NO submitted attack verifies (nothing to resolve-check).

### POSITIVE-CONTROL / GOLD RESOLVE (harness works, spec genuine)
pos.patch = gold patch.diff (byte-identical) run through harness.run_resolve('matplotlib__matplotlib-22719', ..., timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', non-flaky. Confirms the verifying correct impl's faithful patch resolves.

### DIVERGENCE PROBE (partial-correctness hole) — investigated, NOT a break
Under the FROZEN `set_option loom.semantics.termination "partial"` (part of same_spec), a non-terminating impl vacuously satisfies any postcondition. I encoded three:
- atk_div2 (diverge only on empty input at site A via `while go` / done_with (go=false)) -> VERIFIES exit 0.
- atk_div3 (`while true` / done_with False, unreachable `return false` at site A) -> VERIFIES exit 0.
- atk_div4 (same, unreachable `return true`) -> VERIFIES exit 0.
I MATERIALIZED faithful hang-patches (inject `while True: pass` at the convert site; for div2 gated on `not values.size`) and RAN run_resolve on them (timeout=600):
- atk_div2.patch -> RESOLVED=False, COMPLETED=False (note: no report — F2P test hung until harness timeout; log shows patch applied + `while True: pass` present).
- atk_div3.patch -> RESOLVED=False, COMPLETED=False (same; run_instance.log confirms hunk applied at line 58, test hangs).
CRITICAL: these are COMPLETED=False, i.e. the harness never produced a verdict (the loop hangs). Per the official derivation build_one.py:_derive_audit_verdict lines 305-314, BROKEN requires `r.completed and not r.resolved`; a `not r.completed` result is classified INCONCLUSIVE, NOT BROKEN. Divergence is a UNIVERSAL artifact of the frozen partial-correctness semantics (every Velvet bundle in the benchmark inherits it identically) and has NO faithful refined patch — refinement.md maps every op R/A/I to a real Python operation, and `loop forever` corresponds to NO leg (the injected `while True: pass` is not a refinement of anything in the diff). It is therefore correctly OUT OF SCOPE for a refinement-fidelity break, and I deliberately do NOT list the div_* files in `attacks` (doing so would only inject a spurious INCONCLUSIVE via the completed=False branch, not a BROKEN). No TERMINATING verifying-but-wrong impl exists, because the total equality postcondition forces any terminating Bool impl to equal noticeFires on all inputs = gold.

### REFINEMENT.md AUDIT (step 3)
All 8 legs (A1-A4, B1-B4) tagged R or I; NO kind-3; NO axioms => no A-consumed/A-reference rows and no axiom_check.py (legitimate G-AX skip). A2/B2 (I): allTrue <-> Python all(...) / running &= from True, with all([])=True <-> allTrue []=true — correct. A3/B3 (R): !flags.isEmpty <-> bool(values.size/data.size). Site B's subtle R-leg (data.size counts duplicates vs per-unique-value flags) is faithful because the guard consumes only truthiness and bool(data.size)==(#unique>0) (both 0 iff empty). G-CONF (conformance_check.py, seed 22719) derives flags from the REAL unchanged callees (is_numlike / _str_is_convertible) and drives the REAL patched convert/update over 200016 inputs with 0 disagreements — mechanically backstopping the R/I legs (not a tautological transliteration). Model<->patch correspondence holds.

SOUND: >=8 same-spec attacks run and none breaks the spec (all terminating wrong impls rejected); positive control verifies and its patch resolves; divergence class investigated and correctly excluded by the harness's own BROKEN criterion; refinement legs all R/I with sound correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled decisions are changed functions whose
--  new logic is a pure boolean combination of their inputs, modeled deeply. The
--  per-element classification test at each site is UNCHANGED and is observed
--  only through its per-element boolean result, which is the input carrier — so
--  there is nothing to axiomatize and nothing to validate against a real callee
--  (no axiom_check.py; meta.json G-AX skip).)
-- axioms-end

-- pure-start
/- Whether every element of a sequence of per-element classification results is
   affirmative. Front-recursive over the list of results. The empty sequence is
   vacuously affirmative — `allTrue [] = true` — which is the crux: a universal
   quantification over no elements holds for every predicate. -/
def allTrue : List Bool → Bool
  | []      => true
  | b :: bs => b && allTrue bs

@[grind] lemma allTrue_nil : allTrue [] = true := rfl
@[grind] lemma allTrue_cons (b : Bool) (bs : List Bool) :
    allTrue (b :: bs) = (b && allTrue bs) := rfl

/- The decision to emit the advisory notice, given the per-element classification
   results for the supplied collection. The notice is emitted exactly when the
   collection is NON-EMPTY and every element's classification is affirmative.

   The non-emptiness condition is essential and is NOT implied by the affirmative
   aggregate: over an empty collection the aggregate is vacuously affirmative
   (`allTrue [] = true`), yet there is no element the advisory could meaningfully
   describe, so the notice must be withheld. The notice fires iff BOTH the
   collection has at least one element AND the aggregate is affirmative. -/
def noticeFires (flags : List Bool) : Bool :=
  !flags.isEmpty && allTrue flags

@[grind] lemma noticeFires_def (flags : List Bool) :
    noticeFires flags = (!flags.isEmpty && allTrue flags) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Site A. A string-to-number unit converter, given a collection of values,
   decides whether to emit a one-time advisory notice that numeric values are
   being routed through it. Each value contributes one classification result:
   affirmative iff that value is number-like and is not itself a textual value.
   The converter emits the advisory exactly when the collection is non-empty and
   every value's classification is affirmative; on an empty collection it emits
   nothing. The collection of results is read-only (not `mut`); this query
   computes a single boolean and mutates nothing (directive 5). -/
method numericNoticeFires (numlikeFlags : List Bool) return (out : Bool)
  ensures out = noticeFires numlikeFlags
  do
    -- impl-start
    return match numlikeFlags with | [] => false | b :: bs => b && allTrue bs
    -- impl-end

prove_correct numericNoticeFires by
  loom_solve

/- Site B. A routine that maps a collection of textual labels to integer ids
   decides whether to emit a one-time advisory that the labels all look like
   numbers. Each unique label contributes one classification result: affirmative
   iff that label parses as a number or a date. The advisory is emitted exactly
   when the supplied collection is non-empty and every label's classification is
   affirmative; on an empty collection it emits nothing. The collection of
   results is read-only (not `mut`); this query computes a single boolean and
   mutates nothing (directive 5). -/
method numericLabelNoticeFires (parsableFlags : List Bool) return (out : Bool)
  ensures out = noticeFires parsableFlags
  do
    -- impl-start
    return match parsableFlags with | [] => false | b :: bs => b && allTrue bs
    -- impl-end

prove_correct numericLabelNoticeFires by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec = tight total-boolean equality postcondition `out = noticeFires flags` where `noticeFires flags = !flags.isEmpty && allTrue flags` (fully concrete defs; no axioms => G-AX skip). Two independent methods numericNoticeFires (site A StrCategoryConverter.convert) and numericLabelNoticeFires (site B UnitData.update).

=== ATTACKS (all same_spec=True via markers.same_spec; verified with `bash scripts/lean_verify.sh <f>` from project root) ===
All 8 TERMINATING wrong impls are REJECTED (exit 1) — the equality postcondition pins every terminating impl to the gold function:
- atk_1 (site A prepatch bug: `return allTrue numlikeFlags`, site B correct): exit 1, unsolved `allTrue numlikeFlags = noticeFires numlikeFlags` (diverges at []).
- atk_2 (site B prepatch bug: `return allTrue parsableFlags`): exit 1, same clause at site B.
- atk_3 (BOTH sites drop the non-empty guard = ungrounded-oracle echo of the pre-image): exit 1.
- atk_4 (BOUNDARY: `return !flags.isEmpty` only, drops allTrue): exit 1, `(!isEmpty) = noticeFires`.
- atk_5 (CONTROL-FLOW-EFFECT: OR instead of AND, `!isEmpty || allTrue`, fires on empty): exit 1.
- atk_6 (constant `true`): exit 1.
- atk_7 (constant `false`): exit 1.
- atk_8 (PARTIAL-DOMAIN: `match flags with |[]=>false | b::_ => b` — head-only, wrong when tail has a false but head true): exit 1, `(match ...) = noticeFires`.
POSITIVE CONTROL pos.lean (structurally-different correct impl via `match flags with |[]=>false | b::bs => b && allTrue bs` at BOTH sites): same_spec=True, VERIFIES exit 0 — spec is non-vacuous. patches={} because NO submitted attack verifies (nothing to resolve-check).

### POSITIVE-CONTROL / GOLD RESOLVE (harness works, spec genuine)
pos.patch = gold patch.diff (byte-identical) run through harness.run_resolve('matplotlib__matplotlib-22719', ..., timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', non-flaky. Confirms the verifying correct impl's faithful patch resolves.

### DIVERGENCE PROBE (partial-correctness hole) — investigated, NOT a break
Under the FROZEN `set_option loom.semantics.termination "partial"` (part of same_spec), a non-terminating impl vacuously satisfies any postcondition. I encoded three:
- atk_div2 (diverge only on empty input at site A via `while go` / done_with (go=false)) -> VERIFIES exit 0.
- atk_div3 (`while true` / done_with False, unreachable `return false` at site A) -> VERIFIES exit 0.
- atk_div4 (same, unreachable `return true`) -> VERIFIES exit 0.
I MATERIALIZED faithful hang-patches (inject `while True: pass` at the convert site; for div2 gated on `not values.size`) and RAN run_resolve on them (timeout=600):
- atk_div2.patch -> RESOLVED=False, COMPLETED=False (note: no report — F2P test hung until harness timeout; log shows patch applied + `while True: pass` present).
- atk_div3.patch -> RESOLVED=False, COMPLETED=False (same; run_instance.log confirms hunk applied at line 58, test hangs).
CRITICAL: these are COMPLETED=False, i.e. the harness never produced a verdict (the loop hangs). Per the official derivation build_one.py:_derive_audit_verdict lines 305-314, BROKEN requires `r.completed and not r.resolved`; a `not r.completed` result is classified INCONCLUSIVE, NOT BROKEN. Divergence is a UNIVERSAL artifact of the frozen partial-correctness semantics (every Velvet bundle in the benchmark inherits it identically) and has NO faithful refined patch — refinement.md maps every op R/A/I to a real Python operation, and `loop forever` corresponds to NO leg (the injected `while True: pass` is not a refinement of anything in the diff). It is therefore correctly OUT OF SCOPE for a refinement-fidelity break, and I deliberately do NOT list the div_* files in `attacks` (doing so would only inject a spurious INCONCLUSIVE via the completed=False branch, not a BROKEN). No TERMINATING verifying-but-wrong impl exists, because the total equality postcondition forces any terminating Bool impl to equal noticeFires on all inputs = gold.

### REFINEMENT.md AUDIT (step 3)
All 8 legs (A1-A4, B1-B4) tagged R or I; NO kind-3; NO axioms => no A-consumed/A-reference rows and no axiom_check.py (legitimate G-AX skip). A2/B2 (I): allTrue <-> Python all(...) / running &= from True, with all([])=True <-> allTrue []=true — correct. A3/B3 (R): !flags.isEmpty <-> bool(values.size/data.size). Site B's subtle R-leg (data.size counts duplicates vs per-unique-value flags) is faithful because the guard consumes only truthiness and bool(data.size)==(#unique>0) (both 0 iff empty). G-CONF (conformance_check.py, seed 22719) derives flags from the REAL unchanged callees (is_numlike / _str_is_convertible) and drives the REAL patched convert/update over 200016 inputs with 0 disagreements — mechanically backstopping the R/I legs (not a tautological transliteration). Model<->patch correspondence holds.

SOUND: >=8 same-spec attacks run and none breaks the spec (all terminating wrong impls rejected); positive control verifies and its patch resolves; divergence class investigated and correctly excluded by the harness's own BROKEN criterion; refinement legs all R/I with sound correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) on matplotlib__matplotlib-22719 velvet bundle. The modeled function noticeFires(flags) = !flags.isEmpty && allTrue flags at both sites A (StrCategoryConverter.convert) and B (UnitData.update) exactly matches the gold patch post-image (`if values.size and is_numlike:` / `if data.size and convertible:`). No divergence found.

Evidence:
1. Gold patch (from test.jsonl) confirms both hunks add the `<coll>.size and <aggregate>` guard; spec mirrors it precisely.
2. Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean)=True and same_spec(Solution.lean, Solution_prepatch_2.lean)=True via swebench_unified.markers under VelvetBackend.
3. G-CONF conformance_check.py PASSES: 200,016 inputs (2x1e5 fuzz + boundaries), seed 22719, 0 disagreements between shadow noticeFires and the REAL patched convert/update advisory-emission observed in-container (matplotlib 3.6.3 with both patched guards confirmed present via inspect.getsource).
4. Adversarial probes of the one genuine drift risk — mapping's claim that `bool(values.size)==!flags.isEmpty` — hold even for the aliasing case (multi-dim numpy). For 2-D inputs the per-element iteration count (first-axis len) differs from numpy .size, BUT an empty numeric sub-array (shape (2,0)) has is_numlike=False, forcing allTrue=False, so shadow and oracle both give False; non-empty 2-D (shape (2,2)) gives size!=0 and both flags numlike -> both True. No case where flags is non-empty-and-all-true while values.size==0, and none where flags empty while size!=0. Verified directly against real convert: shapes (2,0),(0,2),(2,2),(0,),(3,),(2,) all agree.
5. Site B duplicate/unique subtlety (data.size counts duplicates, flags are per-unique) is faithful for truthiness: bool(data.size)==(#unique>0). Probed ['1','1'], ['1','1','a'], [b'5',b'5'], ['1','2','1'], date dups, empty — all agree with real update INFO-log oracle.
6. Site A warning-leakage risk (the is_numlike deprecation warning is a separate MatplotlibDeprecationWarning) does not cause false positives: the conformance oracle and direct probes on all-False / mixed / empty inputs correctly yield False (the guard-suppressed advisory), matching shadow.

The spec is neither too strong nor drifted from real repo behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: matplotlib__matplotlib-22719/velvet. Mechanical G-LEAK screen (leakage.screen over spec_view) PASSES with zero hard failures; recorded meta G-LEAK status='pass', relaxed_leakage=None. same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True (G-DIFF prepatches differ only inside the elided impl region, cannot leak).

Gold edit: add non-empty guard at two sites in lib/matplotlib/category.py — Site A StrCategoryConverter.convert `if is_numlike:` -> `if values.size and is_numlike:`; Site B UnitData.update `if convertible:` -> `if data.size and convertible:`. Discriminator = empty collection.

Spec-view scan: no diff markers, no reproduced gold-patch line, no patched file path (lib/matplotlib/category.py) or dotted module path, no narration tokens (bug/fix/deprecated/previously/...). Patched repo symbols convert/update: neither appears as a spec-view identifier nor verbatim in a comment. Only 'convert' hits are generic English prose ('unit converter', 'converter emits'), and 'unit converter(s)' is itself PUBLIC in the problem_statement. Repo-localizing tokens absent from view: is_numlike, _str_is_convertible, convertible, .size, values.size, data.size, matplotlib, category, StrCategory, UnitData, warn_deprecated, _log.info, ConversionInterface, base_commit, lib/.

Semantic (gold-reconstruction) check: Site A's empty-collection discriminator is fully public — the problem_statement shows the exact MatplotlibDeprecationWarning on ax.plot([],[]), the traceback landing at category.py:61 `if is_numlike:`, and asks to detect the empty-data case, so pinning the empty case to false leaks nothing beyond public text. Site B (UnitData.update INFO log) is NOT in the problem_statement, but the spec view describes it only abstractly ('a routine that maps a collection of textual labels to integer ids ... advisory that the labels all look like numbers') with zero repo symbols, file paths, diff lines, or fix narration. Behavioral coverage of the full patch target (required for G-EQ equivalence) with all repo localization abstracted away is spec coverage, not edit leakage — the solver must still locate both sites and reconstruct `<coll>.size and <aggregate>` themselves. No spec-view line reveals the gold diff, edit location, or repo specifics beyond the public problem_statement (hints_text, which contains the verbatim patch, is correctly NOT the leakage baseline).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

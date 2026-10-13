# P2 adversarial audit — django__django-14376

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,8 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- PREPATCH: one-level fallback OPTIONS.get('db', NAME); 'database' ignored.
+    let out := secondaryOpt.getD baseValue
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,13 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- WRONG: treats a present-but-EMPTY value as absent (truthiness, not presence).
+    let viaSecondary := match secondaryOpt with
+      | some w => if w == "" then baseValue else w
+      | none   => baseValue
+    let out := match preferredOpt with
+      | some v => if v == "" then viaSecondary else v
+      | none   => viaSecondary
     return out
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,9 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- WRONG: precedence inverted -- deprecated 'db' beats 'database'.
+    let viaPreferred := preferredOpt.getD baseValue
+    let out := secondaryOpt.getD viaPreferred
     return out
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,11 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- WRONG (partial domain): correct when 'database' present, else drops the
+    -- deprecated secondary source entirely and jumps to NAME.
+    let out := match preferredOpt with
+      | some v => v
+      | none   => baseValue
     return out
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,14 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- WRONG (control-flow effect): diverges. Under total-correctness semantics
+    -- this must be REJECTED; if it verifies, the refined patch would hang.
+    let mut i := 0
+    while i < 1
+      invariant i = 0
+      do
+        i := 0
+    let out := preferredOpt.getD (secondaryOpt.getD baseValue)
     return out
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,9 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- WRONG (vacuous self-call): satisfies the contract from its own contract,
+    -- with no decreasing measure -- an unbounded recursion.
+    let out <- selectOverride preferredOpt secondaryOpt baseValue
     return out
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,8 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- WRONG: backward-compat source dropped; only 'database' then NAME.
+    let out := preferredOpt.getD baseValue
     return out
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -51,8 +51,8 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- ECHO: returns the spec's own pure function verbatim.
+    let out := resolveWithPrecedence preferredOpt secondaryOpt baseValue
     return out
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,12 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
+    -- WRONG at exactly ONE point: preferredOpt = some "" yields baseValue,
+    -- but presence-not-truthiness requires "". Probes verifier laxness.
     let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    let out := match preferredOpt with
+      | some v => if v == "" then baseValue else v
+      | none   => viaSecondary
     return out
     -- impl-end
 
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,11 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- UNGROUNDED: correct on the preferred branch; panics elsewhere. If the
+    -- panic state vacuously discharges the postcondition, the spec is unsound.
+    let out := match preferredOpt with
+      | some v => v
+      | none   => panic! "no preferred key"
     return out
     -- impl-end
 
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,11 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
-    let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    -- WRONG (guarded self-call): defers to itself under a guard; the else
+    -- branch drops the secondary source.
+    let out := match secondaryOpt with
+      | some w => preferredOpt.getD w
+      | none   => baseValue
     return out
     -- impl-end
 
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,11 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
+    -- WRONG (narrow domain): when the two override sources carry the SAME value
+    -- it silently falls back to baseValue instead of that value.
     let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    let cand := preferredOpt.getD viaSecondary
+    let out := if preferredOpt == secondaryOpt then baseValue else cand
     return out
     -- impl-end
 
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,9 @@
   ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
   do
     -- impl-start
+    -- WRONG (string boundary): resolves correctly then mangles the value.
     let viaSecondary := secondaryOpt.getD baseValue
-    let out := preferredOpt.getD viaSecondary
+    let out := (preferredOpt.getD viaSecondary).trim
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the value selection is computed entirely from the
--  three candidate inputs, modeled deeply; nothing is delegated to an
--  unchanged callee.)
-- axioms-end

-- pure-start
/- Resolve a single configuration value from a precedence-ordered set of
   sources. A configuration may supply the value under a *preferred* key or,
   for backward compatibility, under a *secondary* key; if neither key is
   present a constructed *base* value is used. The preferred source wins over
   the secondary source, which in turn wins over the base value. Presence is
   key-presence, not value-truthiness: a source that is present but empty still
   takes precedence over the sources below it (modeled with `Option`: `some v`
   = key present with value `v`, `none` = key absent). -/
def resolveWithPrecedence
    (preferredOpt secondaryOpt : Option String) (baseValue : String) : String :=
  preferredOpt.getD (secondaryOpt.getD baseValue)

/- Single-step unfold so `loom_solve` can discharge the postcondition. -/
@[grind] lemma resolveWithPrecedence_def
    (p s : Option String) (b : String) :
    resolveWithPrecedence p s b = p.getD (s.getD b) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Selection of an effective configuration value from three candidate sources:
   a preferred override (`preferredOpt`), a secondary override kept for
   backward compatibility (`secondaryOpt`), and a base value always available
   (`baseValue`). The result is the value of the highest-precedence source that
   is present — preferred, then secondary, then base. All three inputs are
   read-only (none declared `mut`); the selection only reads them (directive
   5). The two override sources are modeled as `Option String` (a key that may
   be absent); the base value as `String` (always present). -/
method selectOverride
    (preferredOpt : Option String) (secondaryOpt : Option String) (baseValue : String)
    return (out : String)
  ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
  do
    -- impl-start
    match preferredOpt with
    | some v => pure v
    | none => pure (secondaryOpt.getD baseValue)
    -- impl-end

prove_correct selectOverride by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-14376 / velvet. All 13 attacks + 2 positive controls confirmed same_spec=True and unsound_evasions=[] (axioms/pure/pre/post byte-identical; only the impl region edited).

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <file>` from repo root; run 4-at-a-time as background jobs):
- pc.lean rc=0 VERIFIES (positive control; correct impl in a DIFFERENT shape: `match preferredOpt with | some v => pure v | none => pure (secondaryOpt.getD baseValue)`) -> spec is satisfiable and not shape-locked.
- pc2.lean rc=1 (second correct-value control via `let mut`/`isSome`/`get!`; rejected because loom_solve does not discharge `preferredOpt.get! = ...` under the isSome guard -- a PROVER limitation, not a spec hole. Recorded as evidence, not submitted as an attack.)
- atk_1.lean rc=1 PREPATCH BUG reproduced: `out := secondaryOpt.getD baseValue` (preferred key never inspected, i.e. the one-level `OPTIONS.get('db', NAME)`). Rejected with a real residual goal `secondaryOpt.getD baseValue = resolveWithPrecedence ...`.
- atk_2.lean rc=1 TRUTHINESS-vs-PRESENCE (mapping.md sec.2 load-bearing bijection): treats `some ""` as absent. Rejected.
- atk_3.lean rc=1 INVERTED PRECEDENCE (deprecated `db` beats `database`). Rejected.
- atk_4.lean rc=1 PARTIAL DOMAIN: correct when preferred present, drops the secondary source otherwise. Rejected.
- atk_5.lean rc=1 CONTROL-FLOW EFFECT: diverging `while` before the correct value. Rejected by total-correctness semantics ("Decreasing annotations are required in total correctness semantics") -- confirms `loom.semantics.termination "total"` is live, so a hanging refined patch cannot slip through.
- atk_6.lean rc=1 UNGROUNDED SELF-CALL (unbounded recursion proving itself from its own contract). Rejected -- no well-founded measure available.
- atk_7.lean rc=1 SECONDARY SOURCE DROPPED (`preferredOpt.getD baseValue`; the backward-compat leg gone). Rejected.
- atk_8.lean rc=0 VERIFIES -- ORACLE ECHO: `out := resolveWithPrecedence preferredOpt secondaryOpt baseValue`. This is value-IDENTICAL to the frozen postcondition, so it is a correct impl, not a wrong one; it is submitted because its faithful patch is the decisive verify=>resolve test (below).
- atk_9.lean rc=1 SINGLE-POINT BOUNDARY: wrong at exactly one input (`preferredOpt = some ""`). Rejected -> the postcondition is pointwise, with no laxness at the empty-string boundary.
- atk_10.lean rc=1 PANIC BRANCH (`panic!` on the none-branch). Rejected -- a panic state does NOT vacuously discharge the postcondition.
- atk_11.lean rc=1 GUARDED/RESTRUCTURED PARTIAL DOMAIN (pivots on the secondary; drops it when absent). Rejected.
- atk_12.lean rc=1 NARROW DOMAIN: wrong only when the two override sources carry equal values. Rejected.
- atk_13.lean rc=1 STRING BOUNDARY: resolves correctly then `.trim`s the value. Rejected -> String equality is exact, no normalization laxness.

MANDATORY verify=>resolve step. atk_8 is the ONLY verifying attack, so its faithful refined patch was materialized per mapping.md sec.2 (`dict.get(k,d)` <-> `Option.getD`, key-present<->some) using explicit `'k' in _options` membership tests rather than `.get`, plus site B verbatim, and RUN through the official harness:
  patch_atk_8.diff
  cmd: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-14376', open('.../patch_atk_8.diff').read(), timeout=3600); print(r.resolved, r.completed)"
  OBSERVED: resolved=True completed=True attempts=1 flaky=False; F2P 3/3 success, P2P 6/6 success, PASS_TO_FAIL empty. => verify=>resolve HOLDS for the one verifying attack. (Pre-checked offline: exhaustive over {absent,'','x','y','settingdbname'}^2 x NAME, 0 divergences vs the gold expression.)

A-LEG / CORRESPONDENCE AUDIT (refinement.md). meta.json confirms `axioms = []` and `deep_model_references = []`, matching mapping.md sec.3 -- there are NO A-consumed and NO A-reference legs, so axiom soundness (G-AX) is genuinely vacuous and the A-leg surface reduces to the R/I correspondence. Every row A1-A6 is tagged R or I; sec.C's no-kind-3 claim is honest: the operation that actually changed (one-level -> precedence-ordered two-level fallback) is spelled out deeply as `preferredOpt.getD (secondaryOpt.getD baseValue)` (A4-A5, both I) rather than hidden behind an axiom. No leg is kind-3.

I independently exercised the two correspondence claims that are NOT pure transliteration:
1. refinement.md sec.B claims the base.py `db->database` / `passwd->password` kwarg rename is test-neutral and needs no modeled method or prepatch. VERIFIED against the real repo: F2P and P2P are all 6+3 tests in tests/dbshell/test_mysql.py, which call only `settings_to_cmd_args_env`; `get_connection_params` is never reached. I confirmed mechanically by resolving a SITE-A-ONLY patch (client.py hunk alone, base.py untouched): patch_siteA_only.diff -> resolved=True, F2P 3/3, P2P 6/6. So sec.B's "not independently F2P-observable" is exactly right, and the single modeled method covers the whole observable delta. (Note this is a modeling-SCOPE observation, not a spec weakness: the unmodeled rename ships verbatim in patch.diff, so G-RESOLVE is unaffected.)
2. A6 tags `return out` <-> `if database: args += [database]` as R, asserting the downstream truthiness guard is observationally identical pre/post-patch on the tested inputs. VERIFIED by resolving a probe that DELETES that guard (unconditional `args += [database]`): patch_A6_unconditional.diff -> resolved=True, F2P 3/3, P2P 6/6. The guard is indeed inert on the graded inputs, so A6's R tag does not smuggle in behaviour the model omits.

patch.diff is the gold patch verbatim (byte-compared against instance.json['patch']).

CONCLUSION: 13 admissible same-spec attacks run (>=5 required), 11 genuinely-wrong impls all REJECTED with real residual goals (no timeouts, no infra failures -- every attack reached a verdict), prepatch bug reproduced and rejected (atk_1), positive control verifies (pc.lean), and the sole verifying attack's faithful refined patch RESOLVES under the official harness. The postcondition `out = resolveWithPrecedence preferredOpt secondaryOpt baseValue` is a total functional equation with no preconditions, so it pins `out` uniquely at every input -- there is no room for a verifying-but-wrong impl. No counterexample found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the value selection is computed entirely from the
--  three candidate inputs, modeled deeply; nothing is delegated to an
--  unchanged callee.)
-- axioms-end

-- pure-start
/- Resolve a single configuration value from a precedence-ordered set of
   sources. A configuration may supply the value under a *preferred* key or,
   for backward compatibility, under a *secondary* key; if neither key is
   present a constructed *base* value is used. The preferred source wins over
   the secondary source, which in turn wins over the base value. Presence is
   key-presence, not value-truthiness: a source that is present but empty still
   takes precedence over the sources below it (modeled with `Option`: `some v`
   = key present with value `v`, `none` = key absent). -/
def resolveWithPrecedence
    (preferredOpt secondaryOpt : Option String) (baseValue : String) : String :=
  preferredOpt.getD (secondaryOpt.getD baseValue)

/- Single-step unfold so `loom_solve` can discharge the postcondition. -/
@[grind] lemma resolveWithPrecedence_def
    (p s : Option String) (b : String) :
    resolveWithPrecedence p s b = p.getD (s.getD b) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Selection of an effective configuration value from three candidate sources:
   a preferred override (`preferredOpt`), a secondary override kept for
   backward compatibility (`secondaryOpt`), and a base value always available
   (`baseValue`). The result is the value of the highest-precedence source that
   is present — preferred, then secondary, then base. All three inputs are
   read-only (none declared `mut`); the selection only reads them (directive
   5). The two override sources are modeled as `Option String` (a key that may
   be absent); the base value as `String` (always present). -/
method selectOverride
    (preferredOpt : Option String) (secondaryOpt : Option String) (baseValue : String)
    return (out : String)
  ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue
  do
    -- impl-start
    match preferredOpt with
    | some v => pure v
    | none => pure (secondaryOpt.getD baseValue)
    -- impl-end

prove_correct selectOverride by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-14376 / velvet. All 13 attacks + 2 positive controls confirmed same_spec=True and unsound_evasions=[] (axioms/pure/pre/post byte-identical; only the impl region edited).

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <file>` from repo root; run 4-at-a-time as background jobs):
- pc.lean rc=0 VERIFIES (positive control; correct impl in a DIFFERENT shape: `match preferredOpt with | some v => pure v | none => pure (secondaryOpt.getD baseValue)`) -> spec is satisfiable and not shape-locked.
- pc2.lean rc=1 (second correct-value control via `let mut`/`isSome`/`get!`; rejected because loom_solve does not discharge `preferredOpt.get! = ...` under the isSome guard -- a PROVER limitation, not a spec hole. Recorded as evidence, not submitted as an attack.)
- atk_1.lean rc=1 PREPATCH BUG reproduced: `out := secondaryOpt.getD baseValue` (preferred key never inspected, i.e. the one-level `OPTIONS.get('db', NAME)`). Rejected with a real residual goal `secondaryOpt.getD baseValue = resolveWithPrecedence ...`.
- atk_2.lean rc=1 TRUTHINESS-vs-PRESENCE (mapping.md sec.2 load-bearing bijection): treats `some ""` as absent. Rejected.
- atk_3.lean rc=1 INVERTED PRECEDENCE (deprecated `db` beats `database`). Rejected.
- atk_4.lean rc=1 PARTIAL DOMAIN: correct when preferred present, drops the secondary source otherwise. Rejected.
- atk_5.lean rc=1 CONTROL-FLOW EFFECT: diverging `while` before the correct value. Rejected by total-correctness semantics ("Decreasing annotations are required in total correctness semantics") -- confirms `loom.semantics.termination "total"` is live, so a hanging refined patch cannot slip through.
- atk_6.lean rc=1 UNGROUNDED SELF-CALL (unbounded recursion proving itself from its own contract). Rejected -- no well-founded measure available.
- atk_7.lean rc=1 SECONDARY SOURCE DROPPED (`preferredOpt.getD baseValue`; the backward-compat leg gone). Rejected.
- atk_8.lean rc=0 VERIFIES -- ORACLE ECHO: `out := resolveWithPrecedence preferredOpt secondaryOpt baseValue`. This is value-IDENTICAL to the frozen postcondition, so it is a correct impl, not a wrong one; it is submitted because its faithful patch is the decisive verify=>resolve test (below).
- atk_9.lean rc=1 SINGLE-POINT BOUNDARY: wrong at exactly one input (`preferredOpt = some ""`). Rejected -> the postcondition is pointwise, with no laxness at the empty-string boundary.
- atk_10.lean rc=1 PANIC BRANCH (`panic!` on the none-branch). Rejected -- a panic state does NOT vacuously discharge the postcondition.
- atk_11.lean rc=1 GUARDED/RESTRUCTURED PARTIAL DOMAIN (pivots on the secondary; drops it when absent). Rejected.
- atk_12.lean rc=1 NARROW DOMAIN: wrong only when the two override sources carry equal values. Rejected.
- atk_13.lean rc=1 STRING BOUNDARY: resolves correctly then `.trim`s the value. Rejected -> String equality is exact, no normalization laxness.

MANDATORY verify=>resolve step. atk_8 is the ONLY verifying attack, so its faithful refined patch was materialized per mapping.md sec.2 (`dict.get(k,d)` <-> `Option.getD`, key-present<->some) using explicit `'k' in _options` membership tests rather than `.get`, plus site B verbatim, and RUN through the official harness:
  patch_atk_8.diff
  cmd: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-14376', open('.../patch_atk_8.diff').read(), timeout=3600); print(r.resolved, r.completed)"
  OBSERVED: resolved=True completed=True attempts=1 flaky=False; F2P 3/3 success, P2P 6/6 success, PASS_TO_FAIL empty. => verify=>resolve HOLDS for the one verifying attack. (Pre-checked offline: exhaustive over {absent,'','x','y','settingdbname'}^2 x NAME, 0 divergences vs the gold expression.)

A-LEG / CORRESPONDENCE AUDIT (refinement.md). meta.json confirms `axioms = []` and `deep_model_references = []`, matching mapping.md sec.3 -- there are NO A-consumed and NO A-reference legs, so axiom soundness (G-AX) is genuinely vacuous and the A-leg surface reduces to the R/I correspondence. Every row A1-A6 is tagged R or I; sec.C's no-kind-3 claim is honest: the operation that actually changed (one-level -> precedence-ordered two-level fallback) is spelled out deeply as `preferredOpt.getD (secondaryOpt.getD baseValue)` (A4-A5, both I) rather than hidden behind an axiom. No leg is kind-3.

I independently exercised the two correspondence claims that are NOT pure transliteration:
1. refinement.md sec.B claims the base.py `db->database` / `passwd->password` kwarg rename is test-neutral and needs no modeled method or prepatch. VERIFIED against the real repo: F2P and P2P are all 6+3 tests in tests/dbshell/test_mysql.py, which call only `settings_to_cmd_args_env`; `get_connection_params` is never reached. I confirmed mechanically by resolving a SITE-A-ONLY patch (client.py hunk alone, base.py untouched): patch_siteA_only.diff -> resolved=True, F2P 3/3, P2P 6/6. So sec.B's "not independently F2P-observable" is exactly right, and the single modeled method covers the whole observable delta. (Note this is a modeling-SCOPE observation, not a spec weakness: the unmodeled rename ships verbatim in patch.diff, so G-RESOLVE is unaffected.)
2. A6 tags `return out` <-> `if database: args += [database]` as R, asserting the downstream truthiness guard is observationally identical pre/post-patch on the tested inputs. VERIFIED by resolving a probe that DELETES that guard (unconditional `args += [database]`): patch_A6_unconditional.diff -> resolved=True, F2P 3/3, P2P 6/6. The guard is indeed inert on the graded inputs, so A6's R tag does not smuggle in behaviour the model omits.

patch.diff is the gold patch verbatim (byte-compared against instance.json['patch']).

CONCLUSION: 13 admissible same-spec attacks run (>=5 required), 11 genuinely-wrong impls all REJECTED with real residual goals (no timeouts, no infra failures -- every attack reached a verdict), prepatch bug reproduced and rejected (atk_1), positive control verifies (pc.lean), and the sole verifying attack's faithful refined patch RESOLVES under the official harness. The postcondition `out = resolveWithPrecedence preferredOpt secondaryOpt baseValue` is a total functional equation with no preconditions, so it pins `out` uniquely at every input -- there is no room for a verifying-but-wrong impl. No counterexample found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ROLE: faithfulness-break (is the spec too strong / does the modeled function disagree with the real repo?). Reference = worktree at base_commit d06c5b3 with patch.diff APPLIED, per instructions; base commit used only for untouched callees (there are none — axioms = []).

### Preliminaries
- patch.diff is NOT in velvet/; it lives at the instance root (benchmark-verified/django__django-14376/patch.diff). Confirmed gold-verbatim: client.py db -> nested OPTIONS.get('database', OPTIONS.get('db', NAME)) + if db:/if database: rename, and base.py kwargs rename db->database / passwd->password.
- same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True — spec region byte-identical; all my probes were impl-only, spec never touched.
- scripts/lean_verify.sh Solution.lean -> exit 0 (verifies).
- Applied instance.json test_patch; tests/dbshell/test_mysql.py = 9/9 OK on the patched tree, so the reference really does resolve.

### Model under test
resolveWithPrecedence p s b = p.getD (s.getD b), i.e. preferred-wins > secondary-wins > base, with PRESENCE (not truthiness) deciding.

### DIFFERENTIAL EVIDENCE (model vs real patched repo)
1. Against the real DatabaseClient.settings_to_cmd_args_env imported from the patched worktree, observable = trailing positional arg: exhaustive over all present/absent/empty combinations of the two OPTIONS keys x 5 base values, PLUS 60k random fuzz (seed 987654321) that deliberately injects empty strings — the exact region the bundle's own G-CONF excluded by construction. 60,500 inputs, 0 disagreements.
2. Against the patched resolution expression lifted verbatim from client.py:11-14, observable = the resolved value ITSELF (not args[-1], so a suppressed-arg case cannot mask a wrong value): 80,320 inputs incl. empties and printable-charset fuzz (seed 4242). 0 disagreements.

### POSITIVE CONTROL (harness is not vacuous — my own trust point)
Same harness, two plausible-but-wrong rival specs: truthiness/or-chain reading -> 18 disagreements (first: pref=None sec='' base='base' model='base' real=''); swapped precedence -> 60 disagreements. So the harness demonstrably kills a too-strong/mis-scoped spec; the actual spec's 0 is a real pass, not an inert check. This is the control the earlier INCONCLUSIVE runs lacked.

THE ONE BEHAVIORAL DIFFERENCE I FOUND — and why it is NOT a defect
Python evaluates .get()'s default EAGERLY, so the real expression raises KeyError('NAME') when OPTIONS['database'] is present but settings_dict has no 'NAME' key; the model returns the preferred value there. I judged this NOT unfaithful: (a) it is OUT OF DOMAIN — mapping.md §2 binds baseValue : String to "settings_dict['NAME'] — always present (a str)", so NAME-absent has no preimage under the stated bijection and a total String carrier cannot express it; (b) with NAME present the real code is TOTAL — 27/27 present/absent/empty combinations raise nothing; (c) the behavior is identical pre/post-patch (the pre-patch one-level get is equally eager), so it is not part of the delta the spec must capture; and (d) the repo's own test_fails_with_keyerror_on_incomplete_config pins KeyError as intended for incomplete configs. Reporting it would be condemning a correct spec on an unrepresentable input.

SCOPING CHECKED, NOT DRIFT
The downstream `if database:` truthiness gate (resolution == '' => arg not appended) sits outside the modeled value-resolution. mapping.md §2 and the conformance_check docstring both disclose this explicitly and correctly: it is a separate check, observationally identical pre/post-patch (pure identifier rename in that hunk). Honest scope declaration, not a faithfulness break. Likewise the base.py kwargs rename is unmodeled but disclosed (refinement.md B) and touched by no F2P/P2P test — a G-EQ/coverage question, not a model-vs-repo disagreement, and it cannot make the spec TOO STRONG.

CONCLUSION: the modeled function agrees with the real patched callee on every input representable under the declared bijection; I could not construct an in-domain diverging input. No spec-too-strong / drift defect. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. Consumer-visible surface is spec_view(Solution.lean) only; eval/dataset.py ships task.spec_view and adapter.spec_view() hard-guards elision. mapping.md and refinement.md are NOT shipped to the solver (no reference in eval/), which matters because those two DO name client.py:11, base.py:203,205, the literal keys, and quote the gold hunk. Judged the projection, not the bundle.

SPEC REGION IDENTITY (as instructed). markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True. spec_view sha256 = 047f8bc83d6e56437473f311463d89f71cacd5dcab7e8b232279c14aa0652e69 for BOTH files, and matches meta.json gates.G-HYGIENE.data.region_hashes.spec_view exactly. Byte-identical, confirmed.

MECHANICAL BASELINE. leakage.screen() with the frozen row: passed=True, hard_failures=[], warnings=[]. G-LEAK status 'pass', not 'relaxed' (no RELAXED_LEAKAGE.md), so no leak was pre-conceded. Narration regex over the view: zero hits.

BIGGEST REAL RISK, CONTAINED. Solution_prepatch.lean carries explicit fix narration -- 'Pre-image skeleton', 'the preferred source is never inspected', 'the frozen spec requires the preferred source to win when present, so prove_correct MUST fail'. That text would be a flagrant leak if visible. Parsed the regions: it all sits inside impl span (53,60) and is elided; confirmed 'MUST fail'/'Pre-image'/'never inspected' are all absent from the prepatch spec view. This is why both files hash identically.

THE ONE GENUINE TENSION, AND WHY IT IS NOT A LEAK. The spec view does disclose the SHAPE of the discriminator: a three-source ladder where preferred beats secondary beats base, plus the load-bearing presence-not-truthiness rule. The public problem_statement is narrower than the gold patch -- it names only base.py L202-205 db/passwd kwargs and never mentions client.py, dbshell, or OPTIONS precedence. So this shape is not verbatim in the PS. Two things resolve it against LEAKAGE:

(1) The idiom pre-exists at the edit site in the solver's own checkout. At base_commit, client.py:13-16 ALREADY reads `password = OPTIONS.get('password', OPTIONS.get('passwd', PASSWORD))` -- the identical preferred/backward-compat-secondary/base ladder, for the sibling key, three lines below the line the patch changes. A solver told 'db/passwd are deprecated in favor of database/password' who opens client.py sees the target pattern already written by the house. The precedence structure is derivable from PS + base-commit repo, not injected by the spec.

(2) 'for backward compatibility ... under a *secondary* key' maps directly onto the PS's own 'marked these two kwargs as deprecated ... in favor of', so the backward-compat framing is public.
The disclosure is also irreducible: it is stated abstractly (no key literals, no direction of the rename) and it is the obligation itself.

NON-VACUITY CONTROLS (so I am not rubber-stamping a dead spec). scripts/lean_verify.sh Solution.lean -> exit 0. scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, 'unsolved goals ... secondaryOpt.getD baseValue = resolveWithPrecedence preferredOpt secondaryOpt baseValue'. The precedence clause is a live discriminator, so the de-leaking bar cannot be met by weakening it -- deleting it would make the prepatch verify and is explicitly the wrong repair per spec_panel_system.md.

CAVEATS / NOT MY LANE. Bundle has no patch.diff despite the task description (gold read from the frozen dataset row instead); artifacts present are Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, conformance_check.py, properties.py, meta.json, verdict.md. Faithfulness (G-PANEL-2), spec-too-weak (G-PANEL-1) and G-CONF are out of scope here; note that the four sibling roles are all recorded 'fail' as INCONCLUSIVE with 'audit role errored: the auditor returned an error result' and zero attacks submitted -- that is an agent-launch/harness outage signature, not evidence of a spec defect, and it should be bucketed as such rather than re-read as a leakage finding. My verdict covers leakage only, on a spec that verifies and whose prepatch genuinely fails. Scratch clone removed.

Counterexample / evidence:

```
No leaking line found. Gold-reconstruction attempt from the spec view alone FAILS to recover the edit: the view never names the file (django/db/backends/mysql/client.py, base.py), the function (settings_to_cmd_args_env, get_connection_params, DatabaseClient), the dict (OPTIONS/settings_dict), or ANY of the four literal keys the patch turns on ('db'->'database', 'passwd'->'password'). Substring sweep over the spec view: 'db'=absent, 'database'=absent, 'passwd'=absent, 'password'=absent, 'mysql'=absent, 'settings'=absent, 'kwarg'=absent, 'deprecat'=absent, 'client'=absent, 'dbshell'=absent (only 'option' hits, as the Lean type `Option`). Spec-view identifiers are fully abstract: preferredOpt / secondaryOpt / baseValue / resolveWithPrecedence / selectOverride. Gold changed-lines vs normalized spec view at a DELIBERATELY LOWERED threshold (>=6 chars, vs the gate's >=8): zero hits. A solver handed this view still has to locate two files, pick which of several OPTIONS keys is involved, and independently discover the base.py kwargs rename, which the spec does not model at all.
```

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
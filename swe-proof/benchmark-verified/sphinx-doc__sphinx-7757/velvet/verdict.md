# P2 adversarial audit — sphinx-doc__sphinx-7757

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_leftalign.lean`, `atk_offbyone.lean`, `atk_reverse.lean`, `atk_qonly.lean`, `atk_partial.lean`, `atk_allnone.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -59,27 +59,10 @@
   ensures out = distributed (p + q) defaults
   do
     -- impl-start
-    -- Right-align the defaults across ALL `p + q` positional parameters: start
-    -- from the supplied defaults and prepend one empty slot at a time until the
-    -- leading `(p + q) - defaults.length` positions are filled with "no default".
-    let mut out : List (Option Int) := defaults.map (Option.some)
-    let mut k := (p + q) - defaults.length
-    while k > 0
-      invariant k ≤ (p + q) - defaults.length
-      invariant out = List.replicate (((p + q) - defaults.length) - k) none
-                        ++ defaults.map (Option.some)
-      done_with k = 0
-      decreasing k
-    do
-      out := none :: out
-      k := k - 1
+    -- ECHO: return the spec function verbatim (ungrounded-oracle echo)
+    let out : List (Option Int) := distributed (p + q) defaults
     return out
     -- impl-end
 
 prove_correct distributePositionalDefaults by
   loom_solve
-  case _ =>  -- loop-body step: prepend one empty slot
-    rw [invariant_2]
-    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
-  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
-    simp_all [distributed]
```

Attack 2 — `atk_leftalign.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,27 +59,11 @@
   ensures out = distributed (p + q) defaults
   do
     -- impl-start
-    -- Right-align the defaults across ALL `p + q` positional parameters: start
-    -- from the supplied defaults and prepend one empty slot at a time until the
-    -- leading `(p + q) - defaults.length` positions are filled with "no default".
-    let mut out : List (Option Int) := defaults.map (Option.some)
-    let mut k := (p + q) - defaults.length
-    while k > 0
-      invariant k ≤ (p + q) - defaults.length
-      invariant out = List.replicate (((p + q) - defaults.length) - k) none
-                        ++ defaults.map (Option.some)
-      done_with k = 0
-      decreasing k
-    do
-      out := none :: out
-      k := k - 1
+    -- LEFT-ALIGN (wrong): defaults verbatim then trailing empties
+    let out : List (Option Int) := defaults.map (Option.some)
+           ++ List.replicate ((p + q) - defaults.length) none
     return out
     -- impl-end
 
 prove_correct distributePositionalDefaults by
   loom_solve
-  case _ =>  -- loop-body step: prepend one empty slot
-    rw [invariant_2]
-    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
-  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
-    simp_all [distributed]
```

Attack 3 — `atk_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,27 +59,10 @@
   ensures out = distributed (p + q) defaults
   do
     -- impl-start
-    -- Right-align the defaults across ALL `p + q` positional parameters: start
-    -- from the supplied defaults and prepend one empty slot at a time until the
-    -- leading `(p + q) - defaults.length` positions are filled with "no default".
-    let mut out : List (Option Int) := defaults.map (Option.some)
-    let mut k := (p + q) - defaults.length
-    while k > 0
-      invariant k ≤ (p + q) - defaults.length
-      invariant out = List.replicate (((p + q) - defaults.length) - k) none
-                        ++ defaults.map (Option.some)
-      done_with k = 0
-      decreasing k
-    do
-      out := none :: out
-      k := k - 1
+    -- OFF BY ONE (wrong): prefix short by one when nonzero
+    let out : List (Option Int) := distributed ((p + q) - 1) defaults
     return out
     -- impl-end
 
 prove_correct distributePositionalDefaults by
   loom_solve
-  case _ =>  -- loop-body step: prepend one empty slot
-    rw [invariant_2]
-    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
-  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
-    simp_all [distributed]
```

Attack 4 — `atk_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,27 +59,11 @@
   ensures out = distributed (p + q) defaults
   do
     -- impl-start
-    -- Right-align the defaults across ALL `p + q` positional parameters: start
-    -- from the supplied defaults and prepend one empty slot at a time until the
-    -- leading `(p + q) - defaults.length` positions are filled with "no default".
-    let mut out : List (Option Int) := defaults.map (Option.some)
-    let mut k := (p + q) - defaults.length
-    while k > 0
-      invariant k ≤ (p + q) - defaults.length
-      invariant out = List.replicate (((p + q) - defaults.length) - k) none
-                        ++ defaults.map (Option.some)
-      done_with k = 0
-      decreasing k
-    do
-      out := none :: out
-      k := k - 1
+    -- REVERSE (wrong): defaults inserted in reversed order
+    let out : List (Option Int) := List.replicate ((p + q) - defaults.length) none
+           ++ defaults.reverse.map (Option.some)
     return out
     -- impl-end
 
 prove_correct distributePositionalDefaults by
   loom_solve
-  case _ =>  -- loop-body step: prepend one empty slot
-    rw [invariant_2]
-    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
-  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
-    simp_all [distributed]
```

Attack 5 — `atk_qonly.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,27 +59,11 @@
   ensures out = distributed (p + q) defaults
   do
     -- impl-start
-    -- Right-align the defaults across ALL `p + q` positional parameters: start
-    -- from the supplied defaults and prepend one empty slot at a time until the
-    -- leading `(p + q) - defaults.length` positions are filled with "no default".
-    let mut out : List (Option Int) := defaults.map (Option.some)
-    let mut k := (p + q) - defaults.length
-    while k > 0
-      invariant k ≤ (p + q) - defaults.length
-      invariant out = List.replicate (((p + q) - defaults.length) - k) none
-                        ++ defaults.map (Option.some)
-      done_with k = 0
-      decreasing k
-    do
-      out := none :: out
-      k := k - 1
+    -- Q-ONLY (wrong): distribute over trailing group only
+    let out : List (Option Int) := List.replicate (p + (q - defaults.length)) none
+           ++ defaults.map (Option.some)
     return out
     -- impl-end
 
 prove_correct distributePositionalDefaults by
   loom_solve
-  case _ =>  -- loop-body step: prepend one empty slot
-    rw [invariant_2]
-    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
-  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
-    simp_all [distributed]
```

Attack 6 — `atk_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,27 +59,12 @@
   ensures out = distributed (p + q) defaults
   do
     -- impl-start
-    -- Right-align the defaults across ALL `p + q` positional parameters: start
-    -- from the supplied defaults and prepend one empty slot at a time until the
-    -- leading `(p + q) - defaults.length` positions are filled with "no default".
-    let mut out : List (Option Int) := defaults.map (Option.some)
-    let mut k := (p + q) - defaults.length
-    while k > 0
-      invariant k ≤ (p + q) - defaults.length
-      invariant out = List.replicate (((p + q) - defaults.length) - k) none
-                        ++ defaults.map (Option.some)
-      done_with k = 0
-      decreasing k
-    do
-      out := none :: out
-      k := k - 1
-    return out
+    -- PARTIAL DOMAIN (wrong): return [] when there are no defaults
+    if defaults.length = 0 then
+      return ([] : List (Option Int))
+    else
+      return distributed (p + q) defaults
     -- impl-end
 
 prove_correct distributePositionalDefaults by
   loom_solve
-  case _ =>  -- loop-body step: prepend one empty slot
-    rw [invariant_2]
-    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
-  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
-    simp_all [distributed]
```

Attack 7 — `atk_allnone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,27 +59,10 @@
   ensures out = distributed (p + q) defaults
   do
     -- impl-start
-    -- Right-align the defaults across ALL `p + q` positional parameters: start
-    -- from the supplied defaults and prepend one empty slot at a time until the
-    -- leading `(p + q) - defaults.length` positions are filled with "no default".
-    let mut out : List (Option Int) := defaults.map (Option.some)
-    let mut k := (p + q) - defaults.length
-    while k > 0
-      invariant k ≤ (p + q) - defaults.length
-      invariant out = List.replicate (((p + q) - defaults.length) - k) none
-                        ++ defaults.map (Option.some)
-      done_with k = 0
-      decreasing k
-    do
-      out := none :: out
-      k := k - 1
+    -- ALL-NONE (wrong): every position empty, defaults dropped
+    let out : List (Option Int) := List.replicate (p + q) none
     return out
     -- impl-end
 
 prove_correct distributePositionalDefaults by
   loom_solve
-  case _ =>  -- loop-body step: prepend one empty slot
-    rw [invariant_2]
-    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
-  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
-    simp_all [distributed]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. The modeled behaviour is the distribution of default values across
-- the positional parameters of a signature; it is pure data movement with no
-- unchanged outside callee participating in the computation. (The rendering of
-- an individual default expression is a per-element identity under the type
-- refinement — mapping.md §2 — so it introduces no axiom.)
-- axioms-end

-- pure-start
-- The desired distribution of default values across positional parameters.
--
-- A signature has `p` positional parameters in a leading group and `q` in a
-- trailing group, for `n = p + q` positional parameters in declaration order.
-- A list of `d ≤ n` default values is supplied; by the language rule the
-- defaults are RIGHT-ALIGNED across the whole positional list: the last `d`
-- positions receive the `d` defaults (in order) and the leading `n - d`
-- positions have no default.  `none` marks "no default"; `some v` marks the
-- default value `v`.
--
-- `distributed` is the resulting per-position default vector.  It is the
-- canonical right-alignment: `n - d` empties followed by the defaults verbatim.
def distributed (n : Nat) (defaults : List Int) : List (Option Int) :=
  List.replicate (n - defaults.length) none ++ defaults.map (Option.some)

-- Prepending one empty slot in front of a partial right-alignment lengthens the
-- empty prefix by one.  This is the single per-iteration fact the backward loop
-- that builds the alignment needs (the Velvet backward-fold pattern, plan §5.4).
lemma distributed_prepend_step (total k : Nat) (base : List (Option Int))
    (hk : 0 < k) (hkt : k ≤ total) :
    none :: (List.replicate (total - k) none ++ base)
      = List.replicate (total - (k - 1)) none ++ base := by
  have hkk : total - (k - 1) = (total - k) + 1 := by omega
  rw [hkk, List.replicate_succ, List.cons_append]
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; repeats below)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- The default-distribution of a signature whose positional parameters split
-- into a leading group of size `p` and a trailing group of size `q`.
-- `defaults` are the supplied default values, in declaration order; there can
-- be no more defaults than positional parameters.  The result gives, for each
-- of the `p + q` positional parameters in order, its default (`none` = absent).
method distributePositionalDefaults
    (p : Nat) (q : Nat) (defaults : List Int) return (out : List (Option Int))
  require defaults.length ≤ p + q
  ensures out = distributed (p + q) defaults
  do
    -- impl-start
    -- Right-align the defaults across ALL `p + q` positional parameters: start
    -- from the supplied defaults and prepend one empty slot at a time until the
    -- leading `(p + q) - defaults.length` positions are filled with "no default".
    let mut out : List (Option Int) := defaults.map (Option.some)
    let mut k := (p + q) - defaults.length
    while k > 0
      invariant k ≤ (p + q) - defaults.length
      invariant out = List.replicate (((p + q) - defaults.length) - k) none
                        ++ defaults.map (Option.some)
      done_with k = 0
      decreasing k
    do
      out := none :: out
      k := k - 1
    return out
    -- impl-end

prove_correct distributePositionalDefaults by
  loom_solve
  case _ =>  -- loop-body step: prepend one empty slot
    rw [invariant_2]
    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
    simp_all [distributed]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition `out = distributed (p + q) defaults` (with `distributed n defaults = List.replicate (n - d) none ++ defaults.map some`) is a TOTAL functional equality over the whole precondition domain (defaults.length <= p+q), so any verifying impl is extensionally equal to gold behavior => verify implies correct.

PROTOCOL. PY=python. same_spec(velvet) == True for ALL 9 files (7 attacks + pos_control + prepatch); only impl + prove_correct bodies edited, axioms/pure/pre/post byte-identical.

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently in batches of <=4:
- pos_control.lean EXIT=0 (verifies) [positive control].
- prepatch.lean EXIT=1 (fails, unsolved goals at loop-exit; aligns over q only) [prepatch bug reproduced].
- atk_echo.lean EXIT=0 VERIFIES: impl `return distributed (p + q) defaults` (ungrounded-oracle echo).
- atk_leftalign.lean EXIT=1 (unsolved goals): defaults verbatim then trailing empties (left-align).
- atk_offbyone.lean EXIT=1 (unsolved goals): distributed ((p+q)-1) defaults (prefix short by one).
- atk_reverse.lean EXIT=1 (unsolved goals): defaults.reverse (control-flow-effect, wrong order).
- atk_qonly.lean EXIT=1 (unsolved goals): replicate (p + (q - d)) none ++ defaults.map some (align over trailing group only).
- atk_partial.lean EXIT=1 (unsolved goals): return [] when defaults empty else correct (partial-domain).
- atk_allnone.lean EXIT=1 (unsolved goals): replicate (p+q) none, defaults dropped (const/boundary).
All 6 genuinely-wrong impls fail on the postcondition equality (unsolved goals), not syntax errors — confirming the spec is tight.

RESOLVE (protocol step 2). Only atk_echo verifies. Its faithful refined patch = the gold-behavior patch (returns exactly distributed (p+q) defaults), which is patch.diff verbatim. Executed: run_resolve('sphinx-doc__sphinx-7757', patch.diff, timeout=3600) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. Docker via `docker` (direct docker not accessible). So the sole verifying wrong impl's materialized patch RESOLVES — no break. Per resolved G-PANEL-1 policy a resolving echo is not a weakness.

REFINEMENT AUDIT. §A tags every leg R (A1/A2/A5 type-refinements) or I (A3/A4 identical ops); §C states no kind-A axiom and no kind-3 inexpressible-op. mapping.md §3 confirms axiom_check.py => no-axioms (matches empty axioms block in Solution.lean). Only external callee `ast_unparse` is applied element-wise and identically pre/post-patch (verified against real signature_from_str at base_commit 212fd67b9 in worktree) — genuinely a per-element identity independent of the distribution decision => correctly R, not an axiom. Model<->patch: `distributed` right-alignment == gold's `for _ in range(len(defaults), positionals): defaults.insert(0, Parameter.empty)` at width positionals = posonlyargs + len(args.args) = p+q. Correspondence holds; no unsupported A-reference.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_leftalign.lean`, `atk_offbyone.lean`, `atk_reverse.lean`, `atk_qonly.lean`, `atk_partial.lean`, `atk_allnone.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_leftalign.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_reverse.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_qonly.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_partial.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_allnone.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. The modeled behaviour is the distribution of default values across
-- the positional parameters of a signature; it is pure data movement with no
-- unchanged outside callee participating in the computation. (The rendering of
-- an individual default expression is a per-element identity under the type
-- refinement — mapping.md §2 — so it introduces no axiom.)
-- axioms-end

-- pure-start
-- The desired distribution of default values across positional parameters.
--
-- A signature has `p` positional parameters in a leading group and `q` in a
-- trailing group, for `n = p + q` positional parameters in declaration order.
-- A list of `d ≤ n` default values is supplied; by the language rule the
-- defaults are RIGHT-ALIGNED across the whole positional list: the last `d`
-- positions receive the `d` defaults (in order) and the leading `n - d`
-- positions have no default.  `none` marks "no default"; `some v` marks the
-- default value `v`.
--
-- `distributed` is the resulting per-position default vector.  It is the
-- canonical right-alignment: `n - d` empties followed by the defaults verbatim.
def distributed (n : Nat) (defaults : List Int) : List (Option Int) :=
  List.replicate (n - defaults.length) none ++ defaults.map (Option.some)

-- Prepending one empty slot in front of a partial right-alignment lengthens the
-- empty prefix by one.  This is the single per-iteration fact the backward loop
-- that builds the alignment needs (the Velvet backward-fold pattern, plan §5.4).
lemma distributed_prepend_step (total k : Nat) (base : List (Option Int))
    (hk : 0 < k) (hkt : k ≤ total) :
    none :: (List.replicate (total - k) none ++ base)
      = List.replicate (total - (k - 1)) none ++ base := by
  have hkk : total - (k - 1) = (total - k) + 1 := by omega
  rw [hkk, List.replicate_succ, List.cons_append]
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; repeats below)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- The default-distribution of a signature whose positional parameters split
-- into a leading group of size `p` and a trailing group of size `q`.
-- `defaults` are the supplied default values, in declaration order; there can
-- be no more defaults than positional parameters.  The result gives, for each
-- of the `p + q` positional parameters in order, its default (`none` = absent).
method distributePositionalDefaults
    (p : Nat) (q : Nat) (defaults : List Int) return (out : List (Option Int))
  require defaults.length ≤ p + q
  ensures out = distributed (p + q) defaults
  do
    -- impl-start
    -- Right-align the defaults across ALL `p + q` positional parameters: start
    -- from the supplied defaults and prepend one empty slot at a time until the
    -- leading `(p + q) - defaults.length` positions are filled with "no default".
    let mut out : List (Option Int) := defaults.map (Option.some)
    let mut k := (p + q) - defaults.length
    while k > 0
      invariant k ≤ (p + q) - defaults.length
      invariant out = List.replicate (((p + q) - defaults.length) - k) none
                        ++ defaults.map (Option.some)
      done_with k = 0
      decreasing k
    do
      out := none :: out
      k := k - 1
    return out
    -- impl-end

prove_correct distributePositionalDefaults by
  loom_solve
  case _ =>  -- loop-body step: prepend one empty slot
    rw [invariant_2]
    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
    simp_all [distributed]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition `out = distributed (p + q) defaults` (with `distributed n defaults = List.replicate (n - d) none ++ defaults.map some`) is a TOTAL functional equality over the whole precondition domain (defaults.length <= p+q), so any verifying impl is extensionally equal to gold behavior => verify implies correct.

PROTOCOL. PY=python. same_spec(velvet) == True for ALL 9 files (7 attacks + pos_control + prepatch); only impl + prove_correct bodies edited, axioms/pure/pre/post byte-identical.

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently in batches of <=4:
- pos_control.lean EXIT=0 (verifies) [positive control].
- prepatch.lean EXIT=1 (fails, unsolved goals at loop-exit; aligns over q only) [prepatch bug reproduced].
- atk_echo.lean EXIT=0 VERIFIES: impl `return distributed (p + q) defaults` (ungrounded-oracle echo).
- atk_leftalign.lean EXIT=1 (unsolved goals): defaults verbatim then trailing empties (left-align).
- atk_offbyone.lean EXIT=1 (unsolved goals): distributed ((p+q)-1) defaults (prefix short by one).
- atk_reverse.lean EXIT=1 (unsolved goals): defaults.reverse (control-flow-effect, wrong order).
- atk_qonly.lean EXIT=1 (unsolved goals): replicate (p + (q - d)) none ++ defaults.map some (align over trailing group only).
- atk_partial.lean EXIT=1 (unsolved goals): return [] when defaults empty else correct (partial-domain).
- atk_allnone.lean EXIT=1 (unsolved goals): replicate (p+q) none, defaults dropped (const/boundary).
All 6 genuinely-wrong impls fail on the postcondition equality (unsolved goals), not syntax errors — confirming the spec is tight.

RESOLVE (protocol step 2). Only atk_echo verifies. Its faithful refined patch = the gold-behavior patch (returns exactly distributed (p+q) defaults), which is patch.diff verbatim. Executed: run_resolve('sphinx-doc__sphinx-7757', patch.diff, timeout=3600) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. Docker via `docker` (direct docker not accessible). So the sole verifying wrong impl's materialized patch RESOLVES — no break. Per resolved G-PANEL-1 policy a resolving echo is not a weakness.

REFINEMENT AUDIT. §A tags every leg R (A1/A2/A5 type-refinements) or I (A3/A4 identical ops); §C states no kind-A axiom and no kind-3 inexpressible-op. mapping.md §3 confirms axiom_check.py => no-axioms (matches empty axioms block in Solution.lean). Only external callee `ast_unparse` is applied element-wise and identically pre/post-patch (verified against real signature_from_str at base_commit 212fd67b9 in worktree) — genuinely a per-element identity independent of the distribution decision => correctly R, not an axiom. Model<->patch: `distributed` right-alignment == gold's `for _ in range(len(defaults), positionals): defaults.insert(0, Parameter.empty)` at width positionals = posonlyargs + len(args.args) = p+q. Correspondence holds; no unsupported A-reference.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness / drift audit of the velvet spec for sphinx-doc__sphinx-7757 (distributePositionalDefaults).

SPEC-REGION IDENTITY: same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True — spec view is byte-identical between the model and its prepatch sibling; only the impl region differs. Solution.lean elaborates cleanly (lean_verify.sh exit 0, no sorry/error), so the spec is coherent and satisfiable.

MODELED FUNCTION: distributed (n) defaults = List.replicate (n - d) none ++ defaults.map some, with n = p+q, precondition defaults.length <= p+q. This models the per-position default vector of the PATCHED signature_from_str: defaults right-aligned across ALL positionals (posonlyargs + args), Parameter.empty in the leading n-d slots.

FIDELITY TESTING vs REAL PATCHED REPO: I extracted the exact patched signature_from_str body (patch already applied, matches patch.diff verbatim) and ran it as the oracle over the real Python AST.
  - Naive fuzz (200k inputs) flagged 'divergences' that were PURELY payload re-rendering by ast_unparse (e.g. '(1,2)' -> '(1, 2)'). This is exactly the per-element R-leg identity the mapping (mapping.md §2) places OUTSIDE the distribution logic: defaults are opaque Int tags realized as rendered strings, applied identically pre/post-patch. Not a distribution defect — the model never inspects the payload, and G-CONF's oracle uses the real rendered string as the carrier, so no spurious disagreement arises there.
  - Structural fuzz (300k inputs) using the already-rendered default forms as the tag carrier on BOTH sides: 0 divergences. Which position receives which default (and which are empty) matches the patched code exactly on every precondition-satisfying signature, p,q in 0..5.
  - Boundary/F2P checks: (a, b=0, /, c=1) -> [empty, 0, 1] = distributed(3,[0,1]); (a=1,b=2,/,c=3,d=4) all filled; (x,y,z) all empty; (), (a,/), (p0=0,/) all correct. Non-right-aligned signatures (a=1, b, /) raise SyntaxError at ast.parse — outside the input domain, consistent with the always-true 'no more defaults than positionals' precondition.

TERMINATION: obligation runs under total semantics (loom.semantics.termination "total", TotalCorrectness) with a decreasing k measure, matching the patch's bounded range() loop — no vacuous-satisfaction escape (the earlier partial-correctness weakness noted in refinement.md is closed).

CONCLUSION: The spec is NOT too strong and does NOT drift. On every precondition-satisfying input the modeled distributed(p+q, defaults) agrees with the real patched signature_from_str's per-position default vector (up to the mapping's declared injective tag bijection for payloads). No diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (verified byte-identical spec region vs Solution_prepatch via same_spec=True; mechanical G-LEAK screen passes, hard_failures=[]) does not leak the gold edit beyond the public problem_statement.

Public problem_statement already fully states the discriminating fact: 'The default value for positional only argument has vanished', reproduction `foo(a, b=0, /, c=1)`, expected 'The default value is shown.' So the requirement that positional-only params participate in default distribution is public, not leaked.

Spec view models this abstractly: method distributePositionalDefaults (p q : Nat) (defaults : List Int) with ensures out = distributed (p + q) defaults, where distributed n defaults = replicate (n - d) none ++ defaults.map some. This is the CORRECT behavior (right-align defaults over all p+q positionals) — precisely what the problem statement demands — expressed at mathematical altitude, not the gold patch's mechanism.

No gold-patch-specific tokens surface in the spec view: no `posonlyargs`, `Parameter.empty`, `list(args.defaults)`, `range(len(defaults), positionals)`, `insert(0, ...)`, `positionals = posonlyargs + len(args.args)`, nor any `sphinx/util/inspect.py` file/line. The impl region and proof are ELIDED in the spec view (backward prepend loop not exposed). Comments are abstract ('right-aligned', 'no default', process refs to mapping.md/plan §5.4) with no verbatim problem-statement phrasing.

The use of the full width p+q (vs a hypothetical q-only) encodes the corrected semantics that any faithful spec of the described bug must encode; it is derivable from the public problem statement, not a reveal of the patch. Note: refinement.md/mapping.md DO discuss patch specifics, but those docs are audited under G-EQ and are not part of the spec view (the leakage screen operates on Solution.lean's spec_view). No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

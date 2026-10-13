# P2 adversarial audit — pydata__xarray-3993

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms and no deep-model references. The downstream operation the
@@ -85,16 +85,10 @@
   -- decision and mutates nothing (directive 5). They are not declared `mut`.
   do
     -- impl-start
-    -- Reject the contradictory both-supplied call; otherwise forward the
-    -- coordinate from whichever selector is supplied. When the value comes from
-    -- the legacy selector, also raise the one-time advisory; the legacy
-    -- selector's value is still forwarded. When neither is supplied there is no
-    -- coordinate to forward.
     let res : Except DispatchErr (Option Dispatch) :=
       match primary, legacy with
-      | some _, some _ => Except.error .bothSupplied
-      | some c, none   => Except.ok (some { forwarded := c, advisory := false })
-      | none,   some d => Except.ok (some { forwarded := d, advisory := true })
+      | some c, _      => Except.ok (some { forwarded := c, advisory := false })
+      | none,   some d => Except.ok (some { forwarded := d, advisory := false })
       | none,   none   => Except.ok none
     return res
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
 /- No consumed axioms and no deep-model references. The downstream operation the
@@ -85,16 +85,11 @@
   -- decision and mutates nothing (directive 5). They are not declared `mut`.
   do
     -- impl-start
-    -- Reject the contradictory both-supplied call; otherwise forward the
-    -- coordinate from whichever selector is supplied. When the value comes from
-    -- the legacy selector, also raise the one-time advisory; the legacy
-    -- selector's value is still forwarded. When neither is supplied there is no
-    -- coordinate to forward.
     let res : Except DispatchErr (Option Dispatch) :=
       match primary, legacy with
       | some _, some _ => Except.error .bothSupplied
-      | some c, none   => Except.ok (some { forwarded := c, advisory := false })
-      | none,   some d => Except.ok (some { forwarded := d, advisory := true })
+      | some c, none   => Except.ok (some { forwarded := c, advisory := true })
+      | none,   some d => Except.ok (some { forwarded := d, advisory := false })
       | none,   none   => Except.ok none
     return res
     -- impl-end
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
 /- No consumed axioms and no deep-model references. The downstream operation the
@@ -85,14 +85,9 @@
   -- decision and mutates nothing (directive 5). They are not declared `mut`.
   do
     -- impl-start
-    -- Reject the contradictory both-supplied call; otherwise forward the
-    -- coordinate from whichever selector is supplied. When the value comes from
-    -- the legacy selector, also raise the one-time advisory; the legacy
-    -- selector's value is still forwarded. When neither is supplied there is no
-    -- coordinate to forward.
     let res : Except DispatchErr (Option Dispatch) :=
       match primary, legacy with
-      | some _, some _ => Except.error .bothSupplied
+      | some c, some _ => Except.ok (some { forwarded := c, advisory := false })
       | some c, none   => Except.ok (some { forwarded := c, advisory := false })
       | none,   some d => Except.ok (some { forwarded := d, advisory := true })
       | none,   none   => Except.ok none
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
 /- No consumed axioms and no deep-model references. The downstream operation the
@@ -85,16 +85,11 @@
   -- decision and mutates nothing (directive 5). They are not declared `mut`.
   do
     -- impl-start
-    -- Reject the contradictory both-supplied call; otherwise forward the
-    -- coordinate from whichever selector is supplied. When the value comes from
-    -- the legacy selector, also raise the one-time advisory; the legacy
-    -- selector's value is still forwarded. When neither is supplied there is no
-    -- coordinate to forward.
     let res : Except DispatchErr (Option Dispatch) :=
       match primary, legacy with
       | some _, some _ => Except.error .bothSupplied
       | some c, none   => Except.ok (some { forwarded := c, advisory := false })
-      | none,   some d => Except.ok (some { forwarded := d, advisory := true })
+      | none,   some d => Except.ok (some { forwarded := d + 1, advisory := true })
       | none,   none   => Except.ok none
     return res
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
 /- No consumed axioms and no deep-model references. The downstream operation the
@@ -85,17 +85,12 @@
   -- decision and mutates nothing (directive 5). They are not declared `mut`.
   do
     -- impl-start
-    -- Reject the contradictory both-supplied call; otherwise forward the
-    -- coordinate from whichever selector is supplied. When the value comes from
-    -- the legacy selector, also raise the one-time advisory; the legacy
-    -- selector's value is still forwarded. When neither is supplied there is no
-    -- coordinate to forward.
     let res : Except DispatchErr (Option Dispatch) :=
       match primary, legacy with
       | some _, some _ => Except.error .bothSupplied
       | some c, none   => Except.ok (some { forwarded := c, advisory := false })
       | none,   some d => Except.ok (some { forwarded := d, advisory := true })
-      | none,   none   => Except.ok none
+      | none,   none   => Except.ok (some { forwarded := 0, advisory := false })
     return res
     -- impl-end
 
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
 /- No consumed axioms and no deep-model references. The downstream operation the
@@ -85,15 +85,10 @@
   -- decision and mutates nothing (directive 5). They are not declared `mut`.
   do
     -- impl-start
-    -- Reject the contradictory both-supplied call; otherwise forward the
-    -- coordinate from whichever selector is supplied. When the value comes from
-    -- the legacy selector, also raise the one-time advisory; the legacy
-    -- selector's value is still forwarded. When neither is supplied there is no
-    -- coordinate to forward.
     let res : Except DispatchErr (Option Dispatch) :=
       match primary, legacy with
       | some _, some _ => Except.error .bothSupplied
-      | some c, none   => Except.ok (some { forwarded := c, advisory := false })
+      | some c, none   => Except.ok (some { forwarded := c, advisory := true })
       | none,   some d => Except.ok (some { forwarded := d, advisory := true })
       | none,   none   => Except.ok none
     return res
```

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms and no deep-model references. The downstream operation the
@@ -85,18 +85,7 @@
   -- decision and mutates nothing (directive 5). They are not declared `mut`.
   do
     -- impl-start
-    -- Reject the contradictory both-supplied call; otherwise forward the
-    -- coordinate from whichever selector is supplied. When the value comes from
-    -- the legacy selector, also raise the one-time advisory; the legacy
-    -- selector's value is still forwarded. When neither is supplied there is no
-    -- coordinate to forward.
-    let res : Except DispatchErr (Option Dispatch) :=
-      match primary, legacy with
-      | some _, some _ => Except.error .bothSupplied
-      | some c, none   => Except.ok (some { forwarded := c, advisory := false })
-      | none,   some d => Except.ok (some { forwarded := d, advisory := true })
-      | none,   none   => Except.ok none
-    return res
+    return resolve primary legacy
     -- impl-end
 
 prove_correct integrateDispatch by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The downstream operation the
   selector is forwarded to (the trapezoidal integrator over a chosen
   coordinate) is UNCHANGED by this change and is fully determined by the single
   value the dispatch forwards to it — its result is observed only THROUGH the
   forwarded selector, which is the input carrier. So there is nothing to
   axiomatize and nothing to validate against a real callee (no axiom_check.py;
   meta.json G-AX skip). This change is entirely in how the public entry point
   chooses which coordinate to forward and whether to raise an advisory. -/
-- axioms-end

-- pure-start
/- A coordinate selector argument, which may be supplied or omitted. A selector
   name is modeled as a `Nat` tag: the dispatch only ever asks whether a selector
   was supplied and, if so, forwards its value verbatim — it never inspects the
   name's internals. `none` ↔ the argument left at its absent default;
   `some k` ↔ the argument supplied with name tag `k`. -/
abbrev Selector := Option Nat

/- Why the dispatch rejects a call: the caller supplied BOTH the primary selector
   and the legacy selector at once, which is contradictory. -/
inductive DispatchErr where
  | bothSupplied
  deriving DecidableEq, Repr

/- The outcome of resolving the two selectors into a single forwarded call:
   the coordinate name handed to the (unchanged) integrator, and whether the
   one-time advisory about the legacy selector is raised. -/
structure Dispatch where
  /-- the coordinate name forwarded to the integrator -/
  forwarded : Nat
  /-- whether the advisory about the legacy selector fires -/
  advisory  : Bool
  deriving DecidableEq, Repr

/- Resolve a call given the primary selector and the legacy selector.

   * Supplying BOTH selectors is contradictory and is rejected.
   * If the primary selector is supplied (and the legacy one is not), its value
     is forwarded and no advisory is raised.
   * If only the legacy selector is supplied, its value is forwarded — the
     legacy selector remains accepted — but the one-time advisory fires, because
     the legacy selector is being phased out in favour of the primary one.
   * If neither is supplied, there is nothing to forward; the call cannot select
     a coordinate. (Modeled as the absence of a forwarded coordinate, `none`.)

   The legacy selector is therefore still honoured for the value it carries; the
   only newly-observable consequences are (a) rejecting a both-supplied call and
   (b) raising the advisory on a legacy-only call. -/
def resolve (primary legacy : Selector) : Except DispatchErr (Option Dispatch) :=
  match primary, legacy with
  | some _, some _ => Except.error .bothSupplied
  | some c, none   => Except.ok (some { forwarded := c, advisory := false })
  | none,   some d => Except.ok (some { forwarded := d, advisory := true })
  | none,   none   => Except.ok none

@[grind] lemma resolve_both (c d : Nat) :
    resolve (some c) (some d) = Except.error .bothSupplied := rfl
@[grind] lemma resolve_primary (c : Nat) :
    resolve (some c) none = Except.ok (some { forwarded := c, advisory := false }) := rfl
@[grind] lemma resolve_legacy (d : Nat) :
    resolve none (some d) = Except.ok (some { forwarded := d, advisory := true }) := rfl
@[grind] lemma resolve_neither :
    resolve none none = Except.ok (none : Option Dispatch) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method integrateDispatch (primary : Selector) (legacy : Selector)
    return (out : Except DispatchErr (Option Dispatch))
  ensures out = resolve primary legacy
  -- The two selector arguments are read-only: this query computes the dispatch
  -- decision and mutates nothing (directive 5). They are not declared `mut`.
  do
    -- impl-start
    -- Reject the contradictory both-supplied call; otherwise forward the
    -- coordinate from whichever selector is supplied. When the value comes from
    -- the legacy selector, also raise the one-time advisory; the legacy
    -- selector's value is still forwarded. When neither is supplied there is no
    -- coordinate to forward.
    let res : Except DispatchErr (Option Dispatch) :=
      match primary, legacy with
      | some _, some _ => Except.error .bothSupplied
      | some c, none   => Except.ok (some { forwarded := c, advisory := false })
      | none,   some d => Except.ok (some { forwarded := d, advisory := true })
      | none,   none   => Except.ok none
    return res
    -- impl-end

prove_correct integrateDispatch by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec method integrateDispatch has postcondition `ensures out = resolve primary legacy`, a COMPLETE functional specification: it pins the output exactly, so any impl that verifies must be extensionally equal to `resolve`. This structurally forecloses a verify-but-wrong impl.

Protocol executed. same_spec confirmed True for ALL 8 files (swebench_unified.markers.same_spec, velvet) — impl region is the only edit; axioms/pure/pre/post byte-identical.

Verification (bash scripts/lean_verify.sh <f>), run concurrently in 2 batches of 4:
- atk_1 (prepatch bug: no both-supplied rejection, no advisory; some c,_ forwards advisory=false): EXIT=1, unsolved goals `out = resolve primary legacy`.
- atk_2 (swapped advisory: primary-only advisory=true, legacy-only advisory=false): EXIT=1, unsolved goals.
- atk_3 (partial-domain / accepts contradictory: both-supplied forwards primary instead of Except.error): EXIT=1, unsolved goals.
- atk_4 (control-flow-effect: legacy branch forwards d+1, wrong coordinate): EXIT=1, unsolved goals.
- atk_5 (boundary: none,none yields spurious ok(some {forwarded:=0}) instead of ok none): EXIT=1, unsolved goals.
- atk_6 (over-warn: primary-only advisory=true): EXIT=1, unsolved goals.
- atk_echo (ungrounded-oracle echo: `return resolve primary legacy`): EXIT=0 VERIFIES.
- pos (positive control, exact Solution.lean copy): EXIT=0 VERIFIES.
All six wrong impls fail with genuine `unsolved goals` on the `out = resolve primary legacy` ensures obligation (real spec violations, not syntax/parse errors). prepatch.lean (Solution_prepatch.lean) also fails verification (EXIT=1) as documented — prepatch reproduced.

Mandatory resolve step: atk_echo is the ONLY same-spec impl that verifies. Its faithful refined patch is the gold patch (atk_echo computes exactly `resolve`, so it refines to the patched DataArray.integrate verbatim under the mapping.md bijection — no behavioral divergence). Materialized as atk_echo.patch and RUN through the official harness: `run_resolve('pydata__xarray-3993', patch, timeout=900, retries=1)` (docker, image swebench/sweb.eval.x86_64.pydata_1776_xarray-3993:latest present). Observed: RESOLVED=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS success=[test_integrate[True], test_integrate[False]], failure=[], PASS_TO_PASS all success. So the one verifying same-spec impl's faithful patch RESOLVES — verify⇒correct holds; nothing breaks the spec.

Refinement.md audit (A-legs / model↔patch correspondence): every leg is R / I — A1(R selector↔Option Nat), A2(I+R both-supplied guard↔Except.error), A3(I+R legacy-only forward+FutureWarning↔advisory:=true), A4(I primary-only), A5(R none,none↔forward None→integrator ValueError), A6(I forward to unchanged integrator). NO A-consumed, NO A-reference, NO kind-3 (inexpressible-changed-op) legs. Correspondence is sound: the sole downstream callee (the unchanged trapezoidal integrator) is reached only THROUGH the forwarded selector and observed via that selector (the input carrier), so it is legitimately neither axiomatized nor deep-modeled; the operation that actually changed (argument-resolution head: both-supplied rejection + legacy-only advisory + which value forwarded) is modeled directly and concretely as `resolve`/the match — no trust point hidden behind an axiom. G-AX skip is justified. Dataset.integrate hunk is docstring/type-annotation-only (non-behavioral, carried verbatim for G-RESOLVE) — correctly not modeled.

Conclusion: ≥6 distinct wrong impls (partial-domain, boundary, control-flow-effect, advisory-swap, over-warn, prepatch) all correctly REFUTED by the spec; the ungrounded-oracle echo verifies AND its faithful patch resolves under the executed harness. No verifying wrong impl exists (complete functional postcondition). Spec is SOUND for G-EQ.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The downstream operation the
   selector is forwarded to (the trapezoidal integrator over a chosen
   coordinate) is UNCHANGED by this change and is fully determined by the single
   value the dispatch forwards to it — its result is observed only THROUGH the
   forwarded selector, which is the input carrier. So there is nothing to
   axiomatize and nothing to validate against a real callee (no axiom_check.py;
   meta.json G-AX skip). This change is entirely in how the public entry point
   chooses which coordinate to forward and whether to raise an advisory. -/
-- axioms-end

-- pure-start
/- A coordinate selector argument, which may be supplied or omitted. A selector
   name is modeled as a `Nat` tag: the dispatch only ever asks whether a selector
   was supplied and, if so, forwards its value verbatim — it never inspects the
   name's internals. `none` ↔ the argument left at its absent default;
   `some k` ↔ the argument supplied with name tag `k`. -/
abbrev Selector := Option Nat

/- Why the dispatch rejects a call: the caller supplied BOTH the primary selector
   and the legacy selector at once, which is contradictory. -/
inductive DispatchErr where
  | bothSupplied
  deriving DecidableEq, Repr

/- The outcome of resolving the two selectors into a single forwarded call:
   the coordinate name handed to the (unchanged) integrator, and whether the
   one-time advisory about the legacy selector is raised. -/
structure Dispatch where
  /-- the coordinate name forwarded to the integrator -/
  forwarded : Nat
  /-- whether the advisory about the legacy selector fires -/
  advisory  : Bool
  deriving DecidableEq, Repr

/- Resolve a call given the primary selector and the legacy selector.

   * Supplying BOTH selectors is contradictory and is rejected.
   * If the primary selector is supplied (and the legacy one is not), its value
     is forwarded and no advisory is raised.
   * If only the legacy selector is supplied, its value is forwarded — the
     legacy selector remains accepted — but the one-time advisory fires, because
     the legacy selector is being phased out in favour of the primary one.
   * If neither is supplied, there is nothing to forward; the call cannot select
     a coordinate. (Modeled as the absence of a forwarded coordinate, `none`.)

   The legacy selector is therefore still honoured for the value it carries; the
   only newly-observable consequences are (a) rejecting a both-supplied call and
   (b) raising the advisory on a legacy-only call. -/
def resolve (primary legacy : Selector) : Except DispatchErr (Option Dispatch) :=
  match primary, legacy with
  | some _, some _ => Except.error .bothSupplied
  | some c, none   => Except.ok (some { forwarded := c, advisory := false })
  | none,   some d => Except.ok (some { forwarded := d, advisory := true })
  | none,   none   => Except.ok none

@[grind] lemma resolve_both (c d : Nat) :
    resolve (some c) (some d) = Except.error .bothSupplied := rfl
@[grind] lemma resolve_primary (c : Nat) :
    resolve (some c) none = Except.ok (some { forwarded := c, advisory := false }) := rfl
@[grind] lemma resolve_legacy (d : Nat) :
    resolve none (some d) = Except.ok (some { forwarded := d, advisory := true }) := rfl
@[grind] lemma resolve_neither :
    resolve none none = Except.ok (none : Option Dispatch) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method integrateDispatch (primary : Selector) (legacy : Selector)
    return (out : Except DispatchErr (Option Dispatch))
  ensures out = resolve primary legacy
  -- The two selector arguments are read-only: this query computes the dispatch
  -- decision and mutates nothing (directive 5). They are not declared `mut`.
  do
    -- impl-start
    -- Reject the contradictory both-supplied call; otherwise forward the
    -- coordinate from whichever selector is supplied. When the value comes from
    -- the legacy selector, also raise the one-time advisory; the legacy
    -- selector's value is still forwarded. When neither is supplied there is no
    -- coordinate to forward.
    let res : Except DispatchErr (Option Dispatch) :=
      match primary, legacy with
      | some _, some _ => Except.error .bothSupplied
      | some c, none   => Except.ok (some { forwarded := c, advisory := false })
      | none,   some d => Except.ok (some { forwarded := d, advisory := true })
      | none,   none   => Except.ok none
    return res
    -- impl-end

prove_correct integrateDispatch by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec method integrateDispatch has postcondition `ensures out = resolve primary legacy`, a COMPLETE functional specification: it pins the output exactly, so any impl that verifies must be extensionally equal to `resolve`. This structurally forecloses a verify-but-wrong impl.

Protocol executed. same_spec confirmed True for ALL 8 files (swebench_unified.markers.same_spec, velvet) — impl region is the only edit; axioms/pure/pre/post byte-identical.

Verification (bash scripts/lean_verify.sh <f>), run concurrently in 2 batches of 4:
- atk_1 (prepatch bug: no both-supplied rejection, no advisory; some c,_ forwards advisory=false): EXIT=1, unsolved goals `out = resolve primary legacy`.
- atk_2 (swapped advisory: primary-only advisory=true, legacy-only advisory=false): EXIT=1, unsolved goals.
- atk_3 (partial-domain / accepts contradictory: both-supplied forwards primary instead of Except.error): EXIT=1, unsolved goals.
- atk_4 (control-flow-effect: legacy branch forwards d+1, wrong coordinate): EXIT=1, unsolved goals.
- atk_5 (boundary: none,none yields spurious ok(some {forwarded:=0}) instead of ok none): EXIT=1, unsolved goals.
- atk_6 (over-warn: primary-only advisory=true): EXIT=1, unsolved goals.
- atk_echo (ungrounded-oracle echo: `return resolve primary legacy`): EXIT=0 VERIFIES.
- pos (positive control, exact Solution.lean copy): EXIT=0 VERIFIES.
All six wrong impls fail with genuine `unsolved goals` on the `out = resolve primary legacy` ensures obligation (real spec violations, not syntax/parse errors). prepatch.lean (Solution_prepatch.lean) also fails verification (EXIT=1) as documented — prepatch reproduced.

Mandatory resolve step: atk_echo is the ONLY same-spec impl that verifies. Its faithful refined patch is the gold patch (atk_echo computes exactly `resolve`, so it refines to the patched DataArray.integrate verbatim under the mapping.md bijection — no behavioral divergence). Materialized as atk_echo.patch and RUN through the official harness: `run_resolve('pydata__xarray-3993', patch, timeout=900, retries=1)` (docker, image swebench/sweb.eval.x86_64.pydata_1776_xarray-3993:latest present). Observed: RESOLVED=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS success=[test_integrate[True], test_integrate[False]], failure=[], PASS_TO_PASS all success. So the one verifying same-spec impl's faithful patch RESOLVES — verify⇒correct holds; nothing breaks the spec.

Refinement.md audit (A-legs / model↔patch correspondence): every leg is R / I — A1(R selector↔Option Nat), A2(I+R both-supplied guard↔Except.error), A3(I+R legacy-only forward+FutureWarning↔advisory:=true), A4(I primary-only), A5(R none,none↔forward None→integrator ValueError), A6(I forward to unchanged integrator). NO A-consumed, NO A-reference, NO kind-3 (inexpressible-changed-op) legs. Correspondence is sound: the sole downstream callee (the unchanged trapezoidal integrator) is reached only THROUGH the forwarded selector and observed via that selector (the input carrier), so it is legitimately neither axiomatized nor deep-modeled; the operation that actually changed (argument-resolution head: both-supplied rejection + legacy-only advisory + which value forwarded) is modeled directly and concretely as `resolve`/the match — no trust point hidden behind an axiom. G-AX skip is justified. Dataset.integrate hunk is docstring/type-annotation-only (non-behavioral, carried verbatim for G-RESOLVE) — correctly not modeled.

Conclusion: ≥6 distinct wrong impls (partial-domain, boundary, control-flow-effect, advisory-swap, over-warn, prepatch) all correctly REFUTED by the spec; the ungrounded-oracle echo verifies AND its faithful patch resolves under the executed harness. No verifying wrong impl exists (complete functional postcondition). Spec is SOUND for G-EQ.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled function `resolve` and the real gold-patched `DataArray.integrate` resolution head at base_commit 8cc34cb.

Setup checks: same_spec(Solution.lean, Solution_prepatch.lean)=True (spec regions byte-identical); Solution.lean compiles clean via lean_verify.sh (exit 0); prepatch correctly fails the legacy-only advisory branch (G-DIFF intact).

The frozen spec pins `out = resolve primary legacy` (an exact equality — a uniquely-determined dispatch, not a loose relation). The four `resolve` cases map exactly onto the gold patch's two `if` guards over `dataarray.py:integrate`:
  * (some,some) -> error .bothSupplied  ==  `if dim is not None and coord is not None: raise ValueError("Cannot pass both...")`
  * (none, some d) -> ok {forwarded:=d, advisory:=true}  ==  `if dim is not None and coord is None: coord=dim; warnings.warn(FutureWarning)`
  * (some c, none) -> ok {forwarded:=c, advisory:=false}  ==  neither guard fires; forward coord verbatim, no warning
  * (none, none) -> ok none  ==  neither guard fires; coord stays None and is forwarded to the UNCHANGED downstream integrator (which then raises "Coordinate None does not exist") — this raise is outside the modeled resolution-head boundary and is handled by the G-CONF bijection (forwarding None to the same real integrator on both legs).

The Selector = Option Nat carrier faithfully models the real head's tests, which are exactly `coord is not None` / `dim is not None` (is-not-None, NOT truthiness). Exhaustive comparison of gold dispatch vs resolve over the input product {None,'x','x2',0,''}^2 (including falsy-but-supplied 0 and '') yielded 0 divergences on the observable projection (err? / forwarded / advisory). Sequence selectors forward verbatim and never change the dispatch decision, so the Nat-tag abstraction is neither too strong nor lossy in a way that drifts.

The (none,none)->ok none modeling is a legitimate boundary of the modeled function (the resolution head itself does not raise for that case; the downstream unchanged callee does), not spec-too-strong drift. No input exists where the modeled function disagrees with the real callee. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: pydata__xarray-3993 velvet. same_spec(Solution.lean, Solution_prepatch.lean)=True (verified via swebench_unified.markers.same_spec). Mechanical G-LEAK screen (leakage.screen) passes with zero hard failures. Independent leakage judgment beyond the lexical screen:

PUBLIC problem_statement already discloses: DataArray.integrate uses `dim` while Dataset.integrate uses `coord`; that it should be `coord`; and EXPLICITLY poses 'The only question is whether it requires a deprecation cycle?'. The changed def-symbols in the gold patch (`integrate`, `differentiate`) are BOTH already named in the public problem_statement, so no L2/L5 symbol-collision leak arises.

GOLD-EDIT discriminating content (reject both-supplied via ValueError; accept legacy `dim` but emit FutureWarning; primary `coord` → no warning; forward chosen coord to unchanged integrator; removal in 0.19.0) is expressed in the spec view ONLY through fully abstracted carriers: `primary`/`legacy` selectors (not coord/dim), `Selector = Option Nat`, `Dispatch.advisory : Bool` (not FutureWarning), `DispatchErr.bothSupplied` (not the ValueError string). The spec view contains NO repo-specific tokens — no `dim`, `coord`, `FutureWarning`, `ValueError`, `warnings.warn`, `0.19.0`, warning-message text, file path, module path, or diff marker. No gold-patch line is reproduced; no bug/fix narration.

The spec necessarily encodes the intended post-fix behavior, and here it resolves the deprecation-cycle question that the problem_statement ITSELF poses publicly, using the canonical deprecate-with-warning + reject-conflicting-args design — expressed in abstract vocabulary that does not reveal any edit detail not already public. hints_text (max-sixty PR reference) is not echoed. Solution.lean lean_verify/spec content examined; verdict view is audit-only (refinement.md/mapping.md are NOT part of the consumer spec view and are not screened). Conclusion: no leakage of the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-12125

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec impl that VERIFIES has a faithful refined patch that fails to resolve. The only verifying same-spec attacks are (a) the ungrounded-oracle echo atk_5 (returns renderRef t; its faithful patch is the gold patch verbatim, which RESOLVED=True) and (b) the divergence artifact atk_6 (see notes), whose degenerate infinite-loop patch does not COMPLETE a resolve (timeout, not a clean non-resolve) and is not a refinement-fidelity counterexample.
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
 -- (No axiomatized callees. Building the code reference for a type value is a
@@ -93,10 +93,6 @@
             out = { expr := t.bare, imp := none }
   do
     -- impl-start
-    -- Dispatch in priority order; build and return the reference for the first
-    -- matching kind. A general value is named by its module joined to its full
-    -- within-module location (the location that keeps every enclosing scope),
-    -- and imports that module.
     if t.isSentinelBase then
       return { expr := "models.Model".toList, imp := none }
     else
@@ -106,7 +102,7 @@
         if t.isBuiltin then
           return { expr := t.bare, imp := none }
         else
-          return { expr := t.module ++ ['.'] ++ t.qualified,
+          return { expr := t.module ++ ['.'] ++ t.bare,
                    imp := some ("import ".toList ++ t.module) }
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
 -- (No axiomatized callees. Building the code reference for a type value is a
@@ -93,10 +93,6 @@
             out = { expr := t.bare, imp := none }
   do
     -- impl-start
-    -- Dispatch in priority order; build and return the reference for the first
-    -- matching kind. A general value is named by its module joined to its full
-    -- within-module location (the location that keeps every enclosing scope),
-    -- and imports that module.
     if t.isSentinelBase then
       return { expr := "models.Model".toList, imp := none }
     else
@@ -104,7 +100,7 @@
         return { expr := "type(None)".toList, imp := none }
       else
         if t.isBuiltin then
-          return { expr := t.bare, imp := none }
+          return { expr := t.qualified, imp := none }
         else
           return { expr := t.module ++ ['.'] ++ t.qualified,
                    imp := some ("import ".toList ++ t.module) }
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
 -- (No axiomatized callees. Building the code reference for a type value is a
@@ -93,21 +93,13 @@
             out = { expr := t.bare, imp := none }
   do
     -- impl-start
-    -- Dispatch in priority order; build and return the reference for the first
-    -- matching kind. A general value is named by its module joined to its full
-    -- within-module location (the location that keeps every enclosing scope),
-    -- and imports that module.
     if t.isSentinelBase then
       return { expr := "models.Model".toList, imp := none }
     else
       if t.isNoneType then
         return { expr := "type(None)".toList, imp := none }
       else
-        if t.isBuiltin then
-          return { expr := t.bare, imp := none }
-        else
-          return { expr := t.module ++ ['.'] ++ t.qualified,
-                   imp := some ("import ".toList ++ t.module) }
+        return { expr := "models.Model".toList, imp := none }
     -- impl-end
 
 prove_correct typeReference by
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
 -- (No axiomatized callees. Building the code reference for a type value is a
@@ -93,18 +93,14 @@
             out = { expr := t.bare, imp := none }
   do
     -- impl-start
-    -- Dispatch in priority order; build and return the reference for the first
-    -- matching kind. A general value is named by its module joined to its full
-    -- within-module location (the location that keeps every enclosing scope),
-    -- and imports that module.
-    if t.isSentinelBase then
-      return { expr := "models.Model".toList, imp := none }
+    if t.isBuiltin then
+      return { expr := t.bare, imp := none }
     else
-      if t.isNoneType then
-        return { expr := "type(None)".toList, imp := none }
+      if t.isSentinelBase then
+        return { expr := "models.Model".toList, imp := none }
       else
-        if t.isBuiltin then
-          return { expr := t.bare, imp := none }
+        if t.isNoneType then
+          return { expr := "type(None)".toList, imp := none }
         else
           return { expr := t.module ++ ['.'] ++ t.qualified,
                    imp := some ("import ".toList ++ t.module) }
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. Building the code reference for a type value is a
@@ -93,21 +93,7 @@
             out = { expr := t.bare, imp := none }
   do
     -- impl-start
-    -- Dispatch in priority order; build and return the reference for the first
-    -- matching kind. A general value is named by its module joined to its full
-    -- within-module location (the location that keeps every enclosing scope),
-    -- and imports that module.
-    if t.isSentinelBase then
-      return { expr := "models.Model".toList, imp := none }
-    else
-      if t.isNoneType then
-        return { expr := "type(None)".toList, imp := none }
-      else
-        if t.isBuiltin then
-          return { expr := t.bare, imp := none }
-        else
-          return { expr := t.module ++ ['.'] ++ t.qualified,
-                   imp := some ("import ".toList ++ t.module) }
+    return renderRef t
     -- impl-end
 
 prove_correct typeReference by
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
 -- (No axiomatized callees. Building the code reference for a type value is a
@@ -93,12 +93,8 @@
             out = { expr := t.bare, imp := none }
   do
     -- impl-start
-    -- Dispatch in priority order; build and return the reference for the first
-    -- matching kind. A general value is named by its module joined to its full
-    -- within-module location (the location that keeps every enclosing scope),
-    -- and imports that module.
     if t.isSentinelBase then
-      return { expr := "models.Model".toList, imp := none }
+      return { expr := "models.Models".toList, imp := none }
     else
       if t.isNoneType then
         return { expr := "type(None)".toList, imp := none }
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
 -- (No axiomatized callees. Building the code reference for a type value is a
@@ -93,10 +93,6 @@
             out = { expr := t.bare, imp := none }
   do
     -- impl-start
-    -- Dispatch in priority order; build and return the reference for the first
-    -- matching kind. A general value is named by its module joined to its full
-    -- within-module location (the location that keeps every enclosing scope),
-    -- and imports that module.
     if t.isSentinelBase then
       return { expr := "models.Model".toList, imp := none }
     else
@@ -107,7 +103,7 @@
           return { expr := t.bare, imp := none }
         else
           return { expr := t.module ++ ['.'] ++ t.qualified,
-                   imp := some ("import ".toList ++ t.module) }
+                   imp := none }
     -- impl-end
 
 prove_correct typeReference by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Building the code reference for a type value is a
--  pure straight-line dispatch over a handful of facts read off the value; it
--  calls nothing it does not itself compute. The selected name is modeled
--  DEEPLY in the `pure` region, so there is no consumed axiom and no A-reference
--  deep model of an outside callee. Nothing here is axiomatized.)
-- axioms-end

-- pure-start
/- The facts a type value exposes that the reference computation reacts to.
   Only these are observable to the computation (mapping.md §2):
     * `isSentinelBase` — the value is the framework's base model type, which has
                          one canonical spelling;
     * `isNoneType`     — the value is the type of the absent value, also with one
                          canonical spelling;
     * `isBuiltin`      — the value lives in the language's built-in namespace, so
                          it needs no module prefix and no import;
     * `module`         — the dotted name of the module the value lives in;
     * `qualified`      — the value's location WITHIN its module, INCLUDING every
                          enclosing scope it is nested in (so a value defined
                          inside another is spelled enclosing-then-inner);
     * `bare`           — the value's own name, WITHOUT any enclosing scope. -/
structure TypeValue where
  isSentinelBase : Bool
  isNoneType : Bool
  isBuiltin : Bool
  module : List Char
  qualified : List Char
  bare : List Char
deriving Inhabited, DecidableEq

/- A rendered code reference: the source-text expression that names the value,
   together with the import line needed to make that expression resolve
   (`none` when no import is needed). -/
structure Rendered where
  expr : List Char
  imp : Option (List Char)
deriving Inhabited, DecidableEq

/- The reference for a type value, spelled out. In priority order:
     * the base model type renders to its one canonical spelling, no import;
     * the absent-value type renders to its one canonical spelling, no import;
     * a built-in renders to its own bare name, no module prefix, no import;
     * anything else renders to its module followed by its FULL within-module
       location — the location that includes every enclosing scope, so a value
       nested inside another resolves to the enclosing-then-inner path — and
       carries an import of its module. -/
def renderRef (t : TypeValue) : Rendered :=
  if t.isSentinelBase then
    { expr := "models.Model".toList, imp := none }
  else if t.isNoneType then
    { expr := "type(None)".toList, imp := none }
  else if t.isBuiltin then
    { expr := t.bare, imp := none }
  else
    { expr := t.module ++ ['.'] ++ t.qualified,
      imp := some ("import ".toList ++ t.module) }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the code reference (expression + needed import) for a type value.

   The value is read-only (not `mut`): the computation inspects it and builds a
   fresh reference, mutating nothing (directive 5). The result is pinned exactly:
   the two sentinel types and the built-in case have set spellings with no
   import; every other value is named by its module plus its FULL within-module
   location and imports that module. Crucially, that location is the one that
   includes every enclosing scope (`qualified`) — so a value nested inside another
   resolves to the enclosing-then-inner path, not to a same-named top-level value
   (`bare`). -/
method typeReference (t : TypeValue) return (out : Rendered)
  ensures out = renderRef t
  -- General (non-sentinel, non-builtin) values: named by module + FULL location,
  -- including any enclosing scope; the import is that module.
  ensures (¬ t.isSentinelBase ∧ ¬ t.isNoneType ∧ ¬ t.isBuiltin) →
            out = { expr := t.module ++ ['.'] ++ t.qualified,
                    imp := some ("import ".toList ++ t.module) }
  -- Built-ins: bare name, no import.
  ensures (¬ t.isSentinelBase ∧ ¬ t.isNoneType ∧ t.isBuiltin) →
            out = { expr := t.bare, imp := none }
  do
    -- impl-start
    -- Dispatch in priority order; build and return the reference for the first
    -- matching kind. A general value is named by its module joined to its full
    -- within-module location (the location that keeps every enclosing scope),
    -- and imports that module.
    if t.isSentinelBase then
      return { expr := "models.Model".toList, imp := none }
    else
      if t.isNoneType then
        return { expr := "type(None)".toList, imp := none }
      else
        if t.isBuiltin then
          return { expr := t.bare, imp := none }
        else
          return { expr := t.module ++ ['.'] ++ t.qualified,
                   imp := some ("import ".toList ++ t.module) }
    -- impl-end

prove_correct typeReference by
  loom_solve <;> simp_all [renderRef]
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** `ensures out = renderRef t` fully pins the output to a single value per input; renderRef is a total, deterministic if-else deep model, byte-frozen in the pure region. The two extra implication-ensures are redundant. There are NO axioms/opaque decls: refinement.md legs A1(R str<->List Char), A2/A3/A4/A5(I) are all R/I, no A-consumed / A-reference / kind-3 leg exists; G-AX legitimately skips (verified: `grep -nE '^\s*(axiom|opaque)' Solution.lean` -> none). refinement.md/mapping.md model↔patch correspondence checked: A5 (`t.module ++ ['.'] ++ t.qualified`, `some import module`) is exactly the patched line `"%s.%s" % (module, self.value.__qualname__), {"import %s" % module}`; qualified<->`__qualname__` (full within-scope location), bare<->`__name__`. Correct.

PROTOCOL RUN (all; same_spec=True for ALL 8 attacks + control + prepatch, checked via swebench_unified.markers.same_spec; verify via `bash scripts/lean_verify.sh <f>`, run ≤4 concurrently):
- pos_control.lean (== gold Solution.lean byte-identical): EXIT 0 (VERIFIES) — non-vacuity control.
- prepatch.lean (Solution_prepatch.lean, general branch uses t.bare): EXIT 1, unsolved goal `⊢ t.bare = t.qualified` — PREPATCH BUG REPRODUCED.
- atk_1 prepatch-bug re-encode (general branch t.bare): EXIT 1 `⊢ t.bare = t.qualified` — rejected.
- atk_2 boundary/swap (builtin branch returns t.qualified): EXIT 1 `⊢ t.qualified = t.bare` — rejected.
- atk_3 partial-domain (general branch collapsed to "models.Model" literal): EXIT 1 — rejected.
- atk_4 control-flow-effect (isBuiltin checked BEFORE the two sentinels): EXIT 1 `⊢ False` — rejected.
- atk_5 ungrounded-oracle echo (`return renderRef t`): EXIT 0 (VERIFIES). Faithful patch = gold patch.diff verbatim. RAN via harness.run_resolve('django__django-12125', gold, timeout=1800) -> RESOLVED=True COMPLETED=True. => correct echo of the gold, NOT a spec weakness (per build_one.py:314 policy).
- atk_7 wrong literal ("models.Models" typo in sentinel branch): EXIT 1 `⊢ False` — rejected.
- atk_8 dropped import (general branch imp := none): EXIT 1 `⊢ False` — rejected.

DIVERGENCE VECTOR (atk_6, atk_6.lean — NOT listed in attacks[] because it is not a refinement-fidelity counterexample): impl = `let mut i := 0; while true invariant True done_with False do i := i+1; return {models.Model,none}`. lean_verify EXIT 0 — it VERIFIES vacuously under the frozen `set_option loom.semantics.termination "partial"` (partial correctness: a non-terminating method satisfies any postcondition).

I materialized its FAITHFUL refined patch (atk_6_patch.diff: inserts `_sbu_i=0; while True: _sbu_i += 1` at the top of TypeSerializer.serialize, git-diff'd against base_commit 89d41cba so it applies cleanly) and RAN it through the official harness TWICE: run_resolve('django__django-12125', atk_6_patch, timeout=900 then 600, retries=1) -> BOTH runs: RESOLVED=False, COMPLETED=False, NOTE='no report ... harness error' (the infinite loop hangs the F2P tests; the harness times out and produces no gradable report). Per the official derivation build_one.py:306 vs :310, COMPLETED=False is an INCONCLUSIVE hit, NOT the `completed ∧ ¬resolved` that defines a clean BROKEN.

Crucially, atk_6 is a UNIVERSAL partial-semantics artifact, not a defect of THIS spec: I confirmed the identical `while true` construction VERIFIES against an unrelated bundle too (univ_div.lean, django__django-10554, EXIT 0). Divergence is also not one of the enumerated refinement-fidelity attack classes and has no faithful image in mapping.md's total, straight-line string-construction refinement (there is no real-code counterpart to a non-terminating pure serializer). It is therefore excluded from the mechanized counterexample set and reported here transparently with its executed resolve result.

**VERDICT:** SOUND. Value surface is TIGHT — 6 distinct value-class wrong impls (prepatch-bare, builtin/qualified swap, partial-domain collapse, control-flow reorder, wrong literal, dropped import) are ALL rejected; positive control verifies; prepatch bug reproduced; the one non-echo verifying impl is the universal divergence artifact whose degenerate patch times out (inconclusive, not a clean non-resolve) and is not a faithful refinement counterexample. No verifying wrong impl has a faithful refined patch that COMPLETES and does NOT resolve. verify⇒correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec impl that VERIFIES has a faithful refined patch that fails to resolve. The only verifying same-spec attacks are (a) the ungrounded-oracle echo atk_5 (returns renderRef t; its faithful patch is the gold patch verbatim, which RESOLVED=True) and (b) the divergence artifact atk_6 (see notes), whose degenerate infinite-loop patch does not COMPLETE a resolve (timeout, not a clean non-resolve) and is not a refinement-fidelity counterexample.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Building the code reference for a type value is a
--  pure straight-line dispatch over a handful of facts read off the value; it
--  calls nothing it does not itself compute. The selected name is modeled
--  DEEPLY in the `pure` region, so there is no consumed axiom and no A-reference
--  deep model of an outside callee. Nothing here is axiomatized.)
-- axioms-end

-- pure-start
/- The facts a type value exposes that the reference computation reacts to.
   Only these are observable to the computation (mapping.md §2):
     * `isSentinelBase` — the value is the framework's base model type, which has
                          one canonical spelling;
     * `isNoneType`     — the value is the type of the absent value, also with one
                          canonical spelling;
     * `isBuiltin`      — the value lives in the language's built-in namespace, so
                          it needs no module prefix and no import;
     * `module`         — the dotted name of the module the value lives in;
     * `qualified`      — the value's location WITHIN its module, INCLUDING every
                          enclosing scope it is nested in (so a value defined
                          inside another is spelled enclosing-then-inner);
     * `bare`           — the value's own name, WITHOUT any enclosing scope. -/
structure TypeValue where
  isSentinelBase : Bool
  isNoneType : Bool
  isBuiltin : Bool
  module : List Char
  qualified : List Char
  bare : List Char
deriving Inhabited, DecidableEq

/- A rendered code reference: the source-text expression that names the value,
   together with the import line needed to make that expression resolve
   (`none` when no import is needed). -/
structure Rendered where
  expr : List Char
  imp : Option (List Char)
deriving Inhabited, DecidableEq

/- The reference for a type value, spelled out. In priority order:
     * the base model type renders to its one canonical spelling, no import;
     * the absent-value type renders to its one canonical spelling, no import;
     * a built-in renders to its own bare name, no module prefix, no import;
     * anything else renders to its module followed by its FULL within-module
       location — the location that includes every enclosing scope, so a value
       nested inside another resolves to the enclosing-then-inner path — and
       carries an import of its module. -/
def renderRef (t : TypeValue) : Rendered :=
  if t.isSentinelBase then
    { expr := "models.Model".toList, imp := none }
  else if t.isNoneType then
    { expr := "type(None)".toList, imp := none }
  else if t.isBuiltin then
    { expr := t.bare, imp := none }
  else
    { expr := t.module ++ ['.'] ++ t.qualified,
      imp := some ("import ".toList ++ t.module) }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the code reference (expression + needed import) for a type value.

   The value is read-only (not `mut`): the computation inspects it and builds a
   fresh reference, mutating nothing (directive 5). The result is pinned exactly:
   the two sentinel types and the built-in case have set spellings with no
   import; every other value is named by its module plus its FULL within-module
   location and imports that module. Crucially, that location is the one that
   includes every enclosing scope (`qualified`) — so a value nested inside another
   resolves to the enclosing-then-inner path, not to a same-named top-level value
   (`bare`). -/
method typeReference (t : TypeValue) return (out : Rendered)
  ensures out = renderRef t
  -- General (non-sentinel, non-builtin) values: named by module + FULL location,
  -- including any enclosing scope; the import is that module.
  ensures (¬ t.isSentinelBase ∧ ¬ t.isNoneType ∧ ¬ t.isBuiltin) →
            out = { expr := t.module ++ ['.'] ++ t.qualified,
                    imp := some ("import ".toList ++ t.module) }
  -- Built-ins: bare name, no import.
  ensures (¬ t.isSentinelBase ∧ ¬ t.isNoneType ∧ t.isBuiltin) →
            out = { expr := t.bare, imp := none }
  do
    -- impl-start
    -- Dispatch in priority order; build and return the reference for the first
    -- matching kind. A general value is named by its module joined to its full
    -- within-module location (the location that keeps every enclosing scope),
    -- and imports that module.
    if t.isSentinelBase then
      return { expr := "models.Model".toList, imp := none }
    else
      if t.isNoneType then
        return { expr := "type(None)".toList, imp := none }
      else
        if t.isBuiltin then
          return { expr := t.bare, imp := none }
        else
          return { expr := t.module ++ ['.'] ++ t.qualified,
                   imp := some ("import ".toList ++ t.module) }
    -- impl-end

prove_correct typeReference by
  loom_solve <;> simp_all [renderRef]
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** `ensures out = renderRef t` fully pins the output to a single value per input; renderRef is a total, deterministic if-else deep model, byte-frozen in the pure region. The two extra implication-ensures are redundant. There are NO axioms/opaque decls: refinement.md legs A1(R str<->List Char), A2/A3/A4/A5(I) are all R/I, no A-consumed / A-reference / kind-3 leg exists; G-AX legitimately skips (verified: `grep -nE '^\s*(axiom|opaque)' Solution.lean` -> none). refinement.md/mapping.md model↔patch correspondence checked: A5 (`t.module ++ ['.'] ++ t.qualified`, `some import module`) is exactly the patched line `"%s.%s" % (module, self.value.__qualname__), {"import %s" % module}`; qualified<->`__qualname__` (full within-scope location), bare<->`__name__`. Correct.

PROTOCOL RUN (all; same_spec=True for ALL 8 attacks + control + prepatch, checked via swebench_unified.markers.same_spec; verify via `bash scripts/lean_verify.sh <f>`, run ≤4 concurrently):
- pos_control.lean (== gold Solution.lean byte-identical): EXIT 0 (VERIFIES) — non-vacuity control.
- prepatch.lean (Solution_prepatch.lean, general branch uses t.bare): EXIT 1, unsolved goal `⊢ t.bare = t.qualified` — PREPATCH BUG REPRODUCED.
- atk_1 prepatch-bug re-encode (general branch t.bare): EXIT 1 `⊢ t.bare = t.qualified` — rejected.
- atk_2 boundary/swap (builtin branch returns t.qualified): EXIT 1 `⊢ t.qualified = t.bare` — rejected.
- atk_3 partial-domain (general branch collapsed to "models.Model" literal): EXIT 1 — rejected.
- atk_4 control-flow-effect (isBuiltin checked BEFORE the two sentinels): EXIT 1 `⊢ False` — rejected.
- atk_5 ungrounded-oracle echo (`return renderRef t`): EXIT 0 (VERIFIES). Faithful patch = gold patch.diff verbatim. RAN via harness.run_resolve('django__django-12125', gold, timeout=1800) -> RESOLVED=True COMPLETED=True. => correct echo of the gold, NOT a spec weakness (per build_one.py:314 policy).
- atk_7 wrong literal ("models.Models" typo in sentinel branch): EXIT 1 `⊢ False` — rejected.
- atk_8 dropped import (general branch imp := none): EXIT 1 `⊢ False` — rejected.

DIVERGENCE VECTOR (atk_6, atk_6.lean — NOT listed in attacks[] because it is not a refinement-fidelity counterexample): impl = `let mut i := 0; while true invariant True done_with False do i := i+1; return {models.Model,none}`. lean_verify EXIT 0 — it VERIFIES vacuously under the frozen `set_option loom.semantics.termination "partial"` (partial correctness: a non-terminating method satisfies any postcondition).

I materialized its FAITHFUL refined patch (atk_6_patch.diff: inserts `_sbu_i=0; while True: _sbu_i += 1` at the top of TypeSerializer.serialize, git-diff'd against base_commit 89d41cba so it applies cleanly) and RAN it through the official harness TWICE: run_resolve('django__django-12125', atk_6_patch, timeout=900 then 600, retries=1) -> BOTH runs: RESOLVED=False, COMPLETED=False, NOTE='no report ... harness error' (the infinite loop hangs the F2P tests; the harness times out and produces no gradable report). Per the official derivation build_one.py:306 vs :310, COMPLETED=False is an INCONCLUSIVE hit, NOT the `completed ∧ ¬resolved` that defines a clean BROKEN.

Crucially, atk_6 is a UNIVERSAL partial-semantics artifact, not a defect of THIS spec: I confirmed the identical `while true` construction VERIFIES against an unrelated bundle too (univ_div.lean, django__django-10554, EXIT 0). Divergence is also not one of the enumerated refinement-fidelity attack classes and has no faithful image in mapping.md's total, straight-line string-construction refinement (there is no real-code counterpart to a non-terminating pure serializer). It is therefore excluded from the mechanized counterexample set and reported here transparently with its executed resolve result.

**VERDICT:** SOUND. Value surface is TIGHT — 6 distinct value-class wrong impls (prepatch-bare, builtin/qualified swap, partial-domain collapse, control-flow reorder, wrong literal, dropped import) are ALL rejected; positive control verifies; prepatch bug reproduced; the one non-echo verifying impl is the universal divergence artifact whose degenerate patch times out (inconclusive, not a clean non-resolve) and is not a faithful refinement counterexample. No verifying wrong impl has a faithful refined patch that COMPLETES and does NOT resolve. verify⇒correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift check for django__django-12125 (velvet). The gold patch changes django/db/migrations/serializer.py:272 in TypeSerializer.serialize from `__name__` -> `__qualname__` (confirmed: base_commit 89d41cba shows `%s.%s % (module, self.value.__name__)`; patch selects `__qualname__`). The Solution models the POST-patch callee. Checks performed: (1) same_spec(Solution, Solution_prepatch, velvet.language) = True — the spec region (TypeValue/Rendered structures, renderRef, method typeReference ensures clauses) is frozen byte-identical; the only diff is the impl (t.qualified vs t.bare). (2) lean_verify.sh Solution.lean exit 0 (verifies). (3) The modeled function renderRef: sentinelBase -> 'models.Model'/no-import; noneType -> 'type(None)'/no-import; builtin -> bare/no-import; else -> module++'.'++qualified with import module. Bijection (mapping.md §2): qualified<->`__qualname__`, bare<->`__name__`, module<->`__module__`, isBuiltin<->`__module__`==builtins.`__name__`. This exactly mirrors the real patched serialize. (4) Differential test reproduced independently over 100,014 genuine type objects (both sentinels, 7 builtins, top-level class, real nested classes Outer.Inner/Outer.Middle.Deep, plus 100k synthesized types with controlled `__module__`/`__qualname__`/`__name__` across nested & cross-module placements) comparing spec-shadow vs the patched callee: 0 disagreements. Matches recorded G-CONF (100014 objects, seed=12125, 0 disagreements). Edge cases: builtin branch uses `__name__`==bare (agree); sentinel identity priority cannot collide; nested-class F2P case correctly selects qualified; hasattr(`__module__`) guard is always true of real type objects so the spec's totality introduces no reachable divergence. No input found where the spec disagrees with the real patched repo behavior. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: self.value.`__name__` -> self.value.`__qualname__` in TypeSerializer.serialize's general (non-sentinel, non-builtin) branch, so a nested/inner class serializes to its enclosing-qualified path (module.Outer.Inner) instead of a bare top-level path (module.Inner).

Spec-region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean) == True (velvet LanguageTables). Verified independently.

Mechanical G-LEAK screen over the spec view: PASSES (0 hard failures). No diff markers, no gold-patch line reproduced, no patched file/module path (django/db/migrations/serializer.py absent), the sole distinctive changed symbol 'serialize' is not echoed by any spec-view identifier, and no narration tokens.

The discriminator the spec view encodes is that the general branch renders 'module ++ [.] ++ t.qualified' where the docstring contrasts `qualified` ('the value's location WITHIN its module, INCLUDING every enclosing scope', 'enclosing-then-inner path') against `bare` ('without any enclosing scope', 'same-named top-level value'). This behavior is FULLY PUBLIC in problem_statement (hints excluded): the PS shows the inner class rendered as `test1.models.Inner` 'as if it were a top-level class of the module', states it 'should have been test1.models.Outer.Inner', and repeatedly uses 'inner class' / 'top-level class' and shows `Outer.Inner`. The spec view is a de-narrated restatement of that public issue text, not a leak beyond problem_statement.

Hints-only tokens (`__qualname__`, `__name__`, TypeSerializer, serializer, EnumField, builtins) do NOT appear anywhere in the spec view. The special-case branches (models.Model, type(None), builtin bare-name) describe unchanged surrounding dispatch structure, not the edit. models.Model itself appears in the public PS.

No LEAKAGE line exists to quote; no RELAXED_LEAKAGE deferral needed since the discriminator is already in the public statement.

**Gold edit:** self.value.`__name__` -> self.value.`__qualname__` in TypeSerializer.serialize's general (non-sentinel, non-builtin) branch, so a nested/inner class serializes to its enclosing-qualified path (module.Outer.Inner) instead of a bare top-level path (module.Inner).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
# P2 adversarial audit — sphinx-doc__sphinx-7910

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
| does not verify against this specification, so the specification excludes it | 9 | listed per attack in the audit record below |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None that breaks the spec. The ONLY same-spec impl that verifies is a DIVERGENCE artifact (atk_9_diverge_loop.lean: `while true do pure (); return Decision.forceInclude`), which verifies vacuously under `loom.semantics.termination "partial"` because the wrong return is unreachable. Its faithful refined patch (an unconditional `while True: pass` at the top of `_skip_member`, plus the gold `inspect.unwrap` swap) was materialized (atk_9_patch.diff; git apply --check CLEAN) and RUN through the official harness TWICE (run_resolve, run_id sbu-audit-atk9-diverge / sbu-audit-atk9-diverge2, timeout 600s then 900s, retries=0). BOTH runs returned completed=False, resolved=False (the harness raises EvaluationError on the hung test BEFORE writing report.json, so no verdict is produced). Per _derive_audit_verdict this is an INCONCLUSIVE resolve (line 310: `if not r.completed`), NOT a break — BROKEN requires `r.completed and not r.resolved` (line 306). Divergence is thus definitionally excluded from verify⇏correct under this harness, and is the documented accepted non-defect (build_one.py:225 'only divergence is on an unreachable input'). No TERMINATING wrong impl verifies.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Decide, for one documentable target, whether the documentation builder is told
    to FORCE its inclusion or to leave the default disposition untouched.
@@ -160,14 +160,11 @@
   ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
   do
     -- impl-start
+
     if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
-      -- Ownership for a bodied context is settled against the scope where the
-      -- target is genuinely DEFINED — its resolved scope, which sees through any
-      -- wrapper standing in for the underlying object. A whole-unit context needs
-      -- no owner.
       let owner := match ctx with
-        | Context.classBody     => ownerIn target target.resolvedScope
-        | Context.exceptionBody => ownerIn target target.resolvedScope
+        | Context.classBody     => ownerIn target target.directScope
+        | Context.exceptionBody => ownerIn target target.directScope
         | _                     => false
       if (ctx == Context.wholeUnit) || owner then
         if categoryEnabled name incInit incSpecial incPrivate then
```

Attack 2 — `atk_2_trivial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Decide, for one documentable target, whether the documentation builder is told
    to FORCE its inclusion or to leave the default disposition untouched.
@@ -160,24 +160,8 @@
   ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
   do
     -- impl-start
-    if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
-      -- Ownership for a bodied context is settled against the scope where the
-      -- target is genuinely DEFINED — its resolved scope, which sees through any
-      -- wrapper standing in for the underlying object. A whole-unit context needs
-      -- no owner.
-      let owner := match ctx with
-        | Context.classBody     => ownerIn target target.resolvedScope
-        | Context.exceptionBody => ownerIn target target.resolvedScope
-        | _                     => false
-      if (ctx == Context.wholeUnit) || owner then
-        if categoryEnabled name incInit incSpecial incPrivate then
-          return Decision.forceInclude
-        else
-          return Decision.noOverride
-      else
-        return Decision.noOverride
-    else
-      return Decision.noOverride
+
+    return Decision.noOverride
     -- impl-end
 
 prove_correct inclusionDecisionM by
```

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Decide, for one documentable target, whether the documentation builder is told
    to FORCE its inclusion or to leave the default disposition untouched.
@@ -160,14 +160,11 @@
   ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
   do
     -- impl-start
+
     if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
-      -- Ownership for a bodied context is settled against the scope where the
-      -- target is genuinely DEFINED — its resolved scope, which sees through any
-      -- wrapper standing in for the underlying object. A whole-unit context needs
-      -- no owner.
       let owner := match ctx with
         | Context.classBody     => ownerIn target target.resolvedScope
-        | Context.exceptionBody => ownerIn target target.resolvedScope
+        | Context.exceptionBody => ownerIn target target.directScope
         | _                     => false
       if (ctx == Context.wholeUnit) || owner then
         if categoryEnabled name incInit incSpecial incPrivate then
```

Attack 4 — `atk_4_ctrlflow.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Decide, for one documentable target, whether the documentation builder is told
    to FORCE its inclusion or to leave the default disposition untouched.
@@ -160,16 +160,13 @@
   ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
   do
     -- impl-start
+
     if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
-      -- Ownership for a bodied context is settled against the scope where the
-      -- target is genuinely DEFINED — its resolved scope, which sees through any
-      -- wrapper standing in for the underlying object. A whole-unit context needs
-      -- no owner.
       let owner := match ctx with
         | Context.classBody     => ownerIn target target.resolvedScope
         | Context.exceptionBody => ownerIn target target.resolvedScope
         | _                     => false
-      if (ctx == Context.wholeUnit) || owner then
+      if owner then
         if categoryEnabled name incInit incSpecial incPrivate then
           return Decision.forceInclude
         else
```

Attack 5 — `atk_6_catswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Decide, for one documentable target, whether the documentation builder is told
    to FORCE its inclusion or to leave the default disposition untouched.
@@ -160,17 +160,14 @@
   ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
   do
     -- impl-start
+
     if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
-      -- Ownership for a bodied context is settled against the scope where the
-      -- target is genuinely DEFINED — its resolved scope, which sees through any
-      -- wrapper standing in for the underlying object. A whole-unit context needs
-      -- no owner.
       let owner := match ctx with
         | Context.classBody     => ownerIn target target.resolvedScope
         | Context.exceptionBody => ownerIn target target.resolvedScope
         | _                     => false
       if (ctx == Context.wholeUnit) || owner then
-        if categoryEnabled name incInit incSpecial incPrivate then
+        if categoryEnabled name incInit incPrivate incSpecial then
           return Decision.forceInclude
         else
           return Decision.noOverride
```

Attack 6 — `atk_7_noweakref.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Decide, for one documentable target, whether the documentation builder is told
    to FORCE its inclusion or to leave the default disposition untouched.
@@ -160,11 +160,8 @@
   ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
   do
     -- impl-start
-    if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
-      -- Ownership for a bodied context is settled against the scope where the
-      -- target is genuinely DEFINED — its resolved scope, which sees through any
-      -- wrapper standing in for the underlying object. A whole-unit context needs
-      -- no owner.
+
+    if target.hasDoc && isConsidered ctx then
       let owner := match ctx with
         | Context.classBody     => ownerIn target target.resolvedScope
         | Context.exceptionBody => ownerIn target target.resolvedScope
```

Attack 7 — `atk_8_diverge_while.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Decide, for one documentable target, whether the documentation builder is told
    to FORCE its inclusion or to leave the default disposition untouched.
@@ -160,24 +160,11 @@
   ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
   do
     -- impl-start
-    if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
-      -- Ownership for a bodied context is settled against the scope where the
-      -- target is genuinely DEFINED — its resolved scope, which sees through any
-      -- wrapper standing in for the underlying object. A whole-unit context needs
-      -- no owner.
-      let owner := match ctx with
-        | Context.classBody     => ownerIn target target.resolvedScope
-        | Context.exceptionBody => ownerIn target target.resolvedScope
-        | _                     => false
-      if (ctx == Context.wholeUnit) || owner then
-        if categoryEnabled name incInit incSpecial incPrivate then
-          return Decision.forceInclude
-        else
-          return Decision.noOverride
-      else
-        return Decision.noOverride
-    else
-      return Decision.noOverride
+
+    let mut b := true
+    while b do
+      b := true
+    return Decision.forceInclude
     -- impl-end
 
 prove_correct inclusionDecisionM by
```

Attack 8 — `atk_10_ownertrue.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Decide, for one documentable target, whether the documentation builder is told
    to FORCE its inclusion or to leave the default disposition untouched.
@@ -160,14 +160,11 @@
   ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
   do
     -- impl-start
+
     if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
-      -- Ownership for a bodied context is settled against the scope where the
-      -- target is genuinely DEFINED — its resolved scope, which sees through any
-      -- wrapper standing in for the underlying object. A whole-unit context needs
-      -- no owner.
       let owner := match ctx with
-        | Context.classBody     => ownerIn target target.resolvedScope
-        | Context.exceptionBody => ownerIn target target.resolvedScope
+        | Context.classBody     => true
+        | Context.exceptionBody => true
         | _                     => false
       if (ctx == Context.wholeUnit) || owner then
         if categoryEnabled name incInit incSpecial incPrivate then
```

Attack 9 — `atk_11_nocat.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Decide, for one documentable target, whether the documentation builder is told
    to FORCE its inclusion or to leave the default disposition untouched.
@@ -160,20 +160,14 @@
   ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
   do
     -- impl-start
+
     if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
-      -- Ownership for a bodied context is settled against the scope where the
-      -- target is genuinely DEFINED — its resolved scope, which sees through any
-      -- wrapper standing in for the underlying object. A whole-unit context needs
-      -- no owner.
       let owner := match ctx with
         | Context.classBody     => ownerIn target target.resolvedScope
         | Context.exceptionBody => ownerIn target target.resolvedScope
         | _                     => false
       if (ctx == Context.wholeUnit) || owner then
-        if categoryEnabled name incInit incSpecial incPrivate then
-          return Decision.forceInclude
-        else
-          return Decision.noOverride
+        return Decision.forceInclude
       else
         return Decision.noOverride
     else
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- Decide, for one documentable target, whether the documentation builder is told
   to FORCE its inclusion or to leave the default disposition untouched.

   A target is considered only when it carries documentation text and it sits in a
   context where an owning container can be established (a class- or
   exception-bodied context, or a whole compilation unit). For the container
   contexts, ownership is settled by looking the container name up in the scope
   where the target is actually DEFINED — which, when the target as presented is a
   thin wrapper standing in for another object, is the scope of that underlying
   object rather than the wrapper's own scope. A whole-unit context establishes
   ownership unconditionally. Once ownership holds, the target's name decides
   whether one of the enabled inclusion categories (initializer / dunder-special /
   single-underscore-private) forces inclusion.

   No surrounding callee is axiomatized: the decision is computed structurally
   from the target's recorded fields (mapping.md §3). -/

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure branch decision over the recorded fields of one documentable target:
   establish whether an owning container exists (by consulting the scope in which
   the target is genuinely defined), and, if so, classify the target's name into
   an inclusion category gated by the enabled flags. Every observable is computed
   structurally from the target record; nothing is borrowed from an oracle, so
   there is no consumed axiom. The container-name resolution and scope membership
   that the surrounding, unchanged machinery performs are supplied to the model as
   the target's recorded flags/scopes and exercised structurally by the executable
   conformance check (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The context a documentable target appears in. Only the first three establish a
   potential owner (a documentation-text-bearing target is considered there); the
   `wholeUnit` context establishes ownership unconditionally, the two bodied
   contexts must locate an owning container, and `freestanding` (a plain
   function/method/attribute) never reaches the inclusion decision. -/
inductive Context where
  | classBody        -- a class body
  | exceptionBody    -- an exception class body
  | wholeUnit        -- a whole compilation unit
  | freestanding     -- function / method / attribute
  deriving DecidableEq, Inhabited, Repr

/- What the builder is told about one target:
   * `forceInclude` — override the default and document this target;
   * `noOverride`   — leave the default disposition in place. -/
inductive Decision where
  | forceInclude
  | noOverride
  deriving DecidableEq, Inhabited, Repr

/- One documentable target as the decision sees it.
   * `hasDoc`           — the target carries documentation text;
   * `qualifiedName`    — its fully-qualified name (container path '.' leaf);
   * `ownerViaPathWalk` — for a multi-segment container path (resolved by walking
       the unit's attribute chain — machinery the change does not touch), whether
       that walk yields a container that owns the target;
   * `directScope`      — the name→ownership scope of the target object exactly as
       presented;
   * `resolvedScope`    — the name→ownership scope of the object the target stands
       for once any wrapping is seen through (equal to `directScope` when the
       target is presented directly). Each scope maps a container name to whether
       looking it up there yields a container that owns the target's leaf name. -/
structure DocTarget where
  hasDoc           : Bool
  qualifiedName    : List Char
  ownerViaPathWalk : Bool
  directScope      : List (List Char × Bool)
  resolvedScope    : List (List Char × Bool)
  deriving Inhabited, Repr

/- The container path of a qualified name: everything before its last '.'
   (empty when the name has no '.'). Mirrors splitting on the final dot. -/
def containerPath (s : List Char) : List Char :=
  match s.reverse.dropWhile (· != '.') with
  | []          => []
  | _ :: rest   => rest.reverse

/- Whether a qualified container path is itself multi-segment (contains a '.'). -/
def isMultiSegment (s : List Char) : Bool := s.contains '.'

/- Look a container name up in a scope: yields whether that lookup resolves to a
   container owning the target's leaf name (false when the name is absent). -/
def scopeOwns (scope : List (List Char × Bool)) (key : List Char) : Bool :=
  (scope.find? (fun kv => kv.1 == key)).elim false (·.2)

/- Establish ownership for a bodied context against a chosen scope: an empty
   container path establishes no owner; a multi-segment path defers to the
   attribute-chain walk; a single-segment path is looked up in `scope`. -/
def ownerIn (t : DocTarget) (scope : List (List Char × Bool)) : Bool :=
  let cp := containerPath t.qualifiedName
  if cp.isEmpty then false
  else if isMultiSegment cp then t.ownerViaPathWalk
  else scopeOwns scope cp

/- The contexts whose documentation-text-bearing targets are considered. -/
def isConsidered : Context → Bool
  | .classBody     => true
  | .exceptionBody => true
  | .wholeUnit     => true
  | .freestanding  => false

/- The leaf is an initializer. -/
def isInit (name : List Char) : Bool := name == "__init__".toList

/- The leaf is a dunder-special (not the initializer; starts and ends with '__'). -/
def isSpecial (name : List Char) : Bool :=
  !isInit name && ("__".toList).isPrefixOf name && ("__".toList).isSuffixOf name

/- The leaf is single-underscore-private (not init, not special, starts with '_'). -/
def isPrivate (name : List Char) : Bool :=
  !isInit name && !isSpecial name && ("_".toList).isPrefixOf name

/- Whether the target's name lands in an enabled inclusion category. -/
def categoryEnabled (name : List Char) (incInit incSpecial incPrivate : Bool) : Bool :=
  (isSpecial name && incSpecial) || (isPrivate name && incPrivate) || (isInit name && incInit)

/- The decision for one target. A target is examined only when it carries
   documentation text, its name is not the weak-reference slot, and its context is
   considered. For the bodied contexts ownership is established against the scope
   in which the target is genuinely defined (`resolvedScope`); a whole-unit context
   needs no owner. With ownership established, an enabled category for the leaf
   forces inclusion; otherwise the default disposition stands. -/
def inclusionDecision (ctx : Context) (name : List Char) (t : DocTarget)
    (incInit incSpecial incPrivate : Bool) : Decision :=
  if (name != "__weakref__".toList) && t.hasDoc && isConsidered ctx then
    let owner := match ctx with
      | .classBody     => ownerIn t t.resolvedScope
      | .exceptionBody => ownerIn t t.resolvedScope
      | _              => false
    if (ctx == Context.wholeUnit) || owner then
      if categoryEnabled name incInit incSpecial incPrivate then Decision.forceInclude
      else Decision.noOverride
    else Decision.noOverride
  else Decision.noOverride
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this bundle models one method)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether to force inclusion of one documentable `target` or to leave the
   default disposition. `ctx` is the context the target appears in; `name` its leaf
   name; the three flags say which inclusion categories are enabled. The target is
   read-only — none of `ctx`, `name`, `target`, or the flags is `mut`; the decision
   reads them and returns a verdict, mutating nothing it is handed (directive 5). -/
method inclusionDecisionM (ctx : Context) (name : List Char) (target : DocTarget)
    (incInit : Bool) (incSpecial : Bool) (incPrivate : Bool) return (out : Decision)
  ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
  do
    -- impl-start
    if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
      -- Ownership for a bodied context is settled against the scope where the
      -- target is genuinely DEFINED — its resolved scope, which sees through any
      -- wrapper standing in for the underlying object. A whole-unit context needs
      -- no owner.
      let owner := match ctx with
        | Context.classBody     => ownerIn target target.resolvedScope
        | Context.exceptionBody => ownerIn target target.resolvedScope
        | _                     => false
      if (ctx == Context.wholeUnit) || owner then
        if categoryEnabled name incInit incSpecial incPrivate then
          return Decision.forceInclude
        else
          return Decision.noOverride
      else
        return Decision.noOverride
    else
      return Decision.noOverride
    -- impl-end

prove_correct inclusionDecisionM by
  loom_solve
  all_goals simp_all [inclusionDecision]
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL COMPLETION (velvet G-EQ, sphinx-doc__sphinx-7910).

SPEC SHAPE. Postcondition is a TOTAL functional equality: `ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate`, where `inclusionDecision` is the fully-transparent pure model in the spec view. Any TERMINATING impl that differs on any input fails verification. The frozen impl region is loop-free (0 loop constructs in the whole file). meta.json: axioms=[], deep_model_references=[] — there are NO A-legs; the entire refinement is R/I, so the A-leg / model↔patch correspondence audit reduces to confirming there is no hidden axiom and no kind-3 leg (confirmed).

PATH incl + elan. Verify cmd: `bash scripts/lean_verify.sh <atk>.lean`. same_spec via swebench_unified.markers.same_spec + get_backend('velvet'). All 11 attack files + pos.lean confirmed same_spec=True.

ATTACK BATTERY (all same_spec=True; verify exit reported). Verifications launched concurrently in background batches of ≤4 (batch1: atk1-4; batch2: atk5-8; batch3: atk9-11).
- atk_1_prepatch (PREPATCH BUG: reads directScope not resolvedScope for bodied ctx) → exit 1 REJECTED. Byte-identical in behavior to Solution_prepatch.lean; fails on exactly the directScope-vs-resolvedScope ownership clause. prepatch_reproduced=True.
- atk_2_trivial (partial-domain: always noOverride) → exit 1 REJECTED.
- atk_3_boundary (exceptionBody uses directScope, classBody correct) → exit 1 REJECTED.
- atk_4_ctrlflow (drop the wholeUnit-unconditional-owner rule; require owner) → exit 1 REJECTED.
- atk_5_echo (logically-equivalent boolean reordering of gold) → exit 1 REJECTED (fails on prove_correct tactic brittleness, not a semantic pass; NOT submitted as a floor attack).
- atk_6_catswap (swap incSpecial/incPrivate flags in categoryEnabled) → exit 1 REJECTED.
- atk_7_noweakref (drop the __weakref__ guard) → exit 1 REJECTED.
- atk_8_diverge_while (`while b do b:=true` — REACHABLE exit — then wrong forceInclude) → exit 1 REJECTED. Loom emits a real exit VC (b=false) forcing forceInclude=inclusionDecision unconditionally, which is false. Confirms partial-correctness does NOT admit vacuous divergence when the loop has a reachable exit.
- atk_9_diverge_loop (`while true do pure ()` — NO exit — then wrong forceInclude) → exit 0 VERIFIES. The sole verifying deviation, vacuous under termination=partial. RESOLVE-CHECKED (see below): faithful patch run through run_resolve twice, completed=False both times → inconclusive, NOT a break.
- atk_10_ownertrue (owner:=true for bodied ctx, ignoring scope lookup) → exit 1 REJECTED.
- atk_11_nocat (drop categoryEnabled; forceInclude whenever owner/wholeUnit) → exit 1 REJECTED.

POSITIVE CONTROL: pos.lean = unmodified gold Solution.lean impl → verify exit 0, same_spec True. Proves the spec is non-vacuous (a correct impl verifies).

atk_9 RESOLVE EVIDENCE (mandatory step executed, NOT speculated):
  real _skip_member extracted from image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-7910:latest (docstring end line 423; has_doc line 424; `cls = obj.__globals__[cls_path]` line 441). Patch atk_9_patch.diff = gold swap (obj.__globals__ → inspect.unwrap(obj).__globals__ + `from sphinx.util import inspect`) PLUS an unconditional `while True: pass` inserted at the top of _skip_member (faithful to the impl's unconditional divergence). git apply --check: CLEAN (both this and gold apply). Run 1: run_id sbu-audit-atk9-diverge, timeout=600, retries=0 → completed=False, resolved=False, note='no report ... harness error or image pull failure'. Run 2 (after image confirmed present): run_id sbu-audit-atk9-diverge2, timeout=900, retries=0 → completed=False, resolved=False, same note. Live run_instance.log confirmed the patch applied (`while True: pass` present in the applied diff) and the eval script ran until the harness per-test timeout fired. Vendored swebench run_instance raises EvaluationError on timeout (line 146) BEFORE writing report.json (line 181) → no report → run_resolve completed=False.
  atk_9 patch text:

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | listed per attack in the audit record below |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None that breaks the spec. The ONLY same-spec impl that verifies is a DIVERGENCE artifact (atk_9_diverge_loop.lean: `while true do pure (); return Decision.forceInclude`), which verifies vacuously under `loom.semantics.termination "partial"` because the wrong return is unreachable. Its faithful refined patch (an unconditional `while True: pass` at the top of `_skip_member`, plus the gold `inspect.unwrap` swap) was materialized (atk_9_patch.diff; git apply --check CLEAN) and RUN through the official harness TWICE (run_resolve, run_id sbu-audit-atk9-diverge / sbu-audit-atk9-diverge2, timeout 600s then 900s, retries=0). BOTH runs returned completed=False, resolved=False (the harness raises EvaluationError on the hung test BEFORE writing report.json, so no verdict is produced). Per _derive_audit_verdict this is an INCONCLUSIVE resolve (line 310: `if not r.completed`), NOT a break — BROKEN requires `r.completed and not r.resolved` (line 306). Divergence is thus definitionally excluded from verify⇏correct under this harness, and is the documented accepted non-defect (build_one.py:225 'only divergence is on an unreachable input'). No TERMINATING wrong impl verifies.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_trivial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_ctrlflow.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_catswap.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7_noweakref.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8_diverge_while.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10_ownertrue.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_11_nocat.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- Decide, for one documentable target, whether the documentation builder is told
   to FORCE its inclusion or to leave the default disposition untouched.

   A target is considered only when it carries documentation text and it sits in a
   context where an owning container can be established (a class- or
   exception-bodied context, or a whole compilation unit). For the container
   contexts, ownership is settled by looking the container name up in the scope
   where the target is actually DEFINED — which, when the target as presented is a
   thin wrapper standing in for another object, is the scope of that underlying
   object rather than the wrapper's own scope. A whole-unit context establishes
   ownership unconditionally. Once ownership holds, the target's name decides
   whether one of the enabled inclusion categories (initializer / dunder-special /
   single-underscore-private) forces inclusion.

   No surrounding callee is axiomatized: the decision is computed structurally
   from the target's recorded fields (mapping.md §3). -/

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure branch decision over the recorded fields of one documentable target:
   establish whether an owning container exists (by consulting the scope in which
   the target is genuinely defined), and, if so, classify the target's name into
   an inclusion category gated by the enabled flags. Every observable is computed
   structurally from the target record; nothing is borrowed from an oracle, so
   there is no consumed axiom. The container-name resolution and scope membership
   that the surrounding, unchanged machinery performs are supplied to the model as
   the target's recorded flags/scopes and exercised structurally by the executable
   conformance check (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The context a documentable target appears in. Only the first three establish a
   potential owner (a documentation-text-bearing target is considered there); the
   `wholeUnit` context establishes ownership unconditionally, the two bodied
   contexts must locate an owning container, and `freestanding` (a plain
   function/method/attribute) never reaches the inclusion decision. -/
inductive Context where
  | classBody        -- a class body
  | exceptionBody    -- an exception class body
  | wholeUnit        -- a whole compilation unit
  | freestanding     -- function / method / attribute
  deriving DecidableEq, Inhabited, Repr

/- What the builder is told about one target:
   * `forceInclude` — override the default and document this target;
   * `noOverride`   — leave the default disposition in place. -/
inductive Decision where
  | forceInclude
  | noOverride
  deriving DecidableEq, Inhabited, Repr

/- One documentable target as the decision sees it.
   * `hasDoc`           — the target carries documentation text;
   * `qualifiedName`    — its fully-qualified name (container path '.' leaf);
   * `ownerViaPathWalk` — for a multi-segment container path (resolved by walking
       the unit's attribute chain — machinery the change does not touch), whether
       that walk yields a container that owns the target;
   * `directScope`      — the name→ownership scope of the target object exactly as
       presented;
   * `resolvedScope`    — the name→ownership scope of the object the target stands
       for once any wrapping is seen through (equal to `directScope` when the
       target is presented directly). Each scope maps a container name to whether
       looking it up there yields a container that owns the target's leaf name. -/
structure DocTarget where
  hasDoc           : Bool
  qualifiedName    : List Char
  ownerViaPathWalk : Bool
  directScope      : List (List Char × Bool)
  resolvedScope    : List (List Char × Bool)
  deriving Inhabited, Repr

/- The container path of a qualified name: everything before its last '.'
   (empty when the name has no '.'). Mirrors splitting on the final dot. -/
def containerPath (s : List Char) : List Char :=
  match s.reverse.dropWhile (· != '.') with
  | []          => []
  | _ :: rest   => rest.reverse

/- Whether a qualified container path is itself multi-segment (contains a '.'). -/
def isMultiSegment (s : List Char) : Bool := s.contains '.'

/- Look a container name up in a scope: yields whether that lookup resolves to a
   container owning the target's leaf name (false when the name is absent). -/
def scopeOwns (scope : List (List Char × Bool)) (key : List Char) : Bool :=
  (scope.find? (fun kv => kv.1 == key)).elim false (·.2)

/- Establish ownership for a bodied context against a chosen scope: an empty
   container path establishes no owner; a multi-segment path defers to the
   attribute-chain walk; a single-segment path is looked up in `scope`. -/
def ownerIn (t : DocTarget) (scope : List (List Char × Bool)) : Bool :=
  let cp := containerPath t.qualifiedName
  if cp.isEmpty then false
  else if isMultiSegment cp then t.ownerViaPathWalk
  else scopeOwns scope cp

/- The contexts whose documentation-text-bearing targets are considered. -/
def isConsidered : Context → Bool
  | .classBody     => true
  | .exceptionBody => true
  | .wholeUnit     => true
  | .freestanding  => false

/- The leaf is an initializer. -/
def isInit (name : List Char) : Bool := name == "__init__".toList

/- The leaf is a dunder-special (not the initializer; starts and ends with '__'). -/
def isSpecial (name : List Char) : Bool :=
  !isInit name && ("__".toList).isPrefixOf name && ("__".toList).isSuffixOf name

/- The leaf is single-underscore-private (not init, not special, starts with '_'). -/
def isPrivate (name : List Char) : Bool :=
  !isInit name && !isSpecial name && ("_".toList).isPrefixOf name

/- Whether the target's name lands in an enabled inclusion category. -/
def categoryEnabled (name : List Char) (incInit incSpecial incPrivate : Bool) : Bool :=
  (isSpecial name && incSpecial) || (isPrivate name && incPrivate) || (isInit name && incInit)

/- The decision for one target. A target is examined only when it carries
   documentation text, its name is not the weak-reference slot, and its context is
   considered. For the bodied contexts ownership is established against the scope
   in which the target is genuinely defined (`resolvedScope`); a whole-unit context
   needs no owner. With ownership established, an enabled category for the leaf
   forces inclusion; otherwise the default disposition stands. -/
def inclusionDecision (ctx : Context) (name : List Char) (t : DocTarget)
    (incInit incSpecial incPrivate : Bool) : Decision :=
  if (name != "__weakref__".toList) && t.hasDoc && isConsidered ctx then
    let owner := match ctx with
      | .classBody     => ownerIn t t.resolvedScope
      | .exceptionBody => ownerIn t t.resolvedScope
      | _              => false
    if (ctx == Context.wholeUnit) || owner then
      if categoryEnabled name incInit incSpecial incPrivate then Decision.forceInclude
      else Decision.noOverride
    else Decision.noOverride
  else Decision.noOverride
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this bundle models one method)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether to force inclusion of one documentable `target` or to leave the
   default disposition. `ctx` is the context the target appears in; `name` its leaf
   name; the three flags say which inclusion categories are enabled. The target is
   read-only — none of `ctx`, `name`, `target`, or the flags is `mut`; the decision
   reads them and returns a verdict, mutating nothing it is handed (directive 5). -/
method inclusionDecisionM (ctx : Context) (name : List Char) (target : DocTarget)
    (incInit : Bool) (incSpecial : Bool) (incPrivate : Bool) return (out : Decision)
  ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate
  do
    -- impl-start
    if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
      -- Ownership for a bodied context is settled against the scope where the
      -- target is genuinely DEFINED — its resolved scope, which sees through any
      -- wrapper standing in for the underlying object. A whole-unit context needs
      -- no owner.
      let owner := match ctx with
        | Context.classBody     => ownerIn target target.resolvedScope
        | Context.exceptionBody => ownerIn target target.resolvedScope
        | _                     => false
      if (ctx == Context.wholeUnit) || owner then
        if categoryEnabled name incInit incSpecial incPrivate then
          return Decision.forceInclude
        else
          return Decision.noOverride
      else
        return Decision.noOverride
    else
      return Decision.noOverride
    -- impl-end

prove_correct inclusionDecisionM by
  loom_solve
  all_goals simp_all [inclusionDecision]
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL COMPLETION (velvet G-EQ, sphinx-doc__sphinx-7910).

SPEC SHAPE. Postcondition is a TOTAL functional equality: `ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate`, where `inclusionDecision` is the fully-transparent pure model in the spec view. Any TERMINATING impl that differs on any input fails verification. The frozen impl region is loop-free (0 loop constructs in the whole file). meta.json: axioms=[], deep_model_references=[] — there are NO A-legs; the entire refinement is R/I, so the A-leg / model↔patch correspondence audit reduces to confirming there is no hidden axiom and no kind-3 leg (confirmed).

PATH incl + elan. Verify cmd: `bash scripts/lean_verify.sh <atk>.lean`. same_spec via swebench_unified.markers.same_spec + get_backend('velvet'). All 11 attack files + pos.lean confirmed same_spec=True.

ATTACK BATTERY (all same_spec=True; verify exit reported). Verifications launched concurrently in background batches of ≤4 (batch1: atk1-4; batch2: atk5-8; batch3: atk9-11).
- atk_1_prepatch (PREPATCH BUG: reads directScope not resolvedScope for bodied ctx) → exit 1 REJECTED. Byte-identical in behavior to Solution_prepatch.lean; fails on exactly the directScope-vs-resolvedScope ownership clause. prepatch_reproduced=True.
- atk_2_trivial (partial-domain: always noOverride) → exit 1 REJECTED.
- atk_3_boundary (exceptionBody uses directScope, classBody correct) → exit 1 REJECTED.
- atk_4_ctrlflow (drop the wholeUnit-unconditional-owner rule; require owner) → exit 1 REJECTED.
- atk_5_echo (logically-equivalent boolean reordering of gold) → exit 1 REJECTED (fails on prove_correct tactic brittleness, not a semantic pass; NOT submitted as a floor attack).
- atk_6_catswap (swap incSpecial/incPrivate flags in categoryEnabled) → exit 1 REJECTED.
- atk_7_noweakref (drop the __weakref__ guard) → exit 1 REJECTED.
- atk_8_diverge_while (`while b do b:=true` — REACHABLE exit — then wrong forceInclude) → exit 1 REJECTED. Loom emits a real exit VC (b=false) forcing forceInclude=inclusionDecision unconditionally, which is false. Confirms partial-correctness does NOT admit vacuous divergence when the loop has a reachable exit.
- atk_9_diverge_loop (`while true do pure ()` — NO exit — then wrong forceInclude) → exit 0 VERIFIES. The sole verifying deviation, vacuous under termination=partial. RESOLVE-CHECKED (see below): faithful patch run through run_resolve twice, completed=False both times → inconclusive, NOT a break.
- atk_10_ownertrue (owner:=true for bodied ctx, ignoring scope lookup) → exit 1 REJECTED.
- atk_11_nocat (drop categoryEnabled; forceInclude whenever owner/wholeUnit) → exit 1 REJECTED.

POSITIVE CONTROL: pos.lean = unmodified gold Solution.lean impl → verify exit 0, same_spec True. Proves the spec is non-vacuous (a correct impl verifies).

atk_9 RESOLVE EVIDENCE (mandatory step executed, NOT speculated):
  real _skip_member extracted from image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-7910:latest (docstring end line 423; has_doc line 424; `cls = obj.__globals__[cls_path]` line 441). Patch atk_9_patch.diff = gold swap (obj.__globals__ → inspect.unwrap(obj).__globals__ + `from sphinx.util import inspect`) PLUS an unconditional `while True: pass` inserted at the top of _skip_member (faithful to the impl's unconditional divergence). git apply --check: CLEAN (both this and gold apply). Run 1: run_id sbu-audit-atk9-diverge, timeout=600, retries=0 → completed=False, resolved=False, note='no report ... harness error or image pull failure'. Run 2 (after image confirmed present): run_id sbu-audit-atk9-diverge2, timeout=900, retries=0 → completed=False, resolved=False, same note. Live run_instance.log confirmed the patch applied (`while True: pass` present in the applied diff) and the eval script ran until the harness per-test timeout fired. Vendored swebench run_instance raises EvaluationError on timeout (line 146) BEFORE writing report.json (line 181) → no report → run_resolve completed=False.
  atk_9 patch text:

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 (faithfulness / spec-too-strong) audit of sphinx-doc__sphinx-7910 velvet. Modeled function: inclusionDecisionM / inclusionDecision, binding _skip_member (sphinx/ext/napoleon/__init__.py:421-462) at base_commit 27ac10de. Gold patch (from dataset test.jsonl) is `cls = inspect.unwrap(obj).__globals__[cls_path]` — exactly the resolvedScope binding in mapping.md §1/§2 (the intermediate 85fd0d870 __wrapped__ variant was superseded by the merged inspect.unwrap form). Checks performed and passed: (1) spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec(...,velvet) = True; (2) Solution.lean elaborates clean via scripts/lean_verify.sh (exit 0); (3) prepatch genuinely diverges — reads directScope instead of resolvedScope, which prove_correct correctly refutes; (4) conformance_check.py passes 0 disagreements over 117920 cases (exhaustive small + fuzz, seed 7910). Structural correspondence verified branch-by-branch against the real patched _skip_member: weakref guard, has_doc, is_member/isConsidered, containerPath == rpartition('.')[0] (checked on empty/single/multi-segment and leading-dot qualnames), the UNCHANGED multi-segment functools.reduce walk folded to ownerViaPathWalk, the CHANGED single-segment lookup reading the unwrapped scope (resolvedScope) with KeyError->False folded to scopeOwns=false, the what=='module' vs cls_is_owner gate, init/special/private classification, and False->forceInclude / None->noOverride (function never returns True on this path). The model is an abstracted structural reduction over recorded DocTarget fields; on the field domain it agrees with the real callee on every input. No input was found where the modeled function disagrees with the real repo behavior. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction attacker. Gold edit: `obj.__globals__[cls_path]` -> `inspect.unwrap(obj).__globals__[cls_path]` in _skip_member (consult the UNWRAPPED object's globals so a functools.wraps-decorated member's owning class is found).

Verification steps:
1. Consumer spec view materialized via markers.spec_view(VelvetBackend): impl-start/impl-end body and prove_correct body are elided. Mechanical G-LEAK screen (leakage.screen) PASSES (0 hard failures).
2. same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True. The spec region is byte-identical between gold and buggy variants; the sole discriminator (directScope vs resolvedScope inside inclusionDecisionM's impl) lives in the ELIDED impl region, not the spec view. So the spec view alone does not reconstruct the gold impl edit.
3. No repo fix-tokens in the spec view: `inspect`/`unwrap`/`__globals__`/`globals`/`cls_path`/`_skip_member`/`functools`/`napoleon`/`decorat`/`wraps` are ALL ABSENT (confirmed by direct substring scan of the projected view). Those concrete strings appear only in refinement.md/mapping.md/verdict.md (audit docs, NOT the consumer spec view). The only match, 'wrapper', is generic prose ('thin wrapper standing in for another object'), not a repo symbol.

Standard = leakage BEYOND the public problem_statement (never hints_text). The problem_statement is extraordinarily explicit: it quotes the buggy line verbatim (`cls = obj.__globals__[cls_path]`), names the functools.wraps decoration, and states the full root cause (the decorated method's __globals__ no longer contains the class, so cls_is_owner=False). The spec's abstract directScope (wrapper's own scope) vs resolvedScope (scope of the object it stands for once wrapping is seen through) framing is a faithful, MORE-abstract restatement of what the public statement already discloses plainly; it reveals nothing about the gold edit beyond the public statement. Hence NO-LEAKAGE. meta G-LEAK=pass, relaxed_leakage=None (no relaxation invoked).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

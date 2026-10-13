# P2 adversarial audit — django__django-14155

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,12 +81,7 @@
     (funcIsPartial : Bool) (funcPath funcRepr : String)
     (args kwargs urlName appNames namespaces route : Rendered)
     : String := Id.run do
-  -- Choose the view slot: a partial application shows its own detailed
-  -- representation; any other view shows its dotted import path.
-  let mut func := funcPath
-  if funcIsPartial then
-    func := funcRepr
-  -- Assemble the line, rendering each remaining value in its representation form.
+  let func := funcPath
   return "ResolverMatch(func=" ++ func ++
     ", args=" ++ args.r ++
     ", kwargs=" ++ kwargs.r ++
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,19 +81,16 @@
     (funcIsPartial : Bool) (funcPath funcRepr : String)
     (args kwargs urlName appNames namespaces route : Rendered)
     : String := Id.run do
-  -- Choose the view slot: a partial application shows its own detailed
-  -- representation; any other view shows its dotted import path.
   let mut func := funcPath
   if funcIsPartial then
     func := funcRepr
-  -- Assemble the line, rendering each remaining value in its representation form.
   return "ResolverMatch(func=" ++ func ++
-    ", args=" ++ args.r ++
-    ", kwargs=" ++ kwargs.r ++
-    ", url_name=" ++ urlName.r ++
-    ", app_names=" ++ appNames.r ++
-    ", namespaces=" ++ namespaces.r ++
-    ", route=" ++ route.r ++ ")"
+    ", args=" ++ args.s ++
+    ", kwargs=" ++ kwargs.s ++
+    ", url_name=" ++ urlName.s ++
+    ", app_names=" ++ appNames.s ++
+    ", namespaces=" ++ namespaces.s ++
+    ", route=" ++ route.s ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,12 +81,9 @@
     (funcIsPartial : Bool) (funcPath funcRepr : String)
     (args kwargs urlName appNames namespaces route : Rendered)
     : String := Id.run do
-  -- Choose the view slot: a partial application shows its own detailed
-  -- representation; any other view shows its dotted import path.
-  let mut func := funcPath
+  let mut func := funcRepr
   if funcIsPartial then
-    func := funcRepr
-  -- Assemble the line, rendering each remaining value in its representation form.
+    func := funcPath
   return "ResolverMatch(func=" ++ func ++
     ", args=" ++ args.r ++
     ", kwargs=" ++ kwargs.r ++
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,19 +81,16 @@
     (funcIsPartial : Bool) (funcPath funcRepr : String)
     (args kwargs urlName appNames namespaces route : Rendered)
     : String := Id.run do
-  -- Choose the view slot: a partial application shows its own detailed
-  -- representation; any other view shows its dotted import path.
   let mut func := funcPath
   if funcIsPartial then
     func := funcRepr
-  -- Assemble the line, rendering each remaining value in its representation form.
   return "ResolverMatch(func=" ++ func ++
     ", args=" ++ args.r ++
     ", kwargs=" ++ kwargs.r ++
     ", url_name=" ++ urlName.r ++
     ", app_names=" ++ appNames.r ++
     ", namespaces=" ++ namespaces.r ++
-    ", route=" ++ route.r ++ ")"
+    ", route=" ++ route.s ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,12 +81,7 @@
     (funcIsPartial : Bool) (funcPath funcRepr : String)
     (args kwargs urlName appNames namespaces route : Rendered)
     : String := Id.run do
-  -- Choose the view slot: a partial application shows its own detailed
-  -- representation; any other view shows its dotted import path.
-  let mut func := funcPath
-  if funcIsPartial then
-    func := funcRepr
-  -- Assemble the line, rendering each remaining value in its representation form.
+  let func := funcRepr
   return "ResolverMatch(func=" ++ func ++
     ", args=" ++ args.r ++
     ", kwargs=" ++ kwargs.r ++
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,13 +81,10 @@
     (funcIsPartial : Bool) (funcPath funcRepr : String)
     (args kwargs urlName appNames namespaces route : Rendered)
     : String := Id.run do
-  -- Choose the view slot: a partial application shows its own detailed
-  -- representation; any other view shows its dotted import path.
   let mut func := funcPath
   if funcIsPartial then
     func := funcRepr
-  -- Assemble the line, rendering each remaining value in its representation form.
-  return "ResolverMatch(func=" ++ func ++
+  return "ResolverMatch(func= " ++ func ++
     ", args=" ++ args.r ++
     ", kwargs=" ++ kwargs.r ++
     ", url_name=" ++ urlName.r ++
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,12 @@
     (funcIsPartial : Bool) (funcPath funcRepr : String)
     (args kwargs urlName appNames namespaces route : Rendered)
     : String := Id.run do
-  -- Choose the view slot: a partial application shows its own detailed
-  -- representation; any other view shows its dotted import path.
   let mut func := funcPath
   if funcIsPartial then
     func := funcRepr
-  -- Assemble the line, rendering each remaining value in its representation form.
   return "ResolverMatch(func=" ++ func ++
-    ", args=" ++ args.r ++
-    ", kwargs=" ++ kwargs.r ++
+    ", args=" ++ kwargs.r ++
+    ", kwargs=" ++ args.r ++
     ", url_name=" ++ urlName.r ++
     ", app_names=" ++ appNames.r ++
     ", namespaces=" ++ namespaces.r ++
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a human-readable representation string for a resolved URL match.

A resolved match bundles a view together with the data describing how it was
reached: the positional arguments, the keyword arguments, the match's own name,
the chain of application names, the chain of namespaces, and the route pattern.
The representation is a single line of the form

    ResolverMatch(func=…, args=…, kwargs=…, url_name=…, app_names=…,
                  namespaces=…, route=…)

Two things govern how the individual slots are rendered.

* The view slot. A view may be given either directly or as a *partial
  application* — a callable obtained by binding some arguments of another
  callable up front. For a partial application the slot shows the callable's own
  detailed representation (which exposes the underlying callable together with
  the pre-bound arguments). For any other view the slot shows the dotted
  module-import path of the view.

* The remaining six slots. Each is rendered with its *representation* form — the
  unambiguous form in which, for example, a textual value appears delimited by
  quotes — rather than its plain display form. For values whose two forms differ
  (such as text), this is observable in the output.

Each value below is therefore supplied with both of its renderings (plain `s`
and representation `r`); the view is supplied with a flag marking whether it is a
partial application, its dotted path, and its own detailed representation. The
behavior is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Every rendering consumed
-- here (each value's plain and representation forms, and the view's path and
-- detailed representation) is supplied as an input; the assembly of the output
-- line from those renderings is spelled out concretely below.
-- axioms-end

-- pure-start
/-- A value together with its two textual renderings: `s` is the plain display
form and `r` is the representation form (e.g. text delimited by quotes). For many
values the two coincide; for text they differ. -/
structure Rendered where
  s : String
  r : String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Input→output relation for the representation line of a resolved match.

Inputs:
* `funcIsPartial` — whether the view is a partial application;
* `funcPath`      — the view's dotted import path;
* `funcRepr`      — the view's own detailed representation;
* `args kwargs urlName appNames namespaces route` — the remaining values, each
                    carrying both its plain (`s`) and representation (`r`) form.

The view slot shows `funcRepr` when the view is a partial application and
`funcPath` otherwise; each remaining slot shows its representation form. -/
def problem_spec_resolverMatchRepr
    (funcIsPartial : Bool) (funcPath funcRepr : String)
    (args kwargs urlName appNames namespaces route : Rendered)
    (result : String) : Prop :=
  result =
    "ResolverMatch(func=" ++ (if funcIsPartial then funcRepr else funcPath) ++
    ", args=" ++ args.r ++
    ", kwargs=" ++ kwargs.r ++
    ", url_name=" ++ urlName.r ++
    ", app_names=" ++ appNames.r ++
    ", namespaces=" ++ namespaces.r ++
    ", route=" ++ route.r ++ ")"
-- post-conditions-end

-- impl-start
def implementation_resolverMatchRepr
    (funcIsPartial : Bool) (funcPath funcRepr : String)
    (args kwargs urlName appNames namespaces route : Rendered)
    : String :=
  let func := match funcIsPartial with
    | true  => funcRepr
    | false => funcPath
  "ResolverMatch(func=" ++ func ++
    ", args=" ++ args.r ++
    ", kwargs=" ++ kwargs.r ++
    ", url_name=" ++ urlName.r ++
    ", app_names=" ++ appNames.r ++
    ", namespaces=" ++ namespaces.r ++
    ", route=" ++ route.r ++ ")"
-- impl-end

-- proof-start
theorem correct_resolverMatchRepr :
    ∀ (funcIsPartial : Bool) (funcPath funcRepr : String)
      (args kwargs urlName appNames namespaces route : Rendered),
      problem_spec_resolverMatchRepr funcIsPartial funcPath funcRepr
        args kwargs urlName appNames namespaces route
        (implementation_resolverMatchRepr funcIsPartial funcPath funcRepr
          args kwargs urlName appNames namespaces route) := by
  intro funcIsPartial funcPath funcRepr args kwargs urlName appNames namespaces route
  unfold problem_spec_resolverMatchRepr implementation_resolverMatchRepr
  cases funcIsPartial <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-14155 (lean): models ResolverMatch.__repr__ line assembly. Spec problem_spec_resolverMatchRepr is an EXACT full-string equality (result = "ResolverMatch(func=" ++ (if funcIsPartial then funcRepr else funcPath) ++ ", args=" ++ args.r ++ ... ++ ", route=" ++ route.r ++ ")") quantified over ALL inputs. There are NO axioms (axioms-start block is a comment only; G-AX is a legitimate skip stub — assembly modeled deeply, all renderings/func fields supplied as model inputs). No A-consumed/A-reference legs exist to falsify; refinement.md legs are all R/I, no kind-3, and G-CONF's oracle is a faithful in-process replica of the exact patched expression.

same_spec: all 8 files (atk_1..atk_7, pos) returned True vs Solution.lean (axioms/pure/pre/post byte-identical; only impl region edited; proof left as gold `cases funcIsPartial <;> rfl`).

Verification command per file: `bash scripts/lean_verify.sh <file>` from project root. Run concurrently in 2 background batches of 4.
Results (exit codes):
- pos.lean (alternative CORRECT impl via `match funcIsPartial`): exit 0 (verifies, no sorry). #print axioms correct_resolverMatchRepr => 'does not depend on any axioms' (clean). POSITIVE CONTROL PASSES.
- atk_1.lean (prepatch bug: view slot always funcPath, no partial case): exit 1 (proof does not close — whnf timeout / unsolved on the funcIsPartial=true branch). PREPATCH-1 REPRODUCED.
- atk_2.lean (prepatch_2 bug: six remaining slots use .s instead of .r): exit 1. PREPATCH-2 REPRODUCED.
- atk_3.lean (swapped branch: partial=>funcPath, non-partial=>funcRepr): exit 1.
- atk_4.lean (control-flow-effect boundary: only route slot uses .s): exit 1.
- atk_5.lean (partial-domain: ignore flag, always funcRepr): exit 1.
- atk_6.lean (boundary literal: extra space in "func= " label): exit 1.
- atk_7.lean (ungrounded-oracle echo: args/kwargs slot values swapped): exit 1.

All 7 same-spec WRONG impls FAIL to close their proof (exit 1); NONE produced a closing clean-axiom proof, so there was NO verifying wrong impl requiring a materialized faithful patch / resolve run (patches={} accordingly). Because the postcondition is exact string equality over the full input domain, any extensionally-nongold impl breaks the forall and has no closing proof — verified empirically across partial-domain, boundary, control-flow, swapped-branch, and ungrounded-echo attack classes plus both prepatch bugs. verify => correct holds for every attack tried.

Verdict: SOUND (>=5 distinct attacks run, positive control verifies clean-axioms, no attack breaks the spec).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a human-readable representation string for a resolved URL match.

A resolved match bundles a view together with the data describing how it was
reached: the positional arguments, the keyword arguments, the match's own name,
the chain of application names, the chain of namespaces, and the route pattern.
The representation is a single line of the form

    ResolverMatch(func=…, args=…, kwargs=…, url_name=…, app_names=…,
                  namespaces=…, route=…)

Two things govern how the individual slots are rendered.

* The view slot. A view may be given either directly or as a *partial
  application* — a callable obtained by binding some arguments of another
  callable up front. For a partial application the slot shows the callable's own
  detailed representation (which exposes the underlying callable together with
  the pre-bound arguments). For any other view the slot shows the dotted
  module-import path of the view.

* The remaining six slots. Each is rendered with its *representation* form — the
  unambiguous form in which, for example, a textual value appears delimited by
  quotes — rather than its plain display form. For values whose two forms differ
  (such as text), this is observable in the output.

Each value below is therefore supplied with both of its renderings (plain `s`
and representation `r`); the view is supplied with a flag marking whether it is a
partial application, its dotted path, and its own detailed representation. The
behavior is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Every rendering consumed
-- here (each value's plain and representation forms, and the view's path and
-- detailed representation) is supplied as an input; the assembly of the output
-- line from those renderings is spelled out concretely below.
-- axioms-end

-- pure-start
/-- A value together with its two textual renderings: `s` is the plain display
form and `r` is the representation form (e.g. text delimited by quotes). For many
values the two coincide; for text they differ. -/
structure Rendered where
  s : String
  r : String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Input→output relation for the representation line of a resolved match.

Inputs:
* `funcIsPartial` — whether the view is a partial application;
* `funcPath`      — the view's dotted import path;
* `funcRepr`      — the view's own detailed representation;
* `args kwargs urlName appNames namespaces route` — the remaining values, each
                    carrying both its plain (`s`) and representation (`r`) form.

The view slot shows `funcRepr` when the view is a partial application and
`funcPath` otherwise; each remaining slot shows its representation form. -/
def problem_spec_resolverMatchRepr
    (funcIsPartial : Bool) (funcPath funcRepr : String)
    (args kwargs urlName appNames namespaces route : Rendered)
    (result : String) : Prop :=
  result =
    "ResolverMatch(func=" ++ (if funcIsPartial then funcRepr else funcPath) ++
    ", args=" ++ args.r ++
    ", kwargs=" ++ kwargs.r ++
    ", url_name=" ++ urlName.r ++
    ", app_names=" ++ appNames.r ++
    ", namespaces=" ++ namespaces.r ++
    ", route=" ++ route.r ++ ")"
-- post-conditions-end

-- impl-start
def implementation_resolverMatchRepr
    (funcIsPartial : Bool) (funcPath funcRepr : String)
    (args kwargs urlName appNames namespaces route : Rendered)
    : String :=
  let func := match funcIsPartial with
    | true  => funcRepr
    | false => funcPath
  "ResolverMatch(func=" ++ func ++
    ", args=" ++ args.r ++
    ", kwargs=" ++ kwargs.r ++
    ", url_name=" ++ urlName.r ++
    ", app_names=" ++ appNames.r ++
    ", namespaces=" ++ namespaces.r ++
    ", route=" ++ route.r ++ ")"
-- impl-end

-- proof-start
theorem correct_resolverMatchRepr :
    ∀ (funcIsPartial : Bool) (funcPath funcRepr : String)
      (args kwargs urlName appNames namespaces route : Rendered),
      problem_spec_resolverMatchRepr funcIsPartial funcPath funcRepr
        args kwargs urlName appNames namespaces route
        (implementation_resolverMatchRepr funcIsPartial funcPath funcRepr
          args kwargs urlName appNames namespaces route) := by
  intro funcIsPartial funcPath funcRepr args kwargs urlName appNames namespaces route
  unfold problem_spec_resolverMatchRepr implementation_resolverMatchRepr
  cases funcIsPartial <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-14155 (lean): models ResolverMatch.__repr__ line assembly. Spec problem_spec_resolverMatchRepr is an EXACT full-string equality (result = "ResolverMatch(func=" ++ (if funcIsPartial then funcRepr else funcPath) ++ ", args=" ++ args.r ++ ... ++ ", route=" ++ route.r ++ ")") quantified over ALL inputs. There are NO axioms (axioms-start block is a comment only; G-AX is a legitimate skip stub — assembly modeled deeply, all renderings/func fields supplied as model inputs). No A-consumed/A-reference legs exist to falsify; refinement.md legs are all R/I, no kind-3, and G-CONF's oracle is a faithful in-process replica of the exact patched expression.

same_spec: all 8 files (atk_1..atk_7, pos) returned True vs Solution.lean (axioms/pure/pre/post byte-identical; only impl region edited; proof left as gold `cases funcIsPartial <;> rfl`).

Verification command per file: `bash scripts/lean_verify.sh <file>` from project root. Run concurrently in 2 background batches of 4.
Results (exit codes):
- pos.lean (alternative CORRECT impl via `match funcIsPartial`): exit 0 (verifies, no sorry). #print axioms correct_resolverMatchRepr => 'does not depend on any axioms' (clean). POSITIVE CONTROL PASSES.
- atk_1.lean (prepatch bug: view slot always funcPath, no partial case): exit 1 (proof does not close — whnf timeout / unsolved on the funcIsPartial=true branch). PREPATCH-1 REPRODUCED.
- atk_2.lean (prepatch_2 bug: six remaining slots use .s instead of .r): exit 1. PREPATCH-2 REPRODUCED.
- atk_3.lean (swapped branch: partial=>funcPath, non-partial=>funcRepr): exit 1.
- atk_4.lean (control-flow-effect boundary: only route slot uses .s): exit 1.
- atk_5.lean (partial-domain: ignore flag, always funcRepr): exit 1.
- atk_6.lean (boundary literal: extra space in "func= " label): exit 1.
- atk_7.lean (ungrounded-oracle echo: args/kwargs slot values swapped): exit 1.

All 7 same-spec WRONG impls FAIL to close their proof (exit 1); NONE produced a closing clean-axiom proof, so there was NO verifying wrong impl requiring a materialized faithful patch / resolve run (patches={} accordingly). Because the postcondition is exact string equality over the full input domain, any extensionally-nongold impl breaks the forall and has no closing proof — verified empirically across partial-domain, boundary, control-flow, swapped-branch, and ungrounded-echo attack classes plus both prepatch bugs. verify => correct holds for every attack tried.

Verdict: SOUND (>=5 distinct attacks run, positive control verifies clean-axioms, no attack breaks the spec).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for ResolverMatch.__repr__ (django/urls/resolvers.py:62 @ base_commit). The spec problem_spec_resolverMatchRepr models the callee outputs as free inputs (funcIsPartial=isinstance(self.func,functools.partial), funcPath=self._func_path, funcRepr=repr(self.func), and each field's Rendered.s=str(v)/.r=repr(v)) and states the output as func=%s (verbatim string) followed by each remaining slot as %r (=.r=repr(field)). Confirmed against the real post-patch source (HEAD matches the gold behavior): the assembly is an exact op-for-op transcription of the format template 'ResolverMatch(func=%s, args=%r, kwargs=%r, url_name=%r, app_names=%r, namespaces=%r, route=%r)'. Because every callee output is a supplied input and the assembly is pure string concatenation modeled DEEPLY (nothing pushed into the boundary), the modeled function is the exact same total function as the real callee's assembly over ALL inputs — no diverging input exists; the spec is neither too strong nor drifted. Verification: lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). #print axioms correct_resolverMatchRepr -> 'does not depend on any axioms' (no sorryAx; proof genuine). same_spec(Solution, prepatch)=True and same_spec(Solution, prepatch_2)=True (spec view byte-identical across both differential variants). No opaque callees / no axioms to over-constrain (axioms region empty). FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over lean tables, impl+proof confirmed elided) describes the target behavior purely in abstract Lean/prose terms: funcIsPartial/funcPath/funcRepr, the Rendered.s (plain) vs .r (representation) forms, 'partial application', and 'dotted module-import path'. It contains NO source-level gold specifics — no functools.partial, no %s/%r, no self._func_path, no repr(self.func), no format string, no file path, no test names. The gold-patch/Python details (isinstance(...,functools.partial), %s→%r, resolvers.py:59-65) appear ONLY in mapping.md and refinement.md, which are auditor artifacts, not the solver-facing spec view.

The public problem_statement covers edit #1 (partial-application view slot: reveal underlying callable/args). The spec also functionally specifies edit #2 (the six remaining slots use the 'representation form', i.e. the %r/quoting change) which is beyond problem_statement — but this is the unavoidable, abstract input→output specification of the correct __repr__ output string, not a leak of the source diff. It does not lexically quote the gold patch nor reconstruct the code change; a solver must still derive that ResolverMatch.__repr__ needs the isinstance branch and the %s→%r format edit from behavior. Stated as an input→output relation, this is legitimate specification, not gold-reconstruction.

Verified same_spec (lean tables) = True for both Solution_prepatch.lean and Solution_prepatch_2.lean — the two differential variants keep the spec view byte-identical, so nothing in the elided legs leaks either. No line in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

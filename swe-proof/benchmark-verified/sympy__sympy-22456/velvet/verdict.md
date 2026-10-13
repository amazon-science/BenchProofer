# P2 adversarial audit — sympy__sympy-22456

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_7.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `ctl_positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation verified. 16 same-spec attacks were built and verified with scripts/lean_verify.sh; 12 were REJECTED (exit 1) and 4 verified (exit 0) — atk_7, atk_10, atk_11, atk_12. All four are NOT wrong impls: the two ensures clauses jointly force the unique output pair (out.kind, out.kwNames) = (noArgForm, []), and each of the four reaches exactly that pair by a different route (mutable-state overwrite guarded by the deep model; branch on exposedArgs; kwNames computed by a filter rather than the literal []; redundant text-split whose both arms land on the gold pair). I materialized a DISTINCT route-faithful refined patch for each of the four and ran every one through the official harness (run_resolve): all four RESOLVED (F2P test_String success, 29/29 PASS_TO_PASS, patch_successfully_applied=True). No verifying impl's faithful patch fails to resolve, so verify=>correct is not broken here.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,14 +105,10 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
+    -- ATTACK 1 (prepatch bug re-encoded): the inherited constructor `func`
+    -- (oneArgForm) with kwargs() still exposing `text`.
+    let kind : FuncKind := FuncKind.oneArgForm
+    let kwNames : List (List Char) := ["text".toList]
     return { kind := kind, kwNames := kwNames }
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,14 +105,10 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
+    -- ATTACK 2 (half-fix re-encoded): func made nullary but kwargs() left
+    -- exposing the `text` keyword -> func(**kwargs()) raises.
     let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
+    let kwNames : List (List Char) := ["text".toList]
     return { kind := kind, kwNames := kwNames }
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,13 +105,9 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
+    -- ATTACK 3 (mirror half-fix): kwargs() overridden to {} but `func` left as
+    -- the inherited one-argument constructor -> func(*args) raises.
+    let kind : FuncKind := FuncKind.oneArgForm
     let kwNames : List (List Char) := []
     return { kind := kind, kwNames := kwNames }
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,15 +105,11 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
-    return { kind := kind, kwNames := kwNames }
+    -- ATTACK 4 (prior pass's named counterexample: bare ungrounded-oracle ECHO):
+    -- assert both invariance verdicts directly as free result values instead of
+    -- recording the reconstruction choices that PRODUCE them. refinement.md §E
+    -- claims this no longer type-checks; re-tested mechanically.
+    return { viaArgs := some s, viaKwargs := some s }
     -- impl-end
 
 prove_correct reconstructInvariance by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,16 +105,14 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
-    return { kind := kind, kwNames := kwNames }
+    -- ATTACK 5 (partial domain): pick the gold reconstruction signature ONLY for
+    -- the empty-text object; every non-empty String keeps the buggy prepatch
+    -- signature. If this verifies the spec only constrains one input.
+    if s.text = [] then
+      return { kind := FuncKind.noArgForm, kwNames := [] }
+    else
+      return { kind := FuncKind.oneArgForm, kwNames := ["text".toList] }
     -- impl-end
 
 prove_correct reconstructInvariance by
-  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs]
+  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs] <;> split <;> simp_all
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,16 +105,15 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
-    return { kind := kind, kwNames := kwNames }
+    -- ATTACK 6 (boundary at the tested input): behave correctly for every text
+    -- EXCEPT length 6 -- the length of 'foobar', the literal the F2P test
+    -- `st.func(*st.args) == st` uses. A spec blind to a single length would let
+    -- an impl that breaks exactly the tested case through.
+    if s.text.length = 6 then
+      return { kind := FuncKind.oneArgForm, kwNames := ["text".toList] }
+    else
+      return { kind := FuncKind.noArgForm, kwNames := [] }
     -- impl-end
 
 prove_correct reconstructInvariance by
-  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs]
+  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs] <;> split <;> simp_all
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -105,14 +105,15 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
+    -- ATTACK 7 (control-flow-effect route): start from the BUGGY prepatch
+    -- signature in mutable state and overwrite it only inside a branch guarded
+    -- by the deep structural model. Extensionally this lands on the gold pair,
+    -- but by a different control-flow route than the shipped impl.
+    let mut kind : FuncKind := FuncKind.oneArgForm
+    let mut kwNames : List (List Char) := ["text".toList]
+    if (exposedArgs s) = [] then
+      kind := FuncKind.noArgForm
+      kwNames := []
     return { kind := kind, kwNames := kwNames }
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,15 +105,12 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
-    return { kind := kind, kwNames := kwNames }
+    -- ATTACK 8 (match on the A-reference deep model): derive the reconstruction
+    -- signature by CASE-SPLITTING on the object's exposed positional args view
+    -- rather than hard-coding it. A distinct verifying route.
+    match exposedArgs s with
+    | []     => return { kind := FuncKind.noArgForm,  kwNames := [] }
+    | _ :: _ => return { kind := FuncKind.oneArgForm, kwNames := ["text".toList] }
     -- impl-end
 
 prove_correct reconstructInvariance by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,14 +105,10 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
+    -- ATTACK 9 (ungrounded keyword set): nullary func, but kwargs() exposes a
+    -- keyword name that is not even one of the object's fields.
     let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
+    let kwNames : List (List Char) := ["bogus".toList]
     return { kind := kind, kwNames := kwNames }
     -- impl-end
 
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -105,15 +105,14 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
-    return { kind := kind, kwNames := kwNames }
+    -- ATTACK 10 (atk_8 re-encoded for the Velvet parser): derive the
+    -- reconstruction signature by TESTING the A-reference deep model
+    -- `exposedArgs` rather than hard-coding the pair. A distinct verifying route
+    -- onto the same observable outputs.
+    if (exposedArgs s).isEmpty then
+      return { kind := FuncKind.noArgForm, kwNames := [] }
+    else
+      return { kind := FuncKind.oneArgForm, kwNames := ["text".toList] }
     -- impl-end
 
 prove_correct reconstructInvariance by
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -105,14 +105,11 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
+    -- ATTACK 11 (derived-not-literal route): the keyword-name view is COMPUTED
+    -- by dropping every name from the object's original Token kwargs() view,
+    -- rather than written as the literal []. Extensionally the gold pair.
     let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
+    let kwNames : List (List Char) := (["text".toList]).filter (fun _ => false)
     return { kind := kind, kwNames := kwNames }
     -- impl-end
 
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -105,14 +105,17 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
+    -- ATTACK 12 (redundant control-flow-effect split): branch on the object's
+    -- text and record the gold reconstruction pair on BOTH arms via different
+    -- syntactic paths. Verifies iff the spec is route-insensitive.
+    let mut kind : FuncKind := FuncKind.oneArgForm
+    let mut kwNames : List (List Char) := ["text".toList]
+    if s.text = [] then
+      kind := FuncKind.noArgForm
+      kwNames := []
+    else
+      kind := FuncKind.noArgForm
+      kwNames := List.nil
     return { kind := kind, kwNames := kwNames }
     -- impl-end
 
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,16 +105,11 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
-    return { kind := kind, kwNames := kwNames }
+    -- ATTACK 13 (Inhabited-default echo): ignore the object entirely and hand
+    -- back the structure's derived `default`. If the spec is satisfied by a
+    -- value never derived from the object, it constrains nothing.
+    return (default : InvarianceResult)
     -- impl-end
 
 prove_correct reconstructInvariance by
-  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs]
+  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs, default]
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,16 +105,15 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
+    -- ATTACK 14 (partial domain on the keyword view): nullary func everywhere,
+    -- but for the single object whose text is literally "text" the kwargs() view
+    -- still leaks its `text` keyword. A spec that quantifies weakly over the
+    -- object would miss this one input.
     let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
+    let kwNames : List (List Char) :=
+      if s.text = "text".toList then ["text".toList] else []
     return { kind := kind, kwNames := kwNames }
     -- impl-end
 
 prove_correct reconstructInvariance by
-  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs]
+  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs] <;> split <;> simp_all
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,13 +105,11 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
-    let kind : FuncKind := FuncKind.noArgForm
+    -- ATTACK 15 (ungrounded/nondeterministic choice): do not DECIDE the
+    -- reconstruction arity at all -- take it from an arbitrary inhabitant of
+    -- FuncKind. Under demonic choice a sound spec must reject this, since the
+    -- adversary may hand back oneArgForm.
+    let kind : FuncKind := (Classical.arbitrary FuncKind)
     let kwNames : List (List Char) := []
     return { kind := kind, kwNames := kwNames }
     -- impl-end
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,14 +105,12 @@
   ensures applyKw  out.kind s out.kwNames     = some s
   do
     -- impl-start
-    -- Select the object's reconstruction function arity and the keyword names
-    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
-    -- the object's own positional `args` and to its keyword arguments and demands
-    -- both reproduce the object. For an atomic object the positional `args` view
-    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
-    -- must expose no keyword names; only then do both reconstructions succeed.
+    -- ATTACK 16 (boundary on the keyword-name view): kwargs() exposes ONE
+    -- keyword whose name is the empty string -- distinct from exposing NO
+    -- keyword at all. `[[]] != []`, so a spec that conflates "no names" with
+    -- "one empty name" would wrongly accept this.
     let kind : FuncKind := FuncKind.noArgForm
-    let kwNames : List (List Char) := []
+    let kwNames : List (List Char) := [[]]
     return { kind := kind, kwNames := kwNames }
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_positive.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The positional arguments an atomic
--  string-valued object exposes is the observable result of an UNCHANGED
--  inspection of the object's structure; it is deep-modeled below as
--  `exposedArgs` and validated against the real object by axiom_check.py
--  (G-AX, A-reference), not borrowed from an asserted axiom. The operation
--  under specification — choosing the object's reconstruction function and its
--  keyword-argument view so that argument invariance holds — is modeled deeply
--  as the do block, so it is never axiomatized.)
-- axioms-end

-- pure-start
/- An atomic string-valued object: fully determined by its text content. Two
   such objects are equal exactly when their text agrees (so a reconstruction
   reproduces the object iff it reproduces the text). -/
structure StrObj where
  text : List Char
  deriving DecidableEq, Inhabited

/- The positional arguments an atomic object exposes for reconstruction. An
   atomic object has no constituent sub-arguments, so this is the empty list —
   `args == ()`. (An UNCHANGED structural inspection; A-reference, mapping.md.) -/
def exposedArgs (_ : StrObj) : List StrObj := []

/- The two distinguishable arities a reconstruction function `func` can have:

     * `noArgForm`  — `func` accepts a call with no positional and no keyword
       arguments, and then reproduces the object; supplying any positional or
       keyword argument makes the call fail.
     * `oneArgForm` — `func` requires the single text specifier: a positional
       call succeeds only when exactly one positional value is supplied, and a
       keyword call only when the lone `text` keyword is supplied.

   The behavior under specification turns on WHICH arity the object's `func`
   has, paired with which keyword names its `kwargs()` view exposes. -/
inductive FuncKind
  | noArgForm
  | oneArgForm
  deriving DecidableEq, Inhabited

/- Apply `func` positionally — the `func(*pos)` call. A `noArgForm` function
   accepts the call only when `pos` is empty (and then yields the object); a
   `oneArgForm` function accepts only a single positional value. The call fails
   (`none`) on any incompatible arity. -/
def applyPos (k : FuncKind) (s : StrObj) (pos : List StrObj) : Option StrObj :=
  match k with
  | .noArgForm  => if pos = [] then some s else none
  | .oneArgForm => match pos with
                   | [t] => some { text := t.text }
                   | _   => none

/- Apply `func` by keyword — the `func(**kwargs())` call, where `names` are the
   keyword names the `kwargs()` view supplies. A `noArgForm` function accepts
   the call only when no keyword names are supplied; a `oneArgForm` function
   accepts only the lone `text` keyword. The call fails (`none`) on any
   incompatible keyword set. -/
def applyKw (k : FuncKind) (s : StrObj) (names : List (List Char)) : Option StrObj :=
  match k with
  | .noArgForm  => if names = [] then some s else none
  | .oneArgForm => if names = ["text".toList] then some s else none

/- The reconstruction view selected for an object: the arity its reconstruction
   function `func` has (`kind`) and the keyword names its `kwargs()` view exposes
   (`kwNames`). Argument invariance is checked by APPLYING this `func` to the
   object's own positional `args` and to its keyword `kwargs()` and demanding
   both reproduce the object — so the verdict is *produced by* the recorded
   choices via `applyPos`/`applyKw`, never asserted as a free outcome value. -/
structure InvarianceResult where
  kind      : FuncKind
  kwNames   : List (List Char)
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An atomic string-valued object (a `Basic` subclass) must support argument
   invariance: applying its reconstruction function `func` to its own positional
   arguments `args` reproduces the object — `func(*args) == self` — and likewise
   applying `func` to the keyword arguments returned by `kwargs()` reproduces it
   — `func(**kwargs()) == self`. Both reconstruction identities must hold at the
   same time.

   The operation chooses, for the object, the signature of its reconstruction
   function `func` and the keyword names exposed by its `kwargs()` view. The
   behavior pinned here: applying that `func` to the object's own positional
   arguments and to its keyword arguments BOTH reproduce the object — neither
   reconstruction fails and neither yields a different object.

   `s` is a read-only object handle (not `mut`); the routine inspects it and
   mutates nothing (directive 5). -/
method reconstructInvariance (s : StrObj) return (out : InvarianceResult)
  ensures applyPos out.kind s (exposedArgs s) = some s
  ensures applyKw  out.kind s out.kwNames     = some s
  do
    -- impl-start
    -- Select the object's reconstruction function arity and the keyword names
    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
    -- the object's own positional `args` and to its keyword arguments and demands
    -- both reproduce the object. For an atomic object the positional `args` view
    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
    -- must expose no keyword names; only then do both reconstructions succeed.
    let kind : FuncKind := FuncKind.noArgForm
    let kwNames : List (List Char) := []
    return { kind := kind, kwNames := kwNames }
    -- impl-end

prove_correct reconstructInvariance by
  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs]
```

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all paths below absolute there). All 16 attacks + positive control + both shipped prepatch twins confirmed same_spec=True against the frozen Solution.lean via swebench_unified.markers.same_spec (velvet backend). Verifications run in concurrent batches of 4 as background jobs.

VERIFY COMMANDS (from swe-proof): bash scripts/lean_verify.sh <file>.lean

POSITIVE CONTROL (non-vacuity): ctl_positive.lean = byte-identical copy of the shipped Solution.lean -> exit 0. Spec is satisfiable, so the 12 rejections are real obligations, not a spec that rejects everything.

**PREPATCH REPRODUCED:** yes, both shipped twins, and independently re-encoded.
  ctl_Solution_prepatch.lean -> exit 1 (goal 'ensures_2: applyPos... = some s' reduces to False)
  ctl_Solution_prepatch_2.lean -> exit 1
  atk_1.lean (prepatch bug re-encoded: oneArgForm + kwNames=["text"]) -> exit 1, unsolved goal ensures_2 |- False
  atk_2.lean (half-fix re-encoded: noArgForm + kwNames=["text"]) -> exit 1

THE 12 REJECTED ATTACKS (exit 1 each) and WHY, spanning the required families: atk_1 prepatch bug (oneArgForm, ["text"]) -> ensures_2 |- False atk_2 half-fix (noArgForm, ["text"]) -> keyword identity fails atk_3 mirror half-fix (oneArgForm, []) -> positional identity fails atk_4 UNGROUNDED-ORACLE ECHO, the prior pass's named counterexample re-encoded verbatim (`return { viaArgs:= some s, viaKwargs:= some s }`) -> exit 1: 'viaArgs is not a field of structure InvarianceResult'. refinement.md §E's claim that the echo no longer type-checks is CONFIRMED mechanically. The record exposes only the two structural choices, so there is no free outcome value to assert. atk_5 PARTIAL DOMAIN (gold pair only when s.text = []; buggy otherwise) -> exit 1, residual goal 'if_neg: ¬s.text = [] |- False'.

The spec binds every object, not one. atk_6 BOUNDARY at the tested input (wrong exactly when s.text.length = 6, the length of 'foobar' the F2P test uses) -> exit 1, 'if_pos: s.text.length = 6 |- False'. atk_8 match-return route -> exit 1, but on a Velvet PARSER limitation ('Failed to parse an assertion without names: WPGen'), NOT on spec strength. Re-encoded faithfully as atk_10 with `if`, which then VERIFIED — so I did not count atk_8's rejection as spec strength. atk_9 ungrounded keyword set (noArgForm, ["bogus"] — a name that is not even a field) -> exit 1, ensures_1 |- False. atk_13 Inhabited-default echo (`return (default: InvarianceResult)`) -> exit 1: the derived default's kind/kwNames are opaque to the prover, so neither clause discharges.

A value not derived from the object does not satisfy the spec. atk_14 PARTIAL DOMAIN on the keyword view only (kwargs() leaks "text" for the single object whose text is literally "text") -> exit 1. atk_15 DEMONIC/nondeterministic arity (`Classical.arbitrary FuncKind` instead of a decided value) -> exit 1: goal 'match Classical.arbitrary FuncKind with...' unsolved (plus a noncomputable error). Under demonic choice the adversary may return oneArgForm, and the spec correctly refuses. atk_16 BOUNDARY on the name view ([[]] — one keyword whose name is the empty string, vs [] = no keyword) -> exit 1. The spec does not conflate 'no names' with 'one empty name'.

THE 4 VERIFYING ATTACKS (exit 0) AND THEIR EXECUTED RESOLVE RUNS — this is the mandatory step. Each verifying impl is extensionally the gold pair (noArgForm, []) reached by a DIFFERENT route, so I materialized four TEXTUALLY DISTINCT route-faithful patches (not one text copied four times), each generated by editing the real repo at base_commit a3475b3f9ac and taking `git diff`, each confirmed to `git apply --check` cleanly: atk_7  control-flow-effect: buggy pair in `let mut`, overwritten inside a branch guarded by the deep model `exposedArgs s = []`. Faithful patch: kwargs() builds the inherited Token keyword view then drops every name once `self.args == ()`. atk_10 branch on the A-reference deep model `(exposedArgs s).isEmpty`.

Faithful patch: kwargs() returns {} when `not self.args`. atk_11 kwNames COMPUTED by `.filter (fun _ => false)` rather than the literal []. Faithful patch: kwargs() dict-comprehension with an always-false guard. atk_12 redundant text-split whose both arms record the gold pair via different syntax. Faithful patch: kwargs() branches on `self.text == ''` returning {} / dict().

Resolve command (per attack, run 4-way concurrent, PYTHONPATH=src, anaconda3/envs/swebench-nagini python): run_resolve('sympy__sympy-22456', open('<n>.diff').read(), run_id='geq22456-atk<n>', retries=1) OBSERVED RESULTS — ALL FOUR RESOLVED: atk_7  RESOLVED=True applied=True F2P={'success': ['test_String'], 'failure': []} P2P failures=[] note=resolved atk_10 RESOLVED=True applied=True F2P={'success': ['test_String'], 'failure': []} P2P failures=[] note=resolved atk_11 RESOLVED=True applied=True F2P={'success': ['test_String'], 'failure': []} P2P failures=[] note=resolved atk_12 RESOLVED=True applied=True F2P={'success': ['test_String'], 'failure': []} P2P failures=[] note=resolved Also resolved faithful_gold.diff (the minimal func+kwargs refinement, no inert hunks): RESOLVED=True, F2P test_String success, 29/29 PASS_TO_PASS, patch_successfully_applied=True (JSON at resolve_faithful.json). So NO verifying impl's faithful patch fails to resolve.

RESOLVE-ORACLE DISCRIMINATION CONTROL (so the four True verdicts are not a rubber-stamping oracle): halffix.diff adds ONLY the `func` property and leaves Token.kwargs() intact — the refinement.md prepatch_2 half-fix. run_resolve -> RESOLVED=False, applied=True, F2P={'success': [], 'failure': ['test_String']}, note='patch did not resolve in 1 attempts (consistent — not flaky)'. The oracle applies the patch and still fails it, so it genuinely discriminates. (An empty patch was also tried and merely failed to apply — a weaker control, hence the half-fix.)

WHY NO WRONG IMPL CAN VERIFY (the structural reason, matching refinement.md §E). The observable output is only the record (kind, kwNames). ensures_2 `applyPos out.kind s (exposedArgs s) = some s` with `exposedArgs s = []` reduces to `applyPos out.kind s [] = some s`, which is `none` for oneArgForm — forcing kind = noArgForm. ensures_1 then reads `applyKw noArgForm s out.kwNames = some s`, which is `none` for any non-empty name list — forcing kwNames = []. The verifying set is therefore the SINGLETON (noArgForm, []), which is exactly the gold reconstruction signature. atk_5/atk_6/atk_14 confirm the forcing is per-object (no partial-domain escape) and atk_16/atk_9 confirm the keyword-set boundary is exact.

A-LEG AUDIT (refinement.md), the part G-CONF does not cover: Leg tags: A1 R, A2 R, A3 R, A4 A-reference + I, A5 I, A6 R. Every leg is R / A-reference / I; §B states there are NO A-consumed axioms and the axioms region indeed declares none (it is a comment block only). No kind-3 (inexpressible-changed-op) step: the operation that actually changed — the reconstruction-call semantics — is modeled DEEPLY as FuncKind + applyPos/applyKw rather than hidden behind an axiom about the callee under change. Confirmed by reading the frozen axioms region: it contains no `axiom`/`opaque` declaration to consume.

A4's A-reference correspondence (exposedArgs == real String.args == ()) VALIDATED EXECUTABLY on the unpatched repo at base_commit: ran the bundle's axiom_check.py in a fresh worktree -> exit 0, 'sound on 14 boundary + 20000 fuzz text inputs + subclass'. This is correctly scoped per SPEC_GUIDE §0.7: it asserts ONLY the UNCHANGED structural inspection (`text` stays in not_in_args so args is () both pre- and post-patch) and deliberately does NOT assert the changed reconstruction identities, which would raise on the unpatched tree. I independently attacked refinement.md §C's claim that the `String(Atom, Token)` base-class hunk (and the import/blank-line hunks) are INERT, since §C absorbs that hunk into A4's A-reference — if it were behavioural, absorbing it would be a hidden kind-3.

Probe probe_inert.py in a worktree carrying the faithful-minimal patch (func+kwargs only, NO Atom hunk) over String/QuotedString/Comment/Signifier x 6 boundary texts: args == () and kwargs() == {} and func(*args)==self and func(**kwargs())==self and is_Atom all hold for every case. `String.is_Atom` is already True prepatch via the class attribute `is_Atom = True` at ast.py, so the Atom base change adds no observable behaviour on anything the tests touch.

The full local test run of sympy/codegen/tests/test_ast.py with the test_patch applied and only the faithful-minimal patch gave 31 passed — and the corresponding faithful_gold.diff RESOLVED under the official harness. §C's inertness claim is CONFIRMED, so the absorption is legitimate. mapping.md correspondences spot-checked against the real code: Token.kwargs at ast.py:320 does return {k: getattr(self, k) for k in self.`__slots__`...} = {'text':...} for String (the oneArgForm keyword view), and String.`__slots__` = ('text',), not_in_args = ['text'] — matching mapping.md §1's pre-patch row.

CAVEAT / LIMITATION, disclosed. atk_8 (match-based return) could not be evaluated for spec strength: Velvet's WPGen failed to PARSE a `match` whose arms return, so its exit 1 reflects a backend syntax limitation, not the spec rejecting a wrong impl. I re-encoded the same semantics with `if` as atk_10, which parsed and verified, and resolved its faithful patch — so no evidence was lost, but atk_8's own rejection should not be counted as spec strength by the re-runner.

**BUNDLE-ADDRESSES-AUDITOR CHECK:** I grepped the bundle's *.md / *.py / meta.json for auditor-directed text. Nothing instructs me which verdict to record. verdict.md does frame roles with 'the agent's own verdict and notes are advisory context, not the source of truth for green'; I read that as a description of the machine re-run pipeline and it did not influence this verdict. I did NOT inherit the recorded prior G-EQ 'pass' or any prior role verdict — I re-encoded the prior pass's named counterexample (the viaArgs/viaKwargs echo, my atk_4) from scratch and re-measured it, and every claim above rests on a command I ran in this session.

**VERDICT:** SOUND. 16 same-spec attacks run (>=5 required), covering partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, nondeterministic-choice, and both prepatch legs; 12 rejected; the 4 that verify are the forced-unique gold pair and ALL FOUR of their materialized faithful patches were EXECUTED through the official harness and RESOLVED; positive control verifies; both prepatch twins reproduce; the resolve oracle was shown to discriminate via the half-fix control; and the only A-leg (the exposedArgs A-reference) plus the disputed inert-hunk absorption were both validated executably. No verify=>correct violation found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_7.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `ctl_positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation verified. 16 same-spec attacks were built and verified with scripts/lean_verify.sh; 12 were REJECTED (exit 1) and 4 verified (exit 0) — atk_7, atk_10, atk_11, atk_12. All four are NOT wrong impls: the two ensures clauses jointly force the unique output pair (out.kind, out.kwNames) = (noArgForm, []), and each of the four reaches exactly that pair by a different route (mutable-state overwrite guarded by the deep model; branch on exposedArgs; kwNames computed by a filter rather than the literal []; redundant text-split whose both arms land on the gold pair). I materialized a DISTINCT route-faithful refined patch for each of the four and ran every one through the official harness (run_resolve): all four RESOLVED (F2P test_String success, 29/29 PASS_TO_PASS, patch_successfully_applied=True). No verifying impl's faithful patch fails to resolve, so verify=>correct is not broken here.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_positive.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The positional arguments an atomic
--  string-valued object exposes is the observable result of an UNCHANGED
--  inspection of the object's structure; it is deep-modeled below as
--  `exposedArgs` and validated against the real object by axiom_check.py
--  (G-AX, A-reference), not borrowed from an asserted axiom. The operation
--  under specification — choosing the object's reconstruction function and its
--  keyword-argument view so that argument invariance holds — is modeled deeply
--  as the do block, so it is never axiomatized.)
-- axioms-end

-- pure-start
/- An atomic string-valued object: fully determined by its text content. Two
   such objects are equal exactly when their text agrees (so a reconstruction
   reproduces the object iff it reproduces the text). -/
structure StrObj where
  text : List Char
  deriving DecidableEq, Inhabited

/- The positional arguments an atomic object exposes for reconstruction. An
   atomic object has no constituent sub-arguments, so this is the empty list —
   `args == ()`. (An UNCHANGED structural inspection; A-reference, mapping.md.) -/
def exposedArgs (_ : StrObj) : List StrObj := []

/- The two distinguishable arities a reconstruction function `func` can have:

     * `noArgForm`  — `func` accepts a call with no positional and no keyword
       arguments, and then reproduces the object; supplying any positional or
       keyword argument makes the call fail.
     * `oneArgForm` — `func` requires the single text specifier: a positional
       call succeeds only when exactly one positional value is supplied, and a
       keyword call only when the lone `text` keyword is supplied.

   The behavior under specification turns on WHICH arity the object's `func`
   has, paired with which keyword names its `kwargs()` view exposes. -/
inductive FuncKind
  | noArgForm
  | oneArgForm
  deriving DecidableEq, Inhabited

/- Apply `func` positionally — the `func(*pos)` call. A `noArgForm` function
   accepts the call only when `pos` is empty (and then yields the object); a
   `oneArgForm` function accepts only a single positional value. The call fails
   (`none`) on any incompatible arity. -/
def applyPos (k : FuncKind) (s : StrObj) (pos : List StrObj) : Option StrObj :=
  match k with
  | .noArgForm  => if pos = [] then some s else none
  | .oneArgForm => match pos with
                   | [t] => some { text := t.text }
                   | _   => none

/- Apply `func` by keyword — the `func(**kwargs())` call, where `names` are the
   keyword names the `kwargs()` view supplies. A `noArgForm` function accepts
   the call only when no keyword names are supplied; a `oneArgForm` function
   accepts only the lone `text` keyword. The call fails (`none`) on any
   incompatible keyword set. -/
def applyKw (k : FuncKind) (s : StrObj) (names : List (List Char)) : Option StrObj :=
  match k with
  | .noArgForm  => if names = [] then some s else none
  | .oneArgForm => if names = ["text".toList] then some s else none

/- The reconstruction view selected for an object: the arity its reconstruction
   function `func` has (`kind`) and the keyword names its `kwargs()` view exposes
   (`kwNames`). Argument invariance is checked by APPLYING this `func` to the
   object's own positional `args` and to its keyword `kwargs()` and demanding
   both reproduce the object — so the verdict is *produced by* the recorded
   choices via `applyPos`/`applyKw`, never asserted as a free outcome value. -/
structure InvarianceResult where
  kind      : FuncKind
  kwNames   : List (List Char)
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An atomic string-valued object (a `Basic` subclass) must support argument
   invariance: applying its reconstruction function `func` to its own positional
   arguments `args` reproduces the object — `func(*args) == self` — and likewise
   applying `func` to the keyword arguments returned by `kwargs()` reproduces it
   — `func(**kwargs()) == self`. Both reconstruction identities must hold at the
   same time.

   The operation chooses, for the object, the signature of its reconstruction
   function `func` and the keyword names exposed by its `kwargs()` view. The
   behavior pinned here: applying that `func` to the object's own positional
   arguments and to its keyword arguments BOTH reproduce the object — neither
   reconstruction fails and neither yields a different object.

   `s` is a read-only object handle (not `mut`); the routine inspects it and
   mutates nothing (directive 5). -/
method reconstructInvariance (s : StrObj) return (out : InvarianceResult)
  ensures applyPos out.kind s (exposedArgs s) = some s
  ensures applyKw  out.kind s out.kwNames     = some s
  do
    -- impl-start
    -- Select the object's reconstruction function arity and the keyword names
    -- its `kwargs()` view exposes. The postcondition then APPLIES that `func` to
    -- the object's own positional `args` and to its keyword arguments and demands
    -- both reproduce the object. For an atomic object the positional `args` view
    -- is empty, so `func` must accept a no-argument call, and the `kwargs()` view
    -- must expose no keyword names; only then do both reconstructions succeed.
    let kind : FuncKind := FuncKind.noArgForm
    let kwNames : List (List Char) := []
    return { kind := kind, kwNames := kwNames }
    -- impl-end

prove_correct reconstructInvariance by
  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs]
```

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all paths below absolute there). All 16 attacks + positive control + both shipped prepatch twins confirmed same_spec=True against the frozen Solution.lean via swebench_unified.markers.same_spec (velvet backend). Verifications run in concurrent batches of 4 as background jobs.

VERIFY COMMANDS (from swe-proof): bash scripts/lean_verify.sh <file>.lean

POSITIVE CONTROL (non-vacuity): ctl_positive.lean = byte-identical copy of the shipped Solution.lean -> exit 0. Spec is satisfiable, so the 12 rejections are real obligations, not a spec that rejects everything.

**PREPATCH REPRODUCED:** yes, both shipped twins, and independently re-encoded.
  ctl_Solution_prepatch.lean -> exit 1 (goal 'ensures_2: applyPos... = some s' reduces to False)
  ctl_Solution_prepatch_2.lean -> exit 1
  atk_1.lean (prepatch bug re-encoded: oneArgForm + kwNames=["text"]) -> exit 1, unsolved goal ensures_2 |- False
  atk_2.lean (half-fix re-encoded: noArgForm + kwNames=["text"]) -> exit 1

THE 12 REJECTED ATTACKS (exit 1 each) and WHY, spanning the required families: atk_1 prepatch bug (oneArgForm, ["text"]) -> ensures_2 |- False atk_2 half-fix (noArgForm, ["text"]) -> keyword identity fails atk_3 mirror half-fix (oneArgForm, []) -> positional identity fails atk_4 UNGROUNDED-ORACLE ECHO, the prior pass's named counterexample re-encoded verbatim (`return { viaArgs:= some s, viaKwargs:= some s }`) -> exit 1: 'viaArgs is not a field of structure InvarianceResult'. refinement.md §E's claim that the echo no longer type-checks is CONFIRMED mechanically. The record exposes only the two structural choices, so there is no free outcome value to assert. atk_5 PARTIAL DOMAIN (gold pair only when s.text = []; buggy otherwise) -> exit 1, residual goal 'if_neg: ¬s.text = [] |- False'.

The spec binds every object, not one. atk_6 BOUNDARY at the tested input (wrong exactly when s.text.length = 6, the length of 'foobar' the F2P test uses) -> exit 1, 'if_pos: s.text.length = 6 |- False'. atk_8 match-return route -> exit 1, but on a Velvet PARSER limitation ('Failed to parse an assertion without names: WPGen'), NOT on spec strength. Re-encoded faithfully as atk_10 with `if`, which then VERIFIED — so I did not count atk_8's rejection as spec strength. atk_9 ungrounded keyword set (noArgForm, ["bogus"] — a name that is not even a field) -> exit 1, ensures_1 |- False. atk_13 Inhabited-default echo (`return (default: InvarianceResult)`) -> exit 1: the derived default's kind/kwNames are opaque to the prover, so neither clause discharges.

A value not derived from the object does not satisfy the spec. atk_14 PARTIAL DOMAIN on the keyword view only (kwargs() leaks "text" for the single object whose text is literally "text") -> exit 1. atk_15 DEMONIC/nondeterministic arity (`Classical.arbitrary FuncKind` instead of a decided value) -> exit 1: goal 'match Classical.arbitrary FuncKind with...' unsolved (plus a noncomputable error). Under demonic choice the adversary may return oneArgForm, and the spec correctly refuses. atk_16 BOUNDARY on the name view ([[]] — one keyword whose name is the empty string, vs [] = no keyword) -> exit 1. The spec does not conflate 'no names' with 'one empty name'.

THE 4 VERIFYING ATTACKS (exit 0) AND THEIR EXECUTED RESOLVE RUNS — this is the mandatory step. Each verifying impl is extensionally the gold pair (noArgForm, []) reached by a DIFFERENT route, so I materialized four TEXTUALLY DISTINCT route-faithful patches (not one text copied four times), each generated by editing the real repo at base_commit a3475b3f9ac and taking `git diff`, each confirmed to `git apply --check` cleanly: atk_7  control-flow-effect: buggy pair in `let mut`, overwritten inside a branch guarded by the deep model `exposedArgs s = []`. Faithful patch: kwargs() builds the inherited Token keyword view then drops every name once `self.args == ()`. atk_10 branch on the A-reference deep model `(exposedArgs s).isEmpty`.

Faithful patch: kwargs() returns {} when `not self.args`. atk_11 kwNames COMPUTED by `.filter (fun _ => false)` rather than the literal []. Faithful patch: kwargs() dict-comprehension with an always-false guard. atk_12 redundant text-split whose both arms record the gold pair via different syntax. Faithful patch: kwargs() branches on `self.text == ''` returning {} / dict().

Resolve command (per attack, run 4-way concurrent, PYTHONPATH=src, anaconda3/envs/swebench-nagini python): run_resolve('sympy__sympy-22456', open('<n>.diff').read(), run_id='geq22456-atk<n>', retries=1) OBSERVED RESULTS — ALL FOUR RESOLVED: atk_7  RESOLVED=True applied=True F2P={'success': ['test_String'], 'failure': []} P2P failures=[] note=resolved atk_10 RESOLVED=True applied=True F2P={'success': ['test_String'], 'failure': []} P2P failures=[] note=resolved atk_11 RESOLVED=True applied=True F2P={'success': ['test_String'], 'failure': []} P2P failures=[] note=resolved atk_12 RESOLVED=True applied=True F2P={'success': ['test_String'], 'failure': []} P2P failures=[] note=resolved Also resolved faithful_gold.diff (the minimal func+kwargs refinement, no inert hunks): RESOLVED=True, F2P test_String success, 29/29 PASS_TO_PASS, patch_successfully_applied=True (JSON at resolve_faithful.json). So NO verifying impl's faithful patch fails to resolve.

RESOLVE-ORACLE DISCRIMINATION CONTROL (so the four True verdicts are not a rubber-stamping oracle): halffix.diff adds ONLY the `func` property and leaves Token.kwargs() intact — the refinement.md prepatch_2 half-fix. run_resolve -> RESOLVED=False, applied=True, F2P={'success': [], 'failure': ['test_String']}, note='patch did not resolve in 1 attempts (consistent — not flaky)'. The oracle applies the patch and still fails it, so it genuinely discriminates. (An empty patch was also tried and merely failed to apply — a weaker control, hence the half-fix.)

WHY NO WRONG IMPL CAN VERIFY (the structural reason, matching refinement.md §E). The observable output is only the record (kind, kwNames). ensures_2 `applyPos out.kind s (exposedArgs s) = some s` with `exposedArgs s = []` reduces to `applyPos out.kind s [] = some s`, which is `none` for oneArgForm — forcing kind = noArgForm. ensures_1 then reads `applyKw noArgForm s out.kwNames = some s`, which is `none` for any non-empty name list — forcing kwNames = []. The verifying set is therefore the SINGLETON (noArgForm, []), which is exactly the gold reconstruction signature. atk_5/atk_6/atk_14 confirm the forcing is per-object (no partial-domain escape) and atk_16/atk_9 confirm the keyword-set boundary is exact.

A-LEG AUDIT (refinement.md), the part G-CONF does not cover: Leg tags: A1 R, A2 R, A3 R, A4 A-reference + I, A5 I, A6 R. Every leg is R / A-reference / I; §B states there are NO A-consumed axioms and the axioms region indeed declares none (it is a comment block only). No kind-3 (inexpressible-changed-op) step: the operation that actually changed — the reconstruction-call semantics — is modeled DEEPLY as FuncKind + applyPos/applyKw rather than hidden behind an axiom about the callee under change. Confirmed by reading the frozen axioms region: it contains no `axiom`/`opaque` declaration to consume.

A4's A-reference correspondence (exposedArgs == real String.args == ()) VALIDATED EXECUTABLY on the unpatched repo at base_commit: ran the bundle's axiom_check.py in a fresh worktree -> exit 0, 'sound on 14 boundary + 20000 fuzz text inputs + subclass'. This is correctly scoped per SPEC_GUIDE §0.7: it asserts ONLY the UNCHANGED structural inspection (`text` stays in not_in_args so args is () both pre- and post-patch) and deliberately does NOT assert the changed reconstruction identities, which would raise on the unpatched tree. I independently attacked refinement.md §C's claim that the `String(Atom, Token)` base-class hunk (and the import/blank-line hunks) are INERT, since §C absorbs that hunk into A4's A-reference — if it were behavioural, absorbing it would be a hidden kind-3.

Probe probe_inert.py in a worktree carrying the faithful-minimal patch (func+kwargs only, NO Atom hunk) over String/QuotedString/Comment/Signifier x 6 boundary texts: args == () and kwargs() == {} and func(*args)==self and func(**kwargs())==self and is_Atom all hold for every case. `String.is_Atom` is already True prepatch via the class attribute `is_Atom = True` at ast.py, so the Atom base change adds no observable behaviour on anything the tests touch.

The full local test run of sympy/codegen/tests/test_ast.py with the test_patch applied and only the faithful-minimal patch gave 31 passed — and the corresponding faithful_gold.diff RESOLVED under the official harness. §C's inertness claim is CONFIRMED, so the absorption is legitimate. mapping.md correspondences spot-checked against the real code: Token.kwargs at ast.py:320 does return {k: getattr(self, k) for k in self.`__slots__`...} = {'text':...} for String (the oneArgForm keyword view), and String.`__slots__` = ('text',), not_in_args = ['text'] — matching mapping.md §1's pre-patch row.

CAVEAT / LIMITATION, disclosed. atk_8 (match-based return) could not be evaluated for spec strength: Velvet's WPGen failed to PARSE a `match` whose arms return, so its exit 1 reflects a backend syntax limitation, not the spec rejecting a wrong impl. I re-encoded the same semantics with `if` as atk_10, which parsed and verified, and resolved its faithful patch — so no evidence was lost, but atk_8's own rejection should not be counted as spec strength by the re-runner.

**BUNDLE-ADDRESSES-AUDITOR CHECK:** I grepped the bundle's *.md / *.py / meta.json for auditor-directed text. Nothing instructs me which verdict to record. verdict.md does frame roles with 'the agent's own verdict and notes are advisory context, not the source of truth for green'; I read that as a description of the machine re-run pipeline and it did not influence this verdict. I did NOT inherit the recorded prior G-EQ 'pass' or any prior role verdict — I re-encoded the prior pass's named counterexample (the viaArgs/viaKwargs echo, my atk_4) from scratch and re-measured it, and every claim above rests on a command I ran in this session.

**VERDICT:** SOUND. 16 same-spec attacks run (>=5 required), covering partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, nondeterministic-choice, and both prepatch legs; 12 rejected; the 4 that verify are the forced-unique gold pair and ALL FOUR of their materialized faithful patches were EXECUTED through the official harness and RESOLVED; positive control verifies; both prepatch twins reproduce; the resolve oracle was shown to discriminate via the half-fix control; and the only A-leg (the exposedArgs A-reference) plus the disputed inert-hunk absorption were both validated executably. No verify=>correct violation found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL(2) faithfulness-break attack on sympy__sympy-22456/velvet. No divergence found between the modeled function and the real repo; verdict FAITHFUL.

**REFERENCE DISCIPLINE.** Reference for the modeled (changed) behavior = worktree at base a3475b3f9a with patch.diff APPLIED (git diff confirmed byte-equal to instance.json's gold patch). Base tree (clean a3475b3f9a) used ONLY for (a) the UNCHANGED callee the A-reference models (String.args) and (b) validating the oneArgForm branch, which models the PRE-patch signature by construction (mapping.md §1). I did not report the patch delta as divergence.

**SPEC-REGION IDENTITY.** markers.same_spec(Solution.lean, twin, VelvetBackend().language) = True for BOTH Solution_prepatch.lean and Solution_prepatch_2.lean. diff confirms the twins differ only inside impl-start/impl-end (the two `let` bindings + comments); axioms/pure/pre/post regions and both `ensures` lines are byte-identical.

**WHAT THE SPEC CLAIMS.** Two ensures over the impl's only outputs (out.kind, out.kwNames):
  (C1) applyPos out.kind s (exposedArgs s) = some s
  (C2) applyKw  out.kind s out.kwNames     = some s
No axioms are consumed (axioms region is comment-only); exposedArgs/applyPos/applyKw are deep models.

DIFFERENTIAL EXECUTED (the faithfulness test proper). I transliterated the pure region verbatim to Python (atk2f_diff22456.py) and diffed model vs. real object call outcomes, sweeping BOTH FuncKind branches and SIX recordable kwNames sets ([], ['text'], ['bogus'], ['text','bogus'], ['Text'], ['']) over 2010 texts x 3 classes (String/QuotedString/Comment): boundary ('', 'text', 300-char, whitespace, chr(0), chr(0x10FFFF), astral/CJK) + seeded fuzz. Mapping: raises TypeError/ValueError <-> none; reproduces self <-> some s.
  - noArgForm vs PATCHED tree: 42210 checks, 0 divergences.
  - oneArgForm vs BASE tree: 42210 checks, 0 divergences.
Notably the non-trivial oneArgForm positional branch `some {text:= t.text}` was confirmed: base String('foobar').func(String('abc')) -> String('abc'), text 'abc' (Token.`__new__` single-instance passthrough), matching the model rather than `some s`. Arity/keyword failure modes also match: 2 positional -> ValueError 'Too many arguments' -> none; text+bogus -> ValueError 'Unknown keyword arguments' -> none; noArgForm + any positional or any keyword -> TypeError -> none.

A-REFERENCE (exposedArgs = []) IS GENUINELY UNCHANGED. String.args == () on BOTH trees for String/QuotedString/Comment over 20k+ inputs, because text stays in not_in_args (ast.py:898) so it is never passed to the Basic constructor. Legitimately G-AX-able (patch does not touch it). axiom_check.py run against the UNPATCHED base tree: exit 0, 14 boundary + 20000 fuzz. Repo-wide subclass sweep (full sympy import): String has exactly 2 subclasses, both with `__slots__`=('text',) and not_in_args=['text'] — no subclass escapes the exposedArgs=[] model.

VALUE-INSENSITIVITY OF applyKw IS NOT OVER-STRENGTH. applyKw keys only on the keyword NAME SET, ignoring values. mapping.md §2 documents this explicitly and it is sound for the modeled call, since kwargs() supplies the object's own fields — confirmed: func(**kwargs()) == self on both trees.

NOT TOO STRONG / NOT VACUOUS. The two clauses force exactly one verifying pair, and that pair is the gold signature (func:= lambda: self, kwargs():= {}) — not something stronger than the patch delivers. Rival sweep, all rejected with genuine `⊢ False` postcondition goals (not syntax errors — diffs inspected):
  (oneArgForm, [])            -> exit 1
  (oneArgForm, ['text'])      -> exit 1  (== Solution_prepatch.lean; fails ensures_2/C1)
  (noArgForm,  ['text'])      -> exit 1  (== Solution_prepatch_2.lean; fails ensures_1/C2)
  (noArgForm,  ['bogus'])     -> exit 1
Gold Solution.lean verifies: lean_verify.sh exit 0. Anti-echo holds structurally: InvarianceResult carries no viaArgs/viaKwargs outcome field, so the verdict cannot be asserted — it is produced by applyPos/applyKw over the recorded choices.

**ORACLE CORROBORATION.** Base tree reproduces the exact issue: String('foobar').func(*args) raises TypeError "No value for 'text' given and attribute has no default" while the keyword identity already passes — precisely the asymmetry the problem statement and the added F2P line assert. Patched tree: full test_ast.py 31 passed (F2P test_String + all 27 P2P). Bundle checkers: axiom_check.py exit 0 on base; conformance_check.py exit 0 on patched, 100010 inputs seed=22456, 0 disagreements.

**CONCLUSION.** I could not construct any input on which the modeled function disagrees with the real callee under the documented Lean<->Python bijection, on either branch of FuncKind or any recordable kwNames. No diverging input to cite, so no UNFAITHFUL finding is available. Residual (not a faithfulness defect, noted for the record): the model abstracts arity/keyword-set compatibility rather than reproducing sympy's exception TYPES (TypeError vs ValueError), which mapping.md §2 collapses to `none` by design; and lone-surrogate texts ('\ud800') have no Lean Char preimage but were checked anyway and behave identically.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE / RELAXATION. No documented relaxation in this bundle, so nothing to re-derive or inherit: meta.json has NO `relaxed_leakage` key (top-level keys = additional_change_sites, axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, object_modeling, pbt_audit, prepatch_variants, repo, schema_version, spec_provenance, version) and `find sympy__sympy-22456 -iname '*relax*'` returns empty. The only 'relaxed' substrings in meta.json are inside a PRIOR G-PANEL-3 gate note recording that same absence -- a gate record, not an instruction, and I re-derived everything below from the artifacts rather than inheriting it. Reviewer-directed-content scan came back clean: leakage.reviewer_directed() == [] on Solution.lean, mapping.md, refinement.md and patch.diff, and a manual grep for judge-addressed imperatives (you should/must record, 'the honest verdict', submit NO-LEAKAGE/LEAKAGE, do not flag, dear reviewer/auditor/panel) over Solution.lean, mapping.md, refinement.md, properties.py, axiom_check.py, conformance_check.py and verdict.md found no file telling me how to record. The only 'attacker' hits are properties.py:526,535 describing PBT rival coverage, not addressing me.

SPEC-REGION BYTE-IDENTITY (as instructed). markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True and same_spec(Solution.lean, Solution_prepatch_2.lean, VelvetBackend) = True. Independently recomputed sha256(spec_view) = 93cf20e42148acbe60c8387da9cda8f9f89298a06702dfd12c40c0ce29e84be3, matching the G-HYGIENE-recorded region_hashes.spec_view exactly, so the view I judged is the shipped one and the three variants differ only inside the elided impl region.

DISCRIMINATOR IS LIVE (my own runs, not the recorded gates). Under a fresh mktemp -d via scripts/lean_verify.sh (480s cap): Solution.lean exit=0; Solution_prepatch.lean exit=1 with `case ensures_2: applyPos out.kind s (exposedArgs s) = some s... |- False`; Solution_prepatch_2.lean exit=1 with `case ensures_1: applyKw out.kind s out.kwNames = some s... |- False`. So each of the two postconditions is separately load-bearing and the spec really does reject both the original arity bug and the kwargs half-fix.

**PUBLIC BASELINE.** problem_statement (hints_text is empty, len 0, so nothing to accidentally screen against) names verbatim: the atomic-string `String` class of `codegen.ast`, `expr.func`, `expr.args`, `expr.kwargs()`, both identities `expr.func(*expr.args) == expr` and `expr.func(**expr.kwargs()) == expr`, and that `String` is a `Basic` subclass which must satisfy the former. The spec view's two ensures clauses are exactly those two identities and nothing more.

WHAT THE GOLD EDIT ACTUALLY IS, AND THAT NONE OF ITS MECHANISM APPEARS. Gold added lines: `from sympy.core.expr import Expr, Atom`; `class String(Atom, Token):`; `def kwargs(self, exclude = (), apply = None): return {}`; `#to be removed when Atom is given a suitable func`; `@property def func(self): return lambda: self`. Checked each mechanism token against the spec view: Atom=absent, lambda=absent, property=absent, Token=absent, String=absent, QuotedString=absent, BreakToken=absent, Expr=absent, `_sympystr`=absent, not_in_args=absent, is_Atom=absent, `__slots__`=absent, `_construct_text`/`_construct_iterable`=absent.

No changed gold line survives normalization into the view (zero hits at the >=8-char threshold), no diff marker is present, and no patched path leaks (`sympy/codegen/ast.py`, `ast.py`, even the bare token `codegen` are all absent -- the view is strictly MORE abstract than the public problem_statement, which does name codegen.ast String). Narration regex found 0 hits in the view; the 'buggy'/'pre-image skeleton' prose lives only in the prepatch variants' impl regions (elided) and in mapping.md/refinement.md, which are audit artifacts -- eval/dataset.py ships only task.spec_view, never mapping.md or refinement.md. Mechanical cross-check: leakage.screen(...) passes with hard_failures=[] and warnings=[].

RE-DERIVED THE DISCRIMINATOR FROM problem_statement ALONE (this is what makes it non-leakage rather than merely unnamed). The spec view offers `FuncKind.noArgForm` vs `oneArgForm` and a free `out.kwNames`, forcing the solver to pick. I confirmed the pick is a problem_statement-only derivation, using only PRE-patch facts I measured on a fresh base-commit worktree (git worktree at a3475b3f9ac662cd425157dd3bdb93ad7111c090, mpmath supplied out-of-tree): `String('foobar').args == ()`, `String('foobar').kwargs() == {'text': 'foobar'}`, `st.func(*st.args)` raises TypeError "No value for 'text' given", `st.func(**st.kwargs()) == st` is True, `is_Atom` is already True pre-patch, and the docstring already reads "Atomic object which is not an expression" at line 875 with `not_in_args = ['text']` at 898. Hence: args==() is public and UNCHANGED by the patch (the A-reference `exposedArgs = []`), so the problem_statement's own demand `func(*args) == expr` forces func to be callable with zero positional arguments and return self -- i.e. noArgForm is derivable from the statement plus the unpatched tree, not disclosed.

Given a nullary func, the statement's other named identity `func(**kwargs()) == expr` forces the keyword set empty, i.e. kwNames = [] -- again a derivation, not a disclosure. The literal `"text"` inside applyKw's oneArgForm branch is the PRE-patch kwargs() key (measured above) and the pre-patch `__slots__`/docstring field name; it characterizes the pre-state the statement already describes as current behavior, and the edit's content is that kwargs() becomes {} -- which the view never states. Nothing in the view tells the solver to mix in Atom, to add a `func` property, or to override `kwargs`; the whole Python mechanism remains to be invented.

**STRIP TEST.** Removing the narrative comments leaves the two ensures clauses, which still reject the pre-patch impl (measured: prepatch exit=1 on ensures_2, prepatch_2 exit=1 on ensures_1), so the clauses -- not the prose -- carry the discrimination; the prose is behavioral description of the call semantics, adding no edit-localization.

**CORE GATES LEANED ON.** Confirmed independently rather than read off meta.json: same_spec byte-identity (recomputed), spec_view hash (recomputed, matches G-HYGIENE), gold-verifies/prepatch-fail discrimination (re-ran all three Lean files myself), leakage.screen clean (re-ran). Recorded gate statuses G-AX/G-CONF/G-DIFF/G-GOLD/G-HYGIENE/G-INTEGRITY/G-LEAK/G-MUT/G-EQ are all pass and consistent with what I measured.

**CONCLUSION:** the spec view discloses only what the public problem_statement already discloses (the two invariance identities, the atomic-string object, its text field) plus a pre-patch, patch-invariant structural fact (args == ()) that G-AX legitimately validates on the unpatched tree. The gold edit's mechanism is fully absent and the answer must be re-derived. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

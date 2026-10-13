# P2 adversarial audit — sympy__sympy-20590

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1_prepatch.lean`, `atk2_open_core.lean`, `atk3_constant.lean`, `atk4_partial_domain.lean`, `atk5_flip.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk6_boundary_prepend.lean`, `atk7_drop_append.lean`, `atk8_ifelse.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,9 +92,11 @@
   ensures out = true
   do
     -- impl-start
-    -- The shared contributing type pins a closed instance layout (declares an
-    -- empty closed slot set, adding no named slots and no open namespace).
-    return true
+    -- Pre-image skeleton: the shared contributing type leaves its instance
+    -- layout OPEN — it declares no closed slot set of its own, so an instance
+    -- built through it acquires an open namespace. The frozen spec requires the
+    -- closed-layout flag, so prove_correct MUST fail here.
+    return false
     -- impl-end
 
 /- Whether an instance of the value type carries an open per-instance
@@ -111,7 +113,7 @@
   ensures allClosedLayout others = true → out = false
   do
     -- impl-start
-    let trait := true
+    let trait := false
     let chain : List Bool := others ++ [trait]
     return instanceAdmitsNamespace chain
     -- impl-end
@@ -128,7 +130,7 @@
   ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
   do
     -- impl-start
-    let trait := true
+    let trait := false
     let chain : List Bool := others ++ [trait]
     return bindUndeclared chain
     -- impl-end
```

Attack 2 — `atk2_open_core.lean` → rejected (same spec, does not verify — good)

```diff
@@ -111,7 +111,7 @@
   ensures allClosedLayout others = true → out = false
   do
     -- impl-start
-    let trait := true
+    let trait := false
     let chain : List Bool := others ++ [trait]
     return instanceAdmitsNamespace chain
     -- impl-end
@@ -128,7 +128,7 @@
   ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
   do
     -- impl-start
-    let trait := true
+    let trait := false
     let chain : List Bool := others ++ [trait]
     return bindUndeclared chain
     -- impl-end
```

Attack 3 — `atk3_constant.lean` → rejected (same spec, does not verify — good)

```diff
@@ -111,9 +111,7 @@
   ensures allClosedLayout others = true → out = false
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return instanceAdmitsNamespace chain
+    return false
     -- impl-end
 
 /- The outcome of binding an attribute name the value type did not pre-declare,
@@ -128,9 +126,7 @@
   ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return bindUndeclared chain
+    return Except.error AttrError.bindingRefused
     -- impl-end
 
 prove_correct mixinPinsClosedLayout by
```

Attack 4 — `atk4_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -111,9 +111,9 @@
   ensures allClosedLayout others = true → out = false
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return instanceAdmitsNamespace chain
+    match others with
+    | [] => false
+    | _  => true
     -- impl-end
 
 /- The outcome of binding an attribute name the value type did not pre-declare,
@@ -128,9 +128,9 @@
   ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return bindUndeclared chain
+    match others with
+    | [] => Except.error AttrError.bindingRefused
+    | _  => Except.ok true
     -- impl-end
 
 prove_correct mixinPinsClosedLayout by
```

Attack 5 — `atk5_flip.lean` → rejected (same spec, does not verify — good)

```diff
@@ -111,9 +111,8 @@
   ensures allClosedLayout others = true → out = false
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return instanceAdmitsNamespace chain
+    let chain : List Bool := others ++ [true]
+    return allClosedLayout chain
     -- impl-end
 
 /- The outcome of binding an attribute name the value type did not pre-declare,
@@ -128,9 +127,8 @@
   ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return bindUndeclared chain
+    let chain : List Bool := others ++ [true]
+    return if allClosedLayout chain then Except.ok true else Except.error AttrError.bindingRefused
     -- impl-end
 
 prove_correct mixinPinsClosedLayout by
```

Attack 6 — `atk6_boundary_prepend.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -112,7 +112,7 @@
   do
     -- impl-start
     let trait := true
-    let chain : List Bool := others ++ [trait]
+    let chain : List Bool := trait :: others
     return instanceAdmitsNamespace chain
     -- impl-end
 
@@ -129,7 +129,7 @@
   do
     -- impl-start
     let trait := true
-    let chain : List Bool := others ++ [trait]
+    let chain : List Bool := trait :: others
     return bindUndeclared chain
     -- impl-end
 
@@ -138,8 +138,8 @@
 
 prove_correct coreInstanceAdmitsNamespace by
   loom_solve
-  all_goals simp_all [instanceAdmitsNamespace, allClosedLayout_append, allClosedLayout]
+  all_goals simp_all [instanceAdmitsNamespace, allClosedLayout_append, allClosedLayout, Bool.and_comm]
 
 prove_correct coreBindUndeclared by
   loom_solve
-  all_goals simp_all [bindUndeclared, allClosedLayout_append, allClosedLayout]
+  all_goals simp_all [bindUndeclared, allClosedLayout_append, allClosedLayout, Bool.and_comm]
```

Attack 7 — `atk7_drop_append.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -111,9 +111,7 @@
   ensures allClosedLayout others = true → out = false
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return instanceAdmitsNamespace chain
+    return instanceAdmitsNamespace others
     -- impl-end
 
 /- The outcome of binding an attribute name the value type did not pre-declare,
@@ -128,9 +126,7 @@
   ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return bindUndeclared chain
+    return bindUndeclared others
     -- impl-end
 
 prove_correct mixinPinsClosedLayout by
```

Attack 8 — `atk8_ifelse.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -111,9 +111,11 @@
   ensures allClosedLayout others = true → out = false
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return instanceAdmitsNamespace chain
+    let chain : List Bool := others ++ [true]
+    if allClosedLayout chain then
+      return false
+    else
+      return true
     -- impl-end
 
 /- The outcome of binding an attribute name the value type did not pre-declare,
@@ -128,9 +130,11 @@
   ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
   do
     -- impl-start
-    let trait := true
-    let chain : List Bool := others ++ [trait]
-    return bindUndeclared chain
+    let chain : List Bool := others ++ [true]
+    if allClosedLayout chain then
+      return Except.error AttrError.bindingRefused
+    else
+      return Except.ok true
     -- impl-end
 
 prove_correct mixinPinsClosedLayout by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: every modeled operation is a straight-line pure
   computation over the closed-layout flag chain and always terminates, so a
   diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the exact-pin postconditions
   vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behavior under specification — whether an instance of
   a value type carries an open per-instance namespace, and the consequence for
   binding an undeclared attribute name — is modeled DEEPLY in the `pure` region
   (`allClosedLayout`, `instanceAdmitsNamespace`, `bindUndeclared`). The rule
   relating a type's layout declarations to the presence of an open namespace is
   a property of the host runtime's object model, validated against the real
   interpreter out of band (mapping.md §3, axiom_check.py / G-AX); it is NOT
   axiomatized as a callee. -/
-- axioms-end

-- pure-start
/- The single way binding an undeclared attribute name can be refused: the
   instance carries no open namespace to absorb it, so the binding is rejected
   rather than silently stored. This is the only outcome the desired behavior
   distinguishes from success. -/
inductive AttrError where
  | bindingRefused
  deriving DecidableEq

/- An instance is built from a CHAIN of contributing types (its resolution
   order, with the universal root — which never contributes a namespace —
   excluded). Each entry is a flag: `true` iff that type pins a closed instance
   layout (declares a closed set of attribute slots and so contributes no
   open per-instance namespace of its own); `false` iff it leaves its layout
   open.

   `allClosedLayout` is `true` iff EVERY type in the chain pins a closed layout.
   Front-recursive over the chain so a single unfold is available per step (the
   Velvet fold pattern): the head must pin a closed layout and so must the
   tail. -/
def allClosedLayout : List Bool → Bool
  | []      => true
  | f :: fs => f && allClosedLayout fs

@[grind] lemma allClosedLayout_nil : allClosedLayout [] = true := rfl
@[grind] lemma allClosedLayout_cons (f : Bool) (fs : List Bool) :
    allClosedLayout (f :: fs) = (f && allClosedLayout fs) := rfl
@[grind] lemma allClosedLayout_append (xs ys : List Bool) :
    allClosedLayout (xs ++ ys) = (allClosedLayout xs && allClosedLayout ys) := by
  induction xs with
  | nil => simp [allClosedLayout]
  | cons f fs ih => simp [allClosedLayout, ih, Bool.and_assoc]

/- An instance carries an open per-instance namespace iff AT LEAST ONE type in
   its chain leaves its layout open — equivalently, iff NOT every type pins a
   closed layout. -/
def instanceAdmitsNamespace (chain : List Bool) : Bool :=
  !allClosedLayout chain

/- The outcome of binding an attribute name that none of the contributing types
   pre-declared, as `Except AttrError Bool`:

     * if the instance carries an open namespace (some type leaves its layout
       open) the binding is ABSORBED and succeeds (`ok true`);
     * otherwise — every type in the chain pins a closed layout — there is no
       namespace to hold it, so the binding is REFUSED (`error bindingRefused`).

   This is the deep model of the runtime rule; G-AX validates it against the
   real interpreter (mapping.md §3, A-reference). -/
def bindUndeclared (chain : List Bool) : Except AttrError Bool :=
  if allClosedLayout chain then Except.error AttrError.bindingRefused
  else Except.ok true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Each type contributing to the value type's chain must pin a closed instance
   layout — declare a closed set of attribute slots and so contribute no
   open per-instance namespace of its own — so that combining it with the other
   contributing types does not re-open the layout of the types that use it. The
   desired behavior requires this flag to be `true`: every contributing type,
   INCLUDING the shared mixin contributor, pins a closed layout. -/
method mixinPinsClosedLayout return (out : Bool)
  ensures out = true
  do
    -- impl-start
    -- The shared contributing type pins a closed instance layout (declares an
    -- empty closed slot set, adding no named slots and no open namespace).
    return true
    -- impl-end

/- Whether an instance of the value type carries an open per-instance
   namespace, as a function of the OTHER contributing types' closed-layout
   flags. `others` is the value type's chain WITHOUT the shared mixin
   contributor (resolution order, most-derived first, universal root excluded);
   the full chain appends the shared contributor's flag, which the desired
   behavior pins to `true` (`mixinPinsClosedLayout`). The result must follow
   the runtime rule on that full chain — in particular, when every other
   contributing type pins a closed layout (the value type's actual shape, whose
   own flags are all `true`), the instance carries NO open namespace. -/
method coreInstanceAdmitsNamespace (others : List Bool) return (out : Bool)
  ensures out = instanceAdmitsNamespace (others ++ [true])
  ensures allClosedLayout others = true → out = false
  do
    -- impl-start
    let trait := true
    let chain : List Bool := others ++ [trait]
    return instanceAdmitsNamespace chain
    -- impl-end

/- The outcome of binding an attribute name the value type did not pre-declare,
   on an instance of the value type, as a function of the OTHER contributing
   types' closed-layout flags (`others`, as above; the full chain appends the
   shared contributor's flag, pinned `true` by the desired behavior). The
   outcome must follow the runtime rule on that full chain — in particular,
   when every other contributing type pins a closed layout (the value type's
   actual shape), the binding is REFUSED with the binding-refused outcome. -/
method coreBindUndeclared (others : List Bool) return (out : Except AttrError Bool)
  ensures out = bindUndeclared (others ++ [true])
  ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
  do
    -- impl-start
    let trait := true
    let chain : List Bool := others ++ [trait]
    return bindUndeclared chain
    -- impl-end

prove_correct mixinPinsClosedLayout by
  loom_solve

prove_correct coreInstanceAdmitsNamespace by
  loom_solve
  all_goals simp_all [instanceAdmitsNamespace, allClosedLayout_append, allClosedLayout]

prove_correct coreBindUndeclared by
  loom_solve
  all_goals simp_all [bindUndeclared, allClosedLayout_append, allClosedLayout]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec = 3 methods with EXACT-PIN postconditions over a universally-quantified others:List Bool: mixinPinsClosedLayout out=true (=Printable.__slots__=() gold edit); coreInstanceAdmitsNamespace out=instanceAdmitsNamespace(others++[true]) for ALL others; coreBindUndeclared out=bindUndeclared(others++[true]) for ALL others. pure region concrete/total, grep-clean of axiom/opaque/sorry/native_decide/':|' => no ungrounded-oracle echo target. A-reference (object-model rule) validated ==interpreter: axiom_check.py G-AX exit 0 (4008 chains), conformance_check.py G-CONF exit 0 (seed 20590, 0 disagreements). refinement.md legs are R/A-reference/I, zero A-consumed, no kind-3 — audit holds.

8 attacks, same_spec=True for all, verified concurrently (batches <=4) via scripts/lean_verify.sh <f>.
FAILING (correctly rejected, EXIT 1): atk1_prepatch (mixin=false,core trait=false — prepatch reproduced), atk2_open_core (core trait=false, F2P-failing open-chain observable), atk3_constant (hardcoded gold constants — fails primary clause on e.g. others=[false]), atk4_partial_domain (correct only on others=[]), atk5_flip (returns allClosedLayout instead of its negation).
VERIFYING (EXIT 0): atk6_boundary_prepend (trait::others instead of others++[trait] — conjunction commutes), atk7_drop_append (returns instanceAdmitsNamespace others / bindUndeclared others — appending true is inert), atk8_ifelse (explicit if allClosedLayout chain then.../else... — definitional unfold). All three keep mixinPinsClosedLayout=true and compute the SAME runtime rule as gold; each is behaviorally equal to gold.

MANDATORY resolve step: faithful refined patch for each verifying attack = the gold patch VERBATIM (sha1 838866344636173d1f4d41631d6ad05666dcab72, byte-identical to benchmark-verified/sympy__sympy-20590/patch.diff — the only modeled change is Printable.__slots__=()). Materialized all 3 patches and ran through the official harness: run_resolve('sympy__sympy-20590', gold_patch) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. run_resolve is deterministic on patch bytes, so the single run settles all three identical patches. No verifying wrong impl's faithful patch fails to resolve => verify=>correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1_prepatch.lean`, `atk2_open_core.lean`, `atk3_constant.lean`, `atk4_partial_domain.lean`, `atk5_flip.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk6_boundary_prepend.lean`, `atk7_drop_append.lean`, `atk8_ifelse.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_open_core.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_constant.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_flip.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_boundary_prepend.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk7_drop_append.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk8_ifelse.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: every modeled operation is a straight-line pure
   computation over the closed-layout flag chain and always terminates, so a
   diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the exact-pin postconditions
   vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behavior under specification — whether an instance of
   a value type carries an open per-instance namespace, and the consequence for
   binding an undeclared attribute name — is modeled DEEPLY in the `pure` region
   (`allClosedLayout`, `instanceAdmitsNamespace`, `bindUndeclared`). The rule
   relating a type's layout declarations to the presence of an open namespace is
   a property of the host runtime's object model, validated against the real
   interpreter out of band (mapping.md §3, axiom_check.py / G-AX); it is NOT
   axiomatized as a callee. -/
-- axioms-end

-- pure-start
/- The single way binding an undeclared attribute name can be refused: the
   instance carries no open namespace to absorb it, so the binding is rejected
   rather than silently stored. This is the only outcome the desired behavior
   distinguishes from success. -/
inductive AttrError where
  | bindingRefused
  deriving DecidableEq

/- An instance is built from a CHAIN of contributing types (its resolution
   order, with the universal root — which never contributes a namespace —
   excluded). Each entry is a flag: `true` iff that type pins a closed instance
   layout (declares a closed set of attribute slots and so contributes no
   open per-instance namespace of its own); `false` iff it leaves its layout
   open.

   `allClosedLayout` is `true` iff EVERY type in the chain pins a closed layout.
   Front-recursive over the chain so a single unfold is available per step (the
   Velvet fold pattern): the head must pin a closed layout and so must the
   tail. -/
def allClosedLayout : List Bool → Bool
  | []      => true
  | f :: fs => f && allClosedLayout fs

@[grind] lemma allClosedLayout_nil : allClosedLayout [] = true := rfl
@[grind] lemma allClosedLayout_cons (f : Bool) (fs : List Bool) :
    allClosedLayout (f :: fs) = (f && allClosedLayout fs) := rfl
@[grind] lemma allClosedLayout_append (xs ys : List Bool) :
    allClosedLayout (xs ++ ys) = (allClosedLayout xs && allClosedLayout ys) := by
  induction xs with
  | nil => simp [allClosedLayout]
  | cons f fs ih => simp [allClosedLayout, ih, Bool.and_assoc]

/- An instance carries an open per-instance namespace iff AT LEAST ONE type in
   its chain leaves its layout open — equivalently, iff NOT every type pins a
   closed layout. -/
def instanceAdmitsNamespace (chain : List Bool) : Bool :=
  !allClosedLayout chain

/- The outcome of binding an attribute name that none of the contributing types
   pre-declared, as `Except AttrError Bool`:

     * if the instance carries an open namespace (some type leaves its layout
       open) the binding is ABSORBED and succeeds (`ok true`);
     * otherwise — every type in the chain pins a closed layout — there is no
       namespace to hold it, so the binding is REFUSED (`error bindingRefused`).

   This is the deep model of the runtime rule; G-AX validates it against the
   real interpreter (mapping.md §3, A-reference). -/
def bindUndeclared (chain : List Bool) : Except AttrError Bool :=
  if allClosedLayout chain then Except.error AttrError.bindingRefused
  else Except.ok true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Each type contributing to the value type's chain must pin a closed instance
   layout — declare a closed set of attribute slots and so contribute no
   open per-instance namespace of its own — so that combining it with the other
   contributing types does not re-open the layout of the types that use it. The
   desired behavior requires this flag to be `true`: every contributing type,
   INCLUDING the shared mixin contributor, pins a closed layout. -/
method mixinPinsClosedLayout return (out : Bool)
  ensures out = true
  do
    -- impl-start
    -- The shared contributing type pins a closed instance layout (declares an
    -- empty closed slot set, adding no named slots and no open namespace).
    return true
    -- impl-end

/- Whether an instance of the value type carries an open per-instance
   namespace, as a function of the OTHER contributing types' closed-layout
   flags. `others` is the value type's chain WITHOUT the shared mixin
   contributor (resolution order, most-derived first, universal root excluded);
   the full chain appends the shared contributor's flag, which the desired
   behavior pins to `true` (`mixinPinsClosedLayout`). The result must follow
   the runtime rule on that full chain — in particular, when every other
   contributing type pins a closed layout (the value type's actual shape, whose
   own flags are all `true`), the instance carries NO open namespace. -/
method coreInstanceAdmitsNamespace (others : List Bool) return (out : Bool)
  ensures out = instanceAdmitsNamespace (others ++ [true])
  ensures allClosedLayout others = true → out = false
  do
    -- impl-start
    let trait := true
    let chain : List Bool := others ++ [trait]
    return instanceAdmitsNamespace chain
    -- impl-end

/- The outcome of binding an attribute name the value type did not pre-declare,
   on an instance of the value type, as a function of the OTHER contributing
   types' closed-layout flags (`others`, as above; the full chain appends the
   shared contributor's flag, pinned `true` by the desired behavior). The
   outcome must follow the runtime rule on that full chain — in particular,
   when every other contributing type pins a closed layout (the value type's
   actual shape), the binding is REFUSED with the binding-refused outcome. -/
method coreBindUndeclared (others : List Bool) return (out : Except AttrError Bool)
  ensures out = bindUndeclared (others ++ [true])
  ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
  do
    -- impl-start
    let trait := true
    let chain : List Bool := others ++ [trait]
    return bindUndeclared chain
    -- impl-end

prove_correct mixinPinsClosedLayout by
  loom_solve

prove_correct coreInstanceAdmitsNamespace by
  loom_solve
  all_goals simp_all [instanceAdmitsNamespace, allClosedLayout_append, allClosedLayout]

prove_correct coreBindUndeclared by
  loom_solve
  all_goals simp_all [bindUndeclared, allClosedLayout_append, allClosedLayout]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec = 3 methods with EXACT-PIN postconditions over a universally-quantified others:List Bool: mixinPinsClosedLayout out=true (=Printable.__slots__=() gold edit); coreInstanceAdmitsNamespace out=instanceAdmitsNamespace(others++[true]) for ALL others; coreBindUndeclared out=bindUndeclared(others++[true]) for ALL others. pure region concrete/total, grep-clean of axiom/opaque/sorry/native_decide/':|' => no ungrounded-oracle echo target. A-reference (object-model rule) validated ==interpreter: axiom_check.py G-AX exit 0 (4008 chains), conformance_check.py G-CONF exit 0 (seed 20590, 0 disagreements). refinement.md legs are R/A-reference/I, zero A-consumed, no kind-3 — audit holds.

8 attacks, same_spec=True for all, verified concurrently (batches <=4) via scripts/lean_verify.sh <f>.
FAILING (correctly rejected, EXIT 1): atk1_prepatch (mixin=false,core trait=false — prepatch reproduced), atk2_open_core (core trait=false, F2P-failing open-chain observable), atk3_constant (hardcoded gold constants — fails primary clause on e.g. others=[false]), atk4_partial_domain (correct only on others=[]), atk5_flip (returns allClosedLayout instead of its negation).
VERIFYING (EXIT 0): atk6_boundary_prepend (trait::others instead of others++[trait] — conjunction commutes), atk7_drop_append (returns instanceAdmitsNamespace others / bindUndeclared others — appending true is inert), atk8_ifelse (explicit if allClosedLayout chain then.../else... — definitional unfold). All three keep mixinPinsClosedLayout=true and compute the SAME runtime rule as gold; each is behaviorally equal to gold.

MANDATORY resolve step: faithful refined patch for each verifying attack = the gold patch VERBATIM (sha1 838866344636173d1f4d41631d6ad05666dcab72, byte-identical to benchmark-verified/sympy__sympy-20590/patch.diff — the only modeled change is Printable.__slots__=()). Materialized all 3 patches and ran through the official harness: run_resolve('sympy__sympy-20590', gold_patch) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. run_resolve is deterministic on patch bytes, so the single run settles all three identical patches. No verifying wrong impl's faithful patch fails to resolve => verify=>correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec via VelvetBackend.language = True). Solution.lean verifies cleanly under scripts/lean_verify.sh (exit 0). The spec models the CPython object-model rule: chain of contributing-type closed-layout flags (universal root excluded) -> instanceAdmitsNamespace(chain)=!allClosedLayout(chain); bindUndeclared refuses iff allClosedLayout.

Faithfulness verified against the REAL repo (worktree @ cffd4e0f86):
- PREPATCH (Printable has no __slots__): Basic() MRO=[Basic,Printable,object], chain=[Basic=closed=true, Printable=open=false]. Real: hasattr(b1,'__dict__')=True, b1.x=1 succeeds. Model on [true,false]: instanceAdmitsNamespace=true, bindUndeclared=ok. MATCH.
- GOLD (Printable.__slots__=() applied): chain=[true,true]. Real: hasattr=False, b1.x=1 raises AttributeError. Model on [true,true]: instanceAdmitsNamespace=false, bindUndeclared=error bindingRefused. MATCH. Confirmed also for Symbol() (deep MRO, named non-empty slots) under gold: hasattr __dict__=False.
- F2P observations (B1/B2) match: not hasattr(b1,'__dict__') and AttributeError on b1.x=1 under gold.

General rule fidelity: G-AX (axiom_check.py) exit 0 — model matches interpreter on 4008 chains; G-CONF (conformance_check.py, seed 20590) exit 0, 0 disagreements. Independently ran an EXHAUSTIVE model-vs-interpreter comparison over all boolean chains n=0..7 (build linear inheritance chains, __slots__=() for closed / {} for open): 0 divergences. The universal-quantification over `others` in the core* methods pins the rule on every chain, and the second ensures clause pins the F2P instantiation — neither is stronger than the real repo behavior on any tested/reachable input.

No diverging input found: the modeled function agrees with the real callee (CPython attribute/namespace semantics validated against the real sympy Basic/Symbol types) on every input tested, including the exact F2P shape. The spec is not too strong and does not drift from real repo behavior. G-DIFF confirms the prepatch (trait flag flipped false) fails, so the spec is also discriminating.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical to Solution_prepatch.lean via swebench_unified.markers.same_spec (=> True); only elided impl/proof regions differ. Mechanical leakage.screen passes (no diff markers, no gold-line reproduction, no patched file path/module, no identifier or comment echoing the only distinctive changed symbol 'Printable', no narration terms). Semantic check beyond the lexical screen: the gold edit is `+ __slots__ = ()` on class Printable in sympy/core/_print_helpers.py. The public problem_statement already names __dict__ and __slots__ and states the hypothesis 'some parent class accidentally stopped defining __slots__' — so the edit direction (restore a missing empty __slots__ on a parent/mixin) is public independent of hints_text. The spec view names no patched file, no patched class (Printable/Basic/Symbol all absent), never reproduces `__slots__ = ()`, and describes the behavior only in abstract modeling vocabulary ('shared mixin contributor', 'closed instance layout', 'contributing-type chain', 'open per-instance namespace'). The 'empty slot set' concrete detail appears only inside the impl-start/impl-end region, which is elided from the projected spec view (confirmed: shows '-- implementation elided'). The formalized rule (a mixin must pin a closed layout so subclasses do not reopen a namespace) is a faithful spec whose direction is derivable from the public problem statement; it adds no repo-specific localization beyond what is already public. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

# P2 adversarial audit — pydata__xarray-3677

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_boundary_empty.lean`, `atk_4_swap_order.lean`, `atk_6_echo_coerce.lean`, `atk_7_partial_coerce.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5_echo_spec.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 
 -- axioms-start
 /- No consumed axioms. The one unchanged callee this slice relies on — the core
@@ -88,14 +88,8 @@
   ensures out = combineSpec base other
   do
     -- impl-start
-    -- An operand that is a lone keyed value, not a key→value collection, is
-    -- first re-expressed as a one-entry collection so the core combine — which
-    -- consumes key/value pairs — can process it; a collection passes through.
-    let other' : Operand :=
-      match other with
-      | .single k v => Operand.keyed (asKeyed k v)
-      | .keyed es   => Operand.keyed es
-    let out := combineCore base other'
+    -- Pre-patch: operand handed straight to combineCore WITHOUT re-expressing.
+    let out := combineCore base other
     return out
     -- impl-end
 
```

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The one unchanged callee this slice relies on — the core
@@ -88,14 +88,10 @@
   ensures out = combineSpec base other
   do
     -- impl-start
-    -- An operand that is a lone keyed value, not a key→value collection, is
-    -- first re-expressed as a one-entry collection so the core combine — which
-    -- consumes key/value pairs — can process it; a collection passes through.
-    let other' : Operand :=
+    let out :=
       match other with
-      | .single k v => Operand.keyed (asKeyed k v)
-      | .keyed es   => Operand.keyed es
-    let out := combineCore base other'
+      | .single k v => combineCore base (.keyed (asKeyed k v))
+      | .keyed _    => Except.error CombineErr.notKeyed
     return out
     -- impl-end
 
```

Attack 3 — `atk_3_boundary_empty.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The one unchanged callee this slice relies on — the core
@@ -88,12 +88,9 @@
   ensures out = combineSpec base other
   do
     -- impl-start
-    -- An operand that is a lone keyed value, not a key→value collection, is
-    -- first re-expressed as a one-entry collection so the core combine — which
-    -- consumes key/value pairs — can process it; a collection passes through.
     let other' : Operand :=
       match other with
-      | .single k v => Operand.keyed (asKeyed k v)
+      | .single _ _ => Operand.keyed []
       | .keyed es   => Operand.keyed es
     let out := combineCore base other'
     return out
```

Attack 4 — `atk_4_swap_order.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The one unchanged callee this slice relies on — the core
@@ -88,14 +88,10 @@
   ensures out = combineSpec base other
   do
     -- impl-start
-    -- An operand that is a lone keyed value, not a key→value collection, is
-    -- first re-expressed as a one-entry collection so the core combine — which
-    -- consumes key/value pairs — can process it; a collection passes through.
-    let other' : Operand :=
+    let out : Except CombineErr KeyedMap :=
       match other with
-      | .single k v => Operand.keyed (asKeyed k v)
-      | .keyed es   => Operand.keyed es
-    let out := combineCore base other'
+      | .single k v => Except.ok (asKeyed k v ++ base)
+      | .keyed es   => Except.ok (es ++ base)
     return out
     -- impl-end
 
```

Attack 5 — `atk_5_echo_spec.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The one unchanged callee this slice relies on — the core
@@ -88,14 +88,8 @@
   ensures out = combineSpec base other
   do
     -- impl-start
-    -- An operand that is a lone keyed value, not a key→value collection, is
-    -- first re-expressed as a one-entry collection so the core combine — which
-    -- consumes key/value pairs — can process it; a collection passes through.
-    let other' : Operand :=
-      match other with
-      | .single k v => Operand.keyed (asKeyed k v)
-      | .keyed es   => Operand.keyed es
-    let out := combineCore base other'
+    -- Echo: return the spec oracle directly.
+    let out := combineSpec base other
     return out
     -- impl-end
 
```

Attack 6 — `atk_6_echo_coerce.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The one unchanged callee this slice relies on — the core
@@ -88,14 +88,7 @@
   ensures out = combineSpec base other
   do
     -- impl-start
-    -- An operand that is a lone keyed value, not a key→value collection, is
-    -- first re-expressed as a one-entry collection so the core combine — which
-    -- consumes key/value pairs — can process it; a collection passes through.
-    let other' : Operand :=
-      match other with
-      | .single k v => Operand.keyed (asKeyed k v)
-      | .keyed es   => Operand.keyed es
-    let out := combineCore base other'
+    let out := combineCore base (coerceOperand other)
     return out
     -- impl-end
 
```

Attack 7 — `atk_7_partial_coerce.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The one unchanged callee this slice relies on — the core
@@ -88,14 +88,11 @@
   ensures out = combineSpec base other
   do
     -- impl-start
-    -- An operand that is a lone keyed value, not a key→value collection, is
-    -- first re-expressed as a one-entry collection so the core combine — which
-    -- consumes key/value pairs — can process it; a collection passes through.
-    let other' : Operand :=
+    let out :=
       match other with
-      | .single k v => Operand.keyed (asKeyed k v)
-      | .keyed es   => Operand.keyed es
-    let out := combineCore base other'
+      | .single k v => if v >= 0 then combineCore base (.keyed (asKeyed k v))
+                       else combineCore base (.single k v)
+      | .keyed es   => combineCore base (.keyed es)
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the core
   combine operation `combineCore`, which fuses two key→value collections — is
   modeled DEEPLY in the `pure` region and validated == the real callee by G-AX
   (an A-reference, mapping.md §3), so it carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A key→value collection: a mapping from key identities (modeled as `Nat` tags;
   only key equality/membership is observed) to values (modeled as `Int`; only
   value identity is observed). -/
abbrev KeyedMap := List (Nat × Int)

/- A combine operand, in its two mutually-exclusive shapes:
   `keyed es` — a genuine key→value collection that exposes its entries as
   key/value pairs; `single k v` — a lone keyed value that is NOT itself a
   key→value collection (it does not expose key/value pairs). -/
inductive Operand where
  | keyed  (entries : KeyedMap)
  | single (key : Nat) (value : Int)
  deriving DecidableEq

/- Failure of the core combine operation: it is undefined on an operand that
   does not expose key/value pairs (there is nothing to iterate). -/
inductive CombineErr where
  | notKeyed
  deriving DecidableEq

/- The fused entries of two collections: their union, base first. -/
def combineEntries (a b : KeyedMap) : KeyedMap := a ++ b

/- The core combine callee (unchanged by this change; A-reference, deep model of
   the real fuse-the-collections operation — mapping.md §3.1). It consumes the
   operand's key/value pairs and fuses them with the base. A `keyed` operand
   exposes its pairs, so the fuse succeeds; a `single` operand exposes no
   key/value pairs, so the operation is undefined on it and fails. -/
def combineCore (base : KeyedMap) : Operand → Except CombineErr KeyedMap
  | .keyed es    => Except.ok (combineEntries base es)
  | .single _ _  => Except.error .notKeyed

/- Re-express a lone keyed value as a one-entry key→value collection. -/
def asKeyed (k : Nat) (v : Int) : KeyedMap := [(k, v)]

/- Normalize an operand into a key→value collection: a lone keyed value is
   re-expressed as a one-entry collection so it exposes key/value pairs; an
   operand that is already a collection is left as is. -/
def coerceOperand : Operand → Operand
  | .single k v  => Operand.keyed (asKeyed k v)
  | .keyed es    => Operand.keyed es

/- The intended result: normalize the operand to a key→value collection, then
   hand it to the core combine. Because every normalized operand exposes
   key/value pairs, the combine always succeeds. -/
def combineSpec (base : KeyedMap) (other : Operand) : Except CombineErr KeyedMap :=
  combineCore base (coerceOperand other)

@[grind] lemma coerceOperand_single (k : Nat) (v : Int) :
    coerceOperand (.single k v) = Operand.keyed (asKeyed k v) := rfl
@[grind] lemma coerceOperand_keyed (es : KeyedMap) :
    coerceOperand (.keyed es) = Operand.keyed es := rfl
@[grind] lemma combineCore_keyed (base es : KeyedMap) :
    combineCore base (.keyed es) = Except.ok (combineEntries base es) := rfl
@[grind] lemma combineCore_single (base : KeyedMap) (k : Nat) (v : Int) :
    combineCore base (.single k v) = Except.error .notKeyed := rfl
@[grind] lemma combineSpec_single (base : KeyedMap) (k : Nat) (v : Int) :
    combineSpec base (.single k v)
      = Except.ok (combineEntries base (asKeyed k v)) := rfl
@[grind] lemma combineSpec_keyed (base es : KeyedMap) :
    combineSpec base (.keyed es) = Except.ok (combineEntries base es) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method combineKeyed (base : KeyedMap) (other : Operand)
    return (out : Except CombineErr KeyedMap)
  ensures out = combineSpec base other
  do
    -- impl-start
    -- An operand that is a lone keyed value, not a key→value collection, is
    -- first re-expressed as a one-entry collection so the core combine — which
    -- consumes key/value pairs — can process it; a collection passes through.
    let other' : Operand :=
      match other with
      | .single k v => Operand.keyed (asKeyed k v)
      | .keyed es   => Operand.keyed es
    let out := combineCore base other'
    return out
    -- impl-end

prove_correct combineKeyed by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact-equality, total-domain postcondition 'ensures out = combineSpec base other' (no preconditions), where combineSpec = combineCore of (coerceOperand other). Any verifying impl must be extensionally equal to combineSpec on ALL (base, other) -- near-zero behavioural wiggle room; both the .single case (re-express a lone keyed value to a one-entry collection, then combine) and the .keyed case (combine the collection directly) are pinned exactly.

Verify cmd: bash scripts/lean_verify.sh <file>  (exit 0 = verifies).
### Results
- pos_control.lean (copy of Solution.lean): EXIT 0 VERIFIES (positive control OK).
- atk_1_prepatch.lean (PREPATCH bug: 'let out := combineCore base other', raw operand fed straight to combine): EXIT 1 FAILS -- unsolved goal on the .single case (combineCore base (.single _ _) = .error .notKeyed != .ok ...). Prepatch reproduced.
- atk_2_partial_domain.lean (coerce .single correctly but return .error on .keyed): EXIT 1 FAILS.
- atk_3_boundary_empty.lean (re-express .single as EMPTY collection [] instead of one-entry): EXIT 1 FAILS.
- atk_4_swap_order.lean (control-flow-effect: append operand++base instead of base++operand): EXIT 1 FAILS.
- atk_5_echo_spec.lean (ungrounded-oracle echo: 'let out := combineSpec base other'): EXIT 0 VERIFIES. This is the ONLY verifying wrong-shaped impl.
- atk_6_echo_coerce.lean (echo #2: 'combineCore base (coerceOperand other)', definitionally equal to combineSpec but written unfolded): EXIT 1 FAILS -- loom_solve leaves 'combineCore base (coerceOperand other) = combineSpec base other' unsolved (surface form not defeq-closed by the tactic). Not a counterexample.
- atk_7_partial_coerce.lean (partial coerce: re-express .single only when value>=0): EXIT 1 FAILS.

RESOLVE (protocol step 2 -- every VERIFYING wrong impl must have its faithful refined patch RUN through the harness): only atk_5 verifies. atk_5 returns combineSpec base other verbatim, i.e. it computes EXACTLY the frozen spec oracle = normalize-then-combine, behaviourally identical to the gold. Its faithful refined patch is therefore the gold hunk (the added 'other = other.to_dataset() if isinstance(other, xr.DataArray) else other'). Executed:
  from swebench_unified.harness import run_resolve; run_resolve('pydata__xarray-3677', <atk_5 faithful patch>, timeout=1200, retries=0)
  OBSERVED: RESOLVED=True COMPLETED=True NOTE='resolved'.
The faithful patch of the one verifying impl RESOLVES. Under the resolved echo-attack policy (G-PANEL-1/G-EQ), a same-spec verifying impl whose faithful patch resolves is NOT a weakness. No verifying wrong impl produces a non-resolving faithful patch.

REFINEMENT.MD AUDIT: A legs are the focus (R/I covered by G-CONF, which passed on 100005 inputs seed=3677). The single deep-model reference is combineCore == xarray.core.merge.dataset_merge_method (-> merge_core -> coerce_pandas_values), an A-reference (NOT a consumed axiom -- there are none). It is validated by G-AX/axiom_check.py against the REAL callee: (a) dataset_merge_method on a Dataset operand yields the union of variable name/value mappings; (b) dataset_merge_method on a RAW DataArray raises AttributeError ('DataArray' object has no attribute 'items'). meta.json records G-AX pass (4 boundary + 2000 fuzz merges + 24 raw-DataArray crash checks). The correspondence holds: the .keyed success leg and the .single crash leg both match the real callee. The one genuinely-changed op (the added to_dataset() re-expression) is modeled concretely as coerceOperand (an I leg, step A3), not axiomatized -- so no kind-3 legs. Steps A1/A2 are R (self/other -> KeyedMap/Operand), A4 is A-reference+I, A5 is I. Correspondence sound.

VERDICT: SOUND. 7 attacks encoded+verified (prepatch reproduced; 5 wrong impls correctly rejected; 1 def-equal echo rejected on surface form; 1 spec-oracle echo verifies and its faithful patch RESOLVES). The exact-equality total postcondition leaves no room for a verifying-but-incorrect impl; the only verifying same-spec impl is behaviourally the gold and resolves. Deep-model A-reference validated by G-AX. No verify=>correct violation found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_boundary_empty.lean`, `atk_4_swap_order.lean`, `atk_6_echo_coerce.lean`, `atk_7_partial_coerce.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5_echo_spec.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary_empty.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_swap_order.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_echo_spec.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_echo_coerce.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_partial_coerce.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the core
   combine operation `combineCore`, which fuses two key→value collections — is
   modeled DEEPLY in the `pure` region and validated == the real callee by G-AX
   (an A-reference, mapping.md §3), so it carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A key→value collection: a mapping from key identities (modeled as `Nat` tags;
   only key equality/membership is observed) to values (modeled as `Int`; only
   value identity is observed). -/
abbrev KeyedMap := List (Nat × Int)

/- A combine operand, in its two mutually-exclusive shapes:
   `keyed es` — a genuine key→value collection that exposes its entries as
   key/value pairs; `single k v` — a lone keyed value that is NOT itself a
   key→value collection (it does not expose key/value pairs). -/
inductive Operand where
  | keyed  (entries : KeyedMap)
  | single (key : Nat) (value : Int)
  deriving DecidableEq

/- Failure of the core combine operation: it is undefined on an operand that
   does not expose key/value pairs (there is nothing to iterate). -/
inductive CombineErr where
  | notKeyed
  deriving DecidableEq

/- The fused entries of two collections: their union, base first. -/
def combineEntries (a b : KeyedMap) : KeyedMap := a ++ b

/- The core combine callee (unchanged by this change; A-reference, deep model of
   the real fuse-the-collections operation — mapping.md §3.1). It consumes the
   operand's key/value pairs and fuses them with the base. A `keyed` operand
   exposes its pairs, so the fuse succeeds; a `single` operand exposes no
   key/value pairs, so the operation is undefined on it and fails. -/
def combineCore (base : KeyedMap) : Operand → Except CombineErr KeyedMap
  | .keyed es    => Except.ok (combineEntries base es)
  | .single _ _  => Except.error .notKeyed

/- Re-express a lone keyed value as a one-entry key→value collection. -/
def asKeyed (k : Nat) (v : Int) : KeyedMap := [(k, v)]

/- Normalize an operand into a key→value collection: a lone keyed value is
   re-expressed as a one-entry collection so it exposes key/value pairs; an
   operand that is already a collection is left as is. -/
def coerceOperand : Operand → Operand
  | .single k v  => Operand.keyed (asKeyed k v)
  | .keyed es    => Operand.keyed es

/- The intended result: normalize the operand to a key→value collection, then
   hand it to the core combine. Because every normalized operand exposes
   key/value pairs, the combine always succeeds. -/
def combineSpec (base : KeyedMap) (other : Operand) : Except CombineErr KeyedMap :=
  combineCore base (coerceOperand other)

@[grind] lemma coerceOperand_single (k : Nat) (v : Int) :
    coerceOperand (.single k v) = Operand.keyed (asKeyed k v) := rfl
@[grind] lemma coerceOperand_keyed (es : KeyedMap) :
    coerceOperand (.keyed es) = Operand.keyed es := rfl
@[grind] lemma combineCore_keyed (base es : KeyedMap) :
    combineCore base (.keyed es) = Except.ok (combineEntries base es) := rfl
@[grind] lemma combineCore_single (base : KeyedMap) (k : Nat) (v : Int) :
    combineCore base (.single k v) = Except.error .notKeyed := rfl
@[grind] lemma combineSpec_single (base : KeyedMap) (k : Nat) (v : Int) :
    combineSpec base (.single k v)
      = Except.ok (combineEntries base (asKeyed k v)) := rfl
@[grind] lemma combineSpec_keyed (base es : KeyedMap) :
    combineSpec base (.keyed es) = Except.ok (combineEntries base es) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method combineKeyed (base : KeyedMap) (other : Operand)
    return (out : Except CombineErr KeyedMap)
  ensures out = combineSpec base other
  do
    -- impl-start
    -- An operand that is a lone keyed value, not a key→value collection, is
    -- first re-expressed as a one-entry collection so the core combine — which
    -- consumes key/value pairs — can process it; a collection passes through.
    let other' : Operand :=
      match other with
      | .single k v => Operand.keyed (asKeyed k v)
      | .keyed es   => Operand.keyed es
    let out := combineCore base other'
    return out
    -- impl-end

prove_correct combineKeyed by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact-equality, total-domain postcondition 'ensures out = combineSpec base other' (no preconditions), where combineSpec = combineCore of (coerceOperand other). Any verifying impl must be extensionally equal to combineSpec on ALL (base, other) -- near-zero behavioural wiggle room; both the .single case (re-express a lone keyed value to a one-entry collection, then combine) and the .keyed case (combine the collection directly) are pinned exactly.

Verify cmd: bash scripts/lean_verify.sh <file>  (exit 0 = verifies).
### Results
- pos_control.lean (copy of Solution.lean): EXIT 0 VERIFIES (positive control OK).
- atk_1_prepatch.lean (PREPATCH bug: 'let out := combineCore base other', raw operand fed straight to combine): EXIT 1 FAILS -- unsolved goal on the .single case (combineCore base (.single _ _) = .error .notKeyed != .ok ...). Prepatch reproduced.
- atk_2_partial_domain.lean (coerce .single correctly but return .error on .keyed): EXIT 1 FAILS.
- atk_3_boundary_empty.lean (re-express .single as EMPTY collection [] instead of one-entry): EXIT 1 FAILS.
- atk_4_swap_order.lean (control-flow-effect: append operand++base instead of base++operand): EXIT 1 FAILS.
- atk_5_echo_spec.lean (ungrounded-oracle echo: 'let out := combineSpec base other'): EXIT 0 VERIFIES. This is the ONLY verifying wrong-shaped impl.
- atk_6_echo_coerce.lean (echo #2: 'combineCore base (coerceOperand other)', definitionally equal to combineSpec but written unfolded): EXIT 1 FAILS -- loom_solve leaves 'combineCore base (coerceOperand other) = combineSpec base other' unsolved (surface form not defeq-closed by the tactic). Not a counterexample.
- atk_7_partial_coerce.lean (partial coerce: re-express .single only when value>=0): EXIT 1 FAILS.

RESOLVE (protocol step 2 -- every VERIFYING wrong impl must have its faithful refined patch RUN through the harness): only atk_5 verifies. atk_5 returns combineSpec base other verbatim, i.e. it computes EXACTLY the frozen spec oracle = normalize-then-combine, behaviourally identical to the gold. Its faithful refined patch is therefore the gold hunk (the added 'other = other.to_dataset() if isinstance(other, xr.DataArray) else other'). Executed:
  from swebench_unified.harness import run_resolve; run_resolve('pydata__xarray-3677', <atk_5 faithful patch>, timeout=1200, retries=0)
  OBSERVED: RESOLVED=True COMPLETED=True NOTE='resolved'.
The faithful patch of the one verifying impl RESOLVES. Under the resolved echo-attack policy (G-PANEL-1/G-EQ), a same-spec verifying impl whose faithful patch resolves is NOT a weakness. No verifying wrong impl produces a non-resolving faithful patch.

REFINEMENT.MD AUDIT: A legs are the focus (R/I covered by G-CONF, which passed on 100005 inputs seed=3677). The single deep-model reference is combineCore == xarray.core.merge.dataset_merge_method (-> merge_core -> coerce_pandas_values), an A-reference (NOT a consumed axiom -- there are none). It is validated by G-AX/axiom_check.py against the REAL callee: (a) dataset_merge_method on a Dataset operand yields the union of variable name/value mappings; (b) dataset_merge_method on a RAW DataArray raises AttributeError ('DataArray' object has no attribute 'items'). meta.json records G-AX pass (4 boundary + 2000 fuzz merges + 24 raw-DataArray crash checks). The correspondence holds: the .keyed success leg and the .single crash leg both match the real callee. The one genuinely-changed op (the added to_dataset() re-expression) is modeled concretely as coerceOperand (an I leg, step A3), not axiomatized -- so no kind-3 legs. Steps A1/A2 are R (self/other -> KeyedMap/Operand), A4 is A-reference+I, A5 is I. Correspondence sound.

VERDICT: SOUND. 7 attacks encoded+verified (prepatch reproduced; 5 wrong impls correctly rejected; 1 def-equal echo rejected on surface form; 1 spec-oracle echo verifies and its faithful patch RESOLVES). The exact-equality total postcondition leaves no room for a verifying-but-incorrect impl; the only verifying same-spec impl is behaviourally the gold and resolves. Deep-model A-reference validated by G-AX. No verify=>correct violation found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution, Solution_prepatch, lean) = True — spec region byte-identical, impl properly elided. Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean FAILS the ensures on the .single case (combineCore base other != combineSpec base other), so the spec is discriminating (the added coerceOperand normalization is genuinely required), not vacuous. A-reference validated empirically against the base worktree at ef6e6a7b, pinned onto sys.path so that the installed xarray 0.15.1 -- which already carries the patch -- could not stand in for it: dataset_merge_method on a Dataset operand yields the union of variable maps on disjoint names == combineCore .keyed; dataset_merge_method / coerce_pandas_values on a raw DataArray raises AttributeError "'DataArray' object has no attribute 'items'" == combineCore .single = .error .notKeyed (the reported crash); base.merge(da) crashes at base and succeeds patched ({a:0,b:1}); patched base.merge(DataArray b) == base.merge(Dataset b) == combineSpec (coerce-then-combine). The spec is if anything conservatively scoped (drops dtype/shape/attrs, no-conflict regime) which risks being too WEAK, not too strong; but for panel-2 faithfulness the modeled function matches the real callee on all in-domain inputs. Verdict: FAITHFUL.

Counterexample / evidence:

```
N/A for verdict — the conflicting-name case above is a legitimate, disclosed scoping boundary rather than a spec-too-strong defect. Within the declared disjoint-name domain the model agrees with the real callee on every checked input (keyed union, single->AttributeError/coerced union, empty operands).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec integrity confirmed: markers.same_spec(Solution.lean, Solution_prepatch.lean) = True under the velvet backend — the spec region (axioms/pure/pre/post + signature + ensures) is byte-identical, only the elided impl differs (prepatch feeds the raw operand and fails G-DIFF). Rendered the consumer spec view via markers.spec_view: it exposes abstract carriers (KeyedMap = List(Nat×Int), Operand = keyed|single), helpers combineCore/asKeyed/coerceOperand/combineSpec, and the postcondition `out = combineSpec base other`; impl and proof bodies are elided.

Leakage assessment against the PUBLIC problem_statement (hints_text is empty): the problem_statement already discloses the defect and fix concretely — `ds.merge(da)` raises `AttributeError: 'DataArray' object has no attribute 'items'` inside coerce_pandas_values (obj.items()), and shows the working `xr.merge([ds, da])` output. A reader trivially infers the gold edit: coerce the DataArray operand into a Dataset so it exposes .items() before merging. The spec view mechanizes exactly this behavior (coerceOperand normalizes .single into a one-entry .keyed collection, else pass-through; combineSpec = combineCore∘coerceOperand) but ONLY in abstract terms. It quotes no gold-patch specifics: no `to_dataset()`, no `isinstance`, no `xr.DataArray`, no `dataset_merge_method`, no file/line refs — those concrete tokens live only in mapping.md/refinement.md, which are auditor docs outside the consumer spec view. The pinned behavior does not exceed what the public problem_statement already reveals; it is a faithful abstraction of publicly-disclosed intended behavior.

Mechanical corroboration: leakage.screen(src, velvet, patch, problem_statement) returns passed=True, hard_failures=[]. Bundle is not relaxed (no RELAXED_LEAKAGE.md / relaxed_leakage flag; recorded G-LEAK status=pass). No spec-view line leaks the gold edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

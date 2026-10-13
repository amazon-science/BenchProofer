# P2 adversarial audit — django__django-14752

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

**Non-vacuity.** The positive control `pos2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No consumed axioms. The per-item serialization is an injected, caller-
@@ -77,7 +77,7 @@
   ensures out = items.map serialize
   do
     -- impl-start
-    let results := items.map serialize
+    let results := items.map defaultSerialized
     return results
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
 -- (No consumed axioms. The per-item serialization is an injected, caller-
@@ -51,7 +51,7 @@
   ensures out = defaultSerialized it
   do
     -- impl-start
-    return [("id", it.idText), ("text", it.displayText)]
+    return [("id", it.idText)]
     -- impl-end
 
 prove_correct serializeResult by
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
 -- (No consumed axioms. The per-item serialization is an injected, caller-
@@ -51,7 +51,7 @@
   ensures out = defaultSerialized it
   do
     -- impl-start
-    return [("id", it.idText), ("text", it.displayText)]
+    return [("text", it.displayText), ("id", it.idText)]
     -- impl-end
 
 prove_correct serializeResult by
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
 -- (No consumed axioms. The per-item serialization is an injected, caller-
@@ -77,8 +77,7 @@
   ensures out = items.map serialize
   do
     -- impl-start
-    let results := items.map serialize
-    return results
+    return []
     -- impl-end
 
 prove_correct buildResults by
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
 -- (No consumed axioms. The per-item serialization is an injected, caller-
@@ -77,7 +77,7 @@
   ensures out = items.map serialize
   do
     -- impl-start
-    let results := items.map serialize
+    let results := (items.map serialize).reverse
     return results
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
 -- (No consumed axioms. The per-item serialization is an injected, caller-
@@ -51,7 +51,7 @@
   ensures out = defaultSerialized it
   do
     -- impl-start
-    return [("id", it.idText), ("text", it.displayText)]
+    return [("id", it.displayText), ("text", it.idText)]
     -- impl-end
 
 prove_correct serializeResult by
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
 -- (No consumed axioms. The per-item serialization is an injected, caller-
@@ -77,7 +77,9 @@
   ensures out = items.map serialize
   do
     -- impl-start
-    let results := items.map serialize
+    let results := match items with
+      | [] => [defaultSerialized default]
+      | xs => xs.map serialize
     return results
     -- impl-end
 
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
 -- (No consumed axioms. The per-item serialization is an injected, caller-
@@ -77,7 +77,9 @@
   ensures out = items.map serialize
   do
     -- impl-start
-    let results := items.map serialize
+    let results := match items with
+      | [x] => [defaultSerialized x]
+      | xs => xs.map serialize
     return results
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The per-item serialization is an injected, caller-
--  overridable operation modeled as an arbitrary total function `serialize`;
--  the result postcondition holds for EVERY such function, so it owes no
--  contract and is strictly weaker than any concrete serializer (directive 7).
--  The default serialization is modeled DEEPLY in the `pure` region. There is
--  no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The observable content of one source item that the default serialization
   reads: its chosen identifier rendered as text, and its own display text.
   These two renderings are taken as given observables of the item; the desired
   behavior does not change how either is computed (mapping.md §2). -/
structure Item where
  idText : String
  displayText : String
  deriving DecidableEq, Inhabited

/- A serialized result: an ordered association of string field names to string
   values — the object produced for one item. Modeled as an ordered list of
   key/value pairs so that additional fields may be present beyond the defaults
   (the customization the desired behavior must allow). -/
abbrev Serialized := List (String × String)

/- The default serialization of one item: an object carrying exactly the
   identifier field and the display-text field, in that order. -/
def defaultSerialized (it : Item) : Serialized :=
  [("id", it.idText), ("text", it.displayText)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The default per-item serialization: convert one source item into the result
   object for that item. It carries exactly the identifier field and the
   display-text field, in that order. `it` is read-only (not `mut`); the step
   constructs a fresh result and mutates nothing (directive 5). -/
method serializeResult (it : Item) return (out : Serialized)
  ensures out = defaultSerialized it
  do
    -- impl-start
    return ("id", it.idText) :: ("text", it.displayText) :: []
    -- impl-end

prove_correct serializeResult by
  loom_solve
  simp [defaultSerialized]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the results list from a list of source items by applying a single
   injected per-item serialization to each item, preserving order. The
   serialization `serialize` is supplied by the caller (its default is
   `serializeResult`); building the list applies whichever serialization is in
   effect to EVERY item — so a caller-supplied serialization takes effect for
   every result, and the count and order of the results equal those of the
   items. `items` and `serialize` are read-only (not `mut`); the step builds a
   fresh list and mutates neither input (directive 5). -/
method buildResults (items : List Item) (serialize : Item → Serialized)
    return (out : List Serialized)
  ensures out = items.map serialize
  do
    -- impl-start
    let results := items.map (fun x => serialize x)
    return results
    -- impl-end

prove_correct buildResults by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec = two exact-equality postconditions over a FREE universally-quantified serialize: serializeResult ensures out = defaultSerialized it = [("id",idText),("text",displayText)]; buildResults ensures out = items.map serialize. No axioms (G-AX skip); refinement.md all R/I, no kind-3; A-leg is the free-function model of the late-bound self.serialize_result(obj,to_field_name), which is strictly weaker than any concrete serializer and owes no contract (directive 7) — correspondence to the real callee holds.

Protocol executed. same_spec=True for ALL files (verified via swebench_unified.markers.same_spec, velvet). Verify command per file: `bash scripts/lean_verify.sh <file>`; runs launched concurrently in batches of 4.

8 DISTINCT same-spec wrong impls, ALL correctly REJECTED (exit 1) for the right reason:
- atk_1 PREPATCH BUG (items.map defaultSerialized, ignores injected serialize) exit=1, discriminating goal `List.map defaultSerialized items = List.map serialize items`. Bundle's own Solution_prepatch.lean independently reproduced (exit=1, identical goal). prepatch_reproduced=true.
- atk_2 drop text field exit=1 (⊢ False); atk_3 reversed field order exit=1 (ordered list pins insertion order); atk_4 return [] exit=1; atk_5 (items.map serialize).reverse exit=1; atk_6 swap id/text values exit=1; atk_7 partial-domain wrong-on-empty exit=1; atk_8 control-flow wrong-on-singleton (defaultSerialized) exit=1.
Every terminating wrong VALUE is rejected — the exact-equality postconditions over the free serialize leave no value-level slack; no ungrounded-oracle echo path exists (serialize is a free parameter, not an axiomatized answer key).

Positive control pos2.lean (structurally different but correct: items.map (fun x => serialize x); serializeResult via explicit cons) VERIFIES (exit 0) — spec non-vacuous at the value level. (An earlier control pos.lean using a reverse-reverse identity failed only because loom_solve did not discharge (map f xs.reverse).reverse = map f xs — a proof-tactic gap, not a spec defect; pos2 replaces it.)

ONE verifying attack: atk_9.lean (buildResults = `while true do i := i+1; return []`) VERIFIES (exit 0) — but SOLELY by NON-TERMINATION under the bundle's `set_option loom.semantics.termination "partial"`, the documented universal convention on every velvet/lean bundle (spec_guide.md:112), NOT a value-level weakness of THIS spec. Evidence it is a pure divergence artifact: its terminating twin atk_4 (`return []`, no loop) is REJECTED. atk_9 was therefore NOT submitted as an attack and requires no resolve run: a divergent Lean impl has no faithful TERMINATING refined patch — its faithful image is an infinite loop in get(), which is not a developer fix and would hang the harness (run_resolve cannot complete => INCONCLUSIVE, never BROKEN). It computes no observable wrong terminating value. Hence no verify⇏correct break: patches={} (no submitted attack verifies). This partial-correctness artifact is out of scope for refinement-fidelity/G-EQ and is not a legitimate counterexample.

Verdict: SOUND — 8 distinct same-spec wrong impls all rejected for the right reasons, prepatch reproduced, positive control verifies, and the sole verifier is the accepted non-termination artifact yielding no verify⇏correct break.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The per-item serialization is an injected, caller-
--  overridable operation modeled as an arbitrary total function `serialize`;
--  the result postcondition holds for EVERY such function, so it owes no
--  contract and is strictly weaker than any concrete serializer (directive 7).
--  The default serialization is modeled DEEPLY in the `pure` region. There is
--  no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The observable content of one source item that the default serialization
   reads: its chosen identifier rendered as text, and its own display text.
   These two renderings are taken as given observables of the item; the desired
   behavior does not change how either is computed (mapping.md §2). -/
structure Item where
  idText : String
  displayText : String
  deriving DecidableEq, Inhabited

/- A serialized result: an ordered association of string field names to string
   values — the object produced for one item. Modeled as an ordered list of
   key/value pairs so that additional fields may be present beyond the defaults
   (the customization the desired behavior must allow). -/
abbrev Serialized := List (String × String)

/- The default serialization of one item: an object carrying exactly the
   identifier field and the display-text field, in that order. -/
def defaultSerialized (it : Item) : Serialized :=
  [("id", it.idText), ("text", it.displayText)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The default per-item serialization: convert one source item into the result
   object for that item. It carries exactly the identifier field and the
   display-text field, in that order. `it` is read-only (not `mut`); the step
   constructs a fresh result and mutates nothing (directive 5). -/
method serializeResult (it : Item) return (out : Serialized)
  ensures out = defaultSerialized it
  do
    -- impl-start
    return ("id", it.idText) :: ("text", it.displayText) :: []
    -- impl-end

prove_correct serializeResult by
  loom_solve
  simp [defaultSerialized]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the results list from a list of source items by applying a single
   injected per-item serialization to each item, preserving order. The
   serialization `serialize` is supplied by the caller (its default is
   `serializeResult`); building the list applies whichever serialization is in
   effect to EVERY item — so a caller-supplied serialization takes effect for
   every result, and the count and order of the results equal those of the
   items. `items` and `serialize` are read-only (not `mut`); the step builds a
   fresh list and mutates neither input (directive 5). -/
method buildResults (items : List Item) (serialize : Item → Serialized)
    return (out : List Serialized)
  ensures out = items.map serialize
  do
    -- impl-start
    let results := items.map (fun x => serialize x)
    return results
    -- impl-end

prove_correct buildResults by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec = two exact-equality postconditions over a FREE universally-quantified serialize: serializeResult ensures out = defaultSerialized it = [("id",idText),("text",displayText)]; buildResults ensures out = items.map serialize. No axioms (G-AX skip); refinement.md all R/I, no kind-3; A-leg is the free-function model of the late-bound self.serialize_result(obj,to_field_name), which is strictly weaker than any concrete serializer and owes no contract (directive 7) — correspondence to the real callee holds.

Protocol executed. same_spec=True for ALL files (verified via swebench_unified.markers.same_spec, velvet). Verify command per file: `bash scripts/lean_verify.sh <file>`; runs launched concurrently in batches of 4.

8 DISTINCT same-spec wrong impls, ALL correctly REJECTED (exit 1) for the right reason:
- atk_1 PREPATCH BUG (items.map defaultSerialized, ignores injected serialize) exit=1, discriminating goal `List.map defaultSerialized items = List.map serialize items`. Bundle's own Solution_prepatch.lean independently reproduced (exit=1, identical goal). prepatch_reproduced=true.
- atk_2 drop text field exit=1 (⊢ False); atk_3 reversed field order exit=1 (ordered list pins insertion order); atk_4 return [] exit=1; atk_5 (items.map serialize).reverse exit=1; atk_6 swap id/text values exit=1; atk_7 partial-domain wrong-on-empty exit=1; atk_8 control-flow wrong-on-singleton (defaultSerialized) exit=1.
Every terminating wrong VALUE is rejected — the exact-equality postconditions over the free serialize leave no value-level slack; no ungrounded-oracle echo path exists (serialize is a free parameter, not an axiomatized answer key).

Positive control pos2.lean (structurally different but correct: items.map (fun x => serialize x); serializeResult via explicit cons) VERIFIES (exit 0) — spec non-vacuous at the value level. (An earlier control pos.lean using a reverse-reverse identity failed only because loom_solve did not discharge (map f xs.reverse).reverse = map f xs — a proof-tactic gap, not a spec defect; pos2 replaces it.)

ONE verifying attack: atk_9.lean (buildResults = `while true do i := i+1; return []`) VERIFIES (exit 0) — but SOLELY by NON-TERMINATION under the bundle's `set_option loom.semantics.termination "partial"`, the documented universal convention on every velvet/lean bundle (spec_guide.md:112), NOT a value-level weakness of THIS spec. Evidence it is a pure divergence artifact: its terminating twin atk_4 (`return []`, no loop) is REJECTED. atk_9 was therefore NOT submitted as an attack and requires no resolve run: a divergent Lean impl has no faithful TERMINATING refined patch — its faithful image is an infinite loop in get(), which is not a developer fix and would hang the harness (run_resolve cannot complete => INCONCLUSIVE, never BROKEN). It computes no observable wrong terminating value. Hence no verify⇏correct break: patches={} (no submitted attack verifies). This partial-correctness artifact is out of scope for refinement-fidelity/G-EQ and is not a legitimate counterexample.

Verdict: SOUND — 8 distinct same-spec wrong impls all rejected for the right reasons, prepatch reproduced, positive control verifies, and the sole verifier is the accepted non-termination artifact yielding no verify⇏correct break.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift check for django__django-14752 (velvet). same_spec(Solution, Solution_prepatch)=True with backend=velvet; spec view is signatures + pure model + empty pre/post, impl+proof elided. Solution.lean verifies (lean_verify exit 0); prepatch correctly FAILS the postcondition (unsolved goal List.map defaultSerialized items = List.map serialize items), confirming a genuine differentiator. conformance_check.py passes 100006 inputs (seed 14752, 0 disagreements).

Spec models two functions: (1) serializeResult => defaultSerialized = [("id",idText),("text",displayText)], modeling the real new default serialize_result returning {'id': str(getattr(obj,to_field_name)), 'text': str(obj)} — two-field insertion-ordered dict <-> ordered pair list, exact, no over-claim; (2) buildResults ensures out = items.map serialize, modeling the gold comprehension [self.serialize_result(obj,to_field_name) for obj in object_list] — order/count-preserving element-wise map. Critically, `serialize` is a FREE total function (universally quantified), which is strictly WEAKER than any concrete serializer, so the spec cannot be too strong here; the late-bound real method (default or subclass override) is just one instance. No input divides the modeled functions from the real callee: default serializer reproduced exactly, construction is exactly a map, order/count preserved. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical checks: same_spec(Solution.lean, Solution_prepatch.lean)=True (spec view byte-identical); leakage.screen passes clean (no hard_failures). Substantive review: the public problem_statement for django__django-14752 is exceptionally explicit — it verbatim proposes extracting serialize_result(self, obj, to_field_name) returning {'id': str(getattr(obj, to_field_name)), 'text': str(obj)} and rewriting the results comprehension to call self.serialize_result(obj, to_field_name) per object so subclasses can override it. The gold patch is a byte-level realization of that proposal. The spec view (Item{idText,displayText}, Serialized, defaultSerialized=[('id',…),('text',…)], serializeResult ensures out=defaultSerialized it, buildResults ensures out=items.map serialize over a FREE/overridable serialize) merely restates behavior already disclosed in the problem_statement: the {id,text} default shape and the overridable per-item serializer applied to every item. Impl bodies and proofs are elided. No gold-patch-specific detail (docstring change, method placement) is revealed beyond the public statement. The postconditions describe correct behavior derivable directly from the public description — the legitimate role of a spec, not a leak of the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

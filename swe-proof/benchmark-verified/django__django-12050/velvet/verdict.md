# P2 adversarial audit — django__django-12050

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-wrong-impl requiring a faithful-patch resolve run (the conditional resolve obligation is vacuous). The spec is fully deterministic: both ensures pin the output exactly — out.kind = value.kind AND out.elems = value.elems.map resolveElem — so any verifying impl produces exactly the gold behavior (type-preserving element-wise resolve). verify ⟹ correct holds.
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
 -- (No consumed callee contracts. The per-element resolution is modeled deeply
@@ -62,7 +62,7 @@
   do
     -- impl-start
     let resolvedElems := value.elems.map resolveElem
-    return { kind := value.kind, elems := resolvedElems }
+    return { kind := SeqKind.tuple, elems := resolvedElems }
     -- impl-end
 
 prove_correct resolveSeq by
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
 -- (No consumed callee contracts. The per-element resolution is modeled deeply
@@ -62,7 +62,7 @@
   do
     -- impl-start
     let resolvedElems := value.elems.map resolveElem
-    return { kind := value.kind, elems := resolvedElems }
+    return { kind := SeqKind.list, elems := resolvedElems }
     -- impl-end
 
 prove_correct resolveSeq by
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
 -- (No consumed callee contracts. The per-element resolution is modeled deeply
@@ -61,8 +61,7 @@
   ensures out.elems = value.elems.map resolveElem
   do
     -- impl-start
-    let resolvedElems := value.elems.map resolveElem
-    return { kind := value.kind, elems := resolvedElems }
+    return { kind := value.kind, elems := value.elems }
     -- impl-end
 
 prove_correct resolveSeq by
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
 -- (No consumed callee contracts. The per-element resolution is modeled deeply
@@ -61,8 +61,7 @@
   ensures out.elems = value.elems.map resolveElem
   do
     -- impl-start
-    let resolvedElems := value.elems.map resolveElem
-    return { kind := value.kind, elems := resolvedElems }
+    return { kind := value.kind, elems := [] }
     -- impl-end
 
 prove_correct resolveSeq by
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
 -- (No consumed callee contracts. The per-element resolution is modeled deeply
@@ -62,7 +62,7 @@
   do
     -- impl-start
     let resolvedElems := value.elems.map resolveElem
-    return { kind := value.kind, elems := resolvedElems }
+    return { kind := value.kind, elems := resolvedElems.reverse }
     -- impl-end
 
 prove_correct resolveSeq by
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
 -- (No consumed callee contracts. The per-element resolution is modeled deeply
@@ -62,7 +62,10 @@
   do
     -- impl-start
     let resolvedElems := value.elems.map resolveElem
-    return { kind := value.kind, elems := resolvedElems }
+    if value.kind = SeqKind.list then
+      return { kind := SeqKind.list, elems := resolvedElems }
+    else
+      return { kind := SeqKind.list, elems := resolvedElems }
     -- impl-end
 
 prove_correct resolveSeq by
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
 -- (No consumed callee contracts. The per-element resolution is modeled deeply
@@ -62,7 +62,7 @@
   do
     -- impl-start
     let resolvedElems := value.elems.map resolveElem
-    return { kind := value.kind, elems := resolvedElems }
+    return { kind := value.kind, elems := resolvedElems ++ resolvedElems }
     -- impl-end
 
 prove_correct resolveSeq by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-element resolution is modeled deeply
--  as an opaque total map `resolveElem` and validated element-wise against the
--  real per-element step — an A-reference, see refinement.md / mapping.md. It
--  is not pinned to any value, so no soundness is borrowed from it.)
-- axioms-end

-- pure-start
/- Two kinds of homogeneous ordered container that an input value may take when
   it is itself a sequence of sub-values. The behavior under spec turns on
   WHICH of the two kinds the input is, so the kind is a first-class tag with
   decidable equality. -/
inductive SeqKind where
  | list
  | tuple
  deriving DecidableEq, Inhabited

/- The per-element resolution of a single sub-value. It is the same map the
   operation already applied to each element before; the behavior under change
   does not touch it, so it is modeled opaquely (its concrete result is never
   relied upon — only that the SAME map is applied to every element). -/
opaque resolveElem : Int → Int

/- A sequence carrier: its kind tag together with its ordered elements. -/
structure SeqVal where
  kind : SeqKind
  elems : List Int
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An input value that is a homogeneous ordered sequence is resolved by
   resolving each of its sub-values independently and reassembling them into a
   sequence of the SAME kind as the input. Two guarantees pin the behavior the
   issue demands:

   - the kind of the result equals the kind of the input — a sequence of one
     kind must come back as the same kind (the type of the input sequence is
     preserved, never silently changed to the other kind);
   - the elements of the result are exactly the input elements with the
     per-element resolution applied, in order (an order-preserving element-wise
     map; the count and order are unchanged).

   `value` is read-only (not `mut`); the step constructs a fresh result and
   never mutates its input (directive 5). -/
method resolveSeq (value : SeqVal) return (out : SeqVal)
  ensures out.kind = value.kind
  ensures out.elems = value.elems.map resolveElem
  do
    -- impl-start
    let resolvedElems := value.elems.map resolveElem
    return { kind := value.kind, elems := resolvedElems }
    -- impl-end

prove_correct resolveSeq by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec with get_backend('velvet').language (only impl region edited; axioms/pure/pre/post byte-identical).

### VERIFY (bash scripts/lean_verify.sh <file>, run concurrently in 2 batches of ≤4):
  pos_control.lean  exit=0 (verifies, empty log, no sorry) — positive control PASSES.
  atk_1.lean exit=1 — prepatch bug re-encoded (kind forced SeqKind.tuple); unsolved goal 'SeqKind.tuple = value.kind'. PREPATCH REPRODUCED.
  atk_2.lean exit=1 — kind forced SeqKind.list; unsolved 'SeqKind.list = value.kind'.
  atk_3.lean exit=1 — ungrounded-oracle echo (elems := value.elems, resolveElem dropped); unsolved 'value.elems = List.map resolveElem value.elems'.
  atk_4.lean exit=1 — boundary (elems := []); unsolved '[] = List.map resolveElem value.elems'.
  atk_5.lean exit=1 — control-flow/order (resolvedElems.reverse); unsolved '(map).reverse = map'.
  atk_6.lean exit=1 — partial-domain (if kind=list ok, else still returns list — tuple branch wrong); unsolved 'SeqKind.list = value.kind' under ¬value.kind=list.
  atk_7.lean exit=1 — boundary/count (resolvedElems ++ resolvedElems); unsolved 'map ++ map = map'.

Attack families covered: partial-domain (atk_6), boundary (atk_2/4/7), control-flow-effect (atk_1/5), ungrounded-oracle echo (atk_3). >=5 DISTINCT wrong impls, all verified.

RESULT: 0 of 7 verifying-wrong-impls => no run_resolve obligation triggered (patches={}). Spec pins output exactly on both fields, so verify⇒correct cannot be broken by a same-spec impl.

REFINEMENT AUDIT (refinement.md): 3 legs — A1=R (SeqVal kind/elems <-> runtime container type + ordered sub-values), A2=A-reference (resolveElem: opaque unchanged per-element self.resolve_lookup_value; same map both legs, no value pinned, cancels in G-CONF), A3=I (return {kind:=value.kind,...} <-> type(value)(gen); the load-bearing type-preserving fix). No A-consumed, no kind-3 leg. A-reference correspondence holds: opacity + element-wise-only assertion means the modeled callee cannot contradict the real callee on any input (confirmed by G-CONF 100010 inputs/0 disagreements, seed 12050). The attacks that mutated the element observable (atk_3/4/5/7) all failed on the resolveElem clause, confirming the A-reference is load-bearing and correctly pinned.

VERDICT: SOUND. >=5 attacks run, none breaks the spec; positive control verifies; prepatch reproduced; refinement A-legs audited clean.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-wrong-impl requiring a faithful-patch resolve run (the conditional resolve obligation is vacuous). The spec is fully deterministic: both ensures pin the output exactly — out.kind = value.kind AND out.elems = value.elems.map resolveElem — so any verifying impl produces exactly the gold behavior (type-preserving element-wise resolve). verify ⟹ correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-element resolution is modeled deeply
--  as an opaque total map `resolveElem` and validated element-wise against the
--  real per-element step — an A-reference, see refinement.md / mapping.md. It
--  is not pinned to any value, so no soundness is borrowed from it.)
-- axioms-end

-- pure-start
/- Two kinds of homogeneous ordered container that an input value may take when
   it is itself a sequence of sub-values. The behavior under spec turns on
   WHICH of the two kinds the input is, so the kind is a first-class tag with
   decidable equality. -/
inductive SeqKind where
  | list
  | tuple
  deriving DecidableEq, Inhabited

/- The per-element resolution of a single sub-value. It is the same map the
   operation already applied to each element before; the behavior under change
   does not touch it, so it is modeled opaquely (its concrete result is never
   relied upon — only that the SAME map is applied to every element). -/
opaque resolveElem : Int → Int

/- A sequence carrier: its kind tag together with its ordered elements. -/
structure SeqVal where
  kind : SeqKind
  elems : List Int
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An input value that is a homogeneous ordered sequence is resolved by
   resolving each of its sub-values independently and reassembling them into a
   sequence of the SAME kind as the input. Two guarantees pin the behavior the
   issue demands:

   - the kind of the result equals the kind of the input — a sequence of one
     kind must come back as the same kind (the type of the input sequence is
     preserved, never silently changed to the other kind);
   - the elements of the result are exactly the input elements with the
     per-element resolution applied, in order (an order-preserving element-wise
     map; the count and order are unchanged).

   `value` is read-only (not `mut`); the step constructs a fresh result and
   never mutates its input (directive 5). -/
method resolveSeq (value : SeqVal) return (out : SeqVal)
  ensures out.kind = value.kind
  ensures out.elems = value.elems.map resolveElem
  do
    -- impl-start
    let resolvedElems := value.elems.map resolveElem
    return { kind := value.kind, elems := resolvedElems }
    -- impl-end

prove_correct resolveSeq by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec with get_backend('velvet').language (only impl region edited; axioms/pure/pre/post byte-identical).

### VERIFY (bash scripts/lean_verify.sh <file>, run concurrently in 2 batches of ≤4):
  pos_control.lean  exit=0 (verifies, empty log, no sorry) — positive control PASSES.
  atk_1.lean exit=1 — prepatch bug re-encoded (kind forced SeqKind.tuple); unsolved goal 'SeqKind.tuple = value.kind'. PREPATCH REPRODUCED.
  atk_2.lean exit=1 — kind forced SeqKind.list; unsolved 'SeqKind.list = value.kind'.
  atk_3.lean exit=1 — ungrounded-oracle echo (elems := value.elems, resolveElem dropped); unsolved 'value.elems = List.map resolveElem value.elems'.
  atk_4.lean exit=1 — boundary (elems := []); unsolved '[] = List.map resolveElem value.elems'.
  atk_5.lean exit=1 — control-flow/order (resolvedElems.reverse); unsolved '(map).reverse = map'.
  atk_6.lean exit=1 — partial-domain (if kind=list ok, else still returns list — tuple branch wrong); unsolved 'SeqKind.list = value.kind' under ¬value.kind=list.
  atk_7.lean exit=1 — boundary/count (resolvedElems ++ resolvedElems); unsolved 'map ++ map = map'.

Attack families covered: partial-domain (atk_6), boundary (atk_2/4/7), control-flow-effect (atk_1/5), ungrounded-oracle echo (atk_3). >=5 DISTINCT wrong impls, all verified.

RESULT: 0 of 7 verifying-wrong-impls => no run_resolve obligation triggered (patches={}). Spec pins output exactly on both fields, so verify⇒correct cannot be broken by a same-spec impl.

REFINEMENT AUDIT (refinement.md): 3 legs — A1=R (SeqVal kind/elems <-> runtime container type + ordered sub-values), A2=A-reference (resolveElem: opaque unchanged per-element self.resolve_lookup_value; same map both legs, no value pinned, cancels in G-CONF), A3=I (return {kind:=value.kind,...} <-> type(value)(gen); the load-bearing type-preserving fix). No A-consumed, no kind-3 leg. A-reference correspondence holds: opacity + element-wise-only assertion means the modeled callee cannot contradict the real callee on any input (confirmed by G-CONF 100010 inputs/0 disagreements, seed 12050). The attacks that mutated the element observable (atk_3/4/5/7) all failed on the resolveElem clause, confirming the A-reference is load-bearing and correctly pinned.

VERDICT: SOUND. >=5 attacks run, none breaks the spec; positive control verifies; prepatch reproduced; refinement A-legs audited clean.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec=True with velvet LanguageTables). Solution.lean verifies (lean_verify exit 0). The modeled callee is the post-patch (list,tuple) arm of Query.resolve_lookup_value: `return type(value)(resolve_lookup_value(sub) for sub in value)`. Postconditions: (1) out.kind = value.kind mirrors type(value)(...) preserving container type (list->list, tuple->tuple); (2) out.elems = value.elems.map resolveElem mirrors the order/count-preserving element-wise application of the (unchanged, A-reference) per-element resolution. Over the modeled domain (R-bijection restricts to type(value) is list / is tuple, mapping.md §2), no input makes the spec disagree with the real callee: for every list/tuple the gold produces the same-kind container with each element resolved in order — verified conceptually and by the in-process oracle in conformance_check.py (runs the actual type(value)(gen), 0 disagreements over boundary + 100k fuzz inputs, seed 12050). The spec is not stronger than real behavior. The only place type(value)(gen) diverges from 'kind preserved' is list/tuple SUBCLASSES (e.g. namedtuple, where type(value)(gen) raises), but those are explicitly outside the modeled domain — a coverage/too-weak concern, not a too-strong/faithfulness defect. No diverging input found; verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (leakage.screen over the lean spec view: passed=True, no hard failures). Semantic review confirms no leakage beyond the public problem_statement. The public problem_statement already fully discloses the required behavior: 'Query.resolve_lookup_value coerces value of type list to tuple ... The expected iterable return type should match input iterable type.' The load-bearing gold discriminator (preserve the input container type) is thus PUBLIC. Spec-view checks: (1) no diff markers, no patched file path 'query.py', no patched module path 'django.db.models...' present; (2) gold mechanism `return type(value)(gen)` is NOT reproduced — spec states only the observable `out.kind = value.kind`, i.e. the publicly-stated 'return type matches input type'; (3) patched symbol `resolve_lookup_value` is not echoed (spec method is `resolveSeq`; no comment names it — and it is public anyway); (4) no narration terms (bug/fix/patch/regression/etc.) in any comment — rationale prose is abstract ('the issue demands', 'type is preserved, never silently changed to the other kind'); (5) the second ensures clause `out.elems = value.elems.map resolveElem` models UNCHANGED pre-existing per-element resolution (opaque resolveElem, A-reference), not the gold discriminator. Spec region verified against Solution.lean; prepatch differs only in forcing kind:=SeqKind.tuple (the isolated discriminator), consistent with G-DIFF. No RELAXED_LEAKAGE deferral needed. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

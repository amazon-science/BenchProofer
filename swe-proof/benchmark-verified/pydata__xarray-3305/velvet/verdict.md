# P2 adversarial audit — pydata__xarray-3305

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axiom. The only foreign helper is the resolver of an ambient
@@ -76,12 +76,7 @@
   ensures out = keptAttrs srcAttrs choice glob
   do
     -- impl-start
-    let effective : Bool :=
-      match choice with
-      | some b => b
-      | none   => resolveGlobal glob false
-    let attrs : List (String × String) := if effective then srcAttrs else []
-    return attrs
+    return keptAttrs srcAttrs choice glob
     -- impl-end
 
 prove_correct reduceElementAttrs by
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axiom. The only foreign helper is the resolver of an ambient
@@ -76,12 +76,7 @@
   ensures out = keptAttrs srcAttrs choice glob
   do
     -- impl-start
-    let effective : Bool :=
-      match choice with
-      | some b => b
-      | none   => resolveGlobal glob false
-    let attrs : List (String × String) := if effective then srcAttrs else []
-    return attrs
+    return (if effectiveKeep choice glob then srcAttrs else [])
     -- impl-end
 
 prove_correct reduceElementAttrs by
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
 /- No consumed axiom. The only foreign helper is the resolver of an ambient
@@ -76,11 +76,7 @@
   ensures out = keptAttrs srcAttrs choice glob
   do
     -- impl-start
-    let effective : Bool :=
-      match choice with
-      | some b => b
-      | none   => resolveGlobal glob false
-    let attrs : List (String × String) := if effective then srcAttrs else []
+    let attrs : List (String × String) := srcAttrs
     return attrs
     -- impl-end
 
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
 /- No consumed axiom. The only foreign helper is the resolver of an ambient
@@ -80,7 +80,7 @@
       match choice with
       | some b => b
       | none   => resolveGlobal glob false
-    let attrs : List (String × String) := if effective then srcAttrs else []
+    let attrs : List (String × String) := if effective then [] else srcAttrs
     return attrs
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
 /- No consumed axiom. The only foreign helper is the resolver of an ambient
@@ -79,7 +79,7 @@
     let effective : Bool :=
       match choice with
       | some b => b
-      | none   => resolveGlobal glob false
+      | none   => resolveGlobal glob true
     let attrs : List (String × String) := if effective then srcAttrs else []
     return attrs
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
 /- No consumed axiom. The only foreign helper is the resolver of an ambient
@@ -100,7 +100,7 @@
   ensures out = keptAttrs srcAttrs choice glob
   do
     -- impl-start
-    let r ← reduceElementAttrs srcAttrs choice glob
+    let r ← reduceElementAttrs srcAttrs (some true) glob
     return r
     -- impl-end
 
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
 /- No consumed axiom. The only foreign helper is the resolver of an ambient
@@ -80,7 +80,8 @@
       match choice with
       | some b => b
       | none   => resolveGlobal glob false
-    let attrs : List (String × String) := if effective then srcAttrs else []
+    let attrs : List (String × String) :=
+      if effective then (if srcAttrs = [] then [] else srcAttrs) else []
     return attrs
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
/- No consumed axiom. The only foreign helper is the resolver of an ambient
   library-wide preference into a concrete boolean; it is an UNCHANGED pure
   callee modeled deeply as `resolveGlobal` below (an A-reference, validated
   `resolveGlobal == the real resolver` by axiom_check.py / G-AX), not an
   axiom the proof consumes. Provenance: mapping.md §3. -/
-- axioms-end

-- pure-start
/- The ambient, library-wide preference governing whether metadata is carried
   across a derived result when a caller does not state a per-call choice:
   * `gDefault` — defer to the operation's own fallback;
   * `gKeep`    — always carry metadata;
   * `gDrop`    — never carry metadata. -/
inductive GlobalPref where
  | gDefault
  | gKeep
  | gDrop
deriving DecidableEq, Inhabited, Repr

/- Resolve the ambient preference against an operation-supplied fallback.
   `gDefault` yields the fallback; the explicit settings override it. This is
   the deep model of the unchanged shared resolver (mapping.md §3.1). -/
def resolveGlobal (g : GlobalPref) (fallback : Bool) : Bool :=
  match g with
  | .gDefault => fallback
  | .gKeep    => true
  | .gDrop    => false

/- The effective keep-metadata decision for a single derived result. When the
   caller passes an explicit choice it is honored verbatim; when the caller
   leaves it unset, the decision falls back to the ambient preference resolved
   against the operation's own fallback (here: drop, i.e. `false`). This is the
   semantics every metadata-bearing reduction is expected to share. -/
def effectiveKeep (choice : Option Bool) (g : GlobalPref) : Bool :=
  match choice with
  | some b => b
  | none   => resolveGlobal g false

/- The metadata a derived result must carry: the source metadata when the
   effective decision keeps it, otherwise no metadata (the empty mapping).
   Metadata is modeled as an association list of key/value entries; "no
   metadata" is the empty list (mapping.md §2). -/
def keptAttrs (srcAttrs : List (String × String)) (choice : Option Bool)
    (g : GlobalPref) : List (String × String) :=
  if effectiveKeep choice g then srcAttrs else []
-- pure-end

-- pre-conditions-start
-- (No module-level preconditions; the operations are total in their inputs.)
-- pre-conditions-end

-- post-conditions-start
-- (Postconditions are the inline `ensures` clauses on each `method` below.)
-- post-conditions-end

/- Core element-wise reduction over an array's values, viewed only through the
   metadata it attaches to its derived result. The value/shape computation is
   orthogonal to this view and unchanged (mapping.md §2), so it is elided here.
   Like the other metadata-bearing reductions, this operation accepts an
   optional keep-metadata choice and must attach the source metadata exactly
   when the effective decision keeps it — honoring an explicit choice, and
   otherwise the ambient preference. The source metadata is read-only (not
   `mut`); the result is a freshly built mapping (directive 5). -/
method reduceElementAttrs (srcAttrs : List (String × String))
    (choice : Option Bool) (glob : GlobalPref)
    return (out : List (String × String))
  ensures out = keptAttrs srcAttrs choice glob
  do
    -- impl-start
    let effective : Bool :=
      match choice with
      | some b => b
      | none   => resolveGlobal glob false
    let attrs : List (String × String) := if effective then srcAttrs else []
    return attrs
    -- impl-end

prove_correct reduceElementAttrs by
  loom_solve
  simp_all [keptAttrs, effectiveKeep, resolveGlobal]

/- Container-level reduction that delegates to the element reduction for each
   member and reports the member's resulting metadata. The container must thread
   its own keep-metadata choice through to the element reduction unchanged;
   otherwise the member silently falls back to the ambient preference and the
   caller's explicit choice is lost. Modeled via callee-under-spec: the element
   reduction's contract is applied directly. -/
method reduceContainerAttrs (srcAttrs : List (String × String))
    (choice : Option Bool) (glob : GlobalPref)
    return (out : List (String × String))
  ensures out = keptAttrs srcAttrs choice glob
  do
    -- impl-start
    let r ← reduceElementAttrs srcAttrs choice glob
    return r
    -- impl-end

prove_correct reduceContainerAttrs by
  loom_solve

/- Labeled-array reduction: the user-facing wrapper. It forwards its
   keep-metadata choice to the container reduction and returns the resulting
   metadata. End to end, an explicit "keep" choice must surface the source
   metadata on the result. -/
method reduceLabeledAttrs (srcAttrs : List (String × String))
    (choice : Option Bool) (glob : GlobalPref)
    return (out : List (String × String))
  ensures out = keptAttrs srcAttrs choice glob
  do
    -- impl-start
    let r ← reduceContainerAttrs srcAttrs choice glob
    return r
    -- impl-end

prove_correct reduceLabeledAttrs by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec postcondition is exact equality out = keptAttrs srcAttrs choice glob, so every verifying impl is extensionally equal to the oracle. Positive control verifies (exit0). atk_2 (echo: `if effectiveKeep choice glob then srcAttrs else []`) is a same-spec (same_spec=True) VERIFYING wrong-impl; its faithful refined patch = the gold-behaviour transliteration and RESOLVED under the official harness (run_resolve: resolved=True, completed=True, flaky=False, retries=1). atk_1 (`return keptAttrs ...`) fails verify: loom_solve over-solves and the fixed trailing `simp_all` hits 'No goals' — behaviourally correct but the frozen proof script is brittle, so it does NOT verify (not a counterexample).

Divergent wrong-impls all FAIL verify, confirming spec tightness: atk_3 always-keep, atk_4 inverted branch, atk_5 wrong fallback (resolveGlobal glob true), atk_6 container passes (some true) dropping caller choice, atk_7 partial-domain guard (if srcAttrs=[] then [] else srcAttrs). prepatch reproduced: Solution_prepatch.lean (return [] always-empty attrs) fails verify (exit1, unsolved goals). refinement.md audit: all legs R / A-reference / I; no kind-3; no consumed axiom. A-reference resolveGlobal <-> _get_keep_attrs (=> _get_boolean_with_default) confirmed against real repo source: default->fallback, True->True, False->False; option setter restricts keep_attrs to {True,False,'default'} so the ValueError branch is unreachable; G-AX executes the real callee. No verifying wrong-impl yields a non-resolving faithful patch => verify does not over-admit here. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
/- No consumed axiom. The only foreign helper is the resolver of an ambient
   library-wide preference into a concrete boolean; it is an UNCHANGED pure
   callee modeled deeply as `resolveGlobal` below (an A-reference, validated
   `resolveGlobal == the real resolver` by axiom_check.py / G-AX), not an
   axiom the proof consumes. Provenance: mapping.md §3. -/
-- axioms-end

-- pure-start
/- The ambient, library-wide preference governing whether metadata is carried
   across a derived result when a caller does not state a per-call choice:
   * `gDefault` — defer to the operation's own fallback;
   * `gKeep`    — always carry metadata;
   * `gDrop`    — never carry metadata. -/
inductive GlobalPref where
  | gDefault
  | gKeep
  | gDrop
deriving DecidableEq, Inhabited, Repr

/- Resolve the ambient preference against an operation-supplied fallback.
   `gDefault` yields the fallback; the explicit settings override it. This is
   the deep model of the unchanged shared resolver (mapping.md §3.1). -/
def resolveGlobal (g : GlobalPref) (fallback : Bool) : Bool :=
  match g with
  | .gDefault => fallback
  | .gKeep    => true
  | .gDrop    => false

/- The effective keep-metadata decision for a single derived result. When the
   caller passes an explicit choice it is honored verbatim; when the caller
   leaves it unset, the decision falls back to the ambient preference resolved
   against the operation's own fallback (here: drop, i.e. `false`). This is the
   semantics every metadata-bearing reduction is expected to share. -/
def effectiveKeep (choice : Option Bool) (g : GlobalPref) : Bool :=
  match choice with
  | some b => b
  | none   => resolveGlobal g false

/- The metadata a derived result must carry: the source metadata when the
   effective decision keeps it, otherwise no metadata (the empty mapping).
   Metadata is modeled as an association list of key/value entries; "no
   metadata" is the empty list (mapping.md §2). -/
def keptAttrs (srcAttrs : List (String × String)) (choice : Option Bool)
    (g : GlobalPref) : List (String × String) :=
  if effectiveKeep choice g then srcAttrs else []
-- pure-end

-- pre-conditions-start
-- (No module-level preconditions; the operations are total in their inputs.)
-- pre-conditions-end

-- post-conditions-start
-- (Postconditions are the inline `ensures` clauses on each `method` below.)
-- post-conditions-end

/- Core element-wise reduction over an array's values, viewed only through the
   metadata it attaches to its derived result. The value/shape computation is
   orthogonal to this view and unchanged (mapping.md §2), so it is elided here.
   Like the other metadata-bearing reductions, this operation accepts an
   optional keep-metadata choice and must attach the source metadata exactly
   when the effective decision keeps it — honoring an explicit choice, and
   otherwise the ambient preference. The source metadata is read-only (not
   `mut`); the result is a freshly built mapping (directive 5). -/
method reduceElementAttrs (srcAttrs : List (String × String))
    (choice : Option Bool) (glob : GlobalPref)
    return (out : List (String × String))
  ensures out = keptAttrs srcAttrs choice glob
  do
    -- impl-start
    let effective : Bool :=
      match choice with
      | some b => b
      | none   => resolveGlobal glob false
    let attrs : List (String × String) := if effective then srcAttrs else []
    return attrs
    -- impl-end

prove_correct reduceElementAttrs by
  loom_solve
  simp_all [keptAttrs, effectiveKeep, resolveGlobal]

/- Container-level reduction that delegates to the element reduction for each
   member and reports the member's resulting metadata. The container must thread
   its own keep-metadata choice through to the element reduction unchanged;
   otherwise the member silently falls back to the ambient preference and the
   caller's explicit choice is lost. Modeled via callee-under-spec: the element
   reduction's contract is applied directly. -/
method reduceContainerAttrs (srcAttrs : List (String × String))
    (choice : Option Bool) (glob : GlobalPref)
    return (out : List (String × String))
  ensures out = keptAttrs srcAttrs choice glob
  do
    -- impl-start
    let r ← reduceElementAttrs srcAttrs choice glob
    return r
    -- impl-end

prove_correct reduceContainerAttrs by
  loom_solve

/- Labeled-array reduction: the user-facing wrapper. It forwards its
   keep-metadata choice to the container reduction and returns the resulting
   metadata. End to end, an explicit "keep" choice must surface the source
   metadata on the result. -/
method reduceLabeledAttrs (srcAttrs : List (String × String))
    (choice : Option Bool) (glob : GlobalPref)
    return (out : List (String × String))
  ensures out = keptAttrs srcAttrs choice glob
  do
    -- impl-start
    let r ← reduceContainerAttrs srcAttrs choice glob
    return r
    -- impl-end

prove_correct reduceLabeledAttrs by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec postcondition is exact equality out = keptAttrs srcAttrs choice glob, so every verifying impl is extensionally equal to the oracle. Positive control verifies (exit0). atk_2 (echo: `if effectiveKeep choice glob then srcAttrs else []`) is a same-spec (same_spec=True) VERIFYING wrong-impl; its faithful refined patch = the gold-behaviour transliteration and RESOLVED under the official harness (run_resolve: resolved=True, completed=True, flaky=False, retries=1). atk_1 (`return keptAttrs ...`) fails verify: loom_solve over-solves and the fixed trailing `simp_all` hits 'No goals' — behaviourally correct but the frozen proof script is brittle, so it does NOT verify (not a counterexample).

Divergent wrong-impls all FAIL verify, confirming spec tightness: atk_3 always-keep, atk_4 inverted branch, atk_5 wrong fallback (resolveGlobal glob true), atk_6 container passes (some true) dropping caller choice, atk_7 partial-domain guard (if srcAttrs=[] then [] else srcAttrs). prepatch reproduced: Solution_prepatch.lean (return [] always-empty attrs) fails verify (exit1, unsolved goals). refinement.md audit: all legs R / A-reference / I; no kind-3; no consumed axiom. A-reference resolveGlobal <-> _get_keep_attrs (=> _get_boolean_with_default) confirmed against real repo source: default->fallback, True->True, False->False; option setter restricts keep_attrs to {True,False,'default'} so the ValueError branch is unreachable; G-AX executes the real callee. No verifying wrong-impl yields a non-resolving faithful patch => verify does not over-admit here. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pydata__xarray-3305 (velvet). CONCLUSION: FAITHFUL — no input distinguishes the modeled function from the real repo callee.

SPEC INTEGRITY: same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True (velvet backend). The spec region (axioms/pure/pre/post + method sigs + ensures) is byte-identical across all three files; spec_view elides impl/proof cleanly.

MODEL: keptAttrs srcAttrs choice glob = if effectiveKeep choice glob then srcAttrs else []; effectiveKeep = some b -> b, none -> resolveGlobal glob false; resolveGlobal gDefault fallback=fallback, gKeep=true, gDrop=false. Verified at base_commit 69c7e01e that xarray.core.options._get_keep_attrs matches resolveGlobal exactly, and the variable.py fallback is default=False (matches the modeled `false`). Bijections: Option Bool <-> keep_attrs(bool/None), GlobalPref <-> OPTIONS['keep_attrs']('default'/True/False), List(String x String) <-> attrs(OrderedDict/None; empty<->[]).

EMPIRICAL DIFFERENTIAL (gold patch applied to a fresh base-commit worktree; shadow of spec semantics vs. real patched DataArray.quantile end-to-end, observing result .attrs):
  - 100,036 inputs (pinned seed 3305 boundary sets + fuzz over attrs x choice x glob): 0 disagreements.
  - Extended grid q in {0.25,[0.5],[0.25,0.75]} x dim in {None,'x',['x'],['x','y']} x choice x glob: 0 disagreements.
The real callee threads keep_attrs Dataset.quantile -> Variable.quantile and Variable attaches self._attrs iff keep_attrs, with None resolving through _get_keep_attrs(default=False) — exactly the modeled effectiveKeep/keptAttrs.

LEAN: scripts/lean_verify.sh on Solution.lean exits 0 — contract is real, not vacuous; all three composed methods carry the identical faithful ensures.

No diverging input found. The spec does not overconstrain relative to real repo behavior and does not drift from the gold patch on the tested observable (result attribute mapping).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet, _lean_spec_view) is clean. Mechanical leakage.screen() passes with zero hard_failures against problem_statement. same_spec(Solution, prepatch)=True and same_spec(Solution, prepatch_2)=True (byte-identical spec regions). Patch changed_symbols = {quantile, no_conflicts}; neither appears in any spec-view identifier or comment. No patched file path (variable.py/dataset.py), no dotted module path, no diff marker, no gold-patch line >=8 chars reproduced, no narration keyword. Repo symbols (_get_keep_attrs, OPTIONS, self._attrs, Variable/Dataset/DataArray.quantile) appear ONLY in refinement.md/mapping.md (auditor-facing, not the consumer spec view). The modeled behavior — honoring keep_attrs and preserving attrs on quantile — is already fully public via problem_statement ('DataArray.quantile does not honor keep_attrs', expected attrs preserved). The abstract identifiers (reduceElementAttrs/Container/Labeled, keptAttrs, effectiveKeep, resolveGlobal, GlobalPref) and the drop-fallback default (resolveGlobal g false) are expressed behaviorally, not as quotations of the gold edit; they localize no edit site. Spec does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
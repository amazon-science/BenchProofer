# P2 adversarial audit — sphinx-doc__sphinx-9281

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms. The behaviour under change — how a value is rendered to a
@@ -61,13 +61,10 @@
   ensures out = describe obj
   do
     -- impl-start
-    -- Classify the value: a member of an enumerated type is rendered with the
-    -- structured label `type.member`; anything else passes through with the
-    -- generic textual description it already had.
     let out : String :=
       match obj with
-      | .enumValue className memberName _ => className ++ "." ++ memberName
-      | .plain genericText                => genericText
+      | .enumValue _ _ genericText => genericText
+      | .plain genericText         => genericText
     return out
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
 /- No consumed axioms. The behaviour under change — how a value is rendered to a
@@ -61,12 +61,9 @@
   ensures out = describe obj
   do
     -- impl-start
-    -- Classify the value: a member of an enumerated type is rendered with the
-    -- structured label `type.member`; anything else passes through with the
-    -- generic textual description it already had.
     let out : String :=
       match obj with
-      | .enumValue className memberName _ => className ++ "." ++ memberName
+      | .enumValue className memberName _ => className ++ ":" ++ memberName
       | .plain genericText                => genericText
     return out
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
 /- No consumed axioms. The behaviour under change — how a value is rendered to a
@@ -61,12 +61,9 @@
   ensures out = describe obj
   do
     -- impl-start
-    -- Classify the value: a member of an enumerated type is rendered with the
-    -- structured label `type.member`; anything else passes through with the
-    -- generic textual description it already had.
     let out : String :=
       match obj with
-      | .enumValue className memberName _ => className ++ "." ++ memberName
+      | .enumValue className memberName _ => memberName ++ "." ++ className
       | .plain genericText                => genericText
     return out
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
 /- No consumed axioms. The behaviour under change — how a value is rendered to a
@@ -61,12 +61,9 @@
   ensures out = describe obj
   do
     -- impl-start
-    -- Classify the value: a member of an enumerated type is rendered with the
-    -- structured label `type.member`; anything else passes through with the
-    -- generic textual description it already had.
     let out : String :=
       match obj with
-      | .enumValue className memberName _ => className ++ "." ++ memberName
+      | .enumValue className memberName _ => className ++ memberName
       | .plain genericText                => genericText
     return out
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
 /- No consumed axioms. The behaviour under change — how a value is rendered to a
@@ -61,13 +61,10 @@
   ensures out = describe obj
   do
     -- impl-start
-    -- Classify the value: a member of an enumerated type is rendered with the
-    -- structured label `type.member`; anything else passes through with the
-    -- generic textual description it already had.
     let out : String :=
       match obj with
-      | .enumValue className memberName _ => className ++ "." ++ memberName
-      | .plain genericText                => genericText
+      | .enumValue _ memberName _ => memberName
+      | .plain genericText        => genericText
     return out
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
 /- No consumed axioms. The behaviour under change — how a value is rendered to a
@@ -61,13 +61,10 @@
   ensures out = describe obj
   do
     -- impl-start
-    -- Classify the value: a member of an enumerated type is rendered with the
-    -- structured label `type.member`; anything else passes through with the
-    -- generic textual description it already had.
     let out : String :=
       match obj with
       | .enumValue className memberName _ => className ++ "." ++ memberName
-      | .plain genericText                => genericText
+      | .plain _genericText               => ""
     return out
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
 /- No consumed axioms. The behaviour under change — how a value is rendered to a
@@ -61,14 +61,7 @@
   ensures out = describe obj
   do
     -- impl-start
-    -- Classify the value: a member of an enumerated type is rendered with the
-    -- structured label `type.member`; anything else passes through with the
-    -- generic textual description it already had.
-    let out : String :=
-      match obj with
-      | .enumValue className memberName _ => className ++ "." ++ memberName
-      | .plain genericText                => genericText
-    return out
+    return ""
     -- impl-end
 
 prove_correct objectDescription by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under change — how a value is rendered to a
   short, human-readable piece of text for display in API documentation — is
   modeled DEEPLY in the `pure` region (`describe`). The classification of a
   value and the structured rendering of an enumerated value are concrete data
   and operations, validated against the real renderer by G-CONF; there is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The display-relevant shape of the value being rendered. Two cases matter to
   the desired behaviour:

   * `enumValue className memberName genericText` — a member of an enumerated
     type. It exposes the name of its type (`className`) and the name of the
     member (`memberName`); `genericText` is what the generic textual fallback
     would otherwise produce for it (carried so the unchanged fallback path is
     observable, mapping.md §2).
   * `plain genericText` — any other value; `genericText` is the generic textual
     description already produced for it (the existing, unchanged behaviour). -/
inductive Obj where
  | enumValue (className : String) (memberName : String) (genericText : String)
  | plain (genericText : String)
  deriving DecidableEq

/- The desired rendering. A member of an enumerated type renders as its type
   name and member name joined by a dot — a short, evaluable label — instead of
   the verbose generic fallback. Every other value keeps the generic textual
   description it already had. This is the only distinction the desired
   behaviour draws. -/
def describe : Obj → String
  | .enumValue className memberName _ => className ++ "." ++ memberName
  | .plain genericText                => genericText

@[grind] lemma describe_enum (cn mn g : String) :
    describe (.enumValue cn mn g) = cn ++ "." ++ mn := rfl
@[grind] lemma describe_plain (g : String) :
    describe (.plain g) = g := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a value to a short piece of text safe for display in API
   documentation. Desired behaviour: a member of an enumerated type is shown by
   its type name and member name joined with a dot (a concise, evaluable label),
   while every other value keeps the generic textual description it already
   received. -/
method objectDescription (obj : Obj) return (out : String)
  ensures out = describe obj
  do
    -- impl-start
    -- Classify the value: a member of an enumerated type is rendered with the
    -- structured label `type.member`; anything else passes through with the
    -- generic textual description it already had.
    let out : String :=
      match obj with
      | .enumValue className memberName _ => className ++ "." ++ memberName
      | .plain genericText                => genericText
    return out
    -- impl-end

prove_correct objectDescription by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec shape: the postcondition is an EXACT functional equality `out = describe obj` where `describe : Obj -> String` is fully concrete (`.enumValue cn mn _ => cn ++ "." ++ mn`; `.plain g => g`). This pins the output for every input, making the spec maximally tight; no same-spec wrong impl can verify.

Protocol executed. same_spec verified True for all 7 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical), via swebench_unified.markers.same_spec + get_backend('velvet').language.

ATTACKS (each: `bash scripts/lean_verify.sh <path>`, all rc=1 = does NOT verify; all fail on the genuine goal `case ensures_1: out = describe obj`, NOT syntax errors — confirmed from stderr traces):
  atk_1 (prepatch bug reproduced: enum member falls through to genericText/verbose fallback) -> rc=1, unsolved goals.
  atk_2 (boundary: wrong separator ":" instead of ".") -> rc=1, unsolved goals (goal shows `... ++ ":" ++ ... = describe obj`).
  atk_3 (swapped order memberName ++ "." ++ className) -> rc=1, unsolved goals.
  atk_4 (boundary: dropped the dot separator, className ++ memberName) -> rc=1, unsolved goals.
  atk_5 (partial-domain: member name only) -> rc=1, unsolved goals.
  atk_6 (control-flow-effect / wrong plain leg: non-enum -> "") -> rc=1, unsolved goals.
  atk_7 (ungrounded/degenerate: constant `return ""` for all inputs) -> rc=1, unsolved goals (goal `"" = describe obj`).

Because NO wrong impl verifies, the set of verifying-wrong-impls is empty, so protocol step 2 requires zero resolve runs (no verify-but-not-resolve candidate can exist). To back the verify=>correct chain with executed evidence: positive_control.lean (byte copy of the bundle Solution.lean) VERIFIES (`bash scripts/lean_verify.sh positive_control.lean` -> rc=0), and its faithful patch (= patch.diff verbatim per refinement.md/G-RESOLVE) was RUN through the official harness: run_resolve('sphinx-doc__sphinx-9281', patch.diff, timeout=1200, retries=0) -> RESOLVED=True, completed=True, note='resolved'.

REFINEMENT.MD AUDIT: meta.json axioms=[] (no consumed axioms). The single changed behaviour is modeled DEEPLY via `describe`, recorded as a deep_model_reference (kind 'deep-model (R/I, not an axiom)'), checked by G-CONF (recorded pass, 0/100022 disagreements). Legs A1-A5 are R/R/(I+R)/I/R; Section B correctly asserts no kind-3 (inexpressible-changed-op) legs. A-reference correspondence holds: `describe (.enumValue cn mn _) = cn ++ "." ++ mn` <=> gold `return "%s.%s" % (object.__class__.__name__, object.name)`; `.plain g` <=> unchanged generic renderer, justified by the if->elif behaviour-neutrality argument over mutually-exclusive types (dict/set/frozenset/enum.Enum). No kind-3 leg, correspondence sound.

Conclusion: verify => correct holds for this bundle; no verifying same-spec wrong impl exists whose faithful patch fails to resolve. Verdict SOUND (>=5 distinct attacks run, none breaks the spec; gold patch resolve executed and confirmed).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under change — how a value is rendered to a
   short, human-readable piece of text for display in API documentation — is
   modeled DEEPLY in the `pure` region (`describe`). The classification of a
   value and the structured rendering of an enumerated value are concrete data
   and operations, validated against the real renderer by G-CONF; there is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The display-relevant shape of the value being rendered. Two cases matter to
   the desired behaviour:

   * `enumValue className memberName genericText` — a member of an enumerated
     type. It exposes the name of its type (`className`) and the name of the
     member (`memberName`); `genericText` is what the generic textual fallback
     would otherwise produce for it (carried so the unchanged fallback path is
     observable, mapping.md §2).
   * `plain genericText` — any other value; `genericText` is the generic textual
     description already produced for it (the existing, unchanged behaviour). -/
inductive Obj where
  | enumValue (className : String) (memberName : String) (genericText : String)
  | plain (genericText : String)
  deriving DecidableEq

/- The desired rendering. A member of an enumerated type renders as its type
   name and member name joined by a dot — a short, evaluable label — instead of
   the verbose generic fallback. Every other value keeps the generic textual
   description it already had. This is the only distinction the desired
   behaviour draws. -/
def describe : Obj → String
  | .enumValue className memberName _ => className ++ "." ++ memberName
  | .plain genericText                => genericText

@[grind] lemma describe_enum (cn mn g : String) :
    describe (.enumValue cn mn g) = cn ++ "." ++ mn := rfl
@[grind] lemma describe_plain (g : String) :
    describe (.plain g) = g := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a value to a short piece of text safe for display in API
   documentation. Desired behaviour: a member of an enumerated type is shown by
   its type name and member name joined with a dot (a concise, evaluable label),
   while every other value keeps the generic textual description it already
   received. -/
method objectDescription (obj : Obj) return (out : String)
  ensures out = describe obj
  do
    -- impl-start
    -- Classify the value: a member of an enumerated type is rendered with the
    -- structured label `type.member`; anything else passes through with the
    -- generic textual description it already had.
    let out : String :=
      match obj with
      | .enumValue className memberName _ => className ++ "." ++ memberName
      | .plain genericText                => genericText
    return out
    -- impl-end

prove_correct objectDescription by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec shape: the postcondition is an EXACT functional equality `out = describe obj` where `describe : Obj -> String` is fully concrete (`.enumValue cn mn _ => cn ++ "." ++ mn`; `.plain g => g`). This pins the output for every input, making the spec maximally tight; no same-spec wrong impl can verify.

Protocol executed. same_spec verified True for all 7 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical), via swebench_unified.markers.same_spec + get_backend('velvet').language.

ATTACKS (each: `bash scripts/lean_verify.sh <path>`, all rc=1 = does NOT verify; all fail on the genuine goal `case ensures_1: out = describe obj`, NOT syntax errors — confirmed from stderr traces):
  atk_1 (prepatch bug reproduced: enum member falls through to genericText/verbose fallback) -> rc=1, unsolved goals.
  atk_2 (boundary: wrong separator ":" instead of ".") -> rc=1, unsolved goals (goal shows `... ++ ":" ++ ... = describe obj`).
  atk_3 (swapped order memberName ++ "." ++ className) -> rc=1, unsolved goals.
  atk_4 (boundary: dropped the dot separator, className ++ memberName) -> rc=1, unsolved goals.
  atk_5 (partial-domain: member name only) -> rc=1, unsolved goals.
  atk_6 (control-flow-effect / wrong plain leg: non-enum -> "") -> rc=1, unsolved goals.
  atk_7 (ungrounded/degenerate: constant `return ""` for all inputs) -> rc=1, unsolved goals (goal `"" = describe obj`).

Because NO wrong impl verifies, the set of verifying-wrong-impls is empty, so protocol step 2 requires zero resolve runs (no verify-but-not-resolve candidate can exist). To back the verify=>correct chain with executed evidence: positive_control.lean (byte copy of the bundle Solution.lean) VERIFIES (`bash scripts/lean_verify.sh positive_control.lean` -> rc=0), and its faithful patch (= patch.diff verbatim per refinement.md/G-RESOLVE) was RUN through the official harness: run_resolve('sphinx-doc__sphinx-9281', patch.diff, timeout=1200, retries=0) -> RESOLVED=True, completed=True, note='resolved'.

REFINEMENT.MD AUDIT: meta.json axioms=[] (no consumed axioms). The single changed behaviour is modeled DEEPLY via `describe`, recorded as a deep_model_reference (kind 'deep-model (R/I, not an axiom)'), checked by G-CONF (recorded pass, 0/100022 disagreements). Legs A1-A5 are R/R/(I+R)/I/R; Section B correctly asserts no kind-3 (inexpressible-changed-op) legs. A-reference correspondence holds: `describe (.enumValue cn mn _) = cn ++ "." ++ mn` <=> gold `return "%s.%s" % (object.__class__.__name__, object.name)`; `.plain g` <=> unchanged generic renderer, justified by the if->elif behaviour-neutrality argument over mutually-exclusive types (dict/set/frozenset/enum.Enum). No kind-3 leg, correspondence sound.

Conclusion: verify => correct holds for this bundle; no verifying same-spec wrong impl exists whose faithful patch fails to resolve. Verdict SOUND (>=5 distinct attacks run, none breaks the spec; gold patch resolve executed and confirmed).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous check summary:

1. SPEC FROZEN: same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True. The describe/Obj spec region is byte-identical between patched and prepatch; prepatch differs only in impl and correctly fails G-DIFF. No spec drift between variants.

2. REAL CALLEE (sphinx/util/inspect.py:433 @ base_commit 8ec06e9a1, worktree): dispatch is `if dict / elif set / elif frozenset / elif enum.Enum: return "%s.%s"%(cls.__name__, name) / else repr->memaddr-strip->newline-replace`. Verified against the checked-out worktree source verbatim.

3. MODEL: describe(.enumValue cn mn _) = cn++"."++mn ; describe(.plain gt) = gt. The plain leg is tautological (gt IS the real generic rendering), so it cannot diverge. The only potential divergence is at the abstraction boundary alpha: Python-value -> Obj (enumValue vs plain).

4. AGREEMENT ON THE INTENDED DOMAIN: for every BARE (non-container) enum member the model and real callee both emit class.__name__ + '.' + name. Verified directly on Python 3.12: IntEnum, str-mixin Enum, combined Flag/IntFlag (name='R|W' -> 'Perm.R|W' on BOTH sides — the model uses obj.name so composite flags agree), and the issue's own UglyEnum.ValueA=10 example. Containers, scalars, custom-object repr/strip/newline all agree (plain leg = real).

5. THE ONE CANDIDATE DIVERGENCE (container-subclass enums, e.g. frozenset+Enum) is RESOLVED faithfully: the mechanized model (conformance_check.py shadow) orders container checks before the enum check, exactly mirroring the real elif chain, so F.A routes to the plain/frozenset rendering and AGREES. mapping.md §3.1 also explicitly documents that the if->elif rewrite is behaviour-neutral because dict/set/frozenset/Enum are treated in that dispatch order. I re-ran the shadow vs oracle on: frozenset-mixin (sortable + unsortable), int-mixin, mixed-type unsortable containers, nested enums in list/dict/set, combined flags — 0 disagreements. This matches G-CONF's recorded 0/100022.

6. RESIDUAL (NOT a faithfulness defect): (a) mapping.md §2 row-1 prose, read in isolation, is imprecise for the exotic container-subclass-enum case — but the operative artifact (shadow) and §3.1 pin the correct container-first ordering, so the modeled function does NOT actually disagree with the real callee on any input. (b) The G-CONF fuzz pool (ColorEnum/UglyEnum/IntFlavor/StrName) contains no container-subclass enums, a coverage gap — but adding them would still PASS because the shadow's dispatch order is correct. Neither weakens/over-strengthens the spec relative to real behavior.

CONCLUSION: The modeled describe (under its authoritative, mechanized abstraction) is behaviourally equal to the real patched object_description on all inputs I could construct. No input makes the model disagree with the real callee. Spec is not too strong and does not drift. FAITHFUL.

Counterexample / evidence:

```
object_description(F.A): real='frozenset({1, 2})' vs. literal-§2-prose model='F.A'. Resolved: the mechanized abstraction (conformance_check.py) checks dict/set/frozenset BEFORE enum.Enum, so F.A maps to Obj.plain with genericText='frozenset({1, 2})' and describe returns that — matching the real callee. Confirmed AGREE under the operative model.
```

Rigorous check summary:

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Adversarial leakage/gold-reconstruction review of the velvet spec view for sphinx-doc__sphinx-9281.

Gold edit (patch.diff): in sphinx/util/inspect.py, turn the sequential set/frozenset `if` checks into `elif` and insert `elif isinstance(object, enum.Enum): return "%s.%s" % (object.__class__.__name__, object.name)` before the generic repr() fallback.

Public problem_statement already discloses the full desired external behavior: enum values render 'ugly'; expected signature shows `MyEnum.ValueA`, actual shows `<MyEnum.ValueA: 10>`. So the discriminating behavior — an enum member should render as the dotted ClassName.MemberName label instead of the verbose fallback — is public. (Judged against problem_statement ONLY; hints_text, which names __repr__ and enum.Enum special-casing, is excluded per policy and not used to excuse anything.)

Spec view (computed via markers.spec_view over Solution.lean) encodes exactly that public behavior at behavioral altitude: an inductive `Obj` with `enumValue className memberName genericText` vs `plain genericText`, and `describe (.enumValue cn mn _) = cn ++ "." ++ mn` else `genericText`, with method `objectDescription` ensuring `out = describe obj`. This is the same observable outcome (`ClassName.MemberName`) the problem statement already shows.

Crucially, the spec view does NOT reveal edit-localization beyond the problem statement: no patched file path (inspect.py), no patched function name (object_description), no mention of the if→elif container refactor, no isinstance/enum.Enum/__class__.__name__/.name repo symbols, no diff markers, no bug/fix narration. Comments describe intended behavior ('member of an enumerated type', 'generic textual fallback') in abstract terms. The auditor-facing refinement.md/mapping.md (which DO name inspect.py, object_description, if->elif, enum.Enum) are NOT part of the consumer spec view and are out of scope for G-LEAK.

Mechanical G-LEAK screen (leakage.screen, velvet/lean flavor): PASSED, zero hard failures, zero warnings — no reproduced gold line, no diff marker, no patched path/module, no spec-view identifier or comment echoing a patched repo symbol, no narration.

Conclusion: the spec view leaks nothing about the gold edit beyond the public problem_statement. VERDICT: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

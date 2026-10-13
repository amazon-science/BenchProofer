# P2 adversarial audit — sphinx-doc__sphinx-9229

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees. The two modeled functions decide how an alias entry
@@ -97,10 +97,7 @@
   do
     -- impl-start
     if isAlias then
-      if commentPresent varComment then
-        return (some [])
-      else
-        return none
+      return (some [])
     else
       return normalDoc
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
 -- (No axiomatized callees. The two modeled functions decide how an alias entry
@@ -98,9 +98,9 @@
     -- impl-start
     if isAlias then
       if commentPresent varComment then
+        return none
+      else
         return (some [])
-      else
-        return none
     else
       return normalDoc
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
 -- (No axiomatized callees. The two modeled functions decide how an alias entry
@@ -97,7 +97,7 @@
   do
     -- impl-start
     if isAlias then
-      if commentPresent varComment then
+      if varComment.isSome then
         return (some [])
       else
         return none
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
 -- (No axiomatized callees. The two modeled functions decide how an alias entry
@@ -96,13 +96,7 @@
   ensures (isAlias = true ∧ commentPresent varComment = false) → out = none
   do
     -- impl-start
-    if isAlias then
-      if commentPresent varComment then
-        return (some [])
-      else
-        return none
-    else
-      return normalDoc
+    return normalDoc
     -- impl-end
 
 prove_correct aliasDocstrings by
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
 -- (No axiomatized callees. The two modeled functions decide how an alias entry
@@ -129,7 +129,7 @@
   ensures (isAlias = true ∧ commentPresent varComment = false) → out = aliasLabel
   do
     -- impl-start
-    if isAlias && !commentPresent varComment then
+    if isAlias then
       return aliasLabel
     else
       return incoming
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
 -- (No axiomatized callees. The two modeled functions decide how an alias entry
@@ -129,7 +129,7 @@
   ensures (isAlias = true ∧ commentPresent varComment = false) → out = aliasLabel
   do
     -- impl-start
-    if isAlias && !commentPresent varComment then
+    if isAlias && commentPresent varComment then
       return aliasLabel
     else
       return incoming
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
 -- (No axiomatized callees. The two modeled functions decide how an alias entry
@@ -129,10 +129,7 @@
   ensures (isAlias = true ∧ commentPresent varComment = false) → out = aliasLabel
   do
     -- impl-start
-    if isAlias && !commentPresent varComment then
-      return aliasLabel
-    else
-      return incoming
+    return incoming
     -- impl-end
 
 prove_correct aliasContentOverride by
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
 -- (No axiomatized callees. The two modeled functions decide how an alias entry
@@ -129,7 +129,7 @@
   ensures (isAlias = true ∧ commentPresent varComment = false) → out = aliasLabel
   do
     -- impl-start
-    if isAlias && !commentPresent varComment then
+    if isAlias && !varComment.isSome then
       return aliasLabel
     else
       return incoming
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two modeled functions decide how an alias entry
--  is documented; both decisions read the SAME two observations of the alias:
--  whether it is being documented as an alias at all, and the optional
--  doc-comment attached to the alias name in its source module. The doc-comment
--  lookup is an added helper whose result is carried here as the read-only input
--  `varComment : Option (List String)` (an R refinement, validated against the
--  real lookup by conformance_check.py / G-CONF); the documentation produced by
--  the ordinary, non-alias path is likewise carried as the read-only input
--  `normalDoc` (R), and the rendered alias label as `aliasLabel` (R). Every
--  observable is a closed function of these inputs — nothing is borrowed from an
--  oracle, and there is no unchanged library callee whose contract the proof must
--  axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether a doc-comment attached to an alias name is to be treated as present.
   The lookup yields an optional sequence of comment lines: it is ABSENT (`none`)
   when the alias's source could not be analysed, and otherwise a (possibly empty)
   sequence of lines. A comment counts as present exactly when that sequence is
   actually non-empty — so both "could not analyse" and "analysed but no comment"
   count as ABSENT. -/
@[grind] def commentPresent : Option (List String) → Bool
  | none    => false
  | some xs => !xs.isEmpty

/- The documentation an alias entry exposes.

   * For an alias (`isAlias = true`): if a doc-comment is present, the entry
     exposes an EMPTY docstring container (`some []`) — a real, if empty, body
     that lets the comment attached to the alias name be rendered as the entry's
     documentation; if no comment is present, the entry exposes NO docstring
     container at all (`none`), the long-standing behaviour for a bare alias.
   * Otherwise (`isAlias = false`): the entry exposes exactly the documentation
     produced by the ordinary documentation path (`normalDoc`), untouched.

   The distinction between `some []` (an empty container) and `none` (no
   container) is the whole point: they are genuinely different results and drive
   different downstream rendering. -/
@[grind] def docForAlias (isAlias : Bool) (varComment : Option (List String))
    (normalDoc : Option (List (List String))) : Option (List (List String)) :=
  if isAlias then
    (if commentPresent varComment then some [] else none)
  else
    normalDoc

/- The content forwarded for an alias entry. When the entry is an alias AND has
   no doc-comment present, its content is OVERRIDDEN with the rendered alias label
   (the "alias of …" line). In every other case — not an alias, or an alias that
   does carry a doc-comment — the incoming content is forwarded unchanged, so an
   alias with a doc-comment keeps its own documentation rather than being replaced
   by the alias label. -/
@[grind] def contentForAlias (isAlias : Bool) (varComment : Option (List String))
    (incoming aliasLabel : List String) : List String :=
  if isAlias && !commentPresent varComment then aliasLabel else incoming
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The documentation an entry exposes, for an entry that may be an alias.

   `isAlias` (read-only) selects the regime. When it is false, the entry exposes
   the ordinary documentation `normalDoc` unchanged. When it is true, the entry
   is an alias and the result is governed by the OPTIONAL doc-comment `varComment`
   attached to the alias name:
   - when a comment is PRESENT (a non-empty line sequence), the entry exposes an
     empty docstring container `some []`, so the comment can be shown as the
     entry's documentation;
   - when NO comment is present (the lookup is absent, or present but empty), the
     entry exposes no docstring container, `none`.

   The optional comment is modeled as `Option (List String)` so that "could not
   analyse the source" (`none`) and "analysed, no comment" (`some []`) are
   genuinely different inputs that nonetheless agree on the decision; the result
   is `Option (List (List String))` so that "an empty container" (`some []`) and
   "no container" (`none`) are genuinely different outputs. `isAlias`,
   `varComment` and `normalDoc` are read-only (not `mut`): a fresh result is
   built and none of them is mutated (directive 5). -/
method aliasDocstrings (isAlias : Bool) (varComment : Option (List String))
    (normalDoc : Option (List (List String)))
    return (out : Option (List (List String)))
  ensures out = docForAlias isAlias varComment normalDoc
  ensures (isAlias = true ∧ commentPresent varComment = true) → out = some []
  ensures (isAlias = true ∧ commentPresent varComment = false) → out = none
  do
    -- impl-start
    if isAlias then
      if commentPresent varComment then
        return (some [])
      else
        return none
    else
      return normalDoc
    -- impl-end

prove_correct aliasDocstrings by
  loom_solve

/- The content forwarded for an entry that may be an alias.

   `isAlias` (read-only) says whether the entry is being documented as an alias.
   When it is, the content is replaced by the rendered alias label `aliasLabel`
   ONLY when no doc-comment is present for the alias name; if a doc-comment IS
   present, the incoming content `incoming` is forwarded unchanged so the alias
   keeps its own documentation instead of being replaced by the alias label. When
   the entry is not an alias, the incoming content is always forwarded unchanged.

   `isAlias`, `varComment`, `incoming` and `aliasLabel` are read-only (not `mut`):
   the routine chooses which sequence to forward and mutates none of its inputs
   (directive 5). The incoming content is pinned to be forwarded unchanged
   whenever the override does not apply, so no result component is left free. -/
method aliasContentOverride (isAlias : Bool) (varComment : Option (List String))
    (incoming : List String) (aliasLabel : List String)
    return (out : List String)
  ensures out = contentForAlias isAlias varComment incoming aliasLabel
  ensures (isAlias = true ∧ commentPresent varComment = true) → out = incoming
  ensures (isAlias = true ∧ commentPresent varComment = false) → out = aliasLabel
  do
    -- impl-start
    if isAlias && !commentPresent varComment then
      return aliasLabel
    else
      return incoming
    -- impl-end

prove_correct aliasContentOverride by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for sphinx-doc__sphinx-9229 (velvet). verify cmd `bash scripts/lean_verify.sh <file>` (0=verifies, 1=error, 3=sorry, 124=timeout); same_spec via swebench_unified.markers.same_spec with velvet backend.

SPEC SHAPE: two methods, each pinned by a TOTAL functional equality post-condition (out = docForAlias isAlias varComment normalDoc / out = contentForAlias isAlias varComment incoming aliasLabel) PLUS two guarded clauses per method fixing the alias+comment and alias+no-comment cases. commentPresent none=false, some xs = !xs.isEmpty (so `some []` counts as absent — the None/[] vs non-empty boundary). No axioms, no deep-model references (meta.json axioms=[], deep_model_references=[]) — confirmed; the A-legs the protocol targets do not exist here, all legs are R/I.

POSITIVE CONTROL: pos_control.lean (byte copy of Solution.lean) verifies EXIT=0.

PREPATCH REPRODUCED: prepatch_1.lean (alias always returns none) EXIT=1 unsolved goals at prove_correct (fails (isAlias∧commentPresent)→some []); prepatch_2.lean (alias content always overridden) EXIT=1 unsolved goals (fails (isAlias∧commentPresent)→incoming). Both same_spec=True.

8 DISTINCT SAME-SPEC WRONG IMPLS (all same_spec=True, all EXIT=1 genuine `error: unsolved goals` at prove_correct — NONE verified):
- atk_1 (partial-domain, docstrings): alias always `some []`, ignores comment absence. FAIL @105.
- atk_2 (boundary swap, docstrings): returns none when comment present, some [] when absent. FAIL @108.
- atk_3 (empty-list boundary / ungrounded-oracle echo, docstrings): uses varComment.isSome instead of commentPresent, so `some []` treated as present → some []. FAIL @108.
- atk_4 (control-flow-effect, docstrings): drops alias branch entirely, always normalDoc. FAIL @102.
- atk_5 (control-flow-effect, content, = prepatch_2 shape): alias content always overridden. FAIL @138.
- atk_6 (boundary swap, content): override guard uses commentPresent instead of !commentPresent. FAIL @138.
- atk_7 (partial-domain / echo, content): always forwards incoming, never overrides. FAIL @135.
- atk_8 (empty-list boundary, content): override when alias && !varComment.isSome, so `some []` blocks override. FAIL @138.
Covers partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, and the two prepatch bugs, on both methods and both the isSome-vs-nonempty boundary and the guard-polarity boundary.

Since NO wrong impl verified, no faithful refined patch needed to be materialized or run through run_resolve (the BROKEN condition — a verifying wrong impl whose faithful patch does not resolve — cannot be triggered). patches map intentionally empty.

MODEL↔PATCH CORRESPONDENCE (sole trust point, no axioms): gold patch (from data/swe_bench_verified/test.jsonl) changes get_doc alias branch to `comment=self.get_variable_comment(); if comment: return [] else: return None` (↔ docForAlias with commentPresent=Python list truthiness, some[]↔[], none↔None) and add_content guard to `if self.doc_as_attr and not self.get_variable_comment():` (↔ contentForAlias override iff isAlias && !commentPresent). Correspondence holds exactly; conformance_check.py differentially exercises the shadow against the real patched get_doc/add_content over boundary + 1e5 fuzz (seed 9229). refinement.md audited: every leg R or I, no kind-3, claim of no A-legs verified against meta.json.

VERDICT: SOUND — 8 adversarial same-spec attacks (≥5 required, spanning all requested classes) all fail to verify with genuine unsolved-goals, positive control verifies, both prepatches reproduce; spec's total functional post-conditions leave no room for a verifying wrong impl, so verify⇒correct holds. No resolve run was required because none was triggerable.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two modeled functions decide how an alias entry
--  is documented; both decisions read the SAME two observations of the alias:
--  whether it is being documented as an alias at all, and the optional
--  doc-comment attached to the alias name in its source module. The doc-comment
--  lookup is an added helper whose result is carried here as the read-only input
--  `varComment : Option (List String)` (an R refinement, validated against the
--  real lookup by conformance_check.py / G-CONF); the documentation produced by
--  the ordinary, non-alias path is likewise carried as the read-only input
--  `normalDoc` (R), and the rendered alias label as `aliasLabel` (R). Every
--  observable is a closed function of these inputs — nothing is borrowed from an
--  oracle, and there is no unchanged library callee whose contract the proof must
--  axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether a doc-comment attached to an alias name is to be treated as present.
   The lookup yields an optional sequence of comment lines: it is ABSENT (`none`)
   when the alias's source could not be analysed, and otherwise a (possibly empty)
   sequence of lines. A comment counts as present exactly when that sequence is
   actually non-empty — so both "could not analyse" and "analysed but no comment"
   count as ABSENT. -/
@[grind] def commentPresent : Option (List String) → Bool
  | none    => false
  | some xs => !xs.isEmpty

/- The documentation an alias entry exposes.

   * For an alias (`isAlias = true`): if a doc-comment is present, the entry
     exposes an EMPTY docstring container (`some []`) — a real, if empty, body
     that lets the comment attached to the alias name be rendered as the entry's
     documentation; if no comment is present, the entry exposes NO docstring
     container at all (`none`), the long-standing behaviour for a bare alias.
   * Otherwise (`isAlias = false`): the entry exposes exactly the documentation
     produced by the ordinary documentation path (`normalDoc`), untouched.

   The distinction between `some []` (an empty container) and `none` (no
   container) is the whole point: they are genuinely different results and drive
   different downstream rendering. -/
@[grind] def docForAlias (isAlias : Bool) (varComment : Option (List String))
    (normalDoc : Option (List (List String))) : Option (List (List String)) :=
  if isAlias then
    (if commentPresent varComment then some [] else none)
  else
    normalDoc

/- The content forwarded for an alias entry. When the entry is an alias AND has
   no doc-comment present, its content is OVERRIDDEN with the rendered alias label
   (the "alias of …" line). In every other case — not an alias, or an alias that
   does carry a doc-comment — the incoming content is forwarded unchanged, so an
   alias with a doc-comment keeps its own documentation rather than being replaced
   by the alias label. -/
@[grind] def contentForAlias (isAlias : Bool) (varComment : Option (List String))
    (incoming aliasLabel : List String) : List String :=
  if isAlias && !commentPresent varComment then aliasLabel else incoming
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The documentation an entry exposes, for an entry that may be an alias.

   `isAlias` (read-only) selects the regime. When it is false, the entry exposes
   the ordinary documentation `normalDoc` unchanged. When it is true, the entry
   is an alias and the result is governed by the OPTIONAL doc-comment `varComment`
   attached to the alias name:
   - when a comment is PRESENT (a non-empty line sequence), the entry exposes an
     empty docstring container `some []`, so the comment can be shown as the
     entry's documentation;
   - when NO comment is present (the lookup is absent, or present but empty), the
     entry exposes no docstring container, `none`.

   The optional comment is modeled as `Option (List String)` so that "could not
   analyse the source" (`none`) and "analysed, no comment" (`some []`) are
   genuinely different inputs that nonetheless agree on the decision; the result
   is `Option (List (List String))` so that "an empty container" (`some []`) and
   "no container" (`none`) are genuinely different outputs. `isAlias`,
   `varComment` and `normalDoc` are read-only (not `mut`): a fresh result is
   built and none of them is mutated (directive 5). -/
method aliasDocstrings (isAlias : Bool) (varComment : Option (List String))
    (normalDoc : Option (List (List String)))
    return (out : Option (List (List String)))
  ensures out = docForAlias isAlias varComment normalDoc
  ensures (isAlias = true ∧ commentPresent varComment = true) → out = some []
  ensures (isAlias = true ∧ commentPresent varComment = false) → out = none
  do
    -- impl-start
    if isAlias then
      if commentPresent varComment then
        return (some [])
      else
        return none
    else
      return normalDoc
    -- impl-end

prove_correct aliasDocstrings by
  loom_solve

/- The content forwarded for an entry that may be an alias.

   `isAlias` (read-only) says whether the entry is being documented as an alias.
   When it is, the content is replaced by the rendered alias label `aliasLabel`
   ONLY when no doc-comment is present for the alias name; if a doc-comment IS
   present, the incoming content `incoming` is forwarded unchanged so the alias
   keeps its own documentation instead of being replaced by the alias label. When
   the entry is not an alias, the incoming content is always forwarded unchanged.

   `isAlias`, `varComment`, `incoming` and `aliasLabel` are read-only (not `mut`):
   the routine chooses which sequence to forward and mutates none of its inputs
   (directive 5). The incoming content is pinned to be forwarded unchanged
   whenever the override does not apply, so no result component is left free. -/
method aliasContentOverride (isAlias : Bool) (varComment : Option (List String))
    (incoming : List String) (aliasLabel : List String)
    return (out : List String)
  ensures out = contentForAlias isAlias varComment incoming aliasLabel
  ensures (isAlias = true ∧ commentPresent varComment = true) → out = incoming
  ensures (isAlias = true ∧ commentPresent varComment = false) → out = aliasLabel
  do
    -- impl-start
    if isAlias && !commentPresent varComment then
      return aliasLabel
    else
      return incoming
    -- impl-end

prove_correct aliasContentOverride by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for sphinx-doc__sphinx-9229 (velvet). verify cmd `bash scripts/lean_verify.sh <file>` (0=verifies, 1=error, 3=sorry, 124=timeout); same_spec via swebench_unified.markers.same_spec with velvet backend.

SPEC SHAPE: two methods, each pinned by a TOTAL functional equality post-condition (out = docForAlias isAlias varComment normalDoc / out = contentForAlias isAlias varComment incoming aliasLabel) PLUS two guarded clauses per method fixing the alias+comment and alias+no-comment cases. commentPresent none=false, some xs = !xs.isEmpty (so `some []` counts as absent — the None/[] vs non-empty boundary). No axioms, no deep-model references (meta.json axioms=[], deep_model_references=[]) — confirmed; the A-legs the protocol targets do not exist here, all legs are R/I.

POSITIVE CONTROL: pos_control.lean (byte copy of Solution.lean) verifies EXIT=0.

PREPATCH REPRODUCED: prepatch_1.lean (alias always returns none) EXIT=1 unsolved goals at prove_correct (fails (isAlias∧commentPresent)→some []); prepatch_2.lean (alias content always overridden) EXIT=1 unsolved goals (fails (isAlias∧commentPresent)→incoming). Both same_spec=True.

8 DISTINCT SAME-SPEC WRONG IMPLS (all same_spec=True, all EXIT=1 genuine `error: unsolved goals` at prove_correct — NONE verified):
- atk_1 (partial-domain, docstrings): alias always `some []`, ignores comment absence. FAIL @105.
- atk_2 (boundary swap, docstrings): returns none when comment present, some [] when absent. FAIL @108.
- atk_3 (empty-list boundary / ungrounded-oracle echo, docstrings): uses varComment.isSome instead of commentPresent, so `some []` treated as present → some []. FAIL @108.
- atk_4 (control-flow-effect, docstrings): drops alias branch entirely, always normalDoc. FAIL @102.
- atk_5 (control-flow-effect, content, = prepatch_2 shape): alias content always overridden. FAIL @138.
- atk_6 (boundary swap, content): override guard uses commentPresent instead of !commentPresent. FAIL @138.
- atk_7 (partial-domain / echo, content): always forwards incoming, never overrides. FAIL @135.
- atk_8 (empty-list boundary, content): override when alias && !varComment.isSome, so `some []` blocks override. FAIL @138.
Covers partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, and the two prepatch bugs, on both methods and both the isSome-vs-nonempty boundary and the guard-polarity boundary.

Since NO wrong impl verified, no faithful refined patch needed to be materialized or run through run_resolve (the BROKEN condition — a verifying wrong impl whose faithful patch does not resolve — cannot be triggered). patches map intentionally empty.

MODEL↔PATCH CORRESPONDENCE (sole trust point, no axioms): gold patch (from data/swe_bench_verified/test.jsonl) changes get_doc alias branch to `comment=self.get_variable_comment(); if comment: return [] else: return None` (↔ docForAlias with commentPresent=Python list truthiness, some[]↔[], none↔None) and add_content guard to `if self.doc_as_attr and not self.get_variable_comment():` (↔ contentForAlias override iff isAlias && !commentPresent). Correspondence holds exactly; conformance_check.py differentially exercises the shadow against the real patched get_doc/add_content over boundary + 1e5 fuzz (seed 9229). refinement.md audited: every leg R or I, no kind-3, claim of no A-legs verified against meta.json.

VERDICT: SOUND — 8 adversarial same-spec attacks (≥5 required, spanning all requested classes) all fail to verify with genuine unsolved-goals, positive control verifies, both prepatches reproduce; spec's total functional post-conditions leave no room for a verifying wrong impl, so verify⇒correct holds. No resolve run was required because none was triggerable.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of sphinx-doc__sphinx-9229 velvet bundle. (1) same_spec confirms the spec region (axioms/pure/pre/post + method signatures + ensures) is byte-identical across Solution.lean, Solution_prepatch_1.lean, Solution_prepatch_2.lean (only impl/proof regions differ). (2) The two modeled functions are exact transliterations of the gold patch: docForAlias mirrors get_doc's alias branch (`return [] if comment else None`; normalDoc otherwise) and contentForAlias mirrors add_content's guard (`doc_as_attr and not get_variable_comment()` -> alias label, else forward incoming). Confirmed against base_commit 876fa81e source and patch.diff. (3) commentPresent faithfully models Python truthiness of Optional[List[str]] (None->false, []->false, non-empty->true) — verified explicitly including edge lists like [""] and ["",""], which are truthy in Python and modeled as present. No divergence. (4) normalDoc non-alias leg is a correct R-identity; the fix never touches that path. (5) Lean verifies (lean_verify.sh exit 0); G-CONF passed 10^5 inputs against the real patched ClassDocumenter. Only abstraction boundary is the try/except AttributeError around alias-label CONSTRUCTION in add_content: if restify(self.object) raised, real code forwards incoming while model returns aliasLabel — but this is outside the modeled input domain (aliasLabel : List String presupposes a constructed label; when construction fails there is no such input value), is explicitly disclosed (refinement.md B4/C, mapping 3.2), and does not affect resolved F2P behavior (the F2P alias target constructs fine). This is a legitimate, disclosed refinement boundary, NOT a spec-too-strong drift. No input within the modeled domain makes the spec disagree with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view for sphinx-doc__sphinx-9229/velvet judged for gold-edit leakage beyond the public problem_statement (hints_text empty; excluded per policy).

Lexical screen: leakage.screen() PASSES (hard_failures=[], warnings=[]) — verified live with the frozen row's patch + problem_statement. Spec view contains NO gold-diff line, NO diff markers, NO patched file path (sphinx/ext/autodoc/__init__.py), and NONE of the patch's distinctive changed symbols (get_doc, get_variable_comment, get_object_members) — none appear in the spec view (only the generic word 'docstring', which is not a repo symbol). No bug/fix narration terms.

spec_view (impl + prove_correct bodies elided) exposes only abstract Velvet models: commentPresent / docForAlias / contentForAlias and the two method signatures aliasDocstrings / aliasContentOverride with their ensures clauses. These describe the DESIRED OBSERVABLE behavior: an alias entry with an attached doc-comment retains its own documentation rather than being replaced by the 'alias of …' label; an alias without a comment shows the label. That behavior is exactly what the public problem_statement already states ('The docs should show the contents in the docstrings for all the type aliases instead of the ``alias of ...`` default text'). The some [] vs none modeling distinction is a faithful formalization of the observable rendering difference, not a disclosure of the gold's mechanism (added helper name, `return []`, guard `and not self.get_variable_comment()`, or file/line) — those specifics live only in refinement.md/mapping.md/patch.diff, which are NOT part of the consumer spec view.

Ancillary checks: same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True, so the prepatches do not perturb the spec signature. meta G-LEAK status = pass ('spec view clean'); relaxed_leakage=None (no RELAXED_LEAKAGE deferral in play). No leak of the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

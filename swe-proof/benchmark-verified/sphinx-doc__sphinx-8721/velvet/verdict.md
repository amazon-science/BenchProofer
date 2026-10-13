# P2 adversarial audit — sphinx-doc__sphinx-8721

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_1_epub_only.lean`, `atk_2_single_only.lean`, `atk_3_ignore_optin.lean`, `atk_4_epub_exacteq.lean`, `atk_5_drop_hasmodules.lean`, `atk_6_single_prefix.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The gating decision is a closed function of the
@@ -82,19 +82,10 @@
             (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
   do
     -- impl-start
-    -- Nothing was collected: emit nothing.
     if !hasModules then
       return []
     else
-      -- The single combined-document format hosts no separate companion pages.
-      if isCombinedFormat fmt then
-        return []
-      else
-        -- Suppress for the e-book family unless the project opted in.
-        if isEbookFormat fmt && !ebookOptIn then
-          return []
-        else
-          return generated
+      return generated
     -- impl-end
 
 prove_correct gatedPageEmission by
```

Attack 2 — `atk_1_epub_only.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The gating decision is a closed function of the
@@ -82,19 +82,13 @@
             (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
   do
     -- impl-start
-    -- Nothing was collected: emit nothing.
     if !hasModules then
       return []
     else
-      -- The single combined-document format hosts no separate companion pages.
-      if isCombinedFormat fmt then
+      if isEbookFormat fmt && !ebookOptIn then
         return []
       else
-        -- Suppress for the e-book family unless the project opted in.
-        if isEbookFormat fmt && !ebookOptIn then
-          return []
-        else
-          return generated
+        return generated
     -- impl-end
 
 prove_correct gatedPageEmission by
```

Attack 3 — `atk_2_single_only.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The gating decision is a closed function of the
@@ -82,19 +82,13 @@
             (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
   do
     -- impl-start
-    -- Nothing was collected: emit nothing.
     if !hasModules then
       return []
     else
-      -- The single combined-document format hosts no separate companion pages.
       if isCombinedFormat fmt then
         return []
       else
-        -- Suppress for the e-book family unless the project opted in.
-        if isEbookFormat fmt && !ebookOptIn then
-          return []
-        else
-          return generated
+        return generated
     -- impl-end
 
 prove_correct gatedPageEmission by
```

Attack 4 — `atk_3_ignore_optin.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The gating decision is a closed function of the
@@ -82,16 +82,13 @@
             (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
   do
     -- impl-start
-    -- Nothing was collected: emit nothing.
     if !hasModules then
       return []
     else
-      -- The single combined-document format hosts no separate companion pages.
       if isCombinedFormat fmt then
         return []
       else
-        -- Suppress for the e-book family unless the project opted in.
-        if isEbookFormat fmt && !ebookOptIn then
+        if isEbookFormat fmt then
           return []
         else
           return generated
```

Attack 5 — `atk_4_epub_exacteq.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The gating decision is a closed function of the
@@ -82,16 +82,13 @@
             (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
   do
     -- impl-start
-    -- Nothing was collected: emit nothing.
     if !hasModules then
       return []
     else
-      -- The single combined-document format hosts no separate companion pages.
       if isCombinedFormat fmt then
         return []
       else
-        -- Suppress for the e-book family unless the project opted in.
-        if isEbookFormat fmt && !ebookOptIn then
+        if fmt == "epub".toList && !ebookOptIn then
           return []
         else
           return generated
```

Attack 6 — `atk_5_drop_hasmodules.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The gating decision is a closed function of the
@@ -82,19 +82,13 @@
             (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
   do
     -- impl-start
-    -- Nothing was collected: emit nothing.
-    if !hasModules then
+    if isCombinedFormat fmt then
       return []
     else
-      -- The single combined-document format hosts no separate companion pages.
-      if isCombinedFormat fmt then
+      if isEbookFormat fmt && !ebookOptIn then
         return []
       else
-        -- Suppress for the e-book family unless the project opted in.
-        if isEbookFormat fmt && !ebookOptIn then
-          return []
-        else
-          return generated
+        return generated
     -- impl-end
 
 prove_correct gatedPageEmission by
```

Attack 7 — `atk_6_single_prefix.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The gating decision is a closed function of the
@@ -82,15 +82,12 @@
             (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
   do
     -- impl-start
-    -- Nothing was collected: emit nothing.
     if !hasModules then
       return []
     else
-      -- The single combined-document format hosts no separate companion pages.
-      if isCombinedFormat fmt then
+      if "singlehtml".toList.isPrefixOf fmt then
         return []
       else
-        -- Suppress for the e-book family unless the project opted in.
         if isEbookFormat fmt && !ebookOptIn then
           return []
         else
```

Attack 8 — `atk_7_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The gating decision is a closed function of the
@@ -82,19 +82,7 @@
             (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
   do
     -- impl-start
-    -- Nothing was collected: emit nothing.
-    if !hasModules then
-      return []
-    else
-      -- The single combined-document format hosts no separate companion pages.
-      if isCombinedFormat fmt then
-        return []
-      else
-        -- Suppress for the e-book family unless the project opted in.
-        if isEbookFormat fmt && !ebookOptIn then
-          return []
-        else
-          return generated
+    return collectedPages fmt ebookOptIn hasModules generated
     -- impl-end
 
 prove_correct gatedPageEmission by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The gating decision is a closed function of the
--  output-format name and a project option, both modeled DEEPLY: the
--  format-name tests are ordinary equality/prefix checks over the name's
--  characters, and the option is a boolean input. The set of rendered pages the
--  unchanged emission body would produce is carried as an opaque input
--  `generated` — an unchanged concrete tail (tagged I in refinement.md), not a
--  callee with a contract — so nothing is consumed as an axiom. See
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- One rendered output page: a builder-visible artifact identified by its page
   name (the only field the desired behaviour observes — whether such a page is
   emitted at all). -/
structure Page where
  name : List Char
deriving DecidableEq, Inhabited, Repr

/- Whether the active output format is the single combined-document web format:
   the whole build is rendered into one document, which hosts no separate
   companion source pages. Recognised by its exact name. -/
@[grind] def isCombinedFormat (fmt : List Char) : Bool :=
  fmt == "singlehtml".toList

/- Whether the active output format is the portable e-book family. Every member
   of that family shares the same leading name token, so a prefix test
   recognises the whole family (the plain member and its versioned variants). -/
@[grind] def isEbookFormat (fmt : List Char) : Bool :=
  "epub".toList.isPrefixOf fmt

/- Whether rendered source pages must be SUPPRESSED for this build. They are
   suppressed for the single combined-document format always, and for the
   portable e-book family unless the project has explicitly opted in to
   including them in e-book output. For every other format they are kept. -/
@[grind] def shouldSuppress (fmt : List Char) (ebookOptIn : Bool) : Bool :=
  isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn)

/- The pages actually emitted by the collection step. When no source modules
   were collected at all there is nothing to emit; otherwise the pages are
   suppressed for the formats above, and kept (exactly the pages the emission
   body produces) for all others. -/
@[grind] def collectedPages (fmt : List Char) (ebookOptIn hasModules : Bool)
    (generated : List Page) : List Page :=
  if !hasModules then []
  else if shouldSuppress fmt ebookOptIn then []
  else generated
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The collection step that emits one rendered output page per collected source
   module at the end of a build. The desired behaviour: emit nothing when no
   source modules were collected; otherwise SUPPRESS the rendered pages for the
   single combined-document format, and for the portable e-book family unless
   the project opted in to including them in e-book output — and for every
   other output format emit exactly the pages the unchanged emission body
   produces.

   `fmt` (the output-format name), `ebookOptIn` (the project option),
   `hasModules` (whether any source modules were collected) and `generated`
   (the pages the unchanged emission body yields) are all read-only inputs:
   the step only decides whether to emit `generated` or nothing, and mutates
   none of them (directive 5). The suppression set is pinned exactly by
   `shouldSuppress`, and the emitted page list by `collectedPages`. -/
method gatedPageEmission (fmt : List Char) (ebookOptIn : Bool) (hasModules : Bool)
    (generated : List Page) return (out : List Page)
  ensures out = collectedPages fmt ebookOptIn hasModules generated
  ensures shouldSuppress fmt ebookOptIn =
            (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
  do
    -- impl-start
    if !hasModules then
      return []
    else
      if isCombinedFormat fmt then
        return []
      else
        if isEbookFormat fmt && !ebookOptIn then
          return []
        else
          return generated
    -- impl-end

prove_correct gatedPageEmission by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition `out = collectedPages fmt ebookOptIn hasModules generated` fully pins output as a deterministic pure function of the inputs (no preconditions, no oracle underconstraint). Refinement audit: meta.json axioms=[] and deep_model_references=[]; refinement.md §C confirms every leg is R or I — NO A-legs to attack (no consumed axioms, no A-reference deep models). Kind-3 legs: none. Gating decision modeled deeply (List Char equality, List.isPrefixOf, bool negation).

All 9 same_spec checks = True (byte-identical spec region, edited impl only). Verifications run concurrently (batches of 4) via scripts/lean_verify.sh <file>.

Wrong impls, all FAIL verification (exit 1, genuine `unsolved goals` at the postcondition, not timeouts/parse errors):
- atk_prepatch (prepatch bug: drops both inserted guards) → unsolved goals @ line 91
- atk_1_epub_only (partial-domain: drops singlehtml guard) → unsolved goals @94
- atk_2_single_only (partial-domain: drops epub guard) → unsolved goals @94
- atk_3_ignore_optin (drops opt-in condition, suppress all epub) → unsolved goals @97
- atk_4_epub_exacteq (boundary: exact-eq "epub" instead of prefix) → unsolved goals @97
- atk_5_drop_hasmodules (control-flow-effect: drops hasModules guard) → unsolved goals @94
- atk_6_single_prefix (boundary: prefix vs exact-eq for singlehtml) → unsolved goals @97

Positive control (correct nested impl): pos_control.lean VERIFIES (exit 0).

Only verifying same-spec impl: atk_7_oracle_echo (`return collectedPages fmt ebookOptIn hasModules generated`), which is extensionally equal to the oracle = gold behavior. Per mandatory protocol, its faithful refined patch (= gold patch verbatim) was materialized and RUN through the official harness:
  cmd: python -m swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8721', <gold patch>, timeout=1800) [via docker run_evaluation]
  RESULT: resolved=True. FAIL_TO_PASS test_viewcode_epub_default = success; PASS_TO_PASS test_viewcode_epub_enabled/test_linkcode/test_local_source_files all success; no failures.
A gold-equivalent echo whose patch RESOLVES is not a weakness (resolved echo-attack policy). No verify⇏correct break.

Conclusion: every verifying impl is either the correct impl or has a resolving faithful patch; 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle) + prepatch all fail verification. verify⇒correct holds.

Commands used:
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." → all True
- verify: bash scripts/lean_verify.sh <atk>.lean
- resolve: run_resolve for atk_7 faithful patch → resolved=True

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_1_epub_only.lean`, `atk_2_single_only.lean`, `atk_3_ignore_optin.lean`, `atk_4_epub_exacteq.lean`, `atk_5_drop_hasmodules.lean`, `atk_6_single_prefix.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_epub_only.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2_single_only.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_ignore_optin.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_epub_exacteq.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_drop_hasmodules.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_single_prefix.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The gating decision is a closed function of the
--  output-format name and a project option, both modeled DEEPLY: the
--  format-name tests are ordinary equality/prefix checks over the name's
--  characters, and the option is a boolean input. The set of rendered pages the
--  unchanged emission body would produce is carried as an opaque input
--  `generated` — an unchanged concrete tail (tagged I in refinement.md), not a
--  callee with a contract — so nothing is consumed as an axiom. See
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- One rendered output page: a builder-visible artifact identified by its page
   name (the only field the desired behaviour observes — whether such a page is
   emitted at all). -/
structure Page where
  name : List Char
deriving DecidableEq, Inhabited, Repr

/- Whether the active output format is the single combined-document web format:
   the whole build is rendered into one document, which hosts no separate
   companion source pages. Recognised by its exact name. -/
@[grind] def isCombinedFormat (fmt : List Char) : Bool :=
  fmt == "singlehtml".toList

/- Whether the active output format is the portable e-book family. Every member
   of that family shares the same leading name token, so a prefix test
   recognises the whole family (the plain member and its versioned variants). -/
@[grind] def isEbookFormat (fmt : List Char) : Bool :=
  "epub".toList.isPrefixOf fmt

/- Whether rendered source pages must be SUPPRESSED for this build. They are
   suppressed for the single combined-document format always, and for the
   portable e-book family unless the project has explicitly opted in to
   including them in e-book output. For every other format they are kept. -/
@[grind] def shouldSuppress (fmt : List Char) (ebookOptIn : Bool) : Bool :=
  isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn)

/- The pages actually emitted by the collection step. When no source modules
   were collected at all there is nothing to emit; otherwise the pages are
   suppressed for the formats above, and kept (exactly the pages the emission
   body produces) for all others. -/
@[grind] def collectedPages (fmt : List Char) (ebookOptIn hasModules : Bool)
    (generated : List Page) : List Page :=
  if !hasModules then []
  else if shouldSuppress fmt ebookOptIn then []
  else generated
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The collection step that emits one rendered output page per collected source
   module at the end of a build. The desired behaviour: emit nothing when no
   source modules were collected; otherwise SUPPRESS the rendered pages for the
   single combined-document format, and for the portable e-book family unless
   the project opted in to including them in e-book output — and for every
   other output format emit exactly the pages the unchanged emission body
   produces.

   `fmt` (the output-format name), `ebookOptIn` (the project option),
   `hasModules` (whether any source modules were collected) and `generated`
   (the pages the unchanged emission body yields) are all read-only inputs:
   the step only decides whether to emit `generated` or nothing, and mutates
   none of them (directive 5). The suppression set is pinned exactly by
   `shouldSuppress`, and the emitted page list by `collectedPages`. -/
method gatedPageEmission (fmt : List Char) (ebookOptIn : Bool) (hasModules : Bool)
    (generated : List Page) return (out : List Page)
  ensures out = collectedPages fmt ebookOptIn hasModules generated
  ensures shouldSuppress fmt ebookOptIn =
            (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
  do
    -- impl-start
    if !hasModules then
      return []
    else
      if isCombinedFormat fmt then
        return []
      else
        if isEbookFormat fmt && !ebookOptIn then
          return []
        else
          return generated
    -- impl-end

prove_correct gatedPageEmission by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition `out = collectedPages fmt ebookOptIn hasModules generated` fully pins output as a deterministic pure function of the inputs (no preconditions, no oracle underconstraint). Refinement audit: meta.json axioms=[] and deep_model_references=[]; refinement.md §C confirms every leg is R or I — NO A-legs to attack (no consumed axioms, no A-reference deep models). Kind-3 legs: none. Gating decision modeled deeply (List Char equality, List.isPrefixOf, bool negation).

All 9 same_spec checks = True (byte-identical spec region, edited impl only). Verifications run concurrently (batches of 4) via scripts/lean_verify.sh <file>.

Wrong impls, all FAIL verification (exit 1, genuine `unsolved goals` at the postcondition, not timeouts/parse errors):
- atk_prepatch (prepatch bug: drops both inserted guards) → unsolved goals @ line 91
- atk_1_epub_only (partial-domain: drops singlehtml guard) → unsolved goals @94
- atk_2_single_only (partial-domain: drops epub guard) → unsolved goals @94
- atk_3_ignore_optin (drops opt-in condition, suppress all epub) → unsolved goals @97
- atk_4_epub_exacteq (boundary: exact-eq "epub" instead of prefix) → unsolved goals @97
- atk_5_drop_hasmodules (control-flow-effect: drops hasModules guard) → unsolved goals @94
- atk_6_single_prefix (boundary: prefix vs exact-eq for singlehtml) → unsolved goals @97

Positive control (correct nested impl): pos_control.lean VERIFIES (exit 0).

Only verifying same-spec impl: atk_7_oracle_echo (`return collectedPages fmt ebookOptIn hasModules generated`), which is extensionally equal to the oracle = gold behavior. Per mandatory protocol, its faithful refined patch (= gold patch verbatim) was materialized and RUN through the official harness:
  cmd: python -m swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8721', <gold patch>, timeout=1800) [via docker run_evaluation]
  RESULT: resolved=True. FAIL_TO_PASS test_viewcode_epub_default = success; PASS_TO_PASS test_viewcode_epub_enabled/test_linkcode/test_local_source_files all success; no failures.
A gold-equivalent echo whose patch RESOLVES is not a weakness (resolved echo-attack policy). No verify⇏correct break.

Conclusion: every verifying impl is either the correct impl or has a resolving faithful patch; 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle) + prepatch all fail verification. verify⇒correct holds.

Commands used:
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." → all True
- verify: bash scripts/lean_verify.sh <atk>.lean
- resolve: run_resolve for atk_7 faithful patch → resolved=True

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sphinx-doc__sphinx-8721 velvet bundle. Modeled function gatedPageEmission models sphinx.ext.viewcode.collect_pages at base_commit 82ef497a.

SPEC REGION: same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) == True — the frozen spec (axioms/pure/pre/post/impl markers) is byte-identical between the verifying solution and the prepatch skeleton. Only the impl-region body differs (prepatch drops both inserted guards), as required.

LEAN VERIFY: scripts/lean_verify.sh on Solution.lean exits 0 (prove_correct via loom_solve).

FAITHFULNESS (does the model agree with the REAL callee?): The gold patch inserts exactly two early-return guards into collect_pages:
  if app.builder.name == "singlehtml": return
  if app.builder.name.startswith("epub") and not env.config.viewcode_enable_epub: return
plus the pre-existing `if not hasattr(env,'_viewcode_modules'): return`. The spec transliterates these deeply: isCombinedFormat = (fmt == "singlehtml"), isEbookFormat = isPrefixOf "epub" fmt, shouldSuppress = isCombined || (isEbook && !ebookOptIn), collectedPages returns [] when !hasModules or shouldSuppress, else `generated`. This is a faithful 1:1 model of the gating decision; the unchanged emission body is correctly abstracted as the opaque carrier `generated` (only emit-vs-suppress is observable, matching the F2P/P2P tests which assert file existence).

DIFFERENTIAL TEST: Ran the shadow (Lean impl transliterated to Python) against the REAL patched collect_pages (imported patched worktree, status_iterator monkeypatched to detect body-reached) over 200,000 fuzzed (fmt, opt_in, has_modules) inputs including all boundary cases (epub/epub3/singlehtml/EPUB/Epub/epu/epubx/singlehtml2/single/empty/random tokens). Result: total 200000, mismatches 0. The conformance_check.py in-bundle (seed 8721, 1e5 inputs) is well-constructed and does the same. Case-sensitivity (Python str.startswith / == is case-sensitive) is faithfully matched by List.isPrefixOf / List Char equality — 'EPUB'/'Epub' correctly emit.

RELAXED LEAKAGE: combined-document (singlehtml) guard is not in the public problem_statement, so pinning it is disclosed as relaxed leakage (meta relaxed_leakage=true, G-LEAK=relaxed). This is a faithfulness REQUIREMENT, not a defect: an epub-only spec would be provably UNFAITHFUL at fmt='singlehtml' (real patched code returns early / emits nothing while an epub-only model would emit `generated`). The bundle correctly models both guards.

No diverging input found. The spec neither over-constrains nor drifts from the real repo behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-verified the accepted relaxed-leakage disposition (did not rubber-stamp). (1) same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers with VelvetBackend; spec regions byte-identical and the impl region is properly elided in the spec view. (2) Core soundness holds: lean_verify.sh on Solution.lean exits 0; recorded G-EQ/G-PANEL-1/G-PANEL-2/G-CONF/G-DIFF all pass; prepatch (only hasModules guard) fails out=collectedPages on the suppressing clauses. (3) problem_statement token scan (re-run, case-insensitive): epub=8, viewcode_enable_epub=2 (PUBLIC); singlehtml=0, single=0, combined=0, startswith=0 (NON-PUBLIC). hints_text is empty. (4) The spec view DOES leak the combined-document (singlehtml) facet beyond problem_statement: isCombinedFormat fmt = (fmt == "singlehtml".toList), its disjunct in shouldSuppress, the collectedPages clause, and the second ensures folding isCombinedFormat into the suppression predicate. This is EXACTLY the facet the disposition covers. (5) Unavoidability re-derived and confirmed: fmt is a free input; the gold patch returns early at fmt="singlehtml", so any faithful spec of the patched collect_pages must pin that clause (omitting => model emits `generated` while real patch emits nothing = concrete divergence), and any require-based domain restriction must itself name the singlehtml discriminator, which is derivable from no public vocabulary. Faithful + non-leaking is impossible => genuine problem_statement<->gold mismatch. (6) Disposition is well-formed: relaxed_leakage=true, gates.G-LEAK.status=relaxed, RELAXED_LEAKAGE.md present. The epub clause (isEbookFormat/ebookOptIn) is fully public and not a leak. No NEW leaking line beyond the dispositioned combined-document facet was found, and the disposition is not broken. Per _audit.py convention, a properly-dispositioned relaxed-leakage panel records as pass/NO-LEAKAGE with this note.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.

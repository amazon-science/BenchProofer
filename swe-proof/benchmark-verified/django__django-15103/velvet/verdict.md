# P2 adversarial audit — django__django-15103

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies against the frozen spec, so there is no verifying-but-wrong candidate whose faithful refined patch could be materialized and resolve-tested. verify=>correct holds for this bundle.
```

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
 -- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
@@ -62,10 +62,7 @@
   ensures identifier ≠ []  → out = wrapWithId identifier content
   do
     -- impl-start
-    if identifier = [] then
-      return wrapNoId content
-    else
-      return wrapWithId identifier content
+    return wrapWithId identifier content
     -- impl-end
 
 prove_correct jsonScriptTag by
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
 -- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
@@ -63,9 +63,9 @@
   do
     -- impl-start
     if identifier = [] then
+      return wrapWithId identifier content
+    else
       return wrapNoId content
-    else
-      return wrapWithId identifier content
     -- impl-end
 
 prove_correct jsonScriptTag by
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
 -- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
@@ -62,10 +62,7 @@
   ensures identifier ≠ []  → out = wrapWithId identifier content
   do
     -- impl-start
-    if identifier = [] then
-      return wrapNoId content
-    else
-      return wrapWithId identifier content
+    return wrapNoId content
     -- impl-end
 
 prove_correct jsonScriptTag by
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
 -- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
@@ -62,10 +62,7 @@
   ensures identifier ≠ []  → out = wrapWithId identifier content
   do
     -- impl-start
-    if identifier = [] then
-      return wrapNoId content
-    else
-      return wrapWithId identifier content
+    return content
     -- impl-end
 
 prove_correct jsonScriptTag by
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
 -- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
@@ -62,10 +62,7 @@
   ensures identifier ≠ []  → out = wrapWithId identifier content
   do
     -- impl-start
-    if identifier = [] then
-      return wrapNoId content
-    else
-      return wrapWithId identifier content
+    return []
     -- impl-end
 
 prove_correct jsonScriptTag by
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
 -- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
@@ -63,7 +63,7 @@
   do
     -- impl-start
     if identifier = [] then
-      return wrapNoId content
+      return wrapNoId content ++ ['!']
     else
       return wrapWithId identifier content
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
 -- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
@@ -62,8 +62,8 @@
   ensures identifier ≠ []  → out = wrapWithId identifier content
   do
     -- impl-start
-    if identifier = [] then
-      return wrapNoId content
+    if identifier ≠ [] then
+      return wrapWithId identifier content
     else
       return wrapWithId identifier content
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
 -- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
@@ -65,7 +65,7 @@
     if identifier = [] then
       return wrapNoId content
     else
-      return wrapWithId identifier content
+      return openWithId [] ++ content ++ scriptClose
     -- impl-end
 
 prove_correct jsonScriptTag by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
--  the identifier are unchanged operations, taken as plain inputs: `content` is
--  the already-encoded, already-safe payload text and `identifier` is the
--  already-escaped identifier text. The operation under specification only
--  decides the surrounding markup, so neither input is produced here.)
-- axioms-end

-- pure-start
/- The constant markup fragments of the wrapper. The payload is placed inside a
   `<script type="application/json"> … </script>` element. An identifier, when
   present, is carried by an extra `id="…"` attribute. -/
def scriptClose : List Char := "</script>".toList

/- The opening tag WITHOUT an identifier attribute. -/
def openPlain : List Char := "<script type=\"application/json\">".toList

/- The opening tag WITH the identifier attribute carrying `identifier`. -/
def openWithId (identifier : List Char) : List Char :=
  "<script id=\"".toList ++ identifier ++ "\" type=\"application/json\">".toList

/- The element produced when no identifier is supplied: the payload wrapped in a
   bare script element, with no `id` attribute at all. -/
def wrapNoId (content : List Char) : List Char :=
  openPlain ++ content ++ scriptClose

/- The element produced when an identifier is supplied: the payload wrapped in a
   script element carrying that identifier in an `id` attribute. -/
def wrapWithId (identifier content : List Char) : List Char :=
  openWithId identifier ++ content ++ scriptClose
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Wrap an encoded payload in a `<script type="application/json">` element.

   The element may optionally carry an identifier. The identifier is optional:
   supplying an empty identifier means "no identifier", in which case the result
   is the bare element with NO `id` attribute. When a non-empty identifier is
   supplied, the result additionally carries that identifier in an `id`
   attribute.

   `identifier` and `content` are read-only inputs (neither is `mut`): the
   routine derives the markup and alters nothing (directive 5). Both the
   identifier and the encoded payload are modeled as per-code-point strings
   (`List Char`); the empty identifier `[]` is the "no identifier" case
   (mapping.md §2). -/
method jsonScriptTag (identifier : List Char) (content : List Char) return (out : List Char)
  ensures identifier = []  → out = wrapNoId content
  ensures identifier ≠ []  → out = wrapWithId identifier content
  do
    -- impl-start
    if identifier = [] then
      return wrapNoId content
    else
      return wrapWithId identifier content
    -- impl-end

prove_correct jsonScriptTag by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL/ENV: real project root =.

SAME_SPEC: all 8 attacks + pc_correct give same_spec=True vs velvet Solution.lean (only the impl region varies; spec_view byte-identical). Checked via swebench_unified.markers.same_spec with get_backend('velvet').language. NOTE: a first-pass generation double-indented the '-- impl-start' marker line, which perturbed the impl-region span and flipped same_spec to False; regenerated with the 4-space-indented markers matched exactly, then all True. (Confirmed by inspecting _lean_parse_regions.)

VERIFY commands (run concurrently, batches of 4): bash scripts/lean_verify.sh <file>. Results:
- pc_correct.lean (= exact gold Solution impl, correct positive control): EXIT=0 verifies -> spec non-vacuous/satisfiable.
- atk_1 always wrapWithId (prepatch bug re-encode): EXIT=1, 'unsolved goals' @68:28 (rejected by ensures identifier=[] clause: emits <script id="" ...>).
- atk_2 branches swapped (control-flow-effect): EXIT=1, unsolved goals (rejected by BOTH clauses).
- atk_3 always wrapNoId, never emit id (drops id even when present): EXIT=1, unsolved goals @68:28 (rejected by ensures identifier!=[] clause).
- atk_4 return content, ungrounded-oracle echo: EXIT=1, unsolved goals @68:28 (opaque input cannot discharge constructed-markup postcondition).
- atk_5 return [] empty output: EXIT=1, unsolved goals (rejected by both clauses).
- atk_6 wrapNoId content ++ ['!'] boundary/off-by-one on empty branch: EXIT=1, unsolved goals.
- atk_7 partial-domain: explicit if identifier!=[] both branches return wrapWithId (empty case wrong): EXIT=1, unsolved goals.
- atk_8 control-flow-effect: empty branch correct (wrapNoId) but non-empty branch splices openWithId [] instead of identifier (id=""): EXIT=1, unsolved goals @71:28.
Every rejection is a genuine prove_correct 'unsolved goals' failure, not a syntax/parse error.

PREPATCH: Solution_prepatch.lean copied to prepatch.lean; same_spec=True; EXIT=1 with unsolved goals @73:28 -> fails precisely on the discriminating empty-identifier clause (always emits wrapWithId => <script id="" ...>). G-DIFF sound.

RESOLVE STEP: NOT applicable/none run. The protocol requires materializing + running a faithful refined patch through run_resolve ONLY for wrong impls that VERIFY. Zero wrong impls verified, so 'patches' is empty and no resolve run was needed to reach a verdict. This is not INCONCLUSIVE: the falsification attempt was fully executed (9 same-spec candidates verified end-to-end) and none broke the spec.

WHY THE SPEC IS TIGHT (verify=>correct): the spec is a complete output equality. Two TOTAL ensures clauses partition the entire input domain -- 'identifier = [] -> out = wrapNoId content' and 'identifier != [] -> out = wrapWithId identifier content' -- with no requires narrowing the domain, pinning out exactly to concatenations of the gold format-string literals verbatim (openPlain/openWithId/scriptClose/wrapNoId/wrapWithId encode <script type="application/json">, <script id="..." ...>, </script>). Zero slack: any impl that verifies must reproduce gold behavior on both branches.

REFINEMENT AUDIT (refinement.md): every leg is R or I; NO A-legs and NO deep-model references exist in this bundle (G-AX=skip is correct). A1/A2 = R (json.dumps+translate encoder and conditional_escape are UNCHANGED by the patch, abstracted as opaque List Char inputs content/identifier). A6 = R (mark_safe/SafeString identity on char content). A3/A4/A5 = I (the genuinely-changed op -- whether to emit the id attribute -- is modeled DIRECTLY as the branch on identifier=[], not hidden; format_html template interpolation <=> fragment concatenation). No kind-3 step. The one subtle correspondence is the truthiness bridge 'if element_id:' <=> 'identifier != []' (falsy None/'' <=> Lean []), which is faithful for string identifiers and exercised by G-CONF (falsy None,'' and truthy random ids). patch.diff is the gold patch verbatim (both html.py markup hunk and defaultfilters.py signature-default wrapper, the latter R-only no observable behavior).

VERDICT: SOUND. >=5 distinct attack classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch-bug, always-noId, empty) plus prepatch all executed and verified; none produced a verifying wrong impl; positive control verifies. verify=>correct holds; spec is not broken.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies against the frozen spec, so there is no verifying-but-wrong candidate whose faithful refined patch could be materialized and resolve-tested. verify=>correct holds for this bundle.
```

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
--  the identifier are unchanged operations, taken as plain inputs: `content` is
--  the already-encoded, already-safe payload text and `identifier` is the
--  already-escaped identifier text. The operation under specification only
--  decides the surrounding markup, so neither input is produced here.)
-- axioms-end

-- pure-start
/- The constant markup fragments of the wrapper. The payload is placed inside a
   `<script type="application/json"> … </script>` element. An identifier, when
   present, is carried by an extra `id="…"` attribute. -/
def scriptClose : List Char := "</script>".toList

/- The opening tag WITHOUT an identifier attribute. -/
def openPlain : List Char := "<script type=\"application/json\">".toList

/- The opening tag WITH the identifier attribute carrying `identifier`. -/
def openWithId (identifier : List Char) : List Char :=
  "<script id=\"".toList ++ identifier ++ "\" type=\"application/json\">".toList

/- The element produced when no identifier is supplied: the payload wrapped in a
   bare script element, with no `id` attribute at all. -/
def wrapNoId (content : List Char) : List Char :=
  openPlain ++ content ++ scriptClose

/- The element produced when an identifier is supplied: the payload wrapped in a
   script element carrying that identifier in an `id` attribute. -/
def wrapWithId (identifier content : List Char) : List Char :=
  openWithId identifier ++ content ++ scriptClose
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Wrap an encoded payload in a `<script type="application/json">` element.

   The element may optionally carry an identifier. The identifier is optional:
   supplying an empty identifier means "no identifier", in which case the result
   is the bare element with NO `id` attribute. When a non-empty identifier is
   supplied, the result additionally carries that identifier in an `id`
   attribute.

   `identifier` and `content` are read-only inputs (neither is `mut`): the
   routine derives the markup and alters nothing (directive 5). Both the
   identifier and the encoded payload are modeled as per-code-point strings
   (`List Char`); the empty identifier `[]` is the "no identifier" case
   (mapping.md §2). -/
method jsonScriptTag (identifier : List Char) (content : List Char) return (out : List Char)
  ensures identifier = []  → out = wrapNoId content
  ensures identifier ≠ []  → out = wrapWithId identifier content
  do
    -- impl-start
    if identifier = [] then
      return wrapNoId content
    else
      return wrapWithId identifier content
    -- impl-end

prove_correct jsonScriptTag by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL/ENV: real project root =.

SAME_SPEC: all 8 attacks + pc_correct give same_spec=True vs velvet Solution.lean (only the impl region varies; spec_view byte-identical). Checked via swebench_unified.markers.same_spec with get_backend('velvet').language. NOTE: a first-pass generation double-indented the '-- impl-start' marker line, which perturbed the impl-region span and flipped same_spec to False; regenerated with the 4-space-indented markers matched exactly, then all True. (Confirmed by inspecting _lean_parse_regions.)

VERIFY commands (run concurrently, batches of 4): bash scripts/lean_verify.sh <file>. Results:
- pc_correct.lean (= exact gold Solution impl, correct positive control): EXIT=0 verifies -> spec non-vacuous/satisfiable.
- atk_1 always wrapWithId (prepatch bug re-encode): EXIT=1, 'unsolved goals' @68:28 (rejected by ensures identifier=[] clause: emits <script id="" ...>).
- atk_2 branches swapped (control-flow-effect): EXIT=1, unsolved goals (rejected by BOTH clauses).
- atk_3 always wrapNoId, never emit id (drops id even when present): EXIT=1, unsolved goals @68:28 (rejected by ensures identifier!=[] clause).
- atk_4 return content, ungrounded-oracle echo: EXIT=1, unsolved goals @68:28 (opaque input cannot discharge constructed-markup postcondition).
- atk_5 return [] empty output: EXIT=1, unsolved goals (rejected by both clauses).
- atk_6 wrapNoId content ++ ['!'] boundary/off-by-one on empty branch: EXIT=1, unsolved goals.
- atk_7 partial-domain: explicit if identifier!=[] both branches return wrapWithId (empty case wrong): EXIT=1, unsolved goals.
- atk_8 control-flow-effect: empty branch correct (wrapNoId) but non-empty branch splices openWithId [] instead of identifier (id=""): EXIT=1, unsolved goals @71:28.
Every rejection is a genuine prove_correct 'unsolved goals' failure, not a syntax/parse error.

PREPATCH: Solution_prepatch.lean copied to prepatch.lean; same_spec=True; EXIT=1 with unsolved goals @73:28 -> fails precisely on the discriminating empty-identifier clause (always emits wrapWithId => <script id="" ...>). G-DIFF sound.

RESOLVE STEP: NOT applicable/none run. The protocol requires materializing + running a faithful refined patch through run_resolve ONLY for wrong impls that VERIFY. Zero wrong impls verified, so 'patches' is empty and no resolve run was needed to reach a verdict. This is not INCONCLUSIVE: the falsification attempt was fully executed (9 same-spec candidates verified end-to-end) and none broke the spec.

WHY THE SPEC IS TIGHT (verify=>correct): the spec is a complete output equality. Two TOTAL ensures clauses partition the entire input domain -- 'identifier = [] -> out = wrapNoId content' and 'identifier != [] -> out = wrapWithId identifier content' -- with no requires narrowing the domain, pinning out exactly to concatenations of the gold format-string literals verbatim (openPlain/openWithId/scriptClose/wrapNoId/wrapWithId encode <script type="application/json">, <script id="..." ...>, </script>). Zero slack: any impl that verifies must reproduce gold behavior on both branches.

REFINEMENT AUDIT (refinement.md): every leg is R or I; NO A-legs and NO deep-model references exist in this bundle (G-AX=skip is correct). A1/A2 = R (json.dumps+translate encoder and conditional_escape are UNCHANGED by the patch, abstracted as opaque List Char inputs content/identifier). A6 = R (mark_safe/SafeString identity on char content). A3/A4/A5 = I (the genuinely-changed op -- whether to emit the id attribute -- is modeled DIRECTLY as the branch on identifier=[], not hidden; format_html template interpolation <=> fragment concatenation). No kind-3 step. The one subtle correspondence is the truthiness bridge 'if element_id:' <=> 'identifier != []' (falsy None/'' <=> Lean []), which is faithful for string identifiers and exercised by G-CONF (falsy None,'' and truthy random ids). patch.diff is the gold patch verbatim (both html.py markup hunk and defaultfilters.py signature-default wrapper, the latter R-only no observable behavior).

VERDICT: SOUND. >=5 distinct attack classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch-bug, always-noId, empty) plus prepatch all executed and verified; none produced a verifying wrong impl; positive control verifies. verify=>correct holds; spec is not broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (drift) check for django__django-15103 velvet bundle. (1) same_spec=True under VelvetBackend.language: the spec region (axioms/pure helpers scriptClose/openPlain/openWithId/wrapNoId/wrapWithId, empty pre/post, method signature, and both ensures clauses) is signature-identical between Solution.lean and Solution_prepatch.lean. Modeled function vs real callee: transliterated wrapNoId/wrapWithId + the ensures branch selection to Python and compared to the real patched django.utils.html.json_script at base_commit dd528cb2ce (gold patch applied). Matched on every tested input — falsy element_id (None, ''), truthy string ids, non-string truthy ids (True, 5), whitespace ids, ids/content containing <>&" and </script>, unicode, empty dict/list payloads, and assorted JSON values. No diverging input found. (3) Non-vacuity: Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean (always emits id="") fails exactly the `identifier=[] -> out=wrapNoId content` goal, so the spec genuinely constrains the discriminating change (omit id attribute when identifier absent). (4) The truthiness bridge (Python `if element_id:` <=> Lean identifier != []) and R-abstraction of the unchanged JSON encoder / conditional_escape are documented modeling boundaries verified by G-CONF, not spec drift — the modeled function captures only the template-selection logic, which is the changed code, and agrees with the real function on the abstracted (post-escape) input domain. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified on-host: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True, so the spec region (postconditions/pure fragments/docstring) is byte-identical between gold and prepatch bundles -- it is the frozen spec, not gold-derived. spec_view renders with impl body -> 'implementation elided' and prove_correct body -> 'proof elided'.

Spec view exposes only: (1) postconditions `identifier = [] -> out = wrapNoId content` and `identifier != [] -> out = wrapWithId identifier content`; (2) pure markup fragments openPlain (`<script type="application/json">`), openWithId (`<script id="..." type="application/json">`), scriptClose, and their concatenations; (3) a docstring restating 'the identifier is optional; empty -> bare element with NO id attribute'.

Leakage vs PUBLIC problem_statement (hints_text empty): the statement explicitly requests 'Make the element_id argument of json_script optional' and says there's no reason for the id to be required. The sole behavioral degree of freedom the gold patch introduces -- emit the bare `<script type="application/json">` (no id) when the identifier is absent, vs. the pre-existing id-bearing `<script id="..." ...>` when present -- is EXACTLY the publicly-requested behavior. Formalizing publicly-requested behavior as a postcondition is a specification, not gold reconstruction. The id-bearing markup (openWithId) is the pre-existing public repo code at base_commit (Solution_prepatch.lean emits it unconditionally), so it is not patch-derived; the no-id variant is the trivial 'drop the id attribute' consequence the statement calls out.

The spec view contains NO diff text, NO F2P/PASS_TO_PASS test names, NO hints_text, and NO implementation strategy beyond the publicly-requested behavior (impl and proof both elided). Test-name references (test_json_script_without_id, test_without_id) appear only in the auditor docs refinement.md/mapping.md, which are NOT part of the consumer spec view. No spec-view line hands the solver anything beyond problem_statement.

(Out of scope for leakage: the G-PANEL-2 truthiness-bridge concern -- mapping falsy-non-empty escaped element_ids to identifier != [] -- is a faithfulness matter, not leakage, and does not change the NO-LEAKAGE verdict.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — sphinx-doc__sphinx-10673

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,13 +68,10 @@
   let mut entries : List (Option String × String) := []
   for entry in requested do
     if entry == "" then
-      -- a blank line carries no reference and is ignored
       pure ()
-    else if (existingDocs ++ generatedPages).contains entry then
+    else if existingDocs.contains entry then
       entries := entries ++ [((none : Option String), entry)]
     else
-      -- a reference to no existing document and no special reference page:
-      -- rejected, contributing no entry
       pure ()
   return entries
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,13 +68,10 @@
   let mut entries : List (Option String × String) := []
   for entry in requested do
     if entry == "" then
-      -- a blank line carries no reference and is ignored
       pure ()
-    else if (existingDocs ++ generatedPages).contains entry then
+    else if generatedPages.contains entry then
       entries := entries ++ [((none : Option String), entry)]
     else
-      -- a reference to no existing document and no special reference page:
-      -- rejected, contributing no entry
       pure ()
   return entries
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,15 +67,10 @@
     List (Option String × String) := Id.run do
   let mut entries : List (Option String × String) := []
   for entry in requested do
-    if entry == "" then
-      -- a blank line carries no reference and is ignored
-      pure ()
-    else if (existingDocs ++ generatedPages).contains entry then
+    if (existingDocs ++ generatedPages).contains entry then
       entries := entries ++ [((none : Option String), entry)]
     else
-      -- a reference to no existing document and no special reference page:
-      -- rejected, contributing no entry
-      pure ()
+      entries := entries ++ [((none : Option String), entry)]
   return entries
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,13 +68,10 @@
   let mut entries : List (Option String × String) := []
   for entry in requested do
     if entry == "" then
-      -- a blank line carries no reference and is ignored
       pure ()
     else if (existingDocs ++ generatedPages).contains entry then
-      entries := entries ++ [((none : Option String), entry)]
+      entries := [((none : Option String), entry)] ++ entries
     else
-      -- a reference to no existing document and no special reference page:
-      -- rejected, contributing no entry
       pure ()
   return entries
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,13 +68,10 @@
   let mut entries : List (Option String × String) := []
   for entry in requested do
     if entry == "" then
-      -- a blank line carries no reference and is ignored
       pure ()
     else if (existingDocs ++ generatedPages).contains entry then
-      entries := entries ++ [((none : Option String), entry)]
+      entries := entries ++ [((some entry : Option String), entry)]
     else
-      -- a reference to no existing document and no special reference page:
-      -- rejected, contributing no entry
       pure ()
   return entries
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,13 +68,10 @@
   let mut entries : List (Option String × String) := []
   for entry in requested do
     if entry == "" then
-      -- a blank line carries no reference and is ignored
       pure ()
     else if (existingDocs ++ generatedPages).contains entry then
-      entries := entries ++ [((none : Option String), entry)]
+      entries := entries ++ [((none : Option String), entry), ((none : Option String), entry)]
     else
-      -- a reference to no existing document and no special reference page:
-      -- rejected, contributing no entry
       pure ()
   return entries
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,13 +68,10 @@
   let mut entries : List (Option String × String) := []
   for entry in requested do
     if entry == "" then
-      -- a blank line carries no reference and is ignored
       pure ()
-    else if (existingDocs ++ generatedPages).contains entry then
+    else if existingDocs.contains entry && generatedPages.contains entry then
       entries := entries ++ [((none : Option String), entry)]
     else
-      -- a reference to no existing document and no special reference page:
-      -- rejected, contributing no entry
       pure ()
   return entries
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the accepted entries of a table-of-contents directive.

A table-of-contents directive lists, one per line, references to other documents
that should appear in the tree. When the directive is processed, each listed
reference is examined and either accepted as an entry of the tree or rejected.

A reference is accepted when it names a document that the project actually
contains. In addition to the ordinary source documents, a documentation build
always provides a small constant set of *special reference pages* — the general
index, the module index, and the search page — which exist even though they have
no source file of their own. A reference to one of these special pages is just
as valid a target as a reference to an ordinary document, so it too is accepted.

Blank lines carry no reference and are ignored. Every other reference — one that
names neither an existing document nor one of the special reference pages — is
rejected and contributes no entry.

The accepted entries are kept in the order in which they are listed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each decision
-- the collection makes is over directly-supplied observations: the list of
-- listed references, the names of the documents that exist, and the names of the
-- special reference pages the build always provides. Whether a reference is
-- accepted is a blankness test plus a membership test against the union of those
-- two name collections — both spelled out directly in the implementation — so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (No standalone functional helpers are needed: the accepted-entry relation is
-- stated directly as a `filter`/`map` over the listed references.)
-- pure-end

-- post-conditions-start
/-- The entries accepted from a table-of-contents directive body.

`requested` is the list of references listed in the directive (one per line),
`existingDocs` the names of the documents the project contains, and
`generatedPages` the names of the special reference pages the build always
provides (the general index, the module index, and the search page).

The result is the list of `(title, target)` pairs accepted as tree entries: a
reference contributes an entry exactly when it is non-blank AND names either an
existing document or one of the special reference pages, and the accepted entries
appear in their original order, each with no explicit title (`none`) and its own
name as the target. (Directive 5 frame: the full entry list is pinned as a
function of the inputs — nothing is left unconstrained; Directive 8: the result
is grounded entirely in `requested`/`existingDocs`/`generatedPages`.) -/
def problem_spec_tocEntries
    (requested existingDocs generatedPages : List String)
    (result : List (Option String × String)) : Prop :=
  result =
    (requested.filter
      (fun e => e != "" && (existingDocs ++ generatedPages).contains e)).map
      (fun e => ((none : Option String), e))
-- post-conditions-end

-- impl-start
def implementation_tocEntries
    (requested existingDocs generatedPages : List String) :
    List (Option String × String) := Id.run do
  let mut entries : List (Option String × String) := []
  for entry in requested do
    if entry == "" then
      -- a blank line carries no reference and is ignored
      pure ()
    else if (existingDocs ++ generatedPages).contains entry then
      entries := entries ++ [((none : Option String), entry)]
    else
      -- a reference to no existing document and no special reference page:
      -- rejected, contributing no entry
      pure ()
  return entries
-- impl-end


-- proof-start
theorem correct_tocEntries :
    ∀ (requested existingDocs generatedPages : List String),
      problem_spec_tocEntries requested existingDocs generatedPages
        (implementation_tocEntries requested existingDocs generatedPages) := by
  intro requested existingDocs generatedPages
  unfold problem_spec_tocEntries implementation_tocEntries
  simp only [Id.run, bind_pure_comp, map_pure]
  have key : ∀ (rs : List String) (acc : List (Option String × String)),
      (forIn (m := Id) rs acc (fun entry entries =>
        if entry == "" then pure (ForInStep.yield entries)
        else if (existingDocs ++ generatedPages).contains entry then
          pure (ForInStep.yield (entries ++ [((none : Option String), entry)]))
        else pure (ForInStep.yield entries))) =
      acc ++ (rs.filter (fun e => e != "" && (existingDocs ++ generatedPages).contains e)).map
        (fun e => ((none : Option String), e)) := by
    intro rs
    induction rs with
    | nil => intro acc; simp only [List.forIn_nil, List.filter_nil, List.map_nil,
        List.append_nil]; rfl
    | cons r rs ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [List.filter_cons]
      by_cases h1 : (r == "") = true
      · have hne : (r != "") = false := by simp [bne, h1]
        simp only [h1, if_true, hne, Bool.false_and, Bool.false_eq_true, if_false]
        show (forIn (m := Id) rs acc _) = _
        rw [ih]
      · have hne : (r != "") = true := by simp [bne, h1]
        by_cases h2 : ((existingDocs ++ generatedPages).contains r) = true
        · simp only [h1, if_false, h2, if_true, hne, Bool.and_self, List.map_cons]
          show (forIn (m := Id) rs (acc ++ [((none:Option String), r)]) _) = _
          rw [ih]; simp [List.append_assoc]
        · simp only [h1, if_false, h2, hne, Bool.and_false, Bool.false_eq_true, if_false]
          show (forIn (m := Id) rs acc _) = _
          rw [ih]
  rw [key]
  simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec is OUTPUT-PINNING: problem_spec_tocEntries fixes `result` to a single closed expression `(requested.filter (fun e => e != "" && (existingDocs ++ generatedPages).contains e)).map (fun e => (none, e))`. Any verifying impl is therefore forced extensionally equal to the gold function; no behaviorally-distinct impl can close correct_tocEntries under any proof.

Same-spec check: same_spec=True for all 7 attacks (swebench_unified.markers.same_spec, lean backend) — impl region edited only, axioms/pure/pre/post byte-identical.

Verification (cmd per file: `bash scripts/lean_verify.sh <path>`, run <=4 concurrently as background jobs):
- pc_gold.lean (gold positive control): exit 0; `#print axioms correct_tocEntries` => [propext, Quot.sound] (clean, no sorryAx/native/user axioms).
- atk_1.lean PREPATCH BUG existingDocs-only (drops generatedPages): exit 1 (proof key-lemma step fails to reduce). Reproduces the recorded prepatch failure.
- atk_2.lean partial-domain generatedPages-only: exit 1.
- atk_3.lean control-flow accept-all (no blank skip, no reject arm): exit 1.
- atk_4.lean control-flow-effect reversed order (prepend): exit 1, rewrite pattern mismatch at :117.
- atk_5.lean boundary wrong title (some entry, entry): exit 1.
- atk_6.lean cardinality duplicate append: exit 1.
- atk_7.lean ungrounded-oracle echo intersection (existingDocs && generatedPages): exit 1.

All 7 same-spec wrong impls FAIL verification (exit 1). NONE reaches a closing clean-axiom proof, so there is no faithful patch to materialize or run_resolve — verify=>correct cannot be falsified. patches={} accordingly.

A-leg / correspondence audit: refinement.md declares NO A-legs — 9 legs, all R/I, no kind-3. axiom_check.py is a skip stub consistent with the model: grep of Solution.lean finds no `axiom`/`opaque`/`sorry` (only a comment mentioning them), and #print axioms is clean. Model<->patch correspondence holds: union membership `found_docs | generated_docnames` (patch other.py:122) <-> `(existingDocs ++ generatedPages).contains entry`; `if not entry: continue` <-> blank skip; accepted append `(title=None, docname)` <-> `(none, entry)` in source order. conformance_check.py's shadow (existingDocs++generatedPages membership) matches the post-patch oracle. Downstream patched sites (adapters/collectors) are unchanged-by-default consumers of the same generated-docname set, not independently F2P-observable — single-triple modeling is faithful.

SOUND: prepatch reproduced, 7 distinct attacks run, positive control verifies with clean axioms, none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the accepted entries of a table-of-contents directive.

A table-of-contents directive lists, one per line, references to other documents
that should appear in the tree. When the directive is processed, each listed
reference is examined and either accepted as an entry of the tree or rejected.

A reference is accepted when it names a document that the project actually
contains. In addition to the ordinary source documents, a documentation build
always provides a small constant set of *special reference pages* — the general
index, the module index, and the search page — which exist even though they have
no source file of their own. A reference to one of these special pages is just
as valid a target as a reference to an ordinary document, so it too is accepted.

Blank lines carry no reference and are ignored. Every other reference — one that
names neither an existing document nor one of the special reference pages — is
rejected and contributes no entry.

The accepted entries are kept in the order in which they are listed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each decision
-- the collection makes is over directly-supplied observations: the list of
-- listed references, the names of the documents that exist, and the names of the
-- special reference pages the build always provides. Whether a reference is
-- accepted is a blankness test plus a membership test against the union of those
-- two name collections — both spelled out directly in the implementation — so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (No standalone functional helpers are needed: the accepted-entry relation is
-- stated directly as a `filter`/`map` over the listed references.)
-- pure-end

-- post-conditions-start
/-- The entries accepted from a table-of-contents directive body.

`requested` is the list of references listed in the directive (one per line),
`existingDocs` the names of the documents the project contains, and
`generatedPages` the names of the special reference pages the build always
provides (the general index, the module index, and the search page).

The result is the list of `(title, target)` pairs accepted as tree entries: a
reference contributes an entry exactly when it is non-blank AND names either an
existing document or one of the special reference pages, and the accepted entries
appear in their original order, each with no explicit title (`none`) and its own
name as the target. (Directive 5 frame: the full entry list is pinned as a
function of the inputs — nothing is left unconstrained; Directive 8: the result
is grounded entirely in `requested`/`existingDocs`/`generatedPages`.) -/
def problem_spec_tocEntries
    (requested existingDocs generatedPages : List String)
    (result : List (Option String × String)) : Prop :=
  result =
    (requested.filter
      (fun e => e != "" && (existingDocs ++ generatedPages).contains e)).map
      (fun e => ((none : Option String), e))
-- post-conditions-end

-- impl-start
def implementation_tocEntries
    (requested existingDocs generatedPages : List String) :
    List (Option String × String) := Id.run do
  let mut entries : List (Option String × String) := []
  for entry in requested do
    if entry == "" then
      -- a blank line carries no reference and is ignored
      pure ()
    else if (existingDocs ++ generatedPages).contains entry then
      entries := entries ++ [((none : Option String), entry)]
    else
      -- a reference to no existing document and no special reference page:
      -- rejected, contributing no entry
      pure ()
  return entries
-- impl-end


-- proof-start
theorem correct_tocEntries :
    ∀ (requested existingDocs generatedPages : List String),
      problem_spec_tocEntries requested existingDocs generatedPages
        (implementation_tocEntries requested existingDocs generatedPages) := by
  intro requested existingDocs generatedPages
  unfold problem_spec_tocEntries implementation_tocEntries
  simp only [Id.run, bind_pure_comp, map_pure]
  have key : ∀ (rs : List String) (acc : List (Option String × String)),
      (forIn (m := Id) rs acc (fun entry entries =>
        if entry == "" then pure (ForInStep.yield entries)
        else if (existingDocs ++ generatedPages).contains entry then
          pure (ForInStep.yield (entries ++ [((none : Option String), entry)]))
        else pure (ForInStep.yield entries))) =
      acc ++ (rs.filter (fun e => e != "" && (existingDocs ++ generatedPages).contains e)).map
        (fun e => ((none : Option String), e)) := by
    intro rs
    induction rs with
    | nil => intro acc; simp only [List.forIn_nil, List.filter_nil, List.map_nil,
        List.append_nil]; rfl
    | cons r rs ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [List.filter_cons]
      by_cases h1 : (r == "") = true
      · have hne : (r != "") = false := by simp [bne, h1]
        simp only [h1, if_true, hne, Bool.false_and, Bool.false_eq_true, if_false]
        show (forIn (m := Id) rs acc _) = _
        rw [ih]
      · have hne : (r != "") = true := by simp [bne, h1]
        by_cases h2 : ((existingDocs ++ generatedPages).contains r) = true
        · simp only [h1, if_false, h2, if_true, hne, Bool.and_self, List.map_cons]
          show (forIn (m := Id) rs (acc ++ [((none:Option String), r)]) _) = _
          rw [ih]; simp [List.append_assoc]
        · simp only [h1, if_false, h2, hne, Bool.and_false, Bool.false_eq_true, if_false]
          show (forIn (m := Id) rs acc _) = _
          rw [ih]
  rw [key]
  simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec is OUTPUT-PINNING: problem_spec_tocEntries fixes `result` to a single closed expression `(requested.filter (fun e => e != "" && (existingDocs ++ generatedPages).contains e)).map (fun e => (none, e))`. Any verifying impl is therefore forced extensionally equal to the gold function; no behaviorally-distinct impl can close correct_tocEntries under any proof.

Same-spec check: same_spec=True for all 7 attacks (swebench_unified.markers.same_spec, lean backend) — impl region edited only, axioms/pure/pre/post byte-identical.

Verification (cmd per file: `bash scripts/lean_verify.sh <path>`, run <=4 concurrently as background jobs):
- pc_gold.lean (gold positive control): exit 0; `#print axioms correct_tocEntries` => [propext, Quot.sound] (clean, no sorryAx/native/user axioms).
- atk_1.lean PREPATCH BUG existingDocs-only (drops generatedPages): exit 1 (proof key-lemma step fails to reduce). Reproduces the recorded prepatch failure.
- atk_2.lean partial-domain generatedPages-only: exit 1.
- atk_3.lean control-flow accept-all (no blank skip, no reject arm): exit 1.
- atk_4.lean control-flow-effect reversed order (prepend): exit 1, rewrite pattern mismatch at :117.
- atk_5.lean boundary wrong title (some entry, entry): exit 1.
- atk_6.lean cardinality duplicate append: exit 1.
- atk_7.lean ungrounded-oracle echo intersection (existingDocs && generatedPages): exit 1.

All 7 same-spec wrong impls FAIL verification (exit 1). NONE reaches a closing clean-axiom proof, so there is no faithful patch to materialize or run_resolve — verify=>correct cannot be falsified. patches={} accordingly.

A-leg / correspondence audit: refinement.md declares NO A-legs — 9 legs, all R/I, no kind-3. axiom_check.py is a skip stub consistent with the model: grep of Solution.lean finds no `axiom`/`opaque`/`sorry` (only a comment mentioning them), and #print axioms is clean. Model<->patch correspondence holds: union membership `found_docs | generated_docnames` (patch other.py:122) <-> `(existingDocs ++ generatedPages).contains entry`; `if not entry: continue` <-> blank skip; accepted append `(title=None, docname)` <-> `(none, entry)` in source order. conformance_check.py's shadow (existingDocs++generatedPages membership) matches the post-patch oracle. Downstream patched sites (adapters/collectors) are unchanged-by-default consumers of the same generated-docname set, not independently F2P-observable — single-triple modeling is faithful.

SOUND: prepatch reproduced, 7 distinct attacks run, positive control verifies with clean axioms, none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee) audit for sphinx-doc__sphinx-10673 (lean). Modeled function: the accepted-entry loop of TocTree.parse_content (sphinx/directives/other.py), plain-reference branch.

SPEC INTEGRITY: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend)=True — imports/axioms/pure/post-conditions byte-identical; only impl/proof differ. lean_verify.sh Solution.lean exit 0 (compiles, no sorry; only a benign unused-simp-arg lint on line 114). #print axioms correct_tocEntries = [propext, Quot.sound] — CLEAN, no sorryAx, the proof genuinely closes.

SPEC = problem_spec_tocEntries: result = (requested.filter (e != "" && (existingDocs++generatedPages).contains e)).map (fun e => (none, e)). I.e. entries = [(None,e) for e in content if e!='' and e in (found_docs ∪ generated_pages)].

REAL CALLEE (verified against base worktree + gold-fix semantics): pre-patch other.py has `elif docname not in self.env.found_docs:` (reject). Gold patch adds generated_docnames = frozenset(std.initial_data['labels'].keys()) and changes the test to `not in found_docs | generated_docnames`. Confirmed std.py:603-607 labels = {'genindex','modindex','search'}. Post-patch plain-reference branch: non-blank line accepted iff docname in found_docs∪generated_docnames, appended as (None, docname) with title=None (bare line, ref=docname=entry). This EXACTLY equals the spec on the modeled domain.

DIVERGENCE HUNT: The real callee differs from the spec ONLY on inputs the modeling explicitly and honestly excludes (mapping.md 'Modeling scope' + refinement.md multi-site note): (a) suffix-bearing names ('foo.rst' stripped to 'foo' by the source_suffix loop); (b) docname_join absolutization when self.env.docname is a non-root doc; (c) 'self'/URL lines (accepted BEFORE the found_docs test); (d) glob lines and explicit-title 'Title <doc>' lines. All four are unchanged-by-fix, orthogonal to the F2P behavior, and NOT in the declared modeled domain. The F2P test test_toctree_index uses only root-level plain refs (genindex/modindex/search/foo, docname='index'), where suffix-strip and docname_join are identity — so the modeled domain coincides with the exercised behavior. The one asymmetry I checked (generated page also appearing in found_docs / the 'duplicated entry' warning path) still APPENDS the entry in the real code, matching the spec (which keeps it); warnings are pure side effects not in the modeled value. No membership/order/blank/duplicate case within the plain-reference root-docname no-suffix domain disagrees.

No input found where the spec (a total filter/map function) disagrees with the real repo on the modeled domain. The spec is neither too strong nor overclaiming; the docstring stays abstract and its stated domain matches the fix's observable behavior. G-CONF replica (post-patch oracle vs R/I shadow, 1.2e5 fuzz + exhaustive edge) recorded 0 disagreements, consistent with my analysis. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view rendered via markers.spec_view(LeanBackend.language); same_spec(Solution, Solution_prepatch)=True (spec byte-identical, only impl differs). Lexical screen of the spec view (docstring + axioms + pure + post-conditions regions) shows NO patched repo symbol: 'parse_content','found_docs','generated_docnames','initial_data','labels','std','domains' all ABSENT; no file path ('other.py','toctree.py'), no diff marker ('@@','.diff'), no 'frozenset'. The public problem_statement ALREADY fully discloses the desired behavior: it names genindex/modindex/search and states they should be valid toctree targets without 'nonexisting document' warnings — that is the whole gold edit (found_docs -> found_docs | generated_docnames). Within the spec view, 'search' occurs only in the English phrase 'the search page' (the same public symptom name); 'genindex'/'modindex' do not appear as identifiers at all (only 'general index'/'module index' prose). 'union' appears in the axioms comment and the postcondition uses (existingDocs ++ generatedPages).contains — but this is the formal specification itself, whose purpose is to state the correct post-patch behavior; it abstractly restates 'accept if in existing docs OR the special pages' without naming the gold-diff line, the bug->fix mechanism, or the pre-patch found_docs-only test. It therefore reveals nothing about the gold edit beyond what problem_statement already provides. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

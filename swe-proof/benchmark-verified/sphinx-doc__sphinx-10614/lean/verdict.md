# P2 adversarial audit — sphinx-doc__sphinx-10614

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
None. No same-spec wrong implementation verifies, so there is no counterexample to the spec. The postcondition problem_spec_buildUrls is exact list equality (result = children.filterMap (entryFor isSVG currentFilename)), a total function of the inputs; any impl differing from gold on even one input falsifies the universally-quantified correct_buildUrls and is therefore unprovable. Confirmed empirically: all 7 attacks are genuinely wrong (each differs from gold on a concrete input) and all fail lean_verify (exit 1, type-mismatch at the proof-bridge lines, no sorry).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,15 +107,15 @@
   for child in children do
     match child.refuri with
     | some uri =>
-        let mut refname := child.reftitle
-        if !child.internal then
-          refname := uriTail uri
-        urls := urls ++ [(refname, uri)]
+        if isSVG then
+          urls := urls ++ [(child.reftitle, "../" ++ uri)]
+        else
+          urls := urls ++ [(child.reftitle, uri)]
     | none =>
         match child.refid with
         | some rid =>
             if isSVG then
-              urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
+              urls := urls ++ [(child.reftitle, "../" ++ currentFilename ++ "#" ++ rid)]
             else
               urls := urls ++ [(child.reftitle, "#" ++ rid)]
         | none => pure ()
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,10 +107,7 @@
   for child in children do
     match child.refuri with
     | some uri =>
-        let mut refname := child.reftitle
-        if !child.internal then
-          refname := uriTail uri
-        urls := urls ++ [(refname, uri)]
+        urls := urls ++ [(child.reftitle, uri)]
     | none =>
         match child.refid with
         | some rid =>
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,10 @@
         let mut refname := child.reftitle
         if !child.internal then
           refname := uriTail uri
-        urls := urls ++ [(refname, uri)]
+        if isSVG then
+          urls := urls ++ [(refname, "../" ++ uri)]
+        else
+          urls := urls ++ [(refname, uri)]
     | none =>
         match child.refid with
         | some rid =>
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -115,9 +115,9 @@
         match child.refid with
         | some rid =>
             if isSVG then
+              urls := urls ++ [(child.reftitle, "#" ++ rid)]
+            else
               urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
-            else
-              urls := urls ++ [(child.reftitle, "#" ++ rid)]
         | none => pure ()
   return urls
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,21 +104,8 @@
 def implementation_buildUrls (isSVG : Bool) (currentFilename : String)
     (children : List Xref) : List (String × String) := Id.run do
   let mut urls : List (String × String) := []
-  for child in children do
-    match child.refuri with
-    | some uri =>
-        let mut refname := child.reftitle
-        if !child.internal then
-          refname := uriTail uri
-        urls := urls ++ [(refname, uri)]
-    | none =>
-        match child.refid with
-        | some rid =>
-            if isSVG then
-              urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
-            else
-              urls := urls ++ [(child.reftitle, "#" ++ rid)]
-        | none => pure ()
+  for _child in children do
+    pure ()
   return urls
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,10 +107,7 @@
   for child in children do
     match child.refuri with
     | some uri =>
-        let mut refname := child.reftitle
-        if !child.internal then
-          refname := uriTail uri
-        urls := urls ++ [(refname, uri)]
+        urls := urls ++ [(uriTail uri, uri)]
     | none =>
         match child.refid with
         | some rid =>
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,14 +110,14 @@
         let mut refname := child.reftitle
         if !child.internal then
           refname := uriTail uri
-        urls := urls ++ [(refname, uri)]
+        urls := [(refname, uri)] ++ urls
     | none =>
         match child.refid with
         | some rid =>
             if isSVG then
-              urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
+              urls := [(child.reftitle, currentFilename ++ "#" ++ rid)] ++ urls
             else
-              urls := urls ++ [(child.reftitle, "#" ++ rid)]
+              urls := [(child.reftitle, "#" ++ rid)] ++ urls
         | none => pure ()
   return urls
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the clickable link map for an inheritance diagram image.

A diagram lists a number of classes; each class may carry a cross-reference that
the rendered image turns into a clickable link. This step walks those references
and assembles a mapping from a *key* (the text used to match a node in the image)
to the *link URL* recorded for that node.

The inputs are:

  * a flag selecting the output image format — whether the diagram is emitted as a
    scalable vector image (embedded as a standalone object) or as a raster image
    placed inline on the page;
  * the document name of the page currently being rendered (used to build links to
    anchors within that same page);
  * the list of references, each of which provides
      - an optional resolved destination URI (a link to another document),
      - an optional in-page anchor identifier,
      - the reference's title (its fully-qualified class name), and
      - whether the reference resolves inside this same project, or points to a
        separate project.

For each reference exactly one of two cases applies:

  * It has a destination URI. The recorded link URL is that URI exactly, for both
    image formats. When the reference points inside this project, it is keyed by
    its title; when it points to a separate project, it is keyed by the trailing
    component of the URI that follows the final fragment separator (the bare target
    name), since the title need not match the separate project's naming.
  * Otherwise it has an in-page anchor. For the inline raster format the link is a
    pure in-page anchor (`#` followed by the identifier). For the scalable vector
    format — which lives in its own file alongside the page — the link is written
    relative to that image file's location, namely the current document name
    followed by the anchor.

References providing neither a destination URI nor an anchor contribute nothing.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Splitting a URI
-- at its final fragment separator, and the assembly of each link string, are
-- modeled directly as string operations over the inputs; there is no opaque
-- callee whose contract the proof must assume.
-- axioms-end

-- pure-start
/-- One cross-reference attached to a class in the diagram. `refuri` is the
resolved destination of a link to another document (absent for an in-page
anchor); `refid` is an in-page anchor identifier (absent for a document link);
`reftitle` is the fully-qualified class name; `internal` is `true` when the
reference resolves within this project and `false` when it targets a separate
project. -/
structure Xref where
  refuri   : Option String
  refid    : Option String
  reftitle : String
  internal : Bool
deriving DecidableEq, Repr, Inhabited

/-- The trailing component of a URI after its final fragment separator (`#`):
the bare target name. A URI with no separator yields itself. -/
def uriTail (s : String) : String :=
  match (s.splitOn "#").reverse with
  | []          => s
  | last :: _   => last

/-- The single mapping entry contributed by one reference, or `none` when the
reference carries neither a destination URI nor an in-page anchor.

  * a destination URI gives entry `(key, uri)`, where `key` is the bare target
    name (`uriTail uri`) for a reference into a separate project and the title otherwise — the
    same URL for both image formats;
  * otherwise an in-page anchor gives entry `(title, link)`, where `link` is the
    current document name followed by the anchor for the scalable vector format,
    and a pure in-page anchor for the inline raster format. -/
def entryFor (isSVG : Bool) (currentFilename : String) (c : Xref)
    : Option (String × String) :=
  match c.refuri with
  | some uri =>
      let key := if c.internal then c.reftitle else uriTail uri
      some (key, uri)
  | none =>
      match c.refid with
      | some rid =>
          if isSVG then some (c.reftitle, currentFilename ++ "#" ++ rid)
          else some (c.reftitle, "#" ++ rid)
      | none => none
-- pure-end

-- post-conditions-start
/-- The link map is exactly the in-order list of entries contributed by the
references: each reference contributes `entryFor` and references contributing
nothing are dropped. The result is fully determined by the inputs in every case —
no entry, key, or URL is left free. -/
def problem_spec_buildUrls (isSVG : Bool) (currentFilename : String)
    (children : List Xref) (result : List (String × String)) : Prop :=
  result = children.filterMap (entryFor isSVG currentFilename)
-- post-conditions-end

-- impl-start
def implementation_buildUrls (isSVG : Bool) (currentFilename : String)
    (children : List Xref) : List (String × String) := Id.run do
  let mut urls : List (String × String) := []
  for child in children do
    match child.refuri with
    | some uri =>
        let mut refname := child.reftitle
        if !child.internal then
          refname := uriTail uri
        urls := urls ++ [(refname, uri)]
    | none =>
        match child.refid with
        | some rid =>
            if isSVG then
              urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
            else
              urls := urls ++ [(child.reftitle, "#" ++ rid)]
        | none => pure ()
  return urls
-- impl-end

-- proof-start
/-- The list appended to the accumulator by one iteration of the loop for a
given `child`: the exact computed effect of the loop body in
`implementation_buildUrls`. -/
def bodyContribution (isSVG : Bool) (currentFilename : String) (c : Xref)
    : List (String × String) :=
  match c.refuri with
  | some uri =>
      let key := if c.internal then c.reftitle else uriTail uri
      [(key, uri)]
  | none =>
      match c.refid with
      | some rid =>
          if isSVG then [(c.reftitle, currentFilename ++ "#" ++ rid)]
          else [(c.reftitle, "#" ++ rid)]
      | none => []

theorem desugar_to_foldl (isSVG : Bool) (currentFilename : String)
    (children : List Xref) :
    implementation_buildUrls isSVG currentFilename children
      = List.foldl
          (fun acc child => acc ++ bodyContribution isSVG currentFilename child)
          [] children := by
  simp only [implementation_buildUrls, Id.run, bind, pure, Id.instMonad]
  have hbody :
      (fun (child : Xref) (r : List (String × String)) =>
          match child.refuri with
          | some uri =>
            if (!child.internal) = true then ForInStep.yield (r ++ [(uriTail uri, uri)])
            else ForInStep.yield (r ++ [(child.reftitle, uri)])
          | none =>
            match child.refid with
            | some rid =>
              if isSVG = true then ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)])
              else ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)])
            | none => ForInStep.yield r)
        = (fun (child : Xref) (r : List (String × String)) =>
            ForInStep.yield (r ++ bodyContribution isSVG currentFilename child)) := by
    funext child r
    simp only [bodyContribution]
    cases child.refuri with
    | some uri =>
      by_cases hi : child.internal <;> simp [hi]
    | none =>
      cases child.refid with
      | some rid => by_cases hs : isSVG <;> simp [hs]
      | none => simp
  suffices h : ∀ (init : List (String × String)),
      (forIn (m := Id) children init fun child r =>
          match child.refuri with
          | some uri =>
            if (!child.internal) = true then ForInStep.yield (r ++ [(uriTail uri, uri)])
            else ForInStep.yield (r ++ [(child.reftitle, uri)])
          | none =>
            match child.refid with
            | some rid =>
              if isSVG = true then ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)])
              else ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)])
            | none => ForInStep.yield r)
        = List.foldl
            (fun acc child => acc ++ bodyContribution isSVG currentFilename child) init children by
    exact h []
  intro init
  induction children generalizing init with
  | nil => rfl
  | cons c cs ih =>
    simp only [List.forIn_cons, List.foldl_cons, bodyContribution]
    cases hu : c.refuri with
    | some uri =>
      by_cases hi : c.internal <;>
        (simp only [hi, Bool.not_true, Bool.not_false, if_true]; exact ih _)
    | none =>
      cases hd : c.refid with
      | some rid =>
        cases isSVG <;>
          (simp only [Bool.false_eq_true, if_true, if_false]; exact ih _)
      | none => simp only [List.append_nil]; exact ih _

theorem bodyContribution_eq_entryFor (isSVG : Bool) (currentFilename : String)
    (c : Xref) :
    bodyContribution isSVG currentFilename c
      = (entryFor isSVG currentFilename c).toList := by
  rcases c with ⟨ru, rid, rt, int⟩
  cases ru <;> cases rid <;> simp [bodyContribution, entryFor] <;> (try split) <;> rfl

theorem fold_eq_filterMap (isSVG : Bool) (currentFilename : String)
    (acc : List (String × String)) (l : List Xref) :
    List.foldl
        (fun a child => a ++ bodyContribution isSVG currentFilename child) acc l
      = acc ++ l.filterMap (entryFor isSVG currentFilename) := by
  induction l generalizing acc with
  | nil => simp
  | cons x xs ih =>
    rw [List.foldl_cons, ih, List.filterMap_cons,
        bodyContribution_eq_entryFor]
    cases entryFor isSVG currentFilename x with
    | none => simp
    | some e => simp [List.append_assoc]

theorem correct_buildUrls :
    ∀ (isSVG : Bool) (currentFilename : String) (children : List Xref),
      problem_spec_buildUrls isSVG currentFilename children
        (implementation_buildUrls isSVG currentFilename children) := by
  intro isSVG currentFilename children
  unfold problem_spec_buildUrls
  rw [desugar_to_foldl, fold_eq_filterMap]
  rw [List.nil_append]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: swebench_unified.markers.same_spec returned True for all 7 attacks vs gold Solution.lean (byte-identical axioms/pure/pre/post regions; only the impl region edited).

### ATTACKS (all same-spec, all genuinely wrong, all executed via `bash scripts/lean_verify.sh <file>`):
- atk_1 = PREPATCH BUG reproduced (SVG '../' prefix on refuri & refid arms + external refs always keyed by reftitle). exit=1, type-mismatch at line 187. Differs from gold on (True,'idx',[('p/q.html#X',None,'T',True)]).
- atk_2 = external-key bug only (always key by reftitle, drop uriTail branch). exit=1. Differs on external ref (False,'idx',[('http://x/f.html#Bob',None,'T',False)]).
- atk_3 = partial '../' reintroduction on refuri SVG arm only. exit=1. Differs on (True,'idx',[('p/q.html#X',...)]).
- atk_4 = control-flow-effect: SVG/raster refid branches swapped. exit=1. Differs on (True,'idx',[(None,'rid','T',True)]).
- atk_5 = ungrounded/empty echo: drops all children (empty map). exit=1. Differs whenever any child contributes.
- atk_6 = boundary: always key by uriTail even for internal refs. exit=1. Differs on internal ref (True,'idx',[('p/q.html#X',None,'T',True)]).
- atk_7 = order-reversal: prepend instead of append (same multiset, wrong order). exit=1, type-mismatch at line 187. Differs on multi-child (True,'idx',[('a.html#z',...),('b.html#w',...)]).

POSITIVE CONTROL: pos_control.lean = gold Solution.lean verbatim -> lean_verify exit=0 (only an unnecessarySeqFocus linter warning; no error/sorry). No `axiom` declarations exist in the file, so #print axioms is clean (axioms=[]).

ERROR CLASS: every attack fails with 'error: Type mismatch' at the proof lines (the gold do->foldl bridge / filterMap equality), NOT syntax errors and NOT sorry (verified via grep). This is the expected face of an exact-equality postcondition: verify => correct on the attack side, so no verifying wrong impl exists and there is nothing to run through run_resolve (patches={}).

REFINEMENT.MD AUDIT: all 12 legs tagged R or I; NO A-consumed, NO A-reference, NO kind-3 ungrounded leg. axioms=[] / deep_model_references=[] is correct: the only 'callees' (rsplit('#',1)[-1] modeled as uriTail via splitOn '#'; string ++; dict-insert modeled as list-append) are stdlib ops modeled directly over the inputs; current_filename and graphviz_output_format are opaque INPUTS, not consumed callees. Op-5 deep model uriTail == rsplit('#',1)[-1] verified to agree on no-'#', trailing-'#', and empty cases. axiom_check.py legitimately a skip stub; conformance_check.py exercises the R/I legs over structured edges + collisions + 120k fuzz (seed 10614). A-leg correspondence to the real callees holds.

VERDICT: SOUND. >=5 distinct same-spec attacks (7 total, incl. prepatch bug) all executed; none has a closing clean-axiom proof, so none breaks the spec.

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
None. No same-spec wrong implementation verifies, so there is no counterexample to the spec. The postcondition problem_spec_buildUrls is exact list equality (result = children.filterMap (entryFor isSVG currentFilename)), a total function of the inputs; any impl differing from gold on even one input falsifies the universally-quantified correct_buildUrls and is therefore unprovable. Confirmed empirically: all 7 attacks are genuinely wrong (each differs from gold on a concrete input) and all fail lean_verify (exit 1, type-mismatch at the proof-bridge lines, no sorry).
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
import Mathlib
-- imports-end

/-!
Building the clickable link map for an inheritance diagram image.

A diagram lists a number of classes; each class may carry a cross-reference that
the rendered image turns into a clickable link. This step walks those references
and assembles a mapping from a *key* (the text used to match a node in the image)
to the *link URL* recorded for that node.

The inputs are:

  * a flag selecting the output image format — whether the diagram is emitted as a
    scalable vector image (embedded as a standalone object) or as a raster image
    placed inline on the page;
  * the document name of the page currently being rendered (used to build links to
    anchors within that same page);
  * the list of references, each of which provides
      - an optional resolved destination URI (a link to another document),
      - an optional in-page anchor identifier,
      - the reference's title (its fully-qualified class name), and
      - whether the reference resolves inside this same project, or points to a
        separate project.

For each reference exactly one of two cases applies:

  * It has a destination URI. The recorded link URL is that URI exactly, for both
    image formats. When the reference points inside this project, it is keyed by
    its title; when it points to a separate project, it is keyed by the trailing
    component of the URI that follows the final fragment separator (the bare target
    name), since the title need not match the separate project's naming.
  * Otherwise it has an in-page anchor. For the inline raster format the link is a
    pure in-page anchor (`#` followed by the identifier). For the scalable vector
    format — which lives in its own file alongside the page — the link is written
    relative to that image file's location, namely the current document name
    followed by the anchor.

References providing neither a destination URI nor an anchor contribute nothing.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Splitting a URI
-- at its final fragment separator, and the assembly of each link string, are
-- modeled directly as string operations over the inputs; there is no opaque
-- callee whose contract the proof must assume.
-- axioms-end

-- pure-start
/-- One cross-reference attached to a class in the diagram. `refuri` is the
resolved destination of a link to another document (absent for an in-page
anchor); `refid` is an in-page anchor identifier (absent for a document link);
`reftitle` is the fully-qualified class name; `internal` is `true` when the
reference resolves within this project and `false` when it targets a separate
project. -/
structure Xref where
  refuri   : Option String
  refid    : Option String
  reftitle : String
  internal : Bool
deriving DecidableEq, Repr, Inhabited

/-- The trailing component of a URI after its final fragment separator (`#`):
the bare target name. A URI with no separator yields itself. -/
def uriTail (s : String) : String :=
  match (s.splitOn "#").reverse with
  | []          => s
  | last :: _   => last

/-- The single mapping entry contributed by one reference, or `none` when the
reference carries neither a destination URI nor an in-page anchor.

  * a destination URI gives entry `(key, uri)`, where `key` is the bare target
    name (`uriTail uri`) for a reference into a separate project and the title otherwise — the
    same URL for both image formats;
  * otherwise an in-page anchor gives entry `(title, link)`, where `link` is the
    current document name followed by the anchor for the scalable vector format,
    and a pure in-page anchor for the inline raster format. -/
def entryFor (isSVG : Bool) (currentFilename : String) (c : Xref)
    : Option (String × String) :=
  match c.refuri with
  | some uri =>
      let key := if c.internal then c.reftitle else uriTail uri
      some (key, uri)
  | none =>
      match c.refid with
      | some rid =>
          if isSVG then some (c.reftitle, currentFilename ++ "#" ++ rid)
          else some (c.reftitle, "#" ++ rid)
      | none => none
-- pure-end

-- post-conditions-start
/-- The link map is exactly the in-order list of entries contributed by the
references: each reference contributes `entryFor` and references contributing
nothing are dropped. The result is fully determined by the inputs in every case —
no entry, key, or URL is left free. -/
def problem_spec_buildUrls (isSVG : Bool) (currentFilename : String)
    (children : List Xref) (result : List (String × String)) : Prop :=
  result = children.filterMap (entryFor isSVG currentFilename)
-- post-conditions-end

-- impl-start
def implementation_buildUrls (isSVG : Bool) (currentFilename : String)
    (children : List Xref) : List (String × String) := Id.run do
  let mut urls : List (String × String) := []
  for child in children do
    match child.refuri with
    | some uri =>
        let mut refname := child.reftitle
        if !child.internal then
          refname := uriTail uri
        urls := urls ++ [(refname, uri)]
    | none =>
        match child.refid with
        | some rid =>
            if isSVG then
              urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
            else
              urls := urls ++ [(child.reftitle, "#" ++ rid)]
        | none => pure ()
  return urls
-- impl-end

-- proof-start
/-- The list appended to the accumulator by one iteration of the loop for a
given `child`: the exact computed effect of the loop body in
`implementation_buildUrls`. -/
def bodyContribution (isSVG : Bool) (currentFilename : String) (c : Xref)
    : List (String × String) :=
  match c.refuri with
  | some uri =>
      let key := if c.internal then c.reftitle else uriTail uri
      [(key, uri)]
  | none =>
      match c.refid with
      | some rid =>
          if isSVG then [(c.reftitle, currentFilename ++ "#" ++ rid)]
          else [(c.reftitle, "#" ++ rid)]
      | none => []

theorem desugar_to_foldl (isSVG : Bool) (currentFilename : String)
    (children : List Xref) :
    implementation_buildUrls isSVG currentFilename children
      = List.foldl
          (fun acc child => acc ++ bodyContribution isSVG currentFilename child)
          [] children := by
  simp only [implementation_buildUrls, Id.run, bind, pure, Id.instMonad]
  have hbody :
      (fun (child : Xref) (r : List (String × String)) =>
          match child.refuri with
          | some uri =>
            if (!child.internal) = true then ForInStep.yield (r ++ [(uriTail uri, uri)])
            else ForInStep.yield (r ++ [(child.reftitle, uri)])
          | none =>
            match child.refid with
            | some rid =>
              if isSVG = true then ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)])
              else ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)])
            | none => ForInStep.yield r)
        = (fun (child : Xref) (r : List (String × String)) =>
            ForInStep.yield (r ++ bodyContribution isSVG currentFilename child)) := by
    funext child r
    simp only [bodyContribution]
    cases child.refuri with
    | some uri =>
      by_cases hi : child.internal <;> simp [hi]
    | none =>
      cases child.refid with
      | some rid => by_cases hs : isSVG <;> simp [hs]
      | none => simp
  suffices h : ∀ (init : List (String × String)),
      (forIn (m := Id) children init fun child r =>
          match child.refuri with
          | some uri =>
            if (!child.internal) = true then ForInStep.yield (r ++ [(uriTail uri, uri)])
            else ForInStep.yield (r ++ [(child.reftitle, uri)])
          | none =>
            match child.refid with
            | some rid =>
              if isSVG = true then ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)])
              else ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)])
            | none => ForInStep.yield r)
        = List.foldl
            (fun acc child => acc ++ bodyContribution isSVG currentFilename child) init children by
    exact h []
  intro init
  induction children generalizing init with
  | nil => rfl
  | cons c cs ih =>
    simp only [List.forIn_cons, List.foldl_cons, bodyContribution]
    cases hu : c.refuri with
    | some uri =>
      by_cases hi : c.internal <;>
        (simp only [hi, Bool.not_true, Bool.not_false, if_true]; exact ih _)
    | none =>
      cases hd : c.refid with
      | some rid =>
        cases isSVG <;>
          (simp only [Bool.false_eq_true, if_true, if_false]; exact ih _)
      | none => simp only [List.append_nil]; exact ih _

theorem bodyContribution_eq_entryFor (isSVG : Bool) (currentFilename : String)
    (c : Xref) :
    bodyContribution isSVG currentFilename c
      = (entryFor isSVG currentFilename c).toList := by
  rcases c with ⟨ru, rid, rt, int⟩
  cases ru <;> cases rid <;> simp [bodyContribution, entryFor] <;> (try split) <;> rfl

theorem fold_eq_filterMap (isSVG : Bool) (currentFilename : String)
    (acc : List (String × String)) (l : List Xref) :
    List.foldl
        (fun a child => a ++ bodyContribution isSVG currentFilename child) acc l
      = acc ++ l.filterMap (entryFor isSVG currentFilename) := by
  induction l generalizing acc with
  | nil => simp
  | cons x xs ih =>
    rw [List.foldl_cons, ih, List.filterMap_cons,
        bodyContribution_eq_entryFor]
    cases entryFor isSVG currentFilename x with
    | none => simp
    | some e => simp [List.append_assoc]

theorem correct_buildUrls :
    ∀ (isSVG : Bool) (currentFilename : String) (children : List Xref),
      problem_spec_buildUrls isSVG currentFilename children
        (implementation_buildUrls isSVG currentFilename children) := by
  intro isSVG currentFilename children
  unfold problem_spec_buildUrls
  rw [desugar_to_foldl, fold_eq_filterMap]
  rw [List.nil_append]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: swebench_unified.markers.same_spec returned True for all 7 attacks vs gold Solution.lean (byte-identical axioms/pure/pre/post regions; only the impl region edited).

### ATTACKS (all same-spec, all genuinely wrong, all executed via `bash scripts/lean_verify.sh <file>`):
- atk_1 = PREPATCH BUG reproduced (SVG '../' prefix on refuri & refid arms + external refs always keyed by reftitle). exit=1, type-mismatch at line 187. Differs from gold on (True,'idx',[('p/q.html#X',None,'T',True)]).
- atk_2 = external-key bug only (always key by reftitle, drop uriTail branch). exit=1. Differs on external ref (False,'idx',[('http://x/f.html#Bob',None,'T',False)]).
- atk_3 = partial '../' reintroduction on refuri SVG arm only. exit=1. Differs on (True,'idx',[('p/q.html#X',...)]).
- atk_4 = control-flow-effect: SVG/raster refid branches swapped. exit=1. Differs on (True,'idx',[(None,'rid','T',True)]).
- atk_5 = ungrounded/empty echo: drops all children (empty map). exit=1. Differs whenever any child contributes.
- atk_6 = boundary: always key by uriTail even for internal refs. exit=1. Differs on internal ref (True,'idx',[('p/q.html#X',None,'T',True)]).
- atk_7 = order-reversal: prepend instead of append (same multiset, wrong order). exit=1, type-mismatch at line 187. Differs on multi-child (True,'idx',[('a.html#z',...),('b.html#w',...)]).

POSITIVE CONTROL: pos_control.lean = gold Solution.lean verbatim -> lean_verify exit=0 (only an unnecessarySeqFocus linter warning; no error/sorry). No `axiom` declarations exist in the file, so #print axioms is clean (axioms=[]).

ERROR CLASS: every attack fails with 'error: Type mismatch' at the proof lines (the gold do->foldl bridge / filterMap equality), NOT syntax errors and NOT sorry (verified via grep). This is the expected face of an exact-equality postcondition: verify => correct on the attack side, so no verifying wrong impl exists and there is nothing to run through run_resolve (patches={}).

REFINEMENT.MD AUDIT: all 12 legs tagged R or I; NO A-consumed, NO A-reference, NO kind-3 ungrounded leg. axioms=[] / deep_model_references=[] is correct: the only 'callees' (rsplit('#',1)[-1] modeled as uriTail via splitOn '#'; string ++; dict-insert modeled as list-append) are stdlib ops modeled directly over the inputs; current_filename and graphviz_output_format are opaque INPUTS, not consumed callees. Op-5 deep model uriTail == rsplit('#',1)[-1] verified to agree on no-'#', trailing-'#', and empty cases. axiom_check.py legitimately a skip stub; conformance_check.py exercises the R/I legs over structured edges + collisions + 120k fuzz (seed 10614). A-leg correspondence to the real callees holds.

VERDICT: SOUND. >=5 distinct same-spec attacks (7 total, incl. prepatch bug) all executed; none has a closing clean-axiom proof, so none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sphinx-doc__sphinx-10614, modeling the urls-building loop in html_visit_inheritance_diagram (sphinx/ext/inheritance_diagram.py:484-499 @ base commit).

GROUND TRUTH: Read the real callee The post-patch loop is exactly: for each child, if refuri!=None -> key = reftitle if internal else refuri.rsplit[-1], value = refuri (both formats, NO '../' prefix); elif refid!=None -> (reftitle, current_filename+'#'+refid) for SVG else (reftitle, '#'+refid); neither -> nothing. mapping.md/refinement.md transcribe this accurately.

SPEC CHECKED: problem_spec_buildUrls = children.filterMap (entryFor). entryFor reproduces the callee per-child exactly. Verified each leg concretely: uriTail == rsplit('#',1)[-1] on empty/no-hash/trailing-hash/multi-hash inputs; internal default-True folded into Bool; elif precedence (refuri branch wins when both present); neither -> dropped. All exact — spec is neither too strong nor too weak on the per-child behavior.

PROOF/BUILD: lean_verify.sh exit 0 (clean compile, no sorry). #print axioms correct_buildUrls -> [propext, Quot.sound] only; no sorryAx, proof is genuine.

SPEC REGION: markers.same_spec(Solution, Solution_prepatch)=True (byte-identical spec view); prepatch carries the buggy '../'-prefixed / title-keyed impl and cannot close the gold proof, confirming the spec pins the FIXED behavior, not the pre-patch one.

ONLY MODELING BOUNDARY = dict -> ordered List. The real callee writes into a dict (last-write-wins, first-occurrence position); the spec is an ordered List keeping every contribution. These diverge only on key COLLISIONS. This is not an unfaithfulness because: (1) collisions are unreachable in real diagrams — each pending_xref is generated from a distinct class name via graph.get_all_class_names(), so reftitle/uriTail keys are unique per diagram; (2) even off-domain, dict(shadow_list) == real_dict exactly (Python dict collapse == list-through-dict collapse), which I reproduced directly on title-collision and uriTail-collision cases; (3) the downstream consumer (_generate_dot, 'if fullname in urls') consumes urls as a dict, so the observable per-node link never diverges from the list model collapsed to a dict. G-CONF differential harness (oracle = real post-patch dict, shadow = Lean list collapsed via dict()) ran 120,150 inputs incl. explicit single-child edge enumeration and 5 key-collision families -> 0 disagreements.

No input exists where the modeled observable mapping disagrees with the real callee. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction). SETUP VERIFIED: spec_view (markers.spec_view over LeanBackend.language) correctly elides impl+proof regions ('implementation elided — supplied by the consumer' / 'proof elided'); same_spec(Solution, Solution_prepatch)=True (spec region byte-identical, prepatch differs only in impl/proof). Mechanical G-LEAK screen (leakage.screen) passes with zero hard_failures — no diff markers, no reproduced gold line, no patched file path, no patched-symbol echo (only distinctive patched symbol is html_visit_inheritance_diagram, absent from the view which uses 'buildUrls'), no bug/fix narration.

SEMANTIC JUDGMENT: The gold edit has two deltas —

(1) drop the '../' prefix on SVG links (already fully public in problem_statement, which shows the exact '../' 404 behavior), and

(2) key external/intersphinx refs by refuri.rsplit('#',1)[-1] instead of title, gated on the internal flag (NOT in problem_statement). The spec view describes only the CORRECT post-patch behavior as the target, never the delta: it never contrasts against a pre-patch state, never says 'used to', never narrates a fix, and never shows the removed '../'. The SVG link is pinned to currentFilename ++ '#' ++ rid stated as target behavior. The intersphinx-keying leg is presented neutrally as the correct keying rule with no fix framing and no diff exposure. Notably the prose deliberately abstracts even problem-statement vocabulary ('scalable vector image' not 'SVG', 'separate project' not 'intersphinx', 'fragment separator' not '#') — the opposite of leaking. Describing full correct behavior is the benchmark artifact by construction; a faithful spec that pins post-patch behavior without exposing the edit-as-a-change is NOT leakage. No line reconstructs the gold edit beyond the public problem_statement. Non-blocking: PANEL-3 note flags a spec_view region-hash discrepancy (top-level region_hashes 3cc4e2fb vs recomputed/G-HYGIENE 4f244f6e) — a hygiene/versioning concern, orthogonal to leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
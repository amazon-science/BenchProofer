# P2 adversarial audit — sphinx-doc__sphinx-9673

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
fields=[["returns"]], annotations=[("return","int")]: gold augmentSpec = [("rtype","int")] but any impl that drops hunk 1 (plural 'returns' not recognized in the classification loop) yields []; distinguished by `decide` (machine-checked in ce_check.lean, exit 0). This makes correct_augment a concretely FALSE equality for every reverted-hunk / wrong impl, unprovable with clean axioms.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,7 +119,7 @@
         pure ()
     else if p0 == "type" then
       hasType := hasType ++ [joinSp (parts.drop 1)]
-    else if p0 == "return" || p0 == "returns" then
+    else if p0 == "return" then
       hasDesc := hasDesc ++ ["return"]
     else if p0 == "rtype" then
       hasType := hasType ++ ["return"]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,7 +128,7 @@
   let mut out : List (String × String) := []
   for entry in annotations do
     let (name, ann) := entry
-    if name == "return" || name == "returns" then
+    if name == "return" then
       pure ()
     else if hasDesc.contains name && !hasType.contains name then
       out := out ++ [("type " ++ name, ann)]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,7 @@
     let p0 := parts.headD ""
     if p0 == "param" then
       if parts.length == 2 then
-        hasDesc := hasDesc ++ [parts.getD 1 ""]
+        pure ()
       else if parts.length > 2 then
         let name := joinSp (parts.drop 2)
         hasDesc := hasDesc ++ [name]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -118,7 +118,7 @@
       else
         pure ()
     else if p0 == "type" then
-      hasType := hasType ++ [joinSp (parts.drop 1)]
+      hasType := hasType ++ [joinSp (parts.drop 2)]
     else if p0 == "return" || p0 == "returns" then
       hasDesc := hasDesc ++ ["return"]
     else if p0 == "rtype" then
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,7 +131,7 @@
     if name == "return" || name == "returns" then
       pure ()
     else if hasDesc.contains name && !hasType.contains name then
-      out := out ++ [("type " ++ name, ann)]
+      out := out ++ [("type" ++ name, ann)]
     else
       pure ()
   match annotations.lookup "return" with
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,8 +136,7 @@
       pure ()
   match annotations.lookup "return" with
   | some ann =>
-    if hasDesc.contains "return" && !hasType.contains "return" then
-      out := out ++ [("rtype", ann)]
+    pure ()
   | none => pure ()
   return out
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The modeled procedure is
-- pure control flow over two abstract inputs: the parsed markers of a
-- documentation field list (each already split into whitespace-separated tokens
-- by the caller) and an ordered table mapping documented names to their declared
-- type text. Both are produced by the caller/environment; the decision logic the
-- procedure performs is modeled DEEPLY below. The proof agent may add `_prop`
-- axioms only if a proof obligation needs one.
-- axioms-end

-- pure-start
/-- Join a list of tokens with single spaces (the inverse of splitting a marker
on runs of whitespace). -/
def joinSp (parts : List String) : String := String.intercalate " " parts

/-- Classify one parsed field marker, updating the running pair of
"has a description" / "has a declared type" name collections.

`parts` is the marker split into whitespace-separated tokens. A marker headed by
`param` records a described name (and, in its three-token form, also a typed
name); a marker headed by `type` records a typed name; a marker headed by the
short OR the plural return keyword records that the result carries a description;
a marker headed by `rtype` records that the result carries a declared type. -/
def classifyStep (acc : List String × List String) (parts : List String) :
    List String × List String :=
  let (hasDesc, hasType) := acc
  let p0 := parts.headD ""
  if p0 == "param" then
    if parts.length == 2 then
      (hasDesc ++ [parts.getD 1 ""], hasType)
    else if parts.length > 2 then
      let name := joinSp (parts.drop 2)
      (hasDesc ++ [name], hasType ++ [name])
    else
      (hasDesc, hasType)
  else if p0 == "type" then
    (hasDesc, hasType ++ [joinSp (parts.drop 1)])
  else if p0 == "return" || p0 == "returns" then
    (hasDesc ++ ["return"], hasType)
  else if p0 == "rtype" then
    (hasDesc, hasType ++ ["return"])
  else
    (hasDesc, hasType)

/-- Fold `classifyStep` over every parsed marker of the field list. -/
def classify (fields : List (List String)) : List String × List String :=
  fields.foldl classifyStep ([], [])

/-- Process one entry of the name→type table, appending a freshly-built type
field when that name already carries a description but no declared type. The
short and plural return keywords are skipped here (the result's type is handled
separately, after the table is walked). -/
def outStep (hasDesc hasType : List String)
    (acc : List (String × String)) (entry : String × String) :
    List (String × String) :=
  let (name, ann) := entry
  if name == "return" || name == "returns" then
    acc
  else if hasDesc.contains name && !hasType.contains name then
    acc ++ [("type " ++ name, ann)]
  else
    acc

/-- The list of fields appended to a documentation field list when augmenting it
with declared-type information.

For every documented name (other than the result) that already carries a
description but no declared type, a `type <name>` field carrying its type text is
appended, in table order. Finally, if the result has declared type text and the
field list shows a result description but no declared result type, a single
`rtype` field carrying that text is appended. -/
def augmentSpec (fields : List (List String)) (annotations : List (String × String)) :
    List (String × String) :=
  let (hasDesc, hasType) := classify fields
  let typeFields := annotations.foldl (outStep hasDesc hasType) []
  match annotations.lookup "return" with
  | some ann =>
    if hasDesc.contains "return" && !hasType.contains "return" then
      typeFields ++ [("rtype", ann)]
    else
      typeFields
  | none => typeFields
-- pure-end

-- post-conditions-start
/-- Specification of augmenting a documentation field list with declared types.

`fields` is the field list, each marker pre-split into whitespace-separated
tokens. `annotations` is the ordered table mapping each documented name to its
declared type text (the result's type, when present, is stored under the name
`return`). `result` is the list of fields the procedure appends.

The result is exactly the appended-field list determined by the inputs: the
per-name `type <name>` fields followed by the optional `rtype` field, as
characterised by `augmentSpec`. -/
def problem_spec_augment (fields : List (List String))
    (annotations : List (String × String)) (result : List (String × String)) : Prop :=
  result = augmentSpec fields annotations
-- post-conditions-end

-- impl-start
def implementation_augment (fields : List (List String))
    (annotations : List (String × String)) : List (String × String) := Id.run do
  let mut hasDesc : List String := []
  let mut hasType : List String := []
  for parts in fields do
    let p0 := parts.headD ""
    if p0 == "param" then
      if parts.length == 2 then
        hasDesc := hasDesc ++ [parts.getD 1 ""]
      else if parts.length > 2 then
        let name := joinSp (parts.drop 2)
        hasDesc := hasDesc ++ [name]
        hasType := hasType ++ [name]
      else
        pure ()
    else if p0 == "type" then
      hasType := hasType ++ [joinSp (parts.drop 1)]
    else if p0 == "return" || p0 == "returns" then
      hasDesc := hasDesc ++ ["return"]
    else if p0 == "rtype" then
      hasType := hasType ++ ["return"]
    else
      pure ()
  let mut out : List (String × String) := []
  for entry in annotations do
    let (name, ann) := entry
    if name == "return" || name == "returns" then
      pure ()
    else if hasDesc.contains name && !hasType.contains name then
      out := out ++ [("type " ++ name, ann)]
    else
      pure ()
  match annotations.lookup "return" with
  | some ann =>
    if hasDesc.contains "return" && !hasType.contains "return" then
      out := out ++ [("rtype", ann)]
  | none => pure ()
  return out
-- impl-end


-- proof-start
/-- The first loop's body (the `p0`/length cascade producing the mutated
`(hasDesc, hasType)` pair) equals `classifyStep acc parts` for every input. -/
theorem classifyBodyEq (acc : List String × List String) (parts : List String) :
    (if (parts.headD "" == "param") = true then
        if (parts.length == 2) = true then (acc.1 ++ [parts.getD 1 ""], acc.2)
        else if parts.length > 2 then
          (acc.1 ++ [joinSp (parts.drop 2)], acc.2 ++ [joinSp (parts.drop 2)])
        else (acc.1, acc.2)
      else if (parts.headD "" == "type") = true then
        (acc.1, acc.2 ++ [joinSp (parts.drop 1)])
      else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
        (acc.1 ++ ["return"], acc.2)
      else if (parts.headD "" == "rtype") = true then (acc.1, acc.2 ++ ["return"])
      else (acc.1, acc.2)) = classifyStep acc parts := by
  simp only [classifyStep]

/-- The first `for parts in fields` loop (starting `⟨[],[]⟩`) computes
`classify fields`, rendered with the mutable-variable pair (`MProd`) the
`Id.run do` block actually uses. -/
theorem loop1_is_classify (fields : List (List String)) :
    (forIn fields (⟨[], []⟩ : MProd (List String) (List String)) fun parts r =>
        (if (parts.headD "" == "param") = true then
            if (parts.length == 2) = true then
              ForInStep.yield ⟨r.fst ++ [parts.getD 1 ""], r.snd⟩
            else if parts.length > 2 then
              ForInStep.yield ⟨r.fst ++ [joinSp (parts.drop 2)], r.snd ++ [joinSp (parts.drop 2)]⟩
            else ForInStep.yield ⟨r.fst, r.snd⟩
          else if (parts.headD "" == "type") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ [joinSp (parts.drop 1)]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else ForInStep.yield ⟨r.fst, r.snd⟩ : Id _))
      = ⟨(classify fields).1, (classify fields).2⟩ := by
  -- Step 1: the loop body always yields, so rewrite it to `ForInStep.yield (f r parts)`.
  have hbody :
      (fun (parts : List String) (r : MProd (List String) (List String)) =>
        (if (parts.headD "" == "param") = true then
            if (parts.length == 2) = true then
              ForInStep.yield ⟨r.fst ++ [parts.getD 1 ""], r.snd⟩
            else if parts.length > 2 then
              ForInStep.yield ⟨r.fst ++ [joinSp (parts.drop 2)], r.snd ++ [joinSp (parts.drop 2)]⟩
            else ForInStep.yield ⟨r.fst, r.snd⟩
          else if (parts.headD "" == "type") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ [joinSp (parts.drop 1)]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else ForInStep.yield ⟨r.fst, r.snd⟩ : Id _))
      = (fun parts r => ForInStep.yield
          (⟨(classifyStep (r.fst, r.snd) parts).1, (classifyStep (r.fst, r.snd) parts).2⟩
            : MProd (List String) (List String))) := by
    funext parts r
    simp only [classifyStep]
    split_ifs <;> rfl
  rw [hbody, List.forIn_yield_eq_foldl]
  -- Step 2: relate the MProd-valued foldl to the pair-valued `classify` foldl.
  have key : ∀ (fs : List (List String)) (r : MProd (List String) (List String)),
      (fs.foldl (fun r parts =>
          (⟨(classifyStep (r.fst, r.snd) parts).1, (classifyStep (r.fst, r.snd) parts).2⟩
            : MProd (List String) (List String))) r)
        = ⟨(fs.foldl classifyStep (r.fst, r.snd)).1, (fs.foldl classifyStep (r.fst, r.snd)).2⟩ := by
    intro fs
    induction fs with
    | nil => intro r; rfl
    | cons p ps ih => intro r; simp only [List.foldl_cons]; rw [ih]
  rw [key]
  rfl

/-- The second loop's body equals `outStep hasDesc hasType acc entry` for every
entry (the `return`/`returns` skip and the described-but-untyped append). -/
theorem outBodyEq (hasDesc hasType : List String)
    (acc : List (String × String)) (entry : String × String) :
    (if (entry.1 == "return" || entry.1 == "returns") = true then acc
      else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
        acc ++ [("type " ++ entry.1, entry.2)]
      else acc) = outStep hasDesc hasType acc entry := by
  simp only [outStep]

/-- The second `for entry in annotations` loop (starting `[]`), using the
`hasDesc`/`hasType` from loop 1, computes `annotations.foldl (outStep …) []`. -/
theorem loop2_is_outfold (hasDesc hasType : List String)
    (annotations : List (String × String)) :
    (forIn annotations ([] : List (String × String)) fun entry r =>
        (if (entry.1 == "return" || entry.1 == "returns") = true then ForInStep.yield r
          else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
            ForInStep.yield (r ++ [("type " ++ entry.1, entry.2)])
          else ForInStep.yield r : Id _))
      = List.foldl (outStep hasDesc hasType) [] annotations := by
  suffices h : ∀ init, (forIn annotations init fun entry r =>
        (if (entry.1 == "return" || entry.1 == "returns") = true then ForInStep.yield r
          else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
            ForInStep.yield (r ++ [("type " ++ entry.1, entry.2)])
          else ForInStep.yield r : Id _))
      = List.foldl (outStep hasDesc hasType) init annotations by exact h []
  intro init
  induction annotations generalizing init with
  | nil => rfl
  | cons e es ih =>
      simp only [List.forIn_cons, List.foldl_cons]
      split_ifs with h1 h2 <;> simp only [outStep] <;>
        [rw [if_pos h1]; rw [if_neg h1, if_pos h2]; rw [if_neg h1, if_neg h2]] <;>
        exact ih _

/-- Bridge: given that the two loops refine to `classify fields` and to the
`outStep` fold, the imperative program's closing `match/if` on
`annotations.lookup "return"` returns exactly `augmentSpec fields annotations`. -/
theorem tail_match_eq (fields : List (List String))
    (annotations : List (String × String))
    (h1 : (forIn fields (⟨[], []⟩ : MProd (List String) (List String)) fun parts r =>
        (if (parts.headD "" == "param") = true then
            if (parts.length == 2) = true then
              ForInStep.yield ⟨r.fst ++ [parts.getD 1 ""], r.snd⟩
            else if parts.length > 2 then
              ForInStep.yield ⟨r.fst ++ [joinSp (parts.drop 2)], r.snd ++ [joinSp (parts.drop 2)]⟩
            else ForInStep.yield ⟨r.fst, r.snd⟩
          else if (parts.headD "" == "type") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ [joinSp (parts.drop 1)]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else ForInStep.yield ⟨r.fst, r.snd⟩ : Id _))
      = ⟨(classify fields).1, (classify fields).2⟩)
    (h2 : ∀ hasDesc hasType,
      (forIn annotations ([] : List (String × String)) fun entry r =>
          (if (entry.1 == "return" || entry.1 == "returns") = true then ForInStep.yield r
            else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
              ForInStep.yield (r ++ [("type " ++ entry.1, entry.2)])
            else ForInStep.yield r : Id _))
        = List.foldl (outStep hasDesc hasType) [] annotations) :
    implementation_augment fields annotations = augmentSpec fields annotations := by
  unfold implementation_augment
  simp only [Id.run, bind, pure, h1, h2, augmentSpec, classify]
  rfl

theorem correct_augment : ∀ (fields : List (List String))
    (annotations : List (String × String)),
    problem_spec_augment fields annotations
      (implementation_augment fields annotations) := by
  intro fields annotations
  show implementation_augment fields annotations = augmentSpec fields annotations
  exact tail_match_eq fields annotations (loop1_is_classify fields)
    (fun hasDesc hasType => loop2_is_outfold hasDesc hasType annotations)

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC POSTURE: problem_spec_augment := (result = augmentSpec fields annotations) is EXACT equality to a TOTAL COMPUTABLE deep model with ZERO axioms and NO opaque callees (the axioms region is comment-only; confirmed against mapping.md/refinement.md). Strongest soundness: a same-spec impl closes correct_augment iff it is extensionally = augmentSpec on the whole domain; with no axioms a false forall-equality cannot be closed without sorry.

SAME-SPEC: all 7 candidates verified same_spec=True via swebench_unified.markers.same_spec (lean backend); only the impl region was edited, axioms/pure/pre/post byte-identical.

ATTACKS (bash scripts/lean_verify.sh <f>), run concurrently <=4:
- atk_1 revert hunk 1 (drop 'returns' in classify loop) -> exit 1 REJECTED (this is the prepatch classification bug).
- atk_2 revert hunk 2 (drop 'returns' in backfill skip) -> exit 1 REJECTED.
- atk_3 partial-domain: param 2-token case no longer records described name -> exit 1 REJECTED.
- atk_4 off-by-one: 'type' marker join uses drop 2 not drop 1 -> exit 1 REJECTED.
- atk_5 boundary/output-text: appends ("type"++name) missing the space -> exit 1 REJECTED.
- atk_6 control-flow-effect: drops the trailing rtype append entirely (the reported F2P symptom) -> exit 1 REJECTED.
Every genuinely-wrong (extensionally != augmentSpec) impl FAILS verification. No wrong impl closes with clean axioms, so per protocol step 2 there is NO verifying wrong-impl requiring a faithful-patch resolve run (patches={} accordingly).

UNGROUNDED-ORACLE ECHO: atk_7/echo_pos sets implementation_augment := augmentSpec and closes correct_augment by rfl (exit 0; #print axioms => 'does not depend on any axioms'). Because augmentSpec is the GROUNDED total deep model (not an unconstrained oracle with a free result component), the echo is extensionally CORRECT; its faithful refined patch is behaviorally the gold widening and would RESOLVE. Per refinement.md it is a positive control, NOT a spec-weakness counterexample; submitting it in attacks would misrecord a correct impl. (atk_7.lean itself failed only because the stale imperative helper tail_match_eq no longer applies; the correct_augment goal closes by rfl, verified in echo_pos.lean exit 0.)

POSITIVE CONTROLS: pos_control.lean (gold) exit 0, #print axioms correct_augment = [propext, Quot.sound] (standard clean, no sorryAx/no custom _prop). echo_pos.lean exit 0, no axioms.

PREPATCH: prepatch.lean (both hunks reverted = literal pre-patch) exit 1 REJECTED -> prepatch_reproduced=True, G-DIFF holds.

COUNTEREXAMPLE MACHINE-CHECK: ce_check.lean proves augmentSpec [["returns"]] [("return","int")] = [("rtype","int")] by decide (exit 0), and classify [["returns"]] = (["return"],[]); reverted-hunk impls produce [] here.

REFINEMENT.MD AUDIT: every leg tagged R or I; NO A-consumed, NO A-reference, NO kind-3 legs. Axioms region declares nothing (comment only) consistent with mapping.md 'no opaque/axiom callee'; there is no A-leg deep-model->callee correspondence to validate (vacuous G-AX). model<->patch correspondence (hunk 1 classify-loop synonym, hunk 2 backfill-skip synonym, joinSp<->' '.join, set-add<->list-append with membership-only observable) checks out.

Verdict SOUND: >=6 distinct same-spec wrong impls (plus prepatch) all fail verification; no impl with a closing clean-axiom proof is extensionally wrong; the only clean-axiom closers are the gold and its extensionally-equal echo (a correct positive control).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
fields=[["returns"]], annotations=[("return","int")]: gold augmentSpec = [("rtype","int")] but any impl that drops hunk 1 (plural 'returns' not recognized in the classification loop) yields []; distinguished by `decide` (machine-checked in ce_check.lean, exit 0). This makes correct_augment a concretely FALSE equality for every reverted-hunk / wrong impl, unprovable with clean axioms.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The modeled procedure is
-- pure control flow over two abstract inputs: the parsed markers of a
-- documentation field list (each already split into whitespace-separated tokens
-- by the caller) and an ordered table mapping documented names to their declared
-- type text. Both are produced by the caller/environment; the decision logic the
-- procedure performs is modeled DEEPLY below. The proof agent may add `_prop`
-- axioms only if a proof obligation needs one.
-- axioms-end

-- pure-start
/-- Join a list of tokens with single spaces (the inverse of splitting a marker
on runs of whitespace). -/
def joinSp (parts : List String) : String := String.intercalate " " parts

/-- Classify one parsed field marker, updating the running pair of
"has a description" / "has a declared type" name collections.

`parts` is the marker split into whitespace-separated tokens. A marker headed by
`param` records a described name (and, in its three-token form, also a typed
name); a marker headed by `type` records a typed name; a marker headed by the
short OR the plural return keyword records that the result carries a description;
a marker headed by `rtype` records that the result carries a declared type. -/
def classifyStep (acc : List String × List String) (parts : List String) :
    List String × List String :=
  let (hasDesc, hasType) := acc
  let p0 := parts.headD ""
  if p0 == "param" then
    if parts.length == 2 then
      (hasDesc ++ [parts.getD 1 ""], hasType)
    else if parts.length > 2 then
      let name := joinSp (parts.drop 2)
      (hasDesc ++ [name], hasType ++ [name])
    else
      (hasDesc, hasType)
  else if p0 == "type" then
    (hasDesc, hasType ++ [joinSp (parts.drop 1)])
  else if p0 == "return" || p0 == "returns" then
    (hasDesc ++ ["return"], hasType)
  else if p0 == "rtype" then
    (hasDesc, hasType ++ ["return"])
  else
    (hasDesc, hasType)

/-- Fold `classifyStep` over every parsed marker of the field list. -/
def classify (fields : List (List String)) : List String × List String :=
  fields.foldl classifyStep ([], [])

/-- Process one entry of the name→type table, appending a freshly-built type
field when that name already carries a description but no declared type. The
short and plural return keywords are skipped here (the result's type is handled
separately, after the table is walked). -/
def outStep (hasDesc hasType : List String)
    (acc : List (String × String)) (entry : String × String) :
    List (String × String) :=
  let (name, ann) := entry
  if name == "return" || name == "returns" then
    acc
  else if hasDesc.contains name && !hasType.contains name then
    acc ++ [("type " ++ name, ann)]
  else
    acc

/-- The list of fields appended to a documentation field list when augmenting it
with declared-type information.

For every documented name (other than the result) that already carries a
description but no declared type, a `type <name>` field carrying its type text is
appended, in table order. Finally, if the result has declared type text and the
field list shows a result description but no declared result type, a single
`rtype` field carrying that text is appended. -/
def augmentSpec (fields : List (List String)) (annotations : List (String × String)) :
    List (String × String) :=
  let (hasDesc, hasType) := classify fields
  let typeFields := annotations.foldl (outStep hasDesc hasType) []
  match annotations.lookup "return" with
  | some ann =>
    if hasDesc.contains "return" && !hasType.contains "return" then
      typeFields ++ [("rtype", ann)]
    else
      typeFields
  | none => typeFields
-- pure-end

-- post-conditions-start
/-- Specification of augmenting a documentation field list with declared types.

`fields` is the field list, each marker pre-split into whitespace-separated
tokens. `annotations` is the ordered table mapping each documented name to its
declared type text (the result's type, when present, is stored under the name
`return`). `result` is the list of fields the procedure appends.

The result is exactly the appended-field list determined by the inputs: the
per-name `type <name>` fields followed by the optional `rtype` field, as
characterised by `augmentSpec`. -/
def problem_spec_augment (fields : List (List String))
    (annotations : List (String × String)) (result : List (String × String)) : Prop :=
  result = augmentSpec fields annotations
-- post-conditions-end

-- impl-start
def implementation_augment (fields : List (List String))
    (annotations : List (String × String)) : List (String × String) := Id.run do
  let mut hasDesc : List String := []
  let mut hasType : List String := []
  for parts in fields do
    let p0 := parts.headD ""
    if p0 == "param" then
      if parts.length == 2 then
        hasDesc := hasDesc ++ [parts.getD 1 ""]
      else if parts.length > 2 then
        let name := joinSp (parts.drop 2)
        hasDesc := hasDesc ++ [name]
        hasType := hasType ++ [name]
      else
        pure ()
    else if p0 == "type" then
      hasType := hasType ++ [joinSp (parts.drop 1)]
    else if p0 == "return" || p0 == "returns" then
      hasDesc := hasDesc ++ ["return"]
    else if p0 == "rtype" then
      hasType := hasType ++ ["return"]
    else
      pure ()
  let mut out : List (String × String) := []
  for entry in annotations do
    let (name, ann) := entry
    if name == "return" || name == "returns" then
      pure ()
    else if hasDesc.contains name && !hasType.contains name then
      out := out ++ [("type " ++ name, ann)]
    else
      pure ()
  match annotations.lookup "return" with
  | some ann =>
    if hasDesc.contains "return" && !hasType.contains "return" then
      out := out ++ [("rtype", ann)]
  | none => pure ()
  return out
-- impl-end


-- proof-start
/-- The first loop's body (the `p0`/length cascade producing the mutated
`(hasDesc, hasType)` pair) equals `classifyStep acc parts` for every input. -/
theorem classifyBodyEq (acc : List String × List String) (parts : List String) :
    (if (parts.headD "" == "param") = true then
        if (parts.length == 2) = true then (acc.1 ++ [parts.getD 1 ""], acc.2)
        else if parts.length > 2 then
          (acc.1 ++ [joinSp (parts.drop 2)], acc.2 ++ [joinSp (parts.drop 2)])
        else (acc.1, acc.2)
      else if (parts.headD "" == "type") = true then
        (acc.1, acc.2 ++ [joinSp (parts.drop 1)])
      else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
        (acc.1 ++ ["return"], acc.2)
      else if (parts.headD "" == "rtype") = true then (acc.1, acc.2 ++ ["return"])
      else (acc.1, acc.2)) = classifyStep acc parts := by
  simp only [classifyStep]

/-- The first `for parts in fields` loop (starting `⟨[],[]⟩`) computes
`classify fields`, rendered with the mutable-variable pair (`MProd`) the
`Id.run do` block actually uses. -/
theorem loop1_is_classify (fields : List (List String)) :
    (forIn fields (⟨[], []⟩ : MProd (List String) (List String)) fun parts r =>
        (if (parts.headD "" == "param") = true then
            if (parts.length == 2) = true then
              ForInStep.yield ⟨r.fst ++ [parts.getD 1 ""], r.snd⟩
            else if parts.length > 2 then
              ForInStep.yield ⟨r.fst ++ [joinSp (parts.drop 2)], r.snd ++ [joinSp (parts.drop 2)]⟩
            else ForInStep.yield ⟨r.fst, r.snd⟩
          else if (parts.headD "" == "type") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ [joinSp (parts.drop 1)]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else ForInStep.yield ⟨r.fst, r.snd⟩ : Id _))
      = ⟨(classify fields).1, (classify fields).2⟩ := by
  -- Step 1: the loop body always yields, so rewrite it to `ForInStep.yield (f r parts)`.
  have hbody :
      (fun (parts : List String) (r : MProd (List String) (List String)) =>
        (if (parts.headD "" == "param") = true then
            if (parts.length == 2) = true then
              ForInStep.yield ⟨r.fst ++ [parts.getD 1 ""], r.snd⟩
            else if parts.length > 2 then
              ForInStep.yield ⟨r.fst ++ [joinSp (parts.drop 2)], r.snd ++ [joinSp (parts.drop 2)]⟩
            else ForInStep.yield ⟨r.fst, r.snd⟩
          else if (parts.headD "" == "type") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ [joinSp (parts.drop 1)]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else ForInStep.yield ⟨r.fst, r.snd⟩ : Id _))
      = (fun parts r => ForInStep.yield
          (⟨(classifyStep (r.fst, r.snd) parts).1, (classifyStep (r.fst, r.snd) parts).2⟩
            : MProd (List String) (List String))) := by
    funext parts r
    simp only [classifyStep]
    split_ifs <;> rfl
  rw [hbody, List.forIn_yield_eq_foldl]
  -- Step 2: relate the MProd-valued foldl to the pair-valued `classify` foldl.
  have key : ∀ (fs : List (List String)) (r : MProd (List String) (List String)),
      (fs.foldl (fun r parts =>
          (⟨(classifyStep (r.fst, r.snd) parts).1, (classifyStep (r.fst, r.snd) parts).2⟩
            : MProd (List String) (List String))) r)
        = ⟨(fs.foldl classifyStep (r.fst, r.snd)).1, (fs.foldl classifyStep (r.fst, r.snd)).2⟩ := by
    intro fs
    induction fs with
    | nil => intro r; rfl
    | cons p ps ih => intro r; simp only [List.foldl_cons]; rw [ih]
  rw [key]
  rfl

/-- The second loop's body equals `outStep hasDesc hasType acc entry` for every
entry (the `return`/`returns` skip and the described-but-untyped append). -/
theorem outBodyEq (hasDesc hasType : List String)
    (acc : List (String × String)) (entry : String × String) :
    (if (entry.1 == "return" || entry.1 == "returns") = true then acc
      else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
        acc ++ [("type " ++ entry.1, entry.2)]
      else acc) = outStep hasDesc hasType acc entry := by
  simp only [outStep]

/-- The second `for entry in annotations` loop (starting `[]`), using the
`hasDesc`/`hasType` from loop 1, computes `annotations.foldl (outStep …) []`. -/
theorem loop2_is_outfold (hasDesc hasType : List String)
    (annotations : List (String × String)) :
    (forIn annotations ([] : List (String × String)) fun entry r =>
        (if (entry.1 == "return" || entry.1 == "returns") = true then ForInStep.yield r
          else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
            ForInStep.yield (r ++ [("type " ++ entry.1, entry.2)])
          else ForInStep.yield r : Id _))
      = List.foldl (outStep hasDesc hasType) [] annotations := by
  suffices h : ∀ init, (forIn annotations init fun entry r =>
        (if (entry.1 == "return" || entry.1 == "returns") = true then ForInStep.yield r
          else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
            ForInStep.yield (r ++ [("type " ++ entry.1, entry.2)])
          else ForInStep.yield r : Id _))
      = List.foldl (outStep hasDesc hasType) init annotations by exact h []
  intro init
  induction annotations generalizing init with
  | nil => rfl
  | cons e es ih =>
      simp only [List.forIn_cons, List.foldl_cons]
      split_ifs with h1 h2 <;> simp only [outStep] <;>
        [rw [if_pos h1]; rw [if_neg h1, if_pos h2]; rw [if_neg h1, if_neg h2]] <;>
        exact ih _

/-- Bridge: given that the two loops refine to `classify fields` and to the
`outStep` fold, the imperative program's closing `match/if` on
`annotations.lookup "return"` returns exactly `augmentSpec fields annotations`. -/
theorem tail_match_eq (fields : List (List String))
    (annotations : List (String × String))
    (h1 : (forIn fields (⟨[], []⟩ : MProd (List String) (List String)) fun parts r =>
        (if (parts.headD "" == "param") = true then
            if (parts.length == 2) = true then
              ForInStep.yield ⟨r.fst ++ [parts.getD 1 ""], r.snd⟩
            else if parts.length > 2 then
              ForInStep.yield ⟨r.fst ++ [joinSp (parts.drop 2)], r.snd ++ [joinSp (parts.drop 2)]⟩
            else ForInStep.yield ⟨r.fst, r.snd⟩
          else if (parts.headD "" == "type") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ [joinSp (parts.drop 1)]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else ForInStep.yield ⟨r.fst, r.snd⟩ : Id _))
      = ⟨(classify fields).1, (classify fields).2⟩)
    (h2 : ∀ hasDesc hasType,
      (forIn annotations ([] : List (String × String)) fun entry r =>
          (if (entry.1 == "return" || entry.1 == "returns") = true then ForInStep.yield r
            else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
              ForInStep.yield (r ++ [("type " ++ entry.1, entry.2)])
            else ForInStep.yield r : Id _))
        = List.foldl (outStep hasDesc hasType) [] annotations) :
    implementation_augment fields annotations = augmentSpec fields annotations := by
  unfold implementation_augment
  simp only [Id.run, bind, pure, h1, h2, augmentSpec, classify]
  rfl

theorem correct_augment : ∀ (fields : List (List String))
    (annotations : List (String × String)),
    problem_spec_augment fields annotations
      (implementation_augment fields annotations) := by
  intro fields annotations
  show implementation_augment fields annotations = augmentSpec fields annotations
  exact tail_match_eq fields annotations (loop1_is_classify fields)
    (fun hasDesc hasType => loop2_is_outfold hasDesc hasType annotations)

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC POSTURE: problem_spec_augment := (result = augmentSpec fields annotations) is EXACT equality to a TOTAL COMPUTABLE deep model with ZERO axioms and NO opaque callees (the axioms region is comment-only; confirmed against mapping.md/refinement.md). Strongest soundness: a same-spec impl closes correct_augment iff it is extensionally = augmentSpec on the whole domain; with no axioms a false forall-equality cannot be closed without sorry.

SAME-SPEC: all 7 candidates verified same_spec=True via swebench_unified.markers.same_spec (lean backend); only the impl region was edited, axioms/pure/pre/post byte-identical.

ATTACKS (bash scripts/lean_verify.sh <f>), run concurrently <=4:
- atk_1 revert hunk 1 (drop 'returns' in classify loop) -> exit 1 REJECTED (this is the prepatch classification bug).
- atk_2 revert hunk 2 (drop 'returns' in backfill skip) -> exit 1 REJECTED.
- atk_3 partial-domain: param 2-token case no longer records described name -> exit 1 REJECTED.
- atk_4 off-by-one: 'type' marker join uses drop 2 not drop 1 -> exit 1 REJECTED.
- atk_5 boundary/output-text: appends ("type"++name) missing the space -> exit 1 REJECTED.
- atk_6 control-flow-effect: drops the trailing rtype append entirely (the reported F2P symptom) -> exit 1 REJECTED.
Every genuinely-wrong (extensionally != augmentSpec) impl FAILS verification. No wrong impl closes with clean axioms, so per protocol step 2 there is NO verifying wrong-impl requiring a faithful-patch resolve run (patches={} accordingly).

UNGROUNDED-ORACLE ECHO: atk_7/echo_pos sets implementation_augment := augmentSpec and closes correct_augment by rfl (exit 0; #print axioms => 'does not depend on any axioms'). Because augmentSpec is the GROUNDED total deep model (not an unconstrained oracle with a free result component), the echo is extensionally CORRECT; its faithful refined patch is behaviorally the gold widening and would RESOLVE. Per refinement.md it is a positive control, NOT a spec-weakness counterexample; submitting it in attacks would misrecord a correct impl. (atk_7.lean itself failed only because the stale imperative helper tail_match_eq no longer applies; the correct_augment goal closes by rfl, verified in echo_pos.lean exit 0.)

POSITIVE CONTROLS: pos_control.lean (gold) exit 0, #print axioms correct_augment = [propext, Quot.sound] (standard clean, no sorryAx/no custom _prop). echo_pos.lean exit 0, no axioms.

PREPATCH: prepatch.lean (both hunks reverted = literal pre-patch) exit 1 REJECTED -> prepatch_reproduced=True, G-DIFF holds.

COUNTEREXAMPLE MACHINE-CHECK: ce_check.lean proves augmentSpec [["returns"]] [("return","int")] = [("rtype","int")] by decide (exit 0), and classify [["returns"]] = (["return"],[]); reverted-hunk impls produce [] here.

REFINEMENT.MD AUDIT: every leg tagged R or I; NO A-consumed, NO A-reference, NO kind-3 legs. Axioms region declares nothing (comment only) consistent with mapping.md 'no opaque/axiom callee'; there is no A-leg deep-model->callee correspondence to validate (vacuous G-AX). model<->patch correspondence (hunk 1 classify-loop synonym, hunk 2 backfill-skip synonym, joinSp<->' '.join, set-add<->list-append with membership-only observable) checks out.

Verdict SOUND: >=6 distinct same-spec wrong impls (plus prepatch) all fail verification; no impl with a closing clean-axiom proof is extensionally wrong; the only clean-axiom closers are the gold and its extensionally-equal echo (a correct positive control).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for sphinx-doc__sphinx-9673 lean bundle. TARGET: does the deep model augmentSpec agree with the real repo's post-patch augment_descriptions_with_types on all inputs?

BINDING CONFIRMED: base_commit 5fb51fb1467dc5eea7505402c3c5d9b378d3b441 present; the worktree file ext/autodoc/typehints.py:130-175 is the PRE-patch source (recognizes only 'return' in both loops). patch.diff == gold (meta.patch_equals_gold=true) applies the two synonym hunks: parts[0] in ('return','returns') and name in ('return','returns'). augmentSpec correctly models the POST-patch (fixed) function, as required.

INDEPENDENT DIFFERENTIAL TEST (did NOT trust the bundled conformance_check shadow): transcribed the Lean augmentSpec/classify/classifyStep/outStep/joinSp directly from Solution.lean and a faithful re-transcription of the real patched Python function (set-based has_description/has_type, OrderedDict iteration, trailing-rtype guard). Compared over 400,000 random inputs (0..6 fields; markers incl. bare 'param', 'param x', 'param x y', 'type', 'type return', 'return', 'returns', 'rtype', noise, empty; annotations as unique-key ordered dicts over names incl. 'return','returns','x','a b','self',''; types incl. '' and 'return') -> 0 divergences. Plus an EXHAUSTIVE enumeration of 3441 small-domain inputs (<=2 fields x <=2 unique-key annotation entries) -> 0 divergences.

EDGE CASES: empty marker list (Lean headD "" -> else branch; real Python re.split(' +',s) never yields [], so unreachable and non-divergent); annotations.lookup "return" (first match) vs Python 'return' in dict -> equivalent since annotations model an OrderedDict with unique keys. No divergence in the reachable domain.

PROOF GENUINE: scripts/lean_verify.sh Solution.lean exits 0 (only a Mathlib deprecation warning). #print axioms correct_augment = [propext, Quot.sound] -- clean, no sorryAx, no injected _prop axioms. The spec problem_spec_augment is EXACT equality (result = augmentSpec fields annotations) to a total computable model with no oracle and no free output component, so the clean-axiom proof forces extensional identity impl==augmentSpec on the whole domain.

NOTE on relaxed_leakage: G-LEAK is 'relaxed' (dispositioned plural-synonym discriminator absent from problem_statement). That is a G-LEAK/G-PANEL-3 concern, not a faithfulness/drift defect for panel_2; core soundness (G-VERIFY clean, G-DIFF prepatch diverges on plural-only docstring) re-confirmed. The spec is neither too strong nor drifted from the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-verified the relaxed-leakage disposition (not rubber-stamped).

### CORE SOUNDNESS (re-confirmed myself):
- same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers with the Lean backend tables: the axioms/pure/post-conditions spec regions are byte-identical; the fix lives ONLY in the impl region (prepatch reverts both gold hunks to the single 'return' spelling).
- Solution.lean compiles: lean_verify.sh exit 0, no sorry (only a non-fatal List.forIn_yield_eq_foldl deprecation warning).
- #print axioms correct_augment = [propext, Quot.sound] only — no sorryAx, no custom _prop axiom; the proof genuinely closes. axioms region empty.
- Spec pins result = augmentSpec fields annotations: exact equality to a total computable function, no oracle, no free output component.

### Leakage analysis
- The spec view DOES encode the gold discriminator: pure region classifyStep line 41 (p0 == "return" || p0 == "returns") and outStep line 60 (name == "return" || name == "returns"), plus docstrings naming 'the short OR the plural return keyword'. This is the two-spelling :returns: synonym = exactly the gold edit's two hunks (patch.diff: parts[0] in ('return','returns') and name in ('return','returns')).
- Scanned instance.json problem_statement directly: contains NO reST field markers :return: or :returns:. Its only 'Returns' token is the Google-style docstring SECTION HEADER 'Returns:' (in the reproduction docstring) — a homograph of, not identical to, the Napoleon-generated reST field marker :returns:. The :return:/:returns: synonym diagnosis lives only in hints_text/gold/test_patch (NOT counted as public here).
- A faithful spec (prepatch fails, no wrong impl passes) MUST name the plural synonym; a PS-only spec could model only the single 'return' spelling = pre-patch behavior, which would not reject the bug. Faithful + non-leaking is provably impossible — I re-derived this; no PS-only derivation of the synonym exists.

This is EXACTLY the documented, dispositioned facet: meta.json gates.G-LEAK.status='relaxed', in-bundle RELAXED_LEAKAGE.md, unavoidability argument present. The remaining spec content (param/type/rtype/back-fill modeling) is pre-existing function behavior, PS/general-knowledge derivable — not the fix. I found NO new leaking line beyond the dispositioned plural-synonym facet and NO broken disposition. Per the panel recording convention (a properly-dispositioned relaxed-leakage bundle records as pass/NO-LEAKAGE + note), the honest verdict is NO-LEAKAGE: the known dispositioned facet was re-confirmed and no leak beyond it was found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.

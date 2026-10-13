# P2 adversarial audit — sphinx-doc__sphinx-10449

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_or.lean`, `atk_order.lean`, `atk_partial.lean`, `atk_body.lean`, `atk_nogatetype.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -136,24 +136,10 @@
 -- impl-start
 def implementation_render_typehint_fields
     (existing : List DocField) (annotations : List (String × String))
-    (suppressTrivialReturn : Bool) : List DocField := Id.run do
-  let mut fields := existing
-  for entry in annotations do
-    let name := entry.1
-    let ann := entry.2
-    unless name == "return" do
-      if !(declaresType existing name) then
-        fields := fields ++ [⟨"type " ++ name, ann⟩]
-      if !(declaresParam existing name) then
-        fields := fields ++ [⟨"param " ++ name, ""⟩]
-  match lookupReturn annotations with
-  | some ann =>
-      if !(hasReturnField existing) then
-        if ann == "None" && suppressTrivialReturn then
-          return fields
-        fields := fields ++ [⟨"rtype", ann⟩]
-  | none => pure ()
-  return fields
+    (suppressTrivialReturn : Bool) : List DocField :=
+  existing
+    ++ genParamTypeFields existing annotations
+    ++ genReturnField existing annotations suppressTrivialReturn
 -- impl-end
 
 
@@ -164,49 +150,5 @@
       problem_spec_render_typehint_fields existing annotations suppressTrivialReturn
         (implementation_render_typehint_fields existing annotations suppressTrivialReturn) := by
   intro existing annotations suppressTrivialReturn
-  have loop : ∀ (anns : List (String × String)) (acc : List DocField),
-      (forIn (m := Id) anns acc (fun entry r =>
-        if (entry.1 == "return") = true then ForInStep.yield r
-        else if (!declaresType existing entry.1) = true then
-          if (!declaresParam existing entry.1) = true then
-            ForInStep.yield (r ++ [⟨"type " ++ entry.1, entry.2⟩] ++ [⟨"param " ++ entry.1, ""⟩])
-          else ForInStep.yield (r ++ [⟨"type " ++ entry.1, entry.2⟩])
-        else if (!declaresParam existing entry.1) = true then
-          ForInStep.yield (r ++ [⟨"param " ++ entry.1, ""⟩])
-        else ForInStep.yield r) : Id (List DocField))
-      = acc ++ genParamTypeFields existing anns := by
-    intro anns
-    induction anns with
-    | nil =>
-      intro acc
-      simp only [List.forIn_nil, genParamTypeFields, List.flatMap_nil, List.append_nil]
-      rfl
-    | cons p ps ih =>
-      intro acc
-      rw [List.forIn_cons]
-      simp only [genParamTypeFields, List.flatMap_cons]
-      split_ifs with hr ht hp <;>
-        simp only [ForInStep.yield, bind, Id.run] <;>
-        rw [ih] <;>
-        simp_all [genForName, genParamTypeFields]
-  simp only [problem_spec_render_typehint_fields, implementation_render_typehint_fields, Id.run,
-    bind, pure]
-  simp only [loop, genReturnField]
-  cases hlr : lookupReturn annotations with
-  | none => simp
-  | some ann =>
-    by_cases hrf : hasReturnField existing = true
-    · simp [hrf]
-    · simp only [hrf, Bool.false_eq_true, if_false, Bool.not_eq_true]
-      by_cases hsup : (ann == "None" && suppressTrivialReturn) = true
-      · simp only [hsup, if_true]
-        simp only [Bool.and_eq_true, beq_iff_eq] at hsup
-        obtain ⟨h1, h2⟩ := hsup
-        simp [h1, h2]
-      · simp only [hsup, if_false, Bool.not_eq_true]
-        simp only [Bool.and_eq_true, beq_iff_eq, not_and] at hsup
-        by_cases hn : ann = "None"
-        · simp [hn, hsup hn]
-        · simp [hn]
-
+  rfl
 -- proof-end
```

Attack 2 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -149,8 +149,6 @@
   match lookupReturn annotations with
   | some ann =>
       if !(hasReturnField existing) then
-        if ann == "None" && suppressTrivialReturn then
-          return fields
         fields := fields ++ [⟨"rtype", ann⟩]
   | none => pure ()
   return fields
```

Attack 3 — `atk_or.lean` → rejected (same spec, does not verify — good)

```diff
@@ -149,7 +149,7 @@
   match lookupReturn annotations with
   | some ann =>
       if !(hasReturnField existing) then
-        if ann == "None" && suppressTrivialReturn then
+        if ann == "None" || suppressTrivialReturn then
           return fields
         fields := fields ++ [⟨"rtype", ann⟩]
   | none => pure ()
```

Attack 4 — `atk_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -142,10 +142,10 @@
     let name := entry.1
     let ann := entry.2
     unless name == "return" do
+      if !(declaresParam existing name) then
+        fields := fields ++ [⟨"param " ++ name, ""⟩]
       if !(declaresType existing name) then
         fields := fields ++ [⟨"type " ++ name, ann⟩]
-      if !(declaresParam existing name) then
-        fields := fields ++ [⟨"param " ++ name, ""⟩]
   match lookupReturn annotations with
   | some ann =>
       if !(hasReturnField existing) then
```

Attack 5 — `atk_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -146,13 +146,6 @@
         fields := fields ++ [⟨"type " ++ name, ann⟩]
       if !(declaresParam existing name) then
         fields := fields ++ [⟨"param " ++ name, ""⟩]
-  match lookupReturn annotations with
-  | some ann =>
-      if !(hasReturnField existing) then
-        if ann == "None" && suppressTrivialReturn then
-          return fields
-        fields := fields ++ [⟨"rtype", ann⟩]
-  | none => pure ()
   return fields
 -- impl-end
 
```

Attack 6 — `atk_body.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,7 +151,7 @@
       if !(hasReturnField existing) then
         if ann == "None" && suppressTrivialReturn then
           return fields
-        fields := fields ++ [⟨"rtype", ann⟩]
+        fields := fields ++ [⟨"rtype", ""⟩]
   | none => pure ()
   return fields
 -- impl-end
```

Attack 7 — `atk_nogatetype.lean` → rejected (same spec, does not verify — good)

```diff
@@ -142,8 +142,7 @@
     let name := entry.1
     let ann := entry.2
     unless name == "return" do
-      if !(declaresType existing name) then
-        fields := fields ++ [⟨"type " ++ name, ann⟩]
+      fields := fields ++ [⟨"type " ++ name, ann⟩]
       if !(declaresParam existing name) then
         fields := fields ++ [⟨"param " ++ name, ""⟩]
   match lookupReturn annotations with
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Populating a structured field list with parameter- and return-type information
derived from a set of named type annotations.

The routine is given the fields already present in the list, a list of named
annotations (a name paired with its rendered type, in order; names are unique),
and a flag. For each annotation it appends, in order:

* a `type <name>` field carrying the rendered type, unless the existing fields
  already declare a type for that name; and
* an empty `param <name>` field, unless the existing fields already declare that
  parameter.

After the per-name fields, if the annotations carry an entry for the return
position and the existing fields do not already declare a return type, a single
`rtype` field carrying the return annotation is appended — EXCEPT that, when the
flag is set and the return annotation is the trivial unit annotation (`"None"`),
no return-type field is appended at all.

A field is observed only through its name text and its body text; both are
modeled as `String`. Existing fields are classified by tokenizing their name on
runs of spaces:

* `type <name>` declares a type for `<name>`;
* `param <name>` declares the parameter `<name>`;
* `param <kind> <name…>` declares both the parameter and a type for `<name…>`;
* `rtype …` declares that a return type is already present;
* a field that declares a type for, or the parameter named, the return
  position (`type return`, `param return`, `param <kind> return`) likewise
  counts as declaring the return type: the scan records all of these under
  the return name, so no return-type field is appended after any of them.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The field-name parsing, the
-- per-name type/param generation, and the return-type decision are all modeled
-- deeply (element-wise). The field-record constructors are pure data builders
-- whose output is taken as the modeled result.
-- axioms-end

-- pure-start
/-- A structured field, observed through its name text and body text. -/
structure DocField where
  name : String
  body : String
deriving Repr, DecidableEq

/-- Split a field name on runs of spaces (empty tokens dropped). -/
def tokenize (s : String) : List String :=
  (s.splitOn " ").filter (fun t => t ≠ "")

/-- Does field `f` declare a *type* for the name `nm`? True for a `type nm`
field or a 3+-token `param <kind> nm…` field. -/
def declaresTypeField (f : DocField) (nm : String) : Bool :=
  match tokenize f.name with
  | "type" :: rest => rest ≠ [] && " ".intercalate rest == nm
  | "param" :: _ :: p :: ps => " ".intercalate (p :: ps) == nm
  | _ => false

/-- Does field `f` declare the *parameter* `nm`? True for a 2-token `param nm`
field or a 3+-token `param <kind> nm…` field. -/
def declaresParamField (f : DocField) (nm : String) : Bool :=
  match tokenize f.name with
  | "param" :: p :: [] => p == nm
  | "param" :: _ :: p :: ps => " ".intercalate (p :: ps) == nm
  | _ => false

/-- Does field `f` declare that a return type is already present? True for an
`rtype …` field, and also for any field that declares a type for, or the
parameter named, the return position (`type return`, `param return`,
`param <kind> return`) — the scan records all of these under the return name. -/
def isReturnField (f : DocField) : Bool :=
  match tokenize f.name with
  | "rtype" :: _ => true
  | _ => declaresTypeField f "return" || declaresParamField f "return"

/-- Some existing field already declares a type for `nm`. -/
def declaresType (existing : List DocField) (nm : String) : Bool :=
  existing.any (fun f => declaresTypeField f nm)

/-- Some existing field already declares the parameter `nm`. -/
def declaresParam (existing : List DocField) (nm : String) : Bool :=
  existing.any (fun f => declaresParamField f nm)

/-- Some existing field already declares a return type. -/
def hasReturnField (existing : List DocField) : Bool :=
  existing.any isReturnField

/-- The return annotation carried by `annotations`, if any. -/
def lookupReturn (annotations : List (String × String)) : Option String :=
  (annotations.find? (fun p => p.1 == "return")).map Prod.snd

/-- Fields generated for one annotation `(name, ann)` (return entries skipped by
the caller): a `type` field unless a type is already declared, then a `param`
field unless the parameter is already declared. -/
def genForName (existing : List DocField) (name ann : String) : List DocField :=
  (if declaresType existing name then [] else [⟨"type " ++ name, ann⟩]) ++
  (if declaresParam existing name then [] else [⟨"param " ++ name, ""⟩])

/-- All per-name fields generated for `annotations` (the return entry, if any, is
skipped here — it is handled by the return-type rule). -/
def genParamTypeFields (existing : List DocField)
    (annotations : List (String × String)) : List DocField :=
  annotations.flatMap (fun p =>
    if p.1 == "return" then [] else genForName existing p.1 p.2)

/-- The return-type field, if one is to be appended: only when the annotations
carry a return entry, the existing fields declare no return type, and the entry
is not suppressed (flag set and the annotation is the trivial unit `"None"`). -/
def genReturnField (existing : List DocField)
    (annotations : List (String × String)) (suppressTrivialReturn : Bool) : List DocField :=
  match lookupReturn annotations with
  | some ann =>
      if hasReturnField existing then []
      else if ann == "None" && suppressTrivialReturn then []
      else [⟨"rtype", ann⟩]
  | none => []
-- pure-end

-- post-conditions-start
/-- The resulting field list is the existing fields, followed by the generated
per-name type/param fields (in annotation order), followed by the return-type
field if the return rule produces one. -/
def problem_spec_render_typehint_fields
    (existing : List DocField) (annotations : List (String × String))
    (suppressTrivialReturn : Bool) (result : List DocField) : Prop :=
  result =
    existing
      ++ genParamTypeFields existing annotations
      ++ genReturnField existing annotations suppressTrivialReturn
-- post-conditions-end

-- impl-start
def implementation_render_typehint_fields
    (existing : List DocField) (annotations : List (String × String))
    (suppressTrivialReturn : Bool) : List DocField := Id.run do
  let mut fields := existing
  for entry in annotations do
    let name := entry.1
    let ann := entry.2
    unless name == "return" do
      if !(declaresType existing name) then
        fields := fields ++ [⟨"type " ++ name, ann⟩]
      if !(declaresParam existing name) then
        fields := fields ++ [⟨"param " ++ name, ""⟩]
  match lookupReturn annotations with
  | some ann =>
      if !(hasReturnField existing) then
        if ann == "None" && suppressTrivialReturn then
          return fields
        fields := fields ++ [⟨"rtype", ann⟩]
  | none => pure ()
  return fields
-- impl-end


-- proof-start
theorem correct_render_typehint_fields :
    ∀ (existing : List DocField) (annotations : List (String × String))
      (suppressTrivialReturn : Bool),
      problem_spec_render_typehint_fields existing annotations suppressTrivialReturn
        (implementation_render_typehint_fields existing annotations suppressTrivialReturn) := by
  intro existing annotations suppressTrivialReturn
  have loop : ∀ (anns : List (String × String)) (acc : List DocField),
      (forIn (m := Id) anns acc (fun entry r =>
        if (entry.1 == "return") = true then ForInStep.yield r
        else if (!declaresType existing entry.1) = true then
          if (!declaresParam existing entry.1) = true then
            ForInStep.yield (r ++ [⟨"type " ++ entry.1, entry.2⟩] ++ [⟨"param " ++ entry.1, ""⟩])
          else ForInStep.yield (r ++ [⟨"type " ++ entry.1, entry.2⟩])
        else if (!declaresParam existing entry.1) = true then
          ForInStep.yield (r ++ [⟨"param " ++ entry.1, ""⟩])
        else ForInStep.yield r) : Id (List DocField))
      = acc ++ genParamTypeFields existing anns := by
    intro anns
    induction anns with
    | nil =>
      intro acc
      simp only [List.forIn_nil, genParamTypeFields, List.flatMap_nil, List.append_nil]
      rfl
    | cons p ps ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [genParamTypeFields, List.flatMap_cons]
      split_ifs with hr ht hp <;>
        simp only [ForInStep.yield, bind, Id.run] <;>
        rw [ih] <;>
        simp_all [genForName, genParamTypeFields]
  simp only [problem_spec_render_typehint_fields, implementation_render_typehint_fields, Id.run,
    bind, pure]
  simp only [loop, genReturnField]
  cases hlr : lookupReturn annotations with
  | none => simp
  | some ann =>
    by_cases hrf : hasReturnField existing = true
    · simp [hrf]
    · simp only [hrf, Bool.false_eq_true, if_false, Bool.not_eq_true]
      by_cases hsup : (ann == "None" && suppressTrivialReturn) = true
      · simp only [hsup, if_true]
        simp only [Bool.and_eq_true, beq_iff_eq] at hsup
        obtain ⟨h1, h2⟩ := hsup
        simp [h1, h2]
      · simp only [hsup, if_false, Bool.not_eq_true]
        simp only [Bool.and_eq_true, beq_iff_eq, not_and] at hsup
        by_cases hn : ann = "None"
        · simp [hn, hsup hn]
        · simp [hn]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The postcondition problem_spec_render_typehint_fields is an EXACT functional equality: result = existing ++ genParamTypeFields existing annotations ++ genReturnField existing annotations suppressTrivialReturn. This pins `result` uniquely for every input, so only impls extensionally equal to the model can satisfy correct_*.

Setup: same_spec True for pos_control and all 7 attacks (verified via swebench_unified.markers.same_spec, lean backend). same_spec elides BOTH impl and proof regions, so attacks freely rewrite impl+proof while keeping imports/axioms/pure/post-conditions byte-identical.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <file>`, from project root):

1. atk_echo (ungrounded-oracle echo): impl literally returns the spec RHS; proof by `rfl`. lean_verify EXIT 0 (verifies, no sorry). `#print axioms correct_render_typehint_fields` => [propext] (clean; no sorryAx/custom axioms). Per protocol MUST materialize faithful patch + run_resolve. Its faithful patch is behaviorally the gold patch (echo of the spec RHS = gold-correct behavior). RESOLVE RESULT: RESOLVED=true. Ran the official harness (python -m swebench_unified.run_evaluation, image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-10449:latest); report at experiments/logs/run_evaluation/sbu-audit-echo-dbg/.../report.json shows resolved:true, FAIL_TO_PASS test_autodoc_typehints_description_with_documented_init success, all 30 PASS_TO_PASS success. Copy saved NOTE: run_resolve() wrapper first reported completed=False because the swebench harness crashes in its post-run clean_images() step (docker ImageNotFound 404 on a sha digest — a benign concurrent image-cleanup race) AFTER writing the report; a bare re-run of run_evaluation confirmed 'All instances run.' + resolved:true. A resolving same-spec echo is NOT a weakness (G-PANEL-1/G-EQ policy: candidate breaks the spec only if its faithful patch does NOT resolve). Since it resolves => spec not broken by this attack.

2. atk_prepatch (the pre-fix bug: suppress flag ignored, rtype always appended): reuses the gold proof. lean_verify EXIT 1 — `error: unsolved goals` on case pos with h1: ann="None", h2: suppressTrivialReturn=true, goal False. Correctly FAILS to verify (⇒ prepatch reproduced; matches recorded G-DIFF fail on Solution_prepatch.lean).

3. atk_or (boundary: `ann=="None" || suppressTrivialReturn` instead of &&): lean_verify EXIT 1 — unsolved goals in both case pos and case neg. Correctly FAILS.

4. atk_order (control-flow-effect: emit param field BEFORE type field): lean_verify EXIT 1. Correctly FAILS (order in list differs from model).

5. atk_partial (partial-domain: drop the entire return-type handling): lean_verify EXIT 1. Correctly FAILS.

6. atk_body (boundary: rtype field carries "" body instead of the return annotation): lean_verify EXIT 1. Correctly FAILS.

7. atk_nogatetype (control-flow-effect: emit `type <name>` field even when a type is already declared — drop the declaresType guard): lean_verify EXIT 1. Correctly FAILS.

Positive control (bundle Solution.lean, unmodified): lean_verify EXIT 0; `#print axioms` => [propext, Quot.sound] (clean).

RESULT: 6 of 7 wrong-shaped attacks FAIL to verify (exact-equality spec rejects them). The only attack that closes is the oracle echo, whose faithful patch RESOLVES — so no impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds.

REFINEMENT.MD AUDIT: meta.json confirms axioms=[], deep_model_references=[], opaque_callees=[]. All 8 legs are tagged R or R/I (no A-legs, so no callee↔axiom correspondence can fail; no kind-3 inexpressible legs). The deep model (tokenize / declaresType / declaresParam / hasReturnField / isReturnField / genReturnField) faithfully mirrors the Python scan-loop over the `arguments` dict per mapping.md (including the `type return`/`param return` => 'return' in arguments equivalence). R/I legs are additionally covered by G-CONF (100000 inputs, seed 10449, status ok). No weakness in the refinement.

VERDICT: SOUND (>=5 distinct attacks run; the one closing attack resolves).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_or.lean`, `atk_order.lean`, `atk_partial.lean`, `atk_body.lean`, `atk_nogatetype.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_or.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_order.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_partial.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_body.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_nogatetype.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Populating a structured field list with parameter- and return-type information
derived from a set of named type annotations.

The routine is given the fields already present in the list, a list of named
annotations (a name paired with its rendered type, in order; names are unique),
and a flag. For each annotation it appends, in order:

* a `type <name>` field carrying the rendered type, unless the existing fields
  already declare a type for that name; and
* an empty `param <name>` field, unless the existing fields already declare that
  parameter.

After the per-name fields, if the annotations carry an entry for the return
position and the existing fields do not already declare a return type, a single
`rtype` field carrying the return annotation is appended — EXCEPT that, when the
flag is set and the return annotation is the trivial unit annotation (`"None"`),
no return-type field is appended at all.

A field is observed only through its name text and its body text; both are
modeled as `String`. Existing fields are classified by tokenizing their name on
runs of spaces:

* `type <name>` declares a type for `<name>`;
* `param <name>` declares the parameter `<name>`;
* `param <kind> <name…>` declares both the parameter and a type for `<name…>`;
* `rtype …` declares that a return type is already present;
* a field that declares a type for, or the parameter named, the return
  position (`type return`, `param return`, `param <kind> return`) likewise
  counts as declaring the return type: the scan records all of these under
  the return name, so no return-type field is appended after any of them.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The field-name parsing, the
-- per-name type/param generation, and the return-type decision are all modeled
-- deeply (element-wise). The field-record constructors are pure data builders
-- whose output is taken as the modeled result.
-- axioms-end

-- pure-start
/-- A structured field, observed through its name text and body text. -/
structure DocField where
  name : String
  body : String
deriving Repr, DecidableEq

/-- Split a field name on runs of spaces (empty tokens dropped). -/
def tokenize (s : String) : List String :=
  (s.splitOn " ").filter (fun t => t ≠ "")

/-- Does field `f` declare a *type* for the name `nm`? True for a `type nm`
field or a 3+-token `param <kind> nm…` field. -/
def declaresTypeField (f : DocField) (nm : String) : Bool :=
  match tokenize f.name with
  | "type" :: rest => rest ≠ [] && " ".intercalate rest == nm
  | "param" :: _ :: p :: ps => " ".intercalate (p :: ps) == nm
  | _ => false

/-- Does field `f` declare the *parameter* `nm`? True for a 2-token `param nm`
field or a 3+-token `param <kind> nm…` field. -/
def declaresParamField (f : DocField) (nm : String) : Bool :=
  match tokenize f.name with
  | "param" :: p :: [] => p == nm
  | "param" :: _ :: p :: ps => " ".intercalate (p :: ps) == nm
  | _ => false

/-- Does field `f` declare that a return type is already present? True for an
`rtype …` field, and also for any field that declares a type for, or the
parameter named, the return position (`type return`, `param return`,
`param <kind> return`) — the scan records all of these under the return name. -/
def isReturnField (f : DocField) : Bool :=
  match tokenize f.name with
  | "rtype" :: _ => true
  | _ => declaresTypeField f "return" || declaresParamField f "return"

/-- Some existing field already declares a type for `nm`. -/
def declaresType (existing : List DocField) (nm : String) : Bool :=
  existing.any (fun f => declaresTypeField f nm)

/-- Some existing field already declares the parameter `nm`. -/
def declaresParam (existing : List DocField) (nm : String) : Bool :=
  existing.any (fun f => declaresParamField f nm)

/-- Some existing field already declares a return type. -/
def hasReturnField (existing : List DocField) : Bool :=
  existing.any isReturnField

/-- The return annotation carried by `annotations`, if any. -/
def lookupReturn (annotations : List (String × String)) : Option String :=
  (annotations.find? (fun p => p.1 == "return")).map Prod.snd

/-- Fields generated for one annotation `(name, ann)` (return entries skipped by
the caller): a `type` field unless a type is already declared, then a `param`
field unless the parameter is already declared. -/
def genForName (existing : List DocField) (name ann : String) : List DocField :=
  (if declaresType existing name then [] else [⟨"type " ++ name, ann⟩]) ++
  (if declaresParam existing name then [] else [⟨"param " ++ name, ""⟩])

/-- All per-name fields generated for `annotations` (the return entry, if any, is
skipped here — it is handled by the return-type rule). -/
def genParamTypeFields (existing : List DocField)
    (annotations : List (String × String)) : List DocField :=
  annotations.flatMap (fun p =>
    if p.1 == "return" then [] else genForName existing p.1 p.2)

/-- The return-type field, if one is to be appended: only when the annotations
carry a return entry, the existing fields declare no return type, and the entry
is not suppressed (flag set and the annotation is the trivial unit `"None"`). -/
def genReturnField (existing : List DocField)
    (annotations : List (String × String)) (suppressTrivialReturn : Bool) : List DocField :=
  match lookupReturn annotations with
  | some ann =>
      if hasReturnField existing then []
      else if ann == "None" && suppressTrivialReturn then []
      else [⟨"rtype", ann⟩]
  | none => []
-- pure-end

-- post-conditions-start
/-- The resulting field list is the existing fields, followed by the generated
per-name type/param fields (in annotation order), followed by the return-type
field if the return rule produces one. -/
def problem_spec_render_typehint_fields
    (existing : List DocField) (annotations : List (String × String))
    (suppressTrivialReturn : Bool) (result : List DocField) : Prop :=
  result =
    existing
      ++ genParamTypeFields existing annotations
      ++ genReturnField existing annotations suppressTrivialReturn
-- post-conditions-end

-- impl-start
def implementation_render_typehint_fields
    (existing : List DocField) (annotations : List (String × String))
    (suppressTrivialReturn : Bool) : List DocField := Id.run do
  let mut fields := existing
  for entry in annotations do
    let name := entry.1
    let ann := entry.2
    unless name == "return" do
      if !(declaresType existing name) then
        fields := fields ++ [⟨"type " ++ name, ann⟩]
      if !(declaresParam existing name) then
        fields := fields ++ [⟨"param " ++ name, ""⟩]
  match lookupReturn annotations with
  | some ann =>
      if !(hasReturnField existing) then
        if ann == "None" && suppressTrivialReturn then
          return fields
        fields := fields ++ [⟨"rtype", ann⟩]
  | none => pure ()
  return fields
-- impl-end


-- proof-start
theorem correct_render_typehint_fields :
    ∀ (existing : List DocField) (annotations : List (String × String))
      (suppressTrivialReturn : Bool),
      problem_spec_render_typehint_fields existing annotations suppressTrivialReturn
        (implementation_render_typehint_fields existing annotations suppressTrivialReturn) := by
  intro existing annotations suppressTrivialReturn
  have loop : ∀ (anns : List (String × String)) (acc : List DocField),
      (forIn (m := Id) anns acc (fun entry r =>
        if (entry.1 == "return") = true then ForInStep.yield r
        else if (!declaresType existing entry.1) = true then
          if (!declaresParam existing entry.1) = true then
            ForInStep.yield (r ++ [⟨"type " ++ entry.1, entry.2⟩] ++ [⟨"param " ++ entry.1, ""⟩])
          else ForInStep.yield (r ++ [⟨"type " ++ entry.1, entry.2⟩])
        else if (!declaresParam existing entry.1) = true then
          ForInStep.yield (r ++ [⟨"param " ++ entry.1, ""⟩])
        else ForInStep.yield r) : Id (List DocField))
      = acc ++ genParamTypeFields existing anns := by
    intro anns
    induction anns with
    | nil =>
      intro acc
      simp only [List.forIn_nil, genParamTypeFields, List.flatMap_nil, List.append_nil]
      rfl
    | cons p ps ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [genParamTypeFields, List.flatMap_cons]
      split_ifs with hr ht hp <;>
        simp only [ForInStep.yield, bind, Id.run] <;>
        rw [ih] <;>
        simp_all [genForName, genParamTypeFields]
  simp only [problem_spec_render_typehint_fields, implementation_render_typehint_fields, Id.run,
    bind, pure]
  simp only [loop, genReturnField]
  cases hlr : lookupReturn annotations with
  | none => simp
  | some ann =>
    by_cases hrf : hasReturnField existing = true
    · simp [hrf]
    · simp only [hrf, Bool.false_eq_true, if_false, Bool.not_eq_true]
      by_cases hsup : (ann == "None" && suppressTrivialReturn) = true
      · simp only [hsup, if_true]
        simp only [Bool.and_eq_true, beq_iff_eq] at hsup
        obtain ⟨h1, h2⟩ := hsup
        simp [h1, h2]
      · simp only [hsup, if_false, Bool.not_eq_true]
        simp only [Bool.and_eq_true, beq_iff_eq, not_and] at hsup
        by_cases hn : ann = "None"
        · simp [hn, hsup hn]
        · simp [hn]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The postcondition problem_spec_render_typehint_fields is an EXACT functional equality: result = existing ++ genParamTypeFields existing annotations ++ genReturnField existing annotations suppressTrivialReturn. This pins `result` uniquely for every input, so only impls extensionally equal to the model can satisfy correct_*.

Setup: same_spec True for pos_control and all 7 attacks (verified via swebench_unified.markers.same_spec, lean backend). same_spec elides BOTH impl and proof regions, so attacks freely rewrite impl+proof while keeping imports/axioms/pure/post-conditions byte-identical.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <file>`, from project root):

1. atk_echo (ungrounded-oracle echo): impl literally returns the spec RHS; proof by `rfl`. lean_verify EXIT 0 (verifies, no sorry). `#print axioms correct_render_typehint_fields` => [propext] (clean; no sorryAx/custom axioms). Per protocol MUST materialize faithful patch + run_resolve. Its faithful patch is behaviorally the gold patch (echo of the spec RHS = gold-correct behavior). RESOLVE RESULT: RESOLVED=true. Ran the official harness (python -m swebench_unified.run_evaluation, image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-10449:latest); report at experiments/logs/run_evaluation/sbu-audit-echo-dbg/.../report.json shows resolved:true, FAIL_TO_PASS test_autodoc_typehints_description_with_documented_init success, all 30 PASS_TO_PASS success. Copy saved NOTE: run_resolve() wrapper first reported completed=False because the swebench harness crashes in its post-run clean_images() step (docker ImageNotFound 404 on a sha digest — a benign concurrent image-cleanup race) AFTER writing the report; a bare re-run of run_evaluation confirmed 'All instances run.' + resolved:true. A resolving same-spec echo is NOT a weakness (G-PANEL-1/G-EQ policy: candidate breaks the spec only if its faithful patch does NOT resolve). Since it resolves => spec not broken by this attack.

2. atk_prepatch (the pre-fix bug: suppress flag ignored, rtype always appended): reuses the gold proof. lean_verify EXIT 1 — `error: unsolved goals` on case pos with h1: ann="None", h2: suppressTrivialReturn=true, goal False. Correctly FAILS to verify (⇒ prepatch reproduced; matches recorded G-DIFF fail on Solution_prepatch.lean).

3. atk_or (boundary: `ann=="None" || suppressTrivialReturn` instead of &&): lean_verify EXIT 1 — unsolved goals in both case pos and case neg. Correctly FAILS.

4. atk_order (control-flow-effect: emit param field BEFORE type field): lean_verify EXIT 1. Correctly FAILS (order in list differs from model).

5. atk_partial (partial-domain: drop the entire return-type handling): lean_verify EXIT 1. Correctly FAILS.

6. atk_body (boundary: rtype field carries "" body instead of the return annotation): lean_verify EXIT 1. Correctly FAILS.

7. atk_nogatetype (control-flow-effect: emit `type <name>` field even when a type is already declared — drop the declaresType guard): lean_verify EXIT 1. Correctly FAILS.

Positive control (bundle Solution.lean, unmodified): lean_verify EXIT 0; `#print axioms` => [propext, Quot.sound] (clean).

RESULT: 6 of 7 wrong-shaped attacks FAIL to verify (exact-equality spec rejects them). The only attack that closes is the oracle echo, whose faithful patch RESOLVES — so no impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds.

REFINEMENT.MD AUDIT: meta.json confirms axioms=[], deep_model_references=[], opaque_callees=[]. All 8 legs are tagged R or R/I (no A-legs, so no callee↔axiom correspondence can fail; no kind-3 inexpressible legs). The deep model (tokenize / declaresType / declaresParam / hasReturnField / isReturnField / genReturnField) faithfully mirrors the Python scan-loop over the `arguments` dict per mapping.md (including the `type return`/`param return` => 'return' in arguments equivalence). R/I legs are additionally covered by G-CONF (100000 inputs, seed 10449, status ok). No weakness in the refinement.

VERDICT: SOUND (>=5 distinct attacks run; the one closing attack resolves).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verification: (1) same_spec(Solution, Solution_prepatch)=True -> spec region byte-identical. (2) lean_verify.sh exit 0, no sorry. (3) #print axioms correct_render_typehint_fields => [propext, Quot.sound], no sorryAx -> proof genuine. (4) Real callee obtained from base_commit 36367765 + gold patch.diff; standalone patched modify_field_list fuzzed vs the conformance shadow. Root cause of out-of-domain diffs: real uses re.split(' +', field_name) reading parts[0] without dropping empty leading/trailing tokens, vs model tokenize which filters empties; and model emits fields for empty annotation keys. Both cases are explicitly and correctly excluded by the mapping.md 'Domain note' (field names have no leading/trailing spaces; annotation keys are unique Python identifiers). Within the reachable domain the modeled function agrees with the real callee on every input; G-CONF (100K, seed 10449) passes. Spec is neither too strong nor drifted. FAITHFUL.

Counterexample / evidence:

```
In-domain: NONE. 500K adversarial domain-restricted inputs (realistic identifier names incl. 'return', multi-word param names, rtype/raises/returns fields, suppress 50/50) => 0 disagreements. Out-of-domain near-miss: existing=[('  type x','')], annotations=[('x','str')], suppress=False -> real=[('  type x',''),('type x','str'),('param x','')], shadow=[('  type x',''),('param x','')]; unreachable because docutils never produces a field name with a leading space.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: passed=True, hard_failures=[]). same_spec(Solution, Solution_prepatch)=True — the judged spec view is the shared spec region. No relaxation flag in play.

Checks: (1) No diff markers, no patched file path (sphinx/ext/autodoc/typehints.py), no module path, no reproduced gold-patch line in the spec view. (2) Gold repo symbols {modify_field_list, suppress_rtype, merge_typehints} do NOT appear; the spec uses de-narrated aliases render_typehint_fields / suppressTrivialReturn (confirmed by _patch_changed_symbols collision check = clean). (3) No bug/fix narration in comments.

Semantic check vs public problem_statement (NOT hints_text): the problem_statement already discloses the correct behavior fully — autodoc_typehints='description' wrongly renders a return type for a class whose __init__ returns -> None, and 'I expected there to be no return type listed for the class.' The spec-view docstring says only that 'when the flag is set and the return annotation is the trivial unit annotation ("None"), no return-type field is appended' — a faithful spec of behavior already public in the task, not a disclosure beyond it. The caller-side detail tying the flag to objtype=='class' lives only in refinement.md/mapping.md (auditor docs, not the solver-visible spec view); the spec view just says 'and a flag.' No leakage of gold-edit localization or mechanism beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — sphinx-doc__sphinx-11445

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_ignore_preamble.lean`, `atk_3_no_trailing_blank.lean`, `atk_4_no_header_sep.lean`, `atk_5_off_by_one.lean`, `atk_6_count_all.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,10 +105,21 @@
     (body preamble : List String) : List String := Id.run do
   if preamble = [] then
     return body
-  -- count the consecutive leading field lines
+  -- Pre-patch loose classifier: accepts any `:word:` head regardless of trailing text.
+  let looseFieldHead : List Char → Bool := fun cs =>
+    match cs with
+    | (':' :: rest) =>
+      let rec scan : List Char → Bool → Bool
+        | [], _ => false
+        | (c :: cs'), seen =>
+          if c == ':' then seen
+          else if c.isAlphanum || c == '_' then scan cs' true
+          else false
+      scan rest false
+    | _ => false
   let mut pos := 0
   for line in body do
-    if isFieldLine line.toList then
+    if looseFieldHead line.toList then
       pos := pos + 1
     else
       break
@@ -119,39 +130,13 @@
 -- impl-end
 
 -- proof-start
-/-- The `for … break` loop counting leading field lines equals the
-`takeWhile`-based `leadingFieldCount`, generalized over the accumulator so the
-induction goes through. -/
-theorem loop_helper (body : List String) (init : Nat) :
-    Id.run (forIn body init (fun line r =>
-      if isFieldLine line.toList = true then
-        (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-      else pure (ForInStep.done r)))
-    = init + (body.takeWhile (fun l => isFieldLine l.toList)).length := by
-  induction body generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isFieldLine a.toList = true
-    · simp only [h, if_true, List.takeWhile_cons]
-      rw [ih, List.length_cons]
-      omega
-    · simp only [h, List.takeWhile_cons, if_false, List.length_nil, Nat.add_zero,
-        Bool.false_eq_true]
-
 theorem correct_placePreamble : ∀ (body preamble : List String),
     problem_spec_placePreamble body preamble
       (implementation_placePreamble body preamble) := by
   intro body preamble
   unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec
-  by_cases hp : preamble = []
-  · simp only [hp, if_true, Id.run]; rfl
-  · have hloop : Id.run (forIn body 0 (fun line r =>
-        if isFieldLine line.toList = true then
-          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-        else pure (ForInStep.done r))) = leadingFieldCount body := by
-      rw [loop_helper, leadingFieldCount, Nat.zero_add]
-    simp only [hp, if_false, Id.run, bind, pure] at *
-    rw [hloop]
+  simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (by_cases hp : preamble = [] <;> simp_all <;> rfl)
 -- proof-end
```

Attack 2 — `atk_2_ignore_preamble.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,56 +102,18 @@
 
 -- impl-start
 def implementation_placePreamble
-    (body preamble : List String) : List String := Id.run do
-  if preamble = [] then
-    return body
-  -- count the consecutive leading field lines
-  let mut pos := 0
-  for line in body do
-    if isFieldLine line.toList then
-      pos := pos + 1
-    else
-      break
-  let head := body.take pos
-  let tail := body.drop pos
-  let sep := if pos > 0 then ([""] : List String) else []
-  return head ++ sep ++ preamble ++ [""] ++ tail
+    (body preamble : List String) : List String :=
+  body
 -- impl-end
 
 -- proof-start
-/-- The `for … break` loop counting leading field lines equals the
-`takeWhile`-based `leadingFieldCount`, generalized over the accumulator so the
-induction goes through. -/
-theorem loop_helper (body : List String) (init : Nat) :
-    Id.run (forIn body init (fun line r =>
-      if isFieldLine line.toList = true then
-        (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-      else pure (ForInStep.done r)))
-    = init + (body.takeWhile (fun l => isFieldLine l.toList)).length := by
-  induction body generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isFieldLine a.toList = true
-    · simp only [h, if_true, List.takeWhile_cons]
-      rw [ih, List.length_cons]
-      omega
-    · simp only [h, List.takeWhile_cons, if_false, List.length_nil, Nat.add_zero,
-        Bool.false_eq_true]
-
 theorem correct_placePreamble : ∀ (body preamble : List String),
     problem_spec_placePreamble body preamble
       (implementation_placePreamble body preamble) := by
   intro body preamble
   unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec
-  by_cases hp : preamble = []
-  · simp only [hp, if_true, Id.run]; rfl
-  · have hloop : Id.run (forIn body 0 (fun line r =>
-        if isFieldLine line.toList = true then
-          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-        else pure (ForInStep.done r))) = leadingFieldCount body := by
-      rw [loop_helper, leadingFieldCount, Nat.zero_add]
-    simp only [hp, if_false, Id.run, bind, pure] at *
-    rw [hloop]
+  simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (by_cases hp : preamble = [] <;> simp_all <;> rfl)
 -- proof-end
```

Attack 3 — `atk_3_no_trailing_blank.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,56 +102,21 @@
 
 -- impl-start
 def implementation_placePreamble
-    (body preamble : List String) : List String := Id.run do
-  if preamble = [] then
-    return body
-  -- count the consecutive leading field lines
-  let mut pos := 0
-  for line in body do
-    if isFieldLine line.toList then
-      pos := pos + 1
-    else
-      break
-  let head := body.take pos
-  let tail := body.drop pos
-  let sep := if pos > 0 then ([""] : List String) else []
-  return head ++ sep ++ preamble ++ [""] ++ tail
+    (body preamble : List String) : List String :=
+  if preamble = [] then body
+  else
+    let k := leadingFieldCount body
+    body.take k ++ (if k > 0 then [""] else []) ++ preamble ++ body.drop k
 -- impl-end
 
 -- proof-start
-/-- The `for … break` loop counting leading field lines equals the
-`takeWhile`-based `leadingFieldCount`, generalized over the accumulator so the
-induction goes through. -/
-theorem loop_helper (body : List String) (init : Nat) :
-    Id.run (forIn body init (fun line r =>
-      if isFieldLine line.toList = true then
-        (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-      else pure (ForInStep.done r)))
-    = init + (body.takeWhile (fun l => isFieldLine l.toList)).length := by
-  induction body generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isFieldLine a.toList = true
-    · simp only [h, if_true, List.takeWhile_cons]
-      rw [ih, List.length_cons]
-      omega
-    · simp only [h, List.takeWhile_cons, if_false, List.length_nil, Nat.add_zero,
-        Bool.false_eq_true]
-
 theorem correct_placePreamble : ∀ (body preamble : List String),
     problem_spec_placePreamble body preamble
       (implementation_placePreamble body preamble) := by
   intro body preamble
   unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec
-  by_cases hp : preamble = []
-  · simp only [hp, if_true, Id.run]; rfl
-  · have hloop : Id.run (forIn body 0 (fun line r =>
-        if isFieldLine line.toList = true then
-          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-        else pure (ForInStep.done r))) = leadingFieldCount body := by
-      rw [loop_helper, leadingFieldCount, Nat.zero_add]
-    simp only [hp, if_false, Id.run, bind, pure] at *
-    rw [hloop]
+  simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (by_cases hp : preamble = [] <;> simp_all <;> rfl)
 -- proof-end
```

Attack 4 — `atk_4_no_header_sep.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,56 +102,21 @@
 
 -- impl-start
 def implementation_placePreamble
-    (body preamble : List String) : List String := Id.run do
-  if preamble = [] then
-    return body
-  -- count the consecutive leading field lines
-  let mut pos := 0
-  for line in body do
-    if isFieldLine line.toList then
-      pos := pos + 1
-    else
-      break
-  let head := body.take pos
-  let tail := body.drop pos
-  let sep := if pos > 0 then ([""] : List String) else []
-  return head ++ sep ++ preamble ++ [""] ++ tail
+    (body preamble : List String) : List String :=
+  if preamble = [] then body
+  else
+    let k := leadingFieldCount body
+    body.take k ++ preamble ++ [""] ++ body.drop k
 -- impl-end
 
 -- proof-start
-/-- The `for … break` loop counting leading field lines equals the
-`takeWhile`-based `leadingFieldCount`, generalized over the accumulator so the
-induction goes through. -/
-theorem loop_helper (body : List String) (init : Nat) :
-    Id.run (forIn body init (fun line r =>
-      if isFieldLine line.toList = true then
-        (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-      else pure (ForInStep.done r)))
-    = init + (body.takeWhile (fun l => isFieldLine l.toList)).length := by
-  induction body generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isFieldLine a.toList = true
-    · simp only [h, if_true, List.takeWhile_cons]
-      rw [ih, List.length_cons]
-      omega
-    · simp only [h, List.takeWhile_cons, if_false, List.length_nil, Nat.add_zero,
-        Bool.false_eq_true]
-
 theorem correct_placePreamble : ∀ (body preamble : List String),
     problem_spec_placePreamble body preamble
       (implementation_placePreamble body preamble) := by
   intro body preamble
   unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec
-  by_cases hp : preamble = []
-  · simp only [hp, if_true, Id.run]; rfl
-  · have hloop : Id.run (forIn body 0 (fun line r =>
-        if isFieldLine line.toList = true then
-          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-        else pure (ForInStep.done r))) = leadingFieldCount body := by
-      rw [loop_helper, leadingFieldCount, Nat.zero_add]
-    simp only [hp, if_false, Id.run, bind, pure] at *
-    rw [hloop]
+  simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (by_cases hp : preamble = [] <;> simp_all <;> rfl)
 -- proof-end
```

Attack 5 — `atk_5_off_by_one.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,56 +102,21 @@
 
 -- impl-start
 def implementation_placePreamble
-    (body preamble : List String) : List String := Id.run do
-  if preamble = [] then
-    return body
-  -- count the consecutive leading field lines
-  let mut pos := 0
-  for line in body do
-    if isFieldLine line.toList then
-      pos := pos + 1
-    else
-      break
-  let head := body.take pos
-  let tail := body.drop pos
-  let sep := if pos > 0 then ([""] : List String) else []
-  return head ++ sep ++ preamble ++ [""] ++ tail
+    (body preamble : List String) : List String :=
+  if preamble = [] then body
+  else
+    let k := leadingFieldCount body + 1
+    body.take k ++ (if k > 0 then [""] else []) ++ preamble ++ [""] ++ body.drop k
 -- impl-end
 
 -- proof-start
-/-- The `for … break` loop counting leading field lines equals the
-`takeWhile`-based `leadingFieldCount`, generalized over the accumulator so the
-induction goes through. -/
-theorem loop_helper (body : List String) (init : Nat) :
-    Id.run (forIn body init (fun line r =>
-      if isFieldLine line.toList = true then
-        (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-      else pure (ForInStep.done r)))
-    = init + (body.takeWhile (fun l => isFieldLine l.toList)).length := by
-  induction body generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isFieldLine a.toList = true
-    · simp only [h, if_true, List.takeWhile_cons]
-      rw [ih, List.length_cons]
-      omega
-    · simp only [h, List.takeWhile_cons, if_false, List.length_nil, Nat.add_zero,
-        Bool.false_eq_true]
-
 theorem correct_placePreamble : ∀ (body preamble : List String),
     problem_spec_placePreamble body preamble
       (implementation_placePreamble body preamble) := by
   intro body preamble
   unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec
-  by_cases hp : preamble = []
-  · simp only [hp, if_true, Id.run]; rfl
-  · have hloop : Id.run (forIn body 0 (fun line r =>
-        if isFieldLine line.toList = true then
-          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-        else pure (ForInStep.done r))) = leadingFieldCount body := by
-      rw [loop_helper, leadingFieldCount, Nat.zero_add]
-    simp only [hp, if_false, Id.run, bind, pure] at *
-    rw [hloop]
+  simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (by_cases hp : preamble = [] <;> simp_all <;> rfl)
 -- proof-end
```

Attack 6 — `atk_6_count_all.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,56 +102,21 @@
 
 -- impl-start
 def implementation_placePreamble
-    (body preamble : List String) : List String := Id.run do
-  if preamble = [] then
-    return body
-  -- count the consecutive leading field lines
-  let mut pos := 0
-  for line in body do
-    if isFieldLine line.toList then
-      pos := pos + 1
-    else
-      break
-  let head := body.take pos
-  let tail := body.drop pos
-  let sep := if pos > 0 then ([""] : List String) else []
-  return head ++ sep ++ preamble ++ [""] ++ tail
+    (body preamble : List String) : List String :=
+  if preamble = [] then body
+  else
+    let k := (body.filter (fun l => isFieldLine l.toList)).length
+    body.take k ++ (if k > 0 then [""] else []) ++ preamble ++ [""] ++ body.drop k
 -- impl-end
 
 -- proof-start
-/-- The `for … break` loop counting leading field lines equals the
-`takeWhile`-based `leadingFieldCount`, generalized over the accumulator so the
-induction goes through. -/
-theorem loop_helper (body : List String) (init : Nat) :
-    Id.run (forIn body init (fun line r =>
-      if isFieldLine line.toList = true then
-        (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-      else pure (ForInStep.done r)))
-    = init + (body.takeWhile (fun l => isFieldLine l.toList)).length := by
-  induction body generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isFieldLine a.toList = true
-    · simp only [h, if_true, List.takeWhile_cons]
-      rw [ih, List.length_cons]
-      omega
-    · simp only [h, List.takeWhile_cons, if_false, List.length_nil, Nat.add_zero,
-        Bool.false_eq_true]
-
 theorem correct_placePreamble : ∀ (body preamble : List String),
     problem_spec_placePreamble body preamble
       (implementation_placePreamble body preamble) := by
   intro body preamble
   unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec
-  by_cases hp : preamble = []
-  · simp only [hp, if_true, Id.run]; rfl
-  · have hloop : Id.run (forIn body 0 (fun line r =>
-        if isFieldLine line.toList = true then
-          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
-        else pure (ForInStep.done r))) = leadingFieldCount body := by
-      rw [loop_helper, leadingFieldCount, Nat.zero_add]
-    simp only [hp, if_false, Id.run, bind, pure] at *
-    rw [hloop]
+  simp only [Id.run, bind, pure]
+  first
+    | rfl
+    | (by_cases hp : preamble = [] <;> simp_all <;> rfl)
 -- proof-end
```

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```lean
import Mathlib
-- imports-end

/-!
Behavior: inserting a configured preamble block into the leading lines of a
reStructuredText document body, while preserving any bibliographic header that
the document opens with.

A document body is a sequence of text lines. A preamble (itself a sequence of
lines) is spliced in near the top. The placement rule depends on how many of the
document's *leading* lines are bibliographic field lines:

  * A bibliographic field line opens with a name enclosed in colons followed by
    a space or the end of the line (the reStructuredText field-marker grammar):
    `:name: value` or `:name:`. The name is non-empty, may itself contain
    (escaped or interior) colons, and may not begin with a space.
  * Lines that merely START with a colon-delimited token but are NOT field
    markers — e.g. an interpreted-text role applied to a title such as a
    cross-reference written `:role:` immediately followed by back-quoted text —
    are NOT counted as leading field lines.

Let `k` be the number of consecutive field lines at the very front of the body.
The preamble is placed immediately after those `k` lines. When `k > 0` a single
blank line is emitted between the header block and the preamble; in every case a
single blank line is emitted after the preamble, before the remaining body.
When the preamble is empty the body is returned unchanged.

This module pins exactly where the preamble lands relative to the leading lines,
so that a document whose first line is a colon-delimited role (not a field) keeps
that line adjacent to the line that follows it.
-/

-- axioms-start
-- No outside callee is consumed: the classification of a leading line as a
-- field line, and the placement arithmetic, are modeled DEEPLY from the input
-- line text. There are no `opaque` declarations and no `_prop` axioms; the
-- field-line grammar is validated against the real reference matcher by the
-- mechanical differential check (G-CONF).
-- axioms-end

-- pure-start
/-- Scan the body of a field marker starting just after its opening colon.
`prev` is the character immediately to the left of the cursor (used to enforce
that a closing colon is not preceded by a space). Returns `true` as soon as a
valid closing colon — one not preceded by a space and followed by a space or the
end of the line — is reached. Interior colons (followed by a non-space,
non-backtick character) and backslash-escaped characters are consumed as part of
the name; a backtick or space directly after an interior-looking colon ends the
scan unsuccessfully. -/
def fieldMarkerScan : List Char → Char → Bool
  -- ran off the end without reaching a valid closing colon: no field marker
  | [], _ => false
  -- a trailing backslash with nothing to escape: no field marker
  | (['\\']), _ => false
  -- backslash escapes the next character; both are consumed as name text and
  -- the escaped character becomes the left-neighbour of what follows
  | ('\\' :: d :: rest2), _ => fieldMarkerScan rest2 d
  | (':' :: []), prev => prev != ' '
  | (':' :: d :: tail), prev =>
    -- a closing colon: not preceded by a space, followed by a space or EOL
    if prev != ' ' && d == ' ' then true
    -- an interior colon (part of the name): keep scanning
    else if d != ' ' && d != '`' then fieldMarkerScan (d :: tail) ':'
    else false
  | (c :: rest), _ => fieldMarkerScan rest c
termination_by l _ => l.length
decreasing_by all_goals (simp_wf; try omega)

/-- Whether a line is a bibliographic field line: it opens with `:`, the first
name character is neither `:` nor a space, and the field-marker grammar reaches
a valid closing colon. -/
def isFieldLine (line : List Char) : Bool :=
  match line with
  | (':' :: d :: rest) =>
    if d == ':' || d == ' ' then false else fieldMarkerScan (d :: rest) ':'
  | _ => false

/-- The number of consecutive leading lines of `body` that are field lines. -/
def leadingFieldCount (body : List String) : Nat :=
  (body.takeWhile (fun l => isFieldLine l.toList)).length

/-- The placed-preamble result: the leading `k = leadingFieldCount body` lines,
then (only when `k > 0`) a blank separator, then the preamble, then a blank
separator, then the rest of the body. An empty preamble leaves the body as-is. -/
def placePreambleSpec (body preamble : List String) : List String :=
  if preamble = [] then body
  else
    let k := leadingFieldCount body
    body.take k ++ (if k > 0 then [""] else []) ++ preamble ++ [""] ++ body.drop k
-- pure-end

-- post-conditions-start
/-- The result is exactly the body with the preamble spliced in after the
leading run of field lines: the unchanged leading lines, an optional blank
separator present iff there was at least one leading field line, the preamble
lines in order, a trailing blank separator, and the remaining body lines
unchanged. An empty preamble yields the body verbatim. -/
def problem_spec_placePreamble
    (body preamble : List String) (result : List String) : Prop :=
  result = placePreambleSpec body preamble
-- post-conditions-end

-- impl-start
def implementation_placePreamble
    (body preamble : List String) : List String := Id.run do
  if preamble = [] then
    return body
  -- count the consecutive leading field lines
  let mut pos := 0
  for line in body do
    if isFieldLine line.toList then
      pos := pos + 1
    else
      break
  let head := body.take pos
  let tail := body.drop pos
  let sep := if pos > 0 then ([""] : List String) else []
  return head ++ sep ++ preamble ++ [""] ++ tail
-- impl-end

-- proof-start
/-- The `for … break` loop counting leading field lines equals the
`takeWhile`-based `leadingFieldCount`, generalized over the accumulator so the
induction goes through. -/
theorem loop_helper (body : List String) (init : Nat) :
    Id.run (forIn body init (fun line r =>
      if isFieldLine line.toList = true then
        (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
      else pure (ForInStep.done r)))
    = init + (body.takeWhile (fun l => isFieldLine l.toList)).length := by
  induction body generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    by_cases h : isFieldLine a.toList = true
    · simp only [h, if_true, List.takeWhile_cons]
      rw [ih, List.length_cons]
      omega
    · simp only [h, List.takeWhile_cons, if_false, List.length_nil, Nat.add_zero,
        Bool.false_eq_true]

theorem correct_placePreamble : ∀ (body preamble : List String),
    problem_spec_placePreamble body preamble
      (implementation_placePreamble body preamble) := by
  intro body preamble
  unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec
  by_cases hp : preamble = []
  · simp only [hp, if_true, Id.run]; rfl
  · have hloop : Id.run (forIn body 0 (fun line r =>
        if isFieldLine line.toList = true then
          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
        else pure (ForInStep.done r))) = leadingFieldCount body := by
      rw [loop_helper, leadingFieldCount, Nat.zero_add]
    simp only [hp, if_false, Id.run, bind, pure] at *
    rw [hloop]
-- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Behavior: inserting a configured preamble block into the leading lines of a
reStructuredText document body, while preserving any bibliographic header that
the document opens with.

A document body is a sequence of text lines. A preamble (itself a sequence of
lines) is spliced in near the top. The placement rule depends on how many of the
document's *leading* lines are bibliographic field lines:

  * A bibliographic field line opens with a name enclosed in colons followed by
    a space or the end of the line (the reStructuredText field-marker grammar):
    `:name: value` or `:name:`. The name is non-empty, may itself contain
    (escaped or interior) colons, and may not begin with a space.
  * Lines that merely START with a colon-delimited token but are NOT field
    markers — e.g. an interpreted-text role applied to a title such as a
    cross-reference written `:role:` immediately followed by back-quoted text —
    are NOT counted as leading field lines.

Let `k` be the number of consecutive field lines at the very front of the body.
The preamble is placed immediately after those `k` lines. When `k > 0` a single
blank line is emitted between the header block and the preamble; in every case a
single blank line is emitted after the preamble, before the remaining body.
When the preamble is empty the body is returned unchanged.

This module pins exactly where the preamble lands relative to the leading lines,
so that a document whose first line is a colon-delimited role (not a field) keeps
that line adjacent to the line that follows it.
-/

-- axioms-start
-- No outside callee is consumed: the classification of a leading line as a
-- field line, and the placement arithmetic, are modeled DEEPLY from the input
-- line text. There are no `opaque` declarations and no `_prop` axioms; the
-- field-line grammar is validated against the real reference matcher by the
-- mechanical differential check (G-CONF).
-- axioms-end

-- pure-start
/-- Scan the body of a field marker starting just after its opening colon.
`prev` is the character immediately to the left of the cursor (used to enforce
that a closing colon is not preceded by a space). Returns `true` as soon as a
valid closing colon — one not preceded by a space and followed by a space or the
end of the line — is reached. Interior colons (followed by a non-space,
non-backtick character) and backslash-escaped characters are consumed as part of
the name; a backtick or space directly after an interior-looking colon ends the
scan unsuccessfully. -/
def fieldMarkerScan : List Char → Char → Bool
  -- ran off the end without reaching a valid closing colon: no field marker
  | [], _ => false
  -- a trailing backslash with nothing to escape: no field marker
  | (['\\']), _ => false
  -- backslash escapes the next character; both are consumed as name text and
  -- the escaped character becomes the left-neighbour of what follows
  | ('\\' :: d :: rest2), _ => fieldMarkerScan rest2 d
  | (':' :: []), prev => prev != ' '
  | (':' :: d :: tail), prev =>
    -- a closing colon: not preceded by a space, followed by a space or EOL
    if prev != ' ' && d == ' ' then true
    -- an interior colon (part of the name): keep scanning
    else if d != ' ' && d != '`' then fieldMarkerScan (d :: tail) ':'
    else false
  | (c :: rest), _ => fieldMarkerScan rest c
termination_by l _ => l.length
decreasing_by all_goals (simp_wf; try omega)

/-- Whether a line is a bibliographic field line: it opens with `:`, the first
name character is neither `:` nor a space, and the field-marker grammar reaches
a valid closing colon. -/
def isFieldLine (line : List Char) : Bool :=
  match line with
  | (':' :: d :: rest) =>
    if d == ':' || d == ' ' then false else fieldMarkerScan (d :: rest) ':'
  | _ => false

/-- The number of consecutive leading lines of `body` that are field lines. -/
def leadingFieldCount (body : List String) : Nat :=
  (body.takeWhile (fun l => isFieldLine l.toList)).length

/-- The placed-preamble result: the leading `k = leadingFieldCount body` lines,
then (only when `k > 0`) a blank separator, then the preamble, then a blank
separator, then the rest of the body. An empty preamble leaves the body as-is. -/
def placePreambleSpec (body preamble : List String) : List String :=
  if preamble = [] then body
  else
    let k := leadingFieldCount body
    body.take k ++ (if k > 0 then [""] else []) ++ preamble ++ [""] ++ body.drop k
-- pure-end

-- post-conditions-start
/-- The result is exactly the body with the preamble spliced in after the
leading run of field lines: the unchanged leading lines, an optional blank
separator present iff there was at least one leading field line, the preamble
lines in order, a trailing blank separator, and the remaining body lines
unchanged. An empty preamble yields the body verbatim. -/
def problem_spec_placePreamble
    (body preamble : List String) (result : List String) : Prop :=
  result = placePreambleSpec body preamble
-- post-conditions-end

-- impl-start
def implementation_placePreamble
    (body preamble : List String) : List String := Id.run do
  if preamble = [] then
    return body
  -- count the consecutive leading field lines
  let mut pos := 0
  for line in body do
    if isFieldLine line.toList then
      pos := pos + 1
    else
      break
  let head := body.take pos
  let tail := body.drop pos
  let sep := if pos > 0 then ([""] : List String) else []
  return head ++ sep ++ preamble ++ [""] ++ tail
-- impl-end

-- proof-start
/-- The `for … break` loop counting leading field lines equals the
`takeWhile`-based `leadingFieldCount`, generalized over the accumulator so the
induction goes through. -/
theorem loop_helper (body : List String) (init : Nat) :
    Id.run (forIn body init (fun line r =>
      if isFieldLine line.toList = true then
        (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
      else pure (ForInStep.done r)))
    = init + (body.takeWhile (fun l => isFieldLine l.toList)).length := by
  induction body generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    by_cases h : isFieldLine a.toList = true
    · simp only [h, if_true, List.takeWhile_cons]
      rw [ih, List.length_cons]
      omega
    · simp only [h, List.takeWhile_cons, if_false, List.length_nil, Nat.add_zero,
        Bool.false_eq_true]

theorem correct_placePreamble : ∀ (body preamble : List String),
    problem_spec_placePreamble body preamble
      (implementation_placePreamble body preamble) := by
  intro body preamble
  unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec
  by_cases hp : preamble = []
  · simp only [hp, if_true, Id.run]; rfl
  · have hloop : Id.run (forIn body 0 (fun line r =>
        if isFieldLine line.toList = true then
          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
        else pure (ForInStep.done r))) = leadingFieldCount body := by
      rw [loop_helper, leadingFieldCount, Nat.zero_add]
    simp only [hp, if_false, Id.run, bind, pure] at *
    rw [hloop]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a tight universal EQUALITY: `problem_spec_placePreamble body preamble result := result = placePreambleSpec body preamble`, where placePreambleSpec is a TOTAL, CONCRETE reference function over all (body, preamble). By Lean soundness any impl that honestly closes the canonical `correct_placePreamble : ∀ body preamble, problem_spec ... (implementation ...)` is provably equal to placePreambleSpec on all inputs, hence its faithful patch reproduces gold behavior (G-CONF-validated == real post-patch prepend_prolog over 1e5 pairs) and must resolve.

Same_spec confirmed True for all 7 attacks + positive control (proof region is elided by spec_view, so only impl edits were made; axioms/pure/pre/post byte-identical).

Attacks (verify via `bash scripts/lean_verify.sh <f>`, from project root):
- atk_1_prepatch.lean (prepatch looseFieldHead `:word:` classifier — the real bug): EXIT=1 (proof does NOT close; `rfl` fails). PREPATCH BUG REPRODUCED.
- atk_2_ignore_preamble.lean (partial/degenerate: returns body, ignores preamble): EXIT=1 (rfl failed).
- atk_3_no_trailing_blank.lean (drops the trailing blank separator): EXIT=1.
- atk_4_no_header_sep.lean (drops the conditional header separator): EXIT=1.
- atk_5_off_by_one.lean (boundary: k = leadingFieldCount+1): EXIT=1 (rfl failed).
- atk_6_count_all.lean (control-flow-effect: counts ALL field lines via filter, not the leading run): EXIT=1.
- atk_7_echo.lean (ungrounded-oracle echo = gold impl + canonical closing proof): EXIT=0, `#print axioms correct_placePreamble` = [propext, Classical.choice, Quot.sound] (clean standard axioms, no sorryAx).

All 6 honest impl-only wrong variants FAIL to verify — the tight equality spec rejects them; only the gold echo verifies. MANDATORY resolve run on the single verifying candidate (atk_7 echo, faithful patch = gold post-patch prepend_prolog):
  python -c "from swebench_unified.harness import run_resolve; run_resolve('sphinx-doc__sphinx-11445', <gold patch>)"
  => RESOLVED=True, completed=True, flaky=False, note='resolved'.
So the only verifying candidate is a CORRECT echo (verify AND resolve) — NOT a spec weakness. No same-spec impl-only wrong impl both verifies and fails to resolve. verify⇒correct holds; NOT BROKEN.

pos_control.lean = byte-identical Solution.lean: EXIT=0, clean axioms — positive control verifies.

Refinement.md A-leg audit: only non-R/I leg is Leg 2 = A-reference (isFieldLine/fieldMarkerScan is a DEEP model of the unchanged docutils `field_marker` regex the patch newly consults). SPEC_GUIDE §3 forbids axiomatizing the changed op, so it is modeled deeply, not consumed as an axiom. Correspondence to the REAL callee is validated by G-CONF LEG 1 (== real compiled `re.compile(Body.patterns['field_marker']).match` over 16 structured + 1e5 fuzzed lines, 0 disagreements; meta G-CONF pass). LEG 2 additionally validates the full impl == real post-patch prepend_prolog over 1e5 (body,prolog) pairs. Axioms region is EMPTY (no `axiom`/`opaque`) => no A-consumed leg and NO kind-3 (no ungrounded oracle/axiom); G-AX legitimately skips. All legs are R / A-reference / I. Correspondence holds.

CAVEAT (out of scope, universal harness property — NOT a break of this spec): check_attack's same_spec elides the ENTIRE proof region including the `theorem correct_` header, and lean_verify.sh checks only elaboration+no-sorry (no canonical-statement pin). I confirmed a probe (probe_vacuous.lean) that changes the impl to `body` AND weakens the theorem to `correct_placePreamble : True := trivial` passes same_spec=True and verifies with `does not depend on any axioms`. This requires editing the PROOF region, which violates the impl-only G-EQ attack contract (the prompt fixes impl-only, proof must re-prove the SAME canonical theorem), so it is not a same-spec impl-only counterexample and is not claimed as BROKEN. It is a general observation about the mechanized check surface, not specific to this bundle.

Verdict: SOUND — 7 attacks (>=5) re-run, prepatch reproduced, positive control verifies; the sole verifying candidate resolves. No impl-only same-spec wrong impl verifies-without-resolving.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_ignore_preamble.lean`, `atk_3_no_trailing_blank.lean`, `atk_4_no_header_sep.lean`, `atk_5_off_by_one.lean`, `atk_6_count_all.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_ignore_preamble.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_no_trailing_blank.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_no_header_sep.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_off_by_one.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_count_all.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Behavior: inserting a configured preamble block into the leading lines of a
reStructuredText document body, while preserving any bibliographic header that
the document opens with.

A document body is a sequence of text lines. A preamble (itself a sequence of
lines) is spliced in near the top. The placement rule depends on how many of the
document's *leading* lines are bibliographic field lines:

  * A bibliographic field line opens with a name enclosed in colons followed by
    a space or the end of the line (the reStructuredText field-marker grammar):
    `:name: value` or `:name:`. The name is non-empty, may itself contain
    (escaped or interior) colons, and may not begin with a space.
  * Lines that merely START with a colon-delimited token but are NOT field
    markers — e.g. an interpreted-text role applied to a title such as a
    cross-reference written `:role:` immediately followed by back-quoted text —
    are NOT counted as leading field lines.

Let `k` be the number of consecutive field lines at the very front of the body.
The preamble is placed immediately after those `k` lines. When `k > 0` a single
blank line is emitted between the header block and the preamble; in every case a
single blank line is emitted after the preamble, before the remaining body.
When the preamble is empty the body is returned unchanged.

This module pins exactly where the preamble lands relative to the leading lines,
so that a document whose first line is a colon-delimited role (not a field) keeps
that line adjacent to the line that follows it.
-/

-- axioms-start
-- No outside callee is consumed: the classification of a leading line as a
-- field line, and the placement arithmetic, are modeled DEEPLY from the input
-- line text. There are no `opaque` declarations and no `_prop` axioms; the
-- field-line grammar is validated against the real reference matcher by the
-- mechanical differential check (G-CONF).
-- axioms-end

-- pure-start
/-- Scan the body of a field marker starting just after its opening colon.
`prev` is the character immediately to the left of the cursor (used to enforce
that a closing colon is not preceded by a space). Returns `true` as soon as a
valid closing colon — one not preceded by a space and followed by a space or the
end of the line — is reached. Interior colons (followed by a non-space,
non-backtick character) and backslash-escaped characters are consumed as part of
the name; a backtick or space directly after an interior-looking colon ends the
scan unsuccessfully. -/
def fieldMarkerScan : List Char → Char → Bool
  -- ran off the end without reaching a valid closing colon: no field marker
  | [], _ => false
  -- a trailing backslash with nothing to escape: no field marker
  | (['\\']), _ => false
  -- backslash escapes the next character; both are consumed as name text and
  -- the escaped character becomes the left-neighbour of what follows
  | ('\\' :: d :: rest2), _ => fieldMarkerScan rest2 d
  | (':' :: []), prev => prev != ' '
  | (':' :: d :: tail), prev =>
    -- a closing colon: not preceded by a space, followed by a space or EOL
    if prev != ' ' && d == ' ' then true
    -- an interior colon (part of the name): keep scanning
    else if d != ' ' && d != '`' then fieldMarkerScan (d :: tail) ':'
    else false
  | (c :: rest), _ => fieldMarkerScan rest c
termination_by l _ => l.length
decreasing_by all_goals (simp_wf; try omega)

/-- Whether a line is a bibliographic field line: it opens with `:`, the first
name character is neither `:` nor a space, and the field-marker grammar reaches
a valid closing colon. -/
def isFieldLine (line : List Char) : Bool :=
  match line with
  | (':' :: d :: rest) =>
    if d == ':' || d == ' ' then false else fieldMarkerScan (d :: rest) ':'
  | _ => false

/-- The number of consecutive leading lines of `body` that are field lines. -/
def leadingFieldCount (body : List String) : Nat :=
  (body.takeWhile (fun l => isFieldLine l.toList)).length

/-- The placed-preamble result: the leading `k = leadingFieldCount body` lines,
then (only when `k > 0`) a blank separator, then the preamble, then a blank
separator, then the rest of the body. An empty preamble leaves the body as-is. -/
def placePreambleSpec (body preamble : List String) : List String :=
  if preamble = [] then body
  else
    let k := leadingFieldCount body
    body.take k ++ (if k > 0 then [""] else []) ++ preamble ++ [""] ++ body.drop k
-- pure-end

-- post-conditions-start
/-- The result is exactly the body with the preamble spliced in after the
leading run of field lines: the unchanged leading lines, an optional blank
separator present iff there was at least one leading field line, the preamble
lines in order, a trailing blank separator, and the remaining body lines
unchanged. An empty preamble yields the body verbatim. -/
def problem_spec_placePreamble
    (body preamble : List String) (result : List String) : Prop :=
  result = placePreambleSpec body preamble
-- post-conditions-end

-- impl-start
def implementation_placePreamble
    (body preamble : List String) : List String := Id.run do
  if preamble = [] then
    return body
  -- count the consecutive leading field lines
  let mut pos := 0
  for line in body do
    if isFieldLine line.toList then
      pos := pos + 1
    else
      break
  let head := body.take pos
  let tail := body.drop pos
  let sep := if pos > 0 then ([""] : List String) else []
  return head ++ sep ++ preamble ++ [""] ++ tail
-- impl-end

-- proof-start
/-- The `for … break` loop counting leading field lines equals the
`takeWhile`-based `leadingFieldCount`, generalized over the accumulator so the
induction goes through. -/
theorem loop_helper (body : List String) (init : Nat) :
    Id.run (forIn body init (fun line r =>
      if isFieldLine line.toList = true then
        (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
      else pure (ForInStep.done r)))
    = init + (body.takeWhile (fun l => isFieldLine l.toList)).length := by
  induction body generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    by_cases h : isFieldLine a.toList = true
    · simp only [h, if_true, List.takeWhile_cons]
      rw [ih, List.length_cons]
      omega
    · simp only [h, List.takeWhile_cons, if_false, List.length_nil, Nat.add_zero,
        Bool.false_eq_true]

theorem correct_placePreamble : ∀ (body preamble : List String),
    problem_spec_placePreamble body preamble
      (implementation_placePreamble body preamble) := by
  intro body preamble
  unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec
  by_cases hp : preamble = []
  · simp only [hp, if_true, Id.run]; rfl
  · have hloop : Id.run (forIn body 0 (fun line r =>
        if isFieldLine line.toList = true then
          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))
        else pure (ForInStep.done r))) = leadingFieldCount body := by
      rw [loop_helper, leadingFieldCount, Nat.zero_add]
    simp only [hp, if_false, Id.run, bind, pure] at *
    rw [hloop]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a tight universal EQUALITY: `problem_spec_placePreamble body preamble result := result = placePreambleSpec body preamble`, where placePreambleSpec is a TOTAL, CONCRETE reference function over all (body, preamble). By Lean soundness any impl that honestly closes the canonical `correct_placePreamble : ∀ body preamble, problem_spec ... (implementation ...)` is provably equal to placePreambleSpec on all inputs, hence its faithful patch reproduces gold behavior (G-CONF-validated == real post-patch prepend_prolog over 1e5 pairs) and must resolve.

Same_spec confirmed True for all 7 attacks + positive control (proof region is elided by spec_view, so only impl edits were made; axioms/pure/pre/post byte-identical).

Attacks (verify via `bash scripts/lean_verify.sh <f>`, from project root):
- atk_1_prepatch.lean (prepatch looseFieldHead `:word:` classifier — the real bug): EXIT=1 (proof does NOT close; `rfl` fails). PREPATCH BUG REPRODUCED.
- atk_2_ignore_preamble.lean (partial/degenerate: returns body, ignores preamble): EXIT=1 (rfl failed).
- atk_3_no_trailing_blank.lean (drops the trailing blank separator): EXIT=1.
- atk_4_no_header_sep.lean (drops the conditional header separator): EXIT=1.
- atk_5_off_by_one.lean (boundary: k = leadingFieldCount+1): EXIT=1 (rfl failed).
- atk_6_count_all.lean (control-flow-effect: counts ALL field lines via filter, not the leading run): EXIT=1.
- atk_7_echo.lean (ungrounded-oracle echo = gold impl + canonical closing proof): EXIT=0, `#print axioms correct_placePreamble` = [propext, Classical.choice, Quot.sound] (clean standard axioms, no sorryAx).

All 6 honest impl-only wrong variants FAIL to verify — the tight equality spec rejects them; only the gold echo verifies. MANDATORY resolve run on the single verifying candidate (atk_7 echo, faithful patch = gold post-patch prepend_prolog):
  python -c "from swebench_unified.harness import run_resolve; run_resolve('sphinx-doc__sphinx-11445', <gold patch>)"
  => RESOLVED=True, completed=True, flaky=False, note='resolved'.
So the only verifying candidate is a CORRECT echo (verify AND resolve) — NOT a spec weakness. No same-spec impl-only wrong impl both verifies and fails to resolve. verify⇒correct holds; NOT BROKEN.

pos_control.lean = byte-identical Solution.lean: EXIT=0, clean axioms — positive control verifies.

Refinement.md A-leg audit: only non-R/I leg is Leg 2 = A-reference (isFieldLine/fieldMarkerScan is a DEEP model of the unchanged docutils `field_marker` regex the patch newly consults). SPEC_GUIDE §3 forbids axiomatizing the changed op, so it is modeled deeply, not consumed as an axiom. Correspondence to the REAL callee is validated by G-CONF LEG 1 (== real compiled `re.compile(Body.patterns['field_marker']).match` over 16 structured + 1e5 fuzzed lines, 0 disagreements; meta G-CONF pass). LEG 2 additionally validates the full impl == real post-patch prepend_prolog over 1e5 (body,prolog) pairs. Axioms region is EMPTY (no `axiom`/`opaque`) => no A-consumed leg and NO kind-3 (no ungrounded oracle/axiom); G-AX legitimately skips. All legs are R / A-reference / I. Correspondence holds.

CAVEAT (out of scope, universal harness property — NOT a break of this spec): check_attack's same_spec elides the ENTIRE proof region including the `theorem correct_` header, and lean_verify.sh checks only elaboration+no-sorry (no canonical-statement pin). I confirmed a probe (probe_vacuous.lean) that changes the impl to `body` AND weakens the theorem to `correct_placePreamble : True := trivial` passes same_spec=True and verifies with `does not depend on any axioms`. This requires editing the PROOF region, which violates the impl-only G-EQ attack contract (the prompt fixes impl-only, proof must re-prove the SAME canonical theorem), so it is not a same-spec impl-only counterexample and is not claimed as BROKEN. It is a general observation about the mechanized check surface, not specific to this bundle.

Verdict: SOUND — 7 attacks (>=5) re-run, prepatch reproduced, positive control verifies; the sole verifying candidate resolves. No impl-only same-spec wrong impl verifies-without-resolving.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of sphinx-doc__sphinx-11445 (lean). Modeled routine: prepend_prolog (sphinx/util/rst.py), post-patch classifier FIELD_NAME_RE = re.compile(Body.patterns['field_marker']).

### Baseline checks
- same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True: spec regions (docstring/axioms/pure/post-conditions) byte-identical.
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). #print axioms correct_placePreamble = [propext, Classical.choice, Quot.sound]; NO sorryAx. Genuine proof of result = placePreambleSpec body preamble (a total functional equality).

INDEPENDENT DIFFERENTIAL (not the bundle's fuzzer; wider charset incl. tab, backtick, backslash, brackets, quotes, unicode; larger N; own re-transliteration of the Lean source following its match order):
- LEG 1 (classifier). Re-derived isFieldLine/fieldMarkerScan diffed against the ACTUAL compiled Body.patterns['field_marker'] regex over 34 adversarial structured lines (escapes, interior colons, backticks, `::`, trailing spaces, multi-colon names, tabs) + 3,000,000 fuzzed lines. In the MODELED DOMAIN (no embedded newline/CR) => 0 mismatches. The only divergences found (31/2M in the unrestricted run) ALL involve embedded \n/\r, which mapping.md's documented model precondition explicitly excludes (StringList entries are pre-split logical lines with no embedded breaks; matches Sphinx's real call path). Python's `.` in the regex not matching newline is precisely what those out-of-domain cases exercise, so they are not a faithfulness defect.
- LEG 2 (full impl). Lean implementation_placePreamble shadow diffed against a GENUINE StringList-based post-patch prepend_prolog (real docutils.statemachine.StringList, real .insert, real FIELD_NAME_RE, including the lineno=0 guard) over 400,000 fuzzed (body, prolog) pairs + all F2P/P2P/structured/edge cases (:x:, :x: , :x:y, ::, leading role heading :mod:`foo`, empty prolog, empty body, trailing-newline prolog, backslash line). => 0 mismatches on observable line-value ordering.

QUOTIENT/BOUNDARY: preamble=[] <-> prolog='' is exact ('' is the only string with splitlines()==[]); the (source,lineno) metadata triple is deterministic StringList bookkeeping not part of the observable content/order the F2P xitems() tests assert. Empty axioms region; no consumed callee (the changed classifier is modeled deeply, per SPEC_GUIDE 3); G-AX skips legitimately.

CONCLUSION: the modeled function agrees with the real callee on every input within the stated domain; the spec is not too strong and does not drift from real repo behavior. No diverging input exists in-domain. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (behavior docstring + axioms + pure region fieldMarkerScan/isFieldLine/leadingFieldCount/placePreambleSpec + post-conditions; impl & proof elided) verified via markers.spec_view with Lean tables. same_spec(Solution.lean, Solution_prepatch.lean)=True, so the spec region is genuinely impl-independent. The spec describes the CORRECT behavior of the post-patch classifier (field line = :name:/:name: value with closing colon followed by space/EOL; :role:`text` NOT counted; preamble placed after leading field-line run) — this is the legitimate, inherent behavioral specification of the modeled function, i.e. the public oracle of a refinement-style bundle, not a reconstruction of the withheld gold. It stays strictly behavioral: no gold-patch identifiers (docinfo_re, FIELD_NAME_RE, Body.patterns['field_marker'], prepend_prolog), no raw docutils regex string (that lives only in mapping.md, an audit artifact outside the spec view), no framing as a change/fix, no reference to the prepatch delta, and no private test inputs (the :role: example is generic; the :mod: example is already public in problem_statement). problem_statement itself already reveals :mod:-heading + rst_prolog as the trigger. Nothing in the spec view lets one reconstruct the gold edit beyond what a faithful correct-behavior spec necessarily conveys. G-LEAK lexical screen also recorded pass with empty failures.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

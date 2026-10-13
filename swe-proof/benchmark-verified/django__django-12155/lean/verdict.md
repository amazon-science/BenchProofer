# P2 adversarial audit — django__django-12155

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 8 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,16 +106,13 @@
 -- impl-start
 def implementation_normalizeIndent (lines : List (List Char)) :
     List (List Char) := Id.run do
-  -- common indentation, measured over the lines after the first
   let mut margin : Option Nat := none
-  for line in lines.drop 1 do
+  for line in lines do          -- BUG: includes first line
     if !isBlank line then
       let ind := leadingWs line
       margin := some (match margin with
                       | none   => ind
                       | some m => Nat.min m ind)
-  -- strip the first line's leading whitespace; dedent each following line by the
-  -- common margin
   let mut out : List (List Char) :=
     match lines with
     | []          => []
@@ -124,7 +121,6 @@
     match margin with
     | none   => out := out ++ [line]
     | some m => out := out ++ [line.drop m]
-  -- drop completely empty lines from the end, then from the beginning
   out := dropTrailingEmpty out
   out := dropLeadingEmpty out
   return out
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,7 +106,6 @@
 -- impl-start
 def implementation_normalizeIndent (lines : List (List Char)) :
     List (List Char) := Id.run do
-  -- common indentation, measured over the lines after the first
   let mut margin : Option Nat := none
   for line in lines.drop 1 do
     if !isBlank line then
@@ -114,8 +113,6 @@
       margin := some (match margin with
                       | none   => ind
                       | some m => Nat.min m ind)
-  -- strip the first line's leading whitespace; dedent each following line by the
-  -- common margin
   let mut out : List (List Char) :=
     match lines with
     | []          => []
@@ -124,9 +121,8 @@
     match margin with
     | none   => out := out ++ [line]
     | some m => out := out ++ [line.drop m]
-  -- drop completely empty lines from the end, then from the beginning
   out := dropTrailingEmpty out
-  out := dropLeadingEmpty out
+  -- BUG: forgot dropLeadingEmpty
   return out
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,16 +106,13 @@
 -- impl-start
 def implementation_normalizeIndent (lines : List (List Char)) :
     List (List Char) := Id.run do
-  -- common indentation, measured over the lines after the first
   let mut margin : Option Nat := none
-  for line in lines.drop 1 do
+  for line in lines.drop 2 do   -- BUG: off-by-one, skips second line
     if !isBlank line then
       let ind := leadingWs line
       margin := some (match margin with
                       | none   => ind
                       | some m => Nat.min m ind)
-  -- strip the first line's leading whitespace; dedent each following line by the
-  -- common margin
   let mut out : List (List Char) :=
     match lines with
     | []          => []
@@ -124,7 +121,6 @@
     match margin with
     | none   => out := out ++ [line]
     | some m => out := out ++ [line.drop m]
-  -- drop completely empty lines from the end, then from the beginning
   out := dropTrailingEmpty out
   out := dropLeadingEmpty out
   return out
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

```diff
@@ -106,7 +106,6 @@
 -- impl-start
 def implementation_normalizeIndent (lines : List (List Char)) :
     List (List Char) := Id.run do
-  -- common indentation, measured over the lines after the first
   let mut margin : Option Nat := none
   for line in lines.drop 1 do
     if !isBlank line then
@@ -114,17 +113,14 @@
       margin := some (match margin with
                       | none   => ind
                       | some m => Nat.min m ind)
-  -- strip the first line's leading whitespace; dedent each following line by the
-  -- common margin
   let mut out : List (List Char) :=
     match lines with
     | []          => []
-    | first :: _  => [lstripWs first]
+    | first :: _  => [first]     -- BUG: first line not lstripped
   for line in lines.drop 1 do
     match margin with
     | none   => out := out ++ [line]
     | some m => out := out ++ [line.drop m]
-  -- drop completely empty lines from the end, then from the beginning
   out := dropTrailingEmpty out
   out := dropLeadingEmpty out
   return out
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,7 +106,6 @@
 -- impl-start
 def implementation_normalizeIndent (lines : List (List Char)) :
     List (List Char) := Id.run do
-  -- common indentation, measured over the lines after the first
   let mut margin : Option Nat := none
   for line in lines.drop 1 do
     if !isBlank line then
@@ -114,17 +113,15 @@
       margin := some (match margin with
                       | none   => ind
                       | some m => Nat.min m ind)
-  -- strip the first line's leading whitespace; dedent each following line by the
-  -- common margin
   let mut out : List (List Char) :=
-    match lines with
-    | []          => []
-    | first :: _  => [lstripWs first]
+    match lines, margin with
+    | [], _              => []
+    | first :: _, none   => [lstripWs first]
+    | first :: _, some m => [(lstripWs first).drop m]  -- BUG: also dedent first
   for line in lines.drop 1 do
     match margin with
     | none   => out := out ++ [line]
     | some m => out := out ++ [line.drop m]
-  -- drop completely empty lines from the end, then from the beginning
   out := dropTrailingEmpty out
   out := dropLeadingEmpty out
   return out
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,16 +106,13 @@
 -- impl-start
 def implementation_normalizeIndent (lines : List (List Char)) :
     List (List Char) := Id.run do
-  -- common indentation, measured over the lines after the first
   let mut margin : Option Nat := none
   for line in lines.drop 1 do
     if !isBlank line then
       let ind := leadingWs line
       margin := some (match margin with
                       | none   => ind
-                      | some m => Nat.min m ind)
-  -- strip the first line's leading whitespace; dedent each following line by the
-  -- common margin
+                      | some m => Nat.max m ind)   -- BUG: max not min
   let mut out : List (List Char) :=
     match lines with
     | []          => []
@@ -124,7 +121,6 @@
     match margin with
     | none   => out := out ++ [line]
     | some m => out := out ++ [line.drop m]
-  -- drop completely empty lines from the end, then from the beginning
   out := dropTrailingEmpty out
   out := dropLeadingEmpty out
   return out
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -105,144 +105,15 @@
 
 -- impl-start
 def implementation_normalizeIndent (lines : List (List Char)) :
-    List (List Char) := Id.run do
-  -- common indentation, measured over the lines after the first
-  let mut margin : Option Nat := none
-  for line in lines.drop 1 do
-    if !isBlank line then
-      let ind := leadingWs line
-      margin := some (match margin with
-                      | none   => ind
-                      | some m => Nat.min m ind)
-  -- strip the first line's leading whitespace; dedent each following line by the
-  -- common margin
-  let mut out : List (List Char) :=
-    match lines with
-    | []          => []
-    | first :: _  => [lstripWs first]
-  for line in lines.drop 1 do
-    match margin with
-    | none   => out := out ++ [line]
-    | some m => out := out ++ [line.drop m]
-  -- drop completely empty lines from the end, then from the beginning
-  out := dropTrailingEmpty out
-  out := dropLeadingEmpty out
-  return out
+    List (List Char) :=
+  normalizeIndentSpec lines
 -- impl-end
 
 -- proof-start
--- @ns:fold_append_map-start
--- @decl:fold_append_map-start
-theorem fold_append_map {α β : Type _} (g : α → β) (init : List β) (l : List α) :
-    List.foldl (fun acc x => acc ++ [g x]) init l = init ++ l.map g := by
-  induction l generalizing init with
-  | nil => simp
-  | cons a t ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
--- @decl:fold_append_map-end
--- @ns:fold_append_map-end
-
--- @ns:margin_loop_eq-start
--- @decl:margin_loop_eq-start
-theorem margin_loop_eq (rest : List (List Char)) :
-    List.foldl
-      (fun margin line =>
-        if !isBlank line then
-          some (match margin with
-                | none   => leadingWs line
-                | some m => Nat.min m (leadingWs line))
-        else margin)
-      none rest = marginSpec rest := by
-  unfold marginSpec
-  congr 1
-  funext m line
-  cases isBlank line <;> simp
--- @decl:margin_loop_eq-end
--- @ns:margin_loop_eq-end
-
--- @ns:dedent_loop_eq-start
--- @decl:dedent_loop_eq-start
-theorem dedent_loop_eq (lines : List (List Char)) (margin : Option Nat) :
-    (match lines with
-     | []           => []
-     | first :: _   => [lstripWs first]) ++
-      List.foldl
-        (fun out line =>
-          match margin with
-          | none   => out ++ [line]
-          | some m => out ++ [line.drop m])
-        [] (lines.drop 1) = dedentSpec margin lines := by
-  cases lines with
-  | nil => simp [dedentSpec]
-  | cons first rest =>
-    simp only [List.drop_succ_cons, List.drop_zero, dedentSpec]
-    cases margin with
-    | none =>
-      show [lstripWs first] ++ List.foldl (fun out line => out ++ [id line]) [] rest = _
-      rw [fold_append_map (g := id)]; simp
-    | some m =>
-      show [lstripWs first] ++ List.foldl (fun out line => out ++ [(fun l => List.drop m l) line]) [] rest = _
-      rw [fold_append_map (g := fun l => List.drop m l)]; simp
--- @decl:dedent_loop_eq-end
--- @ns:dedent_loop_eq-end
-
--- @ns:impl_as_folds-start
--- @decl:impl_as_folds-start
-theorem impl_as_folds (lines : List (List Char)) :
-    implementation_normalizeIndent lines =
-      dropLeadingEmpty (dropTrailingEmpty
-        ((match lines with
-          | []          => []
-          | first :: _  => [lstripWs first]) ++
-          List.foldl
-            (fun out line =>
-              match
-                (List.foldl
-                  (fun margin line =>
-                    if !isBlank line then
-                      some (match margin with
-                            | none   => leadingWs line
-                            | some m => Nat.min m (leadingWs line))
-                    else margin)
-                  none (lines.drop 1)) with
-              | none   => out ++ [line]
-              | some m => out ++ [line.drop m])
-            [] (lines.drop 1))) := by
-  unfold implementation_normalizeIndent
-  simp only [Id.run, bind, pure]
-  simp only [← apply_ite ForInStep.yield]
-  rw [List.forIn_yield_eq_foldl]
-  generalize List.foldl (fun b a =>
-      if (!isBlank a) = true then
-        some (match b with | none => leadingWs a | some m => m.min (leadingWs a))
-      else b) none (lines.drop 1) = M
-  cases M with
-  | none =>
-    simp only []
-    rw [List.forIn_yield_eq_foldl]
-    rw [fold_append_map (fun a => a), fold_append_map (fun a => a)]
-    simp
-  | some m =>
-    simp only []
-    rw [List.forIn_yield_eq_foldl]
-    rw [fold_append_map (fun a : List Char => a.drop m),
-        fold_append_map (fun a : List Char => a.drop m)]
-    simp
--- @decl:impl_as_folds-end
--- @ns:impl_as_folds-end
-
-
 theorem correct_normalizeIndent :
     ∀ (lines : List (List Char)),
       problem_spec_normalizeIndent lines
         (implementation_normalizeIndent lines) := by
   intro lines
-  unfold problem_spec_normalizeIndent
-  rw [impl_as_folds]
-  simp only [margin_loop_eq]
-  unfold normalizeIndentSpec
-  congr 1
-  congr 1
-  rcases h : marginSpec (lines.drop 1) with _ | m
-  · exact dedent_loop_eq lines none
-  · exact dedent_loop_eq lines (some m)
+  rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,7 +106,6 @@
 -- impl-start
 def implementation_normalizeIndent (lines : List (List Char)) :
     List (List Char) := Id.run do
-  -- common indentation, measured over the lines after the first
   let mut margin : Option Nat := none
   for line in lines.drop 1 do
     if !isBlank line then
@@ -114,8 +113,6 @@
       margin := some (match margin with
                       | none   => ind
                       | some m => Nat.min m ind)
-  -- strip the first line's leading whitespace; dedent each following line by the
-  -- common margin
   let mut out : List (List Char) :=
     match lines with
     | []          => []
@@ -123,8 +120,7 @@
   for line in lines.drop 1 do
     match margin with
     | none   => out := out ++ [line]
-    | some m => out := out ++ [line.drop m]
-  -- drop completely empty lines from the end, then from the beginning
+    | some m => out := out ++ [line.drop (m+1)]   -- BUG: over-dedent by 1
   out := dropTrailingEmpty out
   out := dropLeadingEmpty out
   return out
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing the indentation of a multi-line block of text.

The routine takes a block of text already split into lines (tab stops having
been expanded beforehand) and returns the block with its indentation uniformly
normalized, following the conventional rule for laying out indented text blocks:

* the first line is stripped of all of its leading whitespace;
* a single common indentation amount is determined as the smallest number of
  leading whitespace characters occurring on any non-blank line *among the lines
  that follow the first*; every line after the first then has exactly that many
  leading characters removed (lines after the first keep whatever indentation
  they have in excess of the common amount);
* if there is no non-blank line after the first, the lines after the first are
  left untouched;
* finally, completely empty lines are removed from the end of the block and then
  from the beginning of the block.

A blank line (a line whose characters are all whitespace) does not contribute to
the common indentation amount, but only a *completely empty* line (no characters
at all) is eligible for removal at the ends.

"Whitespace" here follows the ambient string library's notion of a whitespace
character (space, the various separators, no-break and other Unicode spaces),
not merely the ASCII space.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Splitting the text into
-- lines and rejoining them, and expanding tab stops, happen outside this routine
-- and are supplied/consumed at the boundary; the indentation-normalization logic
-- itself is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The whitespace code points recognized by the ambient string library's
whitespace predicate (the same set its left-strip operation removes). Kept as an
explicit table so the model matches that predicate exactly rather than only the
ASCII space. -/
def whitespaceCodes : List Nat :=
  [0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20,
   0x85, 0xa0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007,
   0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]

/-- Whether a character is whitespace under the ambient predicate. -/
def isSpaceChar (c : Char) : Bool := whitespaceCodes.contains c.toNat

/-- Number of leading whitespace characters on a line. -/
def leadingWs (l : List Char) : Nat := (l.takeWhile isSpaceChar).length

/-- A line with its leading whitespace removed. -/
def lstripWs (l : List Char) : List Char := l.dropWhile isSpaceChar

/-- A line is blank when it has no non-whitespace content. -/
def isBlank (l : List Char) : Bool := (lstripWs l).isEmpty

/-- The common indentation amount: the least leading-whitespace count over the
non-blank lines of `rest`, or `none` when `rest` has no non-blank line. -/
def marginSpec (rest : List (List Char)) : Option Nat :=
  rest.foldl (fun m line =>
    if isBlank line then m
    else some (match m with
               | none   => leadingWs line
               | some k => Nat.min k (leadingWs line))) none

/-- Strip the first line's leading whitespace and dedent every following line by
the common margin (or leave them untouched when there is no common margin). -/
def dedentSpec (margin : Option Nat) (lines : List (List Char)) : List (List Char) :=
  match lines with
  | []            => []
  | first :: rest =>
    lstripWs first :: (match margin with
                       | none   => rest
                       | some m => rest.map (·.drop m))

/-- Drop completely empty lines from the end of the block. -/
def dropTrailingEmpty (ls : List (List Char)) : List (List Char) :=
  (ls.reverse.dropWhile (· == ([] : List Char))).reverse

/-- Drop completely empty lines from the beginning of the block. -/
def dropLeadingEmpty (ls : List (List Char)) : List (List Char) :=
  ls.dropWhile (· == ([] : List Char))

/-- Functional reference for indentation normalization. -/
def normalizeIndentSpec (lines : List (List Char)) : List (List Char) :=
  dropLeadingEmpty (dropTrailingEmpty
    (dedentSpec (marginSpec (lines.drop 1)) lines))
-- pure-end

-- post-conditions-start
/-- Input→output relation for indentation normalization. `lines` is the block of
text already split into lines; `result` is the normalized block. The result is
exactly the normalized block produced by the rule above. -/
def problem_spec_normalizeIndent (lines : List (List Char))
    (result : List (List Char)) : Prop :=
  result = normalizeIndentSpec lines
-- post-conditions-end

-- impl-start
def implementation_normalizeIndent (lines : List (List Char)) :
    List (List Char) := Id.run do
  -- common indentation, measured over the lines after the first
  let mut margin : Option Nat := none
  for line in lines.drop 1 do
    if !isBlank line then
      let ind := leadingWs line
      margin := some (match margin with
                      | none   => ind
                      | some m => Nat.min m ind)
  -- strip the first line's leading whitespace; dedent each following line by the
  -- common margin
  let mut out : List (List Char) :=
    match lines with
    | []          => []
    | first :: _  => [lstripWs first]
  for line in lines.drop 1 do
    match margin with
    | none   => out := out ++ [line]
    | some m => out := out ++ [line.drop m]
  -- drop completely empty lines from the end, then from the beginning
  out := dropTrailingEmpty out
  out := dropLeadingEmpty out
  return out
-- impl-end

-- proof-start
-- @ns:fold_append_map-start
-- @decl:fold_append_map-start
theorem fold_append_map {α β : Type _} (g : α → β) (init : List β) (l : List α) :
    List.foldl (fun acc x => acc ++ [g x]) init l = init ++ l.map g := by
  induction l generalizing init with
  | nil => simp
  | cons a t ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
-- @decl:fold_append_map-end
-- @ns:fold_append_map-end

-- @ns:margin_loop_eq-start
-- @decl:margin_loop_eq-start
theorem margin_loop_eq (rest : List (List Char)) :
    List.foldl
      (fun margin line =>
        if !isBlank line then
          some (match margin with
                | none   => leadingWs line
                | some m => Nat.min m (leadingWs line))
        else margin)
      none rest = marginSpec rest := by
  unfold marginSpec
  congr 1
  funext m line
  cases isBlank line <;> simp
-- @decl:margin_loop_eq-end
-- @ns:margin_loop_eq-end

-- @ns:dedent_loop_eq-start
-- @decl:dedent_loop_eq-start
theorem dedent_loop_eq (lines : List (List Char)) (margin : Option Nat) :
    (match lines with
     | []           => []
     | first :: _   => [lstripWs first]) ++
      List.foldl
        (fun out line =>
          match margin with
          | none   => out ++ [line]
          | some m => out ++ [line.drop m])
        [] (lines.drop 1) = dedentSpec margin lines := by
  cases lines with
  | nil => simp [dedentSpec]
  | cons first rest =>
    simp only [List.drop_succ_cons, List.drop_zero, dedentSpec]
    cases margin with
    | none =>
      show [lstripWs first] ++ List.foldl (fun out line => out ++ [id line]) [] rest = _
      rw [fold_append_map (g := id)]; simp
    | some m =>
      show [lstripWs first] ++ List.foldl (fun out line => out ++ [(fun l => List.drop m l) line]) [] rest = _
      rw [fold_append_map (g := fun l => List.drop m l)]; simp
-- @decl:dedent_loop_eq-end
-- @ns:dedent_loop_eq-end

-- @ns:impl_as_folds-start
-- @decl:impl_as_folds-start
theorem impl_as_folds (lines : List (List Char)) :
    implementation_normalizeIndent lines =
      dropLeadingEmpty (dropTrailingEmpty
        ((match lines with
          | []          => []
          | first :: _  => [lstripWs first]) ++
          List.foldl
            (fun out line =>
              match
                (List.foldl
                  (fun margin line =>
                    if !isBlank line then
                      some (match margin with
                            | none   => leadingWs line
                            | some m => Nat.min m (leadingWs line))
                    else margin)
                  none (lines.drop 1)) with
              | none   => out ++ [line]
              | some m => out ++ [line.drop m])
            [] (lines.drop 1))) := by
  unfold implementation_normalizeIndent
  simp only [Id.run, bind, pure]
  simp only [← apply_ite ForInStep.yield]
  rw [List.forIn_yield_eq_foldl]
  generalize List.foldl (fun b a =>
      if (!isBlank a) = true then
        some (match b with | none => leadingWs a | some m => m.min (leadingWs a))
      else b) none (lines.drop 1) = M
  cases M with
  | none =>
    simp only []
    rw [List.forIn_yield_eq_foldl]
    rw [fold_append_map (fun a => a), fold_append_map (fun a => a)]
    simp
  | some m =>
    simp only []
    rw [List.forIn_yield_eq_foldl]
    rw [fold_append_map (fun a : List Char => a.drop m),
        fold_append_map (fun a : List Char => a.drop m)]
    simp
-- @decl:impl_as_folds-end
-- @ns:impl_as_folds-end


theorem correct_normalizeIndent :
    ∀ (lines : List (List Char)),
      problem_spec_normalizeIndent lines
        (implementation_normalizeIndent lines) := by
  intro lines
  unfold problem_spec_normalizeIndent
  rw [impl_as_folds]
  simp only [margin_loop_eq]
  unfold normalizeIndentSpec
  congr 1
  congr 1
  rcases h : marginSpec (lines.drop 1) with _ | m
  · exact dedent_loop_eq lines none
  · exact dedent_loop_eq lines (some m)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: For the lean backend, _lean_spec_view collapses BOTH the impl AND proof regions to placeholders, so same_spec pins imports/docstring/axioms/pure/post. The postcondition problem_spec_normalizeIndent is EXACT total functional equality: result = normalizeIndentSpec lines, and normalizeIndentSpec is defined in the pinned `pure` region. Hence any impl whose proof closes must be extensionally equal to normalizeIndentSpec on ALL inputs -- a maximally tight spec. All 8 attacks confirmed same_spec=True (swebench_unified.markers.same_spec, lean backend). Positive control (unmodified impl+proof) verifies: lean_verify exit 0.

### ATTACKS (all, cmd: bash scripts/lean_verify.sh <f>; run concurrently <=4):
- atk_1 PREPATCH BUG (margin folded over `lines` incl. first line, not `lines.drop 1`): exit 1 (rewrite failed at :217/:222). REJECTED. This reproduces the issue bug: flush-left first line collapses margin to 0, following lines not dedented.
- atk_2 PARTIAL-DOMAIN (dropLeadingEmpty omitted): exit 1. REJECTED.
- atk_3 BOUNDARY off-by-one (margin over lines.drop 2): exit 1. REJECTED.
- atk_4 CONTROL-FLOW EFFECT (first line NOT lstripped): exit 1. REJECTED.
- atk_5 CONTROL-FLOW EFFECT (first line also dedented by margin): exit 1 (unsolved goals). REJECTED.
- atk_6 WRONG-OP (Nat.max instead of Nat.min for margin): exit 1. REJECTED.
- atk_8 BOUNDARY (over-dedent line.drop (m+1)): exit 1. REJECTED.
- atk_7 UNGROUNDED-ORACLE ECHO (implementation := normalizeIndentSpec lines, proof closed by rfl): exit 0 VERIFIES. `#print axioms correct_normalizeIndent` => 'does not depend on any axioms' (CLEAN). Per protocol materialized its faithful refined patch (= the inspect.cleandoc gold patch, since the echo computes EXACTLY the modeled function) and RAN it through the official harness via swebench_unified.harness.run_resolve('django__django-12155', patch): completed=True resolved=True attempts=1 flaky=False (note='resolved'). Report: FAIL_TO_PASS test_parse_rst_with_docstring_no_leading_line_feed -> success; all 6 PASS_TO_PASS success. => a CORRECT ECHO (verifies AND its patch resolves), NOT a weakness -- exactly the G-PANEL-1 echo-attack policy case.

No verifying impl has a faithful patch that fails to resolve => spec is NOT broken.

REFINEMENT.MD AUDIT: 9 legs. Leg 8 = R (carrier List (List Char) <-> s.expandtabs().split('\n')). Legs 0-7 = A-reference (isSpaceChar/whitespaceCodes, margin over lines[1:], isBlank guard, first-line lstrip, drop m, margin=none untouched, dropTrailingEmpty, dropLeadingEmpty), each mapped to a concrete post-patch inspect.cleandoc op. NO A-consumed axiom (axioms region is empty/comment-only, G-AX skip), NO I-only/kind-3 leg. The single load-bearing A-reference correspondence (normalizeIndentSpec <-> inspect.cleandoc) is validated deeply by G-CONF (conformance_check.py: SEED 20240629, N=120000 + 20 edge incl. CRLF/formfeed/NBSP/vtab/ASCII-sep; oracle=REAL inspect.cleandoc). I INDEPENDENTLY re-ran a wider differential (300000 random inputs, alphabet incl. \t \r \x0c \x0b \xa0 \x1c \x85 and newlines) shadow-vs-real-cleandoc: 0 disagreements. Correspondence holds.

CONCLUSION: verify => correct holds on this bundle. The only verifying same-spec impl is the gold echo whose patch RESOLVES. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 8 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing the indentation of a multi-line block of text.

The routine takes a block of text already split into lines (tab stops having
been expanded beforehand) and returns the block with its indentation uniformly
normalized, following the conventional rule for laying out indented text blocks:

* the first line is stripped of all of its leading whitespace;
* a single common indentation amount is determined as the smallest number of
  leading whitespace characters occurring on any non-blank line *among the lines
  that follow the first*; every line after the first then has exactly that many
  leading characters removed (lines after the first keep whatever indentation
  they have in excess of the common amount);
* if there is no non-blank line after the first, the lines after the first are
  left untouched;
* finally, completely empty lines are removed from the end of the block and then
  from the beginning of the block.

A blank line (a line whose characters are all whitespace) does not contribute to
the common indentation amount, but only a *completely empty* line (no characters
at all) is eligible for removal at the ends.

"Whitespace" here follows the ambient string library's notion of a whitespace
character (space, the various separators, no-break and other Unicode spaces),
not merely the ASCII space.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Splitting the text into
-- lines and rejoining them, and expanding tab stops, happen outside this routine
-- and are supplied/consumed at the boundary; the indentation-normalization logic
-- itself is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The whitespace code points recognized by the ambient string library's
whitespace predicate (the same set its left-strip operation removes). Kept as an
explicit table so the model matches that predicate exactly rather than only the
ASCII space. -/
def whitespaceCodes : List Nat :=
  [0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20,
   0x85, 0xa0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007,
   0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]

/-- Whether a character is whitespace under the ambient predicate. -/
def isSpaceChar (c : Char) : Bool := whitespaceCodes.contains c.toNat

/-- Number of leading whitespace characters on a line. -/
def leadingWs (l : List Char) : Nat := (l.takeWhile isSpaceChar).length

/-- A line with its leading whitespace removed. -/
def lstripWs (l : List Char) : List Char := l.dropWhile isSpaceChar

/-- A line is blank when it has no non-whitespace content. -/
def isBlank (l : List Char) : Bool := (lstripWs l).isEmpty

/-- The common indentation amount: the least leading-whitespace count over the
non-blank lines of `rest`, or `none` when `rest` has no non-blank line. -/
def marginSpec (rest : List (List Char)) : Option Nat :=
  rest.foldl (fun m line =>
    if isBlank line then m
    else some (match m with
               | none   => leadingWs line
               | some k => Nat.min k (leadingWs line))) none

/-- Strip the first line's leading whitespace and dedent every following line by
the common margin (or leave them untouched when there is no common margin). -/
def dedentSpec (margin : Option Nat) (lines : List (List Char)) : List (List Char) :=
  match lines with
  | []            => []
  | first :: rest =>
    lstripWs first :: (match margin with
                       | none   => rest
                       | some m => rest.map (·.drop m))

/-- Drop completely empty lines from the end of the block. -/
def dropTrailingEmpty (ls : List (List Char)) : List (List Char) :=
  (ls.reverse.dropWhile (· == ([] : List Char))).reverse

/-- Drop completely empty lines from the beginning of the block. -/
def dropLeadingEmpty (ls : List (List Char)) : List (List Char) :=
  ls.dropWhile (· == ([] : List Char))

/-- Functional reference for indentation normalization. -/
def normalizeIndentSpec (lines : List (List Char)) : List (List Char) :=
  dropLeadingEmpty (dropTrailingEmpty
    (dedentSpec (marginSpec (lines.drop 1)) lines))
-- pure-end

-- post-conditions-start
/-- Input→output relation for indentation normalization. `lines` is the block of
text already split into lines; `result` is the normalized block. The result is
exactly the normalized block produced by the rule above. -/
def problem_spec_normalizeIndent (lines : List (List Char))
    (result : List (List Char)) : Prop :=
  result = normalizeIndentSpec lines
-- post-conditions-end

-- impl-start
def implementation_normalizeIndent (lines : List (List Char)) :
    List (List Char) := Id.run do
  -- common indentation, measured over the lines after the first
  let mut margin : Option Nat := none
  for line in lines.drop 1 do
    if !isBlank line then
      let ind := leadingWs line
      margin := some (match margin with
                      | none   => ind
                      | some m => Nat.min m ind)
  -- strip the first line's leading whitespace; dedent each following line by the
  -- common margin
  let mut out : List (List Char) :=
    match lines with
    | []          => []
    | first :: _  => [lstripWs first]
  for line in lines.drop 1 do
    match margin with
    | none   => out := out ++ [line]
    | some m => out := out ++ [line.drop m]
  -- drop completely empty lines from the end, then from the beginning
  out := dropTrailingEmpty out
  out := dropLeadingEmpty out
  return out
-- impl-end

-- proof-start
-- @ns:fold_append_map-start
-- @decl:fold_append_map-start
theorem fold_append_map {α β : Type _} (g : α → β) (init : List β) (l : List α) :
    List.foldl (fun acc x => acc ++ [g x]) init l = init ++ l.map g := by
  induction l generalizing init with
  | nil => simp
  | cons a t ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
-- @decl:fold_append_map-end
-- @ns:fold_append_map-end

-- @ns:margin_loop_eq-start
-- @decl:margin_loop_eq-start
theorem margin_loop_eq (rest : List (List Char)) :
    List.foldl
      (fun margin line =>
        if !isBlank line then
          some (match margin with
                | none   => leadingWs line
                | some m => Nat.min m (leadingWs line))
        else margin)
      none rest = marginSpec rest := by
  unfold marginSpec
  congr 1
  funext m line
  cases isBlank line <;> simp
-- @decl:margin_loop_eq-end
-- @ns:margin_loop_eq-end

-- @ns:dedent_loop_eq-start
-- @decl:dedent_loop_eq-start
theorem dedent_loop_eq (lines : List (List Char)) (margin : Option Nat) :
    (match lines with
     | []           => []
     | first :: _   => [lstripWs first]) ++
      List.foldl
        (fun out line =>
          match margin with
          | none   => out ++ [line]
          | some m => out ++ [line.drop m])
        [] (lines.drop 1) = dedentSpec margin lines := by
  cases lines with
  | nil => simp [dedentSpec]
  | cons first rest =>
    simp only [List.drop_succ_cons, List.drop_zero, dedentSpec]
    cases margin with
    | none =>
      show [lstripWs first] ++ List.foldl (fun out line => out ++ [id line]) [] rest = _
      rw [fold_append_map (g := id)]; simp
    | some m =>
      show [lstripWs first] ++ List.foldl (fun out line => out ++ [(fun l => List.drop m l) line]) [] rest = _
      rw [fold_append_map (g := fun l => List.drop m l)]; simp
-- @decl:dedent_loop_eq-end
-- @ns:dedent_loop_eq-end

-- @ns:impl_as_folds-start
-- @decl:impl_as_folds-start
theorem impl_as_folds (lines : List (List Char)) :
    implementation_normalizeIndent lines =
      dropLeadingEmpty (dropTrailingEmpty
        ((match lines with
          | []          => []
          | first :: _  => [lstripWs first]) ++
          List.foldl
            (fun out line =>
              match
                (List.foldl
                  (fun margin line =>
                    if !isBlank line then
                      some (match margin with
                            | none   => leadingWs line
                            | some m => Nat.min m (leadingWs line))
                    else margin)
                  none (lines.drop 1)) with
              | none   => out ++ [line]
              | some m => out ++ [line.drop m])
            [] (lines.drop 1))) := by
  unfold implementation_normalizeIndent
  simp only [Id.run, bind, pure]
  simp only [← apply_ite ForInStep.yield]
  rw [List.forIn_yield_eq_foldl]
  generalize List.foldl (fun b a =>
      if (!isBlank a) = true then
        some (match b with | none => leadingWs a | some m => m.min (leadingWs a))
      else b) none (lines.drop 1) = M
  cases M with
  | none =>
    simp only []
    rw [List.forIn_yield_eq_foldl]
    rw [fold_append_map (fun a => a), fold_append_map (fun a => a)]
    simp
  | some m =>
    simp only []
    rw [List.forIn_yield_eq_foldl]
    rw [fold_append_map (fun a : List Char => a.drop m),
        fold_append_map (fun a : List Char => a.drop m)]
    simp
-- @decl:impl_as_folds-end
-- @ns:impl_as_folds-end


theorem correct_normalizeIndent :
    ∀ (lines : List (List Char)),
      problem_spec_normalizeIndent lines
        (implementation_normalizeIndent lines) := by
  intro lines
  unfold problem_spec_normalizeIndent
  rw [impl_as_folds]
  simp only [margin_loop_eq]
  unfold normalizeIndentSpec
  congr 1
  congr 1
  rcases h : marginSpec (lines.drop 1) with _ | m
  · exact dedent_loop_eq lines none
  · exact dedent_loop_eq lines (some m)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: For the lean backend, _lean_spec_view collapses BOTH the impl AND proof regions to placeholders, so same_spec pins imports/docstring/axioms/pure/post. The postcondition problem_spec_normalizeIndent is EXACT total functional equality: result = normalizeIndentSpec lines, and normalizeIndentSpec is defined in the pinned `pure` region. Hence any impl whose proof closes must be extensionally equal to normalizeIndentSpec on ALL inputs -- a maximally tight spec. All 8 attacks confirmed same_spec=True (swebench_unified.markers.same_spec, lean backend). Positive control (unmodified impl+proof) verifies: lean_verify exit 0.

### ATTACKS (all, cmd: bash scripts/lean_verify.sh <f>; run concurrently <=4):
- atk_1 PREPATCH BUG (margin folded over `lines` incl. first line, not `lines.drop 1`): exit 1 (rewrite failed at :217/:222). REJECTED. This reproduces the issue bug: flush-left first line collapses margin to 0, following lines not dedented.
- atk_2 PARTIAL-DOMAIN (dropLeadingEmpty omitted): exit 1. REJECTED.
- atk_3 BOUNDARY off-by-one (margin over lines.drop 2): exit 1. REJECTED.
- atk_4 CONTROL-FLOW EFFECT (first line NOT lstripped): exit 1. REJECTED.
- atk_5 CONTROL-FLOW EFFECT (first line also dedented by margin): exit 1 (unsolved goals). REJECTED.
- atk_6 WRONG-OP (Nat.max instead of Nat.min for margin): exit 1. REJECTED.
- atk_8 BOUNDARY (over-dedent line.drop (m+1)): exit 1. REJECTED.
- atk_7 UNGROUNDED-ORACLE ECHO (implementation := normalizeIndentSpec lines, proof closed by rfl): exit 0 VERIFIES. `#print axioms correct_normalizeIndent` => 'does not depend on any axioms' (CLEAN). Per protocol materialized its faithful refined patch (= the inspect.cleandoc gold patch, since the echo computes EXACTLY the modeled function) and RAN it through the official harness via swebench_unified.harness.run_resolve('django__django-12155', patch): completed=True resolved=True attempts=1 flaky=False (note='resolved'). Report: FAIL_TO_PASS test_parse_rst_with_docstring_no_leading_line_feed -> success; all 6 PASS_TO_PASS success. => a CORRECT ECHO (verifies AND its patch resolves), NOT a weakness -- exactly the G-PANEL-1 echo-attack policy case.

No verifying impl has a faithful patch that fails to resolve => spec is NOT broken.

REFINEMENT.MD AUDIT: 9 legs. Leg 8 = R (carrier List (List Char) <-> s.expandtabs().split('\n')). Legs 0-7 = A-reference (isSpaceChar/whitespaceCodes, margin over lines[1:], isBlank guard, first-line lstrip, drop m, margin=none untouched, dropTrailingEmpty, dropLeadingEmpty), each mapped to a concrete post-patch inspect.cleandoc op. NO A-consumed axiom (axioms region is empty/comment-only, G-AX skip), NO I-only/kind-3 leg. The single load-bearing A-reference correspondence (normalizeIndentSpec <-> inspect.cleandoc) is validated deeply by G-CONF (conformance_check.py: SEED 20240629, N=120000 + 20 edge incl. CRLF/formfeed/NBSP/vtab/ASCII-sep; oracle=REAL inspect.cleandoc). I INDEPENDENTLY re-ran a wider differential (300000 random inputs, alphabet incl. \t \r \x0c \x0b \xa0 \x1c \x85 and newlines) shadow-vs-real-cleandoc: 0 disagreements. Correspondence holds.

CONCLUSION: verify => correct holds on this bundle. The only verifying same-spec impl is the gold echo whose patch RESOLVES. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec vs real repo callee) verified for django__django-12155 (lean). The modeled function normalizeIndentSpec/implementation_normalizeIndent models the post-patch behavior — the docstring indentation normalization now performed via inspect.cleandoc (PEP 257), replacing the buggy hand-rolled trim_docstring (mapping.md site A utils.py:27-39, site B views.py). The real callee is stdlib inspect.cleandoc, used as the oracle in conformance_check.py.

Checks performed:
1. same_spec (spec_signature) post vs pre-patch = True; spec region parses cleanly. Spec view stable.
2. Solution.lean compiles via lean_verify.sh (exit 0, no sorry). `#print axioms correct_normalizeIndent` = [propext, Quot.sound] — NO sorryAx, the proof is real (only harmless forIn_yield_eq_foldl deprecation warnings). impl↔spec proof (impl_as_folds/margin_loop_eq/dedent_loop_eq) genuinely closes.
3. Whitespace set exactness: Lean whitespaceCodes (29 code points) == Python's full str.isspace() set == the exact set str.lstrip() removes over all 0x110000 code points (verified all three equal). This is the crux — cleandoc uses lstrip()/`not line` over the FULL whitespace set, and the model mirrors it exactly (correcting a prior ASCII-only Role-3 defect).
4. Algorithm match: cleandoc source (margin=min indent over lines[1:] non-blank; lines[0].lstrip(); dedent i>=1 by margin; drop trailing then leading empty '') is transliterated op-for-op into the shadow and matches the Lean defs (marginSpec over lines.drop 1, lstripWs first, .drop m, dropTrailingEmpty then dropLeadingEmpty).
5. Independent differential fuzz beyond the bundled alphabet: 2,000,000 random inputs over an alphabet containing EVERY unicode whitespace char + letters + heavy newlines; plus 500,000 structured indent+body line inputs with unicode-whitespace prefixes — 0 disagreements vs real inspect.cleandoc. Bundled conformance (120,020 inputs) also passes.
6. Corner cases: lone surrogates (\ud800) — real cleandoc's expandtabs does not raise here on this Python; oracle and shadow agree. Empty string agrees. F2P behavior (issue: 'firstline\n\n    second line' must dedent the indented later line) reproduced and matches.

No input found where the spec disagrees with the real repo behavior. The spec is neither too strong nor drifted: it is a deep, faithful model of the patched callee. Note: this bundle predates the G-CONF-required policy but conformance_check.py is present and passes; carrier correspondence (expandtabs+split/join) is bridged there and consistent with real cleandoc's own expandtabs/split.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the projected spec view (computed via markers.spec_view + leakage.screen; mechanical screen passes clean: no diff markers, no reproduced gold-patch lines, no patched file/module path, no patched-symbol identifier/comment echo, no bug/fix narration).

Semantic assessment (leakage / gold-reconstruction) vs the SOLVER-VISIBLE problem_statement ONLY:

1. The discriminating behavior the spec encodes — that the common indentation is measured over the lines AFTER the first (spec doc: 'the smallest number of leading whitespace characters occurring on any non-blank line *among the lines that follow the first*') — is ALREADY PUBLIC in problem_statement. The issue text verbatim gives the buggy line `indent = min(len(line) - len(line.lstrip()) for line in lines if line.lstrip())`, states 'The problem is that the indentation of the first line is 0', and gives 'The solution is to skip the first line: ... for line in lines[1:] ...'. So the spec reveals nothing beyond the publicly-disclosed fix discriminator.

2. The spec view is in fact MORE abstract than problem_statement: it never names the gold edit's substance — no `trim_docstring`, `parse_docstring`, `inspect.cleandoc`, `docstring`, `admindocs`, `PEP 257`, no patched file paths, and no mention that the fix is 'switch to cleandoc'. It describes a generic 'indentation normalization of a multi-line block of text' as an input→output relation. A solver reading only the spec could not reconstruct the specific gold edit (import + delete trim_docstring + call cleandoc) — it only learns the abstract normalization behavior, which is exactly what a faithful behavioral spec should convey.

3. Extra spec details (leading/trailing empty-line removal, the full str.isspace() whitespace set, no-margin case) are faithful behavioral descriptions of the normalization; none of them localizes or names the edit or leaks gold specifics beyond problem_statement.

4. Comments/docstrings in the view are abstract ('the ambient string library's whitespace predicate', 'the conventional rule for laying out indented text blocks') and carry no bug/fix narration or patched-symbol names.

Conclusion: no line in the spec view leaks the gold edit beyond the already-public problem_statement (hints_text, which additionally mentions cleandoc, was correctly NOT used as the leakage baseline).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

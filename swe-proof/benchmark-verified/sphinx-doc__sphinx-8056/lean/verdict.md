# P2 adversarial audit — sphinx-doc__sphinx-8056

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_notrim.lean`, `atk_3_noguard.lean`, `atk_4_dropdesc.lean`, `atk_5_headpiece.lean`, `atk_6_leadtrim.lean`, `atk_7_reversed.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition problem_spec_normalizeEntries is an EXACT functional equality: result = raws.flatMap (expandEntry splitGrouped), over fully concrete pure functions (expandEntry/commaPieces/trim/isBlank). It completely pins the output, so any verifying implementation must be provably output-identical to the gold expression. No same-spec wrong impl can close any proof (the theorem statement becomes a false equality), hence there is no verifying-wrong-impl to materialize a patch for — verify=>correct holds. Discriminating input for the prepatch/no-guard bug: splitGrouped=true, raws=[(['a',',','b'], [], [])] -> gold yields [(['a'],[],[]),(['b'],[],[])] (2 trimmed pieces) while prepatch yields [(['a',',','b'],[],[])]; for the no-trim bug: raws=[([' ','a'],[],[])], splitGrouped=true -> gold trims to ['a'], no-trim keeps [' ','a'].
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,10 +91,7 @@
   let mut fields : List FieldEntry := []
   for f in raws do
     let (name, typ, desc) := f
-    if splitGrouped && (name != []) then
-      for piece in commaPieces name do
-        fields := fields ++ [(trim piece, typ, desc)]
-    else if (name != []) || (typ != []) || (desc != []) then
+    if (name != []) || (typ != []) || (desc != []) then
       fields := fields ++ [(name, typ, desc)]
   return fields
 -- impl-end
@@ -108,7 +105,6 @@
   intro splitGrouped raws
   unfold problem_spec_normalizeEntries implementation_normalizeEntries
   simp only [Id.run]
-  -- inner loop over comma pieces accumulates a map/append
   have inner : ∀ (pieces : List (List Char)) (typ : List Char) (desc : List (List Char))
       (acc : List FieldEntry),
       (forIn (m := Id) pieces acc
@@ -122,7 +118,6 @@
       show (forIn rest (acc ++ [(trim p, typ, desc)]) fun piece r =>
         pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))) = _
       rw [ih]; simp [List.append_assoc]
-  -- main loop
   have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),
       (forIn (m := Id) rs acc
         (fun f r =>
@@ -166,6 +161,4 @@
           simp only [List.nil_append]
   have := key raws []
   simpa using this
-
-
 -- proof-end
```

Attack 2 — `atk_2_notrim.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,7 +93,7 @@
     let (name, typ, desc) := f
     if splitGrouped && (name != []) then
       for piece in commaPieces name do
-        fields := fields ++ [(trim piece, typ, desc)]
+        fields := fields ++ [(piece, typ, desc)]
     else if (name != []) || (typ != []) || (desc != []) then
       fields := fields ++ [(name, typ, desc)]
   return fields
@@ -108,7 +108,6 @@
   intro splitGrouped raws
   unfold problem_spec_normalizeEntries implementation_normalizeEntries
   simp only [Id.run]
-  -- inner loop over comma pieces accumulates a map/append
   have inner : ∀ (pieces : List (List Char)) (typ : List Char) (desc : List (List Char))
       (acc : List FieldEntry),
       (forIn (m := Id) pieces acc
@@ -122,7 +121,6 @@
       show (forIn rest (acc ++ [(trim p, typ, desc)]) fun piece r =>
         pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))) = _
       rw [ih]; simp [List.append_assoc]
-  -- main loop
   have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),
       (forIn (m := Id) rs acc
         (fun f r =>
@@ -166,6 +164,4 @@
           simp only [List.nil_append]
   have := key raws []
   simpa using this
-
-
 -- proof-end
```

Attack 3 — `atk_3_noguard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,7 @@
   let mut fields : List FieldEntry := []
   for f in raws do
     let (name, typ, desc) := f
-    if splitGrouped && (name != []) then
+    if (name != []) then
       for piece in commaPieces name do
         fields := fields ++ [(trim piece, typ, desc)]
     else if (name != []) || (typ != []) || (desc != []) then
@@ -108,7 +108,6 @@
   intro splitGrouped raws
   unfold problem_spec_normalizeEntries implementation_normalizeEntries
   simp only [Id.run]
-  -- inner loop over comma pieces accumulates a map/append
   have inner : ∀ (pieces : List (List Char)) (typ : List Char) (desc : List (List Char))
       (acc : List FieldEntry),
       (forIn (m := Id) pieces acc
@@ -122,7 +121,6 @@
       show (forIn rest (acc ++ [(trim p, typ, desc)]) fun piece r =>
         pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))) = _
       rw [ih]; simp [List.append_assoc]
-  -- main loop
   have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),
       (forIn (m := Id) rs acc
         (fun f r =>
@@ -166,6 +164,4 @@
           simp only [List.nil_append]
   have := key raws []
   simpa using this
-
-
 -- proof-end
```

Attack 4 — `atk_4_dropdesc.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,7 @@
     if splitGrouped && (name != []) then
       for piece in commaPieces name do
         fields := fields ++ [(trim piece, typ, desc)]
-    else if (name != []) || (typ != []) || (desc != []) then
+    else if (name != []) || (typ != []) then
       fields := fields ++ [(name, typ, desc)]
   return fields
 -- impl-end
@@ -108,7 +108,6 @@
   intro splitGrouped raws
   unfold problem_spec_normalizeEntries implementation_normalizeEntries
   simp only [Id.run]
-  -- inner loop over comma pieces accumulates a map/append
   have inner : ∀ (pieces : List (List Char)) (typ : List Char) (desc : List (List Char))
       (acc : List FieldEntry),
       (forIn (m := Id) pieces acc
@@ -122,7 +121,6 @@
       show (forIn rest (acc ++ [(trim p, typ, desc)]) fun piece r =>
         pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))) = _
       rw [ih]; simp [List.append_assoc]
-  -- main loop
   have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),
       (forIn (m := Id) rs acc
         (fun f r =>
@@ -166,6 +164,4 @@
           simp only [List.nil_append]
   have := key raws []
   simpa using this
-
-
 -- proof-end
```

Attack 5 — `atk_5_headpiece.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,8 +92,9 @@
   for f in raws do
     let (name, typ, desc) := f
     if splitGrouped && (name != []) then
-      for piece in commaPieces name do
-        fields := fields ++ [(trim piece, typ, desc)]
+      match commaPieces name with
+      | piece :: _ => fields := fields ++ [(trim piece, typ, desc)]
+      | [] => pure ()
     else if (name != []) || (typ != []) || (desc != []) then
       fields := fields ++ [(name, typ, desc)]
   return fields
@@ -108,7 +109,6 @@
   intro splitGrouped raws
   unfold problem_spec_normalizeEntries implementation_normalizeEntries
   simp only [Id.run]
-  -- inner loop over comma pieces accumulates a map/append
   have inner : ∀ (pieces : List (List Char)) (typ : List Char) (desc : List (List Char))
       (acc : List FieldEntry),
       (forIn (m := Id) pieces acc
@@ -122,7 +122,6 @@
       show (forIn rest (acc ++ [(trim p, typ, desc)]) fun piece r =>
         pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))) = _
       rw [ih]; simp [List.append_assoc]
-  -- main loop
   have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),
       (forIn (m := Id) rs acc
         (fun f r =>
@@ -166,6 +165,4 @@
           simp only [List.nil_append]
   have := key raws []
   simpa using this
-
-
 -- proof-end
```

Attack 6 — `atk_6_leadtrim.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,7 +93,7 @@
     let (name, typ, desc) := f
     if splitGrouped && (name != []) then
       for piece in commaPieces name do
-        fields := fields ++ [(trim piece, typ, desc)]
+        fields := fields ++ [(piece.dropWhile isBlank, typ, desc)]
     else if (name != []) || (typ != []) || (desc != []) then
       fields := fields ++ [(name, typ, desc)]
   return fields
@@ -108,7 +108,6 @@
   intro splitGrouped raws
   unfold problem_spec_normalizeEntries implementation_normalizeEntries
   simp only [Id.run]
-  -- inner loop over comma pieces accumulates a map/append
   have inner : ∀ (pieces : List (List Char)) (typ : List Char) (desc : List (List Char))
       (acc : List FieldEntry),
       (forIn (m := Id) pieces acc
@@ -122,7 +121,6 @@
       show (forIn rest (acc ++ [(trim p, typ, desc)]) fun piece r =>
         pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))) = _
       rw [ih]; simp [List.append_assoc]
-  -- main loop
   have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),
       (forIn (m := Id) rs acc
         (fun f r =>
@@ -166,6 +164,4 @@
           simp only [List.nil_append]
   have := key raws []
   simpa using this
-
-
 -- proof-end
```

Attack 7 — `atk_7_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,9 +93,9 @@
     let (name, typ, desc) := f
     if splitGrouped && (name != []) then
       for piece in commaPieces name do
-        fields := fields ++ [(trim piece, typ, desc)]
+        fields := (trim piece, typ, desc) :: fields
     else if (name != []) || (typ != []) || (desc != []) then
-      fields := fields ++ [(name, typ, desc)]
+      fields := (name, typ, desc) :: fields
   return fields
 -- impl-end
 
@@ -108,7 +108,6 @@
   intro splitGrouped raws
   unfold problem_spec_normalizeEntries implementation_normalizeEntries
   simp only [Id.run]
-  -- inner loop over comma pieces accumulates a map/append
   have inner : ∀ (pieces : List (List Char)) (typ : List Char) (desc : List (List Char))
       (acc : List FieldEntry),
       (forIn (m := Id) pieces acc
@@ -122,7 +121,6 @@
       show (forIn rest (acc ++ [(trim p, typ, desc)]) fun piece r =>
         pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))) = _
       rw [ih]; simp [List.append_assoc]
-  -- main loop
   have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),
       (forIn (m := Id) rs acc
         (fun f r =>
@@ -166,6 +164,4 @@
           simp only [List.nil_append]
   have := key raws []
   simpa using this
-
-
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing a sequence of documented item entries.

A documentation block describes a list of items. Each raw entry, as read from the
block, is a triple `(name, type, description)`: a name (a sequence of characters),
a type (a sequence of characters), and a description (a sequence of text lines).

Producing the normalized entry list applies, to each raw entry in order, one rule:

* When grouping is enabled and the entry has a non-empty name, the name may itself
  denote several items written together and separated by commas (for example a
  single line introducing `a, b`). Such an entry expands into one normalized entry
  per comma-separated piece: each piece, with surrounding blank characters removed,
  paired with the shared type and the shared description.
* Otherwise the entry is kept as a single normalized entry, provided it carries
  some content (a non-empty name, type, or description); a wholly empty entry
  contributes nothing.

The normalized list is the in-order concatenation of every raw entry's expansion.
-/

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature. The reading of raw entries and
-- the detection of the block boundary are unchanged bookkeeping and are abstracted
-- into the input list `raws`. The two character-level operations the rule performs
-- (separating a name on commas, and trimming surrounding blank characters) are
-- modeled directly in the `pure` region and differential-tested against their real
-- library counterparts by conformance_check.py. No consumed axioms.
-- axioms-end

-- pure-start
/-- A raw / normalized documented item entry: a name, a type, and a description
(a list of text lines). -/
abbrev FieldEntry := List Char × List Char × List (List Char)

/-- Blank characters trimmed from the ends of a separated name piece: exactly the
code points Python's bare `str.strip()` removes (the `str.isspace` set) —
U+0009–U+000D, U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028,
U+2029, U+202F, U+205F, and U+3000. -/
def isBlank (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || (0x1c ≤ n && n ≤ 0x20) ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) ||
  n == 0x2028 || n == 0x2029 || n == 0x202f || n == 0x205f || n == 0x3000

/-- Remove leading and trailing blank characters from a sequence. -/
def trim (cs : List Char) : List Char :=
  ((cs.dropWhile isBlank).reverse.dropWhile isBlank).reverse

/-- Separate a name into the comma-delimited pieces it is written as. A name with
no comma yields the single piece `[name]`; each comma starts a new piece, so an
empty piece is produced for an absent segment (mirroring delimiter-based string
splitting, which always yields at least one piece). -/
def commaPieces : List Char → List (List Char)
  | [] => [[]]
  | ',' :: cs => [] :: commaPieces cs
  | c :: cs =>
    match commaPieces cs with
    | h :: t => (c :: h) :: t
    | [] => [[c]]

/-- Expansion of one raw entry into its normalized entries, under the grouping
flag. With grouping and a non-empty name, the name is separated on commas and each
trimmed piece becomes an entry with the shared type and description; otherwise a
single entry is kept iff it has any content. -/
def expandEntry (splitGrouped : Bool) (f : FieldEntry) : List FieldEntry :=
  let (name, typ, desc) := f
  if splitGrouped && (name != []) then
    (commaPieces name).map (fun piece => (trim piece, typ, desc))
  else if (name != []) || (typ != []) || (desc != []) then
    [(name, typ, desc)]
  else
    []
-- pure-end

-- post-conditions-start
/-- The normalized entry list is the in-order concatenation of every raw entry's
expansion under the grouping flag. -/
def problem_spec_normalizeEntries
    (splitGrouped : Bool) (raws : List FieldEntry) (result : List FieldEntry) : Prop :=
  result = raws.flatMap (expandEntry splitGrouped)
-- post-conditions-end

-- impl-start
def implementation_normalizeEntries
    (splitGrouped : Bool) (raws : List FieldEntry) : List FieldEntry := Id.run do
  let mut fields : List FieldEntry := []
  for f in raws do
    let (name, typ, desc) := f
    if splitGrouped && (name != []) then
      for piece in commaPieces name do
        fields := fields ++ [(trim piece, typ, desc)]
    else if (name != []) || (typ != []) || (desc != []) then
      fields := fields ++ [(name, typ, desc)]
  return fields
-- impl-end


-- proof-start
theorem correct_normalizeEntries :
    ∀ (splitGrouped : Bool) (raws : List FieldEntry),
      problem_spec_normalizeEntries splitGrouped raws
        (implementation_normalizeEntries splitGrouped raws) := by
  intro splitGrouped raws
  unfold problem_spec_normalizeEntries implementation_normalizeEntries
  simp only [Id.run]
  have inner : ∀ (pieces : List (List Char)) (typ : List Char) (desc : List (List Char))
      (acc : List FieldEntry),
      (forIn (m := Id) pieces acc
        (fun piece r => pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))))
        = acc ++ pieces.map (fun piece => (trim piece, typ, desc)) := by
    intro pieces typ desc acc
    induction pieces generalizing acc with
    | nil => simp; rfl
    | cons p rest ih =>
      rw [List.forIn_cons]
      show (forIn rest (acc ++ [(trim p, typ, desc)]) fun piece r =>
        pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))) = _
      rw [ih]; simp [List.append_assoc]
  have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),
      (forIn (m := Id) rs acc
        (fun f r =>
          if (splitGrouped && f.1 != []) = true then do
            let r ← forIn (commaPieces f.1) r fun piece r => do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [(trim piece, f.2.1, f.2.2)]))
            pure PUnit.unit
            pure (ForInStep.yield r)
          else
            if (f.1 != [] || f.2.1 != [] || f.2.2 != []) = true then do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(f.1, f.2.1, f.2.2)]))
            else do
              pure PUnit.unit
              pure (ForInStep.yield r)))
        = acc ++ rs.flatMap (expandEntry splitGrouped) := by
    intro rs acc
    induction rs generalizing acc with
    | nil => simp; rfl
    | cons f rest ih =>
      rw [List.forIn_cons]
      simp only [expandEntry, List.flatMap_cons]
      by_cases h1 : (splitGrouped && f.1 != []) = true
      · simp only [h1, if_true]
        show (forIn rest _ _) = _
        rw [show (forIn (m:=Id) (commaPieces f.1) acc fun piece r => do
                  pure PUnit.unit
                  pure (ForInStep.yield (r ++ [(trim piece, f.2.1, f.2.2)]))) = _ from inner _ _ _ _]
        rw [ih]
        simp only [List.append_assoc]
      · simp only [h1, Bool.false_eq_true, if_false]
        by_cases h2 : (f.1 != [] || f.2.1 != [] || f.2.2 != []) = true
        · simp only [h2, if_true]
          show (forIn rest _ _) = _
          rw [ih]
          simp only [List.append_assoc, List.cons_append, List.nil_append]
        · simp only [h2, Bool.false_eq_true, if_false]
          show (forIn rest _ _) = _
          rw [ih]
          simp only [List.nil_append]
  have := key raws []
  simpa using this
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Commands: `bash scripts/lean_verify.sh <file>` from project root, run concurrently in 2 batches of 4.

### Results
- pos_control (gold impl, gold proof): EXIT 0 (verifies, no sorry). `#print axioms correct_normalizeEntries` => [propext, Quot.sound] — CLEAN (no sorryAx / no custom axioms).
- atk_1_prepatch (ignores splitGrouped; THE real prepatch bug): EXIT 1, genuine 'error: Type mismatch: After simplification' — proof cannot close.
- atk_2_notrim (emit piece without trim): EXIT 1, type-mismatch error.
- atk_3_noguard (split whenever name nonempty, ignoring flag): EXIT 1.
- atk_4_dropdesc (boundary: keep-if branch drops the desc disjunct: name||typ only): EXIT 1.
- atk_5_headpiece (partial-domain: only first comma piece kept): EXIT 1.
- atk_6_leadtrim (control-flow/partial: dropWhile isBlank leading-only, no trailing trim): EXIT 1.
- atk_7_reversed (control-flow effect: cons-accumulation => reversed output order): EXIT 1.
All seven attack failures are genuine 'Type mismatch: After simplification' proof errors, not env/timeout artifacts.

No attack verified => patches={} (no faithful patch to materialize/resolve-run; the resolve-every-verifying-candidate clause is vacuously satisfied, NOT skipped for lack of tooling).

REFINEMENT AUDIT (refinement.md): 10 legs, all R / A-reference / I — NO kind-3 (no A-consumed / no ungrounded oracle). The axioms region declares no opaque callee and no consumed _prop axiom; #print axioms on the closing gold proof confirms only [propext, Quot.sound]. The only two deep-model (A-reference) legs are commaPieces == str.split(',') and trim == str.strip(); their correspondence to the real Python callees is validated by conformance_check.py: `python conformance_check.py` => checked=120034 disagreements=0, status=pass, exit 0 (oracle = faithful post-patch _consume_fields replica; fuzz alphabet includes commas + full Unicode str.isspace() set incl. NBSP/NEL; seed 8056 matches mapping.md). isBlank's set is asserted == {chr(i) for isspace} inside the script.

CONCLUSION: exact-equality postcondition + clean-axiom deep model + G-CONF-validated A-reference legs => verify implies correct on this bundle. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_notrim.lean`, `atk_3_noguard.lean`, `atk_4_dropdesc.lean`, `atk_5_headpiece.lean`, `atk_6_leadtrim.lean`, `atk_7_reversed.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition problem_spec_normalizeEntries is an EXACT functional equality: result = raws.flatMap (expandEntry splitGrouped), over fully concrete pure functions (expandEntry/commaPieces/trim/isBlank). It completely pins the output, so any verifying implementation must be provably output-identical to the gold expression. No same-spec wrong impl can close any proof (the theorem statement becomes a false equality), hence there is no verifying-wrong-impl to materialize a patch for — verify=>correct holds. Discriminating input for the prepatch/no-guard bug: splitGrouped=true, raws=[(['a',',','b'], [], [])] -> gold yields [(['a'],[],[]),(['b'],[],[])] (2 trimmed pieces) while prepatch yields [(['a',',','b'],[],[])]; for the no-trim bug: raws=[([' ','a'],[],[])], splitGrouped=true -> gold trims to ['a'], no-trim keeps [' ','a'].
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_notrim.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_noguard.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

Attack 4 — `atk_4_dropdesc.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_headpiece.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_leadtrim.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_reversed.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing a sequence of documented item entries.

A documentation block describes a list of items. Each raw entry, as read from the
block, is a triple `(name, type, description)`: a name (a sequence of characters),
a type (a sequence of characters), and a description (a sequence of text lines).

Producing the normalized entry list applies, to each raw entry in order, one rule:

* When grouping is enabled and the entry has a non-empty name, the name may itself
  denote several items written together and separated by commas (for example a
  single line introducing `a, b`). Such an entry expands into one normalized entry
  per comma-separated piece: each piece, with surrounding blank characters removed,
  paired with the shared type and the shared description.
* Otherwise the entry is kept as a single normalized entry, provided it carries
  some content (a non-empty name, type, or description); a wholly empty entry
  contributes nothing.

The normalized list is the in-order concatenation of every raw entry's expansion.
-/

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature. The reading of raw entries and
-- the detection of the block boundary are unchanged bookkeeping and are abstracted
-- into the input list `raws`. The two character-level operations the rule performs
-- (separating a name on commas, and trimming surrounding blank characters) are
-- modeled directly in the `pure` region and differential-tested against their real
-- library counterparts by conformance_check.py. No consumed axioms.
-- axioms-end

-- pure-start
/-- A raw / normalized documented item entry: a name, a type, and a description
(a list of text lines). -/
abbrev FieldEntry := List Char × List Char × List (List Char)

/-- Blank characters trimmed from the ends of a separated name piece: exactly the
code points Python's bare `str.strip()` removes (the `str.isspace` set) —
U+0009–U+000D, U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028,
U+2029, U+202F, U+205F, and U+3000. -/
def isBlank (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || (0x1c ≤ n && n ≤ 0x20) ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) ||
  n == 0x2028 || n == 0x2029 || n == 0x202f || n == 0x205f || n == 0x3000

/-- Remove leading and trailing blank characters from a sequence. -/
def trim (cs : List Char) : List Char :=
  ((cs.dropWhile isBlank).reverse.dropWhile isBlank).reverse

/-- Separate a name into the comma-delimited pieces it is written as. A name with
no comma yields the single piece `[name]`; each comma starts a new piece, so an
empty piece is produced for an absent segment (mirroring delimiter-based string
splitting, which always yields at least one piece). -/
def commaPieces : List Char → List (List Char)
  | [] => [[]]
  | ',' :: cs => [] :: commaPieces cs
  | c :: cs =>
    match commaPieces cs with
    | h :: t => (c :: h) :: t
    | [] => [[c]]

/-- Expansion of one raw entry into its normalized entries, under the grouping
flag. With grouping and a non-empty name, the name is separated on commas and each
trimmed piece becomes an entry with the shared type and description; otherwise a
single entry is kept iff it has any content. -/
def expandEntry (splitGrouped : Bool) (f : FieldEntry) : List FieldEntry :=
  let (name, typ, desc) := f
  if splitGrouped && (name != []) then
    (commaPieces name).map (fun piece => (trim piece, typ, desc))
  else if (name != []) || (typ != []) || (desc != []) then
    [(name, typ, desc)]
  else
    []
-- pure-end

-- post-conditions-start
/-- The normalized entry list is the in-order concatenation of every raw entry's
expansion under the grouping flag. -/
def problem_spec_normalizeEntries
    (splitGrouped : Bool) (raws : List FieldEntry) (result : List FieldEntry) : Prop :=
  result = raws.flatMap (expandEntry splitGrouped)
-- post-conditions-end

-- impl-start
def implementation_normalizeEntries
    (splitGrouped : Bool) (raws : List FieldEntry) : List FieldEntry := Id.run do
  let mut fields : List FieldEntry := []
  for f in raws do
    let (name, typ, desc) := f
    if splitGrouped && (name != []) then
      for piece in commaPieces name do
        fields := fields ++ [(trim piece, typ, desc)]
    else if (name != []) || (typ != []) || (desc != []) then
      fields := fields ++ [(name, typ, desc)]
  return fields
-- impl-end


-- proof-start
theorem correct_normalizeEntries :
    ∀ (splitGrouped : Bool) (raws : List FieldEntry),
      problem_spec_normalizeEntries splitGrouped raws
        (implementation_normalizeEntries splitGrouped raws) := by
  intro splitGrouped raws
  unfold problem_spec_normalizeEntries implementation_normalizeEntries
  simp only [Id.run]
  have inner : ∀ (pieces : List (List Char)) (typ : List Char) (desc : List (List Char))
      (acc : List FieldEntry),
      (forIn (m := Id) pieces acc
        (fun piece r => pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))))
        = acc ++ pieces.map (fun piece => (trim piece, typ, desc)) := by
    intro pieces typ desc acc
    induction pieces generalizing acc with
    | nil => simp; rfl
    | cons p rest ih =>
      rw [List.forIn_cons]
      show (forIn rest (acc ++ [(trim p, typ, desc)]) fun piece r =>
        pure (ForInStep.yield (r ++ [(trim piece, typ, desc)]))) = _
      rw [ih]; simp [List.append_assoc]
  have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),
      (forIn (m := Id) rs acc
        (fun f r =>
          if (splitGrouped && f.1 != []) = true then do
            let r ← forIn (commaPieces f.1) r fun piece r => do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [(trim piece, f.2.1, f.2.2)]))
            pure PUnit.unit
            pure (ForInStep.yield r)
          else
            if (f.1 != [] || f.2.1 != [] || f.2.2 != []) = true then do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(f.1, f.2.1, f.2.2)]))
            else do
              pure PUnit.unit
              pure (ForInStep.yield r)))
        = acc ++ rs.flatMap (expandEntry splitGrouped) := by
    intro rs acc
    induction rs generalizing acc with
    | nil => simp; rfl
    | cons f rest ih =>
      rw [List.forIn_cons]
      simp only [expandEntry, List.flatMap_cons]
      by_cases h1 : (splitGrouped && f.1 != []) = true
      · simp only [h1, if_true]
        show (forIn rest _ _) = _
        rw [show (forIn (m:=Id) (commaPieces f.1) acc fun piece r => do
                  pure PUnit.unit
                  pure (ForInStep.yield (r ++ [(trim piece, f.2.1, f.2.2)]))) = _ from inner _ _ _ _]
        rw [ih]
        simp only [List.append_assoc]
      · simp only [h1, Bool.false_eq_true, if_false]
        by_cases h2 : (f.1 != [] || f.2.1 != [] || f.2.2 != []) = true
        · simp only [h2, if_true]
          show (forIn rest _ _) = _
          rw [ih]
          simp only [List.append_assoc, List.cons_append, List.nil_append]
        · simp only [h2, Bool.false_eq_true, if_false]
          show (forIn rest _ _) = _
          rw [ih]
          simp only [List.nil_append]
  have := key raws []
  simpa using this
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Commands: `bash scripts/lean_verify.sh <file>` from project root, run concurrently in 2 batches of 4.

### Results
- pos_control (gold impl, gold proof): EXIT 0 (verifies, no sorry). `#print axioms correct_normalizeEntries` => [propext, Quot.sound] — CLEAN (no sorryAx / no custom axioms).
- atk_1_prepatch (ignores splitGrouped; THE real prepatch bug): EXIT 1, genuine 'error: Type mismatch: After simplification' — proof cannot close.
- atk_2_notrim (emit piece without trim): EXIT 1, type-mismatch error.
- atk_3_noguard (split whenever name nonempty, ignoring flag): EXIT 1.
- atk_4_dropdesc (boundary: keep-if branch drops the desc disjunct: name||typ only): EXIT 1.
- atk_5_headpiece (partial-domain: only first comma piece kept): EXIT 1.
- atk_6_leadtrim (control-flow/partial: dropWhile isBlank leading-only, no trailing trim): EXIT 1.
- atk_7_reversed (control-flow effect: cons-accumulation => reversed output order): EXIT 1.
All seven attack failures are genuine 'Type mismatch: After simplification' proof errors, not env/timeout artifacts.

No attack verified => patches={} (no faithful patch to materialize/resolve-run; the resolve-every-verifying-candidate clause is vacuously satisfied, NOT skipped for lack of tooling).

REFINEMENT AUDIT (refinement.md): 10 legs, all R / A-reference / I — NO kind-3 (no A-consumed / no ungrounded oracle). The axioms region declares no opaque callee and no consumed _prop axiom; #print axioms on the closing gold proof confirms only [propext, Quot.sound]. The only two deep-model (A-reference) legs are commaPieces == str.split(',') and trim == str.strip(); their correspondence to the real Python callees is validated by conformance_check.py: `python conformance_check.py` => checked=120034 disagreements=0, status=pass, exit 0 (oracle = faithful post-patch _consume_fields replica; fuzz alphabet includes commas + full Unicode str.isspace() set incl. NBSP/NEL; seed 8056 matches mapping.md). isBlank's set is asserted == {chr(i) for isspace} inside the script.

CONCLUSION: exact-equality postcondition + clean-axiom deep model + G-CONF-validated A-reference legs => verify implies correct on this bundle. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True via swebench_unified.markers with LeanBackend.language). Lean compiles clean (exit 0, no sorry); #print axioms correct_normalizeEntries = [propext, Quot.sound] only — no sorryAx, proof is genuine. conformance_check.py passes (checked=120034, disagreements=0). Independent verification (transcribing Lean isBlank/trim/commaPieces from scratch, NOT reusing the bundle's _BLANK): isBlank's range set exactly equals Python str.isspace() over the full 0..0x10FFFF code-point range (no extra, no missing); trim==str.strip() and commaPieces==str.split(',') under 200k+ fuzz incl. Unicode whitespace (NBSP U+00A0, ideographic space U+3000, NEL U+0085, U+2028). Full Lean model (expandEntry over raws) == the real POST-PATCH _consume_fields decision (`if multiple and _name: for name in _name.split(','): fields.append((name.strip(), _type, _desc)); elif _name or _type or _desc: ...`) over 300k fuzzed inputs, zero disagreements. Gold patch verified at base_commit e188d56: _consume_fields gains `multiple` param; _parse_parameters_section sets multiple=True under napoleon_use_param (captured by splitGrouped). The modeling boundary — abstracting unchanged _consume_field reading and _is_section_break detection into the input list `raws` — is faithful (identical pre/post-patch). The empty-name case (name=='') never reaches split because the guard requires non-empty _name, so the str.split('')==[''] edge is irrelevant. No diverging input exists; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous check performed. (1) Mechanical leakage.screen() over the lean spec view PASSES: no diff markers, no gold-patch line reproduced, no patched file path (sphinx/ext/napoleon/docstring.py), and none of the patched distinctive repo symbols {consume_fields, consume_field, parse_other_parameters_section} appear in spec-view identifiers or comments. (2) markers.same_spec(Solution.lean, Solution_prepatch.lean) == True: the spec region (docstring + axioms + pure + post-conditions) is byte-identical pre/post patch; the entire behavioral delta is confined to the elided impl region, so the spec view carries no pre/post discriminator. (3) The prepatch 'grouping flag never honored' narration lives ONLY in the elided impl, not in the projected view. (4) The behavior the spec describes (grouping flag -> split name on commas -> trim each piece -> one entry per piece, shared type/desc) is exactly the DESIRED behavior already public in problem_statement, which literally shows 'x1, x2 : array_like' and states the expected split. A spec must describe correct behavior; here that behavior is public and the abstract Lean names (splitGrouped, commaPieces, trim, normalizeEntries, FieldEntry) echo no repo symbol and do not localize the edit. The str.strip()/str.isspace notes are G-CONF modeling-fidelity commentary, not edit localization. No leakage beyond problem_statement (hints_text not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

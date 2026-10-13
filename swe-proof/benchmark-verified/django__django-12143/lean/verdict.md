# P2 adversarial audit — django__django-12143

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,11 +124,15 @@
 -- post-conditions-end
 
 -- impl-start
+def matchesRowKeyUnescaped (mark pkName key : List Char) : Bool :=
+  if mark.contains '$' then false
+  else matchesRowKey mark pkName key
+
 def implementation_rowKeySelection {α : Type}
     (mark pkName : List Char) (items : List (List Char × α)) : List α := Id.run do
   let mut acc : List α := []
   for kv in items do
-    if matchesRowKey mark pkName kv.1 then
+    if matchesRowKeyUnescaped mark pkName kv.1 then
       acc := acc ++ [kv.2]
   return acc
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,11 +124,27 @@
 -- post-conditions-end
 
 -- impl-start
+def matchesRowKey2 (mark pkName key : List Char) : Bool :=
+  match stripPrefix? mark key with
+  | none => false
+  | some r1 =>
+    match r1 with
+    | '-' :: r2 =>
+      let ds := r2.takeWhile isDecimalDigit
+      let rest := r2.dropWhile isDecimalDigit
+      match rest with
+      | '-' :: r3 =>
+        match stripPrefix? pkName r3 with
+        | some tail => ds.length >= 2 && atEnd tail
+        | none => false
+      | _ => false
+    | _ => false
+
 def implementation_rowKeySelection {α : Type}
     (mark pkName : List Char) (items : List (List Char × α)) : List α := Id.run do
   let mut acc : List α := []
   for kv in items do
-    if matchesRowKey mark pkName kv.1 then
+    if matchesRowKey2 mark pkName kv.1 then
       acc := acc ++ [kv.2]
   return acc
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,11 +124,29 @@
 -- post-conditions-end
 
 -- impl-start
+def atEndStrict (cs : List Char) : Bool := cs.isEmpty
+
+def matchesRowKey3 (mark pkName key : List Char) : Bool :=
+  match stripPrefix? mark key with
+  | none => false
+  | some r1 =>
+    match r1 with
+    | '-' :: r2 =>
+      let ds := r2.takeWhile isDecimalDigit
+      let rest := r2.dropWhile isDecimalDigit
+      match rest with
+      | '-' :: r3 =>
+        match stripPrefix? pkName r3 with
+        | some tail => !ds.isEmpty && atEndStrict tail
+        | none => false
+      | _ => false
+    | _ => false
+
 def implementation_rowKeySelection {α : Type}
     (mark pkName : List Char) (items : List (List Char × α)) : List α := Id.run do
   let mut acc : List α := []
   for kv in items do
-    if matchesRowKey mark pkName kv.1 then
+    if matchesRowKey3 mark pkName kv.1 then
       acc := acc ++ [kv.2]
   return acc
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -129,7 +129,7 @@
   let mut acc : List α := []
   for kv in items do
     if matchesRowKey mark pkName kv.1 then
-      acc := acc ++ [kv.2]
+      acc := [kv.2] ++ acc
   return acc
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -125,12 +125,8 @@
 
 -- impl-start
 def implementation_rowKeySelection {α : Type}
-    (mark pkName : List Char) (items : List (List Char × α)) : List α := Id.run do
-  let mut acc : List α := []
-  for kv in items do
-    if matchesRowKey mark pkName kv.1 then
-      acc := acc ++ [kv.2]
-  return acc
+    (mark pkName : List Char) (items : List (List Char × α)) : List α :=
+  items.map (·.2)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,11 +124,26 @@
 -- post-conditions-end
 
 -- impl-start
+def matchesRowKey6 (mark pkName key : List Char) : Bool :=
+  match stripPrefix? mark key with
+  | none => false
+  | some r1 =>
+    match r1 with
+    | '-' :: r2 =>
+      let rest := r2.dropWhile isDecimalDigit
+      match rest with
+      | '-' :: r3 =>
+        match stripPrefix? pkName r3 with
+        | some tail => atEnd tail
+        | none => false
+      | _ => false
+    | _ => false
+
 def implementation_rowKeySelection {α : Type}
     (mark pkName : List Char) (items : List (List Char × α)) : List α := Id.run do
   let mut acc : List α := []
   for kv in items do
-    if matchesRowKey mark pkName kv.1 then
+    if matchesRowKey6 mark pkName kv.1 then
       acc := acc ++ [kv.2]
   return acc
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,11 +124,27 @@
 -- post-conditions-end
 
 -- impl-start
+def matchesRowKey7 (mark pkName key : List Char) : Bool :=
+  match stripPrefix? mark (key.drop 1) with
+  | none => false
+  | some r1 =>
+    match r1 with
+    | '-' :: r2 =>
+      let ds := r2.takeWhile isDecimalDigit
+      let rest := r2.dropWhile isDecimalDigit
+      match rest with
+      | '-' :: r3 =>
+        match stripPrefix? pkName r3 with
+        | some tail => !ds.isEmpty && atEnd tail
+        | none => false
+      | _ => false
+    | _ => false
+
 def implementation_rowKeySelection {α : Type}
     (mark pkName : List Char) (items : List (List Char × α)) : List α := Id.run do
   let mut acc : List α := []
   for kv in items do
-    if matchesRowKey mark pkName kv.1 then
+    if matchesRowKey7 mark pkName kv.1 then
       acc := acc ++ [kv.2]
   return acc
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting submitted primary-key values for the editable rows of a tabular form.

A bulk-edit form submits its fields as a flat collection of `(key, value)` pairs.
Each editable row contributes one key that encodes the row's primary key, built
from three parts joined by hyphens:

  * a constant marker string identifying the form as a whole;
  * a run of one or more decimal digits giving the row's position; and
  * the name of the primary-key field.

This routine scans the submitted pairs, in their original order, and returns the
values of exactly those pairs whose key has this three-part shape for the given
marker and primary-key-field name.

The marker is treated as an ordinary literal string: a key qualifies precisely
when it begins with the marker character-for-character, followed by a hyphen,
then a non-empty block of decimal digits, then a hyphen, then the primary-key
field name, and then the end of the key (one final trailing line break is
tolerated there, mirroring the end-of-input rule of the matching engine). Every
character of the marker — whatever it may be — must appear verbatim at the front
of the key; the marker carries no special meaning of its own. A decimal digit
here is a digit of any decimal number system (the Unicode decimal digits,
general category Nd), not only the Latin `'0'..'9'`. The order of the surviving
values, and the values themselves, are preserved unchanged from the input.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed as an axiom. The submitted pairs are
-- supplied directly as the input `items`. The decision of whether one key
-- denotes an editable row's primary key for the given marker and field name is
-- modeled DEEPLY below (`matchesRowKey`, with the pure helpers `stripPrefix?`,
-- `isDecimalDigit`, and `atEnd`), so there is no `opaque`/`axiom` callee
-- contract. The deep model is validated against the real matching behavior by
-- the differential conformance check.
-- axioms-end

-- pure-start
/-- The decimal-digit code points the matching engine's digit class accepts:
the digits of every decimal number system (Unicode general category Nd, per
the Unicode data the modeled engine ships), as inclusive `(lo, hi)`
scalar-value bounds. The digit class is Unicode-aware, not restricted to the
Latin digits. -/
def digitRanges : List (Nat × Nat) :=
  [ (0x30, 0x39), (0x660, 0x669), (0x6f0, 0x6f9), (0x7c0, 0x7c9),
    (0x966, 0x96f), (0x9e6, 0x9ef), (0xa66, 0xa6f), (0xae6, 0xaef),
    (0xb66, 0xb6f), (0xbe6, 0xbef), (0xc66, 0xc6f), (0xce6, 0xcef),
    (0xd66, 0xd6f), (0xde6, 0xdef), (0xe50, 0xe59), (0xed0, 0xed9),
    (0xf20, 0xf29), (0x1040, 0x1049), (0x1090, 0x1099), (0x17e0, 0x17e9),
    (0x1810, 0x1819), (0x1946, 0x194f), (0x19d0, 0x19d9), (0x1a80, 0x1a89),
    (0x1a90, 0x1a99), (0x1b50, 0x1b59), (0x1bb0, 0x1bb9), (0x1c40, 0x1c49),
    (0x1c50, 0x1c59), (0xa620, 0xa629), (0xa8d0, 0xa8d9), (0xa900, 0xa909),
    (0xa9d0, 0xa9d9), (0xa9f0, 0xa9f9), (0xaa50, 0xaa59), (0xabf0, 0xabf9),
    (0xff10, 0xff19), (0x104a0, 0x104a9), (0x11066, 0x1106f),
    (0x110f0, 0x110f9), (0x11136, 0x1113f), (0x111d0, 0x111d9),
    (0x112f0, 0x112f9), (0x11450, 0x11459), (0x114d0, 0x114d9),
    (0x11650, 0x11659), (0x116c0, 0x116c9), (0x11730, 0x11739),
    (0x118e0, 0x118e9), (0x11c50, 0x11c59), (0x16a60, 0x16a69),
    (0x16b50, 0x16b59), (0x1d7ce, 0x1d7ff), (0x1e950, 0x1e959) ]

/-- Whether a single character is a decimal digit: a member of one of the
decimal-digit runs above (any decimal number system's digits, not only
`'0'..'9'`). -/
def isDecimalDigit (c : Char) : Bool :=
  digitRanges.any (fun r => r.1 ≤ c.toNat && c.toNat ≤ r.2)

/-- If `p` occurs verbatim at the front of `s`, return what remains after it;
otherwise `none`. This is literal (character-for-character) prefix consumption. -/
def stripPrefix? (p s : List Char) : Option (List Char) :=
  if p.isPrefixOf s then some (s.drop p.length) else none

/-- The end-of-key position: nothing remains, or exactly one trailing line
break remains (the end-of-input tolerance of the matching engine). -/
def atEnd (cs : List Char) : Bool := cs.isEmpty || cs == ['\n']

/-- Whether `key` denotes an editable row's primary key for the form marker
`mark` and primary-key field name `pkName`.

`key` qualifies exactly when it decomposes, character-for-character, as

    mark ++ ['-'] ++ ds ++ ['-'] ++ pkName ++ tail

where `ds` is a non-empty run of decimal digits (`isDecimalDigit`, i.e. the
digits of any decimal number system) and `tail` is the end of the key (empty,
or one final line break — `atEnd`). The marker `mark` is matched as a plain
literal (consumed verbatim by `stripPrefix?`), and so is the field name
`pkName`. -/
def matchesRowKey (mark pkName key : List Char) : Bool :=
  match stripPrefix? mark key with
  | none => false
  | some r1 =>
    match r1 with
    | '-' :: r2 =>
      let ds := r2.takeWhile isDecimalDigit
      let rest := r2.dropWhile isDecimalDigit
      match rest with
      | '-' :: r3 =>
        match stripPrefix? pkName r3 with
        | some tail => !ds.isEmpty && atEnd tail
        | none => false
      | _ => false
    | _ => false
-- pure-end

-- post-conditions-start
/-- Input→output relation for the per-row primary-key selection.

Inputs:
* `mark`   — the form marker matched literally at the front of a row key;
* `pkName` — the primary-key field name closing a row key;
* `items`  — the submitted `(key, value)` pairs in submission order.

The result is fully pinned to the inputs: it is exactly the values of the pairs
whose key qualifies under `matchesRowKey`, kept in their original order. This
pins the membership (a value is present iff its key qualifies), the order, the
multiplicity (one output entry per qualifying pair), and each value (carried
through unchanged); no output component is left free. -/
def problem_spec_rowKeySelection {α : Type}
    (mark pkName : List Char) (items : List (List Char × α)) (result : List α) : Prop :=
  result = (items.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2)
-- post-conditions-end

-- impl-start
def implementation_rowKeySelection {α : Type}
    (mark pkName : List Char) (items : List (List Char × α)) : List α :=
  (items.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2)
-- impl-end

-- proof-start
theorem correct_rowKeySelection {α : Type} :
    ∀ (mark pkName : List Char) (items : List (List Char × α)),
      problem_spec_rowKeySelection mark pkName items
        (implementation_rowKeySelection mark pkName items) := by
  intro mark pkName items
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Spec is a fully-pinned functional postcondition: problem_spec_rowKeySelection ... result := result = (items.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2). It pins membership, order, multiplicity, and each value with no free component, so any impl differing from the reference on ANY input makes the Prop literally false and unprovable — proof effort is irrelevant. Confirmed byte-identical spec regions via swebench_unified.markers.same_spec = True for pc + all 7 attacks (axioms/pure/pre/post untouched).

Positive control pc.lean (extensional filter/map impl + rfl proof): VERIFIES. `bash scripts/lean_verify.sh .../pc.lean` -> EXIT 0. Appended `#print axioms correct_rowKeySelection` (pc_ax.lean) -> EXIT 0, output: 'correct_rowKeySelection does not depend on any axioms' (clean axioms, no sorry).

7 DISTINCT same-spec wrong impls, each attempted with the gold proof body, cmd `bash scripts/lean_verify.sh .../atk_N.lean`:
- atk_1 (prepatch bug, $ in marker rejects longer keys): EXIT 1.
- atk_2 (partial-domain: require >=2 digit index): EXIT 1.
- atk_3 (boundary: drop one-trailing-newline tolerance, atEnd=strictly empty): EXIT 1.
- atk_4 (control-flow-effect: prepend => reverses output order): EXIT 1.
- atk_5 (ungrounded-oracle echo: ignore matcher, return all values): EXIT 1.
- atk_6 (off-by-one: allow empty digit run): EXIT 1.
- atk_7 (literal-prefix corruption: match marker after dropping first char): EXIT 1.
All 7 EXIT 1 with genuine unclosed correctness goals (Lean residual goal = impl term ≠ List.map .2 (List.filter matchesRowKey items)), NOT tactic/timeout artifacts.

Concrete divergence verified in diverge.lean (#eval, EXIT 0): spec on the discriminating inputs gives [7] (marker form$, key form$-0-uuid — F2P case, atk_1 gives []), [9] (single-digit index form-0-id, atk_2 gives []), [1,2] (order, atk_4 gives [2,1]), [2] (atk_5 gives [1,2]). Each attack observably wrong.

Because NO wrong impl produced a closing clean-axiom proof, there is no verifying-but-wrong artifact to materialize into a faithful patch; patches={} accordingly (nothing to run through run_resolve). prepatch_reproduced=true: atk_1 is the recorded prepatch counterexample (matchesRowKeyUnescaped), reproduced and confirmed non-verifying + observably data-lossy.

refinement.md audit: 6 legs. Row1 R (accumulator loop ↔ list comprehension, order+multiplicity preserved). Row6 I/R (opaque value passthrough ↔ arbitrary α frame). Rows 2-5 A-reference: the re engine + re.escape are UNCHANGED callees whose composite matching decision is deeply modeled by matchesRowKey (stripPrefix?/isDecimalDigit/digitRanges/atEnd + takeWhile/dropWhile split), validated == real engine by conformance_check.py (G-CONF, seed 20240627, >=1.2e5 fuzzed inputs incl non-Latin Nd digits and trailing-newline keys). NO A-consumed rows, NO kind-3 legs; no opaque/axiom declaration exists. A-reference correspondence holds: digit-class note (\d ↔ 54 Nd runs) and end-anchor note ($ ↔ atEnd, one-trailing-newline tolerance) match the py3 re semantics. All legs R / A-reference / I. Verify⇒correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting submitted primary-key values for the editable rows of a tabular form.

A bulk-edit form submits its fields as a flat collection of `(key, value)` pairs.
Each editable row contributes one key that encodes the row's primary key, built
from three parts joined by hyphens:

  * a constant marker string identifying the form as a whole;
  * a run of one or more decimal digits giving the row's position; and
  * the name of the primary-key field.

This routine scans the submitted pairs, in their original order, and returns the
values of exactly those pairs whose key has this three-part shape for the given
marker and primary-key-field name.

The marker is treated as an ordinary literal string: a key qualifies precisely
when it begins with the marker character-for-character, followed by a hyphen,
then a non-empty block of decimal digits, then a hyphen, then the primary-key
field name, and then the end of the key (one final trailing line break is
tolerated there, mirroring the end-of-input rule of the matching engine). Every
character of the marker — whatever it may be — must appear verbatim at the front
of the key; the marker carries no special meaning of its own. A decimal digit
here is a digit of any decimal number system (the Unicode decimal digits,
general category Nd), not only the Latin `'0'..'9'`. The order of the surviving
values, and the values themselves, are preserved unchanged from the input.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed as an axiom. The submitted pairs are
-- supplied directly as the input `items`. The decision of whether one key
-- denotes an editable row's primary key for the given marker and field name is
-- modeled DEEPLY below (`matchesRowKey`, with the pure helpers `stripPrefix?`,
-- `isDecimalDigit`, and `atEnd`), so there is no `opaque`/`axiom` callee
-- contract. The deep model is validated against the real matching behavior by
-- the differential conformance check.
-- axioms-end

-- pure-start
/-- The decimal-digit code points the matching engine's digit class accepts:
the digits of every decimal number system (Unicode general category Nd, per
the Unicode data the modeled engine ships), as inclusive `(lo, hi)`
scalar-value bounds. The digit class is Unicode-aware, not restricted to the
Latin digits. -/
def digitRanges : List (Nat × Nat) :=
  [ (0x30, 0x39), (0x660, 0x669), (0x6f0, 0x6f9), (0x7c0, 0x7c9),
    (0x966, 0x96f), (0x9e6, 0x9ef), (0xa66, 0xa6f), (0xae6, 0xaef),
    (0xb66, 0xb6f), (0xbe6, 0xbef), (0xc66, 0xc6f), (0xce6, 0xcef),
    (0xd66, 0xd6f), (0xde6, 0xdef), (0xe50, 0xe59), (0xed0, 0xed9),
    (0xf20, 0xf29), (0x1040, 0x1049), (0x1090, 0x1099), (0x17e0, 0x17e9),
    (0x1810, 0x1819), (0x1946, 0x194f), (0x19d0, 0x19d9), (0x1a80, 0x1a89),
    (0x1a90, 0x1a99), (0x1b50, 0x1b59), (0x1bb0, 0x1bb9), (0x1c40, 0x1c49),
    (0x1c50, 0x1c59), (0xa620, 0xa629), (0xa8d0, 0xa8d9), (0xa900, 0xa909),
    (0xa9d0, 0xa9d9), (0xa9f0, 0xa9f9), (0xaa50, 0xaa59), (0xabf0, 0xabf9),
    (0xff10, 0xff19), (0x104a0, 0x104a9), (0x11066, 0x1106f),
    (0x110f0, 0x110f9), (0x11136, 0x1113f), (0x111d0, 0x111d9),
    (0x112f0, 0x112f9), (0x11450, 0x11459), (0x114d0, 0x114d9),
    (0x11650, 0x11659), (0x116c0, 0x116c9), (0x11730, 0x11739),
    (0x118e0, 0x118e9), (0x11c50, 0x11c59), (0x16a60, 0x16a69),
    (0x16b50, 0x16b59), (0x1d7ce, 0x1d7ff), (0x1e950, 0x1e959) ]

/-- Whether a single character is a decimal digit: a member of one of the
decimal-digit runs above (any decimal number system's digits, not only
`'0'..'9'`). -/
def isDecimalDigit (c : Char) : Bool :=
  digitRanges.any (fun r => r.1 ≤ c.toNat && c.toNat ≤ r.2)

/-- If `p` occurs verbatim at the front of `s`, return what remains after it;
otherwise `none`. This is literal (character-for-character) prefix consumption. -/
def stripPrefix? (p s : List Char) : Option (List Char) :=
  if p.isPrefixOf s then some (s.drop p.length) else none

/-- The end-of-key position: nothing remains, or exactly one trailing line
break remains (the end-of-input tolerance of the matching engine). -/
def atEnd (cs : List Char) : Bool := cs.isEmpty || cs == ['\n']

/-- Whether `key` denotes an editable row's primary key for the form marker
`mark` and primary-key field name `pkName`.

`key` qualifies exactly when it decomposes, character-for-character, as

    mark ++ ['-'] ++ ds ++ ['-'] ++ pkName ++ tail

where `ds` is a non-empty run of decimal digits (`isDecimalDigit`, i.e. the
digits of any decimal number system) and `tail` is the end of the key (empty,
or one final line break — `atEnd`). The marker `mark` is matched as a plain
literal (consumed verbatim by `stripPrefix?`), and so is the field name
`pkName`. -/
def matchesRowKey (mark pkName key : List Char) : Bool :=
  match stripPrefix? mark key with
  | none => false
  | some r1 =>
    match r1 with
    | '-' :: r2 =>
      let ds := r2.takeWhile isDecimalDigit
      let rest := r2.dropWhile isDecimalDigit
      match rest with
      | '-' :: r3 =>
        match stripPrefix? pkName r3 with
        | some tail => !ds.isEmpty && atEnd tail
        | none => false
      | _ => false
    | _ => false
-- pure-end

-- post-conditions-start
/-- Input→output relation for the per-row primary-key selection.

Inputs:
* `mark`   — the form marker matched literally at the front of a row key;
* `pkName` — the primary-key field name closing a row key;
* `items`  — the submitted `(key, value)` pairs in submission order.

The result is fully pinned to the inputs: it is exactly the values of the pairs
whose key qualifies under `matchesRowKey`, kept in their original order. This
pins the membership (a value is present iff its key qualifies), the order, the
multiplicity (one output entry per qualifying pair), and each value (carried
through unchanged); no output component is left free. -/
def problem_spec_rowKeySelection {α : Type}
    (mark pkName : List Char) (items : List (List Char × α)) (result : List α) : Prop :=
  result = (items.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2)
-- post-conditions-end

-- impl-start
def implementation_rowKeySelection {α : Type}
    (mark pkName : List Char) (items : List (List Char × α)) : List α :=
  (items.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2)
-- impl-end

-- proof-start
theorem correct_rowKeySelection {α : Type} :
    ∀ (mark pkName : List Char) (items : List (List Char × α)),
      problem_spec_rowKeySelection mark pkName items
        (implementation_rowKeySelection mark pkName items) := by
  intro mark pkName items
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Spec is a fully-pinned functional postcondition: problem_spec_rowKeySelection ... result := result = (items.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2). It pins membership, order, multiplicity, and each value with no free component, so any impl differing from the reference on ANY input makes the Prop literally false and unprovable — proof effort is irrelevant. Confirmed byte-identical spec regions via swebench_unified.markers.same_spec = True for pc + all 7 attacks (axioms/pure/pre/post untouched).

Positive control pc.lean (extensional filter/map impl + rfl proof): VERIFIES. `bash scripts/lean_verify.sh .../pc.lean` -> EXIT 0. Appended `#print axioms correct_rowKeySelection` (pc_ax.lean) -> EXIT 0, output: 'correct_rowKeySelection does not depend on any axioms' (clean axioms, no sorry).

7 DISTINCT same-spec wrong impls, each attempted with the gold proof body, cmd `bash scripts/lean_verify.sh .../atk_N.lean`:
- atk_1 (prepatch bug, $ in marker rejects longer keys): EXIT 1.
- atk_2 (partial-domain: require >=2 digit index): EXIT 1.
- atk_3 (boundary: drop one-trailing-newline tolerance, atEnd=strictly empty): EXIT 1.
- atk_4 (control-flow-effect: prepend => reverses output order): EXIT 1.
- atk_5 (ungrounded-oracle echo: ignore matcher, return all values): EXIT 1.
- atk_6 (off-by-one: allow empty digit run): EXIT 1.
- atk_7 (literal-prefix corruption: match marker after dropping first char): EXIT 1.
All 7 EXIT 1 with genuine unclosed correctness goals (Lean residual goal = impl term ≠ List.map .2 (List.filter matchesRowKey items)), NOT tactic/timeout artifacts.

Concrete divergence verified in diverge.lean (#eval, EXIT 0): spec on the discriminating inputs gives [7] (marker form$, key form$-0-uuid — F2P case, atk_1 gives []), [9] (single-digit index form-0-id, atk_2 gives []), [1,2] (order, atk_4 gives [2,1]), [2] (atk_5 gives [1,2]). Each attack observably wrong.

Because NO wrong impl produced a closing clean-axiom proof, there is no verifying-but-wrong artifact to materialize into a faithful patch; patches={} accordingly (nothing to run through run_resolve). prepatch_reproduced=true: atk_1 is the recorded prepatch counterexample (matchesRowKeyUnescaped), reproduced and confirmed non-verifying + observably data-lossy.

refinement.md audit: 6 legs. Row1 R (accumulator loop ↔ list comprehension, order+multiplicity preserved). Row6 I/R (opaque value passthrough ↔ arbitrary α frame). Rows 2-5 A-reference: the re engine + re.escape are UNCHANGED callees whose composite matching decision is deeply modeled by matchesRowKey (stripPrefix?/isDecimalDigit/digitRanges/atEnd + takeWhile/dropWhile split), validated == real engine by conformance_check.py (G-CONF, seed 20240627, >=1.2e5 fuzzed inputs incl non-Latin Nd digits and trailing-newline keys). NO A-consumed rows, NO kind-3 legs; no opaque/axiom declaration exists. A-reference correspondence holds: digit-class note (\d ↔ 54 Nd runs) and end-anchor note ($ ↔ atEnd, one-trailing-newline tolerance) match the py3 re semantics. All legs R / A-reference / I. Verify⇒correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No faithfulness defect found; the modeled function agrees with the real callee on the modeled domain.

**Modeled callee:** the per-row PK selection in ModelAdmin.`_get_edited_object_pks` (django/contrib/admin/options.py), fixed pattern re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkName)).match over ordered POST (key,value) pairs. Spec: problem_spec_rowKeySelection result = (items.filter matchesRowKey).map (.2).

Evidence:
1) same_spec(Solution, Solution_prepatch, lean_tables) = True — spec region (problem_spec + matchesRowKey + digitRanges/isDecimalDigit/stripPrefix?/atEnd) byte-identical across pre/post patch, so the attacked spec is the shared one.
2) Solution.lean compiles (lean_verify exit 0); #print axioms correct_rowKeySelection = [propext, Quot.sound] — no sorryAx, proof is genuine.
3) Structural faithfulness of matchesRowKey vs the REAL stdlib re engine: 400k adversarial fuzz cases with metachar-laden markers (form$, $, \, ^, [, empty, trailing marker), trailing \n/\r keys, and digit-run boundaries — using only Unicode-9.0.0-stable digits so version differences are excluded — produced 0 mismatches. Confirms re.escape literal-prefix semantics, start-anchoring, literal pkName, and $-before-single-trailing-newline tolerance (atEnd) all match.
4) Digit table: digitRanges = exactly 54 runs / 580 code points, sorted & disjoint = the Unicode 9.0.0 Nd set. The instance image runs Python 3.6 (MAP_REPO_VERSION_TO_SPECS['django/django']['3.1'].python == '3.6'), so the model is faithful to the real callee's engine; the host-only discrepancy is a Python-version artifact, NOT a spec defect. If someone (incorrectly) treated a modern Python as the oracle, the model would be too STRONG (spec accepts fewer keys than re) — but that would be an unfaithful test harness, not an unfaithful spec, and the pinned in-container image makes the model correct.
5) conformance_check.py passes (120,004 cases, 0 mismatches).

The spec is neither too strong nor drifted relative to the real repo behavior at base_commit's runtime; no diverging input exists on the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Role: leakage / gold-reconstruction over the SPEC VIEW (Solution.lean projection), judged only against the public problem_statement (not hints).

**Gold edit:** wrap `prefix` in `re.escape(...)` in `_get_edited_object_pks` so the formset prefix is matched as a LITERAL string, not a regex fragment.

What problem_statement already discloses publicly: it quotes the exact buggy line (`pk_pattern = re.compile(r'{}-\d+-{}$'.format(prefix, self.model._meta.pk.name))`), states the defect (regex special chars in `prefix`), notes pkName is safe as a Python identifier, AND explicitly states the fix verbatim: "The fix is quite straightforward (use re.escape()) ...". So the entire content of the gold edit is public.

Spec-view content examined: the docstring describes the intended (post-fix) literal-matching semantics -- 'The marker is treated as an ordinary literal string ... begins with the marker character-for-character ... the marker carries no special meaning of its own', plus the \d+ Unicode-Nd digit class and the $ end-anchor (one trailing newline) semantics; the pure helpers stripPrefix?/isDecimalDigit/digitRanges/atEnd/matchesRowKey; problem_spec_rowKeySelection. None of these quote the patch, `re.escape`, `prefix`, or any gold-patch token; they state only the correct intended behavior, which is exactly what a faithful spec must state and is fully derivable from the public problem_statement.

Crucially the bug/prepatch story (raw prefix, metachars active, `$` in marker rejects) lives ONLY in refinement.md and Solution_prepatch.lean, which are NOT part of the spec view (spec_view projection confirmed: imports/docstring/axioms/pure/post-conditions regions, plus impl/proof which are not spec-view text leakage of gold specifics). The digit-range table and end-anchor tolerance are engine-faithfulness details of the correct matcher, not disclosures of the gold discriminator beyond problem_statement.

Mechanical G-LEAK screen (leakage.screen over lean backend): passed=True, hard_failures=[]. No RELAXED_LEAKAGE.md / relaxed flag involved. The spec view does not leak the gold edit beyond the public problem_statement.

**Role:** leakage / gold-reconstruction over the SPEC VIEW (Solution.lean projection), judged only against the public problem_statement (not hints).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

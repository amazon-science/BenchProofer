# P2 adversarial audit — astropy__astropy-13453

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is an exact functional equation: result = cols.map (fun c => c.values.map (renderCell (effFormat formats c))). It fully determines the output as a function of the inputs. renderCell : Option String -> CellValue -> String and CellValue are opaque with NO consumed property (A-reference per refinement.md leg 4), so no proof can equate renderCell a v with renderCell b v when a != b, nor collapse distinct value/order structure. Any same-spec impl that verifies must therefore be extensionally equal to the reference. Verify <=> correct at the Lean level; no wrong impl closes, hence no faithful patch to resolve-test.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,14 +67,8 @@
 def implementation_formattedCells
     (formats : List (String × String)) (cols : List Column) :
     List (List String) := Id.run do
-  -- First, fix up the columns' display formats from the requested mapping
-  -- (the step the writer previously omitted).
-  let mut updated : Array Column := #[]
+  let mut out : Array (List String) := #[]
   for c in cols do
-    updated := updated.push (applyFormat formats c)
-  -- Then render each column's values using its (now effective) format.
-  let mut out : Array (List String) := #[]
-  for c in updated do
     out := out.push (c.values.map (renderCell c.format))
   return out.toList
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,10 @@
 -- impl-start
 def implementation_formattedCells
     (formats : List (String × String)) (cols : List Column) :
-    List (List String) := Id.run do
-  -- First, fix up the columns' display formats from the requested mapping
-  -- (the step the writer previously omitted).
-  let mut updated : Array Column := #[]
-  for c in cols do
-    updated := updated.push (applyFormat formats c)
-  -- Then render each column's values using its (now effective) format.
-  let mut out : Array (List String) := #[]
-  for c in updated do
-    out := out.push (c.values.map (renderCell c.format))
-  return out.toList
+    List (List String) :=
+  match formats with
+  | [] => cols.map (fun c => c.values.map (renderCell (effFormat formats c)))
+  | _  => []
 -- impl-end
 
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,12 @@
 -- impl-start
 def implementation_formattedCells
     (formats : List (String × String)) (cols : List Column) :
-    List (List String) := Id.run do
-  -- First, fix up the columns' display formats from the requested mapping
-  -- (the step the writer previously omitted).
-  let mut updated : Array Column := #[]
-  for c in cols do
-    updated := updated.push (applyFormat formats c)
-  -- Then render each column's values using its (now effective) format.
-  let mut out : Array (List String) := #[]
-  for c in updated do
-    out := out.push (c.values.map (renderCell c.format))
-  return out.toList
+    List (List String) :=
+  match cols with
+  | [] => []
+  | c :: rest =>
+    (c.values.map (renderCell c.format)) ::
+      rest.map (fun d => d.values.map (renderCell (effFormat formats d)))
 -- impl-end
 
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,8 @@
 -- impl-start
 def implementation_formattedCells
     (formats : List (String × String)) (cols : List Column) :
-    List (List String) := Id.run do
-  -- First, fix up the columns' display formats from the requested mapping
-  -- (the step the writer previously omitted).
-  let mut updated : Array Column := #[]
-  for c in cols do
-    updated := updated.push (applyFormat formats c)
-  -- Then render each column's values using its (now effective) format.
-  let mut out : Array (List String) := #[]
-  for c in updated do
-    out := out.push (c.values.map (renderCell c.format))
-  return out.toList
+    List (List String) :=
+  cols.map (fun c => (c.values.reverse).map (renderCell (effFormat formats c)))
 -- impl-end
 
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,8 @@
 -- impl-start
 def implementation_formattedCells
     (formats : List (String × String)) (cols : List Column) :
-    List (List String) := Id.run do
-  -- First, fix up the columns' display formats from the requested mapping
-  -- (the step the writer previously omitted).
-  let mut updated : Array Column := #[]
-  for c in cols do
-    updated := updated.push (applyFormat formats c)
-  -- Then render each column's values using its (now effective) format.
-  let mut out : Array (List String) := #[]
-  for c in updated do
-    out := out.push (c.values.map (renderCell c.format))
-  return out.toList
+    List (List String) :=
+  cols.map (fun c => c.values.map (renderCell none))
 -- impl-end
 
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,17 +66,9 @@
 -- impl-start
 def implementation_formattedCells
     (formats : List (String × String)) (cols : List Column) :
-    List (List String) := Id.run do
-  -- First, fix up the columns' display formats from the requested mapping
-  -- (the step the writer previously omitted).
-  let mut updated : Array Column := #[]
-  for c in cols do
-    updated := updated.push (applyFormat formats c)
-  -- Then render each column's values using its (now effective) format.
-  let mut out : Array (List String) := #[]
-  for c in updated do
-    out := out.push (c.values.map (renderCell c.format))
-  return out.toList
+    List (List String) :=
+  let g := formats.head?.map (·.2)
+  cols.map (fun c => c.values.map (renderCell g))
 -- impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Tabular output to a structured-markup format, given a set of per-column display
formats keyed by column name.

The exported behavior: when rendering a collection of columns to their string
cells, each column is displayed using the format requested for it by name when
such a request exists; otherwise the column keeps whatever display format it
already carried. The string for every individual value is produced by the
shared value-to-string rendering primitive, applied with the *effective* format
for that column.
-/

-- axioms-start
/-- An opaque value carried by a table cell (an integer, a real, etc.). -/
opaque CellValue : Type

/-- The shared rendering primitive: turn a single cell value into its display
string under an optional display format. Declared only as a signature (no
consumed property). -/
opaque renderCell : Option String → CellValue → String
-- axioms-end

-- pure-start
/-- A column: a name, the display format it already carries (if any), and its
sequence of cell values. -/
structure Column where
  name : String
  format : Option String
  values : List CellValue

/-- The display format explicitly requested for `name` by the format mapping
(association list keyed by column name), if present. -/
def lookupFormat (formats : List (String × String)) (name : String) : Option String :=
  (formats.find? (fun p => p.1 == name)).map (·.2)

/-- The *effective* display format for a column: the requested format when one
exists for the column's name, otherwise the column's pre-existing format. -/
def effFormat (formats : List (String × String)) (c : Column) : Option String :=
  match lookupFormat formats c.name with
  | some f => some f
  | none   => c.format

/-- Apply the requested format to a column, overriding its display format only
when a format is requested for the column's name. -/
def applyFormat (formats : List (String × String)) (c : Column) : Column :=
  match lookupFormat formats c.name with
  | some f => { c with format := some f }
  | none   => c
-- pure-end

-- post-conditions-start
/-- The rendered cells: one list of strings per column, where each value is
rendered with that column's effective format. Frame: the result is determined
entirely by the input columns and the requested formats — the column order, the
per-column value order, and the value contents are all preserved, and the only
format that may differ from a column's pre-existing one is a by-name request. -/
def problem_spec_formattedCells
    (formats : List (String × String)) (cols : List Column)
    (result : List (List String)) : Prop :=
  result = cols.map (fun c => c.values.map (renderCell (effFormat formats c)))
-- post-conditions-end

-- impl-start
def implementation_formattedCells
    (formats : List (String × String)) (cols : List Column) :
    List (List String) := Id.run do
  -- First, fix up the columns' display formats from the requested mapping
  -- (the step the writer previously omitted).
  let mut updated : Array Column := #[]
  for c in cols do
    updated := updated.push (applyFormat formats c)
  -- Then render each column's values using its (now effective) format.
  let mut out : Array (List String) := #[]
  for c in updated do
    out := out.push (c.values.map (renderCell c.format))
  return out.toList
-- impl-end


-- proof-start
theorem correct_formattedCells : ∀ (formats : List (String × String)) (cols : List Column),
    problem_spec_formattedCells formats cols
      (implementation_formattedCells formats cols) := by
  intro formats cols
  simp only [problem_spec_formattedCells, implementation_formattedCells, Id.run, effFormat, applyFormat]
  simp
  apply List.map_congr_left
  intro c _
  cases h : lookupFormat formats c.name <;> simp [Function.comp, h]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec=True confirmed for all 6 attacks (swebench_unified.markers.same_spec, backend lean) vs Solution.lean; axioms/pure/pre/post left byte-identical, only impl region edited.

### ATTACKS (each a DISTINCT wrong impl; command: `bash scripts/lean_verify.sh <file>` from project root):
- atk_1 PREPATCH BUG: ignores formats mapping, renders each column with its pre-existing c.format. exit 1.
- atk_2 PARTIAL-DOMAIN: correct only when formats==[], else returns []. exit 1.
- atk_3 BOUNDARY (off-by-one): applies effective format to all columns except the first. exit 1.
- atk_4 CONTROL-FLOW-EFFECT: reverses each column's value order before rendering. exit 1.
- atk_5 UNGROUNDED-ORACLE ECHO: renders every value with fixed `none` format, ignoring effFormat. exit 1.
- atk_6 GLOBAL-FORMAT wrong: applies the FIRST requested format to every column. exit 1.

Each attack run with 3 proof strategies: (i) original reference proof text -> exit 1 (atk_N.lean); (ii) simp_all with all defs unfolded -> exit 1 (atk_Na.lean); (iii) unfold+aesop -> exit 1 (atk_Nb.lean). ALL 18 wrong-impl proof attempts FAILED to close. Error messages are genuine (e.g. atk_1a/atk_5a: 'unsolved goals'; atk_4b/atk_6b: 'unfold failed' on the changed body) — NOT sorry (exit 3) and NOT timeout (exit 124).

POSITIVE CONTROL: positive_control.lean (byte-identical to Solution.lean) -> lean_verify.sh exit 0. #print axioms correct_formattedCells => 'depends on axioms: [propext, Quot.sound]' (clean; no sorryAx, no opaque axiom leakage).

prepatch_reproduced=true: atk_1 IS the recorded prepatch bug (formats never copied onto columns; renders using each column's prior info.format only), and it verifies FALSE (exit 1) against the spec — i.e. the spec correctly rejects the prepatch behavior.

NO faithful patches materialized/resolve-run because NO wrong impl closed with clean axioms (protocol step 2 vacuously satisfied: 'for EVERY wrong impl whose proof closes' — the set is empty here).

REFINEMENT.MD AUDIT: legs 1-3,5 = R (format-selection + framing, G-CONF differential-tested); leg 4 = A-reference (renderCell models col.info.iter_str_vals()/info.format formatting; opaque signature, NO consumed property in the proof — proof renders pointwise identically in spec and impl, `cases lookupFormat ... <;> simp`). No A-consumed leg, no kind-3 inexpressible leg. The A-reference correspondence holds: renderCell is a deterministic per-value rendering driven solely by info.format, unchanged by the patch, matching the impl's set-format-then-render composition. mapping.md symbol bindings consistent (HTML.write / BaseData._set_col_formats / iter_str_vals). Spec is a tight exact functional equation over an opaque renderer — no room for a same-spec wrong impl to verify.

VERDICT: SOUND. >=5 distinct attacks (6) run, none breaks the spec; verify => correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is an exact functional equation: result = cols.map (fun c => c.values.map (renderCell (effFormat formats c))). It fully determines the output as a function of the inputs. renderCell : Option String -> CellValue -> String and CellValue are opaque with NO consumed property (A-reference per refinement.md leg 4), so no proof can equate renderCell a v with renderCell b v when a != b, nor collapse distinct value/order structure. Any same-spec impl that verifies must therefore be extensionally equal to the reference. Verify <=> correct at the Lean level; no wrong impl closes, hence no faithful patch to resolve-test.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Tabular output to a structured-markup format, given a set of per-column display
formats keyed by column name.

The exported behavior: when rendering a collection of columns to their string
cells, each column is displayed using the format requested for it by name when
such a request exists; otherwise the column keeps whatever display format it
already carried. The string for every individual value is produced by the
shared value-to-string rendering primitive, applied with the *effective* format
for that column.
-/

-- axioms-start
/-- An opaque value carried by a table cell (an integer, a real, etc.). -/
opaque CellValue : Type

/-- The shared rendering primitive: turn a single cell value into its display
string under an optional display format. Declared only as a signature (no
consumed property). -/
opaque renderCell : Option String → CellValue → String
-- axioms-end

-- pure-start
/-- A column: a name, the display format it already carries (if any), and its
sequence of cell values. -/
structure Column where
  name : String
  format : Option String
  values : List CellValue

/-- The display format explicitly requested for `name` by the format mapping
(association list keyed by column name), if present. -/
def lookupFormat (formats : List (String × String)) (name : String) : Option String :=
  (formats.find? (fun p => p.1 == name)).map (·.2)

/-- The *effective* display format for a column: the requested format when one
exists for the column's name, otherwise the column's pre-existing format. -/
def effFormat (formats : List (String × String)) (c : Column) : Option String :=
  match lookupFormat formats c.name with
  | some f => some f
  | none   => c.format

/-- Apply the requested format to a column, overriding its display format only
when a format is requested for the column's name. -/
def applyFormat (formats : List (String × String)) (c : Column) : Column :=
  match lookupFormat formats c.name with
  | some f => { c with format := some f }
  | none   => c
-- pure-end

-- post-conditions-start
/-- The rendered cells: one list of strings per column, where each value is
rendered with that column's effective format. Frame: the result is determined
entirely by the input columns and the requested formats — the column order, the
per-column value order, and the value contents are all preserved, and the only
format that may differ from a column's pre-existing one is a by-name request. -/
def problem_spec_formattedCells
    (formats : List (String × String)) (cols : List Column)
    (result : List (List String)) : Prop :=
  result = cols.map (fun c => c.values.map (renderCell (effFormat formats c)))
-- post-conditions-end

-- impl-start
def implementation_formattedCells
    (formats : List (String × String)) (cols : List Column) :
    List (List String) := Id.run do
  -- First, fix up the columns' display formats from the requested mapping
  -- (the step the writer previously omitted).
  let mut updated : Array Column := #[]
  for c in cols do
    updated := updated.push (applyFormat formats c)
  -- Then render each column's values using its (now effective) format.
  let mut out : Array (List String) := #[]
  for c in updated do
    out := out.push (c.values.map (renderCell c.format))
  return out.toList
-- impl-end


-- proof-start
theorem correct_formattedCells : ∀ (formats : List (String × String)) (cols : List Column),
    problem_spec_formattedCells formats cols
      (implementation_formattedCells formats cols) := by
  intro formats cols
  simp only [problem_spec_formattedCells, implementation_formattedCells, Id.run, effFormat, applyFormat]
  simp
  apply List.map_congr_left
  intro c _
  cases h : lookupFormat formats c.name <;> simp [Function.comp, h]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec=True confirmed for all 6 attacks (swebench_unified.markers.same_spec, backend lean) vs Solution.lean; axioms/pure/pre/post left byte-identical, only impl region edited.

### ATTACKS (each a DISTINCT wrong impl; command: `bash scripts/lean_verify.sh <file>` from project root):
- atk_1 PREPATCH BUG: ignores formats mapping, renders each column with its pre-existing c.format. exit 1.
- atk_2 PARTIAL-DOMAIN: correct only when formats==[], else returns []. exit 1.
- atk_3 BOUNDARY (off-by-one): applies effective format to all columns except the first. exit 1.
- atk_4 CONTROL-FLOW-EFFECT: reverses each column's value order before rendering. exit 1.
- atk_5 UNGROUNDED-ORACLE ECHO: renders every value with fixed `none` format, ignoring effFormat. exit 1.
- atk_6 GLOBAL-FORMAT wrong: applies the FIRST requested format to every column. exit 1.

Each attack run with 3 proof strategies: (i) original reference proof text -> exit 1 (atk_N.lean); (ii) simp_all with all defs unfolded -> exit 1 (atk_Na.lean); (iii) unfold+aesop -> exit 1 (atk_Nb.lean). ALL 18 wrong-impl proof attempts FAILED to close. Error messages are genuine (e.g. atk_1a/atk_5a: 'unsolved goals'; atk_4b/atk_6b: 'unfold failed' on the changed body) — NOT sorry (exit 3) and NOT timeout (exit 124).

POSITIVE CONTROL: positive_control.lean (byte-identical to Solution.lean) -> lean_verify.sh exit 0. #print axioms correct_formattedCells => 'depends on axioms: [propext, Quot.sound]' (clean; no sorryAx, no opaque axiom leakage).

prepatch_reproduced=true: atk_1 IS the recorded prepatch bug (formats never copied onto columns; renders using each column's prior info.format only), and it verifies FALSE (exit 1) against the spec — i.e. the spec correctly rejects the prepatch behavior.

NO faithful patches materialized/resolve-run because NO wrong impl closed with clean axioms (protocol step 2 vacuously satisfied: 'for EVERY wrong impl whose proof closes' — the set is empty here).

REFINEMENT.MD AUDIT: legs 1-3,5 = R (format-selection + framing, G-CONF differential-tested); leg 4 = A-reference (renderCell models col.info.iter_str_vals()/info.format formatting; opaque signature, NO consumed property in the proof — proof renders pointwise identically in spec and impl, `cases lookupFormat ... <;> simp`). No A-consumed leg, no kind-3 inexpressible leg. The A-reference correspondence holds: renderCell is a deterministic per-value rendering driven solely by info.format, unchanged by the patch, matching the impl's set-format-then-render composition. mapping.md symbol bindings consistent (HTML.write / BaseData._set_col_formats / iter_str_vals). Spec is a tight exact functional equation over an opaque renderer — no room for a same-spec wrong impl to verify.

VERDICT: SOUND. >=5 distinct attacks (6) run, none breaks the spec; verify => correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (drift/too-strong) audit of implementation_formattedCells vs HTML.write's format-honoring cell path at base_commit 19cc80471.

Evidence:
1. Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True, LeanBackend). The fix is confined to the impl region; post-conditions/pure defs unchanged.
2. Lean elaborates clean; #print axioms correct_formattedCells => [propext, Quot.sound] (no sorryAx; proof is real).
3. Repo correspondence verified live: _set_col_formats sets col.info.format = formats[name] iff name in formats, else leaves info.format untouched — exactly effFormat/applyFormat (override only when a by-name request exists, else keep pre-existing format). Confirmed: pre-existing '04d' on col a honored ('0001','0002') while requested '+d' applies to col b ('+3','+4').
4. The only real drift risk is the opaque renderCell abstraction, which asserts per-value rendering depends solely on (format, value). I probed astropy iter_str_vals / default_format_func (str(val)) / get_auto_format_func: rendering IS pointwise — same value renders identically regardless of sibling values and regardless of first-vs-later position, for None and for '.3f','.2f','g','e'. No column-wide or order/cache dependence found. So modeling it as an opaque pointwise A-reference is faithful (not too strong: no property of renderCell is consumed by the proof).
5. G-CONF differential test passes: 15447/20000 fuzzed cases agree, 0 disagreements (seed 13453).

No diverging input exists between the modeled function and the real callee. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = module docstring + axioms (CellValue, renderCell opaque) + pure defs (Column, lookupFormat, effFormat, applyFormat) + post-conditions (problem_spec_formattedCells). Verified spec regions are byte-identical between Solution.lean and Solution_prepatch.lean (docstring, axioms, pure, post-conditions all IDENTICAL), so the differential (impl/proof) carries the gold; the spec does not. G-LEAK gate recorded pass/strict, spec view clean.

Gold edit (patch.diff): add `self.data.cols = cols` and `self.data._set_col_formats()` to HTML.write so HTML output honors the user-supplied `formats` mapping. Public problem_statement ALREADY states this behavior explicitly ('I expect the HTML table output to respect the formatting given by the formats argument') with worked examples of formats being applied vs ignored.

The spec's post-condition (render each column with its effective format = requested-by-name if present else pre-existing) is precisely the correctness property derivable from the public problem_statement — this is the spec doing its job, not leaking the fix. The spec view names no Python symbol, no file/line, no diff mechanism, and does not reference `_set_col_formats` or the two-line change; those appear only in refinement.md/mapping.md (auditor docs, not the spec view) and in the impl-region comment 'the step the writer previously omitted' (which is the gold/impl side, not the spec view). No spec-view line reconstructs the gold edit beyond what problem_statement discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

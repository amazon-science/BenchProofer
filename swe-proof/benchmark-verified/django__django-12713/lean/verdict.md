# P2 adversarial audit — django__django-12713

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.lean`, `atk2_flatfiltered.lean`, `atk3_orderswap.lean`, `atk4_invguard.lean`, `atk5_echoincoming.lean`, `atk6_vertfromhoriz.lean`, `atk7_drophoriz.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closes correct_resolveWidget with clean axioms; therefore no faithful patch exists to run through the resolve harness. The postcondition is a TOTAL FUNCTIONAL EQUATION result = F(inputs) where F = (match incoming with some w => some w | none => defaultWidget name auto raw vert horiz). Any impl differing from F on any reachable input makes the universally-quantified correctness theorem FALSE, so it cannot verify. Machine-confirmed: for each of the 7 same-spec wrong impls a native_decide refutation file (ref_<atk>.lean) proves NOT problem_spec_resolveWidget <witness> (implementation_resolveWidget <witness>) at a concrete input, exit 0 -- so none can have any closing proof.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,14 +88,12 @@
     (name : FieldName) (incoming : Option Widget)
     (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
   let mut widget := incoming
-  -- Only consult the configuration when the caller chose nothing.
-  if widget.isNone then
-    if name ∈ auto then
-      widget := some .autocomplete
-    else if name ∈ raw then
-      widget := some .rawId
-    else if name ∈ (vert ++ horiz) then
-      widget := some (.filtered (name ∈ vert))
+  if name ∈ auto then
+    widget := some .autocomplete
+  else if name ∈ raw then
+    widget := some .rawId
+  else if name ∈ (vert ++ horiz) then
+    widget := some (.filtered (name ∈ vert))
   return widget
 -- impl-end
 
```

Attack 2 — `atk2_flatfiltered.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,14 +88,13 @@
     (name : FieldName) (incoming : Option Widget)
     (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
   let mut widget := incoming
-  -- Only consult the configuration when the caller chose nothing.
   if widget.isNone then
     if name ∈ auto then
       widget := some .autocomplete
     else if name ∈ raw then
       widget := some .rawId
     else if name ∈ (vert ++ horiz) then
-      widget := some (.filtered (name ∈ vert))
+      widget := some (.filtered false)
   return widget
 -- impl-end
 
```

Attack 3 — `atk3_orderswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,12 +88,11 @@
     (name : FieldName) (incoming : Option Widget)
     (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
   let mut widget := incoming
-  -- Only consult the configuration when the caller chose nothing.
   if widget.isNone then
-    if name ∈ auto then
+    if name ∈ raw then
+      widget := some .rawId
+    else if name ∈ auto then
       widget := some .autocomplete
-    else if name ∈ raw then
-      widget := some .rawId
     else if name ∈ (vert ++ horiz) then
       widget := some (.filtered (name ∈ vert))
   return widget
```

Attack 4 — `atk4_invguard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,8 +88,7 @@
     (name : FieldName) (incoming : Option Widget)
     (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
   let mut widget := incoming
-  -- Only consult the configuration when the caller chose nothing.
-  if widget.isNone then
+  if ¬ widget.isNone then
     if name ∈ auto then
       widget := some .autocomplete
     else if name ∈ raw then
@@ -108,14 +107,8 @@
   intro name incoming auto raw vert horiz
   unfold problem_spec_resolveWidget implementation_resolveWidget defaultWidget
   cases incoming with
-  | some w => rfl
+  | some w => first | rfl | simp_all | (split <;> rfl)
   | none =>
-    simp only [Id.run, Option.isNone_none, if_true]
-    by_cases hauto : name ∈ auto
-    · simp only [hauto, if_true]; rfl
-    · by_cases hraw : name ∈ raw
-      · simp only [hauto, hraw, if_true, if_false]; rfl
-      · by_cases hvh : name ∈ (vert ++ horiz)
-        · simp only [hauto, hraw, hvh, if_true, if_false]; rfl
-        · simp only [hauto, hraw, hvh, if_false]; rfl
+    simp only [Id.run, Option.isNone_none]
+    split <;> first | rfl | simp_all | split <;> rfl
 -- proof-end
```

Attack 5 — `atk5_echoincoming.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,16 +87,7 @@
 def implementation_resolveWidget
     (name : FieldName) (incoming : Option Widget)
     (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
-  let mut widget := incoming
-  -- Only consult the configuration when the caller chose nothing.
-  if widget.isNone then
-    if name ∈ auto then
-      widget := some .autocomplete
-    else if name ∈ raw then
-      widget := some .rawId
-    else if name ∈ (vert ++ horiz) then
-      widget := some (.filtered (name ∈ vert))
-  return widget
+  return incoming
 -- impl-end
 
 -- proof-start
@@ -108,14 +99,8 @@
   intro name incoming auto raw vert horiz
   unfold problem_spec_resolveWidget implementation_resolveWidget defaultWidget
   cases incoming with
-  | some w => rfl
+  | some w => first | rfl | simp_all | (split <;> rfl)
   | none =>
-    simp only [Id.run, Option.isNone_none, if_true]
-    by_cases hauto : name ∈ auto
-    · simp only [hauto, if_true]; rfl
-    · by_cases hraw : name ∈ raw
-      · simp only [hauto, hraw, if_true, if_false]; rfl
-      · by_cases hvh : name ∈ (vert ++ horiz)
-        · simp only [hauto, hraw, hvh, if_true, if_false]; rfl
-        · simp only [hauto, hraw, hvh, if_false]; rfl
+    simp only [Id.run, Option.isNone_none]
+    split <;> first | rfl | simp_all | split <;> rfl
 -- proof-end
```

Attack 6 — `atk6_vertfromhoriz.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,14 +88,13 @@
     (name : FieldName) (incoming : Option Widget)
     (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
   let mut widget := incoming
-  -- Only consult the configuration when the caller chose nothing.
   if widget.isNone then
     if name ∈ auto then
       widget := some .autocomplete
     else if name ∈ raw then
       widget := some .rawId
     else if name ∈ (vert ++ horiz) then
-      widget := some (.filtered (name ∈ vert))
+      widget := some (.filtered (name ∈ horiz))
   return widget
 -- impl-end
 
```

Attack 7 — `atk7_drophoriz.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,14 +88,13 @@
     (name : FieldName) (incoming : Option Widget)
     (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
   let mut widget := incoming
-  -- Only consult the configuration when the caller chose nothing.
   if widget.isNone then
     if name ∈ auto then
       widget := some .autocomplete
     else if name ∈ raw then
       widget := some .rawId
-    else if name ∈ (vert ++ horiz) then
-      widget := some (.filtered (name ∈ vert))
+    else if name ∈ vert then
+      widget := some (.filtered true)
   return widget
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting the form widget for a multi-valued relation field on an admin form.

The setting: an admin form is being built for a field that relates one record to
MANY others. The form-builder receives a bag of keyword options that the CALLER
may have already populated, plus the admin configuration that classifies field
names into three groups:

  * names that should use an autocomplete-style multi-select;
  * names that should use a raw-id multi-select;
  * names that should use a two-box filtered multi-select (further split into a
    "vertical" subset and a "horizontal" subset).

The builder must decide which widget the field ends up with. The intended
behavior:

  * a widget the CALLER has already chosen takes precedence — it is kept as-is
    and the configuration-driven classification is not consulted at all;
  * otherwise the widget is chosen from the configuration: an autocomplete name
    wins first, then a raw-id name, then a filtered-select name (carrying whether
    that name is in the vertical subset);
  * if the caller chose nothing and the name matches none of the groups, the
    field is left without a configuration-chosen widget.

`Widget` records only the touched distinction: which KIND of widget is selected
(and, for a caller-chosen one, its opaque object identity).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The field-name
-- classification is supplied directly as the three configuration lists (the
-- accessor that returns the autocomplete-eligible names is read as its result
-- list), and the widget-selection decision is modeled structurally over those
-- lists and the caller-supplied option. No `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A field-name identity. Modeled as a `Nat` (an injective encoding of the
distinct field-name strings; only equality / list-membership is observed). -/
abbrev FieldName := Nat

/-- The kind of widget selected for the relation field, restricted to the
touched distinctions:
* `autocomplete` — an autocomplete-style multi-select;
* `rawId` — a raw-id multi-select;
* `filtered vertical` — a two-box filtered multi-select; `vertical = true` iff
  the field name belongs to the "vertical" subset;
* `supplied id` — a widget the caller chose, identified only by its opaque
  object identity `id`. -/
inductive Widget where
  | autocomplete
  | rawId
  | filtered (vertical : Bool)
  | supplied (id : Nat)
deriving DecidableEq

/-- The configuration-driven widget choice for a field name, absent any
caller-supplied widget: an autocomplete name wins first, then a raw-id name,
then a filtered-select name (carrying membership in the vertical subset); a name
in none of the groups gets no configuration-chosen widget. -/
def defaultWidget (name : FieldName) (auto raw vert horiz : List FieldName) :
    Option Widget :=
  if name ∈ auto then some .autocomplete
  else if name ∈ raw then some .rawId
  else if name ∈ (vert ++ horiz) then some (.filtered (name ∈ vert))
  else none
-- pure-end

-- post-conditions-start
/-- The widget the field ends up with. A caller-supplied widget (`incoming =
some w`) is kept exactly; otherwise the configuration-driven choice is used. The
result is fully pinned by the inputs. -/
def problem_spec_resolveWidget
    (name : FieldName) (incoming : Option Widget)
    (auto raw vert horiz : List FieldName) (result : Option Widget) : Prop :=
  result =
    (match incoming with
     | some w => some w
     | none   => defaultWidget name auto raw vert horiz)
-- post-conditions-end

-- impl-start
def implementation_resolveWidget
    (name : FieldName) (incoming : Option Widget)
    (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
  let mut widget := incoming
  -- Only consult the configuration when the caller chose nothing.
  if widget.isNone then
    if name ∈ auto then
      widget := some .autocomplete
    else if name ∈ raw then
      widget := some .rawId
    else if name ∈ (vert ++ horiz) then
      widget := some (.filtered (name ∈ vert))
  return widget
-- impl-end

-- proof-start
theorem correct_resolveWidget :
    ∀ (name : FieldName) (incoming : Option Widget)
      (auto raw vert horiz : List FieldName),
      problem_spec_resolveWidget name incoming auto raw vert horiz
        (implementation_resolveWidget name incoming auto raw vert horiz) := by
  intro name incoming auto raw vert horiz
  unfold problem_spec_resolveWidget implementation_resolveWidget defaultWidget
  cases incoming with
  | some w => rfl
  | none =>
    simp only [Id.run, Option.isNone_none, if_true]
    by_cases hauto : name ∈ auto
    · simp only [hauto, if_true]; rfl
    · by_cases hraw : name ∈ raw
      · simp only [hauto, hraw, if_true, if_false]; rfl
      · by_cases hvh : name ∈ (vert ++ horiz)
        · simp only [hauto, hraw, hvh, if_true, if_false]; rfl
        · simp only [hauto, hraw, hvh, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

venv activated; NEVER called lake/lean directly (only scripts/lean_verify.sh). same_spec=True for all 8 files (7 attacks + pc_gold) via swebench_unified.markers.same_spec with get_backend('lean').

BUNDLE STRUCTURE: axioms region is EMPTY (axiom_check.py is a G-AX skip stub). So there are NO A-legs / deep-model references to attack. Per refinement.md every impl leg is R or I: R legs = the four config lists read directly as UNCHANGED callee results (get_autocomplete_fields(request)->auto returns self.autocomplete_fields verbatim, self.raw_id_fields->raw, self.filter_vertical->vert, self.filter_horizontal->horiz); I leg = the patch's fixed guard widget.isNone <-> 'widget' not in kwargs (deeply modeled; None-vs-absent coincide on the reachable domain since formfield_overrides widgets are always real instances -- argument in mapping.md is sound). Correspondence to base_commit source options.py:252-261 + patch.diff verified. No kind-3 legs. R/I shadow validated by G-CONF (conformance_check.py present).

### PROTOCOL EXECUTED (all files; verifications run concurrently as background jobs, <=4 at a time, in 2 batches):
Command per file: bash scripts/lean_verify.sh <file>.lean

### ATTACK RESULTS (impl-region-only edits; each carried a genuine gold-style or aggressive proof attempt):
- atk1_prepatch (PREPATCH BUG: cascade runs unconditionally, overwrites caller widget): VERIFY exit 1 (unprovable leftover goal). REFUTED: ref_atk1_prepatch.lean exit 0 at name=0, incoming=some(supplied 7), auto=[0] -> spec demands some(supplied 7), impl gives some autocomplete. prepatch bug reproduced.
- atk2_flatfiltered (drop vertical flag, always filtered false -- value/partial-domain): VERIFY exit 1 (leftover: filtered false = filtered (name in vert)). REFUTED: ref_atk2 exit 0 at name=0,none,vert=[0].
- atk3_orderswap (raw checked before auto -- control-flow order): VERIFY exit 1. REFUTED: ref_atk3 exit 0 at name=0,none,auto=[0],raw=[0] (both match) -> autocomplete expected.
- atk4_invguard (inverted guard: consult config only when caller HAD a widget -- control-flow-effect): VERIFY exit 1. REFUTED: ref_atk4 exit 0 at name=0,none,auto=[0] -> autocomplete expected, impl leaves none.
- atk5_echoincoming (ungrounded-oracle echo: return incoming, never consult config): VERIFY exit 1. REFUTED: ref_atk5 exit 0 at name=0,none,auto=[0] -> autocomplete expected, echo gives none.
- atk6_vertfromhoriz (vertical flag reads horiz membership -- subtle value swap): VERIFY exit 1 (leftover: filtered (name in horiz) = filtered (name in vert)). REFUTED: ref_atk6 exit 0 at name=0,none,horiz=[0] -> filtered false expected, impl gives filtered true.
- atk7_drophoriz (drop horiz from filtered domain -- boundary/partial-domain): VERIFY exit 1 (leftover: none = none obstruction on horiz branch). REFUTED: ref_atk7 exit 0 at name=0,none,horiz=[0] -> filtered false expected, impl gives none.

POSITIVE CONTROL pc_gold.lean (gold impl verbatim): VERIFY exit 0. #print axioms correct_resolveWidget (pc_gold_ax.lean) -> depends on axioms: [propext, Quot.sound] -- CLEAN, no sorryAx.

CONCLUSION: 7 distinct same-spec wrong impls attempted (prepatch bug + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + value swaps). ALL fail to verify AND are machine-proven to violate the spec at concrete witnesses. ZERO wrong impls closed with clean axioms, so there is no faithful patch to materialize/run through resolve -- the verify=>correct implication holds vacuously on the wrong-impl side and positively via the total functional equation. Spec is TIGHT. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.lean`, `atk2_flatfiltered.lean`, `atk3_orderswap.lean`, `atk4_invguard.lean`, `atk5_echoincoming.lean`, `atk6_vertfromhoriz.lean`, `atk7_drophoriz.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closes correct_resolveWidget with clean axioms; therefore no faithful patch exists to run through the resolve harness. The postcondition is a TOTAL FUNCTIONAL EQUATION result = F(inputs) where F = (match incoming with some w => some w | none => defaultWidget name auto raw vert horiz). Any impl differing from F on any reachable input makes the universally-quantified correctness theorem FALSE, so it cannot verify. Machine-confirmed: for each of the 7 same-spec wrong impls a native_decide refutation file (ref_<atk>.lean) proves NOT problem_spec_resolveWidget <witness> (implementation_resolveWidget <witness>) at a concrete input, exit 0 -- so none can have any closing proof.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_flatfiltered.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_orderswap.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_invguard.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_echoincoming.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_vertfromhoriz.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_drophoriz.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting the form widget for a multi-valued relation field on an admin form.

The setting: an admin form is being built for a field that relates one record to
MANY others. The form-builder receives a bag of keyword options that the CALLER
may have already populated, plus the admin configuration that classifies field
names into three groups:

  * names that should use an autocomplete-style multi-select;
  * names that should use a raw-id multi-select;
  * names that should use a two-box filtered multi-select (further split into a
    "vertical" subset and a "horizontal" subset).

The builder must decide which widget the field ends up with. The intended
behavior:

  * a widget the CALLER has already chosen takes precedence — it is kept as-is
    and the configuration-driven classification is not consulted at all;
  * otherwise the widget is chosen from the configuration: an autocomplete name
    wins first, then a raw-id name, then a filtered-select name (carrying whether
    that name is in the vertical subset);
  * if the caller chose nothing and the name matches none of the groups, the
    field is left without a configuration-chosen widget.

`Widget` records only the touched distinction: which KIND of widget is selected
(and, for a caller-chosen one, its opaque object identity).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The field-name
-- classification is supplied directly as the three configuration lists (the
-- accessor that returns the autocomplete-eligible names is read as its result
-- list), and the widget-selection decision is modeled structurally over those
-- lists and the caller-supplied option. No `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A field-name identity. Modeled as a `Nat` (an injective encoding of the
distinct field-name strings; only equality / list-membership is observed). -/
abbrev FieldName := Nat

/-- The kind of widget selected for the relation field, restricted to the
touched distinctions:
* `autocomplete` — an autocomplete-style multi-select;
* `rawId` — a raw-id multi-select;
* `filtered vertical` — a two-box filtered multi-select; `vertical = true` iff
  the field name belongs to the "vertical" subset;
* `supplied id` — a widget the caller chose, identified only by its opaque
  object identity `id`. -/
inductive Widget where
  | autocomplete
  | rawId
  | filtered (vertical : Bool)
  | supplied (id : Nat)
deriving DecidableEq

/-- The configuration-driven widget choice for a field name, absent any
caller-supplied widget: an autocomplete name wins first, then a raw-id name,
then a filtered-select name (carrying membership in the vertical subset); a name
in none of the groups gets no configuration-chosen widget. -/
def defaultWidget (name : FieldName) (auto raw vert horiz : List FieldName) :
    Option Widget :=
  if name ∈ auto then some .autocomplete
  else if name ∈ raw then some .rawId
  else if name ∈ (vert ++ horiz) then some (.filtered (name ∈ vert))
  else none
-- pure-end

-- post-conditions-start
/-- The widget the field ends up with. A caller-supplied widget (`incoming =
some w`) is kept exactly; otherwise the configuration-driven choice is used. The
result is fully pinned by the inputs. -/
def problem_spec_resolveWidget
    (name : FieldName) (incoming : Option Widget)
    (auto raw vert horiz : List FieldName) (result : Option Widget) : Prop :=
  result =
    (match incoming with
     | some w => some w
     | none   => defaultWidget name auto raw vert horiz)
-- post-conditions-end

-- impl-start
def implementation_resolveWidget
    (name : FieldName) (incoming : Option Widget)
    (auto raw vert horiz : List FieldName) : Option Widget := Id.run do
  let mut widget := incoming
  -- Only consult the configuration when the caller chose nothing.
  if widget.isNone then
    if name ∈ auto then
      widget := some .autocomplete
    else if name ∈ raw then
      widget := some .rawId
    else if name ∈ (vert ++ horiz) then
      widget := some (.filtered (name ∈ vert))
  return widget
-- impl-end

-- proof-start
theorem correct_resolveWidget :
    ∀ (name : FieldName) (incoming : Option Widget)
      (auto raw vert horiz : List FieldName),
      problem_spec_resolveWidget name incoming auto raw vert horiz
        (implementation_resolveWidget name incoming auto raw vert horiz) := by
  intro name incoming auto raw vert horiz
  unfold problem_spec_resolveWidget implementation_resolveWidget defaultWidget
  cases incoming with
  | some w => rfl
  | none =>
    simp only [Id.run, Option.isNone_none, if_true]
    by_cases hauto : name ∈ auto
    · simp only [hauto, if_true]; rfl
    · by_cases hraw : name ∈ raw
      · simp only [hauto, hraw, if_true, if_false]; rfl
      · by_cases hvh : name ∈ (vert ++ horiz)
        · simp only [hauto, hraw, hvh, if_true, if_false]; rfl
        · simp only [hauto, hraw, hvh, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

venv activated; NEVER called lake/lean directly (only scripts/lean_verify.sh). same_spec=True for all 8 files (7 attacks + pc_gold) via swebench_unified.markers.same_spec with get_backend('lean').

BUNDLE STRUCTURE: axioms region is EMPTY (axiom_check.py is a G-AX skip stub). So there are NO A-legs / deep-model references to attack. Per refinement.md every impl leg is R or I: R legs = the four config lists read directly as UNCHANGED callee results (get_autocomplete_fields(request)->auto returns self.autocomplete_fields verbatim, self.raw_id_fields->raw, self.filter_vertical->vert, self.filter_horizontal->horiz); I leg = the patch's fixed guard widget.isNone <-> 'widget' not in kwargs (deeply modeled; None-vs-absent coincide on the reachable domain since formfield_overrides widgets are always real instances -- argument in mapping.md is sound). Correspondence to base_commit source options.py:252-261 + patch.diff verified. No kind-3 legs. R/I shadow validated by G-CONF (conformance_check.py present).

### PROTOCOL EXECUTED (all files; verifications run concurrently as background jobs, <=4 at a time, in 2 batches):
Command per file: bash scripts/lean_verify.sh <file>.lean

### ATTACK RESULTS (impl-region-only edits; each carried a genuine gold-style or aggressive proof attempt):
- atk1_prepatch (PREPATCH BUG: cascade runs unconditionally, overwrites caller widget): VERIFY exit 1 (unprovable leftover goal). REFUTED: ref_atk1_prepatch.lean exit 0 at name=0, incoming=some(supplied 7), auto=[0] -> spec demands some(supplied 7), impl gives some autocomplete. prepatch bug reproduced.
- atk2_flatfiltered (drop vertical flag, always filtered false -- value/partial-domain): VERIFY exit 1 (leftover: filtered false = filtered (name in vert)). REFUTED: ref_atk2 exit 0 at name=0,none,vert=[0].
- atk3_orderswap (raw checked before auto -- control-flow order): VERIFY exit 1. REFUTED: ref_atk3 exit 0 at name=0,none,auto=[0],raw=[0] (both match) -> autocomplete expected.
- atk4_invguard (inverted guard: consult config only when caller HAD a widget -- control-flow-effect): VERIFY exit 1. REFUTED: ref_atk4 exit 0 at name=0,none,auto=[0] -> autocomplete expected, impl leaves none.
- atk5_echoincoming (ungrounded-oracle echo: return incoming, never consult config): VERIFY exit 1. REFUTED: ref_atk5 exit 0 at name=0,none,auto=[0] -> autocomplete expected, echo gives none.
- atk6_vertfromhoriz (vertical flag reads horiz membership -- subtle value swap): VERIFY exit 1 (leftover: filtered (name in horiz) = filtered (name in vert)). REFUTED: ref_atk6 exit 0 at name=0,none,horiz=[0] -> filtered false expected, impl gives filtered true.
- atk7_drophoriz (drop horiz from filtered domain -- boundary/partial-domain): VERIFY exit 1 (leftover: none = none obstruction on horiz branch). REFUTED: ref_atk7 exit 0 at name=0,none,horiz=[0] -> filtered false expected, impl gives none.

POSITIVE CONTROL pc_gold.lean (gold impl verbatim): VERIFY exit 0. #print axioms correct_resolveWidget (pc_gold_ax.lean) -> depends on axioms: [propext, Quot.sound] -- CLEAN, no sorryAx.

CONCLUSION: 7 distinct same-spec wrong impls attempted (prepatch bug + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + value swaps). ALL fail to verify AND are machine-proven to violate the spec at concrete witnesses. ZERO wrong impls closed with clean axioms, so there is no faithful patch to materialize/run through resolve -- the verify=>correct implication holds vacuously on the wrong-impl side and positively via the total functional equation. Spec is TIGHT. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verification performed:
1. same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical; prepatch differs ONLY in impl+proof regions, which are elided from the spec view). Confirmed spec_view elides impl/proof.
2. lean_verify.sh Solution.lean -> EXIT 0 (compiles, no sorry).
3. #print axioms correct_resolveWidget -> [propext, Quot.sound] only; NO sorryAx -> proof is genuine, not fake.
4. conformance_check.py -> checked=120014 disagreements=0, status=pass.
5. Cross-checked against real repo (base_commit) post-patch code in options.py:252-261. Model faithfully mirrors: guard 'widget' not in kwargs <-> incoming.isNone; cascade autocomplete->rawId->filtered(name in filter_vertical)->none; precedence order identical; vertical flag = name in filter_vertical; [*filter_vertical,*filter_horizontal] <-> vert++horiz membership. get_autocomplete_fields returns self.autocomplete_fields unchanged by patch (read AS list auto) - confirmed.

The spec pins the result EXACTLY (result = match incoming...), so it is neither too weak nor drifting on any reachable input. The presence-vs-None boundary is a legitimate documented domain restriction, not spec drift. VERDICT: FAITHFUL.

Counterexample / evidence:

```
Theoretical only, on the excluded domain: kwargs={'widget': None}, db_field.name='members', get_autocomplete_fields=['members']. Real callee: 'widget' IS in kwargs -> cascade skipped -> kwargs['widget'] stays None. Model (were it representable): incoming=none -> defaultWidget returns some .autocomplete. Not a real divergence because Option Widget cannot represent this input and it is unreachable.
```

Verification performed:
1. same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical; prepatch differs ONLY in impl+proof regions, which are elided from the spec view). Confirmed spec_view elides impl/proof.
2. lean_verify.sh Solution.lean -> EXIT 0 (compiles, no sorry).
3. #print axioms correct_resolveWidget -> [propext, Quot.sound] only; NO sorryAx -> proof is genuine, not fake.
4. conformance_check.py -> checked=120014 disagreements=0, status=pass.
5. Cross-checked against real repo (base_commit) post-patch code in options.py:252-261. Model faithfully mirrors: guard 'widget' not in kwargs <-> incoming.isNone; cascade autocomplete->rawId->filtered(name in filter_vertical)->none; precedence order identical; vertical flag = name in filter_vertical; [*filter_vertical,*filter_horizontal] <-> vert++horiz membership. get_autocomplete_fields returns self.autocomplete_fields unchanged by patch (read AS list auto) - confirmed.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + pure + post-conditions regions) verified byte-identical to Solution_prepatch via swebench_unified.markers.same_spec = True; impl/proof regions are elided in the projection so no gold impl content is visible. Mechanical G-LEAK screen (leakage.screen) passes with zero hard failures.

Content analysis of what the spec view reveals vs. public problem_statement:
- problem_statement: 'Allow overridding widget in formfield_for_manytomany()... It does not work when I set widget param... This is different from the formfield_for_foreignkey() function.' This publicly discloses the intended behavior: a caller-supplied widget must be honored. The spec's clause 'a widget the CALLER has already chosen takes precedence — it is kept as-is and the configuration-driven classification is not consulted at all' is directly derivable from this public task; it is not leakage.
- No diff markers (@@, diff --git, +++, index) in the spec view.
- No gold-patch changed line reproduced: the added guard `if 'widget' not in kwargs:` and its structure never appear in the spec view (verified: no changed line of len>=8 matches the normalized view).
- No patched file path (django/contrib/admin/options.py) or dotted module path in the view.
- The only distinctive patched symbol is `formfield_for_manytomany`; it is fully abstracted to resolveWidget/defaultWidget/Widget and appears in no spec-view identifier or comment.
- No fix/bug/regression/previously/incorrectly narration in spec-view comments; the prose is behavioral (widget kinds, precedence, classification cascade), describing the contract, not the edit.

The spec necessarily states the full function contract (caller precedence + autocomplete/raw-id/filtered cascade), but the caller-precedence behavior is exactly what the public issue requests, so the view does not reveal the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

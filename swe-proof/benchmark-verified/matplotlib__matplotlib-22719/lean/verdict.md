# P2 adversarial audit — matplotlib__matplotlib-22719

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatchA.lean`, `atk2_prepatchB.lean`, `atk3_boundaryA.lean`, `atk4_ctrlB.lean`, `atk5_partialA.lean`, `atk6_constfalse.lean`, `atk7_len2B.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. Both legs are maximally-tight equality specs (result = (!seq.isEmpty && seq.all pred)); every genuinely-wrong impl (atk1-atk7) makes correct_* a false Prop and FAILS to verify (exit 1). Only the gold-equivalent echo (atk8) closes, and its faithful patch = gold patch, which RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatchA.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
   for v in values do
     if !isNumeric v then
       isNumlike := false
-  return (!values.isEmpty && isNumlike)
+  return isNumlike
 -- impl-end
 
 -- proof-start
@@ -91,8 +91,11 @@
   intro values
   unfold problem_spec_numericPassthrough implementation_numericPassthrough
   simp only [Id.run, bind]
-  rw [flag_loop isNumeric values true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop isNumeric values true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
 
 -- post-conditions-start
@@ -119,6 +122,9 @@
   intro data
   unfold problem_spec_parsableInfo implementation_parsableInfo
   simp only [Id.run, bind]
-  rw [flag_loop looksNumeric data true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop looksNumeric data true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
```

Attack 2 — `atk2_prepatchB.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,8 +91,11 @@
   intro values
   unfold problem_spec_numericPassthrough implementation_numericPassthrough
   simp only [Id.run, bind]
-  rw [flag_loop isNumeric values true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop isNumeric values true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
 
 -- post-conditions-start
@@ -108,7 +111,7 @@
   for val in data do
     if !looksNumeric val then
       convertible := false
-  return (!data.isEmpty && convertible)
+  return convertible
 -- impl-end
 
 -- proof-start
@@ -119,6 +122,9 @@
   intro data
   unfold problem_spec_parsableInfo implementation_parsableInfo
   simp only [Id.run, bind]
-  rw [flag_loop looksNumeric data true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop looksNumeric data true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
```

Attack 3 — `atk3_boundaryA.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
   for v in values do
     if !isNumeric v then
       isNumlike := false
-  return (!values.isEmpty && isNumlike)
+  return (values.isEmpty || isNumlike)
 -- impl-end
 
 -- proof-start
@@ -91,8 +91,11 @@
   intro values
   unfold problem_spec_numericPassthrough implementation_numericPassthrough
   simp only [Id.run, bind]
-  rw [flag_loop isNumeric values true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop isNumeric values true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
 
 -- post-conditions-start
@@ -119,6 +122,9 @@
   intro data
   unfold problem_spec_parsableInfo implementation_parsableInfo
   simp only [Id.run, bind]
-  rw [flag_loop looksNumeric data true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop looksNumeric data true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
```

Attack 4 — `atk4_ctrlB.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,8 +91,11 @@
   intro values
   unfold problem_spec_numericPassthrough implementation_numericPassthrough
   simp only [Id.run, bind]
-  rw [flag_loop isNumeric values true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop isNumeric values true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
 
 -- post-conditions-start
@@ -107,7 +110,7 @@
   let mut convertible := true
   for val in data do
     if !looksNumeric val then
-      convertible := false
+      convertible := true
   return (!data.isEmpty && convertible)
 -- impl-end
 
@@ -119,6 +122,9 @@
   intro data
   unfold problem_spec_parsableInfo implementation_parsableInfo
   simp only [Id.run, bind]
-  rw [flag_loop looksNumeric data true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop looksNumeric data true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
```

Attack 5 — `atk5_partialA.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,11 +56,14 @@
 
 -- impl-start
 def implementation_numericPassthrough (values : List Element) : Bool := Id.run do
-  let mut isNumlike := true
-  for v in values do
-    if !isNumeric v then
-      isNumlike := false
-  return (!values.isEmpty && isNumlike)
+  match values with
+  | [] => true
+  | vs =>
+    let mut isNumlike := true
+    for v in vs do
+      if !isNumeric v then
+        isNumlike := false
+    return isNumlike
 -- impl-end
 
 -- proof-start
@@ -91,8 +94,11 @@
   intro values
   unfold problem_spec_numericPassthrough implementation_numericPassthrough
   simp only [Id.run, bind]
-  rw [flag_loop isNumeric values true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop isNumeric values true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
 
 -- post-conditions-start
@@ -119,6 +125,9 @@
   intro data
   unfold problem_spec_parsableInfo implementation_parsableInfo
   simp only [Id.run, bind]
-  rw [flag_loop looksNumeric data true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop looksNumeric data true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
```

Attack 6 — `atk6_constfalse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_numericPassthrough (values : List Element) : Bool := Id.run do
-  let mut isNumlike := true
-  for v in values do
-    if !isNumeric v then
-      isNumlike := false
-  return (!values.isEmpty && isNumlike)
+def implementation_numericPassthrough (values : List Element) : Bool :=
+  false
 -- impl-end
 
 -- proof-start
@@ -91,8 +87,11 @@
   intro values
   unfold problem_spec_numericPassthrough implementation_numericPassthrough
   simp only [Id.run, bind]
-  rw [flag_loop isNumeric values true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop isNumeric values true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
 
 -- post-conditions-start
@@ -103,12 +102,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_parsableInfo (data : List String) : Bool := Id.run do
-  let mut convertible := true
-  for val in data do
-    if !looksNumeric val then
-      convertible := false
-  return (!data.isEmpty && convertible)
+def implementation_parsableInfo (data : List String) : Bool :=
+  false
 -- impl-end
 
 -- proof-start
@@ -119,6 +114,9 @@
   intro data
   unfold problem_spec_parsableInfo implementation_parsableInfo
   simp only [Id.run, bind]
-  rw [flag_loop looksNumeric data true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop looksNumeric data true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
```

Attack 7 — `atk7_len2B.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,8 +91,11 @@
   intro values
   unfold problem_spec_numericPassthrough implementation_numericPassthrough
   simp only [Id.run, bind]
-  rw [flag_loop isNumeric values true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop isNumeric values true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
 
 -- post-conditions-start
@@ -108,7 +111,7 @@
   for val in data do
     if !looksNumeric val then
       convertible := false
-  return (!data.isEmpty && convertible)
+  return (1 < data.length && convertible)
 -- impl-end
 
 -- proof-start
@@ -119,6 +122,9 @@
   intro data
   unfold problem_spec_parsableInfo implementation_parsableInfo
   simp only [Id.run, bind]
-  rw [flag_loop looksNumeric data true]
-  rfl
+  first
+  | rfl
+  | (rw [flag_loop looksNumeric data true]; rfl)
+  | (simp_all [flag_loop, List.all_eq_true, Bool.and_eq_true]; try rfl)
+  | decide
 -- proof-end
```

Attack 8 — `atk8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,12 +55,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_numericPassthrough (values : List Element) : Bool := Id.run do
-  let mut isNumlike := true
-  for v in values do
-    if !isNumeric v then
-      isNumlike := false
-  return (!values.isEmpty && isNumlike)
+def implementation_numericPassthrough (values : List Element) : Bool :=
+  (!values.isEmpty && values.all isNumeric)
 -- impl-end
 
 -- proof-start
@@ -90,8 +86,6 @@
         (implementation_numericPassthrough values) := by
   intro values
   unfold problem_spec_numericPassthrough implementation_numericPassthrough
-  simp only [Id.run, bind]
-  rw [flag_loop isNumeric values true]
   rfl
 -- proof-end
 
@@ -103,12 +97,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_parsableInfo (data : List String) : Bool := Id.run do
-  let mut convertible := true
-  for val in data do
-    if !looksNumeric val then
-      convertible := false
-  return (!data.isEmpty && convertible)
+def implementation_parsableInfo (data : List String) : Bool :=
+  (!data.isEmpty && data.all looksNumeric)
 -- impl-end
 
 -- proof-start
@@ -118,7 +108,5 @@
         (implementation_parsableInfo data) := by
   intro data
   unfold problem_spec_parsableInfo implementation_parsableInfo
-  simp only [Id.run, bind]
-  rw [flag_loop looksNumeric data true]
   rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether to emit an advisory notification when categorical (string) unit
conversion is asked to handle a sequence of values.

Two independent notifications are governed by the same rule. In each case a
boolean "flag" is computed by scanning every element of the incoming sequence and
checking a per-element property:

* one notification concerns a sequence whose elements are *all* non-string
  numeric values — the situation in which numbers are being pushed through a
  string-oriented converter (an advisory deprecation notice);
* the other concerns a sequence of strings that are *all* individually parsable
  as a number or a date — the situation in which the strings might really have
  been meant as numbers (an informational notice).

A per-element "all" check over an EMPTY sequence is vacuously satisfied, so the
flag alone is `true` even when there is nothing to convert. The desired behavior
is that neither notification fires for an empty sequence: a notification is
emitted exactly when the sequence is non-empty AND its flag holds. This avoids a
spurious, non-actionable notice (and the failure it triggered downstream) when an
empty data structure is plotted on a categorically-united axis.
-/

-- axioms-start
/-- Whether a single string "looks numeric" — i.e. is individually parsable as a
number or a date. This is an unchanged library helper; the notification rule does
not depend on HOW it decides, only on the sequence-level conjunction of its
results, so it is left abstract here. -/
opaque looksNumeric : String → Bool
-- axioms-end

-- pure-start
/-- A classification of one incoming element of a to-be-converted sequence: a
non-string numeric value, versus anything else (a string or other categorical
value). -/
inductive Element where
  | numeric
  | categorical

/-- The per-element property tested for the numeric-passthrough notification:
the element is a non-string numeric value. -/
def isNumeric : Element → Bool
  | .numeric => true
  | .categorical => false
-- pure-end

-- post-conditions-start
/-- The numeric-passthrough advisory fires exactly when the sequence is non-empty
and every element is a non-string numeric value. -/
def problem_spec_numericPassthrough (values : List Element) (result : Bool) : Prop :=
  result = (!values.isEmpty && values.all isNumeric)
-- post-conditions-end

-- impl-start
def implementation_numericPassthrough (values : List Element) : Bool := Id.run do
  let mut isNumlike := true
  for v in values do
    if !isNumeric v then
      isNumlike := false
  return (!values.isEmpty && isNumlike)
-- impl-end

-- proof-start
/-- The scanning loop sets its boolean accumulator to `init && values.all p`,
where `p` is the per-element predicate tested in the loop body. Generalized over
the accumulator so the cons step's IH applies. -/
private theorem flag_loop {α : Type} (p : α → Bool) (values : List α) (init : Bool) :
    (forIn (m := Id) values init fun v r =>
      if (!p v) = true then pure (ForInStep.yield false)
      else pure (ForInStep.yield r)) = (init && values.all p) := by
  induction values generalizing init with
  | nil => simp [List.forIn_nil, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    by_cases h : (!p a) = true
    · simp only [h, if_true, List.all_cons, ih]
      simp only [Bool.not_eq_true'] at h
      simp [h]
    · simp only [h, List.all_cons, ih]
      simp only [Bool.not_eq_true, Bool.not_eq_false'] at h
      simp [h]

theorem correct_numericPassthrough :
    ∀ (values : List Element),
      problem_spec_numericPassthrough values
        (implementation_numericPassthrough values) := by
  intro values
  unfold problem_spec_numericPassthrough implementation_numericPassthrough
  simp only [Id.run, bind]
  rw [flag_loop isNumeric values true]
  rfl
-- proof-end

-- post-conditions-start
/-- The parsable-strings informational notice fires exactly when the sequence is
non-empty and every string in it individually looks numeric. -/
def problem_spec_parsableInfo (data : List String) (result : Bool) : Prop :=
  result = (!data.isEmpty && data.all looksNumeric)
-- post-conditions-end

-- impl-start
def implementation_parsableInfo (data : List String) : Bool := Id.run do
  let mut convertible := true
  for val in data do
    if !looksNumeric val then
      convertible := false
  return (!data.isEmpty && convertible)
-- impl-end

-- proof-start
theorem correct_parsableInfo :
    ∀ (data : List String),
      problem_spec_parsableInfo data
        (implementation_parsableInfo data) := by
  intro data
  unfold problem_spec_parsableInfo implementation_parsableInfo
  simp only [Id.run, bind]
  rw [flag_loop looksNumeric data true]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: twin equality specs. problem_spec_numericPassthrough values result := result = (!values.isEmpty && values.all isNumeric); problem_spec_parsableInfo data result := result = (!data.isEmpty && data.all looksNumeric). Both pin the boolean result EXACTLY, so any impl that differs on any input yields an unprovable correct_*.

SAME_SPEC: all 8 attacks + identity confirmed True via swebench_unified.markers.same_spec (axioms/pure/pre/post byte-identical; only impl regions edited).

VERIFY CMD (each): bash scripts/lean_verify.sh <file>. Ran concurrently (<=4 background jobs).
### RESULTS (deduped results.txt):
  atk1_prepatchA (site-A bare isNumlike, drops empty guard) -> EXIT=1 (does NOT verify) - the actual prepatch bug for site A, reproduced.
  atk2_prepatchB (site-B bare convertible) -> EXIT=1 - actual prepatch bug for site B, reproduced.
  atk3_boundaryA (inverted empty guard: values.isEmpty || isNumlike) -> EXIT=1.
  atk4_ctrlB (control-flow-effect: latch convertible:=TRUE on failing elt) -> EXIT=1.
  atk5_partialA (partial-domain: match []=>true else bare flag) -> EXIT=1.
  atk6_constfalse (constant false both legs) -> EXIT=1.
  atk7_len2B (boundary: guard 1 < data.length, drops singleton) -> EXIT=1.
  atk8_echo (ungrounded-oracle echo: impl := spec RHS on both legs) -> EXIT=0 VERIFIES.
All wrong impls used an aggressive closing proof (first | rfl | rw flag_loop; rfl | simp_all | decide) and STILL fail to close - confirming the tight equality spec rejects them.

CLEAN-AXIOM CHECK on the closing artifacts (#print axioms appended, re-verified exit 0):
  pos_control (gold impls, gold proofs): correct_numericPassthrough / correct_parsableInfo depend on [propext, Quot.sound] (clean; no sorry, no looksNumeric_prop).
  atk8_echo: both theorems 'do not depend on any axioms' (clean).

RESOLVE (mandatory for every closing attack): atk8_echo is the ONLY same-spec impl that closes. Its faithful refined patch is the gold patch (both notification sites gated with 'size and flag'; impl echoes spec RHS => identical observable decision). Ran harness.run_resolve('matplotlib__matplotlib-22719', patch, timeout=1800) -> RESOLVED=True COMPLETED=True NOTE='resolved' FLAKY=False. So verify => correct holds for the closing attack; no break.

REFINEMENT.MD AUDIT: legs 1-3 R, 4 I, 5 R, 5a A-reference, 6 R. No kind-3 (undischarged) legs. A-reference looksNumeric <-> UnitData._str_is_convertible: unchanged opaque callee, consumed only structurally (proof uses flag_loop reduction; no looksNumeric_prop axiom - confirmed by clean pos_control axioms). Callee correspondence verified against base_commit a2a1b0a category.py in worktree (convert @55-66, update @222-237, _str_is_convertible @194-207). R/I legs mechanically covered by G-CONF (conformance_check.py oracle=bool(size and flag), shadow=impl transliteration, empty-seq discriminator pinned). Correspondence holds.

CONCLUSION: >=5 distinct wrong impls (7 genuinely-wrong + echo) attacked; none with a closing clean-axiom proof has a non-resolving faithful patch. The equality spec is maximally tight; wrong impls cannot close. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatchA.lean`, `atk2_prepatchB.lean`, `atk3_boundaryA.lean`, `atk4_ctrlB.lean`, `atk5_partialA.lean`, `atk6_constfalse.lean`, `atk7_len2B.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. Both legs are maximally-tight equality specs (result = (!seq.isEmpty && seq.all pred)); every genuinely-wrong impl (atk1-atk7) makes correct_* a false Prop and FAILS to verify (exit 1). Only the gold-equivalent echo (atk8) closes, and its faithful patch = gold patch, which RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatchA.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_prepatchB.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_boundaryA.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_ctrlB.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_partialA.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_constfalse.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_len2B.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether to emit an advisory notification when categorical (string) unit
conversion is asked to handle a sequence of values.

Two independent notifications are governed by the same rule. In each case a
boolean "flag" is computed by scanning every element of the incoming sequence and
checking a per-element property:

* one notification concerns a sequence whose elements are *all* non-string
  numeric values — the situation in which numbers are being pushed through a
  string-oriented converter (an advisory deprecation notice);
* the other concerns a sequence of strings that are *all* individually parsable
  as a number or a date — the situation in which the strings might really have
  been meant as numbers (an informational notice).

A per-element "all" check over an EMPTY sequence is vacuously satisfied, so the
flag alone is `true` even when there is nothing to convert. The desired behavior
is that neither notification fires for an empty sequence: a notification is
emitted exactly when the sequence is non-empty AND its flag holds. This avoids a
spurious, non-actionable notice (and the failure it triggered downstream) when an
empty data structure is plotted on a categorically-united axis.
-/

-- axioms-start
/-- Whether a single string "looks numeric" — i.e. is individually parsable as a
number or a date. This is an unchanged library helper; the notification rule does
not depend on HOW it decides, only on the sequence-level conjunction of its
results, so it is left abstract here. -/
opaque looksNumeric : String → Bool
-- axioms-end

-- pure-start
/-- A classification of one incoming element of a to-be-converted sequence: a
non-string numeric value, versus anything else (a string or other categorical
value). -/
inductive Element where
  | numeric
  | categorical

/-- The per-element property tested for the numeric-passthrough notification:
the element is a non-string numeric value. -/
def isNumeric : Element → Bool
  | .numeric => true
  | .categorical => false
-- pure-end

-- post-conditions-start
/-- The numeric-passthrough advisory fires exactly when the sequence is non-empty
and every element is a non-string numeric value. -/
def problem_spec_numericPassthrough (values : List Element) (result : Bool) : Prop :=
  result = (!values.isEmpty && values.all isNumeric)
-- post-conditions-end

-- impl-start
def implementation_numericPassthrough (values : List Element) : Bool := Id.run do
  let mut isNumlike := true
  for v in values do
    if !isNumeric v then
      isNumlike := false
  return (!values.isEmpty && isNumlike)
-- impl-end

-- proof-start
/-- The scanning loop sets its boolean accumulator to `init && values.all p`,
where `p` is the per-element predicate tested in the loop body. Generalized over
the accumulator so the cons step's IH applies. -/
private theorem flag_loop {α : Type} (p : α → Bool) (values : List α) (init : Bool) :
    (forIn (m := Id) values init fun v r =>
      if (!p v) = true then pure (ForInStep.yield false)
      else pure (ForInStep.yield r)) = (init && values.all p) := by
  induction values generalizing init with
  | nil => simp [List.forIn_nil, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    by_cases h : (!p a) = true
    · simp only [h, if_true, List.all_cons, ih]
      simp only [Bool.not_eq_true'] at h
      simp [h]
    · simp only [h, List.all_cons, ih]
      simp only [Bool.not_eq_true, Bool.not_eq_false'] at h
      simp [h]

theorem correct_numericPassthrough :
    ∀ (values : List Element),
      problem_spec_numericPassthrough values
        (implementation_numericPassthrough values) := by
  intro values
  unfold problem_spec_numericPassthrough implementation_numericPassthrough
  simp only [Id.run, bind]
  rw [flag_loop isNumeric values true]
  rfl
-- proof-end

-- post-conditions-start
/-- The parsable-strings informational notice fires exactly when the sequence is
non-empty and every string in it individually looks numeric. -/
def problem_spec_parsableInfo (data : List String) (result : Bool) : Prop :=
  result = (!data.isEmpty && data.all looksNumeric)
-- post-conditions-end

-- impl-start
def implementation_parsableInfo (data : List String) : Bool := Id.run do
  let mut convertible := true
  for val in data do
    if !looksNumeric val then
      convertible := false
  return (!data.isEmpty && convertible)
-- impl-end

-- proof-start
theorem correct_parsableInfo :
    ∀ (data : List String),
      problem_spec_parsableInfo data
        (implementation_parsableInfo data) := by
  intro data
  unfold problem_spec_parsableInfo implementation_parsableInfo
  simp only [Id.run, bind]
  rw [flag_loop looksNumeric data true]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: twin equality specs. problem_spec_numericPassthrough values result := result = (!values.isEmpty && values.all isNumeric); problem_spec_parsableInfo data result := result = (!data.isEmpty && data.all looksNumeric). Both pin the boolean result EXACTLY, so any impl that differs on any input yields an unprovable correct_*.

SAME_SPEC: all 8 attacks + identity confirmed True via swebench_unified.markers.same_spec (axioms/pure/pre/post byte-identical; only impl regions edited).

VERIFY CMD (each): bash scripts/lean_verify.sh <file>. Ran concurrently (<=4 background jobs).
### RESULTS (deduped results.txt):
  atk1_prepatchA (site-A bare isNumlike, drops empty guard) -> EXIT=1 (does NOT verify) - the actual prepatch bug for site A, reproduced.
  atk2_prepatchB (site-B bare convertible) -> EXIT=1 - actual prepatch bug for site B, reproduced.
  atk3_boundaryA (inverted empty guard: values.isEmpty || isNumlike) -> EXIT=1.
  atk4_ctrlB (control-flow-effect: latch convertible:=TRUE on failing elt) -> EXIT=1.
  atk5_partialA (partial-domain: match []=>true else bare flag) -> EXIT=1.
  atk6_constfalse (constant false both legs) -> EXIT=1.
  atk7_len2B (boundary: guard 1 < data.length, drops singleton) -> EXIT=1.
  atk8_echo (ungrounded-oracle echo: impl := spec RHS on both legs) -> EXIT=0 VERIFIES.
All wrong impls used an aggressive closing proof (first | rfl | rw flag_loop; rfl | simp_all | decide) and STILL fail to close - confirming the tight equality spec rejects them.

CLEAN-AXIOM CHECK on the closing artifacts (#print axioms appended, re-verified exit 0):
  pos_control (gold impls, gold proofs): correct_numericPassthrough / correct_parsableInfo depend on [propext, Quot.sound] (clean; no sorry, no looksNumeric_prop).
  atk8_echo: both theorems 'do not depend on any axioms' (clean).

RESOLVE (mandatory for every closing attack): atk8_echo is the ONLY same-spec impl that closes. Its faithful refined patch is the gold patch (both notification sites gated with 'size and flag'; impl echoes spec RHS => identical observable decision). Ran harness.run_resolve('matplotlib__matplotlib-22719', patch, timeout=1800) -> RESOLVED=True COMPLETED=True NOTE='resolved' FLAKY=False. So verify => correct holds for the closing attack; no break.

REFINEMENT.MD AUDIT: legs 1-3 R, 4 I, 5 R, 5a A-reference, 6 R. No kind-3 (undischarged) legs. A-reference looksNumeric <-> UnitData._str_is_convertible: unchanged opaque callee, consumed only structurally (proof uses flag_loop reduction; no looksNumeric_prop axiom - confirmed by clean pos_control axioms). Callee correspondence verified against base_commit a2a1b0a category.py in worktree (convert @55-66, update @222-237, _str_is_convertible @194-207). R/I legs mechanically covered by G-CONF (conformance_check.py oracle=bool(size and flag), shadow=impl transliteration, empty-seq discriminator pinned). Correspondence holds.

CONCLUSION: >=5 distinct wrong impls (7 genuinely-wrong + echo) attacked; none with a closing clean-axiom proof has a non-resolving faithful patch. The equality spec is maximally tight; wrong impls cannot close. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO diverging input; the modeled functions agree with the real post-patch category.py on all inputs.

Real callee (post-patch, category.py, base a2a1b0a):
  - convert: is_numlike = all(units.ConversionInterface.is_numlike(v) and not isinstance(v,(str,bytes)) for v in values); decision = bool(values.size and is_numlike), values = np.atleast_1d(np.array(value,dtype=object)).
  - update: convertible latched over OrderedDict.fromkeys(data) via _str_is_convertible; decision = bool(data.size and convertible), data = np.atleast_1d(np.array(data,dtype=object)).

Model:
  - problem_spec_numericPassthrough: result = (!values.isEmpty && values.all isNumeric).
  - problem_spec_parsableInfo: result = (!data.isEmpty && data.all looksNumeric).

Faithfulness checks (all pass):
1. Solution.lean compiles under lean_verify.sh (exit 0); #print axioms correct_numericPassthrough / correct_parsableInfo = [propext, Quot.sound] — no sorryAx, proofs are genuine.
2. same_spec(Solution, prepatch_1)=True, same_spec(Solution, prepatch_2)=True (lean backend tables); spec region frozen across the two G-DIFF variants.
3. Site-1: the numeric-passthrough predicate is(v)=is_numlike(v) and not isinstance(v,(str,bytes)) is total and baked into the Element classification (numeric/categorical); values.all isNumeric == the real all(...) conjunction; values.size==(!values.isEmpty) since atleast_1d list is empty iff array empty. Agrees on empty→False (post-patch, was True pre-patch — the fix), all-numeric-nonempty→True, mixed→False.
4. Site-2: real loop tests _str_is_convertible only over unique values (OrderedDict.fromkeys) and latches; a conjunction is invariant under dedup/reorder, and data.size is measured on the FULL (non-deduped) array which is empty iff the unique set is empty, so data.all looksNumeric && !data.isEmpty faithfully reproduces bool(data.size and convertible). _str_is_convertible is total (try/except → bool), matching opaque looksNumeric : String → Bool; the decision never depends on its value for any specific string, so declaring it signature-only (A-reference, G-AX skip) is correct — no over- or under-constraint.
5. Orthogonal real ops (warn_deprecated text, float cast, mapping update, check_isinstance TypeError) do not affect the modeled boolean decision, so omitting them does not make the spec disagree with the callee's decision output. np.atleast_1d scalar→1-elem and empty→empty are consistently reflected by the List model; the empty-vs-nonempty discriminator (the entire bug) is preserved.

The spec is not too strong and does not drift from real repo behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction audit for matplotlib__matplotlib-22719 (lean). VERIFIED with swebench_unified.markers over LeanBackend: (1) same_spec is True for all pairs among Solution.lean / Solution_prepatch_1.lean / Solution_prepatch_2.lean — the spec region is byte-identical (frozen); (2) spec_view properly elides both impl and proof regions (ELISION_IMPL/ELISION_PROOF placeholders present); no impl code ('let mut', 'return', '!_.isEmpty && ...') leaks into the consumer view. Lexical scan of the spec view found ZERO gold-patch artifacts: no 'category.py', 'values.size', 'data.size', 'is_numlike', 'convertible', '_str_is_convertible', 'StrCategoryConverter', 'UnitData', 'isinstance', 'warn_deprecated', numpy code, or diff text. What the spec view exposes is (a) an abstract behavioral docstring and (b) two postconditions of the form result = (!seq.isEmpty && seq.all pred). This behavior — 'the notice must NOT fire for empty data; it fires exactly when the sequence is non-empty AND its per-element flag holds' — is directly derivable from the PUBLIC problem_statement alone, which reports the spurious MatplotlibDeprecationWarning fired on empty data ([], plotted on a category-united axis) and states the expected outcome that it should not (the false-alarm/empty-data edge case). The second modeled site (parsableInfo / info-log) is not named in the problem_statement but is modeled purely abstractly (opaque looksNumeric, generic conjunction) and is the structurally-identical mirror of the same 'all() is vacuously true on empty' bug; it discloses no gold-patch code mechanics and no fix specifics beyond the empty-sequence principle already public. Note: this judgment excludes hints_text (which contains an explicit patch sketch) per scope — even so, the spec only encodes correct behavior in abstract Lean terms and does not quote gold-patch specifics or problem-statement phrasing. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

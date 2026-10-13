# P2 adversarial audit — django__django-13112

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's `ensures out = normalizedRef ref` fully pins the output over the modeled domain (require: ≤1 dot AND all code points <128), which contains every string model reference the tests exercise — including the F2P input `MiXedCase_migrations.Author` (1 dot, ASCII) and all P2P inputs. No verifying same-spec impl produces a faithful patch that fails to resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is the normalization of a
@@ -69,11 +69,7 @@
   ensures out = normalizedRef ref
   do
     -- impl-start
-    let result : List Char :=
-      if ref.contains '.' then
-        (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
-      else
-        ref.map Char.toLower
+    let result : List Char := ref.map Char.toLower
     return result
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is the normalization of a
@@ -73,7 +73,7 @@
       if ref.contains '.' then
         (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
       else
-        ref.map Char.toLower
+        ref
     return result
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is the normalization of a
@@ -71,7 +71,7 @@
     -- impl-start
     let result : List Char :=
       if ref.contains '.' then
-        (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
+        (ref.takeWhile (· ≠ '.')).map Char.toLower ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
       else
         ref.map Char.toLower
     return result
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is the normalization of a
@@ -70,7 +70,7 @@
   do
     -- impl-start
     let result : List Char :=
-      if ref.contains '.' then
+      if ref.any (· = '.') then
         (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
       else
         ref.map Char.toLower
@@ -80,3 +80,5 @@
 prove_correct normalizeRef by
   loom_solve
   simp only [normalizedRef, isQualified, appPart, namePart, foldCase]
+  congr 1
+  simp [List.any_eq_true, List.contains_eq_any_beq, beq_iff_eq]
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is the normalization of a
@@ -70,7 +70,7 @@
   do
     -- impl-start
     let result : List Char :=
-      if ref.contains '.' then
+      if (ref.filter (· = '.')).length == 1 then
         (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
       else
         ref.map Char.toLower
@@ -80,3 +80,27 @@
 prove_correct normalizeRef by
   loom_solve
   simp only [normalizedRef, isQualified, appPart, namePart, foldCase]
+  have hcontains : ref.contains '.' = decide ((ref.filter (· = '.')).length = 1) := by
+    by_cases hc : ref.contains '.' = true
+    · have hmem : '.' ∈ ref := List.mem_of_elem_eq_true hc
+      have hmf : '.' ∈ ref.filter (· = '.') := by simp [List.mem_filter, hmem]
+      have hpos : 0 < (ref.filter (· = '.')).length :=
+        List.length_pos_iff.mpr (by intro he; rw [he] at hmf; simp at hmf)
+      have h1 : (ref.filter (· = '.')).length = 1 := by omega
+      simp [h1, hmem]
+    · have hc' : ref.contains '.' = false := by simpa using hc
+      have hnm : '.' ∉ ref := by
+        intro hm
+        exact hc (List.elem_eq_true_of_mem hm)
+      have hempty : ref.filter (· = '.') = [] := by
+        rcases hf : ref.filter (· = '.') with _ | ⟨a, t⟩
+        · rfl
+        · exfalso
+          have hain : a ∈ ref.filter (· = '.') := by rw [hf]; exact List.mem_cons_self
+          have hae : a = '.' := by have := List.of_mem_filter hain; simpa using this
+          exact hnm (hae ▸ List.mem_of_mem_filter hain)
+      simp [hempty, hnm]
+  rw [hcontains]
+  by_cases hb : (ref.filter (· = '.')).length = 1
+  · simp [hb]
+  · simp [hb]
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is the normalization of a
@@ -71,7 +71,7 @@
     -- impl-start
     let result : List Char :=
       if ref.contains '.' then
-        (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
+        (ref.takeWhile (· ≠ '.')) ++ '.' :: ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
       else
         ref.map Char.toLower
     return result
@@ -79,4 +79,4 @@
 
 prove_correct normalizeRef by
   loom_solve
-  simp only [normalizedRef, isQualified, appPart, namePart, foldCase]
+  simp only [normalizedRef, isQualified, appPart, namePart, foldCase, List.append_assoc, List.singleton_append]
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is the normalization of a
@@ -71,9 +71,9 @@
     -- impl-start
     let result : List Char :=
       if ref.contains '.' then
-        (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
+        List.takeWhile (fun c => c ≠ '.') ref ++ (List.cons '.' []) ++ List.map Char.toLower (List.drop 1 (List.dropWhile (fun c => c ≠ '.') ref))
       else
-        ref.map Char.toLower
+        List.map Char.toLower ref
     return result
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is the normalization of a
@@ -70,13 +70,21 @@
   do
     -- impl-start
     let result : List Char :=
-      if ref.contains '.' then
-        (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
+      if ref.all (fun c => c.toNat < 128) then
+        (if ref.contains '.' then
+          (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
+        else
+          ref.map Char.toLower)
       else
-        ref.map Char.toLower
+        ref
     return result
     -- impl-end
 
 prove_correct normalizeRef by
   loom_solve
-  simp only [normalizedRef, isQualified, appPart, namePart, foldCase]
+  have hall : ref.all (fun c => c.toNat < 128) = true := by
+    rw [List.all_eq_true]
+    intro c hc
+    exact decide_eq_true (require_1 c hc)
+  rw [hall]
+  simp only [normalizedRef, isQualified, appPart, namePart, foldCase, if_true]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is the normalization of a
--  model-reference string into its canonical form. It is built entirely from
--  concrete character operations over the input (a case fold of code points and
--  a split on the first dot separator) and is modeled DEEPLY in the `pure`
--  region below. There is no outside callee whose contract is consumed and no
--  A-reference deep model of an outside callee: the per-code-point case fold of
--  an identifier and the dot split are modeled directly, with the Lean↔Python
--  bijection over the ASCII domain (pinned by the `require ∀ c ∈ ref,
--  c.toNat < 128`) recorded in mapping.md §2 and exercised mechanically by
--  conformance_check.py (G-CONF). See refinement.md §C.)
-- axioms-end

-- pure-start
/- Case fold of a code-point sequence: lower every code point. Over the
   identifier alphabet (ASCII letters/digits/underscore — the alphabet of
   application labels and model names, mapping.md §2) this is exactly the
   value-level case fold the reference normalization applies to a model name. -/
def foldCase (s : List Char) : List Char := s.map Char.toLower

/- Whether the reference carries an application qualifier: it contains the dot
   separator that splits an application label from a model name. -/
def isQualified (ref : List Char) : Bool := ref.contains '.'

/- The application-label part: the prefix up to (not including) the first dot. -/
def appPart (ref : List Char) : List Char := ref.takeWhile (· ≠ '.')

/- The model-name part: everything after the first dot. -/
def namePart (ref : List Char) : List Char := (ref.dropWhile (· ≠ '.')).drop 1

/- The normalized model reference. When the reference qualifies a model with an
   application label (a single dot separator), the application label keeps its
   original case and only the model name is case-folded; otherwise the whole
   reference is case-folded. (Front: app label verbatim; back: folded name.) -/
def normalizedRef (ref : List Char) : List Char :=
  if isQualified ref then
    appPart ref ++ ['.'] ++ foldCase (namePart ref)
  else
    foldCase ref
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `ref` is a model reference. A qualified reference carries exactly one dot
   separator (an application label and a model name); the domain therefore
   excludes references with more than one dot. The reference is an ASCII
   code-point sequence (every code point < 128): application labels and model
   names are ASCII identifiers, and on ASCII the per-code-point case fold
   `Char.toLower` coincides exactly with the reference value-level case fold
   (only A–Z fold; no multi-code-point or context-sensitive Unicode folds),
   so the modeled domain is pinned to where that correspondence is exact
   (mapping.md §2–§3). The result is the canonical normalization
   `normalizedRef`. -/
method normalizeRef (ref : List Char) return (out : List Char)
  require (ref.filter (· = '.')).length ≤ 1
  require ∀ c ∈ ref, c.toNat < 128
  ensures out = normalizedRef ref
  do
    -- impl-start
    let result : List Char :=
      if ref.contains '.' then
        (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
      else
        ref.map Char.toLower
    return result
    -- impl-end

prove_correct normalizeRef by
  loom_solve
  simp only [normalizedRef, isQualified, appPart, namePart, foldCase]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED IN; same_spec=True verified for all 8 attacks via swebench_unified.markers.same_spec (velvet); verify via scripts/lean_verify.sh (300s). Positive control pos_control.lean (= gold Solution.lean) verifies (exit 0).

SPEC SHAPE: tight functional spec — `ensures out = normalizedRef ref` fully determines the output on the modeled domain, and `normalizedRef` is a DEEP model (foldCase/appPart/namePart), not an axiom/oracle. refinement.md has NO A-legs (no consumed axiom, no A-reference deep model of an outside callee) — confirmed against mapping.md §5 and refinement.md §C: str.lower/'.' in/str.split are language primitives modeled directly by total Lean list/char ops, R/I only, checked by G-CONF. Model↔patch correspondence (A1–A5 table) holds: gold patch verbatim = patch.diff; F2P test_reference_mixed_case_app_label lands squarely in the pinned domain and normalizedRef models it correctly (app label case preserved, model name folded). No kind-3 legs.

### ATTACKS (all same_spec=True):
- atk_1 (prepatch bug, whole-fold `ref.map Char.toLower`): FAILS verify (exit 1) — reproduces prepatch, wrong on qualified refs with uppercase app label (mirrors Solution_prepatch.lean / G-DIFF). prepatch_reproduced=True.
- atk_2 (partial-domain: fold only qualified branch, identity else): FAILS verify (exit 1) — unqualified uppercase not folded.
- atk_3 (boundary: also fold the app label): FAILS verify (exit 1) — wrong on qualified upper app label.
- atk_4 (echo: `ref.any (·='.')` for the guard): VERIFIES (exit 0) — defeq/equivalent to gold.
- atk_5 (DOMAIN-EXPLOIT: branch on `(filter '.').length == 1` else whole-fold): VERIFIES (exit 0) with a real proof discharging `filter.length==1 ↔ contains '.'` under require_2 (≤1 dot). Differs from gold ONLY on >1-dot refs (outside the pinned domain).
- atk_6 (echo: `'.' :: xs` cons-form instead of `['.'] ++ xs`): VERIFIES (exit 0) — defeq to gold.
- atk_7 (cosmetic defeq echo, function-form takeWhile/List.cons): VERIFIES (exit 0) under gold's own proof script.
- atk_8 (DOMAIN-EXPLOIT: guard on all-ASCII (`ref.all c.toNat<128`) do gold else IDENTITY, no fold): VERIFIES (exit 0) with a real proof using require_1 to discharge the ASCII guard. Differs from gold ONLY on non-ASCII refs (outside the pinned domain).

### RESOLVE (official harness, swebench_unified.harness.run_resolve, django__django-13112, timeout 1800, retries 1):
- GOLD faithful patch (atk_4/atk_6/atk_7 echoes): resolved=True, completed=True, note='resolved'.
- atk_5 faithful patch (`.count('.')==1`): resolved=True, completed=True, note='resolved'. The >1-dot divergence is unreachable by the hidden tests (no >1-dot string model ref anywhere in tests/, and >1-dot refs are not valid Django model references).
- atk_8 faithful patch (all-ASCII guard else identity): resolved=True, completed=True, note='resolved'. The non-ASCII divergence is unreachable (no non-ASCII string model reference reaches deconstruct in the F2P/P2P set; the only non-ASCII test strings, tests/invalid_models_tests/test_relative_fields.py:706/742-743, are rejected as invalid identifiers before deconstruct's str-lower branch).

Every verifying same-spec impl's materialized faithful patch RESOLVES under the official harness (executed, not speculated). No verify⇏correct witness exists. Attack verifications were scheduled concurrently (≤4 background Bash jobs); the three resolve runs ran concurrently as background jobs (run_ids sbu-eq-13112-{gold,atk5,atk8}). Pass criteria unchanged by the schedule.

VERDICT: SOUND — ≥5 attacks verified (atk_4/5/6/7/8), 3 wrong-on-domain attacks correctly rejected, all verifying-attack faithful patches resolve; refinement.md legs are all R/I (no A-legs, no kind-3), correspondence to real callee holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's `ensures out = normalizedRef ref` fully pins the output over the modeled domain (require: ≤1 dot AND all code points <128), which contains every string model reference the tests exercise — including the F2P input `MiXedCase_migrations.Author` (1 dot, ASCII) and all P2P inputs. No verifying same-spec impl produces a faithful patch that fails to resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is the normalization of a
--  model-reference string into its canonical form. It is built entirely from
--  concrete character operations over the input (a case fold of code points and
--  a split on the first dot separator) and is modeled DEEPLY in the `pure`
--  region below. There is no outside callee whose contract is consumed and no
--  A-reference deep model of an outside callee: the per-code-point case fold of
--  an identifier and the dot split are modeled directly, with the Lean↔Python
--  bijection over the ASCII domain (pinned by the `require ∀ c ∈ ref,
--  c.toNat < 128`) recorded in mapping.md §2 and exercised mechanically by
--  conformance_check.py (G-CONF). See refinement.md §C.)
-- axioms-end

-- pure-start
/- Case fold of a code-point sequence: lower every code point. Over the
   identifier alphabet (ASCII letters/digits/underscore — the alphabet of
   application labels and model names, mapping.md §2) this is exactly the
   value-level case fold the reference normalization applies to a model name. -/
def foldCase (s : List Char) : List Char := s.map Char.toLower

/- Whether the reference carries an application qualifier: it contains the dot
   separator that splits an application label from a model name. -/
def isQualified (ref : List Char) : Bool := ref.contains '.'

/- The application-label part: the prefix up to (not including) the first dot. -/
def appPart (ref : List Char) : List Char := ref.takeWhile (· ≠ '.')

/- The model-name part: everything after the first dot. -/
def namePart (ref : List Char) : List Char := (ref.dropWhile (· ≠ '.')).drop 1

/- The normalized model reference. When the reference qualifies a model with an
   application label (a single dot separator), the application label keeps its
   original case and only the model name is case-folded; otherwise the whole
   reference is case-folded. (Front: app label verbatim; back: folded name.) -/
def normalizedRef (ref : List Char) : List Char :=
  if isQualified ref then
    appPart ref ++ ['.'] ++ foldCase (namePart ref)
  else
    foldCase ref
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `ref` is a model reference. A qualified reference carries exactly one dot
   separator (an application label and a model name); the domain therefore
   excludes references with more than one dot. The reference is an ASCII
   code-point sequence (every code point < 128): application labels and model
   names are ASCII identifiers, and on ASCII the per-code-point case fold
   `Char.toLower` coincides exactly with the reference value-level case fold
   (only A–Z fold; no multi-code-point or context-sensitive Unicode folds),
   so the modeled domain is pinned to where that correspondence is exact
   (mapping.md §2–§3). The result is the canonical normalization
   `normalizedRef`. -/
method normalizeRef (ref : List Char) return (out : List Char)
  require (ref.filter (· = '.')).length ≤ 1
  require ∀ c ∈ ref, c.toNat < 128
  ensures out = normalizedRef ref
  do
    -- impl-start
    let result : List Char :=
      if ref.contains '.' then
        (ref.takeWhile (· ≠ '.')) ++ ['.'] ++ ((ref.dropWhile (· ≠ '.')).drop 1).map Char.toLower
      else
        ref.map Char.toLower
    return result
    -- impl-end

prove_correct normalizeRef by
  loom_solve
  simp only [normalizedRef, isQualified, appPart, namePart, foldCase]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED IN; same_spec=True verified for all 8 attacks via swebench_unified.markers.same_spec (velvet); verify via scripts/lean_verify.sh (300s). Positive control pos_control.lean (= gold Solution.lean) verifies (exit 0).

SPEC SHAPE: tight functional spec — `ensures out = normalizedRef ref` fully determines the output on the modeled domain, and `normalizedRef` is a DEEP model (foldCase/appPart/namePart), not an axiom/oracle. refinement.md has NO A-legs (no consumed axiom, no A-reference deep model of an outside callee) — confirmed against mapping.md §5 and refinement.md §C: str.lower/'.' in/str.split are language primitives modeled directly by total Lean list/char ops, R/I only, checked by G-CONF. Model↔patch correspondence (A1–A5 table) holds: gold patch verbatim = patch.diff; F2P test_reference_mixed_case_app_label lands squarely in the pinned domain and normalizedRef models it correctly (app label case preserved, model name folded). No kind-3 legs.

### ATTACKS (all same_spec=True):
- atk_1 (prepatch bug, whole-fold `ref.map Char.toLower`): FAILS verify (exit 1) — reproduces prepatch, wrong on qualified refs with uppercase app label (mirrors Solution_prepatch.lean / G-DIFF). prepatch_reproduced=True.
- atk_2 (partial-domain: fold only qualified branch, identity else): FAILS verify (exit 1) — unqualified uppercase not folded.
- atk_3 (boundary: also fold the app label): FAILS verify (exit 1) — wrong on qualified upper app label.
- atk_4 (echo: `ref.any (·='.')` for the guard): VERIFIES (exit 0) — defeq/equivalent to gold.
- atk_5 (DOMAIN-EXPLOIT: branch on `(filter '.').length == 1` else whole-fold): VERIFIES (exit 0) with a real proof discharging `filter.length==1 ↔ contains '.'` under require_2 (≤1 dot). Differs from gold ONLY on >1-dot refs (outside the pinned domain).
- atk_6 (echo: `'.' :: xs` cons-form instead of `['.'] ++ xs`): VERIFIES (exit 0) — defeq to gold.
- atk_7 (cosmetic defeq echo, function-form takeWhile/List.cons): VERIFIES (exit 0) under gold's own proof script.
- atk_8 (DOMAIN-EXPLOIT: guard on all-ASCII (`ref.all c.toNat<128`) do gold else IDENTITY, no fold): VERIFIES (exit 0) with a real proof using require_1 to discharge the ASCII guard. Differs from gold ONLY on non-ASCII refs (outside the pinned domain).

### RESOLVE (official harness, swebench_unified.harness.run_resolve, django__django-13112, timeout 1800, retries 1):
- GOLD faithful patch (atk_4/atk_6/atk_7 echoes): resolved=True, completed=True, note='resolved'.
- atk_5 faithful patch (`.count('.')==1`): resolved=True, completed=True, note='resolved'. The >1-dot divergence is unreachable by the hidden tests (no >1-dot string model ref anywhere in tests/, and >1-dot refs are not valid Django model references).
- atk_8 faithful patch (all-ASCII guard else identity): resolved=True, completed=True, note='resolved'. The non-ASCII divergence is unreachable (no non-ASCII string model reference reaches deconstruct in the F2P/P2P set; the only non-ASCII test strings, tests/invalid_models_tests/test_relative_fields.py:706/742-743, are rejected as invalid identifiers before deconstruct's str-lower branch).

Every verifying same-spec impl's materialized faithful patch RESOLVES under the official harness (executed, not speculated). No verify⇏correct witness exists. Attack verifications were scheduled concurrently (≤4 background Bash jobs); the three resolve runs ran concurrently as background jobs (run_ids sbu-eq-13112-{gold,atk5,atk8}). Pass criteria unchanged by the schedule.

VERDICT: SOUND — ≥5 attacks verified (atk_4/5/6/7/8), 3 wrong-on-domain attacks correctly rejected, all verifying-attack faithful patches resolve; refinement.md legs are all R/I (no A-legs, no kind-3), correspondence to real callee holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled function and the real callee on the modeled domain.

Spec region: same_spec(Solution.lean, Solution_prepatch.lean) = True under VelvetBackend.language (byte-identical spec view: axioms/pure/pre/post + method signature with the two requires and `ensures out = normalizedRef ref`). Spec is frozen and clean.

Modeled function: normalizedRef over List Char — qualified (exactly one dot): appPart verbatim ++ '.' ++ foldCase(namePart); unqualified: foldCase whole ref. foldCase = map Char.toLower.

Real callee: patched ForeignObject.deconstruct (related.py:583-587, inherited by ForeignKey) — if '.' in model: app_label,model_name = model.split('.'); to = '%s.%s' % (app_label, model_name.lower()) else to = model.lower(). Driven via models.ForeignKey(ref,...).deconstruct()[3]['to'] on the real repo worktree.

Evidence of agreement across the modeled domain (<=1 dot, all code points ASCII <128):
1. Adversarial edge cases (self/Self/SELF, '', '.', 'a.', '.a', 'A.', '.A', mixed-case app labels, spaces, hyphens, digits, punctuation, tabs): 0 diffs.
2. Full-ASCII (0..127 incl. control/punct/space) random fuzz, 200k inputs, seed 999, len 0..8: 0 diffs.
3. Identifier-alphabet edge cases: 0 diffs.
4. Lean Char.toLower vs Python str.lower over ALL 128 ASCII code points (the one leg the Python shadow doesn't exercise): computed in Lean via lean_verify.sh, 0 mismatches — confirms the foldCase<->lower() leg is exact on the whole pinned domain, not just letters.
5. Lean normalizedRef evaluated DIRECTLY (not the Python transliteration) on 12 representative cases (App.Model->App.model, APP.MODEL->APP.model, MiXedCase_migrations.Author->MiXedCase_migrations.author, '.'->'.', '.A'->'.a', 'A.'->'A.', 'a b.C d'->'a b.c d', etc.) — every result matches the oracle.

Domain fences are honest, not spec-strengthening drift: outside ASCII Python's full Unicode case mapping genuinely diverges from Lean's ASCII-only Char.toLower ('Sigma'.lower()='sigma'/final-sigma, 'Idot'.lower()=2 code points), and >1-dot references raise ValueError from the two-target unpacking of model.split('.') — so both requires pin the domain to exactly where the callee is defined and where the R-refinement bijection is exact. The domain is not narrowed below the region of interest (mixed-case app-label qualified refs — the F2P test_reference_mixed_case_app_label scenario — are inside the domain and correctly modeled). No input in the modeled domain makes normalizedRef disagree with the real deconstruct. Spec is not too strong. G-CONF (100016 inputs, seed 13112) already recorded pass and this independent audit reproduces and extends it.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous G-PANEL-3 leakage/gold-reconstruction review of the velvet spec view for django__django-13112.

METHOD: Generated the consumer spec view via swebench_unified.markers.spec_view (velvet backend) — impl-start/impl-end and prove_correct bodies collapse to placeholders. Confirmed spec region byte-identity with same_spec(Solution.lean, Solution_prepatch.lean) = True (only the elided impl/proof differ, so the frozen consumer view is identical). Ran the mechanical G-LEAK screen (leakage.screen): PASSED, zero hard failures. meta.json records G-LEAK status='pass' ('spec view clean'), relaxed_leakage=None — no relaxation in force, so a strict judgment applies.

GOLD EDIT: patch adds a dotted-reference branch inside ForeignObject.deconstruct (django/db/models/fields/related.py:582-589): `if '.' in self.remote_field.model: app_label, model_name = model.split('.'); kwargs['to'] = '%s.%s' % (app_label, model_name.lower()) else: kwargs['to'] = model.lower()`.

### LEAKAGE ASSESSMENT (beyond problem_statement, NOT hints_text):
- Patched symbols/paths: the spec view names NONE of deconstruct, ForeignObject, ForeignKey, remote_field, kwargs, model.split, related.py, or 'migrations'. All identifiers are abstract (normalizeRef, normalizedRef, foldCase, isQualified, appPart, namePart, ref) and localize no repo edit site.
- No gold-diff line reproduced; no diff markers; no patched file/module path.
- No bug/fix/regression/patch narration in the consumer view. (Solution_prepatch.lean contains 'Pre-image skeleton'/'pre-patch' narration and a differing impl, but it is NOT part of the spec view — the frozen view is byte-identical to Solution.lean's.)
- Behavioral content of the ensures oracle (qualified ref: preserve app-label case, fold only the model name; else fold the whole ref) is exactly the fix the PUBLIC problem_statement already discloses: the report shows the crash stems from lowercasing the mixed-case app label ('DJ_RegLogin' -> lazy ref 'dj_reglogin.category', app 'dj_reglogin' not installed) and that it worked in 3.0. The corrective behavior — do not lowercase the app-label portion of a dotted model reference — is directly derivable from the public report. The spec view adds no edit-localization or reconstruction detail beyond it.
- Encoding correct behavior in the ensures postcondition is intrinsic to the velvet spec-as-oracle design; it does not by itself constitute leakage under the panel-3 standard (leak of the gold EDIT beyond problem_statement). The domain requires (<=1 dot; ASCII) are modeling boundaries, not edit hints.

CONCLUSION: NO-LEAKAGE. Mechanical screen clean, no relaxation, and no spec-view line reveals the gold edit beyond what the public problem_statement already makes derivable.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

# P2 adversarial audit — sphinx-doc__sphinx-7757

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,14 +61,15 @@
 -- impl-start
 def implementation_positionalDefaults
     (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
-  let positionals := nPosonly + nArgs
-  -- Start from the supplied defaults and left-pad with "no default" until there
-  -- is one entry per positional parameter; the defaults thus land on the
-  -- rightmost positions across the whole positional run.
-  let mut padded : List (Option String) := defaults.map some
-  for _ in [padded.length:positionals] do
-    padded := none :: padded
-  return padded
+  let mut params : List (Option String) := []
+  for _ in [0:nPosonly] do
+    params := params ++ [none]
+  for i in [0:nArgs] do
+    if nArgs - i ≤ defaults.length then
+      params := params ++ [some (defaults[defaults.length - (nArgs - i)]!)]
+    else
+      params := params ++ [none]
+  return params
 -- impl-end
 
 -- proof-start
@@ -77,10 +78,11 @@
       defaults.length ≤ nPosonly + nArgs →
       problem_spec_positionalDefaults nPosonly nArgs defaults
         (implementation_positionalDefaults nPosonly nArgs defaults) := by
-  intro nPosonly nArgs defaults _h
+  intro nPosonly nArgs defaults h
   unfold problem_spec_positionalDefaults implementation_positionalDefaults
   simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
     Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
     List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
     bind_pure, Id.run_pure]
+  <;> simp_all <;> omega
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,15 +60,8 @@
 
 -- impl-start
 def implementation_positionalDefaults
-    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
-  let positionals := nPosonly + nArgs
-  -- Start from the supplied defaults and left-pad with "no default" until there
-  -- is one entry per positional parameter; the defaults thus land on the
-  -- rightmost positions across the whole positional run.
-  let mut padded : List (Option String) := defaults.map some
-  for _ in [padded.length:positionals] do
-    padded := none :: padded
-  return padded
+    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
+  defaults.map some
 -- impl-end
 
 -- proof-start
@@ -77,10 +70,11 @@
       defaults.length ≤ nPosonly + nArgs →
       problem_spec_positionalDefaults nPosonly nArgs defaults
         (implementation_positionalDefaults nPosonly nArgs defaults) := by
-  intro nPosonly nArgs defaults _h
+  intro nPosonly nArgs defaults h
   unfold problem_spec_positionalDefaults implementation_positionalDefaults
   simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
     Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
     List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
     bind_pure, Id.run_pure]
+  <;> simp_all <;> omega
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,15 +60,8 @@
 
 -- impl-start
 def implementation_positionalDefaults
-    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
-  let positionals := nPosonly + nArgs
-  -- Start from the supplied defaults and left-pad with "no default" until there
-  -- is one entry per positional parameter; the defaults thus land on the
-  -- rightmost positions across the whole positional run.
-  let mut padded : List (Option String) := defaults.map some
-  for _ in [padded.length:positionals] do
-    padded := none :: padded
-  return padded
+    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
+  List.replicate (nPosonly + nArgs - defaults.length - 1) none ++ defaults.map some
 -- impl-end
 
 -- proof-start
@@ -77,10 +70,11 @@
       defaults.length ≤ nPosonly + nArgs →
       problem_spec_positionalDefaults nPosonly nArgs defaults
         (implementation_positionalDefaults nPosonly nArgs defaults) := by
-  intro nPosonly nArgs defaults _h
+  intro nPosonly nArgs defaults h
   unfold problem_spec_positionalDefaults implementation_positionalDefaults
   simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
     Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
     List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
     bind_pure, Id.run_pure]
+  <;> simp_all <;> omega
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,15 +60,8 @@
 
 -- impl-start
 def implementation_positionalDefaults
-    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
-  let positionals := nPosonly + nArgs
-  -- Start from the supplied defaults and left-pad with "no default" until there
-  -- is one entry per positional parameter; the defaults thus land on the
-  -- rightmost positions across the whole positional run.
-  let mut padded : List (Option String) := defaults.map some
-  for _ in [padded.length:positionals] do
-    padded := none :: padded
-  return padded
+    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
+  defaults.map some ++ List.replicate (nPosonly + nArgs - defaults.length) none
 -- impl-end
 
 -- proof-start
@@ -77,10 +70,11 @@
       defaults.length ≤ nPosonly + nArgs →
       problem_spec_positionalDefaults nPosonly nArgs defaults
         (implementation_positionalDefaults nPosonly nArgs defaults) := by
-  intro nPosonly nArgs defaults _h
+  intro nPosonly nArgs defaults h
   unfold problem_spec_positionalDefaults implementation_positionalDefaults
   simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
     Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
     List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
     bind_pure, Id.run_pure]
+  <;> simp_all <;> omega
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,15 +60,8 @@
 
 -- impl-start
 def implementation_positionalDefaults
-    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
-  let positionals := nPosonly + nArgs
-  -- Start from the supplied defaults and left-pad with "no default" until there
-  -- is one entry per positional parameter; the defaults thus land on the
-  -- rightmost positions across the whole positional run.
-  let mut padded : List (Option String) := defaults.map some
-  for _ in [padded.length:positionals] do
-    padded := none :: padded
-  return padded
+    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
+  List.replicate (nArgs - defaults.length) none ++ defaults.map some
 -- impl-end
 
 -- proof-start
@@ -77,10 +70,11 @@
       defaults.length ≤ nPosonly + nArgs →
       problem_spec_positionalDefaults nPosonly nArgs defaults
         (implementation_positionalDefaults nPosonly nArgs defaults) := by
-  intro nPosonly nArgs defaults _h
+  intro nPosonly nArgs defaults h
   unfold problem_spec_positionalDefaults implementation_positionalDefaults
   simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
     Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
     List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
     bind_pure, Id.run_pure]
+  <;> simp_all <;> omega
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,15 +60,8 @@
 
 -- impl-start
 def implementation_positionalDefaults
-    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
-  let positionals := nPosonly + nArgs
-  -- Start from the supplied defaults and left-pad with "no default" until there
-  -- is one entry per positional parameter; the defaults thus land on the
-  -- rightmost positions across the whole positional run.
-  let mut padded : List (Option String) := defaults.map some
-  for _ in [padded.length:positionals] do
-    padded := none :: padded
-  return padded
+    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
+  List.replicate (nPosonly + nArgs) none
 -- impl-end
 
 -- proof-start
@@ -77,10 +70,11 @@
       defaults.length ≤ nPosonly + nArgs →
       problem_spec_positionalDefaults nPosonly nArgs defaults
         (implementation_positionalDefaults nPosonly nArgs defaults) := by
-  intro nPosonly nArgs defaults _h
+  intro nPosonly nArgs defaults h
   unfold problem_spec_positionalDefaults implementation_positionalDefaults
   simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
     Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
     List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
     bind_pure, Id.run_pure]
+  <;> simp_all <;> omega
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,15 +60,8 @@
 
 -- impl-start
 def implementation_positionalDefaults
-    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
-  let positionals := nPosonly + nArgs
-  -- Start from the supplied defaults and left-pad with "no default" until there
-  -- is one entry per positional parameter; the defaults thus land on the
-  -- rightmost positions across the whole positional run.
-  let mut padded : List (Option String) := defaults.map some
-  for _ in [padded.length:positionals] do
-    padded := none :: padded
-  return padded
+    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
+  List.replicate (nPosonly + nArgs - defaults.length) (some "") ++ defaults.map some
 -- impl-end
 
 -- proof-start
@@ -77,10 +70,11 @@
       defaults.length ≤ nPosonly + nArgs →
       problem_spec_positionalDefaults nPosonly nArgs defaults
         (implementation_positionalDefaults nPosonly nArgs defaults) := by
-  intro nPosonly nArgs defaults _h
+  intro nPosonly nArgs defaults h
   unfold problem_spec_positionalDefaults implementation_positionalDefaults
   simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
     Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
     List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
     bind_pure, Id.run_pure]
+  <;> simp_all <;> omega
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Attaching default values to the positional parameters of a parsed function
signature.

A function's positional parameters come in two consecutive groups: first the
positional-only parameters (there are `nPosonly` of them), then the
positional-or-keyword parameters (there are `nArgs` of them). Separately, the
signature supplies a list of default-value expressions. By the usual rule for
positional parameters, the supplied defaults fill the parameters from the right:
the LAST `defaults.length` positional parameters carry the given defaults, in
order, and every earlier positional parameter has no default.

This holds across the WHOLE positional run — the positional-only group and the
positional-or-keyword group are treated as one sequence for the purpose of lining
defaults up with parameters. So when a positional-only parameter is among the
rightmost ones, it keeps its default just like a positional-or-keyword parameter
would.

The result reports, for each positional parameter in order (positional-only
parameters first, then positional-or-keyword parameters), the default it carries:
`some d` when it has default expression `d`, or `none` when it has no default.
-/

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The modeled behavior is
-- the pure alignment of supplied default-value expressions to positional
-- parameters; the parser that produces the parameter groups and default
-- expressions, and the routine that renders a default expression back to text,
-- are modeled by the abstract inputs directly (a count of each parameter group
-- and the list of default expressions as text). No `axiom <callee>_prop` is
-- consumed by the proof.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- Specification of the default carried by each positional parameter.

`nPosonly` is the number of positional-only parameters, `nArgs` the number of
positional-or-keyword parameters, and `defaults` the supplied default-value
expressions (as text), which fill the rightmost positional parameters.

`result` lists, for each of the `nPosonly + nArgs` positional parameters in order
(positional-only first, then positional-or-keyword), `some d` if it carries
default expression `d`, otherwise `none`. The supplied defaults occupy the last
`defaults.length` positions in order, and every earlier position has no default —
hence the result is `defaults.length` fewer-than-`nPosonly+nArgs` `none`s followed
by the defaults wrapped in `some`. -/
def problem_spec_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String)
    (result : List (Option String)) : Prop :=
  result = List.replicate (nPosonly + nArgs - defaults.length) none
            ++ defaults.map some
-- post-conditions-end

-- impl-start
def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
  let positionals := nPosonly + nArgs
  -- Start from the supplied defaults and left-pad with "no default" until there
  -- is one entry per positional parameter; the defaults thus land on the
  -- rightmost positions across the whole positional run.
  let mut padded : List (Option String) := defaults.map some
  for _ in [padded.length:positionals] do
    padded := none :: padded
  return padded
-- impl-end

-- proof-start
theorem correct_positionalDefaults :
    ∀ (nPosonly nArgs : Nat) (defaults : List String),
      defaults.length ≤ nPosonly + nArgs →
      problem_spec_positionalDefaults nPosonly nArgs defaults
        (implementation_positionalDefaults nPosonly nArgs defaults) := by
  intro nPosonly nArgs defaults _h
  unfold problem_spec_positionalDefaults implementation_positionalDefaults
  simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
    Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
    List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
    bind_pure, Id.run_pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_positionalDefaults is a fully-pinned closed functional equation: result = List.replicate (nPosonly+nArgs - defaults.length) none ++ defaults.map some. Any impl whose output list differs is decidably unequal to the RHS, so its proof cannot close. Attempted 7 DISTINCT same-spec wrong impls (all same_spec=True verified via swebench_unified.markers.same_spec, lean backend): atk_1 = prepatch bug (posonly params always none + regular group aligns defaults only among itself — the exact dropped-b=0 defect from patch.diff/mapping.md); atk_2 = partial-domain (defaults.map some, no left-pad, only correct when defaults fills all positions); atk_3 = boundary off-by-one (pad to positionals-1); atk_4 = control-flow-effect (right-pad: defaults on LEFT, none on right); atk_5 = ungrounded/ignore-posonly (pad count uses nArgs only); atk_6 = all-none (drops all defaults); atk_7 = wrong sentinel (some "" instead of none in the pad).

Commands: bash scripts/lean_verify.sh <file>, run concurrently ≤4 at a time.
Results: pos.lean exit=0 (VERIFIES); atk_1..atk_7 ALL exit=1 (genuine proof errors, e.g. atk_2 'simp made no progress'; grep confirms NO 'sorry' and NO 124 timeout in any attack output). Positive control #print axioms correct_positionalDefaults => [propext, Classical.choice, Quot.sound] (clean, no sorryAx/native).

Since NO wrong impl closed with a clean-axiom proof, the step-2 obligation (materialize + run_resolve every closing wrong impl's faithful patch) is vacuously satisfied — there is no verifying-but-incorrect impl to exhibit. verify⇒correct holds on all attacks tried.

A-leg audit: meta.json declares axioms=[] and deep_model_references=[]; G-AX status=pass (skip, behavior modeled deeply into List String input + Option String result). refinement.md legs are all R/I (ops 1&3 R; ops 2,4,5 I) — NO A-tagged content, no kind-3 leg, so no A-leg correspondence to real callees can be falsified. G-CONF passed (shadow_provenance=transliterated). The R/I legs are G-CONF's mandate; nothing to break there.

Verdict SOUND: ≥5 (7) distinct same-spec attacks run under the official verifier, none verifies, positive control verifies with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Attaching default values to the positional parameters of a parsed function
signature.

A function's positional parameters come in two consecutive groups: first the
positional-only parameters (there are `nPosonly` of them), then the
positional-or-keyword parameters (there are `nArgs` of them). Separately, the
signature supplies a list of default-value expressions. By the usual rule for
positional parameters, the supplied defaults fill the parameters from the right:
the LAST `defaults.length` positional parameters carry the given defaults, in
order, and every earlier positional parameter has no default.

This holds across the WHOLE positional run — the positional-only group and the
positional-or-keyword group are treated as one sequence for the purpose of lining
defaults up with parameters. So when a positional-only parameter is among the
rightmost ones, it keeps its default just like a positional-or-keyword parameter
would.

The result reports, for each positional parameter in order (positional-only
parameters first, then positional-or-keyword parameters), the default it carries:
`some d` when it has default expression `d`, or `none` when it has no default.
-/

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The modeled behavior is
-- the pure alignment of supplied default-value expressions to positional
-- parameters; the parser that produces the parameter groups and default
-- expressions, and the routine that renders a default expression back to text,
-- are modeled by the abstract inputs directly (a count of each parameter group
-- and the list of default expressions as text). No `axiom <callee>_prop` is
-- consumed by the proof.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- Specification of the default carried by each positional parameter.

`nPosonly` is the number of positional-only parameters, `nArgs` the number of
positional-or-keyword parameters, and `defaults` the supplied default-value
expressions (as text), which fill the rightmost positional parameters.

`result` lists, for each of the `nPosonly + nArgs` positional parameters in order
(positional-only first, then positional-or-keyword), `some d` if it carries
default expression `d`, otherwise `none`. The supplied defaults occupy the last
`defaults.length` positions in order, and every earlier position has no default —
hence the result is `defaults.length` fewer-than-`nPosonly+nArgs` `none`s followed
by the defaults wrapped in `some`. -/
def problem_spec_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String)
    (result : List (Option String)) : Prop :=
  result = List.replicate (nPosonly + nArgs - defaults.length) none
            ++ defaults.map some
-- post-conditions-end

-- impl-start
def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
  let positionals := nPosonly + nArgs
  -- Start from the supplied defaults and left-pad with "no default" until there
  -- is one entry per positional parameter; the defaults thus land on the
  -- rightmost positions across the whole positional run.
  let mut padded : List (Option String) := defaults.map some
  for _ in [padded.length:positionals] do
    padded := none :: padded
  return padded
-- impl-end

-- proof-start
theorem correct_positionalDefaults :
    ∀ (nPosonly nArgs : Nat) (defaults : List String),
      defaults.length ≤ nPosonly + nArgs →
      problem_spec_positionalDefaults nPosonly nArgs defaults
        (implementation_positionalDefaults nPosonly nArgs defaults) := by
  intro nPosonly nArgs defaults _h
  unfold problem_spec_positionalDefaults implementation_positionalDefaults
  simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
    Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
    List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
    bind_pure, Id.run_pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_positionalDefaults is a fully-pinned closed functional equation: result = List.replicate (nPosonly+nArgs - defaults.length) none ++ defaults.map some. Any impl whose output list differs is decidably unequal to the RHS, so its proof cannot close. Attempted 7 DISTINCT same-spec wrong impls (all same_spec=True verified via swebench_unified.markers.same_spec, lean backend): atk_1 = prepatch bug (posonly params always none + regular group aligns defaults only among itself — the exact dropped-b=0 defect from patch.diff/mapping.md); atk_2 = partial-domain (defaults.map some, no left-pad, only correct when defaults fills all positions); atk_3 = boundary off-by-one (pad to positionals-1); atk_4 = control-flow-effect (right-pad: defaults on LEFT, none on right); atk_5 = ungrounded/ignore-posonly (pad count uses nArgs only); atk_6 = all-none (drops all defaults); atk_7 = wrong sentinel (some "" instead of none in the pad).

Commands: bash scripts/lean_verify.sh <file>, run concurrently ≤4 at a time.
Results: pos.lean exit=0 (VERIFIES); atk_1..atk_7 ALL exit=1 (genuine proof errors, e.g. atk_2 'simp made no progress'; grep confirms NO 'sorry' and NO 124 timeout in any attack output). Positive control #print axioms correct_positionalDefaults => [propext, Classical.choice, Quot.sound] (clean, no sorryAx/native).

Since NO wrong impl closed with a clean-axiom proof, the step-2 obligation (materialize + run_resolve every closing wrong impl's faithful patch) is vacuously satisfied — there is no verifying-but-incorrect impl to exhibit. verify⇒correct holds on all attacks tried.

A-leg audit: meta.json declares axioms=[] and deep_model_references=[]; G-AX status=pass (skip, behavior modeled deeply into List String input + Option String result). refinement.md legs are all R/I (ops 1&3 R; ops 2,4,5 I) — NO A-tagged content, no kind-3 leg, so no A-leg correspondence to real callees can be falsified. G-CONF passed (shadow_provenance=transliterated). The R/I legs are G-CONF's mandate; nothing to break there.

Verdict SOUND: ≥5 (7) distinct same-spec attacks run under the official verifier, none verifies, positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verification performed: (1) scripts/lean_verify.sh on Solution.lean -> exit 0; #print axioms correct_positionalDefaults = [propext, Classical.choice, Quot.sound], no sorryAx (real proof). (2) markers.same_spec(Solution, Solution_prepatch, LeanBackend.language) = True — spec region byte-identical. (3) Faithfulness: built git worktree at base_commit 212fd67b, applied patch.diff, ran real post-patch signature_from_str over exhaustive (nPosonly,nArgs in 0..5 x all legal default-list lengths) + random defaults (seed 7757, unparse-stable tokens) = 864 checks, 0 divergences vs spec `replicate(nPosonly+nArgs-len) none ++ defaults.map some`. Bug-fix discriminator `(a,b=0,/,c=1)` faithful. Spec precondition (len defaults ≤ positionals) is exactly the well-formedness condition of every real signature, so the spec is not too strong. G-CONF replica oracle also independently mirrors the post-patch alignment. Conclusion: spec is FAITHFUL to the real callee; no drift/over-strengthening found.

Counterexample / evidence:

```
n/a — no input makes problem_spec_positionalDefaults disagree with post-patch signature_from_str under the precondition defaults.length ≤ nPosonly+nArgs (which holds for all well-formed signatures). Verified: real `(a, b=0, /, c=1)` positional defaults = [None,'0','1'] == spec [None,'0','1'].
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view (imports + docstring + axioms/pure notes + post-conditions region) elides impl-start and proof-start ('supplied by the consumer'), so the gold implementation and proof are not exposed. same_spec(Solution, Solution_prepatch)=True — spec region byte-identical, so it cannot encode the fix. Mechanical G-LEAK screen (leakage.screen) PASSES with zero hard failures: no gold-patch line reproduced (left-pad loop / defaults.insert(0, Parameter.empty) / defaults[i+posonlyargs] all absent), no diff markers, no patched file path (sphinx/util/inspect.py) or module, and the only distinctive changed symbol 'signature_from_str' does not appear in any identifier or comment. No narration terms.

Semantic judgment: the spec states the CORRECT behavior — supplied defaults fill the rightmost positional parameters across the whole positional run (posonly+regular as one sequence), result = replicate(nPosonly+nArgs-defaults.length) none ++ defaults.map some. This is a faithful abstract formalization of behavior ALREADY fully public in problem_statement, which names the bug ('default value for positional only argument has vanished'), the exact repro foo(a, b=0, /, c=1), and the expected behavior ('The default value is shown'). Describing correct semantics is the intrinsic role of a spec and does not leak the concrete gold edit beyond the public problem_statement. No line permits reconstructing the Python diff. relaxed_leakage flag not set; recorded G-LEAK status 'pass'. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

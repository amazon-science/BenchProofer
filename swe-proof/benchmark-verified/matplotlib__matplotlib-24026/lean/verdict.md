# P2 adversarial audit — matplotlib__matplotlib-24026

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl both closes with clean axioms AND has a non-resolving faithful patch.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,8 @@
 def implementation_stackplotColors
     (colors : List String) (n : Nat) : Except String (List String) := Id.run do
   let mut r : List String := []
-  for i in [0:n] do
-    r := r ++ [nthColor colors i]
+  for _ in [0:n] do
+    r := r ++ [colors[0]!]
   return Except.ok r
 -- impl-end
 
@@ -66,9 +66,6 @@
         (implementation_stackplotColors colors n) := by
   intro colors n _
   unfold problem_spec_stackplotColors
-  have h : implementation_stackplotColors colors n
-      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
-    unfold implementation_stackplotColors
-    simp [List.range_eq_range']
-  rw [h, foldl_append_eq_map, List.nil_append]
+  unfold implementation_stackplotColors
+  sorry
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
     (colors : List String) (n : Nat) : Except String (List String) := Id.run do
   let mut r : List String := []
   for i in [0:n] do
-    r := r ++ [nthColor colors i]
+    r := r ++ [nthColor colors (n - 1 - i)]
   return Except.ok r
 -- impl-end
 
@@ -66,9 +66,6 @@
         (implementation_stackplotColors colors n) := by
   intro colors n _
   unfold problem_spec_stackplotColors
-  have h : implementation_stackplotColors colors n
-      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
-    unfold implementation_stackplotColors
-    simp [List.range_eq_range']
-  rw [h, foldl_append_eq_map, List.nil_append]
+  unfold implementation_stackplotColors
+  sorry
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,11 +44,8 @@
 
 -- impl-start
 def implementation_stackplotColors
-    (colors : List String) (n : Nat) : Except String (List String) := Id.run do
-  let mut r : List String := []
-  for i in [0:n] do
-    r := r ++ [nthColor colors i]
-  return Except.ok r
+    (colors : List String) (n : Nat) : Except String (List String) :=
+  Except.ok []
 -- impl-end
 
 -- proof-start
@@ -66,9 +63,6 @@
         (implementation_stackplotColors colors n) := by
   intro colors n _
   unfold problem_spec_stackplotColors
-  have h : implementation_stackplotColors colors n
-      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
-    unfold implementation_stackplotColors
-    simp [List.range_eq_range']
-  rw [h, foldl_append_eq_map, List.nil_append]
+  unfold implementation_stackplotColors
+  sorry
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,8 +43,16 @@
 -- post-conditions-end
 
 -- impl-start
+def isCycleRef (s : String) : Bool :=
+  match s.toList with
+  | ['C', d] => d.isDigit
+  | _ => false
+
 def implementation_stackplotColors
     (colors : List String) (n : Nat) : Except String (List String) := Id.run do
+  for c in colors do
+    if isCycleRef c then
+      return Except.error "Cannot put cycle reference in prop_cycler"
   let mut r : List String := []
   for i in [0:n] do
     r := r ++ [nthColor colors i]
@@ -66,9 +74,6 @@
         (implementation_stackplotColors colors n) := by
   intro colors n _
   unfold problem_spec_stackplotColors
-  have h : implementation_stackplotColors colors n
-      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
-    unfold implementation_stackplotColors
-    simp [List.range_eq_range']
-  rw [h, foldl_append_eq_map, List.nil_append]
+  unfold implementation_stackplotColors
+  sorry
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
     (colors : List String) (n : Nat) : Except String (List String) := Id.run do
   let mut r : List String := []
   for i in [0:n] do
-    r := r ++ [nthColor colors i]
+    r := r ++ [nthColor colors (i + 1)]
   return Except.ok r
 -- impl-end
 
@@ -66,9 +66,6 @@
         (implementation_stackplotColors colors n) := by
   intro colors n _
   unfold problem_spec_stackplotColors
-  have h : implementation_stackplotColors colors n
-      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
-    unfold implementation_stackplotColors
-    simp [List.range_eq_range']
-  rw [h, foldl_append_eq_map, List.nil_append]
+  unfold implementation_stackplotColors
+  sorry
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,8 @@
     (colors : List String) (n : Nat) : Except String (List String) := Id.run do
   let mut r : List String := []
   for i in [0:n] do
-    r := r ++ [nthColor colors i]
+    if i + 1 < n then
+      r := r ++ [nthColor colors i]
   return Except.ok r
 -- impl-end
 
@@ -66,9 +67,6 @@
         (implementation_stackplotColors colors n) := by
   intro colors n _
   unfold problem_spec_stackplotColors
-  have h : implementation_stackplotColors colors n
-      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
-    unfold implementation_stackplotColors
-    simp [List.range_eq_range']
-  rw [h, foldl_append_eq_map, List.nil_append]
+  unfold implementation_stackplotColors
+  sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -44,11 +44,8 @@
 
 -- impl-start
 def implementation_stackplotColors
-    (colors : List String) (n : Nat) : Except String (List String) := Id.run do
-  let mut r : List String := []
-  for i in [0:n] do
-    r := r ++ [nthColor colors i]
-  return Except.ok r
+    (colors : List String) (n : Nat) : Except String (List String) :=
+  Except.ok ((List.range n).map (fun i => nthColor colors i))
 -- impl-end
 
 -- proof-start
@@ -65,10 +62,5 @@
       problem_spec_stackplotColors colors n
         (implementation_stackplotColors colors n) := by
   intro colors n _
-  unfold problem_spec_stackplotColors
-  have h : implementation_stackplotColors colors n
-      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
-    unfold implementation_stackplotColors
-    simp [List.range_eq_range']
-  rw [h, foldl_append_eq_map, List.nil_append]
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Assigning colors to a sequence of stacked regions from a caller-supplied
palette.

When a non-empty palette of colors is supplied, the regions of the plot are
colored by walking the palette in order and wrapping around once it is
exhausted: the color of region `i` is the palette entry at position
`i mod (palette size)`. Supplying a palette always succeeds and produces exactly
one color per region — every entry the caller provides is accepted verbatim as a
color, with no further validation that could reject otherwise-meaningful color
tokens.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the cycling behavior is
-- spelled out concretely (modular indexing into the palette over a count of
-- regions), so there is no opaque callee to axiomatize.
-- axioms-end

-- pure-start
/-- The color assigned to region `i` when cycling through `colors`: the palette
entry at index `i mod (palette size)`. For a non-empty palette this is always a
genuine palette entry. -/
def nthColor (colors : List String) (i : Nat) : String :=
  colors[i % colors.length]!
-- pure-end

-- post-conditions-start
/-- Coloring `n` stacked regions from a non-empty palette always succeeds and
yields exactly the `n`-long list whose `i`-th entry is the palette color for
region `i` (cyclic, wrapping at the palette size). The success carrier pins both
the length and every element to the input palette, so no other coloring — and no
failure — satisfies it. -/
def problem_spec_stackplotColors
    (colors : List String) (n : Nat) (result : Except String (List String)) : Prop :=
  result = Except.ok ((List.range n).map (fun i => nthColor colors i))
-- post-conditions-end

-- impl-start
def implementation_stackplotColors
    (colors : List String) (n : Nat) : Except String (List String) := Id.run do
  let mut r : List String := []
  for i in [0:n] do
    r := r ++ [nthColor colors i]
  return Except.ok r
-- impl-end

-- proof-start
/-- The accumulating append-loop equals prepending the accumulator to the map. -/
theorem foldl_append_eq_map (colors : List String) (xs : List Nat) (acc : List String) :
    xs.foldl (fun r i => r ++ [nthColor colors i]) acc
      = acc ++ xs.map (fun i => nthColor colors i) := by
  induction xs generalizing acc with
  | nil => simp
  | cons a as ih => simp [List.foldl_cons, ih, List.append_assoc]

theorem correct_stackplotColors :
    ∀ (colors : List String) (n : Nat), colors ≠ [] →
      problem_spec_stackplotColors colors n
        (implementation_stackplotColors colors n) := by
  intro colors n _
  unfold problem_spec_stackplotColors
  have h : implementation_stackplotColors colors n
      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
    unfold implementation_stackplotColors
    simp [List.range_eq_range']
  rw [h, foldl_append_eq_map, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: post-condition is an EXACT-EQUALITY success carrier `result = Except.ok ((List.range n).map (fun i => nthColor colors i))` with `nthColor colors i = colors[i % colors.length]!`, guarded by precondition `colors ≠ []`. This pins `result` to exactly ONE value per (colors,n) on the modeled domain, so any impl whose `correct_` closes is propositionally equal to the gold observable (always `ok`, exactly n entries, region i = colors[i%len]).

same_spec: all 7 attacks True (project python python; pre-impl/spec/axioms/pure/post regions byte-identical to Solution.lean).

VERIFY CMD: `bash scripts/lean_verify.sh <f>`.

Positive control pos.lean (gold impl, unchanged): exit 0. `#print axioms correct_stackplotColors` = [propext, Classical.choice, Quot.sound] (clean, no sorryAx).

### ATTACKS (6 distinct wrong impls + 1 echo):
- atk_1 constant color (colors[0]! every region): exit 3 (declaration uses 'sorry'; cannot close).
- atk_2 reversed indexing (nthColor colors (n-1-i)): exit 3 (sorry).
- atk_3 partial-domain truncation to Except.ok []: exit 3 (sorry).
- atk_4 PREPATCH BUG re-encoded (CN-token rejection ⇒ Except.error, matches validate_color_for_prop_cycle `^C[0-9]$`): exit 3 (sorry). Prepatch bug reproduced: the buggy impl cannot close the always-`ok` carrier ⇒ prepatch_reproduced=True.
- atk_5 off-by-one boundary (nthColor colors (i+1)): exit 3 (sorry).
- atk_6 control-flow-effect (drops last region via `if i+1<n`): exit 3 (sorry).
- atk_7 ungrounded-oracle ECHO (Except.ok ((List.range n).map (fun i => nthColor colors i)), closed by `rfl`): exit 0. `#print axioms` = 'does not depend on any axioms' (clean, no sorryAx).

RESOLVE (protocol step 2): atk_7 is the ONLY same-spec wrong impl whose proof closes with clean axioms. It is observationally IDENTICAL to the gold (always ok, n entries, region i = colors[i%len]), so its faithful refined patch = the cyclic per-region palette assignment = the gold patch. Materialized as atk_7_patch.diff and RUN through the official harness:
  run_resolve('matplotlib__matplotlib-24026', patch, timeout=1200, retries=1) => RESOLVED=True COMPLETED=True NOTE='resolved' (active bench swe_bench_verified, Docker oracle). F2P test_stackplot[png/pdf] pass.
The echo's patch RESOLVES ⇒ it does NOT break verify⇒correct.

REFINEMENT AUDIT: legs = 1:R, 2:R, 3:A-reference, 4:I, 5:A-reference. No kind-3 (inexpressible) legs, no A-consumed. A-reference legs (leg3 itertools.cycle/next ↔ modular indexing; leg5 absence of CN-rejecting validator ⇒ always ok) correspond to the real patched callees and are mechanically validated by G-CONF (conformance_check.py: 120054 checks over CN/hex/named/mixed palettes + 120k fuzz draws seed 20240629, 0 disagreements). Correspondence holds. colors is None branch (get_next_color) correctly out of model scope via precondition colors≠[].

CONCLUSION: The exact-equality carrier admits exactly one observable; every genuinely-different impl fails to close (6/6 sorry), and the sole closing echo resolves. No closing-clean-axiom impl has a non-resolving faithful patch. verify⇒correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl both closes with clean axioms AND has a non-resolving faithful patch.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Assigning colors to a sequence of stacked regions from a caller-supplied
palette.

When a non-empty palette of colors is supplied, the regions of the plot are
colored by walking the palette in order and wrapping around once it is
exhausted: the color of region `i` is the palette entry at position
`i mod (palette size)`. Supplying a palette always succeeds and produces exactly
one color per region — every entry the caller provides is accepted verbatim as a
color, with no further validation that could reject otherwise-meaningful color
tokens.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the cycling behavior is
-- spelled out concretely (modular indexing into the palette over a count of
-- regions), so there is no opaque callee to axiomatize.
-- axioms-end

-- pure-start
/-- The color assigned to region `i` when cycling through `colors`: the palette
entry at index `i mod (palette size)`. For a non-empty palette this is always a
genuine palette entry. -/
def nthColor (colors : List String) (i : Nat) : String :=
  colors[i % colors.length]!
-- pure-end

-- post-conditions-start
/-- Coloring `n` stacked regions from a non-empty palette always succeeds and
yields exactly the `n`-long list whose `i`-th entry is the palette color for
region `i` (cyclic, wrapping at the palette size). The success carrier pins both
the length and every element to the input palette, so no other coloring — and no
failure — satisfies it. -/
def problem_spec_stackplotColors
    (colors : List String) (n : Nat) (result : Except String (List String)) : Prop :=
  result = Except.ok ((List.range n).map (fun i => nthColor colors i))
-- post-conditions-end

-- impl-start
def implementation_stackplotColors
    (colors : List String) (n : Nat) : Except String (List String) := Id.run do
  let mut r : List String := []
  for i in [0:n] do
    r := r ++ [nthColor colors i]
  return Except.ok r
-- impl-end

-- proof-start
/-- The accumulating append-loop equals prepending the accumulator to the map. -/
theorem foldl_append_eq_map (colors : List String) (xs : List Nat) (acc : List String) :
    xs.foldl (fun r i => r ++ [nthColor colors i]) acc
      = acc ++ xs.map (fun i => nthColor colors i) := by
  induction xs generalizing acc with
  | nil => simp
  | cons a as ih => simp [List.foldl_cons, ih, List.append_assoc]

theorem correct_stackplotColors :
    ∀ (colors : List String) (n : Nat), colors ≠ [] →
      problem_spec_stackplotColors colors n
        (implementation_stackplotColors colors n) := by
  intro colors n _
  unfold problem_spec_stackplotColors
  have h : implementation_stackplotColors colors n
      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
    unfold implementation_stackplotColors
    simp [List.range_eq_range']
  rw [h, foldl_append_eq_map, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: post-condition is an EXACT-EQUALITY success carrier `result = Except.ok ((List.range n).map (fun i => nthColor colors i))` with `nthColor colors i = colors[i % colors.length]!`, guarded by precondition `colors ≠ []`. This pins `result` to exactly ONE value per (colors,n) on the modeled domain, so any impl whose `correct_` closes is propositionally equal to the gold observable (always `ok`, exactly n entries, region i = colors[i%len]).

same_spec: all 7 attacks True (project python python; pre-impl/spec/axioms/pure/post regions byte-identical to Solution.lean).

VERIFY CMD: `bash scripts/lean_verify.sh <f>`.

Positive control pos.lean (gold impl, unchanged): exit 0. `#print axioms correct_stackplotColors` = [propext, Classical.choice, Quot.sound] (clean, no sorryAx).

### ATTACKS (6 distinct wrong impls + 1 echo):
- atk_1 constant color (colors[0]! every region): exit 3 (declaration uses 'sorry'; cannot close).
- atk_2 reversed indexing (nthColor colors (n-1-i)): exit 3 (sorry).
- atk_3 partial-domain truncation to Except.ok []: exit 3 (sorry).
- atk_4 PREPATCH BUG re-encoded (CN-token rejection ⇒ Except.error, matches validate_color_for_prop_cycle `^C[0-9]$`): exit 3 (sorry). Prepatch bug reproduced: the buggy impl cannot close the always-`ok` carrier ⇒ prepatch_reproduced=True.
- atk_5 off-by-one boundary (nthColor colors (i+1)): exit 3 (sorry).
- atk_6 control-flow-effect (drops last region via `if i+1<n`): exit 3 (sorry).
- atk_7 ungrounded-oracle ECHO (Except.ok ((List.range n).map (fun i => nthColor colors i)), closed by `rfl`): exit 0. `#print axioms` = 'does not depend on any axioms' (clean, no sorryAx).

RESOLVE (protocol step 2): atk_7 is the ONLY same-spec wrong impl whose proof closes with clean axioms. It is observationally IDENTICAL to the gold (always ok, n entries, region i = colors[i%len]), so its faithful refined patch = the cyclic per-region palette assignment = the gold patch. Materialized as atk_7_patch.diff and RUN through the official harness:
  run_resolve('matplotlib__matplotlib-24026', patch, timeout=1200, retries=1) => RESOLVED=True COMPLETED=True NOTE='resolved' (active bench swe_bench_verified, Docker oracle). F2P test_stackplot[png/pdf] pass.
The echo's patch RESOLVES ⇒ it does NOT break verify⇒correct.

REFINEMENT AUDIT: legs = 1:R, 2:R, 3:A-reference, 4:I, 5:A-reference. No kind-3 (inexpressible) legs, no A-consumed. A-reference legs (leg3 itertools.cycle/next ↔ modular indexing; leg5 absence of CN-rejecting validator ⇒ always ok) correspond to the real patched callees and are mechanically validated by G-CONF (conformance_check.py: 120054 checks over CN/hex/named/mixed palettes + 120k fuzz draws seed 20240629, 0 disagreements). Correspondence holds. colors is None branch (get_next_color) correctly out of model scope via precondition colors≠[].

CONCLUSION: The exact-equality carrier admits exactly one observable; every genuinely-different impl fails to close (6/6 sorry), and the sole closing echo resolves. No closing-clean-axiom impl has a non-resolving faithful patch. verify⇒correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verification: Solution.lean compiles (lean_verify.sh exit 0); #print axioms correct_stackplotColors = [propext, Classical.choice, Quot.sound] — clean, NO sorryAx, proof genuine. same_spec(Solution, Solution_prepatch, lean)=True (spec region byte-identical). The i-th next() of itertools.cycle(palette) = palette[i%len] = nthColor colors i; pull count = 1 (region 0 fill_between) + len(y)-1 (loop) = n, in order — order/count/value all match the real patched callee. The 'always Except.ok / no validation that rejects tokens' clause precisely encodes the gold fix (removal of validate_color_for_prop_cycle's ^C[0-9]$ rejection). Divergences found are strictly on inputs the documented bijection excludes (to_rgba-invalid strings and n=0/empty row_stack), i.e. a benign type over-approximation, not spec drift or spec-too-strong. Ran an independent extended-token differential (none/grayscale-strings/alpha-hex/tab:/xkcd:/C9/w/k, n up to 9) — 0 in-domain disagreements. Spec is faithful to the real repo behavior on the modeled domain.

Counterexample / evidence:

```
N/A within modeled domain. On every valid color spec (named/hex/alpha-hex/tab:/xkcd:/CN cycle-refs) and n>=1, my differential probe against real matplotlib 3.6.3 found 0 disagreements, matching G-CONF's 120054 checks / 0 disagreements. E.g. colors=['C0','C1','C2'], n=9 -> both give the cyclic RGBA list [C0,C1,C2,C0,C1,C2,C0,C1,C2]; the F2P CN-token acceptance is faithfully modeled.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical to Solution_prepatch.lean: same_spec(Solution, Solution_prepatch, lean-backend)=True; impl+proof regions elided to placeholders in the spec view; spec_view hash matches meta.json region_hashes.spec_view (ffc08c3f...) and G-HYGIENE. hints_text is EMPTY and excluded regardless.

Spec view exposes only: (a) docstring: a non-empty palette 'always succeeds ... every entry accepted verbatim ... with no further validation that could reject otherwise-meaningful color tokens'; (b) nthColor = colors[i % colors.length]! (cyclic palette indexing); (c) problem_spec pinning result = Except.ok of the n-long cyclic map.

Leakage assessment vs the PUBLIC problem_statement: the problem_statement already fully discloses the observable behavioral change the gold enacts — it shows stackplot raising 'ValueError: Cannot put cycle reference (\'C2\') in prop_cycler' via set_prop_cycle -> validate_color_for_prop_cycle on CN tokens, and explicitly asks that stackplot accept CN colors as ax.plot()/Rectangle do, with colors supplied as a palette. The spec-view claim 'always succeeds / no validation that rejects tokens' is a direct restatement of that public ask (accept CN, stop raising), stated as an input->output relation, NOT the solution mechanism.

The cyclic-indexing behavior (nthColor) is PRESERVED across the edit — the pre-patch set_prop_cycle + get_next_color path also cycled through the palette — so it does not reveal the gold edit. Crucially, the spec view names NO implementation mechanism (no itertools.cycle, no next(), no removal of set_prop_cycle). The distinguishing rejecting-validator mechanism lives only inside the elided impl region of Solution_prepatch.lean and is not visible in the spec view. No spec-view line reconstructs the gold edit beyond the public problem_statement. Note: this audit is G-PANEL-3 (leakage) only; the recorded G-PANEL-1 fail (spec-too-weak) is a separate role and out of scope here.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

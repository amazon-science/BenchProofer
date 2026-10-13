# P2 adversarial audit — sympy__sympy-12481

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. All 3 verifying wrong impls' faithful refined patches RESOLVE under the official harness (run_resolve: resolved=true, completed=true, attempts=1, flaky=false for each). No verify-but-not-resolve triple exists among the 10 attacks.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,8 +101,12 @@
     result = Except.error ()
   do
     -- impl-start
+    -- PRE-EXISTING skeleton: a point repeated anywhere in the flattened argument
+    -- is refused outright, even when the repeat only spans distinct groups of the
+    -- grouped reading -- so composable grouped input is refused, contradicting the
+    -- grouped reading's postcondition (G-DIFF).
     let temp := entries.flatten
-    if !pointsDistinct temp && !grouped then
+    if !pointsDistinct temp then
       return Except.error ()
     else
       if !grouped && !rangeCovered temp then
```

Attack 2 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,16 +102,13 @@
   do
     -- impl-start
     let temp := entries.flatten
-    if !pointsDistinct temp && !grouped then
+    if !grouped && !rangeCovered temp then
       return Except.error ()
     else
-      if !grouped && !rangeCovered temp then
-        return Except.error ()
+      if grouped then
+        return Except.ok (arrayForm entries)
       else
-        if grouped then
-          return Except.ok (arrayForm entries)
-        else
-          return Except.ok temp
+        return Except.ok temp
     -- impl-end
 
 prove_correct buildExplicitForm by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,8 @@
     if !pointsDistinct temp && !grouped then
       return Except.error ()
     else
-      if !grouped && !rangeCovered temp then
+      if !grouped && !((List.range (temp.dedup.length - 1)).all
+          (fun i => temp.contains i)) then
         return Except.error ()
       else
         if grouped then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,10 +108,7 @@
       if !grouped && !rangeCovered temp then
         return Except.error ()
       else
-        if grouped then
-          return Except.ok (arrayForm entries)
-        else
-          return Except.ok temp
+        return Except.ok (arrayForm entries)
     -- impl-end
 
 prove_correct buildExplicitForm by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
         return Except.error ()
       else
         if grouped then
-          return Except.ok (arrayForm entries)
+          return Except.ok (arrayForm entries.reverse)
         else
           return Except.ok temp
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,13 +105,10 @@
     if !pointsDistinct temp && !grouped then
       return Except.error ()
     else
-      if !grouped && !rangeCovered temp then
-        return Except.error ()
+      if grouped then
+        return Except.ok (arrayForm entries)
       else
-        if grouped then
-          return Except.ok (arrayForm entries)
-        else
-          return Except.ok temp
+        return Except.ok temp
     -- impl-end
 
 prove_correct buildExplicitForm by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,7 @@
     if !pointsDistinct temp && !grouped then
       return Except.error ()
     else
-      if !grouped && !rangeCovered temp then
+      if !rangeCovered temp then
         return Except.error ()
       else
         if grouped then
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -102,18 +102,30 @@
   do
     -- impl-start
     let temp := entries.flatten
-    if !pointsDistinct temp && !grouped then
+    if grouped && !(entries.all pointsDistinct) then
       return Except.error ()
     else
-      if !grouped && !rangeCovered temp then
+      let temp := entries.flatten
+      if !pointsDistinct temp && !grouped then
         return Except.error ()
       else
-        if grouped then
-          return Except.ok (arrayForm entries)
+        if !grouped && !rangeCovered temp then
+          return Except.error ()
         else
-          return Except.ok temp
+          if grouped then
+            return Except.ok (arrayForm entries)
+          else
+            return Except.ok temp
     -- impl-end
 
 prove_correct buildExplicitForm by
   loom_solve
-  all_goals simp_all [explicitForm]
+  all_goals (
+    first
+      | (intro hg
+         obtain ⟨hne, hnd⟩ := require_1 hg
+         subst hg
+         simp [pointsDistinct, List.all_eq_true] at if_pos
+         obtain ⟨c, hc, hcn⟩ := if_pos
+         exact absurd (hnd c hc) hcn)
+      | simp_all [explicitForm])
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -102,18 +102,34 @@
   do
     -- impl-start
     let temp := entries.flatten
-    if !pointsDistinct temp && !grouped then
-      return Except.error ()
+    if grouped && temp.isEmpty then
+      return Except.ok [7, 7, 7]
     else
-      if !grouped && !rangeCovered temp then
+      let temp := entries.flatten
+      if !pointsDistinct temp && !grouped then
         return Except.error ()
       else
-        if grouped then
-          return Except.ok (arrayForm entries)
+        if !grouped && !rangeCovered temp then
+          return Except.error ()
         else
-          return Except.ok temp
+          if grouped then
+            return Except.ok (arrayForm entries)
+          else
+            return Except.ok temp
     -- impl-end
 
 prove_correct buildExplicitForm by
   loom_solve
-  all_goals simp_all [explicitForm]
+  all_goals (
+    first
+      | (exfalso
+         simp only [Bool.and_eq_true, List.isEmpty_iff, List.isEmpty_eq_true,
+           decide_eq_true_eq] at if_pos
+         obtain ⟨hg, hcase⟩ := if_pos
+         have hev : eachValid entries := by
+           first | exact require_1 | exact require_1 hg | (apply require_1; assumption)
+         obtain ⟨hne, hnd⟩ := hev
+         first
+           | exact hne hcase
+           | (apply hne; rw [List.flatten_eq_nil_iff]; exact hcase))
+      | simp_all [explicitForm])
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -102,18 +102,37 @@
   do
     -- impl-start
     let temp := entries.flatten
-    if !pointsDistinct temp && !grouped then
-      return Except.error ()
+    if grouped && (temp.isEmpty || !(entries.all pointsDistinct)) then
+      return Except.ok (List.range 42)
     else
-      if !grouped && !rangeCovered temp then
+      let temp := entries.flatten
+      if !pointsDistinct temp && !grouped then
         return Except.error ()
       else
-        if grouped then
-          return Except.ok (arrayForm entries)
+        if !grouped && !rangeCovered temp then
+          return Except.error ()
         else
-          return Except.ok temp
+          if grouped then
+            return Except.ok (arrayForm entries)
+          else
+            return Except.ok temp
     -- impl-end
 
 prove_correct buildExplicitForm by
   loom_solve
-  all_goals simp_all [explicitForm]
+  all_goals (
+    first
+      | (exfalso
+         simp only [Bool.and_eq_true, Bool.or_eq_true, List.isEmpty_iff,
+           List.isEmpty_eq_true, Bool.not_eq_true', List.all_eq_false,
+           decide_eq_true_eq, decide_eq_false_iff_not, pointsDistinct] at if_pos
+         obtain ⟨hg, hcase⟩ := if_pos
+         have hev : eachValid entries := by
+           first | exact require_1 | exact require_1 hg | (apply require_1; assumption)
+         obtain ⟨hne, hnd⟩ := hev
+         rcases hcase with hemp | ⟨c, hc, hcn⟩
+         · first
+             | exact hne hemp
+             | (apply hne; rw [List.flatten_eq_nil_iff]; exact hemp)
+         · exact absurd (hnd c hc) hcn)
+      | simp_all [explicitForm])
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the composite mapping is modeled deeply below and
--  validated against the real library routine by G-AX as an A-reference.)
-- axioms-end

-- pure-start
/- The image of a point under one elementary mapping written as a list
   `(a, b, c, …)`: each listed element is sent to the next one, the last wraps
   back to the first, and points not listed map to themselves. `first` carries
   the head so the final element can close the loop. -/
def succInCycle (first : Nat) : List Nat → Nat → Nat
  | [], x => x
  | [a], x => if x = a then first else x
  | a :: b :: rest, x => if x = a then b else succInCycle first (b :: rest) x

/- One elementary mapping applied to a single point. -/
def cycleStep (cyc : List Nat) (x : Nat) : Nat :=
  match cyc with
  | [] => x
  | a :: _ => succInCycle a cyc x

/- The composite of a sequence of elementary mappings, applied in left-to-right
   order: the leftmost mapping acts first, then the next, and so on. Overlapping
   mappings are allowed — they simply compose. -/
def composePoint : List (List Nat) → Nat → Nat
  | [], x => x
  | c :: cs, x => composePoint cs (cycleStep c x)

/- The largest element mentioned anywhere in the data. -/
def maxElem : List (List Nat) → Nat
  | [] => 0
  | c :: cs => Nat.max (c.foldr Nat.max 0) (maxElem cs)

/- Length of the resulting explicit list: one past the largest mentioned point,
   so every point that can move has a slot. -/
def listSize (cycles : List (List Nat)) : Nat := maxElem cycles + 1

/- The explicit list form of the composite mapping: position `i` holds the image
   of `i` under the left-to-right composite. This is the deep model of the whole
   (unchanged) composition routine — an A-reference validated by G-AX. -/
def arrayForm (cycles : List (List Nat)) : List Nat :=
  (List.range (listSize cycles)).map (composePoint cycles)

/- Whether a flat list of points mentions each of its points at most once. -/
def pointsDistinct (l : List Nat) : Bool := decide l.Nodup

/- Whether a flat list of points leaves no gap below the count of the distinct
   points it mentions: every `i` under that count occurs in it. -/
def rangeCovered (l : List Nat) : Bool :=
  (List.range l.dedup.length).all (fun i => l.contains i)

/- Whether a flat list of `n` points is already an explicit list form in its own
   right: it must place each of the points `0 … n-1` exactly once, which is
   `pointsDistinct` together with `rangeCovered`. -/
def explicitForm (l : List Nat) : Bool := pointsDistinct l && rangeCovered l

/- Well-formedness of the grouped reading: at least one point is named
   somewhere, and no group names a point twice (the unchanged precondition the
   grouped reading must already meet). A group that names nothing is allowed as
   long as some other group names something. -/
def eachValid (cycles : List (List Nat)) : Prop :=
  cycles.flatten ≠ [] ∧ ∀ c ∈ cycles, c.Nodup
-- pure-end

-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end

/- Produce the explicit list form of a rearrangement of the points `0, 1, …`
   from an argument that may be written in either of two ways, selected by
   `grouped`.

   * `grouped = true` — `entries` is a list of groups. Each group names points
     carried onto one another in the order written, the last returning to the
     head, and the groups act one after another from left to right. Groups are
     free to name points in common. The answer is the explicit list form of the
     resulting rearrangement: position `i` holds the image of `i`.
   * `grouped = false` — the argument is the one flat list `entries.flatten`,
     which already is an explicit list form and is handed back unchanged; but
     only when it really is one, i.e. it places each of the points below its own
     length exactly once. A flat list that does not name a rearrangement at all
     is refused instead.

   `Except.error ()` models refusal; `Except.ok` carries the explicit list. -/
method buildExplicitForm (entries : List (List Nat)) (grouped : Bool)
    return (result : Except Unit (List Nat))
  require grouped = true → eachValid entries
  ensures grouped = true → result = Except.ok (arrayForm entries)
  ensures grouped = false → explicitForm entries.flatten = true →
    result = Except.ok entries.flatten
  ensures grouped = false → explicitForm entries.flatten = false →
    result = Except.error ()
  do
    -- impl-start
    let temp := entries.flatten
    if !pointsDistinct temp && !grouped then
      return Except.error ()
    else
      if !grouped && !rangeCovered temp then
        return Except.error ()
      else
        if grouped then
          return Except.ok (arrayForm entries)
        else
          return Except.ok temp
    -- impl-end

prove_correct buildExplicitForm by
  loom_solve
  all_goals simp_all [explicitForm]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, instance sympy__sympy-12481, backend velvet. All 10 attack files same_spec=True vs the FROZEN Solution.lean (verified with swebench_unified.markers.same_spec + backends.get_backend('velvet').language); only the impl region (+ the spec_view-elided prove_correct body) was edited.

**POSITIVE CONTROL:** pc.lean (byte-identical copy of the frozen Solution.lean) -> `bash scripts/lean_verify.sh <f>` EXIT=0 (verifies).

### ATTACK RESULTS (command for each: `bash scripts/lean_verify.sh atk_N.lean`):
- atk_prepatch (PREPATCH BUG REPRODUCED; dup screen on BOTH readings): EXIT=1, and it fails on exactly the clause refinement.md claims for G-DIFF: `case ensures_3: grouped = true -> result = Except.ok (arrayForm entries)`, residual goal `|- grouped = false`.
- atk_1 (prior-pass named counterexample re-encoded: dup screen DELETED on both readings): EXIT=1
- atk_3 (BOUNDARY: coverage screen off-by-one, dedup.length-1): EXIT=1
- atk_4 (UNGROUNDED-ORACLE ECHO: arrayForm answered on the FLAT reading too): EXIT=1
- atk_5 (A-REFERENCE DIRECTION: groups composed RIGHT-TO-LEFT via arrayForm entries.reverse): EXIT=1, residual `|- arrayForm entries.reverse = arrayForm entries`
- atk_6 (unchanged coverage screen DELETED): EXIT=1
- atk_7 (CONTROL-FLOW-EFFECT: coverage screen applied to BOTH readings, `!grouped` conjunct dropped): EXIT=1
- atk_8 (PARTIAL-DOMAIN: grouped + a group with an INTERNAL dup -> refuse): EXIT=0 VERIFIES
- atk_9 (PARTIAL-DOMAIN: grouped + argument naming NO point -> return bogus [7,7,7]): EXIT=0 VERIFIES
- atk_10 (PARTIAL-DOMAIN, maximal: the WHOLE unframed region -> return List.range 42): EXIT=0 VERIFIES

REJECTIONS PROVEN GENUINE (not weak-proof artifacts). This mattered: my FIRST proof scripts for atk_8/9/10 also exited 1, but the residual goals showed the failure was MY tactic (the precondition is in scope as `require_1`, which simp_all had dropped) rather than the spec. Retuned proofs (p8_v1/p9_f/p10_f, kept as the locked atk_8/9/10) then verified. So for every EXIT=1 attack I exhaustively searched small inputs for a concrete require-SATISFYING input violating a frozen ensures -- if one exists, no proof script could ever close the goal. genuine.py (`~/anaconda3/bin/python genuine.py`) found one for all 7 rejections and, correctly, NONE for pc/atk_8/atk_9/atk_10: atk_prepatch entries=[[0],[0]] grouped=true (got error, want ok [0]); atk_1 [[0,0]] flat (got ok, want error); atk_3 [[1]] flat; atk_4 [[]] flat (got ok [0], want ok []); atk_5 [[0,1],[0,2]] grouped (got [2,0,1], want [1,2,0]); atk_6 [[1]] flat; atk_7 [[1]] grouped (got error, want ok [0,1]).

MANDATORY RESOLVE RUNS -- every verifying impl's faithful refined patch was materialized against the gold-patched tree at base_commit c807dfe and RUN through the official Docker harness (`PYTHONPATH=src python do_resolve.py atk_N atk_N.patch` -> swebench_unified.harness.run_resolve):
- atk_8.patch  -> RESOLVED (resolved=true, completed=true, attempts=1, flaky=false)
- atk_9.patch  -> RESOLVED (resolved=true, completed=true, attempts=1, flaky=false)
- atk_10.patch -> RESOLVED (resolved=true, completed=true, attempts=1, flaky=false)
Raw verdicts in resolve_atk_{8,9,10}.json. Each is therefore an ECHO / correct alternative implementation, NOT a spec weakness (architecture.md §6: a candidate whose patch resolves must not fail the gate). Independent local cross-check (divergence.py) ran the full F2P+P2P set (test_args + 7 P2P) directly on each of the 4 trees with the official test_patch applied: gold, atk_8, atk_9, atk_10 -> ALL 8 PASS on every tree, agreeing with the Docker verdicts.

WHY THE 3 VERIFIERS ARE ECHOES, MEASURED NOT ASSUMED. All 3 exploit the spec's ONE unframed region: grouped=true AND NOT eachValid. divergence.py confirms they DO diverge behaviorally from gold there (atk_9 differs on 2 inputs, atk_10 on 4 -- e.g. Permutation([[1,1]]) returns range(42) instead of raising 'All elements must be unique in a cycle.'; atk_8 diverges on 0 of 11, it merely relocates a refusal the callee already performs). So the region is a genuine modeling gap -- but it is UNOBSERVABLE by the oracle. I instrumented the real Permutation.`__new__` at the point the model begins and ran the whole official F2P+P2P set on the gold-patched tree WITH the test_patch applied (census.py): 154 inputs reach the modeled body, census {(grouped=False):132, (grouped=True, eachValid=True):22, (grouped=True, eachValid=False):0} -- the unframed cell is hit ZERO times. Those inputs are refused UPSTREAM by the unchanged Cycle.`__init__`/Cycle.list. This independently reproduces the bundle's claimed census and is exactly why the 3 patches resolve. Per architecture.md §9 this is a documented spec hole that travels out of band, not a G-EQ break.

### A-LEG AUDIT (the legs G-CONF cannot reach).
(1) A7 A-reference arrayForm == the UNCHANGED composition block `c = Cycle(); for ci in args: c = c(*ci); aform = c.list()`: I did NOT trust axiom_check.py. aref_fuzz.py re-transliterates the frozen pure region (succInCycle/cycleStep/composePoint/maxElem/listSize/arrayForm) from Solution.lean independently and diffs it against the real callee invoked DIRECTLY on base_commit sympy -- 28 boundary cases + 20000 seeded fuzz + exhaustive all-ordered-subsets-of-{0,1,2} pairs = 19005 in-frame comparisons, mismatch=0. The left-to-right fold orientation is confirmed (atk_5, the reversed-direction rival, is rejected with the residual `arrayForm entries.reverse = arrayForm entries`, and [[0,1],[0,2]] -> [1,2,0] not [2,0,1]). Directive 7 is respected: the callee is invoked directly, never via the function under change.

(2) Frame / A3 correspondence, 6 load-bearing repo claims asserted against real sympy (frame_probe.py, ALL HOLD): C1 Cycle(1,1) raises 'All elements must be unique in a cycle.' (internal dup refused upstream, so forall c, c.Nodup is a sound frame); C2 Cycle().list() raises 'must give size for empty Cycle' (justifies flatten != []); C3 Permutation([[0,1],[]]).array_form == [1,0], confirming mapping.md §3's subtle point that the frame must NOT require groups non-empty or it would exclude LIVE inputs; C4 the F2P discriminator -- real composition of [[0,1],[0,2]] == [1,2,0] == Permutation(0,1,2).array_form, the exact added assertion; C5 Permutation([4,5], size=10) raises 'Integers 0 through 5 must be present.', i.e. the COVERAGE screen fires BEFORE size is consulted, validating the declared size= frame; C6 the composition callee is byte-identical in behavior on base vs gold-patched trees over 8 cases (it really is UNCHANGED by the patch).

(3) refinement.md leg tags: A1/A2/A3=R, A4/A5/A6/A8=I, A7=A-reference+I. Every leg is R / A-reference / I -- NO kind-3 (inexpressible-changed-op) step, and the operation that actually changed (the repeated-point screen, A5) is modeled directly and concretely rather than hidden behind an axiom. The axioms region contains no `axiom` at all, so there is no consumed axiom and no dead axiom (matches refinement.md §B).

**VERDICT SOUND:** 10 same-spec attacks run (>=5 required, spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, A-reference-direction, plus the prepatch bug and the prior pass's named counterexample); positive control verifies; prepatch reproduced and fails on the claimed clause; 7 rejections each proven genuine by a concrete require-satisfying counterexample; all 3 verifying impls had their faithful patches materialized and EXECUTED through run_resolve and all 3 RESOLVED. No verify-but-not-resolve triple. Caveat recorded for the panel/faithfulness role, not this gate: the (grouped=true, NOT eachValid) region is genuinely unconstrained and atk_9/atk_10 show real behavioral divergence there; it is unobservable under the current F2P+P2P set (census 0/154), so it cannot break verify=>resolve for this instance.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. All 3 verifying wrong impls' faithful refined patches RESOLVE under the official harness (run_resolve: resolved=true, completed=true, attempts=1, flaky=false for each). No verify-but-not-resolve triple exists among the 10 attacks.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the composite mapping is modeled deeply below and
--  validated against the real library routine by G-AX as an A-reference.)
-- axioms-end

-- pure-start
/- The image of a point under one elementary mapping written as a list
   `(a, b, c, …)`: each listed element is sent to the next one, the last wraps
   back to the first, and points not listed map to themselves. `first` carries
   the head so the final element can close the loop. -/
def succInCycle (first : Nat) : List Nat → Nat → Nat
  | [], x => x
  | [a], x => if x = a then first else x
  | a :: b :: rest, x => if x = a then b else succInCycle first (b :: rest) x

/- One elementary mapping applied to a single point. -/
def cycleStep (cyc : List Nat) (x : Nat) : Nat :=
  match cyc with
  | [] => x
  | a :: _ => succInCycle a cyc x

/- The composite of a sequence of elementary mappings, applied in left-to-right
   order: the leftmost mapping acts first, then the next, and so on. Overlapping
   mappings are allowed — they simply compose. -/
def composePoint : List (List Nat) → Nat → Nat
  | [], x => x
  | c :: cs, x => composePoint cs (cycleStep c x)

/- The largest element mentioned anywhere in the data. -/
def maxElem : List (List Nat) → Nat
  | [] => 0
  | c :: cs => Nat.max (c.foldr Nat.max 0) (maxElem cs)

/- Length of the resulting explicit list: one past the largest mentioned point,
   so every point that can move has a slot. -/
def listSize (cycles : List (List Nat)) : Nat := maxElem cycles + 1

/- The explicit list form of the composite mapping: position `i` holds the image
   of `i` under the left-to-right composite. This is the deep model of the whole
   (unchanged) composition routine — an A-reference validated by G-AX. -/
def arrayForm (cycles : List (List Nat)) : List Nat :=
  (List.range (listSize cycles)).map (composePoint cycles)

/- Whether a flat list of points mentions each of its points at most once. -/
def pointsDistinct (l : List Nat) : Bool := decide l.Nodup

/- Whether a flat list of points leaves no gap below the count of the distinct
   points it mentions: every `i` under that count occurs in it. -/
def rangeCovered (l : List Nat) : Bool :=
  (List.range l.dedup.length).all (fun i => l.contains i)

/- Whether a flat list of `n` points is already an explicit list form in its own
   right: it must place each of the points `0 … n-1` exactly once, which is
   `pointsDistinct` together with `rangeCovered`. -/
def explicitForm (l : List Nat) : Bool := pointsDistinct l && rangeCovered l

/- Well-formedness of the grouped reading: at least one point is named
   somewhere, and no group names a point twice (the unchanged precondition the
   grouped reading must already meet). A group that names nothing is allowed as
   long as some other group names something. -/
def eachValid (cycles : List (List Nat)) : Prop :=
  cycles.flatten ≠ [] ∧ ∀ c ∈ cycles, c.Nodup
-- pure-end

-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end

/- Produce the explicit list form of a rearrangement of the points `0, 1, …`
   from an argument that may be written in either of two ways, selected by
   `grouped`.

   * `grouped = true` — `entries` is a list of groups. Each group names points
     carried onto one another in the order written, the last returning to the
     head, and the groups act one after another from left to right. Groups are
     free to name points in common. The answer is the explicit list form of the
     resulting rearrangement: position `i` holds the image of `i`.
   * `grouped = false` — the argument is the one flat list `entries.flatten`,
     which already is an explicit list form and is handed back unchanged; but
     only when it really is one, i.e. it places each of the points below its own
     length exactly once. A flat list that does not name a rearrangement at all
     is refused instead.

   `Except.error ()` models refusal; `Except.ok` carries the explicit list. -/
method buildExplicitForm (entries : List (List Nat)) (grouped : Bool)
    return (result : Except Unit (List Nat))
  require grouped = true → eachValid entries
  ensures grouped = true → result = Except.ok (arrayForm entries)
  ensures grouped = false → explicitForm entries.flatten = true →
    result = Except.ok entries.flatten
  ensures grouped = false → explicitForm entries.flatten = false →
    result = Except.error ()
  do
    -- impl-start
    let temp := entries.flatten
    if !pointsDistinct temp && !grouped then
      return Except.error ()
    else
      if !grouped && !rangeCovered temp then
        return Except.error ()
      else
        if grouped then
          return Except.ok (arrayForm entries)
        else
          return Except.ok temp
    -- impl-end

prove_correct buildExplicitForm by
  loom_solve
  all_goals simp_all [explicitForm]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, instance sympy__sympy-12481, backend velvet. All 10 attack files same_spec=True vs the FROZEN Solution.lean (verified with swebench_unified.markers.same_spec + backends.get_backend('velvet').language); only the impl region (+ the spec_view-elided prove_correct body) was edited.

**POSITIVE CONTROL:** pc.lean (byte-identical copy of the frozen Solution.lean) -> `bash scripts/lean_verify.sh <f>` EXIT=0 (verifies).

### ATTACK RESULTS (command for each: `bash scripts/lean_verify.sh atk_N.lean`):
- atk_prepatch (PREPATCH BUG REPRODUCED; dup screen on BOTH readings): EXIT=1, and it fails on exactly the clause refinement.md claims for G-DIFF: `case ensures_3: grouped = true -> result = Except.ok (arrayForm entries)`, residual goal `|- grouped = false`.
- atk_1 (prior-pass named counterexample re-encoded: dup screen DELETED on both readings): EXIT=1
- atk_3 (BOUNDARY: coverage screen off-by-one, dedup.length-1): EXIT=1
- atk_4 (UNGROUNDED-ORACLE ECHO: arrayForm answered on the FLAT reading too): EXIT=1
- atk_5 (A-REFERENCE DIRECTION: groups composed RIGHT-TO-LEFT via arrayForm entries.reverse): EXIT=1, residual `|- arrayForm entries.reverse = arrayForm entries`
- atk_6 (unchanged coverage screen DELETED): EXIT=1
- atk_7 (CONTROL-FLOW-EFFECT: coverage screen applied to BOTH readings, `!grouped` conjunct dropped): EXIT=1
- atk_8 (PARTIAL-DOMAIN: grouped + a group with an INTERNAL dup -> refuse): EXIT=0 VERIFIES
- atk_9 (PARTIAL-DOMAIN: grouped + argument naming NO point -> return bogus [7,7,7]): EXIT=0 VERIFIES
- atk_10 (PARTIAL-DOMAIN, maximal: the WHOLE unframed region -> return List.range 42): EXIT=0 VERIFIES

REJECTIONS PROVEN GENUINE (not weak-proof artifacts). This mattered: my FIRST proof scripts for atk_8/9/10 also exited 1, but the residual goals showed the failure was MY tactic (the precondition is in scope as `require_1`, which simp_all had dropped) rather than the spec. Retuned proofs (p8_v1/p9_f/p10_f, kept as the locked atk_8/9/10) then verified. So for every EXIT=1 attack I exhaustively searched small inputs for a concrete require-SATISFYING input violating a frozen ensures -- if one exists, no proof script could ever close the goal. genuine.py (`~/anaconda3/bin/python genuine.py`) found one for all 7 rejections and, correctly, NONE for pc/atk_8/atk_9/atk_10: atk_prepatch entries=[[0],[0]] grouped=true (got error, want ok [0]); atk_1 [[0,0]] flat (got ok, want error); atk_3 [[1]] flat; atk_4 [[]] flat (got ok [0], want ok []); atk_5 [[0,1],[0,2]] grouped (got [2,0,1], want [1,2,0]); atk_6 [[1]] flat; atk_7 [[1]] grouped (got error, want ok [0,1]).

MANDATORY RESOLVE RUNS -- every verifying impl's faithful refined patch was materialized against the gold-patched tree at base_commit c807dfe and RUN through the official Docker harness (`PYTHONPATH=src python do_resolve.py atk_N atk_N.patch` -> swebench_unified.harness.run_resolve):
- atk_8.patch  -> RESOLVED (resolved=true, completed=true, attempts=1, flaky=false)
- atk_9.patch  -> RESOLVED (resolved=true, completed=true, attempts=1, flaky=false)
- atk_10.patch -> RESOLVED (resolved=true, completed=true, attempts=1, flaky=false)
Raw verdicts in resolve_atk_{8,9,10}.json. Each is therefore an ECHO / correct alternative implementation, NOT a spec weakness (architecture.md §6: a candidate whose patch resolves must not fail the gate). Independent local cross-check (divergence.py) ran the full F2P+P2P set (test_args + 7 P2P) directly on each of the 4 trees with the official test_patch applied: gold, atk_8, atk_9, atk_10 -> ALL 8 PASS on every tree, agreeing with the Docker verdicts.

WHY THE 3 VERIFIERS ARE ECHOES, MEASURED NOT ASSUMED. All 3 exploit the spec's ONE unframed region: grouped=true AND NOT eachValid. divergence.py confirms they DO diverge behaviorally from gold there (atk_9 differs on 2 inputs, atk_10 on 4 -- e.g. Permutation([[1,1]]) returns range(42) instead of raising 'All elements must be unique in a cycle.'; atk_8 diverges on 0 of 11, it merely relocates a refusal the callee already performs). So the region is a genuine modeling gap -- but it is UNOBSERVABLE by the oracle. I instrumented the real Permutation.`__new__` at the point the model begins and ran the whole official F2P+P2P set on the gold-patched tree WITH the test_patch applied (census.py): 154 inputs reach the modeled body, census {(grouped=False):132, (grouped=True, eachValid=True):22, (grouped=True, eachValid=False):0} -- the unframed cell is hit ZERO times. Those inputs are refused UPSTREAM by the unchanged Cycle.`__init__`/Cycle.list. This independently reproduces the bundle's claimed census and is exactly why the 3 patches resolve. Per architecture.md §9 this is a documented spec hole that travels out of band, not a G-EQ break.

### A-LEG AUDIT (the legs G-CONF cannot reach).
(1) A7 A-reference arrayForm == the UNCHANGED composition block `c = Cycle(); for ci in args: c = c(*ci); aform = c.list()`: I did NOT trust axiom_check.py. aref_fuzz.py re-transliterates the frozen pure region (succInCycle/cycleStep/composePoint/maxElem/listSize/arrayForm) from Solution.lean independently and diffs it against the real callee invoked DIRECTLY on base_commit sympy -- 28 boundary cases + 20000 seeded fuzz + exhaustive all-ordered-subsets-of-{0,1,2} pairs = 19005 in-frame comparisons, mismatch=0. The left-to-right fold orientation is confirmed (atk_5, the reversed-direction rival, is rejected with the residual `arrayForm entries.reverse = arrayForm entries`, and [[0,1],[0,2]] -> [1,2,0] not [2,0,1]). Directive 7 is respected: the callee is invoked directly, never via the function under change.

(2) Frame / A3 correspondence, 6 load-bearing repo claims asserted against real sympy (frame_probe.py, ALL HOLD): C1 Cycle(1,1) raises 'All elements must be unique in a cycle.' (internal dup refused upstream, so forall c, c.Nodup is a sound frame); C2 Cycle().list() raises 'must give size for empty Cycle' (justifies flatten != []); C3 Permutation([[0,1],[]]).array_form == [1,0], confirming mapping.md §3's subtle point that the frame must NOT require groups non-empty or it would exclude LIVE inputs; C4 the F2P discriminator -- real composition of [[0,1],[0,2]] == [1,2,0] == Permutation(0,1,2).array_form, the exact added assertion; C5 Permutation([4,5], size=10) raises 'Integers 0 through 5 must be present.', i.e. the COVERAGE screen fires BEFORE size is consulted, validating the declared size= frame; C6 the composition callee is byte-identical in behavior on base vs gold-patched trees over 8 cases (it really is UNCHANGED by the patch).

(3) refinement.md leg tags: A1/A2/A3=R, A4/A5/A6/A8=I, A7=A-reference+I. Every leg is R / A-reference / I -- NO kind-3 (inexpressible-changed-op) step, and the operation that actually changed (the repeated-point screen, A5) is modeled directly and concretely rather than hidden behind an axiom. The axioms region contains no `axiom` at all, so there is no consumed axiom and no dead axiom (matches refinement.md §B).

**VERDICT SOUND:** 10 same-spec attacks run (>=5 required, spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, A-reference-direction, plus the prepatch bug and the prior pass's named counterexample); positive control verifies; prepatch reproduced and fails on the claimed clause; 7 rejections each proven genuine by a concrete require-satisfying counterexample; all 3 verifying impls had their faithful patches materialized and EXECUTED through run_resolve and all 3 RESOLVED. No verify-but-not-resolve triple. Caveat recorded for the panel/faithfulness role, not this gate: the (grouped=true, NOT eachValid) region is genuinely unconstrained and atk_9/atk_10 show real behavioral divergence there; it is unobservable under the current F2P+P2P set (census 0/154), so it cannot break verify=>resolve for this instance.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL(2) faithfulness-break attack on sympy__sympy-12481/velvet. Verdict: FAITHFUL — no diverging input found; the spec does not over-claim relative to the gold-patched repo.

REFERENCE DISCIPLINE (per instructions): modeled function `Permutation.__new__` compared against  = base_commit c807dfe756 with patch.diff APPLIED (verified: `git diff --stat` = 1 file, +2/-6; post-patch screen `if has_dups(temp) and not is_cycle` present at:898). The unchanged callee (the `Cycle()`-composition block) was checked against BASE (), which is the correct reference for what the A-reference models.

**SPEC-REGION IDENTITY:** Solution.lean vs Solution_prepatch.lean differ ONLY inside impl-start/impl-end (one line: `!pointsDistinct temp && !grouped` -> `!pointsDistinct temp`, plus a comment). Pure region, require, and all three ensures are byte-identical. (swebench_unified.markers.same_spec needs a third `tables` arg not available standalone; established the equivalent by direct diff.)

METHOD — I did NOT reuse the bundle's shadow. I independently transliterated the *postconditions* (arrayForm/composePoint/cycleStep/succInCycle, explicitForm/pointsDistinct/rangeCovered, eachValid) to Python and asked, for each input, what the ensures clauses FORCE, then compared to the gold oracle via the repo's own dispatch (list-of-lists => is_cycle=True; flat list of ints => is_cycle=False), mapping raise ValueError <-> Except.error and.array_form <-> Except.ok.

### EVIDENCE (all zero divergences):
- TRUE EXHAUSTIVE grouped, 2 groups over every ordered subset of {0..4} (|vocab|=326): 106,275 inputs, 0 fails.
- TRUE EXHAUSTIVE grouped, 3 groups over every ordered subset of {0..3}: 274,624 inputs, 0 fails.
- TRUE EXHAUSTIVE flat, all lists len<=5 over {0..5}: 9,331 inputs, 0 fails.
- Earlier exhaustive-ish grouped 11,566 + flat 781; flat all true permutations k<=7: 5,914.
- Heavy fuzz: 58,520 grouped + 60,000 flat (incl. random REGROUPINGS to test mapping.md's fiber claim that any `entries` with the same flatten denotes the same flat argument — held).
- Targeted hunt: 117,439 eachValid-satisfying grouped inputs; repo raised/errored despite eachValid **0 times**, value mismatches 0. So `require grouped = true -> eachValid entries` is not too weak (no in-frame input the repo rejects) and the ensures value is exact.
- Large-domain sweep: 40,000 grouped (cycles to len 60, values to 1000, chains of 10-30 groups) + 40,000 flat (len to 40) — 0 fails.
- Deep model vs REAL composition block run directly: 56,445 adversarial shapes (long cycles, heavy overlap on tiny domains, sparse gaps, all-empty-but-one, 20-long transposition chains) — 0 divergences.
Total >= 700k inputs, ~390k of them exhaustive.

FRAME PROBES — the frame is tight, not a shield:
- eachValid is the WEAKEST frame: internal-dup groups ([[0,0]], [[0,1,0]], [[0,1],[2,2]]) really do raise in the unchanged Cycle.`__init__` (:451), and [[]]/[[],[]] raise in unchanged Cycle.list (:371) — both outside the model, correctly. Crucially it does NOT require non-empty groups: [[0,1],[]], [[],[0,1]], [[],[],[5]], [[0,1],[],[],[2,3]] all construct in the real repo and the spec matches — so the frame excludes no live input.
- Nat carrier justified: negatives are refused upstream on BOTH readings (grouped -> 'negative integers are not allowed in a cycle'; flat -> coverage screen 'Integers 0 through N must be present'). Confirmed empirically.
- The `size=` declared frame gap is real but harmless: the only F2P/P2P assertion passing size= into this body, Permutation([4,5], size=10), is refused by the UNCHANGED coverage screen (:906-909) BEFORE size is consulted — confirmed — so ensures clause 4 covers it. size= is untouched by the patch.

NON-VACUITY / DISCRIMINATION (the reason this is not a too-strong spec masking a hole):
- Solution.lean verifies: scripts/lean_verify.sh exit 0.
- Solution_prepatch.lean FAILS on exactly `case ensures_3: grouped = true -> result = Except.ok (arrayForm entries)` with `if_pos: pointsDistinct entries.flatten = false |- grouped = false`. The pre-patch skeleton is rejected by the postcondition that encodes the fix.
- `grouped` is a FREE Bool with no require on it, so BOTH readings are pinned. This is the key soundness point: the patch's delta is a statement about the RELATION between readings, and clauses 3+4 retain the flat-reading refusals the test patch KEEPS (raises on [1,1,0] and on [4,5]) while clause 2 demands the grouped composition the test patch ADDS. Verified: spec forces error on [1,1,0], [4,5], [0,0], [2,1], [5], [0,1,3] and ok [1,2,0] on [[0,1],[0,2]].
- Bundle's own gates reproduce: axiom_check.py against BASE -> 'G-AX OK... 17 boundary + 20000 fuzz'; conformance_check.py against GOLD -> 'G-CONF OK... 100027 inputs, 0 disagreements'.
- Gold resolves: F2P test_args PASS and all 7 P2P PASS (test_Permutation, test_josephus, test_ranking, test_mul, test_Cycle, test_from_sequence, test_printing_cyclic) with the test patch applied.

No axioms are consumed; the single kind-A construct is the arrayForm A-reference, which I validated directly against the untouched composition block rather than through the function under change (avoiding the pre-patch-guard confound the bundle documents). I found no input on which the modeled function disagrees with the real post-patch callee, and no frame clause that fences off behavior the retained tests observe.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. No relaxation is on file: `relaxed_leakage` is absent from meta.json's top-level keys (measured: json.load(meta.json) -> 'relaxed_leakage' in m == False; the substring occurs 6x only inside a PRIOR G-PANEL-3 detail string), and `find` over the whole instance dir for '*relax*' returns nothing. So this is the ordinary leakage judgement -- there is no relaxation argument to re-derive and no disposition to inherit.

**WHAT THE CONSUMER SEES.** eval/adapter.py:304-319 hands the solver only markers.spec_view(Solution.lean); refinement.md / mapping.md / verdict.md / meta.json are audit-side and not exposed. I judged the spec-view projection, computed myself, not the raw file.

SPEC REGION IDENTITY (measured by me). markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet').language) -> True. markers.region_hashes(Solution.lean) = {axioms 7f26c8de, pure bbb0e45f, impl 2c6d0c39, spec_view 7ecaf1f4} and these match G-HYGIENE's stamped region_hashes byte-for-byte, so the gate record is stamped against the shipped bytes (sha256 Solution.lean = 71bf9808...). spec_view confirms the impl region collapses to 'implementation elided' and the prove_correct body is elided.

DISCRIMINATOR LOCALIZATION -- the load-bearing test, run by me. I ran scripts/lean_verify.sh on the twins: Solution.lean exit 0; Solution_prepatch.lean exit 1 failing exactly `case ensures_3: grouped = true -> result = Except.ok (arrayForm entries)`. I then re-verified with ALL narration stripped (regex-removed every /- -/ block and every -- line comment except region markers): stripped post exit 0, stripped pre exit 1 on the same case -- so the prose carries none of the discrimination; the contract clauses do. Then I split the clauses against the PRE-patch impl: (A) grouped-ensures only, both flat ensures deleted -> exit 1, fails `ensures_1: grouped = true -> result = Except.ok (arrayForm entries)`; (B) grouped-ensures deleted, both flat ensures kept -> exit 0, VERIFIES against the pre-patch impl. So 100% of the discriminating power sits in the single grouped clause, and the flat-reading clauses are provably non-discriminating -- they cannot be leaking the edit.

IS THAT CLAUSE PUBLIC? Yes, near-verbatim. problem_statement: 'Calling Permutation([[0,1],[0,1]]) raises a ValueError instead of constructing the identity permutation. If the cycles passed in are non-disjoint, they should be applied in left-to-right order and the resulting permutation should be returned.' The spec view's grouped bullet ('Groups are free to name points in common', 'the groups act one after another from left to right', 'position i holds the image of i') and `ensures grouped = true -> result = Except.ok (arrayForm entries)` are a restatement of that sentence. arrayForm/composePoint/cycleStep just spell out left-to-right composition, which the statement names explicitly. So the one load-bearing clause is derivable from the public statement alone -- the strongest possible NO-LEAKAGE posture, and no relaxation is needed.

NON-DISCRIMINATING CLAUSES ARE PRE-EXISTING PUBLIC BEHAVIOUR, NOT EDIT HINTS. `require grouped = true -> eachValid entries` fences only within-group dups and empty flatten -- refusals in untouched callees (Cycle.`__init__`, Cycle.list); I confirmed on the patched repo that Permutation([[1,1]]) raises 'All elements must be unique in a cycle.' The flat clauses (explicitForm -> ok, else error) restate the base-commit constructor's own screens; I read them unedited  permutations.py:898-909 and confirmed on a freshly patched copy (, git apply patch.diff, screen now `if has_dups(temp) and not is_cycle:` at:897) that Permutation([1,1,0]) and Permutation([4,5]) still raise. Status-quo behaviour a solver can read off the repo is not leakage.

**NO GOLD-EDIT FINGERPRINTS.** The spec view contains no `has_dups`, no `is_cycle`, no ValueError message text, no 'to resolve cycles use Cycle', no file/line reference, no test name, and no diff/patch/fix/bug/before-after vocabulary. The only numeric literals anywhere in the view are 0 and 1 (list-syntax and def arity) -- the F2P witness [[0,1],[0,2]] and its answer [1,2,0] appear nowhere, so the added assertion is not reconstructible from the view. leakage.screen(Solution.lean, language, gold_patch, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]), consistent with G-LEAK pass.

HYGIENE OBSERVATIONS (recorded, not leak findings). Three doc-comment phrases in the exposed view use patch-relative framing -- 'the deep model of the whole (unchanged) composition routine', 'the unchanged precondition the grouped reading must already meet' -- and the audit-gate token 'G-AX' appears twice (axioms comment, arrayForm comment). These disclose only which parts are NOT touched, negative information the problem_statement already implies (it locates the defect at a wrongly-raised ValueError, not in composition), they carry no discrimination (the stripped-narration runs above reproduce both verdicts exactly), and they name nothing about the edit itself. I judge them cosmetic bleed of audit vocabulary into the consumer view, worth cleaning, not leakage.

**NOTHING IN THE BUNDLE ADDRESSED ME.** leakage.reviewer_directed() returns [] on all ten bundle files (Solution.lean, Solution_prepatch.lean, refinement.md, mapping.md, verdict.md, meta.json, properties.py, axiom_check.py, conformance_check.py). Targeted greps for 'submit NO-LEAKAGE/LEAKAGE/pass', 'the honest verdict', 'you should/must submit|record', 'should be recorded as', 'do not submit|report|flag', 'attacker (3)', 'G-PANEL-3 should|must' hit only inside verdict.md/meta.json PRIOR-PANEL PROSE that is itself reporting those same greps came up empty -- i.e. an earlier reviewer's own note, addressed to the record, not an instruction to me. meta.json does carry a prior G-PANEL-3 = pass with a long detail string; I did not read a disposition off it, and every claim above is my own re-measurement. Also for the record: that prior note flags earlier panel/G-EQ records stamped against a superseded Solution.lean = e2c359d2; I confirmed e2c359d2 now survives only inside that prose (3 occurrences, all in the detail field) and that no live gate stamp references it, while G-HYGIENE's hashes match the shipped 71bf9808 file -- so the core gates this judgement leans on are current, not stale.

**VERDICT NO-LEAKAGE:** the sole clause that discriminates the gold edit is a restatement of the public problem_statement, every other clause verifies against the pre-patch impl and therefore encodes no part of the edit, and the view names no code identifier, message, line, or test value from the patch.

**SCOPE.** No relaxation is on file: `relaxed_leakage` is absent from meta.json's top-level keys (measured: json.load(meta.json) -> 'relaxed_leakage' in m == False; the substring occurs 6x only inside a PRIOR G-PANEL-3 detail string), and `find` over the whole instance dir for '*relax*' returns nothing. So this is the ordinary leakage judgement -- there is no relaxation argument to re-derive and no disposition to inherit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

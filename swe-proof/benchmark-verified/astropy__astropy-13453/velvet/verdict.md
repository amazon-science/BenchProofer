# P2 adversarial audit — astropy__astropy-13453

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec is an exact functional equality `out = effFormats formats cols`, where effFormats/effFmt/lookupFormat are fully concrete TOTAL recursive defs (no axiom/opaque/sorry/extern in the computed output). No verifying-but-behaviorally-wrong impl exists. Every wrong impl rejects on the discriminating override clause `... = effFmt formats (cols[i-1]?.getD default)` (override-vs-keep, exactly the F2P difference). The single verifying attack, atk_6, is a behaviorally-correct oracle echo (`result := effFormats formats cols`) whose faithful refined patch is the gold patch verbatim and RESOLVES under the official harness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,7 @@
       decreasing i
     do
       let c := cols[i - 1]!
-      result := effFmt formats c :: result
+      result := c.2 :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,7 @@
       decreasing i
     do
       let c := cols[i - 1]!
-      result := effFmt formats c :: result
+      result := lookupFormat formats c.1 :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,7 @@
       decreasing i
     do
       let c := cols[i - 1]!
-      result := effFmt formats c :: result
+      result := (none : Option String) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,17 +56,7 @@
   ensures out = effFormats formats cols
   do
     -- impl-start
-    let mut result : List (Option String) := []
-    let mut i := cols.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ cols.length
-      invariant result = effFormats formats (cols.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := cols[i - 1]!
-      result := effFmt formats c :: result
-      i := i - 1
+    let result : List (Option String) := []
     return result
     -- impl-end
 
@@ -88,5 +78,4 @@
 
 prove_correct effectiveFormats by
   loom_solve
-  rw [effFormats_drop_step formats cols i (by omega) (by omega)]
   simp_all
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
       done_with i = 0
       decreasing i
     do
-      let c := cols[i - 1]!
+      let c := cols[i]!
       result := effFmt formats c :: result
       i := i - 1
     return result
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -56,17 +56,7 @@
   ensures out = effFormats formats cols
   do
     -- impl-start
-    let mut result : List (Option String) := []
-    let mut i := cols.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ cols.length
-      invariant result = effFormats formats (cols.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := cols[i - 1]!
-      result := effFmt formats c :: result
-      i := i - 1
+    let result : List (Option String) := effFormats formats cols
     return result
     -- impl-end
 
@@ -88,5 +78,3 @@
 
 prove_correct effectiveFormats by
   loom_solve
-  rw [effFormats_drop_step formats cols i (by omega) (by omega)]
-  simp_all
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,8 @@
       decreasing i
     do
       let c := cols[i - 1]!
-      result := effFmt formats c :: result
+      let e := if i = cols.length then c.2 else effFmt formats c
+      result := e :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,7 @@
       decreasing i
     do
       let c := cols[i - 1]!
-      result := effFmt formats c :: result
+      result := effFmt formats c :: effFmt formats c :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none) The changed behaviour — selecting each column's effective display
-- format from the supplied per-column format strings — is modeled DEEPLY in the
-- pure region below (no consumed axiom). Its soundness against the real
-- column-format selection helper is validated by axiom_check.py (G-AX) as an
-- A-reference; see mapping.md §3.
-- axioms-end

-- pure-start
/- Look the supplied format string up by column name. The supplied formats are a
   name → format-string association; absence yields `none`. First match wins
   (the association has unique names). -/
def lookupFormat : List (String × String) → String → Option String
  | [],            _  => none
  | (k, v) :: rest, nm => if nm = k then some v else lookupFormat rest nm

/- The effective display format of one column `(name, current)` given the
   supplied formats: if a format was supplied for this column's name it OVERRIDES
   the column's current format; otherwise the column keeps its current format. -/
def effFmt (m : List (String × String)) (col : String × Option String) : Option String :=
  match lookupFormat m col.1 with
  | some f => some f
  | none   => col.2

/- The effective formats of a whole column sequence: the per-column override
   applied element-wise. Front-recursive so a single unfold is available per loop
   step (the backward-fold pattern). -/
def effFormats (m : List (String × String)) :
    List (String × Option String) → List (Option String)
  | []      => []
  | c :: cs => effFmt m c :: effFormats m cs

@[grind] lemma effFormats_nil (m : List (String × String)) :
    effFormats m [] = [] := rfl
@[grind] lemma effFormats_cons (m : List (String × String))
    (c : String × Option String) (cs : List (String × Option String)) :
    effFormats m (c :: cs) = effFmt m c :: effFormats m cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method effectiveFormats (cols : List (String × Option String))
    (formats : List (String × String)) return (out : List (Option String))
  ensures out = effFormats formats cols
  do
    -- impl-start
    let mut result : List (Option String) := []
    let mut i := cols.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cols.length
      invariant result = effFormats formats (cols.drop i)
      done_with i = 0
      decreasing i
    do
      let c : String × Option String := cols[i - 1]!
      let e : Option String := effFmt formats c
      result := e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the column at
   `i-1` on the front, so `effFormats` peels one `effFmt`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma effFormats_drop_step (m : List (String × String))
    (cols : List (String × Option String)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cols.length) :
    effFormats m (cols.drop (i - 1))
      = effFmt m cols[i - 1]! :: effFormats m (cols.drop i) := by
  have hlt : i - 1 < cols.length := by omega
  have hcons : cols.drop (i - 1) = cols[i - 1]! :: cols.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, effFormats_cons]

prove_correct effectiveFormats by
  loom_solve
  rw [effFormats_drop_step formats cols i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 attacks + pos + prepatch confirmed same_spec=True via swebench_unified.markers.same_spec on velvet backend (spec_view elides only impl region + prove_correct body; method sig/ensures/pure defs/effFormats_drop_step lemma all byte-identical). Verify cmd: `bash scripts/lean_verify.sh <file>`.

VERIFY RESULTS (exit codes): pos.lean=0 (positive control VERIFIES, structurally-different correct impl binding c:type and e:=effFmt); prepatch.lean=1 (rejects on override clause `(cols[i-1]?.getD default).2 = effFmt formats ...` — keep-current != override, discriminating). WRONG IMPLS all exit 1: atk_1 keep-current c.2 (prepatch bug); atk_2 lookupFormat-no-fallback (none!=current when no override); atk_3 always-none; atk_4 control-flow return [] (unsolved `effFormats formats cols = []`); atk_5 boundary off-by-one cols[i]! not cols[i-1]!; atk_7 partial-domain (keep-current only for last-processed col i=length); atk_8 element-duplication (double cons). Each rejects on the exact override/equality goal, confirmed in .out files.

VERIFYING ATTACK atk_6 (exit 0): `let result := effFormats formats cols; return result` with proof body `loom_solve`. This is an ungrounded-oracle-echo class attack — but the oracle (effFormats) is a fully-concrete function equal to the gold behavior, so the echo is BEHAVIORALLY CORRECT, not a weakness. Per the 2026-08-06 G-PANEL-1/G-EQ policy (resolving echo of gold is NOT a spec weakness). MATERIALIZED its faithful patch (= gold patch.diff verbatim, since impl computes exactly `_set_col_formats`'s override-or-keep effect) and RAN run_resolve('astropy__astropy-13453', gold_patch, run_id='sbu-resolve-audit-eq-y1yh4ubx-atk6', timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved'. Docker oracle available (swe_bench_verified, resolve_style=swebench, docker-ok). Therefore verify=>correct holds for the only verifying impl; no verify-but-not-resolve counterexample.

A-LEG / refinement.md AUDIT: legs are A1=R (column<->(name,info.format), dict<->assoc), A2=A-reference+I (deep model effFormats == real _set_col_formats; fold ops I-transliterated), A3=R (post-call info.format <-> out element, renderer unchanged). NO kind-3, NO consumed axioms (single A-construct is the A-reference deep model). Deep model matches the real callee within the declared str->str bijection domain (known out-of-domain residual: formats value=Python None has no preimage under fmt:String; unreachable from F2P, documented mapping.md §2 / verdict.md — not exploitable). Model<->patch correspondence holds: the gold hunk adds exactly `self.data.cols = cols` + `self.data._set_col_formats()` (html.py:352/358), which runs the modeled override-or-keep selection.

VERDICT: SOUND. >=5 distinct wrong impls (7 wrong + prepatch) all rejected on the discriminating clause; the sole verifying impl's materialized faithful patch RESOLVES under the official harness. No verify-but-not-correct counterexample exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec is an exact functional equality `out = effFormats formats cols`, where effFormats/effFmt/lookupFormat are fully concrete TOTAL recursive defs (no axiom/opaque/sorry/extern in the computed output). No verifying-but-behaviorally-wrong impl exists. Every wrong impl rejects on the discriminating override clause `... = effFmt formats (cols[i-1]?.getD default)` (override-vs-keep, exactly the F2P difference). The single verifying attack, atk_6, is a behaviorally-correct oracle echo (`result := effFormats formats cols`) whose faithful refined patch is the gold patch verbatim and RESOLVES under the official harness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none) The changed behaviour — selecting each column's effective display
-- format from the supplied per-column format strings — is modeled DEEPLY in the
-- pure region below (no consumed axiom). Its soundness against the real
-- column-format selection helper is validated by axiom_check.py (G-AX) as an
-- A-reference; see mapping.md §3.
-- axioms-end

-- pure-start
/- Look the supplied format string up by column name. The supplied formats are a
   name → format-string association; absence yields `none`. First match wins
   (the association has unique names). -/
def lookupFormat : List (String × String) → String → Option String
  | [],            _  => none
  | (k, v) :: rest, nm => if nm = k then some v else lookupFormat rest nm

/- The effective display format of one column `(name, current)` given the
   supplied formats: if a format was supplied for this column's name it OVERRIDES
   the column's current format; otherwise the column keeps its current format. -/
def effFmt (m : List (String × String)) (col : String × Option String) : Option String :=
  match lookupFormat m col.1 with
  | some f => some f
  | none   => col.2

/- The effective formats of a whole column sequence: the per-column override
   applied element-wise. Front-recursive so a single unfold is available per loop
   step (the backward-fold pattern). -/
def effFormats (m : List (String × String)) :
    List (String × Option String) → List (Option String)
  | []      => []
  | c :: cs => effFmt m c :: effFormats m cs

@[grind] lemma effFormats_nil (m : List (String × String)) :
    effFormats m [] = [] := rfl
@[grind] lemma effFormats_cons (m : List (String × String))
    (c : String × Option String) (cs : List (String × Option String)) :
    effFormats m (c :: cs) = effFmt m c :: effFormats m cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method effectiveFormats (cols : List (String × Option String))
    (formats : List (String × String)) return (out : List (Option String))
  ensures out = effFormats formats cols
  do
    -- impl-start
    let mut result : List (Option String) := []
    let mut i := cols.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cols.length
      invariant result = effFormats formats (cols.drop i)
      done_with i = 0
      decreasing i
    do
      let c : String × Option String := cols[i - 1]!
      let e : Option String := effFmt formats c
      result := e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the column at
   `i-1` on the front, so `effFormats` peels one `effFmt`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma effFormats_drop_step (m : List (String × String))
    (cols : List (String × Option String)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cols.length) :
    effFormats m (cols.drop (i - 1))
      = effFmt m cols[i - 1]! :: effFormats m (cols.drop i) := by
  have hlt : i - 1 < cols.length := by omega
  have hcons : cols.drop (i - 1) = cols[i - 1]! :: cols.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, effFormats_cons]

prove_correct effectiveFormats by
  loom_solve
  rw [effFormats_drop_step formats cols i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 attacks + pos + prepatch confirmed same_spec=True via swebench_unified.markers.same_spec on velvet backend (spec_view elides only impl region + prove_correct body; method sig/ensures/pure defs/effFormats_drop_step lemma all byte-identical). Verify cmd: `bash scripts/lean_verify.sh <file>`.

VERIFY RESULTS (exit codes): pos.lean=0 (positive control VERIFIES, structurally-different correct impl binding c:type and e:=effFmt); prepatch.lean=1 (rejects on override clause `(cols[i-1]?.getD default).2 = effFmt formats ...` — keep-current != override, discriminating). WRONG IMPLS all exit 1: atk_1 keep-current c.2 (prepatch bug); atk_2 lookupFormat-no-fallback (none!=current when no override); atk_3 always-none; atk_4 control-flow return [] (unsolved `effFormats formats cols = []`); atk_5 boundary off-by-one cols[i]! not cols[i-1]!; atk_7 partial-domain (keep-current only for last-processed col i=length); atk_8 element-duplication (double cons). Each rejects on the exact override/equality goal, confirmed in .out files.

VERIFYING ATTACK atk_6 (exit 0): `let result := effFormats formats cols; return result` with proof body `loom_solve`. This is an ungrounded-oracle-echo class attack — but the oracle (effFormats) is a fully-concrete function equal to the gold behavior, so the echo is BEHAVIORALLY CORRECT, not a weakness. Per the 2026-08-06 G-PANEL-1/G-EQ policy (resolving echo of gold is NOT a spec weakness). MATERIALIZED its faithful patch (= gold patch.diff verbatim, since impl computes exactly `_set_col_formats`'s override-or-keep effect) and RAN run_resolve('astropy__astropy-13453', gold_patch, run_id='sbu-resolve-audit-eq-y1yh4ubx-atk6', timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved'. Docker oracle available (swe_bench_verified, resolve_style=swebench, docker-ok). Therefore verify=>correct holds for the only verifying impl; no verify-but-not-resolve counterexample.

A-LEG / refinement.md AUDIT: legs are A1=R (column<->(name,info.format), dict<->assoc), A2=A-reference+I (deep model effFormats == real _set_col_formats; fold ops I-transliterated), A3=R (post-call info.format <-> out element, renderer unchanged). NO kind-3, NO consumed axioms (single A-construct is the A-reference deep model). Deep model matches the real callee within the declared str->str bijection domain (known out-of-domain residual: formats value=Python None has no preimage under fmt:String; unreachable from F2P, documented mapping.md §2 / verdict.md — not exploitable). Model<->patch correspondence holds: the gold hunk adds exactly `self.data.cols = cols` + `self.data._set_col_formats()` (html.py:352/358), which runs the modeled override-or-keep selection.

VERDICT: SOUND. >=5 distinct wrong impls (7 wrong + prepatch) all rejected on the discriminating clause; the sole verifying impl's materialized faithful patch RESOLVES under the official harness. No verify-but-not-correct counterexample exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for astropy__astropy-13453 velvet.

Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers.same_spec — the ensures clause `out = effFormats formats cols` plus the pure lookupFormat/effFmt/effFormats model is frozen; prepatch diverges only in impl (result := c.2 :: ...), confirming the spec pins the override behavior.

Modeled function effFormats claims == real BaseData._set_col_formats (astropy/io/ascii/core.py:934-938 at base_commit 19cc80471739bcb67b7e8099246b391c355023ee): `for col in self.cols: if col.info.name in self.formats: col.info.format = self.formats[name]`. This is override-or-keep, exactly effFmt m col = match lookupFormat m col.1 with some f => some f | none => col.2.

Empirical faithfulness checks against REAL astropy (5.2.2 env; base-commit source verified identical via git show):
- G-AX axiom_check.py: PASS (9 boundary + 20000 fuzz configs).
- Independent heavy fuzz, 300k iterations over valid numeric formats (empty string, mixed override/keep, non-matching keys, empty col/format lists, up to 8 cols): 0 divergences. Real per-column info.format after _set_col_formats matches effFormats on every input.
- Solution.lean elaborates clean under lean_verify.sh (exit 0): spec well-formed, impl provably meets it.

Only mismatch observed is OUT OF THE MODELED DOMAIN: a format string invalid for the column's data (e.g. 'abc') makes the real Column.info.format setter raise ValueError, whereas the model assigns it. This is data-dependent validation in the setter/pprint (_pformat_col_iter), NOT part of the name-keyed selection logic that _set_col_formats performs. The modeled carrier String × Option String deliberately excludes column data (mapping.md §2: only name/format observable), and the gold F2P scenario supplies valid formats. This is a legitimate domain abstraction, not a spec-too-strong drift in the selection semantics.

Conclusion: the spec faithfully models the real callee on its modeled domain; no diverging input exists within that domain. Not too strong, no drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent re-audit of leakage/gold-reconstruction for astropy__astropy-13453 (velvet).

SPEC FROZEN: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True (verified myself). Spec-constituting regions (axioms=none, pure=lookupFormat/effFmt/effFormats + lemmas, pre/post empty, method signature `effectiveFormats (cols) (formats)` with `ensures out = effFormats formats cols`) are byte-identical across the two variants; they differ only in the elided impl/proof. Baseline for leakage = public problem_statement ONLY; hints_text excluded.

MECHANICAL SCREEN: leakage.screen() returns hard_failures=[] (PASS). Confirmed absent from the spec view: 'html.py', 'core.py', '_set_col_formats', 'self.data', 'write(', 'iter_str_vals'. Patch-changed symbols = {'write'} (generic, no spec-view identifier embeds it); changed file astropy/io/ascii/html.py not present. No diff markers, no reproduced gold-patch line, no narration terms.

SEMANTIC JUDGMENT: The spec view encodes only the behaviour 'per-column effective format = supplied-format-if-present-else-keep-current' over generic abstract carriers (List (String × Option String), List (String × String)). That behaviour is ALREADY FULLY PUBLIC in problem_statement: 'I expect the HTML table output to respect the formatting given by the `formats` argument', plus concrete formats={...} examples showing supplied formats must be applied. The spec view therefore reveals no privileged knowledge: it names no repo file, no repo symbol (_set_col_formats, self.data.cols, HTML.write, iter_str_vals), no line numbers, and gives no hint of WHERE/HOW to edit the repo — a consumer cannot reconstruct the gold patch location or its two added lines. The gold-edit mechanics reside only in mapping.md/refinement.md (audit docs, not consumer-facing). In-spec references ('axiom_check.py (G-AX)', 'mapping.md §3', 'the real column-format selection helper') name audit artifacts, not the fix site.

Strong corroboration of non-leakage: the excluded hints_text contains the EXACT fix (`_set_col_formats`, html.py line numbers, the two-line diff) — and the spec view echoes NONE of it. No relaxed_leakage flag / RELAXED_LEAKAGE.md present, so no deferral needed; this is a genuine clean pass.

CONCLUSION: NO-LEAKAGE. The spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-16662

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
 def implementation_sortImportStatements (imports : List String) : List String :=
   Id.run do
     let mut sortedStatements := imports
-    sortedStatements := sortedStatements.mergeSort importLe
+    sortedStatements := sortedStatements.mergeSort (fun a b => decide (moduleName a ≤ moduleName b))
     return sortedStatements
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,6 @@
 def implementation_sortImportStatements (imports : List String) : List String :=
   Id.run do
     let mut sortedStatements := imports
-    sortedStatements := sortedStatements.mergeSort importLe
     return sortedStatements
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
 def implementation_sortImportStatements (imports : List String) : List String :=
   Id.run do
     let mut sortedStatements := imports
-    sortedStatements := sortedStatements.mergeSort importLe
+    sortedStatements := sortedStatements.mergeSort (fun a b => decide (firstToken a ≤ firstToken b))
     return sortedStatements
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
 def implementation_sortImportStatements (imports : List String) : List String :=
   Id.run do
     let mut sortedStatements := imports
-    sortedStatements := sortedStatements.mergeSort importLe
+    sortedStatements := (sortedStatements.mergeSort importLe).reverse
     return sortedStatements
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
 def implementation_sortImportStatements (imports : List String) : List String :=
   Id.run do
     let mut sortedStatements := imports
-    sortedStatements := sortedStatements.mergeSort importLe
+    sortedStatements := (sortedStatements.mergeSort importLe).dedup
     return sortedStatements
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,7 +81,7 @@
 def implementation_sortImportStatements (imports : List String) : List String :=
   Id.run do
     let mut sortedStatements := imports
-    sortedStatements := sortedStatements.mergeSort importLe
+    sortedStatements := sortedStatements.reverse.mergeSort importLe
     return sortedStatements
 -- impl-end
 
@@ -107,9 +107,9 @@
   intro imports
   unfold implementation_sortImportStatements problem_spec_sortImportStatements
   simp only [Id.run, pure]
-  refine ⟨List.mergeSort_perm imports importLe, ?_⟩
+  refine ⟨(List.mergeSort_perm imports.reverse importLe).trans (imports.reverse_perm), ?_⟩
   exact List.sorted_mergeSort
     (fun a b c => by simpa using importLe_trans a b c)
     (fun a b => by simpa using importLe_total a b)
-    imports
+    imports.reverse
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,7 +81,7 @@
 def implementation_sortImportStatements (imports : List String) : List String :=
   Id.run do
     let mut sortedStatements := imports
-    sortedStatements := sortedStatements.mergeSort importLe
+    sortedStatements := (sortedStatements.mergeSort importLe).drop 0
     return sortedStatements
 -- impl-end
 
@@ -106,7 +106,7 @@
         (implementation_sortImportStatements imports) := by
   intro imports
   unfold implementation_sortImportStatements problem_spec_sortImportStatements
-  simp only [Id.run, pure]
+  simp only [Id.run, pure, List.drop_zero]
   refine ⟨List.mergeSort_perm imports importLe, ?_⟩
   exact List.sorted_mergeSort
     (fun a b c => by simpa using importLe_trans a b c)
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -79,10 +79,10 @@
 
 -- impl-start
 def implementation_sortImportStatements (imports : List String) : List String :=
-  Id.run do
-    let mut sortedStatements := imports
-    sortedStatements := sortedStatements.mergeSort importLe
-    return sortedStatements
+  match imports with
+  | [] => []
+  | [x] => [x]
+  | x :: y :: rest => (x :: y :: rest).mergeSort importLe
 -- impl-end
 
 -- proof-start
@@ -105,11 +105,14 @@
       problem_spec_sortImportStatements imports
         (implementation_sortImportStatements imports) := by
   intro imports
-  unfold implementation_sortImportStatements problem_spec_sortImportStatements
-  simp only [Id.run, pure]
-  refine ⟨List.mergeSort_perm imports importLe, ?_⟩
-  exact List.sorted_mergeSort
-    (fun a b c => by simpa using importLe_trans a b c)
-    (fun a b => by simpa using importLe_total a b)
-    imports
+  unfold problem_spec_sortImportStatements implementation_sortImportStatements
+  match imports with
+  | [] => exact ⟨List.Perm.refl _, by simp⟩
+  | [x] => exact ⟨List.Perm.refl _, by simp⟩
+  | x :: y :: rest =>
+    refine ⟨List.mergeSort_perm _ importLe, ?_⟩
+    exact List.sorted_mergeSort
+      (fun a b c => by simpa using importLe_trans a b c)
+      (fun a b => by simpa using importLe_total a b)
+      (x :: y :: rest)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Ordering the import statements that head a generated source file.

A generated module begins with a block of import statements. Each statement is
either a plain module import (`import <module>`) or a selective import that
pulls named objects out of a module (`from <module> import <objects>`). The
generator collects these statements and must emit them in a canonical order.

The desired order follows the conventional sectioning of import blocks:

  * every plain module-import statement comes before every selective
    `from ... import ...` statement;
  * within each of those two groups the statements are ordered by the name of
    the module being imported (the token immediately following the leading
    keyword);
  * the same statements are emitted — none added, none dropped, none
    duplicated — only rearranged.

Each statement is carried as its textual line. `firstToken` is the leading
keyword (`import` or `from`); `moduleName` is the following whitespace-delimited
token, i.e. the module a statement refers to. A statement is a selective import
exactly when its leading keyword is `from`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each import
-- statement is carried as plain textual data; the leading keyword and the
-- module token are extracted by whitespace splitting, modeled directly below.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The leading whitespace-delimited token of a statement line (its keyword,
`import` or `from`). -/
def firstToken (line : String) : String := (line.splitOn " ").headD ""

/-- The module token of a statement line: the whitespace-delimited token that
immediately follows the leading keyword (the module being imported). -/
def moduleName (line : String) : String := (line.splitOn " ").getD 1 ""

/-- A statement is a selective import exactly when its leading keyword is
`from`. -/
def isFromStatement (line : String) : Bool := firstToken line == "from"

/-- The canonical ordering on statement lines: plain module imports precede
selective `from ... import ...` statements, and within each group the order is
by module name.

`importLe a b` holds when `a` may appear no later than `b`:

  * a plain import precedes any selective import;
  * a selective import never precedes a plain import;
  * two statements of the same kind are ordered by their module name. -/
def importLe (a b : String) : Bool :=
  match isFromStatement a, isFromStatement b with
  | false, true  => true
  | true,  false => false
  | _,     _     => decide (moduleName a ≤ moduleName b)
-- pure-end

-- post-conditions-start
/-- The emitted statements are exactly the input statements rearranged into the
canonical order:

  * `result` is a permutation of `imports` — the same multiset of statement
    lines, nothing added, dropped, or duplicated (frame: the content is pinned
    to the input);
  * `result` is sorted by `importLe` — consecutively, and hence (because
    `importLe` is a total preorder) globally: every plain import precedes every
    selective import, and within each group statements are by module name.

Together these pin the output for every input. -/
def problem_spec_sortImportStatements (imports result : List String) : Prop :=
  List.Perm result imports ∧ result.Pairwise (fun a b => importLe a b = true)
-- post-conditions-end

-- impl-start
def implementation_sortImportStatements (imports : List String) : List String :=
  Id.run do
    let mut sortedStatements := imports
    sortedStatements := sortedStatements.mergeSort importLe
    return sortedStatements
-- impl-end

-- proof-start
theorem importLe_trans (a b c : String) :
    importLe a b → importLe b c → importLe a c := by
  unfold importLe
  rcases hb : isFromStatement b <;> rcases ha : isFromStatement a <;>
    rcases hc : isFromStatement c <;>
    simp_all <;> intro h1 h2
  · exact le_trans h1 h2
  · exact le_trans h1 h2

theorem importLe_total (a b : String) : importLe a b || importLe b a := by
  unfold importLe
  rcases ha : isFromStatement a <;> rcases hb : isFromStatement b <;> simp_all <;>
    exact le_total _ _

theorem correct_sortImportStatements :
    ∀ imports : List String,
      problem_spec_sortImportStatements imports
        (implementation_sortImportStatements imports) := by
  intro imports
  unfold implementation_sortImportStatements problem_spec_sortImportStatements
  simp only [Id.run, pure]
  refine ⟨List.mergeSort_perm imports importLe, ?_⟩
  exact List.sorted_mergeSort
    (fun a b c => by simpa using importLe_trans a b c)
    (fun a b => by simpa using importLe_total a b)
    imports
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND — verify⇒resolve holds for every verifying same-spec impl found. Spec = `List.Perm result imports ∧ result.Pairwise importLe` with `importLe` a TOTAL PREORDER (plain-import<from-import, then String ≤ on the module token). This pins the output UNIQUELY on distinct-key inputs; the only degree of freedom is reordering TIES (statements with identical (isFromStatement, moduleName) but different full text). The F2P test (#24155) uses distinct module names, so any verifying impl reproduces gold's F2P output.

Protocol: same_spec=True confirmed for all 9 files (impl+proof elided). All verifications run concurrently in ≤4 background batches via scripts/lean_verify.sh (300s cap).

WRONG impls that the spec correctly REJECTS (fail to verify, EXIT 1 — spec is not too weak here):
- atk_1 = the real prepatch bug (module-name-only sort, mergeSort (moduleName a ≤ moduleName b)): EXIT=1. Prepatch reproduced.
- atk_2 = identity/no-sort: EXIT=1.
- atk_3 = group-by-firstToken-only (no module order within group): EXIT=1.
- atk_4 = descending (sort then reverse): EXIT=1.
- atk_5 = dedup after sort (breaks Perm on duplicates): EXIT=1.

ALTERNATIVE same-spec impls that VERIFY (EXIT=0, clean #print axioms = [propext, Classical.choice, Quot.sound]) — for each I materialized a faithful patch and RAN run_resolve (timeout 1800):
- atk_6 = reverse input then stable `mergeSort importLe` (reverses TIE order vs gold). Patch `sorted(list(imports)[::-1], key=(split[0]=='from', split[1]))`. run_resolve: resolved=true, completed=true.
- atk_7 = gold sort then `.drop 0` (behavioral no-op, echo). Patch `sorted(...)[0:]`. run_resolve: resolved=true, completed=true.
- atk_8 = partial-domain guard: identity on len≤1, else composite-key sort. Patch len<=1 branch. run_resolve: resolved=true, completed=true.

All three verifying variants are behaviorally equivalent to gold on distinct-key inputs (verified by local F2P simulation and by resolve); atk_6's only divergence from gold is tie-order, which is unobservable in Django's `set()`-sourced import lines where a tie requires two byte-identical strings (collapsed by the set). No verifying impl produces a patch that fails to resolve. positive_control (gold impl) verifies with clean axioms.

Refinement.md audit: all legs are R/I (op1 I: accumulator init; op2 R: sorted(key) ↔ mergeSort importLe with composite-key refinement; op3 I: return). No A-consumed / A-reference legs; meta.json axioms=[], deep_model_references=[], conf_skip=false. No kind-3 legs. The A-leg concern is vacuous here (no axioms), so correspondence trivially holds; str.split and sorted are modeled deeply (splitOn/mergeSort), consistent with mapping.md's type bijection.

Commands: `bash scripts/lean_verify.sh <atk>.lean` (verify + `#print axioms`), `run_resolve(iid, patch, timeout=1800, retries=1)` via harness. No attack breaks the spec after ≥8 attacks (5 rejected-wrong + 3 verifying-that-resolve). VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Ordering the import statements that head a generated source file.

A generated module begins with a block of import statements. Each statement is
either a plain module import (`import <module>`) or a selective import that
pulls named objects out of a module (`from <module> import <objects>`). The
generator collects these statements and must emit them in a canonical order.

The desired order follows the conventional sectioning of import blocks:

  * every plain module-import statement comes before every selective
    `from ... import ...` statement;
  * within each of those two groups the statements are ordered by the name of
    the module being imported (the token immediately following the leading
    keyword);
  * the same statements are emitted — none added, none dropped, none
    duplicated — only rearranged.

Each statement is carried as its textual line. `firstToken` is the leading
keyword (`import` or `from`); `moduleName` is the following whitespace-delimited
token, i.e. the module a statement refers to. A statement is a selective import
exactly when its leading keyword is `from`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each import
-- statement is carried as plain textual data; the leading keyword and the
-- module token are extracted by whitespace splitting, modeled directly below.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The leading whitespace-delimited token of a statement line (its keyword,
`import` or `from`). -/
def firstToken (line : String) : String := (line.splitOn " ").headD ""

/-- The module token of a statement line: the whitespace-delimited token that
immediately follows the leading keyword (the module being imported). -/
def moduleName (line : String) : String := (line.splitOn " ").getD 1 ""

/-- A statement is a selective import exactly when its leading keyword is
`from`. -/
def isFromStatement (line : String) : Bool := firstToken line == "from"

/-- The canonical ordering on statement lines: plain module imports precede
selective `from ... import ...` statements, and within each group the order is
by module name.

`importLe a b` holds when `a` may appear no later than `b`:

  * a plain import precedes any selective import;
  * a selective import never precedes a plain import;
  * two statements of the same kind are ordered by their module name. -/
def importLe (a b : String) : Bool :=
  match isFromStatement a, isFromStatement b with
  | false, true  => true
  | true,  false => false
  | _,     _     => decide (moduleName a ≤ moduleName b)
-- pure-end

-- post-conditions-start
/-- The emitted statements are exactly the input statements rearranged into the
canonical order:

  * `result` is a permutation of `imports` — the same multiset of statement
    lines, nothing added, dropped, or duplicated (frame: the content is pinned
    to the input);
  * `result` is sorted by `importLe` — consecutively, and hence (because
    `importLe` is a total preorder) globally: every plain import precedes every
    selective import, and within each group statements are by module name.

Together these pin the output for every input. -/
def problem_spec_sortImportStatements (imports result : List String) : Prop :=
  List.Perm result imports ∧ result.Pairwise (fun a b => importLe a b = true)
-- post-conditions-end

-- impl-start
def implementation_sortImportStatements (imports : List String) : List String :=
  Id.run do
    let mut sortedStatements := imports
    sortedStatements := sortedStatements.mergeSort importLe
    return sortedStatements
-- impl-end

-- proof-start
theorem importLe_trans (a b c : String) :
    importLe a b → importLe b c → importLe a c := by
  unfold importLe
  rcases hb : isFromStatement b <;> rcases ha : isFromStatement a <;>
    rcases hc : isFromStatement c <;>
    simp_all <;> intro h1 h2
  · exact le_trans h1 h2
  · exact le_trans h1 h2

theorem importLe_total (a b : String) : importLe a b || importLe b a := by
  unfold importLe
  rcases ha : isFromStatement a <;> rcases hb : isFromStatement b <;> simp_all <;>
    exact le_total _ _

theorem correct_sortImportStatements :
    ∀ imports : List String,
      problem_spec_sortImportStatements imports
        (implementation_sortImportStatements imports) := by
  intro imports
  unfold implementation_sortImportStatements problem_spec_sortImportStatements
  simp only [Id.run, pure]
  refine ⟨List.mergeSort_perm imports importLe, ?_⟩
  exact List.sorted_mergeSort
    (fun a b c => by simpa using importLe_trans a b c)
    (fun a b => by simpa using importLe_total a b)
    imports
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND — verify⇒resolve holds for every verifying same-spec impl found. Spec = `List.Perm result imports ∧ result.Pairwise importLe` with `importLe` a TOTAL PREORDER (plain-import<from-import, then String ≤ on the module token). This pins the output UNIQUELY on distinct-key inputs; the only degree of freedom is reordering TIES (statements with identical (isFromStatement, moduleName) but different full text). The F2P test (#24155) uses distinct module names, so any verifying impl reproduces gold's F2P output.

Protocol: same_spec=True confirmed for all 9 files (impl+proof elided). All verifications run concurrently in ≤4 background batches via scripts/lean_verify.sh (300s cap).

WRONG impls that the spec correctly REJECTS (fail to verify, EXIT 1 — spec is not too weak here):
- atk_1 = the real prepatch bug (module-name-only sort, mergeSort (moduleName a ≤ moduleName b)): EXIT=1. Prepatch reproduced.
- atk_2 = identity/no-sort: EXIT=1.
- atk_3 = group-by-firstToken-only (no module order within group): EXIT=1.
- atk_4 = descending (sort then reverse): EXIT=1.
- atk_5 = dedup after sort (breaks Perm on duplicates): EXIT=1.

ALTERNATIVE same-spec impls that VERIFY (EXIT=0, clean #print axioms = [propext, Classical.choice, Quot.sound]) — for each I materialized a faithful patch and RAN run_resolve (timeout 1800):
- atk_6 = reverse input then stable `mergeSort importLe` (reverses TIE order vs gold). Patch `sorted(list(imports)[::-1], key=(split[0]=='from', split[1]))`. run_resolve: resolved=true, completed=true.
- atk_7 = gold sort then `.drop 0` (behavioral no-op, echo). Patch `sorted(...)[0:]`. run_resolve: resolved=true, completed=true.
- atk_8 = partial-domain guard: identity on len≤1, else composite-key sort. Patch len<=1 branch. run_resolve: resolved=true, completed=true.

All three verifying variants are behaviorally equivalent to gold on distinct-key inputs (verified by local F2P simulation and by resolve); atk_6's only divergence from gold is tie-order, which is unobservable in Django's `set()`-sourced import lines where a tie requires two byte-identical strings (collapsed by the set). No verifying impl produces a patch that fails to resolve. positive_control (gold impl) verifies with clean axioms.

Refinement.md audit: all legs are R/I (op1 I: accumulator init; op2 R: sorted(key) ↔ mergeSort importLe with composite-key refinement; op3 I: return). No A-consumed / A-reference legs; meta.json axioms=[], deep_model_references=[], conf_skip=false. No kind-3 legs. The A-leg concern is vacuous here (no axioms), so correspondence trivially holds; str.split and sorted are modeled deeply (splitOn/mergeSort), consistent with mapping.md's type bijection.

Commands: `bash scripts/lean_verify.sh <atk>.lean` (verify + `#print axioms`), `run_resolve(iid, patch, timeout=1800, retries=1)` via harness. No attack breaks the spec after ≥8 attacks (5 rejected-wrong + 3 verifying-that-resolve). VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-16662 lean bundle. Modeled callee: MigrationWriter.as_string sort line (writer.py:178 @ base 0eb3e9b), post-patch `sorted(imports, key=lambda i: (i.split()[0]=='from', i.split()[1]))`. Confirmed against worktree (base commit) and gold patch from test.jsonl.

Checks performed:
1. lean_verify.sh exit 0; `#print axioms correct_sortImportStatements` = [propext, Classical.choice, Quot.sound] — no sorryAx, proof is genuine.
2. same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True — spec region byte-identical, impl/proof differ (correct 'same spec, buggy vs fixed impl' setup).
3. Spec = List.Perm result imports ∧ result.Pairwise importLe, with importLe = plain-import (isFromStatement false) before from-import, then moduleName ≤.

Differential test (500k random canonical import-statement lists over a realistic module pool): the REAL post-patch callee's output ALWAYS satisfies problem_spec_sortImportStatements. Found NO input where the spec rejects real repo behavior. The spec is, if anything, marginally WEAKER than the real function (Perm+Pairwise permits any valid tie-ordering; the real sort is stable/deterministic) — that is not a too-strong defect and does not admit the buggy prepatch (which the refinement.md correctly notes fails Pairwise on the #24155 case).

Only theoretical divergence: multi-space lines (e.g. 'import  time') where Python str.split() drops empty fields but Lean splitOn " " retains "", flipping moduleName. On such an input the real output would violate Pairwise. HOWEVER the real writer only ever assembles canonical single-space lines ('import %s' / 'from %s import ...'; module tokens are dotted ASCII identifiers with no internal spaces), so this input is OUTSIDE the real callee's reachable domain. mapping.md and conformance_check.py explicitly scope-restrict the model to canonical single-space lines and log the restriction — a legitimate, documented modeling boundary, not unfaithful drift. On the actual input domain the spec and real callee agree everywhere. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec=True across Solution.lean vs Solution_prepatch.lean). The public problem_statement already fully discloses the target behavior: it quotes the Django coding-style rule ('Place all import module statements before from module import objects in each section'), equates it to isort's default, and gives a concrete before/after example grouping plain `import` statements ahead of `from ... import ...`, each ordered by module name. The spec view encodes exactly this in neutral behavioral vocabulary (plain-import-before-selective-import, then by module name; firstToken/moduleName as leading/second whitespace token). It contains none of the gold-patch specifics absent from the problem_statement: no `writer`/`as_string`/`sorted_imports`/`split`/`key`/`lambda`, no tuple sort key `(i.split()[0]=="from", i.split()[1])`, no file path or line numbers. Modeled identifier `sortImportStatements` is behavioral, not the patched local `sorted_imports`. Impl and proof regions are elided in the spec view. No line leaks the gold edit beyond public info.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

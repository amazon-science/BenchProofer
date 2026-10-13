# P2 adversarial audit — pytest-dev__pytest-6197

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5b.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,15 +83,13 @@
 def implementation_packageCollect {α : Type}
     (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
     List α × Bool := Id.run do
-  -- Enumeration walks the directory structure only; it never imports the
-  -- package's own initialization file.
-  let importsOwnInit := false
+  -- BUG: eager mount imports the package's own init file before walking.
+  let importsOwnInit := true
   let mut collected : List α := []
   if initMatches then
     collected := collected ++ [initNode]
   for e in entries do
     if e.boundary then
-      -- the path is on this package's enumeration boundary: contribute nothing
       continue
     if e.isFile then
       collected := collected ++ e.yields
@@ -99,8 +97,6 @@
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
-`init` followed by `walkEntries`, generalized over the accumulator. -/
 private theorem packageCollect_forIn {α : Type}
     (entries : List (PkgEntry α)) (init : List α) :
     Id.run (forIn entries init (fun e r =>
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,15 +83,13 @@
 def implementation_packageCollect {α : Type}
     (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
     List α × Bool := Id.run do
-  -- Enumeration walks the directory structure only; it never imports the
-  -- package's own initialization file.
   let importsOwnInit := false
   let mut collected : List α := []
-  if initMatches then
-    collected := collected ++ [initNode]
+  -- BUG: forgets to yield the own-init Module collector.
+  let _ := initMatches
+  let _ := initNode
   for e in entries do
     if e.boundary then
-      -- the path is on this package's enumeration boundary: contribute nothing
       continue
     if e.isFile then
       collected := collected ++ e.yields
@@ -99,8 +97,6 @@
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
-`init` followed by `walkEntries`, generalized over the accumulator. -/
 private theorem packageCollect_forIn {α : Type}
     (entries : List (PkgEntry α)) (init : List α) :
     Id.run (forIn entries init (fun e r =>
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,15 +83,13 @@
 def implementation_packageCollect {α : Type}
     (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
     List α × Bool := Id.run do
-  -- Enumeration walks the directory structure only; it never imports the
-  -- package's own initialization file.
   let importsOwnInit := false
   let mut collected : List α := []
   if initMatches then
     collected := collected ++ [initNode]
   for e in entries do
-    if e.boundary then
-      -- the path is on this package's enumeration boundary: contribute nothing
+    -- BUG: inverted boundary test — keeps boundary paths, skips non-boundary
+    if !e.boundary then
       continue
     if e.isFile then
       collected := collected ++ e.yields
@@ -99,8 +97,6 @@
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
-`init` followed by `walkEntries`, generalized over the accumulator. -/
 private theorem packageCollect_forIn {α : Type}
     (entries : List (PkgEntry α)) (init : List α) :
     Id.run (forIn entries init (fun e r =>
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,24 +83,20 @@
 def implementation_packageCollect {α : Type}
     (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
     List α × Bool := Id.run do
-  -- Enumeration walks the directory structure only; it never imports the
-  -- package's own initialization file.
   let importsOwnInit := false
   let mut collected : List α := []
-  if initMatches then
-    collected := collected ++ [initNode]
   for e in entries do
     if e.boundary then
-      -- the path is on this package's enumeration boundary: contribute nothing
       continue
     if e.isFile then
       collected := collected ++ e.yields
+  -- BUG: own-init collector appended LAST instead of first.
+  if initMatches then
+    collected := collected ++ [initNode]
   return (collected, importsOwnInit)
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
-`init` followed by `walkEntries`, generalized over the accumulator. -/
 private theorem packageCollect_forIn {α : Type}
     (entries : List (PkgEntry α)) (init : List α) :
     Id.run (forIn entries init (fun e r =>
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,25 +82,11 @@
 -- impl-start
 def implementation_packageCollect {α : Type}
     (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
-    List α × Bool := Id.run do
-  -- Enumeration walks the directory structure only; it never imports the
-  -- package's own initialization file.
-  let importsOwnInit := false
-  let mut collected : List α := []
-  if initMatches then
-    collected := collected ++ [initNode]
-  for e in entries do
-    if e.boundary then
-      -- the path is on this package's enumeration boundary: contribute nothing
-      continue
-    if e.isFile then
-      collected := collected ++ e.yields
-  return (collected, importsOwnInit)
+    List α × Bool :=
+  ((if initMatches then [initNode] else []) ++ walkEntries entries, false)
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
-`init` followed by `walkEntries`, generalized over the accumulator. -/
 private theorem packageCollect_forIn {α : Type}
     (entries : List (PkgEntry α)) (init : List α) :
     Id.run (forIn entries init (fun e r =>
```

Attack 6 — `atk_5b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -82,55 +82,15 @@
 -- impl-start
 def implementation_packageCollect {α : Type}
     (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
-    List α × Bool := Id.run do
-  -- Enumeration walks the directory structure only; it never imports the
-  -- package's own initialization file.
-  let importsOwnInit := false
-  let mut collected : List α := []
-  if initMatches then
-    collected := collected ++ [initNode]
-  for e in entries do
-    if e.boundary then
-      -- the path is on this package's enumeration boundary: contribute nothing
-      continue
-    if e.isFile then
-      collected := collected ++ e.yields
-  return (collected, importsOwnInit)
+    List α × Bool :=
+  ((if initMatches then [initNode] else []) ++ walkEntries entries, false)
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
-`init` followed by `walkEntries`, generalized over the accumulator. -/
-private theorem packageCollect_forIn {α : Type}
-    (entries : List (PkgEntry α)) (init : List α) :
-    Id.run (forIn entries init (fun e r =>
-        if e.boundary = true then ForInStep.yield r
-        else if e.isFile = true then ForInStep.yield (r ++ e.yields)
-        else ForInStep.yield r))
-      = init ++ walkEntries entries := by
-  induction entries generalizing init with
-  | nil => simp [walkEntries, Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases hb : a.boundary = true
-    · simp only [hb, if_true, ih, walkEntries]
-      simp
-    · by_cases hf : a.isFile = true
-      · simp only [hb, hf, if_true, ih, walkEntries]
-        simp [List.append_assoc]
-      · simp only [hb, hf, ih, walkEntries]
-        simp
-
 theorem correct_packageCollect {α : Type}
     (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
     problem_spec_packageCollect initMatches initNode entries
       (implementation_packageCollect initMatches initNode entries) := by
   unfold problem_spec_packageCollect implementation_packageCollect
-  simp only [Id.run, bind, pure]
-  have hh := packageCollect_forIn entries
-  simp only [Id.run] at hh
-  refine ⟨?_, ?_⟩
-  · split <;> rfl
-  · split <;> simp [hh]
+  exact ⟨rfl, rfl⟩
 -- proof-end
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,24 +83,19 @@
 def implementation_packageCollect {α : Type}
     (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
     List α × Bool := Id.run do
-  -- Enumeration walks the directory structure only; it never imports the
-  -- package's own initialization file.
   let importsOwnInit := false
   let mut collected : List α := []
   if initMatches then
     collected := collected ++ [initNode]
   for e in entries do
     if e.boundary then
-      -- the path is on this package's enumeration boundary: contribute nothing
       continue
-    if e.isFile then
-      collected := collected ++ e.yields
+    -- BUG: ignores isFile — directories also contribute their yields.
+    collected := collected ++ e.yields
   return (collected, importsOwnInit)
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
-`init` followed by `walkEntries`, generalized over the accumulator. -/
 private theorem packageCollect_forIn {α : Type}
     (entries : List (PkgEntry α)) (init : List α) :
     Id.run (forIn entries init (fun e r =>
```

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,15 +83,13 @@
 def implementation_packageCollect {α : Type}
     (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
     List α × Bool := Id.run do
-  -- Enumeration walks the directory structure only; it never imports the
-  -- package's own initialization file.
-  let importsOwnInit := false
+  -- BUG: imports own init only when the init file matches the pattern.
+  let importsOwnInit := initMatches
   let mut collected : List α := []
   if initMatches then
     collected := collected ++ [initNode]
   for e in entries do
     if e.boundary then
-      -- the path is on this package's enumeration boundary: contribute nothing
       continue
     if e.isFile then
       collected := collected ++ e.yields
@@ -99,8 +97,6 @@
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
-`init` followed by `walkEntries`, generalized over the accumulator. -/
 private theorem packageCollect_forIn {α : Type}
     (entries : List (PkgEntry α)) (init : List α) :
     Id.run (forIn entries init (fun e r =>
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Enumerating the contents of a test package.

A test package is a directory carrying an initialization file. Enumerating the
package's contents walks the directory tree and produces the child collectors it
contains:

* if the package's own initialization file matches the configured test-file
  pattern, a collector for that file is produced first;
* then, for every visited path, the path is examined: paths belonging to the
  package's own enumeration boundary (its own initialization file, or paths that
  already sit inside a nested sub-package that has been accounted for) contribute
  nothing, and every other regular file contributes whatever child collectors it
  resolves to.

Enumerating the package's contents is a directory-structure operation: it
inspects paths and builds collectors lazily. It must therefore NOT import the
package's own initialization file as a side effect — importing it is the job of
the produced collectors when (and if) they are later realized, not of the
enumeration itself. Importing an arbitrary package's initialization file merely
because its directory is being scanned would run that file's top-level code
prematurely.

The values modeled here are: the sequence of child collectors produced, and
whether enumerating the package imported the package's own initialization file.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-path
-- resolution of a regular file to its child collectors is an orthogonal,
-- unchanged operation whose result enters as plain input data (the `yields`
-- field of each enumerated entry); likewise whether a path lies on the package's
-- own enumeration boundary enters as a plain Boolean observation. No
-- `opaque`/`axiom` callee contract is therefore needed.
-- axioms-end

-- pure-start
/-- One enumerated path of the package directory, reduced to what content
enumeration consumes:

* `boundary` — the path contributes nothing to this package's own enumeration
  (it is the package's own initialization file, or it already sits inside a
  nested sub-package that has been accounted for);
* `isFile` — the path is a regular file (as opposed to a directory);
* `yields` — the child collectors a non-boundary regular file resolves to. -/
structure PkgEntry (α : Type) where
  boundary : Bool
  isFile : Bool
  yields : List α

/-- The child collectors produced by walking the enumerated paths, front
recursively: a boundary path or a directory contributes nothing; a non-boundary
regular file contributes its resolved collectors. -/
def walkEntries {α : Type} : List (PkgEntry α) → List α
  | [] => []
  | e :: es =>
    (if e.boundary || !e.isFile then [] else e.yields) ++ walkEntries es
-- pure-end

-- post-conditions-start
/-- Enumerating a package's contents:

* produces, in order, the collector for the package's own initialization file
  when it matches the configured test-file pattern (`initMatches`), followed by
  the child collectors of every non-boundary regular file enumerated; and
* does NOT import the package's own initialization file (`result.2 = false`):
  enumeration is a directory-structure operation with no such side effect.

Both output components are pinned to the inputs: the produced sequence is the
exact walk of the enumerated paths, and the import flag is unconditionally
absent. -/
def problem_spec_packageCollect {α : Type}
    (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α))
    (result : List α × Bool) : Prop :=
  result.2 = false ∧
  result.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
-- post-conditions-end

-- impl-start
def implementation_packageCollect {α : Type}
    (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
    List α × Bool := Id.run do
  -- Enumeration walks the directory structure only; it never imports the
  -- package's own initialization file.
  let importsOwnInit := false
  let mut collected : List α := []
  if initMatches then
    collected := collected ++ [initNode]
  for e in entries do
    if e.boundary then
      -- the path is on this package's enumeration boundary: contribute nothing
      continue
    if e.isFile then
      collected := collected ++ e.yields
  return (collected, importsOwnInit)
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
`init` followed by `walkEntries`, generalized over the accumulator. -/
private theorem packageCollect_forIn {α : Type}
    (entries : List (PkgEntry α)) (init : List α) :
    Id.run (forIn entries init (fun e r =>
        if e.boundary = true then ForInStep.yield r
        else if e.isFile = true then ForInStep.yield (r ++ e.yields)
        else ForInStep.yield r))
      = init ++ walkEntries entries := by
  induction entries generalizing init with
  | nil => simp [walkEntries, Id.run, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases hb : a.boundary = true
    · simp only [hb, if_true, ih, walkEntries]
      simp
    · by_cases hf : a.isFile = true
      · simp only [hb, hf, if_true, ih, walkEntries]
        simp [List.append_assoc]
      · simp only [hb, hf, ih, walkEntries]
        simp

theorem correct_packageCollect {α : Type}
    (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
    problem_spec_packageCollect initMatches initNode entries
      (implementation_packageCollect initMatches initNode entries) := by
  unfold problem_spec_packageCollect implementation_packageCollect
  simp only [Id.run, bind, pure]
  have hh := packageCollect_forIn entries
  simp only [Id.run] at hh
  refine ⟨?_, ?_⟩
  · split <;> rfl
  · split <;> simp [hh]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_packageCollect is a TOTAL, fully-pinning equality spec — it constrains BOTH output components exactly: result.2 = false AND result.1 = (if initMatches then [initNode] else []) ++ walkEntries entries. There is no free/underspecified degree of freedom, so any verifying impl must produce byte-exact gold output. No axioms/opaque declared (axioms region is a justified narrative skip; axiom_check.py is a legitimate G-AX skip). REFINEMENT AUDIT: refinement.md rows 1-6 are all R (type refinement of concrete imperative ops); no A-consumed and no A-reference legs exist (grep for axiom|opaque in Solution.lean = NONE), so there are no A-legs whose callee-correspondence could be wrong — the A-leg attack surface is empty by construction, and _collectfile's per-file resolution + the boundary predicate correctly enter as plain input data (yields / boundary), not as axiomatized contracts. No kind-3 leg.

SAME-SPEC: all 8 attack files pass swebench_unified.markers.same_spec == True (lines 1-81 byte-identical; only impl+proof edited).

### ATTACKS (all verified via `bash scripts/lean_verify.sh <f>`, run concurrently ≤4/batch; genuine elaboration errors, NOT timeouts):
- atk_1 (prepatch regression, importsOwnInit:=true): EXIT=1, rfl failed on `...,true).2 = false` (reproduces prepatch bug). PREPATCH REPRODUCED.
- atk_2 (partial-domain, drops initNode): EXIT=1, `⊢ False` under h:initMatches=true (unsolved goals).
- atk_3 (boundary inverted, keeps boundary/skips non-boundary): EXIT=1, unsolved goals at 131:2.
- atk_4 (control-flow-effect, initNode appended LAST not first): EXIT=1, unsolved goals at 131:2.
- atk_5 (ungrounded-oracle echo of spec RHS, reference proof shape): EXIT=1, `split` failed (proof-shape mismatch only).
- atk_5b (same echo impl, proper `exact ⟨rfl,rfl⟩` proof): EXIT=0 VERIFIES, `#print axioms correct_packageCollect` => does NOT depend on any axioms (clean). This is the ONLY closing candidate.
- atk_6 (isFile ignored, dirs contribute yields): EXIT=1, unsolved goals at 130:2.
- atk_7 (importsOwnInit:=initMatches, conditional flag): EXIT=1, rfl failed at 130:14.

CLOSING-CANDIDATE RESOLVE (mandatory): atk_5b is the only same-spec wrong-impl candidate that closes with clean axioms. Because the spec pins both outputs exactly, the echo is behaviorally IDENTICAL to gold, so its faithful refined patch IS the gold patch. Materialized it and ran run_resolve('pytest-dev__pytest-6197', gold_patch) via swebench_unified.harness => RESOLVED: True (note='resolved'). This is a resolving echo of the gold, which per the 2026-08-06 G-PANEL-1/EQ policy is NOT a weakness. No closing candidate has a non-resolving faithful patch.

POSITIVE CONTROL: unmodified Solution.lean verifies EXIT=0; `#print axioms correct_packageCollect` => [propext, Quot.sound] only (clean, no sorryAx).

CONCLUSION: 7 distinct wrong-impl classes attacked (partial-domain, boundary-inversion, control-flow-order, isFile-ignored, conditional-flag, prepatch, ungrounded-echo). Every behaviorally-wrong impl FAILS to close (genuine goal errors, not timeouts). The one impl that closes with clean axioms is a behavioral twin of gold whose faithful patch RESOLVES. verify⇒correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5b.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Enumerating the contents of a test package.

A test package is a directory carrying an initialization file. Enumerating the
package's contents walks the directory tree and produces the child collectors it
contains:

* if the package's own initialization file matches the configured test-file
  pattern, a collector for that file is produced first;
* then, for every visited path, the path is examined: paths belonging to the
  package's own enumeration boundary (its own initialization file, or paths that
  already sit inside a nested sub-package that has been accounted for) contribute
  nothing, and every other regular file contributes whatever child collectors it
  resolves to.

Enumerating the package's contents is a directory-structure operation: it
inspects paths and builds collectors lazily. It must therefore NOT import the
package's own initialization file as a side effect — importing it is the job of
the produced collectors when (and if) they are later realized, not of the
enumeration itself. Importing an arbitrary package's initialization file merely
because its directory is being scanned would run that file's top-level code
prematurely.

The values modeled here are: the sequence of child collectors produced, and
whether enumerating the package imported the package's own initialization file.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-path
-- resolution of a regular file to its child collectors is an orthogonal,
-- unchanged operation whose result enters as plain input data (the `yields`
-- field of each enumerated entry); likewise whether a path lies on the package's
-- own enumeration boundary enters as a plain Boolean observation. No
-- `opaque`/`axiom` callee contract is therefore needed.
-- axioms-end

-- pure-start
/-- One enumerated path of the package directory, reduced to what content
enumeration consumes:

* `boundary` — the path contributes nothing to this package's own enumeration
  (it is the package's own initialization file, or it already sits inside a
  nested sub-package that has been accounted for);
* `isFile` — the path is a regular file (as opposed to a directory);
* `yields` — the child collectors a non-boundary regular file resolves to. -/
structure PkgEntry (α : Type) where
  boundary : Bool
  isFile : Bool
  yields : List α

/-- The child collectors produced by walking the enumerated paths, front
recursively: a boundary path or a directory contributes nothing; a non-boundary
regular file contributes its resolved collectors. -/
def walkEntries {α : Type} : List (PkgEntry α) → List α
  | [] => []
  | e :: es =>
    (if e.boundary || !e.isFile then [] else e.yields) ++ walkEntries es
-- pure-end

-- post-conditions-start
/-- Enumerating a package's contents:

* produces, in order, the collector for the package's own initialization file
  when it matches the configured test-file pattern (`initMatches`), followed by
  the child collectors of every non-boundary regular file enumerated; and
* does NOT import the package's own initialization file (`result.2 = false`):
  enumeration is a directory-structure operation with no such side effect.

Both output components are pinned to the inputs: the produced sequence is the
exact walk of the enumerated paths, and the import flag is unconditionally
absent. -/
def problem_spec_packageCollect {α : Type}
    (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α))
    (result : List α × Bool) : Prop :=
  result.2 = false ∧
  result.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
-- post-conditions-end

-- impl-start
def implementation_packageCollect {α : Type}
    (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
    List α × Bool := Id.run do
  -- Enumeration walks the directory structure only; it never imports the
  -- package's own initialization file.
  let importsOwnInit := false
  let mut collected : List α := []
  if initMatches then
    collected := collected ++ [initNode]
  for e in entries do
    if e.boundary then
      -- the path is on this package's enumeration boundary: contribute nothing
      continue
    if e.isFile then
      collected := collected ++ e.yields
  return (collected, importsOwnInit)
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
`init` followed by `walkEntries`, generalized over the accumulator. -/
private theorem packageCollect_forIn {α : Type}
    (entries : List (PkgEntry α)) (init : List α) :
    Id.run (forIn entries init (fun e r =>
        if e.boundary = true then ForInStep.yield r
        else if e.isFile = true then ForInStep.yield (r ++ e.yields)
        else ForInStep.yield r))
      = init ++ walkEntries entries := by
  induction entries generalizing init with
  | nil => simp [walkEntries, Id.run, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases hb : a.boundary = true
    · simp only [hb, if_true, ih, walkEntries]
      simp
    · by_cases hf : a.isFile = true
      · simp only [hb, hf, if_true, ih, walkEntries]
        simp [List.append_assoc]
      · simp only [hb, hf, ih, walkEntries]
        simp

theorem correct_packageCollect {α : Type}
    (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
    problem_spec_packageCollect initMatches initNode entries
      (implementation_packageCollect initMatches initNode entries) := by
  unfold problem_spec_packageCollect implementation_packageCollect
  simp only [Id.run, bind, pure]
  have hh := packageCollect_forIn entries
  simp only [Id.run] at hh
  refine ⟨?_, ?_⟩
  · split <;> rfl
  · split <;> simp [hh]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_packageCollect is a TOTAL, fully-pinning equality spec — it constrains BOTH output components exactly: result.2 = false AND result.1 = (if initMatches then [initNode] else []) ++ walkEntries entries. There is no free/underspecified degree of freedom, so any verifying impl must produce byte-exact gold output. No axioms/opaque declared (axioms region is a justified narrative skip; axiom_check.py is a legitimate G-AX skip). REFINEMENT AUDIT: refinement.md rows 1-6 are all R (type refinement of concrete imperative ops); no A-consumed and no A-reference legs exist (grep for axiom|opaque in Solution.lean = NONE), so there are no A-legs whose callee-correspondence could be wrong — the A-leg attack surface is empty by construction, and _collectfile's per-file resolution + the boundary predicate correctly enter as plain input data (yields / boundary), not as axiomatized contracts. No kind-3 leg.

SAME-SPEC: all 8 attack files pass swebench_unified.markers.same_spec == True (lines 1-81 byte-identical; only impl+proof edited).

### ATTACKS (all verified via `bash scripts/lean_verify.sh <f>`, run concurrently ≤4/batch; genuine elaboration errors, NOT timeouts):
- atk_1 (prepatch regression, importsOwnInit:=true): EXIT=1, rfl failed on `...,true).2 = false` (reproduces prepatch bug). PREPATCH REPRODUCED.
- atk_2 (partial-domain, drops initNode): EXIT=1, `⊢ False` under h:initMatches=true (unsolved goals).
- atk_3 (boundary inverted, keeps boundary/skips non-boundary): EXIT=1, unsolved goals at 131:2.
- atk_4 (control-flow-effect, initNode appended LAST not first): EXIT=1, unsolved goals at 131:2.
- atk_5 (ungrounded-oracle echo of spec RHS, reference proof shape): EXIT=1, `split` failed (proof-shape mismatch only).
- atk_5b (same echo impl, proper `exact ⟨rfl,rfl⟩` proof): EXIT=0 VERIFIES, `#print axioms correct_packageCollect` => does NOT depend on any axioms (clean). This is the ONLY closing candidate.
- atk_6 (isFile ignored, dirs contribute yields): EXIT=1, unsolved goals at 130:2.
- atk_7 (importsOwnInit:=initMatches, conditional flag): EXIT=1, rfl failed at 130:14.

CLOSING-CANDIDATE RESOLVE (mandatory): atk_5b is the only same-spec wrong-impl candidate that closes with clean axioms. Because the spec pins both outputs exactly, the echo is behaviorally IDENTICAL to gold, so its faithful refined patch IS the gold patch. Materialized it and ran run_resolve('pytest-dev__pytest-6197', gold_patch) via swebench_unified.harness => RESOLVED: True (note='resolved'). This is a resolving echo of the gold, which per the 2026-08-06 G-PANEL-1/EQ policy is NOT a weakness. No closing candidate has a non-resolving faithful patch.

POSITIVE CONTROL: unmodified Solution.lean verifies EXIT=0; `#print axioms correct_packageCollect` => [propext, Quot.sound] only (clean, no sorryAx).

CONCLUSION: 7 distinct wrong-impl classes attacked (partial-domain, boundary-inversion, control-flow-order, isFile-ignored, conditional-flag, prepatch, ungrounded-echo). Every behaviorally-wrong impl FAILS to close (genuine goal errors, not timeouts). The one impl that closes with clean axioms is a behavioral twin of gold whose faithful patch RESOLVES. verify⇒correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attacker (spec-too-strong / drift). No divergence between the modeled function and the real post-patch Package.collect could be found.

Setup verified:
- Solution.lean compiles via lean_verify.sh (exit 0). `#print axioms correct_packageCollect` = [propext, Quot.sound] — clean, NO sorryAx; proof is genuine.
- same_spec(Solution, Solution_prepatch) = True (spec region byte-identical; only impl region differs). G-HYGIENE/G-LEAK pass in meta.json.
- Real callee: python.py:641-670 at base_commit e856638ba (PRE-patch worktree; line 642 still has self._mount_obj_if_needed()). The gold patch removes exactly that leading statement; rest of the body is unchanged.

Faithfulness analysis (spec = result.2 = false ∧ result.1 = (if initMatches then [initNode] else []) ++ walkEntries entries):
1. Ordering: real generator yields Module(init_module,self) first when init matches, then walks — matches the [initNode]-prefix ++ walk. ✓
2. walkEntries per path: both real skip branches (own __init__.py at 654; pkg_prefix membership at 658-662) `continue` with no yield regardless of is_file → correctly collapse to the single `boundary` observable; a non-boundary regular file yields `list(self._collectfile(path))` → `yields`; a directory (isFile=false, non-boundary) yields no collector (only updates pkg_prefixes bookkeeping, itself reflected in later entries' boundary). Spec's (if e.boundary || !e.isFile then [] else e.yields) matches every case. ✓ The stateful pkg_prefixes accumulation is faithfully abstracted into per-entry boundary Booleans fed as input data — not axiomatized, no over-strength.
3. result.2 = false unconditionally: the ONLY own-init import trigger in collect() was _mount_obj_if_needed() (line 642), removed by the patch; coordinated edits make Module.__init__/obj lazy so no path imports the own __init__.py during enumeration. This is exactly the behavior the F2P tests (test_does_not_eagerly_collect_packages, test_does_not_put_src_on_path) observe. ✓

I specifically probed for a too-strong pin the real callee could violate on some realizable input (wrong ordering, a skip branch that should still yield, or any path that would import the own init) and found none. The spec is neither too strong nor drifted from real repo behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view projection (impl/proof elided) inspected directly via markers.spec_view. Mechanical G-LEAK screen (leakage.screen) PASSES with zero hard failures; spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec == True). No relaxation in play (relaxed_leakage=None, no RELAXED_LEAKAGE.md).

Gold-reconstruction assessment: the gold edit removes self._mount_obj_if_needed() from Package.collect so package enumeration no longer eagerly imports its own __init__.py; the modeled discriminator is result.2 = false ('enumeration does NOT import the package's own initialization file'). This behavior is ALREADY PUBLIC in problem_statement, which states verbatim that pytest 5.2.3 wrongly 'tries to import any __init__.py file under the current directory' — i.e. the fix (don't eagerly import __init__.py during collection) is disclosed by the task itself. The spec view therefore restates public knowledge, not a hidden gold edit.

No patched repo symbol appears in the view: changed-symbols set {genfunctions, PyobjMixin, isinitpath, mount_obj_if_needed} — none embedded in any spec-view identifier or comment. No patched file path/module (src/_pytest/python.py) present. No gold-diff line reproduced, no diff markers, no bug/fix/regression narration in the projected comments. The abstract PkgEntry/walkEntries directory-walk encoding does not localize the specific edit (removal of an eager-mount call in Package.collect) beyond what problem_statement already reveals. Bug/fix narration and symbol references are confined to refinement.md and mapping.md, which are NOT part of the consumer spec view. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

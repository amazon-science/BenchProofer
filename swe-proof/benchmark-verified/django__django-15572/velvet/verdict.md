# P2 adversarial audit — django__django-15572

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,7 +131,7 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      result := (if keepConfigured e then [normalizePath e] else []) ++ result
+      result := [normalizePath e] ++ result
       i := i - 1
     return result
     -- impl-end
@@ -187,7 +187,7 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      result := (if keepLoader e then [normalizePath e] else []) ++ result
+      result := (if !isFrameworkOwned e then [normalizePath e] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,7 +131,7 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      result := (if keepConfigured e then [normalizePath e] else []) ++ result
+      result := [normalizePath e] ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,7 +131,7 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      result := (if keepConfigured e then [normalizePath e] else []) ++ result
+      result := (if keepConfigured e then [] else [normalizePath e]) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,18 +122,7 @@
   ensures ∀ p, p ∈ out → ∃ e, e ∈ entries ∧ keepConfigured e = true ∧ p = normalizePath e
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := entries.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ entries.length
-      invariant result = collectConfigured (entries.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := entries[i - 1]!
-      result := (if keepConfigured e then [normalizePath e] else []) ++ result
-      i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step for the configured collection: dropping one fewer
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -187,7 +187,7 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      result := (if keepLoader e then [normalizePath e] else []) ++ result
+      result := (if !isFrameworkOwned e then [normalizePath e] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,7 +131,7 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      result := (if keepConfigured e then [normalizePath e] else []) ++ result
+      result := result ++ (if keepConfigured e then [normalizePath e] else [])
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,7 +131,7 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      result := (if keepConfigured e then [normalizePath e] else []) ++ result
+      result := (if keepConfigured e then [normalizePath (normalizePath e)] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 8 — `atk_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,18 +122,7 @@
   ensures ∀ p, p ∈ out → ∃ e, e ∈ entries ∧ keepConfigured e = true ∧ p = normalizePath e
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := entries.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ entries.length
-      invariant result = collectConfigured (entries.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := entries[i - 1]!
-      result := (if keepConfigured e then [normalizePath e] else []) ++ result
-      i := i - 1
-    return result
+    return collectConfigured entries
     -- impl-end
 
 /- The backward-fold step for the configured collection: dropping one fewer
@@ -178,18 +167,7 @@
   ensures ∀ es, entries = [] :: es → out = collectLoader es
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := entries.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ entries.length
-      invariant result = collectLoader (entries.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := entries[i - 1]!
-      result := (if keepLoader e then [normalizePath e] else []) ++ result
-      i := i - 1
-    return result
+    return collectLoader entries
     -- impl-end
 
 /- The backward-fold step for the loader collection. -/
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An unchanged path-normaliser applied to every retained entry: it turns a raw
   directory entry (a character sequence) into the canonical absolute path that
   gets watched. It is a free function (OPAQUE) because the operation refines the
   collection step around it, never changing the normaliser itself; nothing is
   asserted about its result, so there is nothing for G-AX to validate.
   Provenance: mapping.md §3. -/
opaque normalizePath : List Char → List Char

/- An unchanged predicate that recognises an entry already owned by the
   framework's own bundled-template area; such entries are excluded from the
   watch set. Also OPAQUE (a free boolean function of the entry): the operation
   keeps deferring to it unchanged, asserting nothing about its value.
   Provenance: mapping.md §3. -/
opaque isFrameworkOwned : List Char → Bool
-- axioms-end

-- pure-start
/- Whether a directly-configured directory entry is admissible: an entry is kept
   only when it is non-empty. An empty entry carries no usable location and must
   be dropped before normalisation, so that it can never be expanded into a
   spurious watched location. -/
def keepConfigured (entry : List Char) : Bool :=
  decide (entry ≠ [])

/- Whether a loader-supplied directory entry is admissible: it must be non-empty
   AND not already owned by the framework. Emptiness is checked first and on its
   own, independently of the ownership test. -/
def keepLoader (entry : List Char) : Bool :=
  decide (entry ≠ []) && (!isFrameworkOwned entry)

/- The watched locations contributed by a list of directly-configured entries:
   each admissible entry is normalised, in order; inadmissible entries
   contribute nothing. Front-recursive so a single unfold is available per loop
   step (the Velvet fold pattern). -/
def collectConfigured : List (List Char) → List (List Char)
  | []      => []
  | e :: es => (if keepConfigured e then [normalizePath e] else []) ++ collectConfigured es

/- The watched locations contributed by a list of loader-supplied entries: same
   shape, with the loader admissibility test. -/
def collectLoader : List (List Char) → List (List Char)
  | []      => []
  | e :: es => (if keepLoader e then [normalizePath e] else []) ++ collectLoader es

@[grind] lemma collectConfigured_nil : collectConfigured [] = [] := rfl
@[grind] lemma collectConfigured_cons (e : List Char) (es : List (List Char)) :
    collectConfigured (e :: es) =
      (if keepConfigured e then [normalizePath e] else []) ++ collectConfigured es := rfl

@[grind] lemma collectLoader_nil : collectLoader [] = [] := rfl
@[grind] lemma collectLoader_cons (e : List Char) (es : List (List Char)) :
    collectLoader (e :: es) =
      (if keepLoader e then [normalizePath e] else []) ++ collectLoader es := rfl

/- An empty entry is never admissible at either site. These are the clauses the
   pre-image skeleton (which omits the emptiness test) cannot satisfy. -/
@[grind] lemma keepConfigured_empty : keepConfigured [] = false := by
  unfold keepConfigured; simp
@[grind] lemma keepLoader_empty : keepLoader [] = false := by
  unfold keepLoader; simp

/- Hence an empty entry contributes nothing to either collection, regardless of
   the surrounding entries. -/
@[grind] lemma collectConfigured_cons_empty (es : List (List Char)) :
    collectConfigured ([] :: es) = collectConfigured es := by
  rw [collectConfigured_cons, keepConfigured_empty]; simp

@[grind] lemma collectLoader_cons_empty (es : List (List Char)) :
    collectLoader ([] :: es) = collectLoader es := by
  rw [collectLoader_cons, keepLoader_empty]; simp

/- Nothing is invented: every collected location is the normalisation of some
   admissible entry of the input. Proven by induction; `@[grind]` so the
   corresponding postcondition discharges automatically. -/
@[grind] lemma collectConfigured_mem (es : List (List Char)) :
    ∀ p, p ∈ collectConfigured es →
      ∃ e, e ∈ es ∧ keepConfigured e = true ∧ p = normalizePath e := by
  induction es with
  | nil => intro p h; simp [collectConfigured] at h
  | cons e es ih =>
      intro p h
      rw [collectConfigured_cons] at h
      by_cases hk : keepConfigured e = true
      · rw [if_pos hk] at h
        rw [List.singleton_append, List.mem_cons] at h
        rcases h with hpe | htail
        · exact ⟨e, List.mem_cons_self, hk, hpe⟩
        · obtain ⟨e', hmem, hkeep, hpe'⟩ := ih p htail
          exact ⟨e', List.mem_cons_of_mem _ hmem, hkeep, hpe'⟩
      · rw [if_neg hk, List.nil_append] at h
        obtain ⟨e', hmem, hkeep, hpe'⟩ := ih p h
        exact ⟨e', List.mem_cons_of_mem _ hmem, hkeep, hpe'⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Gather the set of locations to watch from the directly-configured directory
   entries. The result is exactly the per-entry expansion of the input: each
   non-empty entry is normalised, in order, and every empty entry is skipped.
   `entries` is read-only (not `mut`); the loop builds a fresh result and never
   mutates its input (directive 5).

   The behaviour of interest is the emptiness skip: an empty configured entry
   must contribute nothing to the watched locations — pinned by the second
   postcondition. -/
method collectConfiguredDirs (entries : List (List Char)) return (out : List (List Char))
  ensures out = collectConfigured entries
  ensures ∀ es, entries = [] :: es → out = collectConfigured es
  ensures ∀ p, p ∈ out → ∃ e, e ∈ entries ∧ keepConfigured e = true ∧ p = normalizePath e
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectConfigured (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      result := (if keepConfigured e then [normalizePath e] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the configured collection: dropping one fewer
   element exposes the entry at `i-1` on the front, so `collectConfigured` peels
   one keep-decision. This is the single goal `loom_solve` leaves for the loop
   body. -/
lemma collectConfigured_drop_step (es : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ es.length) :
    collectConfigured (es.drop (i - 1)) =
      (if keepConfigured es[i - 1]! then [normalizePath es[i - 1]!] else [])
        ++ collectConfigured (es.drop i) := by
  have hlt : i - 1 < es.length := by omega
  have hcons : es.drop (i - 1) = es[i - 1]! :: es.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, collectConfigured_cons]

prove_correct collectConfiguredDirs by
  loom_solve
  rw [collectConfigured_drop_step entries i (by omega) (by omega)]
  rw [‹result = collectConfigured (entries.drop i)›]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Gather the set of locations to watch from a loader's supplied directory
   entries. Same shape as the configured collection, but an entry is admissible
   only when it is non-empty AND not already owned by the framework. The
   emptiness skip is independent of the ownership test: an empty entry
   contributes nothing even if it would otherwise pass the ownership test
   (pinned by the second postcondition).

   `entries` is read-only (not `mut`); the loop builds a fresh result and never
   mutates its input (directive 5). -/
method collectLoaderDirs (entries : List (List Char)) return (out : List (List Char))
  ensures out = collectLoader entries
  ensures ∀ es, entries = [] :: es → out = collectLoader es
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectLoader (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      result := (if keepLoader e then [normalizePath e] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the loader collection. -/
lemma collectLoader_drop_step (es : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ es.length) :
    collectLoader (es.drop (i - 1)) =
      (if keepLoader es[i - 1]! then [normalizePath es[i - 1]!] else [])
        ++ collectLoader (es.drop i) := by
  have hlt : i - 1 < es.length := by omega
  have hcons : es.drop (i - 1) = es[i - 1]! :: es.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, collectLoader_cons]

prove_correct collectLoaderDirs by
  loom_solve
  rw [collectLoader_drop_step entries i (by omega) (by omega)]
  rw [‹result = collectLoader (entries.drop i)›]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-15572 (velvet). verifier: `bash scripts/lean_verify.sh <file>`; same_spec via swebench_unified.markers.same_spec with get_backend('velvet').language. All 8 attacks + pos_control confirmed same_spec=True (impl-region-only edits; axioms/pure/pre/post/signature byte-identical).

SPEC STRENGTH: TIGHT. Both methods (collectConfiguredDirs / collectLoaderDirs) carry a FULL FUNCTIONAL postcondition `out = collectConfigured entries` / `out = collectLoader entries`, where collectConfigured/collectLoader are CONCRETE recursive defs (not an opaque answer-key), plus a redundant empty-skip clause and a membership clause. This fully pins the abstract output: a verifying impl must recompute the exact per-entry filtered/normalised list in order.

### ATTACKS (all same_spec=True, all EXIT 1 = fail-to-verify; logs in scratch dir):
- atk_1 = prepatch bug (site1 normalises unconditionally; site2 drops only framework-owned): EXIT 1, unsolved goals at line 156 (collectConfiguredDirs) AND 209 (collectLoaderDirs) — the empty-skip clause at both sites.
- atk_2 (site1 keep-all, no emptiness filter): EXIT 1, unsolved goal line 156.
- atk_3 (site1 inverted filter, keeps only EMPTY entries): EXIT 1, unsolved goal line 156.
- atk_4 (partial-domain / `return []`): EXIT 1, postcondition `out = collectConfigured entries` unsatisfiable.
- atk_5 (loader half-fix: site2 drops only framework-owned, keeps empties): EXIT 1, unsolved goal line 209.
- atk_6 (control-flow-effect: correct filter but appends contribution at TAIL in backward loop => reversed order): EXIT 1 line 156 — list-equality postcondition pins order.
- atk_7 (ungrounded-oracle/opaque-callee misuse: double normalizePath): EXIT 1 line 156 — confirms opacity of normalizePath does NOT create a masking surface; postcondition forces the exact applied term.
- atk_echo (echo of oracle: `return collectConfigured entries` / `return collectLoader entries`): EXIT 1 (`No goals to be solved` at the frozen prove_correct bodies) — behaviourally correct but fails as-is; not a verifying wrong impl.

POSITIVE CONTROL (gold impl, same_spec=True): EXIT 0 — spec non-vacuous.
PREPATCH (Solution_prepatch.lean, same_spec=True): EXIT 1 at lines 163 & 220 — bug reproduced at both loop invariants on the empty-skip goal (matches the reported regression: empty DIRS entry normalised to project root and watched).

MANDATORY STEP 2 (materialize+resolve every verifying wrong impl): VACUOUSLY SATISFIED — ZERO wrong impls verified, so there is no verifying-wrong-impl whose faithful patch could fail to resolve. `patches` intentionally empty. No resolve run was required and none would change the verdict.

REFINEMENT.MD LEG AUDIT (A-leg focus): A1/B1 = R (List (List Char) <-> str/Path entries). A2/B2 (emptiness filter, the discriminating change) = I, modeled DEEPLY via keepConfigured/keepLoader + spelled-out folds — NOT hidden behind an axiom. A3/B3 normalizePath <-> `cwd / to_path(dir)` = A-consumed (opaque free fn, UNCHANGED by patch, no asserted ensures). B2 isFrameworkOwned <-> `is_django_path(directory)` = A-consumed (opaque free fn, UNCHANGED, no ensures). A4/B4 = I+R (fold + set membership carrier). NO kind-3 leg. G-AX skip is legitimate: no `axiom`/`_prop` decls, no `ensures` asserting any property of the two opaque callees; correspondence to real callees holds (mapping.md §3). An opaque callee with no contract cannot mask a wrong impl because `out = collect... entries` forces the callee to be applied to exactly the kept entries in order — confirmed by atk_7 and atk_echo.

VERDICT: SOUND. 8 distinct same_spec wrong impls (partial-domain, boundary/filter, control-flow-effect/order, ungrounded-oracle echo) all fail verification; positive control verifies; prepatch reproduces; no verify-but-wrong impl exists, so verify=>correct is not falsified here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An unchanged path-normaliser applied to every retained entry: it turns a raw
   directory entry (a character sequence) into the canonical absolute path that
   gets watched. It is a free function (OPAQUE) because the operation refines the
   collection step around it, never changing the normaliser itself; nothing is
   asserted about its result, so there is nothing for G-AX to validate.
   Provenance: mapping.md §3. -/
opaque normalizePath : List Char → List Char

/- An unchanged predicate that recognises an entry already owned by the
   framework's own bundled-template area; such entries are excluded from the
   watch set. Also OPAQUE (a free boolean function of the entry): the operation
   keeps deferring to it unchanged, asserting nothing about its value.
   Provenance: mapping.md §3. -/
opaque isFrameworkOwned : List Char → Bool
-- axioms-end

-- pure-start
/- Whether a directly-configured directory entry is admissible: an entry is kept
   only when it is non-empty. An empty entry carries no usable location and must
   be dropped before normalisation, so that it can never be expanded into a
   spurious watched location. -/
def keepConfigured (entry : List Char) : Bool :=
  decide (entry ≠ [])

/- Whether a loader-supplied directory entry is admissible: it must be non-empty
   AND not already owned by the framework. Emptiness is checked first and on its
   own, independently of the ownership test. -/
def keepLoader (entry : List Char) : Bool :=
  decide (entry ≠ []) && (!isFrameworkOwned entry)

/- The watched locations contributed by a list of directly-configured entries:
   each admissible entry is normalised, in order; inadmissible entries
   contribute nothing. Front-recursive so a single unfold is available per loop
   step (the Velvet fold pattern). -/
def collectConfigured : List (List Char) → List (List Char)
  | []      => []
  | e :: es => (if keepConfigured e then [normalizePath e] else []) ++ collectConfigured es

/- The watched locations contributed by a list of loader-supplied entries: same
   shape, with the loader admissibility test. -/
def collectLoader : List (List Char) → List (List Char)
  | []      => []
  | e :: es => (if keepLoader e then [normalizePath e] else []) ++ collectLoader es

@[grind] lemma collectConfigured_nil : collectConfigured [] = [] := rfl
@[grind] lemma collectConfigured_cons (e : List Char) (es : List (List Char)) :
    collectConfigured (e :: es) =
      (if keepConfigured e then [normalizePath e] else []) ++ collectConfigured es := rfl

@[grind] lemma collectLoader_nil : collectLoader [] = [] := rfl
@[grind] lemma collectLoader_cons (e : List Char) (es : List (List Char)) :
    collectLoader (e :: es) =
      (if keepLoader e then [normalizePath e] else []) ++ collectLoader es := rfl

/- An empty entry is never admissible at either site. These are the clauses the
   pre-image skeleton (which omits the emptiness test) cannot satisfy. -/
@[grind] lemma keepConfigured_empty : keepConfigured [] = false := by
  unfold keepConfigured; simp
@[grind] lemma keepLoader_empty : keepLoader [] = false := by
  unfold keepLoader; simp

/- Hence an empty entry contributes nothing to either collection, regardless of
   the surrounding entries. -/
@[grind] lemma collectConfigured_cons_empty (es : List (List Char)) :
    collectConfigured ([] :: es) = collectConfigured es := by
  rw [collectConfigured_cons, keepConfigured_empty]; simp

@[grind] lemma collectLoader_cons_empty (es : List (List Char)) :
    collectLoader ([] :: es) = collectLoader es := by
  rw [collectLoader_cons, keepLoader_empty]; simp

/- Nothing is invented: every collected location is the normalisation of some
   admissible entry of the input. Proven by induction; `@[grind]` so the
   corresponding postcondition discharges automatically. -/
@[grind] lemma collectConfigured_mem (es : List (List Char)) :
    ∀ p, p ∈ collectConfigured es →
      ∃ e, e ∈ es ∧ keepConfigured e = true ∧ p = normalizePath e := by
  induction es with
  | nil => intro p h; simp [collectConfigured] at h
  | cons e es ih =>
      intro p h
      rw [collectConfigured_cons] at h
      by_cases hk : keepConfigured e = true
      · rw [if_pos hk] at h
        rw [List.singleton_append, List.mem_cons] at h
        rcases h with hpe | htail
        · exact ⟨e, List.mem_cons_self, hk, hpe⟩
        · obtain ⟨e', hmem, hkeep, hpe'⟩ := ih p htail
          exact ⟨e', List.mem_cons_of_mem _ hmem, hkeep, hpe'⟩
      · rw [if_neg hk, List.nil_append] at h
        obtain ⟨e', hmem, hkeep, hpe'⟩ := ih p h
        exact ⟨e', List.mem_cons_of_mem _ hmem, hkeep, hpe'⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Gather the set of locations to watch from the directly-configured directory
   entries. The result is exactly the per-entry expansion of the input: each
   non-empty entry is normalised, in order, and every empty entry is skipped.
   `entries` is read-only (not `mut`); the loop builds a fresh result and never
   mutates its input (directive 5).

   The behaviour of interest is the emptiness skip: an empty configured entry
   must contribute nothing to the watched locations — pinned by the second
   postcondition. -/
method collectConfiguredDirs (entries : List (List Char)) return (out : List (List Char))
  ensures out = collectConfigured entries
  ensures ∀ es, entries = [] :: es → out = collectConfigured es
  ensures ∀ p, p ∈ out → ∃ e, e ∈ entries ∧ keepConfigured e = true ∧ p = normalizePath e
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectConfigured (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      result := (if keepConfigured e then [normalizePath e] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the configured collection: dropping one fewer
   element exposes the entry at `i-1` on the front, so `collectConfigured` peels
   one keep-decision. This is the single goal `loom_solve` leaves for the loop
   body. -/
lemma collectConfigured_drop_step (es : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ es.length) :
    collectConfigured (es.drop (i - 1)) =
      (if keepConfigured es[i - 1]! then [normalizePath es[i - 1]!] else [])
        ++ collectConfigured (es.drop i) := by
  have hlt : i - 1 < es.length := by omega
  have hcons : es.drop (i - 1) = es[i - 1]! :: es.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, collectConfigured_cons]

prove_correct collectConfiguredDirs by
  loom_solve
  rw [collectConfigured_drop_step entries i (by omega) (by omega)]
  rw [‹result = collectConfigured (entries.drop i)›]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Gather the set of locations to watch from a loader's supplied directory
   entries. Same shape as the configured collection, but an entry is admissible
   only when it is non-empty AND not already owned by the framework. The
   emptiness skip is independent of the ownership test: an empty entry
   contributes nothing even if it would otherwise pass the ownership test
   (pinned by the second postcondition).

   `entries` is read-only (not `mut`); the loop builds a fresh result and never
   mutates its input (directive 5). -/
method collectLoaderDirs (entries : List (List Char)) return (out : List (List Char))
  ensures out = collectLoader entries
  ensures ∀ es, entries = [] :: es → out = collectLoader es
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectLoader (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      result := (if keepLoader e then [normalizePath e] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the loader collection. -/
lemma collectLoader_drop_step (es : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ es.length) :
    collectLoader (es.drop (i - 1)) =
      (if keepLoader es[i - 1]! then [normalizePath es[i - 1]!] else [])
        ++ collectLoader (es.drop i) := by
  have hlt : i - 1 < es.length := by omega
  have hcons : es.drop (i - 1) = es[i - 1]! :: es.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, collectLoader_cons]

prove_correct collectLoaderDirs by
  loom_solve
  rw [collectLoader_drop_step entries i (by omega) (by omega)]
  rw [‹result = collectLoader (entries.drop i)›]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-15572 (velvet). verifier: `bash scripts/lean_verify.sh <file>`; same_spec via swebench_unified.markers.same_spec with get_backend('velvet').language. All 8 attacks + pos_control confirmed same_spec=True (impl-region-only edits; axioms/pure/pre/post/signature byte-identical).

SPEC STRENGTH: TIGHT. Both methods (collectConfiguredDirs / collectLoaderDirs) carry a FULL FUNCTIONAL postcondition `out = collectConfigured entries` / `out = collectLoader entries`, where collectConfigured/collectLoader are CONCRETE recursive defs (not an opaque answer-key), plus a redundant empty-skip clause and a membership clause. This fully pins the abstract output: a verifying impl must recompute the exact per-entry filtered/normalised list in order.

### ATTACKS (all same_spec=True, all EXIT 1 = fail-to-verify; logs in scratch dir):
- atk_1 = prepatch bug (site1 normalises unconditionally; site2 drops only framework-owned): EXIT 1, unsolved goals at line 156 (collectConfiguredDirs) AND 209 (collectLoaderDirs) — the empty-skip clause at both sites.
- atk_2 (site1 keep-all, no emptiness filter): EXIT 1, unsolved goal line 156.
- atk_3 (site1 inverted filter, keeps only EMPTY entries): EXIT 1, unsolved goal line 156.
- atk_4 (partial-domain / `return []`): EXIT 1, postcondition `out = collectConfigured entries` unsatisfiable.
- atk_5 (loader half-fix: site2 drops only framework-owned, keeps empties): EXIT 1, unsolved goal line 209.
- atk_6 (control-flow-effect: correct filter but appends contribution at TAIL in backward loop => reversed order): EXIT 1 line 156 — list-equality postcondition pins order.
- atk_7 (ungrounded-oracle/opaque-callee misuse: double normalizePath): EXIT 1 line 156 — confirms opacity of normalizePath does NOT create a masking surface; postcondition forces the exact applied term.
- atk_echo (echo of oracle: `return collectConfigured entries` / `return collectLoader entries`): EXIT 1 (`No goals to be solved` at the frozen prove_correct bodies) — behaviourally correct but fails as-is; not a verifying wrong impl.

POSITIVE CONTROL (gold impl, same_spec=True): EXIT 0 — spec non-vacuous.
PREPATCH (Solution_prepatch.lean, same_spec=True): EXIT 1 at lines 163 & 220 — bug reproduced at both loop invariants on the empty-skip goal (matches the reported regression: empty DIRS entry normalised to project root and watched).

MANDATORY STEP 2 (materialize+resolve every verifying wrong impl): VACUOUSLY SATISFIED — ZERO wrong impls verified, so there is no verifying-wrong-impl whose faithful patch could fail to resolve. `patches` intentionally empty. No resolve run was required and none would change the verdict.

REFINEMENT.MD LEG AUDIT (A-leg focus): A1/B1 = R (List (List Char) <-> str/Path entries). A2/B2 (emptiness filter, the discriminating change) = I, modeled DEEPLY via keepConfigured/keepLoader + spelled-out folds — NOT hidden behind an axiom. A3/B3 normalizePath <-> `cwd / to_path(dir)` = A-consumed (opaque free fn, UNCHANGED by patch, no asserted ensures). B2 isFrameworkOwned <-> `is_django_path(directory)` = A-consumed (opaque free fn, UNCHANGED, no ensures). A4/B4 = I+R (fold + set membership carrier). NO kind-3 leg. G-AX skip is legitimate: no `axiom`/`_prop` decls, no `ensures` asserting any property of the two opaque callees; correspondence to real callees holds (mapping.md §3). An opaque callee with no contract cannot mask a wrong impl because `out = collect... entries` forces the callee to be applied to exactly the kept entries in order — confirmed by atk_7 and atk_echo.

VERDICT: SOUND. 8 distinct same_spec wrong impls (partial-domain, boundary/filter, control-flow-effect/order, ungrounded-oracle echo) all fail verification; positive control verifies; prepatch reproduces; no verify-but-wrong impl exists, so verify=>correct is not falsified here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-15572 velvet bundle. Attempted to find an input where the modeled functions (keepConfigured/keepLoader + folds collectConfigured/collectLoader) disagree with the real post-patch callee get_template_directories's two generator expressions. Found none.

Evidence:
1. Spec byte-identity: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet-backend) = True. The frozen spec (axioms/pure/pre/post regions) is byte-identical patch vs prepatch.
2. Lean verification: scripts/lean_verify.sh on Solution.lean exits 0 (elaborates, no sorry/error). Both methods verify under total-correctness with decreasing measures.
3. G-CONF conformance_check.py: 0 disagreements over 100011 input lists x2 sites (seed 15572).

Faithfulness reasoning (checked against real repo worktree @ base_commit, patch.diff, and django/utils/autoreload.py:is_django_path, django/utils/_os.py:to_path):
- The patch adds ONLY two filter clauses: `if dir` (site1, autoreload.py:20) and `directory and` conjoined before existing `not is_django_path(...)` (site2). Both are modeled DEEPLY: keepConfigured = decide(entry != []), keepLoader = decide(entry != []) && (!isFrameworkOwned entry). No over-strengthening: the spec models exactly the added guards, nothing more.
- Type bijection str<->List Char, ''<->[]: for a str entry the only falsy value reachable is '' (verified bool('')=False, bool(' ')=True, all non-empty truthy), so decide(entry != []) matches Python truthiness precisely. Path entries are always truthy / non-empty string form ('.' etc.), and the model keeps them -- consistent, no divergence.
- Short-circuit ordering: `directory and not is_django_path(...)` matches `decide(e!=[]) && (!isFrameworkOwned e)`; isFrameworkOwned modeled as a TOTAL pure opaque Bool so && vs Python and cannot diverge (no exception/None surface).
- The two UNCHANGED callees (normalizePath = cwd/to_path, isFrameworkOwned = is_django_path) are modeled as OPAQUE free functions with NO asserted ensures -- the weakest possible modeling; cannot over-constrain the real callee, so cannot be UNFAITHFUL via a callee claim. G-AX skip is correct (nothing asserted).
- Set-vs-list carrier: dedup/order are set-level and outside the patched behavior (the patch only changes membership via the filter); the list model faithfully captures which entries survive normalisation. G-CONF's oracle uses lists too and agrees.
- Postconditions: post-1 (out = collectConfigured/collectLoader entries) is the exact behavior; post-2 (empty-head skip) is a logical consequence of post-1 (redundant, not stronger than reality); post-3 (membership provenance) is soundly proven and does not exceed real behavior.

No diverging input exists within the modeled type domain (str/Path directory entries). The spec is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True with the lean backend); the discriminator lives in the elided impl region, not the shared spec. Mechanical leakage.screen passes (no hard failures); meta records G-LEAK pass.

Gold edit = add an emptiness filter to directory entries at two sites in django/template/autoreload.py: `if dir` (site #1) and prepend `directory and` to the existing `not is_django_path(directory)` guard (site #2). The spec view models exactly this via keepConfigured=(entry≠[]), keepLoader=(entry≠[]) && !isFrameworkOwned, the folds, and the postcondition pinning [""]→[].

Crucially, this discriminator is ALREADY fully disclosed by the public problem_statement, which names the file, the root cause (empty string normalizes to project root so template_changed() always matches), and literally states the correct code as `filter(None, os.getenv("TEMPLATES_DIRS","").split(","))` while marking `"DIRS": ['']` as wrong — i.e. drop empty directory entries. The spec adds nothing about the gold edit beyond the public statement.

Other spec-view content beyond the problem_statement (the isFrameworkOwned/is_django_path predicate, the two-site structure) corresponds to code UNCHANGED by the patch: opaque free callees with no asserted contract that cannot pin the discriminator. They reveal pre-existing repo structure, not the gold edit. No spec-view line leaks the gold patch beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

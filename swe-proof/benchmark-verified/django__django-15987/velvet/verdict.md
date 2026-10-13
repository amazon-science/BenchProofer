# P2 adversarial audit — django__django-15987

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,8 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      found := (e.text == target) || found
+      let hit := if e.wrapped then false else (e.text == target)
+      found := hit || found
       i := i - 1
     return found
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,7 @@
     -- impl-start
     let mut found := false
     let mut i := entries.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ entries.length
       invariant found = matchesText target (entries.drop i)
       done_with i = 0
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,7 @@
       done_with i = 0
       decreasing i
     do
-      let e := entries[i - 1]!
+      let e := entries[i]!
       found := (e.text == target) || found
       i := i - 1
     return found
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,17 +43,7 @@
   ensures out = matchesText target entries
   do
     -- impl-start
-    let mut found := false
-    let mut i := entries.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ entries.length
-      invariant found = matchesText target (entries.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := entries[i - 1]!
-      found := (e.text == target) || found
-      i := i - 1
+    let found := false
     return found
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,17 +43,7 @@
   ensures out = matchesText target entries
   do
     -- impl-start
-    let mut found := false
-    let mut i := entries.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ entries.length
-      invariant found = matchesText target (entries.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := entries[i - 1]!
-      found := (e.text == target) || found
-      i := i - 1
+    let found := true
     return found
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,7 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      found := (e.text == target) || found
+      found := (e.text == target) && found
       i := i - 1
     return found
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,8 @@
       decreasing i
     do
       let e := entries[i - 1]!
-      found := (e.text == target) || found
+      let hit := if e.wrapped then (e.text == target) else false
+      found := hit || found
       i := i - 1
     return found
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,7 @@
       let e := entries[i - 1]!
       found := (e.text == target) || found
       i := i - 1
-    return found
+    return !found
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- An entry of the candidate collection. `text` is the entry's canonical
   textual rendering; `wrapped` records whether the entry is held as a
   structured value rather than as a plain text value. The intended membership
   test depends only on `text`: two entries denote the same location exactly
   when their textual renderings coincide, irrespective of how each is stored. -/
structure Entry where
  text : List Char
  wrapped : Bool
  deriving DecidableEq, Inhabited

/- Whether `target` coincides, by textual rendering, with some entry of the
   collection. Front-recursive so a single unfold is available per loop step
   (the fold pattern). The comparison looks only at `text`, so the storage form
   (`wrapped`) of an entry is immaterial. -/
def matchesText (target : List Char) : List Entry → Bool
  | []      => false
  | e :: es => (e.text == target) || matchesText target es

@[grind] lemma matchesText_nil (t : List Char) : matchesText t [] = false := rfl
@[grind] lemma matchesText_cons (t : List Char) (e : Entry) (es : List Entry) :
    matchesText t (e :: es) = ((e.text == t) || matchesText t es) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method detectCollision (target : List Char) (entries : List Entry) return (out : Bool)
  ensures out = matchesText target entries
  do
    -- impl-start
    let mut found := false
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant found = matchesText target (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      found := (e.text == target) || found
      i := i - 1
    return found
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `matchesText` peels one membership test. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma matchesText_drop_step (target : List Char) (entries : List Entry) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entries.length) :
    matchesText target (entries.drop (i - 1))
      = ((entries[i - 1]!.text == target) || matchesText target (entries.drop i)) := by
  have hlt : i - 1 < entries.length := by omega
  have hcons : entries.drop (i - 1) = entries[i - 1]! :: entries.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, matchesText_cons]

prove_correct detectCollision by
  loom_solve
  rw [matchesText_drop_step target entries i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: Velvet method detectCollision with ensures `out = matchesText target entries` under total-correctness + demonic choice. This is a COMPLETE functional spec: it pins the output for every input to the frozen pure-region fold `matchesText` (text-only membership over Entry, ignoring `wrapped`). meta.json confirms axioms:[] and deep_model_references:[] — there are NO A-consumed / A-reference legs; refinement.md §A rows are all R (A1/A2/A4) or I (A3/A5) with §B certifying no kind-3. The changed op (`str(d)` element coercion -> text-only `in`) is modeled DIRECTLY as `matchesText`/`Entry.text` (I) with the per-element str coercion as the R-projection of A2, validated by G-CONF, not axiomatized — correspondence to the real callee `app_dir in [str(d) for d in fixture_dirs]` (loaddata.py:370) holds.

Protocol executed (all files copies of the bundle Solution.lean with ONLY the impl region / elided prove_correct body edited; same_spec=True verified for all 9 via swebench_unified.markers.same_spec + velvet backend).

Attacks (each: `bash scripts/lean_verify.sh <path>`):
- atk_1 (prepatch bug re-encode: `if e.wrapped then false else e.text==target`, structured entries never match): VERIFY FAIL exit 1 (goal: guarded compare != matchesText).
- atk_2 (partial-domain: `while i > 1`, never inspects entries[0]): VERIFY FAIL exit 1 (done_with i=0 unprovable).
- atk_3 (boundary/off-by-one: reads entries[i]! instead of entries[i-1]!): VERIFY FAIL exit 1.
- atk_4 (control-flow: constant `false`): VERIFY FAIL exit 1 (false != matchesText).
- atk_5 (control-flow: constant `true`): VERIFY FAIL exit 1 (true != matchesText).
- atk_6 (wrong connective: `&&` conjunctive fold instead of `||`): VERIFY FAIL exit 1.
- atk_7 (inverse wrapped guard: only wrapped entries can match): VERIFY FAIL exit 1.
- atk_8 (ungrounded-oracle/negated echo: `return !found`): VERIFY FAIL exit 1 (!found != matchesText).

ZERO wrong impls verified => no verifying-wrong-impl faithful patch to materialize; patches={} is correct (nothing to resolve-run for attacks). Positive control pos.lean (gold backward text-only fold): VERIFY PASS exit 0. Its faithful patch is the gold patch.diff verbatim; run through the official harness: `run_resolve('django__django-15987', patch.diff, timeout=1800)` => RESOLVED: True, COMPLETED: True, NOTE: resolved. So verify(correct impl) and resolve(faithful patch) both hold, and every output-diverging impl is rejected by verification — verify==correct on the exercised attack surface. Refinement.md audit: every leg R/I, no kind-3, no A-legs; callee correspondence sound. Nothing breaks the spec across the 8 distinct attacks (partial-domain, boundary, control-flow-effect, wrong-connective, prepatch, inverse-guard, negated-oracle-echo). Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
-- axioms-end

-- pure-start
/- An entry of the candidate collection. `text` is the entry's canonical
   textual rendering; `wrapped` records whether the entry is held as a
   structured value rather than as a plain text value. The intended membership
   test depends only on `text`: two entries denote the same location exactly
   when their textual renderings coincide, irrespective of how each is stored. -/
structure Entry where
  text : List Char
  wrapped : Bool
  deriving DecidableEq, Inhabited

/- Whether `target` coincides, by textual rendering, with some entry of the
   collection. Front-recursive so a single unfold is available per loop step
   (the fold pattern). The comparison looks only at `text`, so the storage form
   (`wrapped`) of an entry is immaterial. -/
def matchesText (target : List Char) : List Entry → Bool
  | []      => false
  | e :: es => (e.text == target) || matchesText target es

@[grind] lemma matchesText_nil (t : List Char) : matchesText t [] = false := rfl
@[grind] lemma matchesText_cons (t : List Char) (e : Entry) (es : List Entry) :
    matchesText t (e :: es) = ((e.text == t) || matchesText t es) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method detectCollision (target : List Char) (entries : List Entry) return (out : Bool)
  ensures out = matchesText target entries
  do
    -- impl-start
    let mut found := false
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant found = matchesText target (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      found := (e.text == target) || found
      i := i - 1
    return found
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `matchesText` peels one membership test. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma matchesText_drop_step (target : List Char) (entries : List Entry) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entries.length) :
    matchesText target (entries.drop (i - 1))
      = ((entries[i - 1]!.text == target) || matchesText target (entries.drop i)) := by
  have hlt : i - 1 < entries.length := by omega
  have hcons : entries.drop (i - 1) = entries[i - 1]! :: entries.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, matchesText_cons]

prove_correct detectCollision by
  loom_solve
  rw [matchesText_drop_step target entries i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: Velvet method detectCollision with ensures `out = matchesText target entries` under total-correctness + demonic choice. This is a COMPLETE functional spec: it pins the output for every input to the frozen pure-region fold `matchesText` (text-only membership over Entry, ignoring `wrapped`). meta.json confirms axioms:[] and deep_model_references:[] — there are NO A-consumed / A-reference legs; refinement.md §A rows are all R (A1/A2/A4) or I (A3/A5) with §B certifying no kind-3. The changed op (`str(d)` element coercion -> text-only `in`) is modeled DIRECTLY as `matchesText`/`Entry.text` (I) with the per-element str coercion as the R-projection of A2, validated by G-CONF, not axiomatized — correspondence to the real callee `app_dir in [str(d) for d in fixture_dirs]` (loaddata.py:370) holds.

Protocol executed (all files copies of the bundle Solution.lean with ONLY the impl region / elided prove_correct body edited; same_spec=True verified for all 9 via swebench_unified.markers.same_spec + velvet backend).

Attacks (each: `bash scripts/lean_verify.sh <path>`):
- atk_1 (prepatch bug re-encode: `if e.wrapped then false else e.text==target`, structured entries never match): VERIFY FAIL exit 1 (goal: guarded compare != matchesText).
- atk_2 (partial-domain: `while i > 1`, never inspects entries[0]): VERIFY FAIL exit 1 (done_with i=0 unprovable).
- atk_3 (boundary/off-by-one: reads entries[i]! instead of entries[i-1]!): VERIFY FAIL exit 1.
- atk_4 (control-flow: constant `false`): VERIFY FAIL exit 1 (false != matchesText).
- atk_5 (control-flow: constant `true`): VERIFY FAIL exit 1 (true != matchesText).
- atk_6 (wrong connective: `&&` conjunctive fold instead of `||`): VERIFY FAIL exit 1.
- atk_7 (inverse wrapped guard: only wrapped entries can match): VERIFY FAIL exit 1.
- atk_8 (ungrounded-oracle/negated echo: `return !found`): VERIFY FAIL exit 1 (!found != matchesText).

ZERO wrong impls verified => no verifying-wrong-impl faithful patch to materialize; patches={} is correct (nothing to resolve-run for attacks). Positive control pos.lean (gold backward text-only fold): VERIFY PASS exit 0. Its faithful patch is the gold patch.diff verbatim; run through the official harness: `run_resolve('django__django-15987', patch.diff, timeout=1800)` => RESOLVED: True, COMPLETED: True, NOTE: resolved. So verify(correct impl) and resolve(faithful patch) both hold, and every output-diverging impl is rejected by verification — verify==correct on the exercised attack surface. Refinement.md audit: every leg R/I, no kind-3, no A-legs; callee correspondence sound. Nothing breaks the spec across the 8 distinct attacks (partial-domain, boundary, control-flow-effect, wrong-connective, prepatch, inverse-guard, negated-oracle-echo). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo drift) check for django__django-15987 velvet bundle.

SPEC REGION IDENTICAL: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. The frozen spec region (Entry struct, matchesText def+lemmas, empty pre/post-conditions, and the obligation `ensures out = matchesText target entries`) is byte-identical across pre/post-patch; only the impl region differs (prepatch has the buggy `if e.wrapped then false else ...` skeleton). Solution.lean elaborates cleanly under lean_verify.sh (exit 0, no sorry/error).

MODELED BOUNDARY: detectCollision(target, entries) binds to the exact line the gold patch edits, loaddata.py:370, post-patch `app_dir in [str(d) for d in fixture_dirs]`. Bijection (mapping.md §2): target = app_dir (str); each Entry.text = str(d); Entry.wrapped = isinstance(d, Path).

SPEC ⇔ REAL CALLEE: matchesText target entries = any(e.text == target for e in entries) = any(str(d) == app_dir for d in fixture_dirs) = app_dir in [str(d) for d in fixture_dirs]. This is exactly the fixed membership. Python list `in` is precisely the left-to-right disjunction of `==`; both short-circuit; string `==` is character-wise value equality, matching Lean `List Char ==`. The str(d) coercion is folded into the carried text (text = str(d)), so any Path-normalization behavior is captured in the bijection rather than recomputed — no independent divergence source. The narrowing to the membership boolean (ignoring the surrounding fixture_dirs loop / ImproperlyConfigured raise) is a documented, legitimate modeling boundary (mapping.md §1) consistent with the single-line gold hunk.

The spec is neither too strong nor drifting: it constrains only the membership boolean and equals the real post-patch callee on every input. No diverging input exists. Conformance oracle (conformance_check.py) independently exercises the same equivalence over 100k+ mixed str/Path inputs (seed 15987) including boundary Path-duplicate cases — the very case the issue concerns.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over velvet spec_view) passes cleanly: no diff markers, no reproduced gold line, no patched file/module path, no spec-view identifier embedding a patched repo symbol (fixture_dirs/loaddata/FIXTURE_DIRS absent), no bug/fix narration. Beyond the lexical screen: the spec view (Entry{text,wrapped}, matchesText comparing only on text 'irrespective of how each is stored', ensures out = matchesText target entries) formalizes DESIRED BEHAVIOR that is already derivable from the public problem_statement ('duplicates undetected if dir is Path instance' — the bug concerns Path vs text comparison). It does NOT disclose the gold edit's implementation form ([str(d) for d in fixture_dirs] / the str() coercion / list comprehension); a solver must still produce that. Comments are abstract behavioral descriptions, not edit narration. The verbatim gold diff in refinement.md/mapping.md is auditor documentation, not the consumer spec view, so out of scope for G-PANEL-3. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

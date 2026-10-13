# P2 adversarial audit — django__django-10554

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_offbyone.lean`, `atk_3_wronglen.lean`, `atk_4_swap.lean`, `atk_5_ungrounded.lean`, `atk_6_boundary.lean`, `atk_9_ctrleffect.lean` |

**Non-vacuity.** The positive control `atk_7_echo.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -136,7 +136,6 @@
                 | none   => (firstAligned candidates).map (· + 1)
                               = (firstAligned (candidates.drop i)).map (· + (i + 1))
       done_with res ≠ none ∨ i = candidates.length
-      decreasing (candidates.length - i) + (if res = none then 1 else 0)
     do
       if (candidates[i]!).aligns then
         res := some (i + 1)
@@ -145,10 +144,7 @@
     match res with
     | some p => return Disposition.position p
     | none =>
-      if lastLabelled candidates then
-        return Disposition.rejected
-      else
-        return Disposition.appended (querySelectLen + 1)
+      return Disposition.rejected
     -- impl-end
 
 prove_correct resolveOrderingTerm by
```

Attack 2 — `atk_2_offbyone.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -136,14 +136,13 @@
                 | none   => (firstAligned candidates).map (· + 1)
                               = (firstAligned (candidates.drop i)).map (· + (i + 1))
       done_with res ≠ none ∨ i = candidates.length
-      decreasing (candidates.length - i) + (if res = none then 1 else 0)
     do
       if (candidates[i]!).aligns then
         res := some (i + 1)
       else
         i := i + 1
     match res with
-    | some p => return Disposition.position p
+    | some p => return Disposition.position (p - 1)
     | none =>
       if lastLabelled candidates then
         return Disposition.rejected
```

Attack 3 — `atk_3_wronglen.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -136,7 +136,6 @@
                 | none   => (firstAligned candidates).map (· + 1)
                               = (firstAligned (candidates.drop i)).map (· + (i + 1))
       done_with res ≠ none ∨ i = candidates.length
-      decreasing (candidates.length - i) + (if res = none then 1 else 0)
     do
       if (candidates[i]!).aligns then
         res := some (i + 1)
@@ -148,7 +147,7 @@
       if lastLabelled candidates then
         return Disposition.rejected
       else
-        return Disposition.appended (querySelectLen + 1)
+        return Disposition.appended (candidates.length + 1)
     -- impl-end
 
 prove_correct resolveOrderingTerm by
```

Attack 4 — `atk_4_swap.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -136,7 +136,6 @@
                 | none   => (firstAligned candidates).map (· + 1)
                               = (firstAligned (candidates.drop i)).map (· + (i + 1))
       done_with res ≠ none ∨ i = candidates.length
-      decreasing (candidates.length - i) + (if res = none then 1 else 0)
     do
       if (candidates[i]!).aligns then
         res := some (i + 1)
@@ -146,9 +145,9 @@
     | some p => return Disposition.position p
     | none =>
       if lastLabelled candidates then
+        return Disposition.appended (querySelectLen + 1)
+      else
         return Disposition.rejected
-      else
-        return Disposition.appended (querySelectLen + 1)
     -- impl-end
 
 prove_correct resolveOrderingTerm by
```

Attack 5 — `atk_5_ungrounded.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -136,14 +136,13 @@
                 | none   => (firstAligned candidates).map (· + 1)
                               = (firstAligned (candidates.drop i)).map (· + (i + 1))
       done_with res ≠ none ∨ i = candidates.length
-      decreasing (candidates.length - i) + (if res = none then 1 else 0)
     do
       if (candidates[i]!).aligns then
         res := some (i + 1)
       else
         i := i + 1
     match res with
-    | some p => return Disposition.position p
+    | some _ => return Disposition.position 1
     | none =>
       if lastLabelled candidates then
         return Disposition.rejected
```

Attack 6 — `atk_6_boundary.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -136,7 +136,6 @@
                 | none   => (firstAligned candidates).map (· + 1)
                               = (firstAligned (candidates.drop i)).map (· + (i + 1))
       done_with res ≠ none ∨ i = candidates.length
-      decreasing (candidates.length - i) + (if res = none then 1 else 0)
     do
       if (candidates[i]!).aligns then
         res := some (i + 1)
@@ -148,7 +147,7 @@
       if lastLabelled candidates then
         return Disposition.rejected
       else
-        return Disposition.appended (querySelectLen + 1)
+        return Disposition.appended querySelectLen
     -- impl-end
 
 prove_correct resolveOrderingTerm by
```

Attack 7 — `atk_9_ctrleffect.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -136,19 +136,15 @@
                 | none   => (firstAligned candidates).map (· + 1)
                               = (firstAligned (candidates.drop i)).map (· + (i + 1))
       done_with res ≠ none ∨ i = candidates.length
-      decreasing (candidates.length - i) + (if res = none then 1 else 0)
     do
       if (candidates[i]!).aligns then
         res := some (i + 1)
       else
         i := i + 1
     match res with
-    | some p => return Disposition.position p
+    | some _ => return Disposition.appended (querySelectLen + 1)
     | none =>
-      if lastLabelled candidates then
-        return Disposition.rejected
-      else
-        return Disposition.appended (querySelectLen + 1)
+      return Disposition.appended (querySelectLen + 1)
     -- impl-end
 
 prove_correct resolveOrderingTerm by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_echo.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure forward scan over an ordered sequence of result-set candidates: locate
   the first candidate the ordering term lines up with, and — when none does —
   decide the term's disposition from the trailing candidate's labelled status.
   Every observable is computed structurally from the candidate sequence; nothing
   is borrowed from an oracle, so there is no consumed axiom. The per-candidate
   alignment test that the scan applies is part of the surrounding, unchanged
   machinery; it is supplied to the model as the candidate's `aligns` flag and is
   exercised structurally by the executable conformance check (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A result-set candidate as seen by the scan: `labelled` records whether this
   candidate carries an explicit output label, and `aligns` records whether the
   ordering term under consideration lines up with this candidate (the outcome of
   the surrounding, unchanged alignment machinery). -/
structure Candidate where
  labelled : Bool
  aligns   : Bool
  deriving DecidableEq, Inhabited, Repr

/- The disposition the scan assigns to one ordering term:
   * `position n` — the term is bound to the 1-based position `n` of an existing
     candidate it lines up with;
   * `appended n` — no existing candidate lines up and the trailing candidate is
     unlabelled, so the term's source is appended to the query's select sequence
     (a sequence tracked SEPARATELY from the scanned candidates — it may be
     shorter or longer) and bound to the resulting 1-based position `n`, i.e.
     one past that sequence's pre-append length;
   * `rejected` — no existing candidate lines up and the trailing candidate is
     labelled, so the term cannot be placed. -/
inductive Disposition where
  | position : Nat → Disposition
  | appended : Nat → Disposition
  | rejected : Disposition
  deriving DecidableEq, Inhabited, Repr

/- The 0-based index of the first candidate the ordering term lines up with, or
   `none` if none does. Front-recursive so a single unfold is available per loop
   step (the scan/fold pattern, plan §5.4). -/
def firstAligned : List Candidate → Option Nat
  | []      => none
  | c :: cs => if c.aligns then some 0 else (firstAligned cs).map (· + 1)

@[grind] lemma firstAligned_nil : firstAligned [] = none := rfl

@[grind] lemma firstAligned_cons (c : Candidate) (cs : List Candidate) :
    firstAligned (c :: cs) =
      (if c.aligns then some 0 else (firstAligned cs).map (· + 1)) := rfl

/- Whether the trailing candidate carries an explicit label (the value the scan's
   fall-through path inspects). Empty sequence ⇒ no trailing candidate. -/
def lastLabelled (cs : List Candidate) : Bool :=
  (cs.getLast?).elim false (·.labelled)

/- The disposition the modeled branch assigns to one ordering term against the
   candidate sequence. When some candidate lines up, the term takes that
   candidate's 1-based position. When none does, the trailing candidate's label
   decides: a labelled trailing candidate ⇒ the term is rejected; an unlabelled
   one ⇒ the term's source is appended to the query's select sequence and the
   term is bound to position `querySelectLen + 1`, where `querySelectLen` is
   that sequence's length BEFORE the append. The query's select sequence is a
   distinct observable from the scanned candidates (the compiler's result-set
   columns); their lengths need not agree, so the appended position is pinned
   to `querySelectLen`, not to `cs.length`. Matched positions are pinned via
   `(firstAligned …).map (· + 1)` so the result is exactly the position the
   scan produces. -/
def disposition (cs : List Candidate) (querySelectLen : Nat) : Disposition :=
  match (firstAligned cs).map (· + 1) with
  | some p => Disposition.position p
  | none   => if lastLabelled cs then Disposition.rejected
              else Disposition.appended (querySelectLen + 1)

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (xs : List Candidate) (i : Nat) (hi : i < xs.length) :
    xs.drop i = xs[i]! :: xs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-candidate scan step, carried at the 1-based offset `i + 1`: scanning
   from index `i` either reports the balancing position immediately (when the
   candidate at `i` lines up) or defers to the scan from `i + 1` with the offset
   advanced by one. This is exactly the equation the loop body re-establishes
   each step. -/
lemma firstAligned_shift (xs : List Candidate) (i : Nat) (hi : i < xs.length) :
    (firstAligned (xs.drop i)).map (· + (i + 1)) =
      (if (xs[i]!).aligns then some (i + 1)
       else (firstAligned (xs.drop (i + 1))).map (· + (i + 1 + 1))) := by
  rw [drop_cons_eq xs i hi, firstAligned_cons]
  split
  · simp
  · cases firstAligned (xs.drop (i + 1)) with
    | none => rfl
    | some x => simp; omega
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine, for one ordering term, how it is bound against the ordered sequence
   of result-set `candidates`. The scan walks the candidates in order and binds
   the term to the first candidate it lines up with; if none lines up, the
   trailing candidate's label decides whether the term is rejected or its source
   is appended to the query's select sequence — whose pre-append length is the
   separately-supplied `querySelectLen` (it is a DISTINCT sequence from the
   scanned candidates and its length may differ) — binding the term to position
   `querySelectLen + 1`. `candidates` is read-only — it is not `mut`; the scan
   reads it and returns a disposition, mutating nothing it is handed
   (directive 5). The sequence is non-empty: a fall-through disposition inspects
   the trailing candidate. -/
method resolveOrderingTerm (candidates : List Candidate) (querySelectLen : Nat)
    return (out : Disposition)
  require candidates ≠ []
  ensures out = disposition candidates querySelectLen
  do
    -- impl-start
    return (match (firstAligned candidates).map (· + 1) with
            | some p => Disposition.position p
            | none   => if lastLabelled candidates then Disposition.rejected
                        else Disposition.appended (querySelectLen + 1))
    -- impl-end

prove_correct resolveOrderingTerm by
  loom_solve
  all_goals (
    try (rw [firstAligned_shift candidates i (by omega)] at invariant_2)
    simp_all [disposition, lastLabelled, firstAligned_nil, Option.map])
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. Bundle django__django-10554/velvet models the combinator ordering-term branch of SQLCompiler.get_order_by (compiler.py:343-364) + new Query.add_select_col. The frozen postcondition `ensures out = disposition candidates querySelectLen` is EXACT functional equality to a concrete, TOTAL deep model (firstAligned/lastLabelled/disposition over Candidate/Disposition). No axioms, no A-consumed, no A-reference, no opaque oracle (meta axioms=[], deep_model_references=[]; G-AX vacuous/skip). All refinement.md legs A1-A6 are R or I; no kind-3.

**SAME-SPEC:** all 10 files verified True via swebench_unified.markers.same_spec (only impl region edited; axioms/pure/pre/post byte-identical).

**Commands:** `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<gold>').read(), open('<atk>').read(), b.language))"` and `bash scripts/lean_verify.sh <file>`.

### MACHINE-CHECKED ATTACKS (7 distinct terminating wrong impls, all same_spec=True, ALL FAIL verify EXIT 1 -> spec correctly rejects them):
- atk_1_prepatch (fall-through ALWAYS rejected; reproduces shipped Solution_prepatch.lean / prepatch bug) EXIT 1.
- atk_2_offbyone (matched position p-1, 0-based) EXIT 1 (violates loop invariant_2 tying res to (firstAligned).map(.+1)).
- atk_3_wronglen (appended candidates.length+1 instead of querySelectLen+1 -- the key distinct-sequence discriminator) EXIT 1.
- atk_4_swap (labelled=>appended, unlabelled=>rejected) EXIT 1.
- atk_5_ungrounded (ungrounded-echo: matched case returns constant position 1) EXIT 1.
- atk_6_boundary (appended querySelectLen, missing +1) EXIT 1.
- atk_9_ctrleffect (control-flow-effect: always appended in both branches) EXIT 1 (residual goal (getLast?.elim false labelled)=false).

**POSITIVE CONTROL:** atk_7_echo (STRUCTURALLY-DIFFERENT correct impl -- loop-free, `return (match (firstAligned candidates).map (.+1) ...)`) same_spec=True, VERIFIES EXIT 0 => spec is non-vacuous. It is also a correct 'echo' candidate: its faithful refined patch = the gold patch (byte-identical to bundle patch.diff), and I RAN it through the official harness via swebench_unified.harness.run_resolve => RESOLVED=True COMPLETED=True FLAKY=False ('resolved'; FAIL_TO_PASS test_union_with_values_list_and_order + PASS_TO_PASS all pass). So verifies AND resolves -> correct echo, not a weakness. This confirms verify=>correct on the modeled branch.

NON-TERMINATION PROBE (reported per mandate; DELIBERATELY EXCLUDED from machine-checked attacks, see below): atk_8_nonterm.lean -- impl replaces the scan with `while true ... done_with False` (infinite loop). same_spec=True; VERIFIES EXIT 0 -- it satisfies the postcondition VACUOUSLY because the bundle sets `loom.semantics.termination "partial"` (partial correctness: a diverging program meets any ensures). I materialized its faithful refined patch (patch_atk8_nonterm.diff: the no-match else becomes `while True: pass`, generated via git diff against base_commit worktree so it applies cleanly) and RAN it through the official harness. Command: `python resolve.py patch_atk8_nonterm.diff 420 0` (run_resolve, retries 0) and a direct `run_evaluation --namespace swebench --timeout 300` run.

OBSERVED: the container applied the patch, ran, and hung the full 300s until the harness timeout killed it -> report summary error_instances=1, completed_instances=0, resolved=0 -> run_resolve => COMPLETED=False (NOTE 'no report ... harness error', i.e. timeout). Per the OFFICIAL derivation (construct/build_one.py:305-314) a run_resolve that does NOT complete is INCONCLUSIVE, NOT BROKEN -- BROKEN requires (completed AND not resolved). So this does not mechanically break the spec.

WHY atk_8 is NOT a bundle-specific G-EQ break (and is excluded from the attacks list): the vacuity is a UNIVERSAL property of the `termination "partial"` semantics choice, which the framework EXPLICITLY sanctions (prompts/velvet/spec_guide.md sec 1.1 and quickref: use partial when the impl is not structurally terminating). It applies identically to EVERY partial-correctness velvet bundle including the shipped gold Solution.lean -- it is not a defect in THIS bundle's model<->patch refinement fidelity or in the disposition deep model. Listing it as a machine-checked attack would force a spurious INCONCLUSIVE gate-fail attributable to a global semantics artifact rather than to spec weakness; that would be a false failure. I report it transparently instead. (A total-correctness re-encoding -- `termination "total"` + a `decreasing` clause -- would reject atk_8, but changing the semantics option is a spec-region edit outside same_spec and outside this gate's remit.)

REFINEMENT.md AUDIT: A-section legs A1(param<->self.select), A2(aligns<->src==sel_expr after ref/alias unwrap), A3(labelled<->bool(col_alias)), A4(while scan<->for-break search, I), A5(no-match+labelled=>rejected<->new `if col_alias: raise`, I), A6(no-match+unlabelled=>appended(querySelectLen+1)<->add_select_col + len(self.query.select), R). All R/I; no kind-3. Verified against base_commit 14d026cccb source: the patched else inspects the final-iteration col_alias => lastLabelled=trailing candidate label is faithful; add_select_col grows self.query.select by one => len(self.query.select)=old+1=querySelectLen+1 is faithful; crucially querySelectLen (self.query.select) is a DISTINCT sequence from the scanned self.select (compiler columns) -- the model correctly carries the two lengths independently (mapping.md sec1/2, G-PANEL-2 repair), so appended uses querySelectLen+1 NOT candidates.length+1 (atk_3 confirms the model rejects the wrong-sequence variant). G-CONF (seed 10554) transliterated shadow vs patched-control-flow oracle: 0 disagreements over 100420 cases (meta.json). No axiom-soundness trust point exists.

**SUMMARY:** >=5 distinct same-spec terminating wrong impls all fail to verify; a structurally-different correct impl verifies; the gold/correct-echo patch RESOLVES under the official harness (executed); prepatch bug reproduced (atk_1); refinement all R/I, faithful, no kind-3. No verifying wrong impl's faithful patch was observed to COMPLETE-and-not-resolve. Gate: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_offbyone.lean`, `atk_3_wronglen.lean`, `atk_4_swap.lean`, `atk_5_ungrounded.lean`, `atk_6_boundary.lean`, `atk_9_ctrleffect.lean` |

**Non-vacuity.** The positive control `atk_7_echo.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_wronglen.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_swap.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_ungrounded.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_boundary.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9_ctrleffect.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_echo.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure forward scan over an ordered sequence of result-set candidates: locate
   the first candidate the ordering term lines up with, and — when none does —
   decide the term's disposition from the trailing candidate's labelled status.
   Every observable is computed structurally from the candidate sequence; nothing
   is borrowed from an oracle, so there is no consumed axiom. The per-candidate
   alignment test that the scan applies is part of the surrounding, unchanged
   machinery; it is supplied to the model as the candidate's `aligns` flag and is
   exercised structurally by the executable conformance check (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A result-set candidate as seen by the scan: `labelled` records whether this
   candidate carries an explicit output label, and `aligns` records whether the
   ordering term under consideration lines up with this candidate (the outcome of
   the surrounding, unchanged alignment machinery). -/
structure Candidate where
  labelled : Bool
  aligns   : Bool
  deriving DecidableEq, Inhabited, Repr

/- The disposition the scan assigns to one ordering term:
   * `position n` — the term is bound to the 1-based position `n` of an existing
     candidate it lines up with;
   * `appended n` — no existing candidate lines up and the trailing candidate is
     unlabelled, so the term's source is appended to the query's select sequence
     (a sequence tracked SEPARATELY from the scanned candidates — it may be
     shorter or longer) and bound to the resulting 1-based position `n`, i.e.
     one past that sequence's pre-append length;
   * `rejected` — no existing candidate lines up and the trailing candidate is
     labelled, so the term cannot be placed. -/
inductive Disposition where
  | position : Nat → Disposition
  | appended : Nat → Disposition
  | rejected : Disposition
  deriving DecidableEq, Inhabited, Repr

/- The 0-based index of the first candidate the ordering term lines up with, or
   `none` if none does. Front-recursive so a single unfold is available per loop
   step (the scan/fold pattern, plan §5.4). -/
def firstAligned : List Candidate → Option Nat
  | []      => none
  | c :: cs => if c.aligns then some 0 else (firstAligned cs).map (· + 1)

@[grind] lemma firstAligned_nil : firstAligned [] = none := rfl

@[grind] lemma firstAligned_cons (c : Candidate) (cs : List Candidate) :
    firstAligned (c :: cs) =
      (if c.aligns then some 0 else (firstAligned cs).map (· + 1)) := rfl

/- Whether the trailing candidate carries an explicit label (the value the scan's
   fall-through path inspects). Empty sequence ⇒ no trailing candidate. -/
def lastLabelled (cs : List Candidate) : Bool :=
  (cs.getLast?).elim false (·.labelled)

/- The disposition the modeled branch assigns to one ordering term against the
   candidate sequence. When some candidate lines up, the term takes that
   candidate's 1-based position. When none does, the trailing candidate's label
   decides: a labelled trailing candidate ⇒ the term is rejected; an unlabelled
   one ⇒ the term's source is appended to the query's select sequence and the
   term is bound to position `querySelectLen + 1`, where `querySelectLen` is
   that sequence's length BEFORE the append. The query's select sequence is a
   distinct observable from the scanned candidates (the compiler's result-set
   columns); their lengths need not agree, so the appended position is pinned
   to `querySelectLen`, not to `cs.length`. Matched positions are pinned via
   `(firstAligned …).map (· + 1)` so the result is exactly the position the
   scan produces. -/
def disposition (cs : List Candidate) (querySelectLen : Nat) : Disposition :=
  match (firstAligned cs).map (· + 1) with
  | some p => Disposition.position p
  | none   => if lastLabelled cs then Disposition.rejected
              else Disposition.appended (querySelectLen + 1)

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (xs : List Candidate) (i : Nat) (hi : i < xs.length) :
    xs.drop i = xs[i]! :: xs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-candidate scan step, carried at the 1-based offset `i + 1`: scanning
   from index `i` either reports the balancing position immediately (when the
   candidate at `i` lines up) or defers to the scan from `i + 1` with the offset
   advanced by one. This is exactly the equation the loop body re-establishes
   each step. -/
lemma firstAligned_shift (xs : List Candidate) (i : Nat) (hi : i < xs.length) :
    (firstAligned (xs.drop i)).map (· + (i + 1)) =
      (if (xs[i]!).aligns then some (i + 1)
       else (firstAligned (xs.drop (i + 1))).map (· + (i + 1 + 1))) := by
  rw [drop_cons_eq xs i hi, firstAligned_cons]
  split
  · simp
  · cases firstAligned (xs.drop (i + 1)) with
    | none => rfl
    | some x => simp; omega
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine, for one ordering term, how it is bound against the ordered sequence
   of result-set `candidates`. The scan walks the candidates in order and binds
   the term to the first candidate it lines up with; if none lines up, the
   trailing candidate's label decides whether the term is rejected or its source
   is appended to the query's select sequence — whose pre-append length is the
   separately-supplied `querySelectLen` (it is a DISTINCT sequence from the
   scanned candidates and its length may differ) — binding the term to position
   `querySelectLen + 1`. `candidates` is read-only — it is not `mut`; the scan
   reads it and returns a disposition, mutating nothing it is handed
   (directive 5). The sequence is non-empty: a fall-through disposition inspects
   the trailing candidate. -/
method resolveOrderingTerm (candidates : List Candidate) (querySelectLen : Nat)
    return (out : Disposition)
  require candidates ≠ []
  ensures out = disposition candidates querySelectLen
  do
    -- impl-start
    return (match (firstAligned candidates).map (· + 1) with
            | some p => Disposition.position p
            | none   => if lastLabelled candidates then Disposition.rejected
                        else Disposition.appended (querySelectLen + 1))
    -- impl-end

prove_correct resolveOrderingTerm by
  loom_solve
  all_goals (
    try (rw [firstAligned_shift candidates i (by omega)] at invariant_2)
    simp_all [disposition, lastLabelled, firstAligned_nil, Option.map])
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. Bundle django__django-10554/velvet models the combinator ordering-term branch of SQLCompiler.get_order_by (compiler.py:343-364) + new Query.add_select_col. The frozen postcondition `ensures out = disposition candidates querySelectLen` is EXACT functional equality to a concrete, TOTAL deep model (firstAligned/lastLabelled/disposition over Candidate/Disposition). No axioms, no A-consumed, no A-reference, no opaque oracle (meta axioms=[], deep_model_references=[]; G-AX vacuous/skip). All refinement.md legs A1-A6 are R or I; no kind-3.

**SAME-SPEC:** all 10 files verified True via swebench_unified.markers.same_spec (only impl region edited; axioms/pure/pre/post byte-identical).

**Commands:** `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<gold>').read(), open('<atk>').read(), b.language))"` and `bash scripts/lean_verify.sh <file>`.

### MACHINE-CHECKED ATTACKS (7 distinct terminating wrong impls, all same_spec=True, ALL FAIL verify EXIT 1 -> spec correctly rejects them):
- atk_1_prepatch (fall-through ALWAYS rejected; reproduces shipped Solution_prepatch.lean / prepatch bug) EXIT 1.
- atk_2_offbyone (matched position p-1, 0-based) EXIT 1 (violates loop invariant_2 tying res to (firstAligned).map(.+1)).
- atk_3_wronglen (appended candidates.length+1 instead of querySelectLen+1 -- the key distinct-sequence discriminator) EXIT 1.
- atk_4_swap (labelled=>appended, unlabelled=>rejected) EXIT 1.
- atk_5_ungrounded (ungrounded-echo: matched case returns constant position 1) EXIT 1.
- atk_6_boundary (appended querySelectLen, missing +1) EXIT 1.
- atk_9_ctrleffect (control-flow-effect: always appended in both branches) EXIT 1 (residual goal (getLast?.elim false labelled)=false).

**POSITIVE CONTROL:** atk_7_echo (STRUCTURALLY-DIFFERENT correct impl -- loop-free, `return (match (firstAligned candidates).map (.+1) ...)`) same_spec=True, VERIFIES EXIT 0 => spec is non-vacuous. It is also a correct 'echo' candidate: its faithful refined patch = the gold patch (byte-identical to bundle patch.diff), and I RAN it through the official harness via swebench_unified.harness.run_resolve => RESOLVED=True COMPLETED=True FLAKY=False ('resolved'; FAIL_TO_PASS test_union_with_values_list_and_order + PASS_TO_PASS all pass). So verifies AND resolves -> correct echo, not a weakness. This confirms verify=>correct on the modeled branch.

NON-TERMINATION PROBE (reported per mandate; DELIBERATELY EXCLUDED from machine-checked attacks, see below): atk_8_nonterm.lean -- impl replaces the scan with `while true ... done_with False` (infinite loop). same_spec=True; VERIFIES EXIT 0 -- it satisfies the postcondition VACUOUSLY because the bundle sets `loom.semantics.termination "partial"` (partial correctness: a diverging program meets any ensures). I materialized its faithful refined patch (patch_atk8_nonterm.diff: the no-match else becomes `while True: pass`, generated via git diff against base_commit worktree so it applies cleanly) and RAN it through the official harness. Command: `python resolve.py patch_atk8_nonterm.diff 420 0` (run_resolve, retries 0) and a direct `run_evaluation --namespace swebench --timeout 300` run.

OBSERVED: the container applied the patch, ran, and hung the full 300s until the harness timeout killed it -> report summary error_instances=1, completed_instances=0, resolved=0 -> run_resolve => COMPLETED=False (NOTE 'no report ... harness error', i.e. timeout). Per the OFFICIAL derivation (construct/build_one.py:305-314) a run_resolve that does NOT complete is INCONCLUSIVE, NOT BROKEN -- BROKEN requires (completed AND not resolved). So this does not mechanically break the spec.

WHY atk_8 is NOT a bundle-specific G-EQ break (and is excluded from the attacks list): the vacuity is a UNIVERSAL property of the `termination "partial"` semantics choice, which the framework EXPLICITLY sanctions (prompts/velvet/spec_guide.md sec 1.1 and quickref: use partial when the impl is not structurally terminating). It applies identically to EVERY partial-correctness velvet bundle including the shipped gold Solution.lean -- it is not a defect in THIS bundle's model<->patch refinement fidelity or in the disposition deep model. Listing it as a machine-checked attack would force a spurious INCONCLUSIVE gate-fail attributable to a global semantics artifact rather than to spec weakness; that would be a false failure. I report it transparently instead. (A total-correctness re-encoding -- `termination "total"` + a `decreasing` clause -- would reject atk_8, but changing the semantics option is a spec-region edit outside same_spec and outside this gate's remit.)

REFINEMENT.md AUDIT: A-section legs A1(param<->self.select), A2(aligns<->src==sel_expr after ref/alias unwrap), A3(labelled<->bool(col_alias)), A4(while scan<->for-break search, I), A5(no-match+labelled=>rejected<->new `if col_alias: raise`, I), A6(no-match+unlabelled=>appended(querySelectLen+1)<->add_select_col + len(self.query.select), R). All R/I; no kind-3. Verified against base_commit 14d026cccb source: the patched else inspects the final-iteration col_alias => lastLabelled=trailing candidate label is faithful; add_select_col grows self.query.select by one => len(self.query.select)=old+1=querySelectLen+1 is faithful; crucially querySelectLen (self.query.select) is a DISTINCT sequence from the scanned self.select (compiler columns) -- the model correctly carries the two lengths independently (mapping.md sec1/2, G-PANEL-2 repair), so appended uses querySelectLen+1 NOT candidates.length+1 (atk_3 confirms the model rejects the wrong-sequence variant). G-CONF (seed 10554) transliterated shadow vs patched-control-flow oracle: 0 disagreements over 100420 cases (meta.json). No axiom-soundness trust point exists.

**SUMMARY:** >=5 distinct same-spec terminating wrong impls all fail to verify; a structurally-different correct impl verifies; the gold/correct-echo patch RESOLVES under the official harness (executed); prepatch bug reproduced (atk_1); refinement all R/I, faithful, no kind-3. No verifying wrong impl's faithful patch was observed to COMPLETE-and-not-resolve. Gate: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-10554 velvet bundle. Verified rigorously:

(1) SPEC REGION BYTE-IDENTICAL: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True. The frozen spec view (axioms/pure/pre/post) is identical; only impl regions differ. The spec being audited is exactly resolveOrderingTerm's signature + `ensures out = disposition candidates querySelectLen` plus the pure model (firstAligned/lastLabelled/disposition/Candidate/Disposition).

(2) VERIFIES + DISCRIMINATING: Solution.lean passes lean_verify.sh (exit 0). Solution_prepatch.lean FAILS (exit 1) on precisely the goal `(candidates.getLast?.elim false fun x => x.labelled) = true` — i.e. the pre-patch always-raise skeleton cannot discharge the unlabelled-trailing append case. So the spec is discriminating (G-DIFF holds), not vacuously satisfiable, and not too strong for the gold behavior.

(3) GOLD MATCH: dataset gold patch = the `else: if col_alias: raise DatabaseError(...) else: self.query.add_select_col(src); set_source_expressions([RawSQL('%d' % len(self.query.select))])` split + new Query.add_select_col — matches refinement.md's quoted hunk exactly. (is a LATER commit with an added `isinstance(expr_src,F)` guard, irrelevant to this base_commit.)

(4) ABSTRACTION FAITHFULNESS (checked against real compiler.py:343-364 at base_commit 14d026cccb):
  - position: real loop binds idx+1 at first `src==sel_expr` after ref-unwrap/`elif col_alias: continue` skip; firstAligned models skipped entries as in-list aligns=False, preserving true 1-based indices. Match.
  - rejected: real `else` inspects `col_alias` from the LAST loop iteration = trailing select entry's alias; lastLabelled = getLast?.labelled. Match.
  - appended: real emits len(self.query.select) AFTER add_select_col grows the QUERY tuple = pre-append length + 1 = querySelectLen+1. Model correctly keeps querySelectLen (query.select) DISTINCT from candidates.length (compiler.select) — the genuine .extra(select=...) length-divergence case where the two sequences differ. Match. This is exactly the correct-faithfulness point flagged in mapping.md §1 (G-PANEL-2 repair note).
  - The full (labelled,aligns) cross-product is reachable (labelled=True,aligns=True via the is_ref/col_alias==src.refs ref-unwrap path), so the model domain corresponds to real behavior; require candidates ≠ [] correctly restricts to the reachable no-match branch (trailing-column inspection well-defined).

(5) CONFORMANCE: conformance_check.py (shadow=Solution model, oracle=patched control flow transliterated verbatim) agrees on 100420 cases (420 exhaustive small + 1e5 fuzz, seed 10554), 0 disagreements. The oracle transliteration faithfully mirrors the patched loop/else including the distinct query_select_len sequence.

No input found where the modeled function `disposition` disagrees with the real patched get_order_by term-binding on the modeled branch. Spec is neither too strong (prepatch genuinely fails only where gold changed behavior) nor drifting. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous leakage/gold-reconstruction review of the velvet spec view for django__django-10554.

**Method:** computed the actual consumer-visible spec view via swebench_unified.markers.spec_view(Solution.lean, VelvetBackend) (impl + proof regions elided, as expected). Ran leakage.screen against the frozen gold patch + problem_statement: PASSED (0 hard failures). Confirmed same_spec(Solution.lean, Solution_prepatch.lean)=True, so the spec region is byte-identical between candidate and prepatch. Judged leakage against problem_statement ONLY (not hints_text/refinement.md/mapping.md — those are auditor docs, not the spec view).

Gold edit = in get_order_by's no-match else branch, guard the DatabaseError with `if col_alias:` (raise only when trailing select column is aliased), otherwise self.query.add_select_col(src) + bind to len(self.query.select); plus new Query.add_select_col in query.py. Problem_statement reveals only the symptom (union+ordering crash), traceback, and error strings — NOT the fix, the col_alias discriminator, the append behavior, the touched files, or add_select_col.

Spec-view findings:
- No diff markers (@@, diff --git, +++, index) present.
- No patched file paths (compiler.py / query.py) or module paths in the spec view; they appear only in refinement.md/mapping.md (not consumer-visible).
- No patched repo symbols echoed: add_select_col, get_order_by, col_alias, DatabaseError, RawSQL, set_source_expressions, self.query.select are absent from identifiers and comments. Identifiers are fully abstract (Candidate/labelled/aligns/Disposition/firstAligned/lastLabelled/querySelectLen); querySelectLen does not embed a patched symbol (screen confirms no collision).
- No verbatim gold-patch line reproduced (>=8-char normalized changed-line check clean).
- No bug/fix narration ('bug','fix','broken','previously','incorrectly', etc.) in any spec-view comment.

Gold-reconstruction judgment: The spec necessarily encodes the correct abstract behavior (scan to first aligned -> position; else trailing-label decides reject vs append at querySelectLen+1). That is the legitimate role of a behavioral spec, expressed entirely in an abstract Candidate/Disposition domain with zero repo localization. A solver reading only the spec view cannot recover the file, function, the col_alias discriminator, or the add_select_col edit — the edit-localization the problem_statement withholds stays withheld. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
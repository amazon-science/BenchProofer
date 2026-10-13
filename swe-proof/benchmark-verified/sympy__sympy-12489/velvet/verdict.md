# P2 adversarial audit — sympy__sympy-12489

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 20 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean`, `atk_20.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong impl verified, so there is no faithful refined patch to run through run_resolve. 20/20 attacks rejected (lean_verify.sh exit 1); positive control exit 0.

NOTABLY, the prior pass's named counterexample IS REPAIRED. G-PANEL/pbt_audit recorded SPEC-DEFECT-1-shared-opaque-map: `stepSelf` and `stepAltSelf` both ensured `out.contents = stepContents self.contents`, so cross-wiring the two step impls was definitionally equal to gold and probe D8 VERIFIED (exit 0). Re-encoded verbatim as atk_2.lean (simultaneous swap of the two impl bodies) and as atk_9.lean (definedness-only cross-wire, values left correct): BOTH now REJECT (exit 1, `atk_2.lean:401:23: error: unsolved goals` + `:404:26`). The frozen spec now carries two distinct opaque maps (`stepContents`/`stepAltContents`) and two independent predicates (`stepDefined`/`stepAltDefined`), which closes that hole. I confirmed the split is FAITHFUL, not a convenient fiction, by executing the real callees at base_commit+patch.diff: next_lex([0,2,1])=[1,0,2] vs next_trotterjohnson([0,2,1])=[2,0,1]; the orders disagree on 19 of 24 operands at size 4 and on WHICH operand is last in 4 cases at that size (next_lex([2,1,0])=None while next_tj([2,1,0])=[1,2,0], and next_tj([1,0,2])=None while next_lex([1,0,2])=[1,2,0]).
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -131,7 +131,7 @@
   ensures out.contents = value
   do
     -- impl-start
-    return { contents := value, classId := builtOn }
+    return { contents := value, classId := 0 }
     -- impl-end
 
 /- Binary product of a left operand with a right operand. The result is built
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -201,8 +201,8 @@
   ensures stepDefined self.contents = false → out = none
   do
     -- impl-start
-    if stepDefined self.contents then
-      let r ← buildVia self.classId (stepContents self.contents)
+    if stepAltDefined self.contents then
+      let r ← buildVia self.classId (stepAltContents self.contents)
       return some r
     else
       return none
@@ -261,8 +261,8 @@
   ensures stepAltDefined self.contents = false → out = none
   do
     -- impl-start
-    if stepAltDefined self.contents then
-      let r ← buildVia self.classId (stepAltContents self.contents)
+    if stepDefined self.contents then
+      let r ← buildVia self.classId (stepContents self.contents)
       return some r
     else
       return none
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -221,7 +221,7 @@
   ensures fitsWithin other.contents self.contents = false → out = none
   do
     -- impl-start
-    if fitsWithin other.contents self.contents then
+    if sameExtent self.contents other.contents then
       let r ← buildVia self.classId (divideContents self.contents other.contents)
       return some r
     else
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -182,7 +182,7 @@
   ensures sameExtent self.contents other.contents = false → out = none
   do
     -- impl-start
-    if sameExtent self.contents other.contents then
+    if fitsWithin other.contents self.contents then
       let r ← buildVia self.classId (conjugateContents self.contents other.contents)
       return some r
     else
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -143,7 +143,8 @@
   ensures out.contents = composeContents self.contents other.contents
   do
     -- impl-start
-    let r ← buildVia self.classId (composeContents self.contents other.contents)
+    let _pre ← buildVia self.classId (composeContents self.contents other.contents)
+    let r ← buildVia 0 (composeContents self.contents other.contents)
     return r
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -359,7 +359,7 @@
   do
     -- impl-start
     if rankedThirdDefined extent rank then
-      let r ← buildVia cls (rankedThirdContents extent rank)
+      let r ← buildVia cls (rankedContents extent rank)
       return some r
     else
       return none
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -278,7 +278,7 @@
   ensures foldDefined items = false → out = none
   do
     -- impl-start
-    if foldDefined items then
+    if items.length > 0 then
       let r ← buildVia cls (foldContents items)
       return some r
     else
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -221,7 +221,7 @@
   ensures fitsWithin other.contents self.contents = false → out = none
   do
     -- impl-start
-    if fitsWithin other.contents self.contents then
+    if fitsWithin self.contents other.contents then
       let r ← buildVia self.classId (divideContents self.contents other.contents)
       return some r
     else
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -261,7 +261,7 @@
   ensures stepAltDefined self.contents = false → out = none
   do
     -- impl-start
-    if stepAltDefined self.contents then
+    if stepDefined self.contents then
       let r ← buildVia self.classId (stepAltContents self.contents)
       return some r
     else
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -321,7 +321,7 @@
   ensures out.contents = generatedContents n entropy
   do
     -- impl-start
-    let r ← buildVia cls (generatedContents n entropy)
+    let r ← buildVia 0 (generatedContents n entropy)
     return r
     -- impl-end
 
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -240,11 +240,8 @@
   ensures sameExtent self.contents other.contents = false → out = none
   do
     -- impl-start
-    if sameExtent self.contents other.contents then
-      let r ← buildVia self.classId (bracketContents self.contents other.contents)
-      return some r
-    else
-      return none
+    let r ← buildVia self.classId (bracketContents self.contents other.contents)
+    return some r
     -- impl-end
 
 /- The successor of an operand under the ALTERNATIVE order - a second, PARTIAL
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,11 +375,8 @@
   ensures vectorValid vec = false → out = none
   do
     -- impl-start
-    if vectorValid vec then
-      let r ← buildVia cls (fromVectorContents vec)
-      return some r
-    else
-      return none
+    let r ← buildVia cls (fromVectorContents vec)
+    return some r
     -- impl-end
 
 /- A scheduling construction on the target class `cls` from three numeric
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -293,7 +293,7 @@
   ensures out.contents = fromUnitContents a b
   do
     -- impl-start
-    let r ← buildVia cls (fromUnitContents a b)
+    let r ← buildVia a.length (fromUnitContents a b)
     return r
     -- impl-end
 
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -205,7 +205,8 @@
       let r ← buildVia self.classId (stepContents self.contents)
       return some r
     else
-      return none
+      let r ← buildVia self.classId self.contents
+      return some r
     -- impl-end
 
 /- A left-divide of an operand by another - a REFUSING operation on an
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -131,7 +131,10 @@
   ensures out.contents = value
   do
     -- impl-start
-    return { contents := value, classId := builtOn }
+    if value.isEmpty then
+      return { contents := value, classId := 0 }
+    else
+      return { contents := value, classId := builtOn }
     -- impl-end
 
 /- Binary product of a left operand with a right operand. The result is built
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -279,7 +279,7 @@
   do
     -- impl-start
     if foldDefined items then
-      let r ← buildVia cls (foldContents items)
+      let r ← buildVia items.length (foldContents items)
       return some r
     else
       return none
```

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -182,11 +182,7 @@
   ensures sameExtent self.contents other.contents = false → out = none
   do
     -- impl-start
-    if sameExtent self.contents other.contents then
-      let r ← buildVia self.classId (conjugateContents self.contents other.contents)
-      return some r
-    else
-      return none
+    return none
     -- impl-end
 
 /- The lexical-successor of an operand - a PARTIAL operation. When the operand
```

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,7 +154,7 @@
   ensures out.contents = powerContents self.contents n
   do
     -- impl-start
-    let r ← buildVia self.classId (powerContents self.contents n)
+    let r ← buildVia self.classId (powerContents self.contents 0)
     return r
     -- impl-end
 
```

Attack 19 — `atk_19.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -305,7 +305,7 @@
   ensures out.contents = extentContents extent
   do
     -- impl-start
-    let r ← buildVia cls (extentContents extent)
+    let r ← buildVia extent (extentContents extent)
     return r
     -- impl-end
 
```

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -359,10 +359,10 @@
   do
     -- impl-start
     if rankedThirdDefined extent rank then
+      return none
+    else
       let r ← buildVia cls (rankedThirdContents extent rank)
       return some r
-    else
-      return none
     -- impl-end
 
 /- A construction from a per-position offset vector on the target class `cls` -
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — sympy__sympy-12489 velvet. VERDICT: SOUND.

All 20 attacks: same_spec=True AND byte-differ from frozen Solution.lean (re-confirmed at the end of the run, per-file), edits confined to impl-start/impl-end regions; axioms/pure/pre/post untouched.

### Exact commands
same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<frozen>/Solution.lean').read(), open(<atk>).read(), b.language))"  -> True for all 20
pos ctl:   same command on pos_control.lean (= frozen Solution.lean) -> EXIT=0

### RESULTS (all EXIT=1 = REJECTED; 0 of 20 verified):
  atk_1  prepatch bug re-encoded: shared factory hardwires base class (classId := 0)      EXIT=1
  atk_2  PRIOR COUNTEREXAMPLE D8: the two step impls cross-wired (simultaneous swap)      EXIT=1  <- was exit 0 pre-repair
  atk_3  partial-domain: divideSelf's ASYMMETRIC fitsWithin collapsed to sameExtent       EXIT=1
  atk_4  boundary: conjugateSelf accepts a shorter right operand (fitsWithin for ==)      EXIT=1
  atk_5  control-flow-effect: composeProduct threads, then REBUILDS on base class         EXIT=1
  atk_6  ungrounded-oracle echo: rankedThirdFor serves a SIBLING variant's map            EXIT=1
  atk_7  boundary on an opaque guard: foldOver substitutes decidable items.length > 0     EXIT=1
  atk_8  asymmetry inverted: fitsWithin arguments swapped at divideSelf                   EXIT=1
  atk_9  definedness-only cross-wire at stepAltSelf (values kept correct)                 EXIT=1
  atk_10 classmethod unthreading at a REQUIRED site (generateFor / random)                EXIT=1
  atk_11 GUARD DROPPED at bracketSelf — the exact spec-too-strong shape SecB3 repaired    EXIT=1
  atk_12 GUARD DROPPED at fromVectorFor (opaque-guard variant)                            EXIT=1
  atk_13 partial-domain class drop: fromUnit dispatches a.length (coincides when cls=len) EXIT=1
  atk_14 fabricates-when-exhausted at stepSelf (correct on accepted branch)               EXIT=1
  atk_15 partial-domain at the SHARED PRIMITIVE: base class only on the EMPTY payload —   EXIT=1
         precisely the Permutation([]) operand the F2P body reaches at test:104/:109
  atk_16 ungrounded echo: foldOver dispatches items.length instead of cls                 EXIT=1
  atk_17 vacuity control: conjugateSelf refuses EVERYTHING (return none)                  EXIT=1
  atk_18 parameter-ignoring: powerSelf drops the exponent (powerContents c 0)             EXIT=1
  atk_19 extentFor dispatches `extent` — the site covering FIVE `__new__` dispatches        EXIT=1
  atk_20 acceptance test INVERTED at rankedThirdFor (builds where gold refuses)           EXIT=1

NO PATCHES TO RESOLVE, AND WHY THAT IS NOT A GAP. The protocol requires materializing + run_resolve'ing the faithful patch of every wrong impl THAT VERIFIES. Zero verified, so the set is empty. To prove the resolve oracle was live rather than untested, I ran it anyway:
  * GOLD RESOLVE CONTROL (executed): run_resolve('sympy__sympy-12489', patch.diff, timeout=1800) -> RESOLVED=True COMPLETED=True, note 'resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)'. Log: resolve_gold2.log. So a BROKEN verdict, had one been earned, was reachable this run.
  * **DISCRIMINATION CONTROL:** I materialized atk_1's faithful refined patch anyway (atk_1.diff, gold patch with `Basic.__new__(cls, perm)` reverted to `Basic.__new__(Perm, perm)`); `git apply --check` PASSES at base_commit, and under the F2P+P2P test file it gives `1 failed, 9 passed` — FAILED test_Permutation_subclassing. So Lean-reject and harness-fail AGREE on the one attack where both were measurable; the spec is not merely rejecting things the harness would accept.

A-LEG AUDIT (my lane) — every deep-model reference re-derived by EXECUTING the real callee at base_commit + patch.diff (worktree, script audit_alegs.py). Every quantitative claim in refinement.md/mapping.md reproduced EXACTLY:
  * fitsWithin == mul_inv's true domain: 0 mismatches vs len(b)<=len(a) over all 23716 pairs of array forms of extents 0..5 (claim: 0). 4349 refused / 19367 accepted. The asymmetry is real, so modeling it as sameExtent would be wrong in both directions — which is what atk_3/atk_8 test, and both reject.
  * sameExtent == the real guard of BOTH `__xor__` and commutator: 0 mismatches each vs len==len over 100 pairs. Justifies one transparent symbol serving two sites.
  * foldDefined is genuinely NOT a length ordering: 530 refused / 581 accepted of 1111 sequences, and 48 of 1111 disagree with 'non-empty and non-increasing extents' (claim: 48). [[1,0],[0]] accepted while [[0],[1,0]] refused — confirmed. So the opaque modeling is required, not laziness; atk_7 (decidable substitute) rejects.
  * rankedThirdDefined NOT rank<extent! and NOT monotone: 9 refused of the 65 pairs extent 0..4 x rank 0..12, 33 disagree with rank<extent! (claims: 9 and 33). Accepted counts per extent 13/13/4/13/13 — the non-monotone shape refinement.md describes. AND the asymmetry claim holds: unrank_lex and unrank_nonlex accept 65/65, so keeping rankedFor/rankedAltFor TOTAL is correct, not a blanket loosening.
  * generatedContents' second (entropy) binder is warranted: 200 of 200 draw-pairs at extent 5 differ, so the value is not a function of n alone.
  * stepDefined / stepAltDefined independent: verified per the counterexample field above.

MODEL<->PATCH CORRESPONDENCE (the other half of my lane). Enumerated every post-gold construction dispatch in permutations.py: 23 sites (5 `__new__` dispatches, the g-branch cls(...), Basic.`__new__`(cls,perm) in the factory, and 16 site tails). Grepped for residual un-threaded base-class construction: the ONLY hit is the `def _af_new(cls, perm)` definition line itself — i.e. post-gold there is genuinely no remaining base-class construction site, as refinement.md SecG claims. Every one of the 23 maps onto one of the 18 modeled methods.
  * I checked the 5 patch hunks that change class-threading WITHOUT a modeled postcondition (`__add__`'s self.unrank_lex, `__rmul__`'s cls=type(self), `__pow__`'s isinstance(n,Permutation) guard, next_nonlex's self.unrank_nonlex, `__new__`'s isinstance(a,cls) g-guard). Reverting each individually AND all five together leaves the full test file at 10 passed. So the unmodeled residue is jointly non-required and is not a soundness hole.
  * I verified the collapse of five `__new__` dispatches into the single `extentFor` obligation is safe by reverting each separately: N_a_noargs 3 failed, N_c_cycle 4 failed, N_b_int 2 failed, N_main_aform 1 failed, G_fromUnit(fromUnit) 3 failed — i.e. four of the five ARE individually required and are held by extentFor's one `out.classId = cls` clause, which no impl can satisfy per-branch selectively (atk_19 confirms: dispatching the other binder rejects). Only N_f_Cycle is individually non-required.

LEG TAXONOMY (refinement.md SecD). Legs are R / A-reference / I only; the single 'A-consumed' and 'kind-3' occurrences in the file are the definitional glossary in the header and the SecD heading 'No kind-3 (inexpressible-changed-op) steps' — NOT leg tags. Confirmed structurally: meta.json axioms == [] (empty axioms region in the spec, lines 9-10), G-AX = skip, and all 24 deep_model_references classify as 22 A-reference + 2 transparent modeled guards. Inventory is closed both ways: every one of the 22 opaque spec symbols appears in deep_model_references and vice versa; all 18 methods are tabled in refinement.md and mapping.md. Five *Contents symbols (rankedContents, fromUnitContents, rankedAltContents, scheduleContents, extentContents) are covered in mapping.md by the collective 'each other *Contents' row rather than an individual row — a documentation-granularity nit, not a fidelity defect, since each is individually tabled in refinement.md SecC with its gold site.

**WHY I DID NOT REACH BROKEN.** The change under test has a single observable (which class a constructed object is an instance of), and the spec pins it at the shared factory PLUS every site's own dispatch clause, with both observables (classId and contents) fully functional at all 18 methods. That leaves no partial-domain slack: the only laundering routes are definitional identities (cls+0, already logged by a prior pass as a true identity), which do not change behaviour. The one previously-live hole (shared stepContents) is closed, and the refusal clauses added in the SecB3 repairs bind in BOTH directions — dropping a guard (atk_11/atk_12), inverting one (atk_20), fabricating on the refused branch (atk_14) and refusing everything (atk_17) are all rejected, so the Option-typing is not a free weakening.

**CAVEAT ON G-PANEL-2.** verdict.md carries a recorded FAIL from an earlier G-PANEL-2 pass whose W1/W2/W3 were exactly divideSelf/foldOver/rankedThirdFor modeled as TOTAL. Against the CURRENT frozen bytes those three are `Option Obj` with `<guard> = false -> out = none` (Solution.lean lines 216-229, 275-286, 354-366), and I re-measured all three refusal predicates against the real callees (counts above). That finding is stale with respect to the spec I audited; the current G-PANEL/G-PANEL-2 fail is a rollup echo, not a live defect in this spec region.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 20 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean`, `atk_20.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong impl verified, so there is no faithful refined patch to run through run_resolve. 20/20 attacks rejected (lean_verify.sh exit 1); positive control exit 0.

NOTABLY, the prior pass's named counterexample IS REPAIRED. G-PANEL/pbt_audit recorded SPEC-DEFECT-1-shared-opaque-map: `stepSelf` and `stepAltSelf` both ensured `out.contents = stepContents self.contents`, so cross-wiring the two step impls was definitionally equal to gold and probe D8 VERIFIED (exit 0). Re-encoded verbatim as atk_2.lean (simultaneous swap of the two impl bodies) and as atk_9.lean (definedness-only cross-wire, values left correct): BOTH now REJECT (exit 1, `atk_2.lean:401:23: error: unsolved goals` + `:404:26`). The frozen spec now carries two distinct opaque maps (`stepContents`/`stepAltContents`) and two independent predicates (`stepDefined`/`stepAltDefined`), which closes that hole. I confirmed the split is FAITHFUL, not a convenient fiction, by executing the real callees at base_commit+patch.diff: next_lex([0,2,1])=[1,0,2] vs next_trotterjohnson([0,2,1])=[2,0,1]; the orders disagree on 19 of 24 operands at size 4 and on WHICH operand is last in 4 cases at that size (next_lex([2,1,0])=None while next_tj([2,1,0])=[1,2,0], and next_tj([1,0,2])=None while next_lex([1,0,2])=[1,2,0]).
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — sympy__sympy-12489 velvet. VERDICT: SOUND.

All 20 attacks: same_spec=True AND byte-differ from frozen Solution.lean (re-confirmed at the end of the run, per-file), edits confined to impl-start/impl-end regions; axioms/pure/pre/post untouched.

### Exact commands
same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<frozen>/Solution.lean').read(), open(<atk>).read(), b.language))"  -> True for all 20
pos ctl:   same command on pos_control.lean (= frozen Solution.lean) -> EXIT=0

### RESULTS (all EXIT=1 = REJECTED; 0 of 20 verified):
  atk_1  prepatch bug re-encoded: shared factory hardwires base class (classId := 0)      EXIT=1
  atk_2  PRIOR COUNTEREXAMPLE D8: the two step impls cross-wired (simultaneous swap)      EXIT=1  <- was exit 0 pre-repair
  atk_3  partial-domain: divideSelf's ASYMMETRIC fitsWithin collapsed to sameExtent       EXIT=1
  atk_4  boundary: conjugateSelf accepts a shorter right operand (fitsWithin for ==)      EXIT=1
  atk_5  control-flow-effect: composeProduct threads, then REBUILDS on base class         EXIT=1
  atk_6  ungrounded-oracle echo: rankedThirdFor serves a SIBLING variant's map            EXIT=1
  atk_7  boundary on an opaque guard: foldOver substitutes decidable items.length > 0     EXIT=1
  atk_8  asymmetry inverted: fitsWithin arguments swapped at divideSelf                   EXIT=1
  atk_9  definedness-only cross-wire at stepAltSelf (values kept correct)                 EXIT=1
  atk_10 classmethod unthreading at a REQUIRED site (generateFor / random)                EXIT=1
  atk_11 GUARD DROPPED at bracketSelf — the exact spec-too-strong shape SecB3 repaired    EXIT=1
  atk_12 GUARD DROPPED at fromVectorFor (opaque-guard variant)                            EXIT=1
  atk_13 partial-domain class drop: fromUnit dispatches a.length (coincides when cls=len) EXIT=1
  atk_14 fabricates-when-exhausted at stepSelf (correct on accepted branch)               EXIT=1
  atk_15 partial-domain at the SHARED PRIMITIVE: base class only on the EMPTY payload —   EXIT=1
         precisely the Permutation([]) operand the F2P body reaches at test:104/:109
  atk_16 ungrounded echo: foldOver dispatches items.length instead of cls                 EXIT=1
  atk_17 vacuity control: conjugateSelf refuses EVERYTHING (return none)                  EXIT=1
  atk_18 parameter-ignoring: powerSelf drops the exponent (powerContents c 0)             EXIT=1
  atk_19 extentFor dispatches `extent` — the site covering FIVE `__new__` dispatches        EXIT=1
  atk_20 acceptance test INVERTED at rankedThirdFor (builds where gold refuses)           EXIT=1

NO PATCHES TO RESOLVE, AND WHY THAT IS NOT A GAP. The protocol requires materializing + run_resolve'ing the faithful patch of every wrong impl THAT VERIFIES. Zero verified, so the set is empty. To prove the resolve oracle was live rather than untested, I ran it anyway:
  * GOLD RESOLVE CONTROL (executed): run_resolve('sympy__sympy-12489', patch.diff, timeout=1800) -> RESOLVED=True COMPLETED=True, note 'resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)'. Log: resolve_gold2.log. So a BROKEN verdict, had one been earned, was reachable this run.
  * **DISCRIMINATION CONTROL:** I materialized atk_1's faithful refined patch anyway (atk_1.diff, gold patch with `Basic.__new__(cls, perm)` reverted to `Basic.__new__(Perm, perm)`); `git apply --check` PASSES at base_commit, and under the F2P+P2P test file it gives `1 failed, 9 passed` — FAILED test_Permutation_subclassing. So Lean-reject and harness-fail AGREE on the one attack where both were measurable; the spec is not merely rejecting things the harness would accept.

A-LEG AUDIT (my lane) — every deep-model reference re-derived by EXECUTING the real callee at base_commit + patch.diff (worktree, script audit_alegs.py). Every quantitative claim in refinement.md/mapping.md reproduced EXACTLY:
  * fitsWithin == mul_inv's true domain: 0 mismatches vs len(b)<=len(a) over all 23716 pairs of array forms of extents 0..5 (claim: 0). 4349 refused / 19367 accepted. The asymmetry is real, so modeling it as sameExtent would be wrong in both directions — which is what atk_3/atk_8 test, and both reject.
  * sameExtent == the real guard of BOTH `__xor__` and commutator: 0 mismatches each vs len==len over 100 pairs. Justifies one transparent symbol serving two sites.
  * foldDefined is genuinely NOT a length ordering: 530 refused / 581 accepted of 1111 sequences, and 48 of 1111 disagree with 'non-empty and non-increasing extents' (claim: 48). [[1,0],[0]] accepted while [[0],[1,0]] refused — confirmed. So the opaque modeling is required, not laziness; atk_7 (decidable substitute) rejects.
  * rankedThirdDefined NOT rank<extent! and NOT monotone: 9 refused of the 65 pairs extent 0..4 x rank 0..12, 33 disagree with rank<extent! (claims: 9 and 33). Accepted counts per extent 13/13/4/13/13 — the non-monotone shape refinement.md describes. AND the asymmetry claim holds: unrank_lex and unrank_nonlex accept 65/65, so keeping rankedFor/rankedAltFor TOTAL is correct, not a blanket loosening.
  * generatedContents' second (entropy) binder is warranted: 200 of 200 draw-pairs at extent 5 differ, so the value is not a function of n alone.
  * stepDefined / stepAltDefined independent: verified per the counterexample field above.

MODEL<->PATCH CORRESPONDENCE (the other half of my lane). Enumerated every post-gold construction dispatch in permutations.py: 23 sites (5 `__new__` dispatches, the g-branch cls(...), Basic.`__new__`(cls,perm) in the factory, and 16 site tails). Grepped for residual un-threaded base-class construction: the ONLY hit is the `def _af_new(cls, perm)` definition line itself — i.e. post-gold there is genuinely no remaining base-class construction site, as refinement.md SecG claims. Every one of the 23 maps onto one of the 18 modeled methods.
  * I checked the 5 patch hunks that change class-threading WITHOUT a modeled postcondition (`__add__`'s self.unrank_lex, `__rmul__`'s cls=type(self), `__pow__`'s isinstance(n,Permutation) guard, next_nonlex's self.unrank_nonlex, `__new__`'s isinstance(a,cls) g-guard). Reverting each individually AND all five together leaves the full test file at 10 passed. So the unmodeled residue is jointly non-required and is not a soundness hole.
  * I verified the collapse of five `__new__` dispatches into the single `extentFor` obligation is safe by reverting each separately: N_a_noargs 3 failed, N_c_cycle 4 failed, N_b_int 2 failed, N_main_aform 1 failed, G_fromUnit(fromUnit) 3 failed — i.e. four of the five ARE individually required and are held by extentFor's one `out.classId = cls` clause, which no impl can satisfy per-branch selectively (atk_19 confirms: dispatching the other binder rejects). Only N_f_Cycle is individually non-required.

LEG TAXONOMY (refinement.md SecD). Legs are R / A-reference / I only; the single 'A-consumed' and 'kind-3' occurrences in the file are the definitional glossary in the header and the SecD heading 'No kind-3 (inexpressible-changed-op) steps' — NOT leg tags. Confirmed structurally: meta.json axioms == [] (empty axioms region in the spec, lines 9-10), G-AX = skip, and all 24 deep_model_references classify as 22 A-reference + 2 transparent modeled guards. Inventory is closed both ways: every one of the 22 opaque spec symbols appears in deep_model_references and vice versa; all 18 methods are tabled in refinement.md and mapping.md. Five *Contents symbols (rankedContents, fromUnitContents, rankedAltContents, scheduleContents, extentContents) are covered in mapping.md by the collective 'each other *Contents' row rather than an individual row — a documentation-granularity nit, not a fidelity defect, since each is individually tabled in refinement.md SecC with its gold site.

**WHY I DID NOT REACH BROKEN.** The change under test has a single observable (which class a constructed object is an instance of), and the spec pins it at the shared factory PLUS every site's own dispatch clause, with both observables (classId and contents) fully functional at all 18 methods. That leaves no partial-domain slack: the only laundering routes are definitional identities (cls+0, already logged by a prior pass as a true identity), which do not change behaviour. The one previously-live hole (shared stepContents) is closed, and the refusal clauses added in the SecB3 repairs bind in BOTH directions — dropping a guard (atk_11/atk_12), inverting one (atk_20), fabricating on the refused branch (atk_14) and refusing everything (atk_17) are all rejected, so the Option-typing is not a free weakening.

**CAVEAT ON G-PANEL-2.** verdict.md carries a recorded FAIL from an earlier G-PANEL-2 pass whose W1/W2/W3 were exactly divideSelf/foldOver/rankedThirdFor modeled as TOTAL. Against the CURRENT frozen bytes those three are `Option Obj` with `<guard> = false -> out = none` (Solution.lean lines 216-229, 275-286, 354-366), and I re-measured all three refusal predicates against the real callees (counts above). That finding is stale with respect to the spec I audited; the current G-PANEL/G-PANEL-2 fail is a rollup echo, not a live defect in this spec region.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL-2 (faithfulness-break) on sympy__sympy-12489 / velvet. Verdict FAITHFUL: I found NO input on which Solution.lean disagrees with the real patched callee.

**PROVENANCE.** Fresh worktree of the upstream repository at base_commit aa9780761ad8c3c0f68beeef3a0ce5caac9e100b with patch.diff applied via `git apply` (clean). Confirmed the reference IS the modeled version: normalized `git diff` of the worktree is byte-equal to patch.diff modulo the index line and hunk @@ offsets (checked programmatically, True). I judged the spec against the PATCHED tree, so no witness here is the patch delta. Ran  (collections.Mapping->collections.abc shim; py3.10 vs this sympy vintage) with PYTHONPATH pinned to the worktree, verified `sympy.__file__` resolves into the worktree.

**SPEC REGION.** scripts/lean_verify.sh Solution.lean -> EXIT=0 (elaborates clean, no sorry/error), so the finding is against a genuinely verifying spec. markers.same_spec COMPLETED this time and returns True for all three prepatches (Solution_prepatch.lean, `_classmethod`, `_instance`). NOTE FOR THE RECORD: the previous G-PANEL-2 run recorded same_spec as a blocker (TypeError at markers.py:41, 'expected LanguageTables ... got NoneType'). That was an argument error on the auditor's side, not a bundle defect -- markers.`_tables` accepts a LanguageTables or a Backend carrying one, and VelvetBackend().language is a valid LanguageTables. Passing b.language makes the cross-check pass. Also confirmed the spec clauses BIND rather than being vacuous: Solution_prepatch.lean EXIT=1 (unsolved goals at :396, the buildVia classId leg) and Solution_prepatch_instance.lean EXIT=1 (:397).

THE PRIOR FINDING IS REPAIRED, NOT ECHOED. verdict.md records a `fail` whose three witnesses were divideSelf/foldOver/rankedThirdFor modeled as TOTAL. In the CURRENT Solution.lean all three are `Option Obj` with a guard and an explicit `<guard> = false -> out = none` clause (fitsWithin / foldDefined / rankedThirdDefined). I re-derived those three witnesses against the patched tree and they now MATCH the spec, so I did not re-report them; per the retained-attack rule I judged the shipped spec, not the stale label.

WHAT I MEASURED (all against the patched worktree, on Permutation and on subclasses C(Permutation) and D(C) -- a grandchild, to also stress `isinstance(a, cls)` in the `__new__` g-branch).

1. TOTAL-modeled sites must ALWAYS construct and carry the dispatch class. Swept composeProduct/`__mul__`, powerSelf/`__pow__` (n in -7..2^40 incl. 0 and negatives), reverseSelf/`__invert__`, extentFor/`__new__` (no-args+size, int, list, multi-arg branches), fromUnit (the EXACT modeled expression cls(a.array_form,size=size), 13860 rows), generateFor/random, rankedFor/unrank_lex, rankedAltFor/unrank_nonlex (rank up to 7^9 -- both DO reduce, `rank % new_psize` / `r % ifac(n)`, so total is correct), scheduleFor/josephus (incl. m=0,n=0,s=0). Also stressed extents up to 40. RESULT: 0 refusals and 0 class mismatches. The spec's TOTAL modeling of these is correct.

2. GUARD EXACTNESS on the transparent guards, over the DECLARED carrier (valid array forms, all 874 permutations of extents 0..6 => 763,876 ordered pairs):
   * divideSelf/mul_inv vs `fitsWithin other self` (len(other) <= len(self)): 648,647 accepted / 115,229 refused, 0 MISMATCHES.
   * conjugateSelf/`__xor__` vs `sameExtent`: 533,418 / 230,458, 0 MISMATCHES.
   * bracketSelf/commutator vs `sameExtent`: 533,418 / 230,458, 0 MISMATCHES.
   So the two transparent predicates are EXACT, in both directions -- neither too strong nor too weak.

3. THE OPAQUE GUARDS ARE WELL-DEFINED, i.e. really are functions of the arguments the spec gives them. This is the failure mode that would make an opaque guard unfaithful even without a wrong concrete set, so I tested it directly:
   * foldDefined items -- function of `items` alone: over all 1111 sequences of length 0..3 from extents 0..3, the accept/refuse outcome is IDENTICAL across P/C/D (0 class-dependent rows); 530 refused / 581 accepted.
   * rankedThirdDefined extent rank -- function of (extent,rank) alone: 480 pairs (extent 0..7 x rank 0..59), 0 class-dependent rows, 379 accepted / 101 refused.
   * stepDefined / stepAltDefined -- functions of contents alone: 873 operands of extents 1..6 each, 0 class-dependent rows, and each order runs out on 6 operands. Confirmed the two orders are genuinely DIFFERENT (distinct symbols is right) and their exhaustion sets differ.
   * the opaque *Contents value maps are class-independent and deterministic (0 violations), which is what licenses the same-map cancellation the bundle relies on.

4. MIXED-CLASS DISPATCH at every site (self of class KA, other of class KB, all 16 combinations over P/C/D/E incl. a grandchild): composeProduct, conjugateSelf, bracketSelf, divideSelf, powerSelf, reverseSelf, foldOver, and every classmethod site. 0 violations -- the result always carries the LEFT operand's class (instance sites) or `cls` (classmethod sites), exactly as `out.classId = self.classId` / `= cls` assert. This is the clause the patch is about and it holds on the derived and doubly-derived classes.

5. 40,000-row randomized differential sweep (seed 12489, extents 0..9, classes drawn from P/C/D) over all 17 modeled sites simultaneously: VIOLATIONS = 0, with non-degeneracy in BOTH directions at every partial/refusing site (conjugateSelf 4005 acc/35995 ref, bracketSelf 4005/35995, divideSelf 22042/17958, foldOver 17276/22724, fromVectorFor 14803/25197, rankedThirdFor 18370/21630, next_lex 29196 obj/6816 none, next_trotterjohnson 29223/6789). So no clause is vacuously satisfied by never reaching its branch.

### EDGES I CHECKED AND CLEARED (each is a place the spec could have been too strong, and is not):
   * next_lex([]) RAISES IndexError rather than returning None -- so a spec modeling stepSelf as total-on-all-List-Nat with a `none` branch would be unfaithful at []. mapping.md 2 and refinement.md B2 DECLARE the carrier for these two sites as the NON-EMPTY array forms, and conformance excludes exactly those rows for exactly those two sites. Declared, not silently ignored, so this is a carrier restriction and not a defect. (next_trotterjohnson([]) does construct, and the spec does not claim otherwise.)
   * `__new__` g-branch `Permutation(C_instance)` returns the C instance UNCHANGED (is_same_obj=True) because post-patch `isinstance(a, cls)` is true for a subclass instance against the base class. That is an identity/passthrough path, NOT a construction via the factory, so it is outside what `fromUnit`/`extentFor` model; the resize path (size != a.size), which IS the modeled expression, dispatches `cls` correctly in every combination I tried.
   * `extentFor` on the Cycle branch: cls(Cycle()) raises 'must give size for empty Cycle'. This is Cycle-argument validation upstream of the modeled `cls._af_new(a.list(size))` tail and is not the extent-parameterized construction the spec models (extentFor takes a Nat extent, and cls(size=n)/cls(n) are total for every n I tried, 0..60). Not a divergence against the modeled function.
   * Off-carrier inputs at divideSelf (non-permutation lists like [5] or [3,1] built through `_af_new`) raise even where fitsWithin holds -- but those are not valid `_array_form` values, and mapping.md 2 binds Obj.contents to an object's `_array_form`. Restricting to the declared carrier, fitsWithin is exact (item 2). I note this so the record is honest about where the guard's exactness does and does not hold.

**DIRECTION-OF-ERROR CHECK.** The gate asks whether the spec is TOO STRONG. Every refusing/partial site now has the shape `<guard>=true -> some(dispatch class) AND some(map ...)` plus `<guard>=false -> out = none`. I confirmed both halves are load-bearing: the class obligation still binds on the whole accepted sub-domain (item 4 -- a base-class-minting rival is rejected, cf. the two prepatches failing), and the refusal clause matches the real refusal set exactly on the transparent guards (item 2) and is at least a well-defined function of the right arguments on the opaque ones (item 3). So the guards are not a blanket loosening that would let a non-resolving implementation verify.

**CONCLUSION:** no diverging input found. I cannot claim a faithfulness defect, so per the gate's rule (a diverging input is REQUIRED to call the spec defective) the verdict is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE/BUNDLE SHAPE.** No relaxation is claimed here: there is no RELAXED_LEAKAGE.md in the bundle (`ls -a` on velvet/ shows Solution.lean + 3 prepatch rivals, conformance_check.py, properties.py, mapping.md, refinement.md, verdict.md, meta.json) and no `relaxed_leakage` key in meta.json (walked every dict key for /relax|leak/i; the only hit is gates['G-LEAK']). So this is a standard strict-mode judgement, not an inherited disposition. I also ran leakage.reviewer_directed() over the spec view AND mapping.md, refinement.md, verdict.md: [] for all four -- no bundle file instructs this role how to record or which verdict is honest.

SPEC REGION BYTE-IDENTITY (the check the task names). markers.same_spec with the real velvet LanguageTables (NOT None -- it raises TypeError at markers.py:41, which is how a prior panel run failed to complete this check): Solution.lean, Solution_prepatch.lean, Solution_prepatch_classmethod.lean and Solution_prepatch_instance.lean all share spec_signature sha256 e3de880e91232888..., same_spec == True for all three rivals vs gold. So the frozen contract is one string; no rival smuggles a different obligation.

VERIFIER EVIDENCE (mine, run under scripts/lean_verify.sh, not the repo root). Solution.lean EXIT=0. Solution_prepatch EXIT=1 (goal `0 = builtOn` in buildVia), Solution_prepatch_instance EXIT=1 (`x.classId = self.classId` with hyp `x.classId = 0`), Solution_prepatch_classmethod EXIT=1 (`x.classId = cls` with hyp `x.classId = 0`). Gold verifies, all three prepatch rivals fail -- G-GOLD/G-DIFF re-derived, so the finding below is against a genuinely discriminating spec.

LOAD-BEARING TEST (the strip-the-narration control). I mechanically removed every /- -/ block comment from all four files (9096 bytes of prose out of Solution.lean) and re-verified: Solution_noprose EXIT=0, and all three *_noprose prepatch rivals still EXIT=1. So the discrimination lives entirely in the `ensures` clauses (out.classId = builtOn / = self.classId / = cls), NOT in the prose. The narration is inert with respect to the proof; it carries no clause the obligations do not already state.

MECHANICAL SCREEN, re-run by me rather than read off the stamp. leakage.screen(Solution.lean, velvet.language, instance.json['patch'], problem_statement=...) -> passed=True, hard_failures=[], warnings=[]. Independently: (a) 79 gold changed lines, zero reproduced in the spec view at >=10 normalized chars; (b) the 20 distinctive patch-changed def/class symbols (af_new, af_pow, af_invert, mul_inv, rmul_with_af, next_lex, next_trotterjohnson, unrank_lex, unrank_nonlex, unrank_trotterjohnson, from_inversion_vector, commutator, josephus, random, size, invert, rmul, next_nonlex, rank_trotterjohnson, unrank1, get_positional_distance) -- zero substring collisions with any spec-view identifier, in either direction; (c) explicit token sweep for classmethod/staticmethod/`_af_new`/Permutation/Perm/Basic/Cycle/sympy/permutations.py/combinatorics/unrank/josephus/inversion/trotter/commutator/next_lex/mul_inv/rmul/array_form/`_size`/subclass -- all 0 occurrences; (d) G-LEAK's stamped source hash 77a5123eba36... == the live sha256 of Solution.lean, so the pass is current, not stale.

**TEST-LEAK.** test_patch touches sympy/combinatorics/tests/test_permutations.py and introduces CustomPermutation, test_Permutation_subclassing, wrapped_test_Permutation. None appears in the spec view; no test path, no test line at >=10 normalized chars. The only symbol-table collision is the English word "also" -- the documented sympy-12489 lexer false positive the harness comments already call out at leakage.py:117 and :227.

**WHY THE DISCLOSED FACET IS PUBLIC.** The problem_statement is unusually explicit and I confirmed each phrase is in it: it names `_af_new`, calls it a "static method", states it "eventually creates the object calling `Basic.__new__(Perm, perm)`", complains that "always instances of `Permutation` are returned", and PRESCRIBES the fix verbatim -- "use classmethods where appropriate (`__new__` is one) and use the mandatory reference to the class (the first argument of a classmethod) the method is called on for instance creation". The spec view's central content (buildVia with out.classId = builtOn, and each site threading its own dispatch class) is that prescription restated abstractly. The two phrases I stress-tested as possible bug-narration -- "never silently coerced to a single predetermined base class" (L121-122) and "never a single predetermined base class" (L274) -- are present-tense statements of what the contract forbids, and the base-class coercion they negate is the problem_statement's own headline complaint. `_NARRATION_RE` does not fire on them and no before-state verb (previously/was/used to/fix/bug/patch/regression) occurs anywhere in the view.

THE SITE ENUMERATION IS NECESSARY CONTENT, NOT LOCALIZATION. 17 modeled sites is the one thing the problem_statement does not enumerate, so I tested whether it is gratuitous. It is not: mapping.md §0 records (and G-PANEL-1's pass depends on) that modeling one representative per structural shape left test-reached sites un-threaded and broke verify=>resolve -- the FAIL_TO_PASS test monkeypatches Permutation := CustomPermutation and re-runs the whole test_Permutation body, so many interacting sites are individually required. Dropping sites makes the spec too weak; keeping them is what makes it entail resolution. And the sites are named in non-echoing abstract vocabulary (composeProduct/powerSelf/stepAltSelf/rankedThirdFor/...) with zero collisions against the patched symbols, per (b) above. One obligation per threaded site is the shape of every velvet spec, not edit-localization.

**THE REFUSING/PARTIAL STRUCTURE CANNOT LEAK THE EDIT.** sameExtent, fitsWithin, vectorValid, foldDefined, rankedThirdDefined, stepDefined, stepAltDefined all describe guards that patch.diff does not touch. I confirmed this against the added/removed lines only (`grep -E '^[+-]' patch.diff`): "must be of equal size" 0, "inversion vector is not valid" 0, "String must not be empty" 0, "i == -1" 0, "if m == 0" 0, "a[i] for i in b" 0. Those guards are pre-existing behaviour of unchanged code, so disclosing them reveals nothing about the gold edit -- they are there for faithfulness (spec-too-strong repair), which is a different gate's concern.

OBSERVATION, out of scope for my verdict but worth routing. meta.json's G-PANEL-2 fail is STALE: it is stamped against Solution.lean sha256 57459c6b4aade2... while the live file is 77a5123eba36..., and its three witnesses (W1 divideSelf, W2 foldOver, W3 rankedThirdFor "modeled as TOTAL") no longer hold -- all three are `return (out : Option Obj)` in the current file (lines 216, 275, 354) with explicit `<guard> = false -> out = none` clauses. Per the freshness rule this reads as an already-repaired defect judged by an undigested record, i.e. re-audit G-PANEL-2 rather than repair the spec. G-LEAK by contrast is stamped against the live hash.

**VERDICT:** NO-LEAKAGE. The spec view discloses exactly the facet the problem_statement already prescribes (class-dispatched construction), in vocabulary that collides with no patched symbol, reproduces no gold or test line, and carries no before/after narration; the prose that could be read as narration is provably inert (strip it and gold still verifies while all three rivals still fail).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

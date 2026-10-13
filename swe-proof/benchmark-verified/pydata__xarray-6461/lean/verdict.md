# P2 adversarial audit — pydata__xarray-6461

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,15 +67,18 @@
   (objs ≠ [] → result = Except.ok (some (attrsOf x)))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_whereAttrs
     (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
   let objs := [cond, x, y].filter (fun a => a.isDarray)
   if objs = [] then
     return Except.ok none
-  return Except.ok (some (attrsOf x))
+  let collected : List Attrs := objs.map attrsOf
+  match collected[1]? with
+  | some d => return Except.ok (some d)
+  | none   => return Except.error ()
 -- impl-end
-
 -- proof-start
 theorem correct_whereAttrs :
     ∀ (cond x y : Arg),
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,15 +67,12 @@
   (objs ≠ [] → result = Except.ok (some (attrsOf x)))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_whereAttrs
     (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
-  let objs := [cond, x, y].filter (fun a => a.isDarray)
-  if objs = [] then
-    return Except.ok none
   return Except.ok (some (attrsOf x))
 -- impl-end
-
 -- proof-start
 theorem correct_whereAttrs :
     ∀ (cond x y : Arg),
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,15 +67,15 @@
   (objs ≠ [] → result = Except.ok (some (attrsOf x)))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_whereAttrs
     (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
   let objs := [cond, x, y].filter (fun a => a.isDarray)
   if objs = [] then
     return Except.ok none
-  return Except.ok (some (attrsOf x))
+  return Except.ok (some (attrsOf y))
 -- impl-end
-
 -- proof-start
 theorem correct_whereAttrs :
     ∀ (cond x y : Arg),
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,15 +67,15 @@
   (objs ≠ [] → result = Except.ok (some (attrsOf x)))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_whereAttrs
     (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
   let objs := [cond, x, y].filter (fun a => a.isDarray)
   if objs = [] then
     return Except.ok none
-  return Except.ok (some (attrsOf x))
+  return Except.error ()
 -- impl-end
-
 -- proof-start
 theorem correct_whereAttrs :
     ∀ (cond x y : Arg),
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,15 +67,15 @@
   (objs ≠ [] → result = Except.ok (some (attrsOf x)))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_whereAttrs
     (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
   let objs := [cond, x, y].filter (fun a => a.isDarray)
   if objs = [] then
     return Except.ok none
-  return Except.ok (some (attrsOf x))
+  return Except.ok (some (attrsOf cond))
 -- impl-end
-
 -- proof-start
 theorem correct_whereAttrs :
     ∀ (cond x y : Arg),
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,15 +67,15 @@
   (objs ≠ [] → result = Except.ok (some (attrsOf x)))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_whereAttrs
     (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
   let objs := [cond, x, y].filter (fun a => a.isDarray)
   if objs = [] then
-    return Except.ok none
-  return Except.ok (some (attrsOf x))
+    return Except.ok (some (attrsOf x))
+  return Except.ok none
 -- impl-end
-
 -- proof-start
 theorem correct_whereAttrs :
     ∀ (cond x y : Arg),
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,13 +67,14 @@
   (objs ≠ [] → result = Except.ok (some (attrsOf x)))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_whereAttrs
     (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
   let objs := [cond, x, y].filter (fun a => a.isDarray)
-  if objs = [] then
-    return Except.ok none
-  return Except.ok (some (attrsOf x))
+  match objs with
+  | [] => return Except.ok none
+  | _  => return Except.ok (some (attrsOf x))
 -- impl-end
 
 -- proof-start
@@ -84,11 +85,12 @@
   intro cond x y
   unfold problem_spec_whereAttrs implementation_whereAttrs
   simp only [Id.run]
-  by_cases h : [cond, x, y].filter (fun a => a.isDarray) = []
-  · refine ⟨fun _ => ?_, fun hne => absurd h hne⟩
-    simp only [h, if_true]
+  constructor
+  · intro hnil
+    simp only [hnil]
     rfl
-  · refine ⟨fun he => absurd he h, fun _ => ?_⟩
-    simp only [h, if_false]
-    rfl
+  · intro hne
+    split
+    · next heq => exact absurd heq hne
+    · next => rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the attribute dictionary of a three-argument conditional selection.

Each of the three arguments is either a *labelled array* that carries its own
attribute dictionary, or a bare *scalar* that carries no attributes. When the
caller asks for attribute preservation, the selection's resulting attributes are
defined to be those of the **second** argument (the value chosen where the
condition holds) — its attribute dictionary if it is a labelled array, or the
empty dictionary if it is a scalar.

There is one subtlety inherited from the underlying attribute-merging routine:
if *none* of the three arguments is a labelled array there is nothing to merge,
and the routine yields "no attributes" (modeled as `none`) without consulting
the preservation rule at all.

An attribute dictionary is modeled as an association list `List (String ×
String)` (key/value pairs). The overall result is modeled as `Except Unit
(Option Attrs)`: `Except.ok none` for the no-arrays case, `Except.ok (some d)`
for a resolved dictionary `d`, and `Except.error ()` reserved for an
out-of-range lookup failure.
-/

-- axioms-start
-- No unchanged callee is consumed: the attribute-selection rule and the
-- "nothing to merge" short-circuit are both modeled deeply (spelled out).
-- axioms-end

-- pure-start
/-- An attribute dictionary: an ordered list of key/value pairs. -/
abbrev Attrs := List (String × String)

/-- A positional argument to the conditional selection: either a labelled array
carrying its own attribute dictionary, or a bare scalar (no attributes). -/
inductive Arg where
  | darray (attrs : Attrs)
  | scalar
  deriving DecidableEq, Repr

/-- Whether an argument is a labelled array (carries attributes). -/
def Arg.isDarray : Arg → Bool
  | .darray _ => true
  | .scalar   => false

/-- The attribute dictionary of an argument: its own dictionary if it is a
labelled array, otherwise the empty dictionary. -/
def attrsOf : Arg → Attrs
  | .darray a => a
  | .scalar   => []
-- pure-end

-- post-conditions-start
/-- Specification of the resolved attributes of `select cond x y` under
attribute preservation.

Let `objs` be the labelled-array arguments, in positional order. Then:
* if there are no labelled-array arguments, the result is `ok none`
  (nothing to merge);
* otherwise the result is `ok (some (attrsOf x))` — the attributes of the
  second positional argument `x`. -/
def problem_spec_whereAttrs
    (cond x y : Arg) (result : Except Unit (Option Attrs)) : Prop :=
  let objs := [cond, x, y].filter (fun a => a.isDarray)
  (objs = [] → result = Except.ok none) ∧
  (objs ≠ [] → result = Except.ok (some (attrsOf x)))
-- post-conditions-end

-- impl-start
def implementation_whereAttrs
    (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
  let objs := [cond, x, y].filter (fun a => a.isDarray)
  if objs = [] then
    return Except.ok none
  return Except.ok (some (attrsOf x))
-- impl-end

-- proof-start
theorem correct_whereAttrs :
    ∀ (cond x y : Arg),
      problem_spec_whereAttrs cond x y
        (implementation_whereAttrs cond x y) := by
  intro cond x y
  unfold problem_spec_whereAttrs implementation_whereAttrs
  simp only [Id.run]
  by_cases h : [cond, x, y].filter (fun a => a.isDarray) = []
  · refine ⟨fun _ => ?_, fun hne => absurd h hne⟩
    simp only [h, if_true]
    rfl
  · refine ⟨fun he => absurd he h, fun _ => ?_⟩
    simp only [h, if_false]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_whereAttrs is TOTAL and FUNCTIONAL — for every (cond,x,y) it uniquely pins the result via two complementary/exhaustive implications (objs=[] → ok none; objs≠[] → ok (some (attrsOf x))); Except.error is never permitted. Both impl and proof regions collapse to placeholders in the Lean spec_view, so same_spec stays True while I edit impl+proof freely (verified True for all 7 attacks).

### ATTACKS (all same_spec=True; run from project root, `bash scripts/lean_verify.sh <path>`):
- atk_1 PREPATCH BUG (collected[1]? indexing, Except.error on single array / wrong selection): exit=1. Genuine goal-mismatch (rfl fails on `pure (Except.error ())` vs pinned value). Spec correctly rejects the real bug ⇒ prepatch_reproduced=True (G-DIFF discriminator = 2nd conjunct).
- atk_2 PARTIAL-DOMAIN (always `ok (some (attrsOf x))`, drops the none short-circuit): exit=1 (simp made no progress on the objs=[] conjunct).
- atk_3 BOUNDARY (`attrsOf y` instead of `attrsOf x`): exit=1 (rfl fails).
- atk_4 CONTROL-FLOW-EFFECT (`Except.error ()` in nonempty branch): exit=1 (rfl fails).
- atk_5 WRONG SELECTION (`attrsOf cond`, first arg): exit=1 (rfl fails).
- atk_6 SWAPPED BRANCHES (none↔some): exit=1 (rfl fails).
- atk_7 UNGROUNDED-ORACLE ECHO (match-based, spec-equivalent to gold): exit=0 VERIFIES; `#print axioms correct_whereAttrs` ⇒ 'does not depend on any axioms' (clean). Materialized faithful patch atk_7.patch (behaviorally identical to gold; byte-identical to bundle patch.diff since callback = attrsOf x = getattr(x,'attrs',{}) and empty→None). run_resolve('pydata__xarray-6461', patch): COMPLETED=True, RESOLVED=True, attempts=1, note='resolved'. Echo that resolves ⇒ NOT a weakness under the fixed panel/eq policy.

POSITIVE CONTROL: positive_control.lean (verbatim Solution.lean) verifies exit=0; axioms=[propext] (clean).

REFINEMENT AUDIT: refinement.md declares all 3 legs R (positional filter ↔ List.filter; merge_attrs empty→None short-circuit ↔ Except.ok none; fixed callback getattr(x,'attrs',{}) ↔ attrsOf x). No A-consumed / A-reference / kind-3 legs. Confirmed grep of Solution.lean finds NO axiom/opaque decls, so axiom_check.py's skip stub is honest and there are no deep-model references to correspond-check. A-leg audit trivially satisfied (none present).

CONCLUSION: The only same-spec impl that closes with clean axioms (atk_7) is behaviorally identical to gold and its faithful patch RESOLVES; all 6 distinct genuinely-wrong impls fail to verify (real goal mismatches, not syntax). No verify⇏correct gap found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the attribute dictionary of a three-argument conditional selection.

Each of the three arguments is either a *labelled array* that carries its own
attribute dictionary, or a bare *scalar* that carries no attributes. When the
caller asks for attribute preservation, the selection's resulting attributes are
defined to be those of the **second** argument (the value chosen where the
condition holds) — its attribute dictionary if it is a labelled array, or the
empty dictionary if it is a scalar.

There is one subtlety inherited from the underlying attribute-merging routine:
if *none* of the three arguments is a labelled array there is nothing to merge,
and the routine yields "no attributes" (modeled as `none`) without consulting
the preservation rule at all.

An attribute dictionary is modeled as an association list `List (String ×
String)` (key/value pairs). The overall result is modeled as `Except Unit
(Option Attrs)`: `Except.ok none` for the no-arrays case, `Except.ok (some d)`
for a resolved dictionary `d`, and `Except.error ()` reserved for an
out-of-range lookup failure.
-/

-- axioms-start
-- No unchanged callee is consumed: the attribute-selection rule and the
-- "nothing to merge" short-circuit are both modeled deeply (spelled out).
-- axioms-end

-- pure-start
/-- An attribute dictionary: an ordered list of key/value pairs. -/
abbrev Attrs := List (String × String)

/-- A positional argument to the conditional selection: either a labelled array
carrying its own attribute dictionary, or a bare scalar (no attributes). -/
inductive Arg where
  | darray (attrs : Attrs)
  | scalar
  deriving DecidableEq, Repr

/-- Whether an argument is a labelled array (carries attributes). -/
def Arg.isDarray : Arg → Bool
  | .darray _ => true
  | .scalar   => false

/-- The attribute dictionary of an argument: its own dictionary if it is a
labelled array, otherwise the empty dictionary. -/
def attrsOf : Arg → Attrs
  | .darray a => a
  | .scalar   => []
-- pure-end

-- post-conditions-start
/-- Specification of the resolved attributes of `select cond x y` under
attribute preservation.

Let `objs` be the labelled-array arguments, in positional order. Then:
* if there are no labelled-array arguments, the result is `ok none`
  (nothing to merge);
* otherwise the result is `ok (some (attrsOf x))` — the attributes of the
  second positional argument `x`. -/
def problem_spec_whereAttrs
    (cond x y : Arg) (result : Except Unit (Option Attrs)) : Prop :=
  let objs := [cond, x, y].filter (fun a => a.isDarray)
  (objs = [] → result = Except.ok none) ∧
  (objs ≠ [] → result = Except.ok (some (attrsOf x)))
-- post-conditions-end

-- impl-start
def implementation_whereAttrs
    (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
  let objs := [cond, x, y].filter (fun a => a.isDarray)
  if objs = [] then
    return Except.ok none
  return Except.ok (some (attrsOf x))
-- impl-end

-- proof-start
theorem correct_whereAttrs :
    ∀ (cond x y : Arg),
      problem_spec_whereAttrs cond x y
        (implementation_whereAttrs cond x y) := by
  intro cond x y
  unfold problem_spec_whereAttrs implementation_whereAttrs
  simp only [Id.run]
  by_cases h : [cond, x, y].filter (fun a => a.isDarray) = []
  · refine ⟨fun _ => ?_, fun hne => absurd h hne⟩
    simp only [h, if_true]
    rfl
  · refine ⟨fun he => absurd he h, fun _ => ?_⟩
    simp only [h, if_false]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_whereAttrs is TOTAL and FUNCTIONAL — for every (cond,x,y) it uniquely pins the result via two complementary/exhaustive implications (objs=[] → ok none; objs≠[] → ok (some (attrsOf x))); Except.error is never permitted. Both impl and proof regions collapse to placeholders in the Lean spec_view, so same_spec stays True while I edit impl+proof freely (verified True for all 7 attacks).

### ATTACKS (all same_spec=True; run from project root, `bash scripts/lean_verify.sh <path>`):
- atk_1 PREPATCH BUG (collected[1]? indexing, Except.error on single array / wrong selection): exit=1. Genuine goal-mismatch (rfl fails on `pure (Except.error ())` vs pinned value). Spec correctly rejects the real bug ⇒ prepatch_reproduced=True (G-DIFF discriminator = 2nd conjunct).
- atk_2 PARTIAL-DOMAIN (always `ok (some (attrsOf x))`, drops the none short-circuit): exit=1 (simp made no progress on the objs=[] conjunct).
- atk_3 BOUNDARY (`attrsOf y` instead of `attrsOf x`): exit=1 (rfl fails).
- atk_4 CONTROL-FLOW-EFFECT (`Except.error ()` in nonempty branch): exit=1 (rfl fails).
- atk_5 WRONG SELECTION (`attrsOf cond`, first arg): exit=1 (rfl fails).
- atk_6 SWAPPED BRANCHES (none↔some): exit=1 (rfl fails).
- atk_7 UNGROUNDED-ORACLE ECHO (match-based, spec-equivalent to gold): exit=0 VERIFIES; `#print axioms correct_whereAttrs` ⇒ 'does not depend on any axioms' (clean). Materialized faithful patch atk_7.patch (behaviorally identical to gold; byte-identical to bundle patch.diff since callback = attrsOf x = getattr(x,'attrs',{}) and empty→None). run_resolve('pydata__xarray-6461', patch): COMPLETED=True, RESOLVED=True, attempts=1, note='resolved'. Echo that resolves ⇒ NOT a weakness under the fixed panel/eq policy.

POSITIVE CONTROL: positive_control.lean (verbatim Solution.lean) verifies exit=0; axioms=[propext] (clean).

REFINEMENT AUDIT: refinement.md declares all 3 legs R (positional filter ↔ List.filter; merge_attrs empty→None short-circuit ↔ Except.ok none; fixed callback getattr(x,'attrs',{}) ↔ attrsOf x). No A-consumed / A-reference / kind-3 legs. Confirmed grep of Solution.lean finds NO axiom/opaque decls, so axiom_check.py's skip stub is honest and there are no deep-model references to correspond-check. A-leg audit trivially satisfied (none present).

CONCLUSION: The only same-spec impl that closes with clean axioms (atk_7) is behaviorally identical to gold and its faithful patch RESOLVES; all 6 distinct genuinely-wrong impls fail to verify (real goal mismatches, not syntax). No verify⇏correct gap found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real repo). Verdict: FAITHFUL — no diverging input exists in the modeled domain.

Setup: base_commit 851dade worktree with patch.diff applied; real patched `where` uses `keep_attrs = lambda attrs, context: getattr(x, "attrs", {})` (computation.py:1832).

Callee trace (matches mapping.md/refinement.md exactly): where(keep_attrs=True) -> apply_ufunc keeps the callable (isinstance(keep_attrs,bool) at 1132 does not fire) -> apply_dataarray_vfunc computes objs=_all_of_type(args,DataArray) [order-preserving positional filter, computation.py:281/52-54] and calls merge_attrs([o.attrs for o in objs], combine_attrs=callback) [computation.py:311]. merge_attrs (merge.py:604): `if not variable_attrs: return None` (empty objs => None), else `if callable(combine_attrs): return combine_attrs(...)` which returns getattr(x,'attrs',{}). This is precisely the modeled function: objs=[] -> Except.ok none; else Except.ok (some (attrsOf x)).

Spec integrity: same_spec(Solution, Solution_prepatch, LeanBackend.language) = True (spec region byte-identical — not weakened for the postpatch impl). Solution.lean compiles (lean_verify exit 0); #print axioms correct_whereAttrs = [propext] only — no sorryAx, proof is genuine.

Empirical faithfulness confirmation against the REAL patched repo (xarray 0.15.1):
- conformance_check.py: checked=87475, none_branch=12525, mismatches=0 over 100k fuzzed cases; G-CONF PASS.
- Targeted adversarial cases all match: issue case (cond darray, x/y scalars -> {}); wrong-selection cases where objs[1]!=x (cond & y darrays, x scalar -> {}); all-three-darrays with distinct attrs -> x's attrs; x darray with empty attrs -> {}.
- Exhaustive enumeration over the ENTIRE modeled Arg domain (64 combos of scalar/darray x {empty, single, double attr dicts} for cond/x/y): 0 mismatches.

The spec is neither too strong nor drifted: it agrees with the real callee on every input in the modeled domain. The Except.error branch is reserved (never produced by the postpatch impl); it only serves to discriminate the prepatch attrs[1] IndexError bug (G-DIFF). Modeled domain (keep_attrs is True path only) is honestly scoped per mapping.md; keep_attrs None/str/other-callable paths are explicitly out of scope and not claimed.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier or comment naming the patched repo symbol 'where', no bug/fix narration). Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean via markers.same_spec.

Semantic judgment: every fact the spec view discloses is already public in the problem_statement, not beyond it. (a) 'resulting attributes are those of the SECOND argument (the value chosen where the condition holds), its dict if labelled array or empty dict if scalar' — the public traceback's own intent comment states 'keep the attributes of x, the second parameter, by default'; the scalar-second-argument case with keep_attrs=True is exactly the reported failure. (b) 'Except.error () reserved for an out-of-range lookup failure' — the public traceback ends in 'IndexError: list index out of range'. (c) The 'nothing to merge -> none' short-circuit is an abstract modeling detail, discloses no gold edit.

The gold fix (lambda ...: getattr(x, "attrs", {})) is not revealed beyond the publicly stated intent of keeping x's attrs. The spec is framed as an abstract 'three-argument conditional selection' and names no xarray/repo symbols (where, getattr, merge_attrs, _all_of_type, computation.py) — those appear only in refinement.md/mapping.md, which are NOT part of the consumer spec view. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

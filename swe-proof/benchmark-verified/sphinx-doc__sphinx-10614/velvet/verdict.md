# P2 adversarial audit — sphinx-doc__sphinx-10614

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `ensures out = linkMap isSvg page refs` pins the output EXACTLY, so every genuinely-refining verifying impl computes precisely `linkMap`. All wrong impls that deviate from the model (drop external-key recovery, off-by-one index, reintroduce '../' SVG prefix, drop anchor branch) FAIL verify (exit 1); the non-terminating partial-correctness escape also FAILS verify (loom_solve still must establish out=linkMap from the loop invariant). The two impls that verify (atk_1 echo `return linkMap`, atk_8 distinct `foldr`) both refine to the gold patch and RESOLVE.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No consumed axioms. The only non-trivial callee touched is the standard
@@ -81,18 +81,7 @@
   ensures out = linkMap isSvg page refs
   do
     -- impl-start
-    let mut acc : List (List Char × List Char) := []
-    let mut i := refs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ refs.length
-      invariant acc = linkMap isSvg page (refs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := refs[i - 1]!
-      acc := refEntry isSvg page c ++ acc
-      i := i - 1
-    return acc
+    return linkMap isSvg page refs
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -112,5 +101,3 @@
 
 prove_correct buildLinkMap by
   loom_solve
-  rw [linkMap_drop_step isSvg page refs i (by omega) (by omega)]
-  simp_all
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only non-trivial callee touched is the standard
@@ -82,16 +82,15 @@
   do
     -- impl-start
     let mut acc : List (List Char × List Char) := []
-    let mut i := refs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ refs.length
-      invariant acc = linkMap isSvg page (refs.drop i)
-      done_with i = 0
-      decreasing i
+    let mut j := 0
+    while j < refs.length
+      invariant 0 ≤ j ∧ j ≤ refs.length
+      invariant acc = linkMap isSvg page (refs.take j)
+      done_with j = refs.length
     do
-      let c := refs[i - 1]!
-      acc := refEntry isSvg page c ++ acc
-      i := i - 1
+      let c := refs[j]!
+      acc := acc ++ refEntry isSvg page c
+      j := j + 1
     return acc
     -- impl-end
 
@@ -112,5 +111,4 @@
 
 prove_correct buildLinkMap by
   loom_solve
-  rw [linkMap_drop_step isSvg page refs i (by omega) (by omega)]
-  simp_all
+  sorry
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only non-trivial callee touched is the standard
@@ -87,10 +87,16 @@
       invariant 0 ≤ i ∧ i ≤ refs.length
       invariant acc = linkMap isSvg page (refs.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := refs[i - 1]!
-      acc := refEntry isSvg page c ++ acc
+      let e : List (List Char × List Char) :=
+        match c.target with
+        | some uri => [(c.name, uri)]
+        | none =>
+          match c.anchor with
+          | some aid => [(c.name, (if isSvg then page else []) ++ ('#' :: aid))]
+          | none => []
+      acc := e ++ acc
       i := i - 1
     return acc
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only non-trivial callee touched is the standard
@@ -87,9 +87,8 @@
       invariant 0 ≤ i ∧ i ≤ refs.length
       invariant acc = linkMap isSvg page (refs.drop i)
       done_with i = 0
-      decreasing i
     do
-      let c := refs[i - 1]!
+      let c := refs[i]!
       acc := refEntry isSvg page c ++ acc
       i := i - 1
     return acc
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only non-trivial callee touched is the standard
@@ -82,16 +82,13 @@
   do
     -- impl-start
     let mut acc : List (List Char × List Char) := []
-    let mut i := refs.length
+    let mut i := 1
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ refs.length
-      invariant acc = linkMap isSvg page (refs.drop i)
+      invariant True
       done_with i = 0
-      decreasing i
     do
-      let c := refs[i - 1]!
-      acc := refEntry isSvg page c ++ acc
-      i := i - 1
+      acc := acc
+      i := 1
     return acc
     -- impl-end
 
@@ -112,5 +109,3 @@
 
 prove_correct buildLinkMap by
   loom_solve
-  rw [linkMap_drop_step isSvg page refs i (by omega) (by omega)]
-  simp_all
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only non-trivial callee touched is the standard
@@ -87,10 +87,16 @@
       invariant 0 ≤ i ∧ i ≤ refs.length
       invariant acc = linkMap isSvg page (refs.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := refs[i - 1]!
-      acc := refEntry isSvg page c ++ acc
+      let e : List (List Char × List Char) :=
+        match c.target with
+        | some uri => [(if c.outside then afterLastHash uri else c.name, (if isSvg then "../".toList else []) ++ uri)]
+        | none =>
+          match c.anchor with
+          | some aid => [(c.name, (if isSvg then page else []) ++ ('#' :: aid))]
+          | none => []
+      acc := e ++ acc
       i := i - 1
     return acc
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The only non-trivial callee touched is the standard
@@ -87,10 +87,13 @@
       invariant 0 ≤ i ∧ i ≤ refs.length
       invariant acc = linkMap isSvg page (refs.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := refs[i - 1]!
-      acc := refEntry isSvg page c ++ acc
+      let e : List (List Char × List Char) :=
+        match c.target with
+        | some uri => [(if c.outside then afterLastHash uri else c.name, uri)]
+        | none => []
+      acc := e ++ acc
       i := i - 1
     return acc
     -- impl-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No consumed axioms. The only non-trivial callee touched is the standard
@@ -81,18 +81,7 @@
   ensures out = linkMap isSvg page refs
   do
     -- impl-start
-    let mut acc : List (List Char × List Char) := []
-    let mut i := refs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ refs.length
-      invariant acc = linkMap isSvg page (refs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := refs[i - 1]!
-      acc := refEntry isSvg page c ++ acc
-      i := i - 1
-    return acc
+    return (refs.foldr (fun c acc => refEntry isSvg page c ++ acc) [])
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -112,5 +101,10 @@
 
 prove_correct buildLinkMap by
   loom_solve
-  rw [linkMap_drop_step isSvg page refs i (by omega) (by omega)]
-  simp_all
+  have h : ∀ xs : List DiagRef,
+      linkMap isSvg page xs = xs.foldr (fun c acc => refEntry isSvg page c ++ acc) [] := by
+    intro xs
+    induction xs with
+    | nil => rfl
+    | cons c cs ih => simp [linkMap, List.foldr, ih]
+  rw [h]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The only non-trivial callee touched is the standard
--  string operation that returns the final segment of a delimited string; it is
--  modeled DEEPLY by `afterLastHash` in the pure region (an A-reference), and
--  validated against the real library call by axiom_check.py (G-AX). Nothing is
--  axiomatized away.)
-- axioms-end

-- pure-start
/- One reference appearing in a diagram. The link map keys a fully-qualified
   class name to the URL the class should point at. A reference carries:
   * `name`     — the class key used to look the entry up;
   * `target`   — an explicit destination URL, if the class is documented;
   * `anchor`   — an in-page fragment id, used when there is no explicit target;
   * `outside` — whether the reference resolves outside the current project. -/
structure DiagRef where
  name : List Char
  target : Option (List Char)
  anchor : Option (List Char)
  outside : Bool
deriving Inhabited

/- The final segment of a `#`-delimited string: everything after the last `#`,
   or the whole string when there is no `#`. (Take from the end up to the last
   `#`, then restore order.) Deep model of the standard "split on the last
   delimiter, keep the tail" operation; validated == the real call by G-AX. -/
def afterLastHash (s : List Char) : List Char :=
  (s.reverse.takeWhile (· ≠ '#')).reverse

/- The link map entry a single reference contributes (zero or one pair):

   * With an explicit `target`, the entry maps to that target URL **verbatim**
     — never adorned with a leading relative-path prefix. The key is the
     reference `name` for an in-project class, but for an outside reference the
     key is recovered from the final segment of the target URL (so the diagram's
     class name resolves to the outside destination).
   * Otherwise, with an `anchor`, the entry maps `name` to a fragment link;
     under the embedded-object (SVG) rendering the link is taken relative to the
     page it sits on (`page` is prepended), and is a bare fragment otherwise.
   * With neither, the reference contributes nothing. -/
def refEntry (isSvg : Bool) (page : List Char) (c : DiagRef) : List (List Char × List Char) :=
  match c.target with
  | some uri => [(if c.outside then afterLastHash uri else c.name, uri)]
  | none =>
    match c.anchor with
    | some aid => [(c.name, (if isSvg then page else []) ++ ('#' :: aid))]
    | none => []

/- The whole link map: concatenate, in order, the per-reference entries.
   Front-recursive so a single unfold is available per loop step (the backward
   fold pattern). -/
def linkMap (isSvg : Bool) (page : List Char) : List DiagRef → List (List Char × List Char)
  | []      => []
  | c :: cs => refEntry isSvg page c ++ linkMap isSvg page cs

@[grind] lemma linkMap_nil (isSvg : Bool) (page : List Char) :
    linkMap isSvg page [] = [] := rfl
@[grind] lemma linkMap_cons (isSvg : Bool) (page : List Char) (c : DiagRef) (cs : List DiagRef) :
    linkMap isSvg page (c :: cs) = refEntry isSvg page c ++ linkMap isSvg page cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the link map for a diagram: walk its references in order and collect
   each one's contributed entry. `refs`, `isSvg`, `page` are read-only
   (directive 5). -/
method buildLinkMap (refs : List DiagRef) (isSvg : Bool) (page : List Char)
    return (out : List (List Char × List Char))
  ensures out = linkMap isSvg page refs
  do
    -- impl-start
    let mut acc : List (List Char × List Char) := []
    let mut i := refs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ refs.length
      invariant acc = linkMap isSvg page (refs.drop i)
      done_with i = 0
    do
      let c := refs[i - 1]!
      acc := refEntry isSvg page c ++ acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `linkMap` peels one `refEntry`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma linkMap_drop_step (isSvg : Bool) (page : List Char) (xs : List DiagRef) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    linkMap isSvg page (xs.drop (i - 1))
      = refEntry isSvg page xs[i - 1]! ++ linkMap isSvg page (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, linkMap_cons]

prove_correct buildLinkMap by
  loom_solve
  rw [linkMap_drop_step isSvg page refs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. All 8 attacks + pos_control same_spec=True (verified).

VERIFY RESULTS (lean_verify.sh, exit codes): pos_control=0; atk_1(echo `return linkMap`)=0 VERIFIES; atk_8(distinct `foldr` impl, inline induction lemma inside prove_correct)=0 VERIFIES; atk_2(forward-fold, sorry)=3; atk_3(drop c.outside external-key recovery, always key on name)=1 FAIL; atk_4(off-by-one refs[i]! vs refs[i-1]!)=1 FAIL; atk_5(non-terminating loop / partial-correctness escape)=1 FAIL; atk_6(reintroduce prepatch '../' SVG target prefix)=1 FAIL; atk_7(partial-domain: drop anchor branch)=1 FAIL. prepatch_1 & prepatch_2 both FAIL verify (exit 1) on the invariant_2 fold-step goal => prepatch bug reproduced.

KEY STRUCTURAL FACT: the frozen spec's postcondition equates out to linkMap exactly; same_spec freezes pure region (refEntry/linkMap/afterLastHash) + ensures. Therefore impl-region variation cannot yield a behaviorally-DIFFERENT verifying impl — every verifying impl is output-identical to linkMap. Soundness reduces to MODEL FIDELITY.

MODEL FIDELITY (independently re-checked): axiom_check.py exit 0 (afterLastHash == str.rsplit('#',1)[-1] on 16 boundary + 20000 fuzz). conformance_check.py exit 0 (R/I shadow of buildLinkMap == gold-patched loop on 100048 inputs, seed 10614, 0 disagreements). Base_commit source at inheritance_diagram.py:407-417 matches the prepatch; gold patch transforms it into exactly refEntry behavior (external->afterLastHash, verbatim uri no '../', anchor page++'#'++aid no '../').

RESOLVE (official harness, run_resolve): faithful_atk_1.diff is BYTE-IDENTICAL to the dataset gold patch (only trailing-newline diff) and applies cleanly. No verifying impl's faithful patch fails to resolve.

REFINEMENT.MD LEG AUDIT: A1 R, A2 I(G-CONF), A3 R, A4 A-reference(afterLastHash==rsplit, G-AX re-passed)+R+I, A5 R+I, A6 I, A7 R. No kind-3 legs; axioms region empty (no consumed axioms); the sole library call rsplit('#',1)[-1] is deep-modeled as an A-reference and its correspondence holds. mapping.md bijection (str<->List Char, Option, Bool, dict<->assoc-list) is sound; distinct-key assumption per single diagram noted and honest.

VERDICT: SOUND — 8 attacks encoded+verified, 2 verifying impls' faithful patches materialized and RESOLVED via the official harness, none breaks verify=>correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `ensures out = linkMap isSvg page refs` pins the output EXACTLY, so every genuinely-refining verifying impl computes precisely `linkMap`. All wrong impls that deviate from the model (drop external-key recovery, off-by-one index, reintroduce '../' SVG prefix, drop anchor branch) FAIL verify (exit 1); the non-terminating partial-correctness escape also FAILS verify (loom_solve still must establish out=linkMap from the loop invariant). The two impls that verify (atk_1 echo `return linkMap`, atk_8 distinct `foldr`) both refine to the gold patch and RESOLVE.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The only non-trivial callee touched is the standard
--  string operation that returns the final segment of a delimited string; it is
--  modeled DEEPLY by `afterLastHash` in the pure region (an A-reference), and
--  validated against the real library call by axiom_check.py (G-AX). Nothing is
--  axiomatized away.)
-- axioms-end

-- pure-start
/- One reference appearing in a diagram. The link map keys a fully-qualified
   class name to the URL the class should point at. A reference carries:
   * `name`     — the class key used to look the entry up;
   * `target`   — an explicit destination URL, if the class is documented;
   * `anchor`   — an in-page fragment id, used when there is no explicit target;
   * `outside` — whether the reference resolves outside the current project. -/
structure DiagRef where
  name : List Char
  target : Option (List Char)
  anchor : Option (List Char)
  outside : Bool
deriving Inhabited

/- The final segment of a `#`-delimited string: everything after the last `#`,
   or the whole string when there is no `#`. (Take from the end up to the last
   `#`, then restore order.) Deep model of the standard "split on the last
   delimiter, keep the tail" operation; validated == the real call by G-AX. -/
def afterLastHash (s : List Char) : List Char :=
  (s.reverse.takeWhile (· ≠ '#')).reverse

/- The link map entry a single reference contributes (zero or one pair):

   * With an explicit `target`, the entry maps to that target URL **verbatim**
     — never adorned with a leading relative-path prefix. The key is the
     reference `name` for an in-project class, but for an outside reference the
     key is recovered from the final segment of the target URL (so the diagram's
     class name resolves to the outside destination).
   * Otherwise, with an `anchor`, the entry maps `name` to a fragment link;
     under the embedded-object (SVG) rendering the link is taken relative to the
     page it sits on (`page` is prepended), and is a bare fragment otherwise.
   * With neither, the reference contributes nothing. -/
def refEntry (isSvg : Bool) (page : List Char) (c : DiagRef) : List (List Char × List Char) :=
  match c.target with
  | some uri => [(if c.outside then afterLastHash uri else c.name, uri)]
  | none =>
    match c.anchor with
    | some aid => [(c.name, (if isSvg then page else []) ++ ('#' :: aid))]
    | none => []

/- The whole link map: concatenate, in order, the per-reference entries.
   Front-recursive so a single unfold is available per loop step (the backward
   fold pattern). -/
def linkMap (isSvg : Bool) (page : List Char) : List DiagRef → List (List Char × List Char)
  | []      => []
  | c :: cs => refEntry isSvg page c ++ linkMap isSvg page cs

@[grind] lemma linkMap_nil (isSvg : Bool) (page : List Char) :
    linkMap isSvg page [] = [] := rfl
@[grind] lemma linkMap_cons (isSvg : Bool) (page : List Char) (c : DiagRef) (cs : List DiagRef) :
    linkMap isSvg page (c :: cs) = refEntry isSvg page c ++ linkMap isSvg page cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the link map for a diagram: walk its references in order and collect
   each one's contributed entry. `refs`, `isSvg`, `page` are read-only
   (directive 5). -/
method buildLinkMap (refs : List DiagRef) (isSvg : Bool) (page : List Char)
    return (out : List (List Char × List Char))
  ensures out = linkMap isSvg page refs
  do
    -- impl-start
    let mut acc : List (List Char × List Char) := []
    let mut i := refs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ refs.length
      invariant acc = linkMap isSvg page (refs.drop i)
      done_with i = 0
    do
      let c := refs[i - 1]!
      acc := refEntry isSvg page c ++ acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `linkMap` peels one `refEntry`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma linkMap_drop_step (isSvg : Bool) (page : List Char) (xs : List DiagRef) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    linkMap isSvg page (xs.drop (i - 1))
      = refEntry isSvg page xs[i - 1]! ++ linkMap isSvg page (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, linkMap_cons]

prove_correct buildLinkMap by
  loom_solve
  rw [linkMap_drop_step isSvg page refs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. All 8 attacks + pos_control same_spec=True (verified).

VERIFY RESULTS (lean_verify.sh, exit codes): pos_control=0; atk_1(echo `return linkMap`)=0 VERIFIES; atk_8(distinct `foldr` impl, inline induction lemma inside prove_correct)=0 VERIFIES; atk_2(forward-fold, sorry)=3; atk_3(drop c.outside external-key recovery, always key on name)=1 FAIL; atk_4(off-by-one refs[i]! vs refs[i-1]!)=1 FAIL; atk_5(non-terminating loop / partial-correctness escape)=1 FAIL; atk_6(reintroduce prepatch '../' SVG target prefix)=1 FAIL; atk_7(partial-domain: drop anchor branch)=1 FAIL. prepatch_1 & prepatch_2 both FAIL verify (exit 1) on the invariant_2 fold-step goal => prepatch bug reproduced.

KEY STRUCTURAL FACT: the frozen spec's postcondition equates out to linkMap exactly; same_spec freezes pure region (refEntry/linkMap/afterLastHash) + ensures. Therefore impl-region variation cannot yield a behaviorally-DIFFERENT verifying impl — every verifying impl is output-identical to linkMap. Soundness reduces to MODEL FIDELITY.

MODEL FIDELITY (independently re-checked): axiom_check.py exit 0 (afterLastHash == str.rsplit('#',1)[-1] on 16 boundary + 20000 fuzz). conformance_check.py exit 0 (R/I shadow of buildLinkMap == gold-patched loop on 100048 inputs, seed 10614, 0 disagreements). Base_commit source at inheritance_diagram.py:407-417 matches the prepatch; gold patch transforms it into exactly refEntry behavior (external->afterLastHash, verbatim uri no '../', anchor page++'#'++aid no '../').

RESOLVE (official harness, run_resolve): faithful_atk_1.diff is BYTE-IDENTICAL to the dataset gold patch (only trailing-newline diff) and applies cleanly. No verifying impl's faithful patch fails to resolve.

REFINEMENT.MD LEG AUDIT: A1 R, A2 I(G-CONF), A3 R, A4 A-reference(afterLastHash==rsplit, G-AX re-passed)+R+I, A5 R+I, A6 I, A7 R. No kind-3 legs; axioms region empty (no consumed axioms); the sole library call rsplit('#',1)[-1] is deep-modeled as an A-reference and its correspondence holds. mapping.md bijection (str<->List Char, Option, Bool, dict<->assoc-list) is sound; distinct-key assumption per single diagram noted and honest.

VERDICT: SOUND — 8 attacks encoded+verified, 2 verifying impls' faithful patches materialized and RESOLVED via the official harness, none breaks verify=>correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of buildLinkMap vs the gold-patched html_visit_inheritance_diagram link-map construction (sphinx/ext/inheritance_diagram.py:411-423). No diverging input found; the modeled function agrees with the real callee on all analyzed inputs.

Evidence:
1. Spec region byte-identical across variants: swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True (velvet LanguageTables). Both prepatches diverge in impl only, so the frozen spec is non-vacuous — it genuinely constrains external-key recovery + verbatim URL (prepatch_1) and SVG anchor '../'-prefix removal (prepatch_2).
2. Solution.lean elaborates cleanly (lean_verify.sh exit 0), so the ensures (out = linkMap isSvg page refs) is a real, provable postcondition, not sorry/vacuous.
3. Branch precedence matches: real 'if refuri is not None: ... elif refid ...' == model 'match c.target | some => ... | none => match c.anchor'. A DiagRef with both target and anchor takes the target branch on both sides.
4. External key recovery: real 'refname = refuri.rsplit("#",1)[-1]' (when not internal) is deep-modeled by afterLastHash; verified equal on 16 boundary + 20000 (axiom_check.py, G-AX pass) and an independent 300k fuzz I ran (0 mismatches). Value emitted verbatim (uri) on both sides.
5. Anchor branch: SVG -> page ++ '#'::aid == current_filename + '#' + refid; non-SVG -> '#'::aid. Matches gold patch (removal of leading '../').
6. current_filename's os.path.basename(...) is computed OUTSIDE the modeled loop region (411-423); page is a free read-only parameter bound to that runtime value, a fair parameterization boundary — not drift.
7. The one genuine abstraction risk — dict (real) vs ordered assoc-list of writes (model) — is honored by the mapping.md bijection (last-write-wins on collision, matching Python dict ==). conformance_check.py (SHADOW=Solution R/I transliteration vs ORACLE=verbatim gold-patched loop) agrees on 100,048 inputs incl. duplicate-key children, seed 10614, 0 disagreements.
8. Confirmed the ORACLE transliteration matches the actual patched source (gold patch from test.jsonl and the checked-out visitor read directly).

Conclusion: the spec is not too strong; it faithfully tracks the real callee's observable behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: no hard failures); spec is byte-identical across both prepatch variants (same_spec True). Spec view contains no diff markers, no reproduced gold-patch line (>=8 char normalized), no patched file path (sphinx/ext/inheritance_diagram.py) or module path, and no echo of the only distinctive patched symbol html_visit_inheritance_diagram. The repo attribute 'internal' is deliberately abstracted to the model field 'outside' (external = not internal), avoiding a repo-symbol echo; model names (DiagRef, afterLastHash, refEntry, linkMap, buildLinkMap) do not localize the edit. Comments describe target behavior abstractly ('maps to that target URL verbatim — never adorned with a leading relative-path prefix'; SVG link 'taken relative to the page it sits on') with zero bug/fix/patch/previously narration and no before/after contrast — _NARRATION_RE clean. The '../'-free SVG anchor behavior is already public in problem_statement (the 404-with-SVG bug); the intersphinx external-key recovery (rsplit('#',1)[-1]) appears only as forward behavioral spec, not as an edit to apply. Specifying corrected behavior is the spec's purpose and is not gold-edit leakage beyond the public problem_statement. Recorded G-PANEL-3 = pass; not a relaxed bundle (no RELAXED_LEAKAGE.md, relaxed_leakage unset). Concur: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

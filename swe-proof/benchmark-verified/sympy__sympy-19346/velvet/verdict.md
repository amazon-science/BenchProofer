# P2 adversarial audit — sympy__sympy-19346

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,7 +97,7 @@
       done_with i = 0
       decreasing i
     do
-      let piece := kvText items[i - 1]!
+      let piece := items[i - 1]!.1.strText ++ ": ".toList ++ items[i - 1]!.2.strText
       joined := if i = items.length then piece else piece ++ ", ".toList ++ joined
       i := i - 1
     return "{".toList ++ joined ++ "}".toList
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,7 +122,7 @@
         done_with i = 0
         decreasing i
       do
-        let piece := doprint elems[i - 1]!
+        let piece := elems[i - 1]!.strText
         joined := if i = elems.length then piece else piece ++ ", ".toList ++ joined
         i := i - 1
       return "{".toList ++ joined ++ "}".toList
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
       decreasing i
     do
       let piece := kvText items[i - 1]!
-      joined := if i = items.length then piece else piece ++ ", ".toList ++ joined
+      joined := if i = items.length then piece else piece ++ ",".toList ++ joined
       i := i - 1
     return "{".toList ++ joined ++ "}".toList
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,7 @@
   do
     -- impl-start
     if elems = [] then
-      return "set()".toList
+      return "{}".toList
     else
       let mut joined : List Char := []
       let mut i := elems.length
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,7 +97,7 @@
       done_with i = 0
       decreasing i
     do
-      let piece := kvText items[i - 1]!
+      let piece := doprint items[i - 1]!.2 ++ ": ".toList ++ doprint items[i - 1]!.1
       joined := if i = items.length then piece else piece ++ ", ".toList ++ joined
       i := i - 1
     return "{".toList ++ joined ++ "}".toList
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,7 +100,7 @@
       let piece := kvText items[i - 1]!
       joined := if i = items.length then piece else piece ++ ", ".toList ++ joined
       i := i - 1
-    return "{".toList ++ joined ++ "}".toList
+    return "[".toList ++ joined ++ "]".toList
     -- impl-end
 
 /- Render a collection of already-rendered elements as ordinary supported code:
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,7 +123,7 @@
         decreasing i
       do
         let piece := doprint elems[i - 1]!
-        joined := if i = elems.length then piece else piece ++ ", ".toList ++ joined
+        joined := if i = elems.length then piece else piece ++ joined
         i := i - 1
       return "{".toList ++ joined ++ "}".toList
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,10 +91,10 @@
     -- impl-start
     let mut joined : List Char := []
     let mut i := items.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant joined = joinComma ((items.map kvText).drop i)
-      done_with i = 0
+      done_with i = 1 ∨ items.length = 0
       decreasing i
     do
       let piece := kvText items[i - 1]!
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,16 @@
   do
     -- impl-start
     let mut joined : List Char := []
-    let mut i := items.length
-    while i > 0
+    let mut i := 0
+    while i < items.length
       invariant 0 ≤ i ∧ i ≤ items.length
-      invariant joined = joinComma ((items.map kvText).drop i)
-      done_with i = 0
-      decreasing i
+      invariant joined = joinComma (((items.map kvText).take i).reverse)
+      done_with i = items.length
+      decreasing items.length - i
     do
-      let piece := kvText items[i - 1]!
-      joined := if i = items.length then piece else piece ++ ", ".toList ++ joined
-      i := i - 1
+      let piece := kvText items[i]!
+      joined := if i = 0 then piece else piece ++ ", ".toList ++ joined
+      i := i + 1
     return "{".toList ++ joined ++ "}".toList
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. Each element/key/value of the container is
--  supplied as an already-rendered carrier: `reprText` is the text the
--  recursive element renderer produces for it, `strText` its shallow textual
--  form. These are outputs of an unchanged rendering helper, so they are part
--  of the input carrier — not opaque oracles. The behaviour under
--  specification — assembling the brace-delimited, comma-separated rendering
--  from the RECURSIVE per-element text — is modeled DEEPLY below. Nothing is
--  borrowed from an answer key. See mapping.md.)
-- axioms-end

-- pure-start
/- A container element, carrying the two textual forms the assembler may pick
   for it: `reprText`, the text produced by the recursive element renderer
   (the same renderer applied to the whole container), and `strText`, the
   shallow textual form. The faithful rendering selects `reprText`. -/
structure Obj where
  reprText : List Char
  strText  : List Char
deriving DecidableEq, Inhabited

/- The recursive element renderer applied to one element: it yields that
   element's own fully-rendered text. -/
def doprint (o : Obj) : List Char := o.reprText

/- Join a list of already-rendered fragments with the two-character separator
   ", " between consecutive fragments (no leading or trailing separator). The
   empty list joins to the empty fragment; a single fragment joins to itself.
   Front-recursive so a single unfold is available per loop step (the backward
   fold pattern). -/
def joinComma : List (List Char) → List Char
  | []             => []
  | [x]            => x
  | x :: y :: rest => x ++ ", ".toList ++ joinComma (y :: rest)

@[grind] lemma joinComma_nil : joinComma [] = [] := rfl
@[grind] lemma joinComma_single (x : List Char) : joinComma [x] = x := rfl
@[grind] lemma joinComma_cons2 (x y : List Char) (rest : List (List Char)) :
    joinComma (x :: y :: rest) = x ++ ", ".toList ++ joinComma (y :: rest) := rfl

/- The join of a non-empty tail peels one fragment and one separator. -/
lemma joinComma_cons_ne (x : List Char) (l : List (List Char)) (h : l ≠ []) :
    joinComma (x :: l) = x ++ ", ".toList ++ joinComma l := by
  cases l with
  | nil => exact absurd rfl h
  | cons y rest => rfl

/- The rendering of one key↦value entry: the key's recursive text, the
   separator ": ", then the value's recursive text. Both components are
   recursive renderings (`doprint`), never the shallow form. -/
def kvText (p : Obj × Obj) : List Char :=
  doprint p.1 ++ ": ".toList ++ doprint p.2

/- The fully assembled mapping rendering: the entries, each rendered key↦value
   via the recursive renderer, joined by ", " and wrapped in braces. The empty
   mapping renders to "{}". -/
def dictRender (items : List (Obj × Obj)) : List Char :=
  "{".toList ++ joinComma (items.map kvText) ++ "}".toList

/- The fully assembled collection rendering: when empty it renders to the
   explicit empty-collection token "set()"; otherwise its elements, each
   rendered via the recursive renderer, joined by ", " and wrapped in braces. -/
def setRender (elems : List Obj) : List Char :=
  if elems = [] then "set()".toList
  else "{".toList ++ joinComma (elems.map doprint) ++ "}".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a mapping of already-rendered elements as ordinary supported code:
   an opening brace, then each entry "key: value" — both key and value rendered
   by the RECURSIVE element renderer (`doprint`), not the shallow textual form —
   joined by ", ", then a closing brace. `items` is the ordered list of
   key↦value pairs and is read-only (not `mut`); the loop builds a fresh result
   and never mutates its input (directive 5). -/
method printDict (items : List (Obj × Obj)) return (out : List Char)
  ensures out = dictRender items
  do
    -- impl-start
    return dictRender items
    -- impl-end

/- Render a collection of already-rendered elements as ordinary supported code:
   if it is empty, the explicit empty-collection token "set()"; otherwise an
   opening brace, its elements rendered by the RECURSIVE element renderer
   (`doprint`) and joined by ", ", then a closing brace. `elems` is read-only. -/
method printSet (elems : List Obj) return (out : List Char)
  ensures out = setRender elems
  do
    -- impl-start
    return setRender elems
    -- impl-end

/- The backward-fold step (mapping entries): dropping one fewer entry exposes
   the entry at `i-1` on the front. When it is the last entry it joins to
   itself; otherwise `joinComma` peels it with its trailing separator. The
   single goal `loom_solve` leaves for the loop body. -/
lemma joinComma_drop_step_kv (items : List (Obj × Obj)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ items.length) :
    joinComma ((items.map kvText).drop (i - 1)) =
      (if i = items.length then kvText items[i - 1]!
       else kvText items[i - 1]! ++ ", ".toList ++ joinComma ((items.map kvText).drop i)) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  have hmap1 : (items.map kvText).drop (i - 1) = (items.drop (i-1)).map kvText :=
    (List.map_drop ..).symm
  have hmap2 : (items.map kvText).drop i = (items.drop i).map kvText :=
    (List.map_drop ..).symm
  rw [hmap1, hmap2, hcons, List.map_cons]
  by_cases hempty : (items.drop i).map kvText = []
  · have hi_eq : i = items.length := by
      have h0 : ((items.drop i).map kvText).length = 0 := by rw [hempty]; rfl
      rw [List.length_map, List.length_drop] at h0; omega
    rw [hempty, joinComma_single, if_pos hi_eq]
  · have hi_ne : i ≠ items.length := by
      intro he
      apply hempty
      have h0 : ((items.drop i).map kvText).length = 0 := by
        rw [List.length_map, List.length_drop, he]; omega
      exact List.length_eq_zero_iff.mp h0
    rw [joinComma_cons_ne _ _ hempty, if_neg hi_ne]

/- The backward-fold step (collection elements): identical reasoning for the
   element renderer `doprint` in place of the entry renderer `kvText`. -/
lemma joinComma_drop_step_elem (elems : List Obj) (i : Nat)
    (hi : 0 < i) (hle : i ≤ elems.length) :
    joinComma ((elems.map doprint).drop (i - 1)) =
      (if i = elems.length then doprint elems[i - 1]!
       else doprint elems[i - 1]! ++ ", ".toList ++ joinComma ((elems.map doprint).drop i)) := by
  have hlt : i - 1 < elems.length := by omega
  have hcons : elems.drop (i - 1) = elems[i - 1]! :: elems.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  have hmap1 : (elems.map doprint).drop (i - 1) = (elems.drop (i-1)).map doprint :=
    (List.map_drop ..).symm
  have hmap2 : (elems.map doprint).drop i = (elems.drop i).map doprint :=
    (List.map_drop ..).symm
  rw [hmap1, hmap2, hcons, List.map_cons]
  by_cases hempty : (elems.drop i).map doprint = []
  · have hi_eq : i = elems.length := by
      have h0 : ((elems.drop i).map doprint).length = 0 := by rw [hempty]; rfl
      rw [List.length_map, List.length_drop] at h0; omega
    rw [hempty, joinComma_single, if_pos hi_eq]
  · have hi_ne : i ≠ elems.length := by
      intro he
      apply hempty
      have h0 : ((elems.drop i).map doprint).length = 0 := by
        rw [List.length_map, List.length_drop, he]; omega
      exact List.length_eq_zero_iff.mp h0
    rw [joinComma_cons_ne _ _ hempty, if_neg hi_ne]

prove_correct printDict by
  loom_solve

prove_correct printSet by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec structure: both methods pin their output by EXACT EQUALITY against fully-concrete TOTAL functions (printDict ensures out = dictRender items; printSet ensures out = setRender elems). dictRender/setRender/kvText/joinComma/doprint are all concrete recursive Lean defs (no axioms, no opaque, no sorry/admit; meta.json axioms=[], deep_model_references=[], conf_skip=False). same_spec elides only the impl regions + prove_correct bodies, so all postconditions and models are FROZEN and part of the signature. Under loom.semantics.termination=total, any verifying same-spec impl must terminate and be extensionally equal to dictRender/setRender.

All 11 attacks confirmed same_spec=True (swebench_unified.markers.same_spec, velvet). Verified with `bash scripts/lean_verify.sh <file>` from project root, run concurrently in batches of 4 (isolated scratch dir — no shared *.lean namespace collision; every error references THIS instance's symbols dictRender/setRender/kvText/joinComma/strText).

POSITIVE CONTROL: atk_pos (structurally different correct impl: bodies `return dictRender items` / `return setRender elems`, no loop; prove_correct trimmed to loom_solve) => EXIT 0, VERIFIES. Spec is NON-VACUOUS.

### WRONG IMPLS (all EXIT 1, genuinely rejected with 'unsolved goals' on this instance's symbols):
- atk_1 (ungrounded-oracle ECHO / prepatch dict bug: shallow .strText per key/value instead of recursive doprint=.reprText) EXIT 1 — rejected by loop invariant joined = joinComma((items.map kvText).drop i). This is the answer-key echo probe: echoing the WRONG carrier field (.strText) fails, proving reprText is a per-element INPUT CARRIER, not a baked oracle.
- atk_2 (prepatch set bug: shallow .strText per element) EXIT 1 — rejected by joined = joinComma((elems.map doprint).drop i). => prepatch_reproduced=True (matches bundle Solution_prepatch.lean / Solution_prepatch_2.lean).
- atk_3 (boundary/separator: ',' not ', ') EXIT 1 — goal shows ',' :: vs required ',' :: ' ' ::.
- atk_4 (boundary: empty set -> '{}' not 'set()') EXIT 1 — ensures out = setRender elems yields ⊢ False under elems = [].
- atk_5 (order/effect: dict emits 'value: key') EXIT 1 — kvText is order-sensitive doprint k ++ ": " ++ doprint v.
- atk_6 (delimiter: brackets '[' ']' not braces) EXIT 1 — braces pinned by dictRender.
- atk_7 (separator: set joins with NO separator) EXIT 1 — joinComma invariant.
- atk_8 (PARTIAL-DOMAIN / control-flow: while i>1 drops the entry at index 0; correct only for len<=1) EXIT 1 — ensures out = dictRender items leaves ⊢ joined_1 = joinComma (List.map kvText items) unclosed for the dropped entry.
- atk_9 (control-flow-effect: forward loop building entries in REVERSED order) EXIT 1 — reverse-tracking invariant cannot reach dictRender.

No wrong impl verified, so there are NO verifying-wrong-impl patches to materialize/run through run_resolve — the mandatory resolve step is vacuously satisfied (patches={}); no resolve run was needed, so this is not INCONCLUSIVE.

Note: a fully-CORRECT alt impl (atk_10: forward in-order build, dicts are ordered) EXIT 1 — but that is a proof/impl mismatch with the frozen backward-fold prove_correct script (proof not re-derived), NOT a spec breakage; a breakage requires a WRONG impl to VERIFY. Confirmed the frozen atk_pos (and the correct return-form) does verify, so the spec is satisfiable.

REFINEMENT.MD AUDIT (A-legs focus): legs A1/B1 = R (str↔List Char, dict↔List(Obj×Obj) in .items() order, set↔List Obj same-object iteration); A2 = I+R, A3/A4/B2/B4 = I, B3 = I+R. There are NO A-consumed and NO A-reference legs (axioms=[], deep_model_references=[]), so G-AX is legitimately skipped and there is nothing to audit for A-consumed/A-reference correspondence. No kind-3 (inexpressible-changed-op) steps: the genuinely-changed behavior (select the RECURSIVE element text; assemble brace/comma/': '-delimited string; 'set()' empty token) is modeled DEEPLY (kvText/doprint, joinComma, dictRender, setRender + verified folds), not hidden behind an axiom.

The only callee, the unchanged recursive renderer self.doprint/self._print, is correctly treated as an input carrier (Obj.reprText); the wrong-carrier echo attacks atk_1/atk_2 failing confirm this is sound (a wrong impl cannot discharge the postcondition by echoing an oracle — it must actually compute the rendering). model↔patch correspondence holds: dictRender = '{%s}' % ', '.join('%s: %s' % (doprint k, doprint v)); setRender = 'set()' if empty else '{%s}' % ', '.join(doprint e) — verbatim gold _print_dict/_print_set. G-CONF (conformance_check.py, seed 19346) independently passed 100012 inputs, 0 disagreements.

VERDICT: SOUND. 9 distinct wrong impls (echo, prepatch dict+set, separator, boundary empty-set, order-swap, delimiter, no-separator, partial-domain, reversed-order) all rejected; positive control verifies; no verify⇏correct gap.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. Each element/key/value of the container is
--  supplied as an already-rendered carrier: `reprText` is the text the
--  recursive element renderer produces for it, `strText` its shallow textual
--  form. These are outputs of an unchanged rendering helper, so they are part
--  of the input carrier — not opaque oracles. The behaviour under
--  specification — assembling the brace-delimited, comma-separated rendering
--  from the RECURSIVE per-element text — is modeled DEEPLY below. Nothing is
--  borrowed from an answer key. See mapping.md.)
-- axioms-end

-- pure-start
/- A container element, carrying the two textual forms the assembler may pick
   for it: `reprText`, the text produced by the recursive element renderer
   (the same renderer applied to the whole container), and `strText`, the
   shallow textual form. The faithful rendering selects `reprText`. -/
structure Obj where
  reprText : List Char
  strText  : List Char
deriving DecidableEq, Inhabited

/- The recursive element renderer applied to one element: it yields that
   element's own fully-rendered text. -/
def doprint (o : Obj) : List Char := o.reprText

/- Join a list of already-rendered fragments with the two-character separator
   ", " between consecutive fragments (no leading or trailing separator). The
   empty list joins to the empty fragment; a single fragment joins to itself.
   Front-recursive so a single unfold is available per loop step (the backward
   fold pattern). -/
def joinComma : List (List Char) → List Char
  | []             => []
  | [x]            => x
  | x :: y :: rest => x ++ ", ".toList ++ joinComma (y :: rest)

@[grind] lemma joinComma_nil : joinComma [] = [] := rfl
@[grind] lemma joinComma_single (x : List Char) : joinComma [x] = x := rfl
@[grind] lemma joinComma_cons2 (x y : List Char) (rest : List (List Char)) :
    joinComma (x :: y :: rest) = x ++ ", ".toList ++ joinComma (y :: rest) := rfl

/- The join of a non-empty tail peels one fragment and one separator. -/
lemma joinComma_cons_ne (x : List Char) (l : List (List Char)) (h : l ≠ []) :
    joinComma (x :: l) = x ++ ", ".toList ++ joinComma l := by
  cases l with
  | nil => exact absurd rfl h
  | cons y rest => rfl

/- The rendering of one key↦value entry: the key's recursive text, the
   separator ": ", then the value's recursive text. Both components are
   recursive renderings (`doprint`), never the shallow form. -/
def kvText (p : Obj × Obj) : List Char :=
  doprint p.1 ++ ": ".toList ++ doprint p.2

/- The fully assembled mapping rendering: the entries, each rendered key↦value
   via the recursive renderer, joined by ", " and wrapped in braces. The empty
   mapping renders to "{}". -/
def dictRender (items : List (Obj × Obj)) : List Char :=
  "{".toList ++ joinComma (items.map kvText) ++ "}".toList

/- The fully assembled collection rendering: when empty it renders to the
   explicit empty-collection token "set()"; otherwise its elements, each
   rendered via the recursive renderer, joined by ", " and wrapped in braces. -/
def setRender (elems : List Obj) : List Char :=
  if elems = [] then "set()".toList
  else "{".toList ++ joinComma (elems.map doprint) ++ "}".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a mapping of already-rendered elements as ordinary supported code:
   an opening brace, then each entry "key: value" — both key and value rendered
   by the RECURSIVE element renderer (`doprint`), not the shallow textual form —
   joined by ", ", then a closing brace. `items` is the ordered list of
   key↦value pairs and is read-only (not `mut`); the loop builds a fresh result
   and never mutates its input (directive 5). -/
method printDict (items : List (Obj × Obj)) return (out : List Char)
  ensures out = dictRender items
  do
    -- impl-start
    return dictRender items
    -- impl-end

/- Render a collection of already-rendered elements as ordinary supported code:
   if it is empty, the explicit empty-collection token "set()"; otherwise an
   opening brace, its elements rendered by the RECURSIVE element renderer
   (`doprint`) and joined by ", ", then a closing brace. `elems` is read-only. -/
method printSet (elems : List Obj) return (out : List Char)
  ensures out = setRender elems
  do
    -- impl-start
    return setRender elems
    -- impl-end

/- The backward-fold step (mapping entries): dropping one fewer entry exposes
   the entry at `i-1` on the front. When it is the last entry it joins to
   itself; otherwise `joinComma` peels it with its trailing separator. The
   single goal `loom_solve` leaves for the loop body. -/
lemma joinComma_drop_step_kv (items : List (Obj × Obj)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ items.length) :
    joinComma ((items.map kvText).drop (i - 1)) =
      (if i = items.length then kvText items[i - 1]!
       else kvText items[i - 1]! ++ ", ".toList ++ joinComma ((items.map kvText).drop i)) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  have hmap1 : (items.map kvText).drop (i - 1) = (items.drop (i-1)).map kvText :=
    (List.map_drop ..).symm
  have hmap2 : (items.map kvText).drop i = (items.drop i).map kvText :=
    (List.map_drop ..).symm
  rw [hmap1, hmap2, hcons, List.map_cons]
  by_cases hempty : (items.drop i).map kvText = []
  · have hi_eq : i = items.length := by
      have h0 : ((items.drop i).map kvText).length = 0 := by rw [hempty]; rfl
      rw [List.length_map, List.length_drop] at h0; omega
    rw [hempty, joinComma_single, if_pos hi_eq]
  · have hi_ne : i ≠ items.length := by
      intro he
      apply hempty
      have h0 : ((items.drop i).map kvText).length = 0 := by
        rw [List.length_map, List.length_drop, he]; omega
      exact List.length_eq_zero_iff.mp h0
    rw [joinComma_cons_ne _ _ hempty, if_neg hi_ne]

/- The backward-fold step (collection elements): identical reasoning for the
   element renderer `doprint` in place of the entry renderer `kvText`. -/
lemma joinComma_drop_step_elem (elems : List Obj) (i : Nat)
    (hi : 0 < i) (hle : i ≤ elems.length) :
    joinComma ((elems.map doprint).drop (i - 1)) =
      (if i = elems.length then doprint elems[i - 1]!
       else doprint elems[i - 1]! ++ ", ".toList ++ joinComma ((elems.map doprint).drop i)) := by
  have hlt : i - 1 < elems.length := by omega
  have hcons : elems.drop (i - 1) = elems[i - 1]! :: elems.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  have hmap1 : (elems.map doprint).drop (i - 1) = (elems.drop (i-1)).map doprint :=
    (List.map_drop ..).symm
  have hmap2 : (elems.map doprint).drop i = (elems.drop i).map doprint :=
    (List.map_drop ..).symm
  rw [hmap1, hmap2, hcons, List.map_cons]
  by_cases hempty : (elems.drop i).map doprint = []
  · have hi_eq : i = elems.length := by
      have h0 : ((elems.drop i).map doprint).length = 0 := by rw [hempty]; rfl
      rw [List.length_map, List.length_drop] at h0; omega
    rw [hempty, joinComma_single, if_pos hi_eq]
  · have hi_ne : i ≠ elems.length := by
      intro he
      apply hempty
      have h0 : ((elems.drop i).map doprint).length = 0 := by
        rw [List.length_map, List.length_drop, he]; omega
      exact List.length_eq_zero_iff.mp h0
    rw [joinComma_cons_ne _ _ hempty, if_neg hi_ne]

prove_correct printDict by
  loom_solve

prove_correct printSet by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec structure: both methods pin their output by EXACT EQUALITY against fully-concrete TOTAL functions (printDict ensures out = dictRender items; printSet ensures out = setRender elems). dictRender/setRender/kvText/joinComma/doprint are all concrete recursive Lean defs (no axioms, no opaque, no sorry/admit; meta.json axioms=[], deep_model_references=[], conf_skip=False). same_spec elides only the impl regions + prove_correct bodies, so all postconditions and models are FROZEN and part of the signature. Under loom.semantics.termination=total, any verifying same-spec impl must terminate and be extensionally equal to dictRender/setRender.

All 11 attacks confirmed same_spec=True (swebench_unified.markers.same_spec, velvet). Verified with `bash scripts/lean_verify.sh <file>` from project root, run concurrently in batches of 4 (isolated scratch dir — no shared *.lean namespace collision; every error references THIS instance's symbols dictRender/setRender/kvText/joinComma/strText).

POSITIVE CONTROL: atk_pos (structurally different correct impl: bodies `return dictRender items` / `return setRender elems`, no loop; prove_correct trimmed to loom_solve) => EXIT 0, VERIFIES. Spec is NON-VACUOUS.

### WRONG IMPLS (all EXIT 1, genuinely rejected with 'unsolved goals' on this instance's symbols):
- atk_1 (ungrounded-oracle ECHO / prepatch dict bug: shallow .strText per key/value instead of recursive doprint=.reprText) EXIT 1 — rejected by loop invariant joined = joinComma((items.map kvText).drop i). This is the answer-key echo probe: echoing the WRONG carrier field (.strText) fails, proving reprText is a per-element INPUT CARRIER, not a baked oracle.
- atk_2 (prepatch set bug: shallow .strText per element) EXIT 1 — rejected by joined = joinComma((elems.map doprint).drop i). => prepatch_reproduced=True (matches bundle Solution_prepatch.lean / Solution_prepatch_2.lean).
- atk_3 (boundary/separator: ',' not ', ') EXIT 1 — goal shows ',' :: vs required ',' :: ' ' ::.
- atk_4 (boundary: empty set -> '{}' not 'set()') EXIT 1 — ensures out = setRender elems yields ⊢ False under elems = [].
- atk_5 (order/effect: dict emits 'value: key') EXIT 1 — kvText is order-sensitive doprint k ++ ": " ++ doprint v.
- atk_6 (delimiter: brackets '[' ']' not braces) EXIT 1 — braces pinned by dictRender.
- atk_7 (separator: set joins with NO separator) EXIT 1 — joinComma invariant.
- atk_8 (PARTIAL-DOMAIN / control-flow: while i>1 drops the entry at index 0; correct only for len<=1) EXIT 1 — ensures out = dictRender items leaves ⊢ joined_1 = joinComma (List.map kvText items) unclosed for the dropped entry.
- atk_9 (control-flow-effect: forward loop building entries in REVERSED order) EXIT 1 — reverse-tracking invariant cannot reach dictRender.

No wrong impl verified, so there are NO verifying-wrong-impl patches to materialize/run through run_resolve — the mandatory resolve step is vacuously satisfied (patches={}); no resolve run was needed, so this is not INCONCLUSIVE.

Note: a fully-CORRECT alt impl (atk_10: forward in-order build, dicts are ordered) EXIT 1 — but that is a proof/impl mismatch with the frozen backward-fold prove_correct script (proof not re-derived), NOT a spec breakage; a breakage requires a WRONG impl to VERIFY. Confirmed the frozen atk_pos (and the correct return-form) does verify, so the spec is satisfiable.

REFINEMENT.MD AUDIT (A-legs focus): legs A1/B1 = R (str↔List Char, dict↔List(Obj×Obj) in .items() order, set↔List Obj same-object iteration); A2 = I+R, A3/A4/B2/B4 = I, B3 = I+R. There are NO A-consumed and NO A-reference legs (axioms=[], deep_model_references=[]), so G-AX is legitimately skipped and there is nothing to audit for A-consumed/A-reference correspondence. No kind-3 (inexpressible-changed-op) steps: the genuinely-changed behavior (select the RECURSIVE element text; assemble brace/comma/': '-delimited string; 'set()' empty token) is modeled DEEPLY (kvText/doprint, joinComma, dictRender, setRender + verified folds), not hidden behind an axiom.

The only callee, the unchanged recursive renderer self.doprint/self._print, is correctly treated as an input carrier (Obj.reprText); the wrong-carrier echo attacks atk_1/atk_2 failing confirm this is sound (a wrong impl cannot discharge the postcondition by echoing an oracle — it must actually compute the rendering). model↔patch correspondence holds: dictRender = '{%s}' % ', '.join('%s: %s' % (doprint k, doprint v)); setRender = 'set()' if empty else '{%s}' % ', '.join(doprint e) — verbatim gold _print_dict/_print_set. G-CONF (conformance_check.py, seed 19346) independently passed 100012 inputs, 0 disagreements.

VERDICT: SOUND. 9 distinct wrong impls (echo, prepatch dict+set, separator, boundary empty-set, order-swap, delimiter, no-separator, partial-domain, reversed-order) all rejected; positive control verifies; no verify⇏correct gap.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of sympy__sympy-19346/velvet. No divergence found; the modeled functions AGREE with the real callee on every tested input.

SPEC-REGION BYTE-IDENTITY: swebench_unified.markers.same_spec(Solution.lean, prepatch, VelvetBackend.language) = True for BOTH Solution_prepatch.lean and Solution_prepatch_2.lean. The spec view (structure Obj {reprText, strText}; doprint; joinComma; kvText = doprint p.1 ++ ": ".toList ++ doprint p.2; dictRender = "{"++joinComma(items.map kvText)++"}"; setRender = "set()" if empty else "{"++joinComma(elems.map doprint)++"}"; ensures out = dictRender items / out = setRender elems) is byte-identical; only impl/proof regions differ. Prepatch skeletons legitimately share the spec.

MODEL vs REAL CALLEE: Gold patch applied (sympy/printing/repr.py @ base 94fb720). Real _print_dict = '{%s}' % ', '.join('%s: %s' % (doprint(k),doprint(v)) for k,v in expr.items()); real _print_set = 'set()' if not expr else '{%s}' % reprify(expr, ', ') where reprify = ', '.join(doprint(e) for e in args). These map 1:1 onto kvText/joinComma/dictRender/setRender under the stated bijection (str<->List Char char-for-char; Obj.reprText<->doprint(e); dict<->List(Obj x Obj) in .items() order; set<->List Obj same-object iteration; ', '.join<->joinComma with []->'' , [x]->x, no leading/trailing sep).

EMPIRICAL CHECK (swebench-lean env + worktree sympy): ran the transliterated model against the REAL patched printer on {} , {x:y}, {x:y,y:z}, {x:{y:z}}, {Integer(1):x,x:Integer(2)}, {x+y:x*y} and set(), {x}, {x,y}, {x,y,z}, frozenset({x,y}), {Integer(0)} -> 0 divergences (identical strings including empty-dict '{}' and empty-set 'set()'). G-CONF fuzz: 100012 inputs (seed=19346) 0 disagreements.

NOT TOO STRONG: postcondition is exact-equality to the transliterated output, which equals the real repo output under the bijection, so no real behavior is rejected. Obj carrier quantifies over arbitrary reprText/strText (domain not over-restricted). Total-correctness reading is faithful: the real assembly is a bounded comprehension/', '.join over expr.items()/set elements, which trivially terminates; the decreasing i measure in each while loop matches. Solution.lean verifies exit 0 (positive control atk_pos also verifies -> non-vacuous).

Conclusion: no diverging input; spec is a faithful, tight transliteration of the gold _print_dict/_print_set.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: only the consumer spec view (the marker-projected Solution.lean, rendered via markers.spec_view) is judged; refinement.md/mapping.md quote the gold hunk verbatim + file path + 'pre-patch' but are auditor-only docs, NOT the spec view, so they are out of G-LEAK scope. Mechanical screen (leakage.screen, lean flavor) PASSES with zero hard_failures. Manual review confirms: (1) no diff markers, no 'sympy/printing/repr.py' path, no dotted module path in the spec view; (2) no gold-symbol echo — patched symbols are _print_dict/_print_set; the spec names printDict/printSet/dictRender/setRender are camelCase abstractions of the PUBLIC terms 'dict'/'set' from the problem statement, and normalized 'print_dict'/'print_set' do not appear; (3) no bug/fix narration keywords in spec-view comments — rationale prose is abstract ('recursive element renderer' vs 'shallow textual form', 'empty-collection token'). The core discriminator of the gold edit — dict/set should render elements RECURSIVELY like list/tuple instead of shallowly, with brace/comma/':' formatting — is already fully public in problem_statement (which shows srepr([x,y]) correct/recursive vs srepr({x:y})=={x: y} wrong/shallow, verbatim brace and ':' formatting, and 'fixing it will be an easy job'). The only spec-view detail not literally in the problem statement is the 'set()' empty-set token; this is standard Python repr(set()) behavior and constitutes legitimate behavioral specification, not disclosure of the edit/diff/file/symbol. The spec view specifies correct behavior (its purpose) without revealing the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
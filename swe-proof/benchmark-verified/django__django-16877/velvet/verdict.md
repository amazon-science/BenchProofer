# P2 adversarial audit — django__django-16877

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-element transformation a consumer of the
@@ -80,10 +80,9 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant acc = escSeq (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := items[i - 1]!
-      acc := condEscape e :: acc
+      acc := escapedSeq e.chars :: acc
       i := i - 1
     return acc
     -- impl-end
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
 -- (No axiomatized callees. The per-element transformation a consumer of the
@@ -80,10 +80,9 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant acc = escSeq (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := items[i - 1]!
-      acc := condEscape e :: acc
+      acc := e.chars :: acc
       i := i - 1
     return acc
     -- impl-end
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
 -- (No axiomatized callees. The per-element transformation a consumer of the
@@ -80,10 +80,9 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant acc = escSeq (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := items[i - 1]!
-      acc := condEscape e :: acc
+      acc := (if e.safe then escapedSeq e.chars else e.chars) :: acc
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
 -- (No axiomatized callees. The per-element transformation a consumer of the
@@ -80,9 +80,8 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant acc = escSeq (items.drop i)
       done_with i = 0
-      decreasing i
     do
-      let e := items[i - 1]!
+      let e := items[i]!
       acc := condEscape e :: acc
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
 -- (No axiomatized callees. The per-element transformation a consumer of the
@@ -80,10 +80,9 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant acc = escSeq (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := items[i - 1]!
-      acc := condEscape e :: acc
+      acc := (if i = 1 then condEscape e else e.chars) :: acc
       i := i - 1
     return acc
     -- impl-end
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
 -- (No axiomatized callees. The per-element transformation a consumer of the
@@ -80,12 +80,11 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant acc = escSeq (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := items[i - 1]!
-      acc := condEscape e :: acc
+      acc := acc
       i := i - 1
-    return acc
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 -- (No axiomatized callees. The per-element transformation a consumer of the
@@ -80,10 +80,9 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant acc = escSeq (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := items[i - 1]!
-      acc := condEscape e :: acc
+      acc := (if e.safe then e.chars else escapedSeq (escapedSeq e.chars)) :: acc
       i := i - 1
     return acc
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-element transformation a consumer of the
--  sequence relies on is modeled DEEPLY in the `pure` region (`condEscape`, with
--  `escapedSeq`/`entity`), so its callee is an A-reference validated against the
--  real callee by axiom_check.py (G-AX), NOT a consumed axiom. Nothing here is
--  axiomatized.)
-- axioms-end

-- pure-start
/- One element of the input sequence: its code points, plus whether it is already
   marked as safe — an element whose producer has guaranteed it needs no further
   HTML escaping. Only these two facts are observable to a consumer of the built
   sequence (mapping.md §2). -/
structure Elem where
  chars : List Char
  safe : Bool
deriving Inhabited

/- The HTML escape of a single code point: the five significant characters expand
   to their entity sequences; every other code point passes through. The ampersand
   expands such that an emitted '&' is never re-escaped, so a single per-code-point
   map is faithful (mapping.md §3.1). -/
def entity (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#x27;".toList
  else [c]

/- The HTML escape of a whole code-point sequence: concatenate the per-code-point
   entity sequences. Front-recursive so a single unfold is available per loop step
   (the backward fold pattern, plan §5.4). -/
def escapedSeq : List Char → List Char
  | []      => []
  | c :: cs => entity c ++ escapedSeq cs

/- The conditional escape of one element: an element already marked safe is
   emitted unchanged; any other element is HTML-escaped per code point. -/
def condEscape (e : Elem) : List Char :=
  if e.safe then e.chars else escapedSeq e.chars

/- The conditional escape of a whole sequence: escape each element individually,
   in the original order. Front-recursive so a single unfold is available per loop
   step. -/
def escSeq : List Elem → List (List Char)
  | []      => []
  | e :: es => condEscape e :: escSeq es

@[grind] lemma escSeq_nil : escSeq [] = [] := rfl
@[grind] lemma escSeq_cons (e : Elem) (es : List Elem) :
    escSeq (e :: es) = condEscape e :: escSeq es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Escape each element of a sequence individually, returning the list of escaped
   results in the original order. Each element is treated on its own: an element
   already marked safe is emitted unchanged; any other element is HTML-escaped per
   code point. The input sequence is read-only (directive 5: not `mut`). -/
method escapeEach (items : List Elem) return (out : List (List Char))
  ensures out = escSeq items
  do
    -- impl-start
    -- Structurally different correct impl: functional map instead of the
    -- backward-fold loop. escapeEach items = items.map condEscape.
    return items.map condEscape
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escSeq` peels one `condEscape`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma escSeq_drop_step (xs : List Elem) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    escSeq (xs.drop (i - 1)) = condEscape xs[i - 1]! :: escSeq (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escSeq_cons]

prove_correct escapeEach by
  loom_solve
  induction items with
  | nil => rfl
  | cons e es ih => simp_all [escSeq_cons]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec is `ensures out = escSeq items` — a TOTAL closed-form structural equality; axioms region is EMPTY and escSeq/condEscape/escapedSeq/entity are all concrete `def`s (no opaque/axiomatized oracle). Therefore verify <=> compute escSeq exactly, and a verifying-but-wrong impl is structurally impossible; the ungrounded-oracle-echo attack class is vacuous (nothing to echo).

ATTACKS (all same_spec=True vs bundle Solution.lean; each edits ONLY the impl region; command: `bash scripts/lean_verify.sh <path>`):
- atk_1 (prepatch bug: escape unconditionally, `escapedSeq e.chars`): rc=1. Residual `escapedSeq (items[i-1]).chars = condEscape (items[i-1])` — false when safe.
- atk_2 (identity / no escape, `e.chars`; partial-domain, correct only on safe elems): rc=1. Residual `e.chars = condEscape e` — false for non-safe.
- atk_3 (inverted safe condition): rc=1. Residual `(if safe then escapedSeq else chars) = condEscape e` — false.
- atk_4 (off-by-one boundary: `items[i]!` instead of `items[i-1]!`): rc=1. verify-fails.
- atk_5 (partial-domain: only escape index 0, `if i=1 then condEscape e else e.chars`): rc=1. Residual `(if i=1 then condEscape .. else chars) = condEscape (items[i-1])` — false.
- atk_6 (degenerate: `return []`): rc=1. Residual `[] = escSeq items` — false for nonempty.
- atk_7 (content divergence: double-escape non-safe, `escapedSeq (escapedSeq e.chars)`): rc=1. verify-fails.
All failures are genuine discriminating postcondition residuals (not syntax errors); error tails captured *.out.

POSITIVE CONTROL: pc.lean (structurally different correct impl `return items.map condEscape`, proof by induction) VERIFIES rc=0 => spec non-vacuous.

PREPATCH: bundle Solution_prepatch.lean re-verified rc=1 with documented residual `escapedSeq (items[i-1]).chars = condEscape (items[i-1])`.

A-LEG EXECUTED EVIDENCE (my mandate). Real repo at base_commit 98f6ada0... in worktree; real conditional_escape/escape source matches mapping.md §3.1 EXACTLY (`escape = SafeString(html.escape(str(text)))`; conditional_escape: Promise->str, `__html__` passthrough, else escape).
- G-AX: ` python axiom_check.py` -> rc=0 ("condEscape == conditional_escape (safe & non-safe) + escaped_seq == html.escape sound on 25 boundary + 20000 fuzz"). A-reference is EXECUTED-sound, not merely asserted.
- G-CONF: applied gold patch to, `python conformance_check.py` -> rc=0 ("R/I shadow agrees with patch.diff behaviour on 100024 inputs, 0 disagreements").

HARNESS POSITIVE CONTROL: run_resolve('django__django-16877', gold.patch) -> resolved=True, completed=True, note='resolved'. (Gold patch = `[conditional_escape(obj) for obj in value]`; F2P test_escapeseq passes.)

REFINEMENT AUDIT (refinement.md): A1/A4 = R (type bijection value<->List Elem, obj<-><chars,safe>, mark_safe/SafeString content-identity), A2 = I (order-preserving element-wise build), A3 = A-reference (conditional_escape deep-modeled by condEscape; escapedSeq sub-model == html.escape). No kind-3 (no changed-and-inexpressible op behind an axiom — whole transform is in the verified pure region). No A-consumed axioms; axioms region empty. A-reference correspondence to the real callee HOLDS (executed G-AX). The SafeString-wrapping subtlety (conditional_escape returns marked-safe; F2P join under autoescape) is correctly captured as content-identity R-leg (mapping §2) and confirmed by gold-resolve + G-CONF's str(x) comparison.

Since NO attack verifies, there is no faithful refined patch to materialize/resolve (patches={}); the verify=>correct implication holds and cannot be broken. All required runs completed; evidence present. Not INCONCLUSIVE.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-element transformation a consumer of the
--  sequence relies on is modeled DEEPLY in the `pure` region (`condEscape`, with
--  `escapedSeq`/`entity`), so its callee is an A-reference validated against the
--  real callee by axiom_check.py (G-AX), NOT a consumed axiom. Nothing here is
--  axiomatized.)
-- axioms-end

-- pure-start
/- One element of the input sequence: its code points, plus whether it is already
   marked as safe — an element whose producer has guaranteed it needs no further
   HTML escaping. Only these two facts are observable to a consumer of the built
   sequence (mapping.md §2). -/
structure Elem where
  chars : List Char
  safe : Bool
deriving Inhabited

/- The HTML escape of a single code point: the five significant characters expand
   to their entity sequences; every other code point passes through. The ampersand
   expands such that an emitted '&' is never re-escaped, so a single per-code-point
   map is faithful (mapping.md §3.1). -/
def entity (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#x27;".toList
  else [c]

/- The HTML escape of a whole code-point sequence: concatenate the per-code-point
   entity sequences. Front-recursive so a single unfold is available per loop step
   (the backward fold pattern, plan §5.4). -/
def escapedSeq : List Char → List Char
  | []      => []
  | c :: cs => entity c ++ escapedSeq cs

/- The conditional escape of one element: an element already marked safe is
   emitted unchanged; any other element is HTML-escaped per code point. -/
def condEscape (e : Elem) : List Char :=
  if e.safe then e.chars else escapedSeq e.chars

/- The conditional escape of a whole sequence: escape each element individually,
   in the original order. Front-recursive so a single unfold is available per loop
   step. -/
def escSeq : List Elem → List (List Char)
  | []      => []
  | e :: es => condEscape e :: escSeq es

@[grind] lemma escSeq_nil : escSeq [] = [] := rfl
@[grind] lemma escSeq_cons (e : Elem) (es : List Elem) :
    escSeq (e :: es) = condEscape e :: escSeq es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Escape each element of a sequence individually, returning the list of escaped
   results in the original order. Each element is treated on its own: an element
   already marked safe is emitted unchanged; any other element is HTML-escaped per
   code point. The input sequence is read-only (directive 5: not `mut`). -/
method escapeEach (items : List Elem) return (out : List (List Char))
  ensures out = escSeq items
  do
    -- impl-start
    -- Structurally different correct impl: functional map instead of the
    -- backward-fold loop. escapeEach items = items.map condEscape.
    return items.map condEscape
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escSeq` peels one `condEscape`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma escSeq_drop_step (xs : List Elem) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    escSeq (xs.drop (i - 1)) = condEscape xs[i - 1]! :: escSeq (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escSeq_cons]

prove_correct escapeEach by
  loom_solve
  induction items with
  | nil => rfl
  | cons e es ih => simp_all [escSeq_cons]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec is `ensures out = escSeq items` — a TOTAL closed-form structural equality; axioms region is EMPTY and escSeq/condEscape/escapedSeq/entity are all concrete `def`s (no opaque/axiomatized oracle). Therefore verify <=> compute escSeq exactly, and a verifying-but-wrong impl is structurally impossible; the ungrounded-oracle-echo attack class is vacuous (nothing to echo).

ATTACKS (all same_spec=True vs bundle Solution.lean; each edits ONLY the impl region; command: `bash scripts/lean_verify.sh <path>`):
- atk_1 (prepatch bug: escape unconditionally, `escapedSeq e.chars`): rc=1. Residual `escapedSeq (items[i-1]).chars = condEscape (items[i-1])` — false when safe.
- atk_2 (identity / no escape, `e.chars`; partial-domain, correct only on safe elems): rc=1. Residual `e.chars = condEscape e` — false for non-safe.
- atk_3 (inverted safe condition): rc=1. Residual `(if safe then escapedSeq else chars) = condEscape e` — false.
- atk_4 (off-by-one boundary: `items[i]!` instead of `items[i-1]!`): rc=1. verify-fails.
- atk_5 (partial-domain: only escape index 0, `if i=1 then condEscape e else e.chars`): rc=1. Residual `(if i=1 then condEscape .. else chars) = condEscape (items[i-1])` — false.
- atk_6 (degenerate: `return []`): rc=1. Residual `[] = escSeq items` — false for nonempty.
- atk_7 (content divergence: double-escape non-safe, `escapedSeq (escapedSeq e.chars)`): rc=1. verify-fails.
All failures are genuine discriminating postcondition residuals (not syntax errors); error tails captured *.out.

POSITIVE CONTROL: pc.lean (structurally different correct impl `return items.map condEscape`, proof by induction) VERIFIES rc=0 => spec non-vacuous.

PREPATCH: bundle Solution_prepatch.lean re-verified rc=1 with documented residual `escapedSeq (items[i-1]).chars = condEscape (items[i-1])`.

A-LEG EXECUTED EVIDENCE (my mandate). Real repo at base_commit 98f6ada0... in worktree; real conditional_escape/escape source matches mapping.md §3.1 EXACTLY (`escape = SafeString(html.escape(str(text)))`; conditional_escape: Promise->str, `__html__` passthrough, else escape).
- G-AX: ` python axiom_check.py` -> rc=0 ("condEscape == conditional_escape (safe & non-safe) + escaped_seq == html.escape sound on 25 boundary + 20000 fuzz"). A-reference is EXECUTED-sound, not merely asserted.
- G-CONF: applied gold patch to, `python conformance_check.py` -> rc=0 ("R/I shadow agrees with patch.diff behaviour on 100024 inputs, 0 disagreements").

HARNESS POSITIVE CONTROL: run_resolve('django__django-16877', gold.patch) -> resolved=True, completed=True, note='resolved'. (Gold patch = `[conditional_escape(obj) for obj in value]`; F2P test_escapeseq passes.)

REFINEMENT AUDIT (refinement.md): A1/A4 = R (type bijection value<->List Elem, obj<-><chars,safe>, mark_safe/SafeString content-identity), A2 = I (order-preserving element-wise build), A3 = A-reference (conditional_escape deep-modeled by condEscape; escapedSeq sub-model == html.escape). No kind-3 (no changed-and-inexpressible op behind an axiom — whole transform is in the verified pure region). No A-consumed axioms; axioms region empty. A-reference correspondence to the real callee HOLDS (executed G-AX). The SafeString-wrapping subtlety (conditional_escape returns marked-safe; F2P join under autoescape) is correctly captured as content-identity R-leg (mapping §2) and confirmed by gold-resolve + G-CONF's str(x) comparison.

Since NO attack verifies, there is no faithful refined patch to materialize/resolve (patches={}); the verify=>correct implication holds and cannot be broken. All required runs completed; evidence present. Not INCONCLUSIVE.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found; spec is a faithful (not too-strong) model of the real callee.

SPEC-REGION INTEGRITY: swebench_unified.markers.same_spec(reference, current, VelvetBackend) = True. The spec view (imports, empty axioms region, pure region Elem/entity/escapedSeq/condEscape/escSeq + the @grind lemmas, the escapeEach signature with `ensures out = escSeq items`, and the escSeq_drop_step lemma) is byte-identical with Solution.lean. Only the elided impl/proof regions differ. Solution.lean elaborates cleanly under lean_verify.sh (exit 0).

MODELED FUNCTION: escapeEach(items) with postcondition out = escSeq items. escSeq maps each Elem<chars,safe> through condEscape (safe -> chars unchanged; else escapedSeq per-code-point HTML escape). Real callee = gold patch escapeseq(value) = [conditional_escape(obj) for obj in value] (django/template/defaultfilters.py:447, additions-only patch; conditional_escape/html.escape UNCHANGED). Bijection: obj <-> <list(str(obj)), hasattr(obj,'__html__')>.

FIDELITY TESTING against REAL python html.escape (django.utils not importable in local envs, so exercised the stdlib callee that django.utils.html.escape delegates to, quote=True):
  * escapedSeq/entity (per-code-point map & -> &amp;, < -> &lt;, > -> &gt;, " -> &quot;, ' -> &#x27;, else id) vs html.escape: 0 divergences over 200,000 fuzz strings (seed 16877) + boundary set (empty, already-escaped &amp;/&#39;/&#x27;/&quot;, XSS payload, apostrophes, mixed). Confirms the ampersand-first chained .replace collapses to the per-code-point map (refinement.md 3.1 argument correct: emitted '&' never re-escaped).
  * condEscape (safe -> passthrough, non-safe -> escapedSeq) vs conditional_escape semantics: 0 divergences over 300,000 fuzz strings in BOTH safe and non-safe flavours, including astral/whitespace/backslash/'&amp;'-substring chars.
  * sequence-level escSeq (order preservation, mixed safe/non-safe): 0 divergences over 50,000 random sequences.

The R-refinements (mark_safe/SafeString wrapper and str()/Promise coercion as content-identities on List Char) match what the F2P tests observe (rendered string after join). No input in the Lean domain (List Elem) maps to a real-repo value where escSeq disagrees with escapeseq. The spec neither over- nor under-constrains relative to the real callee. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Solver-visible spec view (spec_view projection of Solution.lean; impl/proof elided) does not leak the gold edit beyond the public problem_statement. same_spec(Solution, Solution_prepatch)=True; lexical G-LEAK screen passes (no failures). Gold edit = `return [conditional_escape(obj) for obj in value]` adding filter `escapeseq` in django/template/defaultfilters.py. Checks: (L1) no diff markers, no gold-patch line reproduced; (L2) no patched file path/module (`defaultfilters`) present; identifiers are abstracted (escapeEach, condEscape, escapedSeq, escSeq, entity, Elem) and none embeds patched symbols `escapeseq`/`escape_filter` (screen confirmed no L2/L5 hit); (L3) comments describe behavior abstractly, name no gold symbol (conditional_escape/escapeseq), no file path, no bug/fix narration. The problem_statement already publicly states escapeseq escapes each element of a sequence individually (analogous to safeseq↔safe), so the modeled per-element escaping is not beyond public scope. The precise escape semantics (5-entity table, safe-passthrough via condEscape) is faithful behavioral specification inherent to a spec-based benchmark, not edit-localization leakage; it does not enable gold reconstruction that the public task did not already permit. mapping.md/refinement.md are auditor artifacts, not part of the solver spec view. No RELAXED_LEAKAGE deferral needed — screen is clean.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

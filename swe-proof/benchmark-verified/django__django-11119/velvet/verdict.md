# P2 adversarial audit — django__django-11119

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong ALGORITHM found. The only same-spec impl that verifies is a nonterminating loop (atk_8), which verifies vacuously under partial-correctness WP and has no faithful refined patch (see notes) — not a verify⇏correct break.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
@@ -60,7 +60,6 @@
       invariant 0 ≤ i ∧ i ≤ value.length
       invariant result = escapedSeq (value.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := value[i - 1]!
       result := entity c ++ result
@@ -99,12 +98,7 @@
   ensures out = (if encodeMarkup then escapedSeq value else value)
   do
     -- impl-start
-    -- The display text honors the configured escaping policy: escape when the
-    -- policy is on, otherwise pass the value through unchanged.
-    let out ← if encodeMarkup then
-        escapeCodepoints value
-      else
-        pure value
+    let out ← escapeCodepoints value
     return out
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
 -- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
@@ -60,7 +60,6 @@
       invariant 0 ≤ i ∧ i ≤ value.length
       invariant result = escapedSeq (value.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := value[i - 1]!
       result := entity c ++ result
@@ -99,13 +98,7 @@
   ensures out = (if encodeMarkup then escapedSeq value else value)
   do
     -- impl-start
-    -- The display text honors the configured escaping policy: escape when the
-    -- policy is on, otherwise pass the value through unchanged.
-    let out ← if encodeMarkup then
-        escapeCodepoints value
-      else
-        pure value
-    return out
+    return value
     -- impl-end
 
 prove_correct valueToDisplay by
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
 -- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
@@ -60,7 +60,6 @@
       invariant 0 ≤ i ∧ i ≤ value.length
       invariant result = escapedSeq (value.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := value[i - 1]!
       result := entity c ++ result
@@ -99,12 +98,10 @@
   ensures out = (if encodeMarkup then escapedSeq value else value)
   do
     -- impl-start
-    -- The display text honors the configured escaping policy: escape when the
-    -- policy is on, otherwise pass the value through unchanged.
     let out ← if encodeMarkup then
+        pure value
+      else
         escapeCodepoints value
-      else
-        pure value
     return out
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
 -- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
@@ -54,18 +54,7 @@
   ensures out = escapedSeq value
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := value.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ value.length
-      invariant result = escapedSeq (value.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := value[i - 1]!
-      result := entity c ++ result
-      i := i - 1
-    return result
+    return value
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 -- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
@@ -56,11 +56,10 @@
     -- impl-start
     let mut result : List Char := []
     let mut i := value.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ value.length
       invariant result = escapedSeq (value.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := value[i - 1]!
       result := entity c ++ result
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
 -- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
@@ -60,10 +60,9 @@
       invariant 0 ≤ i ∧ i ≤ value.length
       invariant result = escapedSeq (value.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := value[i - 1]!
-      result := entity c ++ result
+      result := [c] ++ result
       i := i - 1
     return result
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
 -- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
@@ -60,7 +60,6 @@
       invariant 0 ≤ i ∧ i ≤ value.length
       invariant result = escapedSeq (value.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := value[i - 1]!
       result := entity c ++ result
@@ -99,9 +98,7 @@
   ensures out = (if encodeMarkup then escapedSeq value else value)
   do
     -- impl-start
-    -- The display text honors the configured escaping policy: escape when the
-    -- policy is on, otherwise pass the value through unchanged.
-    let out ← if encodeMarkup then
+    let out ← if !encodeMarkup then
         escapeCodepoints value
       else
         pure value
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
@@ -60,7 +60,6 @@
       invariant 0 ≤ i ∧ i ≤ value.length
       invariant result = escapedSeq (value.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := value[i - 1]!
       result := entity c ++ result
@@ -99,12 +98,13 @@
   ensures out = (if encodeMarkup then escapedSeq value else value)
   do
     -- impl-start
-    -- The display text honors the configured escaping policy: escape when the
-    -- policy is on, otherwise pass the value through unchanged.
-    let out ← if encodeMarkup then
-        escapeCodepoints value
-      else
-        pure value
+    let mut out : List Char := []
+    let mut i := value.length
+    while i > 0
+      invariant 0 ≤ i ∧ i ≤ value.length
+      done_with i = 0
+    do
+      i := i - 1
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
--  — `escapedSeq`/`entity` ARE the per-code-point substitution — and validated
--  == the real escaping callee by axiom_check.py (G-AX), an A-reference, not a
--  consumed contract. The policy-selection the change introduces is modeled
--  concretely by the `if` in `valueToDisplay`.)
-- axioms-end

-- pure-start
/- The escape of a single code point: the five significant markup characters
   expand to their entity sequences, every other code point passes through
   unchanged. The substitution is per-code-point and single-pass — each input
   character is mapped once and the emitted entity characters are never
   re-scanned (mapping.md §3.1). -/
def entity (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#39;".toList
  else [c]

/- The escape of a whole sequence: concatenate the per-code-point entity
   sequences. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern, plan §5.4). -/
def escapedSeq : List Char → List Char
  | []      => []
  | c :: cs => entity c ++ escapedSeq cs

@[grind] lemma escapedSeq_nil : escapedSeq [] = [] := rfl
@[grind] lemma escapedSeq_cons (c : Char) (cs : List Char) :
    escapedSeq (c :: cs) = entity c ++ escapedSeq cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Markup-escape a value: produce the per-code-point entity expansion of the
   input. The five significant characters become their entities; everything else
   passes through. Read-only input (`value` is not `mut`; the escape produces a
   fresh sequence — directive 5). -/
method escapeCodepoints (value : List Char) return (out : List Char)
  ensures out = escapedSeq value
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := value.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ value.length
      invariant result = escapedSeq (value.drop i)
      done_with i = 0
    do
      let c := value[i - 1]!
      result := entity c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escapedSeq` peels one `entity`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma escapedSeq_drop_step (value : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ value.length) :
    escapedSeq (value.drop (i - 1)) = entity value[i - 1]! ++ escapedSeq (value.drop i) := by
  have hlt : i - 1 < value.length := by omega
  have hcons : value.drop (i - 1) = value[i - 1]! :: value.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escapedSeq_cons]

prove_correct escapeCodepoints by
  loom_solve
  rw [escapedSeq_drop_step value i (by omega) (by omega)]
  simp_all

/- Render an input value to its display text under the configured markup-escaping
   policy. The policy flag `encodeMarkup` is the configured escaping setting,
   which MUST govern this rendering: when the policy is on, the value is
   markup-escaped (its per-code-point entity expansion); when the policy is off,
   the value is displayed verbatim. The policy flag must be honored — a value is
   escaped if and only if the policy says so. Both inputs are read-only (neither
   is `mut`; rendering mutates nothing — directive 5); the result is a fresh
   sequence. -/
method valueToDisplay (encodeMarkup : Bool) (value : List Char) return (out : List Char)
  ensures out = (if encodeMarkup then escapedSeq value else value)
  do
    -- impl-start
    let mut out : List Char := value
    if encodeMarkup then
      out ← escapeCodepoints value
    return out
    -- impl-end

prove_correct valueToDisplay by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-pinned functional postconditions, NO consumed axiom. escapeCodepoints ensures out=escapedSeq value; valueToDisplay ensures out=(if encodeMarkup then escapedSeq value else value). escapedSeq/entity are concrete pure defs (per-code-point HTML-entity substitution, legacy '&#39;' apostrophe — commit-correct). Attack surface is the A-reference (escapedSeq==real escape callee) and the model↔patch correspondence; R/I legs pre-cleared by G-CONF.

SAME-SPEC: all 9 wrong impls + both positive controls return same_spec=True via swebench_unified.markers.same_spec (velvet). Command form: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(BUNDLE_Solution).read(), open(ATK).read(), b.language))".

### VERIFY (bash scripts/lean_verify.sh <file>, run concurrently <=4):
  atk_1 prepatch always-escape (ignores flag)  -> EXIT 1 REJECTED (goal x = if encodeMarkup then escapedSeq value else value, hyp x=escapedSeq value; the encodeMarkup=false leg = F2P test_autoescape_off).
  atk_2 never-escape/verbatim                  -> EXIT 1 REJECTED (value = if encodeMarkup then escapedSeq value else value; then-branch).
  atk_3 swapped branches                        -> EXIT 1 REJECTED.
  atk_4 ungrounded-oracle echo (escapeCodepoints returns raw input) -> EXIT 1 REJECTED (value = escapedSeq value).
  atk_5 boundary off-by-one (while i>1, drops first char) -> EXIT 1 REJECTED (done_with unsatisfiable: i=0).
  atk_6 control-flow effect (loop appends [c] not entity c) -> EXIT 1 REJECTED (invariant: value[i-1]::escapedSeq(...) = entity value[i-1] ++ escapedSeq(...), false on the 5 significant chars).
  atk_7 negated flag polarity (if !encodeMarkup)-> EXIT 1 REJECTED.
  atk_9 terminating control-flow-effect (returns [] after draining loop) -> EXIT 1 REJECTED ([] = if encodeMarkup then escapedSeq value else value).
  pos_control.lean (gold, byte-identical impl)  -> EXIT 0 verifies.
  pos_control2.lean (structurally different correct: let mut out:=value; if encodeMarkup then out<-escapeCodepoints value) -> EXIT 0 verifies (non-vacuity).

THE ONE VERIFIER — atk_8 (atk_8.lean): diverging loop `while true invariant True done_with False do k:=k+1` then `return out`. VERIFY EXIT 0 (elaborates, no sorry/admit/error). This verifies VACUOUSLY: under set_option loom.semantics.termination "partial" the weakest-precondition of a non-returning command is trivially true, so it satisfies ANY postcondition. This is NOT a refinement-fidelity defect of this spec:

  (a) UNIVERSAL ARTIFACT of the sanctioned partial mode (spec_guide.md 1.1 explicitly allows partial; 401/500 accepted velvet bundles use "partial" and every one admits an identical diverging verifier). Treating it as BROKEN would false-fail essentially every partial-correctness bundle — clearly not the gate's scope, which is refinement fidelity of the ALGORITHM.

  (b) OUTSIDE the enumerated attack surface (partial-domain/boundary/control-flow-effect/ungrounded-oracle echo). Divergence is none of these; the analogous TERMINATING control-flow attack (atk_9) is correctly rejected.

  (c) NO FAITHFUL REFINED PATCH EXISTS. refinement.md A1-A5 maps each impl op to a gold-patch op (the one-token `Context(context, autoescape=self.autoescape)` change and the render_value_in_context branch). A `while true` corresponds to NO operation in the gold patch; any 'hanging render_to_string' I could author would be fabricated, not obtained by refining through the documented R/A/I correspondence. Hence no resolve run is 'needed' for atk_8 (a fabricated hang would merely time out, proving nothing about verify⇏correct). Excluded from the counterexample list on that basis, reported here for full transparency.

A-LEG audited (step 3): ran the bundle's axiom_check.py against the REAL repo — python axiom_check.py -> rc 0: 'G-AX OK: escaped_seq deep model (== django.utils.html.escape and conditional_escape, legacy \'&#39;\') sound on 23 boundary + 20000 fuzz inputs'. Confirmed html.py _html_escapes maps ord->'&#39;' (legacy decimal) at this base_commit — NOT the later '&#x27;' (instance 11276), which refinement.md B correctly disclaims. refinement.md legs are all R (bool<->Bool, str<->List Char), A-reference (escapedSeq deep model == real escape callee, validated by G-AX), or I — NO kind-3, NO consumed axiom (the changed op — escape-iff-policy — is modeled concretely by `if encodeMarkup`, not hidden behind an oracle). mapping.md correspondence to Engine.render_to_string / render_value_in_context / django.utils.html.escape holds.

POSITIVE CONTROLS: pos_control2 (structurally different correct impl) verifies -> spec is non-vacuous and accepts genuine alternatives. Gold (pos_control) also verifies.

CONCLUSION: >=5 attacks run (8 terminating same-spec wrong impls, all REJECTED); prepatch reproduced (atk_1); positive control verifies; A-reference sound against the real repo. No verifying wrong ALGORITHM; the only verifying impl is the universal partial-correctness divergence artifact, which has no faithful refined patch and is out of the refinement-fidelity attack surface. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong ALGORITHM found. The only same-spec impl that verifies is a nonterminating loop (atk_8), which verifies vacuously under partial-correctness WP and has no faithful refined patch (see notes) — not a verify⇏correct break.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The markup-escape of a value is modeled DEEPLY below
--  — `escapedSeq`/`entity` ARE the per-code-point substitution — and validated
--  == the real escaping callee by axiom_check.py (G-AX), an A-reference, not a
--  consumed contract. The policy-selection the change introduces is modeled
--  concretely by the `if` in `valueToDisplay`.)
-- axioms-end

-- pure-start
/- The escape of a single code point: the five significant markup characters
   expand to their entity sequences, every other code point passes through
   unchanged. The substitution is per-code-point and single-pass — each input
   character is mapped once and the emitted entity characters are never
   re-scanned (mapping.md §3.1). -/
def entity (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#39;".toList
  else [c]

/- The escape of a whole sequence: concatenate the per-code-point entity
   sequences. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern, plan §5.4). -/
def escapedSeq : List Char → List Char
  | []      => []
  | c :: cs => entity c ++ escapedSeq cs

@[grind] lemma escapedSeq_nil : escapedSeq [] = [] := rfl
@[grind] lemma escapedSeq_cons (c : Char) (cs : List Char) :
    escapedSeq (c :: cs) = entity c ++ escapedSeq cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Markup-escape a value: produce the per-code-point entity expansion of the
   input. The five significant characters become their entities; everything else
   passes through. Read-only input (`value` is not `mut`; the escape produces a
   fresh sequence — directive 5). -/
method escapeCodepoints (value : List Char) return (out : List Char)
  ensures out = escapedSeq value
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := value.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ value.length
      invariant result = escapedSeq (value.drop i)
      done_with i = 0
    do
      let c := value[i - 1]!
      result := entity c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escapedSeq` peels one `entity`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma escapedSeq_drop_step (value : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ value.length) :
    escapedSeq (value.drop (i - 1)) = entity value[i - 1]! ++ escapedSeq (value.drop i) := by
  have hlt : i - 1 < value.length := by omega
  have hcons : value.drop (i - 1) = value[i - 1]! :: value.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escapedSeq_cons]

prove_correct escapeCodepoints by
  loom_solve
  rw [escapedSeq_drop_step value i (by omega) (by omega)]
  simp_all

/- Render an input value to its display text under the configured markup-escaping
   policy. The policy flag `encodeMarkup` is the configured escaping setting,
   which MUST govern this rendering: when the policy is on, the value is
   markup-escaped (its per-code-point entity expansion); when the policy is off,
   the value is displayed verbatim. The policy flag must be honored — a value is
   escaped if and only if the policy says so. Both inputs are read-only (neither
   is `mut`; rendering mutates nothing — directive 5); the result is a fresh
   sequence. -/
method valueToDisplay (encodeMarkup : Bool) (value : List Char) return (out : List Char)
  ensures out = (if encodeMarkup then escapedSeq value else value)
  do
    -- impl-start
    let mut out : List Char := value
    if encodeMarkup then
      out ← escapeCodepoints value
    return out
    -- impl-end

prove_correct valueToDisplay by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-pinned functional postconditions, NO consumed axiom. escapeCodepoints ensures out=escapedSeq value; valueToDisplay ensures out=(if encodeMarkup then escapedSeq value else value). escapedSeq/entity are concrete pure defs (per-code-point HTML-entity substitution, legacy '&#39;' apostrophe — commit-correct). Attack surface is the A-reference (escapedSeq==real escape callee) and the model↔patch correspondence; R/I legs pre-cleared by G-CONF.

SAME-SPEC: all 9 wrong impls + both positive controls return same_spec=True via swebench_unified.markers.same_spec (velvet). Command form: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(BUNDLE_Solution).read(), open(ATK).read(), b.language))".

### VERIFY (bash scripts/lean_verify.sh <file>, run concurrently <=4):
  atk_1 prepatch always-escape (ignores flag)  -> EXIT 1 REJECTED (goal x = if encodeMarkup then escapedSeq value else value, hyp x=escapedSeq value; the encodeMarkup=false leg = F2P test_autoescape_off).
  atk_2 never-escape/verbatim                  -> EXIT 1 REJECTED (value = if encodeMarkup then escapedSeq value else value; then-branch).
  atk_3 swapped branches                        -> EXIT 1 REJECTED.
  atk_4 ungrounded-oracle echo (escapeCodepoints returns raw input) -> EXIT 1 REJECTED (value = escapedSeq value).
  atk_5 boundary off-by-one (while i>1, drops first char) -> EXIT 1 REJECTED (done_with unsatisfiable: i=0).
  atk_6 control-flow effect (loop appends [c] not entity c) -> EXIT 1 REJECTED (invariant: value[i-1]::escapedSeq(...) = entity value[i-1] ++ escapedSeq(...), false on the 5 significant chars).
  atk_7 negated flag polarity (if !encodeMarkup)-> EXIT 1 REJECTED.
  atk_9 terminating control-flow-effect (returns [] after draining loop) -> EXIT 1 REJECTED ([] = if encodeMarkup then escapedSeq value else value).
  pos_control.lean (gold, byte-identical impl)  -> EXIT 0 verifies.
  pos_control2.lean (structurally different correct: let mut out:=value; if encodeMarkup then out<-escapeCodepoints value) -> EXIT 0 verifies (non-vacuity).

THE ONE VERIFIER — atk_8 (atk_8.lean): diverging loop `while true invariant True done_with False do k:=k+1` then `return out`. VERIFY EXIT 0 (elaborates, no sorry/admit/error). This verifies VACUOUSLY: under set_option loom.semantics.termination "partial" the weakest-precondition of a non-returning command is trivially true, so it satisfies ANY postcondition. This is NOT a refinement-fidelity defect of this spec:

  (a) UNIVERSAL ARTIFACT of the sanctioned partial mode (spec_guide.md 1.1 explicitly allows partial; 401/500 accepted velvet bundles use "partial" and every one admits an identical diverging verifier). Treating it as BROKEN would false-fail essentially every partial-correctness bundle — clearly not the gate's scope, which is refinement fidelity of the ALGORITHM.

  (b) OUTSIDE the enumerated attack surface (partial-domain/boundary/control-flow-effect/ungrounded-oracle echo). Divergence is none of these; the analogous TERMINATING control-flow attack (atk_9) is correctly rejected.

  (c) NO FAITHFUL REFINED PATCH EXISTS. refinement.md A1-A5 maps each impl op to a gold-patch op (the one-token `Context(context, autoescape=self.autoescape)` change and the render_value_in_context branch). A `while true` corresponds to NO operation in the gold patch; any 'hanging render_to_string' I could author would be fabricated, not obtained by refining through the documented R/A/I correspondence. Hence no resolve run is 'needed' for atk_8 (a fabricated hang would merely time out, proving nothing about verify⇏correct). Excluded from the counterexample list on that basis, reported here for full transparency.

A-LEG audited (step 3): ran the bundle's axiom_check.py against the REAL repo — python axiom_check.py -> rc 0: 'G-AX OK: escaped_seq deep model (== django.utils.html.escape and conditional_escape, legacy \'&#39;\') sound on 23 boundary + 20000 fuzz inputs'. Confirmed html.py _html_escapes maps ord->'&#39;' (legacy decimal) at this base_commit — NOT the later '&#x27;' (instance 11276), which refinement.md B correctly disclaims. refinement.md legs are all R (bool<->Bool, str<->List Char), A-reference (escapedSeq deep model == real escape callee, validated by G-AX), or I — NO kind-3, NO consumed axiom (the changed op — escape-iff-policy — is modeled concretely by `if encodeMarkup`, not hidden behind an oracle). mapping.md correspondence to Engine.render_to_string / render_value_in_context / django.utils.html.escape holds.

POSITIVE CONTROLS: pos_control2 (structurally different correct impl) verifies -> spec is non-vacuous and accepts genuine alternatives. Gold (pos_control) also verifies.

CONCLUSION: >=5 attacks run (8 terminating same-spec wrong impls, all REJECTED); prepatch reproduced (atk_1); positive control verifies; A-reference sound against the real repo. No verifying wrong ALGORITHM; the only verifying impl is the universal partial-correctness divergence artifact, which has no faithful refined patch and is out of the refinement-fidelity attack surface. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real repo callee at base_commit d4df5e1b.

(1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, LeanBackend.language) = True; the only diff is inside impl-start/impl-end. Solution.lean verifies clean (lean_verify.sh exit 0).

(2) Escape model faithful: escapedSeq/entity ({&->&amp;,<->&lt;,>->&gt;,"->&quot;,'->&#39;, else identity}) matches django.utils.html.escape and conditional_escape exactly on boundary inputs (each significant char alone/doubled/combined/mixed) and 200,000 randomized fuzz strings (alphabet includes the 5 markup chars, printable ASCII, non-ASCII BMP é/ñ/中, and \t/\n). Apostrophe correctly maps to legacy decimal &#39; (matches this commit's _html_escapes; NOT the later &#x27; of instance 11276). BAD=0.

(3) Policy branch faithful: valueToDisplay = if encodeMarkup then escapedSeq value else value corresponds to render_value_in_context: escape via conditional_escape(str(value)) when context.autoescape on, plain str(value) verbatim when off (base.py:970-975). The gold patch threads Context(context, autoescape=self.autoescape) so the engine's configured flag governs the branch — confirmed present in the worktree engine.py:171.

(4) End-to-end faithful: the patched Engine.render_to_string over the 'obj:{{ obj }}\n' locmem template, for both autoescape=True/False, equals the shadow 'obj:' + valueToDisplay(ae, val) + '\n' on boundary cases + 3000 fuzz strings. BAD=0.

The type abstraction (Bool<->autoescape flag, List Char<->str, plain-str-only domain) is legitimate and not spec-too-strong: the F2P input '<script>' is an ordinary str, so conditional_escape's Promise/__html__ short-circuits are genuinely out of the tested input domain; restricting the model to plain str is faithful to what the F2P test exercises. str()/template_localtime/localize/mark_safe are observationally identity on plain-str content. No input was found where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution, Solution_prepatch)=True (spec region byte-identical; discriminator lives only in elided impl). Mechanical leakage.screen passes with zero hard failures. Spec view uses only abstract Lean vocabulary — valueToDisplay(encodeMarkup:Bool)(value:List Char) with postcondition out = (if encodeMarkup then escapedSeq value else value). It contains NO repo-specific gold-edit tokens: no 'autoescape', 'render_to_string', 'engine', 'Context(context, autoescape=self.autoescape)', 'self.autoescape', file path, or django symbols (grep confirmed absent). The modeled semantic 'escape iff the flag is set' is exactly the intended behavior the PUBLIC problem_statement already discloses ('a Context is created without specifying the engine autoescape attribute ... result will always be autoescaped'), so it is baseline knowledge, not leakage. The escapedSeq/entity table (&amp;, &#39;, etc.) describes the UNCHANGED escaping callee (background model, G-AX A-reference), not the gold edit, so it does not reveal what to change. Comments reference internal docs (mapping.md/plan/directive 5), not the gold diff or problem-statement phrasing. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.
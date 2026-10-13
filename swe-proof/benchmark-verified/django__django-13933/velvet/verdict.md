# P2 adversarial audit — django__django-13933

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_0_prepatch.lean`, `atk_1_slot_dropped.lean`, `atk_2_offbyone_index.lean`, `atk_3_partial_domain.lean`, `atk_4_control_flow_short.lean`, `atk_5_oracle_echo.lean`, `atk_6_first_slot_only.lean`, `atk_7_value_reversed.lean`, `atk_8_value_truncated.lean`, `atk_9_vacuous_empty.lean`, `atk_10_forward_fold.lean`, +8 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5b_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying same-spec impl has a faithful refined patch that fails to resolve. 19 distinct wrong impls were encoded and machine-checked; every one was REJECTED by lean_verify.sh. The single non-reference impl that verified (atk_5b_oracle_echo, exit 0) is extensionally EQUAL to the spec function (`return rendered value template`), so it carries no behavioral divergence to exploit; its faithful refined patch was materialized and EXECUTED through the official harness: resolved=true, attempts=1, flaky=false. Most notable near-misses, all refuted: (a) atk_3_partial_domain — correct on the ENTIRE tested domain (F2P template has exactly one %(value)s, P2P template has none) and wrong only on multi-placeholder templates; rejected, proving the postcondition is TOTAL over `List Frag` and not narrowed to the tested shape, so the empty pre-conditions region is genuinely load-bearing. (b) atk_12_value_duplicated / atk_7_value_reversed / atk_8_value_truncated — all DO 'expose the offending value' (the issue's stated goal) yet were rejected, showing the spec pins exact character sequence and multiplicity, not mere value presence. (c) atk_14_percent_escaping — the real-world printf escaping bug (emitting '%%' for a literal '%'); rejected, and independently confirmed harmless because the `List Frag` carrier makes format-string escaping unrepresentable by construction. (d) atk_15b_nontermination — diverges on exactly the F2P input; rejected under `termination "total"` even with a fair, adapted proof script.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,6 +80,20 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+    -- Pre-image skeleton: the rejection message is built WITHOUT supplying the
+    -- offending value to the renderer (no substitution parameter is passed). The
+    -- value placeholder slot is therefore NOT filled with the value; it is left
+    -- standing as its literal placeholder token (`%(value)s`). The frozen spec
+    -- demands the value be substituted at the slot (`rendered value [valueSlot]
+    -- = value`), so `prove_correct` MUST fail on exactly the value-slot clause
+    -- (G-DIFF). On a template with no value slot this skeleton renders the same
+    -- literal text, so the divergence is isolated to templates that carry the
+    -- placeholder — the real bug.
+    let placeholderToken : List Char := "%(value)s".toList
+    let renderFragPre : Frag → List Char := fun f =>
+      match f with
+      | .lit c     => [c]
+      | .valueSlot => placeholderToken
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
@@ -89,7 +103,7 @@
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      result := renderFragPre f ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_1_slot_dropped.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,16 +80,25 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (ungrounded "value never reaches the message"): the value slot
+    -- renders to the EMPTY string instead of being filled with the offending
+    -- value. Realistic mis-fix: passing params={} / params={'value': ''}.
+    -- Wrong on the F2P template (which carries one %(value)s).
+    let renderFragW : Frag -> List Char := fun f =>
+      match f with
+      | .lit c     => [c]
+      | .valueSlot => []
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      result := renderFragW f ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_2_offbyone_index.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,15 +80,19 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (boundary / off-by-one): indexes `template[i]!` instead of
+    -- `template[i-1]!`, so the first read is OUT OF BOUNDS (returns `default`)
+    -- and fragment 0 is never rendered. Classic fencepost error.
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
-      let f := template[i - 1]!
+      let f := template[i]!
       result := renderFrag value f ++ result
       i := i - 1
     return result
```

Attack 4 — `atk_3_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,16 +80,29 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (PARTIAL DOMAIN): fills the slot only when the template
+    -- carries AT MOST ONE placeholder; on multi-placeholder templates the slots
+    -- render EMPTY. This is correct on the whole *tested* domain (the F2P
+    -- template has exactly one %(value)s; the P2P template has none), so only a
+    -- spec that constrains ALL templates can refute it. If the frozen spec had
+    -- a precondition narrowing to the tested shape, this would verify.
+    let singleSlot : Bool :=
+      (template.filter (fun g => g == Frag.valueSlot)).length <= 1
+    let renderFragW : Frag -> List Char := fun f =>
+      match f with
+      | .lit c     => [c]
+      | .valueSlot => if singleSlot then value else []
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      result := renderFragW f ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_4_control_flow_short.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,12 +80,18 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (CONTROL-FLOW EFFECT): the backward fold halts at i = 1
+    -- instead of i = 0, so fragment 0 is never rendered -- the message loses its
+    -- leading character. Wrong on the F2P template (which begins with a quote).
+    -- The loop is internally consistent and terminates; only the postcondition
+    -- `out = rendered value template` can refute it.
     let mut result : List Char := []
     let mut i := template.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+    while i > 1
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
-      done_with i = 0
+      done_with i <= 1
       decreasing i
     do
       let f := template[i - 1]!
```

Attack 6 — `atk_5_oracle_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,18 +80,12 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := template.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
-      invariant result = rendered value (template.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let f := template[i - 1]!
-      result := renderFrag value f ++ result
-      i := i - 1
-    return result
+
+    -- ORACLE ECHO: no algorithm at all -- return the specification's own pure
+    -- function verbatim. This carries ZERO implementation content, so it MUST be
+    -- checked whether the spec accepts it and, if so, whether its faithful
+    -- refined patch still resolves.
+    return rendered value template
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the fragment at
```

Attack 7 — `atk_5b_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -80,18 +80,10 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := template.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
-      invariant result = rendered value (template.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let f := template[i - 1]!
-      result := renderFrag value f ++ result
-      i := i - 1
-    return result
+
+    -- ORACLE ECHO (adapted proof): no algorithm at all -- return the
+    -- specification's own pure function verbatim. Zero implementation content.
+    return rendered value template
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the fragment at
@@ -111,5 +103,3 @@
 
 prove_correct renderInvalidChoice by
   loom_solve
-  rw [rendered_drop_step value template i (by omega) (by omega)]
-  simp_all
```

Attack 8 — `atk_6_first_slot_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,16 +80,27 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (repeated-placeholder boundary): substitutes the value at the
+    -- LAST slot only and leaves earlier slots empty -- the shape of a mis-fix
+    -- using a replace-once primitive (`str.replace(ph, v, 1)`). Correct whenever
+    -- the template has <=1 placeholder, wrong on repeated placeholders.
+    let mut filled : Bool := false
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      let piece : List Char :=
+        match f with
+        | .lit c     => [c]
+        | .valueSlot => if filled then [] else value
+      filled := (match f with | .lit _ => filled | .valueSlot => true)
+      result := piece ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 9 — `atk_7_value_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,16 +80,25 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (value-carrier corruption): the slot is filled with the value's
+    -- code points in REVERSE order. Exercises whether the spec pins the ORDER of
+    -- the substituted characters, not merely their presence. Wrong on the F2P
+    -- input ("invalid" vs "dilavni").
+    let renderFragW : Frag -> List Char := fun f =>
+      match f with
+      | .lit c     => [c]
+      | .valueSlot => value.reverse
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      result := renderFragW f ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 10 — `atk_8_value_truncated.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,16 +80,25 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (BOUNDARY on the value carrier): the slot is filled with the
+    -- value minus its first code point -- an off-by-one slice of the
+    -- interpolated value. Wrong on the F2P input ("nvalid" vs "invalid"), and
+    -- INDISTINGUISHABLE from correct whenever the value is empty.
+    let renderFragW : Frag -> List Char := fun f =>
+      match f with
+      | .lit c     => [c]
+      | .valueSlot => value.drop 1
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      result := renderFragW f ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 11 — `atk_9_vacuous_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,10 +80,16 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (degenerate CONTROL FLOW): the loop counter starts at 0 so the
+    -- body NEVER runs and the rendered message is empty. Probes whether the two
+    -- corroborating `ensures` (which are pure-region tautologies about
+    -- `rendered`, independent of the impl) can be satisfied while the real
+    -- functional postcondition is abandoned.
     let mut result : List Char := []
-    let mut i := template.length
+    let mut i := 0
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
```

Attack 12 — `atk_10_forward_fold.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,17 +80,22 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- DIFFERENT ALGORITHM, same function: a FORWARD fold appending on the right,
+    -- instead of the reference backward fold prepending on the left. If the spec
+    -- is a real functional characterization this must verify; its faithful patch
+    -- must then resolve (a same-spec/different-impl positive, not a break).
     let mut result : List Char := []
-    let mut i := template.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
-      invariant result = rendered value (template.drop i)
-      done_with i = 0
-      decreasing i
+    let mut j := 0
+    while j < template.length
+      invariant j <= template.length
+      invariant result = rendered value (template.take j)
+      done_with j = template.length
+      decreasing template.length - j
     do
-      let f := template[i - 1]!
-      result := renderFrag value f ++ result
-      i := i - 1
+      let f := template[j]!
+      result := result ++ renderFrag value f
+      j := j + 1
     return result
     -- impl-end
 
```

Attack 13 — `atk_10b_forward_fold.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,17 +80,21 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- DIFFERENT ALGORITHM, same function: FORWARD fold appending on the right
+    -- (reference walks backward prepending). A genuine same-spec/different-impl
+    -- candidate: it must verify, and its faithful patch must then resolve.
     let mut result : List Char := []
-    let mut i := template.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
-      invariant result = rendered value (template.drop i)
-      done_with i = 0
-      decreasing i
+    let mut j := 0
+    while j < template.length
+      invariant j <= template.length
+      invariant result = rendered value (template.take j)
+      done_with j = template.length
+      decreasing template.length - j
     do
-      let f := template[i - 1]!
-      result := renderFrag value f ++ result
-      i := i - 1
+      let f := template[j]!
+      result := result ++ renderFrag value f
+      j := j + 1
     return result
     -- impl-end
 
@@ -111,5 +115,14 @@
 
 prove_correct renderInvalidChoice by
   loom_solve
-  rw [rendered_drop_step value template i (by omega) (by omega)]
-  simp_all
+  · have hlt : j < template.length := by omega
+    have hj : template.take (j + 1) = template.take j ++ [template[j]!] := by
+      rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
+      rw [List.take_succ, List.getElem?_eq_getElem hlt]
+      simp
+    rw [hj]
+    clear hj
+    induction template.take j generalizing result with
+    | nil => simp [rendered]
+    | cons g gs ih => simp [rendered] at *; grind
+  · simp_all [List.take_of_length_le]
```

Attack 14 — `atk_11_literal_corrupted.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,16 +80,26 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (literal carrier corrupted): the value slot is filled correctly,
+    -- but LITERAL fragments are dropped whenever they are the quote character --
+    -- the message loses its surrounding quotes. Probes whether the spec pins the
+    -- non-placeholder text as tightly as the substitution. Wrong on the F2P
+    -- template (which is quote-delimited) while still "exposing the value".
+    let renderFragW : Frag -> List Char := fun f =>
+      match f with
+      | .lit c     => if c == '"' then [] else [c]
+      | .valueSlot => value
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      result := renderFragW f ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 15 — `atk_12_value_duplicated.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,16 +80,25 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (multiplicity at the slot): the slot is filled with the value
+    -- TWICE -- the shape of a mis-fix that both interpolates params AND
+    -- concatenates the value into the message. It DOES "expose the offending
+    -- value", so only an exact-equality postcondition can refute it.
+    let renderFragW : Frag -> List Char := fun f =>
+      match f with
+      | .lit c     => [c]
+      | .valueSlot => value ++ value
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      result := renderFragW f ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 16 — `atk_13_message_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,16 +80,21 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (fold ORDER / associativity): the backward walk APPENDS instead
+    -- of prepending, so fragments accumulate in reverse -- the message text comes
+    -- out mirrored. Every fragment is rendered correctly and the value IS
+    -- substituted; only the ORDER of the concatenation is wrong.
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      result := result ++ renderFrag value f
       i := i - 1
     return result
     -- impl-end
```

Attack 17 — `atk_14_percent_escaping.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,16 +80,25 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (escaping / carrier confusion): renders each literal '%' as the
+    -- DOUBLED printf escape '%%' instead of a single '%'. This is the classic
+    -- real-world interpolation bug (confusing the format string with the rendered
+    -- output). Every value slot is still filled correctly.
+    let renderFragW : Frag -> List Char := fun f =>
+      match f with
+      | .lit c     => if c == '%' then ['%', '%'] else [c]
+      | .valueSlot => value
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
-      result := renderFrag value f ++ result
+      result := renderFragW f ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 18 — `atk_15_nontermination.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,17 +80,22 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (TERMINATION): the counter is not decreased on the value-slot
+    -- branch, so the loop diverges on any template containing a placeholder --
+    -- exactly the F2P input. Under `termination "total"` this must be rejected;
+    -- accepting it would let a hanging renderer carry a correctness proof.
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
       result := renderFrag value f ++ result
-      i := i - 1
+      i := (match f with | .lit _ => i - 1 | .valueSlot => i)
     return result
     -- impl-end
 
```

Attack 19 — `atk_15b_nontermination.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,17 +80,22 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
+
+    -- WRONG IMPL (TERMINATION, fair proof attempt): the counter is NOT decreased
+    -- on the value-slot branch, so the loop diverges on any template carrying a
+    -- placeholder -- exactly the F2P input. Under `termination "total"` this must
+    -- be rejected no matter what proof is offered.
     let mut result : List Char := []
     let mut i := template.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
+      invariant 0 <= i /\ i <= template.length
       invariant result = rendered value (template.drop i)
       done_with i = 0
       decreasing i
     do
       let f := template[i - 1]!
       result := renderFrag value f ++ result
-      i := i - 1
+      i := (match f with | .lit _ => i - 1 | .valueSlot => i)
     return result
     -- impl-end
 
@@ -110,6 +115,9 @@
   rw [hcons, rendered_cons]
 
 prove_correct renderInvalidChoice by
-  loom_solve
-  rw [rendered_drop_step value template i (by omega) (by omega)]
-  simp_all
+  loom_solve <;>
+    first
+      | (rw [rendered_drop_step value template i (by omega) (by omega)]; simp_all)
+      | simp_all [rendered, renderFrag]
+      | grind [rendered, renderFrag, rendered_drop_step]
+      | omega
```

Attack 20 — `atk_16_value_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,18 +80,12 @@
   ensures ∀ c, rendered value [Frag.lit c] = [c]
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := template.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ template.length
-      invariant result = rendered value (template.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let f := template[i - 1]!
-      result := renderFrag value f ++ result
-      i := i - 1
-    return result
+
+    -- WRONG IMPL (message replaced by the bare value): discards the template and
+    -- returns ONLY the offending value. It maximally "exposes the value" (the
+    -- issue's stated goal) yet destroys the message -- and it is EXACTLY correct
+    -- on the single-slot template, so only the general postcondition refutes it.
+    return value
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the fragment at
@@ -111,5 +105,3 @@
 
 prove_correct renderInvalidChoice by
   loom_solve
-  rw [rendered_drop_step value template i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The rendering of a parametrized message — the
--  substitution of the offending value into the value placeholder — is the one
--  operation that changes, and it is modeled DEEPLY below (`rendered`), then
--  validated == the real string-interpolation builtin out-of-band by
--  axiom_check.py (G-AX). There is no unchanged callee whose contract the proof
--  must assume.)
-- axioms-end

-- pure-start
/- A fragment of a parametrized message: either a literal code point that passes
   through verbatim, or the value placeholder slot that stands for the offending
   submitted value. A message template is a sequence of such fragments — the
   abstract shape of a human-readable message with a single named substitution
   parameter. -/
inductive Frag where
  | lit (c : Char)
  | valueSlot
  deriving Inhabited, DecidableEq, Repr

/- The rendering of one fragment under a given value: a literal contributes its
   one code point; the value slot is FILLED with the value's code points. This is
   the substitution the parametrized message performs — the placeholder is
   replaced by the value, not left standing. -/
def renderFrag (value : List Char) : Frag → List Char
  | .lit c     => [c]
  | .valueSlot => value

/- The rendering of a whole template under a value: concatenate the per-fragment
   renderings left to right. Front-recursive so a single unfold is available per
   loop step (the Velvet fold pattern). -/
def rendered (value : List Char) : List Frag → List Char
  | []      => []
  | f :: fs => renderFrag value f ++ rendered value fs

@[grind] lemma rendered_nil (value : List Char) : rendered value [] = [] := rfl
@[grind] lemma rendered_cons (value : List Char) (f : Frag) (fs : List Frag) :
    rendered value (f :: fs) = renderFrag value f ++ rendered value fs := rfl

/- Behavioral anchors (definitional). A lone value slot renders to EXACTLY the
   value — the placeholder is substituted, never echoed literally — and a lone
   literal renders to exactly that one code point. Marked `@[grind]` so
   `loom_solve` discharges the corroborating postconditions automatically. -/
@[grind] lemma rendered_valueSlot (value : List Char) :
    rendered value [Frag.valueSlot] = value := by simp [rendered, renderFrag]
@[grind] lemma rendered_lit (value : List Char) (c : Char) :
    rendered value [Frag.lit c] = [c] := by simp [rendered, renderFrag]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When an invalid choice is rejected, the human-readable rejection message is
   produced by interpolating the offending submitted value into the message
   template. The template is a sequence of fragments (literal code points and a
   value placeholder slot); rendering substitutes the offending value at the
   placeholder and passes every literal through unchanged.

   The guarantee the issue demands: the rendered message is the template with the
   value FILLED IN at the placeholder — so a template that carries a value slot
   exposes the offending value, rather than leaving the placeholder standing
   uninterpreted.

   `template` and `value` are read-only (not `mut`): the rendering builds a fresh
   character sequence and mutates neither input (directive 5). -/
method renderInvalidChoice (template : List Frag) (value : List Char) return (out : List Char)
  ensures out = rendered value template
  ensures rendered value [Frag.valueSlot] = value
  ensures ∀ c, rendered value [Frag.lit c] = [c]
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := template.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ template.length
      invariant result = rendered value (template.drop i)
      done_with i = 0
      decreasing i
    do
      let f := template[i - 1]!
      result := renderFrag value f ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the fragment at
   `i-1` on the front, so `rendered` peels one `renderFrag`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma rendered_drop_step (value : List Char) (template : List Frag) (i : Nat)
    (hi : 0 < i) (hle : i ≤ template.length) :
    rendered value (template.drop (i - 1)) =
      renderFrag value template[i - 1]! ++ rendered value (template.drop i) := by
  have hlt : i - 1 < template.length := by omega
  have hcons : template.drop (i - 1) = template[i - 1]! :: template.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, rendered_cons]

prove_correct renderInvalidChoice by
  loom_solve
  rw [rendered_drop_step value template i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLIANCE. Same-spec: ALL 20 attack files + positive control return True from swebench_unified.markers.same_spec against the frozen Solution.lean (axioms/pure/pre/post regions byte-identical; only the impl region — and, where noted, the elided `prove_correct` body — differ). Verify cmd for each: `bash scripts/lean_verify.sh <file>`. Run 4-at-a-time as concurrent background jobs per instructions.

BASELINES. pos_control.lean (unmodified Solution.lean) -> exit 0 (verifies, no sorry). atk_0_prepatch.lean (bundle's Solution_prepatch.lean) -> exit 1, PREPATCH REPRODUCED: the unsolved goal is exactly the value-slot clause, `(match ... | Frag.valueSlot => ['%','(','v','a','l','u','e',')','s']) = renderFrag value ...` — i.e. the placeholder left standing verbatim, which is precisely the real bug (pre-patch raised ValidationError with no `params`, so `__iter__` skipped `message %= error.params`). G-DIFF confirmed.

ATTACK LEDGER (0=verifies, 1=rejected). atk_0_prepatch 1 | atk_1_slot_dropped (slot->[], params={} mis-fix) 1 | atk_2_offbyone_index (template[i]! fencepost, OOB read) 1 | atk_3_partial_domain (correct iff <=1 placeholder) 1 | atk_4_control_flow_short (loop halts at i=1, drops leading char) 1 | atk_5_oracle_echo (inherited proof) 1 | atk_5b_oracle_echo (adapted proof) **0 = VERIFIES** | atk_6_first_slot_only (replace-once mis-fix) 1 | atk_7_value_reversed 1 | atk_8_value_truncated (value.drop 1) 1 | atk_9_vacuous_empty (counter starts 0, body never runs) 1 | atk_10_forward_fold (inherited proof) 1 | atk_10b_forward_fold (adapted proof) 1 | atk_11_literal_corrupted (drops quote literals) 1 | atk_12_value_duplicated 1 | atk_13_message_reversed (append vs prepend) 1 | atk_14_percent_escaping 1 | atk_15_nontermination (inherited proof) 1 | atk_15b_nontermination (adapted proof) 1 | atk_16_value_only (return value) 1. Coverage spans every class required: partial-domain (3), boundary (2,8,11,14), control-flow-effect (4,9,13,15b), ungrounded-oracle-echo (5,5b,16), plus value-carrier corruption (7,12) and the prepatch bug (0).

FAIRNESS NOTE (important). Three attacks (5, 10, 15) initially failed with proof-script artifacts rather than genuine spec rejections — the spec view elides `prove_correct` bodies, so a legitimate consumer supplies its own proof, and inheriting the reference's tactic script is not a fair refutation. I re-ran all three with adapted proofs (5b, 10b, 15b). This is what surfaced the one verifying impl (5b, exit 0) that the naive run would have hidden — and it is the reason a mandatory resolve run happened at all. atk_10b (forward fold, extensionally correct, different algorithm) still failed only because I could not discharge its fold lemma without adding top-level lemmas (which would change the spec signature); that is a limitation of MY proof effort, NOT evidence about the spec, and it is not counted as a refutation.

MANDATORY RESOLVE RUN (executed, not speculated). atk_5b_oracle_echo is the only verifying wrong-impl candidate, so its faithful refined patch was materialized at patch_atk_5b.diff. Faithfulness argument: atk_5b's impl is `return rendered value template`, extensionally identical to the reference impl and to the spec's own postcondition, so under the refinement.md map (A1-A4) it refines to precisely the same call-site change — adding `params={'value': value}` to the ValidationError raised in the `except` branch of ModelChoiceField.to_python. Verified `git apply --check` clean against a worktree at base_commit 42e8cf47c7ee2db238bf91197ea398126c546741. Command: `python do_resolve.py atk_5b <patch>` calling swebench_unified.harness.run_resolve('django__django-13933', patch, run_id='sbu-geq-13933-atk_5b', timeout=3600). OBSERVED RESULT: {"completed": true, "resolved": true, "attempts": 1, "flaky": false, "note": "resolved"} (saved to resolve_atk_5b.json). So the one verifying impl DOES resolve — no verify⇏correct witness. Docker oracle was live (benchmark swe_bench_verified, docker ps OK), so this is a real harness verdict, not a skip.

REFINEMENT.MD AUDIT (§4.3). Leg tags: 3x R (A1 template str<->List Frag, A2 value str<->List Char, A4 out<->messages[0]) + 1x A-reference+I (A3, the substitution itself). ZERO kind-3 legs; §B explicitly discharges the changed op as deeply modeled rather than axiomatized. Confirmed NO `axiom` declarations exist anywhere in Solution.lean (regex over the file returns []), and the axioms region is a pure comment — so there is no A-consumed leg and no axiom-soundness trust point to attack. That is the strongest possible posture for this gate: the changed behavior is spelled out as a verified fold, not assumed.

A-LEG CORRESPONDENCE INDEPENDENTLY RE-DERIVED (not merely re-run). Bundle's own axiom_check.py -> exit 0 (17 boundary + 50k fuzz). Bundle's conformance_check.py -> 0 disagreements on 100,018 inputs (seed 13933). Because re-running the author's own script proves little, I wrote my own adversarial differential at my_axref.py: it drives the REAL django path (`ValidationError(fmt, code='invalid_choice', params={'value': value}).messages[0]`, imported from the base_commit worktree) against the deep model `rendered`, over EXHAUSTIVE templates of length 0-3 drawn from a printf-hostile alphabet ('%','','s','v','a','l','u','e','\\','{','}','#','0','d','r','\"','é') crossed with adversarial values ('%', '%(value)s', '%s', '%d', '100%', '{v}', '\\n', 'é•', ''), plus 40k random cases under MY OWN seed 0xBADC0DE (deliberately not the pinned 13933). Result: checked=119640, mismatches/exceptions=0. The A-reference leg holds, including the '%'-doubling bijection detail that atk_14 probed.

WHY THE SPEC IS TIGHT. The postcondition `out = rendered value template` is a total functional characterization over an EMPTY pre-conditions region, so it admits no domain restriction — which is exactly why atk_3 (right on all tested inputs, wrong only off-domain) is rejected. The two corroborating `ensures` are pure-region tautologies and carry no impl obligation on their own (atk_9/atk_16 confirm they cannot rescue an abandoned functional postcondition). The `List Frag` carrier additionally makes an entire real-world bug class (format-string escaping confusion) unrepresentable by construction.

RESIDUAL RISK (stated honestly, does not change the verdict). The spec models only the rendering of the message, taking the template and value as given; it does not model the `try/except` branch selection, the `queryset.get` lookup, or ValidationError construction/storage (refinement.md/mapping.md §1 scope this out explicitly, and the gold patch changes no control flow — it adds one keyword argument). A hypothetical impl that renders correctly but attaches the message to the wrong branch is outside the modeled scope; the gold patch's shape makes that divergence unreachable here, and G-CONF/G-RESOLVE cover the end-to-end path. Flagging for the record, not as a break.

HOUSEKEEPING. All artifacts confined to (attack .lean files, per-attack .log with EXIT=, resolve_atk_5b.json/.log, patch_atk_5b.diff, my_axref.py). The temporary git worktree was removed with `git worktree remove --force`; no tree-wide git operation was performed.

VERDICT: SOUND. 19 distinct same-spec wrong impls run and all rejected; the sole verifying same-spec impl had its faithful patch materialized and EXECUTED through the official harness with resolved=true. No verify⇏correct witness exists for this frozen spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_0_prepatch.lean`, `atk_1_slot_dropped.lean`, `atk_2_offbyone_index.lean`, `atk_3_partial_domain.lean`, `atk_4_control_flow_short.lean`, `atk_5_oracle_echo.lean`, `atk_6_first_slot_only.lean`, `atk_7_value_reversed.lean`, `atk_8_value_truncated.lean`, `atk_9_vacuous_empty.lean`, `atk_10_forward_fold.lean`, +8 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5b_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying same-spec impl has a faithful refined patch that fails to resolve. 19 distinct wrong impls were encoded and machine-checked; every one was REJECTED by lean_verify.sh. The single non-reference impl that verified (atk_5b_oracle_echo, exit 0) is extensionally EQUAL to the spec function (`return rendered value template`), so it carries no behavioral divergence to exploit; its faithful refined patch was materialized and EXECUTED through the official harness: resolved=true, attempts=1, flaky=false. Most notable near-misses, all refuted: (a) atk_3_partial_domain — correct on the ENTIRE tested domain (F2P template has exactly one %(value)s, P2P template has none) and wrong only on multi-placeholder templates; rejected, proving the postcondition is TOTAL over `List Frag` and not narrowed to the tested shape, so the empty pre-conditions region is genuinely load-bearing. (b) atk_12_value_duplicated / atk_7_value_reversed / atk_8_value_truncated — all DO 'expose the offending value' (the issue's stated goal) yet were rejected, showing the spec pins exact character sequence and multiplicity, not mere value presence. (c) atk_14_percent_escaping — the real-world printf escaping bug (emitting '%%' for a literal '%'); rejected, and independently confirmed harmless because the `List Frag` carrier makes format-string escaping unrepresentable by construction. (d) atk_15b_nontermination — diverges on exactly the F2P input; rejected under `termination "total"` even with a fair, adapted proof script.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_slot_dropped.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2_offbyone_index.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_control_flow_short.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_oracle_echo.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_5b_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_6_first_slot_only.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_7_value_reversed.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_8_value_truncated.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_9_vacuous_empty.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_10_forward_fold.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_10b_forward_fold.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_11_literal_corrupted.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_12_value_duplicated.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_13_message_reversed.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_14_percent_escaping.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_15_nontermination.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_15b_nontermination.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_16_value_only.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The rendering of a parametrized message — the
--  substitution of the offending value into the value placeholder — is the one
--  operation that changes, and it is modeled DEEPLY below (`rendered`), then
--  validated == the real string-interpolation builtin out-of-band by
--  axiom_check.py (G-AX). There is no unchanged callee whose contract the proof
--  must assume.)
-- axioms-end

-- pure-start
/- A fragment of a parametrized message: either a literal code point that passes
   through verbatim, or the value placeholder slot that stands for the offending
   submitted value. A message template is a sequence of such fragments — the
   abstract shape of a human-readable message with a single named substitution
   parameter. -/
inductive Frag where
  | lit (c : Char)
  | valueSlot
  deriving Inhabited, DecidableEq, Repr

/- The rendering of one fragment under a given value: a literal contributes its
   one code point; the value slot is FILLED with the value's code points. This is
   the substitution the parametrized message performs — the placeholder is
   replaced by the value, not left standing. -/
def renderFrag (value : List Char) : Frag → List Char
  | .lit c     => [c]
  | .valueSlot => value

/- The rendering of a whole template under a value: concatenate the per-fragment
   renderings left to right. Front-recursive so a single unfold is available per
   loop step (the Velvet fold pattern). -/
def rendered (value : List Char) : List Frag → List Char
  | []      => []
  | f :: fs => renderFrag value f ++ rendered value fs

@[grind] lemma rendered_nil (value : List Char) : rendered value [] = [] := rfl
@[grind] lemma rendered_cons (value : List Char) (f : Frag) (fs : List Frag) :
    rendered value (f :: fs) = renderFrag value f ++ rendered value fs := rfl

/- Behavioral anchors (definitional). A lone value slot renders to EXACTLY the
   value — the placeholder is substituted, never echoed literally — and a lone
   literal renders to exactly that one code point. Marked `@[grind]` so
   `loom_solve` discharges the corroborating postconditions automatically. -/
@[grind] lemma rendered_valueSlot (value : List Char) :
    rendered value [Frag.valueSlot] = value := by simp [rendered, renderFrag]
@[grind] lemma rendered_lit (value : List Char) (c : Char) :
    rendered value [Frag.lit c] = [c] := by simp [rendered, renderFrag]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When an invalid choice is rejected, the human-readable rejection message is
   produced by interpolating the offending submitted value into the message
   template. The template is a sequence of fragments (literal code points and a
   value placeholder slot); rendering substitutes the offending value at the
   placeholder and passes every literal through unchanged.

   The guarantee the issue demands: the rendered message is the template with the
   value FILLED IN at the placeholder — so a template that carries a value slot
   exposes the offending value, rather than leaving the placeholder standing
   uninterpreted.

   `template` and `value` are read-only (not `mut`): the rendering builds a fresh
   character sequence and mutates neither input (directive 5). -/
method renderInvalidChoice (template : List Frag) (value : List Char) return (out : List Char)
  ensures out = rendered value template
  ensures rendered value [Frag.valueSlot] = value
  ensures ∀ c, rendered value [Frag.lit c] = [c]
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := template.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ template.length
      invariant result = rendered value (template.drop i)
      done_with i = 0
      decreasing i
    do
      let f := template[i - 1]!
      result := renderFrag value f ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the fragment at
   `i-1` on the front, so `rendered` peels one `renderFrag`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma rendered_drop_step (value : List Char) (template : List Frag) (i : Nat)
    (hi : 0 < i) (hle : i ≤ template.length) :
    rendered value (template.drop (i - 1)) =
      renderFrag value template[i - 1]! ++ rendered value (template.drop i) := by
  have hlt : i - 1 < template.length := by omega
  have hcons : template.drop (i - 1) = template[i - 1]! :: template.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, rendered_cons]

prove_correct renderInvalidChoice by
  loom_solve
  rw [rendered_drop_step value template i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLIANCE. Same-spec: ALL 20 attack files + positive control return True from swebench_unified.markers.same_spec against the frozen Solution.lean (axioms/pure/pre/post regions byte-identical; only the impl region — and, where noted, the elided `prove_correct` body — differ). Verify cmd for each: `bash scripts/lean_verify.sh <file>`. Run 4-at-a-time as concurrent background jobs per instructions.

BASELINES. pos_control.lean (unmodified Solution.lean) -> exit 0 (verifies, no sorry). atk_0_prepatch.lean (bundle's Solution_prepatch.lean) -> exit 1, PREPATCH REPRODUCED: the unsolved goal is exactly the value-slot clause, `(match ... | Frag.valueSlot => ['%','(','v','a','l','u','e',')','s']) = renderFrag value ...` — i.e. the placeholder left standing verbatim, which is precisely the real bug (pre-patch raised ValidationError with no `params`, so `__iter__` skipped `message %= error.params`). G-DIFF confirmed.

ATTACK LEDGER (0=verifies, 1=rejected). atk_0_prepatch 1 | atk_1_slot_dropped (slot->[], params={} mis-fix) 1 | atk_2_offbyone_index (template[i]! fencepost, OOB read) 1 | atk_3_partial_domain (correct iff <=1 placeholder) 1 | atk_4_control_flow_short (loop halts at i=1, drops leading char) 1 | atk_5_oracle_echo (inherited proof) 1 | atk_5b_oracle_echo (adapted proof) **0 = VERIFIES** | atk_6_first_slot_only (replace-once mis-fix) 1 | atk_7_value_reversed 1 | atk_8_value_truncated (value.drop 1) 1 | atk_9_vacuous_empty (counter starts 0, body never runs) 1 | atk_10_forward_fold (inherited proof) 1 | atk_10b_forward_fold (adapted proof) 1 | atk_11_literal_corrupted (drops quote literals) 1 | atk_12_value_duplicated 1 | atk_13_message_reversed (append vs prepend) 1 | atk_14_percent_escaping 1 | atk_15_nontermination (inherited proof) 1 | atk_15b_nontermination (adapted proof) 1 | atk_16_value_only (return value) 1. Coverage spans every class required: partial-domain (3), boundary (2,8,11,14), control-flow-effect (4,9,13,15b), ungrounded-oracle-echo (5,5b,16), plus value-carrier corruption (7,12) and the prepatch bug (0).

FAIRNESS NOTE (important). Three attacks (5, 10, 15) initially failed with proof-script artifacts rather than genuine spec rejections — the spec view elides `prove_correct` bodies, so a legitimate consumer supplies its own proof, and inheriting the reference's tactic script is not a fair refutation. I re-ran all three with adapted proofs (5b, 10b, 15b). This is what surfaced the one verifying impl (5b, exit 0) that the naive run would have hidden — and it is the reason a mandatory resolve run happened at all. atk_10b (forward fold, extensionally correct, different algorithm) still failed only because I could not discharge its fold lemma without adding top-level lemmas (which would change the spec signature); that is a limitation of MY proof effort, NOT evidence about the spec, and it is not counted as a refutation.

MANDATORY RESOLVE RUN (executed, not speculated). atk_5b_oracle_echo is the only verifying wrong-impl candidate, so its faithful refined patch was materialized at patch_atk_5b.diff. Faithfulness argument: atk_5b's impl is `return rendered value template`, extensionally identical to the reference impl and to the spec's own postcondition, so under the refinement.md map (A1-A4) it refines to precisely the same call-site change — adding `params={'value': value}` to the ValidationError raised in the `except` branch of ModelChoiceField.to_python. Verified `git apply --check` clean against a worktree at base_commit 42e8cf47c7ee2db238bf91197ea398126c546741. Command: `python do_resolve.py atk_5b <patch>` calling swebench_unified.harness.run_resolve('django__django-13933', patch, run_id='sbu-geq-13933-atk_5b', timeout=3600). OBSERVED RESULT: {"completed": true, "resolved": true, "attempts": 1, "flaky": false, "note": "resolved"} (saved to resolve_atk_5b.json). So the one verifying impl DOES resolve — no verify⇏correct witness. Docker oracle was live (benchmark swe_bench_verified, docker ps OK), so this is a real harness verdict, not a skip.

REFINEMENT.MD AUDIT (§4.3). Leg tags: 3x R (A1 template str<->List Frag, A2 value str<->List Char, A4 out<->messages[0]) + 1x A-reference+I (A3, the substitution itself). ZERO kind-3 legs; §B explicitly discharges the changed op as deeply modeled rather than axiomatized. Confirmed NO `axiom` declarations exist anywhere in Solution.lean (regex over the file returns []), and the axioms region is a pure comment — so there is no A-consumed leg and no axiom-soundness trust point to attack. That is the strongest possible posture for this gate: the changed behavior is spelled out as a verified fold, not assumed.

A-LEG CORRESPONDENCE INDEPENDENTLY RE-DERIVED (not merely re-run). Bundle's own axiom_check.py -> exit 0 (17 boundary + 50k fuzz). Bundle's conformance_check.py -> 0 disagreements on 100,018 inputs (seed 13933). Because re-running the author's own script proves little, I wrote my own adversarial differential at my_axref.py: it drives the REAL django path (`ValidationError(fmt, code='invalid_choice', params={'value': value}).messages[0]`, imported from the base_commit worktree) against the deep model `rendered`, over EXHAUSTIVE templates of length 0-3 drawn from a printf-hostile alphabet ('%','','s','v','a','l','u','e','\\','{','}','#','0','d','r','\"','é') crossed with adversarial values ('%', '%(value)s', '%s', '%d', '100%', '{v}', '\\n', 'é•', ''), plus 40k random cases under MY OWN seed 0xBADC0DE (deliberately not the pinned 13933). Result: checked=119640, mismatches/exceptions=0. The A-reference leg holds, including the '%'-doubling bijection detail that atk_14 probed.

WHY THE SPEC IS TIGHT. The postcondition `out = rendered value template` is a total functional characterization over an EMPTY pre-conditions region, so it admits no domain restriction — which is exactly why atk_3 (right on all tested inputs, wrong only off-domain) is rejected. The two corroborating `ensures` are pure-region tautologies and carry no impl obligation on their own (atk_9/atk_16 confirm they cannot rescue an abandoned functional postcondition). The `List Frag` carrier additionally makes an entire real-world bug class (format-string escaping confusion) unrepresentable by construction.

RESIDUAL RISK (stated honestly, does not change the verdict). The spec models only the rendering of the message, taking the template and value as given; it does not model the `try/except` branch selection, the `queryset.get` lookup, or ValidationError construction/storage (refinement.md/mapping.md §1 scope this out explicitly, and the gold patch changes no control flow — it adds one keyword argument). A hypothetical impl that renders correctly but attaches the message to the wrong branch is outside the modeled scope; the gold patch's shape makes that divergence unreachable here, and G-CONF/G-RESOLVE cover the end-to-end path. Flagging for the record, not as a break.

HOUSEKEEPING. All artifacts confined to (attack .lean files, per-attack .log with EXIT=, resolve_atk_5b.json/.log, patch_atk_5b.diff, my_axref.py). The temporary git worktree was removed with `git worktree remove --force`; no tree-wide git operation was performed.

VERDICT: SOUND. 19 distinct same-spec wrong impls run and all rejected; the sole verifying same-spec impl had its faithful patch materialized and EXECUTED through the official harness with resolved=true. No verify⇏correct witness exists for this frozen spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK: faithfulness-break (spec too strong / drifts from real repo behavior). Could NOT break it. No input exists on the modeled domain where `rendered`/`renderInvalidChoice` disagrees with the real callee.

SETUP: fresh worktree of django/django at base_commit 42e8cf47c7ee2db238bf91197ea398126c546741, gold patch + test_patch applied from data/swe_bench_verified/test.jsonl (patch.diff is absent from the bundle dir; I reconstructed it from the dataset and confirmed it applies cleanly, 5 insertions / 1 deletion in django/forms/models.py).

### Evidence
- Solution.lean verifies: scripts/lean_verify.sh exit 0.
- Solution_prepatch.lean fails exit 1, and fails on EXACTLY the right goal: unsolved `invariant_2: result = rendered value (template.drop i)` with `Frag.valueSlot => ['%','(','v','a','l','u','e',')','s']` vs `renderFrag value valueSlot`. G-DIFF genuinely discriminates.
- swebench_unified.markers.same_spec(Solution, Solution_prepatch) = True with the velvet/lean LanguageTables; spec_signature sha256 prefix 45d5afd6e5907e26a389 identical on both. Spec region is byte-identical.
- G-AX axiom_check.py exit 0; G-CONF conformance_check.py exit 0 (100,018 inputs, seed 13933, 0 disagreements).
- F2P test_modelchoicefield_value_placeholder + all P2P in forms_tests.tests.test_error_messages: 20/20 OK with gold patch.
- My OWN independent probe (not the bundle's script) drove the FULL real path -- a real ModelChoiceField(queryset=User.objects.all(), error_messages={'invalid_choice': fmt}).to_python(value) on a real migrated sqlite DB -- and compared messages[0] to the transliterated `rendered`. 0 rendering divergences across boundaries + 20k fuzz, plus 20k direct ValidationError interpolation checks.

### DIVERGENCE CANDIDATES CHASED AND RULED OUT (4 near-misses):
1. value='' / None / [] -> real path returns None (no error raised at all) while model returns ''. NOT a break: to_python short-circuits on `value in self.empty_values` BEFORE reaching the modeled `except` branch. The model's scope is 'the message rendered GIVEN rejection occurred' (mapping.md 1), which is the correct scope -- the gold patch touches only the except body and alters no control flow. All 6 fuzz 'divergences' my probe reported were this same short-circuit (real=None), not rendering disagreements.
2. Non-str values: 4, 0, 3.5, True, ('a',), ['a'], {'k':1}, custom __str__/__repr__ object, bare object(). ALL matched model(str(v)) exactly -- confirms mapping.md's claim that the str(value) coercion is observationally the identity on the carrier, and it holds well beyond the tested str domain.
3. Lazy translation templates -- gettext_lazy, the ACTUAL runtime type of default_error_messages['invalid_choice']. This was my strongest drift hypothesis (__mod__ on a lazy proxy could differ from str.__mod__). It renders identically. No drift.
4. Lone surrogates U+D800 / U+DFFF, U+0000, U+FFFF, astral U+1F600, in BOTH template literals and values: all matched.

DOC NIT (not a defect, no observable consequence): mapping.md 2 asserts 'on the BMP Char.ofNat (ord ch) <-> ch is total and exact'. Imprecise -- I confirmed in Lean that Char.ofNat 0xD800 = 0 and Char.isValidCharNat 0xD800 = false; surrogates are BMP but are NOT valid Lean Chars. No observable disagreement follows, because Python % passes surrogates through verbatim and the identity holds on every non-surrogate BMP point. Recommend rewording to 'on the BMP minus the surrogate range'.

OUT-OF-SCOPE FINDING FOR A COVERAGE GATE (explicitly NOT my verdict, and NOT a faithfulness break): templates outside the image of the List Frag bijection diverge sharply pre- vs post-patch. Post-patch the real code RAISES on '100% bad', 'bad %(pk)s', '%(value)d' (TypeError), '50%' and '%', and silently misrenders 'Select %s' -> "Select {'value': 'v'}" and '%(value)r' -> "'v'"; pre-patch every one of these rendered verbatim. That is a real regression the gold patch introduces for developers with a literal '%' in a custom invalid_choice message. It is NOT a counterexample to faithfulness because List Frag cannot denote such a template at all -- the bijection encodes a literal '%' as '%%', so it can never become a conversion specifier. It is a domain NARROWING (spec incompleteness), which belongs to a completeness/coverage gate, not to faithfulness. Flagging so the panel can route it.

SPEC-STRENGTH OBSERVATION: `ensures rendered value [Frag.valueSlot] = value` and `ensures forall c, rendered value [Frag.lit c] = [c]` are TAUTOLOGICAL -- they constrain only the pure function `rendered` and never mention `out`, so both are discharged by rfl and impose zero constraint on any implementation. All discriminating content lives in `ensures out = rendered value template` (confirmed by the prepatch failing on the loop invariant that drives it, not on either anchor clause). So the '3 postconditions' are effectively one. This makes the spec no WEAKER than it needs to be for G-DIFF to bite, and certainly not too strong -- it does not over-constrain, so it does not reject the gold patch.

CONCLUSION: the modeled function agrees with the real callee on every input in its domain; the domain restriction is documented in mapping.md 2 and is a narrowing rather than a disagreement. No diverging input to cite, hence diverging_input=null. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SPEC-REGION INTEGRITY (checked first, as instructed): recomputed markers.spec_view(Solution.lean, velvet.language) and region_hashes. spec_view sha256 = 6fab294c4bb555d37f0d77fec285fb1d5037ee97cd584f8e174f65cedb3ad040, byte-identical to meta.json gates.G-HYGIENE.data.region_hashes.spec_view. same_spec(Solution.lean, Solution_prepatch.lean) = True (empty spec-view diff), so the prepatch differs ONLY in impl/proof and the spec region is the frozen one. scripts/lean_verify.sh on Solution.lean exits 0.

MECHANICAL SCREEN: re-ran leakage.screen() with the real frozen row (lean flavor): passed=True, hard_failures=[], warnings=[]. Independently confirmed the screen had real material to bite on: _patch_changed_symbols(gold) = {'to_python'}, _patch_changed_files = ['django/forms/models.py'], and 6 changed lines incl. "params={'value': value},". None of 'to_python', 'models.py', the dotted module path, 'params', 'ValidationError', 'error_messages', 'queryset', 'DoesNotExist', '__iter__', or 'django' occurs anywhere in the spec view. Zero commit hashes, zero repo line numbers, zero 'test_*' names, no diff markers. The single regex hit for 'forms' is the tail of the English word 'performs' (line 31) — a lexer false positive, not the app label. The one '.py' hit is 'axiom_check.py', a harness artifact name, not a repo path.

SEMANTIC PASS (the part the lexical screen cannot do). The strongest leak candidates I pressed on, and why each dies against the PUBLIC problem_statement (hints_text deliberately excluded):

(1) 'the placeholder is replaced by the value, not left standing' and 'a template that carries a value slot exposes the offending value, rather than leaving the placeholder standing uninterpreted'. This is the closest call — it contrasts post-state against pre-state, i.e. it edges toward bug->fix narration. It nonetheless adds nothing beyond public text: the problem_statement itself states the defect ('ModelChoiceField does not show the value of the invalid choice when raising a validation error'), states the remedy verbatim ('Passing in parameters with the invalid value and modifying the default error message for the code invalid_choice should fix this'), AND quotes the '%(value)s' placeholder template from ModelMultipleChoiceField's default_error_messages. Given a public template containing %(value)s plus a public 'does not show the value', 'the placeholder is left standing uninterpreted' is a restatement, not a disclosure. The gold MECHANISM (add params={'value': value} to the ValidationError call) is never named, and the spec view never says where the change lives.

(2) The identifier 'renderInvalidChoice' — 'invalid_choice' is explicitly public ('the code invalid_choice'), so no edit-localization is conferred.

(3) Hints-only vocabulary audit: I diffed spec-view word set against hints_text minus problem_statement, yielding ['given','literal','literally','offending','passes','than']. All are ordinary English, not technical discriminators; 'offending value' is a plain synonym for the public 'the invalid value' / 'value of the invalid choice'. No hints-only symbol or term is echoed.

(4) Hidden-test leakage: F2P literals do NOT appear — 'available choices' absent, 'not one of' absent, the test's template string absent, the test name absent. 'invalid' appears only as the public phrase 'invalid choice', never as the test's input literal in a way that reveals the case.

(5) The spec is genuinely abstracted: the carrier is List Frag / List Char with Frag.lit / Frag.valueSlot, and the operation is a generic template-render fold. A solver reading it learns 'a rejection message must interpolate the offending value at its placeholder' — which is precisely the public issue — not 'add a params kwarg at django/forms/models.py:1284'.

BOUNDARY NOTE (scoping, not a finding): meta.json modeled_functions DOES disclose repo_symbol 'django.forms.models.ModelChoiceField.to_python' and repo_location 'django/forms/models.py:1284', and mapping.md spells out the gold kwarg params={'value': value}. Neither is spec-view content: modeled_functions is the deliberate mode-gated edit-localization aid (eval/dataset.py gives_localization / prompts.py), and mapping.md is a private bundle file whose reads eval/audit.py flags as 'our-bundle-access'. Both are outside this gate; I flag them only so the scoping is explicit rather than silently assumed.

Bundle-layout deviation from the task brief (non-substantive): patch.diff lives at the instance dir, not velvet/; velvet/ also carries Solution_prepatch.lean, meta.json, properties.py, axiom_check.py, conformance_check.py, verdict.md. Unrelated observation, outside my gate: meta.json records gates.G-EQ status=fail ('INCONCLUSIVE - only 0 attacks (need >= 5)').

CONCLUSION: the spec view discloses nothing about the gold edit that the public problem_statement does not already state. Verdict NO-LEAKAGE, with (1) recorded as the nearest miss for the panel's record.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — pydata__xarray-4966

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,9 +123,16 @@
   ensures out = decodeModel kind bits attr values
   do
     -- impl-start
-    -- Decide the elementwise reinterpretation and the resulting kind from the
-    -- element kind and the attribute, then map it over the elements.
-    let cm := chooseMode kind attr bits
+    let cm : CastMode × IntKind :=
+      match attr with
+      | none   => (CastMode.keep, kind)
+      | some v =>
+        match kind with
+        | IntKind.signedInt =>
+            if v = "true".toList then (CastMode.toUnsigned bits, IntKind.unsignedInt)
+            else (CastMode.keep, kind)
+        | IntKind.unsignedInt => (CastMode.keep, kind)
+        | IntKind.other => (CastMode.keep, kind)
     let m := cm.1
     let k' := cm.2
     let mut result : List Int := []
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,14 +123,12 @@
   ensures out = decodeModel kind bits attr values
   do
     -- impl-start
-    -- Decide the elementwise reinterpretation and the resulting kind from the
-    -- element kind and the attribute, then map it over the elements.
     let cm := chooseMode kind attr bits
     let m := cm.1
     let k' := cm.2
     let mut result : List Int := []
     let mut i := values.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ values.length
       invariant result = castSeq m (values.drop i)
       done_with i = 0
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,8 +123,6 @@
   ensures out = decodeModel kind bits attr values
   do
     -- impl-start
-    -- Decide the elementwise reinterpretation and the resulting kind from the
-    -- element kind and the attribute, then map it over the elements.
     let cm := chooseMode kind attr bits
     let m := cm.1
     let k' := cm.2
@@ -138,7 +136,7 @@
     do
       let x := values[i - 1]!
       result := applyCast m x :: result
-      i := i - 1
+      i := i
     return { values := result, kind := k' }
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,11 +123,8 @@
   ensures out = decodeModel kind bits attr values
   do
     -- impl-start
-    -- Decide the elementwise reinterpretation and the resulting kind from the
-    -- element kind and the attribute, then map it over the elements.
     let cm := chooseMode kind attr bits
     let m := cm.1
-    let k' := cm.2
     let mut result : List Int := []
     let mut i := values.length
     while i > 0
@@ -139,7 +136,7 @@
       let x := values[i - 1]!
       result := applyCast m x :: result
       i := i - 1
-    return { values := result, kind := k' }
+    return { values := result, kind := kind }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,9 +123,18 @@
   ensures out = decodeModel kind bits attr values
   do
     -- impl-start
-    -- Decide the elementwise reinterpretation and the resulting kind from the
-    -- element kind and the attribute, then map it over the elements.
-    let cm := chooseMode kind attr bits
+    let cm : CastMode × IntKind :=
+      match attr with
+      | none   => (CastMode.keep, kind)
+      | some v =>
+        match kind with
+        | IntKind.signedInt =>
+            if v = "true".toList then (CastMode.toUnsigned bits, IntKind.unsignedInt)
+            else (CastMode.keep, kind)
+        | IntKind.unsignedInt =>
+            if v = "false".toList then (CastMode.toUnsigned bits, IntKind.signedInt)
+            else (CastMode.keep, kind)
+        | IntKind.other => (CastMode.keep, kind)
     let m := cm.1
     let k' := cm.2
     let mut result : List Int := []
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,23 +123,7 @@
   ensures out = decodeModel kind bits attr values
   do
     -- impl-start
-    -- Decide the elementwise reinterpretation and the resulting kind from the
-    -- element kind and the attribute, then map it over the elements.
-    let cm := chooseMode kind attr bits
-    let m := cm.1
-    let k' := cm.2
-    let mut result : List Int := []
-    let mut i := values.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ values.length
-      invariant result = castSeq m (values.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let x := values[i - 1]!
-      result := applyCast m x :: result
-      i := i - 1
-    return { values := result, kind := k' }
+    return { values := values, kind := kind }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -159,5 +143,4 @@
 
 prove_correct decodeUnsigned by
   loom_solve
-  rw [castSeq_drop_step (chooseMode kind attr bits).1 values i (by omega) (by omega)]
   simp_all
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,23 +123,7 @@
   ensures out = decodeModel kind bits attr values
   do
     -- impl-start
-    -- Decide the elementwise reinterpretation and the resulting kind from the
-    -- element kind and the attribute, then map it over the elements.
-    let cm := chooseMode kind attr bits
-    let m := cm.1
-    let k' := cm.2
-    let mut result : List Int := []
-    let mut i := values.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ values.length
-      invariant result = castSeq m (values.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let x := values[i - 1]!
-      result := applyCast m x :: result
-      i := i - 1
-    return { values := result, kind := k' }
+    return decodeModel kind bits attr values
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -159,5 +143,3 @@
 
 prove_correct decodeUnsigned by
   loom_solve
-  rw [castSeq_drop_step (chooseMode kind attr bits).1 values i (by omega) (by omega)]
-  simp_all
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,10 +123,10 @@
   ensures out = decodeModel kind bits attr values
   do
     -- impl-start
-    -- Decide the elementwise reinterpretation and the resulting kind from the
-    -- element kind and the attribute, then map it over the elements.
     let cm := chooseMode kind attr bits
-    let m := cm.1
+    let m : CastMode := match kind with
+      | IntKind.unsignedInt => CastMode.keep
+      | _ => cm.1
     let k' := cm.2
     let mut result : List Int := []
     let mut i := values.length
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The only library operation this routine relies on is the
-- elementwise integer reinterpretation between same-width signed/unsigned
-- representations; it is modeled DEEPLY (`applyCast`/`castSeq`, pure region) and
-- validated == the real array-casting callee by axiom_check.py (G-AX,
-- A-reference). See mapping.md §3.
-- axioms-end

-- pure-start
/- The integer-element kind of a numeric array: a two's-complement signed
   integer, an unsigned integer, or anything else (a non-integer element type
   for which no reinterpretation applies). -/
inductive IntKind where
  | signedInt
  | unsignedInt
  | other
  deriving Inhabited, DecidableEq, Repr

/- How a single element is reinterpreted under a width of `bits` binary digits:
   reinterpret the same bit pattern as unsigned, reinterpret it as signed, or
   leave it untouched. First-order, mirroring the single transform object the
   routine builds once and then maps over the data. -/
inductive CastMode where
  | toUnsigned (bits : Nat)
  | toSigned (bits : Nat)
  | keep
  deriving Inhabited, DecidableEq, Repr

/- The result of the routine: the reinterpreted element values, in order, and the
   element kind they now carry. -/
structure Decoded where
  values : List Int
  kind : IntKind
  deriving Inhabited, DecidableEq, Repr

/- Reinterpret one integer element. `toUnsigned bits` maps a negative value into
   the non-negative range of width `bits` by adding `2 ^ bits` (the wrap-around
   that puts the identical bit pattern into the unsigned range); a value already
   non-negative is unchanged. `toSigned bits` is its inverse: a value at or above
   `2 ^ (bits - 1)` (the top half of the unsigned range, i.e. the values whose
   high bit is set) is mapped down by `2 ^ bits` into the negative range; a value
   below the midpoint is unchanged. `keep` is the identity. -/
@[grind] def applyCast : CastMode → Int → Int
  | CastMode.toUnsigned bits, x => if x < 0 then x + (2 : Int) ^ bits else x
  | CastMode.toSigned bits,   x => if x ≥ (2 : Int) ^ (bits - 1) then x - (2 : Int) ^ bits else x
  | CastMode.keep,            x => x

/- Reinterpret a whole element sequence: apply the chosen mode to each element,
   in order. Front-recursive so a single unfold is available per loop step (the
   fold pattern, plan §5.4). -/
def castSeq (m : CastMode) : List Int → List Int
  | []      => []
  | x :: xs => applyCast m x :: castSeq m xs

@[grind] lemma castSeq_nil (m : CastMode) : castSeq m [] = [] := rfl
@[grind] lemma castSeq_cons (m : CastMode) (x : Int) (xs : List Int) :
    castSeq m (x :: xs) = applyCast m x :: castSeq m xs := rfl

/- The transform to apply and the resulting element kind, decided by the element
   kind and the optional attribute string.

   * No attribute present: nothing is reinterpreted; the kind is preserved.
   * Attribute present with a value `v`:
       - signed elements are reinterpreted as unsigned exactly when `v = "true"`;
       - unsigned elements are reinterpreted as signed exactly when `v = "false"`;
       - in every other configuration (a non-matching value, a non-integer
         element kind) nothing is reinterpreted and the kind is preserved.
   `bits` is the element width, carried into the chosen reinterpretation. -/
@[grind] def chooseMode (kind : IntKind) (attr : Option (List Char)) (bits : Nat) :
    CastMode × IntKind :=
  match attr with
  | none   => (CastMode.keep, kind)
  | some v =>
    match kind with
    | IntKind.signedInt =>
        if v = "true".toList  then (CastMode.toUnsigned bits, IntKind.unsignedInt)
        else (CastMode.keep, kind)
    | IntKind.unsignedInt =>
        if v = "false".toList then (CastMode.toSigned bits, IntKind.signedInt)
        else (CastMode.keep, kind)
    | IntKind.other => (CastMode.keep, kind)

/- The decoded result: the chosen reinterpretation applied elementwise to the
   values, paired with the resulting element kind. -/
@[grind] def decodeModel (kind : IntKind) (bits : Nat) (attr : Option (List Char))
    (values : List Int) : Decoded :=
  { values := castSeq (chooseMode kind attr bits).1 values,
    kind := (chooseMode kind attr bits).2 }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Reinterpret a numeric array's integer elements according to an optional
   signedness attribute.

   The element kind (`kind`) and element width (`bits`) describe the stored
   representation; `attr` is the optional signedness attribute (its raw string,
   absent when no attribute is set); `values` are the stored element values.

   Desired behavior: when the attribute marks a signed array as logically
   unsigned, the elements are reinterpreted into the unsigned range and the kind
   becomes unsigned; SYMMETRICALLY, when the attribute marks an unsigned array as
   logically signed, the elements are reinterpreted into the signed range and the
   kind becomes signed; in any other configuration the values and the kind are
   returned unchanged. The result is exactly `decodeModel` of the inputs.

   All parameters are read-only inputs (none `mut`): the routine consumes them
   and produces a fresh result (directive 5). -/
method decodeUnsigned (kind : IntKind) (bits : Nat) (attr : Option (List Char))
    (values : List Int) return (out : Decoded)
  ensures out = decodeModel kind bits attr values
  do
    -- impl-start
    -- Decide the elementwise reinterpretation and the resulting kind from the
    -- element kind and the attribute, then map it over the elements.
    let cm := chooseMode kind attr bits
    let m := cm.1
    let k' := cm.2
    let mut result : List Int := []
    let mut i := values.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ values.length
      invariant result = castSeq m (values.drop i)
      done_with i = 0
      decreasing i
    do
      let x := values[i - 1]!
      result := applyCast m x :: result
      i := i - 1
    return { values := result, kind := k' }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `castSeq` peels one `applyCast`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma castSeq_drop_step (m : CastMode) (values : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ values.length) :
    castSeq m (values.drop (i - 1))
      = applyCast m values[i - 1]! :: castSeq m (values.drop i) := by
  have hlt : i - 1 < values.length := by omega
  have hcons : values.drop (i - 1) = values[i - 1]! :: values.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, castSeq_cons]

prove_correct decodeUnsigned by
  loom_solve
  rw [castSeq_drop_step (chooseMode kind attr bits).1 values i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition is a TOTAL functional equality `out = decodeModel kind bits attr values` with NO precondition; the entire pure model (decodeModel/chooseMode/applyCast/castSeq), the castSeq_drop_step lemma, and the postcondition are all inside the frozen spec view (confirmed via markers.spec_view). Total-correctness semantics (loom.semantics.termination "total", loop carries `decreasing i`). This pins any verifying impl to compute exactly decodeModel — a very tight spec.

PROTOCOL: work done All 8 attacks + pos_control confirmed byte-spec-identical via swebench_unified.markers.same_spec == True (only impl/proof regions edited). Verified with `bash scripts/lean_verify.sh <f>` from repo root, run concurrently in batches of <=4.

### RESULTS (exit codes):
- pos_control.lean (correct impl): exit 0 = VERIFIES. Positive control good.
- atk_1 PREPATCH BUG (unsignedInt+"false" -> keep, no elif kind=='u' branch): exit 1 = fails. Prepatch reproduced (the genuine behavioral divergence: unsolved goal is the postcondition).
- atk_2 BOUNDARY off-by-one (`while i > 1`, drops first element): exit 1 = fails.
- atk_3 CONTROL-FLOW-EFFECT non-terminating (`i := i`, no progress): exit 1 = fails — total semantics rejects the vacuous-nonterminating attack (the P1 hole refinement.md documents as closed).
- atk_4 wrong resulting kind (return kind instead of k'): exit 1 = fails (goal `{values:=result_1, kind:=kind} = decodeModel ...`).
- atk_5 wrong cast DIRECTION (unsignedInt+"false" -> toUnsigned): exit 1 = fails.
- atk_6 IDENTITY (return inputs unchanged): exit 1 = fails.
- atk_7 UNGROUNDED-ORACLE ECHO (`return decodeModel kind bits attr values`): exit 0 = VERIFIES. This is the only verifying wrong-impl; it is behaviorally identical to gold (a resolving echo of the oracle, explicitly policy-exempt per 2026-08-06 G-PANEL-1/eq resolve rule).
- atk_8 ASYMMETRIC partial-domain (force keep for unsignedInt): exit 1 = fails.

MANDATORY RESOLVE STEP for the verifying wrong impl (atk_7): materialized its faithful refined patch. atk_7's impl is `return decodeModel ...`; decodeModel for unsignedInt+"false" selects toSigned bits with signed resulting kind — i.e. exactly the gold decode `elif data.dtype.kind=='u'` branch. Faithful patch == patch.diff (gold). Ran through the OFFICIAL harness: `swebench_unified.harness.run_resolve('pydata__xarray-4966', <atk_7.patch>, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, NOTE='resolved'. (Harness runs Docker via `docker`; a bare `docker ps` from the audit shell shows no access but the harness completed and produced a report.) So the sole verifying candidate's faithful patch RESOLVES — verify does NOT imply incorrect here.

REFINEMENT.MD AUDIT (A-legs focus): A1=R (type bijection, mapping §2 — ok). A2=I (chooseMode dispatch == nested if/elif; cross-checked by axiom_check.choose_mode vs patched_decode_branch, 21 configs pass). A3=A-reference+I (deep model applyCast/castSeq == real np.asarray(dtype=...); NO consumed axiom). A4=R (resulting kind k' == returned dtype). §B _FillValue lines correctly identified inert on all F2P inputs (tests build variables with no _FillValue key), guarded no-op, not a hidden kind-3. §C: every leg R/A/I, no kind-3. axiom_check.py run: EXIT 0, 'apply_cast deep model sound on 60 boundary + 40000 fuzz elements over 4 widths; choose_mode dispatch matches patched decode on 21 configs; F2P witness holds' — the A-reference correspondence to the real callee holds.

CONCLUSION: >=5 distinct wrong impls (partial-domain atk_8, boundary atk_2, control-flow-effect atk_3, wrong-kind atk_4, wrong-direction atk_5, identity atk_6, prepatch atk_1) ALL fail to verify; the only verifying candidate (echo atk_7) has a faithful patch that RESOLVES under the official harness. No verify-but-not-resolve witness exists. Spec is a tight total functional equality; verify => resolve holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The only library operation this routine relies on is the
-- elementwise integer reinterpretation between same-width signed/unsigned
-- representations; it is modeled DEEPLY (`applyCast`/`castSeq`, pure region) and
-- validated == the real array-casting callee by axiom_check.py (G-AX,
-- A-reference). See mapping.md §3.
-- axioms-end

-- pure-start
/- The integer-element kind of a numeric array: a two's-complement signed
   integer, an unsigned integer, or anything else (a non-integer element type
   for which no reinterpretation applies). -/
inductive IntKind where
  | signedInt
  | unsignedInt
  | other
  deriving Inhabited, DecidableEq, Repr

/- How a single element is reinterpreted under a width of `bits` binary digits:
   reinterpret the same bit pattern as unsigned, reinterpret it as signed, or
   leave it untouched. First-order, mirroring the single transform object the
   routine builds once and then maps over the data. -/
inductive CastMode where
  | toUnsigned (bits : Nat)
  | toSigned (bits : Nat)
  | keep
  deriving Inhabited, DecidableEq, Repr

/- The result of the routine: the reinterpreted element values, in order, and the
   element kind they now carry. -/
structure Decoded where
  values : List Int
  kind : IntKind
  deriving Inhabited, DecidableEq, Repr

/- Reinterpret one integer element. `toUnsigned bits` maps a negative value into
   the non-negative range of width `bits` by adding `2 ^ bits` (the wrap-around
   that puts the identical bit pattern into the unsigned range); a value already
   non-negative is unchanged. `toSigned bits` is its inverse: a value at or above
   `2 ^ (bits - 1)` (the top half of the unsigned range, i.e. the values whose
   high bit is set) is mapped down by `2 ^ bits` into the negative range; a value
   below the midpoint is unchanged. `keep` is the identity. -/
@[grind] def applyCast : CastMode → Int → Int
  | CastMode.toUnsigned bits, x => if x < 0 then x + (2 : Int) ^ bits else x
  | CastMode.toSigned bits,   x => if x ≥ (2 : Int) ^ (bits - 1) then x - (2 : Int) ^ bits else x
  | CastMode.keep,            x => x

/- Reinterpret a whole element sequence: apply the chosen mode to each element,
   in order. Front-recursive so a single unfold is available per loop step (the
   fold pattern, plan §5.4). -/
def castSeq (m : CastMode) : List Int → List Int
  | []      => []
  | x :: xs => applyCast m x :: castSeq m xs

@[grind] lemma castSeq_nil (m : CastMode) : castSeq m [] = [] := rfl
@[grind] lemma castSeq_cons (m : CastMode) (x : Int) (xs : List Int) :
    castSeq m (x :: xs) = applyCast m x :: castSeq m xs := rfl

/- The transform to apply and the resulting element kind, decided by the element
   kind and the optional attribute string.

   * No attribute present: nothing is reinterpreted; the kind is preserved.
   * Attribute present with a value `v`:
       - signed elements are reinterpreted as unsigned exactly when `v = "true"`;
       - unsigned elements are reinterpreted as signed exactly when `v = "false"`;
       - in every other configuration (a non-matching value, a non-integer
         element kind) nothing is reinterpreted and the kind is preserved.
   `bits` is the element width, carried into the chosen reinterpretation. -/
@[grind] def chooseMode (kind : IntKind) (attr : Option (List Char)) (bits : Nat) :
    CastMode × IntKind :=
  match attr with
  | none   => (CastMode.keep, kind)
  | some v =>
    match kind with
    | IntKind.signedInt =>
        if v = "true".toList  then (CastMode.toUnsigned bits, IntKind.unsignedInt)
        else (CastMode.keep, kind)
    | IntKind.unsignedInt =>
        if v = "false".toList then (CastMode.toSigned bits, IntKind.signedInt)
        else (CastMode.keep, kind)
    | IntKind.other => (CastMode.keep, kind)

/- The decoded result: the chosen reinterpretation applied elementwise to the
   values, paired with the resulting element kind. -/
@[grind] def decodeModel (kind : IntKind) (bits : Nat) (attr : Option (List Char))
    (values : List Int) : Decoded :=
  { values := castSeq (chooseMode kind attr bits).1 values,
    kind := (chooseMode kind attr bits).2 }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Reinterpret a numeric array's integer elements according to an optional
   signedness attribute.

   The element kind (`kind`) and element width (`bits`) describe the stored
   representation; `attr` is the optional signedness attribute (its raw string,
   absent when no attribute is set); `values` are the stored element values.

   Desired behavior: when the attribute marks a signed array as logically
   unsigned, the elements are reinterpreted into the unsigned range and the kind
   becomes unsigned; SYMMETRICALLY, when the attribute marks an unsigned array as
   logically signed, the elements are reinterpreted into the signed range and the
   kind becomes signed; in any other configuration the values and the kind are
   returned unchanged. The result is exactly `decodeModel` of the inputs.

   All parameters are read-only inputs (none `mut`): the routine consumes them
   and produces a fresh result (directive 5). -/
method decodeUnsigned (kind : IntKind) (bits : Nat) (attr : Option (List Char))
    (values : List Int) return (out : Decoded)
  ensures out = decodeModel kind bits attr values
  do
    -- impl-start
    -- Decide the elementwise reinterpretation and the resulting kind from the
    -- element kind and the attribute, then map it over the elements.
    let cm := chooseMode kind attr bits
    let m := cm.1
    let k' := cm.2
    let mut result : List Int := []
    let mut i := values.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ values.length
      invariant result = castSeq m (values.drop i)
      done_with i = 0
      decreasing i
    do
      let x := values[i - 1]!
      result := applyCast m x :: result
      i := i - 1
    return { values := result, kind := k' }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `castSeq` peels one `applyCast`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma castSeq_drop_step (m : CastMode) (values : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ values.length) :
    castSeq m (values.drop (i - 1))
      = applyCast m values[i - 1]! :: castSeq m (values.drop i) := by
  have hlt : i - 1 < values.length := by omega
  have hcons : values.drop (i - 1) = values[i - 1]! :: values.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, castSeq_cons]

prove_correct decodeUnsigned by
  loom_solve
  rw [castSeq_drop_step (chooseMode kind attr bits).1 values i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition is a TOTAL functional equality `out = decodeModel kind bits attr values` with NO precondition; the entire pure model (decodeModel/chooseMode/applyCast/castSeq), the castSeq_drop_step lemma, and the postcondition are all inside the frozen spec view (confirmed via markers.spec_view). Total-correctness semantics (loom.semantics.termination "total", loop carries `decreasing i`). This pins any verifying impl to compute exactly decodeModel — a very tight spec.

PROTOCOL: work done All 8 attacks + pos_control confirmed byte-spec-identical via swebench_unified.markers.same_spec == True (only impl/proof regions edited). Verified with `bash scripts/lean_verify.sh <f>` from repo root, run concurrently in batches of <=4.

### RESULTS (exit codes):
- pos_control.lean (correct impl): exit 0 = VERIFIES. Positive control good.
- atk_1 PREPATCH BUG (unsignedInt+"false" -> keep, no elif kind=='u' branch): exit 1 = fails. Prepatch reproduced (the genuine behavioral divergence: unsolved goal is the postcondition).
- atk_2 BOUNDARY off-by-one (`while i > 1`, drops first element): exit 1 = fails.
- atk_3 CONTROL-FLOW-EFFECT non-terminating (`i := i`, no progress): exit 1 = fails — total semantics rejects the vacuous-nonterminating attack (the P1 hole refinement.md documents as closed).
- atk_4 wrong resulting kind (return kind instead of k'): exit 1 = fails (goal `{values:=result_1, kind:=kind} = decodeModel ...`).
- atk_5 wrong cast DIRECTION (unsignedInt+"false" -> toUnsigned): exit 1 = fails.
- atk_6 IDENTITY (return inputs unchanged): exit 1 = fails.
- atk_7 UNGROUNDED-ORACLE ECHO (`return decodeModel kind bits attr values`): exit 0 = VERIFIES. This is the only verifying wrong-impl; it is behaviorally identical to gold (a resolving echo of the oracle, explicitly policy-exempt per 2026-08-06 G-PANEL-1/eq resolve rule).
- atk_8 ASYMMETRIC partial-domain (force keep for unsignedInt): exit 1 = fails.

MANDATORY RESOLVE STEP for the verifying wrong impl (atk_7): materialized its faithful refined patch. atk_7's impl is `return decodeModel ...`; decodeModel for unsignedInt+"false" selects toSigned bits with signed resulting kind — i.e. exactly the gold decode `elif data.dtype.kind=='u'` branch. Faithful patch == patch.diff (gold). Ran through the OFFICIAL harness: `swebench_unified.harness.run_resolve('pydata__xarray-4966', <atk_7.patch>, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, NOTE='resolved'. (Harness runs Docker via `docker`; a bare `docker ps` from the audit shell shows no access but the harness completed and produced a report.) So the sole verifying candidate's faithful patch RESOLVES — verify does NOT imply incorrect here.

REFINEMENT.MD AUDIT (A-legs focus): A1=R (type bijection, mapping §2 — ok). A2=I (chooseMode dispatch == nested if/elif; cross-checked by axiom_check.choose_mode vs patched_decode_branch, 21 configs pass). A3=A-reference+I (deep model applyCast/castSeq == real np.asarray(dtype=...); NO consumed axiom). A4=R (resulting kind k' == returned dtype). §B _FillValue lines correctly identified inert on all F2P inputs (tests build variables with no _FillValue key), guarded no-op, not a hidden kind-3. §C: every leg R/A/I, no kind-3. axiom_check.py run: EXIT 0, 'apply_cast deep model sound on 60 boundary + 40000 fuzz elements over 4 widths; choose_mode dispatch matches patched decode on 21 configs; F2P witness holds' — the A-reference correspondence to the real callee holds.

CONCLUSION: >=5 distinct wrong impls (partial-domain atk_8, boundary atk_2, control-flow-effect atk_3, wrong-kind atk_4, wrong-direction atk_5, identity atk_6, prepatch atk_1) ALL fail to verify; the only verifying candidate (echo atk_7) has a faithful patch that RESOLVES under the official harness. No verify-but-not-resolve witness exists. Spec is a tight total functional equality; verify => resolve holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pydata__xarray-4966 velvet. Verdict: FAITHFUL — no realizable input where decodeModel disagrees with the real UnsignedIntegerCoder.decode.

Evidence:
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True; spec region (axioms/pure/pre/post: IntKind, CastMode, Decoded, applyCast, castSeq, chooseMode, decodeModel + method signature/ensures) is stable and frozen. Lean verifies (lean_verify.sh exit 0): impl provably equals decodeModel.
2. Pure reinterpret model vs real numpy: applyCast(toSigned/toUnsigned bits) == np.asarray(dtype=iN/uN) elementwise over all four widths (8/16/32/64), all boundary values (0,-1,max,midpoint 2^(bits-1),+/-1), and 2000+ fuzz per width. 0 mismatches.
3. End-to-end integration vs real decode (base_commit worktree, patched to gold): 70 configs across kinds i/u/other x every dtype x attrs {none,'true','false','True','yes','1','0'}. Model's chosen transform, resulting kind, and reinterpreted values all match real decode. 0 mismatches. Confirms the chooseMode dispatch is neither too strong nor too weak: only (signedInt,'true') and (unsignedInt,'false') reinterpret; every other attr value / kind keeps values+kind, matching the real nested if/elif and the 'else' warn branch (which leaves data unchanged).

Drift considerations examined and rejected:
- _FillValue re-cast omitted from model, but Decoded observes only {values,kind}; F2P constructs no _FillValue, branch is inert; modeled observables still match. Scope choice, not drift.
- decodeModel is total (no preconditions) over List Int incl. out-of-range ints (e.g. 2^bits for u8). Such values are NOT realizable through the type bijection (a numpy uN/iN array element cannot hold them), so no genuine repo divergence. applyCast's if-threshold semantics coincide with two's-complement wrap only on in-range inputs, which is exactly the realizable domain — verified by fuzz staying in-range.
- Total-correctness semantics correctly required (closes while-True vacuous verify); real decode is a single finite pass, always terminates.

No diverging input found on the realizable domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction) on velvet/pydata__xarray-4966.

Gold edit: add `elif data.dtype.kind == "u": if unsigned == "false": signed_dtype = np.dtype("i%s"%itemsize); transform = partial(np.asarray, dtype=signed_dtype); data = lazy_elemwise_func(...)` (+ inert _FillValue re-cast) in UnsignedIntegerCoder.decode, variables.py.

Mechanical checks (reproduced):
- adapter.spec_view(Solution.lean) elides impl-region + prove_correct body correctly (impl shows only the elided marker); pure/axioms/contracts pass through.
- leakage.screen() against the SOLVER-VISIBLE problem_statement PASSES: no hard failures, no warnings. No diff markers, no reproduced gold-patch line (>=8 chars), no patched file path/module path, no narration terms, no spec-view identifier or comment embedding a distinctive patched symbol.
- _patch_changed_symbols = {'decode'} only; 'decode' is already public in problem_statement (decode_cf_variable in the traceback), so identifiers decodeUnsigned/decodeModel/etc. are exempted correctly.
- same_spec(Solution, Solution_prepatch) = True (frozen spec region legitimate).

Semantic (beyond-problem_statement) judgment: the spec_view is a behavioral specification (decodeModel/chooseMode/applyCast) of the DESIRED end-state behavior. The public problem_statement ALREADY discloses, more concretely than the spec: the exact edit location (variables.py#L311), the exact fix condition verbatim ('handled symmetrically at the same place (i.e. `if .kind == "u" and unsigned == False`)'), that the i->u direction is already handled while u->i is the missing 'hack', and the observable outcome (unsigned bytes with _Unsigned=False decode to negative values). The spec adds no localization, no diff shape, no file-path detail beyond that. It encodes the symmetric dispatch and per-element two's-complement reinterpret which is precisely the behavior the issue requests. Comments are abstract ('Desired behavior...'), with no bug/fix/pre-patch narration.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

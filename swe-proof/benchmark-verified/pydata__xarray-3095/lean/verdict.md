# P2 adversarial audit — pydata__xarray-3095

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_1_hard.lean`, `atk_2_hard.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl has a closing clean-axiom proof, so there is no faithful patch to materialize/resolve. problem_spec_copy pins ALL FIVE observable fields (dims, attrs, values, native, dtype) to the input verbatim and independent of deep, forcing any verifying impl to be gold-equivalent. Machine-checked falsity witness for the ungrounded-oracle echo (atk_2, dtype:=Dtype.object): theorem correct_copy_is_false verifies (exit 0) with v having dtype=unicode 3, native=object, so result.data.dtype=object != unicode 3.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,14 +71,13 @@
 
 -- impl-start
 def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
-  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
-  -- it on a shallow copy (content is identical either way), and re-attach the
-  -- ORIGINAL stored element type rather than re-deriving one.
   let mut arr := v.data.values
+  let mut dt := v.data.dtype
   if deep then
     arr := v.data.values
+    dt := v.data.native
   let newData : IndexData :=
-    { values := arr, native := v.data.native, dtype := v.data.dtype }
+    { values := arr, native := v.data.native, dtype := dt }
   return { dims := v.dims, attrs := v.attrs, data := newData }
 -- impl-end
 
@@ -88,5 +87,5 @@
       problem_spec_copy deep v (implementation_copy deep v) := by
   intro deep v
   unfold problem_spec_copy implementation_copy
-  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  cases deep <;> simp_all <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,16 +70,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
-  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
-  -- it on a shallow copy (content is identical either way), and re-attach the
-  -- ORIGINAL stored element type rather than re-deriving one.
-  let mut arr := v.data.values
-  if deep then
-    arr := v.data.values
-  let newData : IndexData :=
-    { values := arr, native := v.data.native, dtype := v.data.dtype }
-  return { dims := v.dims, attrs := v.attrs, data := newData }
+def implementation_copy (deep : Bool) (v : IVar) : IVar :=
+  { dims := v.dims, attrs := v.attrs,
+    data := { values := v.data.values, native := v.data.native, dtype := Dtype.object } }
 -- impl-end
 
 -- proof-start
@@ -88,5 +81,5 @@
       problem_spec_copy deep v (implementation_copy deep v) := by
   intro deep v
   unfold problem_spec_copy implementation_copy
-  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  cases deep <;> simp_all <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,16 +70,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
-  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
-  -- it on a shallow copy (content is identical either way), and re-attach the
-  -- ORIGINAL stored element type rather than re-deriving one.
-  let mut arr := v.data.values
-  if deep then
-    arr := v.data.values
-  let newData : IndexData :=
-    { values := arr, native := v.data.native, dtype := v.data.dtype }
-  return { dims := v.dims, attrs := v.attrs, data := newData }
+def implementation_copy (deep : Bool) (v : IVar) : IVar :=
+  { dims := v.dims, attrs := v.attrs,
+    data := { values := v.data.values, native := v.data.dtype, dtype := v.data.native } }
 -- impl-end
 
 -- proof-start
@@ -88,5 +81,5 @@
       problem_spec_copy deep v (implementation_copy deep v) := by
   intro deep v
   unfold problem_spec_copy implementation_copy
-  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  cases deep <;> simp_all <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,16 +70,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
-  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
-  -- it on a shallow copy (content is identical either way), and re-attach the
-  -- ORIGINAL stored element type rather than re-deriving one.
-  let mut arr := v.data.values
-  if deep then
-    arr := v.data.values
-  let newData : IndexData :=
-    { values := arr, native := v.data.native, dtype := v.data.dtype }
-  return { dims := v.dims, attrs := v.attrs, data := newData }
+def implementation_copy (deep : Bool) (v : IVar) : IVar :=
+  let arr := if deep then v.data.values.drop 1 else v.data.values
+  { dims := v.dims, attrs := v.attrs,
+    data := { values := arr, native := v.data.native, dtype := v.data.dtype } }
 -- impl-end
 
 -- proof-start
@@ -88,5 +82,5 @@
       problem_spec_copy deep v (implementation_copy deep v) := by
   intro deep v
   unfold problem_spec_copy implementation_copy
-  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  cases deep <;> simp_all <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,16 +70,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
-  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
-  -- it on a shallow copy (content is identical either way), and re-attach the
-  -- ORIGINAL stored element type rather than re-deriving one.
-  let mut arr := v.data.values
-  if deep then
-    arr := v.data.values
-  let newData : IndexData :=
-    { values := arr, native := v.data.native, dtype := v.data.dtype }
-  return { dims := v.dims, attrs := v.attrs, data := newData }
+def implementation_copy (deep : Bool) (v : IVar) : IVar :=
+  match deep with
+  | false => { dims := v.dims, attrs := v.attrs, data := v.data }
+  | true  => { dims := v.dims, attrs := v.attrs,
+               data := { values := v.data.values, native := v.data.native,
+                         dtype := v.data.native } }
 -- impl-end
 
 -- proof-start
@@ -88,5 +84,5 @@
       problem_spec_copy deep v (implementation_copy deep v) := by
   intro deep v
   unfold problem_spec_copy implementation_copy
-  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  cases deep <;> simp_all <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,16 +70,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
-  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
-  -- it on a shallow copy (content is identical either way), and re-attach the
-  -- ORIGINAL stored element type rather than re-deriving one.
-  let mut arr := v.data.values
-  if deep then
-    arr := v.data.values
-  let newData : IndexData :=
-    { values := arr, native := v.data.native, dtype := v.data.dtype }
-  return { dims := v.dims, attrs := v.attrs, data := newData }
+def implementation_copy (deep : Bool) (v : IVar) : IVar :=
+  { dims := v.dims, attrs := [],
+    data := { values := v.data.values, native := v.data.native, dtype := v.data.dtype } }
 -- impl-end
 
 -- proof-start
@@ -88,5 +81,5 @@
       problem_spec_copy deep v (implementation_copy deep v) := by
   intro deep v
   unfold problem_spec_copy implementation_copy
-  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  cases deep <;> simp_all <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,16 +70,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
-  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
-  -- it on a shallow copy (content is identical either way), and re-attach the
-  -- ORIGINAL stored element type rather than re-deriving one.
-  let mut arr := v.data.values
-  if deep then
-    arr := v.data.values
-  let newData : IndexData :=
-    { values := arr, native := v.data.native, dtype := v.data.dtype }
-  return { dims := v.dims, attrs := v.attrs, data := newData }
+def implementation_copy (deep : Bool) (v : IVar) : IVar :=
+  { dims := v.dims, attrs := v.attrs,
+    data := { values := v.data.values.reverse, native := v.data.native, dtype := v.data.dtype } }
 -- impl-end
 
 -- proof-start
@@ -88,5 +81,5 @@
       problem_spec_copy deep v (implementation_copy deep v) := by
   intro deep v
   unfold problem_spec_copy implementation_copy
-  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  cases deep <;> simp_all <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 8 — `atk_1_hard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,14 +71,13 @@
 
 -- impl-start
 def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
-  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
-  -- it on a shallow copy (content is identical either way), and re-attach the
-  -- ORIGINAL stored element type rather than re-deriving one.
   let mut arr := v.data.values
+  let mut dt := v.data.dtype
   if deep then
     arr := v.data.values
+    dt := v.data.native
   let newData : IndexData :=
-    { values := arr, native := v.data.native, dtype := v.data.dtype }
+    { values := arr, native := v.data.native, dtype := dt }
   return { dims := v.dims, attrs := v.attrs, data := newData }
 -- impl-end
 
@@ -88,5 +87,6 @@
       problem_spec_copy deep v (implementation_copy deep v) := by
   intro deep v
   unfold problem_spec_copy implementation_copy
-  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  cases deep <;> refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;>
+    first | rfl | simp_all | (try decide) | tauto
 -- proof-end
```

Attack 9 — `atk_2_hard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,16 +70,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
-  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
-  -- it on a shallow copy (content is identical either way), and re-attach the
-  -- ORIGINAL stored element type rather than re-deriving one.
-  let mut arr := v.data.values
-  if deep then
-    arr := v.data.values
-  let newData : IndexData :=
-    { values := arr, native := v.data.native, dtype := v.data.dtype }
-  return { dims := v.dims, attrs := v.attrs, data := newData }
+def implementation_copy (deep : Bool) (v : IVar) : IVar :=
+  { dims := v.dims, attrs := v.attrs,
+    data := { values := v.data.values, native := v.data.native, dtype := Dtype.object } }
 -- impl-end
 
 -- proof-start
@@ -88,5 +81,6 @@
       problem_spec_copy deep v (implementation_copy deep v) := by
   intro deep v
   unfold problem_spec_copy implementation_copy
-  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  cases deep <;> refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;>
+    first | rfl | simp_all | (try decide) | tauto
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Copying an index-backed array value.

An index-backed array is a wrapper around a sequence of element values together
with an explicitly recorded element type (its `dtype`). The element type is a
distinct, stored attribute of the wrapper: it can be finer-grained than what one
would re-derive purely from the underlying sequence (for instance a fixed-width
text element type carries information that a re-derivation would flatten to the
generic catch-all element type).

Copying such a wrapper — whether a deep copy (its values are duplicated) or a
shallow copy (its values are shared) — must reproduce the value faithfully: the
copy carries the same element values, the same underlying-sequence element type,
and crucially the same *stored* element type as the original. Copying never
re-derives the element type from the sequence; it preserves the one that was
recorded. Surrounding metadata of the containing variable (its dimension names
and its attributes) is likewise carried over unchanged.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Copying is spelled out
-- concretely: the value sequence is carried over (content-preserving for both
-- deep and shallow copies) and every recorded attribute is reproduced verbatim.
-- axioms-end

-- pure-start
/-- A recorded element type. `unicode w` is a fixed-width text element type of
width `w`; `object` is the generic catch-all element type; `other code` is any
other concrete element type (identified by a code). -/
inductive Dtype
  | unicode (width : Nat)
  | object
  | other (code : Nat)
  deriving DecidableEq

/-- An index-backed array value: a sequence of element values, the element type
reported by the underlying sequence (`native`), and the separately recorded
element type of the wrapper (`dtype`). -/
structure IndexData where
  values : List String
  native : Dtype
  dtype  : Dtype

/-- A variable wrapping an index-backed array, with its dimension names and
attributes alongside the data. -/
structure IVar where
  dims  : List String
  attrs : List (String × String)
  data  : IndexData
-- pure-end

-- post-conditions-start
/-- A copy (`deep` or shallow) of an index-backed variable reproduces every
component of the original: same dimension names, same attributes, same element
values, same underlying-sequence element type, and the same *stored* element
type. The stored element type is preserved as recorded — never re-derived from
the sequence. -/
def problem_spec_copy (deep : Bool) (v : IVar) (result : IVar) : Prop :=
  result.dims = v.dims ∧
  result.attrs = v.attrs ∧
  result.data.values = v.data.values ∧
  result.data.native = v.data.native ∧
  result.data.dtype = v.data.dtype
-- post-conditions-end

-- impl-start
def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
  -- it on a shallow copy (content is identical either way), and re-attach the
  -- ORIGINAL stored element type rather than re-deriving one.
  let mut arr := v.data.values
  if deep then
    arr := v.data.values
  let newData : IndexData :=
    { values := arr, native := v.data.native, dtype := v.data.dtype }
  return { dims := v.dims, attrs := v.attrs, data := newData }
-- impl-end

-- proof-start
theorem correct_copy :
    ∀ (deep : Bool) (v : IVar),
      problem_spec_copy deep v (implementation_copy deep v) := by
  intro deep v
  unfold problem_spec_copy implementation_copy
  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROJECT ROOT USED: (its lean_shared/.lake is the fully-built 3.9G workspace with Mathlib.olean). Confirmed pos_gold verifies exit=0 only under the /fsx root; all reported runs used /fsx.

SAME_SPEC: all 7 attacks + pos_gold report True via swebench_unified.markers.same_spec (lean backend); spec/axioms/pure/pre/post regions byte-identical to gold, only impl+proof differ.

COMMANDS (run concurrently <=4): bash scripts/lean_verify.sh <file>.

RESULTS (exit code): pos_gold=0; atk_1=1; atk_2=1; atk_3=1; atk_4=1; atk_5=1; atk_6=1; atk_7=1. Hardened re-attempts with maximally-powerful shared proof (cases deep <;> refine 5 goals <;> first|rfl|simp_all|decide|tauto): atk_1_hard exit=1 'unsolved goals' line 87; atk_2_hard exit=1 'unsolved goals' line 81. All attack failures are genuine goal-closure failures (unsolved goals / type mismatch), not import/syntax errors.

AXIOMS: pos_ax.lean (pos_gold + '#print axioms correct_copy') prints 'correct_copy does not depend on any axioms' -- clean, no sorryAx.

FALSITY WITNESS: atk_2_disproof.lean (atk_2 impl + theorem correct_copy_is_false) verifies exit=0, machine-proving atk_2's correct_copy goal is genuinely FALSE (not merely hard to prove).

ATTACK CLASSES COVERED (>=6 distinct): atk_1 prepatch-bug (deep re-derives dtype:=native); atk_2 ungrounded-oracle echo (dtype:=object always); atk_3 control-flow-effect (swap native<->dtype); atk_4 boundary (drop 1 element on deep); atk_5 partial-domain (only shallow faithful, deep re-derives); atk_6 metadata-drop (attrs:=[]); atk_7 values-mangled (reverse).

WHY SOUND: spec pins all five observables to input verbatim => only gold-equivalent impls verify => no verify-but-incorrect impl exists => verify=>correct holds. Since zero same-spec wrong impls close, the resolve-run leg of the falsification protocol is vacuous (nothing to materialize). patches={} accordingly.

REFINEMENT.MD AUDIT: rows are R / A-reference / I only; no kind-3 (blind axiom) legs; axioms region is empty (no consumed callee axiom, G-AX is a skip stub). Sole A-reference (dtype re-attach <-> PandasIndexAdapter(array, self._dtype)) validated by G-CONF against the real patched IndexVariable.copy (meta.json G-CONF pass; conformance_check.py: checked=120010, disagreements=0). native pinned to input = the value the buggy deep path leaks into dtype; pinning both discriminates the fix. Correspondence holds.

NOTE ON RECORDED G-EQ FAIL: meta.json records G-EQ fail 'INCONCLUSIVE -- 3 attacks inconclusive', a prior-pass protocol artifact (fail-closed), NOT a demonstrated spec weakness. This adversarial pass ran the attacks to completion and found none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_1_hard.lean`, `atk_2_hard.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl has a closing clean-axiom proof, so there is no faithful patch to materialize/resolve. problem_spec_copy pins ALL FIVE observable fields (dims, attrs, values, native, dtype) to the input verbatim and independent of deep, forcing any verifying impl to be gold-equivalent. Machine-checked falsity witness for the ungrounded-oracle echo (atk_2, dtype:=Dtype.object): theorem correct_copy_is_false verifies (exit 0) with v having dtype=unicode 3, native=object, so result.data.dtype=object != unicode 3.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_1_hard.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_2_hard.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Copying an index-backed array value.

An index-backed array is a wrapper around a sequence of element values together
with an explicitly recorded element type (its `dtype`). The element type is a
distinct, stored attribute of the wrapper: it can be finer-grained than what one
would re-derive purely from the underlying sequence (for instance a fixed-width
text element type carries information that a re-derivation would flatten to the
generic catch-all element type).

Copying such a wrapper — whether a deep copy (its values are duplicated) or a
shallow copy (its values are shared) — must reproduce the value faithfully: the
copy carries the same element values, the same underlying-sequence element type,
and crucially the same *stored* element type as the original. Copying never
re-derives the element type from the sequence; it preserves the one that was
recorded. Surrounding metadata of the containing variable (its dimension names
and its attributes) is likewise carried over unchanged.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Copying is spelled out
-- concretely: the value sequence is carried over (content-preserving for both
-- deep and shallow copies) and every recorded attribute is reproduced verbatim.
-- axioms-end

-- pure-start
/-- A recorded element type. `unicode w` is a fixed-width text element type of
width `w`; `object` is the generic catch-all element type; `other code` is any
other concrete element type (identified by a code). -/
inductive Dtype
  | unicode (width : Nat)
  | object
  | other (code : Nat)
  deriving DecidableEq

/-- An index-backed array value: a sequence of element values, the element type
reported by the underlying sequence (`native`), and the separately recorded
element type of the wrapper (`dtype`). -/
structure IndexData where
  values : List String
  native : Dtype
  dtype  : Dtype

/-- A variable wrapping an index-backed array, with its dimension names and
attributes alongside the data. -/
structure IVar where
  dims  : List String
  attrs : List (String × String)
  data  : IndexData
-- pure-end

-- post-conditions-start
/-- A copy (`deep` or shallow) of an index-backed variable reproduces every
component of the original: same dimension names, same attributes, same element
values, same underlying-sequence element type, and the same *stored* element
type. The stored element type is preserved as recorded — never re-derived from
the sequence. -/
def problem_spec_copy (deep : Bool) (v : IVar) (result : IVar) : Prop :=
  result.dims = v.dims ∧
  result.attrs = v.attrs ∧
  result.data.values = v.data.values ∧
  result.data.native = v.data.native ∧
  result.data.dtype = v.data.dtype
-- post-conditions-end

-- impl-start
def implementation_copy (deep : Bool) (v : IVar) : IVar := Id.run do
  -- Copy the wrapped index value: duplicate the sequence on a deep copy, share
  -- it on a shallow copy (content is identical either way), and re-attach the
  -- ORIGINAL stored element type rather than re-deriving one.
  let mut arr := v.data.values
  if deep then
    arr := v.data.values
  let newData : IndexData :=
    { values := arr, native := v.data.native, dtype := v.data.dtype }
  return { dims := v.dims, attrs := v.attrs, data := newData }
-- impl-end

-- proof-start
theorem correct_copy :
    ∀ (deep : Bool) (v : IVar),
      problem_spec_copy deep v (implementation_copy deep v) := by
  intro deep v
  unfold problem_spec_copy implementation_copy
  cases deep <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROJECT ROOT USED: (its lean_shared/.lake is the fully-built 3.9G workspace with Mathlib.olean). Confirmed pos_gold verifies exit=0 only under the /fsx root; all reported runs used /fsx.

SAME_SPEC: all 7 attacks + pos_gold report True via swebench_unified.markers.same_spec (lean backend); spec/axioms/pure/pre/post regions byte-identical to gold, only impl+proof differ.

COMMANDS (run concurrently <=4): bash scripts/lean_verify.sh <file>.

RESULTS (exit code): pos_gold=0; atk_1=1; atk_2=1; atk_3=1; atk_4=1; atk_5=1; atk_6=1; atk_7=1. Hardened re-attempts with maximally-powerful shared proof (cases deep <;> refine 5 goals <;> first|rfl|simp_all|decide|tauto): atk_1_hard exit=1 'unsolved goals' line 87; atk_2_hard exit=1 'unsolved goals' line 81. All attack failures are genuine goal-closure failures (unsolved goals / type mismatch), not import/syntax errors.

AXIOMS: pos_ax.lean (pos_gold + '#print axioms correct_copy') prints 'correct_copy does not depend on any axioms' -- clean, no sorryAx.

FALSITY WITNESS: atk_2_disproof.lean (atk_2 impl + theorem correct_copy_is_false) verifies exit=0, machine-proving atk_2's correct_copy goal is genuinely FALSE (not merely hard to prove).

ATTACK CLASSES COVERED (>=6 distinct): atk_1 prepatch-bug (deep re-derives dtype:=native); atk_2 ungrounded-oracle echo (dtype:=object always); atk_3 control-flow-effect (swap native<->dtype); atk_4 boundary (drop 1 element on deep); atk_5 partial-domain (only shallow faithful, deep re-derives); atk_6 metadata-drop (attrs:=[]); atk_7 values-mangled (reverse).

WHY SOUND: spec pins all five observables to input verbatim => only gold-equivalent impls verify => no verify-but-incorrect impl exists => verify=>correct holds. Since zero same-spec wrong impls close, the resolve-run leg of the falsification protocol is vacuous (nothing to materialize). patches={} accordingly.

REFINEMENT.MD AUDIT: rows are R / A-reference / I only; no kind-3 (blind axiom) legs; axioms region is empty (no consumed callee axiom, G-AX is a skip stub). Sole A-reference (dtype re-attach <-> PandasIndexAdapter(array, self._dtype)) validated by G-CONF against the real patched IndexVariable.copy (meta.json G-CONF pass; conformance_check.py: checked=120010, disagreements=0). native pinned to input = the value the buggy deep path leaks into dtype; pinning both discriminates the fix. Correspondence holds.

NOTE ON RECORDED G-EQ FAIL: meta.json records G-EQ fail 'INCONCLUSIVE -- 3 attacks inconclusive', a prior-pass protocol artifact (fail-closed), NOT a demonstrated spec weakness. This adversarial pass ran the attacks to completion and found none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on the spec for pydata__xarray-3095 (lean). CONCLUSION: FAITHFUL — no diverging input found; the modeled function does NOT drift from the real post-patch callee.

Setup verification:
- Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True. spec_view elides only impl+proof; imports/axioms(empty)/pure/post-conditions identical across patched & prepatch.
- Compiles: scripts/lean_verify.sh Solution.lean -> exit 0, no sorry (only an unused-variable `deep` linter warning). #print axioms correct_copy -> 'does not depend on any axioms' (no sorryAx; proof is genuine).

Modeled function = IndexVariable.copy on the data=None path (variable.py:1919-1959 @ base 1757dff). Spec problem_spec_copy asserts result preserves all five observables: dims, attrs, values, native (dtype re-derived from the pandas index), and the STORED dtype (self._data._dtype). The discriminating clause is result.data.dtype = v.data.dtype (fix keeps recorded dtype; buggy prepatch substitutes native).

Independent differential (my own harness, not the bundle's conformance_check.py): applied gold3095.patch to base worktree, imported the REAL patched xarray.core.variable.IndexVariable, built variables and read back (dims, attrs, values, _data._dtype, re-derived native).
- Discrete catalogue incl. the regression case <U3 deep=True: OK — real dtype=(unicode,3), native=(object,), exactly what the fix preserves; prepatch would leak object. <U1/<U7 unicode, int64, float64, deep & shallow: all OK.
- 20,000 randomized fuzz inputs (unicode widths 1/3/7, int64, float64, deep/shallow, empty value lists n=0, with/without attrs): 0 disagreements. Every spec clause held on the real callee for every input.
- Recorded bundle G-CONF (120k inputs, SEED=20240711) = pass, consistent.

The modeling domain (1-D pandas-index-backed values encoded as List String; Dtype = unicode w | object | other code; data=None path only) is honestly disclosed in mapping.md/refinement.md and matches the callee. The spec is not too strong: I could not construct any input where the modeled output disagrees with the real patched IndexVariable.copy. The dtype-preservation clause correctly and faithfully discriminates the fix from the bug.

Scope note: G-PANEL-2 recorded FAITHFUL/pass; unrelated recorded fails (G-PANEL-1 SOUND-echo, G-EQ) are outside the faithfulness-break role and were not the target of this attack.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lean spec view for pydata__xarray-3095 does not leak the gold edit beyond the public problem_statement.

Mechanical G-LEAK screen (leakage.screen over spec_view) PASSES with zero hard failures. same_spec(Solution, Solution_prepatch)=True; spec region byte-identical.

Semantic review of the consumer-visible spec view (docstring + Dtype/IndexData/IVar structures + problem_spec_copy; impl and proof regions elided):
- No diff markers, no patched file paths (indexing.py/variable.py), no patched module path, no reproduced gold-patch line, and NONE of the patched repo symbols (PandasIndexAdapter, IndexVariable, copy, self._dtype, safe_cast_to_index) appear in the spec view. No bug/fix narration (no 'bug'/'fix'/'regression'/'previously' etc.).
- The public problem_statement ALREADY discloses the full observable: copy(deep=True) casts <U* (fixed-width unicode) index dtype to object, deep=False unaffected, and the desired behavior is that the unicode dtype be preserved (it shows <U3 before vs object after). The spec's abstraction — a wrapper whose *stored* element type (dtype) is distinct from a re-derivable underlying-sequence type (native), where a fixed-width text type flattens to a generic catch-all on re-derivation — is a faithful abstract model of exactly that public observation, not a disclosure of the edit mechanism.
- The postcondition clause result.data.dtype = v.data.dtype states the correct required behavior (preserve the recorded type). A spec is REQUIRED to state correct behavior; the problem_statement itself demands this, so it is not leakage.

The leaky material (gold-patch quotes, file:line, PandasIndexAdapter(array, self._dtype)) lives only in refinement.md / mapping.md, which are auditor derivation docs, not the consumer spec view, hence out of scope for G-LEAK. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

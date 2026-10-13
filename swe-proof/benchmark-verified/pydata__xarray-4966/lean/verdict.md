# P2 adversarial audit — pydata__xarray-4966

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_swapdir.lean`, `atk_nofill.lean`, `atk_nokind.lean`, `atk_cond.lean`, `atk_boundary.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,12 +131,6 @@
           data := data.map (reinterpAsUnsigned bits)
           kind := Kind.unsigned
           fill := fill.map (reinterpAsUnsigned bits)
-      else if kind = Kind.unsigned then
-        if u = "false" then
-          let bits := 8 * inp.itemsize
-          data := data.map (reinterpAsSigned bits)
-          kind := Kind.signed
-          fill := fill.map (reinterpAsSigned bits)
       return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
 -- impl-end
 
```

Attack 2 — `atk_swapdir.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,15 +128,15 @@
       if kind = Kind.signed then
         if u = "true" then
           let bits := 8 * inp.itemsize
-          data := data.map (reinterpAsUnsigned bits)
+          data := data.map (reinterpAsSigned bits)
           kind := Kind.unsigned
-          fill := fill.map (reinterpAsUnsigned bits)
+          fill := fill.map (reinterpAsSigned bits)
       else if kind = Kind.unsigned then
         if u = "false" then
           let bits := 8 * inp.itemsize
-          data := data.map (reinterpAsSigned bits)
+          data := data.map (reinterpAsUnsigned bits)
           kind := Kind.signed
-          fill := fill.map (reinterpAsSigned bits)
+          fill := fill.map (reinterpAsUnsigned bits)
       return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
 -- impl-end
 
```

Attack 3 — `atk_nofill.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,7 +136,6 @@
           let bits := 8 * inp.itemsize
           data := data.map (reinterpAsSigned bits)
           kind := Kind.signed
-          fill := fill.map (reinterpAsSigned bits)
       return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
 -- impl-end
 
```

Attack 4 — `atk_nokind.lean` → rejected (same spec, does not verify — good)

```diff
@@ -135,7 +135,6 @@
         if u = "false" then
           let bits := 8 * inp.itemsize
           data := data.map (reinterpAsSigned bits)
-          kind := Kind.signed
           fill := fill.map (reinterpAsSigned bits)
       return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
 -- impl-end
```

Attack 5 — `atk_cond.lean` → rejected (same spec, does not verify — good)

```diff
@@ -132,7 +132,7 @@
           kind := Kind.unsigned
           fill := fill.map (reinterpAsUnsigned bits)
       else if kind = Kind.unsigned then
-        if u = "false" then
+        if u = "true" then
           let bits := 8 * inp.itemsize
           data := data.map (reinterpAsSigned bits)
           kind := Kind.signed
```

Attack 6 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,6 +121,10 @@
   let mut data := inp.data
   let mut kind := inp.kind
   let mut fill := inp.fill
+  let reinterpAsSignedBad (bits : Nat) (x : Int) : Int :=
+    let m : Int := (2 : Int) ^ bits
+    let r : Int := x % m
+    if 2 * r > m then r - m else r
   match inp.unsignedAttr with
   | none =>
       return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
@@ -134,9 +138,9 @@
       else if kind = Kind.unsigned then
         if u = "false" then
           let bits := 8 * inp.itemsize
-          data := data.map (reinterpAsSigned bits)
+          data := data.map (reinterpAsSignedBad bits)
           kind := Kind.signed
-          fill := fill.map (reinterpAsSigned bits)
+          fill := fill.map (reinterpAsSignedBad bits)
       return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
 -- impl-end
 
```

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```lean
import Mathlib
-- imports-end

/-!
Reinterpreting an integer array between signed and unsigned representations when
decoding a variable that carries an `_Unsigned` attribute.

Some on-disk integer formats can only store one signedness, so a convention adds
an `_Unsigned` attribute to record the intended signedness of the stored bytes:

* an array physically stored as a *signed* integer of some byte width, tagged
  `_Unsigned = "true"`, actually holds *unsigned* values and must be read back as
  the unsigned integer of the same byte width;
* symmetrically, an array physically stored as an *unsigned* integer, tagged
  `_Unsigned = "false"`, actually holds *signed* values and must be read back as
  the signed integer of the same byte width.

Both directions are a width-preserving two's-complement reinterpretation of the
same bytes (and of the fill value, when one is present): an unsigned value `x` of
`bits` bits is read as the signed value `x - 2^bits` when `x ≥ 2^(bits-1)`, else
`x`; the signed→unsigned direction is the inverse `x mod 2^bits`. Any other case
(no attribute, a non-matching attribute value, or a non-integer array) leaves the
array, its element kind, its byte width and its fill value unchanged.

The desired rule: when the attribute is `"true"` on a signed array, the result is
the unsigned reinterpretation; when it is `"false"` on an unsigned array, the
result is the signed reinterpretation; otherwise the result equals the input
array unchanged. The byte width is always preserved.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- reinterpretation the routine performs is modeled DEEPLY as exact integer
-- arithmetic (a width-preserving two's-complement map applied element-wise and
-- to the fill value), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The element kind of an integer array, restricted to the cases the routine
distinguishes: `signed`, `unsigned`, or anything else (`other`). -/
inductive Kind where
  | signed
  | unsigned
  | other
deriving DecidableEq, Repr

/-- The observable inputs the decision reads.
* `data` — the integer array values;
* `kind` — the array's element kind;
* `itemsize` — the element byte width (`bits = 8 * itemsize`);
* `fill` — the fill value, if any (`none` when absent);
* `unsignedAttr` — the `_Unsigned` attribute value, if present (`none` when absent). -/
structure DecodeInput where
  data : List Int
  kind : Kind
  itemsize : Nat
  fill : Option Int
  unsignedAttr : Option String
deriving Repr

/-- The touched output components: the array values, their element kind, the byte
width, and the fill value. -/
structure DecodeResult where
  data : List Int
  kind : Kind
  itemsize : Nat
  fill : Option Int
deriving DecidableEq, Repr

/-- Read a value stored as an unsigned integer of `bits` bits back as the unsigned
integer of the same width: `x mod 2^bits`. -/
def reinterpAsUnsigned (bits : Nat) (x : Int) : Int :=
  x % ((2 : Int) ^ bits)

/-- Read a value stored as an unsigned integer of `bits` bits back as the signed
integer of the same width: the two's-complement value, i.e. `r - 2^bits` when the
top bit is set (`2 * r ≥ 2^bits`), else `r`, where `r = x mod 2^bits`. -/
def reinterpAsSigned (bits : Nat) (x : Int) : Int :=
  let m : Int := (2 : Int) ^ bits
  let r : Int := x % m
  if 2 * r ≥ m then r - m else r

/-- The desired decision: reinterpret the array (and fill value) according to the
attribute and the array's element kind; otherwise pass the input through. -/
def decodeModel (inp : DecodeInput) : DecodeResult :=
  match inp.unsignedAttr with
  | none =>
      { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
  | some u =>
      match inp.kind with
      | Kind.signed =>
          if u = "true" then
            let bits := 8 * inp.itemsize
            { data := inp.data.map (reinterpAsUnsigned bits),
              kind := Kind.unsigned, itemsize := inp.itemsize,
              fill := inp.fill.map (reinterpAsUnsigned bits) }
          else
            { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
      | Kind.unsigned =>
          if u = "false" then
            let bits := 8 * inp.itemsize
            { data := inp.data.map (reinterpAsSigned bits),
              kind := Kind.signed, itemsize := inp.itemsize,
              fill := inp.fill.map (reinterpAsSigned bits) }
          else
            { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
      | Kind.other =>
          { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
-- pure-end

-- post-conditions-start
/-- The result equals the decision above: every output component (values, element
kind, byte width, fill value) is pinned to the input. The byte width is preserved;
the values and kind change only in the two reinterpreting cases. -/
def problem_spec_unsignedDecode (inp : DecodeInput) (result : DecodeResult) : Prop :=
  result = decodeModel inp
-- post-conditions-end

-- impl-start
def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
-- impl-end

-- proof-start
theorem correct_unsignedDecode :
    ∀ (inp : DecodeInput),
      problem_spec_unsignedDecode inp
        (implementation_unsignedDecode inp) := by
  intro inp
  unfold problem_spec_unsignedDecode implementation_unsignedDecode decodeModel
  simp only [Id.run, bind, pure]
  cases hu : inp.unsignedAttr with
  | none => rfl
  | some u =>
    cases hk : inp.kind with
    | signed => by_cases h : u = "true" <;> simp [h]
    | unsigned => by_cases h : u = "false" <;> simp [h]
    | other => rfl
-- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.lean`

```lean
import Mathlib
-- imports-end

/-!
Reinterpreting an integer array between signed and unsigned representations when
decoding a variable that carries an `_Unsigned` attribute.

Some on-disk integer formats can only store one signedness, so a convention adds
an `_Unsigned` attribute to record the intended signedness of the stored bytes:

* an array physically stored as a *signed* integer of some byte width, tagged
  `_Unsigned = "true"`, actually holds *unsigned* values and must be read back as
  the unsigned integer of the same byte width;
* symmetrically, an array physically stored as an *unsigned* integer, tagged
  `_Unsigned = "false"`, actually holds *signed* values and must be read back as
  the signed integer of the same byte width.

Both directions are a width-preserving two's-complement reinterpretation of the
same bytes (and of the fill value, when one is present): an unsigned value `x` of
`bits` bits is read as the signed value `x - 2^bits` when `x ≥ 2^(bits-1)`, else
`x`; the signed→unsigned direction is the inverse `x mod 2^bits`. Any other case
(no attribute, a non-matching attribute value, or a non-integer array) leaves the
array, its element kind, its byte width and its fill value unchanged.

The desired rule: when the attribute is `"true"` on a signed array, the result is
the unsigned reinterpretation; when it is `"false"` on an unsigned array, the
result is the signed reinterpretation; otherwise the result equals the input
array unchanged. The byte width is always preserved.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- reinterpretation the routine performs is modeled DEEPLY as exact integer
-- arithmetic (a width-preserving two's-complement map applied element-wise and
-- to the fill value), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The element kind of an integer array, restricted to the cases the routine
distinguishes: `signed`, `unsigned`, or anything else (`other`). -/
inductive Kind where
  | signed
  | unsigned
  | other
deriving DecidableEq, Repr

/-- The observable inputs the decision reads.
* `data` — the integer array values;
* `kind` — the array's element kind;
* `itemsize` — the element byte width (`bits = 8 * itemsize`);
* `fill` — the fill value, if any (`none` when absent);
* `unsignedAttr` — the `_Unsigned` attribute value, if present (`none` when absent). -/
structure DecodeInput where
  data : List Int
  kind : Kind
  itemsize : Nat
  fill : Option Int
  unsignedAttr : Option String
deriving Repr

/-- The touched output components: the array values, their element kind, the byte
width, and the fill value. -/
structure DecodeResult where
  data : List Int
  kind : Kind
  itemsize : Nat
  fill : Option Int
deriving DecidableEq, Repr

/-- Read a value stored as an unsigned integer of `bits` bits back as the unsigned
integer of the same width: `x mod 2^bits`. -/
def reinterpAsUnsigned (bits : Nat) (x : Int) : Int :=
  x % ((2 : Int) ^ bits)

/-- Read a value stored as an unsigned integer of `bits` bits back as the signed
integer of the same width: the two's-complement value, i.e. `r - 2^bits` when the
top bit is set (`2 * r ≥ 2^bits`), else `r`, where `r = x mod 2^bits`. -/
def reinterpAsSigned (bits : Nat) (x : Int) : Int :=
  let m : Int := (2 : Int) ^ bits
  let r : Int := x % m
  if 2 * r ≥ m then r - m else r

/-- The desired decision: reinterpret the array (and fill value) according to the
attribute and the array's element kind; otherwise pass the input through. -/
def decodeModel (inp : DecodeInput) : DecodeResult :=
  match inp.unsignedAttr with
  | none =>
      { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
  | some u =>
      match inp.kind with
      | Kind.signed =>
          if u = "true" then
            let bits := 8 * inp.itemsize
            { data := inp.data.map (reinterpAsUnsigned bits),
              kind := Kind.unsigned, itemsize := inp.itemsize,
              fill := inp.fill.map (reinterpAsUnsigned bits) }
          else
            { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
      | Kind.unsigned =>
          if u = "false" then
            let bits := 8 * inp.itemsize
            { data := inp.data.map (reinterpAsSigned bits),
              kind := Kind.signed, itemsize := inp.itemsize,
              fill := inp.fill.map (reinterpAsSigned bits) }
          else
            { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
      | Kind.other =>
          { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
-- pure-end

-- post-conditions-start
/-- The result equals the decision above: every output component (values, element
kind, byte width, fill value) is pinned to the input. The byte width is preserved;
the values and kind change only in the two reinterpreting cases. -/
def problem_spec_unsignedDecode (inp : DecodeInput) (result : DecodeResult) : Prop :=
  result = decodeModel inp
-- post-conditions-end

-- impl-start
def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
-- impl-end

-- proof-start
theorem correct_unsignedDecode :
    ∀ (inp : DecodeInput),
      problem_spec_unsignedDecode inp
        (implementation_unsignedDecode inp) := by
  intro inp
  unfold problem_spec_unsignedDecode implementation_unsignedDecode decodeModel
  simp only [Id.run, bind, pure]
  cases hu : inp.unsignedAttr with
  | none => rfl
  | some u =>
    cases hk : inp.kind with
    | signed => by_cases h : u = "true" <;> simp [h]
    | unsigned => by_cases h : u = "false" <;> simp [h]
    | other => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact-equality post-condition `problem_spec_unsignedDecode inp result := result = decodeModel inp`, pinning every touched output component (data, kind, itemsize, fill) to a single total function decodeModel. By Lean soundness any same-spec impl whose correct_ closes must equal decodeModel extensionally on ALL inputs, so every behaviorally-divergent impl produces a provably-false goal that no tactic can close.

### ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; command: `bash scripts/lean_verify.sh <file>`):
1. atk_prepatch (partial-domain: drops the unsigned->signed branch = the prepatch bug) -> EXIT 1, error 'unsolved goals' at the unsigned&'false' case. Does NOT close.
2. atk_swapdir (control-flow-effect: swaps reinterpAsSigned/reinterpAsUnsigned between the two branches) -> EXIT 1, unsolved goals. Does NOT close.
3. atk_nofill (partial: forgets to map fill in the unsigned branch) -> EXIT 1, unsolved goals. Does NOT close.
4. atk_nokind (partial: forgets to flip kind to .signed in the unsigned branch) -> EXIT 1, unsolved goals. Does NOT close.
5. atk_cond (control-flow: unsigned branch fires on u='true' instead of 'false') -> EXIT 1, unsolved goals. Does NOT close.
6. atk_boundary (boundary: local signed-reinterpret uses strict 2*r>m instead of >=m, off-by-one at the sign-bit boundary) -> EXIT 1, unsolved goals. Does NOT close.
7. atk_echo (ungrounded-oracle echo = byte-identical to gold impl; verified via diff of lines 119-141) -> EXIT 0, closes; #print axioms correct_unsignedDecode = [propext, Quot.sound] (clean, no sorryAx).

Only closing same-spec candidates: positive control (EXIT 0, axioms [propext, Quot.sound]) and atk_echo (= gold impl). Per protocol step 2 the echo's FAITHFUL refined patch (= the gold patch) was MATERIALIZED (patch_echo.diff) and RUN through the official harness: `run_resolve('pydata__xarray-4966', patch, ...)` -> RESOLVED=True, COMPLETED=True, note='resolved'. So the sole verifying alternative RESOLVES; no verify-but-not-resolve candidate found.

NONE of the 6 behaviorally-divergent wrong impls close, so there is no closing-clean-axiom impl with a non-resolving patch. verify => correct holds.

REFINEMENT.MD AUDIT: 7 legs, tags {I, R, R, A-reference, A-reference, R, I} - no kind-3 (no ungrounded axiom leg), axioms=[] correct (no opaque/axiom callee; the changed casts are deep-modeled per SPEC_GUIDE §3, not axiomatized). The two A-reference legs model np.asarray(arr,'uN')/unsigned_dtype.type as reinterpAsUnsigned (x % 2^bits) and np.asarray(arr,'iN')/signed_dtype.type as reinterpAsSigned (two's-complement). Correspondence verified against REAL numpy at all boundaries (0/{1,2,4,8}, min, -1, m/2-1, m/2, m/2+1, m-1) => 0 mismatches, consistent with in-bundle G-CONF (100k inputs, 0 disagreements). deep_model_references in meta.json records both casts. A-leg correspondence holds.

VERDICT: SOUND. >=6 distinct diverging wrong impls run and none closes; the one non-positive closing candidate (echo) has an executed resolving patch.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_swapdir.lean`, `atk_nofill.lean`, `atk_nokind.lean`, `atk_cond.lean`, `atk_boundary.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_swapdir.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_nofill.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_nokind.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_cond.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.lean`

```lean
import Mathlib
-- imports-end

/-!
Reinterpreting an integer array between signed and unsigned representations when
decoding a variable that carries an `_Unsigned` attribute.

Some on-disk integer formats can only store one signedness, so a convention adds
an `_Unsigned` attribute to record the intended signedness of the stored bytes:

* an array physically stored as a *signed* integer of some byte width, tagged
  `_Unsigned = "true"`, actually holds *unsigned* values and must be read back as
  the unsigned integer of the same byte width;
* symmetrically, an array physically stored as an *unsigned* integer, tagged
  `_Unsigned = "false"`, actually holds *signed* values and must be read back as
  the signed integer of the same byte width.

Both directions are a width-preserving two's-complement reinterpretation of the
same bytes (and of the fill value, when one is present): an unsigned value `x` of
`bits` bits is read as the signed value `x - 2^bits` when `x ≥ 2^(bits-1)`, else
`x`; the signed→unsigned direction is the inverse `x mod 2^bits`. Any other case
(no attribute, a non-matching attribute value, or a non-integer array) leaves the
array, its element kind, its byte width and its fill value unchanged.

The desired rule: when the attribute is `"true"` on a signed array, the result is
the unsigned reinterpretation; when it is `"false"` on an unsigned array, the
result is the signed reinterpretation; otherwise the result equals the input
array unchanged. The byte width is always preserved.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- reinterpretation the routine performs is modeled DEEPLY as exact integer
-- arithmetic (a width-preserving two's-complement map applied element-wise and
-- to the fill value), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The element kind of an integer array, restricted to the cases the routine
distinguishes: `signed`, `unsigned`, or anything else (`other`). -/
inductive Kind where
  | signed
  | unsigned
  | other
deriving DecidableEq, Repr

/-- The observable inputs the decision reads.
* `data` — the integer array values;
* `kind` — the array's element kind;
* `itemsize` — the element byte width (`bits = 8 * itemsize`);
* `fill` — the fill value, if any (`none` when absent);
* `unsignedAttr` — the `_Unsigned` attribute value, if present (`none` when absent). -/
structure DecodeInput where
  data : List Int
  kind : Kind
  itemsize : Nat
  fill : Option Int
  unsignedAttr : Option String
deriving Repr

/-- The touched output components: the array values, their element kind, the byte
width, and the fill value. -/
structure DecodeResult where
  data : List Int
  kind : Kind
  itemsize : Nat
  fill : Option Int
deriving DecidableEq, Repr

/-- Read a value stored as an unsigned integer of `bits` bits back as the unsigned
integer of the same width: `x mod 2^bits`. -/
def reinterpAsUnsigned (bits : Nat) (x : Int) : Int :=
  x % ((2 : Int) ^ bits)

/-- Read a value stored as an unsigned integer of `bits` bits back as the signed
integer of the same width: the two's-complement value, i.e. `r - 2^bits` when the
top bit is set (`2 * r ≥ 2^bits`), else `r`, where `r = x mod 2^bits`. -/
def reinterpAsSigned (bits : Nat) (x : Int) : Int :=
  let m : Int := (2 : Int) ^ bits
  let r : Int := x % m
  if 2 * r ≥ m then r - m else r

/-- The desired decision: reinterpret the array (and fill value) according to the
attribute and the array's element kind; otherwise pass the input through. -/
def decodeModel (inp : DecodeInput) : DecodeResult :=
  match inp.unsignedAttr with
  | none =>
      { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
  | some u =>
      match inp.kind with
      | Kind.signed =>
          if u = "true" then
            let bits := 8 * inp.itemsize
            { data := inp.data.map (reinterpAsUnsigned bits),
              kind := Kind.unsigned, itemsize := inp.itemsize,
              fill := inp.fill.map (reinterpAsUnsigned bits) }
          else
            { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
      | Kind.unsigned =>
          if u = "false" then
            let bits := 8 * inp.itemsize
            { data := inp.data.map (reinterpAsSigned bits),
              kind := Kind.signed, itemsize := inp.itemsize,
              fill := inp.fill.map (reinterpAsSigned bits) }
          else
            { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
      | Kind.other =>
          { data := inp.data, kind := inp.kind, itemsize := inp.itemsize, fill := inp.fill }
-- pure-end

-- post-conditions-start
/-- The result equals the decision above: every output component (values, element
kind, byte width, fill value) is pinned to the input. The byte width is preserved;
the values and kind change only in the two reinterpreting cases. -/
def problem_spec_unsignedDecode (inp : DecodeInput) (result : DecodeResult) : Prop :=
  result = decodeModel inp
-- post-conditions-end

-- impl-start
def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
-- impl-end

-- proof-start
theorem correct_unsignedDecode :
    ∀ (inp : DecodeInput),
      problem_spec_unsignedDecode inp
        (implementation_unsignedDecode inp) := by
  intro inp
  unfold problem_spec_unsignedDecode implementation_unsignedDecode decodeModel
  simp only [Id.run, bind, pure]
  cases hu : inp.unsignedAttr with
  | none => rfl
  | some u =>
    cases hk : inp.kind with
    | signed => by_cases h : u = "true" <;> simp [h]
    | unsigned => by_cases h : u = "false" <;> simp [h]
    | other => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact-equality post-condition `problem_spec_unsignedDecode inp result := result = decodeModel inp`, pinning every touched output component (data, kind, itemsize, fill) to a single total function decodeModel. By Lean soundness any same-spec impl whose correct_ closes must equal decodeModel extensionally on ALL inputs, so every behaviorally-divergent impl produces a provably-false goal that no tactic can close.

### ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; command: `bash scripts/lean_verify.sh <file>`):
1. atk_prepatch (partial-domain: drops the unsigned->signed branch = the prepatch bug) -> EXIT 1, error 'unsolved goals' at the unsigned&'false' case. Does NOT close.
2. atk_swapdir (control-flow-effect: swaps reinterpAsSigned/reinterpAsUnsigned between the two branches) -> EXIT 1, unsolved goals. Does NOT close.
3. atk_nofill (partial: forgets to map fill in the unsigned branch) -> EXIT 1, unsolved goals. Does NOT close.
4. atk_nokind (partial: forgets to flip kind to .signed in the unsigned branch) -> EXIT 1, unsolved goals. Does NOT close.
5. atk_cond (control-flow: unsigned branch fires on u='true' instead of 'false') -> EXIT 1, unsolved goals. Does NOT close.
6. atk_boundary (boundary: local signed-reinterpret uses strict 2*r>m instead of >=m, off-by-one at the sign-bit boundary) -> EXIT 1, unsolved goals. Does NOT close.
7. atk_echo (ungrounded-oracle echo = byte-identical to gold impl; verified via diff of lines 119-141) -> EXIT 0, closes; #print axioms correct_unsignedDecode = [propext, Quot.sound] (clean, no sorryAx).

Only closing same-spec candidates: positive control (EXIT 0, axioms [propext, Quot.sound]) and atk_echo (= gold impl). Per protocol step 2 the echo's FAITHFUL refined patch (= the gold patch) was MATERIALIZED (patch_echo.diff) and RUN through the official harness: `run_resolve('pydata__xarray-4966', patch, ...)` -> RESOLVED=True, COMPLETED=True, note='resolved'. So the sole verifying alternative RESOLVES; no verify-but-not-resolve candidate found.

NONE of the 6 behaviorally-divergent wrong impls close, so there is no closing-clean-axiom impl with a non-resolving patch. verify => correct holds.

REFINEMENT.MD AUDIT: 7 legs, tags {I, R, R, A-reference, A-reference, R, I} - no kind-3 (no ungrounded axiom leg), axioms=[] correct (no opaque/axiom callee; the changed casts are deep-modeled per SPEC_GUIDE §3, not axiomatized). The two A-reference legs model np.asarray(arr,'uN')/unsigned_dtype.type as reinterpAsUnsigned (x % 2^bits) and np.asarray(arr,'iN')/signed_dtype.type as reinterpAsSigned (two's-complement). Correspondence verified against REAL numpy at all boundaries (0/{1,2,4,8}, min, -1, m/2-1, m/2, m/2+1, m-1) => 0 mismatches, consistent with in-bundle G-CONF (100k inputs, 0 disagreements). deep_model_references in meta.json records both casts. A-leg correspondence holds.

VERDICT: SOUND. >=6 distinct diverging wrong impls run and none closes; the one non-positive closing candidate (echo) has an executed resolving patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on pydata__xarray-4966/lean. Target: UnsignedIntegerCoder.decode (xarray/coding/variables.py:305-336) integer signed/unsigned two's-complement reinterpretation driven by the _Unsigned attribute. Spec is a total equality problem_spec := (result = decodeModel inp) over the modeled carrier (data:List Int, kind, itemsize, fill).

Checks performed:
1. same_spec(Solution, Solution_prepatch, LeanTables) = True — spec region byte-identical; prepatch differs only in impl/proof (drops the .unsigned∧"false" branch), so the shared spec is legitimate.
2. Lean compiles via lean_verify.sh (exit 0, no sorry). #print axioms correct_unsignedDecode => [propext, Quot.sound] only; no sorryAx, proof genuine.
3. Ran conformance_check.py against the PATCHED worktree (base_commit 37522e99 + the elif data.dtype.kind=='u' fix present at line 319): G-CONF OK, 0/100000 disagreements over fuzzed (values, kind, itemsize, unsigned-attr, fill).
4. Independent numpy probing (numpy 1.26.4): np.asarray(arr,'iN'/'uN') data casts and dtype.type(fill) fill casts across itemsizes {1,2,4,8} and boundary values (0, min, max, max/2±1, -1, wrap) ALL equal reinterpAsSigned/reinterpAsUnsigned — the arithmetic model is exact incl. bits=64. reinterpAsUnsigned = x % 2^bits, reinterpAsSigned = (r:=x%2^bits; r-2^bits if 2r>=2^bits else r) match numpy two's-complement wrap exactly.
5. Case coverage: attr absent (none)→passthrough; non-matching values ('True','False','yes','1','0')→passthrough; .other/float kind→real warns and leaves data unchanged, model passes through (matches). Realizable itemsize domain {1,2,4,8} == fuzzed domain — no unrepresentable real input.

The modeled function decodeModel agrees with the real patched callee on every realizable input in the modeled carrier; dims/encoding/other-attrs are untouched passthrough outside the carrier (patch never reads/writes them). No over-strong constraint and no diverging input found. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True with LeanBackend.language tables); impl and proof are elided from the spec view. The spec view describes the symmetric signed/unsigned two's-complement reinterpretation keyed on (kind=.unsigned, _Unsigned="false") — which is precisely the gold edit (adds `elif data.dtype.kind == "u": if unsigned == "false": ...`). However, this content does NOT leak beyond the PUBLIC problem_statement: the problem_statement itself explicitly names the fix — 'maybe should be handled symmetrically at the same place (i.e. `if .kind == "u" and unsigned == False`)' — and its worked example shows the exact numeric reinterpretation (255->-1, 128->-128, i.e. x - 2^bits when top bit set). The condition (kind==u & _Unsigned=false), the width-preserving signed reinterpretation, and fill-value handling are all publicly disclosed in the problem_statement, not in hints_text (hints are only 'Sounds good to me.') nor derived from the gold diff. The spec is a faithful restatement of publicly-described behavior. No spec-view line reveals gold-edit detail absent from problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

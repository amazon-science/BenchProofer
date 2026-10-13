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
      -- An array stored with an unsigned element kind is left untouched: there is
      -- no branch for that case, so an attribute value of "false" has no effect.
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
-- impl-end

-- proof-start
theorem correct_unsignedDecode :
    ∀ (inp : DecodeInput),
      problem_spec_unsignedDecode inp
        (implementation_unsignedDecode inp) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end

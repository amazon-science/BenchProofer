import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Every operation the
-- modeled routine performs — the leading 30-byte signature compare, the
-- case-insensitive filename-suffix test, and the membership probe on the first
-- positional argument — is modeled DEEPLY below (the suffix test is validated as
-- an A-reference against the real standard-library string operations by G-AX).
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The constant leading byte sequence that marks a FITS stream (its first 30
bytes). Compared against the leading bytes read from a file-like input. -/
def fitsSignature : List Char := "SIMPLE  =                    T".toList

/-- The recognised case-insensitive filename suffixes for a FITS path. -/
def fitsExtensions : List (List Char) :=
  [ ".fits".toList, ".fits.gz".toList, ".fit".toList,
    ".fit.gz".toList, ".fts".toList, ".fts.gz".toList ]

/-- `True` iff `s` ends with at least one of the given suffixes. -/
def endsWithAny (s : List Char) (suffixes : List (List Char)) : Bool :=
  suffixes.any (fun suf => suf.isSuffixOf s)
-- pure-end

-- post-conditions-start
/-- Whether the inputs denote a FITS source, as an `Except` whose `error`
captures the out-of-range access that occurs when no positional argument is
available to probe.

Priority of evidence, highest first:
* a readable input is present (`fileobj`): the result is the boolean comparison
  of its leading 30 bytes against the FITS signature;
* otherwise a path is present (`filepath`): the result is the boolean test of
  whether the lower-cased path ends with a recognised FITS suffix — and this is
  the full answer for a path, whether or not a suffix matches;
* otherwise the answer is the membership flag of the first positional argument,
  and if there is no such argument the access is out of range (`error`).

Every output component is pinned to the inputs (frame discipline): the result is
fully determined by `fileobj`, then `filepath`, then `args`. -/
def problem_spec_isFits (filepath fileobj : Option (List Char)) (args : List Bool)
    (result : Except Unit Bool) : Prop :=
  match fileobj with
  | some content => result = Except.ok (content.take 30 == fitsSignature)
  | none =>
    match filepath with
    | some p => result = Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
    | none =>
      match args with
      | [] => result = Except.error ()
      | a :: _ => result = Except.ok a
-- post-conditions-end

-- impl-start
def implementation_isFits (filepath fileobj : Option (List Char)) (args : List Bool) :
    Except Unit Bool := Id.run do
  if let some content := fileobj then
    return Except.ok (content.take 30 == fitsSignature)
  -- Pre-patch (buggy): a present path only short-circuits when a suffix MATCHES;
  -- a non-matching path falls through to the positional-argument probe, which is
  -- out of range when no positional argument was supplied.
  if let some p := filepath then
    if endsWithAny (p.map Char.toLower) fitsExtensions then
      return Except.ok true
  match args with
  | [] => return Except.error ()
  | a :: _ => return Except.ok a
-- impl-end

-- proof-start
theorem correct_isFits : ∀ (filepath fileobj : Option (List Char)) (args : List Bool),
    problem_spec_isFits filepath fileobj args
      (implementation_isFits filepath fileobj args) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end

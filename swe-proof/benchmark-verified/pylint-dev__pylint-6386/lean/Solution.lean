import Mathlib
-- imports-end

/-!
Early scan of a command-line argument vector against a table of options that are
handled *before* the main parser runs.

Some command-line options must be acted on by a small pre-pass that walks the raw
argument vector left to right. The pre-pass is configured by a table that maps an
option's spelling to whether that option *consumes a following value*. As the
pre-pass walks the vector it classifies each token:

* a token that is not option-like (does not begin with the option marker
  character) is left untouched and copied to the residual vector that the main
  parser will later receive;
* an option-like token is split on its first `=` into a name and an optional
  inline value;
* a name that is not in the table is option-like but unknown to the pre-pass, so
  it too is copied to the residual vector;
* a name that IS in the table is handled here and therefore removed from the
  residual vector. If the option consumes a value and none was given inline, the
  value is taken from the next token — but only if a next token exists and is not
  itself option-like; otherwise the vector is malformed and the scan fails because
  the option expected a value. Conversely, if the option does not consume a value
  yet an inline value was supplied, the scan fails because the option was given a
  value it does not accept.

The result is either a failure describing the offending option, or the residual
vector: exactly those tokens that were neither option-like-and-known nor consumed
as the value of a known option. An option recognised by the table is fully
handled by the pre-pass and never appears in the residual vector. Whether the
option's spelling is short (a single marker character) or long (a doubled marker)
makes no difference: recognition is by table membership, not by the spelling's
length.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The pre-pass is
-- modeled structurally over the input vector and the option table; the side
-- effects each handled option performs are orthogonal to the residual-vector /
-- failure observable modeled here, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A failure of the pre-pass.

* `expectsValue` — a recognised option that consumes a value was given none (no
  inline value and no usable following token);
* `unexpectedValue` — a recognised option that does not consume a value was given
  an inline value. -/
inductive PreError where
  | expectsValue (option : String)
  | unexpectedValue (option : String)
deriving DecidableEq, Repr

/-- Split a token on its FIRST `=`, mirroring a single-split on `=`.

Returns the part before the first `=` together with `some` of everything after it
(rejoined on `=`); if the token contains no `=`, the whole token is the name and
there is no inline value. -/
def splitOnFirstEq (s : String) : String × Option String :=
  match s.splitOn "=" with
  | []        => (s, none)
  | [a]       => (a, none)
  | a :: rest => (a, some (String.intercalate "=" rest))

/-- The intended behavior of the pre-pass: walk `args` left to right against the
option `table` (mapping an option spelling to whether it consumes a value),
returning either a failure or the residual vector of tokens that were not handled
here. A token is option-like exactly when it begins with the marker character
`"-"`. -/
def scanArgsSpec (table : List (String × Bool)) :
    List String → Except PreError (List String)
  | []          => Except.ok []
  | arg :: rest =>
    if !(arg.startsWith "-") then
      (scanArgsSpec table rest).map (arg :: ·)
    else
      let (option, value) := splitOnFirstEq arg
      match table.lookup option with
      | none          => (scanArgsSpec table rest).map (arg :: ·)
      | some takearg  =>
        if takearg && value.isNone then
          match rest with
          | []            => Except.error (PreError.expectsValue option)
          | next :: rest2 =>
            if next.startsWith "-" then
              Except.error (PreError.expectsValue option)
            else
              scanArgsSpec table rest2
        else if (!takearg) && value.isSome then
          Except.error (PreError.unexpectedValue option)
        else
          scanArgsSpec table rest
-- pure-end

-- post-conditions-start
/-- The scan returns exactly the intended residual vector (or the intended
failure) computed by `scanArgsSpec`. -/
def problem_spec_scanArgs
    (table : List (String × Bool)) (args : List String)
    (result : Except PreError (List String)) : Prop :=
  result = scanArgsSpec table args
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

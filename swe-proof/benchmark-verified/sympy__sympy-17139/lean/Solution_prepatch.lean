import Mathlib
-- imports-end

/-!
A guarded rewrite rule for power expressions.

The rule targets an expression only when it is a power whose base is a specific
matching form. For such a matching power the rule applies a rewrite that depends
on the exponent's numeric properties (its sign and magnitude). That rewrite is
only meaningful when the exponent denotes a real quantity: the decisions it makes
are ordering comparisons on the exponent, which are undefined for a non-real
exponent.

The rule therefore behaves as follows:

  * an expression that is not a matching power is returned unchanged;
  * a matching power whose exponent is not a real quantity is returned unchanged;
  * a matching power with a real exponent is returned as the rewrite of that
    power.

Guarding on the exponent being real is what lets the rule leave a matching power
with a non-real exponent untouched instead of attempting an order-based rewrite
that its exponent cannot support.
-/

-- axioms-start
-- Three UNCHANGED outside operations are used identically by the specification
-- and the implementation, so each is carried as an opaque callee and NO property
-- of any is consumed (G-AX skips):
--
--   * `isMatchingPow` — the structural test recognising the expressions this rule
--     acts on (a power whose base has the targeted form). A pure predicate on the
--     expression; its internal structure is out of scope here.
--   * `expIsReal` — the query deciding whether the expression's exponent denotes a
--     real quantity. Carried as an opaque predicate.
--   * `transform` — the exponent-driven rewrite tail applied to a matching power
--     with a real exponent: the WHOLE unchanged body (its sign/magnitude decisions,
--     including the sub-cases that return the input unchanged). Carried opaquely so
--     the result on the real-exponent branch is pinned to its input.
--
-- The expression itself is an opaque carrier: only equality and the two queries
-- above are observed, so it is modelled as a `Nat` tag.
abbrev Expr := Nat
opaque isMatchingPow : Expr → Bool
opaque expIsReal : Expr → Bool
opaque transform : Expr → Expr
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The result of the guarded rewrite: a non-matching expression is unchanged; a
matching power with a non-real exponent is unchanged; a matching power with a real
exponent is the rewrite of that power. -/
def problem_spec_powerRewrite (rv : Expr) (result : Expr) : Prop :=
  (isMatchingPow rv = false → result = rv) ∧
  (isMatchingPow rv = true → expIsReal rv = false → result = rv) ∧
  (isMatchingPow rv = true → expIsReal rv = true → result = transform rv)
-- post-conditions-end

-- impl-start
def implementation_powerRewrite (rv : Expr) : Expr := Id.run do
  if !(isMatchingPow rv) then
    return rv
  return transform rv
-- impl-end

-- proof-start
-- Buggy pre-patch skeleton: the realness guard is absent, so a matching power is
-- transformed regardless of whether its exponent is real. The spec demands a
-- matching power with a NON-real exponent be returned unchanged, so this impl
-- disagrees on exactly that case and `correct_powerRewrite` cannot close.
theorem correct_powerRewrite :
    ∀ (rv : Expr),
      problem_spec_powerRewrite rv (implementation_powerRewrite rv) := by
  sorry
-- proof-end

import Mathlib
-- imports-end

/-!
The hash of an identified object.

An object is created with a stable identity token, set once at construction.
The object may later be attached to an owning container, at which point it also
exposes the owner's identity (a label/name pair). Attachment never alters the
object's own construction-time identity token.

The hash of such an object must be IMMUTABLE: it is required to depend ONLY on
the construction-time identity token, so that placing the object in a hash-based
container before attachment and looking it up after attachment still finds it.
The owner's identity, which only becomes available on attachment, must play no
part in the hash.

The identity token is modeled as an `Int` (a per-instance creation serial;
ordinary objects receive non-negative serials, while auto-created objects
receive serials counting down from `-1`, so the token ranges over ALL of
`Int`); the optional owner identity as an `Option (String × String)`; the hash
result as an `Int`.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The standard hash of an
-- unbounded integer identity token is modeled concretely (`int_hash` below):
-- the magnitude is reduced modulo the Mersenne prime 2^61 - 1, the sign is
-- re-applied, and the reserved output -1 is mapped to -2. This concrete model
-- is recorded in refinement.md and differential-tested against the real callee
-- by G-CONF.
-- axioms-end

-- pure-start
/-- An identified object: a stable construction-time identity token, and the
owner's identity (a label/name pair) once the object has been attached to a
container. `owner = none` models an as-yet-unattached object. -/
structure IdObject where
  serial : Int
  owner : Option (String × String)
deriving Repr, DecidableEq

/-- The standard hash of an unbounded integer: the magnitude is reduced modulo
the Mersenne prime `2^61 - 1` and the sign of the input is re-applied; the
reserved output `-1` is then mapped to `-2`. In particular `int_hash n = n`
for `0 ≤ n < 2^61 - 1`, `int_hash (-1) = -2`, and `int_hash` never returns
`-1`. -/
def int_hash (n : Int) : Int :=
  let m : Int := 2 ^ 61 - 1
  let r : Int := if 0 ≤ n then n % m else -((-n) % m)
  if r = -1 then -2 else r
-- pure-end

-- post-conditions-start
/-- Specification of the object's hash.

The hash is exactly the standard integer hash of the construction-time
identity token. Crucially the owner identity `o.owner` does NOT appear on the
right-hand side: the hash is independent of it, so the hash is immutable
across attachment — an object hashes to the same value before and after it
acquires an owner. -/
def problem_spec_object_hash (o : IdObject) (result : Int) : Prop :=
  result = int_hash o.serial
-- post-conditions-end

-- impl-start
def implementation_object_hash (o : IdObject) : Int := Id.run do
  -- The hash of the construction-time identity token alone; the owner identity
  -- (available only after attachment) is deliberately not consulted.
  return int_hash o.serial
-- impl-end

-- proof-start
theorem correct_object_hash :
    ∀ (o : IdObject), problem_spec_object_hash o (implementation_object_hash o) := by
  intro o
  rfl
-- proof-end

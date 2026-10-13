import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the base membership
-- placeholder and the per-value template substitution are rendered concretely as
-- literal-driven list builds, and the per-backend value-extraction template is
-- modeled DEEPLY (below) rather than axiomatized. The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The database backends whose membership clause is rendered as an SQL string
fragment. `postgresql` stores JSON in a native column type; the other three have
no native JSON column type and must extract the scalar/array out of the stored
text before comparing. -/
inductive Vendor
  | postgresql
  | sqlite
  | mysql
  | mariadb
deriving DecidableEq, Repr

/-- Whether the backend has a native JSON column type. When it does, a stored
value is already a comparable JSON scalar/array, so each membership value is
compared directly; otherwise the stored text must first be passed through the
backend's value-extraction function. -/
def hasNativeJson : Vendor → Bool
  | .postgresql => true
  | .sqlite     => false
  | .mysql      => false
  | .mariadb    => false

/-- The text wrapped around a single bound value placeholder `%s`. For a backend
with a native JSON column type the placeholder is left bare; otherwise the
placeholder is passed through that backend's JSON value-extraction function so
the bound value is compared against the extracted scalar/array. -/
def valueExtractor : Vendor → List Char
  | .postgresql => "%s".toList
  | .sqlite     => "JSON_EXTRACT(%s, '$')".toList
  | .mysql      => "JSON_EXTRACT(%s, '$')".toList
  | .mariadb    => "JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))".toList

/-- The text occupying each of the `n` membership-value slots: the bare
placeholder on a native-JSON backend, otherwise the value-extraction wrapper. -/
def slotFor (vendor : Vendor) : List Char :=
  if hasNativeJson vendor then "%s".toList else valueExtractor vendor

/-- A membership clause over `n` value slots: an opening parenthesis, the `n`
slot texts separated by `", "`, and a closing parenthesis. -/
def buildClause (slot : List Char) (n : Nat) : List Char :=
  "(".toList ++ List.intercalate ", ".toList (List.replicate n slot) ++ ")".toList
-- pure-end

-- post-conditions-start
/-- The rendered membership clause for `n ≥ 1` values on the given backend is
exactly the parenthesised, comma-separated list of `n` value slots, where each
slot is the bare placeholder on a native-JSON backend and the value-extraction
wrapper otherwise. The slot count `n` is pinned to its input and every slot is
pinned to the backend; nothing in the clause is left unconstrained. -/
def problem_spec_inClauseSql (vendor : Vendor) (n : Nat) (result : List Char) : Prop :=
  result = buildClause (slotFor vendor) n
-- post-conditions-end

-- impl-start
def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
  -- Pre-patch (buggy): the membership clause keeps the base bare value slots on
  -- every backend; the value-extraction wrapping is never applied.
  let rhs := buildClause "%s".toList n
  return rhs
-- impl-end

-- proof-start
theorem correct_inClauseSql :
    ∀ (vendor : Vendor) (n : Nat), 1 ≤ n →
    problem_spec_inClauseSql vendor n (implementation_inClauseSql vendor n) := by
  -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
  intro vendor n _hn
  unfold problem_spec_inClauseSql implementation_inClauseSql
  cases vendor <;> rfl
-- proof-end

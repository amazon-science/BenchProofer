import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision below is computed entirely from the
--  column's own observable attributes, each a free boolean input. The
--  presence of a server-side default value (`hasServerDefault`) is the only
--  one obtained from a separate read-only routine; it is observed solely as a
--  boolean ("is a usable default present?") and the spec asserts nothing about
--  how it is produced, so it is taken as a FREE INPUT — there is nothing to
--  validate against a real callee, hence no axiom_check.py / G-AX skip.
--  See mapping.md / refinement.md.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A schema operation adds a new column to an already-existing table. It must
   first decide HOW the column can be materialized: some columns can be appended
   in place with a lightweight column-addition primitive, while others can only
   be introduced by rebuilding the entire table from scratch.

   The desired behavior: the table-rebuild route is required exactly when the
   new column is any of the following kinds, because none of them can be
   appended in place —
     * a column that must carry a uniqueness guarantee (`isUnique`) — this is
       the column's EFFECTIVE uniqueness observation, i.e. whether the column
       must be uniquely valued for any reason;
     * a column that is not allowed to hold an absent value (`!acceptsNull`);
     * a column that supplies a server-side default value (`hasServerDefault`).
   Otherwise — a value-optional column with no default and no uniqueness
   obligation — the in-place column-addition primitive suffices.

   All three inputs are read-only boolean observations of the column (none are
   `mut`); the routine computes a single decision and mutates nothing
   (directive 5). The result is the disjunction of the three rebuild-forcing
   conditions. -/
method requiresTableRebuild
    (isUnique : Bool) (acceptsNull : Bool)
    (hasServerDefault : Bool) return (out : Bool)
  ensures out = (isUnique || !acceptsNull || hasServerDefault)
  do
    -- impl-start
    -- Pre-image skeleton: the decision considered only the value-absence and
    -- server-default conditions, ignoring whether the column carried a
    -- uniqueness obligation. This omits the `isUnique` disjunct and MUST fail
    -- the spec whenever a value-optional column with no default nonetheless
    -- carries a uniqueness obligation — it wrongly routes such a column to
    -- the in-place primitive.
    return (!acceptsNull || hasServerDefault)
    -- impl-end

prove_correct requiresTableRebuild by
  loom_solve

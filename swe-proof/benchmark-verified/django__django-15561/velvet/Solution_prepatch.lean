import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The decision the desired
   behaviour concerns — whether replacing one field definition with another
   requires rewriting the stored database column — is modeled directly in the
   `pure` region (`schemaAlterationNeeded`) from observable components of the two
   definitions. The mechanism that projects a concrete field definition onto
   those observable components (its quoted column name, its schema-relevant
   identity, and its enumerated choices) is a stable, unchanged operation; it is a
   type refinement recorded in mapping.md and exercised against the real
   projection by G-CONF (conformance_check.py), not an axiom. Nothing is
   axiomatized. -/
-- axioms-end

-- pure-start
/- A field definition as observed when deciding whether replacing one field
   definition with another requires rewriting the stored database column.
   * `quotedColumn`   — the quoted name of the database column the field maps to.
   * `schemaIdentity` — the part of the field's reconstructable definition that
                        determines the column's database schema: its import path,
                        positional arguments, and the keyword arguments that
                        affect the column. Attributes that never influence the
                        column's schema are not part of it.
   * `choices`        — the field's enumerated choices. A presentation-only
                        attribute, carried separately so the decision can be
                        stated with explicit access to it. -/
structure FieldDef where
  quotedColumn   : String
  schemaIdentity : String
  choices        : String
  deriving DecidableEq, Inhabited

/- Whether replacing the field definition `a` with `b` requires rewriting the
   stored column. A rewrite is required exactly when the quoted column name
   changes or the schema-relevant identity changes. The enumerated `choices`
   attribute is presentation-only: a difference in `choices` alone never requires
   a rewrite, so it is not consulted here even though it is observable. -/
def schemaAlterationNeeded (a b : FieldDef) : Bool :=
  decide (a.quotedColumn ≠ b.quotedColumn) ||
    decide (a.schemaIdentity ≠ b.schemaIdentity)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether replacing the field definition `a` with `b` requires rewriting
   the stored database column. Both `a` and `b` are read-only — the decision
   mutates nothing (directive 5). A rewrite is required precisely when the quoted
   column name differs or the schema-relevant identity differs; a change confined
   to the presentation-only `choices` attribute requires no rewrite. -/
method decideSchemaAlteration (a : FieldDef) (b : FieldDef) return (out : Bool)
  ensures out = schemaAlterationNeeded a b
  do
    -- impl-start
    -- Pre-image skeleton: the enumerated `choices` attribute is treated as
    -- schema-relevant — a difference confined to `choices` is reported as
    -- requiring a column rewrite (the extra `choices` disjunct below). The
    -- frozen spec excludes `choices` from the rewrite decision, so prove_correct
    -- MUST fail precisely when a and b differ only in `choices`.
    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
      decide (a.schemaIdentity ≠ b.schemaIdentity) ||
      decide (a.choices ≠ b.choices))
    -- impl-end

prove_correct decideSchemaAlteration by
  loom_solve
  simp_all [schemaAlterationNeeded]

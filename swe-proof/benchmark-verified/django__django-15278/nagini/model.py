"""Twin-artifact model for django__django-15278.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a column is added to an existing table on a backend whose in-place
  column-append statement (ADD COLUMN) cannot express key, uniqueness, not-null
  or default-value constraints, the operation must choose between two routes:

    * the FULL-REBUILD route, which reconstructs the table and so can realise
      ANY column constraint; and
    * the in-place APPEND route, which is only valid for a column that carries
      NONE of those constraints.

  The required behaviour: the in-place APPEND route may be taken ONLY for a
  column that is

      * not a primary key, AND
      * not unique, AND
      * nullable, AND
      * has no effective database default;

  if the column violates ANY one of these four conditions — it is a primary
  key, OR it is unique, OR it is non-nullable, OR it carries an effective
  default — the FULL-REBUILD route MUST be chosen. In particular a nullable,
  defaultless column that nonetheless carries a uniqueness (or primary-key)
  constraint must NOT be appended in place.

The column descriptor is modelled as a minimal object carrying only the touched
flags: whether it is a primary key, whether it is unique, and whether it is
nullable. Whether the column has an effective database default is reported by
an unchanged backend helper, axiomatized as a pure boolean callee.

The chosen route is reported as an int: 1 = full-rebuild route, 0 = in-place
append route.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ColumnSpec:
    def __init__(self, primary_key: bool, unique: bool, nullable: bool) -> None:
        Ensures(Acc(self.primary_key, 1 / 2) and self.primary_key == primary_key)  # type: ignore
        Ensures(Acc(self.unique, 1 / 2) and self.unique == unique)  # type: ignore
        Ensures(Acc(self.nullable, 1 / 2) and self.nullable == nullable)  # type: ignore
        self.primary_key = primary_key
        self.unique = unique
        self.nullable = nullable


# axioms-start
@Pure
@ContractOnly
def has_effective_default(col: ColumnSpec) -> bool:
    """Whether the unchanged backend helper reports an effective database
    default for this column (i.e. its effective default is not absent). A pure,
    side-effect-free observation of the column. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(col.primary_key, 1 / 8))
    Requires(Acc(col.unique, 1 / 8))
    Requires(Acc(col.nullable, 1 / 8))
# axioms-end


# pure-start
@Pure
def needs_full_rebuild(col: ColumnSpec) -> bool:
    """The in-place append route is valid ONLY for a column that is not a key,
    not unique, nullable, and carries no effective default; any other column
    requires the full-rebuild route."""
    Requires(Acc(col.primary_key, 1 / 4))
    Requires(Acc(col.unique, 1 / 4))
    Requires(Acc(col.nullable, 1 / 4))
    return (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col))
# pure-end


def add_column(col: ColumnSpec) -> int:
    # pre-conditions-start
    Requires(Acc(col.primary_key, 1 / 2))
    Requires(Acc(col.unique, 1 / 2))
    Requires(Acc(col.nullable, 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(col.primary_key, 1 / 2))
    Ensures(Acc(col.unique, 1 / 2))
    Ensures(Acc(col.nullable, 1 / 2))
    # The route is exactly the constraint-presence predicate: full rebuild iff
    # the column is a key, unique, non-nullable, or carries an effective
    # default; the in-place append route only for a column carrying none.
    Ensures(Result() == 1 or Result() == 0)
    Ensures((Result() == 1) == needs_full_rebuild(col))
    # A primary-key column always rebuilds.
    Ensures(Implies(col.primary_key, Result() == 1))
    # A unique column always rebuilds (this includes the nullable, defaultless
    # uniqueness-carrying column that must not be appended in place).
    Ensures(Implies(col.unique, Result() == 1))
    # A non-nullable column always rebuilds.
    Ensures(Implies(not col.nullable, Result() == 1))
    # A column with an effective default always rebuilds.
    Ensures(Implies(has_effective_default(col), Result() == 1))
    # The in-place append route is taken only when every constraint is absent.
    Ensures(Implies(Result() == 0,
                    (not col.primary_key) and (not col.unique) and
                    col.nullable and (not has_effective_default(col))))
    # post-conditions-end
    # impl-start
    if (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col)):
        return 1
    else:
        return 0
    # impl-end

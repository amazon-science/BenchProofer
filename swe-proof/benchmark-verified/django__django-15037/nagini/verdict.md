# P2 adversarial audit — django__django-15037

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,24 +133,7 @@
     # post-conditions-end
     # impl-start
     out = RelationField()
-    # Build a private copy of the referenced-column name up front, so all heap
-    # allocation precedes the pure decisions (keeps framing local).
-    col_copy = []  # type: List[int]
-    i = 0
-    while i < len(referenced_column):
-        # invariants-start
-        Invariant(Acc(list_pred(referenced_column), 1 / 2))
-        Invariant(Acc(list_pred(col_copy)))
-        Invariant(0 <= i and i <= len(referenced_column))
-        Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
-        # invariants-end
-        col_copy.append(referenced_column[i])
-        i = i + 1
-    Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
     out.is_one_to_one = unique_or_pk
     out.rel_to_self = names_equal(referenced_table, table_name)
-    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
-        out.needs_qualifier = True
-        out.qualifier_column = col_copy
     return out
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,24 +133,20 @@
     # post-conditions-end
     # impl-start
     out = RelationField()
-    # Build a private copy of the referenced-column name up front, so all heap
-    # allocation precedes the pure decisions (keeps framing local).
     col_copy = []  # type: List[int]
     i = 0
     while i < len(referenced_column):
-        # invariants-start
         Invariant(Acc(list_pred(referenced_column), 1 / 2))
         Invariant(Acc(list_pred(col_copy)))
         Invariant(0 <= i and i <= len(referenced_column))
         Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
-        # invariants-end
         col_copy.append(referenced_column[i])
         i = i + 1
     Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
     out.is_one_to_one = unique_or_pk
     out.rel_to_self = names_equal(referenced_table, table_name)
+    out.qualifier_column = col_copy
     if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
         out.needs_qualifier = True
-        out.qualifier_column = col_copy
     return out
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,23 +133,19 @@
     # post-conditions-end
     # impl-start
     out = RelationField()
-    # Build a private copy of the referenced-column name up front, so all heap
-    # allocation precedes the pure decisions (keeps framing local).
     col_copy = []  # type: List[int]
     i = 0
     while i < len(referenced_column):
-        # invariants-start
         Invariant(Acc(list_pred(referenced_column), 1 / 2))
         Invariant(Acc(list_pred(col_copy)))
         Invariant(0 <= i and i <= len(referenced_column))
         Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
-        # invariants-end
         col_copy.append(referenced_column[i])
         i = i + 1
     Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
     out.is_one_to_one = unique_or_pk
     out.rel_to_self = names_equal(referenced_table, table_name)
-    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
+    if not unique_or_pk:
         out.needs_qualifier = True
         out.qualifier_column = col_copy
     return out
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,21 +133,17 @@
     # post-conditions-end
     # impl-start
     out = RelationField()
-    # Build a private copy of the referenced-column name up front, so all heap
-    # allocation precedes the pure decisions (keeps framing local).
     col_copy = []  # type: List[int]
     i = 0
     while i < len(referenced_column):
-        # invariants-start
         Invariant(Acc(list_pred(referenced_column), 1 / 2))
         Invariant(Acc(list_pred(col_copy)))
         Invariant(0 <= i and i <= len(referenced_column))
         Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
-        # invariants-end
         col_copy.append(referenced_column[i])
         i = i + 1
     Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
-    out.is_one_to_one = unique_or_pk
+    out.is_one_to_one = not unique_or_pk
     out.rel_to_self = names_equal(referenced_table, table_name)
     if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
         out.needs_qualifier = True
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,22 +133,17 @@
     # post-conditions-end
     # impl-start
     out = RelationField()
-    # Build a private copy of the referenced-column name up front, so all heap
-    # allocation precedes the pure decisions (keeps framing local).
     col_copy = []  # type: List[int]
     i = 0
     while i < len(referenced_column):
-        # invariants-start
         Invariant(Acc(list_pred(referenced_column), 1 / 2))
         Invariant(Acc(list_pred(col_copy)))
         Invariant(0 <= i and i <= len(referenced_column))
         Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
-        # invariants-end
         col_copy.append(referenced_column[i])
         i = i + 1
     Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
     out.is_one_to_one = unique_or_pk
-    out.rel_to_self = names_equal(referenced_table, table_name)
     if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
         out.needs_qualifier = True
         out.qualifier_column = col_copy
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,24 +133,20 @@
     # post-conditions-end
     # impl-start
     out = RelationField()
-    # Build a private copy of the referenced-column name up front, so all heap
-    # allocation precedes the pure decisions (keeps framing local).
-    col_copy = []  # type: List[int]
+    tbl_copy = []  # type: List[int]
     i = 0
-    while i < len(referenced_column):
-        # invariants-start
-        Invariant(Acc(list_pred(referenced_column), 1 / 2))
-        Invariant(Acc(list_pred(col_copy)))
-        Invariant(0 <= i and i <= len(referenced_column))
-        Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
-        # invariants-end
-        col_copy.append(referenced_column[i])
+    while i < len(referenced_table):
+        Invariant(Acc(list_pred(referenced_table), 1 / 2))
+        Invariant(Acc(list_pred(tbl_copy)))
+        Invariant(0 <= i and i <= len(referenced_table))
+        Invariant(ToSeq(tbl_copy) == ToSeq(referenced_table).take(i))
+        tbl_copy.append(referenced_table[i])
         i = i + 1
-    Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
+    Assert(ToSeq(referenced_table).take(len(referenced_table)) == ToSeq(referenced_table))
     out.is_one_to_one = unique_or_pk
     out.rel_to_self = names_equal(referenced_table, table_name)
     if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
         out.needs_qualifier = True
-        out.qualifier_column = col_copy
+        out.qualifier_column = tbl_copy
     return out
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,24 +133,9 @@
     # post-conditions-end
     # impl-start
     out = RelationField()
-    # Build a private copy of the referenced-column name up front, so all heap
-    # allocation precedes the pure decisions (keeps framing local).
-    col_copy = []  # type: List[int]
-    i = 0
-    while i < len(referenced_column):
-        # invariants-start
-        Invariant(Acc(list_pred(referenced_column), 1 / 2))
-        Invariant(Acc(list_pred(col_copy)))
-        Invariant(0 <= i and i <= len(referenced_column))
-        Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
-        # invariants-end
-        col_copy.append(referenced_column[i])
-        i = i + 1
-    Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
     out.is_one_to_one = unique_or_pk
     out.rel_to_self = names_equal(referenced_table, table_name)
     if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
         out.needs_qualifier = True
-        out.qualifier_column = col_copy
     return out
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15037.

Behaviour under specification (stated as desired behaviour, not as an edit):

A column that participates in a relationship to another table is rendered as a
relational model field. The introspected facts about one such column are:

  * whether the relationship is one-to-one (a unique or primary-key relation)
    rather than a plain many-to-one relationship;
  * the name of the column it references in the other table (the referenced
    column);
  * the name of the other table, and the name of the table being introspected;
  * the primary-key column of the other table, if that table has one.

The result records three decisions:

  (1) the relation kind: one-to-one exactly when the relation is unique/primary;
  (2) whether the related target is the table itself (the referenced table name
      equals the current table name);
  (3) whether an explicit referenced-column qualifier must be emitted, and which
      column it names. The qualifier is required exactly when the relationship
      is the plain many-to-one kind AND the other table has a primary-key column
      AND that primary-key column is NOT the referenced column; in that case the
      qualifier names the referenced column. A one-to-one relation, a referenced
      table without a primary key, or a relationship that already targets the
      other table's primary key needs no qualifier — and then the result's
      qualifier column is empty (the canonical representation of an absent
      qualifier: in reality no qualifier value exists at all in that case).

Column and table names are modelled as `List[int]` of Unicode code points
(Nagini bans `str` indexing); name equality is carried by `PSeq[int]` via
`ToSeq`. The other table's primary-key column is the (unchanged) introspected
fact `other_pk_column`, an `Optional[List[int]]` (None when there is no primary
key); its provenance and out-of-band soundness check live in mapping.md /
axiom_check.py (an A-reference, not a consumed axiom).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axiom is consumed by the proof. The other table's
#  primary-key column name is taken directly as the introspected
#  `other_pk_column` input and validated against reality out-of-band by
#  axiom_check.py / G-AX — an A-reference, see refinement.md and mapping.md.)
# axioms-end


# pure-start
@Pure
def names_equal(a: List[int], b: List[int]) -> bool:
    """Two column/table names are equal iff their code-point sequences match."""
    Requires(Acc(list_pred(a), 1 / 4))
    Requires(Acc(list_pred(b), 1 / 4))
    return ToSeq(a) == ToSeq(b)


@Pure
def qualifier_required(unique_or_pk: bool, referenced_column: List[int],
                       other_pk_column: Optional[List[int]]) -> bool:
    """The referenced-column qualifier is required exactly for a plain
    many-to-one relationship whose other table has a (non-empty) primary-key
    column name that is not the referenced column."""
    Requires(Acc(list_pred(referenced_column), 1 / 4))
    Requires(Implies(other_pk_column is not None,
                     Acc(list_pred(other_pk_column), 1 / 4)))
    return (not unique_or_pk) and other_pk_column is not None and \
        len(other_pk_column) > 0 and \
        ToSeq(other_pk_column) != ToSeq(referenced_column)
# pure-end


class RelationField:
    """Carrier of the three decisions about one relational column.

    `qualifier_column` names the emitted qualifier when `needs_qualifier` is
    True, and is empty when `needs_qualifier` is False (the canonical
    representation of an absent qualifier).
    """

    def __init__(self) -> None:
        Ensures(Acc(self.is_one_to_one) and Acc(self.rel_to_self) and
                Acc(self.needs_qualifier) and Acc(self.qualifier_column))
        Ensures(self.is_one_to_one is False and self.rel_to_self is False)
        Ensures(self.needs_qualifier is False)
        Ensures(Acc(list_pred(self.qualifier_column)) and len(self.qualifier_column) == 0)
        self.is_one_to_one = False  # type: bool
        self.rel_to_self = False  # type: bool
        self.needs_qualifier = False  # type: bool
        self.qualifier_column = []  # type: List[int]


def relation_field(unique_or_pk: bool,
                   referenced_column: List[int],
                   referenced_table: List[int],
                   table_name: List[int],
                   other_pk_column: Optional[List[int]]) -> RelationField:
    # pre-conditions-start
    Requires(Acc(list_pred(referenced_column), 1 / 2))
    Requires(Acc(list_pred(referenced_table), 1 / 2))
    Requires(Acc(list_pred(table_name), 1 / 2))
    Requires(Implies(other_pk_column is not None,
                     Acc(list_pred(other_pk_column), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs are returned at the same fractional permission.
    Ensures(Acc(list_pred(referenced_column), 1 / 2))
    Ensures(Acc(list_pred(referenced_table), 1 / 2))
    Ensures(Acc(list_pred(table_name), 1 / 2))
    Ensures(Implies(other_pk_column is not None,
                    Acc(list_pred(other_pk_column), 1 / 2)))
    # The freshly produced result object is fully owned.
    Ensures(Acc(Result().is_one_to_one) and Acc(Result().rel_to_self) and
            Acc(Result().needs_qualifier) and Acc(Result().qualifier_column))
    Ensures(Acc(list_pred(Result().qualifier_column)))
    # (1) relation kind: one-to-one iff unique/primary.
    Ensures(Result().is_one_to_one == unique_or_pk)
    # (2) target is the table itself iff the referenced table is the current one.
    Ensures(Result().rel_to_self == names_equal(referenced_table, table_name))
    # (3) the referenced-column qualifier is emitted exactly when required,
    #     and when emitted it names the referenced column.
    Ensures(Result().needs_qualifier ==
            qualifier_required(unique_or_pk, referenced_column, other_pk_column))
    Ensures(Implies(Result().needs_qualifier,
                    ToSeq(Result().qualifier_column) == ToSeq(referenced_column)))
    #     when NOT required, no qualifier value exists in reality (the to_field
    #     key is absent), so the column is pinned to the canonical empty value —
    #     an impl must not smuggle a value into the absent case.
    Ensures(Implies(not Result().needs_qualifier,
                    len(Result().qualifier_column) == 0))
    # post-conditions-end
    # impl-start
    out = RelationField()
    # Build a private copy of the referenced-column name up front, so all heap
    # allocation precedes the pure decisions (keeps framing local).
    col_copy = []  # type: List[int]
    i = 0
    while i < len(referenced_column):
        # invariants-start
        Invariant(Acc(list_pred(referenced_column), 1 / 2))
        Invariant(Acc(list_pred(col_copy)))
        Invariant(0 <= i and i <= len(referenced_column))
        Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
        # invariants-end
        col_copy.append(referenced_column[i])
        i = i + 1
    Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
        out.needs_qualifier = True
        out.qualifier_column = col_copy
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins all four output fields of relation_field: is_one_to_one==unique_or_pk; rel_to_self==names_equal(referenced_table,table_name); needs_qualifier==qualifier_required(...); Implies(needs_qualifier, ToSeq(qualifier_column)==ToSeq(referenced_column)); Implies(not needs_qualifier, len(qualifier_column)==0). The last postcondition closes the historic don't-care gap (source-repo G-PANEL-1 atk_6, where qualifier_column was unconstrained on the else branch).

Protocol (all run from project root with SBU_BENCHMARK_DIR=benchmark-verified, python=python; attack files built by splicing ONLY the impl region, axioms/@Pure/Requires/Ensures byte-identical; same-spec exit 0 confirmed for every file incl. positive control).

Positive control (model.py verbatim): `python -m swebench_unified.adversary verify nagini django__django-15037 .../positive_control.py` => VERIFIED in 17.0s (exit 0).

Seven distinct same-spec wrong impls, each `python -m swebench_unified.adversary weakness nagini django__django-15037 .../atk_N.py`:
- atk_1 (prepatch bug: never emits qualifier; needs_qualifier stays False) => exit 2, NOT-A-COUNTEREXAMPLE (verification failed). PREPATCH REPRODUCED.
- atk_2 (smuggle: qualifier_column=col_copy always, needs_qualifier gated) => exit 2 (violates Implies(not needs_qualifier, len==0); this is exactly the historic atk_6 gap, now rejected).
- atk_3 (control-flow-effect: needs_qualifier := not unique_or_pk, ignoring pk logic) => exit 2.
- atk_4 (field flip: is_one_to_one = not unique_or_pk) => exit 2.
- atk_5 (boundary: rel_to_self never assigned, left constructor False) => exit 2.
- atk_6 (ungrounded/wrong-value echo: qualifier_column names referenced_table copy instead of referenced_column) => exit 2.
- atk_7 (partial-domain: needs_qualifier=True set but qualifier_column left empty) => exit 2.

No attack came back a CANDIDATE (none both shares spec AND verifies), so no faithful refined patch needed materializing/resolving; verify => correct holds.

A-leg audit: refinement.md legs are all R / I / A-reference; NO consumed @ContractOnly axiom (axioms region is a comment only) and explicitly NO kind-3 step. The single A-reference is step 4, get_primary_key_column (django/db/backends/base/introspection.py:166-173), taken as the introspected Optional[List[int]] input other_pk_column. Its correspondence to the real callee is validated by axiom_check.py: `python benchmark-verified/django__django-15037/nagini/axiom_check.py` => 'G-AX OK: get_primary_key_column reproduction sound on 6 pk scenarios; relation_field decision == real inspectdb on 7 boundary + 50000 fuzz cases' (exit 0). Model<->patch correspondence (mapping.md/refinement.md steps 1-7) holds: str<->List[int] code points, rel_type<->is_one_to_one bijection, ref_db_table==table_name <-> rel_to_self, and the added to_field guard exactly matches qualifier_required.

Parallelism: attack verifications launched as concurrent background Bash jobs, <=3 JVM+Z3 at a time (batch1: posctl+atk_1+atk_2; batch2: atk_3,4,5; batch3: atk_6,7). Schedule only; every attack fully verified and reported.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15037.

Behaviour under specification (stated as desired behaviour, not as an edit):

A column that participates in a relationship to another table is rendered as a
relational model field. The introspected facts about one such column are:

  * whether the relationship is one-to-one (a unique or primary-key relation)
    rather than a plain many-to-one relationship;
  * the name of the column it references in the other table (the referenced
    column);
  * the name of the other table, and the name of the table being introspected;
  * the primary-key column of the other table, if that table has one.

The result records three decisions:

  (1) the relation kind: one-to-one exactly when the relation is unique/primary;
  (2) whether the related target is the table itself (the referenced table name
      equals the current table name);
  (3) whether an explicit referenced-column qualifier must be emitted, and which
      column it names. The qualifier is required exactly when the relationship
      is the plain many-to-one kind AND the other table has a primary-key column
      AND that primary-key column is NOT the referenced column; in that case the
      qualifier names the referenced column. A one-to-one relation, a referenced
      table without a primary key, or a relationship that already targets the
      other table's primary key needs no qualifier — and then the result's
      qualifier column is empty (the canonical representation of an absent
      qualifier: in reality no qualifier value exists at all in that case).

Column and table names are modelled as `List[int]` of Unicode code points
(Nagini bans `str` indexing); name equality is carried by `PSeq[int]` via
`ToSeq`. The other table's primary-key column is the (unchanged) introspected
fact `other_pk_column`, an `Optional[List[int]]` (None when there is no primary
key); its provenance and out-of-band soundness check live in mapping.md /
axiom_check.py (an A-reference, not a consumed axiom).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axiom is consumed by the proof. The other table's
#  primary-key column name is taken directly as the introspected
#  `other_pk_column` input and validated against reality out-of-band by
#  axiom_check.py / G-AX — an A-reference, see refinement.md and mapping.md.)
# axioms-end


# pure-start
@Pure
def names_equal(a: List[int], b: List[int]) -> bool:
    """Two column/table names are equal iff their code-point sequences match."""
    Requires(Acc(list_pred(a), 1 / 4))
    Requires(Acc(list_pred(b), 1 / 4))
    return ToSeq(a) == ToSeq(b)


@Pure
def qualifier_required(unique_or_pk: bool, referenced_column: List[int],
                       other_pk_column: Optional[List[int]]) -> bool:
    """The referenced-column qualifier is required exactly for a plain
    many-to-one relationship whose other table has a (non-empty) primary-key
    column name that is not the referenced column."""
    Requires(Acc(list_pred(referenced_column), 1 / 4))
    Requires(Implies(other_pk_column is not None,
                     Acc(list_pred(other_pk_column), 1 / 4)))
    return (not unique_or_pk) and other_pk_column is not None and \
        len(other_pk_column) > 0 and \
        ToSeq(other_pk_column) != ToSeq(referenced_column)
# pure-end


class RelationField:
    """Carrier of the three decisions about one relational column.

    `qualifier_column` names the emitted qualifier when `needs_qualifier` is
    True, and is empty when `needs_qualifier` is False (the canonical
    representation of an absent qualifier).
    """

    def __init__(self) -> None:
        Ensures(Acc(self.is_one_to_one) and Acc(self.rel_to_self) and
                Acc(self.needs_qualifier) and Acc(self.qualifier_column))
        Ensures(self.is_one_to_one is False and self.rel_to_self is False)
        Ensures(self.needs_qualifier is False)
        Ensures(Acc(list_pred(self.qualifier_column)) and len(self.qualifier_column) == 0)
        self.is_one_to_one = False  # type: bool
        self.rel_to_self = False  # type: bool
        self.needs_qualifier = False  # type: bool
        self.qualifier_column = []  # type: List[int]


def relation_field(unique_or_pk: bool,
                   referenced_column: List[int],
                   referenced_table: List[int],
                   table_name: List[int],
                   other_pk_column: Optional[List[int]]) -> RelationField:
    # pre-conditions-start
    Requires(Acc(list_pred(referenced_column), 1 / 2))
    Requires(Acc(list_pred(referenced_table), 1 / 2))
    Requires(Acc(list_pred(table_name), 1 / 2))
    Requires(Implies(other_pk_column is not None,
                     Acc(list_pred(other_pk_column), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs are returned at the same fractional permission.
    Ensures(Acc(list_pred(referenced_column), 1 / 2))
    Ensures(Acc(list_pred(referenced_table), 1 / 2))
    Ensures(Acc(list_pred(table_name), 1 / 2))
    Ensures(Implies(other_pk_column is not None,
                    Acc(list_pred(other_pk_column), 1 / 2)))
    # The freshly produced result object is fully owned.
    Ensures(Acc(Result().is_one_to_one) and Acc(Result().rel_to_self) and
            Acc(Result().needs_qualifier) and Acc(Result().qualifier_column))
    Ensures(Acc(list_pred(Result().qualifier_column)))
    # (1) relation kind: one-to-one iff unique/primary.
    Ensures(Result().is_one_to_one == unique_or_pk)
    # (2) target is the table itself iff the referenced table is the current one.
    Ensures(Result().rel_to_self == names_equal(referenced_table, table_name))
    # (3) the referenced-column qualifier is emitted exactly when required,
    #     and when emitted it names the referenced column.
    Ensures(Result().needs_qualifier ==
            qualifier_required(unique_or_pk, referenced_column, other_pk_column))
    Ensures(Implies(Result().needs_qualifier,
                    ToSeq(Result().qualifier_column) == ToSeq(referenced_column)))
    #     when NOT required, no qualifier value exists in reality (the to_field
    #     key is absent), so the column is pinned to the canonical empty value —
    #     an impl must not smuggle a value into the absent case.
    Ensures(Implies(not Result().needs_qualifier,
                    len(Result().qualifier_column) == 0))
    # post-conditions-end
    # impl-start
    out = RelationField()
    # Build a private copy of the referenced-column name up front, so all heap
    # allocation precedes the pure decisions (keeps framing local).
    col_copy = []  # type: List[int]
    i = 0
    while i < len(referenced_column):
        # invariants-start
        Invariant(Acc(list_pred(referenced_column), 1 / 2))
        Invariant(Acc(list_pred(col_copy)))
        Invariant(0 <= i and i <= len(referenced_column))
        Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
        # invariants-end
        col_copy.append(referenced_column[i])
        i = i + 1
    Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
        out.needs_qualifier = True
        out.qualifier_column = col_copy
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins all four output fields of relation_field: is_one_to_one==unique_or_pk; rel_to_self==names_equal(referenced_table,table_name); needs_qualifier==qualifier_required(...); Implies(needs_qualifier, ToSeq(qualifier_column)==ToSeq(referenced_column)); Implies(not needs_qualifier, len(qualifier_column)==0). The last postcondition closes the historic don't-care gap (source-repo G-PANEL-1 atk_6, where qualifier_column was unconstrained on the else branch).

Protocol (all run from project root with SBU_BENCHMARK_DIR=benchmark-verified, python=python; attack files built by splicing ONLY the impl region, axioms/@Pure/Requires/Ensures byte-identical; same-spec exit 0 confirmed for every file incl. positive control).

Positive control (model.py verbatim): `python -m swebench_unified.adversary verify nagini django__django-15037 .../positive_control.py` => VERIFIED in 17.0s (exit 0).

Seven distinct same-spec wrong impls, each `python -m swebench_unified.adversary weakness nagini django__django-15037 .../atk_N.py`:
- atk_1 (prepatch bug: never emits qualifier; needs_qualifier stays False) => exit 2, NOT-A-COUNTEREXAMPLE (verification failed). PREPATCH REPRODUCED.
- atk_2 (smuggle: qualifier_column=col_copy always, needs_qualifier gated) => exit 2 (violates Implies(not needs_qualifier, len==0); this is exactly the historic atk_6 gap, now rejected).
- atk_3 (control-flow-effect: needs_qualifier := not unique_or_pk, ignoring pk logic) => exit 2.
- atk_4 (field flip: is_one_to_one = not unique_or_pk) => exit 2.
- atk_5 (boundary: rel_to_self never assigned, left constructor False) => exit 2.
- atk_6 (ungrounded/wrong-value echo: qualifier_column names referenced_table copy instead of referenced_column) => exit 2.
- atk_7 (partial-domain: needs_qualifier=True set but qualifier_column left empty) => exit 2.

No attack came back a CANDIDATE (none both shares spec AND verifies), so no faithful refined patch needed materializing/resolving; verify => correct holds.

A-leg audit: refinement.md legs are all R / I / A-reference; NO consumed @ContractOnly axiom (axioms region is a comment only) and explicitly NO kind-3 step. The single A-reference is step 4, get_primary_key_column (django/db/backends/base/introspection.py:166-173), taken as the introspected Optional[List[int]] input other_pk_column. Its correspondence to the real callee is validated by axiom_check.py: `python benchmark-verified/django__django-15037/nagini/axiom_check.py` => 'G-AX OK: get_primary_key_column reproduction sound on 6 pk scenarios; relation_field decision == real inspectdb on 7 boundary + 50000 fuzz cases' (exit 0). Model<->patch correspondence (mapping.md/refinement.md steps 1-7) holds: str<->List[int] code points, rel_type<->is_one_to_one bijection, ref_db_table==table_name <-> rel_to_self, and the added to_field guard exactly matches qualifier_required.

Parallelism: attack verifications launched as concurrent background Bash jobs, <=3 JVM+Z3 at a time (batch1: posctl+atk_1+atk_2; batch2: atk_3,4,5; batch3: atk_6,7). Schedule only; every attack fully verified and reported.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the modeled decision vs the REAL post-patch inspectdb block (django/core/management/commands/inspectdb.py:118-130). Verified against a fresh copy of with the gold patch (identical to swe-bench-verified gold and to refinement.md's hunk) applied — the base worktree is pre-patch, so the block must be patched before comparison (an unpatched extraction spuriously diverges everywhere because it never sets to_field).

Method: extracted the real relation-handling block from the patched module source by AST (located by rel_type/rel_to assignment targets, guard=is_relation, no hard-coded text), executed it against controlled namespaces with a stub get_primary_key_column returning the fuzzed pk (the model's input boundary — the callee itself is G-AX's A-reference), and compared the four observations (is_one_to_one, rel_to_self, to_field present, to_field value) to the model's decision reimplemented from model.py's @Pure helpers.

Results: 0 divergences on a 25,200-case boundary grid (14 extra_params forms incl. truthy/falsy/missing unique & primary_key and '' / 0 / None variants; name pools with '', unicode 'café_id'/'名前', self-relation and pk==ref_col collisions) AND 0 divergences on 300,000 randomized fuzz cases (seed=99). Total 325,200 inputs, all agree.

Each clause matches reality: (1) is_one_to_one==unique_or_pk <-> the OneToOneField/ForeignKey bijection where unique_or_pk = truthiness of extra_params.pop('unique',False) or .get('primary_key'); (2) rel_to_self <-> ref_db_table==table_name; (3) qualifier_required = (not unique_or_pk) and other_pk_column is not None and len>0 and ToSeq!=ref_col <-> the else-branch guard `if ref_pk_column and ref_pk_column != ref_db_column` — the `len>0` clause correctly models Python str falsiness ('' and None both falsy, matching the empty-string PK edge); when required qualifier_column==ref_db_column <-> extra_params['to_field']=ref_db_column; when not required the empty-list canonical form <-> to_field key absent (real block leaves it unset). get_primary_key_column is an unchanged callee taken as introspected Optional input (A-reference validated by G-AX / axiom_check.py), not a consumed contract.

Cross-checks: spec region byte-identical (adversary same-spec on the unmodified model.py exits 0). Bundle's own G-CONF passes on 110,245 inputs (0 disagreements) and G-AX passes on 6 pk scenarios + 50,000 fuzz. The spec is neither too strong nor drifting — no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over the nagini spec view) passes: no diff markers, no reproduced gold-patch line (>=8 chars normalized), no patched file path (inspectdb.py) or module path, and the only distinctive changed symbol ('table2model') does not appear in the spec view. Manual repo-symbol sweep of the spec view confirms NONE of get_primary_key_column, inspectdb, table2model, ref_db_column, ref_db_table, ref_pk_column, extra_params, OneToOneField, ForeignKey, relations[...], connection.introspection appear. The spec is stated abstractly (relation kind, referenced column, qualifier emission), never as an edit. The single Django-ish token present, 'to_field', occurs only in a behavioral post-condition comment and names precisely the concept the PUBLIC problem_statement already discloses (title: 'Foreign key to a specific field is not handled in inspectdb'; body shows the generated FK should target foo(other_id) not foo). It localizes no file/function/callee/diff-line beyond the public task. Spec view does not enable gold-edit reconstruction beyond problem_statement (hints_text not considered per policy).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

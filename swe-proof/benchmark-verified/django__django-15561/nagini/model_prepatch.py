"""Twin-artifact model for django__django-15561.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a schema editor is asked to reconcile an existing column definition with
  a proposed one, it must decide whether the underlying table actually needs to
  be rebuilt. Each definition is summarised by its column name plus a bag of
  configuration attributes (an attribute-code together with its value). Some of
  those attributes have NO bearing on the physical column -- presentation,
  validation and relation-management options among them -- so a difference in
  any of THOSE attributes alone must never trigger a rebuild.

  Two facts are pinned here:

    (1) The set of attributes that do not affect a column definition is EXACTLY
        the enumeration-of-permitted-values attribute together with the eleven
        further presentation, validation and relation-management options
        (attr_blank() ... attr_verbose_name()) -- and nothing else. A field
        whose only change is to gain, drop, or alter the enumeration carries an
        identical physical column; it is therefore one of the schema-irrelevant
        attributes and is ignored when deciding whether to rebuild. Every
        attribute OUTSIDE this twelve-element set is schema-relevant: it MUST
        keep participating in the rebuild decision (a larger set would wrongly
        suppress rebuilds on schema-relevant changes).

    (2) The rebuild decision is TRUE exactly when EITHER the non-attribute part
        of the two definitions differs (column name or any other structural
        component), OR the two attribute bags disagree on at least one attribute
        that IS schema-relevant -- i.e. on an attribute OUTSIDE the
        schema-irrelevant set. Disagreement confined entirely to
        schema-irrelevant attributes (the enumeration attribute among them)
        yields FALSE: no rebuild.

  The consequence that matters: altering ONLY the enumeration of permitted values
  on a field, with the column name and every schema-relevant attribute unchanged,
  is a no-op -- the editor issues no table rebuild.

Modelling choices (Nagini fragment):
  * Each attribute is an ``int`` code; the enumeration-of-permitted-values
    attribute is the module-level constant ``attr_choices()``. The eleven
    further schema-irrelevant attribute codes are ``attr_blank()`` ... etc.
  * The schema-irrelevant attribute set is a ``PSet[int]`` of attribute codes,
    produced by ``schema_irrelevant_attrs()`` (the first modelled site); its postcondition
    pins the result EXACTLY: it equals the twelve-element set of the enumeration
    attribute plus the eleven legacy codes (set equality, so neither a subset
    nor a superset is admitted -- an extra member would silently mark a
    schema-RELEVANT attribute as irrelevant and suppress required rebuilds).
  * The two attribute bags to compare are modelled as aligned read-only
    sequences: ``attrs: PSeq[int]`` lists the attribute codes that appear in
    either bag, and ``old_vals`` / ``new_vals`` carry, for each listed attribute,
    the value token on each side. An attribute absent from one side is faithfully
    a value-token mismatch (a distinct absence token), so "membership disagrees"
    and "value disagrees" are the same elementwise test (mapping.md §2). Object
    / value identity is carried by integer equality.
  * The non-attribute structural comparison (column name plus the path / leading
    arguments of the two definitions) is summarised by a single read-only
    ``bool`` parameter ``other_differs``; booleans need no permission.

The compared bags and the schema-irrelevant set are read-only inputs, held at
fractional permission (Required AND Ensured). The whole behaviour is modelled
deeply: ``schema_irrelevant_attrs`` builds the set explicitly, and ``field_alteration_needed``
spells out the "structural difference OR a schema-relevant attribute disagrees"
scan as an existential discharged by a loop. There is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the schema-irrelevant attribute set and the rebuild decision are the
# behaviour under specification and are spelled out deeply in the impl regions.
# There is no unchanged opaque callee whose Ensures the proof consumes.
# axioms-end


# pure-start
@Pure
def attr_choices() -> int:
    # Attribute code for the enumeration of permitted values.
    return 0


@Pure
def attr_blank() -> int:
    return 1


@Pure
def attr_db_column() -> int:
    return 2


@Pure
def attr_editable() -> int:
    return 3


@Pure
def attr_error_messages() -> int:
    return 4


@Pure
def attr_help_text() -> int:
    return 5


@Pure
def attr_limit_choices_to() -> int:
    return 6


@Pure
def attr_on_delete() -> int:
    return 7


@Pure
def attr_related_name() -> int:
    return 8


@Pure
def attr_related_query_name() -> int:
    return 9


@Pure
def attr_validators() -> int:
    return 10


@Pure
def attr_verbose_name() -> int:
    return 11


@Pure
def disagrees_relevant(attrs: PSeq[int], old_vals: PSeq[int], new_vals: PSeq[int],
                       non_db: PSet[int]) -> bool:
    """The two attribute bags disagree on at least one SCHEMA-RELEVANT attribute:
    some listed attribute is OUTSIDE the schema-irrelevant set and yet carries
    different value tokens on the two sides. This is the existential over the
    listed attributes of the per-attribute "relevant and disagreeing" test."""
    Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
    return Exists(int, lambda j: 0 <= j and j < len(attrs)
                  and not (attrs[j] in non_db)
                  and old_vals[j] != new_vals[j])
# pure-end


def schema_irrelevant_attrs() -> PSet[int]:
    # pre-conditions-start
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
    # membership): it is the enumeration-of-permitted-values attribute together
    # with the eleven further presentation / validation / relation-management
    # attributes, and NOTHING ELSE. Equality (rather than one-sided membership)
    # is load-bearing in both directions: a set missing the enumeration
    # attribute makes a choices-only change trigger a rebuild (the behaviour
    # the problem statement rules out), and a set with ANY extra member would
    # mark a schema-RELEVANT attribute as irrelevant, silently suppressing
    # required rebuilds.
    Ensures(Result() == PSet(attr_choices(), attr_blank(), attr_db_column(),
                             attr_editable(), attr_error_messages(),
                             attr_help_text(), attr_limit_choices_to(),
                             attr_on_delete(), attr_related_name(),
                             attr_related_query_name(), attr_validators(),
                             attr_verbose_name()))
    # In particular the enumeration-of-permitted-values attribute is a member:
    # a difference confined to it never warrants a rebuild.
    Ensures(attr_choices() in Result())
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the schema-irrelevant set is built WITHOUT the
    # enumeration-of-permitted-values attribute, so the postcondition
    # ``attr_choices() in Result()`` is unprovable and verification FAILS
    # (G-DIFF: the spec senses the missing enumeration attribute).
    s = PSet(attr_blank(), attr_db_column(), attr_editable(),
             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
             attr_on_delete(), attr_related_name(), attr_related_query_name(),
             attr_validators(), attr_verbose_name())
    return s
    # impl-end


def field_alteration_needed(attrs: PSeq[int], old_vals: PSeq[int],
                            new_vals: PSeq[int], non_db: PSet[int],
                            other_differs: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(non_db), 1 / 2))
    # The listed attributes and their two value vectors are aligned.
    Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(non_db), 1 / 2))
    # A rebuild is needed exactly when the non-attribute structural part differs,
    # OR the bags disagree on some SCHEMA-RELEVANT attribute. Disagreement
    # confined to schema-irrelevant attributes (the enumeration attribute among
    # them, when it is in ``non_db``) yields FALSE.
    Ensures(Result() == (other_differs
                         or disagrees_relevant(attrs, old_vals, new_vals, non_db)))
    # post-conditions-end
    # impl-start
    if other_differs:
        return True
    i = 0
    while i < len(attrs):
        # invariants-start
        Invariant(Acc(set_pred(non_db), 1 / 2))
        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
        Invariant(0 <= i and i <= len(attrs))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
        Invariant(MustTerminate(len(attrs) - i + 1))
        # invariants-end
        if not (attrs[i] in non_db):
            if old_vals[i] != new_vals[i]:
                return True
        i = i + 1
    return False
    # impl-end

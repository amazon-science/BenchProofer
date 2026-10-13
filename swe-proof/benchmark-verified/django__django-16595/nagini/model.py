"""Twin-artifact model for django__django-16595.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A field-altering migration step, when asked whether it can be combined with a
  later step acting on the SAME field of the SAME model, must collapse the pair
  into just that later step in two cases:

    (1) the later step REMOVES that field (the prior alteration is irrelevant
        once the field is gone), and
    (2) the later step ALTERS that same field again (the second alteration
        fully supersedes the first; only the final field definition matters).

  In both cases the combined result is the singleton sequence containing
  exactly the later step. For a later step that RENAMES the same field (and
  whose new field definition pins no explicit stored-column name), the
  alteration is carried across the rename instead, yielding the rename followed
  by an equivalent alteration of the renamed field.

  The behaviour must be symmetric between the two collapsing cases: altering a
  field then altering it again is reduced the same way as altering then
  removing it. Failing to collapse the alter-then-alter case (case 2) leaves a
  redundant alteration that should not survive.

  A pair that none of those same-field rules resolves is then decided by the
  two steps' own ELIDABLE marks (a step is elidable when it is safe to elide
  and to optimize across): if the earlier step is elidable the pair reduces to
  just the later step; otherwise, if the later step is elidable, it reduces to
  just the earlier step.

  Otherwise the pair is not combined here, and the answer is instead a
  REORDERING VERDICT about the two steps: the caller is told whether it may
  optimize across the later step, which it may do exactly when that later step
  does not itself reference the altered field. So "not combined here" is not one
  answer but two: combining is declined AND permission to reorder is either
  granted or withheld, and a step that touches the altered field withholds it.

Migration steps are modelled as a minimal class carrying only the touched
fields: a kind tag, the lower-cased owning model name and field name, the new
name a rename gives that field, (for the rename carry-across) whether the new
field definition pins an explicit column, and the elidable mark. Not every
facet belongs to every step, and the reduction is only ever lent the ones that
do: a NEW NAME is something only a renaming step has, so the reduction may
consult the later step's new name only once that step is known to be a rename,
and it is lent no new name of its own at all, an altering step having none to
give. Reaching for a facet a step does not carry is not a reading that returns
some value; in the real program it is a failure, so the reduction must reach
the answer without it. That holds just as much for a step the reduction BUILDS
as for one it is handed: a step built as an alteration has no new name either,
so building one grants nothing to read back on that facet and nothing is
claimed about it. Whether an explicit stored column is pinned is partial in the
same way and for the same reason, being a facet of the field definition a step
carries rather than of the step: the altering step whose definition is being
carried across has one, and so may a removing step, but a renaming step is two
names and no definition, so neither the later step's column status nor that of a
renaming step the reduction builds is anything it may consult. Whether the later step references the altered field is a
question about the PAIR (the repository asks it as a query taking the altered
step's model and field name), so it is an ARGUMENT to the reduction rather than
state stored on a step; no step object carries it, and nothing is claimed about
it for a step the reduction constructs. The
result is a pair: a list of steps when the pair IS combined here (with the
reordering verdict normalised to False, no reordering question being asked),
and `None` plus the reordering verdict when it is not.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# Step-kind tags (distinct small integers).
KIND_OTHER = 0
KIND_ALTER = 1
KIND_REMOVE = 2
KIND_RENAME = 3


class MigrationStep:
    def __init__(self, kind: int, model_name_lower: int, name_lower: int,
                 new_name_lower: int, has_explicit_column: bool,
                 elidable: bool) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.kind) and self.kind == kind)                       # type: ignore
        Ensures(Acc(self.model_name_lower) and self.model_name_lower == model_name_lower)  # type: ignore
        Ensures(Acc(self.name_lower) and self.name_lower == name_lower)     # type: ignore
        # A NEW NAME is a facet only a RENAMING step carries, and a step BUILT
        # here is no different from one handed in: it carries a new name exactly
        # when it is built as a rename. So building an ALTERING step yields no
        # new name to read back and says nothing about that facet of it — the
        # same partiality the later step's new name is lent under. A total grant
        # here would model every step ever built as carrying a new name, and a
        # reduction could then name the step it returns by reading a facet that,
        # on an altering step in the real program, is not a value but a failure.
        Ensures(Implies(kind == KIND_RENAME,
                        Acc(self.new_name_lower)                            # type: ignore
                        and self.new_name_lower == new_name_lower))         # type: ignore
        # WHETHER AN EXPLICIT STORED COLUMN IS PINNED is not a facet of a step
        # as such: it is a facet of the FIELD DEFINITION a step carries, so only
        # a step of a kind that carries a field definition has one. An ALTERING
        # step is built from a definition and a REMOVING step may be given one,
        # but a RENAMING step is built from two names and no definition at all,
        # and a step of some other kind need not carry one either. So this facet
        # is granted on exactly the two kinds that carry a definition; building a
        # renaming step, or one of some other kind, yields no column status to
        # read back and says nothing about it. A total grant here would let a
        # reduction reach its answer through the column of a step it built as a
        # rename, which in the real program is not a value but a failure — there
        # is no definition there to ask.
        Ensures(Implies(kind == KIND_ALTER or kind == KIND_REMOVE,
                        Acc(self.has_explicit_column)                       # type: ignore
                        and self.has_explicit_column == has_explicit_column))  # type: ignore
        Ensures(Acc(self.elidable) and self.elidable == elidable)           # type: ignore
        self.kind = kind
        self.model_name_lower = model_name_lower
        self.name_lower = name_lower
        self.new_name_lower = new_name_lower
        self.has_explicit_column = has_explicit_column
        self.elidable = elidable


# axioms-start
# (no axioms: the behaviour is pure control flow over step kinds, the same-field
# test, the two elidable marks and the supplied answer to whether the later step
# references the altered field; nothing the changed routine CALLS is opaque to
# Nagini)
# axioms-end


# pure-start
@Pure
def is_same_field(this: MigrationStep, other: MigrationStep) -> bool:
    """Two field steps act on the same field iff they name the same model and
    the same field (compared case-insensitively, hence on the lower-cased
    names)."""
    Requires(Acc(this.model_name_lower, 1 / 4) and Acc(this.name_lower, 1 / 4))
    Requires(Acc(other.model_name_lower, 1 / 4) and Acc(other.name_lower, 1 / 4))
    return (this.model_name_lower == other.model_name_lower
            and this.name_lower == other.name_lower)


@Pure
def joined_by_field_rule(this: MigrationStep, nxt: MigrationStep) -> bool:
    """The same-field rules resolve this pair: the two steps touch the same
    field and the later one either alters it again, removes it, or renames it
    while the alteration pins no explicit stored-column name."""
    Requires(Acc(this.model_name_lower, 1 / 4) and Acc(this.name_lower, 1 / 4)
             and Acc(this.has_explicit_column, 1 / 4))
    Requires(Acc(nxt.model_name_lower, 1 / 4) and Acc(nxt.name_lower, 1 / 4)
             and Acc(nxt.kind, 1 / 4))
    return (is_same_field(this, nxt)
            and (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE
                 or (nxt.kind == KIND_RENAME
                     and not this.has_explicit_column)))


@Pure
def elides_to_one_step(this: MigrationStep, nxt: MigrationStep) -> bool:
    """No same-field rule resolves the pair, yet one of the two steps carries
    the elidable mark, so the pair still reduces to a single step."""
    Requires(Acc(this.model_name_lower, 1 / 4) and Acc(this.name_lower, 1 / 4)
             and Acc(this.has_explicit_column, 1 / 4) and Acc(this.elidable, 1 / 4))
    Requires(Acc(nxt.model_name_lower, 1 / 4) and Acc(nxt.name_lower, 1 / 4)
             and Acc(nxt.kind, 1 / 4) and Acc(nxt.elidable, 1 / 4))
    return (not joined_by_field_rule(this, nxt)
            and (this.elidable or nxt.elidable))
# pure-end


def reduce(this: MigrationStep, nxt: MigrationStep,
           nxt_references_altered_field: bool
           ) -> Tuple[Optional[List[MigrationStep]], bool]:
    # pre-conditions-start
    Requires(Acc(this.kind, 1 / 2) and Acc(this.model_name_lower, 1 / 2)
             and Acc(this.name_lower, 1 / 2) and Acc(this.has_explicit_column, 1 / 2)
             and Acc(this.elidable, 1 / 2))
    Requires(Acc(nxt.kind, 1 / 2) and Acc(nxt.model_name_lower, 1 / 2)
             and Acc(nxt.name_lower, 1 / 2) and Acc(nxt.elidable, 1 / 2))
    # A NEW NAME is a facet only a RENAMING step has. A step of any other kind
    # carries no new name at all — just as the altering step itself carries
    # none, which is why no access to `this.new_name_lower` is asked for
    # either — and in the real program reading a facet off a step that has none
    # is not a value at all but a failure. So the reduction is lent the later
    # step's new name only when that step is a rename: it may consult that
    # facet only after establishing the later step IS a rename, never
    # unconditionally, and an answer it could reach only by consulting a new
    # name that is not there is not an answer this routine may give.
    Requires(Implies(nxt.kind == KIND_RENAME, Acc(nxt.new_name_lower, 1 / 2)))
    Requires(this.kind == KIND_ALTER)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(this.kind, 1 / 2) and Acc(this.model_name_lower, 1 / 2)
            and Acc(this.name_lower, 1 / 2) and Acc(this.has_explicit_column, 1 / 2)
            and Acc(this.elidable, 1 / 2))
    Ensures(Acc(nxt.kind, 1 / 2) and Acc(nxt.model_name_lower, 1 / 2)
            and Acc(nxt.name_lower, 1 / 2) and Acc(nxt.elidable, 1 / 2))
    # The rename-only facet is handed back on exactly the condition it was lent.
    Ensures(Implies(nxt.kind == KIND_RENAME, Acc(nxt.new_name_lower, 1 / 2)))
    # When a list is returned, the caller owns it (and its fresh carried step).
    Ensures(Implies(Result()[0] is not None, Acc(list_pred(Result()[0]))))
    # The two answers are exclusive: combining the pair asks no reordering
    # question, so the verdict is normalised to False whenever steps come back.
    Ensures(Implies(Result()[0] is not None, not Result()[1]))
    # The collapsing cases (1) remove and (2) alter on the same field: the pair
    # is reduced to exactly the later step, on its own.
    Ensures(Implies(nxt.kind == KIND_REMOVE and is_same_field(this, nxt),
                    Result()[0] is not None and len(Result()[0]) == 1
                    and Result()[0][0] is nxt))
    Ensures(Implies(nxt.kind == KIND_ALTER and is_same_field(this, nxt),
                    Result()[0] is not None and len(Result()[0]) == 1
                    and Result()[0][0] is nxt))
    # The two collapsing cases agree: same-field alter and same-field remove
    # both yield the singleton [later step]. (Symmetry of the reduction.)
    Ensures(Implies((nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE)
                    and is_same_field(this, nxt),
                    Result()[0] is not None and len(Result()[0]) == 1
                    and Result()[0][0] is nxt))
    # Rename carry-across on the same field with no explicit pinned column: the
    # result is the rename followed by an equivalent alteration of the field
    # under its new name (two steps, the rename first). The carried second
    # step is one the reduction BUILDS, so it is neither of the two steps it was
    # handed; it is itself an ALTER step on the SAME model, targeting the field
    # under its renamed name, and it keeps the original step's field
    # definition (hence the same pinned-column status); being a plain
    # alteration it carries no elidable mark of its own. It is an alteration, so
    # a new name is not among the facets it carries and there is none to pin or
    # to read off it; the name it is BUILT UNDER is the new name of the RENAME it
    # is carried across, which is the later step's facet and is pinned as this
    # step's plain name. Every facet the carried step does carry is pinned here,
    # so it is determined outright.
    Ensures(Implies(nxt.kind == KIND_RENAME and is_same_field(this, nxt)
                    and not this.has_explicit_column,
                    Result()[0] is not None and len(Result()[0]) == 2
                    and Result()[0][0] is nxt and Result()[0][1] is not nxt
                    and Result()[0][1] is not this
                    and Acc(Result()[0][1].kind)
                    and Result()[0][1].kind == KIND_ALTER
                    and Acc(Result()[0][1].model_name_lower)
                    and Result()[0][1].model_name_lower == this.model_name_lower
                    and Acc(Result()[0][1].name_lower)
                    and Result()[0][1].name_lower == nxt.new_name_lower
                    and Acc(Result()[0][1].has_explicit_column)
                    and Result()[0][1].has_explicit_column
                    == this.has_explicit_column
                    and Acc(Result()[0][1].elidable)
                    and not Result()[0][1].elidable))
    # A pair no same-field rule resolves is decided by the two elidable marks,
    # the EARLIER step's mark taking precedence: an elidable earlier step leaves
    # just the later step, an elidable later step leaves just the earlier one.
    Ensures(Implies(not joined_by_field_rule(this, nxt) and this.elidable,
                    Result()[0] is not None and len(Result()[0]) == 1
                    and Result()[0][0] is nxt))
    Ensures(Implies(not joined_by_field_rule(this, nxt)
                    and not this.elidable and nxt.elidable,
                    Result()[0] is not None and len(Result()[0]) == 1
                    and Result()[0][0] is this))
    # With neither mark set the pair is not combined here, and the answer is
    # the REORDERING VERDICT instead: the caller may optimize across the later
    # step exactly when that step does not reference the altered field. The
    # verdict is not a constant — withholding permission for a step that
    # touches the altered field is what keeps an unrelated step from being
    # reordered past the alteration, and granting it for a step that does not
    # is what lets a collapsible pair separated by such a step still collapse.
    Ensures(Implies(not joined_by_field_rule(this, nxt)
                    and not this.elidable and not nxt.elidable,
                    Result()[0] is None
                    and Result()[1] == (not nxt_references_altered_field)))
    # A later step on a DIFFERENT field is never collapsed by the same-field
    # rules, so with neither elidable mark set such a pair is not combined and
    # yields the same reordering verdict.
    Ensures(Implies(not is_same_field(this, nxt)
                    and not this.elidable and not nxt.elidable,
                    Result()[0] is None
                    and Result()[1] == (not nxt_references_altered_field)))
    # Conversely, the pair is combined here EXACTLY when a same-field rule
    # resolves it or one of the two elidable marks does; in every other case
    # the reordering verdict is the answer.
    Ensures((Result()[0] is not None)
            == (joined_by_field_rule(this, nxt)
                or elides_to_one_step(this, nxt)))
    # post-conditions-end
    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end

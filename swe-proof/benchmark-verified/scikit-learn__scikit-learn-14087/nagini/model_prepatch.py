"""Twin-artifact model for scikit-learn__scikit-learn-14087.

Behaviour under specification (stated as desired behaviour, not as an edit):

A cross-validated linear classifier, when it summarises the cross-validation
outcome WITHOUT re-fitting, performs two per-class record-keeping steps. The
classifier consults two categorical settings: an effective per-class strategy
and a regularisation family.

  (1) Selecting the best per-class summary across folds.
      The per-class strategy is one of two concrete forms: a per-class-
      independent form, or a joint form. It is consulted in an UNRESOLVED form
      that admits a third, deferred value standing for "decide later"; the
      concrete form actually in effect is the resolved one (one of the two
      concrete forms). The per-class summary table is laid out with a number of
      index axes determined by the concrete strategy in effect: the joint form
      carries one extra leading axis. Reading the best summary across folds
      must address that table with an index arity equal to its actual number of
      axes, for every admissible input. The observable behaviour is that this
      read is always admissible (no out-of-range axis access).

  (2) Recording the per-class regularisation-mixing value.
      A mixing value exists only for the regularisation family that carries a
      mixing parameter. For that family the per-class record is the value
      selected from the candidate-mixing table. For every other family the
      candidate table holds no mixing value at all — only an "absent"
      placeholder — so selecting from it yields nothing that could be recorded;
      the observable behaviour is that no such selection is performed for that
      family at any point in the step, and the per-class record is the explicit
      "absent" marker.
      The candidate-mixing table also has a definite EXTENT (a number of
      entries), settled before the step runs. A selection addresses one of the
      entries that table actually holds: the observable behaviour is that every
      selection the step performs stays within the table's own extent (no
      out-of-range entry access), for every admissible input.

The categorical settings are modelled as small integer tags; the concrete
strategy in effect is guaranteed (precondition) to be one of the two resolved
forms. The summary table's layout is modelled by its index-axis rank (an int);
the gathered summary vector and the mixing value are modelled as identity
tokens / an Optional sentinel — the tested observable is that the index arity
matches the layout (an admissible read) and the "absent" marker, not the
numeric values (Nagini cannot express the numeric arrays, and the tested
behaviour is value-independent; see mapping.md and refinement.md).

Likewise there is exactly ONE candidate-mixing table in effect for the
recording step, modelled as a RESOURCE the step is handed and hands back
(`candidate_table(holds_mixing_values, actual_len)`, an abstract predicate
carrying BOTH whether that table's entries are real mixing values AND the
table's ACTUAL extent — how many entries it has). Selecting a mixing value is a
PARTIAL operation on it, admissible only against a held table whose entries are
real, so the selection cannot be performed at all for the family whose table
holds only the placeholder — which is what makes "no mixing value exists for
that family" an observable rather than a claim about the delivered value alone.
For the same reason the extent a selection's position is checked against is the
HELD table's own extent and never a bound the selector names for itself: because
performing a selection CONSUMES this resource at the extent the position is
checked against, EVERY selection the step performs — not merely the one whose
value it records — addresses a position the candidate table in effect actually
has, which is what "the selection stays within the table" means when a step may
address the table more than once.

There is exactly ONE per-class summary table in effect for the step, and it
is modelled as a RESOURCE the step is handed and hands back
(`summary_table(actual_rank)`, an abstract predicate carrying the table's
actual number of index axes) rather than as a rank the reader supplies for
itself. EVERY across-folds read is performed against that one held table, so
the arity of every read the step performs — not merely the read whose value is
delivered — is compared against the actual layout. Alongside it, the
admissibility of the read is pinned by an UNFORGEABLE capability token
(`read_admissible(rank)`, an abstract predicate over the axis rank the read
was checked against): the only way to obtain it is via `read_across_folds`,
which is invoked against the held table, requires the read arity to equal that
table's actual rank, and grants the token AT that rank. The result-side
obligation demands the token at the table's ACTUAL axis rank, so an
implementation cannot discharge the contract by merely returning a summary
value; and because no read can be performed except against the held table,
neither can it address the table at a rank of its own choosing — at any point
in the step, whether or not that read is the one it delivers.

Both record-keeping steps are TOTAL: the observable behaviour includes that
each step actually completes and delivers its record. Nagini checks partial
correctness by default — a diverging body would satisfy every postcondition
vacuously — so every function carries a ``MustTerminate`` obligation (with a
strictly smaller measure for the callee) to reject non-terminating
implementations.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# UNFORGEABLE capability token witnessing that the across-folds read was
# admissible AT a given axis rank (the read's index arity matched that rank).
# It is abstract (no body), so no implementation can `Fold` or otherwise
# fabricate it; the ONLY way to obtain it is to call `read_across_folds`,
# whose precondition forces the read arity to equal the rank it is invoked
# with, and which grants the token at exactly that rank. `gather_per_class`'s
# result-side obligation demands the token at the table's ACTUAL rank
# (`table_axes`), so an implementation that returns a summary value WITHOUT a
# read, or that performs a read checked against a self-consistent rank other
# than the actual layout's, cannot discharge the contract. This pins the
# admissibility behaviour the desired contract demands; the returned-value
# equality alone would be an echoable constant.
@ContractOnly
@Predicate
def read_admissible(checked_rank: int) -> bool:
    pass


# The ONE per-class summary table in effect for the record-keeping step,
# carried together with its ACTUAL number of index axes. This is a RESOURCE,
# not a value: to hold `summary_table(r)` is to hold the single table whose
# layout carries exactly `r` index axes. It is abstract (no body), so no
# implementation can `Fold` or otherwise conjure a table laid out at a rank of
# its own choosing; the step is handed the one table that exists and hands it
# back. Because performing an across-folds read CONSUMES this resource at the
# rank the read is checked against, EVERY read the step performs — not merely
# the one whose value it delivers — is checked against the actual layout of
# the table it holds, which is what "the read is always admissible" means when
# a step may address the table more than once.
@ContractOnly
@Predicate
def summary_table(actual_rank: int) -> bool:
    pass


# The across-folds read of the per-class summary table. The read expression
# consumes `gather_arity(use_joint_layout)` index axes; the table it is
# invoked against carries `table_rank` axes. The read is admissible ONLY when
# the two agree (otherwise it addresses a non-existent axis). Returns the
# gathered summary vector and grants the `read_admissible` capability AT the
# rank the read was checked against — the caller's obligation to hold the
# token at the layout's ACTUAL rank is what ties the read to the real table.
# This is the unchanged numeric read of the surrounding code (an indexed mean
# over folds), modelled deeply over its index arity; axiom_check.py / G-AX
# validates the arity / out-of-range behaviour against the real array indexing.
@ContractOnly
def read_across_folds(use_joint_layout: bool, table_rank: int,
                      summary_token: int) -> int:
    # Terminates: a bounded indexed mean over finitely many folds; measure
    # 1 lets any caller holding MustTerminate(2) perform the read without
    # leaking its own obligation.
    Requires(MustTerminate(1))
    # The read addresses the ONE summary table in effect, whose actual layout
    # carries `table_rank` index axes. The rank the read is checked against is
    # therefore the held table's, never a rank the reader names for itself.
    Requires(summary_table(table_rank))
    Requires(gather_arity(use_joint_layout) == table_rank)
    Ensures(Result() == summary_token)
    # The table is handed back unchanged, so addressing it again with a
    # matching arity stays admissible.
    Ensures(summary_table(table_rank))
    Ensures(read_admissible(table_rank))
# The per-class candidate-mixing table in effect for the recording step,
# carried together with WHETHER its entries are real mixing values AND its
# ACTUAL extent (the number of entries it holds). This is a RESOURCE, not a
# value: to hold `candidate_table(True, n)` is to hold the single candidate
# table whose entries are actual mixing values and which has exactly `n`
# entries, and `candidate_table(False, n)` a table of `n` entries carrying only
# the explicit "absent" placeholder. It is abstract (no body), so no
# implementation can `Fold` or otherwise conjure a table whose entries it
# declares real for itself, nor one longer than the table the step was handed;
# the step is handed the one candidate table that exists and hands it back.
# Carrying the extent alongside the entry reality is what makes the in-range
# condition of a selection a property of the HELD table rather than a bound the
# selector supplies for itself — the site-2 counterpart of `summary_table`.
@ContractOnly
@Predicate
def candidate_table(holds_mixing_values: bool, actual_len: int) -> bool:
    pass


# UNFORGEABLE capability witnessing that a mixing value was actually SELECTED
# from the candidate-mixing table. It is abstract (no body), so no
# implementation can `Fold` or otherwise fabricate it; the ONLY way to obtain it
# is to call `select_mixing_value`, whose precondition forces the table it
# selects from to be one that holds real mixing values. A step that records a
# mixing value must hold it, so recording a value the step never selected — and
# in particular recording one for the family whose table holds no mixing values
# — cannot discharge the contract.
@ContractOnly
@Predicate
def mixing_selected() -> bool:
    pass


# Selecting the mixing value at the chosen position of the candidate-mixing
# table. This selection is a PARTIAL operation on the table it addresses: it
# yields a mixing value only for a table whose entries are real mixing values.
# For the family that carries no mixing parameter the candidate table holds the
# "absent" placeholder alone, and averaging that placeholder yields no mixing
# value at all — so the selection is admissible ONLY against a table whose
# entries are real (`Requires(holds_mixing_values)`), and only against the ONE
# table the step holds (`Requires(candidate_table(...))`, so the reality of the
# entries is the held table's and never a property the selector asserts of
# itself). It is likewise admissible ONLY at a position the held table actually
# has: the extent the position is checked against is the held table's own extent
# (`candidate_table(..., candidates_len)`), never a bound the selector names for
# itself, so a position outside the table in effect addresses no entry and no
# selection can be performed there. The table is handed back unchanged. This is
# the unchanged numeric selection of the surrounding code (an averaged lookup at
# the chosen position); axiom_check.py / G-AX validates against real numpy that
# the placeholder table does not average to a mixing value.
@ContractOnly
def select_mixing_value(holds_mixing_values: bool, selected_index: int,
                        candidates_len: int, mixing_value: int) -> int:
    Requires(MustTerminate(1))
    # The selection addresses the ONE candidate table in effect, whose entries'
    # reality is `holds_mixing_values` and whose ACTUAL extent is
    # `candidates_len`. Both facts are therefore the held table's, never
    # properties the selector asserts of itself.
    Requires(candidate_table(holds_mixing_values, candidates_len))
    Requires(holds_mixing_values)
    # The position selected is one the held table actually has.
    Requires(0 <= selected_index and selected_index < candidates_len)
    Ensures(Result() == mixing_value)
    Ensures(candidate_table(holds_mixing_values, candidates_len))
    Ensures(mixing_selected())
# axioms-end


# pure-start
# Categorical encodings of the per-class strategy.
INDEPENDENT = 0   # per-class-independent strategy
JOINT = 1         # joint strategy (one extra leading layout axis)
UNRESOLVED = 2    # the deferred "decide later" form (never a concrete value)


@Pure
def table_rank(resolved_strategy: int) -> int:
    """The number of leading index axes the per-class summary table carries, as
    a function of the concrete strategy in effect: the joint form carries one
    extra leading axis (4) over the per-class-independent form (3). Defined only
    for the two concrete strategies."""
    Requires(resolved_strategy == INDEPENDENT or resolved_strategy == JOINT)
    if resolved_strategy == INDEPENDENT:
        return 3
    return 4


@Pure
def gather_arity(use_joint_layout: bool) -> int:
    """The number of index axes consumed by the across-folds read expression:
    the per-class-independent read addresses [fold, best, :] (3 axes); the joint
    read addresses [:, fold, best, :] (4 axes)."""
    if use_joint_layout:
        return 4
    return 3
# pure-end


def gather_per_class(resolved_strategy: int, unresolved_form: int,
                     table_axes: int, summary_token: int) -> int:
    # pre-conditions-start
    # The gather step must complete and deliver its summary: a diverging body
    # would satisfy every postcondition vacuously under partial correctness,
    # yet the observable behaviour is that the record-keeping step finishes.
    Requires(MustTerminate(2))
    # The strategy in effect is one of the two concrete forms (never the
    # deferred form).
    Requires(resolved_strategy == INDEPENDENT or resolved_strategy == JOINT)
    # The unresolved form may be any of the three values.
    Requires(unresolved_form == INDEPENDENT or unresolved_form == JOINT
             or unresolved_form == UNRESOLVED)
    # The summary table's layout (its index-axis rank) is built from the
    # concrete strategy in effect.
    Requires(table_axes == table_rank(resolved_strategy))
    # The step is handed the ONE per-class summary table in effect, whose
    # actual layout carries `table_axes` index axes. It is the only table the
    # step has to address; a read can be performed against nothing else.
    Requires(summary_table(table_axes))
    # pre-conditions-end
    # post-conditions-start
    # The returned summary token is the gathered per-class vector.
    Ensures(Result() == summary_token)
    # The across-folds read was admissible AT THE TABLE'S ACTUAL AXIS RANK for
    # this (any admissible) input — its index arity matched the actual layout.
    # This capability can ONLY be obtained from `read_across_folds`, which
    # grants it at the rank the read was checked against; demanding it at
    # `table_axes` rules out both fabricating the token and checking the read
    # against a self-consistent rank other than the actual layout's, so an
    # implementation whose read arity could disagree with the table layout (in
    # particular when the deferred form is supplied) cannot discharge it.
    Ensures(read_admissible(table_axes))
    # The step still holds the same summary table it was handed, at the same
    # actual axis rank: it addresses the table in effect throughout and never
    # exchanges it for a differently-laid-out one. Together with the read
    # addressing only the held table, this makes EVERY read the step performs
    # — not just the one it delivers — an arity-matching read of the actual
    # layout, for every admissible input.
    Ensures(summary_table(table_axes))
    # post-conditions-end
    # impl-start
    # (pre-patch site 1) Address the table with the arity determined by the
    # UNRESOLVED form rather than the strategy actually in effect.
    use_joint_layout = unresolved_form != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w
    # impl-end


def mixing_record(family_has_mixing: bool, selected_index: int,
                  candidates_len: int,
                  mixing_value: int) -> Optional[int]:
    # pre-conditions-start
    # The recording step must complete and deliver its record: a diverging
    # body would satisfy every postcondition vacuously under partial
    # correctness, yet the observable behaviour is that the record-keeping
    # step finishes.
    Requires(MustTerminate(2))
    # The candidate-mixing table has at least one entry, and the selected
    # position is within it.
    Requires(candidates_len >= 1)
    Requires(0 <= selected_index and selected_index < candidates_len)
    # A family without a mixing parameter carries a single-entry candidate
    # table (there are no mixing values to choose among).
    Requires(Implies(not family_has_mixing, candidates_len == 1))
    # mixing_value is the selected mixing value (defined only for the family
    # that carries one).
    # The step is handed the ONE candidate-mixing table in effect. Its entries
    # are real mixing values exactly for the family that carries a mixing
    # parameter; for every other family the table holds only the "absent"
    # placeholder. Its ACTUAL extent is `candidates_len` entries. It is the only
    # candidate table the step has to address; a selection can be performed
    # against nothing else, and only at a position within that extent.
    Requires(candidate_table(family_has_mixing, candidates_len))
    # pre-conditions-end
    # post-conditions-start
    # The per-class mixing record is a value EXACTLY when the family carries a
    # mixing parameter; otherwise it is the explicit "absent" marker.
    Ensures(Implies(family_has_mixing, Result() is not None
                    and Result() == mixing_value))
    Ensures(Implies(not family_has_mixing, Result() is None))
    # The step still holds the same candidate-mixing table it was handed, with
    # the same entry reality AND the same actual extent: it addresses the table
    # in effect throughout and never exchanges it for one whose entries it
    # treats as real when they are not, nor for one it treats as longer than it
    # is. Because a selection is performable only against the held table, only
    # when that table's entries are real mixing values, and only at a position
    # within that table's actual extent, EVERY selection the step performs —
    # not merely the one whose value is delivered — is a selection of an entry
    # the candidate table in effect actually holds. So for the family carrying
    # no mixing parameter the step performs NO selection from the placeholder
    # table at all, at any point, rather than selecting from it and then
    # substituting the "absent" marker for the result; and for the family that
    # does carry a mixing parameter no selection anywhere in the step reaches
    # past the end of the candidate table.
    Ensures(candidate_table(family_has_mixing, candidates_len))
    # Whenever a mixing value is recorded, it was actually SELECTED from the
    # held candidate-mixing table. This capability can ONLY be obtained from
    # that selection, which is admissible only against a table whose entries
    # are real mixing values and only at a position within that table's actual
    # extent, so a step cannot record a value it did not select — nor select
    # from the placeholder table and substitute the marker, nor obtain it from a
    # selection past the end of the table it holds.
    Ensures(Implies(family_has_mixing, mixing_selected()))
    # post-conditions-end
    # impl-start
    if family_has_mixing:
        # The family carries a mixing parameter: select the value from the
        # candidate table and record it.
        entry = select_mixing_value(family_has_mixing, selected_index,
                                    candidates_len,
                                    mixing_value)  # type: Optional[int]
    else:
        # No mixing parameter for this family: the candidate table holds only
        # the absent placeholder, so nothing is selected from it — record the
        # explicit absent marker.
        entry = None
    return entry
    # impl-end

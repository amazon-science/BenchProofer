"""Twin-artifact model for django__django-14631.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a form cleans a field whose input is taken from its bound initial value
  (the case where the field does not draw its value from submitted data, so the
  bound initial is the value to be cleaned), the cleaned value MUST equal the
  value exposed as that field's bound initial.

  The bound initial value has two defining properties:

    (1) the underlying initial source is evaluated EXACTLY ONCE and the single
        resulting value is reused (it is cached) — even when the source is a
        callable that would yield a different value on each evaluation; and

    (2) for an auto-generated date/time value whose presentation widget does
        not carry sub-second precision, the sub-second component is dropped
        (normalised), for standardised handling.

  Consequently the value produced when cleaning such a field must match the
  field's bound initial value exactly: it must be the SAME single evaluation,
  and it must be the NORMALISED (sub-second-stripped) form — never a fresh,
  un-normalised re-evaluation of the source.

  Moreover, evaluating the initial source is a STATEFUL operation: a callable
  source may advance its own state on every call, so any EXTRA evaluation —
  even one whose result is immediately discarded — can change which value the
  single cached evaluation captures (an extra call made before the cached
  bound initial is first read shifts the cache to a later evaluation).
  Cleaning the field therefore has NO RIGHT to evaluate the source afresh: it
  may only read the already-cached bound initial. In the model this is
  encoded by granting the cleaning function NO permission at all to
  `fresh_eval`: an implementation that so much as READS the fresh
  re-evaluation (i.e. performs a second evaluation of the source, even a
  dead one) fails verification for insufficient permission.

The field is modelled as a minimal class carrying only the touched quantities:
the value of the first evaluation of the initial source (`first_eval`), the
value a second, independent evaluation would yield (`fresh_eval`, distinct for a
stateful source), and the cached bound initial. A date/time value is modelled as
an integer encoding `whole_seconds * 1_000_000 + sub_second_units`; dropping the
sub-second component is modelled by `normalise`. Cleaning such a field is the
identity on the value it is given (a date/time value validates to itself).

Cleaning a field is a bounded, per-field step of form validation: it MUST
terminate and produce the cleaned value (a total-correctness obligation,
carried as MustTerminate in the precondition). An implementation that
diverges — e.g. hangs inside the cleaning step instead of producing the
value — would satisfy the value postconditions only vacuously and would hang
form validation (and the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class FieldState:
    def __init__(self, first_eval: int, fresh_eval: int) -> None:
        Requires(first_eval >= 0 and fresh_eval >= 0)
        Ensures(Acc(self.first_eval, 1 / 2) and self.first_eval == first_eval)  # type: ignore
        Ensures(Acc(self.fresh_eval, 1 / 2) and self.fresh_eval == fresh_eval)  # type: ignore
        self.first_eval = first_eval
        self.fresh_eval = fresh_eval


# axioms-start
# (no @ContractOnly axioms are consumed: every operation the cleaned-value
# computation performs — the single normalised evaluation read from the bound
# initial, and the identity clean of a date/time value — is modelled deeply.)
# axioms-end


# pure-start
@Pure
def normalise(value: int) -> int:
    """Drop the sub-second component of an encoded date/time value. The
    encoding is `whole_seconds * 1_000_000 + sub_second_units` with
    `0 <= sub_second_units < 1_000_000`; normalisation floors to the whole
    second. Idempotent and a function of its argument alone."""
    Requires(value >= 0)
    Ensures(Result() >= 0)
    Ensures(Result() == (value // 1000000) * 1000000)
    return (value // 1000000) * 1000000


@Pure
def bound_initial(fs: FieldState) -> int:
    """The value exposed as the field's bound initial: the NORMALISED form of
    the SINGLE (first) evaluation of the initial source. This is the cached
    value reused everywhere the bound initial is read."""
    Requires(Acc(fs.first_eval, 1 / 4))
    Requires(fs.first_eval >= 0)
    Ensures(Result() == normalise(fs.first_eval))
    return normalise(fs.first_eval)
# pure-end


def clean_bound_initial_field(fs: FieldState) -> int:
    # pre-conditions-start
    Requires(Acc(fs.first_eval, 1 / 2))
    Requires(fs.first_eval >= 0)
    # DELIBERATELY NO permission to fs.fresh_eval: evaluating the initial
    # source is a stateful operation (a callable source advances its state on
    # every call), so ANY extra evaluation — even one whose result is
    # immediately discarded — shifts which value the single cached evaluation
    # captures and breaks cleaned == bound initial in the real form machinery.
    # Cleaning may only read the already-cached bound initial; an impl that so
    # much as READS fs.fresh_eval (performs a second evaluation of the source)
    # must fail verification for insufficient permission.
    # Cleaning a field is a bounded step of form validation: it MUST terminate
    # (total correctness). A diverging impl (e.g. hanging inside the cleaning
    # step instead of producing the cleaned value) would satisfy the value
    # postconditions only vacuously and hang form validation (and the F2P
    # test) forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(fs.first_eval, 1 / 2))
    Ensures(fs.first_eval >= 0)
    # The cleaned value equals the field's bound initial value: the single,
    # cached evaluation of the source...
    Ensures(Result() == bound_initial(fs))
    # ...grounded in the inputs: it is the NORMALISED form of the first (the
    # only) evaluation of the initial source, never a fresh re-evaluation.
    Ensures(Result() == normalise(fs.first_eval))
    # post-conditions-end
    # impl-start
    # Read the value through the field's bound initial (single cached,
    # normalised evaluation), then clean it. Cleaning a date/time value is the
    # identity on the value it is given.
    value = bound_initial(fs)
    cleaned = value
    return cleaned
    # impl-end

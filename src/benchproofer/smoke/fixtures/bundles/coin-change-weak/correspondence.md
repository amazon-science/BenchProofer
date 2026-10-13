# Where each obligation comes from

The task asks `make_change` to break an amount in cents into the fewest US coins.
This specification states only that the coins add up to the amount.

- `def property_change_sums_to_the_amount(cents):` -> `make_change`, `change.py`
- `assert quarters * 25 + dimes * 10 + nickels * 5 + pennies == cents` -> `quarters`, `pennies`

The part of the task about using the fewest coins is not stated here, which is why
the pre-fix implementation still satisfies this specification. Correspondence asks
whether every obligation is traceable to the task, not whether the task is fully
covered, so this file is honest and the specification is still too weak: the two
gates that attack strength are the ones that say so.

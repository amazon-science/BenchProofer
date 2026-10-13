# Where each obligation comes from

The task asks `make_change` to break an amount in cents into the fewest US coins.
Conservation is the first property; the three inequalities are what "fewest" means
for these denominations, since leaving five pennies where a nickel would do, or two
nickels where a dime would do, is exactly what the pre-fix code did.

- `def property_change_sums_to_the_amount(cents):` -> `make_change`, `change.py`
- `assert quarters * 25 + dimes * 10 + nickels * 5 + pennies == cents` -> `quarters`, `pennies`
- `def property_change_uses_no_negative_coin(cents):` -> `make_change`, `cents`
- `assert all(count >= 0 for count in impl(cents))` -> `make_change`, `change.py`
- `def property_change_is_the_fewest_coins(cents):` -> `make_change`, `change.py`
- `assert dimes * 10 + nickels * 5 + pennies < 25` -> `quarters`, `change.py`
- `assert nickels * 5 + pennies < 10` -> `dimes`, `change.py`
- `assert pennies < 5` -> `nickels`, `change.py`

Nothing in the task constrains the order of the tuple beyond the docstring of
`make_change`, which names it, so the specification reads the tuple positionally and
says nothing else about the shape of the result.

# Where each obligation comes from

The task asks for the partial sums of a list, one per element.

- `def property_running_total_matches_the_reference(values):` -> `running_total`, `totals.py`
- `assert impl(values) == totals` -> `running_total`, `totals.py`

Every obligation traces to the task, and the specification is still worthless: it
states the result by recomputing it the way the benchmark's own solution does. That
is what the leakage gate is for, and no verification result would have revealed it.

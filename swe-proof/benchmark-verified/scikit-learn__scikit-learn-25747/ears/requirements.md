# Requirements: Preserve a transformer's own row index when wrapping pandas output

## Introduction

scikit-learn lets estimators emit their `transform` output as a pandas
`DataFrame` (via `set_config(transform_output="pandas")` or a per-estimator
`set_output(transform="pandas")`). The wrapping is performed by the helper
`_wrap_in_pandas_container` in `sklearn/utils/_set_output.py`, which is called
from the output-wrapping machinery in that module (`_wrap_data_with_container`
and the `_SetOutputMixin` method wrapper).

When a transformer's `transform` method returns data whose number of rows
differs from the number of rows of the original input `X` — for example a
transformer that aggregates/groups rows — the wrapper attempted to force the
original input's index onto the already-shaped DataFrame. Because the row counts
no longer match, pandas raised a `ValueError` about a length mismatch, and any
composition that aggregates rows (such as a feature union over such a
transformer) failed under pandas output while working under the default numpy
output.

The goal is: when the data being wrapped is already a pandas `DataFrame`, the
wrapper must leave that DataFrame's own row index untouched, so that
transformers which change the number or labeling of rows produce pandas output
without error. All other wrapping behavior — column relabeling, array wrapping,
sparse rejection — must be preserved.

The affected module is `sklearn/utils/_set_output.py`; the primary behavioral
surface is the helper `_wrap_in_pandas_container`.

## Requirement 1: Keep an existing DataFrame's row index

**User story:** As a user configuring pandas transform output, I want a
transformer that returns a DataFrame to keep the index it produced, so that
transformers which aggregate or re-index rows do not fail.

**Acceptance criteria**

1. WHEN `_wrap_in_pandas_container` is called with `data_to_wrap` that is
   already a pandas `DataFrame`, THEN the wrapper SHALL return a DataFrame whose
   row index is exactly the row index carried by that input DataFrame.
2. WHEN `data_to_wrap` is already a `DataFrame` and an `index` argument is also
   supplied, THEN the wrapper SHALL ignore the supplied `index` and SHALL NOT
   modify the DataFrame's row index.
3. WHEN a transformer configured for pandas output returns a `DataFrame` whose
   number of rows differs from the number of rows of the estimator's input,
   THEN the wrapped result SHALL be returned without raising, and its row index
   SHALL be the index of the returned DataFrame.
4. WHEN a transformer configured for pandas output returns a `DataFrame` that
   carries specific row labels, THEN the wrapped output SHALL expose those same
   row labels unchanged.
5. The system SHALL preserve the row count of an already-DataFrame
   `data_to_wrap`; the number of rows in the returned container SHALL equal the
   number of rows of that input DataFrame.

## Requirement 2: Continue relabeling columns of an existing DataFrame

**User story:** As a maintainer, I want column relabeling to keep working, so
that pandas output still carries the estimator's feature names.

**Acceptance criteria**

1. WHEN `data_to_wrap` is already a `DataFrame` and non-null `columns` are
   supplied, THEN the wrapper SHALL set the returned DataFrame's column labels
   to those supplied columns.
2. IF `columns` is a callable, THEN the wrapper SHALL invoke it to obtain the
   column labels, and IF that call raises, THEN the wrapper SHALL treat
   `columns` as unspecified and SHALL leave the DataFrame's existing column
   labels unchanged.
3. WHEN `data_to_wrap` is already a `DataFrame` and `columns` is unspecified
   (`None`), THEN the wrapper SHALL leave the DataFrame's existing column labels
   unchanged.

## Requirement 3: Preserve array-wrapping behavior

**User story:** As a maintainer, I want plain array output to still be wrapped
into a DataFrame with the given index and columns, so that non-DataFrame
transformers are unaffected by the fix.

**Acceptance criteria**

1. WHEN `data_to_wrap` is not a pandas `DataFrame` (for example a NumPy array),
   THEN the wrapper SHALL construct and return a new `DataFrame` built from that
   data using the supplied `index` and `columns` arguments.
2. WHEN a new DataFrame is constructed and an `index` is supplied, THEN the
   returned DataFrame's row index SHALL be that supplied `index`.
3. WHEN a new DataFrame is constructed and `columns` is supplied, THEN the
   returned DataFrame's column labels SHALL be those supplied `columns`.

## Requirement 4: Preserve sparse-input rejection

**User story:** As a maintainer, I want sparse inputs to keep being rejected, so
that pandas output continues to fail loudly for unsupported data.

**Acceptance criteria**

1. IF `data_to_wrap` is a scipy sparse matrix, THEN the wrapper SHALL raise a
   `ValueError` indicating that pandas output does not support sparse data.

## Requirement 5: Preserve end-to-end set_output behavior

**User story:** As a user of the set_output API, I want the existing
configuration and dispatch behavior to remain intact, so that only the index
handling changes.

**Acceptance criteria**

1. WHEN an estimator has `set_output(transform="pandas")` (or the global config
   selects pandas output) and its `transform` returns a `DataFrame`, THEN the
   value delivered to the caller SHALL be that DataFrame with its own row index
   preserved.
2. The system SHALL continue to resolve the effective output container from the
   per-estimator setting when present and otherwise from the global
   configuration, keeping the existing precedence.
3. WHEN the configured output is the default (numpy) container, THEN the
   wrapper's behavior SHALL be unchanged and the transformer's output SHALL be
   returned as before.

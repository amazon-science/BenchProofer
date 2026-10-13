# Requirements: Propagate the output-container choice to a composite transformer's fall-back transformer

## Introduction

`ColumnTransformer` (in `sklearn/compose/_column_transformer.py`) is a composite
estimator that applies an ordered collection of sub-transformers to selected
columns of the input, and handles the columns that no sub-transformer claims via
its `remainder` argument. The `remainder` may be one of the two reserved
sentinels — the string `"passthrough"` (keep the leftover columns unchanged) or
`"drop"` (discard them) — or it may itself be an estimator (a transformer) that
processes the leftover columns.

scikit-learn estimators expose a `set_output(transform=...)` method (from the
`_SetOutputMixin` machinery) that chooses the output container of `transform` /
`fit_transform` — `"pandas"` for a `DataFrame`, `"default"` for the native
NumPy/scipy container, or `None` to leave the configuration unchanged. When
`set_output` is called on a `ColumnTransformer`, the chosen container must be
propagated to every contained estimator so the assembled output is consistent.

The defect being corrected: `ColumnTransformer.set_output` propagated the choice
to the sub-transformers listed in `transformers` (and the fitted
`transformers_`) but **ignored the `remainder` transformer when it is an
estimator**. As a result, the fall-back transformer kept its default container
and the assembled `fit_transform` result was not the requested container (e.g.
leftover columns came back as a NumPy-backed block instead of the expected
`DataFrame` columns, silently corrupting the combined output). The goal is to
make `set_output` also configure the `remainder` estimator, while leaving the
two reserved sentinels untouched and preserving all previously-working behavior.

## Requirement 1: Propagate the output-container choice to an estimator remainder

**User story:** As a user configuring a `ColumnTransformer` whose leftover
columns are handled by a transformer, I want `set_output` to apply my chosen
output container to that fall-back transformer as well, so that the combined
`fit_transform` result is returned entirely in the container I requested.

**Acceptance criteria**

1. WHEN `set_output(transform=<value>)` is called on a `ColumnTransformer` whose
   `remainder` attribute is an estimator (i.e. not one of the reserved sentinels
   `"passthrough"` or `"drop"`), THEN `ColumnTransformer.set_output` SHALL apply
   the same `transform` output-container choice to that `remainder` estimator.
2. WHEN a `ColumnTransformer` has been configured with `set_output(transform="pandas")`
   and its `remainder` is an estimator, THEN a subsequent `fit_transform` SHALL
   return a pandas `DataFrame` in which the columns produced by the `remainder`
   transformer preserve their original values and column labels rather than being
   coerced through a different container.
3. WHEN the leftover columns handled by an estimator `remainder` should pass
   through with their values unchanged, THEN the assembled pandas output SHALL be
   equal to the corresponding input columns (same values, same dtype-preserving
   content, same labels) and SHALL NOT alter those values.

## Requirement 2: Leave reserved sentinel remainders unchanged

**User story:** As a user who leaves `remainder` at its sentinel value, I want
`set_output` to keep working without error, so that configuring output on a
`ColumnTransformer` with a `"drop"` or `"passthrough"` remainder behaves exactly
as before.

**Acceptance criteria**

1. IF the `remainder` of a `ColumnTransformer` is the reserved string
   `"passthrough"` or `"drop"`, THEN `set_output` SHALL leave the `remainder`
   unchanged and SHALL NOT attempt to configure an output container on it.
2. WHEN `set_output(transform=<value>)` is called on a `ColumnTransformer` whose
   `remainder` is a reserved sentinel, THEN the call SHALL complete without
   raising an error and SHALL behave identically to the pre-existing behavior for
   sentinel remainders.

## Requirement 3: Continue configuring the listed and fitted sub-transformers

**User story:** As a user of `ColumnTransformer`, I want the output-container
choice to keep reaching all of the regular sub-transformers, so that fixing the
`remainder` does not regress the configuration of the other transformers.

**Acceptance criteria**

1. WHEN `set_output(transform=<value>)` is called, THEN `ColumnTransformer.set_output`
   SHALL apply the chosen output container to every estimator among the entries
   of `transformers` and, when present, the fitted `transformers_`.
2. WHILE iterating those entries, `set_output` SHALL skip any entry whose
   transformer is the reserved string `"passthrough"` or `"drop"` and configure
   only the actual estimators.
3. The system SHALL first apply the requested `transform` setting to the
   `ColumnTransformer` itself (its own output configuration via the base
   `set_output` behavior) before configuring the contained estimators and the
   remainder.

## Requirement 4: Preserve the return value and default-container behavior

**User story:** As a user chaining calls, I want `set_output` to keep returning
the estimator and I want the `"default"` setting to keep producing native output,
so that existing pipelines and idioms continue to work.

**Acceptance criteria**

1. WHEN `set_output(transform=<value>)` is called on a `ColumnTransformer`, THEN
   the method SHALL return the same `ColumnTransformer` instance (`self`) to
   support method chaining.
2. WHEN a `ColumnTransformer` (including one with an estimator `remainder`) is
   configured with `set_output(transform="default")`, THEN a subsequent
   `fit_transform` SHALL return the native NumPy array container rather than a
   pandas `DataFrame`.
3. WHEN `set_output` is called with `transform=None`, THEN the output-container
   configuration of the `ColumnTransformer` and its contained transformers SHALL
   remain unchanged.

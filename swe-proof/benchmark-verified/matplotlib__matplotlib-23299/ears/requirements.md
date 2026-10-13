# Requirements: `rc_context` must not revert the rendering backend setting

## Introduction

Matplotlib exposes a context manager, `matplotlib.rc_context` (defined in
`lib/matplotlib/__init__.py`), for temporarily changing runtime configuration
values held in the global `matplotlib.rcParams` mapping. On entry it snapshots
the current configuration; on exit it restores the snapshot so that any changes
made inside the `with` block are undone.

One configuration key, `"backend"`, is special: it names the active rendering
backend, and resolving/restoring it has side effects beyond the value itself.
In particular, reading the `"backend"` entry can trigger backend
resolution, and blindly writing the snapshotted `"backend"` value back on exit
interferes with the global figure registry (`matplotlib._pylab_helpers.Gcf`):
calling `matplotlib.get_backend()` after a figure was created inside an
`rc_context` block was observed to clear all entries from `Gcf.figs`, which then
breaks operations such as closing that figure.

The goal is to make `rc_context` leave the `"backend"` setting untouched by its
restore step — the backend selection is intended to outlive the scoped
override — while continuing to revert every other configuration value exactly as
before, including when the block exits because of an exception.

Affected module/function: `matplotlib.rc_context` in `lib/matplotlib/__init__.py`,
its interaction with `matplotlib.rcParams`, `matplotlib.get_backend`, and the
figure registry `matplotlib._pylab_helpers.Gcf`.

## Requirement 1: Preserve the backend selection across the context manager

**User story:** As a user who sets or changes the rendering backend inside a
temporary configuration block, I want that backend choice to remain in effect
after the block ends, so that my selected backend is not silently discarded.

**Acceptance criteria**

1. WHEN a `rc_context` block exits normally, THEN `rc_context` SHALL leave the
   `"backend"` entry of `rcParams` set to the value it holds at the moment the
   block finishes.
2. IF the `"backend"` value is changed while a `rc_context` block is active,
   THEN after the block exits `rcParams["backend"]` SHALL equal the changed
   value and SHALL NOT be reset to the value it held when the block was entered.
3. WHEN a `rc_context` block exits and the `"backend"` value was not changed
   inside the block, THEN `rcParams["backend"]` SHALL retain its unchanged
   value.
4. The system SHALL NOT overwrite or re-assign the `"backend"` entry of
   `rcParams` as part of the context manager's restore step.

## Requirement 2: Continue reverting all other configuration values

**User story:** As a user relying on `rc_context` for scoped configuration
changes, I want every setting other than the backend to be restored on exit, so
that temporary changes do not leak into surrounding code.

**Acceptance criteria**

1. WHEN a `rc_context` block exits, THEN every `rcParams` entry other than
   `"backend"` SHALL be restored to the value it held at the moment the block
   was entered.
2. IF one or more non-`"backend"` values are modified inside the block, THEN
   after the block exits those entries SHALL hold their pre-block values.
3. The system SHALL restore the non-backend configuration values whether the
   block exits normally or by propagating an exception.
4. WHEN entering a `rc_context` block with an explicit mapping of overrides
   and/or a settings file, THEN those overrides SHALL take effect inside the
   block and (except for `"backend"`) SHALL be reverted on exit.

## Requirement 3: Reverting configuration after a failed context entry

**User story:** As a user whose `rc_context` block raises because of invalid
settings, I want the global configuration to be left in its original state, so
that a failed temporary change does not corrupt later work.

**Acceptance criteria**

1. IF applying the requested overrides inside a `rc_context` block raises an
   exception, THEN every non-`"backend"` `rcParams` entry SHALL be restored to
   the value it held before the block was entered.
2. WHEN a `rc_context` block terminates by exception, THEN the exception SHALL
   propagate to the caller after the restore step has run.

## Requirement 4: Keep the figure registry intact when querying the backend

**User story:** As a user who creates a figure inside a temporary configuration
block, I want the figure to remain registered and closable afterward, so that
querying the active backend does not silently drop my figures.

**Acceptance criteria**

1. WHEN `matplotlib.get_backend()` is called after a figure was created inside a
   `rc_context` block, THEN the set of figures registered in
   `matplotlib._pylab_helpers.Gcf` SHALL be unchanged by that call.
2. The system SHALL keep a figure created inside a `rc_context` block registered
   in `Gcf` so that it can subsequently be closed through the normal figure-close
   path.
3. WHEN `matplotlib.get_backend()` is called, THEN it SHALL return the name of
   the currently active rendering backend without removing any figures from the
   registry.

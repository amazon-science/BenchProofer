# Requirements: Preserve explicit range in `Axes.hist` when computing a density histogram

## Introduction

`matplotlib.axes.Axes.hist` (in `lib/matplotlib/axes/_axes.py`) computes each
dataset's histogram by delegating to `numpy.histogram`. Before calling
`numpy.histogram`, `hist` builds a keyword-argument mapping that accumulates the
options it wants to forward — notably the bin `range` (derived from the caller's
`range=` argument) and, for probability-density histograms, a `density` flag.

There is a bug: when the caller requests a density/normalized histogram
(`density=True`, or the deprecated `normed=True`) together with an explicit
`range=(lo, hi)`, the resulting bin edges ignore the requested range. Concretely,
`hist(data, "auto", range=(0, 1), density=True)` returns bin edges whose first
and last values are driven by the data extremes rather than being `0` and `1`.

The root cause is that the step which records the density option **replaces** the
whole keyword-argument mapping with a freshly constructed one holding only the
density option, discarding the `range` entry that had already been recorded. The
goal of this change is to make the density option additive: recording it must
leave any previously recorded `range` intact, so that an explicit `range=`
continues to govern the bin edges even for density histograms. This must be done
without disturbing the existing, already-correct behavior for non-density
histograms, stacked histograms, multi-dataset histograms, and the other options
`hist` already forwards.

## Requirement 1: Explicit range governs bin edges for density histograms

**User story:** As a user plotting a probability-density histogram, I want the
`range=(lo, hi)` I pass to `hist` to determine the outermost bin edges, so that
my histogram spans exactly the interval I asked for regardless of the data.

**Acceptance criteria**
1. WHEN `Axes.hist` is called for a single dataset with an explicit
   `range=(lo, hi)` and with `density=True`, THEN `Axes.hist` SHALL return bin
   edges whose first edge equals `lo` and whose last edge equals `hi`.
2. WHEN `Axes.hist` is called for a single dataset with an explicit
   `range=(lo, hi)` and with the deprecated `normed=True` (and `density` left
   unset), THEN `Axes.hist` SHALL return bin edges whose first edge equals `lo`
   and whose last edge equals `hi`.
3. WHEN `Axes.hist` is called with an explicit `range=(lo, hi)` and a string bin
   specification (e.g. an automatic bin-count rule) together with `density=True`,
   THEN the automatic bin-edge selection SHALL be performed over the interval
   `[lo, hi]` so that the outermost returned edges are `lo` and `hi`.
4. IF an explicit `range` has been recorded for forwarding to the underlying
   histogram computation, THEN recording the density option SHALL NOT remove,
   replace, or overwrite that recorded `range`.

## Requirement 2: The density option is still forwarded when requested

**User story:** As a user, I want `density=True` (or `normed=True`) to still
produce a normalized histogram, so that the fix for range handling does not
disable density normalization.

**Acceptance criteria**
1. WHEN `Axes.hist` is called with `density=True` (or the deprecated
   `normed=True`) for an unstacked histogram, THEN the histogram values SHALL be
   normalized so that the integral over the bins (the sum of value×bin-width) is
   1, exactly as before this change.
2. The system SHALL treat a truthy `density` or a truthy `normed` as a request
   for a density histogram (a density request is active when either is truthy).
3. WHEN a density histogram is requested for an unstacked histogram, THEN the
   density option SHALL be forwarded to the underlying per-dataset histogram
   computation.

## Requirement 3: Preserve existing behavior for non-density and stacked cases

**User story:** As a maintainer, I want the previously working code paths to keep
behaving identically, so that fixing the range/density interaction introduces no
regressions.

**Acceptance criteria**
1. WHEN `Axes.hist` is called with an explicit `range=(lo, hi)` and
   `density=False` (no density/normed request), THEN `Axes.hist` SHALL return
   bin edges whose first edge equals `lo` and whose last edge equals `hi`, as it
   did before this change.
2. WHILE a histogram is stacked (`stacked=True`) together with a density request,
   the density option SHALL NOT be forwarded to the per-dataset histogram
   computation; instead the stacked histograms SHALL be normalized together so
   that their combined area is 1, exactly as before this change.
3. WHEN multiple datasets are supplied, THEN all datasets SHALL share a common
   set of bin edges, and any explicit `range` SHALL continue to constrain those
   shared edges as it did before this change.
4. The system SHALL continue to forward every other histogram keyword option it
   previously forwarded (such as the resolved bin range for the single/empty
   dataset path) unchanged; the only behavioral change SHALL be that recording
   the density option no longer discards a previously recorded range.
5. WHEN `range` is not given and the density behavior does not apply, THEN
   `Axes.hist` SHALL continue to derive bin edges from the (non-NaN, finite) data
   extremes exactly as before this change.

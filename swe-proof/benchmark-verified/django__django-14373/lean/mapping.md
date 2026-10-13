# mapping.md — django__django-14373

## Symbol binding (file:line @ base_commit `b1a4b1f0bdf05adbd3dc4dde14228e68da54c1a3`)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_renderYear` | `DateFormat.Y` (the method that renders the 4-digit year) | `django/utils/dateformat.py:315-317` |
| `year : Nat` | `self.data.year` — the year of the date being formatted | `datetime.date.year`, read in `Y` |
| `result : String` | the string that the formatter appends for the `Y` specifier | produced by `str(getattr(self, 'Y')())` in `Formatter.format`, `django/utils/dateformat.py:40` |
| `padZeros 4 (toString year)` | `'%04d' % self.data.year` | the post-patch return value of `DateFormat.Y` |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX

| Python | Lean | notes |
|---|---|---|
| `self.data.year` (a non-negative `int`; `datetime` requires `1 ≤ year ≤ 9999`) | `year : Nat` | the date's year. The real domain is `1..9999`; the model accepts all of `Nat`, a superset that preserves the rendering semantics. |
| `'%04d' % year` (a Python `str`) | `padZeros 4 (toString year)` | base-ten numeral of `year`, left-padded with `'0'` to a minimum width of 4. For `year ≥ 1000` the value already has ≥4 digits and is returned unchanged. |
| the value the formatter appends for `Y` | `result : String` | `Formatter.format` does `str(getattr(self, piece)())`. Post-patch `Y()` already returns a `str`, so `str(...)` is the identity. |

### Bridging note (the observable the fix governs)
`Formatter.format` stringifies whatever each specifier method returns
(`str(getattr(self, piece)())`). Pre-patch `Y()` returns the bare `int`
`self.data.year`, which `str(...)` renders WITHOUT leading zeros (e.g. `str(1)`
== `'1'`, `str(999)` == `'999'`). Post-patch `Y()` returns `'%04d' %
self.data.year`, already a zero-padded width-4 string. The observable governed by
the fix is therefore the exact text appended for the `Y` specifier: the padded
decimal numeral. We model that text directly — `padZeros 4 (toString year)` —
and represent the formatter's `str(...)` wrapper as the identity, since the
post-patch method already yields a string.

`%04d` semantics: minimum field width 4, zero-flag pad on the left; values whose
numeral is already ≥4 digits are emitted in full with no truncation. `padZeros`
reproduces this exactly via natural subtraction (`width - s.length` clamps to 0).

## Callee provenance
No UNCHANGED outside callee is consumed. The year-rendering (decimal conversion +
leading-zero padding) is the operation the fix introduces, so it is modeled
deeply with concrete Lean operations (`toString`, `padZeros`), NOT axiomatized
(SPEC_GUIDE §3, §0.7). Hence: no `opaque`/`axiom` declarations, `axiom_check.py`
is a skip stub, G-AX skips.

## Flag dependencies
None. `Y()` renders unconditionally from `self.data.year`.

## G-CONF fuzz seed
Pinned seed: **14373** (also in `conformance_check.py`).

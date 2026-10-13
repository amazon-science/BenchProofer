# mapping.md — matplotlib__matplotlib-24026

## Instance
- repo: matplotlib/matplotlib
- base_commit: `14c96b510ebeba40f573e512299b1976f35b620e` (v3.6)
- changed file: `lib/matplotlib/stackplot.py`
- changed function: `stackplot(axes, x, *args, labels=(), colors=None, baseline='zero', **kwargs)`
  (def at `lib/matplotlib/stackplot.py:16` @ base_commit)

## Symbol binding

| Lean | Python | provenance (file:line @ base_commit) |
|---|---|---|
| `implementation_stackplotColors` / `problem_spec_stackplotColors` / `correct_stackplotColors` | the per-layer facecolor assignment inside `stackplot` when `colors` is supplied | `lib/matplotlib/stackplot.py:72-123` |
| `nthColor colors i` | `next(itertools.cycle(colors))` on the i-th pull | `lib/matplotlib/stackplot.py:74` (fix), `:113,:121` |
| `n` (layer count) | `len(y)` where `y = np.row_stack(args)` (number of stacked series) | `lib/matplotlib/stackplot.py:69`, loop `:119` |
| `colors : List String` | `colors` kwarg (a sequence of color specs), supplied & non-empty | param `:17` |
| result `Except String (List String)` | success ⇒ the facecolor list `[coll.facecolor for coll in r]`; error ⇒ the `ValueError` the pre-patch raised | `:112-123` |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX

- `colors : List String`  ↔  the Python `colors` list of color specs
  (named colors, `#rrggbb` hex, `CN` cycle-reference tokens, `(r,g,b)` tuples).
- `n : Nat`  ↔  `len(y)` = number of stacked series (≥ 1; `np.row_stack`
  always yields ≥ 1 row).
- Lean facecolor token `s : String` bridges to the real observed facecolor via
  matplotlib's color-spec resolver `matplotlib.colors.to_rgba(s)` (the I/O
  bridge applied to BOTH legs in G-CONF — it is NOT part of the modeled
  algorithm, it is the comparison normaliser).
- result `Except.ok fc`  ↔  `stackplot(...)` returns; layer i's
  `r[i].get_facecolor()[0] == to_rgba(colors[i % len(colors)])`.
- result `Except.error _`  ↔  `stackplot(...)` raises `ValueError`
  ("Cannot put cycle reference ... in prop_cycler") — the pre-patch behavior on
  any `CN` token.

## Callee provenance + flag deps

- `itertools.cycle(colors)` + `next(...)` — UNCHANGED stdlib behavior, modeled
  DEEPLY as `nthColor colors i = colors[i % colors.length]` (A-reference,
  validated == real by G-CONF). The i-th `next()` of `cycle(xs)` yields
  `xs[i % len(xs)]`.
- `axes._get_lines.get_next_color()` — used ONLY in the `colors is None` else
  branch (`lib/matplotlib/stackplot.py:75` fix). OUT OF MODEL SCOPE: the
  precondition `colors ≠ []` pins the `colors is not None` branch (the one the
  fix and the F2P test exercise). No opaque callee is declared.
- `axes.set_prop_cycle(color=colors)` → `validate_color_for_prop_cycle`
  (`lib/matplotlib/rcsetup.py:282`) rejects any token matching `^C[0-9]$`
  (`re.match`). This is the PRE-PATCH path the fix deletes; modeled in the
  prepatch impl as an inline `['C', d]`-with-digit rejection.
- Flag dep: behavior modeled is the `colors is not None` configuration.

## G-CONF fuzz seed
- pinned seed: `20240629` (see `conformance_check.py` `SEED`).

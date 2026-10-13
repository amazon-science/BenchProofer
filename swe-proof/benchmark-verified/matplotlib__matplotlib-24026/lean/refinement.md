# refinement.md — matplotlib__matplotlib-24026

Maps every op in `implementation_stackplotColors` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-CONF/G-AX), **I** (identical concrete op).

## Scope
The fix replaces, in `stackplot`, the pre-patch palette handling
(`axes.set_prop_cycle(color=colors)` + per-layer `get_next_color()`) with a
local `itertools.cycle(colors)` from which each region's facecolor is pulled by
`next(colors)`. Modeled behavior: the **`colors is not None` (non-empty palette)
configuration** — the one the F2P test
(`test_stackplot[...]` with `colors=["C0","C1","C2"]`) exercises. Precondition
`colors ≠ []` pins this branch; the `colors is None` else-branch
(`get_next_color()` generator) is out of model scope.

## Operation correspondence

| # | Lean op (`implementation_stackplotColors`) | patch.diff counterpart | tag |
|---|---|---|---|
| 1 | `result : Except String (List String)` carrier | `stackplot` returns a list of collections (success) vs the pre-patch `ValueError` | R — the returned collection list is refined to the list of its facecolor tokens; raising is `Except.error`. Bijection in mapping.md. |
| 2 | `n : Nat` = number of regions | `len(y)` regions: the first `fill_between` (`:112`) + `len(y)-1` loop iterations (`:119`) = `len(y)` total | R — `np.row_stack(args)` row count ↔ `n`. |
| 3 | `nthColor colors i = colors[i % colors.length]!` | `next(colors)` where `colors = itertools.cycle(palette)`; the i-th pull yields `palette[i % len(palette)]` | A-reference — `itertools.cycle`/`next` modeled deeply as modular indexing; validated == real by G-CONF. |
| 4 | `for i in [0:n] do r := r ++ [nthColor colors i]` | facecolor `next(colors)` assigned to region 0 (`facecolor=next(colors)`, `:113` fix) then region i for i in `range(len(y)-1)` (`:121` fix) — n pulls total, in order | I — one ordered `next` per region, accumulated into the result list `r`. |
| 5 | `return Except.ok r` | the fix never validates palette tokens, so a non-empty palette always succeeds | A-reference — absence of the rejecting validator is the observable; success on every palette token (incl. `CN`) validated by G-CONF. |

No changed op is left inexpressible. No op is axiomatized (the cycling is
modeled deeply, so `itertools.cycle` is an A-reference, not a consumed axiom).

## Prepatch (the bug)
`Solution_prepatch.lean` reintroduces the deleted validation: any palette token
matching a cycle-reference (`'C'` + single digit) makes the impl
`Except.error`, exactly the pre-patch `set_prop_cycle` → `validate_color_for_prop_cycle`
`ValueError` (`lib/matplotlib/rcsetup.py:282`, regex `^C[0-9]$`). This violates
the "always `Except.ok`" success carrier on any `CN` palette (e.g. the F2P
`["C0","C1","C2"]`), so `correct_stackplotColors` is unclosable there → G-DIFF.

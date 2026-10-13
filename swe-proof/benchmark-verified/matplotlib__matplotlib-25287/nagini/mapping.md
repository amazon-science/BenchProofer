# mapping.md — matplotlib__matplotlib-25287

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f8ffce6d44127d4ea7d6491262ab30046b03294b`, states the type
abstraction, and records the (none) callee provenance.

Repo file under change: `lib/matplotlib/axis.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `offset_color_primary(base_color, label_color)` | the colour-selection feeding `self.offsetText.set(..., color=...)` inside `XAxis._init` — `lib/matplotlib/axis.py:2237` (the `color=mpl.rcParams['xtick.color']` argument at `axis.py:2258`) | modeled changed behaviour, site 1: choosing the offset-text colour from `xtick.color` / `xtick.labelcolor` |
| `offset_color_secondary(base_color, label_color)` | the colour-selection feeding `self.offsetText.set(..., color=...)` inside `YAxis._init` — `lib/matplotlib/axis.py:2496` (the `color=mpl.rcParams['ytick.color']` argument at `axis.py:2518`) | modeled changed behaviour, site 2: choosing the offset-text colour from `ytick.color` / `ytick.labelcolor` |
| `effective_color(base_color, label_color)` | the conditional `tick_color = rcParams[...'.color'] if rcParams[...'.labelcolor']=='inherit' else rcParams[...'.labelcolor']` introduced by the patch at both sites | pure spec: the colour the offset text takes |
| `sentinel_inherit()` | the literal string `'inherit'` that `<axis>tick.labelcolor` defaults to and that means "fall back to `<axis>tick.color`" | pure spec: the sentinel colour value as a code-point sequence |

`base_color` ↔ `mpl.rcParams['xtick.color']` / `['ytick.color']`;
`label_color` ↔ `mpl.rcParams['xtick.labelcolor']` / `['ytick.labelcolor']`.

The pre-patch repo behaviour (for the refinement audit, not referenced from the
consumer spec view): both sites passed `color=mpl.rcParams['<axis>tick.color']`
unconditionally — the explicitly-configured label colour was never consulted.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an rcParam colour value, here a colour **name** `str` (e.g. `'blue'`, `'yellow'`, `'inherit'`) | `List[int]` of Unicode code points | `s[k]` ↔ `name[k] == ord(s[k])`; `len(s)` ↔ `len(name)`; equality of names ↔ equality of code-point lists; `'inherit'` ↔ `PSeq(105,110,104,101,114,105,116)` |
| a colour value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `==` mirrors `str` equality |
| `Text.set(color=v)` then `Text.get_color()` (`lib/matplotlib/text.py:985,808`) | identity on the colour value | `set_color` stores `v` verbatim in `self._color`; `get_color` returns `self._color` unchanged (it is not normalised/parsed). The F2P tests assert `offsetText.get_color() == '<name>'`, i.e. the stored value is exactly the selected colour. Modeled as: the function returns the chosen colour value. |
| the `if/else` on `labelcolor == 'inherit'` | `effective_color` / the impl `if ToSeq(label_color) == sentinel_inherit()` | identical control flow (kind I); only the carrier of the compared/returned colour values is refined (`str` → `List[int]`). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance

**None.** The changed operation is a two-way conditional selection between two
already-available colour values; it is expressed **directly** in the model
(`effective_color` + the impl `if`). There is no library/utility callee that the
changed code invokes and the model abstracts, so there are no `@ContractOnly`
axioms and no `axiom_check.py` (G-AX is vacuous for this instance). The only
adjacent callees — `dict.__getitem__` on `rcParams` (reads the configured
values, modeled as the inputs `base_color`/`label_color`) and
`Text.set`/`get_color` (identity passthrough of the colour value, §2) — carry no
behaviour the spec depends on beyond the value-identity refinements stated above.

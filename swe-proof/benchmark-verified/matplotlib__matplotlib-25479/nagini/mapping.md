# mapping.md — matplotlib__matplotlib-25479

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7fdf772201e4c9bafbc16dfac23b5472d6a53fa2`, states the type
abstraction, and gives the provenance of each deep-model reference (the real
operations the deep models are validated against by axiom_check.py / G-AX).

Repo files under change: `lib/matplotlib/colors.py` and `lib/matplotlib/cm.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `Cmap` (class) | `matplotlib.colors.Colormap` — `lib/matplotlib/colors.py:663` | the colormap object; modelled with only the three touched attributes |
| `Cmap.name` | `Colormap.name` (`colors.py:684`, set in `__init__`) | the colormap's label |
| `Cmap.colorbar_extend` | `Colormap.colorbar_extend` (`colors.py:697`) | the colorbar-extension flag |
| `Cmap.lut` | `Colormap._lut` (`colors.py`, built by `_init`; compared via `np.array_equal`) | the lookup-table contents |
| `colormaps_equal(self, other)` | `Colormap.__eq__(self, other)` — `lib/matplotlib/colors.py:776` | the modeled changed function (equality) |
| `register_named(reg, name, cmap)` | `ColormapRegistry.register(self, cmap, *, name, force)` — `lib/matplotlib/cm.py:103` (changed body at 148+) | the modeled changed function (registration) |
| `reg` (`Dict[int, Cmap]`) | `ColormapRegistry._cmaps` — `lib/matplotlib/cm.py:72`, a `dict` from name to `Colormap` | the by-label registry store |
| `entry_eq(x, y)` *(deep model — A-reference)* | the elementwise scalar comparison `==` inside `np.array_equal` (`colors.py:785`), on `float64` rows | pure spec: equality of two lookup-table entries, non-reflexive on an indeterminate (NaN-carrying) entry |
| `seq_eq(a, b)` *(deep model — A-reference)* | the elementwise lookup-table comparison `np.array_equal(self._lut, other._lut)` (`colors.py:785`) | pure spec: entrywise (over `entry_eq`) content equality of two lookup tables |

The two gold hunks, for the refinement audit:

* `colors.py` `Colormap.__eq__` (line 776–779): the guard
  `... or self.name != other.name or self.colorbar_extend != other.colorbar_extend`
  loses its `self.name != other.name` disjunct, so equality no longer depends on
  the label.
* `cm.py` `ColormapRegistry.register` (after line 148, `self._cmaps[name] = cmap.copy()`):
  three new lines set the stored copy's `.name` to the registration `name` when
  they differ (`if self._cmaps[name].name != name: self._cmaps[name].name = name`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection / justification |
|---|---|---|
| `Colormap.name` : `str` | `int` token | The tested behaviour observes label EQUALITY / INEQUALITY only (`__eq__`'s dropped `name`-disjunct; `register`'s `name != name` check; the F2P `cmap_returned.name == "wrong-cmap"`). Distinct strings ↔ distinct ints is a faithful bijection on the observed relation; label spelling is never inspected. |
| `Colormap.colorbar_extend` : `False` or one of the extend strings `'neither'`/`'min'`/`'max'`/`'both'` (and `True`, which the F2P's `not` toggle produces) | `int` token | `__eq__` compares it with `!=` only — the value's spelling is never inspected — so an injective token map is the faithful carrier. It must be injective on the WHOLE domain: with equal luts the real `__eq__` separates all 6 values pairwise (verified in-container), so a 2-valued `bool` carrier would identify values the callee distinguishes. The token map used by the G-CONF bridge is `0->False, 1->True, 2->'neither', 3->'min', 4->'max', 5->'both'`; token `0` is the constructor default. Reachable publicly: `colorbar_extend` is a documented attribute (`colors.py:693-697`) and `from_levels_and_colors` assigns an extend string to it (`colors.py:2706`). |
| `Colormap._lut` : `numpy.ndarray` of `float64`, compared by `np.array_equal` | `List[int]`, one token per row, compared entrywise by `entry_eq` and threaded by `seq_eq` over `PSeq[int]` | `__eq__` decides lut equality by `np.array_equal(self._lut, other._lut)` = same shape AND `(a1 == a2).all()` elementwise, with `equal_nan` left at its default `False`. Flat length determines shape here (row width is fixed at 4), so token-list length carries shape. The elementwise `==` is NOT reflexive on a `float64` table: a row holding a NaN channel compares unequal to every row, itself included, so a table carrying one is `==`-equal to NO table (verified in-container: `c.set_bad((nan,)*4); c._init(); (c == c) is False`). The carrier therefore splits the token domain: a NON-NEGATIVE token is a determinate row (equal iff the tokens are equal), a NEGATIVE token is a row carrying a NaN channel, which `entry_eq` reports unequal to everything. `meta.json float_encoding` stays null: the tokens are not a float encoding, they are row identities under the compared relation. NaN rows are reachable publicly via `set_bad`/`set_over`/`set_under`, whose `to_rgba` accepts a NaN channel. |
| `cmap.copy()` (`colors.py:950` → `__copy__` at 768) | the `Cmap(...)` constructor producing a fresh object with copied content | `copy()` returns a new `Colormap` with `__dict__` copied and `_lut` deep-copied; modelled as a fresh `Cmap` whose `lut` is a fresh `List[int]` with the same contents and whose `name`/`colorbar_extend` are copied. Validated as an A-reference by axiom_check.py. |
| `ColormapRegistry._cmaps` : `dict[str, Colormap]` | `Dict[int, Cmap]` | the registry store; subscription guarded by membership test (`name in reg`). |

`str` indexing/iteration is banned in Nagini; here labels are never indexed —
only compared — so the `int`-token carrier needs no `List[int]` spelling.

## 3. Deep-model references (kind-A-reference — checked by G-AX / axiom_check.py)

No `@ContractOnly` axiom is consumed. The two operations under change are
modelled DEEPLY; axiom_check.py validates each deep model against the REAL
matplotlib callee, in-container, on boundary + fuzz inputs.

### 3.1 `colormaps_equal` / `seq_eq` ↔ `Colormap.__eq__` (A-reference 1)
**Callee:** `matplotlib.colors.Colormap.__eq__` (post-patch). Source
(`colors.py:776`, after the gold hunk):

```python
def __eq__(self, other):
    if (not isinstance(other, Colormap) or
            self.colorbar_extend != other.colorbar_extend):
        return False
    if not self._isinit:
        self._init()
    if not other._isinit:
        other._init()
    return np.array_equal(self._lut, other._lut)
```

So equality is: `other` is a Colormap AND equal `colorbar_extend` AND equal
lookup tables — the label is NOT consulted. The model's postcondition
`Result() == (colorbar_extend-equal AND seq_eq(lut, lut))` is exactly this, with
`seq_eq` threading `entry_eq` so that the elementwise comparison's behaviour on an
indeterminate entry is carried too.
G-AX asserts the real `__eq__` agrees with the model predicate over: equal
copies; relabelled copies (equal); flipped extension flag (unequal); each pair of
DISTINCT extension-flag values from the whole documented domain over identical
luts (unequal — this is what forces an injective flag carrier); a table carrying
a NaN channel compared with itself and with a copy (unequal — the elementwise
`==` is not reflexive there); mutated lut via `set_bad` (unequal); truncated lut
(unequal); non-Colormap comparand (unequal); plus randomized fuzz pairs over
labels, extension flags drawn from the FULL domain, and small lookup tables with
and without NaN channels.

### 3.2 `register_named` ↔ `ColormapRegistry.register` (A-reference 2)
**Callee:** `matplotlib.cm.ColormapRegistry.register` (post-patch). Source
(`cm.py:148`, after the gold hunk):

```python
self._cmaps[name] = cmap.copy()
if self._cmaps[name].name != name:
    self._cmaps[name].name = name
```

So after registration the store holds an independent copy under `name` whose own
`.name` equals `name` (regardless of `cmap.name`), and the supplied `cmap` is
untouched. The model's postconditions
(`name in reg`, `reg[name] is not cmap`, `reg[name].name == name`,
`reg[name].colorbar_extend == cmap.colorbar_extend`,
`ToSeq(reg[name].lut) == ToSeq(cmap.lut)`, `cmap` unchanged) encode exactly
this. G-AX asserts it against the real `matplotlib.colormaps.register` +
`plt.get_cmap`, both for the issue's exact scenario
(`viridis.with_extremes(over='r')`, `name="test-cmap"`, registered as
`"wrong-cmap"`, then `get_cmap("wrong-cmap").name == "wrong-cmap"` and
`== cmap`) and 300 randomized (supplied-label, registration-label) pairs.

**Flag dependency:** `register`'s `name` keyword defaults to `cmap.name`; the
behaviour modelled here is for an explicit `name` differing from `cmap.name`
(the issue scenario). axiom_check.py exercises this explicit-name path, which is
the one the F2P test and the model cover.

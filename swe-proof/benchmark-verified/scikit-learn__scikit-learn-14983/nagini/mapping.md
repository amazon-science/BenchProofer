# mapping.md — scikit-learn__scikit-learn-14983

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 06632c0d185128a53c57ccc73b25b6408e90bb89`, states the type
abstraction, and gives the provenance of the deep-model reference (there are no
consumed `@ContractOnly` axioms).

Repo file under change: `sklearn/model_selection/_split.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reported_param_value(attr, none, has_store, store, key)` | the per-parameter value-resolution body of `_build_repr(self)` — `sklearn/model_selection/_split.py:2161-2166` (the `value = getattr(self, key, None)` block inside the `for key in args:` loop) | the modeled changed function: how one reported parameter value is resolved |
| `resolved_value(attr, none, has_store, store, key)` *(deep model — A-reference)* | the same resolution as a pure function of the object's attribute store + the secondary keyword store; validated `== real _build_repr resolution` by axiom_check.py (G-AX) | pure spec: the value resolved for one parameter |
| `store` (`Dict[int,int]`) | `self.cvargs` — the `**cvargs` captured in `_RepeatedSplits.__init__` (`_split.py:1090,1104`); for `RepeatedKFold` it holds `{'n_splits': n_splits}` (`_split.py:1216-1218`), for `RepeatedStratifiedKFold` likewise (`_split.py:1296-1298`) | the secondary keyword-argument store |
| `has_store` (`bool`) | `hasattr(self, 'cvargs')` (`_split.py:2164`, gold) | whether the object carries the secondary store |
| `attr` (`int`, `none`-sentinel for absent) | `getattr(self, key, None)` (`_split.py:2162`) | the object's own direct attribute for the parameter |
| `key` (`int`) | one element of `args` (sorted constructor parameter names) (`_split.py:2150-2151`) | the parameter name being reported |

The two gold hunks this models:

1. **`_RepeatedSplits.__repr__`** added (`_split.py:1166`, gold):
   `def __repr__(self): return _build_repr(self)`. This makes `repr()` of
   `RepeatedKFold` / `RepeatedStratifiedKFold` (subclasses of `_RepeatedSplits`)
   route through `_build_repr` instead of `object.__repr__`. Modeled as: the
   reported representation IS the per-parameter resolution (the function under
   spec); see refinement.md §A.
2. **`_build_repr` cvargs fallback** added (`_split.py:2163-2164`, gold):
   `if value is None and hasattr(self, 'cvargs'): value = self.cvargs.get(key, None)`.
   This is the discriminating change — modeled directly by `reported_param_value`'s
   impl and `resolved_value`; see refinement.md §B.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| parameter NAME (`str`, e.g. `'n_splits'`) | `int` key | each name ↔ a distinct `int`; the resolution logic is name-agnostic, so the renaming is an exact bijection. (Nagini bans `str` indexing; the resolution never inspects the characters of a name.) |
| parameter VALUE (`int`, e.g. `n_splits=2`, `n_repeats=6`) | `int` | identity. The F2P values are small ints; `random_state=None` is the absent case below. |
| Python `None` (absent / unset value) | the `int` sentinel `none` | `getattr(self, key, None) is None` ↔ `attr == none`; `cvargs.get(key, None) is None` ↔ key not present (or stored-None) ↔ resolves to `none`. The sentinel keeps the resolver total and `int`-typed (an `Optional[int]` return from a `@Pure` helper used inside an `Ensures` trips a translator defect in this Nagini build). |
| `self.cvargs` (`dict`, name→value) | `store: Dict[int,int]` | `name in self.cvargs` ↔ `key in store`; `self.cvargs[name]` ↔ `store[key]`. cvargs holds only concrete (non-None) configured values, encoded by the precondition `Implies(key in store, store[key] != none)`. |
| `hasattr(self, 'cvargs')` | `has_store: bool` | identity (true for `_RepeatedSplits` subclasses; false for plain estimators / the `test_build_repr` MockSplitter). |
| `getattr(self, key, None)` (attribute lookup with default) | the `attr` argument | the lookup result, with `None` encoded as `none`. |

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `resolved_value` deep model ↔ real `_build_repr` per-key resolution

**Reference (the changed operation, modeled DEEPLY — there is NO consumed
axiom):** the patched per-key body of `_build_repr`
(`sklearn/model_selection/_split.py:2161-2166`, gold):

```python
value = getattr(self, key, None)
if value is None and hasattr(self, 'cvargs'):
    value = self.cvargs.get(key, None)
```

The `@Pure resolved_value` (model.py `pure` region) is the spelled-out form of
this resolution under the §2 bijection:

* `attr != none`            → `attr`        (a present direct attribute wins);
* `has_store and key in store` → `store[key]` (else the secondary store value);
* otherwise                 → `none`        (absent everywhere).

This is precisely the gold body: `getattr` yields the attribute (or `None`);
when that is `None` and `self` carries `cvargs`, `cvargs.get(key, None)` yields
the store value (or `None`). The legacy buggy form omitted the second clause,
so a parameter held only in `cvargs` (e.g. `n_splits`, which
`_RepeatedSplits.__init__` stows in `**cvargs`, not as a direct attribute —
`_split.py:1090,1104`) resolved to `None`; that is the exact bug in the issue.

**Soundness check (G-AX):** `axiom_check.py` (a) transcribes the real gold
resolution (`real_resolution`) and asserts it equals `resolved_value` on 8
boundary objects + ~20000 randomized fuzz objects — including objects WITHOUT a
`cvargs` store (the `test_build_repr` / MockSplitter PASS_TO_PASS case, where a
`None` attribute must stay `None`); and (b), in-container where sklearn is
built, constructs the real `RepeatedKFold` / `RepeatedStratifiedKFold`, asserts
`repr(obj)` equals the FAIL_TO_PASS string
`"<cls>(n_repeats=6, n_splits=2, random_state=None)"`, and asserts the real
`_build_repr` resolution agrees with the deep model on `n_splits` /
`n_repeats` / `random_state`. Imports are stdlib-only; the sklearn import is
guarded. Exit 0 iff every observation agrees.

No flag dependency: the resolution is plain attribute/dict access, independent
of any global configuration.

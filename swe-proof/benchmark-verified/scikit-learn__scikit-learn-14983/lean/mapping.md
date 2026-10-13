# mapping.md — scikit-learn__scikit-learn-14983

## Symbol binding (file:line @ base_commit 06632c0d185128a53c57ccc73b25b6408e90bb89)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_reprString` / `problem_spec_reprString` | `_build_repr(self)` (the constructor-style summary builder) | `sklearn/model_selection/_split.py:2138-2168` |
| `reprString` (pure helper) | the body of `_build_repr` (the per-key value resolution + the final `'%s(%s)'` assembly) | `_split.py:2150-2168` |
| `renderParam` (pure helper) | the per-`key` loop body of `_build_repr` plus the `%s=%s` rendering done in `_pprint` | `_split.py:2151-2166` + `sklearn/base.py:82-129` (`_pprint`) |
| `pyRepr` (pure helper) | the `printer=repr` value formatting used by `_pprint` (int → decimal, `None` → `None`, str → `'...'`) | `base.py:82-129` |
| `lookupVal` (pure helper) | `getattr(self, key, None)` (against attribute dict) and `self.cvargs.get(key, None)` (against the auxiliary map) | `_split.py:2159` + patch line |

## What the function does (base_commit) and the change

`_build_repr(self)` produces an estimator's `repr()` text in the form
`ClassName(p1=v1, p2=v2, ...)`. It collects the constructor parameter names
(`args`, sorted, excluding `self` / `**kwargs`), then for each `key`:

```python
value = getattr(self, key, None)            # base_commit
...
params[key] = value
return '%s(%s)' % (class_name, _pprint(params, offset=len(class_name)))
```

`_pprint` formats each entry as `key=printer(value)` with `printer=repr`
(so an int renders as its decimal form, `None` as `None`, a str as `'...'`),
joins them with `, `, and (for the short reprs in scope here) keeps them on one
line.

The objects under the issue (`RepeatedKFold`, `RepeatedStratifiedKFold`, both
subclasses of `_RepeatedSplits`) keep some constructor parameters NOT as direct
attributes but inside a `self.cvargs` dict (e.g. `n_splits` is passed through to
`cvargs`, while `n_repeats` / `random_state` are direct attributes). So
`getattr(self, 'n_splits', None)` is `None`, and base_commit renders
`n_splits=None`.

The **fix** has two coupled edits:

1. `_RepeatedSplits.__repr__` is added (`return _build_repr(self)`) so that
   `repr()` on these objects is routed to `_build_repr` at all (without it the
   default `object.__repr__` — the `<... object at 0x...>` form — is used). This
   is *plumbing*: it selects the builder, it does not change what the builder
   computes.
2. `_build_repr`'s value resolution gains a fallback to the auxiliary map:

   ```python
   value = getattr(self, key, None)
   if value is None and hasattr(self, 'cvargs'):
       value = self.cvargs.get(key, None)
   ```

   so a parameter held only in `cvargs` (e.g. `n_splits`) renders with its real
   value (`n_splits=2`) instead of `None`.

The **bug** the F2P test pins is edit (2): `repr(RepeatedKFold(n_splits=2,
n_repeats=6))` must be `RepeatedKFold(n_repeats=6, n_splits=2,
random_state=None)`, but base_commit (even with `__repr__` routed) yields
`RepeatedKFold(n_repeats=6, n_splits=None, random_state=None)`.

## Lean modeling

The modeled function is the constructor-style summary BUILDER `_build_repr`
together with `_pprint`'s per-entry formatting (the observable the F2P test
asserts on is the final repr STRING). Inputs are the observables the builder
reads:

- `className : String` = `self.__class__.__name__`.
- `argNames : List String` = the sorted constructor parameter names (`args`).
  The sort and the `self`/`**kwargs` exclusion are performed by the unchanged
  signature-introspection prologue; their RESULT (the ordered name list) is the
  input, exactly as the real loop consumes it.
- `attrs : List (String × PyVal)` = the object's direct attributes, modeled as an
  association list; `lookupVal attrs key` = `getattr(self, key, None)` (absence ⇒
  `PyVal.null`, i.e. the `None` default).
- `extra : List (String × PyVal)` = the auxiliary map `self.cvargs`;
  `lookupVal extra key` = `self.cvargs.get(key, None)`.
- `hasExtra : Bool` = `hasattr(self, 'cvargs')`.

`renderParam` resolves one parameter's value: direct attribute first, and — when
that is the null sentinel and the auxiliary map is present — the auxiliary map's
entry; then renders `key=pyRepr value`. `reprString` joins the rendered
parameters with `", "` inside `className ++ "(" ++ … ++ ")"`.

`pyVal` models the three value shapes the F2P / PASS-TO-PASS reprs exercise:
integers (`n_splits`, `n_repeats`), the null sentinel (`random_state=None`), and
text values (general estimator string params). `pyRepr` mirrors `repr()` on each:
`repr(2) == '2'`, `repr(None) == 'None'`, `repr('x') == "'x'"`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.__class__.__name__` | `className : String` | identity |
| sorted ctor param names | `argNames : List String` | identity (order preserved) |
| object attribute dict | `attrs : List (String × PyVal)` | key → value assoc; absent key ↔ no entry |
| `self.cvargs` | `extra : List (String × PyVal)` | key → value assoc |
| `hasattr(self, 'cvargs')` | `hasExtra : Bool` | identity |
| `getattr(self, key, None)` | `lookupVal attrs key` | found ↔ entry value; absent ↔ `PyVal.null` |
| `self.cvargs.get(key, None)` | `lookupVal extra key` | found ↔ entry value; absent ↔ `PyVal.null` |
| `repr(int)` | `pyRepr (.int n)` | decimal string |
| `None` / `repr(None)` | `PyVal.null` / `pyRepr .null = "None"` | the null sentinel |
| `repr(str)` | `pyRepr (.str s)` | `'s'` (single-quoted) |
| `'%s=%s' % (k, repr(v))` | `key ++ "=" ++ pyRepr v` | identity |
| `_pprint` join (short reprs) | `String.intercalate ", "` | one-line `, `-join (no wrapping for the in-scope reprs) |
| `'%s(%s)' % (class_name, body)` | `className ++ "(" ++ body ++ ")"` | identity |

### Modeling fidelity notes (what is in scope)

- `_pprint` has multi-line wrapping logic (`this_line_length >= 75`, the `500`-char
  truncation, the `float`-uses-`str` special-case). For the estimator reprs in
  scope (a handful of short scalar params: ints, `None`, short strings) NONE of
  these branches fire — the output is the simple one-line `, `-join. G-CONF fuzzes
  only inputs in this regime (short scalar values, few params) so the modeled
  `String.intercalate ", "` is exact over the tested domain. (The `float`→`str`
  case is excluded by modeling values as int/null/str — the F2P estimators carry
  no float params.)
- The signature-introspection prologue (collect → sort → drop `self`/`**kwargs`)
  is unchanged by the patch; its output (the ordered `argNames`) is taken as the
  input, so the model does not re-derive it.
- The `DeprecationWarning` skip (`if len(w) and w[0].category == DeprecationWarning:
  continue`) is unchanged and never fires for the in-scope params (none are
  deprecated), so it is not modeled.

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The behavior the patch changes —
  the per-parameter value resolution (direct attribute, then the auxiliary map)
  and its Python-style rendering — is modeled DEEPLY as pure functions
  (`renderParam`, `lookupVal`, `pyRepr`, `reprString`). SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed op, so the `axioms` region is empty and
  **G-AX skips**.
- The `__repr__` routing edit (edit 1) is *plumbing*: it makes `repr()` call this
  builder at all. It changes WHICH renderer runs, not WHAT the renderer computes,
  and is not separately expressible in the builder model (the un-routed case is
  the opaque `object.__repr__` address string). The single modeled behavioral fix
  is edit (2), captured by the one `Solution_prepatch.lean`.

## G-CONF fuzz seed

Pinned LCG seed: **14983** (see `conformance_check.py` `SEED`). Corpus: randomized
estimator-like inputs — varying the class name, the sorted param-name list, which
params are direct attributes vs held only in the auxiliary map, presence/absence
of the auxiliary map (`hasExtra`), and value shapes (int / null / short str) — over
≥1e5 fuzzed inputs. The R/I shadow of `implementation_reprString` is diffed
byte-for-byte against an in-process replica of the POST-PATCH resolution
(`getattr`-then-`cvargs.get` + `repr` rendering + `, `-join). Hand-picked edge
cases pin the F2P scenario: `RepeatedKFold` with `n_repeats` direct = 6,
`n_splits` only-in-cvargs = 2, `random_state` = None →
`RepeatedKFold(n_repeats=6, n_splits=2, random_state=None)`.

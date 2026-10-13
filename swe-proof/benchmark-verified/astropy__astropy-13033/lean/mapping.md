# mapping.md — astropy__astropy-13033

## Symbol binding (file:line @ base_commit 298ccb478e6bf092953bca67a3d29dc6c35f6752)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_checkRequiredColumns` / `problem_spec_checkRequiredColumns` | `BaseTimeSeries._check_required_columns` | `astropy/timeseries/core.py:57-85` |
| `checkRequiredColumns` (pure helper) | the body of `_check_required_columns` (no-op decisions + the mismatch `raise` + the relaxed toggle) | `core.py:59-85` |
| `renderNames` (pure helper) | the nested `as_scalar_or_list_str(obj)` introduced by the patch | `core.py:58-64 (post-patch)` |
| `pyStrRepr` (pure helper) | Python `f"'{obj}'"` / `f"'{obj[0]}'"` rendering of a single value (verbatim interpolation, no escaping) | post-patch helper |
| `pyReprStr` (**opaque**, axioms region) | Python `repr` of a `str` — the per-element rendering `str(list)` applies (quote choice + escaping rules) | platform builtin (UNCHANGED); binding validated by G-AX (A-reference) |
| `pyListRepr` (pure helper) | Python `str(obj)` of a `list[str]` (`['a', 'b']`; each element via `repr`) | post-patch helper |

## What the function does (base_commit)

`_check_required_columns` re-validates the table after a column-related method:

```python
def _check_required_columns(self):
    if not self._required_columns_enabled:
        return
    if self._required_columns is not None:
        if self._required_columns_relax:
            required_columns = self._required_columns[:len(self.colnames)]
        else:
            required_columns = self._required_columns
        plural = 's' if len(required_columns) > 1 else ''
        if not self._required_columns_relax and len(self.colnames) == 0:
            raise ValueError("{} object is invalid - expected '{}' "
                             "as the first column{} but time series has no columns"
                             .format(self.__class__.__name__, required_columns[0], plural))
        elif self.colnames[:len(required_columns)] != required_columns:
            raise ValueError("{} object is invalid - expected '{}' "
                             "as the first column{} but found '{}'"
                             .format(self.__class__.__name__, required_columns[0], plural, self.colnames[0]))
        if (self._required_columns_relax
                and self._required_columns == self.colnames[:len(self._required_columns)]):
            self._required_columns_relax = False
```

The **bug**: the mismatch message hard-codes `required_columns[0]` and
`self.colnames[0]` — only the FIRST expected name and the FIRST present name —
even when several columns are required. So removing column `a` from a table
requiring `['time', 'a']` (leaving `['time', 'b']`) produces
`expected 'time' ... but found 'time'`, which is misleading (both heads are
`'time'`).

The **fix** introduces `as_scalar_or_list_str(obj)` and renders BOTH sides with
it, and the found side now uses `self.colnames[:len(required_columns)]` (the
present leading columns truncated to the required length) instead of
`self.colnames[0]`. `as_scalar_or_list_str` shows a single-element collection as
the one quoted name (`'time'`) and a multi-element collection as the whole list
(`['time', 'a']`). A non-`__len__` scalar is shown quoted via `str` (this branch
is only reachable for a degenerate `required_columns` scalar — both call sites in
the changed function pass lists, so the modeled inputs are always list-shaped).

## Lean modeling

- The method mutates `self._required_columns_relax` and otherwise either returns
  (no error) or `raise`s a `ValueError`. Modeled as
  `Except String Bool`: `.error msg` for the raise (the message string is the
  observable the F2P test asserts on), `.ok newRelax` for the no-error path
  carrying the (possibly toggled) relax flag.
- Inputs map to the observables the method reads:
  `requiredColumnsEnabled` = `self._required_columns_enabled`;
  `requiredColumns : Option (List String)` = `self._required_columns`
  (`none` ↔ `None`, `some xs` ↔ a list of names);
  `requiredColumnsRelax` = `self._required_columns_relax`;
  `colnames : List String` = `self.colnames`;
  `className` = `self.__class__.__name__`.
- `required` = `self._required_columns[:len(colnames)]` when relaxed else
  `self._required_columns`, modeled as `reqCols.take colnames.length` / `reqCols`.
- `plural` = `"s"` iff `required.length > 1`.
- The empty-columns branch (`not relax and len(colnames)==0`) keeps its original
  single-head wording (`required[0]`, modeled `required.headD ""`) — the patch
  does NOT touch it.
- The mismatch branch (`colnames[:len(required)] != required`) is the changed
  one: `renderNames required` for the expected side and
  `renderNames (colnames.take required.length)` for the found side.
- The trailing relaxed toggle: when relaxed and `self._required_columns ==
  self.colnames[:len(self._required_columns)]`, relax flips to `False`; modeled as
  the `.ok` payload.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.__class__.__name__` | `className : String` | identity |
| `self._required_columns_enabled` | `requiredColumnsEnabled : Bool` | identity |
| `self._required_columns` | `requiredColumns : Option (List String)` | `None ↔ none`; list of names ↔ `some` |
| `self._required_columns_relax` | `requiredColumnsRelax : Bool` | identity |
| `self.colnames` | `colnames : List String` | identity (ordered names) |
| `len(xs)` | `xs.length` | identity |
| `xs[:n]` | `xs.take n` | identity (Python slice clamps; `List.take` clamps) |
| `xs[0]` (head, lists nonempty here) | `xs.headD ""` | head of a nonempty list |
| `raise ValueError(msg)` | `Except.error msg` | the message string is the observable |
| no raise; relax possibly toggled | `Except.ok newRelax` | `newRelax` = post-call `_required_columns_relax` |
| `f"'{x}'"` | `pyStrRepr x` | `'x'` (verbatim interpolation — Python f-strings do NOT escape) |
| `repr(x)` for `x: str` | `pyReprStr x` (opaque) | quote choice + escaping per the platform; binding validated by G-AX |
| `str(list_of_str)` | `pyListRepr xs` | `['a', 'b']` (`repr` of each element = `pyReprStr`, comma+space, brackets) |
| `as_scalar_or_list_str(xs)` | `renderNames xs` | 1-elt → quoted scalar (`f"'{obj[0]}'"`, verbatim); else → list repr |

Note on `as_scalar_or_list_str`'s `not hasattr(obj, "__len__")` (scalar) branch:
in the changed function both arguments are always Python lists
(`required_columns` is a list/slice; `self.colnames[:n]` is a list), so the
scalar branch is unreachable for the modeled inputs. The Lean model therefore
covers the two list-shaped branches (`len == 1` and `len != 1`); the empty list
renders as `[]` (matching `str([])`).

## Callee provenance + flag dependencies

- **No consumed callee axiom; ONE A-reference.** The message construction and
  the single-vs-list rendering are the behavior the patch changes; SPEC_GUIDE §3
  forbids axiomatizing a deeply-modeled changed op, so they are modeled DEEPLY as
  pure string functions (`renderNames`, `pyStrRepr`, `pyListRepr`). ONE
  building block inside that rendering is an UNCHANGED platform builtin: the
  per-element rendering `str(list)` applies (Python `repr` of a `str`, with its
  quote choice and escaping rules). It is declared `opaque pyReprStr` in the
  axioms region — an A-reference, NOT an axiomatized changed op: the patch never
  touches `repr`, and committing to a concrete Lean approximation of the CPython
  escaping tables would be unfaithful on names containing quotes, backslashes,
  or control characters. `axiom_check.py` (G-AX) validates the binding
  executably: the composition `"[" ++ ", ".join(pyReprStr x) ++ "]"` with
  `pyReprStr := repr` equals the REAL `str(list)` byte-for-byte over adversarial
  and fuzzed name lists, and `repr` round-trips each name. No `axiom` is
  consumed — the proof never inspects `pyReprStr`'s behavior.
- `self.colnames` is a property of `QTable` (unchanged); its value is an input.
- The `_required_columns_relax` toggle and the no-columns branch are unchanged by
  the patch but modeled inline because they share the function's control flow.

## G-CONF fuzz seed

Pinned LCG seed: **13033** (see `conformance_check.py` `SEED`). Corpus:
randomized inputs crossing every branch — disabled check, `None` required
columns, relaxed vs strict, empty `colnames`, matching vs mismatching leading
columns, and required-column lists of length 1 vs ≥2 (the discriminating
category) — over ≥1e5 fuzzed inputs. The name pool includes adversarial names
(embedded single/double quotes, backslashes, control characters, non-ASCII),
pinning the `str(list)`-vs-naive-quoting divergence class; the shadow
interprets the opaque `pyReprStr` as the real `repr` (its G-AX-validated
binding). The R/I shadow of
`implementation_checkRequiredColumns` is diffed against an in-process replica of
the POST-PATCH `_check_required_columns` (message strings compared byte-for-byte).
Hand-picked edge cases pin the F2P scenario: required `['time','a']`, present
`['time','b']` → `expected ['time', 'a'] ... columns but found ['time', 'b']`;
and the preserved single-column message `expected 'time' ... column but found
'banana'`.

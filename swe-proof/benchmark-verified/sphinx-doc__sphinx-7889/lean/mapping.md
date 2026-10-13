# mapping.md — sphinx-doc__sphinx-7889

## Symbol binding (file:line @ base_commit ec9af606c6cfa515f946d74da9b51574f2f9b16f)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_mockSubscript` / `problem_spec_mockSubscript` | `_MockObject.__getitem__` | `sphinx/ext/autodoc/mock.py:55-56` |
| `concatName` (pure helper) | display-name construction inside `_make_subclass`: `'__display_name__': module + '.' + name` | `sphinx/ext/autodoc/mock.py:71-76` (line 73) |
| `strChars` (pure helper) | `str(key)` — the textual rendering applied to the subscript key (the post-patch `str(...)` call) | `sphinx/ext/autodoc/mock.py:56` (post-patch) |
| `PyKey` (key carrier) | the `key` argument of `__getitem__` (`str` or any other object, e.g. a `TypeVar`) | `sphinx/ext/autodoc/mock.py:55` |

The modeled fragment is `_MockObject.__getitem__`. Subscripting a mock object
(`obj[key]`) constructs a fresh subclass whose `__display_name__` is
`module + '.' + name`, where `name` is derived from the subscript key. This is
the only behavior the gold patch changes and the only behavior the FAIL_TO_PASS
test (`tests/test_ext_autodoc_mock.py::test_MockObject`, the parametrized-type
case) observes.

### What the modeled fragment does

base_commit (`sphinx/ext/autodoc/mock.py:55-56`):
```python
def __getitem__(self, key: str) -> "_MockObject":
    return _make_subclass(key, self.__display_name__, self.__class__)()
```
`_make_subclass(name, module, ...)` (`mock.py:71-76`) builds
```python
attrs = {'__module__': module, '__display_name__': module + '.' + name}
return type(name, (superclass,), attrs)
```
The key `key` is passed straight through as `name`. The display-name expression
`module + '.' + name` is a `str + str + name` concatenation: it requires `name`
to be a `str`. When `obj` is subscripted with a non-`str` key — e.g. a `TypeVar`
when indexing a generic, `obj[T]` — the concatenation `module + '.' + T` raises
`TypeError: can only concatenate str (not "typing.TypeVar") to str`.

post-patch (gold):
```python
def __getitem__(self, key: Any) -> "_MockObject":
    return _make_subclass(str(key), self.__display_name__, self.__class__)()
```
The key is rendered to text with `str(key)` BEFORE being handed to
`_make_subclass`, so the display-name concatenation always receives a `str` and
never raises. `str(some_str) is/== that_str` (idempotent on text), and
`str(TypeVar('T')) == '~T'`, so a generic index now produces a derived subclass
with display name `module + '.' + '~T'` instead of raising.

(The `type(name, ...)` call also receives `name`; CPython's `type()` accepts a
non-`str` class name without raising at construction in this path, so the
TypeError observed by the issue originates specifically at the `module + '.' +
name` display-name concatenation. We model the display-name construction, which
is the operation that fails.)

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean | bijection |
|---|---|---|
| subscript key `key` (any object) | `key : PyKey` | `PyKey.str s` ↔ a key that is already a `str` with code points `s`; `PyKey.other r` ↔ a non-`str` key whose `str(key)` rendering has code points `r`. |
| `str(key)` (textual rendering of the key) | `strChars key : List Char` | `str(s) == s` for a `str` key (`PyKey.str s ↦ s`); `str(key)` for a non-`str` key ↦ its rendering `r` (`PyKey.other r ↦ r`). |
| `self.__display_name__` (parent display name) | `displayName : List Char` | per-code-point `str` ↔ `List Char` (SPEC_GUIDE §2). |
| `module + '.' + name` (display-name join) | `concatName module name : Except Unit (List Char)` | `Except.ok (module ++ '.' :: s)` ↔ the joined display name when `name` is text (`PyKey.str s`); `Except.error ()` ↔ the `TypeError` raised when `name` is non-text (`PyKey.other _`). |
| return value `_make_subclass(...)()` / raised `TypeError` | `Except Unit (List Char)` | `Except.ok d` ↔ a successfully constructed subclass whose `__display_name__` is `d`; `Except.error ()` ↔ the raised `TypeError`. |

We model `__getitem__`'s observable outcome by the derived display name it
produces (the field whose construction can fail), as a pure function from
`(displayName, key)` to `Except Unit (List Char)`.

## Callee provenance + flag dependencies

- **`concatName` — the display-name construction, an A-reference (deep model).**
  Models the unchanged `module + '.' + name` concatenation inside `_make_subclass`
  (`mock.py:73`). It is UNCHANGED by the patch; what changes is what the caller
  feeds it. Modeled deeply: a textual component joins to `module ++ '.' :: s`; a
  non-textual component raises (`Except.error ()`). Validated against the real
  concatenation by `axiom_check.py` (G-AX). No `_prop` axiom consumed — the model
  IS the behavior.
- **`strChars` — `str(key)`, the changed operation, modeled deeply (R/I).** This
  is the operation the patch introduces (`key` → `str(key)`). `str` is idempotent
  on text (`str(s) == s`) and renders a non-`str` key to its textual form.
  Modeled structurally over `PyKey`; NEVER axiomatized (SPEC_GUIDE §3). G-CONF
  differential-tests the full subscript outcome that depends on it.
- **No `opaque` callees / no consumed axioms.** Both operations the subscript
  uses are modeled directly; the proof consumes no callee property.
- **Flag dependencies.** None — `__getitem__` takes a single positional key and
  branches on no configuration flag.

## G-CONF fuzz seed

Pinned LCG seed: **7889** (see `conformance_check.py` `SEED`). Corpus: keys of
both kinds — `str` keys (code points 0–10 from a mixed ASCII/punctuation/Unicode
alphabet) and non-`str` keys (modeled by their `str()` rendering), paired with
parent display names of length 0–8 — over ≥1e5 fuzzed inputs, diffed against an
in-process replica of the post-patch `__getitem__` display-name outcome
(`str(key)` then `module + '.' + str(key)`).

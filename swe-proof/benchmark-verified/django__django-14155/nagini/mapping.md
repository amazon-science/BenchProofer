# mapping.md — django__django-14155

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 2f13c476abe4ba787b6cb71131818341911f43cc`, states the type
abstraction, and records the provenance of the deep-model reference (the real
Python interpolation / `repr` semantics the deep model is validated against by
G-AX). No callee is axiomatized as a `@ContractOnly` consumed axiom.

Repo file under change: `django/urls/resolvers.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolver_match_repr(func_path, func_repr, is_prebound, url_name, route)` | `ResolverMatch.__repr__(self)` — `django/urls/resolvers.py:61` | the modeled changed function (the textual description builder) |
| `func_token(func_path, func_repr, is_prebound)` | the new `func = repr(self.func) if isinstance(self.func, functools.partial) else self._func_path` selection (`resolvers.py:62-65` post-patch) | pure spec: the callable-naming choice |
| `quoted(s)` | the `%r` conversion applied to a `str` field (`url_name`, `route`) in the new format string (`resolvers.py:67-71` post-patch) | pure spec: the quoted textual rendering of a text value |
| `delim(s)`, `contains(s,x)` | the delimiter CPython's `repr` picks for that `str` (apostrophe, or double quote when the value holds an apostrophe and no double quote) | pure spec: the delimiter choice inside `%r` |
| `esc_char(c,d)`, `esc_body(s,d)`, `quoted_with(s,d)` | the per-code-point escaping `repr` performs between the delimiters (backslash and the delimiter itself are marked) | pure spec: the body rendering inside `%r` |
| `built_repr(...)` | the whole `'ResolverMatch(func=%s, ... url_name=%r, ... route=%r)' % (...)` interpolation (`resolvers.py:66-72` post-patch), restricted to the modelled fields | pure spec: the assembled description |
| `lit_head/lit_url_name/lit_route/lit_tail` | the literal label segments of the format string | pure spec: format-string literals as code-point sequences |

Pre-patch repo state the change replaces (refinement audit, not referenced from
the consumer spec view): `__repr__` returned
`"ResolverMatch(func=%s, args=%s, kwargs=%s, url_name=%s, app_names=%s, namespaces=%s, route=%s)" % (self._func_path, ...)`
(`resolvers.py:62-65`) — i.e. (A) the callable was ALWAYS named by
`self._func_path`, with no `functools.partial` handling, and (B) every field
used `%s` (plain `str`), so the text fields were unquoted.

`self._func_path` is computed in `__init__` (`resolvers.py:48-53`): for a
callable with `__name__` it is `func.__module__ + '.' + func.__name__`; for one
without (a class-based view, OR a `functools.partial`, which has no `__name__`),
it is `func.__class__.__module__ + '.' + func.__class__.__name__` — for a
partial that is the unhelpful `"functools.partial"`. The fix is exactly: when
`self.func` is a `functools.partial`, name it by `repr(self.func)` instead
(which shows the wrapped callable and the pre-bound arguments).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`self._func_path`, `repr(self.func)`, `self.url_name`, `self.route`, the `__repr__` return) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `str` concatenation / `%`-interpolation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`len`/`[i]` mirror `str` `+`/`len`/index |
| `isinstance(self.func, functools.partial)` | the `bool` flag `is_prebound` | True iff the resolved callable is a `functools.partial` wrapper |
| `repr(self.func)` for a partial | the input `func_repr: List[int]` | the partial's own textual form, supplied as an opaque code-point string (its internal structure is not modelled; only that it is the chosen token when `is_prebound`) |
| `self._func_path` | the input `func_path: List[int]` | the dotted import path, an opaque code-point string |
| `%r` applied to a printable-ASCII `str` field | `quoted(s) = quoted_with(s, delim(s))`, i.e. `[delim(s)] + esc_body(s, delim(s)) + [delim(s)]` | `repr`/`%r` of such a `str` delimits it with `'` (U+0027), or with `"` (U+0022) when it contains a `'` and no `"`; inside, a `\` (U+005C) and each occurrence of the chosen delimiter are preceded by an extra `\`; see §3 |
| the delimiter CPython's `repr` picks for a `str` | `delim(s)` (34 iff `contains(s,39) and not contains(s,34)`, else 39) | the quote-switch rule of `repr`; `contains(s,x)` is front-recursive membership |
| the escaping `repr` applies between the delimiters | `esc_body(s, d)` = elementwise `esc_char(c, d)` (`92 -> [92,92]`, `c == d -> [92,c]`, else `[c]`) | the backslash/delimiter marking of `repr` |
| the four collection fields `args`, `kwargs`, `app_names`, `namespaces` | elided from the model | their `%r` rendering equals their `%s` rendering (tuple/dict/list `repr` == `str`); carry no behavioural distinction (refinement.md step I-collections; G-AX checks the identity) |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**: the changed operation is string
interpolation / `repr`, which is modelled DEEPLY in `model.py` (the literal
segments, `quoted`, `func_token`, `built_repr`). The deep model is validated
against the REAL Python operations it abstracts:

### 3.1 `quoted` ↔ `'%r' % s` (the str-field repr)
**Real operation:** CPython `repr(s)` / `'%r' % s` for a `str` `s`. For a `str`
whose characters are all printable ASCII (code points 32..126) the rendering is
exactly:

* **delimiter.** `'` (U+0027), except that when `s` contains a `'` and does not
  contain a `"`, the delimiter is `"` (U+0022) — so the apostrophes inside need
  no marking. (When `s` contains both, `repr` keeps the `'` delimiter and marks
  the embedded apostrophes.)
* **body.** each code point stands for itself, except that a `\` (U+005C) and
  each occurrence of the chosen delimiter are preceded by an extra `\`.

That is precisely `delim` / `esc_char` / `esc_body` / `quoted_with` / `quoted`
in the pure region. **No code point of the printable range is excluded**: the
apostrophe and the backslash are INSIDE the modelled domain, because they are
the ordinary content of the values this function renders — Django route
patterns carry regex escapes (`\d`, `\w`, `\.`, `\s`) constantly, so a route
like `^\d+/$` is the typical input, not an exotic one. The model's
precondition states the domain it claims (`32 <= url_name[k] <= 126` and the
same for `route`), so the spec no longer asserts anything outside it.
`axiom_check.py` asserts `quoted(s) == '%r' % s` over an exhaustive single-char
sweep of the FULL printable-ASCII range, 49 boundary strings (including
`^\d+/$`, `it's`, `both'and"`, `\`, `\\`, `'\`) and 20 000 fuzz strings drawn
from that whole range.
Docs: the `str` case of the `%`-format `r` conversion (`repr`).

### 3.2 `func_token` ↔ the partial-aware name selection
**Real operation:** `repr(self.func) if isinstance(self.func, functools.partial) else self._func_path`.
A `functools.partial` object has no `__name__`, so the pre-patch `_func_path`
computation yields the class path `"functools.partial"`; the fix substitutes
`repr(self.func)`, exposing the wrapped callable and pre-bound arguments.
`axiom_check.py` builds real `functools.partial` / `update_wrapper` objects
(mirroring the test fixtures `empty_view_partial`, `empty_view_nested_partial`,
`empty_view_wrapped`) and asserts the model's selection matches the real one.

### 3.3 `built_repr` ↔ the full interpolation (modelled fields)
**Real operation:** the new
`'ResolverMatch(func=%s, args=%r, kwargs=%r, url_name=%r, app_names=%r, namespaces=%r, route=%r)' % (func, ...)`.
Restricted to the modelled fields (`func`, `url_name`, `route`) and their
surrounding literals, `axiom_check.py` asserts `built_repr` reproduces the real
interpolation exactly, for both partial and non-partial callables.

### 3.4 The elided collection fields (`%r` == `%s`)
The model omits `args`, `kwargs`, `app_names`, `namespaces` because the
str→repr change is a no-op on their values: `repr(())==str(())`,
`repr({})==str({})`, `repr([])==str([])`, etc. `axiom_check.py`
(`check_collection_field_identity`) confirms `'%r' % v == '%s' % v` for the
collection values that occur, justifying the I-collections refinement step.

**Flag dependency:** none (no `quote=`-style configuration). The only
domain restriction is the printable-ASCII range of §3.1, which is stated as a
`Requires` in the model (not merely as prose) and fuzzed over its whole extent
by G-AX and G-CONF.

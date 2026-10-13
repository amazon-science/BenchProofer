# refinement.md — django__django-14155

The operation-by-operation correspondence between `model.py`'s implementation
(`resolver_match_repr`, the deep `built_repr`/`func_token`/`quoted` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, proof uses the axiom's
`Ensures`, and **A-reference**, a deep model validated == the real operation by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The changed function — `ResolverMatch.__repr__` (`django/urls/resolvers.py:61`)

Gold hunk (whole body):
```
-        return "ResolverMatch(func=%s, args=%s, kwargs=%s, url_name=%s, app_names=%s, namespaces=%s, route=%s)" % (
-            self._func_path, self.args, self.kwargs, self.url_name,
-            self.app_names, self.namespaces, self.route,
-        )
+        if isinstance(self.func, functools.partial):
+            func = repr(self.func)
+        else:
+            func = self._func_path
+        return (
+            'ResolverMatch(func=%s, args=%r, kwargs=%r, url_name=%r, '
+            'app_names=%r, namespaces=%r, route=%r)' % (
+                func, self.args, self.kwargs, self.url_name,
+                self.app_names, self.namespaces, self.route,
+            )
+        )
```

Two independently-observable behaviours change: **(A)** how the callable is
named, and **(B)** that the text fields are now quoted (`%s`→`%r`).

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | params `func_path, func_repr, url_name, route: List[int]` | the `str` attributes `self._func_path`, `repr(self.func)`, `self.url_name`, `self.route` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| 2 | param `is_prebound: bool` | `isinstance(self.func, functools.partial)` | R | the boolean test on the resolved callable; True iff `self.func` is a partial wrapper (mapping.md §2). |
| 3 | `if is_prebound: func = func_repr else: func = func_path` (proven `== func_token(...)`) | `if isinstance(self.func, functools.partial): func = repr(self.func) else: func = self._func_path` | A-reference | the callable-naming choice is modelled DEEPLY (`func_token`); there is no consumed axiom. G-AX validates `func_token` == the real selection on real `functools.partial`/`update_wrapper` objects (mapping.md §3.2). |
| 4 | `du = delim(ToSeq(url_name))`, then the back-to-front fold building `ub` (`92 -> [92,92]`, `c == du -> [92,c]`, else `[c]`) and `q_url = [du] + ub + [du]` (proven `== quoted(ToSeq(url_name))`); same for `route` | the `%r` conversion of the `str` fields `url_name`, `route` in the new format string | A-reference | the str→repr change on a text field is modelled DEEPLY (`delim`/`esc_char`/`esc_body`/`quoted_with`/`quoted`), reproducing BOTH parts of real `repr`: the delimiter choice (double quote when the value holds an apostrophe and no double quote) and the marking of a backslash / an embedded delimiter. G-AX validates `quoted(s) == '%r' % s` over the FULL printable-ASCII range the model's precondition admits — apostrophe and backslash included (mapping.md §3.1). |
| 5 | the literal label segments `lit_head/lit_url_name/lit_route/lit_tail` interleaved with the rendered fields, assembled by `+` (proven `== built_repr(...)`) | the format-string literals + the `%`-interpolation | R + I | the literal segments are the format string's constant pieces (R: `str` literal ↔ code-point `PSeq`); `%`-interpolation of already-rendered pieces is list/`str` concatenation (I). G-AX validates the assembled `built_repr` == the real interpolation (mapping.md §3.3). |
| 6 | (elided) `args`, `kwargs`, `app_names`, `namespaces` | their `%r` conversions in the new format string | I-collections | for these collection values `repr == str`, so the `%s`→`%r` change is a no-op on their content; they carry no behavioural distinction and are omitted from the model. G-AX confirms `'%r' % v == '%s' % v` for the occurring values (mapping.md §3.4). |
| 7 | `return result` (a `List[int]`) | `return ( ... )` (a `str`) | R | the `str` return ↔ the code-point list; `__repr__`'s consumer (the F2P assertions) compares the rendered characters. |

## Why two failing prepatch variants (one per independently-fixed behaviour)

The patch fixes two independently-observable behaviours, so G-DIFF gets one
verification-failing skeleton each (the shared spec is byte-identical):

- **`model_prepatch.py` — behaviour (A) reverted.** `func = func_path`
  unconditionally (no partial handling). FAILS the postcondition
  `ToSeq(Result()) == built_repr(...)`: when `is_prebound` the spec requires the
  `func_repr` token (`func_token` selects it) but the impl emits `func_path`.
  This is exactly the `test_repr_functools_partial` F2P observation (the partial
  must show `repr(self.func)`, not `functools.partial`).
- **`model_prepatch_2.py` — behaviour (B) reverted.** `q_url = url_name`,
  `q_route = route` (no delimiters and no marking — the old `%s`). FAILS the
  same postcondition: the spec requires `quoted(url_name)`/`quoted(route)` but
  the impl emits the bare value. This is exactly the modified `test_repr` F2P
  observation (`url_name='no-kwargs'` and `route='…$'` are now quoted).

### The quoted rendering is modelled as CPython actually renders it

The `quoted` deep model reproduces real `%r` over the whole printable-ASCII
domain the precondition admits, including the two classes that a
single-quote-wrap model gets wrong: a value containing a **backslash** (marked
with an extra backslash — and a Django route such as `^\d+/$` is the ORDINARY
input to this function, not an edge case) and a value containing an
**apostrophe** (which sends the delimiter to the double quote). Both classes are
inside the domain, inside G-AX's exhaustive/fuzz sweep, and inside G-CONF's
differential shadow, so the postcondition states what the real callee
guarantees rather than what an escaping-free idealization would.

## No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. The two operations that genuinely *changed*
— the partial-aware callable name (step 3) and the str→repr quoting of the text
fields (step 4) — are modelled **deeply** (`func_token`, `quoted`, spelled out
over `List[int]`), not hidden behind an axiom about the function under change.
There is **no consumed `@ContractOnly` axiom** (the `axioms` region is empty);
the only kind-A relationships are the **A-reference** validations of the deep
model against real Python `repr`/`%`-interpolation (G-AX, mapping.md §3).

## verify(model) ⇒ resolved

`resolver_match_repr` verifies only if its output equals `built_repr(...)`,
which (3) selects the partial's own form when `is_prebound` and (4) renders the
text fields in their quoted form — delimiter chosen by `delim`, body marked by
`esc_body`. By R (str ↔ List[int], the literal segments, the
collection-field identity) the verified builder equals the gold
`__repr__`'s interpolation on the tested inputs; by G-AX the deep models
`func_token`/`quoted`/`built_repr` equal the real Python selection and
`%`-rendering (A-reference). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and audited deep-model
references — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: deep-model/axiom soundness (G-AX) and refinement
fidelity (this document, G-EQ).

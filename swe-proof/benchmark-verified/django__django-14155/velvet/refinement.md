# refinement.md — django__django-14155

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolverMatchRepr` `do` block, routed through the deep model `matchRepr`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** / **A-reference** (axiomatized callee — none
here), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (absent) A legs and this narrative are audited by **G-EQ**. Claim:
any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The render site — `ResolverMatch.__repr__()` (`resolvers.py:61`)

Gold hunk (condensed):
```
-        return "ResolverMatch(func=%s, args=%s, kwargs=%s, url_name=%s, app_names=%s, namespaces=%s, route=%s)" % (
-            self._func_path, self.args, self.kwargs, self.url_name,
-            self.app_names, self.namespaces, self.route,
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
         )
```
Two independently-observable behavioural changes:
- **(change 1)** the callable component is the partial-application callable's
  full textual form `repr(self.func)` when `self.func` is a `functools.partial`,
  otherwise the dotted path `self._func_path` (pre-patch: always `_func_path`);
- **(change 2)** every other component switches from `%s` to `%r`. Observable
  only on the two string-valued fields `url_name` and `route` (mapping.md §2a):
  they become single-quoted (`%r` of a `str`), the absent case rendering as
  `None`. The container fields render identically under `%s`/`%r`.

| # | Solution.lean impl op (`resolverMatchRepr` / `matchRepr`) | patch.diff / source op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `m : MatchView` | the `ResolverMatch` instance `self` | R | a match ↔ its observable-field record (mapping.md §2). |
| A2 | `let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath` | `if isinstance(self.func, functools.partial): func = repr(self.func) else: func = self._func_path` | R + I | `isinstance(...partial)` ↔ `isPartialFunc` (R); `repr(self.func)` ↔ `funcPartialText`, `self._func_path` ↔ `funcPath` (R, carried verbatim). The `if/else` is the identical two-arm choice (I). **This is discriminating step (change 1)**: `Solution_prepatch_1.lean` drops the partial branch (always `funcPath`) → fails `out = matchRepr m` (G-DIFF). |
| A3 | `"ResolverMatch(func=" ++ funcStr ++ ", args=" ++ m.argsText ++ ", kwargs=" ++ m.kwargsText` | `'ResolverMatch(func=%s, args=%r, kwargs=%r, ' % (func, self.args, self.kwargs, ...)` | R + I | the fixed literal fragments concatenated with the components in source order (R: `%`-format ↔ `++`). `args`/`kwargs` carried as `repr(...)` text; `%r` ≡ `%s` on these containers (mapping.md §2a), so verbatim carry is exact. |
| A4 | `", url_name=" ++ quotedOpt m.urlName` | `'url_name=%r' % self.url_name` | R + I | `%r` of an optional `str` ↔ `quotedOpt` (`None` ↔ `"None"`; `some s` ↔ `quoted s`, the full Python `repr(str)` rule over the ASCII plane: single-quote wrapping with backslash/quote escaping, double-quote wrapping when the value holds a single quote but no double quote, tab/LF/CR as two-letter escape codes and other control characters/DEL as `\xNN` hex escapes — mapping.md §2). The `require asciiOpt` preconditions scope the name/route domain to ASCII, on which the rule is exhaustively validated. **This is discriminating step (change 2)**: `Solution_prepatch_2.lean` renders `url_name`/`route` unquoted (the `%s` form) → fails `out = matchRepr m` (G-DIFF). |
| A5 | `", app_names=" ++ m.appNamesText ++ ", namespaces=" ++ m.namespacesText` | `'app_names=%r, namespaces=%r' % (self.app_names, self.namespaces)` | R + I | the two lists carried as `repr(...)` text; `%r` ≡ `%s` on lists (mapping.md §2a), verbatim carry exact. |
| A6 | `", route=" ++ quotedOpt m.route ++ ")"` | `'route=%r)' % self.route` | R + I | as A4 for the optional route string; closing `)` literal. |

## B. No consumed axioms / no deep-model references

`ResolverMatch.__repr__` consumes no callee contract: every operation is an
`isinstance` test, an attribute read, an unchanged rendering whose result is
carried verbatim as opaque text (`repr(self.func)`, `repr(self.args)`, …), or
`%`-string formatting — all modeled directly as R/I (mapping.md §3). There is
therefore no A-consumed axiom and no A-reference deep model. `meta.json`
`axioms` / `deep_model_references` are empty; **G-AX is `skip`**.

Note on the carried `repr(...)` texts (A3/A5/A6): these are the outputs of
rendering operations the patch does **not** vary (the container `repr`s, and the
callable `repr` whose *selection* — not computation — change 1 adds). They are
**not** axiomatized callees: the spec carries them as given input text (R), it
makes no claim about their internal value, and G-CONF supplies the real
`repr(...)` of real objects on both sides, so any mismodeling would surface as a
disagreement. They are inputs to the modeled formatting, not trust points.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The two operations that genuinely *changed* — the
callable-component selection (A2) and the `%s`→`%r` quoting of the two
string-valued fields (A4/A6) — are modeled **directly and concretely** (the
`if isPartialFunc` choice and the `quoted`/`quotedOpt` function), not hidden
behind an axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`resolverMatchRepr` verifies only if its output equals `matchRepr m` for every
`MatchView` — in particular (change 1) the callable component must be the
partial form exactly when `isPartialFunc` (A2), and (change 2) `url_name` and
`route` must be quoted (A4/A6). By R (`ResolverMatch ↔ MatchView`, `%r`↔`quoted`,
`%`-format↔`++`, container `%r`≡`%s`) the verified renderer equals the patched
`ResolverMatch.__repr__` on the modeled inputs; by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed matches
spanning both branches. The two pre-patch skeletons each fail `out = matchRepr m`
on exactly one of the changed clauses:
- `Solution_prepatch_1.lean`: callable always `funcPath` — fails on the
  partial branch, exactly the F2P `test_repr_functools_partial` assertion
  (`func=functools.partial(<empty_view>, template_name='…')`);
- `Solution_prepatch_2.lean`: `url_name`/`route` unquoted — fails on the
  quoting, exactly the F2P `test_repr` assertion change (`url_name='no-kwargs'`,
  `route='^no_kwargs/…$'`).

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There
are no axiom trust points (G-AX skip); the only trust point is refinement
fidelity (this doc, G-EQ + G-CONF).

# refinement.md — scikit-learn__scikit-learn-14983

Operation-by-operation correspondence between `implementation_reprString`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `_build_repr`
value-resolution loop + `_pprint` rendering). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut parts : List String := []` | `params = dict()` (accumulated rendered entries) | R |
| 2 | `for key in argNames do …` | `for key in args:` (args = sorted ctor param names) | R |
| 3 | `let v0 := lookupVal attrs key` | `value = getattr(self, key, None)` | R |
| 4 | `let mut v := v0; if v0 == PyVal.null && hasExtra then v := lookupVal extra key` | `if value is None and hasattr(self, 'cvargs'): value = self.cvargs.get(key, None)` | R |
| 5 | `parts := parts ++ [key ++ "=" ++ pyRepr v]` | `params[key] = value` then `_pprint` renders `'%s=%s' % (key, repr(value))` | R |
| 6 | `return className ++ "(" ++ String.intercalate ", " parts ++ ")"` | `return '%s(%s)' % (class_name, _pprint(params, …))` (join with `, `) | R |
| 3a | `lookupVal m k = (m.find? (·.1 == k)).elim .null (·.2)` | `getattr(...,None)` / `dict.get(...,None)` (found ↔ value; absent ↔ `None`) | R |
| 5a | `pyRepr (.int n) = toString n` / `.null = "None"` / `.str s = "'"++s++"'"` | `repr(int)` / `repr(None)` / `repr(str)` | R |

Notes:

- **Every step is R — no A, no I-as-literal-transliteration.** The changed op
  (step 4, the auxiliary-map fallback) is modeled DEEPLY; the surrounding loop and
  rendering are refined from Python objects (`self`, `dict`, `getattr`, `repr`,
  `_pprint`) to the `List (String × PyVal)` / `String` carriers per the mapping.md
  bijection. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so the
  `axioms` region is empty and **G-AX skips**. The R legs are validated by G-CONF.

- **The fix itself** is step 4. Base_commit (`Solution_prepatch.lean`) computes
  `v := lookupVal attrs key` with NO fallback, so a parameter held only in the
  auxiliary map (`hasExtra = true`, absent from `attrs`) renders as
  `pyRepr .null = "None"`. The post-patch impl (`Solution.lean`) falls back to
  `lookupVal extra key`, rendering the real value. That single discriminating
  clause is what the F2P test observes (`n_splits=2` vs `n_splits=None`).

- **R vs I.** All rows are **R**: the Python side operates over `self` /
  `dict` / `getattr` / `repr` / `_pprint`, which are refined to the modeled
  `attrs`/`extra`/`lookupVal`/`pyRepr`/`String.intercalate` per mapping.md. There
  is no row that is a byte-for-byte identical concrete op, because every op
  crosses the Python↔Lean carrier boundary.

- **Frame discipline (directive 5).** The result is a single output component
  (the repr string); it is pinned completely by `reprString` over ALL inputs
  (`className`, every `key` in `argNames`, both maps, `hasExtra`). No output
  component is left unconstrained — a wrong renderer (e.g. one that drops the
  fallback, reorders params, or mis-renders a value) cannot satisfy the spec.

- **The `__repr__` routing edit** (the second gold hunk, adding
  `_RepeatedSplits.__repr__`) is *plumbing*: it selects this builder as the
  `repr()` implementation. It is not a step in the builder and is not separately
  modeled — the un-routed alternative is the opaque `object.__repr__` address
  string, which the builder model does not (and need not) express. The one
  behavioral fix the builder model captures is step 4; hence one
  `Solution_prepatch.lean`.

- **G-CONF** mechanically refutes the R legs: a faithful in-process replica of the
  post-patch resolution (`getattr`-then-`cvargs.get`, `repr` rendering, `, `-join)
  is diffed byte-for-byte against the impl shadow over ≥1e5 fuzzed inputs. No A
  legs.

# mapping.md — django__django-15382

Symbol binding, the Lean↔Python type bijection (used by G-CONF), callee
provenance + flag dependencies, and the pinned G-CONF fuzz seed.

All line numbers are at `base_commit`
`770d3e6a4ce8e0a91a9e27156036c1985e74d4a3`.

## 1. Symbol binding

| Lean (`Solution.lean`) | Python (repo @ base_commit) |
|---|---|
| `method renderExistsTest` | `Exists.as_sql` — `django/db/models/expressions.py:1211` |
| input `complemented : Bool` | `self.negated : bool` (the `Exists` instance's negation flag, set by `__invert__`, `expressions.py:1207-1210`) |
| input `inner : Except Unit Frag` | the outcome of the **unchanged** call `super().as_sql(compiler, connection, template=template, query=query, **extra_context)` — `Subquery.as_sql`, `expressions.py:1177`. Returns `(sql, params)` OR raises `EmptyResultSet`. |
| result `out : Except Unit Frag` | the `(sql, params)` returned by `Exists.as_sql`, OR the `EmptyResultSet` it (re-)raises |

The slice under spec is the body of `Exists.as_sql` *downstream of* the
`super().as_sql(...)` call: the post-call handling of its outcome under the
`self.negated` flag. The lines before the call (`query =
self.query.exists(using=...)`) are unchanged setup that only configures the
argument fed to the unchanged callee; they are folded into the callee's free
outcome.

## 2. Type bijection (G-CONF bridge)

| repo reality | Lean model | bridge |
|---|---|---|
| `(sql: str, params: tuple)` SQL fragment | `Frag { sql : List Char, params : List Int }` | `sql ↔ str` via `List Char` (per-char), `params ↔ tuple` via `List Int` (positional). Only used as opaque carriers; element identity is irrelevant — the behaviour observes the negation-prefix on `sql` and the empty-fragment substitution, never individual characters/params. |
| `super().as_sql(...)` returns `(sql, params)` | `inner = Except.ok ⟨sql, params⟩` | the renderer produced a fragment |
| `super().as_sql(...)` raises `EmptyResultSet` | `inner = Except.error ()` | the renderer signalled a provably-empty underlying set; the unit payload carries no information (the exception is a pure control signal) |
| `Exists.as_sql` returns `(sql, params)` | `out = Except.ok ⟨sql, params⟩` | normal return |
| `Exists.as_sql` returns `('', ())` | `out = Except.ok ⟨[], []⟩` | the **new** post-patch empty/always-true fragment |
| `Exists.as_sql` (re-)raises `EmptyResultSet` | `out = Except.error ()` | emptiness propagated (plain, non-negated case) |
| `sql = 'NOT {}'.format(sql)` | `{ f with sql := "NOT ".toList ++ f.sql }` | negation prepends the keyword + space to the text; `params` unchanged |

`Frag.params : List Int` is a positional stand-in for the parameter tuple; the
change never inspects, reorders, or drops parameters on the `ok` path (it copies
the tuple through) and emits the empty tuple `()` on the new empty-fragment path,
so `List Int` is a faithful carrier for the differential.

## 3. Callee provenance + flag dependencies

- **`super().as_sql` (`Subquery.as_sql`, `expressions.py:1177`)** — UNCHANGED by
  the patch. It is the renderer whose outcome is the free input `inner`. It is
  NOT axiomatized: modeling its outcome as an arbitrary `Except Unit Frag`
  (directive 7) is strictly weaker than any contract on it, so the spec owes it
  nothing and there is no consumed axiom / A-reference. Its `EmptyResultSet`
  outcome is real: `Subquery.as_sql` → `Query.as_sql` → the compiler can raise
  `EmptyResultSet` when a subquery's WHERE is provably empty (e.g. an
  `__in=[]`/`.none()` queryset). G-CONF exercises both outcomes by driving the
  real `Exists.as_sql` with both an empty (`.none()`) and a non-empty subquery.
- **Flag dependency:** the empty-fragment substitution fires only when
  `self.negated is True`. `__invert__` (`~Exists(...)`) flips `negated`; the
  reported issue uses `~Exists(MyModel.objects.none())`, i.e. `negated=True` over
  a provably-empty subquery. G-CONF fuzzes both flag values × both renderer
  outcomes (the full 2×2 matrix).

No deeply-modeled changed op → no A-reference. No consumed axiom → `axiom_check.py`
is absent and G-AX is `skip` (consistent with django-14017).

## 4. G-CONF fuzz seed

`SEED = 15382`, `N_FUZZ = 100000` (pinned; `conformance_check.py`). Boundary
cases (the 2×2 matrix of `negated ∈ {False, True}` × renderer ∈ {fragment,
`EmptyResultSet`}) are enumerated first, then randomized fragments.

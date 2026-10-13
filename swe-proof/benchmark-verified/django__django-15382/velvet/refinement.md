# refinement.md — django__django-15382

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`renderExistsTest` `do` block / the `renderExists` pure model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
narrative is audited by **G-EQ**. `patch.diff` is the gold patch **verbatim**
(G-RESOLVE).

## Gold hunk (`django/db/models/expressions.py`, `Exists.as_sql`)

```python
 def as_sql(self, compiler, connection, template=None, **extra_context):
     query = self.query.exists(using=connection.alias)
-    sql, params = super().as_sql(
-        compiler, connection, template=template, query=query, **extra_context,
-    )
+    try:
+        sql, params = super().as_sql(
+            compiler, connection, template=template, query=query, **extra_context,
+        )
+    except EmptyResultSet:
+        if self.negated:
+            return '', ()
+        raise
     if self.negated:
         sql = 'NOT {}'.format(sql)
     return sql, params
```

## Correspondence table

| # | `Solution.lean` op (`renderExistsTest`) | `patch.diff` op | tag | justification |
|---|---|---|---|---|
| 1 | param `complemented : Bool` | `self.negated` | R | `bool ↔ Bool` (mapping.md §1). |
| 2 | param `inner : Except Unit Frag` | the outcome of the unchanged `super().as_sql(...)` call: `(sql, params)` returned **or** `EmptyResultSet` raised | R | `(sql,params) ↔ Except.ok ⟨sql,params⟩`; `EmptyResultSet ↔ Except.error ()` (mapping.md §2). The renderer is unchanged; its outcome is a **free input**, strictly weaker than any contract — no axiom owed (directive 7). |
| 3 | `match inner with \| Except.ok f => …` | the `try:` body succeeds: `sql, params = super().as_sql(...)` binds | I | the success path: the produced fragment is taken as-is into the downstream handling. Concrete, transliterated by G-CONF. |
| 4 | `Except.ok (if complemented then { f with sql := "NOT ".toList ++ f.sql } else f)` | `if self.negated: sql = 'NOT {}'.format(sql)` then `return sql, params` | R + I | the post-success negation: prepend `"NOT "` to the text, parameters unchanged. `'NOT {}'.format(sql) ↔ "NOT ".toList ++ f.sql` (mapping.md §2). The `else` branch returns `f` unchanged. |
| 5 | `\| Except.error _ => if complemented then Except.ok ⟨[], []⟩ else Except.error ()` | `except EmptyResultSet: if self.negated: return '', () ; raise` | R + I | **the fix.** On the emptiness signal: when inverted, return the empty (always-true) fragment `('', ()) ↔ ⟨[], []⟩`; otherwise re-`raise`, i.e. propagate `Except.error ()`. mapping.md §2. |

## No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — catching the
emptiness signal and, under inversion, substituting the empty fragment instead of
propagating it — is modeled **directly** as the `match`/`if` on the free-input
`Except` carrier (steps 3–5), not hidden behind an axiom about the function under
change. There is **no consumed axiom and no A-reference**: the only callee
(`super().as_sql`) is unchanged and modeled as a free input (step 2), so it owes
no contract and needs no G-AX check.

## What the prepatch fails on (G-DIFF)

`Solution_prepatch.lean` reproduces the pre-patch skeleton: the `Except.error`
branch returns `Except.error ()` **unconditionally** (the emptiness signal
propagates before the inversion is consulted — the missing `try/except`). It
fails `out = renderExists complemented inner` precisely on `inner = Except.error ()`,
`complemented = true`, where the frozen spec requires `Except.ok ⟨[], []⟩` (the empty
always-true fragment) — exactly the `~Exists(...none())` case the F2P test
`test_negated_empty_exists` exercises.

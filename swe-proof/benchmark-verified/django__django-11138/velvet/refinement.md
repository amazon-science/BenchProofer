# refinement.md — django__django-11138

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildTzAdjustedExpr` `do` block + the `tzAdjustedExpr` deep model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — A-consumed / A-reference), or **I** (identical
concrete op). This bundle has **no A steps**: the SQL expression is computed
entirely from the inputs, so every step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled site — MySQL `_convert_field_to_tz` (`django/db/backends/mysql/operations.py:71`)

Gold hunk:
```
-        if settings.USE_TZ:
-            field_name = "CONVERT_TZ(%s, 'UTC', '%s')" % (field_name, tzname)
+        if settings.USE_TZ and self.connection.timezone_name != tzname:
+            field_name = "CONVERT_TZ(%s, '%s', '%s')" % (field_name, self.connection.timezone_name, tzname)
         return field_name
```

| # | Solution.lean impl op (`buildTzAdjustedExpr`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `active : Bool` | `settings.USE_TZ` read | R | truthy `bool` ↔ `Bool` (mapping.md §2). |
| A2 | param `expr : List Char` | `field_name : str` arg | R | `str` ↔ `List Char` (mapping.md §2). |
| A3 | param `queryZone : List Char` | `tzname : str` arg | R | `str` ↔ `List Char`. |
| A4 | param `storedZone : List Char` | `self.connection.timezone_name` (base.py:137) | R | `str` ↔ `List Char`; the connection's stored zone (mapping.md §1). |
| A5 | guard `active ∧ storedZone ≠ queryZone` | `if settings.USE_TZ and self.connection.timezone_name != tzname:` | I | identical boolean decision; `≠` on `List Char` ↔ `!=` on `str` (mapping.md §2). |
| A6 | wrap `"CONVERT_TZ(" ++ expr ++ ", '" ++ storedZone ++ "', '" ++ queryZone ++ "')"` | `"CONVERT_TZ(%s, '%s', '%s')" % (field_name, self.connection.timezone_name, tzname)` | I | `%`-interpolation ↔ concatenation of literal fragments around the three substituted strings (mapping.md §2). |
| A7 | else branch returns `expr` unchanged | `return field_name` (unwrapped) | I | identity when support off or zones equal. |

Discriminating content of the change — the conversion **source** is the
connection's stored zone, not a hardcoded `'UTC'` (A6), AND when the stored zone
equals the query zone the expression is returned **verbatim** (A5/A7) — lives in
the guard `storedZone ≠ queryZone` and the `storedZone` interpolation.
`Solution_prepatch.lean` reproduces the pre-patch bug (always wrap under
`active`, fixed `'UTC'` origin, no skip) and **fails** `out = tzAdjustedExpr …`
(G-DIFF) on both discriminating clauses.

## B. The three additional change sites (shipped, not modeled)

Gold patch.diff also edits the Oracle `_convert_field_to_tz`
(`oracle/operations.py`) and the SQLite path (`sqlite3/base.py`
`_sqlite_datetime_parse` + the five `_sqlite_datetime_*` SQL functions;
`sqlite3/operations.py` `_convert_tznames_to_sql` + four `datetime_*_sql`).

All three are the **same conceptual fix** as site A: convert from the
connection's stored zone (`connection.timezone_name` / `conn_tzname`) instead of
forcing UTC, and skip the conversion when the stored zone equals the query zone
(`if tzname is not None and tzname != conn_tzname` for SQLite;
`if self.connection.timezone_name != tzname` for Oracle). They are shipped in
`patch.diff` (gold verbatim) so the harness resolves — the single F2P test
`test_query_convert_timezones` exercises the **SQLite** backend — but they
express **no behaviour independent** of the modeled decision in site A. Hence:

- no second `method` is modeled for them, and
- no `Solution_prepatch_<k>.lean` (a prepatch must keep the spec byte-identical,
  G-DIFF; there is no independently-observable fixed behaviour to discriminate
  that site A's prepatch does not already discriminate).

This is the django__django-14376 precedent (a shipped-but-unmodeled second
change site, kwargs rename, with no independently-observable behaviour).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the SQL-builder's
conversion decision and its source zone — is modeled **deeply** (the spelled-out
`tzAdjustedExpr` string computation, steps A5-A7), not hidden behind an axiom
about the function under change. There are **no axioms** in this bundle
(`axioms = []`, `deep_model_references = []`): nothing is delegated to an
unchanged callee, so there is no `axiom_check.py` and G-AX = skip.

## D. verify(Solution) ⇒ resolved

`buildTzAdjustedExpr` verifies only if its output equals the exact conversion
decision: wrap with `storedZone` as the origin precisely when support is active
and the zones differ, identity otherwise (A5-A7). By R (`str ↔ List Char`,
`bool ↔ Bool`, `%`-format ↔ `++`) the verified builder equals the patched MySQL
`_convert_field_to_tz` on every input; by G-CONF the R/I transliteration agrees
with `patch.diff`'s behaviour on ≥10⁵ inputs (the patched real callee as oracle);
the three additional sites (§B) ship verbatim in patch.diff and resolve the F2P
SQLite test (G-RESOLVE). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The only trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms to trust (G-AX = skip).
